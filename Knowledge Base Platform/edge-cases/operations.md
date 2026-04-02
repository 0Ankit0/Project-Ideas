# Operations — Edge Cases

## Introduction

The operations subsystem encompasses the infrastructure, data pipelines, and background job systems that underpin the Knowledge Base Platform's reliability: Amazon RDS PostgreSQL 15, BullMQ on Redis 7 (ElastiCache), AWS ECS Fargate for containerized API and worker services, Amazon OpenSearch Service for full-text indexing, CloudFront CDN for article delivery, S3 for attachment storage, and the platform's analytics event pipeline. Operational failures in this layer are often invisible to end users until they become catastrophic — a growing connection pool backlog, a swelling job queue, or a quietly misconfigured S3 bucket may cause no visible symptoms until the system crosses a threshold and fails hard.

The eight edge cases below cover the critical operational failure modes that SREs and on-call engineers are most likely to encounter: database resource exhaustion, queue saturation, memory-induced process crashes, schema evolution conflicts, CDN cache poisoning, storage policy misconfigurations, cache failover disruption, and analytics write amplification.

---

## EC-OPS-001: Database Connection Pool Exhaustion

### Failure Mode
The RDS PostgreSQL 15 instance is configured with `max_connections = 400`. The NestJS API runs as multiple ECS Fargate tasks (e.g., 10 tasks), each initializing a TypeORM connection pool with a maximum of 50 connections. Under peak load, all 10 tasks saturate their pools to 50 connections each, consuming all 400 available database connections. Simultaneously, BullMQ workers running in separate ECS tasks also maintain connection pools. New API requests that require a database connection are queued by TypeORM's pool manager. If they are not served within the configured `connectionTimeout` (5 seconds), they fail with `Error: Timeout acquiring a connection. The pool is probably full.` The user receives a 503 Service Unavailable error.

### Impact
**Severity: Critical**
- All API endpoints that require database access fail with 503 errors simultaneously.
- Under extreme pool exhaustion, even health check endpoints backed by the database fail, causing ECS to mark tasks as unhealthy and cycle them — further reducing capacity and increasing the outage duration.
- Write operations (article saves, user actions) fail without the user's data being persisted.

### Detection
- **Connection Count Metric**: CloudWatch `DatabaseConnections` metric. Alert at 75% of `max_connections` (300 connections).
- **TypeORM Pool Wait Time**: Track the pool connection acquisition wait time. Alert if P95 exceeds 2 seconds.
- **5XXError Rate**: CloudWatch alarm on `HTTPCode_Target_5XX_Count` spike correlating with `DatabaseConnections` saturation.
- **RDS Performance Insights**: View active queries and wait events. `ClientRead` and `Lock` wait events spiking indicate pool contention.
- **Application Logs**: `Error: Timeout acquiring a connection` log entries captured in CloudWatch Logs with a count-based alarm.

### Mitigation/Recovery
1. Immediately enable RDS Proxy (Amazon RDS Proxy) for connection multiplexing. RDS Proxy pools and reuses database connections, allowing thousands of application-layer connections to share a smaller set of actual database connections.
2. Reduce the TypeORM `max` pool size per task from 50 to 20 as a temporary measure. With 10 ECS tasks × 20 connections = 200 application connections, freeing headroom.
3. Identify and terminate any long-running idle connections: `SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND query_start < NOW() - INTERVAL '5 minutes'`.
4. Scale up the ECS API service horizontally (more tasks), but do not increase pool size — the additional tasks should use the same reduced pool size.
5. If RDS Proxy deployment takes time, temporarily raise `max_connections` on RDS by modifying the parameter group (requires a restart for non-RDS-Proxy instances — schedule during low-traffic window).

### Prevention
- Deploy RDS Proxy from the start. Configure it to maintain a maximum pool of 300 connections to RDS, shared across unlimited application connections.
- Set TypeORM pool `max` to 10 per ECS task and rely on RDS Proxy for connection multiplexing.
- Implement a connection pool health endpoint: `GET /api/health/db-pool` returns current pool size, idle connections, and wait queue depth.
- Set CloudWatch alarms at 60% (warning), 75% (high), and 90% (critical) of `max_connections`.
- Use `pg_stat_activity` monitoring to detect and automatically terminate connections idle for more than 5 minutes via a scheduled Lambda function.

