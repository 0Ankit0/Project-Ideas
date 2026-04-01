# Hotel Property Management System — Edge Cases: Check-In and Check-Out

## Overview

Check-in and check-out are the two moments of peak guest-system interaction. Every transaction that accumulated during the guest's stay — room charges, F&B, minibar, spa, parking, incidentals — must reconcile at checkout. Every promise made at booking — room type, bed configuration, view, floor preference — must be honoured at check-in. The edge cases in this file represent the scenarios where the physical reality of the hotel diverges from the digital state of the PMS, placing front-desk staff in the difficult position of managing guest expectations with limited system support.

These six edge cases cover arrival, departure, and the no-show scenario. Each is documented with the full guest experience, staff workflow, system state transitions, financial implications, and resolution path.

---

## EC-CHK-001 — Early Arrival: No Clean Room Available

*Category:* Check-In and Check-Out
*Severity:* High
*Likelihood:* Very High (occurs at nearly every property during morning rush, 08:00–12:00)
*Affected Services:* FrontDeskService, HousekeepingService, RoomService, NotificationService, LoyaltyService

**Description**
Standard check-in time is 15:00. A guest arrives at 09:00 — six hours early. Their reserved room is either occupied by a late-checkout guest or in the housekeeping queue and not yet cleaned. The guest may have come directly from an overnight flight, be travelling with a young child or elderly relative, or have a business meeting starting at 11:00. The system must track the guest's arrival, manage room readiness, and communicate proactively rather than leaving the guest standing at the front desk asking for updates.

**Trigger Conditions**

1. Guest arrives before 15:00 (standard check-in time) or before the earliest early check-in window (typically 12:00 with a fee).
2. The guest's assigned room status is `OCCUPIED` (prior guest still checked in) or `DIRTY` (prior guest checked out, awaiting housekeeping).
3. No equivalent or superior alternative room is available in `CLEAN_INSPECTED` status.
4. The guest has not pre-arranged an early check-in upgrade or paid an early check-in fee at booking.

**Expected System Behaviour**

1. Front desk agent opens the reservation in HPMS. System displays room status: `DIRTY — Est. Ready: 11:30`.
2. Agent informs the guest of the expected room ready time.
3. Agent adds the guest to the `EARLY_ARRIVAL_QUEUE` in FrontDeskService with a mobile number and preferred notification method (SMS or app push).
4. System checks if a clean room of equal or superior type is available immediately. If yes, agent is prompted with an upgrade offer.
5. If no room is available, the system creates a housekeeping priority task: `PRIORITY_CLEAN: Room {X}, Guest awaiting`. HousekeepingService reassigns this room to the next available housekeeper.
6. When the room transitions to `CLEAN_INSPECTED`, the system automatically sends the guest an SMS: "Your room {number} is ready. Please proceed to check-in desk or use mobile check-in."
7. The early arrival queue entry is marked `RESOLVED_ROOM_READY`.
8. Lobby amenities (luggage storage, complimentary coffee, lounge access if loyalty tier qualifies) are offered and recorded in the guest's profile.

**Guest Experience**
Guest is proactively managed. They store luggage, receive lounge access or F&B voucher, and get a mobile notification when the room is ready. They do not need to re-approach the front desk.

**Staff Workflow**
1. Check the early arrival queue at 08:00 and 10:00.
2. Coordinate with Housekeeping Supervisor to prioritise early-arrival rooms.
3. If the room will not be ready before 13:00, proactively call the guest and offer an upgrade if one is available.
4. Document all actions in the reservation note field.

**Financial Impact**
- If an early check-in fee was agreed at booking, it is automatically posted to the folio at check-in time.
- If an upgrade is given to accommodate the early arrival without a fee, post a `COMP_UPGRADE` entry with supervisor approval.
- F&B vouchers issued as goodwill are posted as `COMP_FB` with a $25 cap per guest per incident.

**Failure Mode**
If the early arrival queue is not managed:
- Guest waits at the lobby for hours without updates.
- Multiple guests approach the desk repeatedly, creating a queue and increasing staff stress.
- Some guests leave to find alternative accommodation and dispute the charge on their credit card.
- Online reviews frequently cite "had to wait hours for my room" as the primary complaint.

