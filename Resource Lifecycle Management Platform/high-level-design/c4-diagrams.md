# C4 Diagrams

## Context
```mermaid
flowchart LR
  Users --> RLMP
  RLMP --> Cloud
  RLMP --> CMDB
```

## Containers
```mermaid
flowchart TB
  Portal --> API
  API --> Core
  Core --> Workflow
  Core --> DB
```
