# Sequence Diagrams

## Overview
Internal component interaction sequence diagrams for key workflows in the Finance Management System.

---

## Journal Entry Creation and GL Posting

```mermaid
sequenceDiagram
    participant Router as GL Router
    participant JES as JournalEntryService
    participant VS as ValidationService
    participant PS as PeriodService
    participant JRepo as JournalRepository
    participant AuditSvc as AuditService
    participant NotifySvc as NotificationService

    Router->>JES: create_entry(user_id, data)

    JES->>VS: validate_balanced(lines)
    VS-->>JES: valid

    JES->>PS: is_period_open(entry_date, entity_id)
    PS-->>JES: open=True

    JES->>JRepo: save(entry, status=POSTED)
    JRepo-->>JES: entry{id, entry_number}

    JES->>AuditSvc: log(user_id, CREATE, JOURNAL_ENTRY, entry.id, None, entry)
    AuditSvc-->>JES: logged

    JES->>JES: is_high_value(entry.total_debit)

    alt High-value entry
        JES->>NotifySvc: send_alert(finance_manager_id, LARGE_JE, entry.id)
    end

    JES-->>Router: JournalEntry response
```

---

## 3-Way Invoice Match and Approval

```mermaid
sequenceDiagram
    participant Router as AP Router
    participant IS as InvoiceService
    participant MS as MatchingService
    participant WF as WorkflowService
    participant GL as GLPostingService
    participant NS as NotificationService

    Router->>IS: create_invoice(user_id, invoice_data)
    IS->>IS: check_duplicate(vendor_id, invoice_no, amount)
    IS-->>Router: 409 if duplicate

    IS->>MS: perform_three_way_match(invoice_id, po_id, receipt_id)
    MS->>MS: compare invoice lines vs PO lines vs receipt
    MS->>MS: calculate_variance_pct per line
    MS-->>IS: MatchResult{status, variances[]}

    alt Match passes
        IS->>IS: set status=PENDING_APPROVAL
        IS->>WF: route_for_approval(invoice_id, amount)
        WF->>NS: notify_approver(fm_id, INVOICE_APPROVAL, invoice_id)
    else Variance exceeds tolerance
        IS->>IS: set status=MATCH_EXCEPTION
        IS->>NS: notify_fm(MATCH_EXCEPTION, invoice_id, variances)
    end

    Note over WF,NS: Finance Manager approves via API

    WF->>IS: approve(invoice_id, fm_user_id)
    IS->>GL: post_ap_liability(invoice_id)
    GL-->>IS: journal_entry_id
    IS->>IS: set status=APPROVED
    IS-->>Router: VendorInvoice response
```

---

## Budget Variance Alert on GL Posting

```mermaid
sequenceDiagram
    participant GL as GL Posting Engine
    participant BV as BudgetVarianceService
    participant AE as AlertEngine
    participant NS as NotificationService
    participant WS as WebSocketManager

    GL->>BV: on_gl_posted(account_id, cost_center_id, period_id, amount)
    BV->>BV: fetch approved budget for account + cost center + period
    BV->>BV: fetch actuals YTD
    BV->>BV: calculate utilization_pct

    BV->>BV: upsert budget_variance record

    BV->>AE: evaluate_and_alert(account_id, cost_center_id, utilization_pct)

    alt utilization >= 80%
        AE->>NS: send_budget_alert(budget_manager_id, level=WARNING, utilization_pct)
        NS->>WS: broadcast_to_user(budget_manager_id, {type: BUDGET_ALERT, level: WARNING})
    end

    alt utilization >= 95%
        AE->>NS: send_budget_alert(budget_manager_id, level=CRITICAL, utilization_pct)
        AE->>NS: send_budget_alert(finance_manager_id, level=CRITICAL, utilization_pct)
        NS->>WS: broadcast_to_role(FINANCE_MANAGER, {type: BUDGET_ALERT, level: CRITICAL})
    end

    alt utilization > 100%
        AE->>NS: send_budget_alert(cfo_id, level=BREACH, utilization_pct)
    end
```

