# System Sequence Diagram — Government Services Portal

## 1. Overview

System Sequence Diagrams (SSDs) describe the interactions between external actors and the internal system components for a specific use case, showing the sequence of messages, the actors involved, and the data exchanged. Each SSD in this document corresponds to a key system scenario and is labelled with a unique identifier (SSC-XXX) for traceability to requirements and test cases.

**Participants key used across all diagrams:**
- External actors are shown as `actor` nodes (Citizen, FieldOfficer, DepartmentHead).
- Internal system components are shown as `participant` nodes.
- Thick arrows (`->>`) indicate synchronous calls where the caller waits for a response.
- Dashed arrows (`-->>`) indicate synchronous responses.
- Notes (`Note over`) are used to indicate important business rules or validations.

**Error flows** are noted but not fully diagrammed for brevity. Each happy path diagram is accompanied by a written description of the primary error paths.

---

## 2. SSC-001: Citizen Registration and NID OTP Verification

**Description:** A new citizen visits the portal for the first time. They choose to register using their NID number. The system initiates an OTP to the mobile number linked to their NID account via NASC (National Identity Management Centre). The citizen enters the OTP, NASC (National Identity Management Centre) verifies it, the citizen's profile is created using e-KYC data, and a JWT is issued.

**Primary Error Paths:**
- NASC (National Identity Management Centre) returns `OTP_REQUEST_LIMIT_EXCEEDED`: System returns HTTP 429 with retry-after header.
- NASC (National Identity Management Centre) OTP verification fails (`OTP_INVALID`): System returns HTTP 400; after 5 failures, the session is locked for 30 minutes.
- Mobile number does not match NID-linked mobile: System informs citizen and suggests email OTP fallback.
- Citizen already registered with same NID token: System logs them in instead of re-registering (idempotent).

```mermaid
sequenceDiagram
    autonumber
    actor Citizen
    participant UI as BrowserUI<br/>(Next.js App)
    participant FE as NextJSFrontend<br/>(Server Component)
    participant API as DjangoAPI<br/>(auth/views.py)
    participant NASC (National Identity Management Centre) as NIDNASC (National Identity Management Centre)<br/>(AUA API v2)
    participant SMS as SMSGateway<br/>(MSG91)
    participant DB as PostgreSQL<br/>(identity schema)
    participant Cache as Redis<br/>(session store)

    Citizen->>UI: Navigate to /register, select "Register with NID"
    UI->>FE: GET /register (server-side render)
    FE-->>UI: Render registration form (NID number input + consent checkbox)

    Citizen->>UI: Enter NID number (12 digits), tick consent checkbox, click "Get OTP"
    UI->>UI: Client-side validation: Luhn-like NID checksum (Verhoeff algorithm)

    UI->>API: POST /api/auth/aadhaar/otp/initiate<br/>{ aadhaar_number: "XXXX XXXX XXXX", consent: true }
    Note over API: Rate limit check: max 5 OTP requests per IP per 10 min<br/>Validate consent = true (mandatory)

    API->>Cache: INCR ratelimit:otp:ip:{client_ip}<br/>GET current count
    Cache-->>API: count = 1 (within limit)

    API->>API: Encrypt NID number for NASC (National Identity Management Centre) transmission<br/>(RSA-2048 with NASC (National Identity Management Centre) public key)<br/>Generate txn_id (UUID v4)

    API->>NASC (National Identity Management Centre): POST https://auth.uidai.gov.in/otp<br/>{ uid: "<encrypted_aadhaar>", ac: "<AUA_code>",<br/>sa: "<sub_AUA>", ver: "2.0",<br/>txn: "<txn_id>", type: "A" }<br/>Request signed with AUA private key (pkcs1v15 + SHA-256)
    NASC (National Identity Management Centre)-->>API: HTTP 200 { ret: "y", txn: "<txn_id>",<br/>info: "OTP sent to registered mobile XXXXXX7891" }

    Note over API: NASC (National Identity Management Centre) sends OTP directly to citizen's<br/>NID-linked mobile — NOT via portal

    API->>Cache: SETEX otp_session:{txn_id} 300<br/>{ aadhaar_hash: SHA256(aadhaar), attempt_count: 0, ip: client_ip }
    API-->>UI: HTTP 200 { txn_id: "<txn_id>", expires_in: 300,<br/>masked_mobile: "XXXXXX7891" }

    UI->>Citizen: Display OTP entry screen with 5-minute countdown<br/>Show masked mobile number for confirmation

    Citizen->>UI: Enter 6-digit OTP received on mobile
    UI->>API: POST /api/auth/aadhaar/otp/verify<br/>{ txn_id: "<txn_id>", otp: "483921" }

    API->>Cache: GET otp_session:{txn_id}
    Cache-->>API: Session data (not expired, attempt_count < 5)
    API->>Cache: HINCRBY otp_session:{txn_id} attempt_count 1

    API->>API: Prepare PID block: encrypt OTP with<br/>NASC (National Identity Management Centre) session key (AES-256-GCM)<br/>Build XML Auth request per NASC (National Identity Management Centre) spec

    API->>NASC (National Identity Management Centre): POST https://auth.uidai.gov.in/auth<br/>{ uid: "<encrypted_aadhaar>", txn: "<txn_id>",<br/>pid: "<encrypted_pid_block_with_otp>",<br/>uses: { pi: "y", pa: "y", bio: "n" },<br/>ac: "<AUA_code>" }<br/>Signed with AUA key

    NASC (National Identity Management Centre)-->>API: HTTP 200 { ret: "y", txn: "<txn_id>",<br/>info: "<base64_encrypted_eKYC>" }

    API->>API: Decrypt e-KYC response using AUA session key<br/>Extract KYC: { name, dob, gender, address, co, pc }

    API->>DB: SELECT citizen_id FROM citizens<br/>WHERE aadhaar_token = SHA256(aadhaar + salt)
    DB-->>API: Empty result (new citizen)

    API->>DB: BEGIN TRANSACTION
    API->>DB: INSERT INTO citizens<br/>{ citizen_id: UUID, aadhaar_token: SHA256(aadhaar+salt),<br/>mobile: NASC (National Identity Management Centre)_linked_mobile,<br/>mobile_verified: true, aadhaar_verified: true,<br/>status: "ACTIVE", created_at: NOW() }
    API->>DB: INSERT INTO citizen_profiles<br/>{ profile_id: UUID, citizen_id: new_id,<br/>full_name: eKYC.name, date_of_birth: eKYC.dob,<br/>gender: eKYC.gender, address: eKYC.address,<br/>kyc_verified_at: NOW(), kyc_source: "AADHAAR_EKYC" }
    API->>DB: INSERT INTO consent_records<br/>{ citizen_id, consent_type: "AADHAAR_EKYC",<br/>consent_given: true, consent_at: NOW(),<br/>ip_address, user_agent, text_version: "v2.1" }
    API->>DB: COMMIT

    API->>DB: INSERT INTO audit_log<br/>{ event: "CITIZEN_REGISTERED", citizen_id,<br/>auth_type: "AADHAAR_OTP", ip_address, timestamp }

    API->>API: Generate RS256 JWT access token<br/>{ sub: citizen_id, role: "citizen",<br/>aadhaar_verified: true, exp: now+900 }
    API->>API: Generate RS256 JWT refresh token<br/>{ sub: citizen_id, type: "refresh", jti: UUID, exp: now+604800 }

    API->>Cache: SETEX session:{citizen_id} 604800<br/>{ refresh_jti: jti_hash, ip, user_agent, created_at }
    API->>Cache: DEL otp_session:{txn_id}

    API-->>UI: HTTP 201 { access_token, refresh_token,<br/>expires_in: 900, citizen_id, is_new_registration: true }
    Note over UI: Store access_token in React province (memory only)<br/>Set refresh_token in httpOnly Secure SameSite=Strict cookie

    UI->>Citizen: Redirect to /dashboard with welcome banner<br/>"Registration successful! Welcome, {name}."
```

