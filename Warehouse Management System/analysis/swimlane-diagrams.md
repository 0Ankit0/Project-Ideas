# Swimlane Diagrams

## End-to-End Fulfillment Swimlane
```mermaid
flowchart LR
    subgraph OMS
      O1[Release order]
    end
    subgraph WMS_Planner[WMS Planner]
      W1[Allocate inventory]
      W2[Create wave]
    end
    subgraph Picker
      P1[Execute pick]
      P2[Confirm pick scan]
    end
    subgraph PackStation
      K1[Reconcile carton]
      K2[Print label]
    end
    subgraph Shipping
      S1[Manifest with carrier]
      S2[Confirm handoff]
    end

    O1 --> W1 --> W2 --> P1 --> P2 --> K1 --> K2 --> S1 --> S2
```

## Exception Swimlane (Carrier Failure)
```mermaid
flowchart LR
    subgraph Shipping
      A1[Carrier API timeout]
      A2[Queue shipment pending]
    end
    subgraph Operations
      B1[Review pending queue]
      B2[Retry or reroute carrier]
    end
    subgraph WMS
      C1[Update shipment state]
      C2[Emit customer update]
    end

    A1 --> A2 --> B1 --> B2 --> C1 --> C2
```

## Implementation Notes
- Swimlanes represent ownership boundaries used in on-call routing.
- Each lane handoff must have observable event + correlation id.
