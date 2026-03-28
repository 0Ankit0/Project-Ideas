# System Sequence Diagrams

```mermaid
sequenceDiagram
  autonumber
  actor App
  participant API
  participant Dispatch
  participant Provider
  App->>API: create notification
  API->>Dispatch: queue
  Dispatch->>Provider: deliver
  Provider-->>Dispatch: status callback
  Dispatch-->>API: accepted
```
