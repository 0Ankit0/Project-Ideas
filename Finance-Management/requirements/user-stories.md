# User Stories — Finance Management System

Stories are organised by epic. Each story follows the format: **"As a [actor], I want to [action] so that [benefit]."** Acceptance criteria (AC) define the conditions of satisfaction for each story.

---

## Epic 1 — General Ledger

### US-001 · Create GL Account

**As a** Finance Manager, **I want to** add a new account to the chart of accounts with type, normal balance, and segment codes **so that** transactions can be posted to the correct ledger account.

**Acceptance Criteria:**
- AC-1: The form requires account number (unique), account name, account type (Asset / Liability / Equity / Revenue / Expense), and normal balance (Debit / Credit).
- AC-2: Submitting a duplicate account number returns a 409 error with a descriptive message.
- AC-3: The new account appears immediately in the COA hierarchy view and is available for journal entry selection.
- AC-4: An audit log entry is created capturing the creator, timestamp, and all field values.
- AC-5: Deactivating an account with open balances requires a Finance Manager confirmation prompt and generates a system warning.

---

### US-002 · Create and Submit Journal Entry

**As an** Accountant, **I want to** create a multi-line journal entry and submit it for approval **so that** financial transactions are recorded accurately in the general ledger.

**Acceptance Criteria:**
- AC-1: The entry form enforces that total debits equal total credits before allowing submission; an unbalanced entry cannot be saved as Submitted.
- AC-2: Each line requires a GL account, debit or credit amount, cost centre, and optional memo.
- AC-3: Up to ten supporting documents (PDF, XLSX, image) can be attached per entry.
- AC-4: On submission, the designated approver receives an in-app notification and email with a direct link to the entry.
- AC-5: The entry status changes to Submitted and is visible in the approver's pending-approval queue.

---

### US-003 · Approve and Post Journal Entry

**As a** Finance Manager, **I want to** review and approve submitted journal entries **so that** only authorised transactions are reflected in the general ledger.

**Acceptance Criteria:**
- AC-1: The approval screen displays entry header (date, reference, description), all debit/credit lines, and attached documents.
- AC-2: Approving the entry changes its status to Approved and makes it available for batch posting.
- AC-3: Rejecting the entry returns it to Draft with a mandatory rejection comment visible to the originator.
- AC-4: Posting an Approved entry creates an immutable ledger record and updates account balances in real time.
- AC-5: The approver cannot be the same user who created the entry (segregation of duties enforced at the API layer).

---

### US-004 · Reverse a Posted Journal Entry

**As an** Accountant, **I want to** create a reversal of a posted journal entry **so that** an incorrect posting is corrected without altering the immutable original record.

**Acceptance Criteria:**
- AC-1: The reversal form auto-populates all lines with swapped debit/credit amounts and a reversal date defaulting to the first day of the next open period.
- AC-2: The reversal entry is linked to the original by `source_entry_id` and displayed as a paired record in the GL view.
- AC-3: The original entry shows a "Reversed" badge and the reversal entry ID in its detail panel.
- AC-4: Reversals follow the same Submitted → Approved → Posted workflow as original entries.

---

### US-005 · Lock Posting to a Closed Period

**As a** Controller, **I want** the system to prevent any postings to a hard-closed period **so that** finalised financial statements cannot be altered without authorised override.

**Acceptance Criteria:**
- AC-1: Attempting to post a journal entry with a date in a hard-closed period returns a 422 error: "Period [YYYY-MM] is hard-closed."
- AC-2: The override workflow requires a CFO-level approver and a mandatory reason code selected from a configurable list.
- AC-3: Every override creates an audit log entry with actor, reason code, original requester, and timestamp.
- AC-4: The overridden period is flagged in the period list with an "Override used" indicator and approver name.

---

### US-006 · Multi-Currency Journal Entry

**As an** Accountant, **I want to** record a transaction in a foreign currency with automatic functional-currency conversion **so that** the ledger always reflects amounts in the entity's base currency.

**Acceptance Criteria:**
- AC-1: The entry form allows selection of transaction currency; the system auto-fetches the rate for the entry date.
- AC-2: Functional-currency amounts are displayed alongside transaction-currency amounts on all line items.
- AC-3: Manual rate override is allowed with a mandatory reason code; the override is flagged in the entry detail.
- AC-4: Period-end revaluation automatically recalculates open monetary balances and posts FX gain/loss to the designated account.

---

## Epic 2 — Accounts Payable

### US-007 · Record Vendor Invoice

**As an** Accountant, **I want to** record a vendor invoice against a purchase order **so that** the payable is tracked and the PO is consumed.

