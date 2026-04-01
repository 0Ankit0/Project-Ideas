# User Stories — Supply Chain Management Platform

## Overview

User stories are organised by epic. Each story follows the format:
> *As a [role], I want to [action], so that [benefit].*

Acceptance criteria use the **Given / When / Then** convention or bullet-point style.

---

## Epic 1: Supplier Onboarding & Management

### US-SUP-01 — Invite a Prospective Supplier

**As a** Procurement Manager,
**I want to** send a self-service onboarding invitation to a prospective supplier by email,
**so that** they can register their details without requiring manual data entry by my team.

**Acceptance Criteria:**
- Given a valid supplier email address is entered, when I click "Send Invitation", then the supplier receives an email with a unique, time-limited registration link (expires in 7 days).
- The invitation link leads to a branded registration form collecting: legal name, registered address, tax registration number, primary contact details, and bank account details.
- The system records the invite status as "Invited" and transitions it to "Registered" upon form submission.
- Duplicate email invitations to the same address within 7 days are rejected with an informative error.
- I can view all outstanding invitations and resend or revoke them.

---

### US-SUP-02 — Complete Supplier Self-Registration

**As a** Supplier,
**I want to** complete my company registration on the supplier portal,
**so that** I can begin receiving purchase orders from the buying organisation.

**Acceptance Criteria:**
- The registration form is accessible without a login using the unique invitation link.
- All mandatory fields (legal name, address, tax ID, bank details, primary contact) must be completed before submission.
- I can upload supporting documents (insurance certificate, trade licence, ISO certification) during registration.
- Upon submission, I receive a confirmation email and my account is created in a "Pending Review" state.
- I cannot log into the portal until my qualification is approved by the procurement team.

---

### US-SUP-03 — Qualify a Supplier

**As a** Procurement Manager,
**I want to** review and approve or reject a supplier's registration documents,
**so that** only vetted suppliers are activated in the system and eligible to receive POs.

**Acceptance Criteria:**
- I can view all suppliers in "Pending Review" from a qualification queue.
- I can view all uploaded documents inline and request additional documents with a comment.
- I can approve the supplier (transition to "Qualified"), setting a qualification expiry date.
- I can reject the supplier with a mandatory rejection reason, which is emailed to the supplier.
- Approved suppliers receive a welcome email with portal login instructions.

---

### US-SUP-04 — Manage Supplier Documents with Expiry Alerts

**As a** Procurement Manager,
**I want to** receive automated alerts when a supplier's qualification documents are approaching expiry,
**so that** I can request updated documents before the supplier is blocked from receiving new POs.

**Acceptance Criteria:**
- The system sends email alerts to the supplier account manager at 60 days, 30 days, and 7 days before any document's expiry date.
- A "Documents Expiring" dashboard widget shows all suppliers with documents expiring within 90 days.
- When a document expires, the system automatically flags the supplier as "Qualification Expired".
- Suppliers with "Qualification Expired" status cannot be added to new POs (system enforces this at PO creation).
- Suppliers can upload renewal documents via the supplier portal; re-approval resets the expiry date.

---

### US-SUP-05 — Update Supplier Bank Details (Fraud-Prevention Workflow)

**As a** Supplier,
**I want to** update my bank account details via the portal,
**so that** future payments are sent to my new account.

**Acceptance Criteria:**
- I can initiate a bank detail change request from my portal profile.
- The change triggers a dual-approval workflow requiring two finance team members to authorise.
- Existing bank details remain active until the change is approved.
- Both the supplier and the approvers receive email notifications at each workflow step.
- The system logs the old and new bank details, the requestor, and both approvers with timestamps.
- The old account is immediately deactivated once the new account is confirmed.

---

### US-SUP-06 — Segment and Search Suppliers

**As a** Procurement Manager,
**I want to** filter and search the supplier directory by category, tier, geography, and qualification status,
**so that** I can quickly identify the right suppliers for a new sourcing event.

