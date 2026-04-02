# Business Rules — Government Services Portal

## Overview

This document defines the authoritative business rules governing the Government Services Portal. Rules are grouped by domain. Each rule specifies the rule ID, description, trigger, condition, action, and regulatory basis.

---

## Domain 1 — Service Eligibility (BR-ELIG-001..012)

### BR-ELIG-001 — NID Verification Required for Registration
- **Description:** Every citizen must verify their identity using NID OTP before their account is activated.
- **Trigger:** Citizen attempts to complete registration.
- **Condition:** NID OTP verification has not been completed.
- **Action:** Block account activation. Citizen can only access public service catalog (read-only) until verified.
- **Regulatory Basis:** NID Act 2016, Section 8 — authentication use for electronic services.

### BR-ELIG-002 — One Account per NID Number
- **Description:** No two citizen accounts may share the same NID number.
- **Trigger:** New citizen registration or identity re-verification.
- **Condition:** NID hash (SHA-256 of NID + salt) already exists in the identity table.
- **Action:** Block registration. Redirect to account recovery.
- **Regulatory Basis:** Prevention of fraudulent duplicate benefit avoidance.

### BR-ELIG-003 — Age Eligibility Enforcement
- **Description:** Services with minimum age requirements must validate the applicant's age from NID-verified date of birth.
- **Trigger:** Application submission.
- **Condition:** Citizen's NID-verified DoB gives an age below the configured service minimum age (or above maximum age if configured).
- **Action:** Block submission. Display age eligibility message with the applicable rule.
- **Regulatory Basis:** Service-specific government orders (e.g., pension scheme eligibility, youth scholarships).

### BR-ELIG-004 — Income-Based Eligibility (BPL / Category)
- **Description:** Services targeted at Below Poverty Line (BPL) citizens require a valid BPL card or income certificate.
- **Trigger:** Application submission for an income-restricted service.
- **Condition:** Citizen has not attached a valid income proof document (issued within 1 year).
- **Action:** Block submission. Prompt citizen to attach income certificate or apply for offline submission.
- **Regulatory Basis:** Targeted delivery guidelines under NREGA, PM-Jan Dhan Yojana, province welfare schemes.

### BR-ELIG-005 — Residency / Domicile Requirement
- **Description:** Province-specific services require proof of domicile (permanent resident certificate or ration card showing province address).
- **Trigger:** Application submission for a province-restricted service.
- **Condition:** Citizen's NID-linked address province does not match the service's jurisdiction province.
- **Action:** Block submission. Inform citizen about the domicile requirement and applicable documentation.
- **Regulatory Basis:** Province Domicile Certificate rules; inter-province service delivery guidelines.

### BR-ELIG-006 — No Active Pending Application for Same Service
- **Description:** A citizen cannot submit a new application for a service if they already have an active (non-rejected, non-expired) application for the same service.
- **Trigger:** New application submission.
- **Condition:** An application exists for the same citizen + service combination with status: DRAFT, SUBMITTED, PAYMENT_PENDING, UNDER_REVIEW, or PENDING_INFO.
- **Action:** Block submission. Show existing application's ARN and current status.
- **Regulatory Basis:** Prevention of duplicate benefit claims; administrative efficiency.

### BR-ELIG-007 — Service Availability by Jurisdiction
- **Description:** Services are only available to citizens within the configured jurisdiction (national, province, district).
- **Trigger:** Service catalog browse or application submission.
- **Condition:** Citizen's registered address is outside the service's jurisdiction boundary.
- **Action:** Hide service from catalog for out-of-jurisdiction citizens; block application if reached via direct URL.
- **Regulatory Basis:** Decentralised service delivery mandates.

### BR-ELIG-008 — Service Publication Province
- **Description:** Only services in PUBLISHED province are visible to citizens.
- **Trigger:** Service catalog query.
- **Condition:** Service status = DRAFT, ARCHIVED, or SUSPENDED.
- **Action:** Exclude from catalog. Return 404 for direct URL access.
- **Exception:** Officers and department heads can preview unpublished services.

