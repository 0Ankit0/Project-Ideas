# Deployment Diagram - Library Management System

```mermaid
flowchart TB
    internet[Patron Internet Access] --> edge[WAF / CDN]
    staffNet[Branch or Corporate Network] --> internalLb[Internal Access Gateway]
    edge --> patronWeb[Patron Portal Frontend]
    internalLb --> staffWeb[Staff Workspace Frontend]
    patronWeb --> api[Application API Cluster]
    staffWeb --> api
    api --> workers[Background Worker Cluster]
    api --> db[(Managed PostgreSQL)]
    api --> search[(Search Cluster)]
    api --> queue[(Managed Queue / Bus)]
    api --> object[(Object Storage)]
    workers --> db
    workers --> queue
    workers --> object
```

## Deployment Notes
- Patron and staff interfaces are separated at the edge even when they share backend services.
- Background workers handle notifications, fine assessment jobs, search projection, and batch inventory tasks.
- Search infrastructure should be isolated from primary write workloads to preserve transaction stability.

## Borrowing & Reservation Lifecycle, Consistency, Penalties, and Exception Patterns

### Artifact focus: Deployment topology and runtime isolation

This section is intentionally tailored for this specific document so implementation teams can convert architecture and analysis into build-ready tasks.

### Implementation directives for this artifact
- Map workloads to environments, regions, and fault domains.
- Document blue/green or canary strategy for zero-downtime releases.
- Define worker scaling policy for hold allocation and fine accrual processing.

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
