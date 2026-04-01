# Use Case Descriptions — Library Management System

## Overview

This document provides detailed behavioural specifications for the thirteen use cases identified in `use-case-diagram.md`. Each description follows a structured template covering actors, preconditions, step-by-step flows, exception handling, postconditions, and traceability to business rules and domain events. These descriptions are the primary input for API contract design, acceptance-test criteria, and service-boundary decisions.

---

### UC-001: Search Catalog

**Actor:** Member (primary), Librarian (primary), Anonymous User (secondary)
**Goal:** Locate bibliographic items matching search criteria and determine real-time availability by branch, format, and copy status.
**Preconditions:**
- The catalog search index is online and reflects the current state of the bibliographic database.
- The user has access to the public OPAC or staff portal (anonymous access permitted for search only).

**Main Flow:**
1. User enters a search query: keyword, author, title, ISBN/ISSN, subject heading, or call number.
2. System normalises the query (lowercase, stop-word removal, stemming) and executes a full-text search against the bibliographic index.
3. System returns a ranked result set displaying: title, primary author, format (print, e-book, audiobook, periodical), publication year, and aggregate availability count per branch.
4. User applies optional facet filters: format, language, branch, audience level, publication year range, or availability (available now / all).
5. User selects a title from the result list.
6. System displays the title detail page: full bibliographic record, cover image, summary, holdings table (branch, call number, copy status per copy), and digital-access link where applicable.
7. User initiates a borrow, hold, or ILL request directly from the detail page.

**Alternative Flows:**
- **AF1 — No results:** System displays "No items found" with spelling-correction suggestions, a prompt to broaden search terms, and a link to submit an ILL request.
- **AF2 — Search timeout (> 5 s):** System returns any partial results with a warning banner; user may refine the query or try again.
- **AF3 — Anonymous user attempts a transactional action:** System intercepts and presents a login prompt or library card number entry before proceeding to the requested action.

**Postconditions:**
- The user has visibility of item availability and may proceed to borrow, reserve, or request an inter-library loan.
- Search query is logged anonymously for analytics (no member ID attached).

**Business Rules Referenced:** BR-01 (anonymous search permitted), BR-08 (availability count excludes lost, withdrawn, and in-repair copies)

---

### UC-002: Check Out Item (Physical)

**Actor:** Librarian (primary), Member via self-checkout kiosk (secondary)
**Goal:** Issue a physical copy to a member, create an active loan record, and update item status to Checked Out.
**Preconditions:**
- Member is authenticated; member account exists in the system.
- The copy being issued exists in the catalog with a status of Available or On Hold Shelf (for a hold assigned to this member).
- The branch is open and the circulation service is online.

**Main Flow:**
1. Librarian scans or manually enters the member card number at the circulation desk or self-checkout kiosk.
2. System loads the member record and validates account status: Active, not expired, not suspended.
3. System evaluates the outstanding fine balance. If balance ≥ fine-block threshold (default $25, configurable by policy), system presents the fine-payment step before proceeding.
4. Librarian scans the item barcode or RFID tag.
5. System validates:
   - Copy status is Available (or On Hold Shelf assigned to this member).
   - Copy is not reserved for a different member.
   - Member has not reached the loan limit for the item's material type and borrower category.
6. System creates a loan record: `member_id`, `copy_id`, `checkout_date` (UTC), `due_date` (calculated from material-type policy and branch calendar), `renewal_count = 0`, `loan_status = Active`.
7. System atomically updates copy status to Checked Out within the same database transaction.
8. System writes a `LoanCreated` outbox record; the outbox worker publishes the domain event asynchronously.
9. System prints or emails a checkout receipt showing the item title, due date, and current loan count.

