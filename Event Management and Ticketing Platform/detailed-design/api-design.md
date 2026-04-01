# API Design

## Overview

The platform exposes a RESTful JSON API versioned under `/api/v1/`. All endpoints return `application/json`. Request bodies must set `Content-Type: application/json`. The API is designed around resource-oriented URLs; bulk operations use sub-resource paths (e.g., `/events/{id}/publish`) rather than RPC-style action verbs. Idempotency is supported on mutating endpoints via an `Idempotency-Key` header — the server caches the response for 24 hours and replays it on duplicate requests with the same key.

Pagination uses cursor-based encoding: responses include a `meta.nextCursor` opaque string that callers pass as `?cursor=` on the next request. Page size is controlled by `?limit=` (default 20, max 100). All list endpoints support `?sort=` and `?order=asc|desc` query parameters.

## Authentication and Authorization

All endpoints except `GET /events` (public browse) and `GET /events/{id}` (public detail) require a Bearer JWT in the `Authorization` header. JWTs are issued by the platform's Auth Service (Auth0 or Keycloak) and contain a `roles` claim and a `sub` claim identifying the user.

| Scope | Claim | Granted to | Permitted operations |
|---|---|---|---|
| `organizer` | `roles: ["organizer"]` | Verified organizer accounts | Create/edit/publish/cancel events, manage ticket types, view sales reports, approve refunds |
| `attendee` | `roles: ["attendee"]` | Any authenticated end-user | Browse events, place orders, view own tickets, request refunds |
| `staff` | `roles: ["staff"]` | Gate/venue staff assigned via event_staff | Access check-in endpoints, download manifest, scan tickets |
| `admin` | `roles: ["admin"]` | Platform operators | All operations including force-approve refunds and payout overrides |

The API Gateway validates the JWT signature and expiry before forwarding the request. Services trust the gateway and read the decoded `X-User-Id`, `X-User-Roles`, and `X-Organizer-Id` headers injected by the gateway — they do not re-validate the token.

## API Versioning

URL versioning is used: `/api/v1/`. When a breaking change is required, a new version path (`/api/v2/`) is introduced and the old version is maintained for a minimum of 12 months with a `Sunset` response header indicating the deprecation date. Non-breaking additions (new optional fields, new endpoints) are made in-place without a version bump.

## Event Endpoints

### POST /api/v1/events

Creates a new event in `DRAFT` status. Requires `organizer` scope.

**Request**
```json
{
  "title": "ElectroPulse Festival 2025",
  "description": "Three-stage outdoor electronic music festival.",
  "venueId": "f3a1c2d4-...",
  "startAt": "2025-08-15T18:00:00Z",
  "endAt": "2025-08-16T02:00:00Z",
  "timezone": "America/Los_Angeles",
  "maxCapacity": 5000,
  "isOnline": false,
  "coverImageUrl": "https://cdn.example.com/events/electropulse-2025.jpg"
}
```

**Response — 201 Created**
```json
{
  "data": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "title": "ElectroPulse Festival 2025",
    "status": "DRAFT",
    "organizerId": "9988aabb-...",
    "createdAt": "2025-01-10T12:00:00Z",
    "updatedAt": "2025-01-10T12:00:00Z"
  }
}
```

### GET /api/v1/events

Publicly browsable. Supports filters: `?status=PUBLISHED`, `?venueId=`, `?startAfter=`, `?startBefore=`, `?organizerId=`, `?q=` (full-text search on title).

**Response — 200 OK**
```json
{
  "data": [
    {
      "id": "a1b2c3d4-...",
      "title": "ElectroPulse Festival 2025",
      "startAt": "2025-08-15T18:00:00Z",
      "status": "PUBLISHED",
      "coverImageUrl": "https://cdn.example.com/...",
      "venue": { "name": "Shoreline Amphitheatre", "city": "Mountain View" }
    }
  ],
  "meta": { "total": 142, "limit": 20, "nextCursor": "eyJpZCI6Ii4uLiJ9" }
}
```

