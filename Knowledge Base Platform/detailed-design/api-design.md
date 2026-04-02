# API Design — Knowledge Base Platform

## 1. Design Principles

| Principle | Detail |
|-----------|--------|
| **Style** | REST with resource-oriented URLs; JSON request/response bodies |
| **Versioning** | URI versioning: `/api/v1/`; breaking changes increment the version |
| **Authentication** | Bearer JWT (`Authorization: Bearer <access_token>`); access token TTL = 15 min; refresh token TTL = 30 days |
| **Widget Auth** | `X-Widget-Key: <api_key>` for widget-origin requests; no JWT required |
| **HTTPS** | All traffic over TLS 1.2+; HTTP → HTTPS redirect enforced at ALB |
| **Rate Limiting** | Sliding window per user/IP; limits in `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` response headers |
| **Pagination** | Cursor-based; `cursor` + `limit` query params; response includes `nextCursor` |
| **Idempotency** | `POST` endpoints that create resources accept optional `Idempotency-Key` header (UUID) |
| **Content-Type** | `application/json` for all endpoints; `multipart/form-data` for file upload |
| **CORS** | Allowed origins configurable per workspace; Widget endpoints use `Access-Control-Allow-Origin: *` |
| **Error Format** | RFC 7807 Problem Details (`application/problem+json`) |
| **Tracing** | `X-Request-ID` header echoed in response; used for distributed tracing in CloudWatch |

---

## 2. OpenAPI 3.1 Info Block

```yaml
openapi: "3.1.0"
info:
  title: Knowledge Base Platform API
  version: "1.0.0"
  description: >
    RESTful API for the Knowledge Base Platform. Provides article management,
    semantic search, AI-powered Q&A, widget configuration, analytics, and
    third-party integrations.
  contact:
    name: Platform Team
    email: api-support@kbplatform.io
  license:
    name: Proprietary
servers:
  - url: https://api.kbplatform.io/api/v1
    description: Production
  - url: https://api.staging.kbplatform.io/api/v1
    description: Staging
  - url: http://localhost:3001/api/v1
    description: Local development
components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
    WidgetApiKey:
      type: apiKey
      in: header
      name: X-Widget-Key
security:
  - BearerAuth: []
tags:
  - name: Auth
  - name: Articles
  - name: Collections
  - name: Search
  - name: AI
  - name: Users
  - name: Workspaces
  - name: Widgets
  - name: Analytics
  - name: Webhooks
```

---

## 3. Error Response Format (RFC 7807)

```json
{
  "type": "https://api.kbplatform.io/errors/validation-failed",
  "title": "Validation Failed",
  "status": 422,
  "detail": "The 'title' field is required and may not be blank.",
  "instance": "/api/v1/articles",
  "requestId": "req_01HY8F4QVZE9WXDP3NKRTM",
  "errors": [
    { "field": "title", "code": "required", "message": "Title is required" },
    { "field": "collectionId", "code": "invalid_uuid", "message": "Must be a valid UUID" }
  ]
}
```

**Standard HTTP Status Codes Used:**

| Code | Meaning |
|------|---------|
| 200 | OK — successful GET, PATCH |
| 201 | Created — successful POST that creates a resource |
| 204 | No Content — successful DELETE |
| 400 | Bad Request — malformed JSON |
| 401 | Unauthorized — missing or invalid JWT |
| 403 | Forbidden — authenticated but lacking permission |
| 404 | Not Found — resource does not exist |
| 409 | Conflict — duplicate slug, optimistic lock mismatch |
| 422 | Unprocessable Entity — validation errors |
| 429 | Too Many Requests — rate limit exceeded |
| 500 | Internal Server Error — unexpected server error |
| 503 | Service Unavailable — dependency down (OpenAI, ES) |

---

## 4. Pagination Pattern

All list endpoints use **cursor-based pagination**:

