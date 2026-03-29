# User Stories

## Purpose
Define implementation-ready user stories with explicit acceptance criteria and operational edge behavior.

## Receiving and Putaway Stories

### US-REC-01 - Receive pallet against ASN
**As** a receiving associate
**I want** to scan ASN and pallet identifiers
**So that** inventory is validated before becoming allocatable.

**Acceptance Criteria**
1. Invalid ASN or over-tolerance quantity returns actionable error code and creates discrepancy case.
2. On success, receipt transaction and audit event are persisted atomically.
3. Duplicate scan submission with same idempotency key returns original result only.

### US-REC-02 - Supervisor variance override
**As** a supervisor
**I want** to approve quantity variance within tolerance policy
**So that** dock flow can continue while preserving controls.

**Acceptance Criteria**
1. Override requires reason code, approver identity, and expiry timestamp.
2. System records both original variance and override evidence.
3. Expired overrides are rejected and trigger follow-up task.

## Picking and Packing Stories

### US-PICK-01 - Execute pick with reservation
**As** a picker
**I want** to pick by scanner-confirmed tasks
**So that** stock decrements align with reservation commitments.

**Acceptance Criteria**
1. Pick confirm must reference active task and reservation line.
2. Short pick path offers alternate-bin reallocation before backorder.
3. Every short pick emits event for SLA and customer-impact tracking.

### US-PACK-01 - Pack with reconciliation gate
**As** a pack station operator
**I want** to close carton only after line-level reconciliation
**So that** mis-ships are prevented.

**Acceptance Criteria**
1. Packed quantity must equal confirmed picks per shipment line.
2. Label generation failure moves parcel to `PackingBlocked` queue.
3. Repack flow requires dual scan and reason capture.

## Shipping and Exception Stories

### US-SHIP-01 - Confirm shipment handoff
**As** a transportation coordinator
**I want** manifest confirmation to finalize shipment state
**So that** tracking and downstream billing trigger once.

**Acceptance Criteria**
1. Shipment confirmation emits outbound event exactly once from outbox.
2. Carrier API timeout retries with exponential backoff and circuit breaker.
3. Dock release is blocked when label/manifest confirmation is missing.

### US-EXC-01 - Resolve scanner replay conflict
**As** an inventory controller
**I want** to resolve offline scanner replay collisions
**So that** inventory remains consistent.

**Acceptance Criteria**
1. Version conflict creates review task with conflicting event snapshots.
2. Resolver can choose merge or compensating adjustment path.
3. Resolution emits audit event and recalculates affected projections.

## Rule Coverage
- BR-6: Receiving validation and putaway gating.
- BR-7: Reservation-coupled picking.
- BR-8: Packing reconciliation.
- BR-9: Shipment confirmation as terminal handoff.
- BR-10: Deterministic exception recovery.
