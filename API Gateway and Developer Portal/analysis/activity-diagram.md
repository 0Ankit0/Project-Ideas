# Activity Diagrams — API Gateway and Developer Portal

## Overview

This document presents five detailed activity diagrams modelling the primary process flows within the API Gateway and Developer Portal system. Each diagram is rendered using Mermaid `flowchart TD` syntax with decision diamonds for conditional branches, parallelism notes where concurrent processing occurs, and explicit error/exception paths. Together these diagrams cover the end-to-end lifecycle of API request processing, developer self-service onboarding, OAuth 2.0 authorization, webhook delivery, and API version deprecation.

The diagrams reference the Node.js 20 / Fastify gateway runtime, the Next.js 14 developer portal, PostgreSQL 15, Redis 7, BullMQ, and AWS infrastructure components (ECS Fargate, CloudFront, WAF, SES, S3). Authentication mechanisms modelled include HMAC-SHA256 API keys, OAuth 2.0 with PKCE, and RS256-signed JWTs.

---

## Activity 1: Inbound API Request Processing

This activity models the complete lifecycle of an HTTP request from the moment it reaches the CloudFront distribution through authentication, rate limiting, quota enforcement, request transformation, upstream routing, response transformation, and telemetry emission.

```mermaid
flowchart TD
    A([Start: Client Sends HTTP Request]) --> B[CloudFront receives request\nApply WAF rule evaluation]
    B --> C{WAF rule\nblocked?}
    C -- Yes --> D[Return HTTP 403 Forbidden\nLog WAF block event]
    D --> ZZ([End])
    C -- No --> E[Forward to ECS Fargate\nFastify Gateway Instance]
    E --> F[Parse HTTP headers\nExtract auth credential\nX-API-Key / Authorization Bearer]
    F --> G{Auth scheme\ndetected?}
    G -- None --> H[Return HTTP 401 Unauthorized\nWWW-Authenticate header set]
    H --> ZZ
    G -- API Key --> I[Hash key SHA-256\nRedis GET auth:apikey:hash]
    G -- OAuth Bearer --> J[Decode JWT header\nFetch JWKS from Redis cache]
    G -- JWT RS256 --> K[Verify RS256 signature\nCheck exp and aud claims]
    I --> L{Key found\nand active?}
    L -- No --> M[Return HTTP 401\nLog auth failure with IP and prefix]
    M --> ZZ
    L -- Yes --> N[Inject authContext\ndeveloper_id, app_id, plan_id, scopes]
    J --> N
    K --> N
    N --> O[Fetch rate-limit policy\nfrom Redis plan cache]
    O --> P[Execute Lua script on Redis\nINCR per-second and per-minute counters atomically]
    P --> Q{Rate limit\nexceeded?}
    Q -- Yes --> R[Return HTTP 429 Too Many Requests\nRetry-After header set\nIncrement violation counter]
    R --> ZZ
    Q -- No --> S[Decrement monthly quota counter\nRedis DECRBY quota:app_id]
    S --> T{Quota\nexhausted?}
    T -- Yes --> U[Return HTTP 429 Quota Exhausted\nRetry-After set to month-end\nSend quota alert to developer]
    U --> ZZ
    T -- No --> V[Apply Request Transformation\nStrip X-API-Key header\nInject X-Consumer-ID, X-Request-ID\nRemove api_key query param]
    V --> W{Body transform\nrule exists?}
    W -- Yes --> X[Apply JSONata expression\nValidate against JSON Schema\nUpdate Content-Length]
    X --> Y{Schema\nvalidation\npassed?}
    Y -- No --> AA[Return HTTP 422 Validation Failed\nReturn field-level error details]
    AA --> ZZ
    Y -- Yes --> AB[Dispatch to Upstream via undici\nStart OTel span gateway.upstream.request]
    W -- No --> AB
    AB --> AC{Upstream\nresponded\nwithin timeout?}
    AC -- No --> AD[Return HTTP 504 Gateway Timeout\nClose OTel span with error=true\nIncrement timeout counter]
    AD --> ZZ
    AC -- Yes --> AE{Upstream\nstatus 5xx?}
    AE -- Yes --> AF[Map upstream error to gateway format\nLog upstream failure\nIncrement error counter]
    AF --> AG[Apply Response Transformation\nStrip internal headers\nInject X-Request-ID]
    AE -- No --> AG
    AG --> AH[Increment usage counters in Redis\nINCRBY usage:developer_id:yearmonth 1]
    AH --> AI{Response\ncacheable?}
    AI -- Yes --> AJ[Store response in Redis\nSET cache:route_id:req_hash body EX max-age]
    AJ --> AK[Emit OTel span and Prometheus metrics\ngateway_requests_total, gateway_request_duration]
    AI -- No --> AK
    AK --> AL([End: Return Response to Client])
```

