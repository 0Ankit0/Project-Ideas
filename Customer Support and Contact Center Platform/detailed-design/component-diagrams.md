# Component Diagrams

```mermaid
flowchart LR
    subgraph API
      Gateway[Gateway/BFF]
      TicketAPI[Ticket API]
      SessionAPI[Session API]
    end

    subgraph Core
      TicketSvc[Ticket Service]
      RoutingSvc[Routing Engine]
      SessionSvc[Conversation Session Service]
      SlaSvc[SLA Service]
      EscSvc[Escalation Service]
      QASvc[QA/Scoring Service]
      KBSvc[Knowledge Service]
    end

    subgraph Integrations
      CRM[CRM Adapter]
      Voice[Telephony Adapter]
      Chat[Chat Adapter]
      Notify[Notification Adapter]
    end

    subgraph Data
      DB[(PostgreSQL)]
      MQ[(Event Bus)]
      Search[(Search Index)]
      Cache[(Redis)]
    end

    Gateway --> TicketAPI --> TicketSvc
    Gateway --> SessionAPI --> SessionSvc

    TicketSvc --> RoutingSvc
    TicketSvc --> SlaSvc
    TicketSvc --> EscSvc
    SessionSvc --> Voice
    SessionSvc --> Chat
    TicketSvc --> CRM

    TicketSvc --> DB
    SessionSvc --> DB
    SlaSvc --> DB
    QASvc --> DB
    KBSvc --> DB

    TicketSvc --> MQ
    SessionSvc --> MQ
    SlaSvc --> MQ
    MQ --> Notify
    MQ --> Search
    RoutingSvc --> Cache
```

## Component Diagram Narrative: Runtime Behavior

```mermaid
flowchart TD
    IN[Ingress Adapters] --> NOR[Normalization Service]
    NOR --> QUE[Queue Orchestrator]
    QUE --> ASSIGN[Assignment Engine]
    QUE --> SLAM[SLA Monitor]
    ASSIGN --> AGUI[Agent Workspace APIs]
    SLAM --> ESC[Escalation Engine]
    ESC --> NOTIF[Pager/Notification]
    QUE --> AUDIT[Audit Pipeline]
```

Each component must declare failure semantics:
- Normalizer: retry + dedup.
- Queue orchestrator: optimistic lock on queue item.
- SLA monitor: deterministic timer recalculation on replay.
- Escalation engine: once-only escalation using durable idempotency token.

Operational coverage note: this artifact also specifies omnichannel and incident controls for this design view.
