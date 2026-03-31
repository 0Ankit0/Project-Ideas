# Class Diagrams

Detailed class diagrams for the **Resource Lifecycle Management Platform** implementation layers: domain model, application services, and infrastructure adapters.

---

## 1. Core Domain Classes

```mermaid
classDiagram
  direction TB

  class Resource {
    -UUID resourceId
    -UUID tenantId
    -ResourceCategory category
    -String assetTag
    -String serialNumber
    -String name
    -ConditionGrade conditionGrade
    -UUID locationId
    -String costCentre
    -Money acquisitionCost
    -UUID policyProfileId
    -ResourceState state
    -int version
    +provision(template) ResourceProvisioned
    +updateCondition(grade, notes) ConditionAssessed
    +transitionTo(newState, command, actor) AuditEvent
    +decommission(request) DecommissionRequested
    -guardTransition(from, to, command) void
  }

  class Reservation {
    -UUID reservationId
    -UUID resourceId
    -UUID requestorId
    -UUID tenantId
    -DateTimeWindow window
    -int priority
    -ReservationState state
    -String idempotencyKey
    -Instant slaDueAt
    +confirm() ReservationCreated
    +cancel(reason) ReservationCancelled
    +expire() ReservationExpired
    +convertToAllocation(custodian, condition) Allocation
    -guardNoOverlap(existingReservations) void
  }

  class Allocation {
    -UUID allocationId
    -UUID reservationId
    -UUID resourceId
    -UUID custodianId
    -Instant checkoutAt
    -Instant dueAt
    -ConditionGrade checkoutCondition
    -ConditionGrade checkinCondition
    -ConditionDelta conditionDelta
    -AllocationState state
    -int extendedCount
    +checkout(condition) AllocationCheckedOut
    +checkin(condition) AllocationCheckedIn
    +extend(newDueAt, policy) AllocationExtended
    +markOverdue() AllocationOverdue
    +transferCustody(toActor) CustodyTransferred
    +forceReturn(approver, reason) ForcedReturn
    -computeConditionDelta() ConditionDelta
  }

  class PolicyProfile {
    -UUID policyProfileId
    -int maxDurationHours
    -int maxExtensions
    -int quotaPerRequestor
    -int quotaPerTenant
    -List~String~ eligibleRoles
    -PolicyPriorityRules priorityRules
    -UUID depositRateCardId
    +evaluate(request, quota) PolicyDecision
    +isEligible(requestorRole) Boolean
    +maxAllowedDueAt(checkoutAt) Instant
  }

  class IncidentCase {
    -UUID caseId
    -UUID resourceId
    -UUID allocationId
    -CaseType caseType
    -Severity severity
    -CaseState state
    -UUID ownerId
    -Instant slaDueAt
    +open() IncidentOpened
    +assign(ownerId) IncidentUpdated
    +resolve(notes) IncidentResolved
    +requiresSettlement() Boolean
  }

  class SettlementRecord {
    -UUID settlementId
    -UUID caseId
    -UUID allocationId
    -ChargeType chargeType
    -Money amount
    -UUID rateCardId
    -SettlementState state
    -UUID ledgerEventId
    +calculate(delta, rateCard) SettlementCalculated
    +approve(actor) SettlementApproved
    +post(ledgerEventId) SettlementPosted
    +dispute(notes) SettlementDisputed
    +void(reason) SettlementVoided
  }

  class AuditEvent {
    -UUID auditId
    -UUID entityId
    -String entityType
    -String command
    -UUID actorId
    -UUID correlationId
    -String reasonCode
    -JsonNode beforeState
    -JsonNode afterState
    -Instant timestamp
    -String hash
    +computeHash(previousHash, payload) String
  }

  Resource "1" --> "1" PolicyProfile : governed by
  Resource "1" --> "0..*" Reservation : reserved via
  Resource "1" --> "0..*" Allocation : allocated via
  Resource "1" --> "0..*" IncidentCase : involved in
  Reservation "1" --> "0..1" Allocation : converts to
  Allocation "1" --> "0..*" IncidentCase : triggers
  IncidentCase "1" --> "0..*" SettlementRecord : settled by
```

---

## 2. Application Service Layer

