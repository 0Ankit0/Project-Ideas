# Use-Case Descriptions — API Gateway and Developer Portal

This document provides fully detailed use-case descriptions for the twelve most critical use cases across all ten core domains of the API Gateway and Developer Portal system. Each description follows a structured template covering actors, preconditions, main scenario, alternative flows, and exception flows. Cross-references to the use-case inventory in `use-case-diagram.md` are provided via UC identifiers.

---

## Domain 1 — Developer Portal

### UC-001: Register Developer Account

| Field | Value |
|-------|-------|
| Use Case ID | UC-001 |
| Name | Register Developer Account |
| Primary Actor | Developer |
| Secondary Actors | Email Service (AWS SES), Developer Portal Backend (Next.js API Route) |
| Preconditions | The developer has a valid email address not previously registered on the platform. The developer portal is accessible and the registration endpoint returns HTTP 200 on health check. |
| Postconditions | A new developer account record is created in the `developers` PostgreSQL table with `status = pending_verification`. A verification email is dispatched. No API keys or applications are created at this stage. |
| Trigger | Developer navigates to `/register` on the portal and submits the registration form. |

**Main Success Scenario:**

1. Developer opens the developer portal at `https://portal.example.com/register`.
2. Developer enters first name, last name, email address, password (min 12 characters), and accepts the Terms of Service checkbox.
3. The portal frontend validates all fields client-side: email format via RFC 5322 regex, password strength score ≥ 3 via zxcvbn, ToS checkbox checked.
4. Developer clicks **Create Account**.
5. The Next.js API route `POST /api/auth/register` receives the payload over TLS.
6. The backend checks the `developers` table for an existing record with the submitted email; none is found.
7. The backend hashes the password using bcrypt with a cost factor of 12.
8. A new row is inserted into `developers` with `id = uuid_generate_v4()`, `email`, `password_hash`, `status = pending_verification`, `created_at = NOW()`.
9. A time-limited (24-hour) HMAC-SHA256 verification token is generated and stored in Redis with key `email:verify:{token}` → `developer_id`.
10. The backend calls AWS SES `SendEmail` with the verification link `https://portal.example.com/verify-email?token={token}`.
11. The portal responds with HTTP 201 and displays a "Check your inbox" confirmation page.

**Alternative Flows:**

- **A1 — SSO Registration via OAuth:** If the developer clicks "Sign up with GitHub" or "Sign up with Google", the flow redirects to UC-039 (Initiate OAuth Authorization Code Flow). Upon successful OAuth callback, an account is created with `auth_provider = 'github'|'google'` and `status = active` (email pre-verified by the OAuth provider).
- **A2 — Invitation-Based Registration:** If the developer arrives via an Admin-issued invitation link containing a pre-validated `invite_token`, the email field is pre-populated and read-only. Steps 6–8 execute normally, but `status` is set to `active` immediately (no verification email required) and the invitation token is consumed.

**Exception Flows:**

- **E1 — Duplicate Email:** At step 6, if a record with the submitted email already exists, the API returns HTTP 409 with error code `ERR_EMAIL_ALREADY_REGISTERED`. The portal displays "An account with this email address already exists. Try signing in."
- **E2 — Email Dispatch Failure:** If the AWS SES call at step 10 fails, the account row is still committed (idempotent retry safety), but the portal displays a warning: "Account created but we couldn't send the verification email. Use the resend link below." A background BullMQ job is enqueued for a retry with exponential back-off.
- **E3 — Weak Password:** If client-side validation passes but server-side validation (zxcvbn score < 3) detects a weak password, the API returns HTTP 422 with field-level error `password: too_weak`.

---

### UC-003: Create Application

| Field | Value |
|-------|-------|
| Use Case ID | UC-003 |
| Name | Create Application |
| Primary Actor | Developer |
| Secondary Actors | Developer Portal Backend, PostgreSQL |
| Preconditions | Developer is authenticated (active session JWT or OAuth access token). Developer's account `status = active` (email verified). Developer has not exceeded the maximum application limit for their account tier (Free: 1, Pro: 10, Enterprise: unlimited). |
| Postconditions | A new `applications` record is created in PostgreSQL with a system-assigned `app_id` (UUID). The application appears in the developer's application dashboard. No API keys are generated at this stage. |
| Trigger | Developer navigates to **My Apps → New Application** in the developer portal and submits the creation form. |

**Main Success Scenario:**

1. Developer clicks **New Application** on the portal dashboard.
2. Portal renders the application creation form requesting: Application Name (required, 3–64 chars), Description (optional, max 500 chars), Allowed Origins (optional CORS whitelist), Environment (Sandbox / Production).
3. Developer fills in the form and clicks **Create Application**.
4. `POST /api/apps` is called with the form payload and the developer's session token in the `Authorization: Bearer` header.
5. The API route authenticates the session, extracts `developer_id` from the JWT payload.
6. The backend validates the application name for uniqueness within the developer's account scope.
7. A new row is inserted into `applications`: `app_id = uuid_generate_v4()`, `developer_id`, `name`, `description`, `environment`, `allowed_origins`, `status = active`, `created_at = NOW()`.
8. An audit event `APP_CREATED` is written to the `audit_log` table with `actor_id`, `app_id`, and `timestamp`.
9. The API returns HTTP 201 with the new `app_id` and application details.
10. The portal redirects the developer to the application detail page showing the empty API keys panel with a **Generate Key** button.

**Alternative Flows:**

