# BPMN Swimlane Diagram - Library Management System

```mermaid
flowchart LR
    subgraph lane1[Patron]
        p1[Search or request title]
        p2[Place hold or borrow]
        p3[Collect item]
        p4[Return or renew]
    end

    subgraph lane2[Circulation Staff]
        c1[Validate patron and item]
        c2[Issue item]
        c3[Process return]
        c4[Manage fines or exceptions]
    end

    subgraph lane3[Cataloging / Acquisitions]
        a1[Create title and item records]
        a2[Receive and accession stock]
    end

    subgraph lane4[Branch Manager]
        m1[Approve transfer or audit actions]
        m2[Review branch dashboards]
    end

    subgraph lane5[Admin]
        ad1[Define policies and calendars]
    end

    a2 --> a1 --> p1 --> p2 --> c1 --> c2 --> p3 --> p4 --> c3 --> c4 --> m2
    c3 -->|hold queue| m1 --> p3
    ad1 --> c1
    ad1 --> c4
```

## Swimlane Interpretation

- Patron-facing actions stay lightweight while staff workflows handle policy, exceptions, and operations.
- Cataloging and acquisitions supply circulation with accurate, branch-aware inventory.
- Administrative policy changes affect every circulation validation path.
