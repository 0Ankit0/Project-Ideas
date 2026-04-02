# Edge Cases: Rate Limiting and Quotas

## Overview

This document captures critical edge cases related to rate limiting and quota enforcement in the API
Gateway. The gateway uses Redis 7 as the primary counter store for sliding window, token bucket, and
fixed window rate limiting algorithms. BullMQ handles asynchronous quota usage analytics that feed
the Developer Portal and billing systems. Gateway instances maintain a local in-memory token bucket
as an L1 cache in front of Redis to minimize round-trip latency on hot paths.

Rate limiting operates across three enforcement dimensions simultaneously:

- **Per-API-Key quota** — the canonical enforcement boundary, tied to the consumer's billing plan.
- **Per-IP secondary limit** — abuse protection, not the primary billing gate.
- **Per-route burst limit** — protects individual backend services from instantaneous overload.
- **Global cluster limit** — a safety ceiling applied across all consumers to protect shared infrastructure.

Failure modes in this layer have direct revenue, availability, and trust implications. Under-
enforcement allows consumers to consume more than their paid quota, causing billing fraud and
unexpected backend load. Over-enforcement causes false 429s that degrade consumer experience and
can violate SLAs. The scenarios below cover Redis infrastructure failures, adversarial bypass
attempts, clock synchronisation issues, configuration errors, boundary race conditions, queue
backlogs, plan lifecycle transitions, and in-memory state loss on restart.

---

## Edge Cases

---

### EC-RATELIMIT-001: Redis Cluster Split-Brain Causes Rate Limit Counters to Diverge Across Partitions

**Background:** Redis cluster split-brain is one of the most severe distributed systems failure
modes for the rate limiting subsystem because it silently multiplies allowances without producing
any application-level errors. The gateway continues operating normally from a request-handling
perspective; the fault is invisible without dedicated inter-shard counter consistency monitoring.
This scenario is particularly dangerous because it can occur during routine AWS Availability Zone
maintenance windows when transient network partitions are more likely.

| Field | Detail |
|-------|--------|
| **Failure Mode** | A network partition in the Redis 7 cluster splits the cluster into two isolated segments. Gateway instances in Availability Zone A write INCR commands to one segment while instances in AZ B write to another. Because each segment accepts writes independently, the rate limit counter for the same API key increments toward the quota limit twice in parallel. The two segments each permit a full quota of requests before the partition heals and the cluster reconciles state. In effect the consumer receives 2× or more their entitled quota during the split window. |
| **Impact** | Consumers may issue 2× the permitted request volume during the partition window. For metered pay-per-request APIs this is direct revenue leakage. Backend services protected by the gateway receive unexpected doubled load, risking cascading failures in downstream databases and third-party provider rate limits. If the split lasts longer than a single quota window, the damage compounds. SLA commitments made to downstream providers may be breached, triggering penalty clauses. |
| **Detection** | Prometheus metric `redis_cluster_partition_detected` alerts within 30 seconds via the cluster bus heartbeat monitoring built into Redis 7. Grafana dashboard "Rate Limiting — Counter Consistency" visualises per-shard counter values for the same API key and fires an alert when any two shards diverge by more than 5% of the plan quota. Jaeger distributed traces for rate-limit decision spans expose which Redis node answered each request; diverging node IDs for the same key within a 10-second window flag the split. |
| **Mitigation / Recovery** | Switch rate limit writes to quorum mode using the Redis `WAIT` command (`WAIT 2 0`) requiring acknowledgement from at least two primaries before returning. Immediately reduce in-flight quota allowance by 50% as a conservative safety margin until full cluster quorum is restored. On partition heal, run a Redis SCAN over all `rl:*` keys and perform read-repair by writing the maximum observed counter value to all nodes, preventing a counter reset that would re-grant excess quota. Page the on-call SRE immediately with the affected partition topology. |
| **Prevention** | Deploy the Redis 7 cluster with a minimum of three primary nodes spread across three distinct AWS Availability Zones with one replica per primary. Enable `cluster-require-full-coverage no` so the cluster continues serving available shards rather than going fully offline during a partial partition. Implement consistent hashing with a designated tiebreaker Redis node for rate-limit keys when cluster health degrades below majority quorum. Run quarterly Redis partition chaos experiments using AWS Fault Injection Simulator to validate detection and recovery procedures. |