### BR-ELIG-009 — Category-Based Reservation Eligibility
- **Description:** Services with reserved quotas (SC/ST/OBC/EWS) require documentary proof of category.
- **Trigger:** Application submission for a category-reserved service.
- **Condition:** Citizen claims a reserved category but has not attached a valid caste/category certificate.
- **Action:** Allow submission but flag as PENDING_VERIFICATION. Officer must verify category document before approval.
- **Regulatory Basis:** Constitution of Nepal, Articles 15, 16; reservation policy orders.

### BR-ELIG-010 — Minimum Document Age Constraints
- **Description:** Certain documents presented as eligibility proof must have been issued within a defined validity period.
- **Trigger:** Document attachment during application.
- **Condition:** Document issue date (extracted via OCR or Nepal Document Wallet (NDW) metadata) is older than the configured maximum age (e.g., income certificate > 1 year old).
- **Action:** Warn citizen that document may be too old; officer may reject if age exceeds threshold.
- **Regulatory Basis:** Government administrative circulars on document validity.

### BR-ELIG-011 — Prior Benefit Exhaustion Check
- **Description:** One-time benefit services (e.g., widow pension, subsidy for first house) cannot be applied for if the citizen has previously received the benefit.
- **Trigger:** Application submission.
- **Condition:** Legacy system records or previous approved application shows prior benefit for the same citizen + benefit type.
- **Action:** Block submission. Show reference to previous benefit with date.
- **Regulatory Basis:** Scheme-specific government orders preventing double-dipping.

### BR-ELIG-012 — Mandatory NID Linking for Financial Services
- **Description:** Applications for services involving financial disbursement (subsidy, pension, scholarship) must have an NID-linked bank account.
- **Trigger:** Application submission for a financial disbursement service.
- **Condition:** Citizen's profile does not have a bank account number verified against NPCI NID Mapper.
- **Action:** Block submission. Redirect citizen to bank account linking flow.
- **Regulatory Basis:** DBT (Direct Benefit Transfer) mandate; NID Seeding requirement.

---

## Domain 2 — Application Workflow (BR-APP-001..015)

### BR-APP-001 — Dynamic Form Versioning
- **Description:** Application forms are version-controlled. A submitted application captures the form version at submission time. Future form changes do not alter submitted applications.
- **Trigger:** Service form configuration update.
- **Action:** New version created; existing submitted applications retain reference to original form version.

### BR-APP-002 — Draft Expiry
- **Description:** Incomplete draft applications expire after 30 calendar days.
- **Trigger:** Celery Beat scheduler (daily at midnight).
- **Condition:** Application in DRAFT province; created_at < current_date − 30 days.
- **Action:** Transition to EXPIRED. Notify citizen with re-application option.

### BR-APP-003 — ARN Format Standard
- **Description:** Application Reference Number format: `{STATE_CODE}/{DEPT_CODE}/{YYYY}/{SEQ_7_DIGITS}` (e.g., `MH/RTO/2024/0012345`).
- **Trigger:** Application creation.
- **Action:** ARN generated using the defined format; unique constraint enforced at database level.

### BR-APP-004 — SLA Calculation Based on Working Days
- **Description:** Application processing deadlines are calculated in working days, excluding weekends and public holidays per the department's configured calendar.
- **Trigger:** Application submission (SUBMITTED province reached).
- **Action:** SLA deadline = submission date + service SLA (working days), evaluated against department holiday calendar.

### BR-APP-005 — Status Transition Validation
- **Description:** Application state machine enforces valid transitions only. Illegal transitions are rejected.
- **Valid Transitions:** DRAFT→SUBMITTED, SUBMITTED→UNDER_REVIEW, UNDER_REVIEW→PENDING_INFO, PENDING_INFO→UNDER_REVIEW, UNDER_REVIEW→APPROVED, UNDER_REVIEW→REJECTED, APPROVED→CERTIFICATE_ISSUED.
- **Action:** Any attempt to make an invalid transition raises a WorkflowViolationError (HTTP 409).

