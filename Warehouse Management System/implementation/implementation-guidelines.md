# Implementation Guidelines

## Overview and Guiding Principles

This document defines the phased delivery plan, technical standards, coding conventions, and test coverage requirements for the Warehouse Management System. All implementation decisions are governed by the following principles:

1. **Correctness before performance:** Inventory accuracy is non-negotiable. Every mutation must be transactional, idempotent, and auditable before performance optimisation is applied.
2. **Domain model owns invariants:** Business rules live in domain aggregates, not in API handlers, database triggers, or worker scripts. Services orchestrate; aggregates enforce.
3. **Event-driven integration:** Cross-service communication uses domain events on Kafka. No synchronous cross-service calls on the critical pick/pack/ship path.
4. **Idempotency everywhere:** Every mutating endpoint and every async worker must be idempotent. Duplicate requests (retries, replays) must produce the same outcome without duplicate side effects.
5. **Outbox-first event publication:** Domain events are written to the outbox table atomically with the state change. The OutboxRelay worker forwards them to Kafka. Direct Kafka produce from command handlers is prohibited.
6. **Test coverage as a delivery gate:** Each phase has a minimum coverage target. No phase exits without the specified coverage and integration test suites passing in CI.

---

## Phase 1: Foundation (Weeks 1–4)

### Week 1–2 Deliverables

**Warehouse & Location Master Data**
- Warehouse CRUD API with multi-warehouse support (warehouse_id as partition key everywhere).
- Zone management: zone types (RECEIVING, STORAGE, PICKING, STAGING, SHIPPING), temperature class, hazmat flag.
- Aisle / Bay / Level / Position hierarchy with physical dimension attributes.
- Bin management: capacity (volume, weight), SKU compatibility rules, zone assignment.
- Bin capacity rules engine: putaway eligibility checks per SKU class and bin type.

**SKU & Product Master**
- SKU Master API: create/update/archive SKU with attributes (UOM, dimensions, weight, temperature class, hazmat flag, rotation policy override).
- Product barcode registration (GS1-128, QR, SSCC support).
- Lot tracking configuration per SKU (lot-tracked, serial-tracked, or neither).
- SKU compatibility rules for mixed-SKU bin storage.

**Employee & Device Management**
- Employee profile: role assignment (RECEIVER, PICKER, PACKER, SHIPPING_COORD, SUPERVISOR, ADMIN).
- Scanner device registration and assignment to employee + zone.
- Forklift device registration.
- Employee shift schedule (used by wave planner for capacity).

**Authentication & Authorization**
- JWT issuance with warehouse-scoped claims `{warehouse_id, role, employee_id}`.
- RBAC middleware: role-based endpoint guards (table: endpoint → minimum role).
- Refresh token rotation with 8-hour access token TTL.
- Service-to-service auth: shared JWT signing key with separate `service` claim.

**Exit Criteria — Week 1–2:**
- All master data CRUD endpoints pass integration tests.
- RBAC blocks unauthorized access (verified by security tests).
- Warehouse + Zone + Bin hierarchy query returns correct bin list in <50ms for 10,000 bins.
- Unit test coverage ≥ 80%.

### Week 3–4 Deliverables

**Receiving Orders & ASN Validation**
- ASN intake API (manual entry + EDI 856 translation adapter).
- ASN line validation: PO line match, SKU existence check, lot expiry check, quantity tolerance (configurable per supplier).
- Receipt recording: write receipt, receipt lines, inventory ledger entry, outbox event atomically.
- Discrepancy case creation with severity classification (MINOR, MAJOR, CRITICAL).
- Supervisor discrepancy workflow: review, override with evidence, reject (trigger recount).

**Putaway Planning**
- Putaway rule engine: zone affinity by SKU class, temperature matching, hazmat isolation, FIFO bin fill.
- Putaway task generation with idempotent task IDs (receipt_id + line_number hash).
- Scanner putaway confirmation: scan bin barcode, confirm quantity, update inventory balance.
- Putaway task retry on bin occupied: automatic reassignment to next eligible bin.

