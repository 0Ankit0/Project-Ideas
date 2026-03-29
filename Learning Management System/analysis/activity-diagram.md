# Activity Diagram - Learning Management System

## Enroll-to-Certification Flow

```mermaid
flowchart TD
    start([Learner needs training]) --> browse[Browse or search course catalog]
    browse --> eligible{Eligible and seats available?}
    eligible -- No --> wait[Waitlist or request access]
    eligible -- Yes --> enroll[Enroll learner]
    wait --> enroll
    enroll --> learn[Consume lessons and resources]
    learn --> checkpoint{Lesson or module completion?}
    checkpoint -- Yes --> progress[Update progress and unlock next content]
    checkpoint -- No --> learn
    progress --> assessment{Assessment due?}
    assessment -- Yes --> submit[Submit quiz or assignment]
    submit --> grade[Auto-grade or manual review]
    grade --> passed{Completion criteria met?}
    passed -- No --> remediate[Retry, remediate, or continue learning]
    remediate --> learn
    passed -- Yes --> certify[Issue certificate and update dashboards]
    certify --> end([Learning record completed])
```

## Implementation Details: Flow Guards and Retries

### Decision-point implementation notes
- `Eligible and seats available?` maps to a policy endpoint that returns machine-readable denial reasons.
- `Completion criteria met?` must use the same evaluator for learner UI and certificate issuance.
- Retry loops require attempt caps and cooldown configuration.

```mermaid
flowchart LR
    E[Event received] --> O{Out-of-order?}
    O -- yes --> Q[Queue for reorder/replay]
    O -- no --> I[Apply invariant checks]
    I --> S{State valid?}
    S -- no --> F[Flag for remediation]
    S -- yes --> P[Project progress]
```
