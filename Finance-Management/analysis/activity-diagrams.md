# Activity Diagrams

## Overview
Activity diagrams showing the business process flows for key operations in the Finance Management System.

---

## Journal Entry Creation Flow

```mermaid
flowchart TD
    Start([Accountant opens Journal Entries]) --> NewEntry[Click New Journal Entry]
    NewEntry --> EnterHeader[Enter Date, Reference, Description]
    EnterHeader --> AddLines[Add Debit and Credit Lines]
    AddLines --> MoreLines{More Lines<br>to Add?}
    MoreLines -->|Yes| AddLines
    MoreLines -->|No| CheckBalance{Debits =<br>Credits?}

    CheckBalance -->|No| ShowImbalance[Show Imbalance Error]
    ShowImbalance --> AddLines

    CheckBalance -->|Yes| AttachDoc{Supporting<br>Document<br>Required?}
    AttachDoc -->|Yes| UploadDoc[Upload Supporting Document]
    UploadDoc --> SelectAction
    AttachDoc -->|No| SelectAction{Save or Post?}

    SelectAction -->|Save Draft| SaveDraft[Save as Draft]
    SaveDraft --> End1([Entry Saved as Draft])

    SelectAction -->|Post| CheckPeriod{Period<br>Open?}
    CheckPeriod -->|No| PeriodError[Show Period Closed Error]
    PeriodError --> EnterHeader

    CheckPeriod -->|Yes| PostEntry[Post Journal Entry]
    PostEntry --> AssignNumber[Assign Entry Number]
    AssignNumber --> UpdateGL[Update General Ledger Balances]
    UpdateGL --> LogAudit[Write Audit Log Entry]
    LogAudit --> NotifyReviewer{High-Value<br>Entry?}

    NotifyReviewer -->|Yes| AlertManager[Alert Finance Manager]
    AlertManager --> End2([Entry Posted])
    NotifyReviewer -->|No| End2
```

---

## Vendor Invoice Processing Flow

```mermaid
flowchart TD
    Start([Invoice Received from Vendor]) --> EnterInvoice[Record Invoice in System]
    EnterInvoice --> SelectVendor[Select Vendor]
    SelectVendor --> VendorActive{Vendor<br>Active?}

    VendorActive -->|No| RejectVendor[Reject - Inactive Vendor]
    RejectVendor --> End1([Invoice Rejected])

    VendorActive -->|Yes| EnterDetails[Enter Invoice Number, Date, Lines]
    EnterDetails --> DuplicateCheck{Duplicate<br>Invoice?}

    DuplicateCheck -->|Yes| ShowDuplicate[Show Duplicate Warning]
    ShowDuplicate --> ConfirmUnique{Confirm<br>Unique?}
    ConfirmUnique -->|No| End2([Stop - Duplicate])
    ConfirmUnique -->|Yes| MatchType

    DuplicateCheck -->|No| MatchType{PO Linked?}

    MatchType -->|Yes| ThreeWayMatch[Perform 3-Way Match<br>Invoice vs PO vs Receipt]
    ThreeWayMatch --> MatchResult{Match<br>Result?}
    MatchResult -->|Pass| UploadInvoice[Upload Invoice Document]
    MatchResult -->|Variance| FlagVariance[Flag Variance for Review]
    FlagVariance --> EscalateManager[Route to Finance Manager]
    EscalateManager --> ManagerDecision{Manager<br>Approves?}
    ManagerDecision -->|No| RejectInvoice[Reject Invoice]
    RejectInvoice --> NotifyVendor[Notify Vendor]
    NotifyVendor --> End3([Invoice Rejected])
    ManagerDecision -->|Yes| UploadInvoice

    MatchType -->|No| TwoWayMatch[Perform 2-Way Match<br>Invoice vs PO]
    TwoWayMatch --> UploadInvoice

    UploadInvoice --> SubmitApproval[Submit for Payment Approval]
    SubmitApproval --> AmountCheck{Amount Exceeds<br>Threshold?}

    AmountCheck -->|Yes| SeniorApproval[Route to Finance Manager]
    SeniorApproval --> FMDecision{Approved?}
    FMDecision -->|No| ReturnAccountant[Return to Accountant]
    ReturnAccountant --> End4([Invoice Returned])
    FMDecision -->|Yes| SchedulePayment

    AmountCheck -->|No| SchedulePayment[Schedule for Next Payment Run]
    SchedulePayment --> CreateAPEntry[Create AP Liability in GL]
    CreateAPEntry --> End5([Invoice Queued for Payment])
```

---

