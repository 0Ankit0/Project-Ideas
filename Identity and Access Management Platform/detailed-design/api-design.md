# API Design

**Base URL:** `https://api.iam-platform.example.com/v1`

---

## 1. Authentication

All endpoints require a JWT Bearer token unless explicitly marked as public.

```
Authorization: Bearer <access_token>
```

Tokens are RS256-signed JWTs issued by the IAM Platform Token Service. The `aud` claim must match the target service identifier. Token lifetime is 10 minutes. Refresh tokens are opaque, single-use, and rotate on each exchange.

---

## 2. Standard Request Headers

| Header | Required | Description |
|---|---|---|
| `Authorization` | Yes (most) | `Bearer <access_token>` |
| `Content-Type` | Yes (writes) | `application/json` |
| `Accept` | No | `application/json` (default) |
| `X-Request-ID` | Recommended | Client-generated UUID for end-to-end tracing |
| `X-Idempotency-Key` | Recommended | UUID for safe retry of write operations |
| `X-Tenant-ID` | Conditional | Required when acting on behalf of a specific tenant |

All responses include:

| Header | Description |
|---|---|
| `X-Request-ID` | Echoed from request, or server-generated |
| `X-Correlation-ID` | Internal trace identifier |
| `X-RateLimit-Limit` | Requests allowed per window |
| `X-RateLimit-Remaining` | Requests remaining in current window |
| `X-RateLimit-Reset` | Unix timestamp when window resets |

---

## 3. Pagination

All list endpoints use **cursor-based pagination** to ensure consistency under concurrent writes.

**Query parameters:**

| Parameter | Type | Default | Max | Description |
|---|---|---|---|---|
| `after` | string | — | — | Opaque cursor from previous response |
| `limit` | integer | 20 | 100 | Number of items to return |

**Response envelope:**

```json
{
  "data": [ ... ],
  "pagination": {
    "next_cursor": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9",
    "has_more": true,
    "total_count": 4820
  }
}
```

`total_count` is an approximate count for large tables. When `has_more` is `false`, `next_cursor` is omitted. Cursors are opaque base64-encoded values; clients must not attempt to decode or construct them.

---

## 4. Error Format

All errors follow [RFC 7807](https://www.rfc-editor.org/rfc/rfc7807) Problem+JSON.

```json
{
  "type": "https://api.iam-platform.example.com/errors/AUTH_003",
  "title": "MFA verification required",
  "status": 403,
  "detail": "This action requires a verified MFA challenge for the current session.",
  "instance": "/v1/users/8f3c2a1b-...",
  "code": "AUTH_003",
  "retryable": false,
  "correlation_id": "3b7a9c01-f2de-4811-bb3a-7c92ed4f1aa2",
  "remediation": "Complete MFA verification at POST /v1/auth/mfa/verify before retrying."
}
```

---

## 5. Endpoint Reference

### 5.1 Authentication (`/auth`)

#### POST /auth/login

Initiate the authentication flow. Accepts password, SAML, or OIDC federation depending on the `method` field.

**Request:**
```json
{
  "email": "alice@example.com",
  "password": "correct-horse-battery-staple",
  "method": "password",
  "client_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "redirect_uri": "https://app.example.com/callback",
  "state": "opaque-state-string",
  "nonce": "random-nonce-string"
}
```

**Response `200 OK`:**
```json
{
  "status": "mfa_required",
  "mfa_token": "eyJhbGciOiJSUzI1NiJ9...",
  "available_methods": ["totp", "webauthn"],
  "expires_in": 300
}
```

**Response `200 OK` (no MFA):**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiJ9...",
  "refresh_token": "dGhpcyBpcyBhbiBlbmNvZGVkIHJlZnJlc2ggdG9rZW4",
  "token_type": "Bearer",
  "expires_in": 600,
  "scope": "openid profile email",
  "session_id": "a1b2c3d4-..."
}
```

#### POST /auth/callback

Handles the OAuth 2.0 authorization code exchange or SAML assertion post.

**Request:**
```json
{
  "code": "SplxlOBeZQQYbYS6WxSbIA",
  "state": "opaque-state-string",
  "provider_id": "9a8b7c6d-..."
}
```

**Response `200 OK`:** Same token response shape as `/auth/login`.

#### POST /auth/refresh

Exchange a refresh token for a new access/refresh token pair. The old refresh token is invalidated immediately.

**Request:**
```json
{
  "refresh_token": "dGhpcyBpcyBhbiBlbmNvZGVkIHJlZnJlc2ggdG9rZW4",
  "client_id": "3fa85f64-..."
}
```

**Response `200 OK`:**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiJ9...",
  "refresh_token": "bmV3IHJlZnJlc2ggdG9rZW4gZ29lcyBoZXJl",
  "token_type": "Bearer",
  "expires_in": 600
}
```

