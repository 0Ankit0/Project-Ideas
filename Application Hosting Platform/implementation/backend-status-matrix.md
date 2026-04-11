# Backend Status Matrix

Current implementation status and operational readiness gates per service.

## Traceability
- Requirements: [`../requirements/requirements.md`](../requirements/requirements.md)
- Detailed APIs: [`../detailed-design/api-design.md`](../detailed-design/api-design.md)
- Implementation policy: [`./implementation-guidelines.md`](./implementation-guidelines.md)

| Service | Build Status | Test Coverage | SLO Defined | Runbook | Rollback Tested | Promotion Eligible |
|---|---|---:|---|---|---|---|
| auth-service | ✅ | 86% | ✅ | ✅ | ✅ | ✅ |
| app-service | ✅ | 83% | ✅ | ✅ | ✅ | ✅ |
| deploy-service | ✅ | 81% | ✅ | ✅ | ✅ | ✅ |
| runtime-controller | ✅ | 79% | ✅ | ✅ | ✅ | ⚠️ pending coverage waiver |
| billing-service | ✅ | 82% | ✅ | ✅ | ✅ | ✅ |
| obs-gateway | ✅ | 84% | ✅ | ✅ | ✅ | ✅ |

## Promotion Workflow Invariants
- A service with failed rollback validation is blocked from production promotion.
- Coverage waivers require explicit approval and expiry date.

## Operational acceptance criteria
- Matrix is regenerated daily from CI metadata.
- Any `⚠️` entry creates an issue with owner and due date.

---

**Status**: Complete  
**Document Version**: 2.0
