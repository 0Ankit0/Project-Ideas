# Code Guidelines - Learning Management System

## Reference Implementation Stack
- Frontend: React + TypeScript for learner and staff applications
- Backend: TypeScript service layer (for example NestJS) with modular domain packages
- Persistence: PostgreSQL for transactional data, search index for discovery and analytics projections, object storage for media and files
- Async processing: queue + workers for notifications, grading queues, progress aggregation, and certificate issuance

## Suggested Repository Structure

```text
learning-platform/
├── apps/
│   ├── learner-portal/
│   ├── staff-workspace/
│   ├── api/
│   └── worker/
├── packages/
│   ├── domain/
│   │   ├── identity/
│   │   ├── courses/
│   │   ├── enrollments/
│   │   ├── assessments/
│   │   ├── grading/
│   │   ├── progress/
│   │   └── certificates/
│   ├── ui/
│   └── shared/
├── infra/
└── tests/
```

## Domain Boundaries
- Keep course authoring, enrollment, assessments, grading, progress, and certification in separate domain modules.
- Use domain events for notifications, reporting, at-risk learner detection, and certificate issuance rather than tightly coupling write paths.
- Never expose tenant-internal or reviewer-only data through learner-facing DTOs.

## Backend Guidelines
- Treat tenant scoping as a first-class concern on every query and command.
- Keep completion, grading, and prerequisite evaluation inside explicit policy services.
- Preserve historical course-version references in learner records to avoid retroactive data corruption.
- Record audit events for grading changes, course publication, role changes, and administrative overrides.

## Frontend Guidelines
- Optimize the learner portal for low-friction catalog, lesson, assessment, and progress workflows.
- Optimize the staff workspace for authoring, cohort operations, grading, and reporting efficiency.
- Design long-running authoring, grading, and import flows with save state, validation, and recoverability.

## Example Domain Types

```ts
export type EnrollmentStatus =
  | 'invited'
  | 'active'
  | 'completed'
  | 'dropped'
  | 'expired'
  | 'reactivated';

export interface RecordProgressEventCommand {
  tenantId: string;
  learnerId: string;
  lessonId: string;
  eventType: 'lesson_started' | 'lesson_completed' | 'checkpoint';
  percentComplete: number;
  recordedAt: string;
}
```

## Testing Expectations
- Unit tests for policy evaluation, completion rules, attempt limits, and grading calculations.
- Integration tests for enrollment, lesson progression, assessment submission, grading, and certificate issuance.
- API contract tests for learner-facing and staff-facing endpoints.
- E2E tests for discover-to-enroll, learn-to-submit, grade-to-feedback, and complete-to-certificate flows.

## Implementation Details: Engineering Quality Gates

- Domain invariants belong in domain modules, not controllers.
- All write handlers produce structured audit and tracing context.
- Background jobs must be idempotent, resumable, and observable.
