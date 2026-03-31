# Use Case Descriptions

Detailed use case descriptions for the **Resource Lifecycle Management Platform**. Each use case specifies preconditions, main success flow, alternate flows, exception flows, and postconditions. These descriptions are directly traceable to requirements and serve as the basis for integration tests.

---

## UC-01: Provision a New Resource

**Actor**: Resource Manager  
**Goal**: Register a new physical or virtual asset in the platform catalog.  
**Related Requirements**: FR-PROV-01 to FR-PROV-05

### Preconditions
- Actor is authenticated and holds the `resource_manager` role.
- A valid resource template exists for the target category.
- The tenant's provisioning quota has not been reached.

### Main Success Flow
1. Resource Manager submits a `POST /resources` command with template reference, asset tag, condition grade, location, and cost centre.
2. API Gateway validates JWT and checks the `resource:write` scope.
3. Command Handler validates the request against the template schema.
4. Policy Engine evaluates tenant entitlement and provisioning quota.
5. Provisioning Service assigns a unique `resource_id` and writes the record in `Pending` state.
6. Mandatory field check passes → resource transitions to `Available`.
7. `rlmp.resource.provisioned` event is published via outbox.
8. API returns `201 Created` with `resource_id` and initial state.

### Alternate Flow A – Bulk Provisioning
1a. Resource Manager uploads a CSV with up to 1,000 rows.  
1b. System validates all rows; any validation failures are reported per-row.  
1c. If all rows pass, batch is committed atomically; `rlmp.resource.provisioned` is emitted for each record.  
1d. If any row fails, the entire batch is rolled back; the caller receives a structured error report.

### Exception Flow – Validation Failure
3a. Schema validation fails (missing mandatory field).  
3b. System returns `400 Bad Request` with `error_code: VALIDATION_FAILED` and the list of invalid fields.  
3c. No resource record is created.

### Exception Flow – Quota Exceeded
4a. Policy Engine denies the request due to provisioning quota.  
4b. System returns `422 Unprocessable Entity` with `error_code: QUOTA_EXCEEDED`.

### Postconditions
- Resource exists in catalog with state `Available`.
- `rlmp.resource.provisioned` event visible on event bus.
- Audit record written with `actor_id` and `correlation_id`.

---

## UC-02: Reserve a Resource

**Actor**: Requestor  
**Goal**: Place a time-bound hold on a specific resource for a future use window.  
**Related Requirements**: FR-ALLOC-01, FR-ALLOC-02, FR-ALLOC-03, FR-ALLOC-04

### Preconditions
- Requestor is authenticated.
- Target resource is in `Available` state.
- Requested window does not conflict with existing reservations.
- Requestor has not exceeded their quota.

### Main Success Flow
1. Requestor submits `POST /reservations` with `resource_id`, `start_at`, `end_at`, `priority`, and `idempotency_key`.
2. API Gateway validates token and `reservation:create` scope.
3. Allocation Service acquires a short-lived optimistic lock on `(resource_id, window)`.
4. Policy Engine evaluates quota, eligibility, and time-limit rules.
5. System checks for window overlap against existing `CONFIRMED` reservations.
6. Reservation record is created in `CONFIRMED` state; SLA timer is set for checkout window close.
7. `rlmp.reservation.created` event published.
8. API returns `201 Created` with `reservation_id` and `sla_due_at`.

### Alternate Flow A – Priority Displacement
4a. A higher-priority reservation from another requestor targets the same window.  
4b. Policy Engine permits displacement.  
4c. Lower-priority `CONFIRMED` reservation is cancelled with reason `PRIORITY_DISPLACED`.  
4d. `rlmp.reservation.priority_displaced` event published; displaced requestor notified.  
4e. New reservation is confirmed.

### Exception Flow – Window Conflict
5a. Overlap with existing confirmed reservation detected.  
5b. System returns `409 Conflict` with `error_code: WINDOW_CONFLICT`, the conflicting `reservation_id`, and a list of alternative available windows.

### Exception Flow – Duplicate Request
1a. Request carries an `idempotency_key` already used by this tenant.  
1b. System returns `200 OK` with the original reservation response (no new record created).

### Postconditions
- Reservation in `CONFIRMED` state; resource availability blocked for the window.
- SLA timer active for checkout deadline.
- `rlmp.reservation.created` visible on event bus.

---

## UC-03: Check Out a Resource

**Actor**: Custodian  
**Goal**: Physically or logically take possession of a reserved resource, initiating the allocation.  
**Related Requirements**: FR-ALLOC-05, FR-CUST-01, FR-CUST-02

### Preconditions
- A `CONFIRMED` reservation exists for the resource.
- Actor is authenticated as the designated custodian.
- Resource is in `Available` or `Reserved` state.
- Checkout is occurring within the SLA window.

### Main Success Flow
1. Custodian scans the asset tag or submits `POST /allocations` referencing `reservation_id`.
2. Custody Service validates the reservation is active and within the checkout window.
3. Condition assessment is recorded (grade + optional notes).
4. Resource transitions: `Available → Reserved → Allocated` (or directly `Available → Allocated` for immediate allocation).
5. Allocation record created; `checkout_at` and `due_at` are persisted.
6. Overdue Detector registers the allocation for future monitoring.
7. `rlmp.allocation.checked_out` event published.
8. API returns `201 Created` with `allocation_id`.

### Exception Flow – Checkout Outside Window
2a. Current time is past `sla_due_at` for the reservation.  
2b. System returns `422` with `error_code: CHECKOUT_WINDOW_EXPIRED`; reservation is expired.

### Exception Flow – Resource Not Ready
2a. Resource is in `Maintenance` or `Inspection` state.  
2b. System returns `409` with `error_code: RESOURCE_UNAVAILABLE` and current state.

