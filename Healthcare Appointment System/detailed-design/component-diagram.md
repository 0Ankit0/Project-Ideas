# Component Diagram

The detailed component map below shows how the core services collaborate to implement clinic scheduling and visit operations.

```mermaid
flowchart LR
  subgraph Entry[Channel and API Layer]
    Portal[Patient Portal]
    Staff[Staff Console]
    ProviderUI[Provider Workspace]
    Gateway[API Gateway]
  end

  subgraph Services[Domain Services]
    Scheduling[Scheduling Service]
    Availability[Availability Service]
    Eligibility[Eligibility Service]
    Billing[Billing Service]
    Notifications[Notification Orchestrator]
    Waitlist[Waitlist Service]
    Downtime[Downtime Service]
    Audit[Audit Service]
  end

  subgraph Data[State and Messaging]
    AppDB[(Appointments DB)]
    PatientDB[(Patients DB)]
    Ledger[(Payment Ledger)]
    Cache[(Slot Cache)]
    Bus[(Event Bus)]
  end

  subgraph Integrations[Adapters]
    EHR[EHR Adapter]
    Clearinghouse[Insurance Adapter]
    Payments[Payment Adapter]
    Messaging[Messaging Adapter]
    Video[Telehealth Adapter]
  end

  Portal --> Gateway
  Staff --> Gateway
  ProviderUI --> Gateway
  Gateway --> Scheduling
  Gateway --> Availability
  Gateway --> Billing
  Gateway --> Audit
  Scheduling --> AppDB
  Scheduling --> Bus
  Scheduling --> EHR
  Scheduling --> Video
  Availability --> AppDB
  Availability --> Cache
  Eligibility --> PatientDB
  Eligibility --> Clearinghouse
  Billing --> Ledger
  Billing --> Payments
  Notifications --> Messaging
  Notifications --> Bus
  Waitlist --> Bus
  Waitlist --> AppDB
  Downtime --> AppDB
  Downtime --> Bus
  Audit --> AppDB
  Audit --> Ledger
  Scheduling --> Eligibility
  Scheduling --> Billing
  Scheduling --> Notifications
  Scheduling --> Waitlist
```

## Component Interaction Rules
- The gateway may aggregate reads, but writes always route to the domain service that owns the aggregate.
- Scheduling orchestrates the booking lifecycle and calls eligibility and billing synchronously only when policy requires a fresh result.
- Notification, waitlist, and reporting updates are event-driven to keep patient-facing APIs responsive.
- Downtime service is write-capable only during declared degraded mode and otherwise acts as a read-only incident utility.

## Failure Isolation
- External integration failures are contained inside adapters and surfaced as retryable or terminal reason codes.
- Cache invalidation failures can affect search freshness, but booking commit still relies on the authoritative appointment database.
- Ledger persistence is isolated from general appointment reads to keep finance reconciliation auditable and queryable.

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
