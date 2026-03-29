# API Design - Library Management System

## API Style
- RESTful JSON APIs with role-aware authorization and branch scoping.
- Cursor pagination for large activity feeds, transaction logs, and search results.
- Idempotency keys for staff-side create operations such as checkout, receiving, and transfer requests.
- Search endpoints optimized for read-heavy discovery workloads; transactional endpoints remain strongly consistent.

## Core Endpoints

| Area | Method | Endpoint | Purpose |
|------|--------|----------|---------|
| Catalog | GET | `/api/v1/catalog/search` | Search titles and availability |
| Catalog | POST | `/api/v1/catalog/records` | Create bibliographic record |
| Catalog | POST | `/api/v1/catalog/records/{recordId}/copies` | Add item copy |
| Patrons | GET | `/api/v1/patrons/{patronId}` | Retrieve patron account |
| Patrons | PATCH | `/api/v1/patrons/{patronId}` | Update membership or restrictions |
| Loans | POST | `/api/v1/loans` | Issue item to patron |
| Loans | POST | `/api/v1/returns` | Return item and trigger downstream actions |
| Loans | POST | `/api/v1/loans/{loanId}/renew` | Renew eligible loan |
| Holds | POST | `/api/v1/holds` | Place hold |
| Holds | PATCH | `/api/v1/holds/{holdId}` | Cancel or update pickup details |
| Fines | POST | `/api/v1/fines/{entryId}/payments` | Record payment |
| Fines | POST | `/api/v1/fines/{entryId}/waive` | Apply waiver or adjustment |
| Acquisitions | POST | `/api/v1/purchase-orders` | Create purchase order |
| Inventory | POST | `/api/v1/transfers` | Create branch transfer |
| Inventory | POST | `/api/v1/inventory-audits` | Start audit session |
| Reports | GET | `/api/v1/reports/branch-summary` | Operational dashboards |
| Admin | PATCH | `/api/v1/admin/policies/{policyId}` | Update circulation or fine policies |

## Example: Checkout Request

```json
{
  "patronId": "pat_1001",
  "itemBarcode": "BC-00045911",
  "issuedAtBranchId": "br_main",
  "operatorId": "staff_22"
}
```

## Example: Hold Request

```json
{
  "patronId": "pat_1001",
  "recordId": "rec_391",
  "pickupBranchId": "br_north",
  "requestedFormat": "physical"
}
```

## Authorization Notes
- Patrons may search, manage their own holds, and view only their own account data.
- Staff permissions are scoped by branch and role to circulation, cataloging, acquisitions, or administration surfaces.
- Financial overrides, policy changes, and inventory write-offs require elevated roles and full audit logging.

## Borrowing & Reservation Lifecycle, Consistency, Penalties, and Exception Patterns

### Artifact focus: API surface and contract precision

This section is intentionally tailored for this specific document so implementation teams can convert architecture and analysis into build-ready tasks.

### Implementation directives for this artifact
- Define request/response schemas for checkout, renew, return, hold, cancel-hold, pay-fee, and waive-fee endpoints.
- Publish error model with deterministic codes and retry classification to support robust clients.
- Document optimistic concurrency fields (`etag`/`row_version`) and idempotency semantics for mutating operations.

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
