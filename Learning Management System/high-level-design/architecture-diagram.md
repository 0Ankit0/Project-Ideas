# Architecture Diagram - Learning Management System

```mermaid
flowchart TB
    subgraph access[Access Channels]
        learnerPortal[Learner Portal]
        staffWorkspace[Staff Workspace]
    end

    subgraph platform[Core Platform]
        gateway[API Gateway]
        identity[Identity and Access]
        course[Course and Authoring Service]
        enrollment[Enrollment and Cohort Service]
        assessment[Assessment Service]
        grading[Grading and Review Service]
        progress[Progress Tracking Service]
        certificate[Certification Service]
        notification[Notification Service]
        reporting[Reporting and Search Projection]
    end

    subgraph data[Data Layer]
        pg[(PostgreSQL)]
        search[(Search Index)]
        bus[(Message Bus)]
        object[(Object Storage)]
    end

    learnerPortal --> gateway
    staffWorkspace --> gateway
    gateway --> identity
    gateway --> course
    gateway --> enrollment
    gateway --> assessment
    gateway --> grading
    gateway --> progress
    gateway --> certificate
    course --> pg
    enrollment --> pg
    assessment --> pg
    grading --> pg
    progress --> pg
    certificate --> pg
    course --> object
    course --> search
    enrollment --> bus
    assessment --> bus
    grading --> bus
    progress --> bus
    certificate --> bus
    bus --> notification
    bus --> reporting
    reporting --> search
```

## Responsibilities

| Component | Responsibility |
|-----------|----------------|
| Course and Authoring Service | Course definitions, versions, modules, lessons, publishing |
| Enrollment and Cohort Service | Learner enrollment, seat rules, cohorts, schedules |
| Assessment Service | Attempts, timers, submissions, auto-grading triggers |
| Grading and Review Service | Manual review, rubric scoring, feedback, overrides |
| Progress Tracking Service | Lesson completion, resume state, engagement signals |
| Certification Service | Completion evaluation and certificate issuance |
| Reporting and Search Projection | Catalog discovery, dashboards, analytics summaries |

## Implementation Details: Service Boundaries

### Boundary decisions
- Grading service owns score calculation and moderation outcomes; no other service mutates final grade records.
- Progress service owns derived completion percentages and status projections.
- Certificate service only consumes completion decisions and integrity verdicts.

### Failure containment
- Integration adapters isolate provider outages from core learning workflows.
- Read models are eventually consistent; transactional correctness remains in system-of-record services.
