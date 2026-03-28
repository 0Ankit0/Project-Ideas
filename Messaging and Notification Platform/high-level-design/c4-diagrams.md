# C4 Diagrams

## Context
```mermaid
flowchart LR
  Apps --> Platform[Messaging Platform]
  Platform --> Providers[Email/SMS/Push]
  Platform --> Analytics
```

## Containers
```mermaid
flowchart TB
  API --> Core
  Core --> Queue
  Queue --> Workers
  Core --> DB
```
