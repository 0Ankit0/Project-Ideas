# System Sequence Diagram

```mermaid
sequenceDiagram
  actor Dispatcher
  participant API
  participant ShipmentSvc
  Dispatcher->>API: create shipment
  API->>ShipmentSvc: persist + publish event
  ShipmentSvc-->>API: shipment id
```
