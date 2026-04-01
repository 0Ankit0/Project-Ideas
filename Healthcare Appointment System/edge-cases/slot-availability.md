# Slot Availability — Edge Cases

**Domain:** Slot Availability  
**Edge Case IDs:** EC-SLOT-001 through EC-SLOT-010  
**Owner:** Scheduling Platform Team  
**Related Alerts:** `slot.conflict.rate.high`, `slot.cache.staleness`, `slot.hold.expired.mid.payment`, `dst.ambiguous.slot.unreviewed`

---

## Governing Principles
All edge cases in this file are governed by cross-cutting principles **P-01** (Idempotency), **P-03** (Audit Trail), **P-07** (Retry Safety), **P-09** (Observability-First), **P-11** (Timezone Canonicalization), and **P-12** (Eventual Consistency Contracts). See `edge-cases/README.md` for full principle definitions.

---

### EC-SLOT-001: Concurrent Booking Race Condition

- **Failure Mode:** Two or more patients submit `POST /bookings` for the same provider slot within the same millisecond window. Both requests pass the initial availability check (which reads from the cache or a non-locking SELECT), and both proceed to the reservation step. Without a database-level exclusive lock, both transactions commit, creating two confirmed appointments for a single slot — a hard double-booking.

- **Impact:** Provider can only serve one patient; the second patient travels unnecessarily, potentially missing work or arranging dependent care. The clinic faces a trust and safety incident, a mandatory rescheduling task, and possible complaint escalation. In a high-traffic specialty (e.g., oncology second opinion), conflict rate as low as 0.5% over a peak hour translates to ~15 double-bookings per week. Average cost per incident (patient outreach + re-scheduling labor + goodwill credit) is estimated at $40–$80.

- **Detection:**
  - **Alert:** `slot.conflict.rate.high` — fires when `rate(edge_case.triggered{id="EC-SLOT-001"}[5m]) > 0.02` (2% of booking attempts)
  - **Log pattern:** `level=ERROR edge_case_id=EC-SLOT-001 msg="slot reservation conflict" slot_id=<id> winning_booking_id=<id> losing_booking_id=<id>`
  - **DB query for manual inspection:** `SELECT slot_id, count(*) FROM appointments WHERE status NOT IN ('CANCELLED','NO_SHOW') GROUP BY slot_id HAVING count(*) > slot_capacity;`

- **Mitigation/Recovery:**
  1. The losing `INSERT` is rejected by the unique partial index `uidx_slot_one_active_booking(slot_id) WHERE status NOT IN ('CANCELLED','NO_SHOW')`. The reservation transaction rolls back.
  2. Return `409 SLOT_ALREADY_BOOKED` with `{ "alternatives": [...top_3_available_slots...] }` to the losing request.
  3. Emit `edge_case.triggered{id="EC-SLOT-001"}` counter metric.
  4. If the unique index constraint is missing (legacy migration gap), the reconciliation job `jobs/slot-conflict-sweep` detects the double-booking within 5 minutes, cancels the later-created appointment, initiates a refund saga for the affected patient, and creates an `OPS_INCIDENT` record for on-call review.
  5. On-call engineer confirms reconciliation completed and closes the ops incident with a postmortem link.

- **Prevention:**
  - Create a unique partial index on `appointments(slot_id)` filtered to non-cancelled, non-no-show statuses. This makes the race a database-enforced constraint, not an application-layer check.
  - Use `INSERT INTO appointments ... ON CONFLICT ON CONSTRAINT uidx_slot_one_active_booking DO NOTHING RETURNING id` and treat a null return as a conflict.
  - Add an optimistic-lock `slot_version` column to `slots`; increment it on reservation. Reservation command must supply the version seen at read time; a mismatch returns `409`.
  - Load-test with 1,000 concurrent booking requests per slot before every major release.

---

### EC-SLOT-002: Provider Schedule Update Mid-Checkout

- **Failure Mode:** A provider (or clinic admin) modifies or cancels their schedule — adds emergency leave, closes a clinic location, or changes a shift end time — while a patient is in an active checkout flow (slot selected, payment form open). The slot that was valid when selected becomes invalid before the patient submits payment. If the system does not re-validate at booking commit time, it confirms an appointment for a slot the provider is no longer available for.

