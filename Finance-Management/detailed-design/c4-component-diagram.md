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
- Maintain an explicit traceability matrix for this artifact (`detailed-design/c4-component-diagram.md`):
  - `Requirement ID` → `Business Rule / Event` → `Design Element` (API/schema/diagram component) → `Code Module` → `Test Evidence` → `Control Owner`.
- Lineage metadata minimums: source event ID, transformation ID/version, posting rule version, reconciliation batch ID, and report consumption path.
- Any change touching accounting semantics must include impact analysis across upstream requirements and downstream close/compliance reports.
- Documentation updates are blocking for release when they alter financial behavior, posting logic, or reconciliation outcomes.

### 7) Phase-Specific Implementation Readiness
- Specify schema-level constraints: unique idempotency keys, check constraints for debit/credit signs, immutable posting rows, FK coverage.
- Define API contracts for posting/approval/reconciliation including error codes, retry semantics, and deterministic conflict handling.
- Include state-transition guards for approval and period-close flows to prevent illegal transitions.

### 8) Implementation Checklist for `c4 component diagram`
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


