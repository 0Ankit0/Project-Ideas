# System Sequence Diagram

This system-level sequence covers the most business-critical path: booking an appointment with coverage verification, copay authorization, and downstream confirmation.

```mermaid
sequenceDiagram
  actor Patient
  participant Portal as PatientPortal
  participant Gateway as APIGateway
  participant Avail as AvailabilityService
  participant Sched as SchedulingService
  participant Elig as EligibilityService
  participant Pay as BillingService
  participant Notify as NotificationService
  participant EHR as EHRAdapter
  Patient->>Portal: Choose slot
  Patient->>Portal: Choose visit type
  Portal->>Gateway: Submit booking request
  Gateway->>Avail: Validate slot version
  Avail-->>Gateway: Slot available
  Gateway->>Sched: Create booking command
  Sched->>Elig: Verify coverage
  Elig-->>Sched: Coverage result
  alt Coverage valid
    Sched->>Pay: Authorize copay hold
    Pay-->>Sched: Authorization approved
    Sched->>Sched: Persist appointment transaction
    Sched->>Notify: Queue confirmation
    Sched->>Notify: Queue reminder schedule
    Sched->>EHR: Queue appointment sync
    Sched-->>Gateway: Appointment confirmed
    Gateway-->>Portal: Confirmation number
    Portal-->>Patient: Show confirmation
  else Manual review required
    Sched-->>Gateway: Return manual review outcome
    Gateway-->>Portal: Explain next actions
  end
```

## System Contracts
- The portal must supply `Idempotency-Key`, `slot_id`, `slot_version`, `visit_type`, `patient_id`, and notification preferences.
- The scheduling service owns the final appointment commit and is the only component allowed to transition a slot from bookable to reserved.
- Eligibility and payment responses may be cached briefly, but the scheduling service must verify freshness before confirming the visit.
- Notification and EHR work are asynchronous after commit; failure to complete them must not roll back the confirmed appointment.

## Failure Handling
- If slot validation fails, the portal receives a conflict response plus alternative slots.
- If copay authorization fails, the appointment is not created and the user gets a recoverable payment message.
- If EHR or notification delivery fails after commit, the appointment remains confirmed while the work item is retried and surfaced operationally.

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