- **A1 — Sandbox vs. Production Environment:** If the developer selects Sandbox, the application is bound to the sandbox gateway cluster with relaxed rate limits and no billing. Sandbox apps cannot be promoted to Production directly; a new Production application must be created separately.

**Exception Flows:**

- **E1 — Application Limit Reached:** If the developer already has the maximum number of applications for their plan, the API returns HTTP 403 with `ERR_APP_LIMIT_EXCEEDED` and a prompt to upgrade the plan.
- **E2 — Duplicate Name:** If an application with the same name already exists in the developer's account, the API returns HTTP 409 with `ERR_APP_NAME_DUPLICATE`.

---

## Domain 2 — Authentication & Authorization

### UC-013: Authenticate via API Key (HMAC-SHA256)

| Field | Value |
|-------|-------|
| Use Case ID | UC-013 |
| Name | Authenticate via API Key (HMAC-SHA256) |
| Primary Actor | External Client |
| Secondary Actors | Gateway Auth Plugin (Fastify), Redis 7, PostgreSQL |
| Preconditions | The External Client holds a valid API key issued to an active application. The API key's associated subscription is active and not suspended. The gateway is running and the Redis auth-cache is reachable. |
| Postconditions | The request is marked as authenticated with `developer_id`, `app_id`, `plan_id`, and `scopes` injected into the Fastify request context for downstream plugins. A cache hit is recorded in Redis with TTL refresh. |
| Trigger | External Client includes an `X-API-Key: {key}` header (or `Authorization: ApiKey {key}`) in an HTTP request to a gateway-protected endpoint. |

**Main Success Scenario:**

1. Fastify gateway receives the inbound HTTP request and invokes the authentication plugin as the first lifecycle hook (`onRequest`).
2. The auth plugin extracts the API key from the `X-API-Key` header or `Authorization: ApiKey` scheme.
3. The plugin computes the SHA-256 hash of the submitted key.
4. The plugin performs a Redis `GET` lookup on key `auth:apikey:{hash}` to check the warm cache.
5. Cache hit: the plugin deserializes the cached JSON payload containing `developer_id`, `app_id`, `plan_id`, `scopes`, `status`, `rate_limit_tier`.
6. The plugin verifies `status = active`. If active, it injects the identity context into `request.authContext` and calls `next()`.
7. The plugin emits an OpenTelemetry span `auth.apikey.validate` with `cache_hit = true`, `developer_id`, and `app_id` as span attributes.
8. Downstream plugins (rate limiter, quota enforcer, transformer) read `request.authContext` to apply per-developer policies.

**Alternative Flows:**

- **A1 — Cache Miss:** At step 4, if no cache entry exists, the plugin queries `SELECT * FROM api_keys WHERE key_hash = $1 AND status = 'active'` in PostgreSQL. On a successful row return, the plugin serializes the identity payload and writes it to Redis with `SET auth:apikey:{hash} {payload} EX 300` (5-minute TTL). Execution continues from step 6.
- **A2 — HMAC Request Signing:** For routes configured to require HMAC request signing, the plugin additionally validates an `X-Signature: hmac-sha256={signature}` header by recomputing `HMAC-SHA256(secret_key, method + path + timestamp + body_hash)` and comparing with constant-time comparison to prevent timing attacks.

**Exception Flows:**

- **E1 — Key Not Found:** If neither the Redis cache nor the PostgreSQL lookup finds a matching active key, the plugin returns HTTP 401 with `WWW-Authenticate: ApiKey` and body `{"error": "invalid_api_key"}`. The failed attempt is logged to `auth_failures` with IP, timestamp, and key prefix.
- **E2 — Key Suspended:** If the key exists but `status = suspended`, the plugin returns HTTP 403 with `{"error": "api_key_suspended", "contact": "support@example.com"}`.
- **E3 — Redis Unavailable:** If the Redis lookup times out (> 50 ms), the plugin falls back to the PostgreSQL lookup. If PostgreSQL is also unavailable, the plugin returns HTTP 503 with `{"error": "auth_service_unavailable"}` and fires a PagerDuty alert via the alerting pipeline.

---

### UC-014: Authenticate via OAuth 2.0 Access Token

| Field | Value |
|-------|-------|
| Use Case ID | UC-014 |
| Name | Authenticate via OAuth 2.0 Access Token |
| Primary Actor | External Client |
| Secondary Actors | Gateway Auth Plugin, OAuth Provider (external OIDC), Redis Token Cache, PostgreSQL |
| Preconditions | The External Client has previously completed the OAuth 2.0 Authorization Code + PKCE flow (UC-039/UC-040) and holds a valid access token. The OAuth provider's JWKS endpoint is reachable or keys are cached. The gateway route is configured to accept the `oauth2` authentication scheme. |
| Postconditions | The request is authenticated. `developer_id`, `app_id`, `scopes`, and `sub` (OAuth subject) are injected into `request.authContext`. Token expiry is checked. |
| Trigger | External Client includes `Authorization: Bearer {access_token}` in the HTTP request to a gateway endpoint configured for OAuth 2.0 authentication. |

**Main Success Scenario:**

