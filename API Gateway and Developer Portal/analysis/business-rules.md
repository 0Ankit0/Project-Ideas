# Business Rules — API Gateway and Developer Portal

## Overview

This document catalogues all business rules governing the behaviour of the **API Gateway and Developer Portal** platform. Each rule is uniquely identified, fully described with its triggering condition and resulting action, assigned a priority (1 = highest), and dated for audit compliance. Rules are enforced by the gateway request pipeline, the portal backend service, the BullMQ worker fleet, or a combination of these components.

Business rules are owned by the **Platform Product team**, reviewed quarterly, and versioned in this document. Any change to a rule requires a change-management ticket, impact analysis, stakeholder sign-off, and a minimum 14-day lead time before production enforcement (except for emergency security rules, which may be applied immediately with retrospective approval).

---

## Rate Limiting Rules

### BR-RL-001

| Field | Value |
|-------|-------|
| **Rule ID** | BR-RL-001 |
| **Name** | Per-Consumer Per-Minute Rate Limit |
| **Description** | Every API request made with a valid API key is counted against the consumer's per-minute request allowance as defined by their active subscription plan. The counter is stored in Redis as a sliding-window counter using the key pattern `rl:{consumer_id}:{route_id}:{window_minute}`. |
| **Condition** | A request arrives at the gateway with a valid API key or JWT belonging to a consumer on any paid or free plan. |
| **Action** | Increment the sliding-window counter. If the counter exceeds the plan's `requests_per_minute` limit, return HTTP 429 with `Retry-After` header set to the number of seconds until the current window expires. Emit `ratelimit.quota.exceeded` event. |
| **Priority** | 1 |
| **Effective Date** | 2024-01-01 |

---

### BR-RL-002

| Field | Value |
|-------|-------|
| **Rule ID** | BR-RL-002 |
| **Name** | Per-Consumer Daily Quota Hard Cap |
| **Description** | Each consumer has a daily request quota defined by their plan. This quota resets at 00:00 UTC each day. The daily counter is maintained in Redis alongside the per-minute counter. Unlike the per-minute limit, the daily quota represents an absolute hard cap with no burst allowance. |
| **Condition** | The daily request counter for a consumer reaches or exceeds the plan's `requests_per_day` value. |
| **Action** | Return HTTP 429 with `X-Quota-Reset` header set to the next UTC midnight timestamp (Unix epoch). Log the event as `ratelimit.quota.exceeded` with `window_type: daily`. Send a quota-exhaustion email via SES if the consumer has notifications enabled. |
| **Priority** | 1 |
| **Effective Date** | 2024-01-01 |

---

### BR-RL-003

| Field | Value |
|-------|-------|
| **Rule ID** | BR-RL-003 |
| **Name** | Quota Warning Notification at 80% |
| **Description** | When a consumer's daily request count reaches 80% of their plan's `requests_per_day` limit, a single quota-warning notification is dispatched for that calendar day. Repeated warnings for the same consumer on the same day are suppressed. |
| **Condition** | Daily counter crosses the threshold `floor(requests_per_day * 0.80)` for the first time in the current UTC day. |
| **Action** | Emit `ratelimit.quota.warning` event with `threshold_pct: 80`. Enqueue a BullMQ job to send a quota-warning email. Set a Redis flag `rl_warn_sent:{consumer_id}:{date}` with TTL of 86400 seconds to prevent duplicate notifications. |
| **Priority** | 2 |
| **Effective Date** | 2024-01-01 |

---

### BR-RL-004

| Field | Value |
|-------|-------|
| **Rule ID** | BR-RL-004 |
| **Name** | Global IP-Level Burst Limiter |
| **Description** | Regardless of consumer identity, the gateway enforces a global per-IP burst limit to protect against credential stuffing and scraping attacks. This rule operates on the raw client IP after extracting from `X-Forwarded-For` (first untrusted hop). |
| **Condition** | A single IP address submits more than 500 requests within any rolling 60-second window, regardless of the API key or JWT presented. |
| **Action** | Return HTTP 429 with `Retry-After: 60`. Log the event to SIEM as a security alert with severity `MEDIUM`. If the same IP triggers this rule 3 times within 10 minutes, escalate to severity `HIGH` and create an automatic WAF block rule candidate for Admin review. |
| **Priority** | 1 |
| **Effective Date** | 2024-01-01 |

---

### BR-RL-005

| Field | Value |
|-------|-------|
| **Rule ID** | BR-RL-005 |
| **Name** | Route-Level Override Rate Limit |
| **Description** | Individual API routes may have a route-level rate-limit policy that is stricter than the consumer's plan limit. When both a plan-level and a route-level policy apply, the more restrictive limit takes precedence. |
| **Condition** | A request targets a route that has an active `RateLimitPolicy` with `scope: ROUTE` and the route-level limit is lower than the consumer's plan-level limit for any window dimension (per-minute or per-day). |
| **Action** | Apply the route-level limit as the effective limit for that route only. Return HTTP 429 with header `X-RateLimit-Policy: route-override` when the route limit is hit. This does not consume the consumer's global plan quota. |
| **Priority** | 2 |
| **Effective Date** | 2024-02-01 |

---

### BR-RL-006

