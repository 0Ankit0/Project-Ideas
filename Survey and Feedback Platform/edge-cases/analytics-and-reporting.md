# Edge Cases: Analytics and Reporting — Survey and Feedback Platform

**Domain:** `ANALYTICS` | **File:** `analytics-and-reporting.md` | **EC IDs:** EC-ANALYTICS-001 through EC-ANALYTICS-008

This file documents edge cases in the analytics and reporting pipeline. Analytics are powered by
AWS Kinesis Data Streams (ingestion) → AWS Lambda (stream processing) → DynamoDB (aggregated metrics),
with Celery workers handling scheduled report generation, Redis 7 for dashboard caching, and
AWS Comprehend for sentiment analysis of open-text responses.

---

## Edge Cases

### EC-ANALYTICS-001: NPS Calculation with <10 Responses (Statistically Unreliable)

| Field | Details |
|-------|---------|
| **Failure Mode** | A workspace owner views the NPS dashboard for a newly distributed survey that has received only 4 responses (3 Promoters, 1 Detractor). The platform calculates NPS = (3 − 1) / 4 × 100 = 50 and displays this as a confident NPS score with no caveats. The workspace owner reports the 50 NPS to their executive team as a statistically valid result. In reality, with n=4, the 95% confidence interval spans from −36 to +96 — the displayed number is meaningless. When the survey accumulates 200 responses, the actual NPS is 12, creating a significant credibility problem. |
| **Impact** | Medium. Business decisions made on unreliable statistical metrics. No data corruption, but misleading information presented as fact. Trust in the platform's analytics is damaged when numbers change drastically as more responses arrive. Severity increases if the metric is used for executive reporting or SLA purposes. |
| **Detection** | The `NPSCalculator.compute()` method checks `if total_responses < NPS_MIN_SAMPLE_SIZE (default: 10)` and sets `nps_result.reliability = 'INSUFFICIENT_SAMPLE'`. The dashboard API response includes `reliability_flag: 'insufficient_sample'` and a 95% confidence interval band. A `LowSampleNPSViewed` metric is emitted when a user views an NPS score with n < 10. |
| **Mitigation / Recovery** | 1. Retroactively add reliability flags to all NPS scores stored in DynamoDB where `response_count < 10`: update the `reliability` attribute on existing items. 2. Send a platform notification to workspace owners who have viewed NPS results with < 10 responses in the last 30 days: "We've added a statistical reliability indicator to NPS results with small sample sizes." 3. Add a tooltip to NPS cards: "NPS with fewer than 10 responses has a wide confidence interval and may not reflect your actual score." |
| **Prevention** | (1) **Code-level:** `NPSCalculator.compute()` always returns a `confidence_interval` (Wilson score interval) alongside the NPS value. (2) **UI-level:** NPS widgets display a yellow badge "Low sample size" when n < 10 and a red badge "Too few responses for NPS" when n < 5. (3) **API-level:** The `GET /analytics/surveys/{id}/nps` endpoint includes `min_sample_met: bool` and `confidence_interval: {lower: float, upper: float}` in every response. (4) **Email reports:** Automated NPS digest emails include a footnote: "Statistical reliability: Good (n=142)" or "Statistical reliability: Low (n=6, confidence interval ±47 points)". |

---

### EC-ANALYTICS-002: Kinesis Consumer Lag >5 Minutes (Real-Time Dashboard Becomes Stale)

