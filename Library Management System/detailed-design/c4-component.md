# C4 Component Diagram - Library Management System

```mermaid
flowchart TB
    subgraph backend[Backend Application]
        auth[Auth and Scope Guard]
        catalogApi[Catalog API]
        patronApi[Patron API]
        circulationApi[Circulation API]
        holdApi[Hold API]
        acquisitionsApi[Acquisitions API]
        adminApi[Admin API]
        projector[Search Projector]
        notifier[Notification Adapter]
    end

    auth --> catalogApi
    auth --> patronApi
    auth --> circulationApi
    auth --> holdApi
    auth --> acquisitionsApi
    auth --> adminApi
    circulationApi --> notifier
    holdApi --> notifier
    catalogApi --> projector
    acquisitionsApi --> projector
```

## Borrowing & Reservation Lifecycle, Consistency, Penalties, and Exception Patterns

### Artifact focus: Component-level responsibility allocation

This section is intentionally tailored for this specific document so implementation teams can convert architecture and analysis into build-ready tasks.

### Implementation directives for this artifact
- Show which component owns policy evaluation versus state mutation versus notification dispatch.
- Identify synchronous versus asynchronous boundaries and where outbox relay runs.
- Add explicit anti-corruption layer between legacy catalog systems and circulation domain.

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
    API[Circulation API] --> POL[Policy Engine]
    API --> APP[Application Service]
    APP --> REPO[(Loan/Hold Repositories)]
    APP --> OUT[(Outbox)]
    OUT --> PUB[Event Publisher]
    PUB --> BUS[(Event Bus)]
    BUS --> NOTIF[Notification Service]
```

### Definition of done for this artifact
- Content is specific to this artifact type and not a generic duplicate.
- Rules are testable (unit/integration/contract) and reference concrete data/events/errors.
- Diagram semantics (if present) are consistent with textual constraints and lifecycle behavior.
