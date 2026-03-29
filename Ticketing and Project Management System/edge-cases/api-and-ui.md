# Edge Cases - API and UI

| Scenario | Impact | Mitigation |
|----------|--------|------------|
| Client sees stale ticket status after internal update | Trust drops | Push timeline updates via polling or real-time channels with cache invalidation |
| Two users edit the same ticket at once | Last-write-wins causes data loss | Use version checks and conflict messaging |
| Long activity timelines load slowly | UI becomes unusable | Cursor pagination and incremental rendering |
| Search results leak unauthorized project names | Security issue | Enforce scope checks before indexing and before rendering results |
| Attachment preview fails in browser | Evidence appears missing | Provide download fallback and storage health alerting |

## Cross-Cutting Workflow and Operational Governance

### Api And Ui: Document-Specific Scope
- Primary focus for this artifact: **edge-case controls and recovery strategy for api and ui**.
- Implementation handoff expectation: this document must be sufficient for an engineer/architect/operator to implement without hidden assumptions.
- Traceability anchor: `EDGE_CASES_API_AND_UI` should be referenced in backlog items, design reviews, and release checklists when this artifact changes.

### Workflow and State Machine Semantics (EDGE_CASES_API_AND_UI)
- For this document, workflow guidance must **define safe recovery transitions when normal flow is interrupted**.
- Transition definitions must include trigger, actor, guard, failure code, side effects, and audit payload contract.
- Any asynchronous transition path must define idempotency key strategy and replay safety behavior.

### SLA and Escalation Rules (EDGE_CASES_API_AND_UI)
- For this document, SLA guidance must **preserve SLA correctness through outage/retry/manual-intervention situations**.
- Escalation must explicitly identify owner, dwell-time threshold, notification channel, and acknowledgement requirement.
- Breach and near-breach states must be queryable in reporting without recomputing from free-form notes.

### Permission Boundaries (EDGE_CASES_API_AND_UI)
- For this document, permission guidance must **prevent bypass during retries, replays, or emergency overrides**.
- Privileged actions require reason codes, actor identity, and immutable audit entries.
- Client-visible payloads must be explicitly redacted from internal-only and regulated fields.

### Reporting and Metrics (EDGE_CASES_API_AND_UI)
- For this document, reporting guidance must **tag anomalies (duplicates/conflicts/retries) for separate trend analysis**.
- Metric definitions must include numerator/denominator, time window, dimensional keys, and null/missing-data behavior.
- Each metric should map to raw events/tables so results are reproducible during audits.

### Operational Edge-Case Handling (EDGE_CASES_API_AND_UI)
- For this document, operational guidance must **provide scenario-specific operator actions and post-incident remediation tracking**.
- Partial failure handling must identify what is rolled back, compensated, or deferred.
- Recovery completion criteria must be measurable (not subjective) and tied to dashboard/alert signals.

### Implementation Readiness Checklist (EDGE_CASES_API_AND_UI)
| Checklist Item | This Document Must Provide | Validation Evidence |
|---|---|---|
| Workflow Contract Completeness | All relevant states, transitions, and invalid paths for `edge-cases/api-and-ui.md` | Scenario walkthrough + transition test mapping |
| SLA/ Escalation Determinism | Timer, pause, escalation, and override semantics | Policy table review + simulated timer run |
| Authorization Correctness | Role scope, tenant scope, and field visibility boundaries | Auth matrix review + API/UI parity checks |
| Reporting Reproducibility | KPI formulas, dimensions, and source lineage | Recompute KPI from event data sample |
| Operations Recoverability | Degraded-mode and compensation runbook steps | Tabletop/game-day evidence and postmortem template |

