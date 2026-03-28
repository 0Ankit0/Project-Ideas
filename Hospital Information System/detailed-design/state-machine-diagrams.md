# State Machine Diagrams

## Appointment Lifecycle
```mermaid
stateDiagram-v2
    [*] --> Requested
    Requested --> Confirmed
    Confirmed --> CheckedIn
    CheckedIn --> InProgress
    InProgress --> Completed
    Requested --> Cancelled
    Confirmed --> Cancelled
    Confirmed --> NoShow
    Completed --> [*]
    Cancelled --> [*]
    NoShow --> [*]
```

## Admission Lifecycle
```mermaid
stateDiagram-v2
    [*] --> Planned
    Planned --> Admitted
    Admitted --> Transferred
    Transferred --> Admitted
    Admitted --> Discharged
    Admitted --> Expired
    Discharged --> [*]
    Expired --> [*]
```

## Claim Lifecycle
```mermaid
stateDiagram-v2
    [*] --> Draft
    Draft --> Submitted
    Submitted --> Accepted
    Submitted --> Rejected
    Accepted --> Paid
    Accepted --> PartiallyPaid
    Accepted --> Denied
    Rejected --> Draft
    Paid --> [*]
    Denied --> [*]
```
