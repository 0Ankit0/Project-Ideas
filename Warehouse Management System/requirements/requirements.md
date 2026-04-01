# Requirements

## Purpose
Define implementation-ready functional and non-functional requirements for the **Warehouse Management System (WMS)**. All requirements are traceable to business rules, use cases, and design artifacts.

## Scope

### In-Scope
- Inbound operations: ASN/PO-based receiving, GRN generation, discrepancy handling, putaway task management
- Inventory management: bin-level tracking, lot/serial control, FIFO/FEFO/LIFO rotation, quarantine management
- Zone and bin management: location hierarchy (Warehouse → Zone → Aisle → Rack → Bin), capacity enforcement
- Allocation engine: demand reservation, priority-based allocation, release and de-allocation
- Wave planning: wave creation, order grouping, carrier cutoff enforcement, backpressure gating
- Picking: task assignment, scan-confirmation, short-pick handling, batch/cluster/zone picking modes
- Packing: station reconciliation, carton close, label generation, parcel manifest
- Outbound shipping: manifest confirmation, carrier label handoff, tracking event emission
- Returns and adjustments: RMA receipt, restock or quarantine routing, manual inventory adjustments
- Cycle counting: count plan generation, blind-count enforcement, variance approval workflow
- Replenishment: min/max rule evaluation, replenishment task generation, cross-zone transfer
- Integration: ERP (purchase orders, invoices), TMS/carrier APIs, barcode/RFID scanning subsystems, WCS
- Reporting: operational dashboards, SLA metrics, inventory accuracy KPIs, carrier performance reports
- 3PL multi-tenant support: client isolation, per-client billing events, configurable business rules per client

### Out-of-Scope
- Procurement and purchase order creation (owned by ERP)
- Transportation route optimization (owned by TMS)
- Customer order management and customer-facing portals (owned by OMS)
- Physical warehouse infrastructure (conveyors, sorters, WCS hardware control)
- Accounts payable and financial reconciliation (owned by ERP)
- Human resources and labor scheduling (owned by WFM system)

## Stakeholders

| Role | Primary Responsibilities |
|---|---|
| Receiving Associate | Executes ASN scanning, GRN confirmation, discrepancy reporting |
| Putaway Worker | Executes directed putaway tasks, confirms bin placement |
| Inventory Planner | Manages allocation policies, replenishment rules, cycle count schedules |
| Picker | Executes pick tasks from wave-released pick lists |
| Pack Station Operator | Reconciles picks into cartons, generates and applies labels |
| Transportation Coordinator | Confirms manifests, manages carrier handoffs, dock scheduling |
| Supervisor | Approves exceptions, variances, and overrides |
| Inventory Controller | Resolves conflicts, audits adjustments, reconciles scanner batches |
| Warehouse Manager | Configures zones, policies, SLA thresholds, and operational reports |
| System Administrator | Manages integrations, user roles, and system configuration |

---

## Functional Requirements (Implementation Ready)

### Receiving

| ID | Requirement | Acceptance Criteria | Related Rules |
|---|---|---|---|
| FR-REC-01 | System shall validate ASN/PO line, lot/serial policy, and quantity tolerances during receiving. | Invalid scans are rejected with reason code within 2 s; mismatch case is created atomically; no allocatable inventory is created on failed validation. | BR-6, BR-10 |
| FR-REC-02 | System shall generate deterministic putaway tasks after receipt confirmation. | Task priority, destination bin, and travel path are persisted; duplicate scanner submit with same idempotency key returns original task without duplication. | BR-5, BR-6 |
| FR-REC-03 | System shall support cross-docking by routing receipts directly to outbound staging when a matching open shipment order exists. | Cross-dock eligibility is evaluated at receipt line; cross-dock tasks are generated before standard putaway tasks; no bin capacity is consumed in reserve storage for cross-docked units. | BR-5, BR-6 |
| FR-REC-04 | System shall enforce quarantine flagging for items that fail QC inspection or have an active hold at receipt time. | Quarantined inventory is excluded from allocation and picking; quarantine reason and inspector identity are recorded; release requires supervisor approval. | BR-3, BR-6 |
| FR-REC-05 | System shall capture lot number, expiry date, and serial number at receipt for items under lot/serial control. | Lot-controlled items without expiry date are rejected when FEFO policy is active; serial numbers must be unique per SKU across the warehouse; duplicate serial scan returns `SERIAL_DUPLICATE` with conflicting GRN reference. | BR-6, BR-7 |
| FR-REC-06 | System shall generate a Goods Receipt Note (GRN) upon receipt confirmation and publish a `ReceivingCompleted` event. | GRN includes PO/ASN reference, received quantities per line, variance notes, operator ID, and timestamp; event is published exactly once via transactional outbox. | BR-5, BR-6 |

