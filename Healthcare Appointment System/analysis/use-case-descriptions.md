# Use Case Descriptions

These use cases describe the core healthcare scheduling flows the system must implement and validate.

## UC-01 Patient Self-Books Appointment
- **Primary actor:** Patient.
- **Supporting actors:** Patient portal, Scheduling API, Eligibility service, Payment gateway, Notification service, EHR adapter.
- **Goal:** Create a confirmed appointment with verified coverage and any required copay authorization.
- **Trigger:** Patient submits a booking request from the portal after selecting a slot.
- **Preconditions:** patient profile exists, consent for portal use is accepted, provider and slot are active, booking window allows the visit.
- **Main success scenario:**
  1. Patient searches providers and open slots.
  2. Portal requests eligibility and copay estimate.
  3. Patient confirms the slot, reason for visit, and notification preferences.
  4. Scheduling API validates slot version, payer requirements, and cancellation policy visibility.
  5. Payment service authorizes the copay if required.
  6. Appointment is persisted in `CONFIRMED` state, the slot becomes `RESERVED`, notifications are queued, and the EHR sync task is created.
- **Extensions:** stale slot version, inactive coverage, missing referral, prior auth required, payment authorization failure, messaging outage.
- **Postconditions:** appointment confirmation number returned, audit trail written, reminder schedule created.
- **Key APIs and events:** `GET /v1/providers/:id/slots`, `POST /v1/insurance/verify`, `POST /v1/appointments`, `appointment.booked.v1`.

## UC-02 Staff-Assisted Booking and Override
- **Primary actor:** Front desk staff.
- **Supporting actors:** Patient record service, Scheduling API, Audit service.
- **Goal:** Book an appointment for a patient who needs phone support, urgent overbooking, or manual assistance.
- **Trigger:** Staff receives a call, walk-in request, or provider escalation.
- **Preconditions:** staff member is authenticated with clinic-scoped permission; patient record exists or can be created.
- **Main success scenario:**
  1. Staff locates the patient or creates a new `STAFF_MANAGED` patient profile.
  2. Staff searches slots or invokes an authorized override workflow for urgent care.
  3. System validates staff permissions, records the booking agent, and stores any override reason or approving actor.
  4. Appointment is confirmed and patient receives outbound communication through the preferred reachable channel.
- **Extensions:** patient has no portal account, coverage requires manual verification, override approval denied, downtime mode active.
- **Postconditions:** appointment is visible on staff and provider queues with the booking source recorded.

## UC-03 Maintain Provider Availability
- **Primary actor:** Provider or clinic administrator.
- **Supporting actors:** Availability service, Scheduling service, Notification service.
- **Goal:** Publish recurring schedules and one-off exceptions without losing auditability or patient safety.
- **Trigger:** A provider updates office hours, vacation time, clinic closures, or emergency blocks.
- **Preconditions:** provider profile is active and credential status allows scheduling.
- **Main success scenario:**
  1. Actor retrieves the current provider calendar.
  2. Actor updates the weekly template or creates a calendar exception.
  3. Availability service regenerates future slots from the effective date.
  4. Scheduling service identifies impacted appointments and emits `appointment.rebook_required.v1` where needed.
  5. Notification service contacts affected patients and staff worklists are populated.
- **Extensions:** conflicting template blocks, credential suspension, same-day emergency closure, EHR sync lag.
- **Postconditions:** slot inventory is regenerated, rebooking worklist exists for impacted patients, audit evidence is complete.
- **Key APIs and events:** `GET/PUT /v1/admin/providers/:id/calendar`, `POST /v1/admin/providers/:id/calendar/exceptions`, `provider.calendar_exception_added.v1`.

## UC-04 Reschedule or Cancel Appointment
- **Primary actors:** Patient, front desk staff.
- **Supporting actors:** Scheduling API, Payment service, Notification service.
- **Goal:** Change or cancel an appointment while correctly applying windows, fees, refunds, and notifications.
- **Trigger:** Patient or staff requests a change to an existing appointment.
- **Preconditions:** appointment is not completed, and actor is authorized for the appointment.
- **Main success scenario:**
  1. System shows cancellation window, refund policy, and replacement slot options if rescheduling.
  2. Actor confirms the change.
  3. Scheduling service applies policy rules, reserves any replacement slot, and updates appointment history.
  4. Payment service voids or refunds the copay per policy outcome.
  5. Notification service sends updated confirmation or cancellation communication.
