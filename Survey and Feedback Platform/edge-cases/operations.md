# Edge Cases: Operations — Survey and Feedback Platform

## Overview

This document covers operational failure modes, infrastructure incidents, and system reliability edge cases for the Survey and Feedback Platform. These cases focus on AWS infrastructure failures, database incidents, container crashes, queue backlogs, and deployment risks. Each case includes specific CloudWatch alarm configurations, AWS CLI recovery commands, and runbook steps.

**Scope**: RDS PostgreSQL failover, ElastiCache Redis failure, ECS OOM kills, Kinesis throttling, Celery queue backlogs, S3 misconfiguration, database migration failures, and AWS AZ outages.

**Edge Case IDs**: EC-OPS-001 through EC-OPS-008

---

## EC-OPS-001: RDS PostgreSQL Primary Failover During Peak Response Collection

| Field | Details |
|-------|---------|
| **Failure Mode** | The RDS PostgreSQL primary instance in us-east-1a experiences a hardware failure or software issue. AWS initiates an automatic Multi-AZ failover to the standby instance in us-east-1b. During the 30-60 second failover window, all database connections are dropped. In-flight response submissions receive 500 errors. The response service's SQLAlchemy connection pool exhausts and may temporarily fail to reconnect. |
| **Impact** | **Critical** — 30-60 seconds of response submission failures. Any in-flight database transactions are rolled back (no data loss due to PostgreSQL ACID guarantees, but respondents must re-submit). Connection pool may take 5-15 seconds additional to recover after failover completes. For a survey receiving 100 responses/minute, approximately 50-100 responses may need re-submission. |
| **Detection** | CloudWatch alarm: `DatabaseConnections` drops to 0 on primary RDS endpoint. `RDS_EVENT_0006` (Multi-AZ failover initiated) triggers SNS notification → PagerDuty P1. Application logs: SQLAlchemy `OperationalError: server closed the connection unexpectedly`. ECS ALB: 5xx error rate > 5% for 60 seconds triggers health check alarm. |
| **Mitigation / Recovery** | 1. **Automatic**: RDS performs failover automatically; new primary is promoted in us-east-1b within 60 seconds. DNS CNAME for RDS cluster endpoint automatically updates. 2. Verify failover complete: `aws rds describe-db-instances --db-instance-identifier survey-platform-postgres --query 'DBInstances[0].{Status:DBInstanceStatus,AZ:AvailabilityZone}'`. 3. Verify application reconnects: `pool_pre_ping=True` in SQLAlchemy ensures stale connections are detected and replaced on next use. 4. Check for failed response_sessions: `SELECT id FROM response_sessions WHERE status='in_progress' AND last_activity_at < NOW() - INTERVAL '5 minutes'` — these are likely stale from the failover window. 5. Send CloudWatch alarm to PagerDuty; on-call engineer verifies application health within 5 minutes. 6. Monitor for remaining replication lag on new standby (should catch up within 30 minutes). |
| **Prevention** | 1. **RDS Multi-AZ**: Always enabled. Primary: db.r6g.2xlarge (8 vCPU, 64GB RAM), Standby: same spec in separate AZ. 2. **Connection pool configuration**: `pool_pre_ping=True`, `pool_size=20`, `max_overflow=10`, `pool_timeout=30`, `pool_recycle=1800`. 3. **Retry logic in Response Service**: SQLAlchemy with `tenacity` retry decorator on DB operations — retry up to 3 times with 1-second backoff for `OperationalError`. 4. **Respondent-friendly error handling**: If DB unavailable, return 503 with `Retry-After: 30` header and informative message: "We're experiencing a brief outage. Your progress is saved. Please try submitting again in 30 seconds." 5. **Response session partial save**: All answers are saved individually (not as one transaction), so only the final `complete` call fails — answers are preserved. 6. **Read replicas**: Non-critical read queries (analytics, survey config reads) route to RDS read replica in us-east-1b, reducing primary load. |

