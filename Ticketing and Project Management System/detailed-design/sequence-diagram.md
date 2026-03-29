# Sequence Diagram - Ticketing and Project Management System

```mermaid
sequenceDiagram
    participant Support as Support Agent
    participant UI as Internal Workspace
    participant API as API Layer
    participant Ticket as Ticket Service
    participant Project as Project Service
    participant Workflow as SLA Engine
    participant Notify as Notification Service
    participant Dev as Developer
    participant QA as QA Reviewer

    Support->>UI: Open triage queue item
    UI->>API: PATCH /tickets/{id}/triage
    API->>Ticket: update classification and priority
    Ticket->>Workflow: recalculate SLA timers
    Support->>UI: Assign developer and milestone
    UI->>API: POST /tickets/{id}/assignments
    API->>Ticket: create assignment
    API->>Project: link ticket to milestone
    Ticket->>Notify: send assignment notification
    Dev->>API: PATCH /tickets/{id}/status ready_for_qa
    API->>Ticket: persist work log and status
    QA->>API: POST /tickets/{id}/verification
    alt verification passes
        API->>Ticket: close ticket
        API->>Project: update milestone progress
    else verification fails
        API->>Ticket: reopen ticket with rejection notes
        Ticket->>Notify: notify developer and PM
    end
```

## Cross-Cutting Workflow and Operational Governance

### Sequence Diagram: Document-Specific Scope
- Primary focus for this artifact: **message ordering, timeout strategy, and side-effect guarantees**.
- Implementation handoff expectation: this document must be sufficient for an engineer/architect/operator to implement without hidden assumptions.
- Traceability anchor: `DETAILED_DESIGN_SEQUENCE_DIAGRAM` should be referenced in backlog items, design reviews, and release checklists when this artifact changes.

### Workflow and State Machine Semantics (DETAILED_DESIGN_SEQUENCE_DIAGRAM)
- For this document, workflow guidance must **specify transition APIs, optimistic concurrency, and deterministic error contracts**.
- Transition definitions must include trigger, actor, guard, failure code, side effects, and audit payload contract.
- Any asynchronous transition path must define idempotency key strategy and replay safety behavior.

### SLA and Escalation Rules (DETAILED_DESIGN_SEQUENCE_DIAGRAM)
- For this document, SLA guidance must **formalize calendar/timezone logic and immutable timer checkpoints**.
- Escalation must explicitly identify owner, dwell-time threshold, notification channel, and acknowledgement requirement.
- Breach and near-breach states must be queryable in reporting without recomputing from free-form notes.

### Permission Boundaries (DETAILED_DESIGN_SEQUENCE_DIAGRAM)
- For this document, permission guidance must **specify endpoint scopes, row-level filters, and redaction rules**.
- Privileged actions require reason codes, actor identity, and immutable audit entries.
- Client-visible payloads must be explicitly redacted from internal-only and regulated fields.

### Reporting and Metrics (DETAILED_DESIGN_SEQUENCE_DIAGRAM)
- For this document, reporting guidance must **define schema-level correctness rules and backfill/replay semantics**.
- Metric definitions must include numerator/denominator, time window, dimensional keys, and null/missing-data behavior.
- Each metric should map to raw events/tables so results are reproducible during audits.

### Operational Edge-Case Handling (DETAILED_DESIGN_SEQUENCE_DIAGRAM)
- For this document, operational guidance must **define retryability, DLQ handling, and compensation command contracts**.
- Partial failure handling must identify what is rolled back, compensated, or deferred.
- Recovery completion criteria must be measurable (not subjective) and tied to dashboard/alert signals.

### Implementation Readiness Checklist (DETAILED_DESIGN_SEQUENCE_DIAGRAM)
| Checklist Item | This Document Must Provide | Validation Evidence |
|---|---|---|
| Workflow Contract Completeness | All relevant states, transitions, and invalid paths for `detailed-design/sequence-diagram.md` | Scenario walkthrough + transition test mapping |
| SLA/ Escalation Determinism | Timer, pause, escalation, and override semantics | Policy table review + simulated timer run |
| Authorization Correctness | Role scope, tenant scope, and field visibility boundaries | Auth matrix review + API/UI parity checks |
| Reporting Reproducibility | KPI formulas, dimensions, and source lineage | Recompute KPI from event data sample |
| Operations Recoverability | Degraded-mode and compensation runbook steps | Tabletop/game-day evidence and postmortem template |

### Mermaid Diagram Contract (DETAILED_DESIGN_SEQUENCE_DIAGRAM)
- Diagram syntax must remain Mermaid JS compatible and parse in standard Markdown renderers.
- Every node/edge must map to a term defined in this file to avoid orphaned visual semantics.
- Update both diagram and prose together whenever adding/removing workflow states, actors, services, or data stores.

```mermaid
flowchart TD
  A[Update Sequence Diagram Diagram] --> B[Validate Mermaid Syntax]
  B --> C[Verify Node-to-Prose Mapping]
  C --> D[Review Workflow/SLA/Auth Consistency]
  D --> E[Approve with Implementation Checklist Evidence]
```