---

## Payroll Run: Calculate and Approve

```mermaid
sequenceDiagram
    participant ACC as Accountant
    participant PR as PayrollRouter
    participant PS as PayrollService
    participant DE as DeductionEngine
    participant HR as HR Integration
    participant GL as GLPostingService
    participant BANK as BankFileService

    ACC->>PR: POST /payroll/runs (period, pay_group)
    PR->>PS: create_run(period, pay_group)
    PS->>HR: get_employees(pay_group)
    HR-->>PS: employee list with salary and deductions

    PS->>PS: run_pre_validation(employees)
    PS-->>ACC: ValidationReport {errors, warnings}

    ACC->>PR: POST /payroll/runs/{id}/calculate
    PR->>PS: calculate_run(run_id)

    loop for each employee
        PS->>DE: calculate_income_tax(gross, employee)
        PS->>DE: calculate_statutory_deductions(gross, employee)
        PS->>DE: calculate_voluntary_deductions(employee)
        DE-->>PS: DeductionResult{tax, ss, pf, others}
        PS->>PS: compute net_pay
    end

    PS->>PS: aggregate totals
    PS-->>ACC: PayrollRegister

    ACC->>PR: POST /payroll/runs/{id}/submit
    PR->>PS: submit_for_approval(run_id)
    PS->>NS: notify_fm(PAYROLL_APPROVAL, run_id)

    Note over ACC,NS: Finance Manager approves

    PS->>BANK: generate_direct_deposit_file(run_id)
    BANK-->>PS: BankFile{file_path, employee_count}

    PS->>GL: post_payroll_gl_entries(run_id)
    GL-->>PS: journal_entry_id

    PS->>NS: send_pay_stubs(run_id)
    PS-->>ACC: {status: DISBURSED}
```

---

## Fixed Asset Depreciation Posting at Period Close

```mermaid
sequenceDiagram
    participant FM as Finance Manager
    participant FARouter as Fixed Asset Router
    participant DES as DepreciationEngine
    participant AssetRepo as AssetRepository
    participant GL as GLPostingService
    participant NS as NotificationService

    FM->>FARouter: POST /assets/depreciation/post?period_id={id}
    FARouter->>DES: post_period_depreciation(period_id)

    DES->>AssetRepo: get_active_assets(entity_id)
    AssetRepo-->>DES: list of FixedAsset

    loop for each asset
        DES->>DES: calculate_period_depreciation(asset, period)
        DES->>GL: post_entry(debit=depr_expense_acct, credit=accum_depr_acct, amount)
        GL-->>DES: journal_entry_id
        DES->>AssetRepo: update_accumulated_depreciation(asset_id, amount)
        DES->>AssetRepo: save_depreciation_entry(asset_id, period_id, journal_entry_id)
    end

    DES-->>FARouter: DepreciationSummary{assets_processed, total_depr_amount}
    FARouter-->>FM: 200 { summary }
    FARouter->>NS: notify_fm(DEPRECIATION_POSTED, period_id, summary)
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
- Maintain an explicit traceability matrix for this artifact (`detailed-design/sequence-diagrams.md`):
  - `Requirement ID` → `Business Rule / Event` → `Design Element` (API/schema/diagram component) → `Code Module` → `Test Evidence` → `Control Owner`.
- Lineage metadata minimums: source event ID, transformation ID/version, posting rule version, reconciliation batch ID, and report consumption path.
- Any change touching accounting semantics must include impact analysis across upstream requirements and downstream close/compliance reports.
- Documentation updates are blocking for release when they alter financial behavior, posting logic, or reconciliation outcomes.

### 7) Phase-Specific Implementation Readiness
- Specify schema-level constraints: unique idempotency keys, check constraints for debit/credit signs, immutable posting rows, FK coverage.
- Define API contracts for posting/approval/reconciliation including error codes, retry semantics, and deterministic conflict handling.
- Include state-transition guards for approval and period-close flows to prevent illegal transitions.

### 8) Implementation Checklist for `sequence diagrams`
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


