# System Context Diagram

```mermaid
flowchart LR
  Patient --> HAS[Healthcare Appointment System]
  Provider --> HAS
  Reception --> HAS
  HAS --> EHR[Electronic Health Record]
  HAS --> SMS[Reminder Service]
  HAS --> Billing
```