**Request:**
```
GET /api/v1/articles?limit=20&cursor=eyJpZCI6Ijk4YWNiZiJ9
```

**Response:**
```json
{
  "data": [ ... ],
  "pagination": {
    "limit": 20,
    "nextCursor": "eyJpZCI6IjhhYmNkZWYifQ==",
    "hasNextPage": true,
    "total": 143
  }
}
```

Cursor is a base64-encoded JSON object `{ "id": "<last_item_id>", "ts": "<last_item_created_at>" }`. Server-side decodes the cursor and applies `WHERE created_at <= :ts AND id < :id ORDER BY created_at DESC, id DESC LIMIT :limit+1`.

---

## 5. Full Endpoint Reference

### 5.1 Auth — `/auth`

| Method | Path | Auth | Rate Limit | Description |
|--------|------|------|------------|-------------|
| POST | `/auth/login` | None | 10/min | Authenticate with email + password |
| POST | `/auth/logout` | JWT | 30/min | Revoke refresh token |
| POST | `/auth/refresh` | None (refresh token in body) | 20/min | Issue new access token |
| POST | `/auth/sso/saml` | None | 10/min | SAML 2.0 SSO callback |
| POST | `/auth/verify-email` | None | 5/min | Confirm email with token |
| POST | `/auth/resend-verification` | None | 3/min | Resend verification email |

**POST /auth/login — Request:**
```json
{ "email": "alice@example.com", "password": "S3cure!Pass" }
```
**POST /auth/login — Response 200:**
```json
{
  "accessToken": "eyJhbGciOiJSUzI1NiJ9...",
  "refreshToken": "rt_01HY8F...",
  "expiresIn": 900,
  "user": { "id": "uuid", "email": "alice@example.com", "name": "Alice" }
}
```

---

### 5.2 Articles — `/articles`

| Method | Path | Auth | Roles | Rate Limit | Description |
|--------|------|------|-------|------------|-------------|
| GET | `/articles` | JWT | Reader+ | 120/min | List articles (paginated, filterable) |
| POST | `/articles` | JWT | Author+ | 60/min | Create new article (DRAFT) |
| GET | `/articles/:id` | JWT | Reader+ | 120/min | Get single article |
| PATCH | `/articles/:id` | JWT | Author/Editor+ | 60/min | Update article (creates version snapshot) |
| DELETE | `/articles/:id` | JWT | WorkspaceAdmin+ | 30/min | Archive (soft delete) article |
| POST | `/articles/:id/submit-review` | JWT | Author | 30/min | Submit article for editorial review |
| POST | `/articles/:id/publish` | JWT | Editor+ | 30/min | Publish approved article |
| POST | `/articles/:id/unpublish` | JWT | Editor+ | 30/min | Unpublish a published article |
| GET | `/articles/:id/versions` | JWT | Author+ | 60/min | List version history |
| POST | `/articles/:id/versions/:versionId/restore` | JWT | Editor+ | 20/min | Restore to historical version |
| POST | `/articles/:id/attachments` | JWT | Author+ | 20/min | Upload attachment (multipart) |
| DELETE | `/articles/:id/attachments/:attachId` | JWT | Author+ | 20/min | Remove attachment |

**POST /articles — Request Body:**
```json
{
  "title": "Getting Started with Password Reset",
  "collectionId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "excerpt": "Learn how to reset your account password in 3 simple steps.",
  "content": { "type": "doc", "content": [ { "type": "paragraph", "content": [] } ] },
  "tags": ["account", "security"],
  "seoMetadata": { "metaTitle": "Reset Password Guide", "metaDescription": "Step-by-step guide..." }
}
```

**POST /articles — Response 201:**
```json
{
  "id": "9e107d9d-372b-4e26-9f48-f66b0e0f3b74",
  "title": "Getting Started with Password Reset",
  "slug": "getting-started-with-password-reset",
  "status": "draft",
  "collectionId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "authorId": "user-uuid",
  "versionNumber": 1,
  "createdAt": "2024-09-01T10:30:00Z",
  "updatedAt": "2024-09-01T10:30:00Z"
}
```

