# C4 Code Diagram

```mermaid
flowchart TB
    subgraph Interface
      TicketController
      SessionController
      EscalationController
      QAController
    end

    subgraph Application
      TicketAppService
      SessionAppService
      EscalationAppService
      QAAppService
    end

    subgraph Domain
      TicketAggregate
      SessionAggregate
      EscalationAggregate
      SlaPolicy
    end

    subgraph Infrastructure
      TicketRepository
      SessionRepository
      QueueAdapter
      ChannelAdapter
      EventPublisher
      AuditAdapter
    end

    TicketController --> TicketAppService --> TicketAggregate
    SessionController --> SessionAppService --> SessionAggregate
    EscalationController --> EscalationAppService --> EscalationAggregate
    QAController --> QAAppService --> TicketAggregate

    TicketAppService --> SlaPolicy
    EscalationAppService --> SlaPolicy

    TicketAppService --> TicketRepository
    SessionAppService --> SessionRepository
    SessionAppService --> ChannelAdapter
    TicketAppService --> QueueAdapter

    TicketAppService --> EventPublisher
    SessionAppService --> EventPublisher
    EscalationAppService --> AuditAdapter
```

## C4-Code Narrative
Map code modules to runtime responsibilities:
- `ingestion/*` -> connector adapters and event normalizer.
- `workflow/*` -> queue state machine and transition guards.
- `sla/*` -> timer service + escalation policies.
- `audit/*` -> immutable event writer.
- `ops/*` -> incident toggles and degraded-mode controls.

```mermaid
flowchart LR
    ingestion --> workflow
    workflow --> sla
    workflow --> audit
    sla --> ops
```

Operational coverage note: this artifact also specifies omnichannel controls for this design view.
