# C4 Code Diagram

This code-level view maps key modules inside the CRM backend service.

```mermaid
flowchart TB
    subgraph Interface[Interface Layer]
      CtrlLead[LeadController]
      CtrlOpp[OpportunityController]
      CtrlForecast[ForecastController]
      CtrlTerritory[TerritoryController]
    end

    subgraph App[Application Layer]
      LeadApp[LeadApplicationService]
      OppApp[OpportunityApplicationService]
      ForecastApp[ForecastApplicationService]
      TerritoryApp[TerritoryApplicationService]
    end

    subgraph Domain[Domain Layer]
      LeadAgg[Lead Aggregate]
      OppAgg[Opportunity Aggregate]
      ForecastAgg[ForecastSnapshot Aggregate]
      TerritoryAgg[Territory Aggregate]
      Rules[Policy/Domain Rules]
    end

    subgraph Infra[Infrastructure Layer]
      Repo[Repositories]
      Outbox[Outbox Publisher]
      Audit[AuditWriter]
      Authz[AuthzAdapter]
    end

    CtrlLead --> LeadApp
    CtrlOpp --> OppApp
    CtrlForecast --> ForecastApp
    CtrlTerritory --> TerritoryApp

    LeadApp --> LeadAgg
    OppApp --> OppAgg
    ForecastApp --> ForecastAgg
    TerritoryApp --> TerritoryAgg

    LeadApp --> Rules
    OppApp --> Rules
    ForecastApp --> Rules
    TerritoryApp --> Rules

    LeadApp --> Repo
    OppApp --> Repo
    ForecastApp --> Repo
    TerritoryApp --> Repo

    LeadApp --> Outbox
    OppApp --> Outbox
    ForecastApp --> Outbox
    TerritoryApp --> Outbox

    OppApp --> Audit
    ForecastApp --> Audit
    TerritoryApp --> Audit
    LeadApp --> Authz
    OppApp --> Authz
```

## Domain Glossary
- **Code Module Boundary**: File-specific term used to anchor decisions in **C4 Code Diagram**.
- **Lead**: Prospect record entering qualification and ownership workflows.
- **Opportunity**: Revenue record tracked through pipeline stages and forecast rollups.
- **Correlation ID**: Trace identifier propagated across APIs, queues, and audits for this workflow.

## Entity Lifecycles
- Lifecycle for this document: `Module Planned -> Implemented -> Reviewed -> Tagged -> Released`.
- Each transition must capture actor, timestamp, source state, target state, and justification note.

```mermaid
flowchart LR
    A[Module Planned] --> B[Implemented]
    B[Implemented] --> C[Reviewed]
    C[Reviewed] --> D[Tagged]
    D[Tagged] --> E[Released]
    E[Released]
```

## Integration Boundaries
- Maps code packages to runtime containers and ownership teams.
- Data ownership and write authority must be explicit at each handoff boundary.
- Interface changes require schema/version review and downstream impact acknowledgement.

## Error and Retry Behavior
- Build retries transient dependency fetch failures; test failures are non-retryable.
- Retries must preserve idempotency token and correlation ID context.
- Exhausted retries route to an operational queue with triage metadata.

## Measurable Acceptance Criteria
- Each module has dependency direction and public API surface documented.
- Observability must publish latency, success rate, and failure-class metrics for this document's scope.
- Quarterly review confirms definitions and diagrams still match production behavior.