**Acceptance Criteria:**
- AC-1: The invoice form requires vendor, invoice number, invoice date, due date, line items with GL account, and tax code.
- AC-2: 3-way PO match validates quantity received, unit price, and invoice total against the linked PO and goods receipt; variances above 2 % are flagged.
- AC-3: Duplicate detection checks vendor ID + invoice number + amount; a duplicate candidate is blocked pending review.
- AC-4: The system calculates and displays the early-payment discount amount and discount expiry date based on vendor payment terms.
- AC-5: A GL entry (Debit: Expense / Credit: Accounts Payable) is staged and visible prior to approval.

---

### US-008 · Approve and Schedule Vendor Payment

**As a** Finance Manager, **I want to** review approved invoices and schedule them for payment **so that** suppliers are paid on time within cash-flow constraints.

**Acceptance Criteria:**
- AC-1: The payment scheduling screen lists all approved invoices with due date, discount expiry, and outstanding amount.
- AC-2: Selecting invoices and clicking "Schedule" creates a payment batch with a proposed payment date.
- AC-3: Payment batches above the configurable dual-approval threshold are routed to a second Finance Manager before transmission.
- AC-4: Approved batches generate a NACHA, SEPA XML, or BAI2 payment file downloadable for bank upload.
- AC-5: Confirmed payments update invoice status to Paid and post the GL settlement entry automatically.

---

### US-009 · Generate AP Ageing Report

**As an** Accountant, **I want to** generate an AP ageing report **so that** overdue payables are identified and cash-flow planning is supported.

**Acceptance Criteria:**
- AC-1: Report displays ageing buckets: Current, 1–30, 31–60, 61–90, 91–120, and 120+ days past due.
- AC-2: Results can be filtered by vendor, cost centre, and entity.
- AC-3: Drill-down from any bucket cell navigates to the list of underlying invoices.
- AC-4: Report is exportable to PDF and XLSX with filters and run-date preserved in the export header.

---

### US-010 · Record Vendor Credit Note

**As an** Accountant, **I want to** record a vendor credit note **so that** overbillings are offset against outstanding payables.

**Acceptance Criteria:**
- AC-1: The credit note form links to the original invoice and pre-fills vendor and GL account.
- AC-2: The credit note reduces the vendor's outstanding AP balance; it cannot exceed the original invoice amount.
- AC-3: A GL entry (Debit: Accounts Payable / Credit: Expense) is posted on approval.
- AC-4: The original invoice shows the applied credit amount and revised outstanding balance.

---

## Epic 3 — Accounts Receivable

### US-011 · Create and Issue Customer Invoice

**As an** Accountant, **I want to** create and issue a customer invoice with auto-calculated tax **so that** revenue is billed accurately and promptly.

**Acceptance Criteria:**
- AC-1: The invoice form requires customer, invoice date, payment terms, and at least one line item with quantity, unit price, and tax code.
- AC-2: Tax is auto-calculated per line based on the customer's jurisdiction and the product/service tax code.
- AC-3: Issuing the invoice generates a PDF and sends it to the customer's registered email; delivery status is tracked.
- AC-4: A GL entry (Debit: Accounts Receivable / Credit: Revenue) is posted on issue.
- AC-5: Issuing an invoice to a customer at or above their credit limit is blocked with a clear error; Finance Manager can override with a reason code.

---

### US-012 · Apply Customer Payment

**As an** Accountant, **I want to** record a customer payment and apply it to one or more outstanding invoices **so that** AR balances are accurately maintained.

**Acceptance Criteria:**
- AC-1: Payment entry form allows selection of customer, payment method, amount, and value date.
- AC-2: Partial payments are supported; the invoice shows both the payment applied and the remaining open balance.
- AC-3: Overpayments create a customer credit that can be applied to future invoices or refunded.
- AC-4: A GL entry (Debit: Bank / Credit: Accounts Receivable) is posted on confirmation.

---

### US-013 · Automated Dunning

**As a** Finance Manager, **I want** the system to send automated payment reminders to overdue customers **so that** collections are prompt and consistent without manual chasing.

**Acceptance Criteria:**
- AC-1: Dunning schedules are configurable per customer tier (standard, VIP, high-risk) with message templates and escalation levels.
- AC-2: Reminders are dispatched at 7, 14, 30, and 60 days past due; each dispatch is logged with recipient, channel, and timestamp.
- AC-3: A customer on a legal-hold flag is excluded from automated dunning.
- AC-4: Dunning activity is visible on the AR invoice detail screen.

---

### US-014 · AR Write-Off

**As an** Accountant, **I want to** write off an uncollectable AR balance **so that** the balance sheet reflects only realisable receivables.

