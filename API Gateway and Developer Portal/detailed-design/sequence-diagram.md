# Detailed Sequence Diagrams

## 1. Overview

This document contains seven detailed sequence diagrams describing the key runtime interactions within
the API Gateway and Developer Portal platform. Each diagram captures internal method-level calls,
Redis command sequences, database queries, and error branches.

| Diagram | Title                                                   |
|---------|---------------------------------------------------------|
| SD-001  | API Key HMAC-SHA256 Validation                          |
| SD-002  | Sliding Window Rate Limit with Redis                    |
| SD-003  | Request Body Transformation Pipeline                    |
| SD-004  | OAuth 2.0 Authorization Code with PKCE                 |
| SD-005  | Webhook Delivery with Exponential Backoff               |
| SD-006  | Developer Portal Create Application and Generate API Key|
| SD-007  | Real-Time Analytics Ingestion                           |

All diagrams use Mermaid `sequenceDiagram` syntax. Actors prefixed with `+` indicate activation bars.

---

## 2. SD-001: API Key HMAC-SHA256 Validation

This diagram shows the complete authentication flow when a client sends an API request signed with
HMAC-SHA256. The flow covers: credential extraction, cache lookup, database fallback, HMAC signature
verification, expiry and IP allowlist checks, and context hydration.

```mermaid
sequenceDiagram
    autonumber
    participant C    as Client
    participant FR   as Fastify Request Hook
    participant AP   as AuthPlugin
    participant AKA  as ApiKeyAuthService
    participant HV   as HmacValidator
    participant TC   as TokenCache (Redis)
    participant AKR  as ApiKeyRepository (PostgreSQL)
    participant RC   as RequestContext

    C  ->>+  FR   : HTTP POST /api/v1/orders<br/>X-API-Key: gw_live_abc123...<br/>X-HMAC-Signature: sha256=...<br/>X-Timestamp: 1704067200

    FR ->>+  AP   : onRequest(ctx)
    AP ->>   AP   : detectCredentialType(headers)<br/>returns CredentialType.API_KEY
    AP ->>+  AKA  : authenticate(ctx)

    AKA ->>  AKA  : extractApiKey(headers)<br/>rawKey = "gw_live_abc123<secret>"
    AKA ->>  AKA  : extractHmacSignature(headers)<br/>signature = "sha256=abcdef..."
    AKA ->>  AKA  : hashKey(rawKey)<br/>keyHash = SHA256(rawKey)

    AKA ->>+ TC   : get("tkn:api_key:" + keyHash)
    alt Cache Hit
        TC  -->>- AKA  : CachedToken { apiKey, application, consumer }
        AKA ->>   AKA  : checkKeyExpiry(cachedKey)
        Note right of AKA: expires_at NULL or > NOW()
    else Cache Miss
        TC  -->>  AKA  : null
        AKA ->>+  AKR  : findByKeyHash(keyHash)
        Note right of AKR: SELECT * FROM api_keys<br/>WHERE key_hash = $1<br/>AND status = 'active'
        AKR -->>- AKA  : ApiKey { id, hmac_secret_hash, scopes, allowed_ips, expires_at }
        AKA ->>+  TC   : set("tkn:api_key:" + keyHash, token, ttl=300s)
        TC  -->>- AKA  : OK
    end

    AKA ->>  AKA  : checkKeyExpiry(apiKey)
    alt Key Expired
        AKA -->>  AP   : AuthResult { success: false, failureCode: "KEY_EXPIRED" }
        AP  -->>  FR   : throw GatewayError(401, "API key has expired")
        FR  -->>  C    : 401 Unauthorized { error: "KEY_EXPIRED" }
    end

    AKA ->>  AKA  : checkIpAllowlist(apiKey, ctx.clientIp)
    alt IP Not Allowed
        AKA -->>  AP   : AuthResult { success: false, failureCode: "IP_FORBIDDEN" }
        AP  -->>  FR   : throw GatewayError(403, "IP not in allowlist")
        FR  -->>  C    : 403 Forbidden { error: "IP_FORBIDDEN" }
    end

    AKA ->>+ HV   : buildMessage(method, path, timestamp, bodyHash)
    Note right of HV: message = "POST\n/api/v1/orders\n1704067200\n" + SHA256(body)
    HV  -->>- AKA  : canonicalMessage: string

    AKA ->>+ HV   : validate(canonicalMessage, clientSignature, apiKey.hmacSecretHash)
    Note right of HV: expectedSig = HMAC-SHA256(secret, message)<br/>timingSafeEqual(expected, received)
    HV  -->>- AKA  : valid: true

    alt Signature Invalid
        AKA -->> AP   : AuthResult { success: false, failureCode: "INVALID_SIGNATURE" }
        AP  -->> FR   : throw GatewayError(401, "HMAC signature mismatch")
        FR  -->>  C   : 401 Unauthorized { error: "INVALID_SIGNATURE" }
    end

    AKA ->>  AKA  : validateTimestamp(timestamp, toleranceSeconds=300)
    alt Timestamp Replay Attack
        AKA -->> AP   : AuthResult { success: false, failureCode: "TIMESTAMP_TOO_OLD" }
        AP  -->> FR   : throw GatewayError(401, "Request timestamp out of tolerance")
        FR  -->>  C   : 401 Unauthorized { error: "TIMESTAMP_TOO_OLD" }
    end

    AKA ->>  AKA  : checkScopeRequirement(apiKey, route.requiredScopes)
    AKA ->>  AKA  : hydrateContext(ctx, apiKey)
    AKA ->>  AKA  : recordAuthMetric("success", apiKey.id)
    AKA -->>- AP   : AuthResult { success: true, apiKey, consumer, scopes, cacheHit }

    AP  ->>+  RC   : ctx.isAuthenticated = true<br/>ctx.apiKey = apiKey<br/>ctx.consumer = consumer<br/>ctx.application = application
    RC  -->>- AP   : updated

    AP  -->>- FR   : void (continue chain)
    Note right of FR: PluginChain continues to<br/>RateLimitPlugin (priority 20)
```

