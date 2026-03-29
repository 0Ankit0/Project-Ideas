# Component Diagrams

## Overview
Component-level architecture diagrams showing how the Finance Management System is structured internally.

---

## System Component Overview

```mermaid
graph TB
    subgraph "Client Layer"
        WebApp[Finance Web App<br>Next.js]
        MobileApp[Mobile App<br>Flutter]
        AdminDash[Admin Dashboard<br>Next.js]
    end

    subgraph "API Layer"
        APIGateway[FastAPI Application<br>REST API + WebSocket]
    end

    subgraph "Core Finance Components"
        GLComp[General Ledger<br>Component]
        APComp[Accounts Payable<br>Component]
        ARComp[Accounts Receivable<br>Component]
        BFComp[Budgeting & Forecasting<br>Component]
        EMComp[Expense Management<br>Component]
        PRComp[Payroll<br>Component]
        FAComp[Fixed Assets<br>Component]
        TMComp[Tax Management<br>Component]
    end

    subgraph "Cross-Cutting Components"
        IAMComp[Identity & Access<br>Component]
        NotifyComp[Notifications<br>Component]
        ReportComp[Reporting & Analytics<br>Component]
        AuditComp[Audit & Compliance<br>Component]
        WorkflowComp[Workflow Engine<br>Component]
    end

    subgraph "Infrastructure Components"
        DB[(PostgreSQL)]
        Redis[(Redis)]
        Storage[(Document Storage)]
        AuditStore[(Immutable Audit Store)]
        Worker[Background Worker<br>Celery]
    end

    WebApp --> APIGateway
    MobileApp --> APIGateway
    AdminDash --> APIGateway

    APIGateway --> GLComp
    APIGateway --> APComp
    APIGateway --> ARComp
    APIGateway --> BFComp
    APIGateway --> EMComp
    APIGateway --> PRComp
    APIGateway --> FAComp
    APIGateway --> TMComp
    APIGateway --> IAMComp
    APIGateway --> ReportComp

    GLComp --> AuditComp
    APComp --> WorkflowComp
    ARComp --> WorkflowComp
    EMComp --> WorkflowComp
    PRComp --> WorkflowComp
    BFComp --> WorkflowComp

    WorkflowComp --> NotifyComp

    GLComp --> DB
    APComp --> DB
    ARComp --> DB
    BFComp --> DB
    EMComp --> DB
    PRComp --> DB
    FAComp --> DB
    TMComp --> DB
    AuditComp --> AuditStore
    ReportComp --> DB
    ReportComp --> Redis
    IAMComp --> Redis
    NotifyComp --> Worker
    ReportComp --> Worker
    PRComp --> Worker
    APComp --> Worker
    EMComp --> Storage
    APComp --> Storage
    ARComp --> Storage
    PRComp --> Storage
    ReportComp --> Storage
```

---

## Identity & Access Component

```mermaid
graph LR
    subgraph "IAM Component"
        AuthRouter[Auth Router]
        JWTService[JWT Token Service]
        RBACService[RBAC Service]
        MFAService[MFA / OTP Service]
        SessionStore[Session Store<br>Redis]
        PermissionMatrix[Permission Matrix<br>DB]
    end

    subgraph "External"
        ERPSync[HR / ERP Employee Sync]
    end

    AuthRouter --> JWTService
    AuthRouter --> MFAService
    JWTService --> SessionStore
    RBACService --> PermissionMatrix
    AuthRouter --> RBACService
    AuthRouter --> ERPSync
```

---

## General Ledger Component