**Acceptance Criteria:**
- The supplier directory supports free-text search on company name, tax ID, and contact name.
- Filters include: category (multi-select), tier (strategic/preferred/approved/restricted), country, and qualification status.
- Search results display: supplier name, tier, category, country, OTD score, and qualification status.
- Results can be exported to CSV.

---

### US-SUP-07 — View Supplier Performance History

**As a** Category Manager,
**I want to** view a supplier's historical performance scores and trend charts,
**so that** I can make informed decisions about renewing or terminating the supplier relationship.

**Acceptance Criteria:**
- The supplier profile includes a "Performance" tab showing OTD %, quality acceptance rate, invoice accuracy %, and response time by month for the past 24 months.
- Each KPI is displayed as a trend chart with an industry benchmark line where available.
- I can drill down to the individual POs and receipts that contributed to a KPI score.
- The tab shows any open disputes and their resolution outcomes.

---

### US-SUP-08 — Suspend and Off-board a Supplier

**As a** Procurement Manager,
**I want to** suspend or off-board a supplier without disrupting in-flight POs,
**so that** I can act quickly on compliance failures while maintaining supply continuity.

**Acceptance Criteria:**
- I can set a supplier status to "Suspended" with a mandatory reason code and effective date.
- Suspended suppliers cannot be selected on new PRs or POs; existing open POs are flagged but not cancelled automatically.
- Off-boarding requires a secondary approval from the Compliance Officer role.
- Off-boarded suppliers retain read-only access to their historical invoices and payments in the portal for 12 months.
- The system sends a formal off-boarding notification to the supplier's primary contact.

---

## Epic 2: Purchase Requisition & Approval

### US-PRQ-01 — Create a Purchase Requisition

**As an** Employee (Requester),
**I want to** create a purchase requisition from the internal catalogue or as a free-text request,
**so that** I can formally request goods or services and trigger the approval workflow.

**Acceptance Criteria:**
- I can search and select items from the approved item master catalogue.
- For items not in catalogue, I can enter a free-text description, estimated unit price, and quantity.
- I must specify a cost centre, delivery address, and required delivery date.
- The system performs a budget check and shows my available budget balance before submission.
- If the PR would exceed the available budget, submission is blocked with an explanation.
- Upon submission, the system assigns a PR number and routes to the correct approver(s) automatically.

---

### US-PRQ-02 — Approve or Reject a Purchase Requisition (L1 Approver)

**As a** Line Manager (L1 Approver),
**I want to** review and approve or reject a purchase requisition on my phone,
**so that** I can action requests promptly without being at my desk.

**Acceptance Criteria:**
- I receive an email with a summary and a deep link to approve/reject in one click.
- The mobile-responsive approval view shows: requester name, items, total cost, cost centre, budget balance, and any supporting documents.
- I can approve, reject (with mandatory comment), or return for revision.
- Approved PRs that exceed $10,000 are automatically escalated to L2 for secondary approval.
- If I do not action within 48 hours, the system sends a reminder; after 72 hours it auto-escalates to my manager.

---

### US-PRQ-03 — Multi-Level Approval Routing

**As a** Procurement Manager,
**I want to** configure approval chains based on amount thresholds and cost centres,
**so that** the right level of authority approves each requisition without manual routing.

**Acceptance Criteria:**
- Approval rules are configured per legal entity with at least three tiers: < $1,000 (auto-approve), $1,000–$10,000 (L1), > $10,000 (L1 + L2/CFO).
- Cost-centre owners are assigned as default L1 approvers; their managers are L2.
- Changes to approval rules take effect for new PRs only (no retroactive changes).
- Delegated authority is supported: an approver can delegate to a named colleague for a date range.
- The PR status history shows each approval step, actor, timestamp, and comment.

---

### US-PRQ-04 — Consolidate Requisitions into a Purchase Order

**As a** Procurement Manager,
**I want to** consolidate multiple approved PRs from the same supplier and cost centre into a single PO,
**so that** I reduce administrative overhead and leverage bulk pricing.

**Acceptance Criteria:**
- I can select multiple approved PRs from the consolidation queue, filtered by supplier and cost centre.
- The system warns me if selected PRs have different required delivery dates.
- The consolidated PO combines all line items; I can adjust quantities before issuing.
- The resulting PO references all source PR numbers in its header.
- Consolidated PRs transition to "Converted to PO" status and can no longer be converted again.