### GET /api/v1/events/{id}

Public. Returns full event detail including ticket types.

### PATCH /api/v1/events/{id}

Partial update. Organizer scope. Immutable fields when `status != DRAFT`: `venueId`, `startAt`, `endAt`.

**Request**
```json
{ "title": "ElectroPulse Festival 2025 — Sold Out Edition", "coverImageUrl": "https://cdn.example.com/new.jpg" }
```

**Response — 200 OK** — returns updated event object.

### DELETE /api/v1/events/{id}

Soft-delete. Only allowed when `status = DRAFT`. Organizer scope.

### POST /api/v1/events/{id}/publish

Transitions event from `DRAFT` → `PUBLISHED`. Validates that at least one active ticket type exists. Organizer scope.

**Response — 200 OK**
```json
{ "data": { "id": "a1b2c3d4-...", "status": "PUBLISHED", "updatedAt": "2025-01-11T09:30:00Z" } }
```

### POST /api/v1/events/{id}/cancel

Transitions event to `CANCELLED`. Triggers async job to issue full refunds for all confirmed orders. Organizer or admin scope.

**Request**
```json
{ "reason": "Venue permit revoked due to weather emergency." }
```

**Response — 200 OK** — returns event with `status: CANCELLED`.

## Ticket Type Endpoints

### POST /api/v1/events/{id}/ticket-types

Creates a ticket type for the event. Organizer scope. Event must not be `CANCELLED` or `COMPLETED`.

**Request**
```json
{
  "name": "General Admission",
  "description": "Standing room access to all three stages.",
  "basePrice": 79.00,
  "currency": "USD",
  "quantity": 3000,
  "maxPerOrder": 8,
  "saleStartAt": "2025-02-01T00:00:00Z",
  "saleEndAt": "2025-08-15T16:00:00Z",
  "sortOrder": 1
}
```

**Response — 201 Created**
```json
{
  "data": {
    "id": "tt-aabb-1234-...",
    "name": "General Admission",
    "basePrice": 79.00,
    "currentPrice": 79.00,
    "currency": "USD",
    "quantity": 3000,
    "quantitySold": 0,
    "status": "ACTIVE"
  }
}
```

### GET /api/v1/events/{id}/ticket-types

Returns all non-archived ticket types for the event. Public endpoint; hidden types are excluded for non-organizer callers.

### PATCH /api/v1/ticket-types/{id}

Updates ticket type. Organizer scope. `quantity` may only be increased if `quantitySold + quantityHeld < new quantity`.

**Request**
```json
{ "quantity": 3500, "saleEndAt": "2025-08-15T18:00:00Z" }
```

**Response — 200 OK** — returns updated ticket type.

## Order Endpoints

### POST /api/v1/orders

Initiates a new order. Binds an existing hold. Creates a Stripe PaymentIntent. Returns the `clientSecret` for frontend confirmation. Attendee scope.

**Request**
```json
{
  "eventId": "a1b2c3d4-...",
  "holdId": "hold-redis-abc123",
  "couponCode": "EARLY20",
  "attendee": {
    "firstName": "Maya",
    "lastName": "Chen",
    "email": "maya.chen@example.com",
    "phone": "+14155551234"
  }
}
```

**Response — 201 Created**
```json
{
  "data": {
    "id": "ord-1122-...",
    "status": "PENDING",
    "subtotal": 158.00,
    "discountAmount": 31.60,
    "platformFee": 12.51,
    "totalAmount": 138.91,
    "currency": "USD",
    "stripeClientSecret": "pi_3O...._secret_...",
    "expiresAt": "2025-01-10T12:15:00Z",
    "lineItems": [
      { "ticketTypeName": "General Admission", "quantity": 2, "unitPrice": 79.00, "subtotal": 158.00 }
    ]
  }
}
```

