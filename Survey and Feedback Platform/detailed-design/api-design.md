# API Design — Survey and Feedback Platform

## Overview

The Survey and Feedback Platform exposes a versioned REST API. All endpoints are served under
the base path `/api/v1/`. The API follows REST conventions: resource-oriented URLs, standard
HTTP verbs, and JSON request/response bodies. Breaking changes are introduced only in new
versions (`/api/v2/`); non-breaking changes (new fields, new optional parameters) are added
in-place.

**Base URL:** `https://api.surveyplatform.io/api/v1`

**Content-Type:** All requests and responses use `application/json` unless noted.

**Transport:** TLS 1.2+ required. HTTP requests are redirected to HTTPS via Route 53 + CloudFront.

**API Documentation:** Interactive OpenAPI docs available at `/api/v1/docs` (Swagger UI) and
`/api/v1/redoc` (ReDoc). The OpenAPI 3.1 schema is served at `/api/v1/openapi.json`.

---

## Authentication

### JWT Bearer Token

Most API endpoints require a `Bearer` token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

Access tokens expire after **15 minutes**. Use `POST /api/v1/auth/refresh` with the
`refresh_token` (7-day TTL, stored in `HttpOnly` cookie) to obtain a new access token.

### API Key Authentication

Machine-to-machine integrations use API keys passed in the `X-API-Key` header:

```
X-API-Key: sfp_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

API keys are scoped to a workspace and optionally restricted to specific IP CIDR ranges. Keys
are managed in Settings → Developer → API Keys. API key requests bypass session checks but are
subject to rate limiting per workspace tier.

### OAuth 2.0 Endpoints

| Flow | Endpoint | Description |
|---|---|---|
| Initiate Google OAuth | `GET /api/v1/auth/oauth/google` | Redirects to Google consent screen |
| Initiate Microsoft OAuth | `GET /api/v1/auth/oauth/microsoft` | Redirects to Microsoft consent screen |
| OAuth callback | `GET /api/v1/auth/oauth/callback` | Handles provider redirect; issues JWT tokens |

---

## Standard Response Format

All API responses use a consistent JSON envelope:

```json
{
  "data": { },
  "meta": {
    "request_id": "req_01HX4N9K2P...",
    "timestamp": "2025-01-15T10:30:00Z",
    "version": "v1"
  },
  "errors": null
}
```

For paginated list responses, `meta` also includes:

```json
"meta": {
  "pagination": {
    "total": 142,
    "page": 1,
    "per_page": 20,
    "cursor_next": "eyJpZCI6ICIxMjMifQ==",
    "has_more": true
  }
}
```

Error responses use the same envelope with `data: null` and a populated `errors` array:

```json
{
  "data": null,
  "meta": { "request_id": "req_01HX4N9K2P...", "timestamp": "2025-01-15T10:30:00Z" },
  "errors": [
    {
      "code": "VALIDATION_ERROR",
      "message": "question_type must be one of: text, rating, multiple_choice, ...",
      "field": "questions[0].question_type",
      "docs_url": "https://docs.surveyplatform.io/errors/VALIDATION_ERROR"
    }
  ]
}
```

---

## Error Code Reference

| HTTP Status | Error Code | Description |
|---|---|---|
| `400` | `VALIDATION_ERROR` | Request body or query parameter failed Pydantic validation |
| `400` | `INVALID_QUESTION_TYPE` | Unrecognized `question_type` value |
| `400` | `INVALID_LOGIC_RULE` | Conditional branch rule references a non-existent question ID |
| `400` | `DUPLICATE_EMAIL` | Email address already registered in this workspace |
| `401` | `UNAUTHENTICATED` | Missing or invalid `Authorization` header |
| `401` | `TOKEN_EXPIRED` | JWT access token has expired; refresh required |
| `401` | `MAGIC_LINK_EXPIRED` | Magic link token expired or already used |
| `402` | `SUBSCRIPTION_REQUIRED` | Feature requires an active paid subscription |
| `402` | `PAYMENT_FAILED` | Workspace subscription is past due or suspended |
| `403` | `FORBIDDEN` | Authenticated user lacks permission for this resource |
| `403` | `WORKSPACE_LIMIT_REACHED` | Free tier survey or response count limit exceeded |
| `404` | `SURVEY_NOT_FOUND` | Survey with given `survey_id` does not exist |
| `404` | `SESSION_NOT_FOUND` | Response session with given `session_id` not found |
| `404` | `QUESTION_NOT_FOUND` | Question with given `question_id` not found in survey |
| `409` | `CONFLICT` | Optimistic lock version mismatch; re-fetch and retry |
| `409` | `SURVEY_ALREADY_PUBLISHED` | Survey is already in ACTIVE state |
| `410` | `SURVEY_CLOSED` | Survey is CLOSED or ARCHIVED; no longer accepting responses |
| `422` | `INVALID_STATE_TRANSITION` | Attempted lifecycle event is not valid from current state |
| `422` | `MISSING_REQUIRED_ANSWERS` | Submit attempted with unanswered required questions |
| `429` | `RATE_LIMIT_EXCEEDED` | Request rate limit for the workspace tier exceeded |
| `500` | `INTERNAL_ERROR` | Unexpected server error; `request_id` provided for support |
| `503` | `SERVICE_UNAVAILABLE` | Downstream dependency (database, cache) temporarily unavailable |

---

## Pagination

### Cursor-Based Pagination (default for most list endpoints)

Use cursor-based pagination for large or frequently-updated collections:

| Parameter | Type | Description |
|---|---|---|
| `cursor` | string | Opaque base64-encoded cursor from previous response `meta.pagination.cursor_next` |
| `limit` | integer | Number of records per page (default: `20`, max: `100`) |

### Offset-Based Pagination (for export/analytics endpoints)

| Parameter | Type | Description |
|---|---|---|
| `page` | integer | 1-indexed page number (default: `1`) |
| `per_page` | integer | Records per page (default: `20`, max: `100`) |

---

## Rate Limiting

Rate limits are enforced per workspace and per API key using a sliding-window algorithm in Redis.
Limit headers are returned on every response:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 847
X-RateLimit-Reset: 1705316400
```

