# Component Diagram

```mermaid
flowchart LR
  API --> ShipmentService
  API --> TrackingService
  TrackingService --> GeoService
  TrackingService --> NotificationService
  ShipmentService --> DB[(DB)]
  TrackingService --> DB
```