---

## 3. SD-002: Sliding Window Rate Limit with Redis

This diagram shows the exact Redis commands used in the sliding-window algorithm. Key naming convention:
`ratelimit:{keyId}:{windowStartMs}`. The implementation uses a Lua script for atomicity.

```mermaid
sequenceDiagram
    autonumber
    participant RLP  as RateLimitPlugin
    participant SWR  as SlidingWindowRateLimiter
    participant RLS  as RedisRateLimitStore
    participant R    as Redis 7
    participant RC   as RequestContext
    participant RESP as ResponseContext

    RLP ->>  RLP  : onRequest(ctx)
    RLP ->>  RLP  : resolvePolicy(ctx)<br/>policy = ctx.matchedRoute.rateLimitPolicy
    RLP ->>  RLP  : buildRateLimitKey(ctx)<br/>key = "ratelimit:" + apiKey.id

    RLP ->>+ SWR  : checkLimit(key, policy)
    SWR ->>  SWR  : nowMs = clock.now()  // e.g. 1704067200000
    SWR ->>  SWR  : windowMs = policy.windowSeconds * 1000  // e.g. 60000
    SWR ->>  SWR  : windowStart = nowMs - windowMs  // e.g. 1704067140000
    SWR ->>  SWR  : redisKey = "ratelimit:" + key + ":" + windowStart
    Note right of SWR: e.g. "ratelimit:key_abc:1704067140000"

    SWR ->>+ RLS  : evalsha(slidingWindowLua, [redisKey], [nowMs, windowStart, limit, windowTtlSec])
    RLS ->>+ R    : EVALSHA <sha> 1 "ratelimit:key_abc:1704067140000" 1704067200000 1704067140000 100 120

    Note right of R: Lua script (atomic):<br/>1. ZREMRANGEBYSCORE key 0 (windowStart-1)<br/>   Remove entries older than window<br/>2. count = ZCARD key<br/>3. if count < limit then<br/>     ZADD key nowMs nowMs<br/>     EXPIRE key ttlSec<br/>     return {1, limit - count - 1, nextWindowExpiry}<br/>   else<br/>     oldestEntry = ZRANGE key 0 0 WITHSCORES<br/>     retryAfter = ceil((oldestEntry + windowMs - nowMs) / 1000)<br/>     return {0, 0, retryAfter}

    R   ->>  R    : ZREMRANGEBYSCORE ratelimit:key_abc:1704067140000 0 1704067139999
    Note right of R: Removes all entries older than window start
    R   ->>  R    : count = ZCARD ratelimit:key_abc:1704067140000  // returns 45
    R   ->>  R    : 45 < 100 → allowed
    R   ->>  R    : ZADD ratelimit:key_abc:1704067140000 1704067200000 1704067200000
    R   ->>  R    : EXPIRE ratelimit:key_abc:1704067140000 120
    R   -->>- RLS  : [1, 54, 1704067260]  // [allowed=1, remaining=54, resetEpoch]

    RLS -->>- SWR  : [allowed=true, remaining=54, resetEpochMs=1704067260000]

    SWR ->>  SWR  : build RateLimitResult {<br/>  allowed: true,<br/>  limit: 100,<br/>  remaining: 54,<br/>  resetAt: new Date(1704067260000),<br/>  algorithm: "sliding_window"<br/>}
    SWR -->>- RLP  : RateLimitResult

    RLP ->>+ RC   : ctx.rateLimitResult = result
    RC  -->>- RLP  : updated

    Note over RLP: Request continues to TransformPlugin

    RLP ->>  RLP  : onResponse(ctx)
    RLP ->>  RLP  : setRateLimitHeaders(responseCtx, result)
    RLP ->>+ RESP : setHeader("X-RateLimit-Limit", "100")<br/>setHeader("X-RateLimit-Remaining", "54")<br/>setHeader("X-RateLimit-Reset", "1704067260")<br/>setHeader("X-RateLimit-Policy", "sliding_window")
    RESP -->>- RLP : updated

    alt Rate Limit Exceeded (count >= limit)
        R   -->>  RLS  : [0, 0, retryAfterSeconds=37]
        RLS -->>  SWR  : [allowed=false, retryAfter=37]
        SWR -->>  RLP  : RateLimitResult { allowed: false, retryAfterSeconds: 37 }
        RLP ->>   RLP  : handleLimitExceeded(ctx, result)
        RLP -->>  RLP  : throw RateLimitError(429)
        Note right of RLP: Response: 429 Too Many Requests<br/>Retry-After: 37<br/>X-RateLimit-Limit: 100<br/>X-RateLimit-Remaining: 0<br/>X-RateLimit-Reset: 1704067260
    end
```

