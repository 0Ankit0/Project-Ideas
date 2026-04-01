# Operations — Edge Cases

## Overview

Operational failures in the infrastructure layer tend to be silent until they cascade. A 2-second
replication lag is invisible to users until a read-after-write returns stale data; a cache
stampede is imperceptible until the origin database is overwhelmed; Kafka consumer lag is
harmless until it crosses the retention window and messages are permanently lost. This file
covers the most impactful infrastructure failure modes and the mitigations that prevent them
from becoming user-visible outages.

---

## Failure Modes

| Failure Mode | Impact | Detection | Mitigation | Recovery | Prevention |
|---|---|---|---|---|---|
| Database replication lag | Read replicas serve stale data; read-after-write consistency failures for recently active users | Replica lag metric alert (>500 ms P2, >2s P1); client-visible stale-read complaints | Route writes to primary; route time-sensitive reads to primary or cache with write-through; lag-aware read routing | Direct reads to primary until lag subsides; backfill affected cache keys | Replication health monitoring; replica provisioning at 120% of write throughput |
| Cache stampede (thundering herd) | Cache key expires simultaneously for popular resource; hundreds of threads hit origin DB at once | CPU spike on DB correlated with cache miss rate spike; latency percentile degradation | Probabilistic early expiry (PER); mutex-locked cache population (single filler pattern); stale-while-revalidate | Serve stale data while repopulating; shed excess DB connections via connection pool limit | Cache key expiry jitter; hot-key detection and proactive refresh before expiry |
| Kafka consumer lag exceeding retention window | Messages permanently lost before consumption; data pipeline gaps; notification/event gaps | Consumer lag metric crossing 80% of retention window (alert at 50%) | Increase retention window for critical topics; scale consumer group; shed non-critical processing | Replay from external durable store (S3 event archive) if available; document data loss scope | Topic retention sized at 3× peak consumer processing time; auto-scaling consumer groups |
| Search index lag | Search results stale by minutes to hours; newly created content not discoverable | Index freshness metric; content-creation to search-availability latency alert | Tiered search: hot tier (Elasticsearch, near-real-time) + cold tier (Solr, batched); freshness SLO per content type | Trigger manual re-index of affected time window; notify users if search degraded | Indexing pipeline monitoring; index health checks every 60 seconds; write-through index for new posts |
| Media processing pipeline failure | Videos/images uploaded but not transcoded; users see broken media; engagement loss | Upload success with processing failure rate; media-ready event lag alert | Retry queue with dead-letter escalation; partial delivery (show thumbnail while video transcodes) | Requeue failed jobs; notify users when media becomes available via push/email | Idempotent job IDs; separate queues by media type; capacity planning for peak upload windows |
| CDN cache invalidation lag | Stale content served after update or deletion; legal risk if deleted content lingers at edge | Edge cache age header monitoring; post-deletion content availability probe | Surrogate-key-based purge (purge by tag, not URL); short TTL for mutable resources; soft-delete + edge purge | Manual purge via CDN API; fallback to origin for affected resource | Automated purge tests in deployment pipeline; CDN purge SLA contract with provider |
| Connection pool exhaustion | New DB connections refused; service degraded or down; cascading failures | DB connection count alert at 80% of max_connections; connection wait time spike | Connection pool max sized to DB capacity minus headroom; connection timeout with circuit breaker | Restart connection pool; shed non-critical services from DB tier; add read replicas | PgBouncer/ProxySQL in front of DB; per-service connection budget; connection leak detection |
| Object storage eventual consistency read-after-delete | Deleted media remains accessible via direct S3/GCS URL for seconds to minutes after deletion | Post-deletion URL probe; object storage consistency SLA monitoring | Apply CDN purge immediately on deletion; short TTL on media URLs; signed URL expiry | Purge CDN; wait for object storage consistency propagation; re-verify deletion | Use object storage lifecycle rules; CDN TTL for media set to ≤60 seconds for user-deletable content |

---

## Detailed Scenarios

### Scenario 1: Cache Stampede on Trending Post

**Trigger**: A post goes viral and is fetched 80,000 times/minute. The cache key for the post
holds a 60-second TTL. At expiry, all 80,000 in-flight requests simultaneously find a cache
miss and attempt to fetch from the origin database, generating 80,000 concurrent queries
against the primary read replica.

**Symptoms**:
- DB connection pool saturated within 2 seconds of cache expiry.
- Query latency on the read replica rises from 5 ms to 4,200 ms.
- Surrounding unrelated queries time out; other features (profile load, feed ranking) degrade.
- Error rate spikes; users see loading spinners.

**Detection**:
- Cache miss rate alert: >30% miss rate on post-detail cache (normally <2%) fires P1.
- DB connection pool utilization alert at 80%.
- Correlated: trending post cache miss spike + DB latency spike within same 30-second window.

**Mitigation**:
1. **Probabilistic Early Revalidation (PER)**: Each cache read has a small probability of
   triggering a background refresh in the final 20% of the TTL window. Probability increases as
   expiry approaches. This smooths cache population across time rather than concentrating it.