---

## Activity 2: Developer Registration & API Key Provisioning

This activity models the complete self-service onboarding flow: from portal sign-up through email verification, application creation, plan subscription, and API key generation.

```mermaid
flowchart TD
    A([Start: Developer Opens Registration Page]) --> B[Developer enters name, email\npassword, accepts ToS]
    B --> C{Client-side\nvalidation\npassed?}
    C -- No --> D[Display field-level\nvalidation errors\nHighlight failing fields]
    D --> B
    C -- Yes --> E[POST /api/auth/register\nover TLS to Next.js API route]
    E --> F{Email already\nregistered?}
    F -- Yes --> G[Return HTTP 409\nDisplay: Account already exists\nOffer Sign In link]
    G --> ZZ([End])
    F -- No --> H[Hash password with bcrypt cost=12\nInsert developer row status=pending_verification]
    H --> I[Generate 256-bit HMAC-SHA256\nemail verification token\nStore in Redis EX 86400]
    I --> J[Call AWS SES SendEmail\nDispatch verification link]
    J --> K{SES dispatch\nsucceeded?}
    K -- No --> L[Enqueue retry job in BullMQ\nShow warning: resend link available]
    L --> M[Display: Check your inbox page]
    K -- Yes --> M
    M --> N[Developer clicks verification link\nin email client]
    N --> O[GET /api/auth/verify-email?token=X\nGateway API route handler]
    O --> P{Token found\nin Redis and\nnot expired?}
    P -- No --> Q[Return HTTP 410 Token Expired\nOffer resend verification email]
    Q --> ZZ
    P -- Yes --> R[Update developer status=active\nDelete token from Redis\nRecord email_verified_at timestamp]
    R --> S[Redirect to portal dashboard\nDisplay welcome banner]
    S --> T[Developer clicks New Application\nFills name, description, environment]
    T --> U{Application\nlimit reached\nfor plan?}
    U -- Yes --> V[Return HTTP 403 App Limit Exceeded\nDisplay upgrade prompt]
    V --> ZZ
    U -- No --> W[POST /api/apps\nInsert application row status=active\nWrite AUDIT APP_CREATED]
    W --> X[Developer selects subscription plan\nFree / Pro / Business / Enterprise]
    X --> Y{Paid plan\nselected?}
    Y -- Yes --> Z[Redirect to payment flow\nCollect card via Stripe Elements]
    Z --> AA{Payment\nauthorized?}
    AA -- No --> AB[Display payment failure\nOffer retry or choose free plan]
    AB --> X
    AA -- Yes --> AC[Create Stripe subscription\nInsert subscriptions row status=active]
    Y -- No --> AC
    AC --> AD[Publish subscription.created event\nto BullMQ gateway-config queue]
    AD --> AE[Gateway config consumer\nInvalidates Redis plan cache for app_id]
    AE --> AF[Developer clicks Generate API Key\nSelects key name and expiry optional]
    AF --> AG[POST /api/apps/app_id/keys\nGenerate 32-byte random key\nCompute HMAC-SHA256 hash\nInsert api_keys row]
    AG --> AH[Return plaintext key ONCE in response\nDisplay one-time disclosure modal]
    AH --> AI[Developer copies key to clipboard\nKey stored only as hash in DB henceforth]
    AI --> AJ([End: Developer ready to make API calls])
```

---

## Activity 3: OAuth 2.0 Authorization Code Flow (PKCE)

This activity models the full RFC 7636 Authorization Code + PKCE flow used when a developer connects a third-party OAuth provider or when an External Client authenticates users via the portal's OAuth integration.

