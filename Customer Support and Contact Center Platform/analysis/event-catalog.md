# Event Catalog

This catalog defines stable event contracts for **Customer Support and Contact Center Platform** to support event-driven integrations, auditability, and analytics across customer support and contact center workflows.

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

## Event Catalog Deep Narrative

```mermaid
sequenceDiagram
    participant Ch as Channel Connector
    participant In as Ingestion Bus
    participant Rt as Routing Engine
    participant Sl as SLA Service
    participant Au as Audit Stream
    Ch->>In: message.received
    In->>Rt: interaction.normalized
    Rt->>Sl: queue.entered
    Sl-->>Rt: sla.checkpoint.created
    Rt->>Au: assignment.decided
    Rt->>Au: escalation.triggered (optional)
```

- Required high-value events: `queue.entered`, `assignment.accepted`, `customer.waiting`, `sla.warning`, `sla.breached`, `escalation.acknowledged`, `case.closed`.
- Every event includes `tenant_id`, `conversation_id`, `event_time`, and idempotency key.
- For omnichannel reliability, producers must retry with the same idempotency key and consumers must remain replay-safe.
- Incident handling depends on catalog completeness: missing `sla.breached` events are Sev2 telemetry defects.