---

### US-PRQ-05 — Track Requisition Status

**As an** Employee (Requester),
**I want to** track the status of my submitted purchase requisitions in real time,
**so that** I can plan my work without chasing the procurement team.

**Acceptance Criteria:**
- My PR list view shows all my PRs with current status, the current approver's name, and the last activity date.
- I receive email notifications on: submission, approval at each level, rejection, and conversion to PO.
- I can click a PR to view its full timeline: creation → approval steps → PO number → GRN number.

---

### US-PRQ-06 — Cancel a Purchase Requisition

**As an** Employee (Requester),
**I want to** cancel a purchase requisition I no longer need,
**so that** the reserved budget is released back to my cost centre.

**Acceptance Criteria:**
- I can cancel a PR that is in "Draft" or "Under Review" status.
- PRs in "Approved" status can only be cancelled by a Procurement Manager.
- Cancellation requires a reason code selection.
- Cancelled PRs release any committed budget in real time.
- The system notifies all pending approvers that the PR has been cancelled.

---

## Epic 3: Purchase Order Management

### US-PO-01 — Issue a Purchase Order

**As a** Procurement Manager,
**I want to** issue a purchase order to a supplier directly from an approved requisition,
**so that** the supplier has an official, legally binding document to fulfil.

**Acceptance Criteria:**
- The PO is generated with a unique sequential number per legal entity.
- A formatted PDF is generated and emailed to the supplier's designated contact and made available on the supplier portal.
- The PO includes: PO number, issue date, buyer and supplier details, line items (description, qty, UOM, unit price, extended value), delivery address, payment terms, and special instructions.
- The PO status transitions to "Issued – Pending Acknowledgement".

---

### US-PO-02 — Acknowledge a Purchase Order (Supplier)

**As a** Supplier,
**I want to** acknowledge a purchase order on the supplier portal,
**so that** the buyer knows I have received and accepted the terms.

**Acceptance Criteria:**
- I see all new, unacknowledged POs on my portal dashboard with a clear call-to-action.
- I can acknowledge a PO in full or acknowledge with a comment (e.g., adjusted delivery date).
- If I cannot fulfil, I can reject the PO with a reason; the buyer is notified immediately.
- Acknowledged POs are marked "Confirmed" in the buyer's system.
- POs not acknowledged within 3 business days appear in the buyer's unacknowledged PO alert list.

---

### US-PO-03 — Manage a Change Order

**As a** Procurement Manager,
**I want to** amend an issued PO using a formal change order process,
**so that** all modifications are tracked, versioned, and agreed by the supplier.

**Acceptance Criteria:**
- I can initiate a change order on any PO in "Confirmed" or "Partially Received" status.
- Permitted changes: unit price, quantity, delivery date, and special instructions.
- The change order is assigned a sequential version number (PO-1234 Rev 2).
- The supplier receives a notification and must re-acknowledge the amended PO.
- The original PO version remains accessible in the version history.
- Change orders that increase the PO value above the original approval threshold require re-approval.

---

### US-PO-04 — Create a Blanket Purchase Order

**As a** Procurement Manager,
**I want to** create a blanket purchase order with an agreed supplier for a defined period and maximum value,
**so that** operational teams can create release orders quickly without a new approval each time.

**Acceptance Criteria:**
- A blanket PO has: effective date range, maximum commitment value, agreed unit prices per item, and optional minimum/maximum release quantity per order.
- Release orders against a blanket PO do not require full PR/approval if within the blanket's agreed parameters.
- The system tracks cumulative spend against the blanket PO commitment and alerts at 80% and 100% utilisation.
- Release orders that would exceed the blanket commitment require procurement manager approval.

---

### US-PO-05 — Track Inbound Shipments via ASN

**As a** Warehouse Manager,
**I want to** view Advance Shipment Notices submitted by suppliers,
**so that** I can plan warehouse staffing and dock scheduling before goods arrive.

