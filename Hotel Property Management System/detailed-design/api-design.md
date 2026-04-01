# Hotel Property Management System — API Design

## Table of Contents
1. [API Design Principles](#1-api-design-principles)
2. [Authentication and Authorisation](#2-authentication-and-authorisation)
3. [Versioning and Deprecation](#3-versioning-and-deprecation)
4. [Reservations API](#4-reservations-api)
5. [Rooms API](#5-rooms-api)
6. [Guests API](#6-guests-api)
7. [Folios API](#7-folios-api)
8. [Housekeeping API](#8-housekeeping-api)
9. [Rate Plans API](#9-rate-plans-api)
10. [OTA Channel API](#10-ota-channel-api)
11. [Error Handling](#11-error-handling)
12. [Rate Limiting](#12-rate-limiting)
13. [Webhook Specifications](#13-webhook-specifications)

---

## 1. API Design Principles

The HPMS REST API follows RESTful conventions with pragmatic adjustments for the hospitality domain. The following principles govern all API design decisions.

**Resource-Oriented Design:** URLs represent nouns (resources), not verbs. State transitions are modelled as sub-resource actions (e.g., `POST /reservations/{id}/check-in`) when they do not map cleanly to CRUD.

**Consistent JSON Structure:** All responses use a consistent envelope. Success responses return the resource directly (no wrapper) for single-resource endpoints, and a paginated envelope for list endpoints. Error responses always use the Problem Details format (RFC 7807).

**Idempotency:** All mutating operations (`POST` for state transitions, `PUT`) accept an `Idempotency-Key` header (UUID v4). The server stores results for 24 hours and replays the original response on duplicate requests.

**HATEOAS-Lite:** Responses include a `_links` object with relevant next-action links to reduce client coupling to URL patterns.

**Field Naming:** `camelCase` for JSON fields throughout. Dates use ISO 8601 (`YYYY-MM-DD`). Timestamps use ISO 8601 UTC (`YYYY-MM-DDTHH:mm:ssZ`). Currency amounts are integers in the smallest currency unit (cents/pence) with a separate `currency` field (ISO 4217).

**Pagination:** List endpoints use cursor-based pagination with `cursor` and `limit` query parameters, returning `nextCursor` in the response envelope.

**Partial Responses:** `GET` endpoints support `?fields=field1,field2` to return only requested fields (reduces payload for mobile clients).

---

## 2. Authentication and Authorisation

### 2.1 JWT Bearer Token Authentication

All API endpoints require a valid JWT Bearer token in the `Authorization` header:

```
Authorization: Bearer <token>
```

Tokens are issued by the HPMS Identity Service (OAuth 2.0 / OIDC). Tokens expire after 1 hour. Refresh tokens are valid for 30 days.

**Token Claims:**
```json
{
  "sub": "user-uuid",
  "iss": "https://auth.hpms.example.com",
  "aud": "hpms-api",
  "exp": 1720000000,
  "iat": 1719996400,
  "propertyIds": ["prop-uuid-1", "prop-uuid-2"],
  "scopes": ["hotel:read", "hotel:write"],
  "role": "FRONT_DESK"
}
```

### 2.2 Scopes

| Scope | Description | Typical Roles |
|---|---|---|
| `hotel:read` | Read reservations, rooms, guests, folios | All staff |
| `hotel:write` | Create/modify reservations, check-in/out | Front Desk, Reservations |
| `housekeeping:write` | Update housekeeping task status | Housekeeping staff |
| `revenue:write` | Post charges, apply payments, close folios | Front Desk, Revenue |
| `admin` | Property configuration, rate plan management | Revenue Manager, Admin |
| `channel:write` | OTA/channel manager integration | System accounts only |

### 2.3 Property-Level Access Control

The `propertyIds` claim in the JWT limits access to reservations, rooms, and folios belonging to those properties. Attempting to access a resource belonging to a property not in the token's `propertyIds` returns `403 Forbidden`.

### 2.4 OTA System Accounts

OTA integrations use client-credentials flow. The access token has the `channel:write` scope and a single `propertyId`. Webhook payloads are additionally verified via HMAC-SHA256 signature (see Section 13).

---

## 3. Versioning and Deprecation

**URL Versioning:** The API version is embedded in the URL path (`/v1/`). This provides clear, explicit versioning visible in logs and browser history.

**Minor Changes** (backward compatible: new optional fields, new endpoints) are made within the same major version without a version bump.

**Breaking Changes** (field removal, type changes, semantic changes) require a new major version (`/v2/`). Both versions are supported in parallel for a minimum of 12 months.

**Deprecation Headers:** Deprecated endpoints return:
```
Deprecation: true
Sunset: Sat, 01 Jan 2026 00:00:00 GMT
Link: <https://docs.hpms.example.com/migration/v1-v2>; rel="deprecation"
```

---

## 4. Reservations API

Base path: `/v1/reservations`
Required scope: `hotel:read` (GET), `hotel:write` (POST/PUT/DELETE/actions)

---

### POST /v1/reservations

Creates a new reservation. Validates availability and rate plan before confirming. Returns `409 Conflict` if the requested room type is no longer available.

**Request Headers:**
```
Idempotency-Key: <uuid-v4>
```

**Request Body:**
```json
{
  "propertyId": "string (uuid, required)",
  "roomTypeId": "string (uuid, required)",
  "checkInDate": "string (YYYY-MM-DD, required)",
  "checkOutDate": "string (YYYY-MM-DD, required)",
  "ratePlanCode": "string (required) — e.g. BAR, RACK, CORP-IBM",
  "adults": "integer (min 1, required)",
  "children": "integer (min 0, default 0)",
  "guestId": "string (uuid, optional) — existing guest profile",
  "guest": {
    "firstName": "string (required if guestId not provided)",
    "lastName": "string (required if guestId not provided)",
    "email": "string (email format, required)",
    "phone": "string (E.164 format, optional)",
    "nationality": "string (ISO 3166-1 alpha-2, optional)"
  },
  "channelCode": "string (optional, default DIRECT) — WEB, OTA_BOOKING, GDS, PHONE",
  "specialRequests": "string (max 500 chars, optional)",
  "guaranteeType": "string (required) — CC_GUARANTEE, DEPOSIT, DIRECT_BILL",
  "cardToken": "string (required if guaranteeType=CC_GUARANTEE)",
  "corporateId": "string (optional) — links to corporate profile",
  "groupBlockId": "string (uuid, optional) — allocates from group block"
}
```

**Response Body (201 Created):**
```json
{
  "reservationId": "string (uuid)",
  "confirmationNumber": "string — e.g. HPMS-2024-087423",
  "status": "string — CONFIRMED",
  "propertyId": "string (uuid)",
  "roomTypeId": "string (uuid)",
  "roomTypeName": "string — e.g. Deluxe King",
  "assignedRoomNumber": "string or null — assigned at check-in",
  "checkInDate": "string (YYYY-MM-DD)",
  "checkOutDate": "string (YYYY-MM-DD)",
  "nights": "integer",
  "adults": "integer",
  "children": "integer",
  "guestId": "string (uuid)",
  "guestName": "string — full name",
  "ratePlanCode": "string",
  "ratePlanName": "string",
  "pricing": {
    "nightlyRates": [
      { "date": "YYYY-MM-DD", "amountCents": "integer", "currency": "string" }
    ],
    "totalRoomRevenueCents": "integer",
    "totalTaxCents": "integer",
    "totalAmountCents": "integer",
    "currency": "string (ISO 4217)"
  },
  "cancellationPolicy": {
    "description": "string",
    "freeCancellationBefore": "string (ISO 8601 timestamp or null)",
    "penaltyAmountCents": "integer"
  },
  "channelCode": "string",
  "specialRequests": "string or null",
  "createdAt": "string (ISO 8601 UTC)",
  "_links": {
    "self": { "href": "/v1/reservations/{id}" },
    "checkIn": { "href": "/v1/reservations/{id}/check-in" },
    "modify": { "href": "/v1/reservations/{id}" },
    "cancel": { "href": "/v1/reservations/{id}" }
  }
}
```

**Status Codes:**
| Code | Meaning |
|---|---|
| `201 Created` | Reservation confirmed |
| `400 Bad Request` | Validation error (missing fields, invalid dates) |
| `401 Unauthorized` | Missing or expired token |
| `403 Forbidden` | Insufficient scope or property access |
| `409 Conflict` | Room type no longer available for requested dates |
| `422 Unprocessable Entity` | Business rule violation (BR-001 minimum stay, BR-003 guarantee required) |
| `429 Too Many Requests` | Rate limit exceeded |

---

### GET /v1/reservations/{id}

Retrieves full details of a single reservation.

**Path Parameters:**
- `id` (uuid, required): Reservation ID

**Response Body (200 OK):** Same schema as POST 201 response, with additional fields:
```json
{
  "...all fields from create response...",
  "modifiedAt": "string (ISO 8601 UTC)",
  "cancelledAt": "string (ISO 8601 UTC) or null",
  "cancellationReason": "string or null",
  "checkedInAt": "string (ISO 8601 UTC) or null",
  "checkedOutAt": "string (ISO 8601 UTC) or null",
  "folioId": "string (uuid) or null",
  "roomNumber": "string or null",
  "notes": "string or null"
}
```

**Status Codes:** `200`, `401`, `403`, `404`

---

### PUT /v1/reservations/{id}

Modifies an existing confirmed reservation (dates, room type, guest count, special requests). Cannot modify a reservation that is `CHECKED_IN`, `CHECKED_OUT`, or `CANCELLED`.

**Request Body (all fields optional; only include fields to change):**
```json
{
  "checkInDate": "string (YYYY-MM-DD)",
  "checkOutDate": "string (YYYY-MM-DD)",
  "roomTypeId": "string (uuid)",
  "adults": "integer",
  "children": "integer",
  "specialRequests": "string",
  "ratePlanCode": "string"
}
```

**Response Body (200 OK):** Full reservation object (same as GET).

**Status Codes:** `200`, `400`, `401`, `403`, `404`, `409` (new room type unavailable), `422` (business rule violation)

---

### DELETE /v1/reservations/{id}

Cancels a reservation. Applies cancellation penalty rules. A cancellation reason is required.

**Query Parameters:**
- `reason` (string, required): Reason code — `GUEST_REQUEST`, `NO_SHOW`, `DUPLICATE`, `RATE_ISSUE`, `OTHER`
- `reasonNote` (string, optional): Free-text note (max 200 chars)

**Response Body (200 OK):**
```json
{
  "reservationId": "string (uuid)",
  "confirmationNumber": "string",
  "status": "CANCELLED",
  "cancelledAt": "string (ISO 8601 UTC)",
  "cancellationReason": "string",
  "penaltyApplied": "boolean",
  "penaltyAmountCents": "integer"
}
```

**Status Codes:** `200`, `401`, `403`, `404`, `422` (cannot cancel checked-out reservation)

---

### POST /v1/reservations/{id}/check-in

Initiates check-in for a reservation. Assigns a room, captures or verifies guarantee, opens a folio.

**Request Body:**
```json
{
  "roomNumber": "string (required) — physical room assigned",
  "idDocument": {
    "type": "string — PASSPORT, NATIONAL_ID, DRIVERS_LICENSE",
    "number": "string",
    "expiryDate": "string (YYYY-MM-DD)",
    "issuingCountry": "string (ISO 3166-1 alpha-2)"
  },
  "additionalGuests": [
    {
      "firstName": "string",
      "lastName": "string",
      "nationality": "string (ISO 3166-1 alpha-2)"
    }
  ],
  "preAuthAmountCents": "integer (optional) — pre-authorisation amount"
}
```

**Response Body (200 OK):**
```json
{
  "reservationId": "string (uuid)",
  "confirmationNumber": "string",
  "status": "CHECKED_IN",
  "roomNumber": "string",
  "checkedInAt": "string (ISO 8601 UTC)",
  "folioId": "string (uuid)",
  "preAuthorizationId": "string or null",
  "keyCardInstructions": "string — e.g. your room is ready on floor 4",
  "_links": {
    "folio": { "href": "/v1/folios/{folioId}" },
    "checkOut": { "href": "/v1/reservations/{id}/check-out" }
  }
}
```

**Status Codes:** `200`, `400`, `401`, `403`, `404`, `409` (room already occupied), `422` (reservation not in CONFIRMED state)

---

### POST /v1/reservations/{id}/check-out

Initiates check-out. Triggers final charge posting and folio settlement.

**Request Body:**
```json
{
  "settleBalance": "boolean (default true)",
  "paymentMethod": "string (optional) — CARD_ON_FILE, CASH, DIRECT_BILL",
  "invoiceEmail": "string (email, optional) — override invoice email"
}
```

**Response Body (200 OK):**
```json
{
  "reservationId": "string (uuid)",
  "confirmationNumber": "string",
  "status": "CHECKED_OUT",
  "checkedOutAt": "string (ISO 8601 UTC)",
  "folioId": "string (uuid)",
  "totalChargesCents": "integer",
  "totalPaymentsCents": "integer",
  "balanceCents": "integer",
  "invoiceUrl": "string (pre-signed URL, valid 24 hours)"
}
```

**Status Codes:** `200`, `401`, `403`, `404`, `422` (unsettled balance when settleBalance=false)

---

### GET /v1/reservations

Search and filter reservations with pagination.

**Query Parameters:**
| Parameter | Type | Description |
|---|---|---|
| `propertyId` | uuid | Filter by property (required unless `admin` scope) |
| `checkInDate` | YYYY-MM-DD | Filter by check-in date |
| `checkOutDate` | YYYY-MM-DD | Filter by check-out date |
| `status` | string | `CONFIRMED`, `CHECKED_IN`, `CHECKED_OUT`, `CANCELLED`, `NO_SHOW` |
| `guestName` | string | Partial name search (min 3 chars) |
| `confirmationNumber` | string | Exact match |
| `channelCode` | string | Filter by booking channel |
| `cursor` | string | Pagination cursor |
| `limit` | integer | Results per page (default 20, max 100) |

**Response Body (200 OK):**
```json
{
  "data": [
    {
      "reservationId": "string (uuid)",
      "confirmationNumber": "string",
      "status": "string",
      "guestName": "string",
      "roomTypeName": "string",
      "roomNumber": "string or null",
      "checkInDate": "string",
      "checkOutDate": "string",
      "nights": "integer",
      "totalAmountCents": "integer",
      "currency": "string",
      "channelCode": "string"
    }
  ],
  "pagination": {
    "limit": "integer",
    "nextCursor": "string or null",
    "totalCount": "integer"
  }
}
```

**Status Codes:** `200`, `400`, `401`, `403`

---

## 5. Rooms API

Base path: `/v1/rooms`
Required scope: `hotel:read` (GET), `hotel:write` (PUT)

---

### GET /v1/rooms

Returns all rooms for a property with current housekeeping and occupancy status.

**Query Parameters:** `propertyId` (uuid, required), `floor` (integer, optional), `roomTypeId` (uuid, optional), `housekeepingStatus` (string, optional)

**Response Body (200 OK):**
```json
{
  "data": [
    {
      "roomId": "string (uuid)",
      "roomNumber": "string",
      "floor": "integer",
      "roomTypeId": "string (uuid)",
      "roomTypeName": "string",
      "occupancyStatus": "string — VACANT, OCCUPIED, OUT_OF_ORDER, OUT_OF_SERVICE",
      "housekeepingStatus": "string — CLEAN, DIRTY, INSPECTED, IN_PROGRESS",
      "bedType": "string — KING, QUEEN, TWIN, DOUBLE",
      "maxOccupancy": "integer",
      "squareMetres": "number",
      "features": ["string — e.g. OCEAN_VIEW, BALCONY, ACCESSIBLE"],
      "currentReservationId": "string (uuid) or null"
    }
  ],
  "pagination": { "limit": "integer", "nextCursor": "string or null", "totalCount": "integer" }
}
```

---

### GET /v1/rooms/{id}

Returns full details of a single room including amenities, photos metadata, and current/next reservation summary.

**Response Body (200 OK):**
```json
{
  "roomId": "string (uuid)",
  "roomNumber": "string",
  "floor": "integer",
  "buildingWing": "string or null",
  "roomTypeId": "string (uuid)",
  "roomTypeName": "string",
  "occupancyStatus": "string",
  "housekeepingStatus": "string",
  "bedType": "string",
  "maxOccupancy": "integer",
  "squareMetres": "number",
  "features": ["string"],
  "amenities": ["string — e.g. MINIBAR, SAFE, BATHTUB, SHOWER, DESK"],
  "connectedRoomNumber": "string or null",
  "isAccessible": "boolean",
  "currentReservation": {
    "reservationId": "string (uuid) or null",
    "guestName": "string or null",
    "checkOutDate": "string or null"
  },
  "nextArrival": {
    "reservationId": "string (uuid) or null",
    "guestName": "string or null",
    "checkInDate": "string or null"
  }
}
```

**Status Codes:** `200`, `401`, `403`, `404`

---

### PUT /v1/rooms/{id}/status

Updates the housekeeping or occupancy status of a room.

**Request Body:**
```json
{
  "housekeepingStatus": "string (optional) — CLEAN, DIRTY, INSPECTED, IN_PROGRESS",
  "occupancyStatus": "string (optional) — VACANT, OUT_OF_ORDER, OUT_OF_SERVICE",
  "outOfOrderReason": "string (required if occupancyStatus=OUT_OF_ORDER)",
  "outOfOrderUntil": "string (YYYY-MM-DD, optional)",
  "notes": "string (optional, max 200 chars)"
}
```

**Response Body (200 OK):**
```json
{
  "roomId": "string (uuid)",
  "roomNumber": "string",
  "occupancyStatus": "string",
  "housekeepingStatus": "string",
  "updatedAt": "string (ISO 8601 UTC)"
}
```

**Status Codes:** `200`, `400`, `401`, `403`, `404`

---

### GET /v1/rooms/availability

Returns available room types and counts for a given stay period.

**Query Parameters:**
| Parameter | Type | Required | Description |
|---|---|---|---|
| `propertyId` | uuid | Yes | Property to query |
| `checkIn` | YYYY-MM-DD | Yes | Arrival date |
| `checkOut` | YYYY-MM-DD | Yes | Departure date |
| `roomTypeId` | uuid | No | Filter to specific room type |
| `adults` | integer | No | Number of adults (default 2) |
| `children` | integer | No | Number of children (default 0) |

**Response Body (200 OK):**
```json
{
  "propertyId": "string (uuid)",
  "checkIn": "string (YYYY-MM-DD)",
  "checkOut": "string (YYYY-MM-DD)",
  "roomTypes": [
    {
      "roomTypeId": "string (uuid)",
      "roomTypeName": "string",
      "bedType": "string",
      "maxOccupancy": "integer",
      "availableCount": "integer",
      "lowestRateCents": "integer",
      "currency": "string",
      "features": ["string"],
      "thumbnailUrl": "string"
    }
  ]
}
```

**Status Codes:** `200`, `400` (invalid date range), `401`, `403`

---

## 6. Guests API

Base path: `/v1/guests`
Required scope: `hotel:read` (GET), `hotel:write` (POST/PUT)

---

### POST /v1/guests

Creates a new guest profile. Deduplication check is performed on email + last name combination before creating.

**Request Body:**
```json
{
  "firstName": "string (required)",
  "lastName": "string (required)",
  "email": "string (email format, required)",
  "phone": "string (E.164 format, optional)",
  "dateOfBirth": "string (YYYY-MM-DD, optional)",
  "nationality": "string (ISO 3166-1 alpha-2, optional)",
  "preferredLanguage": "string (BCP 47, optional — e.g. en-GB, fr-FR)",
  "address": {
    "line1": "string",
    "line2": "string or null",
    "city": "string",
    "stateProvince": "string or null",
    "postalCode": "string",
    "country": "string (ISO 3166-1 alpha-2)"
  },
  "preferences": {
    "bedType": "string or null",
    "floorPreference": "string — HIGH, LOW, MIDDLE or null",
    "smokingPreference": "string — NON_SMOKING, SMOKING",
    "dietaryRequirements": ["string — VEGETARIAN, VEGAN, GLUTEN_FREE, HALAL, KOSHER"],
    "specialNeeds": "string or null"
  },
  "loyaltyNumber": "string (optional)",
  "corporateId": "string (uuid, optional)"
}
```

**Response Body (201 Created):**
```json
{
  "guestId": "string (uuid)",
  "profileNumber": "string — e.g. G-0028761",
  "firstName": "string",
  "lastName": "string",
  "email": "string",
  "phone": "string or null",
  "nationality": "string or null",
  "tier": "string — STANDARD, SILVER, GOLD, PLATINUM (loyalty tier)",
  "preferences": { "...all preference fields..." },
  "createdAt": "string (ISO 8601 UTC)"
}
```

**Status Codes:** `201`, `400`, `401`, `403`, `409` (duplicate guest profile detected — returns existing `guestId`)

---

### GET /v1/guests/{id}

Returns full guest profile including loyalty status and stay statistics.

**Response Body (200 OK):**
```json
{
  "guestId": "string (uuid)",
  "profileNumber": "string",
  "firstName": "string",
  "lastName": "string",
  "email": "string",
  "phone": "string or null",
  "dateOfBirth": "string or null",
  "nationality": "string or null",
  "preferredLanguage": "string",
  "address": { "...address fields..." },
  "preferences": { "...preference fields..." },
  "loyalty": {
    "number": "string or null",
    "tier": "string",
    "lifetimePoints": "integer",
    "currentPoints": "integer",
    "memberSince": "string (YYYY-MM-DD) or null"
  },
  "stayStatistics": {
    "totalStays": "integer",
    "totalNights": "integer",
    "lastStayDate": "string (YYYY-MM-DD) or null",
    "totalRevenueAmountCents": "integer",
    "currency": "string"
  },
  "createdAt": "string",
  "updatedAt": "string"
}
```

**Status Codes:** `200`, `401`, `403`, `404`

---

### PUT /v1/guests/{id}

Updates guest profile fields. Supports partial updates (only send fields to change).

**Request Body:** Same schema as POST but all fields optional.

**Response Body (200 OK):** Same as GET response.

**Status Codes:** `200`, `400`, `401`, `403`, `404`

---

### GET /v1/guests/{id}/reservations

Returns reservation history for a guest.

**Query Parameters:** `status` (string, optional), `cursor` (string), `limit` (integer, default 10)

**Response Body (200 OK):**
```json
{
  "guestId": "string (uuid)",
  "data": [
    {
      "reservationId": "string (uuid)",
      "confirmationNumber": "string",
      "propertyId": "string (uuid)",
      "propertyName": "string",
      "checkInDate": "string",
      "checkOutDate": "string",
      "roomTypeName": "string",
      "totalAmountCents": "integer",
      "currency": "string",
      "status": "string"
    }
  ],
  "pagination": { "limit": "integer", "nextCursor": "string or null", "totalCount": "integer" }
}
```

---

## 7. Folios API

Base path: `/v1/folios`
Required scope: `hotel:read` (GET), `revenue:write` (POST/DELETE)

---

### GET /v1/folios/{id}

Returns the full folio with all charge entries, tax breakdown, and payment history.

**Response Body (200 OK):**
```json
{
  "folioId": "string (uuid)",
  "reservationId": "string (uuid)",
  "guestId": "string (uuid)",
  "guestName": "string",
  "propertyId": "string (uuid)",
  "status": "string — OPEN, CLOSED",
  "openedAt": "string (ISO 8601 UTC)",
  "closedAt": "string or null",
  "currency": "string (ISO 4217)",
  "charges": [
    {
      "chargeId": "string (uuid)",
      "date": "string (YYYY-MM-DD)",
      "description": "string",
      "chargeCode": "string — e.g. ROOM_RATE, FB_RESTAURANT, SPA, PARKING",
      "amountCents": "integer",
      "taxBreakdown": [
        { "taxCode": "string", "taxName": "string", "rate": "number", "amountCents": "integer" }
      ],
      "totalWithTaxCents": "integer",
      "status": "string — ACTIVE, VOIDED",
      "voidReason": "string or null",
      "postedBy": "string (userId)",
      "postedAt": "string (ISO 8601 UTC)"
    }
  ],
  "payments": [
    {
      "paymentId": "string (uuid)",
      "method": "string — CREDIT_CARD, CASH, DIRECT_BILL, LOYALTY_POINTS",
      "amountCents": "integer",
      "cardLast4": "string or null",
      "cardBrand": "string or null",
      "transactionId": "string or null",
      "appliedAt": "string (ISO 8601 UTC)"
    }
  ],
  "summary": {
    "totalChargesCents": "integer",
    "totalTaxCents": "integer",
    "totalPaymentsCents": "integer",
    "balanceCents": "integer"
  }
}
```

---

### POST /v1/folios/{id}/charges

Posts a new charge to an open folio.

**Request Headers:** `Idempotency-Key: <uuid-v4>`

**Request Body:**
```json
{
  "date": "string (YYYY-MM-DD, required)",
  "chargeCode": "string (required) — charge code from chart of accounts",
  "description": "string (required, max 100 chars)",
  "amountCents": "integer (required, > 0)",
  "quantity": "integer (default 1)",
  "departmentCode": "string (optional) — e.g. RESTAURANT, SPA, MINIBAR",
  "notes": "string (optional)"
}
```

**Response Body (201 Created):**
```json
{
  "chargeId": "string (uuid)",
  "folioId": "string (uuid)",
  "date": "string",
  "description": "string",
  "chargeCode": "string",
  "amountCents": "integer",
  "taxBreakdown": [ { "taxCode": "string", "taxName": "string", "amountCents": "integer" } ],
  "totalWithTaxCents": "integer",
  "status": "ACTIVE",
  "postedAt": "string (ISO 8601 UTC)"
}
```

**Status Codes:** `201`, `400`, `401`, `403`, `404`, `422` (folio not open)

---

### DELETE /v1/folios/{id}/charges/{chargeId}

Voids a charge entry. Does not delete — creates a compensating void record and marks the original as VOIDED.

**Query Parameters:** `reason` (string, required), `reasonNote` (string, optional, max 200 chars)

**Response Body (200 OK):**
```json
{
  "chargeId": "string (uuid)",
  "status": "VOIDED",
  "voidedAt": "string (ISO 8601 UTC)",
  "voidReason": "string",
  "voidedBy": "string (userId)"
}
```

**Status Codes:** `200`, `400`, `401`, `403`, `404`, `422` (charge already voided)

---

### POST /v1/folios/{id}/payments

Applies a payment to a folio.

**Request Headers:** `Idempotency-Key: <uuid-v4>`

**Request Body:**
```json
{
  "method": "string (required) — CREDIT_CARD, CASH, DIRECT_BILL, LOYALTY_POINTS",
  "amountCents": "integer (required, > 0)",
  "cardToken": "string (required if method=CREDIT_CARD)",
  "directBillAccountId": "string (uuid, required if method=DIRECT_BILL)",
  "loyaltyPointsToRedeem": "integer (optional, required if method=LOYALTY_POINTS)",
  "notes": "string (optional)"
}
```

**Response Body (201 Created):**
```json
{
  "paymentId": "string (uuid)",
  "folioId": "string (uuid)",
  "method": "string",
  "amountCents": "integer",
  "cardLast4": "string or null",
  "cardBrand": "string or null",
  "transactionId": "string (gateway transaction ID) or null",
  "appliedAt": "string (ISO 8601 UTC)",
  "newBalanceCents": "integer"
}
```

**Status Codes:** `201`, `400`, `401`, `403`, `404`, `422` (payment exceeds balance, folio closed), `502` (payment gateway error)

---

### POST /v1/folios/{id}/close

Closes the folio. Requires zero balance or explicit `allowOutstandingBalance: true` for direct-bill accounts.

**Request Body:**
```json
{
  "allowOutstandingBalance": "boolean (default false)",
  "invoiceEmail": "string (email, optional)",
  "invoiceFormat": "string — PDF, XML (default PDF)"
}
```

**Response Body (200 OK):**
```json
{
  "folioId": "string (uuid)",
  "status": "CLOSED",
  "closedAt": "string (ISO 8601 UTC)",
  "invoiceUrl": "string (pre-signed URL, valid 24 hours)",
  "invoiceNumber": "string — e.g. INV-2024-087423",
  "finalBalanceCents": "integer"
}
```

**Status Codes:** `200`, `400`, `401`, `403`, `404`, `422` (outstanding balance, already closed)

---

### GET /v1/folios/{id}/invoice

Downloads the invoice for a closed folio.

**Query Parameters:** `format` (string, optional — `PDF` or `XML`, default `PDF`)

**Response:** Binary PDF stream with `Content-Type: application/pdf` and `Content-Disposition: attachment; filename="invoice-{number}.pdf"`, or XML string.

**Status Codes:** `200`, `401`, `403`, `404`, `422` (folio not yet closed)

---

## 8. Housekeeping API

Base path: `/v1/housekeeping`
Required scope: `hotel:read` (GET), `housekeeping:write` (POST/PUT)

---

### GET /v1/housekeeping/tasks

Returns housekeeping tasks with filtering.

**Query Parameters:**
| Parameter | Type | Description |
|---|---|---|
| `propertyId` | uuid | Required unless admin scope |
| `assignedTo` | uuid | Filter by staff member user ID |
| `status` | string | `PENDING`, `IN_PROGRESS`, `COMPLETED`, `VERIFIED` |
| `taskType` | string | `DEPARTURE_CLEAN`, `STAYOVER_CLEAN`, `TURNDOWN`, `INSPECTION`, `MAINTENANCE` |
| `floor` | integer | Filter by floor |
| `date` | YYYY-MM-DD | Task date (default today) |
| `cursor` | string | Pagination cursor |
| `limit` | integer | Default 50 |

**Response Body (200 OK):**
```json
{
  "data": [
    {
      "taskId": "string (uuid)",
      "taskType": "string",
      "roomId": "string (uuid)",
      "roomNumber": "string",
      "floor": "integer",
      "status": "string",
      "priority": "string — STANDARD, HIGH, URGENT",
      "assignedToUserId": "string or null",
      "assignedToName": "string or null",
      "scheduledFor": "string (ISO 8601 UTC) or null",
      "startedAt": "string or null",
      "completedAt": "string or null",
      "notes": "string or null",
      "checklistItems": [
        { "item": "string", "completed": "boolean" }
      ]
    }
  ],
  "pagination": { "limit": "integer", "nextCursor": "string or null", "totalCount": "integer" }
}
```

---

### POST /v1/housekeeping/tasks

Creates a housekeeping task manually (auto-tasks are created from reservation events).

**Request Body:**
```json
{
  "propertyId": "string (uuid, required)",
  "roomId": "string (uuid, required)",
  "taskType": "string (required)",
  "priority": "string (optional, default STANDARD)",
  "assignedToUserId": "string (uuid, optional)",
  "scheduledFor": "string (ISO 8601 UTC, optional)",
  "notes": "string (optional)"
}
```

**Response Body (201 Created):** Full task object.

**Status Codes:** `201`, `400`, `401`, `403`

---

### PUT /v1/housekeeping/tasks/{id}/status

Updates the status of a housekeeping task. Triggers room status update on completion.

**Request Body:**
```json
{
  "status": "string (required) — IN_PROGRESS, COMPLETED, VERIFIED",
  "notes": "string (optional)",
  "checklistItems": [
    { "item": "string", "completed": "boolean" }
  ]
}
```

**Response Body (200 OK):** Updated task object.

**Status Codes:** `200`, `400`, `401`, `403`, `404`, `422` (invalid status transition)

---

## 9. Rate Plans API

Base path: `/v1/rate-plans`
Required scope: `hotel:read` (GET), `admin` (POST/PUT)

---

### GET /v1/rate-plans

Returns all rate plans configured for a property.

**Query Parameters:** `propertyId` (uuid, required), `activeOnly` (boolean, default true)

**Response Body (200 OK):**
```json
{
  "data": [
    {
      "ratePlanId": "string (uuid)",
      "code": "string — e.g. BAR, RACK, CORP-IBM",
      "name": "string — e.g. Best Available Rate",
      "type": "string — PUBLIC, NEGOTIATED, PACKAGE, PROMOTION",
      "channelRestrictions": ["string — WEB, OTA_BOOKING, GDS"],
      "isActive": "boolean",
      "cancellationPolicyCode": "string",
      "breakfastIncluded": "boolean"
    }
  ]
}
```

---

### GET /v1/rate-plans/{id}/rates

Returns nightly rate breakdown for a rate plan, room type, and stay period.

**Query Parameters:**
| Parameter | Type | Required | Description |
|---|---|---|---|
| `checkIn` | YYYY-MM-DD | Yes | Arrival date |
| `checkOut` | YYYY-MM-DD | Yes | Departure date |
| `roomTypeId` | uuid | Yes | Room type to price |
| `adults` | integer | No | Default 2 |
| `promotionCode` | string | No | Apply a promotion code |

**Response Body (200 OK):**
```json
{
  "ratePlanId": "string (uuid)",
  "ratePlanCode": "string",
  "roomTypeId": "string (uuid)",
  "roomTypeName": "string",
  "nights": [
    {
      "date": "string (YYYY-MM-DD)",
      "baseRateCents": "integer",
      "currency": "string",
      "restrictions": {
        "closedToArrival": "boolean",
        "closedToDeparture": "boolean",
        "minimumStay": "integer"
      }
    }
  ],
  "totals": {
    "roomRevenueCents": "integer",
    "estimatedTaxCents": "integer",
    "grandTotalCents": "integer",
    "currency": "string"
  },
  "inclusions": ["string — e.g. BREAKFAST, PARKING, WIFI"],
  "cancellationPolicy": {
    "description": "string",
    "freeCancellationBefore": "string (ISO 8601 UTC) or null",
    "penaltyAmountCents": "integer"
  }
}
```

**Status Codes:** `200`, `400`, `401`, `403`, `404`

---

## 10. OTA Channel API

Base path: `/v1/channels`
Required scope: `channel:write`

The OTA Channel API provides an inbound webhook endpoint that channel managers and OTAs post booking notifications to. Payloads are validated for HMAC-SHA256 signature authenticity before processing.

### POST /v1/channels/{channelCode}/bookings

Receives an OTA booking notification. See Section 13 for full webhook payload and signature verification details.

**Path Parameters:** `channelCode` (string, required) — registered channel code (e.g. `OTA_BOOKING`, `EXPEDIA`, `DIRECT_WEB`)

**Response Body (202 Accepted):**
```json
{
  "status": "ACCEPTED",
  "messageId": "string (uuid) — internal trace ID"
}
```

Processing is asynchronous. The OTA should use the confirmation number lookup endpoint to verify reservation creation.

**Status Codes:** `202`, `400` (malformed payload), `401` (invalid HMAC signature), `403`, `409` (duplicate booking ID)

---

## 11. Error Handling

All API errors follow RFC 7807 Problem Details format.

**Error Response Schema:**
```json
{
  "type": "string (URI identifying the error type)",
  "title": "string (human-readable summary)",
  "status": "integer (HTTP status code)",
  "detail": "string (specific error description)",
  "instance": "string (URI of the specific request — e.g. /v1/reservations/xyz)",
  "traceId": "string (distributed trace ID for log correlation)",
  "errors": [
    {
      "field": "string (dot-notation field path for validation errors)",
      "code": "string (machine-readable error code)",
      "message": "string (human-readable message)"
    }
  ]
}
```

**Standard Error Codes:**

| HTTP Status | `type` URI | Common Causes |
|---|---|---|
| `400` | `/errors/invalid-request` | Missing required fields, invalid formats |
| `401` | `/errors/unauthorized` | Missing, expired, or malformed JWT |
| `403` | `/errors/forbidden` | Insufficient scope, property access denied |
| `404` | `/errors/not-found` | Resource does not exist |
| `409` | `/errors/conflict` | Availability conflict, duplicate resource |
| `422` | `/errors/business-rule-violation` | BR-001 minimum stay, BR-003 guarantee, invalid state transition |
| `429` | `/errors/rate-limit-exceeded` | Too many requests |
| `502` | `/errors/upstream-error` | Payment gateway or external service failure |
| `503` | `/errors/service-unavailable` | Planned maintenance or overload |

**Example 422 Response:**
```json
{
  "type": "/errors/business-rule-violation",
  "title": "Business Rule Violation",
  "status": 422,
  "detail": "Reservation violates minimum stay requirement",
  "instance": "/v1/reservations",
  "traceId": "4bf92f3577b34da6a3ce929d0e0e4736",
  "errors": [
    {
      "field": "checkOutDate",
      "code": "BR-001",
      "message": "Minimum stay of 3 nights required for this room type from 2024-12-24 to 2024-12-27"
    }
  ]
}
```

---

## 12. Rate Limiting

Rate limits are applied per API key (system accounts) or per authenticated user (staff tokens).

| Tier | Limit | Window |
|---|---|---|
| Standard (staff users) | 300 requests | 60 seconds |
| Channel / OTA accounts | 1,000 requests | 60 seconds |
| Admin operations | 60 requests | 60 seconds |
| Availability search (`GET /v1/rooms/availability`) | 500 requests | 60 seconds |

Rate limit status is communicated via response headers:
```
X-RateLimit-Limit: 300
X-RateLimit-Remaining: 247
X-RateLimit-Reset: 1720000060
Retry-After: 14  (only on 429 responses)
```

When the rate limit is exceeded:
```json
{
  "type": "/errors/rate-limit-exceeded",
  "title": "Rate Limit Exceeded",
  "status": 429,
  "detail": "You have exceeded 300 requests per 60 seconds. Retry after 14 seconds.",
  "instance": "/v1/reservations",
  "traceId": "..."
}
```

---

## 13. Webhook Specifications

### 13.1 OTA Booking Webhook

OTA partners and channel managers deliver booking notifications via HTTP POST to `/v1/channels/{channelCode}/bookings`. The payload represents a new, modified, or cancelled booking from the external channel.

**POST Payload Schema:**
```json
{
  "messageId": "string (uuid) — OTA's unique message ID (used for idempotency)",
  "messageType": "string — NEW_BOOKING, MODIFICATION, CANCELLATION",
  "channelCode": "string — e.g. OTA_BOOKING, EXPEDIA",
  "channelReservationId": "string — OTA's own reservation reference",
  "propertyExternalCode": "string — OTA's property identifier (mapped to internal propertyId)",
  "booking": {
    "checkInDate": "string (YYYY-MM-DD)",
    "checkOutDate": "string (YYYY-MM-DD)",
    "roomTypeExternalCode": "string — OTA room category code",
    "ratePlanExternalCode": "string — OTA rate code",
    "adults": "integer",
    "children": "integer",
    "totalAmountCents": "integer",
    "currency": "string (ISO 4217)",
    "guest": {
      "firstName": "string",
      "lastName": "string",
      "email": "string",
      "phone": "string or null",
      "nationality": "string (ISO 3166-1 alpha-2) or null"
    },
    "specialRequests": "string or null",
    "guaranteeType": "string — CC_GUARANTEE, DEPOSIT, PAY_AT_PROPERTY",
    "cardToken": "string or null"
  },
  "modification": {
    "originalChannelReservationId": "string (only for MODIFICATION)",
    "modifiedFields": ["string — e.g. checkOutDate, adults"]
  },
  "cancellation": {
    "reason": "string or null (only for CANCELLATION)",
    "penaltyApplied": "boolean"
  }
}
```

### 13.2 HMAC-SHA256 Signature Verification

Every inbound OTA webhook request must include the following headers:

```
X-HPMS-Channel-Code: OTA_BOOKING
X-HPMS-Timestamp: 1720000000
X-HPMS-Signature: sha256=<hex-encoded-HMAC>
```

**Signature Computation:**
```
HMAC_message = channelCode + "." + timestamp + "." + rawRequestBodyString
signature = HMAC-SHA256(sharedSecret, HMAC_message)
header_value = "sha256=" + hex(signature)
```

**Verification Steps:**
1. Extract `X-HPMS-Timestamp` from headers.
2. Reject if `|currentTime - timestamp| > 300 seconds` (replay attack prevention).
3. Recompute `HMAC-SHA256(sharedSecret, channelCode + "." + timestamp + "." + rawBody)`.
4. Compare using constant-time comparison (`MessageDigest.isEqual`) against the header value.
5. Return `401 Unauthorized` with `{"type": "/errors/unauthorized", "detail": "Invalid webhook signature"}` if verification fails.

The `sharedSecret` is a 256-bit random value provisioned per channel during onboarding and stored in the secrets manager (HashiCorp Vault). Secrets are rotated every 90 days with a 24-hour dual-secret overlap window.

### 13.3 Outbound Webhooks (HPMS → Partner Systems)

HPMS can push notification webhooks to registered partner endpoints for the following events:

| Event | Trigger |
|---|---|
| `reservation.confirmed` | New reservation created |
| `reservation.modified` | Reservation dates or details changed |
| `reservation.cancelled` | Reservation cancelled |
| `guest.checked_in` | Guest checked in |
| `guest.checked_out` | Guest checked out with settled folio |

Partner endpoints must respond with `2xx` within 10 seconds. HPMS retries with exponential backoff (up to 5 attempts over 24 hours) for non-2xx responses or timeouts. Outbound webhooks are signed using the same HMAC-SHA256 scheme, with the partner's registered secret.
