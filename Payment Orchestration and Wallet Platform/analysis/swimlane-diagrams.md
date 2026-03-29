# Swimlane Diagrams

## Payment Authorization Swimlane
```mermaid
flowchart LR
    subgraph Merchant
      A[Create checkout payment]
    end

    subgraph Platform[Orchestration Platform]
      B[Risk + routing]
      C[Build auth request]
      D[Persist transaction]
    end

    subgraph PSP
      E[Authorize transaction]
    end

    subgraph Ledger
      F[Post accounting entries]
    end

    A --> B --> C --> E --> D --> F
```

## Wallet Transfer Swimlane
```mermaid
flowchart LR
    subgraph Sender
      A[Initiate transfer]
    end

    subgraph Wallet[Wallet Service]
      B[Validate balance/limits]
      C[Debit sender wallet]
      D[Credit receiver wallet]
    end

    subgraph Receiver
      E[Receive funds notification]
    end

    A --> B --> C --> D --> E
```

## Artifact-Specific Deep Dive: Lifecycle, Reconciliation, Disputes, Fraud, and Ledger Safety

### Why this artifact matters
This document now defines **swimlane-analysis** behavior and explicitly maps architecture intent to API contracts, diagrammed flows, and day-2 operations owned by **Business Analyst, Architecture**.

### Transaction state transitions required in this artifact
- `INITIATED -> AUTHORIZING -> AUTHORIZED -> CAPTURE_PENDING -> CAPTURED` for card and wallet charges.
- `CAPTURED -> SETTLEMENT_PENDING -> SETTLED` after provider clearing confirmation.
- `CAPTURED|SETTLED -> REFUND_PENDING -> PARTIALLY_REFUNDED|REFUNDED` for merchant-initiated refunds.
- `SETTLED -> CHARGEBACK_OPEN -> CHARGEBACK_WON|CHARGEBACK_LOST` for issuer disputes.
- Each transition MUST include: actor, triggering API/event, timeout, retry policy, and compensating action.

### API contracts this artifact must keep consistent
- `POST /payments`: documented here with required request ids, idempotency keys, and failure reason codes for **swimlane-analysis**.
- `POST /risk/screen`: documented here with required request ids, idempotency keys, and failure reason codes for **swimlane-analysis**.
- `POST /ledger/journals`: documented here with required request ids, idempotency keys, and failure reason codes for **swimlane-analysis**.
- `POST /reconciliation/runs`: documented here with required request ids, idempotency keys, and failure reason codes for **swimlane-analysis**.
- All mutating calls MUST return `correlation_id`, `idempotency_key`, `previous_state`, `new_state`, and `transition_reason`.

### In-depth flow diagram for swimlane-diagrams
```mermaid
sequenceDiagram
    autonumber
    participant Client
    participant API as Payment API
    participant Risk as Risk Service
    participant Ledger
    participant Recon as Reconciliation
    participant Ops as Operations

    Client->>API: create/capture request (swimlane-analysis)
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

