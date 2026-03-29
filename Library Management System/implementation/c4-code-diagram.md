# C4 Code Diagram - Library Management System

```mermaid
flowchart TB
    subgraph api[apps/api]
        controllers[Controllers]
        guards[Auth Guards]
        commands[Command Handlers]
        queries[Query Handlers]
    end

    subgraph domain[packages/domain]
        catalog[Catalog Module]
        patrons[Patrons Module]
        circulation[Circulation Module]
        holds[Holds Module]
        acquisitions[Acquisitions Module]
        policies[Policies Module]
    end

    subgraph worker[apps/worker]
        overdue[Overdue Jobs]
        notifications[Notification Jobs]
        searchProjector[Search Projector]
        imports[Import and Reindex Jobs]
    end

    controllers --> guards
    controllers --> commands
    controllers --> queries
    commands --> catalog
    commands --> patrons
    commands --> circulation
    commands --> holds
    commands --> acquisitions
    commands --> policies
    queries --> catalog
    queries --> patrons
    queries --> holds
    overdue --> circulation
    notifications --> holds
    searchProjector --> catalog
    imports --> catalog
```

## Borrowing & Reservation Lifecycle, Consistency, Penalties, and Exception Patterns

### Artifact focus: Code-level module organization

This section is intentionally tailored for this specific document so implementation teams can convert architecture and analysis into build-ready tasks.

### Implementation directives for this artifact
- Map application modules to domain capabilities and identify anti-corruption layers.
- Define module dependency direction to enforce clean architecture boundaries.
- List extension points for policy plugins and provider adapters.

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