**Acceptance Criteria:**
- AC-1: Write-off form requires selection of invoice, write-off date, and reason code from a configurable list.
- AC-2: Write-off amounts above the configurable threshold (default £5 000) require dual approval.
- AC-3: A GL entry (Debit: Bad Debt Expense / Credit: Accounts Receivable) is posted on approval.
- AC-4: The written-off invoice is marked "Written Off" and excluded from ageing and collection reports.

---

## Epic 4 — Bank Reconciliation

### US-015 · Import Bank Statement

**As an** Accountant, **I want to** import a bank statement file **so that** bank transactions are available for reconciliation without manual data entry.

**Acceptance Criteria:**
- AC-1: The import accepts CSV, BAI2, and SWIFT MT940 files up to 50 MB.
- AC-2: Invalid files are rejected with a line-level error report identifying each malformed record.
- AC-3: Successfully imported lines appear in the unreconciled queue tagged with the bank account and value date.
- AC-4: Duplicate lines (same bank reference already imported) are flagged for review and blocked from auto-matching.

---

### US-016 · Auto-Match Bank Transactions

**As an** Accountant, **I want** the reconciliation engine to automatically match bank lines to GL transactions **so that** the volume of manual matching work is minimised.

**Acceptance Criteria:**
- AC-1: The engine matches on amount, value date (±1 business day tolerance), and reference; matches above the configurable confidence threshold are accepted automatically.
- AC-2: Ambiguous or below-threshold matches are placed in the exceptions queue for manual review.
- AC-3: Each auto-match records the matching rule applied and confidence score for auditability.
- AC-4: The reconciliation summary shows matched count, unmatched count, and outstanding GL items.

---

### US-017 · Sign Off Bank Reconciliation

**As a** Finance Manager, **I want to** sign off a completed bank reconciliation **so that** the bank balance is certified as agreeing to the GL and the period can proceed to close.

**Acceptance Criteria:**
- AC-1: Sign-off is available only when all imported bank lines are either matched or explicitly marked as resolved exceptions.
- AC-2: Sign-off records the approver's name, timestamp, and GL closing balance at sign-off time.
- AC-3: Signed-off reconciliations are locked and read-only; any subsequent bank adjustment requires a new import and re-reconciliation.
- AC-4: The signed-off reconciliation is linked from the period-close checklist as evidence.

---

## Epic 5 — Budgeting

### US-018 · Create Annual Budget

**As a** Budget Manager, **I want to** create an annual budget at the account and cost-centre level with monthly breakdown **so that** planned spending is authorised and trackable.

**Acceptance Criteria:**
- AC-1: Budget creation form allows selection of fiscal year, entity, cost centre, and GL account range.
- AC-2: Monthly amounts are entered per account line; the form shows the annual total as amounts are entered.
- AC-3: Budgets are saved as Draft until submitted for approval.
- AC-4: The system prevents creation of a second Active budget for the same entity/fiscal year without explicitly superseding the existing one.

---

### US-019 · Approve Budget

**As a** Finance Manager, **I want to** review and approve a submitted budget **so that** departmental spending is formally authorised.

**Acceptance Criteria:**
- AC-1: The approval view shows the full budget matrix and a comparison against the prior year's actuals.
- AC-2: Approving the budget changes its status to Active and notifies the Budget Manager.
- AC-3: Partial approval of individual cost-centre budgets is supported; unapproved sections remain in Draft.
- AC-4: Approval creates an audit log entry with the approver, timestamp, and total approved amount.

---

### US-020 · Budget Overrun Alert and Approval

**As a** Budget Manager, **I want** to receive an alert when actuals reach 80 % of my budget and require approval for spending beyond 100 % **so that** overruns are controlled and visible.

**Acceptance Criteria:**
- AC-1: Email and in-app alerts fire automatically when actuals hit 80 % and 95 % of the approved budget for any account-cost-centre line.
- AC-2: Transactions that would cause budget utilisation to exceed 100 % are routed to the Finance Manager for approval before posting.
- AC-3: Finance Manager approval of an over-budget transaction records a reason code and creates an audit entry.
- AC-4: The budget dashboard shows current utilisation percentage, remaining amount, and overrun status per cost centre.

---

### US-021 · Budget Revision

**As a** Budget Manager, **I want to** submit a budget revision for approval **so that** the approved budget reflects updated business plans mid-year.

**Acceptance Criteria:**
- AC-1: A revision creates a new version linked to the current active budget; the original approved amounts are preserved for comparison.
- AC-2: The revision form highlights changed lines with the delta amount and percentage change.
- AC-3: Revisions require the same approval workflow as the original budget.
- AC-4: On approval, the revision becomes the active budget; prior versions are retained in history with version number and approval date.

---

## Epic 6 — Fixed Assets

### US-022 · Register New Fixed Asset

**As an** Accountant, **I want to** add a new asset to the fixed-asset register **so that** its cost, location, and ownership are tracked from acquisition.

