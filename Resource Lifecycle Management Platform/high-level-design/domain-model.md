# Domain Model

The domain model defines the core aggregates, entities, value objects, and their relationships within the **Resource Lifecycle Management Platform**. All services are aligned to these bounded contexts.

---

## Bounded Contexts

| Bounded Context | Responsibility | Key Aggregates |
|---|---|---|
| **Resource Catalog** | Ownership of the resource record and its metadata | Resource, PolicyProfile |
| **Reservation** | Time-bound holds and priority management | Reservation |
| **Allocation & Custody** | Active possession tracking and condition management | Allocation, CustodyTransfer |
| **Incident & Settlement** | Exception case management and financial charges | IncidentCase, SettlementRecord |
| **Decommission & Archive** | Terminal lifecycle transitions and compliance archival | DecommissionRequest, ArchiveManifest |
| **Audit** | Immutable event ledger for all state changes | AuditEvent |

---

## Domain Class Diagram

```mermaid
classDiagram
  direction TB

  class Resource {
    +UUID resource_id
    +UUID tenant_id
    +ResourceCategory category
    +String asset_tag
    +String serial_number
    +String name
    +ConditionGrade condition_grade
    +UUID location_id
    +String cost_centre
    +Decimal acquisition_cost
    +UUID policy_profile_id
    +ResourceState state
    +DateTime created_at
    +DateTime updated_at
    +int version
    +provision() ResourceProvisioned
    +updateCondition(grade, notes) ConditionAssessed
    +decommission(request) DecommissionRequested
  }

  class PolicyProfile {
    +UUID policy_profile_id
    +String name
    +int max_duration_hours
    +int max_extensions
    +int extension_max_hours
    +int quota_per_requestor
    +int quota_per_tenant
    +String[] eligible_roles
    +JSON priority_rules
    +UUID deposit_rate_card_id
    +Boolean is_active
    +int version
    +evaluate(request) PolicyDecision
  }

  class Reservation {
    +UUID reservation_id
    +UUID resource_id
    +UUID requestor_id
    +UUID tenant_id
    +DateTime start_at
    +DateTime end_at
    +int priority
    +ReservationState state
    +String idempotency_key
    +DateTime sla_due_at
    +String cancellation_reason
    +confirm() ReservationCreated
    +cancel(reason) ReservationCancelled
    +expire() ReservationExpired
    +convertToAllocation() Allocation
  }

  class Allocation {
    +UUID allocation_id
    +UUID reservation_id
    +UUID resource_id
    +UUID custodian_id
    +UUID tenant_id
    +DateTime checkout_at
    +DateTime due_at
    +DateTime checkin_at
    +ConditionGrade checkout_condition
    +ConditionGrade checkin_condition
    +ConditionDelta condition_delta
    +AllocationState state
    +int extended_count
    +checkout(condition) AllocationCheckedOut
    +checkin(condition) AllocationCheckedIn
    +extend(newDueAt) AllocationExtended
    +markOverdue() AllocationOverdue
    +forceReturn(approver, reason) AllocationForcedReturn
  }

  class CustodyTransfer {
    +UUID transfer_id
    +UUID allocation_id
    +UUID from_actor
    +UUID to_actor
    +DateTime transferred_at
    +String reason
  }

  class IncidentCase {
    +UUID case_id
    +UUID resource_id
    +UUID allocation_id
    +CaseType case_type
    +Severity severity
    +CaseState state
    +UUID owner_id
    +DateTime sla_due_at
    +String description
    +String resolution_notes
    +DateTime resolved_at
    +open() IncidentOpened
    +resolve(notes) IncidentResolved
    +close() IncidentClosed
  }

  class SettlementRecord {
    +UUID settlement_id
    +UUID case_id
    +UUID allocation_id
    +ChargeType charge_type
    +Decimal amount
    +String currency
    +UUID rate_card_id
    +SettlementState state
    +UUID ledger_event_id
    +calculate() SettlementCalculated
    +post() SettlementPosted
    +dispute(notes) SettlementDisputed
    +void(reason) SettlementVoided
  }

  class DecommissionRequest {
    +UUID request_id
    +UUID resource_id
    +UUID requested_by
    +String reason
    +String disposal_method
    +Boolean requires_approval
    +UUID approved_by
    +DateTime approved_at
    +requestDecommission() DecommissionRequested
    +approve(approver) DecommissionApproved
    +reject(reason) DecommissionRejected
  }

  class AuditEvent {
    +UUID audit_id
    +UUID entity_id
    +String entity_type
    +String command
    +UUID actor_id
    +UUID correlation_id
    +String reason_code
    +JSON before_state
    +JSON after_state
    +DateTime timestamp
    +String hash
  }

  class Location {
    +UUID location_id
    +String name
    +String building
    +String floor
    +String zone
    +GeoCoordinate coordinates
  }

  %% Relationships
  Resource "1" --> "1" PolicyProfile : governed by
  Resource "1" --> "0..*" Reservation : reserved via
  Resource "1" --> "0..*" Allocation : allocated via
  Resource "1" --> "0..*" IncidentCase : involved in
  Resource "1" --> "0..*" DecommissionRequest : terminates via
  Resource "1" --> "1" Location : located at
  Reservation "1" --> "0..1" Allocation : converted into
  Allocation "1" --> "0..*" CustodyTransfer : has
  Allocation "1" --> "0..*" IncidentCase : triggers
  IncidentCase "1" --> "0..*" SettlementRecord : resolved by
  Resource "1" --> "0..*" AuditEvent : produces
  Reservation "1" --> "0..*" AuditEvent : produces
  Allocation "1" --> "0..*" AuditEvent : produces
```

