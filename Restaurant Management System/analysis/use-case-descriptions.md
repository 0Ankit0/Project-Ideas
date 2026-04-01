# Use Case Descriptions — Restaurant Management System

## Introduction

This document provides detailed system-level use case descriptions for the Restaurant Management System (RMS). Each use case captures a discrete, observable interaction between a named actor and the RMS that yields a measurable business outcome. Use cases are technology-agnostic and are intended to drive feature development, REST/GraphQL API contract design, acceptance test scripting, and UAT sign-off.

**Document Scope**: Front-of-house (FOH), back-of-house (BOH), order lifecycle, kitchen display, billing, multi-tender payments, delivery integration, inventory receiving, discount and void governance, end-of-day accounting, and guest loyalty across single and multi-branch deployments.

**Notation Conventions**:
- `UC-XX` — Use Case identifier, numerically ordered by workflow phase
- `BR-XX` — Business Rule cross-reference (see `business-rules.md`)
- `AF-X` — Alternative Flow (valid, non-error deviation from Main Flow)
- `EF-X` — Exception Flow (error or boundary condition with defined system response)
- Actor names reflect roles; one staff member may hold multiple roles simultaneously.
- Arrow `→` in Exception Flows indicates the automated system response.

---

## Use Case Index

| UC ID | Title | Primary Actor | Module | Priority |
|-------|-------|---------------|--------|----------|
| UC-01 | Make Reservation | Guest / Host | Reservations | High |
| UC-02 | Seat Reserved Guest | Host | Front-of-House | High |
| UC-03 | Seat Walk-in Guest | Host | Front-of-House | High |
| UC-04 | Capture Dine-In Order | Waiter / Server | Ordering | Critical |
| UC-05 | Modify Existing Order | Waiter / Server | Ordering | High |
| UC-06 | Route Order to Kitchen | System | Kitchen Display | Critical |
| UC-07 | Prepare and Complete Kitchen Ticket | Chef / Kitchen Staff | Kitchen Display | Critical |
| UC-08 | Generate and Print Bill | Cashier / Waiter | Billing | Critical |
| UC-09 | Process Multi-Tender Payment | Cashier | Payments | Critical |
| UC-10 | Process Split Bill | Cashier / Waiter | Payments | High |
| UC-11 | Process Delivery Order | External Delivery Platform / Waiter | Delivery | High |
| UC-12 | Receive Inventory Goods | Manager / Inventory Staff | Inventory | High |
| UC-13 | Apply Discount or Void Item | Waiter / Manager | Ordering / Billing | High |
| UC-14 | Close End-of-Day Cash Session | Cashier / Manager | Accounting | Critical |
| UC-15 | Enroll in Loyalty Program and Redeem Points | Guest / Cashier | Loyalty | Medium |

---

## UC-01: Make Reservation

**Actor**: Guest / Host
**Supporting Actors**: Branch Manager (for overrides), Notification Service (automated)

**Preconditions**:
- The branch is open and accepting reservations for the requested date/time window.
- Table capacity, slot duration rules, and party-size constraints are configured in `BranchPolicy`.
- Guest contact information (phone or email) is available for confirmation.
- The requested date falls within the branch's bookable horizon (e.g., max 30 days ahead per BR-01).

**Main Flow**:
1. Guest (online/phone) or Host (POS terminal) initiates a new reservation by supplying `guest_name`, `party_size`, `requested_date`, `requested_time`, and optional `special_requests` (e.g., high chair, allergy note).
2. System queries the `TableAvailability` projection for the branch and date, filtering tables by `min_covers` ≤ `party_size` ≤ `max_covers` and `is_reservable = true`.
3. System presents one or more candidate `(table_id, slot_start, slot_end, section_name)` options ranked by preference score (minimise cover waste, prefer outdoor/indoor per guest preference).
4. Host or Guest selects a preferred slot; system creates a `Reservation` record with `status = HOLD` and sets `hold_expires_at = now() + BranchPolicy.reservation_hold_minutes`.
5. System sends a confirmation notification (SMS/email) containing `reservation_code`, date/time, party size, and cancellation instructions.
6. Host or Guest acknowledges; system transitions `Reservation.status` from `HOLD` to `CONFIRMED` and blocks the linked table slot in `TableAvailability`.
7. System schedules a reminder notification to the guest `BranchPolicy.reminder_hours_before` prior to the reservation time.

**Alternative Flows**:
- **AF-1**: Guest requests a specific table by `table_number` (e.g., window seat, private booth).
  1. System checks if the requested table is available for the slot and satisfies party-size constraints.
  2. If available, system bypasses ranked-choice and assigns directly; flow continues at step 4.
  3. If unavailable, system presents the closest available alternative with an explanation.
- **AF-2**: No tables available — Guest opts for the waitlist.
  1. System creates a `WaitlistEntry` with `status = WAITING`, `estimated_wait_minutes` derived from current turnover forecast, and a `waitlist_position`.
  2. System notifies the guest of their position and estimated wait time.
  3. When a slot opens, system promotes the top-priority entry and sends an availability alert; Guest has `BranchPolicy.waitlist_accept_window_minutes` to confirm before the next entry is promoted.

**Exception Flows**:
- **EF-1**: `party_size` exceeds the maximum combinable table capacity for the branch → System returns error `PARTY_SIZE_EXCEEDS_CAPACITY` with the branch's maximum supported party size; Host is prompted to split the group or contact the manager.
- **EF-2**: Guest-supplied `phone_number` fails E.164 format validation → System returns field-level validation error; reservation is not persisted until corrected.
- **EF-3**: Reservation hold expires before confirmation is received → System automatically releases the `HOLD`, sets `Reservation.status = EXPIRED`, and re-opens the slot; Guest receives an expiry notification with an option to re-book.

**Postconditions**:
- A `Reservation` record exists with `status = CONFIRMED` and a unique `reservation_code`.
- The linked table slot is blocked in `TableAvailability` for the reserved window.
- A guest confirmation notification has been dispatched and logged in `NotificationLog`.
- A reminder task is enqueued in the scheduler for the pre-arrival window.

**Business Rules Applied**: BR-01 (bookable horizon), BR-02 (party-size vs. table capacity), BR-03 (hold expiry window), BR-04 (reservation confirmation notification)
**Data Entities Affected**: Reservation, TableAvailability, WaitlistEntry, Guest, NotificationLog, BranchPolicy

---

## UC-02: Seat Reserved Guest

**Actor**: Host
**Supporting Actors**: Waiter (zone assignment), Guest

**Preconditions**:
- A `Reservation` record exists with `status = CONFIRMED` for the current service window.
- The linked table is in `status = AVAILABLE` or `status = BEING_CLEANED` with imminent readiness.
- The branch day-open checklist has been completed and the service session is active.

