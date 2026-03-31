# Edge Cases – Operations

## Scenarios

| # | Scenario | Severity | Risk | Mitigation |
|---|----------|----------|------|-----------|
| 1 | PostgreSQL failover during active metadata writes | Critical | Control-plane inconsistency; partial transaction committed | Use transactional writes with explicit `BEGIN/COMMIT`; retry with idempotency key after failover; verify row existence before retry |
| 2 | Kafka queue backlog grows faster than worker capacity | High | Delayed jobs, events, and migrations | Autoscale workers on Kafka consumer lag metric (HPA); expose backlog SLO dashboard; alert at lag > 10,000 messages |
| 3 | Adapter runtime becomes unhealthy but binding remains `active` | High | Hidden partial outage; requests fail silently | Continuous adapter health-check every 30 seconds; `active` → `degraded` on 3 consecutive failures; surface in control plane UI |
| 4 | Reporting pipeline lags behind production events | Medium | Misleading usage or audit dashboards | Mark data with `freshness_at` timestamp; UI shows "as of N minutes ago"; `reporting_lag_seconds` SLI alerted above 300s |
| 5 | Switchover rollback partially completes | Critical | Mixed provider state; some objects in old, some in new | Persist step-level checkpoints; rollback is idempotent and resumable; operator intervention path via `POST /switchovers/{id}/resume-rollback` |
| 6 | Multi-incident overlap causes duplicate rollback operations | High | Conflicting rollback attempts destabilize state | Classify incidents by shared dependency; use distributed lock before any rollback; second rollback attempt returns `OPERATION_LOCKED` |
| 7 | Alert flapping causes on-call fatigue | Medium | Real incidents missed due to noise | Require consecutive-window breaches before paging (3-of-5 windows); `resolved` state requires 2 consecutive green windows |
| 8 | EKS node drain under load causes cascading pod evictions | High | Request errors during node maintenance | PodDisruptionBudgets ensure minimum available replicas; pre-drain graceful connection draining via SIGTERM handler |

## Deep Edge Cases

### PostgreSQL Failover Recovery
1. RDS detects primary failure; promotes read replica (typical < 30 seconds).
2. API services detect connection error; retry with exponential backoff up to 60 seconds.
3. Idempotency key cache (Redis) prevents duplicate side effects on retry.
4. After reconnection, in-flight transaction IDs are checked: if not committed, re-execute with same idempotency key.
5. Metrics: `db_connection_error_total` spikes → alert fires → on-call notified.

### Worker Autoscale Policy
```yaml
# HPA for queue-worker based on Kafka consumer lag
metrics:
  - type: External
    external:
      metric:
        name: kafka_consumer_group_lag
        selector:
          matchLabels:
            topic: baas-jobs
            group: queue-workers
      target:
        type: Value
        value: "500"  # scale when lag > 500 messages per replica
minReplicas: 2
maxReplicas: 20
```

### Partial Rollback Resume
Rollback checkpoints stored in `switchover_checkpoints`:
```
checkpoint_key = 'rollback:storage:copy-back:{objectKey}'
state = 'completed' | 'pending' | 'failed'
```
Resume API re-processes only `pending` and `failed` checkpoints, skipping already-`completed` ones. This makes rollback fully idempotent.

### Incident Classification and Correlation
- Each incident tagged with affected `capabilityKey` + `providerKey` + `envId`.
- If two incidents share the same `capabilityKey` + `providerKey`, they are grouped under the same incident umbrella.
- Only one rollback operation may be active per `(envId, capabilityKey)` at a time (enforced by advisory lock).

## SLO Breach Escalation

| Burn Rate | Window | Alert Channel |
|-----------|--------|--------------|
| > 14x | 1 hour | PagerDuty (critical) |
| > 6x | 6 hours | PagerDuty (warning) |
| > 3x | 24 hours | Slack #ops-alerts |
| > 1x | 72 hours | Grafana annotation only |

## State Impact Summary

| Scenario | Platform / Binding State |
|----------|------------------------|
| DB failover | API → retrying; binding unchanged |
| Worker backlog | Kafka consumer lag alert; HPA scales up |
| Adapter unhealthy | `active` → `degraded` |
| Switchover partial rollback | `rolled-back-partial` → resumable |
| Multi-incident overlap | Second rollback → `OPERATION_LOCKED` |
