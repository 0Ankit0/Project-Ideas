# Patient Identity Merge

## Scenario
MPI collisions and safe chart merge workflows.

## Detection Signals
- Error-rate and latency anomalies on affected services.
- Data integrity checks (duplicate keys, missing transitions, imbalance alerts).
- Queue lag or webhook retry saturation above SLO thresholds.

## Immediate Containment
- Pause risky automation path via feature flag/runbook switch.
- Route affected records into review queue with owner assignment.
- Notify operations channel with incident context and blast radius.

## Recovery Steps
- Reconcile canonical state from source-of-truth events and logs.
- Apply deterministic compensating updates with audit annotations.
- Backfill downstream projections and verify invariant checks pass.

## Prevention
- Add contract tests and chaos scenarios for this edge condition.
- Instrument specific leading indicators and alert tuning.

---


## In-Depth Merge Safety Model
### Merge Preconditions
- Confidence score threshold + mandatory human review for risky demographics mismatch.
- Contraindications: active legal hold conflict, neonatal twin collision, or unresolved deceased status discrepancy.
- Unmerge capability must remain available with complete lineage restoration.

## File-Specific Implementation Boundaries
This artifact is implementation-focused on **MPI merge/unmerge safety, lineage, and contraindication handling**. The boundaries below are specific to `edge-cases/patient-identity-merge.md` and are intentionally not reused as generic filler text.

| Boundary Slice | In Scope for this File | Out of Scope for this File | Implementation Consequence |
|---|---|---|---|
| Detection Plane | Signals, anomaly thresholds, and incident trigger criteria | Permanent remediation features | Early detection with low alert noise |
| Containment Plane | Blast-radius limiting actions and operator approvals | Long-term optimization work | Safe short-term control while preserving evidence |
| Recovery Plane | Replay/backfill/unwind sequencing and verification | Product roadmap changes | Deterministic restoration and closure evidence |

## Business Rules to API/Data/Operational Controls (File-Specific)
| Rule Focus | API Enforcement Touchpoint | Data Model/Contract Tie-In | Operational Control |
|---|---|---|---|
| Preconditions for `patient-identity-merge` workflows must be validated before state mutation. | `POST /v1/operations/incidents/{id}/actions` with explicit error taxonomy and correlation IDs. | `incident_timeline, containment_actions, reconciliation_jobs` with strict timestamp, actor, and tenant context fields. | Alert on rule-violation rate and route to owner with SLA-backed response. |
| Mutations must be replay-safe and duplicate-proof. | Idempotency checks on mutation endpoints and async consumers. | Uniqueness keys + immutable evidence rows for side-effect tracking. | Replay runbook with pre/post reconciliation and sign-off checklist. |
| Access to sensitive operations must include least-privilege and evidence. | AuthN/AuthZ middleware + policy decision point reason codes. | Audit/event envelopes include policy version and decision outcome. | Quarterly control review and continuous SIEM correlation for anomalies. |

## Interoperability Assumptions for `patient-identity-merge.md`
- Contract versions are explicitly pinned; backward compatibility is managed per versioned API/event schema.
- External dependencies are treated as failure-prone; timeout/retry budgets and fallback states are documented in this file's scenarios.
- Observability correlation (`tenant_id`, `actor_id`, `correlation_id`) is required for all critical-path operations in this document scope.

## Compliance and Security Posture for this Artifact
- Evidence produced by this workflow/design artifact is audit-consumable (who/what/when/why) and linked to incident/postmortem records.
- Sensitive data exposure is minimized using role-scoped access and redaction guidance relevant to `patient-identity-merge.md`.
- Operational controls for this file include detection, containment, recovery, and verification steps with named ownership.
