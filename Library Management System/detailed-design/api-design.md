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
