# Edge Cases — Operations

Failure modes, impact assessments, and mitigation strategies for infrastructure, deployment, data integrity, and operational processes.

Edge case IDs in this file are permanent: **EC-OPS-001 through EC-OPS-008**.

---

## EC-OPS-001 — Zero-Downtime Deployment Fails Mid-Rollout

| Field | Detail |
|---|---|
| **Failure Mode** | A new ECS task definition is deployed using a rolling update strategy. The new version introduces a bug (e.g., a missing Django migration) that causes 500 errors. The rolling update has already replaced 50% of old tasks with new ones. |
| **Impact** | 50% of API requests succeed (served by remaining old tasks) and 50% fail (served by new buggy tasks). CloudWatch shows 50% 5xx error rate. User experience is degraded. |
| **Detection** | CloudWatch Alarm: API 5xx error rate > 1% for 2 consecutive minutes. ALB target health checks failing for new task instances. |
| **Mitigation / Recovery** | (1) CodeDeploy deployment action: automatic rollback is configured to trigger when the 5xx alarm fires. Rollback restores the previous task definition within 2–5 minutes. (2) If automatic rollback fails, ops engineer manually runs `aws ecs update-service --task-definition <previous-revision>`. (3) Postmortem conducted; missing migration added before re-deploy. |
| **Prevention** | Pre-deployment checklist: run `python manage.py migrate --check` in the CI pipeline — fails the build if there are unapplied migrations. Smoke tests run against the staging environment post-deploy before production promotion. Staging environment mirrors production schema. |

---

## EC-OPS-002 — Database Migration Fails on Production Data Volume

| Field | Detail |
|---|---|
| **Failure Mode** | A Django migration adds a non-nullable column with a default value to the `students` table (2.8 million rows). The migration acquires an exclusive table lock and takes 45 minutes to complete, blocking all reads and writes to the students table during that time. |
| **Impact** | The entire EMIS API is unavailable for any student-related operations for 45 minutes. Enrollment, grade access, and student portal operations all fail. |
| **Detection** | Database lock monitoring: CloudWatch metric `RDS.DatabaseConnections` spikes and then drops as connections queue. Migration duration alert (> 60 seconds). |
| **Mitigation / Recovery** | (1) If migration is running and causing lock contention: connect to the DB and `SELECT * FROM pg_stat_activity WHERE wait_event_type = 'Lock'` to assess. (2) If necessary: cancel the migration with `SELECT pg_cancel_backend(pid)`, restoring table access. (3) Reschedule migration using a safer pattern. |
| **Prevention** | Large table migrations follow the "expand-contract" pattern: (a) Add column as nullable, (b) backfill in batches of 10,000 rows, (c) add NOT NULL constraint only after backfill. For PostgreSQL 11+, `ADD COLUMN ... DEFAULT <constant>` is instant and does not require a table rewrite. Team uses `django-zero-downtime-migrations` library. All migrations are tested against a production-scale dataset in the staging environment before production deployment. |

---

## EC-OPS-003 — Celery Beat Scheduler Crash Causing Missed Periodic Tasks

| Field | Detail |
|---|---|
| **Failure Mode** | The single Celery Beat task (ECS desired count = 1) crashes and ECS takes 3 minutes to replace it. During those 3 minutes, a scheduled periodic task (fee overdue reminder emails, scheduled at exact minute) fires from no running Beat instance. |
| **Impact** | The periodic task is missed entirely. Overdue fee reminders are not sent on schedule. Students do not receive the 7-day overdue notice. Academic calendar jobs (e.g., opening/closing enrollment window) may be delayed. |
| **Detection** | ECS service event: task stopped unexpectedly. CloudWatch Alarm: Beat task count < 1 for > 2 minutes. Celery `celery-redbeat` scheduler logs last-execution timestamps — a gap in execution is visible. |
| **Mitigation / Recovery** | (1) ECS replaces the Beat task automatically (desired count = 1). (2) A "catch-up" mechanism is implemented for idempotent tasks: each periodic task checks its last-execution timestamp in Redis and re-runs if the gap exceeds 2× the expected interval. (3) For critical calendar tasks (opening enrollment window), an ECS EventBridge Rule provides a redundant trigger. |
| **Prevention** | Celery Beat uses `celery-redbeat` (Redis-backed dynamic scheduler with lock) to ensure only one Beat instance is active across potential replica count changes. ECS service restart policy is set to immediate replacement on task failure. |