### BR-APP-006 — Auto-Assignment to Field Officer
- **Description:** Applications in SUBMITTED province are auto-assigned to field officers using weighted round-robin (lower current workload = higher assignment weight).
- **Trigger:** Application reaches SUBMITTED province.
- **Condition:** Service is in the officer's assigned zone and service type.
- **Action:** Application assigned; officer notified. If no eligible officer available, application placed in UNASSIGNED queue with department head alert.

### BR-APP-007 — Officer Reassignment Continuity
- **Description:** When a field officer's account is deactivated, all their UNDER_REVIEW applications are returned to the UNASSIGNED queue.
- **Trigger:** Field officer account deactivation.
- **Action:** All UNDER_REVIEW applications unassigned; SLA timers continue running; department head alerted.

### BR-APP-008 — Approval Requires Checklist Completion
- **Description:** An officer cannot approve an application unless all items on the service's verification checklist are marked as completed.
- **Trigger:** Officer attempts to approve application.
- **Condition:** Any checklist item is unchecked.
- **Action:** Block approval. Highlight incomplete items. Log attempted approval.

### BR-APP-009 — Rejection Reason Mandatory
- **Description:** Every rejection must include a reason code from the predefined list AND a free-text remark of at least 50 characters.
- **Trigger:** Officer submits rejection.
- **Condition:** Reason code absent OR remark length < 50 characters.
- **Action:** Block submission. Display validation error.

### BR-APP-010 — Pending Info Response Deadline
- **Description:** Citizens have 15 calendar days to submit additional information when requested by an officer. After this, the application auto-closes.
- **Trigger:** Application transitions to PENDING_INFO.
- **Action:** Set response_deadline = transition_date + 15. Celery Beat checks daily; send reminder at day 10 and day 14. Auto-close on day 15.

### BR-APP-011 — Maximum Applications Per Citizen Per Day
- **Description:** A citizen may not submit more than 10 applications per calendar day across all services (anti-abuse measure).
- **Trigger:** Application submission.
- **Condition:** Citizen has already submitted 10 applications today.
- **Action:** Block submission with rate-limit message. Log event for security review.

### BR-APP-012 — Officer Note Confidentiality
- **Description:** Officer internal notes are visible only to officers and department heads, never to the citizen.
- **Trigger:** Data retrieval for citizen dashboard.
- **Action:** Officer notes field excluded from citizen-facing API responses.

### BR-APP-013 — Application Immutability Post-Submission
- **Description:** Citizens cannot edit form fields after an application has been submitted (moved from DRAFT to SUBMITTED).
- **Trigger:** Edit attempt on a SUBMITTED or later-province application.
- **Action:** Return 403 Forbidden. Citizen can only add documents if specifically requested by officer (PENDING_INFO province).

### BR-APP-014 — Department Head Override Audit
- **Description:** When a department head overrides or reverses an officer's decision, the override must be documented with a reason and is permanently recorded in the audit trail.
- **Trigger:** Department head approves or rejects an application already actioned by an officer.
- **Action:** Override reason stored; previous decision history preserved; both officer and citizen notified.

### BR-APP-015 — Report Data Retention
- **Description:** Generated reports are retained on the system for 30 days, then archived to S3 Glacier for 7 years.
- **Trigger:** Report generation.
- **Action:** Report stored in S3 Standard; lifecycle policy transitions to Glacier after 30 days.

---

## Domain 3 — Document Management (BR-DOC-001..010)

### BR-DOC-001 — File Type Restriction
- **Description:** Only PDF, JPEG, and PNG file types are accepted for document uploads.
- **Trigger:** Document upload attempt.
- **Condition:** MIME type not in (application/pdf, image/jpeg, image/png).
- **Action:** Reject upload. Return HTTP 415 Unsupported Media Type.

