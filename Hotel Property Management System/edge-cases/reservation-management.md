# Hotel Property Management System — Edge Cases: Reservation Management

## Overview

Reservation management is the most concurrency-sensitive subsystem in any PMS. Every edge case in this file involves either simultaneous competing requests, external channel synchronisation lag, or constraint violations that occur at the boundary between inventory availability and guest commitment. These scenarios are documented in production-incident detail so that engineers understand the exact failure modes and operators understand the exact staff response.

The five edge cases below cover the full spectrum from millisecond-level race conditions to multi-day inventory discrepancies caused by channel manager outages.

---

## EC-RES-001 — Double Booking (Race Condition)

*Category:* Reservation Management
*Severity:* Critical
*Likelihood:* Medium (increases sharply during high-demand periods when inventory drops to 1–3 rooms)
*Affected Services:* ReservationService, InventoryService, DatabaseLayer, NotificationService

**Description**
A double booking occurs when two reservation requests for the same room type arrive within milliseconds of each other while only one room of that type is available. Without a distributed atomic lock, both requests read the same `available_count = 1`, both decrement it concurrently, and both write confirmations before either transaction is committed. The result is two confirmed reservations for one physical room. This is the most damaging reservation edge case because it is invisible until check-in, at which point one guest must be walked to a competing property.

**Trigger Conditions**

1. Exactly one room of the requested type remains in inventory for the requested date range.
2. Two or more HTTP POST `/reservations` requests arrive within the same database transaction window (typically < 50 ms on a loaded system).
3. The inventory read and the inventory decrement are not wrapped in the same atomic operation (e.g., SELECT then UPDATE without SELECT ... FOR UPDATE or Redis SETNX).
4. The database isolation level is set to READ COMMITTED rather than SERIALIZABLE (common misconfiguration in PostgreSQL deployments).
5. No distributed lock exists at the application layer to serialise requests for the same room-type + date-range combination.

**Expected System Behaviour**

1. Request A arrives. ReservationService acquires a Redis lock with key `lock:room_type:{type_id}:date:{checkin}:{checkout}` using SETNX with a 5-second TTL.
2. Request A reads `available_count = 1`, confirms availability, and proceeds to write a `PENDING` reservation record.
3. Request B arrives during Request A's lock window. Redis SETNX returns 0 (lock not acquired). Request B enters a 500 ms retry loop (maximum 3 retries).
4. Request A's database transaction commits. Inventory decrements to 0. Redis lock is released.
5. Request B acquires the lock. Reads `available_count = 0`. Returns HTTP 409 Conflict with body `{"error": "ROOM_UNAVAILABLE", "waitlist_offered": true, "waitlist_url": "/reservations/waitlist/{type_id}/{checkin}/{checkout}"}`.
6. NotificationService is triggered only for the successful reservation (Request A). Request B receives no confirmation email.
7. Total latency for Request A: < 300 ms. Request B: < 800 ms including retry loop.

**Failure Mode**
If the distributed lock is absent or the database transaction isolation is insufficient:
- Both requests read `available_count = 1`.
- Both write reservation records with status `CONFIRMED`.
- Inventory decrements twice, resulting in `available_count = -1`.
- Two confirmation emails are dispatched to two different guests for the same room on the same night.
- At check-in, the second guest to arrive finds the room already occupied or already key-issued.
- Staff must walk the second guest to a comparable property, absorbing transport cost, difference in room rate, and loyalty compensation (industry standard: 1 free night on return visit).
- Reputational damage is amplified if the walked guest is a loyalty member or a large-group organiser.

**Detection**
- *Monitoring:* Alert on `inventory.available_count < 0` for any room type. This is an impossible state and fires a P1 alert immediately.
- *Log Pattern:* `WARN ReservationService - Duplicate confirmation detected: reservation_ids=[{id1},{id2}] room_type={type} checkin={date}` written during the nightly audit reconciliation.
- *Alert:* `InventoryNegativeStock` — threshold: `inventory_available_count < 0`, severity: Critical, channel: PagerDuty.
- *User-Reported:* Front desk calls the on-call engineer when the second guest arrives and the room is occupied. This typically occurs 0–90 days after the booking, depending on lead time.

