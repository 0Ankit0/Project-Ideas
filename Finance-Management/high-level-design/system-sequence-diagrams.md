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
- Maintain an explicit traceability matrix for this artifact (`high-level-design/system-sequence-diagrams.md`):
  - `Requirement ID` → `Business Rule / Event` → `Design Element` (API/schema/diagram component) → `Code Module` → `Test Evidence` → `Control Owner`.
- Lineage metadata minimums: source event ID, transformation ID/version, posting rule version, reconciliation batch ID, and report consumption path.
- Any change touching accounting semantics must include impact analysis across upstream requirements and downstream close/compliance reports.
- Documentation updates are blocking for release when they alter financial behavior, posting logic, or reconciliation outcomes.

### 7) Phase-Specific Implementation Readiness
- Define bounded contexts for Ledger, AP, AR, Treasury, Tax, Payroll, and Reporting with explicit ownership boundaries.
- Specify asynchronous vs synchronous paths and where consistency is strong, eventual, or externally constrained.
- Declare resilience posture for each integration (retry, DLQ, replay, compensating entry, manual hold).

### 8) Implementation Checklist for `system sequence diagrams`
- [ ] Control objectives and success/failure criteria are explicit and testable.
- [ ] Data contracts include mandatory identifiers, timestamps, and provenance fields.
- [ ] Reconciliation logic defines cadence, tolerances, ownership, and escalation.
- [ ] Operational runbooks cover retries, replay, backfill, and close re-certification.
- [ ] Compliance evidence artifacts are named, retained, and linked to control owners.


### Mermaid Control Overlay (Implementation-Ready)
```mermaid
flowchart LR
    Req[Requirements Controls] --> Rules[Posting/Tax/Approval Rules]
    Rules --> Events[Domain Events with Idempotency Keys]
    Events --> Ledger[Immutable Ledger Entries]
    Ledger --> Recon[Automated Reconciliation Jobs]
    Recon --> Close[Period Close & Certification]
    Close --> Reports[Regulatory + Management Reports]
    Reports --> Audit[Evidence Store / Audit Trail]
    Audit -->|Feedback| Req
```