**Acceptance Criteria:**
- Suppliers can submit an ASN via the portal, specifying: carrier, tracking number, expected delivery date, and line-item quantities being shipped.
- I see a daily "Expected Deliveries" view sorted by ETA.
- The system retrieves live tracking status from the carrier API and updates the ASN record.
- When the actual delivery date differs from the ASN by more than 1 business day, an alert is raised on the buyer's dashboard.

---

### US-PO-06 — Cancel a Purchase Order

**As a** Procurement Manager,
**I want to** cancel a purchase order that is no longer required,
**so that** budget is released and the supplier is notified promptly.

**Acceptance Criteria:**
- A PO can be cancelled if no goods have been received against any of its lines.
- Cancellation requires a mandatory reason code.
- The supplier is notified by email and portal notification immediately upon cancellation.
- The PO's committed budget is released to the originating cost centre upon cancellation.
- Partially received POs cannot be fully cancelled; individual open lines can be closed.

---

### US-PO-07 — View PO Spend vs Budget

**As a** Finance Manager,
**I want to** compare actual PO spend against approved budgets by cost centre and period,
**so that** I can identify over-spend early and take corrective action.

**Acceptance Criteria:**
- The budget vs. spend report shows: budget allocated, PO committed, goods received (accrual), and invoiced amounts per cost centre per month.
- I can drill down from cost centre level to individual POs and invoices.
- Variances exceeding ±10% are highlighted in red.
- The report is exportable to Excel.

---

### US-PO-08 — Multi-Currency Purchase Order

**As a** Procurement Manager,
**I want to** issue purchase orders in the supplier's local currency,
**so that** the supplier receives a PO in their preferred currency while my books reflect the base currency equivalent.

**Acceptance Criteria:**
- When creating a PO for a foreign-currency supplier, I select the transaction currency from a configured list.
- The system automatically fetches the exchange rate for the PO issue date and stores it on the PO header.
- All PO values are displayed in both the transaction currency and the base currency.
- The PO PDF shows values in transaction currency only, with an exchange rate disclosure footnote.

---

## Epic 4: Goods Receipt & Quality Inspection

### US-GR-01 — Record a Goods Receipt

**As a** Warehouse Manager,
**I want to** record a goods receipt against an open PO when goods arrive at the warehouse,
**so that** the system reflects accurate received quantities and triggers invoice matching.

**Acceptance Criteria:**
- I can look up the PO by PO number or by scanning a barcode on the delivery note.
- The GRN form pre-fills with all open PO lines and their expected quantities.
- I enter the actual received quantity per line; the system shows the variance from expected.
- I can record partial receipt (some lines not yet delivered).
- Upon saving, the GRN number is assigned and the PO's received quantity is updated in real time.

---

### US-GR-02 — Conduct Quality Inspection

**As a** Quality Inspector,
**I want to** record the quality inspection outcome for received goods,
**so that** defective items are quarantined and the supplier's quality score is updated.

**Acceptance Criteria:**
- For each receipt line flagged for inspection, I can record: accepted quantity, rejected quantity, and defect reason codes.
- I can conditionally accept items (e.g., minor defect, accepted at a discount) with a note.
- Rejected quantities are automatically placed in a quarantine location.
- The inspection result is linked to the GRN and flows to the supplier performance record.
- I can upload photos of defects as attachments to the inspection record.

---

### US-GR-03 — Initiate Return-to-Vendor

**As a** Warehouse Manager,
**I want to** initiate a return-to-vendor (RTV) process for rejected goods,
**so that** the supplier retrieves the items and the financial impact is reflected as a debit note.

**Acceptance Criteria:**
- I can initiate an RTV from a quality inspection record for any rejected quantities.
- The system generates an RTV document with a reference number and emails the supplier.
- A debit note is automatically raised for the value of rejected goods, linked to the original PO.
- The supplier must confirm receipt of the returned goods via the portal.
- Once confirmed, the debit note is applied against the next supplier invoice in the matching engine.

---

### US-GR-04 — Resolve a GRN Discrepancy

