# Use Case Descriptions — Legal Case Management System

## Overview

This document provides detailed use case descriptions for the six core use cases of the Legal Case Management System (LCMS). Each use case follows a structured template aligned with UML and IEEE 830 conventions, extended with legal-domain business rules.

**Notation**
- `[S]` = System action
- `[U]` = User (actor) action
- `BR-XXX` = Business Rule cross-reference

---

## Use Case Index

| UC ID | Name | Primary Actor | Complexity |
|-------|------|---------------|------------|
| UC-01 | Case Intake | Paralegal | Medium |
| UC-02 | Conflict Check | Attorney | High |
| UC-03 | Document Draft from Template | Attorney / Paralegal | Medium |
| UC-04 | Time Entry | Attorney / Paralegal | Low |
| UC-05 | Invoice Generation | Billing Admin | High |
| UC-06 | Court Deadline Alert | System (automated) | Medium |

---

## UC-01 — Case Intake

**Use Case ID:** UC-01
**Name:** Case Intake
**Version:** 1.2
**Status:** Approved
**Last Updated:** 2025-01

**Actors**

| Role | Type | Description |
|------|------|-------------|
| Paralegal | Primary | Initiates and completes the intake form on behalf of the prospective client |
| Attorney | Secondary | Reviews and approves the intake before matter creation |
| System | Supporting | Validates data, creates draft matter, triggers notifications |

**Preconditions**
- The Paralegal is authenticated and has the "Intake Create" permission
- The prospective client is not yet in the system (or is a returning client with a new matter)
- At least one attorney is active and available for assignment

**Trigger**
A prospective client contacts the firm by phone, web form, email, or referral and expresses intent to engage legal services.

**Main Flow**

1. [U] Paralegal navigates to **Matters → New Intake** and selects **Start Intake Form**
2. [S] System presents a multi-section intake form with the following sections: (a) Client Information, (b) Matter Details, (c) Adverse Parties, (d) Prior Representation, (e) Referral Information
3. [U] Paralegal completes Section (a): client name, date of birth / incorporation date, address, phone, email, client type (Individual / Business / Government)
4. [U] Paralegal completes Section (b): matter type (from configurable taxonomy), jurisdiction, court (if known), estimated case value, date of incident or transaction, brief description
5. [U] Paralegal completes Section (c): adverse party name(s), adverse counsel name(s), adverse counsel firm(s), bar numbers
6. [U] Paralegal completes Section (d): has the prospective client previously been represented by this firm? (Yes / No); if Yes, selects prior matters
7. [U] Paralegal completes Section (e): referral source (from configurable list), referral attorney name (if applicable)
8. [U] Paralegal clicks **Submit Intake**
9. [S] System validates all required fields; if validation passes, creates a draft matter record with status **"Pending Conflict Check"** and a system-generated matter number (e.g., `LIT-2025-04312`)
10. [S] System logs the intake creation event in the audit trail
11. [S] System sends an email notification to the designated intake review attorney with a summary and a deep link to the draft matter
12. [S] System automatically initiates UC-02 (Conflict Check) in the background
13. [U] Paralegal is redirected to the draft matter dashboard showing the pending conflict check status

**Alternate Flows**

*AF-01: Returning Client — Existing record found*
- At step 3, if the client's email or phone matches an existing contact, [S] system displays a match suggestion
- [U] Paralegal selects the existing contact; system pre-fills all known fields from the existing record
- [U] Paralegal reviews and updates any changed details, then continues from step 4

*AF-02: Web Intake Form Submission*
- Client submits a public-facing web intake form hosted by the firm
- [S] System creates a draft intake record with status **"Needs Review"** and notifies the intake coordinator
- [U] Intake coordinator reviews, supplements missing data, and progresses to step 8
- Remaining flow is identical to Main Flow from step 9 onward

*AF-03: Paralegal saves form as draft*
- At any point between steps 3–7, Paralegal can click **Save Draft**
- [S] System saves the partially completed form; Paralegal can return and resume later
- Draft intakes are listed in the **My Drafts** queue and automatically purged after 30 days if not submitted

**Exception Flows**

*EF-01: Duplicate intake detected*
- At step 9, if a matter with the same client and matter type was created within the last 90 days, [S] system displays a warning: "Possible duplicate intake detected. View existing matter?"
- [U] Paralegal can proceed anyway (creating a new matter) or navigate to the existing matter
- If proceeding, system appends a duplicate-detection note to the audit log