#### POST /auth/logout

Revoke the current session and associated token family.

**Request body:** empty  
**Response `204 No Content`**

#### POST /auth/logout-all

Revoke all active sessions for the authenticated principal across all devices.

**Response `204 No Content`**

#### GET /auth/me

Return the authenticated principal's profile, effective roles, and current session metadata.

**Response `200 OK`:**
```json
{
  "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "email": "alice@example.com",
  "display_name": "Alice Smith",
  "status": "active",
  "mfa_required": true,
  "assurance_level": 2,
  "roles": ["admin", "viewer"],
  "session_id": "a1b2c3d4-...",
  "auth_time": "2025-01-15T10:30:00Z",
  "expires_at": "2025-01-15T10:40:00Z"
}
```

#### POST /auth/mfa/challenge

Initiate a step-up MFA challenge for an existing session that requires elevated assurance.

**Request:**
```json
{
  "mfa_token": "eyJhbGciOiJSUzI1NiJ9...",
  "method": "totp"
}
```

**Response `200 OK`:**
```json
{
  "challenge_id": "c7d8e9f0-...",
  "method": "totp",
  "expires_in": 300
}
```

#### POST /auth/mfa/verify

Verify the MFA response for an active challenge.

**Request:**
```json
{
  "challenge_id": "c7d8e9f0-...",
  "method": "totp",
  "code": "123456"
}
```

**Response `200 OK`:** Full token response (same as `/auth/login` without MFA).

---

### 5.2 Users (`/users`)

#### GET /users

List users within the authenticated tenant.

**Query params:** `status`, `email` (prefix match), `org_id`, `role_id`, `after`, `limit`

**Response `200 OK`:** Paginated list of user objects.

#### POST /users

Invite or provision a new user.

**Request:**
```json
{
  "email": "bob@example.com",
  "display_name": "Bob Jones",
  "org_id": "1a2b3c4d-...",
  "roles": ["viewer"],
  "mfa_required": true,
  "send_invite": true,
  "profile": {
    "department": "Engineering",
    "job_title": "Software Engineer"
  }
}
```

**Response `201 Created`:** Full user object.

#### GET /users/{userId}

**Response `200 OK`:** Full user object including roles, groups, and last session metadata.

#### PATCH /users/{userId}

Partial update. Accepted fields: `display_name`, `org_id`, `mfa_required`, `profile`.  
Status transitions use dedicated sub-resources (see below).

**Response `200 OK`:** Updated user object.

#### DELETE /users/{userId}

Deprovision the user: revoke all sessions, revoke all tokens, disable all MFA devices, remove all role assignments, and set `status = 'deprovisioned'`. Async; returns `202 Accepted` with an operation ID.

**Response `202 Accepted`:**
```json
{ "operation_id": "op_8d7c6b5a-...", "status": "pending" }
```

#### POST /users/{userId}/suspend

Set `status = 'suspended'` and revoke all active sessions.

**Request:** `{ "reason": "Security investigation" }`  
**Response `200 OK`:** Updated user object.

#### POST /users/{userId}/restore

Restore a suspended user to `active`.

**Response `200 OK`:** Updated user object.

#### GET /users/{userId}/sessions

List all sessions for a user, ordered by `last_active_at` descending.

**Response `200 OK`:** Paginated list of session objects.

#### GET /users/{userId}/roles

List all direct role assignments for the user.

**Response `200 OK`:** Array of `{ role_id, name, granted_by, granted_at, expires_at }`.

#### POST /users/{userId}/roles

Assign a role to a user.

**Request:** `{ "role_id": "...", "expires_at": "2025-12-31T23:59:59Z" }`  
**Response `201 Created`:** Assignment object.

#### DELETE /users/{userId}/roles/{roleId}

Remove a role assignment.  
**Response `204 No Content`**

---