### Putaway

| ID | Requirement | Acceptance Criteria | Related Rules |
|---|---|---|---|
| FR-PUT-01 | Putaway engine shall assign destination bins based on SKU affinity, zone eligibility, and bin capacity constraints. | Recommended bin is never over-capacity; zone eligibility rules (temperature, hazmat class, SKU class) are enforced; travel path is optimized within the assigned zone. | BR-1, BR-5 |
| FR-PUT-02 | System shall support operator override of the suggested putaway bin subject to capacity and zone eligibility checks. | Override is audited with operator ID, original suggestion, alternate bin, and override reason; override bin must pass capacity and eligibility checks before acceptance. | BR-3, BR-5 |
| FR-PUT-03 | System shall publish a `PutawayCompleted` event upon bin confirmation and update bin inventory atomically. | Bin quantity and weight are updated within the same transaction as task closure; event includes bin_id, sku_id, lot_id, quantity, and operator_id. | BR-5 |
| FR-PUT-04 | System shall trigger a `BinCapacityExceeded` alert when a putaway task targets a bin at ≥ 95% utilization. | Alert is published before task is assigned; alternate bin is suggested; task is not assigned to the over-capacity bin without explicit supervisor override. | BR-1, BR-3 |

### Zone and Bin Management

| ID | Requirement | Acceptance Criteria | Related Rules |
|---|---|---|---|
| FR-ZBM-01 | System shall maintain a hierarchical location model: Warehouse → Zone → Aisle → Rack → Bin. | All inventory movements reference a leaf-level bin_id; zone attributes (type, temperature range, hazmat class) are enforced on all inbound and transfer operations. | BR-1 |
| FR-ZBM-02 | System shall enforce per-bin capacity constraints in units, weight, and volume. | Any transaction that would exceed a bin's capacity is rejected with `BIN_CAPACITY_EXCEEDED`; capacity attributes are configurable per bin template. | BR-1 |
| FR-ZBM-03 | System shall support bin status lifecycle: Active, Inactive, Quarantine, Maintenance. | Inactive and Maintenance bins are excluded from putaway and allocation immediately upon status change; Quarantine bins are readable but not allocatable; all status changes are audited. | BR-1, BR-3 |
| FR-ZBM-04 | System shall enforce single-SKU or mixed-SKU bin rules per zone configuration. | Single-SKU bins reject putaway of a second SKU; the violation is surfaced at task assignment time, not at scan confirmation. | BR-1 |

### Inventory Management

| ID | Requirement | Acceptance Criteria | Related Rules |
|---|---|---|---|
| FR-INV-01 | System shall maintain real-time inventory positions at bin level with on-hand, reserved, available, and quarantine quantities. | Quantity ledger satisfies the invariant: on_hand = available + reserved + quarantine at all times; any discrepancy triggers an automated reconciliation alert. | BR-7 |
| FR-INV-02 | System shall enforce inventory rotation policies (FIFO, FEFO, LIFO) per SKU or zone configuration. | Allocation and pick sequences respect the active rotation policy; FEFO selects the lot with the earliest expiry first; policy override requires supervisor role and is audited. | BR-7 |
| FR-INV-03 | System shall support manual inventory adjustments with mandatory reason code, evidence reference, and dual-approval for adjustments above a configurable threshold. | Adjustments above threshold require two approvals from distinct operator IDs; adjustment event includes before/after quantities, reason code, and evidence_ref; adjustment is atomic with event publication. | BR-3, BR-10 |
| FR-INV-04 | System shall support inter-zone and inter-warehouse inventory transfers with a two-phase commit: transfer-out confirmation followed by transfer-in confirmation. | Inventory is in `InTransit` status between confirmations; source bin is decremented on transfer-out; destination bin is incremented on transfer-in; abandoned transfers generate a supervisor alert after configurable timeout. | BR-5 |
| FR-INV-05 | System shall publish an `InventoryAdjusted` event for every stock mutation, including quantity delta, mutation type, operator, and correlation_id. | Event is published via transactional outbox; downstream consumers can reconstruct full position history from the event stream alone. | BR-5, BR-10 |

