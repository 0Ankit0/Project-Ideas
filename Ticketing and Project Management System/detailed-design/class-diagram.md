# Class Diagram - Ticketing and Project Management System

```mermaid
classDiagram
    class Organization {
      +UUID id
      +string name
      +string supportTier
      +string status
    }
    class User {
      +UUID id
      +string displayName
      +string email
      +string accountType
      +string status
    }
    class Project {
      +UUID id
      +string name
      +string status
      +string health
    }
    class Milestone {
      +UUID id
      +string name
      +date plannedDate
      +date forecastDate
      +string status
    }
    class Task {
      +UUID id
      +string title
      +string status
      +date dueDate
    }
    class Ticket {
      +UUID id
      +string title
      +string type
      +string priority
      +string status
    }
    class TicketAttachment {
      +UUID id
      +string storageKey
      +string mimeType
      +string scanStatus
    }
    class TicketComment {
      +UUID id
      +string visibility
      +text body
    }
    class Assignment {
      +UUID id
      +datetime assignedAt
      +datetime dueAt
    }
    class Release {
      +UUID id
      +string version
      +string status
    }
    class AuditLog {
      +UUID id
      +string action
      +datetime createdAt
    }

    Organization "1" --> "many" User
    Organization "1" --> "many" Project
    Project "1" --> "many" Milestone
    Milestone "1" --> "many" Task
    Project "1" --> "many" Ticket
    Ticket "1" --> "many" TicketAttachment
    Ticket "1" --> "many" TicketComment
    Ticket "1" --> "many" Assignment
    Milestone "0..1" --> "many" Ticket
    Project "1" --> "many" Release
    Release "many" --> "many" Ticket
    User "1" --> "many" AuditLog
```

## Cross-Cutting Workflow and Operational Governance

### Class Diagram: Document-Specific Scope
- Primary focus for this artifact: **entity/value object responsibilities and invariants**.
- Implementation handoff expectation: this document must be sufficient for an engineer/architect/operator to implement without hidden assumptions.
- Traceability anchor: `DETAILED_DESIGN_CLASS_DIAGRAM` should be referenced in backlog items, design reviews, and release checklists when this artifact changes.

### Workflow and State Machine Semantics (DETAILED_DESIGN_CLASS_DIAGRAM)
- For this document, workflow guidance must **specify transition APIs, optimistic concurrency, and deterministic error contracts**.
- Transition definitions must include trigger, actor, guard, failure code, side effects, and audit payload contract.
- Any asynchronous transition path must define idempotency key strategy and replay safety behavior.

### SLA and Escalation Rules (DETAILED_DESIGN_CLASS_DIAGRAM)
- For this document, SLA guidance must **formalize calendar/timezone logic and immutable timer checkpoints**.
- Escalation must explicitly identify owner, dwell-time threshold, notification channel, and acknowledgement requirement.
- Breach and near-breach states must be queryable in reporting without recomputing from free-form notes.

### Permission Boundaries (DETAILED_DESIGN_CLASS_DIAGRAM)
- For this document, permission guidance must **specify endpoint scopes, row-level filters, and redaction rules**.
- Privileged actions require reason codes, actor identity, and immutable audit entries.
- Client-visible payloads must be explicitly redacted from internal-only and regulated fields.

### Reporting and Metrics (DETAILED_DESIGN_CLASS_DIAGRAM)
- For this document, reporting guidance must **define schema-level correctness rules and backfill/replay semantics**.
- Metric definitions must include numerator/denominator, time window, dimensional keys, and null/missing-data behavior.
- Each metric should map to raw events/tables so results are reproducible during audits.

### Operational Edge-Case Handling (DETAILED_DESIGN_CLASS_DIAGRAM)
- For this document, operational guidance must **define retryability, DLQ handling, and compensation command contracts**.
- Partial failure handling must identify what is rolled back, compensated, or deferred.
- Recovery completion criteria must be measurable (not subjective) and tied to dashboard/alert signals.

### Implementation Readiness Checklist (DETAILED_DESIGN_CLASS_DIAGRAM)
| Checklist Item | This Document Must Provide | Validation Evidence |
|---|---|---|
| Workflow Contract Completeness | All relevant states, transitions, and invalid paths for `detailed-design/class-diagram.md` | Scenario walkthrough + transition test mapping |
| SLA/ Escalation Determinism | Timer, pause, escalation, and override semantics | Policy table review + simulated timer run |
| Authorization Correctness | Role scope, tenant scope, and field visibility boundaries | Auth matrix review + API/UI parity checks |
| Reporting Reproducibility | KPI formulas, dimensions, and source lineage | Recompute KPI from event data sample |
| Operations Recoverability | Degraded-mode and compensation runbook steps | Tabletop/game-day evidence and postmortem template |

### Mermaid Diagram Contract (DETAILED_DESIGN_CLASS_DIAGRAM)
- Diagram syntax must remain Mermaid JS compatible and parse in standard Markdown renderers.
- Every node/edge must map to a term defined in this file to avoid orphaned visual semantics.
- Update both diagram and prose together whenever adding/removing workflow states, actors, services, or data stores.

```mermaid
flowchart TD
  A[Update Class Diagram Diagram] --> B[Validate Mermaid Syntax]
  B --> C[Verify Node-to-Prose Mapping]
  C --> D[Review Workflow/SLA/Auth Consistency]
  D --> E[Approve with Implementation Checklist Evidence]
```