### 5.3 Service Accounts (`/service-accounts`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/service-accounts` | List service accounts; filter by `status`, `name` |
| `POST` | `/service-accounts` | Create a service account; returns `client_id` + plaintext `client_secret` (shown once) |
| `GET` | `/service-accounts/{id}` | Get service account details |
| `PATCH` | `/service-accounts/{id}` | Update `description`, `allowed_scopes`, `expires_at` |
| `DELETE` | `/service-accounts/{id}` | Retire service account; revoke all active tokens |
| `POST` | `/service-accounts/{id}/rotate-credentials` | Generate a new `client_secret`, invalidate the previous one |

**Create response `201 Created`:**
```json
{
  "sa_id": "5f4e3d2c-...",
  "client_id": "sa_a1b2c3d4e5f6",
  "client_secret": "sk_live_SHOWN_ONCE_...",
  "name": "ci-deploy-bot",
  "status": "active",
  "created_at": "2025-01-15T10:30:00Z"
}
```

---

### 5.4 Groups (`/groups`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/groups` | List groups; filter by `type`, `name` |
| `POST` | `/groups` | Create group |
| `GET` | `/groups/{id}` | Get group |
| `PATCH` | `/groups/{id}` | Update `name`, `description` |
| `DELETE` | `/groups/{id}` | Delete group; removes all memberships and role assignments |
| `GET` | `/groups/{id}/members` | List group members |
| `POST` | `/groups/{id}/members` | Add users: `{ "user_ids": ["..."] }` |
| `DELETE` | `/groups/{id}/members/{userId}` | Remove a member |
| `GET` | `/groups/{id}/roles` | List roles assigned to the group |
| `POST` | `/groups/{id}/roles` | Assign role: `{ "role_id": "..." }` |
| `DELETE` | `/groups/{id}/roles/{roleId}` | Remove role assignment from group |

---

### 5.5 Roles (`/roles`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/roles` | List roles; filter by `is_system`, `status` |
| `POST` | `/roles` | Create role |
| `GET` | `/roles/{id}` | Get role with permission list |
| `PATCH` | `/roles/{id}` | Update `name`, `description`, `is_assignable` |
| `DELETE` | `/roles/{id}` | Deprecate role; reject if currently assigned |
| `GET` | `/roles/{id}/permissions` | List permissions granted to role |
| `POST` | `/roles/{id}/permissions` | Grant permission: `{ "permission_id": "..." }` |
| `DELETE` | `/roles/{id}/permissions/{permId}` | Revoke permission from role |

---

### 5.6 Permissions (`/permissions`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/permissions` | List permissions; filter by `resource_type`, `action` |
| `POST` | `/permissions` | Create permission: `{ "action": "documents:read", "resource_type": "document" }` |
| `GET` | `/permissions/{id}` | Get permission |
| `PATCH` | `/permissions/{id}` | Update `description` |
| `DELETE` | `/permissions/{id}` | Delete permission; rejected if assigned to any role |

---

### 5.7 Policies (`/policies`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/policies` | List policies; filter by `status`, `policy_type` |
| `POST` | `/policies` | Create policy draft |
| `GET` | `/policies/{id}` | Get policy with statements |
| `PATCH` | `/policies/{id}` | Update `name`, `description`, `tags` (draft only) |
| `DELETE` | `/policies/{id}` | Delete policy (draft status only) |
| `POST` | `/policies/{id}/activate` | Transition `approved → active` |
| `POST` | `/policies/{id}/deactivate` | Transition `active → deprecated` |
| `POST` | `/policies/{id}/simulate` | Dry-run evaluation against a test context |
| `GET` | `/policies/{id}/statements` | List statements |
| `POST` | `/policies/{id}/statements` | Add statement to policy |

**Simulate request:**
```json
{
  "subject": { "user_id": "...", "roles": ["viewer"] },
  "action": "documents:delete",
  "resource": { "type": "document", "id": "doc-123", "owner": "alice" },
  "environment": { "ip": "203.0.113.5", "time": "2025-01-15T14:00:00Z" }
}
```

**Simulate response `200 OK`:**
```json
{
  "decision": "Deny",
  "matched_statements": ["stmt_8a7b6c5d-..."],
  "reason": "Explicit Deny on documents:delete for resource type document",
  "obligations": [],
  "evaluation_time_ms": 3
}
```

