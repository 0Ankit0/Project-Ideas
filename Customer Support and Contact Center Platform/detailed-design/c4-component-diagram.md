# C4 Component Diagram

```mermaid
flowchart TB
    subgraph Users
      Customer
      Agent
      Supervisor
      QAAnalyst
    end

    subgraph ContactCenter[Contact Center App Container]
      UIBFF[Agent Console + BFF]
      TicketCmp[Ticket Management]
      RoutingCmp[Routing & Skills]
      SessionCmp[Voice/Chat Session]
      SlaCmp[SLA Monitoring]
      EscCmp[Escalation Management]
      QACmp[Quality Evaluation]
      KBCmp[Knowledge Base Integration]
    end

    subgraph Infra
      OLTP[(Support DB)]
      Bus[(Event Bus)]
      Cache[(Routing Cache)]
      Search[(Search)]
    end

    Customer --> SessionCmp
    Agent --> UIBFF
    Supervisor --> UIBFF
    QAAnalyst --> QACmp

    UIBFF --> TicketCmp
    UIBFF --> SessionCmp
    UIBFF --> EscCmp

    TicketCmp --> RoutingCmp
    TicketCmp --> SlaCmp
    TicketCmp --> OLTP
    SessionCmp --> OLTP
    SlaCmp --> OLTP
    EscCmp --> OLTP

    TicketCmp --> Bus
    SessionCmp --> Bus
    SlaCmp --> Bus
    Bus --> Search
    RoutingCmp --> Cache
```

## C4 Component Deep Narrative

```mermaid
flowchart LR
    subgraph Core
      RT[Routing Component]
      SL[SLA Component]
      WF[Workflow State Component]
      OM[Omnichannel Normalizer]
      AU[Audit Writer]
      IR[Incident Control]
    end
    OM-->RT-->WF
    WF-->SL
    WF-->AU
    SL-->IR
```

Component boundaries:
- Routing decides queue and assignee.
- Workflow owns state machine invariants.
- SLA computes timers and escalation triggers.
- Audit Writer is append-only and asynchronous with guaranteed delivery.
- Incident Control toggles safe-mode features with change records.
