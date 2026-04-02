# Detailed Sequence Diagram — Government Services Portal

## Overview

These sequence diagrams document the precise implementation-level interactions between frontend components, Django views, serializers, service classes, Celery tasks, and external APIs. Each diagram uses the actual class and method names from the codebase to serve as executable specifications. Developers implementing a feature should follow the flow shown here; deviations must be documented with a rationale.

All sequence diagrams use Mermaid `sequenceDiagram` notation. Participants are listed in left-to-right order matching the typical call flow. Notes (`Note over`) document important implementation decisions inline.

---

## SD-001: NID OTP Login

This sequence covers the complete NID OTP-based authentication flow. It involves two round trips: first requesting the OTP, then verifying it. A JWT access token and refresh token are issued on successful verification.

```mermaid
sequenceDiagram
    participant CB as CitizenBrowser
    participant NP as NextJSPage<br/>(app/login/page.tsx)
    participant DAV as DjangoAuthView<br/>(NIDOTPRequestView)
    participant AS as NIDService<br/>(auth_app/services.py)
    participant NASC (National Identity Management Centre) as UIDAPIGateway<br/>(NASC (National Identity Management Centre) Auth API)
    participant RC as RedisCache
    participant CW as CeleryWorker
    participant SGS as SMSGatewayService<br/>(Fast2SMS/MSG91)
    participant CM as CitizenModel<br/>(citizens table)

    CB->>NP: User enters NID number and clicks "Get OTP"
    NP->>NP: Validate NID format (12 digits, Verhoeff checksum)
    NP->>DAV: POST /api/v1/auth/request-otp/ {aadhaar_number}

    DAV->>DAV: OTPRequestSerializer.is_valid()
    Note over DAV: Rate limit check: 3 OTP requests per NID per 10 minutes (Redis counter)
    DAV->>AS: NIDService.request_otp(aadhaar_number)
    AS->>AS: Hash aadhaar_number with bcrypt to get aadhaar_hash
    AS->>NASC (National Identity Management Centre): POST /uidai/auth/1.0/otp {uid, ac, sa, ver, txn, ts}
    Note over AS,NASC (National Identity Management Centre): HTTPS with mutual TLS; NASC (National Identity Management Centre) ASA credentials in AWS Secrets Manager
    NASC (National Identity Management Centre)-->>AS: {status: "y", txnId: "TXN-XXXX", info: "OTP sent to registered mobile"}
    AS->>RC: SET otp_txn:{txnId} = {aadhaar_hash, mobile_hint} EX 600
    Note over AS,RC: TTL 10 minutes; ties txnId to hashed NID for verification step
    AS-->>DAV: OTPRequestResult{txn_id, mobile_hint, expires_in: 600}
    DAV-->>NP: HTTP 200 {txn_id, mobile_hint, expires_in: 600}
    NP->>NP: Store txn_id in component province; show OTP input form
    NP-->>CB: Display "OTP sent to xxxxxx7890" with 10-minute countdown timer

    CB->>NP: User enters 6-digit OTP and clicks "Verify"
    NP->>DAV: POST /api/v1/auth/verify-otp/ {txn_id, otp}
    Note over NP,DAV: Replace with NIDOTPVerifyView endpoint

    DAV->>DAV: OTPVerifySerializer.is_valid()
    DAV->>AS: NIDService.verify_otp(txn_id, otp)
    AS->>RC: GET otp_txn:{txn_id}
    RC-->>AS: {aadhaar_hash, mobile_hint} (or nil if expired)
    AS->>AS: Validate txn_id is not expired and not already used
    AS->>NASC (National Identity Management Centre): POST /uidai/auth/1.0/verify {uid, ac, sa, ver, txn, otp, ts}
    NASC (National Identity Management Centre)-->>AS: {status: "y", ret: "y", txnId: "TXN-XXXX", err: ""}
    Note over AS,NASC (National Identity Management Centre): On failure: {status: "n", ret: "n", err: "330"} → map to user-friendly error
    AS->>NASC (National Identity Management Centre): POST /uidai/ekyc/1.0/ekyc {uid, txn} (if first login)
    NASC (National Identity Management Centre)-->>AS: {name, dob, gender, mobile, email, address}
    AS->>CM: CitizenModel.objects.get_or_create(aadhaar_hash=aadhaar_hash)
    CM-->>AS: (citizen_instance, created: bool)
    AS->>CM: citizen.update_from_ekyc(demographic_data)
    CM-->>AS: Updated CitizenModel instance
    AS->>RC: DEL otp_txn:{txn_id}
    Note over AS,RC: Invalidate used txnId to prevent replay attacks
    AS->>RC: SET used_txn:{txn_id} = "1" EX 86400
    Note over AS,RC: Mark txnId as used for 24 hours as additional replay guard

    AS-->>DAV: AuthResult{citizen, is_new_user}
    DAV->>DAV: JWTManager.issue_tokens(citizen.id, citizen.role)
    Note over DAV: Access token TTL: 15 minutes; Refresh token TTL: 7 days; stored in Redis
    DAV->>CW: audit_login.delay(citizen.id, request.META['REMOTE_ADDR'], 'AADHAAR_OTP')
    CW->>CW: AuditLogModel.objects.create(actor=citizen, action='LOGIN', ...)
    DAV-->>NP: HTTP 200 {access_token, refresh_token, citizen_profile}
    NP->>NP: Store access_token in memory; Set refresh_token as HttpOnly Secure SameSite=Strict cookie
    NP->>NP: Initialize Zustand auth store with citizen_profile
    NP-->>CB: Redirect to /dashboard
```