**Acceptance Criteria:**
- AC-1: The asset form requires description, category, acquisition date, acquisition cost, useful life (months), residual value, depreciation method, cost centre, and responsible department.
- AC-2: On saving, a GL entry (Debit: Asset Account / Credit: Bank or AP) is staged for approval.
- AC-3: The asset is assigned a unique system-generated asset ID and appears in the asset register immediately.
- AC-4: The system calculates and displays the monthly depreciation charge and projected NBV schedule before the asset is activated.

---

### US-023 · Run Monthly Depreciation

**As an** Accountant, **I want to** run the monthly depreciation calculation and post depreciation entries in bulk **so that** asset values are updated accurately each period.

**Acceptance Criteria:**
- AC-1: The depreciation run calculates charges for all active assets for the selected period using each asset's configured method.
- AC-2: The run produces a preview report listing asset ID, method, opening NBV, depreciation charge, and closing NBV before posting.
- AC-3: Posting the run creates individual GL entries per asset category (Debit: Depreciation Expense / Credit: Accumulated Depreciation).
- AC-4: Assets that are fully depreciated (NBV = residual value) are excluded from the calculation and flagged in the run report.

---

### US-024 · Dispose of Fixed Asset

**As an** Accountant, **I want to** record the disposal of a fixed asset **so that** the asset is removed from the register and any gain or loss is recognised in the income statement.

**Acceptance Criteria:**
- AC-1: Disposal form captures disposal date, disposal method (sale, scrap, transfer), proceeds amount, and cost centre.
- AC-2: The system calculates the gain or loss as: proceeds − net book value at disposal date.
- AC-3: GL entries are automatically generated: remove asset cost, remove accumulated depreciation, record proceeds, and post gain/loss.
- AC-4: The disposed asset is marked Inactive in the register with disposal date and final NBV.

---

## Epic 7 — Tax Management

### US-025 · Configure Tax Rate

**As a** Finance Manager, **I want to** configure jurisdiction-specific tax rates with effective dates **so that** all transactions are taxed at the correct rate without manual intervention.

**Acceptance Criteria:**
- AC-1: Tax rate form requires jurisdiction, tax type (VAT, GST, Sales Tax, Withholding), rate percentage, effective date, and optional expiry date.
- AC-2: Overlapping effective-date ranges for the same jurisdiction and tax type are rejected with a validation error.
- AC-3: Rates are applied to transactions based on the transaction date; historical transactions are not retroactively affected unless explicitly requested with a reason code.
- AC-4: A new rate record is created for each change, preserving the history of all prior rates.

---

### US-026 · Auto-Calculate Tax on Invoice

**As an** Accountant, **I want** tax to be automatically calculated on each invoice line based on tax codes and the customer's jurisdiction **so that** invoices are accurate and compliant without manual tax lookup.

**Acceptance Criteria:**
- AC-1: Tax amount is calculated per line using: line amount × applicable rate for the transaction date and jurisdiction.
- AC-2: Reverse-charge VAT is applied automatically when the customer is a VAT-registered business in a cross-border B2B scenario within a supported jurisdiction.
- AC-3: Tax-exempt customers and zero-rated products are handled without manual override; the tax code drives the zero-rate application.
- AC-4: The invoice PDF displays tax amount per line and total tax summary broken down by tax type.

---

### US-027 · Generate Tax Return Summary

**As a** Finance Manager, **I want to** generate a tax return summary report for a selected jurisdiction and period **so that** the data needed for statutory filing is available and accurate.

**Acceptance Criteria:**
- AC-1: Report shows total output tax (sales), total input tax (purchases), and net VAT/GST payable or refundable.
- AC-2: Report is filterable by jurisdiction, entity, and period.
- AC-3: Drill-down from any summary figure navigates to the list of underlying transactions.
- AC-4: Report is exportable to PDF and XLSX in the format prescribed by the relevant tax authority.

---

## Epic 8 — Financial Reporting

### US-028 · Generate Profit and Loss Statement

**As a** CFO, **I want to** generate a P&L statement for any entity and period combination **so that** financial performance is visible for decision-making and board reporting.

**Acceptance Criteria:**
- AC-1: Report parameters include entity (or consolidated group), period (single month, quarter, or YTD), and comparative period.
- AC-2: Report structure follows the configured COA hierarchy with subtotals per account group and grand totals for Revenue, COGS, Gross Profit, Operating Expenses, and Net Income.
- AC-3: Variance columns (amount and %) against the comparative period and approved budget are included.
- AC-4: Report renders in ≤ 2 s for a single entity; exportable to PDF and XLSX.

---

### US-029 · Generate Balance Sheet

**As a** CFO, **I want to** generate a balance sheet as at any date **so that** the financial position of the entity is clearly stated.