**As a** Procurement Manager,
**I want to** investigate and resolve delivery discrepancies flagged on a GRN,
**so that** the PO record is accurate and the correct amount is invoiced.

**Acceptance Criteria:**
- Discrepancies (short-ship, over-ship, wrong item) are listed in a "Discrepancy Queue" dashboard.
- For each discrepancy I can: accept the variance (update PO received qty), raise an RTV, or request re-delivery.
- Resolved discrepancies are removed from the queue and the resolution reason is logged.
- The supplier is notified of the resolution decision via email.

---

### US-GR-05 — Scan and Record Lot/Serial Numbers

**As a** Warehouse Manager,
**I want to** scan lot numbers and serial numbers for traceable items at the point of receipt,
**so that** full traceability is maintained for regulatory compliance and product recalls.

**Acceptance Criteria:**
- Items flagged as "lot-tracked" or "serial-tracked" in the item master require lot/serial entry at receipt.
- I can use a barcode scanner to populate lot/serial fields.
- The system validates that the entered lot/serial number matches the ASN if one was submitted.
- Lot and serial records are stored with GRN number, receipt date, quantity, and location.

---

### US-GR-06 — View ASN-to-GRN Reconciliation

**As a** Procurement Manager,
**I want to** compare submitted ASNs against recorded GRNs,
**so that** I can identify suppliers who consistently under-ship or fail to submit ASNs.

**Acceptance Criteria:**
- The ASN reconciliation report shows: PO line, ASN committed quantity, GRN received quantity, and variance %.
- I can filter by supplier, date range, and variance threshold.
- Suppliers with > 10% negative variance in a rolling 90-day period appear in the supplier performance alert list.

---

## Epic 5: Invoice Processing & Payment

### US-INV-01 — Submit an Invoice (Supplier)

**As a** Supplier,
**I want to** submit an invoice directly via the supplier portal against an acknowledged PO,
**so that** I can ensure the invoice is correctly matched and payment is processed on time.

**Acceptance Criteria:**
- I can create an invoice by selecting an acknowledged PO and specifying quantities and amounts per line.
- I can upload a PDF version of my invoice as an attachment.
- The system validates that invoice line quantities do not exceed remaining uninvoiced PO quantities.
- Upon submission, I see the invoice status ("Submitted", "Under Matching", "Approved", "Disputed", "Paid") in real time.
- I receive an email confirmation of successful invoice submission.

---

### US-INV-02 — Automated Three-Way Matching

**As an** AP Clerk,
**I want** the system to automatically match invoices against POs and goods receipts,
**so that** I only need to review exceptions rather than manually matching every invoice.

**Acceptance Criteria:**
- For each invoice line, the system compares: invoice quantity vs. GRN quantity and invoice unit price vs. PO unit price.
- Invoices within tolerance (±3% price, 0% quantity by default) are auto-approved and flagged "Matched".
- Invoices with variances outside tolerance are flagged "Exception" and routed to the AP queue.
- The matching summary shows which comparison failed, the expected value, actual value, and variance %.
- Matched invoices automatically schedule a payment date based on the supplier's payment terms.

---

### US-INV-03 — Manage an Invoice Dispute

**As an** AP Clerk,
**I want to** raise a structured dispute against an invoice that fails matching,
**so that** the supplier understands the issue and can respond formally.

**Acceptance Criteria:**
- I can raise a dispute on any invoice line, selecting a dispute reason code (price mismatch, quantity variance, duplicate invoice, missing GRN, etc.).
- The supplier is notified immediately via email and portal notification with the dispute details.
- The supplier can respond within the portal: accept the dispute (issue credit note) or contest with evidence.
- If the supplier contests, the AP clerk has 5 business days to review and make a final decision.
- Disputed invoices are on payment hold until the dispute is resolved.
- All dispute messages and attachments are stored as a conversation thread on the invoice.

---

### US-INV-04 — Schedule and Execute Payment

**As a** Finance Manager,
**I want to** review the scheduled payment run and release payments to suppliers,
**so that** suppliers are paid on time in accordance with agreed terms.

