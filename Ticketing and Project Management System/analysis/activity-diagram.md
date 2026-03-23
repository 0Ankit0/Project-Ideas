# Activity Diagram - Ticketing and Project Management System

## Ticket-to-Resolution Flow

```mermaid
flowchart TD
    start([Client reports issue]) --> create[Create ticket and upload image evidence]
    create --> validate{Valid intake and allowed attachment?}
    validate -- No --> clarify[Request clarification or reject upload]
    clarify --> create
    validate -- Yes --> triage[Triage, categorize, and set priority]
    triage --> duplicate{Duplicate or known issue?}
    duplicate -- Yes --> link[Link to existing ticket and notify client]
    duplicate -- No --> assign[Assign to developer or team queue]
    assign --> plan{Needs milestone or change request?}
    plan -- Yes --> milestone[Link to milestone / create backlog task]
    plan -- No --> work[Developer investigates and fixes]
    milestone --> work
    work --> blocked{Blocked?}
    blocked -- Yes --> escalate[Escalate blocker and update risk]
    escalate --> work
    blocked -- No --> qa[Send to QA verification]
    qa --> passed{Fix verified?}
    passed -- No --> reopen[Reopen ticket with failure notes]
    reopen --> work
    passed -- Yes --> close[Close ticket and update release/project metrics]
    close --> end([Client informed and records retained])
```