1. The Fastify auth plugin receives the `Authorization: Bearer {token}` header.
2. The plugin identifies the token type as OAuth 2.0 JWT by checking the `typ` and `iss` claims in the decoded (not yet verified) header.
3. The plugin fetches the OAuth provider's JWKS from a local Redis cache (`jwks:{issuer}`) to avoid network latency.
4. The plugin verifies the token signature using the matching `kid` from the JWKS, the `RS256` algorithm, expected `aud` (gateway client ID), and `exp` claim.
5. Token is valid and not expired. The plugin extracts `sub`, `scope`, `developer_id` (custom claim injected by the authorization server), and `app_id`.
6. The plugin checks the Redis denylist `SET oauth:revoked:{jti}` to confirm the token has not been revoked.
7. The plugin injects the parsed claims into `request.authContext` and calls `next()`.
8. An OpenTelemetry span `auth.oauth2.validate` is emitted with `sub`, `iss`, `scope`, and `jti` attributes.

**Alternative Flows:**

- **A1 — JWKS Cache Miss:** If the JWKS is not cached in Redis, the plugin makes an HTTP GET to `{issuer}/.well-known/jwks.json`, caches the response with a 1-hour TTL, and proceeds with verification.
- **A2 — Token Introspection Mode:** For opaque (non-JWT) access tokens, the plugin calls the OAuth provider's `POST /introspect` endpoint with `client_credentials` and validates the returned `active: true` response. Result is cached per token hash with TTL equal to `expires_in` minus 60 seconds.

**Exception Flows:**

- **E1 — Expired Token:** If `exp` is in the past, the plugin returns HTTP 401 with `{"error": "token_expired", "error_description": "Access token has expired. Obtain a new token using the refresh token."}`.
- **E2 — Invalid Signature:** If the signature verification fails, the plugin returns HTTP 401 with `{"error": "invalid_token"}`. The event is written to the security audit log with `severity = HIGH`.
- **E3 — Revoked Token:** If the `jti` is found in the denylist, the plugin returns HTTP 401 with `{"error": "token_revoked"}`.
- **E4 — Insufficient Scope:** If the token's `scope` claim does not include the scope required by the target route's configuration, the plugin returns HTTP 403 with `{"error": "insufficient_scope", "required_scope": "{route_scope}"}`.

---

## Domain 3 — Rate Limiting & Quotas

### UC-016: Enforce Rate Limit (Per-Second / Per-Minute Window)

| Field | Value |
|-------|-------|
| Use Case ID | UC-016 |
| Name | Enforce Rate Limit (Sliding Window) |
| Primary Actor | Gateway Core (Fastify Rate Limit Plugin) |
| Secondary Actors | Redis 7 (sliding window counters), Developer (receives 429 response) |
| Preconditions | The inbound request has passed authentication (UC-013/014/015) and `request.authContext` contains `plan_id`, `developer_id`, and `app_id`. The route has a rate-limit policy configured in the gateway route registry. |
| Postconditions | If within limit: `X-RateLimit-Remaining` and `X-RateLimit-Reset` headers are set on the response. If exceeded: HTTP 429 is returned immediately. Redis counters are atomically incremented. |
| Trigger | The Fastify `preHandler` hook invokes the rate-limit plugin for every authenticated inbound request. |

**Main Success Scenario:**

1. The rate-limit plugin reads `plan_id` from `request.authContext`.
2. The plugin fetches the rate-limit policy for `plan_id` from the in-memory plan cache (refreshed every 60 seconds from PostgreSQL): `{ requests_per_second: 10, requests_per_minute: 300, burst_multiplier: 1.5 }`.
3. The plugin constructs two Redis keys: `rl:s:{developer_id}:{route_id}:{unix_second}` and `rl:m:{developer_id}:{route_id}:{unix_minute}`.
4. A Lua script executes atomically on Redis:
   - `INCR` the per-second key; set `EXPIRE` to 2 seconds if the key is new.
   - `INCR` the per-minute key; set `EXPIRE` to 120 seconds if the key is new.
   - Return both counter values.
5. If per-second counter ≤ 10 AND per-minute counter ≤ 300: the plugin sets `X-RateLimit-Limit: 10`, `X-RateLimit-Remaining: {10 - counter}`, `X-RateLimit-Reset: {unix_second + 1}` headers on the request object and calls `next()`.
6. Downstream processing continues (quota check → transformation → routing).

**Alternative Flows:**

- **A1 — Burst Allowance:** If the per-second counter exceeds the base limit but is within `base_limit × burst_multiplier` (i.e., ≤ 15 for a 10 rps plan), the request is allowed but tagged `request.burstUsed = true`. The response includes `X-RateLimit-Burst: true`.
- **A2 — IP-Level Global Limit:** For unauthenticated or pre-authentication requests caught at the edge (WAF/CloudFront), a global IP rate limit of 100 req/min applies via AWS WAF rate-based rules, independent of the per-developer Redis counters.

**Exception Flows:**

- **E1 — Rate Limit Exceeded:** If either counter exceeds its configured limit (factoring in burst), the plugin immediately returns HTTP 429 with headers: `Retry-After: {seconds_until_reset}`, `X-RateLimit-Limit: {limit}`, `X-RateLimit-Remaining: 0`, and body `{"error": "rate_limit_exceeded", "retry_after": {seconds}}`. The request is not forwarded to upstream. An increment is made to the `rate_limit_violations` counter in the analytics pipeline.
- **E2 — Redis Timeout:** If the Lua script execution times out (> 20 ms), the plugin applies a fail-open policy: the request is allowed to proceed, a warning span attribute `rate_limit_enforced: false` is set on the OTel trace, and a Redis connectivity alert fires if the timeout rate exceeds 1% of requests in a 1-minute window.

