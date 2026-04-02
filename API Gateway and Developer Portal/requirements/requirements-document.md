# Requirements Document — API Gateway and Developer Portal

## Document Information

| Field       | Value                              |
|-------------|------------------------------------|
| Project     | API Gateway and Developer Portal   |
| Version     | 1.0.0                              |
| Status      | Approved                           |
| Last Updated| 2025-01-01                         |

---

## 1. Functional Requirements

### 1.1 Domain: Request Routing

| ID        | Requirement                                                                                       | Priority | Notes                                  |
|-----------|---------------------------------------------------------------------------------------------------|----------|----------------------------------------|
| FR-RO-001 | The gateway SHALL route inbound HTTP/HTTPS requests to upstream services based on path and method. | P0       | Core proxy function                    |
| FR-RO-002 | The gateway SHALL support wildcard and parameterised path matching (e.g., `/v1/users/{id}`).      | P0       | Regex-capable path matcher             |
| FR-RO-003 | The gateway SHALL support host-based virtual routing for multi-tenant deployments.                | P1       | `Host` header inspection               |
| FR-RO-004 | The gateway SHALL load-balance across multiple upstream targets using round-robin, least-connections, or weighted strategies. | P0 | Configurable per-route              |
| FR-RO-005 | The gateway SHALL perform active health checks on upstream targets and remove unhealthy nodes from rotation automatically. | P0 | Interval, threshold, timeout configurable |
| FR-RO-006 | The gateway SHALL implement a circuit breaker that opens after a configurable threshold of consecutive upstream failures. | P1 | Hystrix-style half-open probe          |
| FR-RO-007 | The gateway SHALL forward client IP via `X-Forwarded-For` and `X-Real-IP` headers.               | P0       | Proxy protocol support                 |
| FR-RO-008 | The gateway SHALL support WebSocket upgrade proxying.                                             | P1       | `Connection: Upgrade` passthrough      |
| FR-RO-009 | The gateway SHALL enforce configurable upstream timeout (connect, read, write) per route.         | P0       | Defaults: connect 5s, read 60s         |
| FR-RO-010 | The gateway SHALL return a structured JSON error payload on routing failures (5xx).               | P0       | Consistent error envelope              |

### 1.2 Domain: Authentication & Authorisation

| ID        | Requirement                                                                                       | Priority | Notes                                  |
|-----------|---------------------------------------------------------------------------------------------------|----------|----------------------------------------|
| FR-AU-001 | The gateway SHALL validate API keys presented in the `Authorization: ApiKey <key>` header or `?api_key=` query parameter. | P0 | Key lookup in Redis with fallback to Postgres |
| FR-AU-002 | The gateway SHALL support OAuth 2.0 Authorization Code Flow for developer login to the portal.   | P0       | PKCE required                          |
| FR-AU-003 | The gateway SHALL support OAuth 2.0 Client Credentials Flow for machine-to-machine API access.   | P0       | Scope enforcement                      |
| FR-AU-004 | The gateway SHALL validate RS256 / ES256 signed JWTs, verify expiry (`exp`), issuer (`iss`), and audience (`aud`). | P0 | JWKS endpoint for key rotation      |
| FR-AU-005 | The gateway SHALL support mutual TLS (mTLS) client certificate authentication for enterprise consumers. | P2 | cert fingerprint stored in consumer profile |
| FR-AU-006 | The gateway SHALL reject requests with missing or malformed credentials with HTTP 401 and a machine-readable error code. | P0 | `WWW-Authenticate` header included  |
| FR-AU-007 | The gateway SHALL reject requests with valid credentials but insufficient scope/plan access with HTTP 403. | P0 | Reason in error payload            |
| FR-AU-008 | The gateway SHALL log every authentication event (success, failure, provider, consumer ID) to the audit log. | P1 | Append-only log                    |

### 1.3 Domain: Rate Limiting