---

## SD-002: Multi-Step Application Submission

This sequence covers the full application submission flow — from the citizen landing on the service detail page, through form completion, document upload, and final submission that triggers the workflow engine.

```mermaid
sequenceDiagram
    participant CB as CitizenBrowser
    participant AF as ApplicationFormPage<br/>(app/apply/[serviceCode]/page.tsx)
    participant AC as ApiClient<br/>(lib/api-client.ts)
    participant ACV as ApplicationCreateView<br/>(applications/views.py)
    participant FSV as FormSchemaValidator<br/>(applications/validators.py)
    participant AM as ApplicationModel<br/>(ServiceApplicationModel)
    participant DUV as DocumentUploadView<br/>(documents/views.py)
    participant S3U as S3Uploader<br/>(documents/storage.py)
    participant WE as WorkflowEngine<br/>(state_machine/engine.py)
    participant CW as CeleryWorker
    participant NS as NotificationService

    CB->>AF: Navigate to /apply/INCOME-CERT-01
    AF->>AC: GET /api/v1/services/INCOME-CERT-01/
    AC-->>AF: ServiceDetail{form_schema, eligibility_criteria, fee_amount, required_docs}
    AF->>AF: FormBuilder.render(form_schema) → Dynamic form with conditional sections
    AF->>AF: EligibilityChecker.evaluate(eligibility_criteria, citizen_profile) → Pass/Fail
    AF-->>CB: Render form with eligibility result and required documents list

    CB->>AF: User fills Step 1 (Personal Details) and clicks "Save & Continue"
    AF->>AF: JSONSchemaValidator.validate(step1_data, form_schema.step1)
    AF->>AC: POST /api/v1/applications/ {service_id, form_data: {step1: {...}}, status: "DRAFT"}
    AC->>ACV: POST /api/v1/applications/
    ACV->>ACV: ApplicationCreateSerializer.is_valid()
    Note over ACV: Verify citizen is authenticated; check for duplicate active application
    ACV->>FSV: FormSchemaValidator.validate(form_data, service.form_schema)
    FSV-->>ACV: ValidationResult{valid: true, errors: []}
    ACV->>AM: ServiceApplicationModel.objects.create(citizen=citizen, service=service, form_data=..., status='DRAFT')
    AM-->>ACV: application_instance
    ACV-->>AC: HTTP 201 {application_id, status: "DRAFT"}
    AC-->>AF: {application_id}
    AF->>AF: Store application_id in local province for subsequent steps

    CB->>AF: User fills Step 2 (Income Details) and uploads Income Certificate PDF
    AF->>AF: FileValidator.validate(file) → Check size ≤ 5MB, type ∈ [PDF, JPEG, PNG]
    AF->>AC: POST /api/v1/applications/{application_id}/documents/ (multipart/form-data)
    AC->>DUV: POST /api/v1/applications/{application_id}/documents/
    DUV->>DUV: DocumentUploadSerializer.is_valid()
    Note over DUV: Verify citizen owns application; check file MIME type server-side
    DUV->>S3U: S3Uploader.upload(file_bytes, application_id, doc_type='INCOME_PROOF')
    Note over S3U: Generate S3 key: docs/{application_id}/INCOME_PROOF/{uuid}.pdf
    S3U->>S3U: Compute SHA-256 checksum of file bytes
    S3U->>S3U: s3_client.put_object(Key=key, Body=bytes, ServerSideEncryption='aws:kms')
    S3U-->>DUV: UploadResult{s3_key, checksum}
    DUV->>DUV: ApplicationDocumentModel.objects.create(application=app, s3_key=..., doc_type=..., verified=False)
    DUV->>CW: scan_document_for_malware.delay(doc_id, s3_key)
    DUV-->>AC: HTTP 201 {doc_id, document_type, original_filename}
    AC-->>AF: Document upload confirmed

    CB->>AF: User reviews summary and clicks "Submit Application"
    AF->>AC: PATCH /api/v1/applications/{application_id}/submit/
    AC->>ACV: PATCH /api/v1/applications/{application_id}/submit/
    ACV->>ACV: ApplicationSubmitSerializer.is_valid()
    Note over ACV: Validate all required documents are uploaded; validate all form steps complete
    ACV->>WE: WorkflowEngine.transition(application, trigger='submit_application', actor_id=citizen.id)
    WE->>WE: validate_transition('DRAFT', 'submit_application') → to_state='SUBMITTED'
    WE->>AM: application.status = 'SUBMITTED'; application.submitted_at = now()
    AM-->>WE: Saved
    WE->>WE: WorkflowStepModel.objects.create(application=app, step_name='SUBMISSION', status='COMPLETED', ...)
    WE->>WE: application_state_changed.send(sender=application, old_state='DRAFT', new_state='SUBMITTED')
    ACV->>CW: send_acknowledgment_notification.delay(application_id)
    CW->>NS: NotificationService.send_application_received(application)
    NS->>NS: Render SMS template in citizen.preferred_lang
    NS->>NS: SMSAdapter.send(citizen.mobile, message)
    NS->>NS: EmailAdapter.send(citizen.email, subject, html_body)
    NS->>NS: NotificationModel.objects.create(...)
    ACV-->>AC: HTTP 200 {application_id, status: "SUBMITTED", submitted_at, acknowledgment_number}
    AC-->>AF: Submission confirmed
    AF-->>CB: Show success screen with acknowledgment number and status tracker link
```

