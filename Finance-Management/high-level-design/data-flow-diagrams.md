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
