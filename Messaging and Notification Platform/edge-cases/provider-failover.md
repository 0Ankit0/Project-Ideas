# Provider Failover

## Traceability
- Routing rules: [`../analysis/business-rules.md`](../analysis/business-rules.md)
- Event contracts: [`../analysis/event-catalog.md`](../analysis/event-catalog.md)
- Delivery internals: [`../detailed-design/delivery-orchestration-and-template-system.md`](../detailed-design/delivery-orchestration-and-template-system.md)

## Scenario Set A: SMS Provider Brownout During OTP Surge

### Trigger
Primary SMS provider begins timing out during a high-volume OTP burst.

```mermaid
flowchart LR
  Send[OTP dispatch] --> Primary[Primary SMS provider]
  Primary -->|timeout/error spike| Circuit[Open circuit]
  Circuit --> Route[Select secondary route]
  Route --> Secondary[Secondary SMS provider]
  Secondary --> Status[Record new dispatch attempt]
```

### Invariants
- Message identity and idempotency key are preserved across failover.
- P0 traffic may fail over automatically; lower-priority traffic can be throttled or delayed.

### Operational acceptance criteria
- Circuit open and failover decisions are visible in route-health dashboards within seconds.
- Replay or duplicate-callback handling does not turn failover into a duplicate business message.

## Scenario Set B: Split-Brain Health View Across Regions

### Trigger
One region marks a provider unhealthy while another still sees it as healthy because callback telemetry is delayed.

### Invariants
- Region-local routing may diverge briefly, but a single dispatch attempt must never use two primary routes at once.
- Health-state convergence must happen through a durable control channel, not ad hoc cache writes.

### Operational acceptance criteria
- Operators can view per-region health scores and last-telemetry timestamps.
- Recovery ramps traffic back gradually instead of immediately restoring 100% share.

---

**Status**: Complete  
**Document Version**: 2.0
