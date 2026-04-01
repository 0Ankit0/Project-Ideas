# Backend Status Matrix

## Overview

This matrix tracks implementation readiness for all backend modules across the eight WMS services. Status values: **PLANNED** (not started), **IN_PROGRESS** (actively being built), **COMPLETE** (feature complete, tests passing), **BLOCKED** (cannot proceed — blocking issue documented). Coverage percentages reflect current CI test run results.

---

## Module Readiness Matrix

| Module Name | Service | Status | Unit % | Integ % | Blocking Issues | Exit Criteria | Owner |
|---|---|---|---|---|---|---|---|
| warehouse-master | operations-service | PLANNED | 0% | 0% | None | CRUD tests pass; partition by warehouse_id verified | TBD |
| zone-bin-management | operations-service | PLANNED | 0% | 0% | None | Bin capacity rules engine integrated | TBD |
| sku-master | inventory-service | PLANNED | 0% | 0% | None | SKU create/update/archive with barcode registration | TBD |
| employee-management | operations-service | PLANNED | 0% | 0% | None | Role assignment + scanner device registration | TBD |
| auth-authz | auth-service | PLANNED | 0% | 0% | None | JWT issuance; RBAC blocks all unauthorized endpoints | TBD |
| receiving-validation | receiving-service | PLANNED | 0% | 0% | ASN tolerance policy wiring | ASN mismatch integration test passes | TBD |
| receipt-recording | receiving-service | PLANNED | 0% | 0% | None | Atomic write: receipt + ledger + outbox | TBD |
| discrepancy-handler | receiving-service | PLANNED | 0% | 0% | None | Supervisor workflow test; override with evidence | TBD |
| putaway-planner | receiving-service | PLANNED | 0% | 0% | Idempotent task generation | Duplicate submission returns existing task | TBD |
| putaway-executor | receiving-service | PLANNED | 0% | 0% | None | Scanner confirm putaway; balance updated | TBD |
| inventory-balance | inventory-service | IN_PROGRESS | 45% | 20% | None | No negative ATP under concurrent load test | TBD |
| inventory-ledger | inventory-service | IN_PROGRESS | 40% | 15% | None | Ledger reconciliation: sum(deltas) == balance | TBD |
| reservation-engine | allocation-service | IN_PROGRESS | 50% | 25% | Conflict retry + FEFO policy scoring | No negative ATP; concurrency test passes | TBD |
| wave-planner | allocation-service | IN_PROGRESS | 35% | 10% | Zone balancing and backpressure controls | Wave release stable under 500-line peak | TBD |
| wave-release | wave-service | PLANNED | 0% | 0% | Depends on wave-planner | Pick lists generated on release | TBD |
| pick-list-generator | wave-service | PLANNED | 0% | 0% | Depends on wave-release | Zone-sorted pick list with bin sequence optimisation | TBD |
| pick-executor | fulfillment-service | PLANNED | 0% | 0% | Reservation guard + short-pick branch | Short-pick creates exception deterministically | TBD |
| short-pick-handler | fulfillment-service | PLANNED | 0% | 0% | Depends on pick-executor | Reallocation event triggered on short pick | TBD |
| pack-reconciler | fulfillment-service | PLANNED | 0% | 0% | Mismatch hold queue + repack API | Cannot close session on line mismatch | TBD |
| pack-close | fulfillment-service | PLANNED | 0% | 0% | Depends on pack-reconciler | pack-closed event emitted atomically | TBD |
| label-generation | shipping-service | PLANNED | 0% | 0% | Carrier API circuit breaker | Label stored in S3; presigned URL resolvable | TBD |
| shipment-confirm | shipping-service | PLANNED | 0% | 0% | Carrier circuit breaker + retry worker | Exactly-once shipment-confirmed event | TBD |
| carrier-adapter | shipping-service | PLANNED | 0% | 0% | FedEx/UPS/DHL contract tests | Circuit breaker triggers on timeout | TBD |
| cycle-count-scheduler | operations-service | PLANNED | 0% | 0% | None | Zone schedule generates count sheets | TBD |
| cycle-count-recorder | operations-service | PLANNED | 0% | 0% | None | Counted qty recorded per scan | TBD |
| variance-approver | operations-service | PLANNED | 0% | 0% | Threshold config per warehouse | MAJOR/CRITICAL require supervisor approval | TBD |
| replenishment-trigger | operations-service | PLANNED | 0% | 0% | Dedup logic for concurrent events | Single open task per SKU+bin | TBD |
| replenishment-executor | operations-service | PLANNED | 0% | 0% | Depends on replenishment-trigger | Balance updated in both bins atomically | TBD |
| returns-processor | operations-service | PLANNED | 0% | 0% | Disposition workflow | RESTOCK path increases balance | TBD |
| crossdock-handler | receiving-service | PLANNED | 0% | 0% | ASN-to-order matching logic | Crossdock SKU bypasses putaway | TBD |
| transfer-handler | inventory-service | PLANNED | 0% | 0% | None | Inter-zone transfer atomic; both balances updated | TBD |
| reporting-engine | reporting-service | PLANNED | 0% | 0% | Athena/Redshift query models | KPI dashboard queries <2s | TBD |
| event-bus-integration | platform | IN_PROGRESS | 60% | 30% | None | All domain events consumed by correct services | TBD |
| outbox-relay | platform | IN_PROGRESS | 65% | 40% | None | No event loss on relay restart (replay test) | TBD |
| audit-pipeline | platform | IN_PROGRESS | 50% | 20% | Unified correlation search + latency SLO board | 100% command audit coverage | TBD |

