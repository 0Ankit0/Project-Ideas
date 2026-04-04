# Edge Cases — API and UI

## EC-API-001: Rate Limit Exceeded

**Scenario:** Client exceeds API Gateway rate limit (2000 req/5 min or burst limit).

**Expected Behaviour:**
- API Gateway returns `429 Too Many Requests` with `Retry-After` header
- Rate limit applies per API key for authenticated requests, per IP for unauthenticated
- Client SDK implements exponential backoff with jitter on 429 responses
- Dashboard users see a "Too many requests, please wait" modal
- Rate limit counters stored in ElastiCache with sliding window

---

## EC-API-002: Pagination Cursor Expiry

**Scenario:** Client holds a pagination cursor for hours before requesting the next page.

**Expected Behaviour:**
- Cursor-based pagination uses opaque base64-encoded cursor
- Cursors reference database primary keys; no TTL on cursor validity
- If underlying data changes between pages (new orders, deleted products):
  - Consistent ordering is maintained (ORDER BY created_at DESC, id)
  - Client may see slightly different total count but no duplicate/missing items within a single paginated range

---

## EC-API-003: Request Timeout — Long-Running Checkout

**Scenario:** API Gateway times out (29 s) before Lambda completes checkout processing.

**Expected Behaviour:**
- API Gateway returns `504 Gateway Timeout` to client
- Lambda may still be running; completes processing in background
- Client retries with same `Idempotency-Key`
- If Lambda completed → idempotency returns cached result
- If Lambda also timed out → reservation released by TTL; client retries fresh checkout

---

## EC-API-004: Concurrent Mutations on Same Resource

**Scenario:** Two admin users update the same product simultaneously.

**Expected Behaviour:**
- Product updates use optimistic locking via `version` column
- First update succeeds; second receives `409 Conflict`
- Client prompted to refresh and reapply changes
- Audit trail captures both attempted changes

---

## EC-API-005: Invalid JSON or Malformed Request

**Scenario:** Client sends invalid JSON body or missing required fields.

**Expected Behaviour:**
- API Gateway returns `400 Bad Request` before reaching Lambda
- Error response includes specific field validation errors
- Example: `{ "error": "VALIDATION_ERROR", "details": [{ "field": "payment_method.type", "message": "required" }] }`
- Malformed requests never reach business logic layer

---

## EC-API-006: Large File Upload (POD Photo)

**Scenario:** Delivery staff uploads a 15 MB photo (exceeding 5 MB limit).

**Expected Behaviour:**
- API Gateway payload limit: 10 MB
- POD photo upload uses S3 presigned URL for direct upload (bypasses API Gateway)
- S3 upload enforces Content-Length check: max 5 MB per photo
- If exceeded → S3 rejects upload; client shown "Photo too large — please reduce size"
- System compresses photos client-side before upload (target < 2 MB)
