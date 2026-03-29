# Event Catalog

This catalog defines stable event contracts for **Backend as a Service Platform** to support event-driven integrations, auditability, and analytics across backend as a service workflows.

## Contract Conventions
- Event naming: `<domain>.<aggregate>.<action>.v1`.
- Required metadata: `event_id`, `occurred_at`, `correlation_id`, `producer`, `schema_version`, `tenant_context`.
- Delivery mode: at-least-once with mandatory consumer idempotency.
- Ordering guarantee: per aggregate key; no global ordering assumption.

## Domain Events
| Event Name | Payload Highlights | Typical Consumers |
|---|---|---|
| `domain.record.created.v1` | record_id, actor_id, initial_state, occurred_at | orchestration, analytics |
| `domain.record.state_changed.v1` | record_id, old_state, new_state, reason_code | notifications, reporting |
| `domain.record.validation_failed.v1` | record_id, violated_rules, correlation_id | operations, quality dashboards |
| `domain.record.override_applied.v1` | record_id, override_type, approver_id, expires_at | compliance, audit |
| `domain.record.closed.v1` | record_id, terminal_state, closed_at | billing/settlement, archives |

## Publish and Consumption Sequence
```mermaid
sequenceDiagram
    participant API as Command Service
    participant DB as Transaction Store
    participant Outbox as Outbox Relay
    participant Bus as Event Bus
    participant Consumer as Downstream Consumer
    API->>DB: Persist state change + outbox row
    Outbox->>DB: Poll committed rows
    Outbox->>Bus: Publish event
    Bus-->>Consumer: Deliver event
    Consumer->>Consumer: Idempotency check + process
    alt Consumer failure
        Consumer->>Bus: NACK
        Bus-->>Consumer: Retry then DLQ
    end
```

## Operational SLOs
- P95 commit-to-publish latency below 5 seconds for tier-1 events.
- DLQ triage acknowledgement within 15 minutes for production incidents.
- Schema changes remain backward compatible within the same major version.

## Contracted Event Semantics

### API contract events
| Event | Payload contract |
|---|---|
| `control.operation.started` | `operationId`, `operationType`, `tenantId`, `envId`, `requestedBy` |
| `control.operation.completed` | `operationId`, `state`, `durationMs`, `resultVersion` |
| `runtime.error.raised` | `error.code`, `error.category`, `retryable`, `correlationId` |

### Isolation events
- `security.isolation.violation.detected` (contains actor scope + denied scope).
- `security.secret.scope.denied` (environment mismatch metadata).

### Lifecycle and migration events
```mermaid
sequenceDiagram
participant CP as Control Plane
participant OP as Operation Tracker
participant AD as Adapter
CP->>OP: operation.started
CP->>AD: apply migration
AD-->>OP: migration.state.changed
AD-->>OP: migration.verified
OP-->>CP: operation.completed
```

### SLO mapping events
| Event | SLI contribution |
|---|---|
| `runtime.request.completed` | latency and success denominator/numerator |
| `realtime.delivery.completed` | dispatch latency |
| `functions.invoke.completed` | completion ratio + queue latency |