**Dependencies:**
- PostgreSQL schema deployed (V1 migration: warehouse, zone, aisle, bin, sku_master, employees, asn, receipts, receipt_lines, putaway_tasks, inventory_ledger, inventory_balances, outbox).
- Redis cluster running (SKU cache, bin capacity cache).
- API Gateway configured with JWT auth plugin.
- OutboxRelay worker deployed and processing outbox table.

**Exit Criteria — Week 3–4:**
- Receive a pallet against ASN, including discrepancy path, passes end-to-end integration test.
- Putaway task idempotency test: duplicate submission returns existing task without side effects.
- Inventory ledger entry created for every receipt line (verified by reconciliation check).
- Unit test coverage ≥ 80%; integration test coverage ≥ 60%.

---

## Phase 2: Core Features (Weeks 5–10)

### Week 5–6: Inventory Management

**Inventory Balance & Ledger**
- Real-time balance API: on_hand, reserved, available per SKU+Lot+Bin.
- ATP (Available-to-Promise) query API: aggregate available across all bins for a SKU (warehouse-wide or zone-scoped).
- Inventory ledger: immutable append-only record of every mutation with actor_id, correlation_id, reason.
- Balance cache in Redis: SET on every mutation; TTL 5 minutes; explicit invalidation on adjustment.
- Manual adjustment API (role: SUPERVISOR): reason codes, variance threshold enforcement, outbox event.
- Lot tracking queries: all bins containing a specific lot (for recall/quarantine scenarios).
- Serial number tracking queries: locate unit by serial number.

**Exit Criteria — Week 5–6:**
- ATP query returns correct value under concurrent reservation simulation (10 concurrent goroutines, no negative ATP).
- Ledger reconciliation job: sum(ledger deltas) == current balance for all SKUs (verified).
- Redis cache invalidation test: balance update reflected in cache within 100ms.
- Unit test coverage ≥ 85%; integration ≥ 65%.

### Week 7–8: Allocation Engine

**Reservation System**
- Reservation creation: SELECT FOR UPDATE on inventory_balances, decrement available, insert reservation record.
- Optimistic lock retry: 3 attempts with 50ms exponential backoff on lock contention.
- FIFO policy: select bins ordered by receipt_date ASC.
- FEFO policy: select bins ordered by lot expiry_date ASC.
- LIFO policy (configurable per SKU class): receipt_date DESC.
- Custom scoring: weighted combination of expiry proximity, bin travel distance, bin fullness.
- Reservation release: triggered by pick confirmation, order cancellation, or force-release (SUPERVISOR role).
- Reservation TTL: configurable per SKU class; expired reservations released by background cleanup job.

**Conflict Resolution**
- Double-reservation guard: idempotency key = hash(order_line_id + sku_code + qty). Returns existing reservation if duplicate.
- Partial allocation: if insufficient stock, allocate partial + emit backorder event to OMS.
- ATP negative-attempt guard: ATP check before lock acquisition; rejects if unavailable without lock overhead.

**Exit Criteria — Week 7–8:**
- No negative ATP under concurrent reservation load test (100 RPS, 5 workers).
- FEFO policy orders bins correctly (verified by unit tests with controlled lot data).
- Force-release requires SUPERVISOR role (verified by security test).
- Unit ≥ 85%; integration ≥ 70%; contract test for OMS backorder callback.

### Week 9–10: Wave Planning

**Wave Planning & Pick List Generation**
- Wave candidate builder: group reservations by zone, apply batch size limits (configurable, default 200 lines/wave).
- Zone balancing: distribute lines evenly across zone workers within a wave.
- Priority tiers: EXPEDITE > STANDARD > BULK; waves planned in priority order.
- Wave approval: SUPERVISOR must approve wave before release (configurable — can be auto-approved for STANDARD tier).
- Pick list generation: one PickList per zone per wave; PickLines sorted by bin sequence for optimised travel.
- Scanner task assignment: round-robin assignment to available scanners in zone.
- Short-pick handling: if bin quantity insufficient at scan time, create ShortPickException, trigger reallocation event.

