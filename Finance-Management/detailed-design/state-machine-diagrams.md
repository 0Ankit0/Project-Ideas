# State Machine Diagrams

## Overview
Entity state transition diagrams for the key financial documents and workflows in the Finance Management System.

---

## Vendor Invoice State Machine

```mermaid
stateDiagram-v2
    [*] --> DRAFT : Accountant creates invoice

    DRAFT --> SUBMITTED : Accountant submits for approval
    DRAFT --> VOID : Accountant voids before submission

    SUBMITTED --> MATCH_EXCEPTION : 3-way match variance exceeds tolerance
    SUBMITTED --> PENDING_FM_APPROVAL : Match passes, amount above threshold
    SUBMITTED --> APPROVED : Match passes, amount below threshold (auto-approved)

    MATCH_EXCEPTION --> PENDING_FM_APPROVAL : FM overrides exception
    MATCH_EXCEPTION --> VOID : FM rejects exception

    PENDING_FM_APPROVAL --> APPROVED : Finance Manager approves
    PENDING_FM_APPROVAL --> DRAFT : Finance Manager returns with comments

    APPROVED --> SCHEDULED : Added to payment run
    SCHEDULED --> PARTIALLY_PAID : Partial payment applied
    SCHEDULED --> PAID : Full payment received and cleared

    PARTIALLY_PAID --> PAID : Remaining balance paid

    APPROVED --> VOID : Finance Manager voids approved invoice
    PAID --> [*]
    VOID --> [*]
```

---

## Customer Invoice State Machine

```mermaid
stateDiagram-v2
    [*] --> DRAFT : Accountant creates invoice

    DRAFT --> ISSUED : Accountant sends to customer
    DRAFT --> VOID : Cancelled before sending

    ISSUED --> PARTIALLY_PAID : Partial payment recorded
    ISSUED --> PAID : Full payment received
    ISSUED --> OVERDUE : Due date passes without payment

    PARTIALLY_PAID --> PAID : Remaining balance collected
    PARTIALLY_PAID --> OVERDUE : Due date passes

    OVERDUE --> PAID : Late payment received
    OVERDUE --> WRITTEN_OFF : CFO approves bad debt write-off

    PAID --> [*]
    WRITTEN_OFF --> [*]
    VOID --> [*]
```

---

## Budget State Machine

```mermaid
stateDiagram-v2
    [*] --> DRAFT : Budget Manager creates budget

    DRAFT --> PENDING_FM_REVIEW : Submitted for Finance Manager review
    DRAFT --> [*] : Deleted as draft

    PENDING_FM_REVIEW --> DRAFT : Returned with comments
    PENDING_FM_REVIEW --> PENDING_CFO_APPROVAL : Finance Manager approves

    PENDING_CFO_APPROVAL --> PENDING_FM_REVIEW : CFO returns to Finance Manager
    PENDING_CFO_APPROVAL --> APPROVED : CFO approves

    APPROVED --> ACTIVE : Fiscal period starts
    ACTIVE --> REVISED : Budget revision submitted
    REVISED --> PENDING_FM_REVIEW : Revision routed for re-approval
    ACTIVE --> CLOSED : Fiscal period ends

    CLOSED --> [*]
```

---

## Expense Claim State Machine

```mermaid
stateDiagram-v2
    [*] --> DRAFT : Employee creates claim

    DRAFT --> SUBMITTED : Employee submits claim
    DRAFT --> [*] : Employee deletes draft

    SUBMITTED --> PENDING_DEPT_APPROVAL : Routed to Department Head

    PENDING_DEPT_APPROVAL --> DRAFT : Rejected – returned to employee
    PENDING_DEPT_APPROVAL --> PENDING_FM_APPROVAL : Approved by Dept Head (high-value)
    PENDING_DEPT_APPROVAL --> APPROVED : Approved by Dept Head (below threshold)

    PENDING_FM_APPROVAL --> DRAFT : Rejected – returned to employee
    PENDING_FM_APPROVAL --> APPROVED : Finance Manager approves

    APPROVED --> QUEUED_FOR_PAYMENT : Added to reimbursement batch
    QUEUED_FOR_PAYMENT --> PAID : Reimbursement transferred to employee

    PAID --> [*]
```

---

## Payroll Run State Machine

