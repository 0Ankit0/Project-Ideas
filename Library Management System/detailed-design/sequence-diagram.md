# Sequence Diagram - Library Management System

```mermaid
sequenceDiagram
    participant Patron as Patron Portal
    participant API as API Layer
    participant Holds as Hold Service
    participant Policy as Policy Engine
    participant Catalog as Catalog Service
    participant Notify as Notification Service

    Patron->>API: POST /holds
    API->>Catalog: verify title and branch eligibility
    API->>Policy: validate patron account and queue rules
    API->>Holds: create hold request
    Holds->>Notify: send confirmation
    Notify-->>Patron: hold created
```

## Return to Hold Shelf Sequence

```mermaid
sequenceDiagram
    participant Desk as Return Desk
    participant API as API Layer
    participant Circ as Circulation Service
    participant Fine as Fine Service
    participant Holds as Hold Service
    participant Transfer as Transfer Service

    Desk->>API: POST /returns
    API->>Circ: close loan
    Circ->>Fine: evaluate overdue charge
    Circ->>Holds: fetch next eligible hold
    alt same branch
        Holds->>Circ: mark item on hold shelf
    else transfer needed
        Holds->>Transfer: create branch transfer
    end
```

## Borrowing & Reservation Lifecycle, Consistency, Penalties, and Exception Patterns

### Artifact focus: Sequence guarantees and timing expectations

This section is intentionally tailored for this specific document so implementation teams can convert architecture and analysis into build-ready tasks.

### Implementation directives for this artifact
- Use sequence messages to show transaction boundaries and when locks are acquired/released.
- Explicitly model duplicate command replay handling with idempotency key lookup.
- Include asynchronous publication branch and eventual consistency delay notes.

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
sequenceDiagram
    actor Staff
    participant API as Circulation API
    participant DB as Database
    participant OUT as Outbox
    Staff->>API: CommitCheckout(command,idempotencyKey)
    API->>DB: begin tx + lock copy
    DB-->>API: lock ok
    API->>DB: insert loan/update copy
    API->>DB: insert outbox event
    API->>DB: commit
    API-->>Staff: 201 LoanCreated
    OUT-->>API: async publish LoanCreated
```

### Definition of done for this artifact
- Content is specific to this artifact type and not a generic duplicate.
- Rules are testable (unit/integration/contract) and reference concrete data/events/errors.
- Diagram semantics (if present) are consistent with textual constraints and lifecycle behavior.
