# API Design

## Overview

RESTful API design for the Order Management and Delivery System. All endpoints follow OpenAPI 3.1 conventions with JSON request/response bodies, JWT authentication via Cognito, and `Idempotency-Key` headers on all mutating operations.

## Base URL

```
https://api.oms.example.com/v1
```

## Authentication

All endpoints require a valid JWT in the `Authorization: Bearer <token>` header. Tokens are issued by Amazon Cognito. Role-based access is enforced via Cognito groups mapped to API Gateway authorizer.

## Common Headers

| Header | Required | Description |
|---|---|---|
| `Authorization` | Yes | `Bearer <JWT>` |
| `Content-Type` | Yes (mutations) | `application/json` |
| `Idempotency-Key` | Yes (POST/PUT/PATCH) | Client-generated UUID for deduplication |
| `X-Correlation-Id` | Optional | Propagated through all services for tracing |

## Common Error Codes

| Code | Meaning | Body |
|---|---|---|
| 400 | Bad Request | `{ "error": "VALIDATION_ERROR", "details": [...] }` |
| 401 | Unauthorized | `{ "error": "UNAUTHORIZED" }` |
| 403 | Forbidden | `{ "error": "FORBIDDEN" }` |
| 404 | Not Found | `{ "error": "NOT_FOUND", "resource": "..." }` |
| 409 | Conflict | `{ "error": "CONFLICT", "reason": "..." }` |
| 429 | Rate Limited | `{ "error": "RATE_LIMITED", "retry_after": 30 }` |
| 500 | Internal Error | `{ "error": "INTERNAL_ERROR", "trace_id": "..." }` |

## Pagination

All list endpoints support cursor-based pagination:
```
GET /orders?cursor=eyJ...&limit=20
```
Response includes: `{ "items": [...], "next_cursor": "eyJ...", "has_more": true }`

---

## Endpoints

### Products

| Method | Path | Auth Role | Description |
|---|---|---|---|
| GET | /products | Public | List/search products with filters |
| GET | /products/{id} | Public | Get product details with variants |
| POST | /products | Admin | Create product |
| PUT | /products/{id} | Admin | Update product |
| DELETE | /products/{id} | Admin | Archive product (soft delete) |
| POST | /products/bulk-import | Admin | Bulk import via CSV upload URL |

### Categories

| Method | Path | Auth Role | Description |
|---|---|---|---|
| GET | /categories | Public | List category tree |
| POST | /categories | Admin | Create category |
| PUT | /categories/{id} | Admin | Update category |

### Cart

| Method | Path | Auth Role | Description |
|---|---|---|---|
| GET | /cart | Customer | Get current cart |
| POST | /cart/items | Customer | Add item to cart |
| PATCH | /cart/items/{id} | Customer | Update item quantity |
| DELETE | /cart/items/{id} | Customer | Remove item from cart |

### Orders

| Method | Path | Auth Role | Description |
|---|---|---|---|
| POST | /orders/checkout | Customer | Create order from cart |
| GET | /orders | Customer/Admin | List orders (filtered by role) |
| GET | /orders/{id} | Customer/Admin | Get order details with milestones |
| PATCH | /orders/{id}/cancel | Customer | Cancel order |
| PATCH | /orders/{id}/address | Customer | Update delivery address |

### Payments

| Method | Path | Auth Role | Description |
|---|---|---|---|
| GET | /payments/{order_id} | Customer/Finance | Get payment details |
| POST | /payments/refund | Finance | Initiate manual refund |
| GET | /payments/reconciliation | Finance | Get reconciliation report |

### Fulfillment

| Method | Path | Auth Role | Description |
|---|---|---|---|
| GET | /fulfillment/tasks | Warehouse | List assigned tasks |
| POST | /fulfillment/tasks/{id}/start | Warehouse | Start picking task |
| POST | /fulfillment/tasks/{id}/scan | Warehouse | Scan item barcode |
| POST | /fulfillment/tasks/{id}/pack | Warehouse | Record packing complete |
| GET | /fulfillment/manifests | Warehouse/Ops | List delivery manifests |

### Deliveries