### Allocation

| ID | Requirement | Acceptance Criteria | Related Rules |
|---|---|---|---|
| FR-ALLOC-01 | Allocation engine shall reserve inventory by rotation policy (FIFO/FEFO/LIFO), zone eligibility, and customer priority tier. | Reservation never exceeds available quantity; conflicting concurrent allocations return 409 with retry token; allocation is fully atomic per order line. | BR-7 |
| FR-ALLOC-02 | System shall support partial allocation when full order quantity is unavailable, with a configurable hold-for-complete policy. | Partial allocation state is persisted; hold-for-complete prevents wave inclusion until full quantity is reserved; a backorder trigger is emitted when the hold threshold expires. | BR-7 |
| FR-ALLOC-03 | System shall release and reclaim reservations on order cancellation, customer priority change, or wave abort. | Released quantity is immediately available for subsequent allocations; a release event is published with the original reservation reference. | BR-7 |
| FR-ALLOC-04 | System shall prevent allocation of quarantined, expired, or inventory in an inactive bin. | Allocation engine filters ineligible lots and bins at query time; a quarantine status change does not retroactively cancel existing reservations but blocks all new ones. | BR-3, BR-7 |

### Wave Planning

| ID | Requirement | Acceptance Criteria | Related Rules |
|---|---|---|---|
| FR-WAVE-01 | Wave planner shall group orders into waves by carrier cutoff time, priority tier, zone cluster, and picker capacity limit. | Wave size does not exceed the configured picker capacity; carrier cutoff is the primary sort key; orders beyond the cutoff are deferred to the next wave. | BR-2, BR-5 |
| FR-WAVE-02 | System shall enforce backpressure on wave release when a downstream carrier API or WCS dependency is degraded. | Wave release is blocked and a `WaveHeld` alert is raised when the relevant circuit breaker is open; wave is auto-released when the dependency recovers and an operator confirms. | BR-5, BR-10 |
| FR-WAVE-03 | System shall publish a `WaveReleased` event upon wave activation and create pick tasks for all wave-included order lines atomically. | Pick tasks are persisted in the same transaction as wave state update; partial task creation is not permitted; wave state machine transitions: Draft → Released → Active → Closed. | BR-5 |
| FR-WAVE-04 | System shall support wave abort with automatic reservation release and requeue of constituent orders. | Aborted wave emits `WaveAborted` event; all reservations under the wave are released; orders return to allocatable state within 30 s of abort. | BR-5, BR-7 |

### Picking

| ID | Requirement | Acceptance Criteria | Related Rules |
|---|---|---|---|
| FR-PICK-01 | Pick execution shall enforce reservation references and scan confirmation for every pick action. | Pick confirm fails without an active reservation reference; scan mismatch returns `SCAN_MISMATCH` with expected vs. actual detail; no inventory movement is permitted without scan confirmation. | BR-7, BR-10 |
| FR-PICK-02 | System shall handle short picks by offering alternate-bin reallocation before triggering a backorder. | Short pick event is emitted with quantity_requested and quantity_picked; alternate bin search completes within 3 s; backorder is created only when no eligible alternate bin is available. | BR-7, BR-10 |
| FR-PICK-03 | System shall support batch, zone, and cluster picking modes configurable per wave. | Picker receives a consolidated and travel-path-sorted task list for their mode; batch pick confirms per line; cluster pick confirms per carton slot; zone pick hands off to the next zone worker. | BR-2, BR-5 |
| FR-PICK-04 | System shall enforce FEFO/FIFO lot selection at pick confirmation and reject scans of non-sequenced lots. | Scan of an out-of-sequence lot returns `LOT_SEQUENCE_VIOLATION` with the correct lot reference; supervisor override is required to bypass the sequence constraint. | BR-7 |

### Packing

