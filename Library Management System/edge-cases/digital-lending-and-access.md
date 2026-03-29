# Edge Cases - Digital Lending and Access

| Scenario | Impact | Mitigation |
|----------|--------|------------|
| Digital provider reports fewer licenses than local system expects | Access denial or oversubscription | Reconcile provider entitlements regularly and prefer provider truth |
| Patron account expires during active digital loan | Access-control ambiguity | Define whether active access continues until expiry or is revoked immediately |
| Provider outage blocks content delivery | Patron sees broken experience | Surface degraded-mode messaging and retry or fallback guidance |
| Same title exists in physical and digital forms | Hold and availability UX becomes confusing | Distinguish fulfillment format clearly in discovery and account views |
| License expires while hold queue exists | Patron dissatisfaction | Notify affected patrons and cancel or re-route demand based on policy |

## Borrowing & Reservation Lifecycle, Consistency, Penalties, and Exception Patterns

### Artifact focus: Digital lending constraints

This section is intentionally tailored for this specific document so implementation teams can convert architecture and analysis into build-ready tasks.

### Implementation directives for this artifact
- Define token/license expiration behavior and re-checkout limits for digital assets.
- Specify DRM or provider outage fallback experience and entitlement reconciliation.
- Cover simultaneous-use licenses and waitlist behavior under provider sync lag.

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
