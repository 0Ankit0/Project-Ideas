# BPMN Swimlane Diagram - Learning Management System

```mermaid
flowchart LR
    subgraph lane1[Learner]
        l1[Discover course]
        l2[Enroll or request access]
        l3[Consume lessons]
        l4[Submit assessment]
        l5[Review result or certificate]
    end

    subgraph lane2[Instructor / Reviewer]
        i1[Approve or manage enrollment]
        i2[Facilitate learning]
        i3[Review submissions]
        i4[Publish grades and feedback]
    end

    subgraph lane3[Content Admin / Author]
        c1[Create and publish course]
    end

    subgraph lane4[Tenant Admin]
        t1[Configure tenant rules and cohorts]
        t2[Review reports]
    end

    subgraph lane5[Platform Admin]
        p1[Manage integrations and platform policy]
    end

    c1 --> l1 --> l2 --> i1 --> l3 --> i2 --> l4 --> i3 --> i4 --> l5
    t1 --> i1
    t1 --> t2
    p1 --> t1
```

## Swimlane Interpretation

- Learner-facing actions stay streamlined while staff workflows manage publication, grading, and operational policy.
- Tenant configuration governs enrollment, deadlines, and reporting visibility.
- Platform administration controls cross-tenant integrations and system-level compliance features.

## Implementation Details: Swimlane SLAs

| Swimlane | Blocking action | SLA target | Escalation owner |
|---|---|---|---|
| Instructor/Reviewer | Grade publication | < 24h standard, < 4h priority | Academic ops lead |
| Content Admin | Publish approval fix | < 2 business days | Content governance |
| Tenant Admin | Cohort policy correction | < 8h | Tenant success |

### Handoff quality requirements
- Every inter-lane handoff emits a traceable event.
- Blocking handoffs surface pending status to learner dashboard.
