# Implementation Guidelines

## Purpose
Define the implementation guidelines artifacts for the **Hospital Information System** with implementation-ready detail.

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


## Implementation Playbook
### Coding and Delivery Standards
- Every mutating endpoint must include idempotency tests and audit evidence assertions.
- Feature flags require default-safe fallback and sunset date.
- Observability minimum: structured logs, RED metrics, trace spans with correlation IDs.

### Release Readiness Checklist
- Schema migration rollback tested in staging with production-like volume profile.
- Incident runbook linked in service README and pager metadata.
- Security review complete for data flows involving PHI export or external integrations.

## File-Specific Implementation Boundaries
This artifact is implementation-focused on **coding standards, release controls, and observability requirements**. The boundaries below are specific to `implementation/implementation-guidelines.md` and are intentionally not reused as generic filler text.

| Boundary Slice | In Scope for this File | Out of Scope for this File | Implementation Consequence |
|---|---|---|---|
| Build & Test Pipeline | Lint, unit/integration/contract tests and policy checks | Runtime scaling strategy | Release quality evidence with traceability |
| Runtime Service Layer | Endpoint handlers, orchestration, retry/dedupe behavior | CI orchestration internals | Production-safe mutating behavior |
| Operational Readiness | Runbook links, SLO dashboards, pager ownership | Product feature semantics | Day-2 readiness and controlled rollout posture |

## Business Rules to API/Data/Operational Controls (File-Specific)
| Rule Focus | API Enforcement Touchpoint | Data Model/Contract Tie-In | Operational Control |
|---|---|---|---|
| Preconditions for `implementation-guidelines` workflows must be validated before state mutation. | `POST /v1/releases/{service}/promote` with explicit error taxonomy and correlation IDs. | `readiness_matrix, release_evidence, rollout_audits` with strict timestamp, actor, and tenant context fields. | Alert on rule-violation rate and route to owner with SLA-backed response. |
| Mutations must be replay-safe and duplicate-proof. | Idempotency checks on mutation endpoints and async consumers. | Uniqueness keys + immutable evidence rows for side-effect tracking. | Replay runbook with pre/post reconciliation and sign-off checklist. |
| Access to sensitive operations must include least-privilege and evidence. | AuthN/AuthZ middleware + policy decision point reason codes. | Audit/event envelopes include policy version and decision outcome. | Quarterly control review and continuous SIEM correlation for anomalies. |

## Interoperability Assumptions for `implementation-guidelines.md`
- Contract versions are explicitly pinned; backward compatibility is managed per versioned API/event schema.
- External dependencies are treated as failure-prone; timeout/retry budgets and fallback states are documented in this file's scenarios.
- Observability correlation (`tenant_id`, `actor_id`, `correlation_id`) is required for all critical-path operations in this document scope.

## Compliance and Security Posture for this Artifact
- Evidence produced by this workflow/design artifact is audit-consumable (who/what/when/why) and linked to incident/postmortem records.
- Sensitive data exposure is minimized using role-scoped access and redaction guidance relevant to `implementation-guidelines.md`.
- Operational controls for this file include detection, containment, recovery, and verification steps with named ownership.
