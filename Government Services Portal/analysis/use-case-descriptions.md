# Use Case Descriptions — Government Services Portal

## UC-001 — Citizen Registration

**Use Case ID:** UC-001  
**Name:** Citizen Registration with NID Verification  
**Actor(s):** Citizen (Primary), NASC (National Identity Management Centre)/NID API (Secondary)  
**Preconditions:**
- Citizen has a valid NID number linked to an active mobile number.
- NID OTP service is available.
- Citizen does not already have a registered account with the same NID.

**Postconditions:**
- Citizen account is created with a unique Citizen ID.
- NID number is stored masked (last 4 digits visible).
- Confirmation SMS and email are dispatched.

**Main Flow:**
1. Citizen navigates to the registration page and selects "Register with NID".
2. Citizen enters their 12-digit NID number.
3. System validates the format (12 numeric digits) and sends OTP request to NASC (National Identity Management Centre) API.
4. NASC (National Identity Management Centre) API dispatches OTP to the NID-linked mobile number.
5. System displays OTP input screen with a 5-minute timer.
6. Citizen enters the OTP received.
7. System verifies OTP with NASC (National Identity Management Centre) API; receives verification response with name and masked NID.
8. System checks for duplicate registration; none found.
9. Citizen completes profile (email, password, alternate mobile).
10. System creates the citizen account, assigns Citizen ID, and stores masked NID.
11. Confirmation SMS sent to registered mobile; confirmation email sent to provided email address.
12. Citizen is redirected to the dashboard.

**Alternative Flows:**
- **A1 (OTP delivery failure):** At step 3, if NASC (National Identity Management Centre) API returns error, system shows "OTP service temporarily unavailable; try after 15 minutes". Retry count increments; after 3 retries, citizen is advised to contact support.
- **A2 (Incorrect OTP):** At step 6, if OTP is wrong, failure counter increments. After 3 failures, OTP is locked for 15 minutes with notification.
- **A3 (Duplicate NID):** At step 8, system shows "Account already registered with this NID" and offers a link to account recovery.
- **A4 (OTP expired):** If the 5-minute window lapses, system shows "OTP expired; request a new OTP" link.

**Exception Flows:**
- **E1 (NASC (National Identity Management Centre) service down):** System switches to offline registration mode; citizen can register with basic details and must complete NID verification within 7 days.

**Business Rules Referenced:** BR-ELIG-001, BR-ELIG-002  
**Frequency:** High (estimated 1,000–5,000 registrations/day at peak)  
**Priority:** Must Have

---

## UC-002 — Submit Service Application

**Use Case ID:** UC-002  
**Name:** Submit Service Application  
**Actor(s):** Citizen (Primary), Workflow Engine (System Secondary)  
**Preconditions:**
- Citizen is logged in with a verified account.
- Service is published and citizen meets eligibility criteria.
- No active/pending application exists for the same service by this citizen.

**Postconditions:**
- Application created in SUBMITTED province with a unique ARN.
- Application is placed in the processing queue for the relevant department.
- Citizen notified via SMS and email with ARN.

**Main Flow:**
1. Citizen selects a service from the service catalog.
2. System checks eligibility rules defined for the service; displays eligibility confirmation.
3. Citizen clicks "Apply Now"; dynamic form rendered based on service definition.
4. Citizen fills all required fields; system performs field-level validation on blur.
5. Citizen attaches required documents (upload or Nepal Document Wallet (NDW) pull).
6. If service has a fee, system shows fee breakup (base + VAT (13%)) and payment options.
7. Citizen reviews the application summary and confirms.
8. For paid services: citizen is redirected to the payment gateway.
9. On successful payment (or for free services): system creates the application record.
10. Application transitions to SUBMITTED province; ARN assigned.
11. Workflow engine places the application in the department's queue.
12. SMS and email with ARN dispatched to citizen.

**Alternative Flows:**
- **A1 (Save Draft):** At any step 3–8, citizen can save draft. Application saved in DRAFT province; citizen can resume within 30 days.
- **A2 (Payment gateway failure):** At step 8, if payment fails, application remains in PAYMENT_PENDING for 24 hours with retry option.
- **A3 (Eligibility failure):** At step 2, if citizen fails eligibility, system shows reason and does not allow submission.

**Exception Flows:**
- **E1 (Duplicate application):** If an active/approved application exists, system blocks new submission with reference to existing application.

