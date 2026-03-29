# Data Flow Diagrams

## Overview
This document shows how data moves through the Finance Management System at different levels of abstraction.

---

## Level 0: System Context DFD

```mermaid
graph LR
    subgraph External_Actors
        Users[Finance Users<br>CFO / FM / Accountant / Employee]
        Bank[Banking System]
        Tax[Tax Authorities]
        ERP[ERP / HR System]
        FX[FX Rate Provider]
    end

    FMS[Finance Management<br>System]

    Users -->|Transactions, Approvals, Reports| FMS
    FMS -->|Dashboards, Reports, Notifications| Users
    FMS -->|Payment Files, ACH| Bank
    Bank -->|Bank Statements, Clearance Confirmations| FMS
    FMS -->|Tax Returns, Remittances| Tax
    Tax -->|Filing Acknowledgments| FMS
    ERP -->|Employee Data, Purchase Orders| FMS
    FMS -->|GL Export, Payroll Data| ERP
    FX -->|Daily Exchange Rates| FMS
```

---

## Level 1: Major Subsystem DFD

```mermaid
graph TD
    subgraph User_Inputs
        JournalInput[Journal Entry Input]
        InvoiceInput[Invoice Input]
        ExpenseInput[Expense Input]
        PayrollInput[Payroll Setup]
        BudgetInput[Budget Input]
    end

    subgraph Processing_Modules
        GL[General Ledger Module]
        AP[Accounts Payable Module]
        AR[Accounts Receivable Module]
        BF[Budgeting & Forecasting Module]
        EM[Expense Module]
        PR[Payroll Module]
        FA[Fixed Assets Module]
        TM[Tax Module]
        RPT[Reporting Module]
    end

    subgraph Data_Stores
        GLStore[(GL Transactions)]
        VendorStore[(Vendor Master)]
        CustomerStore[(Customer Master)]
        BudgetStore[(Budget Data)]
        PayrollStore[(Payroll Records)]
        AssetStore[(Asset Register)]
        AuditStore[(Audit Log)]
    end

    subgraph Outputs
        Payments[Payment Files]
        TaxReturns[Tax Filings]
        Reports[Financial Reports]
        Notifications[Alerts & Notifications]
        PayStubs[Pay Stubs]
    end

    JournalInput --> GL
    InvoiceInput --> AP
    InvoiceInput --> AR
    ExpenseInput --> EM
    PayrollInput --> PR
    BudgetInput --> BF

    GL --> GLStore
    AP --> VendorStore
    AP --> GLStore
    AR --> CustomerStore
    AR --> GLStore
    BF --> BudgetStore
    EM --> GLStore
    PR --> PayrollStore
    PR --> GLStore
    FA --> AssetStore
    FA --> GLStore

    GL --> AuditStore
    AP --> AuditStore
    AR --> AuditStore

    AP --> Payments
    PR --> PayStubs
    TM --> TaxReturns

    GLStore --> RPT
    BudgetStore --> RPT
    RPT --> Reports
    RPT --> Notifications
```

---

## Level 2: General Ledger Data Flow

```mermaid
graph LR
    subgraph Sources
        ManualJE[Manual Journal Entry]
        AutoJE[Auto-Generated Entry<br>AP, AR, PR, FA, EM]
        BankImport[Bank Statement Import]
    end

    subgraph GL_Processing
        Validate[Validation<br>Balanced, Open Period]
        Post[Post to Ledger]
        Reconcile[Reconciliation Engine]
    end

    subgraph GL_Storage
        JournalStore[(Journal Entries)]
        AccountBalance[(Account Balances)]
        TrialBalance[(Trial Balance Snapshot)]
    end

    subgraph Downstream
        FinancialStmts[Financial Statements]
        BudgetComparison[Budget vs Actuals]
        AuditTrail[Audit Trail]
    end

    ManualJE --> Validate
    AutoJE --> Validate
    BankImport --> Reconcile

    Validate --> Post
    Post --> JournalStore
    Post --> AccountBalance
    Reconcile --> AccountBalance

    JournalStore --> TrialBalance
    AccountBalance --> TrialBalance
    TrialBalance --> FinancialStmts
    AccountBalance --> BudgetComparison
    JournalStore --> AuditTrail
```