---

## SD-003: Payment Processing

This sequence covers the full payment lifecycle from initiation through webhook confirmation, with Redis-based locking to prevent duplicate charges.

```mermaid
sequenceDiagram
    participant CB as CitizenBrowser
    participant PP as PaymentPage<br/>(app/pay/[applicationId]/page.tsx)
    participant AC as ApiClient
    participant PIV as PaymentInitiateView<br/>(payments/views.py)
    participant PS as PaymentService<br/>(payments/services.py)
    participant RC as RedisCache
    participant PGC as ConnectIPSClient<br/>(payments/paygov.py)
    participant PGW as ConnectIPSGateway<br/>(external)
    participant PWH as ConnectIPSWebhookView<br/>(payments/views.py)
    participant PM as PaymentModel
    participant CW as CeleryWorker
    participant AS as ApplicationService

    CB->>PP: Citizen opens payment page for application
    PP->>AC: GET /api/v1/payments/application/{application_id}/status/
    AC-->>PP: {status: null, amount: 500.00, gateway_options: ['PAYGOV', 'CHALLAN']}
    PP-->>CB: Show payment options: Online (ConnectIPS) / Offline Challan

    CB->>PP: Citizen selects "Pay Online via ConnectIPS" and clicks "Proceed"
    PP->>AC: POST /api/v1/payments/initiate/ {application_id, gateway: "PAYGOV"}
    AC->>PIV: POST /api/v1/payments/initiate/
    PIV->>PIV: PaymentInitiateSerializer.is_valid()
    Note over PIV: Verify citizen owns application; verify application.status == 'PAYMENT_PENDING'
    PIV->>PS: PaymentService.create_payment(application_id, gateway='PAYGOV')
    PS->>RC: SET payment_lock:{application_id} NX EX 30
    Note over PS,RC: Redis NX lock prevents concurrent duplicate payment creation; 30s TTL
    RC-->>PS: "OK" (lock acquired) or nil (lock already held)
    PS->>PM: PaymentModel.objects.filter(application_id=...).exclude(status__in=['FAILED','REFUNDED']).exists()
    PM-->>PS: False (no active payment exists)
    PS->>PM: PaymentModel.objects.create(application_id=..., amount=500.00, gateway='PAYGOV', status='INITIATED')
    PM-->>PS: payment_instance
    PS->>PGC: ConnectIPSClient.create_order(payment_id, amount=500.00, currency='NPR', callback_url='...')
    PGC->>PGW: POST /paygov/api/v2/orders {merchantId, orderId, amount, callbackUrl, hmac}
    PGW-->>PGC: {orderId, redirectUrl, paygovOrderId}
    PGC-->>PS: OrderResult{order_id, redirect_url, paygov_order_id}
    PS->>PM: payment.gateway_txn_id = paygov_order_id; payment.status = 'PENDING'
    PM-->>PS: Saved
    PS->>RC: DEL payment_lock:{application_id}
    PS-->>PIV: Payment{id, redirect_url, amount}
    PIV-->>AC: HTTP 201 {payment_id, redirect_url, amount, expires_at}
    AC-->>PP: Redirect URL received
    PP-->>CB: Redirect browser to ConnectIPS payment page (redirect_url)

    CB->>PGW: Citizen completes payment on ConnectIPS gateway
    PGW->>PWH: POST /api/v1/payments/webhook/paygov/ {orderId, txnId, status, amount, hmac}
    Note over PGW,PWH: Webhook received asynchronously; may arrive before citizen redirect
    PWH->>PWH: ConnectIPSClient.verify_webhook_signature(payload, request.META['HTTP_X_PAYGOV_SIGNATURE'])
    Note over PWH: HMAC-SHA256 verification with merchant secret; reject if invalid → HTTP 400
    PWH->>PM: PaymentModel.objects.select_for_update().get(gateway_txn_id=order_id)
    Note over PWH,PM: select_for_update() prevents concurrent webhook processing for same payment
    PM-->>PWH: payment_instance (status='PENDING')
    PWH->>PWH: Check idempotency: if payment.status == 'COMPLETED' → return HTTP 200 early
    PWH->>CW: process_payment_webhook.delay(payment_id, payload)
    PWH-->>PGW: HTTP 200 (acknowledge receipt immediately)

    CW->>PM: payment.mark_completed(txn_id=payload['txnId'])
    PM-->>CW: payment.status = 'COMPLETED'; payment.completed_at = now()
    CW->>AS: ApplicationService.on_payment_confirmed(application_id)
    AS->>AS: WorkflowEngine.transition(application, 'payment_confirmed')
    AS->>AS: application.status → 'PAYMENT_COMPLETED'
    CW->>CW: send_payment_confirmation.delay(payment_id)
    Note over CW: Notification sent: SMS + Email receipt with transaction ID

    PGW->>CB: Redirect to /status/{application_id}?payment=success
    CB->>PP: Citizen lands on success page
    PP->>AC: GET /api/v1/payments/application/{application_id}/status/
    AC-->>PP: {status: "COMPLETED", txn_id, amount, completed_at}
    PP-->>CB: Show payment success confirmation with receipt download link
```