---

## EC-OPS-004 — Disk Space Exhaustion on Database Server

| Field | Detail |
|---|---|
| **Failure Mode** | PostgreSQL WAL logs (write-ahead logs) grow during a high-write period (bulk grade import, semester-end operations). The RDS storage allocation is fully consumed. PostgreSQL becomes read-only to prevent data corruption. |
| **Impact** | All write operations to the database fail with `ERROR: could not extend file: No space left on device`. Enrollment, grade submission, payment recording, and all other write operations are unavailable. |
| **Detection** | CloudWatch Alarm: `RDS.FreeStorageSpace < 10 GB`. Alert at < 20 GB (warning) and < 10 GB (critical) thresholds. |
| **Mitigation / Recovery** | (1) Emergency: `aws rds modify-db-instance --db-instance-identifier emis-prod --allocated-storage <new_size> --apply-immediately` — storage can be increased without downtime on gp3 RDS. (2) If autoscaling is enabled (max storage configured), this happens automatically. (3) If WAL accumulation is the cause: identify and remove large WAL retention requirements (e.g., long-running replication slots). |
| **Prevention** | RDS storage autoscaling is enabled with a maximum cap of 2 TB and a scale-up threshold of 10% free space. Regular cleanup job: archive and compress old AuditLog and WebhookEventLog records to S3 at 90 days. CloudWatch alarm at < 20 GB for early warning. |

---

## EC-OPS-005 — Redis Memory Exhaustion Causing Cache Eviction

| Field | Detail |
|---|---|
| **Failure Mode** | During a high-traffic period (registration window), the Redis instance runs out of memory. The eviction policy (`allkeys-lru`) begins evicting Celery task messages from the broker queues (stored in Redis) to free space, discarding queued notifications and scheduled tasks. |
| **Impact** | Celery tasks (notifications, report generation) are silently dropped. Students do not receive enrollment confirmations. Scheduled tasks are lost. |
| **Detection** | CloudWatch metric: `ElastiCache.FreeableMemory < 200 MB`. Alert at < 500 MB. Custom metric: Celery queue depth sudden drop without corresponding task completion. |
| **Mitigation / Recovery** | (1) Alert triggers ops engineer to review memory usage. (2) Immediate: scale up ElastiCache node type (online vertical scaling) or add a read replica. (3) Check for memory leaks: large keys (`SCAN` + `DEBUG OBJECT`), unexpired session keys, or runaway Celery task result accumulation. (4) Use Domain Event outbox (PostgreSQL) as the reconciliation source for lost tasks. |
| **Prevention** | Redis is configured with `maxmemory-policy noeviction` for the Celery broker keys namespace, and `allkeys-lru` only for the cache namespace — using separate logical databases (DB 0 for broker, DB 1 for cache). CloudWatch alarm at 80% memory utilisation. Celery results backend uses `CELERY_RESULT_EXPIRES = 3600` (1 hour) to auto-expire result keys. |

---

## EC-OPS-006 — Secrets Rotation Causing Brief Service Outage

| Field | Detail |
|---|---|
| **Failure Mode** | AWS Secrets Manager automatically rotates the RDS database password. The Lambda rotation function updates the secret. However, running ECS tasks still have the old password cached in their process memory (loaded at startup). New connections fail with authentication errors until the tasks are restarted. |
| **Impact** | PgBouncer connection pool fails to establish new database connections. Existing connections remain valid until they expire or the pool is reset. New requests requiring fresh DB connections fail. Gradual degradation over 5–30 minutes as existing connections close. |
| **Detection** | CloudWatch Alarm: API 5xx rate increase correlated with Secrets Manager rotation event. PgBouncer logs: `password authentication failed for user emis_app`. |
| **Mitigation / Recovery** | (1) ECS tasks are deployed with a `SECRETS_MANAGER_CACHE_TTL = 3600s` — tasks re-fetch secrets from Secrets Manager every hour. Tasks also re-fetch on startup. (2) Rotation Lambda is modified to trigger an ECS service forced redeployment after updating the secret, causing tasks to restart with the new credential. (3) PgBouncer sidecar is configured to reconnect on authentication failure rather than marking the pool broken. |
| **Prevention** | ECS task definition uses Secrets Manager reference (`secrets` field in task definition), which automatically injects the latest secret value at task start. Rotation is scheduled at 3 AM during non-peak hours. Rotation alert notifies ops team. |

