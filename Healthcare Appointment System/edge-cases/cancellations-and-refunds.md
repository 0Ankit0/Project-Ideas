# Edge Cases: Cancellations and Refunds

**Domain:** Appointment Lifecycle · Billing · Patient Experience  
**Severity Classification:** P1 = Revenue or compliance risk; P2 = Patient experience degraded; P3 = Operational overhead  
**Owner:** Payments Platform Team + Scheduling Core Team  
**Last Reviewed:** 2025-07-11  

---

## Overview

Cancellation and refund workflows sit at the intersection of scheduling state machines, payment
processor APIs, and patient-facing policy rules. Failures here carry immediate financial liability,
regulatory exposure under HIPAA/PCI-DSS, and measurable patient trust erosion. Every edge case
below has been identified from production incident data or risk modelling and must be treated as a
first-class design concern, not an afterthought.

**Policy baseline:**
- Routine appointments: full refund if cancelled ≥ 24 h before; 50 % refund if 4 h–24 h; no refund if < 4 h.
- Specialist/procedure appointments: full refund if cancelled ≥ 48 h before; 50 % if 4 h–48 h; no refund if < 4 h.
- Provider-initiated cancellations: always 100 % refund, regardless of timing.
- No-show determination: system marks `NO_SHOW` at T+15 min post-slot-start if check-in event absent.

---

### EC-CXL-001: Same-Day Cancellation Outside Policy Window — Wrong Policy Applied

- **Failure Mode:** Patient cancels at T−3 h 45 min for a routine appointment. The policy engine
  reads the cancellation window boundary as `< 4 h = no refund` but computes the delta using
  wall-clock UTC while the appointment's `slot_start` is stored in the clinic's local timezone
  (e.g. America/Chicago, UTC−5 in winter). A timezone conversion bug causes the engine to believe
  the appointment is only T−2 h 45 min away, applying the no-refund tier and charging a
  $35–$150 cancellation fee the patient does not owe.
- **Impact:** Incorrect fee charged to ~0.3 % of same-day cancellations in multi-timezone
  deployments. Estimated $4,000–$18,000 monthly revenue that must be refunded retroactively once
  detected. Patient NPS drop of 12–18 points per affected cohort. Potential state-level consumer
  protection liability if systemic overcharging is demonstrated.
- **Detection:**
  ```sql
  -- Alert: cancellation fee applied where patient was outside the no-refund window
  SELECT appointment_id, patient_id, fee_charged_cents,
         computed_hours_before, actual_hours_before_utc, policy_tier_applied
  FROM cancellation_audit
  WHERE fee_charged_cents > 0
    AND actual_hours_before_utc >= 4.0
    AND policy_tier_applied = 'NO_REFUND'
    AND cancelled_at > NOW() - INTERVAL '24 hours';
  ```
  Alert threshold: any row returned → P1 page to Payments on-call.  
  Log pattern: `[POLICY_ENGINE] tier=NO_REFUND hours_before=<N> tz_source=<X>` — flag when
  `tz_source != UTC_NORMALISED`.
- **Mitigation/Recovery:**
  1. Identify all affected cancellations using the detection query above.
  2. For each record where `actual_hours_before_utc >= policy_boundary`, issue a corrective refund
     via `POST /v1/refunds` with `reason=SYSTEM_ERROR` and
     `idempotency_key=cxl_{appointment_id}_tz_correction`.
  3. Send patient notification acknowledging the error and refund ETA (3–5 business days).
  4. Log a `POLICY_CORRECTION` audit event with original and corrected amounts, actor
     `SYSTEM_AUTO_REMEDIATION`, and the incident ticket ID.
  5. Escalate to compliance if more than 50 patients are affected in a single cohort.
- **Prevention:** Normalise all `slot_start` timestamps to UTC at write time; store `timezone_id`
  alongside for display only — never use it for arithmetic. Add a unit test covering every
  supported IANA timezone verifying `compute_policy_tier(slot_start_utc, cancelled_at_utc)`.
  Add a compile-time assertion in the policy engine: `assert slot_start.tzinfo == timezone.utc`.

