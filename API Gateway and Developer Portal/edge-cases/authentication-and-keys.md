# Edge Cases: Authentication and API Keys — API Gateway and Developer Portal

## Overview

This file documents eight edge cases covering the authentication and API key management layer of the API Gateway and Developer Portal. Authentication is a multi-mechanism system combining **API Key HMAC-SHA256** validation (the primary machine-to-machine auth method), **OAuth 2.0** (for developer portal and delegated access flows), and **JWT** (for inter-service and user-session tokens). API key metadata is stored in **PostgreSQL 15 (RDS)** and cached in **Redis 7 (ElastiCache)**. OAuth state and token records are persisted in PostgreSQL.

The edge cases below document scenarios where these mechanisms fail, are attacked, or behave unexpectedly due to infrastructure issues, clock drift, caching inconsistencies, or adversarial inputs. Each edge case uses the standard five-section analysis template. The goal is to ensure that every failure mode in the authentication path has a documented mitigation and a prevention strategy so that the system degrades gracefully and never silently accepts unauthenticated requests.

**Scope**: These edge cases apply to the gateway's authentication and key validation middleware, the OAuth 2.0 authorisation server component embedded in the portal backend, and the key management APIs exposed through the developer portal. Rate limiting and quota enforcement are covered in `rate-limiting-and-quotas.md`.

---

## EC-AUTH-001 — Redis Unavailable During HMAC Key Validation

| Field | Detail |
|-------|--------|
| **Failure Mode** | The Redis 7 ElastiCache cluster becomes unreachable from the gateway ECS tasks—due to a cluster failover, a network ACL change, or an ElastiCache maintenance window that exceeds its expected duration. On every inbound API request, the gateway's HMAC key validation middleware first queries Redis for the API key record (hash, permissions, rate-limit tier, tenant ID). With Redis unavailable, the `ioredis` client throws a `ECONNREFUSED` or `ETIMEDOUT` error after its configured connection timeout (500 ms). Without a fallback, this would mean every authenticated request fails with `500 Internal Server Error`, rendering the gateway completely non-functional for the duration of the Redis outage. |
| **Impact** | If no fallback is implemented, 100% of API requests that require key-based authentication fail immediately—a complete service outage for all machine-to-machine consumers. Latency increases by at least 500 ms (the Redis connection timeout) before the error is surfaced. If the fallback to PostgreSQL is implemented but not load-tested, the sudden shift of all key validation queries from Redis (sub-millisecond) to PostgreSQL (1–5 ms per query) under full production traffic can overload the RDS instance, causing a secondary database outage. This cascading failure is the most dangerous risk in this edge case. |
| **Detection** | The `ioredis` client emits connection error events; a Prometheus counter `cache_errors_total{backend="redis",operation="get"}` is incremented on every failed Redis lookup. A Grafana alert fires when this counter's rate exceeds `10 per minute`. Separately, a Redis health check endpoint (`/internal/healthz/redis`) is polled by the gateway every 5 seconds and its status is included in the gateway's own `/healthz` response. CloudWatch ElastiCache alarms monitor the cluster's `EngineCPUUtilization` and `CacheClusterDown` metrics. PagerDuty receives a high-urgency alert within 30 seconds of the Redis cluster going down. |
| **Mitigation / Recovery** | A circuit breaker wraps the Redis key lookup. When Redis is unavailable (circuit breaker in OPEN state), the middleware falls back to a direct PostgreSQL query using a read-replica endpoint to avoid write-path pressure. The PostgreSQL query is: `SELECT key_hash, permissions, rate_limit_tier, tenant_id, status FROM api_keys WHERE key_prefix = $1 AND status = 'active'`. A connection pool of 20 PostgreSQL connections is reserved exclusively for this fallback path (separate from the main application pool) to prevent it from starving other database operations. The fallback path is logged with `auth_path=postgres_fallback` so the duration and frequency of fallback usage can be measured. Once Redis recovers, the circuit breaker enters HALF_OPEN, validates a single probe key lookup, and closes on success, resuming normal cached validation within 10 seconds. |
| **Prevention** | Configure ElastiCache in **cluster mode with Multi-AZ replication** (at least one replica per shard). Enable **automatic failover** so ElastiCache promotes a replica to primary within 30 seconds of primary failure, keeping the Redis outage window below the circuit breaker trip threshold. Set the `ioredis` `retryDelayOnFailover` and `retryDelayOnClusterDown` to `100 ms` with a maximum of 3 retries before the circuit breaker is consulted. Load-test the PostgreSQL fallback path at `100%` of peak traffic to verify the read replica can handle the full query load before relying on it in production. Document the fallback behaviour in runbooks so on-call engineers know that elevated RDS query volume during a Redis outage is expected and not a secondary incident. |

---

## EC-AUTH-002 — API Key Brute-Force Enumeration Attack

