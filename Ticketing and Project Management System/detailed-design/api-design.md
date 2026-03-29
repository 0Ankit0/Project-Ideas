# API Design - Ticketing and Project Management System

## API Style
- RESTful JSON APIs with organization and role-based authorization.
- Cursor pagination for activity-heavy collections.
- Idempotency keys for create operations exposed to client portals.
- Attachment uploads use pre-signed object storage URLs or a direct upload proxy.

## Core Endpoints

| Area | Method | Endpoint | Purpose |
|------|--------|----------|---------|
| Tickets | POST | `/api/v1/tickets` | Create a new ticket |
| Tickets | GET | `/api/v1/tickets/{ticketId}` | Fetch ticket detail |
| Tickets | PATCH | `/api/v1/tickets/{ticketId}` | Update status, fields, or metadata |
| Tickets | POST | `/api/v1/tickets/{ticketId}/comments` | Add comment or clarification |
| Tickets | POST | `/api/v1/tickets/{ticketId}/attachments` | Register attachment upload |
| Tickets | POST | `/api/v1/tickets/{ticketId}/assignments` | Assign or reassign owner |
| Projects | POST | `/api/v1/projects` | Create project |
| Projects | POST | `/api/v1/projects/{projectId}/milestones` | Create milestone |
| Projects | POST | `/api/v1/milestones/{milestoneId}/tasks` | Create task |
| Projects | PATCH | `/api/v1/milestones/{milestoneId}` | Update milestone plan |
| Releases | POST | `/api/v1/releases` | Create release or hotfix |
| Reports | GET | `/api/v1/reports/operational-summary` | Return SLA and project metrics |
| Admin | PATCH | `/api/v1/admin/sla-policies/{policyId}` | Update policy configuration |

## Example: Create Ticket

```json
{
  "projectId": "proj_123",
  "title": "Invoice export fails on mobile layout",
  "description": "Users receive a blank screen when opening exports on Safari.",
  "type": "bug",
  "severity": "high",
  "environment": "production",
  "attachmentIds": ["att_001"]
}
```

## Example: Create Milestone

```json
{
  "name": "Release 2.4 stabilization",
  "plannedDate": "2026-05-12",
  "ownerId": "usr_pm_01",
  "dependencyIds": ["milestone_ux_signoff"],
  "completionCriteria": [
    "All linked P1/P2 tickets closed",
    "Regression suite passed",
    "Client sign-off recorded"
  ]
}
```

## Authorization Notes
- Client tokens can create and read scoped tickets but cannot alter internal assignments or project plans.
- Internal tokens require project or operational scope to edit project, release, or administrative resources.
- Audit metadata is attached to every mutating request.

## Cross-Cutting Workflow and Operational Governance

### Api Design: Document-Specific Scope
- Primary focus for this artifact: **endpoint contracts, authorization scopes, and idempotency/error model**.
- Implementation handoff expectation: this document must be sufficient for an engineer/architect/operator to implement without hidden assumptions.
- Traceability anchor: `DETAILED_DESIGN_API_DESIGN` should be referenced in backlog items, design reviews, and release checklists when this artifact changes.

### Workflow and State Machine Semantics (DETAILED_DESIGN_API_DESIGN)
- For this document, workflow guidance must **specify transition APIs, optimistic concurrency, and deterministic error contracts**.
- Transition definitions must include trigger, actor, guard, failure code, side effects, and audit payload contract.
- Any asynchronous transition path must define idempotency key strategy and replay safety behavior.

### SLA and Escalation Rules (DETAILED_DESIGN_API_DESIGN)
- For this document, SLA guidance must **formalize calendar/timezone logic and immutable timer checkpoints**.
- Escalation must explicitly identify owner, dwell-time threshold, notification channel, and acknowledgement requirement.
- Breach and near-breach states must be queryable in reporting without recomputing from free-form notes.

### Permission Boundaries (DETAILED_DESIGN_API_DESIGN)
- For this document, permission guidance must **specify endpoint scopes, row-level filters, and redaction rules**.
- Privileged actions require reason codes, actor identity, and immutable audit entries.
- Client-visible payloads must be explicitly redacted from internal-only and regulated fields.

### Reporting and Metrics (DETAILED_DESIGN_API_DESIGN)
- For this document, reporting guidance must **define schema-level correctness rules and backfill/replay semantics**.
- Metric definitions must include numerator/denominator, time window, dimensional keys, and null/missing-data behavior.
- Each metric should map to raw events/tables so results are reproducible during audits.

### Operational Edge-Case Handling (DETAILED_DESIGN_API_DESIGN)
- For this document, operational guidance must **define retryability, DLQ handling, and compensation command contracts**.
- Partial failure handling must identify what is rolled back, compensated, or deferred.
- Recovery completion criteria must be measurable (not subjective) and tied to dashboard/alert signals.

### Implementation Readiness Checklist (DETAILED_DESIGN_API_DESIGN)
| Checklist Item | This Document Must Provide | Validation Evidence |
|---|---|---|
| Workflow Contract Completeness | All relevant states, transitions, and invalid paths for `detailed-design/api-design.md` | Scenario walkthrough + transition test mapping |
| SLA/ Escalation Determinism | Timer, pause, escalation, and override semantics | Policy table review + simulated timer run |
| Authorization Correctness | Role scope, tenant scope, and field visibility boundaries | Auth matrix review + API/UI parity checks |
| Reporting Reproducibility | KPI formulas, dimensions, and source lineage | Recompute KPI from event data sample |
| Operations Recoverability | Degraded-mode and compensation runbook steps | Tabletop/game-day evidence and postmortem template |