**Resolution**

*Immediate (0–15 minutes):*
1. Identify both confirmed reservations using query: `SELECT * FROM reservations WHERE room_type_id = ? AND checkin_date = ? AND status = 'CONFIRMED' ORDER BY created_at`.
2. Contact the guest with the more recent `created_at` timestamp by phone within 10 minutes.
3. Offer relocation to an equivalent or superior room at a partner property, all transport paid by the hotel.
4. Issue a full refund of the first night's rate and a complimentary future night.
5. Post a `COMPENSATION_CREDIT` transaction to the walked guest's folio before they depart.

*Short-term (0–1 hour):*
6. Correct the inventory count: `UPDATE room_inventory SET available_count = 0 WHERE room_type_id = ? AND date = ?`.
7. Set the duplicate reservation to status `CANCELLED_WALKED` with an internal note referencing the incident ID.
8. Verify that the Redis lock key no longer exists: `redis-cli EXISTS lock:room_type:{type_id}:date:{checkin}:{checkout}`.

*Full Remediation (0–24 hours):*
9. Deploy the distributed locking fix if not already in place.
10. Run a full inventory reconciliation across all future dates.
11. File an incident report and RCA.

**Prevention**
- Implement Redis SETNX with TTL as a distributed lock around all inventory decrement operations.
- Use PostgreSQL `SELECT ... FOR UPDATE` within the reservation transaction as a secondary guard.
- Set database isolation level to REPEATABLE READ minimum.
- Add a unique constraint: `UNIQUE INDEX uq_reservation_room_date ON reservations(room_id, checkin_date)` — this catches any leak past the application lock.
- Run integration tests simulating concurrent requests using k6 or Gatling with 100 virtual users competing for the last room.

**Test Cases**
- *TC-1 (Concurrent lock acquisition):* Send 50 simultaneous POST `/reservations` requests for the last available room. Assert exactly 1 returns 200 OK, 49 return 409. Assert `available_count` is exactly 0 after all requests complete.
- *TC-2 (Lock TTL expiry):* Simulate Request A holding the lock, then kill the process before releasing it. Assert the TTL expires within 5 seconds and Request B can proceed.
- *TC-3 (Database unique constraint):* Bypass the application lock and insert two reservation rows with the same room_id and checkin_date directly in SQL. Assert a database-level unique constraint violation is raised.

---

## EC-RES-002 — Overbooking Limit Breach

*Category:* Reservation Management
*Severity:* High
*Likelihood:* Medium (most hotels run deliberate overbooking buffers; this case fires when the buffer is exceeded unexpectedly)
*Affected Services:* ReservationService, InventoryService, OverbookingPolicyService, YieldManagementService

**Description**
Hotels intentionally overbook rooms to compensate for expected no-shows. The overbooking policy defines a maximum overbook percentage per room type (e.g., 105% of physical capacity for standard doubles). An overbooking limit breach occurs when the cumulative confirmed reservations exceed the maximum overbook threshold — either because the no-show rate was lower than predicted, because a bulk group booking was confirmed without checking the overbook count, or because a manual inventory adjustment was made incorrectly. When the breach is detected at check-in, more guests arrive than rooms exist.

**Trigger Conditions**

1. `confirmed_reservations_count > physical_room_count * max_overbook_ratio` for the arrival date.
2. The breach occurs because: (a) OverbookingPolicyService failed to enforce the limit during a group booking confirmation, or (b) a manual inventory block was added without adjusting the overbook ceiling, or (c) OTA channels continued accepting bookings after the PMS reached the limit due to a sync delay.
3. Walk-in or early-check-in guests fill physical rooms before all pre-reserved guests arrive.
4. No guest has been proactively relocated before arrival.

