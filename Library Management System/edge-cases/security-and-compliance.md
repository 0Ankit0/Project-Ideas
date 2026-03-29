# Edge Cases - Security and Compliance

| Scenario | Impact | Mitigation |
|----------|--------|------------|
| Patron reading history exposed to unauthorized staff | Major privacy violation | Limit access by role and mask history unless operationally justified |
| Waivers or fee adjustments performed without traceability | Audit failure | Require reason capture and immutable audit logging |
| Shared staff credentials used at branch desks | Accountability loss | Enforce individual logins, session timeout, and privileged-action attribution |
| Export contains personally identifiable patron data beyond purpose | Privacy and compliance risk | Use scoped exports, data minimization, and approval workflows |
| API keys for digital or payment providers leak | Third-party account compromise | Rotate secrets and isolate integration credentials by environment |

## Borrowing & Reservation Lifecycle, Consistency, Penalties, and Exception Patterns

### Artifact focus: Security/compliance exception model

This section is intentionally tailored for this specific document so implementation teams can convert architecture and analysis into build-ready tasks.

### Implementation directives for this artifact
- Cover privileged override workflow with just-in-time elevation and reason-code capture.
- Define fraud and abuse detection indicators for repeated waiver and no-show patterns.
- Specify data subject request handling impacts on historical circulation records.

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
