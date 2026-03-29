# Network Infrastructure - Library Management System

## Network Zones

| Zone | Purpose | Key Controls |
|------|---------|--------------|
| Public Edge | Patron discovery and account access | TLS, WAF, rate limiting |
| Staff Access | Branch or internal operations access | SSO, private network or zero-trust gateway |
| Application Zone | API and worker services | Private subnets, service auth, secrets management |
| Data Zone | Database, search, queue, object storage | No direct public access, encrypted storage |
| Integration Zone | Vendors, notifications, payment, digital providers | Outbound allow-list, credential rotation |

## Traffic Principles
- Patron traffic enters only through the public edge.
- Staff access should traverse managed internal access controls.
- Search and reporting reads should not bypass application-level authorization for protected account data.
- Integrations should use rotated secrets and explicit retry/failure monitoring.

## Borrowing & Reservation Lifecycle, Consistency, Penalties, and Exception Patterns

### Artifact focus: Network and security controls

This section is intentionally tailored for this specific document so implementation teams can convert architecture and analysis into build-ready tasks.

### Implementation directives for this artifact
- Define ingress/egress rules, service mesh policy, and mTLS requirements.
- Specify WAF, DDoS protection, and rate limiting for public API surfaces.
- Document audit/log transport path and tamper-evident storage controls.

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
