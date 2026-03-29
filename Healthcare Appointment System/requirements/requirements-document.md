# Requirements Document

## 1. Product Scope
The **Healthcare Appointment System (HAS)** provides online and assisted scheduling, intake, reminder orchestration, and visit lifecycle management for outpatient clinics. The scope includes multi-tenant support for healthcare groups with centralized policy controls and location-level operating constraints.

## 2. Stakeholders and Objectives
- **Patients:** discover providers, book visits, receive reminders, complete intake.
- **Providers:** publish availability, review schedules, start/complete visits.
- **Front Desk/Operations:** resolve conflicts, process check-ins, handle downtime.
- **Compliance/Security:** enforce privacy controls, retention, and auditability.

## 3. Functional Requirements
### FR-1 Scheduling & Availability
1. System shall expose provider availability by specialty, location, visit type, and payer constraints.
2. System shall support same-day, future-date, recurring, and waitlist bookings.
3. System shall prevent double-booking through atomic reservation and version checks.

### FR-2 Appointment Lifecycle
1. System shall support appointment state transitions from draft through completion with explicit terminal states.
2. System shall enforce transition guards (consent complete, insurance verified, provider active, clinic open).
3. System shall produce domain events for every accepted transition.

### FR-3 Notifications
1. System shall send booking confirmations, reminders, reschedules, and cancellation notices.
2. System shall allow per-channel consent and quiet-hour restrictions.
3. System shall support retry, dead-lettering, and manual outreach fallback.

### FR-4 Billing & Payments
1. System shall compute eligibility for copay, no-show fee, and refund amounts by policy.
2. System shall capture payment intent at booking and settlement on configurable milestones.
3. System shall maintain ledger-grade immutable transaction records.

### FR-5 Administration & Reporting
1. System shall provide operational dashboards for conflict rate, no-show rate, and notification delivery health.
2. System shall export compliance reports with PHI minimization.
3. System shall support tenant-specific policy overrides with audit trail.

## 4. Non-Functional Requirements
- **Availability:** 99.9% monthly for patient booking APIs.
- **Performance:** P95 booking response < 800 ms; P99 < 1.8 s.
- **Scalability:** 10x seasonal surge without architectural changes.
- **Security:** HIPAA-aligned safeguards, encryption at rest and in transit, MFA for privileged access.
- **Observability:** trace id on every request and domain event; SLO alerting on critical paths.

## 5. Acceptance Criteria (Implementation Ready)
- All lifecycle transitions enforced by state machine tests.
- Race-condition simulation confirms no double-booking under concurrent load.
- Notification retry/dead-letter flows validated in staging.
- Downtime and recovery playbook executed successfully in game-day drills.

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