**Detection**
- *Monitoring:* `early_arrival_queue.length > 10` triggers a front-desk task priority alert.
- *Log Pattern:* `INFO FrontDeskService - Early arrival registered: guest_id={id} room={room} est_ready={time} queue_position={n}`.

**Resolution**
If early arrival queue grows beyond 10 guests:
1. Housekeeping Supervisor activates all available housekeepers to morning clean list.
2. Front Office Manager authorises temporary use of out-of-order rooms if they are cosmetically compliant.
3. If spa or pool areas are available, offer complimentary access as holding amenity.

**Prevention**
- Integrate early check-in requests into the pre-arrival email (sent 24 hours before arrival) with an upsell option for guaranteed early check-in for a fee.
- Configure HousekeepingService to auto-prioritise rooms linked to early arrival queue entries.

**Test Cases**
- *TC-1:* Register an early arrival at 09:00. Simulate room cleaning completing at 11:30. Assert SMS is sent within 60 seconds of room status transitioning to CLEAN_INSPECTED.
- *TC-2:* Register 15 early arrivals with no clean rooms available. Assert the housekeeping priority queue reorders correctly.
- *TC-3:* Early arrival fee is configured at $30. Guest checks in at 11:00. Assert $30 fee posts to folio.

---

## EC-CHK-002 — Late Checkout Dispute (Guest Refuses to Leave)

*Category:* Check-In and Check-Out
*Severity:* High
*Likelihood:* Medium
*Affected Services:* FolioService, FrontDeskService, RoomService, HousekeepingService, LegalService

**Description**
A guest's reservation ends at 12:00 (standard checkout time). At 13:00, the guest has not vacated the room and has not requested a late checkout. A new guest is scheduled to check into the same room at 15:00. The outgoing guest may have misunderstood the checkout time, may be disputing charges on their folio, may be unwell, or — in rare cases — may be deliberately refusing to leave pending a resolution to a complaint.

**Trigger Conditions**

1. Guest's reservation checkout date is today and checkout time has passed (> 12:00).
2. No late checkout was requested via app, at the front desk, or by calling the front desk.
3. Room status remains `OCCUPIED` in the system.
4. An incoming reservation for the same room is scheduled within the next 4 hours.

**Expected System Behaviour**

1. At 12:15, if room status is still `OCCUPIED` and no late checkout is on file, the system creates a front-desk task: `LATE_DEPARTURE_ALERT: Room {X} — checkout was at 12:00, incoming guest arrives at 15:00`.
2. Front desk calls the room at 12:30. If no answer, calls the guest's mobile number.
3. If guest confirms they are leaving, update the estimated departure time and inform housekeeping.
4. If guest requests a late checkout, the agent checks availability for the room: if available, offer late checkout until 14:00 for a fee or as a courtesy.
5. If the room cannot be released late (incoming guest arriving), offer the guest use of a day-use room, the spa changing facilities, or luggage storage.
6. At 14:00, if room is still occupied without an extended checkout, escalate to Front Office Manager.
7. All actions are timestamped in the reservation audit log.

**Guest Experience**
Standard departure: guest receives a reminder message via app at 11:00 ("Check-out time is 12:00. Need more time? Contact us."). If late, receives a polite call rather than a confrontational knock.

**System State Transitions**
- 11:00: `CHECKOUT_REMINDER_SENT`
- 12:15: `LATE_DEPARTURE_TASK_CREATED`
- 12:30: `PHONE_CONTACT_ATTEMPTED`
- 14:00 (if unresolved): `FRONT_OFFICE_MANAGER_ESCALATED`
- On physical departure: `CHECKED_OUT`, `DIRTY` triggered on room

**Financial Impact**
- Standard late checkout fee: $50 per hour beyond 12:00 (configurable per property).
- If the room was released without charging and the system state was not updated, the incoming guest may be assigned to an occupied room — escalating to a Critical scenario (see EC-CHK-006).
- If the guest contests the late checkout fee, the dispute is logged as a `FOLIO_DISPUTE` and handled by Front Office Manager with authority to waive up to $100.