---

## 3. SSC-002: Submit Service Application (Happy Path)

**Description:** An authenticated citizen selects a service (e.g., "Domicile Certificate"), checks eligibility, fills the multi-step form, uploads required documents, and submits the application. The workflow engine creates the first review step and the citizen receives an acknowledgement.

**Primary Error Paths:**
- Citizen is ineligible for the service: System displays the failing rule and suggests an alternative service.
- Uploaded document fails virus scan: System rejects the document and prompts re-upload.
- Payment fails or is abandoned: Application stays in `PENDING_PAYMENT` province; citizen can resume from their dashboard.
- Duplicate application detected (INV-009): System links citizen to their existing active application.

```mermaid
sequenceDiagram
    autonumber
    actor Citizen
    participant FE as Frontend<br/>(Next.js)
    participant API as DjangoAPI<br/>(application/views.py)
    participant WE as WorkflowEngine<br/>(workflow/services.py)
    participant S3 as AWS S3<br/>(document store)
    participant DB as PostgreSQL
    participant Cache as Redis
    participant NS as NotificationService<br/>(Celery task)

    Citizen->>FE: Browse service catalogue, select "Domicile Certificate"
    FE->>API: GET /api/services/DOM-001/<br/>Authorization: Bearer {access_token}
    API->>Cache: GET cache:service:DOM-001
    Cache-->>API: Cache miss
    API->>DB: SELECT * FROM services WHERE service_code = 'DOM-001'
    DB-->>API: Service record (schema, docs, fee, SLA)
    API->>Cache: SETEX cache:service:DOM-001 300 {service_data}
    API-->>FE: HTTP 200 { service, form_schema, required_documents, fee_schedule }

    FE->>API: GET /api/services/DOM-001/eligibility/<br/>Authorization: Bearer {access_token}
    API->>DB: SELECT * FROM citizen_profiles WHERE citizen_id = {sub}
    DB-->>API: CitizenProfile (name, dob, address, category)
    API->>API: EligibilityService.check(service=DOM-001, profile=profile)<br/>Rule eval: age >= 18 ✓, domicile_state == service_state ✓,<br/>no existing valid domicile cert ✓
    API-->>FE: HTTP 200 { is_eligible: true, form_prefill: { name, dob, address } }

    FE->>Citizen: Render multi-step form (Step 1: Personal Details pre-filled)
    Citizen->>FE: Complete form steps 1-4 (personal, family, address, declaration)

    Note over FE: Client-side validation at each step<br/>using JSON Schema (Ajv library)

    FE->>API: POST /api/applications/draft/<br/>{ service_id: "DOM-001-uuid", form_data: { ...validated_form... } }
    API->>DB: INSERT INTO applications { status: "DRAFT", form_data, citizen_id, service_id, created_at }
    DB-->>API: { application_id: "app-uuid-xxx" }
    API-->>FE: HTTP 201 { application_id, draft_number }

    loop For each required document (address_proof, age_proof, photo)
        Citizen->>FE: Select file to upload
        FE->>API: POST /api/applications/{app_id}/documents/upload-url/<br/>{ document_type: "address_proof", filename: "aadhaar_card.pdf",<br/>mime_type: "application/pdf", file_size: 524288 }
        API->>API: Validate: mime_type in allowed list ✓, size <= 5MB ✓
        API->>S3: generate_presigned_url(method=PUT,<br/>key=documents/{app_id}/{uuid}/address_proof.pdf,<br/>expiry=900, conditions=[ContentType, ContentLength])
        S3-->>API: Presigned PUT URL (15-min TTL)
        API->>DB: INSERT INTO application_documents { status: "UPLOAD_PENDING", s3_key, document_type }
        API-->>FE: HTTP 200 { upload_url, document_id }
        FE->>S3: PUT {upload_url}<br/>Content-Type: application/pdf<br/>Binary file data (direct browser upload, bypasses Django)
        S3-->>FE: HTTP 200 { ETag, VersionId }
        FE->>API: POST /api/applications/{app_id}/documents/{doc_id}/confirm/<br/>{ etag: "abc123", version_id: "vXXX" }
        API->>DB: UPDATE application_documents SET status = "UPLOADED", etag, version_id
        API->>Cache: LPUSH celery:queue:document scan_task:{doc_id}
        Note over API: ClamAV scan runs async (Celery document queue)<br/>App continues immediately
        API-->>FE: HTTP 200 { status: "uploaded", scan_status: "pending" }
    end

    FE->>API: GET /api/applications/{app_id}/documents/scan-status/
    Note over API: Poll until all documents = "CLEAN" (or timeout 120s)
    API->>DB: SELECT scan_status FROM application_documents WHERE app_id = ?
    DB-->>API: [ { doc_type: "address_proof", scan_status: "CLEAN" }, ... all CLEAN ]
    API-->>FE: HTTP 200 { all_clean: true }

    FE->>API: GET /api/applications/{app_id}/fee/
    API->>DB: SELECT fee_schedule FROM services JOIN fee_schedule_items ...
    API->>API: FeeCalculationService.calculate(service=DOM-001, profile=citizen_profile)<br/>Base fee: रू100, BPL waiver: -रू50 (citizen has BPL card), Net: रू50
    API->>DB: INSERT INTO fees { base_amount: 100, waiver_amount: 50, net_amount: 50 }
    API-->>FE: HTTP 200 { fee_id, base: 100, waiver: 50, net_payable: 50, waiver_reason: "BPL_CARD" }

    FE->>Citizen: Show fee summary with waiver applied, "Proceed to Pay" button
    Citizen->>FE: Click "Proceed to Pay"

    FE->>API: POST /api/payments/initiate/<br/>{ application_id, fee_id, method: "eSewa/Khalti/ConnectIPS" }
    API->>API: Generate idempotency_key = SHA256(application_id + fee_id)
    API->>DB: Check existing payment with same idempotency_key (prevent duplicate)
    Note over API: External payment flow (SSC-003) occurs here<br/>Returns with payment_confirmed = true
    API-->>FE: { payment_id, confirmed: true, txn_id: "PAY-XXXXXX" }

    FE->>API: POST /api/applications/{app_id}/submit/<br/>{ payment_id }
    API->>DB: SELECT * FROM applications WHERE id = app_id FOR UPDATE
    API->>API: ServiceApplication.submit()<br/>Validate: all docs CLEAN ✓, fee PAID ✓, form_data valid ✓<br/>Generate application_number: "MH/DOM/2024/000042371"
    API->>DB: UPDATE applications SET status = "SUBMITTED",<br/>application_number = "MH/DOM/2024/000042371", submitted_at = NOW()
    API->>WE: ApplicationSubmitted event → trigger_initial_workflow(app_id)
    WE->>DB: INSERT INTO workflow_instances { app_id, current_state: "SUBMITTED", created_at }
    WE->>DB: INSERT INTO workflow_steps { step_name: "INITIAL_REVIEW",<br/>assigned_to: null, department_id, due_at: now + 5 working days,<br/>status: "PENDING" }
    WE-->>API: { workflow_id, first_step_id }

    API->>S3: PUT ack_{app_id}.pdf (generate acknowledgement PDF via WeasyPrint)
    S3-->>API: { ack_s3_key }
    API->>DB: UPDATE applications SET ack_s3_key = ?

    API->>Cache: LPUSH celery:queue:default notify_application_submitted:{app_id}
    API-->>FE: HTTP 200 { application_number: "MH/DOM/2024/000042371",<br/>submitted_at, ack_download_url: presigned_s3_url,<br/>expected_completion: "2024-12-20" }

    FE->>Citizen: Show confirmation page with application number,<br/>download acknowledgement button, and tracking info

    NS->>Citizen: SMS: "Application MH/DOM/2024/000042371 submitted successfully.\nTrack: https://portal.gov.in/t/XXXXXXX"
    NS->>Citizen: Email: Acknowledgement with PDF attached
```

