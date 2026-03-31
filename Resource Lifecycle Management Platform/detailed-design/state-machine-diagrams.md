# State Machine Diagrams

Complete state machine diagrams for every stateful entity in the **Resource Lifecycle Management Platform**.

---

## 1. Resource State Machine

```mermaid
stateDiagram-v2
  direction LR
  [*] --> PENDING : provision()

  PENDING --> AVAILABLE : completeProvisioning()\n[all mandatory fields present]
  PENDING --> EXCEPTION : flagForReview()\n[validation issues detected]

  AVAILABLE --> RESERVED : confirmReservation(reservation_id)\n[no overlap, quota OK]
  AVAILABLE --> MAINTENANCE : scheduleMaintenance(ticket_id)\n[maintenance window set]
  AVAILABLE --> DECOMMISSIONING : approveDecommission()\n[preconditions met, approved]

  RESERVED --> AVAILABLE : cancelReservation(reason) / expireReservation()
  RESERVED --> ALLOCATED : checkout(condition_grade)\n[within SLA window, custodian verified]

  ALLOCATED --> ALLOCATED : transferCustody(new_custodian)\n[eligibility verified]
  ALLOCATED --> RETURNING : initiateReturn()\n[custodian action]
  ALLOCATED --> INSPECTION : forceReturn(approver, reason)\n[override granted]

  RETURNING --> INSPECTION : confirmReturn(condition_grade)\n[scan confirmed]

  INSPECTION --> AVAILABLE : passInspection()\n[grade A or B, no open incident]
  INSPECTION --> MAINTENANCE : failInspection(defect_notes)\n[grade C or D]
  INSPECTION --> EXCEPTION : escalateException()\n[loss confirmed or dispute unresolved]

  MAINTENANCE --> AVAILABLE : completeMaintenance()\n[grade A or B after repair]
  MAINTENANCE --> DECOMMISSIONING : approveDecommission()

  EXCEPTION --> AVAILABLE : resolveException()\n[cleared for use]
  EXCEPTION --> DECOMMISSIONING : approveDecommission()

  DECOMMISSIONING --> DECOMMISSIONED : archiveComplete(manifest_id)
  DECOMMISSIONED --> [*]
```

**Guard Matrix for Resource**:

| Transition | Guard Conditions |
|---|---|
| `PENDING → AVAILABLE` | All of: category, asset_tag, condition_grade, location_id, cost_centre, policy_profile_id present |
| `AVAILABLE → RESERVED` | No CONFIRMED reservation overlapping window; requestor quota not exceeded; requestor role in eligible_roles |
| `RESERVED → ALLOCATED` | Current UTC within [reservation.start_at, reservation.sla_due_at]; actor = reservation.requestor_id or delegated custodian |
| `ALLOCATED → INSPECTION` (forced) | approver holds `operations` role; reason_code in override catalog; override not expired |
| `* → DECOMMISSIONING` | No active allocation or reservation; all incident_cases CLOSED; all settlement_records POSTED or VOIDED; retention lock expired |
| `DECOMMISSIONING → DECOMMISSIONED` | Archive manifest ID present; cold storage write confirmed |

---

## 2. Reservation State Machine

```mermaid
stateDiagram-v2
  direction LR
  [*] --> PENDING : create()

  PENDING --> CONFIRMED : validate()\n[overlap check pass, policy permit]
  PENDING --> CANCELLED : reject()\n[validation failed]

  CONFIRMED --> CANCELLED : cancel(reason)\n[requestor or manager]
  CONFIRMED --> EXPIRED : slaTimerFired()\n[checkout window closed]
  CONFIRMED --> CONVERTED : checkout()\n[allocation created]

  CANCELLED --> [*]
  EXPIRED --> [*]
  CONVERTED --> [*]
```

---

## 3. Allocation State Machine

```mermaid
stateDiagram-v2
  direction LR
  [*] --> ACTIVE : checkout()

  ACTIVE --> ACTIVE : transferCustody()\n[actor changes; state stays]
  ACTIVE --> RETURNING : initiateReturn()
  ACTIVE --> OVERDUE : overdueDetected()\n[due_at < now()]
  ACTIVE --> LOST : reportLoss()

  RETURNING --> RETURNED : confirmReturn(condition_grade)

  OVERDUE --> RETURNED : lateCheckin(condition_grade)\n[custodian returns after overdue]
  OVERDUE --> FORCED_RETURN : forceReturn(approver, reason)

  LOST --> [*]
  RETURNED --> [*]
  FORCED_RETURN --> [*]
```

---

## 4. Incident Case State Machine

```mermaid
stateDiagram-v2
  direction LR
  [*] --> OPEN : open()

  OPEN --> IN_REVIEW : assign(owner_id)\n[owner accepts case]
  OPEN --> CLOSED : autoResolve()\n[no action required]

  IN_REVIEW --> PENDING_SETTLEMENT : requiresSettlement()\n[damage or loss confirmed]
  IN_REVIEW --> RESOLVED : resolve(notes)\n[no financial action]

  PENDING_SETTLEMENT --> RESOLVED : settlementPosted()\n[ledger event confirmed]

  RESOLVED --> CLOSED : close()

  CLOSED --> [*]
```

---

## 5. Settlement Record State Machine

```mermaid
stateDiagram-v2
  direction LR
  [*] --> PENDING : calculate()

  PENDING --> APPROVED : approve(finance_actor)
  PENDING --> DISPUTED : dispute(notes)\n[custodian disputes charge]

  APPROVED --> POSTED : postToLedger()\n[outbox event delivered]

  DISPUTED --> APPROVED : resolveDispute()\n[dispute not upheld]
  DISPUTED --> VOIDED : voidCharge()\n[dispute upheld]

  POSTED --> [*]
  VOIDED --> [*]
```

---

## 6. Decommission Request State Machine

```mermaid
stateDiagram-v2
  direction LR
  [*] --> SUBMITTED : requestDecommission()

  SUBMITTED --> APPROVED : approve(approver_id)\n[authorized approver]
  SUBMITTED --> REJECTED : reject(reason)\n[authorized approver]

  APPROVED --> ARCHIVED : archiveComplete(manifest_id)

  REJECTED --> [*]
  ARCHIVED --> [*]
```

---

## State Transition Audit Requirements

Every state transition MUST write an `audit_event` record in the same database transaction with:
- `command` = name of the transition command
- `before_state` = JSON snapshot of entity before change
- `after_state` = JSON snapshot after change
- `actor_id` = identity of the user or system triggering the transition
- `correlation_id` = request correlation ID
- `hash` = SHA-256(`prev_hash || payload`) — forms a tamper-evident chain

---

## Cross-References

- Lifecycle orchestration (transition execution): [lifecycle-orchestration.md](./lifecycle-orchestration.md)
- Domain model (state enumerations): [../high-level-design/domain-model.md](../high-level-design/domain-model.md)
- Business rules (transition guards): [../analysis/business-rules.md](../analysis/business-rules.md)
