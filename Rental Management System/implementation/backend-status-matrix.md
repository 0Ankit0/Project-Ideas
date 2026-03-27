# Backend Status Matrix - Rental Management System

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
