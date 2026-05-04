# Class Diagram

The domain model below identifies the classes needed to implement booking, scheduling, payments, reminders, and downtime recovery.

```mermaid
classDiagram
  class PatientProfile {
    +patientId
    +mrn
    +fullName
    +dateOfBirth
    +preferredLanguage
    +portalStatus
  }
  class InsuranceCoverage {
    +coverageId
    +payerName
    +subscriberId
    +effectiveFrom
    +effectiveTo
    +status
  }
  class Provider {
    +providerId
    +npi
    +displayName
    +specialtyCode
    +status
  }
  class ProviderCalendar {
    +calendarId
    +timezone
    +effectiveFrom
    +version
  }
  class ScheduleTemplateRule {
    +templateRuleId
    +dayOfWeek
    +startTime
    +endTime
    +slotDurationMinutes
    +bufferMinutes
  }
  class CalendarException {
    +exceptionId
    +exceptionType
    +dateFrom
    +dateTo
    +reasonCode
  }
  class Slot {
    +slotId
    +startTime
    +endTime
    +slotVersion
    +status
  }
  class Appointment {
    +appointmentId
    +confirmationNumber
    +visitType
    +channel
    +status
    +bookingChannel
  }
  class AppointmentStatusHistory {
    +historyId
    +fromStatus
    +toStatus
    +reasonCode
    +occurredAt
  }
  class EligibilityCheck {
    +eligibilityCheckId
    +eligible
    +copayAmountCents
    +priorAuthRequired
    +validUntil
  }
  class PaymentIntent {
    +paymentIntentId
    +amountCents
    +status
    +processorReference
  }
  class Refund {
    +refundId
    +amountCents
    +reasonCode
    +status
  }
  class CheckInRecord {
    +checkInId
    +method
    +checkedInAt
    +demographicVerified
    +copayCollected
  }
  class NotificationDispatch {
    +dispatchId
    +eventName
    +channel
    +status
    +attemptCount
  }
  class WaitlistEntry {
    +waitlistEntryId
    +earliestDate
    +latestDate
    +status
    +priorityScore
  }
  class AuditEvent {
    +auditEventId
    +action
    +purposeOfUse
    +createdAt
  }
  class DowntimeQueueItem {
    +queueItemId
    +actionType
    +capturedAt
    +reconciliationStatus
  }

  PatientProfile "1" --> "0..*" InsuranceCoverage : has
  PatientProfile "1" --> "0..*" Appointment : books
  PatientProfile "1" --> "0..*" WaitlistEntry : requests
  Provider "1" --> "1..*" ProviderCalendar : owns
  ProviderCalendar "1" --> "1..*" ScheduleTemplateRule : contains
  ProviderCalendar "1" --> "0..*" CalendarException : overrides
  Provider "1" --> "0..*" Slot : publishes
  Slot "1" --> "0..1" Appointment : reserved_by
  Appointment "1" --> "1..*" AppointmentStatusHistory : records
  Appointment "1" --> "0..1" EligibilityCheck : validates
  Appointment "1" --> "0..1" PaymentIntent : funds
  PaymentIntent "1" --> "0..*" Refund : compensates
  Appointment "1" --> "0..*" CheckInRecord : logs
  Appointment "1" --> "0..*" NotificationDispatch : sends
  Appointment "1" --> "0..*" AuditEvent : audits
  DowntimeQueueItem "0..*" --> "0..1" Appointment : reconciles
```

## Class Responsibilities
- `Appointment` is the aggregate root for booking, rescheduling, cancellation, check-in, completion, and no-show transitions.
- `Slot` remains a separate resource because availability generation, caching, and concurrency control differ from patient-facing appointment behavior.
- `EligibilityCheck`, `PaymentIntent`, and `NotificationDispatch` are attached process records; they are referenced during policy evaluation but can be retried independently.
- `AppointmentStatusHistory` and `AuditEvent` together provide user-facing chronology plus compliance-grade evidence.

## Key Invariants
- One active appointment may reference a slot at a time.
- `CheckInRecord` cannot exist for an appointment still in `DRAFT` or `PENDING_CONFIRMATION`.
- `Refund.amountCents` may not exceed the captured amount minus non-refundable fees.
- `DowntimeQueueItem` cannot be marked `SIGNED_OFF` until any derived appointment, payment, and notification tasks are terminal.

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
