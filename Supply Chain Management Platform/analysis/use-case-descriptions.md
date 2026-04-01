# Use-Case Descriptions — Supply Chain Management Platform

---

## UC-01: Onboard New Supplier

| Field | Detail |
|---|---|
| **Use Case ID** | UC-01 |
| **Use Case Name** | Onboard New Supplier |
| **Actors** | Procurement Manager (initiator), Supplier (registrant), System (automated steps) |
| **Priority** | Must |
| **Preconditions** | 1. Procurement Manager has an active system account with the "Supplier Management" role. 2. The prospective supplier's email address is not already registered in the system. |
| **Postconditions** | 1. Supplier record is created with status "Qualified" and a qualification expiry date set. 2. Supplier can log into the portal. 3. Supplier can be selected on purchase requisitions and purchase orders. |
| **Trigger** | Procurement Manager decides to add a new supplier following a sourcing decision or business request. |

### Main Flow

1. Procurement Manager navigates to the Supplier Directory and clicks **Invite Supplier**.
2. Procurement Manager enters the prospective supplier's legal name, primary contact email, and intended category.
3. System validates the email is not already registered; generates a unique invitation token valid for 7 days.
4. System sends an invitation email to the supplier with a registration link.
5. Supplier clicks the link and is directed to the self-service registration form.
6. Supplier completes all mandatory fields: legal name, registered address, country, tax registration number, primary contact details, and bank account details.
7. Supplier uploads required compliance documents (trade licence, insurance certificate, ISO certification).
8. Supplier submits the registration form.
9. System validates all mandatory fields and file uploads; creates a Supplier record with status "Pending Review".
10. System sends a confirmation email to the supplier and an internal alert to the Procurement Manager's qualification queue.
11. Procurement Manager opens the qualification queue, reviews the submitted details and documents.
12. Procurement Manager (optionally) initiates a credit/risk check via the integrated scoring service.
13. Procurement Manager approves the qualification, sets the expiry date, and selects the supplier tier.
14. System transitions the supplier status to "Qualified", creates portal login credentials, and emails welcome instructions to the supplier.

### Alternative Flows

**A1 — Invitation Link Expired (Step 5):**
- Supplier clicks an expired link. System displays an "Invitation Expired" message with a button to request a new invitation.
- Procurement Manager is notified to re-send the invitation if still valid.

**A2 — Missing Mandatory Documents (Step 9):**
- System identifies missing required document types based on the supplier's category.
- Registration is saved as a draft; supplier receives an email listing the missing items.
- Supplier logs back in to upload the missing documents and re-submits.

**A3 — Procurement Manager Requests Additional Information (Step 12):**
- Procurement Manager clicks "Request Clarification" and adds a comment.
- System sends the comment to the supplier; supplier's status transitions to "Additional Info Required".
- Supplier uploads additional documents and re-submits; status returns to "Pending Review".

**A4 — Procurement Manager Rejects the Supplier (Step 13):**
- Procurement Manager selects "Reject" with a mandatory rejection reason code.
- System sets supplier status to "Rejected" and emails the rejection reason to the supplier.
- Supplier cannot re-register using the same email within 6 months.

**A5 — External Risk Score is High (Step 12):**
- Credit/risk service returns a high-risk flag.
- System displays a warning banner on the qualification form.
- Procurement Manager must explicitly acknowledge the risk flag before approving.
- Risk flag and acknowledgement are logged in the supplier audit trail.

### Business Rules Applied

- BR-03: Suppliers with expired qualifications cannot receive new POs.
- BR-16: Supplier bank account changes require dual-approval workflow.

---

## UC-02: Create Purchase Requisition

| Field | Detail |
|---|---|
| **Use Case ID** | UC-02 |
| **Use Case Name** | Create Purchase Requisition |
| **Actors** | Employee / Requester (initiator), System (budget check, routing) |
| **Priority** | Must |
| **Preconditions** | 1. Requester is an authenticated system user with a valid cost centre assignment. 2. Budget has been allocated to the requester's cost centre for the current period. |
| **Postconditions** | 1. A PR is created with a unique PR number. 2. The PR is routed to the correct approver(s) based on the configured approval matrix. 3. The cost centre shows a budget commitment equal to the PR total. |
| **Trigger** | An employee needs to procure goods or services not yet covered by an existing contract or blanket order. |