**Main Flow**:
1. Guest arrives at the host stand; Host searches by `reservation_code`, `guest_name`, or `phone_number` to retrieve the `Reservation`.
2. System displays reservation details: party size, table assignment, special requests, and any prepaid or deposit amount.
3. Host confirms the actual `arrived_party_size` (which may differ from `reserved_party_size` by ±`BranchPolicy.party_size_variance_tolerance`).
4. Host selects the pre-assigned table or, if unavailable, picks an equivalent table and records a reassignment reason.
5. System sets `Table.status = OCCUPIED`, creates a new `ServiceSession` record linked to the `Reservation`, assigns the `waiter_id` for the table's zone, and timestamps `seated_at`.
6. System marks `Reservation.status = SEATED` and releases any remaining waitlist entries competing for the same slot.
7. Waiter receives a new table alert on their handheld device showing table number, party size, and any special requests or dietary flags.

**Alternative Flows**:
- **AF-1**: Guest arrives significantly early (before grace window opens).
  1. System flags the reservation as `EARLY_ARRIVAL` and checks if the table is ready.
  2. If ready, Host may seat immediately; `ServiceSession.early_seat = true` is recorded for analytics.
  3. If not ready, Host offers the guest a waiting area or bar seating and sets an estimated ready time.
- **AF-2**: Reservation guest requests a table change after initial seating.
  1. Host identifies an alternative table that is available and matches party size.
  2. Host performs a table transfer: old `Table.status` reverts to `OCCUPIED_PENDING_MOVE`, new table is assigned.
  3. `ServiceSession` is updated with `table_id` and a `TABLE_TRANSFER` event is appended to the session log.

**Exception Flows**:
- **EF-1**: Reservation has `status = NO_SHOW` (grace window elapsed) → System prevents seating under the original reservation; Host must create a new walk-in or override with manager PIN and a reason code.
- **EF-2**: Pre-assigned table is still occupied by the previous party (turnover delay) → System alerts the Host with current occupancy duration; Host notifies the waiting guest of the delay and updates `estimated_ready_at`.

**Postconditions**:
- `Table.status = OCCUPIED` with `ServiceSession` created and timestamped.
- `Reservation.status = SEATED` with `actual_party_size` and `seated_at` recorded.
- Waiter has received a table assignment notification.
- Table slot is no longer available in `TableAvailability` for the occupied window.

**Business Rules Applied**: BR-05 (grace window and no-show policy), BR-06 (party-size variance tolerance), BR-07 (zone-based waiter assignment)
**Data Entities Affected**: Reservation, Table, ServiceSession, Waiter, TableAvailability, WaitlistEntry

---

## UC-03: Seat Walk-in Guest

**Actor**: Host
**Supporting Actors**: Waiter, Guest

**Preconditions**:
- The branch is within operating hours and the service session is active.
- At least one table with sufficient capacity is in `status = AVAILABLE`.
- Walk-in seating policy is enabled (`BranchPolicy.accept_walk_ins = true`).

**Main Flow**:
1. Guest approaches the host stand without a prior reservation; Host opens the "Seat Walk-in" workflow on the POS.
2. Host captures `party_size`, optional `guest_name`, `phone_number` (for loyalty lookup or SMS updates), and any immediate special requests.
3. System queries `TableAvailability` for tables where `min_covers` ≤ `party_size` ≤ `max_covers` and `status = AVAILABLE`, ordered by preference (minimise cover waste, enforce section rotation policy per BR-08).
4. Host selects a table from the suggested list; system optionally shows predicted wait times for each if all tables are occupied.
5. System sets `Table.status = OCCUPIED`, creates a `ServiceSession` with `origin = WALK_IN`, assigns the zone waiter, and records `seated_at = now()`.
6. Host issues a printed or digital table card to the guest party.
7. Waiter receives a new-table alert with party size and any captured requests.

**Alternative Flows**:
- **AF-1**: No tables are immediately available — Host offers a quoted wait time.
  1. System calculates `estimated_wait_minutes` based on average turn time and current occupied table count.
  2. Host presents the wait quote; Guest accepts and provides a phone number.
  3. System creates a `WalkInQueue` entry with `status = WAITING` and a pager or SMS token.
  4. When a table becomes available, system sends an SMS prompt and alerts the Host.
- **AF-2**: Guest party is larger than any single available table but can be accommodated by merging adjacent tables.
  1. Host selects the "Merge Tables" option and picks two or more `table_id` values.
  2. System validates that selected tables are adjacent (per `TableLayout.adjacent_to`) and their combined `max_covers` ≥ `party_size`.
  3. A `TableGroup` record is created; both tables transition to `OCCUPIED` linked to the same `ServiceSession`.

**Exception Flows**:
- **EF-1**: Walk-ins are disabled for the current time slot (e.g., fully-booked peak hour) → System displays `WALK_IN_UNAVAILABLE` with the next available walk-in window; Host can override with manager PIN per BR-09.
- **EF-2**: Guest refuses to provide contact details required by policy (e.g., for large-party COVID tracing) → Host records a manual waiver code; system creates the session with `contact_waived = true` for compliance audit.

**Postconditions**:
- `Table.status = OCCUPIED` with a new `ServiceSession` created (`origin = WALK_IN`).
- Section rotation counter updated for the assigned section.
- Waiter notified of the new table assignment.

**Business Rules Applied**: BR-08 (section rotation), BR-09 (walk-in override policy), BR-10 (table merge adjacency rules)
**Data Entities Affected**: Table, ServiceSession, TableGroup, WalkInQueue, Waiter, BranchPolicy

---

## UC-04: Capture Dine-In Order

**Actor**: Waiter / Server
**Supporting Actors**: Guest, Kitchen Display System (automated)

**Preconditions**:
- A `ServiceSession` exists for the table with `status = ACTIVE`.
- The current menu version is published and items are priced for the active `PricingProfile`.
- The waiter is authenticated and assigned to the table's zone.

**Main Flow**:
1. Waiter opens the table on the handheld POS and navigates to the "New Order" screen; the system loads the active `Menu` items grouped by `menu_section` (e.g., Starters, Mains, Desserts, Drinks).
2. Waiter selects items and, for each item, optionally applies `ItemModifier` groups (e.g., cooking level: rare/medium/well-done; extra toppings; allergen substitutions) and enters free-text `chef_notes`.
3. Waiter assigns each item to a `seat_number` within the party for seat-based billing and course-fire sequencing.
4. Waiter sets `CourseSequence` flags (e.g., fire appetizers immediately, hold mains until starters are cleared) per table preference.
5. Waiter submits the order; system validates every `OrderLine`: `item_id` active in the current menu, `MenuItem.available_qty > 0` (if stock-tracked), modifier constraints satisfied, and no allergen conflicts flagged on the guest profile.
6. System persists the `Order` with `status = OPEN` and each `OrderLine` with `status = PENDING_FIRE`, calculates a preliminary `subtotal` using `PricingProfile`, and returns the order summary to the waiter.
7. System automatically triggers UC-06 (Route Order to Kitchen) for all lines with `CourseSequence.fire_now = true`.

**Alternative Flows**:
- **AF-1**: Waiter uses "Quick Add" to fire a single item to the kitchen without re-opening the full order screen.
  1. Waiter selects a previously captured order, taps "Add Item", and chooses the item.
  2. System appends the `OrderLine` to the existing `Order` and fires immediately to the relevant kitchen station.
- **AF-2**: Waiter captures a takeaway order not linked to a table.
  1. Waiter selects "New Takeaway Order" and enters the guest's name and optional phone number.
  2. System creates an `Order` with `order_type = TAKEAWAY` and a `takeaway_sequence_number` for the pass display.
  3. Flow continues from step 2 of the Main Flow.