---

## Domain 4 — Request/Response Transformation

### UC-018: Transform Inbound Request Payload

| Field | Value |
|-------|-------|
| Use Case ID | UC-018 |
| Name | Transform Inbound Request Payload |
| Primary Actor | Gateway Core (Fastify Transform Plugin) |
| Secondary Actors | API Provider (defines transformation rules), Upstream Service (receives transformed request) |
| Preconditions | The request has been authenticated and rate-limit checks have passed. The route configuration in PostgreSQL includes one or more transformation rules of types: header injection, header removal, body field mapping, query-string normalization, or schema validation. |
| Postconditions | The upstream receives a transformed HTTP request conforming to its expected contract. The original client request headers (e.g., client IP, raw API key) that must not leak to upstream are removed. Injected headers such as `X-Consumer-ID`, `X-Plan-ID`, and `X-Request-ID` are present. |
| Trigger | The Fastify `preHandler` hook invokes the transformation plugin after authentication and rate-limit plugins have successfully resolved. |

**Main Success Scenario:**

1. The transformation plugin reads the route's `transformation_rules` JSON array from the cached route configuration (PostgreSQL, refreshed via cache-aside pattern in Redis).
2. **Header removal:** The plugin strips the following headers to prevent upstream leakage: `X-API-Key`, `Authorization`, `X-Forwarded-Client-Cert`.
3. **Header injection:** The plugin injects: `X-Consumer-ID: {developer_id}`, `X-App-ID: {app_id}`, `X-Plan-ID: {plan_id}`, `X-Request-ID: {uuid}` (or passes through existing `X-Request-ID` if present), `X-Forwarded-For: {client_ip}`.
4. **Query-string normalization:** Any API-key query parameters (`?api_key=`, `?apiKey=`) are removed from the URL before forwarding to prevent key leakage in upstream access logs.
5. **Body transformation (if configured):** For routes with `body_transform` rules, the plugin parses the JSON request body, applies JSONata expressions or a field-mapping DSL stored in the route config, and re-serializes the transformed body. The `Content-Length` header is updated to reflect the new body size.
6. **Schema validation (if configured):** The plugin validates the transformed body against the route's JSON Schema definition. Validation errors are collected and returned as HTTP 422 before the request is forwarded.
7. The plugin calls `next()` and the routing plugin dispatches the transformed request to the upstream service.

**Alternative Flows:**

- **A1 — Pass-Through Mode:** Routes with `transformation_rules: []` skip steps 2–6 for body transformation but always execute the header strip/inject steps (steps 2–4) for security reasons regardless of configuration.
- **A2 — XML to JSON Conversion:** Routes configured with `content_type_transform: xml_to_json` use the `fast-xml-parser` library to convert the request body and set `Content-Type: application/json` before forwarding.

**Exception Flows:**

- **E1 — Schema Validation Failure:** If body schema validation at step 6 fails, the plugin returns HTTP 422 with a structured error body: `{"error": "validation_failed", "details": [{field, message}]}`. The upstream is never contacted. The validation failure is counted in the per-route error metrics.
- **E2 — JSONata Expression Error:** If a configured body transformation expression throws a runtime error, the plugin logs the error at `WARN` level, skips the failing transformation step, and proceeds with the partially transformed request. An alert fires if this occurs for more than 5% of requests in a 5-minute window.

---

## Domain 5 — Subscription Plans

### UC-007: Subscribe to API Plan

| Field | Value |
|-------|-------|
| Use Case ID | UC-007 |
| Name | Subscribe to API Plan |
| Primary Actor | Developer |
| Secondary Actors | Developer Portal Backend, PostgreSQL, Billing Service (Stripe), Gateway Config Service |
| Preconditions | Developer is authenticated with an active account. Developer has at least one application created (UC-003). The target plan is active and visible in the plan catalog. If the target plan is paid, the developer has a valid payment method on file. |
| Postconditions | A `subscriptions` record is created in PostgreSQL linking `developer_id`, `app_id`, `plan_id`, and `billing_cycle_start`. The gateway's Redis rate-limit and quota cache is invalidated for the application. The developer can now generate an API key (UC-004). |
| Trigger | Developer selects a plan from the plan comparison page and clicks **Subscribe**. |

**Main Success Scenario:**

1. Developer navigates to **Plans** in the portal and reviews the plan comparison table (Free, Pro $49/month, Business $199/month, Enterprise — custom).
2. Developer selects the **Pro** plan and clicks **Subscribe to Pro**.
3. Portal displays a confirmation modal showing: plan features, monthly quota, rate limits, and billing amount.
4. Developer clicks **Confirm Subscription**.
5. `POST /api/subscriptions` is called with `{ app_id, plan_id }` in the body.
6. Backend verifies the developer owns the application and the application has no active subscription.
7. For paid plans: the backend calls Stripe `POST /v1/subscriptions` with the developer's `stripe_customer_id`, `plan_stripe_price_id`, and `trial_period_days: 14`.
8. Stripe returns a subscription object with `status = trialing` or `status = active`.
9. Backend inserts a row into `subscriptions`: `subscription_id = uuid_generate_v4()`, `developer_id`, `app_id`, `plan_id`, `stripe_subscription_id`, `status = active`, `billing_cycle_start = NOW()`, `quota_remaining = plan.monthly_quota`.
10. Backend publishes a `subscription.created` event to the BullMQ `gateway-config` queue.
11. The gateway config consumer invalidates `auth:apikey:*:{app_id}` and `quota:{app_id}` Redis keys, forcing a fresh policy load on the next request.
12. The portal redirects the developer to the application page with a success banner and an enabled **Generate API Key** button.