---

## EC-OPS-002: BullMQ Job Queue Backlog

### Failure Mode
The article embedding pipeline processes articles through a BullMQ queue (`embed_article`) backed by Redis 7 (ElastiCache). Under normal load, the queue stays near-zero. Following a large workspace import (50,000 articles), or after an extended period of worker downtime (e.g., ECS task failure), the queue depth grows to 100,000+ jobs. Redis memory usage surges because BullMQ stores job payloads (article content, metadata) in Redis sorted sets. With each job averaging 5KB payload, 100,000 jobs consume 500MB of Redis memory. This approaches the ElastiCache instance's memory limit, triggering Redis eviction policies that may evict non-queue data (session tokens, search cache) before queue data.

### Impact
**Severity: High**
- Redis eviction of session tokens logs out all active users.
- Redis eviction of search cache causes a cache stampede on OpenSearch (see EC-SEARCH-003).
- BullMQ workers consume high CPU processing the backlog, degrading the performance of other Redis operations.
- Semantic search is unavailable for all articles enqueued but not yet processed (no embedding = no vector search).

### Detection
- **BullMQ Queue Depth**: Track `bullmq.embed_article.waiting` metric in CloudWatch. Alert at 1,000 (warning) and 10,000 (high).
- **Redis Memory Usage**: CloudWatch `FreeableMemory` dropping below 500MB triggers a High alert. Below 200MB triggers Critical.
- **Redis Eviction Count**: `CacheEvictions` metric > 0 is an immediate alert — evictions should not happen in a correctly sized cluster.
- **Worker Throughput**: Track `bullmq.embed_article.completed_per_minute`. Alert if it falls below 10 for 5 minutes (indicates worker stall).

### Mitigation/Recovery
1. If Redis memory is approaching the limit: immediately pause all non-critical queues (analytics events, email notification queue). Keep only the embedding queue active.
2. Increase ElastiCache instance type (vertical scaling) to a larger memory tier: this can be done as a live modification for cluster mode disabled configurations.
3. For the backlog: add more embedding worker ECS tasks (horizontal scaling) to drain the queue faster.
4. Implement job payload offloading: move large job payloads (article content) to S3 and store only the S3 key in the BullMQ job. This reduces per-job Redis memory from 5KB to ~100 bytes.
5. Prioritize queue jobs: urgent re-indexing jobs should have a higher priority than bulk import jobs.

### Prevention
- Use BullMQ's built-in rate limiting on the `embed_article` queue to cap concurrent jobs and prevent backlog-induced memory spikes.
- Implement job payload offloading as the default architecture: BullMQ stores only job metadata (article ID, workspace ID, version) in Redis; workers fetch the article content from PostgreSQL at processing time.
- Set a maximum queue depth policy: if the queue exceeds 5,000 jobs, new jobs are delayed with a warning to the requesting workspace admin.
- Schedule large imports during off-peak hours with worker concurrency pre-scaled for the expected load.
- Size the ElastiCache instance to accommodate 2x peak expected queue depth with headroom for session and cache data.

---

## EC-OPS-003: ECS Task OOM Kill

### Failure Mode
A workspace admin initiates a large article export: 5,000 articles exported to a single PDF. The NestJS `ExportService.exportWorkspace()` method loads all 5,000 article JSON blobs from PostgreSQL into memory, renders them using a headless Puppeteer instance (or a PDF library), and streams the output to S3. Each article averages 200KB in memory, loading 5,000 articles simultaneously consumes 1GB of RAM. Combined with the Puppeteer renderer (another 500MB), the total memory usage exceeds the ECS task's configured memory limit (1.5GB). The Linux kernel OOM killer terminates the ECS task mid-export. The user's export fails with no output file, the ECS task restarts, and the user receives no explanation other than a generic 502 error.

