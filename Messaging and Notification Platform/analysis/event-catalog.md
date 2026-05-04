# Event Catalog

This catalog defines production event contracts for the **Messaging and Notification Platform**. It covers events produced during message ingestion, dispatch, delivery feedback, and compliance lifecycle.

## Traceability
- Requirements baseline: [`../requirements/requirements.md`](../requirements/requirements.md)
- Data semantics: [`./data-dictionary.md`](./data-dictionary.md)
- Business policy: [`./business-rules.md`](./business-rules.md)
- Detailed orchestration: [`../detailed-design/delivery-orchestration-and-template-system.md`](../detailed-design/delivery-orchestration-and-template-system.md)

## Contract Conventions
- Event name format: `<domain>.<aggregate>.<action>.v1`.
- Mandatory headers: `event_id`, `event_time`, `correlation_id`, `causation_id`, `tenant_id`, `schema_version`.
- Delivery semantics: at-least-once; all consumers must implement idempotency using `event_id`.
- Ordering guarantee: ordered per partition key (`tenant_id:recipient_id:channel`).
- Breaking change policy: major version bump with old topic maintained during migration window.
- Payload policy: business identifiers are immutable, PII is minimized or tokenized, and provider payload excerpts are stored only where operationally necessary.

## Domain Events

| Event | Producer | Partition Key | Key Payload Fields | Trigger | Consumers |
|---|---|---|---|---|---|
| `message.accepted.v1` | ingestion-service | `tenant_id:recipient_id:channel` | `message_id`, `idempotency_key`, `channel`, `priority` | Request validated and queued | Orchestrator, Analytics |
| `message.scheduled.v1` | scheduler-service | `tenant_id:message_id` | `message_id`, `scheduled_for`, `priority`, `window_policy` | Deferred message becomes eligible later | Orchestrator, Analytics |
| `message.dispatch_started.v1` | orchestration-service | `tenant_id:message_id` | `message_id`, `attempt_id`, `provider_route_id`, `attempt_no` | Provider handoff begins | Status API, Audit |
| `message.delivered.v1` | provider-adapter | `tenant_id:message_id` | `message_id`, `provider_message_id`, `delivered_at` | Provider delivery confirmed | Status tracker, Analytics, Audit |
| `message.failed.v1` | provider-adapter | `tenant_id:message_id` | `message_id`, `error_class`, `provider_code`, `attempt_no` | Non-retryable provider failure | DLQ handler, Alerting, Audit |
| `message.retry_scheduled.v1` | orchestration-service | `tenant_id:message_id` | `message_id`, `attempt_id`, `retry_at`, `retry_reason` | Retryable failure classified | Retry scheduler, Audit |
| `message.expired.v1` | orchestrator | `tenant_id:message_id` | `message_id`, `channel`, `queued_at`, `expired_at` | TTL exceeded before dispatch | DLQ handler, Analytics |
| `message.cancelled.v1` | orchestration-service | `tenant_id:message_id` | `message_id`, `cancel_reason`, `cancelled_by`, `cancelled_at` | Operator or system cancels message | Status API, Audit |
| `recipient.suppressed.v1` | compliance-service | `tenant_id:recipient_id` | `recipient_id`, `channel`, `reason`, `suppressed_at` | Opt-out or policy suppression | Preference sync, Audit |
| `consent.revoked.v1` | preference-service | `tenant_id:recipient_id` | `recipient_id`, `channel`, `revoked_at`, `version` | Recipient opts out | Consent cache, In-flight cancel, Audit |
| `provider.circuit.opened.v1` | provider-monitor | `channel:provider_id` | `provider_id`, `channel`, `error_rate`, `opened_at` | Circuit breaker trips | Failover router, Alerting |
| `provider.route.recovered.v1` | provider-monitor | `channel:provider_id` | `provider_id`, `channel`, `recovered_at`, `probe_score` | Provider exits half-open and is healthy again | Routing engine, Alerting |
| `dlq.message.received.v1` | dlq-processor | `tenant_id:message_id` | `message_id`, `error_class`, `attempt_count`, `last_error` | Message sent to DLQ | Alerting, Operator console |
| `template.published.v1` | template-service | `tenant_id:template_id` | `template_id`, `version`, `approved_by`, `published_at` | Template approved and published | Render cache, Audit |
| `template.render_failed.v1` | renderer-service | `tenant_id:template_id` | `template_version_id`, `message_id`, `validation_errors` | Rendering fails due to bad variables or template defect | DLQ handler, Template owners |
| `audit.export.completed.v1` | audit-service | `tenant_id:export_id` | `export_id`, `scope`, `requested_by`, `completed_at` | Compliance export finished | Admin UI, Audit workflows |

## Publish and Consumption Sequence

```mermaid
sequenceDiagram
    participant Caller
    participant Ingestion
    participant Outbox as DB + Outbox
    participant Relay
    participant Bus as Event Bus
    participant Orchestrator

    Caller->>Ingestion: POST /messages
    Ingestion->>Outbox: persist message + outbox row
    Ingestion-->>Caller: 202 Accepted (message_id)
    Relay->>Outbox: poll committed rows
    Relay->>Bus: publish message.accepted.v1
    Bus-->>Orchestrator: deliver event
    Orchestrator->>Orchestrator: check consent + suppression + schedule window
    Orchestrator->>Bus: publish message.dispatch_started.v1
    alt provider accepts and confirms
        Bus-->>Orchestrator: message.delivered.v1
    else provider returns retryable error
        Bus-->>Orchestrator: message.failed.v1
        Orchestrator->>Bus: publish message.retry_scheduled.v1
    else provider returns terminal error
        Bus-->>Orchestrator: message.failed.v1
        Orchestrator->>Bus: publish dlq.message.received.v1
    end
```

## Retention and Replay Policy

- Event topics retain high-volume dispatch events for at least 7 days in the hot bus and 30 days in archive storage.
- Compliance and template-governance events are mirrored to immutable audit storage for 7 years where required.
- Replay tooling supports scoped replay by tenant, event type, time range, and partition key.
- Replays must preserve original `event_id` in the payload metadata while emitting a new replay execution record for observability.

## Operational SLOs
- P95 message.accepted to message.delivered latency: <= 5 seconds for P0 transactional messages.
- P95 message.accepted to message.delivered latency: <= 30 seconds for P1 operational messages.
- DLQ alert acknowledgement within 10 minutes for tenant-impacting failures.
- Consent revocation must propagate to all dispatch workers within 60 seconds P95.
- Monthly schema compatibility review with all registered consumers.
- Provider circuit-breaker state changes must trigger PagerDuty alert within 30 seconds.
- Event publication lag from committed outbox row to bus publish: <= 2 seconds P95.