---

## SD-004: Celery Async Processing

This sequence illustrates the Celery task lifecycle for any asynchronous background operation, using document malware scanning and notification dispatch as concrete examples.

```mermaid
sequenceDiagram
    participant DV as DjangoView
    participant CW as CeleryWorker<br/>(celery -A gsp worker)
    participant RQ as RedisQueue<br/>(broker)
    participant DB as PostgreSQLDB
    participant S3 as AWS S3
    participant MAL as MalwareScanner<br/>(ClamAV/SaaS)
    participant NS as NotificationService

    DV->>RQ: scan_document_for_malware.delay(doc_id, s3_key)
    Note over DV,RQ: Task is serialized to JSON and pushed to 'documents' Celery queue
    DV-->>DV: Response returned to client immediately (non-blocking)

    RQ->>CW: Worker picks up task from 'documents' queue
    CW->>CW: task.max_retries = 3; task.default_retry_delay = 60s
    CW->>S3: s3_client.get_object(Key=s3_key)
    S3-->>CW: file_bytes (streamed)
    CW->>MAL: MalwareScanner.scan(file_bytes)
    Note over CW,MAL: Timeout: 30 seconds; ClamAV daemon or SaaS API (e.g., VirusTotal enterprise)

    alt Clean file
        MAL-->>CW: ScanResult{clean: True}
        CW->>DB: ApplicationDocumentModel.objects.filter(id=doc_id).update(scan_status='CLEAN')
        DB-->>CW: 1 row updated
        CW->>CW: Task completed successfully; result stored in Redis backend (TTL 1h)
    else Infected file
        MAL-->>CW: ScanResult{clean: False, threat_name: 'Trojan.PDF.XYZ'}
        CW->>DB: ApplicationDocumentModel.objects.filter(id=doc_id).update(scan_status='INFECTED')
        CW->>S3: s3_client.delete_object(Key=s3_key)
        Note over CW,S3: Delete infected file immediately; quarantine to separate S3 bucket
        CW->>DB: AuditLogModel.objects.create(action='DOCUMENT_MALWARE_DETECTED', ...)
        CW->>NS: NotificationService.send_admin_alert(event='MALWARE_DETECTED', context={doc_id})
        CW->>CW: Task completed with INFECTED result
    else Scanner unavailable (exception raised)
        MAL-->>CW: ConnectionError / Timeout
        CW->>CW: self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
        Note over CW: Exponential backoff: retry at 60s, 120s, 240s
        alt Max retries exceeded
            CW->>DB: ApplicationDocumentModel.objects.filter(id=doc_id).update(scan_status='SCAN_FAILED')
            CW->>DB: AuditLogModel.objects.create(action='SCAN_TASK_FAILED', ...)
            CW->>NS: NotificationService.send_admin_alert(event='SCAN_FAILURE', context={doc_id})
        end
    end

    Note over CW,RQ: Separate example: notification_tasks.send_notification
    DV->>RQ: send_notification.delay(citizen_id, template_key='APPLICATION_RECEIVED', context={...})
    RQ->>CW: Worker picks up from 'notifications' queue (separate queue with 4 workers)
    CW->>DB: CitizenModel.objects.get(id=citizen_id) → get preferred_lang, mobile, email
    CW->>NS: NotificationService.dispatch(citizen, template_key, context, channels=['SMS','EMAIL'])
    NS->>NS: TemplateRenderer.render(template_key, context, lang=citizen.preferred_lang)
    NS->>NS: SMSAdapter.send(mobile, rendered_sms)
    NS->>NS: EmailAdapter.send(email, subject, html_body)
    NS->>DB: NotificationModel.objects.create(status='SENT', sent_at=now(), reference_id=gateway_ref)
    CW->>CW: Task success
```

