# Backend Status Matrix

| Capability | Module | Dev | Stage | Prod | API Contract | Data Readiness | Test Gate | Owner |
|---|---|---|---|---|---|---|---|---|
| Catalog & availability | `catalog-service` | ✅ | ✅ | ⏳ | v1 locked | Seed + migration ready | Contract + load | Core Platform |
| Reservation orchestration | `reservation-service` | ✅ | ✅ | ⏳ | v1 locked | Conflict model ready | Concurrency + E2E | Booking Team |
| Fulfillment operations | `fulfillment-service` | ✅ | ⏳ | ⏳ | v1 beta | Event replay ready | Workflow + offline sync | Ops Engineering |
| Settlement & billing | `settlement-service` | ✅ | ⏳ | ⏳ | v1 beta | Reconciliation pipelines ready | Ledger + exception tests | Finance Eng |
| Incident/dispute | `incident-service` | ✅ | ⏳ | ⏳ | v0.9 | Evidence retention baseline | Policy + approval tests | Trust & Safety |

## Go-Live Risks to Burn Down
- Backpressure handling under flash-demand bursts.
- Manual-review SLA for high-value disputes.
- Cross-region failover for critical reservation writes.