---

## 4. SSC-003: Fee Payment via ConnectIPS

**Description:** A citizen with a submitted application (or one pending payment) initiates fee payment through ConnectIPS. ConnectIPS hosts the payment page. On completion, ConnectIPS sends a callback to the portal, which records the payment and updates the application status.

**Primary Error Paths:**
- ConnectIPS callback signature validation fails: Payment is marked suspicious; Celery reconciliation job resolves within 24 hours.
- Citizen abandons payment on ConnectIPS: Application remains in `PENDING_PAYMENT`; citizen can retry from dashboard.
- ConnectIPS returns payment failure: System records failure, presents retry option, sends failure notification.
- Webhook is received but application payment already confirmed (duplicate callback): Idempotency key prevents double-recording; 200 OK returned to ConnectIPS with no DB write.

```mermaid
sequenceDiagram
    autonumber
    actor Citizen
    participant FE as Frontend<br/>(Next.js)
    participant API as DjangoAPI<br/>(payment/views.py)
    participant PAYGOV as ConnectIPSGateway<br/>(payment.gov.in)
    participant DB as PostgreSQL
    participant Worker as CeleryWorker<br/>(payment queue)
    participant NS as NotificationService

    Citizen->>FE: Click "Pay Fee" on application dashboard<br/>Application: MH/DOM/2024/000042371, Amount: रू50
    FE->>API: POST /api/payments/initiate/<br/>{ application_id: "app-uuid", fee_id: "fee-uuid",<br/>return_url: "https://portal.gov.in/payment/callback" }
    API->>DB: SELECT fee FROM fees WHERE id = fee_id AND application_id = app_id
    DB-->>API: { net_amount: 50.00, status: "UNPAID" }
    API->>DB: SELECT payment FROM payments<br/>WHERE application_id = ? AND status = "CONFIRMED"
    DB-->>API: Empty (no confirmed payment yet)

    API->>API: Generate ConnectIPS order payload:<br/>{ merchant_id: GOVT_MERCHANT_ID,<br/>order_id: "PG-{application_number}-{timestamp}",<br/>amount: "50.00", currency: "NPR",<br/>return_url, notify_url: "https://api.portal.gov.in/api/payments/callback/",<br/>customer_id: citizen_id }
    API->>API: Sign payload with HMAC-SHA256 using ConnectIPS merchant secret

    API->>PAYGOV: POST https://payment.gov.in/v1/orders/create<br/>{ signed_payload }
    PAYGOV-->>API: HTTP 200 { order_id: "PG-MH-DOM-2024-000042371-1701234567",<br/>payment_url: "https://payment.gov.in/pay/PG-MH-DOM...",<br/>expires_at: "2024-12-15T10:45:00Z" }

    API->>DB: INSERT INTO payments<br/>{ payment_id: UUID, application_id, fee_id,<br/>gateway_order_id: "PG-MH-DOM...",<br/>amount: 50.00, method: "PAYGOV",<br/>status: "INITIATED", initiated_at: NOW() }
    API->>DB: UPDATE applications SET status = "PENDING_PAYMENT"

    API-->>FE: HTTP 200 { payment_id, payment_url, expires_in: 900 }
    FE->>Citizen: Redirect to ConnectIPS payment page (full page redirect)

    Note over Citizen,PAYGOV: Citizen completes payment on ConnectIPS<br/>(eSewa/Khalti/ConnectIPS / Net Banking / Debit Card)

    PAYGOV->>Citizen: Redirect to return_url after payment attempt<br/>"https://portal.gov.in/payment/callback?order_id=PG-MH...&status=SUCCESS"
    Citizen->>FE: Browser follows redirect to payment callback page
    FE->>FE: Extract order_id from URL query params
    FE->>API: GET /api/payments/{payment_id}/status/<br/>Authorization: Bearer {access_token}
    Note over API: Do NOT trust return URL status param<br/>Always verify server-side via ConnectIPS API
    API->>PAYGOV: GET https://payment.gov.in/v1/orders/{gateway_order_id}/status<br/>Authorization: HMAC-signed request
    PAYGOV-->>API: { order_id, txn_id: "TXN8472641920",<br/>status: "PAID", amount: "50.00",<br/>payment_method: "eSewa/Khalti/ConnectIPS", paid_at: "2024-12-15T10:42:33Z" }

    API->>DB: UPDATE payments SET status = "CONFIRMED",<br/>gateway_txn_id = "TXN8472641920", confirmed_at = NOW()
    API->>DB: UPDATE fees SET status = "PAID", paid_at = NOW()
    API->>DB: UPDATE applications SET status = "SUBMITTED"
    Note over API: Emit PaymentConfirmed domain event<br/>→ triggers workflow to proceed

    API->>DB: INSERT INTO audit_log { event: "PAYMENT_CONFIRMED",<br/>citizen_id, payment_id, amount, txn_id, timestamp }
    API-->>FE: HTTP 200 { payment_status: "CONFIRMED", txn_id, amount, receipt_url }
    FE->>Citizen: Show payment success page with receipt download link

    Note over PAYGOV,API: ConnectIPS also sends async webhook callback (server-to-server)
    PAYGOV->>API: POST /api/payments/callback/<br/>{ order_id, txn_id, status: "SUCCESS",<br/>amount, signature: HMAC-SHA256 }
    API->>API: Validate HMAC-SHA256 signature using ConnectIPS secret<br/>Compare amount with expected (anti-tampering check)
    API->>DB: SELECT payment WHERE gateway_order_id = order_id
    DB-->>API: Payment (status = "CONFIRMED" — already processed)
    Note over API: Idempotent: already confirmed, skip DB write
    API->>Worker: LPUSH celery:queue:payment reconcile_payment:{payment_id}
    API-->>PAYGOV: HTTP 200 { received: true }

    Worker->>DB: Mark payment as reconciled, log reconciliation timestamp
    Worker->>NS: Enqueue notification: payment_receipt_email + sms
    NS->>Citizen: SMS: "Payment of रू50 confirmed. Ref: TXN8472641920.\nApplication: MH/DOM/2024/000042371"
    NS->>Citizen: Email: Payment receipt PDF attached
```

