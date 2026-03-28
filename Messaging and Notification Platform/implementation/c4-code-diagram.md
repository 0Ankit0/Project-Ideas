# C4 Code Diagram

This implementation view details the notification dispatch pipeline and reliability boundaries.

## Code-Level Structure
```mermaid
flowchart TB
  subgraph Interface
    NotificationController
    TemplateController
    PreferenceController
  end

  subgraph Application
    NotificationAppService
    TemplateAppService
    PreferenceAppService
    DispatchWorkerService
  end

  subgraph Domain
    NotificationAggregate
    TemplateEntity
    RecipientPreference
    DeliveryPolicy
  end

  subgraph Infrastructure
    NotificationRepository
    TemplateRepository
    QueueAdapter
    ChannelAdapter
    MetricsAdapter
    EventPublisher
  end

  NotificationController --> NotificationAppService --> NotificationAggregate
  TemplateController --> TemplateAppService --> TemplateEntity
  PreferenceController --> PreferenceAppService --> RecipientPreference
  NotificationAppService --> DispatchWorkerService --> DeliveryPolicy
  NotificationAppService --> NotificationRepository
  TemplateAppService --> TemplateRepository
  DispatchWorkerService --> QueueAdapter
  DispatchWorkerService --> ChannelAdapter
  DispatchWorkerService --> MetricsAdapter
  NotificationAppService --> EventPublisher
```

## Critical Runtime Sequence: Notification Dispatch
```mermaid
sequenceDiagram
  autonumber
  participant API as NotificationController
  participant APP as NotificationAppService
  participant Q as QueueAdapter
  participant W as DispatchWorkerService
  participant CH as ChannelAdapter

  API->>APP: create notification
  APP->>Q: enqueue job
  Q->>W: deliver queued job
  W->>CH: send via channel provider
  CH-->>W: delivery response
  W-->>APP: outcome recorded
```

## Notes
- Use idempotent delivery keys for retry safety.
- Separate synchronous acceptance path from asynchronous channel dispatch.