---

### EC-CXL-002: Provider-Initiated Cancellation — Full Refund Not Issued

- **Failure Mode:** A provider or clinic administrator cancels an appointment via the admin portal.
  The cancellation handler routes through the same policy engine used for patient-initiated
  cancellations. Because the `initiator` field defaults to `PATIENT` when missing from the admin
  portal payload, the engine applies time-based fee logic and issues only a partial refund (or no
  refund) rather than the mandatory 100 % refund required for provider-initiated cancellations.
- **Impact:** Patients charged for a cancellation that was not their fault. Direct financial harm
  of $0–$250 per affected appointment. Serious risk of regulatory violation and breach of the
  clinic's contractual obligations. Likely chargeback if the patient disputes via their card
  issuer, adding a $25–$35 chargeback fee on top of the original amount.
- **Detection:**
  ```sql
  SELECT appointment_id, initiator_type, refund_pct_issued, fee_charged_cents
  FROM cancellation_audit
  WHERE initiator_type IN ('PROVIDER', 'ADMIN', 'CLINIC')
    AND refund_pct_issued < 100
    AND cancelled_at > NOW() - INTERVAL '7 days';
  ```
  Alert threshold: 1 row → P1. Log pattern: `[REFUND] initiator=PROVIDER refund_pct=<N>` where
  N < 100 → fire alert immediately.
- **Mitigation/Recovery:**
  1. Halt further admin-initiated cancellations pending patch deployment if the bug is systemic.
  2. Query all provider-initiated cancellations since the last known-good deploy where
     `refund_pct_issued < 100`.
  3. Issue retroactive top-up refunds for the difference via `POST /v1/refunds/topup`.
  4. Notify affected patients with an apology and refund confirmation including ETA.
  5. Document each correction in the billing audit log with
     `reason=PROVIDER_CANCELLATION_CORRECTION`.
- **Prevention:** Make `initiator` a required, explicitly-typed enum
  `(PATIENT | PROVIDER | ADMIN | SYSTEM)` in the cancellation command schema. Reject any
  cancellation command missing `initiator` at the API gateway. In the policy engine add a
  short-circuit: `if initiator != PATIENT: return FULL_REFUND` before any time-based logic.
  Cover with integration tests asserting `refund_pct == 100` for all non-patient initiator values.

---

### EC-CXL-003: Dispute Over No-Show Classification

- **Failure Mode:** A patient arrives at the clinic but check-in fails silently — either the
  front-desk terminal is offline, the patient used a kiosk that could not reach the API, or a
  network partition prevented the `CHECK_IN` event from persisting. The scheduler marks the
  appointment `NO_SHOW` at T+15 min. The patient is billed a no-show fee ($25–$75) and the slot
  is released. The patient contacts support claiming they attended; there is no corroborating
  audit event.
- **Impact:** Patient billed incorrectly; relationship with clinic damaged. If the provider
  documented a clinical note for the visit (possible in hybrid-offline scenarios), a data
  integrity conflict exists between clinical and billing records. Disputed no-show fees account
  for an estimated 8–15 % of all appointment-support tickets at this scale.
- **Detection:**
  - Monitor: `appointment.status = NO_SHOW` where `ehr_note_created = true` within ±30 min of
    slot time → guaranteed conflict → P1 page.
  - Alert on kiosk/terminal `CHECK_IN_API_FAILURE` events in the 30-min window before no-show
    cutoff.
  - Log pattern: `[CHECK_IN] result=FAILURE appointment_id=<X> terminal_id=<Y>` followed within
    15 min by `[NO_SHOW] appointment_id=<X>` → auto-flag for dispute review queue.
