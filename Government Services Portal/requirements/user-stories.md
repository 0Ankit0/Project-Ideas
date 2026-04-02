# User Stories — Government Services Portal

## Story Map by Epic

| Epic | Roles Covered | Story IDs |
|------|--------------|-----------|
| Citizen Onboarding & Identity | Citizen | US-CIT-001..005 |
| Service Discovery & Application | Citizen | US-CIT-006..010 |
| Payments, Certificates & Grievances | Citizen | US-CIT-011..015 |
| Field Officer Operations | Field Officer | US-FO-001..012 |
| Department Administration | Department Head | US-DH-001..010 |
| Platform Administration | Super Admin | US-SA-001..008 |
| Audit & Compliance | Auditor | US-AUD-001..008 |

---

## Role: Citizen (US-CIT-001..015)

### US-CIT-001 — Citizen Registration with NID Verification
**As a** citizen,  
**I want to** register on the portal using my NID number and OTP verification,  
**so that** my identity is cryptographically verified and I can access government services securely.

**Priority:** Must Have | **Story Points:** 8

**Acceptance Criteria:**
1. Given a valid 12-digit NID number, the system triggers an OTP to the NID-linked mobile via NASC (National Identity Management Centre) API within 10 seconds.
2. Given the correct OTP entered within 5 minutes, the system creates a citizen account, stores masked NID (last 4 digits visible), and assigns a unique Citizen ID.
3. Given an incorrect OTP, the system increments failure count; after 3 failures, the OTP flow is locked for 15 minutes.
4. Given the same NID number already registered, the system prevents duplicate registration and prompts password recovery.
5. Given successful registration, the citizen receives a confirmation SMS and email with their Citizen ID.

---

### US-CIT-002 — Citizen Profile Management
**As a** registered citizen,  
**I want to** manage my profile (name, address, phone, email, linked documents),  
**so that** my information is current and auto-filled in service applications.

**Priority:** Must Have | **Story Points:** 5

**Acceptance Criteria:**
1. Citizen can update phone number only after OTP verification to the new number.
2. Name changes require documentary proof (Gazette notification or affidavit) uploaded as PDF.
3. Address update is reflected in all pending applications not yet approved.
4. Profile photo must be ≤ 500 KB in JPEG/PNG format; system validates before saving.
5. Audit trail records every profile field change with timestamp and IP address.

---

### US-CIT-003 — Nepal Document Wallet (NDW) Integration for Document Linking
**As a** citizen,  
**I want to** link my Nepal Document Wallet (NDW) account and pull verified documents,  
**so that** I can submit government-issued documents without uploading physical scans.

**Priority:** Should Have | **Story Points:** 5

**Acceptance Criteria:**
1. OAuth 2.0 redirect to Nepal Document Wallet (NDW) completes within the same browser session.
2. Citizen can browse and select from their Nepal Document Wallet (NDW) document list (driving licence, marksheet, etc.).
3. Pulled document metadata (issuer, date, document number) is displayed for citizen confirmation before attaching.
4. If Nepal Document Wallet (NDW) is unavailable, the system falls back to manual upload gracefully.
5. Nepal Document Wallet (NDW) OAuth tokens are stored encrypted and refreshed automatically before expiry.

---

### US-CIT-004 — Login via NID OTP or Password
**As a** registered citizen,  
**I want to** log in using either NID OTP or username/password,  
**so that** I have multiple secure authentication options.

**Priority:** Must Have | **Story Points:** 3

**Acceptance Criteria:**
1. OTP login generates a fresh OTP valid for 5 minutes; previous OTPs are invalidated.
2. Password login enforces a minimum 8-character password with at least one number and one special character.
3. After 5 consecutive failed logins, account is locked for 30 minutes and the citizen is notified by SMS.
4. Successful login issues a JWT access token (15-minute expiry) and refresh token (7-day expiry).
5. Concurrent sessions from different devices are allowed up to a limit of 3 active sessions.

---

### US-CIT-005 — Account Recovery and MFA Reset
**As a** citizen who lost access,  
**I want to** recover my account via NID re-verification,  
**so that** I can regain access without losing my application history.

**Priority:** Must Have | **Story Points:** 3

**Acceptance Criteria:**
1. Account recovery requires NID OTP plus answering a security question set at registration.
2. After successful recovery, all active sessions are invalidated.
3. Recovery event is logged in the audit trail.
4. Citizen is notified via all registered contact channels upon recovery.
5. Recovery is blocked if the account is under a security freeze by an administrator.

---

### US-CIT-006 — Browse and Search Government Services
**As a** citizen,  
**I want to** browse the service catalog by department, category, and keyword search,  
**so that** I can quickly find the service I need.

**Priority:** Must Have | **Story Points:** 3