### Impact
**Severity: High**
- Large workspace exports consistently fail for workspaces above a certain size threshold.
- ECS task cycling during OOM kill causes a brief period of reduced API capacity, affecting other users.
- The user loses their export request and must start over.
- If the OOM kill happens during an active write transaction, the transaction is rolled back but may leave a partially created S3 object.

### Detection
- **ECS Task Stop Code**: CloudWatch `TaskStopCode = OutOfMemoryError` metric. Alert immediately.
- **ECS Memory Utilization**: CloudWatch `MemoryUtilization` > 90% for a running task triggers a High alert before the OOM kill.
- **Application Logs**: `FATAL: Killed` log entry from the Node.js process.
- **Export Job Monitoring**: BullMQ `export_workspace` job failing with a process exit code rather than an application error.

### Mitigation/Recovery
1. Immediately notify the user: "Your export encountered a resource limit. We are processing it in a dedicated export task."
2. Re-queue the export job with a dedicated high-memory ECS task definition (4GB memory, 2 vCPU) specifically for large exports. This task is only launched on demand.
3. Implement streaming export: process articles in batches of 100, write each batch to S3, and reassemble at the end. This caps peak memory usage at ~20MB per batch.
4. If the task was mid-export, clean up the partial S3 object using the S3 multipart upload abort API.

### Prevention
- Implement paginated, streaming exports: never load all articles into memory simultaneously. Use a cursor-based PostgreSQL query to fetch 100 articles at a time, process, write to S3 multipart upload, and proceed.
- Define a separate high-memory ECS task definition for export jobs. Scale it from 0 (no cost when idle) using ECS auto-scaling triggered by the `export_workspace` BullMQ queue depth.
- Set TypeScript/NestJS memory guards: if the payload size (estimated from article count × average article size) exceeds a configurable threshold, reject the synchronous export and switch to an async background export with email notification.
- Set ECS memory reservation and limit appropriately for the API service (1.5GB limit, 1.0GB reservation). This is separate from the export task definition.

---

## EC-OPS-004: OpenSearch Index Mapping Conflict

### Failure Mode
The platform's OpenSearch index (`kb-articles`) has an existing mapping for the `metadata` field as `type: keyword`. A developer adds a new article feature that stores a JSON object in `metadata` (e.g., `{"readingTime": 5, "category": "engineering"}`). When the `IndexArticleJob` worker attempts to index the first article with the new JSON `metadata`, OpenSearch rejects the document: `mapper_parsing_exception: failed to parse field [metadata] of type [keyword]`. All subsequent article index operations fail for any article with the new metadata structure. New articles are published but never indexed. Existing articles with the old metadata structure continue to index correctly, creating a split index.

### Impact
**Severity: High**
- All newly published articles after the metadata feature deployment are invisible in search.
- The BullMQ `IndexArticleJob` DLQ fills with failed jobs, triggering alerts.
- Users find that recently published articles are missing from search results.
- Rolling back the feature without a mapping migration leaves the index in an inconsistent state.

### Detection
- **OpenSearch Rejection Logs**: CloudWatch logs `mapper_parsing_exception` from the OpenSearch client. Alert on any occurrence.
- **Index Job DLQ Depth**: BullMQ DLQ depth > 10 for `index_article` queue triggers a High alert.
- **Publish-to-Index Lag**: The reconciliation job detects articles published but not indexed (see EC-SEARCH-001) and alerts.
- **Developer Runbook**: The deployment checklist for any change to article data structures must include an OpenSearch mapping migration step.

### Mitigation/Recovery
1. Immediately identify the mapping conflict using: `GET /kb-articles/_mapping` and compare the `metadata` field type against the new code's expectations.
2. Create a new index `kb-articles-v2` with the updated mapping: `metadata` as `type: object` (or `type: nested` if needed).
3. Reindex all existing documents from `kb-articles` to `kb-articles-v2` using OpenSearch's `_reindex` API.
4. Update the index alias (`kb-articles` → `kb-articles-v2`) atomically once reindexing is complete.
5. Delete the old index after the alias is updated and confirmed stable.
6. Re-queue all failed `IndexArticleJob` DLQ jobs to complete indexing of articles missed during the conflict period.

