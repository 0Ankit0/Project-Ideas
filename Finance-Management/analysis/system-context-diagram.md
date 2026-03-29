# System Context Diagram

## Overview
The system context below defines the Finance Management System and its interactions with internal users and external systems.

---

## Main System Context Diagram

```mermaid
graph TB
    subgraph Actors
        CFO((CFO))
        FinanceManager((Finance Manager))
        Accountant((Accountant))
        BudgetManager((Budget Manager))
        Auditor((Auditor))
        Employee((Employee))
        DeptHead((Department Head))
    end

    subgraph ExternalSystems
        Bank[Banking Systems<br>ACH / SWIFT / NEFT]
        Tax[Tax Authorities<br>IRS / GSTN / HMRC]
        ERP[ERP / HR Systems<br>SAP / Oracle / Workday]
        ExchangeRate[FX Rate Providers<br>Open Exchange / Bloomberg]
        Email[Email Service]
        Push[Push Notifications]
        Storage[Document Storage]
        Audit[External Audit Systems]
        Payment[Payment Processors<br>Stripe / Plaid]
    end

    subgraph "Finance Management System"
        Platform[FastAPI Monolith]
    end

    CFO -->|approve budgets, view dashboards, strategic reporting| Platform
    FinanceManager -->|period close, payment runs, payroll approval| Platform
    Accountant -->|journal entries, AP/AR, reconciliation| Platform
    BudgetManager -->|budget creation, variance tracking| Platform
    Auditor -->|read-only audit access, compliance reports| Platform
    Employee -->|expense submission, reimbursement tracking| Platform
    DeptHead -->|expense approvals, budget monitoring| Platform

    Platform -->|ACH/wire payments, direct deposit| Bank
    Platform -->|tax filings, e-payment remittances| Tax
    Platform <-->|employee data, HR sync, GL export| ERP
    Platform -->|daily FX rate feeds| ExchangeRate
    Platform -->|approval emails, remittance advices| Email
    Platform -->|budget alerts, approval notifications| Push
    Platform -->|financial documents, invoices, reports| Storage
    Platform -->|read-only audit log export| Audit
    Platform -->|corporate card feeds, bank transactions| Payment
```

---

## Detailed Context With Data Flows

```mermaid
graph LR
    subgraph Clients
        Web[Web Application]
        MobileApp[Mobile App]
        AdminUI[Admin Dashboard]
    end

    subgraph Platform
        API[REST API]
        WS[Websocket Manager]
        Worker[Async Worker]
    end

    subgraph Banking
        ACH[ACH Network]
        SWIFT[SWIFT / Wire]
        BankFeed[Bank Statement Feed]
    end

    subgraph Compliance
        TaxPortal[Tax Filing Portal]
        AuditLog[Immutable Audit Log]
    end

    subgraph Integrations
        ERP[ERP / HR]
        FXProvider[FX Rate Feed]
        DocStore[Document Storage]
        Notify[Email / SMS / Push]
    end

    Web --> API
    MobileApp --> API
    AdminUI --> API

    API --> WS
    API --> Worker
    API --> ACH
    API --> SWIFT
    API --> BankFeed
    API --> TaxPortal
    API --> AuditLog
    API --> ERP
    API --> FXProvider
    API --> DocStore
    API --> Notify
```

---

## Security Boundaries

```mermaid
graph TB
    subgraph "Public Zone"
        Internet[Internet]
        CDN[CDN]
    end

    subgraph "Edge Zone"
        WAF[Web Application Firewall]
        LB[Load Balancer]
    end

    subgraph "Application Zone"
        API[FastAPI Application]
        Redis[Redis Cache]
        Worker[Async Task Worker]
        WS[Websocket Manager]
    end

    subgraph "Data Zone"
        DB[(Primary Database<br>Encrypted at Rest)]
        Storage[(Document Storage<br>AES-256)]
        AuditDB[(Immutable Audit Store)]
    end

    subgraph "External Services"
        Bank[Banking Networks]
        Tax[Tax Authorities]
        Notify[Email / SMS / Push]
        ERP[HR / ERP Systems]
    end

    Internet --> CDN
    CDN --> WAF
    WAF --> LB
    LB --> API
    API --> Redis
    API --> Worker
    API --> WS
    API --> DB
    API --> Storage
    API --> AuditDB
    API -- mTLS --> Bank
    API -- TLS --> Tax
    API -- TLS --> Notify
    API -- TLS --> ERP
```

---

## External Dependency Notes

| System | Purpose | Integration Type |
|--------|---------|-----------------|
| Banking systems | ACH payments, wire transfers, bank statement import | Direct API / file-based SFTP |
| Tax authorities | E-filing of tax returns, payment remittance | Government API / portal upload |
| ERP / HR systems | Employee master data, purchase order sync | REST API / scheduled sync |
| FX rate providers | Daily exchange rate feeds for multi-currency | REST API polling |
| Email / Push | Approval notifications, remittance advices | Managed notification service |
| Document storage | Invoices, receipts, reports, audit artifacts | Object storage API |
| External audit systems | Read-only audit log export for external auditors | Encrypted file export |
| Payment processors | Corporate card feeds, ACH initiation | REST API / bank feed |

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
- Maintain an explicit traceability matrix for this artifact (`analysis/system-context-diagram.md`):
  - `Requirement ID` → `Business Rule / Event` → `Design Element` (API/schema/diagram component) → `Code Module` → `Test Evidence` → `Control Owner`.
- Lineage metadata minimums: source event ID, transformation ID/version, posting rule version, reconciliation batch ID, and report consumption path.
- Any change touching accounting semantics must include impact analysis across upstream requirements and downstream close/compliance reports.
- Documentation updates are blocking for release when they alter financial behavior, posting logic, or reconciliation outcomes.

### 7) Phase-Specific Implementation Readiness
- Convert business requirements into executable decision tables with explicit preconditions, data dependencies, and exception states.
- Map each business event to accounting impact (`none`, `memo`, `sub-ledger`, `GL-posting`) and expected latency/SLA.
- Document escalation paths for unresolved breaks, including RACI and aging thresholds.

### 8) Implementation Checklist for `system context diagram`
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


