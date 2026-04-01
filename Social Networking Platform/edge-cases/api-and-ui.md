# API and UI — Edge Cases

## Overview

The API and UI layer is the attack surface closest to the outside world. Abuse ranges from
automated scraping and rate-limit bypass to sophisticated GraphQL query bombs that exhaust
backend resources with a single request. On the client side, optimistic UI updates and
concurrent user interactions create race conditions that can produce inconsistent state. This
file documents the key failure modes and the mitigations needed at each layer of the stack.

---

## Failure Modes

| Failure Mode | Impact | Detection | Mitigation | Recovery | Prevention |
|---|---|---|---|---|---|
| Rate limit bypass via IP rotation | Automated scraping or credential stuffing at scale despite per-IP limits | Unusual request patterns from large IP ranges; user-agent clustering; anomalous data-access breadth | Multi-dimensional rate limiting (IP + user-agent + account + behavioral fingerprint); ASN-level limits | Block offending ASN ranges temporarily; require CAPTCHA for affected accounts | Device fingerprinting as rate-limit key; behavioral anomaly scoring; honeypot endpoints |
| GraphQL query complexity attack | Single deeply nested query exhausts CPU/memory on resolver chain; denial of service | Query cost histogram spike; resolver timeout rate increase; CPU saturation on GraphQL workers | Query complexity scoring (max depth + field count budget); query cost limit enforcement at parse time | Rate-limit offending tokens; serve 429 with Retry-After; scale GraphQL workers | Query complexity analysis in CI; persisted queries enforced for production clients |
| REST API parameter pollution | Conflicting duplicate query parameters produce undefined behavior in backend parsing | Unexpected error patterns in API logs; anomalous response codes on specific endpoints | Strict parameter deduplication at API gateway; first-occurrence wins policy enforced | Return 400 with explicit error message; log for security review | API schema validation with strict mode; parameter pollution unit tests in API test suite |
| Optimistic UI update conflict | Two clients simultaneously update the same resource; one update is silently lost | User-reported data loss; divergence between client state and server state | Server-side OCC (Optimistic Concurrency Control) via `If-Match` / ETag; client rehydration on conflict response | Return 409 Conflict; client rehydrates from server state; user sees merge-conflict UI | ETag support mandatory for all mutable resources; client conflict-handling tested in integration suite |
| Infinite scroll pagination cursor invalidation | User paginating through feed receives duplicates or skips posts when cursor becomes stale | User reports seeing duplicate posts; gap detection in client-side feed deduplication layer | Stable cursor design using keyset pagination (timestamp + ID) resistant to insertions | Detect duplicate IDs client-side; skip already-rendered items | Keyset pagination enforced for all list APIs; cursor validity documented and tested |
| Webhook delivery failure and retry storm | Third-party integrations receive partial event streams; retry storms overwhelm the webhook delivery service | Webhook delivery failure rate alert; retry queue depth growth | Exponential backoff with jitter on delivery retries; per-endpoint circuit breaker; dead-letter queue | Drain dead-letter queue with backpressure; notify webhook owner of degradation | Delivery SLA documentation; per-endpoint health scoring; subscriber-side idempotency guidance |
| API versioning break during migration | Clients using deprecated API version receive unexpected errors after server-side breaking change | Elevated 4xx/5xx rates on deprecated version endpoints; client SDK error reports | API versioning contract with minimum 6-month deprecation notice; shadow traffic to new version before cutover | Rollback API gateway routing to previous version; hotfix breaking change | Backwards-compatibility tests in CI; API schema linting with breaking-change detection |
| UI race condition on double-tap reaction | User double-taps like button; two concurrent PATCH requests create or duplicate reaction | Duplicate reaction record in database; like count incremented by 2 | Client-side debounce (300 ms) + idempotency key on reaction request; server-side upsert semantics | Reconcile reaction count from server; deduplicate via idempotency key | Idempotency key enforcement at API gateway; debounce as standard component in UI button library |

---

## Detailed Scenarios

### Scenario 1: GraphQL Query Complexity Attack

**Trigger**: A malicious actor (or a poorly written third-party client) submits a deeply
nested GraphQL query that traverses a circular relationship: `User → friends → User → friends
→ ...` to depth 12, with each level requesting 50 fields including computed properties. A
single request generates over 2 million resolver invocations.