### Prevention
- Adopt index versioning and alias patterns from the start: the application always writes to and reads from the `kb-articles` alias, never directly to a versioned index. Mapping changes are implemented by creating a new versioned index and updating the alias.
- Add OpenSearch mapping validation to the CI/CD pipeline: before deploying any change that affects indexed fields, run a migration check that verifies the new document structure is compatible with the current mapping.
- Include an OpenSearch mapping migration step in the deployment runbook for all schema changes. This step must be completed before the new application code is deployed.
- Write integration tests that index a document with the new structure into the test index and assert the index operation succeeds before merging any change that modifies indexed fields.

---

## EC-OPS-005: CloudFront Cache Poisoning

### Failure Mode
An article is updated and republished. The NestJS API writes the new content to PostgreSQL, updates the OpenSearch index, and invalidates the CloudFront cache for the article's URL path. However, due to a CloudFront cache invalidation API quota limit (3,000 invalidation paths per month), the invalidation request for the updated article is rate-limited and fails silently. CloudFront continues to serve the stale cached version of the article to readers worldwide. Readers see the old version of the article even though the author can see the new version when accessing the API directly. The stale cache persists until the CloudFront TTL expires (24 hours).

A more severe variant: an attacker exploits a CloudFront cache key configuration that includes user-supplied headers to cache a malicious response that is then served to other users (classic cache poisoning).

### Impact
**Severity: High**
- Readers receive stale, incorrect, or outdated article content for up to 24 hours.
- For time-sensitive articles (security advisories, product announcements), stale content is operationally dangerous.
- In the cache poisoning variant, malicious content can be served to all users of a popular article.

### Detection
- **Cache Invalidation Failure Alert**: Track `cloudfront.invalidation_api_errors` metric. Alert on any error.
- **Content Staleness Check**: After every article publish, the backend fetches the article via the CloudFront URL and compares it against the database content hash. A mismatch triggers a `CLOUDFRONT_STALE_CONTENT` alert.
- **Article Version Mismatch**: The frontend article page includes an `X-Content-Version` header with the article's version ID. The API can detect if the version served by CloudFront is older than the latest published version.
- **Cache Poisoning Detection**: AWS WAF inspects CloudFront access logs for responses containing unexpected content types or JavaScript in cached HTML responses.

### Mitigation/Recovery
1. For stale cache: manually submit a targeted CloudFront invalidation for the affected paths via the AWS CLI: `aws cloudfront create-invalidation --distribution-id EDFDVBD6EXAMPLE --paths "/articles/slug-here"`.
2. If the invalidation quota is exhausted: temporarily set CloudFront TTL to 0 for the affected distribution behaviors, forcing all requests to origin. Restore TTL after the content is confirmed fresh.
3. For cache poisoning: immediately revoke the distribution's cache and rotate the CloudFront distribution's origin protocol settings if they may have been compromised.
4. Set up cache invalidation monitoring to track monthly usage against the quota.

### Prevention
- Use cache versioning in article URLs: when an article is published, include the version ID in the URL (`/articles/{slug}?v={versionId}`) so that each version has a unique CloudFront cache key. Old versions can be cached indefinitely; new versions are never cached-stale.
- Implement a CloudFront function at the edge that adds `X-Content-Version` headers to responses and allows the frontend to detect staleness.
- Set a conservative CloudFront TTL (5 minutes, not 24 hours) for article content, balancing cache efficiency with staleness risk.
- Harden cache key configuration: only include `Host` and `Accept-Encoding` headers in the cache key. Never include `Cookie`, `Authorization`, or user-supplied headers that could be exploited for cache poisoning.
- Monitor monthly CloudFront invalidation usage and alert at 80% of the monthly limit.

---

## EC-OPS-006: S3 Bucket Policy Misconfiguration

