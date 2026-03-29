# C4 Diagrams

## Overview
C4 model diagrams for the Finance Management System at Context, Container, and Component levels.

---

## Level 1: System Context Diagram

```mermaid
graph TB
    subgraph "Finance Users"
        CFO((CFO))
        FM((Finance Manager))
        ACC((Accountant))
        EMP((Employee))
        AUD((Auditor))
    end

    FMS["Finance Management System\n[Software System]\nManages all financial operations,\nreporting, compliance, and controls\nfor an organization"]

    subgraph "External Systems"
        BANK["Banking System\n[External System]\nACH, SWIFT, bank feeds"]
        TAX["Tax Authorities\n[External System]\nE-filing, acknowledgments"]
        ERP["HR / ERP System\n[External System]\nEmployee data, purchase orders"]
        FX["FX Rate Provider\n[External System]\nDaily exchange rates"]
        MSG["Messaging Service\n[External System]\nEmail, SMS, push notifications"]
    end

    CFO -->|"Approves budgets, reviews financials"| FMS
    FM -->|"Manages operations, approves payments"| FMS
    ACC -->|"Records transactions, reconciles"| FMS
    EMP -->|"Submits expenses, views pay stubs"| FMS
    AUD -->|"Read-only audit access"| FMS

    FMS -->|"Payment files, ACH transfers"| BANK
    BANK -->|"Bank statements, clearance confirmations"| FMS
    FMS -->|"Tax returns, remittances"| TAX
    TAX -->|"Filing acknowledgments"| FMS
    ERP -->|"Employee data, purchase orders"| FMS
    FMS -->|"GL export, payroll data"| ERP
    FX -->|"Daily exchange rates"| FMS
    FMS -->|"Approval alerts, notifications"| MSG
```

---

## Level 2: Container Diagram

```mermaid
graph TB
    subgraph "Finance Users"
        WebUser[Web Browser]
        MobileUser[Mobile App]
    end

    subgraph "Finance Management System"
        WebApp["Web Application\n[Next.js]\nFinance portal UI for all roles"]
        MobileApp["Mobile App\n[Flutter]\nExpense submission and approvals"]

        API["API Application\n[FastAPI / Python]\nAll business logic, validations,\nworkflow processing"]

        Worker["Background Worker\n[Celery / asyncio]\nAsync processing: report generation,\npayroll, bank file submission"]

        WS["Websocket Server\n[FastAPI WS]\nReal-time budget alerts,\nnotification fanout"]

        DB["Primary Database\n[PostgreSQL]\nAll transactional data,\nencrypted at rest"]

        AuditDB["Audit Store\n[PostgreSQL - Append Only]\nImmutable audit trail for all\nfinancial record changes"]

        Cache["Cache\n[Redis]\nSession tokens, FX rates,\nhot report cache"]

        Storage["Document Storage\n[S3-compatible]\nInvoices, receipts, reports,\npay stubs, bank files"]
    end

    subgraph "External Systems"
        Bank[Banking System]
        Tax[Tax Authorities]
        ERP[HR / ERP]
        FX[FX Rate Feed]
        Notify[Email / SMS / Push]
    end

    WebUser --> WebApp
    MobileUser --> MobileApp
    WebApp --> API
    MobileApp --> API
    API --> DB
    API --> AuditDB
    API --> Cache
    API --> Storage
    API --> Worker
    API --> WS
    Worker --> DB
    Worker --> Bank
    Worker --> Tax
    Worker --> Notify
    API --> FX
    API --> ERP
```

---

## Level 3: Component Diagram — Core Finance Components

```mermaid
graph TB
    subgraph "API Application"
        subgraph "Identity & Access"
            AuthRouter[Auth Router]
            RBACService[RBAC Service]
            AuditService[Audit Log Service]
        end

        subgraph "General Ledger"
            GLRouter[GL Router]
            JournalService[Journal Entry Service]
            PeriodService[Period Management Service]
            ReconcileService[Reconciliation Service]
            TrialBalanceService[Trial Balance Service]
        end

        subgraph "AP/AR"
            APRouter[AP Router]
            ARRouter[AR Router]
            InvoiceService[Invoice Service]
            MatchingService[3-Way Matching Service]
            PaymentRunService[Payment Run Service]
            CollectionService[AR Collection Service]
        end

        subgraph "Planning & Workforce"
            BudgetRouter[Budget Router]
            BudgetService[Budget Service]
            VarianceService[Variance Tracking Service]
            ExpenseRouter[Expense Router]
            ExpenseService[Expense Approval Service]
            PayrollRouter[Payroll Router]
            PayrollService[Payroll Processing Service]
        end

        subgraph "Assets & Tax"
            FARouter[Fixed Asset Router]
            DepreciationService[Depreciation Engine]
            TaxRouter[Tax Router]
            TaxCalcService[Tax Calculation Service]
            FilingService[Tax Filing Service]
        end

        subgraph "Reporting"
            ReportRouter[Report Router]
            FinancialStmtService[Financial Statement Service]
            ConsolidationService[Consolidation Service]
            ReportJobService[Async Report Job Service]
        end

        subgraph "Notifications"
            NotifyDispatcher[Notification Dispatcher]
            AlertEngine[Budget Alert Engine]
            WSFanout[WebSocket Fanout]
        end
    end

    GLRouter --> JournalService
    GLRouter --> PeriodService
    GLRouter --> ReconcileService
    GLRouter --> TrialBalanceService

    APRouter --> InvoiceService
    APRouter --> MatchingService
    APRouter --> PaymentRunService

    ARRouter --> InvoiceService
    ARRouter --> CollectionService

    BudgetRouter --> BudgetService
    BudgetRouter --> VarianceService

    ExpenseRouter --> ExpenseService
    PayrollRouter --> PayrollService

    FARouter --> DepreciationService
    TaxRouter --> TaxCalcService
    TaxRouter --> FilingService

    ReportRouter --> FinancialStmtService
    ReportRouter --> ConsolidationService
    ReportRouter --> ReportJobService

    JournalService --> AuditService
    PaymentRunService --> AuditService
    PayrollService --> AuditService
    VarianceService --> AlertEngine
    AlertEngine --> NotifyDispatcher
    NotifyDispatcher --> WSFanout
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
- Maintain an explicit traceability matrix for this artifact (`high-level-design/c4-diagrams.md`):
  - `Requirement ID` → `Business Rule / Event` → `Design Element` (API/schema/diagram component) → `Code Module` → `Test Evidence` → `Control Owner`.
- Lineage metadata minimums: source event ID, transformation ID/version, posting rule version, reconciliation batch ID, and report consumption path.
- Any change touching accounting semantics must include impact analysis across upstream requirements and downstream close/compliance reports.
- Documentation updates are blocking for release when they alter financial behavior, posting logic, or reconciliation outcomes.

### 7) Phase-Specific Implementation Readiness
- Define bounded contexts for Ledger, AP, AR, Treasury, Tax, Payroll, and Reporting with explicit ownership boundaries.
- Specify asynchronous vs synchronous paths and where consistency is strong, eventual, or externally constrained.
- Declare resilience posture for each integration (retry, DLQ, replay, compensating entry, manual hold).

### 8) Implementation Checklist for `c4 diagrams`
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


