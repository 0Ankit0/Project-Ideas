# BPMN Swimlane Diagram - Ticketing and Project Management System

```mermaid
flowchart LR
    subgraph lane1[Client Requester]
        c1[Submit ticket]
        c2[Answer clarification]
        c3[Review closure update]
    end

    subgraph lane2[Support / Triage]
        s1[Validate intake]
        s2[Set priority and SLA]
        s3[Assign owner]
    end

    subgraph lane3[Project Manager]
        p1[Link to project or milestone]
        p2[Approve replanning or change request]
    end

    subgraph lane4[Developer]
        d1[Investigate issue]
        d2[Implement fix]
        d3[Mark ready for QA]
    end

    subgraph lane5[QA Reviewer]
        q1[Verify fix]
        q2[Close or reopen]
    end

    c1 --> s1 --> s2 --> s3 --> p1 --> d1 --> d2 --> d3 --> q1 --> q2 --> c3
    s1 --> c2 --> s1
    p1 --> p2 --> d1
    q2 -->|reopen| d1
```

## Swimlane Interpretation

- The client lane is intentionally narrow: submit evidence, answer questions, and review updates.
- Internal delivery governance lives across triage, project management, engineering, and QA lanes.
- Replanning is explicit so milestone risk is visible before resolution dates are missed.
