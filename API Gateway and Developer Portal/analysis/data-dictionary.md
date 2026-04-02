# Data Dictionary — API Gateway and Developer Portal

## Overview

This data dictionary defines all persistent entities, their fields, data types, constraints, and semantics for the **API Gateway and Developer Portal** platform. The primary data store is **PostgreSQL 15**. **Redis 7** is used for ephemeral caching and counters. All timestamps are stored in UTC as `TIMESTAMPTZ`. All monetary amounts are stored in integer cents (USD) unless otherwise noted.

Field naming follows `snake_case`. Primary keys are UUID v4 unless noted. Soft deletion is implemented via a `deleted_at` nullable timestamp column rather than physical row deletion, except for entities governed by hard-delete data retention rules.

---

## Core Entities

---

### Entity: ApiKey

Represents a credential issued to a Consumer Application for HMAC-SHA256 authenticated access to the API Gateway.

| Field Name | Data Type | Constraints | Description | Example Value |
|------------|-----------|-------------|-------------|---------------|
| `id` | UUID | PRIMARY KEY, NOT NULL | Unique identifier for the API key record. | `a3f1b2c4-dead-beef-0000-112233445566` |
| `consumer_id` | UUID | NOT NULL, FK → Consumer.id | The consumer account that owns this key. | `b9e0c1d2-1234-5678-abcd-ef0123456789` |
| `application_id` | UUID | NOT NULL, FK → Application.id | The application this key is scoped to. | `c1a2b3d4-0000-1111-2222-333344445555` |
| `key_prefix` | VARCHAR(8) | NOT NULL, UNIQUE | First 8 characters of the key, stored in plaintext for identification. Never the full key. | `sk_live_a` |
| `key_hash` | VARCHAR(64) | NOT NULL, UNIQUE | `HMAC-SHA256(key_prefix + key_secret, signing_secret)` hex-encoded. Used for constant-time validation. | `e3b0c44298fc1c149afb4c8996fb92427...` |
| `name` | VARCHAR(255) | NOT NULL | Human-readable label for the key assigned by the Developer. | `Production API Key` |
| `status` | ENUM(ApiKeyStatus) | NOT NULL, DEFAULT `ACTIVE` | Lifecycle status of the key. | `ACTIVE` |
| `scopes` | TEXT[] | NOT NULL, DEFAULT `{}` | Array of scope patterns (method + path glob). Empty array means all scopes permitted. | `["GET /v1/products/*", "POST /v1/orders"]` |
| `environment` | ENUM(Environment) | NOT NULL, DEFAULT `PRODUCTION` | Whether the key is for the sandbox or production gateway. | `PRODUCTION` |
| `expires_at` | TIMESTAMPTZ | NULLABLE | Optional hard expiry timestamp. Null means the key does not expire. | `2025-12-31T23:59:59Z` |
| `last_used_at` | TIMESTAMPTZ | NULLABLE | Timestamp of the most recent successful authentication. Updated asynchronously. | `2025-03-15T08:42:11Z` |
| `last_used_ip` | INET | NULLABLE | Source IP of the most recent successful use. Pseudonymised (last octet zeroed) before storage. | `192.168.1.0` |
| `rotation_expires_at` | TIMESTAMPTZ | NULLABLE | If set, the old key being replaced remains valid until this timestamp (key rotation overlap window). | `2025-03-16T08:00:00Z` |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Record creation timestamp. | `2024-11-01T10:00:00Z` |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last modification timestamp. Updated via trigger on any column change. | `2025-01-20T14:30:00Z` |
| `deleted_at` | TIMESTAMPTZ | NULLABLE | Soft-delete timestamp. Null = record is active. | `null` |
| `created_by` | UUID | NOT NULL, FK → Consumer.id | The consumer user who created the key (for audit trail). | `b9e0c1d2-1234-5678-abcd-ef0123456789` |
| `metadata` | JSONB | NOT NULL, DEFAULT `{}` | Arbitrary key-value metadata attached by the Developer (max 10 keys, 255 chars per value each). | `{"env": "prod", "team": "payments"}` |

---

### Entity: Consumer

Represents a registered developer or organisation account on the platform.

| Field Name | Data Type | Constraints | Description | Example Value |
|------------|-----------|-------------|-------------|---------------|
| `id` | UUID | PRIMARY KEY, NOT NULL | Unique identifier for the consumer account. | `b9e0c1d2-1234-5678-abcd-ef0123456789` |
| `email` | VARCHAR(320) | NOT NULL, UNIQUE | Primary email address. Used for login, notifications, and billing. | `jane.dev@example.com` |
| `email_verified` | BOOLEAN | NOT NULL, DEFAULT FALSE | Whether the email address has been verified via the confirmation link flow. | `true` |
| `name` | VARCHAR(255) | NOT NULL | Full name of the consumer (individual or primary contact person). | `Jane Doe` |
| `company` | VARCHAR(255) | NULLABLE | Organisation or company name, if applicable. | `Acme Corp` |
| `password_hash` | VARCHAR(255) | NULLABLE | `bcrypt(password, cost=12)`. Null for OAuth-only accounts that use SSO exclusively. | `$2b$12$eW5H...` |
| `oauth_provider` | VARCHAR(64) | NULLABLE | IdP name if the consumer registered via SSO (e.g., `github`, `google`). | `github` |
| `oauth_subject` | VARCHAR(255) | NULLABLE | Subject claim from the IdP for SSO-linked accounts. | `user_01HJKL...` |
| `status` | ENUM(ConsumerStatus) | NOT NULL, DEFAULT `PENDING_VERIFICATION` | Account lifecycle status controlling platform access. | `ACTIVE` |
| `role` | ENUM(UserRole) | NOT NULL, DEFAULT `DEVELOPER` | Platform role determining portal and API access level. | `DEVELOPER` |
| `plan_id` | UUID | NOT NULL, FK → SubscriptionPlan.id | Currently active subscription plan. | `d5e6f7a8-plan-0001...` |
| `pending_plan_id` | UUID | NULLABLE, FK → SubscriptionPlan.id | Scheduled plan change taking effect at `plan_change_at`. | `null` |
| `plan_change_at` | TIMESTAMPTZ | NULLABLE | Timestamp when the `pending_plan_id` transitions to the active plan. | `2025-04-01T00:00:00Z` |
| `stripe_customer_id` | VARCHAR(64) | NULLABLE | Stripe Customer object ID for subscription billing. | `cus_Oa8bH1Jk2lM3nP` |
| `stripe_subscription_id` | VARCHAR(64) | NULLABLE | Active Stripe Subscription object ID. | `sub_1OzQr2Lk...` |
| `trial_ends_at` | TIMESTAMPTZ | NULLABLE | End of free trial period. Null if the consumer is not on a trial. | `2025-04-15T23:59:59Z` |
| `quota_reset_at` | TIMESTAMPTZ | NOT NULL | Next monthly quota reset timestamp (derived from Stripe billing cycle start). | `2025-04-01T00:00:00Z` |
| `timezone` | VARCHAR(64) | NOT NULL, DEFAULT `UTC` | IANA timezone identifier used for display-only purposes in the portal. | `America/New_York` |
| `notification_prefs` | JSONB | NOT NULL, DEFAULT `{"quota_warning": true, "webhook_failure": true, "billing": true}` | Consumer's email notification preference flags per category. | `{"quota_warning": true, "webhook_failure": false}` |
| `mfa_enabled` | BOOLEAN | NOT NULL, DEFAULT FALSE | Whether TOTP multi-factor authentication is active for this account. | `true` |
| `mfa_secret` | VARCHAR(255) | NULLABLE | AES-256-CBC encrypted TOTP secret. Null if MFA is not enabled. | `ENCRYPTED:v1:...` |
| `last_login_at` | TIMESTAMPTZ | NULLABLE | Timestamp of the most recent successful portal login. | `2025-03-10T09:15:00Z` |
| `last_login_ip` | INET | NULLABLE | Pseudonymised IP address of the most recent successful login. | `203.0.113.0` |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Account creation timestamp. | `2024-06-01T12:00:00Z` |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last modification timestamp. | `2025-02-20T16:45:00Z` |
| `deleted_at` | TIMESTAMPTZ | NULLABLE | Soft-delete / account-closure timestamp. Null = account is active. | `null` |