---

## State Enumerations

### ResourceState

```
PENDING → AVAILABLE → RESERVED → ALLOCATED
       ↓                              ↓
   EXCEPTION              RETURNING → INSPECTION
                                     ↙        ↘
                              AVAILABLE    MAINTENANCE
                                                ↓
                                          DECOMMISSIONING
                                                ↓
                                         DECOMMISSIONED
```

| State | Description |
|---|---|
| `PENDING` | Record created; mandatory fields incomplete |
| `AVAILABLE` | Ready for reservation |
| `RESERVED` | Time-window hold confirmed |
| `ALLOCATED` | Active custody with a custodian |
| `RETURNING` | Checkout SLA timer fired; custodian initiated return |
| `INSPECTION` | Post-return condition assessment in progress |
| `MAINTENANCE` | Scheduled or corrective maintenance |
| `DECOMMISSIONING` | Terminal transition in progress; awaiting archive |
| `DECOMMISSIONED` | Terminal; archived; no further transitions |
| `EXCEPTION` | Manual hold; requires ops/compliance resolution |

### ReservationState

| State | Description |
|---|---|
| `PENDING` | Submitted; not yet processed |
| `CONFIRMED` | Active hold; checkout window open |
| `CANCELLED` | Cancelled by requestor or system |
| `EXPIRED` | Checkout window closed without checkout |
| `CONVERTED` | Converted to an active Allocation |

### AllocationState

| State | Description |
|---|---|
| `ACTIVE` | Resource in custody; within due date |
| `OVERDUE` | Due date passed; escalation ladder active |
| `RETURNED` | Resource checked in; condition recorded |
| `FORCED_RETURN` | Ops initiated forced return |
| `LOST` | Custodian reported resource as lost |

---

## Domain Events Summary

| Aggregate | Events Emitted |
|---|---|
| Resource | `provisioned`, `catalog_updated`, `condition_assessed`, `decommission_requested`, `decommissioned`, `archived` |
| Reservation | `created`, `cancelled`, `expired`, `conflict_detected`, `priority_displaced` |
| Allocation | `checked_out`, `checked_in`, `extended`, `overdue`, `forced_return`, `custody_transferred`, `loss_reported` |
| IncidentCase | `opened`, `updated`, `resolved` |
| SettlementRecord | `calculated`, `posted`, `disputed`, `voided` |
| DecommissionRequest | `requested`, `approved`, `rejected` |

---

## Cross-References

- Data dictionary (attribute constraints): [../analysis/data-dictionary.md](../analysis/data-dictionary.md)
- State machine diagrams: [../detailed-design/state-machine-diagrams.md](../detailed-design/state-machine-diagrams.md)
- ERD (database schema): [../detailed-design/erd-database-schema.md](../detailed-design/erd-database-schema.md)
- Class diagrams (implementation detail): [../detailed-design/class-diagrams.md](../detailed-design/class-diagrams.md)