**Operational Notes:**
- Recovery procedure must be documented in the on-call runbook with exact Redis CLI commands.
- Post-incident: run `redis-cli cluster info` on each node to verify full cluster convergence.
- Billing reconciliation is required for any window where counter divergence exceeded 10%.
- This scenario should be included in the quarterly Chaos Engineering exercise plan.
- Coordinate with the AWS Support team if the partition was caused by an underlying AZ event.

---

### EC-RATELIMIT-002: Consumer Distributes Requests Across 1,000 Rotating IP Addresses to Bypass Per-IP Limits

**Background:** IP rotation as a rate-limit bypass technique is well-documented in adversarial
contexts and is also a legitimate pattern for large cloud-based API consumers routing traffic
through multiple NAT gateways. The distinction between legitimate multi-egress architectures and
adversarial IP rotation is made at the API key dimension, not the IP dimension. This case
underscores why API key-dimension enforcement must always be the primary rate limiting boundary.

| Field | Detail |
|-------|--------|
| **Failure Mode** | A consumer or automated bot network programmatically rotates through a pool of 1,000+ IP addresses, distributing requests such that no single source IP ever exceeds the per-IP rate limit threshold. The gateway enforces per-IP limits as a secondary abuse guardrail but does not correlate traffic from different IPs to the same API key for quota purposes. The consumer's aggregate request volume across all IPs far exceeds their plan quota, while each individual IP remains below the per-IP trigger. |
| **Impact** | The protected backend APIs receive traffic equivalent to a volumetric DDoS attack from an infrastructure capacity perspective. Legitimate consumers sharing backend resource pools experience elevated latency and elevated error rates. The offending consumer receives disproportionate value relative to their billing plan, creating billing fraud. If the rotating IPs originate from cloud provider egress ranges, AWS WAF IP reputation lists may not flag them automatically. Backend database connection pools and third-party rate limits may be exhausted. |
| **Detection** | Prometheus alert `api_key_request_rate_anomaly` fires when a single API key's aggregate RPS across all source IPs exceeds 3× the plan's per-second quota equivalent. Grafana dashboard "API Key Traffic Distribution" tracks the count of unique source IPs per API key within a rolling 1-minute window; a cardinality of more than 50 unique IPs triggers a medium-severity investigation alert, more than 200 unique IPs triggers a high-severity page. AWS WAF logs analysed by Amazon Athena can identify IPs belonging to known hosting provider CIDR blocks. |
| **Mitigation / Recovery** | Immediately enforce rate limits at the authenticated API key dimension as the hard enforcement boundary. Apply a temporary emergency quota suspension to the offending API key pending investigation. Activate the AWS WAF Managed Rule Group for anonymous IP lists and known commercial proxy ranges. Submit the observed CIDR ranges to the WAF IP block list. Contact the consumer account team to assess whether the behaviour is intentional (e.g., a legitimate CDN egress scenario) or malicious. Issue a retroactive quota correction in the billing system for the over-consumed window. |
| **Prevention** | The primary rate-limiting key must always be the authenticated API key or OAuth 2.0 client ID. Per-IP limits serve only as secondary abuse protection and must never be the sole enforcement gate. Implement composite rate limiting that evaluates (API key + sliding window) as the canonical enforcement dimension regardless of source IP. Set an IP cardinality hard limit of 500 unique IPs per API key per hour; breaching this triggers automatic temporary suspension and human review. Integrate AWS WAF Bot Control in targeted inspection mode on all gateway listeners. |

**Operational Notes:**
- Log the full list of observed source IPs for the affected API key to the security incident log.
- Coordinate with the enterprise account team before suspending keys of high-value customers.
- The IP cardinality threshold (50 unique IPs/min) should be tuned per plan tier in configuration.
- False positive risk: CDN providers and corporate NAT pools legitimately use many egress IPs.
- Review the WAF Bot Control pricing impact before enabling in targeted inspection mode.

---

### EC-RATELIMIT-003: Clock Drift Between Gateway Instances Causes Sliding Window Miscalculation

**Background:** Clock drift in containerised environments is more common than in traditional VM
deployments because containers share the host kernel clock, and ECS Fargate's hypervisor
architecture introduces additional clock synchronisation challenges. The impact of drift on sliding
window calculations is proportional to drift magnitude divided by window size; a 2-second drift
on a 60-second window produces a 3.3% error, while the same drift on a 10-second window produces
a 20% error.