---

## 5. SSC-004: Field Officer Reviews Application

**Description:** A Field Officer logs into the admin portal, picks an application from their review queue, reviews the form and documents, and either requests clarification from the citizen or makes an approve/reject decision.

**Primary Error Paths:**
- Officer tries to review an application outside their department: API returns HTTP 403 Forbidden.
- Application is already being reviewed by another officer (concurrent review): Optimistic lock prevents double assignment; second officer sees "already claimed" message.
- Citizen does not respond to clarification within the SLA: System auto-escalates to Department Head after configured waiting period.

```mermaid
sequenceDiagram
    autonumber
    actor Officer as FieldOfficer
    participant AP as AdminPortal<br/>(Next.js Admin)
    participant API as DjangoAPI<br/>(application + workflow)
    participant WE as WorkflowEngine
    participant DB as PostgreSQL
    participant NS as NotificationService

    Officer->>AP: Login to staff portal, navigate to "My Review Queue"
    AP->>API: GET /api/admin/applications/queue/<br/>Authorization: Bearer {staff_jwt}
    API->>API: Extract officer_id and department_id from JWT claims<br/>Validate role = "FIELD_OFFICER"
    API->>DB: SELECT applications WHERE department_id = {officer_dept}<br/>AND status = "SUBMITTED"<br/>AND (assigned_to IS NULL OR assigned_to = officer_id)<br/>ORDER BY sla_due_at ASC<br/>LIMIT 20
    DB-->>API: List of 20 applications with service name, citizen name,<br/>submitted_at, sla_due_at, sla_risk_flag
    API-->>AP: HTTP 200 { applications: [...], total_pending: 147 }
    AP->>Officer: Display queue with SLA countdown badges (green/yellow/red)

    Officer->>AP: Click application "MH/DOM/2024/000042371"
    AP->>API: GET /api/admin/applications/app-uuid-xxx/detail/<br/>Authorization: Bearer {staff_jwt}
    API->>DB: SELECT application JOIN citizen_profiles JOIN services<br/>JOIN application_documents JOIN fees JOIN payments<br/>WHERE application_id = app-uuid-xxx
    DB-->>API: Full application detail with all related data
    API->>DB: INSERT INTO audit_log { event: "APPLICATION_VIEWED",<br/>officer_id, application_id, timestamp }
    API-->>AP: HTTP 200 { application, citizen_profile, documents, fee, payment, workflow_history }

    AP->>Officer: Render application detail view:<br/>form data, document previews, fee receipt, workflow timeline

    Officer->>AP: Click "Claim Application" (assigns to self)
    AP->>API: POST /api/admin/applications/app-uuid-xxx/claim/<br/>Authorization: Bearer {staff_jwt}
    API->>DB: UPDATE workflow_steps SET assigned_to = officer_id, claimed_at = NOW()<br/>WHERE step_id = step-uuid AND assigned_to IS NULL
    Note over API: Optimistic lock: returns 409 if assigned_to was already set<br/>by another officer in concurrent request
    DB-->>API: 1 row updated (success)
    API->>DB: INSERT INTO audit_log { event: "APPLICATION_CLAIMED", officer_id, application_id }
    API-->>AP: HTTP 200 { claimed: true, officer_name, claimed_at }

    Officer->>AP: Review form data and download document previews
    AP->>API: GET /api/admin/applications/app-uuid-xxx/documents/{doc_id}/view/<br/>Authorization: Bearer {staff_jwt}
    API->>API: Verify officer has permission to access this document
    API->>DB: INSERT INTO pii_access_log { officer_id, document_id, access_type: "VIEW", timestamp }
    API->>DB: SELECT s3_key FROM application_documents WHERE id = doc_id
    API->>DB: SELECT temporary presigned URL via boto3<br/>s3.generate_presigned_url(key=s3_key, expiry=300)
    API-->>AP: HTTP 200 { document_url: presigned_s3_url_300s }
    AP->>Officer: Open document in embedded PDF viewer (iframe with CSP)

    alt Officer finds missing information — requests clarification
        Officer->>AP: Click "Request Clarification",<br/>enter remarks: "Please upload recent utility bill as address proof (< 3 months old)"
        AP->>API: POST /api/admin/applications/app-uuid-xxx/clarification/<br/>{ remarks: "Please upload recent utility bill..." }
        API->>WE: trigger_transition(app_id, event="REQUEST_CLARIFICATION",<br/>actor=officer_id, remarks=remarks)
        WE->>DB: UPDATE applications SET status = "PENDING_CLARIFICATION"
        WE->>DB: UPDATE workflow_steps SET status = "WAITING_FOR_CITIZEN",<br/>clarification_remarks = remarks, clarification_requested_at = NOW()
        WE->>DB: INSERT INTO workflow_audit_trail { from_state: "UNDER_REVIEW",<br/>to_state: "PENDING_CLARIFICATION", event, actor, remarks, timestamp }
        API->>NS: Enqueue notification: clarification_requested {citizen_id, app_id, remarks}
        NS->>Citizen: SMS + Email: "Additional information required for MH/DOM/2024/000042371.\nRemarks: Please upload recent utility bill...\nPlease respond within 7 days."
        API-->>AP: HTTP 200 { status: "PENDING_CLARIFICATION", citizen_notified: true }
        AP->>Officer: Show confirmation, application removed from active queue

    else Officer approves the application
        Officer->>AP: Click "Approve", enter remarks: "All documents verified. Domicile claim validated."
        AP->>API: POST /api/admin/applications/app-uuid-xxx/decision/<br/>{ decision: "APPROVE", remarks: "All documents verified..." }
        API->>WE: trigger_transition(app_id, event="OFFICER_APPROVE",<br/>actor=officer_id, remarks=remarks)
        WE->>WE: Check service workflow: DOM-001 requires Dept Head final approval
        WE->>DB: UPDATE applications SET status = "PENDING_FINAL_APPROVAL"
        WE->>DB: UPDATE workflow_steps (current) SET status = "COMPLETED",<br/>decision = "APPROVED", completed_at = NOW()
        WE->>DB: INSERT INTO workflow_steps (next step: "FINAL_APPROVAL",<br/>assigned_to: dept_head_id, due_at: now + 2 working days)
        API->>NS: Enqueue notification: application_forwarded_to_dept_head
        NS->>Citizen: SMS: "Your application MH/DOM/2024/000042371 has been reviewed and forwarded for final approval."
        API-->>AP: HTTP 200 { status: "PENDING_FINAL_APPROVAL", next_step: "FINAL_APPROVAL" }

    else Officer rejects the application
        Officer->>AP: Click "Reject", select rejection reason: "DOCUMENT_INVALID",<br/>enter details: "Submitted address proof is expired (dated 2019)"
        AP->>API: POST /api/admin/applications/app-uuid-xxx/decision/<br/>{ decision: "REJECT", reason_code: "DOCUMENT_INVALID",<br/>rejection_details: "Address proof expired..." }
        API->>WE: trigger_transition(app_id, event="OFFICER_REJECT",<br/>actor=officer_id, reason=rejection_details)
        WE->>DB: UPDATE applications SET status = "REJECTED",<br/>rejection_reason = rejection_details, rejected_at = NOW()
        WE->>DB: UPDATE workflow_steps SET status = "COMPLETED",<br/>decision = "REJECTED", completed_at = NOW()
        API->>NS: Enqueue notification: application_rejected {citizen_id, reason}
        NS->>Citizen: SMS + Email: "Application MH/DOM/2024/000042371 rejected.\nReason: Address proof expired.\nYou may file a grievance or re-apply."
        API-->>AP: HTTP 200 { status: "REJECTED", citizen_notified: true }
    end
```

