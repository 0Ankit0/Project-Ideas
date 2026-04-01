# Hotel Property Management System — Edge Cases: API and UI

## Overview

The Hotel Property Management System integrates with a significant number of external systems: Online Travel Agencies (OTAs), Point-of-Sale terminals, keycard management systems, payment gateways, and channel managers. Each integration boundary is a potential failure point. This file documents the six most consequential API and integration edge cases, with emphasis on system resilience mechanisms — circuit breakers, retry logic with exponential backoff, offline queues, idempotency — and the guest-facing and staff-facing fallbacks that keep the hotel operational even when external systems fail.

---

## EC-API-001 — OTA Sync Failure (Booking.com API Down)

*Category:* API and Integration
*Severity:* High
*Likelihood:* Medium (OTA APIs have published SLAs of 99.5%, meaning ~44 hours downtime per year)
*Affected Services:* ChannelManager, BookingDotComAdapter, InventoryService, ReservationService, AlertingService

**Description**
Booking.com's availability and pricing update API becomes unavailable. The hotel's channel manager can no longer push inventory updates to Booking.com, meaning the availability shown to Booking.com users is stale. If the hotel's occupancy is high, Booking.com may continue selling rooms that are no longer available, creating double bookings. If the hotel's occupancy is low, the hotel may be missing revenue from a major distribution channel during the outage.

**Trigger Conditions**

1. `BookingDotComAdapter.push_availability()` returns a non-200 status code or times out for 3 consecutive attempts.
2. The circuit breaker for the Booking.com integration transitions to `OPEN` state.
3. Inventory updates are queued locally but cannot be delivered.

**Expected System Behaviour**

1. **Circuit Breaker:** The Booking.com adapter uses a circuit breaker with the following state machine:
   - `CLOSED` (normal): requests pass through.
   - `OPEN` (tripped): requests fail immediately (no timeout wait) for 60 seconds; a `STOP_SELL` signal is sent to Booking.com's backup endpoint if one exists.
   - `HALF_OPEN` (recovery probe): one request is allowed through every 60 seconds to test recovery.
   - If recovery probe succeeds: transition to `CLOSED`. If it fails: stay `OPEN`.