**Acceptance Criteria:**
1. Service catalog is browsable without login; personal eligibility check requires login.
2. Full-text search returns results within 2 seconds even with 500+ services.
3. Each service listing shows: name, department, description, fee, SLA timeline, and required documents.
4. Citizen can filter by province/district applicability, free vs. paid, and availability (online/offline).
5. Recently viewed services are stored in browser local storage for returning visitors.

---

### US-CIT-007 — Submit Service Application
**As a** citizen,  
**I want to** submit an application for a government service by filling a dynamic form,  
**so that** my request is officially registered and trackable.

**Priority:** Must Have | **Story Points:** 8

**Acceptance Criteria:**
1. Dynamic form renders all required fields per the service definition configured by the department.
2. Citizen can save draft and resume within 30 days before the draft expires.
3. Submission validates all mandatory fields; inline validation errors appear field-by-field.
4. On submission, the system assigns an Application Reference Number (ARN) and sends it via SMS/email.
5. Citizen cannot submit a second application for the same service if a pending/approved application exists.

---

### US-CIT-008 — Upload Supporting Documents
**As a** citizen,  
**I want to** upload supporting documents (PDF, JPEG, PNG) for my application,  
**so that** the officer reviewing my application has all necessary evidence.

**Priority:** Must Have | **Story Points:** 5

**Acceptance Criteria:**
1. File size limit per document is 5 MB; batch upload supports up to 10 documents simultaneously.
2. Allowed file types: PDF, JPEG, PNG; system rejects any other type with a clear error.
3. Uploaded files are scanned for malware before being stored; citizen is notified if a file fails scanning.
4. Each uploaded document is shown with a preview thumbnail and file name.
5. Documents uploaded for an approved application are retained for 7 years per records retention policy.

---

### US-CIT-009 — Track Application Status
**As a** citizen,  
**I want to** track the real-time status of my application with a timeline view,  
**so that** I know what stage my application is in and what actions are required from me.

**Priority:** Must Have | **Story Points:** 3

**Acceptance Criteria:**
1. Status timeline shows all state transitions with timestamps (submitted, under review, pending info, approved/rejected).
2. If additional information is requested, the citizen sees a highlighted action banner with the specific requirements.
3. Estimated completion date is displayed based on service SLA and current queue position (approximate).
4. Push notifications (SMS + email) are sent on every status change.
5. Citizen can view status without login using ARN + date of birth as lookup keys.

---

### US-CIT-010 — Provide Additional Information When Requested
**As a** citizen,  
**I want to** respond to an officer's request for additional information,  
**so that** my application can proceed without being rejected for incomplete data.

**Priority:** Must Have | **Story Points:** 3

**Acceptance Criteria:**
1. Citizen receives notification with specific fields/documents requested by the officer.
2. Response portal opens only for applications in PENDING_INFO province.
3. Citizen has 15 days to respond; the system sends reminders at day 10 and day 14.
4. Submitted response re-triggers the review workflow and notifies the assigned officer.
5. If citizen does not respond within 15 days, application transitions to AUTO_CLOSED with notification.

---

### US-CIT-011 — Pay Service Fee Online
**As a** citizen,  
**I want to** pay the service fee online using eSewa/Khalti/ConnectIPS, net banking, or card,  
**so that** my application can proceed to review without visiting a government office.

**Priority:** Must Have | **Story Points:** 8

**Acceptance Criteria:**
1. Fee amount and breakup (base fee + VAT (13%)) are displayed before payment gateway redirect.
2. ConnectIPS/Razorpay integration supports eSewa/Khalti/ConnectIPS, debit/credit cards, and net banking.
3. On successful payment, a machine-readable receipt (PDF) is generated and emailed within 2 minutes.
4. Payment status is reflected on the application immediately via webhook; no manual reconciliation needed.
5. If payment gateway timeout occurs, application remains in PAYMENT_PENDING for 24 hours for retry.

---

### US-CIT-012 — Download Issued Certificate
**As a** citizen,  
**I want to** download my government-issued certificate as a digitally signed PDF,  
**so that** I have an official, tamper-proof document.

**Priority:** Must Have | **Story Points:** 5

**Acceptance Criteria:**
1. Certificate PDF bears DSC (Digital Signature Certificate) from the issuing officer and a QR code for verification.
2. Download link is available in the citizen's dashboard for 5 years post-issuance.
3. Certificate QR code resolves to a public verification URL without requiring login.
4. Each download event is logged with timestamp, IP address, and citizen ID.
5. Citizen can share certificate via a time-limited shareable link (valid 30 days, one-time use).

---

### US-CIT-013 — File a Grievance
**As a** citizen,  
**I want to** file a grievance about a rejected application or delayed service,  
**so that** my concern is addressed by the appropriate authority.

**Priority:** Must Have | **Story Points:** 5

