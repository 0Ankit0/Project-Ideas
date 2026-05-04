# State Machine Diagram

Appointment and slot state machines must remain deterministic because reminders, payments, EHR sync, and reporting all derive from them.

## Appointment Lifecycle
```mermaid
stateDiagram-v2
  [*] --> Draft
  Draft --> PendingConfirmation: booking intent accepted
  PendingConfirmation --> Confirmed: commit succeeds
  PendingConfirmation --> Expired: token or verification expires
  Confirmed --> CheckedIn: arrival verified
  CheckedIn --> InConsultation: provider starts visit
  InConsultation --> Completed: provider closes encounter
  Confirmed --> Cancelled: patient or staff cancel
  Confirmed --> RebookRequired: provider schedule invalidated
  Confirmed --> NoShow: grace period elapsed
  RebookRequired --> Confirmed: replacement booked
  Completed --> [*]
  Cancelled --> [*]
  NoShow --> [*]
  Expired --> [*]
```

## Slot Lifecycle
```mermaid
stateDiagram-v2
  [*] --> Available
  Available --> Reserved: appointment confirmed
  Reserved --> LockedForVisit: check in completed
  Reserved --> Released: cancellation or reschedule
  LockedForVisit --> Released: visit completed or no show
  Available --> Blocked: planned closure or leave
  Available --> Suspended: credential or safety issue
  Blocked --> Available: block removed
  Suspended --> Available: suspension cleared
  Released --> Available: regenerated for future use
```

## Transition Guards
| Transition | Guard Condition | Side Effects |
|---|---|---|
| `PendingConfirmation -> Confirmed` | slot version still current, eligibility valid, payment gate passed | emit `appointment.booked.v1`, reserve slot |
| `Confirmed -> CheckedIn` | arrival window open, required intake and payment tasks completed | emit `appointment.checked_in.v1`, lock slot for visit |
| `Confirmed -> Cancelled` | actor authorized and cancellation policy evaluated | release slot, compute fee or refund, notify patient |
| `Confirmed -> RebookRequired` | provider calendar exception overlaps scheduled time | create outreach task, suppress normal reminder cadence |
| `Confirmed -> NoShow` | grace period elapsed with no arrival | optional fee, staff follow-up, analytics increment |
| `LockedForVisit -> Released` | visit outcome terminal | capture payment if due, sync EHR, update reports |

## Implementation Considerations
- State changes should be enforced in a domain state machine, not inferred from UI actions.
- Read models may lag briefly, but they must never invent impossible transitions.
- Manual overrides still use the same state machine and must carry explicit override metadata.

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
