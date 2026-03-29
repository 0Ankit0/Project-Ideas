# Backend Status Matrix

## Capability Readiness

| Capability | Service/Module | Status | Gaps to Close | Exit Criteria |
|---|---|---|---|---|
| Receiving validation | receiving-service / `receipt_command` | Planned | ASN tolerance policy wiring, discrepancy queue | Successful receive + mismatch path integration tests |
| Putaway tasking | receiving-service / `putaway_planner` | Planned | idempotent task generation and route optimizer | Duplicate submission test passes |
| Allocation engine | allocation-service / `reservation_engine` | In Progress | conflict retry and FEFO policy scoring | No negative ATP under concurrency test |
| Wave planning | allocation-service / `wave_planner` | In Progress | zone balancing and backpressure controls | Wave release stable under peak simulation |
| Pick confirmation | fulfillment-service / `pick_handler` | Planned | reservation guard + short-pick branch | Short-pick creates reallocation/backorder deterministically |
| Pack reconciliation | fulfillment-service / `pack_reconciler` | Planned | mismatch hold queue and repack API | Cannot close pack on line mismatch |
| Shipping confirm | shipping-service / `shipment_confirm` | Planned | carrier circuit breaker + retry worker | Exactly-once shipment confirmation event |
| Exception workflow | operations-service / `case_manager` | Planned | override evidence validation and SLA metrics | Override audit evidence complete |
| Audit and observability | platform / `audit_pipeline` | In Progress | unified correlation search and latency SLO board | 100% command audit coverage |

## Rule Coverage Matrix

| Rule ID | Primary Module | Test Suite |
|---|---|---|
| BR-1 | API authz + schema validators | `tests/security_validation/*` |
| BR-2 | state guard library | `tests/state_transitions/*` |
| BR-3/BR-4 | operations approval workflow | `tests/override_controls/*` |
| BR-5 | idempotency + outbox modules | `tests/idempotency_and_replay/*` |
| BR-6 | receiving command handler | `tests/receiving/*` |
| BR-7 | reservation engine + pick handler | `tests/allocation_picking/*` |
| BR-8 | pack reconciler | `tests/packing/*` |
| BR-9 | shipment confirm module | `tests/shipping/*` |
| BR-10 | exception case manager | `tests/exception_paths/*` |

## Release Readiness Gates
- Green on unit/integration/contract test suites.
- No P1/P2 open defects for receiving/picking/packing/shipping flows.
- Operational dashboards and on-call runbooks signed off.