---

## 4. SD-003: Request Body Transformation Pipeline

This diagram shows the complete request and response transformation pipeline using JSONata expressions
and JSON Schema validation.

```mermaid
sequenceDiagram
    autonumber
    participant C    as Client
    participant TP   as TransformPlugin
    participant JT   as JsonataTransformer
    participant SV   as SchemaValidator
    participant RC   as RequestContext
    participant RP   as RouterPlugin
    participant UP   as Upstream Service
    participant RESP as ResponseContext

    C   ->>  TP   : (via PluginChain) onRequest(ctx)<br/>ctx.body = { "order_id": "123", "qty": 5 }
    TP  ->>  TP   : check ctx.matchedRoute.transform_request
    Note right of TP: route.transform_request = {<br/>  "expression": "{ \"orderId\": order_id, \"quantity\": qty, \"source\": \"gateway\" }",<br/>  "inputSchema": { ... },<br/>  "outputSchema": { ... }<br/>}

    TP  ->>+ SV   : validateAgainstSchema(ctx.body, route.transform_request.inputSchema)
    SV  ->>  SV   : Ajv.validate(schema, data)
    alt Input Validation Fails
        SV  -->> TP   : ValidationResult { valid: false, errors: [...] }
        TP  -->> C    : 400 Bad Request { errors: [...] }
    end
    SV  -->>- TP   : ValidationResult { valid: true }

    TP  ->>+ JT   : applyJsonataTransform(expression, ctx.body)
    JT  ->>  JT   : jsonata.compile(expression)
    JT  ->>  JT   : compiled.evaluate(ctx.body)
    Note right of JT: Input:  { "order_id": "123", "qty": 5 }<br/>Output: { "orderId": "123", "quantity": 5, "source": "gateway" }
    JT  -->>- TP   : transformedBody: object

    TP  ->>+ SV   : validateAgainstSchema(transformedBody, route.transform_request.outputSchema)
    SV  -->>- TP   : ValidationResult { valid: true }

    TP  ->>+ RC   : ctx.body = transformedBody
    RC  -->>- TP   : updated

    TP  ->>  TP   : addRequestHeaders(ctx, { "X-Gateway-Version": "v1", "X-Request-ID": requestId })
    TP  -->>  RP  : void (continue to RouterPlugin)

    RP  ->>+ UP   : POST /internal/orders { "orderId": "123", "quantity": 5, "source": "gateway" }
    UP  -->>- RP   : 201 Created { "id": "ord_xyz", "status": "created" }

    RP  -->>  TP  : (via onResponse) responseCtx.body = { "id": "ord_xyz", "status": "created" }

    TP  ->>  TP   : check route.transform_response
    Note right of TP: route.transform_response = {<br/>  "expression": "{ \"orderId\": id, \"orderStatus\": status, \"created\": true }",<br/>  "outputSchema": { ... }<br/>}

    TP  ->>+ JT   : applyJsonataTransform(responseExpression, responseCtx.body)
    JT  -->>- TP   : { "orderId": "ord_xyz", "orderStatus": "created", "created": true }

    TP  ->>+ SV   : validateAgainstSchema(transformedResponse, route.transform_response.outputSchema)
    SV  -->>- TP   : ValidationResult { valid: true }

    TP  ->>+ RESP : responseCtx.transformedBody = transformedResponse
    RESP ->>  RESP : removeHeader("X-Internal-Service-ID")
    RESP -->>- TP  : updated

    TP  -->> C    : 201 Created { "orderId": "ord_xyz", "orderStatus": "created", "created": true }
```

---

## 5. SD-004: OAuth 2.0 Authorization Code Flow with PKCE

