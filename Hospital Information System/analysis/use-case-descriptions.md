# Use Case Descriptions

## Purpose
Define the use case descriptions artifacts for the **Hospital Information System** with implementation-ready detail.

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


## Analysis Notes
- Capture alternate/error flows for: patient registration and identity resolution, admission-transfer-discharge, order placement and fulfillment.
- Distinguish synchronous decision points vs asynchronous compensation.
- Track external dependencies through channels: clinical workstation, mobile nursing app, integration HL7/FHIR.

---


## Implementation-Ready Use-Case Detailing
### Canonical Use Case Template
1. Trigger and preconditions (actor role, patient context, consent state).
2. Main success steps with API calls and synchronous response expectations.
3. Alternate/exception flows with reason codes and user-facing remediation text.
4. Audit evidence emitted and control owner assignment.

### Fully-Specified Example: Medication Administration
- **Preconditions:** active encounter, signed medication order, allergy check status resolved.
- **Main flow:** nurse scans patient + medication -> validates five rights -> records administration event -> updates MAR projection.
- **Exception flow:** barcode mismatch or allergy hard-stop -> block administration and route to physician override path.
- **Artifacts:** `med_admin` row, `domain.medication.administered.v1` event, immutable audit entry.

## File-Specific Implementation Boundaries
This artifact is implementation-focused on **step-level operational behavior, alternatives, and exception handling**. The boundaries below are specific to `analysis/use-case-descriptions.md` and are intentionally not reused as generic filler text.

| Boundary Slice | In Scope for this File | Out of Scope for this File | Implementation Consequence |
|---|---|---|---|
| Intake & Identity Analysis | Entry validation checkpoints and mismatch heuristics | UI widget design details | Data-quality metrics and EMPI false-positive rate |
| Clinical Flow Analysis | Encounter/order sequence timing and critical path dependencies | Persistence implementation details | Throughput, wait-time, and bottleneck reporting |
| Governance Analysis | Rule conformance and audit evidence completeness | Runtime policy engine internals | Compliance scorecards and control effectiveness trends |

## Business Rules to API/Data/Operational Controls (File-Specific)
| Rule Focus | API Enforcement Touchpoint | Data Model/Contract Tie-In | Operational Control |
|---|---|---|---|
| Preconditions for `use-case-descriptions` workflows must be validated before state mutation. | `GET /v1/analytics/operational-checkpoints` with explicit error taxonomy and correlation IDs. | `workflow_checkpoints, rule_decisions, observability_snapshots` with strict timestamp, actor, and tenant context fields. | Alert on rule-violation rate and route to owner with SLA-backed response. |
| Mutations must be replay-safe and duplicate-proof. | Idempotency checks on mutation endpoints and async consumers. | Uniqueness keys + immutable evidence rows for side-effect tracking. | Replay runbook with pre/post reconciliation and sign-off checklist. |
| Access to sensitive operations must include least-privilege and evidence. | AuthN/AuthZ middleware + policy decision point reason codes. | Audit/event envelopes include policy version and decision outcome. | Quarterly control review and continuous SIEM correlation for anomalies. |

## Interoperability Assumptions for `use-case-descriptions.md`
- Contract versions are explicitly pinned; backward compatibility is managed per versioned API/event schema.
- External dependencies are treated as failure-prone; timeout/retry budgets and fallback states are documented in this file's scenarios.
- Observability correlation (`tenant_id`, `actor_id`, `correlation_id`) is required for all critical-path operations in this document scope.

## Compliance and Security Posture for this Artifact
- Evidence produced by this workflow/design artifact is audit-consumable (who/what/when/why) and linked to incident/postmortem records.
- Sensitive data exposure is minimized using role-scoped access and redaction guidance relevant to `use-case-descriptions.md`.
- Operational controls for this file include detection, containment, recovery, and verification steps with named ownership.