| ID | Requirement | Acceptance Criteria | Related Rules |
|---|---|---|---|
| FR-PACK-01 | Packing station shall reconcile picked quantity, package content, and label payload before carton close. | Station blocks close on quantity mismatch; mismatch reason code and operator identity are captured in the audit log; partial pack requires explicit supervisor-approved justification. | BR-8, BR-10 |
| FR-PACK-02 | System shall generate carrier-compliant shipping labels (ZPL/PDF) embedding tracking number, weight, and dimensional data. | Label generation failure transitions the parcel to `PackingBlocked`; retry is available up to 3 times before escalation; label content is validated against carrier schema before printing. | BR-8, BR-9 |
| FR-PACK-03 | System shall support a repack workflow requiring dual scan and full reason capture. | Repack closes the original carton and opens a new one; both events are audited; the allocation reference is carried through to the new carton; repack is blocked after final dispatch confirmation. | BR-8, BR-10 |

### Shipping

| ID | Requirement | Acceptance Criteria | Related Rules |
|---|---|---|---|
| FR-SHIP-01 | Shipment confirmation shall finalize inventory decrement and emit a `ShipmentDispatched` event idempotently. | Inventory becomes non-reversible except via return/adjustment flow; event is published exactly once via transactional outbox; duplicate confirmation returns the original event reference without re-publishing. | BR-9, BR-5 |
| FR-SHIP-02 | System shall generate an outbound manifest per carrier load and transmit EDI/API payload to the carrier within the cutoff window. | Manifest includes all parcels with tracking numbers, weights, and dimensions; a late manifest triggers `CarrierCutoffMissed` alert; transmission retries use exponential backoff up to 10 attempts. | BR-9, BR-5 |
| FR-SHIP-03 | System shall enforce dock door assignment for outbound loads and block dispatch until door confirmation is recorded. | Dispatch action is disabled until dock_door_id is confirmed; door conflict (two loads assigned the same door simultaneously) is detected and rejected with a coordinator alert. | BR-9 |
| FR-SHIP-04 | System shall support carrier label void and reprint within the shipment window before final dispatch confirmation. | Label void invalidates tracking number with the carrier API; reprint generates a new tracking number and updates the manifest; void and reprint events are audited with actor ID and both tracking numbers. | BR-9, BR-10 |

### Returns and Adjustments

| ID | Requirement | Acceptance Criteria | Related Rules |
|---|---|---|---|
| FR-RET-01 | System shall receive returned merchandise against an RMA authorization and route items to restock or quarantine based on inspection result. | Items without RMA authorization are held in the receiving discrepancy queue; inspection result (Pass/Fail) determines routing; original shipment reference is preserved on the return record. | BR-3, BR-6 |
| FR-RET-02 | System shall support blind returns (no RMA) for configurable client accounts with mandatory exception audit and dual-approval for restocking. | Blind return creates a discrepancy record and notifies supervisor within 2 min; restocking requires two distinct approver IDs; event published with `return_type: blind`. | BR-3, BR-10 |
| FR-RET-03 | System shall allow inventory adjustments (positive, negative, with reason code) subject to configurable dual-approval thresholds. | Adjustments above threshold require two distinct approver IDs; adjustment is atomic with event publication; history is queryable by SKU, bin, date range, and actor ID. | BR-3, BR-10 |

### Cycle Counting

| ID | Requirement | Acceptance Criteria | Related Rules |
|---|---|---|---|
| FR-CC-01 | System shall generate cycle count plans by zone, ABC velocity class, or ad-hoc bin selection and publish them to assigned counters. | Plan specifies target bins, assigned operators, and count window; bins under active pick or putaway tasks are excluded; `CycleCountStarted` event is published with plan ID and assigned operators. | BR-4 |
| FR-CC-02 | System shall enforce blind counting: counters do not see expected quantities until the count is submitted. | Expected quantity field is hidden at the count screen; system-on-hand is compared to counted quantity only after submission; variance is flagged for approval if it exceeds configurable tolerance. | BR-4 |
| FR-CC-03 | System shall support a recount workflow when variance exceeds tolerance, requiring a second independent count before adjustment is committed. | Recount is assigned to a different operator; if recount confirms variance, adjustment is auto-approved within configured limit or routed to supervisor above the limit; all events are published with count_plan_id. | BR-4, BR-10 |

### Replenishment

