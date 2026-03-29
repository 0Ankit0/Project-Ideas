# Edge Cases - Circulation and Overdues

| Scenario | Impact | Mitigation |
|----------|--------|------------|
| Patron attempts checkout while account is just over fine threshold | Desk workflow ambiguity | Show hard block with override policy and reason capture |
| Item marked returned but physically missing | Inventory and patron history diverge | Use claimed-returned and search workflows before closing discrepancy |
| Holiday calendar changes after loan issued | Due dates and overdue logic shift | Version policies and preserve original calculated due dates unless explicit recalculation is allowed |
| Same item scanned twice during checkout or return | Duplicate transactions | Make circulation commands idempotent and display latest authoritative state |
| Lost item later reappears | Financial status and catalog state conflict | Allow reversal workflow with audit trail and conditional fee adjustments |

## Borrowing & Reservation Lifecycle, Consistency, Penalties, and Exception Patterns

### Artifact focus: Circulation and overdue corner cases

This section is intentionally tailored for this specific document so implementation teams can convert architecture and analysis into build-ready tasks.

### Implementation directives for this artifact
- Address daylight-saving transitions, branch holiday calendars, and due-time cutoff drift.
- Define fairness policy when hold allocation and return are processed concurrently.
- Cover partial returns in bundled media kits and per-component penalty rules.

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
