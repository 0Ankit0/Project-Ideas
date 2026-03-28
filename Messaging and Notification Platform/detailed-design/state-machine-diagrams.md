# State Machine Diagrams

```mermaid
stateDiagram-v2
  [*] --> Queued
  Queued --> Processing
  Processing --> Delivered
  Processing --> Failed
  Failed --> Retrying
  Retrying --> Processing
  Failed --> DeadLettered
  Delivered --> [*]
  DeadLettered --> [*]
```