| ID        | Requirement                                                                                       | Priority | Notes                                  |
|-----------|---------------------------------------------------------------------------------------------------|----------|----------------------------------------|
| FR-RL-001 | The gateway SHALL enforce per-consumer, per-minute request rate limits using a sliding-window algorithm. | P0 | Implemented with Redis sorted sets |
| FR-RL-002 | The gateway SHALL enforce per-consumer, per-day quota limits that reset at midnight UTC.          | P0       | Persisted in Postgres for billing      |
| FR-RL-003 | The gateway SHALL enforce per-IP rate limits for unauthenticated endpoints.                       | P1       | Protects login and token endpoints     |
| FR-RL-004 | The gateway SHALL return HTTP 429 with `Retry-After`, `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset` headers when limits are exceeded. | P0 | RFC 6585 compliant |
| FR-RL-005 | The gateway SHALL support multiple rate-limit tiers (Free, Basic, Pro, Enterprise) linked to subscription plans. | P0 | Plan-to-policy mapping table       |
| FR-RL-006 | The gateway SHALL allow admins to temporarily override rate limits for a consumer without changing their plan. | P1 | Time-bounded override              |
| FR-RL-007 | The gateway SHALL support a token-bucket algorithm as an alternative for bursty traffic patterns. | P1       | Configurable burst size            |
| FR-RL-008 | The gateway SHALL emit a `quota.breached` event when a consumer exhausts their daily quota.       | P0       | Triggers email notification        |

### 1.4 Domain: Request/Response Transformation

| ID        | Requirement                                                                                       | Priority | Notes                                  |
|-----------|---------------------------------------------------------------------------------------------------|----------|----------------------------------------|
| FR-TR-001 | The gateway SHALL support adding, removing, and renaming request headers before forwarding to upstream. | P0 | Plugin-based                       |
| FR-TR-002 | The gateway SHALL support adding, removing, and renaming response headers before returning to the consumer. | P0 | Plugin-based                       |
| FR-TR-003 | The gateway SHALL support request body transformation via configurable JSONPath mapping rules.    | P1       | Body-transform plugin              |
| FR-TR-004 | The gateway SHALL support response body transformation, including field redaction and field renaming. | P1 | Privacy/compatibility use cases    |
| FR-TR-005 | The gateway SHALL support URL rewriting (path prefix stripping and substitution).                 | P0       | Upstream sees clean paths          |
| FR-TR-006 | The gateway SHALL support CORS header injection with configurable origin, methods, and max-age.   | P0       | Browser-facing APIs                |
| FR-TR-007 | The gateway SHALL support response caching with configurable TTL per route.                       | P2       | Redis-backed cache                 |
| FR-TR-008 | The gateway SHALL forward only allow-listed request headers to upstream (header whitelist plugin). | P1       | Security hardening                 |

### 1.5 Domain: Developer Portal

| ID        | Requirement                                                                                       | Priority | Notes                                  |
|-----------|---------------------------------------------------------------------------------------------------|----------|----------------------------------------|
| FR-DP-001 | The developer portal SHALL allow users to self-register using email/password or OAuth 2.0 SSO (Google, GitHub). | P0 | Email verification required        |
| FR-DP-002 | The developer portal SHALL display a searchable, filterable catalogue of all published APIs with descriptions, versions, and status. | P0 | OpenAPI-powered                    |
| FR-DP-003 | The developer portal SHALL render interactive API documentation from uploaded OpenAPI 3.x specifications. | P0 | Swagger UI / Redoc integration     |
| FR-DP-004 | The developer portal SHALL allow developers to provision API keys for subscribed plans without admin approval (for self-service plans). | P0 | Instant issuance                   |
| FR-DP-005 | The developer portal SHALL provide a sandbox environment where developers can test APIs with mock responses. | P1 | Sandbox flag per key               |
| FR-DP-006 | The developer portal SHALL display per-key usage metrics (requests, errors, latency percentiles) in a dashboard. | P0 | Near-realtime (≤ 60 s lag)         |
| FR-DP-007 | The developer portal SHALL send email notifications for key expiry (7-day, 1-day advance warning) and quota breaches. | P1 | SMTP/SES integration               |
| FR-DP-008 | The developer portal SHALL allow developers to manage webhook subscriptions (CRUD endpoint URL, secret, event filters). | P1 | HMAC-SHA256 signature              |

### 1.6 Domain: Analytics & Observability

| ID        | Requirement                                                                                       | Priority | Notes                                  |
|-----------|---------------------------------------------------------------------------------------------------|----------|----------------------------------------|
| FR-AN-001 | The gateway SHALL emit a usage event for every proxied request, containing: timestamp, consumer ID, API ID, route, HTTP method, status code, upstream latency, total latency. | P0 | Published to BullMQ                |
| FR-AN-002 | The analytics service SHALL aggregate usage events into per-minute, per-hour, and per-day roll-ups in TimescaleDB/Postgres. | P0 | Background worker             |
| FR-AN-003 | The admin console SHALL provide charts for: total requests, error rate, p50/p95/p99 latency, top consumers, top APIs. | P0 | Time range selector: 1h, 24h, 7d, 30d |
| FR-AN-004 | The system SHALL support exporting raw usage data as CSV for a configurable date range.           | P1       | Async job with download link       |
| FR-AN-005 | The gateway SHALL expose Prometheus-compatible metrics at `/metrics` (scrape endpoint).           | P0       | Counter, histogram, gauge          |
| FR-AN-006 | The system SHALL integrate with OpenTelemetry and export traces to a configurable OTLP endpoint.  | P1       | Trace per request, span per plugin |
| FR-AN-007 | The system SHALL generate alerts when error rate exceeds a configurable threshold for a rolling 5-minute window. | P1 | PagerDuty / Slack integration  |

