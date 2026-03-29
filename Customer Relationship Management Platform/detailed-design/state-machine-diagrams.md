# State Machine Diagrams

## Lead Lifecycle
```mermaid
stateDiagram-v2
    [*] --> New
    New --> Working: owner assigned
    Working --> Qualified: qualification met
    Working --> Nurturing: not ready
    Working --> Disqualified: invalid / out of scope
    Nurturing --> Working: re-engaged
    Qualified --> Converted: convert to account/contact/opportunity
    Qualified --> Disqualified: later rejected
    Converted --> [*]
    Disqualified --> [*]
```

## Opportunity Lifecycle
```mermaid
stateDiagram-v2
    [*] --> Prospecting
    Prospecting --> Qualification
    Qualification --> Proposal
    Proposal --> Negotiation
    Negotiation --> ClosedWon
    Negotiation --> ClosedLost
    Prospecting --> ClosedLost
    Qualification --> ClosedLost
    Proposal --> ClosedLost
    ClosedWon --> [*]
    ClosedLost --> [*]
```

## Forecast Snapshot Lifecycle
```mermaid
stateDiagram-v2
    [*] --> Draft
    Draft --> Submitted: submit()
    Submitted --> Approved: manager approves
    Submitted --> Returned: manager requests changes
    Returned --> Submitted: resubmit
    Approved --> Locked: close period
    Locked --> [*]
```

## Domain Glossary
- **Transition Guard**: File-specific term used to anchor decisions in **State Machine Diagrams**.
- **Lead**: Prospect record entering qualification and ownership workflows.
- **Opportunity**: Revenue record tracked through pipeline stages and forecast rollups.
- **Correlation ID**: Trace identifier propagated across APIs, queues, and audits for this workflow.

## Entity Lifecycles
- Lifecycle for this document: `Enter State -> Evaluate Guard -> Execute Action -> Next State`.
- Each transition must capture actor, timestamp, source state, target state, and justification note.

```mermaid
flowchart LR
    A[Enter State] --> B[Evaluate Guard]
    B[Evaluate Guard] --> C[Execute Action]
    C[Execute Action] --> D[Next State]
    D[Next State]
```

## Integration Boundaries
- State machines bind to lead, opportunity, and forecast entities.
- Data ownership and write authority must be explicit at each handoff boundary.
- Interface changes require schema/version review and downstream impact acknowledgement.

## Error and Retry Behavior
- Invalid transition requests are rejected with machine-readable reason codes.
- Retries must preserve idempotency token and correlation ID context.
- Exhausted retries route to an operational queue with triage metadata.

## Measurable Acceptance Criteria
- Each state has entry/exit actions and at least one negative transition test.
- Observability must publish latency, success rate, and failure-class metrics for this document's scope.
- Quarterly review confirms definitions and diagrams still match production behavior.