- **Extensions:** outside self-service window, refund processor timeout, new slot conflict, payer acceptance change, provider cancellation.
- **Postconditions:** slot inventory is correct, finance ledger matches the new outcome, patient receives a clear policy result.
- **Key APIs and events:** `PATCH /v1/appointments/:id/reschedule`, `PATCH /v1/appointments/:id/cancel`, `appointment.rescheduled.v1`, `appointment.cancelled.v1`.

## UC-05 Check In, Conduct Visit, and Close Encounter
- **Primary actors:** Front desk staff, provider.
- **Supporting actors:** Scheduling API, Billing service, EHR adapter.
- **Goal:** Move a confirmed appointment through arrival, consultation, and completion or no-show.
- **Trigger:** Patient arrives in person, checks in remotely for telehealth, or fails to arrive before grace period expiry.
- **Preconditions:** appointment is confirmed and falls within the arrival window.
- **Main success scenario:**
  1. Front desk or kiosk captures arrival details and outstanding demographics.
  2. System verifies intake, consent, and copay status and marks the appointment `CHECKED_IN`.
  3. Provider reviews readiness indicators and starts the consultation.
  4. Provider completes the encounter, recommends follow-up if needed, and EHR synchronization is triggered.
  5. Billing and analytics read models update with final visit outcome.
- **Extensions:** missing copay, telehealth link failure, patient leaves before provider arrival, no-show grace period reached.
- **Postconditions:** appointment is `COMPLETED` or `NO_SHOW`, slot is released, downstream systems are synchronized.

## UC-06 Downtime Operations and Recovery
- **Primary actors:** Operations lead, front desk staff, clinic administrator.
- **Supporting actors:** Downtime queue, reconciliation worker, compliance audit service.
- **Goal:** Continue safe clinic operations during outages and restore consistency afterward.
- **Trigger:** Platform, payment, messaging, or integration outage exceeds the tenant's downtime threshold.
- **Preconditions:** incident declared and downtime mode activated for affected clinics.
- **Main success scenario:**
  1. System freezes affected write paths and exposes read-only schedule views plus roster export.
  2. Staff record bookings, cancellations, and check-ins on approved downtime forms and queue entries.
  3. Once service returns, reconciliation workers replay queue items in timestamp order.
  4. Conflicts, duplicate payments, and notification gaps are reviewed by operations staff.
  5. Compliance and clinic leadership sign off on the recovered day.
- **Extensions:** paper forms missing identifiers, replay conflict caused by same slot being booked elsewhere, payment gateway settlement mismatch.
- **Postconditions:** all queue items are terminal, audit exports are available, unresolved discrepancies remain on a tracked incident record.

## Use Case to Service Mapping
| Use Case | Core Services | Key Events | Main Success Metric |
|---|---|---|---|
| Self-Book | Portal, Scheduling, Eligibility, Payments, Notifications | `appointment.booked.v1` | confirmation within 60 seconds |
| Staff-Assisted Booking | Staff console, Patient service, Scheduling, Audit | `appointment.override_booked.v1` | same-call resolution rate |
| Maintain Availability | Availability, Scheduling, Notifications | `provider.calendar_exception_added.v1`, `appointment.rebook_required.v1` | impacted patients contacted within 10 minutes |
| Reschedule or Cancel | Scheduling, Payments, Notifications | `appointment.rescheduled.v1`, `appointment.cancelled.v1` | refund outcome displayed immediately |
| Check In and Complete | Scheduling, Billing, EHR adapter | `appointment.checked_in.v1`, `appointment.completed.v1` | provider queue freshness under 5 seconds |
| Downtime Recovery | Downtime queue, Reconciliation worker, Audit | `ops.downtime_started.v1`, `ops.reconciliation_completed.v1` | all queue items signed off before close |

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
