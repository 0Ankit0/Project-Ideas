# C4 Code Diagram

## Overview
Class-level C4 diagrams showing the internal structure of key service modules in the Finance Management System.

---

## Journal Entry Service Code Diagram

```mermaid
classDiagram
    class JournalRouter {
        +create_entry(data: JournalEntryCreate, db, user) JournalEntryResponse
        +post_entry(entry_id, db, user) JournalEntryResponse
        +reverse_entry(entry_id, db, user) JournalEntryResponse
        +list_entries(filters, db, user) Page[JournalEntryResponse]
        +get_trial_balance(period_id, db, user) TrialBalanceResponse
    }

    class JournalEntryService {
        -db: AsyncSession
        -journal_repo: JournalRepository
        -period_repo: PeriodRepository
        -audit: AuditService
        +create_entry(user_id, data) JournalEntry
        +post_entry(entry_id, user_id) JournalEntry
        +reverse_entry(entry_id, user_id) JournalEntry
        -_validate_balanced(lines) void
        -_validate_period_open(date, entity_id) void
        -_is_high_value(total) bool
    }

    class JournalRepository {
        -db: AsyncSession
        +find_by_id(id) JournalEntry
        +find_by_period(period_id) list[JournalEntry]
        +find_unposted(entity_id) list[JournalEntry]
        +save(entry, lines) JournalEntry
        +get_account_balance(account_id, as_of_date) Decimal
        +get_trial_balance(period_id, entity_id) list[TrialBalanceLine]
    }

    class PeriodRepository {
        -db: AsyncSession
        +find_by_date(date, entity_id) AccountingPeriod
        +find_current(entity_id) AccountingPeriod
        +get_period(period_id) AccountingPeriod
        +update_status(period_id, status, user_id) AccountingPeriod
    }

    class AuditService {
        -db: AsyncSession
        +log(user_id, action, entity_type, entity_id, before, after) void
        +get_logs(filters) list[AuditLog]
        +export_logs(filters) bytes
    }

    class JournalEntry {
        +id: int
        +entity_id: int
        +period_id: int
        +entry_number: str
        +entry_date: date
        +description: str
        +status: JournalEntryStatus
        +prepared_by_user_id: int
        +lines: list[JournalLine]
        +attachments: list[JournalAttachment]
        +to_dict() dict
    }

    class JournalLine {
        +id: int
        +journal_entry_id: int
        +account_id: int
        +cost_center_id: int
        +description: str
        +debit_amount: Decimal
        +credit_amount: Decimal
        +currency_code: str
        +exchange_rate: Decimal
    }

    JournalRouter --> JournalEntryService : uses
    JournalEntryService --> JournalRepository : delegates
    JournalEntryService --> PeriodRepository : delegates
    JournalEntryService --> AuditService : logs via
    JournalRepository --> JournalEntry : persists
    JournalEntry --> JournalLine : contains
```

---

## Budget Service Code Diagram

```mermaid
classDiagram
    class BudgetRouter {
        +create_budget(data, db, user) BudgetResponse
        +submit_budget(budget_id, db, user) BudgetResponse
        +approve_by_fm(budget_id, db, user) BudgetResponse
        +approve_by_cfo(budget_id, db, user) BudgetResponse
        +reject_budget(budget_id, reason, db, user) BudgetResponse
        +get_variance(budget_id, db, user) VarianceResponse
        +get_utilization(cost_center_id, period_id, db, user) UtilizationResponse
    }

    class BudgetService {
        -db: AsyncSession
        -budget_repo: BudgetRepository
        -workflow: ApprovalWorkflowService
        -notify: NotificationService
        -audit: AuditService
        +create_budget(user_id, data) Budget
        +submit_for_approval(budget_id, user_id) Budget
        +approve_by_fm(budget_id, user_id) Budget
        +approve_by_cfo(budget_id, user_id) Budget
        +reject_budget(budget_id, user_id, reason) Budget
        +create_revision(budget_id, user_id) Budget
        -_load_prior_year_actuals(entity_id, fy_id) list[BudgetLine]
    }

    class VarianceTrackingService {
        -db: AsyncSession
        -budget_repo: BudgetRepository
        -alert_engine: AlertEngine
        +calculate_variance(account_id, cc_id, period_id) BudgetVariance
        +on_gl_posted(account_id, cc_id, period_id, amount) void
        +get_utilization(cc_id, period_id) UtilizationReport
        +generate_variance_report(entity_id, period_id) VarianceReport
    }

    class AlertEngine {
        -notify: NotificationService
        +THRESHOLD_WARN: float = 0.80
        +THRESHOLD_CRITICAL: float = 0.95
        +THRESHOLD_BREACH: float = 1.00
        +evaluate_and_alert(account_id, cc_id, utilization_pct) void
        -_get_stakeholders(cc_id) list[int]
        -_determine_level(utilization_pct) AlertLevel
    }

    class Budget {
        +id: int
        +entity_id: int
        +fiscal_year_id: int
        +budget_name: str
        +status: BudgetStatus
        +version: int
        +lines: list[BudgetLine]
        +to_dict() dict
    }

    class BudgetLine {
        +id: int
        +budget_id: int
        +account_id: int
        +cost_center_id: int
        +period_id: int
        +amount: Decimal
        +notes: str
    }

    BudgetRouter --> BudgetService : uses
    BudgetService --> VarianceTrackingService : triggers
    VarianceTrackingService --> AlertEngine : evaluates via
    BudgetService --> Budget : manages
    Budget --> BudgetLine : contains
```

