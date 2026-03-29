# Code Guidelines

## Architecture and Layering
- Adopt clean architecture boundaries: transport -> application -> domain -> infrastructure.
- Domain objects are persistence-agnostic and must not depend on framework primitives.
- Keep side effects at the edges (adapters, gateways, worker handlers).

## Implementation Standards
- Strong typing for IDs (`AppointmentId`, `ProviderId`) to avoid mix-ups.
- Immutable domain events; schema version required.
- Explicit transaction boundaries around slot reservation and appointment creation.
- Command handlers must be idempotent.

## Testing Standards
- Unit tests for state transition guards and policy engines.
- Contract tests for API and event schemas.
- Concurrency tests for slot conflict protection.
- Integration tests for outbox/event delivery pipeline.

## Observability and Operations
- Log format: structured JSON with `trace_id`, `correlation_id`, `tenant_id`.
- Metrics: booking latency, conflict rate, retry counts, dead-letter depth.
- Tracing: propagate context across synchronous and async hops.

## Secure Coding Requirements
- Never log PHI/PII payload content; log references and hashed identifiers only.
- Validate and sanitize all external input.
- Rotate secrets automatically and avoid long-lived static credentials.

## Operational Policy Addendum

### Scheduling Conflict Policies
- Double-booking is prevented through atomic slot reservation (`provider_id + location_id + slot_start`) with optimistic locking (`slot_version`) and idempotency keys per booking command.
- If concurrent requests target one slot, the first committed reservation succeeds; later requests return `409 SLOT_ALREADY_BOOKED` and include the top three alternatives.
- Provider calendar updates (leave, clinic closure, emergency blocks) trigger revalidation and move impacted appointments to `REBOOK_REQUIRED`.
- Any unresolved conflict older than 15 minutes creates an operations incident and outreach task.

### Patient/Provider Workflow States
- Patient lifecycle: `DRAFT -> PENDING_CONFIRMATION -> CONFIRMED -> CHECKED_IN -> IN_CONSULTATION -> COMPLETED` with terminal states `CANCELLED`, `NO_SHOW`, `EXPIRED`.
- Provider slot lifecycle: `AVAILABLE -> RESERVED -> LOCKED_FOR_VISIT -> RELEASED`; exceptional states are `BLOCKED` and `SUSPENDED`.
- Every state transition records actor, timestamp, reason code, and correlation id in immutable audit logs.
- Invalid transitions are rejected and never mutate billing, notification, or reporting projections.

### Notification Guarantees
- Channel order is configurable (in-app, email, SMS if consented). Delivery is at-least-once; consumers enforce idempotency using message keys.
- Critical events (`CONFIRMED`, `RESCHEDULED`, `CANCELLED`, `REBOOK_REQUIRED`) retry with exponential backoff for 24 hours.
- Failed deliveries create `NOTIFICATION_ATTENTION_REQUIRED` tasks for manual outreach.
- Template versions are pinned to event schema versions for deterministic rendering and compliance review.

### Privacy Requirements
- PHI/PII encryption: TLS 1.2+ in transit, AES-256 at rest, and customer-managed key support for regulated tenants.
- Access control: least privilege RBAC/ABAC, MFA for privileged roles, and just-in-time elevation for production support.
- Auditability: all create/read/update/export actions on clinical or billing data are logged with actor, purpose, and source IP.
- Data minimization is mandatory for analytics exports, notifications, and non-production datasets.

### Downtime Fallback Procedures
- In degraded mode, read operations remain available while write commands are queued with ordering guarantees.
- Clinics operate from offline rosters and manual check-in forms, then reconcile after recovery.
- Recovery pipeline replays commands, revalidates slot conflicts, and issues reconciliation notifications.
- Incident closure requires backlog drain, consistency checks, and a postmortem with corrective actions.
