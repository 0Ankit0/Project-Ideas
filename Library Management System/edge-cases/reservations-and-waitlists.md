# Edge Cases - Reservations and Waitlists

| Scenario | Impact | Mitigation |
|----------|--------|------------|
| Patron places hold on a title with many branch-specific copies | Queue fairness becomes unclear | Separate title-level request logic from fulfillment-copy selection |
| Returned item should satisfy a hold at another branch | Delays and misrouting | Auto-create transfer workflow with chain-of-custody states |
| Patron misses pickup window | Queue stalls | Auto-expire hold and advance next eligible request |
| Patron becomes blocked after hold placement but before pickup | Hold fairness conflict | Revalidate eligibility at fulfillment time and pause or skip appropriately |
| High-demand title receives hundreds of holds | Performance and transparency issues | Provide queue-position visibility with bounded recalculation cost |

## Borrowing & Reservation Lifecycle, Consistency, Penalties, and Exception Patterns

### Artifact focus: Queue fairness and reservation anomalies

This section is intentionally tailored for this specific document so implementation teams can convert architecture and analysis into build-ready tasks.

### Implementation directives for this artifact
- Define tie-breakers for same-timestamp holds and branch-priority lanes.
- Handle account status changes after queue entry but before allocation.
- Specify prevention and remediation for duplicate waitlist entries created by race conditions.

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
