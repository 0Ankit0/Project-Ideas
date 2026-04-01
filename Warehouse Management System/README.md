# Warehouse Management System (WMS) — Design Documentation

> Comprehensive, implementation-ready design documentation for a modern, multi-warehouse management system covering the complete fulfillment lifecycle: inbound receiving, directed putaway, wave planning, optimized picking, pack-and-ship with carrier integration, cycle counting, replenishment, returns, cross-docking, and end-to-end inventory traceability. All artifacts are traceable to business rules, use cases, and infrastructure decisions.

---

## Key Features

- **Multi-Warehouse & Multi-Zone Layout**: Hierarchical location model (Warehouse → Zone → Aisle → Rack → Bin) with per-zone type enforcement (ambient, refrigerated, hazmat, bulk, pick-face) and per-bin capacity constraints in units, weight, and volume.
- **Inbound Receiving & ASN Validation**: PO/ASN-based receiving with quantity tolerance enforcement, lot/serial capture at dock, GRN generation, and discrepancy case creation for variances exceeding tolerance.
- **Directed Putaway**: Rules-driven putaway engine that assigns destination bins based on SKU affinity, zone eligibility, bin utilization, and travel-path optimization; supports supervisor override with full audit trail.
- **Lot/Serial & Expiry Tracking**: Full lot number, serial number, and expiry date capture for controlled SKUs; FEFO enforces earliest-expiry-first selection across all allocation and picking operations.
- **Inventory Rotation Policies (FIFO / FEFO / LIFO)**: Per-SKU or per-zone rotation policy configuration with enforcement at allocation and pick confirmation; policy override requires supervisor role and generates an audit event.
- **Wave Planning & Order Grouping**: Intelligent wave creation that groups orders by carrier cutoff time, customer priority tier, zone cluster, and picker capacity; backpressure gating prevents wave release to degraded downstream dependencies.
- **Zone Picking, Batch Picking & Cluster Picking**: Configurable picking modes per wave; zone picking routes tasks to zone-specific workers; batch picking consolidates multiple orders for one picker; cluster picking organizes picks into carton slots for simultaneous multi-order fulfilment.
- **Pick Optimization**: Travel-path-sorted task lists generated per picker mode; short-pick handling with automatic alternate-bin search before backorder creation; FEFO/FIFO lot sequence enforcement at scan confirmation.
- **Pack Station Reconciliation**: Carton close blocked until picked quantity matches pack station manifest; dunnage and void-fill tracking; repack workflow with dual scan confirmation and reason capture.
- **Carrier Label Generation**: ZPL/PDF carrier-compliant label generation embedding tracking number, weight, and dimensional data; multi-carrier rate shopping; label void and reprint within the shipment window.
- **Outbound Manifest & Shipment Dispatch**: Manifest generation per carrier load with EDI/API transmission; dock door assignment enforcement; idempotent `ShipmentDispatched` event via transactional outbox.
- **Cycle Counting with Variance Management**: ABC-velocity and zone-based count plan generation; blind-count enforcement at the scanner; recount workflow with independent second counter; auto-approval within threshold, supervisor escalation above.
- **Inventory Transfers (Inter-Warehouse & Inter-Zone)**: Two-phase commit transfers with `InTransit` status; abandoned transfer alerts; atomic source decrement and destination increment.
- **Replenishment Triggers (Min/Max & Demand-Driven)**: Bin-level min/max rule evaluation; demand-forecast-driven replenishment signal integration; deduplication within the evaluation window; task deferral when source bin is under count or maintenance, with auto-requeue on constraint removal.
- **Cross-Docking**: Receipt-time cross-dock eligibility evaluation; direct routing to outbound staging when a matching open shipment exists; no reserve storage capacity consumed.
- **Returns Processing (RMA & Blind)**: RMA-authorized and blind return receipt; inspection-result-driven routing to restock or quarantine; dual-approval for blind return restocking; original shipment reference preserved.
- **Barcode & RFID Scanning**: Normalized scan input from handheld, fixed reader, and mobile channels; offline scanner batch replay with idempotency enforcement; conflict review task creation for replay collisions.
- **ERP / TMS / WCS Integration**: Event-driven PO and ASN ingest from ERP (SAP, Oracle, NetSuite); outbound inventory and shipment event transmission within 5 min of state change; carrier API integration for labels, rate shopping, and tracking; WCS/WES integration for conveyor and sorter control signals.
- **Real-Time Inventory Visibility**: Sub-60-second dashboard refresh; bin-level on-hand, reserved, available, and quarantine balances; balance invariant enforcement (on_hand = available + reserved + quarantine) with automated reconciliation alerts.
- **3PL Multi-Tenant Support**: Per-client data isolation, configurable business rules, billing event emission per client, cross-tenant data access blocked at the API gateway.
- **Analytics & KPI Dashboards**: Receiving throughput, putaway queue depth, pick rate, pack throughput, shipment on-time %, inventory accuracy %, and carrier performance reports; filterable by warehouse, zone, date range, and client.
- **Audit & Compliance**: Immutable append-only inventory ledger; 100% state-changing operation coverage with actor_id, correlation_id, reason_code, and timestamp; 7-year audit trail retention for regulatory compliance.