### GET /api/v1/orders/{id}

Returns order detail including line items and issued tickets. Attendee may only fetch their own; organizer may fetch orders for their events.

### POST /api/v1/orders/{id}/confirm

Called by the frontend after Stripe payment confirmation succeeds. Triggers ticket issuance and confirmation email.

**Request**
```json
{ "paymentIntentId": "pi_3O...." }
```

**Response — 200 OK**
```json
{
  "data": {
    "id": "ord-1122-...",
    "status": "CONFIRMED",
    "confirmedAt": "2025-01-10T12:03:44Z",
    "tickets": [
      { "id": "tkt-aaaa-...", "qrCode": "EVT2025-AAAA-BBBB", "attendeeName": "Maya Chen" },
      { "id": "tkt-bbbb-...", "qrCode": "EVT2025-CCCC-DDDD", "attendeeName": "Maya Chen" }
    ]
  }
}
```

### POST /api/v1/orders/{id}/cancel

Cancels a `PENDING` order and releases the inventory hold. Attendee scope (before confirmation); admin scope (after confirmation).

**Response — 200 OK** — returns order with `status: CANCELLED`.

## Ticket Hold Endpoints

### POST /api/v1/holds

Acquires a Redis-backed inventory lock for the requested ticket types. TTL is 10 minutes. Should be called immediately when an attendee selects quantities before checkout.

**Request**
```json
{
  "eventId": "a1b2c3d4-...",
  "items": [
    { "ticketTypeId": "tt-aabb-1234-...", "quantity": 2 }
  ],
  "sessionId": "sess-user-xyz-9876"
}
```

**Response — 201 Created**
```json
{
  "data": {
    "holdId": "hold-redis-abc123",
    "expiresAt": "2025-01-10T12:10:00Z",
    "items": [
      { "ticketTypeId": "tt-aabb-1234-...", "quantity": 2, "unitPrice": 79.00 }
    ]
  }
}
```

### DELETE /api/v1/holds/{id}

Explicitly releases a hold before the TTL expires (e.g., user abandons checkout). Returns `204 No Content`.

## Check-In Endpoints

### POST /api/v1/checkin/scan

Validates a QR code scan at the gate. Returns `ADMITTED`, `ALREADY_SCANNED`, `INVALID`, or `CANCELLED` result. Staff scope.

**Request**
```json
{
  "qrCode": "EVT2025-AAAA-BBBB",
  "deviceId": "device-gate1-...",
  "eventId": "a1b2c3d4-...",
  "scannedAt": "2025-08-15T18:47:22Z",
  "latitude": 37.4419,
  "longitude": -122.1430
}
```

**Response — 200 OK**
```json
{
  "data": {
    "result": "ADMITTED",
    "ticket": {
      "id": "tkt-aaaa-...",
      "ticketTypeName": "General Admission",
      "attendeeName": "Maya Chen",
      "photoUrl": null
    },
    "checkInId": "ci-zz99-...",
    "scannedAt": "2025-08-15T18:47:22Z"
  }
}
```

### GET /api/v1/events/{id}/checkin/manifest

Downloads the full attendee manifest as a JSON array for offline use. Staff scope. Manifest includes all valid tickets with QR codes and attendee names.

**Response — 200 OK**
```json
{
  "data": {
    "eventId": "a1b2c3d4-...",
    "generatedAt": "2025-08-15T17:00:00Z",
    "totalTickets": 4832,
    "tickets": [
      { "qrCode": "EVT2025-AAAA-BBBB", "attendeeName": "Maya Chen", "ticketType": "GA", "status": "VALID" }
    ]
  }
}
```

### POST /api/v1/checkin/sync

Batch-uploads offline scans recorded while the device was disconnected. Deduplication is applied server-side. Staff scope.

