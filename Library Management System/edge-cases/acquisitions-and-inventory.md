# Edge Cases - Acquisitions and Inventory

| Scenario | Impact | Mitigation |
|----------|--------|------------|
| Vendor ships fewer items than ordered | Receiving mismatch | Record discrepancy and partial receipt states |
| Received items are damaged | Copy availability and financial records diverge | Capture damaged-on-receipt workflow and supplier follow-up |
| Inter-branch transfer never arrives | Inventory appears lost | Use dispatch, in-transit, received, and exception states with alerts |
| Shelf audit finds ghost items in system | Trust in inventory drops | Support discrepancy reconciliation with manager approval |
| Repair workflow lasts longer than expected | Holds and availability become misleading | Keep repair status visible and exclude from circulation eligibility |

## Borrowing & Reservation Lifecycle, Consistency, Penalties, and Exception Patterns

### Artifact focus: Acquisition/inventory edge handling

This section is intentionally tailored for this specific document so implementation teams can convert architecture and analysis into build-ready tasks.

### Implementation directives for this artifact
- Define behavior for duplicate barcodes, supplier short-shipments, and receiving mismatches.
- Specify quarantine workflow for newly received damaged copies before circulation eligibility.
- Cover retroactive metadata corrections and their impact on outstanding holds.

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
