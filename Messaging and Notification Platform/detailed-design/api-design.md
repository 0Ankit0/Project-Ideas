# API Design — Messaging and Notification Platform

**Document version:** 1.0.0
**API version:** v1
**Base URL:** `https://api.notify.io/v1`
**Last updated:** 2025-07-14
**Status:** Approved for Implementation

---

## Table of Contents

1. [Design Principles](#1-design-principles)
2. [Request / Response Envelopes](#2-request--response-envelopes)
3. [Authentication](#3-authentication)
4. [Pagination](#4-pagination)
5. [Messages API](#5-messages-api)
6. [Templates API](#6-templates-api)
7. [Channels API](#7-channels-api)
8. [Providers API](#8-providers-api)
9. [Contacts API](#9-contacts-api)
10. [Subscriptions API](#10-subscriptions-api)
11. [Opt-Outs API](#11-opt-outs-api)
12. [Campaigns API](#12-campaigns-api)
13. [Analytics API](#13-analytics-api)
14. [Webhooks API](#14-webhooks-api)
15. [API Keys API](#15-api-keys-api)
16. [Error Catalog](#16-error-catalog)
17. [Rate Limiting](#17-rate-limiting)
18. [Authorization Matrix](#18-authorization-matrix)
19. [Webhook Payload Contract](#19-webhook-payload-contract)

---

## 1. Design Principles

| Principle | Implementation |
|---|---|
| **REST Semantics** | Nouns as resources, HTTP verbs for actions; `POST` creates, `GET` reads, `PUT` full-replaces, `PATCH` partial-updates, `DELETE` removes. |
| **Versioning** | URI-based (`/v1/`). Breaking changes increment the major segment. Older versions are supported for 12 months after deprecation notice. |
| **Idempotency** | All mutation endpoints accept an `Idempotency-Key` header (UUID v4). Server caches result for 24 h; replays return cached response with `X-Idempotent-Replayed: true`. |
| **Error Envelopes** | All errors return a structured JSON body with `error.code`, `error.message`, `error.details[]`, `request_id`, and `timestamp`. HTTP status codes are authoritative. |
| **Pagination** | Cursor-based pagination via `after` / `before` cursors and `limit`. No offset pagination. |
| **Rate Limiting** | Per-tenant, per-API-key token-bucket. Headers `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` on every response. |
| **Tracing** | Every response includes `X-Request-Id` (server-generated UUID) and echoes client-supplied `X-Correlation-Id`. Both IDs appear in all logs and events. |
| **Content Negotiation** | `Content-Type: application/json` required on all write requests. `Accept: application/json` assumed. |
| **HTTPS Only** | All endpoints enforce TLS 1.2+. HTTP requests receive `301 Moved Permanently`. |
| **Idempotency Window** | 24 hours; after expiry a repeated `Idempotency-Key` is treated as a new request. |

---

## 2. Request / Response Envelopes

### 2.1 Successful Response Envelope

```json
{
  "data": { },
  "meta": {
    "request_id": "req_01HXYZ1234ABCDEF",
    "timestamp": "2025-07-14T10:30:00.000Z",
    "api_version": "v1"
  }
}
```

For collections:

```json
{
  "data": [ ],
  "meta": {
    "request_id": "req_01HXYZ1234ABCDEF",
    "timestamp": "2025-07-14T10:30:00.000Z",
    "api_version": "v1"
  },
  "pagination": {
    "has_more": true,
    "next_cursor": "eyJpZCI6IjAxSFhZWiJ9",
    "prev_cursor": null,
    "total_count": 4821
  }
}
```

### 2.2 Error Response Envelope

```json
{
  "error": {
    "code": "TEMPLATE_NOT_FOUND",
    "message": "The requested template does not exist or has been deleted.",
    "details": [
      {
        "field": "template_id",
        "issue": "Resource with id 'tpl_01HXYZ' not found in tenant 'ten_ACME'."
      }
    ]
  },
  "meta": {
    "request_id": "req_01HXYZ1234ABCDEF",
    "timestamp": "2025-07-14T10:30:01.000Z",
    "api_version": "v1"
  }
}
```

### 2.3 Standard Response Headers

| Header | Description |
|---|---|
| `X-Request-Id` | Server-generated unique request identifier |
| `X-Correlation-Id` | Echo of client-supplied correlation ID |
| `X-RateLimit-Limit` | Maximum requests allowed in current window |
| `X-RateLimit-Remaining` | Requests remaining in current window |
| `X-RateLimit-Reset` | Unix timestamp when the window resets |
| `X-Idempotent-Replayed` | `true` when response is served from idempotency cache |
| `Retry-After` | Seconds to wait before retrying (present on 429 and 503) |

---

## 3. Authentication

All API requests must include one of the following credentials.

### 3.1 Bearer Token (OAuth 2.0 / JWT)

```
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

Tokens are issued by the Identity Service. Claims include `tenant_id`, `scopes[]`, and `sub` (user or service account). Tokens expire after 1 hour.

### 3.2 API Key

```
X-API-Key: nfk_live_Abc123XyzSecretKeyHere
```

API keys are long-lived secrets scoped to a tenant and a set of permissions. Prefix `nfk_live_` for production, `nfk_test_` for sandbox.

### 3.3 Webhook Signature Verification

Inbound webhook callbacks from providers are authenticated via HMAC-SHA256 signature header:

```
X-Notify-Signature: sha256=a3f9...
```

The signature is computed over the raw request body using the webhook secret.

---

## 4. Pagination

All list endpoints use **cursor-based pagination**.

### 4.1 Query Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `limit` | integer | 20 | Records per page; max 100 |
| `after` | string | — | Cursor; return records after this position |
| `before` | string | — | Cursor; return records before this position |
| `sort` | string | `created_at:desc` | Sort field and direction |

### 4.2 Example Request

```
GET /v1/messages?limit=25&after=eyJpZCI6IjAxSFhZWiJ9&sort=created_at:desc
```

### 4.3 Example Pagination Object

```json
"pagination": {
  "has_more": true,
  "next_cursor": "eyJpZCI6IjAxSFhZWi0yIn0=",
  "prev_cursor": "eyJpZCI6IjAxSFhZWi0xIn0=",
  "total_count": 12457
}
```

---

## 5. Messages API

### 5.1 Endpoint Summary

| Method | Path | Description | Required Scope |
|---|---|---|---|
| `POST` | `/v1/messages` | Send a single message | `messages:write` |
| `POST` | `/v1/messages/batch` | Send a batch of messages (up to 1 000) | `messages:write` |
| `GET` | `/v1/messages/{messageId}` | Get message status and metadata | `messages:read` |
| `GET` | `/v1/messages` | List messages with filters | `messages:read` |

### 5.2 POST /v1/messages — Send Single Message

**Request**

```json
{
  "idempotency_key": "user-1234-order-confirm-20250714",
  "channel": "email",
  "priority": "high",
  "template_id": "tpl_01HXYZ_ORDER_CONFIRM",
  "template_version": "3.2.0",
  "recipient": {
    "contact_id": "con_01HXYZ_USER1234",
    "email": "jane.doe@example.com",
    "name": "Jane Doe",
    "locale": "en-US",
    "timezone": "America/New_York"
  },
  "variables": {
    "order": {
      "id": "ORD-9987",
      "total": 149.99,
      "currency": "USD",
      "items": [
        { "name": "Widget Pro", "qty": 2, "price": 74.99 }
      ],
      "tracking_url": "https://track.example.com/ORD-9987"
    }
  },
  "metadata": {
    "source_system": "order-service",
    "correlation_id": "txn_ABC123",
    "tags": ["order", "transactional"]
  },
  "scheduled_at": null,
  "expires_at": "2025-07-14T14:00:00.000Z"
}
```

**Response — 202 Accepted**

```json
{
  "data": {
    "message_id": "msg_01HXYZ_SEND_A1B2C3",
    "status": "ACCEPTED",
    "channel": "email",
    "priority": "high",
    "template_id": "tpl_01HXYZ_ORDER_CONFIRM",
    "template_version": "3.2.0",
    "recipient": {
      "contact_id": "con_01HXYZ_USER1234",
      "email": "jane.doe@example.com"
    },
    "idempotency_key": "user-1234-order-confirm-20250714",
    "queued_at": "2025-07-14T10:30:00.123Z",
    "estimated_delivery_by": "2025-07-14T10:30:05.000Z"
  },
  "meta": {
    "request_id": "req_01HXYZ1234ABCDEF",
    "timestamp": "2025-07-14T10:30:00.500Z",
    "api_version": "v1"
  }
}
```

**Error Responses**

| HTTP Status | Error Code | Condition |
|---|---|---|
| 400 | `VALIDATION_ERROR` | Missing required field or invalid type |
| 400 | `INVALID_CHANNEL` | Specified channel is not configured |
| 400 | `INVALID_TEMPLATE_VERSION` | Template version is not published |
| 404 | `TEMPLATE_NOT_FOUND` | Template ID does not exist |
| 409 | `IDEMPOTENCY_CONFLICT` | Key reused with different payload |
| 422 | `RECIPIENT_OPT_OUT` | Recipient has opted out of this channel |
| 422 | `MISSING_REQUIRED_VARIABLE` | Template variable missing in payload |
| 429 | `RATE_LIMIT_EXCEEDED` | Tenant rate limit hit |

### 5.3 POST /v1/messages/batch — Send Batch

**Request**

```json
{
  "messages": [
    {
      "idempotency_key": "batch-msg-001",
      "channel": "sms",
      "template_id": "tpl_01HXYZ_PROMO_SMS",
      "recipient": {
        "contact_id": "con_01HXYZ_USER0001",
        "phone": "+14155551234"
      },
      "variables": { "promo_code": "SUMMER25" }
    },
    {
      "idempotency_key": "batch-msg-002",
      "channel": "sms",
      "template_id": "tpl_01HXYZ_PROMO_SMS",
      "recipient": {
        "contact_id": "con_01HXYZ_USER0002",
        "phone": "+14155555678"
      },
      "variables": { "promo_code": "SUMMER25" }
    }
  ],
  "metadata": {
    "campaign_id": "cmp_01HXYZ_SUMMER",
    "batch_label": "summer-promo-wave-1"
  }
}
```

**Response — 202 Accepted**

```json
{
  "data": {
    "batch_id": "bat_01HXYZ_BATCH_001",
    "submitted_count": 2,
    "accepted_count": 2,
    "rejected_count": 0,
    "status": "PROCESSING",
    "results": [
      {
        "index": 0,
        "idempotency_key": "batch-msg-001",
        "message_id": "msg_01HXYZ_M001",
        "status": "ACCEPTED"
      },
      {
        "index": 1,
        "idempotency_key": "batch-msg-002",
        "message_id": "msg_01HXYZ_M002",
        "status": "ACCEPTED"
      }
    ]
  },
  "meta": {
    "request_id": "req_01HXYZ_BATCH_REQ",
    "timestamp": "2025-07-14T10:30:00.500Z",
    "api_version": "v1"
  }
}
```

### 5.4 GET /v1/messages/{messageId} — Get Message Status

**Response — 200 OK**

```json
{
  "data": {
    "message_id": "msg_01HXYZ_SEND_A1B2C3",
    "status": "DELIVERED",
    "channel": "email",
    "priority": "high",
    "template_id": "tpl_01HXYZ_ORDER_CONFIRM",
    "template_version": "3.2.0",
    "recipient": {
      "contact_id": "con_01HXYZ_USER1234",
      "email": "jane.doe@example.com"
    },
    "provider": "sendgrid",
    "provider_message_id": "SG.abc123xyz456",
    "timeline": [
      { "status": "ACCEPTED",           "at": "2025-07-14T10:30:00.123Z" },
      { "status": "QUEUED",             "at": "2025-07-14T10:30:00.201Z" },
      { "status": "DISPATCHING",        "at": "2025-07-14T10:30:00.950Z" },
      { "status": "PROVIDER_ACCEPTED",  "at": "2025-07-14T10:30:01.480Z" },
      { "status": "DELIVERED",          "at": "2025-07-14T10:30:04.800Z" }
    ],
    "open_count": 1,
    "click_count": 2,
    "queued_at": "2025-07-14T10:30:00.201Z",
    "delivered_at": "2025-07-14T10:30:04.800Z",
    "created_at": "2025-07-14T10:30:00.100Z"
  },
  "meta": {
    "request_id": "req_01HXYZ_STATUS_REQ",
    "timestamp": "2025-07-14T11:00:00.000Z",
    "api_version": "v1"
  }
}
```

### 5.5 GET /v1/messages — List Messages

**Query Parameters**

| Parameter | Type | Description |
|---|---|---|
| `status` | string | Filter by status: `ACCEPTED`, `QUEUED`, `DELIVERED`, `FAILED` |
| `channel` | string | Filter by channel: `email`, `sms`, `push`, `webhook` |
| `template_id` | string | Filter by template |
| `contact_id` | string | Filter by recipient contact |
| `from` | ISO 8601 | Start of created_at range |
| `to` | ISO 8601 | End of created_at range |
| `limit` | integer | Page size (default 20, max 100) |
| `after` | string | Pagination cursor |

---

## 6. Templates API

### 6.1 Endpoint Summary

| Method | Path | Description | Required Scope |
|---|---|---|---|
| `POST` | `/v1/templates` | Create a new template | `templates:write` |
| `GET` | `/v1/templates` | List templates | `templates:read` |
| `GET` | `/v1/templates/{templateId}` | Get template details | `templates:read` |
| `PUT` | `/v1/templates/{templateId}` | Replace template (creates new draft) | `templates:write` |
| `DELETE` | `/v1/templates/{templateId}` | Soft-delete template | `templates:delete` |
| `POST` | `/v1/templates/{templateId}/publish` | Publish current draft version | `templates:publish` |
| `GET` | `/v1/templates/{templateId}/versions` | List all versions | `templates:read` |
| `POST` | `/v1/templates/{templateId}/preview` | Render preview with mock variables | `templates:read` |

### 6.2 POST /v1/templates — Create Template

**Request**

```json
{
  "name": "order-confirmation-email",
  "description": "Transactional order confirmation sent after checkout",
  "channel": "email",
  "category": "transactional",
  "locale": "en-US",
  "subject": "Your order {{order.id}} has been confirmed!",
  "html_body": "<!DOCTYPE html><html><body><h1>Hi {{contact.name}},</h1><p>Order <strong>{{order.id}}</strong> is confirmed. Total: {{formatCurrency order.total order.currency}}</p>{{#if order.tracking_url}}<p><a href=\"{{order.tracking_url}}\">Track your order</a></p>{{/if}}</body></html>",
  "text_body": "Hi {{contact.name}}, your order {{order.id}} is confirmed. Total: {{formatCurrency order.total order.currency}}.",
  "preheader": "Order {{order.id}} confirmed — {{formatCurrency order.total order.currency}}",
  "variables_schema": [
    { "name": "contact.name",         "type": "string",  "required": true  },
    { "name": "order.id",             "type": "string",  "required": true  },
    { "name": "order.total",          "type": "number",  "required": true  },
    { "name": "order.currency",       "type": "string",  "required": true  },
    { "name": "order.tracking_url",   "type": "string",  "required": false }
  ],
  "tags": ["order", "transactional", "checkout"],
  "metadata": { "owner_team": "platform-notifications" }
}
```

**Response — 201 Created**

```json
{
  "data": {
    "template_id": "tpl_01HXYZ_ORDER_CONFIRM",
    "name": "order-confirmation-email",
    "channel": "email",
    "status": "DRAFT",
    "current_version": "1.0.0",
    "locale": "en-US",
    "category": "transactional",
    "created_at": "2025-07-14T10:00:00.000Z",
    "updated_at": "2025-07-14T10:00:00.000Z"
  },
  "meta": {
    "request_id": "req_01HXYZ_TPL_CREATE",
    "timestamp": "2025-07-14T10:00:00.100Z",
    "api_version": "v1"
  }
}
```

### 6.3 POST /v1/templates/{templateId}/preview — Preview Template

**Request**

```json
{
  "variables": {
    "contact": { "name": "Jane Doe" },
    "order": {
      "id": "ORD-PREVIEW-001",
      "total": 149.99,
      "currency": "USD",
      "tracking_url": "https://track.example.com/ORD-PREVIEW-001"
    }
  },
  "locale": "en-US"
}
```

**Response — 200 OK**

```json
{
  "data": {
    "template_id": "tpl_01HXYZ_ORDER_CONFIRM",
    "version": "1.0.0",
    "channel": "email",
    "rendered": {
      "subject": "Your order ORD-PREVIEW-001 has been confirmed!",
      "html_body": "<!DOCTYPE html><html><body><h1>Hi Jane Doe,</h1><p>Order <strong>ORD-PREVIEW-001</strong> is confirmed. Total: $149.99</p><p><a href=\"https://track.example.com/ORD-PREVIEW-001\">Track your order</a></p></body></html>",
      "text_body": "Hi Jane Doe, your order ORD-PREVIEW-001 is confirmed. Total: $149.99.",
      "preheader": "Order ORD-PREVIEW-001 confirmed — $149.99"
    },
    "warnings": [],
    "missing_variables": []
  },
  "meta": {
    "request_id": "req_01HXYZ_TPL_PREVIEW",
    "timestamp": "2025-07-14T10:01:00.000Z",
    "api_version": "v1"
  }
}
```

### 6.4 POST /v1/templates/{templateId}/publish — Publish Version

**Request**

```json
{
  "version": "1.0.0",
  "release_notes": "Initial production release of order confirmation email.",
  "notify_subscribers": true
}
```

**Response — 200 OK**

```json
{
  "data": {
    "template_id": "tpl_01HXYZ_ORDER_CONFIRM",
    "published_version": "1.0.0",
    "status": "PUBLISHED",
    "published_at": "2025-07-14T10:05:00.000Z",
    "published_by": "usr_01HXYZ_ADMIN"
  },
  "meta": {
    "request_id": "req_01HXYZ_TPL_PUBLISH",
    "timestamp": "2025-07-14T10:05:00.100Z",
    "api_version": "v1"
  }
}
```

### 6.5 Template Error Codes

| Error Code | HTTP Status | Condition |
|---|---|---|
| `TEMPLATE_NOT_FOUND` | 404 | Template ID not found |
| `TEMPLATE_ALREADY_PUBLISHED` | 409 | Cannot modify a published template; create a new version |
| `TEMPLATE_SYNTAX_ERROR` | 422 | Handlebars/Jinja2 syntax error in body |
| `MISSING_REQUIRED_VARIABLE_SCHEMA` | 422 | Variable marked required has no default and is undeclared |
| `TEMPLATE_VERSION_NOT_DRAFT` | 409 | Publish only allowed on DRAFT version |
| `TEMPLATE_IN_USE` | 409 | Cannot delete a template referenced by active campaigns |

---

## 7. Channels API

### 7.1 Endpoint Summary

| Method | Path | Description | Required Scope |
|---|---|---|---|
| `GET` | `/v1/channels` | List configured channels | `channels:read` |
| `POST` | `/v1/channels` | Create/configure a channel | `channels:write` |
| `GET` | `/v1/channels/{channelId}` | Get channel configuration | `channels:read` |
| `PUT` | `/v1/channels/{channelId}` | Update channel configuration | `channels:write` |
| `DELETE` | `/v1/channels/{channelId}` | Disable and delete channel | `channels:delete` |

### 7.2 POST /v1/channels — Create Channel

**Request**

```json
{
  "name": "Primary Email Channel",
  "type": "email",
  "description": "Main transactional email channel via SendGrid",
  "provider_config_id": "prc_01HXYZ_SENDGRID_PRIMARY",
  "settings": {
    "from_address": "noreply@acme.com",
    "from_name": "ACME Notifications",
    "reply_to": "support@acme.com",
    "track_opens": true,
    "track_clicks": true,
    "sandbox_mode": false
  },
  "priority": 1,
  "is_active": true
}
```

**Response — 201 Created**

```json
{
  "data": {
    "channel_id": "chn_01HXYZ_EMAIL_PRIMARY",
    "name": "Primary Email Channel",
    "type": "email",
    "provider_config_id": "prc_01HXYZ_SENDGRID_PRIMARY",
    "status": "ACTIVE",
    "priority": 1,
    "created_at": "2025-07-14T10:00:00.000Z"
  },
  "meta": {
    "request_id": "req_01HXYZ_CHN_CREATE",
    "timestamp": "2025-07-14T10:00:00.100Z",
    "api_version": "v1"
  }
}
```

### 7.3 Channel Error Codes

| Error Code | HTTP Status | Condition |
|---|---|---|
| `CHANNEL_NOT_FOUND` | 404 | Channel ID not found |
| `CHANNEL_TYPE_IMMUTABLE` | 409 | Channel type cannot be changed after creation |
| `DUPLICATE_CHANNEL_NAME` | 409 | A channel with this name already exists |
| `PROVIDER_CONFIG_NOT_FOUND` | 404 | Referenced provider config does not exist |

---

## 8. Providers API

### 8.1 Endpoint Summary

| Method | Path | Description | Required Scope |
|---|---|---|---|
| `GET` | `/v1/providers` | List provider configurations | `providers:read` |
| `POST` | `/v1/providers` | Create a provider configuration | `providers:write` |
| `GET` | `/v1/providers/{providerId}` | Get provider configuration | `providers:read` |
| `PUT` | `/v1/providers/{providerId}` | Update provider configuration | `providers:write` |
| `DELETE` | `/v1/providers/{providerId}` | Delete provider configuration | `providers:delete` |
| `POST` | `/v1/providers/{providerId}/test` | Send a test message to verify connectivity | `providers:write` |

### 8.2 POST /v1/providers — Create Provider Config

**Request**

```json
{
  "name": "SendGrid Production",
  "provider_type": "sendgrid",
  "description": "Primary SendGrid account for transactional email",
  "credentials": {
    "api_key": "SG.REDACTED_API_KEY"
  },
  "settings": {
    "ip_pool_name": "transactional",
    "click_tracking": true,
    "open_tracking": true,
    "sandbox_mode": false
  },
  "rate_limits": {
    "messages_per_second": 100,
    "messages_per_day": 500000
  },
  "is_active": true
}
```

**Response — 201 Created**

```json
{
  "data": {
    "provider_config_id": "prc_01HXYZ_SENDGRID_PRIMARY",
    "name": "SendGrid Production",
    "provider_type": "sendgrid",
    "status": "ACTIVE",
    "credentials_stored": true,
    "last_tested_at": null,
    "created_at": "2025-07-14T10:00:00.000Z"
  },
  "meta": {
    "request_id": "req_01HXYZ_PRV_CREATE",
    "timestamp": "2025-07-14T10:00:00.100Z",
    "api_version": "v1"
  }
}
```

### 8.3 POST /v1/providers/{providerId}/test — Test Connectivity

**Request**

```json
{
  "test_recipient": {
    "email": "deliverability-test@acme.com"
  }
}
```

**Response — 200 OK**

```json
{
  "data": {
    "provider_config_id": "prc_01HXYZ_SENDGRID_PRIMARY",
    "test_status": "SUCCESS",
    "latency_ms": 312,
    "provider_message_id": "SG.test_abc123",
    "tested_at": "2025-07-14T10:10:00.000Z"
  },
  "meta": {
    "request_id": "req_01HXYZ_PRV_TEST",
    "timestamp": "2025-07-14T10:10:00.400Z",
    "api_version": "v1"
  }
}
```

---

## 9. Contacts API

### 9.1 Endpoint Summary

| Method | Path | Description | Required Scope |
|---|---|---|---|
| `POST` | `/v1/contacts` | Create a contact | `contacts:write` |
| `GET` | `/v1/contacts` | List contacts | `contacts:read` |
| `GET` | `/v1/contacts/{contactId}` | Get contact details | `contacts:read` |
| `PUT` | `/v1/contacts/{contactId}` | Update contact | `contacts:write` |
| `DELETE` | `/v1/contacts/{contactId}` | Soft-delete contact | `contacts:delete` |
| `GET` | `/v1/contacts/{contactId}/subscriptions` | Get contact subscription state | `contacts:read` |

### 9.2 POST /v1/contacts — Create Contact

**Request**

```json
{
  "external_id": "usr_CRM_98765",
  "email": "jane.doe@example.com",
  "phone": "+14155559876",
  "name": "Jane Doe",
  "locale": "en-US",
  "timezone": "America/New_York",
  "attributes": {
    "plan": "premium",
    "signup_date": "2024-03-15",
    "account_type": "individual"
  },
  "channel_addresses": {
    "email": "jane.doe@example.com",
    "sms": "+14155559876",
    "push_tokens": [
      { "platform": "ios",     "token": "apns_token_abc123" },
      { "platform": "android", "token": "fcm_token_xyz789" }
    ]
  }
}
```

**Response — 201 Created**

```json
{
  "data": {
    "contact_id": "con_01HXYZ_USER_JANE",
    "external_id": "usr_CRM_98765",
    "email": "jane.doe@example.com",
    "phone": "+14155559876",
    "name": "Jane Doe",
    "locale": "en-US",
    "timezone": "America/New_York",
    "status": "ACTIVE",
    "created_at": "2025-07-14T10:00:00.000Z",
    "updated_at": "2025-07-14T10:00:00.000Z"
  },
  "meta": {
    "request_id": "req_01HXYZ_CON_CREATE",
    "timestamp": "2025-07-14T10:00:00.100Z",
    "api_version": "v1"
  }
}
```

### 9.3 GET /v1/contacts/{contactId}/subscriptions — Get Subscriptions

**Response — 200 OK**

```json
{
  "data": {
    "contact_id": "con_01HXYZ_USER_JANE",
    "subscriptions": [
      {
        "subscription_group_id": "grp_01HXYZ_MARKETING",
        "group_name": "Marketing Emails",
        "channel": "email",
        "status": "SUBSCRIBED",
        "subscribed_at": "2025-01-10T09:00:00.000Z"
      },
      {
        "subscription_group_id": "grp_01HXYZ_TRANSACTIONAL",
        "group_name": "Transactional",
        "channel": "email",
        "status": "SUBSCRIBED",
        "subscribed_at": "2024-03-15T12:00:00.000Z"
      },
      {
        "subscription_group_id": "grp_01HXYZ_SMS_PROMO",
        "group_name": "SMS Promotions",
        "channel": "sms",
        "status": "UNSUBSCRIBED",
        "unsubscribed_at": "2025-04-01T08:00:00.000Z",
        "opt_out_source": "USER_REQUEST"
      }
    ]
  },
  "meta": {
    "request_id": "req_01HXYZ_SUB_LIST",
    "timestamp": "2025-07-14T10:00:00.100Z",
    "api_version": "v1"
  }
}
```

---

## 10. Subscriptions API

### 10.1 Endpoint Summary

| Method | Path | Description | Required Scope |
|---|---|---|---|
| `POST` | `/v1/subscriptions` | Subscribe a contact to a group | `subscriptions:write` |
| `GET` | `/v1/subscriptions` | List subscriptions with filters | `subscriptions:read` |
| `DELETE` | `/v1/subscriptions/{subscriptionId}` | Unsubscribe (opt-out) | `subscriptions:write` |

### 10.2 POST /v1/subscriptions — Create Subscription

**Request**

```json
{
  "contact_id": "con_01HXYZ_USER_JANE",
  "subscription_group_id": "grp_01HXYZ_WEEKLY_DIGEST",
  "channel": "email",
  "opt_in_source": "WEBSITE_SIGNUP",
  "opt_in_ip": "203.0.113.42",
  "opt_in_user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...",
  "double_opt_in": true
}
```

**Response — 201 Created**

```json
{
  "data": {
    "subscription_id": "sub_01HXYZ_JANE_DIGEST",
    "contact_id": "con_01HXYZ_USER_JANE",
    "subscription_group_id": "grp_01HXYZ_WEEKLY_DIGEST",
    "channel": "email",
    "status": "PENDING_CONFIRMATION",
    "double_opt_in": true,
    "confirmation_sent_at": "2025-07-14T10:00:01.000Z",
    "created_at": "2025-07-14T10:00:00.000Z"
  },
  "meta": {
    "request_id": "req_01HXYZ_SUB_CREATE",
    "timestamp": "2025-07-14T10:00:00.100Z",
    "api_version": "v1"
  }
}
```

---

## 11. Opt-Outs API

### 11.1 Endpoint Summary

| Method | Path | Description | Required Scope |
|---|---|---|---|
| `POST` | `/v1/opt-outs` | Record an opt-out for a contact | `opt-outs:write` |
| `GET` | `/v1/opt-outs` | List opt-outs with filters | `opt-outs:read` |
| `DELETE` | `/v1/opt-outs/{optOutId}` | Re-opt-in (remove opt-out record) | `opt-outs:write` |

### 11.2 POST /v1/opt-outs — Record Opt-Out

**Request**

```json
{
  "contact_id": "con_01HXYZ_USER_JANE",
  "channel": "email",
  "scope": "ALL",
  "source": "UNSUBSCRIBE_LINK",
  "reason": "Too many emails",
  "ip_address": "203.0.113.42",
  "user_agent": "Mozilla/5.0 ...",
  "message_id": "msg_01HXYZ_SEND_A1B2C3"
}
```

**Response — 201 Created**

```json
{
  "data": {
    "opt_out_id": "oot_01HXYZ_JANE_EMAIL",
    "contact_id": "con_01HXYZ_USER_JANE",
    "channel": "email",
    "scope": "ALL",
    "source": "UNSUBSCRIBE_LINK",
    "opted_out_at": "2025-07-14T10:00:00.000Z",
    "is_global": true
  },
  "meta": {
    "request_id": "req_01HXYZ_OPT_CREATE",
    "timestamp": "2025-07-14T10:00:00.100Z",
    "api_version": "v1"
  }
}
```

### 11.3 Opt-Out Scopes

| Scope Value | Meaning |
|---|---|
| `ALL` | Opt out of all messages on this channel |
| `MARKETING` | Opt out of marketing/promotional only |
| `GROUP:{groupId}` | Opt out of a specific subscription group |

---

## 12. Campaigns API

### 12.1 Endpoint Summary

| Method | Path | Description | Required Scope |
|---|---|---|---|
| `POST` | `/v1/campaigns` | Create a campaign | `campaigns:write` |
| `GET` | `/v1/campaigns` | List campaigns | `campaigns:read` |
| `GET` | `/v1/campaigns/{campaignId}` | Get campaign details | `campaigns:read` |
| `PUT` | `/v1/campaigns/{campaignId}` | Update campaign (only if DRAFT) | `campaigns:write` |
| `POST` | `/v1/campaigns/{campaignId}/schedule` | Schedule campaign send | `campaigns:schedule` |
| `POST` | `/v1/campaigns/{campaignId}/cancel` | Cancel a scheduled campaign | `campaigns:write` |
| `GET` | `/v1/campaigns/{campaignId}/stats` | Get delivery statistics | `campaigns:read` |

### 12.2 POST /v1/campaigns — Create Campaign

**Request**

```json
{
  "name": "Summer Sale 2025",
  "description": "Promotional email blast for summer sale event",
  "channel": "email",
  "template_id": "tpl_01HXYZ_SUMMER_PROMO",
  "template_version": "2.1.0",
  "audience": {
    "type": "SEGMENT",
    "segment_filters": [
      { "field": "attributes.plan", "operator": "eq",  "value": "premium" },
      { "field": "attributes.signup_date", "operator": "gte", "value": "2024-01-01" }
    ]
  },
  "variables": {
    "promo_code": "SUMMER25",
    "sale_end_date": "2025-07-31"
  },
  "tags": ["promotion", "summer-2025"]
}
```

**Response — 201 Created**

```json
{
  "data": {
    "campaign_id": "cmp_01HXYZ_SUMMER_2025",
    "name": "Summer Sale 2025",
    "channel": "email",
    "status": "DRAFT",
    "estimated_recipients": 14823,
    "created_at": "2025-07-14T10:00:00.000Z"
  },
  "meta": {
    "request_id": "req_01HXYZ_CMP_CREATE",
    "timestamp": "2025-07-14T10:00:00.100Z",
    "api_version": "v1"
  }
}
```

### 12.3 POST /v1/campaigns/{campaignId}/schedule — Schedule Campaign

**Request**

```json
{
  "send_at": "2025-07-20T09:00:00.000Z",
  "timezone": "America/New_York",
  "send_rate": {
    "messages_per_hour": 5000
  }
}
```

### 12.4 GET /v1/campaigns/{campaignId}/stats — Campaign Statistics

**Response — 200 OK**

```json
{
  "data": {
    "campaign_id": "cmp_01HXYZ_SUMMER_2025",
    "stats": {
      "total_recipients": 14823,
      "sent": 14823,
      "delivered": 14201,
      "bounced": 312,
      "opened": 5880,
      "clicked": 1760,
      "unsubscribed": 94,
      "complained": 3,
      "failed": 310
    },
    "rates": {
      "delivery_rate": 95.8,
      "open_rate":     41.4,
      "click_rate":    12.4,
      "bounce_rate":    2.1,
      "unsubscribe_rate": 0.7
    },
    "as_of": "2025-07-21T12:00:00.000Z"
  },
  "meta": {
    "request_id": "req_01HXYZ_CMP_STATS",
    "timestamp": "2025-07-21T12:00:00.100Z",
    "api_version": "v1"
  }
}
```

---

## 13. Analytics API

### 13.1 Endpoint Summary

| Method | Path | Description | Required Scope |
|---|---|---|---|
| `GET` | `/v1/analytics/overview` | Aggregated delivery metrics across all channels | `analytics:read` |
| `GET` | `/v1/analytics/messages` | Message-level analytics with time series | `analytics:read` |
| `GET` | `/v1/analytics/channels` | Per-channel breakdown | `analytics:read` |
| `GET` | `/v1/analytics/providers` | Per-provider performance metrics | `analytics:read` |

### 13.2 GET /v1/analytics/overview

**Query Parameters:** `from`, `to`, `granularity` (`hour`, `day`, `week`, `month`)

**Response — 200 OK**

```json
{
  "data": {
    "period": { "from": "2025-07-01T00:00:00Z", "to": "2025-07-14T23:59:59Z" },
    "totals": {
      "sent": 2847391,
      "delivered": 2731224,
      "failed": 116167,
      "opened": 1092489,
      "clicked": 218499,
      "bounced": 58432,
      "unsubscribed": 2847
    },
    "delivery_rate": 95.9,
    "open_rate": 40.0,
    "click_rate": 8.0,
    "time_series": [
      { "period": "2025-07-01", "sent": 198234, "delivered": 190012, "failed": 8222 },
      { "period": "2025-07-02", "sent": 203811, "delivered": 195480, "failed": 8331 }
    ]
  },
  "meta": {
    "request_id": "req_01HXYZ_ANALYTICS_OVW",
    "timestamp": "2025-07-14T12:00:00.000Z",
    "api_version": "v1"
  }
}
```

---

## 14. Webhooks API

### 14.1 Endpoint Summary

| Method | Path | Description | Required Scope |
|---|---|---|---|
| `POST` | `/v1/webhooks` | Register a webhook endpoint | `webhooks:write` |
| `GET` | `/v1/webhooks` | List registered webhooks | `webhooks:read` |
| `GET` | `/v1/webhooks/{webhookId}` | Get webhook details | `webhooks:read` |
| `PUT` | `/v1/webhooks/{webhookId}` | Update webhook configuration | `webhooks:write` |
| `DELETE` | `/v1/webhooks/{webhookId}` | Remove webhook | `webhooks:delete` |
| `POST` | `/v1/webhooks/{webhookId}/test` | Send a test event to the endpoint | `webhooks:write` |

### 14.2 POST /v1/webhooks — Register Webhook

**Request**

```json
{
  "name": "Delivery Events Sink",
  "url": "https://events.acme.com/notify/inbound",
  "events": [
    "message.delivered",
    "message.failed",
    "message.bounced",
    "message.opened",
    "message.clicked",
    "contact.unsubscribed"
  ],
  "secret": "whsec_my_webhook_signing_secret_here",
  "is_active": true,
  "retry_policy": {
    "max_attempts": 5,
    "backoff": "exponential"
  },
  "metadata": { "environment": "production" }
}
```

**Response — 201 Created**

```json
{
  "data": {
    "webhook_id": "wh_01HXYZ_DELIVERY_SINK",
    "name": "Delivery Events Sink",
    "url": "https://events.acme.com/notify/inbound",
    "events": ["message.delivered", "message.failed", "message.bounced", "message.opened", "message.clicked", "contact.unsubscribed"],
    "status": "ACTIVE",
    "created_at": "2025-07-14T10:00:00.000Z"
  },
  "meta": {
    "request_id": "req_01HXYZ_WH_CREATE",
    "timestamp": "2025-07-14T10:00:00.100Z",
    "api_version": "v1"
  }
}
```

---

## 15. API Keys API

### 15.1 Endpoint Summary

| Method | Path | Description | Required Scope |
|---|---|---|---|
| `POST` | `/v1/api-keys` | Create an API key | `api-keys:write` |
| `GET` | `/v1/api-keys` | List API keys | `api-keys:read` |
| `DELETE` | `/v1/api-keys/{keyId}` | Revoke an API key | `api-keys:delete` |

### 15.2 POST /v1/api-keys — Create API Key

**Request**

```json
{
  "name": "Order Service Production Key",
  "description": "Used by order-service to send transactional messages",
  "scopes": ["messages:write", "templates:read", "contacts:write"],
  "expires_at": "2026-07-14T00:00:00.000Z",
  "allowed_ips": ["10.0.0.0/8", "172.16.0.0/12"]
}
```

**Response — 201 Created**

```json
{
  "data": {
    "key_id": "key_01HXYZ_ORDER_SVC",
    "name": "Order Service Production Key",
    "key": "nfk_live_Abc123XyzSecretKeyHere_FULL_KEY_SHOWN_ONCE",
    "key_prefix": "nfk_live_Abc123",
    "scopes": ["messages:write", "templates:read", "contacts:write"],
    "expires_at": "2026-07-14T00:00:00.000Z",
    "created_at": "2025-07-14T10:00:00.000Z"
  },
  "meta": {
    "request_id": "req_01HXYZ_APIKEY_CREATE",
    "timestamp": "2025-07-14T10:00:00.100Z",
    "api_version": "v1"
  }
}
```

> **Security notice:** The full API key value is returned **only once** at creation time. Store it securely immediately; it cannot be retrieved again.

---

## 16. Error Catalog

| Code | HTTP Status | Description | Resolution |
|---|---|---|---|
| `VALIDATION_ERROR` | 400 | Request body failed schema validation | Check `error.details[]` for field-level errors |
| `INVALID_CHANNEL` | 400 | Channel not supported or not configured | Use `GET /v1/channels` to list valid channels |
| `INVALID_TEMPLATE_VERSION` | 400 | Specified template version is not published | Publish the version or use the latest published version |
| `MISSING_REQUIRED_VARIABLE` | 422 | Template requires a variable not present in payload | Provide all required variables defined in template schema |
| `UNAUTHENTICATED` | 401 | Missing or invalid authentication credential | Provide valid Bearer token or API key |
| `TOKEN_EXPIRED` | 401 | JWT has expired | Re-authenticate to obtain a new token |
| `FORBIDDEN` | 403 | Caller lacks required scope for this action | Request an API key with the necessary scope |
| `TENANT_SUSPENDED` | 403 | Tenant account is suspended | Contact support |
| `TEMPLATE_NOT_FOUND` | 404 | Template ID not found in tenant | Verify the template ID exists for this tenant |
| `CONTACT_NOT_FOUND` | 404 | Contact ID not found | Verify the contact ID or create it first |
| `CHANNEL_NOT_FOUND` | 404 | Channel ID not found | Verify the channel ID |
| `PROVIDER_NOT_FOUND` | 404 | Provider config ID not found | Verify the provider config ID |
| `CAMPAIGN_NOT_FOUND` | 404 | Campaign ID not found | Verify the campaign ID |
| `WEBHOOK_NOT_FOUND` | 404 | Webhook ID not found | Verify the webhook ID |
| `IDEMPOTENCY_CONFLICT` | 409 | Idempotency key reused with different request body | Use a unique idempotency key per unique request |
| `TEMPLATE_ALREADY_PUBLISHED` | 409 | Template version is already published and immutable | Create a new template version |
| `TEMPLATE_IN_USE` | 409 | Template is referenced by active campaigns | Cancel or reassign campaigns before deleting |
| `DUPLICATE_CHANNEL_NAME` | 409 | A channel with this name already exists | Use a unique channel name |
| `RECIPIENT_OPT_OUT` | 422 | Recipient has opted out of this channel/group | Respect opt-out; do not resend |
| `MISSING_REQUIRED_VARIABLE_SCHEMA` | 422 | Variable in schema not provided in send request | Provide all required variables |
| `TEMPLATE_SYNTAX_ERROR` | 422 | Invalid Handlebars / Jinja2 syntax | Fix syntax errors in template body |
| `BATCH_EXCEEDS_LIMIT` | 422 | Batch contains more than 1 000 messages | Split into smaller batches |
| `RATE_LIMIT_EXCEEDED` | 429 | Tenant or API key rate limit exceeded | Wait until `Retry-After` and reduce request rate |
| `PROVIDER_UNAVAILABLE` | 503 | All configured providers are unavailable | Retry after `Retry-After`; check provider status |
| `INTERNAL_ERROR` | 500 | Unexpected server-side error | Retry with exponential backoff; contact support if persistent |

---

## 17. Rate Limiting

Token-bucket algorithm, enforced per `(tenant_id, api_key_id)` pair.

| Endpoint Group | Limit | Window | Scope | Burst |
|---|---|---|---|---|
| `POST /v1/messages` | 1 000 req | per second | Per tenant | 2 000 |
| `POST /v1/messages/batch` | 50 req | per second | Per tenant | 100 |
| `POST /v1/templates` | 60 req | per minute | Per tenant | 20 |
| Template reads | 600 req | per minute | Per tenant | 200 |
| `POST /v1/campaigns` | 100 req | per hour | Per tenant | 10 |
| Campaign reads | 300 req | per minute | Per tenant | 60 |
| `GET /v1/analytics/*` | 120 req | per minute | Per tenant | 30 |
| `POST /v1/contacts` | 500 req | per minute | Per tenant | 200 |
| Contact reads | 1 000 req | per minute | Per tenant | 400 |
| Webhooks management | 60 req | per minute | Per tenant | 10 |
| `POST /v1/api-keys` | 20 req | per hour | Per tenant | 5 |

When a rate limit is exceeded, the server responds with `429 Too Many Requests` and includes:
- `Retry-After: <seconds>` header
- `X-RateLimit-Limit`, `X-RateLimit-Remaining: 0`, `X-RateLimit-Reset: <unix_timestamp>`

---

## 18. Authorization Matrix

| Scope | Description | Grants Access To |
|---|---|---|
| `messages:read` | Read message status and history | `GET /v1/messages`, `GET /v1/messages/{id}` |
| `messages:write` | Send messages and batches | `POST /v1/messages`, `POST /v1/messages/batch` |
| `templates:read` | View templates and versions | `GET /v1/templates/**` |
| `templates:write` | Create and update templates | `POST /v1/templates`, `PUT /v1/templates/{id}` |
| `templates:publish` | Publish template versions | `POST /v1/templates/{id}/publish` |
| `templates:delete` | Delete templates | `DELETE /v1/templates/{id}` |
| `channels:read` | View channel configurations | `GET /v1/channels/**` |
| `channels:write` | Create and update channels | `POST /v1/channels`, `PUT /v1/channels/{id}` |
| `channels:delete` | Delete channels | `DELETE /v1/channels/{id}` |
| `providers:read` | View provider configs | `GET /v1/providers/**` |
| `providers:write` | Create, update and test providers | `POST /v1/providers`, `PUT /v1/providers/{id}`, `POST /v1/providers/{id}/test` |
| `providers:delete` | Delete provider configs | `DELETE /v1/providers/{id}` |
| `contacts:read` | View contacts and subscriptions | `GET /v1/contacts/**` |
| `contacts:write` | Create and update contacts | `POST /v1/contacts`, `PUT /v1/contacts/{id}` |
| `contacts:delete` | Soft-delete contacts | `DELETE /v1/contacts/{id}` |
| `subscriptions:read` | View subscription state | `GET /v1/subscriptions` |
| `subscriptions:write` | Manage subscriptions | `POST /v1/subscriptions`, `DELETE /v1/subscriptions/{id}` |
| `opt-outs:read` | View opt-out records | `GET /v1/opt-outs` |
| `opt-outs:write` | Create and revoke opt-outs | `POST /v1/opt-outs`, `DELETE /v1/opt-outs/{id}` |
| `campaigns:read` | View campaigns and stats | `GET /v1/campaigns/**` |
| `campaigns:write` | Create and update campaigns | `POST /v1/campaigns`, `PUT /v1/campaigns/{id}`, `POST /v1/campaigns/{id}/cancel` |
| `campaigns:schedule` | Schedule campaign sends | `POST /v1/campaigns/{id}/schedule` |
| `analytics:read` | Access all analytics endpoints | `GET /v1/analytics/**` |
| `webhooks:read` | View webhook registrations | `GET /v1/webhooks/**` |
| `webhooks:write` | Register and update webhooks | `POST /v1/webhooks`, `PUT /v1/webhooks/{id}`, `POST /v1/webhooks/{id}/test` |
| `webhooks:delete` | Remove webhooks | `DELETE /v1/webhooks/{id}` |
| `api-keys:read` | List API keys (prefixes only) | `GET /v1/api-keys` |
| `api-keys:write` | Create API keys | `POST /v1/api-keys` |
| `api-keys:delete` | Revoke API keys | `DELETE /v1/api-keys/{id}` |
| `admin` | Full access to all scopes | All endpoints |

---

## 19. Webhook Payload Contract

All outbound webhook events share a common envelope.

### 19.1 Event Envelope

```json
{
  "event_id": "evt_01HXYZ_EVT_DELIVER",
  "event_type": "message.delivered",
  "api_version": "v1",
  "tenant_id": "ten_01HXYZ_ACME",
  "timestamp": "2025-07-14T10:30:04.800Z",
  "data": { }
}
```

### 19.2 `message.delivered`

```json
{
  "event_id": "evt_01HXYZ_DELIVERED",
  "event_type": "message.delivered",
  "api_version": "v1",
  "tenant_id": "ten_01HXYZ_ACME",
  "timestamp": "2025-07-14T10:30:04.800Z",
  "data": {
    "message_id": "msg_01HXYZ_SEND_A1B2C3",
    "channel": "email",
    "recipient_email": "jane.doe@example.com",
    "provider": "sendgrid",
    "provider_message_id": "SG.abc123xyz456",
    "delivered_at": "2025-07-14T10:30:04.800Z"
  }
}
```

### 19.3 `message.failed`

```json
{
  "event_id": "evt_01HXYZ_FAILED",
  "event_type": "message.failed",
  "api_version": "v1",
  "tenant_id": "ten_01HXYZ_ACME",
  "timestamp": "2025-07-14T10:35:00.000Z",
  "data": {
    "message_id": "msg_01HXYZ_SEND_FAIL1",
    "channel": "sms",
    "recipient_phone": "+14155550001",
    "provider": "twilio",
    "failure_reason": "INVALID_DESTINATION",
    "failure_code": "21211",
    "attempts": 3,
    "failed_at": "2025-07-14T10:35:00.000Z"
  }
}
```

### 19.4 `message.bounced`

```json
{
  "event_id": "evt_01HXYZ_BOUNCED",
  "event_type": "message.bounced",
  "api_version": "v1",
  "tenant_id": "ten_01HXYZ_ACME",
  "timestamp": "2025-07-14T10:31:00.000Z",
  "data": {
    "message_id": "msg_01HXYZ_SEND_BOUNCE",
    "channel": "email",
    "recipient_email": "invalid@noexist.example.com",
    "bounce_type": "HARD",
    "bounce_code": "550",
    "bounce_message": "5.1.1 User unknown",
    "provider": "sendgrid",
    "bounced_at": "2025-07-14T10:31:00.000Z"
  }
}
```

### 19.5 `message.opened`

```json
{
  "event_id": "evt_01HXYZ_OPENED",
  "event_type": "message.opened",
  "api_version": "v1",
  "tenant_id": "ten_01HXYZ_ACME",
  "timestamp": "2025-07-14T11:00:00.000Z",
  "data": {
    "message_id": "msg_01HXYZ_SEND_A1B2C3",
    "channel": "email",
    "recipient_email": "jane.doe@example.com",
    "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 ...)",
    "ip_address": "203.0.113.10",
    "opened_at": "2025-07-14T11:00:00.000Z",
    "open_count": 1
  }
}
```

### 19.6 `message.clicked`

```json
{
  "event_id": "evt_01HXYZ_CLICKED",
  "event_type": "message.clicked",
  "api_version": "v1",
  "tenant_id": "ten_01HXYZ_ACME",
  "timestamp": "2025-07-14T11:01:30.000Z",
  "data": {
    "message_id": "msg_01HXYZ_SEND_A1B2C3",
    "channel": "email",
    "recipient_email": "jane.doe@example.com",
    "link_url": "https://track.example.com/ORD-9987",
    "link_alias": "track-order",
    "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 ...)",
    "ip_address": "203.0.113.10",
    "clicked_at": "2025-07-14T11:01:30.000Z",
    "click_count": 1
  }
}
```

### 19.7 `contact.unsubscribed`

```json
{
  "event_id": "evt_01HXYZ_UNSUB",
  "event_type": "contact.unsubscribed",
  "api_version": "v1",
  "tenant_id": "ten_01HXYZ_ACME",
  "timestamp": "2025-07-14T11:05:00.000Z",
  "data": {
    "contact_id": "con_01HXYZ_USER_JANE",
    "email": "jane.doe@example.com",
    "channel": "email",
    "scope": "ALL",
    "source": "UNSUBSCRIBE_LINK",
    "triggering_message_id": "msg_01HXYZ_SEND_A1B2C3",
    "unsubscribed_at": "2025-07-14T11:05:00.000Z"
  }
}
```

### 19.8 `campaign.completed`

```json
{
  "event_id": "evt_01HXYZ_CMP_DONE",
  "event_type": "campaign.completed",
  "api_version": "v1",
  "tenant_id": "ten_01HXYZ_ACME",
  "timestamp": "2025-07-20T14:35:00.000Z",
  "data": {
    "campaign_id": "cmp_01HXYZ_SUMMER_2025",
    "name": "Summer Sale 2025",
    "channel": "email",
    "total_sent": 14823,
    "total_delivered": 14201,
    "total_failed": 622,
    "completed_at": "2025-07-20T14:35:00.000Z"
  }
}
```

## Scope
- Multi-tenant, multi-channel notifications (email, SMS, push, webhook).
- Transactional, operational, and campaign traffic profiles.
- End-to-end controls from API ingestion to provider callbacks and compliance evidence.

## Design Deep Dive
- Outbox pattern is mandatory for publish consistency with DB transactions.
- Worker lease model prevents concurrent duplicate dispatch.
- Callback signature verification and replay protection are required.
- Template renderer must support strict and permissive modes by message tier.

## Delivery, Reliability, and Compliance Baseline

### 1) Delivery semantics
- **Default guarantee:** At-least-once delivery for all async sends. Exactly-once is not assumed; business safety is achieved via idempotency.
- **Idempotency contract:** `idempotency_key = tenant_id + message_type + recipient + template_version + request_nonce`.
- **Latency tiers:**
  - `P0 Transactional` (OTP, password reset): enqueue < 1s, provider handoff p95 < 5s.
  - `P1 Operational` (alerts, statements): enqueue < 5s, handoff p95 < 30s.
  - `P2 Promotional` (campaign): enqueue < 30s, handoff p95 < 5m.
- **Status model:** `ACCEPTED -> QUEUED -> DISPATCHING -> PROVIDER_ACCEPTED -> DELIVERED|FAILED|EXPIRED`.

### 2) Queue and topic behavior
- **Topic split:** `notifications.transactional`, `notifications.operational`, `notifications.promotional`, plus channel suffixes.
- **Partition key:** `tenant_id:recipient_id:channel` to preserve recipient-level ordering without global lock contention.
- **Backpressure policy:** API returns `202 Accepted` once persisted; throttling starts at queue depth thresholds and adaptive worker concurrency.
- **Poison message isolation:** messages with schema/validation failures bypass retries and go directly to DLQ.

### 3) Retry and dead-letter handling
- **Retry policy:** capped exponential backoff with jitter (e.g., 30s, 2m, 10m, 30m, 2h max).
- **Retryable causes:** transport timeout, 429, 5xx, transient DNS/network faults.
- **Non-retryable causes:** invalid recipient, permanent provider policy reject, malformed template payload.
- **DLQ payload:** original envelope, error class/code, attempt history, provider response excerpt, trace IDs.
- **Redrive controls:** replay by batch, by tenant, by error class; replay requires approval in production.

### 4) Provider routing and failover
- **Routing mode:** weighted primary/secondary by channel and geography.
- **Health model:** active probes + rolling error-rate window + circuit breaker half-open testing.
- **Failover rule:** open circuit on sustained 5xx or timeout rates; route to standby while preserving idempotency keys.
- **Recovery:** gradual traffic ramp-back (10% -> 25% -> 50% -> 100%) with rollback guards.

### 5) Template management
- **Lifecycle:** `DRAFT -> REVIEW -> APPROVED -> PUBLISHED -> DEPRECATED -> RETIRED`.
- **Versioning:** immutable published versions; sends always pin explicit version.
- **Schema checks:** required variables, type validation, locale fallback chain, safe HTML sanitization.
- **Change control:** dual approval for regulated templates; rollback < 5 minutes.

### 6) Compliance and audit logging
- **Audit events:** consent evaluation, suppression decisions, template render inputs/outputs hash, provider requests/responses, operator actions.
- **PII policy:** log tokenized recipient identifiers; redact message body unless explicit legal-hold context.
- **Retention:** operational logs 90 days hot, 1 year warm; compliance evidence 7 years (policy configurable).
- **Forensics query keys:** `tenant_id`, `message_id`, `correlation_id`, `provider_message_id`, `recipient_token`, time range.

## Verification Checklist
- [ ] All interfaces include idempotency + correlation identifiers.
- [ ] Retryable vs non-retryable errors are explicitly classified.
- [ ] DLQ replay process is documented with approvals and guardrails.
- [ ] Provider failover policy defines trigger, action, and recovery criteria.
- [ ] Template versioning and approval workflow are enforceable in tooling.
- [ ] Compliance evidence can be queried by message_id and correlation_id.
