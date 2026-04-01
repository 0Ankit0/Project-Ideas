# User Stories

## Purpose
Define implementation-ready user stories with explicit acceptance criteria and operational edge behavior. Stories are grouped by epic, numbered sequentially, and prioritized. Every story is traced to business rules and system capabilities.

---

## Epic 1: Inbound & Receiving

**US-001: Receive Pallet Against ASN**
- **As a** Receiver
- **I want to** scan an ASN barcode and individual pallet labels at the dock
- **So that** inventory is validated against the purchase order before becoming allocatable
- **Priority:** High
- **Acceptance Criteria:**
  1. Scanning a valid ASN returns the expected line items, quantities, and lot/serial requirements for confirmation.
  2. A quantity exceeding the configured tolerance threshold creates a discrepancy case and halts putaway for that line; lines within tolerance proceed normally.
  3. The resulting GRN records PO/ASN reference, received quantities per line, operator ID, and timestamp atomically with the `ReceivingCompleted` event.
  4. Submitting the same scan with the same idempotency key returns the original GRN reference without creating a duplicate.

**US-002: Capture Lot Number and Expiry Date at Receipt**
- **As a** Receiver
- **I want to** enter lot numbers and expiry dates for controlled SKUs during receiving
- **So that** FEFO rotation and lot traceability are maintained from the point of receipt
- **Priority:** High
- **Acceptance Criteria:**
  1. Items flagged as lot-controlled cannot be confirmed without a lot number.
  2. Items under an active FEFO policy reject receipt if no expiry date is provided, with error `LOT_EXPIRY_REQUIRED`.
  3. Duplicate serial numbers for the same SKU across any open GRN are rejected with `SERIAL_DUPLICATE` and the conflicting GRN reference.
  4. Lot and expiry data are stored and visible on all downstream pick, pack, and shipping events.

**US-003: Flag Item for Quarantine at Receipt**
- **As a** Receiver
- **I want to** mark a received item as quarantined during or after inspection
- **So that** damaged or held items never enter the allocatable stock pool
- **Priority:** High
- **Acceptance Criteria:**
  1. Quarantine flag is applied at the receipt line level with a mandatory reason code and inspector identity.
  2. Quarantined inventory is immediately excluded from all allocation and wave planning queries.
  3. Releasing quarantine requires supervisor approval with a reason code, and emits an `InventoryStatusChanged` event.
  4. Dashboard reflects quarantine quantity separately from available, reserved, and on-hand balances.

**US-004: Cross-Dock Receipt to Outbound Staging**
- **As a** Receiver
- **I want** the system to automatically route eligible receipts to outbound staging instead of reserve storage
- **So that** high-priority orders can be fulfilled without consuming putaway capacity
- **Priority:** High
- **Acceptance Criteria:**
  1. Cross-dock eligibility is evaluated at receipt line level by matching open shipment orders in wave-ready or allocated state.
  2. Cross-dock tasks are generated and queued before standard putaway tasks for the same receipt.
  3. No bin capacity is consumed in reserve storage for cross-docked units.
  4. A `CrossDockRoutingApplied` event is published with receipt line reference, target outbound order, and staging zone.

**US-005: Approve Receiving Variance**
- **As a** Supervisor
- **I want to** review and approve quantity variances flagged during receiving
- **So that** dock operations can continue without stopping the entire receipt flow
- **Priority:** High
- **Acceptance Criteria:**
  1. Variance approval requires a reason code, the approver's identity (distinct from the receiver), and an expiry timestamp.
  2. System records the original discrepancy, the override decision, and the evidence reference atomically.
  3. An expired override auto-invalidates, blocks further processing on the affected line, and creates a follow-up supervisor task.
  4. After approval, putaway tasks are generated for the approved quantity; the variance is surfaced in the carrier performance and receiving accuracy reports.

**US-006: Receive Unplanned Inbound (No ASN)**
- **As a** Receiver
- **I want to** receive stock that arrives without a pre-registered ASN
- **So that** unexpected deliveries do not block dock operations entirely
- **Priority:** Medium
- **Acceptance Criteria:**
  1. Unplanned receipt creates a discrepancy record automatically and notifies the supervisor within 2 minutes.
  2. Inventory from unplanned receipts is placed in a holding zone and is not allocatable until supervisor review.
  3. Supervisor can associate the unplanned receipt with an existing PO or create an ad-hoc receipt with dual approval.
  4. All unplanned receipt events are tagged `receipt_type: unplanned` in the audit log.

