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
