# Operations

## Day-2 Readiness
- SLO dashboard for availability, latency, and data freshness.
- Runbooks for incident triage, rollback, replay, and backfill.
- Capacity planning based on peak traffic and queue depth trends.

## Incident Lifecycle
1. Detect and classify severity with ownership routing.
2. Contain blast radius and communicate stakeholder impact.
3. Recover service and data consistency.
4. Publish postmortem with corrective actions and deadlines.

## Artifact-Specific Deep Dive: Lifecycle, Reconciliation, Disputes, Fraud, and Ledger Safety

### Why this artifact matters
This document now defines **ops-runbooks** behavior and explicitly maps architecture intent to API contracts, diagrammed flows, and day-2 operations owned by **SRE, Finance Ops**.

### Transaction state transitions required in this artifact
- `INITIATED -> AUTHORIZING -> AUTHORIZED -> CAPTURE_PENDING -> CAPTURED` for card and wallet charges.
- `CAPTURED -> SETTLEMENT_PENDING -> SETTLED` after provider clearing confirmation.
- `CAPTURED|SETTLED -> REFUND_PENDING -> PARTIALLY_REFUNDED|REFUNDED` for merchant-initiated refunds.
- `SETTLED -> CHARGEBACK_OPEN -> CHARGEBACK_WON|CHARGEBACK_LOST` for issuer disputes.
- Each transition MUST include: actor, triggering API/event, timeout, retry policy, and compensating action.

### API contracts this artifact must keep consistent
- `POST /reconciliation/runs`: documented here with required request ids, idempotency keys, and failure reason codes for **ops-runbooks**.
- `GET /reconciliation/discrepancies`: documented here with required request ids, idempotency keys, and failure reason codes for **ops-runbooks**.
- `POST /ledger/reversals`: documented here with required request ids, idempotency keys, and failure reason codes for **ops-runbooks**.
- `GET /risk/cases/{id}`: documented here with required request ids, idempotency keys, and failure reason codes for **ops-runbooks**.
- All mutating calls MUST return `correlation_id`, `idempotency_key`, `previous_state`, `new_state`, and `transition_reason`.

### In-depth flow diagram for operations
```mermaid
sequenceDiagram
    autonumber
    participant Client
    participant API as Payment API
    participant Risk as Risk Service
    participant Ledger
    participant Recon as Reconciliation
    participant Ops as Operations

    Client->>API: create/capture request (ops-runbooks)
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

