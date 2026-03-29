# Use Case Descriptions

## Purpose
Define the use case descriptions artifacts for the **Payment Orchestration and Wallet Platform** with implementation-ready detail.

## Domain Context
- Domain: Payments
- Core entities: Payment Intent, Authorization, Capture, Wallet Account, Ledger Entry, Settlement Batch, Payout
- Primary workflows: provider routing decisioning, authorization and capture lifecycle, wallet posting and balance controls, settlement and reconciliation, refunds, disputes, and payout releases

## Key Design Decisions
- Enforce idempotency and correlation IDs for all mutating operations.
- Persist immutable audit events for critical lifecycle transitions.
- Separate online transaction paths from async reconciliation/repair paths.

## Reliability and Compliance
- Define SLOs and error budgets for user-facing operations.
- Include RBAC, least-privilege service identities, and full audit trails.
- Provide runbooks for degraded mode, replay, and backfill operations.


## Analysis Notes
- Capture alternate/error flows for: provider routing decisioning, authorization and capture lifecycle, wallet posting and balance controls.
- Distinguish synchronous decision points vs asynchronous compensation.
- Track external dependencies through channels: checkout API, webhooks, ops console.

## Artifact-Specific Deep Dive: Lifecycle, Reconciliation, Disputes, Fraud, and Ledger Safety

### Why this artifact matters
This document now defines **use-case-analysis** behavior and explicitly maps architecture intent to API contracts, diagrammed flows, and day-2 operations owned by **Product, Business Analyst**.

### Transaction state transitions required in this artifact
- `INITIATED -> AUTHORIZING -> AUTHORIZED -> CAPTURE_PENDING -> CAPTURED` for card and wallet charges.
- `CAPTURED -> SETTLEMENT_PENDING -> SETTLED` after provider clearing confirmation.
- `CAPTURED|SETTLED -> REFUND_PENDING -> PARTIALLY_REFUNDED|REFUNDED` for merchant-initiated refunds.
- `SETTLED -> CHARGEBACK_OPEN -> CHARGEBACK_WON|CHARGEBACK_LOST` for issuer disputes.
- Each transition MUST include: actor, triggering API/event, timeout, retry policy, and compensating action.

### API contracts this artifact must keep consistent
- `POST /payments`: documented here with required request ids, idempotency keys, and failure reason codes for **use-case-analysis**.
- `GET /payments/{id}`: documented here with required request ids, idempotency keys, and failure reason codes for **use-case-analysis**.
- `POST /payments/{id}/refunds`: documented here with required request ids, idempotency keys, and failure reason codes for **use-case-analysis**.
- `GET /reconciliation/runs/{runId}`: documented here with required request ids, idempotency keys, and failure reason codes for **use-case-analysis**.
- All mutating calls MUST return `correlation_id`, `idempotency_key`, `previous_state`, `new_state`, and `transition_reason`.

### In-depth flow diagram for use-case-descriptions
```mermaid
sequenceDiagram
    autonumber
    participant Client
    participant API as Payment API
    participant Risk as Risk Service
    participant Ledger
    participant Recon as Reconciliation
    participant Ops as Operations

    Client->>API: create/capture request (use-case-analysis)
    API->>Risk: score transaction
    Risk-->>API: ALLOW/REVIEW/DECLINE
    API->>Ledger: post provisional journal
    Ledger-->>API: journal_id + invariant check
    API-->>Client: state update + correlation_id
    API->>Recon: publish settlement candidate
    Recon-->>Ops: discrepancy or success signal
```

### Reconciliation, dispute/refund, and fraud controls
- Reconciliation: three-way match (ledger vs PSP file vs bank statement) with tolerance thresholds and auto-classification into `timing`, `amount`, `missing`, `duplicate` breaks.
- Disputes/Refunds: evidence chain-of-custody, SLA timers, and automatic ledger reversals when disputes are lost.
- Fraud: pre-auth risk decisioning, post-auth anomaly detection, and payout velocity controls tied to case management.

### Ledger invariants and operational hooks
- Invariants enforced here: double-entry balance, append-only journal, exactly-once posting per business event, and currency-safe postings.
- Operational process: if any invariant fails, move transaction to `OPERATIONS_HOLD`, page on-call + finance, and block payout release until compensating journals are approved.
- Runbooks must include: replay commands, manual override approvals (dual control), and incident-close reconciliation attestation.