**Acceptance Criteria:**
- AC-1: Report shows Assets, Liabilities, and Equity sections with sub-groupings per the configured COA hierarchy.
- AC-2: The equation Assets = Liabilities + Equity is validated; a warning is surfaced if the statement does not balance (indicating a data integrity issue).
- AC-3: Comparative figures for the prior period and prior year end are included.
- AC-4: Exportable to PDF and XLSX.

---

### US-030 · Generate Cash Flow Statement

**As a** Finance Manager, **I want to** generate a cash flow statement using the indirect method **so that** operating, investing, and financing activities are clearly presented.

**Acceptance Criteria:**
- AC-1: Operating activities are derived from net income adjusted for non-cash items and working capital movements.
- AC-2: Investing and financing activities are derived from configured GL account mappings.
- AC-3: Opening and closing cash balances reconcile to the GL bank account balances.
- AC-4: Exportable to PDF and XLSX with configurable period selection.

---

### US-031 · Consolidated Financial Reporting

**As a** CFO, **I want to** generate consolidated financial statements for the group **so that** the combined financial position and performance of all subsidiaries is reported to stakeholders.

**Acceptance Criteria:**
- AC-1: Consolidation includes all entities flagged as subsidiaries of the selected parent entity.
- AC-2: Intercompany transactions (payables, receivables, revenues, expenses) are automatically eliminated on consolidation.
- AC-3: Minority-interest calculations are applied for subsidiaries with less than 100 % ownership.
- AC-4: The consolidation report identifies eliminated amounts and their source entities for auditability.

---

## Epic 9 — Period Close

### US-032 · Initiate Period-Close Checklist

**As a** Finance Manager, **I want to** initiate the period-close checklist at month-end **so that** all required tasks are assigned, tracked, and completed before the period is locked.

**Acceptance Criteria:**
- AC-1: Initiating the close creates task assignments from the configured close template, with due dates and responsible users.
- AC-2: Assigned users receive in-app and email notifications with task details and deadlines.
- AC-3: The close dashboard shows overall completion percentage and individual task status.
- AC-4: Tasks marked Complete require the completing user to confirm; tasks can be re-opened by a Finance Manager if errors are found.

---

### US-033 · Perform Soft Close

**As a** Controller, **I want to** transition a period to Soft-Close status **so that** adjusting entries can still be posted while preventing routine transactions from being entered into the period.

**Acceptance Criteria:**
- AC-1: Soft-close prevents posting by Accountant role but allows Finance Manager and Controller roles to post adjusting entries.
- AC-2: Users attempting to post to a soft-closed period with insufficient role see a clear error message with the period status and their role limitations.
- AC-3: A soft-close event is logged in the audit trail with actor and timestamp.

---

### US-034 · Hard Close Period

**As a** Controller, **I want to** hard-close a period after all adjustments are complete **so that** the period's financial statements are finalised and protected from further changes.

**Acceptance Criteria:**
- AC-1: Hard-close is only available when all period-close checklist items are marked Complete and the bank reconciliation is signed off.
- AC-2: Hard-close requires Controller sign-off; an optional CFO countersign is configurable.
- AC-3: After hard-close, no postings are accepted for the period without a dual-approved CFO override.
- AC-4: Closing entries for nominal accounts are automatically generated and posted as part of the hard-close process.

---

## Epic 10 — Audit Trail

### US-035 · View Audit Trail

**As an** Auditor, **I want to** search and view the complete audit trail for any financial record **so that** I can trace the full history of every change for compliance and investigation purposes.

**Acceptance Criteria:**
- AC-1: The audit log is searchable by entity type, record ID, user, date range, and action type (create, update, approve, post, delete).
- AC-2: Each log entry shows: timestamp, actor (user ID and name), action, entity type, record ID, and before/after field values in a structured diff format.
- AC-3: The audit log is read-only for all roles including system administrators; no UI or API permits deletion or modification.
- AC-4: The audit log is exportable to PDF and CSV for a selected filter combination.

---

### US-036 · Detect Segregation-of-Duties Violation

**As an** Auditor, **I want** the system to enforce and report on segregation-of-duties (SoD) conflicts **so that** no single user can both initiate and approve the same transaction.

**Acceptance Criteria:**
- AC-1: SoD rules are defined as role-pair conflicts (e.g., "Journal Entry Creator" cannot also be "Journal Entry Approver").
- AC-2: Assigning a conflicting role pair to a single user is blocked at the user-management layer with an explanatory error.
- AC-3: The compliance exception report surfaces any user who has both conflicting roles (e.g., due to a historical configuration error) for remediation.
- AC-4: SoD rule changes are logged in the audit trail with actor and justification.

---