- **Impact:** Provider does not appear for the appointment; patient experiences a failed visit. The clinic must make same-day outreach, offer an emergency rebook, and issue a goodwill credit. Provider-initiated cancellations at short notice violate SLA and trigger penalty clauses in enterprise contracts (typically $25–$100 per incident). Regulatory impact: if the patient had an urgent clinical need, delayed care is a reportable event.

- **Detection:**
  - **Alert:** `slot.schedule.mutated.mid.checkout` — detects when `schedule_mutation_event.timestamp` overlaps with an active checkout session for the same `provider_id`.
  - **Log pattern:** `level=WARN edge_case_id=EC-SLOT-002 msg="schedule updated during active checkout" provider_id=<id> slot_id=<id> checkout_session_id=<id>`
  - **Metric:** `edge_case.triggered{id="EC-SLOT-002"}` counter.

- **Mitigation/Recovery:**
  1. At `POST /bookings` commit time, re-validate the slot against the live schedule (not the cache) using a SELECT FOR SHARE on the `slots` table joined to `provider_schedules`.
  2. If the slot is no longer valid, return `409 SLOT_INVALIDATED` with the reason (`PROVIDER_UNAVAILABLE`, `CLINIC_CLOSED`, etc.) and top-3 alternatives.
  3. If payment was already captured before the conflict was detected (timing edge), immediately trigger the cancellation–refund saga with `reason=PROVIDER_INITIATED` and notify the patient via all consented channels with a priority flag.
  4. Move the affected appointment to `REBOOK_REQUIRED` and assign an outreach task to the clinic coordinator queue.
  5. Escalate to ops incident if the appointment is within 24 hours of the visit time.

- **Prevention:**
  - Implement a `schedule_mutation_lock` advisory lock that is acquired during schedule updates and checked during the booking commit transaction. Block concurrent schedule mutations and bookings for the same `(provider_id, slot_start)` pair.
  - Publish `ScheduleUpdated` domain events that invalidate in-progress checkout sessions via WebSocket push or short-poll; UI shows "This slot is no longer available" in real time.
  - Set slot hold TTL (see EC-SLOT-009) short enough that stale checkout sessions auto-expire before the schedule change window closes.

---

### EC-SLOT-003: Stale Cache Serving Booked Slots

- **Failure Mode:** The availability cache (Redis) contains a slot entry marked `AVAILABLE` after it has been reserved in the database. Cache invalidation fires asynchronously via a domain event, but the invalidation message is delayed, dropped, or delivered out of order. A patient queries availability, receives the stale `AVAILABLE` entry, selects it, and advances to checkout — only to fail at the booking commit step with a conflict error after already investing time in form-filling.

- **Impact:** Booking funnel abandonment is the primary impact. When patients encounter a "slot no longer available" error at the final step, abandonment rates in healthcare booking flows are 40–60% — far higher than e-commerce because the perceived cost of re-searching is higher. At scale, 1% stale-cache rate on a platform booking 10,000 appointments/day causes ~100 abandonment events daily, translating to ~$3,000–$8,000/day in deferred or lost revenue.

- **Detection:**
  - **Alert:** `slot.cache.staleness` — fires when `max(slot_cache_age_seconds) > 60`.
  - **Log pattern:** `level=WARN edge_case_id=EC-SLOT-003 msg="cache miss promoted stale available entry" slot_id=<id> cache_age_ms=<n>`.
  - **Metric:** `slot_cache_stale_hit_total` counter; ratio `stale_hits / total_availability_reads` should be < 0.1%.

- **Mitigation/Recovery:**
  1. On cache miss or stale detection, fall through to the primary database read and re-populate the cache entry with a 10-second TTL.
  2. On every availability API response, include the `X-Data-Freshness-Utc` header (see principle P-12) so clients can display a "last updated" indicator.
  3. If the booking commit fails due to a stale-cache conflict, return `409 SLOT_ALREADY_BOOKED` and proactively warm the correct availability data for adjacent slots in the patient's search context so the alternatives response is accurate.
  4. Run `ops/cache-consistency-check` hourly: compare Redis slot states against DB slot states; publish discrepancy count to `slot_cache_discrepancy_total` metric.

- **Prevention:**
  - Implement write-through caching on the slot reservation path: the reservation transaction itself updates the cache entry to `RESERVED` within the same DB transaction using a Lua script that conditionally updates Redis only if the transaction commits (via a transactional outbox pattern).
  - Set a maximum TTL of 30 seconds on all availability cache entries as a safety net regardless of invalidation events.
  - Use Redis `WATCH`/`MULTI`/`EXEC` to detect cache entry version mismatches and force a DB read-through on conflict.

