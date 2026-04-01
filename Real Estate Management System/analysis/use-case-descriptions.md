# Use-Case Descriptions — Real Estate Management System

---

## UC-01: Process Tenant Application

**ID:** UC-01
**Name:** Process Tenant Application
**Primary Actor:** Property Manager
**Secondary Actors:** Tenant, Background Check Service (Checkr/TransUnion), Credit Check Service (Equifax/Experian), Payment Gateway (Stripe)
**Preconditions:**
- A property unit exists with `status = available`
- An active listing is published for that unit
- The tenant has created an account in the tenant portal
- Application fee amount is configured for the property

**Main Flow:**
1. Tenant navigates to the active listing and clicks "Apply Now."
2. System presents the application form: personal information, employment details, income verification, rental history, emergency contacts, and consent to screening.
3. Tenant completes all required fields and uploads supporting documents (ID, pay stubs, bank statements).
4. System validates the form for completeness and format correctness (e.g., valid SSN format, email, phone).
5. System charges the application fee via the configured Payment Gateway; a `RentPayment` record of type `application_fee` is created.
6. On successful payment, system creates a `TenantApplication` record with `status = submitted` and timestamps the submission.
7. System enqueues an asynchronous background check job, passing applicant PII to the Background Check Service API.
8. System simultaneously enqueues an asynchronous credit check job, passing applicant SSN and consent token to the Credit Check Service API.
9. Both services return results within the SLA window (typically 2–10 minutes). System stores results in `BackgroundCheck` and `CreditCheck` tables linked to the application.
10. System evaluates results against the property's underwriting criteria (minimum credit score, no prior evictions, income ≥ 3× monthly rent).
11. If all criteria pass automatically, `TenantApplication.status` is updated to `approved` and the Property Manager is notified.
12. Property Manager reviews the application summary and confirms approval or overrides the automated decision.
13. System sends the tenant an approval notification and initiates the lease creation workflow (see UC-04).

**Alternative Flows:**
- **AF-01 — Payment Failure:** If the application fee payment fails (Step 5), the application is saved as a draft with `status = payment_failed`. The tenant is redirected to retry payment. No screening is triggered until payment succeeds.
- **AF-02 — Screening Service Timeout:** If either screening API does not respond within 15 minutes (Step 7–9), the application is flagged as `status = pending_manual_review` and assigned to the Property Manager's queue with an alert.
- **AF-03 — Automatic Rejection:** If background check returns a disqualifying finding (prior eviction within 5 years) or credit score falls below the threshold and no override policy applies, `status = rejected` and the tenant receives an adverse action notice per FCRA requirements.
- **AF-04 — Incomplete Application:** If the tenant saves a partial form and exits (Step 3), the application remains as a draft (`status = draft`) for up to 7 days, after which the draft is archived.

**Postconditions:**
- `TenantApplication` record exists with a final `status` (approved, rejected, or pending_manual_review).
- `BackgroundCheck` and `CreditCheck` records are linked with full result payloads stored (encrypted at rest).
- Application fee payment is recorded and the amount is non-refundable per policy.
- If approved, the lease creation workflow is triggered automatically.

---

## UC-02: Create and Execute Lease

**ID:** UC-02
**Name:** Create and Execute Lease
**Primary Actor:** Property Manager
**Secondary Actors:** Tenant, DocuSign
**Preconditions:**
- `TenantApplication.status = approved`
- Lease template exists for the property type and jurisdiction
- DocuSign integration credentials are valid