**Failure Mode**
- Room not flagged as `OCCUPIED_LATE_DEPARTURE` in time.
- Incoming guest checked in and given a keycard to the occupied room.
- Both guests present in the room simultaneously — severe guest experience incident.
- Potential legal exposure if the new guest enters an occupied room.

**Detection**
- *Monitoring:* Room state stays `OCCUPIED` past `checkout_datetime + 15 minutes`. Alert fires.
- *Alert:* `LateDeparture` — severity High, fires 15 minutes past checkout time for any room with an incoming reservation within 4 hours.

**Resolution**
1. Immediate: Block the incoming guest's check-in to that specific room (hold in `PENDING_ASSIGNMENT`) and assign an alternative room while the late departure is resolved.
2. Contact the late-departing guest and resolve the situation before any keycards are issued for the room.

**Prevention**
- Pre-arrival and day-of-departure messaging built into the notification workflow.
- Automated late departure fee posting triggered by room status rather than requiring manual agent action.

**Test Cases**
- *TC-1:* Room still OCCUPIED at 12:15 with incoming guest at 15:00. Assert front-desk task created at 12:15.
- *TC-2:* Guest requests late checkout at 11:30. Room has no incoming guest until 18:00. Assert late checkout to 14:00 granted with fee posted.
- *TC-3:* Simulate incoming guest attempting check-in to late-departure room. Assert the system blocks the room assignment and suggests alternatives.

---

## EC-CHK-003 — No-Show After Guaranteed Reservation

*Category:* Check-In and Check-Out
*Severity:* Medium
*Likelihood:* High
*Affected Services:* ReservationService, FolioService, PaymentService, InventoryService, NightAuditService

**Description**
A guest guaranteed their reservation with a credit card (meaning the hotel holds the room regardless of arrival time). The guest does not arrive by the end of the no-show processing window (typically 23:59 on the arrival date) and does not call to cancel. The system must automatically post the no-show charge, release the room to inventory, and archive the reservation appropriately.

**Trigger Conditions**

1. Reservation status is `CONFIRMED` with `guarantee_type = CREDIT_CARD`.
2. The guest has not checked in by 23:59 on the arrival date.
3. No cancellation was submitted before the cancellation deadline.
4. The night audit process runs the no-show processing job.

**Expected System Behaviour**

1. Night audit job runs at 02:00 and queries all reservations with `status = CONFIRMED AND checkin_date = yesterday AND actual_checkin IS NULL`.
2. For each no-show reservation:
   a. Post a `NO_SHOW_CHARGE` to the folio equal to the first night's room rate plus taxes.
   b. Attempt to charge the credit card on file: `PaymentService.charge(amount=first_night_rate, card_token=token, reason='NO_SHOW')`.
   c. If charge succeeds: update reservation status to `NO_SHOW_CHARGED`. Release the remaining nights' inventory back to the pool.
   d. If charge fails: update reservation status to `NO_SHOW_CHARGE_FAILED`. Flag the folio for manual follow-up by Revenue Manager.
3. Send an automated email to the guest confirming the no-show charge with a note about the cancellation policy and an option to dispute.
4. If the reservation had a multi-night block, release nights 2+ to inventory immediately after charging night 1.

**Financial Impact**
- First night's rate + taxes charged to the card.
- Remaining nights released to inventory (revenue recovery opportunity).
- If the card decline rate on no-show charges is above 15%, a review of the guarantee policy is triggered.

**Failure Mode**
If the no-show job fails to run (see EC-OPS-001):
- Rooms remain blocked in inventory for future nights unnecessarily.
- No-show charge is not applied, resulting in revenue loss.
- Credit card authorisation (if held) expires.

**Detection**
- *Monitoring:* `night_audit.no_show_processed_count` compared with `reservations.expected_no_show_count`. Alert if they diverge by > 5%.
- *Log Pattern:* `INFO NightAuditService - No-show processed: reservation_id={id} charge_result={SUCCESS|FAILED} amount={amount}`.

