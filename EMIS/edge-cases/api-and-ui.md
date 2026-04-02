# Edge Cases — API and UI

Domain-specific failure modes, impact assessments, and mitigation strategies for REST API behaviour, client-side interactions, and cross-cutting concerns.

Edge case IDs in this file are permanent: **EC-API-001 through EC-API-007**.

---

## EC-API-001 — Client Sends Malformed JSON Body

| Field | Detail |
|---|---|
| **Failure Mode** | A third-party integration or a bug in the mobile app sends a request body with invalid JSON (e.g., missing closing brace, trailing comma, or binary data instead of JSON). |
| **Impact** | Unhandled `JSONDecodeError` propagates to the user as a 500 Internal Server Error rather than a descriptive 400 Bad Request. Error details may leak internal stack traces. |
| **Detection** | DRF's `JSONParser` raises `ParseError` on malformed JSON, which is caught by the DRF exception handler and returns 400. Custom exception handler logs the error with request metadata. |
| **Mitigation / Recovery** | (1) DRF exception handler returns `{"error": {"code": "PARSE_ERROR", "message": "Request body contains invalid JSON."}}` with HTTP 400. (2) No stack trace or internal detail is included in the response. (3) Error is logged to CloudWatch for investigation if repeated from the same client. |
| **Prevention** | `DEFAULT_RENDERER_CLASSES` includes only `JSONRenderer` for the API — no form renderers that could accept non-JSON. Content-Type header is validated (`application/json` required). Integration tests include malformed JSON test cases. |

---

## EC-API-002 — Concurrent PATCH Requests Creating State Conflict

| Field | Detail |
|---|---|
| **Failure Mode** | A student opens two browser tabs and simultaneously submits a profile update from both. The second request's payload is stale (it was loaded before the first update) and its save overwrites the first update's values. |
| **Impact** | Data silently overwritten. The student believes they saved change A but actually saved change B (the last-write-wins stale write). |
| **Detection** | PATCH endpoint requires `If-Match: "ETag"` header containing the resource's current `ETag` (hash of `updated_at` timestamp). If the ETag does not match, 412 Precondition Failed is returned. |
| **Mitigation / Recovery** | (1) Client receives 412 `PRECONDITION_FAILED`. (2) Client fetches the latest version (with new ETag), re-applies the user's intended changes on top of the fresh state, and re-submits. (3) User is shown a "Changes were updated — please review" message in the UI. |
| **Prevention** | ETag-based optimistic concurrency control on all PATCH endpoints for mutable user-facing resources. API documentation specifies the `If-Match` requirement. |

---

## EC-API-003 — Pagination Cursor Invalidated by Data Change

| Field | Detail |
|---|---|
| **Failure Mode** | Admin is paginating through a list of 2,000 student records using `?page=5&page_size=20`. While paginating, a new student is enrolled, shifting all records from page 3 onward. The admin sees a duplicate record on page 5 (a record that was on page 4 before the insert). |
| **Impact** | Duplicate or skipped records in paginated responses. Admin may miss processing a record or process one twice. |
| **Detection** | Offset-based pagination is inherently unstable in the presence of concurrent writes. The issue manifests as data inconsistency across pages. |
| **Mitigation / Recovery** | (1) Switch list endpoints to cursor-based pagination: `?after=<opaque_cursor>` where the cursor encodes `(updated_at, id)`. Cursor-based pagination is stable even when records are inserted or deleted. (2) For already-deployed offset pagination: document the limitation and suggest completing pagination in a single session. |
| **Prevention** | Cursor-based pagination is the default for all list endpoints returning more than 100 records. Offset pagination is only used for short, stable lists (e.g., dropdown options). |

---

## EC-API-004 — File Upload Exceeding Size Limit Not Rejected at Edge

| Field | Detail |
|---|---|
| **Failure Mode** | A student attempts to upload a 500 MB video file as an assignment submission. The Django API receives the entire file into memory before the file-size validation runs, consuming large amounts of ECS task memory and potentially causing an OOM crash. |
| **Impact** | ECS task OOM-killed. Request fails with 502. Other requests served by the same task are aborted. Temporary reduction in API capacity. |
| **Detection** | Django `DATA_UPLOAD_MAX_MEMORY_SIZE` setting limits request body size at the framework level. Nginx upstream also enforces `client_max_body_size`. CloudWatch metric: ECS task memory utilization spike. |
| **Mitigation / Recovery** | (1) Django returns 413 `REQUEST_ENTITY_TOO_LARGE` before reading the full body once the size limit is reached. (2) Nginx rejects requests exceeding `client_max_body_size = 100M` at the proxy layer before they reach the application. |
| **Prevention** | Nginx `client_max_body_size` is set to 100 MB. Django `DATA_UPLOAD_MAX_MEMORY_SIZE` is set to 50 MB. Large file uploads (videos, SCORM packages) use presigned S3 multipart upload URLs generated by the API — the client uploads directly to S3, not through Django. |