**Expected System Behaviour**

1. OverbookingPolicyService runs a daily check at 06:00 for all arrivals in the next 48 hours.
2. If `confirmed_count > threshold`, the service flags the date as `OVERBOOK_ALERT` and creates a task in the front-desk task queue: "Overbooked: {n} guests confirmed, {m} rooms available. Action required."
3. YieldManagementService closes availability on all OTA channels immediately via ChannelManager.
4. Front desk supervisor reviews the guest list and selects walk candidates based on loyalty tier (lowest tier first, non-loyalty last), selects comparable hotel, and initiates proactive relocation contact at least 24 hours before arrival.
5. Walked guests receive a call + email: free transport, complimentary first night at the alternative property, and a future stay credit equal to 50% of the original booking value.
6. System records the relocation in the reservation record with status `WALKED_PROACTIVE` and posts a `$0 WALK_COMPENSATION` folio entry that triggers accounting to apply the credit.

**Failure Mode**
If OverbookingPolicyService does not run or the alert is ignored:
- All guests arrive and expect rooms.
- Front desk must perform reactive walking — significantly more distressing for guests than proactive contact.
- Risk of online reviews, social media complaints, and loyalty account escalations.
- In regulated jurisdictions, overbooking without proactive notification may trigger consumer protection liability.

**Detection**
- *Monitoring:* `reservations.overbook_ratio_by_date` gauge metric. Alert when ratio exceeds `max_overbook_ratio + 0.02` (2% safety margin breach).
- *Log Pattern:* `WARN OverbookingPolicyService - Overbook limit breached: date={date} type={type} confirmed={n} capacity={m} ratio={r}`.
- *Alert:* `OverbookLimitBreached` — fires at 08:00 daily for the next 48-hour arrival window.

**Resolution**

1. Pull the overbooked arrival list: `SELECT * FROM reservations WHERE checkin_date = ? AND status = 'CONFIRMED' ORDER BY loyalty_tier ASC, booking_value ASC`.
2. Contact walk candidates starting from the bottom of the list (lowest-value, non-loyalty guests first).
3. Confirm alternative hotel availability via the partner booking system before calling the guest.
4. Document each relocation in the PMS with the alternative hotel confirmation number.
5. Close inventory on all channels: `POST /channel-manager/inventory/close {room_type: *, date: ?}`.

**Prevention**
- Hard cap in OverbookingPolicyService: reject any reservation that would breach `physical_capacity * max_ratio + 1`.
- Group bookings require a supervisor override token if they would push any date past 102% of physical capacity.
- Daily automated overbook report emailed to Front Office Manager at 07:00.
- Nightly audit checks overbook ratios for the next 7 days and creates alerts for all dates above threshold.

**Test Cases**
- *TC-1:* Confirm reservations up to exactly 105% of capacity. Assert no alert fires. Confirm one more. Assert `OverbookLimitBreached` alert fires and OTA channels are closed.
- *TC-2:* Simulate OverbookingPolicyService failure (service crash). Assert the nightly audit catches the overbooked date the following morning.
- *TC-3:* Confirm a group booking that would breach the limit. Assert the booking is blocked with error `OVERBOOK_LIMIT_EXCEEDED` and requires supervisor override.

---

## EC-RES-003 — OTA Sync Conflict (Simultaneous Channel Booking)

*Category:* Reservation Management
*Severity:* Critical
*Likelihood:* High (occurs multiple times weekly at busy properties)
*Affected Services:* ChannelManager, ReservationService, InventoryService, BookingDotComAdapter, ExpediaAdapter

**Description**
The hotel lists rooms on multiple Online Travel Agencies (OTAs) simultaneously — Booking.com, Expedia, Airbnb, direct website. The channel manager is responsible for keeping all channels synchronised: when a room is sold on one channel, the channel manager must close that room on all other channels within the sync window (typically 30–60 seconds). An OTA sync conflict occurs when two guests book the same room on two different channels within the same sync window, both receiving confirmations before the channel manager can close the competing channel. The result is functionally identical to a double booking but harder to detect because the confirmation numbers come from different external systems.

