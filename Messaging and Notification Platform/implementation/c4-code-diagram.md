# C4 Code Diagram

```mermaid
flowchart TB
  NotificationController --> NotificationAppService --> NotificationAggregate
  NotificationAppService --> TemplateRepository
  NotificationAppService --> RecipientRepository
  NotificationAppService --> DispatchAdapter
  NotificationAppService --> EventPublisher
```