| Plan | Requests / Minute | Burst | Response Collection | Campaign Send |
|---|---|---|---|---|
| Free | 100 | 150 | 500 responses / month | Not available |
| Starter | 300 | 450 | 5,000 responses / month | 1,000 emails / month |
| Business | 1,000 | 1,500 | 50,000 responses / month | 50,000 emails / month |
| Enterprise | 10,000 | 15,000 | Unlimited | Unlimited |

---

## API Endpoints by Domain

### Survey Management API

| Method | Path | Description | Auth |
|---|---|---|---|
| `POST` | `/surveys` | Create a new survey in DRAFT state | JWT / API Key |
| `GET` | `/surveys` | List all surveys in workspace (paginated, filterable by status) | JWT / API Key |
| `GET` | `/surveys/{survey_id}` | Get full survey object including questions and logic rules | JWT / API Key |
| `PUT` | `/surveys/{survey_id}` | Update survey metadata (title, description, settings) | JWT / API Key |
| `DELETE` | `/surveys/{survey_id}` | Soft-delete a survey in DRAFT state only | JWT / API Key |
| `POST` | `/surveys/{survey_id}/publish` | Transition survey from DRAFT to ACTIVE | JWT |
| `POST` | `/surveys/{survey_id}/duplicate` | Create a new DRAFT survey copied from this one | JWT |
| `GET` | `/surveys/{survey_id}/questions` | List all questions for a survey (ordered) | JWT / API Key |
| `POST` | `/surveys/{survey_id}/questions` | Add a new question to a DRAFT survey | JWT |
| `PUT` | `/surveys/{survey_id}/questions/{question_id}` | Update a question (DRAFT only) | JWT |
| `DELETE` | `/surveys/{survey_id}/questions/{question_id}` | Remove a question (DRAFT only) | JWT |
| `POST` | `/surveys/{survey_id}/questions/reorder` | Bulk reorder questions by providing ordered ID array | JWT |
| `POST` | `/surveys/{survey_id}/logic-rules` | Create or replace conditional logic rules for survey | JWT |

