# Edge Cases — Security and Compliance

> **Scope:** Covers cross-tenant access, unaudited grade overrides, PII leakage in public endpoints, URL sharing, over-scoped data exports, JWT replay, audit log tampering, IDOR, DRM bypass, and GDPR erasure with active certificates.

---

## 1. Instructor Accesses Cohort Outside Authorized Tenant Scope

**Failure Mode:** An instructor's JWT contains `tenant_id = "acme"`. A misconfigured API endpoint for cohort details does not enforce a `WHERE tenant_id = ?` filter, allowing the instructor to fetch cohort data for `tenant_id = "globex"` by manipulating the `cohort_id` path parameter.

**Impact:** Cross-tenant data exposure: roster names, email addresses, progress data, and grades from another organization are visible to an unauthorized instructor. GDPR data breach notification may be required within 72 hours.

**Detection:**
- Automated integration test in CI: authenticate as Tenant A instructor; assert Tenant B cohort endpoints return `403 Forbidden`.
- WAF rule: flag requests where the `cohort_id` in the URL resolves to a different `tenant_id` than the authenticated user's claim.
- Alert on `cross_tenant_access_denied` events; any occurrence warrants investigation.
- SIEM: alert if the same user account accesses resources belonging to more than one `tenant_id` within a 15-minute window.

**Mitigation/Recovery:**
- All data-access repository methods enforce tenant scope as a mandatory, injected predicate — not an optional caller filter.
- Conduct quarterly penetration tests specifically targeting horizontal privilege escalation (IDOR) across tenant boundaries.
- On confirmed exposure: revoke instructor session, audit the access log for full scope of records accessed, notify affected tenant's data protection officer within 72 hours.

---

## 2. Grade Override Without Reason Code or Approver Identity

**Failure Mode:** An instructor calls `PATCH /grades/{id}` to override a score. The API accepts the override without requiring `reason_code` or `approver_id` fields. The change is applied and appears in the learner's transcript with no audit trail.

**Impact:** Fraudulent grade manipulation is undetectable; compliance audits find unexplained score changes; institution loses accreditation standing if regulatory bodies find missing audit trails.

**Detection:**
- API validation: reject `PATCH /grades/{id}` with `422 Unprocessable Entity` if `reason_code` or `approver_id` is missing.
- Daily audit query: `SELECT * FROM grade_overrides WHERE reason_code IS NULL OR approver_id IS NULL`.
- Alert on any direct UPDATE to `grades` table not originating from the grade service (detected via DB audit log / pgaudit).

**Mitigation/Recovery:**
- Grade override endpoint requires `reason_code` (enumerated: `SYSTEM_ERROR`, `INSTRUCTOR_CORRECTION`, `APPEAL_OUTCOME`, `ADMINISTRATIVE`), `approver_id`, and optional `notes`.
- All overrides are written to an immutable `grade_audit_log` table (append-only; no UPDATE/DELETE privileges granted to the application role).
- Self-approval is blocked: `approver_id` must differ from the `instructor_id` initiating the override for grades above a configurable threshold.

---

## 3. Certificate Verification Endpoint Leaks Learner PII

**Failure Mode:** The public certificate verification endpoint `GET /certificates/verify/{code}` is intended to confirm validity. The current implementation returns the full certificate object including learner email, date of birth, and national ID number — fields added during a feature expansion but not scrubbed from the public response schema.

**Impact:** Anyone with a certificate code (printed on the certificate) can retrieve the learner's full PII. Certificate codes are shared publicly on LinkedIn, resumes, and professional profiles.

**Detection:**
- API response schema validation: automated test asserts that the verify endpoint response contains only `{certificate_id, course_name, issued_at, is_valid, learner_display_name}`  — no email, DOB, or government IDs.
- Periodic API fuzzing: scan public endpoints for PII-pattern responses (email regex, phone patterns, national ID formats).
- DAST scan in CI pipeline flags PII in API responses.

**Mitigation/Recovery:**
- Audit and whitelist the exact fields returned by every public (unauthenticated) endpoint; reject any field not on the whitelist at the serializer layer.
- Immediately deploy a response schema patch to strip PII fields from the verify endpoint.
- If PII was already exposed: assess exposure window, notify affected learners, report to supervisory authority if required under GDPR Art. 33.

---

## 4. Signed Download URL Shared Publicly

**Failure Mode:** A learner shares a pre-signed S3 URL for a copyrighted course video in a public forum. The URL has a TTL of 7 days. Other users download the video without being enrolled or paying for the course. The URL cannot be revoked once shared.

