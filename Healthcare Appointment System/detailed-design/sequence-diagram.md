# Sequence Diagram

This detailed sequence shows the write path for `POST /v1/appointments`, including compensation behavior for eligibility or payment failures.

```mermaid
sequenceDiagram
  actor Patient
  participant Portal as PatientPortal
  participant Gateway as APIGateway
  participant Sched as SchedulingService
  participant Slot as SlotRepository
  participant Elig as EligibilityClient
  participant Pay as PaymentCoordinator
  participant DB as AppointmentDB
  participant Outbox as OutboxRelay
  participant Notify as NotificationWorker
  Patient->>Portal: Confirm chosen slot
  Portal->>Gateway: POST /v1/appointments
  Gateway->>Sched: CreateBooking command
  Sched->>Slot: Lock slot by id
  Sched->>Slot: Check slot version
  Slot-->>Sched: Slot available
  Sched->>Elig: Verify eligibility
  Elig-->>Sched: Eligibility valid
  Sched->>Pay: Authorize copay hold
  Pay-->>Sched: Authorization approved
  Sched->>DB: Insert appointment record
  Sched->>DB: Insert history record
  Sched->>DB: Update slot to RESERVED
  Sched->>DB: Insert outbox rows
  DB-->>Sched: Commit success
  Sched-->>Gateway: 201 confirmed
  Gateway-->>Portal: Confirmation response
  Outbox->>Notify: Publish confirmation event
  Notify->>Notify: Check dedupe key
  alt Payment fails
    Pay-->>Sched: Authorization failed
    Sched->>Slot: Release reservation token
    Sched-->>Gateway: 402 payment failure
  else Eligibility expires
    Elig-->>Sched: Coverage invalid
    Sched->>Slot: Release reservation token
    Sched-->>Gateway: 409 manual verification required
  end
```

## Message-Level Notes
- `Lock slot by id and version` must execute under transaction isolation that prevents a second confirmed winner.
- The scheduling service should not write notification delivery rows directly; it writes an outbox event and lets the worker own channel retries.
- Payment authorization happens before the appointment commit, but capture usually waits until check-in or visit completion depending on tenant policy.
- Every request and event propagation step carries the same `correlation_id` for traceability.

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
