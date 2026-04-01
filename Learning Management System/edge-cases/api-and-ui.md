# Edge Cases — API and UI

> **Scope:** Covers search index lag, dual-tab assessment conflicts, large cohort timeouts, tenant data leaks, signed URL expiry, seat race conditions, rate limit breaches, stale client caches, malicious file uploads, and invalid pagination cursors.

---

## 1. Catalog Search Index Lag After Course Publication

**Failure Mode:** An author publishes a course at 10:00 AM. The search indexer (Elasticsearch/OpenSearch) processes the publish event asynchronously. Due to index queue backlog, the new course does not appear in search results until 10:18 AM. Learners searching for the course in that window get zero results.

**Impact:** New course is invisible to learners for up to 20 minutes post-publication; learners may enroll via a direct link but cannot discover it organically. For time-sensitive launches (product training, compliance deadlines), this delay is operationally significant.

**Detection:**
- Monitor `search_index_lag_seconds` metric; alert if > 60 seconds.
- Synthetic monitor: publish a canary course every 5 minutes; search for it and alert if it does not appear in results within 90 seconds.
- Track `course_not_found_in_search` user feedback events correlated with recent publish timestamps.

**Mitigation/Recovery:**
- For critical publish events, trigger a synchronous index write (bypassing the queue) for the specific course record; eventual consistency handles bulk updates.
- Provide a shareable direct-enrollment URL at publish time that bypasses search; include it in the publish confirmation.
- Search results UI: show "New course? It may take up to 5 minutes to appear in search" note after a course publish event.

---

## 2. Learner Opens Assessment in Two Browser Tabs Simultaneously

**Failure Mode:** Learner opens an assessment in Tab A, then accidentally opens it in Tab B. Both tabs issue `POST /attempts` and both receive an attempt record. Tab A submits; Tab B later submits a partial attempt, overwriting or conflicting with Tab A's completed submission.

**Impact:** Learner's completed submission may be replaced by a partial one from Tab B; grade is lost or incorrect; attempt count is consumed twice.

**Detection:**
- Alert on `attempt_created` events where the same `(learner_id, assessment_id)` produces two active attempts within a 10-second window.
- Monitor `duplicate_active_attempt` metric per assessment.

**Mitigation/Recovery:**
- Enforce at most one active attempt per `(learner_id, assessment_id)` at the database level via a partial unique index: `UNIQUE (learner_id, assessment_id) WHERE state = 'IN_PROGRESS'`.
- When a second `POST /attempts` is received for the same learner+assessment while one is `IN_PROGRESS`, return `409 Conflict` with the existing attempt ID; the client redirects to the in-progress attempt.
- UI detects the 409 and shows a banner: "You already have this assessment open in another tab. Please continue there."

---

## 3. Large Cohort Dashboard Causes API Timeout

**Failure Mode:** A staff member opens the cohort dashboard for a 10,000-learner enrollment. The API endpoint `/cohorts/{id}/dashboard` performs an unindexed JOIN across `enrollments`, `progress_records`, and `grades` tables, returning a single payload. Query takes 45 seconds; the API gateway times out at 30 seconds; the staff member sees a 504 error.

**Impact:** Administrators cannot view cohort progress reports; management dashboards are unavailable; manual workarounds require CSV exports.

**Detection:**
- Alert on API response time p99 > 5 s for `/cohorts/{id}/dashboard`.
- Slow query log: alert on any query exceeding 10 s on cohort-related tables.
- Monitor `504_gateway_timeout` rate on dashboard endpoints; alert if > 0.5%.

**Mitigation/Recovery:**
- Pre-aggregate cohort statistics (completion rate, avg score, active learners) into a `cohort_stats` materialized view refreshed every 5 minutes.
- Dashboard API returns aggregate stats instantly from the materialized view; detailed learner list is paginated (100 per page) with cursor-based pagination.
- Add composite indexes: `(cohort_id, state)` on `enrollments`, `(learner_id, lesson_id)` on `progress_records`.

---

## 4. Staff Workspace Leaks Learner Data Across Tenants

**Failure Mode:** A staff user at Tenant A queries `/learners?search=john` without a tenant scoping filter in the API query. Due to a missing `WHERE tenant_id = ?` clause in a new endpoint, results include learners from Tenant B and Tenant C. The staff user can see names, emails, and progress of learners outside their organization.

