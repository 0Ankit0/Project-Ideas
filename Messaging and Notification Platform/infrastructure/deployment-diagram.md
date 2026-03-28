# Deployment Diagram

```mermaid
flowchart TB
  Internet --> WAF --> LB
  LB --> API[API Pods]
  API --> MQ[(Managed Queue)]
  API --> DB[(PostgreSQL)]
  Workers[Worker Pods] --> MQ
  Workers --> Providers[External Providers]
```