| Field | Detail |
|-------|--------|
| **Failure Mode** | ECS Fargate tasks running gateway instances accumulate clock drift of up to ±2 seconds relative to UTC due to NTP synchronisation delays on container restarts or hypervisor VM clock skew. Sliding window rate limit calculations use `Date.now()` from the local instance clock to compute window start and end boundaries. Two gateway instances processing requests for the same API key compute different window boundaries, causing one instance to assign a request to the current window while another assigns it to the previous window. Counters for both windows are incremented, resulting in under-counting total usage and allowing excess requests through. |
| **Impact** | Consumers receive marginally more requests than their plan quota allows during drift periods. With a 2-second drift across multiple instances and a 60-second sliding window, up to 3-4% additional requests may pass through under normal traffic. For strictly metered pay-per-request plans, this creates billing inaccuracies that compound over high-traffic periods. In a 1-billion-request-per-month plan, a 3% leak represents 30 million unbilled requests. |
| **Detection** | AWS CloudWatch metric `chronyd_tracked_offset_seconds` is monitored for all ECS host instances. A CloudWatch alarm fires when any instance reports an NTP offset exceeding 500 milliseconds for more than 60 consecutive seconds. Grafana panel "Gateway Instance Clock Drift" visualises per-task NTP offset trends. A consistency check in the rate-limit middleware emits a log warning `WARN clock-drift-detected offset_ms=N` whenever the local timestamp deviates from a reference Redis `TIME` call by more than 200ms. |
| **Mitigation / Recovery** | Migrate all sliding window boundary computations to use Redis server-side time via the atomic `TIME` command, ensuring that all gateway instances use a single authoritative clock regardless of local NTP state. Deploy the change as a Lua script executed atomically on Redis that computes window keys from `redis.call('TIME')`, eliminating dependency on the ECS task clock entirely. Restart gateway tasks with excessive drift to trigger NTP resync. Run a one-time counter audit to identify and correct any windows with inflated counts due to historical drift. |
| **Prevention** | Configure all ECS tasks to synchronise with the AWS Time Sync Service endpoint `169.254.169.123` via chrony, with `maxdistance 0.1` (100ms maximum allowed stratum distance). Use Redis Lua scripts for all rate limit increment and check operations that derive window boundaries from `redis.call('TIME')`, making the Redis server the single source of clock truth across the entire fleet. Add a startup health check that rejects traffic routing until the local clock offset is confirmed below 100ms. Include NTP offset thresholds in the quarterly chaos engineering runbook. |

**Operational Notes:**
- The Redis `TIME` Lua script approach eliminates clock drift dependency permanently.
- Validate the fix by deploying to one AZ and inducing artificial clock skew with `timedatectl`.
- Monitor `chronyd_tracking_offset_seconds` as a continuous health metric, not just an alert.
- Clock drift can also affect JWT expiry validation; cross-reference with EC-SEC-004.
- Document the Redis-as-clock-source pattern in the architecture decision record.

---

### EC-RATELIMIT-004: Rate Limit Redis Key Expires Before Window Resets (TTL Misconfiguration)

**Background:** TTL misconfiguration in rate limiting is a class of silent correctness bug that
does not produce immediate errors or alerts. The system continues to function, but the rate
limiting guarantees are violated. This failure mode is most likely to be introduced during code
refactors that change the rate limiting window duration without updating the TTL calculation, or
during environment migrations where TTL constants are specified in environment variables that are
incorrectly translated.