## Payment Run Processing Flow

```mermaid
flowchart TD
    Start([Finance Manager Initiates Payment Run]) --> SelectInvoices[Select Approved Invoices Due for Payment]
    SelectInvoices --> ReviewBatch[Review Payment Batch Summary]
    ReviewBatch --> CheckFunds{Sufficient<br>Funds?}

    CheckFunds -->|No| AlertLowFunds[Alert Finance Manager]
    AlertLowFunds --> AdjustBatch{Adjust<br>Batch?}
    AdjustBatch -->|Yes| SelectInvoices
    AdjustBatch -->|No| End1([Payment Run Deferred])

    CheckFunds -->|Yes| EarlyDiscount{Early Payment<br>Discounts Available?}
    EarlyDiscount -->|Yes| ApplyDiscount[Apply Early-Pay Discount to Eligible Invoices]
    ApplyDiscount --> ApproveBatch
    EarlyDiscount -->|No| ApproveBatch[Finance Manager Approves Batch]

    ApproveBatch --> GenerateBankFile[Generate ACH / Wire Transfer File]
    GenerateBankFile --> SubmitToBank[Submit File to Bank]
    SubmitToBank --> BankResponse{Bank<br>Accepted?}

    BankResponse -->|Rejected| HandleRejection[Flag Rejected Items]
    HandleRejection --> NotifyAccountant[Notify Accountant]
    NotifyAccountant --> End2([Batch Partially Failed])

    BankResponse -->|Accepted| WaitClearance[Wait for Bank Clearance]
    WaitClearance --> PaymentCleared{Payment<br>Cleared?}

    PaymentCleared -->|Yes| MarkPaid[Mark Invoices as Paid]
    MarkPaid --> PostGLEntry[Post GL Payment Entry<br>Debit: AP Liability | Credit: Cash]
    PostGLEntry --> SendRemittance[Send Remittance Advice to Vendors]
    SendRemittance --> End3([Payment Run Complete])

    PaymentCleared -->|No - Timeout| EscalateBank[Escalate to Bank]
    EscalateBank --> WaitClearance
```

---

## Budget Approval Flow

```mermaid
flowchart TD
    Start([Budget Manager Creates Budget]) --> SelectYear[Select Fiscal Year and Department]
    SelectYear --> ChooseTemplate{Use Template?}

    ChooseTemplate -->|Prior Year Actuals| LoadTemplate[Load Prior Year Actuals as Base]
    LoadTemplate --> AdjustLines[Adjust Monthly Budget Lines]
    ChooseTemplate -->|Blank| EnterLines[Enter Monthly Budget Lines from Scratch]

    AdjustLines --> ReviewTotals[Review Annual Totals]
    EnterLines --> ReviewTotals

    ReviewTotals --> AddComments[Add Budget Notes and Justifications]
    AddComments --> SubmitBudget[Submit for Review]
    SubmitBudget --> NotifyFM[Notify Finance Manager]

    NotifyFM --> FMReview[Finance Manager Reviews Budget]
    FMReview --> FMDecision{FM Decision}

    FMDecision -->|Returns with Comments| SendBackBM[Return to Budget Manager]
    SendBackBM --> BudgetManagerRevise[Budget Manager Revises]
    BudgetManagerRevise --> SubmitBudget

    FMDecision -->|Approves| NotifyCFO[Notify CFO]
    NotifyCFO --> CFOReview[CFO Reviews Budget]
    CFOReview --> CFODecision{CFO Decision}

    CFODecision -->|Rejects| RejectBudget[Return to Finance Manager with Notes]
    RejectBudget --> FMReview

    CFODecision -->|Approves| ActivateBudget[Activate Budget]
    ActivateBudget --> NotifyBudgetManagers[Notify All Budget Managers]
    NotifyBudgetManagers --> StartTracking[Begin Actuals Tracking]
    StartTracking --> End([Budget Active])
```

---

## Expense Claim Processing Flow