**Query parameters for `GET /surveys`:**
- `status` — filter by state: `draft`, `active`, `paused`, `closed`, `archived`
- `search` — full-text search on survey title
- `cursor`, `limit` — pagination

---

### Response Collection API

| Method | Path | Description | Auth |
|---|---|---|---|
| `POST` | `/responses/start` | Start a new response session; returns `session_id` and `session_token` | None (public) |
| `POST` | `/responses/{session_id}/answers` | Save one or more answers; supports partial save | `session_token` |
| `POST` | `/responses/{session_id}/complete` | Finalize and submit response session | `session_token` |
| `GET` | `/surveys/{survey_id}/responses` | List completed responses for a survey (paginated) | JWT / API Key |
| `GET` | `/responses/{session_id}` | Get a single response session (admin view with all answers) | JWT / API Key |

**`POST /responses/start` request body:**
- `survey_id` (required): UUID of the target survey
- `respondent_metadata` (optional): anonymous metadata (browser, device) for analytics
- `prefill` (optional): map of `question_id → answer` for pre-filled parameters from URL

---

### Analytics API

| Method | Path | Description | Auth |
|---|---|---|---|
| `GET` | `/surveys/{survey_id}/analytics/summary` | Overall response count, completion rate, avg time, NPS, CSAT | JWT / API Key |
| `GET` | `/surveys/{survey_id}/analytics/nps` | Full NPS breakdown: score, promoters %, passives %, detractors % | JWT / API Key |
| `GET` | `/surveys/{survey_id}/analytics/trend` | Response volume over time (daily/weekly buckets) | JWT / API Key |
| `GET` | `/surveys/{survey_id}/analytics/crosstab` | Cross-tabulation: segment by `row_question_id` and `col_question_id` | JWT / API Key |
| `WebSocket` | `/surveys/{survey_id}/analytics/live` | Real-time response count stream (JSON frames on each new response) | JWT |

**Query parameters for analytics endpoints:**
- `from_date` / `to_date` — ISO 8601 date range filter
- `question_id` — scope analytics to a single question (NPS, CSAT endpoints)
- `segment_by` — `device`, `location`, `referrer` (summary endpoint)

---

### Distribution API

| Method | Path | Description | Auth |
|---|---|---|---|
| `POST` | `/campaigns` | Create a new email or SMS campaign in DRAFT state | JWT |
| `GET` | `/campaigns` | List all campaigns in workspace (paginated) | JWT |
| `GET` | `/campaigns/{campaign_id}` | Get campaign details including delivery stats | JWT |
| `PUT` | `/campaigns/{campaign_id}` | Update DRAFT campaign (audience, template, subject) | JWT |
| `POST` | `/campaigns/{campaign_id}/send` | Send campaign immediately (transitions DRAFT → SENDING) | JWT |
| `POST` | `/campaigns/{campaign_id}/schedule` | Schedule campaign for future delivery | JWT |
| `POST` | `/campaigns/{campaign_id}/pause` | Pause an in-progress campaign | JWT |
| `POST` | `/campaigns/{campaign_id}/cancel` | Cancel a DRAFT or SCHEDULED campaign | JWT |

---

### Audience API

