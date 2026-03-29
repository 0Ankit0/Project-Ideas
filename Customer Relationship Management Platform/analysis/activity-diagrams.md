# Activity Diagrams

This document captures high-value CRM workflow activities with alternate/error handling.

## Lead Capture, Qualification, and Conversion
```mermaid
flowchart TD
    A[Inbound Lead Captured] --> B[Normalize & Validate Payload]
    B --> C{Duplicate Candidate?}
    C -- Yes --> D[Create Merge Review Case]
    D --> E{Reviewer Approves Merge?}
    E -- No --> F[Keep Distinct Lead]
    E -- Yes --> G[Merge Records]
    C -- No --> H[Create Net-New Lead]
    F --> I[Run Lead Scoring]
    G --> I
    H --> I
    I --> J{Score Above MQL Threshold?}
    J -- No --> K[Nurture Queue]
    J -- Yes --> L[Assign Owner + SLA Timer]
    L --> M{Owner Accepts?}
    M -- No --> N[Reassign by Territory Rules]
    M -- Yes --> O[Create Qualification Activity]
    N --> O
    O --> P{Qualified?}
    P -- No --> Q[Disqualify + Reason]
    P -- Yes --> R[Convert to Contact/Account/Opportunity]
```

## Opportunity Stage Progression
```mermaid
flowchart TD
    A[Opportunity Open] --> B[Validate Required Fields for Next Stage]
    B --> C{Validation Passed?}
    C -- No --> D[Return Actionable Errors]
    C -- Yes --> E[Apply Stage Transition]
    E --> F[Recalculate Forecast Category]
    F --> G{Risk Signals Triggered?}
    G -- Yes --> H[Create Manager Review Task]
    G -- No --> I[Publish Stage Changed Event]
    H --> I
    I --> J{Closed Won/Lost?}
    J -- No --> K[Continue Pipeline Execution]
    J -- Yes --> L[Lock Commercial Fields + Trigger Post-Close Workflow]
```

## Territory Reassignment and Forecast Reconciliation
```mermaid
flowchart TD
    A[Territory Reassignment Request] --> B[Validate Effective Date + Policy]
    B --> C{Policy Compliant?}
    C -- No --> D[Reject Request + Audit]
    C -- Yes --> E[Create Reassignment Job]
    E --> F[Reassign Accounts + Open Opportunities]
    F --> G[Recompute Forecast Ownership]
    G --> H{Reconciliation Drift Detected?}
    H -- Yes --> I[Open Reconciliation Exception]
    H -- No --> J[Publish Reassignment Completed]
    I --> K[Finance/Ops Review + Resolution]
    K --> J
```

## Domain Glossary
- **Activity Path**: File-specific term used to anchor decisions in **Activity Diagrams**.
- **Lead**: Prospect record entering qualification and ownership workflows.
- **Opportunity**: Revenue record tracked through pipeline stages and forecast rollups.
- **Correlation ID**: Trace identifier propagated across APIs, queues, and audits for this workflow.

## Entity Lifecycles
- Lifecycle for this document: `Trigger -> Validate Context -> Execute Task -> Emit Outcome -> Close`.
- Each transition must capture actor, timestamp, source state, target state, and justification note.

```mermaid
flowchart LR
    A[Trigger] --> B[Validate Context]
    B[Validate Context] --> C[Execute Task]
    C[Execute Task] --> D[Emit Outcome]
    D[Emit Outcome] --> E[Close]
    E[Close]
```

## Integration Boundaries
- Swimlane actors include sales rep, workflow engine, and policy service.
- Data ownership and write authority must be explicit at each handoff boundary.
- Interface changes require schema/version review and downstream impact acknowledgement.

## Error and Retry Behavior
- Task retries allowed only for technical errors; policy denials halt flow.
- Retries must preserve idempotency token and correlation ID context.
- Exhausted retries route to an operational queue with triage metadata.

## Measurable Acceptance Criteria
- Every activity diagram includes alternate path, timeout path, and compensating action.
- Observability must publish latency, success rate, and failure-class metrics for this document's scope.
- Quarterly review confirms definitions and diagrams still match production behavior.
