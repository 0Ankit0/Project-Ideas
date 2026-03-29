# C4 Code Diagram

```mermaid
flowchart TB
    subgraph Interface
      PaymentController
      WalletController
      RefundController
      ReconciliationController
    end

    subgraph Application
      PaymentAppService
      WalletAppService
      RefundAppService
      ReconciliationAppService
    end

    subgraph Domain
      PaymentAggregate
      WalletAggregate
      RefundAggregate
      LedgerEntryEntity
      RoutingPolicy
    end

    subgraph Infrastructure
      PaymentRepository
      WalletRepository
      PSPGatewayAdapter
      LedgerAdapter
      EventPublisher
      AuditAdapter
    end

    PaymentController --> PaymentAppService --> PaymentAggregate
    WalletController --> WalletAppService --> WalletAggregate
    RefundController --> RefundAppService --> RefundAggregate
    ReconciliationController --> ReconciliationAppService --> LedgerEntryEntity

    PaymentAppService --> RoutingPolicy
    RefundAppService --> RoutingPolicy

    PaymentAppService --> PaymentRepository
    WalletAppService --> WalletRepository
    PaymentAppService --> PSPGatewayAdapter
    ReconciliationAppService --> LedgerAdapter

    PaymentAppService --> EventPublisher
    WalletAppService --> EventPublisher
    RefundAppService --> AuditAdapter
```

## Artifact-Specific Deep Dive: Lifecycle, Reconciliation, Disputes, Fraud, and Ledger Safety

### Why this artifact matters
This document now defines **c4-views** behavior and explicitly maps architecture intent to API contracts, diagrammed flows, and day-2 operations owned by **Architecture, Platform**.

### Transaction state transitions required in this artifact
- `INITIATED -> AUTHORIZING -> AUTHORIZED -> CAPTURE_PENDING -> CAPTURED` for card and wallet charges.
- `CAPTURED -> SETTLEMENT_PENDING -> SETTLED` after provider clearing confirmation.
- `CAPTURED|SETTLED -> REFUND_PENDING -> PARTIALLY_REFUNDED|REFUNDED` for merchant-initiated refunds.
- `SETTLED -> CHARGEBACK_OPEN -> CHARGEBACK_WON|CHARGEBACK_LOST` for issuer disputes.
- Each transition MUST include: actor, triggering API/event, timeout, retry policy, and compensating action.

### API contracts this artifact must keep consistent
- `POST /payments`: documented here with required request ids, idempotency keys, and failure reason codes for **c4-views**.
- `POST /payments/{id}/refunds`: documented here with required request ids, idempotency keys, and failure reason codes for **c4-views**.
- `POST /ledger/journals`: documented here with required request ids, idempotency keys, and failure reason codes for **c4-views**.
- `POST /risk/screen`: documented here with required request ids, idempotency keys, and failure reason codes for **c4-views**.
- All mutating calls MUST return `correlation_id`, `idempotency_key`, `previous_state`, `new_state`, and `transition_reason`.

### In-depth flow diagram for c4-code-diagram
```mermaid
sequenceDiagram
    autonumber
    participant Client
    participant API as Payment API
    participant Risk as Risk Service
    participant Ledger
    participant Recon as Reconciliation
    participant Ops as Operations

    Client->>API: create/capture request (c4-views)
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