### CloudWatch Alarm Configuration
```json
{
  "AlarmName": "RDS-PrimaryFailover",
  "MetricName": "DatabaseConnections",
  "Namespace": "AWS/RDS",
  "Statistic": "Average",
  "Period": 60,
  "EvaluationPeriods": 1,
  "Threshold": 0,
  "ComparisonOperator": "LessThanOrEqualToThreshold",
  "AlarmActions": ["arn:aws:sns:us-east-1:ACCOUNT:pagerduty-p1"]
}
```

---

## EC-OPS-002: ElastiCache Redis Cluster Node Failure

| Field | Details |
|-------|---------|
| **Failure Mode** | One shard primary node in the ElastiCache Redis 7 cluster (3 shards, 1 replica per shard) fails. The shard's replica is promoted to primary automatically, but during the promotion window (typically 15-30 seconds), requests to that shard return `ClusterDown` errors. Redis is used for: JWT refresh token storage, magic link tokens, rate limiting counters, survey config cache, and Celery broker. Any in-flight operations against the failed shard are lost. |
| **Impact** | **High** — During failover: 15-30 seconds of auth failures (refresh tokens on failed shard), rate limit bypass (counters lost — allows burst traffic), and Celery task delays (broker temporarily unavailable). Post-failover: Celery task queue resumes. Rate limit counters reset (burst traffic possible for ~60 seconds). JWT tokens stored on failed shard are lost — those users must re-authenticate. |
| **Detection** | CloudWatch: `EngineCPUUtilization` spike + `Evictions` > 0 on failing node. `CacheMisses` sudden spike. Application logs: `RedisClusterError: ClusterDown` errors. CloudWatch alarm: `RedisNodeFailure` on `ReplicationBytes` = 0 for a node with `NodeType` = primary. ElastiCache Events in AWS Console: `NODE_FAILURE` event triggers SNS notification. |
| **Mitigation / Recovery** | 1. **Automatic**: ElastiCache promotes replica to primary within 30 seconds. 2. Verify shard recovery: `aws elasticache describe-cache-clusters --cache-cluster-id survey-platform-redis`. 3. **Auth impact**: Identify users whose refresh tokens were on the failed shard (sessions from the last 30-day window stored on that keyspace hash range). These users will receive 401 on next token refresh — they must re-login. This is acceptable and expected behaviour. 4. **Rate limit counters**: Accept that rate limits are temporarily reset for ~60 seconds post-failover. Monitor for burst traffic abuse during this window via CloudWatch. 5. **Celery broker recovery**: Celery workers reconnect automatically once Redis cluster is healthy. Tasks in-flight at time of failure are re-queued (Celery visibility timeout: 300s). 6. Verify all Celery workers reconnected: `celery -A app inspect active --timeout 5`. |
| **Prevention** | 1. **ElastiCache cluster mode with replicas**: 3 shards × 1 replica each. Replica in separate AZ from primary. 2. **Failover testing**: Quarterly chaos engineering exercise: force Redis node failure in staging to verify automatic recovery. 3. **Graceful Redis degradation**: Auth service falls back to PostgreSQL for token storage if Redis is unavailable (slower but maintains functionality). 4. **Rate limit graceful degradation**: If Redis unavailable for rate limiting, apply a conservative global rate limit (50% of normal) rather than failing open. 5. **Celery broker redundancy**: Configure Celery to use SQS as backup broker (activated automatically if Redis health check fails for >30 seconds). 6. **Survey config cache fallback**: Cache miss falls back to PostgreSQL — no feature outage, just higher DB load. |

### CloudWatch Alarm Configuration
```json
{
  "AlarmName": "ElastiCache-NodeFailure",
  "MetricName": "ReplicationBytes",
  "Namespace": "AWS/ElastiCache",
  "Dimensions": [{"Name": "CacheClusterId", "Value": "survey-platform-redis-001"}],
  "Statistic": "Sum",
  "Period": 60,
  "EvaluationPeriods": 2,
  "Threshold": 0,
  "ComparisonOperator": "LessThanOrEqualToThreshold",
  "AlarmActions": ["arn:aws:sns:us-east-1:ACCOUNT:pagerduty-p2"]
}
```

---