**Alternative Flows:**
- **AF1 — Account blocked (expired, fines, suspended):** System displays the block reason code. Librarian may apply a supervisor-credential override for expired card or suspension (logged in audit trail with override reason). Fine-block cannot be overridden; payment is required.
- **AF2 — Copy reserved for a different member:** System prevents checkout, identifies the hold patron (to staff only), and offers to notify the hold patron that the item is at the desk.
- **AF3 — Loan limit reached:** System displays the member's active loan count and the configured limit for the material type. This limit cannot be overridden.
- **AF4 — Copy not in Available or assignable Hold status:** System displays current copy status (e.g., In Transit, On Repair) and offers to place a reservation.
- **AF5 — RFID scan failure:** Staff manually enters the barcode. System logs the manual-entry flag on the loan record for inventory reconciliation.

**Postconditions:**
- Loan record created with `loan_status = Active`.
- Copy status updated to Checked Out.
- `LoanCreated` event published.
- Checkout receipt delivered to member.

**Business Rules Referenced:** BR-02 (loan limits by material type and borrower category), BR-03 (fine-block threshold), BR-04 (due-date calculation by material type and branch calendar)

---

### UC-003: Return Item

**Actor:** Librarian (primary)
**Goal:** Close an active loan, assess any overdue fine, update copy status, and allocate the copy to the next reservation in the hold queue.
**Preconditions:**
- The copy has an active loan record (`loan_status = Active`) in the system.
- The branch is open and the circulation service is online.

**Main Flow:**
1. Librarian scans the item barcode or RFID tag at the circulation desk or automated sorter.
2. System locates the active loan associated with the copy.
3. System calculates overdue days: `max(0, return_date − due_date)`. If overdue_days > 0, system computes fine: `min(overdue_days × daily_rate[material_type], fine_cap[material_type])`.
4. System closes the loan: `loan_status = Returned`, `return_date = now (UTC)`.
5. If overdue fine > $0.00, system appends a fine record to the member's account and emits `FineAssessed`.
6. System queries the hold queue for the title (`bib_id` of the returned copy).
7. **If a hold exists at the same branch:** System sets copy status to On Hold Shelf, sets `hold_pickup_expiry = now + 7 days`, and sends a hold-ready notification to the patron via email/SMS. Emits `HoldAllocated`.
8. **If a hold exists at a different branch:** System sets copy status to In Transit and creates a branch-transfer task for the receiving branch. Emits `HoldAllocated` with transit flag.
9. **If no hold exists:** System sets copy status to Available. Item is ready to be reshelved.
10. System emits `LoanClosed` event.
11. System prints an optional return receipt confirming the item was received and any fines assessed.

**Alternative Flows:**
- **AF1 — Copy not found in system:** Staff creates a missing-copy report. No check-in is performed; the issue is escalated for investigation.
- **AF2 — Item visibly damaged on return:** Librarian flags the copy as Damaged before completing check-in. System creates a damage-assessment task. Loan is still closed; a damage surcharge may be applied separately after assessment.
- **AF3 — Wrong branch return:** System accepts the return regardless of the branch. Copy status is set per hold-queue rules; a transfer task is created if needed.

**Postconditions:**
- Loan closed with `loan_status = Returned`.
- Overdue fine assessed and added to member balance if applicable.
- Copy status updated to On Hold Shelf, In Transit, or Available.
- `LoanClosed` and `FineAssessed` (if applicable) events published.
- Hold patron notified if the copy was allocated to a hold.

**Business Rules Referenced:** BR-05 (fine rate by material type), BR-06 (fine cap per loan)

---

### UC-004: Renew Loan

**Actor:** Member (online, mobile, telephone), Librarian (staff desk on behalf of member)
**Goal:** Extend the due date of an active loan without requiring the physical return of the item.
**Preconditions:**
- Loan is in Active status.
- Renewal request is made on or before `due_date + renewal_grace_period` (default: 0 days — renewal must occur on or before the due date unless configured otherwise).
- Member account has no active borrowing block.

**Main Flow:**
1. Member or Librarian identifies the loan by member account view or loan ID.
2. System loads the loan record and evaluates renewal eligibility:
   - `renewal_count < max_renewals[material_type]`
   - No active holds exist for the title from any other member.
   - Member has no borrowing block.