| Field | Detail |
|-------|--------|
| **Failure Mode** | An attacker attempts to discover valid API keys by systematically sending requests with crafted key values—either sequential prefix scanning (the key format includes a human-readable prefix such as `gw_live_` followed by a random suffix, and the attacker tries all possible suffixes), or dictionary-based attacks using common key formats leaked from other breaches. Because HMAC-SHA256 validation involves a database lookup followed by a constant-time hash comparison, each guess incurs a real processing cost on the gateway and database. If rate limiting is applied only at the per-key level (not the per-IP level), an attacker using rotating IPs can generate millions of guesses before any throttle triggers. |
| **Impact** | At scale, a successful brute-force enumeration would yield a valid API key that can be used to make authorised API calls impersonating a legitimate tenant. Even if no key is successfully discovered, the attack consumes gateway CPU (HMAC computation), Redis query capacity (cache lookups for non-existent keys), and PostgreSQL read capacity (cache misses for unknown prefixes), potentially degrading performance for legitimate users. A 401 authentication failure for a non-existent key prefix is a database read with zero cache benefit (the key has never been cached), making each guess disproportionately expensive. |
| **Detection** | An IP-level rate limiter (independent of the API key rate limiter) counts `auth_failures_total{reason="invalid_key"}` per source IP per minute. When a single IP exceeds **50 failed authentication attempts in 60 seconds**, a `warning` alert fires and the IP is flagged. When it exceeds **100 failures in 60 seconds**, the IP is automatically added to the WAF IP block list for 1 hour and a `critical` security alert is sent to the security team Slack channel and PagerDuty. Distributed attacks using rotating IPs are detected by an anomaly detector that monitors the overall `auth_failures_total` rate across all IPs: if the gateway-wide 401 rate rises more than **10x** the 24-hour baseline, a security incident is declared regardless of per-IP rates. |
| **Mitigation / Recovery** | The WAF IP block list automatically drops requests from flagged IPs at the CloudFront edge, preventing them from reaching the gateway at all. For distributed attacks, global rate limiting on the `/auth` validation path is tightened by the on-call engineer via the admin API (`PATCH /admin/rate-limits/global` with reduced thresholds). HMAC validation uses `crypto.timingSafeEqual` for the hash comparison to ensure that the response time does not leak information about how close a guess was to a valid key. Invalid key prefixes (not found in PostgreSQL) are negatively cached in Redis with a short TTL (`60 seconds`) to prevent the same non-existent prefix from generating repeated database reads during an attack. The security team reviews the attack vector and issues a post-incident report within 48 hours. |
| **Prevention** | Generate all API keys using a cryptographically secure random number generator producing **256 bits of entropy** (32 bytes, base62-encoded to ~43 characters). At this entropy level, brute-force enumeration is computationally infeasible even with a trillion guesses per second. Include a **key prefix** (e.g., `gw_live_`) for human recognition, but make the random suffix 32 bytes minimum. Never log full API keys—log only the first 8 characters (the prefix) for correlation. Enforce IP-level rate limiting on all unauthenticated and failed-authentication requests from the first request, not only after a threshold is exceeded. Require API keys to be associated with HMAC request signing (not just key identity) so a stolen or guessed key without the HMAC secret cannot be used. |

---

## EC-AUTH-003 — JWT Token with Future iat Claim Due to Clock Skew

| Field | Detail |
|-------|--------|
| **Failure Mode** | An issuing service (the OAuth authorisation server or an inter-service token issuer) has its system clock drift forward relative to the gateway's clock by more than **5 minutes**—the default `nbf`/`iat` tolerance configured in the JWT validation library (`jose`). This can occur after an NTP synchronisation failure, after a container restart that does not immediately sync time, or during daylight-saving-time edge cases in misconfigured environments. The issued JWT contains an `iat` (issued-at) claim that is in the future from the gateway's perspective. The `jose` library's `clockTolerance` option controls how much skew is accepted; beyond this tolerance, the token is rejected with `JWTClaimValidationFailed: "iat" claim timestamp check failed`. |
| **Impact** | All tokens issued by the drifted service are rejected by the gateway during the skew window. Users or services that have just obtained a new token are denied access immediately, even though the token is cryptographically valid and was legitimately issued. The failure is silent and confusing: the client receives `401 Unauthorized` with a generic message, and without examining the `iat` claim vs. the current time, the root cause is not obvious. If the drifted service is the primary OAuth server, all new OAuth token issuances are affected; existing tokens (issued before the drift) continue to work until they expire. |
| **Detection** | The JWT validation error is logged as a structured event `jwt_validation_error{reason="future_iat", issuer="<iss>", iat_delta_seconds=<N>}`. The `iat_delta_seconds` field captures how far in the future the `iat` claim is, enabling rapid root cause identification. A Prometheus counter `jwt_validation_errors_total{reason="future_iat"}` is monitored; a Grafana alert fires when this counter exceeds **5 per minute** for any single issuer. Separately, a CloudWatch alarm monitors NTP offset for all ECS tasks via a custom metric emitted by the task's health-reporting agent: `ntp_offset_seconds > 30` triggers a `warning`; `> 300` triggers a `critical` infrastructure alert. |
| **Mitigation / Recovery** | The gateway's `jose` library is configured with `clockTolerance: 300` (5 minutes), meaning skews up to 5 minutes are silently accepted. When the clock skew exceeds 5 minutes and tokens begin being rejected, the mitigation is to trigger NTP re-synchronisation on the issuing service's ECS task (by restarting the task, which forces time sync on container start) or by running `chronyc makestep` if exec access is available. Tokens that were rejected during the skew window must be re-requested by the client; there is no server-side replay mechanism. If the skew is detected within the 5-minute tolerance window (via the NTP offset alarm), the on-call engineer can proactively restart the issuing task before any tokens are rejected. |
| **Prevention** | Configure all ECS task definitions to use the Amazon Time Sync Service (`169.254.169.123`) as the NTP source, which is available from any ECS Fargate task without additional networking configuration. Enable the CloudWatch NTP offset metric emission as a sidecar process in every task definition. Set the `clockTolerance` in `jose` to **300 seconds** (5 minutes) as the standard deployment value, and document this as the maximum acceptable NTP drift before tokens are rejected. Add an integration test in the CI pipeline that issues a JWT with `iat = now + 360s` and asserts a `401` response, and another with `iat = now + 240s` asserting a `200` response, to validate tolerance boundaries after every library upgrade. |

