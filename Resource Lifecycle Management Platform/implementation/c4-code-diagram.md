# C4 Code Diagram

Code-level (C4 Level 4) organization for the **Resource Lifecycle Management Platform**. Shows the internal module structure within the Core API service.

---

## Module Dependency Graph

```mermaid
flowchart LR
  subgraph api["api/ (HTTP Layer)"]
    handlers["handlers/\n• provisioning_handler.go\n• allocation_handler.go\n• custody_handler.go\n• incident_handler.go\n• settlement_handler.go\n• decommission_handler.go\n• audit_handler.go\n• search_handler.go"]
    middleware["middleware/\n• auth.go (JWT)\n• rate_limit.go\n• correlation.go\n• logging.go"]
    dto["dto/\n• resource_dto.go\n• reservation_dto.go\n• allocation_dto.go\n• error_response.go"]
  end

  subgraph application["application/ (Use Cases)"]
    prov["provisioning/\n• provision_command.go\n• bulk_provision_command.go\n• provisioning_service.go"]
    alloc["allocation/\n• create_reservation_command.go\n• cancel_reservation_command.go\n• allocation_service.go"]
    custody["custody/\n• checkout_command.go\n• checkin_command.go\n• force_return_command.go\n• transfer_command.go\n• custody_service.go"]
    incident["incident/\n• open_incident_command.go\n• resolve_incident_command.go\n• incident_service.go"]
    settlement["settlement/\n• calculate_settlement.go\n• approve_settlement.go\n• settlement_service.go"]
    decomm["decommission/\n• request_decommission.go\n• decommission_orchestrator.go"]
  end

  subgraph domain["domain/ (Pure Business Logic)"]
    res["resource/\n• resource.go (aggregate)\n• state_machine.go\n• resource_events.go\n• policy_profile.go"]
    reservation["reservation/\n• reservation.go\n• window.go\n• reservation_events.go"]
    allocation_d["allocation/\n• allocation.go\n• condition_delta.go\n• allocation_events.go"]
    incident_d["incident/\n• incident_case.go\n• severity.go\n• incident_events.go"]
    settlement_d["settlement/\n• settlement_record.go\n• rate_card.go\n• settlement_events.go"]
    shared["shared/\n• money.go\n• audit_event.go\n• domain_error.go\n• idempotency_key.go"]
  end

  subgraph infra["infrastructure/ (Adapters)"]
    pg["postgres/\n• resource_repo.go\n• reservation_repo.go\n• allocation_repo.go\n• outbox_publisher.go\n• audit_writer.go\n• migrations/"]
    redis_infra["redis/\n• policy_cache.go\n• idempotency_store.go"]
    kafka_infra["kafka/\n• producer.go\n• consumer_group.go\n• outbox_relay.go"]
    opa_infra["opa/\n• opa_client.go\n• policy_adapter.go"]
    es_infra["elasticsearch/\n• search_client.go\n• index_worker.go"]
    coldstore["coldstore/\n• s3_archive_client.go\n• archive_job.go"]
  end

  api --> application
  application --> domain
  application --> infra
  domain --> shared
```

---

## Key Module Contracts

### domain/resource/state_machine.go

```go
type TransitionCommand struct {
    EntityID      uuid.UUID
    Command       string
    Payload       json.RawMessage
    ActorContext  ActorContext
}

type TransitionResult struct {
    NewState    ResourceState
    Version     int
    EmittedEvents []DomainEvent
}

type StateMachineEngine interface {
    Transition(entity *Resource, cmd TransitionCommand) (TransitionResult, error)
}
```

### application/custody/custody_service.go

```go
type CheckoutCommand struct {
    ReservationID   uuid.UUID
    CustodianID     uuid.UUID
    ConditionGrade  ConditionGrade
    ConditionNotes  string
    IdempotencyKey  string
    CorrelationID   uuid.UUID
}

type CustodyService interface {
    Checkout(ctx context.Context, cmd CheckoutCommand) (*Allocation, error)
    Checkin(ctx context.Context, cmd CheckinCommand) (*Allocation, error)
    ForceReturn(ctx context.Context, cmd ForceReturnCommand) (*Allocation, error)
    TransferCustody(ctx context.Context, cmd TransferCommand) (*CustodyTransfer, error)
}
```

### infrastructure/postgres/outbox_publisher.go

```go
// Must be called within an existing transaction
type OutboxPublisher interface {
    Publish(ctx context.Context, tx *sql.Tx, event DomainEvent) error
}

// Implementation writes to outbox table, NEVER to Kafka directly
type PostgresOutboxPublisher struct {
    // uses the caller's tx — no new transaction opened
}
```

---

## Dependency Inversion Rules

- `domain/` has **zero** external dependencies. It MUST NOT import `infrastructure/` or `application/`.
- `application/` depends on `domain/` and declares **interfaces** for repositories and external services.
- `infrastructure/` **implements** those interfaces; no other layer imports `infrastructure/` directly.
- `api/` depends on `application/` only, never on `domain/` or `infrastructure/` directly.

---

## Cross-References

- Component diagram (runtime view): [../detailed-design/c4-component-diagram.md](../detailed-design/c4-component-diagram.md)
- Class diagrams (type signatures): [../detailed-design/class-diagrams.md](../detailed-design/class-diagrams.md)
- Implementation guidelines (conventions): [implementation-guidelines.md](./implementation-guidelines.md)