**Acceptance Criteria:**
- The payment dashboard shows all invoices due for payment in the next 7/14/30 days, grouped by payment date.
- I can approve the payment run, which generates a payment file in the configured format (BACSv2, ACH, SWIFT).
- I can exclude specific invoices from a payment run with a reason.
- Upon payment execution, supplier invoices are marked "Paid" with a payment reference number.
- Suppliers receive payment advice notifications via email.
- The payment file is automatically transmitted to the banking integration endpoint.

---

### US-INV-05 — Capture Early Payment Discount

**As a** Finance Manager,
**I want to** see invoices eligible for early payment discounts highlighted before the discount window closes,
**so that** the organisation can capture savings by paying early.

**Acceptance Criteria:**
- Invoices with early payment discount terms (e.g., 2/10 Net 30) are highlighted on the payment dashboard with the discount deadline.
- The system calculates the net discount value and displays it alongside the invoice.
- I can filter the payment queue to show only discount-eligible invoices.
- Paying before the discount deadline automatically calculates the discounted amount.
- Captured discounts are recorded as a separate GL line for spend analysis.

---

### US-INV-06 — View Payment Status (Supplier)

**As a** Supplier,
**I want to** view the payment status of my submitted invoices without calling the buyer's accounts payable team,
**so that** I can manage my cash flow accurately.

**Acceptance Criteria:**
- My portal shows all invoices with current status, matched amounts, dispute details if any, scheduled payment date, and actual payment date.
- I can see the payment reference number once payment is executed.
- A remittance advice PDF is available for download for each payment.

---

## Epic 6: Supplier Performance & KPIs

### US-KPI-01 — Calculate Supplier OTD Score

**As the** System,
**I want to** automatically calculate a supplier's On-Time Delivery (OTD) score after each goods receipt,
**so that** the performance record is always current without manual data entry.

**Acceptance Criteria:**
- OTD is calculated as: (number of PO lines received on or before the committed delivery date) / (total PO lines received in the period) × 100.
- The committed delivery date used is the last confirmed date from the supplier's PO acknowledgement.
- OTD is recalculated after every GRN and stored as a rolling 30-day, 90-day, and 12-month average.
- Suppliers with OTD < 85% in any rolling 30-day period appear in the performance alert list.

---

### US-KPI-02 — Generate Supplier Performance Scorecard

**As a** Procurement Manager,
**I want to** generate a monthly performance scorecard for each strategic supplier,
**so that** I have a data-driven basis for performance reviews and contract renewals.

**Acceptance Criteria:**
- The scorecard includes: OTD %, Quality Acceptance Rate %, Invoice Accuracy %, PO Acknowledgement Time (hrs), Dispute Rate %.
- Each KPI is scored 1–5 with a weighted composite score.
- The scorecard can be generated on-demand or scheduled (monthly/quarterly).
- A PDF scorecard is emailed to the supplier's account manager and stored in the supplier record.
- I can add qualitative comments to the scorecard before distribution.

---

### US-KPI-03 — View Supplier Benchmarking

**As a** Category Manager,
**I want to** compare supplier KPIs across all suppliers in a category,
**so that** I can identify best performers and share best practices during sourcing events.

**Acceptance Criteria:**
- The benchmarking view shows all suppliers in a selected category ranked by composite score.
- I can toggle between individual KPIs (OTD, quality, etc.) to see the ranking for each dimension.
- Suppliers below the category median in a KPI are highlighted.
- The view is exportable to Excel for use in business reviews.

---

### US-KPI-04 — Create an SLA Contract for a Supplier

**As a** Procurement Manager,
**I want to** define SLA targets for a strategic supplier's KPIs and track actuals against those targets,
**so that** there is a contractual basis for performance penalties or rewards.

**Acceptance Criteria:**
- I can create an SLA record linked to a supplier and contract, specifying target values for: OTD %, quality %, invoice accuracy %, and response time.
- The system shows actual vs. target on the supplier performance dashboard with RAG (Red/Amber/Green) indicators.
- A breach event is logged when a KPI falls below the SLA threshold for two consecutive months.
- Breach events can trigger a penalty calculation workflow based on the contract terms.

---