2. **Stop-Sell Safety:** When the circuit breaker opens, the channel manager immediately attempts to set availability to 0 on Booking.com (via any available backup endpoint or the OTA's emergency contact). This prevents new bookings on stale inventory.

3. **Offline Queue:** All inventory update events that cannot be delivered are written to a persistent offline queue (Redis Streams or a database table): `{event_type: 'AVAILABILITY_UPDATE', room_type, date, available_count, timestamp}`.

4. **Monitoring Alert:** `OTASyncFailure_BookingDotCom` alert fires within 5 minutes of the first timeout. Severity: High. Channels: PagerDuty (on-call engineer) + Slack (#ops-alerts).

5. **Recovery:** When the circuit breaker transitions back to `CLOSED`, the offline queue is replayed in chronological order. The most recent availability state for each room type + date is applied (not every intermediate state, to avoid redundant API calls).

6. **Staff Notification:** Revenue Manager receives an alert: "Booking.com sync unavailable for {duration}. {n} availability updates queued. Manual rate check recommended."

**Resilience Mechanisms**
- *Circuit Breaker:* Prevents resource exhaustion during OTA outage. Pattern: Hystrix / Resilience4j.
- *Retry with Exponential Backoff:* Before tripping the circuit breaker, individual requests retry with backoff: 1s, 2s, 4s, 8s (maximum 4 retries).
- *Offline Queue:* Persistent queue with at-least-once delivery semantics. Queue consumers use idempotency keys on the OTA's side to prevent duplicate updates.
- *Dead Letter Queue:* Updates that fail after queue replay are moved to a dead letter queue for manual review.

**Data Consistency Guarantees**
The system guarantees that, after recovery, Booking.com's availability state eventually converges to the correct state as of the end of the outage. There is no guarantee of consistency during the outage window.

**Guest Impact**
- During outage: potential for bookings on Booking.com for rooms that are no longer available (if stop-sell was not applied).
- Any double bookings created during the outage are handled per EC-RES-003.

**Recovery SLO**
- Detection to alert: < 5 minutes.
- Alert to stop-sell attempt: < 2 minutes.
- Queue replay to full sync: < 10 minutes after OTA API recovers.

**Test Cases**
- *TC-1:* Simulate Booking.com API returning 503 for 5 minutes. Assert circuit breaker opens within 3 failures, stop-sell is attempted, and the offline queue accumulates updates.
- *TC-2:* API recovers after 10 minutes. Assert the queue is replayed and the final availability state on Booking.com matches the PMS state.
- *TC-3:* Booking.com API recovers but then fails again during queue replay. Assert the queue does not lose events and retries correctly.

---

## EC-API-002 — POS Terminal Offline (Restaurant Charges Cannot Post)

*Category:* API and Integration
*Severity:* High
*Likelihood:* Medium (POS systems on hotel networks are vulnerable to local network issues, software updates, and power cycles)
*Affected Services:* POSIntegrationService, FolioService, RestaurantPOSAdapter, OfflineQueueService

**Description**
The restaurant's POS terminal loses connectivity to the HPMS. A guest orders breakfast and charges it to their room, but the POS cannot reach the HPMS to post the charge. The restaurant completes the transaction (the guest eats and leaves), but the charge is not reflected in the guest's folio. At checkout, the guest may be undercharged, creating a revenue loss and an awkward correction.

**Trigger Conditions**

1. `RestaurantPOSAdapter.post_room_charge()` fails to connect to HPMS (network error, timeout, or HPMS API down).
2. The POS terminal's offline mode is activated.
3. The guest completes the restaurant transaction while the POS is offline.

**Expected System Behaviour — Offline Mode**

1. POS terminal detects connectivity failure (after 3-second timeout on health check).
2. POS transitions to `OFFLINE_MODE`. A visual indicator appears on the POS screen: "⚠ Offline — charges will sync when connection is restored."
3. Restaurant staff can continue processing room charges. Each charge is stored locally in the POS terminal's offline queue: `{room_number, guest_name, amount, items, timestamp, idempotency_key}`.
4. The POS attempts to reconnect every 30 seconds (exponential backoff up to 5 minutes between attempts).
5. When connectivity is restored:
   a. The POS sends all queued charges to HPMS in chronological order.
   b. Each charge uses the stored `idempotency_key` to prevent duplicate posting.
   c. HPMS confirms each charge and sends an acknowledgement back to the POS.
   d. Charges are removed from the offline queue only after HPMS confirmation.
6. HPMS FolioService posts each charge to the correct guest folio based on room number and validates that the guest is currently checked in.

**Edge Sub-Case: Guest Checks Out Before Sync**
If the guest checks out while the POS is still offline and the charge has not synced:
1. The checkout process triggers a `CHECK_PENDING_POS_CHARGES` lookup.
2. If no pending POS charges can be confirmed (POS still offline), the agent is warned: "POS system is offline. There may be unposted charges from restaurant/bar outlets. Manual verification recommended."
3. The agent manually checks with the restaurant manager for any open room charges before completing checkout.
4. When the POS comes back online, any charges for a now-checked-out guest are posted to their folio and flagged as `POST_CHECKOUT_CHARGE`, triggering a card charge attempt.

**Staff Fallback Procedure**
1. Restaurant staff note the room number and amount on a paper charge slip.
2. On POS recovery, staff verify that all paper slips have been synced.
3. Front Desk Supervisor reviews the `POST_CHECKOUT_CHARGE` report each morning.

**Monitoring and Alerting**
- *Alert:* `POSOfflineDetected` — fires when the POS health check fails 3 consecutive times. Notifies Front Office Manager and IT support.
- *Alert:* `POSOfflineQueueGrowing` — fires when the offline queue > 10 items. Escalates to Senior IT.
- *Metric:* `pos.offline_queue_length` — should return to 0 within 5 minutes of connectivity being restored.

**Recovery SLO**
- Detection to alert: < 2 minutes.
- Connectivity restored to queue sync complete: < 5 minutes.
- Post-checkout charge recovery: same business day.

**Test Cases**
- *TC-1:* POS goes offline. Process 5 room charges. Assert all 5 are in the offline queue and none are posted to HPMS folios yet.
- *TC-2:* POS reconnects. Assert all 5 charges are posted in order, each with its idempotency key, and none are duplicated.
- *TC-3:* Guest checks out while POS is offline with 2 unposted charges. Assert front-desk agent receives a warning and the charges are posted to the settled folio when the POS reconnects.

---

## EC-API-003 — Keycard System Failure at Check-In

*Category:* API and Integration
*Severity:* Critical
*Likelihood:* Low
*Affected Services:* KeycardService, CheckInService, FrontDeskService, SecurityService

**Description**
The keycard encoding system (integrated with the PMS via a local or cloud-based API) fails at the moment a guest is being checked in. The guest cannot receive a working room key. This is a Critical scenario because the guest cannot access their room — they have completed check-in financially and administratively, but they are physically blocked. Unlike most digital failures, this one has an immediate physical consequence that cannot be remediated with a software fix alone.

**Trigger Conditions**

1. `KeycardService.encode_card(room_id, guest_id, checkin_datetime, checkout_datetime)` returns an error or times out.
2. The keycard encoder hardware is offline, the keycard management software (e.g., Assa Abloy, Dormakaba, SALTO) API is unreachable, or the encoder is physically jammed.
3. The guest is standing at the front desk expecting to receive their key.

**Expected System Behaviour**

1. `CheckInService` calls `KeycardService.encode_card()`. On failure, the system retries once after a 3-second delay.
2. If retry also fails: front desk agent receives an alert on their workstation: "Keycard encoding failed for Room {X}. Try encoder 2, or use emergency master key protocol."
3. Agent immediately attempts encoding on a backup keycard encoder (if available).
4. If all encoders are offline: agent escalates to Security, who provides the guest with a temporary physical master key (a keyed metal key for the room, held in the physical key safe).
5. Security logs the master key issuance: `POST /security/master-key-issuance {room_id, guest_id, issued_by, reason, timestamp}`.
6. IT is alerted: `KeycardSystemFailure` — P1. Estimated resolution time communicated to front desk.
7. When the keycard system is restored, new keycards are encoded for all guests who received master keys, and the master keys are collected.

**Data Consistency**
- The reservation is marked `CHECKED_IN` even if the keycard encoding failed (the check-in is complete; only the physical key is pending).
- A `KEYCARD_PENDING` flag is set on the reservation to prompt follow-up once the system is restored.

**Guest Impact**
- The guest experiences a delay and the inconvenience of using a metal key rather than a contactless keycard.
- If mobile key (app-based entry) is available and enabled for the property: the agent offers mobile key as an immediate alternative.
- Goodwill gesture: complimentary drink voucher for the inconvenience.

**Security Implications**
- Master key issuance creates a physical security audit record that must be reviewed by Security Manager daily.
- All master keys must be returned and reconciled before the end of each shift.
- If a master key is not returned, an immediate room lock change is triggered.

**Monitoring and Alerting**
- *Alert:* `KeycardEncoderFailure` — severity Critical. Immediate notification to IT and Security.
- *Metric:* `keycard.encode_success_rate` — alert if < 100% over a 5-minute window.

**Test Cases**
- *TC-1:* Keycard encoder API returns 503. Assert retry fires after 3 seconds and front-desk alert appears on second failure.
- *TC-2:* Mobile key is available. Assert agent is prompted to offer mobile key before falling back to physical master key.
- *TC-3:* Master key is issued and system is restored. Assert the system prompts staff to replace master key with encoded keycard and collect the physical key.

---

## EC-API-004 — Payment Gateway Timeout During Checkout

*Category:* API and Integration
*Severity:* Critical
*Likelihood:* Medium
*Affected Services:* PaymentService, CheckoutService, FolioService, IdempotencyService

**Description**
During checkout, the payment gateway (Stripe, Adyen, or similar) takes longer than the configured timeout to respond to a charge request. The system does not know whether the charge succeeded on the gateway's side — the network request may have been received and processed, or it may have failed before reaching the gateway. Without an idempotency-aware recovery mechanism, a naive retry will double-charge the guest.

**Trigger Conditions**

1. `PaymentService.charge(amount, card_token, idempotency_key)` HTTP request does not receive a response within the configured timeout (default: 10 seconds).
2. A `TimeoutException` is thrown.
3. No explicit success or failure response was received.

**Expected System Behaviour**

1. The first charge attempt is sent with a unique `idempotency_key = SHA256(folio_id + attempt_number + date)`.
2. After a 10-second timeout, the system enters recovery mode.
3. `IdempotencyService.check_charge_status(idempotency_key)` is called against the gateway's idempotency endpoint.
   - If the gateway confirms the charge was processed: proceed with checkout — the charge succeeded.
   - If the gateway confirms the charge was not processed: retry the charge with the same `idempotency_key` (idempotent retry — safe to call multiple times).
   - If the gateway is unavailable for the idempotency check: the folio is placed in `PAYMENT_UNCERTAIN` state. The guest is informed that checkout is processing and they will be notified within 5 minutes.
4. A background job polls the idempotency endpoint every 60 seconds for up to 10 minutes.
5. On resolution: if paid, checkout completes. If failed, front desk is notified to complete payment via an alternative method.

**Idempotency Requirements**
The idempotency key architecture is critical for this edge case:
- Key generation: `idempotency_key = base64(sha256(folio_id + ':' + attempt_sequence + ':' + utc_date))`.
- The key is stored against the charge attempt in the database before the gateway request is made.
- The same key is reused for all retries of the same charge attempt.
- A new key is generated only when the agent deliberately initiates a new payment attempt (not a retry).

**Data Consistency Guarantees**
- At-most-once charging: the idempotency key guarantees the gateway processes the charge exactly once, even if the request is submitted multiple times.
- The folio balance is not decremented until a confirmed success response (or idempotency check confirmation) is received.

**Staff Fallback Procedure**
1. If the background job does not resolve within 10 minutes: agent processes the payment offline (on a paper imprinter or via a manual card terminal not connected to the PMS).
2. The manual payment reference is entered into the folio as an `OFFLINE_PAYMENT` entry.
3. When the gateway status is eventually confirmed, the duplicate charge (if any) is immediately refunded.

**Recovery SLO**
- Timeout detection to idempotency check: < 15 seconds.
- Idempotency check to resolution: < 5 minutes.
- Maximum total time in `PAYMENT_UNCERTAIN` state: 10 minutes before manual intervention.

**Test Cases**
- *TC-1:* Gateway times out but the charge was processed. Assert idempotency check returns success and checkout completes without a duplicate charge.
- *TC-2:* Gateway times out and the charge was NOT processed. Assert idempotency check returns not-found, a retry is made with the same key, and the charge succeeds.
- *TC-3:* Idempotency endpoint is also unavailable. Assert the folio enters PAYMENT_UNCERTAIN state and the background polling job fires.

---

## EC-API-005 — Duplicate OTA Webhook Delivery

*Category:* API and Integration
*Severity:* High
*Likelihood:* High (webhook duplication is common; OTAs retry on any non-2xx response, including 504 gateway timeouts from the hotel's side)
*Affected Services:* WebhookIngestionService, ReservationService, IdempotencyService, NotificationService

**Description**
An OTA delivers the same booking webhook multiple times. This occurs when the hotel's webhook endpoint returns a timeout or a 5xx error during the first delivery, causing the OTA to retry. If the hotel's endpoint processed the first request (created the reservation) but returned a timeout before responding 200 OK, a second delivery of the same webhook creates a duplicate reservation.

**Trigger Conditions**

1. OTA delivers `POST /webhooks/booking-created` with `booking_ref = OTA-12345`.
2. `WebhookIngestionService` processes the webhook and creates a reservation in the PMS.
3. The response to the OTA times out (e.g., due to database slowness during the reservation creation).
4. OTA retries the webhook delivery after 60 seconds: another `POST /webhooks/booking-created` with the same `booking_ref = OTA-12345`.

**Expected System Behaviour**

1. `WebhookIngestionService` extracts the `booking_ref` from every incoming webhook.
2. Before processing: `IdempotencyService.check_processed(booking_ref)` — query `processed_webhooks` table.
3. If the `booking_ref` has already been processed: return HTTP 200 OK immediately (acknowledging the duplicate without reprocessing). Log: `INFO - Duplicate webhook received and acknowledged: booking_ref=OTA-12345`.
4. If the `booking_ref` has NOT been processed:
   a. Insert a record into `processed_webhooks(booking_ref, status='processing', received_at=NOW())`.
   b. Process the reservation creation.
   c. On success: update `processed_webhooks(booking_ref, status='completed')`.
   d. Return HTTP 200 OK.
5. If the processing fails between steps (a) and (c), the `status` remains `'processing'`. A background job identifies stale `processing` records (older than 5 minutes) and either retries or flags for manual review.

**Data Consistency Guarantees**
- Exactly-once reservation creation: the idempotency table ensures that even if the webhook is delivered 10 times, the reservation is created exactly once.
- The `processed_webhooks` table must be durable (not in-memory cache) and must survive service restarts.

**Monitoring and Alerting**
- *Metric:* `webhook.duplicate_rate_per_ota` — acceptable threshold < 5%. Above 5% suggests the hotel's endpoint is responding too slowly and the OTA is retrying frequently.
- *Alert:* `WebhookDuplicateRateHigh` — suggests underlying performance issue.

**Test Cases**
- *TC-1:* Same webhook delivered twice with a 60-second gap. Assert the first creates a reservation and the second returns 200 OK without creating a duplicate.
- *TC-2:* The service restarts between the first and second delivery. Assert the `processed_webhooks` table persists through the restart and the second delivery is correctly identified as a duplicate.
- *TC-3:* Webhook with `booking_ref = null`. Assert the system rejects the webhook with HTTP 400 (booking_ref is required for idempotency) and creates an alert.

---

## EC-API-006 — Channel Manager Complete Outage During Peak Booking Period

*Category:* API and Integration
*Severity:* Critical
*Likelihood:* Low (but impact is very high when it occurs)
*Affected Services:* ChannelManager, AllOTAAdapters, ReservationService, InventoryService, RevenueManagementService

**Description**
The channel manager service (the component that synchronises inventory and rates across all OTA channels) experiences a complete outage lasting 12 or more hours. During this time, neither availability updates nor rate changes can be pushed to any OTA. Bookings may continue arriving from OTAs at stale rates and stale availability. If the hotel is near full capacity, this creates double-booking risk. If rates were updated before the outage (e.g., a rate drop was scheduled), the OTAs continue showing the old, higher rates.

**Trigger Conditions**

1. `ChannelManager.health_check()` returns a failure for all channels simultaneously.
2. The outage duration exceeds 1 hour (distinguishing from a transient hiccup).
3. The hotel is in a high-occupancy period (> 80% confirmed).

**Expected System Behaviour**

1. **Detection (T+0):** ChannelManager health check fails. `ChannelManagerOutage` alert fires (severity Critical). On-call engineer is paged.
2. **Immediate Response (T+5 min):** All OTA channel adapters transition their circuit breakers to `OPEN`. Incoming webhooks continue to be accepted (reservations still flow in) but outgoing updates are queued.
3. **Risk Assessment (T+10 min):** ReservationService calculates the current occupancy risk: if confirmed reservations + overbooking buffer > physical capacity for any date in the next 7 days, an `INVENTORY_CLOSE_REQUIRED` alert fires.
4. **Manual Stop-Sell (T+15 min):** Revenue Manager is notified and manually logs into each OTA extranet portal to stop-sell rooms that are at risk of overbooking. This is the manual fallback for the automated channel manager.
5. **Queue Accumulation:** All inventory update and rate change events are written to the persistent offline queue with timestamps.
6. **Recovery:** When the channel manager is restored, the offline queue is replayed. However, rate changes that were scheduled during the outage must be reviewed by the Revenue Manager before replay — stale rate drops applied post-outage may be commercially incorrect.
7. **Post-Recovery Audit:** All reservations received during the outage are audited against inventory to confirm no double bookings occurred.

**Blast Radius**
A channel manager outage affects:
- All OTA channels simultaneously (Booking.com, Expedia, Agoda, Hotels.com, Airbnb for Hotels).
- Rate parity across channels (if rates change manually on one channel during the outage, parity is lost).
- Revenue management decisions (if the RM cannot push new rates in response to competitive pricing).

**Staff Fallback Procedures**
1. Revenue Manager maintains OTA extranet login credentials in the hotel safe (printed).
2. Manual inventory update procedure: log into each OTA portal, set availability to 0 for any dates where `confirmed_count >= physical_capacity * 0.98`.
3. Update the channel manager status board (physical whiteboard in the Revenue office) with which channels have been manually closed.
4. Resume automated updates via the channel manager once it recovers.

**RTO/RPO Targets**
- Recovery Time Objective (RTO): channel manager restored to full function within 4 hours.
- Recovery Point Objective (RPO): no inventory updates lost — the offline queue must replay all events in order.

**Post-Incident Review Steps**
1. Root cause analysis of the outage (infrastructure, software bug, dependency failure).
2. Review all bookings received during the outage for double-booking risk.
3. Assess any revenue impact from rates not being updated during the outage.
4. Update the manual fallback procedure if gaps were identified.

**Test Cases**
- *TC-1:* Channel manager fails for 30 minutes. Assert all OTA adapters' circuit breakers open and the offline queue accumulates updates.
- *TC-2:* Channel manager restores after 3 hours. Assert the offline queue replays all events and does not replay rate changes without Revenue Manager approval.
- *TC-3:* A double booking occurs during the outage. Assert the post-recovery audit detects it and creates a resolution task.

---

## Edge Case Summary Matrix

| ID | Title | Severity | Likelihood | Priority | Primary Resilience Mechanism | Recovery SLO |
|----|-------|----------|------------|----------|-----------------------------|----|
| EC-API-001 | OTA Sync Failure (Booking.com) | High | Medium | P2 | Circuit breaker + offline queue + stop-sell | < 10 min after OTA recovery |
| EC-API-002 | POS Terminal Offline | High | Medium | P2 | POS offline mode + local queue | < 5 min after reconnect |
| EC-API-003 | Keycard System Failure | Critical | Low | P1 | Backup encoder + physical master key | 4 hours max |
| EC-API-004 | Payment Gateway Timeout | Critical | Medium | P1 | Idempotency key + gateway check | < 10 min |
| EC-API-005 | Duplicate OTA Webhook | High | High | P2 | Idempotency table with durable storage | Immediate (< 1 ms per check) |
| EC-API-006 | Channel Manager Outage | Critical | Low | P1 | Offline queue + manual OTA extranet fallback | RTO: 4 hours |
