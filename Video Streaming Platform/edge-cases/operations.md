# Video Streaming Platform - Operations Edge Cases

## Scenario 1: Transcoding Queue Backlog During Peak Demand

During major event (World Cup final), 100,000 concurrent uploads happen. Transcoding queue grows to 50,000 pending jobs. Even with auto-scaling to 500 workers, queue drains at rate of 100 jobs/minute (6000/hour), but arriving at 1000/minute. Queue backlog means 50+ hour wait for new uploads.

**Failure Mode**: Resource exhaustion. Platform can't keep up with demand.

**Symptoms**: Transcoding queue depth 50,000. Estimated wait time 50+ hours. S3 origin underutilized (no content to serve).

**Detection**: Queue depth trend. Alert if queue_depth > 10,000 for >10 minutes.

**Mitigation**:
1. Pre-event capacity planning: predict peak load, pre-scale resources
2. Implement backpressure: reject new uploads with 429 "Try again later" when queue > 5000
3. Priority queue: enterprise/premium uploads prioritized over free tier
4. Reduce transcoding profiles during peak: only encode 480p + 1080p (skip 360p, 720p)
5. Parallel processing: use GPU acceleration to speed up encoding

---

## Scenario 2: CDN Cache Purge Delay Affecting Stale Content Delivery

Creator updates content metadata (e.g., title, description). Change made in database. Cache invalidation request sent to CloudFront. CloudFront cache purge takes 15 minutes to fully propagate. Viewers requesting content within those 15 minutes see old metadata (stale title).

**Failure Mode**: Cache invalidation doesn't instantly purge all edge locations.

**Symptoms**: Metadata changed in API, but viewers see old version for 15+ minutes.

**Detection**: Detect stale content served from CDN. Version header mismatch.

**Mitigation**:
1. Use versioned cache keys: `/content/v2/metadata` instead of `/content/metadata`
2. Short cache TTL: metadata cache TTL = 5 minutes (not 24 hours)
3. Lazy purge: don't wait for purge to complete, update in parallel
4. Client-side cache busting: add timestamp to metadata request URL

---

## Scenario 3: Database Failover During Live Event

Multi-AZ RDS MySQL primary fails (hardware failure). Automatic failover promoted secondary to primary (takes 30-60 seconds). During failover, all database connections drop, API requests fail. Live stream publishing logic can't update stream status.

**Failure Mode**: DB failover causes 30-60 second outage. All API requests timeout.

**Symptoms**: API returns 503 "Service Unavailable" for 30-60 seconds. Live stream status not updated. Viewers see stale stream info.

**Detection**: Monitor RDS failover events. Alert on failover completion.

**Mitigation**:
1. Connection pooling with automatic reconnect: HikariCP retries failed connections
2. Regional read replicas: read-only requests go to replica, not primary
3. Circuit breaker: detect database outage, fail fast instead of waiting for timeout
4. Graceful degradation: serve cached stream info during failover, update asynchronously

**Recovery**: Failover completes within 60 seconds, connections restored.

---

## Scenario 4: Elasticsearch Reindex Blocking Search Availability

Elasticsearch reindex triggered to update mapping (e.g., add new field). Reindexing 1 billion documents takes 4 hours. During reindex, search service is unavailable (or very slow if reindexing in background).

**Failure Mode**: Search temporarily unavailable or extremely slow.

**Symptoms**: Search requests timeout (>30 seconds). Discovery of content broken.

**Detection**: Monitor Elasticsearch query latency. Alert if p99 > 5 seconds.

**Mitigation**:
1. Blue-green deployment: create new index, reindex to new, switch alias (no downtime)
2. Background reindexing: reindex happens in parallel, switch over when complete
3. Routing: during reindex, search goes to old index (not upgraded)
4. Stagger reindex: reindex at off-peak hours (2 AM UTC)
5. Async mapping: add new field without full reindex (if possible)

---

## Scenario 5: Full CDN Region Failure with Cascading Impact

CloudFront region us-east-1 experiences complete failure (network partition from AWS core). All traffic from that region fails. Viewers in US East try to access CDN, get no response. Fallback: origin requests go to origin, which is also in us-east-1 (single region deployment). Origin overloaded.

**Failure Mode**: Single region failure cascades to origin.

**Symptoms**: us-east-1 CDN unavailable. Origin requests overload origin from us-east-1 users.

**Detection**: Monitor CDN availability by region. Alert if region health check fails.

**Mitigation**:
1. Multi-region deployment: origin in primary + secondary region
2. GeoDNS: route users to nearest working region
3. Origin shield: intermediate cache layer protects origin
4. Failover DNS: if primary region down, DNS returns secondary region endpoint

**Recovery**: AWS resolves region failure, traffic returns to normal.

---

## Scenario 6: Kafka Consumer Lag During Mass Notification Storm

Live stream ends with 1 million concurrent viewers. All subscribers send "stream ended" notification to all 1 million followers. Kafka consumer processes notifications, but lag grows: 100,000 messages queued. Notifications delivered hours late instead of seconds.

**Failure Mode**: Notification consumer can't keep up with spike.

**Symptoms**: Consumer lag peaks at 500,000 messages. Notifications delivered 1+ hour late.

**Detection**: Monitor Kafka consumer lag. Alert if lag > 100,000 for >5 minutes.

**Mitigation**:
1. Batch notifications: send 1000 notifications in single message (reduces message count 1000x)
2. Sampling: send notification to 1% of followers, show count "Notification sent to X followers"
3. Async processing: don't wait for all notifications to send before marking stream "ended"
4. Increase consumer parallelism: spawn more consumer instances
5. Prioritize: VIP user notifications sent first, others batched and delayed

---

## Scenario 7: Storage Cost Spike from Orphaned Files

S3 bucket contains orphaned content files from failed transcoding jobs. Segments aren't deleted because cleanup job only deletes finalized content. After 6 months, 500 TB of orphaned segments accumulate. Monthly S3 bill increases $12,000 (500 TB * $0.023/GB/month).

**Failure Mode**: Orphaned files not cleaned up.

**Symptoms**: S3 bucket size unexpectedly large. Cost per GB higher than expected.

**Detection**: Monitor orphaned file count. Alert if orphaned > 10% of total files.

**Mitigation**:
1. S3 Object Tagging: tag all files with lifecycle metadata (status: active/orphaned)
2. Lifecycle policy: auto-delete orphaned files after 30 days
3. Manifest tracking: only keep segments referenced in current manifests
4. Regular audits: identify and delete orphaned files weekly

**Recovery**: Enable lifecycle policy, delete orphaned files, save $12,000/month.

---

(More scenarios would cover database scaling issues, network congestion, vendor API failures, etc.)