---

## EC-API-005 — API Rate Limiting Blocking Legitimate Bulk Admin Operations

| Field | Detail |
|---|---|
| **Failure Mode** | An admin script runs a batch of 500 API calls (e.g., importing student records one at a time) and hits the per-IP rate limit of 1,000 requests/5 minutes configured in WAF. The admin's IP is blocked for 5 minutes mid-import. |
| **Impact** | Import is interrupted. Data is in a partially imported state. Admin must manually clean up or re-run. |
| **Detection** | WAF returns 429 `TOO_MANY_REQUESTS`. Admin script logs 429 errors. |
| **Mitigation / Recovery** | (1) Rate limits are differentiated by endpoint: `/api/` general limit vs. `/api/v1/students/bulk-import/` endpoint-specific limit (higher threshold). (2) Bulk operations are exposed as dedicated batch endpoints (e.g., `POST /api/students/bulk-import/` accepting an array of records or a CSV) to avoid multiple individual calls. (3) Admin scripts that require higher rate limits can use a dedicated API key with an elevated rate limit tier. |
| **Prevention** | All multi-record operations are exposed as batch endpoints. Admin integration scripts use the dedicated API key. Rate limit thresholds are documented in the API reference. |

---

## EC-API-006 — Downstream Service Timeout Causing Cascading Failures

| Field | Detail |
|---|---|
| **Failure Mode** | The Turnitin plagiarism API becomes slow (response time > 30s). Celery workers handling assignment submission tasks are blocked waiting for Turnitin responses. All available Celery workers are occupied, causing a queue backup that delays all other notifications, receipt generation, and report jobs. |
| **Impact** | Entire Celery worker pool is saturated by one slow downstream dependency. Student notifications, payment receipts, and GPA calculations are all delayed. |
| **Detection** | CloudWatch metric: Celery queue depth spike across all queues (`default`, `email`, `reports`). Celery task `plagiarism_check` timeout alarm. |
| **Mitigation / Recovery** | (1) Circuit breaker on Turnitin client: opens after 3 consecutive timeouts (60 s threshold), stays open for 5 minutes. During open state, submissions are queued without immediate plagiarism check. (2) Plagiarism checks for queued submissions are retried once the circuit closes. (3) Faculty is notified that similarity reports may be delayed. |
| **Prevention** | Plagiarism check tasks are assigned to a dedicated Celery queue (`plagiarism`) with its own worker pool — separate from `default` queue. A slow Turnitin call cannot consume the `default` queue workers. Each external API call has a hard timeout configured in the gateway client (30 s). |

---

## EC-API-007 — HTMX Partial Render Race Condition in Student Portal

| Field | Detail |
|---|---|
| **Failure Mode** | A student rapidly clicks "Mark as Read" on multiple in-app notifications in quick succession. HTMX sends multiple simultaneous PATCH requests. Two responses arrive out of order, and the stale response re-renders the notification list without the last update, un-reading a notification the student just read. |
| **Impact** | UI inconsistency. Notification appears unread again after being marked read. Student is confused or contacts support. |
| **Detection** | HTMX request overlap detected on the client side via network tab; user experience degradation reported. |
| **Mitigation / Recovery** | (1) HTMX `hx-sync` attribute is set on the notification list container: `hx-sync="this:queue last"` — queues concurrent requests and processes only the last one, discarding intermediate responses. (2) Server returns the current true state (all marked-read items) in the response, not a delta — making responses idempotent and safe to re-render. |
| **Prevention** | HTMX interactions on stateful lists use `hx-sync` to prevent concurrent request races. All PATCH endpoints return the full updated resource (not a partial delta), so out-of-order responses render the correct final state regardless. UI integration tests cover rapid multi-click scenarios. |

---

## Operational Policy Addendum

### Academic Integrity Policies
All API endpoints that modify grade or attendance records log every invocation (including successful ones) to the AuditLog. This enables forensic reconstruction of any changes made via bulk operations or administrative scripts. API access logs are retained for 1 year.

### Student Data Privacy Policies
API responses never include sensitive fields (date of birth, national ID, full bank details) in list endpoints. These fields are available only in individual resource detail endpoints accessible to authorised roles. All API request and response bodies for endpoints involving PII are excluded from application-level debug logging. Only sanitised metadata (endpoint, status code, latency, user role) is logged.

### Fee Collection Policies
Financial transaction endpoints (payment initiation, refund, invoice generation) enforce idempotency via the `Idempotency-Key` header. Clients must include a unique key per transaction attempt. Duplicate requests with the same key within 24 hours return the original response without reprocessing.

### System Availability During Academic Calendar
API rate limits are reviewed and updated before each registration window and exam period. Rate limit thresholds for student-facing enrollment and grade-checking endpoints are temporarily increased (via WAF rule override) during Mission-Critical calendar windows. All overrides are time-bound and automatically revert after the window closes.
