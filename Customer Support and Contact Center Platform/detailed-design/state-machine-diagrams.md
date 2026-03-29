# State Machine Diagrams

## Ticket Lifecycle
```mermaid
stateDiagram-v2
    [*] --> New
    New --> Assigned
    Assigned --> InProgress
    InProgress --> PendingCustomer
    PendingCustomer --> InProgress
    InProgress --> Escalated
    Escalated --> InProgress
    InProgress --> Resolved
    Resolved --> Closed
    PendingCustomer --> Closed: timeout policy
    Closed --> [*]
```

## Conversation Session Lifecycle
```mermaid
stateDiagram-v2
    [*] --> Waiting
    Waiting --> Connected
    Connected --> OnHold
    OnHold --> Connected
    Connected --> Transferred
    Transferred --> Connected
    Connected --> WrappedUp
    WrappedUp --> Ended
    Ended --> [*]
```

## SLA Timer Lifecycle
```mermaid
stateDiagram-v2
    [*] --> Running
    Running --> Warning
    Warning --> Breached
    Running --> Paused: waiting on customer
    Paused --> Running
    Breached --> Mitigated
    Mitigated --> Closed
    Closed --> [*]
```

## State Machine Operational Narrative

```mermaid
stateDiagram-v2
    [*] --> queued
    queued --> assigned: agent_selected
    assigned --> in_progress: agent_accept
    in_progress --> pending_customer: awaiting_reply
    pending_customer --> in_progress: customer_replied
    in_progress --> escalated: sla_risk_or_manual
    escalated --> in_progress: escalation_ack
    in_progress --> resolved: solution_sent
    resolved --> closed: qa_passed
    closed --> in_progress: reopen_policy
```

Transition guards must validate SLA pause semantics, actor authorization, and audit emission before commit.

Operational coverage note: this artifact also specifies omnichannel and incident controls for this design view.