**US-007: Dock Check-In and Door Assignment**
- **As a** Transportation Coordinator
- **I want to** assign inbound trucks to specific dock doors before unloading begins
- **So that** dock capacity is managed and receiving workflows are organized by door
- **Priority:** Medium
- **Acceptance Criteria:**
  1. A dock door cannot be assigned to more than one active inbound load simultaneously; conflict returns an error with the conflicting load reference.
  2. Door assignment is recorded on every GRN line for traceability and dock utilization reporting.
  3. Dock check-in emits a `DockCheckInCompleted` event that triggers the receiving queue for that door.
  4. Supervisor can reassign a door when the original assignment load departs or is cancelled.

**US-008: Replay Offline Scanner Batch for Receiving**
- **As an** Inventory Controller
- **I want to** replay a batch of receiving scans collected while the scanner was offline
- **So that** all received inventory is reflected in the system when connectivity is restored
- **Priority:** Medium
- **Acceptance Criteria:**
  1. Offline batch is submitted via the scanner gateway with a batch idempotency key; individual scan events within the batch are deduplicated independently.
  2. Conflicting events (same SKU/bin mutated by an online operation during the offline window) create review tasks with both event snapshots.
  3. Non-conflicting events in the same batch are processed normally; partial batch failure does not roll back successful events.
  4. Conflict review task includes a merge path and a compensating adjustment path; resolution emits an audit event.

---

## Epic 2: Putaway & Inventory Management

**US-009: Execute Directed Putaway**
- **As a** Putaway Worker
- **I want to** receive a scanner-guided putaway task that directs me to the optimal bin
- **So that** inventory is placed in the correct zone without manual bin selection
- **Priority:** High
- **Acceptance Criteria:**
  1. The suggested bin satisfies zone eligibility rules (temperature, hazmat class, SKU class) and is within capacity.
  2. The task includes a travel-path-optimized sequence when multiple items need to be put away in the same zone.
  3. Scan confirmation of the bin label is required before the system records the putaway; premature confirmation is rejected.
  4. `PutawayCompleted` event is published with `bin_id`, `sku_id`, `lot_id`, `quantity`, and `operator_id` in the same transaction as the bin inventory increment.

**US-010: Override Suggested Putaway Bin**
- **As a** Putaway Worker
- **I want to** select an alternate bin when the suggested bin is physically unavailable or obstructed
- **So that** I can complete the putaway without waiting for supervisor intervention
- **Priority:** Medium
- **Acceptance Criteria:**
  1. The override bin must pass capacity and zone eligibility checks; an ineligible override bin is rejected with the specific constraint violation.
  2. Override is audited with operator ID, original suggested bin, alternate bin, and a mandatory reason code.
  3. Supervisor is notified of overrides that select a bin in a different zone than originally recommended.
  4. Override frequency is tracked per operator in the operational reports for coaching and process improvement.

**US-011: Track Real-Time Inventory Position**
- **As a** Inventory Planner
- **I want to** view bin-level on-hand, reserved, available, and quarantine quantities in real time
- **So that** I can make informed replenishment and allocation decisions
- **Priority:** High
- **Acceptance Criteria:**
  1. Dashboard reflects inventory position changes within 60 seconds of any stock mutation.
  2. The balance invariant (on_hand = available + reserved + quarantine) is enforced; any violation triggers an automated reconciliation alert.
  3. Inventory is filterable by warehouse, zone, SKU, lot, expiry date range, and bin status.
  4. Export to CSV and JSON is available for up to 1 million records with a resumable cursor.

**US-012: Apply Inventory Rotation Policy**
- **As a** Inventory Planner
- **I want to** configure FIFO, FEFO, or LIFO rotation per SKU or zone
- **So that** stock is consumed in the correct sequence to minimize waste and meet compliance requirements
- **Priority:** High
- **Acceptance Criteria:**
  1. FEFO selects the lot with the earliest expiry date first; ties are broken by receipt timestamp (oldest first).
  2. FIFO selects the lot received earliest regardless of expiry date.
  3. Allocation and pick task generation enforce the active rotation policy; out-of-sequence picks are rejected with `LOT_SEQUENCE_VIOLATION`.
  4. Policy change takes effect for new allocations immediately; existing reservations are not retroactively resequenced.