| Field | Detail |
|-------|--------|
| **Failure Mode** | A code change or configuration error sets the Redis TTL on rate limit counter keys shorter than the rate limit window duration. For example, a 60-second sliding window key receives a 30-second TTL. After 30 seconds the key expires and the counter silently resets to zero, allowing the consumer to make another full quota of requests in the remaining 30 seconds of the window. The consumer effectively receives 2× quota within a single window. The inverse failure — an infinite or excessively long TTL — causes counters to never reset, permanently blocking the consumer after they exhaust their initial quota until manual intervention. |
| **Impact** | For the too-short TTL case, rate limiting becomes completely ineffective during the drift period. Consumers can double their request throughput and billing fraud becomes trivial to automate. For the infinite TTL case, innocent consumers are permanently locked out of the API after exhausting their first window, generating support escalations, SLA breaches, and customer churn. Both failure modes are production-breaking for the affected API keys and may go undetected for hours if monitoring is insufficient. |
| **Detection** | A Redis monitoring job runs every 5 minutes scanning all `rl:*` keys and asserting that `TTL(key) >= window_duration_ms - elapsed_ms` and `TTL(key) <= window_duration_ms * 2`. Any key outside this envelope emits a Prometheus metric `rate_limit_key_ttl_anomaly_total` and triggers a medium-severity alert. The gateway rate-limit middleware logs `WARN rate-limit key TTL mismatch expected=N actual=M key=K` on every enforcement check where the TTL deviates from the expected range by more than 10%. |
| **Mitigation / Recovery** | Run an emergency Redis SCAN over all `rl:*` keys and correct TTLs using `EXPIRE key correct_ttl` for every affected key. For keys with a zero TTL (persisted forever), apply `EXPIRE` immediately. For keys with expired TTLs (already vanished), the auto-reset has already occurred; document the affected window for billing reconciliation. Deploy a hotfix to the TTL computation code and perform a staged rollout through staging before production. Notify consumers affected by false 429 errors (infinite TTL case) with a credit. |
| **Prevention** | Centralise TTL calculation in a single `computeRateLimitTTL(windowMs: number): number` pure function with unit tests covering boundary values (1ms window, maximum window, zero TTL guard). The formula is `TTL = windowMs + Math.ceil(windowMs * 0.1)` (window duration plus a 10% grace buffer). Add an integration test that asserts `TTL >= window_duration` and `TTL <= window_duration * 2` after every Redis write in the rate-limit service. The Redis monitoring cron job described in detection must be a required deployment gate checked in the deployment pipeline. |

**Operational Notes:**
- The Redis key TTL audit cron job must be idempotent and safe to run multiple times.
- Corrections to TTLs should be logged with the old and new TTL values for audit purposes.
- The `computeRateLimitTTL` function must be the single source of truth — no inline calculations.
- Add TTL validation to the staging deployment smoke test to catch regressions pre-production.
- Consider using Redis keyspace notifications to alert on unexpected key expiry events.

---

### EC-RATELIMIT-005: Burst of Requests Exactly at Quota Reset Boundary Causing Double Allowance

**Background:** Fixed-window rate limiting's reset boundary vulnerability is a well-known algorithm
limitation. The "double allowance at boundary" pattern requires the consumer to precisely time
requests, which is trivially achievable with any HTTP client library that supports scheduled
execution. The vulnerability is most acute for plans with large per-window quotas: a plan allowing
10,000 requests per minute can receive 20,000 requests in a sub-second window straddling the reset
boundary, representing a significant backend load spike.

| Field | Detail |
|-------|--------|
| **Failure Mode** | A consumer programmatically times requests to arrive in the final 10 milliseconds before a fixed window quota resets and in the first 10 milliseconds after the reset. Because the Redis counter is atomically reset at the boundary, requests that arrive in the tail of the old window and the head of the new window are each checked against separate, freshly-reset counters. A consumer that exhausts their quota in the last 10ms of window N can immediately exhaust it again in the first 10ms of window N+1, injecting 2× quota worth of requests within a 20-millisecond period. |
| **Impact** | Backend services receive double the expected peak burst load in a sub-20-millisecond window. This is a thundering herd variant specific to quota reset boundaries. APIs with expensive per-request backend operations — database queries, ML inference calls, synchronous third-party API calls — may experience cascading latency spikes or connection pool exhaustion under the doubled instantaneous load. Downstream billing sees the traffic correctly as two separate windows, but the backend damage occurs before the accounting window closes. |
| **Detection** | Prometheus histogram `gateway_requests_per_second` per API key fires an alert when instantaneous RPS exceeds `2 × (quota_per_window / window_duration_seconds)` for more than two consecutive scrape intervals (10 seconds). Grafana time series "Requests at Window Boundary" is rendered with a 100ms resolution and visually shows bi-modal request concentration at reset boundaries. The alert is annotated with the API key, plan tier, and exact reset timestamp for rapid triage. |
| **Mitigation / Recovery** | Apply an immediate token bucket burst cap of 20% of the per-window quota as a per-second ceiling, enforced independently from the window counter. This cap prevents instantaneous full-quota consumption regardless of window boundaries. For consumers already exploiting the pattern, temporarily apply a 50% quota reduction for 1 hour while the burst limiter is deployed. Alert the consumer team to investigate whether the burst pattern is intentional client-side retry logic or adversarial. |
| **Prevention** | Replace fixed window rate limiting with a sliding window counter algorithm, which distributes the quota smoothly over time and eliminates discrete reset boundaries entirely. Implement a supplementary token bucket layer with capacity equal to 10% of the per-window quota, refilling at the plan's average per-second rate. This token bucket absorbs legitimate microbursts while preventing the boundary exploitation pattern. Document the algorithm selection rationale in the rate-limiting architecture decision record (ADR-007). |