### BR-DOC-002 — File Size Limit
- **Description:** Individual document files may not exceed 5 MB.
- **Trigger:** Document upload.
- **Condition:** File size > 5,242,880 bytes.
- **Action:** Reject upload. Inform citizen to compress or scan at lower resolution.

### BR-DOC-003 — Mandatory Virus Scanning
- **Description:** Every uploaded document must pass ClamAV antivirus scanning before storage.
- **Trigger:** Document upload.
- **Action:** Scan synchronously (timeout 30 seconds); if clean → store in S3; if infected → quarantine and alert.

### BR-DOC-004 — Server-Side Encryption at Rest
- **Description:** All documents stored in S3 must use SSE-S3 (AES-256) server-side encryption.
- **Trigger:** S3 PutObject call.
- **Action:** SSE-S3 encryption header applied. Unencrypted put requests are blocked by bucket policy.

### BR-DOC-005 — Document Versioning (No Overwrite)
- **Description:** When a citizen re-uploads a document for the same slot, the old version is retained and a new version created. Documents are never deleted before application closure.
- **Trigger:** Document re-upload for an existing document slot.
- **Action:** New DocumentSubmission record created; previous record marked SUPERSEDED.

### BR-DOC-006 — Document Retention Policy
- **Description:** Documents for approved applications are retained for 7 years. Documents for rejected/expired applications are retained for 2 years, then deleted.
- **Trigger:** S3 lifecycle rules; Celery batch job for DB record cleanup.
- **Regulatory Basis:** Public Records Act 1993; departmental records retention schedules.

### BR-DOC-007 — Nepal Document Wallet (NDW) Document Pull on Consent Only
- **Description:** The portal may only pull documents from Nepal Document Wallet (NDW) with explicit citizen consent per OAuth scope for each document pull.
- **Trigger:** Nepal Document Wallet (NDW) document pull request.
- **Condition:** Citizen has not authorised the specific document scope in the current OAuth session.
- **Action:** Re-initiate OAuth consent flow for the required scope.
- **Regulatory Basis:** Nepal Document Wallet (NDW) usage policy; IT Act 2000 consent requirements.

### BR-DOC-008 — Pre-Signed URL Expiry
- **Description:** S3 pre-signed URLs for document access expire within 1 hour for officer review and 30 seconds for citizen download.
- **Trigger:** Document access request.
- **Action:** Generate pre-signed URL with appropriate expiry; do not serve documents via public URLs.

### BR-DOC-009 — Document Deletion Under PDPA
- **Description:** A citizen's right-to-erasure (PDPA 2023) request for personal documents must be fulfilled for closed applications. Active application documents may not be deleted until application is resolved.
- **Trigger:** Citizen or DPO submits data erasure request.
- **Condition:** Application is in CLOSED, REJECTED, or EXPIRED province.
- **Action:** Delete documents from S3; retain anonymised metadata (file type, date, size) for audit.

### BR-DOC-010 — Certificate Document Immutability
- **Description:** Issued certificate PDFs are immutable. They may not be modified or deleted by any user including super admin. Only revocation (metadata flag) is permitted.
- **Trigger:** Any modification or deletion attempt on a certificate document.
- **Action:** Block with 403. Log attempted modification. Certificate revocation follows a separate revocation workflow.

---

## Domain 4 — Fee Collection (BR-FEE-001..010)

### BR-FEE-001 — Fee Calculation at Invoice Generation
- **Description:** Service fee is calculated at the time of invoice generation using the fee schedule active at submission date. Subsequent fee schedule changes do not affect existing invoices.
- **Trigger:** Application transitions to PAYMENT_PENDING.
- **Action:** Fee invoice generated with fee_amount, gst_amount (18%), total_amount; fee_schedule_version recorded.

