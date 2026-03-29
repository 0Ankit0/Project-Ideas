# Backend Status Matrix

| Capability | Service/Module | Dev | Stage | Prod | API Readiness | Test Coverage | Rollback Ready | Owner |
|---|---|---|---|---|---|---|---|---|
| Asset catalog and inventory | `inventory-service` | ✅ | ✅ | ⏳ | v1 stable | Integration + contract | ✅ | Platform Eng |
| Availability and reservations | `booking-service` | ✅ | ✅ | ⏳ | v1 stable | Concurrency + E2E | ✅ | Booking Team |
| Contracts and e-signature | `contract-service` | ✅ | ⏳ | ⏳ | v1 beta | Workflow + audit | ⏳ | Core Domain |
| Billing and invoicing | `billing-service` | ✅ | ✅ | ⏳ | v1 stable | Ledger + reconciliation | ✅ | Finance Eng |
| Returns and inspections | `returns-service` | ✅ | ⏳ | ⏳ | v1 beta | State-machine tests | ⏳ | Ops Platform |
| Claims and disputes | `claims-service` | ✅ | ⏳ | ⏳ | v0.9 | Policy + approval flow | ⏳ | Trust & Safety |
| Notifications | `notification-service` | ✅ | ✅ | ✅ | v1 stable | Provider failover tests | ✅ | Communications |

## Sector Specialization Notes
- **Property rental**: add lease amendment and utility settlement checks.
- **Vehicle rental**: add mileage/fuel telemetry ingestion readiness.
- **Equipment rental**: add serial-level asset return verification.
## Implementation-Specific Addendum: Execution readiness tracking

### Domain-level decisions
- Add release gates tied to lifecycle, payment, and operations reliability criteria.
- Capture booking lifecycle transition metadata (`actor`, `reason_code`, `request_id`, `policy_version`) for auditability.
- Keep pricing and deposit calculations reproducible from immutable snapshots to support dispute handling.

### Failure handling and recovery
- Define explicit compensation steps for payment success + booking write failure, including replay and operator tooling.
- Record availability conflict outcomes with deterministic winner selection and customer alternative suggestions.
- For maintenance interruptions, document swap/refund decision matrix with SLA-based customer communications.

### Implementation test vectors
- Concurrency: 50+ parallel hold requests on same asset/time window with deterministic outcomes.
- Financial: partial deposit capture + late fee + damage adjustment with tax correctness.
- Operations: offline check-in/check-out replay with out-of-order events and final state convergence.