**Main Flow:**
1. Property Manager initiates lease creation from the approved application screen.
2. System pre-fills the lease template with unit address, tenant details, lease start/end dates, monthly rent, security deposit amount, and included utilities.
3. Property Manager reviews and edits lease terms, adds custom `LeaseClause` records (pet addendum, parking addendum, etc.).
4. Property Manager confirms lease terms and clicks "Send for Signature."
5. System generates a PDF from the lease template, uploads it to DocuSign via the API, and creates an envelope with signing fields for both the tenant and Property Manager.
6. DocuSign sends the tenant an email with a signing link.
7. Tenant reviews the lease in DocuSign and signs electronically.
8. DocuSign webhook fires `envelope.completed` when all signatories have signed.
9. System receives the webhook, downloads the signed PDF, stores it as a `Document` record linked to the `Lease`, and sets `Lease.status = active`.
10. System creates the first `RentSchedule` entry and generates the first `RentInvoice` due on the move-in date.
11. System collects the security deposit via Payment Gateway and creates a `SecurityDeposit` record with `status = held`.
12. Unit status is updated from `available` to `occupied`.
13. Property Manager and tenant both receive confirmation emails with links to download the executed lease.

**Alternative Flows:**
- **AF-01 — Tenant Declines to Sign:** If the tenant declines to sign in DocuSign, a `declined` event fires. The Property Manager is notified. The lease reverts to `draft` status and the PM can re-negotiate terms or cancel.
- **AF-02 — Signing Deadline Exceeded:** If the tenant does not sign within 48 hours, the system sends an automated reminder. After 72 hours with no action, the envelope expires, the lease is voided, and the PM is alerted to re-issue.

**Postconditions:**
- `Lease.status = active` with signed PDF attached.
- `SecurityDeposit` record created with collected amount.
- First `RentInvoice` generated with correct due date.
- `PropertyUnit.status = occupied`.

---

## UC-03: Collect Rent Payment

**ID:** UC-03
**Name:** Collect Rent Payment Online
**Primary Actor:** Tenant
**Secondary Actors:** Payment Gateway (Stripe), Property Manager
**Preconditions:**
- Active `Lease` with `status = active`
- `RentInvoice` exists with `status = due` or `overdue`
- Tenant has a payment method saved or enters one at checkout

**Main Flow:**
1. Tenant logs into the tenant portal and navigates to "Payments."
2. System displays outstanding `RentInvoice` records with amounts, due dates, and any accrued late fees.
3. Tenant selects an invoice to pay and chooses a payment method (saved bank account, new ACH, or credit/debit card).
4. Tenant confirms the payment amount and submits.
5. System creates a pending `RentPayment` record and calls the Stripe API with the payment method token and amount.
6. Stripe processes the transaction and returns a payment intent status.
7. On success, `RentPayment.status = completed`, `RentInvoice.status = paid`, and `RentInvoice.paid_at` is set.
8. If a `LateFee` was applied, it is either settled within the same payment (if included) or left outstanding for the next invoice cycle.
9. System sends a payment receipt to the tenant via email.
10. Property Manager's dashboard updates with the received payment.

**Alternative Flows:**
- **AF-01 — ACH Return:** If the ACH transfer is returned (NSF or invalid account), Stripe fires a `charge.failed` webhook. `RentPayment.status = failed`, `RentInvoice.status` reverts to `overdue`, and the tenant is notified with instructions to retry with a different method.
- **AF-02 — Partial Payment:** If the tenant enters a partial amount below the full invoice value, the system allows the partial payment but marks the invoice as `partially_paid`. The outstanding balance carries to the next billing cycle.

**Postconditions:**
- `RentPayment` record persists with transaction ID, amount, and timestamp.
- `RentInvoice.status = paid` (or `partially_paid`).
- Receipt emailed to tenant; payment event logged for owner statement generation.

---

## UC-04: Submit Maintenance Request

**ID:** UC-04
**Name:** Submit Maintenance Request
**Primary Actor:** Tenant
**Secondary Actors:** Property Manager, Contractor
**Preconditions:**
- Tenant has an active lease
- Maintenance request portal is accessible