**Impact:** Revenue loss from unauthorized access; copyright/DRM compliance breach; if the video is from a licensed third-party provider, breach of content licensing agreement.

**Detection:**
- Monitor download requests per signed URL: alert if a single URL is accessed from more than 3 unique IP addresses or more than 5 times within its TTL.
- CDN access logs: flag signed URL access from IP addresses not associated with the issuing learner's session.

**Mitigation/Recovery:**
- Bind signed URLs to the learner's IP address or a session token embedded in the URL; requests from other IPs return `403 Forbidden`.
- Reduce URL TTL to 15–30 minutes for video content; generate new URLs on each video play request.
- Implement URL usage monitoring: if a URL is accessed from an unexpected IP, invalidate it and flag the learner account for review.
- For high-value content: use HLS with encrypted segments where the decryption key requires a valid session token, making the raw URL useless without the key.

---

## 5. Data Export Contains Over-Scoped Learner Records

**Failure Mode:** A department admin with scope limited to "Engineering Department" requests a progress export. The export service builds the query using `WHERE department = ?` but also joins across an unrestricted `learners` table, including learners from other departments who share a common `cohort_id`. The export file contains 4,500 records instead of the expected 320.

**Impact:** Admin receives PII for learners outside their authorized scope; GDPR data minimization principle violated; if the export is shared, it constitutes a data breach.

