# API Design — Payment Orchestration and Wallet Platform

**Base URL:** `https://api.payments.io/v1`  
**API Version:** v1  
**Document Status:** Implementation-Ready  
**Owners:** API Guild, Payments Engineering

---

## Table of Contents

1. [Overview](#1-overview)
   - 1.1 Authentication
   - 1.2 Standard Request Headers
   - 1.3 Idempotency
   - 1.4 Pagination
   - 1.5 Rate Limiting
   - 1.6 Error Response Format
2. [Error Catalog](#2-error-catalog)
3. [API Endpoints](#3-api-endpoints)
   - 3.1 Payment Intents
   - 3.2 Payment Sessions
   - 3.3 Wallets
   - 3.4 Refunds
   - 3.5 Chargebacks
   - 3.6 Payouts
   - 3.7 Settlement Batches
   - 3.8 Payment Methods
   - 3.9 FX Rates
   - 3.10 Webhooks
   - 3.11 Risk
   - 3.12 Reports
   - 3.13 API Keys
4. [Webhook Event Payloads](#4-webhook-event-payloads)
5. [SDK Usage Examples](#5-sdk-usage-examples)

---

## 1. Overview

### 1.1 Authentication

All API requests must carry **both** credentials simultaneously. Either credential alone is rejected with `HTTP 401`.

#### Bearer JWT (`Authorization` header)

A short-lived JSON Web Token (expiry: 1 hour) issued by the Identity service. The token encodes the caller's merchant ID, scopes, and environment (`sandbox` / `production`). Rotate before expiry using the `/auth/token/refresh` endpoint.

```
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

The JWT payload includes:
- `sub` — merchant or service account ID
- `scope` — space-separated permission scopes (e.g., `payments:write wallets:read`)
- `env` — `sandbox` or `production`
- `exp` — Unix timestamp for expiry

#### API Key (`X-API-Key` header)

A static, long-lived secret bound to an environment (`sandbox` or `production`). API keys are created via `POST /api-keys`, stored as a salted hash server-side, and displayed **once** at creation. Treat API keys as secrets — never expose them in client-side code or version control.

```
X-API-Key: pk_live_4xT9mKZqL8nW2pRvBcYdEjUhFs3aGiNo
```

> **Security note:** Sandbox keys (prefixed `pk_test_`) are rejected in the production environment with error `PAY-1024`. Production keys (prefixed `pk_live_`) are never accepted in sandbox.

---

### 1.2 Standard Request Headers

| Header | Required | Description |
|---|---|---|
| `Content-Type` | Yes (mutating) | Must be `application/json` for all POST/PUT/PATCH requests |
| `Authorization` | Yes | `Bearer <JWT>` — short-lived access token |
| `X-API-Key` | Yes | Static API key for the target environment |
| `Idempotency-Key` | Yes (mutating) | Client-generated unique key; see §1.3 |
| `X-Request-ID` | Recommended | Client-generated UUID for distributed tracing; echoed in response as `X-Request-ID` |
| `X-Merchant-ID` | Conditional | Required when operating as a platform on behalf of a sub-merchant |
| `Accept-Language` | Optional | BCP 47 language tag (e.g., `en-US`, `fr-FR`) for localized error messages |

---

### 1.3 Idempotency

All state-mutating operations (`POST`, `PUT`, `DELETE`) **must** include an `Idempotency-Key` header. This ensures that retried requests due to network failures or timeouts do not produce duplicate side effects.

#### Behavior

| Scenario | Behavior |
|---|---|
| First request with key | Processed normally; response cached against key |
| Retry with same key + same body | Returns **cached** response (HTTP status preserved); no re-execution |
| Retry with same key + different body | `HTTP 409` with error code `PAY-1001` |
| Request after 24-hour TTL | Key expired; treated as a new unique request |

#### Key Format

- Type: String (UUID v4 recommended)
- Max length: 64 characters
- Case-sensitive
- Example: `Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000`

#### Collision Handling

If the same `Idempotency-Key` is submitted with a different request body (different `amount`, `currency`, etc.), the API returns:

```json
HTTP/1.1 409 Conflict

{
  "error": {
    "code": "PAY-1001",
    "message": "Idempotency key already used with different parameters.",
    "details": [
      {
        "field": "idempotency_key",
        "issue": "Key '550e8400-e29b-41d4-a716-446655440000' was previously used with amount=5000, currency=USD."
      }
    ],
    "request_id": "req_01HX9K2M4PQRST6UVWXYZ"
  }
}
```

The response includes an `Idempotent-Replayed: true` header on all cache hits.

---

### 1.4 Pagination

All list endpoints use **cursor-based pagination** to ensure stable, consistent pages even as records are inserted or updated.

#### Request Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `limit` | integer | 20 | Number of records per page. Max: 100 |
| `after` | string | — | Opaque cursor pointing to the last record of the previous page |
| `before` | string | — | Opaque cursor for reverse pagination |

#### Response Envelope

```json
{
  "data": [ ... ],
  "next_cursor": "Y3Vyc29yX2V4YW1wbGVfMTIz",
  "prev_cursor": "Y3Vyc29yX2V4YW1wbGVfMDEx",
  "has_more": true,
  "total_count": 1482
}
```

| Field | Description |
|---|---|
| `data` | Array of resource objects for this page |
| `next_cursor` | Base64-encoded cursor to fetch the next page; omitted if `has_more` is `false` |
| `prev_cursor` | Base64-encoded cursor to fetch the previous page |
| `has_more` | `true` if additional records exist beyond this page |
| `total_count` | Total number of records matching the query (may be approximate for large sets) |

> **Note:** Cursors are opaque strings. Do not attempt to decode or construct them. They expire after 24 hours.

---

### 1.5 Rate Limiting

Rate limits are enforced **per API key** on a sliding 60-second window.

| Operation Type | Limit |
|---|---|
| Read operations (`GET`) | 1,000 requests / minute |
| Write operations (`POST`, `PUT`, `DELETE`) | 500 requests / minute |

#### Rate Limit Response Headers

All API responses include the following headers:

| Header | Description |
|---|---|
| `X-RateLimit-Limit` | Maximum requests allowed in the current window |
| `X-RateLimit-Remaining` | Requests remaining in the current window |
| `X-RateLimit-Reset` | Unix timestamp (UTC) when the window resets |

When the limit is exceeded, the API returns `HTTP 429 Too Many Requests`:

```json
{
  "error": {
    "code": "PAY-4290",
    "message": "Rate limit exceeded. Retry after the reset timestamp.",
    "details": [],
    "request_id": "req_01HX9K2M4PQRST6UVWXYZ"
  }
}
```

Use exponential backoff with jitter when retrying after a `429` response.

---

### 1.6 Error Response Format

All errors follow a consistent envelope regardless of HTTP status code.

```json
{
  "error": {
    "code": "PAY-XXXX",
    "message": "Human-readable summary of the error.",
    "details": [
      {
        "field": "amount",
        "issue": "Must be greater than 50 (minimum $0.50).",
        "value": "25"
      }
    ],
    "request_id": "req_01HX9K2M4PQRST6UVWXYZ"
  }
}
```

| Field | Type | Description |
|---|---|---|
| `error.code` | string | Stable machine-readable error code from the Error Catalog (§2) |
| `error.message` | string | English-language summary; localised if `Accept-Language` header is set |
| `error.details` | array | Optional array of per-field validation issues |
| `error.details[].field` | string | JSON path to the offending field |
| `error.details[].issue` | string | Description of the specific violation |
| `error.details[].value` | string | The value that caused the violation (never includes PAN or CVV) |
| `error.request_id` | string | Unique ID for this request; include in support tickets |

---

## 2. Error Catalog

| Code | HTTP Status | Message | Description |
|---|---|---|---|
| `PAY-1001` | 409 | Idempotency key already used with different parameters | A request with this idempotency key was previously processed with a different body |
| `PAY-1002` | 404 | Payment intent not found | No payment intent exists with the given ID, or it belongs to a different merchant |
| `PAY-1003` | 422 | Invalid currency code | Currency must be a valid ISO 4217 three-letter code (e.g., `USD`, `EUR`) |
| `PAY-1004` | 422 | Payment amount below minimum | Amount must be at least 50 minor units ($0.50 for USD) |
| `PAY-1005` | 422 | Payment amount exceeds maximum | Amount must not exceed 99,999,999 minor units ($999,999.99 for USD) |
| `PAY-1006` | 409 | Payment intent already cancelled | Terminal state; no further operations are permitted |
| `PAY-1007` | 409 | Payment intent already captured | The intent has already been fully captured |
| `PAY-1008` | 422 | Capture amount exceeds authorized amount | `amount_to_capture` is greater than the amount authorized at confirm time |
| `PAY-1009` | 422 | Payment method not found or expired | The referenced payment method ID does not exist or has passed its expiry date |
| `PAY-1010` | 422 | Insufficient wallet balance | The wallet does not have enough available balance for this debit or transfer |
| `PAY-1011` | 403 | Wallet is frozen | All debits and transfers are blocked while the wallet is in a frozen state |
| `PAY-1012` | 422 | Refund amount exceeds captured amount | The total of all refunds would exceed the amount captured on this payment intent |
| `PAY-1013` | 422 | Refund window expired | Refunds are only permitted within 180 days of the capture date |
| `PAY-1014` | 409 | Chargeback already in final state | The chargeback has been resolved (`WON` or `LOST`) and cannot be updated |
| `PAY-1015` | 422 | Fraud score threshold exceeded | The risk engine declined this transaction; do not retry without additional authentication |
| `PAY-1016` | 429 | Velocity limit breached | Too many transactions from this customer/card within the configured velocity window |
| `PAY-1017` | 402 | 3DS2 authentication required | The issuer requires Strong Customer Authentication; follow the `next_action` in the response |
| `PAY-1018` | 503 | PSP routing failure | All configured Payment Service Providers are currently unavailable; retry with backoff |
| `PAY-1019` | 422 | FX rate stale | The referenced FX rate quote is more than 15 minutes old; request a fresh rate |
| `PAY-1020` | 422 | Split payment shares do not sum to 100% | The `splits` array percentages or amounts must total the full payment amount |
| `PAY-1021` | 410 | Virtual account expired | The virtual account number has passed its expiry and can no longer receive funds |
| `PAY-1022` | 409 | Settlement batch already running | A settlement batch for this merchant and date is currently in progress |
| `PAY-1023` | 401 | API key invalid or revoked | The provided `X-API-Key` does not exist, has been revoked, or does not match the JWT environment |
| `PAY-1024` | 403 | Sandbox credentials not accepted in production | Sandbox API keys (prefixed `pk_test_`) cannot be used against the production environment |
| `PAY-1025` | 422 | Webhook endpoint validation failed | The provided webhook URL did not respond to the validation challenge within 5 seconds |

---

## 3. API Endpoints

---

### 3.1 Payment Intents

A **PaymentIntent** represents the merchant's intent to collect a payment. It tracks the full lifecycle from creation through authorization, capture, and settlement.

**PaymentIntent status values:** `requires_payment_method` → `requires_confirmation` → `requires_action` → `processing` → `requires_capture` → `succeeded` → `cancelled`

---

#### `POST /payment-intents`

Create a new payment intent.

**Request Headers:**

| Header | Required | Notes |
|---|---|---|
| `Idempotency-Key` | Yes | Prevent duplicate intents on retry |
| `X-Merchant-ID` | Conditional | Required for platform accounts acting on behalf of sub-merchants |

**Request Body:**

```json
{
  "merchant_id": "mer_01HX9K2M4PQRST6UVWXYZ",
  "customer_id": "cus_01HX8J1N3OQPRS5TUVWXY",
  "amount": 12500,
  "currency": "USD",
  "payment_method_types": ["card", "wallet"],
  "capture_method": "automatic",
  "description": "Order #ORD-20240512-0042 — Premium subscription",
  "statement_descriptor": "ACME PAYMENTS",
  "metadata": {
    "order_id": "ORD-20240512-0042",
    "product_sku": "PREM-ANNUAL-USD"
  },
  "return_url": "https://checkout.merchant.com/return?session=abc123",
  "shipping": {
    "name": "Jane Doe",
    "address": {
      "line1": "123 Main St",
      "line2": "Apt 4B",
      "city": "New York",
      "state": "NY",
      "postal_code": "10001",
      "country": "US"
    },
    "phone": "+12125559876",
    "tracking_number": null
  },
  "billing_details": {
    "name": "Jane Doe",
    "email": "jane.doe@example.com",
    "phone": "+12125559876",
    "address": {
      "line1": "123 Main St",
      "line2": "Apt 4B",
      "city": "New York",
      "state": "NY",
      "postal_code": "10001",
      "country": "US"
    }
  }
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `merchant_id` | string | Yes | Merchant identifier |
| `customer_id` | string | No | Customer identifier for payment method reuse and risk signals |
| `amount` | integer | Yes | Amount in minor currency units (e.g., cents for USD) |
| `currency` | string | Yes | ISO 4217 three-letter code |
| `payment_method_types` | string[] | Yes | Ordered list of accepted payment method types |
| `capture_method` | string | Yes | `automatic` (capture on confirm) or `manual` (separate capture call required) |
| `description` | string | No | Displayed on statements and in the dashboard |
| `statement_descriptor` | string | No | Up to 22 characters; overrides merchant default on card statement |
| `metadata` | object | No | Arbitrary key-value pairs, max 50 keys, 500 chars per value |
| `return_url` | string | Conditional | Required when 3DS2 redirect is possible |
| `shipping` | object | No | Shipping address and contact details |
| `billing_details` | object | No | Billing address used for AVS/CVV checks |

**Response Body — `HTTP 201 Created`:**

```json
{
  "id": "pi_01HX9K2M4PQRST6UVWXYZ",
  "object": "payment_intent",
  "merchant_id": "mer_01HX9K2M4PQRST6UVWXYZ",
  "customer_id": "cus_01HX8J1N3OQPRS5TUVWXY",
  "amount": 12500,
  "amount_capturable": 0,
  "amount_received": 0,
  "currency": "USD",
  "status": "requires_payment_method",
  "capture_method": "automatic",
  "client_secret": "pi_01HX9K2M4PQRST6UVWXYZ_secret_4xT9mKZqL8nW2pRvBcYd",
  "description": "Order #ORD-20240512-0042 — Premium subscription",
  "statement_descriptor": "ACME PAYMENTS",
  "payment_method_types": ["card", "wallet"],
  "payment_method": null,
  "next_action": null,
  "last_payment_error": null,
  "metadata": {
    "order_id": "ORD-20240512-0042",
    "product_sku": "PREM-ANNUAL-USD"
  },
  "shipping": {
    "name": "Jane Doe",
    "address": {
      "line1": "123 Main St",
      "line2": "Apt 4B",
      "city": "New York",
      "state": "NY",
      "postal_code": "10001",
      "country": "US"
    },
    "phone": "+12125559876",
    "tracking_number": null
  },
  "billing_details": {
    "name": "Jane Doe",
    "email": "jane.doe@example.com",
    "phone": "+12125559876",
    "address": {
      "line1": "123 Main St",
      "line2": null,
      "city": "New York",
      "state": "NY",
      "postal_code": "10001",
      "country": "US"
    }
  },
  "psp_reference": null,
  "return_url": "https://checkout.merchant.com/return?session=abc123",
  "created_at": "2024-05-12T10:30:00Z",
  "updated_at": "2024-05-12T10:30:00Z",
  "livemode": true
}
```

**Status Codes:**

| Code | Description |
|---|---|
| `201 Created` | Payment intent created successfully |
| `400 Bad Request` | Malformed JSON or missing required fields |
| `409 Conflict` | Idempotency key collision (`PAY-1001`) |
| `422 Unprocessable Entity` | Validation failure (invalid currency, amount out of range) |
| `401 Unauthorized` | Missing or invalid credentials |

**Possible Error Codes:** `PAY-1001`, `PAY-1003`, `PAY-1004`, `PAY-1005`, `PAY-1023`, `PAY-1024`

---

#### `GET /payment-intents/{id}`

Retrieve a single payment intent with all embedded payment attempts.

**Path Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `id` | string | Payment intent ID (prefix: `pi_`) |

**Response Body — `HTTP 200 OK`:**

Same as `POST /payment-intents` response, with additionally:

```json
{
  "id": "pi_01HX9K2M4PQRST6UVWXYZ",
  "object": "payment_intent",
  "status": "succeeded",
  "amount_capturable": 0,
  "amount_received": 12500,
  "payment_method": {
    "id": "pm_01HX7K1L2MNOPQ4RSTUV",
    "type": "card",
    "card": {
      "brand": "visa",
      "last4": "4242",
      "exp_month": 12,
      "exp_year": 2027,
      "funding": "credit",
      "country": "US"
    }
  },
  "payment_attempts": [
    {
      "id": "pa_01HXA2B3C4D5E6F7G8H9I",
      "status": "succeeded",
      "amount": 12500,
      "currency": "USD",
      "psp": "stripe",
      "psp_reference": "ch_3NkFaB2eZvKYlo2C1234ABCD",
      "authorization_code": "T48291",
      "risk_score": 12,
      "created_at": "2024-05-12T10:30:05Z"
    }
  ],
  "created_at": "2024-05-12T10:30:00Z",
  "updated_at": "2024-05-12T10:30:10Z"
}
```

**Status Codes:**

| Code | Description |
|---|---|
| `200 OK` | Intent found and returned |
| `404 Not Found` | Intent does not exist or belongs to another merchant |
| `401 Unauthorized` | Missing or invalid credentials |

**Possible Error Codes:** `PAY-1002`, `PAY-1023`

---

#### `POST /payment-intents/{id}/confirm`

Attach a payment method and attempt authorization. If 3DS2 authentication is required, `next_action` will be populated in the response.

**Path Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `id` | string | Payment intent ID |

**Request Body:**

```json
{
  "payment_method_id": "pm_01HX7K1L2MNOPQ4RSTUV",
  "payment_method": null,
  "return_url": "https://checkout.merchant.com/return?session=abc123",
  "three_ds_data": {
    "browser_info": {
      "accept_header": "text/html,application/xhtml+xml",
      "color_depth": 24,
      "java_enabled": false,
      "language": "en-US",
      "screen_height": 900,
      "screen_width": 1440,
      "time_zone_offset": -300,
      "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
    }
  }
}
```

> Supply either `payment_method_id` (existing vaulted method) or `payment_method` (inline tokenization object) — not both.

**Response Body — `HTTP 200 OK` (3DS required):**

```json
{
  "id": "pi_01HX9K2M4PQRST6UVWXYZ",
  "status": "requires_action",
  "next_action": {
    "type": "redirect_to_url",
    "redirect_to_url": {
      "url": "https://3ds.bank.com/acs?token=eyJhbGci...",
      "return_url": "https://checkout.merchant.com/return?session=abc123"
    }
  },
  "client_secret": "pi_01HX9K2M4PQRST6UVWXYZ_secret_4xT9mKZqL8nW2pRvBcYd"
}
```

**Status Codes:**

| Code | Description |
|---|---|
| `200 OK` | Confirmation processed (check `status` field) |
| `402 Payment Required` | 3DS2 required — follow `next_action` |
| `404 Not Found` | Intent not found |
| `409 Conflict` | Intent already cancelled or captured |
| `422 Unprocessable Entity` | Invalid payment method or fraud decline |

**Possible Error Codes:** `PAY-1002`, `PAY-1006`, `PAY-1007`, `PAY-1009`, `PAY-1015`, `PAY-1016`, `PAY-1017`, `PAY-1018`

---

#### `POST /payment-intents/{id}/capture`

Capture funds on a payment intent with `capture_method: manual`. Must be called after status is `requires_capture`.

**Request Body:**

```json
{
  "amount_to_capture": 12500,
  "statement_descriptor": "ACME ORDER 0042"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `amount_to_capture` | integer | No | Partial capture amount in minor units; defaults to full authorized amount |
| `statement_descriptor` | string | No | Override statement descriptor for this capture, max 22 chars |

**Response Body — `HTTP 200 OK`:**

```json
{
  "id": "pi_01HX9K2M4PQRST6UVWXYZ",
  "status": "succeeded",
  "amount": 12500,
  "amount_capturable": 0,
  "amount_received": 12500,
  "currency": "USD",
  "captured_at": "2024-05-12T10:35:00Z",
  "updated_at": "2024-05-12T10:35:00Z"
}
```

**Status Codes:**

| Code | Description |
|---|---|
| `200 OK` | Capture successful |
| `404 Not Found` | Intent not found |
| `409 Conflict` | Already captured or cancelled |
| `422 Unprocessable Entity` | Capture amount exceeds authorized amount |

**Possible Error Codes:** `PAY-1002`, `PAY-1006`, `PAY-1007`, `PAY-1008`

---

#### `POST /payment-intents/{id}/cancel`

Cancel a payment intent. Releases any hold on authorized funds.

**Request Body:**

```json
{
  "cancellation_reason": "requested_by_customer"
}
```

`cancellation_reason` enum: `duplicate`, `fraudulent`, `requested_by_customer`, `abandoned`, `failed_invoice`

**Response Body — `HTTP 200 OK`:**

```json
{
  "id": "pi_01HX9K2M4PQRST6UVWXYZ",
  "status": "cancelled",
  "cancellation_reason": "requested_by_customer",
  "cancelled_at": "2024-05-12T10:40:00Z",
  "updated_at": "2024-05-12T10:40:00Z"
}
```

**Status Codes:**

| Code | Description |
|---|---|
| `200 OK` | Intent cancelled |
| `404 Not Found` | Intent not found |
| `409 Conflict` | Intent already cancelled or captured (`PAY-1006`, `PAY-1007`) |

**Possible Error Codes:** `PAY-1002`, `PAY-1006`, `PAY-1007`

---

#### `GET /payment-intents`

List payment intents with filters. Returns cursor-paginated results.

**Query Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `customer_id` | string | Filter by customer |
| `status` | string | Filter by status (comma-separated for multiple) |
| `created_after` | ISO 8601 | Intents created after this timestamp |
| `created_before` | ISO 8601 | Intents created before this timestamp |
| `amount_gte` | integer | Minimum amount in minor units |
| `amount_lte` | integer | Maximum amount in minor units |
| `currency` | string | ISO 4217 currency code |
| `limit` | integer | Page size (default: 20, max: 100) |
| `after` | string | Pagination cursor |

**Response Body — `HTTP 200 OK`:**

```json
{
  "data": [ /* array of PaymentIntent objects */ ],
  "next_cursor": "Y3Vyc29yX3BpXzAxSFg5SzJNNA==",
  "prev_cursor": null,
  "has_more": true,
  "total_count": 3420
}
```

---

### 3.2 Payment Sessions

A **PaymentSession** creates a hosted payment page URL for redirect-based checkout flows, wrapping an existing PaymentIntent.

---

#### `POST /payment-sessions`

**Request Body:**

```json
{
  "payment_intent_id": "pi_01HX9K2M4PQRST6UVWXYZ",
  "success_url": "https://merchant.com/checkout/success?session_id={CHECKOUT_SESSION_ID}",
  "cancel_url": "https://merchant.com/checkout/cancel",
  "expires_in_seconds": 1800,
  "ui_mode": "embedded",
  "locale": "en-US"
}
```

**Response Body — `HTTP 201 Created`:**

```json
{
  "id": "cs_01HXB2C3D4E5F6G7H8I9J",
  "object": "payment_session",
  "payment_intent_id": "pi_01HX9K2M4PQRST6UVWXYZ",
  "url": "https://checkout.payments.io/pay/cs_01HXB2C3D4E5F6G7H8I9J",
  "status": "open",
  "expires_at": "2024-05-12T11:00:00Z",
  "success_url": "https://merchant.com/checkout/success?session_id=cs_01HXB2C3D4E5F6G7H8I9J",
  "cancel_url": "https://merchant.com/checkout/cancel",
  "created_at": "2024-05-12T10:30:00Z"
}
```

**Status Codes:** `201 Created`, `404 Not Found` (intent not found), `409 Conflict` (intent already confirmed), `422 Unprocessable Entity`

---

#### `GET /payment-sessions/{id}`

**Response Body — `HTTP 200 OK`:**

```json
{
  "id": "cs_01HXB2C3D4E5F6G7H8I9J",
  "object": "payment_session",
  "payment_intent_id": "pi_01HX9K2M4PQRST6UVWXYZ",
  "status": "complete",
  "url": "https://checkout.payments.io/pay/cs_01HXB2C3D4E5F6G7H8I9J",
  "expires_at": "2024-05-12T11:00:00Z",
  "completed_at": "2024-05-12T10:45:00Z",
  "created_at": "2024-05-12T10:30:00Z"
}
```

Session `status` values: `open`, `complete`, `expired`

---

### 3.3 Wallets

A **Wallet** is a multi-currency ledger account. Each wallet can hold balances in multiple currencies and supports credit, debit, and peer-to-peer transfers.

---

#### `GET /wallets/{id}`

**Path Parameters:** `id` — wallet ID (prefix: `wal_`)

**Response Body — `HTTP 200 OK`:**

```json
{
  "id": "wal_01HXC2D3E4F5G6H7I8J9K",
  "object": "wallet",
  "owner_id": "cus_01HX8J1N3OQPRS5TUVWXY",
  "owner_type": "customer",
  "status": "active",
  "balances": [
    {
      "currency": "USD",
      "available": 50000,
      "pending": 2500,
      "reserved": 0
    },
    {
      "currency": "EUR",
      "available": 10000,
      "pending": 0,
      "reserved": 500
    }
  ],
  "frozen_at": null,
  "freeze_reason": null,
  "created_at": "2024-01-15T08:00:00Z",
  "updated_at": "2024-05-12T10:30:00Z"
}
```

---

#### `POST /wallets/{id}/credit`

Credit funds into a wallet (e.g., from a captured payment or top-up).

**Request Body:**

```json
{
  "amount": 12500,
  "currency": "USD",
  "reference_type": "payment_intent",
  "reference_id": "pi_01HX9K2M4PQRST6UVWXYZ",
  "description": "Funds from order ORD-20240512-0042",
  "idempotency_key": "credit-pi-01HX9K2M4-to-wal-01HXC2D3E"
}
```

**Response Body — `HTTP 200 OK`:**

```json
{
  "id": "txn_01HXD3E4F5G6H7I8J9K0L",
  "object": "wallet_transaction",
  "wallet_id": "wal_01HXC2D3E4F5G6H7I8J9K",
  "type": "credit",
  "amount": 12500,
  "currency": "USD",
  "balance_after": 62500,
  "reference_type": "payment_intent",
  "reference_id": "pi_01HX9K2M4PQRST6UVWXYZ",
  "description": "Funds from order ORD-20240512-0042",
  "status": "posted",
  "created_at": "2024-05-12T10:35:00Z"
}
```

**Possible Error Codes:** `PAY-1001`, `PAY-1011`

---

#### `POST /wallets/{id}/debit`

Debit funds from a wallet.

**Request Body:**

```json
{
  "amount": 5000,
  "currency": "USD",
  "reference_type": "payout",
  "reference_id": "po_01HXE4F5G6H7I8J9K0L1M",
  "description": "Payout to bank account ending 4567",
  "idempotency_key": "debit-po-01HXE4F5-from-wal-01HXC2D3E"
}
```

**Response Body:** Same schema as `/credit` response with `type: "debit"`.

**Possible Error Codes:** `PAY-1001`, `PAY-1010`, `PAY-1011`

---

#### `GET /wallets/{id}/transactions`

List wallet transactions with cursor-based pagination.

**Query Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `currency` | string | Filter by currency |
| `type` | string | `credit`, `debit`, or `transfer` |
| `created_after` | ISO 8601 | Transactions after this timestamp |
| `created_before` | ISO 8601 | Transactions before this timestamp |
| `limit` | integer | Page size (default: 20, max: 100) |
| `after` | string | Pagination cursor |

**Response Body:** Cursor-paginated array of wallet transaction objects.

---

#### `POST /wallets/{id}/transfer`

Transfer funds to another wallet atomically.

**Request Body:**

```json
{
  "destination_wallet_id": "wal_01HXF5G6H7I8J9K0L1M2N",
  "amount": 10000,
  "currency": "USD",
  "description": "Platform fee distribution",
  "idempotency_key": "transfer-wal-01HXC2D3E-to-wal-01HXF5G6H"
}
```

**Response Body — `HTTP 200 OK`:**

```json
{
  "id": "trf_01HXG6H7I8J9K0L1M2N3O",
  "object": "wallet_transfer",
  "source_wallet_id": "wal_01HXC2D3E4F5G6H7I8J9K",
  "destination_wallet_id": "wal_01HXF5G6H7I8J9K0L1M2N",
  "amount": 10000,
  "currency": "USD",
  "source_transaction_id": "txn_01HXD3E4F5G6H7I8J9K0L",
  "destination_transaction_id": "txn_01HXH7I8J9K0L1M2N3O4P",
  "status": "completed",
  "description": "Platform fee distribution",
  "created_at": "2024-05-12T10:36:00Z"
}
```

**Possible Error Codes:** `PAY-1001`, `PAY-1010`, `PAY-1011`

---

#### `POST /wallets/{id}/freeze`

Freeze a wallet, blocking all debits and outbound transfers. Credits continue to be accepted.

**Request Body:**

```json
{
  "reason": "fraud_investigation"
}
```

`reason` enum: `fraud_investigation`, `kyc_pending`, `compliance_hold`, `customer_request`, `legal_hold`

**Response Body — `HTTP 200 OK`:**

```json
{
  "id": "wal_01HXC2D3E4F5G6H7I8J9K",
  "status": "frozen",
  "frozen_at": "2024-05-12T11:00:00Z",
  "freeze_reason": "fraud_investigation"
}
```

---

#### `POST /wallets/{id}/unfreeze`

Unfreeze a previously frozen wallet. Requires elevated `wallets:admin` scope.

**Request Body:** `{}` (empty)

**Response Body — `HTTP 200 OK`:**

```json
{
  "id": "wal_01HXC2D3E4F5G6H7I8J9K",
  "status": "active",
  "frozen_at": null,
  "freeze_reason": null,
  "unfrozen_at": "2024-05-12T12:00:00Z"
}
```

---

### 3.4 Refunds

**RefundRecord** status values: `pending` → `processing` → `succeeded` | `failed`

---

#### `POST /refunds`

Initiate a full or partial refund against a captured payment intent.

**Request Body:**

```json
{
  "payment_intent_id": "pi_01HX9K2M4PQRST6UVWXYZ",
  "amount": 5000,
  "currency": "USD",
  "reason": "customer_request",
  "metadata": {
    "support_ticket": "TKT-20240512-9901"
  },
  "idempotency_key": "refund-pi-01HX9K2M4-5000-20240512"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `payment_intent_id` | string | Yes | The intent to refund |
| `amount` | integer | No | Minor units; defaults to full remaining captured amount |
| `currency` | string | Yes | Must match the intent's currency |
| `reason` | string | No | `duplicate`, `fraudulent`, `customer_request`, `defective_product`, `other` |
| `metadata` | object | No | Arbitrary key-value pairs |
| `idempotency_key` | string | Yes | Prevent duplicate refunds |

**Response Body — `HTTP 201 Created`:**

```json
{
  "id": "ref_01HXI7J8K9L0M1N2O3P4Q",
  "object": "refund",
  "payment_intent_id": "pi_01HX9K2M4PQRST6UVWXYZ",
  "amount": 5000,
  "currency": "USD",
  "status": "pending",
  "reason": "customer_request",
  "psp_reference": null,
  "failure_reason": null,
  "metadata": {
    "support_ticket": "TKT-20240512-9901"
  },
  "created_at": "2024-05-12T11:00:00Z",
  "updated_at": "2024-05-12T11:00:00Z"
}
```

**Possible Error Codes:** `PAY-1001`, `PAY-1002`, `PAY-1012`, `PAY-1013`

---

#### `GET /refunds/{id}` and `GET /refunds`

`GET /refunds/{id}` — returns single refund by ID.

`GET /refunds` query params: `payment_intent_id` (required), `status`, `limit`, `after`.

---

### 3.5 Chargebacks

---

#### `POST /chargebacks`

Record a chargeback notification received from the payment network.

**Request Body:**

```json
{
  "payment_intent_id": "pi_01HX9K2M4PQRST6UVWXYZ",
  "amount": 12500,
  "currency": "USD",
  "reason_code": "4853",
  "reason_description": "Cardholder dispute — merchandise not received",
  "network": "visa",
  "arn": "74190085426214631285949",
  "received_at": "2024-05-10T00:00:00Z",
  "respond_by": "2024-05-25T00:00:00Z"
}
```

**Response Body — `HTTP 201 Created`:**

```json
{
  "id": "cb_01HXJ8K9L0M1N2O3P4Q5R",
  "object": "chargeback",
  "payment_intent_id": "pi_01HX9K2M4PQRST6UVWXYZ",
  "amount": 12500,
  "currency": "USD",
  "status": "needs_response",
  "reason_code": "4853",
  "reason_description": "Cardholder dispute — merchandise not received",
  "network": "visa",
  "arn": "74190085426214631285949",
  "received_at": "2024-05-10T00:00:00Z",
  "respond_by": "2024-05-25T00:00:00Z",
  "evidence_submitted_at": null,
  "resolved_at": null,
  "resolution": null,
  "created_at": "2024-05-12T11:00:00Z"
}
```

Chargeback `status` values: `needs_response` → `under_review` → `won` | `lost`

---

#### `GET /chargebacks/{id}`

Returns the full chargeback object including submitted evidence.

---

#### `PUT /chargebacks/{id}/respond`

Submit merchant evidence to contest a chargeback.

**Request Body:**

```json
{
  "evidence": {
    "product_description": "Annual premium subscription to ACME SaaS, purchased 2024-04-01. Customer has been actively using the service until dispute date.",
    "customer_communication": "base64_encoded_pdf_of_email_thread",
    "refund_policy_disclosure": "https://merchant.com/refund-policy",
    "receipt": "base64_encoded_pdf_receipt",
    "shipping_tracking_number": null,
    "billing_address_matched": true,
    "customer_signature": null
  },
  "notes": "Customer has logged in 47 times since purchase per attached activity log."
}
```

**Response Body — `HTTP 200 OK`:**

```json
{
  "id": "cb_01HXJ8K9L0M1N2O3P4Q5R",
  "status": "under_review",
  "evidence_submitted_at": "2024-05-14T09:00:00Z",
  "updated_at": "2024-05-14T09:00:00Z"
}
```

**Possible Error Codes:** `PAY-1014` (already in final state)

---

#### `GET /chargebacks`

**Query Parameters:** `payment_intent_id`, `status`, `network`, `created_after`, `created_before`, `limit`, `after`

---

### 3.6 Payouts

---

#### `POST /payouts`

Initiate a payout to a merchant's registered bank account.

**Request Body:**

```json
{
  "merchant_id": "mer_01HX9K2M4PQRST6UVWXYZ",
  "amount": 500000,
  "currency": "USD",
  "bank_account_id": "ba_01HXK9L0M1N2O3P4Q5R6S",
  "description": "Weekly settlement payout — week ending 2024-05-11",
  "idempotency_key": "payout-mer-01HX9K2M4-20240511-weekly"
}
```

**Response Body — `HTTP 201 Created`:**

```json
{
  "id": "po_01HXL0M1N2O3P4Q5R6S7T",
  "object": "payout",
  "merchant_id": "mer_01HX9K2M4PQRST6UVWXYZ",
  "amount": 500000,
  "currency": "USD",
  "bank_account_id": "ba_01HXK9L0M1N2O3P4Q5R6S",
  "status": "pending",
  "description": "Weekly settlement payout — week ending 2024-05-11",
  "arrival_date": "2024-05-14",
  "failure_code": null,
  "failure_message": null,
  "created_at": "2024-05-12T12:00:00Z",
  "updated_at": "2024-05-12T12:00:00Z"
}
```

Payout `status` values: `pending` → `in_transit` → `paid` | `failed` | `cancelled`

**Possible Error Codes:** `PAY-1001`, `PAY-1010`

---

#### `GET /payouts/{id}`

Returns the full Payout object with current status.

---

### 3.7 Settlement Batches

---

#### `GET /settlement-batches`

**Query Parameters:** `merchant_id`, `batch_date` (ISO 8601 date), `status` (`pending`, `running`, `completed`, `failed`), `limit`, `after`

**Response Body:** Cursor-paginated array of SettlementBatch summary objects.

---

#### `POST /settlement-batches/run`

Trigger a settlement batch for a merchant and date. Only one batch can run at a time per merchant+date.

**Request Body:**

```json
{
  "merchant_id": "mer_01HX9K2M4PQRST6UVWXYZ",
  "batch_date": "2024-05-11",
  "dry_run": false
}
```

| Field | Type | Description |
|---|---|---|
| `merchant_id` | string | Target merchant |
| `batch_date` | date | The settlement date (ISO 8601 `YYYY-MM-DD`) |
| `dry_run` | boolean | If `true`, compute and return settlement records without committing |

**Response Body — `HTTP 202 Accepted`:**

```json
{
  "id": "sb_01HXM1N2O3P4Q5R6S7T8U",
  "object": "settlement_batch",
  "merchant_id": "mer_01HX9K2M4PQRST6UVWXYZ",
  "batch_date": "2024-05-11",
  "status": "running",
  "dry_run": false,
  "record_count": null,
  "gross_amount": null,
  "net_amount": null,
  "started_at": "2024-05-12T12:01:00Z",
  "completed_at": null
}
```

**Possible Error Codes:** `PAY-1022`

---

#### `GET /settlement-batches/{id}`

Returns the full batch including all settlement records.

**Response Body — `HTTP 200 OK`:**

```json
{
  "id": "sb_01HXM1N2O3P4Q5R6S7T8U",
  "status": "completed",
  "batch_date": "2024-05-11",
  "record_count": 1240,
  "gross_amount": 6250000,
  "fees_amount": 93750,
  "net_amount": 6156250,
  "currency": "USD",
  "completed_at": "2024-05-12T12:05:00Z",
  "settlement_records": [
    {
      "payment_intent_id": "pi_01HX9K2M4PQRST6UVWXYZ",
      "captured_amount": 12500,
      "fee_amount": 188,
      "net_amount": 12312,
      "currency": "USD",
      "settled_at": "2024-05-12T12:03:00Z"
    }
  ]
}
```

---

### 3.8 Payment Methods

---

#### `GET /payment-methods`

**Query Parameters:** `customer_id` (required), `type` (`card`, `bank_account`, `wallet`), `limit`, `after`

**Response Body:** Paginated array of PaymentMethod objects (never contains raw PAN or CVV).

---

#### `POST /payment-methods`

Tokenize and vault a new payment method. Raw card data is accepted only when the caller holds `PCI-DSS SAQ-D` certification and the connection is TLS 1.2+. The response **never** returns the raw PAN — only the vault token and a masked representation.

**Request Body:**

```json
{
  "customer_id": "cus_01HX8J1N3OQPRS5TUVWXY",
  "type": "card",
  "card": {
    "number": "4242424242424242",
    "exp_month": 12,
    "exp_year": 2027,
    "cvv": "123",
    "cardholder_name": "Jane Doe"
  },
  "billing_address": {
    "line1": "123 Main St",
    "city": "New York",
    "state": "NY",
    "postal_code": "10001",
    "country": "US"
  },
  "set_as_default": false
}
```

**Response Body — `HTTP 201 Created`:**

```json
{
  "id": "pm_01HX7K1L2MNOPQ4RSTUV",
  "object": "payment_method",
  "customer_id": "cus_01HX8J1N3OQPRS5TUVWXY",
  "type": "card",
  "vault_token": "tok_01HXN2O3P4Q5R6S7T8U9V",
  "card": {
    "brand": "visa",
    "last4": "4242",
    "exp_month": 12,
    "exp_year": 2027,
    "funding": "credit",
    "country": "US",
    "fingerprint": "Xt5EWLLDS7FJjR1c",
    "cardholder_name": "Jane Doe"
  },
  "billing_address": {
    "line1": "123 Main St",
    "city": "New York",
    "state": "NY",
    "postal_code": "10001",
    "country": "US"
  },
  "is_default": false,
  "created_at": "2024-05-12T10:00:00Z"
}
```

> **PCI Compliance:** Raw card numbers and CVV values are never logged, stored, or returned post-tokenization. The `vault_token` is a pseudonymous reference to the encrypted card data stored in the PCI-DSS certified vault.

---

#### `DELETE /payment-methods/{id}`

Soft-deletes (deactivates) the payment method vault record.

**Response:** `HTTP 204 No Content`

---

### 3.9 FX Rates

---

#### `GET /fx-rates`

Retrieve current mid-market exchange rates. Rates are refreshed every 5 minutes from multiple data providers. Rates older than 15 minutes are flagged as stale.

**Query Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `base_currency` | string | Yes | ISO 4217 base currency |
| `quote_currencies` | string | Yes | Comma-separated list of target currencies (max 20) |

**Response Body — `HTTP 200 OK`:**

```json
{
  "base_currency": "USD",
  "rates": {
    "EUR": {
      "rate": 0.92340,
      "buy_rate": 0.91880,
      "sell_rate": 0.92800,
      "fetched_at": "2024-05-12T10:25:00Z",
      "is_stale": false
    },
    "GBP": {
      "rate": 0.79120,
      "buy_rate": 0.78650,
      "sell_rate": 0.79590,
      "fetched_at": "2024-05-12T10:25:00Z",
      "is_stale": false
    }
  },
  "timestamp": "2024-05-12T10:30:00Z"
}
```

---

#### `POST /fx-rates/convert`

Convert an amount between currencies, optionally locking the rate to a wallet.

**Request Body:**

```json
{
  "from_currency": "USD",
  "from_amount": 10000,
  "to_currency": "EUR",
  "wallet_id": "wal_01HXC2D3E4F5G6H7I8J9K",
  "lock_rate": true,
  "idempotency_key": "fx-convert-10000-usd-eur-20240512-001"
}
```

**Response Body — `HTTP 200 OK`:**

```json
{
  "id": "fxc_01HXO3P4Q5R6S7T8U9V0W",
  "from_currency": "USD",
  "from_amount": 10000,
  "to_currency": "EUR",
  "to_amount": 9234,
  "rate": 0.92340,
  "rate_locked_until": "2024-05-12T10:45:00Z",
  "fee_amount": 50,
  "fee_currency": "USD",
  "wallet_id": "wal_01HXC2D3E4F5G6H7I8J9K",
  "status": "completed",
  "created_at": "2024-05-12T10:30:00Z"
}
```

**Possible Error Codes:** `PAY-1001`, `PAY-1003`, `PAY-1019`

---

### 3.10 Webhooks

---

#### `POST /webhooks`

Register a webhook endpoint to receive real-time event notifications.

**Request Body:**

```json
{
  "url": "https://merchant.com/webhooks/payments",
  "events": [
    "payment_intent.succeeded",
    "payment_intent.payment_failed",
    "refund.created",
    "refund.updated",
    "chargeback.created",
    "payout.paid",
    "payout.failed"
  ],
  "secret": "whsec_user_provided_32_char_secret",
  "active": true,
  "api_version": "v1"
}
```

At registration, the platform sends a `webhook.endpoint.verified` challenge event to the URL. The endpoint must respond with `HTTP 200` within 5 seconds.

**Response Body — `HTTP 201 Created`:**

```json
{
  "id": "wh_01HXP4Q5R6S7T8U9V0W1X",
  "object": "webhook_endpoint",
  "url": "https://merchant.com/webhooks/payments",
  "events": ["payment_intent.succeeded", "refund.created"],
  "active": true,
  "api_version": "v1",
  "secret_last4": "cret",
  "created_at": "2024-05-12T12:00:00Z"
}
```

> **Security:** The `secret` is write-only. It is displayed once at creation and cannot be retrieved. Use it to verify `X-Signature` headers (see §4).

**Possible Error Codes:** `PAY-1025`

---

#### `GET /webhooks`

Returns paginated list of webhook endpoint configurations (without secrets).

---

#### `DELETE /webhooks/{id}`

Permanently deletes the webhook subscription. In-flight deliveries may still complete.

**Response:** `HTTP 204 No Content`

---

#### `GET /webhooks/{id}/deliveries`

List delivery attempts for a webhook endpoint. Useful for debugging failed deliveries.

**Query Parameters:** `event_type`, `status` (`pending`, `succeeded`, `failed`), `created_after`, `limit`, `after`

**Response Body — `HTTP 200 OK`:**

```json
{
  "data": [
    {
      "id": "wdl_01HXQ5R6S7T8U9V0W1X2Y",
      "webhook_id": "wh_01HXP4Q5R6S7T8U9V0W1X",
      "event_id": "evt_01HXR6S7T8U9V0W1X2Y3Z",
      "event_type": "payment_intent.succeeded",
      "status": "succeeded",
      "attempt_number": 1,
      "response_code": 200,
      "response_body": "ok",
      "latency_ms": 245,
      "delivered_at": "2024-05-12T10:30:05Z",
      "next_retry_at": null
    },
    {
      "id": "wdl_01HXS7T8U9V0W1X2Y3Z4A",
      "event_type": "refund.created",
      "status": "failed",
      "attempt_number": 3,
      "response_code": 503,
      "response_body": "Service Unavailable",
      "latency_ms": 5001,
      "delivered_at": "2024-05-12T10:31:00Z",
      "next_retry_at": "2024-05-12T10:46:00Z"
    }
  ],
  "has_more": false,
  "next_cursor": null,
  "total_count": 2
}
```

Delivery retry schedule (exponential backoff): 5s, 30s, 2m, 10m, 30m, 2h, 8h, 24h (max 8 attempts).

---

### 3.11 Risk

---

#### `GET /risk/scores/{payment_intent_id}`

Retrieve the risk evaluation for a payment intent.

**Path Parameters:** `payment_intent_id` — the payment intent ID

**Response Body — `HTTP 200 OK`:**

```json
{
  "payment_intent_id": "pi_01HX9K2M4PQRST6UVWXYZ",
  "score": 18,
  "level": "low",
  "decision": "allow",
  "signals": [
    { "name": "card_country_mismatch", "weight": 3, "triggered": false },
    { "name": "velocity_24h", "weight": 5, "triggered": false },
    { "name": "device_fingerprint_new", "weight": 10, "triggered": true },
    { "name": "email_domain_free", "weight": 5, "triggered": true }
  ],
  "evaluated_at": "2024-05-12T10:30:02Z",
  "model_version": "risk-v3.2.1"
}
```

Score range: 0–100. Decision thresholds: `allow` (0–30), `review` (31–70), `decline` (71–100).

---

#### `POST /risk/scores/evaluate`

Manually trigger a risk evaluation (e.g., before initiating a payout or high-value transaction).

**Request Body:**

```json
{
  "payment_intent_id": "pi_01HX9K2M4PQRST6UVWXYZ",
  "context": {
    "ip_address": "203.0.113.42",
    "device_fingerprint": "fp_abc123def456",
    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
  }
}
```

**Response Body:** Same schema as `GET /risk/scores/{id}`.

---

### 3.12 Reports

All report endpoints return aggregated analytical data. Reports may be generated asynchronously for large date ranges; in that case, `HTTP 202 Accepted` is returned with a polling URL.

---

#### `GET /reports/revenue`

**Query Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `start_date` | date | Yes | `YYYY-MM-DD` |
| `end_date` | date | Yes | `YYYY-MM-DD` |
| `currency` | string | Yes | ISO 4217 |
| `group_by` | string | Yes | `day`, `week`, or `month` |
| `merchant_id` | string | No | Filter by merchant (platform admins only) |

**Response Body — `HTTP 200 OK`:**

```json
{
  "currency": "USD",
  "group_by": "day",
  "data": [
    {
      "period": "2024-05-11",
      "gross_volume": 6250000,
      "transaction_count": 1240,
      "refund_amount": 125000,
      "chargeback_amount": 12500,
      "net_revenue": 6112500
    }
  ],
  "totals": {
    "gross_volume": 6250000,
    "net_revenue": 6112500,
    "transaction_count": 1240
  },
  "generated_at": "2024-05-12T13:00:00Z"
}
```

---

#### `GET /reports/settlements`

Settlement summary by merchant and date range.

**Query Parameters:** `merchant_id`, `start_date`, `end_date`, `currency`, `limit`, `after`

---

#### `GET /reports/chargebacks`

Chargeback rate report showing dispute rates, win rates, and financial exposure.

**Query Parameters:** `merchant_id`, `start_date`, `end_date`, `network`, `group_by`

**Response Body includes:** `chargeback_count`, `chargeback_rate_bps` (basis points), `won_count`, `won_rate`, `total_exposure`, `recovered_amount`

---

#### `GET /reports/psp-performance`

PSP success rate and latency analytics.

**Query Parameters:** `start_date`, `end_date`, `psp` (filter by PSP name)

**Response Body — `HTTP 200 OK`:**

```json
{
  "data": [
    {
      "psp": "stripe",
      "authorization_count": 8450,
      "success_count": 8312,
      "success_rate": 98.37,
      "avg_latency_ms": 312,
      "p95_latency_ms": 820,
      "p99_latency_ms": 1450,
      "decline_reasons": {
        "insufficient_funds": 62,
        "card_blocked": 41,
        "do_not_honor": 35
      }
    }
  ],
  "generated_at": "2024-05-12T13:00:00Z"
}
```

---

### 3.13 API Keys

---

#### `POST /api-keys`

Create a new API key. Requires `api_keys:write` scope.

**Request Body:**

```json
{
  "name": "Production Server Key",
  "environment": "production",
  "scopes": ["payments:write", "payments:read", "wallets:read", "webhooks:write"],
  "expires_at": null
}
```

**Response Body — `HTTP 201 Created`:**

```json
{
  "id": "key_01HXT8U9V0W1X2Y3Z4A5B",
  "name": "Production Server Key",
  "key": "pk_live_4xT9mKZqL8nW2pRvBcYdEjUhFs3aGiNo",
  "environment": "production",
  "scopes": ["payments:write", "payments:read", "wallets:read", "webhooks:write"],
  "last4": "iNo",
  "expires_at": null,
  "created_at": "2024-05-12T10:00:00Z"
}
```

> **Warning:** The full `key` value is displayed **only once** in this response. Store it securely. Subsequent GET requests return only `last4`.

---

#### `GET /api-keys`

List all API keys for the merchant (keys masked to `last4`).

---

#### `DELETE /api-keys/{id}`

Immediately revoke an API key. All in-flight requests using the key will fail with `PAY-1023`.

**Response:** `HTTP 204 No Content`

---

#### `POST /api-keys/{id}/rotate`

Generate a replacement key with the same scopes and metadata. The old key remains valid for a 24-hour grace period to allow safe rotation.

**Request Body:** `{}` (empty)

**Response Body — `HTTP 200 OK`:**

```json
{
  "id": "key_01HXU9V0W1X2Y3Z4A5B6C",
  "key": "pk_live_7yU0nLArM9oX3qSwCdZeF...",
  "replaces_key_id": "key_01HXT8U9V0W1X2Y3Z4A5B",
  "old_key_expires_at": "2024-05-13T10:00:00Z",
  "created_at": "2024-05-12T10:00:00Z"
}
```

---

## 4. Webhook Event Payloads

### Delivery Format

Each webhook event is delivered as an `HTTP POST` to the registered endpoint URL with the following headers:

| Header | Description |
|---|---|
| `Content-Type` | `application/json` |
| `X-Event-Type` | Event type string (e.g., `payment_intent.succeeded`) |
| `X-Timestamp` | Unix timestamp (seconds since epoch) of event occurrence |
| `X-Delivery-Attempt` | Integer attempt number (1-indexed) |
| `X-Signature` | HMAC-SHA256 signature for payload verification (see below) |
| `X-Webhook-ID` | The registered webhook endpoint ID |
| `X-Event-ID` | Unique event ID for idempotency |

### Event Envelope

```json
{
  "id": "evt_01HXR6S7T8U9V0W1X2Y3Z",
  "object": "event",
  "type": "payment_intent.succeeded",
  "api_version": "v1",
  "created": 1715509800,
  "livemode": true,
  "data": {
    "object": {
      "id": "pi_01HX9K2M4PQRST6UVWXYZ",
      "object": "payment_intent",
      "amount": 12500,
      "currency": "USD",
      "status": "succeeded",
      "customer_id": "cus_01HX8J1N3OQPRS5TUVWXY",
      "merchant_id": "mer_01HX9K2M4PQRST6UVWXYZ",
      "metadata": { "order_id": "ORD-20240512-0042" },
      "created_at": "2024-05-12T10:30:00Z",
      "updated_at": "2024-05-12T10:30:10Z"
    },
    "previous_attributes": {
      "status": "processing"
    }
  }
}
```

### Signature Verification

The `X-Signature` header value is computed as:

```
HMAC-SHA256(secret, timestamp + "." + raw_request_body)
```

Where:
- `secret` — the webhook endpoint secret set at registration
- `timestamp` — the value from the `X-Timestamp` header
- `raw_request_body` — the **raw** UTF-8 bytes of the request body (before JSON parsing)
- The signature is hex-encoded

#### Verification Pseudocode

```python
import hmac, hashlib, time

def verify_webhook(raw_body: bytes, headers: dict, secret: str) -> bool:
    timestamp = headers["X-Timestamp"]
    received_sig = headers["X-Signature"]

    # Reject events older than 5 minutes to prevent replay attacks
    if abs(time.time() - int(timestamp)) > 300:
        return False

    signed_payload = f"{timestamp}.{raw_body.decode('utf-8')}"
    expected_sig = hmac.new(
        secret.encode("utf-8"),
        signed_payload.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    # Use constant-time comparison to prevent timing attacks
    return hmac.compare_digest(expected_sig, received_sig)
```

> **Important:** Always verify signatures using the **raw** request body before any JSON parsing. Normalizing or pretty-printing the body will break the signature check.

### Supported Event Types

| Event Type | Trigger |
|---|---|
| `payment_intent.created` | New payment intent created |
| `payment_intent.requires_action` | 3DS2 or additional action needed |
| `payment_intent.processing` | Payment submitted to PSP |
| `payment_intent.succeeded` | Payment fully captured and settled |
| `payment_intent.payment_failed` | Authorization or capture failed |
| `payment_intent.cancelled` | Intent cancelled |
| `refund.created` | Refund initiated |
| `refund.updated` | Refund status changed |
| `chargeback.created` | New chargeback received from network |
| `chargeback.updated` | Chargeback status changed |
| `chargeback.won` | Merchant won the dispute |
| `chargeback.lost` | Merchant lost the dispute |
| `wallet.credited` | Funds credited to wallet |
| `wallet.debited` | Funds debited from wallet |
| `wallet.frozen` | Wallet frozen |
| `wallet.unfrozen` | Wallet unfrozen |
| `payout.created` | Payout initiated |
| `payout.in_transit` | Payout submitted to banking network |
| `payout.paid` | Payout confirmed by bank |
| `payout.failed` | Payout failed |
| `settlement_batch.completed` | Settlement batch finished |
| `webhook.endpoint.verified` | Webhook endpoint verified at registration |

---

## 5. SDK Usage Examples

### 5.1 End-to-End Card Payment (cURL)

```bash
# Step 1: Create a payment intent
curl -X POST https://api.payments.io/v1/payment-intents \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "X-API-Key: pk_live_4xT9mKZqL8nW2pRvBcYd..." \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(uuidgen)" \
  -d '{
    "merchant_id": "mer_01HX9K2M4PQRST6UVWXYZ",
    "customer_id": "cus_01HX8J1N3OQPRS5TUVWXY",
    "amount": 12500,
    "currency": "USD",
    "payment_method_types": ["card"],
    "capture_method": "automatic",
    "description": "Order #ORD-20240512-0042"
  }'
# Returns: pi_01HX9K2M4PQRST6UVWXYZ with client_secret

# Step 2: Confirm with a vaulted payment method
curl -X POST https://api.payments.io/v1/payment-intents/pi_01HX9K2M4PQRST6UVWXYZ/confirm \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "X-API-Key: pk_live_4xT9mKZqL8nW2pRvBcYd..." \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(uuidgen)" \
  -d '{
    "payment_method_id": "pm_01HX7K1L2MNOPQ4RSTUV",
    "return_url": "https://merchant.com/return"
  }'
# Returns: status=succeeded or status=requires_action with next_action.redirect_to_url
```

### 5.2 Manual Capture Flow (cURL)

```bash
# Create intent with manual capture
curl -X POST https://api.payments.io/v1/payment-intents \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: manual-capture-example-001" \
  -d '{ "amount": 50000, "currency": "USD", "capture_method": "manual", ... }'

# Confirm to authorize (status → requires_capture)
curl -X POST https://api.payments.io/v1/payment-intents/pi_.../confirm \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: confirm-manual-example-001" \
  -d '{ "payment_method_id": "pm_..." }'

# Capture (partial capture: $400 of $500 authorized)
curl -X POST https://api.payments.io/v1/payment-intents/pi_.../capture \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: capture-partial-example-001" \
  -d '{ "amount_to_capture": 40000 }'
```

### 5.3 Wallet Top-Up and Transfer (Pseudocode)

```python
import payments_sdk as pay

client = pay.Client(api_key="pk_live_...", jwt=get_jwt())

# Credit wallet after successful payment capture
txn = client.wallets.credit(
    wallet_id="wal_01HXC2D3E4F5G6H7I8J9K",
    amount=12500,
    currency="USD",
    reference_type="payment_intent",
    reference_id="pi_01HX9K2M4PQRST6UVWXYZ",
    idempotency_key="credit-after-pi-01HX9K2M4"
)

# Transfer between wallets
transfer = client.wallets.transfer(
    source_wallet_id="wal_01HXC2D3E4F5G6H7I8J9K",
    destination_wallet_id="wal_01HXF5G6H7I8J9K0L1M2N",
    amount=5000,
    currency="USD",
    idempotency_key="transfer-platform-fee-20240512-001"
)
```

### 5.4 Issuing a Refund (cURL)

```bash
curl -X POST https://api.payments.io/v1/refunds \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: refund-order-0042-partial-5000" \
  -d '{
    "payment_intent_id": "pi_01HX9K2M4PQRST6UVWXYZ",
    "amount": 5000,
    "currency": "USD",
    "reason": "customer_request",
    "metadata": { "support_ticket": "TKT-20240512-9901" }
  }'
```

### 5.5 FX Conversion Before Wallet Debit (Pseudocode)

```python
# Get current rates
rates = client.fx_rates.get(base_currency="USD", quote_currencies=["EUR", "GBP"])

# Lock rate and convert
conversion = client.fx_rates.convert(
    from_currency="USD",
    from_amount=10000,
    to_currency="EUR",
    wallet_id="wal_01HXC2D3E4F5G6H7I8J9K",
    lock_rate=True,
    idempotency_key="fx-usd-eur-10000-20240512-001"
)

print(f"Converted {conversion.from_amount} USD → {conversion.to_amount} EUR")
print(f"Rate locked until: {conversion.rate_locked_until}")
```

### 5.6 Webhook Verification Handler (Python / Flask)

```python
from flask import Flask, request, abort
import hmac, hashlib, time

app = Flask(__name__)
WEBHOOK_SECRET = "whsec_your_32_char_webhook_secret"

@app.route("/webhooks/payments", methods=["POST"])
def handle_webhook():
    timestamp = request.headers.get("X-Timestamp", "")
    received_sig = request.headers.get("X-Signature", "")
    raw_body = request.get_data()  # raw bytes, before JSON parsing

    # Reject stale events (>5 min)
    if abs(time.time() - int(timestamp)) > 300:
        abort(400, "Timestamp too old")

    # Compute expected signature
    signed_payload = f"{timestamp}.{raw_body.decode('utf-8')}"
    expected_sig = hmac.new(
        WEBHOOK_SECRET.encode("utf-8"),
        signed_payload.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_sig, received_sig):
        abort(403, "Invalid signature")

    event = request.get_json()
    event_type = event["type"]

    if event_type == "payment_intent.succeeded":
        pi = event["data"]["object"]
        fulfill_order(pi["metadata"].get("order_id"))
    elif event_type == "chargeback.created":
        cb_id = event["data"]["object"]["id"]
        open_dispute_case(cb_id)
    elif event_type == "payout.failed":
        handle_payout_failure(event["data"]["object"])

    return "ok", 200
```

### 5.7 Pagination Loop (Pseudocode)

```python
# Fetch all payment intents for a customer using cursor pagination
all_intents = []
cursor = None

while True:
    page = client.payment_intents.list(
        customer_id="cus_01HX8J1N3OQPRS5TUVWXY",
        status="succeeded",
        limit=100,
        after=cursor
    )
    all_intents.extend(page["data"])

    if not page["has_more"]:
        break
    cursor = page["next_cursor"]

print(f"Fetched {len(all_intents)} succeeded intents")
```

### 5.8 Run Settlement Batch with Dry-Run (cURL)

```bash
# Dry-run first to preview settlement
curl -X POST https://api.payments.io/v1/settlement-batches/run \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: settle-dry-run-mer-01HX9K2M4-20240511" \
  -d '{
    "merchant_id": "mer_01HX9K2M4PQRST6UVWXYZ",
    "batch_date": "2024-05-11",
    "dry_run": true
  }'

# Commit if dry-run results look correct
curl -X POST https://api.payments.io/v1/settlement-batches/run \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: settle-commit-mer-01HX9K2M4-20240511" \
  -d '{
    "merchant_id": "mer_01HX9K2M4PQRST6UVWXYZ",
    "batch_date": "2024-05-11",
    "dry_run": false
  }'

# Poll for completion
curl https://api.payments.io/v1/settlement-batches/sb_01HXM1N2O3P4Q5R6S7T8U \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "X-API-Key: $API_KEY"
```

---

*Document maintained by: API Guild, Payments Engineering*  
*Base URL: `https://api.payments.io/v1`*  
*Last updated: 2024-05-12*