| Field | Details |
|-------|---------|
| **Failure Mode** | A viral survey receives a sudden spike of 3,000 submissions per minute. The Kinesis stream has 4 shards (capacity: 4,000 records/sec total, 4 MB/sec). Each shard's Lambda consumer function has a reserved concurrency of 5, totalling 20 concurrent Lambda executions. At 3,000 submissions/minute (50/sec), each submission generates 2 Kinesis events (response_created, answer_recorded). The 100 events/sec volume overwhelms the 20 concurrent Lambda functions. Lambda throttling causes GetRecords calls to back off, causing iterator age to increase. Within 8 minutes, the iterator age exceeds 5 minutes, and the real-time dashboard shows stale data. |
| **Impact** | High. Analytics dashboard shows response counts and NPS scores from 5+ minutes ago. For live event feedback use cases (e.g., a conference session collecting real-time satisfaction scores), this delay makes the analytics practically useless. The workspace owner may make decisions based on outdated data without realising the dashboard is stale. |
| **Detection** | CloudWatch metric `GetRecords.IteratorAgeMilliseconds` on stream `survey-platform-responses` triggers alarm `SurveyPlatform-KinesisConsumerLag` when maximum value > 300,000 ms (5 minutes) for 2 consecutive data points. The analytics dashboard API includes a `last_processed_event_at` timestamp in every response — if this is > 3 minutes old, the frontend shows a "⚠ Data may be delayed" banner. |
| **Mitigation / Recovery** | 1. Immediately increase Lambda reserved concurrency: `aws lambda put-function-concurrency --function-name kinesis-response-processor --reserved-concurrent-executions 200`. 2. Add Kinesis shards to increase throughput capacity: `aws kinesis update-shard-count --stream-name survey-platform-responses --target-shard-count 8 --scaling-type UNIFORM_SCALING` (note: resharding takes ~30 seconds per shard pair). 3. Enable Kinesis Enhanced Fan-Out for the analytics consumer to receive push delivery at 2 MB/s per consumer per shard: `aws kinesis register-stream-consumer --stream-arn <arn> --consumer-name analytics-consumer`. 4. After recovery, verify lag is < 60s: `aws cloudwatch get-metric-statistics --metric-name GetRecords.IteratorAgeMilliseconds --statistics Maximum`. 5. If backfill is needed, trigger a Kinesis Data Analytics application to replay events from the point of lag onset. |
| **Prevention** | (1) **Architecture:** Use Kinesis Enhanced Fan-Out by default for all production consumers — push delivery at dedicated 2 MB/s per shard eliminates iterator sharing throttling. (2) **Auto-scaling:** Deploy a CloudWatch + Lambda auto-scaling policy that increases Kinesis shard count when `IncomingRecords > 70% of shard capacity` for 2 consecutive minutes. (3) **Lambda concurrency:** Set base concurrency to 50 per function and use Application Auto Scaling for Lambda to scale up to 500 during spikes. (4) **Batch size:** Set Kinesis Lambda trigger batch size to 100 records and parallelisation factor to 10 per shard, maximising throughput per Lambda invocation. |

---

### EC-ANALYTICS-003: Cross-Tabulation Query Timeout on 500K+ Response Dataset

| Field | Details |
|-------|---------|
| **Failure Mode** | A workspace analyst runs a cross-tabulation report comparing answers to Q3 (gender, 3 options) against answers to Q7 (satisfaction, 5 options) for a survey with 600,000 responses. The cross-tab SQL query performs two full table scans on the `response_answers` table without using the composite index on `(survey_id, question_id, answer_value)`. PostgreSQL's query planner chooses a hash join strategy that requires 6 GB of work memory. The Celery worker's container has only 4 GB RAM, causing the worker to be killed by the OOM killer (SIGKILL). The report job shows `status = 'FAILED'` with no error details exposed to the user. |
| **Impact** | High. Enterprise users with large datasets cannot generate cross-tabulation reports — a core analytics feature. The Celery worker OOM also kills any other tasks running in the same worker process (though Celery acks tasks after pickup, so other tasks are retried). Repeated OOM failures cause the Celery worker to restart continuously, degrading throughput for all analytics tasks. |
| **Detection** | Celery task `generate_crosstab_report` emits `task.runtime` metric. When a task is killed by SIGKILL, it does not emit a completion event — the task disappears from the queue without acknowledgement. A CloudWatch alarm `SurveyPlatform-CeleryTaskDisappeared` fires when a task's heartbeat stops before completion. ECS container insights show `MemoryUtilization > 95%` for the worker task. CloudWatch Log Insights query: `filter @message like "Killed" | stats count(*) by bin(5min)` on `/survey-platform/worker-service`. |
| **Mitigation / Recovery** | 1. Identify the failing task: `SELECT id, payload, status, error FROM celery_task_log WHERE task_name = 'generate_crosstab_report' AND status = 'FAILED' AND updated_at > NOW() - INTERVAL '1 hour'`. 2. Retry the task with a streaming approach: instead of loading all 600K rows into memory, use a server-side PostgreSQL cursor with `FETCH 10000` rows at a time and build the cross-tab incrementally. 3. For immediate relief, redirect the task to a dedicated high-memory Fargate task definition (`report-worker: 16 vCPU, 32 GB RAM`) instead of the standard worker. 4. Notify the user: "Your report is taking longer than expected due to the large dataset. You'll receive an email when it's ready." |
| **Prevention** | (1) **Query optimisation:** Ensure composite index on `response_answers(survey_id, question_id, answer_value)` is used — run `EXPLAIN ANALYZE` on the cross-tab query in staging and verify index usage. Add `SET enable_hashjoin = off` if the hash join plan is consistently chosen incorrectly. (2) **Streaming aggregation:** Implement cross-tab reports using DynamoDB pre-computed aggregations instead of ad-hoc PostgreSQL queries for datasets > 50K responses. (3) **Memory limits:** Set Celery worker `worker_max_memory_per_child = 2048` (MB) — if a single task exceeds 2 GB, the worker process is gracefully restarted (vs. SIGKILL). (4) **Query timeout:** Set `statement_timeout = 60000` (60 seconds) in the analytics DB connection pool — cross-tab queries exceeding 60s return a structured error rather than hanging. (5) **Task routing:** Route large-dataset report tasks (`response_count > 100000`) to a dedicated `heavy-reports` Celery queue backed by high-memory workers. |