---

### 5.8 Sessions (`/sessions`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/sessions` | List active sessions; filter by `principal_id`, `status`, `ip_address` |
| `GET` | `/sessions/{id}` | Get session details |
| `DELETE` | `/sessions/{id}` | Terminate session and revoke its token family |
| `POST` | `/sessions/revoke-all` | Revoke all sessions for a given `user_id` |

---

### 5.9 Tokens (`/tokens`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/tokens/{id}` | Get token metadata by `token_id` |
| `DELETE` | `/tokens/{id}` | Revoke a specific token |
| `POST` | `/tokens/introspect` | RFC 7662 token introspection |

**Introspect request:** `application/x-www-form-urlencoded`: `token=<value>&token_type_hint=access_token`

**Introspect response `200 OK`:**
```json
{
  "active": true,
  "sub": "3fa85f64-...",
  "iss": "https://api.iam-platform.example.com",
  "aud": "https://app.example.com",
  "exp": 1736938200,
  "iat": 1736937600,
  "scope": "openid profile email",
  "client_id": "sa_a1b2c3d4",
  "tenant_id": "t_abc123"
}
```

---

### 5.10 MFA (`/mfa`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/mfa/devices` | List enrolled MFA devices for the current user |
| `DELETE` | `/mfa/devices/{id}` | Remove an MFA device; requires step-up MFA |
| `POST` | `/mfa/totp/enroll/begin` | Begin TOTP enrollment; returns `secret`, `qr_code_uri` |
| `POST` | `/mfa/totp/enroll/complete` | Complete TOTP enrollment: `{ "code": "123456", "enrollment_id": "..." }` |
| `POST` | `/mfa/webauthn/register/begin` | Begin WebAuthn credential registration; returns `PublicKeyCredentialCreationOptions` |
| `POST` | `/mfa/webauthn/register/complete` | Submit `AuthenticatorAttestationResponse` |
| `POST` | `/mfa/webauthn/authenticate/begin` | Begin WebAuthn assertion; returns `PublicKeyCredentialRequestOptions` |
| `POST` | `/mfa/webauthn/authenticate/complete` | Submit `AuthenticatorAssertionResponse` |

---

### 5.11 OAuth 2.0 / OIDC (`/oauth`)

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/oauth/authorize` | None | Authorization endpoint (RFC 6749 §3.1) |
| `POST` | `/oauth/token` | Client credentials | Token endpoint (RFC 6749 §3.2) |
| `POST` | `/oauth/revoke` | Client credentials | RFC 7009 token revocation |
| `GET` | `/oauth/userinfo` | Bearer | OIDC UserInfo endpoint |
| `GET` | `/.well-known/openid-configuration` | None | OIDC discovery document |
| `GET` | `/.well-known/jwks.json` | None | JSON Web Key Set |
| `GET` | `/oauth/clients` | Bearer | List OAuth clients |
| `POST` | `/oauth/clients` | Bearer | Register OAuth client |
| `GET` | `/oauth/clients/{id}` | Bearer | Get client details |
| `PATCH` | `/oauth/clients/{id}` | Bearer | Update client configuration |
| `DELETE` | `/oauth/clients/{id}` | Bearer | Delete client |
| `POST` | `/oauth/clients/{id}/rotate-secret` | Bearer | Rotate client secret |

**Token endpoint grant types:** `authorization_code`, `client_credentials`, `refresh_token`, `urn:ietf:params:oauth:grant-type:jwt-bearer`

---

### 5.12 SAML 2.0 (`/saml`)

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/saml/metadata` | None | SP metadata (XML) |
| `GET` | `/saml/sso/{providerId}` | None | SP-initiated SSO redirect |
| `POST` | `/saml/acs/{providerId}` | None | Assertion Consumer Service |
| `GET` | `/saml/providers` | Bearer | List SAML IdP configurations |
| `POST` | `/saml/providers` | Bearer | Create SAML IdP configuration |
| `GET` | `/saml/providers/{id}` | Bearer | Get provider details |
| `PATCH` | `/saml/providers/{id}` | Bearer | Update provider configuration |
| `DELETE` | `/saml/providers/{id}` | Bearer | Delete provider |
| `POST` | `/saml/providers/{id}/test` | Bearer | Test connectivity: validates metadata, certificate, and SSO URL reachability |

