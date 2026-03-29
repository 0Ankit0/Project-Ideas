# Sequence Diagrams

## Auth + Capture with Orchestration
```mermaid
sequenceDiagram
    autonumber
    participant M as Merchant
    participant API as Payments API
    participant ORCH as Orchestration Service
    participant RISK as Risk Engine
    participant PSP as PSP Adapter
    participant LEDGER as Ledger Service

    M->>API: POST /v1/payments
    API->>ORCH: create payment intent
    ORCH->>RISK: evaluate transaction
    RISK-->>ORCH: approve
    ORCH->>PSP: authorize + capture
    PSP-->>ORCH: success
    ORCH->>LEDGER: post entries
    ORCH-->>API: payment succeeded
    API-->>M: 201 + status
```

## Wallet Transfer
```mermaid
sequenceDiagram
    autonumber
    participant U as User App
    participant API as Wallet API
    participant WAL as Wallet Service
    participant LEDGER as Ledger

    U->>API: POST /v1/wallet/transfers
    API->>WAL: validate + transfer
    WAL->>LEDGER: post double-entry movement
    LEDGER-->>WAL: committed
    WAL-->>API: transfer complete
    API-->>U: success
```

## Artifact-Specific Deep Dive: Lifecycle, Reconciliation, Disputes, Fraud, and Ledger Safety

### Why this artifact matters
This document now defines **sequence-orchestration** behavior and explicitly maps architecture intent to API contracts, diagrammed flows, and day-2 operations owned by **Payments API, Gateway Adapter, Ledger, Risk Engine**.

### Transaction state transitions required in this artifact
- `INITIATED -> AUTHORIZING -> AUTHORIZED -> CAPTURE_PENDING -> CAPTURED` for card and wallet charges.
- `CAPTURED -> SETTLEMENT_PENDING -> SETTLED` after provider clearing confirmation.
- `CAPTURED|SETTLED -> REFUND_PENDING -> PARTIALLY_REFUNDED|REFUNDED` for merchant-initiated refunds.
- `SETTLED -> CHARGEBACK_OPEN -> CHARGEBACK_WON|CHARGEBACK_LOST` for issuer disputes.
- Each transition MUST include: actor, triggering API/event, timeout, retry policy, and compensating action.

### API contracts this artifact must keep consistent
- `POST /payments`: documented here with required request ids, idempotency keys, and failure reason codes for **sequence-orchestration**.
- `POST /payments/{id}/authorize`: documented here with required request ids, idempotency keys, and failure reason codes for **sequence-orchestration**.
- `POST /payments/{id}/capture`: documented here with required request ids, idempotency keys, and failure reason codes for **sequence-orchestration**.
- `POST /ledger/journals`: documented here with required request ids, idempotency keys, and failure reason codes for **sequence-orchestration**.
- All mutating calls MUST return `correlation_id`, `idempotency_key`, `previous_state`, `new_state`, and `transition_reason`.

### In-depth flow diagram for sequence-diagrams
```mermaid
sequenceDiagram
    autonumber
    participant Client
    participant API as Payment API
    participant Risk as Risk Service
    participant Ledger
    participant Recon as Reconciliation
    participant Ops as Operations

    Client->>API: create/capture request (sequence-orchestration)
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