---

### Entity: Application

Represents a logical grouping of API keys and webhook subscriptions owned by a Consumer for a specific project or product.

| Field Name | Data Type | Constraints | Description | Example Value |
|------------|-----------|-------------|-------------|---------------|
| `id` | UUID | PRIMARY KEY, NOT NULL | Unique identifier for the application. | `c1a2b3d4-0000-1111-2222-333344445555` |
| `consumer_id` | UUID | NOT NULL, FK → Consumer.id ON DELETE CASCADE | Owning consumer account. Cascade deletes all child records. | `b9e0c1d2-1234-5678-abcd-ef0123456789` |
| `name` | VARCHAR(255) | NOT NULL | Developer-assigned name for the application. | `Payments Frontend` |
| `description` | TEXT | NULLABLE | Optional description of the application's purpose or use case. | `React SPA for consumer checkout` |
| `homepage_url` | VARCHAR(2048) | NULLABLE | URL of the application's homepage or product page. | `https://app.acme.com` |
| `callback_urls` | TEXT[] | NOT NULL, DEFAULT `{}` | Allowed OAuth redirect URIs for authorization_code flows. | `["https://app.acme.com/callback"]` |
| `logo_url` | VARCHAR(2048) | NULLABLE | URL of the application logo image stored in S3 via CloudFront. | `https://cdn.domain.com/app_logos/c1a2b3d4.png` |
| `environment` | ENUM(Environment) | NOT NULL, DEFAULT `PRODUCTION` | Whether this is a sandbox or production application context. | `PRODUCTION` |
| `status` | ENUM(ApplicationStatus) | NOT NULL, DEFAULT `ACTIVE` | Lifecycle status: ACTIVE, SUSPENDED, DELETED. | `ACTIVE` |
| `api_key_count` | SMALLINT | NOT NULL, DEFAULT 0 | Cached count of active API keys. Maintained by PostgreSQL trigger. | `2` |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Record creation timestamp. | `2024-07-15T08:00:00Z` |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last modification timestamp. | `2025-01-05T11:30:00Z` |
| `deleted_at` | TIMESTAMPTZ | NULLABLE | Soft-delete timestamp. Null = application is active. | `null` |

---

### Entity: SubscriptionPlan

Defines the rate-limit quotas, feature flags, and pricing for a tier of API access.

| Field Name | Data Type | Constraints | Description | Example Value |
|------------|-----------|-------------|-------------|---------------|
| `id` | UUID | PRIMARY KEY, NOT NULL | Unique identifier for the plan. | `d5e6f7a8-plan-0001-0000-000000000001` |
| `name` | VARCHAR(100) | NOT NULL, UNIQUE | Display name of the plan shown in the portal catalogue. | `Pro` |
| `slug` | VARCHAR(50) | NOT NULL, UNIQUE | URL-safe identifier used in API responses and Stripe metadata. | `pro` |
| `description` | TEXT | NULLABLE | Marketing description shown in the public plan catalogue. | `Best for growing teams and production workloads` |
| `is_public` | BOOLEAN | NOT NULL, DEFAULT TRUE | Whether the plan is visible in the public plan catalogue. False for Enterprise. | `true` |
| `status` | ENUM(PlanStatus) | NOT NULL, DEFAULT `ACTIVE` | Lifecycle status: ACTIVE, DEPRECATED, RETIRED. | `ACTIVE` |
| `price_monthly_usd_cents` | INTEGER | NOT NULL, DEFAULT 0 | Monthly price in US cents. Zero for free plans. | `4900` |
| `price_yearly_usd_cents` | INTEGER | NOT NULL, DEFAULT 0 | Annual price in US cents when yearly billing is selected. | `49000` |
| `stripe_price_id_monthly` | VARCHAR(64) | NULLABLE | Stripe Price object ID for monthly billing cycle. | `price_1OzQr2Lk...` |
| `stripe_price_id_yearly` | VARCHAR(64) | NULLABLE | Stripe Price object ID for annual billing cycle. | `price_1OzQr3Lk...` |
| `requests_per_minute` | INTEGER | NOT NULL | Maximum requests per minute per consumer on this plan. | `1000` |
| `requests_per_day` | INTEGER | NOT NULL | Maximum requests per UTC calendar day per consumer. | `50000` |
| `requests_per_month` | INTEGER | NOT NULL | Maximum requests per billing cycle per consumer. | `1000000` |
| `burst_multiplier` | NUMERIC(4,2) | NOT NULL, DEFAULT 1.0 | Multiplier applied to `requests_per_minute` for burst token bucket. 1.5 = 50% burst. | `1.5` |
| `max_api_keys_per_app` | SMALLINT | NOT NULL, DEFAULT 2 | Maximum active API keys per Application under this plan. | `10` |
| `max_applications` | SMALLINT | NOT NULL, DEFAULT 5 | Maximum number of Applications per Consumer under this plan. | `25` |
| `max_webhooks_per_app` | SMALLINT | NOT NULL, DEFAULT 0 | Maximum webhook subscriptions per Application. Zero means feature is disabled. | `10` |
| `webhook_enabled` | BOOLEAN | NOT NULL, DEFAULT FALSE | Whether the webhook delivery feature is available on this plan. | `true` |
| `analytics_export_enabled` | BOOLEAN | NOT NULL, DEFAULT FALSE | Whether the analytics CSV / Parquet data export feature is available. | `true` |
| `custom_domain_enabled` | BOOLEAN | NOT NULL, DEFAULT FALSE | Whether custom gateway domain routing (CNAME-based) is available. | `false` |
| `sla_uptime_pct` | NUMERIC(6,3) | NULLABLE | Published uptime SLA percentage for this plan. Null = no SLA published. | `99.950` |
| `overage_billing_enabled` | BOOLEAN | NOT NULL, DEFAULT FALSE | Whether metered overage billing is active beyond monthly quota. | `true` |
| `overage_price_per_1k_cents` | INTEGER | NULLABLE | Price in US cents per 1,000 overage requests. Null if overage not enabled. | `50` |
| `trial_days` | SMALLINT | NOT NULL, DEFAULT 0 | Number of free trial days offered to new subscribers on this plan. | `14` |
| `feature_flags` | JSONB | NOT NULL, DEFAULT `{}` | Additional extensible feature toggles specific to this plan version. | `{"graphql_proxy": true}` |
| `sort_order` | SMALLINT | NOT NULL, DEFAULT 0 | Display order in the public plan catalogue (ascending integer). | `2` |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Record creation timestamp. | `2024-01-01T00:00:00Z` |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last modification timestamp. | `2025-01-15T10:00:00Z` |

---

### Entity: ApiRoute