*EF-02: Required field missing*
- At step 9, if required fields are missing, [S] system highlights each missing field with an inline error message
- Form is not submitted; Paralegal must resolve all errors before resubmitting

*EF-03: System unavailable*
- If the system is unavailable during submission, [S] system queues the intake and notifies the Paralegal that it will be processed when connectivity is restored
- A confirmation number is displayed for tracking

**Postconditions**
- A draft matter record exists with status "Pending Conflict Check" or "Needs Attorney Review"
- The conflict check process (UC-02) has been initiated
- All intake data is stored and auditable
- Responsible attorney has been notified

**Business Rules Referenced**

| Rule ID | Description |
|---------|-------------|
| BR-101 | Every matter must have a unique system-generated matter number before any work is recorded |
| BR-102 | Adverse party information is required before the conflict check can proceed |
| BR-103 | A matter may not be opened if a Direct Conflict is identified and not overridden by a Partner |
| BR-104 | Intake records must be retained for a minimum of 7 years after matter closure |

---

## UC-02 — Conflict Check

**Use Case ID:** UC-02
**Name:** Conflict Check
**Version:** 1.3
**Status:** Approved
**Last Updated:** 2025-01

**Actors**

| Role | Type | Description |
|------|------|-------------|
| System | Primary | Executes the automated conflict search against the firm's party index |
| Attorney | Secondary | Reviews results and decides whether to proceed with representation |
| Partner | Secondary | Approves overrides when a potential conflict is flagged |

**Preconditions**
- A draft matter record exists (output of UC-01)
- The party index contains all active and closed matter parties, including aliases
- The conflict check engine is operational

**Trigger**
Automatically triggered at the end of UC-01 (step 12) or manually initiated by an Attorney from the matter record.

**Main Flow**

1. [S] System extracts all party names from the draft matter: client name, client aliases, adverse party names, adverse party counsel names, and their respective firms
2. [S] System normalizes names (strip punctuation, expand common abbreviations, handle entity suffixes: Inc., LLC, Corp., etc.) to reduce false negatives
3. [S] System executes a fuzzy-match search against the Party Index, which contains:
   - All current clients (active and inactive)
   - All adverse parties from all matters (active and closed)
   - All related parties (guarantors, officers, witnesses) from all matters
   - All attorneys associated with the firm (current and former)
4. [S] System classifies each match:
   - **Direct Conflict**: Same party is both a current client AND an adverse party in the proposed matter; or a current attorney has a disqualifying personal relationship
   - **Potential Conflict**: Fuzzy match with confidence ≥ 70%; same entity appears in related matters with different roles; lateral hire conflicts
   - **Clear**: No matches found or all matches below the 30% confidence threshold
5. [S] System compiles the Conflict Check Report including: match type, confidence score, matched record (party name, matter number, matter status), and suggested action
6. [S] System updates the draft matter status:
   - Direct Conflict → **"Conflict Identified — Blocked"**
   - Potential Conflict → **"Potential Conflict — Needs Review"**
   - Clear → **"Conflict Clear — Ready for Assignment"**
7. [S] System notifies the responsible attorney and intake coordinator with the conflict check result and a link to the full report
8. [U] Attorney reviews the Conflict Check Report on the matter record
9. **If Clear:** Attorney proceeds with matter opening (no further action required for this use case)
10. **If Potential Conflict:** Attorney reviews each flagged item, marks each as "Confirms Conflict" or "Not a Conflict — Explain," and enters a written justification for non-conflict determinations; if all items resolved as non-conflict, status changes to "Conflict Clear — Ready for Assignment"
11. **If Direct Conflict:** Attorney cannot proceed unilaterally; case is escalated to a Partner (proceed to step 12)
12. [U] Partner reviews the Direct Conflict details; Partner may (a) confirm the conflict and reject the intake or (b) document an ethics opinion or written consent from all parties and override the conflict
13. [S] If override approved, system records the override with Partner identity, timestamp, and justification; matter status changes to "Conflict Overridden — Ready for Assignment"
14. [S] If intake rejected, matter status changes to "Rejected — Conflict" and a rejection reason is stored permanently

**Alternate Flows**

*AF-01: Manual conflict check requested*
- Attorney or Paralegal can trigger a conflict check at any time from an existing matter record
- Flow begins at step 1 with the existing matter's party data
- Previous conflict check results are retained; new results are appended with timestamp

