# Domain Model

## Overview
This document defines the key entities, their attributes, and relationships that form the core of the Finance Management System.

---

## General Ledger Domain

```mermaid
classDiagram
    class ChartOfAccount {
        +int id
        +string account_code
        +string account_name
        +AccountType account_type
        +int parent_id
        +int level
        +bool is_active
        +bool allow_direct_posting
        +string currency_code
        +datetime created_at
    }

    class JournalEntry {
        +int id
        +string entry_number
        +date entry_date
        +string reference
        +string description
        +JournalEntryStatus status
        +int period_id
        +int prepared_by_user_id
        +int approved_by_user_id
        +bool is_recurring
        +bool is_reversal
        +int reversed_entry_id
        +datetime created_at
        +datetime posted_at
    }

    class JournalLine {
        +int id
        +int journal_entry_id
        +int account_id
        +string description
        +decimal debit_amount
        +decimal credit_amount
        +string currency_code
        +decimal exchange_rate
        +int cost_center_id
        +int entity_id
    }

    class AccountingPeriod {
        +int id
        +int fiscal_year_id
        +string period_name
        +date start_date
        +date end_date
        +PeriodStatus status
        +int closed_by_user_id
        +datetime closed_at
    }

    class FiscalYear {
        +int id
        +string name
        +date start_date
        +date end_date
        +FiscalYearStatus status
    }

    JournalEntry "1" --> "2..*" JournalLine : contains
    JournalLine "many" --> "1" ChartOfAccount : posts_to
    JournalEntry "many" --> "1" AccountingPeriod : belongs_to
    AccountingPeriod "many" --> "1" FiscalYear : part_of
    ChartOfAccount "0..1" --> "0..*" ChartOfAccount : parent_of
```

---

## Accounts Payable Domain

```mermaid
classDiagram
    class Vendor {
        +int id
        +string vendor_code
        +string legal_name
        +string tax_id
        +string payment_terms
        +VendorStatus status
        +bool is_1099_vendor
        +string default_currency
        +datetime approved_at
    }

    class VendorInvoice {
        +int id
        +int vendor_id
        +int purchase_order_id
        +string invoice_number
        +date invoice_date
        +date due_date
        +decimal subtotal
        +decimal tax_amount
        +decimal total_amount
        +string currency_code
        +decimal exchange_rate
        +InvoiceStatus status
        +MatchType match_type
        +datetime created_at
    }

    class PaymentRun {
        +int id
        +string run_reference
        +date payment_date
        +decimal total_amount
        +PaymentRunStatus status
        +int approved_by_user_id
        +string bank_file_reference
        +datetime created_at
        +datetime approved_at
    }

    class PaymentRunItem {
        +int id
        +int payment_run_id
        +int vendor_invoice_id
        +decimal payment_amount
        +decimal discount_taken
        +PaymentItemStatus status
    }

    Vendor "1" --> "0..*" VendorInvoice : bills
    PaymentRun "1" --> "1..*" PaymentRunItem : contains
    PaymentRunItem "many" --> "1" VendorInvoice : pays
```

---

## Accounts Receivable Domain

```mermaid
classDiagram
    class Customer {
        +int id
        +string customer_code
        +string legal_name
        +string tax_id
        +string payment_terms
        +decimal credit_limit
        +CustomerStatus status
        +string currency_code
    }

    class CustomerInvoice {
        +int id
        +int customer_id
        +string invoice_number
        +date invoice_date
        +date due_date
        +decimal subtotal
        +decimal tax_amount
        +decimal total_amount
        +decimal amount_paid
        +decimal balance_due
        +string currency_code
        +InvoiceStatus status
        +datetime created_at
    }

    class CustomerPayment {
        +int id
        +int customer_id
        +date payment_date
        +decimal amount
        +string payment_method
        +string reference
        +string currency_code
        +PaymentStatus status
        +datetime created_at
    }

    class PaymentAllocation {
        +int id
        +int payment_id
        +int invoice_id
        +decimal amount_applied
        +datetime created_at
    }

    Customer "1" --> "0..*" CustomerInvoice : receives
    Customer "1" --> "0..*" CustomerPayment : makes
    CustomerPayment "1" --> "1..*" PaymentAllocation : allocates_to
    PaymentAllocation "many" --> "1" CustomerInvoice : applied_against
```

---

## Budgeting Domain

```mermaid
classDiagram
    class Budget {
        +int id
        +string budget_name
        +int fiscal_year_id
        +int entity_id
        +BudgetStatus status
        +int version
        +int submitted_by_user_id
        +int approved_by_user_id
        +int cfo_approved_by_user_id
        +datetime created_at
        +datetime approved_at
    }

    class BudgetLine {
        +int id
        +int budget_id
        +int account_id
        +int cost_center_id
        +int period_id
        +decimal amount
        +string notes
    }

    class CostCenter {
        +int id
        +string code
        +string name
        +int department_id
        +int manager_user_id
        +bool is_active
    }

    class BudgetVariance {
        +int id
        +int budget_line_id
        +decimal budget_amount
        +decimal actual_amount
        +decimal variance_amount
        +decimal variance_pct
        +date as_of_date
    }

    Budget "1" --> "1..*" BudgetLine : contains
    BudgetLine "many" --> "1" CostCenter : allocated_to
    BudgetLine "1" --> "0..*" BudgetVariance : tracked_via
```

