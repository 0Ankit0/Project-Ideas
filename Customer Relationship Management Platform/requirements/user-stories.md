# User Stories

## Purpose
Define the user stories artifacts for the **Customer Relationship Management Platform** with implementation-ready detail.

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


## Representative User Stories
- As an operator, I can complete the primary workflow with validation and audit evidence.
- As a manager, I can see queue/backlog/SLA metrics to manage throughput.
- As an admin, I can configure policy and recover from partial failures safely.

## Domain Glossary
- **Story Narrative**: File-specific term used to anchor decisions in **User Stories**.
- **Lead**: Prospect record entering qualification and ownership workflows.
- **Opportunity**: Revenue record tracked through pipeline stages and forecast rollups.
- **Correlation ID**: Trace identifier propagated across APIs, queues, and audits for this workflow.

## Entity Lifecycles
- Lifecycle for this document: `Drafted -> Refined -> Estimated -> In Sprint -> Accepted -> Archived`.
- Each transition must capture actor, timestamp, source state, target state, and justification note.

```mermaid
flowchart LR
    A[Drafted] --> B[Refined]
    B[Refined] --> C[Estimated]
    C[Estimated] --> D[In Sprint]
    D[In Sprint] --> E[Accepted]
    E[Accepted] --> F[Archived]
    F[Archived]
```

## Integration Boundaries
- Stories sync with backlog tool, QA test management, and release notes pipeline.
- Data ownership and write authority must be explicit at each handoff boundary.
- Interface changes require schema/version review and downstream impact acknowledgement.

## Error and Retry Behavior
- If acceptance checks fail, story returns to Refined; no silent reopen.
- Retries must preserve idempotency token and correlation ID context.
- Exhausted retries route to an operational queue with triage metadata.

## Measurable Acceptance Criteria
- Each story has at least 3 measurable acceptance checks and one negative-path check.
- Observability must publish latency, success rate, and failure-class metrics for this document's scope.
- Quarterly review confirms definitions and diagrams still match production behavior.