| ID | Requirement | Acceptance Criteria | Related Rules |
|---|---|---|---|
| FR-REP-01 | System shall evaluate replenishment triggers based on min/max rules, demand forecast signals, or on-demand requests. | `ReplenishmentTriggered` event is published within 60 s of bin falling below minimum quantity; replenishment task is generated and queued; duplicate triggers for the same bin/SKU are deduplicated within the evaluation window. | BR-2, BR-5 |
| FR-REP-02 | System shall source replenishment from reserve storage, bulk zone, or cross-docking as configured per SKU and zone, filling to target (max) level without exceeding bin capacity. | Replenishment source is selected by configured priority order; quantity to replenish does not exceed destination bin remaining capacity; source bin is atomically decremented on task completion. | BR-1, BR-2 |
| FR-REP-03 | System shall defer replenishment tasks when the source bin is under active cycle count or in Maintenance status, and auto-requeue when the constraint is lifted. | Task transitions to `Deferred` with constraint reason; auto-requeue fires within 60 s of constraint removal; deferral and requeue events are audited with source constraint reference. | BR-4, BR-5 |

### Integration

| ID | Requirement | Acceptance Criteria | Related Rules |
|---|---|---|---|
| FR-INT-01 | System shall consume purchase orders and ASNs from ERP via event stream or API polling with at-least-once delivery and idempotent processing. | Duplicate PO/ASN messages are detected by document_id and silently discarded; processing failures route to DLQ with structured error payload including document_id and failure reason. | BR-5, BR-6 |
| FR-INT-02 | System shall transmit outbound inventory and shipment events to ERP within 5 minutes of state change. | Transactional outbox guarantees at-least-once delivery; ERP-bound events include correlation_id for deduplication; failed transmissions retry with exponential backoff up to 10 attempts before DLQ routing. | BR-5 |
| FR-INT-03 | System shall integrate with carrier APIs for label generation, rate shopping, and tracking status ingestion. | Carrier API timeout triggers fallback to configured secondary carrier; label generation errors surface with carrier error code; tracking status ingests at configurable polling interval or via webhook. | BR-9 |
| FR-INT-04 | System shall accept barcode (1D/2D) and RFID scan input from handheld, fixed reader, and mobile device channels with a normalized internal payload. | Offline scanner batches replay with idempotency enforcement; conflicting replay events create review tasks; scan channel is recorded on every event for diagnostics. | BR-6, BR-10 |
| FR-INT-05 | System shall expose a REST/gRPC API for all core WMS operations secured by role-based access control with per-client API key isolation. | OpenAPI 3.1 documentation is auto-generated from service contracts; all mutations require authenticated identity with minimum required role; API versioning follows semver with 90-day deprecation notice. | BR-3 |

### Reporting and Analytics

| ID | Requirement | Acceptance Criteria | Related Rules |
|---|---|---|---|
| FR-RPT-01 | System shall provide operational dashboards for: receiving throughput, putaway queue depth, pick rate, pack throughput, shipment on-time %, and inventory accuracy %. | Dashboards refresh within 60 s of underlying data change; all KPIs are filterable by warehouse, zone, date range, and client. | BR-10 |
| FR-RPT-02 | System shall generate inventory snapshot reports (on-hand, reserved, available, quarantine) exportable in CSV and JSON. | Report generation for up to 1 million records completes within 120 s; export is paginated with a resumable cursor; reports are retained for 90 days. | BR-10 |
| FR-RPT-03 | System shall produce carrier performance reports covering on-time pickup %, label error rate, and carrier-reported exceptions. | Reports are generated daily and on-demand; data is sourced from shipment events and carrier webhook ingestion; anomalies trigger automatic coordinator alerts. | BR-9 |

### Exception Handling

| ID | Requirement | Acceptance Criteria | Related Rules |
|---|---|---|---|
| FR-EXC-01 | System shall support operator override for approved exception classes with mandatory approver identity, reason code, and expiry timestamp. | Override approver must be distinct from the initiator; expired overrides auto-invalidate pending work and create follow-up tasks; override audit includes before/after state snapshot. | BR-3, BR-4, BR-10 |
| FR-EXC-02 | Every exception must map to a deterministic resolution action: hold, reallocate, backorder, or manual review. | Unresolved exceptions older than configurable SLA threshold generate supervisor escalation alerts; DLQ-routed exceptions include replay context and post-replay reconciliation reference. | BR-10 |

---

## Non-Functional Requirements