**PATCH /articles/:id — Request Body (all fields optional):**
```json
{
  "title": "Updated Title",
  "content": { "type": "doc", "content": [] },
  "tags": ["billing"],
  "changeSummary": "Added billing section"
}
```

**POST /articles/:id/publish — Request Body:**
```json
{
  "publishedAt": "2024-09-15T09:00:00Z",
  "notifySubscribers": true
}
```

**GET /articles — Query Parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `workspaceId` | UUID (required) | Scope to workspace |
| `collectionId` | UUID | Filter by collection |
| `status` | string | Filter by status (default: published) |
| `tags` | string[] | Filter by tag slugs (comma-separated) |
| `q` | string | Full-text search within results |
| `isFeatured` | boolean | Filter featured articles |
| `cursor` | string | Pagination cursor |
| `limit` | integer | Page size (default: 20, max: 100) |

---

### 5.3 Collections — `/collections`

| Method | Path | Auth | Roles | Rate Limit | Description |
|--------|------|------|-------|------------|-------------|
| GET | `/collections` | JWT | Reader+ | 120/min | Get collection tree for workspace |
| POST | `/collections` | JWT | Editor+ | 30/min | Create new collection |
| GET | `/collections/:id` | JWT | Reader+ | 120/min | Get single collection |
| PATCH | `/collections/:id` | JWT | Editor+ | 30/min | Update collection |
| DELETE | `/collections/:id` | JWT | WorkspaceAdmin+ | 10/min | Delete collection |
| GET | `/collections/:id/articles` | JWT | Reader+ | 60/min | Paginated articles in collection |
| GET | `/collections/:id/permissions` | JWT | WorkspaceAdmin+ | 30/min | List permission grants |
| POST | `/collections/:id/permissions` | JWT | WorkspaceAdmin+ | 20/min | Grant role access |
| DELETE | `/collections/:id/permissions/:permId` | JWT | WorkspaceAdmin+ | 20/min | Revoke permission grant |
| POST | `/collections/reorder` | JWT | Editor+ | 10/min | Reorder collections (array of IDs) |

---

### 5.4 Search — `/search`

| Method | Path | Auth | Rate Limit | Description |
|--------|------|------|------------|-------------|
| GET | `/search` | JWT or WidgetKey | 60/min | Hybrid/FTS search |
| POST | `/search/semantic` | JWT or WidgetKey | 30/min | Semantic (vector) search |

**GET /search — Query Parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `q` | string (required) | Search query (max 512 chars) |
| `workspaceId` | UUID (required) | Workspace scope |
| `type` | enum: `fts`, `semantic`, `hybrid` | Search mode (default: `hybrid`) |
| `collectionId` | UUID | Restrict to collection |
| `tags` | string | Comma-separated tag slugs |
| `limit` | integer | Result count (default: 10, max: 50) |
| `cursor` | string | Pagination cursor |

**GET /search — Response 200:**
```json
{
  "hits": [
    {
      "articleId": "uuid",
      "title": "Getting Started with Password Reset",
      "slug": "getting-started-with-password-reset",
      "excerpt": "Learn how to reset your account password...",
      "highlight": "Reset your <em>password</em> in 3 steps",
      "score": 0.92,
      "tags": ["account", "security"],
      "collectionName": "Account Management",
      "viewCount": 1234,
      "publishedAt": "2024-08-01T00:00:00Z"
    }
  ],
  "total": 7,
  "queryMs": 142,
  "cacheHit": false,
  "pagination": { "nextCursor": null, "hasNextPage": false }
}
```

**POST /search/semantic — Request Body:**
```json
{
  "q": "how do I cancel my subscription",
  "workspaceId": "uuid",
  "topK": 5,
  "minScore": 0.70
}
```

---

### 5.5 AI — `/ai`

