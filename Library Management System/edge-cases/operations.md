# Edge Cases - Operations

| Scenario | Impact | Mitigation |
|----------|--------|------------|
| Background jobs lag, delaying overdue notices or hold notifications | Patron communication becomes unreliable | Monitor queue depth, freshness, and retry rates |
| Branch loses connectivity during checkout | Staff cannot serve patrons | Provide degraded offline transaction buffering or documented fallback process |
| Search cluster outage occurs | Discovery slows or fails | Fallback to database-backed minimal search for staff-critical flows |
| Clock skew across services affects due dates and fines | Policy errors accumulate | Standardize time sources and centralize deadline calculations |
| Bulk import or reindex floods reporting systems | Operational instability | Use backpressure, staged rollouts, and observable reprocessing workflows |

## Borrowing & Reservation Lifecycle, Consistency, Penalties, and Exception Patterns

### Artifact focus: Operational failure and recovery scenarios

This section is intentionally tailored for this specific document so implementation teams can convert architecture and analysis into build-ready tasks.

### Implementation directives for this artifact
- Document backlog surge handling for allocator/fine jobs and safe throttling settings.
- Provide replay and backfill strategy after prolonged message bus outage.
- Define operator-only emergency controls and post-incident audit expectations.

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