**Business Rules Referenced:** BR-APP-001, BR-APP-002, BR-FEE-001  
**Frequency:** Very High (5,000–20,000 submissions/day)  
**Priority:** Must Have

---

## UC-003 — Upload Documents

**Use Case ID:** UC-003  
**Name:** Upload Supporting Documents  
**Actor(s):** Citizen (Primary), Document Verification Service (System Secondary)  
**Preconditions:**
- Citizen has an active application in DRAFT or SUBMITTED province.
- Required document types defined in the service definition.

**Postconditions:**
- Documents uploaded, virus-scanned, and stored in secure S3 with pre-signed URL.
- Document metadata recorded in database.
- Application's document checklist updated.

**Main Flow:**
1. Citizen accesses the Documents section of their application.
2. System displays the required document checklist with upload slots.
3. Citizen selects a file for each document type (max 5 MB, PDF/JPEG/PNG).
4. System validates file size and format before upload.
5. File is transmitted to the server over TLS.
6. Server sends the file to the ClamAV antivirus scanner.
7. On clean scan, file is stored in S3 with server-side encryption (SSE-S3).
8. A pre-signed URL (1-hour validity) is generated for immediate preview.
9. Document metadata (file name, type, checksum, scan result, upload timestamp) saved to database.
10. Document checklist item marked as uploaded; citizen sees green checkmark.

**Alternative Flows:**
- **A1 (Nepal Document Wallet (NDW) pull):** At step 3, citizen selects "Fetch from Nepal Document Wallet (NDW)" instead of uploading a local file. System initiates OAuth flow; citizen authorises and selects document. Document is pulled and processed from step 6 onwards.
- **A2 (File too large):** At step 4, if file exceeds 5 MB, system shows error before upload is attempted.
- **A3 (Wrong file type):** At step 4, system rejects non-PDF/JPEG/PNG files with a format error message.

**Exception Flows:**
- **E1 (Malware detected):** At step 6, ClamAV flags the file. Document is quarantined, citizen is notified, and the document slot is marked as failed. Citizen must upload a clean file.
- **E2 (S3 upload failure):** System retries 3 times; if all fail, citizen is shown a "Service temporarily unavailable" message and upload is queued for retry.

**Business Rules Referenced:** BR-DOC-001, BR-DOC-002, BR-DOC-004  
**Frequency:** High  
**Priority:** Must Have

---

## UC-004 — Track Application Status

**Use Case ID:** UC-004  
**Name:** Track Application Status  
**Actor(s):** Citizen (Primary)  
**Preconditions:**
- Application has been submitted (ARN exists).
- Citizen is logged in OR has ARN + date of birth for guest tracking.

**Postconditions:**
- No state changes; read-only operation.
- Tracking event logged for audit.