**Operational Notes:**
- Sliding window counter is preferred over sliding window log for memory efficiency at scale.
- The token bucket burst cap complements the sliding window and should not replace it.
- Document the algorithm choice rationale in ADR-007 for future engineering context.
- Test the boundary attack pattern in a staging environment before claiming it is mitigated.
- Coordinate with the billing team on how boundary-straddling requests are counted for invoicing.

---

### EC-RATELIMIT-006: BullMQ Analytics Queue Backing Up Causing Rate Limit Status Updates to Lag

**Background:** The BullMQ analytics queue sits on the critical path between real-time enforcement
(Redis) and reportable usage (PostgreSQL). A queue backlog is a "soft failure" — the real-time
enforcement continues working correctly, but the observable state diverges from the actual state.
This divergence creates operational risk in two directions: consumers may over-consume believing
their quota is available, and support teams may incorrectly diagnose quota issues based on stale
Portal data.

| Field | Detail |
|-------|--------|
| **Failure Mode** | The BullMQ queue responsible for processing rate limit usage analytics and persisting quota consumption records to PostgreSQL experiences a growing backlog due to a combination of worker crashes, slow database bulk inserts, and a traffic spike. The gateway's real-time enforcement path uses Redis counters (fast path, sub-millisecond) and is unaffected. However, the Developer Portal quota usage dashboards and the billing system read from PostgreSQL (slow path). During the backlog period, the Portal displays stale usage data — potentially showing 0% quota consumed when the consumer has actually exhausted 100% — and billing records are incomplete. |
| **Impact** | Consumers viewing the Developer Portal make business decisions based on stale quota data, potentially scheduling additional high-volume workloads believing quota is available. Billing systems generate incorrect invoices for the lag period, requiring retroactive corrections that damage consumer trust. If job TTLs expire before processing (default BullMQ TTL is configurable but often overlooked), analytics events are permanently lost, creating unrecoverable gaps in audit trails. A 60-minute backlog at 10,000 requests per second represents 36 million unprocessed events. |
| **Detection** | Prometheus gauge `bullmq_analytics_queue_depth` fires a warning alert at 10,000 jobs and a critical alert at 50,000 jobs. Metric `bullmq_job_processing_lag_seconds` measures the age of the oldest waiting job; alert fires when lag exceeds 60 seconds. A secondary check compares the Redis-stored cumulative counter for an API key against the PostgreSQL-stored cumulative count; divergence exceeding 1,000 requests triggers a `quota_sync_lag_detected` alert. PagerDuty page is sent to on-call SRE when queue depth exceeds 50,000 jobs or lag exceeds 300 seconds. |
| **Mitigation / Recovery** | Trigger ECS auto-scaling for the BullMQ analytics worker service from the baseline of 2 tasks to up to 20 tasks by publishing a CloudWatch custom metric `AnalyticsQueueDepth`. Temporarily switch analytics workers to bulk-insert mode: accumulate up to 500 events in memory and flush with a single multi-row PostgreSQL INSERT every 500ms, increasing throughput from ~200 inserts/sec to ~10,000 inserts/sec per worker. After the backlog clears, run a reconciliation job that cross-checks Redis counters against PostgreSQL for the lag window and patches any missing records. |
| **Prevention** | Implement BullMQ job batching at the producer side: aggregate 100 individual analytics events into a single BullMQ job payload before enqueuing, reducing job count by 100×. Configure job options `removeOnComplete: { count: 10000 }` and `removeOnFail: { count: 5000 }` to bound queue memory usage. Set up BullMQ's built-in flow producer to use a dedicated high-priority queue for quota enforcement updates separate from general analytics, ensuring quota sync is never starved by lower-priority telemetry jobs. Conduct quarterly load tests simulating 10× normal traffic to validate queue throughput and auto-scaling response time. |

**Operational Notes:**
- The queue depth alarm thresholds (10K warning, 50K critical) should be reviewed quarterly.
- Bulk-insert mode must be toggled automatically, not manually, to avoid SRE action in incidents.
- Post-backlog reconciliation should compare Redis counters against PostgreSQL for all API keys.
- Consider Redis Streams as an alternative to BullMQ for high-throughput analytics events.
- The analytics pipeline is non-critical for real-time enforcement; prioritise based on this.

---