**Main Flow:**
1. Tenant navigates to "Maintenance" in the tenant portal and clicks "New Request."
2. Tenant selects the issue category (plumbing, electrical, HVAC, appliance, structural, other) and sub-category.
3. Tenant enters a description of the issue, priority preference (routine, urgent, emergency), and uploads up to 5 photos.
4. Tenant submits the request.
5. System creates a `MaintenanceRequest` record with `status = submitted`, linked to the tenant's active lease and unit.
6. If priority is `emergency`, system immediately sends an SMS and email alert to the Property Manager and the on-call contractor.
7. Property Manager receives an in-app notification and reviews the request.
8. Property Manager assesses the request, selects an available `Contractor`, and creates a `MaintenanceAssignment`.
9. Contractor receives a work order notification with unit address, issue description, and tenant contact information.
10. Contractor accepts the work order; `MaintenanceAssignment.status = accepted`.
11. Contractor performs the work, updates status to `in_progress`, and uploads before/after photos.
12. Contractor marks the job as `completed` with a completion note and materials/labor cost.
13. Property Manager reviews the completion and closes the request: `MaintenanceRequest.status = closed`.
14. Tenant receives a closure notification and is invited to rate the repair experience.

**Alternative Flows:**
- **AF-01 — Contractor Declines:** If the assigned contractor declines (unavailable), the Property Manager is notified and reassigns to another contractor. The request remains in `status = pending_assignment`.
- **AF-02 — Tenant Cancels Request:** Tenant may cancel a request while it is still `submitted` or `pending_assignment`. Once a contractor is assigned, cancellation requires PM approval.

**Postconditions:**
- `MaintenanceRequest.status = closed` with completion timestamp.
- All photos and cost records are stored for owner statement reporting.
- Tenant satisfaction score (if provided) is recorded.

---

## UC-05: Conduct Property Inspection

**ID:** UC-05
**Name:** Conduct Property Inspection
**Primary Actor:** Property Manager
**Secondary Actors:** Tenant, Contractor (optional)
**Preconditions:**
- Property unit exists
- Inspection checklist template is configured for the inspection type
- Scheduled inspection date is set

**Main Flow:**
1. Property Manager schedules an inspection (move-in, move-out, periodic, or post-maintenance) and assigns it to a unit.
2. System creates an `Inspection` record with `status = scheduled` and notifies the tenant with the date and access requirements.
3. On the inspection date, Property Manager opens the inspection form on a mobile device.
4. System loads the `InspectionItem` checklist with all line items for the unit type (walls, floors, fixtures, appliances, HVAC, windows, doors, exterior, etc.).
5. For each checklist item, the inspector records condition (good, fair, poor, damaged) and adds notes.
6. Inspector uploads photos for items flagged as fair, poor, or damaged.
7. Inspector submits the completed checklist.
8. System sets `Inspection.status = completed` with timestamp.
9. For move-out inspections, system compares current condition against the move-in baseline and generates a damage assessment report.
10. Damage assessment feeds directly into the `SecurityDeposit` refund calculation workflow.
11. PM and tenant both receive the signed inspection report via email.

**Alternative Flows:**
- **AF-01 — Tenant Not Present:** If the tenant is not present for a move-out inspection, the PM notes this on the report and proceeds. The report is still legally valid and the tenant is emailed a copy.

**Postconditions:**
- `Inspection.status = completed` with all items scored and photos attached.
- For move-out inspections, a damage report is generated and linked to the `SecurityDeposit` record.

---

## UC-06: Process Security Deposit Refund

**ID:** UC-06
**Name:** Process Security Deposit Refund
**Primary Actor:** Property Manager
**Secondary Actors:** Tenant, Payment Gateway
**Preconditions:**
- Lease is terminated (`Lease.status = terminated`)
- Move-out inspection is completed
- Security deposit is held (`SecurityDeposit.status = held`)

**Main Flow:**
1. Property Manager opens the deposit refund workflow from the terminated lease screen.
2. System displays the held deposit amount and the move-out inspection damage report.
3. Property Manager enters deduction line items (unpaid rent, cleaning fees, damage repair costs) with descriptions and amounts.
4. System calculates the refund amount: `refund = deposit_amount - total_deductions`.
5. If deductions exceed the deposit, PM flags the overage for collections.
6. PM reviews the itemized deduction statement and confirms.
7. System initiates a Stripe payout to the tenant's bank account on file.
8. On successful payout, `DepositRefund.status = paid` and `SecurityDeposit.status = refunded`.
9. System generates and emails the tenant the itemized deposit disposition statement within the state-mandated window (typically 21 days).

