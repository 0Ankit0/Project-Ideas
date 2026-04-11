# System Sequence Diagrams

System-level sequence diagrams for the **Resource Lifecycle Management Platform**'s primary flows. These diagrams show the interaction between external actors and system components, with timing and protocol details.

---

## 1. Resource Provisioning Sequence

```mermaid
sequenceDiagram
  participant RM as Resource Manager
  participant GW as API Gateway
  participant IAM as Identity Provider
  participant PS as Provisioning Service
  participant PE as Policy Engine
  participant DB as PostgreSQL
  participant OB as Outbox Relay
  participant EB as Event Bus

  RM->>GW: POST /resources {template_id, asset_tag, condition, location, cost_centre}
  GW->>IAM: Validate JWT (cache miss or expired)
  IAM-->>GW: Claims {user_id, roles, tenant_id}
  GW->>PS: Forward command with auth context
  PS->>PS: Validate schema against template
  alt Schema invalid
    PS-->>GW: 400 Validation Error
    GW-->>RM: 400 {error_code, field_errors[]}
  end
  PS->>PE: evaluate({action: PROVISION, tenant_id, category})
  PE-->>PS: permit (quota OK)
  PS->>DB: BEGIN TX and INSERT resource (state=PENDING) and INSERT outbox and INSERT audit and COMMIT
  PS->>PS: Check mandatory fields → transition to AVAILABLE
  PS->>DB: UPDATE resource state=AVAILABLE and INSERT audit
  PS-->>GW: 201 {resource_id, state: AVAILABLE}
  GW-->>RM: 201 {resource_id}
  OB->>DB: SELECT pending outbox records
  OB->>EB: Publish rlmp.resource.provisioned
  EB-->>OB: Ack
  OB->>DB: Mark outbox record delivered
```

---

## 2. Reservation Creation Sequence

```mermaid
sequenceDiagram
  participant REQ as Requestor
  participant GW as API Gateway
  participant AS as Allocation Service
  participant PE as Policy Engine
  participant DB as PostgreSQL
  participant RC as Redis Cache
  participant EB as Event Bus
  participant NS as Notification Service

  REQ->>GW: POST /reservations {resource_id, start_at, end_at, priority, idempotency_key}
  GW->>RC: GET idempotency_key
  alt Key exists (duplicate)
    RC-->>GW: Cached response
    GW-->>REQ: 200 (original reservation data)
  end
  GW->>AS: Forward command
  AS->>DB: SELECT FOR UPDATE SKIP LOCKED WHERE resource_id=? AND window overlaps
  alt Conflict found
    DB-->>AS: Conflicting reservation rows
    AS-->>GW: 409 {error_code: WINDOW_CONFLICT, alternatives[]}
    GW-->>REQ: 409
  end
  AS->>PE: evaluate({quota, eligibility, priority})
  PE-->>AS: permit
  AS->>DB: BEGIN TX and INSERT reservation(CONFIRMED) and SET sla_due_at and INSERT outbox and INSERT audit and COMMIT
  AS->>RC: SET idempotency_key → reservation_id (TTL 24h)
  AS-->>GW: 201 {reservation_id, sla_due_at}
  GW-->>REQ: 201
  EB->>NS: rlmp.reservation.created → send confirmation to Requestor
```

---

## 3. Checkout Sequence

```mermaid
sequenceDiagram
  participant CUST as Custodian
  participant GW as API Gateway
  participant CS as Custody Service
  participant AS as Allocation Service
  participant OD as Overdue Detector
  participant DB as PostgreSQL
  participant EB as Event Bus

  CUST->>GW: POST /allocations {reservation_id, condition_grade, condition_notes}
  GW->>CS: Forward command
  CS->>AS: GET reservation(reservation_id) — validate state=CONFIRMED, window open
  alt Reservation expired
    AS-->>CS: error CHECKOUT_WINDOW_EXPIRED
    CS-->>GW: 422
    GW-->>CUST: 422
  end
  CS->>DB: SELECT resource WHERE resource_id=? FOR UPDATE
  alt Resource not AVAILABLE/RESERVED
    DB-->>CS: state=MAINTENANCE
    CS-->>GW: 409 RESOURCE_UNAVAILABLE
    GW-->>CUST: 409
  end
  CS->>DB: BEGIN TX\n  UPDATE resource state=ALLOCATED\n  INSERT allocation {checkout_at, due_at, checkout_condition}\n  UPDATE reservation state=CONVERTED\n  INSERT outbox(rlmp.allocation.checked_out)\n  INSERT audit\nCOMMIT
  CS->>OD: RegisterAllocation(allocation_id, due_at)
  CS-->>GW: 201 {allocation_id, due_at}
  GW-->>CUST: 201
  EB-->>CUST: Reminder scheduled at due_at-24h and due_at-2h
```

---

## 4. Check-In and Condition Assessment Sequence

