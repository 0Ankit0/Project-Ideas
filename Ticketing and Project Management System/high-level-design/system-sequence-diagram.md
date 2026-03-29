# System Sequence Diagram - Ticketing and Project Management System

## Ticket Intake to Closure

```mermaid
sequenceDiagram
    participant C as Client Requester
    participant P as Client Portal
    participant API as Platform API
    participant T as Ticket Service
    participant A as Attachment Service
    participant W as Workflow / SLA Engine
    participant N as Notification Service
    participant D as Developer
    participant Q as QA Reviewer

    C->>P: Submit ticket + screenshots
    P->>API: POST /tickets
    API->>A: Store and scan attachments
    API->>T: Create ticket record
    T->>W: Start triage SLA
    W->>N: Notify triage queue
    D-->>T: Work progress and resolution notes
    T->>Q: Queue verification
    Q->>T: Pass or reopen result
    T->>N: Notify client of status update
    N-->>C: Status and resolution message
```

## Milestone Change Sequence

```mermaid
sequenceDiagram
    participant PM as Project Manager
    participant UI as Internal Workspace
    participant PS as Project Service
    participant RS as Reporting Service
    participant NS as Notification Service

    PM->>UI: Move ticket into committed milestone
    UI->>PS: Update milestone scope
    PS->>PS: Recalculate forecast and dependencies
    PS->>RS: Publish new project health metrics
    alt Forecast slips or scope grows
        PS->>NS: Notify stakeholders and create change review
    end
```

## Cross-Cutting Workflow and Operational Governance

### System Sequence Diagram: Document-Specific Scope
- Primary focus for this artifact: **command/query sequencing, retries, and compensations**.
- Implementation handoff expectation: this document must be sufficient for an engineer/architect/operator to implement without hidden assumptions.
- Traceability anchor: `HIGH_LEVEL_DESIGN_SYSTEM_SEQUENCE_DIAGRAM` should be referenced in backlog items, design reviews, and release checklists when this artifact changes.

### Workflow and State Machine Semantics (HIGH_LEVEL_DESIGN_SYSTEM_SEQUENCE_DIAGRAM)
- For this document, workflow guidance must **declare orchestration boundaries and transaction scopes for state changes**.
- Transition definitions must include trigger, actor, guard, failure code, side effects, and audit payload contract.
- Any asynchronous transition path must define idempotency key strategy and replay safety behavior.

### SLA and Escalation Rules (HIGH_LEVEL_DESIGN_SYSTEM_SEQUENCE_DIAGRAM)
- For this document, SLA guidance must **assign timer/escalation service responsibilities and anti-storm controls**.
- Escalation must explicitly identify owner, dwell-time threshold, notification channel, and acknowledgement requirement.
- Breach and near-breach states must be queryable in reporting without recomputing from free-form notes.

### Permission Boundaries (HIGH_LEVEL_DESIGN_SYSTEM_SEQUENCE_DIAGRAM)
- For this document, permission guidance must **document trust boundaries and identity propagation across services**.
- Privileged actions require reason codes, actor identity, and immutable audit entries.
- Client-visible payloads must be explicitly redacted from internal-only and regulated fields.

### Reporting and Metrics (HIGH_LEVEL_DESIGN_SYSTEM_SEQUENCE_DIAGRAM)
- For this document, reporting guidance must **identify analytics pipeline ownership and reproducibility guarantees**.
- Metric definitions must include numerator/denominator, time window, dimensional keys, and null/missing-data behavior.
- Each metric should map to raw events/tables so results are reproducible during audits.

### Operational Edge-Case Handling (HIGH_LEVEL_DESIGN_SYSTEM_SEQUENCE_DIAGRAM)
- For this document, operational guidance must **declare degraded-mode capabilities and restoration decision criteria**.
- Partial failure handling must identify what is rolled back, compensated, or deferred.
- Recovery completion criteria must be measurable (not subjective) and tied to dashboard/alert signals.

### Implementation Readiness Checklist (HIGH_LEVEL_DESIGN_SYSTEM_SEQUENCE_DIAGRAM)
| Checklist Item | This Document Must Provide | Validation Evidence |
|---|---|---|
| Workflow Contract Completeness | All relevant states, transitions, and invalid paths for `high-level-design/system-sequence-diagram.md` | Scenario walkthrough + transition test mapping |
| SLA/ Escalation Determinism | Timer, pause, escalation, and override semantics | Policy table review + simulated timer run |
| Authorization Correctness | Role scope, tenant scope, and field visibility boundaries | Auth matrix review + API/UI parity checks |
| Reporting Reproducibility | KPI formulas, dimensions, and source lineage | Recompute KPI from event data sample |
| Operations Recoverability | Degraded-mode and compensation runbook steps | Tabletop/game-day evidence and postmortem template |

### Mermaid Diagram Contract (HIGH_LEVEL_DESIGN_SYSTEM_SEQUENCE_DIAGRAM)
- Diagram syntax must remain Mermaid JS compatible and parse in standard Markdown renderers.
- Every node/edge must map to a term defined in this file to avoid orphaned visual semantics.
- Update both diagram and prose together whenever adding/removing workflow states, actors, services, or data stores.

```mermaid
flowchart TD
  A[Update System Sequence Diagram Diagram] --> B[Validate Mermaid Syntax]
  B --> C[Verify Node-to-Prose Mapping]
  C --> D[Review Workflow/SLA/Auth Consistency]
  D --> E[Approve with Implementation Checklist Evidence]
```