---

## Payroll Domain

```mermaid
classDiagram
    class PayrollEmployee {
        +int id
        +int hr_employee_id
        +string employee_code
        +string full_name
        +PayType pay_type
        +decimal base_salary
        +string pay_currency
        +string bank_account_number
        +string bank_routing_number
        +bool is_active
    }

    class PayrollRun {
        +int id
        +string run_reference
        +date period_start
        +date period_end
        +PaySchedule pay_schedule
        +PayrollRunStatus status
        +decimal total_gross
        +decimal total_deductions
        +decimal total_net
        +int approved_by_user_id
        +datetime created_at
        +datetime approved_at
        +datetime disbursed_at
    }

    class PayrollEntry {
        +int id
        +int payroll_run_id
        +int employee_id
        +decimal gross_pay
        +decimal income_tax
        +decimal social_security
        +decimal provident_fund
        +decimal other_deductions
        +decimal net_pay
        +PayEntryStatus status
    }

    PayrollRun "1" --> "1..*" PayrollEntry : contains
    PayrollEntry "many" --> "1" PayrollEmployee : for
```

---

## Fixed Assets Domain

```mermaid
classDiagram
    class FixedAsset {
        +int id
        +string asset_number
        +string asset_name
        +int asset_category_id
        +int location_id
        +int department_id
        +date acquisition_date
        +decimal acquisition_cost
        +decimal residual_value
        +int useful_life_months
        +DepreciationMethod depreciation_method
        +decimal accumulated_depreciation
        +decimal net_book_value
        +AssetStatus status
    }

    class AssetDepreciationEntry {
        +int id
        +int asset_id
        +int period_id
        +decimal depreciation_amount
        +int journal_entry_id
        +datetime posted_at
    }

    class AssetCategory {
        +int id
        +string name
        +int default_useful_life_months
        +DepreciationMethod default_depreciation_method
        +int asset_account_id
        +int accumulated_depreciation_account_id
        +int depreciation_expense_account_id
    }

    FixedAsset "many" --> "1" AssetCategory : classified_as
    FixedAsset "1" --> "0..*" AssetDepreciationEntry : has
```

---

## Enumeration Types

```mermaid
classDiagram
    class AccountType {
        <<enumeration>>
        ASSET
        LIABILITY
        EQUITY
        REVENUE
        EXPENSE
    }

    class JournalEntryStatus {
        <<enumeration>>
        DRAFT
        POSTED
        REVERSED
    }

    class PeriodStatus {
        <<enumeration>>
        OPEN
        SOFT_CLOSED
        HARD_CLOSED
    }

    class InvoiceStatus {
        <<enumeration>>
        DRAFT
        SUBMITTED
        APPROVED
        PARTIALLY_PAID
        PAID
        VOID
    }

    class BudgetStatus {
        <<enumeration>>
        DRAFT
        PENDING_FM_APPROVAL
        PENDING_CFO_APPROVAL
        APPROVED
        REVISED
    }

    class PayrollRunStatus {
        <<enumeration>>
        DRAFT
        PENDING_APPROVAL
        APPROVED
        DISBURSED
        FAILED
    }

    class DepreciationMethod {
        <<enumeration>>
        STRAIGHT_LINE
        DECLINING_BALANCE
        SUM_OF_YEARS_DIGITS
        UNITS_OF_PRODUCTION
    }
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
- Maintain an explicit traceability matrix for this artifact (`high-level-design/domain-model.md`):
  - `Requirement ID` → `Business Rule / Event` → `Design Element` (API/schema/diagram component) → `Code Module` → `Test Evidence` → `Control Owner`.
- Lineage metadata minimums: source event ID, transformation ID/version, posting rule version, reconciliation batch ID, and report consumption path.
- Any change touching accounting semantics must include impact analysis across upstream requirements and downstream close/compliance reports.
- Documentation updates are blocking for release when they alter financial behavior, posting logic, or reconciliation outcomes.

### 7) Phase-Specific Implementation Readiness
- Define bounded contexts for Ledger, AP, AR, Treasury, Tax, Payroll, and Reporting with explicit ownership boundaries.
- Specify asynchronous vs synchronous paths and where consistency is strong, eventual, or externally constrained.
- Declare resilience posture for each integration (retry, DLQ, replay, compensating entry, manual hold).

### 8) Implementation Checklist for `domain model`
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