---

## EC-OPS-007 — S3 Pre-signed URL Expiry During Multi-Part Download

| Field | Detail |
|---|---|
| **Failure Mode** | A student starts downloading a large video file from S3 via a 30-minute pre-signed URL. The download is slow (large file over a slow connection). The pre-signed URL expires mid-download, causing the download to fail and the file to be corrupted/incomplete. |
| **Impact** | Student receives an incomplete file. Frustrated user experience. Re-downloading requires generating a new pre-signed URL. |
| **Detection** | CloudFront/S3 returns 403 `Request has expired` during the download. The file management API returns an error when the student attempts to regenerate the URL (rate-limited). |
| **Mitigation / Recovery** | (1) LMS media is served via CloudFront with signed cookies (not per-object signed URLs). Signed cookies allow the student to access any object in their permitted key prefix for the duration of the session. (2) For document downloads (shorter files), a 2-hour pre-signed URL window is used instead of 30 minutes. (3) On download failure, the portal's download manager automatically generates a new URL and resumes the download from the last byte position using HTTP Range requests. |
| **Prevention** | Large files are delivered via CloudFront signed cookies with a 4-hour validity. The portal uses `multipart-download-manager.js` to resume interrupted downloads. S3 objects support `Accept-Ranges: bytes`, enabling byte-range resumption. |

---

## EC-OPS-008 — Stale Feature Flag State After Deployment

| Field | Detail |
|---|---|
| **Failure Mode** | A feature flag (`ENABLE_NEW_ENROLLMENT_UI`) is enabled in the staging environment for testing. During deployment to production, the feature flag configuration is accidentally promoted to production (it is stored in the same environment config file). The new enrollment UI is exposed to all production students before it has been tested at scale. |
| **Impact** | All students see the new (potentially buggy) enrollment UI. If the new UI has a critical bug (e.g., the Add-Drop API call uses the wrong endpoint), all enrollments during registration window fail. |
| **Detection** | Error monitoring (Sentry/CloudWatch): spike in UI errors after deployment. User support tickets spike. |
| **Mitigation / Recovery** | (1) Feature flag is turned off remotely via the feature flag service (LaunchDarkly or custom flag store in Redis/DB) without a redeployment. (2) Students are notified of a brief interruption. (3) New UI is scheduled for a planned rollout with gradual user percentage exposure. |
| **Prevention** | Feature flags are managed through a centralised feature flag service, not environment config files. Each flag has a `environment_scope` field: staging flags cannot be promoted to production without explicit, separate activation. All feature flag changes require a second approver and are logged in the feature flag audit trail. |

---

## Operational Policy Addendum

### Academic Integrity Policies
All database migrations that modify grade, enrollment, or audit tables must be reviewed by the Engineering Lead and approved by the Registrar before deployment to production. Migration scripts that could destroy data (DROP COLUMN, TRUNCATE) require a database backup verification step in the deployment runbook before execution.

### Student Data Privacy Policies
Operational access to the production database (via bastion host or SSM Session Manager) requires a time-limited IAM role assumption, approved by the CISO or delegated authority. All production DB sessions are logged in CloudTrail. No developer may copy production student data to a non-production environment. Test and staging environments use anonymised data generated by a data masking script.

### Fee Collection Policies
Celery Beat tasks that process financial operations (overdue invoice escalation, refund processing, fee reminder dispatch) have an explicit `ETA` deadline check: if the task is picked up more than 15 minutes after its scheduled time (indicating a Beat crash and catch-up scenario), the task logs a `LATE_EXECUTION` warning and notifies the Finance team before proceeding — to prevent incorrect late-fee applications.

### System Availability During Academic Calendar
A deployment freeze is in effect during `REGISTRATION_WINDOW` and `EXAM_PERIOD` calendar events. No new ECS deployments, database migrations, or infrastructure changes may be performed during these windows without explicit CISO + Registrar + CTO approval. Emergency security patches are the only exception and require the same three-way approval with a post-deployment incident review.