## EC-OPS-003: ECS Fargate Task OOM Kill During Report Generation

| Field | Details |
|-------|---------|
| **Failure Mode** | A report generation Celery task (running on the `report-service` ECS Fargate task with 4GB RAM) processes a survey with 500,000 responses and attempts to load the entire dataset into a pandas DataFrame for Excel generation. The Python process exceeds the 4GB memory limit, the Linux OOM killer sends SIGKILL to the process, and the ECS task exits with exit code 137. The report status remains stuck at `status='processing'` and the user receives no notification. |
| **Impact** | **High** — Report permanently stuck in "processing" state. User not notified of failure. Celery task marked as failed in Redis and moved to dead letter queue. If many concurrent large reports are requested, repeated OOM kills cause cascading ECS task restarts. Platform health check failures on repeated restarts. |
| **Detection** | ECS CloudWatch metric: `MemoryUtilization` > 95% on `report-service` task family. Container exit code 137 (SIGKILL). CloudWatch Logs: `Killed` in Celery worker log without graceful shutdown. Celery task enters `failure` state in `flower` monitoring dashboard. CloudWatch alarm: `ReportTaskOOMKills` counter > 0. |
| **Mitigation / Recovery** | 1. Identify stuck reports: `SELECT id, survey_id, status, created_at FROM reports WHERE status='processing' AND created_at < NOW() - INTERVAL '30 minutes'`. 2. Mark stuck reports as failed: `UPDATE reports SET status='failed', error_message='OOM: report too large. Please use CSV format or reduce date range.' WHERE id IN (...)`. 3. Notify affected analysts: send email with instructions to request a smaller date range or CSV export. 4. Trigger Celery task retry with streaming approach: `celery -A app retry report_generation --task-id {id}`. 5. Temporarily increase ECS task memory to 8GB for the retry. |
| **Prevention** | 1. **Streaming data processing**: Never load all rows into memory. Use SQLAlchemy `yield_per(1000)` for chunked reads. Use `openpyxl` in write-only mode (streaming API) for Excel: `workbook = Workbook(write_only=True)`. 2. **Pre-check data volume**: Before starting report, estimate row count × avg_row_size. If > 500MB estimated, force CSV-only format. 3. **Memory limits and estimation**: Implement memory tracking via `tracemalloc` in Celery tasks — abort and raise `ReportTooLargeError` if memory > 3.5GB. 4. **Dedicated task pools by size**: Small reports (<10K rows) on standard workers (2GB). Large reports (>10K rows) on dedicated `report-large` worker pool (8GB ECS task). 5. **Chunked S3 upload for Excel**: For large Excel files, write in chunks and use S3 multipart upload. 6. **Report size limits by tier**: Free: max 1,000 rows per report. Business: max 100,000 rows. Enterprise: unlimited (streaming). |

### CloudWatch Alarm Configuration
```json
{
  "AlarmName": "ReportService-OOMKill",
  "MetricName": "MemoryUtilization",
  "Namespace": "AWS/ECS",
  "Dimensions": [
    {"Name": "ClusterName", "Value": "survey-platform-cluster"},
    {"Name": "ServiceName", "Value": "report-service"}
  ],
  "Statistic": "Maximum",
  "Period": 60,
  "EvaluationPeriods": 1,
  "Threshold": 90,
  "ComparisonOperator": "GreaterThanOrEqualToThreshold",
  "AlarmActions": ["arn:aws:sns:us-east-1:ACCOUNT:pagerduty-p2"]
}
```

---

## EC-OPS-004: Kinesis Shard Throttling During Viral Survey Event