---

## Payroll Service Code Diagram

```mermaid
classDiagram
    class PayrollRouter {
        +create_run(data, db, user) PayrollRunResponse
        +calculate_run(run_id, db, user) PayrollRegisterResponse
        +submit_run(run_id, db, user) PayrollRunResponse
        +approve_run(run_id, db, user) PayrollRunResponse
        +disburse_run(run_id, db, user) DisbursementResponse
        +get_register(run_id, db, user) PayrollRegisterResponse
        +get_pay_stub(run_id, emp_id, db, user) PDFResponse
    }

    class PayrollService {
        -db: AsyncSession
        -employee_repo: PayrollEmployeeRepository
        -run_repo: PayrollRunRepository
        -deduction_engine: DeductionEngine
        -bank_service: BankFileService
        -gl_service: GLPostingService
        -notify: NotificationService
        -audit: AuditService
        +create_run(user_id, period_start, period_end, pay_group) PayrollRun
        +calculate_run(run_id) PayrollRun
        +submit_for_approval(run_id, user_id) PayrollRun
        +approve_run(run_id, user_id) PayrollRun
        +disburse(run_id) DisbursementResult
        -_validate_pre_run(run_id) ValidationResult
        -_compute_entry(employee, run) PayrollEntry
    }

    class DeductionEngine {
        -tax_config: TaxConfiguration
        +calculate_income_tax(gross_pay, employee) Decimal
        +calculate_social_security(gross_pay, employee) Decimal
        +calculate_provident_fund(gross_pay, employee) Decimal
        +calculate_voluntary_deductions(employee) list[Deduction]
        +compute_net_pay(gross_pay, deductions) Decimal
        -_get_tax_bracket(annual_income, jurisdiction) TaxBracket
    }

    class BankFileService {
        +generate_ach_file(run_id, entries) bytes
        +generate_neft_file(run_id, entries) bytes
        +upload_to_s3(run_id, file_bytes) str
        +submit_to_bank(file_url, bank_config) BankSubmitResult
    }

    class GLPostingService {
        -journal_service: JournalEntryService
        +post_payroll_entries(run_id) JournalEntry
        +post_expense_reimbursement(claim_id) JournalEntry
        +post_depreciation(period_id, entries) JournalEntry
        +post_ap_liability(invoice_id) JournalEntry
        +post_ap_payment(run_id) JournalEntry
    }

    class PayrollRun {
        +id: int
        +run_reference: str
        +period_start: date
        +period_end: date
        +status: PayrollRunStatus
        +total_gross: Decimal
        +total_deductions: Decimal
        +total_net: Decimal
        +entries: list[PayrollEntry]
    }

    class PayrollEntry {
        +id: int
        +payroll_run_id: int
        +employee_id: int
        +gross_pay: Decimal
        +income_tax: Decimal
        +social_security: Decimal
        +provident_fund: Decimal
        +other_deductions: Decimal
        +net_pay: Decimal
        +status: PayEntryStatus
    }

    PayrollRouter --> PayrollService : uses
    PayrollService --> DeductionEngine : computes via
    PayrollService --> BankFileService : disburses via
    PayrollService --> GLPostingService : posts via
    PayrollService --> PayrollRun : manages
    PayrollRun --> PayrollEntry : contains
```
