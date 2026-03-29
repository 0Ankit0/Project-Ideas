# Event Catalog

This catalog defines stable event contracts for **Healthcare Appointment System** to support event-driven integrations, auditability, and analytics across healthcare appointment workflows.

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

## Operational Policy Addendum

### Scheduling Conflict Policies
- Double-booking is prohibited per provider, location, and time-slot; writes enforce an optimistic concurrency check on slot version plus an idempotency key.
- When two booking requests race for the same slot, the first committed request wins and all later requests receive `SLOT_ALREADY_BOOKED` with alternative slot suggestions.
- Provider calendar changes (leave, overrun, emergency block) trigger an automatic revalidation pass that marks impacted bookings as `REBOOK_REQUIRED` and starts remediation workflows.
- Escalation SLA: unresolved conflicts older than 15 minutes are routed to operations for manual intervention and patient outreach.

### Patient/Provider Workflow States
- Patient appointment lifecycle: `DRAFT -> PENDING_CONFIRMATION -> CONFIRMED -> CHECKED_IN -> IN_CONSULTATION -> COMPLETED` with terminal branches `CANCELLED`, `NO_SHOW`, and `EXPIRED`.
- Provider schedule lifecycle: `AVAILABLE -> RESERVED -> LOCKED_FOR_VISIT -> RELEASED`; exceptional states include `BLOCKED` (planned) and `SUSPENDED` (incident/compliance).
- State transitions are event-driven and auditable; every transition records actor, timestamp, source channel, and reason code.
- Invalid transitions are rejected with deterministic error codes and do not mutate downstream billing or notification state.

### Notification Guarantees
- Notification channels include in-app, email, and SMS (when consented); delivery policy is at-least-once with idempotent message keys to prevent duplicate side effects.
- Critical events (`CONFIRMED`, `RESCHEDULED`, `CANCELLED`, `REBOOK_REQUIRED`) are retried with exponential backoff for up to 24 hours.
- If all automated retries fail, a fallback task is created for support-assisted outreach and the record is flagged `NOTIFICATION_ATTENTION_REQUIRED`.
- Template rendering and localization are versioned so users receive content consistent with the transaction version that triggered the event.

### Privacy Requirements
- All PHI/PII is encrypted in transit (TLS 1.2+) and at rest (AES-256 or cloud-provider equivalent managed keys).
- Access control follows least privilege with RBAC/ABAC, MFA for privileged roles, and full audit logging for create/read/update/export actions on medical or billing data.
- Data minimization applies to notifications and analytics exports; only required fields are shared and retention follows policy/legal hold requirements.
- Integrations must use signed requests, scoped credentials, and periodic key rotation; sandbox/test data must be de-identified.

### Downtime Fallback Procedures
- During partial outages, the system enters degraded mode: read-only schedule views remain available while new bookings are queued for deferred processing.
- Clinics maintain a printable/offline daily roster and manual check-in sheet; staff can continue visits using downtime SOPs and reconcile once service is restored.
- Recovery requires replaying queued commands/events in order, conflict revalidation, and sending reconciliation notices for any changed appointments.
- Incident closure criteria include successful backlog drain, data consistency checks, and post-incident communication to affected patients/providers.

