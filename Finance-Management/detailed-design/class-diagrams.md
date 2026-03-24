# Class Diagrams

## Overview
Detailed class structures with attributes and methods for the core Finance Management System domain.

---

## General Ledger Classes

```mermaid
classDiagram
    class JournalEntryService {
        +db: AsyncSession
        +journal_repo: JournalRepository
        +period_repo: PeriodRepository
        +audit_service: AuditService
        +create_entry(user_id, data: JournalEntryCreate) JournalEntry
        +post_entry(entry_id, user_id) JournalEntry
        +reverse_entry(entry_id, user_id) JournalEntry
        +get_entry(entry_id) JournalEntry
        +list_entries(filters, page, limit) Page~JournalEntry~
        -_validate_balanced(lines: list) void
        -_validate_period_open(entry_date, entity_id) void
    }

    class JournalRepository {
        +db: AsyncSession
        +find_by_id(id: int) JournalEntry
        +find_by_period(period_id: int) list~JournalEntry~
        +save(entry: JournalEntry) JournalEntry
        +find_unposted(entity_id: int) list~JournalEntry~
        +get_account_balance(account_id, as_of_date) Decimal
    }

    class PeriodService {
        +db: AsyncSession
        +period_repo: PeriodRepository
        +open_period(period_id, user_id) AccountingPeriod
        +soft_close(period_id, user_id) AccountingPeriod
        +hard_close(period_id, user_id) AccountingPeriod
        +is_period_open(period_id) bool
        +get_current_period(entity_id) AccountingPeriod
        -_run_close_validations(period_id) CloseValidationResult
    }

    class ReconciliationService {
        +db: AsyncSession
        +import_bank_statement(file, bank_account_id) ImportResult
        +auto_match_transactions(bank_account_id) MatchResult
        +manual_match(gl_transaction_id, bank_txn_id) void
        +get_unmatched_items(bank_account_id) list~UnmatchedItem~
        +generate_reconciliation_report(bank_account_id, period_id) ReconciliationReport
    }

    JournalEntryService --> JournalRepository
    JournalEntryService --> PeriodService
```

---

## Accounts Payable Classes

```mermaid
classDiagram
    class InvoiceService {
        +db: AsyncSession
        +invoice_repo: InvoiceRepository
        +vendor_repo: VendorRepository
        +matching_service: MatchingService
        +audit_service: AuditService
        +create_invoice(user_id, data: InvoiceCreate) VendorInvoice
        +submit_for_approval(invoice_id, user_id) VendorInvoice
        +approve_invoice(invoice_id, user_id) VendorInvoice
        +reject_invoice(invoice_id, user_id, reason) VendorInvoice
        +void_invoice(invoice_id, user_id, reason) VendorInvoice
        +get_aging_report(as_of_date) APAgingReport
        -_check_duplicate(vendor_id, invoice_no, amount) bool
    }

    class MatchingService {
        +db: AsyncSession
        +perform_three_way_match(invoice_id, po_id, receipt_id) MatchResult
        +perform_two_way_match(invoice_id, po_id) MatchResult
        -_calculate_variance(invoice_line, po_line) Decimal
        -_is_within_tolerance(variance_pct, tolerance_pct) bool
    }

    class PaymentRunService {
        +db: AsyncSession
        +payment_run_repo: PaymentRunRepository
        +bank_service: BankFileService
        +gl_service: GLPostingService
        +create_run(user_id, invoice_ids: list) PaymentRun
        +approve_run(run_id, user_id) PaymentRun
        +generate_bank_file(run_id) BankFile
        +submit_to_bank(run_id) SubmitResult
        +process_bank_confirmation(batch_ref, status) void
        +mark_invoices_paid(run_id) void
        -_apply_early_pay_discount(invoice_id) Decimal
    }

    InvoiceService --> MatchingService
    PaymentRunService --> InvoiceService
```

---

## Budgeting Classes

