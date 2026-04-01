# Hotel Property Management System — Edge Cases: Room Assignment and Housekeeping

## Overview

Room assignment and housekeeping are the operational backbone of the hotel. Every guest experience promise — the confirmed room type, the view, the bed configuration, the cleanliness — is delivered through these two closely linked functions. Edge cases in this domain combine physical reality (a room that is genuinely dirty, genuinely broken, or genuinely occupied) with digital state (the PMS's record of that room's status). When these two diverge, the front desk bears the consequences. This file documents the six most consequential scenarios in detail.

---

## EC-HSK-001 — Room Not Ready at Check-In Time (Housekeeping Delay)

*Category:* Room Assignment and Housekeeping
*Severity:* High
*Likelihood:* Very High
*Affected Services:* HousekeepingService, RoomService, FrontDeskService, NotificationService, TaskManagementService

**Description**
At 15:00 (standard check-in time), a guest's assigned room is still in status `DIRTY` because the previous occupant checked out late, or because the housekeeping team experienced a coverage gap, or because a room inspection failed and the room was returned to the cleaning queue. This is the most common operational edge case in hospitality and the most visible to guests. It requires a combination of real-time room status tracking, housekeeper task prioritisation, and proactive guest communication.

**Trigger Conditions**

1. Guest reservation has a check-in time of 15:00 and the assigned room is in status `DIRTY` or `CLEANING_IN_PROGRESS` at 14:45.
2. The system has not yet flagged this room for priority cleaning.
3. No equivalent clean room is available for reassignment.

**Expected System Behaviour**

1. At 14:30, HousekeepingService runs a pre-check-in scan: `SELECT room_id, status FROM rooms WHERE checkin_expected_at BETWEEN NOW() AND NOW() + INTERVAL '30 minutes' AND status NOT IN ('CLEAN_INSPECTED', 'CLEAN_UNINSPECTED')`.
2. Any room still dirty with an imminent check-in triggers a `PRIORITY_CLEAN_TASK` pushed to the housekeeper mobile app.
3. FrontDeskService is notified: "Room {X} not ready for check-in at 15:00. Estimated ready time: {est}."
4. Agent reviews alternatives: `GET /rooms/available-clean?type={type}&floor_preference={pref}`. If a comparable room is available clean, the system prompts an automatic reassignment.
5. If no clean room is available, the guest is added to the `AWAITING_ROOM_QUEUE` with an estimated time and offered lobby amenities.
6. When the room transitions to `CLEAN_INSPECTED`, an automated SMS/push notification is sent to the guest.
7. The delay is recorded as a `HOUSEKEEPING_DELAY_INCIDENT` for the weekly operations review.

**System Detection**
- *Monitoring:* `rooms.dirty_at_checkin_rate` gauge — alert if > 5% of expected check-ins have a dirty assigned room at T-30 minutes.
- *Log Pattern:* `WARN HousekeepingService - Room {id} not clean for imminent check-in: guest={id} checkin={time} current_status={status}`.

**Automated vs Manual Steps**
- *Automated:* Priority task creation, alternative room search, guest SMS notification on room readiness.
- *Manual:* Housekeeper physically cleans and inspects the room; front-desk agent communicates delay to guest and manages lobby queue.

**Guest Communication**
- Proactive: pre-arrival message mentions that early check-in is subject to room availability.
- On arrival: honest estimate of wait time, offer of complimentary beverage and luggage storage.
- On resolution: instant notification via mobile app and personal apology from agent.

**Compensation Policy**
- Delay < 30 minutes: lobby coffee or water, no charge.
- Delay 30–60 minutes: F&B voucher up to $20, no supervisor approval required.
- Delay > 60 minutes or > 90 minutes total wait: room upgrade (if available) or $50 F&B credit, requires Front Office Manager approval.
- Delay > 2 hours: complimentary room rate for the night, requires General Manager approval.

