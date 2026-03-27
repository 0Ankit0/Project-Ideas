# Api Design

## Purpose
Define the api design artifacts for the **Hospital Information System** with implementation-ready detail.

## Domain Context
- Domain: Hospital
- Core entities: Patient, Encounter, Admission, Clinical Order, Medication Administration, Care Plan, Discharge Summary
- Primary workflows: patient registration and identity resolution, admission-transfer-discharge, order placement and fulfillment, care documentation and handoff, discharge and follow-up coordination

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