---

### EC-ANALYTICS-004: Report Generation OOM — Celery Worker Killed (SIGKILL at 4GB RAM)

| Field | Details |
|-------|---------|
| **Failure Mode** | A workspace owner schedules a weekly full-export report for a survey with 50,000 responses, each containing 30 questions with long open-text answers. The Celery task `export_full_response_data` loads all 50,000 responses into a Python list in memory using `all_responses = await db.execute(select(Response).where(...).all())`, then iterates to build an XLSX workbook using `openpyxl`. The total in-memory footprint reaches 4.2 GB, exceeding the 4 GB ECS Fargate task limit. The Linux OOM killer sends SIGKILL to the Python process. The XLSX file is partially written to S3 but the multipart upload is not completed — the S3 incomplete multipart upload remains and accumulates storage costs. |
| **Impact** | High. The scheduled report is never delivered. The workspace owner may not notice until they check the report history. Partial S3 multipart uploads accumulate silently, incurring storage costs. If the report is critical (e.g., end-of-month compliance export), the workspace owner may face audit issues. |
| **Detection** | ECS container `MemoryUtilization` metric exceeds 90% for the `report-worker` task. CloudWatch alarm `SurveyPlatform-CeleryWorkerOOM` fires at 90% memory utilisation for 3 consecutive minutes. The Celery task broker shows the task in `STARTED` state with no heartbeat for > 10 minutes — `CeleryTaskStalledDetector` Lambda checks for stalled tasks every 5 minutes. S3 Lifecycle Rule `CleanupIncompleteMultipartUploads` (7-day TTL) is the detection mechanism for stale uploads. |
| **Mitigation / Recovery** | 1. Abort incomplete S3 multipart uploads: `aws s3api list-multipart-uploads --bucket survey-platform-reports | jq '.Uploads[] | select(.Initiated < "CUTOFF_DATE")' | aws s3api abort-multipart-upload --bucket survey-platform-reports --key <Key> --upload-id <UploadId>`. 2. Re-queue the failed export task with chunked processing enabled: `export_full_response_data.apply_async(kwargs={'survey_id': sid, 'chunk_size': 1000}, queue='heavy-reports')`. 3. Increase the report worker task definition memory to 8 GB for the re-run. 4. Notify the workspace owner: "Your scheduled report encountered an error and has been re-queued. Expected delivery: within 2 hours." |
| **Prevention** | (1) **Streaming DB reads:** Replace `all()` with a server-side cursor: iterate `await db.stream(select(Response).where(...))` in chunks of 1,000 rows, writing each chunk to the XLSX file incrementally. (2) **S3 streaming write:** Use `s3transfer` with multipart upload + streaming writer — write XLSX data to S3 directly without accumulating the full workbook in memory. (3) **Memory guard:** Set `worker_max_memory_per_child = 3072` in Celery config — gracefully restart the worker before SIGKILL occurs, allowing the task to be retried. (4) **S3 lifecycle policy:** Configure an S3 lifecycle rule to automatically abort multipart uploads older than 24 hours: `AbortIncompleteMultipartUpload: DaysAfterInitiation: 1`. (5) **Task sizing:** Route export tasks with `response_count > 10000` to the `heavy-reports` queue (16 GB Fargate task definition). |