| Field | Value |
|-------|-------|
| **Rule ID** | BR-RL-006 |
| **Name** | Burst Allowance for Paid Plans |
| **Description** | Paid-tier consumers (plans above the Free tier) are granted a burst allowance that permits short-term traffic spikes up to 1.5× their `requests_per_minute` limit for up to 10 consecutive seconds within a 60-second window, consuming from a dedicated burst token bucket. |
| **Condition** | Consumer is on a paid plan AND the burst token bucket has available tokens AND the base per-minute counter has exceeded the plan limit but not exceeded the burst ceiling (`requests_per_minute * 1.5`). |
| **Action** | Allow the request, decrement the burst token bucket. Attach response header `X-RateLimit-Burst-Remaining: {n}`. Do NOT increment the base per-minute counter for burst-consumed requests. |
| **Priority** | 3 |
| **Effective Date** | 2024-03-01 |

---

### BR-RL-007

| Field | Value |
|-------|-------|
| **Rule ID** | BR-RL-007 |
| **Name** | Admin-Exempt Rate Limiting |
| **Description** | Requests authenticated with an internal service token (issued to Admin or Provider automated tooling) are exempt from consumer rate-limit policies but are still subject to the global IP-level burst limiter (BR-RL-004). This exemption does not apply to end-user Developer API keys. |
| **Condition** | Request carries a valid internal service token in the `X-Internal-Service-Token` header, and the token's `scope` claim includes `admin:bypass_ratelimit`. |
| **Action** | Skip all per-consumer rate-limit counter increments. Allow the request to proceed directly to authentication and upstream forwarding. Log the bypass as an audit event for monitoring purposes. |
| **Priority** | 2 |
| **Effective Date** | 2024-01-01 |

---

### BR-RL-008

| Field | Value |
|-------|-------|
| **Rule ID** | BR-RL-008 |
| **Name** | Concurrent Connection Limit per Consumer |
| **Description** | To prevent a single consumer from holding excessive long-lived connections (e.g., server-sent events or WebSocket streams), a maximum number of concurrent connections per consumer is enforced using Redis atomic counters. |
| **Condition** | A new connection is established and the consumer's active connection count in Redis reaches or exceeds `max_concurrent_connections` as defined by the plan (default: 10 for Free, 100 for Pro, unlimited for Enterprise). |
| **Action** | Reject the new connection with HTTP 429 and error code `concurrent_connection_limit_exceeded`. Decrement the counter when the connection closes. Emit a `ratelimit.connection.limit_exceeded` event for observability. |
| **Priority** | 2 |
| **Effective Date** | 2024-04-01 |

---

### BR-RL-009

| Field | Value |
|-------|-------|
| **Rule ID** | BR-RL-009 |
| **Name** | Rate Limit Header Propagation |
| **Description** | The gateway must attach rate-limit state headers to every successful response (HTTP 2xx and 4xx, excluding 429) so that API consumers can track their quota consumption programmatically without polling a separate endpoint. |
| **Condition** | Any request that completes processing (regardless of upstream success or failure) and does not result in a rate-limit rejection. |
| **Action** | Attach `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` headers derived from the per-minute Redis counter. For daily quota, also attach `X-Quota-Limit-Day`, `X-Quota-Remaining-Day`, `X-Quota-Reset-Day`. |
| **Priority** | 4 |
| **Effective Date** | 2024-01-01 |

---

### BR-RL-010

| Field | Value |
|-------|-------|
| **Rule ID** | BR-RL-010 |
| **Name** | Rate Limit Redis Fallback |
| **Description** | If the Redis cluster is unavailable when the gateway attempts to read or write rate-limit counters, the gateway must fail open (allow the request) rather than fail closed (block all traffic). A circuit breaker tracks Redis availability and opens after 5 consecutive failures within 10 seconds. |
| **Condition** | Redis connection pool returns a connection error, timeout, or CLUSTERDOWN error during a rate-limit counter operation. |
| **Action** | Allow the request to proceed. Attach `X-RateLimit-Mode: degraded` response header. Emit a `ratelimit.backend.unavailable` alert event. Increment a Prometheus counter `gateway_ratelimit_redis_fallback_total`. Open the circuit breaker and retry Redis connection on a 5-second schedule. |
| **Priority** | 1 |
| **Effective Date** | 2024-01-01 |

---

## Authentication Rules

### BR-AUTH-001

| Field | Value |
|-------|-------|
| **Rule ID** | BR-AUTH-001 |
| **Name** | API Key HMAC-SHA256 Validation |
| **Description** | All requests using API key authentication must present the key in the `X-API-Key` header. The gateway computes `HMAC-SHA256(key_prefix + "." + key_secret, gateway_signing_secret)` and compares the result against the stored hash using a constant-time comparison to prevent timing attacks. |
| **Condition** | Request contains an `X-API-Key` header. |
| **Action** | Validate the key hash. On match: resolve consumer identity, load plan metadata from Redis cache (fallback to PostgreSQL), attach consumer context to request. On mismatch or expired key: return HTTP 401 with `WWW-Authenticate: ApiKey` and emit `auth.key.rejected` event. |
| **Priority** | 1 |
| **Effective Date** | 2024-01-01 |

---

### BR-AUTH-002

| Field | Value |
|-------|-------|
| **Rule ID** | BR-AUTH-002 |
| **Name** | JWT Bearer Token Validation |
| **Description** | Requests using OAuth 2.0 / OIDC authentication present a JWT in the `Authorization: Bearer <token>` header. The gateway validates the token's signature using JWKS keys, checks `exp`, `iat`, `iss`, and `aud` claims, and maps the `sub` claim to a consumer identity. |
| **Condition** | Request contains an `Authorization` header with a `Bearer` scheme. |
| **Action** | Validate JWT. On success: extract consumer ID from `sub` claim, load subscription context, attach enrichment headers. On failure (expired, invalid signature, wrong audience): return HTTP 401 with `error: invalid_token` JSON body and emit `auth.jwt.rejected` event. |
| **Priority** | 1 |
| **Effective Date** | 2024-01-01 |