2. **Mutex-locked cache fill**: On a cache miss, only one request proceeds to the DB; all others
   wait on a distributed lock (Redis `SET NX`) for up to 500 ms, then receive the freshly
   populated value.
3. **Stale-while-revalidate**: Serve the expired value to all requests while a single background
   thread fetches the fresh value. Avoids any user-visible latency for stale content.
4. **Hot-key detection**: A sampling layer identifies keys fetched >10,000 times/minute.
   Hot keys are proactively refreshed at T-10s before their TTL expires.

**Recovery**: Once the stampede begins, disable cache expiry for the affected key by extending
TTL by 60 seconds; allow DB to drain; re-enable normal TTL policy.

**Prevention**: PER and mutex-lock implemented as default behavior in the platform cache
client library, not opt-in per feature; hot-key detection runs continuously.

---

### Scenario 2: Kafka Consumer Lag Exceeding Retention Window

**Trigger**: The notification fan-out consumer group encounters a bug that causes it to crash
on a specific message format (a new emoji in post text, incorrectly parsed). The consumer dies
on that message, resets to the same offset, and crashes in a loop. Over 18 hours, the consumer
group falls 22 hours behind the producer — exceeding the 24-hour topic retention window.

**Symptoms**:
- Consumer lag metric climbs linearly from T+0.
- Dead-letter queue grows as the consumer repeatedly fails on the same message.
- At T+18h, lag is within 6 hours of retention; alert fires at 50% retention threshold (T+9h).
- If unaddressed: at T+24h, messages are permanently lost; notification backlog is irrecoverable.

**Detection**:
- **Lag alert at 50% retention**: consumer lag >12 hours on a 24-hour retention topic triggers P1.
- **Consumer restart rate**: >3 restarts/minute on a consumer pod triggers P2 alert.
- **Dead-letter queue growth**: DLQ depth >1,000 triggers P2.

**Mitigation**:
1. **Skip-and-DLQ on parse failure**: Consumer wraps message deserialization in a try/catch;
   unparseable messages are forwarded to a dead-letter topic rather than blocking the consumer.
2. **Retention window extension**: Extend retention to 72 hours for all critical topics as a
   standing configuration, not a reaction.
3. **Consumer group scaling**: Auto-scaling consumer group increases partition consumers when
   lag exceeds 1 hour.
4. **S3 event archive**: All topic messages are mirrored to S3 with infinite retention. If
   messages are lost from Kafka, they can be replayed from the S3 archive.

**Recovery**:
1. Deploy bug fix for emoji parsing.
2. Reset consumer group offset to the last successfully processed message.
3. Scale consumer group to 3× normal size to drain backlog at accelerated rate.
4. Discard or replay DLQ messages depending on staleness.

**Prevention**: Fault-injection test that sends a malformed message to a consumer and verifies
DLQ routing; retention window set to 72 hours by default for all new topics.

---

### Scenario 3: Media Processing Pipeline Failure During Upload Surge

**Trigger**: A major live event causes a 15× spike in video uploads over 30 minutes. The
video transcoding job queue, sized for 3× normal peak, is overwhelmed. Jobs queue for up to
45 minutes. 12% of uploads exhaust their retry budget and fail permanently, with users seeing
"Video processing failed. Please try again."

**Symptoms**:
- Media processing job queue depth alert fires at 5,000 pending jobs (normally <300).
- Media-ready event lag rises from 45 seconds to 48 minutes.
- 12% of upload jobs exceed max-retry limit and write to dead-letter queue.
- User support tickets spike: "My video didn't upload."

**Detection**:
- Job queue depth alert at 1,000 jobs (P2) and 5,000 jobs (P1).
- Processing latency p95 alert at 5-minute threshold.
- Dead-letter queue growth alert at 50 failed jobs in 5 minutes.

**Mitigation**:
1. **Partial delivery**: Show image thumbnail (generated in <2 seconds) immediately on upload;
   display a "Video processing… this may take a few minutes" indicator while the full video
   transcodes. Users confirm their upload succeeded; frustration is mitigated.
2. **Elastic transcoding capacity**: Media processing workers are deployed on spot/preemptible
   instances with an auto-scaling group that scales from 20 to 200 workers in 5 minutes.
3. **Priority queuing**: Verified creator accounts and live-event hashtag content receive
   priority queue slots to ensure timely processing of high-value content.
4. **Dead-letter retry notification**: Failed jobs in the DLQ trigger a push notification
   to the user: "Your video is still processing — we'll notify you when it's ready." A
   background sweep retries DLQ jobs once capacity normalizes.

**Recovery**: Scale workers to drain queue; process DLQ with normal priority; send "your
video is ready" push notification to all users whose jobs completed from the DLQ.

**Prevention**: Load test the media pipeline against 20× normal upload volume annually; auto-
scaling configuration reviewed as part of every major event capacity plan.