---

### EC-ANALYTICS-005: DynamoDB Hot Partition from Viral Survey (Single survey_id Key)

| Field | Details |
|-------|---------|
| **Failure Mode** | A survey goes viral on social media and receives 50,000 submissions within 1 hour (≈14 submissions/second). All analytics events for this survey write to a single DynamoDB partition key: `survey_id = 'abc123'`. DynamoDB's per-partition write throughput limit is 1,000 WCU/second. With each submission writing 3 analytics items (response_created, answers_recorded, nps_event) at 1 WCU each, the peak write rate hits 42 WCU/sec per partition — well within the limit. However, with on-demand billing mode, DynamoDB still throttles when a single partition receives > 1,000 WCU/sec sustained. If the survey receives a burst of 10,000 submissions simultaneously, the 30,000 WCU burst exceeds the single-partition limit and writes are throttled, causing analytics events to be dropped by the Lambda consumer. |
| **Impact** | High. Analytics data for the viral survey is incomplete or delayed. NPS scores and response counts shown on the dashboard are lower than actual. The workspace owner may underreport engagement metrics. Additionally, DynamoDB throttling causes Lambda to retry, increasing Kinesis iterator age (see EC-ANALYTICS-002 interaction). |
| **Detection** | DynamoDB CloudWatch metric `ConsumedWriteCapacityUnits` per partition triggers alarm `SurveyPlatform-DynamoDBHotPartition` when a single partition's WCU exceeds 80% of the per-partition limit for 2 consecutive 1-minute periods. DynamoDB `SystemErrors` and `ThrottledRequests` metrics spike. Lambda `Errors` metric on `kinesis-analytics-processor` increases. |
| **Mitigation / Recovery** | 1. Immediately switch the affected survey's analytics writes to a write-sharding pattern by adding a random shard suffix to the partition key: instead of `PK = survey_id`, use `PK = survey_id#shard_{random.randint(0, 9)}` for the 10-shard pattern. 2. Update the read aggregation to scatter-gather across all 10 shards. 3. For the already-dropped writes: replay Kinesis events for the affected survey from the time of first throttle: `aws kinesis get-shard-iterator --stream-name survey-platform-responses --shard-id shardId-000000000000 --shard-iterator-type AT_TIMESTAMP --timestamp <throttle_start_time>`. 4. Reconcile analytics totals against PostgreSQL response count: `SELECT COUNT(*) FROM responses WHERE survey_id = 'abc123'` vs. DynamoDB aggregated count. |
| **Prevention** | (1) **Key design:** Use composite partition key `survey_id#date_hour` (e.g., `abc123#2024-05-01-14`) — distributes writes across 24 hourly partitions per day. Aggregation queries scan all hourly partitions and sum. (2) **Write sharding:** For surveys flagged as potentially viral (> 1,000 responses in first 10 minutes), automatically apply 10-way write sharding on the DynamoDB partition key. (3) **DynamoDB Accelerator (DAX):** Place DAX in front of DynamoDB for read-heavy analytics queries, reducing WCU consumption for dashboard reads. (4) **Adaptive capacity:** Enable DynamoDB adaptive capacity (on-demand mode) which automatically redistributes capacity across partitions in response to traffic patterns — provides some protection against moderate hot partitions. |

---

### EC-ANALYTICS-006: AWS Comprehend Throttle (500 TPS Limit for Sentiment Analysis)