---

## Level 2: Accounts Payable Data Flow

```mermaid
graph LR
    subgraph Input
        VendorInvoice[Vendor Invoice]
        PurchaseOrder[Purchase Order]
        GoodsReceipt[Goods Receipt]
    end

    subgraph AP_Processing
        DupCheck[Duplicate Detection]
        ThreeWayMatch[3-Way Matching Engine]
        ApprovalWorkflow[Approval Workflow]
        PaymentScheduler[Payment Scheduler]
    end

    subgraph AP_Storage
        InvoiceStore[(Invoice Register)]
        VendorStore[(Vendor Master)]
        PaymentStore[(Payment Records)]
    end

    subgraph Output
        GLEntry[AP GL Entries]
        BankFile[Bank Payment File]
        RemittanceEmail[Remittance Advice]
        AgingReport[AP Aging Report]
    end

    VendorInvoice --> DupCheck
    DupCheck --> ThreeWayMatch
    PurchaseOrder --> ThreeWayMatch
    GoodsReceipt --> ThreeWayMatch

    ThreeWayMatch --> ApprovalWorkflow
    ApprovalWorkflow --> InvoiceStore
    InvoiceStore --> PaymentScheduler
    VendorStore --> PaymentScheduler

    PaymentScheduler --> PaymentStore
    PaymentStore --> GLEntry
    PaymentStore --> BankFile
    PaymentStore --> RemittanceEmail
    InvoiceStore --> AgingReport
```

---

## Level 2: Budgeting and Variance Tracking Data Flow

```mermaid
graph LR
    subgraph Input
        BudgetEntry[Budget Entry<br>by Cost Center and Account]
        ActualGL[Actual GL Postings]
        ForecastInput[Forecast Adjustments]
    end

    subgraph Processing
        BudgetApproval[Budget Approval Workflow]
        VarianceEngine[Variance Calculation Engine]
        ForecastEngine[Forecasting Engine]
        AlertEngine[Budget Alert Engine]
    end

    subgraph Storage
        BudgetStore[(Approved Budgets)]
        VarianceStore[(Variance Records)]
    end

    subgraph Output
        BudgetReport[Budget vs Actuals Report]
        VarianceAlert[Variance Alerts]
        Forecast[Forecast Report]
        CFODashboard[CFO Executive Dashboard]
    end

    BudgetEntry --> BudgetApproval
    BudgetApproval --> BudgetStore
    ActualGL --> VarianceEngine
    BudgetStore --> VarianceEngine
    VarianceEngine --> VarianceStore
    VarianceStore --> AlertEngine
    AlertEngine --> VarianceAlert
    VarianceStore --> BudgetReport
    ForecastInput --> ForecastEngine
    ActualGL --> ForecastEngine
    ForecastEngine --> Forecast
    BudgetReport --> CFODashboard
    Forecast --> CFODashboard
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
- Maintain an explicit traceability matrix for this artifact (`high-level-design/data-flow-diagrams.md`):
  - `Requirement ID` → `Business Rule / Event` → `Design Element` (API/schema/diagram component) → `Code Module` → `Test Evidence` → `Control Owner`.
- Lineage metadata minimums: source event ID, transformation ID/version, posting rule version, reconciliation batch ID, and report consumption path.
- Any change touching accounting semantics must include impact analysis across upstream requirements and downstream close/compliance reports.
- Documentation updates are blocking for release when they alter financial behavior, posting logic, or reconciliation outcomes.

### 7) Phase-Specific Implementation Readiness
- Define bounded contexts for Ledger, AP, AR, Treasury, Tax, Payroll, and Reporting with explicit ownership boundaries.
- Specify asynchronous vs synchronous paths and where consistency is strong, eventual, or externally constrained.
- Declare resilience posture for each integration (retry, DLQ, replay, compensating entry, manual hold).

### 8) Implementation Checklist for `data flow diagrams`
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


