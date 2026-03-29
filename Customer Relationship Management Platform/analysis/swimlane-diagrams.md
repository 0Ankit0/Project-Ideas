# Swimlane Diagrams

## Lead-to-Opportunity Swimlane
```mermaid
flowchart LR
    subgraph SalesRep[Sales Rep]
      A[Review assigned lead]
      B[Contact and qualify]
      C[Convert lead]
    end

    subgraph CRM[CRM System]
      D[Score lead]
      E[Check duplicate candidates]
      F[Create account/contact/opportunity]
      G[Emit conversion event]
    end

    subgraph RevOps[Revenue Operations]
      H[Resolve dedupe/merge case]
    end

    A --> D
    D --> E
    E -->|Duplicate| H
    H --> B
    E -->|No duplicate| B
    B --> C
    C --> F
    F --> G
```

## Forecast Submission Swimlane
```mermaid
flowchart LR
    subgraph Rep[Sales Rep]
      A[Update pipeline]
      B[Submit forecast]
    end

    subgraph CRM[CRM System]
      C[Roll up amounts]
      D[Validate required fields]
      E[Create snapshot]
      F[Notify manager]
    end

    subgraph Manager[Sales Manager]
      G[Review forecast]
      H[Approve / return]
    end

    A --> C --> D --> E
    B --> E
    E --> F --> G --> H
```

## Domain Glossary
- **Lane Responsibility**: File-specific term used to anchor decisions in **Swimlane Diagrams**.
- **Lead**: Prospect record entering qualification and ownership workflows.
- **Opportunity**: Revenue record tracked through pipeline stages and forecast rollups.
- **Correlation ID**: Trace identifier propagated across APIs, queues, and audits for this workflow.

## Entity Lifecycles
- Lifecycle for this document: `Actor Assigned -> Action Performed -> Handoff -> Completion`.
- Each transition must capture actor, timestamp, source state, target state, and justification note.

```mermaid
flowchart LR
    A[Actor Assigned] --> B[Action Performed]
    B[Action Performed] --> C[Handoff]
    C[Handoff] --> D[Completion]
    D[Completion]
```

## Integration Boundaries
- Lanes include human roles and systems with explicit ownership handoffs.
- Data ownership and write authority must be explicit at each handoff boundary.
- Interface changes require schema/version review and downstream impact acknowledgement.

## Error and Retry Behavior
- Failed handoff retries once automatically, then escalates to queue supervisor.
- Retries must preserve idempotency token and correlation ID context.
- Exhausted retries route to an operational queue with triage metadata.

## Measurable Acceptance Criteria
- Every lane handoff specifies input artifact and acceptance condition.
- Observability must publish latency, success rate, and failure-class metrics for this document's scope.
- Quarterly review confirms definitions and diagrams still match production behavior.