*AF-02: Lateral hire conflict*
- When a new attorney joins the firm and their employment record is created, system automatically runs a conflict check against their prior employer's matters
- Matches are presented to the Managing Partner for review
- Matters where a conflict is identified are screened off from the new hire

**Exception Flows**

*EF-01: Conflict check engine timeout*
- If the search engine does not return results within 30 seconds, [S] system marks the check as "Pending — Engine Timeout" and retries after 5 minutes
- Responsible attorney is notified; matter cannot proceed to open status until a result is obtained

*EF-02: Party index out of sync*
- If the party index has not been updated in more than 24 hours, [S] system displays a banner warning on the conflict report indicating that results may be stale
- A system alert is generated for the IT administrator

**Postconditions**
- A Conflict Check Report is permanently associated with the matter record
- Matter status reflects the conflict check outcome
- All overrides are documented with full audit trail
- No matter with status "Conflict Identified — Blocked" can progress to "Active" without a documented override

**Business Rules Referenced**

| Rule ID | Description |
|---------|-------------|
| BR-201 | A conflict check must be completed before a matter can be set to Active status |
| BR-202 | Direct Conflict overrides require Partner-level authorization and written documentation |
| BR-203 | Conflict check results must be retained permanently on the matter record |
| BR-204 | Fuzzy match threshold for Potential Conflict classification is 70% similarity (configurable by firm admin) |
| BR-205 | Lateral hire conflicts must be assessed within 48 hours of attorney onboarding |

---

## UC-03 — Document Draft from Template

**Use Case ID:** UC-03
**Name:** Document Draft from Template
**Version:** 1.1
**Status:** Approved
**Last Updated:** 2025-01

**Actors**

| Role | Type | Description |
|------|------|-------------|
| Attorney | Primary | Selects template and reviews/edits the generated document |
| Paralegal | Primary | May also initiate document generation on behalf of the attorney |
| System | Supporting | Merges template with matter data and creates document record |

**Preconditions**
- The matter has Active status
- At least one document template is configured and published in the template library
- The user has "Document Create" permission on the matter

**Trigger**
Attorney or Paralegal initiates document creation from the matter's Documents tab.

**Main Flow**

1. [U] User navigates to the matter's **Documents** tab and clicks **New Document → From Template**
2. [S] System presents the Template Library, filtered to templates applicable to the matter's practice group and matter type
3. [U] User selects a template (e.g., "Engagement Letter — Litigation" or "Demand Letter — Personal Injury")
4. [S] System displays a preview of the template with identified merge fields highlighted (e.g., `{{ClientFullName}}`, `{{MatterNumber}}`, `{{CourtName}}`)
5. [S] System resolves and populates merge fields from matter data:
   - Client fields: full name, address, phone, email
   - Matter fields: matter number, matter type, responsible attorney name and bar number, practice group
   - Court fields: court name, division, judge name, docket number (if entered on matter)
   - Firm fields: firm name, address, phone, managing partner name
   - Date fields: today's date, statute of limitations date (if applicable)
6. [S] System flags any merge fields it could not resolve (missing data) in yellow; user must resolve flagged fields before finalizing
7. [U] User reviews the populated document in an inline rich-text editor (DOCX rendered as HTML)
8. [U] User edits content as needed, resolves any flagged fields manually
9. [U] User clicks **Save Document** and optionally enters a document title and selects a destination folder within the matter
10. [S] System saves the document as version 1.0, records metadata (creator, creation timestamp, template used, merge field values at time of generation), and indexes content for full-text search
11. [S] System adds an entry to the matter's activity feed: "Document created: [Document Title] from template [Template Name]"
12. [U] User is redirected to the document detail view; available actions include Download (PDF/DOCX), Send for Signature, Share with Client

**Alternate Flows**

*AF-01: Send directly for e-signature after generation*
- At step 12, user clicks **Send for Signature**
- System initiates DocuSign envelope creation (see integration with DocuSign)
- User configures signers, signing order, and expiry; clicks **Send**
- Document status changes to "Pending Signature"

*AF-02: Save as firm-wide template*
- After editing at step 8, an attorney with Template Manager permission can click **Save as Template**
- System prompts for template name, applicable practice groups, and visibility (firm-wide / practice group only)
- Saved template appears in the Template Library pending Firm Administrator approval