3. System calculates the new due date: `due_date + loan_period[material_type]`, adjusted for branch closed days.
4. System increments `renewal_count` on the loan record and saves the new due date.
5. System emits `LoanRenewed` event.
6. Member receives the updated due date via the OPAC, mobile app notification, or printed receipt.

**Alternative Flows:**
- **AF1 — Renewal limit reached:** System rejects the request with an informational message stating the maximum renewal count for the material type.
- **AF2 — Hold exists on the title:** System rejects renewal and advises the member to return the item by the current due date.
- **AF3 — Member has a borrowing block:** System intercepts and presents the fine-payment flow before permitting renewal.
- **AF4 — Loan already overdue:** Renewal is permitted only if within the configured overdue-renewal window (default: 3 days past due). New due date is calculated from today, not from the original due date.

**Postconditions:**
- Loan due date extended; `renewal_count` incremented.
- `LoanRenewed` event published.

**Business Rules Referenced:** BR-07 (maximum renewal count per material type), BR-08 (hold-blocked renewal)

---

### UC-005: Place Reservation / Hold

**Actor:** Member (OPAC / mobile), Librarian (staff desk)
**Goal:** Queue a member for the next available copy of a title at a selected pickup branch.
**Preconditions:**
- Member is authenticated with an Active account.
- The bibliographic title exists in the catalog.
- Member has not exceeded the active-hold limit for their borrower category.

**Main Flow:**
1. Member searches for and selects a title from the catalog.
2. Member selects "Place Hold" from the title detail page.
3. System validates:
   - Member account is Active and not expired.
   - Member's active hold count < hold limit for their borrower category.
   - Member does not already have a hold on this title.
   - No copy is immediately available for checkout at the member's preferred branch (if available, system prompts for direct checkout).
4. Member selects a pickup branch from the list of active branches.
5. System assigns a queue position using FIFO ordering within the borrower-category priority tier.
6. System creates a hold record: `member_id`, `bib_id`, `pickup_branch_id`, `queue_position`, `hold_status = Waiting`, `placed_date = now`, `expiry = null`.
7. System emits `HoldPlaced` event.
8. System confirms the placement and displays the member's queue position and an estimated wait-time range based on copies in circulation and queue depth.

**Alternative Flows:**
- **AF1 — Copy available for immediate checkout at selected branch:** System prompts member to borrow directly; if member confirms, redirects to self-checkout or advises to visit the desk.
- **AF2 — Hold limit reached:** System displays current hold count and the configured maximum; does not permit placement.
- **AF3 — Duplicate hold detected:** System informs the member that a hold on this title already exists on their account.
- **AF4 — Digital title selected:** System redirects to the OverDrive/Libby hold workflow (UC-007 alternative flow).

**Postconditions:**
- Hold record created with `hold_status = Waiting`.
- Queue position assigned and displayed to member.
- `HoldPlaced` event published.

**Business Rules Referenced:** BR-09 (active hold limit per borrower category), BR-10 (FIFO queue ordering; priority adjustments require System Admin intervention)

---

### UC-006: Pay Fine

**Actor:** Member (self-service online), Librarian (staff desk — cash or card)
**Goal:** Settle outstanding fines and restore full borrowing privileges when the balance falls below the block threshold.
**Preconditions:**
- Member account has one or more outstanding fines with a status of Unpaid.
- A payment channel is available (Stripe for card; cash handling at the desk).

**Main Flow:**
1. Member or Librarian navigates to the member's fine summary screen.
2. System displays a fine breakdown: loan ID, item title, fine type (overdue / damage / lost), overdue days, daily rate applied, fine amount, and current status.
3. Member selects fines to pay (full outstanding balance or individual line items).
4. System presents payment options: credit/debit card via Stripe (all channels) or cash (staff desk only).
5. Member or Librarian submits the payment.
6. **Card payment:** System creates a Stripe PaymentIntent server-side. Member completes card entry via Stripe Elements (client-side tokenisation). On `payment_intent.succeeded` webhook, system records `FinePaymentReceived` with the Stripe charge ID.
7. **Cash payment:** Librarian records the cash amount received; system marks fine(s) as Paid (Cash) with staff ID.
8. System updates fine record(s) to Paid status and recalculates the member's total outstanding balance.
9. If `new_balance < borrowing_block_threshold`, system removes the borrowing block from the member account and emits `BorrowingBlockCleared`.
10. System emails a payment receipt to the member's registered email address.

