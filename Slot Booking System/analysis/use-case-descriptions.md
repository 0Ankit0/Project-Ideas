# Use Case Descriptions — Slot Booking System

Detailed pre/post conditions, main flows, and alternate flows for the primary use cases of the Slot Booking System.

---

## UC-01: Create Booking

| Attribute | Detail |
|-----------|--------|
| **Use Case ID** | UC-01 |
| **Name** | Create Booking |
| **Primary Actor** | Customer |
| **Secondary Actors** | Payment Gateway, Notification Service, Slot Service |
| **Trigger** | Customer selects an available slot and initiates checkout |
| **Priority** | Must Have |

**Preconditions:**
1. Customer is authenticated (valid JWT token).
2. Target slot is in `AVAILABLE` status.
3. Current time is within the advance booking window (BR-01).
4. Customer account is not suspended.
5. If customer has `prepayment_required = true` (BR-09), payment mode must be ONLINE.

**Postconditions (Success):**
1. `Booking` record created with status `CONFIRMED`.
2. `BookingItem` record created for each slot.
3. Slot `confirmed_count` incremented; slot status updated to `BOOKED` if at capacity.
4. `PaymentRecord` created with status `CAPTURED`.
5. `BookingCreated` and `BookingConfirmed` events published.
6. Confirmation email and SMS sent to customer.
7. Reminder jobs scheduled for 24h and 1h before slot start.

**Postconditions (Failure):**
1. No booking or payment record created.
2. Slot availability unchanged.
3. Error response returned with specific rule violation code.

**Main Success Flow:**
1. Customer calls `GET /availability?resource_id={id}&date={date}` to view available slots.
2. Customer selects a slot and calls `POST /bookings` with `slot_id`, `payment_method_id`.
3. System acquires Redis distributed lock on `resource_id` (5-second TTL).
4. System validates BR-01 (advance window), BR-04 (duration), BR-07 (capacity), BR-08 (corporate quota), BR-02 (overlap).
5. System creates `Booking` in `PENDING_PAYMENT` state and a provisional slot hold.
6. System calls Payment Gateway to capture payment.
7. Payment Gateway confirms capture.
8. System transitions `Booking` to `CONFIRMED` and publishes events.
9. System releases Redis lock.
10. Returns HTTP 201 with booking detail.

**Alternate Flow A — Slot Already Taken (BR-02):**
- At step 4, overlap check fails.
- System releases Redis lock.
- Returns HTTP 409 `SLOT_CONFLICT`.
- System redirects customer to availability picker with up-to-date slot grid.

**Alternate Flow B — Payment Failure:**
- At step 6, payment gateway returns decline.
- System cancels the provisional hold.
- Booking transitions to `PAYMENT_FAILED`.
- Returns HTTP 402 with `PAYMENT_DECLINED` code.
- Slot availability restored.

**Alternate Flow C — Corporate Quota Exceeded (BR-08):**
- At step 4, quota check fails.
- Booking transitions to `PENDING_CORPORATE_APPROVAL`.
- Corporate admin notified.
- Returns HTTP 202 Accepted with pending-approval message.

---

## UC-02: Cancel Booking

| Attribute | Detail |
|-----------|--------|
| **Use Case ID** | UC-02 |
| **Name** | Cancel Booking |
| **Primary Actor** | Customer |
| **Secondary Actors** | Refund Service, Waitlist Service, Notification Service |
| **Trigger** | Customer requests cancellation of a confirmed booking |
| **Priority** | Must Have |

**Preconditions:**
1. Booking exists in `CONFIRMED` status.
2. Customer is the booking owner or an admin actor.
3. Slot start time has not yet passed.

**Postconditions (Success):**
1. Booking status transitions to `CANCELLED`.
2. Refund initiated per cancellation policy (BR-03).
3. Slot `confirmed_count` decremented; slot status reverts to `AVAILABLE` or `WAITLIST_ONLY`.
4. `BookingCancelled` event published.
5. Waitlist auto-promotion triggered (BR-05).
6. Cancellation email with refund amount sent to customer.

**Main Success Flow:**
1. Customer calls `DELETE /bookings/{booking_id}`.
2. System validates ownership and current booking status.
3. System calculates lead time and determines refund amount per BR-03.
4. System updates `Booking.status = CANCELLED` and records cancellation reason.
5. System decrements slot `confirmed_count`.
6. System initiates refund via Payment Gateway.
7. System publishes `BookingCancelled` event.
8. Waitlist Service consumes event and evaluates promotion (BR-05).
9. Notification Service sends cancellation confirmation.
10. Returns HTTP 200 with `{refund_amount, penalty_amount, refund_eta}`.

**Alternate Flow A — Within Same-Day Window (BR-03):**
- At step 3, lead time < 24h.
- Refund = 50% of `booking.final_amount`.
- Response includes `penalty_amount` field with 50% value.

**Alternate Flow B — Admin-Forced Cancellation:**
- Admin calls `DELETE /admin/bookings/{id}` with `reason = FORCE_MAJEURE`.
- Refund = 100% regardless of policy.
- AuditEvent written with `event_type = ADMIN_CANCELLATION`.

---

## UC-03: Auto-Promote Waitlist

| Attribute | Detail |
|-----------|--------|
| **Use Case ID** | UC-03 |
| **Name** | Auto-Promote Waitlist |
| **Primary Actor** | Background Job / Waitlist Service |
| **Trigger** | `BookingCancelled` event consumed by Waitlist Service |
| **Priority** | Must Have |

