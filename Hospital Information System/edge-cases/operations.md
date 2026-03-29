# Operations

## Day-2 Readiness
- SLO dashboard for availability, latency, and data freshness.
- Runbooks for incident triage, rollback, replay, and backfill.
- Capacity planning based on peak traffic and queue depth trends.

## Incident Lifecycle
1. Detect and classify severity with ownership routing.
2. Contain blast radius and communicate stakeholder impact.
3. Recover service and data consistency.
4. Publish postmortem with corrective actions and deadlines.

---


## In-Depth Operational Readiness
### SRE/Operations Control Plane
- Golden signals tracked per capability: latency, error rate, saturation, and data freshness.
- Error budgets enforce release throttling when critical-path SLO burn exceeds thresholds.
- Incident command model includes clinical liaison role for patient-impact interpretation.

## File-Specific Implementation Boundaries
This artifact is implementation-focused on **incident lifecycle, SLO governance, and service ownership model**. The boundaries below are specific to `edge-cases/operations.md` and are intentionally not reused as generic filler text.

| Boundary Slice | In Scope for this File | Out of Scope for this File | Implementation Consequence |
|---|---|---|---|
| Detection Plane | Signals, anomaly thresholds, and incident trigger criteria | Permanent remediation features | Early detection with low alert noise |
| Containment Plane | Blast-radius limiting actions and operator approvals | Long-term optimization work | Safe short-term control while preserving evidence |
| Recovery Plane | Replay/backfill/unwind sequencing and verification | Product roadmap changes | Deterministic restoration and closure evidence |

## Business Rules to API/Data/Operational Controls (File-Specific)
| Rule Focus | API Enforcement Touchpoint | Data Model/Contract Tie-In | Operational Control |
|---|---|---|---|
| Preconditions for `operations` workflows must be validated before state mutation. | `POST /v1/operations/incidents/{id}/actions` with explicit error taxonomy and correlation IDs. | `incident_timeline, containment_actions, reconciliation_jobs` with strict timestamp, actor, and tenant context fields. | Alert on rule-violation rate and route to owner with SLA-backed response. |
| Mutations must be replay-safe and duplicate-proof. | Idempotency checks on mutation endpoints and async consumers. | Uniqueness keys + immutable evidence rows for side-effect tracking. | Replay runbook with pre/post reconciliation and sign-off checklist. |
| Access to sensitive operations must include least-privilege and evidence. | AuthN/AuthZ middleware + policy decision point reason codes. | Audit/event envelopes include policy version and decision outcome. | Quarterly control review and continuous SIEM correlation for anomalies. |

## Interoperability Assumptions for `operations.md`
- Contract versions are explicitly pinned; backward compatibility is managed per versioned API/event schema.
- External dependencies are treated as failure-prone; timeout/retry budgets and fallback states are documented in this file's scenarios.
- Observability correlation (`tenant_id`, `actor_id`, `correlation_id`) is required for all critical-path operations in this document scope.

## Compliance and Security Posture for this Artifact
- Evidence produced by this workflow/design artifact is audit-consumable (who/what/when/why) and linked to incident/postmortem records.
- Sensitive data exposure is minimized using role-scoped access and redaction guidance relevant to `operations.md`.
- Operational controls for this file include detection, containment, recovery, and verification steps with named ownership.