**Alternative Flows:**
- **AF1 — Stripe payment declined:** System surfaces the Stripe decline code with a user-friendly message; fine records remain Unpaid; no retry is triggered automatically.
- **AF2 — Partial payment:** Payment is applied to the oldest unpaid fines first (configurable). Remaining balance persists; borrowing block is cleared only if the remaining balance falls below the threshold.
- **AF3 — Librarian waives fine:** Librarian selects "Waive Fine", chooses a reason code (hardship, library error, promotion), and confirms with supervisor credentials. System marks the fine as Waived and records staff ID, reason code, and timestamp in the audit log. Emits `FineWaived`.
- **AF4 — Member disputes fine amount:** Member or Librarian flags the fine for review; fine is placed in Disputed status (does not accrue further; borrowing block remains).

**Postconditions:**
- Selected fine(s) marked as Paid or Waived.
- Member balance updated.
- Borrowing block cleared if `balance < threshold`.
- Payment receipt emailed.
- `FinePaymentReceived` or `FineWaived` event published.

**Business Rules Referenced:** BR-11 (borrowing block threshold = $25 by default, configurable), BR-12 (fine waiver requires supervisor role + reason code + audit entry)

---

### UC-007: Borrow Digital Item (DRM)

**Actor:** Member (primary), Digital Content Provider — OverDrive / Libby (secondary)
**Goal:** Check out a DRM-protected e-book or audiobook and deliver a time-limited download link to the member.
**Preconditions:**
- Member is authenticated with an Active account linked to the library's OverDrive account.
- The digital title is available (at least one concurrent licence slot is free).
- Member's active digital-loan count is below the digital-loan limit for their borrower category.

**Main Flow:**
1. Member searches for a digital title in the LMS OPAC or navigates to the digital shelf.
2. Member selects a title and chooses "Borrow" specifying the desired format (EPUB e-book or MP3 audiobook).
3. LMS validates: active membership; digital-loan count < limit; no current digital loan of the same title.
4. LMS sends a checkout API request to OverDrive: `{library_id, patron_card_number, title_id, format}`.
5. OverDrive responds with a download URL, licence expiry date (default: 14 days for e-books, 21 days for audiobooks per policy), and a DRM-protected file link.
6. LMS records the digital loan: `member_id`, `overdrive_title_id`, `checkout_date`, `expiry_date`, `format`, `loan_status = Active`.
7. LMS emits `DigitalLoanCreated` event.
8. LMS presents the member with a "Read / Listen" button linking to the OverDrive/Libby app and an optional direct EPUB/MP3 download link.

**Alternative Flows:**
- **AF1 — All licence slots in use:** LMS displays the member's estimated wait and offers to place a digital hold at OverDrive.
- **AF2 — OverDrive API error or timeout:** LMS queues the checkout request for retry (up to 3 attempts, 5-minute intervals). If all retries fail, the member is notified of a temporary service disruption; no loan record is created.
- **AF3 — Member digital-loan limit reached:** System displays the current digital count and the configured limit; directs the member to return a digital item before borrowing another.
- **AF4 — Early return:** Member selects "Return Early" in the LMS or the OverDrive app. LMS sends a return API call to OverDrive; the licence slot is freed immediately. LMS sets `loan_status = Returned` and emits `DigitalLoanReturned`.

**Postconditions:**
- Digital loan recorded in the LMS with `loan_status = Active`.
- Licence slot consumed at OverDrive; concurrent availability count decremented.
- `DigitalLoanCreated` event published.

