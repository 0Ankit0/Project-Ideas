# State Machine Diagram - Library Management System

## Item Copy Lifecycle

```mermaid
stateDiagram-v2
    [*] --> cataloging
    cataloging --> available
    available --> on_loan
    available --> on_hold_shelf
    available --> in_transfer
    available --> in_repair
    on_loan --> overdue
    on_loan --> available
    overdue --> available
    on_hold_shelf --> on_loan
    in_transfer --> available
    in_repair --> available
    available --> lost
    overdue --> lost
    available --> withdrawn
```

## Patron Membership Lifecycle

```mermaid
stateDiagram-v2
    [*] --> pending_activation
    pending_activation --> active
    active --> suspended
    active --> expired
    suspended --> active
    expired --> renewed
    renewed --> active
    active --> closed
```

## Borrowing & Reservation Lifecycle, Consistency, Penalties, and Exception Patterns

### Artifact focus: State machine executable semantics

This section is intentionally tailored for this specific document so implementation teams can convert architecture and analysis into build-ready tasks.

### Implementation directives for this artifact
- For every state transition, define trigger command/event, guard condition, and side effects.
- Mark forbidden transitions and required compensation paths for invalid state changes.
- Bind state transitions to audit event generation for compliance traceability.

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
stateDiagram-v2
    [*] --> Available
    Available --> OnLoan: CommitCheckout
    OnLoan --> OnLoan: RenewLoan [renewable]
    OnLoan --> AwaitingInspection: ReturnCopy
    AwaitingInspection --> OnHoldShelf: HoldQueueNotEmpty
    AwaitingInspection --> Available: NoHoldQueue
    OnHoldShelf --> OnLoan: PickupCheckout
    OnHoldShelf --> Available: PickupExpired
    OnLoan --> Lost: LostThresholdReached
```

### Definition of done for this artifact
- Content is specific to this artifact type and not a generic duplicate.
- Rules are testable (unit/integration/contract) and reference concrete data/events/errors.
- Diagram semantics (if present) are consistent with textual constraints and lifecycle behavior.