**Exception Flows**:
- **EF-1**: A selected `MenuItem` has been marked `available = false` since the menu loaded → System highlights the item in red and prevents submission; Waiter must remove or substitute the item.
- **EF-2**: An `ItemModifier` combination violates a constraint (e.g., "no cheese" selected but item has `modifier_required = true` for sauce) → System displays an inline validation error identifying the conflicting modifier group.
- **EF-3**: Waiter attempts to submit an order for a `ServiceSession` with `status != ACTIVE` (e.g., session closed in error) → System returns `SESSION_NOT_ACTIVE` error and prompts the manager to reactivate the session.

**Postconditions**:
- `Order` persisted with `status = OPEN` and all `OrderLine` records with `status = PENDING_FIRE` or `HELD`.
- Preliminary `subtotal` calculated and visible to the waiter.
- Kitchen routing triggered for all `fire_now` lines.
- `ServiceSession.last_order_at` updated.

**Business Rules Applied**: BR-11 (menu availability check), BR-12 (modifier constraint validation), BR-13 (seat assignment for billing), BR-14 (course sequencing rules)
**Data Entities Affected**: Order, OrderLine, MenuItem, ItemModifier, CourseSequence, ServiceSession, PricingProfile

---

## UC-05: Modify Existing Order

**Actor**: Waiter / Server
**Supporting Actors**: Manager (for post-fire modifications), Chef (awareness of change)

**Preconditions**:
- An `Order` with `status = OPEN` exists for the active `ServiceSession`.
- The waiter is authenticated and assigned to the table.
- For post-fire modifications, manager PIN or approval token is required per `BranchPolicy.allow_post_fire_edit`.

**Main Flow**:
1. Waiter opens the active order and selects the `OrderLine` to modify (add, change quantity, change modifier, or remove).
2. System checks the `OrderLine.status`: if `PENDING_FIRE` or `HELD`, modification proceeds without manager approval.
3. For lines in `FIRED` or `IN_PREPARATION` status, system displays a warning and requires the waiter to select a modification reason code (e.g., `GUEST_CHANGE`, `ORDERING_ERROR`, `ALLERGY_CONCERN`).
4. If `BranchPolicy.allow_post_fire_edit = MANAGER_APPROVAL`, system sends an approval push notification to the on-duty manager's device with the modification details.
5. Manager reviews the request on their device and approves or rejects with an optional comment.
6. Upon approval (or if pre-fire), system updates the `OrderLine` (quantity/modifier change) or marks it `VOIDED` (removal), recalculates `Order.subtotal`, and records a `OrderAuditEvent` with `actor_id`, `timestamp`, `before_state`, and `after_state`.
7. If the modification affects a kitchen ticket already printed or displayed, system sends a `KitchenTicketAmendment` to the relevant station's KDS with an audible alert.

**Alternative Flows**:
- **AF-1**: Waiter adds a new item to an existing open order (not modifying an existing line).
  1. Waiter selects "Add to Order" and picks the new item with modifiers.
  2. System appends a new `OrderLine` and fires it immediately or holds it per course sequence.
- **AF-2**: Waiter transfers the entire order to a different table (e.g., guests move).
  1. Waiter selects "Transfer Table", picks the destination table (must be `OCCUPIED` with the same session or `AVAILABLE`).
  2. System updates `Order.table_id` and `ServiceSession` linkage, appends a `TABLE_TRANSFER` audit event.
  3. Kitchen tickets are updated with the new table number on the KDS.

**Exception Flows**:
- **EF-1**: Manager rejects the post-fire modification request → System notifies the waiter with the rejection reason; original `OrderLine` remains unchanged; waiter must re-engage the guest.
- **EF-2**: Item being modified has already been marked `SERVED` on the KDS → System blocks the modification and instructs the waiter to use the void/refund flow (UC-13) instead.

**Postconditions**:
- Modified `OrderLine` records reflect the updated state with version incremented.
- `OrderAuditEvent` persisted for every modification with full before/after snapshot.
- Kitchen amendment notification dispatched to the affected station if item was already fired.
- `Order.subtotal` recalculated and consistent with current line states.

**Business Rules Applied**: BR-15 (post-fire edit approval thresholds), BR-16 (void reason codes), BR-17 (audit trail requirements)
**Data Entities Affected**: Order, OrderLine, OrderAuditEvent, KitchenTicket, KitchenTicketAmendment, BranchPolicy

---

## UC-06: Route Order to Kitchen

**Actor**: System (automated, triggered by UC-04, UC-05, or manual fire command)
**Supporting Actors**: Waiter (manual fire trigger), Kitchen Display System

**Preconditions**:
- One or more `OrderLine` records with `status = PENDING_FIRE` exist on a submitted `Order`.
- `MenuItem.prep_station_id` is configured for every item in the order.
- Kitchen Display System (KDS) for each target station is online and reachable.

**Main Flow**:
1. System receives a `FireOrder` command (automatic on submission or manual via waiter "Fire Course" button) with `order_id` and optional `course_filter`.
2. System loads all `OrderLine` records matching `status = PENDING_FIRE` and applies `course_filter` if present, grouping lines by `MenuItem.prep_station_id`.
3. For each station group, system creates a `KitchenTicket` record containing: `ticket_number` (sequential per station per shift), `table_number`, `seat_assignments`, line items with modifiers and chef notes, `priority_band` (Normal/Rush/VIP), and `promised_by` timestamp derived from `ServiceSession.seated_at` + average prep time.
4. System publishes each `KitchenTicket` to the station's KDS message queue; KDS acknowledges receipt.
5. System transitions all fired `OrderLine` records from `PENDING_FIRE` to `FIRED`, recording `fired_at` timestamp.
6. System updates the order's `course_status` on the waiter's device to reflect active kitchen tickets.

**Alternative Flows**:
- **AF-1**: Waiter manually fires a held course (e.g., fires mains after starters are cleared).
  1. Waiter taps "Fire Mains" on the table screen.
  2. System applies `course_filter = MAIN` and executes steps 2–6 above for main course lines only.
- **AF-2**: KDS station is offline; system uses fallback printer routing.
  1. System detects KDS acknowledgment timeout after `BranchPolicy.kds_ack_timeout_seconds`.
  2. System re-routes the `KitchenTicket` to the station's assigned backup thermal printer.
  3. A `StationOfflineAlert` is published to the manager dashboard.

**Exception Flows**:
- **EF-1**: `MenuItem.prep_station_id` is null or points to a deactivated station → System routes the ticket to the `BranchPolicy.default_station_id` and logs a `STATION_CONFIG_FALLBACK` warning to the operations log.
- **EF-2**: Message queue is unavailable (full outage) → System persists `KitchenTicket` with `delivery_status = PENDING_RETRY`, enqueues a retry task, and alerts the manager via push notification.

**Postconditions**:
- `KitchenTicket` records created for each station with `status = OPEN`.
- All fired `OrderLine` records have `status = FIRED` and `fired_at` populated.
- KDS stations display the new tickets sorted by `priority_band` and `promised_by`.

