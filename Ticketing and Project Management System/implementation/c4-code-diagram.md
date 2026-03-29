# C4 Code Diagram - Ticketing and Project Management System

```mermaid
flowchart TB
    subgraph api[apps/api]
        controllers[Controllers]
        guards[Auth Guards]
        commands[Command Handlers]
        queries[Query Handlers]
    end

    subgraph domain[packages/domain]
        tickets[Tickets Module]
        projects[Projects Module]
        releases[Releases Module]
        access[Access Module]
    end

    subgraph worker[apps/worker]
        timers[SLA Timers]
        scans[Attachment Scan Processor]
        projections[Reporting Projector]
        notifications[Notification Jobs]
    end

    controllers --> guards
    controllers --> commands
    controllers --> queries
    commands --> tickets
    commands --> projects
    commands --> releases
    queries --> tickets
    queries --> projects
    queries --> access
    timers --> tickets
    scans --> tickets
    projections --> projects
    notifications --> releases
```

## Cross-Cutting Workflow and Operational Governance

### C4 Code Diagram: Document-Specific Scope
- Primary focus for this artifact: **package/module boundaries and domain-policy encapsulation**.
- Implementation handoff expectation: this document must be sufficient for an engineer/architect/operator to implement without hidden assumptions.
- Traceability anchor: `IMPLEMENTATION_C4_CODE_DIAGRAM` should be referenced in backlog items, design reviews, and release checklists when this artifact changes.

### Workflow and State Machine Semantics (IMPLEMENTATION_C4_CODE_DIAGRAM)
- For this document, workflow guidance must **enforce state semantics in code paths, tests, and release gates**.
- Transition definitions must include trigger, actor, guard, failure code, side effects, and audit payload contract.
- Any asynchronous transition path must define idempotency key strategy and replay safety behavior.

### SLA and Escalation Rules (IMPLEMENTATION_C4_CODE_DIAGRAM)
- For this document, SLA guidance must **implement recomputable SLA engine behavior and regression coverage**.
- Escalation must explicitly identify owner, dwell-time threshold, notification channel, and acknowledgement requirement.
- Breach and near-breach states must be queryable in reporting without recomputing from free-form notes.

### Permission Boundaries (IMPLEMENTATION_C4_CODE_DIAGRAM)
- For this document, permission guidance must **verify API/UI authorization parity using contract tests**.
- Privileged actions require reason codes, actor identity, and immutable audit entries.
- Client-visible payloads must be explicitly redacted from internal-only and regulated fields.

### Reporting and Metrics (IMPLEMENTATION_C4_CODE_DIAGRAM)
- For this document, reporting guidance must **ship dashboards-as-code and data quality tests in CI**.
- Metric definitions must include numerator/denominator, time window, dimensional keys, and null/missing-data behavior.
- Each metric should map to raw events/tables so results are reproducible during audits.

### Operational Edge-Case Handling (IMPLEMENTATION_C4_CODE_DIAGRAM)
- For this document, operational guidance must **wire executable runbooks to deployment and incident response gates**.
- Partial failure handling must identify what is rolled back, compensated, or deferred.
- Recovery completion criteria must be measurable (not subjective) and tied to dashboard/alert signals.

### Implementation Readiness Checklist (IMPLEMENTATION_C4_CODE_DIAGRAM)
| Checklist Item | This Document Must Provide | Validation Evidence |
|---|---|---|
| Workflow Contract Completeness | All relevant states, transitions, and invalid paths for `implementation/c4-code-diagram.md` | Scenario walkthrough + transition test mapping |
| SLA/ Escalation Determinism | Timer, pause, escalation, and override semantics | Policy table review + simulated timer run |
| Authorization Correctness | Role scope, tenant scope, and field visibility boundaries | Auth matrix review + API/UI parity checks |
| Reporting Reproducibility | KPI formulas, dimensions, and source lineage | Recompute KPI from event data sample |
| Operations Recoverability | Degraded-mode and compensation runbook steps | Tabletop/game-day evidence and postmortem template |

### Mermaid Diagram Contract (IMPLEMENTATION_C4_CODE_DIAGRAM)
- Diagram syntax must remain Mermaid JS compatible and parse in standard Markdown renderers.
- Every node/edge must map to a term defined in this file to avoid orphaned visual semantics.
- Update both diagram and prose together whenever adding/removing workflow states, actors, services, or data stores.

```mermaid
flowchart TD
  A[Update C4 Code Diagram Diagram] --> B[Validate Mermaid Syntax]
  B --> C[Verify Node-to-Prose Mapping]
  C --> D[Review Workflow/SLA/Auth Consistency]
  D --> E[Approve with Implementation Checklist Evidence]
```