**Alternative Flows:**

- **A1 — Free Plan:** For the Free plan, steps 7–8 (Stripe calls) are skipped. The subscription is created with `stripe_subscription_id = null` and `status = active`.
- **A2 — Enterprise Plan:** Enterprise plans are not self-service. Selecting Enterprise opens a "Contact Sales" form. The subscription is created manually by an Admin after contract execution.

**Exception Flows:**

- **E1 — Payment Failure:** If Stripe returns a payment failure at step 7, the backend returns HTTP 402 with `{"error": "payment_required", "stripe_error": "{decline_code}"}`. No subscription record is created. The portal displays a payment failure modal with a link to update the payment method.
- **E2 — Duplicate Subscription:** If the application already has an active subscription, the API returns HTTP 409 with `ERR_ACTIVE_SUBSCRIPTION_EXISTS`. The developer is directed to the upgrade or downgrade flow instead.

---

## Domain 6 — Analytics & Observability

### UC-030: View Analytics Dashboard

| Field | Value |
|-------|-------|
| Use Case ID | UC-030 |
| Name | View Analytics Dashboard |
| Primary Actor | Analyst |
| Secondary Actors | Analytics Backend (Next.js API Route), TimescaleDB / Prometheus, Grafana Embedded Panels |
| Preconditions | Analyst is authenticated with the `analyst` or `admin` role. The analytics pipeline has been ingesting OpenTelemetry spans and request metrics from the gateway. At least one API route has received traffic in the selected time window. |
| Postconditions | The dashboard displays real-time and historical metrics. No data mutations occur. Dashboard state (selected filters, time range) is persisted in URL query parameters. |
| Trigger | Analyst navigates to `/admin/analytics` in the portal. |

**Main Success Scenario:**

1. Analyst logs into the portal with admin/analyst credentials.
2. Analyst navigates to **Analytics → Overview Dashboard**.
3. The portal makes authenticated `GET /api/analytics/overview?range=24h` requests to the analytics API.
4. The analytics API queries Prometheus with PromQL expressions:
   - `sum(rate(gateway_requests_total[5m]))` — requests per second
   - `histogram_quantile(0.99, gateway_request_duration_seconds_bucket)` — P99 latency
   - `sum(rate(gateway_errors_total[5m])) / sum(rate(gateway_requests_total[5m]))` — error rate
5. The API returns aggregated JSON metrics to the portal.
6. The portal renders summary cards: Total Requests, Success Rate, P50/P95/P99 Latency, Active API Keys, Top Consumers.
7. The portal embeds Grafana iframes for time-series charts (requests/sec by route, latency heatmap, error rate by upstream) using service-account tokens with read-only scope.
8. The Analyst can filter by: API route, plan tier, time range (1h, 6h, 24h, 7d, 30d, custom), developer, and status code group (2xx, 4xx, 5xx).
9. Filtered results update charts in real time via SWR polling every 30 seconds.

**Alternative Flows:**

- **A1 — Drill Down to Individual Developer:** Analyst clicks on a developer name in the "Top Consumers" widget, which navigates to a developer-scoped dashboard showing per-route usage, quota consumption, and error breakdown for that developer.
- **A2 — Jaeger Trace Lookup:** From the latency chart, the Analyst can click on a high-latency spike to open a Jaeger trace search pre-filtered to the relevant time window and route, enabling distributed trace inspection across gateway, auth service, and upstream.

**Exception Flows:**

- **E1 — Prometheus Unavailable:** If the Prometheus scrape endpoint is unreachable, the API returns cached metric snapshots from Redis with a staleness warning: `"metrics_stale_since": "{timestamp}"`. The Grafana panels display a "Data source error" state.
- **E2 — Insufficient Role:** If a Developer attempts to access the analytics endpoint, the API returns HTTP 403 with `{"error": "insufficient_role", "required": ["analyst", "admin"]}`.

---

## Domain 7 — Webhook Management

### UC-022: Register Webhook Endpoint

| Field | Value |
|-------|-------|
| Use Case ID | UC-022 |
| Name | Register Webhook Endpoint |
| Primary Actor | Developer |
| Secondary Actors | Developer Portal Backend, PostgreSQL, Gateway Webhook Plugin |
| Preconditions | Developer is authenticated. Developer has at least one active application. The webhook endpoint URL is reachable over HTTPS (verified by a test probe). The developer's plan permits webhook registration (Free tier: 0 webhooks, Pro: 5, Enterprise: unlimited). |
| Postconditions | A `webhooks` record is created in PostgreSQL. The gateway webhook dispatcher is aware of the new endpoint. A signing secret is generated and displayed once to the developer. |
| Trigger | Developer navigates to **My Apps → {App} → Webhooks → Add Webhook** and submits the registration form. |

**Main Success Scenario:**