Complete OAuth 2.0 authorization code flow (RFC 6749 + RFC 7636 PKCE). Covers the browser redirect,
code exchange, token issuance, and JWT signing.

```mermaid
sequenceDiagram
    autonumber
    participant U    as User Browser
    participant P    as Developer Portal (Next.js)
    participant AS   as Auth Server (OAuthService)
    participant RCS  as RedisCodeStore
    participant OCR  as OAuthClientRepository
    participant OTR  as OAuthTokenRepository
    participant CR   as ConsumerRepository
    participant JV   as JwtValidator

    Note over U,P: Step 1 — Initiate Authorization Request

    U   ->>+ P    : GET /oauth/authorize?<br/>  client_id=client_abc&<br/>  response_type=code&<br/>  redirect_uri=https://app.example.com/callback&<br/>  scope=read:data write:data&<br/>  state=random_state_xyz&<br/>  code_challenge=BASE64URL(SHA256(verifier))&<br/>  code_challenge_method=S256

    P   ->>+ AS   : authorize({ clientId, redirectUri, scope, state, codeChallenge, codeChallengeMethod })

    AS  ->>+ OCR  : findByClientId("client_abc")
    OCR -->>- AS   : OAuthClient { redirect_uris, allowed_scopes, pkce_required: true }

    AS  ->>  AS   : validateRedirectUri(client, redirectUri)
    AS  ->>  AS   : validateScopes(client, requestedScopes)
    AS  ->>  AS   : client.pkce_required → validateCodeChallengePresent(codeChallenge)

    P   -->>- U    : 302 Redirect to /oauth/login?auth_request_id=req_xxx

    Note over U,P: Step 2 — User Authentication

    U   ->>+ P    : POST /oauth/login { email, password, auth_request_id }
    P   ->>+ CR   : findByEmail(email)
    CR  -->>- P    : Consumer { id, passwordHash, status }
    P   ->>  P    : verifyPassword(password, passwordHash)  // Argon2id
    P   -->>- U    : 302 Redirect to /oauth/consent?auth_request_id=req_xxx

    Note over U,P: Step 3 — User Consent

    U   ->>+ P    : POST /oauth/consent { auth_request_id, approved: true, scopes: ["read:data","write:data"] }

    P   ->>+ AS   : generateAuthorizationCode(clientId, consumerId, codeChallenge)
    AS  ->>  AS   : code = crypto.randomBytes(32).toString("base64url")
    AS  ->>  AS   : data = { clientId, consumerId, scopes, codeChallenge, codeChallengeMethod, redirectUri }
    AS  ->>+ RCS  : store("authcode:" + code, data, ttl=600s)
    Note right of RCS: SET authcode:CODE data EX 600
    RCS -->>- AS   : OK
    AS  -->>- P    : authorizationCode: string

    P   -->>- U    : 302 Redirect to https://app.example.com/callback?code=CODE&state=random_state_xyz

    Note over U,P: Step 4 — Token Exchange

    U   ->>+ P    : POST /oauth/token<br/>  grant_type=authorization_code&<br/>  code=CODE&<br/>  redirect_uri=https://app.example.com/callback&<br/>  client_id=client_abc&<br/>  client_secret=SECRET&<br/>  code_verifier=VERIFIER

    P   ->>+ AS   : exchangeCode({ grantType, code, redirectUri, clientId, clientSecret, codeVerifier })

    AS  ->>+ OCR  : findByClientId("client_abc")
    OCR -->>- AS   : OAuthClient

    AS  ->>  AS   : verifyClientSecret(client, clientSecret)  // Argon2id

    AS  ->>+ RCS  : consume("authcode:" + code)
    Note right of RCS: GETDEL authcode:CODE<br/>(atomic get-and-delete, prevents replay)
    RCS -->>- AS   : AuthCodeData { consumerId, scopes, codeChallenge, codeChallengeMethod }

    AS  ->>  AS   : validatePkceVerifier(codeVerifier, codeChallenge, "S256")
    Note right of AS: SHA256(verifier) == BASE64URL_DECODE(challenge)

    alt PKCE Verification Fails
        AS  -->> P    : Error { code: "invalid_grant", description: "PKCE verification failed" }
        P   -->> U    : 400 Bad Request { error: "invalid_grant" }
    end

    AS  ->>+ CR   : findById(consumerId)
    CR  -->>- AS   : Consumer

    AS  ->>  AS   : issueTokenPair(client, consumer, scopes)

    AS  ->>+ JV   : sign({ sub: consumerId, iss: "https://api.example.com", aud: clientId, scopes }, privateKey, ttl=3600)
    JV  -->>- AS   : accessToken: string (JWT RS256)

    AS  ->>  AS   : refreshToken = crypto.randomBytes(40).toString("base64url")

    AS  ->>+ OTR  : create({ oauth_client_id, consumer_id, access_token_hash, refresh_token_hash, scopes, access_token_expires_at, refresh_token_expires_at })
    OTR -->>- AS   : OAuthToken { id }

    AS  -->>- P    : TokenResponse { access_token, refresh_token, token_type: "Bearer", expires_in: 3600, scope }

    P   -->>- U    : 200 OK { access_token, refresh_token, expires_in: 3600 }
```

