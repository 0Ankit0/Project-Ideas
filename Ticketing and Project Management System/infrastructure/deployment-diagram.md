# Deployment Diagram - Ticketing and Project Management System

```mermaid
flowchart TB
    internet[Internet / Client Network] --> waf[WAF / CDN]
    corp[Corporate Network / VPN] --> internalLb[Internal Load Balancer]
    waf --> clientWeb[Client Portal Frontend]
    internalLb --> internalWeb[Internal Workspace Frontend]
    clientWeb --> api[Application API Cluster]
    internalWeb --> api
    api --> worker[Workflow Worker Cluster]
    api --> db[(Managed PostgreSQL)]
    api --> obj[(Object Storage)]
    api --> bus[(Managed Queue / Bus)]
    worker --> db
    worker --> bus
```

## Deployment Notes
- Client-facing and internal frontends are separated at the edge even when they share backend services.
- Workers handle asynchronous scanning, notifications, SLA timers, and report projection.
- Object storage is required for evidence files and exported reports.

## Cross-Cutting Workflow and Operational Governance

### Deployment Diagram: Document-Specific Scope
- Primary focus for this artifact: **runtime topology, network segmentation, and scaling/failover strategy**.
- Implementation handoff expectation: this document must be sufficient for an engineer/architect/operator to implement without hidden assumptions.
- Traceability anchor: `INFRASTRUCTURE_DEPLOYMENT_DIAGRAM` should be referenced in backlog items, design reviews, and release checklists when this artifact changes.

### Workflow and State Machine Semantics (INFRASTRUCTURE_DEPLOYMENT_DIAGRAM)
- For this document, workflow guidance must **guarantee durable event flow and timer precision for workflow execution**.
- Transition definitions must include trigger, actor, guard, failure code, side effects, and audit payload contract.
- Any asynchronous transition path must define idempotency key strategy and replay safety behavior.

### SLA and Escalation Rules (INFRASTRUCTURE_DEPLOYMENT_DIAGRAM)
- For this document, SLA guidance must **ensure queue/scheduler reliability and time synchronization guarantees**.
- Escalation must explicitly identify owner, dwell-time threshold, notification channel, and acknowledgement requirement.
- Breach and near-breach states must be queryable in reporting without recomputing from free-form notes.

### Permission Boundaries (INFRASTRUCTURE_DEPLOYMENT_DIAGRAM)
- For this document, permission guidance must **implement IAM/network boundaries and privileged-access controls**.
- Privileged actions require reason codes, actor identity, and immutable audit entries.
- Client-visible payloads must be explicitly redacted from internal-only and regulated fields.

### Reporting and Metrics (INFRASTRUCTURE_DEPLOYMENT_DIAGRAM)
- For this document, reporting guidance must **ensure telemetry durability/retention for ops and compliance reporting**.
- Metric definitions must include numerator/denominator, time window, dimensional keys, and null/missing-data behavior.
- Each metric should map to raw events/tables so results are reproducible during audits.

### Operational Edge-Case Handling (INFRASTRUCTURE_DEPLOYMENT_DIAGRAM)
- For this document, operational guidance must **codify failover, backup restore, and game-day validation procedures**.
- Partial failure handling must identify what is rolled back, compensated, or deferred.
- Recovery completion criteria must be measurable (not subjective) and tied to dashboard/alert signals.

### Implementation Readiness Checklist (INFRASTRUCTURE_DEPLOYMENT_DIAGRAM)
| Checklist Item | This Document Must Provide | Validation Evidence |
|---|---|---|
| Workflow Contract Completeness | All relevant states, transitions, and invalid paths for `infrastructure/deployment-diagram.md` | Scenario walkthrough + transition test mapping |
| SLA/ Escalation Determinism | Timer, pause, escalation, and override semantics | Policy table review + simulated timer run |
| Authorization Correctness | Role scope, tenant scope, and field visibility boundaries | Auth matrix review + API/UI parity checks |
| Reporting Reproducibility | KPI formulas, dimensions, and source lineage | Recompute KPI from event data sample |
| Operations Recoverability | Degraded-mode and compensation runbook steps | Tabletop/game-day evidence and postmortem template |

### Mermaid Diagram Contract (INFRASTRUCTURE_DEPLOYMENT_DIAGRAM)
- Diagram syntax must remain Mermaid JS compatible and parse in standard Markdown renderers.
- Every node/edge must map to a term defined in this file to avoid orphaned visual semantics.
- Update both diagram and prose together whenever adding/removing workflow states, actors, services, or data stores.

```mermaid
flowchart TD
  A[Update Deployment Diagram Diagram] --> B[Validate Mermaid Syntax]
  B --> C[Verify Node-to-Prose Mapping]
  C --> D[Review Workflow/SLA/Auth Consistency]
  D --> E[Approve with Implementation Checklist Evidence]
```

