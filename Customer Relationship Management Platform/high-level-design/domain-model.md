# Domain Model

## Purpose
Define the domain model artifacts for the **Customer Relationship Management Platform** with implementation-ready detail.

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


## Architecture Emphasis
- Bounded contexts with explicit API and event contracts.
- Read/write model separation where throughput and consistency needs diverge.
- Cross-cutting layers for authn/authz, observability, and policy enforcement.

## Domain Glossary
- **Aggregate Invariant**: File-specific term used to anchor decisions in **Domain Model**.
- **Lead**: Prospect record entering qualification and ownership workflows.
- **Opportunity**: Revenue record tracked through pipeline stages and forecast rollups.
- **Correlation ID**: Trace identifier propagated across APIs, queues, and audits for this workflow.

## Entity Lifecycles
- Lifecycle for this document: `Create Aggregate -> Mutate via Commands -> Emit Events -> Archive`.
- Each transition must capture actor, timestamp, source state, target state, and justification note.

```mermaid
flowchart LR
    A[Create Aggregate] --> B[Mutate via Commands]
    B[Mutate via Commands] --> C[Emit Events]
    C[Emit Events] --> D[Archive]
    D[Archive]
```

## Integration Boundaries
- Model boundaries align with lead, account, opportunity, and forecast contexts.
- Data ownership and write authority must be explicit at each handoff boundary.
- Interface changes require schema/version review and downstream impact acknowledgement.

## Error and Retry Behavior
- Invariant violations return conflict errors; no partial aggregate writes.
- Retries must preserve idempotency token and correlation ID context.
- Exhausted retries route to an operational queue with triage metadata.

## Measurable Acceptance Criteria
- Each aggregate defines invariants and concurrency strategy.
- Observability must publish latency, success rate, and failure-class metrics for this document's scope.
- Quarterly review confirms definitions and diagrams still match production behavior.