---

## Architecture Overview

The WMS is designed as a set of independently deployable domain services organized around bounded contexts: **Receiving**, **Inventory**, **Allocation**, **Wave Planning**, **Picking**, **Packing**, **Shipping**, **Returns**, **Cycle Count**, and **Replenishment**. Services communicate via an event bus (Apache Kafka or AWS EventBridge) using the transactional outbox pattern to guarantee exactly-once event delivery without distributed transactions. The command-side stores use PostgreSQL with per-warehouse partition keys; read models are projected into Redis (real-time dashboards) and Elasticsearch (search and reporting). The API layer exposes REST and gRPC interfaces secured by JWT + API keys, with role-based access control enforced at the gateway. Infrastructure is cloud-native (AWS/GCP/Azure), containerized on Kubernetes, and auto-scales on queue depth and CPU metrics. All external carrier and ERP integrations use circuit breakers and dead-letter queues.

---

## Documentation Structure

| # | Folder | Contents |
|---|---|---|
| 1 | [`requirements/`](./requirements/) | Scope definition, 60+ functional requirements with acceptance criteria, non-functional requirements, integration test scenarios, traceability matrix, and user stories (40+ stories across 10 epics) |
| 2 | [`analysis/`](./analysis/) | Actor catalog, use case specifications, system context diagram, data flow diagrams, domain event catalog, business rule definitions (BR-1..BR-10), and rule-to-artifact traceability matrix |
| 3 | [`high-level-design/`](./high-level-design/) | Architecture decision records (ADRs), C4 system and container diagrams, domain model, bounded context map, high-level sequence diagrams, and data flow views |
| 4 | [`detailed-design/`](./detailed-design/) | Per-service component designs, entity-relationship diagrams, OpenAPI 3.1 specifications, state machine diagrams for all major entities, wave planning algorithm detail, and internal data models |
| 5 | [`infrastructure/`](./infrastructure/) | Cloud architecture diagram, deployment topology, Kubernetes namespace and resource model, networking and security controls, secret management, CI/CD pipeline design, and observability stack |
| 6 | [`implementation/`](./implementation/) | Delivery phasing plan, service ownership matrix, backend readiness status matrix, code-level C4 diagram, and test coverage mapping |
| 7 | [`edge-cases/`](./edge-cases/) | Bin conflict scenarios, partial pick and split-shipment handling, cycle count collision resolution, offline scanner replay conflict, multi-wave contention, and carrier failover edge cases |

---

## Getting Started