**Business Rules Referenced:** BR-13 (concurrent digital-loan limit per borrower category), BR-14 (digital loan period by format type)

---

### UC-008: Process Acquisition Request

**Actor:** Acquisitions Manager (primary), External Vendor (secondary)
**Goal:** Procure new library materials via a purchase order, receive the shipment, and route items to the cataloging workflow.
**Preconditions:**
- Acquisitions Manager is authenticated with the Acquisitions role.
- At least one active budget fund exists with sufficient balance for the requested material type.
- The vendor is registered in the vendor directory.

**Main Flow:**
1. Acquisitions Manager creates a purchase request: ISBN/ISSN, title, quantity, vendor, fund code, and purchase justification.
2. System validates budget availability: `fund.available_balance ≥ order_total`. Encumbers the order total against the fund.
3. If `order_total > approval_threshold` (default $500, configurable): system routes to Director for approval; status = Pending Approval.
4. Once approved (or if below threshold): Acquisitions Manager finalises the Purchase Order.
5. System generates the PO document and transmits it to the vendor via EDI or email; emits `PurchaseOrderCreated`.
6. Vendor ships the materials and provides an invoice.
7. Staff at the receiving desk scans or enters barcodes of all received items.
8. System matches received items to open PO lines; records quantities received and any discrepancies.
9. System creates stub item records (copy records without full cataloging) and emits `ItemReceived`.
10. Cataloging staff enrich the stub records (UC-013). On completion, `ItemCataloged` is emitted and items become discoverable in the OPAC.

**Alternative Flows:**
- **AF1 — Insufficient budget:** System blocks PO creation and displays the available fund balance. Acquisitions Manager may select an alternative fund or reduce the order quantity.
- **AF2 — Director approval denied:** System notifies Acquisitions Manager with the denial reason and a request reference number. The request is archived with status Rejected.
- **AF3 — Partial shipment received:** System records partial quantities; remaining PO lines remain open. A follow-up reminder is scheduled 30 days after the expected delivery date.
- **AF4 — Item damaged on receipt:** Staff marks individual items as Damaged at receipt. System creates a vendor-credit request and routes the item for return shipping rather than cataloging.

**Postconditions:**
- PO created, transmitted, and status tracked through fulfilment.
- Fund balance reduced; encumbrance released or converted to expense on receipt.
- Items received and routed to cataloging.
- `PurchaseOrderCreated`, `ItemReceived`, and (eventually) `ItemCataloged` events published.

**Business Rules Referenced:** BR-16 (approval threshold for large-value orders), BR-17 (fund encumbrance and budget validation)

---

### UC-009: Generate Circulation Report

**Actor:** Librarian (primary), Acquisitions Manager (primary), System Admin (primary)
**Goal:** Produce a structured operational, financial, or collection-usage report for a specified date range and branch scope.
**Preconditions:**
- User is authenticated with a role that includes reporting permissions.
- The reporting read-replica is online and within acceptable replication lag (< 5 minutes).

**Main Flow:**
1. User selects a report type from the report catalogue (e.g., Circulation Summary, Overdue Items List, Fine Revenue, Most-Borrowed Titles, Collection Age Analysis, Acquisition Spend).
2. User configures parameters: date range, branch scope (single branch or all), material type filter, and borrower-category filter where applicable.
3. System validates parameters (date range ≤ 2 years; end date not in the future).
4. System submits a report generation job to the background report queue.
5. System executes the report query against the read-replica database.
6. Report record is created and marked Ready; system notifies the user in-app and by email with a download link.
7. User downloads the report in the selected format: PDF (print-formatted), CSV (raw data), or XLSX (pivot-ready).

**Alternative Flows:**
- **AF1 — Query execution exceeds 30 seconds:** System delivers the report asynchronously. User is notified by email when the report is available; no action required.
- **AF2 — No data for selected parameters:** System generates a report shell with a "No records found for the selected criteria" notice rather than an error.
- **AF3 — User role lacks access to a specific report type:** System returns a permission-denied message and directs the user to request access from a System Admin.