| Field | Details |
|-------|---------|
| **Failure Mode** | A single survey goes viral (shared on social media, large event opens simultaneously). Responses flood in at 2,000/minute. The Kinesis Data Stream is configured with 4 shards (each shard supports 1,000 records/second write throughput). However, all records are written with `partition_key=survey_id`, causing all records to land on the same shard. That shard is throttled (>1,000 TPS), returning `ProvisionedThroughputExceededException`. The analytics Lambda falls behind, and the real-time dashboard shows stale data. |
| **Impact** | **High** — Analytics Lambda processing falls behind by 5-10+ minutes. Real-time dashboard shows incorrect/stale counts. If Kinesis buffer overflows (24-hour retention), analytics records are lost permanently. Response submission itself is not blocked (Kinesis write is async), but analytics become unreliable. |
| **Detection** | CloudWatch: `GetRecords.IteratorAgeMilliseconds` > 300000 (5 minutes). `WriteProvisionedThroughputExceeded` > 0 on Kinesis stream. Lambda `IteratorAge` metric in CloudWatch. Alarm: `KinesisConsumerLag` alarm triggers SNS notification at 300s lag threshold. |
| **Mitigation / Recovery** | 1. Reshard Kinesis to add capacity: `aws kinesis update-shard-count --stream-name response-events --target-shard-count 8 --scaling-type UNIFORM_SCALING`. (Note: takes ~10 minutes to complete). 2. Fix partition key to distribute load: Change from `partition_key=survey_id` to `partition_key=f"{survey_id}#{session_id[:8]}"` — this distributes records across all shards. 3. If Lambda is backed up, increase Lambda concurrency: `aws lambda put-function-concurrency --function-name analytics-processor --reserved-concurrent-executions 100`. 4. Monitor catch-up: watch `IteratorAgeMilliseconds` decrease after resharding. 5. If records are near expiry (>20 hours old in buffer), prioritize processing: increase Lambda batch size to maximum (10,000 records). |
| **Prevention** | 1. **Composite partition key**: Always use `{survey_id}#{hash(session_id, 8)}` — distributes records across all shards while keeping survey records roughly co-located. 2. **Auto-scaling for Kinesis**: Use Application Auto Scaling for Kinesis shard count based on `IncomingRecords` metric. Scale out at 80% shard capacity utilization. 3. **DynamoDB write sharding for hot surveys**: For analytics aggregations of hot surveys, use composite DynamoDB key `(survey_id, date_hour_shard)` with 10 shards — distribute writes and aggregate at read time. 4. **Circuit breaker on Kinesis producer**: If `ProvisionedThroughputExceededException` occurs > 3 times/second, temporarily buffer in SQS and retry with backoff. 5. **Viral survey detection**: Monitor response rate per survey — if >500 submissions in 5 minutes, proactively add shards and notify platform team. |

### CloudWatch Alarm Configuration
```json
{
  "AlarmName": "Kinesis-ConsumerLag-High",
  "MetricName": "GetRecords.IteratorAgeMilliseconds",
  "Namespace": "AWS/Kinesis",
  "Dimensions": [{"Name": "StreamName", "Value": "survey-platform-response-events"}],
  "Statistic": "Maximum",
  "Period": 60,
  "EvaluationPeriods": 3,
  "Threshold": 300000,
  "ComparisonOperator": "GreaterThanThreshold",
  "AlarmActions": ["arn:aws:sns:us-east-1:ACCOUNT:pagerduty-p2"]
}
```

---

## EC-OPS-005: Celery Queue Backlog Exceeding 10,000 Tasks