| Method | Path | Description | Auth |
|---|---|---|---|
| `POST` | `/audiences` | Create a new audience (named contact list) | JWT |
| `GET` | `/audiences` | List all audiences in workspace | JWT |
| `GET` | `/audiences/{audience_id}` | Get audience details and contact count | JWT |
| `POST` | `/audiences/{audience_id}/contacts/import` | Import contacts from CSV (file uploaded to S3 pre-signed URL) | JWT |
| `GET` | `/audiences/{audience_id}/contacts` | List contacts in audience (paginated) | JWT |
| `DELETE` | `/audiences/{audience_id}` | Delete an audience (contacts are retained) | JWT |
| `DELETE` | `/contacts/{contact_id}/unsubscribe` | Mark contact as globally unsubscribed | None (via signed URL) |

**CSV import flow:**
1. `POST /audiences/{id}/contacts/import` returns a pre-signed S3 upload URL.
2. Client uploads CSV directly to S3 using the pre-signed URL.
3. S3 event triggers Lambda, which validates and imports rows asynchronously.
4. Import job status is polled via `GET /audiences/{id}/import-jobs/{job_id}`.

---

### Webhook API

| Method | Path | Description | Auth |
|---|---|---|---|
| `POST` | `/webhooks` | Register a new webhook endpoint with event subscriptions | JWT |
| `GET` | `/webhooks` | List all webhook endpoints for workspace | JWT |
| `GET` | `/webhooks/{webhook_id}` | Get webhook details including delivery statistics | JWT |
| `PUT` | `/webhooks/{webhook_id}` | Update webhook URL, secret, or event subscriptions | JWT |
| `DELETE` | `/webhooks/{webhook_id}` | Delete webhook endpoint | JWT |
| `POST` | `/webhooks/{webhook_id}/test` | Send a test delivery with a sample payload | JWT |
| `GET` | `/webhooks/{webhook_id}/deliveries` | List recent delivery attempts with status and response | JWT |

---

### Auth API

| Method | Path | Description | Auth |
|---|---|---|---|
| `POST` | `/auth/register` | Create new user account and workspace | None |
| `POST` | `/auth/login` | Authenticate with email + password; returns JWT pair | None |
| `POST` | `/auth/magic-link` | Request a magic link sent to email address | None |
| `POST` | `/auth/magic-link/verify` | Exchange magic link token for JWT tokens | None |
| `POST` | `/auth/refresh` | Refresh access token using `refresh_token` cookie | Refresh token |
| `POST` | `/auth/logout` | Revoke refresh token and clear session | JWT |
| `GET` | `/auth/oauth/google` | Initiate Google OAuth 2.0 flow | None |
| `GET` | `/auth/oauth/microsoft` | Initiate Microsoft OAuth 2.0 flow | None |
| `GET` | `/auth/me` | Get current authenticated user and workspace info | JWT |

---

## Request / Response Examples

### 1. Create Survey — `POST /api/v1/surveys`

**Request:**
```json
{
  "title": "Customer Satisfaction Q4 2025",
  "description": "Post-purchase satisfaction survey",
  "settings": {
    "allow_multiple_responses": false,
    "show_progress_bar": true,
    "response_limit": 1000,
    "end_date": "2025-12-31T23:59:59Z",
    "redirect_url": "https://example.com/thanks"
  }
}
```

**Response `201 Created`:**
```json
{
  "data": {
    "id": "srv_01HX4N9K2PMQAB3CDEF",
    "title": "Customer Satisfaction Q4 2025",
    "state": "DRAFT",
    "workspace_id": "ws_01HX001XYZ",
    "question_count": 0,
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T10:30:00Z",
    "settings": {
      "allow_multiple_responses": false,
      "show_progress_bar": true,
      "response_limit": 1000,
      "end_date": "2025-12-31T23:59:59Z"
    },
    "share_url": "https://survey.io/s/srv_01HX4N9K2PMQAB3CDEF"
  },
  "meta": { "request_id": "req_01HX4N...", "timestamp": "2025-01-15T10:30:00Z", "version": "v1" },
  "errors": null
}
```

### 2. Add Question — `POST /api/v1/surveys/{survey_id}/questions`

