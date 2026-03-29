# Cloud Architecture

## Purpose
Define the cloud architecture artifacts for the **Customer Relationship Management Platform** with implementation-ready detail.

## Domain Context
- Domain: CRM
- Core entities: Lead, Contact, Account, Opportunity, Activity, Forecast Snapshot, Territory
- Primary workflows: lead capture and qualification, deduplication and merge review, opportunity stage progression, territory assignment and reassignment, forecast rollup and approval

## Key Design Decisions
- Enforce idempotency and correlation IDs for all mutating operations.
- Persist immutable audit events for critical lifecycle transitions.
- Separate online transaction paths from async reconciliation/repair paths.

## Reliability and Compliance
- Define SLOs and error budgets for user-facing operations.
- Include RBAC, least-privilege service identities, and full audit trails.
- Provide runbooks for degraded mode, replay, and backfill operations.


## Infrastructure Emphasis
- Multi-environment topology (dev/stage/prod) with promotion gates.
- Network segmentation, private service communication, and WAF boundaries.
- Backup, disaster recovery, and key rotation procedures.

## Domain Glossary
- **Cloud Deployment Cell**: File-specific term used to anchor decisions in **Cloud Architecture**.
- **Lead**: Prospect record entering qualification and ownership workflows.
- **Opportunity**: Revenue record tracked through pipeline stages and forecast rollups.
- **Correlation ID**: Trace identifier propagated across APIs, queues, and audits for this workflow.

## Entity Lifecycles
- Lifecycle for this document: `Plan -> Provision -> Validate -> Operate -> Optimize -> Retire`.
- Each transition must capture actor, timestamp, source state, target state, and justification note.

```mermaid
flowchart LR
    A[Plan] --> B[Provision]
    B[Provision] --> C[Validate]
    C[Validate] --> D[Operate]
    D[Operate] --> E[Optimize]
    E[Optimize] --> F[Retire]
    F[Retire]
```

## Integration Boundaries
- Integrates VPC, managed databases, queueing, and observability services.
- Data ownership and write authority must be explicit at each handoff boundary.
- Interface changes require schema/version review and downstream impact acknowledgement.

## Error and Retry Behavior
- Provisioning retries API throttles; quota failures create infra ticket.
- Retries must preserve idempotency token and correlation ID context.
- Exhausted retries route to an operational queue with triage metadata.

## Measurable Acceptance Criteria
- RTO/RPO, region strategy, and key management are explicitly documented.
- Observability must publish latency, success rate, and failure-class metrics for this document's scope.
- Quarterly review confirms definitions and diagrams still match production behavior.
