# Edge Cases — Operations

> **Scope:** Covers queue backlogs, infrastructure outages, certificate worker loops, CDN failures, bulk import lock contention, crashed grading batches, database failover, at-least-once delivery duplicates, cascading index rebuilds, and stale backup recovery data.

---

## 1. Progress Event Queue Backlog Grows Beyond SLO Threshold

**Failure Mode:** During peak hours (Monday 9 AM), progress event throughput reaches 60,000 events/minute against a worker capacity of 20,000 events/minute. Queue depth reaches 200,000 events; events are processed 10+ minutes late. Completion evaluations run on stale data; learners experience delayed module unlocks and dashboard updates.

**Impact:** Up to 15-minute delay in completion evaluation; learners who finish a course cannot access the next module; real-time dashboards show stale data; p95 SLO of 60 s is breached. Estimated 500+ support contacts per peak hour during the incident.

**Detection:**
- Alert: `progress_event_queue.consumer_lag > 5000 messages` (sustained for 2 minutes).
- Alert: `progress_event_processing_latency_p95 > 120 seconds`.
- Dashboard: queue depth graphed against worker count for real-time visibility.

**Mitigation/Recovery:**
- Autoscaling policy: add 1 worker pod per 2,000 messages of lag above 1,000; scale down when lag < 500 for 5 consecutive minutes.
- Shed non-critical events (e.g., video heartbeats) when lag > 10,000; process only completion and assessment events.
- Implement priority lanes: completion events use a high-priority queue; telemetry events use a best-effort queue.
- Post-incident: run lag reconciliation to catch any events that were dropped during shedding.

---

## 2. Search/Analytics Cluster Outage Makes Catalog and Reports Unavailable

**Failure Mode:** The Elasticsearch/OpenSearch cluster becomes unavailable (OOM crash, disk full, network partition). The catalog search API and all analytics dashboards return `503 Service Unavailable`. Learners cannot search for courses; admins cannot view reports.

**Impact:** Catalog search is completely broken for all tenants; real-time and historical reports are unavailable; learner self-service enrollment is impaired. If the outage exceeds the SLA, compensatory credits may be owed to enterprise customers.

**Detection:**
- Synthetic monitor: issue a search query every 30 s; alert immediately if it fails.
- Elasticsearch cluster health: alert on `status = RED` or `status = YELLOW` for >2 minutes.
- Alert on `search_request_error_rate > 5%` over a 1-minute window.

**Mitigation/Recovery:**
- Catalog search falls back to a PostgreSQL full-text search (`tsvector`) when Elasticsearch is unavailable; results are less sophisticated but functional.
- Analytics dashboards show a "Reports temporarily unavailable" banner with estimated restoration time; do not show an empty page.
- Runbook: cluster recovery steps documented and tested quarterly; auto-restart script triggered by health monitor.
- Elasticsearch snapshots taken every 6 hours to S3; restore from snapshot if index data is corrupted or lost.

---

## 3. Certificate Issuance Worker Stuck in Retry Loop (Duplicate Records)

**Failure Mode:** The certificate issuance worker picks up a job, issues the certificate (DB write succeeds), then fails to acknowledge the queue message (network timeout). The message is re-delivered after the visibility timeout. The worker issues a second certificate for the same learner+course, creating duplicate records.

**Impact:** Learner has two certificate records with different IDs but the same content; certificate verification may return inconsistent results; certificate revocation becomes ambiguous (which record to revoke?).

**Detection:**
- Alert on `duplicate_certificate_detected`: `SELECT learner_id, course_id, COUNT(*) FROM certificates GROUP BY 1,2 HAVING COUNT(*) > 1`.
- Alert on `certificate_issuance_worker.retry_count > 3` for the same job.
- Monitor `certificate_issued_per_minute`; a spike may indicate duplicate issuance.

**Mitigation/Recovery:**
- Idempotency: before issuing a certificate, check for an existing record with `(learner_id, course_id, completion_id)`; return existing ID if found.
- Database unique constraint: `UNIQUE (learner_id, course_id)` on `certificates` table; second insert returns `409` which the worker treats as success.
- Dead-letter queue: after 5 retries, route to DLQ; on-call engineer reviews and manually resolves.
- Cleanup job: periodically find and tombstone duplicate certificate records, preserving the earliest.

---

## 4. Media CDN Outage Makes All Video Lessons Unplayable

**Failure Mode:** The CDN provider (e.g., CloudFront, Fastly) experiences a global outage. All signed URLs for video content return `503` or time out. Every video lesson across all tenants shows a broken player. The outage lasts 45 minutes.

**Impact:** 100% of video-based lessons are unplayable for all learners globally; live training sessions that depend on CDN-hosted content are blocked; instructor-led sessions using screen share of hosted video fail.