---

## 6. SD-005: Webhook Delivery with Exponential Backoff

Full lifecycle of a webhook delivery from event emission through BullMQ, delivery attempt, failure
handling, exponential backoff retries (1 s, 2 s, 4 s, 8 s, 16 s), and dead-lettering after 5 failures.

```mermaid
sequenceDiagram
    autonumber
    participant GW   as Gateway Event Emitter
    participant BQ   as BullMQ Queue (webhook-deliveries)
    participant WW   as Webhook Worker
    participant WSR  as WebhookSubscriptionRepository
    participant WDR  as WebhookDeliveryRepository
    participant HV   as HmacValidator
    participant EP   as Subscriber Endpoint
    participant DLQ  as Dead Letter Queue

    Note over GW,BQ: Event Published

    GW  ->>+ WSR  : findByEventType("api.request.completed")
    WSR ->>  WSR  : SELECT * FROM webhook_subscriptions<br/>WHERE event_types @> ARRAY['api.request.completed']<br/>AND status = 'active'
    WSR -->>- GW   : [WebhookSubscription { id: "sub_abc", endpoint_url, secret_hash }]

    GW  ->>+ WDR  : create({ webhook_subscription_id: "sub_abc", event_type, payload, attempt_number: 1, status: "queued" })
    WDR -->>- GW   : WebhookDelivery { id: "del_001" }

    GW  ->>+ BQ   : add("webhook-deliveries", { deliveryId: "del_001", subscriptionId: "sub_abc" }, { attempts: 1, delay: 0 })
    BQ  -->>- GW   : Job { id: "job_1" }

    Note over BQ,WW: Attempt 1 (delay=0ms)

    BQ  ->>+ WW   : process job { deliveryId: "del_001" }
    WW  ->>+ WDR  : update("del_001", { status: "delivering" })
    WDR -->>- WW   : updated

    WW  ->>+ WSR  : findById("sub_abc")
    WSR -->>- WW   : WebhookSubscription { endpoint_url, secret_hash }

    WW  ->>+ HV   : generate(JSON.stringify(payload), subscriptionSecret)
    HV  -->>- WW   : signature = "sha256=xyz..."

    WW  ->>+ EP   : POST https://subscriber.example.com/webhooks<br/>X-Webhook-Signature: sha256=xyz...<br/>X-Webhook-Event: api.request.completed<br/>X-Delivery-ID: del_001<br/>{ ...payload }

    EP  -->>- WW   : 500 Internal Server Error (first failure)

    WW  ->>+ WDR  : update("del_001", { status: "failed", http_status_code: 500, attempt_number: 1, error_message: "HTTP 500" })
    WDR -->>- WW   : updated

    WW  ->>+ WSR  : incrementFailureCount("sub_abc")  // failure_count = 1
    WSR -->>- WW   : updated

    WW  ->>+ WDR  : scheduleRetry("del_001", nextRetryAt=NOW()+1s, attemptNumber=2)
    WDR -->>- WW   : updated

    WW  ->>+ BQ   : add("webhook-deliveries", { deliveryId: "del_001" }, { delay: 1000, attempts: 1 })
    BQ  -->>- WW   : Job { id: "job_2" }
    WW  -->>- BQ   : void

    Note over BQ,WW: Attempt 2 (delay=1s, 2^0=1)

    BQ  ->>+ WW   : process job { deliveryId: "del_001", attempt: 2 }
    WW  ->>+ EP   : POST https://subscriber.example.com/webhooks { ...payload }
    EP  -->>- WW   : 502 Bad Gateway (second failure)

    WW  ->>+ WDR  : update("del_001", { status: "failed", http_status_code: 502, attempt_number: 2 })
    WDR -->>- WW   : updated
    WW  ->>+ WSR  : incrementFailureCount("sub_abc")  // failure_count = 2
    WSR -->>- WW   : updated
    WW  ->>+ BQ   : add(..., { delay: 2000 })  // 2^1=2s
    BQ  -->>- WW   : Job { id: "job_3" }
    WW  -->>- BQ   : void

    Note over BQ,WW: Attempt 3 (delay=2s, 2^1=2)

    BQ  ->>+ WW   : process job { deliveryId: "del_001", attempt: 3 }
    WW  ->>+ EP   : POST https://subscriber.example.com/webhooks { ...payload }
    EP  -->>- WW   : Connection timeout (third failure)
    WW  ->>+ WDR  : update("del_001", { status: "failed", attempt_number: 3, error_message: "ETIMEDOUT" })
    WDR -->>- WW   : updated
    WW  ->>+ BQ   : add(..., { delay: 4000 })  // 2^2=4s
    BQ  -->>- WW   : Job { id: "job_4" }
    WW  -->>- BQ   : void

    Note over BQ,WW: Attempt 4 (delay=4s, 2^2=4)

    BQ  ->>+ WW   : process job { deliveryId: "del_001", attempt: 4 }
    WW  ->>+ EP   : POST https://subscriber.example.com/webhooks { ...payload }
    EP  -->>- WW   : 503 Service Unavailable (fourth failure)
    WW  ->>+ WDR  : update("del_001", { status: "failed", attempt_number: 4 })
    WDR -->>- WW   : updated
    WW  ->>+ BQ   : add(..., { delay: 8000 })  // 2^3=8s
    BQ  -->>- WW   : Job { id: "job_5" }
    WW  -->>- BQ   : void

    Note over BQ,WW: Attempt 5 (delay=8s, 2^3=8)

    BQ  ->>+ WW   : process job { deliveryId: "del_001", attempt: 5 }
    WW  ->>+ EP   : POST https://subscriber.example.com/webhooks { ...payload }
    EP  -->>- WW   : 500 Internal Server Error (fifth failure — max reached)

    WW  ->>+ WDR  : deadLetter("del_001")
    Note right of WDR: UPDATE webhook_deliveries<br/>SET status = 'dead_lettered'<br/>WHERE id = 'del_001'
    WDR -->>- WW   : updated

    WW  ->>+ WSR  : incrementFailureCount("sub_abc")  // failure_count = 5
    WSR ->>  WSR  : failure_count >= max_failures (5) → suspend
    WSR ->>+ WSR  : suspend("sub_abc")
    Note right of WSR: UPDATE webhook_subscriptions<br/>SET status = 'suspended'<br/>WHERE id = 'sub_abc'
    WSR -->>- WSR  : updated
    WSR -->>- WW   : updated

    WW  ->>+ DLQ  : add("webhook-dead-letters", { deliveryId: "del_001", subscriptionId: "sub_abc", reason: "max_retries_exceeded" })
    DLQ -->>- WW   : Job enqueued for manual investigation

    WW  -->>- BQ   : void (job complete)
    Note over WW,DLQ: Dead-lettered. Ops team alerted via alert_rules monitor.
```

