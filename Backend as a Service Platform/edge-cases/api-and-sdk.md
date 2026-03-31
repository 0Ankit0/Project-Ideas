# Edge Cases – API and SDK

## Scenarios

| # | Scenario | Severity | Risk | Mitigation |
|---|----------|----------|------|-----------|
| 1 | SDK version expects newer facade semantics than deployed platform | High | Client breakage after outdated SDK update | Version APIs with URL prefix (`/api/v1/`); publish SDK compatibility matrix; sunset headers 6 months before removal |
| 2 | Idempotency key reused for a different operation type | High | Wrong cached response returned | Idempotency keys are scoped to `(tenantId, operationType, key)`; cross-type reuse returns `IDEMPOTENCY_KEY_CONFLICT` |
| 3 | Client sends request without `Idempotency-Key` for a non-idempotent mutation | Medium | Duplicate side effects on retry | Log warning; recommend key; certain high-risk operations (switchover, migration) require idempotency key (enforced, not advisory) |
| 4 | API gateway rate limit applied incorrectly to shared IP (NAT gateway) | Medium | Legitimate traffic blocked | Rate limit by `tenantId` claim in JWT, not by source IP |
| 5 | Client retries a 503 without backoff, amplifying outage | High | Thundering herd worsens incident | All `503` and `429` responses include `Retry-After` header; SDK enforces exponential backoff with jitter |
| 6 | Cursor-based pagination cursor becomes stale after data deletion | Medium | Skipped or repeated rows | Cursor encodes a stable sort key (e.g. `(createdAt, id)`); deleted rows cause `next_page` to skip naturally; document behavior |
| 7 | Large response body causes client timeout | Medium | Partial response received; client retries | Streaming responses for large collections; enforce `limit` ≤ 100; warn if response > 1 MB |
| 8 | Breaking API change deployed without version increment | Critical | All existing clients break | API contract tests (Pact) block deployment if consumer contract is violated; breaking changes require new version |

## Deep Edge Cases

### Idempotency Key Conflict
```json
// First call:
POST /api/v1/environments  Idempotency-Key: key-abc
// Returns: { "id": "env_123", ... }

// Second call with same key but different body:
POST /api/v1/projects      Idempotency-Key: key-abc
// Returns HTTP 409:
{ "error": { "code": "IDEMPOTENCY_KEY_CONFLICT", "message": "Key already used for a different operation" } }
```

### SDK Retry with Backoff (TypeScript SDK)
```typescript
async function withRetry<T>(fn: () => Promise<T>, maxAttempts = 4): Promise<T> {
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (err) {
      if (!isRetryable(err) || attempt === maxAttempts) throw err;
      const retryAfter = err.headers?.['retry-after'] ?? Math.pow(2, attempt);
      const jitter = Math.random() * 1000;
      await sleep(retryAfter * 1000 + jitter);
    }
  }
  throw new Error('unreachable');
}
```

### API Sunset Process
1. New major version released with `Deprecation` and `Sunset` response headers added to old version.
2. Developer dashboard shows usage of deprecated endpoints per project.
3. 6 months before sunset: email notification to all projects using deprecated endpoints.
4. 1 month before sunset: 429 throttle at 10% of requests on deprecated version.
5. At sunset: old version returns `HTTP 410 Gone` with migration guide link.

## State Impact Summary

| Scenario | API / Request State |
|----------|-------------------|
| Idempotent duplicate | Returns cached response; no side effects |
| Key conflict | HTTP 409; no state change |
| Rate limited | HTTP 429 with `Retry-After`; no state change |
| Breaking change (Pact failure) | Deployment blocked; no production change |
| Sunset endpoint called | HTTP 410; no state change |