**Exception Flows**

*EF-01: Template merge field data incomplete*
- At step 6, if more than 5 merge fields cannot be resolved, [S] system warns: "This document has significant missing data. Complete the matter record before generating this document."
- User can proceed anyway (all missing fields will be highlighted) or cancel and complete the matter record first

*EF-02: Template version mismatch*
- If the template has been updated since the document was last generated, [S] system notifies the user at step 4: "A newer version of this template is available. Use the updated version?"
- User can choose to use the current version or the updated version

*EF-03: Concurrent edit conflict*
- If two users attempt to save edits to the same document simultaneously, [S] system detects the conflict and presents both versions to the second saver with a merge view
- Second saver must manually reconcile differences before saving

**Postconditions**
- A new versioned document record exists on the matter
- Document is indexed for full-text search
- Merge field values at generation time are stored for audit
- Activity feed on the matter is updated

**Business Rules Referenced**

| Rule ID | Description |
|---------|-------------|
| BR-301 | Documents generated from templates must retain the template version reference for audit purposes |
| BR-302 | Documents marked "Attorney-Client Privileged" cannot be shared externally without attorney override |
| BR-303 | Engagement letters must be sent for e-signature before any billable time is recorded on a new matter |
| BR-304 | Completed signed documents returned from DocuSign are automatically saved as a new version with "Executed" status |

---

## UC-04 — Time Entry

**Use Case ID:** UC-04
**Name:** Time Entry
**Version:** 1.4
**Status:** Approved
**Last Updated:** 2025-01

**Actors**

| Role | Type | Description |
|------|------|-------------|
| Attorney | Primary | Logs time spent on billable and non-billable legal work |
| Paralegal | Primary | Logs time for administrative and substantive legal tasks |
| Billing Admin | Secondary | Reviews and adjusts time entries in the pre-bill review workflow |
| System | Supporting | Validates entries, calculates fees, flags policy violations |

**Preconditions**
- The matter has Active status and a billing arrangement is configured
- The timekeeper (Attorney or Paralegal) is assigned a billable rate (firm default or matter-specific)
- The timekeeper is a member of the matter team or has firm-wide time entry permission

**Trigger**
Timekeeper manually creates a time entry, or a running timer is stopped and converted to a time entry.

**Main Flow**

1. [U] Timekeeper navigates to **Time → New Entry** (or clicks **Stop Timer** on an active timer)
2. [S] System pre-populates entry date (today), timekeeper (current user), and start time (if from timer)
3. [U] Timekeeper selects the matter from a searchable drop-down (filtered to matters where the user is a team member or has access)
4. [U] Timekeeper enters the number of hours worked (minimum 0.1, in 0.1-hour increments)
5. [U] Timekeeper selects a UTBMS Task Code (e.g., L110 — Fact Investigation/Development) from a searchable drop-down filtered by matter's practice area
6. [U] Timekeeper selects a UTBMS Activity Code (e.g., A103 — Draft/Revise) to specify the type of work performed
7. [U] Timekeeper enters a billing narrative describing the work performed
8. [U] Timekeeper confirms the entry is Billable or Non-Billable; if non-billable, selects a reason code (e.g., No Charge, Write-Off, Administrative)
9. [U] Timekeeper clicks **Save Entry**
10. [S] System validates the entry (see BR-401 through BR-405)
11. [S] System calculates the fee: Hours × Timekeeper rate for the matter (or firm default if no matter-specific rate); marks fee as "WIP" (Work in Progress)
12. [S] System saves the entry with status "Pending Review" and updates the matter's WIP balance
13. [S] System logs the entry creation in the audit trail

**Alternate Flows**

*AF-01: Timer-based time capture*
- Timekeeper starts a timer from the matter dashboard by clicking **Start Timer**
- [S] System begins a running timer displayed persistently in the navigation bar
- When the timekeeper finishes the task, they click **Stop & Log**
- [S] System converts elapsed time (rounded up to the next 0.1 hour) into a pre-populated time entry form
- Timekeeper completes steps 5–9 of the Main Flow

*AF-02: Batch time entry (end-of-day)*
- Timekeeper navigates to **Time → Batch Entry** to enter multiple entries at once
- A grid interface allows rapid entry of date, matter, hours, task code, and narrative for up to 20 entries simultaneously
- Entries are validated and saved in bulk; failures are highlighted without blocking successful entries

