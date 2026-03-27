# Activity Diagrams

## Purpose
Define the activity diagrams artifacts for the **Customer Relationship Management Platform** with implementation-ready detail.

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


## Analysis Notes
- Capture alternate/error flows for: lead capture and qualification, deduplication and merge review, opportunity stage progression.
- Distinguish synchronous decision points vs asynchronous compensation.
- Track external dependencies through channels: web, email, calendar, mobile.