| ID | Category | Requirement | Target | Measurement Method |
|---|---|---|---|---|
| NFR-AVAIL-01 | Availability | Tier-1 API uptime (scan/confirm, allocation, shipment dispatch) | 99.9% monthly | Synthetic monitor at 30-s interval |
| NFR-AVAIL-02 | Availability | Background worker availability (wave planner, replenishment engine) | 99.5% monthly | Worker heartbeat and queue lag monitor |
| NFR-LAT-01 | Latency | P95 scan/confirm command response time | ≤ 800 ms | APM trace at API gateway |
| NFR-LAT-02 | Latency | P99 scan/confirm command response time | ≤ 1,500 ms | APM trace at API gateway |
| NFR-LAT-03 | Latency | Allocation engine reservation P95 response time | ≤ 500 ms | APM trace per allocation call |
| NFR-LAT-04 | Latency | Pick task retrieval P95 response time | ≤ 300 ms | APM trace per task fetch |
| NFR-LAT-05 | Latency | Wave release end-to-end: orders to pick tasks persisted (≤ 500 orders) | ≤ 10 s | Trace span from WaveReleased event |
| NFR-TPUT-01 | Throughput | Receiving scan confirmations sustained | ≥ 500 scans/min per warehouse | Load test at P95 |
| NFR-TPUT-02 | Throughput | Concurrent wave releases without degradation | ≥ 10 simultaneous waves | Load test with APM verification |
| NFR-TPUT-03 | Throughput | Outbound shipment events per second sustained | ≥ 200 events/s | Event pipeline load test |
| NFR-CONS-01 | Consistency | Stock mutation correctness per bin | Serializable semantics per `warehouse_id + sku_id + bin_id` key | Concurrent mutation test suite |
| NFR-CONS-02 | Consistency | Inventory ledger balance invariant | Zero tolerance for on_hand ≠ available + reserved + quarantine, detectable by reconciliation job | Nightly reconciliation report |
| NFR-SEC-01 | Security | Authentication coverage | All API endpoints require JWT or API key; anonymous access returns 401 | Penetration test, OWASP checklist |
| NFR-SEC-02 | Security | Role-based authorization | All mutations enforce RBAC; cross-client data access returns 403 | Integration test suite per role |
| NFR-SEC-03 | Security | Audit trail completeness | 100% of state-changing operations record actor_id, correlation_id, reason_code, and timestamp | Audit log coverage report |
| NFR-RET-01 | Data Retention | Operational event log retention | 2 years hot, 7 years cold archive | Data lifecycle policy; quarterly audit |
| NFR-RET-02 | Data Retention | Audit trail retention | 7 years minimum (regulatory compliance) | Data lifecycle policy |
| NFR-RET-03 | Data Retention | Report artifact retention | 90 days hot storage | Report TTL enforcement |
| NFR-DR-01 | Disaster Recovery | Recovery Point Objective (RPO) | ≤ 5 minutes | Measured at last committed database snapshot |
| NFR-DR-02 | Disaster Recovery | Recovery Time Objective (RTO) | ≤ 30 minutes | Measured from incident declaration to traffic resumption |
| NFR-SCALE-01 | Scalability | Horizontal service scaling | All stateless services scale to 10× baseline with no code changes | Auto-scale test in staging environment |
| NFR-SCALE-02 | Scalability | Database partition strategy | Write partition keys include `warehouse_id` to prevent cross-tenant hot spots | Schema review; query plan audit |
| NFR-OBS-01 | Observability | Distributed trace propagation | 100% of inbound API calls carry trace_id through all downstream services | Trace coverage report |
| NFR-OBS-02 | Observability | Structured log format | All log entries are JSON with severity, service, trace_id, and correlation_id | Log pipeline validation |
| NFR-OBS-03 | Observability | SLO breach alerting | PagerDuty alert fires within 2 minutes of SLO breach detection | Alert latency test |

---

## Acceptance Criteria — Integration Test Scenarios

### ITS-01: End-to-End Receiving to Putaway
1. Submit ASN with 3 lines; configure one line with over-tolerance quantity.
2. Confirm: first two lines generate GRN and putaway tasks; over-tolerance line creates a discrepancy case and no allocatable inventory.
3. Supervisor approves variance with reason code and distinct approver identity.
4. Execute putaway scans; verify `PutawayCompleted` event published and bin inventory incremented atomically.
5. Replay the same putaway scan with the original idempotency key; verify no duplicate task or inventory increment.