```mermaid
flowchart TD
    A([Start: Developer clicks Connect with OAuth Provider]) --> B[Portal generates code_verifier\n32 random bytes, base64url encoded]
    B --> C[Compute code_challenge\nSHA-256 of code_verifier, base64url encoded]
    C --> D[Store code_verifier in sessionStorage\nStore state nonce in sessionStorage]
    D --> E[Redirect browser to OAuth Provider\nAuthorization Endpoint\nParams: response_type=code, client_id\nredirect_uri, scope, state, code_challenge\ncode_challenge_method=S256]
    E --> F{User already\nauthenticated\nat provider?}
    F -- No --> G[OAuth Provider renders\nlogin page\nUser enters credentials]
    G --> H{Authentication\nsucceeded at\nprovider?}
    H -- No --> I[Provider displays login error\nUser retries or cancels]
    I --> H
    H -- Yes --> J[OAuth Provider renders\nconsent screen\nDisplays requested scopes]
    F -- Yes --> J
    J --> K{User grants\nconsent?}
    K -- No --> L[Provider redirects back with error=access_denied\nPortal displays: Authorization cancelled]
    L --> ZZ([End])
    K -- Yes --> M[Provider generates authorization code\nShort-lived 60 seconds, single use]
    M --> N[Provider redirects to redirect_uri\nWith code and state params]
    N --> O[Portal callback handler receives code and state\nGET /api/auth/callback]
    O --> P{State nonce\nmatches stored\nvalue?}
    P -- No --> Q[Return HTTP 400 Invalid State\nCSRF protection triggered\nLog security event]
    Q --> ZZ
    P -- Yes --> R[Retrieve code_verifier from sessionStorage\nClear state and verifier from storage]
    R --> S[POST /token to OAuth Provider\nParams: grant_type=authorization_code\ncode, redirect_uri, client_id\ncode_verifier plaintext]
    S --> T{Provider verifies\ncode_verifier against\nstored code_challenge?}
    T -- No --> U[Provider returns error=invalid_grant\nPortal displays: Authorization failed\nLog PKCE verification failure]
    U --> ZZ
    T -- Yes --> V{Authorization code\nalready used\nor expired?}
    V -- Yes --> W[Provider returns error=invalid_grant\nCode replay attack or timeout\nLog security warning]
    W --> ZZ
    V -- No --> X[Provider returns access_token\nrefresh_token, id_token, expires_in, scope]
    X --> Y[Portal backend verifies id_token\nJWT RS256 signature, iss, aud, exp claims]
    Y --> Z{id_token\nsignature\nvalid?}
    Z -- No --> AA[Reject tokens\nReturn HTTP 401\nLog tampered token attempt]
    AA --> ZZ
    Z -- Yes --> AB[Extract sub, email, name from id_token\nUpsert developer record with provider=oauth\nLink OAuth identity to developer_id]
    AB --> AC[Store refresh_token encrypted\nusing AES-256-GCM in PostgreSQL\noauth_tokens table]
    AC --> AD[Issue portal session JWT\nHS256, exp=8h, contains developer_id and roles]
    AD --> AE[Set HttpOnly Secure SameSite=Strict\nsession cookie\nRedirect to portal dashboard]
    AE --> AF([End: Developer authenticated via OAuth])
```

---

## Activity 4: Webhook Delivery Pipeline

This activity models the end-to-end webhook delivery pipeline: from event emission in the gateway through BullMQ queuing, delivery attempts, exponential back-off retries, and dead-letter queue handling.