**Request:**
```json
{
  "question_type": "rating",
  "title": "How likely are you to recommend us to a friend?",
  "required": true,
  "position": 1,
  "config": {
    "scale": "nps",
    "min_label": "Not at all likely",
    "max_label": "Extremely likely"
  }
}
```

**Response `201 Created`:**
```json
{
  "data": {
    "id": "qst_01HX4N9K2PMQAB3",
    "survey_id": "srv_01HX4N9K2PMQAB3CDEF",
    "question_type": "rating",
    "title": "How likely are you to recommend us to a friend?",
    "required": true,
    "position": 1,
    "config": { "scale": "nps", "min_label": "Not at all likely", "max_label": "Extremely likely" }
  },
  "meta": { "request_id": "req_01HX4N...", "timestamp": "2025-01-15T10:31:00Z", "version": "v1" },
  "errors": null
}
```

### 3. Start Response Session — `POST /api/v1/responses/start`

**Request:**
```json
{
  "survey_id": "srv_01HX4N9K2PMQAB3CDEF",
  "respondent_metadata": {
    "device": "desktop",
    "browser": "Chrome 120",
    "referrer": "email_campaign"
  }
}
```

**Response `201 Created`:**
```json
{
  "data": {
    "session_id": "ses_01HX4N9K3FGHABC",
    "session_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "survey": {
      "id": "srv_01HX4N9K2PMQAB3CDEF",
      "title": "Customer Satisfaction Q4 2025",
      "question_count": 5,
      "settings": { "show_progress_bar": true }
    },
    "expires_at": "2025-01-15T11:00:00Z"
  },
  "meta": { "request_id": "req_01HX4N...", "timestamp": "2025-01-15T10:35:00Z", "version": "v1" },
  "errors": null
}
```

### 4. Get Analytics Summary — `GET /api/v1/surveys/{survey_id}/analytics/summary`

**Response `200 OK`:**
```json
{
  "data": {
    "survey_id": "srv_01HX4N9K2PMQAB3CDEF",
    "total_responses": 842,
    "completion_rate": 0.78,
    "avg_completion_time_seconds": 187,
    "nps_score": 42,
    "csat_score": 4.1,
    "response_trend": "increasing",
    "last_response_at": "2025-01-15T10:28:00Z",
    "date_range": { "from": "2025-01-01T00:00:00Z", "to": "2025-01-15T23:59:59Z" }
  },
  "meta": { "request_id": "req_01HX4N...", "timestamp": "2025-01-15T10:40:00Z", "version": "v1" },
  "errors": null
}
```

### 5. Register Webhook — `POST /api/v1/webhooks`

**Request:**
```json
{
  "url": "https://myapp.example.com/hooks/survey",
  "events": ["response.completed", "survey.closed", "campaign.sent"],
  "description": "Production integration webhook"
}
```

**Response `201 Created`:**
```json
{
  "data": {
    "id": "wh_01HX4N9K4MNOPQR",
    "url": "https://myapp.example.com/hooks/survey",
    "events": ["response.completed", "survey.closed", "campaign.sent"],
    "secret": "whsec_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "is_active": true,
    "created_at": "2025-01-15T10:45:00Z"
  },
  "meta": { "request_id": "req_01HX4N...", "timestamp": "2025-01-15T10:45:00Z", "version": "v1" },
  "errors": null
}
```

---

## Webhook Payload Format

All webhook deliveries POST a signed JSON payload to the registered URL:

```http
POST https://myapp.example.com/hooks/survey
Content-Type: application/json
X-Webhook-ID: wh_01HX4N9K4MNOPQR
X-Webhook-Event: response.completed
X-Webhook-Signature: sha256=<hmac_hex>
X-Webhook-Timestamp: 1705316400
X-Webhook-Delivery-ID: del_01HX4N9K5STUVWX
```