### BR-FEE-002 — Duplicate Payment Prevention
- **Description:** If a payment webhook is received for an already-paid invoice, the duplicate is silently discarded (idempotent processing).
- **Trigger:** ConnectIPS webhook received.
- **Condition:** FeeInvoice already in PAID status.
- **Action:** Return HTTP 200 to ConnectIPS (to prevent retries); log duplicate event; no state change.

### BR-FEE-003 — Payment Deadline Enforcement
- **Description:** Fee payment must be completed within 7 days of invoice generation. After the deadline, the invoice expires and the application returns to DRAFT province.
- **Trigger:** Celery Beat daily check.
- **Condition:** FeeInvoice in UNPAID province; invoice_date < current_date − 7 days.
- **Action:** Invoice → EXPIRED; application → DRAFT (not PAYMENT_PENDING). Citizen notified.

### BR-FEE-004 — Fee Waiver Documentary Basis
- **Description:** Fee waivers must be backed by a verified document (BPL card, disability certificate, senior citizen ID — issued within 1 year).
- **Trigger:** Fee waiver request.
- **Condition:** Supporting document not attached or document age > 1 year.
- **Action:** Block waiver request. Prompt citizen to upload required proof.

### BR-FEE-005 — Fee Waiver One-Time Per Application
- **Description:** A fee waiver can only be approved once per application. Subsequent waiver requests for the same application are rejected.
- **Trigger:** Waiver approval attempt.
- **Condition:** Waiver already granted for this application.
- **Action:** Block duplicate waiver. Log attempt.

### BR-FEE-006 — Refund Trigger on System Error
- **Description:** If a citizen is charged twice due to a system error (confirmed by ConnectIPS reconciliation), a refund is automatically initiated to the original payment method.
- **Trigger:** Daily reconciliation job identifies duplicate charge.
- **Action:** Refund initiated via ConnectIPS refund API; citizen notified; financial record updated; incident logged.

### BR-FEE-007 — VAT (13%) Rate Configuration
- **Description:** VAT (13%) rate is a platform-configurable parameter (currently 18%). Changes take effect only on newly generated invoices.
- **Trigger:** Fee invoice generation.
- **Action:** Apply current active VAT (13%) rate. Store effective rate on the invoice record.
- **Regulatory Basis:** VAT (13%) Act 2017 — government services fee classification.

### BR-FEE-008 — ConnectIPS as Mandatory Gateway for Central Services
- **Description:** Federal government department services must use ConnectIPS as the primary payment gateway.
- **Trigger:** Service configuration.
- **Condition:** Department type = CENTRAL.
- **Action:** Block configuration of any gateway other than ConnectIPS for central department services.
- **Regulatory Basis:** Controller General of Accounts (CGA) mandate for GePG usage.

### BR-FEE-009 — Offline Challan Validity Period
- **Description:** Offline challans must be presented at the bank within 5 working days of generation.
- **Trigger:** Challan generation.
- **Action:** Set challan_expiry = generation_date + 5 working days. Expired challans not accepted by reconciliation.

### BR-FEE-010 — Receipt Mandatory on Payment
- **Description:** A government-format receipt (machine-readable PDF with receipt number, amount, service, date, department) must be generated for every completed payment.
- **Trigger:** Payment confirmed (webhook or reconciliation).
- **Action:** Generate receipt PDF; store in S3; email to citizen; link to application.
- **Regulatory Basis:** Government Financial Rules (GFR) 2017 — receipt for public money.

---

## Domain 5 — Grievance Redressal (BR-GRIEV-001..010)

### BR-GRIEV-001 — Grievance Filing Eligibility
- **Description:** Any registered citizen can file a grievance. Unregistered users cannot file grievances (prevents anonymous abuse).
- **Trigger:** Grievance submission.
- **Condition:** Session not authenticated.
- **Action:** Redirect to login. Preserve grievance draft in session storage.

