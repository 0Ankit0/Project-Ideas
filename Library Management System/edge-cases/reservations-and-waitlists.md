# Edge Cases — Reservations and Waitlists

The reservation and waitlist subsystem coordinates title-level demand across multiple patrons, copies, branches, and concurrent operations. Failures in this subsystem manifest as silent queue corruption, unfulfilled holds, or patrons charged unfairly due to stale state. The edge cases below capture the highest-risk failure modes, their downstream impact, and the detection and mitigation strategies that prevent data loss or patron-facing errors. Every rule maps to at least one API endpoint, domain event, or enforced business rule (BR-xx) defined in the system specification.

---

## Failure Mode Reference Table

| Failure Mode | Impact | Detection | Mitigation / Recovery |
|---|---|---|---|
| **All copies checked out when reservation placed** — No available copies; patron added to waitlist | Patron expects immediate availability; silent WAITING state entry may go unnoticed | `POST /reservations` response body includes `status: WAITING` and `queue_position`; client must surface this to the patron | Return HTTP 202 with `ReservationCreated` event payload indicating WAITING status; enqueue the reservation atomically with current `reserved_at` timestamp; notify patron via primary channel that no copy is currently available and provide estimated wait based on average loan duration |
| **Reservation notification delivery failure** — Email and SMS both fail to deliver the hold notification | Patron never learns the item is on the hold shelf; 7-day clock (BR-05) runs down; item auto-cancels; queue advances without patron knowledge | Delivery receipts from the notification service are tracked in the `notification_attempts` table; a Dead Letter Queue (DLQ) alert fires after 3 failed attempts within 30 minutes | Apply notification cascade: attempt primary channel (email); on failure within 5 minutes attempt fallback channel (SMS); on second failure raise a `StaffAlertNotificationFailed` event; staff can manually contact patron or extend hold shelf by 2 days via admin override; log all attempts with `channel`, `error_code`, and `attempted_at` |
| **Multiple simultaneous reservation fulfillments** — Two items returned at the same time but only one reservation exists | Both return events attempt to fulfill the same reservation; duplicate `ReservationFulfilled` events emitted; second copy placed on hold shelf orphaned | Idempotency key on the Kafka consumer (`reservation_id + copy_id`) prevents double-processing; `reservations.status` column has a DB-level check constraint rejecting transitions from `ON_HOLD_SHELF` back to `ON_HOLD_SHELF` | The fulfillment consumer uses `SELECT FOR UPDATE` on the reservation row; only the first committed transaction succeeds; the second copy returns to `AVAILABLE` and triggers the next WAITING reservation in the queue; the second Kafka message is acknowledged and discarded after idempotency check |
| **Patron cancels reservation after hold period expires** — Reservation already expired; cancel request arrives late | `DELETE /reservations/{id}` is called after the scheduler has already transitioned status to `EXPIRED`; double-cancel produces a misleading 404 or 409 | `reservations.status` is checked before applying the cancellation state machine transition; `updated_at` timestamp compared to request receipt time in audit log | Return HTTP 409 with error code `RESERVATION_ALREADY_EXPIRED` and current status in the response body; emit no additional `ReservationCancelled` event; log the late cancellation attempt for audit; ensure the next patron in queue was already notified at expiry time so no re-notification is needed |
| **Item recalled from patron who is also on the waitlist** — Patron in position 5 also has an active loan of the same item | Patron simultaneously has an active loan and a waitlist reservation for the same title; on recall the loan due date resets to today+3 (BR-09); the reservation remains in queue creating a logical conflict | At recall time, query `reservations` for any WAITING entry where `patron_id` matches the recalled loan's `patron_id` and `title_id` matches | When recall is triggered, detect the duplicate and auto-cancel the WAITING reservation with reason code `PATRON_ALREADY_HAS_ACTIVE_LOAN`; emit `ReservationCancelled` with this reason; notify the patron that their waitlist position was released because they hold the current copy; advance all downstream queue positions atomically |
| **Waitlist position when patron is suspended** — Patron becomes suspended while at position 2 in the waitlist | If fulfillment proceeds at suspension time, the item is placed on hold for a patron who cannot collect it; the hold shelf slot is occupied unnecessarily for up to 7 days | Account status is re-validated at fulfillment time (the moment a returned copy is matched to the next eligible reservation); suspension events publish a `PatronSuspended` domain event consumed by the reservation service | At fulfillment, skip the suspended patron: set their reservation to `status: WAITING, skipped: true`; advance to position 3; emit `ReservationSkipped` event; notify the skipped patron that their hold was bypassed due to account suspension and their position will be restored once the suspension is lifted; do not permanently remove them from the queue |
| **Hold pickup branch mismatch** — Item returned to a different branch than the reservation pickup branch | Copy is available at Branch B but the reservation specifies pickup at Branch A; naive fulfillment places the hold at the wrong branch; patron travels to Branch A and finds nothing | `copies.current_branch_id` is compared to `reservations.pickup_branch_id` at fulfillment time; a mismatch triggers an in-transit workflow rather than direct hold placement | Create an `ItemTransfer` record with `origin_branch_id`, `destination_branch_id`, and `reservation_id`; set copy status to `IN_TRANSIT`; reservation status remains `WAITING`; notify patron that the item is being transferred and provide an estimated arrival date; only transition reservation to `ON_HOLD_SHELF` after the destination branch scans the item in |
| **Duplicate reservation detection** — Patron places the same reservation twice before the first one processes | Two WAITING reservations for the same `patron_id` and `title_id` enter the queue; patron occupies two positions unfairly; downstream fulfillment sends two notifications | Unique partial index on `reservations (patron_id, title_id)` where `status IN ('PENDING', 'WAITING', 'ON_HOLD_SHELF')`; `POST /reservations` checks for an existing active reservation before insert | Return HTTP 409 with error code `DUPLICATE_RESERVATION` and the existing reservation's `id` and `queue_position` in the response body; emit no `ReservationCreated` event; the idempotency key for the endpoint is `patron_id + title_id + date`; clients should surface the existing reservation rather than retrying |
| **Reservation fulfillment race condition** — Simultaneous checkout and reservation fulfillment for the same copy | A walk-in patron checks out the last copy at the same instant a return triggers fulfillment for a WAITING reservation; both operations read the copy as `AVAILABLE`; the reservation is marked `ON_HOLD_SHELF` but the copy is already loaned out | Database-level `SELECT FOR UPDATE SKIP LOCKED` on the `copies` row during both checkout and fulfillment; the losing transaction receives a lock timeout and is retried | The fulfillment service acquires the copy row lock first via the return processing pipeline; if the checkout transaction wins the lock instead, the fulfillment event is retried up to 3 times; after 3 retries without an available copy the reservation re-enters `WAITING` status and the patron is notified of the delay; all retry attempts are logged with `copy_id`, `transaction_type`, and `lock_wait_ms` |
| **Entire waitlist for an out-of-print item** — All copies lost or withdrawn; waitlist has 15 patrons | No future fulfillment is possible; 15 patrons are silently queued for an item that will never become available; queue occupies system resources and misleads patrons | Withdrawal of the last active copy triggers a check: if `copies WHERE title_id = X AND status != 'WITHDRAWN'` returns zero rows, fire a `TitleFullyWithdrawn` event | Consume `TitleFullyWithdrawn` in the reservation service; bulk-cancel all WAITING and PENDING reservations for the title with reason code `TITLE_NO_LONGER_AVAILABLE`; emit one `ReservationCancelled` event per patron; send patron notifications with a suggestion to place an inter-library loan request; staff receive a summary report of affected patrons for outreach |

