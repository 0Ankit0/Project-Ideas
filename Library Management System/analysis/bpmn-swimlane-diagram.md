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

## Borrowing & Reservation Lifecycle, Consistency, Penalties, and Exception Patterns

### Artifact focus: Swimlane execution responsibilities

This section is intentionally tailored for this specific document so implementation teams can convert architecture and analysis into build-ready tasks.

### Implementation directives for this artifact
- Ensure each lane has only one accountable role/service for state mutation to avoid split-brain ownership.
- Mark message boundary events between staff actions and automated jobs (hold allocator, fine scheduler).
- Attach SLA timers to long-running human tasks like damage adjudication and waiver approval.

### Lifecycle controls that must be reflected here
- Borrowing must always enforce policy pre-checks, deterministic copy selection, and atomic loan/copy updates.
- Reservation behavior must define queue ordering, allocation eligibility re-checks, and pickup expiry/no-show outcomes.
- Fine and penalty flows must define accrual formula, cap behavior, and lost/damage adjudication paths.
- Exception handling must define idempotency, conflict semantics, outbox reliability, and operator recovery procedures.

### Traceability requirements
- Every major rule in this document should map to at least one API contract, domain event, or database constraint.
- Include policy decision codes and audit expectations wherever staff override or monetary adjustment is possible.

### Mermaid implementation reference
```mermaid
flowchart LR
    subgraph Patron
      P1[Place hold]
      P2[Pickup item]
    end
    subgraph Circulation_Service
      C1[Validate policy]
      C2[Queue hold]
      C3[Allocate copy]
    end
    subgraph Staff
      S1[Prepare hold shelf]
      S2[Override decision]
    end
    subgraph Jobs
      J1[Expiry scheduler]
      J2[Fine accrual]
    end
    P1 --> C1 --> C2 --> C3 --> S1 --> P2
    C3 --> J1
    P2 --> J2
    S2 --> C1
```

### Definition of done for this artifact
- Content is specific to this artifact type and not a generic duplicate.
- Rules are testable (unit/integration/contract) and reference concrete data/events/errors.
- Diagram semantics (if present) are consistent with textual constraints and lifecycle behavior.