```json
{
  "event_id": "evt_01HX4N9K5STUVWX",
  "event_type": "response.completed",
  "created_at": "2025-01-15T10:28:00Z",
  "workspace_id": "ws_01HX001XYZ",
  "data": {
    "session_id": "ses_01HX4N9K3FGHABC",
    "survey_id": "srv_01HX4N9K2PMQAB3CDEF",
    "completed_at": "2025-01-15T10:28:00Z",
    "duration_seconds": 193,
    "answers": [
      { "question_id": "qst_01HX4N9K2PMQAB3", "question_type": "rating", "value": 9 }
    ]
  }
}
```

**Signature verification** (Python example):
```python
import hmac, hashlib
expected = hmac.new(secret.encode(), msg=payload_bytes, digestmod=hashlib.sha256).hexdigest()
assert hmac.compare_digest(f"sha256={expected}", request.headers["X-Webhook-Signature"])
```

Reject deliveries where the `X-Webhook-Timestamp` is more than **5 minutes** in the past to
prevent replay attacks.

---

## Versioning and Deprecation Policy

### API Versioning Strategy

The API uses URL path versioning: `/api/v1/`, `/api/v2/`, etc. A new major version is only
introduced when a breaking change is required. Breaking changes include: removing a field,
changing a field type, renaming a resource URL, or changing authentication mechanisms.

Non-breaking additions (new optional request fields, new response fields, new endpoints) are
deployed to the current version without a version bump. Clients must be written to ignore
unknown fields in responses.

### Deprecation Timeline

1. A deprecated endpoint or field is marked with `X-Deprecated: true` and
   `X-Sunset-Date: <ISO 8601 date>` response headers.
2. Deprecation is announced in the developer changelog with a minimum **6-month** sunset window.
3. On the sunset date, the endpoint returns `HTTP 410 Gone` with error code `ENDPOINT_DEPRECATED`.
4. The previous API version (`/api/vN-1/`) remains active for **12 months** after the release of
   `/api/vN/` to allow migration time.

### Client Compatibility

Clients should always send the `Accept: application/json` header and handle unknown JSON fields
gracefully. The `meta.version` field in every response identifies the API version that served
the request. Monitoring `X-Deprecated` headers in responses allows teams to proactively detect
endpoints nearing sunset before they break.

---

## Operational Policy Addendum

### OPA-1: Idempotency for Write Operations

`POST` endpoints that create resources accept an optional `Idempotency-Key` header (UUID v4).
If a request with the same key is received within **24 hours**, the original response is returned
without re-executing the operation. This prevents duplicate survey creation or double-charge
scenarios caused by network retries. Idempotency keys are stored in Redis with a 24-hour TTL.

### OPA-2: Request Tracing

Every API request is assigned a unique `request_id` (format: `req_<ULID>`) generated at the
API Gateway layer. This ID is returned in the `meta.request_id` response field and propagated
as the `X-Request-ID` header to all downstream service calls and database queries. All log lines
for a single request carry this ID, enabling end-to-end distributed trace reconstruction in
AWS CloudWatch Logs Insights.

### OPA-3: GDPR and Data Residency

API responses for workspaces configured with EU data residency never include raw respondent PII
(email, IP address, name) in response payloads unless the caller has the `data:pii:read`
permission scope. Survey response export endpoints for EU workspaces apply the `GDPRFilter`
component to strip or pseudonymize PII fields. Respondents may exercise the right to erasure
via `DELETE /api/v1/responses/{session_id}`, which permanently deletes the response and all
associated answer data within 30 days.

### OPA-4: API Gateway WAF Rules

All traffic passes through AWS WAF before reaching the API Gateway. Active rules include: SQL
injection protection, XSS filtering, rate-based rules (block IPs exceeding 500 req/5 min),
geo-blocking (configurable per workspace), and bot detection for the public response collection
endpoints. The WAF logs are retained in S3 for 90 days and analyzed daily for threat patterns.
