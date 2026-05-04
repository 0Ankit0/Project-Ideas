# Edge Cases and Failure Modes

## Traceability
- Requirements: [`../requirements/requirements.md`](../requirements/requirements.md)
- Analysis: [`../analysis/business-rules.md`](../analysis/business-rules.md), [`../analysis/event-catalog.md`](../analysis/event-catalog.md)
- Detailed design: [`../detailed-design/delivery-orchestration-and-template-system.md`](../detailed-design/delivery-orchestration-and-template-system.md)
- Operations plan: [`../implementation/implementation-guidelines.md`](../implementation/implementation-guidelines.md)

## Coverage Matrix

| Document | Primary failure domains |
|---|---|
| [`api-and-ui.md`](./api-and-ui.md) | concurrent mutations, stale status, oversized payloads, preview abuse |
| [`provider-failover.md`](./provider-failover.md) | provider brownouts, split-brain route health, partial callback loss |
| [`rate-limiting.md`](./rate-limiting.md) | tenant burst throttling, shared-provider quotas, backpressure propagation |
| [`delayed-deduplicated-delivery.md`](./delayed-deduplicated-delivery.md) | schedule-window drift, duplicate callbacks, clock skew, replay confusion |
| [`opt-out-compliance.md`](./opt-out-compliance.md) | opt-out races, stale consent imports, in-flight promotional cancellation |
| [`security-and-compliance.md`](./security-and-compliance.md) | SSRF via webhooks, provider secret leakage, cross-tenant evidence access |
| [`operations.md`](./operations.md) | queue backlog, callback ingestion outage, migration under live traffic |

## Edge-Case Documentation Standard

Every scenario file captures:
1. Trigger and failure manifestation
2. Mermaid interaction or recovery diagram
3. Invariants that must hold during degradation
4. Operational acceptance criteria for drills and monitoring

## Cross-Cutting Guardrails

- Accepted messages are never silently dropped, even when downstream providers are unhealthy.
- Compliance decisions remain authoritative during retries, failover, and replay.
- Recovery workflows must preserve message lineage and operator audit history.

---

**Status**: Complete  
**Document Version**: 2.0