- **Mitigation/Recovery:**
  1. Open a dispute case tied to `appointment_id`; freeze no-show fee collection (do not capture
     payment).
  2. Gather evidence bundle: kiosk/terminal connectivity logs, EHR note timestamps, provider
     schedule adherence records, any physical sign-in sheet scans uploaded by clinic staff.
  3. If corroborating evidence exists (EHR note, terminal failure log), resolve in patient's
     favour: void fee, update status to `ATTENDED_UNCONFIRMED`, log
     `DISPUTE_RESOLVED_PATIENT_FAVOUR`.
  4. If no evidence, escalate to clinical operations manager for manual review within 48 h.
  5. Issue written outcome to patient within 72 h via email and in-app message.
- **Prevention:** Implement offline-capable check-in — kiosks queue `CHECK_IN` events locally
  and sync on reconnect. Before finalising `NO_SHOW`, run a pre-check: if any
  `CHECK_IN_FAILURE` event exists for the clinic in the last 30 min, delay `NO_SHOW` by 10 min
  and alert ops. Store kiosk heartbeat data at 1-min resolution for at least 30 days.

---

### EC-CXL-004: Partial Refund Calculation Error Due to Floating-Point Arithmetic

- **Failure Mode:** The refund engine calculates 50 % of a $199.99 appointment fee using IEEE-754
  double precision: `199.99 * 0.5 = 99.995`. The value is then truncated (floor) to `$99.99`
  instead of being correctly rounded to `$100.00`. The $0.01 shortfall per refund accumulates
  across thousands of transactions into material financial exposure and triggers reconciliation
  failures in the payment processor's settlement reports.
- **Impact:** $0.01 per affected transaction appears trivial, but at 10,000 refunds/month the
  total under-refund is $100/month and generates reconciliation discrepancies requiring hours of
  manual accounting. If the rounding is consistently in the clinic's favour, it may constitute a
  regulatory violation in jurisdictions mandating exact refund of overcharged amounts.
- **Detection:**
  ```sql
  SELECT appointment_id, original_charge_cents, refund_pct, refund_issued_cents,
         ROUND(original_charge_cents * refund_pct / 100.0) AS expected_refund_cents,
         refund_issued_cents
           - ROUND(original_charge_cents * refund_pct / 100.0) AS delta_cents
  FROM refund_audit
  WHERE ABS(refund_issued_cents
              - ROUND(original_charge_cents * refund_pct / 100.0)) > 0
  ORDER BY ABS(delta_cents) DESC;
  ```
  Alert threshold: any `delta_cents ≠ 0` → P2 page. Daily reconciliation job must fail with
  non-zero count.
- **Mitigation/Recovery:**
  1. Run the detection query for the full history of refund records since last known-good release.
  2. For each under-refunded transaction, issue a top-up refund for the delta amount with
     `reason=ROUNDING_CORRECTION`.
  3. For any over-refund (even by $0.01), log but do not reclaim — the patient is not at fault.
  4. Reprocess the settlement reconciliation report for the affected date range.
- **Prevention:** Store all monetary values as integers in the smallest currency unit (cents for
  USD). Never use floating-point for money calculations. Use integer arithmetic exclusively:
  `refund_cents = round(charge_cents * refund_pct_numerator / refund_pct_denominator)` using
  banker's rounding (half-even). Enforce via a `Money` value object that rejects `float` input
  at the type level. Add a property-based test verifying
  `(original_charge_cents - refund_cents) + refund_cents == original_charge_cents` for all
  valid inputs.

---

### EC-CXL-005: Refund Issued to Expired or Closed Payment Card

- **Failure Mode:** A patient's credit card expires between booking and cancellation. The payment
  processor attempts to credit the original payment method on file. Some processors silently
  route the credit to the card issuer regardless; others return `card_expired` or `card_closed`
  errors. In the latter case, the refund fails, the processor deducts the amount from the
  merchant's settlement, and the funds enter limbo: debited from the clinic, never received by
  the patient.