---

## EC-AUTH-004 — OAuth Authorization Code Reuse Attempt

| Field | Detail |
|-------|--------|
| **Failure Mode** | An OAuth 2.0 authorization code (issued during the `/oauth/authorize` flow) is intercepted by an attacker—via a compromised redirect URI, a network intercept, or a leaked server-side log entry—after the legitimate client has already exchanged it for an access token and refresh token. The attacker attempts to exchange the same code a second time at the `/oauth/token` endpoint. Per RFC 6749 §4.1.2, authorization codes must be single-use and short-lived, but a naive implementation that relies only on the code TTL (not on a consumed-flag or delete-on-use) may accept the second exchange if it occurs before the TTL expires. |
| **Impact** | If the second code exchange succeeds, the attacker receives a fully valid access token and refresh token pair, gaining the same permissions as the legitimate user for the duration of the token's TTL. Per RFC 6749 §4.1.2, the correct response to detecting code reuse is to **invalidate all tokens previously issued from that authorization code**—including the legitimate user's access and refresh tokens—leaving the legitimate user suddenly unauthenticated. This is intentional by the spec (to signal compromise), but it causes immediate user-visible disruption and requires the user to re-authenticate. |
| **Detection** | Authorization codes are stored in PostgreSQL with a `status` column (`pending`, `consumed`, `expired`). The token exchange endpoint executes `UPDATE oauth_codes SET status = 'consumed', consumed_at = NOW() WHERE code = $1 AND status = 'pending' RETURNING id`. If the UPDATE returns zero rows (the code was already consumed or does not exist), the endpoint returns `400 invalid_grant`. A separate counter `oauth_code_reuse_attempts_total` is incremented when the code exists but `status = 'consumed'`. A Grafana alert fires immediately when this counter is non-zero, as any value above 0 indicates a potential code interception attack. The client ID, redirect URI, and IP of the second exchange attempt are logged for security review. |
| **Mitigation / Recovery** | On detection of a code reuse attempt, the OAuth server immediately invalidates all access tokens and refresh tokens that were issued using the original exchange of that code: `UPDATE oauth_tokens SET status = 'revoked', revoked_at = NOW(), revoke_reason = 'code_reuse_detected' WHERE authorization_code_id = $1`. A Redis pub/sub message is published to the `tokens:revoked` channel so all gateway instances flush the affected tokens from their JWT validation cache within 1 second. The legitimate user is forced to re-authenticate. A security audit event is created and the security team is notified via PagerDuty with the full audit trail (original exchange IP, reuse attempt IP, time delta between exchanges). |
| **Prevention** | Use **PostgreSQL row-level locking** (`SELECT ... FOR UPDATE`) on the code record during exchange to prevent race conditions where two concurrent exchange requests both see `status = 'pending'` before either commits. Enforce a short code TTL of **10 minutes** (configurable) and delete consumed codes immediately after successful exchange rather than relying on TTL expiry for cleanup. Require **PKCE (Proof Key for Code Exchange)** for all public clients (RFC 7636): even if an authorization code is intercepted, it cannot be exchanged without the `code_verifier` that only the legitimate client possesses. Log all token exchange attempts (successful and failed) with source IP, client ID, and code ID to the audit log. |

---

## EC-AUTH-005 — API Key Accidentally Committed to Public GitHub Repository