---

### BR-AUTH-003

| Field | Value |
|-------|-------|
| **Rule ID** | BR-AUTH-003 |
| **Name** | Dual Authentication Scheme Priority |
| **Description** | A request may contain both an `X-API-Key` header and a `Bearer` token simultaneously (e.g., from a misconfigured client). In such cases, the gateway applies a defined priority: API key authentication takes precedence over JWT authentication. |
| **Condition** | Request contains both `X-API-Key` and `Authorization: Bearer` headers. |
| **Action** | Attempt API key validation first. If the API key is valid, proceed with the key-authenticated context and ignore the JWT. If the API key is invalid, do NOT fall back to JWT — return HTTP 401 with error `conflicting_auth_schemes`. Log the event for security review. |
| **Priority** | 2 |
| **Effective Date** | 2024-02-01 |

---

### BR-AUTH-004

| Field | Value |
|-------|-------|
| **Rule ID** | BR-AUTH-004 |
| **Name** | Unauthenticated Request Handling |
| **Description** | Requests to non-public routes that carry no authentication credentials are rejected at the gateway before any rate-limit counter is incremented or upstream contact is made. Public routes (explicitly marked `auth_required: false`) are forwarded without authentication. |
| **Condition** | Request targets a route with `auth_required: true` and contains neither `X-API-Key` nor `Authorization` header. |
| **Action** | Return HTTP 401 with body `{"error": "authentication_required", "message": "Supply an API key in X-API-Key or a JWT in Authorization: Bearer"}`. Do not forward to upstream. Do not increment rate-limit counters. |
| **Priority** | 1 |
| **Effective Date** | 2024-01-01 |

---

### BR-AUTH-005

| Field | Value |
|-------|-------|
| **Rule ID** | BR-AUTH-005 |
| **Name** | Suspended API Key Rejection |
| **Description** | API keys in `SUSPENDED` or `REVOKED` status must be rejected even if the HMAC hash is otherwise valid. The key status is checked in the Redis cache as part of the cache entry metadata. Cache entries for suspended keys are invalidated within 60 seconds of a status change. |
| **Condition** | API key HMAC validation succeeds, but the cached or database key record has `status` of `SUSPENDED` or `REVOKED`. |
| **Action** | Return HTTP 403 with `{"error": "key_suspended"}` or `{"error": "key_revoked"}` respectively. Emit `auth.key.rejected` event with `reason` field. Do not increment rate-limit counters. |
| **Priority** | 1 |
| **Effective Date** | 2024-01-01 |

---

### BR-AUTH-006

| Field | Value |
|-------|-------|
| **Rule ID** | BR-AUTH-006 |
| **Name** | API Key Scope Enforcement |
| **Description** | API keys may be scoped to specific routes, environments (sandbox vs. production), or HTTP methods. The gateway enforces scope restrictions after successful key authentication. A key with `scope: ["GET /v1/payments/*"]` may not be used to call `POST /v1/payments/` even if the route exists. |
| **Condition** | API key authentication succeeds AND the key has a non-empty `scopes` array AND the requested route + method combination does not match any scope pattern. |
| **Action** | Return HTTP 403 with `{"error": "insufficient_scope", "required_scope": "<method> <route>"}`. Emit `auth.key.scope_violation` event for audit. |
| **Priority** | 2 |
| **Effective Date** | 2024-03-01 |

---

### BR-AUTH-007

| Field | Value |
|-------|-------|
| **Rule ID** | BR-AUTH-007 |
| **Name** | Failed Authentication Brute-Force Protection |
| **Description** | Repeated authentication failures from the same IP address or presenting the same key prefix indicate a brute-force or credential-stuffing attempt. A Redis counter tracks failures per key prefix per IP to throttle such attacks. |
| **Condition** | More than 10 authentication failures (invalid key hash, invalid JWT signature, or wrong audience) from the same source IP within a 60-second window. |
| **Action** | Block further authentication attempts from that IP for 300 seconds, returning HTTP 429 with `Retry-After: 300`. Emit a security event to SIEM with severity `HIGH`. Admin Console displays an active block in the security dashboard. |
| **Priority** | 1 |
| **Effective Date** | 2024-01-01 |

---

### BR-AUTH-008

| Field | Value |
|-------|-------|
| **Rule ID** | BR-AUTH-008 |
| **Name** | Key Rotation Overlap Window |
| **Description** | When a Developer rotates an API key, the old key remains valid for a configurable overlap period (default: 24 hours) to allow the Developer time to update their application configuration without experiencing authentication failures. Both the old and new keys are valid concurrently during this window. |
| **Condition** | A key rotation event is recorded for a consumer. The old key's `expires_at` is set to `NOW() + overlap_hours`. |
| **Action** | Accept both the old and new key during the overlap window. Attach `X-API-Key-Rotation: old_key_expiring` header to responses authenticated with the old key. After the overlap window, the old key's status is set to `REVOKED` by a scheduled BullMQ job. |
| **Priority** | 3 |
| **Effective Date** | 2024-02-01 |

---

## Subscription and Quota Rules

### BR-PLAN-001

| Field | Value |
|-------|-------|
| **Rule ID** | BR-PLAN-001 |
| **Name** | Plan Activation Requires Payment Confirmation |
| **Description** | A consumer's subscription plan is not considered active, and its quota is not applied in the gateway, until a `invoice.paid` or `checkout.session.completed` event is received from Stripe and processed by the BullMQ subscription worker. |
| **Condition** | A consumer completes plan selection on the portal but the Stripe payment event has not yet been received. |
| **Action** | Consumer remains on their previous plan (or Free plan for new registrations). Portal displays a "Payment pending" status banner. If payment is not confirmed within 24 hours, the subscription is cancelled and the consumer is notified by email. |
| **Priority** | 1 |
| **Effective Date** | 2024-01-01 |