- **Impact:** Patient does not receive refund despite the system showing `REFUND_ISSUED`. Direct
  financial loss of the full appointment fee per occurrence. Regulatory exposure under consumer
  protection laws if not resolved within mandated timeframes (e.g., 7 business days under US
  Reg E equivalents). Estimated 1–3 % of refunds affected when average card tenure is 24–36
  months and booking-to-cancellation windows exceed 3 months.
- **Detection:**
  - Listen for payment processor webhook events: `refund.failed`, `refund.reversed`,
    `card.expired` → map to internal `REFUND_DELIVERY_FAILED` status immediately.
  - Log pattern: `[PAYMENT_GATEWAY] event=refund.failed reason=card_expired appointment_id=<X>`
    → auto-create recovery task.
  - Daily sweep:
    ```sql
    SELECT * FROM refunds
    WHERE status = 'PENDING'
      AND initiated_at < NOW() - INTERVAL '5 days';
    ```
    Any row is anomalous → P2 alert.
- **Mitigation/Recovery:**
  1. On `REFUND_DELIVERY_FAILED` webhook, update refund status and do not re-attempt to the
     same instrument.
  2. Create a `REFUND_RECOVERY_REQUIRED` task visible to the billing operations team.
  3. Outreach to patient within 24 h via in-app message and email: request updated payment
     details or ACH routing information.
  4. If patient provides new instrument, re-issue refund with new `payment_method_id` and
     idempotency key suffix `_recovery_v2`.
  5. If patient is unreachable after 14 days, escalate to accounts payable for cheque or ACH
     origination.
  6. Track all recovery actions in `refund_recovery_log` with timestamps for regulatory evidence.
- **Prevention:** At refund initiation, check card expiry date against `NOW()`. If expired, skip
  the processor attempt and go directly to the recovery workflow. Integrate with the payment
  processor's Account Updater service to passively refresh card metadata monthly. Store
  `card_exp_month` and `card_exp_year` (non-PCI fields) alongside the payment token.

---

### EC-CXL-006: Chargeback Received on a Fully Settled Appointment

- **Failure Mode:** A patient files a chargeback with their card issuer for an appointment that
  was attended and for which the clinic holds a completed `CHECKED_IN` + `COMPLETED` audit trail.
  The payment processor debits the disputed amount from the merchant account and issues a
  chargeback notice with a 7–20 day response window. If the evidence bundle is not submitted in
  time or is insufficient, the chargeback succeeds and the clinic loses the revenue plus a
  $25–$35 chargeback penalty.
- **Impact:** Revenue loss per instance equal to the appointment fee plus the chargeback penalty.
  Chargeback rate above 0.1 % (Visa threshold) or 0.65 % (Mastercard Early Warning) triggers
  enhanced monitoring programs and potential account termination — existential risk if rates
  spike. Fraudulent chargebacks on completed appointments damage provider-clinic economics.
- **Detection:**
  - Webhook: `dispute.created` from payment processor → immediately create `CHARGEBACK_CASE`
    record and page billing on-call within 5 min.
  - Dashboard metric: `chargeback_rate = disputes_opened_mtd / total_successful_charges_mtd` —
    alert at > 0.08 % (before Visa threshold).
- **Mitigation/Recovery:**
  1. On `dispute.created` webhook, auto-generate evidence bundle: appointment confirmation
     record, check-in timestamp, provider note existence flag (not note content — preserve PHI),
     booking IP address, patient-signed consent acknowledgement, prior communication records.
  2. Submit evidence via processor API within 48 h (well before deadline to avoid last-minute
     failures).
  3. Tag `appointment_id` as `CHARGEBACK_UNDER_REVIEW` — block any concurrent refund attempts
     to prevent double-crediting.
  4. If chargeback is won: update status to `CHARGEBACK_WON`, restore settlement journal entry.
  5. If lost: record `CHARGEBACK_LOST`, apply financial journal entry, review for fraud signal,
     and block patient account if fraud is confirmed.
