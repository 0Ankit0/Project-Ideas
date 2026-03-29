# Use Case Descriptions

## Overview
This document provides detailed descriptions for the most important use cases in the Finance Management System.

---

## UC-GL-001: Create Journal Entry

| Attribute | Description |
|-----------|-------------|
| **Use Case ID** | UC-GL-001 |
| **Name** | Create Journal Entry |
| **Actor** | Accountant |
| **Description** | Accountant creates a manual double-entry journal to record a financial event in the General Ledger |
| **Pre-conditions** | Accountant is authenticated; accounting period is open; Chart of Accounts is configured |
| **Post-conditions** | Journal entry is saved and posted to GL; audit log entry is created |

### Main Flow
1. Accountant navigates to Journal Entries and clicks "New Journal Entry"
2. System displays journal entry form with fields: date, reference, description, lines
3. Accountant enters journal date and a memo description
4. Accountant adds at least two lines: each with account code, description, debit or credit amount
5. System calculates running debit and credit totals in real time
6. Accountant uploads at least one supporting document (invoice, receipt, etc.)
7. Accountant clicks "Post Entry"
8. System validates that total debits equal total credits
9. System validates that the journal date falls within an open period
10. System saves the journal entry with status "Posted" and assigns a unique entry number
11. System records audit log entry with user, timestamp, and entry number

### Alternative Flows
- **A1 – Save as Draft**: Accountant clicks "Save Draft" at step 7; entry is saved with status "Draft" and is not posted to GL until explicitly posted
- **A2 – Recurring Entry**: Accountant enables the recurring option, sets frequency and end date; system creates a recurring schedule and auto-generates entries at each interval

### Exception Flows
- **E1 – Imbalanced Entry**: System displays "Debits must equal credits" error and highlights the discrepancy amount; entry is not posted
- **E2 – Closed Period**: System displays "Accounting period is closed" error; accountant must adjust the date to an open period
- **E3 – Missing Document**: System warns that no supporting document is attached; entry can still be saved with a configurable grace period for document attachment

---

## UC-AP-001: Record Vendor Invoice

| Attribute | Description |
|-----------|-------------|
| **Use Case ID** | UC-AP-001 |
| **Name** | Record Vendor Invoice |
| **Actor** | Accountant |
| **Description** | Accountant records a vendor invoice received against a purchase order and submits it for payment processing |
| **Pre-conditions** | Vendor exists in vendor master; purchase order is approved (for 3-way match); period is open |
| **Post-conditions** | Invoice is recorded in AP; corresponding GL entries are created; invoice is queued for payment |

### Main Flow
1. Accountant navigates to Accounts Payable > Invoices and clicks "New Invoice"
2. Accountant selects the vendor from the vendor master
3. System pre-fills vendor payment terms and default GL accounts
4. Accountant enters invoice number, invoice date, due date, and line items
5. Accountant links the invoice to a purchase order
6. System performs 3-way match: validates invoice lines against PO quantities and received goods receipt
7. System checks for duplicate invoice (same vendor + invoice number + amount)
8. Accountant uploads the invoice document
9. Accountant clicks "Submit for Approval"
10. System routes invoice to Finance Manager for payment approval if amount exceeds threshold
11. Upon approval, system creates AP liability journal entry in GL

### Alternative Flows
- **A1 – 2-Way Match**: No goods receipt exists; system performs 2-way match against PO only and flags for Finance Manager review
- **A2 – Manual GL Override**: Accountant manually specifies the GL account if no PO is linked

### Exception Flows
- **E1 – Duplicate Invoice**: System detects a matching invoice and shows a warning; accountant must confirm it is not a duplicate before saving
- **E2 – 3-Way Match Failure**: Quantity or price deviation exceeds tolerance; system flags the variance and routes to Finance Manager for exception approval
- **E3 – Vendor Inactive**: System displays "Vendor is inactive" and prevents invoice creation

---

## UC-BF-001: Create and Approve Budget

| Attribute | Description |
|-----------|-------------|
| **Use Case ID** | UC-BF-001 |
| **Name** | Create and Approve Budget |
| **Actor** | Budget Manager, Finance Manager, CFO |
| **Description** | Budget Manager creates a departmental budget for a fiscal period, which is reviewed and approved by Finance Manager and CFO before activation |
| **Pre-conditions** | Fiscal year is configured; Chart of Accounts is set up; Budget Manager has access to relevant cost centers |
| **Post-conditions** | Budget is approved and activated; actuals tracking against budget begins |

### Main Flow
1. Budget Manager navigates to Budgeting > New Budget
2. Budget Manager selects fiscal year, cost center/department, and budget template (blank or prior period actuals)
3. Budget Manager enters monthly budget amounts per GL account
4. System calculates annual totals and shows comparison to prior year actuals
5. Budget Manager adds comments and clicks "Submit for Review"
6. System routes budget to Finance Manager with email notification
7. Finance Manager reviews budget line by line and either approves or returns with comments
8. If approved by Finance Manager, system routes to CFO for final approval
9. CFO reviews and approves the budget
10. System activates the budget and makes it available for variance tracking