**Acceptance Criteria:**
1. Grievance can be linked to a specific application or filed as a standalone complaint.
2. Grievance form captures: category (rejection, delay, officer conduct, technical), description (max 1000 characters), and supporting evidence.
3. On submission, a Grievance Reference Number (GRN) is issued and communicated via SMS/email.
4. Grievance is auto-assigned to the department head of the relevant department within 1 hour.
5. Resolution SLA is 30 days; citizen is notified of progress updates.

---

### US-CIT-014 — Track Grievance Status
**As a** citizen,  
**I want to** track my grievance and receive updates,  
**so that** I am informed about actions taken on my complaint.

**Priority:** Should Have | **Story Points:** 2

**Acceptance Criteria:**
1. Grievance timeline shows: OPEN → ASSIGNED → IN_PROGRESS → RESOLVED/ESCALATED provinces.
2. Resolution notes from the officer are visible to the citizen after the grievance is closed.
3. Citizen can escalate an unresolved grievance to a higher authority after the SLA deadline.
4. SMS/email notification sent on every grievance status change.
5. Citizen can rate the grievance resolution (1–5 stars) within 7 days of closure.

---

### US-CIT-015 — View Service History and Certificates Archive
**As a** citizen,  
**I want to** see all my past applications and certificates in a personal dashboard,  
**so that** I have a single view of all my government service interactions.

**Priority:** Should Have | **Story Points:** 3

**Acceptance Criteria:**
1. Dashboard shows all applications with status, date, department, and ARN.
2. Certificates tab lists all issued certificates with issue date, expiry (if applicable), and download button.
3. Grievances tab shows all filed grievances with current status.
4. Citizen can export their application history as CSV for personal records.
5. Dashboard data loads within 3 seconds even with 50+ applications.

---

## Role: Field Officer (US-FO-001..012)

### US-FO-001 — View Assigned Application Queue
**As a** field officer,  
**I want to** view my assigned application queue sorted by SLA deadline,  
**so that** I can prioritise reviews to meet department targets.

**Priority:** Must Have | **Story Points:** 5

**Acceptance Criteria:**
1. Queue shows: ARN, citizen name, service type, submission date, SLA deadline, and days remaining.
2. Applications approaching SLA breach (< 2 days) are highlighted in red.
3. Queue supports filtering by service type, status, and date range.
4. Bulk assignment of unassigned applications to self is possible (up to 50 at once).
5. Queue refreshes automatically every 60 seconds without page reload.

---

### US-FO-002 — Review Application Details
**As a** field officer,  
**I want to** view complete application details including form responses, uploaded documents, and citizen profile,  
**so that** I can make an informed decision.

**Priority:** Must Have | **Story Points:** 5

**Acceptance Criteria:**
1. Application detail page shows all form fields, citizen's submitted values, and document previews side-by-side.
2. Officer can view NID-verification status without seeing the full NID number (masked display).
3. Document viewer supports PDF and image rendering inline without download.
4. Previous application history for the same citizen is accessible for context.
5. Officer notes field allows adding internal comments (not visible to citizen).

---

### US-FO-003 — Request Additional Information
**As a** field officer,  
**I want to** request additional documents or information from the citizen,  
**so that** I have everything needed before making a decision.

**Priority:** Must Have | **Story Points:** 3

**Acceptance Criteria:**
1. Officer selects specific required fields or document types from a structured checklist.
2. Application transitions to PENDING_INFO province and citizen is notified automatically.
3. Officer sets a response deadline (7–30 days); system enforces this date.
4. Officer can see the citizen's response with timestamps when submitted.
5. If citizen does not respond, officer receives notification to take action (close or extend).

---

### US-FO-004 — Approve Application
**As a** field officer,  
**I want to** approve a verified application with a digital signature,  
**so that** the citizen's service request is fulfilled officially.

**Priority:** Must Have | **Story Points:** 5

**Acceptance Criteria:**
1. Approval requires officer to confirm checklist completion (all required documents verified, eligibility confirmed).
2. Officer's DSC is applied to the certificate via the DSC signing service.
3. Application transitions to APPROVED province and certificate generation is triggered automatically.
4. Citizen is notified within 2 minutes of approval via SMS and email with certificate download link.
5. Approval action is immutable; only a department head can reverse an approval with documented reason.

---

### US-FO-005 — Reject Application with Reason
**As a** field officer,  
**I want to** reject an application with a documented reason from a predefined list,  
**so that** the citizen understands why their application was not approved.

**Priority:** Must Have | **Story Points:** 3

**Acceptance Criteria:**
1. Rejection reason must be selected from a predefined list (ineligible, incomplete docs, false declaration, etc.).
2. Officer must add a minimum 50-character explanation in the remarks field.
3. Citizen is notified immediately with the rejection reason and guidance for re-application if eligible.
4. Citizen is informed of their right to file a grievance.
5. Rejected application is archived and visible to the citizen in their history.

---