- **Prevention:** Collect explicit digital consent at booking with timestamp and IP logged. Send
  booking confirmation and post-visit summary to establish a documented interaction trail. Use
  3D Secure (Visa Secure / Mastercard Identity Check) for card-not-present transactions to shift
  liability to the card issuer. Maintain a chargeback response playbook with pre-built evidence
  templates per dispute reason code (e.g., Visa reason code 13.1 vs. 10.4).

---

### EC-CXL-007: Waitlist Promotion Sent After Cancellation Notification Already Dispatched

- **Failure Mode:** A patient cancels appointment A, triggering two downstream events nearly
  simultaneously: (1) a `CANCELLATION_CONFIRMED` notification to the cancelling patient, and
  (2) a `SLOT_AVAILABLE` event to the waitlist service. The waitlist service promotes the top-
  ranked waitlisted patient and sends them a `SLOT_OFFERED` notification. Due to eventual
  consistency lag, a race condition briefly allows the slot to appear available to both parties.
  In extreme cases, both the original patient (who may receive a re-confirmation via a stale
  push) and the waitlisted patient believe they hold the slot.
- **Impact:** Double-booking scenario affecting 2 patients and 1 provider. One patient must be
  turned away or rescheduled, causing significant distress. Patient trust score impact:
  −20 to −35 NPS points for affected patients. Operational cost of manual rescheduling and
  apology workflows per incident.
- **Detection:**
  ```sql
  -- Double-booking detector: > 1 active appointment per slot
  SELECT slot_id, COUNT(DISTINCT appointment_id) AS active_count
  FROM appointments
  WHERE status IN ('CONFIRMED', 'PENDING_CONFIRMATION')
  GROUP BY slot_id
  HAVING COUNT(DISTINCT appointment_id) > 1;
  ```
  Any result → P1 double-booking alert. Run every 30 s via a consistency monitor job.  
  Log pattern: `[WAITLIST] slot_offered appointment_id=<NEW>` within 500 ms of
  `[SLOT] status=AVAILABLE slot_id=<X>` for the same slot → flag race condition.
- **Mitigation/Recovery:**
  1. Freeze the slot immediately — prevent further reservations.
  2. Determine which booking was created first by `created_at` timestamp.
  3. Cancel the later (erroneous) booking, issue a full refund if payment was captured, and send
     a high-priority apology notification with an immediate rebook offer.
  4. Confirm the earlier (correct) booking to that patient.
- **Prevention:** Enforce a database-level unique constraint on `(slot_id, status)` where status
  is in the active set `{RESERVED, CONFIRMED}`. Waitlist promotion must acquire the slot via
  the same atomic reservation path used for regular booking. Enforce a minimum 1-s delay between
  slot-release event publication and waitlist-promotion trigger, allowing the cancellation
  notification pipeline to complete first. Use a `SLOT_LOCK` table row with TTL during the
  promotion window.

---

### EC-CXL-008: Chain Cancellation When Provider Leaves Clinic

- **Failure Mode:** A provider departs the clinic (resignation, contract end, or emergency). An
  administrator triggers a bulk cancellation of all future appointments for that provider —
  potentially 200–800 appointments across 4–8 weeks. The bulk job issues a high-velocity stream
  of cancellation events that overwhelms the notification service (SMS/email provider rate
  limits), the refund processor (batch API rate limits), and the waitlist service (simultaneous
  promotions for many newly freed slots). Some notifications are dropped, some refunds fail
  silently, and waitlist promotion logic generates conflicting slot assignments.
- **Impact:** Up to 800 patients receive no cancellation notice or a significantly delayed
  notice; some arrive at the clinic unaware. Refund failures leave patients out of pocket.
  Compliance risk: bulk PHI-touching operations without a complete audit trail. Estimated
  operational recovery time: 4–8 hours.