```mermaid
classDiagram
    class BudgetService {
        +db: AsyncSession
        +budget_repo: BudgetRepository
        +workflow_service: ApprovalWorkflowService
        +notify_service: NotificationService
        +create_budget(user_id, data: BudgetCreate) Budget
        +submit_for_approval(budget_id, user_id) Budget
        +approve_by_fm(budget_id, user_id) Budget
        +approve_by_cfo(budget_id, user_id) Budget
        +reject_budget(budget_id, user_id, reason) Budget
        +create_revision(budget_id, user_id) Budget
        +get_budget_utilization(cost_center_id, period_id) UtilizationReport
        -_load_prior_year_actuals(entity_id, fiscal_year_id) list~BudgetLine~
    }

    class VarianceTrackingService {
        +db: AsyncSession
        +budget_repo: BudgetRepository
        +calculate_variance(account_id, cost_center_id, period_id) BudgetVariance
        +check_budget_thresholds(account_id, cost_center_id, period_id) list~Alert~
        +generate_variance_report(entity_id, period_id) VarianceReport
        +get_forecast(entity_id, period_id) Forecast
    }

    class AlertEngine {
        +variance_service: VarianceTrackingService
        +notify_service: NotificationService
        +THRESHOLD_80: float = 0.80
        +THRESHOLD_95: float = 0.95
        +THRESHOLD_BREACH: float = 1.00
        +evaluate_and_alert(account_id, cost_center_id, period_id) void
        -_determine_alert_level(utilization_pct) AlertLevel
        -_notify_stakeholders(level, cost_center_id, utilization) void
    }

    BudgetService --> VarianceTrackingService
    VarianceTrackingService --> AlertEngine
```

---

## Payroll Classes

```mermaid
classDiagram
    class PayrollService {
        +db: AsyncSession
        +employee_repo: PayrollEmployeeRepository
        +run_repo: PayrollRunRepository
        +deduction_engine: DeductionEngine
        +bank_service: BankFileService
        +gl_service: GLPostingService
        +create_run(user_id, period_start, period_end, pay_group) PayrollRun
        +calculate_run(run_id) PayrollRun
        +submit_for_approval(run_id, user_id) PayrollRun
        +approve_run(run_id, user_id) PayrollRun
        +disburse(run_id) DisbursementResult
        +generate_pay_stubs(run_id) list~PayStub~
        -_validate_pre_run(run_id) ValidationResult
    }

    class DeductionEngine {
        +tax_config: TaxConfiguration
        +calculate_income_tax(gross_pay, employee_id) Decimal
        +calculate_social_security(gross_pay, employee_id) Decimal
        +calculate_provident_fund(gross_pay, employee_id) Decimal
        +calculate_voluntary_deductions(employee_id) list~Deduction~
        +compute_net_pay(gross_pay, deductions: list) Decimal
    }

    PayrollService --> DeductionEngine
```

---

## Notification and Audit Classes

```mermaid
classDiagram
    class NotificationService {
        +db: AsyncSession
        +email_provider: EmailProvider
        +push_provider: PushProvider
        +ws_manager: WebSocketManager
        +send_approval_request(user_id, entity_type, entity_id) void
        +send_approval_decision(user_id, approved: bool, reason) void
        +send_payment_confirmation(user_id, amount, reference) void
        +send_budget_alert(user_id, alert: BudgetAlert) void
        +send_period_close_reminder(user_ids: list, period_id) void
        -_persist_notification(user_id, type, payload) Notification
    }

    class AuditService {
        +db: AsyncSession
        +audit_repo: AuditRepository
        +log(user_id, action, entity_type, entity_id, before, after) AuditLog
        +get_logs(filters: AuditFilter) list~AuditLog~
        +export_logs(filters: AuditFilter) bytes
    }

    class WebSocketManager {
        +connections: dict~int, WebSocket~
        +connect(user_id, ws: WebSocket) void
        +disconnect(user_id) void
        +broadcast_to_user(user_id, event: dict) void
        +broadcast_to_role(role: str, event: dict) void
    }

    NotificationService --> WebSocketManager
    NotificationService --> AuditService
```
