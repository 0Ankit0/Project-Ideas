# Backend Status Matrix

## Traceability
- Delivery roadmap: [`./implementation-guidelines.md`](./implementation-guidelines.md)
- Architecture topology: [`../high-level-design/architecture-diagram.md`](../high-level-design/architecture-diagram.md)
- Detailed orchestration: [`../detailed-design/delivery-orchestration-and-template-system.md`](../detailed-design/delivery-orchestration-and-template-system.md)

## Service Readiness Matrix

| Service | Scope | Core readiness | Test readiness | Operational readiness | Notes |
|---|---|---|---|---|---|
| notification-api | send/status/schedule/cancel APIs | designed | contract tests required | gateway limits + RBAC runbooks required | depends on auth + policy |
| template-service | template CRUD, approval, publish | designed | renderer/schema tests required | approval audit dashboards required | locale fallback critical |
| preference-service | consent, suppression, quiet hours | designed | policy regression tests required | legal evidence export required | blocks dispatch eligibility |
| delivery-orchestrator | queueing, state transitions, retry, failover | designed | integration + chaos tests required | P0 lane SLO dashboards required | canonical message state owner |
| dispatch-workers | channel execution workers | designed | provider adapter tests required | queue lag + saturation alerts required | scale by priority lane |
| provider-adapter-fleet | email, SMS, push, webhook connectors | partially implemented | per-provider contract tests required | route health dashboards required | roll out by channel |
| callback-ingestion | webhook/poll reconciliation | designed | signature/replay tests required | delayed-callback alerting required | security-sensitive surface |
| analytics-pipeline | delivery funnels and provider metrics | planned | reconciliation tests required | warehouse lag monitoring required | can lag behind hot path |
| audit-export-service | compliance evidence and exports | planned | export integrity tests required | immutable retention verification required | required before regulated GA |

## Definition of Ready for Production

- Critical-path services (`notification-api`, `preference-service`, `delivery-orchestrator`, `dispatch-workers`) have SLOs, dashboards, and on-call ownership.
- Provider adapter coverage includes at least one production-grade adapter per core channel.
- Replay tooling exists with approval workflow before enabling self-service DLQ recovery.

## Readiness Gate Definitions

| Gate | Meaning |
|---|---|
| Core readiness | design and ownership are stable enough to implement without major boundary churn |
| Test readiness | automated contract/integration/chaos coverage expectations are defined |
| Operational readiness | alerts, runbooks, SLOs, and escalation paths exist for production support |

## Operational acceptance criteria

- Status in this matrix is updated from real implementation evidence, not only design intent.
- Any service marked `planned` or `partially implemented` must be called out in project-level rollout and scope decisions.
- A service cannot be called GA-ready unless all three readiness columns are satisfied.