```mermaid
graph LR
    subgraph "GL Component"
        GLRouter[GL Router]
        JournalService[Journal Entry Service]
        PeriodService[Period Service]
        CoAService[Chart of Accounts Service]
        ReconcileService[Reconciliation Service]
        TrialBalanceService[Trial Balance Service]
        BankFeedImporter[Bank Statement Importer]
        GLRepo[GL Repository]
    end

    subgraph "Supporting Services"
        FXService[FX Rate Service]
        AuditSvc[Audit Service]
        NotifySvc[Notification Service]
    end

    GLRouter --> JournalService
    GLRouter --> PeriodService
    GLRouter --> CoAService
    GLRouter --> ReconcileService
    GLRouter --> TrialBalanceService

    JournalService --> GLRepo
    PeriodService --> GLRepo
    CoAService --> GLRepo
    ReconcileService --> BankFeedImporter
    ReconcileService --> GLRepo

    JournalService --> FXService
    JournalService --> AuditSvc
    PeriodService --> NotifySvc
```

---

## Budgeting & Variance Component

```mermaid
graph LR
    subgraph "Budgeting Component"
        BudgetRouter[Budget Router]
        BudgetService[Budget CRUD Service]
        ApprovalWorkflow[Approval Workflow Service]
        VarianceService[Variance Tracking Service]
        ForecastService[Forecasting Service]
        AlertEngine[Budget Alert Engine]
        BudgetRepo[Budget Repository]
    end

    subgraph "External Triggers"
        GLPostEvent[GL Posting Event]
    end

    subgraph "Notifications"
        NotifySvc[Notification Service]
        WSManager[WebSocket Manager]
    end

    BudgetRouter --> BudgetService
    BudgetRouter --> VarianceService
    BudgetRouter --> ForecastService

    BudgetService --> ApprovalWorkflow
    BudgetService --> BudgetRepo

    GLPostEvent --> VarianceService
    VarianceService --> AlertEngine
    AlertEngine --> NotifySvc
    NotifySvc --> WSManager

    ApprovalWorkflow --> NotifySvc
    VarianceService --> BudgetRepo
```

---

## Reporting & Analytics Component

```mermaid
graph LR
    subgraph "Reporting Component"
        ReportRouter[Report Router]
        FinStmtService[Financial Statement Service]
        ConsolidationService[Consolidation Service]
        CustomReportService[Custom Report Builder]
        ReportJobService[Async Job Service]
        ReportCache[Report Cache<br>Redis]
        ReportStorage[Report Artifact Storage]
    end

    subgraph "Data Sources"
        GLData[(GL Transactions)]
        BudgetData[(Budget Records)]
        APData[(AP / AR Records)]
    end

    subgraph "Background Worker"
        Worker[Celery Worker]
    end

    ReportRouter --> FinStmtService
    ReportRouter --> ConsolidationService
    ReportRouter --> CustomReportService
    ReportRouter --> ReportJobService

    FinStmtService --> GLData
    ConsolidationService --> GLData
    CustomReportService --> GLData
    CustomReportService --> BudgetData
    CustomReportService --> APData

    FinStmtService --> ReportCache
    ReportJobService --> Worker
    Worker --> ReportStorage

    ConsolidationService --> FinStmtService
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
- Maintain an explicit traceability matrix for this artifact (`detailed-design/component-diagrams.md`):
  - `Requirement ID` → `Business Rule / Event` → `Design Element` (API/schema/diagram component) → `Code Module` → `Test Evidence` → `Control Owner`.
- Lineage metadata minimums: source event ID, transformation ID/version, posting rule version, reconciliation batch ID, and report consumption path.
- Any change touching accounting semantics must include impact analysis across upstream requirements and downstream close/compliance reports.
- Documentation updates are blocking for release when they alter financial behavior, posting logic, or reconciliation outcomes.

### 7) Phase-Specific Implementation Readiness
- Specify schema-level constraints: unique idempotency keys, check constraints for debit/credit signs, immutable posting rows, FK coverage.
- Define API contracts for posting/approval/reconciliation including error codes, retry semantics, and deterministic conflict handling.
- Include state-transition guards for approval and period-close flows to prevent illegal transitions.

### 8) Implementation Checklist for `component diagrams`
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