### Failure Mode
During a routine infrastructure review, an engineer modifies the S3 bucket policy for the `kb-attachments` bucket to test public access for a specific prefix. They add a `"Principal": "*"` statement without scoping it to a specific prefix, accidentally making the entire bucket publicly readable. This passes unnoticed if the S3 bucket's Block Public Access settings are not enabled at the account level. All private article attachments — internal documents, confidential PDFs, proprietary images — are now accessible to anyone with the attachment's S3 URL (which is a predictable format: `s3.amazonaws.com/kb-attachments/{workspaceId}/{articleId}/{filename}`).

### Impact
**Severity: Critical**
- All private attachments across all workspaces are publicly accessible.
- Confidential documents (financial data, product plans, customer data) can be downloaded by anyone.
- This is a data breach affecting all tenants.
- AWS security advisories, mandatory breach notifications, and regulatory investigations follow.

### Detection
- **AWS S3 Block Public Access**: Enable S3 Block Public Access at the account level — this is the first line of defense and would prevent this specific misconfiguration.
- **AWS Config Rule**: `s3-bucket-public-read-prohibited` and `s3-bucket-public-write-prohibited` AWS Config rules alert immediately when a bucket becomes publicly accessible.
- **Macie**: Enable Amazon Macie on the `kb-attachments` bucket to detect and alert on public access configuration changes.
- **GuardDuty S3 Finding**: AWS GuardDuty `Policy:S3/BucketBlockPublicAccessDisabled` finding triggers a Critical alert.
- **CloudTrail**: Track `PutBucketPolicy`, `DeleteBucketPolicy`, and `PutPublicAccessBlock` API calls in CloudTrail. Alert on these events from human IAM principals in production.

### Mitigation/Recovery
1. **Immediately** enable S3 Block Public Access on the affected bucket: `aws s3api put-public-access-block --bucket kb-attachments --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true`.
2. Remove or correct the bucket policy to eliminate the `"Principal": "*"` statement.
3. Determine the exposure window: check CloudTrail for when the policy was changed and estimate whether the bucket was actively accessed during that window.
4. Identify all objects in the bucket and assess whether any contain PII or confidential data.
5. Initiate breach notification procedures if PII was potentially exposed.

### Prevention
- Enable S3 Block Public Access at the AWS account level — this prevents any bucket in the account from being made public, regardless of bucket policies.
- Apply SCPs (Service Control Policies) in AWS Organizations to prevent disabling Block Public Access.
- Require all S3 bucket policy changes to go through the IaC pipeline (Terraform/CDK) and be approved by a second engineer. No manual `PutBucketPolicy` calls in production.
- Run `aws s3api get-public-access-block --bucket kb-attachments` as part of the automated infrastructure compliance check every 15 minutes.
- Use pre-signed URLs with short TTLs (15 minutes) for all attachment downloads, served through the NestJS API, so direct S3 access is never required.

---

## EC-OPS-007: Redis ElastiCache Failover Delay

### Failure Mode
The production ElastiCache Redis cluster uses a Multi-AZ configuration with one primary node and one replica. The primary node experiences a hardware failure or network partition at 2:15 PM on a Tuesday (peak traffic). ElastiCache initiates an automatic failover: it promotes the replica to primary. The failover process takes 30–60 seconds during which the Redis primary is unavailable and writes fail. All NestJS services that depend on Redis — session validation, BullMQ job queuing, search cache, rate limiting — experience errors or timeouts. Active users are effectively logged out (session reads fail), search cache returns misses, and BullMQ workers stop processing jobs.

### Impact
**Severity: High**
- 30–60 second outage for all Redis-dependent functionality.
- Active users are logged out mid-session as JWT session validation fails.
- Rate limiting is disabled during the failover, allowing burst traffic.
- BullMQ job processing halts and resumes after failover is complete.
- If the API service does not handle Redis connection errors gracefully, it may crash rather than degrade.