**Financial Posting**
Compensation is posted as `COMP_HOUSEKEEPING_DELAY` with the agent ID and approval authority. The incident is flagged in the weekly revenue dilution report.

**Resolution Path**
1. Identify the root cause: late checkout from prior guest, housekeeper shortage, or inspection failure.
2. If late checkout was the cause: ensure late checkout fee was posted (see EC-CHK-002) or that a waiver was authorised.
3. Update housekeeper scheduling if a pattern of delays is found.

**Test Cases**
- *TC-1:* Room is DIRTY at 14:45 with a 15:00 check-in. Assert priority task is created and agent is notified.
- *TC-2:* Clean alternative room is available. Assert the system prompts an automatic reassignment offer.
- *TC-3:* Room is clean at 15:30 (30-minute delay). Assert guest SMS is sent within 60 seconds of status change, and $20 F&B voucher is posted.

---

## EC-HSK-002 — Maintenance Emergency Forces Guest Relocation Mid-Stay

*Category:* Room Assignment and Housekeeping
*Severity:* Critical
*Likelihood:* Low
*Affected Services:* MaintenanceService, RoomService, FrontDeskService, FolioService, GuestCommunicationService

**Description**
A guest is mid-stay (e.g., night 2 of a 5-night stay) when a maintenance emergency occurs in their room: a pipe bursts, the HVAC system fails and the room temperature is uncontrollable, a cockroach infestation is discovered during routine housekeeping, or the in-room safe has trapped a guest's valuables and cannot be opened. The guest must be relocated to a different room — ideally of equal or superior quality — with as little disruption as possible.

**Trigger Conditions**

1. A maintenance request or housekeeping incident report for the guest's current room is escalated to severity `EMERGENCY` or `UNINHABITABLE`.
2. The room cannot be made guest-ready within 2 hours.
3. The guest is currently checked in to the room.

**Expected System Behaviour**

1. Maintenance Supervisor or Housekeeper files an emergency report via the mobile app: `POST /maintenance/incident {room_id, severity: "EMERGENCY", description: "pipe burst", uninhabitable: true}`.
2. RoomService immediately transitions the room to status `OUT_OF_ORDER_EMERGENCY`.
3. ReservationService identifies the current guest: `SELECT guest_id, reservation_id FROM reservations WHERE room_id = ? AND status = 'CHECKED_IN'`.
4. FrontDeskService creates a relocation task with `CRITICAL` priority: "Guest {name} in Room {X} must be relocated — room is uninhabitable. Suggested alternatives: [list of available clean rooms of same or superior type]."
5. The system automatically selects the best available relocation room based on guest profile preferences (floor preference, view preference, bed configuration) from their loyalty profile.
6. A front desk agent personally goes to the guest's room (or calls) to explain the situation and escort the guest to the new room.
7. The original room's folio charges continue under the same folio number; the new room's system-generated charges are automatically mapped to the same folio.
8. All keycard access is transferred: the old room keycard is deactivated, new keycards are issued for the new room.
9. Housekeeping moves the guest's luggage (with guest's explicit permission) if the guest cannot do so themselves.

**Compensation Policy**
- Relocation to equal room: sincere apology, bottle of wine or equivalent amenity in the new room.
- Relocation to lesser room: rate difference refunded for each affected night + $50 inconvenience credit.
- Relocation to superior room: no upcharge; upgraded rate does not apply (guest is not charged more due to our failure).
- More than 2 relocations in a single stay: complimentary night's rate waived + General Manager personal apology.

