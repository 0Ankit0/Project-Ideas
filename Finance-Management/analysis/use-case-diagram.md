# Use Case Diagram

## Overview
This document contains use case diagrams for all major actors in the Finance Management System.

---

## Complete System Use Case Diagram

```mermaid
graph TB
    subgraph Actors
        CFO((CFO))
        FM((Finance Manager))
        ACC((Accountant))
        BM((Budget Manager))
        AUD((Auditor))
        EMP((Employee))
        DH((Dept Head))
        Bank((Banking System))
        TaxAuth((Tax Authority))
    end

    subgraph "Finance Management System"
        UC1[Manage General Ledger]
        UC2[Manage Accounts Payable]
        UC3[Manage Accounts Receivable]
        UC4[Manage Budgets]
        UC5[Manage Expenses]
        UC6[Process Payroll]
        UC7[Manage Fixed Assets]
        UC8[Manage Taxes]
        UC9[Generate Reports]
        UC10[Manage Audit & Compliance]
        UC11[Configure System]
        UC12[Manage Period Close]
    end

    CFO --> UC4
    CFO --> UC9
    CFO --> UC12

    FM --> UC1
    FM --> UC2
    FM --> UC3
    FM --> UC4
    FM --> UC6
    FM --> UC8
    FM --> UC9
    FM --> UC12

    ACC --> UC1
    ACC --> UC2
    ACC --> UC3
    ACC --> UC7
    ACC --> UC8

    BM --> UC4

    AUD --> UC10
    AUD --> UC9

    EMP --> UC5

    DH --> UC4
    DH --> UC5

    UC2 --> Bank
    UC3 --> Bank
    UC6 --> Bank
    UC8 --> TaxAuth
```

---

## Accountant Use Cases

```mermaid
graph LR
    Accountant((Accountant))

    subgraph "General Ledger"
        UC1[Create Journal Entry]
        UC2[Create Recurring Entry]
        UC3[Reverse Journal Entry]
        UC4[View Trial Balance]
        UC5[Perform Bank Reconciliation]
        UC6[Manage Chart of Accounts]
    end

    subgraph "Accounts Payable"
        UC7[Register Vendor]
        UC8[Record Vendor Invoice]
        UC9[3-Way Match Invoice]
        UC10[Generate AP Aging Report]
        UC11[Record Credit Note]
        UC12[Process Payment Run]
    end

    subgraph "Accounts Receivable"
        UC13[Create Customer Invoice]
        UC14[Record Customer Payment]
        UC15[Apply Payment to Invoice]
        UC16[Generate AR Aging Report]
        UC17[Write Off Bad Debt]
        UC18[Send Payment Reminder]
    end

    subgraph "Period Close"
        UC19[Run Pre-Close Checklist]
        UC20[Post Accruals]
        UC21[Post Depreciation]
        UC22[Close Accounting Period]
    end

    Accountant --> UC1
    Accountant --> UC2
    Accountant --> UC3
    Accountant --> UC4
    Accountant --> UC5
    Accountant --> UC6
    Accountant --> UC7
    Accountant --> UC8
    Accountant --> UC9
    Accountant --> UC10
    Accountant --> UC11
    Accountant --> UC12
    Accountant --> UC13
    Accountant --> UC14
    Accountant --> UC15
    Accountant --> UC16
    Accountant --> UC17
    Accountant --> UC18
    Accountant --> UC19
    Accountant --> UC20
    Accountant --> UC21
    Accountant --> UC22
```

---

## Finance Manager Use Cases

```mermaid
graph LR
    FM((Finance Manager))

    subgraph "Approval & Control"
        UC1[Approve Payment Batches]
        UC2[Approve Payroll Run]
        UC3[Approve Vendor Onboarding]
        UC4[Approve Journal Entries]
        UC5[Approve Budget Revisions]
    end

    subgraph "Treasury"
        UC6[Monitor Cash Position]
        UC7[Manage Bank Accounts]
        UC8[Initiate Interbank Transfers]
        UC9[View Cash Flow Forecast]
    end

    subgraph "Period Close"
        UC10[Initiate Period Close Checklist]
        UC11[Review Reconciliation Items]
        UC12[Authorize Period Hard-Close]
        UC13[Review Consolidation Adjustments]
    end

    subgraph "Reporting"
        UC14[View Financial Dashboards]
        UC15[Generate P&L Report]
        UC16[Generate Balance Sheet]
        UC17[Generate Cash Flow Statement]
        UC18[Schedule Reports]
    end

    subgraph "Tax & Compliance"
        UC19[Configure Tax Rates]
        UC20[Review Tax Liability Report]
        UC21[Approve Tax Filings]
    end

    FM --> UC1
    FM --> UC2
    FM --> UC3
    FM --> UC4
    FM --> UC5
    FM --> UC6
    FM --> UC7
    FM --> UC8
    FM --> UC9
    FM --> UC10
    FM --> UC11
    FM --> UC12
    FM --> UC13
    FM --> UC14
    FM --> UC15
    FM --> UC16
    FM --> UC17
    FM --> UC18
    FM --> UC19
    FM --> UC20
    FM --> UC21
```

---

## CFO Use Cases

