# Edge Cases - Catalog and Metadata

| Scenario | Impact | Mitigation |
|----------|--------|------------|
| Duplicate bibliographic records created by different staff | Search confusion and split availability | Add duplicate-detection, merge workflow, and canonical-record controls |
| Same title has multiple editions or formats | Patrons place wrong holds or staff check wrong item | Separate work/expression/format metadata clearly in catalog views |
| Barcode assigned twice by mistake | Inventory integrity breaks | Enforce global uniqueness and require supervised override paths |
| Cataloging incomplete when stock arrives | Items exist physically but not discoverably | Support pre-catalog holding states and accession queues |
| Subject or classification changes ripple inconsistently | Search relevance and shelfing degrade | Version metadata changes and reindex affected records |

## Borrowing & Reservation Lifecycle, Consistency, Penalties, and Exception Patterns

### Artifact focus: Catalog/metadata anomaly handling

This section is intentionally tailored for this specific document so implementation teams can convert architecture and analysis into build-ready tasks.

### Implementation directives for this artifact
- Handle title merges/splits while preserving hold queues and loan history continuity.
- Define authority-control updates and de-duplication effects on search and holds.
- Explain suppression/un-suppression semantics and audit requirements.

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
