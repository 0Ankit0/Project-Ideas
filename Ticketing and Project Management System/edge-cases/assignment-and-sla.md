# Edge Cases - Assignment and SLA

| Scenario | Impact | Mitigation |
|----------|--------|------------|
| No engineer with the required skill is available | Ticket sits unowned | Allow queue ownership plus escalation to PM or engineering manager |
| Assigned developer goes on leave | SLA breach risk | Support reassignment with preserved ownership history and alerts |
| Client is waiting to provide details | Resolution timer becomes misleading | Support approved SLA pause states with explicit reason codes |
| Priority is set too low during triage | Critical issue misses response window | Require override approval for downgrading incidents after evidence review |
| One ticket blocks multiple milestones | Risk hidden in individual queues | Propagate blocker state to all linked milestones and portfolio reporting |
| Stale assignment (assignee inactive/off-shift but ticket still owned) | Hidden ownership gap and delayed response | Heartbeat + schedule-aware stale-assignment detector requeues after threshold and notifies manager |
| SLA breach timing drift caused by worker clock skew | False breach/non-breach events and audit inconsistency | Use monotonic time, NTP drift alarms, and periodic deadline recomputation from event history |
| Conflicting status transitions from concurrent actors (e.g., close vs reopen) | State corruption, duplicate notifications, inconsistent timelines | Optimistic locking on version, transition idempotency keys, and conflict response requiring retry with latest version |
| Attachment malware scan delays beyond policy window | Potentially unsafe files or blocked workflows | Enforce pending-scan download block, delayed-scan escalation, and controlled override only for security-approved roles |

## Expanded Edge-Case Catalog (Assignment & SLA)

| Edge Case ID | Trigger | Detection Signal | Automated Action | Manual Action | Metrics |
|---|---|---|---|---|---|
| `ASG-STALE-001` | Assignee has no activity heartbeat for 30 min during active ownership | `assignment_last_seen_at` lag + on-call calendar mismatch | transition ticket to `reassignment_pending`; notify queue owner | manager confirms reassignment within 15 min | stale assignment count, median reassignment time |
| `SLA-DRIFT-002` | timer worker clock drift > 5s/10 min | drift monitor event + timer mismatch sample | mark timer `degraded_clock`; rerun recomputation batch | ops validates NTP + node quarantine | drift incidents/week, corrected deadline delta |
| `WF-CONFLICT-003` | two legal transitions submitted against same ticket version | optimistic lock failure + duplicate idempotency key | reject second transition with `409` and emit `TransitionConflictDetected` | actor retries using refreshed state | transition conflict rate by workflow step |
| `ATT-SCAN-004` | attachment pending scan > 15 min | queue age + attachment state monitor | send delayed-scan alert; route to backup scanner pool | SecOps triages suspicious backlog | p95 scan latency, pending-scan backlog |

## Cross-Cutting Workflow and Operational Governance

### Assignment And Sla: Document-Specific Scope
- Primary focus for this artifact: **edge-case controls and recovery strategy for assignment and sla**.
- Implementation handoff expectation: this document must be sufficient for an engineer/architect/operator to implement without hidden assumptions.
- Traceability anchor: `EDGE_CASES_ASSIGNMENT_AND_SLA` should be referenced in backlog items, design reviews, and release checklists when this artifact changes.

### Workflow and State Machine Semantics (EDGE_CASES_ASSIGNMENT_AND_SLA)
- For this document, workflow guidance must **define safe recovery transitions when normal flow is interrupted**.
- Transition definitions must include trigger, actor, guard, failure code, side effects, and audit payload contract.
- Any asynchronous transition path must define idempotency key strategy and replay safety behavior.

### SLA and Escalation Rules (EDGE_CASES_ASSIGNMENT_AND_SLA)
- For this document, SLA guidance must **preserve SLA correctness through outage/retry/manual-intervention situations**.
- Escalation must explicitly identify owner, dwell-time threshold, notification channel, and acknowledgement requirement.
- Breach and near-breach states must be queryable in reporting without recomputing from free-form notes.

### Permission Boundaries (EDGE_CASES_ASSIGNMENT_AND_SLA)
- For this document, permission guidance must **prevent bypass during retries, replays, or emergency overrides**.
- Privileged actions require reason codes, actor identity, and immutable audit entries.
- Client-visible payloads must be explicitly redacted from internal-only and regulated fields.

### Reporting and Metrics (EDGE_CASES_ASSIGNMENT_AND_SLA)
- For this document, reporting guidance must **tag anomalies (duplicates/conflicts/retries) for separate trend analysis**.
- Metric definitions must include numerator/denominator, time window, dimensional keys, and null/missing-data behavior.
- Each metric should map to raw events/tables so results are reproducible during audits.

### Operational Edge-Case Handling (EDGE_CASES_ASSIGNMENT_AND_SLA)
- For this document, operational guidance must **provide scenario-specific operator actions and post-incident remediation tracking**.
- Partial failure handling must identify what is rolled back, compensated, or deferred.
- Recovery completion criteria must be measurable (not subjective) and tied to dashboard/alert signals.

### Implementation Readiness Checklist (EDGE_CASES_ASSIGNMENT_AND_SLA)
| Checklist Item | This Document Must Provide | Validation Evidence |
|---|---|---|
| Workflow Contract Completeness | All relevant states, transitions, and invalid paths for `edge-cases/assignment-and-sla.md` | Scenario walkthrough + transition test mapping |
| SLA/ Escalation Determinism | Timer, pause, escalation, and override semantics | Policy table review + simulated timer run |
| Authorization Correctness | Role scope, tenant scope, and field visibility boundaries | Auth matrix review + API/UI parity checks |
| Reporting Reproducibility | KPI formulas, dimensions, and source lineage | Recompute KPI from event data sample |
| Operations Recoverability | Degraded-mode and compensation runbook steps | Tabletop/game-day evidence and postmortem template |
