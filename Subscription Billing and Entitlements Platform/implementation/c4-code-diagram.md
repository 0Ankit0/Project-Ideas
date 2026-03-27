# C4 Code Diagram

## Purpose
Define the c4 code diagram artifacts for the **Subscription Billing and Entitlements Platform** with implementation-ready detail.

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


## Delivery Emphasis
- Milestones mapped to slices that are testable end-to-end.
- CI quality gates include lint, unit/integration tests, and contract checks.
- Backend status matrix tracks readiness by capability and release wave.
