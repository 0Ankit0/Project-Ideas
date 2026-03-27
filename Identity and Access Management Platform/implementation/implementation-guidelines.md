# Implementation Guidelines

## Purpose
Define the implementation guidelines artifacts for the **Identity and Access Management Platform** with implementation-ready detail.

## Domain Context
- Domain: IAM
- Core entities: Identity, Session, Token, Policy, Role, Federation Connection, SCIM Provisioning Job
- Primary workflows: authentication and session lifecycle, token issuance and revocation, federation login, SCIM provisioning and deprovisioning, policy decision evaluation

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