- **Detection:**
  - Alert: `cancellations_per_minute > 20` for a single `provider_id` → trigger bulk-cancellation
    circuit breaker and P1 page.
  - Monitor: `refund_failure_rate > 5 %` or `notification_delivery_rate < 90 %` in a 5-min
    rolling window → P2 alert.
  - Log: `[BULK_CANCEL] provider_id=<X> total=<N> initiated_by=<ADMIN_ID>` — require human
    acknowledgement for N > 50 before the job proceeds.
- **Mitigation/Recovery:**
  1. Pause the bulk job at the circuit breaker threshold; resume at a controlled rate of
     ≤ 10 cancellations/min.
  2. For notifications that failed during the burst, replay from the dead-letter queue in
     batches of 50 with a 2-s inter-batch delay.
  3. Run the refund reconciliation sweep for the affected `provider_id` — identify any
     `refund_status = PENDING` records older than 10 min and resubmit.
  4. Activate a clinic front-desk alert: post a notice in the clinic portal listing all affected
     appointment dates and times so staff can intercept walk-in patients.
  5. Generate a patient outreach list for any patient where notification delivery is unconfirmed
     after 30 min; assign to the manual outreach queue.
- **Prevention:** Implement a bulk-cancellation workflow with mandatory human approval for
  N > 25 appointments, a rate-limited job queue (max 10/min), idempotent per-appointment
  cancellation records keyed by `(appointment_id, bulk_job_id)`, and a real-time progress
  dashboard. Make refund submission asynchronous with per-item retry logic isolated from the
  cancellation state machine.

---

### EC-CXL-009: Administrative Force-Cancel During Active Consultation

- **Failure Mode:** A clinic administrator mistakenly (or as a cleanup action) force-cancels an
  appointment while the provider is actively mid-consultation with the patient (state
  `IN_CONSULTATION`). The cancellation transitions the appointment to `CANCELLED`, releases the
  slot for new bookings, triggers a refund, and sends the patient a cancellation notification —
  all while the patient is physically present in the exam room. The provider's EHR session may
  become orphaned or linked to a now-cancelled appointment record.
- **Impact:** Clinical data integrity risk: the provider's notes and orders may not save correctly
  to a cancelled appointment record. The patient receives a confusing cancellation SMS mid-visit.
  The slot is released and potentially booked by another patient, creating a physical room
  conflict. Potential HIPAA audit finding if clinical notes are orphaned without a valid
  appointment anchor.
- **Detection:**
  - Alert: `appointment_status_changed_to = 'CANCELLED' AND previous_status = 'IN_CONSULTATION'`
    → immediate P1 page to clinical ops.
  - Log pattern: `[APPOINTMENT] state_transition from=IN_CONSULTATION to=CANCELLED actor=ADMIN`
    — this is never a valid transition in normal operations.
- **Mitigation/Recovery:**
  1. This state transition must be blocked at the application layer as the primary fix.
  2. If the transition has already occurred: immediately alert both the provider (via in-app push)
     and the front desk via a clinic portal banner.
  3. Revert the appointment to `IN_CONSULTATION` via an admin override command; document the
     rollback in the audit log with the incident ticket ID.
  4. Cancel the erroneous refund if not yet captured; suppress the cancellation notification if
     not yet delivered.
  5. After consultation completes, allow the normal `IN_CONSULTATION → COMPLETED` transition.
  6. File an incident report and review whether the admin action was a UI error or a process gap.
- **Prevention:** Add a state machine guard: `IN_CONSULTATION` is a protected state from which
  only `COMPLETE_VISIT` and `EMERGENCY_ABORT` commands are valid — generic `CANCEL` is rejected
  by the state machine with a `4xx` error. Require dual-approval (admin + clinical supervisor)
  for any force-cancel of an appointment in `IN_CONSULTATION` or `CHECKED_IN`. Display a
  prominent warning modal in the admin portal when an appointment is in these protected states.

---

### EC-CXL-010: Cancellation Requested While Payment Capture Is In-Flight