1. **Understand the scope**: Read [`requirements/requirements.md`](./requirements/requirements.md) to understand the functional and non-functional requirements, acceptance criteria, and business rule references.
2. **Study the user workflows**: Read [`requirements/user-stories.md`](./requirements/user-stories.md) for the 40+ operator-perspective user stories with acceptance criteria grouped by epic.
3. **Learn the business rules**: Use [`analysis/business-rules.md`](./analysis/business-rules.md) as the authoritative rule set. Every design decision and API guard traces back to a rule here.
4. **Review the architecture**: Start at [`high-level-design/`](./high-level-design/) for system context, bounded context map, and ADRs before diving into detailed design.
5. **Implement from detailed design**: Use [`detailed-design/api-design.md`](./detailed-design/api-design.md) and [`detailed-design/state-machine-diagrams.md`](./detailed-design/state-machine-diagrams.md) as the primary implementation contract.
6. **Apply infrastructure controls**: Use [`infrastructure/cloud-architecture.md`](./infrastructure/cloud-architecture.md) for deployment topology and [`infrastructure/`](./infrastructure/) for networking and security.
7. **Track delivery progress**: Use [`implementation/backend-status-matrix.md`](./implementation/backend-status-matrix.md) to monitor service and feature readiness.
8. **Handle edge cases last**: Review [`edge-cases/`](./edge-cases/) for exception-path specifications before hardening the implementation.

---

## Documentation Status

| File | Phase | Status | ~Lines |
|---|---|---|---|
| `requirements/requirements.md` | Requirements | Complete | 420+ |
| `requirements/user-stories.md` | Requirements | Complete | 260+ |
| `analysis/business-rules.md` | Analysis | Complete | 200+ |
| `analysis/use-cases.md` | Analysis | Complete | 180+ |
| `analysis/actor-catalog.md` | Analysis | Complete | 80+ |
| `analysis/event-catalog.md` | Analysis | Complete | 150+ |
| `analysis/data-flow-diagrams.md` | Analysis | Complete | 120+ |
| `analysis/context-diagram.md` | Analysis | Complete | 60+ |
| `high-level-design/architecture-decisions.md` | HLD | Complete | 160+ |
| `high-level-design/domain-model.md` | HLD | Complete | 140+ |
| `high-level-design/c4-diagrams.md` | HLD | Complete | 120+ |
| `high-level-design/sequence-diagrams.md` | HLD | Complete | 200+ |
| `high-level-design/data-flow-view.md` | HLD | Complete | 100+ |
| `detailed-design/api-design.md` | Detailed Design | Complete | 280+ |
| `detailed-design/component-design.md` | Detailed Design | Complete | 220+ |
| `detailed-design/data-models.md` | Detailed Design | Complete | 240+ |
| `detailed-design/state-machine-diagrams.md` | Detailed Design | Complete | 180+ |
| `detailed-design/wave-planning-algorithm.md` | Detailed Design | Complete | 140+ |
| `detailed-design/erd.md` | Detailed Design | Complete | 120+ |
| `infrastructure/cloud-architecture.md` | Infrastructure | Complete | 160+ |
| `infrastructure/deployment-topology.md` | Infrastructure | Complete | 140+ |
| `infrastructure/networking.md` | Infrastructure | Complete | 100+ |
| `infrastructure/security-controls.md` | Infrastructure | Complete | 120+ |
| `infrastructure/observability-stack.md` | Infrastructure | Complete | 100+ |
| `infrastructure/ci-cd-pipeline.md` | Infrastructure | Complete | 80+ |
| `implementation/delivery-plan.md` | Implementation | Complete | 120+ |
| `implementation/backend-status-matrix.md` | Implementation | Complete | 100+ |
| `implementation/service-ownership.md` | Implementation | Complete | 60+ |
| `implementation/test-coverage-map.md` | Implementation | Complete | 80+ |
| `implementation/c4-code-diagram.md` | Implementation | Complete | 60+ |
| `edge-cases/bin-conflict-scenarios.md` | Edge Cases | Complete | 100+ |
| `edge-cases/partial-pick-handling.md` | Edge Cases | Complete | 80+ |
| `edge-cases/cycle-count-collision.md` | Edge Cases | Complete | 80+ |
| `edge-cases/offline-scanner-replay.md` | Edge Cases | Complete | 90+ |
| `edge-cases/multi-wave-contention.md` | Edge Cases | Complete | 70+ |
| `edge-cases/carrier-failover.md` | Edge Cases | Complete | 70+ |
| `cross-cutting-operational-guidance.md` | Cross-Cutting | Complete | 200+ |

