# Backend Status Matrix

Current implementation status and operational readiness gates per service.

## Traceability
- Requirements: [`../requirements/requirements.md`](../requirements/requirements.md)
- Detailed APIs: [`../detailed-design/api-design.md`](../detailed-design/api-design.md)
- Implementation policy: [`./implementation-guidelines.md`](./implementation-guidelines.md)

| Service | Domain | Build Status | Test Coverage | SLO Defined | Runbook | Rollback Tested | Promotion Eligible | Primary next milestone |
|---|---|---|---:|---|---|---|---|---|
| auth-service | identity, sessions, RBAC | ✅ | 86% | ✅ | ✅ | ✅ | ✅ | add delegated admin + SCIM sync |
| app-service | applications, env vars, domains | ✅ | 83% | ✅ | ✅ | ✅ | ✅ | complete app template catalog |
| deploy-service | builds, rollouts, rollback orchestration | ✅ | 81% | ✅ | ✅ | ✅ | ✅ | add multi-cluster canary analysis |
| runtime-controller | autoscaling, placement, quotas | ✅ | 79% | ✅ | ✅ | ✅ | ⚠️ pending coverage waiver | close capacity planner integration gap |
| billing-service | usage metering, invoices, budgets | ✅ | 82% | ✅ | ✅ | ✅ | ✅ | finalize credits and refunds workflow |
| obs-gateway | logs, metrics, traces, alerts | ✅ | 84% | ✅ | ✅ | ✅ | ✅ | add per-tenant alert templates |
| build-orchestrator | runtime detection, worker scheduling, provenance | ✅ | 80% | ✅ | ✅ | ✅ | ✅ | introduce hermetic build mode |
| domain-manager | DNS, certificate lifecycle, edge config | ✅ | 78% | ✅ | ✅ | ✅ | ⚠️ staged rollout only | expand ACME failure simulations |
| addon-broker | database/cache/storage provisioning | ✅ | 77% | ✅ | ✅ | ✅ | ⚠️ pilot tenants only | add backup restore self-service |
| audit-event-pipeline | compliance evidence and platform audit trail | ✅ | 88% | ✅ | ✅ | ✅ | ✅ | move to immutable retention bucket |

## Promotion Workflow Invariants
- A service with failed rollback validation is blocked from production promotion.
- Coverage waivers require explicit approval and expiry date.
- A service marked `staged rollout only` may serve pilot tenants but cannot become the default path until readiness gaps close.

## Operational acceptance criteria
- Matrix is regenerated daily from CI metadata.
- Any `⚠️` entry creates an issue with owner and due date.
- Promotion status is reconciled against rollout controller policy, not updated manually in the document alone.

## Readiness gate definitions

| Gate | Definition |
|---|---|
| Build Status | mainline build and packaging pipeline green on immutable artifacts |
| Test Coverage | automated coverage meets or exceeds agreed threshold for critical paths |
| SLO Defined | service has latency, availability, and error-budget objectives |
| Runbook | on-call procedure exists for primary incidents and failover steps |
| Rollback Tested | previous revision restoration has been exercised in staging or prod-like environment |
| Promotion Eligible | service may participate in standard production rollout without exception |

---

**Status**: Complete  
**Document Version**: 2.1
