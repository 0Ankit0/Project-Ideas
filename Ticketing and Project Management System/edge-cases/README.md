# Edge Cases - Ticketing and Project Management System

This folder captures cross-cutting scenarios that can break ticket intake, assignment, milestone governance, user experience, security, or operations if they are not handled deliberately.

## Contents

- `ticket-intake-and-attachments.md`
- `assignment-and-sla.md`
- `project-planning-and-milestones.md`
- `change-management-and-replanning.md`
- `api-and-ui.md`
- `security-and-compliance.md`
- `operations.md`

## Full Cross-Cutting Edge-Case Catalog

| Category | Edge Case | Primary Risk | Canonical Mitigation Artifact |
|---|---|---|---|
| Assignment & SLA | Stale assignment after assignee inactivity or schedule mismatch | Ticket remains owned but unworked, causing hidden SLA erosion | `assignment-and-sla.md` stale-assignment detector + reassignment workflow |
| Assignment & SLA | SLA breach timing drift from clock skew/retry delays | Incorrect breach timestamps and escalations | `assignment-and-sla.md` drift detection + recompute controls |
| Workflow Integrity | Conflicting status transitions from concurrent updates | Illegal state history and duplicate side effects | `assignment-and-sla.md` optimistic locking + idempotent transitions |
| Attachments & Security | Malware scan delays creating long pending states | Unsafe downloads or blocked delivery timelines | `ticket-intake-and-attachments.md` pending-scan policy + secops escalation |
| Project Planning | Dependency loops across tickets/tasks | Deadlocked plans and incorrect critical path | `project-planning-and-milestones.md` cycle detection + block propagation |
| Change Management | Mid-sprint scope injection without governance | Milestone churn and SLA breach spillover | `change-management-and-replanning.md` change control gates |
| API/UI | Divergent client/internal status rendering | User confusion and incorrect operational actions | `api-and-ui.md` contract tests and parity checks |
| Security & Compliance | Privileged override without reason code | Audit non-compliance and abuse risk | `security-and-compliance.md` enforced reason code + immutable audit |
| Operations | Queue backlog during regional degradation | Cascading latency and delayed escalations | `operations.md` priority queue degradation mode runbook |

## Catalog Usage Rules
- Every edge case must map to an owner team, detector signal, automated reaction, and manual fallback.
- Every detector must have a dashboard metric and alert threshold documented before production rollout.
- Every mitigation must be tested in at least one integration or game-day scenario each release quarter.

## Cross-Cutting Workflow and Operational Governance

### Readme: Document-Specific Scope
- Primary focus for this artifact: **program-level governance, integration boundaries, and delivery accountability**.
- Implementation handoff expectation: this document must be sufficient for an engineer/architect/operator to implement without hidden assumptions.
- Traceability anchor: `EDGE_CASES_README` should be referenced in backlog items, design reviews, and release checklists when this artifact changes.

### Workflow and State Machine Semantics (EDGE_CASES_README)
- For this document, workflow guidance must **define safe recovery transitions when normal flow is interrupted**.
- Transition definitions must include trigger, actor, guard, failure code, side effects, and audit payload contract.
- Any asynchronous transition path must define idempotency key strategy and replay safety behavior.

### SLA and Escalation Rules (EDGE_CASES_README)
- For this document, SLA guidance must **preserve SLA correctness through outage/retry/manual-intervention situations**.
- Escalation must explicitly identify owner, dwell-time threshold, notification channel, and acknowledgement requirement.
- Breach and near-breach states must be queryable in reporting without recomputing from free-form notes.

### Permission Boundaries (EDGE_CASES_README)
- For this document, permission guidance must **prevent bypass during retries, replays, or emergency overrides**.
- Privileged actions require reason codes, actor identity, and immutable audit entries.
- Client-visible payloads must be explicitly redacted from internal-only and regulated fields.

### Reporting and Metrics (EDGE_CASES_README)
- For this document, reporting guidance must **tag anomalies (duplicates/conflicts/retries) for separate trend analysis**.
- Metric definitions must include numerator/denominator, time window, dimensional keys, and null/missing-data behavior.
- Each metric should map to raw events/tables so results are reproducible during audits.

### Operational Edge-Case Handling (EDGE_CASES_README)
- For this document, operational guidance must **provide scenario-specific operator actions and post-incident remediation tracking**.
- Partial failure handling must identify what is rolled back, compensated, or deferred.
- Recovery completion criteria must be measurable (not subjective) and tied to dashboard/alert signals.

### Implementation Readiness Checklist (EDGE_CASES_README)
| Checklist Item | This Document Must Provide | Validation Evidence |
|---|---|---|
| Workflow Contract Completeness | All relevant states, transitions, and invalid paths for `edge-cases/README.md` | Scenario walkthrough + transition test mapping |
| SLA/ Escalation Determinism | Timer, pause, escalation, and override semantics | Policy table review + simulated timer run |
| Authorization Correctness | Role scope, tenant scope, and field visibility boundaries | Auth matrix review + API/UI parity checks |
| Reporting Reproducibility | KPI formulas, dimensions, and source lineage | Recompute KPI from event data sample |
| Operations Recoverability | Degraded-mode and compensation runbook steps | Tabletop/game-day evidence and postmortem template |
