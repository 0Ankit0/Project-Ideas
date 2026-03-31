# API Design — Backend as a Service Platform

## Table of Contents
1. [Design Principles](#1-design-principles)
2. [Versioning & Base URL](#2-versioning--base-url)
3. [Request / Response Envelope](#3-request--response-envelope)
4. [Pagination](#4-pagination)
5. [Idempotency](#5-idempotency)
6. [Rate Limiting](#6-rate-limiting)
7. [Endpoint Reference](#7-endpoint-reference)
   - 7.1 Projects API
   - 7.2 Provider Catalog API
   - 7.3 Capability Bindings API
   - 7.4 Auth API
   - 7.5 Database API
   - 7.6 Storage API
   - 7.7 Functions API
   - 7.8 Events / Realtime API
   - 7.9 Secrets API
   - 7.10 Audit & Reports API
   - 7.11 Operations API
8. [Request / Response Examples](#8-request--response-examples)
9. [Error Code Catalogue](#9-error-code-catalogue)
10. [Authorization Matrix](#10-authorization-matrix)
11. [Webhook Payload Contract](#11-webhook-payload-contract)

---

## 1. Design Principles

| Principle | Implementation |
|-----------|----------------|
| **REST semantics** | Resources are nouns; HTTP verbs carry intent (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`) |
| **Versioning** | URL path prefix `/v1/`, `/v2/`; `Accept: application/vnd.baas.v1+json` header also accepted |
| **Idempotency** | All mutating requests accept `Idempotency-Key: <uuid>` header; replays return cached response for 24 h |
| **Error envelope** | All errors use `{ "error": { "code": "...", "message": "...", "details": [...] } }` |
| **Pagination** | Cursor-based via `next_cursor` / `prev_cursor`; also supports `page` + `per_page` for small collections |
| **Rate limiting** | Token-bucket per project + per caller IP; headers `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` |
| **HATEOAS (light)** | Resources include `_links` for common transitions |
| **Content negotiation** | `Content-Type: application/json`; binary uploads use `multipart/form-data` |
| **Tracing** | All responses carry `X-Request-Id` and `X-Trace-Id` (W3C traceparent) |
| **Deprecation** | `Sunset` header + `Deprecation` header on deprecated endpoints |

---

## 2. Versioning & Base URL

```
https://api.baas.io/v1/{resource}
```

Every endpoint is prefixed with the API version. Breaking changes bump the major version. Non-breaking additions (new optional fields, new endpoints) are shipped within the same version.

---

## 3. Request / Response Envelope

### Success (single resource)
```json
{
  "data": { ... },
  "_links": {
    "self":   { "href": "/v1/projects/proj_abc" },
    "update": { "href": "/v1/projects/proj_abc", "method": "PATCH" }
  },
  "meta": {
    "request_id": "req_01HXZ3K",
    "timestamp":  "2025-01-15T10:30:00Z"
  }
}
```

### Success (list)
```json
{
  "data": [ { ... }, { ... } ],
  "pagination": {
    "total":       150,
    "per_page":    20,
    "next_cursor": "eyJpZCI6IjUwIn0=",
    "prev_cursor": null
  },
  "meta": { "request_id": "req_01HXZ3K", "timestamp": "2025-01-15T10:30:00Z" }
}
```

### Error
```json
{
  "error": {
    "code":    "AUTH_TOKEN_EXPIRED",
    "message": "The provided access token has expired.",
    "details": [
      { "field": "Authorization", "issue": "token_expired", "expired_at": "2025-01-15T09:00:00Z" }
    ],
    "doc_url": "https://docs.baas.io/errors/AUTH_TOKEN_EXPIRED"
  },
  "meta": { "request_id": "req_01HXZ3K", "timestamp": "2025-01-15T10:30:00Z" }
}
```

---

## 4. Pagination

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cursor`  | string | — | Opaque base64 cursor from previous response |
| `page`    | int  | 1 | 1-based page (only for small collections < 10k) |
| `per_page`| int  | 20 | Max 100 |
| `sort`    | string | `created_at:desc` | `field:asc\|desc` |
| `filter`  | string | — | RSQ filter string e.g. `status eq "active"` |

---

## 5. Idempotency

Clients **MUST** send `Idempotency-Key: <uuid-v4>` for all `POST`, `PUT`, `PATCH`, `DELETE` requests. Keys are stored for **24 hours**. A replayed request with the same key returns the original HTTP status and body without re-executing the operation. Keys are scoped to `(project_id, caller_id)`.

---

## 6. Rate Limiting

| Endpoint Group | Limit (per minute) | Burst | Scope |
|----------------|--------------------|-------|-------|
| Auth API | 30 req/min | 10 | Per IP |
| Database API | 600 req/min | 100 | Per project |
| Storage Upload | 60 req/min | 20 | Per project |
| Storage Download | 1200 req/min | 200 | Per project |
| Functions Invoke | 300 req/min | 50 | Per function |
| Events Publish | 600 req/min | 100 | Per channel |
| Control Plane | 120 req/min | 20 | Per tenant |
| Secrets API | 60 req/min | 10 | Per project |
| Audit / Reports | 60 req/min | 10 | Per tenant |

---

## 7. Endpoint Reference

### 7.1 Projects API

Base: `/v1/projects`

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| `GET`    | `/v1/projects`                          | List all projects for the tenant | tenant:viewer |
| `POST`   | `/v1/projects`                          | Create a new project | tenant:admin |
| `GET`    | `/v1/projects/{projectId}`              | Get project details | project:viewer |
| `PATCH`  | `/v1/projects/{projectId}`              | Update project metadata | project:admin |
| `DELETE` | `/v1/projects/{projectId}`              | Soft-delete project | tenant:admin |
| `GET`    | `/v1/projects/{projectId}/environments` | List environments | project:viewer |
| `POST`   | `/v1/projects/{projectId}/environments` | Create environment | project:admin |
| `GET`    | `/v1/projects/{projectId}/environments/{envId}` | Get environment | project:viewer |
| `PATCH`  | `/v1/projects/{projectId}/environments/{envId}` | Update environment | project:admin |
| `DELETE` | `/v1/projects/{projectId}/environments/{envId}` | Delete environment | project:admin |

---

### 7.2 Provider Catalog API

Base: `/v1/catalog`

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| `GET`  | `/v1/catalog/providers`                     | List all certified adapters | any |
| `GET`  | `/v1/catalog/providers/{providerKey}`        | Get provider details + schema | any |
| `GET`  | `/v1/catalog/capability-types`              | List capability type definitions | any |
| `GET`  | `/v1/catalog/capability-types/{typeSlug}`   | Get capability type + required config | any |

---

### 7.3 Capability Bindings API

Base: `/v1/projects/{projectId}/environments/{envId}/bindings`

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| `GET`    | `/bindings`                        | List all bindings for the environment | project:viewer |
| `POST`   | `/bindings`                        | Create a new capability binding | project:admin |
| `GET`    | `/bindings/{bindingId}`            | Get binding details | project:viewer |
| `PATCH`  | `/bindings/{bindingId}`            | Update binding config | project:admin |
| `DELETE` | `/bindings/{bindingId}`            | Delete binding | project:admin |
| `POST`   | `/bindings/{bindingId}/validate`   | Re-validate binding | project:admin |
| `POST`   | `/bindings/{bindingId}/switch`     | Initiate provider switchover | project:admin |
| `POST`   | `/bindings/{bindingId}/rollback`   | Rollback to previous provider | project:admin |
| `GET`    | `/bindings/{bindingId}/history`    | Get binding state history | project:viewer |

---

### 7.4 Auth API

Base: `/v1/auth` (project-scoped via `X-Project-Id` header)

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| `POST`   | `/v1/auth/register`                    | Register new user (email+password) | none |
| `POST`   | `/v1/auth/login`                       | Login with credentials | none |
| `POST`   | `/v1/auth/logout`                      | Invalidate current session | user |
| `POST`   | `/v1/auth/refresh`                     | Refresh access token | refresh_token |
| `GET`    | `/v1/auth/sessions`                    | List active sessions | user |
| `DELETE` | `/v1/auth/sessions/{sessionId}`        | Revoke a session | user |
| `GET`    | `/v1/auth/me`                          | Get current user profile | user |
| `PATCH`  | `/v1/auth/me`                          | Update user profile | user |
| `POST`   | `/v1/auth/password/reset`              | Request password reset | none |
| `PUT`    | `/v1/auth/password/reset/{token}`      | Confirm password reset | none |
| `POST`   | `/v1/auth/mfa/enroll`                  | Enroll TOTP MFA | user |
| `POST`   | `/v1/auth/mfa/verify`                  | Verify TOTP code | user |
| `DELETE` | `/v1/auth/mfa`                         | Disable MFA | user |
| `GET`    | `/v1/auth/oauth/{provider}`            | Initiate OAuth flow | none |
| `GET`    | `/v1/auth/oauth/{provider}/callback`   | OAuth callback handler | none |
| `GET`    | `/v1/auth/providers`                   | List configured OAuth providers | none |

---

### 7.5 Database API

Base: `/v1/db` (project+environment scoped via headers)

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| `GET`    | `/v1/db/namespaces`                          | List namespaces (schemas) | db:viewer |
| `POST`   | `/v1/db/namespaces`                          | Create namespace | db:admin |
| `DELETE` | `/v1/db/namespaces/{ns}`                     | Drop namespace | db:admin |
| `GET`    | `/v1/db/namespaces/{ns}/tables`              | List tables | db:viewer |
| `POST`   | `/v1/db/namespaces/{ns}/tables`              | Define a new table | db:admin |
| `GET`    | `/v1/db/namespaces/{ns}/tables/{table}`      | Get table schema | db:viewer |
| `PATCH`  | `/v1/db/namespaces/{ns}/tables/{table}`      | Alter table | db:admin |
| `DELETE` | `/v1/db/namespaces/{ns}/tables/{table}`      | Drop table | db:admin |
| `GET`    | `/v1/db/namespaces/{ns}/tables/{table}/rows` | Query rows | db:reader |
| `POST`   | `/v1/db/namespaces/{ns}/tables/{table}/rows` | Insert row | db:writer |
| `PATCH`  | `/v1/db/namespaces/{ns}/tables/{table}/rows/{id}` | Update row | db:writer |
| `DELETE` | `/v1/db/namespaces/{ns}/tables/{table}/rows/{id}` | Delete row | db:writer |
| `POST`   | `/v1/db/query`                               | Execute raw parameterized SELECT | db:reader |
| `GET`    | `/v1/db/migrations`                          | List migrations | db:admin |
| `POST`   | `/v1/db/migrations`                          | Create migration | db:admin |
| `POST`   | `/v1/db/migrations/{migId}/apply`            | Apply migration | db:admin |
| `POST`   | `/v1/db/migrations/{migId}/rollback`         | Rollback migration | db:admin |
| `GET`    | `/v1/db/permissions`                         | List RLS policies | db:admin |
| `POST`   | `/v1/db/permissions`                         | Create RLS policy | db:admin |
| `DELETE` | `/v1/db/permissions/{policyId}`              | Remove RLS policy | db:admin |

---

### 7.6 Storage API

Base: `/v1/storage`

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| `GET`    | `/v1/storage/buckets`                            | List buckets | storage:viewer |
| `POST`   | `/v1/storage/buckets`                            | Create bucket | storage:admin |
| `GET`    | `/v1/storage/buckets/{bucketId}`                 | Get bucket metadata | storage:viewer |
| `PATCH`  | `/v1/storage/buckets/{bucketId}`                 | Update bucket config | storage:admin |
| `DELETE` | `/v1/storage/buckets/{bucketId}`                 | Delete bucket | storage:admin |
| `GET`    | `/v1/storage/buckets/{bucketId}/files`           | List files | storage:viewer |
| `POST`   | `/v1/storage/buckets/{bucketId}/files`           | Upload file (multipart) | storage:writer |
| `GET`    | `/v1/storage/buckets/{bucketId}/files/{fileId}`  | Get file metadata | storage:viewer |
| `DELETE` | `/v1/storage/buckets/{bucketId}/files/{fileId}`  | Delete file | storage:writer |
| `GET`    | `/v1/storage/buckets/{bucketId}/files/{fileId}/download` | Download file | storage:reader |
| `POST`   | `/v1/storage/buckets/{bucketId}/files/{fileId}/signed-url` | Generate signed URL | storage:writer |
| `POST`   | `/v1/storage/buckets/{bucketId}/grants`          | Create access grant | storage:admin |
| `DELETE` | `/v1/storage/buckets/{bucketId}/grants/{grantId}` | Revoke access grant | storage:admin |

---

### 7.7 Functions API

Base: `/v1/functions`

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| `GET`    | `/v1/functions`                                | List functions | functions:viewer |
| `POST`   | `/v1/functions`                                | Create function definition | functions:admin |
| `GET`    | `/v1/functions/{funcId}`                       | Get function details | functions:viewer |
| `PATCH`  | `/v1/functions/{funcId}`                       | Update function config | functions:admin |
| `DELETE` | `/v1/functions/{funcId}`                       | Delete function | functions:admin |
| `POST`   | `/v1/functions/{funcId}/deployments`           | Deploy new version | functions:admin |
| `GET`    | `/v1/functions/{funcId}/deployments`           | List deployments | functions:viewer |
| `GET`    | `/v1/functions/{funcId}/deployments/{depId}`   | Get deployment status | functions:viewer |
| `POST`   | `/v1/functions/{funcId}/invoke`                | Synchronous invoke | functions:invoker |
| `POST`   | `/v1/functions/{funcId}/invoke/async`          | Async invoke (returns executionId) | functions:invoker |
| `GET`    | `/v1/functions/{funcId}/executions`            | List executions | functions:viewer |
| `GET`    | `/v1/functions/{funcId}/executions/{execId}`   | Get execution result | functions:viewer |
| `GET`    | `/v1/functions/{funcId}/schedules`             | List schedules | functions:viewer |
| `POST`   | `/v1/functions/{funcId}/schedules`             | Create cron schedule | functions:admin |
| `DELETE` | `/v1/functions/{funcId}/schedules/{schedId}`   | Delete schedule | functions:admin |

---

### 7.8 Events / Realtime API

Base: `/v1/events`

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| `GET`    | `/v1/events/channels`                          | List channels | events:viewer |
| `POST`   | `/v1/events/channels`                          | Create channel | events:admin |
| `DELETE` | `/v1/events/channels/{channelId}`              | Delete channel | events:admin |
| `POST`   | `/v1/events/channels/{channelId}/publish`      | Publish event | events:publisher |
| `GET`    | `/v1/events/channels/{channelId}/subscriptions`| List subscriptions | events:admin |
| `POST`   | `/v1/events/channels/{channelId}/subscribe`    | Create subscription | events:subscriber |
| `DELETE` | `/v1/events/channels/{channelId}/subscriptions/{subId}` | Cancel subscription | events:subscriber |
| `GET`    | `/v1/events/webhooks`                          | List webhooks | events:admin |
| `POST`   | `/v1/events/webhooks`                          | Register webhook | events:admin |
| `DELETE` | `/v1/events/webhooks/{webhookId}`              | Delete webhook | events:admin |
| `GET`    | `/v1/events/realtime`                          | WebSocket upgrade (Realtime) | user |

---

### 7.9 Secrets API

Base: `/v1/secrets`

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| `GET`    | `/v1/secrets`                     | List secret refs (names only) | secrets:viewer |
| `POST`   | `/v1/secrets`                     | Register new secret ref | secrets:admin |
| `GET`    | `/v1/secrets/{secretId}`          | Get secret metadata (no value) | secrets:viewer |
| `PUT`    | `/v1/secrets/{secretId}/rotate`   | Rotate secret value | secrets:admin |
| `DELETE` | `/v1/secrets/{secretId}`          | Delete secret ref | secrets:admin |

---

### 7.10 Audit & Reports API

Base: `/v1/audit`

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| `GET`  | `/v1/audit/logs`                           | Query audit log (filterable) | tenant:auditor |
| `GET`  | `/v1/audit/logs/{logId}`                   | Get single audit event | tenant:auditor |
| `GET`  | `/v1/audit/reports/usage`                  | Usage summary by project | tenant:admin |
| `GET`  | `/v1/audit/reports/capability-health`      | SLO status per binding | project:admin |
| `GET`  | `/v1/audit/reports/error-budget`           | Error budget burn rate | project:admin |

---

### 7.11 Operations API

Base: `/v1/ops`

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| `GET`  | `/v1/ops/switchover-plans`                         | List switchover plans | project:admin |
| `POST` | `/v1/ops/switchover-plans`                         | Create switchover plan | project:admin |
| `GET`  | `/v1/ops/switchover-plans/{planId}`                | Get plan details | project:admin |
| `POST` | `/v1/ops/switchover-plans/{planId}/dry-run`        | Execute dry run | project:admin |
| `POST` | `/v1/ops/switchover-plans/{planId}/apply`          | Apply switchover | project:admin |
| `POST` | `/v1/ops/switchover-plans/{planId}/rollback`       | Rollback switchover | project:admin |
| `GET`  | `/v1/ops/switchover-plans/{planId}/checkpoints`    | List checkpoints | project:admin |
| `GET`  | `/v1/ops/health`                                   | Platform health check | any |
| `GET`  | `/v1/ops/health/{component}`                       | Component health | any |

---

## 8. Request / Response Examples

### 8.1 Register User

**Request**
```http
POST /v1/auth/register
Content-Type: application/json
X-Project-Id: proj_01HXZ3K
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000

{
  "email": "alice@example.com",
  "password": "S3cur3P@ssw0rd!",
  "name": "Alice Smith",
  "metadata": { "signup_source": "web" }
}
```

**Response** `201 Created`
```json
{
  "data": {
    "user_id":    "usr_01J3KMAB",
    "email":      "alice@example.com",
    "name":       "Alice Smith",
    "status":     "pending",
    "created_at": "2025-01-15T10:30:00Z"
  },
  "_links": {
    "self":    { "href": "/v1/auth/me" },
    "verify":  { "href": "/v1/auth/verify-email", "method": "POST" }
  },
  "meta": { "request_id": "req_01HXZ3K", "timestamp": "2025-01-15T10:30:00Z" }
}
```

---

### 8.2 Create Capability Binding

**Request**
```http
POST /v1/projects/proj_01HXZ3K/environments/env_prod/bindings
Content-Type: application/json
Authorization: Bearer <admin_token>
Idempotency-Key: 7c9e6679-7425-40de-944b-e07fc1f90ae7

{
  "capability_type": "object_storage",
  "provider_key":    "aws_s3",
  "display_name":    "Production S3 Bucket",
  "config": {
    "region":      "us-east-1",
    "bucket_name": "baas-prod-assets",
    "secret_refs": {
      "access_key_id":     "secret_ref:sec_awskey",
      "secret_access_key": "secret_ref:sec_awssecret"
    }
  }
}
```

**Response** `201 Created`
```json
{
  "data": {
    "binding_id":      "bind_09ZAQ1",
    "capability_type": "object_storage",
    "provider_key":    "aws_s3",
    "display_name":    "Production S3 Bucket",
    "status":          "validating",
    "version":         1,
    "created_at":      "2025-01-15T10:31:00Z"
  },
  "_links": {
    "self":     { "href": "/v1/projects/proj_01HXZ3K/environments/env_prod/bindings/bind_09ZAQ1" },
    "validate": { "href": "/v1/.../bindings/bind_09ZAQ1/validate", "method": "POST" }
  },
  "meta": { "request_id": "req_02ABY4L", "timestamp": "2025-01-15T10:31:00Z" }
}
```

---

### 8.3 Insert Database Row

**Request**
```http
POST /v1/db/namespaces/app/tables/products/rows
Content-Type: application/json
Authorization: Bearer <user_token>
X-Project-Id: proj_01HXZ3K
X-Environment: prod

{
  "name":        "Wireless Headphones",
  "sku":         "WH-2000",
  "price_cents": 9999,
  "stock":       42,
  "tags":        ["audio", "wireless"]
}
```

**Response** `201 Created`
```json
{
  "data": {
    "id":          "row_7a2bc3",
    "name":        "Wireless Headphones",
    "sku":         "WH-2000",
    "price_cents": 9999,
    "stock":       42,
    "tags":        ["audio", "wireless"],
    "created_at":  "2025-01-15T10:35:00Z",
    "updated_at":  "2025-01-15T10:35:00Z"
  },
  "meta": { "request_id": "req_03CDE5M", "timestamp": "2025-01-15T10:35:00Z" }
}
```

---

### 8.4 Generate Signed URL

**Request**
```http
POST /v1/storage/buckets/bkt_9xzq01/files/file_abc123/signed-url
Content-Type: application/json
Authorization: Bearer <user_token>

{
  "operation":  "download",
  "expires_in": 3600,
  "allowed_ip": "203.0.113.0/24"
}
```

**Response** `200 OK`
```json
{
  "data": {
    "signed_url": "https://storage.baas.io/v1/dl/bkt_9xzq01/file_abc123?sig=eyJhbGci...&exp=1737030600",
    "expires_at": "2025-01-15T11:30:00Z",
    "operation":  "download"
  },
  "meta": { "request_id": "req_04DEF6N", "timestamp": "2025-01-15T10:30:00Z" }
}
```

---

### 8.5 Invoke Function (Synchronous)

**Request**
```http
POST /v1/functions/fn_resize01/invoke
Content-Type: application/json
Authorization: Bearer <user_token>
X-Project-Id: proj_01HXZ3K

{
  "payload": {
    "file_id": "file_abc123",
    "width":   320,
    "height":  240,
    "format":  "webp"
  }
}
```

**Response** `200 OK`
```json
{
  "data": {
    "execution_id":  "exec_99ZZQ1",
    "function_id":   "fn_resize01",
    "status":        "completed",
    "result": {
      "output_file_id": "file_xyz789",
      "size_bytes":     45231
    },
    "duration_ms":  234,
    "started_at":   "2025-01-15T10:30:00.100Z",
    "completed_at": "2025-01-15T10:30:00.334Z"
  },
  "meta": { "request_id": "req_05EFG7O", "timestamp": "2025-01-15T10:30:00Z" }
}
```

---

### 8.6 Create Switchover Plan

**Request**
```http
POST /v1/ops/switchover-plans
Content-Type: application/json
Authorization: Bearer <admin_token>
Idempotency-Key: a1b2c3d4-e5f6-7890-abcd-ef1234567890

{
  "binding_id":      "bind_09ZAQ1",
  "target_provider": "gcp_gcs",
  "target_config": {
    "project_id":  "my-gcp-project",
    "bucket_name": "baas-prod-assets-gcp",
    "secret_refs": { "service_account_json": "secret_ref:sec_gcpsa" }
  },
  "strategy":       "blue_green",
  "dry_run_first":  true,
  "notes":          "Migrating from S3 to GCS for cost optimization"
}
```

**Response** `201 Created`
```json
{
  "data": {
    "plan_id":         "plan_ZZ1001",
    "binding_id":      "bind_09ZAQ1",
    "status":          "planned",
    "target_provider": "gcp_gcs",
    "strategy":        "blue_green",
    "dry_run_first":   true,
    "created_at":      "2025-01-15T10:40:00Z"
  },
  "_links": {
    "dry-run": { "href": "/v1/ops/switchover-plans/plan_ZZ1001/dry-run", "method": "POST" },
    "apply":   { "href": "/v1/ops/switchover-plans/plan_ZZ1001/apply",   "method": "POST" }
  },
  "meta": { "request_id": "req_06FGH8P", "timestamp": "2025-01-15T10:40:00Z" }
}
```

---

## 9. Error Code Catalogue

| Code | HTTP Status | Category | Description | Retry? |
|------|-------------|----------|-------------|--------|
| `VALIDATION_REQUIRED_FIELD` | 400 | Validation | A required field is missing | No |
| `VALIDATION_INVALID_FORMAT` | 400 | Validation | Field value does not match expected format | No |
| `VALIDATION_ENUM_MISMATCH`  | 400 | Validation | Value not in allowed set | No |
| `AUTH_UNAUTHENTICATED`      | 401 | Auth | No valid credentials provided | No |
| `AUTH_TOKEN_EXPIRED`        | 401 | Auth | Access token has expired | With refresh |
| `AUTH_TOKEN_INVALID`        | 401 | Auth | Token signature invalid or malformed | No |
| `AUTH_MFA_REQUIRED`         | 403 | Auth | MFA challenge required | With MFA |
| `AUTHZ_FORBIDDEN`           | 403 | Authorization | Caller lacks required permission | No |
| `AUTHZ_SCOPE_INSUFFICIENT`  | 403 | Authorization | Token scope does not cover this endpoint | No |
| `NOT_FOUND_RESOURCE`        | 404 | Resource | Requested resource does not exist | No |
| `CONFLICT_DUPLICATE_KEY`    | 409 | Conflict | Unique constraint violation | No |
| `CONFLICT_IDEMPOTENCY`      | 409 | Conflict | Idempotency key collision with different body | No |
| `CONFLICT_STATE_TRANSITION` | 409 | Conflict | Invalid state transition requested | No |
| `RATE_LIMIT_EXCEEDED`       | 429 | Rate Limit | Too many requests; see `Retry-After` header | After delay |
| `QUOTA_EXCEEDED_STORAGE`    | 429 | Quota | Project storage quota exceeded | No |
| `QUOTA_EXCEEDED_EXECUTIONS` | 429 | Quota | Monthly function execution quota exceeded | No |
| `DB_QUERY_ERROR`            | 422 | Database | Malformed or invalid SQL query | No |
| `DB_MIGRATION_LOCKED`       | 423 | Database | Another migration is currently running | After delay |
| `DB_RLS_POLICY_VIOLATION`   | 403 | Database | Row blocked by RLS policy | No |
| `STORAGE_OBJECT_TOO_LARGE`  | 413 | Storage | File exceeds max upload size for bucket | No |
| `FUNCTION_TIMEOUT`          | 504 | Functions | Function execution exceeded time limit | Yes (idempotent) |
| `FUNCTION_SCAN_FAILED`      | 422 | Functions | Security scan rejected deployment artifact | No |
| `PROVIDER_UNAVAILABLE`      | 503 | Provider | External provider returned an error | Yes (exponential) |
| `PROVIDER_CONFIG_INVALID`   | 422 | Provider | Provider configuration validation failed | No |
| `SWITCHOVER_PARITY_FAILED`  | 422 | Switchover | Dry-run parity check found discrepancies | No |
| `SECRET_NOT_FOUND`          | 404 | Secrets | Referenced secret does not exist | No |
| `INTERNAL_SERVER_ERROR`     | 500 | Internal | Unexpected server error | Yes |
| `SERVICE_UNAVAILABLE`       | 503 | Internal | Service temporarily unavailable | Yes (exponential) |

---

## 10. Authorization Matrix

Roles: `tenant:admin`, `tenant:auditor`, `project:admin`, `project:viewer`, `db:admin`, `db:reader`, `db:writer`, `storage:admin`, `storage:reader`, `storage:writer`, `functions:admin`, `functions:invoker`, `events:admin`, `events:publisher`, `secrets:admin`, `user`

| Endpoint Group | tenant:admin | project:admin | project:viewer | service-specific role |
|----------------|:---:|:---:|:---:|:---:|
| Projects CRUD | ✅ | read/update own | read own | — |
| Provider Catalog | ✅ | ✅ (read) | ✅ (read) | — |
| Capability Bindings | ✅ | ✅ | read | — |
| Switchover Plans | ✅ | ✅ | — | — |
| Auth API | ✅ | ✅ | read | `user` for own data |
| Database API | ✅ | ✅ | read | `db:*` roles |
| Storage API | ✅ | ✅ | read | `storage:*` roles |
| Functions API | ✅ | ✅ | read | `functions:*` roles |
| Events API | ✅ | ✅ | read | `events:*` roles |
| Secrets API | ✅ | ✅ | — | `secrets:admin` |
| Audit Logs | ✅ (all) | own project | — | `tenant:auditor` |
| Ops / Health | ✅ | ✅ | — | — |

---

## 11. Webhook Payload Contract

All outbound webhooks share this envelope:

```json
{
  "webhook_id":    "wh_01ABCD",
  "delivery_id":   "dlv_99XYZ1",
  "event_type":    "binding.status_changed",
  "project_id":    "proj_01HXZ3K",
  "environment":   "prod",
  "occurred_at":   "2025-01-15T10:30:00Z",
  "payload": {
    "binding_id": "bind_09ZAQ1",
    "old_status": "switching",
    "new_status": "active",
    "provider":   "gcp_gcs"
  },
  "signature": "sha256=abc123...",
  "retry_count": 0
}
```

**Signature verification**: `HMAC-SHA256` over `delivery_id + "." + occurred_at + "." + raw_body` using the webhook secret. Verify before processing.

**Delivery guarantee**: At-least-once. Idempotent handlers are required. Retries use exponential back-off: 5 s, 30 s, 5 min, 30 min, 2 h (5 attempts total).

| Event Type | Trigger |
|------------|---------|
| `binding.created` | New capability binding created |
| `binding.status_changed` | Binding status transition |
| `switchover.completed` | Switchover plan reached `completed` |
| `switchover.rolled_back` | Switchover rolled back |
| `function.deployed` | New function deployment ready |
| `function.execution_failed` | Function execution errored |
| `db.migration_applied` | Schema migration completed |
| `db.migration_failed` | Schema migration errored |
| `storage.quota_warning` | Storage usage > 80% of quota |
| `auth.user_suspended` | User account suspended |