**Detection:**
- Post-export validation: compare `expected_record_count` (computed from the admin's scope at query time) against `actual_record_count` in the export file; alert if they differ.
- Data export audit log: record `admin_id`, `scope_definition`, `requested_at`, `record_count` for every export.
- Alert if `actual_record_count > scope_max_learner_count * 1.05`.

**Mitigation/Recovery:**
- Export queries are generated by the authorization service using the admin's scope claim — not by the export service directly.
- Scope is enforced as a mandatory JOIN or subquery: `WHERE learner_id IN (SELECT id FROM learners WHERE department = :admin_department AND tenant_id = :admin_tenant)`.
- Immediately revoke the over-scoped export file (delete from storage); notify affected data controller; assess breach notification obligation.

---

## 6. JWT Token Replay After Learner Logout

**Failure Mode:** A learner logs out at 2:00 PM. Their JWT was issued with a 4-hour expiry. An attacker who captured the JWT (e.g., from a shared computer, XSS, or log file) replays it at 3:30 PM. The JWT is cryptographically valid; the server accepts the request without checking whether the session was revoked.

**Impact:** Unauthorized access to the learner's account, grades, and personal data; attacker can enroll in courses, submit assessments, or extract certificates.

**Detection:**
- Alert on API requests using a JWT with `issued_at` timestamp before the learner's last `logout_at` timestamp.
- Monitor login events from geographically disparate IPs within a short window (impossible travel detection).
- Alert on access to sensitive operations (grade view, certificate download) from a session that should have been revoked.

**Mitigation/Recovery:**
- On logout: write the JWT's `jti` (JWT ID) to a Redis revocation set with TTL equal to the token's remaining validity; reject any request with a revoked `jti`.
- Use short-lived access tokens (15–30 minutes) paired with refresh tokens; logout invalidates the refresh token, preventing new access tokens from being issued.
- Rotate signing keys periodically; support JWKS endpoint for key discovery.

---

## 7. Audit Log Manipulation Attempt

**Failure Mode:** A database administrator (or a compromised application account) issues `DELETE FROM audit_logs WHERE actor_id = 'instructor_42'` to remove evidence of unauthorized grade changes. Without proper controls, the deletion succeeds silently.

**Impact:** Forensic investigation is obstructed; compliance audit finds gaps; if the manipulation is discovered, it constitutes a separate regulatory offense.

**Detection:**
- pgaudit / database activity monitoring (DAM): alert immediately on any DELETE or UPDATE statement targeting `audit_logs`.
- The application DB role has only INSERT privileges on `audit_logs`; any other operation returns a permission error.
- Hash chaining: each audit log entry includes `previous_hash` so gaps or modifications are detectable.

**Mitigation/Recovery:**
- Audit logs are append-only: database role used by the application has `INSERT` only on `audit_logs`, enforced at the PostgreSQL role level.
- Mirror audit logs to an immutable WORM storage target (e.g., S3 with Object Lock) within 60 seconds of creation.
- Any detection of a gap in the hash chain triggers an automatic security incident (P0); forensics team reviews within 1 hour.

---

## 8. Learner Enumerates Other Learners' Enrollment IDs via API

**Failure Mode:** Enrollment IDs are sequential integers (1001, 1002, 1003…). A learner discovers they can call `GET /enrollments/1005` and receive another learner's enrollment details (name, course, progress) by incrementing the ID. The API does not validate that the requesting learner owns the enrollment.

**Impact:** Learner PII exposure at scale; attacker can enumerate all enrollments systematically; GDPR violation (unauthorized access to others' personal data).

**Detection:**
- Alert on requests where `enrollment.learner_id != authenticated_user.id` unless the requester has an admin role.
- Monitor for sequential enumeration patterns: >10 consecutive enrollment ID requests from a single session.
- Automated IDOR test in CI: authenticate as Learner A; attempt to access Learner B's enrollment; assert `403 Forbidden`.

**Mitigation/Recovery:**
- Use non-guessable IDs for all resources accessible by learners: UUID v4 or ULID, never sequential integers.
- Authorization check on every resource endpoint: `enrollment.learner_id == current_user.id OR current_user.has_role(ADMIN)`.
- Existing sequential IDs: migrate to UUID primary keys in a background migration; update all foreign keys; issue new IDs in external-facing URLs.

---

## 9. DRM Bypass: Learner Downloads Video via Network Proxy Interception

**Failure Mode:** A learner configures a network proxy (e.g., Charles Proxy) to intercept HTTPS traffic. They capture the HLS segment URLs and decryption keys during legitimate playback. Using a download tool, they reassemble the full video from the captured segments without DRM restrictions.

**Impact:** Copyrighted or proprietary course content is permanently extracted and can be redistributed; content licensing agreements may be breached; potential loss of competitive advantage for the course creator.

**Detection:**
- Detect unusual download patterns: a single session downloading every HLS segment sequentially at high speed (>3x real-time).
- Alert on key requests: a session requesting decryption keys for segments beyond the buffer window (e.g., key requests for segments not yet playing).

**Mitigation/Recovery:**
- Use token-bound HLS: each segment URL is signed and tied to `(session_id, learner_id, expires_at)`; replaying the URL from another session returns `403`.
- Rotate segment decryption keys per viewing session; keys delivered via DRM server (e.g., Widevine, FairPlay) that authenticates the device.
- Accept that determined attackers can always capture screen/audio; focus DRM on protecting content at rest and reducing casual redistribution.
- Embed invisible steganographic watermarks in video streams tied to the `learner_id`; use for forensic tracing if content appears online.

---

## 10. GDPR Erasure Request for Learner with Active Certificates

**Failure Mode:** A learner submits a "Right to Be Forgotten" (GDPR Art. 17) request. The automated erasure pipeline deletes the learner's personal data from all tables. However, the learner's certificates reference their name and `learner_id`; deleting the learner record breaks certificate verification (the verify endpoint can no longer confirm the certificate is legitimate) and third parties holding the certificate code receive `"Not Found"`.

**Impact:** Legitimate certificate holders lose the ability to verify their credentials; employer/institution verification fails; learner may be harmed by the erasure of their own proof of achievement.

**Detection:**
- Pre-erasure impact assessment: query `certificates WHERE learner_id = ? AND state = ISSUED AND expiry_date > NOW()` before processing erasure.
- Alert if erasure request affects a learner with `active_certificate_count > 0`.

**Mitigation/Recovery:**
- Erasure pipeline presents a pre-erasure impact report to the privacy officer: lists active certificates, their verification codes, and expiry dates.
- Offer the learner the option to: (a) download all certificates before erasure, (b) retain certificates with pseudonymized display name, or (c) proceed with full erasure (certificates invalidated — learner is informed).
- If erased: replace learner PII in certificate records with a tombstone marker (`[ACCOUNT DELETED]`); certificate verify endpoint returns `{valid: true, learner: "[Account Deleted]"}` to honor credential integrity without PII exposure.
- Retain a minimal cryptographic proof (hash of learner ID + certificate ID) to allow the learner to prove the certificate was theirs without storing PII.
| Grade override occurs without reason capture | Audit weakness and dispute risk | Require mandatory reason and immutable audit history |
| Certificate verification endpoint leaks learner data | Privacy violation | Expose only minimal public verification metadata |
| Downloadable course assets contain sensitive content | Unauthorized redistribution risk | Use signed URLs, scoped access, and watermarking where needed |
| Export includes more learner data than allowed by policy | Compliance issue | Apply role-scoped export templates and approval flows |


## Implementation Details: Compliance Execution

- Privileged operations require role checks plus justification text.
- Tamper-evident audit pipeline with retention lock for regulated windows.
- Data export endpoints enforce scope filtering and signed export manifests.