**Main Flow:**
1. Citizen navigates to "My Applications" or enters ARN on the guest tracking page.
2. System retrieves application by ARN (or from citizen's profile).
3. System renders the status timeline: each transition with timestamp, province name, and actor role.
4. If in PENDING_INFO province, system shows a highlighted action banner with specific requirements.
5. Estimated completion date displayed based on SLA configuration and working-day calendar.
6. Current queue position (approximate, anonymised) displayed for SUBMITTED/UNDER_REVIEW provinces.
7. Action buttons displayed based on province (e.g., "Pay Fee", "Submit Additional Info", "Download Certificate").

**Alternative Flows:**
- **A1 (ARN not found):** System displays "Application not found; verify ARN or check your registered email".
- **A2 (Application auto-closed):** System shows AUTO_CLOSED province with reason and guidance for re-application.

**Business Rules Referenced:** BR-APP-005  
**Frequency:** Very High (10× submission frequency)  
**Priority:** Must Have

---

## UC-005 — Pay Service Fee

**Use Case ID:** UC-005  
**Name:** Pay Service Fee  
**Actor(s):** Citizen (Primary), ConnectIPS / Razorpay (Secondary)  
**Preconditions:**
- Application in PAYMENT_PENDING province.
- Fee invoice generated by the system.

**Postconditions:**
- FeeInvoice status = PAID.
- Application transitions to SUBMITTED province.
- Payment receipt PDF generated and emailed.

**Main Flow:**
1. Citizen selects "Pay Now" from the application dashboard.
2. System displays invoice: base fee, VAT (13%), total, payment deadline.
3. Citizen selects payment mode (eSewa/Khalti/ConnectIPS, net banking, debit/credit card).
4. System creates a payment order in ConnectIPS with unique order ID and amount.
5. Citizen is redirected to ConnectIPS payment page.
6. Citizen completes payment on ConnectIPS.
7. ConnectIPS sends webhook to portal's `/api/v1/payments/webhook` endpoint.
8. System verifies webhook signature; updates FeeInvoice to PAID.
9. Application transitions to SUBMITTED province.
10. Receipt PDF generated (invoice details + payment reference); emailed and available for download.

**Alternative Flows:**
- **A1 (Webhook delayed):** If webhook not received within 5 minutes, system polls ConnectIPS status API. On confirmation, proceeds from step 8.
- **A2 (Payment failure):** ConnectIPS returns failure; invoice remains UNPAID. Citizen shown failure reason and can retry.
- **A3 (Fee waiver approved):** If waiver was approved before payment, system bypasses ConnectIPS; invoice amount set to zero and application auto-advances.

**Exception Flows:**
- **E1 (Duplicate payment):** If ConnectIPS webhook fires twice for the same order, idempotency check prevents double-crediting; second webhook is logged and discarded.

**Business Rules Referenced:** BR-FEE-001, BR-FEE-003, BR-FEE-008  
**Frequency:** High  
**Priority:** Must Have

---

## UC-006 — Download Certificate

**Use Case ID:** UC-006  
**Name:** Download Issued Certificate  
**Actor(s):** Citizen (Primary), Certificate Store (System)  
**Preconditions:**
- Application in CERTIFICATE_ISSUED province.
- DSC-signed certificate PDF exists in document store.

**Postconditions:**
- Certificate downloaded; download event logged.

**Main Flow:**
1. Citizen navigates to the Certificates tab or receives a direct link from SMS/email.
2. Citizen clicks "Download Certificate".
3. System verifies citizen identity (session token) and ownership of the certificate.
4. System retrieves the certificate from S3 using a server-side authenticated request.
5. A pre-signed download URL (valid 30 seconds) is generated and returned to the browser.
6. Browser initiates download; citizen receives the PDF.
7. Download event logged with: timestamp, certificate ID, citizen ID, IP address.

**Alternative Flows:**
- **A1 (Shareable link):** Citizen can generate a shareable link (30-day expiry, single-use) to share with third parties (e.g., bank, employer).
- **A2 (Certificate expired):** If certificate has an expiry date that has passed, download is blocked and citizen is directed to apply for renewal.

**Business Rules Referenced:** BR-CERT-001, BR-CERT-005  
**Frequency:** High  
**Priority:** Must Have

---

## UC-007 — File Grievance

**Use Case ID:** UC-007  
**Name:** File Grievance  
**Actor(s):** Citizen (Primary), Department Grievance System (Secondary)  
**Preconditions:**
- Citizen is logged in.
- Either a rejected/delayed application exists, or citizen has a standalone complaint.

**Postconditions:**
- Grievance record created in OPEN province with GRN.
- Auto-assigned to department head.
- Citizen notified with GRN.

**Main Flow:**
1. Citizen navigates to "File a Grievance".
2. Citizen optionally links the grievance to a specific application (by ARN).
3. Citizen selects grievance category (rejection dispute, delay, officer conduct, technical, other).
4. Citizen provides description (50–1000 characters) and optionally attaches evidence.
5. System validates completeness.
6. Grievance record created in OPEN province; GRN assigned.
7. System auto-assigns to the department head of the linked department (or general grievance cell if unlinked).
8. Department head notified via email and in-portal alert.
9. Citizen notified with GRN via SMS and email.
10. 30-day SLA clock starts.

**Alternative Flows:**
- **A1 (No linked application):** Citizen selects "General Complaint"; system routes to the citizen services grievance cell.
- **A2 (Duplicate grievance):** If the same citizen has an open grievance for the same application, system warns and asks for confirmation to proceed.

**Business Rules Referenced:** BR-GRIEV-001, BR-GRIEV-002, BR-GRIEV-003  
**Frequency:** Medium  
**Priority:** Must Have

---

## UC-008 — Field Officer Review

**Use Case ID:** UC-008  
**Name:** Field Officer Application Review  
**Actor(s):** Field Officer (Primary)  
**Preconditions:**
- Application assigned to the officer and in UNDER_REVIEW province.
- Officer is logged in with an active session.

**Postconditions:**
- Application either advanced (approve/reject/pending-info/forward) or unchanged.
- All review actions logged.

**Main Flow:**
1. Officer opens application from the queue.
2. System displays the application workspace: form data, documents side-by-side, citizen profile, eligibility check results.
3. Officer reviews form fields against the service eligibility criteria.
4. Officer opens each attached document in the inline viewer.
5. Officer marks each document as "Verified" or "Requires Clarification".
6. Officer makes decision: Approve / Reject / Request Info / Forward.
7. Based on decision, the corresponding use case (UC-009 or UC-011) is triggered.
8. All review actions are saved with timestamps in the application's audit trail.

**Alternative Flows:**
- **A1 (Officer reassignment):** If the officer is reassigned mid-review, the work in progress is saved; the new officer sees all review notes.

**Business Rules Referenced:** BR-APP-006, BR-APP-007  
**Frequency:** High  
**Priority:** Must Have

---

## UC-009 — Approve/Reject Application

**Use Case ID:** UC-009  
**Name:** Approve or Reject Application  
**Actor(s):** Field Officer or Department Head (Primary), DSC Service (Secondary)  
**Preconditions:**
- Application is in UNDER_REVIEW province.
- Officer has reviewed all documents and eligibility criteria.

**Postconditions:**
- **Approve path:** Application → APPROVED; certificate generation triggered; citizen notified.
- **Reject path:** Application → REJECTED; rejection reason stored; citizen notified.

**Main Flow (Approve):**
1. Officer confirms the review checklist (all items verified).
2. Officer clicks "Approve" and enters a brief approval note.
3. System validates the checklist is complete.
4. Application transitions to APPROVED province.
5. Certificate generation task dispatched to Celery queue.
6. CertificateIssuanceService renders the PDF template with applicant data.
7. DSCSigningService applies the officer's digital signature.
8. QR code embedded linking to the public verification URL.
9. Certificate PDF stored in S3; CertificateRecord created in the database.
10. Application transitions to CERTIFICATE_ISSUED province.
11. Citizen notified via SMS + email with download link.

**Main Flow (Reject):**
1. Officer selects a rejection reason from the predefined list.
2. Officer adds remarks (minimum 50 characters).
3. System records rejection; application transitions to REJECTED province.
4. Citizen notified with rejection reason, remarks, and re-application guidance.
5. Audit log entry created.

**Alternative Flows:**
- **A1 (DSC failure):** If DSC signing fails, certificate generation is retried 3 times (with back-off). If all retries fail, approval is held in CERTIFICATE_PENDING and the department head is alerted.

**Business Rules Referenced:** BR-APP-008, BR-APP-009, BR-CERT-001  
**Frequency:** High  
**Priority:** Must Have

---

## UC-010 — Generate Report

**Use Case ID:** UC-010  
**Name:** Generate Performance and Compliance Report  
**Actor(s):** Department Head or Auditor (Primary)  
**Preconditions:**
- Requester is authenticated with Department Head or Auditor role.
- Required date range data exists in the database.

**Postconditions:**
- Report generated (PDF and/or CSV) and available for download.
- Report generation event logged.

**Main Flow:**
1. User selects "Reports" and chooses report type (daily summary, officer performance, SLA compliance, financial).
2. User sets parameters: date range, department (if super admin or auditor), format (PDF/CSV).
3. System validates parameters.
4. System queries the analytics tables (pre-aggregated by Celery Beat jobs).
5. Report rendered: for PDF, Django Celery task generates the file; for CSV, data is streamed directly.
6. User is notified (in-portal) when the report is ready (< 2 minutes for standard reports).
7. Download link provided; report stored for 30 days before archival.

**Business Rules Referenced:** BR-APP-015  
**Frequency:** Medium  
**Priority:** Must Have

---

## UC-011 — Configure Service Form

**Use Case ID:** UC-011  
**Name:** Configure Service Definition and Form  
**Actor(s):** Department Head (Primary)  
**Preconditions:**
- Department Head is authenticated.
- Department is active in the system hierarchy.

**Postconditions:**
- Service definition created/updated; form fields and eligibility rules saved.
- If published, service visible in citizen catalog.

**Main Flow:**
1. Department Head navigates to "Service Configuration".
2. Selects "Create New Service" or edits an existing draft service.
3. Fills service metadata: name, description, category, jurisdiction, fee, SLA.
4. Uses the form builder to add/edit fields (text, number, date, dropdown, conditional logic).
5. Configures required documents (type, issuer, max age).
6. Defines eligibility rules using the rule builder.
7. Configures notification templates for each workflow event.
8. Saves as DRAFT; previews the citizen-facing form.
9. Publishes the service; it becomes visible in the service catalog.

**Business Rules Referenced:** BR-APP-001  
**Frequency:** Low  
**Priority:** Must Have

---

## UC-012 — Manage Department Users

**Use Case ID:** UC-012  
**Name:** Manage Department Users (Officer Accounts)  
**Actor(s):** Department Head (Primary)  
**Preconditions:**
- Department Head is authenticated.

**Postconditions:**
- Officer account created / updated / deactivated.
- Pending applications re-queued if officer deactivated.

**Main Flow:**
1. Department Head opens "Officer Management".
2. Creates a new officer account: name, employee ID, designation, email, zone.
3. System generates a temporary password and sends account activation email to officer.
4. Alternatively: deactivates an existing officer account.
5. System reassigns all UNDER_REVIEW applications from the deactivated officer to the unassigned queue.
6. All changes logged in the audit trail.

**Business Rules Referenced:** BR-APP-006  
**Frequency:** Low  
**Priority:** Must Have

---

## UC-013 — Audit Trail Access

**Use Case ID:** UC-013  
**Name:** Access Audit Trail  
**Actor(s):** Auditor or Super Admin (Primary)  
**Preconditions:**
- Requester authenticated with Auditor or Super Admin role.
- 2FA completed for session.

**Postconditions:**
- Audit records retrieved; no data modified.
- Audit access event itself logged.

**Main Flow:**
1. Auditor selects the "Audit Trail" module.
2. Specifies search filters: date range, actor, action type, entity type, entity ID.
3. System queries the AuditLog table using indexed fields.
4. Results displayed with tamper-verification hash indicators.
5. Auditor can drill into a specific log entry to see full change delta.
6. Auditor can export filtered results as a CSV (with masked PII).
7. Access event logged: auditor ID, query parameters, timestamp.

**Business Rules Referenced:** BR-APP-015  
**Frequency:** Low  
**Priority:** Must Have

---

## UC-014 — Mass Notification Broadcast

**Use Case ID:** UC-014  
**Name:** Mass Notification Broadcast  
**Actor(s):** Super Admin (Primary), SMS Gateway / Email Service (Secondary)  
**Preconditions:**
- Super Admin is authenticated.
- Target audience criteria defined.

**Postconditions:**
- Notifications queued for delivery; delivery status tracked.

**Main Flow:**
1. Super Admin opens "Broadcast Notification".
2. Defines audience: all citizens, citizens with active applications, officers in a specific department.
3. Composes message: SMS text (160 characters max) and/or HTML email template.
4. Optionally schedules delivery for a specific date/time.
5. System shows estimated recipient count for confirmation.
6. Super Admin confirms; notifications queued in Celery for batch dispatch.
7. Celery workers send via Nepal Telecom / Sparrow SMS gateway and SES in batches of 500.
8. Delivery status (sent/failed count) updated in real-time and accessible in broadcast history.

**Business Rules Referenced:** N/A (operational policy)  
**Frequency:** Very Low  
**Priority:** Should Have

---

## UC-015 — Service Analytics Dashboard

**Use Case ID:** UC-015  
**Name:** Service Analytics Dashboard  
**Actor(s):** Department Head, Super Admin, Auditor (Primary)  
**Preconditions:**
- Requester is authenticated with appropriate role.

**Postconditions:**
- Analytics data displayed; no state changes.

**Main Flow:**
1. User navigates to the "Analytics" section.
2. System renders pre-aggregated KPI tiles: applications today, MTD, YTD, fee collected MTD, SLA compliance %.
3. User can apply filters: department, service type, date range, geography.
4. Trend charts displayed: application volume over time, SLA compliance trend, grievance trend.
5. Service-wise demand ranking: top 10 most-applied services.
6. Geographic heat map: applications by district/province.
7. User can drill down into any chart segment to see underlying application list.
8. Data exported as PDF report with chart images embedded.

**Business Rules Referenced:** N/A (analytics only)  
**Frequency:** Medium  
**Priority:** Should Have
