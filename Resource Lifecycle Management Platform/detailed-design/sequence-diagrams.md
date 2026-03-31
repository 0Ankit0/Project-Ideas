# Sequence Diagrams

Low-level sequence diagrams for the **Resource Lifecycle Management Platform**'s internal service interactions. These diagrams show service-to-service calls, database operations, and outbox/event bus patterns.

---

## 1. Concurrent Reservation Conflict Resolution

```mermaid
sequenceDiagram
  participant ClientA as Client A
  participant ClientB as Client B
  participant AS as Allocation Service
  participant Lock as Lock Manager (SELECT FOR UPDATE)
  participant DB as PostgreSQL
  participant PE as Policy Engine

  par Concurrent requests
    ClientA->>AS: POST /reservations {resource_id, window: 9-17, priority: 5}
    ClientB->>AS: POST /reservations {resource_id, window: 10-15, priority: 5}
  end

  AS->>Lock: Acquire row lock on resource_id (SELECT FOR UPDATE SKIP LOCKED)
  Note over Lock: ClientA wins the lock\nClientB queues behind it

  AS->>DB: SELECT overlapping CONFIRMED reservations
  DB-->>AS: [] (no conflict for ClientA)
  AS->>PE: Evaluate quota + eligibility (ClientA)
  PE-->>AS: permit
  AS->>DB: INSERT reservation (ClientA, CONFIRMED); INSERT outbox; COMMIT
  AS-->>ClientA: 201 {reservation_id}

  Note over Lock: ClientB lock acquired
  AS->>DB: SELECT overlapping CONFIRMED reservations
  DB-->>AS: [{ClientA reservation}] — overlap detected
  AS-->>ClientB: 409 {error_code: WINDOW_CONFLICT, alternatives: [{start: 17:00}]}
```

---

## 2. Checkout with Condition Recording

```mermaid
sequenceDiagram
  participant Cust as Custodian
  participant API as Core API
  participant CS as Custody Service
  participant SM as State Machine
  participant DB as PostgreSQL
  participant OD as Overdue Detector
  participant EB as Event Bus

  Cust->>API: POST /allocations {reservation_id, condition_grade: "A"}
  API->>CS: CheckoutCommand(reservation_id, custodian_id, condition_grade)
  CS->>DB: SELECT reservation WHERE id=? AND state='CONFIRMED'
  DB-->>CS: reservation {resource_id, sla_due_at, due_at}
  CS->>CS: Verify current_time < sla_due_at
  CS->>DB: SELECT resource WHERE id=? FOR UPDATE
  DB-->>CS: resource {state: 'RESERVED', version: 3}
  CS->>SM: Transition(resource, RESERVED → ALLOCATED)
  SM->>SM: Guard: reservation active, actor=custodian, within window ✓
  SM->>DB: BEGIN TX
  SM->>DB: UPDATE resources SET state='ALLOCATED', version=4 WHERE id=? AND version=3
  SM->>DB: INSERT allocations {checkout_at, due_at, checkout_condition='A', state='ACTIVE'}
  SM->>DB: UPDATE reservations SET state='CONVERTED'
  SM->>DB: INSERT outbox {event=checked_out, payload}
  SM->>DB: INSERT audit_event {command='CHECKOUT', before, after, actor_id, hash}
  SM->>DB: COMMIT
  CS->>OD: RegisterSLATimer(allocation_id, due_at)
  CS-->>API: AllocationResult {allocation_id, state:'ACTIVE', due_at}
  API-->>Cust: 201 {allocation_id}
  Note over EB: Outbox relay publishes rlmp.allocation.checked_out
```

---

## 3. Overdue Detection and Forced Return

```mermaid
sequenceDiagram
  participant CRON as Scheduler
  participant OD as Overdue Detector
  participant DB as PostgreSQL
  participant EE as Escalation Engine
  participant EB as Event Bus
  participant NS as Notification Service
  participant OPS as Operations
  participant CS as Custody Service

  CRON->>OD: trigger (every 5 min)
  OD->>DB: SELECT allocation_id FROM allocations\nWHERE state='ACTIVE' AND due_at < NOW()
  DB-->>OD: [{allocation_id: "abc", custodian_id: "...", due_at: "..."}]
  OD->>DB: UPDATE allocations SET state='OVERDUE' WHERE id IN (...)
  OD->>EB: Publish rlmp.allocation.overdue {allocation_id, escalation_step: 1, due_at}
  EB->>EE: Consume overdue event
  EE->>NS: Send T+0 reminder to custodian
  EE->>EE: Schedule step 2 timer (T+4h)

  Note over EE: 4 hours later
  EE->>EB: Publish rlmp.escalation.warned {step: 2}
  EB->>NS: Send warning to custodian + manager
  EE->>EE: Schedule step 3 timer (T+24h from overdue)

  Note over EE: 24 hours after overdue
  EE->>EB: Publish rlmp.escalation.manager_escalated {step: 3}
  EB->>NS: Notify manager

  Note over EE: 48 hours after overdue
  EE->>EB: Publish rlmp.escalation.forced_return_eligible {step: 4}
  Note over OPS: Ops sees flag in dashboard

  OPS->>CS: POST /allocations/abc/force-return {approver_id, reason_code}
  CS->>DB: Validate approver role + reason_code in override catalog
  CS->>DB: BEGIN TX
  CS->>DB: UPDATE allocations SET state='FORCED_RETURN'
  CS->>DB: UPDATE resources SET state='INSPECTION'
  CS->>DB: INSERT outbox {event=forced_return, approver_id}
  CS->>DB: INSERT audit_event
  CS->>DB: COMMIT
  CS-->>OPS: 200 {state: FORCED_RETURN}
```