---

### BR-PLAN-002

| Field | Value |
|-------|-------|
| **Rule ID** | BR-PLAN-002 |
| **Name** | Immediate Quota Application on Upgrade |
| **Description** | When a consumer upgrades to a higher-tier plan, the new quota limits must be active within 60 seconds of payment confirmation. There is no waiting period or next-billing-cycle delay for plan upgrades. |
| **Condition** | `consumer.plan.upgraded` event is emitted and Stripe `invoice.paid` confirms payment. |
| **Action** | Update consumer plan metadata in PostgreSQL. Publish cache invalidation to Redis for the consumer's API key entries. BullMQ worker verifies cache refresh within 60 seconds. |
| **Priority** | 1 |
| **Effective Date** | 2024-01-01 |

---

### BR-PLAN-003

| Field | Value |
|-------|-------|
| **Rule ID** | BR-PLAN-003 |
| **Name** | Downgrade Takes Effect at Billing Cycle End |
| **Description** | When a consumer downgrades to a lower-tier plan, the downgrade takes effect at the end of the current billing period. The consumer retains their current (higher) quota until that date. This prevents punishing consumers for making plan adjustments mid-cycle. |
| **Condition** | Consumer submits a plan downgrade request via the portal or management API. |
| **Action** | Record `pending_plan_id` on the consumer record. Schedule a BullMQ job to apply the downgrade at `current_period_end` (as returned by Stripe). Display a banner in the portal showing the scheduled downgrade date. |
| **Priority** | 2 |
| **Effective Date** | 2024-01-01 |

---

### BR-PLAN-004

| Field | Value |
|-------|-------|
| **Rule ID** | BR-PLAN-004 |
| **Name** | Free Plan Feature Restrictions |
| **Description** | Consumers on the Free plan are restricted to a subset of gateway features. Specifically: no webhook subscriptions, no custom domain routing, no analytics data export, no SLA guarantee, and a maximum of 2 API keys per application. |
| **Condition** | A Free-plan consumer attempts to create a webhook, export analytics, or create a third API key for an application. |
| **Action** | Return HTTP 403 with `{"error": "plan_restriction", "required_plan": "Pro", "feature": "<feature_name>"}`. Display an upsell prompt in the portal. Log a `consumer.feature.restricted` event for growth analytics. |
| **Priority** | 2 |
| **Effective Date** | 2024-01-01 |

---

### BR-PLAN-005

| Field | Value |
|-------|-------|
| **Rule ID** | BR-PLAN-005 |
| **Name** | Monthly Quota Reset |
| **Description** | Monthly request quotas (for plans with a monthly quota dimension, distinct from the daily quota) reset at the start of each Stripe billing cycle. The reset timestamp is derived from the `current_period_start` field on the Stripe subscription object, not from a fixed calendar date. |
| **Condition** | Stripe delivers a `invoice.paid` event marking the start of a new billing period for a consumer. |
| **Action** | Reset the consumer's monthly usage counter in PostgreSQL. Clear relevant Redis quota keys. Update the `quota_reset_at` field on the consumer's subscription record. Emit `consumer.quota.reset` event. |
| **Priority** | 1 |
| **Effective Date** | 2024-01-01 |

---

### BR-PLAN-006

| Field | Value |
|-------|-------|
| **Rule ID** | BR-PLAN-006 |
| **Name** | Trial Period Handling |
| **Description** | New consumer registrations on paid plans may be eligible for a 14-day free trial. Trial consumers receive the full quota of their selected plan. At the end of the trial, if no valid payment method is on file, the account is automatically downgraded to the Free plan. |
| **Condition** | Consumer registers with a paid plan and Stripe creates a subscription with `trial_end` set 14 days in the future. |
| **Action** | Activate full plan quota immediately. Set a BullMQ job for 48 hours before `trial_end` to send a trial-ending warning email. If `invoice.payment_failed` is received at trial end due to no payment method, emit `consumer.plan.downgraded` and apply Free plan restrictions. |
| **Priority** | 2 |
| **Effective Date** | 2024-03-01 |

---

### BR-PLAN-007

| Field | Value |
|-------|-------|
| **Rule ID** | BR-PLAN-007 |
| **Name** | Plan Deletion Protection |
| **Description** | A subscription plan may not be deleted from the platform if any consumers have active or trial subscriptions on that plan. Deletion is only permitted if the plan has zero active subscribers and is in `DEPRECATED` status. |
| **Condition** | Admin submits a plan deletion request. |
| **Action** | Check for active subscribers. If count > 0: return 409 Conflict with a list of affected consumers and block deletion. If count == 0 and status == `DEPRECATED`: proceed with deletion and emit `plan.deleted` audit event. |
| **Priority** | 2 |
| **Effective Date** | 2024-01-01 |

---

### BR-PLAN-008

| Field | Value |
|-------|-------|
| **Rule ID** | BR-PLAN-008 |
| **Name** | Enterprise Plan Custom Negotiation |
| **Description** | Enterprise plan quotas, pricing, and features are negotiated on a per-customer basis and are not published in the public plan catalogue. Enterprise plan records in the database have `is_public: false` and are only visible to Admins and the specific consumer they are assigned to. |
| **Condition** | A consumer is assigned an Enterprise plan by an Admin. |
| **Action** | Apply custom `requests_per_minute`, `requests_per_day`, `requests_per_month`, and feature flags as defined in the plan record. Do not display the plan details in the public portal API catalogue. Include the plan in the consumer's portal dashboard with full detail. |
| **Priority** | 3 |
| **Effective Date** | 2024-01-01 |