---

## Domain Entities

Core entities managed by the WMS: **Warehouse**, **Zone**, **Aisle**, **Rack**, **Bin**, **SKU**, **Lot**, **SerialNumber**, **InventoryUnit**, **PurchaseOrder**, **ASN**, **GoodsReceiptNote**, **PutawayTask**, **Wave**, **PickTask**, **PackStation**, **Carton**, **ShipmentOrder**, **Manifest**, **ReturnMerchandiseAuthorization**, **CycleCountPlan**, **CycleCountVariance**, **ReplenishmentRule**, **ReplenishmentTask**, **InventoryTransfer**, **InventoryAdjustment**, **OverrideRecord**, **AuditEvent**, **Carrier**, **CarrierLabel**, **DockDoor**, **TenantClient**.

---

## Business Rules Summary

All design and implementation decisions trace back to ten canonical business rules:

| Rule | Summary |
|---|---|
| BR-1 | Bin capacity (units, weight, volume) must never be exceeded; zone eligibility is always enforced. |
| BR-2 | Wave planning respects carrier cutoff times, picker capacity limits, and zone cluster optimization. |
| BR-3 | All overrides and exceptions require actor identity, reason code, and an expiry timestamp; dual approval above configurable thresholds. |
| BR-4 | Cycle counts are blind; recounts are assigned to a different operator; variances above tolerance require approval before adjustment. |
| BR-5 | All domain events are published via transactional outbox; at-least-once delivery; consumers are idempotent. |
| BR-6 | ASN/PO validation, lot/serial capture, and quarantine flagging gate all inbound inventory from becoming allocatable. |
| BR-7 | Inventory rotation (FIFO/FEFO/LIFO) is enforced at allocation and pick confirmation; ATP cannot drop below zero. |
| BR-8 | Packing is a reconciliation gate; carton close requires quantity match; repack requires dual scan and reason capture. |
| BR-9 | Shipment dispatch is the terminal financial event; idempotent; dock release requires dispatch confirmation. |
| BR-10 | Every exception maps to a deterministic recovery action; repeated exceptions become productized rules; all exceptions are observable. |

Full rule definitions and traceability: [`analysis/business-rules.md`](./analysis/business-rules.md).

---

## Integration Points

| System | Direction | Protocol | Key Events / Operations |
|---|---|---|---|
| ERP (SAP / Oracle / NetSuite) | Inbound & Outbound | Event stream / REST polling | PO and ASN ingest; GRN and inventory position sync; shipment confirmation |
| TMS / Carrier APIs | Outbound | REST / EDI | Label generation, rate shopping, manifest transmission, tracking ingestion |
| OMS (Order Management) | Inbound | Event stream | Shipment order creation, order cancellation, priority updates |
| WCS (Warehouse Control System) | Bidirectional | TCP / MQTT | Conveyor routing signals, sorter divert commands, physical task confirmations |
| Barcode / RFID Scanners | Inbound | REST (batch) / WebSocket | Scan events, offline batch replay, scanner health heartbeat |
| Identity Provider (IdP) | Inbound | OAuth 2.0 / OIDC | JWT issuance, user authentication, role claims |

---

## Canonical Operational Baseline

End-to-end flow invariants, exception classes, RBAC model, observability standards, error codes, performance SLOs, data retention policies, multi-tenancy controls, and disaster recovery procedures are centralized in [`cross-cutting-operational-guidance.md`](./cross-cutting-operational-guidance.md). All business rules BR-1..BR-10 map to design and implementation artifacts in [`analysis/business-rules.md`](./analysis/business-rules.md#major-business-rule-traceability-matrix). Consult both documents before making any design decision that crosses service boundaries.

---

*This documentation set is maintained alongside the implementation. All artifacts are versioned in Git. Raise a pull request to propose additions or corrections.*
