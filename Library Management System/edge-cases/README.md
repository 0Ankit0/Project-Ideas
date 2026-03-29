# Edge Cases - Library Management System

This folder captures cross-cutting scenarios that can break catalog accuracy, circulation integrity, hold fairness, patron experience, security, or branch operations if they are not handled deliberately.

## Contents

- `catalog-and-metadata.md`
- `circulation-and-overdues.md`
- `reservations-and-waitlists.md`
- `acquisitions-and-inventory.md`
- `digital-lending-and-access.md`
- `api-and-ui.md`
- `security-and-compliance.md`
- `operations.md`

## Borrowing & Reservation Lifecycle, Consistency, Penalties, and Exception Patterns

### Artifact focus: Edge-case governance index

This section is intentionally tailored for this specific document so implementation teams can convert architecture and analysis into build-ready tasks.

### Implementation directives for this artifact
- List edge-case classes by domain (circulation, catalog, security, operations) with owner and severity.
- Define triage workflow and SLA for documenting newly discovered production edge cases.
- Link each edge case to automated regression tests and observability signals.

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