**Business Rules Applied**: BR-18 (station routing configuration), BR-19 (KDS fallback policy), BR-20 (priority band assignment)
**Data Entities Affected**: KitchenTicket, OrderLine, MenuItem, PrepStation, KDSStation, BranchPolicy

---

## UC-07: Prepare and Complete Kitchen Ticket

**Actor**: Chef / Kitchen Staff
**Supporting Actors**: Expediter, Waiter (pickup notification)

**Preconditions**:
- A `KitchenTicket` with `status = OPEN` is displayed on the station's KDS.
- The chef is logged into the KDS with their `staff_id`.
- Required ingredients for the ticket items are available in kitchen stock.

**Main Flow**:
1. Chef reviews the `KitchenTicket` on the KDS, noting item list, modifiers, seat assignments, chef notes, and `priority_band`.
2. Chef taps "Accept" on the ticket; system transitions `KitchenTicket.status = IN_PREPARATION` and records `prep_started_at = now()`.
3. For each line item, chef taps the item status to progress it: `QUEUED → PREPPING → READY_FOR_PASS`.
4. As items reach `READY_FOR_PASS`, the expediter (or chef in smaller kitchens) physically places them at the pass window and marks the line `PASSED`.
5. System checks course-dependency rules: if all same-course items across all stations for the same `table_id` are `PASSED`, system sends a "Ready for Service" push notification to the assigned waiter.
6. Waiter picks up the items and marks them `SERVED` on the handheld POS; system transitions `OrderLine.status = SERVED` and records `served_at`.
7. Chef marks the `KitchenTicket` as `COMPLETED`; system records `completed_at` and computes `actual_prep_time_seconds` for performance analytics.

**Alternative Flows**:
- **AF-1**: Chef needs to delay a ticket due to equipment or capacity constraints.
  1. Chef taps "Delay" and selects a `delay_reason_code` (EQUIPMENT, CAPACITY, INGREDIENT_PREP) and an estimated delay in minutes.
  2. System transitions `KitchenTicket.status = DELAYED`, updates `promised_by` for the affected ticket, and alerts the expediter and waiter with the new ETA.
- **AF-2**: Chef discovers mid-preparation that an ingredient is depleted.
  1. Chef taps "Flag Stockout" on the KDS, selecting the affected `ingredient_id`.
  2. System immediately marks `MenuItem.available = false` for all items consuming that ingredient on the active menu.
  3. System alerts the front-of-house manager and sends `ITEM_86ED` notifications to all waiters' devices.
  4. Chef selects whether to continue with a substitution (records `substitution_note`) or cancel the line, triggering UC-13 (void flow).

**Exception Flows**:
- **EF-1**: Ticket timer exceeds `promised_by` without status change → System escalates `KitchenTicket.priority_band` to RUSH, applies a red visual indicator on the KDS, and sends an alert to the expediter.
- **EF-2**: Chef requests a refire (item dropped, burned, or wrong preparation) → Chef taps "Refire", selects `refire_reason_code`; system creates a linked `KitchenTicket` with `parent_ticket_id` and `is_refire = true`, increments `refire_count` on the `OrderLine`, and logs the waste event to `KitchenWasteLog`.

**Postconditions**:
- `KitchenTicket.status = COMPLETED` with `completed_at` and `actual_prep_time_seconds` recorded.
- All `OrderLine` records linked to the ticket have `status = SERVED`.
- KDS station capacity freed for the next ticket.
- `KitchenWasteLog` updated if any refire or stockout event occurred.
- Station throughput metrics updated in `KitchenAnalytics`.