---

## 7. SD-006: Developer Portal Create Application and Generate API Key

Full portal flow: consumer authenticates via session, creates an application, then generates an HMAC
API key. The raw key is returned exactly once and never persisted.

```mermaid
sequenceDiagram
    autonumber
    participant U    as Developer (Browser)
    participant P    as Portal API (Next.js API Route)
    participant AR   as ApplicationRepository
    participant AKR  as ApiKeyRepository
    participant ALR  as AuditLogRepository
    participant TC   as TokenCache (Redis)
    participant Q    as BullMQ (analytics-events)

    Note over U,P: Pre-condition: Developer has an active session JWT

    U   ->>+ P    : POST /api/portal/applications<br/>Authorization: Bearer <sessionJwt><br/>{ "name": "My Trading App", "subscription_plan_id": "plan_growth", "description": "..." }

    P   ->>  P    : verifySessionJwt(jwt) → consumerId = "con_xyz"
    P   ->>+ AR   : countByConsumer("con_xyz")
    AR  -->>- P    : 2 (current count)
    P   ->>  P    : check plan.max_applications (10) → 2 < 10 OK

    P   ->>+ AR   : create({ consumer_id: "con_xyz", subscription_plan_id: "plan_growth", name: "My Trading App" })
    Note right of AR: INSERT INTO applications (consumer_id, subscription_plan_id, name, ...)<br/>RETURNING *
    AR  -->>- P    : Application { id: "app_001", name: "My Trading App", status: "active" }

    P   ->>+ ALR  : create({ actor_id: "con_xyz", actor_type: "consumer", action: "APPLICATION_CREATED", resource_type: "application", resource_id: "app_001", after_state: {...} })
    ALR -->>- P    : AuditLog { id }

    P   -->>- U    : 201 Created { id: "app_001", name: "My Trading App" }

    Note over U,P: Developer requests API key generation

    U   ->>+ P    : POST /api/portal/applications/app_001/api-keys<br/>{ "name": "Production Key", "scopes": ["read:data","write:data"], "expires_at": "2026-01-01T00:00:00Z" }

    P   ->>  P    : verifySessionJwt(jwt) → consumerId = "con_xyz"
    P   ->>  P    : verifyApplicationOwnership("app_001", "con_xyz")

    P   ->>  P    : rawKey = "gw_live_" + crypto.randomBytes(32).toString("base64url")
    Note right of P: Raw key: "gw_live_K2mZ9vRfP..."<br/>This is the ONLY time it exists in plaintext.

    P   ->>  P    : keyPrefix = rawKey.slice(0, 16)  // "gw_live_K2mZ9vRf"
    P   ->>  P    : keyHash = SHA256(rawKey)
    P   ->>  P    : hmacSecret = crypto.randomBytes(32).toString("hex")
    P   ->>  P    : hmacSecretHash = argon2id(hmacSecret)

    P   ->>+ AKR  : create({ application_id: "app_001", name: "Production Key", key_prefix: keyPrefix, key_hash: keyHash, hmac_secret_hash: hmacSecretHash, scopes, expires_at })
    Note right of AKR: INSERT INTO api_keys (...) RETURNING *
    AKR -->>- P    : ApiKey { id: "key_001", key_prefix: "gw_live_K2mZ9vRf", status: "active" }

    P   ->>+ ALR  : create({ actor_id: "con_xyz", action: "API_KEY_CREATED", resource_type: "api_key", resource_id: "key_001", after_state: { prefix, scopes, expires_at } })
    ALR -->>- P    : AuditLog { id }

    P   ->>+ TC   : set("tkn:api_key:" + keyHash, { apiKey, application }, ttl=300s)
    TC  -->>- P    : OK

    P   ->>+ Q    : add("portal-events", { event: "api_key.created", key_id: "key_001", consumer_id: "con_xyz" })
    Q   -->>- P    : Job enqueued

    P   -->>- U    : 201 Created {<br/>  "id": "key_001",<br/>  "key_prefix": "gw_live_K2mZ9vRf",<br/>  "raw_key": "gw_live_K2mZ9vRf...",<br/>  "hmac_secret": "a3b7f9...",<br/>  "scopes": ["read:data","write:data"],<br/>  "expires_at": "2026-01-01T00:00:00Z",<br/>  "WARNING": "Save these values now. They will not be shown again."<br/>}

    Note over P,U: raw_key and hmac_secret are not stored.<br/>Consumer must save them securely.
```

