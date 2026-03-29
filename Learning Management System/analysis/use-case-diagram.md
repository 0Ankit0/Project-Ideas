# Use Case Diagram - Learning Management System

```mermaid
flowchart LR
    learner[Learner]
    instructor[Instructor]
    reviewer[Teaching Assistant / Reviewer]
    author[Content Admin / Author]
    tenantAdmin[Tenant Admin]
    platformAdmin[Platform Admin]

    subgraph system[Learning Management System]
        uc1([Search course catalog])
        uc2([Enroll learner])
        uc3([Consume lesson content])
        uc4([Submit assessment])
        uc5([Review and grade])
        uc6([Author or publish course])
        uc7([Track learner progress])
        uc8([Issue certificate])
        uc9([Manage tenant policies])
        uc10([Manage platform integrations])
    end

    learner --> uc1
    learner --> uc3
    learner --> uc4
    instructor --> uc2
    instructor --> uc5
    instructor --> uc7
    reviewer --> uc5
    author --> uc6
    tenantAdmin --> uc2
    tenantAdmin --> uc9
    platformAdmin --> uc10
    uc3 --> uc7
    uc4 --> uc5
    uc5 --> uc8
```

## Implementation Details: Use-Case Realization

### Actor-to-service responsibility mapping
- **Learner** operations map to enrollment, lesson player, assessment, and progress endpoints with tenant guard checks.
- **Instructor/Reviewer** operations map to review queues, rubric workflows, moderation overrides, and feedback publication.
- **Tenant admin** operations map to policy configuration, cohort management, and reporting exports.

```mermaid
flowchart TD
    U[Use case invoked] --> A{Authorization valid?}
    A -- no --> X[Reject + audit]
    A -- yes --> P[Policy evaluation]
    P --> C{Constraint satisfied?}
    C -- no --> D[Return actionable denial reason]
    C -- yes --> W[Write domain state + emit event]
    W --> R[Project read models]
```
