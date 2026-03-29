# C4 Component Diagram

```mermaid
flowchart TB
    subgraph Users
      Picker
      Supervisor
      Planner
      Coordinator
    end

    subgraph WMS[WMS Container]
      BFF[UI BFF]
      Receiving[Receiving Component]
      Allocation[Allocation Component]
      Fulfillment[Fulfillment Component]
      Shipping[Shipping Component]
      Operations[Exception Component]
      Rules[Policy + Rule Engine]
    end

    subgraph Infra
      DB[(PostgreSQL)]
      Bus[(Event Bus)]
      Cache[(Redis)]
      Search[(Operational Search)]
    end

    Picker --> BFF
    Supervisor --> BFF
    Planner --> BFF
    Coordinator --> BFF

    BFF --> Receiving
    BFF --> Allocation
    BFF --> Fulfillment
    BFF --> Shipping
    BFF --> Operations

    Allocation --> Rules
    Operations --> Rules

    WMS --> DB
    WMS --> Bus
    WMS --> Cache
    Bus --> Search
```

## Component Responsibilities
- Receiving: inbound validation + putaway creation.
- Allocation: reservations + wave planning.
- Fulfillment: pick/pack operations.
- Shipping: carrier handoff and tracking confirmation.
- Operations: exception lifecycle and approvals.