*AF-03: Time entry on flat-fee matter*
- System allows time to be logged for tracking and reporting purposes
- Fee calculation is suppressed (no WIP value is added to the invoice)
- Hours are visible in profitability analysis to measure investment on the flat-fee engagement

**Exception Flows**

*EF-01: Narrative missing*
- At step 10, if the entry is billable and the narrative is blank or fewer than 10 characters, [S] system blocks the save and prompts: "A billing narrative is required for billable entries."

*EF-02: Duplicate entry detected*
- At step 10, if an entry with the same timekeeper, matter, date, hours, and task code was saved within the last 2 hours, [S] system displays a warning: "Possible duplicate entry detected." Timekeeper can confirm save or cancel.

*EF-03: Entry on closed or inactive matter*
- At step 3, if the selected matter is Closed or Archived, [S] system displays an error: "Time cannot be logged on a closed matter. Contact your billing admin to reopen the matter."

*EF-04: Entry date in a closed billing period*
- At step 2 or when the timekeeper changes the date, if the date falls in a billing period that has been locked by the Billing Admin, [S] system displays a warning and prevents saving unless the timekeeper has override permission

**Postconditions**
- A time entry record exists with status "Pending Review"
- Matter WIP balance is updated
- Billing Admin pre-bill queue is updated with the new entry
- Audit log reflects the creation

**Business Rules Referenced**

| Rule ID | Description |
|---------|-------------|
| BR-401 | All billable time entries must have a UTBMS task code and activity code |
| BR-402 | A billing narrative is required for any billable entry exceeding 0.5 hours |
| BR-403 | Time entries must be submitted within 5 business days of the work date (configurable by firm) |
| BR-404 | Time entries in a locked billing period require Billing Admin override to modify |
| BR-405 | Non-billable entries must include a reason code for reporting and write-off tracking |

---

## UC-05 — Invoice Generation

**Use Case ID:** UC-05
**Name:** Invoice Generation
**Version:** 1.5
**Status:** Approved
**Last Updated:** 2025-01

**Actors**

| Role | Type | Description |
|------|------|-------------|
| Billing Admin | Primary | Initiates and controls the invoice generation process |
| Partner | Secondary | Approves invoices above a configurable threshold before sending |
| Attorney | Secondary | Reviews pre-bill and approves their own entries (if configured) |
| System | Supporting | Calculates invoice totals, generates LEDES file, sends invoice to client |
| Client | Recipient | Receives invoice via email and/or client portal |

**Preconditions**
- The matter has Active status and at least one approved, billable time or expense entry in the current billing period
- The billing arrangement is configured on the matter
- The client record has a valid billing email address
- The billing period for the invoice is not already invoiced

**Trigger**
Billing Admin initiates invoice generation for one or more matters (individually or via batch billing run).

**Main Flow**

1. [U] Billing Admin navigates to **Billing → Generate Invoices** and selects a billing period (month) and optionally filters by attorney, practice group, or specific matters
2. [S] System presents a pre-bill list showing all matters with unbilled approved entries in the selected period, with totals and WIP summaries
3. [U] Billing Admin selects matters to include in the billing run (all or a subset)
4. [U] Billing Admin clicks **Review Pre-Bill** for the first matter
5. [S] System displays all approved time entries and expense entries for the matter, grouped by timekeeper and task code, with calculated fees
6. [U] Billing Admin reviews each entry; may edit narratives, adjust hours (with audit note), or remove entries from this invoice (moved back to WIP)
7. [U] Billing Admin applies any discounts (flat amount or percentage) at the invoice level with a written justification
8. [U] Billing Admin marks the pre-bill as **Ready to Invoice**
9. **If partner approval required (invoice total ≥ configured threshold):**
   - [S] System routes invoice to the billing partner for approval
   - [U] Partner reviews the pre-bill and approves or rejects with comments
   - [S] If rejected, invoice returns to Billing Admin with partner comments; Billing Admin addresses and resubmits
10. [U] Billing Admin (or Partner after approval) clicks **Generate Invoice**
11. [S] System assigns an invoice number (sequential, configurable prefix, e.g., `INV-2025-0421`)
12. [S] System calculates invoice totals: subtotal by timekeeper, subtotal by task code, expenses subtotal, tax (if applicable per jurisdiction), total due
13. [S] System generates:
    - A PDF invoice in the firm's branded template
    - A LEDES 1998B text file (if required by client billing profile)