### US-FO-006 — Forward Application to Department Head
**As a** field officer,  
**I want to** forward complex or borderline applications to the department head for review,  
**so that** senior oversight is applied to difficult cases.

**Priority:** Should Have | **Story Points:** 3

**Acceptance Criteria:**
1. Forward action includes a mandatory escalation note (minimum 100 characters).
2. Department head is notified immediately upon forwarding.
3. Application shows escalation history: who forwarded, when, and the reason.
4. Department head can reassign back to the officer or a different officer with comments.
5. SLA clock continues to run during escalation.

---

### US-FO-007 — Verify Documents Against Originals (Offline Verification)
**As a** field officer,  
**I want to** mark documents as physically verified after in-person inspection,  
**so that** the system records offline verification completion.

**Priority:** Should Have | **Story Points:** 3

**Acceptance Criteria:**
1. Officer can toggle each uploaded document as "Physically Verified" with date of verification.
2. Offline verification flag is logged with officer ID and timestamp.
3. Services configured to require offline verification cannot be approved without all docs marked verified.
4. Citizen is notified if they need to visit a specific office for in-person document verification.
5. Physical verification location and appointment scheduling link are included in the notification.

---

### US-FO-008 — Bulk Process Applications
**As a** field officer,  
**I want to** bulk-approve straightforward applications after individual review,  
**so that** I can efficiently process high-volume, low-complexity services.

**Priority:** Should Have | **Story Points:** 5

**Acceptance Criteria:**
1. Bulk processing is only available for services marked as "bulk-processable" by the department head.
2. Officer must review each application summary before including it in the bulk set (no blind bulk approval).
3. Maximum 100 applications per bulk action.
4. Any application that fails eligibility checks during bulk processing is excluded and flagged separately.
5. Bulk action is logged as a single batch record with individual application references for audit.

---

### US-FO-009 — Generate Field Visit Report
**As a** field officer,  
**I want to** generate and submit field visit reports for applications requiring site inspection,  
**so that** physical verification findings are officially documented.

**Priority:** Should Have | **Story Points:** 5

**Acceptance Criteria:**
1. Field visit report form includes: visit date, location GPS coordinates, findings, photos (up to 5), and officer signature.
2. Report is attached to the application and visible to the department head.
3. Report submission triggers application transition from FIELD_VISIT_SCHEDULED to FIELD_VISIT_COMPLETE.
4. Photos must be geotagged; system validates GPS metadata before accepting.
5. Report PDF is generated and stored as a document in the application's document store.

---

### US-FO-010 — View Personal Performance Dashboard
**As a** field officer,  
**I want to** view my performance metrics (applications processed, average TAT, SLA breach rate),  
**so that** I can monitor my productivity and identify areas for improvement.

**Priority:** Could Have | **Story Points:** 3

**Acceptance Criteria:**
1. Dashboard shows: total assigned, reviewed, approved, rejected, pending, and SLA-breached for current month.
2. Trend chart shows daily processing volume for the last 30 days.
3. Average turnaround time per service type is displayed.
4. Comparisons against department averages are shown (anonymised peer benchmark).
5. Dashboard data is available from the officer's profile page.

---

### US-FO-011 — Receive SLA Alerts
**As a** field officer,  
**I want to** receive automated alerts when applications in my queue are approaching SLA deadlines,  
**so that** I can act before breaching service commitments.

**Priority:** Must Have | **Story Points:** 2

**Acceptance Criteria:**
1. Alert sent 48 hours before SLA deadline for each application in the officer's queue.
2. Alert sent again 24 hours before SLA deadline.
3. Alerts delivered via SMS, email, and in-portal notification banner.
4. SLA-breached applications appear at the top of the queue with a red "Overdue" badge.
5. Alerts can be configured by the officer (toggle channels); in-portal notifications cannot be disabled.

---

### US-FO-012 — Search Applications Across All Provinces
**As a** field officer,  
**I want to** search for any application by ARN, citizen name, or NID (masked),  
**so that** I can assist citizens who contact me directly about their applications.

**Priority:** Should Have | **Story Points:** 2

**Acceptance Criteria:**
1. Search by ARN returns exact application; search by name returns paginated results.
2. NID-based search is restricted to officers with "advanced search" permission.
3. Search results show only applications within the officer's department scope.
4. Citizen's full NID number is never displayed; masked display (XXXX-XXXX-1234) is used.
5. All search queries are logged with officer ID, search term type, and timestamp.

---

## Role: Department Head (US-DH-001..010)

### US-DH-001 — Configure Service Definitions and Forms
**As a** department head,  
**I want to** create and configure service definitions with dynamic form fields, required documents, fees, and SLAs,  
**so that** new government services can be onboarded without developer intervention.

**Priority:** Must Have | **Story Points:** 8