### Detection
- **ElastiCache Events**: Subscribe to ElastiCache ElastiCache events via SNS. `ElastiCache:Failover:Completed` and `ElastiCache:Failover:Started` events trigger alerts.
- **Redis Connection Error Rate**: Track `redis.connection_errors` metric. Alert if > 10 errors in 60 seconds.
- **Session Validation Failure Spike**: CloudWatch `auth.session_validation_errors` spike correlating with Redis unavailability.
- **BullMQ Worker Stall**: Jobs stop completing during the failover window; track `bullmq.jobs_completed_per_minute` dropping to 0.

### Mitigation/Recovery
1. The ElastiCache Multi-AZ failover is automatic — no manual intervention is needed for the promotion itself.
2. Ensure all NestJS services use the cluster endpoint (not the primary node endpoint directly), so they automatically reconnect to the new primary after failover.
3. If users were logged out during the failover, display a friendly re-authentication prompt: "Your session was interrupted. Please log in again." Use OAuth silent re-authentication where possible to minimize user friction.
4. After failover, verify queue consumption resumes: monitor BullMQ job completion rate for 5 minutes post-failover.
5. Investigate the root cause of the primary node failure and file an AWS support case.

### Prevention
- Always use the ElastiCache cluster endpoint DNS name in application configuration — never the individual node endpoint. The cluster DNS automatically routes to the current primary.
- Implement Redis connection retry logic in the `ioredis` client: `retryStrategy: (times) => Math.min(times * 100, 3000)` to automatically reconnect after failover without crashing.
- For session validation: implement a 10-second grace period where session validation failures fall back to allowing the current request (if the JWT signature is valid) rather than immediately rejecting. This prevents mass logouts during the 30-60 second failover window.
- Test Redis failover in staging quarterly: deliberately fail the primary node and measure the recovery time and user impact.
- Consider upgrading to ElastiCache Global Datastore for cross-region Redis replication, reducing failover time to sub-second for read operations.

---

## EC-OPS-008: Runaway Analytics Event Storm

### Failure Mode
A frontend bug in the Next.js article page causes the analytics event emitter to fire `article_viewed` events in a tight `useEffect` loop without a proper cleanup dependency array. Every re-render of the page (triggered by the same bug) emits an event, resulting in thousands of events per second per affected user. The `POST /api/analytics/events` endpoint writes each event to the `analytics_events` PostgreSQL table. The table receives 50,000+ inserts per minute from a single user session, overwhelming RDS write IOPS, bloating the analytics table, and degrading write performance for the articles and users tables. If the loop persists for hours before detection, the analytics table can grow by tens of gigabytes.

### Impact
**Severity: High**
- RDS write IOPS saturation degrades write performance for all tables, not just analytics.
- Analytics table becomes too large for queries, breaking the analytics dashboard.
- If RDS storage is provisioned with fixed IOPS (gp2), throughput throttling causes cascading slowness across the entire database.
- Autovacuum runs continuously on the bloated analytics table, consuming CPU and locking rows.

### Detection
- **Analytics Insert Rate Alarm**: CloudWatch `WriteThroughput` spike or custom metric `analytics.inserts_per_second` > 1,000 triggers a High alert.
- **Per-User Event Rate**: Track event counts per `user_id` per minute. Alert if a single user emits more than 100 events per minute (legitimate usage is 2–10 events per minute).
- **Table Size Growth**: Monitor `pg_relation_size('analytics_events')` growth rate. Alert if it grows by more than 1GB per hour.
- **Frontend Error Tracking**: Sentry captures rapid-fire network requests from the same page session as a performance anomaly.

### Mitigation/Recovery
1. Immediately deploy a per-user, per-event-type rate limit on `POST /api/analytics/events`: maximum 10 events per user per event type per minute. Excess events are dropped silently.
2. Deploy the frontend bug fix (correct the `useEffect` dependency array) as an emergency hotfix.
3. Purge the anomalous events from the analytics table: `DELETE FROM analytics_events WHERE user_id = :affectedUserId AND created_at > :bugDeploymentTime AND event_type = 'article_viewed'`. This may be a long-running query — run via `pg_background` to avoid locking.
4. Run `VACUUM ANALYZE analytics_events` immediately after the purge.
5. Verify RDS performance metrics return to baseline after the purge.