### Main Flow

1. Employee navigates to "Create Requisition" and selects whether to search the item catalogue or enter a free-text request.
2. **Catalogue path:** Employee searches for items, selects quantities, and the system pre-fills unit prices from the approved price list.
3. **Free-text path:** Employee enters: item description, unit of measure, estimated unit price, quantity, and preferred supplier (optional).
4. Employee specifies: cost centre, delivery address, required-by date, and purpose/justification.
5. Employee attaches supporting documents (quotes, specifications) if available.
6. Employee clicks "Submit for Approval".
7. System performs a real-time budget check: PR total vs. available budget in the cost centre.
8. System routes the PR to the L1 Approver based on the cost centre and amount rules.
9. System assigns a unique PR number and sets status to "Pending L1 Approval".
10. System sends an email and in-app notification to the L1 Approver.
11. Employee can view the PR status, current approver, and history in the "My Requisitions" list.

### Alternative Flows

**A1 — Budget Insufficient (Step 7):**
- System displays a budget warning showing available balance vs. PR total.
- Submission is blocked; employee must either reduce the quantity or obtain a budget override from their Finance Manager.
- Finance Manager can grant a temporary budget override with a reason code; the PR can then be submitted.

**A2 — Preferred Supplier is Suspended or Qualification Expired (Step 6):**
- System displays a warning identifying the supplier's status.
- Employee must select a different approved supplier or leave the preferred supplier blank.

**A3 — PR Saved as Draft (any step):**
- Employee can save an incomplete PR as "Draft" at any point.
- Draft PRs do not trigger budget commitment or notifications.
- Employee can return to complete and submit later.

---

## UC-03: Approve Purchase Requisition (Multi-Level)

| Field | Detail |
|---|---|
| **Use Case ID** | UC-03 |
| **Use Case Name** | Approve Purchase Requisition (Multi-Level) |
| **Actors** | Approver L1 (line manager), Approver L2 / CFO (for high-value), System (routing) |
| **Priority** | Must |
| **Preconditions** | 1. A PR exists in "Pending Approval" status assigned to the current approver. 2. The approver's account is active and not on an active delegation. |
| **Postconditions** | 1. PR is either "Approved" (ready for conversion to PO) or "Rejected" / "Returned for Revision". 2. Budget commitment is confirmed on approval; released on rejection. 3. Requester is notified of the outcome. |
| **Trigger** | Approver receives an email notification or sees a pending PR in their approval queue. |

### Main Flow

1. L1 Approver receives an email with a summary of the PR and a "Review Now" deep link.
2. Approver opens the PR detail view, which shows: requester, items, total cost, cost centre, budget balance, supporting documents, and history.
3. Approver reviews all details.
4. Approver clicks **Approve** and optionally enters a comment.
5. System checks whether the PR total exceeds the L2 threshold (default: $10,000).
6. **Below threshold:** System transitions PR to "Approved" and notifies the requester and Procurement Manager.
7. **Above threshold:** System transitions PR to "Pending L2 Approval" and routes to the L2 Approver (CFO or designated deputy).
8. L2 Approver receives notification, reviews the PR (same view as L1 with the added L1 approval record).
9. L2 Approver approves; System transitions PR to "Approved" and notifies all parties.

### Alternative Flows

**A1 — Approver Rejects (Step 4 or 8):**
- Approver selects "Reject" and must enter a mandatory rejection reason.
- System transitions PR to "Rejected", notifies the requester, and releases the budget commitment.
- Requester cannot re-submit the same PR; they must create a new PR addressing the rejection reason.

**A2 — Approver Returns for Revision (Step 4 or 8):**
- Approver selects "Return for Revision" with a comment explaining what must be changed.
- System transitions PR to "Revision Required" and notifies the requester.
- Requester edits the PR and re-submits; the workflow restarts from step 1.

**A3 — Approval Timeout — Escalation (Steps 4 / 8):**
- If no action is taken within 48 hours, the system sends a reminder notification.
- If no action after 72 hours, the system auto-escalates to the approver's designated deputy or manager.
- The escalation is logged in the PR timeline.

**A4 — Approver Delegates Authority:**
- Approver has a delegation rule active (covering the current date) to a named colleague.
- System routes new approval requests to the delegate.
- Delegate's approvals are annotated "on behalf of [original approver]" in the timeline.

---