| Field | Detail |
|-------|--------|
| **Failure Mode** | A developer inadvertently commits a `.env` file, a configuration file, or inline source code containing a live API key to a public GitHub repository. The key may be committed directly, pushed within a Docker image layer history, or embedded in a CI/CD pipeline configuration file. GitHub's push protection and secret scanning services detect known credential formats, but there is a window between the push and the detection/notification during which the key is publicly visible and indexable. Automated bots scan GitHub for newly committed secrets within seconds of a public push. |
| **Impact** | The exposed API key can be used immediately by any actor who discovers it to make authenticated API calls with the permissions associated with that key. Depending on the key's permission scope (read-only vs. read-write, specific resources vs. all resources), this could mean unauthorised data access, resource creation, data deletion, or billing charges. If the key belongs to a production tenant, the impact extends to that tenant's data. Discovery of the exposure may not occur until the affected tenant notices unexpected API activity or receives an unusual billing invoice. |
| **Detection** | GitHub **push protection** and **secret scanning** are enabled on all GitHub organisation repositories. When a secret matching the gateway's API key format (`gw_live_[A-Za-z0-9]{40,}`) is detected, GitHub sends a webhook to the gateway's security webhook endpoint (`POST /internal/webhooks/github-secret-scan`). This endpoint triggers an immediate key revocation workflow. Additionally, **GitGuardian** (or an equivalent external scanner such as TruffleHog Cloud) is integrated and monitors all public GitHub repositories for the organisation's key patterns, with a webhook that fires within seconds of detection. The security team receives a PagerDuty critical alert and an email notification within 1 minute of detection. |
| **Mitigation / Recovery** | The security webhook endpoint immediately revokes the exposed key: `UPDATE api_keys SET status = 'revoked', revoked_at = NOW(), revoke_reason = 'public_exposure' WHERE key_prefix = $1`. A Redis pub/sub invalidation message is published to flush the key from all gateway caches within 1 second. The affected tenant is notified via email with instructions to generate a new key from the developer portal. The security team reviews the API access logs for the exposed key from the time of commit to the time of revocation to identify any unauthorised access. A new key is issued to the tenant. The GitHub repository history is scrubbed using **BFG Repo Cleaner** or `git filter-repo` to remove the secret from all commits, and the repository is force-pushed. The developer receives a mandatory security training reminder. |
| **Prevention** | Enforce **pre-commit hooks** using `detect-secrets` (or `git-secrets`) across all developer workstations and CI pipelines to prevent secrets from being committed in the first place. Enable **GitHub push protection** at the organisation level to block pushes containing known secret patterns. Instruct all developers to store API keys and credentials exclusively in **AWS Secrets Manager** or environment variable injection via the ECS task definition, never in source files or `.env` files checked into version control. Add the API key format pattern to the organisation's custom secret scanning patterns in GitHub Advanced Security. Include a pre-commit hook validation step in the CI pipeline that runs `detect-secrets scan` and fails the build if any secrets are detected. |

---

## EC-AUTH-006 — Revoked API Key Still Cached in Redis (Stale Cache After Revocation)

| Field | Detail |
|-------|--------|
| **Failure Mode** | An API key is revoked—either by the tenant through the developer portal, by an administrator via the admin API, or automatically by a security incident response workflow. The revocation updates the key's `status` to `revoked` in PostgreSQL immediately. However, the gateway's HMAC validation middleware caches API key records in Redis with a TTL of **5 minutes** to reduce database load. If the key was cached before revocation, the cached record still shows `status = 'active'` for up to 5 minutes after the PostgreSQL update. During this window, requests using the revoked key are incorrectly accepted by any gateway instance that has the stale cache entry. |
| **Impact** | A revoked key continues to function for up to the Redis TTL duration (5 minutes by default) after revocation. In an incident response scenario—where a key has been compromised and is being actively abused—this 5-minute window represents continued unauthorised access that the security team believed had been stopped. For high-security tenants or incidents involving sensitive data, this gap is unacceptable. The severity is proportional to what the attacker can do in 5 minutes with the key and what data they can exfiltrate or modify. |
| **Detection** | The revocation API publishes an invalidation event to a Redis pub/sub channel `api_keys:revoked` with the key prefix as the message payload. All gateway instances subscribe to this channel and immediately delete the cache entry for the revoked key prefix when the message is received. A counter `cache_invalidation_messages_received_total` is incremented on each subscriber on receipt of the message. After revocation, the key's `revoked_at` timestamp is stored in PostgreSQL; if any access log entry shows a request authenticated with that key after `revoked_at`, a `post_revocation_access_detected` security alert is fired automatically by a log analysis rule in CloudWatch Insights. |
| **Mitigation / Recovery** | On receiving the `api_keys:revoked` pub/sub message, each gateway instance calls `redis.del(keyPrefix)` to immediately remove the cache entry. The deletion is confirmed by checking the `DEL` command return value (should be `1`). If a gateway instance was disconnected from Redis pub/sub at the moment of revocation and missed the message, the normal TTL expiry provides a maximum 5-minute fallback window. For high-urgency revocations (confirmed compromise, active abuse), the on-call engineer can trigger a full cache flush on all instances via the admin API (`POST /admin/cache/invalidate-key` with the key prefix). Post-revocation access events trigger immediate key prefix blocking at the WAF level. |
| **Prevention** | Reduce the standard Redis cache TTL for API key records from 5 minutes to **60 seconds** for keys in tenants with elevated security classification (e.g., financial, healthcare). Implement Redis pub/sub key invalidation as described above as the standard revocation mechanism—reducing the effective window from TTL-based (up to 5 minutes) to near-instant (< 1 second for connected instances). Ensure Redis Streams (with consumer groups) is used for the invalidation channel rather than plain pub/sub, so that instances that were temporarily disconnected replay missed invalidation events on reconnection. Add a revocation confirmation step in the developer portal that displays the estimated cache flush time and warns that requests may still be accepted for up to 60 seconds. |

---