**Alternative Flows:**
- **AF-01 — Full Refund (No Deductions):** If no deductions apply, PM clicks "Full Refund" and the full deposit amount is returned automatically.
- **AF-02 — Dispute:** Tenant may dispute deductions within 7 days of receiving the statement. Dispute is recorded and assigned to the PM for resolution.

**Postconditions:**
- `DepositRefund` record created with amount, payout date, and itemized deductions.
- `SecurityDeposit.status = refunded` or `forfeited` depending on outcome.
- Disposition statement stored as a `Document` record.

---

## UC-07: Generate Owner Financial Statement

**ID:** UC-07
**Name:** Generate Owner Financial Statement
**Primary Actor:** Property Manager
**Secondary Actors:** Owner
**Preconditions:**
- At least one property is associated with the owner
- Billing period has closed (end of month)

**Main Flow:**
1. Property Manager triggers monthly statement generation (or system auto-generates on the 1st of each month for the prior month).
2. System queries all `RentPayment`, `LateFee`, `MaintenanceRequest` costs, `UtilityRecord` charges, and owner distribution transactions for the owner's properties during the billing period.
3. System calculates gross income, total expenses, management fee (percentage of collected rent), and net owner distribution.
4. System generates the `OwnerStatement` record with a detailed line-item breakdown.
5. System generates a PDF of the statement and attaches it as a `Document`.
6. Statement is published to the Owner Portal and the owner is notified via email.
7. Owner logs in and reviews the statement; can download the PDF or export to CSV.
8. If an owner distribution payment is configured, the system initiates an ACH transfer to the owner's bank account.

**Postconditions:**
- `OwnerStatement` record persists for the billing period.
- PDF document stored and accessible in both PM and Owner portals.
- Owner distribution payment initiated if configured.

---

## UC-08: Manage Lease Renewal

**ID:** UC-08
**Name:** Manage Lease Renewal
**Primary Actor:** Property Manager
**Secondary Actors:** Tenant, DocuSign
**Preconditions:**
- Active `Lease` exists with end date within the renewal notice window (typically 60–90 days)
- Tenant has not submitted a notice to vacate

**Main Flow:**
1. System automatically generates a `LeaseRenewal` record 90 days before lease end and notifies the Property Manager.
2. Property Manager reviews market rent analysis and decides on the renewal rent amount (same, increase, or decrease).
3. PM configures renewal terms: new rent amount, new lease end date, any updated clauses.
4. PM sends the renewal offer to the tenant via the portal and email.
5. Tenant reviews the renewal offer in the tenant portal.
6. Tenant accepts the renewal terms; `LeaseRenewal.status = tenant_accepted`.
7. System generates a lease amendment PDF and sends it through DocuSign for signatures.
8. After all parties sign, the original `Lease.end_date` and `Lease.rent_amount` are updated, `LeaseRenewal.status = completed`.
9. `RentSchedule` is updated to reflect the new rent amount effective the renewal start date.
10. Tenant and PM receive confirmation emails with the updated lease document.

**Alternative Flows:**
- **AF-01 — Tenant Declines Renewal:** Tenant declines the renewal offer. `LeaseRenewal.status = tenant_declined`. System prompts the PM to begin the vacancy preparation workflow and sends the tenant move-out instructions.
- **AF-02 — Counter-Offer:** Tenant submits a counter-offer with a different rent amount. PM reviews and either accepts, counter-offers again, or withdraws the renewal offer.
- **AF-03 — No Response:** If tenant does not respond within 30 days of the renewal offer, the system sends two automated reminders. After 60 days of no response, PM is alerted to contact the tenant directly.

**Postconditions:**
- `LeaseRenewal.status = completed` with signed amendment attached.
- Original `Lease` record updated with new end date and rent amount.
- Updated `RentSchedule` in place for future invoice generation.
