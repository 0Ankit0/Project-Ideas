# System Sequence Diagram - Library Management System

## Checkout Flow

```mermaid
sequenceDiagram
    participant Staff as Circulation Staff
    participant UI as Staff Workspace
    participant API as Application API
    participant Patron as Patron Service
    participant Circ as Circulation Service
    participant Policy as Policy Engine
    participant Notify as Notification Service

    Staff->>UI: Scan patron card and item barcode
    UI->>API: POST /loans
    API->>Patron: validate patron status and blocks
    API->>Policy: evaluate lending policy
    API->>Circ: create loan and update item status
    Circ->>Notify: send due-date notification
    Notify-->>Staff: confirmation available
```

## Hold Fulfillment Flow

```mermaid
sequenceDiagram
    participant ReturnDesk as Return Desk
    participant API as Application API
    participant Circ as Circulation Service
    participant Hold as Hold Service
    participant Transfer as Transfer Service
    participant Notify as Notification Service

    ReturnDesk->>API: POST /returns
    API->>Circ: close loan and update item status
    Circ->>Hold: evaluate waiting queue
    alt same-branch pickup
        Hold->>Notify: tell patron item is ready
    else other-branch pickup
        Hold->>Transfer: create transfer request
        Transfer->>Notify: update branches and patron
    end
```

## Borrowing & Reservation Lifecycle, Consistency, Penalties, and Exception Patterns

### Artifact focus: Cross-system sequence contracts

This section is intentionally tailored for this specific document so implementation teams can convert architecture and analysis into build-ready tasks.

### Implementation directives for this artifact
- Document end-to-end interaction for checkout-return-hold allocation including external services.
- Include timeout, retry, and fallback decisions at each dependency call.
- Mark ownership of correlation IDs for distributed tracing.

### Lifecycle controls that must be reflected here
- Borrowing must always enforce policy pre-checks, deterministic copy selection, and atomic loan/copy updates.
- Reservation behavior must define queue ordering, allocation eligibility re-checks, and pickup expiry/no-show outcomes.
- Fine and penalty flows must define accrual formula, cap behavior, and lost/damage adjudication paths.
- Exception handling must define idempotency, conflict semantics, outbox reliability, and operator recovery procedures.

### Traceability requirements
- Every major rule in this document should map to at least one API contract, domain event, or database constraint.
- Include policy decision codes and audit expectations wherever staff override or monetary adjustment is possible.

### Definition of done for this artifact
- Content is specific to this artifact type and not a generic duplicate.
- Rules are testable (unit/integration/contract) and reference concrete data/events/errors.
- Diagram semantics (if present) are consistent with textual constraints and lifecycle behavior.