**Trigger Conditions**

1. Inventory for the affected room type is at 1 room for the requested dates.
2. Channel Manager sync interval is 30 seconds (standard) or longer due to API rate limiting.
3. Guest A books on Booking.com and receives an external confirmation number.
4. Guest B books on Expedia within the 30-second sync window before the Booking.com booking is reflected in the PMS inventory.
5. Both bookings are pushed to the PMS via webhook within seconds of each other, both passing the availability check against the now-stale `available_count = 1`.

**Expected System Behaviour**

1. Booking.com webhook arrives: `POST /webhooks/bookingdotcom` with `external_ref=BDC-123456`.
2. ReservationService processes the webhook, acquires the inventory lock, confirms `available_count = 1`, creates reservation with status `CONFIRMED`, decrements inventory to 0, releases lock.
3. Channel Manager immediately pushes a stop-sell signal to all other channels: `POST /expedia/availability {rooms: 0, dates: [...]}`.
4. Expedia webhook arrives: `POST /webhooks/expedia` with `external_ref=EXP-789012`. ReservationService acquires lock, reads `available_count = 0`, rejects the booking.
5. ReservationService calls Expedia cancellation API: `DELETE /expedia/reservations/EXP-789012` with reason `INVENTORY_EXHAUSTED`.
6. Expedia notifies the guest of the cancellation and processes the refund.
7. The entire sequence completes within 10 seconds of the first webhook arriving.

**Failure Mode**
If channel manager sync is delayed or the inventory lock is absent:
- Both webhooks are processed and both reservations are confirmed in the PMS.
- Two different external confirmation numbers are issued to two guests.
- Neither guest is aware of the conflict until check-in.
- Cancellation of one booking requires manual coordination with the OTA, which may take hours and may result in financial penalties if the cancellation window has passed.

**Detection**
- *Monitoring:* `channel_manager.sync_lag_seconds` — alert if > 45 seconds. `reservations.duplicate_external_ref_channel_conflict` counter.
- *Log Pattern:* `ERROR ReservationService - Inventory conflict on OTA webhook: room_type={type} date={date} existing_ref={r1} incoming_ref={r2}`.
- *Alert:* `OTASyncConflict` — fires when a webhook is rejected due to zero inventory within 60 seconds of a previous successful webhook for the same room type.

**Resolution**

1. Identify the conflicting reservations using `external_channel` and `created_at` timestamp.
2. Cancel the Expedia booking via API (prefer cancelling the later-arriving booking).
3. If Expedia cancellation window has passed, contact Expedia partner support directly.
4. Notify the cancelled guest immediately with a sincere apology, full refund, and a direct-booking discount code for a future stay.
5. Reduce channel manager sync interval from 30 to 10 seconds for high-demand periods.

**Prevention**
- Implement a per-room-type advisory lock in Redis applied the moment a webhook begins processing, before any database read.
- Use channel manager's "instant booking" mode where supported, which sends stop-sell signals synchronously before confirming the booking.
- Configure OTA channel allocotments: allocate physical inventory across channels (e.g., 60% Booking.com, 30% Expedia, 10% direct) rather than competing on shared pool, reducing race condition probability.

**Test Cases**
- *TC-1:* Fire two simultaneous webhook requests from different channels. Assert only one creates a confirmed reservation.
- *TC-2:* Simulate Expedia webhook arriving 31 seconds after Booking.com (just outside sync window). Assert both channels' availability shows 0.
- *TC-3:* Simulate channel manager stop-sell API returning 503. Assert fallback retry fires within 5 seconds and the stop-sell is eventually delivered.

---

## EC-RES-004 — VIP Block Conflict (Pre-assigned Room Now Needed for VIP)

