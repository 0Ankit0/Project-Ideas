# User Stories — Legal Case Management System

## Overview

This document contains user stories for the Legal Case Management System (LCMS), a SaaS platform serving law firms of all sizes. Stories are organized by functional area and span five primary personas.

**Personas**

| Code | Persona | Description |
|------|---------|-------------|
| ATT | Attorney | Licensed lawyer managing cases, client relationships, and billable work |
| PAR | Paralegal | Legal professional supporting attorneys with research, drafting, and intake |
| CLI | Client | Individual or corporate client accessing matter status and documents |
| BAD | Billing Admin | Staff responsible for time review, invoice generation, and collections |
| PRT | Partner | Equity or non-equity partner overseeing firm finances, utilization, and strategy |

---

## Case Intake & Conflict Check

**US-001 — Submit New Case Intake Form**
As a Paralegal, I want to submit a structured intake form capturing client details, matter type, opposing parties, and referral source so that a new matter can be opened without missing critical information.
Acceptance Criteria:
- Intake form includes fields for client name, contact info, matter type, date of incident/transaction, opposing parties, referred by, and notes
- Form validates required fields before submission and displays inline errors
- On successful submission, a draft matter record is created with status "Pending Conflict Check"
- An automated email notification is sent to the responsible attorney
- Intake records are auditable and timestamped with the submitting user's identity

---

**US-002 — Run Automated Conflict Check**
As an Attorney, I want the system to automatically check all parties in a new intake against existing clients, opposing parties, and related persons so that I can identify conflicts of interest before agreeing to represent a client.
Acceptance Criteria:
- Conflict check runs against all active and closed matter parties, including aliases
- Results are returned within 10 seconds for firms with up to 50,000 records
- Matches are classified as "Direct Conflict," "Potential Conflict," or "Clear" with a confidence score
- Attorney can override a Potential Conflict by documenting a written justification
- All conflict check results and overrides are stored permanently on the matter record

---

**US-003 — Assign Matter to Attorney and Practice Group**
As a Partner, I want to assign a new matter to a responsible attorney and practice group so that work is properly tracked, billed, and resourced.
Acceptance Criteria:
- Partner can select any active attorney from the firm roster as the responsible attorney
- Practice group and matter type are selected from configurable drop-downs
- Assigned attorney receives an in-app notification and email
- Matter appears in the assigned attorney's dashboard immediately after assignment
- Assignment history is logged for audit purposes

---

**US-004 — Capture Adverse Party Information**
As a Paralegal, I want to record complete information on all adverse parties and their counsel so that the system can perform accurate conflict checks and populate court documents automatically.
Acceptance Criteria:
- System supports multiple adverse parties per matter with individual records
- Each adverse party record includes name, type (individual/entity), counsel name, counsel firm, and bar number
- Adverse party information is searchable across all matters
- Changes to adverse party records trigger a re-run of the conflict check
- Adverse party data can be imported from prior matter records via a look-up

---

**US-005 — Flag Matter for Intake Review**
As an Attorney, I want to flag an intake record for partner review before formally accepting representation so that sensitive or high-risk cases receive appropriate firm-level scrutiny.
Acceptance Criteria:
- Attorney can add a review flag with a free-text reason on any pending intake
- Flagged intakes appear in a dedicated partner review queue
- Partners can approve, reject, or request more information with a written note
- Status transitions (Flagged → Under Review → Accepted / Rejected) are logged
- Rejected intakes are retained for 7 years per recordkeeping policy

---

## Matter Management

**US-006 — View Matter Dashboard**
As an Attorney, I want a single-screen matter dashboard showing open tasks, recent documents, unbilled time, upcoming deadlines, and matter contacts so that I can assess the status of any case at a glance.
Acceptance Criteria:
- Dashboard loads within 2 seconds for matters with up to 1,000 documents
- Displays current matter phase, responsible attorney, billing partner, and client
- Shows unbilled hours and WIP (work-in-progress) dollar value in real time
- Upcoming court deadlines and task due dates are listed in chronological order
- Recent document activity (uploads, edits, signatures) is shown in an activity feed

---

