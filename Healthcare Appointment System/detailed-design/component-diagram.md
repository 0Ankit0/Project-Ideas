# Component Diagram

```mermaid
flowchart LR
  API --> SchedulingService
  API --> AvailabilityService
  SchedulingService --> ReminderService
  SchedulingService --> EHRAdapter
  SchedulingService --> DB[(DB)]
```