```mermaid
sequenceDiagram
  participant CUST as Custodian
  participant GW as API Gateway
  participant CS as Custody Service
  participant IS as Incident Service
  participant DB as PostgreSQL
  participant EB as Event Bus

  CUST->>GW: POST /allocations/{id}/checkin {condition_grade, condition_notes}
  GW->>CS: Forward command
  CS->>DB: SELECT allocation WHERE allocation_id=? AND state IN (ACTIVE, OVERDUE)
  CS->>CS: Compute condition_delta (checkout vs checkin grade)
  CS->>DB: BEGIN TX\n  UPDATE allocation {checkin_at, checkin_condition, condition_delta, state=RETURNED}\n  UPDATE resource state=INSPECTION\n  INSERT outbox(rlmp.allocation.checked_in)\n  INSERT audit\nCOMMIT
  alt condition_delta = MAJOR or LOSS
    CS->>IS: OpenIncident({resource_id, allocation_id, case_type, severity})
    IS->>DB: INSERT incident_case {state=OPEN, sla_due_at}
    IS->>EB: Publish rlmp.incident.opened
  end
  CS-->>GW: 200 {allocation_id, condition_delta, case_id?}
  GW-->>CUST: 200
  Note over DB, EB: Inspection workflow runs asynchronously\nresource transitions AVAILABLE or MAINTENANCE
```

---

## 5. Overdue Detection and Escalation Sequence

```mermaid
sequenceDiagram
  participant CRON as Cron Scheduler
  participant OD as Overdue Detector
  participant DB as PostgreSQL
  participant EE as Escalation Engine
  participant EB as Event Bus
  participant NS as Notification Service
  participant OPS as Operations

  loop Every 5 minutes
    CRON->>OD: Trigger scan
    OD->>DB: SELECT allocations WHERE state=ACTIVE AND due_at < NOW()
    alt No overdue allocations
      DB-->>OD: Empty result set
    end
    DB-->>OD: Overdue allocations list
    OD->>DB: UPDATE allocations SET state=OVERDUE WHERE id IN (...)
    OD->>EB: Publish rlmp.allocation.overdue (per allocation, escalation_step=1)
    EB->>NS: Send reminder to custodian (T+0)
  end

  Note over EE: Subsequent escalation steps triggered by timer
  EE->>EB: rlmp.escalation.warned (T+4h) → NS sends warning to custodian + manager
  EE->>EB: rlmp.escalation.manager_escalated (T+24h) → NS notifies manager
  EE->>EB: rlmp.escalation.forced_return_eligible (T+48h) → Ops dashboard flagged

  OPS->>GW: POST /allocations/{id}/force-return {approver_id, reason_code}
  GW->>CS: Execute forced return
  CS->>DB: UPDATE allocation state=FORCED_RETURN and INSERT outbox and INSERT audit
  EB->>NS: Notify custodian + manager of forced return
```

---

## 6. Settlement Posting Sequence

```mermaid
sequenceDiagram
  participant IS as Incident Service
  participant SS as Settlement Service
  participant RC as Rate Card Engine
  participant DB as PostgreSQL
  participant EB as Event Bus
  participant LDG as Financial Ledger
  participant FIN as Finance

  IS->>SS: rlmp.incident.resolved (case_id, resolution_outcome)
  SS->>RC: CalculateCharge(case_id, condition_delta, rate_card_id)
  RC-->>SS: {charge_type, amount, currency}
  SS->>DB: INSERT settlement_record {state=PENDING}
  SS->>EB: Publish rlmp.settlement.calculated
  FIN->>GW: POST /settlements/{id}/approve
  GW->>SS: Approve settlement
  SS->>DB: BEGIN TX\n  UPDATE settlement state=APPROVED\n  INSERT outbox(rlmp.settlement.posted)\n  INSERT audit\nCOMMIT
  EB->>LDG: rlmp.settlement.posted (idempotency_key=settlement_id)
  LDG-->>EB: Ack (journal entry created)
  SS->>DB: UPDATE settlement SET ledger_event_id=?, state=POSTED
```

---

## Cross-References

- Detailed sequence diagrams: [../detailed-design/sequence-diagrams.md](../detailed-design/sequence-diagrams.md)
- Activity diagrams: [../analysis/activity-diagrams.md](../analysis/activity-diagrams.md)
- State machine: [../detailed-design/state-machine-diagrams.md](../detailed-design/state-machine-diagrams.md)

---

## 7. Maintenance Escalation and Return-to-Service Sequence

```mermaid
sequenceDiagram
  participant OPS as Operations
  participant GW as API Gateway
  participant MS as Maintenance Service
  participant PE as Policy Engine
  participant DB as PostgreSQL
  participant EB as Event Bus
  participant NS as Notification Service

  OPS->>GW: POST /maintenance/{resource_id}/start {issue_type, severity}
  GW->>MS: Forward command with operator context
  MS->>DB: SELECT resource FOR UPDATE
  MS->>PE: evaluate({action: START_MAINTENANCE, severity, tenant_id})
  PE-->>MS: permit
  MS->>DB: BEGIN TX\nUPDATE resource state=MAINTENANCE\nINSERT maintenance_ticket state=OPEN\nINSERT outbox rlmp.maintenance.started\nCOMMIT
  MS-->>GW: 202 {ticket_id, state: "OPEN"}
  EB->>NS: rlmp.maintenance.started → notify requester and manager

  OPS->>GW: POST /maintenance/{ticket_id}/complete {resolution_notes}
  GW->>MS: Complete ticket
  MS->>DB: BEGIN TX\nUPDATE maintenance_ticket state=COMPLETED\nUPDATE resource state=INSPECTION\nINSERT outbox rlmp.maintenance.completed\nCOMMIT
  MS->>EB: Publish rlmp.maintenance.completed
  EB->>NS: Notify inspection team to validate readiness

  OPS->>GW: POST /resources/{resource_id}/return-to-service
  GW->>MS: Request return to service
  MS->>DB: UPDATE resource state=AVAILABLE and set maintenance_cleared_at
  GW-->>OPS: 200 {resource_id, state: "AVAILABLE"}
```

