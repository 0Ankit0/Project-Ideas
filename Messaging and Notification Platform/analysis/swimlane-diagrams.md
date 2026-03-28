# Swimlane Diagrams

## Message Delivery Swimlane
```mermaid
flowchart LR
  subgraph Producer
    A[Publish event]
  end
  subgraph Platform
    B[Template + preference resolution]
    C[Queue dispatch]
  end
  subgraph Provider
    D[Deliver message]
  end
  subgraph Analytics
    E[Store outcome]
  end
  A --> B --> C --> D --> E
```