| Method | Path | Auth | Rate Limit | Description |
|--------|------|------|------------|-------------|
| POST | `/ai/conversations` | JWT or WidgetKey | 20/min | Start a new AI conversation |
| GET | `/ai/conversations/:id` | JWT | 60/min | Get conversation with messages |
| POST | `/ai/conversations/:id/messages` | JWT or WidgetKey | 30/min | Send user message, get AI reply |
| DELETE | `/ai/conversations/:id` | JWT | 20/min | End and delete conversation |
| POST | `/ai/query` | JWT or WidgetKey | 30/min | Single-shot Q&A (no history) |

**POST /ai/conversations — Request Body:**
```json
{
  "workspaceId": "uuid",
  "widgetId": "uuid-or-null",
  "sessionId": "sess_01HY8F...",
  "metadata": { "pageUrl": "https://app.example.com/billing" }
}
```

**POST /ai/conversations/:id/messages — Request Body:**
```json
{
  "content": "How do I update my billing information?"
}
```

**POST /ai/conversations/:id/messages — Response 200:**
```json
{
  "id": "msg-uuid",
  "conversationId": "conv-uuid",
  "role": "assistant",
  "content": "To update your billing information, navigate to **Settings → Billing** and click **Edit Payment Method**. [1]",
  "citations": [
    {
      "index": 1,
      "articleId": "art-uuid",
      "title": "Managing Billing Information",
      "slug": "managing-billing-information",
      "snippet": "Navigate to Settings → Billing to manage your payment methods."
    }
  ],
  "tokensUsed": 312,
  "latencyMs": 1843,
  "createdAt": "2024-09-01T10:35:22Z"
}
```

**POST /ai/query — Request Body:**
```json
{
  "query": "What payment methods do you accept?",
  "workspaceId": "uuid",
  "sessionId": "sess_01HY8F..."
}
```

---

### 5.6 Users — `/users`

| Method | Path | Auth | Roles | Rate Limit | Description |
|--------|------|------|-------|------------|-------------|
| GET | `/users/me` | JWT | Any | 60/min | Get current user profile |
| PATCH | `/users/me` | JWT | Any | 30/min | Update profile (name, avatar, preferences) |
| GET | `/users/me/workspaces` | JWT | Any | 30/min | List workspaces for current user |
| DELETE | `/users/me` | JWT | Any | 5/min | Deactivate own account |
| GET | `/users/me/export` | JWT | Any | 2/min | Request personal data export |
| GET | `/users/:id` | JWT | WorkspaceAdmin+ | 30/min | Get user profile (admin) |
| DELETE | `/users/:id` | JWT | SuperAdmin | 5/min | Deactivate user account (admin) |

---

### 5.7 Workspaces — `/workspaces`

| Method | Path | Auth | Roles | Rate Limit | Description |
|--------|------|------|-------|------------|-------------|
| GET | `/workspaces` | JWT | Any | 30/min | List workspaces for current user |
| POST | `/workspaces` | JWT | Any | 5/min | Create new workspace |
| GET | `/workspaces/:id` | JWT | Member | 60/min | Get workspace details |
| PATCH | `/workspaces/:id` | JWT | WorkspaceAdmin+ | 20/min | Update workspace |
| DELETE | `/workspaces/:id` | JWT | SuperAdmin | 2/min | Delete workspace |
| GET | `/workspaces/:id/members` | JWT | Member | 30/min | List workspace members |
| POST | `/workspaces/:id/members` | JWT | WorkspaceAdmin+ | 20/min | Invite member by email |
| PATCH | `/workspaces/:id/members/:userId` | JWT | WorkspaceAdmin+ | 20/min | Update member role |
| DELETE | `/workspaces/:id/members/:userId` | JWT | WorkspaceAdmin+ | 10/min | Remove member |
| GET | `/workspaces/:id/settings` | JWT | WorkspaceAdmin+ | 30/min | Get workspace settings |
| PATCH | `/workspaces/:id/settings` | JWT | WorkspaceAdmin+ | 10/min | Update workspace settings |
| GET | `/workspaces/:id/integrations` | JWT | WorkspaceAdmin+ | 30/min | List integrations |