---

## 8. SD-007: Real-Time Analytics Ingestion

Gateway request completion triggers analytics event buffering in Redis, flushed by a BullMQ worker
to PostgreSQL via bulk COPY.

```mermaid
sequenceDiagram
    autonumber
    participant RP   as RouterPlugin (onResponse)
    participant AP   as AnalyticsPlugin
    participant RB   as RedisBuffer (List)
    participant AW   as Analytics Worker (BullMQ)
    participant AR   as AnalyticsRepository
    participant PG   as PostgreSQL (analytics_events)
    participant MV   as Materialized View (analytics_hourly_summary)

    Note over RP,AP: After upstream response received

    RP  ->>+ AP   : onResponse(responseCtx)
    AP  ->>  AP   : buildAnalyticsEvent(ctx) = {<br/>  id: randomUUID(),<br/>  api_key_id: ctx.apiKey.id,<br/>  application_id: ctx.application.id,<br/>  api_route_id: ctx.matchedRoute.id,<br/>  method: ctx.method,<br/>  path: ctx.path,<br/>  status_code: responseCtx.statusCode,<br/>  latency_ms: Date.now() - ctx.startTime,<br/>  upstream_latency_ms: responseCtx.upstreamResponse.duration,<br/>  region: process.env.AWS_REGION,<br/>  gateway_node_id: process.env.ECS_TASK_ID,<br/>  tags: pluginTags,<br/>  created_at: new Date()<br/>}

    AP  ->>+ RB   : RPUSH analytics:buffer JSON.stringify(event)
    RB  -->>- AP   : listLength = 234

    alt Buffer Threshold Reached (length >= 500) or Flush Interval (every 1s)
        AP  ->>+ RB   : LLEN analytics:buffer
        RB  -->>- AP   : 500 (threshold)
        AP  ->>+ RB   : LPOP analytics:buffer COUNT 500
        RB  -->>- AP   : [event_1, event_2, ..., event_500]
        AP  ->>+ AW   : add("analytics-flush", { events: [...] }, { priority: 1, attempts: 3 })
        AW  -->>- AP   : Job { id: "flush_job_42" }
    end

    AP  -->>- RP   : void (non-blocking, fire-and-forget)

    Note over AW,PG: Analytics Worker Flush

    AW  ->>+ AR   : batchInsert(events[500])
    AR  ->>  AR   : client = await pool.connect()
    AR  ->>  AR   : BEGIN

    AR  ->>  AR   : generate COPY stream:<br/>COPY analytics_events (id, api_key_id, application_id, ..., created_at)<br/>FROM STDIN WITH (FORMAT binary)

    loop For each event in batch
        AR  ->>+ PG   : stream.write(row binary)
        PG  -->>- AR   : buffer accepted
    end

    AR  ->>+ PG   : stream.end() → COPY completes
    Note right of PG: PostgreSQL routes rows to correct monthly partition:<br/>e.g. analytics_events_2025_01<br/>based on created_at range
    PG  -->>- AR   : 500 rows inserted

    AR  ->>  AR   : COMMIT
    AR  -->>- AW   : void

    Note over AW,MV: Every 5 minutes: Materialized View Refresh

    AW  ->>+ PG   : REFRESH MATERIALIZED VIEW CONCURRENTLY analytics_hourly_summary
    Note right of PG: Computes p50/p95/p99 latency, error rates,<br/>request counts per (hour, application, route).<br/>CONCURRENTLY means reads are not blocked.
    PG  -->>- AW   : OK (view refreshed)

    alt Batch Insert Fails
        AR  ->>  AR   : ROLLBACK
        AR  -->>  AW   : throw Error
        AW  ->>  AW   : BullMQ retries (attempts: 3, backoff: exponential)
        Note right of AW: Events are not lost — stored in BullMQ<br/>job payload in Redis until successful insert
    end
```

