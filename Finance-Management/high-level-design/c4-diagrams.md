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