## EC-AUTH-007 — mTLS Client Certificate Presented with Revoked CA Certificate

| Field | Detail |
|-------|--------|
| **Failure Mode** | A small number of high-trust API consumers are configured to authenticate using mutual TLS (mTLS), presenting a client certificate signed by a trusted Certificate Authority registered in the gateway's trust store. The CA's own certificate is revoked—either because the CA was compromised, its private key was exposed, or its operating organisation shut down—and the CA's OCSP responder begins returning `revoked` for all certificates it ever issued. When the gateway's TLS layer performs OCSP stapling or online OCSP verification for a new mTLS connection from a client holding a certificate from this CA, the OCSP check returns `revoked`, and the TLS handshake is aborted at the certificate verification step. |
| **Impact** | All clients holding certificates issued by the revoked CA are immediately locked out—they cannot establish any new connections to the gateway. This is the correct security behaviour (preventing compromised-CA-issued certificates from being accepted), but it is operationally disruptive for legitimate clients who had no knowledge of their CA's revocation. They receive a TLS connection failure (not even an HTTP error response), which is harder to diagnose than a `401`. If the revoked CA issued certificates for many tenants, the outage is broad. |
| **Detection** | TLS handshake failures due to certificate verification errors are logged at the Fastify/Node.js `tls` layer as structured events `tls_handshake_error{reason="cert_verify_failed", detail="OCSP_revoked"}`. A Prometheus counter `mtls_cert_errors_total{reason="revoked_ca"}` is incremented per failure. A Grafana alert fires when this counter exceeds `5 per minute`. Separately, the OCSP responder URL listed in all registered CA certificates is polled every 6 hours by a monitoring Lambda function. If the OCSP response for any registered CA changes from `good` to `revoked`, a `critical` infrastructure alert is fired immediately, giving the operations team advance warning before the client-facing TLS failures begin. |
| **Mitigation / Recovery** | The immediate mitigation is to remove the revoked CA's certificate from the gateway's trust store (the `ca-bundle.pem` mounted into the ECS task). This change requires an ECS task definition update and a rolling deployment (< 5 minutes). Clients that held certificates from the revoked CA must obtain new certificates from a replacement CA. The gateway's CA rotation runbook documents the process: (1) add new CA to trust store, (2) deploy updated trust store, (3) notify affected tenants to present new certificates, (4) remove old CA from trust store after migration window (typically 7 days). During the migration window, both CAs are trusted simultaneously. |
| **Prevention** | Enable **OCSP stapling** on the gateway's TLS configuration so that the OCSP validity check is performed at the gateway level using a cached staple (refreshed every 1 hour) rather than requiring a live OCSP lookup on every new connection—this reduces latency and protects against OCSP responder unavailability. Configure **CRL Distribution Points** as a fallback for OCSP failures. Monitor the expiry date of every registered CA certificate with the same 30/14/7/1-day alert ladder used for upstream certificates (EC-ROUTE-008). Require tenants using mTLS to register their CA certificate and point of contact in the developer portal so they can be notified rapidly during a CA revocation event. Conduct a CA rotation drill annually to ensure the trust store update process is practiced and documented. |

---

## EC-AUTH-008 — OAuth Refresh Token Has Expired (User Must Re-Authenticate)

| Field | Detail |
|-------|--------|
| **Failure Mode** | An OAuth 2.0 refresh token has a finite lifetime (default: **30 days** for confidential clients, **7 days** for public clients). When a client application attempts to use an expired refresh token to obtain a new access token at the `/oauth/token` endpoint with `grant_type=refresh_token`, the server returns `400 Bad Request` with `{"error":"invalid_grant","error_description":"refresh_token_expired"}`. This is the expected RFC 6749 behaviour, but the failure mode emerges when the client application does not handle this error gracefully—crashing, entering an error loop, or presenting the user with a confusing technical error rather than a clean "please log in again" prompt. |
| **Impact** | The user is logged out and must complete the full OAuth authorisation flow again. For web portal users, this means being redirected to the login page, which is a minor inconvenience if the UX is well-designed but a significant disruption if it occurs during a critical workflow (e.g., mid-transaction on the developer portal). For server-to-server integrations using long-lived refresh tokens, expiry can cause a background job or integration to begin failing silently at the 30-day mark—particularly dangerous if the job runs infrequently and the failure is not immediately noticed. |
| **Detection** | The gateway logs `oauth_refresh_error{reason="expired_refresh_token",client_id="<id>"}` for every failed refresh attempt. A Prometheus counter `oauth_refresh_errors_total{reason="expired_refresh_token"}` is monitored. A Grafana alert fires when the count exceeds **20 per hour** for any single `client_id`, indicating a client application is in a retry loop or that many users are experiencing simultaneous expiry. The developer portal's own session management layer catches `invalid_grant` responses from the OAuth token endpoint and displays a user-friendly "Your session has expired. Please sign in again." message rather than surfacing the raw error. |
| **Mitigation / Recovery** | The gateway returns `401 Unauthorized` (not `400`—the portal frontend treats `401` as the session-expired signal for consistent UX handling) with `{"error":"session_expired","error_description":"Your session has expired. Please sign in to continue.","login_url":"/auth/login"}`. The Next.js portal intercepts this response in its global Axios/fetch interceptor and redirects the user to the login page, preserving the user's current page URL as a `redirect_to` query parameter so they are returned to their previous location after re-authentication. For server-to-server integrations, the client SDK documentation and error handling guide explicitly covers the `expired_refresh_token` case with a code example showing how to trigger re-authentication. |
| **Prevention** | Implement a **sliding-window refresh token TTL**: each time a refresh token is successfully used to obtain a new access token, the refresh token's expiry is extended by the standard TTL (30 days), ensuring that active users never experience unexpected expiry. Set a lower TTL only for refresh tokens that have not been used for more than 30 days (truly idle sessions). Add a **proactive refresh** mechanism to the portal frontend: if the access token's `exp` is within 5 minutes of expiry and the user is active, silently refresh the access token in the background using the refresh token before it expires. Emit a `token_refresh_approaching_expiry` event at 7 days before refresh token expiry, processed by a background job that sends the developer an email warning: "Your API integration's OAuth session will expire in 7 days. Please re-authenticate your integration." |

