# ERD and Database Schema - Learning Management System

```mermaid
erDiagram
    TENANT ||--o{ USER : contains
    TENANT ||--o{ COURSE : owns
    COURSE ||--o{ COURSE_VERSION : versions
    COURSE_VERSION ||--o{ MODULE : contains
    MODULE ||--o{ LESSON : contains
    MODULE ||--o{ ASSESSMENT : contains
    COURSE ||--o{ COHORT : offers
    USER ||--o{ ENROLLMENT : has
    COHORT ||--o{ ENROLLMENT : includes
    USER ||--o{ PROGRESS_RECORD : generates
    USER ||--o{ ASSESSMENT_ATTEMPT : submits
    ASSESSMENT ||--o{ ASSESSMENT_ATTEMPT : receives
    USER ||--o{ CERTIFICATE : earns
    USER ||--o{ AUDIT_LOG : triggers
```

## Table Notes

| Table | Notes |
|-------|-------|
| tenants | Tenant lifecycle, branding, and configuration scope |
| users | Learners and staff within tenant isolation boundaries |
| courses | Top-level course entities |
| course_versions | Stable published or draft snapshots |
| modules | Ordered course sections |
| lessons | Content units and resources |
| cohorts | Schedule and audience grouping |
| enrollments | Learner participation records |
| assessments | Assessment definitions and settings |
| assessment_attempts | Learner attempt history |
| progress_records | Lesson- or content-level completion data |
| certificates | Completion credentials |
| audit_logs | Immutable system and workflow history |