1. Developer opens the webhook registration form for their application.
2. Developer enters: Endpoint URL (HTTPS required), a human-readable Description, and selects one or more Event Types from the checkbox list (e.g., `api.request.ratelimited`, `subscription.updated`, `api.version.deprecated`).
3. Developer clicks **Register Webhook**.
4. `POST /api/webhooks` is called with `{ app_id, url, description, events[] }`.
5. Backend validates the URL: HTTPS scheme required, no private IP ranges (RFC 1918), passes a DNS resolution check.
6. Backend performs a webhook verification probe: sends `POST {url}` with header `X-Webhook-Challenge: {random_32_byte_hex}` and expects a `200 OK` response with body `{"challenge": "{same_hex}"}` within 5 seconds.
7. Probe succeeds. Backend generates a 256-bit signing secret using `crypto.randomBytes(32)`.
8. A `webhooks` row is inserted: `webhook_id = uuid_generate_v4()`, `app_id`, `url`, `events`, `signing_secret_hash` (HMAC-SHA256 of the secret), `status = active`.
9. The plaintext signing secret is returned once in the HTTP 201 response: `{ webhook_id, signing_secret }`. It is never returned again.
10. The portal displays the secret in a one-time disclosure modal with instructions for verifying `X-Webhook-Signature` headers.

**Alternative Flows:**

- **A1 — Probe Timeout / Challenge Mismatch:** If the verification probe at step 6 times out or the challenge value does not match, the system skips probe failure and proceeds with registration but sets `status = unverified`. An orange warning badge is shown in the portal. Delivery attempts to unverified endpoints are made but failures do not trigger retries beyond the first attempt until the endpoint passes verification.

**Exception Flows:**

- **E1 — Private IP Rejected:** If URL resolution returns a private/loopback IP address, the API returns HTTP 422 with `{"error": "webhook_url_private_ip_rejected"}`. This prevents SSRF attacks.
- **E2 — Webhook Limit Reached:** If the developer has reached the plan's webhook limit, the API returns HTTP 403 with `ERR_WEBHOOK_LIMIT_EXCEEDED`.
- **E3 — Non-HTTPS URL:** The API immediately rejects non-HTTPS URLs with HTTP 422 and `{"error": "https_required"}`.

---

## Domain 8 — API Versioning

### UC-026: Publish New API Version

| Field | Value |
|-------|-------|
| Use Case ID | UC-026 |
| Name | Publish New API Version |
| Primary Actor | API Provider |
| Secondary Actors | Admin (approval), Gateway Config Service, PostgreSQL, Redis, BullMQ, Notification Service (SES) |
| Preconditions | API Provider is authenticated with the `api_provider` role. An existing API product record exists or is being created. The new version's OpenAPI 3.1 specification has been uploaded and passes automated linting (Spectral ruleset). The version string follows SemVer 2.0. |
| Postconditions | The new API version is registered in the `api_versions` table. A gateway route is created for the version prefix (e.g., `/v2/`). The version appears in the developer portal catalog. Existing subscribers to previous versions receive a migration notice if the new version introduces breaking changes. |
| Trigger | API Provider submits a new API version via `POST /api/admin/apis/{api_id}/versions` or through the Admin Console UI. |

**Main Success Scenario:**

1. API Provider navigates to **Admin Console → APIs → {API Product} → Versions → Publish New Version**.
2. API Provider enters: Version number (SemVer, e.g., `2.0.0`), Changelog notes (Markdown), Breaking Change flag (boolean), and uploads the OpenAPI 3.1 YAML/JSON specification file.
3. The portal uploads the spec to S3 (`s3://api-specs/{api_id}/v{version}/openapi.yaml`) and runs Spectral linting via a Lambda function.
4. Spectral returns zero errors (warnings are allowed but displayed). The spec passes validation.
5. `POST /api/admin/apis/{api_id}/versions` is called with `{ version, changelog, is_breaking, spec_s3_key, upstream_url, route_prefix }`.
6. A `pending_review` record is created in `api_versions`. For non-breaking minor/patch versions, the record auto-approves if no Admin approval gate is configured. For breaking (major) changes, the status is set to `pending_approval`.
7. Admin receives a notification in the Admin Console and approves the version.
8. The backend updates the version record to `status = active` and inserts a row into `gateway_routes`: `{ api_version_id, route_prefix: '/v2/', upstream_url, auth_schemes, rate_limit_policy_id, transformation_rules }`.
9. A `route.published` event is published to BullMQ, triggering the gateway config hot-reload consumer, which updates the in-memory route registry without restarting the Fastify process.
10. The new version appears in the developer portal API catalog with a "New" badge for 7 days.
11. If `is_breaking = true`, the notification service sends a migration advisory email to all active subscribers of the previous major version.

**Exception Flows:**

- **E1 — Spectral Lint Failure:** If Spectral reports errors at step 4, the upload is rejected with a structured error report listing rule violations. No version record is created.
- **E2 — Version Already Exists:** If a version with the same SemVer string already exists for the API product, the API returns HTTP 409 with `ERR_VERSION_ALREADY_EXISTS`.
- **E3 — Upstream URL Unreachable:** A connectivity health check is performed against `upstream_url`. If the health check fails after 3 attempts, the version is published with a `health_status = degraded` warning and an alert is raised.

---

## Domain 9 — Admin Console

### UC-033: Configure Rate Limit Policy

| Field | Value |
|-------|-------|
| Use Case ID | UC-033 |
| Name | Configure Rate Limit Policy |
| Primary Actor | Admin |
| Secondary Actors | Gateway Config Service, PostgreSQL, Redis, BullMQ |
| Preconditions | Admin is authenticated with the `admin` role. The target plan or route exists in the system. The Admin understands the downstream impact of the policy change on active developer traffic. |
| Postconditions | The new rate limit policy is persisted in PostgreSQL. Redis rate-limit policy caches are invalidated for all affected plan subscribers. The gateway applies the new limits on the next request cycle (within 60 seconds via cache TTL or immediate via forced invalidation). |
| Trigger | Admin navigates to **Admin Console → Policies → Rate Limits → Edit** and submits an updated policy configuration. |

