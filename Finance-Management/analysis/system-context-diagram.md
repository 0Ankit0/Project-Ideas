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
