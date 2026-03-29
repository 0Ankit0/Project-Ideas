# Network Infrastructure

## Purpose
Define the network infrastructure artifacts for the **Customer Relationship Management Platform** with implementation-ready detail.

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
- **Network Trust Zone**: File-specific term used to anchor decisions in **Network Infrastructure**.
- **Lead**: Prospect record entering qualification and ownership workflows.
- **Opportunity**: Revenue record tracked through pipeline stages and forecast rollups.
- **Correlation ID**: Trace identifier propagated across APIs, queues, and audits for this workflow.

## Entity Lifecycles
- Lifecycle for this document: `Design Segments -> Apply Policies -> Validate Flows -> Monitor`.
- Each transition must capture actor, timestamp, source state, target state, and justification note.

```mermaid
flowchart LR
    A[Design Segments] --> B[Apply Policies]
    B[Apply Policies] --> C[Validate Flows]
    C[Validate Flows] --> D[Monitor]
    D[Monitor]
```

## Integration Boundaries
- Covers public ingress, private service mesh, and data subnet boundaries.
- Data ownership and write authority must be explicit at each handoff boundary.
- Interface changes require schema/version review and downstream impact acknowledgement.

## Error and Retry Behavior
- Packet loss alarms trigger path failover; ACL misconfigurations require manual approval to reapply.
- Retries must preserve idempotency token and correlation ID context.
- Exhausted retries route to an operational queue with triage metadata.

## Measurable Acceptance Criteria
- All ingress/egress rules are documented with owner and review cadence.
- Observability must publish latency, success rate, and failure-class metrics for this document's scope.
- Quarterly review confirms definitions and diagrams still match production behavior.