| Field | Details |
|-------|---------|
| **Failure Mode** | The analytics pipeline uses AWS Comprehend `DetectSentiment` API to analyse open-text responses in real time as they are submitted. During a high-traffic period, 800 responses per second arrive, each containing one open-text answer. The Comprehend API call rate exceeds the default quota of 500 TPS per account per region. AWS Comprehend returns `ThrottlingException`. The Lambda function does not implement a back-off strategy and retries immediately, amplifying the throttle and causing cascading Lambda timeouts. Sentiment analysis results are missing for 40% of responses during the spike. |
| **Impact** | Medium. Sentiment scores are missing for a significant portion of responses. The sentiment trend chart on the analytics dashboard shows a gap. The workspace owner notices missing sentiment data but can still use other analytics (NPS, completion rates). No response data loss — sentiment is a derived enrichment, not primary data. However, missing sentiment data cannot be retroactively filled if the responses are anonymised before re-processing. |
| **Detection** | AWS Comprehend `ThrottlingException` count > 0 triggers CloudWatch alarm `SurveyPlatform-ComprehendThrottle`. Lambda `Errors` metric on `sentiment-analysis-processor` spikes. A `SentimentEnrichmentGapRate` custom metric (percentage of responses without sentiment score) exceeds 5% in a 5-minute window. |
| **Mitigation / Recovery** | 1. Request Comprehend quota increase via AWS Service Quotas console: target 2,000 TPS per region. 2. Enable exponential backoff with jitter in the sentiment Lambda: use `@retry(stop=stop_after_attempt(5), wait=wait_random_exponential(min=1, max=60))`. 3. Process missing sentiment scores retroactively from PostgreSQL: `SELECT id, open_text_answer FROM response_answers WHERE sentiment_score IS NULL AND question_type = 'open_text' ORDER BY created_at DESC LIMIT 10000` — feed these into a batch Comprehend `BatchDetectSentiment` job (batch size 25 per API call). 4. Batch Comprehend API is billed per unit and not subject to the same 500 TPS limit — use for backfill. |
| **Prevention** | (1) **Async enrichment:** Decouple sentiment analysis from the real-time Kinesis pipeline. Sentiment scoring is a non-critical enrichment — process it asynchronously via a Celery task queue with rate limiting: `celery -Q sentiment --concurrency=10 -Ofair`. (2) **Rate limiting:** Implement a token bucket rate limiter in the sentiment processor: max 400 Comprehend API calls per second (80% of quota), using `aiolimiter` for async rate limiting. (3) **Batch API:** Use `BatchDetectSentiment` (25 texts per call, 10 TPS limit but processes 250 texts/call) instead of individual `DetectSentiment` calls — more efficient for bulk processing. (4) **Quota increase:** Pre-request Comprehend quota increase to 2,000 TPS as part of production launch preparation. |

---

### EC-ANALYTICS-007: Scheduled Report Email Delivery Failure (SendGrid 5xx / Bounce)

| Field | Details |
|-------|---------|
| **Failure Mode** | A workspace owner has configured a weekly NPS digest report to be sent every Monday at 09:00 UTC to their team's email addresses. The Celery beat scheduler triggers the `send_scheduled_report` task on Monday. The task generates the PDF report, uploads it to S3, and calls the SendGrid `POST /mail/send` API. SendGrid returns HTTP 500 (Internal Server Error). The Celery task has no retry logic for transient email delivery failures — it marks the task as `SUCCEEDED` (because no exception was raised by the fire-and-forget email function) and the email is never delivered. The workspace owner doesn't receive the report and doesn't notice for a week. |
| **Impact** | Medium. The scheduled report is silently dropped. Workspace owners who rely on automated reports for weekly standups or board meetings miss their data. No data is lost (the report was generated and stored in S3), but the delivery failure is invisible. If multiple teams are affected, customer support tickets increase. |
| **Detection** | The email delivery function must check SendGrid's response status and raise an exception on non-2xx: `if response.status_code >= 400: raise EmailDeliveryError(...)`. A `ScheduledReportDeliveryFailure` CloudWatch metric is emitted on delivery failure. A separate `ScheduledReportDeliveryReceipt` metric is emitted on success — alerts fire when the success rate for a scheduled window drops below 90%. SendGrid webhook events (delivered, bounce, dropped) are consumed by an EventBridge integration and stored in `email_delivery_events`. |
| **Mitigation / Recovery** | 1. Identify failed delivery reports: `SELECT * FROM scheduled_report_runs WHERE status = 'FAILED' OR (status = 'SENT' AND id NOT IN (SELECT report_run_id FROM email_delivery_events WHERE event_type = 'delivered'))`. 2. For each failed report, re-trigger delivery from the stored S3 pre-signed URL: `send_scheduled_report.apply_async(kwargs={'report_run_id': rid, 're_deliver': True})`. 3. Check SendGrid account status for domain reputation issues: `GET https://api.sendgrid.com/v3/ips/pools` and review bounce rates. 4. If SendGrid is experiencing an outage, switch to the backup email provider (Amazon SES) by updating the `EMAIL_PROVIDER` environment variable and redeploying. |
| **Prevention** | (1) **Retry logic:** Celery task uses `autoretry_for = (EmailDeliveryError,)` with `max_retries = 5` and exponential backoff (`default_retry_delay = 300` seconds). (2) **Webhook confirmation:** Store SendGrid delivery webhook events in `email_delivery_events`. A reconciliation job runs hourly to flag any scheduled reports sent > 2 hours ago without a `delivered` webhook event. (3) **Dual provider:** Maintain Amazon SES as a fallback email provider. The `EmailRouter` class tries SendGrid first and falls back to SES after 2 consecutive failures. (4) **Delivery monitoring:** Subscribe to SendGrid's IP/domain reputation alerts to proactively detect deliverability issues before they affect report delivery. |

