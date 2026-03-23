# State Machine Diagram - Learning Management System

## Course Version Lifecycle

```mermaid
stateDiagram-v2
    [*] --> draft
    draft --> in_review
    in_review --> published
    published --> archived
    in_review --> draft
    published --> draft_update
    draft_update --> in_review
```

## Enrollment Lifecycle

```mermaid
stateDiagram-v2
    [*] --> invited
    invited --> active
    active --> completed
    active --> dropped
    active --> expired
    expired --> reactivated
    reactivated --> active
    completed --> certified
```