```mermaid
flowchart TD
    Start([Employee Submits Expense Claim]) --> EnterExpenses[Enter Expense Items and Upload Receipts]
    EnterExpenses --> PolicyCheck{Policy<br>Violations?}

    PolicyCheck -->|Yes| ShowViolations[Show Policy Violation Flags]
    ShowViolations --> AddJustification{Employee Adds<br>Justification?}
    AddJustification -->|No| CannotSubmit[Cannot Submit Without Justification]
    CannotSubmit --> End1([Claim Blocked])
    AddJustification -->|Yes| Submit

    PolicyCheck -->|No| Submit[Submit Claim]
    Submit --> NotifyDeptHead[Notify Department Head]

    NotifyDeptHead --> DeptReview[Dept Head Reviews Claim]
    DeptReview --> DeptDecision{Decision}

    DeptDecision -->|Rejects| ReturnEmployee[Return to Employee with Reason]
    ReturnEmployee --> EmployeeAction{Employee<br>Corrects?}
    EmployeeAction -->|Yes| EnterExpenses
    EmployeeAction -->|No| End2([Claim Closed])

    DeptDecision -->|Approves| AmountThreshold{Amount Exceeds<br>Threshold?}

    AmountThreshold -->|Yes| FMReview[Route to Finance Manager]
    FMReview --> FMDecision{FM Decision}
    FMDecision -->|Rejects| ReturnEmployee
    FMDecision -->|Approves| QueueReimbursement

    AmountThreshold -->|No| QueueReimbursement[Queue for Reimbursement]

    QueueReimbursement --> ReimburseMethod{Reimbursement<br>Method}

    ReimburseMethod -->|Payroll| AddToPayroll[Include in Next Payroll Run]
    AddToPayroll --> NotifyEmployee
    ReimburseMethod -->|Direct| InitiateTransfer[Initiate Bank Transfer]
    InitiateTransfer --> NotifyEmployee[Notify Employee of Payment]
    NotifyEmployee --> PostGL[Post GL Entry: Expense Debit / Cash Credit]
    PostGL --> End3([Expense Reimbursed])
```

---

## Period Close Flow

```mermaid
flowchart TD
    Start([Finance Manager Initiates Period Close]) --> OpenChecklist[Open Period-Close Checklist]
    OpenChecklist --> Subledgers[Reconcile All Subledgers<br>AP, AR, Payroll, Fixed Assets]
    Subledgers --> CheckSubs{All Subledgers<br>Reconciled?}

    CheckSubs -->|No| ResolveItems[Resolve Reconciling Items]
    ResolveItems --> Subledgers

    CheckSubs -->|Yes| PostAccruals[Post Accrual Entries]
    PostAccruals --> PostDepreciation[Post Depreciation for All Assets]
    PostDepreciation --> ReviewJournals[Review All Unposted Journals]
    ReviewJournals --> UnpostedExist{Unposted<br>Journals?}

    UnpostedExist -->|Yes| PostOrVoid[Post or Void Each Unposted Entry]
    PostOrVoid --> ReviewJournals

    UnpostedExist -->|No| RunTrialBalance[Run Trial Balance]
    RunTrialBalance --> TrialBalanced{Trial Balance<br>Balanced?}

    TrialBalanced -->|No| InvestigateVariance[Investigate and Correct Variance]
    InvestigateVariance --> RunTrialBalance

    TrialBalanced -->|Yes| GenerateStatements[Generate Draft Financial Statements]
    GenerateStatements --> FMReview[Finance Manager Reviews Statements]
    FMReview --> FMSignOff{FM Signs Off?}

    FMSignOff -->|No| PostAdjustments[Post Adjustment Entries]
    PostAdjustments --> RunTrialBalance

    FMSignOff -->|Yes| CFOReview[CFO Reviews Final Statements]
    CFOReview --> CFOApprove{CFO Approves?}

    CFOApprove -->|No| PostAdjustments
    CFOApprove -->|Yes| HardClosePeriod[Hard-Close the Accounting Period]
    HardClosePeriod --> ArchiveRecords[Archive Period Records]
    ArchiveRecords --> OpenNextPeriod[Open Next Accounting Period]
    OpenNextPeriod --> End([Period Close Complete])
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
- Maintain an explicit traceability matrix for this artifact (`analysis/activity-diagrams.md`):
  - `Requirement ID` → `Business Rule / Event` → `Design Element` (API/schema/diagram component) → `Code Module` → `Test Evidence` → `Control Owner`.
- Lineage metadata minimums: source event ID, transformation ID/version, posting rule version, reconciliation batch ID, and report consumption path.
- Any change touching accounting semantics must include impact analysis across upstream requirements and downstream close/compliance reports.
- Documentation updates are blocking for release when they alter financial behavior, posting logic, or reconciliation outcomes.

### 7) Phase-Specific Implementation Readiness
- Convert business requirements into executable decision tables with explicit preconditions, data dependencies, and exception states.
- Map each business event to accounting impact (`none`, `memo`, `sub-ledger`, `GL-posting`) and expected latency/SLA.
- Document escalation paths for unresolved breaks, including RACI and aging thresholds.

### 8) Implementation Checklist for `activity diagrams`
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


