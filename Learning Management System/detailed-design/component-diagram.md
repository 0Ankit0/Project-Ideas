# Component Diagram - Learning Management System

```mermaid
flowchart LR
    ui[Learner Portal / Staff Workspace] --> api[API Layer]
    api --> auth[Access Control Component]
    api --> catalog[Catalog and Authoring Component]
    api --> enrollment[Enrollment and Cohort Component]
    api --> delivery[Content Delivery and Progress Component]
    api --> assessment[Assessment Component]
    api --> grading[Grading and Feedback Component]
    api --> certification[Certification Component]
    api --> reporting[Reporting Component]
    assessment --> policy[Policy and Rule Evaluation Component]
    grading --> policy
    certification --> policy
```

## Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| Access Control | Authentication, tenant scoping, RBAC |
| Catalog and Authoring | Courses, versions, lessons, metadata, publication |
| Enrollment and Cohort | Learner assignment, schedules, access windows |
| Content Delivery and Progress | Lesson rendering state, checkpoints, completion tracking |
| Assessment | Attempts, submissions, timers, question delivery |
| Grading and Feedback | Rubrics, reviewer workflows, overrides |
| Certification | Completion evaluation and credential issuance |
| Reporting | Dashboards, exports, engagement summaries |

## Implementation Details: Component Interaction Rules

- Commands and queries remain separated to simplify replay and projection rebuild.
- Cross-component calls must use versioned contracts and fallback behavior.
- Side-effecting components must emit audit and metric events.