---

## SD-005: Certificate Generation and DSC Signing

This sequence shows the complete certificate issuance flow triggered when a field officer approves an application.

```mermaid
sequenceDiagram
    participant FO as FieldOfficer<br/>(Browser)
    participant DP as DashboardPage<br/>(Next.js)
    participant AC as ApiClient
    participant AAV as ApplicationApproveView<br/>(applications/views.py)
    participant WE as WorkflowEngine
    participant AM as ApplicationModel
    participant CW as CeleryWorker
    participant CG as CertificateGenerator<br/>(certificates/generator.py)
    participant DSC as DSCSigningService<br/>(certificates/dsc.py)
    participant S3C as S3Client
    participant DLS as Nepal Document Wallet (NDW)Service
    participant NS as NotificationService
    participant CM as CertificateModel

    FO->>DP: Officer clicks "Approve Application" on review dashboard
    DP->>AC: POST /api/v1/applications/{application_id}/approve/ {notes}
    AC->>AAV: POST with JWT (officer role validated by IsOfficerPermission)
    AAV->>AAV: ApprovalSerializer.is_valid()
    Note over AAV: Verify officer is assigned to this application; verify all documents verified
    AAV->>WE: WorkflowEngine.transition(application, trigger='approve', actor_id=officer.id, notes=notes)
    WE->>WE: validate_transition('UNDER_REVIEW', 'approve') → OK
    WE->>AM: application.status = 'APPROVED'; application.approved_at = now()
    WE->>WE: WorkflowStepModel.objects.create(step_name='APPROVAL', actor=officer, action='APPROVED', notes=notes)
    WE->>WE: application_state_changed.send(old='UNDER_REVIEW', new='APPROVED')
    AAV->>CW: generate_and_issue_certificate.delay(application_id, officer_id)
    AAV-->>AC: HTTP 200 {status: "APPROVED", approved_at}
    AC-->>DP: Application approved; certificate generation queued
    DP-->>FO: Show "Approved — Certificate being generated" status

    CW->>CW: Task: generate_and_issue_certificate(application_id, officer_id)
    CW->>AM: application = ServiceApplicationModel.objects.select_related('citizen','service','payment').get(id=application_id)
    CW->>CG: CertificateGenerator.render_pdf(application, template_name='income_certificate_v2')
    CG->>CG: Load Jinja2 HTML template from templates/certificates/
    CG->>CG: Render template with application.form_data + citizen.full_name + service.name + today's date
    CG->>CG: WeasyPrint.write_pdf(html_content) → certificate_bytes (PDF/A-1b)
    Note over CG: PDF/A-1b format required for long-term archiving; embedded fonts; no external resources
    CG-->>CW: certificate_bytes
    CW->>CW: Generate certificate_number: f"{service.code}-{state_code}-{year}-{seq_number:06d}"
    CW->>DSC: DSCSigningService.sign(certificate_bytes, certificate_number)
    DSC->>DSC: Load DSC PFX from AWS Secrets Manager (cached in memory, refreshed hourly)
    DSC->>DSC: pkcs7.sign(certificate_bytes, dsc_cert, dsc_key, digest='sha256')
    Note over DSC: PKCS#7 detached signature; creates CMS SignedData envelope
    DSC->>DSC: Compute SHA-256 fingerprint of DSC certificate
    DSC-->>CW: SignedPDF{signed_bytes, dsc_fingerprint}
    CW->>S3C: s3_client.put_object(Key=certs/{application_id}/{cert_number}.pdf, Body=signed_bytes, SSEKMSKeyId=KMS_KEY_ID)
    S3C-->>CW: UploadResult{s3_key, version_id}
    CW->>CM: CertificateModel.objects.create(application=application, certificate_number=cert_number, s3_key=s3_key, signed_at=now(), dsc_fingerprint=fingerprint)
    CM-->>CW: certificate_instance
    CW->>WE: WorkflowEngine.transition(application, trigger='issue_certificate', actor_id=SYSTEM_ACTOR)
    WE->>AM: application.status = 'CERTIFICATE_ISSUED'; application.certificate_id = certificate.id
    CW->>DLS: Nepal Document Wallet (NDW)Sync.push(citizen.digilocker_token_enc, signed_bytes, {cert_number, service_name, issued_date})
    Note over CW,DLS: Decrypt token with KMS before API call; handle token refresh if needed
    DLS-->>CW: {digilocker_uri: "in.gov.tn-revenue/income-certificate/cert_number"}
    CW->>CM: certificate.digilocker_uri = digilocker_uri
    CM-->>CW: Saved
    CW->>NS: NotificationService.send_certificate_ready(certificate, citizen)
    NS->>NS: SMS: "Your Income Certificate {cert_number} is ready. Download: {presigned_url}"
    NS->>NS: Email: Attached PDF + Nepal Document Wallet (NDW) link
    NS->>NS: In-App: Push notification via FCM
    CW->>CW: Task completed; log to audit_logs: CERTIFICATE_ISSUED
```