**US-013: Execute Manual Inventory Adjustment**
- **As an** Inventory Controller
- **I want to** record a positive or negative inventory adjustment for a specific bin and lot
- **So that** system quantities match the physical count after a discrepancy is confirmed
- **Priority:** High
- **Acceptance Criteria:**
  1. Every adjustment requires a mandatory reason code and an evidence reference (e.g., count sheet ID, photo reference).
  2. Adjustments above the configured threshold require two distinct approver IDs before being committed.
  3. The adjustment is atomic with `InventoryAdjusted` event publication; the event includes before/after quantities, reason code, and `correlation_id`.
  4. Adjustment history is queryable by SKU, bin, date range, and actor ID for audit purposes.

**US-014: Transfer Inventory Between Zones**
- **As a** Inventory Planner
- **I want to** initiate an inter-zone inventory transfer
- **So that** stock can be repositioned to meet demand or rebalance zone utilization
- **Priority:** Medium
- **Acceptance Criteria:**
  1. Transfer is a two-phase commit: transfer-out confirmation decrements the source bin; transfer-in confirmation increments the destination bin.
  2. Inventory shows `InTransit` status between the two confirmations and is not allocatable during that window.
  3. A supervisor alert is generated if transfer-in is not confirmed within the configured abandonment timeout.
  4. Both transfer-out and transfer-in events are published with the same `transfer_id` correlation reference.

---

## Epic 3: Outbound Wave Planning

**US-015: Create and Release a Wave**
- **As a** Warehouse Manager
- **I want to** group orders into a wave by carrier cutoff time, priority tier, and zone cluster
- **So that** pick resources are focused on the highest-priority fulfilment work first
- **Priority:** High
- **Acceptance Criteria:**
  1. Wave creation groups orders respecting picker capacity limits; orders beyond the capacity limit are deferred to the next wave.
  2. Carrier cutoff time is the primary sort key; orders for earlier cutoffs appear in earlier waves.
  3. Wave release emits `WaveReleased` and creates all pick tasks atomically; partial task creation is rejected.
  4. Wave state machine transitions are enforced: Draft → Released → Active → Closed; illegal transitions return 409.

**US-016: Hold Wave for Downstream Degradation**
- **As a** Warehouse Manager
- **I want** the system to automatically hold wave release when a downstream carrier API or WCS is degraded
- **So that** pick tasks are not created for shipments that cannot be dispatched
- **Priority:** High
- **Acceptance Criteria:**
  1. A `WaveHeld` alert is raised immediately when the relevant circuit breaker is open during wave release.
  2. Wave is auto-released when the dependency recovers, subject to operator confirmation.
  3. Operator can manually acknowledge the degradation and force-release with a supervisor override and reason code.
  4. Hold duration and the triggering dependency are recorded in the wave audit log.

**US-017: Abort Wave and Release Reservations**
- **As a** Warehouse Manager
- **I want to** abort an active wave when operational conditions change significantly
- **So that** order reservations are freed for re-planning without manual inventory reconciliation
- **Priority:** Medium
- **Acceptance Criteria:**
  1. Wave abort emits `WaveAborted` event and releases all reservations under the wave within 30 seconds.
  2. Orders return to allocatable state and are available for inclusion in the next wave.
  3. Abort requires supervisor authorization with a reason code when the wave is in Active state.
  4. Partial progress (already-completed picks) is preserved and excluded from the released reservation pool.

**US-018: Configure Batch, Zone, and Cluster Picking Modes**
- **As a** Warehouse Manager
- **I want to** select the picking mode per wave (zone, batch, or cluster)
- **So that** the pick strategy matches the current order profile and staffing layout
- **Priority:** Medium
- **Acceptance Criteria:**
  1. Zone picking routes tasks to the pickers assigned to each zone; zone handoff confirmation is tracked per task.
  2. Batch picking consolidates multiple orders into a single travel-path-sorted task list for one picker.
  3. Cluster picking organizes tasks by carton slot so one picker simultaneously fulfils multiple orders.
  4. Picking mode is configurable at wave creation time and cannot be changed after wave release.

**US-019: View Wave Planning KPIs**
- **As a** Warehouse Manager
- **I want to** see a real-time dashboard of wave release latency, pick task assignment rate, and wave completion time
- **So that** I can identify bottlenecks and adjust staffing or zone assignments
- **Priority:** Medium
- **Acceptance Criteria:**
  1. Dashboard shows active waves, pick task completion %, estimated completion time, and short-pick rate per wave.
  2. Data refreshes within 60 seconds of any wave or pick task state change.
  3. Wave KPIs are filterable by warehouse, zone, date range, and picker.
  4. Completed wave metrics are retained in the reporting database for 90 days for trend analysis.

