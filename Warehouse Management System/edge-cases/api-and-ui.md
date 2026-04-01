# API and UI Edge Cases

## Failure Mode

Four distinct failure scenarios exist at the API and UI boundary:

**(a) Network timeout causing duplicate submit**: a scanner or browser client sends a request, the network times out before the response is received, and the client retries — sending a second identical request after the first has already been committed server-side.

**(b) Optimistic concurrency violation**: a worker loads a task, another worker or background process modifies the same task, and the first worker submits an update with a stale `version` field, creating a conflict.

**(c) Partial composite operation failure**: a multi-step operation (e.g., pack close + label generation) succeeds on the first step but fails on the second, leaving the resource in a blocked intermediate state (`PackingBlocked`).

**(d) UI showing stale state**: the UI displays a task or inventory record that has been modified server-side since the last poll/render, causing the worker to act on outdated information.

---

## Impact

- **Duplicate submit**: double processing of a pick or pack event; inventory double-decremented; potential duplicate shipment.
- **Version conflict**: worker submits a valid update that is silently lost or rejected without clear guidance on how to proceed.
- **Partial composite failure**: pack is in `PackingBlocked` status; no label generated; shipment cannot proceed without manual intervention.
- **Stale UI state**: worker performs an action on a task already completed by another worker, causing an error and confusion.
- **Support call volume increase**: all four scenarios generate user-facing errors that require support team intervention if not self-recoverable.
- **SLA impact**: pack blocked or duplicate processing can delay shipment confirmation past carrier cut-off.

---

## Detection

- **Metric**: idempotency key duplicate hit rate > 1% of requests → alert `IdempotencyKeyHitRateHigh` (Sev-3).
- **Metric**: HTTP `409 Conflict` response rate per endpoint > 2% → alert `OptimisticLockConflictRateHigh`.
- **Metric**: `PackingBlocked` status duration > 10 minutes for any pack → alert `PackBlockedTooLong` (Sev-2).
- **Metric**: UI stale-state duration (time since last successful poll) > 30 s → client-side warning displayed to user.
- **Log pattern**: `IDEMPOTENCY_KEY_COLLISION` and `VERSION_CONFLICT` in API gateway logs.

---

## Mitigation

**Scenario (a) — Duplicate submit:**
1. **System**: idempotency middleware intercepts the duplicate request, looks up the stored response by idempotency key, and returns it with a `X-Idempotency-Hit: true` header.
2. **Worker**: UI displays "already processed" banner with original timestamp and outcome.
3. No manual intervention required if idempotency middleware is functioning correctly.

**Scenario (b) — Version conflict:**
1. **System**: returns `409 Conflict` with the current resource version in the response body.
2. **UI**: displays "Task updated by another user — please review and resubmit" with a diff of the changes.
3. **Worker**: reviews the current state, re-applies their change if still valid, and resubmits with the latest version.

**Scenario (c) — Partial composite failure:**
1. **On-call Engineer**: identify the `PackingBlocked` pack via the remediation queue dashboard.
2. **On-call Engineer**: invoke the saga compensation endpoint: `POST /packs/{packId}/compensate { "action": "retry_label" }`.
3. **System**: retries the label generation step; if it succeeds, pack status advances to `LABEL_GENERATED`.
4. **If label generation continues to fail**: escalate to carrier integration team; manually generate label via carrier portal as a bypass.

**Scenario (d) — Stale UI:**
1. **System**: UI detects poll gap > 30 s and displays a "refresh required" banner.
2. **Worker**: clicks refresh; UI fetches current authoritative state from the server.
3. **On-call Engineer**: if stale state is systemic (all users affected), investigate server-sent event (SSE) or WebSocket connection health.

---

## Recovery

**Scenario (a):**
1. Verify no duplicate ledger rows exist for the affected operation: query by idempotency key and confirm single row.
2. If a duplicate row exists (idempotency middleware failure), run the de-duplication compensating job: `POST /jobs/dedup-ledger { "idempotency_key": "..." }`.

**Scenario (b):**
1. No recovery needed beyond the worker resubmitting with the correct version — the `409` is a safe rejection.
2. If conflict rate is elevated, investigate whether a background process is updating tasks without holding the correct lock.

**Scenario (c):**
1. After saga compensation succeeds, confirm pack status = `LABEL_GENERATED` and shipment record is created.
2. **Checkpoint**: confirm no orphaned `PackingBlocked` records older than 15 minutes remain in the queue.