14. [S] System saves both documents on the matter; updates matter financial summary (invoiced to date, outstanding balance)
15. [S] System sends invoice to the client via:
    - Email (PDF attached; LEDES file attached if configured)
    - Client portal notification (invoice appears in client's portal billing section)
16. [S] System updates invoice status to "Sent" and logs delivery timestamp
17. [S] System records the billing event in the audit trail

**Alternate Flows**

*AF-01: Batch billing run*
- Billing Admin selects multiple matters in step 3
- Pre-bill review is completed for each matter in sequence
- Invoices are generated simultaneously for all "Ready to Invoice" matters
- A batch run summary report is generated showing all invoices created, total billed, and any errors

*AF-02: Credit memo issuance*
- Billing Admin selects **New Credit Memo** for a matter with a previous invoice
- Enters the reason and credit amount; system generates a negative-amount invoice (credit memo)
- Credit memo is applied to the client's account balance

*AF-03: Apply trust retainer to invoice*
- At step 10, if the client has an IOLTA trust balance, Billing Admin can select **Apply Trust Funds**
- System shows available trust balance; Billing Admin enters the amount to apply (up to the lesser of invoice total or trust balance)
- System records a trust disbursement and marks the invoice as fully or partially paid
- Client receives a statement showing invoice amount, trust funds applied, and remaining balance due

**Exception Flows**

*EF-01: No approved entries for selected period*
- At step 2, if a selected matter has no approved entries, [S] system excludes it from the pre-bill list with a note: "No billable activity in selected period"

*EF-02: LEDES file validation failure*
- At step 13, if the LEDES 1998B file fails format validation (e.g., missing required field, invalid code), [S] system blocks the generation and displays the specific validation error
- Billing Admin must correct the underlying data (e.g., missing UTBMS code on a time entry) and retry

*EF-03: Email delivery failure*
- At step 15, if invoice email fails to deliver (bounced), [S] system updates invoice status to "Send Failed" and notifies the Billing Admin
- Billing Admin can correct the email address and resend

*EF-04: Invoice disputed by client*
- After invoice is sent, client contacts the firm to dispute line items
- Billing Admin can mark the invoice as "Disputed," add dispute notes, and create an adjusted invoice
- Original and adjusted invoices are both retained on the matter record

**Postconditions**
- Invoice record exists with status "Sent"
- Matter financial summary is updated (invoiced to date, outstanding balance)
- PDF and LEDES files are stored on the matter
- Client has received invoice via email and portal notification
- Audit trail records the complete billing run

**Business Rules Referenced**

| Rule ID | Description |
|---------|-------------|
| BR-501 | Invoices may only include time entries that have been approved in the pre-bill workflow |
| BR-502 | A LEDES 1998B file must be generated for any client with "LEDES Required" set in their billing profile |
| BR-503 | Invoices exceeding the firm-configured approval threshold must be approved by the billing partner before sending |
| BR-504 | Invoice numbers are sequential and may not be reused or manually overridden |
| BR-505 | Applying trust funds to an invoice requires that the trust balance be sufficient; partial application is permitted |
| BR-506 | A credit memo must reference the original invoice number it is correcting |

---

## UC-06 — Court Deadline Alert

**Use Case ID:** UC-06
**Name:** Court Deadline Alert
**Version:** 1.2
**Status:** Approved
**Last Updated:** 2025-01

**Actors**

| Role | Type | Description |
|------|------|-------------|
| System | Primary | Monitors the deadline registry and dispatches alerts |
| Attorney | Recipient | Receives alerts and acts on upcoming deadlines |
| Paralegal | Recipient | Receives alerts and coordinates with attorneys |
| Partner | Recipient | Receives escalation alerts for overdue or high-risk deadlines |

**Preconditions**
- The matter has Active status
- At least one deadline is recorded on the matter with a specific due date
- Notification preferences are configured for the attorney and/or paralegal
- The system's scheduled notification job is running

**Trigger**
A scheduled background job runs nightly (configurable) and evaluates all active deadlines against the current date to determine which alerts are due.

**Main Flow**

1. [S] System's scheduled job runs at the configured time (default: 07:00 local time)
2. [S] System queries the Deadline Registry for all active deadlines across all Active matters where:
   - The deadline is not yet marked complete or waived
   - An alert at today's lookahead horizon is configured (e.g., 30 days, 14 days, 7 days, 3 days, 1 day)
3. [S] For each qualifying deadline, system retrieves:
   - Matter number, matter name, responsible attorney, assigned paralegal
   - Deadline type (e.g., Response to Complaint, Motion Filing Deadline, Deposition, Statute of Limitations)
   - Due date, jurisdiction, court
   - Alert recipients (from matter team and matter-level notification settings)
4. [S] System composes an alert message for each deadline, including:
   - Matter name and number
   - Deadline type and due date
   - Days remaining
   - Jurisdiction and court name
   - A direct link to the matter's Deadlines tab
5. [S] System dispatches alerts via configured channels:
   - In-app notification (bell icon; persists until acknowledged)
   - Email (using firm's branded email template)
   - SMS (if opted in by the recipient and a phone number is on file)
6. [S] System logs each alert dispatch: deadline ID, recipient, channel, timestamp, delivery status (delivered / failed)
7. [S] System updates the deadline record: last alert sent timestamp and next scheduled alert date

**Alternate Flows**

*AF-01: Manual deadline alert trigger*
- Attorney or Paralegal can click **Send Reminder** on any deadline record at any time
- [S] System dispatches a one-off alert to all configured recipients immediately
- Manual alerts are logged separately from automated alerts

*AF-02: Deadline marked complete*
- When a deadline is marked complete, [S] system cancels all future scheduled alerts for that deadline
- A completion notice is sent to the responsible attorney and billing partner

*AF-03: Statute of Limitations deadline (critical)*
- Deadlines classified as "Statute of Limitations" are treated as high-priority
- Alert schedule is extended: 120 days, 90 days, 60 days, 30 days, 14 days, 7 days, 3 days, 1 day
- At 30 days remaining, the Partner is added as an alert recipient automatically
- At 7 days remaining, the Managing Partner receives a critical-priority alert

*AF-04: Calendar sync*
- When a deadline is created or updated, [S] system pushes the change to the attorney's connected calendar (Google Calendar or Microsoft Outlook) via the calendar integration
- Calendar event is created/updated within 60 seconds
- If the calendar sync fails (e.g., OAuth token expired), system flags a sync error on the attorney's profile and sends an in-app notification

**Exception Flows**

*EF-01: Email delivery failure*
- If an email alert fails to deliver (bounced or rejected), [S] system retries up to 3 times at 15-minute intervals
- After 3 failures, system marks the delivery as "Failed," logs the error, and sends an in-app notification to the affected user and the firm's IT administrator

*EF-02: SMS delivery failure*
- If SMS delivery fails (invalid number or carrier error), [S] system marks the SMS as "Failed" and falls back to in-app notification only
- System disables SMS for the affected recipient after 3 consecutive failures and notifies the user to update their phone number

*EF-03: Overdue deadline detected*
- If a deadline's due date has passed and it is not marked complete, [S] system generates an overdue alert
- Overdue alerts are sent to the responsible attorney, the billing partner, and the Managing Partner
- Overdue deadlines are highlighted in red on the matter dashboard and the firm-wide docket calendar
- A risk log entry is created on the matter for malpractice risk tracking

*EF-04: Notification job failure*
- If the scheduled notification job fails to run, [S] system detects the missed run on the next job cycle and processes any alerts that should have been sent
- IT administrator receives a job failure alert via monitoring system
- Catchup alerts are sent with a note: "Note: This reminder was delayed due to a system processing issue."

**Postconditions**
- Each qualifying deadline has dispatched the appropriate alert to all configured recipients
- Alert dispatch records are stored in the audit log
- Overdue deadlines are escalated to partner-level recipients
- Calendar events reflect the latest deadline data

**Business Rules Referenced**

| Rule ID | Description |
|---------|-------------|
| BR-601 | Default alert schedule for all deadlines: 30, 14, 7, 3, and 1 day before due date |
| BR-602 | Statute of Limitations deadlines trigger an extended alert schedule and Partner escalation at 30 days |
| BR-603 | Overdue deadlines must be escalated to the Managing Partner within 24 hours of the missed due date |
| BR-604 | Deadline records cannot be deleted; they can only be marked Complete, Waived (with justification), or Superseded |
| BR-605 | Court deadlines in jurisdictions with local court rules must use the court-specific rule set for derivative deadline calculation |
| BR-606 | Alert recipients must include at minimum the matter's responsible attorney; additional recipients are configurable |
