# Operations Edge Cases

Infrastructure and operational failure scenarios for the **Resource Lifecycle Management Platform**, covering database failover, Kafka lag, outbox relay failure, and DLQ management.

---

## EC-OPS-01: PostgreSQL Primary Failover

**Description**: The PostgreSQL primary instance fails (hardware, network, or software crash). RDS Multi-AZ promotes the standby automatically.

| Aspect | Detail |
|---|---|
| **Trigger** | RDS Multi-AZ detects primary unhealthy; DNS CNAME for `postgres-primary` updated to standby |
| **Detection** | Application connection pool retries; `rlmp_db_connection_errors` metric spikes; RDS event notification fires |
| **Containment** | Application pods retry connections with exponential backoff (max 30 s); in-flight transactions fail with connection error; clients retry with idempotency keys |
| **Recovery** | RDS failover takes ~60 s; connection pool reconnects automatically; no data loss (synchronous replication to standby); in-flight commands are retried by clients |
| **Evidence** | RDS event log; application pod connection retry logs; health check failures during failover window |
| **Owner** | SRE |
| **SLA** | Automatic recovery within 60–90 s; manual escalation if > 5 min |
| **RPO** | Zero (synchronous replication) |
| **RTO** | ≤ 90 s for automatic Multi-AZ failover |

---

## EC-OPS-02: Kafka Consumer Lag Spike

**Description**: One or more Kafka consumer groups fall behind, causing event processing delays. This may affect: notifications, search indexing, audit forwarding, or settlement workers.

| Aspect | Detail |
|---|---|
| **Trigger** | Consumer lag > 1,000 messages for any consumer group for > 2 min |
| **Detection** | `rlmp_kafka_consumer_lag` metric alert; Kafka consumer group status shows lag increasing |
| **Containment** | Worker pods scale out via HPA (if CPU/memory pressure); no business operation blocked by consumer lag (writes succeed independently) |
| **Recovery** | HPA scales workers; lag drains within minutes; if specific worker is stuck (e.g., Notification Service down), DLQ receives messages after max retries |
| **Evidence** | Kafka consumer group lag metrics; worker pod count before/after HPA scale event; DLQ depth if worker is permanently failing |
| **Owner** | SRE |
| **SLA** | Alert within 2 min; lag drain within 10 min (auto-scale); manual escalation if > 30 min |
| **Prevention** | HPA configured for worker pods based on Kafka consumer lag metric (KEDA) |

---

## EC-OPS-03: Outbox Relay Job Failure

**Description**: The Outbox Relay Job pod fails and no events are published to Kafka. Business state mutations succeed (DB commits) but events are stuck in the outbox table.

| Aspect | Detail |
|---|---|
| **Trigger** | Outbox Relay pod crashes; `outbox.state = PENDING` count grows; `rlmp_outbox_pending` gauge exceeds 100 |
| **Detection** | Outbox pending metric alert (> 100 for > 2 min); SIEM notices no events from `rlmp.*` for > 5 min |
| **Containment** | All business state mutations continue to succeed (DB writes unaffected); events are safely queued in outbox table |
| **Recovery** | K8s restarts pod (crashloop backoff); on pod recovery, relay job processes all pending outbox records; events are delivered in order of `created_at`; no events lost |
| **Evidence** | Pod restart events; outbox pending count timeline showing accumulation then drain; event bus shows gap in events then burst |
| **Owner** | SRE |
| **SLA** | Alert within 2 min; auto-recovery within 60 s (K8s restart); manual escalation if > 5 min |
| **Prevention** | Pod liveness probe: restart pod if no records processed in last 30 s; DLQ for outbox records that fail relay after 5 attempts |

---

## EC-OPS-04: DLQ Overflow

**Description**: The Dead Letter Queue accumulates many unprocessable messages because an external dependency (e.g., Notification Service, Financial Ledger) is continuously unavailable.

| Aspect | Detail |
|---|---|
| **Trigger** | DLQ depth > 50 for > 10 min; alert fires |
| **Detection** | `rlmp_dlq_depth` gauge alert; specific queue name and oldest message age reported |
| **Containment** | DLQ holds messages safely; no data loss; investigate root cause of consumer failure |
| **Recovery** | (a) Fix external dependency (restore Notification Service or Ledger). (b) Replay DLQ messages: `POST /admin/dlq/replay?queue=<name>&limit=<n>`. (c) If messages are permanently unprocessable (schema change), triage individually and discard or patch. |
| **Evidence** | DLQ message contents with `original_event_id`, `failure_reason`, `retry_count`; Notification Service or Ledger error log |
| **Owner** | SRE |
| **SLA** | Alert within 5 min; triage within 30 min; resolution within 2 h |