**Detection:**
- Synthetic monitor: attempt to load a test video segment from CDN every 60 s; alert immediately on failure.
- Monitor `video_play_error_rate`; alert if > 2% over a 1-minute window (baseline: <0.1%).
- CDN status page integration: subscribe to CDN provider's status feed and surface to ops dashboard.

**Mitigation/Recovery:**
- Maintain a secondary CDN provider (multi-CDN failover); route traffic to secondary when primary error rate exceeds 5%.
- Origin fallback: serve video directly from origin storage (S3) with reduced capacity; apply aggressive rate limiting to prevent origin overload.
- Learner-facing status page updated within 5 minutes of CDN outage detection: "Video content is temporarily unavailable due to a CDN provider issue. We expect restoration by [ETA]."
- Instructors receive immediate email/Slack alert with incident status to adjust live session plans.

---

## 5. Bulk Enrollment Import Causes Database Lock Contention

**Failure Mode:** An admin imports 50,000 learner enrollments via the bulk import endpoint. The import job runs a tight loop of `INSERT INTO enrollments` statements within a single long-running transaction. This holds row-level locks on the `enrollments` table for 8+ minutes, blocking other enrollment operations and causing timeouts for learners trying to enroll via the UI.

**Impact:** All learner-facing enrollment requests time out for 8 minutes; enrollment failures during this window; degraded course launch experience. Concurrent admin operations on the same tenant also fail.

**Detection:**
- Alert on `pg_locks` wait times exceeding 30 s on `enrollments` table.
- Monitor API p99 latency on enrollment endpoints; alert if > 5 s (baseline: <500 ms).
- Slow query log: alert on any transaction running for >60 s on `enrollments`.

**Mitigation/Recovery:**
- Bulk import processes rows in micro-batches of 500 within separate, short-lived transactions; pauses 100 ms between batches to release locks.
- Use `INSERT ... ON CONFLICT DO NOTHING` for idempotent upserts, reducing transaction time.
- Separate the bulk import DB connection from the learner-facing API connection pool using read/write splitting or a dedicated bulk-operations replica.
- Schedule large bulk imports during off-peak hours (e.g., 2–4 AM local tenant time) with admin confirmation.

---

## 6. Grading Queue Processor Crashes Mid-Batch

**Failure Mode:** The grading queue processor picks up a batch of 200 submissions for regrade. It processes 80 submissions, writes the new scores, then crashes (OOM, unhandled exception). The remaining 120 submissions are still in `state = GRADING_IN_PROGRESS` and are never re-queued because the crash prevents the ack/nack handshake.

**Impact:** 120 submissions are stuck in `GRADING_IN_PROGRESS` indefinitely; learners cannot see their grades; completion evaluations cannot proceed for these learners.

**Detection:**
- Alert on `submission.state = GRADING_IN_PROGRESS` for more than 30 minutes without a state transition.
- Monitor `grading_worker.heartbeat`; alert if heartbeat stops for > 60 s.
- Alert on any grading worker process exit with non-zero code.

**Mitigation/Recovery:**
- Heartbeat timeout: each submission claimed by a worker has a `claimed_until` timestamp; another worker can reclaim submissions past this timestamp.
- Worker supervisor: Kubernetes restarts the crashed worker pod within 30 s; the new worker reclaims in-progress submissions.
- Grading operations are idempotent: re-processing an already-graded submission detects the existing score and skips re-grading.
- Alert on-call if >10 submissions are stuck; runbook provides SQL to manually reset `state = QUEUED` for the affected submissions.

---

## 7. PostgreSQL Primary Failover Causes Brief Write Unavailability

**Failure Mode:** The PostgreSQL primary node fails (hardware fault). The cluster's automatic failover promotes the standby to primary in approximately 20–30 seconds. During this window, all write operations fail with `connection refused` or `read-only transaction` errors. The application does not detect the failover immediately and continues routing writes to the old primary.

**Impact:** 20–30 seconds of write downtime; progress events, enrollment requests, and grade writes are lost or rejected; users see 503 errors. With automatic reconnect, recovery is within 60 s.

**Detection:**
- Alert on `database.write_error_rate > 1%` over a 30-second window.
- Application health check: test write availability every 10 s; alert on failure.
- Database cluster monitoring: alert on primary failover event immediately.

**Mitigation/Recovery:**
- Application uses a connection pool with automatic failover: when the primary is unavailable, the pool detects the failover (via PgBouncer or AWS RDS proxy) and re-routes within 10–15 s.
- Write failures during the failover window are queued in a local buffer (for idempotent operations) or returned to the client as `503 Retry-After: 30`.
- Progress events use an event queue (Kafka/SQS) as the primary write path; the queue absorbs the 30-second outage and workers replay on recovery.
- Failover runbook: documented and tested quarterly; RTO = 60 s; RPO = 0 (synchronous replication).