### ITS-02: Wave Release and Pick Execution with Short Pick
1. Allocate inventory for 10 orders across 3 zones.
2. Release wave; verify `WaveReleased` event and all pick tasks persisted within 10 s.
3. Execute picks for 9 orders; introduce a short pick on order 10.
4. Verify short-pick event emitted with quantity_requested and quantity_picked; alternate bin offered.
5. If no alternate: verify backorder created and wave task marked complete; reservation released for the backordered line.

### ITS-03: Pack, Ship, and Idempotent Dispatch
1. Confirm all picks for a wave; route to packing station.
2. Introduce a quantity mismatch on one carton; verify station blocks close and audit record is created.
3. Resolve mismatch; close all cartons; generate and validate carrier labels against schema.
4. Confirm shipment dispatch; verify `ShipmentDispatched` published exactly once via outbox.
5. Submit duplicate dispatch confirmation; verify idempotent response returns original event reference with no re-publish.

### ITS-04: Cycle Count with Recount and Adjustment
1. Generate cycle count plan for Zone A, bins B1–B10; verify plan appears in assigned counters' queues.
2. Submit blind counts with one bin showing a variance above tolerance threshold.
3. Verify variance flagged; recount assigned to a different operator.
4. Recount confirms the variance; verify auto-approval within the configured limit and `InventoryAdjusted` event published.
5. Verify inventory ledger satisfies the balance invariant after adjustment.

### ITS-05: Replenishment Trigger, Deduplication, and Deferral
1. Drive a pick-face bin to below minimum quantity; verify `ReplenishmentTriggered` event within 60 s.
2. Simulate a second trigger for the same bin within the evaluation window; verify deduplication.
3. Set source bin to Maintenance status; verify replenishment task transitions to `Deferred`.
4. Clear Maintenance status; verify task auto-requeues within 60 s.
5. Execute replenishment; confirm source bin decrement and destination bin increment are atomic.

### ITS-06: Offline Scanner Replay Conflict Resolution
1. Disconnect scanner; execute 3 pick confirmations offline.
2. Concurrently, an online pick runs the same bin and SKU.
3. Reconnect scanner and replay the offline batch.
4. Verify conflict detection; review task created with both conflicting event snapshots.
5. Resolve via compensating adjustment; verify audit event published and inventory projections recalculated.

---

## Traceability Matrix

