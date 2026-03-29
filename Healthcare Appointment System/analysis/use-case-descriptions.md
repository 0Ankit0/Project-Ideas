# Use Case Descriptions

## UC-01 Book Appointment
- **Primary actor:** Patient
- **Supporting actors:** Scheduling API, Payment service, Notification service
- **Goal:** Confirm a valid appointment with payment/eligibility checks.
- **Preconditions:** patient account exists; provider/location active; slot available.
- **Main success scenario:**
  1. Patient selects provider, visit type, and slot.
  2. System validates eligibility, policy constraints, and slot version.
  3. System reserves slot and creates appointment (`CONFIRMED`).
  4. System sends confirmation and writes audit/event records.
- **Extensions:** conflict handling, payment fallback, consent missing, channel failures.

## UC-02 Reschedule Appointment
- Guardrails: within reschedule window, provider availability exists, replacement slot valid.
- Business outcomes: old slot released atomically, new slot reserved, reschedule notifications emitted.

## UC-03 Cancel Appointment
- Supports patient cancellation, provider cancellation, and administrative force-cancel.
- Fee/refund policy depends on cancellation window and visit type.

## UC-04 Provider Check-In and Visit Completion
- Intake verified -> check-in -> consultation -> completion.
- No-show path includes configurable grace period and optional fee application.

## UC-05 Downtime and Recovery
- During outage, staff performs manual check-ins using downtime roster.
- Recovery process replays queued commands and reconciles mismatches.

## Use-Case to Service Mapping
| Use Case | Core Services | Key Events |
|---|---|---|
| Book | Scheduling, Eligibility, Payments, Notifications | `appointment.confirmed.v1` |
| Reschedule | Scheduling, Notifications | `appointment.rescheduled.v1` |
| Cancel | Scheduling, Billing, Notifications | `appointment.cancelled.v1` |
| Check-In/Complete | Visit workflow, EHR adapter | `appointment.checked_in.v1`, `appointment.completed.v1` |
| Downtime Recovery | Queue replay, Reconciliation | `ops.reconciliation.completed.v1` |

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