**Acceptance Criteria:**
1. Form builder supports: text, number, date, dropdown, checkbox, file upload, and conditional fields.
2. Required document list is configurable per service with document type, issuer, and maximum age constraints.
3. Fee can be configured as fixed, tiered (by income/category), or waived for BPL/senior citizens.
4. SLA duration is set in working days; the system auto-calculates deadlines excluding holidays.
5. Service can be published, unpublished, or archived; published services are visible in the citizen catalog.

---

### US-DH-002 — Manage Field Officer Accounts
**As a** department head,  
**I want to** create, deactivate, and assign roles to field officer accounts within my department,  
**so that** I can control who processes applications in my department.

**Priority:** Must Have | **Story Points:** 3

**Acceptance Criteria:**
1. Department head can create officer accounts with name, employee ID, designation, and zone assignment.
2. Officer accounts can be deactivated; their pending applications are automatically re-assigned to the queue.
3. Role assignment: basic officer or senior officer (with approval authority for higher-value services).
4. Officer account changes are logged in the audit trail.
5. Bulk CSV import for creating multiple officer accounts is supported.

---

### US-DH-003 — Monitor Department Performance Dashboard
**As a** department head,  
**I want to** view real-time department performance metrics (pending applications, SLA compliance, officer workload),  
**so that** I can make staffing and process decisions.

**Priority:** Must Have | **Story Points:** 5

**Acceptance Criteria:**
1. Dashboard KPIs: pending count, approved today, rejected today, SLA breach rate (%), avg processing time.
2. Officer-wise workload breakdown (applications assigned, in progress, completed this week).
3. Service-wise demand trend (applications per service over last 30/90 days).
4. Drill-down available: click on a metric to see individual applications.
5. Dashboard auto-refreshes every 5 minutes; last updated timestamp is displayed.

---

### US-DH-004 — Review and Approve Escalated Applications
**As a** department head,  
**I want to** review applications escalated by field officers and make final decisions,  
**so that** complex cases receive authoritative resolution.

**Priority:** Must Have | **Story Points:** 5

**Acceptance Criteria:**
1. Escalated applications appear in a dedicated escalation queue separated from regular queue.
2. Department head can approve, reject, or return to officer with instructions.
3. Decision requires documented reason (minimum 100 characters).
4. Approval by department head uses their DSC for certificate signing.
5. Citizen is notified of the escalated decision with department head's designation (not name) mentioned.

---

### US-DH-005 — Configure Service Eligibility Rules
**As a** department head,  
**I want to** define eligibility rules for services (age, income, residency, category),  
**so that** the system automatically validates applicant eligibility and reduces invalid submissions.

**Priority:** Should Have | **Story Points:** 8

**Acceptance Criteria:**
1. Eligibility rules can be defined using a rule builder: field comparisons, AND/OR logic, age calculations.
2. Rules are evaluated against citizen profile data (NID-verified fields) and form inputs.
3. Citizens who fail eligibility checks are shown a clear message explaining disqualification before submission.
4. Rules can be configured with exception handling: allow submission with officer override for borderline cases.
5. Rule history is maintained; previously published rules cannot be deleted, only superseded.

---

### US-DH-006 — Generate Department Reports
**As a** department head,  
**I want to** generate reports on service delivery performance, officer productivity, and SLA compliance,  
**so that** I can present data to ministry officials and plan resource allocation.

**Priority:** Must Have | **Story Points:** 5

**Acceptance Criteria:**
1. Report types: daily summary, monthly service-wise performance, officer productivity, SLA compliance.
2. Reports can be generated for custom date ranges.
3. Export formats: PDF (formatted report) and CSV (raw data).
4. Scheduled report generation (weekly/monthly) can be configured and sent to specific email addresses.
5. Reports include digital watermark with department name, generated date, and system version.

---

### US-DH-007 — Manage Fee Waiver Approvals
**As a** department head,  
**I want to** review and approve fee waiver requests from citizens (BPL, senior citizen, disabled),  
**so that** eligible citizens receive the benefits they are entitled to.

**Priority:** Should Have | **Story Points:** 3

**Acceptance Criteria:**
1. Citizens must submit proof of eligibility (BPL card, age proof, disability certificate) for waiver request.
2. Fee waiver queue is separate from application review queue.
3. Approved waiver automatically updates the application's fee record to zero; invoice is regenerated.
4. Rejected waiver requires documented reason; citizen is notified and can appeal.
5. Waiver decisions are auditable and reported in monthly financial summaries.

---

### US-DH-008 — Set Department Notifications and Alerts
**As a** department head,  
**I want to** configure automated notifications for citizens and officers for key workflow events,  
**so that** all stakeholders are proactively informed without manual communication.

**Priority:** Should Have | **Story Points:** 3

**Acceptance Criteria:**
1. Notification templates are configurable per service and event type (approval, rejection, pending info, etc.).
2. Templates support dynamic placeholders: citizen name, ARN, service name, deadline date.
3. Notification channels configurable per event: SMS (mandatory), email (optional), in-portal (always).
4. Department head can trigger manual broadcast notifications to all citizens with active applications.
5. Notification delivery logs are viewable by the department head for troubleshooting.