**Preconditions:**
1. A `BookingCancelled` event has been published for a slot that has waiting `WaitlistEntry` records.
2. The slot's start time is in the future.

**Postconditions (Success):**
1. First eligible `WaitlistEntry` promoted: status = `PROMOTED`.
2. Provisional `Booking` created in `WAITLIST_PROMOTED` state with 30-minute expiry.
3. `WaitlistPromoted` event published.
4. Customer notified via push + email + SMS with confirmation link.

**Postconditions (No Eligible Candidate):**
1. No promotion occurs.
2. Slot reverts to `AVAILABLE`.

**Main Success Flow:**
1. Waitlist Service consumes `BookingCancelled` event.
2. Queries `WaitlistEntry` for `slot_id`, ordered by `priority ASC, joined_at ASC`.
3. Evaluates first entry: checks customer account status, no suspension, BR-09 compliance.
4. Creates provisional booking with `expires_at = NOW() + 30 min`.
5. Updates `WaitlistEntry.status = PROMOTED` and sets `expires_at`.
6. Publishes `WaitlistPromoted` event.
7. Notification Service sends promotion alert.
8. Customer calls `POST /bookings/{id}/confirm` with payment within 30 minutes.
9. Booking transitions to `CONFIRMED` on payment capture.

**Alternate Flow A — Customer Does Not Respond:**
- At T+30 minutes, expiry job runs.
- Provisional booking transitions to `EXPIRED`.
- `WaitlistEntry.status = EXPIRED`.
- Process repeats from step 2 with next candidate.

**Alternate Flow B — Customer Declines:**
- Customer calls `DELETE /bookings/{id}` on the provisional booking.
- `WaitlistEntry.status = WITHDRAWN`.
- Process repeats from step 2 with next candidate.

---

## UC-04: Setup Recurring Booking

| Attribute | Detail |
|-----------|--------|
| **Use Case ID** | UC-04 |
| **Name** | Setup Recurring Booking |
| **Primary Actor** | Customer |
| **Trigger** | Customer configures a recurring series for a resource |
| **Priority** | Should Have |

**Preconditions:**
1. Customer is authenticated.
2. Resource is active and has available slots matching the requested cadence.

**Postconditions (Success):**
1. `RecurringRule` record created.
2. Individual `Booking` and `BookingItem` records created for each occurrence.
3. Each occurrence validated against BR-02, BR-04, BR-06.
4. First occurrence payment captured or payment schedule created.
5. `BookingCreated` events published for each occurrence.

**Main Success Flow:**
1. Customer calls `POST /recurring-bookings` with `resource_id`, `cadence`, `start_date`, `end_date`, `time`, `duration`.
2. System generates the list of occurrence dates using the `RecurringRule`.
3. For each occurrence, system validates BR-01, BR-02, BR-04, BR-06 in a dry-run transaction.
4. If all occurrences pass validation, system commits the entire series.
5. Returns HTTP 201 with `series_id` and list of booking IDs.

**Alternate Flow — Conflict Detected:**
- At step 3, one or more occurrences fail BR-02.
- System rolls back all (nothing committed).
- Returns HTTP 409 with array of conflicting dates and reason codes.
- Customer must adjust dates or cadence and retry.

---

## UC-05: Apply Rule Override

| Attribute | Detail |
|-----------|--------|
| **Use Case ID** | UC-05 |
| **Name** | Apply Rule Override |
| **Primary Actor** | Platform Admin |
| **Trigger** | Admin needs to bypass an enforceable business rule for a specific booking |
| **Priority** | Must Have |

**Preconditions:**
1. Admin is authenticated with `PLATFORM_ADMIN` role.
2. Admin holds the specific override permission for the target rule.

**Postconditions (Success):**
1. Override applied; booking proceeds bypassing the specified rule check.
2. `AuditEvent` written with full override detail.
3. Override count tracked; alert raised if threshold exceeded.

**Main Success Flow:**
1. Admin calls `POST /admin/overrides` with `booking_id`, `rule_id`, `reason`, `approver_id`.
2. System validates admin has required override permission.
3. System stores override record in `AuditEvent`.
4. System marks the booking with `rule_override = true` and the overridden rule ID.
5. Booking allowed to proceed through normal flow with the specified rule disabled for this booking.
6. Returns HTTP 200 with override confirmation.

**Alternate Flow — Insufficient Permission:**
- Admin does not hold the override permission.
- Returns HTTP 403 with `OVERRIDE_PERMISSION_DENIED`.
- Attempted override written to security audit log.

---

## UC-06: View Occupancy Reports

| Attribute | Detail |
|-----------|--------|
| **Use Case ID** | UC-06 |
| **Name** | View Occupancy Reports |
| **Primary Actor** | Venue Admin |
| **Trigger** | Admin navigates to the Reports section of the admin console |
| **Priority** | Should Have |

**Preconditions:**
1. Venue Admin is authenticated.
2. At least one resource exists for the venue with historical booking data.

**Postconditions:**
1. Report rendered with occupancy %, revenue, no-show rate, and cancellation rate for the selected date range.

**Main Success Flow:**
1. Venue Admin calls `GET /reports/occupancy?venue_id={id}&from={date}&to={date}`.
2. System queries the read replica and pre-aggregated `reporting_facts` table.
3. Returns occupancy by resource, by hour-of-day heatmap, revenue breakdown, and trend data.
4. Admin can export results to CSV via `GET /reports/occupancy/export`.