### BR-GRIEV-002 — Grievance Category Mandatory
- **Description:** Every grievance must be categorised (rejection dispute, service delay, officer conduct, technical issue, other).
- **Trigger:** Grievance submission.
- **Condition:** Category field is blank.
- **Action:** Block submission. Display validation error.

### BR-GRIEV-003 — Auto-Assignment to Department Grievance Officer
- **Description:** Grievances linked to an application are auto-assigned to the department head of the linked application's department within 1 hour.
- **Trigger:** Grievance reaches OPEN province.
- **Action:** Celery task runs within 1 hour; assigns to department head; transitions to ASSIGNED; notifies.

### BR-GRIEV-004 — 30-Day Primary Resolution SLA
- **Description:** Grievances must be resolved or escalated within 30 calendar days of filing.
- **Trigger:** Grievance creation.
- **Action:** Set sla_deadline = filed_date + 30. Day 25: alert to officer. Day 30: auto-escalate.
- **Regulatory Basis:** DARPG CPGRAMS guidelines.

### BR-GRIEV-005 — Escalation on SLA Breach
- **Description:** Grievances not resolved within 30 days are automatically escalated to the senior authority (ministry-level officer).
- **Trigger:** Celery Beat check at midnight; condition: sla_deadline < current_date AND status not RESOLVED.
- **Action:** Transition to ESCALATED; assign to configured senior authority; citizen notified.

### BR-GRIEV-006 — Resolution Notes Visibility
- **Description:** Resolution notes are shared with the citizen after the grievance is marked RESOLVED.
- **Trigger:** Grievance status transitions to RESOLVED.
- **Action:** Resolution notes (excluding internal investigation details) published to citizen dashboard.

### BR-GRIEV-007 — Citizen Satisfaction Rating
- **Description:** Citizens have 7 days after grievance closure to rate the resolution quality (1–5 stars). Rating is optional.
- **Trigger:** Grievance transitions to RESOLVED.
- **Action:** Rating request notification sent. Rating recorded in GrievanceFeedback table.

### BR-GRIEV-008 — Duplicate Grievance Detection
- **Description:** If a citizen files more than one grievance for the same application within 30 days, the system warns before allowing the second submission.
- **Trigger:** Grievance submission.
- **Condition:** Open grievance exists for the same citizen + application.
- **Action:** Show warning with existing GRN. Citizen must confirm before proceeding.

### BR-GRIEV-009 — Grievance Record Retention
- **Description:** All grievance records (including evidence, correspondence, and resolution notes) are retained for 5 years.
- **Trigger:** Grievance closure.
- **Action:** Grievance archived after closure; accessible to auditor for 5 years before deletion.
- **Regulatory Basis:** CPGRAMS data retention guidelines.

### BR-GRIEV-010 — Officer Conduct Complaints Flagging
- **Description:** Grievances categorised as "officer conduct" are escalated directly to the department head (bypassing the officer) and flagged for HR review.
- **Trigger:** Grievance creation with category = OFFICER_CONDUCT.
- **Action:** Assign directly to department head; exclude the named officer from the resolution workflow; flag for HR module.

---

## Domain 6 — Certificate Issuance (BR-CERT-001..008)

### BR-CERT-001 — Certificate Issued Only on Approval
- **Description:** Certificate generation is triggered only when an application transitions to APPROVED province via a valid workflow path.
- **Trigger:** Application state machine: UNDER_REVIEW → APPROVED.
- **Action:** Asynchronous Celery task queued for certificate generation.

### BR-CERT-002 — DSC Signing Mandatory
- **Description:** Every issued certificate must bear the digital signature of the approving officer (DSC compliant with IT Act 2000, Section 5).
- **Trigger:** Certificate generation.
- **Condition:** DSC not available for the approving officer.
- **Action:** Certificate held in PENDING_SIGNATURE province. Department head alerted to provision DSC.
- **Regulatory Basis:** IT Act 2000, Section 5; Controller of Certifying Authorities (CCA) guidelines.