---

### US-DH-009 — Holiday and Working Days Calendar
**As a** department head,  
**I want to** manage the department's holiday and working days calendar,  
**so that** SLA calculations correctly exclude non-working days.

**Priority:** Must Have | **Story Points:** 2

**Acceptance Criteria:**
1. Calendar supports: public holidays (national, province), department-specific closures, and working Saturdays.
2. SLA calculation engine uses the department's calendar for all deadline calculations.
3. Holiday changes retroactively recalculate SLA deadlines for in-progress applications.
4. Citizens are shown the expected completion date excluding holidays.
5. Calendar for the next 12 months must be configured before the period starts; system warns if not done.

---

### US-DH-010 — Conduct Quality Audit of Officer Decisions
**As a** department head,  
**I want to** randomly sample and audit officer approval/rejection decisions,  
**so that** I can ensure consistent and fair decision-making.

**Priority:** Could Have | **Story Points:** 3

**Acceptance Criteria:**
1. Quality audit module selects a configurable percentage (default 5%) of completed applications randomly.
2. Department head reviews the selected application and marks the decision as: Correct, Needs Improvement, or Incorrect.
3. Incorrect decisions trigger a corrective action workflow (officer coaching alert).
4. Audit findings are summarised in the monthly performance report.
5. Audited applications are flagged and excluded from subsequent sampling periods.

---

## Role: Super Admin (US-SA-001..008)

### US-SA-001 — Manage Department and Ministry Hierarchy
**As a** super admin,  
**I want to** configure the department hierarchy (ministry → department → sub-department → zone),  
**so that** the platform structure mirrors the actual government organisation.

**Priority:** Must Have | **Story Points:** 8

**Acceptance Criteria:**
1. Hierarchical tree view allows creating, editing, and deactivating departments at any level.
2. Each department has: name, code, parent, jurisdiction (province/national), head officer, and contact details.
3. Service definitions are scoped to a specific department; services cannot exist without a parent department.
4. Deactivating a department archives its services and notifies active applicants.
5. Hierarchy changes are versioned; historical structure is preserved for audit.

---

### US-SA-002 — Platform Configuration and Feature Flags
**As a** super admin,  
**I want to** manage global platform configurations (maintenance windows, feature flags, API rate limits),  
**so that** I can control platform behaviour without code deployments.

**Priority:** Must Have | **Story Points:** 5

**Acceptance Criteria:**
1. Feature flags enable/disable: Nepal Document Wallet (NDW) integration, NID OTP login, ConnectIPS gateway, biometric verification.
2. Maintenance window configuration shows a scheduled downtime banner to all users with a countdown.
3. API rate limits are configurable per endpoint (default 100 req/min per IP).
4. Configuration changes take effect within 60 seconds without restarting the application.
5. All configuration changes are audit-logged with admin ID, old value, new value, and timestamp.

---

### US-SA-003 — Manage Citizen Accounts (Support Operations)
**As a** super admin,  
**I want to** manage citizen accounts (view, suspend, unsuspend, merge duplicates),  
**so that** I can resolve citizen issues escalated from department heads.

**Priority:** Must Have | **Story Points:** 5

**Acceptance Criteria:**
1. Citizen account lookup by Citizen ID, mobile number, or email address.
2. Account suspension requires documented reason; citizen is notified via SMS with a helpdesk reference.
3. Duplicate account merge preserves all application history under the surviving account.
4. Account deletion (PDPA data erasure) retains financial transaction records for legal compliance (7 years).
5. All admin actions on citizen accounts are logged with justification.

---

### US-SA-004 — Platform Security Configuration
**As a** super admin,  
**I want to** configure security policies (password complexity, session timeout, IP whitelisting for admin portals),  
**so that** the platform meets government cybersecurity standards.

**Priority:** Must Have | **Story Points:** 5

**Acceptance Criteria:**
1. Password policy configurable: minimum length, complexity, expiry period (default 90 days for officers).
2. Session timeout configurable per role (citizen: 30 min idle, officer: 20 min idle, admin: 15 min idle).
3. Admin console access restricted to whitelisted IP ranges; configurable without restart.
4. Failed login policy: lockout threshold and duration configurable.
5. Security configuration changes are restricted to super admin and require 2FA confirmation.

---

### US-SA-005 — Manage External Integration Configuration
**As a** super admin,  
**I want to** configure external service integrations (NID/NASC (National Identity Management Centre), Nepal Document Wallet (NDW), ConnectIPS, Nepal Telecom / Sparrow SMS gateway),  
**so that** the platform connects to the correct government infrastructure for each environment.

**Priority:** Must Have | **Story Points:** 5