**US-007 — Manage Matter Phases and Milestones**
As a Paralegal, I want to move a matter through configurable phases (e.g., Intake, Discovery, Pre-Trial, Trial, Closed) and mark milestones so that the entire team understands where the case stands.
Acceptance Criteria:
- Phases are configurable per practice group by firm administrators
- Phase transitions require a checklist of required actions to be completed or deliberately waived
- Milestone completion sends notifications to the billing partner and responsible attorney
- Phase history is displayed as a timeline on the matter record
- Closing a matter requires resolution of all open tasks and a trust account balance of zero

---

**US-008 — Track Matter Contacts and Relationships**
As an Attorney, I want to associate multiple contacts with a matter—including clients, adverse parties, witnesses, experts, and judges—and define each contact's role so that all parties are accessible from a single place.
Acceptance Criteria:
- Contacts can be linked from the global contact directory or created inline
- Each linked contact has a role label configurable by practice group
- Contact records show all matters they are associated with (from the contact's profile)
- Attorney-client contacts are flagged with privilege indicators
- Exporting a matter's contact list generates a formatted PDF or CSV

---

**US-009 — Set and Track Matter Budget**
As a Partner, I want to set a fee budget for a matter (hours and dollars) and receive alerts when actuals approach or exceed the budget so that we can manage client expectations and profitability.
Acceptance Criteria:
- Budget can be set in hours, dollars, or both, with separate fields per phase
- Dashboard shows budget vs. actual (billed + WIP) with a visual progress bar
- Automatic alert is sent at 75% and 100% of budget consumption
- Budget adjustments are logged with the author, date, and reason
- Budget vs. actual data feeds into the partner reporting dashboard

---

**US-010 — Close and Archive a Matter**
As a Paralegal, I want to close a matter and move it to archive status once all work is complete, all invoices are paid, and all trust funds are disbursed so that the firm's active matter list remains clean.
Acceptance Criteria:
- Closing workflow checks for open tasks, outstanding invoices, and non-zero trust balance
- If blockers exist, system lists them and prevents closure until resolved or waived by partner
- A closing memo template is automatically generated and attached to the matter
- Archived matters remain fully searchable and all documents remain accessible
- Physical file destruction date is auto-calculated based on matter type retention schedule

---

## Document Management

**US-011 — Upload and Version-Control Documents**
As a Paralegal, I want to upload documents to a matter and have the system maintain full version history so that I can always retrieve a prior version and know who made each change.
Acceptance Criteria:
- System accepts PDF, DOCX, XLSX, PPTX, MSG, and EML file formats up to 250 MB per file
- Each upload creates a new version; prior versions are accessible from a version history panel
- Version records include uploader name, timestamp, file size, and an optional change note
- Documents are organized in configurable folder structures within each matter
- Bulk upload supports up to 50 files simultaneously with a progress indicator

---

**US-012 — Draft Documents Using Templates**
As an Attorney, I want to select a document template (e.g., Engagement Letter, Demand Letter, Pleading Cover Sheet) and have the system auto-populate matter and client fields so that I can produce consistent, accurate documents in seconds.
Acceptance Criteria:
- Template library supports DOCX templates with merge fields mapped to matter data
- Auto-populated fields include client name/address, matter number, attorney name, court, and dates
- Attorney can edit the generated document inline before saving
- Saving creates a new document version linked to the matter
- Templates are managed by firm administrators and versioned independently of matters

---

**US-013 — Send Document for E-Signature via DocuSign**
As an Attorney, I want to send a document directly to a client or opposing counsel for electronic signature through DocuSign so that I can execute agreements without printing or mailing.
Acceptance Criteria:
- Attorney can initiate a DocuSign envelope from any matter document in one click
- Multiple signers can be configured with sequenced or parallel signing order
- Signing status (Sent, Viewed, Signed, Completed, Declined) is reflected in real time on the matter
- Completed signed document is automatically saved back to the matter with a "Signed" tag
- System captures audit trail from DocuSign and stores it with the document record

---

**US-014 — Perform Full-Text Document Search**
As an Attorney, I want to search document contents across all matters I have access to using keywords so that I can quickly locate relevant precedents, clauses, or case facts.
Acceptance Criteria:
- Full-text index is updated within 5 minutes of a document upload or edit
- Search supports AND, OR, NOT operators and phrase matching with quotes
- Results display document name, matter number, matter name, and a snippet with highlighted keyword
- Results are filtered by matter access permissions; attorneys only see documents from their matters
- Search history is retained per user for the last 30 queries

---

**US-015 — Apply Document Tags and Custom Metadata**
As a Paralegal, I want to apply custom tags and metadata fields (e.g., Privilege, Work Product, Confidential, Exhibit Number) to documents so that I can filter and organize large document sets efficiently.
Acceptance Criteria:
- Tags are firm-configurable and color-coded
- Multiple tags can be applied to a single document
- Documents can be filtered by one or more tags within a matter
- Tagged documents can be exported as a tagged index list
- Privilege tags trigger a warning if a user attempts to share the document externally

---

## Time Entry & Billing

**US-016 — Log Billable Time with UTBMS Task Codes**
As an Attorney, I want to record time entries using ABA UTBMS task codes and activity codes so that invoices comply with LEDES billing standards required by corporate clients.
Acceptance Criteria:
- Time entry form includes date, matter, timekeeper, hours (in 0.1-hour increments), UTBMS task code, activity code, and narrative
- UTBMS task code and activity code drop-downs are searchable and filtered by practice area
- System validates that a narrative is present for any entry exceeding 0.5 hours
- Entries can be created from a running timer widget accessible from any screen
- Bulk time import is supported via CSV for migration from prior systems

---

**US-017 — Edit and Approve Time Entries Before Billing**
As a Billing Admin, I want to review, edit, and approve or reject time entries before they are included in an invoice so that billing narratives are professional and entries are accurate.
Acceptance Criteria:
- Billing Admin sees a pre-bill queue showing all unapproved entries by attorney and matter
- Each entry can be edited (narrative, hours, task code) with an audit note
- Rejected entries are returned to the originating attorney with a rejection reason
- Approved entries are locked and cannot be edited without a billing partner override
- Pre-bill review workflow supports configurable approval tiers (e.g., attorney self-review → billing admin → partner)

---

**US-018 — Generate LEDES 1998B Invoice**
As a Billing Admin, I want to generate a LEDES 1998B-formatted invoice from approved time and expense entries so that I can submit invoices directly to corporate client e-billing portals.
Acceptance Criteria:
- System produces a valid LEDES 1998B file with all required fields populated from matter data
- LEDES file passes standard format validation before download is offered
- Invoice is also rendered as a human-readable PDF for client records
- Generated invoices are stored on the matter with status, version, and send date
- System supports LEDES 1998BI (with insurance-specific fields) as a configurable option

---

**US-019 — Apply Retainer and Trust Funds to Invoice**
As a Billing Admin, I want to apply funds held in a client's IOLTA trust account against an outstanding invoice so that the trust account is properly debited and the invoice is marked paid.
Acceptance Criteria:
- System shows available trust balance alongside invoice amount during payment application
- Applying trust funds creates a corresponding trust disbursement transaction with memo
- If trust balance is less than invoice total, system applies partial payment and shows the remaining balance
- Transaction records include matter number, payee, check number, date, and purpose per IOLTA rules
- Client receives an automated email receipt showing trust draw-down and invoice settlement

---

**US-020 — Record Expense Disbursements**
As a Paralegal, I want to log out-of-pocket expenses (e.g., filing fees, courier, travel) against a matter so that they can be billed to the client with supporting receipts attached.
Acceptance Criteria:
- Expense form includes date, matter, category (from configurable list), amount, description, and receipt upload
- Expenses can be marked billable or non-billable; only billable expenses appear on invoices
- Receipts are stored as attachments to the expense record on the matter
- Expense report for a date range can be exported per matter or per timekeeper
- Markup percentage rules can be configured per expense category by firm administrators

---

**US-021 — Set Up Billing Arrangements per Matter**
As a Partner, I want to configure the billing arrangement for each matter (hourly, flat fee, contingency, blended rate) so that time entry and invoice generation respect the agreed fee structure.
Acceptance Criteria:
- Supported arrangements: Hourly (standard rates or matter-specific rates per timekeeper), Flat Fee, Contingency, Retainer with hourly draw-down, Blended Rate
- Timekeeper-specific rates at the matter level override firm default rates
- Flat fee matters display billed vs. remaining flat fee budget on the dashboard
- Contingency matters track total time invested without invoicing until resolution
- Billing arrangement is locked once the first invoice is sent; changes require partner override

---

## IOLTA Trust Accounting

**US-022 — Open and Manage IOLTA Trust Account**
As a Billing Admin, I want to open and configure an IOLTA trust ledger for a client so that client funds are tracked separately from firm operating funds in compliance with state bar rules.
Acceptance Criteria:
- Each trust ledger is linked to a specific client and bank account (3-way reconciliation supported)
- System enforces that trust funds are never commingled with operating funds
- Every trust transaction (receipt, disbursement, transfer) requires matter number, description, and authorization
- Trust account balance can never go negative at the individual client ledger level
- System generates a 3-way reconciliation report (bank balance vs. book balance vs. individual ledger sum) on demand

---

**US-023 — Record Trust Fund Receipt**
As a Billing Admin, I want to record an incoming trust deposit (e.g., client advance, settlement proceeds) so that the client's trust ledger immediately reflects the available funds.
Acceptance Criteria:
- Receipt entry includes date, amount, payer, payment method (check, wire, ACH), check number, and purpose
- Cleared funds indicator can be toggled; disbursements against uncleared funds require partner override
- Receipt automatically updates the client's individual ledger balance and the pooled trust account total
- System prints a trust receipt PDF for client delivery
- Duplicate receipt detection warns if same amount, payer, and date are entered within 24 hours

---

**US-024 — Disburse Trust Funds**
As a Billing Admin, I want to record a trust disbursement (e.g., payment to client, settlement payment, transfer to operating for earned fees) so that the ledger accurately reflects all outgoing trust transactions.
Acceptance Criteria:
- Disbursement requires authorization from an attorney or partner (two-factor for amounts above $10,000)
- System prevents disbursement if it would result in a negative individual client ledger balance
- Each disbursement generates a trust check record with payee, amount, memo, and check number
- Transfer to operating account for earned fees is recorded as a separate transaction type
- Monthly trust account statement is auto-generated showing all activity per client ledger

---

## Court Calendar & Deadlines

**US-025 — Enter and Track Court Deadlines**
As a Paralegal, I want to manually enter court-ordered deadlines and hearing dates on a matter and have the system automatically calculate derivative deadlines (e.g., discovery cutoff, response deadlines) based on configurable rules so that no critical date is missed.
Acceptance Criteria:
- User enters a trigger date and selects a deadline rule set; system calculates all dependent dates
- Deadline rule sets are configurable per jurisdiction and matter type (civil, criminal, family, etc.)
- Calculated deadlines can be individually adjusted with a notation of the reason
- All deadlines are visible on a firm-wide calendar filterable by attorney, practice group, or matter
- Deadlines within 14 days appear highlighted in amber; overdue deadlines appear in red

---

**US-026 — Receive Deadline Reminder Notifications**
As an Attorney, I want to receive automated email and in-app reminders at configurable intervals before a deadline so that I have adequate time to prepare and file.
Acceptance Criteria:
- Default reminder schedule: 30 days, 14 days, 7 days, 3 days, 1 day before deadline
- Reminder schedule is customizable per matter and per deadline type
- Reminders are sent to the responsible attorney and any additional attendees specified
- Reminders include matter name, matter number, deadline type, due date, and a deep link to the matter
- SMS reminders are available as an opt-in feature per user

---

**US-027 — Sync Deadlines with Google Calendar and Outlook**
As an Attorney, I want court deadlines and hearing dates to sync automatically with my Google Calendar or Microsoft Outlook calendar so that my schedule reflects all legal commitments in one place.
Acceptance Criteria:
- OAuth 2.0 integration supports Google Calendar and Microsoft 365 / Outlook
- New deadlines are pushed to the attorney's calendar within 60 seconds of creation
- Updated or deleted deadlines are reflected in the external calendar within 60 seconds
- Calendar event includes matter name, matter number, deadline type, location (if applicable), and notes
- Sync can be enabled or disabled per user; attorneys can choose which deadline types to sync

---

**US-028 — View Firm-Wide Docket Calendar**
As a Partner, I want to view a firm-wide calendar showing all hearings, deadlines, and key dates across all active matters so that I can identify scheduling conflicts and resource constraints.
Acceptance Criteria:
- Calendar supports month, week, and list views with filtering by attorney, practice group, and matter type
- Color coding distinguishes hearings, deadlines, tasks, and statute of limitations dates
- Partner can click any calendar entry to navigate directly to the underlying matter
- Calendar can be exported as a PDF or iCalendar (.ics) file for the current view
- Conflicts (same attorney, overlapping times) are flagged with a warning icon

---

## Client Portal

**US-029 — Access Matter Status via Client Portal**
As a Client, I want to log in to a secure online portal and see the current status of my matters, recent activity, and upcoming dates so that I stay informed without having to call the firm.
Acceptance Criteria:
- Client portal is accessible at a firm-branded subdomain (e.g., clientportal.smithlaw.com)
- Clients only see matters to which they are linked; multi-matter clients see all their matters
- Matter status, responsible attorney, and next scheduled date are shown for each matter
- Recent activity feed shows document uploads, invoice generation, and key milestone completions
- Portal requires MFA (email OTP or authenticator app) for all logins

---

**US-030 — Download Invoices and Make Payments via Client Portal**
As a Client, I want to download my invoices and pay outstanding balances online via credit card or ACH so that I can settle accounts without mailing a check.
Acceptance Criteria:
- Invoices are listed with status (Outstanding, Partially Paid, Paid, Overdue) and amount due
- Clients can download PDF invoices with one click
- Online payment is processed via Stripe; supported methods include Visa, Mastercard, Amex, and ACH
- Payment confirmation is displayed immediately and an email receipt is sent automatically
- Payments are automatically recorded in the billing system and applied to the correct invoice

---

**US-031 — Upload Documents to Client Portal**
As a Client, I want to upload documents requested by my attorney directly through the client portal so that I can share files securely without using unencrypted email.
Acceptance Criteria:
- Clients can upload files up to 100 MB per file; accepted formats include PDF, DOCX, JPEG, PNG, HEIC
- Uploaded files are stored in a dedicated "Client Uploads" folder within the matter
- Attorney and paralegal receive an in-app notification and email when a client uploads a file
- Clients can see the status of their uploads (Received, Under Review, Reviewed) updated by the attorney
- All file transfers are encrypted in transit (TLS 1.3) and at rest (AES-256)

---

**US-032 — Send and Receive Secure Messages via Client Portal**
As a Client, I want to send and receive messages with my attorney through the portal so that our communications are privileged, documented, and not scattered across personal email threads.
Acceptance Criteria:
- Messaging is threaded per matter with timestamps and read receipts
- Attorneys and paralegals can reply from the LCMS desktop interface; clients reply from the portal
- Messages are encrypted end-to-end; no message content is stored in plaintext
- Attachments up to 25 MB can be sent in messages
- Firm can configure an auto-reply message for after-hours messages with expected response time

---

## Reporting & Analytics

**US-033 — View Attorney Utilization Report**
As a Partner, I want to view a utilization report showing billable hours worked, billed, and collected per attorney for a selectable date range so that I can assess productivity and identify underperforming timekeepers.
Acceptance Criteria:
- Report displays hours worked, hours billed, realization rate (billed/worked), and collection rate (collected/billed)
- Data can be sliced by attorney, practice group, matter type, and date range
- Report includes a comparison to prior period and target utilization percentage
- Partners can export the report as PDF or XLSX
- Data refreshes on a nightly batch; real-time estimates are shown with a "as of" timestamp

---

**US-034 — Run Accounts Receivable Aging Report**
As a Billing Admin, I want to run an A/R aging report showing all outstanding invoice balances categorized by age (0–30, 31–60, 61–90, 90+ days) so that I can prioritize collection efforts.
Acceptance Criteria:
- Report lists each client, matter, invoice number, original amount, amount paid, balance due, and aging bucket
- Overdue balances exceeding 90 days are highlighted in red
- Billing Admin can send a collection reminder email directly from the report row with one click
- Report can be filtered by responsible attorney, billing partner, or practice group
- Report data can be exported to CSV and synced to QuickBooks Accounts Receivable

---

**US-035 — Generate Matter Profitability Report**
As a Partner, I want to see the profitability of each matter (fees billed minus timekeeper cost) so that I can evaluate which client relationships and matter types are most profitable.
Acceptance Criteria:
- Report calculates gross margin as: fees billed − (hours worked × standard cost rate per timekeeper)
- Cost rates are configurable per timekeeper and are not exposed to clients or non-partner users
- Results can be sorted by margin (absolute or percentage) to identify highest and lowest profit matters
- Report includes originating partner attribution for business development analysis
- Historical profitability data is retained for closed matters and included in trend analysis

---

**US-036 — Export Data to QuickBooks**
As a Billing Admin, I want to export billing and trust accounting transactions to QuickBooks Online so that the firm's general ledger is kept in sync without manual data entry.
Acceptance Criteria:
- QuickBooks Online integration supports OAuth 2.0 connection from the firm's settings page
- Exported data includes invoices, payments received, trust receipts, and trust disbursements
- Export runs automatically on a nightly schedule; manual on-demand export is also available
- Failed exports generate an error notification to the Billing Admin with the specific record and error message
- Exported records are tagged with a QuickBooks sync status (Pending, Synced, Error) in LCMS

---

**US-037 — Set Up and Monitor Staff Performance KPIs**
As a Partner, I want to configure performance KPIs for each timekeeper (target billable hours, target realization, target collection rate) and track actuals against targets so that performance conversations are data-driven.
Acceptance Criteria:
- KPI targets are set per timekeeper for each calendar year or custom period
- Dashboard widget shows each timekeeper's progress toward KPI targets with a RAG status (Red/Amber/Green)
- Partners receive a weekly KPI digest email summarizing firm-wide performance
- KPI data is restricted to partners and firm administrators; individual attorneys only see their own KPIs
- Historical KPI attainment is stored for annual performance review purposes

---

## System Administration & Security

**US-038 — Configure Role-Based Access Control**
As a Partner (acting as Firm Administrator), I want to define permission roles (e.g., Attorney, Paralegal, Billing Admin, Read-Only) and assign users to roles so that staff only access data relevant to their function.
Acceptance Criteria:
- Predefined roles are available out of the box with sensible default permissions
- Custom roles can be created with granular permissions at the feature level
- Matter-level access can be restricted to assigned team members only, regardless of firm role
- User role assignments are logged and auditable
- Role changes take effect immediately without requiring the affected user to log out

---

**US-039 — Enforce Multi-Factor Authentication**
As a Partner (acting as Firm Administrator), I want to require MFA for all user logins so that unauthorized access to sensitive legal and financial data is prevented even if credentials are compromised.
Acceptance Criteria:
- MFA can be enforced at the firm level; users cannot opt out when enforcement is active
- Supported second factors: TOTP authenticator app (Google Authenticator, Authy), email OTP, hardware key (FIDO2/WebAuthn)
- MFA enrollment is required on first login after enforcement is activated; login is blocked until enrollment is complete
- Administrators can view MFA enrollment status for all users and force re-enrollment
- Failed MFA attempts are logged and trigger an alert after 5 consecutive failures

---

**US-040 — Receive System Audit Log**
As a Partner (acting as Firm Administrator), I want to view a complete audit log of user actions (logins, data access, edits, exports, deletions) so that I can investigate security incidents and demonstrate compliance.
Acceptance Criteria:
- Audit log captures: timestamp, user identity, action type, affected record type and ID, IP address, and result (success/failure)
- Log is immutable; no user (including administrators) can delete or modify audit entries
- Log can be filtered by user, action type, date range, and affected record type
- Log can be exported as CSV for ingestion into a SIEM or external compliance tool
- Audit log is retained for a minimum of 7 years per legal recordkeeping requirements