### US-KPI-05 — Respond to Performance Review (Supplier)

**As a** Supplier,
**I want to** view my performance scorecard and submit a corrective action plan when I receive a below-target score,
**so that** I can demonstrate commitment to improvement and maintain my supplier relationship.

**Acceptance Criteria:**
- I can see my latest and historical scorecards on the portal.
- When a scorecard is marked "Below Target", I can submit a corrective action plan (free text + attachment).
- The buyer receives a notification when a corrective action plan is submitted.
- The corrective action plan and buyer response are stored as a conversation thread on the scorecard.

---

## Epic 7: Sourcing & RFQ Management

### US-SRC-01 — Publish an RFQ Event

**As a** Category Manager,
**I want to** create and publish a Request for Quotation to a shortlist of qualified suppliers,
**so that** I can solicit competitive pricing for an upcoming purchase.

**Acceptance Criteria:**
- I can create an RFQ with: event name, description, line items (item, description, quantity, UOM), response deadline, and evaluation criteria.
- I must invite at least 3 suppliers (system enforced) before publishing.
- On publish, invited suppliers receive an email with a link to the event in their portal.
- The RFQ closes automatically at the deadline; late submissions are rejected.
- I can extend the deadline before it passes.

---

### US-SRC-02 — Submit a Quote (Supplier)

**As a** Supplier,
**I want to** view RFQ details and submit my quotation through the supplier portal,
**so that** my pricing is considered in the buyer's sourcing decision.

**Acceptance Criteria:**
- I can see open RFQs addressed to me on my portal dashboard.
- I can enter a unit price and lead time per line, and attach supporting documentation.
- I can save a draft and submit before the deadline.
- Once submitted, I cannot amend my quote unless the buyer opens a clarification round.
- I receive a confirmation email with a copy of my submitted quotation.

---

### US-SRC-03 — Evaluate and Award RFQ

**As a** Category Manager,
**I want to** compare all supplier quotes using a weighted scoring model and award the RFQ,
**so that** the sourcing decision is transparent and auditable.

**Acceptance Criteria:**
- The evaluation view shows all responses in a side-by-side comparison with total cost, lead time, and quality score.
- I can apply a configurable weight to each criterion (price, OTD, quality, sustainability) and see calculated scores.
- I can award the full RFQ to one supplier or split lines across multiple suppliers.
- Upon award, the winning supplier(s) are notified; unsuccessful suppliers receive a polite decline notification.
- The award decision and evaluation matrix are stored for 5 years.

---

### US-SRC-04 — Conduct a Reverse Auction

**As a** Category Manager,
**I want to** run a timed reverse auction for commodity items,
**so that** suppliers compete on price in real time and I achieve the lowest possible cost.

**Acceptance Criteria:**
- I can set up a reverse auction with: start time, duration, reserve price (optional), and invited suppliers.
- Suppliers see a live countdown timer and their current rank (not the specific prices of other bidders).
- The system accepts only bids lower than the current lowest bid.
- When the auction closes, the system displays the winning bid and supplier.
- I can accept the winning bid with one click, which creates a draft PO pre-populated with the winning price.

---

### US-SRC-05 — Convert RFQ Award to Purchase Order

**As a** Procurement Manager,
**I want to** convert a sourcing award directly into a purchase order,
**so that** the agreed prices and terms are used without re-keying data.

**Acceptance Criteria:**
- From the awarded RFQ, I can click "Create PO" to generate a draft PO pre-populated with the supplier, line items, quantities, and unit prices from the award.
- I can review and adjust before issuing.
- The PO references the source RFQ number for traceability.
- The generated PO follows the standard PR→PO approval workflow if the value exceeds the approval threshold.

---

## Epic 8: Contract Management

### US-CTR-01 — Create a Supplier Contract

**As a** Procurement Manager,
**I want to** create a formal contract record for a strategic supplier with pricing, SLAs, and terms,
**so that** all procurement activity with that supplier is governed by agreed terms.