---

## 6. SSC-005: Certificate Issuance by Department Head

**Description:** After a Field Officer forwards an application for final approval, the Department Head reviews it and approves it. The system triggers certificate generation: a PDF is generated, digitally signed using DSC, uploaded to S3, pushed to the citizen's Nepal Document Wallet (NDW), and the citizen is notified.

**Primary Error Paths:**
- DSC HSM signing fails (token not connected, PIN locked): Task retried up to 3 times; after 3 failures, P1 alert raised to platform team. Certificate job marked `SIGNING_FAILED`; manual intervention required.
- Nepal Document Wallet (NDW) push fails (citizen has not linked Nepal Document Wallet (NDW)): Certificate is still issued and available for download from portal. Nepal Document Wallet (NDW) push is retried for 7 days before being marked permanently failed.
- Certificate template rendering fails (missing data field): Error captured in Sentry; certificate job marked `GENERATION_FAILED`; alert sent to backend team.

```mermaid
sequenceDiagram
    autonumber
    actor DeptHead as DepartmentHead
    participant API as DjangoAPI<br/>(application + certificate)
    participant WE as WorkflowEngine
    participant DB as PostgreSQL
    participant DSC as DSCSigningService<br/>(Celery document worker)
    participant S3 as AWS S3
    participant DL as Nepal Document Wallet (NDW)API
    participant NS as NotificationService
    actor Citizen

    DeptHead->>API: POST /api/admin/applications/{app_id}/final-approval/<br/>{ decision: "APPROVE",<br/>remarks: "Domicile verified, all documents in order." }
    API->>API: Validate JWT: role = "DEPT_HEAD",<br/>department_id matches application.department_id
    API->>WE: trigger_transition(app_id, event="FINAL_APPROVAL", actor=dept_head_id)
    WE->>DB: UPDATE applications SET status = "APPROVED", approved_at = NOW()
    WE->>DB: UPDATE workflow_steps (FINAL_APPROVAL step) SET status = "COMPLETED",<br/>decision = "APPROVED", completed_at = NOW()
    WE->>DB: INSERT INTO workflow_audit_trail { event: "FINAL_APPROVAL",<br/>actor: dept_head_id, remarks, timestamp }
    WE->>DB: INSERT INTO certificate_generation_jobs<br/>{ job_id: UUID, application_id, service_id, citizen_id,<br/>status: "QUEUED", created_at: NOW() }
    WE->>DB: UPDATE applications SET cert_generation_job_id = job_id

    WE->>DSC: LPUSH celery:queue:document generate_certificate:{job_id}
    API-->>DeptHead: HTTP 200 { status: "APPROVED",<br/>message: "Certificate generation initiated", job_id }

    DSC->>DB: SELECT cert_job, application, citizen_profile,<br/>service, fee, payment, approved_by FROM ...<br/>WHERE cert_job.id = job_id
    DB-->>DSC: Full data required for certificate

    DSC->>DB: UPDATE certificate_generation_jobs SET status = "GENERATING"

    DSC->>DSC: Load certificate template:<br/>templates/certificates/DOM-001-domicile.html.j2<br/>Render with Jinja2:<br/>{ citizen_name, dob, address, father_name,<br/>issue_date, cert_number: UUID-based,<br/>qr_verification_url, dept_head_name, seal }

    DSC->>DSC: Convert rendered HTML → PDF/A-3 via WeasyPrint<br/>Embed metadata: creator, producer, subject, keywords<br/>Generate SHA-256 hash of PDF bytes

    DSC->>S3: PUT documents/certificates/draft/{cert_id}.pdf<br/>SSE-KMS: true, ContentType: application/pdf
    S3-->>DSC: { ETag, VersionId }

    DSC->>DSC: Initialize PKCS#11 interface to HSM<br/>(AWS CloudHSM or physical USB HSM token)<br/>Login with HSM PIN from Secrets Manager<br/>Locate signing key by DSC label "DEPT_DOM_CLASS3_2024"

    DSC->>DSC: Sign PDF using PKCS#7 detached signature<br/>(pkcs11-tool or pyhanko library)<br/>Signature embedded in PDF /ByteRange<br/>Algorithm: RSA-2048 + SHA-256<br/>Certificate chain: Leaf → SubCA → CCA Root

    DSC->>DSC: Verify signature post-signing:<br/>Extract signature, validate against DSC certificate,<br/>check CRL (or OCSP) for DSC revocation status
    Note over DSC: Verification failure triggers retry and P1 alert

    DSC->>S3: PUT documents/certificates/signed/{cert_id}.pdf<br/>S3 Object Lock: ComplianceMode, RetainUntil: now + 20 years<br/>SSE-KMS: true
    S3-->>DSC: { ETag, VersionId: final_version }
    DSC->>S3: DELETE documents/certificates/draft/{cert_id}.pdf

    DSC->>DB: INSERT INTO certificates<br/>{ cert_id, cert_number, application_id, citizen_id, service_id,<br/>s3_key: "documents/certificates/signed/{cert_id}.pdf",<br/>s3_version_id, valid_from: today, valid_until: today + service.validity_years,<br/>dsc_serial, dsc_thumbprint, status: "ISSUED",<br/>verification_url: "https://portal.gov.in/verify/{cert_uuid}",<br/>issued_at: NOW() }
    DSC->>DB: UPDATE certificate_generation_jobs SET status = "COMPLETED", cert_id

    DSC->>DL: POST https://api.digitallocker.gov.in/public/oauth2/1/pull-uri/file<br/>Authorization: Bearer {citizen_digilocker_token}<br/>{ doctype: "DOMCRT", org_id: "DEPT_DOM",<br/>doc_name: "Domicile Certificate 2024",<br/>uri: s3_presigned_url_of_signed_cert, date: today,<br/>valid_from, valid_till }
    DL-->>DSC: HTTP 200 { push_uri: "digi:DOMCRT:XXXXXX",<br/>status: "SUCCESS" }

    DSC->>DB: UPDATE certificates SET digilocker_uri = "digi:DOMCRT:XXXXXX",<br/>digilocker_synced_at = NOW()
    DSC->>DB: INSERT INTO audit_log { event: "CERTIFICATE_ISSUED",<br/>cert_id, citizen_id, dept_head_id, dsc_serial, timestamp }

    DSC->>NS: LPUSH celery:queue:default notify_certificate_issued<br/>{ citizen_id, cert_id, app_id,<br/>download_url: s3_presigned_15min,<br/>digilocker_uri, cert_number, valid_until }

    NS->>Citizen: SMS: "Your Domicile Certificate (Cert No: MH/DOM/2024/XXXXX) is ready.\nDownload: https://bit.ly/XXXXX | Nepal Document Wallet (NDW): https://digilocker.gov.in/XXXXX"
    NS->>Citizen: Email (HTML): Certificate issued notification with:<br/>Certificate number, validity, download button, Nepal Document Wallet (NDW) link, QR code image for verification
    NS->>DB: INSERT INTO notification_log { citizen_id, channel: "SMS", status: "SENT", sent_at }
    NS->>DB: INSERT INTO notification_log { citizen_id, channel: "EMAIL", status: "SENT", sent_at }
```