## UC-04: Issue Purchase Order

| Field | Detail |
|---|---|
| **Use Case ID** | UC-04 |
| **Use Case Name** | Issue Purchase Order |
| **Actors** | Procurement Manager (initiator), Supplier (recipient), System |
| **Priority** | Must |
| **Preconditions** | 1. One or more PRs are in "Approved" status and have not yet been converted to a PO. 2. At least one qualified supplier is available for the items on the PR. |
| **Postconditions** | 1. A PO is created with a unique PO number. 2. PO PDF is delivered to the supplier via email and portal. 3. PO status is "Issued – Pending Acknowledgement". 4. Budget commitment is updated from PR-level to PO-level. |
| **Trigger** | Procurement Manager reviews the approved PR queue and acts on pending PO creation. |

### Main Flow

1. Procurement Manager opens the Approved PR Queue.
2. Procurement Manager selects one or more approved PRs (same supplier and cost centre) and clicks **Create PO**.
3. System pre-populates the PO with: supplier details, delivery address, line items, quantities, unit prices (from price list or quote), and required-by dates.
4. Procurement Manager selects the transaction currency and verifies the exchange rate.
5. Procurement Manager adds payment terms, special delivery instructions, and a contract reference if applicable.
6. Procurement Manager clicks **Issue PO**.
7. System validates: supplier is qualified, prices are within tolerance of the last approved quote, total does not exceed combined PR approvals.
8. System generates a unique PO number, creates the PO record, and generates a formatted PDF.
9. System sends the PDF to the supplier's designated contact via email and posts it to the supplier portal.
10. PO status is set to "Issued – Pending Acknowledgement".
11. System sends an in-app confirmation to the Procurement Manager with the PO number.

### Alternative Flows

**A1 — Supplier Not Qualified (Step 7):**
- System blocks PO issuance and displays the supplier's qualification issue.
- Procurement Manager must either resolve the qualification issue or select an alternative supplier.

**A2 — Change Order on Issued PO:**
- Procurement Manager opens an issued PO and clicks **Create Change Order**.
- System creates a new PO version, preserving the original; sends the revised PO to the supplier for re-acknowledgement.
- If the change increases the PO value above the original approval threshold, the change order triggers a re-approval workflow.

---

## UC-05: Record Goods Receipt

| Field | Detail |
|---|---|
| **Use Case ID** | UC-05 |
| **Use Case Name** | Record Goods Receipt |
| **Actors** | Warehouse Manager (recorder), Quality Inspector (if applicable), System |
| **Priority** | Must |
| **Preconditions** | 1. A PO exists in "Confirmed" or "Partially Received" status with open lines. 2. Warehouse Manager is authenticated with the "Goods Receipt" role. |
| **Postconditions** | 1. GRN is created with a unique GRN number. 2. PO received quantities are updated. 3. Inventory quantities are updated. 4. Invoice matching engine is notified that receipt data is available. 5. If quality inspection is required, inspection task is created. |
| **Trigger** | Goods arrive at the warehouse accompanied by a delivery note referencing a PO number. |

### Main Flow

1. Warehouse Manager navigates to "Record Goods Receipt" and looks up the PO by PO number or scans the barcode on the delivery note.
2. System displays the PO header and all open lines with expected quantities.
3. Warehouse Manager enters the actual received quantity for each delivered line.
4. For lot-tracked or serial-tracked items, Warehouse Manager scans or enters the lot/serial numbers.
5. Warehouse Manager records the carrier details, delivery note number, and delivery date.
6. For items with a quality inspection flag, Warehouse Manager records a preliminary pass/fail.
7. Warehouse Manager clicks **Confirm Receipt**.
8. System saves the GRN, assigns a GRN number, and updates PO received quantities.
9. System updates inventory in the linked ERP or warehouse module.
10. System checks whether any lines are now fully received; if so, sets those PO lines to "Fully Received".
11. System notifies the three-way matching engine that new GRN data is available for matching.
12. If quality inspection items exist, System creates inspection tasks and notifies the Quality Inspector.

### Alternative Flows

**A1 — Short Delivery (Step 3):**
- Received quantity is less than expected. System marks the variance as a short-ship discrepancy.
- Discrepancy is logged in the Discrepancy Queue.
- PO line remains open for the undelivered balance unless manually closed.