---

## Summary Table

| ID | Name | Severity | Detection Method | Recovery Time |
|----|------|----------|-----------------|---------------|
| EC-AUTH-001 | Redis Unavailable During HMAC Key Validation | High | `cache_errors_total` rate alert; Redis health check; CloudWatch ElastiCache alarm | 10–30 seconds (circuit breaker + PostgreSQL fallback); 30 seconds for Redis failover |
| EC-AUTH-002 | API Key Brute-Force Enumeration Attack | Critical | Per-IP `auth_failures_total` threshold; gateway-wide 401 rate anomaly; WAF rate rule | Immediate for IP block (WAF); ongoing monitoring for distributed attack |
| EC-AUTH-003 | JWT Token with Future iat Claim (Clock Skew) | Medium | `jwt_validation_errors_total{reason="future_iat"}`; NTP offset CloudWatch alarm | 1–5 minutes (ECS task restart to re-sync NTP) |
| EC-AUTH-004 | OAuth Authorization Code Reuse Attempt | High | `oauth_code_reuse_attempts_total` counter; PostgreSQL consumed-flag check | Immediate token revocation (< 1 second); user must re-authenticate |
| EC-AUTH-005 | API Key Committed to Public GitHub Repository | Critical | GitHub push protection webhook; GitGuardian/TruffleHog scan; security webhook | < 1 minute (automated revocation); tenant notified within 5 minutes |
| EC-AUTH-006 | Revoked API Key Still Cached in Redis | High | Post-revocation access log alert; `cache_invalidation_messages_received_total`; pub/sub receipt | < 1 second (Redis pub/sub invalidation); max 60 seconds (TTL fallback) |
| EC-AUTH-007 | mTLS Client Certificate with Revoked CA | High | `mtls_cert_errors_total{reason="revoked_ca"}`; OCSP poll monitoring Lambda | 5–10 minutes (trust store update + rolling ECS deploy) |
| EC-AUTH-008 | OAuth Refresh Token Expired | Medium | `oauth_refresh_errors_total{reason="expired_refresh_token"}`; portal UX error events | Immediate (user re-authenticates); sliding-window TTL prevents recurrence |

---

## Appendix A: Authentication Configuration Reference

The following configuration values govern the authentication and key-validation behaviour described in the edge cases above. Values are managed in `src/config/auth.ts` and injected as environment variables into the ECS task definition.

```typescript
// src/config/auth.ts
export const authConfig = {
  apiKey: {
    // EC-AUTH-001: Redis TTL for cached API key records (seconds)
    cacheTtlSeconds: 300,
    // EC-AUTH-006: reduced TTL applied after a revocation event
    postRevocationTtlSeconds: 60,
    // EC-AUTH-001: reserved PostgreSQL connection pool size for fallback
    postgressFallbackPoolSize: 20,
    // EC-AUTH-002: number of characters in the public key prefix (e.g. "gw_live_")
    keyPrefixLength: 8,
    // EC-AUTH-002: total entropy length of the random suffix in bytes
    keyEntropySizeBytes: 32,
    // EC-AUTH-002: max failed auth attempts per IP per 60 seconds before WAF block
    bruteForceIpThreshold: 50,
  },
  jwt: {
    // EC-AUTH-003: tolerated clock skew between issuer and gateway (seconds)
    clockToleranceSeconds: 300,
    // algorithm allow-list — RS256 only; HS256 is explicitly rejected
    allowedAlgorithms: ['RS256'],
    // EC-AUTH-003: issuer URLs whose tokens are accepted
    trustedIssuers: [
      'https://auth.internal.example.com',
      'https://portal.example.com',
    ],
  },
  oauth: {
    // EC-AUTH-004: authorization code TTL in seconds
    authCodeTtlSeconds: 600,
    // EC-AUTH-008: access token TTL in seconds
    accessTokenTtlSeconds: 3_600,
    // EC-AUTH-008: refresh token TTL for confidential clients (seconds)
    refreshTokenTtlSeconds: 2_592_000,
    // EC-AUTH-008: refresh token TTL for public clients (seconds)
    publicClientRefreshTokenTtlSeconds: 604_800,
    // EC-AUTH-008: sliding window extension on each successful refresh (seconds)
    refreshTokenSlidingWindowSeconds: 2_592_000,
    // EC-AUTH-004: whether PKCE is required for public clients
    requirePkceForPublicClients: true,
  },
  mtls: {
    // EC-AUTH-007: OCSP staple refresh interval in milliseconds
    ocspStapleRefreshMs: 3_600_000,
    // EC-AUTH-007: path to the PEM bundle of trusted CA certificates
    caBundlePath: '/etc/gateway/tls/ca-bundle.pem',
    // EC-AUTH-007: whether to enforce OCSP verification (disable only in break-glass)
    enforceOcsp: true,
  },
};
```

