# Architecture Diagram

```mermaid
flowchart TB
    Channels[Voice, Chat, Email, Portal] --> Edge[API Gateway / Channel Ingress]

    subgraph Services[Support Domain Services]
      Ticket[Ticket Management]
      Routing[Routing/Skills]
      Session[Conversation Session]
      SLA[SLA Monitor]
      Escalation[Escalation]
      QA[Quality & Coaching]
      Knowledge[Knowledge Integration]
    end

    Edge --> Ticket
    Edge --> Session
    Ticket --> Routing
    Ticket --> SLA
    Ticket --> Escalation

    subgraph CrossCutting[Cross-Cutting]
      Auth[AuthZ]
      Audit[Audit]
      Notify[Notifications]
      Jobs[Async Workers]
    end

    Edge --> Auth
    Ticket --> Audit
    Session --> Audit
    SLA --> Jobs

    subgraph DataInfra[Data/Infra]
      DB[(PostgreSQL)]
      Bus[(Event Bus)]
      Search[(Search)]
      BI[(Analytics Warehouse)]
    end

    Services --> DB
    Services --> Bus
    Bus --> Search
    Bus --> BI
    Jobs --> Notify
```

## Architecture Narrative (Operational Focus)
High-level architecture should depict control planes for routing, SLA policy, and incident orchestration alongside data planes.

```mermaid
flowchart TB
    CH[Channel Adapters] --> IN[Ingestion + Normalization]
    IN --> ORCH[Queue Workflow Orchestrator]
    ORCH --> WKS[Agent Workspace]
    ORCH --> POL[SLA & Escalation Policy]
    ORCH --> AUD[Audit/Compliance Store]
    POL --> IR[Incident Automation]
```

Design requirement: no component can bypass orchestrator-owned workflow transitions; direct writes are forbidden to preserve auditability.

Operational coverage note: this artifact also specifies omnichannel controls for this design view.
