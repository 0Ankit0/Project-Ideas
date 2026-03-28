# State Machine Diagram

```mermaid
stateDiagram-v2
  [*] --> Created
  Created --> Assigned
  Assigned --> PickedUp
  PickedUp --> InTransit
  InTransit --> OutForDelivery
  OutForDelivery --> Delivered
  InTransit --> Exception
  Exception --> InTransit
  Delivered --> [*]
```