### US-037 · Generate Compliance Exception Report

**As an** Auditor, **I want to** run a compliance exception report **so that** control failures are identified and can be investigated before the audit.

**Acceptance Criteria:**
- AC-1: Report includes: high-value journal entries without dual approval, invoices approved by the same user who created them, payments above threshold without a second approver, and period-close overrides.
- AC-2: Each exception row shows the record ID, actors involved, amounts, and dates.
- AC-3: Report is filterable by exception type, entity, and date range.
- AC-4: Exportable to PDF and XLSX.

---

## Epic 11 — Employee Expenses

### US-038 · Submit Expense Claim

**As an** Employee, **I want to** submit an expense claim with receipts **so that** I am reimbursed for business expenditure in a timely manner.

**Acceptance Criteria:**
- AC-1: Expense form requires date, expense category, amount, currency, and receipt upload (JPEG, PNG, PDF, max 10 MB).
- AC-2: Per-diem and mileage-rate amounts are auto-calculated based on configurable rate tables; the employee enters distance or days.
- AC-3: Duplicate detection warns if an expense with the same amount, date, and category was submitted within the last 30 days.
- AC-4: Submitted claims appear in the approving manager's queue within 60 seconds of submission.
- AC-5: Employee receives a confirmation notification with expected approval timeline.

---

### US-039 · Approve Expense Claim

**As a** Department Head, **I want to** approve or reject expense claims from my team **so that** only legitimate business expenses are reimbursed.

**Acceptance Criteria:**
- AC-1: Approval screen shows expense details, category, amount, receipt image, and policy compliance flag.
- AC-2: Claims flagged as policy violations (e.g., over the meal allowance limit) are highlighted with the violated rule.
- AC-3: Partial approval is not supported; the claim is approved or rejected in full with a mandatory comment on rejection.
- AC-4: Approved claims are batched for payment processing in the next payroll or ad-hoc reimbursement run.

---

## Epic 12 — Multi-Currency and Revaluation

### US-040 · Period-End FX Revaluation

**As an** Accountant, **I want to** run a period-end foreign-currency revaluation **so that** open monetary balances are restated at the closing exchange rate and unrealised FX gains/losses are recognised.

**Acceptance Criteria:**
- AC-1: Revaluation applies the period closing rate to all open foreign-currency AR, AP, and bank balances.
- AC-2: The system posts a GL entry for each revalued balance: (Debit/Credit: Balance Account / Credit/Debit: Unrealised FX Gain-Loss Account).
- AC-3: Revaluation entries are automatically reversed at the start of the next period to avoid double-counting.
- AC-4: A revaluation report lists each balance revalued, original amount, closing rate, revalued amount, and FX adjustment.

---

### US-041 · Manage Exchange Rate Table

**As a** Finance Manager, **I want to** review and override the system-loaded exchange rates **so that** rates are accurate when the automatic feed is delayed or incorrect.

**Acceptance Criteria:**
- AC-1: Daily rates are auto-loaded from the configured provider; the last successful load timestamp is displayed.
- AC-2: Manual rate override requires a mandatory reason code and Finance Manager approval; the override is flagged in all transactions that use it.
- AC-3: A rate history view shows all rates per currency pair, source (auto/manual), and entry date.
- AC-4: If the automatic rate feed fails, the system uses the last known rate and raises an operational alert to the Finance Manager.

---

### US-042 · Multi-Entity Intercompany Elimination

**As a** Controller, **I want** intercompany balances to be automatically identified and eliminated during consolidation **so that** group financial statements do not double-count intra-group transactions.

**Acceptance Criteria:**
- AC-1: Intercompany transactions are identified by the counterparty dimension matching another entity within the consolidation group.
- AC-2: Elimination entries are generated for matched IC payable/receivable pairs and IC revenue/expense pairs.
- AC-3: Unmatched IC balances (where one side has no corresponding entry) are surfaced in an IC discrepancy report before consolidation is finalised.
- AC-4: The consolidated P&L and Balance Sheet show eliminated amounts in a separate disclosure column for transparency.

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| CFO-001 | As a CFO, I want to view a real-time financial dashboard so that I can monitor the organization's financial health | - Key KPIs visible<br>- Live P&L summary<br>- Cash position shown |
| CFO-002 | As a CFO, I want to review consolidated financial statements so that I can report to the board | - P&L, Balance Sheet, Cash Flow<br>- Multi-entity consolidation<br>- Period comparison |
| CFO-003 | As a CFO, I want to approve the annual budget so that organizational spending is authorized | - Budget review screen<br>- Comment and approve action<br>- Notify Budget Managers |
| CFO-004 | As a CFO, I want to set spending authorization thresholds so that controls are enforced | - Per-role threshold setup<br>- Saves and applies immediately<br>- Audit log entry created |
| CFO-005 | As a CFO, I want to view cash flow forecasts so that I can make funding decisions | - 13-week rolling forecast<br>- Inflows vs. outflows<br>- Drill-down to source transactions |