---

### EC-SLOT-004: Timezone / DST Transition Errors

- **Failure Mode:** A slot is created or displayed using the wrong local time because of incorrect timezone offset application. Common sub-cases: (a) system applies a static UTC offset instead of the IANA-resolved offset (which changes at DST boundaries), (b) slot generation uses the server's local timezone instead of the clinic's declared `timezone_id`, (c) a patient in one timezone books a provider in a different timezone and the UI renders the provider's local time without timezone disambiguation.

- **Impact:** Patients arrive at the wrong time — either an hour early (wasted trip, no disruption to provider) or an hour late (missed appointment, no-show fee applied incorrectly, provider slot wasted). For chronic-care patients with transport dependencies, arriving an hour late at a specialist visit can result in a multi-week rescheduling delay. Regulatory risk: if a medication administration appointment is missed due to a system clock error, it is a reportable event.

- **Detection:**
  - **Alert:** `slot.timezone.mismatch` — fires when `count(appointments WHERE ABS(slot_start_utc - expected_utc_from_local) > 3600) > 0` after slot generation runs.
  - **Log pattern:** `level=ERROR edge_case_id=EC-SLOT-004 msg="timezone offset mismatch" slot_id=<id> clinic_tz=<tz> computed_offset=<n> expected_offset=<n>`.
  - **Monitoring:** Post-generation slot audit job compares stored `slot_start_utc` against the result of `convert_tz(slot_start_local, clinic_timezone_id)` using the authoritative IANA database.

- **Mitigation/Recovery:**
  1. On detection, immediately flag affected slots as `TIMEZONE_REVIEW_REQUIRED` to prevent new bookings.
  2. Notify clinic coordinators with the list of affected slots and the correct UTC times.
  3. For already-booked appointments, determine whether the patient's intended local time or the stored UTC time is correct (requires human review), then update accordingly and send a reschedule notification.
  4. Re-run slot generation for affected date ranges after the timezone configuration is corrected.

- **Prevention:**
  - Store `timezone_id` (IANA name, e.g., `America/New_York`) on every `clinic` and `provider_schedule` record. Never store raw UTC offsets.
  - Use a battle-tested IANA timezone library (e.g., `date-fns-tz`, `java.time.ZoneId`, `pytz`) for all datetime arithmetic. Pin the IANA timezone database version and update it at least quarterly.
  - Generate slots using the clinic's declared `timezone_id` and validate that `slot_start_utc = ZonedDateTime.of(slot_start_local, clinic_tz).toInstant()`. Automated tests cover DST boundary dates for all supported timezone regions.

---

### EC-SLOT-005: Slot Generation Failure for Recurring Templates

- **Failure Mode:** The scheduled job that materializes concrete slot records from recurring provider schedule templates fails silently or partially. The job may throw an unhandled exception on a specific template (e.g., an invalid recurrence rule, a null clinic reference, an expired provider license), log the error, skip the template, and continue — leaving that provider's future calendar empty. Patients see no available slots; the provider's schedule appears to be fully booked when it is actually ungenerated.

- **Impact:** Provider availability appears falsely full for the affected period (days to weeks ahead). Patients cannot book and may seek care elsewhere. Revenue impact: a specialist averaging 8 appointments/day × $150 average booking value = $1,200/day of prevented bookings per affected provider. If the failure affects a high-demand provider during open enrollment season, the downstream no-booking window compounds with rebook demand.

- **Detection:**
  - **Alert:** `slot.generation.failure` — fires when `count(slot_generation_job_errors) > 0` in any job run, or when `count(generated_slots_per_run) = 0` for a run window that previously generated > 0 slots.
  - **Log pattern:** `level=ERROR edge_case_id=EC-SLOT-005 msg="slot generation failed for template" template_id=<id> error=<message>`.
  - **Anomaly alert:** `slot.generation.provider.gap` — fires when a provider who had slots last week has zero slots generated for any day 7–14 days ahead.

