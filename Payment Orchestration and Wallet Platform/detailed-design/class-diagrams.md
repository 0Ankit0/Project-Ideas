# Class Diagrams

```mermaid
classDiagram
    class Merchant {
      +UUID id
      +String name
      +String mcc
      +MerchantStatus status
    }

    class CustomerWallet {
      +UUID id
      +UUID customerId
      +Money availableBalance
      +Money reservedBalance
      +credit(amount)
      +debit(amount)
    }

    class PaymentIntent {
      +UUID id
      +UUID merchantId
      +UUID customerId
      +Money amount
      +Currency currency
      +PaymentStatus status
      +authorize()
      +capture()
      +refund()
    }

    class PaymentRoute {
      +UUID id
      +String strategy
      +String pspCode
      +Integer priority
      +select()
    }

    class LedgerEntry {
      +UUID id
      +UUID transactionId
      +String accountCode
      +Money debit
      +Money credit
      +post()
    }

    class Refund {
      +UUID id
      +UUID paymentIntentId
      +Money amount
      +RefundStatus status
      +submit()
    }

    class ChargebackCase {
      +UUID id
      +UUID paymentIntentId
      +String reasonCode
      +ChargebackStatus status
      +open()
      +resolve()
    }

    Merchant "1" --> "many" PaymentIntent
    PaymentIntent "1" --> "many" LedgerEntry
    PaymentIntent "1" --> "many" Refund
    PaymentIntent "1" --> "0..many" ChargebackCase
    CustomerWallet "1" --> "many" LedgerEntry
    PaymentIntent "many" --> "1" PaymentRoute : routed by
```

## Artifact-Specific Deep Dive: Lifecycle, Reconciliation, Disputes, Fraud, and Ledger Safety

### Why this artifact matters
This document now defines **class-design** behavior and explicitly maps architecture intent to API contracts, diagrammed flows, and day-2 operations owned by **Backend Eng, Architecture**.

### Transaction state transitions required in this artifact
- `INITIATED -> AUTHORIZING -> AUTHORIZED -> CAPTURE_PENDING -> CAPTURED` for card and wallet charges.
- `CAPTURED -> SETTLEMENT_PENDING -> SETTLED` after provider clearing confirmation.
- `CAPTURED|SETTLED -> REFUND_PENDING -> PARTIALLY_REFUNDED|REFUNDED` for merchant-initiated refunds.
- `SETTLED -> CHARGEBACK_OPEN -> CHARGEBACK_WON|CHARGEBACK_LOST` for issuer disputes.
- Each transition MUST include: actor, triggering API/event, timeout, retry policy, and compensating action.

### API contracts this artifact must keep consistent
- `POST /payments`: documented here with required request ids, idempotency keys, and failure reason codes for **class-design**.
- `POST /payments/{id}/capture`: documented here with required request ids, idempotency keys, and failure reason codes for **class-design**.
- `POST /ledger/journals`: documented here with required request ids, idempotency keys, and failure reason codes for **class-design**.
- `POST /ledger/reversals`: documented here with required request ids, idempotency keys, and failure reason codes for **class-design**.
- All mutating calls MUST return `correlation_id`, `idempotency_key`, `previous_state`, `new_state`, and `transition_reason`.

### In-depth flow diagram for class-diagrams
```mermaid
sequenceDiagram
    autonumber
    participant Client
    participant API as Payment API
    participant Risk as Risk Service
    participant Ledger
    participant Recon as Reconciliation
    participant Ops as Operations

    Client->>API: create/capture request (class-design)
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

