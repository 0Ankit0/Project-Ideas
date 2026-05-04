# User Stories

This backlog turns the healthcare scheduling requirements into build-ready stories for the portal, staff console, scheduling services, and supporting integrations.

## Story Map by Persona

### Patient Stories
| ID | Story | Acceptance Notes | Primary APIs and Events |
|---|---|---|---|
| `US-PAT-01` | As a patient, I want to search by specialty, location, insurance, and telehealth availability so I can find a clinically appropriate slot without calling the clinic. | Search results show only active providers, honor accepted payer rules, and return slots from `GET /v1/providers/:id/slots` within the configured date window. | `GET /v1/providers`, `GET /v1/providers/:id/slots`, `availability.slot_published.v1` |
| `US-PAT-02` | As a patient, I want to book a visit after reviewing eligibility and estimated copay so I know the appointment is financially valid before confirmation. | Booking requires a fresh reservation token or slot version, invokes `POST /v1/insurance/verify`, and blocks confirmation when coverage is inactive or prior authorization is missing. | `POST /v1/appointments`, `POST /v1/insurance/verify`, `appointment.booked.v1`, `eligibility.verified.v1` |
| `US-PAT-03` | As a patient, I want to receive reminders in my preferred channel so I do not miss appointments. | Preferences from `GET/PATCH /v1/notifications/preferences` respect consent, language, quiet hours, and same-day escalation rules. | `PATCH /v1/notifications/preferences`, `notification.requested.v1`, `notification.delivered.v1` |
| `US-PAT-04` | As a patient, I want to reschedule or cancel within policy and see any refund or late-cancel fee before I confirm the change. | UI shows cancellation window, refund amount, and replacement slot options before `PATCH /v1/appointments/:id/reschedule` or `PATCH /v1/appointments/:id/cancel` executes. | `PATCH /v1/appointments/:id/reschedule`, `PATCH /v1/appointments/:id/cancel`, `payment.refund_requested.v1` |
| `US-PAT-05` | As a patient, I want self check-in to verify my demographics, intake forms, and copay status when I arrive. | Check-in blocks completion if required consent, demographic verification, or copay collection tasks remain open. | `PATCH /v1/appointments/:id/check-in`, `appointment.checked_in.v1` |

### Front Desk and Scheduling Staff Stories
| ID | Story | Acceptance Notes | Primary APIs and Events |
|---|---|---|---|
| `US-STAFF-01` | As front desk staff, I want to create appointments on behalf of a patient by phone so I can support patients who cannot self-serve. | Staff can search or create the patient record inline, capture booking channel as `STAFF_ASSISTED`, and store the booking agent in the audit log. | `GET /v1/patients`, `POST /v1/patients`, `POST /v1/appointments`, `audit.appointment_mutation.v1` |
| `US-STAFF-02` | As scheduling staff, I want to override normal capacity rules for urgent visits with approval evidence so urgent care can be accommodated safely. | Override booking requires a reason, approving actor, and visible banner on the appointment and provider worklist. | internal override command, `appointment.override_booked.v1` |
| `US-STAFF-03` | As front desk staff, I want a rebooking worklist when provider schedules change so affected patients are contacted in priority order. | Worklist sorts by appointment date, patient risk category, and notification failure status after a calendar exception is created. | `POST /v1/admin/providers/:id/calendar/exceptions`, `appointment.rebook_required.v1` |
| `US-STAFF-04` | As front desk staff, I want downtime booking and check-in procedures so the clinic can continue during outages. | Downtime actions produce queue items with reconciliation status, paper roster references, and required supervisor sign-off after recovery. | downtime queue service, `ops.downtime_started.v1`, `ops.reconciliation_completed.v1` |

### Provider and Clinical Operations Stories
| ID | Story | Acceptance Notes | Primary APIs and Events |
|---|---|---|---|
| `US-PROV-01` | As a provider, I want weekly schedule templates, location-specific blocks, and emergency closures so my calendar reflects reality. | Template replacement regenerates future slots only; exceptions immediately mark impacted appointments and block new bookings. | `GET/PUT /v1/admin/providers/:id/calendar`, `POST /v1/admin/providers/:id/calendar/exceptions` |
| `US-PROV-02` | As a provider, I want visit readiness indicators for eligibility, intake, copay, and referral completion so I know whether the patient is ready. | The provider dashboard shows readiness badges from the latest eligibility, payment, and intake projections without exposing unnecessary PHI. | read models, `eligibility.verified.v1`, `payment.authorized.v1`, `appointment.checked_in.v1` |
| `US-PROV-03` | As a provider, I want to update visit status quickly so downstream EHR, billing, and reporting processes remain accurate. | `CHECKED_IN`, `IN_CONSULTATION`, `COMPLETED`, and `NO_SHOW` transitions enforce valid state order and write audit evidence. | `PATCH /v1/appointments/:id/check-in`, `PATCH /v1/appointments/:id/complete`, `appointment.completed.v1` |

