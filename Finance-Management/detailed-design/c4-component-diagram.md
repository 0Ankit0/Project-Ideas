# C4 Component Diagram

## Overview
C4 Level 3 component diagrams showing the internal structure of the Finance Management System's major containers.

---

## GL and Transaction Processing Components

```mermaid
graph TB
    subgraph "API Application — GL & Transactions"
        subgraph "GL Module"
            GLRouter["GL Router\n[FastAPI Router]\nHandles HTTP for journal entries,\nCoA, trial balance, periods"]
            JES["JournalEntryService\n[Service]\nValidation, posting, reversals,\nrecurring entry management"]
            PES["PeriodService\n[Service]\nPeriod lifecycle, close checklist,\nsoft/hard close enforcement"]
            CAS["ChartOfAccountsService\n[Service]\nAccount CRUD, hierarchy,\ntype validation"]
            RS["ReconciliationService\n[Service]\nBank statement import,\nauto-match, unmatched flagging"]
            TBS["TrialBalanceService\n[Service]\nReal-time trial balance,\naccount balance queries"]
            GLRepo["GL Repository\n[Repository]\nJournal entry and account\npersistence"]
        end

        subgraph "AP Module"
            APRouter["AP Router\n[FastAPI Router]\nVendor invoices, payment runs,\nAP aging"]
            InvSvc["InvoiceService\n[Service]\nInvoice CRUD, duplicate check,\napproval workflow routing"]
            MtchSvc["MatchingService\n[Service]\n2-way and 3-way PO/receipt matching,\nvariance tolerance check"]
            PayRunSvc["PaymentRunService\n[Service]\nBatch payment scheduling,\nbank file generation, clearance"]
        end

        subgraph "AR Module"
            ARRouter["AR Router\n[FastAPI Router]\nCustomer invoices, payment collection,\nAR aging"]
            CustInvSvc["CustomerInvoiceService\n[Service]\nInvoice creation, PDF generation,\nauto-reminders"]
            PayAllocSvc["PaymentAllocationService\n[Service]\nFIFO or manual payment-to-invoice allocation"]
            CollectSvc["CollectionService\n[Service]\nOverdue tracking, escalation workflow,\nbad debt write-off"]
        end

        GLRouter --> JES
        GLRouter --> PES
        GLRouter --> CAS
        GLRouter --> RS
        GLRouter --> TBS
        JES --> GLRepo
        PES --> GLRepo
        CAS --> GLRepo
        RS --> GLRepo
        TBS --> GLRepo

        APRouter --> InvSvc
        APRouter --> MtchSvc
        APRouter --> PayRunSvc
        InvSvc --> GLRepo

        ARRouter --> CustInvSvc
        ARRouter --> PayAllocSvc
        ARRouter --> CollectSvc
        CustInvSvc --> GLRepo
    end
```

---

## Planning and Workforce Components

```mermaid
graph TB
    subgraph "API Application — Planning & Workforce"
        subgraph "Budgeting Module"
            BudgetRouter["Budget Router\n[FastAPI Router]\nBudget CRUD, approval actions,\nvariance and forecast endpoints"]
            BudgetSvc["BudgetService\n[Service]\nBudget creation, version control,\napproval workflow"]
            VarSvc["VarianceTrackingService\n[Service]\nActuals vs budget calculation,\nutilization percentage"]
            ForecastSvc["ForecastingService\n[Service]\nRolling forecast based on actuals\nrun rate and adjustments"]
            AlertEng["AlertEngine\n[Service]\nThreshold evaluation (80%, 95%, 100%),\nalert dispatch"]
        end

        subgraph "Expense Module"
            ExpenseRouter["Expense Router\n[FastAPI Router]\nClaim submission, approval actions,\npolicy lookup"]
            ExpenseSvc["ExpenseApprovalService\n[Service]\nPolicy check, multi-level approval,\nreimbursement queuing"]
            CardSvc["CorporateCardService\n[Service]\nCard transaction import,\nclaim matching"]
        end

        subgraph "Payroll Module"
            PayrollRouter["Payroll Router\n[FastAPI Router]\nRun management, register,\ndisburse, pay stubs"]
            PayrollSvc["PayrollService\n[Service]\nCalculation orchestration,\napproval, bank file"]
            DedEng["DeductionEngine\n[Service]\nTax, SS, PF, voluntary deductions,\nnet pay computation"]
            PayStubSvc["PayStubService\n[Service]\nPDF generation per employee per run"]
        end

        BudgetRouter --> BudgetSvc
        BudgetRouter --> VarSvc
        BudgetRouter --> ForecastSvc
        BudgetSvc --> AlertEng

        ExpenseRouter --> ExpenseSvc
        ExpenseRouter --> CardSvc

        PayrollRouter --> PayrollSvc
        PayrollSvc --> DedEng
        PayrollSvc --> PayStubSvc
    end
```

---

## Cross-Cutting Infrastructure Components

```mermaid
graph TB
    subgraph "API Application — Cross-Cutting"
        subgraph "Identity & Access"
            AuthRouter["Auth Router\n[FastAPI Router]\nLogin, refresh, logout, MFA"]
            JWTSvc["JWTService\n[Service]\nToken issue, verify, revoke"]
            RBACSvc["RBACService\n[Service]\nPermission check per request"]
            MFASvc["MFAService\n[Service]\nTOTP / OTP enable, verify"]
        end

        subgraph "Audit & Compliance"
            AuditSvc["AuditService\n[Service]\nAppend-only log writes,\nlog query and export"]
            CompSvc["ComplianceService\n[Service]\nSoD violation detection,\nexception report generation"]
        end

        subgraph "Workflow Engine"
            WFEngine["WorkflowEngine\n[Service]\nConfigurable multi-step approval routing,\nstep tracking, SLA monitoring"]
            ApprovalRepo["ApprovalRepository\n[Repository]\nApproval instances, steps, audit"]
        end

        subgraph "Notifications"
            NotifyDisp["NotificationDispatcher\n[Service]\nEmail, push, in-app, websocket routing"]
            WSManager["WebSocketManager\n[Service]\nReal-time broadcast per user and role"]
            AlertEngine["AlertEngine\n[Service]\nBudget threshold alerts,\nperiod-close reminders"]
        end

        subgraph "Reporting"
            ReportRouter["Report Router\n[FastAPI Router]\nStatement endpoints, async job management"]
            FinStmtSvc["FinancialStatementService\n[Service]\nP&L, Balance Sheet, Cash Flow generation"]
            ConsolSvc["ConsolidationService\n[Service]\nMulti-entity consolidation,\nintercompany eliminations"]
            ReportJobSvc["ReportJobService\n[Service]\nAsync job queuing, status polling,\nartifact storage"]
        end

        AuthRouter --> JWTSvc
        AuthRouter --> MFASvc
        JWTSvc --> RBACSvc

        WFEngine --> ApprovalRepo
        WFEngine --> NotifyDisp
        NotifyDisp --> WSManager

        ReportRouter --> FinStmtSvc
        ReportRouter --> ConsolSvc
        ReportRouter --> ReportJobSvc
        ConsolSvc --> FinStmtSvc
    end
```