---

## 8. Background Worker Picks Up a Job Twice (At-Least-Once Delivery)

**Failure Mode:** A job is dequeued by Worker A. Worker A processes the job (e.g., sends a certificate email) but takes 35 seconds — longer than the visibility timeout (30 s). The queue re-delivers the message to Worker B, which also processes it. Both workers complete the job; the learner receives two certificate emails and two certificate records are created.

**Impact:** Duplicate certificates, duplicate notifications, duplicated side effects (e.g., two webhook calls to external HR systems). Cleanup requires identifying and tombstoning the duplicate.

**Detection:**
- Monitor `job_processed_duplicate` events; alert on any occurrence.
- Track `job_execution_duration_p99` per job type; alert if p99 approaches 80% of the visibility timeout.

**Mitigation/Recovery:**
- All job handlers are idempotent: use a `job_id` as an idempotency key; check a `processed_jobs` table before executing; insert after execution.
- Set visibility timeout to `job_p99_duration * 3`; extend the timeout (heartbeat) for long-running jobs.
- Use distributed locking (Redis SETNX on `job_id`) to prevent two workers from processing the same job simultaneously; lock TTL = visibility timeout.

---

## 9. Course Publish Triggers Cascading Index Rebuild Causing Slowdown

**Failure Mode:** A course publish event triggers: (1) a search index rebuild for the course, (2) a prerequisite graph recalculation for 1,200 dependent courses, (3) a progress evaluation re-run for 8,000 enrolled learners, and (4) a cache invalidation sweep. All four operations fan out simultaneously and saturate the database CPU at 95%, causing a 3-minute degradation across all tenants.

**Impact:** All tenants experience degraded API response times (3–10 s instead of <500 ms) for 3 minutes; some requests time out; learner-facing errors appear unrelated to the publish action.

**Detection:**
- Alert on `database.cpu_utilization > 80%` sustained for >60 seconds.
- Trace `course_publish` events using distributed tracing (e.g., Jaeger); measure fan-out depth and total job count triggered.
- Alert on `api_response_time_p99 > 2000 ms` sustained for >30 seconds.

**Mitigation/Recovery:**
- Introduce a rate-limited publish pipeline: downstream jobs are enqueued but processed at a controlled rate (e.g., max 500 evaluations/s).
- Stagger the four post-publish operations with delays and priority: search index first, then cache invalidation, then prerequisite recalc, then progress re-evaluation.
- Circuit breaker: if database CPU > 70%, defer non-critical post-publish jobs to an off-peak queue.

---

## 10. Backup Restoration Test Reveals Progress Records Are 6 Hours Stale

**Failure Mode:** During a quarterly disaster recovery drill, the team restores from the most recent backup and discovers that the `progress_records` table backup is 6 hours old. The backup job silently failed at 2 AM due to insufficient disk space on the backup server; the failure was not alerted on. The actual RPO (Recovery Point Objective) is 6 h instead of the required 30 minutes.

**Impact:** In a real disaster scenario, 6 hours of learner progress data would be lost; completion evaluations must be re-run; certificates issued in that window would need revalidation. SLA breach; enterprise customer contract penalties may apply.

**Detection:**
- Backup job completion must emit a `backup_completed` event with `backup_age_seconds`; alert immediately on job failure.
- Alert if `backup_completed` event is not received within `backup_interval * 1.5` (e.g., alert if no backup within 45 minutes for a 30-minute schedule).
- Weekly automated restore test: restore to a test environment, compare `MAX(updated_at)` in restored data against expected timestamp; alert if gap > RPO.

**Mitigation/Recovery:**
- Progress events are written to both the primary DB and an event log (Kafka with 7-day retention); in a recovery scenario, replay events from the log to fill the gap between the backup timestamp and the incident.
- Backup storage target has pre-allocated reserved space to prevent disk-full failures.
- Backup monitoring dashboard: show last successful backup timestamp, backup size, and restoration test status for every database per tenant.
- Runbook: quarterly DR drill is mandatory; results are reviewed by the engineering lead and filed in the incident register.
| Search or analytics cluster outage occurs | Reporting and discovery degrade | Fallback to core transactional reads for critical flows |
| Certificate issuance worker retries repeatedly | Duplicate certificates or confusion | Use idempotent issuance keys and issuance-state guards |
| Media CDN outage affects lessons | Learner experience collapses | Provide degraded mode messaging and retry policies |
| Tenant bulk import floods downstream systems | Operational instability | Stage imports with backpressure and observable job control |


## Implementation Details: Incident Response for LMS

- Define runbooks for grading backlog, projection lag, notification outage, and certificate issuance delays.
- For learner-impacting incidents, publish status update cadence and expected recovery timelines.
- Post-incident action items must include detection, automation, and documentation updates.