### EC-RATELIMIT-007: Consumer Plan Downgrade While Active Requests Are In-Flight Against Old Quota

**Background:** Plan downgrades are high-stakes operations because they are frequently triggered
by negative business events (payment failure, policy violation, abuse detection) that require
immediate enforcement rather than graceful propagation. The in-flight request window during a
downgrade is small (under 500ms for Redis pub/sub propagation), but in regulated environments
(financial services, healthcare APIs), even a sub-second period of over-service at an expired
plan tier may require documentation and audit trail justification.

| Field | Detail |
|-------|--------|
| **Failure Mode** | A consumer's account is downgraded from "Professional" (10,000 req/min) to "Starter" (100 req/min) via the Developer Portal admin interface — typically triggered by a billing payment failure or explicit plan change. The new quota configuration is written to PostgreSQL and a Redis pub/sub invalidation message is published. However, gateway instances that have the old quota cached in their local L1 memory store (TTL up to 30 seconds) continue admitting requests at the Professional limit for the duration of the cache TTL. During this window, 50–500 requests may be processed at the old, higher quota. |
| **Impact** | During the propagation window (up to 30 seconds for L1 cache expiry), the consumer continues receiving service at their previous plan tier. If the downgrade is triggered by a payment failure or security policy violation, this brief continued access at the higher tier constitutes a billing compliance breach and potentially a fraud risk. For regulatory environments (PCI-DSS, financial services), any access beyond the authorised plan tier must be logged, reported, and justified. The over-served requests must be documented for billing reconciliation. |
| **Detection** | The audit log records a `QUOTA_CONFIG_CHANGE` event with the API key, old plan, new plan, and the RFC3339 timestamp of the change. Prometheus metric `quota_config_stale_enforcements_total` is incremented whenever a rate-limit decision uses a quota configuration whose cache timestamp predates the last known update time for that key by more than 1 second. A Grafana alert fires if this counter exceeds 10 events per 5-second window for any single API key following a known plan change. |
| **Mitigation / Recovery** | On plan downgrade, immediately publish a Redis pub/sub message on channel `quota:config:invalidate` carrying the API key hash. All subscribed gateway ECS tasks evict the cached quota configuration for that key within 50ms of receiving the message, falling back to a synchronous Redis fetch for the next request. For payment-failure-driven downgrades, immediately suspend the API key entirely (HTTP 402 Payment Required) rather than downgrading, eliminating any in-flight window risk. Produce a post-incident report detailing the number of over-served requests and adjust billing accordingly. |
| **Prevention** | Use a write-through cache strategy: all quota configuration writes must update both PostgreSQL and Redis atomically before the API acknowledges the plan change. Set the maximum L1 in-memory cache TTL for quota configurations to 5 seconds (down from 30) to bound the worst-case propagation delay. For security-sensitive downgrades (payment failure, policy violation, abuse detection), bypass the cache entirely using a direct Redis write with a `PUBLISH` to the invalidation channel as a single Lua script, guaranteeing sub-100ms enforcement across all instances. |

**Operational Notes:**
- The pub/sub invalidation channel must be monitored for missed messages (subscription health).
- For payment-failure downgrades, the account suspension flow should be a separate code path.
- Test the propagation latency end-to-end with 50 gateway instances in a staging environment.
- Audit log the exact timestamp of plan change and first enforcement of new limits for compliance.
- The 5-second maximum L1 cache TTL represents a deliberate trade-off between performance and enforcement speed.

---

### EC-RATELIMIT-008: Gateway Restart Loses In-Memory Token Bucket State Mid-Window

**Background:** In-memory state loss on restart is a fundamental characteristic of stateless
container deployments. The pattern of using Redis as the authoritative state store with an
in-memory cache as a performance optimisation must be designed with the assumption that the cache
will be lost at any time. The initialisation strategy (pessimistic vs. optimistic bucket state)
determines whether a cold start results in brief under-enforcement or brief over-enforcement;
under-enforcement is always preferable from a backend protection perspective.

