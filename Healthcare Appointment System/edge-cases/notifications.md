# Notification Edge Cases

Reminder and alert delivery must handle consent changes, provider outages, and operational urgency without leaking PHI or confusing patients.

## Common Failure Modes
| Failure Mode | Detection | Required Behavior | Escalation |
|---|---|---|---|
| SMS or email provider outage | provider API error, webhook failure, or timeout | retry with backoff, fail over to secondary provider for critical notices, keep audit trail of every attempt | create operations incident after threshold breach |
| Template rendering fails because localization or dynamic data is missing | render pipeline validation | stop send, raise `template_error`, route to fallback approved template if allowed | notify content owner and support queue |
| Patient revokes consent after event emission but before send | final delivery gate | suppress delivery, mark dispatch `SUPPRESSED`, avoid duplicate escalation | none unless critical same-day notice requires phone outreach |
| Duplicate event delivery from broker replay | dedupe key check | drop duplicate side effect while keeping observability count | none |
| Quiet hours conflict with same-day appointment reminder | policy evaluation at send time | defer non-critical reminder until quiet window ends or use approved emergency template | front desk phone call for high-risk cases |
| Bounce or invalid phone number | provider webhook | mark destination unverified, suppress future attempts, prompt staff to collect updated contact data | patient contact worklist |
| Provider cancellation within two hours of start | schedule exception impact workflow | bypass quiet-hour suppression if clinic policy allows emergency outreach, send staff task immediately | manual outreach until acknowledgement obtained |
| Telehealth link generation delayed | pre-visit reminder build | send reminder without link only if policy allows, otherwise hold message until link available or escalate | support and provider dashboard alert |

## Delivery Controls
- Retry policy is channel-specific: SMS and push use shorter retry intervals for same-day relevance, email can tolerate longer backoff.
- The final send decision re-evaluates patient preference, consent, language, quiet hours, and appointment state.
- Message dedupe key is `event_id + channel + template_version + destination_hash`.
- Delivery receipts, bounces, complaints, and opt-outs update the patient communication preference record within minutes.

## Message Quality and Privacy
| Message Type | Must Include | Must Exclude |
|---|---|---|
| Booking confirmation | clinic name, date and time, location or telehealth instructions, contact path, confirmation number | diagnosis, chief complaint, referral notes |
| Reminder | appointment time, arrival instructions, check-in link, cancellation policy reminder | test results, medication names, detailed treatment context |
| Cancellation or emergency closure | who initiated the change, replacement or callback instructions, expected refund if relevant | free-text provider notes |
| Waitlist offer | offered slot, response deadline, booking CTA | internal priority score or other patient data |

## Operational KPIs
- Delivery success rate by channel and notification category.
- Median time from appointment commit to first confirmation attempt.
- Manual outreach rate for same-day cancellations and provider closures.
- Opt-out rate by tenant and channel to detect over-messaging.

## Operational Acceptance Criteria
- Critical appointment events retain a communication trail even if no automated delivery succeeds.
- Suppressed notifications remain explainable from consent, quiet-hour, or state data.
- Emergency schedule-change notices can be replayed safely without duplicate patient confusion.

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
