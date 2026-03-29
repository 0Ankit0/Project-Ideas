# C4 Code Diagram

This document provides a code-level map for shipment lifecycle and tracking event processing.

## Code-Level Structure
```mermaid
flowchart TB
  subgraph Interface
    ShipmentController
    TrackingController
    ExceptionController
  end

  subgraph Application
    ShipmentAppService
    TrackingAppService
    ETAAppService
    ExceptionAppService
  end

  subgraph Domain
    ShipmentAggregate
    TrackingEventEntity
    RoutePolicy
    ExceptionCase
  end

  subgraph Infrastructure
    ShipmentRepository
    TrackingRepository
    MapsAdapter
    NotificationAdapter
    EventPublisher
  end

  ShipmentController --> ShipmentAppService --> ShipmentAggregate
  TrackingController --> TrackingAppService --> TrackingEventEntity
  ExceptionController --> ExceptionAppService --> ExceptionCase
  TrackingAppService --> ETAAppService --> RoutePolicy
  ShipmentAppService --> ShipmentRepository
  TrackingAppService --> TrackingRepository
  ETAAppService --> MapsAdapter
  ExceptionAppService --> NotificationAdapter
  TrackingAppService --> EventPublisher
```

## Critical Runtime Sequence: Tracking Update
```mermaid
sequenceDiagram
  autonumber
  actor Driver
  participant API as TrackingController
  participant APP as TrackingAppService
  participant ETA as ETAAppService
  participant NOTIFY as NotificationAdapter

  Driver->>API: post location/status
  API->>APP: validate update
  APP->>ETA: recompute ETA
  ETA-->>APP: updated ETA
  APP->>NOTIFY: push customer update
  APP-->>API: accepted
```

## Notes
- Preserve immutable tracking history for audit and dispute handling.
- Recompute ETA asynchronously on bursty update streams when needed.
