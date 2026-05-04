# Use Case Diagram

This diagram highlights who interacts with the appointment platform and which capabilities must be implemented for a working clinic deployment.

```mermaid
flowchart LR
  Patient[Patient]
  FrontDesk[Front Desk Staff]
  Provider[Provider]
  Admin[Clinic Admin]
  Compliance[Compliance Officer]

  UC1((Search Providers and Slots))
  UC2((Book Appointment))
  UC3((Reschedule or Cancel))
  UC4((Join Waitlist))
  UC5((Check In Patient))
  UC6((Manage Schedule Templates))
  UC7((Create Calendar Exception))
  UC8((Collect Copay and Refund))
  UC9((Send Reminders and Alerts))
  UC10((Complete Visit or Mark No Show))
  UC11((Run Downtime Reconciliation))
  UC12((Export Audit and Reports))

  Patient --> UC1
  Patient --> UC2
  Patient --> UC3
  Patient --> UC4
  Patient --> UC5
  FrontDesk --> UC2
  FrontDesk --> UC3
  FrontDesk --> UC5
  FrontDesk --> UC8
  FrontDesk --> UC11
  Provider --> UC6
  Provider --> UC7
  Provider --> UC10
  Admin --> UC6
  Admin --> UC7
  Admin --> UC8
  Admin --> UC9
  Admin --> UC11
  Compliance --> UC11
  Compliance --> UC12
  UC2 --> UC8
  UC2 --> UC9
  UC3 --> UC8
  UC7 --> UC9
  UC10 --> UC12
```

## Actor Coverage Matrix
| Actor | Primary Use Cases | Notes |
|---|---|---|
| Patient | Search, book, reschedule, cancel, waitlist, check in | limited to own appointments and preferences |
| Front Desk Staff | Assisted booking, overrides, check-in, payment collection, downtime reconciliation | override actions require explicit justification |
| Provider | Manage recurring schedule, declare exceptions, complete visit, mark no-show | schedule changes can affect future patients |
| Clinic Admin | Tenant policy, reminder cadence, payment rules, downtime coordination | cross-clinic reporting access may be restricted |
| Compliance Officer | Audit review, downtime sign-off, PHI investigations | read-only to most transactional workflows |

## Use Case Relationships
- `Book Appointment` includes eligibility evaluation, optional copay authorization, and confirmation notification.
- `Reschedule or Cancel` includes policy evaluation and may trigger refund or fee workflows.
- `Create Calendar Exception` includes impacted-appointment analysis and emergency patient outreach.
- `Run Downtime Reconciliation` includes replay of manual queue items, conflict handling, and final compliance sign-off.

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