**Resolution**
For `NO_SHOW_CHARGE_FAILED`:
1. Revenue Manager receives a daily report of failed no-show charges.
2. Attempt re-charge within 24 hours.
3. If re-charge fails, send a formal invoice to the guest's email with payment link.
4. After 30 days with no payment, refer to accounts receivable.

**Prevention**
- Send a pre-arrival reminder at 48 hours and 24 hours before arrival with a cancellation link.
- Require re-confirmation for reservations with lead time > 60 days.
- Night audit no-show job must have a dead man's switch — if it does not run by 03:00, a P1 alert fires.

**Test Cases**
- *TC-1:* Guaranteed reservation, no check-in by 23:59. Assert no-show charge is posted at 02:00 and card is charged.
- *TC-2:* Card charge fails during no-show processing. Assert reservation is flagged `NO_SHOW_CHARGE_FAILED` and appears in Revenue Manager dashboard.
- *TC-3:* No-show on a 3-night reservation. Assert only night 1 is charged and nights 2–3 are released to inventory.

---

## EC-CHK-004 — Walk-In Guest During 100% Occupancy

*Category:* Check-In and Check-Out
*Severity:* Medium
*Likelihood:* Medium
*Affected Services:* ReservationService, InventoryService, FrontDeskService, PartnerHotelService

**Description**
A guest arrives at the front desk without a reservation during a period of 100% physical occupancy. This can occur on event nights, holiday weekends, or when the hotel has sold out across all channels. The system must communicate availability accurately, avoid creating a reservation that cannot be fulfilled, and — if the guest is a loyalty member or a corporate account holder — explore every alternative before turning them away.

**Trigger Conditions**

1. `available_count = 0` for all room types for tonight.
2. All overbooking slots are also consumed.
3. Guest requests accommodation without a reservation.

**Expected System Behaviour**

1. Front desk agent searches for availability: `GET /inventory/available?checkin=today&checkout=tomorrow&occupants=1`. Response: `{"available": false, "occupancy_rate": 1.0, "message": "Fully booked"}`.
2. System automatically checks partner hotel availability via PartnerHotelService: `GET /partner-hotels/nearby/availability?checkin=today&checkout=tomorrow&star_rating=>=3`.
3. System presents agent with a list of available partner hotels with rates, distance, and a booking URL.
4. If the guest is a loyalty member, the agent is prompted to check for last-minute cancellations or VIP-held rooms before proceeding to partner referral.
5. If a partner hotel room is confirmed, the system records the referral: `POST /partner-hotels/referral {guest_id, partner_hotel_id, booking_ref}`. This populates the monthly referral report.
6. Agent provides the guest with a referral card that includes the partner hotel address, the front desk's direct number, and a $20 F&B voucher for the referring hotel (to be redeemed on a future visit).

**Financial Impact**
- No revenue from tonight's stay.
- Referral relationship preserves guest loyalty.
- $20 F&B voucher has a cost-of-goods of ~$8 and creates a future visit incentive.

**Failure Mode**
If the system does not check partner availability:
- Agent turns the guest away without alternatives.
- Guest books at a competitor hotel, potentially permanently losing them.
- No referral record is created, so the Revenue Manager does not know how many guests were turned away (invisible lost revenue).

**Test Cases**
- *TC-1:* Walk-in during full occupancy. Assert partner hotel search returns at least one result.
- *TC-2:* Walk-in loyalty platinum member during full occupancy. Assert VIP-held rooms are checked before partner referral.
- *TC-3:* All partner hotels are also fully booked. Assert agent receives a "No availability in area" message with a list of same-brand properties within 20 km.

---

## EC-CHK-005 — Express Checkout with Outstanding Folio Balance

*Category:* Check-In and Check-Out
*Severity:* High
*Likelihood:* Medium
*Affected Services:* FolioService, PaymentService, CheckoutService, NotificationService

**Description**
Express checkout allows guests to check out via the mobile app or TV system without visiting the front desk. The guest reviews their folio, approves the charges, and their card is automatically charged. An outstanding balance situation occurs when the card on file cannot cover the full folio amount, the card has expired, the folio contains disputed charges, or a split-folio arrangement (e.g., company pays room, guest pays incidentals) requires manual processing that cannot be automated.