| Field | Details |
|-------|---------|
| **Failure Mode** | A series of large email campaigns are scheduled simultaneously (e.g., end of quarter, a product launch). The Celery distribution queue accumulates 50,000+ pending tasks (send_email_campaign subtasks). Workers process at 500 tasks/minute — the backlog would take 100 minutes to clear. Meanwhile, survey creators see campaigns stuck in "sending" status for over an hour, and some campaigns miss their scheduled send windows. |
| **Impact** | **High** — Campaign delivery delays of 1-3 hours. Time-sensitive campaigns (event day surveys, NPS follow-ups post-purchase) miss their optimal send window. Creator trust impact. If Redis memory is exhausted by queue size, new task submissions fail. Worker processes may become unhealthy from prolonged processing loops. |
| **Detection** | Celery Flower dashboard: queue length > 10,000 triggers alert. Redis metric `UsedMemory` > 80% on ElastiCache. Custom CloudWatch metric `CeleryQueueDepth` pushed by Celery beat monitor. Alarm: `CeleryQueueDepth > 10000` → SNS → PagerDuty P2. |
| **Mitigation / Recovery** | 1. Scale out Celery distribution workers immediately: `aws ecs update-service --cluster survey-platform-cluster --service distribution-workers --desired-count 20`. 2. Prioritize time-sensitive campaigns: Implement priority queue (Redis sorted set) — campaigns scheduled for current hour get priority score=1, future campaigns score=2. 3. Throttle new campaign starts: Temporarily pause "Schedule" action for new campaigns until backlog clears. 4. Notify creators via email: "Campaigns scheduled between 14:00-15:00 UTC are delayed by approximately 45 minutes due to high platform volume." 5. Drain low-priority tasks (old scheduled campaigns past their window): `celery -A app purge -Q low-priority`. |
| **Prevention** | 1. **Queue capacity planning**: ECS auto-scaling for Celery workers based on SQS queue depth (use SQS as backing store for high-volume queues with visibility timeout). 2. **Rate limiting per workspace**: Maximum 2 active concurrent campaign sends per workspace — queue rest for sequential processing. 3. **Campaign scheduling with spread**: If multiple workspaces schedule campaigns simultaneously, spread start times by +/- 15 minutes (jitter) to avoid thundering herd. 4. **Redis memory monitoring**: Alarm at 70% Redis memory utilization to catch queue buildup early. 5. **Dead task cleanup**: Celery beat task runs hourly to purge tasks older than 24 hours that are still in `PENDING` state (campaign window has passed). 6. **Worker auto-scaling**: Celery worker count auto-scales from 5 (normal) to 50 (high) based on queue depth — uses ECS service auto-scaling. |

### CloudWatch Alarm Configuration
```json
{
  "AlarmName": "Celery-QueueBacklog-High",
  "MetricName": "CeleryDistributionQueueDepth",
  "Namespace": "SurveyPlatform/Celery",
  "Statistic": "Maximum",
  "Period": 300,
  "EvaluationPeriods": 2,
  "Threshold": 10000,
  "ComparisonOperator": "GreaterThanThreshold",
  "AlarmActions": ["arn:aws:sns:us-east-1:ACCOUNT:pagerduty-p2"]
}
```

---

## EC-OPS-006: S3 Bucket Policy Misconfiguration Exposing Report Files

| Field | Details |
|-------|---------|
| **Failure Mode** | During a Terraform apply, an incorrect S3 bucket policy is deployed to `survey-platform-reports`, setting `"Principal": "*"` for `s3:GetObject` — making all generated PDF reports publicly accessible without authentication. Pre-signed URLs are still valid but now unnecessary; anyone with the object key can access reports directly. |
| **Impact** | **Critical** — All generated PDF/Excel/CSV reports are publicly accessible. These files contain respondent PII, NPS scores, employee feedback, and business-critical survey data. GDPR Article 32 (security of processing) violation. Data breach requiring DPA notification within 72 hours. Business trust damage if reports contain confidential survey results. |
| **Detection** | AWS Config rule: `s3-bucket-public-read-prohibited` fires immediately when bucket ACL or policy allows public read. CloudWatch Events: `s3.amazonaws.com/PutBucketPolicy` API call triggers Lambda that validates policy for public access. AWS S3 Block Public Access setting (all 4 options enabled) — if someone disables this, Config rule fires. Security Hub finding: `S3.2 — S3 buckets should prohibit public read access`. |
| **Mitigation / Recovery** | 1. **Immediate**: Restore S3 Block Public Access: `aws s3api put-public-access-block --bucket survey-platform-reports --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true`. 2. Correct bucket policy: `aws s3api delete-bucket-policy --bucket survey-platform-reports && aws s3api put-bucket-policy --bucket survey-platform-reports --policy file://correct-policy.json`. 3. Assess exposure: Check S3 access logs to identify if any objects were accessed by unauthorized IP addresses during the exposure window: `aws s3 ls s3://survey-platform-reports/access-logs/ --recursive`. 4. Rotate all pre-signed URL signing keys (IAM key rotation). 5. Notify all workspace admins: "A security configuration was briefly misconfigured. We have no evidence of unauthorized access. As a precaution, please regenerate any downloaded reports." 6. File GDPR breach assessment — if access logs show unauthorized access, file Art. 33 notification within 72 hours of detection. |
| **Prevention** | 1. **S3 Block Public Access**: All 4 options enabled by default on all buckets via AWS Organizations SCP — cannot be disabled by individual accounts. 2. **Terraform plan validation**: `checkov` and `tfsec` scan Terraform plans in CI/CD; block apply if S3 public access is detected. 3. **AWS Config continuous compliance**: `s3-bucket-public-read-prohibited` and `s3-bucket-ssl-requests-only` Config rules with auto-remediation Lambda. 4. **Separation of duties**: S3 bucket policy changes require two-person approval in Terraform Cloud with security team reviewer. 5. **Bucket-specific IAM policy**: Only specific IAM roles (ECS task roles for report-service) can GetObject from the reports bucket. All other identities denied. 6. **VPC endpoint**: S3 access from ECS tasks uses VPC endpoint — no traffic leaves AWS network; public URL access still possible via CloudFront with signed URLs. |

