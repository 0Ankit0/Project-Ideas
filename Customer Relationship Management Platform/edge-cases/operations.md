# Operations

## Day-2 Readiness
- SLO dashboard for availability, latency, and data freshness.
- Runbooks for incident triage, rollback, replay, and backfill.
- Capacity planning based on peak traffic and queue depth trends.

## Incident Lifecycle
1. Detect and classify severity with ownership routing.
2. Contain blast radius and communicate stakeholder impact.
3. Recover service and data consistency.
4. Publish postmortem with corrective actions and deadlines.

## Domain Glossary
- **Operational Incident**: File-specific term used to anchor decisions in **Operations**.
- **Lead**: Prospect record entering qualification and ownership workflows.
- **Opportunity**: Revenue record tracked through pipeline stages and forecast rollups.
- **Correlation ID**: Trace identifier propagated across APIs, queues, and audits for this workflow.

## Entity Lifecycles
- Lifecycle for this document: `Alert -> Diagnose -> Mitigate -> Recover -> Postmortem`.
- Each transition must capture actor, timestamp, source state, target state, and justification note.

```mermaid
flowchart LR
    A[Alert] --> B[Diagnose]
    B[Diagnose] --> C[Mitigate]
    C[Mitigate] --> D[Recover]
    D[Recover] --> E[Postmortem]
    E[Postmortem]
```

## Integration Boundaries
- Incident workflow boundaries span monitoring, ticketing, comms, and runbooks.
- Data ownership and write authority must be explicit at each handoff boundary.
- Interface changes require schema/version review and downstream impact acknowledgement.

## Error and Retry Behavior
- Auto-remediation retries once; repeated failures page on-call immediately.
- Retries must preserve idempotency token and correlation ID context.
- Exhausted retries route to an operational queue with triage metadata.

## Measurable Acceptance Criteria
- P1 incidents have postmortem completed within 5 business days.
- Observability must publish latency, success rate, and failure-class metrics for this document's scope.
- Quarterly review confirms definitions and diagrams still match production behavior.