**Trigger Conditions**

1. Guest initiates express checkout via mobile app or in-room TV.
2. At least one of the following is true:
   - The credit card on file is declined when charged the folio total.
   - The card stored has an expiry date in the past.
   - The folio contains a `DISPUTED` charge flag that requires supervisor review before checkout can be finalised.
   - The folio is configured as a split folio with a company account that has not pre-authorised.
3. The automated checkout flow cannot resolve the issue without human intervention.

**Expected System Behaviour**

1. Guest requests express checkout: `POST /checkout/express {reservation_id, approved_folio: true}`.
2. CheckoutService retrieves the folio total and attempts to charge the stored payment method.
3. If charge succeeds: reservation transitions to `CHECKED_OUT`, room transitions to `DIRTY`, and a final invoice PDF is emailed to the guest.
4. If charge fails (card declined):
   a. System does NOT complete the checkout.
   b. Guest receives an in-app notification: "We were unable to process your payment. Please visit the front desk or update your payment method in the app to complete checkout."
   c. System adds a `CHECKOUT_BLOCKED_PAYMENT_FAILURE` flag to the reservation.
   d. Front desk receives a task: "Express checkout failed — guest {name} in room {n}: payment declined. Amount due: ${amount}."
5. If the folio contains a dispute flag:
   a. System does NOT complete the checkout.
   b. Guest receives: "Your folio contains a charge that requires review. A front desk agent will contact you."
   c. Front desk agent calls the guest's room within 15 minutes.

**Financial Impact**
- A completed checkout with an outstanding balance means the hotel has provided accommodation without payment — a bad debt risk.
- The card must be charged before the guest leaves the property. Once the guest departs, recovery becomes significantly more difficult and may require third-party collection.

**System State Transitions**
- `EXPRESS_CHECKOUT_REQUESTED` → `PAYMENT_FAILED` → `CHECKOUT_BLOCKED` (guest notified) → `FRONT_DESK_INTERVENTION_REQUIRED`

**Resolution**

1. Front desk agent contacts the guest immediately (by phone and in-room message).
2. Guest options: (A) Provide a new credit card at the front desk, (B) Pay cash, (C) Dispute specific charges — disputed charges are temporarily removed and guest pays the undisputed amount.
3. If the guest has already departed without completing payment (checkout was not properly blocked): Revenue Manager initiates debt recovery using the card-on-file for partial charges and formal invoice for the balance.

**Prevention**
- Run a pre-checkout folio review at 22:00 the night before departure: check for declined test charges and notify the guest proactively.
- Require card re-authorisation for folios exceeding $500 at 07:00 on departure day.
- Block express checkout if the folio contains any `DISPUTED` flag — require front-desk resolution first.

**Test Cases**
- *TC-1:* Express checkout with a valid card and clean folio. Assert checkout completes and invoice is emailed within 30 seconds.
- *TC-2:* Express checkout with declined card. Assert checkout is blocked, guest is notified in-app, and front-desk task is created.
- *TC-3:* Express checkout with an expired card. Assert the system detects expiry before attempting the charge and notifies the guest to update payment method.

---

## EC-CHK-006 — Duplicate Check-In (System Already Shows Guest Checked In)

*Category:* Check-In and Check-Out
*Severity:* Critical
*Likelihood:* Low
*Affected Services:* FrontDeskService, ReservationService, KeycardService, AuditService

**Description**
A front desk agent attempts to check in a guest, but the system shows the reservation as already in status `CHECKED_IN` — yet the guest is physically at the front desk saying they have not checked in. This scenario can occur if a previous agent performed a check-in prematurely (e.g., checked in the wrong guest by mistake), if the system processed a mobile check-in that the guest did not initiate, or if a synchronisation error between PMS nodes resulted in a stale state.

**Trigger Conditions**

1. Guest presents at the front desk for check-in.
2. ReservationService returns `status = CHECKED_IN` for the guest's reservation.
3. The guest credibly denies having previously checked in.
4. No keycard activity exists for the assigned room since the supposed check-in time (confirming no physical entry was made).