---

## 9. Error Propagation Patterns

| Error Code          | HTTP Status | Thrown By               | Propagated To   | Client Response Body                                          |
|---------------------|-------------|-------------------------|-----------------|---------------------------------------------------------------|
| `KEY_EXPIRED`       | 401         | ApiKeyAuthService       | AuthPlugin      | `{ "error": "KEY_EXPIRED", "message": "API key has expired" }`|
| `INVALID_SIGNATURE` | 401         | HmacValidator           | ApiKeyAuthService| `{ "error": "INVALID_SIGNATURE" }`                           |
| `TIMESTAMP_TOO_OLD` | 401         | HmacValidator           | ApiKeyAuthService| `{ "error": "TIMESTAMP_TOO_OLD", "tolerance": 300 }`         |
| `IP_FORBIDDEN`      | 403         | ApiKeyAuthService       | AuthPlugin      | `{ "error": "IP_FORBIDDEN", "ip": "1.2.3.4" }`               |
| `SCOPE_INSUFFICIENT`| 403         | ApiKeyAuthService       | AuthPlugin      | `{ "error": "SCOPE_INSUFFICIENT", "required": [...] }`        |
| `RATE_LIMIT_EXCEEDED`| 429        | SlidingWindowRateLimiter| RateLimitPlugin | `{ "error": "RATE_LIMIT_EXCEEDED", "retryAfter": 37 }`        |
| `TRANSFORM_FAILED`  | 400         | JsonataTransformer      | TransformPlugin | `{ "error": "TRANSFORM_FAILED", "details": "..." }`           |
| `SCHEMA_INVALID`    | 400         | SchemaValidator         | TransformPlugin | `{ "error": "SCHEMA_INVALID", "errors": [...] }`              |
| `ROUTE_NOT_FOUND`   | 404         | RouterPlugin            | PluginChain     | `{ "error": "ROUTE_NOT_FOUND" }`                              |
| `UPSTREAM_TIMEOUT`  | 504         | RouterPlugin            | PluginChain     | `{ "error": "UPSTREAM_TIMEOUT", "timeoutMs": 30000 }`         |
| `UPSTREAM_ERROR`    | 502         | RouterPlugin            | PluginChain     | `{ "error": "UPSTREAM_ERROR", "upstream_status": 500 }`       |
| `CIRCUIT_OPEN`      | 503         | CircuitBreaker          | RouterPlugin    | `{ "error": "CIRCUIT_OPEN", "route": "/api/v1/orders" }`      |
| `PKCE_FAILED`       | 400         | OAuthService            | Auth endpoint   | `{ "error": "invalid_grant", "description": "PKCE failed" }`  |
| `invalid_grant`     | 400         | OAuthService            | Token endpoint  | `{ "error": "invalid_grant" }`                                |
| `WEBHOOK_DEAD_LETTERED`| N/A     | WebhookWorker           | DLQ + Alerts    | (no client response; internal event)                          |

All errors are wrapped in a `GatewayError` class that carries:
- `statusCode: number` — HTTP status to return
- `errorCode: string` — machine-readable code for client handling
- `message: string` — human-readable description
- `traceId: string` — OpenTelemetry trace ID for log correlation
- `requestId: string` — unique per-request identifier

```typescript
// src/errors/GatewayError.ts
export class GatewayError extends Error {
    constructor(
        public readonly statusCode: number,
        public readonly errorCode: string,
        message: string,
        public readonly traceId?: string,
        public readonly requestId?: string,
        public readonly details?: unknown
    ) {
        super(message);
        this.name = 'GatewayError';
    }
}
```