**US-020: Handle Backpressure During Carrier Cutoff Window**
- **As a** Transportation Coordinator
- **I want** the system to notify me when wave release is blocked by a carrier dependency failure within 30 minutes of the carrier cutoff
- **So that** I can escalate or switch to a backup carrier before the cutoff is missed
- **Priority:** High
- **Acceptance Criteria:**
  1. Alert includes affected wave ID, carrier name, cutoff time, and dependency failure detail.
  2. System provides a one-click failover option to re-assign the wave's orders to the configured backup carrier.
  3. Backup carrier assignment generates new label requests automatically; no manual re-entry required.
  4. `CarrierCutoffMissed` event is emitted if the cutoff passes without wave release; it triggers a coordinator notification and SLA report entry.

---

## Epic 4: Picking Operations

**US-021: Execute Pick with Scan Confirmation**
- **As a** Picker
- **I want to** scan the bin label and item barcode to confirm each pick
- **So that** stock decrements are tied to physical confirmation and reservation records
- **Priority:** High
- **Acceptance Criteria:**
  1. Pick confirmation fails with `RESERVATION_NOT_FOUND` if the task's reservation has been released or expired.
  2. Scan mismatch (wrong bin or wrong item) returns `SCAN_MISMATCH` with expected vs. actual detail; no inventory movement is recorded.
  3. FEFO/FIFO lot sequence is validated at scan; scanning an out-of-sequence lot returns `LOT_SEQUENCE_VIOLATION` with the correct lot.
  4. Successful pick confirmation emits a `PickConfirmed` event and decrements the reserved quantity atomically.

**US-022: Handle Short Pick**
- **As a** Picker
- **I want** the system to offer an alternate bin when I cannot pick the full requested quantity
- **So that** I can partially fulfil the order without creating a backorder unnecessarily
- **Priority:** High
- **Acceptance Criteria:**
  1. Short pick event is emitted with `quantity_requested` and `quantity_picked` when a picker confirms less than the task quantity.
  2. Alternate bin search completes within 3 seconds and offers the picker a new task for the remaining quantity.
  3. Backorder is created only when no alternate bin contains sufficient eligible stock.
  4. Both the short-pick event and any resulting backorder are surfaced in the shipment SLA and customer-impact reports.

**US-023: Override FEFO Lot Sequence**
- **As a** Supervisor
- **I want to** authorize a picker to pick a later-expiry lot when the earliest-expiry lot is physically inaccessible
- **So that** pick operations can continue without obstructing aisles to reach the sequenced lot
- **Priority:** Low
- **Acceptance Criteria:**
  1. Supervisor override is initiated from the exception queue or directly from the picker's scanner screen.
  2. Override requires supervisor identity, reason code, and the specific lot being bypassed.
  3. Override is valid for the single pick task and expires after the task is completed or reassigned.
  4. Override event is recorded with full audit context and surfaced in the inventory rotation compliance report.

**US-024: Execute Zone Pick Handoff**
- **As a** Picker
- **I want to** confirm completion of my zone portion and hand off the partially-picked order to the next zone
- **So that** multi-zone orders flow through the warehouse without supervisor intervention
- **Priority:** Medium
- **Acceptance Criteria:**
  1. Zone handoff is confirmed with a scan of the transfer tote label and the destination zone conveyor or staging location.
  2. The next zone picker is notified of the incoming tote within 30 seconds of handoff confirmation.
  3. Handoff scan failure (wrong tote or wrong destination) is rejected; the current zone picker retains task ownership.
  4. Zone handoff events are captured for travel-time analysis and zone balance reporting.

**US-025: Execute Batch Pick**
- **As a** Picker
- **I want to** execute a consolidated batch pick list that spans multiple orders in travel-path sequence
- **So that** I minimize travel distance while picking for several orders simultaneously
- **Priority:** Medium
- **Acceptance Criteria:**
  1. Batch task list is sorted by travel path (zone → aisle → rack → bin sequence) to minimize backtracking.
  2. Pick confirmation is per order line; each line is linked to its order and reservation record.
  3. The system tracks which carton slot each pick goes into and alerts the picker if a slot scan is missing.
  4. Batch pick efficiency (lines/hour) is tracked per picker and reported on the picking KPI dashboard.