---

### 5.8 Widgets — `/widgets`

| Method | Path | Auth | Roles | Rate Limit | Description |
|--------|------|------|-------|------------|-------------|
| GET | `/widgets` | JWT | WorkspaceAdmin+ | 30/min | List widgets in workspace |
| POST | `/widgets` | JWT | WorkspaceAdmin+ | 10/min | Create widget |
| GET | `/widgets/:id` | JWT | WorkspaceAdmin+ | 60/min | Get widget config |
| PATCH | `/widgets/:id` | JWT | WorkspaceAdmin+ | 20/min | Update widget config |
| DELETE | `/widgets/:id` | JWT | WorkspaceAdmin+ | 5/min | Delete widget |
| POST | `/widgets/:id/rotate-key` | JWT | WorkspaceAdmin+ | 5/min | Rotate API key |
| GET | `/widgets/:id/suggestions` | WidgetKey | — | 100/min | Get URL-contextual suggestions |
| POST | `/widgets/:id/chat` | WidgetKey | — | 30/min | Start or continue widget AI chat |

**GET /widgets/:id/suggestions — Query Parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `url` | string (required) | Current page URL (URL-encoded) |
| `limit` | integer | Max suggestions (default: 3, max: 5) |

**GET /widgets/:id/suggestions — Response 200:**
```json
{
  "suggestions": [
    {
      "articleId": "uuid",
      "title": "Managing Your Billing Information",
      "slug": "managing-billing-information",
      "snippet": "Update your payment method from Settings → Billing.",
      "url": "https://docs.example.com/billing",
      "score": 0.88
    }
  ],
  "widgetId": "uuid",
  "cacheHit": true
}
```

---

### 5.9 Analytics — `/analytics`

| Method | Path | Auth | Roles | Rate Limit | Description |
|--------|------|------|-------|------------|-------------|
| GET | `/analytics/articles` | JWT | WorkspaceAdmin+ | 30/min | Article engagement stats |
| GET | `/analytics/search` | JWT | WorkspaceAdmin+ | 30/min | Search query analytics |
| GET | `/analytics/deflection` | JWT | WorkspaceAdmin+ | 30/min | Widget deflection rate report |
| GET | `/analytics/top-articles` | JWT | WorkspaceAdmin+ | 30/min | Top articles by views |
| GET | `/analytics/ai` | JWT | WorkspaceAdmin+ | 30/min | AI conversation analytics |
| POST | `/analytics/events` | JWT or WidgetKey | — | 300/min | Track client-side event |

**GET /analytics/articles — Query Parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `workspaceId` | UUID (required) | Workspace scope |
| `from` | ISO 8601 date | Start of date range |
| `to` | ISO 8601 date | End of date range |
| `collectionId` | UUID | Filter by collection |
| `granularity` | enum: `day`,`week`,`month` | Aggregation granularity |

**GET /analytics/deflection — Response 200:**
```json
{
  "workspaceId": "uuid",
  "dateRange": { "from": "2024-08-01", "to": "2024-08-31" },
  "totalWidgetSessions": 4821,
  "deflectedSessions": 3104,
  "deflectionRate": 0.644,
  "escalatedSessions": 712,
  "ticketsCreated": 689,
  "topDeflectedArticles": [
    { "articleId": "uuid", "title": "Password Reset", "deflectionCount": 312 }
  ]
}
```

---

### 5.10 Integrations — `/integrations` & Webhooks