---

## Finance Manager User Stories

### Operations Management

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| FM-001 | As a Finance Manager, I want to initiate the period-close checklist so that month-end is completed on time | - Checklist items listed<br>- Assignees notified<br>- Progress tracked |
| FM-002 | As a Finance Manager, I want to approve vendor payment batches so that suppliers are paid on time | - Batch summary visible<br>- Approve/reject individual items<br>- Confirmation email sent |
| FM-003 | As a Finance Manager, I want to review budget vs. actuals so that overspending is caught early | - Side-by-side comparison<br>- Variance percentage shown<br>- Drill-down to transactions |
| FM-004 | As a Finance Manager, I want to manage vendor payment runs so that cash outflows are controlled | - Schedule payment runs<br>- Select invoices<br>- Generate payment file |
| FM-005 | As a Finance Manager, I want to configure tax rates by jurisdiction so that invoices are taxed correctly | - Add/edit tax rates<br>- Assign to transaction types<br>- Effective date support |
| FM-006 | As a Finance Manager, I want to approve payroll runs before disbursement so that errors are caught | - Payroll summary visible<br>- Exception flags highlighted<br>- Approve triggers bank file |

---

## Accountant User Stories

### General Ledger

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| ACC-001 | As an accountant, I want to create journal entries so that financial events are recorded | - Debit/credit lines<br>- Balance validation<br>- Supporting document upload |
| ACC-002 | As an accountant, I want to create recurring journal entries so that regular postings are automated | - Set frequency<br>- Configure start/end date<br>- Auto-post or require review |
| ACC-003 | As an accountant, I want to reverse a journal entry so that incorrect postings are corrected | - Select entry<br>- Generate reversal<br>- Link reversal to original |
| ACC-004 | As an accountant, I want to perform bank reconciliation so that cash balances are verified | - Import bank statement<br>- Auto-match transactions<br>- Flag mismatches |
| ACC-005 | As an accountant, I want to view the trial balance so that I can verify account balances | - All accounts listed<br>- Debit/credit columns<br>- Totals balance |

### Accounts Payable

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| ACC-006 | As an accountant, I want to record vendor invoices so that payables are tracked | - Invoice form<br>- 3-way match validation<br>- Duplicate detection |
| ACC-007 | As an accountant, I want to generate AP aging report so that overdue payables are identified | - Aging buckets (0-30, 31-60, 61-90, 90+)<br>- Per-vendor detail<br>- Export to Excel |
| ACC-008 | As an accountant, I want to record vendor credit notes so that overbillings are adjusted | - Link to original invoice<br>- GL impact shown<br>- AR offset option |

### Accounts Receivable

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| ACC-009 | As an accountant, I want to create customer invoices so that revenue is billed | - Invoice form<br>- Tax calculation<br>- PDF generation |
| ACC-010 | As an accountant, I want to record customer payments so that AR balances are updated | - Payment entry screen<br>- Invoice matching<br>- Partial payment support |
| ACC-011 | As an accountant, I want to view AR aging report so that overdue collections are tracked | - Aging buckets<br>- Per-customer detail<br>- Collection status |
| ACC-012 | As an accountant, I want to write off bad debts so that uncollectable AR is removed | - Select invoice<br>- Enter write-off reason<br>- GL entry auto-created |

---

## Budget Manager User Stories

### Budget Planning

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| BM-001 | As a Budget Manager, I want to create departmental budgets so that spending is planned | - Budget form by account<br>- Monthly breakdown<br>- Save as draft |
| BM-002 | As a Budget Manager, I want to submit budgets for approval so that they are authorized | - Submit button<br>- Route to Finance Manager<br>- Status updates via notification |
| BM-003 | As a Budget Manager, I want to revise approved budgets so that plans stay current | - Create revision<br>- Show changes from original<br>- Re-approval required |
| BM-004 | As a Budget Manager, I want to view budget utilization in real time so that I can manage spending | - % utilized shown<br>- Remaining amount visible<br>- Transaction drill-down |
| BM-005 | As a Budget Manager, I want to receive alerts when spending approaches budget limits so that I can act early | - Alert at 80% and 95% thresholds<br>- Email and in-app<br>- Link to budget detail |

---

## Auditor User Stories