**Main Success Scenario:**

1. Admin opens the rate-limit policy editor for the **Pro Plan** policy.
2. Admin reviews the current configuration: `{ requests_per_second: 10, requests_per_minute: 300, daily_limit: 50000, burst_multiplier: 1.5 }`.
3. Admin updates `requests_per_minute` to `500` and `daily_limit` to `100000` to reflect a plan tier upgrade decision.
4. Admin clicks **Save Policy**.
5. `PUT /api/admin/policies/rate-limits/{policy_id}` is called with the updated payload.
6. Backend validates the new values: all limits are positive integers, `requests_per_minute ≥ requests_per_second × 60` constraint is checked, no limit exceeds the platform maximum cap.
7. Backend updates the `rate_limit_policies` row in PostgreSQL inside a transaction.
8. Backend publishes a `policy.updated` event to BullMQ with `{ policy_id, affected_plan_ids[] }`.
9. The gateway config consumer processes the event and executes `SCAN + DEL` on Redis keys matching `rl:*:{plan_id}:*` and `plan_cache:{plan_id}` for all affected plans.
10. The gateway's in-memory plan cache TTL is set to expire immediately, forcing a fresh read from PostgreSQL on the next request.
11. Admin Console records an `ADMIN_POLICY_UPDATED` audit log entry with `actor_id`, `policy_id`, `before` snapshot, and `after` snapshot for compliance.
12. API returns HTTP 200. Admin sees a success toast: "Rate limit policy updated. Changes take effect within 60 seconds."

**Exception Flows:**

- **E1 — Constraint Violation:** If `requests_per_second > requests_per_minute / 60` (e.g., 100 rps but only 10/min), the API returns HTTP 422 with a specific constraint error message.
- **E2 — Insufficient Permissions:** If the requester does not hold the `admin` role, the API returns HTTP 403.
- **E3 — Policy In Use by Active Plans:** If the policy change would reduce limits below the current usage of any active developer, the Admin Console displays a warning (non-blocking) listing affected developers and their current usage levels before confirming the save.

---

## Domain 10 — Gateway Core

### UC-020: Route Request to Upstream Service

| Field | Value |
|-------|-------|
| Use Case ID | UC-020 |
| Name | Route Request to Upstream Service |
| Primary Actor | Gateway Core (Fastify Proxy Plugin) |
| Secondary Actors | Upstream Service, Redis (response cache), OpenTelemetry Collector |
| Preconditions | The request has passed authentication, rate limiting, quota enforcement, and request transformation. The route registry contains a valid upstream URL and health status for the target route. The upstream service is healthy according to the most recent health-check result. |
| Postconditions | The upstream response (potentially transformed) is returned to the External Client. OpenTelemetry trace spans are emitted. Usage counters are incremented in Redis. The response is conditionally cached. |
| Trigger | The Fastify proxy plugin (`fastify-reply-from`) receives a proxied request after all pre-handler hooks have resolved successfully. |

**Main Success Scenario:**

1. The proxy plugin reads `request.routeContext.upstream_url` set by the route-matching middleware.
2. The plugin constructs the upstream request: carries the transformed headers and body, sets `X-Request-ID` for end-to-end tracing, and sets a per-route upstream timeout (default: 30 seconds, configurable per route).
3. An OpenTelemetry child span `gateway.upstream.request` is started with `http.method`, `http.url`, `net.peer.name` span attributes.
4. The plugin dispatches the HTTP request to the upstream service using the Node.js `undici` client connection pool.
5. The upstream service processes the request and returns an HTTP response within the timeout window.
6. The proxy plugin receives the upstream response (status, headers, body).
7. The OTel span is closed with `http.status_code` and `http.response_content_length` attributes.
8. The response transformation plugin (UC-019) is invoked: strips internal headers (`X-Consumer-ID`, `X-Plan-ID`), maps upstream error codes to gateway standard error format, and injects `X-Request-ID` and `X-Powered-By` headers.
9. Redis counters are incremented: `INCRBY usage:{developer_id}:{year_month} 1` and `INCRBY usage:{route_id}:{year_month} 1`.
10. If the response status is 2xx and the route has `cache_enabled: true`, and the response includes a `Cache-Control: max-age={n}` header, the response body is stored in Redis: `SET cache:{route_id}:{request_hash} {body} EX {max-age}`.
11. The gateway returns the transformed response to the External Client.

**Alternative Flows:**

- **A1 — Cache Hit:** Before step 2, the proxy plugin computes a cache key `SHA256(method + path + sorted_query_string)` and performs a Redis `GET cache:{route_id}:{key}`. On a cache hit, the plugin returns the cached body with `X-Cache: HIT` and `Age: {seconds}` headers, skipping upstream dispatch entirely.
- **A2 — Load-Balanced Upstream:** For routes with multiple upstream targets, the plugin uses a weighted round-robin algorithm to select the target, respecting health-check state (unhealthy targets are excluded from rotation).

**Exception Flows:**