---

## 4. Settlement Calculation and Posting

```mermaid
sequenceDiagram
  participant IS as Incident Service
  participant SS as Settlement Service
  participant RC as Rate Card Engine
  participant DB as PostgreSQL
  participant EB as Event Bus
  participant FIN as Finance
  participant LDG as Financial Ledger

  IS->>EB: Publish rlmp.incident.resolved {case_id, allocation_id, outcome: SETTLEMENT_REQUIRED}
  EB->>SS: Consume resolved event
  SS->>DB: SELECT incident_case WHERE case_id=?
  SS->>DB: SELECT allocation WHERE id=? (for condition_delta, checkout_at, due_at)
  SS->>RC: CalculateCharge(condition_delta='MAJOR', rate_card_id, currency='USD')
  RC-->>SS: {charge_type: DAMAGE, amount: 350.00, currency: USD}
  SS->>DB: INSERT settlement_records {case_id, charge_type, amount, state='PENDING'}
  SS->>EB: Publish rlmp.settlement.calculated {settlement_id, amount}

  FIN->>API: GET /settlements?case_id=...
  FIN->>API: POST /settlements/{id}/approve
  SS->>DB: BEGIN TX
  SS->>DB: UPDATE settlement_records SET state='APPROVED'
  SS->>DB: INSERT outbox {event=settlement.posted, payload, idempotency_key=settlement_id}
  SS->>DB: INSERT audit_event
  SS->>DB: COMMIT
  Note over EB: Outbox relay delivers to event bus
  EB->>LDG: rlmp.settlement.posted {settlement_id, amount, currency}
  LDG-->>EB: Ack
  SS->>DB: UPDATE settlement_records SET state='POSTED', ledger_event_id=?
  EB->>EB: Publish rlmp.settlement.posted (for audit)
```

---

## 5. Decommission Orchestration

```mermaid
sequenceDiagram
  participant MGR as Resource Manager
  participant DO as Decommission Orchestrator
  participant DB as PostgreSQL
  participant Approval as Approval Service
  participant Archive as Archive Job
  participant CS as Cold Storage
  participant EB as Event Bus

  MGR->>DO: POST /resources/{id}/decommission {reason, disposal_method}
  DO->>DB: SELECT resource WHERE id=? (state, acquisition_cost, policy_profile_id)
  DO->>DB: SELECT COUNT(*) FROM allocations WHERE resource_id=? AND state IN ('ACTIVE','OVERDUE')
  DO->>DB: SELECT COUNT(*) FROM incident_cases WHERE resource_id=? AND state NOT IN ('CLOSED')
  DO->>DB: SELECT COUNT(*) FROM settlement_records WHERE state IN ('PENDING','DISPUTED')
  DO->>DB: SELECT retention_lock WHERE resource_id=? AND expires_at > NOW()
  Note over DO: All checks must return 0 / no lock
  alt Any blocking condition
    DO-->>MGR: 409 DECOMMISSION_BLOCKED {blocking_entities[]}
  end

  alt acquisition_cost >= approval_threshold
    DO->>Approval: CreateApprovalTask(resource_id, approver_role='resource_manager')
    Approval-->>DO: task_id
    DO-->>MGR: 202 {requires_approval: true, task_id}
    Note over Approval: Manager approves task
    Approval->>DO: ApprovalGranted(resource_id, approver_id)
  end

  DO->>DB: BEGIN TX
  DO->>DB: UPDATE resources SET state='DECOMMISSIONING'
  DO->>DB: INSERT outbox {event=decommission_approved}
  DO->>DB: INSERT audit_event
  DO->>DB: COMMIT
  DO->>Archive: ScheduleArchive(resource_id)
  Archive->>DB: SELECT all records for resource_id (resource, reservations, allocations, incidents, settlements, audit_events)
  Archive->>CS: Write archive bundle {manifest_id, records}
  CS-->>Archive: Write confirmed
  Archive->>DB: BEGIN TX
  Archive->>DB: UPDATE resources SET state='DECOMMISSIONED'
  Archive->>DB: INSERT outbox {event=decommissioned, manifest_id}
  Archive->>DB: COMMIT
  EB-->>MGR: rlmp.resource.decommissioned notification
```

---

## Cross-References

- System sequence diagrams (external actor view): [../high-level-design/system-sequence-diagrams.md](../high-level-design/system-sequence-diagrams.md)
- Lifecycle orchestration (state transition detail): [lifecycle-orchestration.md](./lifecycle-orchestration.md)
- State machine (all entity state graphs): [state-machine-diagrams.md](./state-machine-diagrams.md)
