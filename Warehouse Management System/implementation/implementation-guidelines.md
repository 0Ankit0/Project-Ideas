# Implementation Guidelines

## Service Ownership Model

| Domain Capability | Primary Service | Supporting Components |
|---|---|---|
| Receiving & Putaway | `receiving-service` | scanner gateway, discrepancy handler |
| Allocation & Waves | `allocation-service` | wave planner worker, reservation engine |
| Picking & Packing | `fulfillment-service` | task dispatcher, pack reconciler |
| Shipping | `shipping-service` | carrier adapter, manifest retry worker |
| Exceptions & Overrides | `operations-service` | case workflow, approval policy engine |

## Coding and Data Guidelines
- All mutating handlers must implement idempotency middleware.
- Command handlers must emit structured audit events on success and rule violation.
- Domain events are published only from committed outbox records.
- State transitions must use centralized guard library (shared rule engine).

## Delivery Plan (Implementation Ready)
1. **Phase 1:** Receiving + putaway + discrepancy cases.
2. **Phase 2:** Allocation + wave planning + reservation protections.
3. **Phase 3:** Pick/pack reconciliation and short-pick handling.
4. **Phase 4:** Shipping confirmation, carrier resilience, and observability hardening.

## Required Automated Tests
- Unit tests for rule guards (BR-1..BR-10 coverage).
- Integration tests for transactional boundaries (`reserve_inventory`, `confirm_pick`, `confirm_shipment`).
- Contract tests for OMS/carrier integrations.
- Chaos tests for worker crash and replay scenarios.

## Observability and Operations
- Dashboards: receiving mismatch rate, reservation conflicts, pack blocks, shipment retries.
- Alerts: DLQ depth, event lag, ATP negative-attempt guard triggers.
- Runbooks: replay, backfill, carrier outage failover, scanner offline recovery.