Defines a proxied API endpoint registered by an API Provider, including upstream target, authentication requirements, and policies.

| Field Name | Data Type | Constraints | Description | Example Value |
|------------|-----------|-------------|-------------|---------------|
| `id` | UUID | PRIMARY KEY, NOT NULL | Unique identifier for the route record. | `e9f0a1b2-0000-aaaa-bbbb-ccccddddeeee` |
| `provider_id` | UUID | NOT NULL, FK → Consumer.id | The API Provider account that registered and manages this route. | `f1e2d3c4-prov-0001-0000-111122223333` |
| `api_version_id` | UUID | NOT NULL, FK → ApiVersion.id | The API version this route belongs to. | `a0b1c2d3-ver-0001-0000-000011112222` |
| `name` | VARCHAR(255) | NOT NULL | Human-readable route name shown in the portal API catalogue. | `List Products` |
| `description` | TEXT | NULLABLE | Detailed description of the route's purpose and behaviour. | `Returns a paginated list of products matching query filters` |
| `path_pattern` | VARCHAR(1024) | NOT NULL | Incoming request path pattern supporting `{param}` named placeholders. | `/v1/products/{productId}` |
| `http_methods` | TEXT[] | NOT NULL | Allowed HTTP methods for this route (e.g., GET, POST, PUT, DELETE). | `["GET", "HEAD"]` |
| `upstream_url` | VARCHAR(2048) | NOT NULL | Full base URL of the upstream service this route proxies to. | `https://products-svc.internal.acme.com` |
| `upstream_path` | VARCHAR(1024) | NOT NULL | Path pattern on the upstream service. May differ from `path_pattern`. | `/api/v2/products/{productId}` |
| `upstream_timeout_ms` | INTEGER | NOT NULL, DEFAULT 30000 | Maximum time in milliseconds to wait for the upstream response before aborting. | `10000` |
| `strip_path_prefix` | BOOLEAN | NOT NULL, DEFAULT FALSE | Whether to remove the versioned path prefix when forwarding to upstream. | `true` |
| `auth_required` | BOOLEAN | NOT NULL, DEFAULT TRUE | Whether authentication (API key or JWT) is required to access this route. | `true` |
| `classification` | ENUM(RouteClassification) | NOT NULL, DEFAULT `STANDARD` | Data sensitivity classification affecting request/response body logging. | `STANDARD` |
| `status` | ENUM(RouteStatus) | NOT NULL, DEFAULT `ACTIVE` | Lifecycle status: ACTIVE, INACTIVE, DEPRECATED, RETIRED. | `ACTIVE` |
| `rate_limit_policy_id` | UUID | NULLABLE, FK → RateLimitPolicy.id | Optional route-level rate-limit policy override. Null = plan-level policy applies. | `null` |
| `plugin_ids` | UUID[] | NOT NULL, DEFAULT `{}` | Ordered array of GatewayPlugin IDs applied to this route's pipeline. | `["plug-cors-0001", "plug-cache-0002"]` |
| `request_transform` | JSONB | NULLABLE | Header or body transformation rules applied to inbound requests before forwarding. | `{"headers": {"add": {"X-Source": "gateway"}}}` |
| `response_transform` | JSONB | NULLABLE | Transformation rules applied to the upstream response before returning to the client. | `null` |
| `health_check_path` | VARCHAR(1024) | NULLABLE | Path on the upstream service used for active health check polling. | `/health` |
| `health_check_interval_s` | SMALLINT | NOT NULL, DEFAULT 30 | Active health check polling interval in seconds. | `30` |
| `tags` | TEXT[] | NOT NULL, DEFAULT `{}` | Searchable tags enabling API catalogue filtering by topic or domain. | `["payments", "public", "stable"]` |
| `documentation_url` | VARCHAR(2048) | NULLABLE | URL to the OpenAPI specification or documentation page for this route. | `https://portal.domain.com/docs/products/v1` |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Record creation timestamp. | `2024-03-01T09:00:00Z` |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last modification timestamp. | `2025-02-01T14:00:00Z` |
| `deleted_at` | TIMESTAMPTZ | NULLABLE | Soft-delete timestamp. Null = route is active. | `null` |

---

### Entity: RateLimitPolicy

Defines a named, reusable rate-limit configuration that can be applied at the plan level or route level.

| Field Name | Data Type | Constraints | Description | Example Value |
|------------|-----------|-------------|-------------|---------------|
| `id` | UUID | PRIMARY KEY, NOT NULL | Unique identifier for the rate-limit policy. | `f0e1d2c3-rlp-0001-0000-aabbccddeeff` |
| `name` | VARCHAR(255) | NOT NULL | Descriptive name for the policy used in Admin Console. | `Strict Payments Route Limit` |
| `scope` | ENUM(PolicyScope) | NOT NULL | Whether this policy is applied at PLAN or ROUTE level. | `ROUTE` |
| `requests_per_second` | INTEGER | NULLABLE | Maximum requests per second. Null = no per-second limit enforced. | `null` |
| `requests_per_minute` | INTEGER | NOT NULL | Maximum requests per 60-second sliding window. | `100` |
| `requests_per_hour` | INTEGER | NULLABLE | Maximum requests per 60-minute rolling window. Null = no hourly limit. | `3000` |
| `requests_per_day` | INTEGER | NOT NULL | Maximum requests per UTC calendar day. | `10000` |
| `burst_enabled` | BOOLEAN | NOT NULL, DEFAULT FALSE | Whether burst allowance over the per-minute limit is permitted. | `false` |
| `burst_multiplier` | NUMERIC(4,2) | NULLABLE | Burst ceiling as a multiple of `requests_per_minute`. Null if burst disabled. | `null` |
| `concurrent_connections_limit` | SMALLINT | NULLABLE | Maximum simultaneous long-lived connections per consumer. Null = no limit. | `20` |
| `strategy` | ENUM(RateLimitStrategy) | NOT NULL, DEFAULT `SLIDING_WINDOW` | Counter algorithm: SLIDING_WINDOW, FIXED_WINDOW, or TOKEN_BUCKET. | `SLIDING_WINDOW` |
| `key_dimension` | ENUM(RateLimitKeyDimension) | NOT NULL, DEFAULT `CONSUMER` | Counter partition dimension: CONSUMER, IP, API_KEY, or ROUTE_CONSUMER. | `CONSUMER` |
| `quota_exceeded_action` | ENUM(QuotaExceededAction) | NOT NULL, DEFAULT `REJECT` | Action when quota is exhausted: REJECT (HTTP 429) or THROTTLE (delayed response). | `REJECT` |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Record creation timestamp. | `2024-02-01T00:00:00Z` |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last modification timestamp. | `2024-06-15T12:00:00Z` |

---

### Entity: WebhookSubscription

Represents a consumer's subscription to receive platform event notifications at a specified HTTPS endpoint.