```mermaid
flowchart TD
    A([Start: Gateway emits internal event\ne.g. subscription.updated, api.version.deprecated]) --> B[Webhook dispatcher plugin\nQueries webhooks table\nfor all endpoints subscribed to event type]
    B --> C{Any active webhook\nendpoints found\nfor this event?}
    C -- No --> D[Drop event silently\nIncrement undelivered_events counter]
    D --> ZZ([End])
    C -- Yes --> E[For each matching webhook endpoint\nConstruct delivery payload\nJSON: event_type, timestamp, data, webhook_id]
    E --> F[Compute HMAC-SHA256 signature\nSign payload with stored signing secret\nSet X-Webhook-Signature header]
    F --> G[Enqueue delivery job in BullMQ\nQueue: webhook-delivery\nJob data: webhook_id, payload, signature, attempt=1]
    G --> H[BullMQ worker picks up job\nfrom webhook-delivery queue]
    H --> I[POST to webhook endpoint URL\nSet headers: Content-Type, X-Webhook-Signature\nX-Delivery-ID, X-Event-Type\nTimeout: 10 seconds]
    I --> J{HTTP 2xx\nresponse received\nwithin 10s?}
    J -- Yes --> K[Mark delivery as succeeded\nInsert webhook_deliveries row status=delivered\nRecord response_code, response_time_ms]
    K --> ZZ
    J -- No --> L{Response was\nHTTP 410 Gone?}
    L -- Yes --> M[Mark webhook as auto-deactivated\nstatus=deactivated reason=410_gone\nNotify developer via email]
    M --> ZZ
    L -- No --> N[Increment attempt counter\nRecord failure reason\nTimeout, 4xx, 5xx, DNS error]
    N --> O{Max retry\nattempts\nreached? max=5}
    O -- No --> P[Calculate exponential back-off delay\ndelay = 2^attempt × 10s, jitter ±20%\nattempts: 10s, 20s, 40s, 80s, 160s]
    P --> Q[Re-enqueue job with delay\nBullMQ delayed queue\nUpdate attempt count]
    Q --> H
    O -- Yes --> R[Mark delivery as permanently failed\nInsert webhook_deliveries row status=failed\nAll 5 attempts exhausted]
    R --> S[Move payload to Dead-Letter Queue\nBullMQ queue: webhook-dlq\nRetain for 30 days]
    S --> T[Send failure notification\nto developer via email\nInclude delivery_id and failure details]
    T --> U{Admin DLQ\nreplay\nrequested?}
    U -- No --> ZZ
    U -- Yes --> V[Admin triggers replay\nPOST /api/admin/webhooks/dlq/replay/delivery_id]
    V --> W{Endpoint responds\nto probe before\nreplay?}
    W -- No --> X[Abort replay\nReturn HTTP 422 Endpoint unreachable]
    X --> ZZ
    W -- Yes --> H
```

---

## Activity 5: API Version Deprecation Workflow

This activity models the formal process of deprecating an API version: from the API Provider's deprecation request through sunset-period traffic monitoring, developer migration tracking, canary traffic migration, and final version retirement.

```mermaid
flowchart TD
    A([Start: API Provider initiates deprecation\nfor existing API version]) --> B[API Provider opens Admin Console\nNavigates to APIs > Version > Deprecate]
    B --> C[Provider fills deprecation form:\nSunset date minimum 90 days from today\nMigration guide URL\nSuccessor version ID\nReason for deprecation]
    C --> D{Successor\nversion\nexists and\nis active?}
    D -- No --> E[Return error: Successor version required\nbefore deprecation can be initiated]
    E --> B
    D -- Yes --> F{Sunset date\ngreater than\n90 days from today?}
    F -- No --> G[Return error: Minimum 90-day sunset\nperiod not satisfied]
    G --> B
    F -- Yes --> H[Update api_versions row\nstatus=deprecated\ndeprecated_at=NOW\nsunset_at=provided_date]
    H --> I[Add Deprecation headers to all route responses\nDeprecation: date as RFC 7231 timestamp\nSunset: sunset_date as RFC 7231 timestamp\nLink: migration guide URL]
    I --> J[Query subscribers table\nfor all active subscribers\nof deprecated version]
    J --> K[Send initial deprecation notice\nvia AWS SES to all subscribers\nInclude migration guide and sunset date]
    K --> L[Schedule 60-day reminder job\nin BullMQ scheduler queue\nSchedule 30-day final notice job]
    L --> M[Monitor traffic split dashboard\nDeprecated vs successor version]
    M --> N{60-day\nremainder\njob fires?}
    N -- Yes --> O[Send 60-day reminder email\nto subscribers still on deprecated version\nHighlight breaking changes]
    O --> P{30-day\nfinal notice\njob fires?}
    P -- Yes --> Q[Send 30-day final notice\nto remaining subscribers\nInclude escalation contact]
    Q --> R{API Provider\nconfigures canary\nauto-migration?}
    N -- No --> R
    R -- Yes --> S[Enable canary migration policy\nBegin routing 5% of deprecated traffic\nto successor version]
    S --> T{Error rate\non canary\nabove threshold 1%?}
    T -- Yes --> U[Pause canary migration\nAlert API Provider\nRevert to 0% canary split]
    U --> S
    T -- No --> V[Gradually increase canary split\n5% > 25% > 50% > 75% > 100%\nOver 14-day ramp period]
    V --> W{Sunset date\nreached?}
    R -- No --> W
    W -- No --> M
    W -- Yes --> X{Any active\nsubscribers still\non deprecated version?}
    X -- Yes --> Y[Force-migrate remaining subscribers\nBlock API key usage on deprecated version\nReturn HTTP 410 Gone with migration URL]
    Y --> Z[Deactivate deprecated version route\nUpdate api_versions status=retired\nRemove from gateway route registry]
    X -- No --> Z
    Z --> AA[Publish route.retired event to BullMQ\nGateway config consumer removes route\nfrom in-memory registry]
    AA --> AB[Archive OpenAPI spec to S3\ns3://api-specs/archive/version_id/]
    AB --> AC[Write AUDIT VERSION_RETIRED entry\nRecord final traffic stats snapshot]
    AC --> AD([End: API version fully retired])
```