### AWS CLI Recovery Commands
```bash
# 1. Re-enable S3 Block Public Access
aws s3api put-public-access-block \
  --bucket survey-platform-reports \
  --public-access-block-configuration \
  "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

# 2. Restore correct bucket policy (deny non-role access)
aws s3api put-bucket-policy \
  --bucket survey-platform-reports \
  --policy '{"Version":"2012-10-17","Statement":[{"Sid":"DenyPublicAccess","Effect":"Deny","Principal":"*","Action":"s3:*","Resource":["arn:aws:s3:::survey-platform-reports","arn:aws:s3:::survey-platform-reports/*"],"Condition":{"Bool":{"aws:SecureTransport":"false"}}}]}'

# 3. Check access logs for unauthorized access
aws s3api get-bucket-logging --bucket survey-platform-reports
```

---

## EC-OPS-007: Database Migration Failure During Rolling Deploy

| Field | Details |
|-------|---------|
| **Failure Mode** | A new service version is deployed with an Alembic migration that renames a column (`response_sessions.metadata` → `response_sessions.respondent_metadata`). The rolling deployment runs old and new code simultaneously for 5-10 minutes. Old code references `metadata`, new code references `respondent_metadata`. The column rename migration runs before all old containers stop, causing `column "metadata" does not exist` errors from old ECS tasks still processing requests. |
| **Impact** | **High** — 5-10 minutes of 500 errors on response submission and analytics endpoints during rolling deployment. Database inconsistency if both column names are referenced simultaneously. Failed responses during the deployment window. Potential need for emergency rollback. |
| **Detection** | Application logs: `ProgrammingError: column "metadata" does not exist` during deployment. ECS CloudWatch: 5xx error rate spike during deployment window. Deployment alarms: ALB `HTTPCode_Target_5XX_Count` > 10 during deployment → deployment auto-rollback. |
| **Mitigation / Recovery** | 1. Trigger ECS service rollback: `aws ecs update-service --cluster survey-platform-cluster --service response-service --force-new-deployment --task-definition response-service:PREVIOUS`. 2. Revert migration: `alembic downgrade -1` to undo the rename. 3. Assess impact: count failed submissions in the deployment window: `SELECT COUNT(*) FROM response_sessions WHERE created_at BETWEEN :deploy_start AND :deploy_end AND status='initiated'`. 4. Notify affected respondents if identifiable. |
| **Prevention** | 1. **Expand-Contract (Blue-Green) Migration Pattern**: Phase 1: Add new column `respondent_metadata` as nullable (migration runs). Phase 2: Deploy new code that writes to BOTH `metadata` AND `respondent_metadata`. Phase 3: Backfill: `UPDATE response_sessions SET respondent_metadata=metadata WHERE respondent_metadata IS NULL`. Phase 4: Deploy code that reads from `respondent_metadata` only. Phase 5: In next release: drop old `metadata` column. **Never rename or drop a column in the same deploy as the code that references the new name.** 2. **Migration compatibility check**: CI pipeline runs Alembic migration against a copy of production schema and tests both old and new application versions against it. 3. **Feature flags for schema changes**: New column usage is behind a feature flag (`USE_NEW_SCHEMA=false` in Parameter Store) — enabled only after all old containers have drained. 4. **Separate migration pipeline**: Migrations run in a dedicated pre-deploy step (GitHub Actions job), not at application startup. If migration fails, deployment is blocked. 5. **Canary deployments**: 5% of traffic routed to new version first; if error rate exceeds 1%, auto-rollback before full deployment. |