**A2 — Over-Delivery (Step 3):**
- Received quantity exceeds PO quantity. System blocks acceptance of over-received quantity by default.
- Warehouse Manager must seek procurement manager approval to accept the excess.
- If approved, the PO is amended via a change order.

**A3 — Quality Inspection Failure (Step 6 onwards):**
- Quality Inspector marks items as rejected with a defect code.
- Rejected quantities are placed in quarantine; inventory is not updated for rejected items.
- System triggers the Return-to-Vendor (RTV) workflow automatically.
- Supplier performance record is updated with the defect event.

---

## UC-06: Three-Way Invoice Matching

| Field | Detail |
|---|---|
| **Use Case ID** | UC-06 |
| **Use Case Name** | Three-Way Invoice Matching |
| **Actors** | Supplier (invoice submitter), AP Clerk (exception handler), System (matching engine) |
| **Priority** | Must |
| **Preconditions** | 1. A confirmed PO exists. 2. A GRN has been recorded for the PO. 3. Supplier has submitted an invoice referencing the PO number. |
| **Postconditions** | 1. Invoice is either auto-approved (within tolerance) or flagged as an exception requiring manual review. 2. Approved invoices have a scheduled payment date set. 3. Exception invoices are assigned to the AP queue for resolution. |
| **Trigger** | Supplier submits an invoice through the portal, EDI, or the OCR pipeline processes an email-received invoice. |

### Main Flow

1. System receives invoice data (from portal submission, EDI, or OCR).
2. System validates the invoice header: PO number exists, supplier matches the PO, invoice date is after PO issue date.
3. For each invoice line, System retrieves the corresponding PO line and all GRN lines referencing it.
4. System performs three comparisons per line:
   - **Price check:** Invoice unit price vs. PO unit price. Variance within ±3% → pass.
   - **Quantity check:** Invoice quantity ≤ GRN received quantity (uninvoiced) → pass.
   - **Total check:** Invoice line total within ±3% of (GRN qty × PO unit price) → pass.
5. If all lines pass all checks, System sets invoice status to "Matched – Approved".
6. System calculates payment due date using the supplier's payment terms and posts the scheduled payment.
7. Supplier is notified of invoice approval via portal and email.

### Alternative Flows

**A1 — Price Variance Outside Tolerance (Step 4):**
- Invoice line is flagged as "Price Exception".
- AP Clerk is notified; the invoice appears in the exception queue.
- AP Clerk reviews and either: (a) approves the variance (with reason), (b) raises a price dispute, or (c) asks the supplier to re-issue at the PO price.

**A2 — Quantity Exceeds GRN (Step 4):**
- Invoice quantity exceeds received quantity.
- System holds the invoice pending a matching GRN.
- Once the remaining goods are received and a GRN recorded, the system re-runs matching automatically.

**A3 — Duplicate Invoice Detected (Step 2):**
- System detects a duplicate by matching supplier ID + invoice number. Duplicate is automatically rejected.
- Supplier is notified of the rejection with reason "Duplicate Invoice".

**A4 — Debit Note from RTV Applied (Step 4):**
- If an open debit note exists for the supplier (from a prior RTV), System applies the debit note against the invoice total.
- The matched invoice shows both the gross invoice amount and the debit note offset.

---

## UC-07: Conduct Supplier Performance Review

| Field | Detail |
|---|---|
| **Use Case ID** | UC-07 |
| **Use Case Name** | Conduct Supplier Performance Review |
| **Actors** | Procurement Manager / Category Manager (reviewer), Supplier (recipient), System (score computation) |
| **Priority** | Must |
| **Preconditions** | 1. At least 3 months of transaction data exists for the supplier. 2. An SLA contract record is linked to the supplier (optional, for target comparison). |
| **Postconditions** | 1. A performance scorecard is generated and stored on the supplier record. 2. The supplier receives the scorecard via portal and email. 3. SLA breach events are logged if any KPI is below the contracted target. |
| **Trigger** | Monthly or quarterly schedule trigger, or Procurement Manager manually initiates a review. |

### Main Flow

1. System (or Procurement Manager) initiates the scorecard generation for the review period.
2. System aggregates data for the period:
   - OTD: counts PO lines received on-time / total PO lines received.
   - Quality Acceptance Rate: accepted quantities / total received quantities.
   - Invoice Accuracy Rate: invoices matched without exception / total invoices.
   - PO Acknowledgement Time: average hours from PO issuance to supplier acknowledgement.
   - Dispute Rate: number of disputed invoices / total invoices.
