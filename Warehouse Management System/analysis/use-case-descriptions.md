# Use Case Descriptions

## UC-REC-01 Receive and Validate Inbound
- **Primary actor:** Receiving Associate
- **Preconditions:** ASN/PO exists; dock appointment active; device authenticated.
- **Main flow:** scan container -> validate line/lot/qty -> confirm receipt -> generate putaway tasks.
- **Alternate flows:** tolerance breach, unknown SKU, damaged pallet.
- **Postconditions:** receipt transaction committed; inventory state `Received`; audit + event emitted.
- **Rules:** BR-1, BR-2, BR-6, BR-10.

## UC-ALLOC-01 Allocate Orders and Release Wave
- **Primary actor:** Inventory Planner
- **Preconditions:** Orders released from OMS; allocatable stock available.
- **Main flow:** compute candidate stock -> reserve -> build wave -> dispatch tasks.
- **Alternate flows:** insufficient stock (backorder), reservation conflict (retry), policy override.
- **Postconditions:** wave created with deterministic task set; reservations persisted.
- **Rules:** BR-5, BR-7.

## UC-PICKPACK-01 Execute Pick-Pack-Ship
- **Primary actor:** Picker / Pack Operator / Transport Coordinator
- **Preconditions:** Wave active; tasks assigned; stations online.
- **Main flow:** confirm picks -> reconcile package -> generate label -> carrier handoff -> confirm shipment.
- **Alternate flows:** short pick, pack mismatch, carrier timeout.
- **Postconditions:** shipment terminal state set; tracking emitted; decrement finalized.
- **Rules:** BR-7, BR-8, BR-9, BR-10.

## UC-EXC-01 Resolve Operational Exception
- **Primary actor:** Supervisor / Inventory Controller
- **Preconditions:** exception case created from failure branch.
- **Main flow:** inspect evidence -> select action (`retry/reallocate/hold/backorder/override`) -> execute -> close case.
- **Postconditions:** deterministic remediation persisted; evidence attached; KPI updated.
- **Rules:** BR-3, BR-4, BR-10.

## Implementation Notes
- Each use case maps to command handlers, state guards, and audit emitters.
- Alternate flows are not optional; each requires explicit API contract and runbook entry.