---

## Rule Coverage Matrix

| Rule ID | Rule Description | Primary Module | Test Suite | Status |
|---|---|---|---|---|
| BR-01 | ATP must never go negative | inventory-balance, reservation-engine | `tests/allocation/atp_negative_test` | IN_PROGRESS |
| BR-02 | State transitions must follow guard table | all aggregates (StateGuard) | `tests/state_transitions/*` | IN_PROGRESS |
| BR-03 | Supervisor approval required for MAJOR/CRITICAL variance | variance-approver | `tests/cycle_count/variance_approval_test` | PLANNED |
| BR-04 | Override requires evidence attachment (audit) | discrepancy-handler, variance-approver | `tests/override_controls/*` | PLANNED |
| BR-05 | Idempotency key prevents duplicate mutations | all command handlers (idempotency middleware) | `tests/idempotency/*` | IN_PROGRESS |
| BR-06 | ASN quantity within tolerance before receipt accept | receiving-validation | `tests/receiving/tolerance_test` | PLANNED |
| BR-07 | PickTask confirmation requires scan match (SKU+Lot+Bin) | pick-executor | `tests/fulfillment/scan_mismatch_test` | PLANNED |
| BR-08 | Pack session cannot close with unresolved pick lines | pack-reconciler | `tests/packing/close_guard_test` | PLANNED |
| BR-09 | Shipment confirmation requires valid tracking number + S3 label | shipment-confirm | `tests/shipping/confirm_guard_test` | PLANNED |
| BR-10 | Short pick triggers reallocation, not silent drop | short-pick-handler | `tests/fulfillment/short_pick_test` | PLANNED |
| BR-11 | Lot with expired shelf life rejected at receiving | receiving-validation | `tests/receiving/lot_expiry_test` | PLANNED |
| BR-12 | Putaway task idempotent: duplicate receipt+line returns existing task | putaway-planner | `tests/receiving/putaway_idempotency_test` | PLANNED |
| BR-13 | Reservation released on order cancel or pick confirm | reservation-engine | `tests/allocation/release_test` | IN_PROGRESS |
| BR-14 | Wave release blocked if zone has no available scanners | wave-release | `tests/wave/release_guard_test` | PLANNED |
| BR-15 | Return order requires confirmed shipment reference | returns-processor | `tests/returns/ref_validation_test` | PLANNED |
| BR-16 | Carrier circuit breaker opens after 5 failures in 10s | carrier-adapter | `tests/shipping/circuit_breaker_test` | PLANNED |
| BR-17 | Replenishment task deduplicated per SKU+bin | replenishment-trigger | `tests/replenishment/dedup_test` | PLANNED |
| BR-18 | Outbox events published exactly-once per commit | outbox-relay | `tests/platform/outbox_replay_test` | IN_PROGRESS |

---

## Integration Test Coverage