| Field Name | Data Type | Constraints | Description | Example Value |
|------------|-----------|-------------|-------------|---------------|
| `id` | UUID | PRIMARY KEY, NOT NULL | Unique identifier for the webhook subscription record. | `a1b2c3d4-whs-0001-0000-112233445566` |
| `consumer_id` | UUID | NOT NULL, FK → Consumer.id | The consumer account that owns this webhook subscription. | `b9e0c1d2-1234-5678-abcd-ef0123456789` |
| `application_id` | UUID | NOT NULL, FK → Application.id | The application that this webhook subscription is associated with. | `c1a2b3d4-0000-1111-2222-333344445555` |
| `target_url` | VARCHAR(2048) | NOT NULL | HTTPS URL to which event payload POST requests are delivered. | `https://app.acme.com/webhooks/gateway` |
| `secret_hash` | VARCHAR(255) | NOT NULL | Encrypted webhook signing secret (AES-256-CBC via pgcrypto + KMS key). Used to derive HMAC-SHA256 payload signature. | `ENCRYPTED:v1:iv:ciphertext` |
| `event_types` | TEXT[] | NOT NULL | Array of event type patterns this subscription listens to. Supports `*` wildcards. | `["ratelimit.quota.exceeded", "webhook.delivery.failed"]` |
| `status` | ENUM(WebhookStatus) | NOT NULL, DEFAULT `PENDING_VERIFICATION` | Lifecycle: PENDING_VERIFICATION, ACTIVE, SUSPENDED, FAILED, DELETED. | `ACTIVE` |
| `verified_at` | TIMESTAMPTZ | NULLABLE | Timestamp when the endpoint ownership was successfully verified. | `2025-01-10T10:05:33Z` |
| `failure_rate_7d` | NUMERIC(5,2) | NOT NULL, DEFAULT 0.00 | Rolling 7-day delivery failure rate percentage (0.00 to 100.00). Updated nightly. | `0.00` |
| `last_delivery_at` | TIMESTAMPTZ | NULLABLE | Timestamp of the most recent delivery attempt regardless of outcome. | `2025-03-14T07:22:05Z` |
| `last_delivery_status` | ENUM(DeliveryStatus) | NULLABLE | Outcome of the most recent delivery attempt. | `SUCCESS` |
| `total_deliveries` | INTEGER | NOT NULL, DEFAULT 0 | Cumulative total of all delivery attempts since subscription creation. | `1482` |
| `total_failures` | INTEGER | NOT NULL, DEFAULT 0 | Cumulative total of failed delivery attempts since subscription creation. | `3` |
| `description` | VARCHAR(255) | NULLABLE | Developer-assigned plain-text description of the webhook's purpose. | `Notify Slack on quota exceeded` |
| `max_retries` | SMALLINT | NOT NULL, DEFAULT 5 | Maximum number of BullMQ retry attempts before moving to the Dead Letter Queue. | `5` |
| `api_version` | VARCHAR(10) | NOT NULL, DEFAULT `v1` | Event payload schema version this subscription is configured to receive. | `v1` |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Record creation timestamp. | `2025-01-10T10:00:00Z` |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last modification timestamp. | `2025-02-28T15:00:00Z` |
| `deleted_at` | TIMESTAMPTZ | NULLABLE | Soft-delete timestamp. Null = subscription is active. | `null` |

---

### Entity: ApiVersion

Represents a major version of an API registered on the platform, grouping related API routes under a common versioned namespace.

| Field Name | Data Type | Constraints | Description | Example Value |
|------------|-----------|-------------|-------------|---------------|
| `id` | UUID | PRIMARY KEY, NOT NULL | Unique identifier for the API version record. | `a0b1c2d3-ver-0001-0000-000011112222` |
| `provider_id` | UUID | NOT NULL, FK → Consumer.id | The API Provider account that owns and manages this version. | `f1e2d3c4-prov-0001-0000-111122223333` |
| `api_name` | VARCHAR(255) | NOT NULL | Name of the API product this version belongs to (e.g., "Payments API"). | `Payments API` |
| `major_version` | SMALLINT | NOT NULL, CHECK (major_version > 0) | Monotonically increasing major version integer (1, 2, 3…). | `2` |
| `version_label` | VARCHAR(20) | NOT NULL | Human-readable display label (e.g., "v2", "v2-beta"). Unique per provider + api_name. | `v2` |
| `changelog_url` | VARCHAR(2048) | NULLABLE | URL to the version changelog or release notes document. | `https://portal.domain.com/docs/payments/v2/changelog` |
| `openapi_spec_url` | VARCHAR(2048) | NULLABLE | URL to the OpenAPI 3.0 YAML/JSON specification for this version. | `https://portal.domain.com/specs/payments-v2.yaml` |
| `status` | ENUM(ApiVersionStatus) | NOT NULL, DEFAULT `ACTIVE` | Lifecycle: DRAFT, ACTIVE, DEPRECATED, RETIRED. | `ACTIVE` |
| `deprecated_at` | TIMESTAMPTZ | NULLABLE | Timestamp when this version entered DEPRECATED status. | `null` |
| `sunset_at` | TIMESTAMPTZ | NULLABLE | Scheduled retirement date. Must be at least 90 days after `deprecated_at`. | `null` |
| `retired_at` | TIMESTAMPTZ | NULLABLE | Actual timestamp when the version was transitioned to RETIRED and routes were disabled. | `null` |
| `successor_version_id` | UUID | NULLABLE, FK → ApiVersion.id | Points to the replacement version shown in deprecation notices. | `null` |
| `active_consumer_count` | INTEGER | NOT NULL, DEFAULT 0 | Cached count of consumers generating active traffic on this version. Refreshed by analytics job. | `347` |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Record creation timestamp. | `2024-05-01T00:00:00Z` |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last modification timestamp. | `2025-01-30T09:00:00Z` |

---

### Entity: AnalyticsEvent

Records each gateway request event for usage analytics, quota billing, and capacity planning. High-volume table partitioned by month on `event_time`.

| Field Name | Data Type | Constraints | Description | Example Value |
|------------|-----------|-------------|-------------|---------------|
| `id` | UUID | NOT NULL (partition key) | Unique identifier for each analytics event record. | `e1f2a3b4-evt-0001-0000-aabbccddeeff` |
| `event_time` | TIMESTAMPTZ | NOT NULL (partition key) | Timestamp when the request was received at the gateway ingress. | `2025-03-15T08:42:11.123Z` |
| `consumer_id` | UUID | NOT NULL, FK → Consumer.id | Consumer account that originated the request. | `b9e0c1d2-...` |
| `api_key_id` | UUID | NULLABLE, FK → ApiKey.id | API key used for authentication. Null when JWT Bearer auth is used. | `a3f1b2c4-...` |
| `route_id` | UUID | NOT NULL, FK → ApiRoute.id | The API route record that matched and handled the request. | `e9f0a1b2-...` |
| `api_version_id` | UUID | NOT NULL, FK → ApiVersion.id | The API version that the matched route belongs to. | `a0b1c2d3-...` |
| `http_method` | VARCHAR(10) | NOT NULL | HTTP method of the inbound request (GET, POST, PUT, PATCH, DELETE…). | `GET` |
| `request_path` | VARCHAR(2048) | NOT NULL | Actual request path. Truncated to 2048 chars. Query params excluded for PII routes. | `/v1/products/12345` |
| `status_code` | SMALLINT | NOT NULL | HTTP status code returned to the calling client. | `200` |
| `upstream_status_code` | SMALLINT | NULLABLE | HTTP status code from the upstream service. Null if upstream was not reached. | `200` |
| `latency_ms` | INTEGER | NOT NULL | Total end-to-end processing time in milliseconds measured at the gateway. | `45` |
| `upstream_latency_ms` | INTEGER | NULLABLE | Time from gateway forwarding the request to receiving the upstream response. | `38` |
| `request_size_bytes` | INTEGER | NOT NULL, DEFAULT 0 | Size of the inbound request body in bytes (0 for requests without a body). | `0` |
| `response_size_bytes` | INTEGER | NOT NULL, DEFAULT 0 | Size of the response body returned to the client in bytes. | `4096` |
| `source_ip` | INET | NOT NULL | Pseudonymised source IP address (last IPv4 octet zeroed before storage). | `203.0.113.0` |
| `user_agent` | TEXT | NULLABLE | `User-Agent` header value, truncated to the first 512 characters. | `python-requests/2.31.0` |
| `gateway_instance_id` | VARCHAR(64) | NOT NULL | ECS task ID of the specific gateway container that processed this request. | `ecs-task-abc123` |
| `auth_type` | ENUM(AuthType) | NOT NULL | Authentication method used: API_KEY, JWT, or NONE. | `API_KEY` |
| `rate_limited` | BOOLEAN | NOT NULL, DEFAULT FALSE | True if this event corresponds to a rate-limited (HTTP 429) response. | `false` |
| `cache_hit` | BOOLEAN | NOT NULL, DEFAULT FALSE | True if the response was served from the gateway response-cache plugin. | `false` |
| `error_code` | VARCHAR(64) | NULLABLE | Machine-readable error code string for non-2xx responses. | `null` |
| `trace_id` | VARCHAR(128) | NULLABLE | OpenTelemetry W3C trace-context trace ID for distributed tracing correlation. | `4bf92f3577b34da6a3ce929d0e0e4736` |