### Alternative Flows
- **A1 – Revision**: An approved budget can be revised; Budget Manager creates a revision that repeats the approval workflow
- **A2 – Top-Down Input**: CFO enters top-level limits; system distributes to Budget Managers for bottom-up entry within those limits

### Exception Flows
- **E1 – Finance Manager Rejects**: Budget is returned to Budget Manager with rejection comments; Budget Manager revises and resubmits
- **E2 – CFO Rejects**: Budget is returned to Finance Manager with notes; Finance Manager works with Budget Manager to address concerns

---

## UC-EM-001: Submit Expense Claim

| Attribute | Description |
|-----------|-------------|
| **Use Case ID** | UC-EM-001 |
| **Name** | Submit Expense Claim |
| **Actor** | Employee |
| **Description** | Employee submits one or more expense items with receipts for reimbursement |
| **Pre-conditions** | Employee is authenticated; expense categories are configured; reimbursement policy rules are active |
| **Post-conditions** | Expense claim is submitted and routed to Department Head for approval |

### Main Flow
1. Employee navigates to Expenses > New Claim
2. Employee enters claim title and expense period
3. Employee adds expense lines: date, category, amount, description, and receipt upload
4. System validates each line against policy rules (category limits, receipt requirement)
5. System calculates total claim amount and shows applicable policy flags
6. Employee reviews the claim summary and clicks "Submit"
7. System routes claim to the employee's Department Head with notification email
8. System assigns the claim a tracking number and updates status to "Pending Approval"

### Alternative Flows
- **A1 – Mileage Claim**: Employee enters origin, destination, and distance; system auto-calculates amount using configured mileage rate
- **A2 – Corporate Card Reconciliation**: Employee selects imported card transactions instead of manually entering amounts; system links card transactions to the expense report

### Exception Flows
- **E1 – Policy Violation**: System flags items exceeding category limits; employee must add a business justification to proceed
- **E2 – Missing Receipt**: System warns of missing receipts for categories that require them; employee must upload before submission
- **E3 – Duplicate Submission**: System detects a similar claim submitted recently and warns the employee

---

## UC-PR-001: Process Payroll Run

| Attribute | Description |
|-----------|-------------|
| **Use Case ID** | UC-PR-001 |
| **Name** | Process Payroll Run |
| **Actor** | Finance Manager, Accountant |
| **Description** | Finance team processes the payroll for a given pay period, calculates all payments and deductions, and disburses net pay to employees |
| **Pre-conditions** | Payroll period is configured; all employee payroll profiles are complete; timesheets are submitted (if hourly); banking details are on file |
| **Post-conditions** | Payroll is disbursed; GL entries for payroll expense and liabilities are posted; pay stubs are distributed |

### Main Flow
1. Accountant navigates to Payroll > New Payroll Run
2. Accountant selects pay period and pay group
3. System performs pre-run validation: missing bank details, incomplete timesheets, blocked employees
4. Accountant reviews validation report; resolves any blocking issues
5. System calculates gross pay for all employees in the run
6. System applies statutory deductions (income tax, social security, provident fund)
7. System applies voluntary deductions (health insurance, retirement contributions)
8. System generates payroll register showing gross pay, deductions, and net pay per employee
9. Accountant reviews the register and clicks "Submit for Approval"
10. Finance Manager reviews the payroll register and clicks "Approve"
11. System generates the bank ACH/NEFT transfer file for direct deposits
12. System posts payroll journal entries to GL: salary expense, tax liabilities, net pay
13. Finance Manager submits the bank file to the banking system
14. System notifies employees with digital pay stubs once the disbursement is confirmed

### Alternative Flows
- **A1 – Off-Cycle Run**: Ad-hoc payroll for bonuses or corrections; follows same flow with a different run type flag
- **A2 – Manual Check**: Specific employees flagged for check payment instead of direct deposit

### Exception Flows
- **E1 – Bank File Rejection**: Bank rejects one or more transactions; system flags failed entries, notifies Finance Manager, and marks affected employees for re-processing
- **E2 – Finance Manager Rejects**: Payroll run returned with comments; Accountant investigates and corrects before resubmitting

---

## UC-FA-001: Register and Depreciate Fixed Asset

| Attribute | Description |
|-----------|-------------|
| **Use Case ID** | UC-FA-001 |
| **Name** | Register and Depreciate Fixed Asset |
| **Actor** | Accountant |
| **Description** | Accountant registers a newly acquired asset in the system, configures depreciation parameters, and the system automatically posts periodic depreciation journal entries |
| **Pre-conditions** | Asset categories and depreciation methods are configured; corresponding GL accounts exist; period is open |
| **Post-conditions** | Asset is registered with a unique asset ID; depreciation schedule is generated; depreciation journal entries post at each period close |