**Exit Criteria — Week 9–10:**
- Wave stable under peak simulation (500 lines/wave, 3 zones, 10 concurrent scanners).
- Short-pick reallocation event triggers allocation retry (verified by integration test).
- Pick list bin sequence reduces simulated travel distance by ≥ 20% vs random order (benchmark test).
- Unit ≥ 85%; integration ≥ 70%; chaos test: worker crash mid-wave, verify tasks reassigned on restart.

---

## Phase 3: Advanced Features (Weeks 11–16)

### Week 11–12: Packing, Shipping, and Carrier Integration

**Pack Reconciliation**
- Pack session lifecycle: OPEN → PACKING → RECONCILED → CLOSED.
- Pick-to-pack reconciliation: all expected PickTasks must be in CONFIRMED or SHORT_PICKED state before close.
- Container barcode validation: pre-printed label required; duplicate container barcodes rejected.
- Weight validation: actual weight within ±5% of system-calculated weight; discrepancy triggers hold.
- Pack session close: emit pack-closed event → trigger label generation worker.

**Carrier Label Generation**
- Carrier router: FedEx, UPS, DHL adapters behind circuit breaker.
- Label request: build carrier-specific API payload from shipment address + container dimensions.
- Label storage: PDF stored in S3 `labels/{shipment_id}/{tracking_number}.pdf`.
- Tracking label record: insert into tracking_labels table with S3 key.
- Fallback queue: carrier timeout → label_retry_queue → LabelWorker retries every 60 seconds.

**Shipment Confirmation & Manifesting**
- Manifest builder: aggregate containers per carrier route into manifest.
- Shipment confirmation: requires valid tracking number + label stored in S3.
- OMS callback: POST shipment-confirmed with tracking number; retry 3× with backoff.
- End-of-day manifest close: batch all confirmed shipments for carrier pickup.

**Exit Criteria — Week 11–12:**
- Exactly-once shipment confirmation event (verified by idempotency replay test).
- Carrier timeout handled without blocking pick/pack flow (circuit breaker test).
- Label stored in S3 and presigned URL resolvable (verified by integration test).
- Unit ≥ 85%; integration ≥ 75%; contract test for all 3 carrier adapters.

### Week 13–14: Cycle Counting & Variance Management

**Cycle Count Scheduler**
- Scheduled cycle counts: zone-based schedule (e.g., each zone counted once per week).
- Ad-hoc cycle count: triggered by supervisor or by balance anomaly detection.
- Count sheet generation: expected quantities from inventory_balances at count initiation time.

**Count Execution & Variance Approval**
- Scanner count recording: scan bin + enter counted quantity; supports multiple re-scans per bin.
- Variance calculation: counted_qty − system_qty; classify as MINOR (<$100), MAJOR ($100–$500), CRITICAL (>$500).
- MINOR variances: auto-approved (configurable).
- MAJOR/CRITICAL variances: require SUPERVISOR approval with reason code.
- Approved adjustment: atomic write to inventory_ledger + inventory_balances + outbox event.

**Exit Criteria — Week 13–14:**
- Variance approval workflow enforces threshold rules (unit + integration tests).
- Adjustment atomicity: no partial adjustments on failure (verified by fault injection test).
- Unit ≥ 85%; integration ≥ 75%.

### Week 15–16: Replenishment, Crossdocking, and Returns

**Replenishment**
- Low-stock trigger: consume balance-updated events; compare to per-SKU/bin minimum quantity rule.
- Replenishment task deduplication: only one open task per SKU+bin.
- Task execution: operator scans from bulk storage bin + destination pick face bin.
- Balance update: deduct from source bin; add to destination bin atomically.

**Cross-Docking**
- Crossdock rule: SKU flagged for crossdock bypasses putaway; routes directly to staging/shipping.
- ASN-to-order matching: inbound ASN matched to outstanding order at receiving time.
- Crossdock task: generated in parallel with receiving confirmation.