**Acceptance Criteria:**
1. Each integration has: endpoint URL, API key (encrypted), timeout, retry policy, and circuit breaker threshold.
2. Configuration supports multiple environments: production and disaster recovery.
3. Integration health status dashboard shows last successful call, failure rate, and latency p95.
4. API keys are stored encrypted (AES-256) and never displayed in the UI after saving.
5. Failover configuration: if primary endpoint fails, system automatically switches to secondary.

---

### US-SA-006 — View Platform-Wide Audit Logs
**As a** super admin,  
**I want to** access the full audit log of all system events across all departments,  
**so that** I can investigate security incidents and compliance issues.

**Priority:** Must Have | **Story Points:** 3

**Acceptance Criteria:**
1. Audit log is tamper-evident (hash-chained entries; any deletion is detectable).
2. Log entries include: timestamp, actor (user ID + role), action type, target entity, IP address, change delta.
3. Log search supports: date range, actor, action type, entity ID, and keyword.
4. Sensitive fields (NID, PAN) are masked in audit log exports.
5. Audit logs are retained for 7 years and archived to cold storage after 1 year.

---

### US-SA-007 — Mass Notification Broadcast
**As a** super admin,  
**I want to** send system-wide or targeted notifications to citizens and officers,  
**so that** I can communicate maintenance windows, policy changes, and emergency alerts.

**Priority:** Should Have | **Story Points:** 3

**Acceptance Criteria:**
1. Notification targeting: all citizens, citizens with active applications, officers in specific departments.
2. Scheduled delivery: notifications can be queued for specific dates/times.
3. Notification content supports HTML email template and plain-text SMS.
4. Delivery status report available after broadcast: sent, delivered, failed counts.
5. Broadcast history is retained for 1 year.

---

### US-SA-008 — Backup, Recovery, and Data Export
**As a** super admin,  
**I want to** initiate database backups, verify restore integrity, and export anonymised data for analytics,  
**so that** the platform's data is protected and available for government reporting.

**Priority:** Must Have | **Story Points:** 5

**Acceptance Criteria:**
1. Automated daily database backup to S3 with 30-day retention; super admin can initiate manual backup anytime.
2. Backup restoration test runs monthly in the DR environment; results are logged.
3. Anonymised data export (NID/PAN/phone replaced with pseudonyms) available for analytics team.
4. Export includes: aggregate statistics by service type, district, and month.
5. Export files are encrypted at rest; download links expire in 24 hours.

---

## Role: Auditor (US-AUD-001..008)

### US-AUD-001 — Access Read-Only Audit Dashboard
**As an** auditor,  
**I want to** access a read-only dashboard showing all system activities, decisions, and financial transactions,  
**so that** I can conduct compliance audits without affecting platform operations.

**Priority:** Must Have | **Story Points:** 3

**Acceptance Criteria:**
1. Auditor role has read-only access; no create, update, or delete operations are available.
2. Dashboard shows: total applications by status, fee collected, certificates issued, grievances, SLA metrics.
3. Data is current to within 15 minutes (near-real-time).
4. Auditor session activity is itself logged in the audit trail.
5. Auditor login requires 2FA (OTP to registered government email).

---

### US-AUD-002 — Review Application Decision Trail
**As an** auditor,  
**I want to** review the complete decision trail for any specific application,  
**so that** I can verify that processing followed prescribed procedures.

**Priority:** Must Have | **Story Points:** 3

**Acceptance Criteria:**
1. Decision trail shows every state transition with: timestamp, actor, action, and attached documents at each stage.
2. Officer notes and escalation reasons are visible to the auditor.
3. Document version at time of decision is retrievable (documents are versioned, not overwritten).
4. Auditor can export the trail as a PDF report for inclusion in official audit reports.
5. All data is rendered in a tamper-evident chain-of-custody format.

---

### US-AUD-003 — Review Financial Transaction Audit
**As an** auditor,  
**I want to** audit all financial transactions (fees collected, waivers granted, refunds processed),  
**so that** I can verify financial accuracy and detect irregularities.

**Priority:** Must Have | **Story Points:** 5

**Acceptance Criteria:**
1. Financial audit view shows: invoice ID, application ARN, citizen ID, amount, payment gateway reference, date.
2. Fee waivers show: waiver reason, approving officer, and documentary basis.
3. Reconciliation report compares portal-recorded amounts against payment gateway settlement reports.
4. Auditor can flag transactions for further investigation; flags are visible to super admin only.
5. Transaction data is exportable to CSV for offline analysis.

---

### US-AUD-004 — Monitor SLA Compliance
**As an** auditor,  
**I want to** review SLA compliance statistics by department, service, and time period,  
**so that** I can identify systemic delays and non-compliance patterns.

**Priority:** Should Have | **Story Points:** 3

