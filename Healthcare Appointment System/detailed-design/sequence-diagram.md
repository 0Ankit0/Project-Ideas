# Sequence Diagram

```mermaid
sequenceDiagram
  actor Patient
  participant Portal
  participant API
  participant Scheduling
  Patient->>Portal: choose slot
  Portal->>API: create appointment
  API->>Scheduling: reserve slot
  Scheduling-->>API: confirmation
  API-->>Portal: success
```
