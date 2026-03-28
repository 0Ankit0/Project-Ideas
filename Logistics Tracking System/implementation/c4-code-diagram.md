# C4 Code Diagram

```mermaid
flowchart TB
  ShipmentController --> ShipmentAppService --> ShipmentAggregate
  TrackingController --> TrackingAppService --> TrackingEventEntity
  TrackingAppService --> TrackingRepository
  TrackingAppService --> NotificationAdapter
```
