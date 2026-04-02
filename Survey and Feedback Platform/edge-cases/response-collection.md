# Edge Cases: Response Collection — Survey and Feedback Platform

**Domain:** `RESPONSE` | **File:** `response-collection.md` | **EC IDs:** EC-RESPONSE-001 through EC-RESPONSE-010

This file documents edge cases in the response collection pipeline. The pipeline accepts submissions
from the respondent-facing API (FastAPI), validates them against the survey schema, persists responses
to PostgreSQL 15 (transactional store), publishes events to AWS Kinesis Data Streams, and handles
partial session state in Redis 7. Celery workers process asynchronous tasks such as notifications
and analytics fan-out.

---

## Edge Cases

### EC-RESPONSE-001: Duplicate Response Submission (Double-Click / Network Retry Causing 2 Records)

| Field | Details |
|-------|---------|
| **Failure Mode** | A respondent clicks the "Submit" button on the last page of the survey. Due to a slow mobile connection, the HTTP 200 response is delayed by 3 seconds. The respondent double-clicks the submit button. Two identical `POST /surveys/{survey_id}/responses` requests hit the API within 50ms of each other. Both requests pass schema validation and both attempt to insert a new response record into PostgreSQL. The idempotency key check uses `Redis.SETNX` but a race condition between the two simultaneous requests means both acquire the lock before either has written to the DB. Two duplicate response records are created. |
| **Impact** | High. Duplicate responses skew survey analytics — NPS, completion rate, and all aggregate metrics are calculated from the total response count. A survey with 10% duplicates will show inflated engagement metrics and distorted answer distributions. Detecting and removing duplicates retroactively requires manual intervention and re-computation of all derived analytics. |
| **Detection** | Every response submission is assigned a client-generated `X-Idempotency-Key` header (UUID v4, generated on the respondent's device at session start). The API enforces idempotency by checking `Redis.SET idempotency:{key} {response_id} NX EX 86400` — if the key already exists, return HTTP 200 with the original response ID. A `DuplicateResponseBlocked` CloudWatch metric is emitted each time a duplicate is caught. A separate `DuplicateResponseLeaked` metric fires via a nightly dedup audit query: `SELECT survey_id, respondent_fingerprint, COUNT(*) FROM responses GROUP BY survey_id, respondent_fingerprint HAVING COUNT(*) > 1`. |
| **Mitigation / Recovery** | 1. Run the dedup audit query to identify affected surveys and response pairs. 2. For each duplicate pair, retain the record with the lower `id` (first insert) and soft-delete the duplicate: `UPDATE responses SET deleted_at = NOW(), deletion_reason = 'DUPLICATE' WHERE id = $duplicate_id`. 3. Invalidate the analytics cache for affected surveys: `redis.delete(f"analytics:{survey_id}:*")`. 4. Trigger an analytics recalculation task for each affected survey via Celery: `recalculate_survey_analytics.delay(survey_id)`. 5. Notify workspace owners of surveys where >1% of responses were duplicates. |
| **Prevention** | (1) **Code-level:** Implement atomic idempotency using a Lua script in Redis that executes `SETNX` and `GET` atomically, eliminating the race window. (2) **DB-level:** Add a unique partial index: `CREATE UNIQUE INDEX uq_response_idempotency ON responses (idempotency_key) WHERE deleted_at IS NULL` — the database is the final guard against duplicates. (3) **Frontend:** Disable the submit button immediately on first click and show a spinner. Re-enable only on explicit error (HTTP 4xx/5xx). (4) **Respondent fingerprint:** Generate a session fingerprint from `(survey_id, respondent_token, started_at_date)` stored in `responses.fingerprint` as an additional dedup signal. |

---

### EC-RESPONSE-002: Response Session Expires After 7-Day Inactivity (Partial Data Handling)

| Field | Details |
|-------|---------|
| **Failure Mode** | A respondent starts a long survey (30 questions) but saves their progress and returns 8 days later to complete it. The partial session is stored in Redis as `session:{token}` with a 7-day TTL. After 7 days, Redis evicts the key. When the respondent resumes via their saved link, the API returns HTTP 404 for the session token. The respondent's partial answers (questions 1–20) are permanently lost. The respondent must start from scratch, leading to survey fatigue and abandonment. |
| **Impact** | Medium. Loss of partial response data for respondents who take long breaks. For long surveys or surveys sent to populations with low response urgency (e.g., annual reviews), this could affect a meaningful percentage of respondents. The respondent experience is degraded — they see no warning that their session will expire. |
| **Detection** | The response API returns HTTP 404 with `error_code: SESSION_EXPIRED` for expired session tokens. A `SessionExpiredOnResume` CloudWatch metric is emitted per occurrence. The rate of this metric compared to total session resumes gives the session expiry rate. A CloudWatch alarm fires when session expiry rate > 5% in any 1-hour window (indicates a systematic TTL issue, not normal attrition). |
| **Mitigation / Recovery** | 1. When a session expiry is detected, the API returns a user-friendly HTML page explaining that the session expired and offering to restart the survey. 2. For surveys with a `allow_partial_save` flag, partial sessions are also persisted to PostgreSQL (not just Redis) with a 30-day retention, enabling recovery after Redis expiry. 3. To recover a specific respondent's session: `SELECT partial_data FROM partial_responses WHERE session_token_hash = $hash AND created_at > NOW() - INTERVAL '30 days'`. 4. If the DB partial response exists, restore it and issue a new Redis session token. |
| **Prevention** | (1) **Code-level:** For surveys longer than 10 questions, automatically enable `allow_partial_save=True` which persists partial responses to the `partial_responses` PostgreSQL table in addition to Redis. (2) **UX-level:** Display a session expiry countdown in the survey footer ("Your session will expire in 3 days") and send an email reminder 24 hours before expiry if the respondent provided an email. (3) **Infrastructure-level:** For enterprise-tier surveys, set Redis session TTL to 30 days (configurable per workspace). Free tier: 7 days. Business tier: 14 days. (4) **TTL refresh:** Extend the Redis TTL by 7 days on every page navigation within the survey — a respondent actively completing the survey will not have their session expire. |

---

### EC-RESPONSE-003: File Upload in Response Exceeds Tier Limit (10MB Free, 50MB Business)

| Field | Details |
|-------|---------|
| **Failure Mode** | A respondent attempts to upload a file in response to a file upload question. The respondent is on the Free tier workspace and tries to upload a 15MB MP4 video. The API's file size check uses the `Content-Length` header from the multipart request, but the respondent's client omits `Content-Length` (some mobile browsers do this for chunked uploads). The server begins streaming the upload to S3 before detecting the file size, resulting in a 15MB file stored in S3 for a Free tier workspace. The workspace storage quota is silently exceeded. |
| **Impact** | Medium. Workspace storage limits are violated. If left unchecked across many respondents, Free tier users can accumulate gigabytes of file storage, creating billing and storage cost overruns for the platform. Files stored over-limit may also be served to workspace owners, implicitly granting more than the paid-for capacity. |
| **Detection** | After the S3 multipart upload completes, the Lambda function `post-upload-validator` is triggered via S3 event notification. It checks the uploaded object size against the respondent's workspace plan limit. If the limit is exceeded, it emits the `FileUploadOverLimit` CloudWatch metric and invokes a remediation step. Additionally, a `WorkspaceStorageQuotaExceeded` CloudWatch alarm fires when total S3 usage per workspace crosses 95% of the plan limit. |
| **Mitigation / Recovery** | 1. The `post-upload-validator` Lambda immediately moves the over-limit file to `s3://survey-platform-quarantine/over-limit/` and updates the response record: `UPDATE response_files SET status = 'REJECTED', rejection_reason = 'SIZE_OVER_LIMIT' WHERE s3_key = $key`. 2. The respondent is notified via the survey's confirmation page that their file was rejected and the allowed limit. 3. The workspace owner is notified if their workspace is over storage quota. 4. The respondent is given 7 days to re-submit a smaller file via a re-upload link. |
| **Prevention** | (1) **API-level:** Generate S3 pre-signed upload URLs with a `Content-Length-Range` condition: `Conditions=[["content-length-range", 0, max_bytes]]` — S3 itself enforces the size limit and rejects over-limit uploads without storing any data. (2) **Frontend:** Validate file size client-side before initiating upload: `if (file.size > maxBytes) { showError(...); return; }`. (3) **Pydantic v2:** `FileUploadQuestion` model includes `max_file_size_bytes: int` field validated against plan limits in a `model_validator`. (4) **CDN-level:** CloudFront WAF rule `BlockLargeUploads` rejects requests with `Content-Length > 55000000` (55MB) at the edge, preventing even the API from receiving oversized uploads. |

---

### EC-RESPONSE-004: Survey Closed Mid-Response (Creator Closes Survey While Respondent Is Active)

| Field | Details |
|-------|---------|
| **Failure Mode** | A respondent is midway through completing a survey when the survey creator closes the survey (sets `status = 'closed'`). The respondent navigates to the next page and the API returns HTTP 403 Forbidden with `survey_status: closed`. The respondent's partially completed answers are in the browser state but cannot be submitted. The respondent loses their progress and sees an unhelpful error message. |
| **Impact** | Medium. Partial response data is lost for in-flight respondents at the moment of survey closure. Depending on the timing, this could affect dozens of respondents if the survey is popular and the creator closes it abruptly. The respondent experience is poor — no warning is given before the survey is closed. |
| **Detection** | The API returns HTTP 403 with `error_code: SURVEY_CLOSED` for submission attempts on closed surveys. A `SurveyClosedMidResponse` CloudWatch metric is emitted. The survey service logs the count of active sessions at the time of closure: `SELECT COUNT(*) FROM response_sessions WHERE survey_id = $1 AND status = 'in_progress'` — this is logged as `active_sessions_at_close` in the survey audit log. |
| **Mitigation / Recovery** | 1. When a creator closes a survey, the API checks for active in-progress sessions: `SELECT COUNT(*) FROM response_sessions WHERE survey_id = $1 AND status = 'in_progress' AND last_activity > NOW() - INTERVAL '30 minutes'`. 2. If active sessions > 0, the API returns a warning: "X respondents are currently completing this survey. Close anyway or schedule closure?" 3. If the creator proceeds, in-progress sessions are given a 15-minute grace period before the survey API endpoint returns 403. 4. Push a WebSocket notification to active respondent sessions: "This survey will close in 15 minutes. Please submit your responses." 5. Partial responses from respondents who could not submit are flagged as `status = 'grace_period_expired'` and retained for the creator's review. |
| **Prevention** | (1) **Code-level:** Implement a soft-close mechanism — `status = 'closing'` — that prevents new sessions from starting but allows existing sessions to complete. Only after all active sessions end (or a 30-minute timeout) does the status transition to `closed`. (2) **UX-level:** Add a prominent "X active respondents" counter on the survey creator dashboard. (3) **API-level:** The `PATCH /surveys/{id}` endpoint with `status: closed` triggers the soft-close workflow asynchronously via Celery task `soft_close_survey.delay(survey_id)`. |

---

### EC-RESPONSE-005: Required Question Bypass via Direct API Manipulation (Burp Suite)

| Field | Details |
|-------|---------|
| **Failure Mode** | A survey has 5 questions, with Q3 marked as required (must be answered before submission). An attacker intercepts the `POST /surveys/{id}/responses` request using Burp Suite and removes the `answers` entry for Q3 from the JSON payload. The API performs server-side validation but the required-field check uses only the frontend-generated answer list without cross-referencing the survey's `required_questions` list from the database. The response is accepted and stored with Q3 missing, bypassing the survey integrity requirement. |
| **Impact** | Critical. Required questions serve as data quality gates — they may be consent questions, mandatory demographic fields, or compliance statements. A bypassed required question means the response is incomplete and potentially invalid. If the required question is a consent checkbox (GDPR Article 6 lawful basis), an incomplete consent record could constitute a compliance violation. |
| **Detection** | Post-submission, the `ResponseIntegrityValidator` background task (Celery) re-validates every stored response against the survey's current required question list. Responses with missing required answers emit `RequiredQuestionBypassDetected` CloudWatch metric. A WAF rule `BlockSuspiciousResponsePayloads` monitors for response payloads that have fewer `answers` keys than the survey's `required_question_count` field. |
| **Mitigation / Recovery** | 1. Mark the affected response as `integrity_status = 'FAILED_VALIDATION'` in the `responses` table. 2. Do not include failed-validation responses in analytics calculations — filter with `WHERE integrity_status = 'PASSED'`. 3. Notify the workspace owner: "X responses failed integrity validation. They have been excluded from analytics." 4. If the bypassed question was a consent question, treat the response as non-consented and apply data handling accordingly (do not process PII). 5. IP-ban the source IP at the WAF level for 24 hours if >3 bypass attempts are detected from the same IP. |
| **Prevention** | (1) **Code-level (primary):** Server-side validation in the response submission handler always re-fetches the survey's question schema from the DB and validates that all required questions have non-null, non-empty answers — this check is completely independent of the client-submitted payload structure. (2) **Pydantic v2:** `ResponseSubmitRequest` model uses a `model_validator(mode='after')` that calls `validate_required_answers(self, survey_schema)` before the record is written. (3) **DB-level:** A PostgreSQL trigger `trg_validate_response_completeness` fires `BEFORE INSERT` on `responses` and checks the `answers` JSONB field against the survey's required question mask. (4) **Rate limiting:** WAF rate rule limits `POST /surveys/*/responses` to 60 requests per minute per IP, reducing the feasibility of automated bypass attempts. |

---

### EC-RESPONSE-006: Kinesis Shard Iterator Expiry (Analytics 5+ Minutes Behind)

| Field | Details |
|-------|---------|
| **Failure Mode** | The analytics pipeline reads response events from an AWS Kinesis Data Stream using a Lambda consumer. The Lambda function has a concurrency limit of 10 and is overwhelmed during a traffic spike (a viral survey receives 2,000 submissions/minute). The Lambda function throttles. Kinesis shard iterators expire after 5 minutes of inactivity. By the time Lambda recovers, the iterator has expired and the consumer must reset to `TRIM_HORIZON` or `LATEST` — causing either a gap in analytics data (LATEST) or a re-processing flood (TRIM_HORIZON). |
| **Impact** | High. Real-time analytics dashboard becomes stale — NPS scores, response counts, and live completion maps show data that is 5+ minutes old. For surveys with real-time monitoring use cases (e.g., live event feedback), this severely degrades the value of the platform. Re-processing from TRIM_HORIZON causes duplicate analytics events and inflated metrics. |
| **Detection** | CloudWatch metric `GetRecords.IteratorAgeMilliseconds` for the Kinesis stream `survey-platform-responses` triggers alarm `SurveyPlatform-KinesisConsumerLag` when value > 300,000 ms (5 minutes). Lambda `ThrottleCount` metric triggers `KinesisLambdaThrottling` alarm when > 100 throttles in 5 minutes. The analytics dashboard shows a `data_freshness_warning` banner when the last processed event timestamp is > 3 minutes old. |
| **Mitigation / Recovery** | 1. Immediately increase Lambda concurrency limit for `kinesis-response-processor` from 10 to 100: `aws lambda put-function-concurrency --function-name kinesis-response-processor --reserved-concurrent-executions 100`. 2. Add Kinesis shards to increase read throughput: `aws kinesis update-shard-count --stream-name survey-platform-responses --target-shard-count 8 --scaling-type UNIFORM_SCALING`. 3. After recovery, use Kinesis Enhanced Fan-Out to provide a dedicated 2 MB/s throughput per consumer, eliminating iterator sharing. 4. Monitor `IteratorAgeMilliseconds` until it drops below 60,000 ms. 5. If TRIM_HORIZON was used: run dedup Lambda to identify and remove duplicate analytics records in DynamoDB (compare event IDs). |
| **Prevention** | (1) **Architecture:** Enable Kinesis Enhanced Fan-Out for the analytics Lambda consumer — each consumer gets dedicated 2 MB/s throughput with push delivery, eliminating iterator expiry risk. (2) **Lambda scaling:** Set Lambda reserved concurrency to 50 (not 10) and configure Provisioned Concurrency for the analytics function to eliminate cold starts. (3) **Error handling:** Lambda consumer implements exponential backoff with jitter on `ProvisionedThroughputExceededException`. (4) **Idempotency:** Every Kinesis event includes a unique `event_id`. Lambda consumer checks `event_id` against a DynamoDB idempotency table before processing, preventing duplicate analytics on TRIM_HORIZON replay. |

---

### EC-RESPONSE-007: Offline PWA Response Sync Conflict (Same Partial Session Submitted from 2 Devices)

| Field | Details |
|-------|---------|
| **Failure Mode** | A respondent starts a survey on their laptop (offline PWA mode) and answers questions 1–10. Without completing the survey, they also open the same survey link on their phone and answer questions 1–10 with different answers. Both devices regain connectivity simultaneously and both submit their partial sessions. The sync endpoint receives two `POST /surveys/{id}/responses/sync` requests with the same `session_token` but different `answers` payloads and different `device_id` values. Both are written to the `partial_responses` table, creating conflicting records. |
| **Impact** | High. Two conflicting partial responses for the same respondent exist in the system. If both are promoted to full responses (after completion), the survey has duplicate data with contradictory answers. If only one is promoted (last-write-wins), half the respondent's deliberate answers are silently discarded. The respondent is not informed of the conflict. |
| **Detection** | The sync endpoint checks `SELECT COUNT(*) FROM partial_responses WHERE session_token = $1` — if > 1, a `PWASyncConflict` event is logged to `/survey-platform/response-service` with both device IDs. A CloudWatch metric `PWASyncConflictRate` is emitted. The alarm `SurveyPlatform-PWASyncConflict` fires if this rate exceeds 0.5% of sync attempts in a 10-minute window. |
| **Mitigation / Recovery** | 1. Apply Last-Write-Wins with timestamp comparison: retain the partial response with the higher `synced_at` timestamp — this represents the most recent device activity. 2. Set the losing record's status to `conflict_discarded` and retain it for 30 days for audit purposes. 3. Flag the winning response in the UI: the survey creator sees a `⚠ Sync Conflict Resolved` badge on the response, with a diff of the two conflicting answer sets available for review. 4. Notify the respondent (if email is available): "We detected a sync conflict between your devices. We've kept your most recent answers." |
| **Prevention** | (1) **Code-level:** Each partial response sync includes a `vector_clock` or `lamport_timestamp` field generated by the device. The server uses vector clocks to detect concurrent conflicting writes — if clocks indicate true concurrency (not a simple ordering), trigger the conflict resolution workflow rather than silently applying last-write-wins. (2) **UX-level:** The PWA displays a warning when a sync conflict is detected: "We found answers from another device. Which set would you like to keep?" (3) **Architecture-level:** Session tokens are device-scoped: `session_token = SHA256(respondent_token + device_id + survey_id)`. Different devices generate different session tokens, so their partial responses are stored as separate records. The completion endpoint then requires the respondent to explicitly choose which device session to submit. |

---

### EC-RESPONSE-008: Bot Flood (100+ Responses/Minute from Rotating IPs)

| Field | Details |
|-------|---------|
| **Failure Mode** | A bad actor runs a bot that submits 500 responses per minute to a competitor's survey, flooding it with fake data. The bot rotates through 50 IP addresses (each contributing 10 req/min), staying below the per-IP rate limit of 60 req/min. The WAF per-IP rate rule does not fire. The survey accumulates thousands of junk responses within minutes, completely corrupting the analytics data. The RDS `responses` table grows rapidly, consuming disk I/O and degrading performance for all surveys in the cluster. |
| **Impact** | Critical. The affected survey's analytics are permanently corrupted unless the fake responses can be identified and removed. NPS, CSAT, and completion metrics are meaningless. If the survey owner is a paying enterprise customer, data integrity SLAs are violated. The DB performance degradation affects all tenants on the cluster (noisy neighbour effect). |
| **Detection** | CloudWatch custom metric `SurveyResponseRate` per `survey_id` dimension triggers alarm `SurveyPlatform-BotFloodDetection` when `ResponseSubmissionRate > 100/min per survey_id` — this is a per-survey metric, not per-IP, so it catches distributed bot attacks. AWS WAF `AWSManagedRulesBotControlRuleSet` detects bot signatures. AWS Shield Advanced detects volumetric anomalies. Honeypot field `hp_field` (hidden in form, never filled by humans) triggers `HoneypotFieldFilled` metric when non-null. |
| **Mitigation / Recovery** | 1. Immediately auto-enable CAPTCHA for the affected survey: `UPDATE surveys SET captcha_required = TRUE WHERE id = $1`. 2. Pause the survey to stop further submissions: `UPDATE surveys SET status = 'paused' WHERE id = $1`. 3. Identify bot responses using heuristics: `SELECT id FROM responses WHERE survey_id = $1 AND (completion_time_seconds < 10 OR honeypot_field IS NOT NULL OR ip_address IN (SELECT ip FROM known_bot_ips))`. 4. Bulk-delete bot responses: `UPDATE responses SET deleted_at = NOW(), deletion_reason = 'BOT_DETECTION' WHERE id = ANY($bot_ids)`. 5. Recalculate analytics post-cleanup: `recalculate_survey_analytics.delay(survey_id)`. 6. Alert the survey owner and offer a clean data report. |
| **Prevention** | (1) **WAF:** Deploy AWS WAF Bot Control managed rule group on the survey submission endpoint. Enable Targeted Bot Control for sophisticated bots. (2) **Per-survey rate limiting:** Redis rate limit at the survey level (not just IP level): `INCR survey:{id}:submissions:{minute_window}` — if > 200/min, auto-enable CAPTCHA. (3) **Honeypot fields:** Every survey form includes a hidden input field `hp_survey_token` that is invisible to humans (CSS `display: none`) but filled in by bots. Server-side rejects any submission where `hp_survey_token` is non-null. (4) **Behavioural analysis:** Flag responses with completion time < 10 seconds (typical minimum human completion for 5+ questions) for manual review. (5) **AWS Shield Advanced:** Enrolled on the survey submission endpoint for volumetric DDoS protection. |

---

### EC-RESPONSE-009: Response Data Loss During RDS Primary Failover

| Field | Details |
|-------|---------|
| **Failure Mode** | The RDS PostgreSQL primary instance (Multi-AZ) experiences a hardware failure and initiates an automated failover to the standby. During the 30–60 second failover window, all writes to the `responses` table fail with `OperationalError: could not connect to server`. The FastAPI application does not have a retry mechanism — it returns HTTP 503 to respondents and their answers are lost. Because the response form does not buffer failed submissions locally, the respondent must re-answer all questions. |
| **Impact** | Critical. Response data is permanently lost for submissions attempted during the failover window. For high-traffic surveys (1000+ submissions/hour), this could mean 17–33 lost responses per incident. If the failover is caused by a planned maintenance event and not communicated, multiple respondents are affected simultaneously. |
| **Detection** | RDS emits event `RDS-EVENT-0006` (failover started) and `RDS-EVENT-0025` (failover completed) to EventBridge. A CloudWatch alarm `SurveyPlatform-RDSFailover` triggers on these events and pages the on-call engineer via PagerDuty P1. Application-level: SQLAlchemy `OperationalError` exceptions spike — `DBWriteErrorRate > 5/min` CloudWatch alarm fires. RDS Enhanced Monitoring shows `DatabaseConnections` dropping to 0 then recovering. |
| **Mitigation / Recovery** | 1. Confirm the new RDS primary endpoint in the RDS console — with Multi-AZ, the cluster endpoint automatically points to the new primary within 60 seconds. 2. The application uses the RDS cluster endpoint (not the instance endpoint), so it auto-reconnects without configuration changes. 3. Verify SQLAlchemy connection pool recovers: `pool_pre_ping=True` ensures stale connections are tested and replaced. 4. Check in-flight transactions: `SELECT pid, query, state FROM pg_stat_activity WHERE state = 'idle in transaction' AND query_start < NOW() - INTERVAL '5 minutes'` — cancel stale transactions: `SELECT pg_cancel_backend(pid)`. 5. Implement a response submission buffer: failed 503 submissions are queued in a client-side IndexedDB store and auto-retried when connectivity is restored. |
| **Prevention** | (1) **SQLAlchemy config:** `create_engine(..., pool_pre_ping=True, pool_size=20, max_overflow=10, pool_timeout=30)` — `pool_pre_ping` tests each connection before use, automatically removing stale connections from the pool. (2) **Application retry:** Wrap response write operations with `tenacity` retry decorator: `@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=0.5, max=5), retry=retry_if_exception_type(OperationalError))`. (3) **Client-side buffering:** The survey PWA queues `POST /responses` requests in IndexedDB on HTTP 503. The `Background Sync API` (Service Worker) replays the queue when connectivity is restored. (4) **RDS PITR:** Enable RDS Point-In-Time Recovery (5-minute RPO) — even in the worst case, at most 5 minutes of data could be lost (though with Write-Ahead Logging and Multi-AZ synchronous replication, no committed transactions are lost). |

---

### EC-RESPONSE-010: GDPR Subject Access Request — Respondent Was Anonymous (No Email, Just IP)

| Field | Details |
|-------|---------|
| **Failure Mode** | A respondent submits a response to an anonymous survey (no email required). Six months later, the respondent submits a GDPR Subject Access Request (SAR) claiming their IP address `198.51.100.42` uniquely identifies them, and requests all their personal data. The SAR processing team cannot identify the respondent's responses because: (a) the IP address was truncated to `/24` after 30 days per policy, so the exact IP is gone; (b) there is no email or account linking the respondent to their responses; (c) the respondent cannot provide any corroborating information (survey link, approximate submission date) to narrow the search. The SAR cannot be fulfilled, but the platform must respond within the 30-day GDPR deadline. |
| **Impact** | High. Failure to respond to a SAR within 30 days (GDPR Article 12) constitutes a regulatory violation. The Information Commissioner's Office (ICO) or relevant DPA can levy fines of up to €20M or 4% of annual global turnover. Reputational damage if the respondent files a complaint. Legal costs of DPA engagement. |
| **Detection** | SAR tickets are tracked in the `data_subject_requests` table with `status` (pending/processing/completed/unable_to_identify) and `due_date` (submitted_at + 30 days). A CloudWatch Events rule triggers a Lambda reminder 5 days before the `due_date` if the status is still `pending` or `processing`. A `SARDeadlineApproaching` SNS notification is sent to the DPO inbox. |
| **Mitigation / Recovery** | 1. Within 5 business days, send a written acknowledgement to the requester confirming receipt of the SAR. 2. Request additional information to identify the respondent: survey URL, approximate submission date/time, browser/device type (to narrow down responses). 3. If the respondent provides a submission date range, query: `SELECT * FROM responses WHERE survey_id = ANY($known_surveys) AND created_at BETWEEN $start AND $end AND ip_prefix = '198.51.100'` — return matching records (using the truncated IP prefix). 4. If identification is genuinely impossible, respond to the requester in writing explaining the anonymisation policy and why the responses cannot be linked to their identity — this is an acceptable GDPR response per Recital 57. 5. Document the process, the response sent, and the outcome in `data_subject_requests.resolution_notes`. |
| **Prevention** | (1) **Privacy by design:** Anonymous surveys display a clear notice before the respondent starts: "This survey is anonymous. We store only a partial IP address for security. We will be unable to retrieve or delete your specific response after submission." This sets expectations and provides evidence of informed acceptance. (2) **Respondent tokens:** Offer respondents an optional "response token" (a random code displayed at submission confirmation) that they can save and use to identify their response in a future SAR — this enables identification without storing PII. (3) **Policy-level:** Document the anonymisation pipeline in the platform Privacy Policy with specific retention durations, ensuring GDPR Recital 57 (genuinely anonymous data) defences are well-founded. (4) **Process-level:** SAR SOP includes a standardised "Unable to Identify" response template pre-approved by legal counsel. |

---

## Response Integrity Guarantees

### Exactly-Once Semantics

The response collection pipeline provides exactly-once delivery guarantees through a multi-layer
approach:

1. **Client-side idempotency key:** Every survey session generates a UUID v4 `idempotency_key` stored
   in the browser's `sessionStorage`. This key is sent as `X-Idempotency-Key` header on every
   submission attempt.

2. **Redis atomic lock:** The API uses a Lua script to atomically check and set the idempotency key
   in Redis with a 24-hour TTL. If the key already exists, the original response record ID is returned
   immediately without any DB write.

3. **PostgreSQL unique constraint:** A unique partial index on `responses(idempotency_key)` ensures
   the database layer rejects duplicates even if the Redis layer fails.

4. **Kinesis sequence deduplication:** Every event published to Kinesis includes the response's
   `idempotency_key`. The Lambda analytics consumer tracks processed event IDs in a DynamoDB
   idempotency table (`kinesis_processed_events`) with a 24-hour TTL.

### Idempotency Key Format

```
{survey_id}:{respondent_token}:{session_start_timestamp_ms}:{random_4_bytes_hex}
```

Example: `abc123:resp_xyz:1714500000000:a1b2c3d4`

### ACID Guarantees

All response writes to PostgreSQL are wrapped in explicit transactions:

```python
async with db.begin():
    response = await db.execute(insert(Response).values(...))
    await db.execute(insert(ResponseAnswer).values(...).returning(ResponseAnswer.id))
    await publish_kinesis_event(response.id)  # best-effort; does not roll back transaction
```

The PostgreSQL transaction ensures atomicity of the response record and all its answer records.
Kinesis publication is best-effort — if Kinesis publish fails, the response is still committed to
PostgreSQL. The Kinesis publisher retries via a Celery task `retry_kinesis_publish` with
exponential backoff (max 5 attempts, max 30s delay).

### Partial Response Consistency

Partial responses saved during multi-page survey navigation are stored in Redis AND PostgreSQL:
- Redis (`session:{token}:answers`) — fast access, 7-day TTL (plan-dependent)
- PostgreSQL `partial_responses` — durable store, 30-day retention
- On final submission, the `partial_responses` record is atomically promoted to `responses` in a
  single transaction, preventing orphaned partial records.

---

## Operational Policy Addendum

### 1. Response Data Privacy Policies

Survey responses are personal data under GDPR Article 4(1) if they can be attributed to an identified
or identifiable natural person. The platform handles responses as follows:

- **Data minimisation (Article 5(1)(c)):** Only questions marked as required are required. The platform
  does not infer or derive additional personal data from responses without explicit workspace configuration.
- **Purpose limitation (Article 5(1)(b)):** Response data is used only for the purposes declared by
  the workspace owner in their workspace Privacy Policy. The platform does not process response data
  for its own advertising, profiling, or data resale purposes.
- **IP address retention:** Full IP addresses are retained for 30 days for security purposes (bot
  detection, abuse prevention). After 30 days, IPs are truncated to /24 (IPv4) or /48 (IPv6). Truncated
  IPs are retained for up to 90 days as statistical signals only.
- **Respondent rights:** Respondents who provided an email can exercise erasure rights via
  `DELETE /me/responses`. Anonymous respondents are advised of the limitations (EC-RESPONSE-010).

CCPA: California respondents may opt-out of any cross-survey profiling by emailing privacy@surveyplatform.io
or via the in-survey opt-out link. No response data is sold to third parties.

### 2. Survey Distribution Policies

Response collection endpoints are designed to accept only submissions from respondents who have received
a valid survey distribution link. Unauthenticated `POST /surveys/{id}/responses` requests are accepted
only if the survey has `access_type = 'public'`. All other surveys require a signed token in the survey
URL to submit a response.

CAN-SPAM / CASL: Response collection itself is not subject to CAN-SPAM (no commercial email is sent
at submission time). Survey invitation emails that drove the respondent to the survey are governed by
CAN-SPAM and CASL rules (see distribution-and-sharing.md).

### 3. Analytics and Retention Policies

- **Response retention:** Free tier: 12 months. Business tier: 36 months. Enterprise tier: configurable.
- **Partial response retention:** 30 days (all tiers). Partial responses not completed within 30 days
  are anonymised (email/IP removed) and retained as statistical data for completion rate analysis.
- **Analytics aggregation:** Per-survey aggregates (NPS, completion rate, average score) are persisted
  in DynamoDB with indefinite retention. Raw response records are subject to tier-based retention.
- **Anonymisation:** After the retention period, response records have all PII fields nulled:
  `UPDATE responses SET respondent_email = NULL, ip_address = NULL, metadata = NULL WHERE survey_id = $1 AND created_at < $cutoff`.
  Anonymised responses are retained for aggregate statistics.

### 4. System Availability Policies

- **Response submission SLA:** 99.9% monthly uptime. The submission endpoint is the highest-priority
  service component — it is deployed as a dedicated ECS Fargate service separate from the admin API.
- **RTO:** 15 minutes for submission endpoint Critical incidents.
- **RPO:** 5 minutes (RDS PITR continuous backup). No committed response data is lost after the
  RDS Multi-AZ failover (synchronous replication ensures standby is fully up-to-date).
- **Maintenance:** The response submission endpoint is never taken offline for planned maintenance.
  Schema migrations use the Expand-Contract pattern to ensure zero-downtime deploys.
