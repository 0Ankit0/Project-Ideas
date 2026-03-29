# Data Flow Diagrams

## DFD Level 0 - Fulfillment Data Flow
```mermaid
flowchart LR
    OMS[OMS Orders] --> P1[Allocate + Wave]
    P1 --> D1[(Reservations)]
    P1 --> P2[Pick Execution]
    P2 --> D2[(Pick Confirmations)]
    P2 --> P3[Pack Reconciliation]
    P3 --> D3[(Pack Sessions)]
    P3 --> P4[Ship Confirmation]
    P4 --> D4[(Shipments)]
    P4 --> OMS
```

## DFD Level 1 - Receiving Flow
```mermaid
flowchart LR
    ERP[ASN/PO] --> R1[Receive Validation]
    Scanner[RF Scan] --> R1
    R1 --> D5[(Receipt Ledger)]
    R1 --> R2[Putaway Planner]
    R2 --> D6[(Putaway Tasks)]
    R1 --> EX[Exception Case Manager]
```

## Data Controls
- All writes carry `correlation_id`, `actor_id`, and reason metadata.
- Outbox ensures event publication after commit only.
- Reconciliation jobs compare ledger totals with balances.
