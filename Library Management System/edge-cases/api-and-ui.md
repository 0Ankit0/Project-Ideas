# Edge Cases - API and UI

| Scenario | Impact | Mitigation |
|----------|--------|------------|
| Search index is stale after recent returns | Patron sees incorrect availability | Display freshness indicators and reconcile from authoritative store when needed |
| Staff and patron edit account preferences concurrently | Lost updates | Use optimistic concurrency and explicit conflict messaging |
| Very large hold queues slow item-detail pages | UX degradation | Cache queue summaries and paginate administrative detail views |
| Staff workspace leaks patron borrowing history across branches | Privacy breach | Enforce branch and role scopes before query and render |
| Barcode scanner sends malformed input bursts | Desk workflow breaks | Normalize input and validate scan patterns before transaction execution |

## Borrowing & Reservation Lifecycle, Consistency, Penalties, and Exception Patterns

### Artifact focus: API/UI failure and usability scenarios

This section is intentionally tailored for this specific document so implementation teams can convert architecture and analysis into build-ready tasks.

### Implementation directives for this artifact
- Describe offline retry UX for kiosk/self-check devices with eventual command submission.
- Define optimistic UI rollback behavior when backend conflicts occur.
- Standardize error-to-user-message mapping from machine error codes.

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