---

## API Versioning Rules

### BR-VER-001

| Field | Value |
|-------|-------|
| **Rule ID** | BR-VER-001 |
| **Name** | Semantic Versioning Required |
| **Description** | All API routes published on the platform must use URI path versioning in the format `/v{major}` (e.g., `/v1/`, `/v2/`). Minor and patch version changes are made within the same major version path and documented in the API changelog. Breaking changes always require a new major version. |
| **Condition** | An API Provider submits a new route registration or a route update. |
| **Action** | Validate that the route path begins with `/v{integer}/`. Reject registrations that do not conform with HTTP 422 and a descriptive validation error. |
| **Priority** | 2 |
| **Effective Date** | 2024-01-01 |

---

### BR-VER-002

| Field | Value |
|-------|-------|
| **Rule ID** | BR-VER-002 |
| **Name** | Deprecation Notice Period |
| **Description** | Before an API version is retired (removed from the gateway), it must be in `DEPRECATED` status for a minimum of 90 calendar days. During the deprecation period, the gateway attaches a `Deprecation` header and a `Sunset` header to all responses from that version, informing consumers of the retirement date. |
| **Condition** | An API version's status is changed to `DEPRECATED` by an API Provider or Admin. |
| **Action** | Record `deprecated_at` and `sunset_at = deprecated_at + 90 days`. For every response from that route version, attach `Deprecation: true` and `Sunset: {HTTP-date of sunset_at}`. Emit `api.version.deprecated` event. Notify all consumers subscribed to that version by email. |
| **Priority** | 2 |
| **Effective Date** | 2024-01-01 |

---

### BR-VER-003

| Field | Value |
|-------|-------|
| **Rule ID** | BR-VER-003 |
| **Name** | Version Retirement Enforcement |
| **Description** | On or after the `sunset_at` date, an API version in `DEPRECATED` status is automatically transitioned to `RETIRED` by a scheduled BullMQ job. Once retired, all requests to that version path return HTTP 410 Gone. |
| **Condition** | BullMQ scheduled job runs daily at 00:05 UTC and finds API versions with `sunset_at <= NOW()` and `status = DEPRECATED`. |
| **Action** | Update status to `RETIRED`. Disable the route in the gateway route table. Return HTTP 410 for all requests to the retired version path. Emit `api.version.retired` event. |
| **Priority** | 1 |
| **Effective Date** | 2024-01-01 |

---

### BR-VER-004

| Field | Value |
|-------|-------|
| **Rule ID** | BR-VER-004 |
| **Name** | Version Co-existence Limit |
| **Description** | An API Provider may not have more than 3 simultaneous active (`ACTIVE`) major versions of the same API registered on the gateway. This limit prevents version sprawl and encourages timely migration. Enterprise-tier Providers may request an exception reviewed by Admin. |
| **Condition** | An API Provider attempts to register a new major version when they already have 3 active major versions of the same API. |
| **Action** | Reject the registration with HTTP 422 and error `max_active_versions_exceeded`. Recommend deprecating an existing version before adding a new one. |
| **Priority** | 3 |
| **Effective Date** | 2024-04-01 |

---

### BR-VER-005

| Field | Value |
|-------|-------|
| **Rule ID** | BR-VER-005 |
| **Name** | Version Traffic Migration Reporting |
| **Description** | During the deprecation period, the gateway tracks and reports the percentage of daily traffic still hitting a deprecated version versus the replacement version. This data is surfaced on the Provider's Analytics dashboard and used by Admin to decide whether to extend the deprecation window. |
| **Condition** | An API version has `status = DEPRECATED` and the current date is within the deprecation window. |
| **Action** | Emit `analytics.metric.recorded` events tagged with `version_migration: true`. Aggregate daily request counts per version in the analytics database. Display migration progress chart in the Provider portal. If traffic to the deprecated version is still above 10% at 30 days before `sunset_at`, trigger a migration-risk alert to the Admin. |
| **Priority** | 3 |
| **Effective Date** | 2024-03-01 |

---

## Webhook Delivery Rules

### BR-WH-001

| Field | Value |
|-------|-------|
| **Rule ID** | BR-WH-001 |
| **Name** | Webhook Delivery Retry Policy |
| **Description** | When a webhook delivery attempt fails (non-2xx response or connection timeout), the platform retries delivery using exponential backoff. The retry schedule is: 30 s, 2 min, 10 min, 30 min, 2 h. After 5 failed attempts, the webhook is marked `DEAD` and moved to the Dead Letter Queue. |
| **Condition** | A webhook delivery attempt receives a non-2xx HTTP response or times out after 10 seconds. |
| **Action** | Emit `webhook.delivery.attempted` event with `success: false`. Schedule the next retry via BullMQ `delay` option. After 5th failure: emit `webhook.delivery.failed`, mark subscription as `FAILED`, notify the subscriber by email, and move the payload to the DLQ. |
| **Priority** | 2 |
| **Effective Date** | 2024-01-01 |

---

### BR-WH-002