| Integration Pair | Test Description | Status | Test File |
|---|---|---|---|
| ERP → Receiving (ASN) | EDI 856 translated to WMS ASN; line validation end-to-end | PLANNED | `tests/integration/erp_asn_test` |
| Receiving → Inventory | receipt-created event triggers balance update | IN_PROGRESS | `tests/integration/receipt_balance_test` |
| OMS → Allocation | order-released event triggers reservation creation | IN_PROGRESS | `tests/integration/oms_reservation_test` |
| Allocation → Wave | reservation-created triggers wave candidate | PLANNED | `tests/integration/alloc_wave_test` |
| Wave → Fulfillment | wave-planned triggers pick list generation | PLANNED | `tests/integration/wave_picklist_test` |
| Fulfillment → Shipping | pack-closed triggers label generation | PLANNED | `tests/integration/pack_label_test` |
| Shipping → OMS | shipment-confirmed callback to OMS | PLANNED | `tests/integration/ship_oms_callback_test` |
| Operations → Inventory | cycle-count-adjusted triggers balance update | PLANNED | `tests/integration/cyclecount_balance_test` |
| Outbox → Kafka | outbox relay publishes events after commit | IN_PROGRESS | `tests/integration/outbox_kafka_test` |
| FedEx Contract | FedEx label API request/response contract | PLANNED | `tests/contract/fedex_label_test` |
| UPS Contract | UPS label API request/response contract | PLANNED | `tests/contract/ups_label_test` |
| DHL Contract | DHL label API request/response contract | PLANNED | `tests/contract/dhl_label_test` |

---

## Performance Benchmark Results

| Operation | Target p99 | Current p99 | Status | Notes |
|---|---|---|---|---|
| ATP query (Redis hit) | <5ms | Not measured | PENDING | Load test not yet run |
| ATP query (cache miss) | <30ms | Not measured | PENDING | Needs index tuning |
| Pick confirm | <100ms | Not measured | PENDING | DB write path TBD |
| Wave plan (200 lines) | <2s | Not measured | PENDING | Worker not complete |
| Carrier label generation | <3s | Not measured | PENDING | Carrier adapters TBD |
| Shipment confirmation | <500ms | Not measured | PENDING | — |
| Inventory balance update | <80ms | Not measured | PENDING | — |

---

## Known Technical Debt

| ID | Description | Severity | Module | Plan to Resolve |
|---|---|---|---|---|
| TD-001 | Outbox relay uses polling (500ms interval); HIGH event volume may cause lag | MEDIUM | outbox-relay | Migrate to PG LISTEN/NOTIFY trigger in Phase 3 |
| TD-002 | Redis balance cache TTL is fixed 5min; stale reads possible after large batch adjustments | LOW | inventory-balance | Add explicit cache invalidation on adjustment-posted event |
| TD-003 | Carrier adapter does not yet validate carrier-specific barcode formats before API call | LOW | carrier-adapter | Add format validation in Phase 3 |
| TD-004 | Wave planner travel distance optimisation uses simple bin sequence sort, not TSP | LOW | wave-planner | Replace with nearest-neighbour heuristic in Phase 4 |
| TD-005 | Manual adjustments lack reason code validation against approved enum list | LOW | inventory-balance | Add reason code table + FK in DB migration |

---

## Release Readiness Gates

| Gate | Criteria | Current State | Responsible |
|---|---|---|---|
| G1 — Unit Test Coverage | All modules ≥ 85% unit coverage | PENDING (Phase 1 not started) | Engineering Lead |
| G2 — Integration Tests Green | All integration test suites pass in CI | PENDING | QA Lead |
| G3 — Contract Tests Green | All OMS, ERP, carrier contract tests pass | PENDING | Platform Team |
| G4 — Load Test Passed | All p99 SLOs met under 30-minute peak load | PENDING | Performance Team |
| G5 — Security Audit | Zero MEDIUM/HIGH/CRITICAL findings | PENDING | Security Team |
| G6 — Runbooks Signed Off | All operational runbooks reviewed and approved | PENDING | Operations Lead |
| G7 — DR Drill Complete | Failover + RTO <30min verified | PENDING | Infrastructure Team |
| G8 — No P1/P2 Defects | Zero open P1 or P2 defects in bug tracker | PENDING | QA Lead |
