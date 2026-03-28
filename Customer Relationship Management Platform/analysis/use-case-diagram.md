# Use Case Diagram

This diagram captures key user goals and supporting CRM capabilities.

```mermaid
flowchart LR
    Rep[Sales Rep]
    Mgr[Sales Manager]
    Ops[RevOps]
    Admin[CRM Admin]
    Int[Integration System]

    UC1((Capture & Qualify Lead))
    UC2((Merge Duplicate Records))
    UC3((Manage Opportunity Pipeline))
    UC4((Log Activities & Follow-ups))
    UC5((Submit Forecast))
    UC6((Approve Forecast))
    UC7((Reassign Territory))
    UC8((Configure Roles & Policies))
    UC9((Sync External Data))

    Rep --> UC1
    Rep --> UC3
    Rep --> UC4
    Rep --> UC5

    Mgr --> UC3
    Mgr --> UC6

    Ops --> UC2
    Ops --> UC7

    Admin --> UC8

    Int --> UC9
```

## Notes
- Forecast and territory actions are managerial/operations controlled.
- Deduplication is explicit to prevent accidental irreversible merges.