---

### EC-ANALYTICS-008: Analytics Cache Poisoning (Stale NPS Score Served from Redis for 1 Hour)

| Field | Details |
|-------|---------|
| **Failure Mode** | The analytics API caches NPS scores in Redis with a 1-hour TTL: `redis.setex(f"nps:{survey_id}", 3600, nps_score)`. A bug in the cache invalidation logic means that when a batch of 500 new responses is imported via the bulk import API, the cache invalidation call (`redis.delete(f"nps:{survey_id}")`) is skipped — the code path for bulk import does not call `invalidate_analytics_cache()`. For the next 1 hour, the dashboard displays the pre-import NPS score. If the NPS before import was 45 and after import is 23 (a significant drop), decision-makers are shown the inflated score. |
| **Impact** | High. Business decisions are made based on analytically incorrect data for up to 1 hour. The workspace owner may send out a celebratory message about a high NPS before the real data surfaces. Trust in the platform's analytics accuracy is eroded when the score suddenly drops. This is particularly damaging for enterprise customers using NPS in performance reviews or investor reporting. |
| **Detection** | A `AnalyticsCacheStaleness` check runs every 15 minutes as a Lambda function: it independently computes NPS from PostgreSQL and compares to the Redis-cached value. If the discrepancy is > 5 NPS points, it emits `AnalyticsCacheStalenessDetected` CloudWatch metric and triggers the alarm `SurveyPlatform-AnalyticsCachePoisoning`. Additionally, every analytics API response includes an `X-Cache-Computed-At` header — the dashboard warns users when `computed_at < NOW() - 30 minutes`. |
| **Mitigation / Recovery** | 1. Immediately flush the stale cache for all surveys affected by recent bulk imports: `redis.delete(f"nps:{survey_id}")` for all surveys that received bulk imports in the last 2 hours. 2. Run a cache warmup job that re-computes NPS from PostgreSQL and populates Redis: `recalculate_and_cache_nps.apply_async(kwargs={'survey_ids': affected_ids})`. 3. Alert the workspace owner: "NPS scores were recently updated following a data import. Previous figures may have been out of date." 4. Audit all cache invalidation paths to identify other missing invalidation calls. |
| **Prevention** | (1) **Code-level:** Implement a centralised `CacheInvalidationService` that is the single point of truth for all cache invalidation. Every function that modifies response data must call `cache_invalidation_service.invalidate_survey_analytics(survey_id)` — making it easy to audit that all write paths call the same invalidation function. (2) **Cache TTL:** Reduce cache TTL from 1 hour to 5 minutes for the NPS metric. The computation cost for NPS from PostgreSQL with a covering index is < 100ms even for 100K responses. (3) **Write-through caching:** On every new response write, immediately update the Redis NPS cache incrementally: `redis.hincrby(f"nps_counters:{survey_id}", "promoters", 1)` — eliminates staleness entirely for the promoter/detractor/passive counts. NPS is then computed on read from the in-Redis counters. (4) **Testing:** Integration test that bulk import triggers cache invalidation: assert `redis.get(f"nps:{survey_id}")` is None after bulk import API call. |

---

## Analytics Data Quality Rules

The following data quality rules are enforced by the analytics pipeline before any metric is stored or
served. Violations emit `DataQualityViolation` CloudWatch events with a `rule_id` dimension.

