# API Design

## Table of Contents

1. [Overview](#overview)
2. [Authentication and Authorization](#authentication-and-authorization)
3. [Common Conventions](#common-conventions)
4. [Error Response Format](#error-response-format)
5. [Warehouse Management API](#warehouse-management-api)
6. [SKU Master API](#sku-master-api)
7. [Inventory API](#inventory-api)
8. [Receiving Orders API](#receiving-orders-api)
9. [Putaway Tasks API](#putaway-tasks-api)
10. [Wave Jobs API](#wave-jobs-api)
11. [Pick Lists API](#pick-lists-api)
12. [Shipment Orders API](#shipment-orders-api)
13. [Packing Lists API](#packing-lists-api)
14. [Shipments API](#shipments-api)
15. [Cycle Counts API](#cycle-counts-api)
16. [Replenishment API](#replenishment-api)
17. [Returns API](#returns-api)
18. [Carriers API](#carriers-api)
19. [Reports API](#reports-api)
20. [Request/Response JSON Schemas](#requestresponse-json-schemas)
21. [Pagination and Filtering](#pagination-and-filtering)
22. [Rate Limiting](#rate-limiting)
23. [Webhook Events](#webhook-events)

---

## Overview

### Base URL

```
https://api.wms.example.com/api/v1
```

### Versioning Strategy

All API paths are versioned using a URL path prefix (`/api/v1`, `/api/v2`). A new major version is introduced only when a breaking change cannot be avoided. The previous version is supported for a minimum of **12 months** after the successor is Generally Available.

- Deprecation notices are communicated via the `Deprecation` and `Sunset` response headers.
- Minor, additive changes (new optional fields, new endpoints) do NOT increment the version.
- Clients must check the `Deprecation` header and migrate before the `Sunset` date.

```
Deprecation: true
Sunset: Sat, 01 Jan 2027 00:00:00 GMT
Link: <https://api.wms.example.com/api/v2>; rel="successor-version"
```

### Content Type

All requests and responses use `application/json`. Clients must set:

```
Content-Type: application/json
Accept: application/json
```

### Authentication

Every request must include a Bearer JWT in the `Authorization` header:

```
Authorization: Bearer <token>
```

### Required Headers for Mutating Requests

All `POST`, `PUT`, `PATCH`, and `DELETE` requests must include:

| Header | Format | Description |
|---|---|---|
| `Idempotency-Key` | UUID v4 | Ensures safe retries; server returns cached response for duplicate keys within 24 h |
| `X-Correlation-Id` | UUID v4 | Propagated across all downstream service calls and included in audit logs |

---

## Authentication and Authorization

### JWT Structure

**Header**

```json
{
  "alg": "RS256",
  "typ": "JWT",
  "kid": "wms-signing-key-2025"
}
```

**Payload**

```json
{
  "sub": "usr_01HX9Z2KPQR4T5VWXY3B",
  "email": "picker@warehouse.example.com",
  "warehouse_ids": ["WH-001", "WH-002"],
  "scopes": ["wms:read", "wms:picking"],
  "roles": ["warehouse_operator"],
  "iat": 1716220800,
  "exp": 1716307200,
  "jti": "tok_9fae3b1c-0d2a-4f7e-bcd4-aef123456789",
  "iss": "https://auth.wms.example.com",
  "aud": "https://api.wms.example.com"
}
```

### Scopes

| Scope | Description | Typical Roles |
|---|---|---|
| `wms:read` | Read-only access to all resources | Analyst, Auditor |
| `wms:write` | Create and update non-privileged resources | Warehouse Operator |
| `wms:admin` | Full access including destructive operations | Warehouse Admin |
| `wms:receiving` | Receive ASN lines, close receiving orders | Receiving Clerk |
| `wms:picking` | Confirm pick lines, report short picks | Picker |
| `wms:shipping` | Confirm packing, close shipments | Packer, Shipping Clerk |
| `wms:counting` | Submit cycle count results, request recounts | Inventory Counter |
| `wms:returns` | Receive, inspect, and disposition returns | Returns Processor |
| `wms:reports` | Access all reporting endpoints | Manager, Analyst |

### Rate Limiting Headers

Every response includes the following headers:

| Header | Description |
|---|---|
| `X-RateLimit-Limit` | Maximum requests allowed in the current window |
| `X-RateLimit-Remaining` | Requests remaining in the current window |
| `X-RateLimit-Reset` | Unix epoch timestamp when the window resets |
| `Retry-After` | Seconds to wait before retrying (only on `429` responses) |

### Rate Limits by Tier

| Tier / Scope | Requests / Minute | Burst | Notes |
|---|---|---|---|
| `wms:read` (standard) | 300 | 500 | Per user token |
| `wms:write` (standard) | 120 | 200 | Per user token |
| `wms:admin` | 60 | 100 | Per user token |
| `wms:reports` | 30 | 50 | Expensive aggregation queries |
| Service-to-service (machine token) | 1 200 | 2 000 | Per client_id |
| Global per-warehouse partition | 5 000 | 8 000 | Shared across all users of a warehouse |

When a limit is exceeded the server returns `429 Too Many Requests` with a `Retry-After` header.

---

## Common Conventions

### Pagination

All collection endpoints support **cursor-based pagination** by default.

| Field | Type | Description |
|---|---|---|
| `cursor` | string | Opaque cursor returned by the previous page |
| `limit` | integer | Maximum number of records per page (default: 20, max: 100) |
| `hasNextPage` | boolean | Whether more records follow |
| `nextCursor` | string | Cursor to pass in the next request |
| `totalCount` | integer | Total matching records (only included when `?includeTotalCount=true`) |

**Cursor-based example:**

```
GET /api/v1/inventory?limit=50&cursor=eyJpZCI6IklOVi0wMDEyMyJ9
```

**Offset-based (legacy compatibility):**

| Param | Description |
|---|---|
| `page` | 1-based page number |
| `pageSize` | Records per page (default: 20, max: 100) |

```
GET /api/v1/inventory?page=3&pageSize=25
```

### Filtering

Use the `filter[field][operator]=value` query syntax.

| Operator | Meaning | Example |
|---|---|---|
| `eq` (default) | Equal | `filter[status]=PENDING` |
| `neq` | Not equal | `filter[status][neq]=CLOSED` |
| `gt` | Greater than | `filter[qty][gt]=0` |
| `gte` | Greater than or equal | `filter[createdAt][gte]=2025-01-01` |
| `lt` | Less than | `filter[qty][lt]=10` |
| `lte` | Less than or equal | `filter[updatedAt][lte]=2025-06-30T23:59:59Z` |
| `in` | In set | `filter[warehouseId][in]=WH-001,WH-002` |
| `contains` | Substring match | `filter[skuCode][contains]=PROD-` |

Multiple filters are ANDed together.

### Sorting

```
GET /api/v1/receiving-orders?sort=createdAt          # ascending
GET /api/v1/receiving-orders?sort=-createdAt         # descending
GET /api/v1/receiving-orders?sort=-priority,createdAt # multi-field
```

### Field Selection (Sparse Fieldsets)

```
GET /api/v1/inventory?fields=id,skuId,binId,qty,status
```

Only the listed fields are returned in each object, reducing payload size.

### Idempotency

- Clients MUST supply a unique UUID v4 `Idempotency-Key` for every mutating request.
- If the server receives an identical key within **24 hours**, it returns the original response (with a `208 Already Reported` status for duplicate detection) without re-processing.
- Different resources MUST use different idempotency keys.

### X-Correlation-Id

- Clients SHOULD generate and attach a UUID v4 `X-Correlation-Id` to every request.
- If not provided, the gateway generates one.
- The correlation ID appears in all log entries and error responses, facilitating distributed tracing.

---

## Error Response Format

All errors follow a consistent JSON envelope:

```json
{
  "error": {
    "code": "STOCK_BELOW_ZERO",
    "message": "The requested operation would bring on-hand quantity below zero.",
    "details": [
      {
        "field": "pickedQty",
        "issue": "Value 10 exceeds available reservation quantity 7.",
        "location": "body"
      }
    ],
    "retryable": false,
    "correlationId": "c3d4e5f6-0000-4abc-9def-aabbccdd0011",
    "documentationUrl": "https://docs.wms.example.com/errors/STOCK_BELOW_ZERO"
  }
}
```

### Error Code Catalog

| HTTP Status | Error Code | Retryable | Description |
|---|---|---|---|
| 400 | `INVALID_REQUEST_BODY` | No | Malformed JSON or missing required fields |
| 400 | `INVALID_FIELD_VALUE` | No | A field value fails type or format validation |
| 400 | `FILTER_SYNTAX_ERROR` | No | Unrecognized filter operator or field name |
| 401 | `UNAUTHORIZED` | No | Missing or invalid Authorization header |
| 401 | `TOKEN_EXPIRED` | No | JWT has passed its `exp` claim |
| 403 | `FORBIDDEN` | No | Token lacks required scope |
| 403 | `WAREHOUSE_ACCESS_DENIED` | No | Token does not include the target warehouse ID |
| 404 | `RESOURCE_NOT_FOUND` | No | The requested resource ID does not exist |
| 409 | `DUPLICATE_IDEMPOTENCY_KEY` | No | Idempotency key reused with different payload |
| 409 | `STATE_TRANSITION_INVALID` | No | Resource is in a state that does not allow the action |
| 409 | `DUPLICATE_GENERATION` | No | Putaway or wave tasks already generated for this batch |
| 409 | `RESERVATION_MISMATCH` | No | Pick confirmation reservation ID does not match task |
| 409 | `EXCEPTION_STATE_CONFLICT` | No | Exception is already resolved or cancelled |
| 409 | `WAVE_ALREADY_RELEASED` | No | Wave cannot be modified after release |
| 409 | `CYCLE_COUNT_ALREADY_APPROVED` | No | Count cannot be re-submitted after approval |
| 422 | `RECEIPT_TOLERANCE_BREACH` | No | Received qty exceeds ASN tolerance percentage |
| 422 | `STOCK_BELOW_ZERO` | No | Operation would create negative on-hand quantity |
| 422 | `PACK_RECONCILIATION_FAILED` | No | Packed items do not match shipment order lines |
| 422 | `INSUFFICIENT_ALLOCATABLE_STOCK` | No | Not enough ATP stock to build wave |
| 422 | `BIN_CAPACITY_EXCEEDED` | No | Putaway target bin cannot hold the requested quantity |
| 422 | `RETURN_DISPOSITION_INVALID` | No | Disposition code not valid for item condition |
| 422 | `LABEL_GENERATION_FAILED` | No | Carrier rejected label request (see details) |
| 429 | `RATE_LIMIT_EXCEEDED` | Yes | Too many requests; see `Retry-After` header |
| 500 | `INTERNAL_SERVER_ERROR` | Yes | Unexpected server error |
| 503 | `CARRIER_CONFIRMATION_UNAVAILABLE` | Yes | Carrier API is temporarily unavailable |
| 503 | `SERVICE_UNAVAILABLE` | Yes | Downstream dependency is down |

---

## Warehouse Management API

Base path: `/api/v1/warehouses`

### `GET /warehouses`

Retrieve a paginated list of warehouses the token has access to.

- **Scope:** `wms:read`
- **Query params:** `filter[status]`, `filter[country]`, `sort`, `cursor`, `limit`

**Response `200`:**

```json
{
  "data": [
    {
      "id": "WH-001",
      "name": "North Distribution Center",
      "address": { "street": "100 Logistics Blvd", "city": "Memphis", "state": "TN", "zip": "38118", "country": "US" },
      "status": "ACTIVE",
      "totalBins": 12400,
      "createdAt": "2022-06-01T00:00:00Z"
    }
  ],
  "cursor": null,
  "hasNextPage": false
}
```

---

### `POST /warehouses`

Create a new warehouse.

- **Scope:** `wms:admin`
- **Required headers:** `Idempotency-Key`, `X-Correlation-Id`

**Request body:**

```json
{
  "name": "South Fulfillment Hub",
  "address": { "street": "200 Warehouse Dr", "city": "Atlanta", "state": "GA", "zip": "30301", "country": "US" },
  "timezone": "America/New_York",
  "operatingHours": { "open": "06:00", "close": "22:00" }
}
```

**Response `201`:** Returns full warehouse object with generated `id`.

**Errors:** `INVALID_FIELD_VALUE`, `FORBIDDEN`

---

### `GET /warehouses/{id}`

Retrieve a single warehouse by ID.

- **Scope:** `wms:read`

**Response `200`:** Full warehouse object including zone summary counts.

**Errors:** `RESOURCE_NOT_FOUND`, `WAREHOUSE_ACCESS_DENIED`

---

### `PUT /warehouses/{id}`

Full update of a warehouse record.

- **Scope:** `wms:admin`
- **Required headers:** `Idempotency-Key`, `X-Correlation-Id`

**Request body:** Same schema as `POST /warehouses`. All fields required.

**Response `200`:** Updated warehouse object.

**Errors:** `RESOURCE_NOT_FOUND`, `INVALID_FIELD_VALUE`

---

### `GET /warehouses/{id}/zones`

List all zones within a warehouse.

- **Scope:** `wms:read`
- **Query params:** `filter[type]` (`RECEIVING`, `STORAGE`, `PICKING`, `STAGING`, `SHIPPING`, `RETURNS`), `sort`, `cursor`, `limit`

**Response `200`:**

```json
{
  "data": [
    {
      "id": "ZN-001",
      "warehouseId": "WH-001",
      "name": "Zone A — Bulk Storage",
      "type": "STORAGE",
      "temperature": "AMBIENT",
      "binCount": 3200,
      "status": "ACTIVE"
    }
  ],
  "hasNextPage": false
}
```

---

### `POST /warehouses/{id}/zones`

Create a new zone within the warehouse.

- **Scope:** `wms:admin`
- **Required headers:** `Idempotency-Key`, `X-Correlation-Id`

**Request body fields:**

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | Yes | Human-readable zone name |
| `type` | enum | Yes | `RECEIVING`, `STORAGE`, `PICKING`, `STAGING`, `SHIPPING`, `RETURNS` |
| `temperature` | enum | No | `AMBIENT`, `REFRIGERATED`, `FROZEN` (default: `AMBIENT`) |
| `pickingStrategy` | enum | No | `FIFO`, `FEFO`, `LIFO` (default: `FIFO`) |

**Response `201`:** Zone object with generated `id`.

---

### `GET /warehouses/{warehouseId}/zones/{zoneId}/bins`

List bins in a zone with optional availability filters.

- **Scope:** `wms:read`
- **Query params:** `filter[status]` (`ACTIVE`, `BLOCKED`, `MAINTENANCE`), `filter[isEmpty]=true`, `sort=aisle,level`, `cursor`, `limit`

**Response `200`:**

```json
{
  "data": [
    {
      "id": "BIN-A-01-01",
      "zoneId": "ZN-001",
      "aisle": "A",
      "bay": "01",
      "level": "01",
      "maxWeight": 500,
      "maxVolume": 2.0,
      "currentWeight": 120.5,
      "status": "ACTIVE",
      "isEmpty": false
    }
  ],
  "hasNextPage": true,
  "nextCursor": "eyJpZCI6IkJJTi1BLTAxLTA1In0="
}
```

---

### `POST /warehouses/{warehouseId}/zones/{zoneId}/bins`

Create one or more bins (bulk create supported).

- **Scope:** `wms:admin`
- **Required headers:** `Idempotency-Key`, `X-Correlation-Id`

**Request body:**

```json
{
  "bins": [
    { "aisle": "B", "bay": "02", "level": "03", "maxWeight": 300, "maxVolume": 1.5 },
    { "aisle": "B", "bay": "02", "level": "04", "maxWeight": 300, "maxVolume": 1.5 }
  ]
}
```

**Response `201`:** Array of created bin objects with generated IDs.

---

### `PATCH /warehouses/{warehouseId}/zones/{zoneId}/bins/{binId}`

Update bin status or capacity constraints.

- **Scope:** `wms:admin`
- **Required headers:** `Idempotency-Key`, `X-Correlation-Id`

**Request body (partial update):**

```json
{
  "status": "MAINTENANCE",
  "maintenanceReason": "Damaged rack — pending repair"
}
```

**Response `200`:** Updated bin object.

**Errors:** `RESOURCE_NOT_FOUND`, `STATE_TRANSITION_INVALID`

---

## SKU Master API

Base path: `/api/v1/sku-master`

### `GET /sku-master`

Paginated list of SKU records.

- **Scope:** `wms:read`
- **Query params:** `filter[status]`, `filter[category]`, `filter[supplierId]`, `filter[skuCode][contains]`, `sort=-createdAt`, `cursor`, `limit`

**Response `200`:**

```json
{
  "data": [
    {
      "id": "SKU-0001",
      "skuCode": "PROD-ABC-001",
      "description": "Blue Widget 500ml",
      "category": "WIDGETS",
      "unitOfMeasure": "EACH",
      "weight": 0.45,
      "dimensions": { "lengthCm": 10, "widthCm": 8, "heightCm": 6 },
      "hazmat": false,
      "perishable": false,
      "serialTracked": false,
      "lotTracked": true,
      "status": "ACTIVE"
    }
  ],
  "hasNextPage": false
}
```

---

### `POST /sku-master`

Create a new SKU.

- **Scope:** `wms:write`
- **Required headers:** `Idempotency-Key`, `X-Correlation-Id`

**Request body fields:**

| Field | Type | Required | Description |
|---|---|---|---|
| `skuCode` | string | Yes | Unique business key |
| `description` | string | Yes | Human-readable name |
| `category` | string | Yes | Product category |
| `unitOfMeasure` | enum | Yes | `EACH`, `CASE`, `PALLET`, `KG`, `LITRE` |
| `weight` | number | No | Weight in kg |
| `dimensions` | object | No | `lengthCm`, `widthCm`, `heightCm` |
| `hazmat` | boolean | No | Hazardous material flag |
| `perishable` | boolean | No | Perishable / expiry-tracked |
| `serialTracked` | boolean | No | Serial number tracking required |
| `lotTracked` | boolean | No | Lot / batch tracking required |
| `minStock` | integer | No | Replenishment trigger threshold |
| `maxStock` | integer | No | Replenishment target quantity |

**Response `201`:** SKU object with generated `id`.

**Errors:** `INVALID_FIELD_VALUE` (duplicate `skuCode`)

---

### `GET /sku-master/{skuId}`

Get a single SKU record.

- **Scope:** `wms:read`

**Response `200`:** Full SKU object.

**Errors:** `RESOURCE_NOT_FOUND`

---

### `PUT /sku-master/{skuId}`

Full update of a SKU record.

- **Scope:** `wms:write`
- **Required headers:** `Idempotency-Key`, `X-Correlation-Id`

**Response `200`:** Updated SKU object.

**Errors:** `RESOURCE_NOT_FOUND`, `INVALID_FIELD_VALUE`

---

### `GET /sku-master/{skuId}/inventory`

Return a summary of on-hand, reserved, and available-to-promise (ATP) quantities across all warehouses for this SKU.

- **Scope:** `wms:read`
- **Query params:** `filter[warehouseId]`

**Response `200`:**

```json
{
  "skuId": "SKU-0001",
  "summary": [
    {
      "warehouseId": "WH-001",
      "onHand": 450,
      "reserved": 120,
      "atp": 330,
      "inReceiving": 50,
      "inTransit": 0
    }
  ]
}
```

---

## Inventory API

Base path: `/api/v1/inventory`

### `GET /inventory`

List inventory records with rich filtering.

- **Scope:** `wms:read`
- **Query params:**

| Param | Example | Description |
|---|---|---|
| `filter[warehouseId]` | `WH-001` | Restrict to warehouse |
| `filter[zoneId]` | `ZN-002` | Restrict to zone |
| `filter[binId]` | `BIN-A-01-01` | Restrict to bin |
| `filter[skuId]` | `SKU-0001` | Restrict to SKU |
| `filter[status]` | `AVAILABLE` | `AVAILABLE`, `RESERVED`, `QUARANTINE`, `DAMAGED` |
| `filter[lotNumber]` | `LOT-2025-01` | Lot number |
| `filter[expiryDate][lte]` | `2025-12-31` | Expiry date filter |
| `sort` | `-onHand` | Sort field |
| `cursor`, `limit` | — | Pagination |

**Response `200`:**

```json
{
  "data": [
    {
      "id": "INV-00123",
      "warehouseId": "WH-001",
      "zoneId": "ZN-001",
      "binId": "BIN-A-01-01",
      "skuId": "SKU-0001",
      "lotNumber": "LOT-2025-01",
      "expiryDate": "2026-01-15",
      "qty": 80,
      "reservedQty": 20,
      "status": "AVAILABLE",
      "lastCountedAt": "2025-04-10T08:00:00Z"
    }
  ],
  "hasNextPage": true,
  "nextCursor": "eyJpZCI6IklOVi0wMDEyNCJ9"
}
```

---

### `GET /inventory/{binId}`

Get all inventory records for a specific bin.

- **Scope:** `wms:read`

**Response `200`:** Array of inventory records for the bin.

---

### `POST /inventory/adjustments`

Manually adjust inventory quantity with a reason code.

- **Scope:** `wms:write`
- **Required headers:** `Idempotency-Key`, `X-Correlation-Id`

**Request body:**

```json
{
  "warehouseId": "WH-001",
  "binId": "BIN-A-01-01",
  "skuId": "SKU-0001",
  "lotNumber": "LOT-2025-01",
  "adjustmentQty": -5,
  "reasonCode": "DAMAGED_IN_STORAGE",
  "notes": "Found 5 units with broken packaging during audit"
}
```

**Response `200`:**

```json
{
  "adjustmentId": "ADJ-00099",
  "previousQty": 80,
  "newQty": 75,
  "status": "APPLIED",
  "appliedAt": "2025-06-10T14:22:00Z"
}
```

**Errors:** `STOCK_BELOW_ZERO`, `RESOURCE_NOT_FOUND`

---

### `GET /inventory/ledger`

Retrieve the immutable inventory ledger (audit trail of all quantity changes).

- **Scope:** `wms:read`
- **Query params:** `filter[skuId]`, `filter[binId]`, `filter[eventType]`, `filter[createdAt][gte]`, `filter[createdAt][lte]`, `sort=-createdAt`, `cursor`, `limit`

**Response `200`:** Paginated list of ledger entries with `eventType`, `deltaQty`, `newQty`, `referenceId`, `actorId`, `correlationId`, `createdAt`.

---

### `POST /inventory/transfers`

Initiate an internal inventory transfer between bins or warehouses.

- **Scope:** `wms:write`
- **Required headers:** `Idempotency-Key`, `X-Correlation-Id`

**Request body:**

```json
{
  "skuId": "SKU-0001",
  "lotNumber": "LOT-2025-01",
  "qty": 30,
  "fromBinId": "BIN-A-01-01",
  "toBinId": "BIN-C-05-02",
  "reason": "ZONE_CONSOLIDATION"
}
```

**Response `202`:**

```json
{
  "transferId": "TRF-00055",
  "status": "PENDING_CONFIRMATION",
  "fromBinId": "BIN-A-01-01",
  "toBinId": "BIN-C-05-02",
  "qty": 30,
  "createdAt": "2025-06-10T14:30:00Z"
}
```

---

### `GET /inventory/transfers/{transferId}`

Get status of an inventory transfer.

- **Scope:** `wms:read`

---

### `PATCH /inventory/transfers/{transferId}/confirm`

Confirm that a physical inventory transfer has been completed.

- **Scope:** `wms:write`
- **Required headers:** `Idempotency-Key`, `X-Correlation-Id`

**Request body:**

```json
{
  "confirmedQty": 30,
  "deviceTimestamp": "2025-06-10T14:55:00Z"
}
```

**Response `200`:** Updated transfer object with `status: COMPLETED`.

**Errors:** `STATE_TRANSITION_INVALID`, `STOCK_BELOW_ZERO`

---

## Receiving Orders API

Base path: `/api/v1/receiving-orders`

### `GET /receiving-orders`

List receiving orders (ASNs) with filters.

- **Scope:** `wms:read`
- **Query params:** `filter[warehouseId]`, `filter[status]` (`OPEN`, `IN_PROGRESS`, `CLOSED`, `DISCREPANCY`), `filter[supplierId]`, `filter[expectedDateFrom]`, `filter[expectedDateTo]`, `sort=-expectedDate`, `cursor`, `limit`

---

### `POST /receiving-orders`

Create a new receiving order / ASN.

- **Scope:** `wms:receiving`
- **Required headers:** `Idempotency-Key`, `X-Correlation-Id`

**Request body:**

```json
{
  "warehouseId": "WH-001",
  "supplierId": "SUP-012",
  "purchaseOrderId": "PO-20250601-001",
  "expectedDate": "2025-06-15",
  "lines": [
    { "skuId": "SKU-0001", "expectedQty": 200, "unitCost": 4.50 },
    { "skuId": "SKU-0002", "expectedQty": 100, "unitCost": 12.00 }
  ]
}
```

**Response `201`:** Receiving order with generated `id` and `lines[].asnLineId`.

---

### `GET /receiving-orders/{id}`

Get full receiving order including line details and receipt history.

- **Scope:** `wms:read`

---

### `POST /receiving-orders/{id}/receive`

Record the physical receipt of one ASN line.

- **Scope:** `wms:receiving`
- **Required headers:** `Idempotency-Key`, `X-Correlation-Id`

**Request body:**

```json
{
  "asnLineId": "ASNL-001",
  "receivedQty": 195,
  "lotNumber": "LOT-2025-06-A",
  "expiryDate": "2026-06-01",
  "serialNumbers": [],
  "condition": "GOOD",
  "receivingBinId": "BIN-RECV-01",
  "deviceTimestamp": "2025-06-15T09:30:00Z"
}
```

**Response `200`:**

```json
{
  "receiptId": "RCP-00444",
  "asnLineId": "ASNL-001",
  "receivedQty": 195,
  "toleranceStatus": "WITHIN_TOLERANCE",
  "inventoryRecordId": "INV-00201",
  "putawayTaskId": "PAT-00310",
  "status": "RECEIVED"
}
```

**Errors:** `RECEIPT_TOLERANCE_BREACH`, `RESOURCE_NOT_FOUND`, `STATE_TRANSITION_INVALID`

---

### `POST /receiving-orders/{id}/close`

Close the receiving order. Remaining undelivered lines are marked as short-shipped.

- **Scope:** `wms:receiving`
- **Required headers:** `Idempotency-Key`, `X-Correlation-Id`

**Response `200`:** Updated order with `status: CLOSED` and a `discrepancySummary`.

---

### `GET /receiving-orders/{id}/discrepancies`

List all discrepancies (over-receipts, under-receipts, condition issues) for the order.

- **Scope:** `wms:read`

**Response `200`:** Array of discrepancy records with `asnLineId`, `type`, `expectedQty`, `receivedQty`, `delta`, `resolutionStatus`.

---

## Putaway Tasks API

Base path: `/api/v1/put-away-tasks`

### `GET /put-away-tasks`

List putaway tasks with filters.

- **Scope:** `wms:read`
- **Query params:** `filter[warehouseId]`, `filter[status]` (`PENDING`, `ASSIGNED`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`), `filter[assignedTo]`, `sort=-createdAt`, `cursor`, `limit`

---

### `POST /put-away-tasks/generate`

Trigger batch generation of putaway tasks from unplaced receipt records.

- **Scope:** `wms:receiving`
- **Required headers:** `Idempotency-Key`, `X-Correlation-Id`

**Request body:**

```json
{
  "warehouseId": "WH-001",
  "receivingOrderId": "RO-00100",
  "strategy": "NEAREST_EMPTY_BIN"
}
```

**Response `202`:**

```json
{
  "batchId": "PATBATCH-009",
  "tasksGenerated": 12,
  "status": "PENDING"
}
```

**Errors:** `DUPLICATE_GENERATION`, `RESOURCE_NOT_FOUND`

---

### `GET /put-away-tasks/{taskId}`

Get a single putaway task.

- **Scope:** `wms:read`

---

### `POST /put-away-tasks/{taskId}/assign`

Assign a putaway task to a specific operator.

- **Scope:** `wms:write`
- **Required headers:** `Idempotency-Key`, `X-Correlation-Id`

**Request body:**

```json
{ "assignedTo": "usr_01HX9Z2KPQR4T5VWXY3B" }
```

**Response `200`:** Updated task with `status: ASSIGNED`.

---

### `POST /put-away-tasks/{taskId}/confirm`

Confirm physical putaway completion.

- **Scope:** `wms:receiving`
- **Required headers:** `Idempotency-Key`, `X-Correlation-Id`

**Request body:**

```json
{
  "confirmedBinId": "BIN-A-03-07",
  "deviceTimestamp": "2025-06-15T10:45:00Z"
}
```

**Response `200`:** Task `status: COMPLETED`; inventory record updated to `AVAILABLE`.

**Errors:** `BIN_CAPACITY_EXCEEDED`, `STATE_TRANSITION_INVALID`

---

### `POST /put-away-tasks/{taskId}/override-bin`

Override the system-suggested bin with a manually selected bin. Requires `wms:admin`.

- **Scope:** `wms:admin`
- **Required headers:** `Idempotency-Key`, `X-Correlation-Id`

**Request body:**

```json
{
  "overrideBinId": "BIN-B-10-02",
  "reason": "ORIGINAL_BIN_BLOCKED",
  "approverId": "usr_manager_001"
}
```

**Response `200`:** Updated task with new `suggestedBinId`.

---

## Wave Jobs API

Base path: `/api/v1/wave-jobs`

### `GET /wave-jobs`

List wave jobs.

- **Scope:** `wms:read`
- **Query params:** `filter[warehouseId]`, `filter[status]` (`DRAFT`, `RELEASED`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`), `filter[createdAt][gte]`, `sort=-createdAt`, `cursor`, `limit`

---

### `POST /wave-jobs`

Create a new wave job by selecting eligible shipment orders.

- **Scope:** `wms:write`
- **Required headers:** `Idempotency-Key`, `X-Correlation-Id`

**Request body:**

```json
{
  "warehouseId": "WH-001",
  "shipmentOrderIds": ["SO-001", "SO-002", "SO-003"],
  "waveType": "BATCH_PICK",
  "priority": "HIGH",
  "notes": "Priority wave for SLA orders due today"
}
```

**Response `202`:**

```json
{
  "waveId": "WAVE-00088",
  "status": "DRAFT",
  "shipmentOrderCount": 3,
  "totalPickLines": 47,
  "estimatedPickTime": "PT45M",
  "createdAt": "2025-06-10T07:00:00Z"
}
```

**Errors:** `INSUFFICIENT_ALLOCATABLE_STOCK`

---

### `GET /wave-jobs/{waveId}`

Get wave details including allocation summary.

- **Scope:** `wms:read`

---

### `POST /wave-jobs/{waveId}/release`

Release the wave, freezing allocations and generating pick lists.

- **Scope:** `wms:write`
- **Required headers:** `Idempotency-Key`, `X-Correlation-Id`

**Response `200`:** Wave `status: RELEASED`; returns `pickListIds[]`.

**Errors:** `WAVE_ALREADY_RELEASED`, `INSUFFICIENT_ALLOCATABLE_STOCK`

---

### `POST /wave-jobs/{waveId}/cancel`

Cancel a wave in `DRAFT` status. Releases all reservations.

- **Scope:** `wms:write`
- **Required headers:** `Idempotency-Key`, `X-Correlation-Id`

**Response `200`:** Wave `status: CANCELLED`.

**Errors:** `STATE_TRANSITION_INVALID` (cannot cancel released wave)

---

### `GET /wave-jobs/{waveId}/pick-lists`

List all pick lists generated for a wave.

- **Scope:** `wms:read`

**Response `200`:** Array of pick list summary objects.

---

## Pick Lists API

Base path: `/api/v1/pick-lists`

### `GET /pick-lists`

List pick lists.

- **Scope:** `wms:read`
- **Query params:** `filter[warehouseId]`, `filter[waveId]`, `filter[status]`, `filter[assignedTo]`, `sort`, `cursor`, `limit`

---

### `GET /pick-lists/{pickListId}`

Get pick list with all lines.

- **Scope:** `wms:read`

**Response `200`:**

```json
{
  "id": "PL-00201",
  "waveId": "WAVE-00088",
  "status": "ASSIGNED",
  "assignedTo": "usr_01HX9Z2KPQR4T5VWXY3B",
  "lines": [
    {
      "lineId": "PLL-001",
      "skuId": "SKU-0001",
      "binId": "BIN-A-01-01",
      "lotNumber": "LOT-2025-01",
      "requestedQty": 10,
      "pickedQty": null,
      "status": "PENDING"
    }
  ]
}
```

---

### `POST /pick-lists/{pickListId}/assign`

Assign a pick list to an operator.

- **Scope:** `wms:write`
- **Required headers:** `Idempotency-Key`, `X-Correlation-Id`

**Request body:** `{ "assignedTo": "usr_picker_007" }`

**Response `200`:** Pick list `status: ASSIGNED`.

---

### `POST /pick-lists/{pickListId}/lines/{lineId}/confirm`

Confirm the pick of a single line.

- **Scope:** `wms:picking`
- **Required headers:** `Idempotency-Key`, `X-Correlation-Id`

**Request body:**

```json
{
  "reservationId": "RSV-9922",
  "pickedQty": 10,
  "actualBinId": "BIN-A-01-01",
  "deviceTimestamp": "2025-06-10T08:55:00Z"
}
```

**Response `200`:**

```json
{
  "lineId": "PLL-001",
  "status": "COMPLETED",
  "pickedQty": 10,
  "inventoryDelta": -10,
  "newOnHand": 70
}
```

**Errors:** `RESERVATION_MISMATCH`, `STOCK_BELOW_ZERO`

---

### `POST /pick-lists/{pickListId}/lines/{lineId}/short-pick`

Report that a line cannot be fully picked (shortage).

- **Scope:** `wms:picking`
- **Required headers:** `Idempotency-Key`, `X-Correlation-Id`

**Request body:**

```json
{
  "pickedQty": 7,
  "shortQty": 3,
  "reasonCode": "BIN_EMPTY",
  "deviceTimestamp": "2025-06-10T09:05:00Z"
}
```

**Response `200`:** Line `status: SHORT_PICKED`; a replenishment or backorder task may be auto-generated.

---

### `POST /pick-lists/{pickListId}/complete`

Mark the entire pick list as complete.

- **Scope:** `wms:picking`
- **Required headers:** `Idempotency-Key`, `X-Correlation-Id`

**Response `200`:** Pick list `status: COMPLETED`. If all lines of the wave are complete, wave transitions to `COMPLETED`.

**Errors:** `STATE_TRANSITION_INVALID` (open lines remain)

---

## Shipment Orders API

Base path: `/api/v1/shipment-orders`

### `GET /shipment-orders`

List shipment orders.

- **Scope:** `wms:read`
- **Query params:** `filter[warehouseId]`, `filter[status]` (`PENDING`, `ALLOCATED`, `WAVED`, `PICKING`, `PACKING`, `READY_TO_SHIP`, `SHIPPED`, `CANCELLED`), `filter[customerId]`, `filter[carrierId]`, `filter[requiredShipDateFrom]`, `sort=-requiredShipDate`, `cursor`, `limit`

---

### `POST /shipment-orders`

Create a new outbound shipment order.

- **Scope:** `wms:write`
- **Required headers:** `Idempotency-Key`, `X-Correlation-Id`

**Request body:**

```json
{
  "warehouseId": "WH-001",
  "externalOrderId": "ORD-20250610-9988",
  "customerId": "CUST-0055",
  "requiredShipDate": "2025-06-12",
  "carrierId": "CARRIER-UPS",
  "serviceLevel": "UPS_GROUND",
  "shippingAddress": {
    "name": "Jane Doe",
    "street": "123 Main St",
    "city": "Nashville",
    "state": "TN",
    "zip": "37201",
    "country": "US"
  },
  "lines": [
    { "skuId": "SKU-0001", "orderedQty": 5 },
    { "skuId": "SKU-0002", "orderedQty": 2 }
  ]
}
```

**Response `201`:** Shipment order with `id`, `status: PENDING`, and line details.

---

### `GET /shipment-orders/{id}`

Get full shipment order including lines, allocation status, and shipment references.

- **Scope:** `wms:read`

---

### `PATCH /shipment-orders/{id}/cancel`

Cancel a shipment order that has not yet been shipped.

- **Scope:** `wms:write`
- **Required headers:** `Idempotency-Key`, `X-Correlation-Id`

**Request body:** `{ "reason": "CUSTOMER_REQUESTED_CANCELLATION" }`

**Response `200`:** Order `status: CANCELLED`; all reservations released.

**Errors:** `STATE_TRANSITION_INVALID` (cannot cancel after shipment confirmed)

---

## Packing Lists API

Base path: `/api/v1/packing-lists`

### `GET /packing-lists/{shipmentOrderId}`

Get the current packing state for a shipment order.

- **Scope:** `wms:read`

---

### `POST /packing-lists/{shipmentOrderId}/containers`

Create a new packing container (box/carton) for the shipment.

- **Scope:** `wms:shipping`
- **Required headers:** `Idempotency-Key`, `X-Correlation-Id`

**Request body:**

```json
{
  "containerType": "BOX_MEDIUM",
  "weight": 0,
  "dimensions": { "lengthCm": 40, "widthCm": 30, "heightCm": 25 }
}
```

**Response `201`:** `{ "containerId": "CTN-0099", "status": "OPEN" }`

---

### `POST /packing-lists/{shipmentOrderId}/containers/{containerId}/items`

Add a picked item to a container.

- **Scope:** `wms:shipping`
- **Required headers:** `Idempotency-Key`, `X-Correlation-Id`

**Request body:**

```json
{
  "skuId": "SKU-0001",
  "qty": 5,
  "lotNumber": "LOT-2025-01",
  "pickListLineId": "PLL-001"
}
```

**Response `200`:** Updated container with packed item list.

---

### `POST /packing-lists/{shipmentOrderId}/close`

Close all containers and finalize the packing list.

- **Scope:** `wms:shipping`
- **Required headers:** `Idempotency-Key`, `X-Correlation-Id`

**Request body:**

```json
{
  "verifiedBy": "usr_packer_003",
  "deviceTimestamp": "2025-06-10T11:30:00Z"
}
```

**Response `200`:**

```json
{
  "packingListId": "PK-00500",
  "shipmentOrderId": "SO-001",
  "status": "CLOSED",
  "containers": [
    { "containerId": "CTN-0099", "totalItems": 7, "totalWeight": 3.2 }
  ],
  "reconciliationStatus": "MATCHED",
  "closedAt": "2025-06-10T11:30:05Z"
}
```

**Errors:** `PACK_RECONCILIATION_FAILED`

---

## Shipments API

Base path: `/api/v1/shipments`

### `GET /shipments`

List shipments.

- **Scope:** `wms:read`
- **Query params:** `filter[warehouseId]`, `filter[carrierId]`, `filter[status]`, `filter[dispatchedAt][gte]`, `sort=-dispatchedAt`, `cursor`, `limit`

---

### `GET /shipments/{shipmentId}`

Get full shipment record including carrier details and tracking info.

- **Scope:** `wms:read`

---

### `POST /shipments/{shipmentId}/confirm`

Confirm physical handoff to carrier.

- **Scope:** `wms:shipping`
- **Required headers:** `Idempotency-Key`, `X-Correlation-Id`

**Request body:**

```json
{
  "driverName": "John Smith",
  "proNumber": "PRO-123456",
  "signedBy": "usr_dock_001",
  "deviceTimestamp": "2025-06-10T14:00:00Z"
}
```

**Response `200`:** Shipment `status: DISPATCHED`; inventory debited.

**Errors:** `CARRIER_CONFIRMATION_UNAVAILABLE`

---

### `GET /shipments/{shipmentId}/labels`

Retrieve carrier-generated shipping label(s) as base64-encoded PDF.

- **Scope:** `wms:shipping`

**Response `200`:**

```json
{
  "labels": [
    {
      "containerId": "CTN-0099",
      "trackingNumber": "1Z999AA10123456784",
      "format": "PDF",
      "encodedLabel": "JVBERi0xLjQK..."
    }
  ]
}
```

---

### `GET /shipments/{shipmentId}/tracking`

Get latest carrier tracking status.

- **Scope:** `wms:read`

**Response `200`:** Tracking events array with `status`, `location`, `timestamp`, `description`.

---

## Cycle Counts API

Base path: `/api/v1/cycle-counts`

### `GET /cycle-counts`

List cycle count sessions.

- **Scope:** `wms:read`
- **Query params:** `filter[warehouseId]`, `filter[status]` (`DRAFT`, `ASSIGNED`, `IN_PROGRESS`, `PENDING_APPROVAL`, `APPROVED`, `CLOSED`), `filter[zoneId]`, `sort=-scheduledDate`, `cursor`, `limit`

---

### `POST /cycle-counts`

Create a new cycle count session.

- **Scope:** `wms:counting`
- **Required headers:** `Idempotency-Key`, `X-Correlation-Id`

**Request body:**

```json
{
  "warehouseId": "WH-001",
  "zoneIds": ["ZN-001", "ZN-002"],
  "scheduledDate": "2025-06-20",
  "countType": "BLIND",
  "notes": "Monthly cycle count for Zones A & B"
}
```

**Response `201`:** Count session with generated lines (one per bin/SKU combination in scope).

---

### `GET /cycle-counts/{countId}`

Get cycle count with all lines.

- **Scope:** `wms:read`

---

### `POST /cycle-counts/{countId}/assign`

Assign the count session to one or more counters.

- **Scope:** `wms:write`
- **Required headers:** `Idempotency-Key`, `X-Correlation-Id`

**Request body:** `{ "assignedTo": ["usr_counter_001", "usr_counter_002"] }`

---

### `POST /cycle-counts/{countId}/lines/{lineId}/submit`

Submit a counted quantity for one line.

- **Scope:** `wms:counting`
- **Required headers:** `Idempotency-Key`, `X-Correlation-Id`

**Request body:**

```json
{
  "countedQty": 78,
  "countedBy": "usr_counter_001",
  "deviceTimestamp": "2025-06-20T09:15:00Z"
}
```

**Response `200`:**

```json
{
  "lineId": "CCL-0055",
  "systemQty": 80,
  "countedQty": 78,
  "variance": -2,
  "variancePct": -2.5,
  "status": "SUBMITTED",
  "requiresRecount": false
}
```

---

### `POST /cycle-counts/{countId}/lines/{lineId}/recount`

Request a recount for a line that has an unacceptable variance.

- **Scope:** `wms:counting`
- **Required headers:** `Idempotency-Key`, `X-Correlation-Id`

**Request body:** `{ "reason": "VARIANCE_EXCEEDS_THRESHOLD" }`

**Response `200`:** Line `status: RECOUNT_REQUESTED`.

---

### `POST /cycle-counts/{countId}/approve`

Approve cycle count results. Applies inventory adjustments for all accepted variances.

- **Scope:** `wms:admin`
- **Required headers:** `Idempotency-Key`, `X-Correlation-Id`

**Request body:**

```json
{
  "approvedBy": "usr_manager_001",
  "overrideThreshold": false,
  "notes": "All variances within acceptable range"
}
```

**Response `200`:** Count `status: APPROVED`; `adjustmentsApplied` count returned.

**Errors:** `CYCLE_COUNT_ALREADY_APPROVED`

---

### `POST /cycle-counts/{countId}/close`

Close the cycle count session.

- **Scope:** `wms:counting`
- **Required headers:** `Idempotency-Key`, `X-Correlation-Id`

**Response `200`:** Count `status: CLOSED`.

---

## Replenishment API

Base path: `/api/v1/replenishment`

### `GET /replenishment/tasks`

List pending and in-progress replenishment tasks.

- **Scope:** `wms:read`
- **Query params:** `filter[warehouseId]`, `filter[status]`, `filter[skuId]`, `filter[priority]`, `sort=-createdAt`, `cursor`, `limit`

---

### `POST /replenishment/tasks/trigger`

Manually trigger replenishment evaluation for a warehouse or specific SKUs.

- **Scope:** `wms:write`
- **Required headers:** `Idempotency-Key`, `X-Correlation-Id`

**Request body:**

```json
{
  "warehouseId": "WH-001",
  "skuIds": ["SKU-0001", "SKU-0003"],
  "strategy": "MIN_MAX"
}
```

**Response `202`:** `{ "tasksCreated": 3, "batchId": "RPL-BATCH-012" }`

---

### `GET /replenishment/tasks/{taskId}`

Get a single replenishment task.

- **Scope:** `wms:read`

**Response `200`:**

```json
{
  "taskId": "RPL-00088",
  "skuId": "SKU-0001",
  "fromBinId": "BIN-RESERVE-01",
  "toBinId": "BIN-A-01-01",
  "requestedQty": 50,
  "status": "PENDING",
  "triggeredBy": "AUTO_MIN_MAX",
  "createdAt": "2025-06-10T06:00:00Z"
}
```

---

### `POST /replenishment/tasks/{taskId}/confirm`

Confirm physical replenishment completion.

- **Scope:** `wms:write`
- **Required headers:** `Idempotency-Key`, `X-Correlation-Id`

**Request body:** `{ "confirmedQty": 50, "deviceTimestamp": "2025-06-10T06:45:00Z" }`

**Response `200`:** Task `status: COMPLETED`; pick bin ATP updated.

---

## Returns API

Base path: `/api/v1/returns`

### `GET /returns`

List return authorizations.

- **Scope:** `wms:read`
- **Query params:** `filter[warehouseId]`, `filter[status]` (`PENDING`, `RECEIVING`, `INSPECTING`, `DISPOSITIONED`, `CLOSED`), `filter[customerId]`, `sort=-createdAt`, `cursor`, `limit`

---

### `POST /returns`

Create a Return Merchandise Authorization (RMA).

- **Scope:** `wms:returns`
- **Required headers:** `Idempotency-Key`, `X-Correlation-Id`

**Request body:**

```json
{
  "warehouseId": "WH-001",
  "customerId": "CUST-0055",
  "originalShipmentId": "SHP-00300",
  "lines": [
    { "skuId": "SKU-0001", "expectedQty": 2, "reason": "DAMAGED_IN_TRANSIT" }
  ]
}
```

**Response `201`:** RMA with generated `returnId` and `rmaNumber`.

---

### `GET /returns/{returnId}`

Get full return record.

- **Scope:** `wms:read`

---

### `POST /returns/{returnId}/receive`

Record physical receipt of returned items.

- **Scope:** `wms:returns`
- **Required headers:** `Idempotency-Key`, `X-Correlation-Id`

**Request body:**

```json
{
  "lines": [
    {
      "returnLineId": "RTL-001",
      "receivedQty": 2,
      "receivingBinId": "BIN-RETURNS-01",
      "deviceTimestamp": "2025-06-12T10:00:00Z"
    }
  ]
}
```

**Response `200`:** Return `status: RECEIVING`.

---

### `POST /returns/{returnId}/inspect`

Record inspection outcome for each return line.

- **Scope:** `wms:returns`
- **Required headers:** `Idempotency-Key`, `X-Correlation-Id`

**Request body:**

```json
{
  "lines": [
    {
      "returnLineId": "RTL-001",
      "condition": "DAMAGED",
      "inspectionNotes": "Packaging torn; product intact",
      "inspectedBy": "usr_returns_001"
    }
  ]
}
```

**Response `200`:** Return `status: INSPECTING`.

---

### `POST /returns/{returnId}/disposition`

Apply disposition action to inspected return lines.

- **Scope:** `wms:returns`
- **Required headers:** `Idempotency-Key`, `X-Correlation-Id`

**Request body:**

```json
{
  "lines": [
    {
      "returnLineId": "RTL-001",
      "disposition": "RESTOCK",
      "targetBinId": "BIN-A-01-01",
      "lotNumber": "LOT-RETURN-001"
    }
  ]
}
```

| Disposition Code | Meaning |
|---|---|
| `RESTOCK` | Item is resalable; put back into available inventory |
| `QUARANTINE` | Needs further review; placed in quarantine bin |
| `SCRAP` | Write off; remove from inventory |
| `VENDOR_RETURN` | Return to supplier |
| `REFURBISH` | Route to refurbishment process |

**Response `200`:** Return `status: DISPOSITIONED`.

**Errors:** `RETURN_DISPOSITION_INVALID`, `BIN_CAPACITY_EXCEEDED`

---

## Carriers API

Base path: `/api/v1/carriers`

### `GET /carriers`

List configured carrier integrations.

- **Scope:** `wms:read`

**Response `200`:** Array of carrier objects with `id`, `name`, `accountNumber`, `status`, `supportedServices[]`.

---

### `GET /carriers/{carrierId}/service-levels`

List all available service levels for a carrier.

- **Scope:** `wms:read`

**Response `200`:**

```json
{
  "carrierId": "CARRIER-UPS",
  "serviceLevels": [
    { "code": "UPS_GROUND", "name": "UPS Ground", "maxDays": 5, "trackingSupported": true },
    { "code": "UPS_2DAY", "name": "UPS 2nd Day Air", "maxDays": 2, "trackingSupported": true }
  ]
}
```

---

### `POST /carriers/{carrierId}/rate-shop`

Request shipping rate quotes for a shipment.

- **Scope:** `wms:shipping`
- **Required headers:** `Idempotency-Key`, `X-Correlation-Id`

**Request body:**

```json
{
  "fromZip": "38118",
  "toZip": "37201",
  "packages": [
    { "weightKg": 3.2, "lengthCm": 40, "widthCm": 30, "heightCm": 25 }
  ],
  "requiredByDate": "2025-06-12"
}
```

**Response `200`:** Array of rate quotes with `serviceLevel`, `estimatedCost`, `currency`, `estimatedDeliveryDate`.

---

### `POST /carriers/{carrierId}/labels`

Request label generation from carrier.

- **Scope:** `wms:shipping`
- **Required headers:** `Idempotency-Key`, `X-Correlation-Id`

**Request body:** Shipment details including service level, package dimensions, recipient address.

**Response `200`:** Array of label objects with `trackingNumber`, `encodedLabel` (base64 PDF), `labelFormat`.

**Errors:** `LABEL_GENERATION_FAILED`

---

## Reports API

Base path: `/api/v1/reports`

All report endpoints accept `filter[warehouseId]`, `filter[dateFrom]`, `filter[dateTo]`, and `filter[zoneId]` query parameters unless noted otherwise.

### `GET /reports/inventory-accuracy`

Inventory accuracy derived from cycle count results.

- **Scope:** `wms:reports`

**Response `200`:**

```json
{
  "period": { "from": "2025-06-01", "to": "2025-06-30" },
  "warehouseId": "WH-001",
  "locationsAudited": 840,
  "accurateLocations": 820,
  "accuracyPct": 97.6,
  "totalVarianceUnits": 42,
  "totalVarianceValue": 189.50
}
```

---

### `GET /reports/receiving-productivity`

Units received per hour by operator and shift.

- **Scope:** `wms:reports`

**Response `200`:** Array of rows with `date`, `operatorId`, `shift`, `unitsReceived`, `hoursWorked`, `unitsPerHour`.

---

### `GET /reports/pick-rate`

Pick lines and units per hour by operator and wave.

- **Scope:** `wms:reports`

**Response `200`:** Array of rows with `date`, `operatorId`, `waveId`, `linesCompleted`, `unitsCompleted`, `shortPicks`, `hoursWorked`, `linesPerHour`.

---

### `GET /reports/shipment-on-time`

On-time shipment rate by carrier and service level.

- **Scope:** `wms:reports`

**Response `200`:**

```json
{
  "period": { "from": "2025-06-01", "to": "2025-06-30" },
  "rows": [
    {
      "carrierId": "CARRIER-UPS",
      "serviceLevel": "UPS_GROUND",
      "totalShipments": 1200,
      "onTimeShipments": 1176,
      "onTimePct": 98.0,
      "lateShipments": 24
    }
  ]
}
```

---

### `GET /reports/cycle-count-variance`

Variance report showing SKUs and bins with the highest inventory discrepancy.

- **Scope:** `wms:reports`

**Response `200`:** Array of rows with `skuId`, `binId`, `systemQty`, `countedQty`, `variance`, `variancePct`, `varianceValue`, `countedAt`.

---

## Request/Response JSON Schemas

### 1. `POST /receiving-orders/{id}/receive`

**Full Request:**

```json
{
  "asnLineId": "ASNL-001",
  "receivedQty": 195,
  "lotNumber": "LOT-2025-06-A",
  "expiryDate": "2026-06-01",
  "serialNumbers": [],
  "condition": "GOOD",
  "receivingBinId": "BIN-RECV-01",
  "deviceTimestamp": "2025-06-15T09:30:00Z"
}
```

**Full Response `200`:**

```json
{
  "receiptId": "RCP-00444",
  "receivingOrderId": "RO-00100",
  "asnLineId": "ASNL-001",
  "skuId": "SKU-0001",
  "expectedQty": 200,
  "receivedQty": 195,
  "tolerancePct": 5.0,
  "toleranceStatus": "WITHIN_TOLERANCE",
  "lotNumber": "LOT-2025-06-A",
  "expiryDate": "2026-06-01",
  "condition": "GOOD",
  "receivingBinId": "BIN-RECV-01",
  "inventoryRecordId": "INV-00201",
  "putawayTaskId": "PAT-00310",
  "status": "RECEIVED",
  "receivedAt": "2025-06-15T09:30:12Z",
  "receivedBy": "usr_receiver_002"
}
```

---

### 2. `POST /wave-jobs` (Create Wave)

**Full Request:**

```json
{
  "warehouseId": "WH-001",
  "shipmentOrderIds": ["SO-001", "SO-002", "SO-003"],
  "waveType": "BATCH_PICK",
  "priority": "HIGH",
  "pickZones": ["ZN-001", "ZN-002"],
  "maxPickLines": 100,
  "notes": "SLA wave — all orders ship by 14:00"
}
```

**Full Response `202`:**

```json
{
  "waveId": "WAVE-00088",
  "warehouseId": "WH-001",
  "status": "DRAFT",
  "waveType": "BATCH_PICK",
  "priority": "HIGH",
  "shipmentOrderCount": 3,
  "totalPickLines": 47,
  "totalUnits": 312,
  "allocations": [
    { "skuId": "SKU-0001", "allocatedQty": 150, "reservationIds": ["RSV-9920", "RSV-9921"] },
    { "skuId": "SKU-0002", "allocatedQty": 162, "reservationIds": ["RSV-9922"] }
  ],
  "estimatedPickTime": "PT45M",
  "createdAt": "2025-06-10T07:00:00Z",
  "createdBy": "usr_planner_001"
}
```

---

### 3. `POST /pick-lists/{pickListId}/lines/{lineId}/confirm`

**Full Request:**

```json
{
  "reservationId": "RSV-9922",
  "pickedQty": 10,
  "actualBinId": "BIN-A-01-01",
  "lotNumber": "LOT-2025-01",
  "deviceTimestamp": "2025-06-10T08:55:00Z",
  "deviceId": "RF-GUN-007"
}
```

**Full Response `200`:**

```json
{
  "lineId": "PLL-001",
  "pickListId": "PL-00201",
  "skuId": "SKU-0001",
  "requestedQty": 10,
  "pickedQty": 10,
  "status": "COMPLETED",
  "inventoryDelta": -10,
  "newOnHand": 70,
  "newReserved": 30,
  "newAtp": 40,
  "confirmedAt": "2025-06-10T08:55:04Z",
  "confirmedBy": "usr_picker_007"
}
```

---

### 4. `POST /packing-lists/{shipmentOrderId}/close`

**Full Request:**

```json
{
  "verifiedBy": "usr_packer_003",
  "deviceTimestamp": "2025-06-10T11:30:00Z",
  "notes": "All items packed; ready for label print"
}
```

**Full Response `200`:**

```json
{
  "packingListId": "PK-00500",
  "shipmentOrderId": "SO-001",
  "status": "CLOSED",
  "containers": [
    {
      "containerId": "CTN-0099",
      "containerType": "BOX_MEDIUM",
      "totalItems": 7,
      "totalWeight": 3.2,
      "dimensions": { "lengthCm": 40, "widthCm": 30, "heightCm": 25 },
      "items": [
        { "skuId": "SKU-0001", "qty": 5, "lotNumber": "LOT-2025-01" },
        { "skuId": "SKU-0002", "qty": 2, "lotNumber": "LOT-2025-06-B" }
      ]
    }
  ],
  "reconciliationStatus": "MATCHED",
  "shipmentId": "SHP-00300",
  "closedAt": "2025-06-10T11:30:05Z",
  "closedBy": "usr_packer_003"
}
```

---

### 5. `POST /cycle-counts/{countId}/lines/{lineId}/submit`

**Full Request:**

```json
{
  "countedQty": 78,
  "countedBy": "usr_counter_001",
  "lotNumber": "LOT-2025-01",
  "serialNumbers": [],
  "deviceTimestamp": "2025-06-20T09:15:00Z",
  "deviceId": "RF-GUN-012",
  "notes": "2 units appeared physically absent from bin"
}
```

**Full Response `200`:**

```json
{
  "lineId": "CCL-0055",
  "cycleCountId": "CC-00010",
  "binId": "BIN-A-01-01",
  "skuId": "SKU-0001",
  "lotNumber": "LOT-2025-01",
  "systemQty": 80,
  "countedQty": 78,
  "variance": -2,
  "variancePct": -2.5,
  "varianceValue": -9.00,
  "status": "SUBMITTED",
  "requiresRecount": false,
  "submittedAt": "2025-06-20T09:15:10Z",
  "submittedBy": "usr_counter_001"
}
```

---

## Pagination and Filtering

### Cursor-Based Pagination Details

Cursors are opaque, base64-encoded JSON objects that encode the sort key(s) of the last seen record. They are valid for **1 hour** from generation. Using an expired cursor returns `400 INVALID_CURSOR`.

**Example multi-page traversal:**

```
# Page 1
GET /api/v1/inventory?limit=50
→ { "hasNextPage": true, "nextCursor": "eyJpZCI6IklOVi0wMDA1MCJ9" }

# Page 2
GET /api/v1/inventory?limit=50&cursor=eyJpZCI6IklOVi0wMDA1MCJ9
→ { "hasNextPage": true, "nextCursor": "eyJpZCI6IklOVi0wMDEwMCJ9" }

# Page 3
GET /api/v1/inventory?limit=50&cursor=eyJpZCI6IklOVi0wMDEwMCJ9
→ { "hasNextPage": false, "nextCursor": null }
```

### Filtering Operators Reference

| Operator | URL Syntax | SQL Equivalent | Example |
|---|---|---|---|
| `eq` | `filter[status]=ACTIVE` | `status = 'ACTIVE'` | Exact match |
| `neq` | `filter[status][neq]=CLOSED` | `status != 'CLOSED'` | Exclusion |
| `gt` | `filter[qty][gt]=0` | `qty > 0` | Positive stock only |
| `gte` | `filter[createdAt][gte]=2025-01-01` | `created_at >= '2025-01-01'` | Date range start |
| `lt` | `filter[qty][lt]=10` | `qty < 10` | Low stock |
| `lte` | `filter[updatedAt][lte]=2025-06-30` | `updated_at <= '2025-06-30'` | Date range end |
| `in` | `filter[warehouseId][in]=WH-001,WH-002` | `warehouse_id IN (...)` | Multi-warehouse |
| `contains` | `filter[skuCode][contains]=WIDGET` | `sku_code ILIKE '%WIDGET%'` | Substring search |

### Combined Filter Example

```
GET /api/v1/inventory
  ?filter[warehouseId]=WH-001
  &filter[status]=AVAILABLE
  &filter[qty][gt]=0
  &filter[expiryDate][lte]=2025-12-31
  &sort=expiryDate
  &limit=100
```

---

## Rate Limiting

### Response Headers

| Header | Type | Description |
|---|---|---|
| `X-RateLimit-Limit` | integer | Total requests allowed in window |
| `X-RateLimit-Remaining` | integer | Requests left in current window |
| `X-RateLimit-Reset` | unix timestamp | When the window resets |
| `Retry-After` | integer (seconds) | Populated only on `429` responses |

### Limits Table

| Endpoint Group | Requests/Min | Burst | Window |
|---|---|---|---|
| `GET /warehouses*` | 300 | 500 | 60 s |
| `POST/PUT/PATCH /warehouses*` | 60 | 100 | 60 s |
| `GET /inventory*` | 300 | 500 | 60 s |
| `POST /inventory/adjustments` | 60 | 100 | 60 s |
| `GET /receiving-orders*` | 200 | 300 | 60 s |
| `POST /receiving-orders/*/receive` | 120 | 200 | 60 s |
| `POST /wave-jobs*` | 30 | 60 | 60 s |
| `POST /pick-lists/*/lines/*/confirm` | 300 | 500 | 60 s |
| `POST /packing-lists/*/close` | 60 | 100 | 60 s |
| `POST /shipments/*/confirm` | 60 | 100 | 60 s |
| `POST /cycle-counts/*/lines/*/submit` | 200 | 400 | 60 s |
| `GET /reports/*` | 30 | 50 | 60 s |
| `POST /carriers/*/labels` | 60 | 100 | 60 s |
| Machine tokens (service-to-service) | 1 200 | 2 000 | 60 s |

---

## Webhook Events

Webhooks deliver real-time event notifications to registered HTTPS endpoints. Each delivery includes:

- `X-WMS-Event` header: event type
- `X-WMS-Delivery-Id`: unique delivery UUID
- `X-WMS-Signature`: HMAC-SHA256 of payload using the shared secret

Failed deliveries are retried with exponential backoff up to **10 attempts** over 24 hours.

---

### Event: `receiving.order.completed`

Fired when all lines of a receiving order have been receipted and the order is closed.

```json
{
  "event": "receiving.order.completed",
  "deliveryId": "del_001abc",
  "timestamp": "2025-06-15T10:00:00Z",
  "warehouseId": "WH-001",
  "payload": {
    "receivingOrderId": "RO-00100",
    "purchaseOrderId": "PO-20250601-001",
    "supplierId": "SUP-012",
    "closedAt": "2025-06-15T09:58:00Z",
    "totalLinesReceived": 2,
    "discrepancyCount": 1,
    "putawayTasksGenerated": 12
  }
}
```

---

### Event: `inventory.adjusted`

Fired after any inventory adjustment (manual, cycle count approval, or return disposition).

```json
{
  "event": "inventory.adjusted",
  "deliveryId": "del_002def",
  "timestamp": "2025-06-10T14:22:10Z",
  "warehouseId": "WH-001",
  "payload": {
    "adjustmentId": "ADJ-00099",
    "skuId": "SKU-0001",
    "binId": "BIN-A-01-01",
    "lotNumber": "LOT-2025-01",
    "previousQty": 80,
    "newQty": 75,
    "deltaQty": -5,
    "reasonCode": "DAMAGED_IN_STORAGE",
    "adjustedBy": "usr_supervisor_001",
    "correlationId": "c3d4e5f6-0000-4abc-9def-aabbccdd0011"
  }
}
```

---

### Event: `wave.released`

Fired when a wave transitions from `DRAFT` to `RELEASED` and pick lists are generated.

```json
{
  "event": "wave.released",
  "deliveryId": "del_003ghi",
  "timestamp": "2025-06-10T07:05:00Z",
  "warehouseId": "WH-001",
  "payload": {
    "waveId": "WAVE-00088",
    "releasedAt": "2025-06-10T07:05:00Z",
    "releasedBy": "usr_planner_001",
    "shipmentOrderCount": 3,
    "pickListIds": ["PL-00201", "PL-00202"],
    "totalPickLines": 47,
    "totalUnits": 312
  }
}
```

---

### Event: `pick.completed`

Fired when a pick list is fully completed.

```json
{
  "event": "pick.completed",
  "deliveryId": "del_004jkl",
  "timestamp": "2025-06-10T09:30:00Z",
  "warehouseId": "WH-001",
  "payload": {
    "pickListId": "PL-00201",
    "waveId": "WAVE-00088",
    "completedAt": "2025-06-10T09:30:00Z",
    "completedBy": "usr_picker_007",
    "linesCompleted": 24,
    "linesShortPicked": 1,
    "unitsCompleted": 158,
    "unitsShortPicked": 3
  }
}
```

---

### Event: `shipment.dispatched`

Fired when a shipment is confirmed as handed off to the carrier.

```json
{
  "event": "shipment.dispatched",
  "deliveryId": "del_005mno",
  "timestamp": "2025-06-10T14:01:00Z",
  "warehouseId": "WH-001",
  "payload": {
    "shipmentId": "SHP-00300",
    "shipmentOrderId": "SO-001",
    "carrierId": "CARRIER-UPS",
    "serviceLevel": "UPS_GROUND",
    "trackingNumbers": ["1Z999AA10123456784"],
    "totalWeight": 3.2,
    "dispatchedAt": "2025-06-10T14:00:45Z",
    "estimatedDeliveryDate": "2025-06-15"
  }
}
```

---

### Event: `cycle_count.approved`

Fired when a cycle count session is approved and inventory adjustments are applied.

```json
{
  "event": "cycle_count.approved",
  "deliveryId": "del_006pqr",
  "timestamp": "2025-06-20T16:00:00Z",
  "warehouseId": "WH-001",
  "payload": {
    "cycleCountId": "CC-00010",
    "approvedAt": "2025-06-20T16:00:00Z",
    "approvedBy": "usr_manager_001",
    "zoneIds": ["ZN-001", "ZN-002"],
    "linesAudited": 420,
    "linesWithVariance": 8,
    "adjustmentsApplied": 8,
    "totalVarianceUnits": 18,
    "totalVarianceValue": 81.00,
    "inventoryAccuracyPct": 98.1
  }
}
```

---

### Event: `return.received`

Fired when physical return items are received at the warehouse.

```json
{
  "event": "return.received",
  "deliveryId": "del_007stu",
  "timestamp": "2025-06-12T10:05:00Z",
  "warehouseId": "WH-001",
  "payload": {
    "returnId": "RET-00022",
    "rmaNumber": "RMA-20250610-001",
    "customerId": "CUST-0055",
    "originalShipmentId": "SHP-00280",
    "linesReceived": 1,
    "totalUnitsReceived": 2,
    "receivedAt": "2025-06-12T10:04:55Z",
    "receivedBy": "usr_returns_001"
  }
}
```

---

*Last updated: 2025-06-10 | Version: v1.0.0*
