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
