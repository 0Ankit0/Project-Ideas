# Backend Status Matrix

This matrix documents the implementation status of the Finance Management System backend capabilities.

Status labels:

- `core`: fundamental capability that must be implemented for the system to function
- `standard`: important feature for full production readiness
- `advanced`: enhanced capability for mature financial operations
- `future`: documented but not yet implemented

| Area | Capability | Priority |
|------|------------|----------|
| **Auth & RBAC** | JWT authentication, token refresh, logout | `core` |
| **Auth & RBAC** | Role-based access control with permission matrix | `core` |
| **Auth & RBAC** | MFA / TOTP enforcement for privileged roles (FM, CFO) | `standard` |
| **Auth & RBAC** | Session management and audit log of logins | `standard` |
| **Auth & RBAC** | ERP employee data sync for user provisioning | `advanced` |
| **General Ledger** | Chart of Accounts CRUD with hierarchy support | `core` |
| **General Ledger** | Manual journal entry creation with balanced validation | `core` |
| **General Ledger** | Period management (open, soft-close, hard-close) | `core` |
| **General Ledger** | Trial balance generation for any period | `core` |
| **General Ledger** | Account activity and balance reporting | `core` |
| **General Ledger** | Recurring journal entries with auto-posting | `standard` |
| **General Ledger** | Journal entry reversal | `standard` |
| **General Ledger** | Bank statement import (CSV / bank feed) | `standard` |
| **General Ledger** | Auto-matching of bank statement to GL transactions | `standard` |
| **General Ledger** | Multi-currency journal entries with FX rate stamping | `advanced` |
| **General Ledger** | Period-close checklist with sign-off tracking | `advanced` |
| **Accounts Payable** | Vendor master CRUD with onboarding approval workflow | `core` |
| **Accounts Payable** | Vendor invoice recording with duplicate detection | `core` |
| **Accounts Payable** | 2-way and 3-way PO/receipt matching | `standard` |
| **Accounts Payable** | Invoice approval workflow with threshold routing | `standard` |
| **Accounts Payable** | Payment run creation, approval, and bank file generation | `core` |
| **Accounts Payable** | AP aging report | `standard` |
| **Accounts Payable** | Early payment discount application | `advanced` |
| **Accounts Payable** | Vendor credit note processing | `standard` |
| **Accounts Payable** | 1099/TDS vendor flag and withholding tax tracking | `advanced` |
| **Accounts Receivable** | Customer master CRUD | `core` |
| **Accounts Receivable** | Customer invoice creation with PDF generation | `core` |
| **Accounts Receivable** | Customer payment recording and invoice allocation | `core` |
| **Accounts Receivable** | AR aging report | `standard` |
| **Accounts Receivable** | Automated overdue payment reminders | `standard` |
| **Accounts Receivable** | Recurring invoice generation | `advanced` |
| **Accounts Receivable** | Bad debt write-off with GL entry | `standard` |
| **Accounts Receivable** | Credit limit enforcement | `standard` |
| **Budgeting** | Budget creation per cost center and account | `core` |
| **Budgeting** | Multi-level approval workflow (BM → FM → CFO) | `core` |
| **Budgeting** | Budget version control and revision management | `standard` |
| **Budgeting** | Real-time budget vs. actuals tracking | `core` |
| **Budgeting** | Budget utilization alerts (80%, 95%, breach) | `standard` |
| **Budgeting** | Rolling forecast from actuals run rate | `advanced` |
| **Budgeting** | Top-down budget constraint distribution | `advanced` |
| **Expense Management** | Expense claim submission with receipt upload | `core` |
| **Expense Management** | Per-category policy limit enforcement | `standard` |
| **Expense Management** | Multi-level approval (Dept Head → FM) | `core` |
| **Expense Management** | Mileage claim with configurable rates | `standard` |
| **Expense Management** | Corporate card transaction import and reconciliation | `advanced` |
| **Expense Management** | Reimbursement processing via payroll or direct transfer | `standard` |
| **Payroll** | Employee payroll profile management | `core` |
| **Payroll** | Payroll run initiation and calculation engine | `core` |
| **Payroll** | Statutory deduction calculation (income tax, SS, PF) | `core` |
| **Payroll** | Payroll approval workflow (FM approval before disburse) | `core` |
| **Payroll** | Bank file generation for direct deposit | `core` |
| **Payroll** | Digital pay stub generation (PDF) | `standard` |
| **Payroll** | Payroll GL entry posting | `core` |
| **Payroll** | Year-end tax form generation (W-2, Form 16) | `advanced` |
| **Payroll** | Off-cycle / ad-hoc payroll run support | `standard` |
| **Fixed Assets** | Asset registration with depreciation configuration | `core` |
| **Fixed Assets** | Straight-line and declining balance depreciation | `core` |
| **Fixed Assets** | Automated period depreciation posting | `standard` |
| **Fixed Assets** | Depreciation schedule generation | `standard` |
| **Fixed Assets** | Asset transfer between departments | `standard` |
| **Fixed Assets** | Asset disposal with gain/loss calculation | `standard` |
| **Fixed Assets** | Asset impairment and write-down | `advanced` |
| **Tax Management** | Multi-jurisdiction tax rate configuration | `standard` |
| **Tax Management** | Auto-tax calculation on AP/AR invoices | `standard` |
| **Tax Management** | Tax liability report (input vs. output) | `standard` |
| **Tax Management** | TDS/WHT calculation and certificate generation | `advanced` |
| **Tax Management** | E-filing integration (GSTN, IRS, HMRC) | `future` |
| **Reporting** | Profit & Loss statement | `core` |
| **Reporting** | Balance Sheet | `core` |
| **Reporting** | Cash Flow Statement | `core` |
| **Reporting** | GL detail / general ledger report | `core` |
| **Reporting** | Budget vs. actuals variance report | `standard` |
| **Reporting** | Cost center P&L report | `standard` |
| **Reporting** | Async report job queue with email delivery | `standard` |
| **Reporting** | Multi-entity consolidation | `advanced` |
| **Reporting** | Intercompany elimination | `advanced` |
| **Reporting** | Custom report builder | `advanced` |
| **Compliance** | Append-only audit trail (all mutations) | `core` |
| **Compliance** | Audit log query and export | `core` |
| **Compliance** | Segregation of duties enforcement | `standard` |
| **Compliance** | SoD violation exception report | `standard` |
| **Compliance** | High-value transaction dual-control | `standard` |
| **Compliance** | Period-close sign-off tracking | `standard` |
| **Security** | Field-level encryption for bank account and tax ID | `core` |
| **Security** | Idempotency keys for payment and payroll submission | `core` |
| **Security** | Hashid public identifiers (no integer IDs in API) | `standard` |
| **Notifications** | Approval request and decision emails | `core` |
| **Notifications** | Budget threshold alert (80%, 95%, 100%) | `standard` |
| **Notifications** | Payment confirmation and remittance advice | `standard` |
| **Notifications** | Period-close deadline reminders | `standard` |
| **Notifications** | Real-time WebSocket alerts for budget breaches | `advanced` |
| **Integrations** | FX rate daily feed (Open Exchange / Bloomberg) | `standard` |
| **Integrations** | Bank statement file import (CSV / OFX) | `standard` |
| **Integrations** | ACH / NEFT bank file generation | `core` |
| **Integrations** | ERP / HR employee data sync | `advanced` |
| **Integrations** | Purchase order API sync | `advanced` |
| **Integrations** | Direct bank API integration (Plaid / Open Banking) | `future` |