**Financial Posting**
- `RELOCATION_COMPENSATION` folio entry for any credits given.
- Room rate difference adjustment if downgraded: `RATE_ADJUSTMENT_DOWNGRADE` credit.
- If the emergency caused property damage (e.g., guest's clothing was damaged by the pipe burst), a `PROPERTY_DAMAGE_CLAIM` folio entry is created and referred to insurance.

**Resolution Path**
1. Contain the maintenance emergency (shut off water, dispatch repair crew, etc.).
2. Complete the guest relocation before informing the guest of the emergency (where possible, so the new room is ready).
3. Ensure the new room is clean, inspected, and has the amenity placed before the guest arrives.
4. Document the incident in MaintenanceService with estimated repair time and actual repair time.
5. When the original room is restored, it must pass a full inspection before it can be returned to inventory.

**Test Cases**
- *TC-1:* Pipe burst reported for occupied room. Assert room transitions to OUT_OF_ORDER_EMERGENCY and relocation task is created within 60 seconds.
- *TC-2:* No equivalent room available — only a lesser room. Assert rate adjustment credit is calculated and posted automatically.
- *TC-3:* Guest's belongings must be moved. Assert the system prompts for explicit guest consent before flagging the task as ready for housekeeping action.

---

## EC-HSK-003 — Room Downgrade Required (Assigned Room Out of Order)

*Category:* Room Assignment and Housekeeping
*Severity:* High
*Likelihood:* Medium
*Affected Services:* RoomService, ReservationService, FrontDeskService, FolioService, YieldManagementService

**Description**
A guest booked a Superior Ocean View King room. On check-in day, the assigned room (or all rooms of that type) is placed out of order due to a maintenance issue discovered during the morning inspection. No other Ocean View King rooms are clean and available. The only available option is a Standard Garden View King room, which is a downgrade in both view and room tier. The guest must be informed diplomatically, compensated appropriately, and the financial adjustment must be posted correctly.

**Trigger Conditions**

1. An `OUT_OF_ORDER` status is applied to the guest's assigned room (or all rooms of the booked type) on the check-in day.
2. No equivalent or superior rooms are available in clean status.
3. The guest is arriving within 4 hours.

**Expected System Behaviour**

1. RoomService detects that all rooms of `type = SUPERIOR_OCEAN_VIEW_KING` are `OUT_OF_ORDER` or `OCCUPIED`.
2. YieldManagementService is called to find the nearest comparable substitution: `GET /rooms/substitution-candidates?type=SUPERIOR_OCEAN_VIEW_KING&required_checkin=today`.
3. FrontDeskService receives an alert: "Downgrade required for guest {name} — check-in today. Best available alternative: Standard Garden View King (2 available clean). Rate differential: $60/night."
4. Front desk supervisor is notified (not just the agent) because a downgrade requires supervisor-level approval.
5. A rate adjustment is automatically calculated: `rate_differential = original_rate - substitute_rate` multiplied by the number of downgraded nights.
6. A `DOWNGRADE_RATE_CREDIT` is posted to the folio for each affected night.
7. Agent calls the guest before arrival (if time allows) to explain and apologise.
8. The agent is scripted: acknowledge the inconvenience, confirm the rate credit, offer an additional goodwill gesture.

**Compensation Policy**
- Rate differential for each affected night (mandatory, applied automatically).
- Complimentary room service item or F&B voucher ($30–$50) as goodwill.
- If the full stay is downgraded and the guest objects: option to cancel with no penalty and full refund (even if within the cancellation window, because the downgrade is the hotel's fault).
- If the guest agrees to stay: upgrade at no charge for the first available night of the correct room type if the stay continues.

**Financial Posting**
- `DOWNGRADE_RATE_CREDIT`: automatic per-night.
- `COMP_DOWNGRADE_GOODWILL`: manual, requires supervisor approval, capped at $50 without General Manager approval.

**Test Cases**
- *TC-1:* All Superior Ocean View King rooms go OUT_OF_ORDER. Assert front desk alert fires and downgrade credit is calculated.
- *TC-2:* Guest refuses downgrade and requests cancellation. Assert full refund is processed without a cancellation penalty fee.
- *TC-3:* Guest is upgraded from downgrade room to correct room type on day 2. Assert rate adjustment is reversed for night 2 onwards.

---

## EC-HSK-004 — All Housekeepers Unavailable (Shift Coverage Gap)

*Category:* Room Assignment and Housekeeping
*Severity:* Critical
*Likelihood:* Low
*Affected Services:* HousekeepingService, TaskManagementService, StaffSchedulingService, FrontDeskService

**Description**
A housekeeping shift has no coverage due to mass sick call, a transportation disruption, or a scheduling system error. The rooms scheduled for cleaning cannot be cleaned in time for afternoon check-in. This is a Critical scenario because it affects the entire hotel's check-in capacity — not just individual rooms. The system must detect the coverage gap early and escalate to hotel management so that contingency measures (calling in off-duty staff, using a contract cleaning service, or delaying check-ins with compensation) can be activated.

**Trigger Conditions**

1. `StaffSchedulingService.shift_coverage_rate` for the housekeeping shift falls below 50% (fewer than half the scheduled housekeepers are available).
2. The shift in question is the primary check-out cleaning shift (typically 08:00–14:00).
3. The shortfall is detected fewer than 3 hours before the shift start.

**Expected System Behaviour**

1. StaffSchedulingService receives shift cancellations (via mobile app or phone call logged by manager): `POST /staff/shift-cancellation {staff_id, shift_id, reason}`.
2. When coverage drops below 80%, a `LOW_COVERAGE_WARNING` alert is sent to the Housekeeping Manager and Front Office Manager.
3. When coverage drops below 50%, a `CRITICAL_COVERAGE_GAP` alert is escalated to the General Manager.
4. The system automatically calculates the cleaning capacity shortfall: `rooms_to_clean - (available_housekeepers * rooms_per_housekeeper_per_shift)` = unserviceable rooms.
5. The system queries the departure list and prioritises rooms where the arriving guest has a same-day check-in, ordering them by guest loyalty tier and booking value.
6. FrontDeskService is updated: check-in delays are anticipated for the bottom N% of the priority list. The front desk is given an estimated room-ready time for each affected reservation.
7. Pre-arrival messages are sent to affected guests: "Due to unforeseen operational circumstances, your room may not be ready at our standard check-in time of 15:00. We will notify you as soon as your room is ready and appreciate your patience."

**Immediate Response Runbook**

1. Housekeeping Manager calls all off-duty housekeepers (overtime rate applies).
2. Front Office Manager contacts contract cleaning services.
3. General Manager authorises any overtime costs.
4. Rooms are triaged: suites and VIP rooms are cleaned first, regardless of check-in time, because their guests are least tolerant of delays.
5. Standard rooms are cleaned in order of earliest-arriving guest.
6. All food and beverage staff who have housekeeping cross-training are deployed to assist.

**Compensation Trigger**
- Any guest who waits more than 30 minutes past 15:00 due to the coverage gap: $30 F&B voucher.
- Any guest who waits more than 90 minutes: $75 F&B credit and a 10% discount on a future booking.

**Detection**
- *Alert:* `HousekeepingCoverageGap` — fires when `shift_coverage_rate < 0.80` with severity High; re-escalates at `< 0.50` with severity Critical.
- *Log Pattern:* `CRITICAL StaffSchedulingService - Coverage gap: shift={id} scheduled={n} available={m} coverage_rate={r}`.

**Test Cases**
- *TC-1:* 6 of 10 scheduled housekeepers cancel. Assert CRITICAL_COVERAGE_GAP alert fires and GM is notified.
- *TC-2:* Priority cleaning list is generated. Assert VIP and suite rooms are at the top regardless of alphabetical or room number ordering.
- *TC-3:* Guest waits 90 minutes due to coverage gap. Assert $75 credit is posted automatically when the room-ready notification is sent.

---

## EC-HSK-005 — Room Status Mismatch (System Shows Clean, Room Is Dirty)

*Category:* Room Assignment and Housekeeping
*Severity:* High
*Likelihood:* Medium
*Affected Services:* HousekeepingService, RoomService, FrontDeskService, AuditService

**Description**
The PMS shows a room as `CLEAN_INSPECTED` and the front desk assigns it to a newly arriving guest. The guest uses their keycard to enter the room and finds it in a dirty state — unmade beds, used towels, previous guest's belongings potentially still in the room. This scenario results from a race condition in room status updates, a housekeeper marking a room clean without completing the task (fraud or negligence), or a system synchronisation failure between the mobile housekeeper app and the central PMS.

**Trigger Conditions**

1. Housekeeper marks room `CLEAN` in mobile app without physically cleaning it (accidental or deliberate).
2. Room inspector signs off on the status without visiting the room, OR the inspection step is bypassed in the workflow.
3. The PMS syncs the `CLEAN_INSPECTED` status.
4. Front desk assigns the room to an arriving guest.

**Expected System Behaviour**

1. The room should not be marked `CLEAN_INSPECTED` without an inspection step. The workflow: `DIRTY` → `CLEANING_IN_PROGRESS` → `PENDING_INSPECTION` → `CLEAN_INSPECTED`.
2. The `PENDING_INSPECTION` step requires a different staff member (the inspector, not the cleaner) to confirm the room quality via the inspector's mobile app, which triggers a geolocation check to confirm the inspector is physically near the room.
3. If the inspector's geolocation is > 20 metres from the room's registered coordinates, the inspection is flagged as `SUSPICIOUS_INSPECTION` and requires supervisor review.

**Failure Mode**
If the inspection step is bypassed or the geolocation check is absent:
- Guest enters a dirty room.
- Guest calls the front desk or posts a review immediately.
- Reputational damage is disproportionate: a dirty room is one of the top-rated negative experiences in hospitality reviews.

**Detection**
- *Monitoring:* `rooms.status_mismatch_incidents_per_day` — should be 0. Any value > 0 triggers an immediate investigation.
- *Guest-Reported:* Guest calls front desk. Agent must log this as a `ROOM_CONDITION_COMPLAINT` to create a formal record.
- *Audit:* Random physical inspection audits (inspector visits 5% of rooms marked CLEAN_INSPECTED daily without prior notice).

**Resolution**

1. Apologise to the guest immediately and move them to an alternative room.
2. Issue compensation appropriate to the severity (dirty towels: $30 F&B; previous guest's belongings: full night waived + security notification).
3. Investigate the discrepancy: review the housekeeper's mobile app log and geolocation data.
4. If the housekeeper marked the room clean falsely, initiate an HR investigation.
5. Review the last 5 rooms cleaned by the same housekeeper on the same shift for quality issues.

**Prevention**
- Mandatory two-step workflow: cleaner marks `PENDING_INSPECTION`, inspector marks `CLEAN_INSPECTED`. These must be different staff IDs.
- Geolocation validation on all inspection actions.
- Random daily spot-check audits logged in AuditService.
- AI-assisted room inspection tool (optional): tablet-based checklist with photo evidence required for sign-off.

**Test Cases**
- *TC-1:* Cleaner marks room CLEAN_INSPECTED without the inspector step. Assert the direct status transition is rejected.
- *TC-2:* Inspector signs off from 50 metres away. Assert `SUSPICIOUS_INSPECTION` flag and supervisor review task are created.
- *TC-3:* Guest reports dirty room. Assert a ROOM_CONDITION_COMPLAINT record is created and linked to the inspection audit trail.

---

## EC-HSK-006 — VIP Room Fails Final Inspection

*Category:* Room Assignment and Housekeeping
*Severity:* High
*Likelihood:* Low
*Affected Services:* HousekeepingService, VIPManagementService, FrontDeskService, GuestCommunicationService

**Description**
A returning VIP guest (loyalty platinum, major corporate account, or personally flagged by the General Manager) is scheduled to check in at 16:00. The room was cleaned and inspected at 13:00 and designated `CLEAN_INSPECTED`. At 15:30, the Executive Housekeeper conducts a final VIP inspection and identifies deficiencies: a stain on the carpet, a flickering lightbulb, the welcome amenity is the wrong type (the guest's profile indicates a nut allergy but the standard fruit and nut basket was placed). The room must be corrected before the guest arrives.

**Trigger Conditions**

1. Reservation has `vip_status = true` or `loyalty_tier = PLATINUM`.
2. VIP pre-arrival checklist is enabled for the property.
3. A VIP room inspection is scheduled 90 minutes before the guest's expected arrival time.
4. The inspection identifies one or more deficiencies that require corrective action.

**Expected System Behaviour**

1. VIPManagementService generates a pre-arrival VIP checklist at T-24 hours: room condition, amenity placement, in-room preferences (pillow type, newspaper, mini-bar pre-stocking, welcome message personalisation).
2. At T-90 minutes, the system sends a reminder to the Executive Housekeeper to conduct the VIP inspection.
3. If the inspection fails any item: the room transitions back to `PENDING_VIP_REINSPECTION` and a corrective action task is created with the specific deficiencies noted.
4. The estimated correction time is logged. If the correction cannot be completed before the guest arrives, FrontDeskService is notified.
5. If the room cannot be ready on time, the system searches for an alternative VIP-eligible room (same or superior type, same or higher floor, similar view).
6. The General Manager is notified of any VIP room deficiency — this is a personal touch that allows the GM to personally welcome the guest if there was a disruption.

**Compensation Policy**
- If the VIP experiences no disruption (correction completed on time): no compensation needed.
- If the VIP waits > 15 minutes due to a failed inspection: complimentary bottle of champagne or equivalent preference item, GM personal welcome note.
- If the VIP must be relocated to a different room: the rate difference is absorbed by the hotel (VIP is not charged less for a superior room if the original room was the issue).

**Staff Workflow**
1. Executive Housekeeper completes VIP inspection using the VIP inspection checklist in the mobile app.
2. Each checklist item is marked pass/fail with notes.
3. Failed items trigger immediate corrective tasks assigned to specific staff.
4. Final re-inspection is conducted and signed off before the arrival window.

**Test Cases**
- *TC-1:* VIP room fails inspection at T-90 minutes. Assert corrective tasks are created and the room transitions to PENDING_VIP_REINSPECTION.
- *TC-2:* Correction is completed at T-20 minutes. Assert the room transitions to CLEAN_VIP_APPROVED and the GM is notified.
- *TC-3:* VIP profile shows nut allergy. Assert the welcome amenity checklist flags the standard nut basket as incompatible and substitutes the approved alternative.

---

## Edge Case Summary Matrix

| ID | Title | Severity | Likelihood | Priority | Detection Method | Primary Prevention |
|----|-------|----------|------------|----------|------------------|--------------------|
| EC-HSK-001 | Room Not Ready at Check-In | High | Very High | P2 | Pre-check-in status scan at T-30 min | Priority clean task automation |
| EC-HSK-002 | Maintenance Emergency Relocation | Critical | Low | P1 | MaintenanceService EMERGENCY flag | Regular maintenance inspection schedule |
| EC-HSK-003 | Room Downgrade Required | High | Medium | P2 | OOO flag on booked room type at check-in | Preventive maintenance scheduling |
| EC-HSK-004 | All Housekeepers Unavailable | Critical | Low | P1 | Shift coverage rate < 50% alert | Cross-training; contract cleaning agreements |
| EC-HSK-005 | Room Status Mismatch | High | Medium | P2 | Guest complaint + audit random checks | Two-person inspection workflow + geolocation |
| EC-HSK-006 | VIP Room Fails Final Inspection | High | Low | P2 | VIP inspection checklist at T-90 min | Pre-arrival VIP checklist automation |