---

## SD-006: Grievance Escalation

This sequence shows how a grievance progresses through SLA-based automatic escalation.

```mermaid
sequenceDiagram
    participant CB as CitizenBrowser
    participant GP as GrievancePortal<br/>(Next.js)
    participant AC as ApiClient
    participant GCV as GrievanceCreateView
    participant GM as GrievanceModel
    participant CW as CeleryWorker<br/>(Celery Beat)
    participant GS as GrievanceService
    participant DH as DeptHeadUser
    participant SA as SuperAdmin
    participant NS as NotificationService

    CB->>GP: Citizen opens grievance portal and clicks "File Grievance"
    GP->>AC: POST /api/v1/grievances/ {application_id, category: "DELAY", description}
    AC->>GCV: POST with citizen JWT
    GCV->>GCV: GrievanceCreateSerializer.is_valid()
    GCV->>GM: GrievanceModel.objects.create(citizen=citizen, application=application, category='DELAY', status='FILED', sla_due_at=now()+timedelta(days=7))
    Note over GCV,GM: SLA: 7 days for standard grievances; 3 days for officer conduct grievances
    GM-->>GCV: grievance_instance
    GCV->>CW: acknowledge_grievance.delay(grievance_id)
    GCV-->>AC: HTTP 201 {grievance_id, status: "FILED", sla_due_at}
    AC-->>GP: Grievance filed confirmation
    GP-->>CB: Show grievance ID and SLA deadline

    CW->>GS: GrievanceService.acknowledge(grievance_id)
    GS->>GM: grievance.status = 'ACKNOWLEDGED'
    GS->>NS: Send acknowledgment SMS + Email to citizen with grievance ID
    GS->>NS: Notify department head of new grievance

    Note over CW: --- Celery Beat runs check_grievance_sla every 2 hours ---
    CW->>CW: Task: check_grievance_sla_breaches()
    CW->>GM: GrievanceModel.objects.filter(status__in=['FILED','ACKNOWLEDGED','ASSIGNED','UNDER_INVESTIGATION'], sla_due_at__lte=now()+timedelta(hours=24))
    GM-->>CW: [grievance_instance] (SLA within 24 hours)
    CW->>NS: NotificationService.send_sla_warning(grievance, assigned_to, dept_head)
    Note over CW: Warning sent 24 hours before SLA breach

    CW->>GM: GrievanceModel.objects.filter(status__not_in=['RESOLVED','CLOSED','ESCALATED'], sla_due_at__lt=now())
    GM-->>CW: [overdue_grievance_instance]
    CW->>GS: GrievanceService.auto_escalate(grievance_id)
    GS->>GM: grievance.status = 'ESCALATED'; grievance.escalated_at = now()
    GS->>NS: NotificationService.send_escalation_alert(grievance)
    NS->>NS: Email to Department Head: "Grievance {grievance_id} has breached SLA and been escalated"
    NS->>NS: Email to Super Admin: Escalation summary

    DH->>GP: Department Head reviews escalated grievance and assigns investigator
    GP->>AC: PATCH /api/v1/grievances/{grievance_id}/ {action: "assign", officer_id: X}
    AC->>GCV: PATCH with dept_head JWT
    GCV->>GS: GrievanceService.assign(grievance_id, officer_id=X, assigned_by=dept_head_id)
    GS->>GM: grievance.assigned_to = officer_id; grievance.status = 'ASSIGNED'
    GCV-->>AC: HTTP 200 {status: "ASSIGNED", assigned_to}

    Note over CW: --- If escalated grievance also breaches extended SLA ---
    CW->>GS: GrievanceService.refer_to_ombudsman(grievance_id)
    GS->>GM: grievance.status = 'OMBUDSMAN_REFERRED'
    GS->>SA: Email notification to Super Admin
    GS->>NS: Notify citizen: grievance referred to ombudsman
```

