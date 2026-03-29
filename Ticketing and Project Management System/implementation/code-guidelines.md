# Code Guidelines - Ticketing and Project Management System

## Reference Implementation Stack
- Frontend: React + TypeScript for both client portal and internal workspace
- Backend: NestJS or similar TypeScript service layer
- Persistence: PostgreSQL for transactional records, object storage for attachments
- Async processing: message bus + worker service for scans, notifications, SLA timers, and projections

## Suggested Repository Structure

```text
ticketing-platform/
├── apps/
│   ├── client-portal/
│   ├── internal-workspace/
│   ├── api/
│   └── worker/
├── packages/
│   ├── domain/
│   │   ├── tickets/
│   │   ├── projects/
│   │   ├── releases/
│   │   └── access/
│   ├── ui/
│   └── shared/
├── infra/
└── tests/
```

## Domain Boundaries
- Keep ticketing, project planning, release management, and access control as separate domain modules.
- Publish domain events instead of making reporting or notification logic part of write transactions.
- Do not let client-portal DTOs expose internal-only fields such as private comments or internal priority overrides.

## Backend Guidelines
- Validate every command with organization scope and role scope.
- Keep workflow transitions explicit through command handlers or state policies.
- Model attachments as metadata records that reference object storage rather than storing blobs in PostgreSQL.
- Record assignment history and audit history as append-only events.

## Frontend Guidelines
- Build the client portal and internal workspace from shared UI primitives but separate route guards and feature exposure.
- Keep timeline, comments, and status widgets real-time aware.
- Make milestone and dependency visualizations readable on large internal dashboards.

## Example Domain Types

```ts
export type TicketStatus =
  | 'new'
  | 'awaiting_clarification'
  | 'triaged'
  | 'assigned'
  | 'in_progress'
  | 'blocked'
  | 'ready_for_qa'
  | 'closed'
  | 'reopened';

export interface CreateTicketCommand {
  organizationId: string;
  projectId?: string;
  title: string;
  description: string;
  type: 'bug' | 'incident' | 'service_request' | 'change_request';
  severity: 'low' | 'medium' | 'high' | 'critical';
  attachmentIds: string[];
  reporterId: string;
}
```

## Testing Expectations
- Unit tests for workflow policy decisions and priority/SLA calculation.
- Integration tests for ticket creation, assignment, milestone linking, and verification.
- API contract tests for client-visible and internal-only endpoints.
- E2E tests for the major happy paths: client intake, triage, fix, QA close, milestone replanning.

## Cross-Cutting Workflow and Operational Governance

### Code Guidelines: Document-Specific Scope
- Primary focus for this artifact: **coding standards that enforce workflow/policy correctness**.
- Implementation handoff expectation: this document must be sufficient for an engineer/architect/operator to implement without hidden assumptions.
- Traceability anchor: `IMPLEMENTATION_CODE_GUIDELINES` should be referenced in backlog items, design reviews, and release checklists when this artifact changes.

### Workflow and State Machine Semantics (IMPLEMENTATION_CODE_GUIDELINES)
- For this document, workflow guidance must **enforce state semantics in code paths, tests, and release gates**.
- Transition definitions must include trigger, actor, guard, failure code, side effects, and audit payload contract.
- Any asynchronous transition path must define idempotency key strategy and replay safety behavior.

### SLA and Escalation Rules (IMPLEMENTATION_CODE_GUIDELINES)
- For this document, SLA guidance must **implement recomputable SLA engine behavior and regression coverage**.
- Escalation must explicitly identify owner, dwell-time threshold, notification channel, and acknowledgement requirement.
- Breach and near-breach states must be queryable in reporting without recomputing from free-form notes.

### Permission Boundaries (IMPLEMENTATION_CODE_GUIDELINES)
- For this document, permission guidance must **verify API/UI authorization parity using contract tests**.
- Privileged actions require reason codes, actor identity, and immutable audit entries.
- Client-visible payloads must be explicitly redacted from internal-only and regulated fields.

### Reporting and Metrics (IMPLEMENTATION_CODE_GUIDELINES)
- For this document, reporting guidance must **ship dashboards-as-code and data quality tests in CI**.
- Metric definitions must include numerator/denominator, time window, dimensional keys, and null/missing-data behavior.
- Each metric should map to raw events/tables so results are reproducible during audits.

### Operational Edge-Case Handling (IMPLEMENTATION_CODE_GUIDELINES)
- For this document, operational guidance must **wire executable runbooks to deployment and incident response gates**.
- Partial failure handling must identify what is rolled back, compensated, or deferred.
- Recovery completion criteria must be measurable (not subjective) and tied to dashboard/alert signals.

### Implementation Readiness Checklist (IMPLEMENTATION_CODE_GUIDELINES)
| Checklist Item | This Document Must Provide | Validation Evidence |
|---|---|---|
| Workflow Contract Completeness | All relevant states, transitions, and invalid paths for `implementation/code-guidelines.md` | Scenario walkthrough + transition test mapping |
| SLA/ Escalation Determinism | Timer, pause, escalation, and override semantics | Policy table review + simulated timer run |
| Authorization Correctness | Role scope, tenant scope, and field visibility boundaries | Auth matrix review + API/UI parity checks |
| Reporting Reproducibility | KPI formulas, dimensions, and source lineage | Recompute KPI from event data sample |
| Operations Recoverability | Degraded-mode and compensation runbook steps | Tabletop/game-day evidence and postmortem template |

