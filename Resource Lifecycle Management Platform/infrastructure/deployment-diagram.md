# Deployment Diagram

```mermaid
flowchart TB
  Users --> WAF --> LB --> API
  API --> DB[(PostgreSQL)]
  API --> MQ[(Queue)]
  Workers --> MQ
  Workers --> Cloud
```