| Field | Detail |
|-------|--------|
| **Failure Mode** | The gateway maintains a local in-memory token bucket cache (L1 cache) in front of Redis to reduce per-request latency from ~2ms (Redis round-trip) to ~0.1ms (memory read). This L1 state is written back to Redis every 50ms in batch. When an ECS Fargate task is replaced during a rolling deployment, ECS auto-scaling event, or health-check-triggered restart, the in-memory token bucket state for all API keys assigned to that instance is lost. The restarting instance initialises fresh token buckets with full capacity for all keys, allowing consumers routed to that instance to consume a full quota burst until the first Redis sync at 50ms post-restart. |
| **Impact** | A consumer whose requests are routed to a cold-started gateway instance can issue up to a full quota burst in the 50ms window between instance start and the first Redis sync. In a 10-instance cluster undergoing a rolling deployment where 2 instances restart simultaneously, the effective momentary quota leakage can be 2× for consumers load-balanced across restarting instances. For plans with very high quotas (enterprise, 1M req/min), a single cold-start burst represents a significant backend spike. |
| **Detection** | ECS task lifecycle events published to CloudWatch Events trigger a Lambda function that records the restart and sets a `cold_start` flag for the instance in a Redis set `gw:cold_starts`. Prometheus metric `token_bucket_cold_start_total` is incremented on each gateway process initialisation. A Grafana alert fires when more than 3 cold starts occur within a 5-minute window, indicating an unusual restart pattern. Redis counter vs. local bucket discrepancy — when the Redis counter for an API key exceeds the plan quota but the local bucket reports available tokens — emits `WARN token-bucket-cold-start-over-allowance key=K`. |
| **Mitigation / Recovery** | Implement a "pessimistic initialisation" strategy for the in-memory token bucket: on ECS task cold start, initialise all token buckets to 0 tokens (fully consumed state) rather than full capacity. The gateway immediately fetches current Redis counter values for all active API keys via a pipeline GET on startup and hydrates the buckets with the accurate remaining tokens before accepting any inbound requests. The ECS task health check endpoint returns HTTP 503 until hydration is complete, preventing premature traffic routing during the 200ms hydration window. |
| **Prevention** | Enforce the pessimistic initialisation pattern in the token bucket constructor with a named parameter `initialState: 'empty' | 'redis-hydrated'`; the constructor must reject the value `'full'` at compile time via a TypeScript discriminated union, making the unsafe initialisation path unrepresentable. Add an integration test that asserts zero over-allowance during a simulated ECS task restart under active traffic. Document the startup sequence — (1) Redis connect, (2) hydrate buckets, (3) health check passes, (4) accept traffic — in the gateway operations runbook and enforce it in the ECS task definition health check configuration. |

**Operational Notes:**
- The pessimistic initialisation mode adds ~200ms to ECS task startup time — account for this.
- ECS deployment health check warm-up period must be longer than the Redis hydration time.
- Test cold-start behaviour during a rolling deployment in staging before every production release.
- The TypeScript compile-time guard on initialisation mode prevents regression without runtime cost.
- Correlate cold-start events with any quota anomaly alerts in the 60 seconds following a restart.

---

## Summary Table

| ID | Title | Severity | Primary Component | Worst-Case Impact | Recovery Time |
|----|-------|----------|-------------------|-------------------|---------------|
| EC-RATELIMIT-001 | Redis Cluster Split-Brain Divergence | Critical | Redis 7 Cluster | 2× quota per partition window | 5–15 min |
| EC-RATELIMIT-002 | Distributed IP Rotation Bypass | High | WAF + Gateway enforcement layer | Unlimited quota bypass | 10–30 min |
| EC-RATELIMIT-003 | Clock Drift in Sliding Window | Medium | ECS task NTP + Gateway logic | ~3–4% quota overrun | 1–5 min |
| EC-RATELIMIT-004 | Redis Key TTL Misconfiguration | High | Redis 7 TTL + Gateway config | 2× quota or permanent lockout | 2–10 min |
| EC-RATELIMIT-005 | Quota Reset Boundary Double Allowance | Medium | Gateway rate limit algorithm | 2× instantaneous burst | 5–15 min |
| EC-RATELIMIT-006 | BullMQ Analytics Queue Backlog | Medium | BullMQ + PostgreSQL | Stale Portal data, billing gaps | 15–60 min |
| EC-RATELIMIT-007 | Plan Downgrade In-Flight Requests | Low | Redis cache + pub/sub | Up to 30s over-service | < 1 min |
| EC-RATELIMIT-008 | Gateway Restart Token Bucket Loss | High | In-memory token bucket | Full burst leak on cold start | < 30 sec |

---

## Testing and Validation

The following test scenarios should be executed against the staging environment after any change to
the rate limiting subsystem. Each scenario maps to one or more edge cases documented above.

