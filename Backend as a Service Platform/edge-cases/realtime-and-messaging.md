# Edge Cases - Realtime and Messaging

| Scenario | Risk | Mitigation |
|----------|------|------------|
| Event provider guarantees only at-least-once delivery | Duplicate consumer processing | Require consumer idempotency and delivery identifiers |
| Events arrive out of order during failover | Broken projections or client state | Include sequence metadata and backfill mechanisms |
| WebSocket provider outage interrupts subscriptions | Realtime UX degradation | Reconnect through alternate gateway and backfill missed events where supported |
| Backpressure on webhook deliveries | Queue growth and delayed notifications | Use retry policies, DLQs, and delivery health dashboards |
| Provider migration mid-stream | Lost or duplicated events | Define drain, fence, or dual-publish cutover patterns per capability |

## Deep Edge Cases: Realtime and Messaging

- Out-of-order delivery across shards: include monotonic sequence in envelope and client reorder logic.
- Subscriber reconnect storm: apply tenant-aware backoff buckets.
- Webhook destination 5xx: map to `DEP_SUBSCRIBER_UNAVAILABLE` and schedule dead-letter handling.

SLO: p95 delivery latency and dead-letter rate per tenant/environment.