**Impact:** Cross-tenant PII exposure; GDPR/data breach notification obligations may be triggered. Regulatory fines up to 4% of annual global turnover. Complete loss of learner trust.

**Detection:**
- Automated API test: assert that all `/learners` and related endpoints return only records matching the authenticated user's `tenant_id`.
- Integration test: create learners in two separate tenants; authenticate as Tenant A admin; assert Tenant B learners are not returned.
- Alert on any query to `learners` table that does not include `tenant_id` in the WHERE clause (via query analysis or ORM audit).

**Mitigation/Recovery:**
- All data access must flow through a tenant-scoped repository layer that injects `AND tenant_id = :current_tenant_id` into every query — never rely on the caller to add this filter.
- Penetration test tenant isolation quarterly; include cross-tenant enumeration tests in CI/CD pipeline.
- If a leak is detected: immediately revoke the staff user's session, audit what data was accessed, notify affected tenants within 72 hours per GDPR Art. 33.

---

## 5. Lesson Video Player Fails Due to Signed URL Expiry

**Failure Mode:** Learner opens a lesson page; the server generates a signed S3/CloudFront URL valid for 15 minutes. The learner reads the lesson text and pauses for 20 minutes before clicking play. The URL has expired; the video player returns `403 Forbidden` and renders a broken player.

**Impact:** Learner cannot play the video; if the lesson requires video completion, the learner is blocked. Common for lessons with long text introductions before video content.

**Detection:**
- Monitor `video_player_403_error` events; alert if rate exceeds 5% of video play attempts.
- Track time-delta between `page_load` and `video_play_initiated` events; alert if p90 > URL TTL.

**Mitigation/Recovery:**
- Generate signed URLs server-side on-demand when the play button is clicked (`POST /lessons/{id}/media-url`), not at page load time.
- Set URL TTL to 2 hours minimum; invalidate URLs on lesson completion or session end.
- Video player component catches 403 responses and automatically fetches a fresh signed URL before retrying playback.

---

## 6. Concurrent Enrollment in Last Available Seat (Race Condition)

**Failure Mode:** A course has a seat limit of 1 seat remaining. Two learners click "Enroll" simultaneously. Both requests pass the availability check (`available_seats = 1 > 0`) before either enrollment is committed. Both enrollments succeed; the course now has -1 available seats.

**Impact:** Course is over-enrolled; instructor may face issues with a cohort larger than the intended size; if physical resources (e.g., lab access) are tied to seat count, this creates a logistics problem.

**Detection:**
- Alert on `available_seats < 0` for any course.
- Monitor `enrollment_over_limit` events; these should never occur.

**Mitigation/Recovery:**
- Implement optimistic locking on `courses.available_seats`: `UPDATE courses SET available_seats = available_seats - 1 WHERE id = ? AND available_seats > 0`; check affected row count; if 0 rows updated, return `409 No Seats Available`.
- Alternative: use a Redis atomic decrement (`DECR seats:{course_id}`) as a distributed seat counter; enrollment proceeds only if the decrement result is >= 0.
- If over-enrollment is detected post-fact, notify the later-enrolling learner and offer waitlist placement or a refund.

---

## 7. API Rate Limit Hit During Bulk Enrollment Import

**Failure Mode:** An admin imports a CSV of 5,000 learners. The import service calls `POST /enrollments` in a tight loop without rate limiting, saturating the API at 500 req/s. The API gateway rate limit (200 req/s per tenant) kicks in and returns `429` for 60% of requests. The import job fails; only 2,000 of 5,000 learners are enrolled.

**Impact:** Partial enrollment; 3,000 learners are not enrolled; admin must re-run the import; course launch is delayed. No learners are notified of the failed enrollment.

**Detection:**
- Alert on bulk import job completing with `failed_count / total_count > 0.05` (>5% failure rate).
- Monitor `429_rate` on enrollment endpoint; alert if > 2% during import windows.

**Mitigation/Recovery:**
- Bulk import uses an async background job that processes enrollments at a controlled rate (e.g., 50 req/s) with exponential backoff on 429 responses.
- Provide a dedicated bulk enrollment endpoint (`POST /enrollments/bulk`) that accepts up to 1,000 records per request and processes them within a single transaction, bypassing per-request rate limits.
- Import job reports status in real-time: `{total: 5000, enrolled: 4998, failed: 2}`; failed records are downloadable for re-import.