*Category:* Reservation Management
*Severity:* High
*Likelihood:* Low
*Affected Services:* ReservationService, RoomAssignmentService, VIPManagementService, FolioService

**Description**
A VIP guest (loyalty platinum, returning major account, or designated by GM) is assigned a specific room (e.g., Room 412, corner suite) when their reservation is made 60 days in advance. Within those 60 days, Room 412 is separately pre-assigned to a non-VIP group booking as part of a block allocation. On arrival day, both the VIP guest and a group member expect Room 412. The VIP takes priority by policy, but the system allowed the conflicting assignment to persist undetected.

**Trigger Conditions**

1. VIP reservation is created with a hard room assignment (`preferred_room_id = 412`, `assignment_type = HARD`).
2. A group block allocation is created that includes Room 412 in its room list without checking for existing hard assignments.
3. RoomAssignmentService does not validate hard VIP assignments when processing group block allocations.
4. The conflict is not detected until check-in day room assignment compilation.

**Expected System Behaviour**

1. When a group block requests Room 412, RoomAssignmentService checks `SELECT * FROM room_assignments WHERE room_id = 412 AND date_range OVERLAPS(?) AND assignment_type = 'HARD'`.
2. If a VIP hard assignment exists, the group block allocation for Room 412 is rejected: `{"error": "ROOM_HARD_ASSIGNED_VIP", "suggested_alternatives": [413, 415, 420]}`.
3. Group coordinator is notified of the substitution via email with the list of suggested alternatives.
4. If the group coordinator has already communicated Room 412 to the group member, a proactive reassignment notice is sent directly to the group member at least 72 hours before arrival.

**Failure Mode**
- VIP guest arrives expecting Room 412. Group member is already checked in to Room 412.
- Relocating the group member from an already-occupied room requires full housekeeping, a new keycard, and a personal apology.
- If the VIP is not accommodated correctly, the account relationship may be lost.

**Resolution**

1. On conflict detection, immediately relocate the group member to the best available comparable room before VIP arrival.
2. Deliver a personalised note and F&B credit to the relocated group member.
3. Confirm VIP's room is ready, inspected to VIP standard, with pre-arrival amenities placed.
4. Brief the Front Office Manager before VIP arrival.

**Prevention**
- Hard VIP room assignments must create a `ROOM_HARD_LOCK` record that blocks all other assignment types for the same room and date range.
- Group block allocation must validate against `ROOM_HARD_LOCK` before confirming any room in the block.
- Nightly conflict detection job: `SELECT * FROM room_assignments GROUP BY room_id, date HAVING COUNT(*) > 1` — any result is a P2 alert.

**Test Cases**
- *TC-1:* Create a hard VIP assignment, then attempt a group block that includes the same room. Assert the group block is rejected.
- *TC-2:* Create a group block first, then create a VIP hard assignment to a room in the block. Assert the VIP assignment triggers a conflict notification to the group coordinator.
- *TC-3:* Simulate nightly conflict detection with two overlapping assignments. Assert the alert fires and creates a front-desk task.

---

## EC-RES-005 — Group Booking Partial Failure (Some Rooms Unavailable)

*Category:* Reservation Management
*Severity:* High
*Likelihood:* Medium
*Affected Services:* ReservationService, InventoryService, GroupBookingService, NotificationService

**Description**
A group coordinator requests a block of 20 rooms for a corporate retreat from Friday to Sunday. At the time of the request, 17 rooms of the required type are available and 3 are not (one is out of order for maintenance, one is already reserved, one was just booked by another guest milliseconds earlier). The system must decide: confirm 17 and notify the coordinator of the 3 shortfall, reject the entire block and require the coordinator to renegotiate, or hold the 17 and place the 3 on a pending waitlist with a 24-hour resolution window.

**Trigger Conditions**