---

## Implementation Notes

- All monetary values are stored as `NUMERIC(18, 4)` and handled as `Decimal` in Python; `float` is prohibited for financial arithmetic
- The audit log database uses a separate PostgreSQL instance with an INSERT-only application role
- FX rates are fetched daily and cached in Redis; the rate at posting time is stamped on every foreign-currency journal line
- The payroll deduction engine is tax-jurisdiction-aware; the initial implementation covers Indian payroll (PF, PT, TDS) and US payroll (SS, Medicare, Federal/State income tax)
- Report generation for large datasets is queued as Celery tasks with status polling via the `/api/v1/reports/jobs/{id}` endpoint
- E-filing integration for GSTN and IRS remains a future integration; the tax liability report and manual upload workflow are the current path
- Multi-entity consolidation requires all entities to share the same Chart of Accounts structure; intercompany accounts must be configured before consolidation reports are generated

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
- Maintain an explicit traceability matrix for this artifact (`implementation/backend-status-matrix.md`):
  - `Requirement ID` → `Business Rule / Event` → `Design Element` (API/schema/diagram component) → `Code Module` → `Test Evidence` → `Control Owner`.
- Lineage metadata minimums: source event ID, transformation ID/version, posting rule version, reconciliation batch ID, and report consumption path.
- Any change touching accounting semantics must include impact analysis across upstream requirements and downstream close/compliance reports.
- Documentation updates are blocking for release when they alter financial behavior, posting logic, or reconciliation outcomes.

### 7) Phase-Specific Implementation Readiness
- Require feature flags for risky accounting behaviors (auto-post, auto-close, auto-writeoff) with dual-control enablement.
- Instrument critical paths with domain metrics (unposted queue depth, reconciliation break count, close blockers, duplicate suppression).
- Provide migration and rollback playbooks for rule-engine, chart-of-accounts, and tax-rate changes.

### 8) Implementation Checklist for `backend status matrix`
- [ ] Control objectives and success/failure criteria are explicit and testable.
- [ ] Data contracts include mandatory identifiers, timestamps, and provenance fields.
- [ ] Reconciliation logic defines cadence, tolerances, ownership, and escalation.
- [ ] Operational runbooks cover retries, replay, backfill, and close re-certification.
- [ ] Compliance evidence artifacts are named, retained, and linked to control owners.


