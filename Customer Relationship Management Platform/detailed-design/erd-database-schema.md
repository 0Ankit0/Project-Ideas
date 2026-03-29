# Erd Database Schema

## Purpose
Define the erd database schema artifacts for the **Customer Relationship Management Platform** with implementation-ready detail.

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


## Detailed Design Emphasis
- Table/entity constraints and invariants are explicit.
- Failure semantics for retries/timeouts are defined per integration.
- Versioning strategy documented for APIs, events, and data migrations.

## Domain Glossary
- **Table Constraint**: File-specific term used to anchor decisions in **Erd Database Schema**.
- **Lead**: Prospect record entering qualification and ownership workflows.
- **Opportunity**: Revenue record tracked through pipeline stages and forecast rollups.
- **Correlation ID**: Trace identifier propagated across APIs, queues, and audits for this workflow.

## Entity Lifecycles
- Lifecycle for this document: `Design Table -> Apply Migration -> Backfill -> Verify -> Lock`.
- Each transition must capture actor, timestamp, source state, target state, and justification note.

```mermaid
flowchart LR
    A[Design Table] --> B[Apply Migration]
    B[Apply Migration] --> C[Backfill]
    C[Backfill] --> D[Verify]
    D[Verify] --> E[Lock]
    E[Lock]
```

## Integration Boundaries
- Schema integrates with migration tooling, ORM mappings, and CDC capture.
- Data ownership and write authority must be explicit at each handoff boundary.
- Interface changes require schema/version review and downstream impact acknowledgement.

## Error and Retry Behavior
- Migration retries only for lock timeouts; checksum mismatches require rollback.
- Retries must preserve idempotency token and correlation ID context.
- Exhausted retries route to an operational queue with triage metadata.

## Measurable Acceptance Criteria
- All critical tables include PK/FK and uniqueness constraints plus index strategy.
- Observability must publish latency, success rate, and failure-class metrics for this document's scope.
- Quarterly review confirms definitions and diagrams still match production behavior.
