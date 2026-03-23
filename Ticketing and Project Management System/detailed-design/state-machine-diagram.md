# State Machine Diagram - Ticketing and Project Management System

## Ticket Lifecycle

```mermaid
stateDiagram-v2
    [*] --> new
    new --> awaiting_clarification
    new --> triaged
    awaiting_clarification --> triaged
    triaged --> assigned
    assigned --> in_progress
    in_progress --> blocked
    blocked --> in_progress
    in_progress --> ready_for_qa
    ready_for_qa --> reopened
    reopened --> in_progress
    ready_for_qa --> closed
    closed --> reopened
```

## Milestone Lifecycle

```mermaid
stateDiagram-v2
    [*] --> draft
    draft --> baselined
    baselined --> in_progress
    in_progress --> at_risk
    at_risk --> in_progress
    in_progress --> completed
    baselined --> cancelled
    at_risk --> replanning
    replanning --> baselined
```
