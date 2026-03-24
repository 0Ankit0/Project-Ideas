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
