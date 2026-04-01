# API Design — Restaurant Management System

## API Style

This API follows REST principles with JSON as the primary data exchange format, served exclusively over HTTPS.
All communication uses Content-Type: application/json and Accept: application/json headers.

- **RESTful JSON over HTTPS**: All endpoints communicate via HTTPS. Plaintext HTTP is rejected with a 301 redirect.
- **Resource-oriented URL design**: URLs represent nouns (resources), not verbs or actions.
- **Plural nouns and kebab-case**: Collections use plural nouns (e.g., `/orders`, `/menu-items`). Multi-word segments use kebab-case.
- **HTTP verbs for semantics**: GET retrieves, POST creates, PATCH partially updates, PUT fully replaces, DELETE removes.
- **Branch-aware authorization**: Every endpoint that touches branch data validates the `branchId` claim in the JWT against the requested resource. Cross-branch access is rejected with 403.
- **Idempotency keys**: State-mutating operations (POST, PATCH, DELETE) SHOULD include an `X-Idempotency-Key` header. The server caches the response for 24 hours and returns the same response for duplicate keys, preventing double submissions.
- **Cursor-based pagination**: Large collections use opaque cursor tokens (`?cursor=<token>&limit=50`) rather than offset pagination to ensure consistency on live data.
- **Structured error responses**: Every error returns a machine-readable `errorCode`, human-readable `message`, `correlationId`, and optional `details` object.
- **API versioning via URL prefix**: All endpoints are prefixed with `/api/v1/`. Breaking changes increment the version (`/api/v2/`).
- **Timestamps in ISO 8601 UTC**: All datetime fields are returned as `2024-03-15T18:30:00Z`.
- **Monetary values as decimals**: All currency values are represented as decimal numbers (e.g., `28.50`), never as integers or strings.
- **Partial updates via PATCH**: PATCH accepts a subset of fields. Only provided fields are updated; omitted fields are unchanged.
- **Soft deletes**: Resources are never hard-deleted. A `deletedAt` timestamp and `status: "archived"` are set instead.
- **Audit trail**: Every mutating request is logged with `actorId`, `branchId`, `ipAddress`, `userAgent`, and `correlationId` for compliance and troubleshooting.
- **Request size limits**: Request bodies are limited to 1 MB. Larger payloads (e.g., bulk imports) use a separate multipart upload flow.

---

## Authentication and Authorization

All API requests must carry a valid JWT access token in the `Authorization` header using the Bearer scheme:

```
Authorization: Bearer <access_token>
```

### Token Lifecycle

- **Access token expiry**: 15 minutes. Short-lived to reduce exposure if intercepted.
- **Refresh token expiry**: 7 days. Stored securely (HttpOnly cookie or secure storage). Used to obtain a new access token pair via `POST /api/v1/auth/refresh`.
- **Token revocation**: Tokens can be revoked server-side on logout, password change, or staff deactivation. Revoked tokens are maintained in a deny-list for their remaining TTL.
- **PIN-based quick auth**: POS terminals use a 4–6 digit PIN to authenticate via `POST /api/v1/auth/pin-session`. Returns a short-lived session token (30 minutes) scoped to the specific terminal and branch.

### Roles

| Role | Description |
|------|-------------|
| `super_admin` | Platform-wide access; can create/manage restaurants |
| `restaurant_admin` | Full access within a restaurant; cross-branch visibility |
| `branch_manager` | Full access within their assigned branch |
| `waiter` | Table service operations; own orders only |
| `cashier` | Billing and payment operations at a branch |
| `chef` | Kitchen ticket reads and status updates |
| `host` | Reservation and table management only |
| `delivery_manager` | Delivery order management; delivery partner integrations |
| `inventory_manager` | Inventory reads/writes; procurement management |

### Branch Scoping

Every JWT includes a `branchId` claim. Requests to endpoints under a different `branchId` are rejected with `403 FORBIDDEN`. `restaurant_admin` and `super_admin` roles carry a wildcard scope and may access any branch.

### API Keys

Webhook integrations and delivery partner callbacks use API keys passed via the `X-API-Key` header. API keys are scoped to a single restaurant and can be restricted to specific IP ranges and event types.

### Elevated Operations

Refunds, voids, exports, staff role changes, and discount overrides require `branch_manager`, `restaurant_admin`, or `super_admin` roles. Attempting these operations with a lower-privilege token returns `403 FORBIDDEN` with error code `INSUFFICIENT_ROLE`.

### Security Headers