| Method | Path | Auth Role | Description |
|---|---|---|---|
| GET | /deliveries/assignments | Delivery | List my assignments |
| GET | /deliveries/assignments/{id} | Delivery/Ops | Get assignment details |
| PATCH | /deliveries/assignments/{id}/status | Delivery | Update delivery status |
| POST | /deliveries/assignments/{id}/pod | Delivery | Upload proof of delivery |
| POST | /deliveries/assignments/{id}/fail | Delivery | Record failed delivery |
| PATCH | /deliveries/assignments/{id}/reassign | Ops Manager | Reassign to different staff |

### Returns

| Method | Path | Auth Role | Description |
|---|---|---|---|
| POST | /returns | Customer | Initiate return request |
| GET | /returns/{id} | Customer/Admin | Get return details |
| PATCH | /returns/{id}/pickup | Delivery | Confirm return pickup |
| POST | /returns/{id}/inspect | Warehouse | Record inspection result |

### Delivery Zones

| Method | Path | Auth Role | Description |
|---|---|---|---|
| GET | /delivery-zones | Ops Manager/Admin | List delivery zones |
| POST | /delivery-zones | Ops Manager | Create delivery zone |
| PUT | /delivery-zones/{id} | Ops Manager | Update delivery zone |
| PATCH | /delivery-zones/{id}/deactivate | Ops Manager | Deactivate zone |

### Staff

| Method | Path | Auth Role | Description |
|---|---|---|---|
| GET | /staff | Admin | List staff members |
| POST | /staff | Admin | Create staff account |
| PUT | /staff/{id} | Admin | Update staff details |
| PATCH | /staff/{id}/deactivate | Admin | Deactivate staff account |

### Notifications

| Method | Path | Auth Role | Description |
|---|---|---|---|
| GET | /notifications/templates | Admin | List notification templates |
| POST | /notifications/templates | Admin | Create template |
| PUT | /notifications/templates/{id} | Admin | Update template |
| GET | /notifications/preferences | Customer | Get notification preferences |
| PUT | /notifications/preferences | Customer | Update preferences |

### Analytics

| Method | Path | Auth Role | Description |
|---|---|---|---|
| GET | /analytics/sales | Admin/Ops | Sales dashboard data |
| GET | /analytics/delivery | Ops Manager | Delivery performance KPIs |
| GET | /analytics/inventory | Admin/Ops | Inventory reports |
| GET | /analytics/staff/{id} | Ops Manager | Staff performance metrics |
| POST | /analytics/reports/export | Admin | Generate and export report |

### Configuration

| Method | Path | Auth Role | Description |
|---|---|---|---|
| GET | /config | Admin | Get platform configuration |
| PUT | /config/{key} | Admin | Update configuration value |
| GET | /config/history | Admin | Get configuration change history |

### Audit

| Method | Path | Auth Role | Description |
|---|---|---|---|
| GET | /audit-logs | Admin | Search audit logs (filtered) |

---

## Sample Request / Response

### POST /orders/checkout

**Request:**
```json
{
  "cart_id": "cart-abc123",
  "delivery_address_id": "addr-def456",
  "payment_method": {
    "type": "card",
    "token": "tok_stripe_xyz"
  },
  "coupon_code": "SAVE10"
}
```

**Response (201):**
```json
{
  "order_id": "ord-9f8e7d6c",
  "order_number": "ORD-20260404-0023",
  "status": "Confirmed",
  "subtotal": 2500.00,
  "tax_amount": 325.00,
  "shipping_fee": 100.00,
  "discount_amount": 250.00,
  "total_amount": 2675.00,
  "estimated_delivery": "2026-04-06T18:00:00+05:45",
  "created_at": "2026-04-04T14:30:00+05:45"
}
```

### POST /deliveries/assignments/{id}/pod

**Request (multipart/form-data):**
```
signature: <binary image file>
photo: <binary image file>
delivery_notes: "Left with security guard"
```

**Response (200):**
```json
{
  "pod_id": "pod-abc123",
  "order_id": "ord-9f8e7d6c",
  "status": "Delivered",
  "captured_at": "2026-04-05T15:30:00+05:45"
}
```