3. System calculates a weighted composite score (configurable weights, default: OTD 30%, Quality 30%, Invoice Accuracy 20%, Acknowledgement Time 10%, Dispute Rate 10%).
4. System maps the composite score to a tier (5 = Excellent, 4 = Good, 3 = Meets Expectations, 2 = Below Target, 1 = Poor).
5. Procurement Manager reviews the auto-calculated scores on the scorecard form.
6. Procurement Manager adds qualitative comments and selects a recommended action (no action, improvement plan, contract review, off-board consideration).
7. Procurement Manager clicks **Distribute Scorecard**.
8. System emails the scorecard PDF to the supplier's primary contact and stores it on the supplier record.
9. If any KPI is below the SLA target, System logs a breach event linked to the SLA contract.

### Alternative Flows

**A1 — Supplier Disputes Scorecard (after Step 8):**
- Supplier logs into the portal, views the scorecard, and selects "Dispute Score".
- Supplier enters a written explanation and attaches evidence.
- Procurement Manager is notified; they review and either accept the dispute (adjust score) or reject it with a response.
- All communications are stored on the scorecard thread.

**A2 — Corrective Action Plan Required:**
- Score is below 3 composite. Procurement Manager marks the scorecard as "Improvement Required".
- Supplier receives the scorecard with a request to submit a Corrective Action Plan within 15 business days.
- System creates a follow-up reminder for the Procurement Manager after 15 days.

---

## UC-08: Manage RFQ / RFP Sourcing Event

| Field | Detail |
|---|---|
| **Use Case ID** | UC-08 |
| **Use Case Name** | Manage RFQ/RFP Sourcing Event |
| **Actors** | Category Manager (event owner), Supplier (respondent), System |
| **Priority** | Must |
| **Preconditions** | 1. Category Manager has the "Sourcing" role. 2. At least 3 qualified suppliers exist in the relevant category. 3. Item master records exist for all line items to be sourced. |
| **Postconditions** | 1. Sourcing event is awarded to one or more suppliers. 2. Award decision and evaluation matrix are stored. 3. Unsuccessful suppliers receive a decline notification. 4. A PO or contract can be created directly from the award. |
| **Trigger** | Category Manager identifies a sourcing need: new category, contract expiry approaching, or spend review triggering competitive tender. |

### Main Flow

1. Category Manager navigates to "Sourcing Events" and clicks **Create RFQ/RFP**.
2. Category Manager selects event type (RFQ for price/delivery, RFP for technical proposals).
3. Category Manager enters: event name, description, evaluation criteria and weights, line items (with quantities and specifications), submission deadline.
4. Category Manager invites at least 3 qualified suppliers from the supplier directory.
5. Category Manager clicks **Publish**. System validates that ≥ 3 suppliers are invited.
6. System sends email invitations and portal notifications to all invited suppliers.
7. Each supplier logs into the portal, reviews the event, and submits a quotation/proposal before the deadline.
8. At the deadline, the event closes automatically. System acknowledges all respondents.
9. Category Manager opens the evaluation view.
10. System displays all responses in a side-by-side comparison matrix with weighted scores per criterion.
11. Category Manager reviews scores, adjusts weights if needed, and adds qualitative notes.
12. Category Manager selects the winning supplier(s) and clicks **Award**.
13. System records the award decision with the evaluation matrix snapshot.
14. System notifies winning supplier(s) and sends polite decline notifications to unsuccessful suppliers.
15. Category Manager initiates a PO or contract creation directly from the award record.

### Alternative Flows

**A1 — Insufficient Supplier Responses:**
- Fewer than 2 suppliers respond by the deadline.
- Category Manager can extend the deadline, invite additional suppliers, or close the event and proceed with negotiation (with documented justification).

**A2 — Split Award:**
- Category Manager decides to award different line items to different suppliers.
- System records the split award decision; separate POs are created per awarded supplier.

**A3 — Reverse Auction Mode:**
- Category Manager enables reverse auction mode within the RFQ.
- After initial quote submission, a timed live auction opens where suppliers submit competitive bids.
- System shows live ranking (not competitor prices); only lower bids are accepted.
- Auction closes at the set time; winning bid is carried into the award flow.