### Audit & Compliance

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| AUD-001 | As an auditor, I want read-only access to all financial records so that I can perform my review | - View GL, AP, AR, payroll<br>- No edit capability<br>- Full history accessible |
| AUD-002 | As an auditor, I want to view the complete audit trail so that I can trace all changes | - Filter by user, date, entity<br>- Before/after values shown<br>- Exportable |
| AUD-003 | As an auditor, I want to run compliance exception reports so that control failures are identified | - Segregation of duties violations<br>- High-value transactions without dual approval<br>- PDF export |
| AUD-004 | As an auditor, I want to review journal entries with supporting documents so that postings are validated | - Entry details visible<br>- Attachments accessible<br>- Preparer and approver shown |
| AUD-005 | As an auditor, I want to generate confirmation letters for AR balances so that customer amounts are verified | - Select customers<br>- Generate confirmation PDF<br>- Track responses |

---

## Employee User Stories

### Expense Management

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| EMP-001 | As an employee, I want to submit an expense claim so that I can be reimbursed | - Expense form<br>- Receipt upload<br>- Category selection |
| EMP-002 | As an employee, I want to track my expense claim status so that I know when I'll be paid | - Status visible (Submitted, Approved, Paid)<br>- Rejection reason shown<br>- Expected payment date |
| EMP-003 | As an employee, I want to submit mileage claims so that travel costs are reimbursed | - Distance entry<br>- Rate auto-applied<br>- Map route option |
| EMP-004 | As an employee, I want to reconcile my corporate card transactions so that my expenses are matched | - Card transaction list<br>- Link to expense report<br>- Unmatched flag |
| EMP-005 | As an employee, I want to view my reimbursement history so that I can track past payments | - Date range filter<br>- Amount and status<br>- Download receipt |

---

## Department Head User Stories

### Departmental Finance

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| DH-001 | As a Department Head, I want to approve expense claims from my team so that spending is controlled | - Pending list<br>- Expense details and receipt<br>- Approve/reject with comment |
| DH-002 | As a Department Head, I want to view my department's budget and spending so that I stay within limits | - Budget vs. actual chart<br>- Top expenses list<br>- Period selector |
| DH-003 | As a Department Head, I want to request a budget revision so that unexpected needs are funded | - Revision form<br>- Justification field<br>- Route to Finance Manager |
| DH-004 | As a Department Head, I want to approve purchase requisitions for my department so that procurement is authorized | - Requisition list<br>- Item details and cost<br>- Approve routes to AP |

---

## System Administrator User Stories

### System Configuration

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| ADM-001 | As an admin, I want to configure the Chart of Accounts so that the GL structure is set up | - Add/edit/deactivate accounts<br>- Account type classification<br>- Hierarchy view |
| ADM-002 | As an admin, I want to manage user roles and permissions so that access is controlled | - Role matrix<br>- Assign to users<br>- Audit log of changes |
| ADM-003 | As an admin, I want to configure approval workflows so that financial controls are enforced | - Workflow builder<br>- Threshold-based routing<br>- Multi-level support |
| ADM-004 | As an admin, I want to manage fiscal year and period settings so that the accounting calendar is accurate | - Fiscal year setup<br>- Period open/close controls<br>- Year-end rollover |
| ADM-005 | As an admin, I want to configure integration credentials for banks and ERP systems so that data flows correctly | - Credential management<br>- Connection test<br>- Sync status visible |
| ADM-006 | As an admin, I want to view system health and audit logs so that I can troubleshoot issues | - Activity logs<br>- Integration status<br>- Error notifications |

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
- Maintain an explicit traceability matrix for this artifact (`requirements/user-stories.md`):
  - `Requirement ID` → `Business Rule / Event` → `Design Element` (API/schema/diagram component) → `Code Module` → `Test Evidence` → `Control Owner`.
- Lineage metadata minimums: source event ID, transformation ID/version, posting rule version, reconciliation batch ID, and report consumption path.
- Any change touching accounting semantics must include impact analysis across upstream requirements and downstream close/compliance reports.
- Documentation updates are blocking for release when they alter financial behavior, posting logic, or reconciliation outcomes.

### 7) Phase-Specific Implementation Readiness
- Define control objectives as testable statements: completeness, accuracy, authorization, cutoff, classification, and valuation.
- Assign each requirement a stable ID (`FR-`, `NFR-`, `CTRL-`) and a control owner (Finance Ops, Controller, Tax, Security, SRE).
- Capture statutory scope per jurisdiction (sales tax/VAT/GST, payroll withholding, e-invoicing, retention windows).

### 8) Implementation Checklist for `user stories`
- [ ] Control objectives and success/failure criteria are explicit and testable.
- [ ] Data contracts include mandatory identifiers, timestamps, and provenance fields.
- [ ] Reconciliation logic defines cadence, tolerances, ownership, and escalation.
- [ ] Operational runbooks cover retries, replay, backfill, and close re-certification.
- [ ] Compliance evidence artifacts are named, retained, and linked to control owners.