| Rule ID | Rule Description | Enforcement Point | Action on Violation |
|---------|-----------------|-------------------|---------------------|
| DQ-001 | NPS score must be in range [−100, 100] | `NPSCalculator.compute()` | Raise `InvalidNPSScore`, do not cache |
| DQ-002 | Response count in analytics must not exceed PostgreSQL response count | Cache staleness check Lambda | Invalidate cache, recompute |
| DQ-003 | Completion rate must be in range [0%, 100%] | `CompletionRateCalculator` | Clamp to valid range, log warning |
| DQ-004 | Sentiment score distribution must sum to ≤ response count | `SentimentAggregator` | Log discrepancy, use PostgreSQL count as denominator |
| DQ-005 | Cross-tab cell counts must sum to total response count | `CrossTabBuilder` | Reject cross-tab if sum mismatch > 1% |
| DQ-006 | Average score for rating questions must be in [min_rating, max_rating] | `RatingAggregator` | Reject if out of range, flag question for review |
| DQ-007 | Analytics cache age must not exceed 2× configured TTL | Cache staleness check Lambda | Force refresh, emit `CacheOverAged` metric |
| DQ-008 | Kinesis event count must match PostgreSQL insert count (within 0.1%) | Hourly reconciliation Lambda | Trigger Kinesis replay for gap period |

---

## Operational Policy Addendum

### 1. Response Data Privacy Policies

Analytics aggregations are computed from response data and are presented in aggregate form only.
Individual responses are never exposed through the analytics API. NPS, CSAT, and completion rate
metrics are non-personal aggregate statistics and do not constitute personal data under GDPR.

Open-text sentiment analysis: When AWS Comprehend processes open-text responses, the text is sent to
the AWS API. The AWS Data Processing Addendum (DPA) covers this processing. Workspaces may disable
sentiment analysis for surveys containing sensitive PII in open-text fields (e.g., medical feedback).
When disabled, open-text responses are stored but not sent to Comprehend.

Cross-tabulation reports: The platform enforces k-anonymity (k≥5) on all cross-tab cells — cells with
fewer than 5 responses display "<5" rather than the exact count, preventing re-identification of
individual respondents (see EC-SEC-008 for details).

### 2. Survey Distribution Policies

Analytics reports distributed via scheduled email (EC-ANALYTICS-007) are internal operational emails
sent to authenticated workspace members. They are not marketing emails and are not subject to CAN-SPAM
opt-out requirements. However, workspace members can disable personal analytics email subscriptions
via their profile preferences.

Report pre-signed URLs in S3 have a 72-hour expiry. After expiry, the workspace owner must regenerate
the report from the analytics dashboard. This prevents indefinite access to sensitive aggregate data
via a stale link.

### 3. Analytics and Retention Policies

**Aggregate metric retention:** Pre-computed analytics aggregates in DynamoDB (NPS history, completion
rate trends, sentiment trends) are retained indefinitely — they are non-personal derived data.

**Raw event retention:** Kinesis events are retained for 7 days (Kinesis default). The Lambda analytics
processor must consume all events within this window. Events older than 7 days are not accessible for
replay; use the PostgreSQL `responses` table as the source of truth for re-computation.

**Report file retention:** Generated XLSX/PDF reports in S3 are retained for:
- Free tier: 30 days
- Business tier: 180 days
- Enterprise tier: 365 days (configurable)

After the retention period, reports are deleted by S3 lifecycle policy. Workspace owners are warned
7 days before report deletion via email.

**Anonymisation:** Aggregate analytics are never anonymised (they are already non-personal). The raw
response data underpinning the analytics is anonymised per the response retention policy.

### 4. System Availability Policies

**Analytics dashboard SLA:** 99.5% monthly uptime (read path). Dashboard reads serve from Redis cache
— even during DB maintenance windows, cached analytics remain available.

**Report generation SLA:** Scheduled reports are delivered within ±2 hours of the scheduled time.
On-demand reports for datasets < 100K responses are generated within 60 seconds; > 100K responses
within 30 minutes.

**RTO:** Analytics service: 30 minutes. Stale cached data continues to serve during a short outage.

**RPO:** Kinesis events have a 7-day replay window. PostgreSQL PITR provides a 5-minute RPO for the
raw response data used to recompute analytics.