### Postconditions
- Resource in `Allocated` state; allocation record active.
- Reservation in `CONVERTED` state.
- Overdue timer set for `due_at`.
- Audit record written.

---

## UC-04: Check In a Resource

**Actor**: Custodian or Operations  
**Goal**: Return a resource and record post-use condition.  
**Related Requirements**: FR-CUST-01, FR-CUST-02, FR-CUST-03, FR-SETT-01

### Preconditions
- Allocation exists in `ACTIVE` or `OVERDUE` state.
- Actor is the custodian or an authorized operations engineer.

### Main Success Flow
1. Custodian scans asset tag or submits `POST /allocations/{id}/checkin` with condition grade and notes.
2. Custody Service validates actor authorization.
3. Condition delta is computed: `checkout_condition` vs `checkin_condition`.
4. If delta = `NONE` or `MINOR` → resource transitions to `Inspection`.
5. If delta = `MAJOR` or `LOSS` → Incident Service opens an incident case; resource transitions to `Inspection` with hold.
6. `rlmp.allocation.checked_in` event published with `condition_delta`.
7. Inspection workflow determines next state: `Available` (pass) or `Maintenance` / `Incident Hold` (fail).
8. API returns `200 OK` with allocation summary and any incident `case_id`.

### Exception Flow – Condition Dispute
5a. Custodian disputes the pre-existing condition grade recorded at checkout.  
5b. Dispute is flagged on the incident case with custodian notes.  
5c. Resource remains in `Inspection` hold pending manual review.

### Postconditions
- Allocation in `RETURNED` state; `checkin_at` recorded.
- Resource in `Inspection` → `Available` or `Maintenance` depending on outcome.
- If condition delta was Major or Loss: incident case created.
- Audit record written.

---

## UC-05: Handle Overdue Allocation

**Actor**: System (Overdue Detector), Operations  
**Goal**: Detect and escalate allocations that have not been returned by their due date.  
**Related Requirements**: FR-OVER-01, FR-OVER-02, FR-OVER-03

### Preconditions
- An allocation is in `ACTIVE` state.
- Current UTC time > `due_at`.

### Main Success Flow
1. Overdue Detector (scheduled job, 5-min interval) scans active allocations.
2. Overdue allocation detected → allocation state updated to `OVERDUE`.
3. `rlmp.allocation.overdue` event emitted (step 1 of escalation ladder).
4. Notification Service sends reminder to custodian (T+0).
5. If no check-in within 4 h → `rlmp.escalation.warned` emitted; custodian + manager notified (T+4 h).
6. If no check-in within 24 h → `rlmp.escalation.manager_escalated` emitted; escalated to manager (T+24 h).
7. If no check-in within 48 h → `rlmp.escalation.forced_return_eligible` emitted; forced-return available in ops UI.

### Alternate Flow – Forced Return
7a. Operations engineer initiates forced return via `POST /allocations/{id}/force-return` with `approver_id` and `reason_code`.  
7b. Custody Service validates approver role and reason code.  
7c. Allocation transitions to `FORCED_RETURN` state.  
7d. `rlmp.allocation.forced_return` event published; custodian and manager notified.  
7e. Inspection workflow initiated.

### Postconditions
- Allocation state = `OVERDUE` or `FORCED_RETURN`.
- All escalation steps recorded in audit log.
- Incident case opened at forced-return or critical overdue threshold.

---

## UC-06: Decommission a Resource

**Actor**: Resource Manager, Compliance Officer  
**Goal**: Permanently retire a resource from service with financial and compliance closure.  
**Related Requirements**: FR-DECOM-01, FR-DECOM-02, FR-DECOM-03

### Preconditions
- Resource is in `Available` state (no active allocations or reservations).
- All incident cases linked to this resource are `CLOSED`.
- All settlement cases are resolved with zero outstanding balance.
- Retention lock has expired or been released by Compliance Officer.

### Main Success Flow
1. Resource Manager submits `POST /resources/{id}/decommission` with `reason` and `disposal_method`.
2. Decommission Orchestrator checks all preconditions (settlement closure, retention lock, active allocations).
3. If asset value ≥ configured threshold → Approval workflow triggered; task assigned to authorized approver.
4. Approver reviews and grants approval.
5. Resource transitions to `Decommissioning` state.
6. `rlmp.resource.decommission_approved` event published.
7. Archive Job queues the resource record for cold-storage archival.
8. Resource transitions to `Decommissioned` (terminal state).
9. `rlmp.resource.decommissioned` and `rlmp.resource.archived` events published.
10. API returns `200 OK` with decommission summary and `archive_manifest_id`.

### Exception Flow – Blocking Condition
2a. Open settlement case or active allocation detected.  
2b. System returns `409` with `error_code: DECOMMISSION_BLOCKED`, listing blocking entity IDs.

### Exception Flow – Retention Lock Active
2c. Compliance retention lock not yet expired.  
2d. System returns `409` with `error_code: RETENTION_LOCK_ACTIVE` and `lock_expires_at`.

### Postconditions
- Resource in `Decommissioned` state (terminal; no further transitions).
- All records archived to cold storage.
- `rlmp.resource.decommissioned` and `rlmp.resource.archived` events visible on event bus.

---

## Cross-References

- Use case diagram: [use-case-diagram.md](./use-case-diagram.md)
- Sequence diagrams for key flows: [../detailed-design/sequence-diagrams.md](../detailed-design/sequence-diagrams.md)
- State transitions: [../detailed-design/state-machine-diagrams.md](../detailed-design/state-machine-diagrams.md)
- Business rules referenced: [business-rules.md](./business-rules.md)