| Method | Path | Auth | Roles | Rate Limit | Description |
|--------|------|------|-------|------------|-------------|
| GET | `/integrations` | JWT | WorkspaceAdmin+ | 30/min | List integrations for workspace |
| POST | `/integrations` | JWT | WorkspaceAdmin+ | 10/min | Create integration |
| GET | `/integrations/:id` | JWT | WorkspaceAdmin+ | 30/min | Get integration details & status |
| POST | `/integrations/:id/connect` | JWT | WorkspaceAdmin+ | 5/min | Connect with OAuth credentials |
| POST | `/integrations/:id/disconnect` | JWT | WorkspaceAdmin+ | 5/min | Disconnect integration |
| POST | `/integrations/:id/sync` | JWT | WorkspaceAdmin+ | 5/min | Trigger manual sync |
| GET | `/integrations/:id/sync-status` | JWT | WorkspaceAdmin+ | 30/min | SSE stream of sync progress |
| POST | `/webhooks/zapier` | HMAC signature | — | 60/min | Zapier webhook receiver |
| POST | `/webhooks/zendesk` | HMAC signature | — | 60/min | Zendesk webhook receiver |

---

## 6. Request/Response Examples — 5 Key Endpoints

### Example 1: Create Article

**Request:**
```http
POST /api/v1/articles HTTP/1.1
Host: api.kbplatform.io
Authorization: Bearer eyJhbGci...
Content-Type: application/json
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000

{
  "title": "How to Export Your Data",
  "collectionId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "excerpt": "Step-by-step guide to exporting all your account data.",
  "content": {
    "type": "doc",
    "content": [
      { "type": "heading", "attrs": { "level": 2 }, "content": [{ "type": "text", "text": "Overview" }] },
      { "type": "paragraph", "content": [{ "type": "text", "text": "You can export your data at any time." }] }
    ]
  },
  "tags": ["data", "privacy", "account"]
}
```

**Response 201:**
```json
{
  "id": "9e107d9d-372b-4e26-9f48-f66b0e0f3b74",
  "workspaceId": "ws-uuid",
  "title": "How to Export Your Data",
  "slug": "how-to-export-your-data",
  "status": "draft",
  "collectionId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "authorId": "user-uuid",
  "versionNumber": 1,
  "tags": [{ "id": "t1", "name": "data", "slug": "data" }],
  "createdAt": "2024-09-01T10:30:00Z",
  "updatedAt": "2024-09-01T10:30:00Z"
}
```

---

### Example 2: Semantic Search

**Request:**
```http
POST /api/v1/search/semantic HTTP/1.1
Host: api.kbplatform.io
Authorization: Bearer eyJhbGci...
Content-Type: application/json

{
  "q": "I forgot my password and cannot log in",
  "workspaceId": "ws-uuid",
  "topK": 5,
  "minScore": 0.70
}
```

**Response 200:**
```json
{
  "hits": [
    {
      "articleId": "art-001",
      "title": "Resetting Your Password",
      "slug": "resetting-your-password",
      "excerpt": "Follow these steps to reset your password via email link.",
      "score": 0.93,
      "similarity": 0.93,
      "collectionName": "Account Help",
      "publishedAt": "2024-07-10T00:00:00Z"
    },
    {
      "articleId": "art-002",
      "title": "Two-Factor Authentication Setup",
      "slug": "two-factor-auth-setup",
      "excerpt": "Enable 2FA to protect your account.",
      "score": 0.78,
      "similarity": 0.78,
      "collectionName": "Security",
      "publishedAt": "2024-06-01T00:00:00Z"
    }
  ],
  "total": 2,
  "queryMs": 210,
  "cacheHit": false,
  "pagination": { "nextCursor": null, "hasNextPage": false }
}
```

---

### Example 3: AI Conversation Message

**Request:**
```http
POST /api/v1/ai/conversations/conv-uuid/messages HTTP/1.1
Host: api.kbplatform.io
X-Widget-Key: wk_live_01HY8F4QVZE9WXDP3NKRTM
Content-Type: application/json

{
  "content": "How do I add a team member to my workspace?"
}
```