---

## 7. Implementation Notes

**JWT Token Strategy:** Access tokens (15-minute TTL) are stored in JavaScript memory only, never in `localStorage`. Refresh tokens (7-day TTL) are stored in `HttpOnly; Secure; SameSite=Strict` cookies to prevent XSS theft. The Next.js API routes act as a token refresh proxy, so the browser never directly touches the Django `/api/v1/auth/refresh-token/` endpoint.

**Redis Locking for Payments:** The `SET key NX EX 30` pattern in SD-003 is a critical idempotency guard. The lock TTL of 30 seconds covers the ConnectIPS API round-trip. If the application crashes after acquiring the lock but before releasing it, the 30-second TTL ensures the citizen can retry after the TTL expires. The unique partial index on `payments(application_id)` WHERE status NOT IN ('FAILED','REFUNDED') is an additional database-layer guard.

**Celery Queue Segregation:** Tasks are assigned to named queues: `documents` (malware scan), `notifications` (SMS/email dispatch), `certificates` (PDF generation, DSC signing), `payments` (webhook processing), `default` (everything else). Certificate generation uses a dedicated worker with 1 concurrency to manage DSC key access serially.

**Webhook Idempotency:** ConnectIPS webhooks are deduplicated by `gateway_txn_id` — the handler checks existing payment status before processing. The `select_for_update()` lock prevents concurrent webhook handlers from double-processing. A positive acknowledgment (`HTTP 200`) is returned immediately before the Celery task is dispatched.

