# User Stories

## CFO User Stories

### Financial Oversight

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