**Response 200:**
```json
{
  "id": "msg-uuid-789",
  "conversationId": "conv-uuid",
  "role": "assistant",
  "content": "To add a team member, go to **Workspace Settings → Members** and click **Invite Member**. Enter their email address and select their role (Author, Editor, or Reader). They will receive an invitation email valid for 72 hours. [1]",
  "citations": [
    {
      "index": 1,
      "articleId": "art-member-mgmt",
      "title": "Managing Workspace Members",
      "slug": "managing-workspace-members",
      "snippet": "Invite members from Workspace Settings → Members."
    }
  ],
  "tokensUsed": 278,
  "latencyMs": 1620,
  "createdAt": "2024-09-01T11:00:05Z"
}
```

---

### Example 4: Widget Suggestions

**Request:**
```http
GET /api/v1/widgets/wgt-uuid/suggestions?url=https%3A%2F%2Fapp.example.com%2Fsettings%2Fmembers HTTP/1.1
Host: api.kbplatform.io
X-Widget-Key: wk_live_01HY8F
Origin: https://app.example.com
```

**Response 200:**
```json
{
  "suggestions": [
    {
      "articleId": "art-001",
      "title": "Inviting Team Members",
      "slug": "inviting-team-members",
      "snippet": "Use the Invite Member button on the Members settings page.",
      "url": "https://docs.example.com/inviting-team-members",
      "score": 0.91
    },
    {
      "articleId": "art-002",
      "title": "Understanding Roles and Permissions",
      "slug": "roles-and-permissions",
      "snippet": "Authors can create articles; Editors can publish; Readers can view.",
      "url": "https://docs.example.com/roles-and-permissions",
      "score": 0.84
    },
    {
      "articleId": "art-003",
      "title": "Removing a Team Member",
      "slug": "removing-team-member",
      "snippet": "Remove a member from Workspace Settings → Members → Remove.",
      "url": "https://docs.example.com/removing-team-member",
      "score": 0.79
    }
  ],
  "widgetId": "wgt-uuid",
  "cacheHit": false
}
```

---

### Example 5: Analytics Deflection Report

**Request:**
```http
GET /api/v1/analytics/deflection?workspaceId=ws-uuid&from=2024-08-01&to=2024-08-31 HTTP/1.1
Host: api.kbplatform.io
Authorization: Bearer eyJhbGci...
```

**Response 200:**
```json
{
  "workspaceId": "ws-uuid",
  "dateRange": { "from": "2024-08-01", "to": "2024-08-31" },
  "totalWidgetSessions": 4821,
  "deflectedSessions": 3104,
  "deflectionRate": 0.644,
  "escalatedSessions": 712,
  "ticketsCreated": 689,
  "aiConversations": 2103,
  "avgResponseLatencyMs": 1734,
  "topDeflectedArticles": [
    { "articleId": "art-001", "title": "Password Reset", "deflectionCount": 312, "url": "/password-reset" },
    { "articleId": "art-002", "title": "Billing FAQ", "deflectionCount": 289, "url": "/billing-faq" }
  ],
  "dailyBreakdown": [
    { "date": "2024-08-01", "sessions": 157, "deflected": 99, "escalated": 23 }
  ]
}
```

---

## 7. Rate Limiting Headers