### BR-CERT-003 — QR Code Verification URL
- **Description:** Every certificate must include a QR code linking to the public certificate verification endpoint.
- **Trigger:** Certificate PDF generation.
- **Action:** QR code generated encoding URL: `https://portal.gov.in/verify/cert/{certificate_id}`; embedded in PDF footer.

### BR-CERT-004 — Certificate Serial Number Uniqueness
- **Description:** Certificate serial numbers are globally unique within the platform.
- **Format:** `{DEPT_CODE}/{YYYY}/{SERVICE_CODE}/{SEQ_8_DIGITS}` (e.g., `RTO/2024/DL/00012345`).
- **Action:** Unique constraint at database level; generation uses atomic sequence.

### BR-CERT-005 — Certificate Expiry Handling
- **Description:** Services that produce certificates with an expiry date must configure the validity period. The system tracks expiry and notifies citizens 30 days before expiry for renewal.
- **Trigger:** Certificate issuance (for services with validity period configured).
- **Action:** Set certificate.expiry_date; schedule Celery task for renewal reminder notification.

### BR-CERT-006 — Certificate Revocation
- **Description:** A department head can revoke a certificate if issued in error. Revocation is permanent; a new application must be filed for a replacement certificate.
- **Trigger:** Department head revokes a certificate.
- **Condition:** Certificate must be in ISSUED or ACTIVE province.
- **Action:** Certificate.status = REVOKED; revocation_reason and revoked_by stored; verification URL shows revocation message; citizen and officer notified.

### BR-CERT-007 — Certificate Accessibility
- **Description:** Certificates must be downloadable by the citizen from the dashboard for 5 years post-issuance.
- **Trigger:** Certificate download request.
- **Condition:** Certificate not revoked; citizen is the owner; session authenticated.
- **Action:** Generate time-limited pre-signed S3 URL (30 seconds). Log download event.

### BR-CERT-008 — Certificate Template Versioning
- **Description:** Certificate PDF templates are version-controlled. Certificates generated from a specific template version retain that version for legal validity.
- **Trigger:** Template update by department head.
- **Action:** New template version created. Existing certificates reference their original template version and remain unchanged.

---

## Operational Policy Addendum

### Section 1 — Citizen Data Privacy Policy
1. NID numbers are stored as one-way hashed tokens (SHA-256 + salt). The raw 12-digit number is never persisted post-verification.
2. PII fields (mobile, email, address) are encrypted at rest using AES-256 with application-layer encryption (in addition to database encryption).
3. Citizens have the right to request a copy of their personal data (PDPA Section 11) and the right to erasure for closed applications (PDPA Section 17).
4. Data minimisation: only data fields required for service delivery are collected; no speculative data collection.

### Section 2 — Service Delivery SLA Policy
1. Default service SLAs are defined by each department; the platform enforces them via the SLA monitoring engine.
2. SLA timers pause when an application is in PENDING_INFO province (citizen response awaited).
3. System downtime periods are excluded from SLA calculations using the downtime registry.
4. SLA breach rates above 10% for any department trigger an automatic alert to the ministry nodal officer.

### Section 3 — Fee Policies
1. Fee waivers approved in the current financial year cannot exceed 15% of total expected fee collection for any service (reviewed quarterly).
2. Refunds are processed within 7 working days of approval.
3. No cash payment is accepted for online services; all payments must go through ConnectIPS or authorised bank challans.
4. Fee revisions take effect at the start of the next financial quarter; applications submitted before revision retain the original fee amount.

### Section 4 — System Availability Policy
1. The platform targets 99.9% monthly uptime (excluding scheduled maintenance windows).
2. Scheduled maintenance windows are on the second Sunday of each month from 2:00 AM to 4:00 AM IST.
3. During maintenance, a pre-announced downtime banner is displayed from 24 hours before.
4. Emergency unplanned outages must be resolved within 4 hours; a status update published every 30 minutes.
