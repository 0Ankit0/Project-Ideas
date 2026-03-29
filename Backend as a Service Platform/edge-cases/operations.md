# Edge Cases - Operations

| Scenario | Risk | Mitigation |
|----------|------|------------|
| PostgreSQL failover during active metadata writes | Control-plane inconsistency | Use transactional writes, retries, and explicit recovery verification |
| Queue backlog grows faster than worker capacity | Delayed jobs, events, and migrations | Autoscale workers and expose backlog SLO dashboards |
| Adapter runtime becomes unhealthy but binding remains active | Hidden partial outage | Continuously health-check bindings and surface degraded state in control plane |
| Reporting pipeline lags behind production events | Misleading usage or audit dashboards | Mark freshness timestamps and distinguish operational truth from projections |
| Switchover rollback partially completes | Mixed provider state | Persist step checkpoints and allow resumable rollback or operator intervention |

## Deep Edge Cases: Operations

- Multi-incident overlap: classify by shared dependency and prevent duplicate rollbacks.
- Alert flapping: require consecutive-window breaches before paging.
- Partial outage: support per-capability `degraded` state while core APIs remain `ready`.

Migration rule: freeze non-critical deploys when burn-rate exceeds incident policy threshold.