| Field | Value |
|-------|-------|
| **Rule ID** | BR-WH-002 |
| **Name** | Webhook HMAC Signature |
| **Description** | All outgoing webhook deliveries must include a `X-Signature-256` header containing `HMAC-SHA256(payload_body, webhook_secret)` encoded as `sha256=<hex>`. Webhook secrets are generated per subscription using 32 bytes of cryptographic randomness and stored in PostgreSQL. |
| **Condition** | Any outgoing webhook payload is dispatched by the BullMQ webhook worker. |
| **Action** | Compute HMAC-SHA256 of the raw JSON body. Attach `X-Signature-256: sha256={hex_digest}`. Include a `X-Webhook-ID` header with the delivery attempt UUID and `X-Webhook-Timestamp` with the current Unix timestamp. |
| **Priority** | 1 |
| **Effective Date** | 2024-01-01 |

---

### BR-WH-003

| Field | Value |
|-------|-------|
| **Rule ID** | BR-WH-003 |
| **Name** | Webhook Endpoint Validation |
| **Description** | When a webhook subscription is created or updated, the platform validates the target URL by sending a `GET` request with a `X-Webhook-Verification-Token` query parameter. The endpoint must respond with the token value in the response body within 10 seconds. |
| **Condition** | Developer submits a new or updated webhook subscription with a target URL. |
| **Action** | Send a verification `GET` request. If verified: activate the subscription. If not verified within 10 seconds or the token does not match: reject the subscription with HTTP 422 and `webhook_endpoint_verification_failed`. |
| **Priority** | 2 |
| **Effective Date** | 2024-02-01 |

---

### BR-WH-004

| Field | Value |
|-------|-------|
| **Rule ID** | BR-WH-004 |
| **Name** | Webhook Payload Size Limit |
| **Description** | Outgoing webhook payloads are limited to 512 KB. Events whose payloads exceed this size are truncated and marked with `truncated: true` in the payload metadata. The Developer is notified that full payloads can be retrieved via the event details API. |
| **Condition** | A webhook event payload serialises to a JSON body exceeding 512 KB. |
| **Action** | Truncate the `data` field. Add `metadata.truncated: true` and `metadata.full_event_url: "https://api.domain.com/v1/events/{event_id}"` to the payload. Deliver the truncated payload as normal. |
| **Priority** | 3 |
| **Effective Date** | 2024-03-01 |

---

### BR-WH-005

| Field | Value |
|-------|-------|
| **Rule ID** | BR-WH-005 |
| **Name** | Automatic Webhook Subscription Suspension |
| **Description** | A webhook subscription is automatically suspended if its delivery failure rate exceeds 80% over a rolling 7-day window (minimum 10 delivery attempts). Suspension prevents wasted retry cycles against permanently unavailable endpoints. |
| **Condition** | The platform calculates a webhook subscription's 7-day delivery failure rate and it is ≥ 80% with at least 10 attempts. |
| **Action** | Set subscription `status = SUSPENDED`. Emit `webhook.subscription.suspended` event. Send the subscriber an email listing the failed endpoint URL, failure rate, and instructions to re-enable after fixing the endpoint. |
| **Priority** | 2 |
| **Effective Date** | 2024-04-01 |

---

### BR-WH-006

| Field | Value |
|-------|-------|
| **Rule ID** | BR-WH-006 |
| **Name** | Webhook Delivery Ordering Guarantee |
| **Description** | Webhook deliveries for a given subscription are delivered in chronological order (FIFO) within the same event type. Out-of-order delivery is prevented by assigning a monotonically increasing `sequence_number` and processing deliveries serially per subscription in the BullMQ queue. |
| **Condition** | Multiple events of the same type are queued for delivery to the same webhook subscription. |
| **Action** | Assign sequential `sequence_number` values at event emission time. BullMQ processes deliveries for a given `subscription_id` serially (concurrency: 1 per subscription). Receivers may use the `sequence_number` to detect gaps or re-ordering. |
| **Priority** | 3 |
| **Effective Date** | 2024-04-01 |

---

## Data Retention Rules

### BR-DATA-001

| Field | Value |
|-------|-------|
| **Rule ID** | BR-DATA-001 |
| **Name** | Request Access Log Retention |
| **Description** | Raw request access logs (IP, timestamp, route, status code, latency, consumer ID) are retained for 90 days in the hot storage tier (PostgreSQL `analytics_events` table) and then archived to S3 in Parquet format. S3 archives are retained for 2 years. After 2 years, archives are permanently deleted via S3 lifecycle rules. |
| **Condition** | Automated data lifecycle job runs nightly at 02:00 UTC. |
| **Action** | Archive rows with `created_at < NOW() - INTERVAL '90 days'` from `analytics_events` to S3. Delete rows from PostgreSQL after successful S3 write confirmation. Update retention audit log. |
| **Priority** | 2 |
| **Effective Date** | 2024-01-01 |

---

### BR-DATA-002

| Field | Value |
|-------|-------|
| **Rule ID** | BR-DATA-002 |
| **Name** | Audit Log Immutability |
| **Description** | Records in the `audit_logs` table may never be updated or deleted by application code, including Admin actions. Audit logs are append-only. Database-level row security policies enforce this. Audit logs are retained for a minimum of 7 years to meet financial and regulatory compliance requirements. |
| **Condition** | Any attempt to `UPDATE` or `DELETE` rows in the `audit_logs` table via the application database user. |
| **Action** | Reject the operation at the PostgreSQL row-level security policy layer and return a database error. The application layer must never issue `DELETE` or `UPDATE` on this table. |
| **Priority** | 1 |
| **Effective Date** | 2024-01-01 |

---

### BR-DATA-003