---

## Activity 6: Subscription Plan Upgrade (Supplementary Flow)

This activity supplements the BPMN diagram in `bpmn-swimlane-diagram.md` by modelling the portal-side decision logic and gateway policy hot-reload steps during a subscription plan upgrade.

```mermaid
flowchart TD
    A([Start: Developer clicks Upgrade Plan]) --> B[Portal fetches available plans\nGET /api/plans filters plans higher than current]
    B --> C[Developer selects target plan\nPortal renders comparison modal\nShowing new limits and proration charge]
    C --> D{Developer\nconfirms\nupgrade?}
    D -- No --> E([End: Upgrade Cancelled])
    D -- Yes --> F{Payment method\nalready on file?}
    F -- No --> G[Redirect to payment method\ncollection form\nStripe Elements iframe]
    G --> H{Card\nauthorized?}
    H -- No --> I[Display payment failure\nOffer retry or cancel]
    I --> G
    H -- Yes --> J[Payment method saved\nStripe customer updated]
    J --> K[POST /api/subscriptions/id/upgrade\nIdempotency key in header]
    F -- Yes --> K
    K --> L[Backend validates:\nnew plan tier higher than current\nNo pending cancellation]
    L --> M{Validation\npassed?}
    M -- No --> N[Return HTTP 422 with reason\nDisplay error in portal]
    N --> E
    M -- Yes --> O[Call Stripe POST /v1/subscriptions/id\nWith new price_id and proration_behavior=create_prorations]
    O --> P{Stripe\ncharge\nsucceeded?}
    P -- No --> Q[Return HTTP 402 Payment Failed\nLog Stripe decline_code]
    Q --> G
    P -- Yes --> R[Update subscriptions row\nnew plan_id, quota_remaining=new_plan_quota\nbilling_cycle_start unchanged]
    R --> S[Publish subscription.upgraded event\nto BullMQ portal-events queue]
    S --> T[BullMQ consumer processes event\nLoads new plan policy from PostgreSQL]
    T --> U[Invalidate Redis caches:\nplan_cache:plan_id\nquota:app_id\nauth:apikey cache for all app keys]
    U --> V[Gateway in-memory policy cache\nrefreshed on next request within 60 seconds]
    V --> W[Write AUDIT SUBSCRIPTION_UPGRADED\nBefore snapshot and after snapshot]
    W --> X[Send upgrade confirmation email\nvia AWS SES to developer]
    X --> Y[Portal displays success page\nNew quota bar, new rate limit badge]
    Y --> Z([End: Upgrade complete, new limits active])
```

---

## State Transitions Summary

The following table summarises the key state machines and their transitions across all six activity flows.

