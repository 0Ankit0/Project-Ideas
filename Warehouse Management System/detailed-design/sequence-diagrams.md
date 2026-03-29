# Sequence Diagrams

## Wave Creation and Task Dispatch
```mermaid
sequenceDiagram
    autonumber
    participant OMS as OMS
    participant API as WMS API
    participant ALLOC as Allocation Service
    participant WAVE as Wave Service
    participant TASK as Task Service

    OMS->>API: push released orders
    API->>ALLOC: reserve inventory
    ALLOC->>WAVE: create wave plan
    WAVE->>TASK: generate pick tasks
    TASK-->>API: task ids + queue
    API-->>OMS: wave accepted
```

**Critical Guarantees**
- Allocation reservation and wave creation are linked by correlation id.
- Duplicate OMS release message must return same `wave_id` (idempotent).

## Goods Receipt with Discrepancy
```mermaid
sequenceDiagram
    autonumber
    participant Scanner
    participant API as Receiving API
    participant REC as Receiving Service
    participant INV as Inventory Service
    participant QA as Exception Queue

    Scanner->>API: receive pallet scan
    API->>REC: validate ASN line
    alt mismatch
      REC->>QA: create discrepancy case
    end
    REC->>INV: post received quantity
    INV-->>API: updated stock
    API-->>Scanner: receipt confirmation
```

## Pick -> Pack -> Ship with Carrier Failure Path
```mermaid
sequenceDiagram
    autonumber
    participant Picker
    participant PickAPI
    participant PackAPI
    participant ShipAPI
    participant Carrier
    participant EXQ as Exception Queue

    Picker->>PickAPI: confirm pick
    PickAPI->>PackAPI: mark line pick-complete
    PackAPI->>PackAPI: reconcile carton
    PackAPI->>ShipAPI: request shipment confirmation
    ShipAPI->>Carrier: create manifest + label
    alt carrier timeout
      ShipAPI->>EXQ: enqueue shipping exception
      ShipAPI-->>PackAPI: shipment pending
    else success
      Carrier-->>ShipAPI: tracking + label
      ShipAPI-->>PackAPI: shipment confirmed
    end
```

## Implementation Guidance
- Use outbox relay between command DB and event bus.
- Ensure retries are safe via business idempotency, not transport dedupe alone.
- Persist external request/response hash for carrier disputes.
