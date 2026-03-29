# Activity Diagram - Ticketing and Project Management System

## Ticket-to-Resolution Flow

```mermaid
flowchart TD
    start([Client reports issue]) --> create[Create ticket and upload image evidence]
    create --> validate{Valid intake and allowed attachment?}
    validate -- No --> clarify[Request clarification or reject upload]
    clarify --> create
    validate -- Yes --> triage[Triage, categorize, and set priority]
    triage --> duplicate{Duplicate or known issue?}
    duplicate -- Yes --> link[Link to existing ticket and notify client]
    duplicate -- No --> assign[Assign to developer or team queue]
    assign --> plan{Needs milestone or change request?}
    plan -- Yes --> milestone[Link to milestone / create backlog task]
    plan -- No --> work[Developer investigates and fixes]
    milestone --> work
    work --> blocked{Blocked?}
    blocked -- Yes --> escalate[Escalate blocker and update risk]
    escalate --> work
    blocked -- No --> qa[Send to QA verification]
    qa --> passed{Fix verified?}
    passed -- No --> reopen[Reopen ticket with failure notes]
    reopen --> work
    passed -- Yes --> close[Close ticket and update release/project metrics]
    close --> end([Client informed and records retained])
```

## Cross-Cutting Workflow and Operational Governance

### Activity Diagram: Document-Specific Scope
- Primary focus for this artifact: **step-level control flow, forks/joins, and failure loops**.
- Implementation handoff expectation: this document must be sufficient for an engineer/architect/operator to implement without hidden assumptions.
- Traceability anchor: `ANALYSIS_ACTIVITY_DIAGRAM` should be referenced in backlog items, design reviews, and release checklists when this artifact changes.

### Workflow and State Machine Semantics (ANALYSIS_ACTIVITY_DIAGRAM)
- For this document, workflow guidance must **bind business scenarios to evented state transitions including negative paths**.
- Transition definitions must include trigger, actor, guard, failure code, side effects, and audit payload contract.
- Any asynchronous transition path must define idempotency key strategy and replay safety behavior.

### SLA and Escalation Rules (ANALYSIS_ACTIVITY_DIAGRAM)
- For this document, SLA guidance must **model pause/resume/escalate behaviors and ownership transfers**.
- Escalation must explicitly identify owner, dwell-time threshold, notification channel, and acknowledgement requirement.
- Breach and near-breach states must be queryable in reporting without recomputing from free-form notes.

### Permission Boundaries (ANALYSIS_ACTIVITY_DIAGRAM)
- For this document, permission guidance must **map actor boundaries and authorization failures in primary/alternate flows**.
- Privileged actions require reason codes, actor identity, and immutable audit entries.
- Client-visible payloads must be explicitly redacted from internal-only and regulated fields.

### Reporting and Metrics (ANALYSIS_ACTIVITY_DIAGRAM)
- For this document, reporting guidance must **trace KPI source events and decision points for operational governance**.
- Metric definitions must include numerator/denominator, time window, dimensional keys, and null/missing-data behavior.
- Each metric should map to raw events/tables so results are reproducible during audits.

### Operational Edge-Case Handling (ANALYSIS_ACTIVITY_DIAGRAM)
- For this document, operational guidance must **cover compensation behavior for partial success and temporal inconsistency**.
- Partial failure handling must identify what is rolled back, compensated, or deferred.
- Recovery completion criteria must be measurable (not subjective) and tied to dashboard/alert signals.

### Implementation Readiness Checklist (ANALYSIS_ACTIVITY_DIAGRAM)
| Checklist Item | This Document Must Provide | Validation Evidence |
|---|---|---|
| Workflow Contract Completeness | All relevant states, transitions, and invalid paths for `analysis/activity-diagram.md` | Scenario walkthrough + transition test mapping |
| SLA/ Escalation Determinism | Timer, pause, escalation, and override semantics | Policy table review + simulated timer run |
| Authorization Correctness | Role scope, tenant scope, and field visibility boundaries | Auth matrix review + API/UI parity checks |
| Reporting Reproducibility | KPI formulas, dimensions, and source lineage | Recompute KPI from event data sample |
| Operations Recoverability | Degraded-mode and compensation runbook steps | Tabletop/game-day evidence and postmortem template |

### Mermaid Diagram Contract (ANALYSIS_ACTIVITY_DIAGRAM)
- Diagram syntax must remain Mermaid JS compatible and parse in standard Markdown renderers.
- Every node/edge must map to a term defined in this file to avoid orphaned visual semantics.
- Update both diagram and prose together whenever adding/removing workflow states, actors, services, or data stores.

```mermaid
flowchart TD
  A[Update Activity Diagram Diagram] --> B[Validate Mermaid Syntax]
  B --> C[Verify Node-to-Prose Mapping]
  C --> D[Review Workflow/SLA/Auth Consistency]
  D --> E[Approve with Implementation Checklist Evidence]
```