---

## 8. Client Caches Stale Course Version

**Failure Mode:** A learner's browser aggressively caches the course outline response (`Cache-Control: max-age=3600`). The author publishes a corrected course version with updated lesson ordering. The learner's client serves the stale v1 outline for up to 1 hour; the learner navigates to a lesson that no longer exists in v2 and receives a 404.

**Impact:** Learner encounters confusing 404 errors; in-progress navigation is broken; incorrect lesson ordering may affect learning experience.

**Detection:**
- Monitor 404 rate on `/lessons/{id}` for recently deleted or moved lessons; spike after a publish event indicates stale cache issue.
- Track `course_version_mismatch` events: client sends the version it has cached; server compares against current version.

**Mitigation/Recovery:**
- Course outline responses include an `ETag` and `Last-Modified` header; client validates on each navigation.
- On course publish, increment `course.version` and include in the course outline URL or as a cache-busting query parameter.
- Client-side service worker: on detecting a `course_version` change, invalidates the course outline cache and refetches before rendering.
- API returns `410 Gone` (not `404`) for lessons from superseded course versions, with a redirect to the current version's equivalent lesson where mappable.

---

## 9. File Upload Endpoint Accepts Malicious File via MIME Type Bypass

**Failure Mode:** The assignment submission endpoint accepts files with `Content-Type: application/pdf`. An attacker uploads a polyglot file that passes the MIME-type check but is actually a valid HTML file that executes JavaScript when opened in certain PDF viewers. The file is stored and served to other learners (e.g., peer review).

**Impact:** Cross-site scripting (XSS) or script execution in PDF viewers; credentials or session tokens may be stolen from learners who open the file.

**Detection:**
- Alert on any upload where server-side MIME detection (`file --mime-type`) disagrees with the `Content-Type` header.
- Monitor for file uploads that fail server-side content scanning (antivirus/malware scan).
- Security scan alerts from ClamAV or equivalent integrated at upload time.

**Mitigation/Recovery:**
- Never trust the client-supplied `Content-Type`; perform server-side MIME detection using magic bytes (e.g., libmagic) after upload.
- Reject files where `server_detected_mime != allowed_mime` for the endpoint.
- Store uploaded files in an isolated S3 bucket with no public website hosting enabled; serve via pre-signed URLs with `Content-Disposition: attachment` to prevent in-browser execution.
- Run all uploads through an antivirus scanner (ClamAV / cloud scanning API) before making files downloadable by other users.

---

## 10. Pagination Cursor Becomes Invalid After Records Are Deleted Mid-Page

**Failure Mode:** An admin is paginating through a learner list. After page 3 is returned, the admin deletes 50 learner records. The cursor for page 4 was calculated based on the deleted records' IDs. The next request using the cursor returns 0 results or skips learners, causing the admin to miss records mid-pagination.

**Impact:** Admin sees incomplete data; learner records may be skipped during export or bulk operations; compliance audits miss entries.

**Detection:**
- Alert when a cursor-based pagination request returns a significantly smaller page than requested without reaching the end of the dataset.
- Monitor `pagination_cursor_invalid` events; these should be rare under normal conditions.

**Mitigation/Recovery:**
- Use keyset pagination with `(created_at, id)` as the cursor; this is stable against deletions (deleted records are simply skipped, not causing cursor invalidation).
- Avoid offset-based pagination for any admin list views where records may be deleted mid-session.
- If cursor is invalidated (e.g., referenced record deleted), return the next available record after the cursor position and include a `X-Cursor-Adjusted: true` response header so callers can detect the gap.
- For compliance exports, use a snapshot-based export that captures the full dataset at a point in time, independent of real-time pagination.
| Learner opens assessment in multiple windows | Attempt collisions occur | Lock active attempts or define deterministic continuation behavior |
| Large cohort dashboard becomes slow | Staff lose operational visibility | Use projection-based summaries and paginated drill-downs |
| Staff workspace leaks learner data across tenants | Severe isolation breach | Enforce tenant scoping before query and render on every route |
| Lesson player fails to render embedded content | Progress flow breaks | Provide graceful fallback with retry and support messaging |


## Implementation Details: API/UI Contract Alignment

- Each API error code maps to deterministic UI copy and retry guidance.
- UI should not assume completion/grade finalization until evaluator confirmation event.
- Long-running operations expose polling status and correlation reference.
