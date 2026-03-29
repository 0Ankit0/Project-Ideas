# System Sequence Diagrams

## System Sequence: Submit Forecast
```mermaid
sequenceDiagram
    autonumber
    actor Rep as Sales Rep
    participant UI as CRM UI
    participant API as Forecast API
    participant Svc as Forecast Service
    participant DB as DB
    participant Mgr as Manager Queue

    Rep->>UI: Submit monthly forecast
    UI->>API: POST /v1/forecasts/snapshots/{id}/submit
    API->>Svc: submit(snapshotId, actor)
    Svc->>DB: persist status=Submitted
    Svc->>Mgr: notify manager for review
    Svc-->>API: submission accepted
    API-->>UI: 200 OK + submitted status
```

## System Sequence: Territory Reassignment
```mermaid
sequenceDiagram
    autonumber
    actor Ops as RevOps
    participant UI as Admin UI
    participant API as Territory API
    participant Job as Reassignment Worker
    participant DB as DB
    participant Bus as Event Bus

    Ops->>UI: Request territory reassignment
    UI->>API: POST /v1/territories/reassignments
    API->>DB: create reassignment job
    API->>Job: start async execution
    Job->>DB: reassign accounts + opportunities
    Job->>Bus: publish TerritoryReassignmentCompleted
    Job-->>API: done
    API-->>UI: job status completed
```

## Domain Glossary
- **Interaction Step**: File-specific term used to anchor decisions in **System Sequence Diagrams**.
- **Lead**: Prospect record entering qualification and ownership workflows.
- **Opportunity**: Revenue record tracked through pipeline stages and forecast rollups.
- **Correlation ID**: Trace identifier propagated across APIs, queues, and audits for this workflow.

## Entity Lifecycles
- Lifecycle for this document: `Request -> Authenticate -> Authorize -> Execute -> Respond -> Observe`.
- Each transition must capture actor, timestamp, source state, target state, and justification note.

```mermaid
flowchart LR
    A[Request] --> B[Authenticate]
    B[Authenticate] --> C[Authorize]
    C[Authorize] --> D[Execute]
    D[Execute] --> E[Respond]
    E[Respond] --> F[Observe]
    F[Observe]
```

## Integration Boundaries
- Sequences include UI, API gateway, domain service, and async processors.
- Data ownership and write authority must be explicit at each handoff boundary.
- Interface changes require schema/version review and downstream impact acknowledgement.

## Error and Retry Behavior
- Timeout branch and retry branch are drawn for each critical sequence.
- Retries must preserve idempotency token and correlation ID context.
- Exhausted retries route to an operational queue with triage metadata.

## Measurable Acceptance Criteria
- At least one happy path and one failure path per tier-1 sequence.
- Observability must publish latency, success rate, and failure-class metrics for this document's scope.
- Quarterly review confirms definitions and diagrams still match production behavior.
