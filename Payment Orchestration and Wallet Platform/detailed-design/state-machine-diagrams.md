# State Machine Diagrams

## Payment Transaction Lifecycle
```mermaid
stateDiagram-v2
    [*] --> Created
    Created --> Authorized
    Authorized --> Captured
    Authorized --> Voided
    Captured --> Settled
    Captured --> Refunded
    Authorized --> Failed
    Created --> Failed
    Settled --> [*]
    Refunded --> [*]
```

## Wallet Transfer Lifecycle
```mermaid
stateDiagram-v2
    [*] --> Initiated
    Initiated --> PendingValidation
    PendingValidation --> Posted
    PendingValidation --> Rejected
    Posted --> Completed
    Rejected --> [*]
    Completed --> [*]
```

## Chargeback Lifecycle
```mermaid
stateDiagram-v2
    [*] --> Opened
    Opened --> UnderReview
    UnderReview --> Won
    UnderReview --> Lost
    Lost --> Settled
    Won --> Closed
    Settled --> Closed
    Closed --> [*]
```

## Artifact-Specific Deep Dive: Lifecycle, Reconciliation, Disputes, Fraud, and Ledger Safety

### Why this artifact matters
This document now defines **state-control** behavior and explicitly maps architecture intent to API contracts, diagrammed flows, and day-2 operations owned by **Payments Core, State Manager**.

### Transaction state transitions required in this artifact
- `INITIATED -> AUTHORIZING -> AUTHORIZED -> CAPTURE_PENDING -> CAPTURED` for card and wallet charges.
- `CAPTURED -> SETTLEMENT_PENDING -> SETTLED` after provider clearing confirmation.
- `CAPTURED|SETTLED -> REFUND_PENDING -> PARTIALLY_REFUNDED|REFUNDED` for merchant-initiated refunds.
- `SETTLED -> CHARGEBACK_OPEN -> CHARGEBACK_WON|CHARGEBACK_LOST` for issuer disputes.
- `*_PENDING -> FAILED_TIMEOUT` if callback SLA expires; retry is through idempotent replay only.
- Each transition MUST include: actor, triggering API/event, timeout, retry policy, and compensating action.

### API contracts this artifact must keep consistent
- `GET /payments/{id}`: documented here with required request ids, idempotency keys, and failure reason codes for **state-control**.
- `POST /payments/{id}/void`: documented here with required request ids, idempotency keys, and failure reason codes for **state-control**.
- `POST /payments/{id}/refunds`: documented here with required request ids, idempotency keys, and failure reason codes for **state-control**.
- `POST /ledger/reversals`: documented here with required request ids, idempotency keys, and failure reason codes for **state-control**.
- All mutating calls MUST return `correlation_id`, `idempotency_key`, `previous_state`, `new_state`, and `transition_reason`.

### In-depth flow diagram for state-machine-diagrams
```mermaid
stateDiagram-v2
    [*] --> INITIATED
    INITIATED --> AUTHORIZING
    AUTHORIZING --> AUTHORIZED: risk allow
    AUTHORIZING --> REVIEW_REQUIRED: risk review
    REVIEW_REQUIRED --> AUTHORIZED: analyst approve
    AUTHORIZED --> CAPTURED: capture api
    CAPTURED --> SETTLEMENT_PENDING
    SETTLEMENT_PENDING --> SETTLED: recon match
    CAPTURED --> REFUND_PENDING
    REFUND_PENDING --> REFUNDED
    SETTLED --> CHARGEBACK_OPEN
    CHARGEBACK_OPEN --> CHARGEBACK_WON
    CHARGEBACK_OPEN --> CHARGEBACK_LOST
```

### Reconciliation, dispute/refund, and fraud controls
- Reconciliation: three-way match (ledger vs PSP file vs bank statement) with tolerance thresholds and auto-classification into `timing`, `amount`, `missing`, `duplicate` breaks.
- Disputes/Refunds: evidence chain-of-custody, SLA timers, and automatic ledger reversals when disputes are lost.
- Fraud: pre-auth risk decisioning, post-auth anomaly detection, and payout velocity controls tied to case management.

### Ledger invariants and operational hooks
- Invariants enforced here: double-entry balance, append-only journal, exactly-once posting per business event, and currency-safe postings.
- Operational process: if any invariant fails, move transaction to `OPERATIONS_HOLD`, page on-call + finance, and block payout release until compensating journals are approved.
- Runbooks must include: replay commands, manual override approvals (dual control), and incident-close reconciliation attestation.