**Returns Processing**
- Return order creation: requires reference to confirmed shipment; validates return quantities.
- Return receiving: scan returned items, record condition (GOOD, DAMAGED, DEFECTIVE).
- Disposition: RESTOCK (re-enters inventory), QUARANTINE (held), DESTROY (write-off).
- Balance update: RESTOCK path triggers inventory ledger entry + balance update.

**Exit Criteria — Week 15–16:**
- Replenishment task not duplicated on concurrent low-stock events (concurrency test).
- Returns restock path correctly increases inventory balance (integration test).
- Unit ≥ 85%; integration ≥ 75%.

---

## Phase 4: Production Hardening (Weeks 17–20)

### Week 17–18: Performance Optimisation and Load Testing

- PostgreSQL query analysis: EXPLAIN ANALYZE for all critical queries; add missing indexes.
- Partition pruning validation: confirm warehouse_id partition pruning active on all major tables.
- PgBouncer pool sizing: calibrate pool size to peak concurrency load.
- Redis pipeline batching: batch multi-key reads (ATP checks for wave planning).
- Connection pool tuning: max_conns per service pod calibrated against DB max_connections.
- Load test: 1,000 picks/minute, 500 reservations/minute, 100 shipments/minute sustained for 30 minutes.
- p99 latency targets: ATP query <10ms, pick confirm <100ms, wave plan <2s for 200-line wave.

### Week 19–20: Observability, Security Audit, and DR Testing

**Observability**
- Grafana dashboards: receiving mismatch rate, ATP conflicts/hour, wave cycle time, shipment retry rate, DLQ depth.
- Prometheus alerts: DLQ depth >100, event lag >60s, ATP negative-attempt rate >0, p99 >SLO threshold.
- Distributed tracing: X-Ray trace IDs propagated from API Gateway through all service calls.
- Runbooks: carrier outage failover, scanner offline recovery, outbox replay, wave reopen procedure.

**Security Audit**
- OWASP Top 10 scan on all API endpoints.
- IAM least-privilege audit: each service role has only required permissions.
- KMS key rotation schedule verified.
- Secrets Manager rotation enabled for all DB credentials.

**DR Testing**
- RDS failover drill: promote read replica; verify services reconnect within 30 seconds.
- Kafka partition leader failover: verify consumer group rebalance completes within 60 seconds.
- Redis eviction under memory pressure: verify balance cache rebuilds correctly from PG.
- Full DR scenario: failover to DR region, run acceptance test suite.

**Exit Criteria — Phase 4:**
- All SLOs met under load test (p99 ATP <10ms, pick <100ms, shipment <500ms).
- Zero P1/P2 defects open.
- All runbooks signed off by operations lead.
- DR drill completed with RTO <30 minutes.
- Security audit findings ≤ 2 LOW severity, zero MEDIUM/HIGH/CRITICAL.

---

## Technology Stack Decisions

| Component | Choice | Rationale | Alternatives Considered |
|---|---|---|---|
| API Language | Go 1.22 | High throughput, low latency, compiled binary, native goroutine concurrency | Java/Spring (heavier runtime), Node.js (GC pauses) |
| Web Framework | Gin | Minimal overhead, fast router, middleware ecosystem | Echo (comparable), Fiber (less mature ecosystem) |
| Database | PostgreSQL 15 | ACID, partitioning, JSONB, row-level locks for inventory | MySQL 8 (weaker partition pruning), MongoDB (no ACID multi-doc) |
| Connection Pool | PgBouncer (transaction mode) | Reduces DB connection overhead; compatible with prepared statements | pgx pool (per-service, simpler but no cross-pod pooling) |
| Cache | Redis 7 Cluster | Sub-ms reads, Lua scripting for atomic ops, Redlock for distributed locks | Memcached (no Lua, no data types), Hazelcast (JVM dependency) |
| Event Bus | Apache Kafka (MSK) | Durable, replayable, high-throughput, exactly-once consumer semantics | RabbitMQ (not replayable), SQS (per-message cost at scale) |
| Auth | JWT + Auth0 | Stateless, warehouse-scoped claims, RBAC support | Session-based (requires sticky sessions), PASETO (less tooling) |
| Container Platform | EKS (Kubernetes) | HPA, pod isolation, GitOps with ArgoCD | ECS (less flexible scheduling), bare EC2 (no orchestration) |
| IaC | Terraform + Helm | Industry standard, reproducible, environment parity | CDK (AWS-specific), Pulumi (less adoption) |