---

## Appendix B: Redis Key Schema for Authentication Data

The gateway stores authentication-related data in Redis using the following key naming conventions. Understanding this schema is essential for diagnosing cache-related edge cases (EC-AUTH-001, EC-AUTH-006).

| Redis Key Pattern | Data Stored | TTL | Related EC |
|-------------------|------------|-----|-----------|
| `apikey:{prefix}` | Serialised API key record (JSON): `{keyHash, permissions, tenantId, rateLimitTier, status}` | 300 s (configurable) | EC-AUTH-001, EC-AUTH-006 |
| `apikey:negative:{prefix}` | Negative cache entry for non-existent key prefix (prevents DB read on repeat invalid guesses) | 60 s | EC-AUTH-002 |
| `oauth:code:{code_id}` | OAuth authorization code record: `{clientId, redirectUri, scope, pkceChallenge, consumed}` | 600 s | EC-AUTH-004 |
| `oauth:token:{jti}` | JWT revocation status: `{revoked: true, revokedAt: <timestamp>}` | Equal to token remaining TTL | EC-AUTH-004, EC-AUTH-006 |
| `mtls:ocsp:{thumbprint}` | Cached OCSP staple for a CA certificate | 3600 s | EC-AUTH-007 |
| `revoke:broadcast` | Redis Streams channel for key/token revocation events (consumer group per gateway task) | Stream retention: 24 h | EC-AUTH-006 |

All Redis values are serialised as compact JSON. Keys are namespaced by the Redis database index (database `1` for auth data, database `0` for rate-limit counters) to allow separate eviction policies per data type.

---

## Appendix C: Security Event Log Format

All authentication-related security events are emitted as structured JSON log entries to CloudWatch Logs and to the audit log stream. The following table describes the fields included in each event type.

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `event_type` | string | Identifies the specific security event | `auth_failure`, `key_revoked`, `oauth_code_reuse` |
| `timestamp` | ISO 8601 string | UTC timestamp of the event | `2025-01-15T14:23:01.456Z` |
| `trace_id` | string | OpenTelemetry trace ID for the request | `4bf92f3577b34da6a3ce929d0e0e4736` |
| `source_ip` | string | Client IP address (from `X-Forwarded-For` after trust proxy unwinding) | `203.0.113.42` |
| `api_key_prefix` | string | First 8 characters of the API key used (never the full key) | `gw_live_` |
| `tenant_id` | UUID | Tenant associated with the key or OAuth client | `a1b2c3d4-...` |
| `oauth_client_id` | string | OAuth client ID for OAuth-related events | `portal-app-prod` |
| `failure_reason` | string | Machine-readable failure code | `invalid_hmac`, `key_revoked`, `jwt_expired`, `future_iat` |
| `auth_path` | string | Which auth backend was used | `redis_cache`, `postgres_fallback` |
| `severity` | string | Event severity matching the edge case classification | `critical`, `high`, `medium`, `low` |

Security events are retained in CloudWatch Logs for 90 days (standard tier) and archived to S3 Glacier for 7 years to satisfy compliance requirements. The audit log S3 bucket has Object Lock enabled (COMPLIANCE mode) to prevent tampering (see EC-SEC-008).

---

## Appendix D: Prometheus Alert Rule Definitions

The following PromQL alert expressions correspond to the detection methods described in the authentication edge cases. These rules are deployed alongside the routing alerts in the `gateway.auth` Prometheus rule group.