**Scenario (d):**
1. Confirm SSE/WebSocket push pipeline is healthy; check for connection drops or message backlog.
2. If SSE pipeline is down, fall back to polling at 10-second intervals until the push pipeline recovers.

---

## API Failure Modes Reference Table

| Case | Trigger | HTTP Response | UI Behavior | Recovery Path |
|---|---|---|---|---|
| Duplicate submit | Scanner retries after timeout | `200` (or original status) + `X-Idempotency-Hit: true` | Show "already processed" with original timestamp | None — idempotency middleware handles automatically |
| Version conflict | Stale `version` in request | `409` with current version in body | "Task updated — review and resubmit" prompt | Worker refreshes and resubmits |
| Pack close succeeds; label fails | Label service unavailable | `202` with `PackingBlocked` status | Route operator to remediation queue | Saga compensation: retry label generation |
| Resource not found | Task deleted or ID wrong | `404` with `NOT_FOUND` code | "Task no longer exists" message; redirect to queue | Worker picks next task from queue |
| Rate limit exceeded | Burst traffic from scanner batch | `429` with `Retry-After` header | Exponential backoff with jitter | Client respects `Retry-After` |

---

## Idempotency Implementation Guide

Every mutating API endpoint must:
1. Accept an `Idempotency-Key` header (UUID v4, max 64 chars).
2. Store `(idempotency_key, response_body, status_code, created_at)` in a dedicated `idempotency_keys` table with a 72-hour TTL.
3. On duplicate key: return the stored response with `X-Idempotency-Hit: true`; do not re-execute the operation.
4. If the first request is still in-flight: return `409` with `IDEMPOTENCY_KEY_IN_FLIGHT` to prevent concurrent duplicate processing.

Scanner clients must generate idempotency keys using: `SHA256(device_id + ":" + session_id + ":" + action_type + ":" + local_timestamp_ms)`.

---

## UI Consistency Patterns

| Pattern | Use Case | Latency | Complexity |
|---|---|---|---|
| **Short polling** (10 s interval) | Fallback when push unavailable; low-priority dashboards | High (wasted requests) | Low |
| **Long polling** | Task assignment updates; medium-priority state | Medium | Medium |
| **Server-Sent Events (SSE)** | Real-time pick task state; one-directional push | Low | Medium |
| **WebSockets** | Bidirectional: scanner input + real-time feedback | Very low | High |

Recommended: use SSE for all task state updates in the WMS UI. Fall back to 10-second polling if SSE connection drops for > 60 s.

---

## Error Response Contract

Every error response must conform to this JSON schema:

```json
{
  "error": {
    "code": "string (e.g. RESERVATION_MISMATCH, VERSION_CONFLICT)",
    "message": "string (human-readable, English)",
    "retryable": "boolean",
    "rule_id": "string (e.g. BR-07) — optional",
    "correlation_id": "string (UUID — required for support handoff)",
    "timestamp": "string (ISO 8601)",
    "details": "object (optional — additional context specific to the error type)"
  }
}
```

---

## Rate Limiting and Retry-After

- Scanner clients must respect the `Retry-After` header (value in seconds) on `429` responses.
- Clients must implement exponential backoff with jitter: `wait = min(cap, base * 2^attempt) + random_jitter`.
- Default cap: 30 seconds. Base: 1 second. Jitter: 0–1 s uniform random.
- After 5 consecutive `429` responses, the client should surface an error to the operator and halt retries.

---

## Related Business Rules

- **BR-05 (Idempotency)**: all mutating operations must be safe to retry via idempotency key.
- **BR-07 (Version Conflict Policy)**: `409` on version mismatch is the correct and expected behavior; never silently overwrite.

---

## Test Scenarios to Add

| # | Scenario | Expected Outcome |
|---|---|---|
| T-AU-01 | Same request sent twice with identical idempotency key | Second returns `X-Idempotency-Hit: true`; no duplicate ledger row |
| T-AU-02 | Task updated by worker B while worker A has stale version | Worker A receives `409` with current version; no silent overwrite |
| T-AU-03 | Pack close succeeds; label generation returns 503 | Pack status = `PackingBlocked`; remediation queue entry created |
| T-AU-04 | SSE connection drops for 90 s | UI falls back to polling; "refresh required" banner shown |
| T-AU-05 | Scanner sends 10 identical requests in 2 s (burst) | `429` after rate limit; `Retry-After` header present; no duplicate processing |
| T-AU-06 | Idempotency key sent while first request still in-flight | `409 IDEMPOTENCY_KEY_IN_FLIGHT` returned; no duplicate execution |