Every response includes:

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 43
X-RateLimit-Reset: 1725187200
Retry-After: 17
```

On `429 Too Many Requests`:
```json
{
  "type": "https://api.kbplatform.io/errors/rate-limit-exceeded",
  "title": "Rate Limit Exceeded",
  "status": 429,
  "detail": "You have exceeded the rate limit of 60 requests per minute.",
  "retryAfter": 17
}
```

---

## 8. Operational Policy Addendum

### 8.1 Content Governance Policies

- **Idempotency Window**: `Idempotency-Key` values are stored in Redis with a 24-hour TTL; duplicate requests within the window return the cached response with status `200` and header `X-Idempotent-Replay: true`.
- **Slug Generation**: Article and collection slugs are auto-generated from the title using `slugify` (lowercase, hyphen-separated, Unicode normalised); if a collision occurs, a 4-character nanoid suffix is appended. Authors may supply a custom slug subject to format validation.
- **API Versioning Lifecycle**: When a breaking change is introduced in `/api/v2/`, the `/api/v1/` version is supported for a minimum of 12 months with a `Deprecation` response header and a sunset date. Non-breaking additions (new optional fields) are made in-place.
- **Webhook Signature Verification**: All inbound webhooks (`/webhooks/zapier`, `/webhooks/zendesk`) are verified using HMAC-SHA256 with the workspace's webhook secret; requests with invalid signatures receive `401 Unauthorized` and are logged with `action=webhook_signature_invalid` in `audit_logs`.

### 8.2 Reader Data Privacy Policies

- **Anonymous Endpoint Access**: `GET /widgets/:id/suggestions` and `POST /widgets/:id/chat` accept unauthenticated requests authenticated only by `X-Widget-Key`; the response never includes PII of other users.
- **Content-Security-Policy**: All API responses include `Content-Security-Policy: default-src 'none'; frame-ancestors 'none'` to prevent embedding of API responses in iframes; the widget embed endpoint has its own relaxed CSP.
- **GDPR Data Subject Requests**: `POST /users/me/export` initiates an asynchronous data export job covering articles authored, feedback submitted, AI conversations, and analytics events linked to the user; the response includes a `jobId` polled via `GET /users/me/export/:jobId`.
- **Sensitive Endpoint Audit**: All calls to `DELETE /users/:id`, `PATCH /workspaces/:id/settings`, `POST /auth/sso/saml`, and `POST /integrations/:id/connect` write entries to `audit_logs` regardless of response outcome; failed attempts are logged with their error reason.

### 8.3 AI Usage Policies

- **POST /ai/conversations/:id/messages — Token Budget Header**: When the workspace's hourly token budget is below 20% remaining, the response includes `X-AI-TokenBudget-Remaining: <count>` and `X-AI-TokenBudget-Reset: <unix_ts>` to allow clients to display a usage warning.
- **Streaming Mode**: Adding `Accept: text/event-stream` to `POST /ai/conversations/:id/messages` switches the endpoint to SSE streaming; each token chunk is emitted as `data: {"delta": "token"}` and finalised with `data: {"done": true, "citations": [...]}`.
- **Content Moderation Pre-screen**: Before calling GPT-4o, the user's message is sent to `POST /v1/moderations` (OpenAI); if flagged, the endpoint returns `422` with `code: content_policy_violation` and a human-readable `detail` message.
- **AI Endpoint Disablement**: If `workspace.settings.ai.enabled = false`, all `/ai/*` endpoints return `403 Forbidden` with `code: ai_disabled_for_workspace`; this is enforced by a `AiEnabledGuard` applied globally to `AIController`.

### 8.4 System Availability Policies

- **Health Endpoint**: `GET /health` (unauthenticated) returns `{ "status": "ok", "db": true, "redis": true, "es": true, "version": "1.0.0" }`; used by ALB health checks and external uptime monitors. DB/Redis/ES checks use lightweight ping queries.
- **Circuit Breaker Headers**: When `ElasticsearchAdapter` or `OpenAIAdapter` circuit breakers are open, the corresponding API response includes `X-Degraded: elasticsearch` or `X-Degraded: openai` to inform clients of partial degradation.
- **Request Timeout**: All inbound API requests are subject to a 30-second server-side timeout enforced by the NestJS `TimeoutInterceptor`; timed-out requests return `503 Service Unavailable` with `code: request_timeout`.
- **Graceful Shutdown**: On ECS task SIGTERM, the NestJS app drains in-flight requests for up to 30 seconds before exiting; BullMQ workers complete the current job before shutting down, preventing mid-job state corruption.