---

## EC-OPS-008: AWS Availability Zone Outage

| Field | Details |
|-------|---------|
| **Failure Mode** | AWS us-east-1b experiences a partial outage (power failure, networking issue). 50% of ECS Fargate tasks (those in us-east-1b) become unreachable. The RDS standby (in us-east-1b) is unavailable — RDS primary must stay in us-east-1a (no failover needed if primary is healthy). ElastiCache Redis shards with primaries in us-east-1b are promoted from replicas in us-east-1a. Route 53 health checks detect ALB health degradation and can failover. |
| **Impact** | **High** — 50% capacity reduction for ECS services. ALB drops requests to unhealthy tasks, increasing load on remaining tasks. Survey response collection continues but at reduced throughput (2x load on remaining tasks). If Redis primary shards were in us-east-1b, brief (30s) Redis unavailability during promotion. RDS read replicas in us-east-1b become unavailable — read traffic falls back to primary. Service degradation rather than outage. |
| **Detection** | AWS Health Dashboard event for us-east-1b. CloudWatch: `UnHealthyHostCount` on ALB target groups increases to 50%. ECS: `RunningTaskCount` drops by 50% on affected services. CloudWatch composite alarm `AZOutage` triggers if multiple services simultaneously show degradation. PagerDuty P1 alert. |
| **Mitigation / Recovery** | 1. **Automatic**: ECS places new tasks only in healthy AZ (us-east-1a) after us-east-1b tasks fail health checks. ALB stops routing to unhealthy tasks. 2. Scale up remaining capacity: `aws ecs update-service --cluster survey-platform-cluster --service response-service --desired-count 8` (double the usual). 3. Verify Redis cluster health: `aws elasticache describe-replication-groups --replication-group-id survey-platform-redis`. 4. If RDS read replicas in us-east-1b are down: `aws rds modify-db-instance --db-instance-identifier survey-platform-read-1 --no-multi-az --apply-immediately` to add replica in us-east-1a. 5. Monitor ALB request rates and error rates — if error rate > 5%, activate emergency CloudFront static fallback page. 6. ETA for AWS AZ recovery: monitor AWS Health Dashboard. Typically 1-4 hours for partial AZ issues. |
| **Prevention** | 1. **Minimum 2 ECS tasks per AZ**: Always maintain at least 2 tasks per AZ per service (4 total) so single-AZ outage does not drop below 50% capacity. 2. **ECS task placement strategy**: `SPREAD` across AZs for even distribution. 3. **Auto-scaling on AZ failure**: CloudWatch alarm on `UnHealthyHostCount > 20%` triggers ECS scale-out to compensate for lost capacity. 4. **Redis replicas in opposite AZ**: Ensure all Redis shard replicas are in the opposite AZ from their primary. 5. **RDS primary/standby cross-AZ**: RDS Multi-AZ ensures standby is always in opposite AZ. 6. **Disaster recovery runbook**: Quarterly DR drill simulating AZ outage in staging — verify recovery time meets 4-hour RTO. 7. **Static fallback**: CloudFront S3 origin fallback serves static "maintenance" page if ALB returns 5xx for >120 seconds. |

### Recovery Commands
```bash
# Scale up response-service to compensate for lost capacity
aws ecs update-service \
  --cluster survey-platform-cluster \
  --service response-service \
  --desired-count 8

# Check ElastiCache cluster status
aws elasticache describe-replication-groups \
  --replication-group-id survey-platform-redis \
  --query 'ReplicationGroups[0].NodeGroups[*].{Status:Status,PrimaryEndpoint:PrimaryEndpoint}'

# Check RDS instances across AZs
aws rds describe-db-instances \
  --query 'DBInstances[?DBInstanceIdentifier==`survey-platform-postgres`].[AvailabilityZone,DBInstanceStatus]'
```

