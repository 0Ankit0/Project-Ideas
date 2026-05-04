# BPMN Swimlane Diagram

The swimlane view shows operational responsibility across patient, clinic staff, core platform services, external systems, and providers.

## Booking to Visit Swimlanes
```mermaid
flowchart LR
  subgraph Patient[Patient]
    P1[Choose provider and slot]
    P2[Review cost and policy notice]
    P3[Confirm booking]
    P4[Receive reminders]
    P5[Arrive or join telehealth session]
  end

  subgraph FrontDesk[Front Desk]
    F1[Assist phone booking]
    F2[Resolve manual eligibility issues]
    F3[Check in patient]
    F4[Contact no-show or rebook list]
  end

  subgraph Platform[Healthcare Appointment System]
    S1[Validate slot and booking rules]
    S2[Create appointment and audit record]
    S3[Drive reminders and worklists]
    S4[Track visit lifecycle]
    S5[Queue downtime reconciliation]
  end

  subgraph External[External Systems]
    E1[Insurance clearinghouse]
    E2[Payment gateway]
    E3[EHR and billing adapters]
    E4[SMS and email providers]
  end

  subgraph Provider[Provider]
    R1[Publish template and exceptions]
    R2[Review readiness queue]
    R3[Conduct visit]
    R4[Complete visit or mark no-show]
  end

  P1 --> S1
  F1 --> S1
  S1 --> E1
  E1 --> S1
  S1 --> E2
  E2 --> S2
  P2 --> P3
  P3 --> S2
  S2 --> E3
  S2 --> E4
  S2 --> S3
  S3 --> P4
  R1 --> S1
  P5 --> F3
  F3 --> S4
  S4 --> R2
  R2 --> R3
  R3 --> R4
  R4 --> S4
  S4 --> E3
  S3 --> F4
  S5 --> F4
  F2 --> S2
```

## Lane Responsibilities
| Lane | Responsibility | Key Outputs |
|---|---|---|
| Patient | Discover care, consent to booking, respond to reminders, attend visit | Booking confirmation, intake completion, telehealth join |
| Front Desk | Support non-digital patients, resolve eligibility exceptions, check in arrivals, manage downtime forms | Staff-assisted bookings, reconciled worklists |
| Healthcare Appointment System | Enforce policy, reserve slots, persist appointments, emit events, produce dashboards | Appointment state, audit trail, notification tasks |
| External Systems | Validate coverage, authorize funds, sync schedule state, deliver communications | Eligibility response, payment decision, EHR sync status |
| Provider | Publish schedule constraints, review readiness, conduct visit, close encounter | Schedule template, visit disposition, follow-up recommendation |

## BPMN Semantics to Preserve in Implementation
- Message boundaries between the platform and external systems are asynchronous and must use retry plus dead-letter handling.
- Patient and front-desk entry points converge on the same booking policy engine so self-service and assisted flows produce identical appointment outcomes.
- Provider schedule mutations are upstream events that can invalidate downstream bookings; the platform must recalculate impact immediately.

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