**Postconditions:**
- Report record created, available for download, and retained for 90 days.
- Report generation is logged for audit purposes (user ID, report type, parameters, generation timestamp).

**Business Rules Referenced:** BR-18 (report retention = 90 days; data access scope enforced by role)

---

### UC-010: Register New Member

**Actor:** Librarian (in-branch registration), Member (online self-registration)
**Goal:** Create a new member account, assign a borrower category, issue a library card number, and activate full borrowing privileges.
**Preconditions:**
- The registration channel is available.
- For in-branch: applicant has presented valid identity documents.
- For online: applicant has provided contact details that can be email-verified.

**Main Flow:**
1. Librarian or applicant fills in the registration form: given name, family name, date of birth, street address, email address, and phone number.
2. System validates: all required fields are present and correctly formatted; email address is unique in the system; date of birth is consistent with the requested borrower category.
3. **Online registration path:** System sends an email verification link. Account is created with `member_status = PendingVerification`; the link expires after 24 hours. Member must click the link to activate the account.
4. **In-branch path:** Librarian confirms the applicant's identity against the presented document; account is activated immediately.
5. Librarian (or system for online) selects the borrower category: Adult, Junior (under 16), Senior (65+), Staff, Institutional.
6. System generates a unique library card number (format: `LIB-YYYYMMDD-NNNNNN`).
7. System creates the member record with `member_status = Active` and `expiry_date = registration_date + expiry_period[borrower_category]`.
8. System emits `MemberCreated` event.
9. Member receives a welcome email summarising the card number, loan limits, and borrower-category privileges.

**Alternative Flows:**
- **AF1 — Duplicate email detected:** System alerts the Librarian or applicant. Librarian may search for and recover the existing account rather than creating a duplicate.
- **AF2 — Online verification email not received:** Member may request a resend after 5 minutes; the verification link is regenerated and the previous link invalidated. After 3 resend attempts, the registration is abandoned and must be restarted.
- **AF3 — Applicant under 16, in-branch:** Librarian records parental or guardian consent (consent reference number) before activating the Junior account.

**Postconditions:**
- Member account created with `member_status = Active`.
- Library card number issued.
- `MemberCreated` event published.
- Welcome email sent with borrowing privileges summary.

**Business Rules Referenced:** BR-19 (borrower category eligibility by age), BR-20 (card expiry periods: Adult 2 years, Junior 1 year, Senior 3 years, Staff 1 year renewable)

---

### UC-011: Recall Overdue Item

**Actor:** System automated job (primary), Librarian (secondary — manual recall)
**Goal:** Notify members of overdue or recalled items and, if unresolved, escalate to lost-item status with a replacement charge.
**Preconditions:**
- Loan `due_date < today − grace_period` and `loan_status = Active`; **or** a high-demand recall is triggered because the hold queue for the title has ≥ 3 patrons waiting.

**Main Flow:**
1. The overdue-notice background job runs daily at 08:00 local branch time. It selects all loans where `due_date < today − grace_period (1 day)` and `loan_status = Active`.
2. System sends a **First Notice** to the member's preferred channel (email and/or SMS) stating: item title, original due date, days overdue, current fine balance, and return instructions.
3. If the loan remains open 14 days past due: System sends a **Second Notice** with an escalated tone, updated fine balance, and a warning that the item will be marked lost after 30 days.
4. If the loan remains open 30 days past due: System sends a **Final Notice**, sets `loan_status = Lost-Assumed`, applies a replacement cost charge to the member's account (`replacement_cost[material_type]`), and updates copy status to Lost. Emits `ItemDeclaredLost`.
5. **Manual recall:** Librarian may trigger an immediate recall notice for any active loan when the hold queue for the title reaches the recall threshold. The recall notice specifies a shortened return-by date (current date + 7 days) and waives accumulated fines up to the recall trigger date.