---

### Entity: OAuthClient

Represents an OAuth 2.0 client application registered on the platform for machine-to-machine (M2M) or authorisation-code flows.

| Field Name | Data Type | Constraints | Description | Example Value |
|------------|-----------|-------------|-------------|---------------|
| `id` | UUID | PRIMARY KEY, NOT NULL | Unique identifier for the OAuth client record. | `b2c3d4e5-oac-0001-0000-aabbccddeeff` |
| `consumer_id` | UUID | NOT NULL, FK → Consumer.id | The consumer account that registered and owns this OAuth client. | `b9e0c1d2-...` |
| `application_id` | UUID | NOT NULL, FK → Application.id | The application this OAuth client is associated with. | `c1a2b3d4-...` |
| `client_id` | VARCHAR(64) | NOT NULL, UNIQUE | Publicly visible OAuth client identifier used in token requests. | `client_01HJKL9MN2PQ3RS4TU5VW6XY` |
| `client_secret_hash` | VARCHAR(255) | NOT NULL | `bcrypt(client_secret, cost=12)`. The plaintext secret is shown exactly once at creation. | `$2b$12$...` |
| `client_name` | VARCHAR(255) | NOT NULL | Human-readable display name of the OAuth client shown in consent screens. | `Acme M2M Service` |
| `grant_types` | TEXT[] | NOT NULL | Allowed OAuth 2.0 grant types: `client_credentials`, `authorization_code`, `refresh_token`. | `["client_credentials"]` |
| `redirect_uris` | TEXT[] | NOT NULL, DEFAULT `{}` | Allowed redirect URIs for authorization_code grant flows. Must be HTTPS. | `["https://app.acme.com/callback"]` |
| `scopes` | TEXT[] | NOT NULL | Allowed OAuth scopes this client is permitted to request access tokens for. | `["read:orders", "write:orders"]` |
| `token_endpoint_auth_method` | ENUM(TokenAuthMethod) | NOT NULL, DEFAULT `client_secret_basic` | Method used to authenticate the client at the token endpoint. | `client_secret_basic` |
| `access_token_ttl_s` | INTEGER | NOT NULL, DEFAULT 3600 | Lifetime of issued access tokens in seconds. | `3600` |
| `refresh_token_ttl_s` | INTEGER | NULLABLE | Lifetime of issued refresh tokens in seconds. Null if refresh tokens are not issued. | `2592000` |
| `status` | ENUM(OAuthClientStatus) | NOT NULL, DEFAULT `ACTIVE` | Lifecycle status: ACTIVE, SUSPENDED, REVOKED. | `ACTIVE` |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Record creation timestamp. | `2024-09-01T00:00:00Z` |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last modification timestamp. | `2025-01-20T12:00:00Z` |

---

### Entity: OAuthToken

Represents an issued OAuth 2.0 access token or refresh token, stored by hash for introspection and revocation support.