---

## Waitlist Queue Ordering and Tie-Breaking

Reservations in WAITING status are ordered chronologically by `reserved_at` timestamp in ascending order (earliest reservation first). This guarantees strict FIFO semantics within the default queue and makes queue position deterministic and auditable.

When two or more WAITING reservations share identical `reserved_at` timestamps — possible when bulk imports or system migrations create entries — the tie-breaking rule applies membership tier priority in the following descending order: **Scholar > Premium > Standard > Basic**. A Scholar-tier patron with the same timestamp as a Standard-tier patron will receive the earlier queue position. Tier is resolved at queue position calculation time, not at reservation creation time, so a patron who upgrades their membership before fulfillment benefits from the updated tier rank.

Within the same tier and the same timestamp (an extremely rare edge case), queue position is broken by ascending `patron_id` (lexicographic) to ensure full determinism without any random element.

When a patron is skipped due to suspension (see row 6 in the table), their `queue_position` is logically preserved: all patrons behind them advance by one position, but the suspended patron's row retains a `skipped: true` flag and the original `reserved_at`. The atomic position update is executed inside a single database transaction that locks the affected reservation rows using `SELECT FOR UPDATE`; no partial queue state is ever visible to concurrent readers.

---

## Hold Shelf Workflow

A reservation progresses through the following states after a copy becomes available:

```
WAITING → IN_TRANSIT → ON_HOLD_SHELF → COLLECTED
                                      ↘ EXPIRED
```

