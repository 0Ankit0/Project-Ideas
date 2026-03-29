# Backend Status Matrix

## Purpose
Define the backend status matrix artifacts for the **Hospital Information System** with implementation-ready detail.

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


## Delivery Emphasis
- Milestones mapped to slices that are testable end-to-end.
- CI quality gates include lint, unit/integration tests, and contract checks.
- Backend status matrix tracks readiness by capability and release wave.

---


## Implementation Readiness Matrix Details
### Capability Maturity Scale
- **L0**: draft API/data contract only.
- **L1**: endpoint implemented with unit tests.
- **L2**: integration-tested with contract verification and observability hooks.
- **L3**: production-ready with runbook, SLO dashboard, and on-call ownership.

### Exit Criteria per Module
- Patient/ADT: replay-safe idempotency + merge/unmerge workflows validated.
- Clinical/orders: CDS gating, result reconciliation, and abnormal alert workflows validated.
- Billing: claim lifecycle + denial pathways validated against sandbox payer endpoints.

## File-Specific Implementation Boundaries
This artifact is implementation-focused on **delivery maturity scoring and go-live exit criteria**. The boundaries below are specific to `implementation/backend-status-matrix.md` and are intentionally not reused as generic filler text.

| Boundary Slice | In Scope for this File | Out of Scope for this File | Implementation Consequence |
|---|---|---|---|
| Build & Test Pipeline | Lint, unit/integration/contract tests and policy checks | Runtime scaling strategy | Release quality evidence with traceability |
| Runtime Service Layer | Endpoint handlers, orchestration, retry/dedupe behavior | CI orchestration internals | Production-safe mutating behavior |
| Operational Readiness | Runbook links, SLO dashboards, pager ownership | Product feature semantics | Day-2 readiness and controlled rollout posture |

## Business Rules to API/Data/Operational Controls (File-Specific)
| Rule Focus | API Enforcement Touchpoint | Data Model/Contract Tie-In | Operational Control |
|---|---|---|---|
| Preconditions for `backend-status-matrix` workflows must be validated before state mutation. | `POST /v1/releases/{service}/promote` with explicit error taxonomy and correlation IDs. | `readiness_matrix, release_evidence, rollout_audits` with strict timestamp, actor, and tenant context fields. | Alert on rule-violation rate and route to owner with SLA-backed response. |
| Mutations must be replay-safe and duplicate-proof. | Idempotency checks on mutation endpoints and async consumers. | Uniqueness keys + immutable evidence rows for side-effect tracking. | Replay runbook with pre/post reconciliation and sign-off checklist. |
| Access to sensitive operations must include least-privilege and evidence. | AuthN/AuthZ middleware + policy decision point reason codes. | Audit/event envelopes include policy version and decision outcome. | Quarterly control review and continuous SIEM correlation for anomalies. |

## Interoperability Assumptions for `backend-status-matrix.md`
- Contract versions are explicitly pinned; backward compatibility is managed per versioned API/event schema.
- External dependencies are treated as failure-prone; timeout/retry budgets and fallback states are documented in this file's scenarios.
- Observability correlation (`tenant_id`, `actor_id`, `correlation_id`) is required for all critical-path operations in this document scope.

## Compliance and Security Posture for this Artifact
- Evidence produced by this workflow/design artifact is audit-consumable (who/what/when/why) and linked to incident/postmortem records.
- Sensitive data exposure is minimized using role-scoped access and redaction guidance relevant to `backend-status-matrix.md`.
- Operational controls for this file include detection, containment, recovery, and verification steps with named ownership.