- **Mitigation/Recovery:**
  1. On job failure, emit `edge_case.triggered{id="EC-SLOT-005"}` and write a `SLOT_GENERATION_FAILURE` ops task with the failing template ID and error details.
  2. On-call engineer diagnoses the root cause (invalid template, missing FK, license expiry) and either corrects the template data or triggers a manual re-run scoped to the affected `provider_id`.
  3. Run `ops/slot-gap-detector` to identify any providers with zero slots in the next 14 days who have an active schedule template; surface in the ops dashboard.
  4. Notify clinic coordinators for affected providers so they can manually handle booking requests via phone.

- **Prevention:**
  - Wrap each template's generation logic in an isolated transaction with structured exception handling; log the failure with full context and continue to the next template, but record the failure count in the job result.
  - Implement a mandatory post-job health check: after every slot generation run, assert that every provider with an active schedule template has at least N slots in the next 14 days. Fail the job with a non-zero exit code if the assertion fails.
  - Add CI tests that exercise slot generation with malformed templates, null FK references, and timezone boundary dates.

---

### EC-SLOT-006: Buffer Time Violation Between Appointments

- **Failure Mode:** A new appointment is booked in a slot that does not respect the provider's configured post-appointment buffer time (e.g., 15 minutes for documentation and room turnover). This happens when: (a) buffer time is not subtracted from the effective slot end time during generation, (b) a provider's buffer time setting is changed after slots are already generated, or (c) slot generation calculates buffers but the booking UI renders the raw slot end time, allowing selection of overlapping slots.

- **Impact:** Provider is double-scheduled in terms of time, even if not in terms of slot count. Appointments run over, cascading delays accumulate through the day, and the last patient may wait 30–60 minutes beyond their scheduled time. Provider burnout and patient satisfaction scores degrade. For clinical procedures requiring sterilization (e.g., minor surgery), a buffer violation is a patient safety issue.

- **Detection:**
  - **Alert:** `slot.buffer.violation` — fires when a booking is committed where `new_appointment.start_time < previous_appointment.end_time + provider.buffer_minutes` for the same provider.
  - **Log pattern:** `level=WARN edge_case_id=EC-SLOT-006 msg="buffer time violation detected" appointment_id=<id> provider_id=<id> gap_minutes=<n> required_buffer=<n>`.

- **Mitigation/Recovery:**
  1. Reject the booking at commit time with `409 BUFFER_TIME_VIOLATION` and suggest the next available slot that respects the buffer.
  2. For violations already committed (e.g., from a misconfigured slot generation run), run `ops/buffer-violation-detector` to identify affected appointments and flag them for provider review.
  3. Clinic coordinator contacts affected patients to offer adjusted times or advance the preceding appointment.

- **Prevention:**
  - Encode buffer time into slot records at generation time: `effective_end_time = start_time + duration + buffer_minutes`. Bookings are only permitted when `next_slot.start_time >= previous_slot.effective_end_time`.
  - When a provider's buffer time is updated, invalidate and regenerate all future slots for that provider. Trigger rebook-required notifications for any appointments now in violation.
  - Add a database CHECK constraint: `slot_start >= (SELECT MAX(effective_end_time) FROM slots WHERE provider_id = NEW.provider_id AND slot_start < NEW.slot_start)`.

---

### EC-SLOT-007: Blackout Date Not Applied to Generated Slots

- **Failure Mode:** A clinic or health system administrator defines a blackout date (public holiday, facility maintenance, accreditation inspection) in the `blackout_dates` table. The slot generation job processes the recurring schedule template but does not join against `blackout_dates`, materializing slots for the blacked-out date. Patients can book these slots. When the blackout date arrives, the provider is not present and all booked appointments must be cancelled with same-day notice.

- **Impact:** Same-day or next-day mass cancellation is the worst-case patient experience outcome. Operational cost: each emergency cancellation requires a manual outreach call (~10 minutes) plus a rebook offer. A single blacked-out day for a clinic with 40 daily appointments costs ~6.7 hours of coordinator labor plus goodwill credits. Reputation impact is high, particularly if the blackout is a public holiday the patient reasonably expected the clinic to observe.

- **Detection:**
  - **Alert:** `slot.blackout.date.violation` — fires when `count(slots WHERE slot_date IN (SELECT date FROM blackout_dates WHERE clinic_id = slots.clinic_id) AND status = 'AVAILABLE') > 0`.
  - **Log pattern:** `level=ERROR edge_case_id=EC-SLOT-007 msg="slots generated for blackout date" clinic_id=<id> blackout_date=<date> slot_count=<n>`.
  - **Scheduled check:** Daily at 02:00 UTC, a sweep job queries for any slots in the next 30 days that conflict with blackout dates and alerts immediately.

