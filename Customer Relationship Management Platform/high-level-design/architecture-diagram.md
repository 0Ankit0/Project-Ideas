# Architecture Diagram

## High-Level Architecture
```mermaid
flowchart TB
    CH[Channels\nWeb, Mobile, Integrations] --> EDGE[API Gateway / BFF]

    subgraph Domain[CRM Domain Services]
      Lead[Lead Service]
      Account[Account & Contact Service]
      Opp[Opportunity Service]
      Activity[Activity Service]
      Forecast[Forecast Service]
      Territory[Territory Service]
    end

    EDGE --> Lead
    EDGE --> Account
    EDGE --> Opp
    EDGE --> Activity
    EDGE --> Forecast
    EDGE --> Territory

    subgraph Platform[Platform Services]
      Auth[AuthN/AuthZ]
      Audit[Audit/Compliance]
      Notify[Notifications]
      Workflow[Workflow/Jobs]
    end

    Lead --> Workflow
    Opp --> Workflow
    Forecast --> Workflow
    Territory --> Workflow

    EDGE --> Auth
    Opp --> Audit
    Forecast --> Audit

    subgraph Data[Data Layer]
      OLTP[(OLTP DB)]
      Cache[(Redis)]
      Bus[(Event Bus)]
      Search[(Search)]
      WH[(Warehouse)]
    end

    Lead --> OLTP
    Account --> OLTP
    Opp --> OLTP
    Activity --> OLTP
    Forecast --> OLTP
    Territory --> OLTP

    Workflow --> Bus
    Bus --> Notify
    Bus --> Search
    Bus --> WH
    Auth --> Cache
```

## Domain Glossary
- **Architecture View**: File-specific term used to anchor decisions in **Architecture Diagram**.
- **Lead**: Prospect record entering qualification and ownership workflows.
- **Opportunity**: Revenue record tracked through pipeline stages and forecast rollups.
- **Correlation ID**: Trace identifier propagated across APIs, queues, and audits for this workflow.

## Entity Lifecycles
- Lifecycle for this document: `Current State -> Target State -> Migration Stage -> Steady State`.
- Each transition must capture actor, timestamp, source state, target state, and justification note.

```mermaid
flowchart LR
    A[Current State] --> B[Target State]
    B[Target State] --> C[Migration Stage]
    C[Migration Stage] --> D[Steady State]
    D[Steady State]
```

## Integration Boundaries
- Boundaries separate ingress, domain microservices, event fabric, and data planes.
- Data ownership and write authority must be explicit at each handoff boundary.
- Interface changes require schema/version review and downstream impact acknowledgement.

## Error and Retry Behavior
- Inter-service calls retry with circuit breakers; cross-domain writes use saga compensation.
- Retries must preserve idempotency token and correlation ID context.
- Exhausted retries route to an operational queue with triage metadata.

## Measurable Acceptance Criteria
- Diagram identifies all tier-1 components with HA strategy and owner.
- Observability must publish latency, success rate, and failure-class metrics for this document's scope.
- Quarterly review confirms definitions and diagrams still match production behavior.