### Main Flow
1. Accountant navigates to Fixed Assets > New Asset
2. Accountant enters asset name, category, acquisition date, and purchase cost
3. Accountant selects the depreciation method (Straight-Line, Declining Balance)
4. Accountant enters useful life in years and residual value
5. System calculates the annual and monthly depreciation amounts and shows a full schedule
6. Accountant assigns the asset to a department and physical location
7. Accountant attaches the purchase invoice
8. Accountant saves the asset record
9. At each period close, the system automatically posts a depreciation journal entry debiting the depreciation expense account and crediting the accumulated depreciation account

### Alternative Flows
- **A1 – Partial Period**: Asset acquired mid-period; system calculates pro-rated depreciation for first period
- **A2 – Asset Disposal**: When an asset is disposed of, the system calculates gain/loss and posts disposal journal entry

### Exception Flows
- **E1 – Negative Net Book Value**: System prevents configurations that would result in net book value going below residual value
- **E2 – Period Closed**: If depreciation posting fails because period is closed, system queues the entry for the next open period and alerts the accountant

## Implementation-Ready Finance Control Expansion

### 1) Accounting Rule Assumptions (Detailed)
- Ledger model is strictly double-entry with balanced journal headers and line-level dimensional tagging (entity, cost-center, project, product, counterparty).
- Posting policies are versioned and time-effective; historical transactions are evaluated against the rule version active at transaction time.
- Currency handling requires transaction currency, functional currency, and optional reporting currency; FX revaluation and realized/unrealized gains are separated.
- Materiality thresholds are explicit and configurable; below-threshold variances may auto-resolve only when policy explicitly allows.

### 2) Transaction Invariants and Data Contracts
- Every command/event must include `transaction_id`, `idempotency_key`, `source_system`, `event_time_utc`, `actor_id/service_principal`, and `policy_version`.
- Mutations affecting posted books are append-only. Corrections use reversal + adjustment entries with causal linkage to original posting IDs.
- Period invariant checks: no unapproved journals in closing period, all sub-ledger control accounts reconciled, and close checklist fully attested.
- Referential invariants: every ledger line links to a provenance artifact (invoice/payment/payroll/expense/asset/tax document).

### 3) Reconciliation and Close Strategy
- Continuous reconciliation cadence:
  - **T+0/T+1** operational reconciliation (gateway, bank, processor, payroll outputs).
  - **Daily** sub-ledger to GL tie-out.
  - **Monthly/Quarterly** close certification with controller sign-off.
- Exception taxonomy is mandatory: timing mismatch, mapping/config error, duplicate, missing source event, external counterparty variance, FX rounding.
- Close blockers are machine-detectable and surfaced on a close dashboard with ownership, ETA, and escalation policy.

### 4) Failure Handling and Operational Recovery
- Posting pipeline uses outbox/inbox patterns with deterministic retries and dead-letter quarantine for non-retriable payloads.
- Duplicate delivery and partial failure scenarios must be proven safe through idempotency and compensating accounting entries.
- Incident runbooks require: containment decision, scope quantification, replay/rebuild method, reconciliation rerun, and financial controller approval.
- Recovery drills must be executed periodically with evidence retained for audit.

### 5) Regulatory / Compliance / Audit Expectations
- Controls must support segregation of duties, least privilege, and end-to-end tamper-evident audit trails.
- Retention strategy must satisfy jurisdictional requirements for financial records, tax documents, and payroll artifacts.
- Sensitive data handling includes classification, masking/tokenization for non-production, and secure export controls.
- Every policy override (manual journal, reopened period, emergency access) requires reason code, approver, and expiration window.

### 6) Data Lineage & Traceability (Requirements → Implementation)
- Maintain an explicit traceability matrix for this artifact (`analysis/use-case-descriptions.md`):
  - `Requirement ID` → `Business Rule / Event` → `Design Element` (API/schema/diagram component) → `Code Module` → `Test Evidence` → `Control Owner`.
- Lineage metadata minimums: source event ID, transformation ID/version, posting rule version, reconciliation batch ID, and report consumption path.
- Any change touching accounting semantics must include impact analysis across upstream requirements and downstream close/compliance reports.
- Documentation updates are blocking for release when they alter financial behavior, posting logic, or reconciliation outcomes.

### 7) Phase-Specific Implementation Readiness
- Convert business requirements into executable decision tables with explicit preconditions, data dependencies, and exception states.
- Map each business event to accounting impact (`none`, `memo`, `sub-ledger`, `GL-posting`) and expected latency/SLA.
- Document escalation paths for unresolved breaks, including RACI and aging thresholds.

### 8) Implementation Checklist for `use case descriptions`
- [ ] Control objectives and success/failure criteria are explicit and testable.
- [ ] Data contracts include mandatory identifiers, timestamps, and provenance fields.
- [ ] Reconciliation logic defines cadence, tolerances, ownership, and escalation.
- [ ] Operational runbooks cover retries, replay, backfill, and close re-certification.
- [ ] Compliance evidence artifacts are named, retained, and linked to control owners.