**Alternative Flows:**
- **AF1 — Member returns the item before Lost status:** Standard return flow (UC-003) applies. The replacement charge is not applied; accumulated overdue fine is assessed normally.
- **AF2 — Member disputes Lost status:** Librarian investigates; if the item is found and returned, Lost status is reversed, the replacement charge is waived, and the loan is closed with standard overdue fine.
- **AF3 — Email/SMS delivery fails:** System logs the delivery failure and increments a failure counter. After two consecutive delivery failures, the Librarian is prompted to contact the member by telephone.

**Postconditions:**
- Member notified at each escalation point.
- Loan escalated to `Lost-Assumed` after 30 days; replacement charge applied; copy status set to Lost.
- `ItemDeclaredLost` event published at escalation.

**Business Rules Referenced:** BR-05 (fine rate by material type), BR-06 (fine cap per loan), BR-23 (lost-item replacement cost schedule by material type)

---

### UC-012: Process Inter-Library Loan

**Actor:** Member (requestor), Librarian ILL Coordinator (processor)
**Goal:** Obtain a library item not held in the local collection from a partner lending library and fulfil the member's loan request.
**Preconditions:**
- Member is authenticated with an Active account in good standing (no borrowing block, ILL-eligible borrower category).
- The requested title has been confirmed as absent from the local catalog (no copies with Available, On Order, or In Transit status).
- ILL network connectivity is available (OCLC WorldShare or equivalent).

**Main Flow:**
1. Member submits an ILL request form: title, author, ISBN, publication year, preferred format, and urgency level.
2. System verifies the item is not locally available and that no pending ILL request exists for this member and title.
3. System creates an ILL request record with `ill_status = Submitted` and emits `ILLRequestSubmitted`.
4. ILL Coordinator reviews the request, verifies the member's eligibility, and selects a lending institution from the network based on holdings, cost, and delivery speed.
5. ILL Coordinator transmits the request to the lending library via the ILL network protocol; `ill_status = Requested`.
6. Lending library accepts; `ill_status = In Progress`. Member is notified of estimated arrival date.
7. Lending library ships the item; `ill_status = In Transit`. Member receives a shipping confirmation.
8. Item arrives at the home library. ILL Coordinator checks the item in, assigns a temporary barcode, and creates a temporary copy record with `copy_type = ILL`.
9. System notifies the member that the ILL item is ready for pickup. Hold pickup expiry is set to 7 days.
10. Member collects the item. ILL Coordinator creates an ILL loan with the lending library's specified loan period. The loan is marked as non-renewable unless the lending library's policy permits.
11. On return, ILL Coordinator checks in the item, removes the temporary copy record, packages the item for return shipping, and updates `ill_status = Returned to Lender`.
12. Lending library confirms receipt; `ill_status = Closed`. System emits `ILLRequestClosed`.

**Alternative Flows:**
- **AF1 — No lending library available:** ILL Coordinator notifies the member with reason (no holdings, cost too high). Request archived with status Unfulfillable.
- **AF2 — Item arrives damaged:** ILL Coordinator documents the damage with photographs, notifies the lending library, and escalates for adjudication. Member is notified of the delay.
- **AF3 — Member does not collect within 7 days:** System cancels the member's hold and sets `ill_status = Uncollected`. ILL Coordinator begins return-to-lender process.
- **AF4 — Member requests renewal:** ILL Coordinator sends a renewal request to the lending library. `ill_status = Renewal Requested`. Renewal is contingent on the lender's confirmation.

**Postconditions:**
- ILL loan created; member has access to the requested item.
- Return shipping arranged when the member returns the item.
- `ILLRequestSubmitted`, `ILLItemReceived`, and `ILLRequestClosed` domain events published at key lifecycle transitions.

**Business Rules Referenced:** BR-15 (ILL eligibility: Active member, good standing, local-copy absence confirmed, ILL-eligible borrower category), BR-24 (ILL loan period follows lending library terms and is non-renewable unless lender permits)