**DSC Key Management:** The DSC PFX file is stored in AWS Secrets Manager, not on disk. The DSC signing service caches the loaded key in process memory for 1 hour, refreshing before expiry. This avoids repeated decryption cost while ensuring key rotation takes effect within 1 hour.

**Nepal Document Wallet (NDW) Push:** SD-005 shows a best-effort push. If `Nepal Document Wallet (NDW)Service.push()` raises an exception, the Celery task catches it, logs the failure to `audit_logs`, and schedules a `retry_digilocker_push.delay(cert_id)` task. The certificate is still issued; the Nepal Document Wallet (NDW) URI is populated later when the retry succeeds.

---

## 8. Operational Policy Addendum

### 8.1 Sequence Implementation Compliance Policy

Every sequence diagram in this document is considered an authoritative specification. Developer implementations must match the actor names, method signatures, and ordering shown. Deviations require a design review comment in the pull request explaining the rationale. The tech lead maintains this document and updates it when the implementation diverges to ensure diagrams remain current.

### 8.2 External API Call Policy

All calls to external services (NASC (National Identity Management Centre), Nepal Document Wallet (NDW), ConnectIPS, Nepal Telecom / Sparrow SMS gateway) must be wrapped in try/except blocks with timeout settings. Default HTTP timeout is 10 seconds; NASC (National Identity Management Centre) e-KYC is 20 seconds. Circuit breakers (using `circuitbreaker` library) are configured for ConnectIPS (threshold: 5 failures in 60 seconds, recovery: 30 seconds) and Nepal Document Wallet (NDW) (threshold: 10 failures in 120 seconds, recovery: 60 seconds). All external call durations are emitted as CloudWatch metrics.

### 8.3 Celery Task Reliability Policy

All Celery tasks must be idempotent — safe to run multiple times with the same arguments. Tasks must not mutate shared province without database transactions. Celery task results (success/failure) are logged to `audit_logs` by the task itself, not by the caller. The `default_retry_delay` and `max_retries` must be explicitly set on every task class. Dead-letter handling: tasks that exhaust retries write to a `failed_tasks` database table for manual remediation.

### 8.4 Sequence Security Policy

The NID OTP flow implements multiple anti-abuse controls visible in SD-001: rate limiting (3 requests per NID per 10 minutes via Redis counter), `txnId` invalidation after use, and a 24-hour used-txnId blacklist. The payment flow uses Redis locking and a database unique index as dual guards against double-charging. Webhook handlers validate HMAC signatures before any processing. All inter-service calls within AWS VPC use private endpoints; no traffic leaves the VPC for internal service communication.