- **WAITING**: The reservation is queued; no copy has been assigned yet.
- **IN_TRANSIT**: A copy has been matched to the reservation but is being transferred from another branch to the patron's preferred pickup branch.
- **ON_HOLD_SHELF**: The copy has arrived at the pickup branch and is physically placed on the hold shelf. The 7-day expiry clock starts at this exact transition time (`hold_shelf_expires_at = NOW() + 7 days`), enforced by business rule BR-05.
- **COLLECTED**: The patron completed checkout of the held copy; the reservation is closed successfully.
- **EXPIRED**: The patron did not collect the item within 7 calendar days. The scheduler runs every hour, selects reservations where `status = 'ON_HOLD_SHELF' AND hold_shelf_expires_at < NOW()`, transitions them to `EXPIRED`, releases the copy back to `AVAILABLE`, and triggers fulfillment for the next WAITING patron in queue.

The notification cascade operates as follows upon the `WAITING → ON_HOLD_SHELF` transition:

1. The system attempts delivery via the patron's primary notification channel (typically email) within 5 minutes.
2. If the primary channel returns a non-2xx delivery receipt or times out, the fallback channel (SMS) is attempted within 10 minutes of the original transition.
3. If both channels fail within 30 minutes, a `StaffAlertNotificationFailed` event is raised; staff can view the alert in the circulation dashboard and contact the patron directly or extend the hold shelf by up to 2 days.
4. All notification attempts are recorded in `notification_attempts (reservation_id, channel, status, attempted_at, error_code)` for audit and debugging.

A `HoldExpiredNotification` domain event is emitted when the scheduler expires a hold. This event triggers the next fulfillment cycle and sends a courtesy expired-hold notice to the patron.

---

## Reservation Fulfillment Concurrency

When a copy is returned, the return processing pipeline executes the following sequence to safely assign it to the next eligible reservation:

1. **Lock acquisition**: The pipeline issues `SELECT * FROM reservations WHERE title_id = ? AND status = 'WAITING' ORDER BY queue_position ASC LIMIT 1 FOR UPDATE` inside an open transaction. This prevents any concurrent return or fulfillment process from reading the same row simultaneously.

2. **Eligibility re-check**: Before committing the fulfillment, the selected patron's account is re-evaluated for borrowing blocks. Per BR-08, if the patron has an outstanding balance exceeding $25, the reservation is skipped and the lock is released to the next eligible row. The skipped patron's status is updated to `WAITING, skipped: true` and they are notified.

3. **Atomic state transition**: If the patron is eligible, the copy's status is set to `ON_HOLD_SHELF`, the reservation's status is set to `ON_HOLD_SHELF`, `hold_shelf_expires_at` is populated, and `copy_id` is written to the reservation row — all within the same transaction. No intermediate state is observable.

4. **Idempotency on the Kafka consumer**: The fulfillment event consumer (subscribed to the `copy.returned` topic) uses a composite idempotency key of `reservation_id + copy_id`. Before processing, it checks the `processed_fulfillment_events` table for an existing entry with the same key. If found, the message is acknowledged and discarded without side effects. This guards against duplicate delivery in at-least-once Kafka configurations.

5. **Domain event emission**: On successful fulfillment, a `ReservationFulfilled` domain event is published to the `reservation.events` topic. This event carries `reservation_id`, `copy_id`, `patron_id`, `title_id`, `pickup_branch_id`, and `hold_shelf_expires_at`. Downstream consumers include the notification service (triggers hold-ready message), the analytics pipeline (updates demand metrics), and the circulation dashboard (refreshes hold shelf view).

---

## Business Rules Summary

| Rule | Description |
|---|---|
| BR-03 | Renewals are blocked for a loan when one or more WAITING or ON_HOLD_SHELF reservations exist for the same title |
| BR-05 | Hold shelf expiry is 7 calendar days from the moment the copy transitions to ON_HOLD_SHELF; failed pickup triggers auto-cancel and advances the queue |
| BR-08 | Patron borrowing block threshold is $25 outstanding balance; this is re-checked at fulfillment time, not only at reservation creation |
| BR-09 | A recalled item has its loan due date reset to today + 3 calendar days regardless of original due date |

## API and Event Reference

| Resource / Event | Description |
|---|---|
| `POST /reservations` | Creates a new reservation; returns 202 with WAITING status if no copy is available, or 200 with ON_HOLD_SHELF if a copy is immediately assignable |
| `DELETE /reservations/{id}` | Cancels an active reservation; returns 409 if already EXPIRED or COLLECTED |
| `GET /reservations/{id}/position` | Returns current queue position, estimated wait, and reservation status in real time |
| `ReservationCreated` | Emitted on successful reservation creation; consumed by notification and analytics services |
| `ReservationFulfilled` | Emitted when a copy is assigned to a reservation; triggers hold-ready notification and shelf update |
| `HoldExpiredNotification` | Emitted when BR-05 expiry clock elapses; triggers patron notification and next-queue fulfillment |
| `ReservationCancelled` | Emitted on explicit cancel, skip due to suspension, or bulk cancel on title withdrawal; includes `reason_code` |