**Example Query Structure (simplified)**:
```graphql
query {
  user(id: "target") {
    friends(first: 100) {
      friends(first: 100) {
        friends(first: 100) {   # depth 3, already 1,000,000 potential nodes
          id name avatar posts(first: 50) { id text media { url } }
        }
      }
    }
  }
}
```

**Symptoms**:
- GraphQL worker CPU climbs to 100% within 2 seconds of request receipt.
- Response time for all other requests on the same worker pool degrades severely.
- Out-of-memory kill on worker if depth is extreme enough.
- Attacker retries from different tokens, compounding the impact.

**Detection**:
- Query cost calculator at parse time computes depth × breadth × field count score.
- Alert fires when >5 queries/minute exceed cost threshold 500 from a single token.
- Worker CPU saturation alert.

**Mitigation**:
1. **Pre-execution cost analysis**: Parse and score every query before execution. Reject with
   HTTP 400 ("Query complexity limit exceeded") if score >1000.
2. **Maximum query depth limit**: Hard limit of 8 levels of nesting.
3. **Persisted query enforcement**: Production mobile/web clients use persisted queries (hashed
   query store). Ad-hoc queries from unverified tokens are subject to strict complexity caps.
4. **Per-token rate limiting**: >10 complexity-rejected queries/minute from a single token
   results in a 1-hour suspension of that token.
5. **Query timeout**: Any resolver chain exceeding 5 seconds is cancelled with a 504 response.

**Prevention**: Complexity scoring integrated into the GraphQL schema linting pipeline; any
new schema addition that enables circular traversal requires a complexity-test case.

---

### Scenario 2: Optimistic UI Conflict — Concurrent Post Edit

**Trigger**: A user opens the same post in two browser tabs and edits the text simultaneously.
Tab A submits its edit at T+2s; Tab B submits its edit at T+3s. Both were based on version V1
of the post. Tab B's request, if processed naively, silently overwrites Tab A's changes.

**Server-Side Flow**:
- Tab A sends `PATCH /posts/123` with `If-Match: "etag-v1"` → server applies edit, returns
  `ETag: "etag-v2"`.
- Tab B sends `PATCH /posts/123` with `If-Match: "etag-v1"` → server detects stale ETag →
  returns `409 Conflict` with current body at `"etag-v2"`.

**Client Handling on 409**:
1. Tab B receives 409; displays a merge-conflict modal showing the server's current version
   alongside the user's draft.
2. User chooses to merge, overwrite, or discard their draft.
3. User submits final version with the updated ETag from the 409 response body.

**Detection**: 409 rate on write endpoints; client error logging of conflict occurrences.

**Prevention**: ETag support mandated in API specification for all mutable resource types;
client-side conflict handling included in UI component acceptance tests.

---

### Scenario 3: API Rate Limit Bypass via Token Rotation

**Trigger**: A scraper operator registers 10,000 free accounts, each with a valid API token.
Per-token rate limits of 100 requests/minute are met; the scraper round-robins across tokens,
achieving an effective rate of 1,000,000 requests/minute and harvesting user profile data.

**Symptoms**:
- User profile read endpoint traffic 20× above baseline.
- CDN cache hit rate drops as scraper targets random user IDs, bypassing cache.
- Database read replica lag increases; connection pool saturation.

**Detection**:
- Per-endpoint global request rate alert at 5× 7-day baseline.
- Clustering analysis on User-Agent strings reveals uniform scraper fingerprint.
- Behavioral: tokens requesting maximally diverse user IDs in round-robin order (not organic).

**Mitigation**:
1. **Behavioral rate limiting**: Rate limit keyed on behavioral fingerprint (access pattern
   entropy, request timing uniformity) in addition to token identity.
2. **Account creation velocity limit**: New accounts limited to 5 API token requests/minute
   for the first 30 days; rate increases with account trust score.
3. **Honeypot user IDs**: Inject known-fake user IDs into the ID space; any token requesting
   a honeypot ID is flagged as a scraper and rate-limited to 1 req/minute.
4. **ASN-level rate cap**: Data-center ASNs (common for scraper infrastructure) receive
   stricter default rate limits than residential ISPs.
5. **CAPTCHA wall**: Accounts with scraper behavioral fingerprint are required to solve a
   CAPTCHA before each API session token is issued.

**Recovery**: Revoke token batch; notify account owners (usually bot operators via registered
email); submit DMCA-equivalent abuse notice if commercially significant data exfiltration occurred.

**Prevention**: Scraper detection integrated into token-issuance flow; honeypot ID coverage
expanded quarterly; user data minimization in public-facing API responses.