All responses include:
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`

---

## API Versioning

The API uses URL-path versioning. The current stable version is **v1**, accessible via:

```
https://api.yourplatform.com/api/v1/
```

### Version Strategy

- **Non-breaking changes** (new optional fields, new endpoints) are added to the current version without incrementing.
- **Breaking changes** (field removals, renamed fields, changed semantics) are introduced in a new major version (`/api/v2/`).
- **Deprecation policy**: A version is deprecated with a minimum 6-month notice. Deprecated endpoints return a `Deprecation` response header with the sunset date: `Deprecation: Sat, 15 Sep 2025 00:00:00 GMT`.
- **Sunset header**: `Sunset: Sat, 15 Sep 2025 00:00:00 GMT` is included from the deprecation date onward.
- **Version coexistence**: Two major versions are supported simultaneously. After the sunset date, v1 returns `410 Gone`.
- **Client version pinning**: Clients SHOULD explicitly request a version. A versionless base URL is not supported.
- **Changelog**: Every version change is documented at `GET /api/changelog` with semantic versioning and change descriptions.

---

## Pagination

### Cursor Pagination (default for collections)

Cursor-based pagination ensures stable, consistent results even when data is inserted or deleted between pages.

**Request:**
```
GET /api/v1/branches/{branchId}/orders?cursor=eyJpZCI6Im9yZF8xMjMifQ&limit=50
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cursor` | string | — | Opaque cursor from previous response `meta.nextCursor`. Omit for the first page. |
| `limit` | integer | 50 | Number of records per page. Max 200. |

### Page-Based Pagination (reports only)

Report endpoints support offset-based pagination for predictable page navigation:

```
GET /api/v1/reports/daily-sales?page=2&per_page=25
```

### Response Envelope

All paginated responses wrap data in a standard envelope:

```json
{
  "data": [],
  "meta": {
    "cursor": "eyJpZCI6InRibF8wNSJ9",
    "nextCursor": "eyJpZCI6InRibF8xMCJ9",
    "limit": 50,
    "hasMore": true,
    "totalCount": 243
  },
  "links": {
    "self": "/api/v1/branches/br_abc/orders?limit=50&cursor=eyJpZCI6InRibF8wNSJ9",
    "next": "/api/v1/branches/br_abc/orders?limit=50&cursor=eyJpZCI6InRibF8xMCJ9"
  }
}
```

- `cursor`: The cursor representing the start of the current page.
- `nextCursor`: The cursor to use to fetch the next page. Absent when `hasMore` is `false`.
- `hasMore`: Boolean flag indicating whether more records exist beyond this page.
- `totalCount`: Total count of matching records. May be approximate (>10 000 returns `10000+`).

---

## Error Codes Reference

All errors follow the canonical error response shape (see **Canonical Error Response** section).

| Error Code | HTTP Status | Message | Retryable |
|------------|-------------|---------|-----------|
| `VALIDATION_ERROR` | 400 | One or more request fields failed validation. | No |
| `INVALID_JSON` | 400 | Request body is not valid JSON. | No |
| `MISSING_REQUIRED_FIELD` | 400 | A required field is absent from the request. | No |
| `UNAUTHORIZED` | 401 | Authentication credentials are missing or invalid. | No |
| `TOKEN_EXPIRED` | 401 | The access token has expired. Refresh and retry. | Yes |
| `PIN_LOCKED` | 401 | PIN entry locked after 5 failed attempts. Contact manager. | No |
| `FORBIDDEN` | 403 | You do not have permission to perform this action. | No |
| `INSUFFICIENT_ROLE` | 403 | Operation requires a higher privilege role. | No |
| `BRANCH_INACTIVE` | 403 | The target branch is inactive or suspended. | No |
| `RESOURCE_NOT_FOUND` | 404 | The requested resource does not exist. | No |
| `METHOD_NOT_ALLOWED` | 405 | HTTP method not supported for this endpoint. | No |
| `DUPLICATE_ORDER_NUMBER` | 409 | An order with this reference number already exists. | No |
| `ORDER_VERSION_CONFLICT` | 409 | Order was modified by another process. Fetch latest and retry. | Yes |
| `TABLE_NOT_AVAILABLE` | 409 | The table is occupied or reserved and cannot be seated. | No |
| `RESERVATION_CONFLICT` | 409 | A reservation already exists for this table/time slot. | No |
| `BILL_ALREADY_PAID` | 409 | This bill has already been settled. | No |
| `KITCHEN_TICKET_LOCKED` | 409 | Kitchen ticket is locked for editing once cooking has started. | No |
| `IDEMPOTENCY_KEY_REUSED` | 409 | The idempotency key was used for a different request payload. | No |
| `SHIFT_OVERLAP` | 409 | The new shift overlaps an existing scheduled shift for this staff member. | No |
| `MENU_ITEM_UNAVAILABLE` | 422 | This menu item is currently marked as unavailable. | No |
| `INSUFFICIENT_STOCK` | 422 | Not enough stock available to fulfil the requested quantity. | No |
| `PAYMENT_AMOUNT_MISMATCH` | 422 | Total payment amounts do not equal the bill total. | No |
| `ORDER_NOT_CANCELLABLE` | 422 | Order cannot be cancelled in its current state. | No |
| `DELIVERY_AREA_UNSUPPORTED` | 422 | The delivery address is outside the supported delivery zone. | No |
| `LOYALTY_POINTS_INSUFFICIENT` | 422 | Customer does not have enough loyalty points for this redemption. | No |
| `SPLIT_PAYMENT_EXCEEDS_TOTAL` | 422 | The sum of split amounts exceeds the bill total. | No |
| `PAYMENT_DECLINED` | 402 | Payment was declined by the payment processor. | No |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests. Slow down and retry after the reset time. | Yes |
| `INTERNAL_SERVER_ERROR` | 500 | An unexpected error occurred. Our team has been notified. | Yes |
| `SERVICE_UNAVAILABLE` | 503 | The service is temporarily unavailable. Please retry later. | Yes |

---

## Core Endpoints Overview

| API Group | Method | Endpoint | Auth Role | Description |
|-----------|--------|----------|-----------|-------------|
| Restaurants | POST | `/api/v1/restaurants` | super_admin | Create a new restaurant |
| Restaurants | GET | `/api/v1/restaurants/{restaurantId}` | restaurant_admin+ | Get restaurant details |
| Restaurants | GET | `/api/v1/restaurants/{restaurantId}/branches` | restaurant_admin+ | List branches |
| Branches | POST | `/api/v1/branches` | restaurant_admin+ | Create a new branch |
| Branches | GET | `/api/v1/branches/{branchId}` | branch_manager+ | Get branch details |
| Branches | PATCH | `/api/v1/branches/{branchId}` | branch_manager+ | Update branch settings |
| Tables | GET | `/api/v1/branches/{branchId}/tables` | host+ | List tables with live status |
| Tables | POST | `/api/v1/branches/{branchId}/tables` | branch_manager+ | Create a new table |
| Tables | GET | `/api/v1/tables/{tableId}` | host+ | Get table details |
| Tables | PATCH | `/api/v1/tables/{tableId}/status` | host+ | Update table status |
| Tables | POST | `/api/v1/tables/{tableId}/seat` | host, waiter | Seat a party |
| Tables | POST | `/api/v1/tables/{tableId}/release` | host, waiter | Release/clear table |
| Tables | POST | `/api/v1/tables/merge` | branch_manager+ | Merge tables |
| Tables | POST | `/api/v1/tables/split` | branch_manager+ | Split merged tables |
| Reservations | GET | `/api/v1/branches/{branchId}/reservations` | host+ | List reservations |
| Reservations | POST | `/api/v1/reservations` | host+ | Create reservation |
| Reservations | GET | `/api/v1/reservations/{reservationId}` | host+ | Get reservation |
| Reservations | PATCH | `/api/v1/reservations/{reservationId}` | host+ | Update reservation |
| Reservations | POST | `/api/v1/reservations/{reservationId}/confirm` | host+ | Confirm reservation |
| Reservations | POST | `/api/v1/reservations/{reservationId}/cancel` | host+ | Cancel reservation |
| Reservations | POST | `/api/v1/reservations/{reservationId}/arrive` | host, waiter | Mark guest arrived |
| Menus | GET | `/api/v1/branches/{branchId}/menus` | any | List menus |
| Menus | POST | `/api/v1/menus` | branch_manager+ | Create menu |
| Menus | GET | `/api/v1/menus/{menuId}` | any | Get menu with categories |
| Menus | GET | `/api/v1/menus/{menuId}/items` | any | List menu items |
| Menu Items | POST | `/api/v1/menu-items` | branch_manager+ | Create menu item |
| Menu Items | GET | `/api/v1/menu-items/{itemId}` | any | Get menu item details |
| Menu Items | PATCH | `/api/v1/menu-items/{itemId}` | branch_manager+ | Update menu item |
| Menu Items | PATCH | `/api/v1/menu-items/{itemId}/availability` | branch_manager, chef | Toggle availability |
| Orders | GET | `/api/v1/branches/{branchId}/orders` | waiter+ | List orders |
| Orders | POST | `/api/v1/orders` | waiter+ | Create draft order |
| Orders | GET | `/api/v1/orders/{orderId}` | waiter+ | Get order with items |
| Orders | PATCH | `/api/v1/orders/{orderId}/items` | waiter+ | Modify order items |
| Orders | POST | `/api/v1/orders/{orderId}/submit` | waiter+ | Submit to kitchen |
| Orders | POST | `/api/v1/orders/{orderId}/cancel` | branch_manager+ | Cancel order |
| Orders | PATCH | `/api/v1/orders/{orderId}/status` | branch_manager+ | Update order status |
| Kitchen | GET | `/api/v1/branches/{branchId}/kitchen/tickets` | chef, branch_manager | List open tickets |
| Kitchen | GET | `/api/v1/kitchen/stations/{stationId}/queue` | chef | Station KDS queue |
| Kitchen | PATCH | `/api/v1/kitchen/tickets/{ticketId}/status` | chef | Update ticket status |
| Kitchen | POST | `/api/v1/kitchen/tickets/{ticketId}/bump` | chef | Bump ticket |
| Kitchen | POST | `/api/v1/kitchen/tickets/{ticketId}/recall` | chef | Recall bumped ticket |
| Billing | POST | `/api/v1/orders/{orderId}/bill` | cashier, waiter | Generate bill |
| Billing | GET | `/api/v1/bills/{billId}` | cashier+ | Get bill details |
| Billing | POST | `/api/v1/bills/{billId}/splits` | cashier | Split bill |
| Billing | POST | `/api/v1/bills/{billId}/payments` | cashier | Record payment |
| Billing | POST | `/api/v1/bills/{billId}/void` | branch_manager+ | Void bill |
| Billing | POST | `/api/v1/bills/{billId}/refund` | branch_manager+ | Process refund |
| Billing | GET | `/api/v1/bills/{billId}/receipt` | cashier+ | Get receipt |
| Inventory | GET | `/api/v1/branches/{branchId}/ingredients` | inventory_manager+ | List ingredients |
| Inventory | POST | `/api/v1/ingredients` | inventory_manager+ | Create ingredient |
| Inventory | PATCH | `/api/v1/ingredients/{ingredientId}` | inventory_manager+ | Update ingredient |
| Inventory | POST | `/api/v1/inventory/adjustments` | inventory_manager+ | Record adjustment |
| Inventory | GET | `/api/v1/inventory/stock-movements` | inventory_manager+ | List stock movements |
| Inventory | GET | `/api/v1/inventory/low-stock-alerts` | inventory_manager+ | Low-stock alerts |
| Procurement | GET | `/api/v1/branches/{branchId}/purchase-orders` | inventory_manager+ | List POs |
| Procurement | POST | `/api/v1/purchase-orders` | inventory_manager+ | Create PO |
| Procurement | GET | `/api/v1/purchase-orders/{poId}` | inventory_manager+ | Get PO details |
| Procurement | POST | `/api/v1/purchase-orders/{poId}/submit` | inventory_manager+ | Submit PO to supplier |
| Procurement | POST | `/api/v1/purchase-orders/{poId}/receive` | inventory_manager+ | Record goods receipt |
| Procurement | POST | `/api/v1/purchase-orders/{poId}/cancel` | branch_manager+ | Cancel PO |
| Staff | GET | `/api/v1/branches/{branchId}/staff` | branch_manager+ | List staff |
| Staff | POST | `/api/v1/staff` | branch_manager+ | Create staff member |
| Staff | GET | `/api/v1/staff/{staffId}` | branch_manager+ | Get staff details |
| Staff | PATCH | `/api/v1/staff/{staffId}` | branch_manager+ | Update staff record |
| Shifts | POST | `/api/v1/shifts` | branch_manager+ | Create shift |
| Shifts | GET | `/api/v1/branches/{branchId}/shifts` | branch_manager+ | List branch shifts |
| Shifts | POST | `/api/v1/shifts/{shiftId}/clock-in` | any staff | Clock in |
| Shifts | POST | `/api/v1/shifts/{shiftId}/clock-out` | any staff | Clock out |
| Delivery | POST | `/api/v1/delivery-orders` | delivery_manager+ | Create delivery order |
| Delivery | GET | `/api/v1/delivery-orders/{deliveryOrderId}` | delivery_manager+ | Get delivery status |
| Delivery | PATCH | `/api/v1/delivery-orders/{deliveryOrderId}/status` | delivery_manager+ | Update delivery status |
| Delivery | POST | `/api/v1/delivery/webhook/{channelId}` | API key | Inbound platform webhook |
| Reports | GET | `/api/v1/reports/daily-sales` | branch_manager+ | Daily sales report |
| Reports | GET | `/api/v1/reports/branch-operations` | branch_manager+ | Operational KPIs |
| Reports | GET | `/api/v1/reports/menu-engineering` | branch_manager+ | Menu item performance |
| Reports | GET | `/api/v1/reports/inventory-valuation` | inventory_manager+ | Inventory valuation |
| Reports | GET | `/api/v1/reports/staff-performance` | branch_manager+ | Staff performance |

---

## Restaurants and Branches API

### POST /api/v1/restaurants — Create restaurant

**Description**: Creates a new top-level restaurant entity on the platform. A restaurant acts as the organizational parent for one or more branches. Only `super_admin` tokens may call this endpoint.

**Auth**: `super_admin`

**Request Body:**
```json
{
  "name": "The Golden Fork",
  "legalName": "Golden Fork Hospitality Pvt Ltd",
  "timezone": "Asia/Kolkata",
  "currencyCode": "INR",
  "contactEmail": "ops@goldenfork.com",
  "logoUrl": "https://cdn.example.com/logos/gf.png"
}
```

**Response:**
```json
{
  "data": {
    "restaurantId": "rst_7x9kp2",
    "name": "The Golden Fork",
    "legalName": "Golden Fork Hospitality Pvt Ltd",
    "timezone": "Asia/Kolkata",
    "currencyCode": "INR",
    "status": "active",
    "createdAt": "2024-03-15T10:00:00Z"
  }
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 201 | Restaurant created successfully |
| 400 | Validation error in request body |
| 401 | Missing or invalid token |
| 403 | Caller is not super_admin |
| 409 | Restaurant with this legal name already exists |

---

### GET /api/v1/restaurants/{restaurantId} — Get restaurant details

**Description**: Returns the full profile of a restaurant, including metadata and feature flags. `restaurant_admin` tokens scoped to this restaurant and `super_admin` tokens may access this endpoint.

**Auth**: `restaurant_admin`, `super_admin`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `restaurantId` | string | Unique restaurant identifier |

**Response:**
```json
{
  "data": {
    "restaurantId": "rst_7x9kp2",
    "name": "The Golden Fork",
    "timezone": "Asia/Kolkata",
    "currencyCode": "INR",
    "status": "active",
    "branchCount": 4,
    "features": {
      "loyaltyEnabled": true,
      "onlineOrderingEnabled": true,
      "kdsEnabled": true
    },
    "createdAt": "2024-03-15T10:00:00Z",
    "updatedAt": "2024-06-01T08:30:00Z"
  }
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 200 | Success |
| 401 | Unauthorized |
| 403 | Forbidden — token not scoped to this restaurant |
| 404 | Restaurant not found |

---

### GET /api/v1/restaurants/{restaurantId}/branches — List branches

**Description**: Returns all branches belonging to the restaurant. Results include basic branch info and operational status. Supports filtering by `status` query parameter.

**Auth**: `restaurant_admin`, `super_admin`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `restaurantId` | string | Unique restaurant identifier |

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by `active`, `inactive`, `suspended` |
| `limit` | integer | Page size (default 50) |
| `cursor` | string | Pagination cursor |

**Response:**
```json
{
  "data": [
    {
      "branchId": "br_abc123",
      "name": "MG Road",
      "city": "Bengaluru",
      "status": "active",
      "tableCount": 28,
      "phone": "+91-80-12345678"
    }
  ],
  "meta": { "cursor": null, "nextCursor": null, "limit": 50, "hasMore": false, "totalCount": 4 }
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 200 | Success |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Restaurant not found |

---

### POST /api/v1/branches — Create branch

**Description**: Creates a new branch under a restaurant. Includes physical address, operating hours, timezone overrides, and capacity settings. Returns the created branch with its assigned `branchId`.

**Auth**: `restaurant_admin`, `super_admin`

**Request Body:**
```json
{
  "restaurantId": "rst_7x9kp2",
  "name": "Koramangala",
  "address": {
    "line1": "47 5th Block",
    "city": "Bengaluru",
    "state": "Karnataka",
    "postalCode": "560034",
    "country": "IN"
  },
  "phone": "+91-80-98765432",
  "seatingCapacity": 60,
  "operatingHours": {
    "monday": { "open": "11:00", "close": "23:00" },
    "tuesday": { "open": "11:00", "close": "23:00" }
  }
}
```

**Response:**
```json
{
  "data": {
    "branchId": "br_km456",
    "restaurantId": "rst_7x9kp2",
    "name": "Koramangala",
    "status": "active",
    "seatingCapacity": 60,
    "createdAt": "2024-03-16T09:00:00Z"
  }
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 201 | Branch created successfully |
| 400 | Validation error |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Restaurant not found |

---

### GET /api/v1/branches/{branchId} — Get branch details

**Description**: Returns full branch details including address, operating hours, and feature flags. Any staff token scoped to this branch may read it.

**Auth**: `branch_manager`, `restaurant_admin`, `super_admin`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `branchId` | string | Unique branch identifier |

**Response:**
```json
{
  "data": {
    "branchId": "br_km456",
    "name": "Koramangala",
    "restaurantId": "rst_7x9kp2",
    "status": "active",
    "address": { "line1": "47 5th Block", "city": "Bengaluru", "postalCode": "560034" },
    "seatingCapacity": 60,
    "tableCount": 15,
    "phone": "+91-80-98765432",
    "createdAt": "2024-03-16T09:00:00Z"
  }
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 200 | Success |
| 401 | Unauthorized |
| 403 | Forbidden — token scoped to different branch |
| 404 | Branch not found |

---

### PATCH /api/v1/branches/{branchId} — Update branch settings

**Description**: Updates mutable branch settings such as operating hours, capacity, contact details, and feature toggles. Only fields included in the body are updated.

**Auth**: `branch_manager`, `restaurant_admin`, `super_admin`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `branchId` | string | Unique branch identifier |

**Request Body:**
```json
{
  "seatingCapacity": 75,
  "phone": "+91-80-11112222",
  "operatingHours": {
    "monday": { "open": "12:00", "close": "22:30" }
  }
}
```

**Response:**
```json
{
  "data": {
    "branchId": "br_km456",
    "seatingCapacity": 75,
    "updatedAt": "2024-06-10T14:00:00Z"
  }
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 200 | Updated successfully |
| 400 | Validation error |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Branch not found |

---

## Tables API

### GET /api/v1/branches/{branchId}/tables — List all tables with status

**Description**: Returns all tables for a branch with their real-time status (`available`, `occupied`, `reserved`, `cleaning`). Optionally filter by status or section.

**Auth**: `host`, `waiter`, `branch_manager`, `restaurant_admin`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `branchId` | string | Unique branch identifier |

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter: `available`, `occupied`, `reserved`, `cleaning` |
| `section` | string | Filter by floor/section name |

**Response:**
```json
{
  "data": [
    {
      "tableId": "tbl_05",
      "label": "T-05",
      "section": "Main Hall",
      "capacity": 4,
      "status": "available",
      "currentOrderId": null,
      "reservationId": null
    },
    {
      "tableId": "tbl_12",
      "label": "T-12",
      "section": "Terrace",
      "capacity": 6,
      "status": "occupied",
      "currentOrderId": "ord_998",
      "seatedAt": "2024-03-15T19:00:00Z"
    }
  ],
  "meta": { "totalCount": 28 }
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 200 | Success |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Branch not found |

---

### POST /api/v1/branches/{branchId}/tables — Create table

**Description**: Adds a new table definition to a branch. Sets the table label, seating capacity, and section. The table starts in `available` status.

**Auth**: `branch_manager`, `restaurant_admin`

**Request Body:**
```json
{
  "label": "T-29",
  "section": "Private Dining",
  "capacity": 10,
  "shape": "round",
  "positionX": 300,
  "positionY": 150
}
```

**Response:**
```json
{
  "data": {
    "tableId": "tbl_29",
    "label": "T-29",
    "section": "Private Dining",
    "capacity": 10,
    "status": "available",
    "branchId": "br_km456",
    "createdAt": "2024-03-16T10:00:00Z"
  }
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 201 | Table created |
| 400 | Validation error |
| 403 | Forbidden |
| 409 | Table label already exists in branch |

---

### PATCH /api/v1/tables/{tableId}/status — Update table status

**Description**: Manually updates the status of a table. Used by hosts to mark tables for cleaning or make them available again after maintenance.

**Auth**: `host`, `branch_manager`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `tableId` | string | Unique table identifier |

**Request Body:**
```json
{
  "status": "cleaning",
  "reason": "Post-occupancy cleaning required"
}
```

**Response:**
```json
{
  "data": {
    "tableId": "tbl_05",
    "status": "cleaning",
    "updatedAt": "2024-03-15T20:30:00Z"
  }
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 200 | Status updated |
| 400 | Invalid status transition |
| 404 | Table not found |

---

### POST /api/v1/tables/{tableId}/seat — Seat a party at table

**Description**: Marks a table as occupied and associates it with a party. Optionally links to an existing reservation. Returns `TABLE_NOT_AVAILABLE` if the table is not in `available` status.

**Auth**: `host`, `waiter`

**Request Body:**
```json
{
  "partySize": 3,
  "reservationId": "res_abc99",
  "staffId": "stf_host01",
  "notes": "VIP guest, allergic to nuts"
}
```

**Response:**
```json
{
  "data": {
    "tableId": "tbl_05",
    "status": "occupied",
    "partySize": 3,
    "seatedAt": "2024-03-15T19:15:00Z",
    "reservationId": "res_abc99"
  }
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 200 | Party seated |
| 404 | Table not found |
| 409 | TABLE_NOT_AVAILABLE — table is not in available status |

---

### POST /api/v1/tables/{tableId}/release — Release table

**Description**: Releases a table after guests have departed, transitioning it to `cleaning` status. The associated order must be fully billed before release is permitted.

**Auth**: `host`, `waiter`, `branch_manager`

**Request Body:**
```json
{
  "cleaningRequired": true
}
```

**Response:**
```json
{
  "data": {
    "tableId": "tbl_05",
    "status": "cleaning",
    "releasedAt": "2024-03-15T21:00:00Z"
  }
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 200 | Table released |
| 422 | Unpaid bill — order must be settled first |
| 404 | Table not found |

---

### POST /api/v1/tables/merge — Merge two or more tables

**Description**: Merges multiple tables into a single logical seating unit. All specified tables must be in `available` or `occupied` status. A merged table group shares a single order context.

**Auth**: `branch_manager`, `host`

**Request Body:**
```json
{
  "branchId": "br_km456",
  "tableIds": ["tbl_05", "tbl_06"],
  "primaryTableId": "tbl_05"
}
```

**Response:**
```json
{
  "data": {
    "mergeGroupId": "mg_001",
    "primaryTableId": "tbl_05",
    "mergedTableIds": ["tbl_05", "tbl_06"],
    "combinedCapacity": 8,
    "createdAt": "2024-03-15T19:00:00Z"
  }
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 200 | Tables merged |
| 400 | Fewer than 2 tables specified |
| 409 | One or more tables have conflicting statuses |

---

### POST /api/v1/tables/split — Split merged tables

**Description**: Reverses a table merge, returning each table to its individual status. Any active order on the merge group must be resolved or transferred before splitting.

**Auth**: `branch_manager`, `host`

**Request Body:**
```json
{
  "mergeGroupId": "mg_001"
}
```

**Response:**
```json
{
  "data": {
    "splitAt": "2024-03-15T21:30:00Z",
    "releasedTableIds": ["tbl_05", "tbl_06"]
  }
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 200 | Tables split |
| 404 | Merge group not found |
| 422 | Active unresolved order on merge group |

---

## Reservations API

### GET /api/v1/branches/{branchId}/reservations — List reservations

**Description**: Returns all reservations for a branch, filterable by date range and status. Results are sorted by reservation time ascending by default.

**Auth**: `host`, `branch_manager`, `restaurant_admin`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `date` | string | ISO date filter: `2024-03-15` |
| `status` | string | `pending`, `confirmed`, `arrived`, `cancelled` |
| `cursor` | string | Pagination cursor |
| `limit` | integer | Page size |

**Response:**
```json
{
  "data": [
    {
      "reservationId": "res_abc99",
      "guestName": "Priya Sharma",
      "guestPhone": "+91-9876543210",
      "partySize": 4,
      "reservationTime": "2024-03-15T19:30:00Z",
      "tableId": "tbl_08",
      "status": "confirmed"
    }
  ],
  "meta": { "totalCount": 12 }
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Invalid date format |
| 403 | Forbidden |

---

### POST /api/v1/reservations — Create reservation

**Description**: Creates a new reservation for a guest. Checks table availability for the requested time slot and party size. Returns `RESERVATION_CONFLICT` if the table is unavailable at the requested time.

**Auth**: `host`, `branch_manager`

**Request Body:**
```json
{
  "branchId": "br_km456",
  "guestName": "Rahul Mehta",
  "guestPhone": "+91-9876543211",
  "guestEmail": "rahul@example.com",
  "partySize": 2,
  "reservationTime": "2024-03-16T20:00:00Z",
  "tableId": "tbl_03",
  "notes": "Anniversary dinner",
  "source": "phone"
}
```

**Response:**
```json
{
  "data": {
    "reservationId": "res_d8f2a1",
    "status": "pending",
    "confirmationCode": "RMS-8821",
    "reservationTime": "2024-03-16T20:00:00Z",
    "tableId": "tbl_03",
    "createdAt": "2024-03-15T11:00:00Z"
  }
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 201 | Reservation created |
| 400 | Validation error |
| 409 | RESERVATION_CONFLICT |
| 422 | Table capacity insufficient for party size |

---

### PATCH /api/v1/reservations/{reservationId} — Update reservation

**Description**: Updates mutable fields on a reservation such as party size, time, table assignment, or guest notes. Cannot update a cancelled or completed reservation.

**Auth**: `host`, `branch_manager`

**Request Body:**
```json
{
  "partySize": 3,
  "reservationTime": "2024-03-16T20:30:00Z",
  "notes": "Anniversary dinner — cake requested"
}
```

**Response:**
```json
{
  "data": {
    "reservationId": "res_d8f2a1",
    "partySize": 3,
    "reservationTime": "2024-03-16T20:30:00Z",
    "updatedAt": "2024-03-15T12:00:00Z"
  }
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 200 | Updated |
| 404 | Reservation not found |
| 409 | RESERVATION_CONFLICT with new time |
| 422 | Reservation is in a terminal state |

---

### POST /api/v1/reservations/{reservationId}/confirm — Confirm reservation

**Description**: Transitions a reservation from `pending` to `confirmed` status. May trigger an SMS or email confirmation to the guest if notifications are enabled.

**Auth**: `host`, `branch_manager`

**Response:**
```json
{
  "data": {
    "reservationId": "res_d8f2a1",
    "status": "confirmed",
    "confirmedAt": "2024-03-15T12:05:00Z"
  }
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 200 | Confirmed |
| 404 | Not found |
| 422 | Cannot confirm — reservation already cancelled |

---

### POST /api/v1/reservations/{reservationId}/cancel — Cancel reservation

**Description**: Cancels a reservation and releases the held table slot. Optionally records a cancellation reason. Triggers a cancellation notification to the guest.

**Auth**: `host`, `branch_manager`

**Request Body:**
```json
{
  "reason": "Guest called to cancel",
  "notifyGuest": true
}
```

**Response:**
```json
{
  "data": {
    "reservationId": "res_d8f2a1",
    "status": "cancelled",
    "cancelledAt": "2024-03-15T13:00:00Z"
  }
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 200 | Cancelled |
| 404 | Not found |
| 422 | Already cancelled |

---

### POST /api/v1/reservations/{reservationId}/arrive — Mark guest as arrived

**Description**: Marks the guest as arrived, transitioning status to `arrived`. Typically triggers table assignment and seating workflow. Must be followed by `POST /tables/{tableId}/seat`.

**Auth**: `host`, `waiter`

**Response:**
```json
{
  "data": {
    "reservationId": "res_d8f2a1",
    "status": "arrived",
    "arrivedAt": "2024-03-16T20:02:00Z"
  }
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 200 | Marked as arrived |
| 404 | Reservation not found |
| 422 | Reservation not in confirmed state |

---

## Menus API

### GET /api/v1/branches/{branchId}/menus — List menus

**Description**: Returns all menus associated with a branch (e.g., Lunch, Dinner, Takeaway). Menus include metadata and category summaries but not the full item list. Use `GET /menus/{menuId}/items` for item details.

**Auth**: Any authenticated token scoped to the branch

**Response:**
```json
{
  "data": [
    {
      "menuId": "mnu_dine01",
      "name": "Dinner Menu",
      "type": "dine_in",
      "status": "active",
      "categoryCount": 6,
      "itemCount": 48,
      "validFrom": "17:00",
      "validTo": "23:00"
    }
  ]
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 200 | Success |
| 403 | Forbidden |
| 404 | Branch not found |

---

### POST /api/v1/menus — Create menu

**Description**: Creates a new menu under a branch. Menu type controls which order types can reference it. Operating time windows (`validFrom`/`validTo`) restrict availability.

**Auth**: `branch_manager`, `restaurant_admin`

**Request Body:**
```json
{
  "branchId": "br_km456",
  "name": "Lunch Special",
  "type": "dine_in",
  "validFrom": "11:00",
  "validTo": "15:00",
  "categories": [
    { "name": "Starters", "displayOrder": 1 },
    { "name": "Mains", "displayOrder": 2 }
  ]
}
```

**Response:**
```json
{
  "data": {
    "menuId": "mnu_lunch02",
    "name": "Lunch Special",
    "status": "active",
    "createdAt": "2024-03-17T08:00:00Z"
  }
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 201 | Menu created |
| 400 | Validation error |
| 403 | Forbidden |

---

### GET /api/v1/menus/{menuId}/items — List menu items (paginated)

**Description**: Returns paginated menu items for the specified menu. Items include pricing, availability, allergens, and modifier groups. Filterable by category and availability status.

**Auth**: Any authenticated token

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `categoryId` | string | Filter by category |
| `available` | boolean | Filter by availability |
| `cursor` | string | Pagination cursor |
| `limit` | integer | Page size (default 50) |

**Response:**
```json
{
  "data": [
    {
      "itemId": "mi_grilled_salmon",
      "name": "Grilled Salmon",
      "categoryId": "cat_mains",
      "price": 28.50,
      "available": true,
      "allergens": ["fish", "dairy"],
      "preparationTime": 18,
      "modifierGroups": [
        { "groupId": "mg_sauce", "name": "Sauce Choice", "required": true }
      ]
    }
  ],
  "meta": { "totalCount": 48, "cursor": null, "hasMore": false }
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 200 | Success |
| 404 | Menu not found |

---

### POST /api/v1/menu-items — Create menu item

**Description**: Creates a new item within a menu category. Includes pricing, preparation metadata, allergen information, and modifier group links. The item is initially set to `available: true`.

**Auth**: `branch_manager`, `restaurant_admin`

**Request Body:**
```json
{
  "menuId": "mnu_dine01",
  "categoryId": "cat_mains",
  "name": "Truffle Risotto",
  "description": "Creamy Arborio rice with black truffle shavings",
  "price": 32.00,
  "preparationTime": 20,
  "allergens": ["dairy", "gluten"],
  "calories": 620,
  "tags": ["vegetarian", "chef-special"],
  "modifierGroups": ["mg_portion_size"]
}
```

**Response:**
```json
{
  "data": {
    "itemId": "mi_truffle_risotto",
    "name": "Truffle Risotto",
    "price": 32.00,
    "available": true,
    "createdAt": "2024-03-17T09:00:00Z"
  }
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 201 | Item created |
| 400 | Validation error |
| 403 | Forbidden |
| 404 | Menu or category not found |

---

### PATCH /api/v1/menu-items/{itemId}/availability — Toggle availability

**Description**: Quickly toggles a menu item's availability without requiring a full item update. Commonly used by kitchen staff to 86 an item when stock runs out mid-service.

**Auth**: `branch_manager`, `chef`

**Request Body:**
```json
{
  "available": false,
  "reason": "Sold out for the evening",
  "resumeAt": "2024-03-17T11:00:00Z"
}
```

**Response:**
```json
{
  "data": {
    "itemId": "mi_truffle_risotto",
    "available": false,
    "updatedAt": "2024-03-15T20:00:00Z"
  }
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 200 | Availability updated |
| 404 | Item not found |
| 403 | Forbidden |

---

## Orders API

### POST /api/v1/orders — Create draft order

**Description**: Creates a new draft order for a table or as a takeaway/delivery order. Items can be added at creation time or subsequently via `PATCH /orders/{orderId}/items`. The order remains in `draft` status until submitted to the kitchen.

**Auth**: `waiter`, `cashier`, `branch_manager`

**Request Body:**
```json
{
  "branchId": "br_abc123",
  "tableId": "tbl_05",
  "orderType": "dine_in",
  "covers": 4,
  "staffId": "stf_waiter01",
  "items": [
    {
      "menuItemId": "mi_grilled_salmon",
      "quantity": 2,
      "unitPrice": 28.50,
      "courseNumber": 2,
      "notes": "one well-done",
      "modifiers": [{ "modifierId": "mod_no_sauce" }]
    },
    {
      "menuItemId": "mi_caesar_salad",
      "quantity": 1,
      "unitPrice": 14.00,
      "courseNumber": 1
    }
  ],
  "notes": "Birthday celebration, please arrange dessert surprise"
}
```

**Response:**
```json
{
  "data": {
    "orderId": "ord_998",
    "orderNumber": "ORD-2024-0998",
    "status": "draft",
    "tableId": "tbl_05",
    "orderType": "dine_in",
    "covers": 4,
    "subtotal": 71.00,
    "itemCount": 3,
    "createdAt": "2024-03-15T18:30:00Z"
  }
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 201 | Order created |
| 400 | Validation error |
| 409 | TABLE_NOT_AVAILABLE |
| 422 | MENU_ITEM_UNAVAILABLE |

---

### GET /api/v1/orders/{orderId} — Get order with items

**Description**: Returns the full order object including all line items, modifiers, course numbers, status history, and associated bill ID if billing has been initiated.

**Auth**: `waiter`, `cashier`, `chef`, `branch_manager`

**Response:**
```json
{
  "data": {
    "orderId": "ord_998",
    "orderNumber": "ORD-2024-0998",
    "status": "in_progress",
    "tableId": "tbl_05",
    "covers": 4,
    "items": [
      {
        "lineItemId": "li_001",
        "menuItemId": "mi_grilled_salmon",
        "name": "Grilled Salmon",
        "quantity": 2,
        "unitPrice": 28.50,
        "totalPrice": 57.00,
        "courseNumber": 2,
        "status": "preparing",
        "notes": "one well-done"
      }
    ],
    "subtotal": 71.00,
    "billId": null,
    "createdAt": "2024-03-15T18:30:00Z"
  }
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 200 | Success |
| 403 | Forbidden |
| 404 | Order not found |

---

### POST /api/v1/orders/{orderId}/submit — Submit order to kitchen

**Description**: Transitions the order from `draft` to `submitted` and creates kitchen tickets for each station. This operation is idempotent — submitting the same order twice returns the existing ticket IDs without creating duplicates. Requires `X-Idempotency-Key` header.

**Auth**: `waiter`, `branch_manager`

**Request Body:**
```json
{
  "idempotencyKey": "submit_ord998_20240315_1"
}
```

**Response:**
```json
{
  "data": {
    "orderId": "ord_998",
    "status": "submitted",
    "kitchenTickets": [
      { "ticketId": "kt_001", "stationId": "sta_grill", "itemCount": 2 },
      { "ticketId": "kt_002", "stationId": "sta_cold", "itemCount": 1 }
    ],
    "submittedAt": "2024-03-15T18:32:00Z"
  }
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 200 | Submitted (idempotent) |
| 404 | Order not found |
| 422 | Order has no items |
| 409 | KITCHEN_TICKET_LOCKED |

---

### POST /api/v1/orders/{orderId}/cancel — Cancel order

**Description**: Cancels an order and voids any associated kitchen tickets. Only orders in `draft` or `submitted` status can be cancelled. In-progress cooking orders require manager approval.

**Auth**: `branch_manager`, `restaurant_admin`

**Request Body:**
```json
{
  "reason": "Guest left before food was prepared",
  "notifyKitchen": true
}
```

**Response:**
```json
{
  "data": {
    "orderId": "ord_998",
    "status": "cancelled",
    "cancelledAt": "2024-03-15T18:45:00Z"
  }
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 200 | Cancelled |
| 404 | Order not found |
| 422 | ORDER_NOT_CANCELLABLE |

---

## Kitchen API

### GET /api/v1/branches/{branchId}/kitchen/tickets — Get all open tickets

**Description**: Returns all open kitchen tickets for a branch, sorted by priority (VIP, time elapsed). Used by the KDS overhead display or kitchen manager view. Tickets include station assignment, item details, and elapsed time.

**Auth**: `chef`, `branch_manager`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `stationId` | string | Filter by kitchen station |
| `status` | string | `new`, `acknowledged`, `preparing`, `ready` |

**Response:**
```json
{
  "data": [
    {
      "ticketId": "kt_001",
      "orderNumber": "ORD-2024-0998",
      "stationId": "sta_grill",
      "status": "preparing",
      "items": [
        { "lineItemId": "li_001", "name": "Grilled Salmon x2", "notes": "one well-done" }
      ],
      "createdAt": "2024-03-15T18:32:00Z",
      "elapsedSeconds": 420
    }
  ]
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 200 | Success |
| 403 | Forbidden |
| 404 | Branch not found |

---

### PATCH /api/v1/kitchen/tickets/{ticketId}/status — Update ticket status

**Description**: Updates the status of a kitchen ticket. Allowed transitions: `new` → `acknowledged` → `preparing` → `ready`. Attempting an invalid transition returns `400`.

**Auth**: `chef`, `branch_manager`

**Request Body:**
```json
{
  "status": "ready",
  "notes": "Plated and ready for runner"
}
```

**Response:**
```json
{
  "data": {
    "ticketId": "kt_001",
    "status": "ready",
    "readyAt": "2024-03-15T18:45:00Z"
  }
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 200 | Status updated |
| 400 | Invalid status transition |
| 404 | Ticket not found |
| 409 | KITCHEN_TICKET_LOCKED |

---

### POST /api/v1/kitchen/tickets/{ticketId}/bump — Bump ticket to complete

**Description**: Marks a ticket as completed and removes it from the active KDS display. Bumping a ticket updates the associated order line item statuses to `served`. Triggers order completion check.

**Auth**: `chef`

**Response:**
```json
{
  "data": {
    "ticketId": "kt_001",
    "status": "completed",
    "bumpedAt": "2024-03-15T18:47:00Z"
  }
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 200 | Bumped |
| 404 | Ticket not found |
| 422 | Ticket not in ready status |

---

### POST /api/v1/kitchen/tickets/{ticketId}/recall — Recall bumped ticket

**Description**: Recalls an accidentally bumped ticket back to the active display with a `recalled` status. The ticket is highlighted in the KDS to indicate it needs attention.

**Auth**: `chef`, `branch_manager`

**Response:**
```json
{
  "data": {
    "ticketId": "kt_001",
    "status": "recalled",
    "recalledAt": "2024-03-15T18:48:00Z"
  }
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 200 | Recalled |
| 404 | Ticket not found |
| 422 | Ticket not in completed status |

---

## Billing and Payments API

### POST /api/v1/orders/{orderId}/bill — Generate bill for order

**Description**: Generates a bill for a completed order. Applies applicable taxes, service charges, and any active discounts or loyalty redemptions. A bill can only be generated once per order; subsequent calls return the existing bill.

**Auth**: `cashier`, `waiter`, `branch_manager`

**Request Body:**
```json
{
  "discountCode": "SUMMER10",
  "loyaltyPointsRedeem": 200,
  "serviceChargeOverride": null
}
```

**Response:**
```json
{
  "data": {
    "billId": "bil_443",
    "orderId": "ord_998",
    "subtotal": 71.00,
    "discountAmount": 7.10,
    "serviceCharge": 6.39,
    "taxAmount": 8.45,
    "totalAmount": 78.74,
    "status": "unpaid",
    "generatedAt": "2024-03-15T21:00:00Z"
  }
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 201 | Bill generated |
| 200 | Existing bill returned (idempotent) |
| 404 | Order not found |
| 422 | Order not yet complete |

---

### POST /api/v1/bills/{billId}/payments — Record payment

**Description**: Records one or more payments against a bill. Supports split payment across multiple methods (cash, card, UPI, wallet). The sum of all payment amounts plus tip must equal the bill total. Returns `PAYMENT_AMOUNT_MISMATCH` otherwise.

**Auth**: `cashier`, `branch_manager`

**Request Body:**
```json
{
  "payments": [
    { "paymentMethod": "credit_card", "amount": 85.00, "referenceNumber": "AUTH_88721" },
    { "paymentMethod": "cash", "amount": 15.00 }
  ],
  "tipAmount": 12.00,
  "idempotencyKey": "pay_ord456_20240315_1"
}
```

**Response:**
```json
{
  "data": {
    "billId": "bil_443",
    "status": "paid",
    "totalPaid": 112.00,
    "tipAmount": 12.00,
    "payments": [
      { "paymentId": "pay_001", "method": "credit_card", "amount": 85.00, "processedAt": "2024-03-15T21:05:00Z" },
      { "paymentId": "pay_002", "method": "cash", "amount": 15.00 }
    ],
    "settledAt": "2024-03-15T21:05:00Z"
  }
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 200 | Payment recorded, bill settled |
| 402 | PAYMENT_DECLINED |
| 404 | Bill not found |
| 409 | BILL_ALREADY_PAID |
| 422 | PAYMENT_AMOUNT_MISMATCH |
| 422 | SPLIT_PAYMENT_EXCEEDS_TOTAL |

---

### POST /api/v1/bills/{billId}/splits — Split bill among guests

**Description**: Splits a bill into multiple sub-bills by seat, item, or equal share. Each resulting split bill can be paid independently. Returns the list of generated split bill IDs.

**Auth**: `cashier`, `branch_manager`

**Request Body:**
```json
{
  "splitMethod": "by_seat",
  "splits": [
    { "label": "Guest 1", "lineItemIds": ["li_001"] },
    { "label": "Guest 2", "lineItemIds": ["li_002", "li_003"] }
  ]
}
```

**Response:**
```json
{
  "data": {
    "parentBillId": "bil_443",
    "splitBills": [
      { "billId": "bil_443a", "label": "Guest 1", "totalAmount": 57.00 },
      { "billId": "bil_443b", "label": "Guest 2", "totalAmount": 21.74 }
    ]
  }
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 200 | Bill split |
| 404 | Bill not found |
| 409 | BILL_ALREADY_PAID |
| 422 | Split amounts do not cover full bill |

---

### POST /api/v1/bills/{billId}/void — Void a bill

**Description**: Voids an unpaid bill, typically used when an order is cancelled post-billing. Requires `branch_manager` or higher role. Records a void reason for audit compliance.

**Auth**: `branch_manager`, `restaurant_admin`

**Request Body:**
```json
{
  "reason": "Order cancelled by guest before payment",
  "managerId": "stf_mgr01"
}
```

**Response:**
```json
{
  "data": {
    "billId": "bil_443",
    "status": "voided",
    "voidedAt": "2024-03-15T21:10:00Z",
    "voidedBy": "stf_mgr01"
  }
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 200 | Bill voided |
| 403 | INSUFFICIENT_ROLE |
| 404 | Bill not found |
| 409 | BILL_ALREADY_PAID — cannot void a paid bill; use refund |

---

### POST /api/v1/bills/{billId}/refund — Process refund

**Description**: Initiates a full or partial refund for a paid bill. Partial refunds specify `lineItemIds` or a `refundAmount`. Refunds are processed asynchronously; the response includes a `refundId` that can be polled for status.

**Auth**: `branch_manager`, `restaurant_admin`

**Request Body:**
```json
{
  "refundType": "partial",
  "refundAmount": 28.50,
  "reason": "Incorrect item served",
  "refundMethod": "original_payment"
}
```

**Response:**
```json
{
  "data": {
    "refundId": "ref_991",
    "billId": "bil_443",
    "refundAmount": 28.50,
    "status": "processing",
    "initiatedAt": "2024-03-15T21:20:00Z"
  }
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 202 | Refund initiated |
| 403 | INSUFFICIENT_ROLE |
| 404 | Bill not found |
| 422 | Refund amount exceeds original payment |

---

## Inventory API

### GET /api/v1/branches/{branchId}/ingredients — List ingredients with stock levels

**Description**: Returns all ingredients for a branch with current stock quantities, unit of measure, reorder thresholds, and last movement timestamp. Filterable by below-reorder-threshold status.

**Auth**: `inventory_manager`, `branch_manager`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `lowStock` | boolean | If true, return only items at or below reorder level |
| `category` | string | Filter by ingredient category (e.g., `dairy`, `proteins`) |

**Response:**
```json
{
  "data": [
    {
      "ingredientId": "ing_salmon",
      "name": "Atlantic Salmon Fillet",
      "unit": "kg",
      "currentStock": 4.5,
      "reorderLevel": 3.0,
      "reorderQuantity": 10.0,
      "lastMovementAt": "2024-03-15T07:00:00Z",
      "supplierId": "sup_seafood01"
    }
  ]
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 200 | Success |
| 403 | Forbidden |
| 404 | Branch not found |

---

### POST /api/v1/inventory/adjustments — Record stock adjustment

**Description**: Records a manual stock adjustment for reasons such as wastage, theft, spillage, or physical count correction. Each adjustment debits or credits the ingredient's stock and creates an immutable audit log entry.

**Auth**: `inventory_manager`, `branch_manager`

**Request Body:**
```json
{
  "branchId": "br_km456",
  "adjustments": [
    {
      "ingredientId": "ing_salmon",
      "adjustmentType": "wastage",
      "quantity": -0.5,
      "unit": "kg",
      "notes": "Spoilage during prep — missed temperature check"
    }
  ],
  "staffId": "stf_inv01",
  "adjustedAt": "2024-03-15T16:00:00Z"
}
```

**Response:**
```json
{
  "data": {
    "adjustmentBatchId": "adj_batch_007",
    "adjustmentsRecorded": 1,
    "processedAt": "2024-03-15T16:00:05Z"
  }
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 201 | Adjustments recorded |
| 400 | Validation error |
| 422 | INSUFFICIENT_STOCK — adjustment would result in negative stock |

---

### GET /api/v1/inventory/low-stock-alerts — Get low-stock alerts

**Description**: Returns all ingredients at or below their reorder level across a branch. Includes estimated days of stock remaining based on consumption rate. Intended for the daily procurement review workflow.

**Auth**: `inventory_manager`, `branch_manager`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `branchId` | string | Required. Branch to check |

**Response:**
```json
{
  "data": [
    {
      "ingredientId": "ing_salmon",
      "name": "Atlantic Salmon Fillet",
      "currentStock": 2.0,
      "reorderLevel": 3.0,
      "estimatedDaysRemaining": 1.5,
      "suggestedOrderQuantity": 10.0,
      "supplierId": "sup_seafood01"
    }
  ]
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Missing branchId |

---

## Procurement API

### POST /api/v1/purchase-orders — Create purchase order

**Description**: Creates a new purchase order for one or more ingredients from a supplier. The PO starts in `draft` status and must be explicitly submitted to the supplier.

**Auth**: `inventory_manager`, `branch_manager`

**Request Body:**
```json
{
  "branchId": "br_km456",
  "supplierId": "sup_seafood01",
  "expectedDeliveryDate": "2024-03-18",
  "lineItems": [
    { "ingredientId": "ing_salmon", "quantity": 10, "unit": "kg", "unitCost": 18.00 },
    { "ingredientId": "ing_tuna", "quantity": 5, "unit": "kg", "unitCost": 22.00 }
  ],
  "notes": "Urgent — low stock on salmon"
}
```

**Response:**
```json
{
  "data": {
    "poId": "po_2024_088",
    "status": "draft",
    "totalAmount": 290.00,
    "lineItemCount": 2,
    "createdAt": "2024-03-15T17:00:00Z"
  }
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 201 | PO created |
| 400 | Validation error |
| 404 | Supplier or ingredient not found |

---

### POST /api/v1/purchase-orders/{poId}/receive — Record goods receipt

**Description**: Records actual received quantities when goods arrive from the supplier. Increments ingredient stock accordingly. Supports partial receipts — unreceived items remain open on the PO.

**Auth**: `inventory_manager`

**Request Body:**
```json
{
  "receivedAt": "2024-03-18T09:00:00Z",
  "receivedBy": "stf_inv01",
  "lineItems": [
    { "ingredientId": "ing_salmon", "receivedQuantity": 10, "unit": "kg", "invoiceNumber": "INV-S-4421" },
    { "ingredientId": "ing_tuna", "receivedQuantity": 4, "unit": "kg", "invoiceNumber": "INV-S-4421" }
  ],
  "notes": "Tuna short by 1 kg — supplier to credit"
}
```

**Response:**
```json
{
  "data": {
    "poId": "po_2024_088",
    "status": "partially_received",
    "stockUpdated": true,
    "receivedAt": "2024-03-18T09:00:00Z"
  }
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 200 | Receipt recorded, stock updated |
| 404 | PO not found |
| 422 | Received quantity exceeds ordered quantity |

---

## Staff and Shifts API

### POST /api/v1/staff — Create staff member

**Description**: Creates a new staff profile under a branch. Sets the assigned role, contact details, and pay rate. A PIN for POS terminal access can be set at creation or via a separate PIN-setup flow.

**Auth**: `branch_manager`, `restaurant_admin`

**Request Body:**
```json
{
  "branchId": "br_km456",
  "firstName": "Anjali",
  "lastName": "Rao",
  "role": "waiter",
  "email": "anjali.rao@goldenfork.com",
  "phone": "+91-9876500001",
  "startDate": "2024-04-01",
  "hourlyRate": 180.00
}
```

**Response:**
```json
{
  "data": {
    "staffId": "stf_anj01",
    "firstName": "Anjali",
    "lastName": "Rao",
    "role": "waiter",
    "status": "active",
    "createdAt": "2024-03-20T10:00:00Z"
  }
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 201 | Staff created |
| 400 | Validation error |
| 409 | Email already registered |

---

### POST /api/v1/shifts — Create shift schedule

**Description**: Creates a scheduled shift for a staff member. Validates against existing shifts for the same staff member to prevent overlaps. Returns `SHIFT_OVERLAP` if a conflict is detected.

**Auth**: `branch_manager`

**Request Body:**
```json
{
  "staffId": "stf_anj01",
  "branchId": "br_km456",
  "startTime": "2024-04-01T17:00:00Z",
  "endTime": "2024-04-01T23:30:00Z",
  "role": "waiter",
  "notes": "Evening dinner service"
}
```

**Response:**
```json
{
  "data": {
    "shiftId": "shf_001",
    "staffId": "stf_anj01",
    "startTime": "2024-04-01T17:00:00Z",
    "endTime": "2024-04-01T23:30:00Z",
    "status": "scheduled",
    "createdAt": "2024-03-20T10:05:00Z"
  }
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 201 | Shift created |
| 400 | Validation error |
| 409 | SHIFT_OVERLAP |
| 404 | Staff not found |

---

### POST /api/v1/shifts/{shiftId}/clock-in — Staff clock in

**Description**: Records the actual clock-in time for a staff member's shift. Optionally validates that the clock-in is within an acceptable window of the scheduled start time. Updates shift status to `active`.

**Auth**: Any authenticated staff token (own shifts only)

**Request Body:**
```json
{
  "clockInTime": "2024-04-01T17:02:00Z",
  "terminalId": "term_pos_02",
  "pin": "4821"
}
```

**Response:**
```json
{
  "data": {
    "shiftId": "shf_001",
    "status": "active",
    "clockedInAt": "2024-04-01T17:02:00Z",
    "lateBy": "2m"
  }
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 200 | Clocked in |
| 401 | PIN_LOCKED or invalid PIN |
| 404 | Shift not found |
| 422 | Already clocked in |

---

### POST /api/v1/shifts/{shiftId}/clock-out — Staff clock out

**Description**: Records the actual clock-out time and computes total hours worked. If clock-out is earlier than scheduled end time, a `shortHours` flag is set for manager review.

**Auth**: Any authenticated staff token (own shifts only)

**Request Body:**
```json
{
  "clockOutTime": "2024-04-01T23:35:00Z",
  "terminalId": "term_pos_02"
}
```

**Response:**
```json
{
  "data": {
    "shiftId": "shf_001",
    "status": "completed",
    "clockedOutAt": "2024-04-01T23:35:00Z",
    "totalHoursWorked": 6.55,
    "shortHours": false
  }
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 200 | Clocked out |
| 404 | Shift not found |
| 422 | Not currently clocked in |

---

## Delivery API

### POST /api/v1/delivery-orders — Create delivery order

**Description**: Creates a delivery order, either from manual entry or an integrated delivery platform. Validates the delivery address against the branch's configured delivery zone. Returns `DELIVERY_AREA_UNSUPPORTED` if outside zone.

**Auth**: `delivery_manager`, `branch_manager`

**Request Body:**
```json
{
  "branchId": "br_km456",
  "source": "zomato",
  "externalOrderId": "ZMT-88991234",
  "customer": {
    "name": "Karan Patel",
    "phone": "+91-9998887770",
    "address": {
      "line1": "12 HSR Layout Sector 3",
      "city": "Bengaluru",
      "postalCode": "560102"
    }
  },
  "items": [
    { "menuItemId": "mi_grilled_salmon", "quantity": 1, "unitPrice": 28.50 }
  ],
  "deliveryFee": 49.00,
  "estimatedDeliveryMinutes": 35
}
```

**Response:**
```json
{
  "data": {
    "deliveryOrderId": "dlv_771",
    "orderId": "ord_1005",
    "status": "accepted",
    "estimatedDeliveryTime": "2024-03-15T20:05:00Z",
    "trackingUrl": "https://track.example.com/dlv_771"
  }
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 201 | Delivery order created |
| 422 | DELIVERY_AREA_UNSUPPORTED |
| 422 | MENU_ITEM_UNAVAILABLE |
| 409 | DUPLICATE_ORDER_NUMBER — external order ID already exists |

---

### POST /api/v1/delivery/webhook/{channelId} — Webhook from external delivery platform

**Description**: Receives inbound webhook events from external delivery platforms (Zomato, Swiggy, Dunzo). Validates the HMAC-SHA256 signature in the `X-Webhook-Signature` header before processing. Returns `200` immediately and processes the event asynchronously.

**Auth**: API key (`X-API-Key` header)

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `channelId` | string | Delivery channel identifier (e.g., `zomato`, `swiggy`) |

**Request Body:**
```json
{
  "event": "delivery.status_updated",
  "externalOrderId": "ZMT-88991234",
  "status": "out_for_delivery",
  "driverName": "Vikram",
  "driverPhone": "+91-9001002003",
  "estimatedArrival": "2024-03-15T20:00:00Z",
  "timestamp": "2024-03-15T19:45:00Z"
}
```

**Response:**
```json
{ "acknowledged": true }
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 200 | Acknowledged |
| 401 | Invalid API key |
| 400 | Signature validation failed |

---

## Reports API

### GET /api/v1/reports/daily-sales — Daily sales report

**Description**: Returns aggregated sales data for a branch within a date range. Includes total revenue, order counts, average order value, payment method breakdown, and top-selling items.

**Auth**: `branch_manager`, `restaurant_admin`

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `branchId` | string | Yes | Target branch |
| `startDate` | string | Yes | ISO date `2024-03-01` |
| `endDate` | string | Yes | ISO date `2024-03-15` |
| `format` | string | No | `json` (default) or `csv` |

**Response:**
```json
{
  "data": {
    "branchId": "br_km456",
    "period": { "from": "2024-03-01", "to": "2024-03-15" },
    "totalRevenue": 148500.00,
    "totalOrders": 612,
    "averageOrderValue": 242.65,
    "paymentBreakdown": {
      "cash": 22000.00,
      "credit_card": 85000.00,
      "upi": 41500.00
    },
    "topItems": [
      { "itemId": "mi_grilled_salmon", "name": "Grilled Salmon", "quantity": 210, "revenue": 5985.00 }
    ]
  }
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 200 | Report returned |
| 400 | Missing required parameters |
| 403 | Forbidden |

---

### GET /api/v1/reports/branch-operations — Operational KPIs

**Description**: Returns operational performance metrics including average preparation time by station, table turn rate, covers served, and peak hour analysis. Useful for staffing and capacity planning.

**Auth**: `branch_manager`, `restaurant_admin`

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `branchId` | string | Yes | Target branch |
| `startDate` | string | Yes | ISO date |
| `endDate` | string | Yes | ISO date |
| `format` | string | No | `json` or `csv` |

**Response:**
```json
{
  "data": {
    "averageTableTurnMinutes": 68,
    "tableTurnsPerDay": 3.4,
    "coversServed": 2080,
    "averagePrepTimeByStation": {
      "grill": 16,
      "cold": 8,
      "pastry": 22
    },
    "peakHour": "20:00"
  }
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Invalid date range |

---

### GET /api/v1/reports/menu-engineering — Item performance

**Description**: Returns the menu engineering matrix — sales volume vs. contribution margin for each item. Items are classified as Stars, Plowhorses, Puzzles, or Dogs. Useful for menu optimization decisions.

**Auth**: `branch_manager`, `restaurant_admin`

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `branchId` | string | Yes | Target branch |
| `startDate` | string | Yes | ISO date |
| `endDate` | string | Yes | ISO date |
| `format` | string | No | `json` or `csv` |

**Response:**
```json
{
  "data": [
    {
      "itemId": "mi_grilled_salmon",
      "name": "Grilled Salmon",
      "quantitySold": 210,
      "totalRevenue": 5985.00,
      "foodCostPct": 28.5,
      "contributionMargin": 20.37,
      "category": "star"
    }
  ]
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Missing parameters |

---

### GET /api/v1/reports/inventory-valuation — Inventory valuation

**Description**: Returns the current inventory valuation including cost of goods on hand, consumption over the period, and wastage amounts by category. Used for cost-of-goods-sold accounting.

**Auth**: `inventory_manager`, `branch_manager`

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `branchId` | string | Yes | Target branch |
| `startDate` | string | Yes | ISO date |
| `endDate` | string | Yes | ISO date |
| `format` | string | No | `json` or `csv` |

**Response:**
```json
{
  "data": {
    "openingStockValue": 42000.00,
    "closingStockValue": 38500.00,
    "totalConsumptionValue": 31200.00,
    "totalWastageValue": 2300.00,
    "purchasesValue": 30000.00,
    "costOfGoodsSold": 33500.00
  }
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Missing parameters |

---

### GET /api/v1/reports/staff-performance — Staff productivity and attendance

**Description**: Returns attendance, punctuality, hours worked, and orders handled per staff member for the specified period. Useful for payroll preparation and performance reviews.

**Auth**: `branch_manager`, `restaurant_admin`

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `branchId` | string | Yes | Target branch |
| `startDate` | string | Yes | ISO date |
| `endDate` | string | Yes | ISO date |
| `format` | string | No | `json` or `csv` |

**Response:**
```json
{
  "data": [
    {
      "staffId": "stf_anj01",
      "name": "Anjali Rao",
      "role": "waiter",
      "totalHoursWorked": 78.5,
      "shiftsCompleted": 13,
      "lateArrivals": 1,
      "ordersHandled": 194,
      "averageOrderValue": 215.00
    }
  ]
}
```

**Response Codes:**

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Missing parameters |

---

## Webhook Contracts

Webhooks allow external systems (delivery platforms, payment gateways, SMS providers) to push events into the Restaurant Management System asynchronously.

### Supported Webhook Sources

- **Delivery platforms** (Zomato, Swiggy, Dunzo): order lifecycle events — accepted, picked up, out for delivery, delivered, failed.
- **Payment gateways** (Razorpay, Stripe): payment captured, payment failed, refund processed, dispute opened.
- **SMS/email providers** (Twilio, SendGrid): delivery receipts, bounce notifications, OTP confirmation.

### Inbound Endpoint

All inbound webhooks are received at:
```
POST /api/v1/delivery/webhook/{channelId}
```

### Signature Validation

Every inbound webhook MUST include an `X-Webhook-Signature` header. The server validates the signature using HMAC-SHA256:

```
signature = HMAC-SHA256(secret_key, request_body_bytes)
```

Requests with missing or invalid signatures are rejected with `400 Bad Request` and error code `WEBHOOK_SIGNATURE_INVALID`. The shared secret is configured per-channel in the integration settings.

### Retry Policy

Webhook delivery from the platform to partners follows exponential backoff:
- Attempt 1: immediate
- Attempt 2: 30 seconds
- Attempt 3: 5 minutes
- Attempt 4: 30 minutes
- Attempt 5: 2 hours

After 5 failed attempts, the webhook is marked `dead_letter` and an alert is raised. Partners may replay dead-letter webhooks via the admin console.

### Response Requirements

Webhook receivers must respond with `200 OK` within 5 seconds. Any non-2xx response or timeout is treated as a delivery failure and triggers a retry.

### Example: Delivery Status Update Webhook

```json
{
  "event": "delivery.status_updated",
  "webhookId": "wh_00112233",
  "channelId": "zomato",
  "deliveredAt": "2024-03-15T19:45:00Z",
  "payload": {
    "externalOrderId": "ZMT-88991234",
    "internalDeliveryOrderId": "dlv_771",
    "status": "out_for_delivery",
    "driver": {
      "name": "Vikram",
      "phone": "+91-9001002003",
      "currentLocation": { "lat": 12.9352, "lon": 77.6245 }
    },
    "estimatedArrival": "2024-03-15T20:00:00Z"
  },
  "signature": "sha256=abcdef1234567890abcdef1234567890abcdef12"
}
```

---

## Rate Limiting

The API enforces rate limits per API key and per authenticated user to ensure fair usage and system stability.

### Limits by Endpoint Category

| Category | Limit | Window |
|----------|-------|--------|
| Standard operations (orders, tables, billing) | 1000 req/min | rolling 60s |
| Report endpoints | 100 req/min | rolling 60s |
| Auth endpoints (login, refresh, PIN) | 50 req/min | rolling 60s |
| Webhook ingest | 500 req/min | rolling 60s |

### Burst Allowance

A burst of up to **200 requests per 10 seconds** is permitted for standard operations. Requests exceeding the burst limit immediately receive a `429 RATE_LIMIT_EXCEEDED` response.

### Rate Limit Response Headers

All responses include rate limit context headers:

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Maximum requests allowed in the current window |
| `X-RateLimit-Remaining` | Requests remaining in the current window |
| `X-RateLimit-Reset` | Unix timestamp when the rate limit window resets |
| `Retry-After` | Seconds to wait before retrying (only on 429 responses) |

### Exceeding the Limit

When rate limited, the server responds with:

```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1710527460
Retry-After: 17
Content-Type: application/json

{
  "errorCode": "RATE_LIMIT_EXCEEDED",
  "message": "Rate limit of 1000 req/min exceeded. Retry after 17 seconds.",
  "retryable": true,
  "retryAfterSeconds": 17
}
```

### Per-IP Limits for Unauthenticated Requests

Unauthenticated requests (e.g., delivery webhook verification before authentication) are limited to **30 req/min per IP address** to prevent abuse. Exceeding this limit results in a temporary 10-minute IP block.

---

## Canonical Error Response

All API errors are returned in a consistent JSON envelope to simplify client-side error handling:

### JSON Schema

```json
{
  "errorCode": "string — machine-readable error code from the Error Codes Reference table",
  "message": "string — human-readable description of the error",
  "correlationId": "string — unique request trace ID for support escalation",
  "retryable": "boolean — whether the client may safely retry this request",
  "timestamp": "string — ISO 8601 UTC timestamp of the error",
  "path": "string — the request path that produced the error",
  "details": "object — optional structured context specific to the error type"
}
```

### Example

```json
{
  "errorCode": "TABLE_NOT_AVAILABLE",
  "message": "Table T-05 is currently occupied and cannot be seated.",
  "correlationId": "corr_d4e5f6",
  "retryable": false,
  "timestamp": "2024-03-15T18:30:00Z",
  "path": "/api/v1/tables/tbl_05/seat",
  "details": {
    "tableId": "tbl_05",
    "currentStatus": "occupied",
    "estimatedAvailableAt": "2024-03-15T19:15:00Z"
  }
}
```

### Validation Error Example (400)

When `errorCode` is `VALIDATION_ERROR`, the `details.fields` array provides per-field errors:

```json
{
  "errorCode": "VALIDATION_ERROR",
  "message": "Request validation failed. See details.fields for specifics.",
  "correlationId": "corr_a1b2c3",
  "retryable": false,
  "timestamp": "2024-03-15T18:00:00Z",
  "path": "/api/v1/orders",
  "details": {
    "fields": [
      { "field": "covers", "issue": "must be a positive integer" },
      { "field": "items[0].quantity", "issue": "must be greater than 0" }
    ]
  }
}
```

---

## Pagination Response Envelope

All list endpoints return data wrapped in the standard pagination envelope:

### Full Envelope Structure

```json
{
  "data": [
    {
      "orderId": "ord_998",
      "orderNumber": "ORD-2024-0998",
      "status": "in_progress",
      "tableId": "tbl_05",
      "createdAt": "2024-03-15T18:30:00Z"
    }
  ],
  "meta": {
    "cursor": "eyJpZCI6InRibF8wNSJ9",
    "nextCursor": "eyJpZCI6InRibF8xMCJ9",
    "limit": 50,
    "hasMore": true,
    "totalCount": 243
  },
  "links": {
    "self": "/api/v1/branches/br_abc/orders?limit=50&cursor=eyJpZCI6InRibF8wNSJ9",
    "next": "/api/v1/branches/br_abc/orders?limit=50&cursor=eyJpZCI6InRibF8xMCJ9"
  }
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `data` | array | The records for the current page |
| `meta.cursor` | string | Opaque cursor for the start of this page |
| `meta.nextCursor` | string | Opaque cursor to pass for the next page. Absent when `hasMore` is false |
| `meta.limit` | integer | The page size used for this response |
| `meta.hasMore` | boolean | Whether more records exist beyond this page |
| `meta.totalCount` | integer | Total matching records. Approximate for large datasets |
| `links.self` | string | Full URL for the current page |
| `links.next` | string | Full URL for the next page. Absent when `hasMore` is false |

### Cursor Encoding

Cursors are base64-encoded JSON objects containing the last-seen resource identifier and sort key. Clients MUST treat cursors as opaque strings and not attempt to parse or construct them:

```
eyJpZCI6Im9yZF85OTgifQ==  →  {"id": "ord_998"}
```

Cursors are valid for 24 hours after generation. Expired cursors return `400 VALIDATION_ERROR` with `details.field: "cursor"`.