1. Group booking request specifies `quantity = 20`, `room_type = STANDARD_DOUBLE`, `dates = Friday-Sunday`.
2. `available_count` for the specified type and dates is 17 (< 20) at the time of processing.
3. The group booking policy is set to `PARTIAL_CONFIRM_THRESHOLD = 80%` — the system will partially confirm if at least 80% of the requested rooms are available.
4. 17/20 = 85% > 80%, so partial confirmation is triggered.

**Expected System Behaviour**

1. GroupBookingService reads available inventory: 17 of 20 rooms available.
2. Calculates partial ratio: 85% — above `PARTIAL_CONFIRM_THRESHOLD`.
3. Atomically reserves all 17 available rooms (one transaction with a list of room IDs).
4. Creates reservation records for 17 rooms with status `CONFIRMED_PARTIAL_GROUP`.
5. Creates 3 waitlist records with status `WAITLIST_PENDING` and a 24-hour expiry.
6. Returns HTTP 207 Multi-Status: `{"confirmed": 17, "waitlisted": 3, "waitlist_expiry": "ISO8601_TIMESTAMP", "message": "17 of 20 rooms confirmed. 3 rooms on waitlist — you will be notified within 24 hours."}`.
7. Sends coordinator a detailed email with the confirmed room list and the waitlist status.
8. Schedules a background job to monitor inventory for the waitlisted room type and auto-confirm if 3 more rooms become available within 24 hours (e.g., due to a cancellation).

**Failure Mode**
If the group booking is an all-or-nothing operation without a partial confirmation path:
- The entire 20-room request is rejected even though 17 rooms are available.
- Coordinator tries other hotels. If the 17 rooms sell individually before the coordinator returns, the hotel loses the entire group.
- Alternatively, if all 20 are confirmed without checking inventory (the optimistic failure), 3 guests arrive without rooms.

**Resolution**

If the 24-hour waitlist window expires without the 3 rooms becoming available:
1. NotificationService sends the coordinator a notification: "3 rooms could not be confirmed. Options: (A) Confirm 17-room block, (B) Cancel with no penalty, (C) Extend waitlist 24 hours."
2. Coordinator selects an option via a secure link in the email.
3. If option (B) is selected, all 17 reserved rooms are released atomically.
4. If 17-room option is selected, the waitlist records are closed and the group contract is updated.

**Prevention**
- Define group booking policy thresholds in configuration, not hardcoded.
- Ensure the partial confirmation transaction uses a single database transaction to avoid partial writes (some rooms confirmed, others not, due to a mid-transaction crash).
- Implement a saga pattern: if the transaction fails partway, compensating actions release all already-confirmed rooms in the group.

**Test Cases**
- *TC-1:* Request 20 rooms when 17 are available. Assert 207 response with 17 confirmed, 3 waitlisted.
- *TC-2:* A cancellation makes 3 rooms available during the waitlist window. Assert the waitlist auto-confirms and coordinator is notified.
- *TC-3:* Request 20 rooms when 15 are available (75% < 80% threshold). Assert the entire request is rejected rather than partially confirmed.
- *TC-4:* Simulate a crash midway through the partial reservation transaction. Assert that no rooms are left in a CONFIRMED_PARTIAL state — either all 17 are confirmed or none are.

---

## Edge Case Summary Matrix

| ID | Title | Severity | Likelihood | Priority | Primary Prevention |
|----|-------|----------|------------|----------|--------------------|
| EC-RES-001 | Double Booking (Race Condition) | Critical | Medium | P1 | Redis distributed lock + DB unique constraint |
| EC-RES-002 | Overbooking Limit Breach | High | Medium | P2 | Hard cap in OverbookingPolicyService + daily audit |
| EC-RES-003 | OTA Sync Conflict | Critical | High | P1 | Per-webhook advisory lock + channel allocation split |
| EC-RES-004 | VIP Block Conflict | High | Low | P3 | ROOM_HARD_LOCK prevents group block overlap |
| EC-RES-005 | Group Booking Partial Failure | High | Medium | P2 | Partial confirmation saga + waitlist auto-resolution |