**US-026: Resolve Pick Task Discrepancy After Wave Close**
- **As an** Inventory Controller
- **I want to** investigate and resolve a pick task that was marked complete but has a quantity discrepancy
- **So that** shipment accuracy and inventory positions are corrected before dispatch
- **Priority:** Medium
- **Acceptance Criteria:**
  1. Controller can view the full pick task audit trail including scanner channel, operator ID, lot, and timestamp.
  2. Resolution options include: re-pick from alternate bin, record adjustment, or escalate to supervisor for approval.
  3. All resolution actions are logged with the controller's identity and reason code.
  4. Resolution closes the discrepancy task and updates the shipment line status accordingly.

---

## Epic 5: Packing & Shipping

**US-027: Close Carton with Reconciliation Gate**
- **As a** Pack Station Operator
- **I want to** be prevented from closing a carton until all expected items are scanned
- **So that** mis-ships are caught at the packing station rather than at the customer
- **Priority:** High
- **Acceptance Criteria:**
  1. Carton close is blocked when the packed quantity is less than the pick confirmation quantity for any shipment line.
  2. Mismatch reason code and operator identity are captured in the audit log before the station allows recount.
  3. Supervisor approval is required to close a carton with a partial pack; approval is audited with both identities.
  4. Pack station throughput (cartons/hour) is tracked and surfaced on the operational dashboard.

**US-028: Generate Carrier-Compliant Shipping Label**
- **As a** Pack Station Operator
- **I want to** generate and print a carrier-compliant label automatically when a carton is closed
- **So that** the correct tracking number, weight, and dimensions are applied without manual data entry
- **Priority:** High
- **Acceptance Criteria:**
  1. Label is generated in ZPL or PDF format and validated against the carrier schema before printing.
  2. Label generation failure transitions the parcel to `PackingBlocked` and retries up to 3 times before escalation.
  3. Label content includes: tracking number, carrier service code, recipient details, weight, dimensional data, and barcode.
  4. Labels can be voided and reprinted within the shipment window; void invalidates the tracking number with the carrier API.

**US-029: Execute Repack Workflow**
- **As a** Pack Station Operator
- **I want to** move items from one carton to another when damage or content errors are discovered
- **So that** the shipment is corrected before it leaves the warehouse
- **Priority:** Medium
- **Acceptance Criteria:**
  1. Repack closes the original carton (without generating a label) and opens a new carton; both events are audited.
  2. The allocation reference and all pick confirmations are carried through to the new carton.
  3. Repack requires dual scan confirmation and a mandatory reason code.
  4. Repack is blocked after the final dispatch confirmation has been issued for the shipment.

**US-030: Confirm Shipment Dispatch**
- **As a** Transportation Coordinator
- **I want to** confirm the final shipment dispatch after all parcels are loaded onto the carrier vehicle
- **So that** inventory is decremented, tracking events start, and downstream billing triggers exactly once
- **Priority:** High
- **Acceptance Criteria:**
  1. Dispatch confirmation emits `ShipmentDispatched` exactly once via the transactional outbox; duplicate confirmations return the original event reference.
  2. Inventory decrement becomes non-reversible except via return or adjustment flow.
  3. Dock door release is blocked until dispatch confirmation is recorded.
  4. Carrier receives tracking activation webhook or EDI notification within 60 seconds of dispatch confirmation.

**US-031: Handle Manifest Transmission Failure**
- **As a** Transportation Coordinator
- **I want** the system to retry manifest transmission automatically when the carrier API is unavailable
- **So that** carrier SLA is maintained even during transient API outages
- **Priority:** High
- **Acceptance Criteria:**
  1. Manifest transmission retries with exponential backoff for up to 10 attempts before DLQ routing.
  2. `CarrierCutoffMissed` alert fires if the cutoff time is passed while retries are still in progress.
  3. A manual retry action is available from the coordinator dashboard after DLQ routing.
  4. All retry attempts and outcomes are logged with carrier error codes for SLA reporting.

---

## Epic 6: Cycle Counting & Inventory Accuracy

**US-032: Generate Cycle Count Plan**
- **As an** Inventory Controller
- **I want to** generate a cycle count plan by zone, ABC velocity class, or specific bin selection
- **So that** high-velocity locations are counted more frequently to maintain inventory accuracy
- **Priority:** High
- **Acceptance Criteria:**
  1. Plan specifies target bins, assigned operators, and count window; bins under active pick or putaway tasks are excluded automatically.
  2. `CycleCountStarted` event is published with plan ID, assigned operators, and target bin list.
  3. ABC velocity classification is applied automatically based on 30-day pick frequency data.
  4. Plan is available on assigned counters' scanner queues within 60 seconds of creation.

