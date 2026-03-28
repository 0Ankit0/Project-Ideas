# Architecture Diagram

```mermaid
flowchart TB
  Portal --> API
  API --> Core[Lifecycle Services]
  Core --> Workflow
  Core --> DB
  Workflow --> Cloud
  Workflow --> CMDB
  Core --> FinOps
```