| Field Name | Data Type | Constraints | Description | Example Value |
|------------|-----------|-------------|-------------|---------------|
| `id` | UUID | PRIMARY KEY, NOT NULL | Unique identifier for the OAuth token record. | `c3d4e5f6-oat-0001-0000-aabbccddeeff` |
| `client_id` | UUID | NOT NULL, FK → OAuthClient.id | The OAuth client that was issued this token. | `b2c3d4e5-...` |
| `consumer_id` | UUID | NOT NULL, FK → Consumer.id | The consumer account associated with the token issuance. | `b9e0c1d2-...` |
| `token_hash` | VARCHAR(255) | NOT NULL, UNIQUE | `SHA-256(token_value)` hex-encoded. Used for token lookup during introspection without storing plaintext. | `a665a45920422f9d417e4867efdc4fb8...` |
| `token_type` | ENUM(OAuthTokenType) | NOT NULL | Token type: ACCESS token or REFRESH token. | `ACCESS` |
| `scopes` | TEXT[] | NOT NULL | The specific scopes granted to this token instance. Subset of the client's allowed scopes. | `["read:orders"]` |
| `issued_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Timestamp when the token was generated and issued. | `2025-03-15T09:00:00Z` |
| `expires_at` | TIMESTAMPTZ | NOT NULL | Timestamp when the token expires and will be rejected. Enforced on every use. | `2025-03-15T10:00:00Z` |
| `revoked_at` | TIMESTAMPTZ | NULLABLE | Timestamp when the token was explicitly revoked. Null = token has not been revoked. | `null` |
| `last_used_at` | TIMESTAMPTZ | NULLABLE | Timestamp of the most recent successful use of this token for authentication. | `2025-03-15T09:45:00Z` |
| `grant_type` | VARCHAR(50) | NOT NULL | The OAuth grant type that produced this token issuance. | `client_credentials` |
| `refresh_token_id` | UUID | NULLABLE, FK → OAuthToken.id | For access tokens issued via a refresh, references the parent refresh token record. | `null` |

---

### Entity: GatewayPlugin

Represents a plugin instance installed and configured on the gateway to extend or modify the request processing pipeline.

| Field Name | Data Type | Constraints | Description | Example Value |
|------------|-----------|-------------|-------------|---------------|
| `id` | UUID | PRIMARY KEY, NOT NULL | Unique identifier for the plugin instance record. | `d4e5f6a7-plg-0001-0000-aabbccddeeff` |
| `name` | VARCHAR(100) | NOT NULL | Machine-readable identifier for the plugin type (e.g., `cors`, `cache`, `transform`). | `cors` |
| `display_name` | VARCHAR(255) | NOT NULL | Human-readable display name shown in the Admin Console. | `CORS Plugin` |
| `version` | VARCHAR(20) | NOT NULL | Semantic version string of the installed plugin implementation. | `2.3.1` |
| `scope` | ENUM(PluginScope) | NOT NULL | Attachment scope: GLOBAL (all routes), ROUTE (specific route), or CONSUMER (specific consumer). | `ROUTE` |
| `route_id` | UUID | NULLABLE, FK → ApiRoute.id | The route this plugin is attached to. Null if scope is GLOBAL or CONSUMER. | `e9f0a1b2-...` |
| `consumer_id` | UUID | NULLABLE, FK → Consumer.id | The consumer this plugin is scoped to. Null if scope is GLOBAL or ROUTE. | `null` |
| `config` | JSONB | NOT NULL | Plugin-specific configuration object. Validated at write time against the plugin's JSON Schema document. | `{"origins": ["*"], "methods": ["GET","POST"], "max_age": 3600}` |
| `enabled` | BOOLEAN | NOT NULL, DEFAULT TRUE | Whether this plugin instance is currently active in the request pipeline. | `true` |
| `execution_order` | SMALLINT | NOT NULL, DEFAULT 100 | Numeric priority determining the order of plugin execution (lower = executed earlier). | `10` |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Record creation timestamp. | `2024-04-01T00:00:00Z` |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last modification timestamp, updated on any config or status change. | `2025-03-01T09:00:00Z` |
| `configured_by` | UUID | NOT NULL, FK → Consumer.id | ID of the Admin user who created or last updated this plugin instance. | `admin-uuid-0001` |

---

### Entity: AuditLog

Immutable append-only record of every state-mutating action performed by any actor on the platform. Enforced by PostgreSQL row-level security policies.

| Field Name | Data Type | Constraints | Description | Example Value |
|------------|-----------|-------------|-------------|---------------|
| `id` | UUID | NOT NULL | Unique identifier for each audit log entry. | `e5f6a7b8-aud-0001-0000-aabbccddeeff` |
| `actor_id` | UUID | NULLABLE | Consumer ID of the actor who performed the action. Null for system-initiated background actions. | `admin-uuid-0001` |
| `actor_role` | ENUM(UserRole) | NOT NULL | Platform role of the actor at the time the action was performed. | `ADMIN` |
| `actor_ip` | INET | NOT NULL | Pseudonymised source IP address of the actor (last IPv4 octet zeroed). | `10.0.1.0` |
| `action` | VARCHAR(100) | NOT NULL | Machine-readable action identifier following the pattern `{entity}.{verb}` (e.g., `api_key.create`). | `consumer.plan.upgraded` |
| `entity_type` | VARCHAR(100) | NOT NULL | Name of the data entity type that was affected by the action. | `Consumer` |
| `entity_id` | UUID | NOT NULL | Primary key value of the affected entity record. | `b9e0c1d2-...` |
| `before_state` | JSONB | NULLABLE | JSON snapshot of the entity's relevant fields immediately before the change. | `{"plan_id": "free-plan-uuid"}` |
| `after_state` | JSONB | NULLABLE | JSON snapshot of the entity's relevant fields immediately after the change. | `{"plan_id": "pro-plan-uuid"}` |
| `trace_id` | VARCHAR(128) | NOT NULL | OpenTelemetry W3C trace ID correlating this audit entry to the full distributed trace. | `4bf92f3577b34da6a3ce929d0e0e4736` |
| `session_id` | VARCHAR(128) | NULLABLE | Hashed portal session identifier at the time of the action. Null for API or system actions. | `sess_hash_abc123` |
| `occurred_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Timestamp of the action. Set at insert time; immutable thereafter. | `2025-03-10T14:00:00Z` |
| `source` | ENUM(AuditSource) | NOT NULL | Origin of the action: PORTAL_UI, MANAGEMENT_API, SYSTEM, or WEBHOOK. | `PORTAL_UI` |
| `result` | ENUM(AuditResult) | NOT NULL | Whether the action succeeded (SUCCESS) or failed (FAILURE). | `SUCCESS` |
| `failure_reason` | TEXT | NULLABLE | Human-readable explanation of why the action failed. Null for successful actions. | `null` |

---

### Entity: Alert

Represents a triggered monitoring alert for a consumer, API route, or platform-wide threshold breach.

