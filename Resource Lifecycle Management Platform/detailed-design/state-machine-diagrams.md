# State Machine Diagrams

```mermaid
stateDiagram-v2
  [*] --> Requested
  Requested --> Approved
  Approved --> Provisioning
  Provisioning --> Active
  Active --> Suspended
  Suspended --> Active
  Active --> Decommissioning
  Decommissioning --> Retired
  Retired --> [*]
```
