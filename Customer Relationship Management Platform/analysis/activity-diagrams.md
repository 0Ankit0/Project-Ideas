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
