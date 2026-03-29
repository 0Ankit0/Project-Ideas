# Requirements

## Purpose
Define implementation-ready functional and non-functional requirements for the **Warehouse Management System (WMS)**.

## Scope
The scope includes inbound receiving, putaway, allocation, wave planning, picking, packing, shipping, inventory adjustments, and operational exception handling.

## Functional Requirements (Implementation Ready)

| ID | Requirement | Acceptance Criteria | Related Rules |
|---|---|---|---|
| FR-REC-01 | System shall validate ASN/PO line, lot/serial policy, and quantity tolerances during receiving. | Invalid scans are rejected with reason code; mismatch case is created in < 2s; no allocatable inventory created on failed validation. | BR-6, BR-10 |
| FR-REC-02 | System shall generate deterministic putaway tasks after receipt confirmation. | Task priority, destination bin, and travel path are persisted; duplicate scanner submit does not duplicate tasks. | BR-5, BR-6 |
| FR-ALLOC-01 | Allocation engine shall reserve inventory by policy (FIFO/FEFO, zone eligibility, customer priority). | Reservation never exceeds available quantity; conflicting allocations return 409 with retry token. | BR-7 |
| FR-PICK-01 | Pick execution shall enforce reservation references and scan confirmation. | Pick confirm fails without active reservation; short pick emits exception event and reallocation workflow. | BR-7, BR-10 |
| FR-PACK-01 | Packing station shall reconcile picked qty, package content, and label payload before close. | Station blocks close on mismatch; mismatch reason and operator evidence are audited. | BR-8, BR-10 |
| FR-SHIP-01 | Shipment confirmation shall finalize decrement and emit customer-visible tracking event. | Inventory becomes non-reversible except via return/adjustment flow; outbound events emitted once (idempotent). | BR-9, BR-5 |
| FR-EXC-01 | System shall support operator override for approved exception classes. | Override requires approver, reason code, expiry; expired override auto-invalidates pending work. | BR-3, BR-4, BR-10 |

## Non-Functional Requirements

| ID | Requirement | Target |
|---|---|---|
| NFR-AVAIL-01 | API availability (tier-1 command APIs) | 99.9% monthly |
| NFR-LAT-01 | P95 command latency for scan/confirm actions | <= 800 ms |
| NFR-CONS-01 | Stock mutation consistency | Per `warehouse_id + sku + bin` serializable command semantics |
| NFR-OBS-01 | Audit/traceability | 100% state changes include `actor_id`, `correlation_id`, `reason_code` |
| NFR-DR-01 | Disaster recovery objectives | RPO <= 5 min, RTO <= 30 min |

## Exception Handling Requirements
- Every exception must map to deterministic action: **hold**, **reallocate**, **backorder**, or **manual review**.
- Retried operations must reuse idempotency keys and preserve original business intent.
- DLQ processing runbook must include replay guardrails and post-replay reconciliation query.

## Infrastructure-Scale Requirements
- Queue-driven workers must auto-scale on queue depth and lag.
- Wave release must enforce backpressure if downstream carrier/WCS dependency is degraded.
- Partition keys for hot paths must include `warehouse_id` to isolate noisy regions.

## Traceability
- Business rule mapping source: [../analysis/business-rules.md](../analysis/business-rules.md#major-business-rule-traceability-matrix).
- Cross-cutting execution model: [../cross-cutting-operational-guidance.md](../cross-cutting-operational-guidance.md).
