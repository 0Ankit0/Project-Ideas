# Use Case Diagram

This diagram captures key user goals and supporting CRM capabilities.

```mermaid
flowchart LR
    Rep[Sales Rep]
    Mgr[Sales Manager]
    Ops[RevOps]
    Admin[CRM Admin]
    Int[Integration System]

    UC1((Capture & Qualify Lead))
    UC2((Merge Duplicate Records))
    UC3((Manage Opportunity Pipeline))
    UC4((Log Activities & Follow-ups))
    UC5((Submit Forecast))
    UC6((Approve Forecast))
    UC7((Reassign Territory))
    UC8((Configure Roles & Policies))
    UC9((Sync External Data))

    Rep --> UC1
    Rep --> UC3
    Rep --> UC4
    Rep --> UC5

    Mgr --> UC3
    Mgr --> UC6

    Ops --> UC2
    Ops --> UC7

    Admin --> UC8

    Int --> UC9
```

## Notes
- Forecast and territory actions are managerial/operations controlled.
- Deduplication is explicit to prevent accidental irreversible merges.

## Domain Glossary
- **Actor Association**: File-specific term used to anchor decisions in **Use Case Diagram**.
- **Lead**: Prospect record entering qualification and ownership workflows.
- **Opportunity**: Revenue record tracked through pipeline stages and forecast rollups.
- **Correlation ID**: Trace identifier propagated across APIs, queues, and audits for this workflow.

## Entity Lifecycles
- Lifecycle for this document: `Identify Actor -> Link Use Case -> Validate Scope -> Baseline`.
- Each transition must capture actor, timestamp, source state, target state, and justification note.

```mermaid
flowchart LR
    A[Identify Actor] --> B[Link Use Case]
    B[Link Use Case] --> C[Validate Scope]
    C[Validate Scope] --> D[Baseline]
    D[Baseline]
```

## Integration Boundaries
- Associations map to RBAC roles and service authorization scopes.
- Data ownership and write authority must be explicit at each handoff boundary.
- Interface changes require schema/version review and downstream impact acknowledgement.

## Error and Retry Behavior
- Unauthorized actor links are rejected during model review.
- Retries must preserve idempotency token and correlation ID context.
- Exhausted retries route to an operational queue with triage metadata.

## Measurable Acceptance Criteria
- Diagram covers 100% of tier-1 capabilities listed in requirements.
- Observability must publish latency, success rate, and failure-class metrics for this document's scope.
- Quarterly review confirms definitions and diagrams still match production behavior.