**Business Rules Applied**: BR-21 (ticket escalation timer), BR-22 (refire governance and waste logging), BR-23 (86'd item propagation), BR-24 (course dependency for service notification)
**Data Entities Affected**: KitchenTicket, OrderLine, KitchenWasteLog, MenuItem, Ingredient, KitchenAnalytics, PrepStation

---

## UC-08: Generate and Print Bill

**Actor**: Cashier / Waiter
**Supporting Actors**: Guest, Loyalty Service (points lookup)

**Preconditions**:
- The `Order` is in `status = OPEN` and all desired items have been ordered (some may still be in service).
- All `OrderLine` records that are to be billed are in `status = SERVED` or `status = VOID` (voided lines excluded from total).
- The active `TaxProfile` and any table-level `Discount` are resolved.

**Main Flow**:
1. Cashier or Waiter selects the table and taps "Generate Bill"; system locks the `Order` against further line additions (`status = BILL_REQUESTED`).
2. System computes line-level amounts: `unit_price × quantity` for each non-voided `OrderLine`, applying any active `ItemDiscount` or `ComboPromotion` per BR-25.
3. System applies order-level charges in sequence: subtotal → service charge (`BranchPolicy.service_charge_pct`) → applicable `TaxProfile` rates (e.g., GST, VAT, local levy) → rounding adjustment.
4. If the guest has a linked `LoyaltyAccount`, system calculates redeemable points value and presents it as an optional tender line.
5. System generates a `Bill` record with a unique `bill_number`, `generated_at` timestamp, `subtotal`, `service_charge`, `tax_breakdown` (itemised by tax component), `grand_total`, and `outstanding_amount`.
6. System prints the bill to the table's assigned printer and/or sends a digital copy to the guest's registered email/SMS if preferred.
7. Bill is presented to the guest; `Bill.status = PRESENTED`.

**Alternative Flows**:
- **AF-1**: Waiter prints an interim bill ("running total") without locking the order.
  1. Waiter selects "Print Interim Bill"; system generates a non-final `Bill` with `is_interim = true`.
  2. Order remains in `OPEN` status and additional items can still be added.
  3. Interim bill is printed with a watermark "NOT FINAL — Subject to Change".
- **AF-2**: Bill needs to be reprinted (guest lost the original).
  1. Cashier selects "Reprint Bill" on the closed `Bill` record.
  2. System generates an identical copy marked "DUPLICATE COPY" with reprint timestamp.
  3. Reprint event is logged in `BillAuditLog`.

**Exception Flows**:
- **EF-1**: One or more `OrderLine` records are still in `FIRED` or `IN_PREPARATION` status when "Generate Bill" is requested → System warns the cashier that items are still being prepared; cashier must confirm to proceed or wait for all items to reach `SERVED`/`VOID` status.
- **EF-2**: Applied `Discount` code has expired or is invalid for the current table/order → System rejects the discount with error `DISCOUNT_NOT_APPLICABLE`, removes it from the bill calculation, and notifies the cashier.

**Postconditions**:
- `Bill` record persisted with `status = PRESENTED` and a fully itemised breakdown.
- `Order.status = BILL_REQUESTED` (locked against new line additions).
- Bill printed to the physical printer and/or dispatched digitally per guest preference.
- Loyalty redemption option surfaced if applicable.

**Business Rules Applied**: BR-25 (discount precedence and stacking rules), BR-26 (service charge applicability), BR-27 (tax profile selection by order type), BR-28 (bill lock on generation)
**Data Entities Affected**: Bill, Order, OrderLine, TaxProfile, Discount, LoyaltyAccount, BillAuditLog, BranchPolicy

---

## UC-09: Process Multi-Tender Payment

**Actor**: Cashier
**Supporting Actors**: Payment Gateway, Guest, Manager (for override scenarios)

**Preconditions**:
- A `Bill` with `status = PRESENTED` and `outstanding_amount > 0` exists.
- At least one `PaymentMethod` is enabled for the branch (Cash, Card, UPI, Wallet, etc.).
- Payment gateway connection is healthy or cash fallback is available.

**Main Flow**:
1. Cashier opens the bill and selects "Collect Payment"; system displays `grand_total`, `outstanding_amount`, and available `PaymentMethod` options.
2. Cashier selects the first tender type and enters the tender amount (may be partial — e.g., Guest pays ₹500 cash toward a ₹1,200 bill).
3. For card/digital tenders, system initiates a `PaymentIntent` with `amount`, `currency`, and `merchant_reference = bill_number` via the Payment Gateway API.
4. Payment Gateway processes the transaction and returns `payment_status = SUCCESS` or `FAILED` with a `gateway_transaction_id`.
5. System records a `Payment` record linked to the `Bill` with `tender_type`, `amount`, `gateway_transaction_id`, `processed_at`, and updates `Bill.outstanding_amount -= payment.amount`.
6. If `outstanding_amount > 0`, cashier repeats steps 2–5 with the next tender (e.g., remaining ₹700 by card).
7. Once `outstanding_amount = 0` (or a cash overpayment triggers change calculation), system sets `Bill.status = PAID`, `Order.status = CLOSED`, releases the table (`Table.status = AVAILABLE_DIRTY`), and triggers receipt generation.
8. System prints/sends a payment receipt with itemised tender breakdown and `transaction_ids`.

**Alternative Flows**:
- **AF-1**: Guest pays with exact cash — no change required.
  1. Cashier selects "Cash" tender and enters the exact amount.
  2. System records the `Payment` and immediately closes the bill without a change-due step.
- **AF-2**: Guest pays with cash and is owed change.
  1. Cashier enters the cash amount tendered (e.g., ₹1,500 for a ₹1,200 bill).
  2. System calculates `change_due = tendered_amount − outstanding_amount` (₹300) and displays it prominently.
  3. Cashier dispenses change; system records `cash_tendered` and `change_given` on the `Payment` record.

**Exception Flows**:
- **EF-1**: Payment Gateway returns `TIMEOUT` or network error → System retains the `PaymentIntent` with `status = PENDING_RECONCILIATION`; cashier is advised to check the physical terminal. System runs an async reconciliation job every 60 seconds for up to `BranchPolicy.payment_reconcile_max_attempts` retries; on confirmed success, bill is closed; on confirmed failure, intent is abandoned and cashier retries.
- **EF-2**: Card payment is declined by the gateway → System returns `PAYMENT_DECLINED` with the decline code; `outstanding_amount` is unchanged; cashier offers alternative tender types to the guest.
- **EF-3**: Cashier attempts to collect more than `grand_total` across tenders (accidental over-entry) → System caps tender acceptance at `outstanding_amount` and prompts cashier to adjust the tender amount.

**Postconditions**:
- `Bill.status = PAID`, `Bill.outstanding_amount = 0`.
- `Payment` records created for each tender with `gateway_transaction_id` where applicable.
- `Order.status = CLOSED`.
- `Table.status = AVAILABLE_DIRTY` (requires cleaning before next seating).
- Cash drawer balance updated by the net cash tender amount.
- Receipt dispatched to the guest.

**Business Rules Applied**: BR-29 (payment idempotency via intent tokens), BR-30 (change calculation for cash tenders), BR-31 (gateway reconciliation retry policy)
**Data Entities Affected**: Bill, Payment, PaymentIntent, Order, Table, CashDrawer, Receipt, BranchPolicy

---

## UC-10: Process Split Bill

**Actor**: Cashier / Waiter
**Supporting Actors**: Guest, Payment Gateway

**Preconditions**:
- A `Bill` with `status = PRESENTED` and `outstanding_amount > 0` exists.
- The split request is initiated before any partial payment has been taken, or a partial split is explicitly authorised.
- At least 2 payees are identified.

**Main Flow**:
1. Cashier opens the bill and selects "Split Bill"; system presents split strategy options: **Equal Split**, **By Seat**, **By Item Selection**, or **Custom Amounts**.
2. Cashier (or guest via table-side QR self-pay) selects the strategy and defines split parameters (e.g., 4 equal parts; seat 1 pays for seat 1's items; Guest A selects specific items).
3. System creates `ChildBill` records (one per payee): each `ChildBill` contains the selected `OrderLine` references, a proportional share of `service_charge` and `tax` (calculated per BR-32), and its own `child_bill_number` and `outstanding_amount`.
4. System validates that the sum of all `ChildBill.grand_total` equals the parent `Bill.grand_total` (within rounding tolerance per BR-33).
5. Each `ChildBill` is settled independently via UC-09 (Process Multi-Tender Payment), accepting any mix of tender types per payee.
6. As each `ChildBill.status` transitions to `PAID`, system updates the parent `Bill.outstanding_amount` accordingly.
7. When all `ChildBill` records are `PAID`, system sets parent `Bill.status = PAID` and `Order.status = CLOSED`; table is released.

**Alternative Flows**:
- **AF-1**: Guest requests split mid-payment (one payee has already paid their share via UC-09).
  1. Cashier initiates a split on the remaining `outstanding_amount` only.
  2. System creates `ChildBill` records for the remaining payees based on the residual amount.
  3. Already-paid amount is recorded on the parent bill; split proceeds for the remainder.
- **AF-2**: One payee in a split cannot pay (walks out or declines) — remaining guests agree to cover.
  1. Cashier selects the unpaid `ChildBill` and taps "Redistribute".
  2. System redistributes the unpaid amount equally across the remaining `ChildBill` records and recalculates tax/service charge.

**Exception Flows**:
- **EF-1**: Sum of `ChildBill.grand_total` does not reconcile with parent `Bill.grand_total` after rounding → System blocks bill generation, logs a `SPLIT_RECONCILIATION_ERROR`, and requires cashier to adjust the split parameters.
- **EF-2**: A `ChildBill` payment fails mid-split (gateway decline) → The failed `ChildBill` remains `OPEN`; other payees' settled `ChildBill` records remain `PAID`; cashier manages the failed payee's tender independently.

**Postconditions**:
- All `ChildBill` records have `status = PAID`.
- Parent `Bill.status = PAID` and `Order.status = CLOSED`.
- Each payee receives an individual receipt for their `ChildBill`.
- Table released for cleaning.

**Business Rules Applied**: BR-32 (proportional tax/service charge in splits), BR-33 (split rounding tolerance), BR-34 (partial split authorisation)
**Data Entities Affected**: Bill, ChildBill, OrderLine, Payment, Order, Table, Receipt

---

## UC-11: Process Delivery Order

**Actor**: External Delivery Platform / Waiter
**Supporting Actors**: Kitchen Staff, Delivery Agent, System (webhook receiver)

**Preconditions**:
- The branch has at least one `DeliveryChannel` configured (e.g., Swiggy, Zomato, in-house) with webhook credentials active.
- Delivery menu is published with platform-specific `external_item_id` mappings in `DeliveryMenuMapping`.
- The branch is within delivery operating hours.

**Main Flow**:
1. External Delivery Platform sends an order webhook payload to the RMS `POST /webhooks/delivery/{channel_id}` endpoint containing `external_order_id`, `customer_name`, `delivery_address`, `items` (with `external_item_id`, `quantity`, `modifiers`), `platform_order_total`, and `estimated_delivery_time`.
2. System validates the webhook signature using the channel's `webhook_secret`, confirms the branch is online and the delivery menu is active.
3. System maps `external_item_id` → `internal_item_id` using `DeliveryMenuMapping`; flags any unmapped items as `MAPPING_ERROR` and rejects the order with a 4xx response to the platform if critical items are unmapped.
4. System creates a `DeliveryOrder` with `status = RECEIVED`, links to an internal `Order` with `order_type = DELIVERY`, assigns a `delivery_sequence_number`, and acknowledges the platform webhook within the SLA window (typically 30 seconds).
5. System routes the order to the kitchen via UC-06 with `priority_band = DELIVERY` and includes the `estimated_delivery_time` as `promised_by`.
6. Kitchen prepares the order per UC-07; when all items are `PASSED`, system transitions `DeliveryOrder.status = READY_FOR_PICKUP`.
7. System notifies the delivery agent (or platform) of readiness; on agent pickup, staff marks `DeliveryOrder.status = PICKED_UP` with `pickup_at` timestamp.
8. Platform webhook confirms delivery completion; system sets `DeliveryOrder.status = DELIVERED`, marks the internal `Order.status = CLOSED`, and triggers financial reconciliation with the platform for settlement.

**Alternative Flows**:
- **AF-1**: Waiter manually creates a phone-in delivery order (not from a third-party platform).
  1. Waiter opens "New Delivery Order", enters customer name, phone, delivery address, and items.
  2. System creates a `DeliveryOrder` with `channel = IN_HOUSE` and assigns an in-house delivery agent from the `DeliveryAgentPool`.
  3. Flow continues from step 5 of the Main Flow.
- **AF-2**: Delivery agent is delayed — estimated delivery time must be updated.
  1. Cashier or platform updates `DeliveryOrder.estimated_delivery_at` with a new time and a delay reason.
  2. System sends an updated ETA notification to the customer via the platform's notification API.

**Exception Flows**:
- **EF-1**: Webhook signature validation fails → System returns HTTP 401, logs the attempt in `WebhookSecurityLog`, and sends an alert to the tech team; the order is not created.
- **EF-2**: Kitchen is unable to fulfill the delivery order (stockout discovered post-acceptance) → System calls the platform's order cancellation API with `reason = ITEM_UNAVAILABLE`, voids the internal `Order`, updates `MenuItem.available = false`, and logs the cancellation in `DeliveryOrderLog`.

**Postconditions**:
- `DeliveryOrder.status = DELIVERED` and internal `Order.status = CLOSED`.
- `DeliveryOrderLog` updated with full lifecycle timestamps: `received_at`, `accepted_at`, `ready_at`, `pickup_at`, `delivered_at`.
- Platform financial reconciliation record created for the settlement cycle.

**Business Rules Applied**: BR-35 (webhook SLA acknowledgment window), BR-36 (delivery menu mapping validation), BR-37 (delivery priority band), BR-38 (platform settlement reconciliation)
**Data Entities Affected**: DeliveryOrder, DeliveryMenuMapping, Order, OrderLine, DeliveryChannel, DeliveryAgent, WebhookSecurityLog, DeliveryOrderLog

---

## UC-12: Receive Inventory Goods

**Actor**: Manager / Inventory Staff
**Supporting Actors**: Vendor, Purchase Order System

**Preconditions**:
- A `PurchaseOrder` with `status = DISPATCHED` or `EXPECTED` exists for the arriving shipment.
- The receiving staff member is authenticated with `INVENTORY_RECEIVE` permission.
- The branch's inventory store is open for receiving (within `InventoryPolicy.receiving_window`).

**Main Flow**:
1. Inventory Staff opens the "Receive Goods" screen and scans or searches for the `PurchaseOrder` by `po_number` or vendor name.
2. System displays expected line items: `ingredient_id`, `ingredient_name`, `ordered_quantity`, `unit_of_measure`, and `expected_unit_cost`.
3. Staff physically inspects delivered goods and enters the `received_quantity` for each line item (may differ from `ordered_quantity`).
4. Staff records quality inspection notes: `batch_number`, `expiry_date`, `condition` (Good / Damaged / Rejected), and optionally uploads a photo of the delivery.
5. For any `received_quantity < ordered_quantity`, system automatically creates a `GoodsReceiptVariance` record with `variance_qty` and prompts staff to select a reason (`SHORT_DELIVERY`, `QUALITY_REJECTION`, `ORDER_CANCELLED_BY_VENDOR`).
6. Staff confirms the receipt; system creates a `GoodsReceiptNote` (GRN) with a unique `grn_number`, transitions `PurchaseOrder.status = PARTIALLY_RECEIVED` or `FULLY_RECEIVED` based on completeness.
7. System updates `IngredientStock.on_hand_qty += received_quantity` for each accepted line, records a `StockMovement` entry with `movement_type = RECEIPT`, `grn_number`, `batch_number`, and `unit_cost`.
8. If a received ingredient was previously in `LOW_STOCK` or `STOCKOUT` status, system automatically re-enables associated `MenuItem.available = true` and notifies the kitchen manager.

**Alternative Flows**:
- **AF-1**: Goods arrive without a prior Purchase Order (emergency or surprise delivery).
  1. Staff selects "Receive Without PO" and creates a `BlindReceipt` by entering vendor name, items, and quantities manually.
  2. System creates a `PurchaseOrder` in `status = RETROSPECTIVE` and a `GoodsReceiptNote` linked to it.
  3. Manager receives an alert to review and approve the retrospective PO within `InventoryPolicy.retro_po_approval_hours`.
- **AF-2**: Part of the delivery is rejected due to quality issues.
  1. Staff marks affected lines with `condition = REJECTED` and enters the `rejection_reason`.
  2. System creates a `VendorClaim` record for the rejected items, decrements accepted quantity, and includes rejection details in the GRN.
  3. System sends an automated email to the vendor with the `VendorClaim` details.

**Exception Flows**:
- **EF-1**: `received_quantity` entered exceeds `ordered_quantity` by more than `InventoryPolicy.over_receipt_tolerance_pct` → System blocks the receipt and requires manager override with a reason code to prevent stock inflation errors.
- **EF-2**: `expiry_date` entered is within `InventoryPolicy.min_shelf_life_days` of today → System warns staff that the item is near-expiry; staff must confirm acceptance or reject the batch; near-expiry stock is flagged in the `IngredientStock` record.

**Postconditions**:
- `GoodsReceiptNote` created with `status = CONFIRMED` and `grn_number` assigned.
- `IngredientStock.on_hand_qty` updated for all received ingredients.
- `StockMovement` records created for full auditability.
- `PurchaseOrder.status` updated to reflect receipt completeness.
- Previously stockout items re-enabled on the menu if stock now available.

**Business Rules Applied**: BR-39 (over-receipt tolerance), BR-40 (near-expiry acceptance policy), BR-41 (blind receipt approval window), BR-42 (stockout auto-enable on receipt)
**Data Entities Affected**: PurchaseOrder, GoodsReceiptNote, GoodsReceiptVariance, IngredientStock, StockMovement, VendorClaim, MenuItem, InventoryPolicy

---

## UC-13: Apply Discount or Void Item

**Actor**: Waiter / Manager
**Supporting Actors**: Cashier (bill recalculation), POS Audit System

**Preconditions**:
- An `Order` with `status = OPEN` or `BILL_REQUESTED` exists.
- The waiter has `APPLY_DISCOUNT` permission, or a manager PIN is available for above-threshold discounts.
- The `Discount` record being applied is active, within its validity window, and applicable to the selected items per `Discount.applicability_rules`.

**Main Flow**:
1. Waiter selects the target `OrderLine` or the entire `Order` and taps "Apply Discount" or "Void Item".
2. For a discount, system presents available `Discount` options filtered by applicability (item-level, category-level, order-level, day-of-week, happy-hour window).
3. Waiter or cashier selects the discount or enters a `discount_code`; system validates the code against `Discount.usage_limit` and `Discount.min_order_value`.
4. System calculates the `discount_amount` (flat or percentage) and checks if the discount requires manager approval per `BranchPolicy.discount_approval_threshold_pct`.
5. If approval required, system sends a push notification to the on-duty manager with the discount details and requesting actor; manager approves or rejects from their device.
6. Upon approval (or if below threshold), system applies the `OrderLineDiscount` or `OrderDiscount` record, recalculates `Order.subtotal` and `Bill.grand_total` if a bill is already generated.
7. For a void, waiter selects the `OrderLine`, enters a `void_reason_code`, and system marks `OrderLine.status = VOIDED`; if the item was already `FIRED`, a kitchen amendment is sent (per UC-05, step 7).
8. All discount and void actions are recorded in `OrderAuditEvent` with `actor_id`, `approval_actor_id` (if applicable), `before_amount`, and `after_amount`.

**Alternative Flows**:
- **AF-1**: Manager proactively applies a complimentary discount to a table (e.g., guest complaint resolution).
  1. Manager opens the table, selects "Complimentary", enters the `comp_reason` and amount or percentage.
  2. System creates an `OrderDiscount` with `discount_type = COMPLIMENTARY` and `requires_approval = false` (manager self-approves).
  3. `CompReport` entry is created for management review.
- **AF-2**: Void is requested for an item already marked `SERVED` (post-service void).
  1. System requires manager approval and a `post_serve_void_reason`.
  2. Upon approval, `OrderLine.status = VOIDED_POST_SERVE`; system creates a `VoidCredit` record for the corresponding bill adjustment.
  3. If a payment has already been collected, system creates a `RefundInstruction` for the cashier to process.

**Exception Flows**:
- **EF-1**: `discount_code` has already reached `Discount.usage_limit` → System returns `DISCOUNT_LIMIT_REACHED`; the code is not applied; waiter is prompted to use an alternative discount or contact the manager.
- **EF-2**: Manager rejects the discount approval request → System notifies the waiter with the rejection reason; `OrderLine` and `Order.subtotal` remain unchanged; the request is logged in `OrderAuditEvent` with `status = REJECTED`.

**Postconditions**:
- `OrderLineDiscount` or `OrderDiscount` record created with all approval metadata.
- `Order.subtotal` and linked `Bill.grand_total` recalculated and consistent.
- Voided `OrderLine` records have `status = VOIDED` with reason code.
- Full audit trail in `OrderAuditEvent` for every discount and void action.

**Business Rules Applied**: BR-43 (discount stacking and precedence), BR-44 (discount approval thresholds), BR-45 (void reason code requirements), BR-46 (post-serve void governance)
**Data Entities Affected**: OrderLineDiscount, OrderDiscount, OrderLine, Order, Bill, OrderAuditEvent, Discount, VoidCredit, RefundInstruction, BranchPolicy

---

## UC-14: Close End-of-Day Cash Session

**Actor**: Cashier / Manager
**Supporting Actors**: Accounting System, Branch Manager

**Preconditions**:
- The branch service day is ending (or a shift handover is occurring).
- All tables are in `status = AVAILABLE` or `AVAILABLE_DIRTY` (no open `ServiceSession` records with `status = ACTIVE`).
- The `CashSession` for the current shift is in `status = OPEN`.
- Cashier is authenticated with `EOD_CLOSE` permission.

**Main Flow**:
1. Cashier initiates "Close Cash Session" on the POS; system validates that no `Order` with `status = OPEN` or `BILL_REQUESTED` exists (blocking check).
2. System presents the theoretical closing figures: `total_cash_sales`, `total_card_sales`, `total_digital_sales`, `total_voids`, `total_discounts`, `total_refunds`, and `expected_cash_in_drawer`.
3. Cashier physically counts the cash in the drawer and enters the `actual_cash_counted` per denomination (`DenominationCount` record).
4. System calculates `cash_variance = actual_cash_counted − expected_cash_in_drawer`; if `|cash_variance| > BranchPolicy.cash_variance_tolerance`, system flags the session for manager review.
5. Cashier records the `closing_float` (cash retained for the next shift) and the `cash_drop_amount` (cash to be deposited or handed to the safe).
6. Manager reviews and electronically signs off the session on their device; system transitions `CashSession.status = CLOSED` with `closed_at`, `closed_by_cashier_id`, and `approved_by_manager_id`.
7. System generates the End-of-Day Report: sales summary by payment method, item category, waiter, and hour; void and discount summary; tax collected; and variance report.
8. System exports the EOD data package to the accounting integration (`AccountingExport` record) and optionally emails the report to configured recipients.

**Alternative Flows**:
- **AF-1**: Mid-shift cash session handover (cashier change without day close).
  1. Outgoing cashier performs a "Shift Handover" instead of EOD close.
  2. System creates a new `CashSession` for the incoming cashier, transferring the `closing_float` as the incoming `opening_float`.
  3. A `ShiftHandoverReport` is generated for both cashiers' records.
- **AF-2**: Manager overrides the cash variance and approves despite exceeding tolerance.
  1. Manager selects "Approve with Variance", enters a `variance_explanation`, and signs off.
  2. System records `variance_override = true` and `variance_explanation` on the `CashSession`.
  3. A `CashVarianceAlert` is sent to the regional manager for review.

**Exception Flows**:
- **EF-1**: One or more `Order` records are still in `OPEN` status when EOD close is initiated → System blocks the close with a list of open orders; manager must resolve (force-close or transfer) each open order before EOD close can proceed.
- **EF-2**: Accounting integration export fails → System retains the `AccountingExport` in `status = PENDING_EXPORT` and retries on a schedule; `CashSession` is still closed; an alert is sent to the finance team for manual export if retries are exhausted.

**Postconditions**:
- `CashSession.status = CLOSED` with manager sign-off recorded.
- EOD Report generated and stored in `Reports` with `report_type = EOD`.
- `AccountingExport` record created and dispatched (or queued for retry).
- `CashDrawer.balance` reset to `closing_float` for next session.
- All branch POS terminals locked from new order creation until the next day-open checklist is completed.

**Business Rules Applied**: BR-47 (EOD blocking on open orders), BR-48 (cash variance tolerance and override), BR-49 (shift handover float transfer), BR-50 (accounting export SLA)
**Data Entities Affected**: CashSession, CashDrawer, DenominationCount, EODReport, AccountingExport, Order, BranchPolicy, ShiftHandoverReport

---

## UC-15: Enroll in Loyalty Program and Redeem Points

**Actor**: Guest / Cashier
**Supporting Actors**: Loyalty Service, SMS/Email Notification Service, Manager (tier upgrade approvals)

**Preconditions**:
- The branch has an active `LoyaltyProgram` configured with earn and burn rules.
- Guest provides a valid phone number or email address for account creation.
- For redemption, a `LoyaltyAccount` with sufficient `points_balance` exists and the `Bill` is in `status = PRESENTED`.

**Main Flow**:
1. Cashier asks the guest if they are enrolled in the loyalty program; guest indicates they are new or provides their registered phone number.
2. **New enrollment**: Cashier selects "Enroll Guest" and enters `phone_number`, `guest_name`, and optional `email_address`; system creates a `LoyaltyAccount` with `status = ACTIVE`, `tier = BRONZE`, `points_balance = 0`, and a unique `loyalty_card_number`.
3. System sends a welcome SMS/email with the `loyalty_card_number`, current tier benefits, and earn rate (e.g., 1 point per ₹10 spent per BR-51).
4. Post-payment, system calculates `points_earned = floor(Bill.subtotal / LoyaltyProgram.spend_per_point)` and credits the `LoyaltyAccount.points_balance`; records a `PointsTransaction` with `transaction_type = EARN`, `reference_order_id`, and `earned_at`.
5. **Redemption (existing member)**: Cashier looks up the account by phone number; system displays `points_balance`, current `tier`, and `redeemable_value = points_balance × LoyaltyProgram.point_redemption_value`.
6. Guest selects how many points to redeem; system validates the amount does not exceed `min_bill_pct` restriction (BR-52) and that `points_balance ≥ redemption_points`.
7. System creates a `PointsRedemption` record, reduces `LoyaltyAccount.points_balance`, and applies the `redemption_value` as a tender line on the `Bill` (treated as a `LOYALTY_TENDER` in UC-09).
8. System checks if the updated lifetime spend crosses a tier threshold and automatically upgrades the tier (e.g., BRONZE → SILVER at ₹10,000 lifetime), sending a tier upgrade notification.

**Alternative Flows**:
- **AF-1**: Guest enrolls via QR code self-registration (table-side or receipt QR).
  1. Guest scans the QR code, fills in the enrollment form on their mobile browser, and submits.
  2. System creates the `LoyaltyAccount` and links it to the current `Order` via a session token.
  3. Points from the current order are credited automatically post-payment.
- **AF-2**: Guest requests a points balance inquiry without making a purchase.
  1. Cashier looks up the account by phone; system displays `points_balance`, `redeemable_value`, `tier`, and `tier_progress` (current spend toward next tier).
  2. No transaction is created; inquiry is logged in `LoyaltyAccountActivityLog`.

**Exception Flows**:
- **EF-1**: Phone number is already registered to an existing `LoyaltyAccount` → System prevents duplicate enrollment and surfaces the existing account; cashier proceeds with the existing account for earning/redemption.
- **EF-2**: Redemption request exceeds `LoyaltyProgram.max_redemption_pct_of_bill` (e.g., guest tries to pay 100% of the bill with points when max is 50%) → System caps the redeemable points at the policy limit, displays the maximum redeemable amount, and prompts the guest to pay the remainder via another tender.

**Postconditions**:
- `LoyaltyAccount` created (new enrollment) or updated (earn/burn transaction).
- `PointsTransaction` record persisted with `transaction_type = EARN` or `REDEEM`, `reference_order_id`, and timestamp.
- Welcome or tier-upgrade notification dispatched where applicable.
- Lifetime spend and tier recalculated and updated on the `LoyaltyAccount`.

**Business Rules Applied**: BR-51 (points earn rate), BR-52 (minimum bill percentage for redemption), BR-53 (tier threshold and upgrade rules), BR-54 (duplicate enrollment prevention)
**Data Entities Affected**: LoyaltyAccount, PointsTransaction, PointsRedemption, LoyaltyProgram, Bill, Guest, NotificationLog, LoyaltyAccountActivityLog

---

## Cross-Cutting Concerns

### Authentication and Authorisation
Every use case requires the acting user to be authenticated via the RMS session token (JWT). Role-based access control (RBAC) enforces that actors can only invoke endpoints within their permission scope (e.g., `WAITER` cannot close a cash session; `CASHIER` cannot approve post-fire modifications without `MANAGER` role). Manager PIN overrides are logged as impersonation events and are subject to audit.

### Optimistic Concurrency and Versioning
All mutable entities (`Order`, `Bill`, `Table`, `KitchenTicket`, `LoyaltyAccount`, `IngredientStock`) carry an `entity_version` integer. Write operations must supply the last-known version; the system rejects updates where the supplied version does not match the persisted version, returning `CONCURRENT_MODIFICATION_CONFLICT`. Clients must re-fetch and retry.

### Audit Trail
All state-changing operations across every use case produce an immutable `AuditEvent` record containing: `entity_type`, `entity_id`, `action`, `actor_id`, `actor_role`, `before_state` (JSON snapshot), `after_state` (JSON snapshot), `branch_id`, `session_id`, and `event_timestamp`. Audit records are append-only and cannot be deleted.

### Idempotency
Payment operations (UC-09, UC-10), webhook ingestion (UC-11), and inventory receipts (UC-12) support idempotency keys. Duplicate requests with the same `idempotency_key` within a 24-hour window return the original response without re-executing the operation.

### Notification Delivery
Outbound notifications (confirmation, reminder, receipt, loyalty, alerts) are dispatched via the `NotificationService` which supports SMS (via Twilio/MSG91), email (via SendGrid), and in-app push (Firebase). Each notification is logged in `NotificationLog` with delivery status. Failed notifications are retried up to 3 times with exponential backoff.

### Offline Resilience
The POS is designed for offline-first operation. If the central API is unreachable, the handheld POS stores `Order`, `OrderLine`, and `Payment` events in a local SQLite queue and synchronises when connectivity is restored. Conflicts are resolved server-side using the event timestamp and entity version; unresolvable conflicts are escalated to the manager dashboard.

### Tax Compliance
Tax calculations adhere to the jurisdiction-specific `TaxProfile` configured per branch. Tax amounts are always computed server-side to prevent client-side tampering. Every `Bill` stores a `tax_breakdown` array with individual tax component names, rates, and computed amounts for regulatory compliance. GST invoice numbers are assigned sequentially per branch per financial year.

### Data Retention and Privacy
Guest contact information (`phone_number`, `email_address`) is stored encrypted at rest. Per the configured retention policy (default 36 months), guest records are anonymised after inactivity. Loyalty account data is retained for the lifetime of the account plus 12 months post-closure. Right-to-erasure requests trigger a `GuestDataErasureJob` that anonymises PII while preserving financial transaction records for statutory compliance.