- **Mitigation/Recovery:**
  1. The daily sweep job marks violating slots as `BLOCKED` (preventing new bookings) and emits `edge_case.triggered{id="EC-SLOT-007"}`.
  2. For already-booked appointments, initiate provider-initiated cancellation sagas with `reason=FACILITY_CLOSURE`, trigger full refunds, and send priority rebook notifications.
  3. On-call engineer confirms the blackout date is correctly configured and re-runs slot generation for the affected date range (blackout dates will now be excluded).

- **Prevention:**
  - In slot generation SQL, add an explicit LEFT JOIN to `blackout_dates` and filter out any `slot_date` that has a matching blackout record for the clinic or health system.
  - Add a post-generation assertion: `SELECT count(*) FROM generated_slots WHERE slot_date IN (SELECT date FROM blackout_dates) MUST = 0`.
  - Add blackout date management to the clinic admin UI with a real-time preview showing which existing slots will be removed by a new blackout entry.

---

### EC-SLOT-008: Capacity Limit Exceeded for Group Appointment

- **Failure Mode:** A group appointment slot (e.g., group therapy, prenatal class, wellness workshop) has a defined `max_capacity` (e.g., 12 participants). Concurrent bookings race past the capacity check because the check is done in application code with a non-atomic read-then-write, allowing more participants to be enrolled than the room or provider can handle.

- **Impact:** Clinical and physical safety risk for group therapy (therapist-to-patient ratio) and group procedure sessions (equipment constraints). Administrative burden: identifying which patients to turn away after over-enrollment is ethically complex and legally sensitive. Revenue impact is secondary to the safety and liability exposure.

- **Detection:**
  - **Alert:** `slot.capacity.exceeded` — fires when `count(appointments WHERE slot_id = X AND status NOT IN ('CANCELLED','NO_SHOW')) > (SELECT max_capacity FROM slots WHERE id = X)`.
  - **Log pattern:** `level=ERROR edge_case_id=EC-SLOT-008 msg="group slot capacity exceeded" slot_id=<id> enrolled=<n> max_capacity=<n>`.

- **Mitigation/Recovery:**
  1. Detect over-enrollment via the capacity sweep job (runs every 5 minutes). Page the clinic coordinator immediately.
  2. The clinic coordinator reviews the enrollment list and determines which patient(s) to contact for re-scheduling (typically LIFO — last enrolled is first moved, unless clinical priority overrides).
  3. Issue refunds for any involuntarily re-scheduled patients and offer priority rebooking.
  4. Emit `edge_case.triggered{id="EC-SLOT-008"}` and create an ops incident.

- **Prevention:**
  - Enforce capacity as a database-level constraint using a `FOR UPDATE SKIP LOCKED` select on the capacity counter row, or use a serializable transaction that counts current enrollment before inserting.
  - Alternatively, maintain a `current_enrollment` counter column on `slots` and use a `CHECK CONSTRAINT (current_enrollment <= max_capacity)` with an atomic `UPDATE slots SET current_enrollment = current_enrollment + 1 WHERE id = ? AND current_enrollment < max_capacity` that returns 0 rows on overflow.
  - For high-traffic group slots, use a distributed semaphore (Redis `SETNX` with TTL) as a pre-filter before hitting the database.

---

### EC-SLOT-009: Slot Hold Expiry During Payment Processing

- **Failure Mode:** When a patient selects a slot and enters the payment flow, the system places a temporary hold on the slot (`status = RESERVED`, `hold_expires_at = now() + 10 minutes`). If the payment flow takes longer than the hold TTL — due to 3D-Secure authentication delays, slow network, or the patient stepping away — the hold expires and a background job returns the slot to `AVAILABLE`. A second patient then books the slot. When the first patient completes payment, their booking attempt fails with a slot conflict despite their payment being authorized.

- **Impact:** Patient has an authorized payment hold on their card but no appointment. If the system does not immediately void the authorization, the hold remains for 3–7 days depending on card network. Patient frustration is high. Revenue: the second booking is retained, but the first patient's trust is severely damaged. If the authorization is not voided, there is a potential card-network dispute.