- **Failure Mode:** A patient requests cancellation at the exact moment the billing service is
  executing a delayed payment capture (common with pre-authorisation patterns where capture
  occurs T−2 h before the appointment). The cancellation handler reads
  `payment_status = AUTHORISED` (pre-capture) and concludes no refund is needed — it voids the
  authorisation. Simultaneously, the capture job reads `appointment_status = CONFIRMED`
  (pre-cancellation) and executes the capture. The two operations race: the void may fail if
  the capture lands first, or the capture succeeds and no refund is initiated because the
  cancellation handler believed the auth was voided.
- **Impact:** Patient is charged the full appointment fee ($50–$500) despite successfully
  cancelling. No refund workflow is triggered automatically. This is a silent revenue leakage
  issue that may go undetected for days until the patient notices the charge on their statement
  and disputes it. Chargebacks in this scenario are very likely to succeed against the merchant.
- **Detection:**
  ```sql
  SELECT appointment_id, payment_status, appointment_status, captured_at, cancelled_at
  FROM appointments a
  JOIN payments p USING (appointment_id)
  WHERE a.appointment_status = 'CANCELLED'
    AND p.payment_status = 'CAPTURED'
    AND p.refund_status IS NULL
    AND a.cancelled_at > NOW() - INTERVAL '1 hour';
  ```
  Alert threshold: any row → P1 page. Run this sweep every 5 min.
- **Mitigation/Recovery:**
  1. On detection, immediately create a `REFUND_REQUIRED` record for the captured amount with
     `reason=RACE_CONDITION_CAPTURE_AFTER_CANCEL`.
  2. Issue a full refund via the payment processor API. If within the full-refund policy window,
     issue 100 %; otherwise apply standard policy but document the anomaly in the audit log.
  3. Notify patient: "Your cancellation was processed and a refund of $X will appear in
     3–5 business days."
  4. Audit the race window: check all appointments in the same time slice for the same pattern.
- **Prevention:** The capture job must perform a `SELECT FOR UPDATE` on the `payments` row and
  read `appointment_status` at the time of capture. If status is `CANCELLING` or `CANCELLED`,
  abort the capture and void the authorisation. Introduce a `CANCELLING` intermediate state that
  the cancellation handler sets atomically before triggering any downstream actions — this state
  blocks the capture job from proceeding. Use a distributed lock (Redis `SETNX` with 30-s TTL)
  keyed on `appointment_id` during the capture-or-cancel decision window.

---

## Summary Reference Table

| Code | Name | Severity | Primary Risk | Owner |
|------|------|----------|-------------|-------|
| EC-CXL-001 | Timezone-based wrong policy tier | P1 | Financial + Compliance | Payments |
| EC-CXL-002 | Provider cancel — partial refund issued | P1 | Financial + Legal | Payments |
| EC-CXL-003 | Disputed no-show classification | P2 | Patient Trust | Scheduling |
| EC-CXL-004 | Floating-point refund rounding error | P2 | Financial + Reconciliation | Payments |
| EC-CXL-005 | Refund to expired/closed card | P1 | Financial + Regulatory | Payments |
| EC-CXL-006 | Chargeback on completed appointment | P1 | Revenue + Processor Risk | Payments |
| EC-CXL-007 | Waitlist race condition double-booking | P1 | Patient Trust + Ops | Scheduling |
| EC-CXL-008 | Chain cancellation — provider departure | P1 | Ops + Compliance | Platform |
| EC-CXL-009 | Force-cancel during active consultation | P1 | Clinical + Data Integrity | Clinical Ops |
| EC-CXL-010 | Cancellation–capture race condition | P1 | Financial (silent) | Payments |

---

## Operational SLAs

| Metric | Target |
|--------|--------|
| Refund initiation after eligible cancellation | ≤ 5 minutes |
| Chargeback evidence submission | ≤ 48 hours of dispute receipt |
| No-show dispute resolution | ≤ 72 hours of patient contact |
| Bulk cancellation notification delivery | ≤ 30 minutes for all affected patients |
| Race condition detection and auto-remediation | ≤ 5 minutes |
