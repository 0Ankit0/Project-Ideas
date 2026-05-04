# Booking and Payments Edge Cases

These scenarios cover the failure modes where slot reservation and money movement can diverge. The implementation must preserve patient trust, financial accuracy, and auditability in every case.

## Combined Failure Scenarios
| Scenario | Detection Point | Required System Behavior | Manual Follow-Up |
|---|---|---|---|
| Slot still looks open in cache but is already reserved in the database | booking commit | reject with `SLOT_ALREADY_BOOKED`, return alternatives, invalidate cache | none unless repeated cache drift alerts fire |
| Payment authorized but appointment commit fails | after payment response | void the authorization immediately, write reconciliation task, return recoverable error | finance reviews any authorization still open after 15 minutes |
| Appointment confirmed but payment capture later fails | check-in or completion settlement | keep appointment valid, flag `PAYMENT_ATTENTION_REQUIRED`, route to staff collection workflow | revenue-cycle staff contacts patient and records outcome |
| Gateway timeout with unknown payment outcome | payment call timeout | mark payment intent `PENDING_PROCESSOR_CONFIRMATION`, hold slot for short window, poll webhook before releasing or confirming | finance queue resolves if still unknown after SLA window |
| Reschedule succeeds but refund API fails | cancellation compensation | keep new appointment valid, create retryable refund task, show patient expected refund timeline | supervisor reviews unresolved refund older than 1 business day |
| Same patient opens two browser tabs and submits booking twice | idempotency check | first request wins, second returns original confirmation using same key or a conflict on a new key | none |
| Staff override books beyond capacity without valid approval | policy engine | reject commit and write compliance audit event | clinic manager reviews attempted override |
| Coverage changes between estimate and booking confirmation | fresh eligibility check | block booking or show explicit out-of-network acknowledgment requirement | insurance coordinator may assist with manual options |

## Saga and Compensation Rules
1. Reservation comes before payment capture but after pre-authorization checks.
2. Authorization hold is compensatable through void until capture occurs.
3. Appointment confirmation is the pivot point: after it commits, failures must be handled with compensating finance or notification tasks, not silent rollback.
4. Refund jobs reconcile against appointment state, policy version, and processor settlement status before issuing money movement.

## Reconciliation Jobs
- Sweep orphaned authorizations every 15 minutes and classify them as `VOIDED`, `CAPTURE_PENDING`, or `MANUAL_REVIEW`.
- Match appointment ledger rows to processor settlements by `processor_reference`, `appointment_id`, and `correlation_id`.
- Re-run late cancellation fee calculations nightly for appointments whose policy changed due to incident recovery or manual override.
- Escalate unresolved payment mismatches older than 1 hour during clinic hours and 4 hours off-hours.

## Compliance and UX Notes
- Store only tokenized payment references and masked card metadata.
- Patient-facing error messages must explain whether money moved, whether the slot is still held, and what the next action should be.
- Booking receipts and cancellation confirmations must show copay, fee, refund, and expected settlement timing.
- Finance staff need a searchable view filtered by clinic, processor, appointment date, and policy reason code.

## Operational Acceptance Criteria
- No orphaned authorization remains unresolved beyond the configured sweep threshold without a visible task owner.
- Refund decisions are reproducible from audit data alone.
- Concurrent booking or reschedule races never result in two confirmed appointments for the same slot.

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
