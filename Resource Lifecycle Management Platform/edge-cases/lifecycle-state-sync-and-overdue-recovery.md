# Lifecycle State Sync and Overdue Recovery

Edge cases related to resource state drift, overdue detection failures, and escalation ladder gaps in the **Resource Lifecycle Management Platform**.

---

## EC-LSS-01: Overdue Detector Job Fails to Run

**Description**: The overdue detector cron job crashes or is not scheduled (e.g., leader election failure in Kubernetes), leaving overdue allocations undetected.

| Aspect | Detail |
|---|---|
| **Trigger** | Overdue Detector pod crashes; no new overdue events published for > 10 min |
| **Detection** | `rlmp_overdue_detector_last_run` metric drops below threshold; alert fires after 10 min gap |
| **Containment** | No new escalations are triggered; existing OVERDUE allocations remain in their last escalation step |
| **Recovery** | Kubernetes restarts the pod (crashloop); leader election reassigns to healthy pod within 60 s; on recovery, job runs a full scan and catches up; missed escalation steps are sent |
| **Evidence** | Pod restart events in K8s; gap in overdue metric timeline; `rlmp.allocation.overdue` events resume after recovery |
| **Owner** | SRE |
| **SLA** | Auto-recovery within 2 min (K8s restart policy); manual escalation if > 10 min |
| **Prevention** | Readiness probe fails if job has not run within 10 min; PodDisruptionBudget ensures at least 0 replicas are not simultaneously disrupted during rolling updates |

---

## EC-LSS-02: Resource State Drift (DB State vs Event Store)

**Description**: A resource is in `ALLOCATED` state in the operational database, but no active allocation record exists (e.g., allocation was deleted by a bug or direct DB mutation).

| Aspect | Detail |
|---|---|
| **Trigger** | Reconciliation job detects: `resources.state = ALLOCATED` but no matching `allocation.state = ACTIVE` for this `resource_id` |
| **Detection** | Daily reconciliation job compares resource state with allocation state; publishes `rlmp.reconciliation.state_mismatch` event |
| **Containment** | Resource is quarantined to `EXCEPTION` state; no new reservations or allocations allowed; ops dashboard flags it |
| **Recovery** | SRE and Resource Manager investigate: (a) if allocation was incorrectly deleted, restore from backup and replay events; (b) if allocation genuinely completed, manually transition resource to `Inspection` → `Available` with a correction audit entry |
| **Evidence** | Reconciliation report with `resource_id`, `expected_state`, `actual_state`; audit trail gap or direct-DB-mutation evidence |
| **Owner** | SRE + Platform Engineering |
| **SLA** | Detection: daily; containment: < 1 h after detection; resolution: < 4 h |

---

## EC-LSS-03: Escalation Timer Drift (Step Skipped)

**Description**: An escalation step (e.g., step 2 T+4h warning) is skipped because the Escalation Engine was down when the timer should have fired.

| Aspect | Detail |
|---|---|
| **Trigger** | Escalation Engine pod restarts; the in-flight timer for step 2 is not persisted to DB; timer fires after restart on a different pod |
| **Detection** | Allocation still in step 1 escalation after T+4h; `rlmp.escalation.warned` event not published within expected window |
| **Containment** | Escalation Engine uses a persisted timer store (e.g., Redis Sorted Set or DB table) so timers survive pod restarts |
| **Recovery** | On pod restart, Escalation Engine reads the timer store and re-queues overdue timers; missed steps are sent with a delay note |
| **Evidence** | Timer store shows last-executed step and timestamp; gap in escalation events in SIEM |
| **Owner** | Platform Engineering |
| **SLA** | Timer recovery within 60 s of pod restart |
| **Prevention** | Timer state MUST be persisted to DB or Redis, not held in-process memory |

---

## EC-LSS-04: Allocation Left in RETURNING State

**Description**: Custodian initiated return (`RETURNING` state) but the final `confirmReturn` command (scan at desk) was never submitted. Resource is indefinitely in `RETURNING` state.

| Aspect | Detail |
|---|---|
| **Trigger** | `allocation.state = RETURNING` for > 30 min without a `checkin` event |
| **Detection** | Reconciliation job detects long-running `RETURNING` state; alert to Resource Manager |
| **Containment** | No automatic state change; resource is blocked for new reservations while in `RETURNING` |
| **Recovery** | Resource Manager contacts Custodian to complete return scan; if no response within 2 h, Manager initiates a forced return which transitions resource to `INSPECTION` |
| **Evidence** | Allocation audit trail shows `return_initiated` event but no `checked_in` event; timestamp gap |
| **Owner** | Resource Manager |
| **SLA** | Alert within 30 min; resolved within 2 h |

---

## EC-LSS-05: Maintenance Window Overlaps Active Allocation

**Description**: Resource Manager schedules a maintenance window while the resource is currently allocated to a custodian.

| Aspect | Detail |
|---|---|
| **Trigger** | `POST /resources/{id}/maintenance` submitted when `resource.state = ALLOCATED` |
| **Detection** | Provisioning Service checks current state before creating maintenance window |
| **Containment** | Two options: (a) reject maintenance window with `409 RESOURCE_CURRENTLY_ALLOCATED`; (b) schedule maintenance for after the current `allocation.due_at` with a warning to the manager |
| **Recovery** | Manager receives error and schedules maintenance for a future window after current allocation ends; or triggers early forced return if maintenance is urgent |
| **Evidence** | Audit log records attempted maintenance scheduling and the blocking allocation_id |
| **Owner** | Resource Manager |
| **SLA** | Automated error response; manager resolution within business hours |

---

## State Sync Reconciliation Flow

```mermaid
flowchart TD
  Start([Daily Reconciliation Job - 02:00 UTC]) --> QueryResources[SELECT all resources WHERE state != DECOMMISSIONED]
  QueryResources --> CheckAllocations[For each ALLOCATED resource:\nSELECT allocation WHERE resource_id=? AND state=ACTIVE]
  CheckAllocations --> Mismatch{Mismatch found?\nstate=ALLOCATED but no ACTIVE allocation}
  Mismatch -->|No| CheckOverdue[Check OVERDUE: allocation.due_at < NOW() but state=ACTIVE]
  Mismatch -->|Yes| QuarantineResource[Transition resource to EXCEPTION state\nWrite correction audit entry]
  QuarantineResource --> PublishMismatch[Publish rlmp.reconciliation.state_mismatch]
  PublishMismatch --> AlertOps[Alert SRE + Resource Manager]
  CheckOverdue --> OverdueFound{ACTIVE allocation past due_at?}
  OverdueFound -->|Yes| EmitOverdue[Publish rlmp.allocation.overdue\n(catchup event)]
  OverdueFound -->|No| CheckSettlement[Check settlement discrepancies]
  CheckSettlement --> FinanceReport[Publish rlmp.reconciliation.completed\n{discrepancy_count}]
  FinanceReport --> End([End])
```
