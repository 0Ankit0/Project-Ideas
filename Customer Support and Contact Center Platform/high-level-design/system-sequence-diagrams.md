# System Sequence Diagrams

## System Sequence: Agent Resolves Ticket
```mermaid
sequenceDiagram
    autonumber
    actor Agent
    participant UI as Agent Console
    participant API as Ticket API
    participant T as Ticket Service
    participant SLA as SLA Service

    Agent->>UI: resolve ticket
    UI->>API: POST /v1/tickets/{id}/resolve
    API->>T: validate + apply resolution
    T->>SLA: stop SLA clocks
    T-->>API: resolved state
    API-->>UI: success
```

## System Sequence: Supervisor Escalation
```mermaid
sequenceDiagram
    autonumber
    actor Sup as Supervisor
    participant UI as Supervisor Console
    participant API as Escalation API
    participant ESC as Escalation Service

    Sup->>UI: escalate ticket
    UI->>API: POST /v1/tickets/{id}/escalations
    API->>ESC: create escalation case
    ESC-->>API: escalation opened
    API-->>UI: case id
```