---

## 7. SSC-006: Grievance Filing and Resolution

**Description:** A citizen files a grievance regarding their rejected application (or a service-related complaint). The grievance is automatically routed to the concerned department. A Field Officer responds. If unresolved within SLA, it escalates to the Department Head.

**Primary Error Paths:**
- Citizen attempts to file a grievance after the 90-day appeal window: System returns HTTP 400 with `GrievanceWindowExpiredError`.
- Department does not respond within SLA (15 days): Celery Beat job detects overdue grievance and escalates to Department Head, sending alert.
- Grievance escalation to province grievance portal (CPGRAMS) is triggered by the Super Admin for unresolved complaints older than 30 days.

```mermaid
sequenceDiagram
    autonumber
    actor Citizen
    participant FE as Frontend<br/>(Next.js)
    participant API as DjangoAPI<br/>(grievance/views.py)
    participant DB as PostgreSQL
    participant NS as NotificationService
    actor Officer as FieldOfficer
    participant AP as AdminPortal
    participant Beat as CeleryBeat<br/>(SLA Checker)
    actor DeptHead as DepartmentHead

    Citizen->>FE: Navigate to rejected application MH/DOM/2024/000042371<br/>Click "File Grievance"
    FE->>API: GET /api/applications/{app_id}/grievance-eligibility/
    API->>DB: SELECT rejected_at FROM applications WHERE id = app_id
    DB-->>API: { rejected_at: "2024-12-10T14:30:00Z" }
    API->>API: Check: today - rejected_at = 5 days < 90 days (eligible)
    API-->>FE: HTTP 200 { eligible: true, window_closes_at: "2025-03-10" }

    Citizen->>FE: Fill grievance form:<br/>Category: "INCORRECT_REJECTION",<br/>Description: "My address proof (electricity bill dated Nov 2024) is valid but was rejected as expired. I am attaching a new copy."
    Citizen->>FE: Upload supporting document (electricity_bill_nov2024.pdf)
    FE->>API: POST /api/applications/{app_id}/grievances/<br/>{ category: "INCORRECT_REJECTION",<br/>description: "...", supporting_doc_url: s3_presigned }

    API->>DB: INSERT INTO grievances<br/>{ grievance_id: UUID, grievance_number: "GRV/MH/DOM/2024/000042371/001",<br/>citizen_id, application_id, category: "INCORRECT_REJECTION",<br/>description, status: "FILED",<br/>assigned_to_department: {original_dept_id},<br/>filed_at: NOW(), resolution_due_at: now + 15 working days }

    API->>DB: INSERT INTO audit_log { event: "GRIEVANCE_FILED",<br/>citizen_id, grievance_id, application_id, timestamp }

    API->>NS: Enqueue: grievance_filed_citizen_ack { citizen_id, grievance_number }
    API->>NS: Enqueue: grievance_filed_officer_alert { department_id, grievance_id }
    NS->>Citizen: SMS + Email: "Grievance GRV/MH/DOM/2024/000042371/001 filed.\nExpected resolution by 2025-01-03. Track: https://portal.gov.in/g/XXXXX"
    NS->>Officer: Email to department grievance inbox: "New grievance received for application MH/DOM/2024/000042371"

    API-->>FE: HTTP 201 { grievance_id, grievance_number, resolution_due_at }
    FE->>Citizen: Show grievance confirmation with tracking number

    Note over Officer,AP: Officer reviews grievance in Admin Portal

    Officer->>AP: Open grievance GRV/MH/DOM/2024/000042371/001
    AP->>API: GET /api/admin/grievances/{grievance_id}/
    API->>DB: SELECT grievance JOIN application JOIN citizen_profile JOIN documents
    DB-->>API: Full grievance detail with linked application and citizen documents
    API-->>AP: HTTP 200 { grievance_detail, application_summary, citizen_contact }

    Officer->>AP: Review original rejection and new supporting document
    AP->>API: GET /api/admin/grievances/{grievance_id}/documents/{doc_id}/view/
    Note over API: PII access logged for every officer document view
    API-->>AP: Presigned S3 URL for electricity bill

    Officer->>AP: Click "Resolve Grievance — Upheld"<br/>Remarks: "Electricity bill dated November 2024 is valid. Original rejection was incorrect. Application re-opened for review."
    AP->>API: POST /api/admin/grievances/{grievance_id}/resolve/<br/>{ decision: "UPHELD", remarks: "..." }

    API->>DB: UPDATE grievances SET status = "RESOLVED_UPHELD",<br/>resolved_at = NOW(), resolution_remarks = remarks,<br/>resolved_by = officer_id
    API->>DB: UPDATE applications SET status = "SUBMITTED",<br/>rejection_reason = NULL
    API->>DB: INSERT INTO workflow_steps { step_name: "INITIAL_REVIEW" (re-opened),<br/>assigned_to: officer_id, due_at: now + 5 working days }

    API->>NS: Enqueue: grievance_resolved { citizen_id, grievance_number, decision: "UPHELD" }
    NS->>Citizen: SMS + Email: "Good news! Your grievance GRV/MH/DOM/2024/000042371/001 has been upheld.\nYour application has been re-opened for review.\nExpected decision by 2025-01-08."
    API-->>AP: HTTP 200 { resolved: true, application_status: "SUBMITTED" }

    Note over Beat,DB: Celery Beat SLA checker runs every 15 minutes

    Beat->>DB: SELECT grievances WHERE status NOT IN ("RESOLVED_UPHELD","RESOLVED_REJECTED","CLOSED")<br/>AND resolution_due_at < NOW() + INTERVAL "2 days"
    DB-->>Beat: Overdue grievances list
    Beat->>DB: UPDATE grievances SET status = "ESCALATED",<br/>escalated_at = NOW(), escalated_to = dept_head_id
    Beat->>NS: Enqueue: grievance_escalated { dept_head_id, grievance_id, days_overdue }
    NS->>DeptHead: Email: "ESCALATION: Grievance {grievance_number} is overdue by {N} days and requires your immediate attention."
    NS->>Citizen: Email: "Your grievance {grievance_number} has been escalated to the Department Head for urgent resolution."
```

