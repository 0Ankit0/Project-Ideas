# Domain Model - Learning Management System

## Core Domain Areas

| Domain Area | Key Concepts |
|-------------|--------------|
| Identity and Tenancy | Tenant, User, RoleAssignment, Audience |
| Catalog and Authoring | Course, CourseVersion, Module, Lesson, Resource |
| Delivery and Access | Cohort, Enrollment, LiveSession, AccessWindow |
| Assessment and Grading | Assessment, Attempt, SubmissionArtifact, GradeRecord, Rubric |
| Progress and Certification | ProgressRecord, CompletionRule, Certificate |
| Operations | Notification, AuditLog, AnalyticsSnapshot |

## Relationship Summary
- A **tenant** owns users, courses, cohorts, reporting scope, and administrative policies.
- A **course** can have many versions, modules, lessons, assessments, cohorts, and certificates.
- A **learner** can hold many enrollments, progress records, attempts, grades, and certificates.
- **Completion rules** depend on course structure, assessment outcomes, and optional attendance requirements.

```mermaid
erDiagram
    TENANT ||--o{ USER : contains
    TENANT ||--o{ COURSE : owns
    COURSE ||--o{ COURSE_VERSION : versions
    COURSE_VERSION ||--o{ MODULE : contains
    MODULE ||--o{ LESSON : contains
    MODULE ||--o{ ASSESSMENT : contains
    COURSE ||--o{ COHORT : offers
    USER ||--o{ ENROLLMENT : joins
    COHORT ||--o{ ENROLLMENT : includes
    USER ||--o{ ASSESSMENT_ATTEMPT : submits
    ASSESSMENT ||--o{ ASSESSMENT_ATTEMPT : receives
    USER ||--o{ PROGRESS_RECORD : generates
    USER ||--o{ CERTIFICATE : earns
```

## Implementation Details: Aggregate Consistency Rules

- `Enrollment` and `Attempt` aggregates must not be updated from projection services.
- `GradeRecord` is append-only by revision; overrides create new revision entries.
- `CertificateRecord` transitions require completed + integrity-cleared invariant checks.

```mermaid
flowchart LR
    Attempt --> GradeRecord
    GradeRecord --> CompletionDecision
    CompletionDecision --> CertificateRecord
```
