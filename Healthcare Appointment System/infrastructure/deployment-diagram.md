# Deployment Diagram

```mermaid
flowchart TB
  Internet --> LB --> API
  API --> DB[(PostgreSQL)]
  API --> MQ[(Queue)]
  Workers --> MQ
  Workers --> ReminderProviders
```