### Prevention
- Implement rate limiting as a standard middleware on all analytics ingestion endpoints: per-user and per-event-type limits enforced server-side, independent of frontend behavior.
- Write events to a BullMQ queue rather than directly to PostgreSQL. The queue acts as a buffer and allows rate limiting and deduplication before the database write.
- Implement deduplication at the analytics write layer: if an identical event (same `user_id`, `event_type`, `article_id`) occurs within a 5-second window, deduplicate and count rather than insert a new row.
- Add analytics event validation in the frontend: track event emission frequency client-side. If more than 5 identical events are emitted within 1 second, log a warning to Sentry and stop emitting.
- Partition the `analytics_events` table by day and drop old partitions automatically, limiting the maximum table size regardless of write volume.

---

## Summary Table

| ID         | Edge Case                             | Severity | Primary Owner           | Status   |
|------------|---------------------------------------|----------|-------------------------|----------|
| EC-OPS-001 | DB Connection Pool Exhaustion         | Critical | Backend / SRE           | Open     |
| EC-OPS-002 | BullMQ Job Queue Backlog              | High     | Backend / Infrastructure| Open     |
| EC-OPS-003 | ECS Task OOM Kill                     | High     | Backend / SRE           | Open     |
| EC-OPS-004 | OpenSearch Index Mapping Conflict     | High     | Backend / Search        | Open     |
| EC-OPS-005 | CloudFront Cache Poisoning            | High     | Infrastructure / SRE    | Open     |
| EC-OPS-006 | S3 Bucket Policy Misconfiguration     | Critical | Infrastructure / Security| Open    |
| EC-OPS-007 | Redis ElastiCache Failover Delay      | High     | Infrastructure / SRE    | Open     |
| EC-OPS-008 | Runaway Analytics Event Storm         | High     | Backend / Frontend      | Open     |

---

## Operational Policy Addendum

### 1. Infrastructure Change Management Policy

All changes to production infrastructure (RDS parameter groups, ElastiCache configurations, ECS task definitions, S3 bucket policies, CloudFront distribution settings, OpenSearch index mappings) must be made via the IaC pipeline (Terraform or AWS CDK). Direct console or CLI changes to production infrastructure are prohibited except during active incidents with Engineering Lead authorization. All infrastructure changes must be reviewed by a second engineer before apply. Database parameter changes that require an instance restart must be scheduled during the maintenance window (Sunday 2–4 AM local time).

### 2. Database Capacity Management Policy

RDS connection counts must be monitored continuously. RDS Proxy must be deployed for all production database connections. The connection pool size per ECS task must be configured such that `tasks × pool_size × 1.2 ≤ max_connections`. RDS storage must be monitored with an alarm at 80% capacity. Storage autoscaling must be enabled with a maximum storage limit set to 5x the initial provisioned storage. Monthly capacity reviews must assess CPU, storage, IOPS, and connection count trends and forecast scaling needs 3 months ahead.

### 3. Job Queue Operations Policy

BullMQ dead letter queues must be monitored. Any DLQ depth > 10 triggers a High alert and must be investigated within 4 hours. Failed jobs must not be silently discarded — they must always go to the DLQ with the full error context. BullMQ Redis memory usage must be monitored separately from session and cache memory. The embedding queue must have rate limiting configured to prevent single large operations from monopolizing Redis resources. BullMQ worker processes must implement graceful shutdown: on ECS task drain signal (`SIGTERM`), pause the queue and allow in-progress jobs to complete before exiting.

### 4. Export and Batch Operation Policy

All export operations producing more than 500 records must be processed asynchronously via BullMQ in a dedicated high-memory ECS task definition. Synchronous exports are limited to 100 records maximum. Large export jobs must stream their output to S3 using multipart upload — never accumulate the full output in memory. Export jobs must implement progress reporting so users can monitor long-running exports via a status endpoint. All export jobs must have a maximum runtime of 30 minutes; jobs exceeding this limit are failed with a `TIMEOUT` error and the user is notified with an option to export a smaller subset.