**US-033: Execute Blind Count**
- **As an** Inventory Controller
- **I want to** count bin contents without seeing the system's expected quantity
- **So that** counts are unbiased and not influenced by the current system value
- **Priority:** High
- **Acceptance Criteria:**
  1. Expected quantity is hidden on the count screen until the count is submitted.
  2. System compares submitted count to on-hand quantity only after submission; variance is flagged for approval if it exceeds configurable tolerance.
  3. Counter cannot view or modify any other bin's inventory data from the count screen.
  4. Count submission is idempotent; resubmission with the same count plan ID and bin returns the original count record.

**US-034: Manage Count Variance and Recount**
- **As a** Supervisor
- **I want to** review variances that exceed tolerance and assign a recount to an independent operator
- **So that** large discrepancies are confirmed by a second count before any ledger adjustment is made
- **Priority:** High
- **Acceptance Criteria:**
  1. Recount is assigned to an operator different from the original counter; assignment is enforced by the system.
  2. If recount confirms variance, adjustment is auto-approved within the configured limit; above the limit it is routed to supervisor.
  3. All count, recount, and adjustment events are published with `count_plan_id` for traceability.
  4. Balance invariant is verified after adjustment commits; any violation triggers an immediate reconciliation alert.

**US-035: Schedule Perpetual Inventory Audit**
- **As a** Warehouse Manager
- **I want to** set a recurring cycle count schedule so that every bin in the warehouse is counted at least once per quarter
- **So that** inventory accuracy targets are met without requiring a full annual physical inventory
- **Priority:** Medium
- **Acceptance Criteria:**
  1. Schedule configuration specifies frequency, zone rotation order, and count window per zone.
  2. Scheduler generates count plans automatically according to the configured cadence.
  3. Bins not counted within the scheduled window generate an overdue alert to the inventory controller.
  4. Inventory accuracy % (counted vs. adjusted vs. expected) is reported per zone per period.

---

## Epic 7: Replenishment

**US-036: Trigger Replenishment from Min/Max Rule**
- **As an** Inventory Planner
- **I want** the system to automatically trigger a replenishment task when a pick-face bin falls below its minimum quantity
- **So that** pickers always have stock available in the forward pick zone
- **Priority:** High
- **Acceptance Criteria:**
  1. `ReplenishmentTriggered` event is published within 60 seconds of the bin falling below its configured minimum.
  2. Duplicate triggers for the same bin/SKU within the evaluation window are deduplicated.
  3. Replenishment task specifies source bin, destination bin, quantity to replenish (up to max), and priority.
  4. Source bin is atomically decremented and destination bin is incremented upon task completion.

**US-037: Execute Replenishment Task**
- **As a** Putaway Worker
- **I want to** receive a scanner-guided replenishment task directing me to move stock from reserve to pick face
- **So that** pick-face bins are refilled without requiring manual planning
- **Priority:** High
- **Acceptance Criteria:**
  1. Task includes source bin, destination bin, SKU, lot, quantity, and travel-path guidance.
  2. Source bin eligibility is checked at task assignment; bins in Maintenance or active cycle count are excluded.
  3. Replenishment quantity does not exceed destination bin remaining capacity; excess is queued as a separate task.
  4. Task completion emits `ReplenishmentCompleted` event; both source and destination ledgers are updated atomically.

**US-038: Defer Replenishment When Source Bin Is Constrained**
- **As an** Inventory Planner
- **I want** replenishment tasks to automatically defer and requeue when source bins become available
- **So that** replenishment workflows do not require manual monitoring of bin status changes
- **Priority:** Medium
- **Acceptance Criteria:**
  1. Task transitions to `Deferred` with constraint reason (Maintenance, CycleCount, InTransit) recorded.
  2. Auto-requeue fires within 60 seconds of constraint removal.
  3. Deferral and requeue events are audited with the source constraint reference.
  4. Deferral duration is tracked and surfaced in replenishment SLA reports.