---

## 8. Sequence Diagram Notes

The following table summarises key technical decisions and patterns that are visible across the sequence diagrams above.

| # | Pattern / Decision | Diagrams | Technical Detail |
|---|---|---|---|
| SDN-001 | **Server-side JWT validation on every API call** | SSC-001 through SSC-006 | Django API extracts `sub`, `role`, `department_id` from RS256 JWT on every request. No session database lookup required for authentication. Refresh token is validated against Redis session store for revocation detection. |
| SDN-002 | **Direct-to-S3 document upload (pre-signed URLs)** | SSC-002 | Citizens upload documents directly to S3 using pre-signed PUT URLs. The Django API is never in the document upload data path, eliminating bandwidth bottleneck on API containers. API only handles metadata; S3 handles bytes. |
| SDN-003 | **Asynchronous virus scanning** | SSC-002 | ClamAV scan is non-blocking. The citizen can fill other form steps while the scan runs. The submission endpoint polls for scan completion and blocks only at the final submit step. |
| SDN-004 | **Idempotency keys on payment operations** | SSC-003 | All ConnectIPS order creation requests include an idempotency key (`SHA256(application_id + fee_id)`). Webhook callbacks are processed with a Redis idempotency check to prevent duplicate payment confirmations even if ConnectIPS retries the webhook. |
| SDN-005 | **Never trust redirect-based payment status** | SSC-003 | When ConnectIPS redirects the citizen back to the portal, the portal always performs an active server-side status query to ConnectIPS's order API, ignoring any status in the redirect URL parameters. This prevents tampering with the redirect URL to bypass payment. |
| SDN-006 | **Optimistic locking for application claim** | SSC-004 | The `UPDATE workflow_steps SET assigned_to = ? WHERE step_id = ? AND assigned_to IS NULL` query uses the database's atomic update as the lock mechanism. A return of `0 rows affected` signals a concurrent claim by another officer (HTTP 409). |
| SDN-007 | **Immutable audit log entries** | SSC-001 through SSC-006 | Every state transition, document access, payment event, and login event creates an `INSERT INTO audit_log` record. There are no UPDATE or DELETE operations on the audit log table. The DB role has INSERT-only permission on this table. |
| SDN-008 | **DSC signing in Celery worker, not API server** | SSC-005 | Certificate signing is computationally intensive and involves HSM I/O. Running it in a dedicated Celery worker (document queue) prevents it from blocking API response threads. The worker has direct access to the HSM via PKCS#11 over a TLS connection to AWS CloudHSM. |
| SDN-009 | **Nepal Document Wallet (NDW) push is non-blocking** | SSC-005 | Certificate is marked as ISSUED in the portal database as soon as DSC signing completes. Nepal Document Wallet (NDW) push happens in the same Celery task but after the DB write. If Nepal Document Wallet (NDW) push fails, the certificate is still accessible on the portal; the push is retried asynchronously. |
| SDN-010 | **Celery Beat for SLA enforcement** | SSC-006 (escalation), SSC-002 (SLA tracking) | A Celery Beat job runs every 15 minutes to detect SLA breaches. It does NOT send notifications synchronously — it enqueues notification tasks. This means SLA alerts may lag by up to 15 minutes from the exact breach moment, which is acceptable per product SLA. |
| SDN-011 | **PII access logging for all officer document views** | SSC-004, SSC-006 | Every time an officer requests a document's presigned URL, an entry is written to the `pii_access_log` table before the URL is generated. This creates an auditable trail of who accessed which citizen document and when, even if the document was never actually opened (pre-signed URL generated but not fetched). |
| SDN-012 | **Application re-opening via grievance upheld** | SSC-006 | A grievance decision of `UPHELD` directly modifies the linked application's status from `REJECTED` back to `SUBMITTED` and creates a new workflow step, effectively reopening the application. This is a domain service operation within the Grievance context that crosses into the Application context via a published service call (not direct model access). |
