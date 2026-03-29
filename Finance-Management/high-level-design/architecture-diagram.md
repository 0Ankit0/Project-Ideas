# High-Level Architecture Diagram

## Overview
This document describes the high-level architecture of the Finance Management System as a FastAPI monolith with domain modules, shared persistence, async workflow processing, and external banking/tax/ERP integrations.

---

## System Architecture Overview

```mermaid
graph TB
    subgraph "Clients"
        WebApp[Finance Web App]
        MobileApp[Mobile App]
        AdminApp[Admin Dashboard]
        ApiClient[ERP / External API Client]
    end

    subgraph "Edge"
        CDN[CDN]
        WAF[WAF]
        LB[Load Balancer]
    end

    subgraph "Application"
        API[FastAPI Monolith]

        subgraph "Backend Modules"
            IAM[IAM & RBAC]
            GL[General Ledger]
            AP[Accounts Payable]
            AR[Accounts Receivable]
            BF[Budgeting & Forecasting]
            EM[Expense Management]
            PR[Payroll]
            FA[Fixed Assets]
            TM[Tax Management]
            RPT[Reporting & Analytics]
            Notify[Notifications & Alerts]
        end
    end

    subgraph "Data"
        DB[(PostgreSQL<br>Encrypted at Rest)]
        Redis[(Redis<br>Cache & Sessions)]
        AuditDB[(Immutable Audit Log)]
        Storage[(Document Storage)]
    end

    subgraph "External Services"
        Bank[Banking Systems<br>ACH / SWIFT / NEFT]
        TaxPortal[Tax Authorities<br>GSTN / IRS / HMRC]
        ERPSystem[HR / ERP System]
        FXFeed[FX Rate Feed]
        Messaging[Email / SMS / Push]
    end

    WebApp --> CDN
    MobileApp --> CDN
    AdminApp --> CDN
    ApiClient --> LB

    CDN --> WAF
    WAF --> LB
    LB --> API

    API --> IAM
    API --> GL
    API --> AP
    API --> AR
    API --> BF
    API --> EM
    API --> PR
    API --> FA
    API --> TM
    API --> RPT
    API --> Notify

    GL --> DB
    AP --> DB
    AR --> DB
    BF --> DB
    EM --> DB
    PR --> DB
    FA --> DB
    TM --> DB
    RPT --> DB
    IAM --> DB

    IAM --> Redis
    GL --> Redis
    BF --> Redis
    RPT --> Redis

    GL --> AuditDB
    AP --> AuditDB
    AR --> AuditDB
    PR --> AuditDB

    AP --> Storage
    AR --> Storage
    EM --> Storage
    RPT --> Storage

    AP --> Bank
    PR --> Bank
    AR --> Bank
    TM --> TaxPortal
    IAM --> ERPSystem
    PR --> ERPSystem
    GL --> FXFeed
    Notify --> Messaging
```

---

## Runtime Interaction Model

```mermaid
graph LR
    Client[Client Request] --> API[FastAPI Router]
    API --> Domain[Domain Service / Repository]
    Domain --> DB[(PostgreSQL)]
    Domain --> Redis[(Redis)]

    Domain --> Event[Domain Event / Workflow Task]
    Event --> Worker[Async Worker]
    Worker --> Notify[Notification Dispatcher]
    Worker --> BankAPI[Banking API]
    Worker --> TaxAPI[Tax Filing API]

    Notify --> Email[Email / SMS / Push]
```

---

## Key Backend Responsibilities

| Module | Main Responsibilities |
|--------|-----------------------|
| IAM | JWT auth, RBAC, MFA, audit logging, ERP employee sync |
| General Ledger | Journal entries, CoA management, trial balance, bank reconciliation, period management |
| Accounts Payable | Vendor master, invoice recording, 3-way match, payment runs, AP aging |
| Accounts Receivable | Customer master, invoicing, payment collection, AR aging, collections |
| Budgeting & Forecasting | Budget creation, approval workflows, variance tracking, rolling forecasts, alerts |
| Expense Management | Expense submission, approval workflows, corporate card reconciliation, reimbursements |
| Payroll | Payroll run processing, statutory deductions, pay stubs, bank file generation, tax remittance |
| Fixed Assets | Asset registration, depreciation scheduling, asset lifecycle, disposal |
| Tax Management | Tax configuration, auto-calculation, e-filing, TDS/WHT management |
| Reporting & Analytics | Financial statements, management reports, consolidation, custom report builder |
| Notifications | Approval alerts, budget threshold notifications, payment confirmations, period-close reminders |

---

## Current Architectural Constraints

- The system is designed as a single FastAPI monolith to reduce operational complexity during initial deployment.
- The audit log module writes to an append-only store to prevent tampering.
- All financial calculations (tax, depreciation, payroll deductions) are performed server-side.
- FX rate feeds are polled daily and cached in Redis for intra-day use.
- External bank file submission is handled asynchronously via background workers to avoid blocking API responses.
- Report generation for large datasets is queued as background jobs with status polling and email delivery.

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
- Maintain an explicit traceability matrix for this artifact (`high-level-design/architecture-diagram.md`):
  - `Requirement ID` → `Business Rule / Event` → `Design Element` (API/schema/diagram component) → `Code Module` → `Test Evidence` → `Control Owner`.
- Lineage metadata minimums: source event ID, transformation ID/version, posting rule version, reconciliation batch ID, and report consumption path.
- Any change touching accounting semantics must include impact analysis across upstream requirements and downstream close/compliance reports.
- Documentation updates are blocking for release when they alter financial behavior, posting logic, or reconciliation outcomes.

### 7) Phase-Specific Implementation Readiness
- Define bounded contexts for Ledger, AP, AR, Treasury, Tax, Payroll, and Reporting with explicit ownership boundaries.
- Specify asynchronous vs synchronous paths and where consistency is strong, eventual, or externally constrained.
- Declare resilience posture for each integration (retry, DLQ, replay, compensating entry, manual hold).

### 8) Implementation Checklist for `architecture diagram`
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