### 1.7 Domain: Subscription Management

| ID        | Requirement                                                                                       | Priority | Notes                                  |
|-----------|---------------------------------------------------------------------------------------------------|----------|----------------------------------------|
| FR-SM-001 | The system SHALL support multiple subscription plans (Free, Basic, Pro, Enterprise) with configurable rate limits and quota. | P0 | Admin-managed                      |
| FR-SM-002 | The system SHALL allow a consumer to subscribe to a plan via the developer portal.                | P0       | Immediate activation for self-service  |
| FR-SM-003 | The system SHALL support plan upgrades and downgrades; upgrades take effect immediately, downgrades at the next billing cycle. | P1 | Prorated billing via Razorpay      |
| FR-SM-004 | The system SHALL integrate with Razorpay to collect payment for paid subscription plans.          | P1       | Webhook for payment confirmation   |
| FR-SM-005 | The system SHALL suspend API key access when a paid subscription lapses (payment failure > 3 days). | P1 | Grace period configurable          |
| FR-SM-006 | The system SHALL allow API providers to create custom plans visible only to invited consumers.    | P2       | Private plans                      |

### 1.8 Domain: Webhooks

| ID        | Requirement                                                                                       | Priority | Notes                                  |
|-----------|---------------------------------------------------------------------------------------------------|----------|----------------------------------------|
| FR-WH-001 | The system SHALL deliver webhook payloads to consumer-registered HTTPS endpoints via POST with a JSON body. | P0 | TLS verification required          |
| FR-WH-002 | The system SHALL sign webhook payloads with HMAC-SHA256 using a per-endpoint secret and include the signature in `X-Webhook-Signature` header. | P0 | Consumers verify server-side       |
| FR-WH-003 | The system SHALL retry failed webhook deliveries with exponential back-off (1, 5, 25, 125 minutes) up to 5 attempts. | P0 | BullMQ delayed jobs                |
| FR-WH-004 | The system SHALL mark a webhook endpoint as disabled after 5 consecutive delivery failures and notify the consumer. | P1 | Re-enable via portal               |
| FR-WH-005 | The system SHALL allow consumers to rotate the webhook signing secret without downtime (dual-verify window of 30 minutes). | P1 | Old and new secret both accepted   |
| FR-WH-006 | The developer portal SHALL display a delivery log for each webhook endpoint (timestamp, status, attempt, response code). | P1 | 30-day retention                   |

### 1.9 Domain: API Versioning

| ID        | Requirement                                                                                       | Priority | Notes                                  |
|-----------|---------------------------------------------------------------------------------------------------|----------|----------------------------------------|
| FR-VR-001 | The gateway SHALL support URL-path versioning (`/v1/`, `/v2/`) and header-based versioning (`Accept-Version`). | P0 | Configurable per-API             |
| FR-VR-002 | The system SHALL allow providers to publish new API versions while keeping older versions active. | P0       | Concurrent versions               |
| FR-VR-003 | The system SHALL support deprecating a version: sends deprecation warning header `Deprecation` (RFC 8594) on all responses. | P1 | Sunset date configurable          |
| FR-VR-004 | The system SHALL support sunsetting a version: blocks all traffic after the sunset date and returns HTTP 410. | P1 | Advance notice emails to subscribers |
| FR-VR-005 | The developer portal SHALL show version lifecycle status (Draft, Active, Deprecated, Sunset) on the API catalogue. | P0 | Colour-coded badges               |
| FR-VR-006 | The system SHALL allow providers to upload an OpenAPI diff when publishing a new version to highlight breaking changes. | P2 | Optional changelog                |

### 1.10 Domain: Administration