| Entity | Initial State | Intermediate States | Terminal States | Trigger for Transition |
|--------|--------------|---------------------|-----------------|------------------------|
| **Developer Account** | `pending_verification` | `active`, `suspended` | `deleted` | Email verification, Admin suspension, GDPR erasure |
| **Application** | `active` | `suspended` | `deleted` | Plan violation, Admin action, Developer deletion |
| **API Key** | `active` | `rotated`, `suspended` | `revoked` | Developer rotation, Security event, Plan cancellation |
| **Subscription** | `trialing` | `active`, `past_due` | `cancelled`, `expired` | Payment, Cancellation, Plan downgrade, Expiry |
| **Webhook Endpoint** | `unverified` | `active`, `failing` | `deactivated` | Probe success, Delivery failure, HTTP 410 received |
| **Webhook Delivery** | `queued` | `in_flight`, `retrying` | `delivered`, `failed` | Worker pick-up, 2xx response, Max retries exhausted |
| **API Version** | `draft` | `active`, `deprecated` | `retired` | Admin approval, Deprecation notice, Sunset date reached |
| **Rate Limit Window** | `fresh` | `within_limit`, `burst_active` | `exceeded` | First request in window, Burst threshold, Hard limit hit |
| **OAuth Token** | `issued` | `refreshed`, `revoked` | `expired` | Refresh grant, Revocation endpoint call, `exp` timestamp |
| **Circuit Breaker** | `closed` | `half_open` | `open` | Failure threshold exceeded, Probe success/failure |
| **WAF Request Inspection** | `pending` | `inspecting` | `allowed`, `blocked` | WAF rule match, No matching rule found |
| **API Request** | `received` | `authenticated`, `rate_limited`, `transforming`, `routing` | `responded`, `rejected` | Each pipeline stage completion or failure |
| **PKCE Auth Code** | `issued` | — | `consumed`, `expired` | Successful token exchange, 60-second TTL elapsed, Code replay attempt |
| **Gateway Route** | `draft` | `active`, `degraded` | `retired` | Admin activation, Upstream health failure, Version retirement |
| **BullMQ Job** | `waiting` | `active`, `delayed` | `completed`, `failed` | Worker pickup, Retry delay, Max attempts, 2xx delivery |

---

## Operational Policy Addendum

### API Governance Policies

1. **Request Pipeline Integrity**: All inbound requests must traverse the complete Fastify plugin chain (WAF → Auth → Rate Limit → Quota → Transform → Route → Transform Response) without any plugin being skippable at runtime. Plugin bypass at any stage is treated as a P0 security incident. Plugins are registered as mandatory lifecycle hooks with no opt-out path per route.
2. **Authentication Scheme Enforcement by Route**: Each gateway route must declare exactly one or more permitted authentication schemes. Routes with no authentication scheme configured are automatically blocked from receiving traffic and flagged in the Admin Console as misconfigured. Wildcard anonymous access must be explicitly approved by an Admin.
3. **Transformation Rule Audit**: All changes to request and response transformation rules are recorded in the `audit_log` table with `before` and `after` snapshots. Transformation rules may not be modified in production by non-Admin roles. A staging dry-run must be executed and reviewed before production transformation rules are activated.
4. **Version Deprecation Lead Time**: No API version may be deprecated with fewer than 90 days of advance notice. Emergency deprecations for critical security vulnerabilities may proceed with a 7-day window, but require CISO sign-off and immediate email notification to all active subscribers.

### Developer Data Privacy Policies

1. **Request Body Logging Prohibition**: Gateway plugins must not log raw request or response bodies to any persistent log store. Only metadata (method, path, status code, latency, developer_id, app_id, route_id) is logged. Body content is permissible only in temporary in-memory debug traces that are never persisted, and only when explicitly enabled by an Admin for a maximum duration of 15 minutes.
2. **OAuth Token Storage**: Refresh tokens obtained during the OAuth flow are stored encrypted at rest using AES-256-GCM with a key stored in AWS KMS. Refresh tokens are never logged. Access tokens are held in short-lived Redis sessions with TTLs matching the `expires_in` value and are not written to PostgreSQL.
3. **Analytics Data Retention**: Aggregated per-route and per-developer metrics are retained for 13 months in the analytics store. Raw OpenTelemetry spans are retained for 30 days in Jaeger. Prometheus metrics series are retained for 15 days in the Prometheus instance and 13 months in long-term storage (Thanos or Cortex).
4. **Webhook Payload Security**: Webhook payloads must not include API key values, plaintext secrets, or payment card data. If an event payload would naturally contain such data, the field must be masked (e.g., `card_last_four` instead of full PAN) before the payload is serialised for delivery.