**Expected System Behaviour**

1. Front desk agent sees the CHECKED_IN status. Before issuing a new keycard, the agent verifies by checking the keycard access log: `GET /keycard/access-log?room={room}&since={checkin_timestamp}`. If no entries exist, the check-in is confirmed as erroneous.
2. Agent escalates to supervisor. Supervisor uses their override token to: `POST /reservations/{id}/override-checkin {reason: "False check-in detected, guest confirmed not in building"}`.
3. System creates a full audit trail entry: timestamp, supervisor ID, reason, before/after state.
4. System re-issues the check-in: reservation transitions from `CHECKED_IN_OVERRIDE_PENDING` to `CHECKED_IN_CONFIRMED_FRESH`, a new keycard is encoded, and any previously encoded keycards for that room are invalidated by the keycard system.
5. AuditService logs the anomaly for investigation: `SECURITY_AUDIT: Duplicate check-in override on reservation {id} by supervisor {id}`.
6. If the false check-in was associated with a different guest's profile (i.e., wrong guest was checked in), the original guest's reservation is corrected and their folio is reconciled.

**Guest Experience**
From the guest's perspective, there is a brief delay while the supervisor override is completed. The agent apologises for the system issue, processes the check-in, and offers a goodwill gesture (e.g., a bottle of water, a complimentary room upgrade if available).

**Financial Impact**
- If charges were posted to the folio between the false check-in time and the current time, those charges must be reviewed.
- If minibar access logs or POS charges are tied to the room during that period, a manual folio audit is required.

**Failure Mode**
If the duplicate check-in is not detected and a second keycard is issued:
- The room may now have two active keycards.
- A potential security issue exists if the first keycard was issued to an incorrect guest who entered the room.

**Detection**
- *Monitoring:* `checkin.duplicate_attempt_count` counter. Alert if > 3 per day at a single property.
- *Log Pattern:* `WARN FrontDeskService - Check-in attempted for already-checked-in reservation: reservation_id={id} agent_id={id}`.
- *Security Alert:* `DuplicateCheckInDetected` — triggers an automatic review of keycard access logs for the affected room.

**Resolution**
1. Supervisor override to reset check-in state.
2. Invalidate all previously encoded keycards for the room.
3. Issue fresh keycard and complete check-in.
4. Conduct a post-incident review to identify how the false check-in was created.

**Prevention**
- Mobile check-in must require biometric or OTP confirmation before transitioning the reservation state.
- PMS should check for keycard activity before allowing a check-in state transition from another agent's session.
- Add a 2-minute cooldown: if a reservation was checked in within the last 2 minutes by a different agent, the second check-in attempt triggers a supervisor approval workflow rather than completing automatically.

**Test Cases**
- *TC-1:* Attempt to check in a reservation that is already CHECKED_IN. Assert the system warns the agent and requires supervisor override.
- *TC-2:* Supervisor completes override with valid reason. Assert audit trail is created and old keycards are invalidated.
- *TC-3:* Mobile check-in is processed without OTP confirmation (simulating a bug). Assert the check-in state change is rejected.

---

## Edge Case Summary Matrix

| ID | Title | Severity | Likelihood | Priority | Guest Impact | Financial Impact |
|----|-------|----------|------------|----------|--------------|-----------------|
| EC-CHK-001 | Early Arrival: No Clean Room | High | Very High | P2 | Wait time, inconvenience | Upgrade cost, F&B comp |
| EC-CHK-002 | Late Checkout Dispute | High | Medium | P2 | Potential room conflict | Late fee, relocation cost |
| EC-CHK-003 | No-Show After Guaranteed Reservation | Medium | High | P2 | None (guest absent) | First-night revenue recovery |
| EC-CHK-004 | Walk-In During Full Occupancy | Medium | Medium | P3 | Turned away; referral offered | No revenue; referral relationship |
| EC-CHK-005 | Express Checkout Payment Failure | High | Medium | P2 | Checkout delayed | Bad debt risk if guest departs |
| EC-CHK-006 | Duplicate Check-In | Critical | Low | P1 | Security concern; brief delay | Folio audit required |
