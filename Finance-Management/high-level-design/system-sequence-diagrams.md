# System Sequence Diagrams

## Overview
System-level black-box interaction sequences showing how actors interact with the Finance Management System and how it interacts with external systems.

---

## Create and Post Journal Entry

```mermaid
sequenceDiagram
    participant ACC as Accountant
    participant FMS as Finance Management System
    participant DB as Database
    participant AUDIT as Audit Log

    ACC->>FMS: POST /api/v1/journal-entries (header, lines, attachment)
    FMS->>FMS: Validate debit == credit
    FMS->>FMS: Validate period is open
    FMS->>DB: Check account codes exist
    DB-->>FMS: Accounts valid
    FMS->>DB: Save journal entry (status=POSTED)
    DB-->>FMS: Entry saved with entry_number
    FMS->>AUDIT: Write audit log (user, timestamp, entry_number)
    AUDIT-->>FMS: Logged
    FMS-->>ACC: 201 Created { entry_number, status: POSTED }
```

---

## Process Vendor Payment Run

```mermaid
sequenceDiagram
    participant FM as Finance Manager
    participant FMS as Finance Management System
    participant DB as Database
    participant BANK as Banking System
    participant VENDOR as Vendor (Email)

    FM->>FMS: GET /api/v1/ap/invoices?status=approved&due_before=X
    FMS-->>FM: List of payable invoices

    FM->>FMS: POST /api/v1/ap/payment-runs (invoice_ids[])
    FMS->>FMS: Validate all invoices are approved
    FMS->>FMS: Calculate total and check cash availability
    FMS->>DB: Save payment run (status=PENDING_APPROVAL)
    FMS-->>FM: 201 { run_id, total_amount, invoice_count }

    FM->>FMS: POST /api/v1/ap/payment-runs/{run_id}/approve
    FMS->>FMS: Apply early-payment discounts if eligible
    FMS->>DB: Update run status=APPROVED
    FMS->>BANK: Submit ACH/wire file
    BANK-->>FMS: 200 { batch_ref, status: ACCEPTED }

    FMS->>DB: Update run status=SUBMITTED
    BANK->>FMS: Webhook: payment_cleared (batch_ref)
    FMS->>DB: Mark invoices as PAID
    FMS->>DB: Post GL payment entries
    FMS->>VENDOR: Send remittance advice emails
    FMS-->>FM: Notification: Payment run completed
```

---

## Employee Expense Claim Approval

```mermaid
sequenceDiagram
    participant EMP as Employee
    participant FMS as Finance Management System
    participant DH as Department Head
    participant FM as Finance Manager
    participant PAY as Payment System

    EMP->>FMS: POST /api/v1/expenses (items[], receipts[])
    FMS->>FMS: Validate policy rules
    FMS->>FMS: Check category limits
    FMS-->>EMP: 201 { claim_id, status: PENDING_DEPT_APPROVAL }
    FMS->>DH: Email: Expense claim pending review

    DH->>FMS: POST /api/v1/expenses/{id}/approve
    FMS->>FMS: Check if amount exceeds FM threshold
    FMS-->>DH: 200 { status: PENDING_FM_APPROVAL }
    FMS->>FM: Email: High-value expense pending review

    FM->>FMS: POST /api/v1/expenses/{id}/approve
    FMS->>FMS: Queue for reimbursement
    FMS-->>FM: 200 { status: APPROVED }

    FMS->>PAY: Initiate bank transfer to employee
    PAY-->>FMS: Transfer confirmed
    FMS->>FMS: Post GL expense and cash entries
    FMS->>EMP: Email/push: Reimbursement of {amount} deposited
```

---

## Payroll Run Processing

```mermaid
sequenceDiagram
    participant ACC as Accountant
    participant FMS as Finance Management System
    participant HR as HR System
    participant FM as Finance Manager
    participant BANK as Banking System
    participant EMP as Employee (Push)

    ACC->>FMS: POST /api/v1/payroll/runs (period, pay_group)
    FMS->>HR: GET employee profiles and timesheets
    HR-->>FMS: Employee data
    FMS->>FMS: Run pre-validation (missing data, blocked employees)
    FMS-->>ACC: Validation report { errors[], warnings[] }

    ACC->>FMS: POST /api/v1/payroll/runs/{id}/calculate
    FMS->>FMS: Calculate gross pay per employee
    FMS->>FMS: Apply statutory and voluntary deductions
    FMS->>FMS: Compute net pay
    FMS-->>ACC: Payroll register { employees[], totals{} }

    ACC->>FMS: POST /api/v1/payroll/runs/{id}/submit
    FMS->>FM: Notify: Payroll run ready for approval

    FM->>FMS: POST /api/v1/payroll/runs/{id}/approve
    FMS->>BANK: Submit direct deposit file
    BANK-->>FMS: Accepted
    FMS->>FMS: Post payroll GL entries
    FMS->>EMP: Send digital pay stubs
    FMS-->>FM: 200 { status: DISBURSED, employee_count }
```

---

## Budget Variance Alert

```mermaid
sequenceDiagram
    participant GL as GL Posting Engine
    participant FMS as Finance Management System
    participant DB as Database
    participant BM as Budget Manager
    participant DH as Department Head

    GL->>FMS: Transaction posted to cost center account
    FMS->>DB: Fetch approved budget for cost center + account + period
    DB-->>FMS: Budget amount and actuals YTD
    FMS->>FMS: Calculate utilization %

    alt Utilization >= 80%
        FMS->>BM: Push/email: Budget 80% utilized for {account}
        FMS->>DH: Push/email: Department budget 80% utilized
    end

    alt Utilization >= 95%
        FMS->>BM: Push/email: ALERT - Budget 95% utilized for {account}
        FMS->>DH: Push/email: ALERT - Department nearing budget limit
        FMS->>FM: Alert: Cost center {x} at 95% of budget
    end

    alt Utilization > 100%
        FMS->>BM: Push/email: CRITICAL - Budget exceeded for {account}
        FMS->>FM: Alert: Budget breach - requires CFO review
    end
```

---

## Period Close Sequence

```mermaid
sequenceDiagram
    participant FM as Finance Manager
    participant FMS as Finance Management System
    participant ACC as Accountant
    participant CFO as CFO
    participant ARCHIVE as Archive Storage

    FM->>FMS: POST /api/v1/periods/{id}/initiate-close
    FMS->>FMS: Generate period-close checklist
    FMS->>ACC: Notify: Period close checklist items assigned

    ACC->>FMS: POST /api/v1/periods/{id}/checklist/{item}/complete (subledger reconciliation)
    ACC->>FMS: POST /api/v1/periods/{id}/accruals (accrual entries)
    ACC->>FMS: POST /api/v1/periods/{id}/depreciation/post

    FMS->>FMS: Run trial balance
    FMS-->>ACC: Trial balance report

    ACC->>FMS: POST /api/v1/periods/{id}/checklist/sign-off
    FMS->>FM: Notify: Accountant sign-off complete

    FM->>FMS: GET /api/v1/reports/financial-statements?period={id}
    FMS-->>FM: Draft P&L, Balance Sheet, Cash Flow

    FM->>FMS: POST /api/v1/periods/{id}/soft-close
    FMS->>CFO: Notify: Period ready for final sign-off

    CFO->>FMS: GET /api/v1/reports/financial-statements?period={id}
    CFO->>FMS: POST /api/v1/periods/{id}/approve

    FM->>FMS: POST /api/v1/periods/{id}/hard-close
    FMS->>FMS: Lock period from any further postings
    FMS->>ARCHIVE: Archive period records
    FMS-->>FM: 200 { status: CLOSED }
```