```mermaid
stateDiagram-v2
    [*] --> DRAFT : Accountant initiates payroll run

    DRAFT --> CALCULATED : Calculations completed
    DRAFT --> CANCELLED : Cancelled before calculation

    CALCULATED --> PENDING_APPROVAL : Submitted to Finance Manager

    PENDING_APPROVAL --> CALCULATED : Returned for corrections
    PENDING_APPROVAL --> APPROVED : Finance Manager approves

    APPROVED --> SUBMITTED_TO_BANK : Bank file submitted

    SUBMITTED_TO_BANK --> DISBURSED : Bank confirms clearance
    SUBMITTED_TO_BANK --> PARTIALLY_FAILED : Some disbursements failed

    PARTIALLY_FAILED --> DISBURSED : Failed entries reprocessed
    PARTIALLY_FAILED --> FAILED : All retries exhausted

    DISBURSED --> [*]
    FAILED --> [*]
    CANCELLED --> [*]
```

---

## Accounting Period State Machine

```mermaid
stateDiagram-v2
    [*] --> OPEN : Period created and activated

    OPEN --> SOFT_CLOSED : Finance Manager initiates soft-close
    note right of SOFT_CLOSED : Restricted posting\nAdjustments require approval

    SOFT_CLOSED --> OPEN : Reopened for corrections (rare)
    SOFT_CLOSED --> HARD_CLOSED : CFO approves final close

    note right of HARD_CLOSED : No postings allowed\nFully locked

    HARD_CLOSED --> [*]
```

---

## Fixed Asset State Machine

```mermaid
stateDiagram-v2
    [*] --> REGISTERED : Asset acquired and registered

    REGISTERED --> IN_SERVICE : Asset placed in service (depreciation begins)

    IN_SERVICE --> TRANSFERRED : Asset transferred to another dept/location
    TRANSFERRED --> IN_SERVICE : Transfer complete

    IN_SERVICE --> IMPAIRED : Write-down applied
    IMPAIRED --> IN_SERVICE : Impairment reversed

    IN_SERVICE --> FULLY_DEPRECIATED : Net book value reaches residual value
    FULLY_DEPRECIATED --> DISPOSED : Asset sold or scrapped
    IN_SERVICE --> DISPOSED : Early disposal

    DISPOSED --> [*]
```

---

## Payment Run State Machine

```mermaid
stateDiagram-v2
    [*] --> PENDING_APPROVAL : Finance Manager creates payment run

    PENDING_APPROVAL --> APPROVED : Finance Manager approves run
    PENDING_APPROVAL --> CANCELLED : Cancelled before approval

    APPROVED --> BANK_FILE_GENERATED : Bank transfer file generated

    BANK_FILE_GENERATED --> SUBMITTED_TO_BANK : File submitted to banking system
    BANK_FILE_GENERATED --> CANCELLED : Cancelled after file generation

    SUBMITTED_TO_BANK --> CLEARED : Bank confirms all payments cleared
    SUBMITTED_TO_BANK --> PARTIALLY_FAILED : Some payments failed
    SUBMITTED_TO_BANK --> FAILED : All payments failed

    PARTIALLY_FAILED --> CLEARED : Failed payments re-initiated and cleared

    CLEARED --> [*]
    FAILED --> [*]
    CANCELLED --> [*]
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
- Maintain an explicit traceability matrix for this artifact (`detailed-design/state-machine-diagrams.md`):
  - `Requirement ID` → `Business Rule / Event` → `Design Element` (API/schema/diagram component) → `Code Module` → `Test Evidence` → `Control Owner`.
- Lineage metadata minimums: source event ID, transformation ID/version, posting rule version, reconciliation batch ID, and report consumption path.
- Any change touching accounting semantics must include impact analysis across upstream requirements and downstream close/compliance reports.
- Documentation updates are blocking for release when they alter financial behavior, posting logic, or reconciliation outcomes.

### 7) Phase-Specific Implementation Readiness
- Specify schema-level constraints: unique idempotency keys, check constraints for debit/credit signs, immutable posting rows, FK coverage.
- Define API contracts for posting/approval/reconciliation including error codes, retry semantics, and deterministic conflict handling.
- Include state-transition guards for approval and period-close flows to prevent illegal transitions.

### 8) Implementation Checklist for `state machine diagrams`
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