| Test Scenario | Target Edge Case | Expected Outcome | Frequency |
|---------------|-----------------|------------------|-----------|
| Simulate Redis cluster partition using AWS FIS | EC-RATELIMIT-001 | Quorum fallback activates, counter divergence alert fires within 30s | Quarterly |
| Send 10,000 requests from 500 rotating IPs using a single API key | EC-RATELIMIT-002 | API key suspension triggered, IP cardinality alert fires | Monthly |
| Introduce 3-second NTP offset on one ECS task | EC-RATELIMIT-003 | Clock drift alert fires, Redis TIME Lua script enforces correct window | Monthly |
| Deploy a config with TTL = window/2 to staging | EC-RATELIMIT-004 | TTL anomaly alert fires within 5 minutes | Per deployment |
| Send burst at exact fixed-window reset boundary | EC-RATELIMIT-005 | Token bucket burst cap prevents double allowance | Per algorithm change |
| Crash all BullMQ workers while under load | EC-RATELIMIT-006 | Dead-letter queue alert fires, auto-scaling recovers within 5 minutes | Quarterly |
| Downgrade consumer plan via admin API under traffic | EC-RATELIMIT-007 | New quota enforced within 5 seconds, no over-service > 2s | Per plan-change flow change |
| Restart all gateway ECS tasks simultaneously | EC-RATELIMIT-008 | No quota over-allowance during cold start, hydration completes in < 500ms | Per deployment |

All test results must be recorded in the rate limiting regression test log maintained in Confluence.
Failures in any scenario must be treated as a blocking issue before production deployment.

---

## Revision History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0 | 2025-01-01 | Platform Engineering | Initial edge case documentation |
| 1.1 | 2025-01-15 | Platform Engineering | Added EC-RATELIMIT-007 and EC-RATELIMIT-008 |

---

## Operational Policy Addendum

### A. Rate Limiting Governance Policy

All changes to rate-limit policy values (requests_per_minute, daily_quota, burst_size) for any subscription plan require:

1. A change request ticket approved by the Platform Engineering lead.
2. An impact analysis listing all consumers currently on the affected plan and their current utilisation versus the new limits.
3. A 7-day advance notification to affected consumers if limits are being decreased.
4. A staged rollout: change applied in staging environment for 24 hours before production deployment.

Emergency limit reductions (responding to an active abuse incident) may bypass the 7-day notice but require post-incident documentation within 48 hours.

### B. Redis Capacity and Scaling Policy

The Redis ElastiCache cluster used for rate-limit counters must maintain a minimum memory headroom of 30% at all times. Automated CloudWatch alarms must fire at:

- **Warning**: Redis `DatabaseMemoryUsagePercentage` > 60% for 5 consecutive minutes.
- **Critical**: `DatabaseMemoryUsagePercentage` > 80% for 2 consecutive minutes.

On receiving a Critical alarm, the on-call SRE must trigger a vertical scale-up (increase node type) within 15 minutes. A horizontal scale-out (add read replicas) is not sufficient for write-heavy rate-limit workloads.

The `maxmemory-policy` configuration must be set to `noeviction` for all rate-limit key namespaces (`rl:*`, `quota:*`). Eviction of rate-limit keys causes silent quota bypass (under-enforcement). If memory pressure requires eviction, the policy must be changed to `allkeys-lru` only for non-critical namespaces (e.g., response cache keys).

### C. Incident Response for Rate Limit Failures

Rate-limit related incidents are classified as follows:

| Severity | Condition | Response Time |
|----------|-----------|---------------|
| P1 — Critical | Redis unavailable; all rate limits bypassed | 15 minutes |
| P2 — High | Counter divergence > 10% detected across nodes | 30 minutes |
| P1 — Critical | Consumer receiving 0 requests due to false positive 429 | 15 minutes |
| P3 — Medium | Single consumer quota miscalculation | 4 hours |

All P1 incidents require a post-mortem document to be published within 5 business days.

### D. Audit and Compliance Requirements

For billing and dispute resolution purposes, the following data must be retained:

- Per-consumer daily quota usage snapshots: retained 2 years in PostgreSQL, archived to S3 Glacier thereafter.
- Rate-limit override records (who authorised, when applied, expiry): retained 1 year.
- Redis counter values: NOT retained (ephemeral by design). Billing disputes rely on the `usage_events` table in PostgreSQL, which is the authoritative billing source.
- Incident records referencing rate-limit failures: retained in the incident management system for 3 years.

Consumers may request a billing dispute review within 30 days of their monthly invoice. The platform will provide a CSV export of their `usage_events` records for the disputed period.