- **Detection:**
  - **Alert:** `slot.hold.expired.mid.payment` — fires when `count(edge_case.triggered{id="EC-SLOT-009"}) > 10` in any 10-minute window.
  - **Log pattern:** `level=WARN edge_case_id=EC-SLOT-009 msg="slot hold expired during active payment session" slot_id=<id> session_id=<id> hold_expired_at=<ts>`.
  - **Metric:** `slot_hold_expiry_during_payment_total` counter.

- **Mitigation/Recovery:**
  1. When the first patient's booking commit fails with `SLOT_ALREADY_BOOKED` after payment capture, immediately trigger a void/refund saga for the captured amount.
  2. Return a specific error code `SLOT_EXPIRED_REBOOK_REQUIRED` (distinct from `SLOT_ALREADY_BOOKED`) with the top-3 alternatives populated.
  3. Send the patient an in-app and email notification explaining the situation and offering the alternatives with one-tap booking (pre-populated payment method).
  4. Log the authorization void in the payment ledger with `reason=SLOT_HOLD_EXPIRY`.

- **Prevention:**
  - Extend the hold TTL to 20 minutes (covering the 95th percentile of 3DS completion time, measured from payment analytics).
  - Implement a hold-renewal endpoint: the payment UI pings `POST /slots/{id}/hold/renew` every 5 minutes during active checkout; the server extends the hold if the slot is still reserved for this session.
  - Monitor active payment sessions and proactively alert the patient at T-2 minutes before expiry: "Your slot will be released in 2 minutes. Complete payment or select a new slot."

---

### EC-SLOT-010: DST-Ambiguous Time Slots (Clock Fallback Creates Duplicate Hour)

- **Failure Mode:** During the "fall back" DST transition (clocks roll back 1 hour at 02:00 → 01:00), local times in the repeated hour (e.g., 01:00–01:59 local) occur twice. If the slot generation job materializes slots using local time without explicitly resolving DST ambiguity, it may generate two slot records with the same local display time but different UTC times, or it may fail to generate the second occurrence entirely. Patients booking in this window may see confusing duplicate time labels, or providers may be double-scheduled.

- **Impact:** In the worst case, a provider ends up with two patients scheduled for what appears (in local time) to be the same slot. This is a subset of EC-SLOT-001 but with a root cause in time arithmetic rather than concurrency. The failure is silent — the UI shows a valid-looking time and neither patient nor provider has any indication of the conflict until the appointment day. Regulatory impact: if medication administration appointments are involved, a timing confusion is a patient safety event.

- **Detection:**
  - **Alert:** `dst.ambiguous.slot.unreviewed` — fires at 23:00 local clinic time on the night of the DST transition when `count(slots WHERE dst_ambiguous = true AND reviewed = false) > 0`.
  - **Log pattern:** `level=WARN edge_case_id=EC-SLOT-010 msg="DST-ambiguous slot generated" slot_id=<id> local_time=<t> utc_time_a=<t1> utc_time_b=<t2>`.
  - **Scheduled pre-transition check:** 48 hours before every DST transition date (enumerated for all supported clinic timezones), run a check for affected slots.

- **Mitigation/Recovery:**
  1. Flag all slots in the ambiguous hour with `dst_ambiguous = true` before they are opened for booking.
  2. Block booking on `dst_ambiguous = true` slots until a clinic coordinator has reviewed and confirmed the correct UTC interpretation (i.e., "pre-transition" or "post-transition" occurrence).
  3. Send a task to the clinic coordinator queue: "DST transition on [date]. Please review [N] ambiguous slots for [provider]."
  4. After review, set `dst_ambiguous = false` and `dst_resolution = PRE|POST` on each slot. The slot is then opened for booking.
  5. If a double-booking was already created before detection, follow EC-SLOT-001 mitigation steps.

- **Prevention:**
  - During slot generation, use the IANA timezone library's `fold` attribute (Python) or `ZoneOffset` disambiguation (Java `ZoneId`) to explicitly select either the pre-transition or post-transition interpretation for each ambiguous time. Store the `dst_fold` value on the slot record.
  - Generate a DST transition calendar for all supported clinic timezones for the next 12 months as part of the annual infrastructure review. Pre-configure the resolution policy (e.g., "for all ambiguous slots, use the post-transition UTC time") in the clinic settings, so generation can proceed unambiguously.
  - Maintain a unit test suite that generates slots across the DST transition boundaries for every IANA timezone in use by any clinic tenant.