---

## EC-OPS-05: Redis Cache Unavailability

**Description**: The Redis cluster becomes unavailable. Policy decisions cannot be cached, and idempotency checks fail.

| Aspect | Detail |
|---|---|
| **Trigger** | Redis cluster node failure; all replicas of a shard unavailable |
| **Detection** | Application connection errors to Redis; `rlmp_redis_errors` metric alert |
| **Containment** | **Policy Engine**: falls back to direct OPA evaluation (no cache); increased latency but no functional degradation. **Idempotency Store**: falls back to DB-based idempotency check (slower but correct). Commands continue to process. |
| **Recovery** | ElastiCache failover: standby shard promoted within 60 s; policy cache warms up within a few requests |
| **Evidence** | Redis error rate metric; P95 latency spike (OPA direct calls ~10 ms vs 1 ms cached); ElastiCache event log |
| **Owner** | SRE |
| **SLA** | Degraded mode (higher latency) tolerated for < 5 min; hard fail escalation if > 5 min |
| **Prevention** | Redis Cluster mode with 3 primary + 3 replica shards; ElastiCache Multi-AZ with automatic failover |

---

## EC-OPS-06: Elasticsearch Index Corruption or Unavailability

**Description**: The Elasticsearch cluster becomes unavailable or an index is corrupted. Catalog search and availability queries fail.

| Aspect | Detail |
|---|---|
| **Trigger** | Elasticsearch node crash; query returns `503`; search indexer consumer starts backing up |
| **Detection** | `rlmp_search_errors` metric alert; search endpoint returns errors; consumer lag on search-indexer topic increases |
| **Containment** | Search and catalog queries degrade gracefully: return `503 SEARCH_UNAVAILABLE` to clients; all write operations (reservations, allocations) continue unaffected via PostgreSQL |
| **Recovery** | Elasticsearch auto-recovers shards from replicas; or restore from last snapshot (S3); search indexer catches up on backlogged events; full catalog rebuilt from `rlmp.resource.*` events if index corrupted |
| **Evidence** | Elasticsearch cluster health API; snapshot manifest; consumer lag timeline |
| **Owner** | SRE |
| **SLA** | Degraded search within 5 min; full recovery within 30 min (failover) or 2 h (full rebuild) |
| **Prevention** | 3-node Elasticsearch cluster with replica shards; automated daily snapshots to S3 |

---

## EC-OPS-07: Audit Archive Job Failure (Decommission Blocked)

**Description**: The archive job is triggered for a decommissioning resource but fails to write to cold storage. The resource is stuck in `DECOMMISSIONING` state.

| Aspect | Detail |
|---|---|
| **Trigger** | S3 write fails (bucket permission error, S3 outage, or quota); archive job reports failure |
| **Detection** | `rlmp.resource.archived` event not published within 24 h of `rlmp.resource.decommission_approved`; alert fires |
| **Containment** | Resource remains in `DECOMMISSIONING` (not yet terminal `DECOMMISSIONED`); no further allocations possible; no data loss |
| **Recovery** | SRE investigates S3 error (permissions/quota); archive job retries up to 3 times with exponential backoff; after 3 failures, ops alert escalated; manual re-trigger available via `POST /admin/archive/{resource_id}` |
| **Evidence** | Archive job logs with S3 error code; `rlmp_archive_job_failures` metric; resource audit trail stuck at `DECOMMISSIONING` |
| **Owner** | SRE |
| **SLA** | Alert within 24 h; resolution within 4 h |

---

## Ops Runbook Summary

| Scenario | First Action | Escalation |
|---|---|---|
| DB failover | Monitor auto-recovery; verify connection pool reconnect | Escalate to DBA if > 5 min |
| Kafka lag | Check HPA scaling; verify external dependencies | Escalate to SRE lead if not draining after 30 min |
| Outbox lag | Check Relay pod health; review K8s restart events | Manual pod restart; escalate if > 5 min |
| DLQ overflow | Identify failing queue; investigate root cause; replay after fix | Finance/Compliance alert for settlement DLQ |
| Redis down | Verify degraded-mode operation; monitor latency | Escalate if > 5 min; failover to replica |
| Search down | Verify writes still operational; restore from snapshot | Escalate if rebuild > 2 h |
| Archive failure | Check S3 permissions; retry manually | Escalate to cloud team if S3 service issue |

---

## Cross-References

- Infrastructure deployment: [../infrastructure/deployment-diagram.md](../infrastructure/deployment-diagram.md)
- Implementation observability: [../implementation/implementation-guidelines.md](../implementation/implementation-guidelines.md)
- Security edge cases: [security-and-compliance.md](./security-and-compliance.md)
