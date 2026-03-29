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
- Maintain an explicit traceability matrix for this artifact (`detailed-design/class-diagrams.md`):
  - `Requirement ID` → `Business Rule / Event` → `Design Element` (API/schema/diagram component) → `Code Module` → `Test Evidence` → `Control Owner`.
- Lineage metadata minimums: source event ID, transformation ID/version, posting rule version, reconciliation batch ID, and report consumption path.
- Any change touching accounting semantics must include impact analysis across upstream requirements and downstream close/compliance reports.
- Documentation updates are blocking for release when they alter financial behavior, posting logic, or reconciliation outcomes.

### 7) Phase-Specific Implementation Readiness
- Specify schema-level constraints: unique idempotency keys, check constraints for debit/credit signs, immutable posting rows, FK coverage.
- Define API contracts for posting/approval/reconciliation including error codes, retry semantics, and deterministic conflict handling.
- Include state-transition guards for approval and period-close flows to prevent illegal transitions.

### 8) Implementation Checklist for `class diagrams`
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