| FR ID | Use Case | Design Artifact | Business Rules |
|---|---|---|---|
| FR-REC-01 | UC-REC-01: Receive Against ASN | [Receiving Flow](../design/sequence-diagrams.md#receiving) | BR-6, BR-10 |
| FR-REC-02 | UC-REC-01: Receive Against ASN | [Putaway Task Generation](../design/sequence-diagrams.md#putaway) | BR-5, BR-6 |
| FR-REC-03 | UC-REC-03: Cross-Dock Routing | [Cross-Dock Flow](../design/sequence-diagrams.md#cross-dock) | BR-5, BR-6 |
| FR-REC-04 | UC-REC-04: Quarantine at Receipt | [Quarantine Policy](../design/data-models.md#inventory-unit) | BR-3, BR-6 |
| FR-REC-05 | UC-REC-02: Lot/Serial Capture | [Lot Model](../design/data-models.md#lot) | BR-6, BR-7 |
| FR-REC-06 | UC-REC-01: Receive Against ASN | [GRN Event](../design/event-catalog.md#receiving-completed) | BR-5, BR-6 |
| FR-PUT-01 | UC-PUT-01: Directed Putaway | [Putaway Engine](../design/component-design.md#putaway-engine) | BR-1, BR-5 |
| FR-PUT-02 | UC-PUT-02: Override Suggested Bin | [Override Policy](../design/data-models.md#override) | BR-3, BR-5 |
| FR-ZBM-01 | UC-ZBM-01: Zone Configuration | [Location Hierarchy](../design/data-models.md#location) | BR-1 |
| FR-INV-01 | UC-INV-01: Inventory Inquiry | [Inventory Ledger](../design/data-models.md#inventory-unit) | BR-7 |
| FR-INV-02 | UC-INV-02: Rotation Policy | [Rotation Engine](../design/component-design.md#allocation-engine) | BR-7 |
| FR-ALLOC-01 | UC-ALLOC-01: Reserve Inventory | [Allocation Engine](../design/component-design.md#allocation-engine) | BR-7 |
| FR-ALLOC-02 | UC-ALLOC-02: Partial Allocation | [Partial Allocation Flow](../design/sequence-diagrams.md#allocation) | BR-7 |
| FR-WAVE-01 | UC-WAVE-01: Plan Wave | [Wave Planner](../design/component-design.md#wave-planner) | BR-2, BR-5 |
| FR-WAVE-04 | UC-WAVE-02: Abort Wave | [Wave State Machine](../design/component-design.md#wave-planner) | BR-5, BR-7 |
| FR-PICK-01 | UC-PICK-01: Execute Pick | [Pick Execution](../design/sequence-diagrams.md#picking) | BR-7, BR-10 |
| FR-PICK-02 | UC-PICK-02: Short Pick Handling | [Short Pick Flow](../design/sequence-diagrams.md#short-pick) | BR-7, BR-10 |
| FR-PACK-01 | UC-PACK-01: Pack Station Close | [Pack Station](../design/component-design.md#pack-station) | BR-8, BR-10 |
| FR-PACK-02 | UC-PACK-02: Label Generation | [Label Service](../design/component-design.md#label-service) | BR-8, BR-9 |
| FR-SHIP-01 | UC-SHIP-01: Dispatch Confirmation | [Shipment Dispatch](../design/sequence-diagrams.md#shipping) | BR-9, BR-5 |
| FR-SHIP-02 | UC-SHIP-02: Manifest Transmission | [Carrier Integration](../design/component-design.md#integration) | BR-9, BR-5 |
| FR-RET-01 | UC-RET-01: RMA Receipt | [Returns Flow](../design/sequence-diagrams.md#returns) | BR-3, BR-6 |
| FR-CC-01 | UC-CC-01: Count Plan Generation | [Cycle Count Engine](../design/component-design.md#cycle-count) | BR-4 |
| FR-CC-03 | UC-CC-03: Variance Approval | [Variance Workflow](../design/sequence-diagrams.md#cycle-count) | BR-4, BR-10 |
| FR-REP-01 | UC-REP-01: Replenishment Trigger | [Replenishment Engine](../design/component-design.md#replenishment) | BR-2, BR-5 |
| FR-INT-01 | UC-INT-01: ERP PO Ingest | [Integration Layer](../design/component-design.md#integration) | BR-5, BR-6 |
| FR-INT-04 | UC-INT-04: Scanner Batch Replay | [Scanner Gateway](../design/component-design.md#scanner-gateway) | BR-6, BR-10 |
| FR-INT-05 | UC-INT-05: Public API | [API Gateway](../design/component-design.md#api-gateway) | BR-3 |
| FR-RPT-01 | UC-RPT-01: Operational Dashboard | [Reporting Service](../design/component-design.md#reporting) | BR-10 |
| FR-EXC-01 | UC-EXC-01: Exception Override | [Override Workflow](../design/sequence-diagrams.md#exception-handling) | BR-3, BR-4, BR-10 |

---

## Infrastructure-Scale Requirements
- Queue-driven workers shall auto-scale on queue depth and consumer lag; scale-down grace period must be ≥ 2× the maximum processing time of a single batch to prevent task loss.
- Wave release shall enforce backpressure when the downstream carrier or WCS circuit breaker is open; no wave may be released to a degraded dependency without explicit operator acknowledgment.
- Write-path partition keys must include `warehouse_id` to prevent cross-tenant storage hot spots and support per-region data residency.
- All stateful command handlers must be idempotent, keyed on a client-supplied or system-generated idempotency key with a minimum TTL of 24 hours.
- Database connection pools must be sized per service tier with read replicas serving all read-model queries to isolate analytical load from command processing.
- All services must expose `/health/live` and `/health/ready` endpoints consumable by the orchestration layer for zero-downtime deployments.

## References
- Business rule mapping: [../analysis/business-rules.md](../analysis/business-rules.md)
- Cross-cutting execution model: [../cross-cutting-operational-guidance.md](../cross-cutting-operational-guidance.md)
- Event catalog: [../design/event-catalog.md](../design/event-catalog.md)
- Component design: [../design/component-design.md](../design/component-design.md)
- Sequence diagrams: [../design/sequence-diagrams.md](../design/sequence-diagrams.md)