**US-039: Configure Demand-Driven Replenishment Signal**
- **As an** Inventory Planner
- **I want to** integrate a demand forecast signal to trigger replenishment proactively before pick-face bins reach minimum
- **So that** replenishment is not reactive but anticipates consumption patterns
- **Priority:** Low
- **Acceptance Criteria:**
  1. Demand signal (quantity forecast for next N hours) is accepted via a configured integration endpoint or manual entry.
  2. Replenishment is triggered when projected on-hand at the pick face falls below the minimum, based on current available quantity minus forecasted demand.
  3. Demand-driven replenishment tasks are tagged `trigger_type: demand_forecast` in events and reports.
  4. Forecast accuracy vs. actual consumption is tracked and reported monthly.

---

## Epic 8: Returns & Cross-Docking

**US-040: Receive Authorized Return (RMA)**
- **As a** Receiver
- **I want to** scan an RMA authorization at the dock before processing a customer return
- **So that** returned items are matched to their original shipment and routed correctly
- **Priority:** High
- **Acceptance Criteria:**
  1. RMA authorization lookup returns the original shipment reference, expected items, and inspection disposition (restock or quarantine).
  2. Items passing inspection are routed to the configured restock zone; failed items are quarantined automatically.
  3. Original shipment reference is preserved on the return record for financial and customer service reconciliation.
  4. `ReturnReceived` event is published with RMA ID, inspection result, and routing decision.

**US-041: Handle Blind Return (No RMA)**
- **As a** Receiver
- **I want to** process a customer return that arrives without an RMA authorization
- **So that** items do not sit indefinitely at the dock while awaiting manual decision
- **Priority:** Medium
- **Acceptance Criteria:**
  1. Blind return creates a discrepancy record and notifies the supervisor within 2 minutes.
  2. Items are placed in a holding location and are not allocatable until supervisor review is complete.
  3. Restocking a blind return requires two distinct approver IDs.
  4. All blind return events are tagged `return_type: blind` and tracked in the returns exception report.

**US-042: Route Cross-Dock Receipt to Outbound**
- **As a** Receiver
- **I want** the system to identify receipts that can be cross-docked and route them to outbound staging without putaway
- **So that** urgent orders are expedited and reserve storage capacity is preserved
- **Priority:** High
- **Acceptance Criteria:**
  1. Cross-dock eligibility check runs at receipt line level against open, wave-ready shipment orders.
  2. Cross-dock task is generated with higher priority than standard putaway tasks in the same receipt.
  3. Outbound staging location is confirmed by scan before cross-dock task is marked complete.
  4. Cross-docked units are excluded from bin capacity calculations for reserve zones.

**US-043: Process Return for Vendor Credit**
- **As a** Transportation Coordinator
- **I want to** initiate an outbound return shipment to a vendor after inspection confirms a product defect
- **So that** vendor credit is initiated with a documented chain of custody
- **Priority:** Low
- **Acceptance Criteria:**
  1. Vendor return order references the original receipt GRN and inspection result.
  2. Items are moved from quarantine to an outbound return staging zone before dispatch.
  3. Vendor return dispatch emits `VendorReturnDispatched` event with GRN reference, vendor ID, carrier, and tracking number.
  4. Return is reflected in inventory as a negative adjustment from quarantine stock, with reason code `VENDOR_RETURN`.

---

## Epic 9: Reporting & Analytics

**US-044: View Operational Dashboard**
- **As a** Warehouse Manager
- **I want to** see a single real-time dashboard covering receiving throughput, putaway queue depth, pick rate, pack throughput, and shipment on-time %
- **So that** I can identify operational bottlenecks and make staffing decisions in real time
- **Priority:** High
- **Acceptance Criteria:**
  1. All KPIs refresh within 60 seconds of underlying data changes.
  2. Dashboard is filterable by warehouse, zone, date range, and client (tenant).
  3. Click-through from any KPI opens a drill-down view with per-operator or per-zone detail.
  4. Dashboard is accessible from both desktop browsers and mobile devices.

**US-045: Export Inventory Snapshot Report**
- **As an** Inventory Planner
- **I want to** export a full inventory snapshot in CSV or JSON format
- **So that** I can reconcile system quantities against physical counts or share data with the ERP
- **Priority:** Medium
- **Acceptance Criteria:**
  1. Report includes: SKU, lot, expiry, bin, zone, on-hand, reserved, available, quarantine quantities, and last movement timestamp.
  2. Report for up to 1 million records generates within 120 seconds; exports are paginated with a resumable cursor.
  3. Completed reports are retained for 90 days and downloadable from the report history screen.
  4. Export is protected by the `InventoryController` or `WarehouseManager` role; unauthorized access returns 403.