```mermaid
classDiagram
  direction LR

  class ProvisioningService {
    -ResourceRepository resourceRepo
    -PolicyProfileRepository policyRepo
    -PolicyEngine policyEngine
    -OutboxPublisher outbox
    +provision(cmd ProvisionCommand) Resource
    +bulkProvision(cmd BulkProvisionCommand) List~Resource~
    -validateTemplate(templateId) ResourceTemplate
  }

  class AllocationService {
    -ReservationRepository reservationRepo
    -ResourceRepository resourceRepo
    -PolicyEngine policyEngine
    -LockManager lockManager
    -OutboxPublisher outbox
    -IdempotencyStore idempotency
    +createReservation(cmd CreateReservationCommand) Reservation
    +cancelReservation(cmd CancelReservationCommand) Reservation
    +expireReservation(reservationId) Reservation
  }

  class CustodyService {
    -AllocationRepository allocationRepo
    -ResourceRepository resourceRepo
    -IncidentService incidentSvc
    -OutboxPublisher outbox
    +checkout(cmd CheckoutCommand) Allocation
    +checkin(cmd CheckinCommand) Allocation
    +transferCustody(cmd TransferCommand) CustodyTransfer
    +forceReturn(cmd ForceReturnCommand) Allocation
    -openIncidentIfRequired(allocation) Optional~IncidentCase~
  }

  class OverdueDetectorService {
    -AllocationRepository allocationRepo
    -EscalationEngine escalationEngine
    -OutboxPublisher outbox
    +detectAndMark() OverdueReport
    +processEscalationStep(allocationId, step) void
  }

  class IncidentService {
    -IncidentRepository incidentRepo
    -SettlementService settlementSvc
    -OutboxPublisher outbox
    +openCase(cmd OpenIncidentCommand) IncidentCase
    +resolveCase(cmd ResolveIncidentCommand) IncidentCase
    +assignOwner(caseId, ownerId) IncidentCase
  }

  class SettlementService {
    -SettlementRepository settlementRepo
    -RateCardEngine rateCardEngine
    -OutboxPublisher outbox
    +calculate(caseId) SettlementRecord
    +approve(settlementId, actor) SettlementRecord
    +dispute(settlementId, notes) SettlementRecord
    +void(settlementId, reason) SettlementRecord
  }

  class DecommissionOrchestrator {
    -ResourceRepository resourceRepo
    -ApprovalService approvalSvc
    -ArchiveJob archiveJob
    -OutboxPublisher outbox
    +requestDecommission(cmd) DecommissionRequest
    +processApproval(requestId, approver) DecommissionRequest
    -checkPreconditions(resourceId) PreconditionResult
  }

  class PolicyEngine {
    -OpaClient opaClient
    -Cache policyCache
    +evaluate(request PolicyRequest) PolicyDecision
    +evaluateQuota(tenantId, requestorId, resourceId) QuotaDecision
  }

  ProvisioningService --> PolicyEngine
  AllocationService --> PolicyEngine
  AllocationService --> CustodyService
  CustodyService --> IncidentService
  IncidentService --> SettlementService
  OverdueDetectorService --> AllocationService
```

---

## 3. Infrastructure Layer

```mermaid
classDiagram
  direction LR

  class ResourceRepository {
    <<interface>>
    +findById(id) Optional~Resource~
    +findByAssetTag(tenantId, tag) Optional~Resource~
    +save(resource) Resource
    +findAvailableInWindow(window) List~Resource~
  }

  class PostgresResourceRepository {
    -DataSource ds
    +findById(id) Optional~Resource~
    +save(resource) Resource
  }

  class OutboxPublisher {
    <<interface>>
    +publish(event DomainEvent, tx Transaction) void
  }

  class PostgresOutboxPublisher {
    -DataSource ds
    +publish(event, tx) void
  }

  class OutboxRelayJob {
    -DataSource ds
    -EventBusProducer producer
    -ScheduledExecutorService scheduler
    +relay() void
    +markDelivered(outboxId) void
    +moveToDLQ(outboxId, reason) void
  }

  class PolicyCache {
    -RedisClient redis
    -OpaClient opaClient
    -Duration ttl
    +get(cacheKey) Optional~PolicyDecision~
    +put(cacheKey, decision) void
    +invalidate(policyProfileId) void
  }

  class IdempotencyStore {
    -RedisClient redis
    -Duration ttl
    +getIfPresent(key) Optional~ApiResponse~
    +put(key, response) void
  }

  PostgresResourceRepository ..|> ResourceRepository
  PostgresOutboxPublisher ..|> OutboxPublisher
  OutboxRelayJob --> PostgresOutboxPublisher
```

---

## Cross-References

- Domain model (aggregate overview): [../high-level-design/domain-model.md](../high-level-design/domain-model.md)
- ERD (persistence layer): [erd-database-schema.md](./erd-database-schema.md)
- Component diagrams (deployment view): [component-diagrams.md](./component-diagrams.md)