- **E1 — Upstream Timeout:** If the upstream does not respond within the configured timeout, the proxy plugin returns HTTP 504 with `{"error": "upstream_timeout", "timeout_ms": {configured_timeout}}`. The OTel span is closed with `error = true`. The upstream timeout is counted in the `gateway_upstream_errors_total{reason="timeout"}` Prometheus counter.
- **E2 — Upstream 5xx:** If the upstream returns a 5xx response, the gateway returns the upstream error code to the client (passthrough) but also records it in the `gateway_upstream_errors_total{status="5xx"}` counter. The response body is optionally mapped to a gateway-standard error format if `error_mapping: true` is set on the route.
- **E3 — Circuit Breaker Open:** If the upstream's failure rate exceeds 50% in a 30-second rolling window (tracked via Redis), the circuit breaker transitions to OPEN state and the gateway returns HTTP 503 with `{"error": "upstream_unavailable", "retry_after": 30}` without contacting the upstream, until the half-open probe succeeds.

---

## Operational Policy Addendum

### API Governance Policies

1. **API Publication Standard**: All APIs published through the portal must include an OpenAPI 3.1 specification with complete endpoint definitions, a changelog entry describing changes from the prior version, at least one working code sample per supported SDK language (JavaScript, Python, cURL), and a defined deprecation timeline. Routes are not made publicly visible in the catalog until all artefacts pass automated Spectral lint validation and receive Admin approval for major versions.
2. **Version Lifecycle Mandate**: API versions must remain active for a minimum of 12 months after a successor version is published. Deprecation notices must be sent to all active subscribers no fewer than 90 days before the sunset date, with follow-up reminders at the 60-day and 30-day marks. Emergency deprecations may occur within 7 days only for critical security vulnerabilities, with immediate notification.
3. **Breaking Change Classification**: Any modification that removes an endpoint, changes required request parameters, alters HTTP response status codes, removes or renames response fields, or alters authentication scheme requirements is classified as a breaking change requiring a new major version. Non-breaking additions (new optional fields, new endpoints) may be published as minor versions.
4. **Route Ownership Enforcement**: Each API route registered in the gateway must have exactly one designated API Provider owner. Routes without an assigned owner for more than 30 consecutive days are automatically flagged, placed in a read-only state, and escalated to the Admin team for reassignment or deactivation.
5. **Security Review Gate**: APIs that expose PII, financial transaction data, or PHI must pass a mandatory security review and receive explicit Admin approval before publication. Automated validation passing alone is not sufficient to publish such APIs.

### Developer Data Privacy Policies

1. **Minimal Data Collection**: The developer portal collects only the data necessary for account management, billing, and API access: email address, display name, payment details (tokenized via PCI-DSS-compliant processor), and per-request usage telemetry. No behavioral browsing data or third-party tracking scripts are permitted.
2. **API Key Storage Security**: All API keys are stored exclusively as HMAC-SHA256 hashes in PostgreSQL. The plaintext key is returned exactly once at generation time over TLS and is never stored, logged, or included in audit records. Only the first 8-character prefix is retained for identification.
3. **Log Anonymization Schedule**: Request logs written to the analytics pipeline must have IPv4 addresses truncated to a /24 CIDR block within 24 hours of ingestion. Full IP addresses are retained in raw access logs for a maximum of 7 days for security forensics exclusively.
4. **Right to Erasure**: Upon a verified account deletion request, all developer PII must be purged within 30 days. API call records are anonymized by replacing developer identifiers with a cryptographic tombstone UUID to preserve aggregate analytics integrity without retaining personal linkage.
5. **Cross-Border Data Restrictions**: Developer PII is stored exclusively in the primary AWS region designated at account creation. Replication to secondary regions is restricted to anonymized aggregate metrics unless the developer provides explicit cross-border consent.

### Monetization and Quota Policies

1. **Quota Reset Schedule**: API call quotas reset at 00:00 UTC on the first day of each calendar month for all subscription plans. Unused quota does not roll over to the following billing period under any plan tier.
2. **Overage Handling**: When a developer's monthly quota is exhausted, subsequent requests are rejected with HTTP 429 and a `Retry-After` header set to the ISO 8601 timestamp of the next quota reset. Overage blocks may be purchased in increments of 10,000 calls at the overage rate defined in the active plan.
3. **Plan Downgrade Restriction**: Subscription downgrades take effect at the end of the current billing cycle. Immediate downgrades are not permitted if current-month usage already exceeds the target plan's monthly quota.
4. **Free Tier Abuse Prevention**: Free tier accounts are limited to one application and one API key. Programmatic creation of multiple free-tier accounts by the same legal entity constitutes a ToS violation and will result in suspension of all associated accounts pending review.

### System Availability and SLA Policies

1. **Gateway Availability SLA**: The API gateway commits to 99.95% monthly uptime measured by Route 53 health check polling at 10-second intervals. Planned maintenance windows are excluded, provided they are announced at least 48 hours in advance and do not collectively exceed 4 hours per calendar month.
2. **Latency SLA**: The gateway must process, authenticate, transform, and forward requests within a P99 added-latency budget of 50 ms (gateway-only overhead, excluding upstream response time) measured over any rolling 5-minute window. Breach for more than 3 consecutive minutes constitutes a P1 incident.
3. **Incident Escalation Timeline**: P0 incidents must be acknowledged within 5 minutes, mitigated within 30 minutes, and have a root-cause analysis published within 5 business days of resolution.
4. **Disaster Recovery Objectives**: The system must achieve an RTO of 15 minutes and an RPO of 1 minute using RDS Multi-AZ automated failover and ElastiCache replication groups with automatic failover across a minimum of three Availability Zones.
