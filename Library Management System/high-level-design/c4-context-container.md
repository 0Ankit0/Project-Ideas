# C4 Context and Container Diagrams - Library Management System

## C4 Context

```mermaid
flowchart LR
    patrons[Patrons]
    staff[Library Staff]
    vendors[Vendors and Suppliers]
    payment[Payment Provider]
    digital[Digital Content Provider]
    notify[Notification Services]

    system[Library Management System]

    patrons --> system
    staff --> system
    system --> vendors
    system --> payment
    system --> digital
    system --> notify
```

## C4 Container

```mermaid
flowchart TB
    subgraph users[Users]
        patronWeb[Patron Portal Web App]
        staffWeb[Staff Workspace Web App]
    end

    subgraph app[Application Containers]
        api[REST API]
        workers[Background Workers]
        projector[Search and Reporting Projector]
    end

    subgraph stores[Data Stores]
        db[(PostgreSQL)]
        idx[(Search Index)]
        queue[(Message Bus)]
        blob[(Object Storage)]
    end

    patronWeb --> api
    staffWeb --> api
    api --> db
    api --> blob
    api --> queue
    workers --> db
    workers --> queue
    projector --> db
    projector --> idx
    queue --> workers
    queue --> projector
```

## Borrowing & Reservation Lifecycle, Consistency, Penalties, and Exception Patterns

### Artifact focus: C4 context/container implementation notes

This section is intentionally tailored for this specific document so implementation teams can convert architecture and analysis into build-ready tasks.

### Implementation directives for this artifact
- Show which containers are stateful versus stateless and how they scale.
- Define inter-container authN/authZ mechanism and token scopes.
- Add container-level failure domains and circuit-breaker boundaries.

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