### Billing, Compliance, and Platform Admin Stories
| ID | Story | Acceptance Notes | Primary APIs and Events |
|---|---|---|---|
| `US-ADMIN-01` | As an administrator, I want tenant-level rules for cancellation windows, reminder cadence, and copay policy so each clinic can operate according to its own policies. | Policy changes are versioned, effective-dated, and traceable to all appointments evaluated under that policy version. | policy admin APIs, `policy.updated.v1` |
| `US-ADMIN-02` | As a compliance officer, I need immutable audit logs for PHI access, schedule mutations, and manual overrides so investigations can be completed from the platform alone. | Audit exports include actor, patient, action, purpose, source channel, and correlation id; tampering is prevented by append-only storage. | audit query APIs, `audit.phi_accessed.v1`, `audit.override_applied.v1` |
| `US-ADMIN-03` | As a revenue-cycle lead, I want copay authorizations, captures, voids, and refunds reconciled to appointments so payment leakage is detectable. | Every payment ledger record references appointment id, processor transaction id, and policy reason; orphaned authorizations are swept every 15 minutes. | payment service APIs, `payment.authorized.v1`, `payment.voided.v1`, `payment.refunded.v1` |

## Release Slice Recommendations
1. **MVP booking slice:** provider search, slot lookup, self-booking, confirmation notification, staff-assisted booking, and basic audit logging.
2. **Financial readiness slice:** insurance verification, copay estimation, authorization holds, cancellation fee logic, and reconciliation jobs.
3. **Visit operations slice:** check-in, reminder escalation, no-show handling, telehealth session launch, and EHR synchronization.
4. **Operational resilience slice:** downtime mode, emergency schedule blocks, manual outreach worklists, and compliance exports.

## Detailed Story Example

### `US-PAT-02` — Book an Appointment
- **Goal:** Confirm a visit only when provider, slot, eligibility, and copay rules pass.
- **Primary actor:** Authenticated patient.
- **Supporting actors:** Scheduling API, Eligibility service, Payment gateway, Notification service, EHR adapter.
- **Trigger:** Patient submits a booking request with `Idempotency-Key`, `slot_id`, `slot_version`, `visit_type`, and notification preferences.
- **Preconditions:** patient profile is active, provider is schedulable, slot is open, referral and prior authorization requirements are known, and clinic booking window allows the visit.
- **Main flow:**
  1. Portal obtains slot availability and displays the estimated copay and policy notices.
  2. Booking API validates the idempotency key, slot version, booking window, and patient consent prerequisites.
  3. Eligibility service verifies active coverage and returns copay, referral, and prior-auth flags.
  4. Payment service authorizes the copay hold when the visit type requires prepayment.
  5. Scheduling transaction persists the appointment, reserves the slot, writes audit entries, and stores an outbox message.
  6. Notification service sends confirmation and reminder schedules; EHR adapter creates or updates the external appointment resource.
- **Failure flows:**
  - `SLOT_ALREADY_BOOKED`: return the next three valid slots plus the stale slot version.
  - `INSURANCE_NOT_VERIFIED`: place the request in manual verification mode and block payment capture.
  - `PAYMENT_AUTH_FAILED`: release the slot, return a recoverable payment error, and keep no appointment record beyond the audit attempt.
  - `FHIR_SYNC_DELAYED`: keep the appointment confirmed, flag the EHR sync task, and surface an operations alert.
- **Postconditions:** appointment is `CONFIRMED`, slot is `RESERVED`, payment is `AUTHORIZED` or explicitly waived, patient receives a confirmation number, and all side effects are traceable.
- **Definition of done:** contract tests cover the booking API, integration tests cover eligibility and payment compensations, and observability captures `tenant_id`, `clinic_id`, `provider_id`, `appointment_id`, and `correlation_id` for every booking attempt.

## Operational Acceptance Criteria
- Same-day urgent bookings created by staff must appear on the provider queue within 5 seconds.
- Emergency provider blocks must notify affected patients within 10 minutes of the exception being created.
- No-show automation must wait for the clinic grace period before status mutation and fee assessment.
- Downtime reconciliation must reach a signed-off state before the clinic day is closed.

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
