# State Machine Diagram

```mermaid
stateDiagram-v2
  [*] --> Requested
  Requested --> Confirmed
  Confirmed --> CheckedIn
  CheckedIn --> Completed
  Confirmed --> Cancelled
  Confirmed --> NoShow
  Completed --> [*]
  Cancelled --> [*]
  NoShow --> [*]
```
