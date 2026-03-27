# Sequence Diagrams

## Purpose
Define the sequence diagrams artifacts for the **Subscription Billing and Entitlements Platform** with implementation-ready detail.

## Domain Context
- Domain: Subscription Billing
- Core entities: Plan, Subscription, Invoice, Usage Record, Entitlement, Credit Note, Dunning Case
- Primary workflows: subscription creation and renewal, usage ingestion and rating, invoice generation and collection, dunning retry orchestration, entitlement grant and revoke

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