| ID        | Requirement                                                                                       | Priority | Notes                                  |
|-----------|---------------------------------------------------------------------------------------------------|----------|----------------------------------------|
| FR-AD-001 | The admin console SHALL allow administrators to onboard new API providers and assign them to organisations. | P0 | RBAC: admin, provider, developer   |
| FR-AD-002 | The admin console SHALL allow administrators to approve or reject API publishing requests.        | P1       | Configurable; auto-approve available   |
| FR-AD-003 | The admin console SHALL allow administrators to create, edit, and delete subscription plans.      | P0       | Plan change triggers cache invalidation |
| FR-AD-004 | The admin console SHALL allow administrators to revoke any consumer's API key.                    | P0       | Immediate effect via Redis cache purge |
| FR-AD-005 | The admin console SHALL display a complete audit log of all administrative actions.               | P0       | Immutable, searchable              |
| FR-AD-006 | The admin console SHALL allow configuration of global plugins (e.g., request logging, IP blacklist). | P1 | Plugins applied before route-level plugins |
| FR-AD-007 | The system SHALL support SSO login for admin users via an enterprise OIDC provider.              | P1       | Okta / Azure AD                    |
| FR-AD-008 | The admin console SHALL allow administrators to configure alert thresholds and notification channels. | P1 | Per-metric thresholds              |

---

## 2. Non-Functional Requirements

### 2.1 Performance

| ID       | Requirement                                                                                             | Target               |
|----------|---------------------------------------------------------------------------------------------------------|----------------------|
| NFR-P-001 | Gateway proxy p99 latency (overhead, excluding upstream) SHALL be less than 5 ms under nominal load.   | p99 < 5 ms           |
| NFR-P-002 | Gateway SHALL sustain 50,000 requests per second (RPS) per ECS Fargate cluster under normal conditions.| 50,000 RPS           |
| NFR-P-003 | Developer portal page load (Time-to-Interactive) SHALL be below 3 s on a 4G connection.               | TTI < 3 s            |
| NFR-P-004 | Analytics dashboard queries for 24 h data SHALL complete in under 2 s.                                 | < 2 s                |

### 2.2 Availability & Reliability

| ID        | Requirement                                                                                            | Target               |
|-----------|--------------------------------------------------------------------------------------------------------|----------------------|
| NFR-A-001 | The gateway proxy tier SHALL achieve 99.95% monthly uptime (< 22 min downtime/month).                 | 99.95% uptime        |
| NFR-A-002 | The developer portal SHALL achieve 99.9% monthly uptime.                                              | 99.9% uptime         |
| NFR-A-003 | Gateway configuration changes SHALL be hot-reloaded without restarting worker processes.              | Zero-downtime reload |
| NFR-A-004 | The system SHALL survive the loss of a single AWS Availability Zone with automatic failover.          | Multi-AZ             |

### 2.3 Security

| ID        | Requirement                                                                                            | Notes                |
|-----------|--------------------------------------------------------------------------------------------------------|----------------------|
| NFR-S-001 | All external traffic SHALL be encrypted with TLS 1.2 or higher.                                       | TLS 1.3 preferred    |
| NFR-S-002 | API keys SHALL be stored as SHA-256 hashed values; the plaintext SHALL only be returned once at creation. | Irreversible hash |
| NFR-S-003 | The system SHALL pass OWASP API Security Top 10 assessment with no critical or high findings.          | Annual pentest       |
| NFR-S-004 | All sensitive operations SHALL be captured in an append-only audit log retained for 1 year.           | Compliance           |

### 2.4 Scalability

| ID        | Requirement                                                                                            | Notes                |
|-----------|--------------------------------------------------------------------------------------------------------|----------------------|
| NFR-SC-001| Gateway instances SHALL scale horizontally via ECS auto-scaling triggered by CPU > 60% or RPS > 40 K. | ECS target tracking  |
| NFR-SC-002| The system SHALL support at least 10,000 registered consumers and 100,000 active API keys.            | Db capacity planned  |

### 2.5 Maintainability

| ID        | Requirement                                                                                            | Notes                |
|-----------|--------------------------------------------------------------------------------------------------------|----------------------|
| NFR-M-001 | Unit test code coverage SHALL be ≥ 80% across all backend services.                                   | CI gate              |
| NFR-M-002 | Each service SHALL expose a structured `/health` and `/ready` endpoint conforming to the platform health-check standard. | Kubernetes / ECS     |

---

## 3. Constraints

- Must deploy on AWS ECS Fargate; no self-managed Kubernetes.
- Backend runtime: Node.js 20 LTS with Fastify 4.x.
- Frontend: Next.js 14 (App Router).
- Primary database: PostgreSQL 15.
- Cache/rate-limit store: Redis 7 (ElastiCache).
- Job queue: BullMQ 5 on Redis.
- Observability: OpenTelemetry SDK with OTLP export.
- Payment processor: Razorpay (India-first; Stripe as secondary).
- Open-source plugin architecture; no vendor lock-in for transformation logic.
