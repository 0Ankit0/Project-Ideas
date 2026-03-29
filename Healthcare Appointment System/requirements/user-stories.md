# User Stories

## Story Map by Persona

### Patient Stories
1. **As a patient**, I want to find the earliest appointment for my condition so I can receive care quickly.
   - Acceptance: supports specialty, distance, telehealth, insurance filters.
2. **As a patient**, I want reminders in my preferred channel so I do not miss appointments.
   - Acceptance: channel consent and quiet hours respected.
3. **As a patient**, I want clear cancellation/refund outcomes before confirming changes.
   - Acceptance: policy preview displays fees and refund timeline.

### Provider Stories
1. **As a provider**, I want schedule templates and exception blocks so my calendar remains accurate.
2. **As a provider**, I want a concise visit queue with readiness indicators (intake, eligibility, copay).
3. **As a provider**, I want to mark visit status quickly (in consultation/completed/no-show).

### Front Desk Stories
1. **As front desk staff**, I want conflict resolution recommendations when a slot is no longer valid.
2. **As front desk staff**, I want offline fallback check-in capability during outages.
3. **As front desk staff**, I want a reconciliation worklist after recovery.

### Compliance/Admin Stories
1. **As a compliance officer**, I need immutable audit logs for PHI access and schedule mutations.
2. **As an admin**, I want tenant-level policy controls for cancellation windows and reminder cadence.

## Detailed Story Example (Implementation-Ready)
### US-BOOK-001: Book an Appointment
- **Preconditions:** patient verified, provider active, slot AVAILABLE.
- **Trigger:** patient submits booking command with idempotency key.
- **Main flow:** reserve slot -> persist appointment -> publish `appointment.confirmed.v1` -> trigger notifications.
- **Postconditions:** appointment `CONFIRMED`, slot `RESERVED`, audit entry written.
- **Failure flows:** conflict (`409`), payment auth failure (`402`), provider suspended (`423`).
- **Definition of done:** contract tests, integration tests, and observability fields validated.

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
