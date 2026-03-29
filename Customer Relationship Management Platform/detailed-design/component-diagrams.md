# Component Diagrams

This document details runtime components and key internal interactions for CRM services.

## Service-Level Component Topology
```mermaid
flowchart LR
    subgraph API[API Tier]
      GW[Gateway]
      BFF[BFF]
    end

    subgraph Core[Core CRM Components]
      LeadSvc[Lead Service]
      ContactSvc[Contact/Account Service]
      OppSvc[Opportunity Service]
      ActSvc[Activity Service]
      ForecastSvc[Forecast Service]
      TerritorySvc[Territory Service]
      DedupeSvc[Deduplication Service]
    end

    subgraph CrossCutting[Cross-Cutting Components]
      AuthSvc[AuthZ/Policy Service]
      AuditSvc[Audit Service]
      NotifySvc[Notification Service]
      SearchProj[Search Projector]
      ETL[Warehouse ETL]
    end

    subgraph Infra[Infrastructure]
      DB[(PostgreSQL)]
      MQ[(Message Broker)]
      Cache[(Redis)]
      Search[(OpenSearch)]
      WH[(Warehouse)]
    end

    GW --> BFF
    BFF --> AuthSvc
    BFF --> LeadSvc
    BFF --> ContactSvc
    BFF --> OppSvc
    BFF --> ActSvc
    BFF --> ForecastSvc
    BFF --> TerritorySvc

    LeadSvc --> DedupeSvc

    LeadSvc --> DB
    ContactSvc --> DB
    OppSvc --> DB
    ActSvc --> DB
    ForecastSvc --> DB
    TerritorySvc --> DB
    DedupeSvc --> DB

    LeadSvc --> MQ
    OppSvc --> MQ
    ForecastSvc --> MQ
    TerritorySvc --> MQ
    DedupeSvc --> MQ

    MQ --> NotifySvc
    MQ --> SearchProj
    MQ --> ETL

    SearchProj --> Search
    ETL --> WH

    AuthSvc --> Cache
    AuditSvc --> DB
    OppSvc --> AuditSvc
    ForecastSvc --> AuditSvc
    TerritorySvc --> AuditSvc
```

## Critical Interaction Path: Stage Change
```mermaid
sequenceDiagram
    participant U as Sales Rep
    participant B as BFF
    participant O as Opportunity Service
    participant A as Audit Service
    participant M as Message Broker

    U->>B: Change opportunity stage
    B->>O: validate + execute transition
    O->>A: append audit entry
    O->>M: emit OpportunityStageChanged
    O-->>B: updated opportunity view
    B-->>U: success response
```

## Domain Glossary
- **Runtime Component**: File-specific term used to anchor decisions in **Component Diagrams**.
- **Lead**: Prospect record entering qualification and ownership workflows.
- **Opportunity**: Revenue record tracked through pipeline stages and forecast rollups.
- **Correlation ID**: Trace identifier propagated across APIs, queues, and audits for this workflow.

## Entity Lifecycles
- Lifecycle for this document: `Build -> Package -> Configure -> Deploy -> Observe`.
- Each transition must capture actor, timestamp, source state, target state, and justification note.

```mermaid
flowchart LR
    A[Build] --> B[Package]
    B[Package] --> C[Configure]
    C[Configure] --> D[Deploy]
    D[Deploy] --> E[Observe]
    E[Observe]
```

## Integration Boundaries
- Components integrate through REST, events, and scheduled jobs.
- Data ownership and write authority must be explicit at each handoff boundary.
- Interface changes require schema/version review and downstream impact acknowledgement.

## Error and Retry Behavior
- Component restart policy retries 3 times before alerting on-call.
- Retries must preserve idempotency token and correlation ID context.
- Exhausted retries route to an operational queue with triage metadata.

## Measurable Acceptance Criteria
- Diagram includes startup dependencies and health probe endpoints.
- Observability must publish latency, success rate, and failure-class metrics for this document's scope.
- Quarterly review confirms definitions and diagrams still match production behavior.