| Field Name | Data Type | Constraints | Description | Example Value |
|------------|-----------|-------------|-------------|---------------|
| `id` | UUID | PRIMARY KEY, NOT NULL | Unique identifier for the alert record. | `f6a7b8c9-alt-0001-0000-aabbccddeeff` |
| `alert_type` | ENUM(AlertType) | NOT NULL | Alert category: QUOTA_WARNING, QUOTA_EXCEEDED, UPSTREAM_DEGRADED, ERROR_RATE, LATENCY_P99, SECURITY. | `QUOTA_WARNING` |
| `severity` | ENUM(AlertSeverity) | NOT NULL | Severity level: INFO, WARNING, or CRITICAL. Determines paging behaviour. | `WARNING` |
| `consumer_id` | UUID | NULLABLE, FK → Consumer.id | Associated consumer account if this is a consumer-scoped alert. Null for platform alerts. | `b9e0c1d2-...` |
| `route_id` | UUID | NULLABLE, FK → ApiRoute.id | Associated API route if this is a route-scoped alert. Null for consumer or platform alerts. | `null` |
| `threshold_value` | NUMERIC(15,4) | NOT NULL | The configured threshold that when crossed caused this alert to fire. | `80.0000` |
| `observed_value` | NUMERIC(15,4) | NOT NULL | The actual observed metric value that exceeded the threshold. | `81.3400` |
| `metric_name` | VARCHAR(100) | NOT NULL | Prometheus metric name evaluated by the alerting rule (e.g., `gateway_consumer_daily_quota_pct`). | `gateway_consumer_daily_quota_pct` |
| `status` | ENUM(AlertStatus) | NOT NULL, DEFAULT `FIRING` | Alert lifecycle: FIRING, ACKNOWLEDGED, or RESOLVED. | `FIRING` |
| `fired_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Timestamp when the alert condition was first detected and the alert was created. | `2025-03-15T10:00:00Z` |
| `acknowledged_at` | TIMESTAMPTZ | NULLABLE | Timestamp when an operator acknowledged the alert in the Admin Console. | `null` |
| `resolved_at` | TIMESTAMPTZ | NULLABLE | Timestamp when the alert condition was no longer met and the alert auto-resolved. | `null` |
| `acknowledged_by` | UUID | NULLABLE, FK → Consumer.id | ID of the Admin user who acknowledged the alert. Null until acknowledged. | `null` |
| `notification_sent` | BOOLEAN | NOT NULL, DEFAULT FALSE | Whether an email or PagerDuty notification was successfully dispatched for this alert. | `true` |
| `event_ref` | VARCHAR(128) | NULLABLE | Reference to the triggering event ID in the analytics pipeline for drill-down investigation. | `evt-uuid-...` |

---

## Enumerations

| Enum Type | Allowed Values | Description |
|-----------|---------------|-------------|
| `ApiKeyStatus` | `ACTIVE`, `SUSPENDED`, `REVOKED`, `EXPIRED` | Lifecycle states of an API key. |
| `ConsumerStatus` | `PENDING_VERIFICATION`, `ACTIVE`, `SUSPENDED`, `DELETED` | Lifecycle states of a consumer account. |
| `UserRole` | `DEVELOPER`, `API_PROVIDER`, `ADMIN`, `ANALYST` | Platform roles controlling portal and API access level. |
| `Environment` | `PRODUCTION`, `SANDBOX` | Distinguishes live traffic credentials from test credentials. |
| `ApplicationStatus` | `ACTIVE`, `SUSPENDED`, `DELETED` | Lifecycle of a Consumer's Application. |
| `PlanStatus` | `ACTIVE`, `DEPRECATED`, `RETIRED` | Lifecycle of a SubscriptionPlan record. |
| `PolicyScope` | `PLAN`, `ROUTE` | Scope at which a RateLimitPolicy is applied. |
| `RateLimitStrategy` | `SLIDING_WINDOW`, `FIXED_WINDOW`, `TOKEN_BUCKET` | Algorithm used for rate-limit counter evaluation. |
| `RateLimitKeyDimension` | `CONSUMER`, `IP`, `API_KEY`, `ROUTE_CONSUMER` | The partitioning dimension for the rate-limit counter key. |
| `QuotaExceededAction` | `REJECT`, `THROTTLE` | What the gateway does when the quota is exhausted. |
| `RouteClassification` | `STANDARD`, `CONTAINS_PII`, `CONFIDENTIAL` | Data sensitivity classification controlling body logging behaviour. |
| `RouteStatus` | `ACTIVE`, `INACTIVE`, `DEPRECATED`, `RETIRED` | Lifecycle of an ApiRoute record. |
| `ApiVersionStatus` | `DRAFT`, `ACTIVE`, `DEPRECATED`, `RETIRED` | Lifecycle of an ApiVersion record. |
| `WebhookStatus` | `PENDING_VERIFICATION`, `ACTIVE`, `SUSPENDED`, `FAILED`, `DELETED` | Lifecycle of a WebhookSubscription record. |
| `DeliveryStatus` | `SUCCESS`, `FAILED`, `TIMEOUT` | Outcome of a single webhook delivery attempt. |
| `OAuthClientStatus` | `ACTIVE`, `SUSPENDED`, `REVOKED` | Lifecycle of an OAuthClient record. |
| `TokenAuthMethod` | `client_secret_basic`, `client_secret_post`, `private_key_jwt` | OAuth 2.0 client authentication method at the token endpoint. |
| `OAuthTokenType` | `ACCESS`, `REFRESH` | Distinguishes OAuth access tokens from refresh tokens. |
| `PluginScope` | `GLOBAL`, `ROUTE`, `CONSUMER` | Scope at which a GatewayPlugin instance is applied. |
| `AuthType` | `API_KEY`, `JWT`, `NONE` | Authentication method used for a specific gateway request. |
| `AuditSource` | `PORTAL_UI`, `MANAGEMENT_API`, `SYSTEM`, `WEBHOOK` | Origin system that produced an AuditLog entry. |
| `AuditResult` | `SUCCESS`, `FAILURE` | Outcome of the audited action. |
| `AlertType` | `QUOTA_WARNING`, `QUOTA_EXCEEDED`, `UPSTREAM_DEGRADED`, `ERROR_RATE`, `LATENCY_P99`, `SECURITY` | Categories of platform monitoring alerts. |
| `AlertSeverity` | `INFO`, `WARNING`, `CRITICAL` | Severity levels determining notification and escalation behaviour. |
| `AlertStatus` | `FIRING`, `ACKNOWLEDGED`, `RESOLVED` | Lifecycle states of a triggered Alert record. |

---

## Relationships Summary

| Entity A | Relationship | Entity B | Cardinality | FK Location |
|----------|-------------|----------|-------------|-------------|
| Consumer | owns | Application | 1 : many | `Application.consumer_id` |
| Consumer | holds | ApiKey | 1 : many | `ApiKey.consumer_id` |
| Consumer | subscribes to | SubscriptionPlan | many : 1 | `Consumer.plan_id` |
| Consumer | registers | OAuthClient | 1 : many | `OAuthClient.consumer_id` |
| Application | has | ApiKey | 1 : many | `ApiKey.application_id` |
| Application | has | WebhookSubscription | 1 : many | `WebhookSubscription.application_id` |
| Application | has | OAuthClient | 1 : many | `OAuthClient.application_id` |
| ApiRoute | belongs to | ApiVersion | many : 1 | `ApiRoute.api_version_id` |
| ApiRoute | governed by | RateLimitPolicy | many : 0..1 | `ApiRoute.rate_limit_policy_id` |
| ApiRoute | has | GatewayPlugin | many : many | `ApiRoute.plugin_ids[]` |
| ApiVersion | published by | Consumer (Provider) | many : 1 | `ApiVersion.provider_id` |
| ApiVersion | succeeded by | ApiVersion | 1 : 0..1 | `ApiVersion.successor_version_id` |
| AnalyticsEvent | generated by | Consumer | many : 1 | `AnalyticsEvent.consumer_id` |
| AnalyticsEvent | targets | ApiRoute | many : 1 | `AnalyticsEvent.route_id` |
| AnalyticsEvent | authenticated by | ApiKey | many : 0..1 | `AnalyticsEvent.api_key_id` |
| OAuthToken | issued to | OAuthClient | many : 1 | `OAuthToken.client_id` |
| OAuthToken | linked to (refresh) | OAuthToken | 1 : 0..1 | `OAuthToken.refresh_token_id` |
| AuditLog | records action by | Consumer | many : 0..1 | `AuditLog.actor_id` |
| Alert | scoped to | Consumer | many : 0..1 | `Alert.consumer_id` |
| Alert | scoped to | ApiRoute | many : 0..1 | `Alert.route_id` |
| GatewayPlugin | attached to | ApiRoute | many : 0..1 | `GatewayPlugin.route_id` |
| GatewayPlugin | scoped to | Consumer | many : 0..1 | `GatewayPlugin.consumer_id` |

---

## Glossary of Terms

| Term | Definition |
|------|------------|
| **API Gateway** | The Fastify-based Node.js 20 service receiving external HTTP/WebSocket requests, authenticating them, enforcing rate limits, applying plugins, and forwarding to upstream services. |
| **API Key** | An opaque credential issued to a Consumer Application, validated using HMAC-SHA256. The plaintext key is shown once at creation and never stored. |
| **API Provider** | A Consumer with the `API_PROVIDER` role that registers, configures, and publishes API routes and versions on the platform. |
| **API Route** | A single gateway-proxied endpoint defined by path pattern, HTTP methods, upstream URL, and associated policies. |
| **API Version** | A major version grouping of related API routes (v1, v2). Versions follow a DRAFT → ACTIVE → DEPRECATED → RETIRED lifecycle. |
| **Application** | A logical container owned by a Consumer that groups API keys and webhooks for a specific project or product. |
| **Audit Log** | An immutable append-only record of all state-mutating actions, retained for 7 years for regulatory compliance. |
| **BullMQ** | Redis-backed queue library used for async job processing including webhook delivery, analytics writes, and plan enforcement. |
| **Burst Allowance** | A temporary credit allowing paid-tier consumers to exceed their per-minute rate limit by up to 1.5× for short traffic spikes. |
| **Consumer** | A registered entity (individual developer or organisation) that subscribes to API access plans and manages API keys. |
| **Dead Letter Queue (DLQ)** | A BullMQ queue receiving jobs that exhausted all retry attempts, holding them for manual review or replay. |
| **Developer Portal** | The Next.js 14 web application providing self-service API catalogue, subscription management, key management, and analytics. |
| **Gateway Plugin** | A composable pipeline module (CORS, cache, request transform, IP restriction) applied to API routes in execution-order sequence. |
| **HMAC-SHA256** | Hash-based Message Authentication Code with SHA-256. Used for API key validation and webhook payload signing. |
| **JWT (JSON Web Token)** | A compact, signed token in OAuth 2.0 / OIDC flows for stateless authentication. Validated against the IdP's JWKS keys. |
| **JWKS (JSON Web Key Set)** | Public keys published by the OAuth IdP, used by the gateway to verify JWT signatures without contacting the IdP per-request. |
| **OAuth 2.0** | An authorisation framework enabling controlled API access. Platform supports client_credentials and authorization_code grant types. |
| **OIDC (OpenID Connect)** | An identity layer built on OAuth 2.0 used for Developer SSO login via external identity providers. |
| **OpenTelemetry** | Vendor-neutral observability framework collecting distributed traces, metrics, and logs from all platform components. |
| **Plan** | A named tier of API access with defined quotas, feature flags, and pricing (Free, Pro, Enterprise). |
| **Rate Limit** | A constraint on the number of requests a Consumer may make in a given time window, enforced via Redis sliding-window counters. |
| **Redis** | In-memory data store used for API key caching, rate-limit counters, session tokens, and BullMQ job queues. |
| **Route Classification** | Data sensitivity label (STANDARD, CONTAINS_PII, CONFIDENTIAL) controlling whether request bodies are logged. |
| **Sliding Window** | A rate-limit algorithm tracking requests in a rolling time window for smoother enforcement than a fixed window. |
| **Stripe** | Third-party payment processor managing subscription billing, invoicing, and payment lifecycle webhooks. |
| **Sunset Header** | HTTP response header (`Sunset: <HTTP-date>`) announcing an API version's retirement date per RFC 8594. |
| **Upstream Service** | The backend microservice the API Gateway proxies requests to after successful authentication and rate-limit checks. |
| **WAF** | AWS Web Application Firewall rules at the CloudFront edge blocking OWASP Top 10 patterns and DDoS traffic. |
| **Webhook** | An HTTP POST callback dispatched by the platform to a Developer's endpoint when a specified platform event occurs. |
| **Webhook Subscription** | A Developer's registration of a target URL and event type filter for receiving webhook deliveries. |

---

## Operational Policy Addendum

### API Governance Policies

1. **Policy AGP-001 — Schema Validation on Entity Creation:** All entity creation and update operations must validate input against field constraints defined in this data dictionary before any database write. Validation failures return HTTP 422 Unprocessable Entity with a structured error body listing each violated constraint by field name. No partial writes are permitted; all field validations must pass atomically.

2. **Policy AGP-002 — Foreign Key Integrity:** All foreign key relationships defined in the Relationships Summary must be enforced at the PostgreSQL database level with `ON DELETE RESTRICT` or `ON DELETE CASCADE` as appropriate. Application-level-only FK enforcement is prohibited. The cascade policy for each relationship must be reviewed and approved when new entities are added to the data model.

3. **Policy AGP-003 — Enumeration Value Governance:** New enum values may not be added to PostgreSQL ENUM types without a migration tested in staging, reviewed by two engineers, and deployed during a maintenance window. Deprecated enum values are retained indefinitely to preserve historical record integrity. The complete list of enum types and values in this document is the authoritative source of truth.

4. **Policy AGP-004 — JSONB Field Schema Governance:** All JSONB fields (e.g., `metadata`, `config`, `notification_prefs`, `feature_flags`, `before_state`, `after_state`) must have a defined JSON Schema document at `docs/json-schemas/{entity}_{field}.schema.json`. Application-layer validation must enforce this schema before writing to PostgreSQL. Unvalidated free-form JSONB writes are prohibited. Schema documents are reviewed quarterly.

---

### Developer Data Privacy Policies

1. **Policy DDP-001 — PII Field Classification Register:** All fields in this data dictionary containing or deriving from personally identifiable information must be listed in the PII Field Register at `docs/privacy/pii-register.md`. Additions or changes to PII-classified fields require a privacy impact assessment and Data Protection Officer review before deployment. The register is audited quarterly.

2. **Policy DDP-002 — Consumer Credential Zero-Knowledge Design:** The platform maintains a zero-knowledge posture for all Consumer credentials. `ApiKey.key_hash`, `Consumer.password_hash`, `OAuthClient.client_secret_hash`, and `WebhookSubscription.secret_hash` must never be decryptable or reversible by any platform operator. Lost credentials must be rotated (new credential issued), never retrieved or decrypted.

3. **Policy DDP-003 — Analytics Event PII Pseudonymisation:** The `AnalyticsEvent` table must not contain unmasked IP addresses. `source_ip` is pseudonymised by zeroing the last IPv4 octet (or last 80 bits of IPv6) before insert. Requests to routes with `classification = CONTAINS_PII` must not have `request_path` query parameters recorded. `user_agent` strings are truncated to 512 characters.

4. **Policy DDP-004 — Data Portability Export Completeness:** The Consumer data export (GDPR Article 20) must include all entities referencing `consumer_id` in this dictionary, exported as structured JSON within 30 days of request. Export links expire after 72 hours, are delivered to the Consumer's verified email address, and must not include any other Consumer's data.

---

### Monetization and Quota Policies

1. **Policy MQP-001 — Plan Field Immutability After Live Subscription:** Once a `SubscriptionPlan` has active consumer subscriptions, the fields `price_monthly_usd_cents`, `requests_per_minute`, `requests_per_day`, and `requests_per_month` must not be modified in place. Changes require creating a new plan record, migrating consumers, and deprecating the old record. In-place changes to live plan pricing are a data integrity violation.

2. **Policy MQP-002 — Quota Counter Atomic Accuracy:** Rate-limit counters in Redis must be updated atomically using `INCR` and `EXPIRE` in a single Lua script to prevent race conditions. Counter drift exceeding 1% relative to the PostgreSQL analytics source-of-truth (verified by daily reconciliation jobs) must be investigated and resolved within 48 hours of detection.

3. **Policy MQP-003 — Overage Billing Data Integrity:** The `AnalyticsEvent` table is the sole source of truth for overage billing calculations. Monthly overage totals submitted to Stripe as usage records must be derived exclusively from this table. Manual adjustments to overage billing require dual approval from Finance and Platform Engineering with an AuditLog entry.

4. **Policy MQP-004 — Trial Abuse Detection:** Free-trial activations where the same Stripe payment method fingerprint or email domain has been used for a prior trial on any account must be flagged for manual Admin review before quota is activated. The platform maintains a trial-fingerprint registry and blocks automatic trial activation for confirmed-abusive fingerprints.

---

### System Availability and SLA Policies

1. **Policy SAP-001 — Database Schema Migration Safety:** All PostgreSQL schema migrations must be non-blocking and backward-compatible. Migrations locking tables for more than 1 second are prohibited in production. New NOT NULL columns are added with a DEFAULT value, back-filled via background job, then DEFAULT removed in a subsequent migration. All migrations are tested against a production-scale snapshot in staging before production deployment.

2. **Policy SAP-002 — Redis Cache Consistency Guarantees:** ApiKey and Consumer plan metadata cache entries must have a maximum TTL of 300 seconds. The `updated_at` timestamp on each cache entry must be compared against the database record during periodic consistency sweeps run every 60 seconds. Stale entries detected by the sweep are invalidated immediately and the anomaly reported to the on-call engineer.

3. **Policy SAP-003 — Read Replica Query Routing:** All read-heavy queries from the Developer Portal (analytics dashboards, API catalogue browsing, audit log searches, plan listings) must be directed to the PostgreSQL read replica, not the primary. The primary instance is reserved exclusively for write operations and time-sensitive reads (e.g., active key validation fallback when Redis is unavailable).

4. **Policy SAP-004 — Database Backup Verification Cadence:** Automated daily RDS snapshots must be verified monthly by restoring to an isolated test environment and executing the full data dictionary schema validation suite. Backup verification failures are escalated as Severity-1 incidents. A verification log entry is produced for each test and reviewed at the quarterly security and compliance review.