| Field | Value |
|-------|-------|
| **Rule ID** | BR-DATA-003 |
| **Name** | API Key Plaintext Never Stored |
| **Description** | The full plaintext API key is displayed to the Developer exactly once, immediately after creation, and is never stored in the platform's database or logs. Only the HMAC-SHA256 hash of the key is persisted. The key prefix (first 8 characters) is stored in plaintext for identification purposes only. |
| **Condition** | API key creation completes. |
| **Action** | Generate 32-byte cryptographic key, prefix with 8-character identifier. Return full key in creation API response. Store only `key_hash = HMAC-SHA256(key)` and `key_prefix` in the database. Never log the full key value. |
| **Priority** | 1 |
| **Effective Date** | 2024-01-01 |

---

### BR-DATA-004

| Field | Value |
|-------|-------|
| **Rule ID** | BR-DATA-004 |
| **Name** | Deleted Consumer Data Anonymisation |
| **Description** | When a consumer account is deleted (either by the consumer or by an Admin), all personally identifiable information is anonymised within 30 days. Related subscription and analytics records are retained in anonymised form for financial reporting and platform integrity. |
| **Condition** | Consumer account deletion request is received and confirmed. |
| **Action** | Set `status = DELETED`, nullify PII fields (`email`, `name`, `company`), replace with `REDACTED_{uuid}` tokens. Revoke all active API keys. Cancel Stripe subscriptions. Schedule a BullMQ job for the 30-day full anonymisation sweep. |
| **Priority** | 2 |
| **Effective Date** | 2024-01-01 |

---

### BR-DATA-005

| Field | Value |
|-------|-------|
| **Rule ID** | BR-DATA-005 |
| **Name** | Webhook Event Payload Retention |
| **Description** | Webhook event payloads (including the raw JSON body dispatched to consumer endpoints) are retained for 30 days in the `webhook_deliveries` table to allow consumers to re-fetch missed events via the Event Replay API. After 30 days, payload bodies are deleted but metadata (event ID, subscription ID, delivery status, timestamp) is retained for 12 months. |
| **Condition** | Automated data lifecycle job runs nightly at 03:00 UTC. |
| **Action** | Nullify `payload_body` column for `webhook_deliveries` rows older than 30 days. Retain all other columns. Delete entire rows older than 12 months. |
| **Priority** | 3 |
| **Effective Date** | 2024-02-01 |

---

## Conflict Resolution

When multiple business rules are triggered simultaneously, the following precedence table governs the outcome. Higher precedence rules are applied first; lower precedence rules are not evaluated if the request is already rejected.

| Precedence | Rule Category | Rule ID(s) | Rationale |
|------------|--------------|------------|-----------|
| 1 | Security suspension | BR-AUTH-005, BR-AUTH-007 | Revoked/suspended keys and brute-force blocks must be enforced before any other check to prevent security bypasses. |
| 2 | Authentication | BR-AUTH-001, BR-AUTH-002, BR-AUTH-004 | A request that cannot be authenticated must be rejected before quota is consumed. |
| 3 | Scope enforcement | BR-AUTH-006 | Authenticated but unauthorised-scope requests are rejected before rate limits are checked. |
| 4 | Admin/internal bypass | BR-RL-007 | Internal service tokens bypass consumer rate limits but are still subject to IP-level limits. |
| 5 | Global IP burst limit | BR-RL-004 | IP-level limits protect platform infrastructure and take precedence over per-consumer plan limits. |
| 6 | Route-level rate limit | BR-RL-005 | Route-specific limits take precedence over plan-level limits when more restrictive. |
| 7 | Plan-level rate limit | BR-RL-001, BR-RL-002 | Standard per-minute and daily plan limits. |
| 8 | Burst allowance | BR-RL-006 | Burst tokens are consumed only after the base per-minute limit is reached. |
| 9 | Plan feature restriction | BR-PLAN-004, BR-PLAN-008 | Feature restrictions apply after authentication and quota checks. |
| 10 | Versioning rules | BR-VER-003 | Retired version 410 responses are returned after all auth and quota checks pass. |

---

## Rule Change Management

All changes to business rules documented in this catalogue follow the **Platform Rule Change Management Process**:

1. **Proposal:** The requester creates a Change Request ticket in the Ticketing and Project Management System with: Rule ID(s) affected, proposed change text, business justification, impact analysis (which consumers, routes, or plans are affected), and rollback plan.

2. **Review:** The Platform Product team reviews the proposal within 3 business days. Security-related rule changes are additionally reviewed by the Security team. High-impact changes (affecting rate limits for more than 10% of consumers) are escalated to the CTO for approval.

3. **Documentation:** Approved changes are reflected in this document with an updated `Effective Date` and a changelog note. The old rule text is preserved in the git history of this document.

4. **Lead Time:** Standard rule changes require a minimum 14-day lead time before production enforcement. Emergency security rules (e.g., closing an active exploit) may be applied immediately with the approval of one Admin and the Security Lead, with retrospective change management documentation completed within 5 business days.

5. **Communication:** Developer-facing rule changes (rate limits, authentication scheme changes, plan restrictions) are communicated via the platform status page and email to affected consumers at least 7 days before the effective date.

6. **Validation:** After a rule change is deployed to production, a 24-hour monitoring period is observed. If the change produces unexpected results (e.g., false-positive rate-limit rejections exceeding 0.1% of baseline traffic), the change is automatically rolled back and the incident is escalated.

---

## Operational Policy Addendum

### API Governance Policies

1. **Policy AGP-001 — Rule Ownership and Accountability:** Every business rule catalogued in this document must have a designated owner from the Platform Product team. The owner is responsible for reviewing the rule at least once per quarter, ensuring the rule remains aligned with platform strategy, and initiating change management when amendments are required. Ownerless rules are flagged for review within 30 days.