```yaml
# k8s/monitoring/auth-alerts.yaml
groups:
  - name: gateway.auth
    interval: 15s
    rules:

      - alert: RedisAuthCacheUnavailable
        expr: >
          rate(cache_errors_total{job="api-gateway",backend="redis",operation="get"}[1m])
          > 10
        for: 30s
        labels:
          severity: high
        annotations:
          summary: "Redis auth cache is returning errors; PostgreSQL fallback is active"
          runbook: "https://runbooks.internal/ec-auth-001"

      - alert: ApiKeyBruteForceDetected
        expr: >
          rate(auth_failures_total{job="api-gateway",reason="invalid_key"}[1m])
          > 100
        for: 0s
        labels:
          severity: critical
        annotations:
          summary: "API key brute-force rate {{ $value | humanize }}/min detected"
          runbook: "https://runbooks.internal/ec-auth-002"

      - alert: JwtFutureIatErrors
        expr: >
          rate(jwt_validation_errors_total{job="api-gateway",reason="future_iat"}[1m])
          > 5
        for: 60s
        labels:
          severity: medium
        annotations:
          summary: "JWT future iat errors from issuer {{ $labels.issuer }}"
          runbook: "https://runbooks.internal/ec-auth-003"

      - alert: OAuthCodeReuseAttempt
        expr: increase(oauth_code_reuse_attempts_total{job="api-gateway"}[5m]) > 0
        labels:
          severity: high
        annotations:
          summary: "OAuth authorization code reuse attempt detected for client {{ $labels.client_id }}"
          runbook: "https://runbooks.internal/ec-auth-004"

      - alert: PostRevocationKeyAccess
        expr: increase(post_revocation_access_total{job="api-gateway"}[1m]) > 0
        labels:
          severity: high
        annotations:
          summary: "Request accepted with a revoked API key (stale cache)"
          runbook: "https://runbooks.internal/ec-auth-006"

      - alert: MtlsCertificateError
        expr: >
          rate(mtls_cert_errors_total{job="api-gateway",reason="revoked_ca"}[1m]) > 5
        for: 30s
        labels:
          severity: high
        annotations:
          summary: "mTLS handshakes failing due to revoked CA for {{ $labels.ca_subject }}"
          runbook: "https://runbooks.internal/ec-auth-007"
```

---

## Appendix E: On-Call Incident Response Quick Reference

**EC-AUTH-001 — Redis Unavailable for Key Validation**

- [ ] Open Grafana → `API Gateway / Cache Health` dashboard; confirm `cache_errors_total` rate spike
- [ ] Check ElastiCache console for cluster health; identify if failover is in progress
- [ ] Verify PostgreSQL fallback is active: look for `auth_path=postgres_fallback` in CloudWatch Logs
- [ ] Monitor RDS read-replica CPU; if > 80%, notify DBA team of elevated fallback load
- [ ] Once ElastiCache failover completes (< 30 s), verify `cache_errors_total` returns to zero
- [ ] If ElastiCache does not recover within 5 minutes, page the infrastructure team

**EC-AUTH-002 — API Key Brute-Force Attack**

- [ ] Confirm attack via `auth_failures_total` by source IP in Grafana
- [ ] Verify WAF has auto-blocked the top offending IPs (check WAF console → IP sets)
- [ ] For distributed attacks, tighten the global WAF rate-based rule threshold via AWS console
- [ ] Review whether any valid keys were discovered: check for `auth_success` events from attacker IP ranges
- [ ] Notify security team; create security incident report within 2 hours
- [ ] Review key generation entropy; ensure all keys have ≥ 32-byte random suffix

**EC-AUTH-005 — API Key Committed to GitHub**

- [ ] Verify GitHub secret scanning webhook triggered automated revocation; check `key_revoked` event in audit log
- [ ] If webhook did not fire, manually revoke the key immediately via admin API: `DELETE /admin/keys/{prefix}`
- [ ] Review API access logs for the exposed key from commit timestamp to revocation timestamp
- [ ] If unauthorised access occurred, notify the affected tenant immediately and preserve logs for forensics
- [ ] Issue a new key to the affected tenant; confirm they have updated their integration
- [ ] Initiate GitHub history scrub with BFG Repo Cleaner; force-push the cleaned repository

**EC-AUTH-006 — Revoked Key Still in Redis Cache**

- [ ] Confirm post-revocation access via `post_revocation_access_total` counter alert
- [ ] Trigger immediate full-key cache flush via admin API: `POST /admin/cache/invalidate-key` with key prefix
- [ ] Verify all gateway instances received the Redis pub/sub invalidation: check `cache_invalidation_messages_received_total` per instance
- [ ] Block the key prefix at the WAF level for immediate protection while investigating
- [ ] Determine root cause of pub/sub miss: was the Redis Streams consumer group offset behind?
- [ ] Review and reduce cache TTL for affected tenant's key tier if the key is high-risk

---

## Appendix F: API Key Lifecycle State Machine

API keys managed through the developer portal follow a defined lifecycle. Understanding this state machine is essential for diagnosing EC-AUTH-005 and EC-AUTH-006.

| State | Description | Allowed Transitions | Cache Behaviour |
|-------|-------------|-------------------|-----------------|
| `pending_activation` | Key created but owner has not yet activated it | → `active` (on first use or explicit activation) | Not cached (no traffic expected) |
| `active` | Key is valid and accepts requests | → `suspended`, `revoked`, `expired` | Cached in Redis with standard TTL |
| `suspended` | Temporarily disabled by tenant or admin | → `active` (if re-enabled), `revoked` | Cache entry deleted immediately on suspension |
| `revoked` | Permanently disabled; cannot be re-enabled | Terminal state | Cache entry deleted via pub/sub within 1 s; negative cache entry added for 24 h |
| `expired` | TTL-based expiry (for time-limited keys) | Terminal state | Cache entry deleted on TTL expiry; no negative cache needed |

Key state transitions are recorded in the `api_key_events` PostgreSQL table with the actor (tenant user ID or admin ID), timestamp, and reason. This table is the authoritative audit trail for all key lifecycle changes and is queried during security incident investigations.
