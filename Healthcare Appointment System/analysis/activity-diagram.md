# Activity Diagram

This activity flow captures the end-to-end appointment journey for both patient self-booking and staff-assisted scheduling, including eligibility, payment, reminders, visit execution, and recovery paths.

## Primary Appointment Journey
```mermaid
flowchart TD
  A[Start booking request] --> B{Booking channel}
  B -->|Patient portal| C[Search provider and slot]
  B -->|Front desk| D[Search or create patient record]
  C --> E[Select visit type and slot]
  D --> E
  E --> F[Validate booking window and slot version]
  F --> G{Referral or prior auth required}
  G -->|Yes| H[Verify referral and auth status]
  G -->|No| I[Run insurance eligibility]
  H --> I
  I --> J{Coverage active}
  J -->|No| K[Send to manual verification queue]
  J -->|Yes| L[Estimate copay or waive payment]
  L --> M{Copay authorization needed}
  M -->|Yes| N[Authorize payment hold]
  M -->|No| O[Create appointment transaction]
  N --> P{Authorization approved}
  P -->|No| Q[Release slot hold and return payment error]
  P -->|Yes| O
  O --> R[Reserve slot and persist appointment]
  R --> S[Write audit and outbox records]
  S --> T[Notify patient and clinic]
  T --> U[Sync appointment to EHR and billing]
  U --> V[Schedule reminders and waitlist updates]
  V --> W[Patient arrives and checks in]
  W --> X{Ready for visit}
  X -->|No| Y[Resolve intake or copay issues]
  Y --> X
  X -->|Yes| Z[Provider starts consultation]
  Z --> AA[Complete visit or mark no-show]
  AA --> AB[Release slot and finalize ledger]
  K --> AC[Staff completes manual review]
  AC --> E
  Q --> AD[End with recoverable failure]
  AB --> AE[End with auditable appointment outcome]
```

## Alternate Flow Notes
- **Reschedule:** after `R`, the old slot is released only when the new slot reservation succeeds in the same transaction.
- **Cancellation:** a confirmed appointment can branch from `V` to cancellation policy evaluation, refund calculation, slot release, and notification dispatch.
- **Emergency schedule change:** future confirmed appointments bypass `W` and enter `REBOOK_REQUIRED`, producing staff worklist tasks.
- **Downtime mode:** if scheduling writes are unavailable at `O`, staff capture the request on the downtime queue and reconcile after recovery.

## Implementation Notes
- The flow maps directly to `GET /v1/providers/:id/slots`, `POST /v1/insurance/verify`, `POST /v1/appointments`, `PATCH /v1/appointments/:id/check-in`, and `PATCH /v1/appointments/:id/complete`.
- Eligibility, payment, and notification side effects must be idempotent because retries may occur after partial failures.
- Every decision branch must emit metrics and structured logs so booking drop-off, no-show risk, and manual workload are measurable.

## Operational Policy Addendum

### Scheduling Conflict Policies
- Double-booking is prevented by the natural key `provider_id + location_id + slot_start + slot_end` plus optimistic locking on `slot_version` during booking and rescheduling.
- Reservation tokens shield a slot for up to 10 minutes during patient checkout, but the slot does not transition to `RESERVED` until the appointment transaction commits.
- Provider calendar updates caused by leave, clinic closure, overrun, or emergency blocks trigger immediate impact analysis; future appointments move to `REBOOK_REQUIRED` and create a staffed outreach task.
- Staff-assisted overrides may exceed normal template capacity only when a justification, approving actor, and override expiry are stored in the audit trail.

### Patient and Provider Workflow States
- Appointment lifecycle: `DRAFT -> PENDING_CONFIRMATION -> CONFIRMED -> CHECKED_IN -> IN_CONSULTATION -> COMPLETED`, with terminal states `CANCELLED`, `NO_SHOW`, `EXPIRED`, and `REBOOK_REQUIRED`.
- Slot lifecycle: `AVAILABLE -> RESERVED -> LOCKED_FOR_VISIT -> RELEASED`, with exceptional states `BLOCKED` for planned closures and `SUSPENDED` for compliance or credential issues.
- Invalid state transitions fail fast with deterministic error codes and do not publish downstream billing or notification events.
- Every transition records actor, channel, reason code, correlation id, timestamp, and source IP where available.

### Notification Guarantees
- Confirmation, reminder, cancellation, reschedule, emergency-closure, and waitlist-offer notifications are delivered through in-app, email, and SMS channels according to patient consent and clinic policy.
- Delivery is at-least-once with message deduplication keyed by `event_id + template_version + channel`; critical events retry for up to 24 hours before manual outreach is queued.
- Quiet hours suppress non-critical SMS and voice outreach, but life-safety or same-day operational notices may escalate to approved emergency templates.
- Notification content follows the minimum-necessary standard and excludes diagnosis, treatment details, or referral notes from SMS and push previews.

### Privacy Requirements
- PHI and billing artifacts are encrypted in transit and at rest, and non-production data must be de-identified before use outside regulated workflows.
- Role-based and attribute-based access controls restrict patient, scheduling, billing, and audit data to least-privilege views; privileged access requires MFA.
- Audit logs are immutable, exportable, and searchable by patient, provider, actor, action, and correlation id for compliance investigations.
- Downtime printouts, callback lists, and manual forms are treated as regulated records and must be secured, reconciled, and shredded per clinic policy after recovery.

### Downtime Fallback Procedures
- In degraded mode, staff retain read-only access to schedules while new booking, cancellation, and payment actions are captured in an ordered reconciliation queue.
- Clinics maintain a printable daily roster, manual check-in sheet, and downtime appointment intake form to continue operations during platform or integration outages.
- Recovery replays queued commands in timestamp order, revalidates slot conflicts and insurance status, syncs EHR and billing side effects, and notifies patients if outcomes changed.
- Incident closure requires backlog drain, reconciliation sign-off, communication to affected clinics, and a post-incident review with corrective actions.