2. **Policy AGP-002 — Emergency Rule Bypass Prohibition:** No business rule may be bypassed in production outside of the formal exception process, even under time pressure during an incident. Emergency rule changes must still go through the abbreviated emergency change management process described in the Rule Change Management section. Undocumented bypasses discovered during audit reviews are treated as security incidents.

3. **Policy AGP-003 — Rule Consistency Across Environments:** Business rules applied in the production environment must be mirrored exactly in the staging environment. Staging may have lower absolute thresholds (e.g., lower rate limits) for testing purposes, but the rule logic, conditions, and actions must be identical. Discrepancies between staging and production rule sets are considered defects and must be resolved before the next production deployment.

4. **Policy AGP-004 — Third-Party Rule Compliance:** When an upstream service, Stripe, or OAuth Identity Provider imposes constraints (e.g., Stripe API rate limits, IdP token issuance limits) that conflict with platform business rules, the platform rules must be adjusted to remain within the third-party constraints. The Platform team is responsible for monitoring third-party limit changes and proactively updating platform rules before breaches occur.

---

### Developer Data Privacy Policies

1. **Policy DDP-001 — Rule Enforcement Logging and PII:** When logging business rule enforcement actions (rate-limit hits, authentication failures, plan restriction events), the platform must not include request body content, URL query parameters that may contain PII, or full IP addresses without pseudonymisation. Only the consumer ID, anonymised IP, route, and rule ID may be included in enforcement logs.

2. **Policy DDP-002 — Quota Data Minimisation:** Rate-limit counters stored in Redis must only contain the consumer ID and counter value. They must not be enriched with email addresses, company names, or other personal data that would constitute PII in a Redis cache layer subject to broader access.

3. **Policy DDP-003 — Webhook Secret Confidentiality:** Webhook secrets (used for HMAC-SHA256 signing per BR-WH-002) must never be exposed via API responses after the initial creation response. Read operations on webhook subscriptions must mask the secret as `sk_****{last_4_chars}`. Secrets are stored encrypted at rest using AWS KMS in PostgreSQL using the `pgcrypto` extension.

4. **Policy DDP-004 — Data Subject Access Requests for Rule Enforcement History:** Upon request by a Developer (as data subject), the platform must be able to provide a structured export of all business rule enforcement actions taken against their consumer account within the past 12 months, including: rate-limit events, authentication failures, plan changes, and webhook failures. This export capability must be implemented and tested annually.

---

### Monetization and Quota Policies

1. **Policy MQP-001 — Plan Pricing Integrity:** Published plan pricing in the portal must always match the Stripe price objects. Any discrepancy between portal-displayed pricing and Stripe billing amounts is a critical defect. Automated reconciliation runs daily to compare portal `SubscriptionPlan.price_monthly_usd` against the corresponding Stripe price object amount. Discrepancies trigger an immediate alert to the Finance and Product teams.

2. **Policy MQP-002 — No Silent Quota Exhaustion:** When a consumer's quota is exhausted (daily or monthly), the platform must not silently drop requests. All quota-exhausted requests must receive an HTTP 429 response with a `Retry-After` or `X-Quota-Reset` header so consumers can implement appropriate backoff. Silent dropping of requests is prohibited by this policy.

3. **Policy MQP-003 — Refund Policy for Platform Outages:** If the platform fails to meet its published SLA (99.95% for paid tiers) in any calendar month, affected consumers are entitled to a service credit equivalent to 10% of their monthly subscription fee for each 0.1% of availability below the SLA threshold, up to 100% of the monthly fee. Credits are applied automatically to the next Stripe invoice without requiring a consumer claim.

4. **Policy MQP-004 — Quota Audit Trail:** All quota enforcement decisions (allow, deny, burst consumed) must be recorded as `analytics.metric.recorded` events in the analytics pipeline. These records are used for billing reconciliation, dispute resolution, and capacity planning. The quota audit trail must be available for query via the Admin API for at least 12 months.

---

### System Availability and SLA Policies

1. **Policy SAP-001 — Rule Engine Availability:** The rate-limiting and authentication rule engine (Redis-backed) must maintain sub-2ms p99 latency for rule evaluation under nominal load (up to 10,000 RPS per gateway instance). Any rule evaluation that exceeds 10ms is logged as a latency anomaly. A p99 latency breach above 5ms sustained for more than 60 seconds triggers a paging alert to the on-call engineer.

2. **Policy SAP-002 — Rule Change Zero-Downtime Deployment:** Business rule configuration changes (rate limit thresholds, plan feature flags, route policies) must be deployable without restarting the gateway process. Rule configuration is stored in Redis and PostgreSQL and hot-reloaded by the gateway on a 30-second polling interval. Any rule change that requires a gateway restart must be treated as a high-risk change and scheduled during a maintenance window.

3. **Policy SAP-003 — Failover Rule Consistency:** During a primary Redis cluster failover, rate-limit counters that are lost must cause the gateway to fail open (allow traffic) per BR-RL-010. The failover detection time must be under 30 seconds. After failover, counters are re-initialised from zero for the new window, and a monitoring alert documents the brief period during which rate limits were not enforced.

4. **Policy SAP-004 — Rule Version Control and Rollback:** All business rule configuration changes deployed to production must be tracked in version control with a timestamp, deployer identity, and diff. The platform must support single-step rollback of any rule configuration change within 5 minutes of deployment. Rollback procedures must be tested quarterly in the staging environment as part of the platform's disaster-recovery drills.