**Request**
```json
{
  "deviceId": "device-gate1-...",
  "scans": [
    { "qrCode": "EVT2025-AAAA-BBBB", "scannedAt": "2025-08-15T19:02:11Z", "localId": "local-001" }
  ]
}
```

**Response — 200 OK**
```json
{
  "data": {
    "accepted": 1,
    "duplicates": 0,
    "invalid": 0,
    "results": [
      { "localId": "local-001", "status": "ACCEPTED", "checkInId": "ci-zz99-..." }
    ]
  }
}
```

## Refund Endpoints

### POST /api/v1/refunds

Submits a refund request. Attendee scope. Eligibility is checked against the event's refund policy.

**Request**
```json
{
  "orderId": "ord-1122-...",
  "ticketId": "tkt-aaaa-...",
  "reason": "Unable to attend due to travel cancellation."
}
```

**Response — 201 Created**
```json
{
  "data": {
    "id": "ref-5566-...",
    "status": "PENDING",
    "amount": 69.46,
    "currency": "USD",
    "requestedAt": "2025-07-20T10:00:00Z"
  }
}
```

### GET /api/v1/refunds/{id}

Returns refund status and details. Attendee (own) or organizer (for their event) scope.

### PATCH /api/v1/refunds/{id}/approve

Approves a pending refund and triggers Stripe refund processing. Organizer or admin scope.

**Request**
```json
{ "reviewNote": "Verified — within 30-day policy window." }
```

**Response — 200 OK**
```json
{
  "data": {
    "id": "ref-5566-...",
    "status": "PROCESSED",
    "stripeRefundId": "re_3O....",
    "resolvedAt": "2025-07-20T11:15:00Z"
  }
}
```

## Error Response Format

All errors follow a standard envelope regardless of HTTP status code.

```json
{
  "error": {
    "code": "HOLD_EXPIRED",
    "message": "The ticket hold has expired. Please restart the checkout process.",
    "details": [
      {
        "field": "holdId",
        "issue": "Hold hold-redis-abc123 expired at 2025-01-10T12:10:00Z"
      }
    ],
    "requestId": "req-99aabb-...",
    "timestamp": "2025-01-10T12:11:04Z"
  }
}
```

| HTTP Status | When Used |
|---|---|
| `400 Bad Request` | Validation failure — missing fields, constraint violations |
| `401 Unauthorized` | Missing or invalid JWT |
| `403 Forbidden` | Valid JWT but insufficient scope |
| `404 Not Found` | Resource does not exist or is not visible to caller |
| `409 Conflict` | State conflict — e.g., publishing an event with no ticket types |
| `410 Gone` | Resource existed but is permanently deleted |
| `422 Unprocessable Entity` | Business rule violation — e.g., hold expired, ticket already used |
| `429 Too Many Requests` | Rate limit exceeded; `Retry-After` header included |
| `500 Internal Server Error` | Unexpected server fault; `requestId` for log correlation |

## Rate Limiting

Rate limits are enforced at the API Gateway per authenticated user (JWT `sub`) or per IP for unauthenticated callers. Limits reset on a rolling 60-second window. Response headers `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset` are included on every response.

| Endpoint Category | Limit (per 60 s) | Applies To |
|---|---|---|
| `GET /events`, `GET /events/{id}` | 300 requests | Per IP (unauthenticated) |
| `GET /events/**` (authenticated) | 600 requests | Per user |
| `POST /holds` | 30 requests | Per user |
| `POST /orders` | 10 requests | Per user |
| `POST /orders/{id}/confirm` | 5 requests | Per order (idempotent) |
| `POST /checkin/scan` | 600 requests | Per device token |
| `POST /checkin/sync` | 10 requests | Per device token |
| `POST /refunds` | 5 requests | Per user |
| `POST /events` | 20 requests | Per organizer |
| `POST /events/{id}/publish` | 5 requests | Per organizer |
| Organizer analytics (`GET /analytics/**`) | 120 requests | Per organizer |