---

### 5.13 SCIM 2.0 (`/scim/v2`)

Implements [RFC 7644](https://www.rfc-editor.org/rfc/rfc7644). Bearer token auth via `Authorization: Bearer <scim_token>`.

| Method | Path | Description |
|---|---|---|
| `GET` | `/scim/v2/Users` | List/filter users (supports `filter`, `startIndex`, `count`) |
| `POST` | `/scim/v2/Users` | Provision user |
| `GET` | `/scim/v2/Users/{id}` | Get user |
| `PUT` | `/scim/v2/Users/{id}` | Replace user |
| `PATCH` | `/scim/v2/Users/{id}` | Partial update (RFC 7396 patch ops) |
| `DELETE` | `/scim/v2/Users/{id}` | Deprovision user |
| `GET` | `/scim/v2/Groups` | List groups |
| `POST` | `/scim/v2/Groups` | Create group |
| `GET` | `/scim/v2/Groups/{id}` | Get group |
| `PUT` | `/scim/v2/Groups/{id}` | Replace group |
| `PATCH` | `/scim/v2/Groups/{id}` | Partial update |
| `DELETE` | `/scim/v2/Groups/{id}` | Delete group |
| `GET` | `/scim/v2/Schemas` | List supported SCIM schemas |
| `GET` | `/scim/v2/ResourceTypes` | List resource types |
| `GET` | `/scim/v2/ServiceProviderConfig` | Service provider capabilities |

---

### 5.14 Audit Logs (`/audit-logs`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/audit-logs` | List audit events |
| `GET` | `/audit-logs/{id}` | Get single audit event |
| `POST` | `/audit-logs/export` | Trigger async export to S3/GCS |

**Audit log query params:** `actor_id`, `action`, `target_type`, `target_id`, `outcome`, `from` (ISO 8601), `to` (ISO 8601), `after`, `limit`

**Export request:**
```json
{
  "from": "2025-01-01T00:00:00Z",
  "to": "2025-01-31T23:59:59Z",
  "format": "ndjson",
  "destination": "s3://my-audit-bucket/exports/"
}
```

**Export response `202 Accepted`:**
```json
{ "export_id": "exp_abc123", "status": "pending", "estimated_rows": 142000 }
```

---

## 6. Error Codes

| Code | HTTP Status | Description | Retryable |
|---|---|---|---|
| `AUTH_001` | 401 | Missing or malformed Authorization header | No |
| `AUTH_002` | 401 | Access token expired | No |
| `AUTH_003` | 401 | Access token signature invalid | No |
| `AUTH_004` | 401 | Token audience mismatch | No |
| `AUTH_005` | 401 | Refresh token invalid or already used | No |
| `AUTH_006` | 401 | Refresh token expired | No |
| `AUTH_007` | 401 | Token family revoked (reuse detected) | No |
| `AUTH_008` | 401 | Session revoked or terminated | No |
| `AUTH_009` | 401 | Session expired | No |
| `AUTH_010` | 401 | Invalid credentials | No |
| `AUTH_011` | 401 | Account locked; retry after locked_until | Yes (after delay) |
| `AUTH_012` | 403 | MFA verification required (step-up) | No |
| `AUTH_013` | 403 | MFA challenge expired | No |
| `AUTH_014` | 403 | MFA code invalid | No |
| `AUTH_015` | 403 | Account suspended | No |
| `AUTH_016` | 403 | Account deprovisioned | No |
| `AUTH_017` | 403 | IP address not in allowlist | No |
| `AUTH_018` | 403 | Login denied by risk policy | No |
| `AUTH_019` | 429 | Login rate limit exceeded | Yes |
| `AUTH_020` | 503 | Identity provider unavailable | Yes |
| `AUTHZ_001` | 403 | Insufficient permissions | No |
| `AUTHZ_002` | 403 | Policy explicit deny | No |
| `AUTHZ_003` | 403 | Policy indeterminate (fail closed) | No |
| `AUTHZ_004` | 403 | Tenant scope violation | No |
| `AUTHZ_005` | 403 | Action requires break-glass session | No |
| `AUTHZ_006` | 403 | Resource ownership check failed | No |
| `AUTHZ_007` | 403 | Role assignment limit reached | No |
| `AUTHZ_008` | 403 | Conflicting policy constraint | No |
| `AUTHZ_009` | 403 | Assurance level insufficient | No |
| `AUTHZ_010` | 403 | OAuth scope insufficient | No |
| `AUTHZ_011` | 403 | Client not authorized for grant type | No |
| `AUTHZ_012` | 403 | Redirect URI not registered | No |
| `AUTHZ_013` | 403 | PKCE verification failed | No |
| `AUTHZ_014` | 403 | OAuth state mismatch | No |
| `AUTHZ_015` | 403 | SAML audience restriction failed | No |
| `AUTHZ_016` | 403 | SAML assertion replay detected | No |
| `AUTHZ_017` | 403 | SAML signature verification failed | No |
| `AUTHZ_018` | 403 | SAML assertion expired | No |
| `AUTHZ_019` | 403 | Federation trust disabled | No |
| `AUTHZ_020` | 403 | Break-glass session terminated | No |
| `USER_001` | 404 | User not found | No |
| `USER_002` | 409 | Email already registered in tenant | No |
| `USER_003` | 409 | External ID conflict | No |
| `USER_004` | 422 | Invalid email format | No |
| `USER_005` | 422 | Invalid status transition | No |
| `USER_006` | 422 | Cannot deprovision user with active sessions; use force=true | No |
| `USER_007` | 422 | System user cannot be modified | No |
| `USER_008` | 409 | Role already assigned | No |
| `USER_009` | 422 | Role assignment expired or invalid | No |
| `USER_010` | 422 | MFA device limit reached | No |
| `SCIM_001` | 400 | Unsupported SCIM filter | No |
| `SCIM_002` | 400 | Invalid SCIM patch operation | No |
| `SCIM_003` | 409 | SCIM uniqueness constraint violated | No |
| `SCIM_004` | 404 | SCIM resource not found | No |
| `SCIM_005` | 400 | SCIM schema validation failed | No |
| `SCIM_006` | 403 | SCIM bearer token invalid | No |
| `SCIM_007` | 503 | SCIM directory sync in progress | Yes |
| `SCIM_008` | 422 | Required SCIM attribute missing | No |
| `SCIM_009` | 409 | SCIM Group already exists | No |
| `SCIM_010` | 429 | SCIM rate limit exceeded | Yes |
| `POLICY_001` | 404 | Policy not found | No |
| `POLICY_002` | 409 | Policy name already exists in tenant | No |
| `POLICY_003` | 422 | Invalid policy statement JSON | No |
| `POLICY_004` | 422 | Policy must be in draft status to modify | No |
| `POLICY_005` | 422 | Policy must be approved before activation | No |
| `POLICY_006` | 422 | Cannot delete active or approved policy | No |
| `POLICY_007` | 409 | Policy version conflict (optimistic lock) | Yes |
| `POLICY_008` | 422 | Simulation context invalid | No |
| `POLICY_009` | 422 | Circular policy dependency detected | No |
| `POLICY_010` | 422 | Policy statement has conflicting principals | No |

---

## 7. Rate Limiting

Rate limits are applied per `(tenant_id, client_ip)` and enforced at the API gateway using a sliding window algorithm. Limits below represent the default tier; enterprise tenants may have elevated limits configured via tenant settings.

| Endpoint Group | Limit | Window | Burst |
|---|---|---|---|
| `POST /auth/login` | 10 requests | 60 seconds | 3 |
| `POST /auth/refresh` | 60 requests | 60 seconds | 10 |
| `POST /auth/mfa/verify` | 5 requests | 60 seconds | 0 |
| `POST /oauth/token` | 120 requests | 60 seconds | 20 |
| `POST /tokens/introspect` | 1000 requests | 60 seconds | 100 |
| `GET /users`, `GET /roles`, `GET /groups` (list) | 120 requests | 60 seconds | 20 |
| Write operations (POST/PATCH/DELETE) | 60 requests | 60 seconds | 10 |
| `GET /audit-logs` | 30 requests | 60 seconds | 5 |
| `POST /audit-logs/export` | 3 requests | 3600 seconds | 1 |
| SCIM endpoints | 300 requests | 60 seconds | 50 |
| `GET /.well-known/*` | 600 requests | 60 seconds | 100 |

When a rate limit is exceeded the API returns `429 Too Many Requests` with the `Retry-After` header set to the number of seconds until the window resets.