**US-046: View Carrier Performance Report**
- **As a** Transportation Coordinator
- **I want to** review a daily carrier performance report covering on-time pickup %, label error rate, and carrier-reported exceptions
- **So that** I can evaluate carrier SLA compliance and escalate chronic issues
- **Priority:** Medium
- **Acceptance Criteria:**
  1. Report is generated daily at 06:00 UTC and available on-demand.
  2. Data is sourced from shipment events and carrier webhook ingestion; discrepancies trigger automatic coordinator alerts.
  3. Report is filterable by carrier, warehouse, date range, and service class.
  4. Carriers with anomalous exception rates generate an automatic alert to the coordinator.

**US-047: Track Inventory Accuracy KPIs**
- **As a** Warehouse Manager
- **I want to** view inventory accuracy % by zone over time alongside cycle count coverage
- **So that** I can demonstrate compliance with accuracy SLAs and prioritize zones for more frequent counting
- **Priority:** Medium
- **Acceptance Criteria:**
  1. Inventory accuracy % is calculated as: (bins with zero variance / total counted bins) × 100, per zone per period.
  2. Trend chart shows accuracy % over the last 12 months with cycle count plan coverage overlaid.
  3. Zones below the configured accuracy threshold are highlighted and generate a planner notification.
  4. Report is exportable in CSV format and retained for 2 years.

---

## Epic 10: System Administration

**US-048: Manage Zones, Bins, and Location Hierarchy**
- **As a** Warehouse Manager
- **I want to** configure the location hierarchy (zones, aisles, racks, bins) with capacity, type, and eligibility attributes
- **So that** putaway rules, allocation logic, and capacity enforcement reflect the physical warehouse layout
- **Priority:** High
- **Acceptance Criteria:**
  1. Creating or modifying a bin requires specifying unit capacity, weight capacity, volume capacity, zone type, and SKU eligibility rules.
  2. Bin status changes (Active ↔ Inactive ↔ Maintenance ↔ Quarantine) take effect immediately; inventory in an Inactive or Maintenance bin is excluded from allocation.
  3. All location hierarchy changes are audited with manager identity, timestamp, and before/after configuration.
  4. Deleting a bin is blocked when it contains inventory or has open tasks; the error includes the blocking reference.

**US-049: Manage API Keys and Tenant Integrations**
- **As a** System Administrator
- **I want to** create, rotate, and revoke scoped API keys for third-party integrations
- **So that** external systems can integrate securely without sharing user credentials
- **Priority:** High
- **Acceptance Criteria:**
  1. API key creation requires specifying tenant, integration name, allowed scopes, and expiry date.
  2. Key rotation generates a new key immediately; the old key remains valid for a configurable grace period (default: 24 hours).
  3. Key revocation takes effect within 60 seconds across all API gateway instances.
  4. All key lifecycle events (create, rotate, revoke) are recorded in the security audit log.

**US-050: Configure Business Rules Per Client**
- **As a** System Administrator
- **I want to** configure business rules (tolerance thresholds, rotation policies, replenishment min/max, approval thresholds) independently per tenant client
- **So that** each 3PL client's unique operational requirements are met without impacting other clients
- **Priority:** Medium
- **Acceptance Criteria:**
  1. All configurable business rule parameters expose a per-tenant override that takes precedence over system defaults.
  2. Rule changes take effect for new operations immediately; in-flight operations (active waves, open tasks) use the rule set active at the time they were created.
  3. Configuration changes are audited with admin identity, tenant ID, parameter name, and before/after values.
  4. System admin can clone a client's rule set as a starting template for a new client onboarding.

---

## Rule Coverage Summary

| Epic | Business Rules |
|---|---|
| Inbound & Receiving | BR-5, BR-6, BR-10 |
| Putaway & Inventory Management | BR-1, BR-3, BR-5, BR-7, BR-10 |
| Wave Planning | BR-2, BR-5, BR-7, BR-10 |
| Picking Operations | BR-7, BR-10 |
| Packing & Shipping | BR-8, BR-9, BR-10 |
| Cycle Counting | BR-4, BR-10 |
| Replenishment | BR-1, BR-2, BR-5 |
| Returns & Cross-Docking | BR-3, BR-5, BR-6, BR-10 |
| Reporting & Analytics | BR-10 |
| System Administration | BR-1, BR-3 |