```mermaid
graph LR
    CFO((CFO))

    subgraph "Executive Reporting"
        UC1[View Executive Dashboard]
        UC2[Review Consolidated Financials]
        UC3[View Budget vs Actuals]
        UC4[Analyze Financial Ratios]
        UC5[View Cash Flow Forecast]
    end

    subgraph "Strategic Approvals"
        UC6[Approve Annual Budget]
        UC7[Approve Capital Expenditure]
        UC8[Approve Large Payments]
        UC9[Approve New Entity Setup]
    end

    subgraph "Governance"
        UC10[Set Approval Thresholds]
        UC11[View Audit Exception Reports]
        UC12[Review Internal Controls]
        UC13[Sign Off on Period Close]
    end

    CFO --> UC1
    CFO --> UC2
    CFO --> UC3
    CFO --> UC4
    CFO --> UC5
    CFO --> UC6
    CFO --> UC7
    CFO --> UC8
    CFO --> UC9
    CFO --> UC10
    CFO --> UC11
    CFO --> UC12
    CFO --> UC13
```

---

## Employee & Department Head Use Cases

```mermaid
graph LR
    Employee((Employee))
    DeptHead((Dept Head))

    subgraph "Expense Submission"
        UC1[Submit Expense Claim]
        UC2[Upload Receipt]
        UC3[Submit Mileage Claim]
        UC4[Reconcile Corporate Card]
        UC5[Track Reimbursement Status]
    end

    subgraph "Department Management"
        UC6[Approve Team Expense Claims]
        UC7[View Department Budget]
        UC8[Request Budget Revision]
        UC9[Approve Purchase Requisition]
        UC10[View Departmental Reports]
    end

    Employee --> UC1
    Employee --> UC2
    Employee --> UC3
    Employee --> UC4
    Employee --> UC5

    DeptHead --> UC1
    DeptHead --> UC2
    DeptHead --> UC3
    DeptHead --> UC5
    DeptHead --> UC6
    DeptHead --> UC7
    DeptHead --> UC8
    DeptHead --> UC9
    DeptHead --> UC10
```

---

## Auditor Use Cases

```mermaid
graph LR
    Auditor((Auditor))

    subgraph "Audit Access"
        UC1[View All Financial Records]
        UC2[View Full Audit Trail]
        UC3[Export Audit Logs]
        UC4[View Approval Workflows]
        UC5[Access Supporting Documents]
    end

    subgraph "Compliance Reporting"
        UC6[Run Segregation of Duties Report]
        UC7[Run High-Value Transaction Report]
        UC8[Run Exception Report]
        UC9[Generate Confirmation Letters]
        UC10[Review Period-Close Sign-offs]
    end

    Auditor --> UC1
    Auditor --> UC2
    Auditor --> UC3
    Auditor --> UC4
    Auditor --> UC5
    Auditor --> UC6
    Auditor --> UC7
    Auditor --> UC8
    Auditor --> UC9
    Auditor --> UC10
```

---

## Use Case Relationships

```mermaid
graph TB
    subgraph "Include Relationships"
        CreateJE[Create Journal Entry] -->|includes| ValidateBalance[Validate Debit = Credit]
        CreateJE -->|includes| AttachDocument[Attach Supporting Document]
        CreateJE -->|includes| PostToGL[Post to General Ledger]

        ProcessPayment[Process Payment Run] -->|includes| ValidateApproval[Check Approval Status]
        ProcessPayment -->|includes| GenerateBankFile[Generate Bank Transfer File]
        ProcessPayment -->|includes| UpdateAPLedger[Update AP Ledger]

        PeriodClose[Close Accounting Period] -->|includes| RunTrialBalance[Run Trial Balance]
        PeriodClose -->|includes| PostDepreciation[Post Depreciation]
        PeriodClose -->|includes| ReconcileAccounts[Reconcile All Accounts]
    end

    subgraph "Extend Relationships"
        RecordInvoice[Record Vendor Invoice] -.->|extends| ThreeWayMatch[3-Way Match Validation]
        RecordInvoice -.->|extends| DuplicateCheck[Duplicate Invoice Check]

        ApproveExpense[Approve Expense] -.->|extends| PolicyCheck[Policy Limit Check]
        ApproveExpense -.->|extends| ReceiptVerification[Receipt Verification]

        GenerateReport[Generate Report] -.->|extends| ConsolidationAdjust[Apply Consolidation]
        GenerateReport -.->|extends| CurrencyConvert[Multi-Currency Conversion]
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
- Maintain an explicit traceability matrix for this artifact (`analysis/use-case-diagram.md`):
  - `Requirement ID` → `Business Rule / Event` → `Design Element` (API/schema/diagram component) → `Code Module` → `Test Evidence` → `Control Owner`.
- Lineage metadata minimums: source event ID, transformation ID/version, posting rule version, reconciliation batch ID, and report consumption path.
- Any change touching accounting semantics must include impact analysis across upstream requirements and downstream close/compliance reports.
- Documentation updates are blocking for release when they alter financial behavior, posting logic, or reconciliation outcomes.

### 7) Phase-Specific Implementation Readiness
- Convert business requirements into executable decision tables with explicit preconditions, data dependencies, and exception states.
- Map each business event to accounting impact (`none`, `memo`, `sub-ledger`, `GL-posting`) and expected latency/SLA.
- Document escalation paths for unresolved breaks, including RACI and aging thresholds.

### 8) Implementation Checklist for `use case diagram`
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