---

## On-Call Runbook Overview

### Incident Escalation Matrix

| Severity | Response Time | Escalation | Example |
|----------|-------------|------------|---------|
| **P1 — Critical** | 15 minutes (on-call engineer) | On-call → Lead Engineer → CTO (if >1 hour) | Data breach, full service outage, security incident |
| **P2 — High** | 1 hour | On-call engineer | Single service degraded, AZ outage, database failover |
| **P3 — Medium** | 4 hours (business hours) | On-call during hours, next-day otherwise | Feature degradation, Celery backlog, analytics delay |
| **P4 — Low** | Next business day | Engineering team standup | Non-critical bug, minor performance issue |

---

## Incident Severity Levels

| Level | Name | Definition | SLA | Communication |
|-------|------|-----------|-----|---------------|
| P1 | Critical | Complete service outage, active security breach, data loss | 15-min response, 4-hr resolution | Status page update, customer email within 1 hour |
| P2 | High | Major feature unavailable, AZ failure, >5% error rate | 1-hr response, 8-hr resolution | Status page update, affected workspace notification |
| P3 | Medium | Degraded performance, analytics delay, campaign delivery delay | 4-hr response, 24-hr resolution | In-app banner notification |
| P4 | Low | Minor bug, cosmetic issue, non-urgent improvement | Next business day | Ticket created, no user notification |

### On-Call Tooling
- **PagerDuty**: Incident management and escalation (integrated with CloudWatch SNS topics)
- **AWS Systems Manager Session Manager**: SSH-free access to ECS tasks for debugging
- **Datadog / CloudWatch Dashboards**: Service health, error rates, response times
- **Celery Flower**: Real-time Celery task monitoring (`https://celery-monitor.internal.survey-platform.com`)
- **AWS Console Bookmarks**: RDS failover, ECS task management, WAF IP blocking
- **Runbook Wiki**: Confluence space: `SurveyPlatform > Operations > Runbooks`

---

## Operational Policy Addendum

### Response Data Privacy Policies

Operational incidents that involve potential data exposure (S3 misconfiguration, DB exposure, unauthorized access) are treated as GDPR incidents. The DPO is notified within 24 hours of detection; if personal data was exposed, a supervisory authority notification under GDPR Article 33 is filed within 72 hours. Operational logs containing request metadata (IP addresses, session IDs) are retained for 12 months and then purged. Production database snapshots are encrypted at rest (AWS KMS) and retained for 30 days.

### Survey Distribution Policies

Operational incidents affecting the distribution service (Celery backlog, SendGrid outage) trigger automatic campaign pause to prevent partial deliveries. Workspace admins are notified via email when their campaigns are paused due to platform incidents. When the incident is resolved, admins can resume campaigns from the last successful delivery point (checkpoint-based resumption).

### Analytics and Retention Policies

Operational incidents affecting Kinesis or the analytics Lambda (EC-OPS-004) cause temporary analytics staleness. The platform displays a banner on affected dashboards: "Analytics are currently delayed due to a platform issue. Data will update within [ETA] minutes." DynamoDB analytics data is retained for 90 days; RDS response data is retained per subscription tier. Database backups are retained for 30 days with point-in-time recovery (PITR) enabled.

### System Availability Policies

SLA targets: Response submission API 99.9%, Survey Builder 99.5%, Analytics Dashboard 99.5%, Distribution API 99.5%. Planned maintenance windows: Sundays 02:00–04:00 UTC with 48-hour advance notice. Emergency maintenance may be performed with 30-minute notice for P1 security issues. All availability metrics are reported on the public status page (status.survey-platform.com) and in the monthly SLA report to Enterprise customers. RTO: 4 hours for any single service outage. RPO: 1 hour (RDS PITR every 5 minutes; Kinesis 24-hour retention as buffer).