### Monetization and Quota Policies

1. **Quota Enforcement Accuracy**: The Redis quota counter is the authoritative source for real-time quota enforcement. In the event of a Redis failure causing quota counters to be temporarily unavailable, the gateway applies a fail-open policy allowing up to 1,000 requests per application before halting. Usage reconciliation is performed against PostgreSQL within 5 minutes of Redis restoration.
2. **Billing Cycle Alignment**: Usage data exported to the billing service (Stripe) for metered billing must reflect counters captured at 23:59:59 UTC on the last day of the billing period. A scheduled Lambda function performs the snapshot and submits it as a Stripe usage record before the billing cycle closes.
3. **SLA Credit Issuance**: When the gateway availability SLA (99.95% monthly uptime) is breached, affected developers are entitled to a pro-rated service credit calculated as: `credit = (monthly_subscription_cost × downtime_minutes) / total_minutes_in_month`. Credits are issued automatically as Stripe balance credits within 5 business days of the incident's root-cause analysis publication.
4. **Free Tier Rate Limit Non-Negotiability**: The free tier rate limit (10 req/s, 1,000 req/day) is enforced at the gateway level and cannot be increased by customer service without an account upgrade. Requests to increase free tier limits are redirected to the plan upgrade flow in the developer portal.

### System Availability and SLA Policies

1. **Gateway Availability SLA**: The API gateway commits to 99.95% monthly uptime measured by Route 53 health check polling at 10-second intervals against the primary gateway endpoint. Planned maintenance windows are excluded from availability calculations, provided they are announced at least 48 hours in advance and do not collectively exceed 4 hours per calendar month.
2. **Activity Pipeline Latency Budgets**: The gateway inbound pipeline (auth + rate limit + quota + transform) must complete within 50 ms P99. Upstream routing timeout defaults to 30 seconds per route, configurable down to 5 seconds or up to 120 seconds. Webhook delivery workers must process each delivery attempt within 10 seconds before marking it as timed out.
3. **Webhook Delivery SLA**: The webhook delivery system commits to delivering events to healthy endpoints within 30 seconds of event emission for 99% of events. The BullMQ worker pool is sized to process a minimum of 500 concurrent delivery attempts without queue depth exceeding 10,000 unprocessed jobs under normal load.
4. **Dead-Letter Queue Retention**: Webhook payloads in the dead-letter queue are retained for 30 days from the date of final delivery failure. After 30 days, payloads are permanently deleted. Admins may trigger DLQ replay at any time within the retention window. Developers are notified via email when their webhook endpoint has entries in the DLQ.
5. **Canary Traffic Migration SLA**: During API version migration with automated canary routing enabled, traffic increments from 5% to 100% over a minimum 14-day ramp period. Each increment step (5% → 25% → 50% → 75% → 100%) is gated by an error rate check: if the successor version error rate exceeds 1% for any 5-minute window, the migration is automatically paused and the on-call engineer is alerted.
6. **Plan Upgrade Propagation SLA**: New plan policies (rate limits, quota) must be active on the gateway within 60 seconds of a subscription upgrade being confirmed in the portal. If BullMQ event processing lag causes propagation to exceed 90 seconds, a P2 alert fires. Developers receive an in-portal notification that the upgrade is pending propagation if they return to the portal within the window.
7. **OAuth PKCE Enforcement**: All OAuth 2.0 authorization flows initiated from the developer portal or SDK clients must use the Authorization Code grant with PKCE (RFC 7636, S256 method). Implicit grant and Resource Owner Password Credentials grant are disabled at the authorization server level and may not be re-enabled without CISO sign-off.
8. **Activity Diagram Change Control**: Changes to any gateway plugin pipeline ordering or webhook retry parameters require a documented Architecture Decision Record (ADR) to be filed in the project repository before the change is merged. ADRs must be reviewed and approved by at least two platform engineers and one security engineer.
