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