**Acceptance Criteria:**
- I can create a contract with: supplier, effective date, expiry date, contract type (framework, MSA, SOW), currency, payment terms, price list reference, and penalty clauses.
- I can upload the signed contract PDF.
- The contract requires secondary approval from the Finance Manager before activation.
- Activated contracts are visible to the supplier in their portal.

---

### US-CTR-02 — Monitor Contract Spend Utilisation

**As a** Category Manager,
**I want to** track actual spend against contracted commitments in real time,
**so that** I can take action before under-utilisation penalties or over-spend scenarios occur.

**Acceptance Criteria:**
- The contract dashboard shows: committed spend, actual PO value released, actual invoiced spend, and remaining commitment.
- Utilisation is shown as a progress bar with alerts at 80% (near limit) and 20% utilisation with 30 days remaining (under-utilisation risk).
- I can drill into the specific POs and invoices contributing to the spend figure.

---

### US-CTR-03 — Renew or Terminate a Contract

**As a** Procurement Manager,
**I want to** initiate a contract renewal or termination workflow with appropriate approvals,
**so that** the organisation is never caught with an expired or unintentionally lapsed contract.

**Acceptance Criteria:**
- The system sends alerts at 90, 60, and 30 days before contract expiry to the contract owner.
- I can initiate a renewal (creates a new contract version with updated terms) or termination (with a notice period and reason).
- Renewal requires the same dual approval as original contract creation.
- Terminated contracts move to an archived status; associated POs are flagged for review.

---

### US-CTR-04 — Execute Contract via eSignature

**As a** Procurement Manager,
**I want to** send a contract for electronic signature to both internal approvers and the supplier,
**so that** contract execution is fast, paperless, and legally compliant.

**Acceptance Criteria:**
- I can initiate an eSignature workflow from the contract record (integrated with DocuSign or equivalent).
- The system tracks signature status for each required signatory.
- Upon all parties signing, the signed PDF is automatically stored on the contract record.
- The contract status transitions to "Executed" automatically.

---

## Epic 9: Analytics & Reporting

### US-ANA-01 — View Spend Analytics Dashboard

**As a** CFO,
**I want to** view a real-time spend analytics dashboard segmented by category, supplier, entity, and time period,
**so that** I can identify savings opportunities and areas of non-compliant spend.

**Acceptance Criteria:**
- The dashboard loads within 5 seconds with up to 24 months of data.
- I can toggle between PO spend, invoiced spend, and paid spend.
- Drill-down is available from category → sub-category → supplier → individual PO.
- The dashboard highlights non-PO invoices (invoices with no matching PO) as a % of total spend.

---

### US-ANA-02 — Generate a Procurement Cycle Time Report

**As a** Procurement Manager,
**I want to** see average cycle times for key procurement milestones,
**so that** I can identify bottlenecks and set improvement targets.

**Acceptance Criteria:**
- The report shows average and 90th percentile times for: PR submission → L1 approval, L1 → L2 approval, PO issuance → supplier acknowledgement, PO issuance → goods receipt, goods receipt → invoice receipt, invoice receipt → payment.
- I can filter by entity, cost centre, category, and supplier.
- The report compares the current quarter to the same quarter last year.

---

### US-ANA-03 — Export Ad-hoc Report

**As a** Finance Manager,
**I want to** build a custom report with configurable filters and export it to Excel,
**so that** I can answer ad-hoc questions from leadership without waiting for IT.

**Acceptance Criteria:**
- I can access a report builder with field selection from the PO, GRN, and invoice data models.
- I can apply filters on any field and sort/group results.
- The report is exportable to CSV and formatted Excel with column headers.
- Saved report configurations can be reused and shared with colleagues.

---

### US-ANA-04 — View Executive KPI Dashboard

**As a** CEO / COO,
**I want to** view a single-page executive dashboard showing the health of the supply chain,
**so that** I can spot risks and achievements at a glance in my monthly review.

**Acceptance Criteria:**
- The dashboard shows: total PO spend YTD, savings vs. target, supplier on-time delivery (fleet average), pending invoices value, active disputes, and contract compliance %.
- Each KPI shows current value, trend arrow, and target.
- The page is printable as a PDF for board pack inclusion.