**Acceptance Criteria:**
1. SLA compliance report shows: total applications, on-time %, breach count, avg resolution time per service.
2. Drill-down by department, by officer, by service type.
3. SLA breach heat map by day-of-week and month highlights patterns.
4. Breaches caused by system downtime vs. officer inaction are categorised separately.
5. Report exportable as PDF with auditor's digital signature field for submission to ministry.

---

### US-AUD-005 — Review Grievance Redressal Records
**As an** auditor,  
**I want to** review grievance filing, resolution, and escalation records,  
**so that** I can assess the effectiveness of the redressal mechanism.

**Priority:** Should Have | **Story Points:** 3

**Acceptance Criteria:**
1. Grievance audit shows: GRN, type, department, filed date, resolved date, resolution quality rating.
2. Escalation patterns are visible: how many grievances escalated vs. resolved at first level.
3. Repeat grievances from the same citizen or about the same service are flagged.
4. Average grievance resolution time by department and category.
5. Audit findings can be annotated with auditor's notes attached to the grievance record.

---

### US-AUD-006 — Export Audit Reports for RTI Compliance
**As an** auditor,  
**I want to** generate and export statutory compliance reports for RTI responses and ministry submissions,  
**so that** transparency obligations under the RTI Act 2005 are met.

**Priority:** Must Have | **Story Points:** 5

**Acceptance Criteria:**
1. RTI report template generates: services offered, applications received, disposed, pending, and fee collected.
2. Reports are generated at district, department, and province levels.
3. PII (NID, full name) is excluded from RTI reports; aggregate and anonymised data only.
4. Report is signed with the system's audit certificate (DSC) for authenticity.
5. Report generation is logged as an audit event.

---

### US-AUD-007 — Security and Compliance Violation Review
**As an** auditor,  
**I want to** review security violation logs (failed logins, unauthorised access attempts, PII access anomalies),  
**so that** I can identify potential security threats and compliance breaches.

**Priority:** Must Have | **Story Points:** 5

**Acceptance Criteria:**
1. Security log view shows: all failed logins, locked accounts, admin privilege escalations, API key usage.
2. PII access log shows: which officer accessed which citizen's NID-linked data, when, and from which IP.
3. Anomaly detection: access patterns deviating significantly from baseline are highlighted.
4. Auditor can generate an Incident Report for any flagged security event.
5. Security audit reports are stored for 7 years per IT Act 2000 Section 67C requirements.

---

### US-AUD-008 — Verify Certificate Integrity
**As an** auditor,  
**I want to** verify the integrity of issued certificates using the QR code verification system,  
**so that** I can confirm that issued documents are genuine and unmodified.

**Priority:** Must Have | **Story Points:** 3

**Acceptance Criteria:**
1. Auditor can scan any certificate QR code or enter the certificate ID for verification.
2. Verification shows: issuance date, issuing officer designation, citizen masked identity, current validity status.
3. If a certificate was revoked, the verification page shows the revocation reason and date.
4. Bulk verification supports uploading a list of certificate IDs for batch verification reporting.
5. Verification events are logged for anti-fraud monitoring.

---

## Operational Policy Addendum

### Section 1 — Story Prioritisation Framework
Stories are prioritised using MoSCoW:
- **Must Have:** Core legal mandate; platform unusable without these features.
- **Should Have:** Significant operational value; included in Phase 1 if capacity allows.
- **Could Have:** Nice-to-have; deferred to Phase 2.
- **Won't Have (This Release):** Explicitly excluded to manage scope.

### Section 2 — Compliance Touchpoints by Story
| Regulation | Applicable Stories |
|------------|-------------------|
| NID Act 2016 | US-CIT-001, US-CIT-004, US-FO-002, US-AUD-007 |
| IT Act 2000 | US-SA-006, US-AUD-007, US-CIT-008 |
| PDPA 2023 (Nepal) | US-CIT-003, US-SA-003, US-AUD-006 |
| RTI Act 2005 | US-AUD-006, US-AUD-003 |
| eSign Act | US-FO-004, US-CIT-012, US-AUD-008 |

### Section 3 — Story Point Estimation Baseline
| Points | Effort Equivalent |
|--------|------------------|
| 1 | Trivial UI change or config update |
| 2 | Simple CRUD with standard validation |
| 3 | Feature with external dependency or complex validation |
| 5 | Multi-component feature with workflow state changes |
| 8 | Complex integration or new subsystem component |

### Section 4 — Definition of Done
A story is "Done" when:
1. Code reviewed and approved by senior developer.
2. Unit test coverage ≥ 85% for new code.
3. Integration tests pass in CI/CD pipeline.
4. Security scan (SAST) passes with no critical findings.
5. Accessibility check: WCAG 2.1 Level AA for citizen-facing stories.
6. Performance benchmark: response time within SLA under 100 concurrent users.
7. Acceptance criteria verified by QA against staging environment.
8. Documentation updated (API docs, user guide section).