---

## Coding Standards and Patterns

**Idempotency:**
All mutating handlers accept an `Idempotency-Key` header. The key and its response are stored in a Redis hash with a 24-hour TTL. Duplicate requests return the cached response without re-executing side effects.

**Outbox Pattern:**
Domain event writes use a helper function `WriteOutboxEvent(tx, event)` that inserts into the `outbox` table within the active transaction. Direct Kafka produce from command handlers is a lint-flagged error.

**State Machine Guards:**
All aggregate state transitions use the `StateGuard.Transition(from, to, role)` function. Invalid transitions return a `DomainError{Code: INVALID_STATE_TRANSITION}`. The guard table is the single source of truth for allowed transitions.

**Domain Events:**
Aggregates emit domain events by returning a slice of `DomainEvent` from command methods. The application service is responsible for passing these to `OutboxWriter`. Aggregates never write to the outbox directly.

**Error Handling:**
Domain errors use typed error codes (`INSUFFICIENT_STOCK`, `LOT_EXPIRED`, `INVALID_STATE_TRANSITION`). API handlers translate domain errors to HTTP status codes via a central error mapper.

---

## Test Coverage Requirements

| Module | Unit % Target | Integration % Target | Contract Tests | Chaos Tests |
|---|---|---|---|---|
| warehouse-master | 85% | 70% | — | — |
| sku-master | 85% | 70% | — | — |
| auth-authz | 90% | 80% | — | — |
| receiving-validation | 90% | 80% | EDI ASN → WMS | — |
| receipt-recording | 90% | 80% | — | DB failure mid-write |
| putaway-planner | 85% | 75% | — | — |
| inventory-balance | 95% | 85% | — | Concurrent reservation storm |
| reservation-engine | 95% | 85% | OMS order release | Lock contention simulation |
| wave-planner | 90% | 80% | — | Worker crash mid-wave |
| pick-executor | 90% | 80% | — | Scanner disconnect mid-pick |
| pack-reconciler | 90% | 80% | — | — |
| label-generation | 85% | 80% | FedEx / UPS / DHL | Carrier API timeout |
| shipment-confirm | 90% | 80% | OMS callback | Outbox relay crash |
| cycle-count | 85% | 75% | — | — |
| replenishment | 85% | 70% | — | Duplicate event storm |
| returns-processor | 85% | 70% | — | — |
| outbox-relay | 90% | 85% | — | Kafka broker unavailable |

---

## CI/CD Pipeline Requirements

```
PR Merge Gate:
  - go vet + staticcheck (zero warnings)
  - Unit tests (target coverage enforced)
  - Integration tests (Docker Compose: PG + Redis + Kafka)
  - Contract tests (Pact broker verify)

Deploy to Staging:
  - All above +
  - Load test (abbreviated, 5-minute burst)
  - Smoke test suite against staging environment

Deploy to Production:
  - Staging green +
  - Manual approval gate (lead engineer)
  - Blue/green deploy (API tier) or canary (worker tier)
  - Automated rollback if error rate >1% within 10 minutes of deploy
```

---

## Performance Benchmarks and Targets

| Operation | p50 Target | p99 Target | Notes |
|---|---|---|---|
| ATP query (Redis cache hit) | <2ms | <5ms | Most frequent read in system |
| ATP query (cache miss, PG) | <10ms | <30ms | Falls through to read replica |
| Pick task confirmation | <50ms | <100ms | Includes DB write + outbox |
| Wave plan (200 lines) | <500ms | <2s | Background worker, not user-facing |
| Carrier label generation | <1s | <3s | FedEx API included |
| Shipment confirmation | <200ms | <500ms | Excludes carrier API (async) |
| Cycle count adjustment | <100ms | <300ms | Includes ledger write + outbox |
| Inventory balance update | <30ms | <80ms | PG write + Redis invalidation |
