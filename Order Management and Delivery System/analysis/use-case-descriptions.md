# Use Case Descriptions

## UC-01: Register Account

**Primary Actor:** Customer
**Preconditions:** Customer has a valid email or phone number.
**Postconditions:** Customer account is created and verified; customer can log in.

**Main Flow:**
1. Customer navigates to registration page.
2. Customer selects registration method (email/password or phone/OTP or social login).
3. System validates input format and checks for duplicate accounts.
4. System sends OTP to email/phone for verification.
5. Customer enters OTP within 5-minute window.
6. System verifies OTP, creates account, and issues JWT tokens.
7. System redirects customer to homepage with welcome notification.

**Alternative Flows:**
- **3a.** Duplicate email/phone detected → System displays error with option to log in or recover password.
- **3b.** Social login selected → System redirects to OAuth provider, receives profile data, and creates account.
- **5a.** OTP expired → System offers resend with rate limit (max 3 per 10 minutes).
- **5b.** Invalid OTP → System increments attempt counter; after 5 invalid attempts, block for 30 minutes.

---

## UC-03: Manage Addresses

**Primary Actor:** Customer
**Preconditions:** Customer is authenticated.
**Postconditions:** Address saved/updated/deleted; default address may be changed.

**Main Flow (Add Address):**
1. Customer navigates to addresses section.
2. Customer selects Add New Address.
3. Customer fills in address fields (label, line1, line2, city, state, postal code, country).
4. System validates postal code against active delivery zones.
5. System displays serviceability status (serviceable / not serviceable).
6. Customer saves address.
7. System creates address record; if first address, sets as default automatically.

**Alternative Flows:**
- **4a.** Postal code not in any active delivery zone → System saves address but marks as "not serviceable"; customer can still save for future use.
- **6a.** Customer edits existing address → System updates record; if address is linked to active orders, shows warning.
- **6b.** Customer deletes address → System checks active orders; if linked, shows error "Address linked to active order"; otherwise soft-deletes.
- **6c.** Customer sets as default → System unsets previous default and sets new one.

---

## UC-05: Search Products

**Primary Actor:** Customer
**Preconditions:** Product catalog is populated with at least one active product.
**Postconditions:** Search results are displayed within P95 latency target (500 ms).

**Main Flow:**
1. Customer enters search query in the search bar.
2. System sends query to OpenSearch with configured analyzers (stemming, synonyms).
3. System applies active filters (category, price range, availability).
4. System returns paginated results sorted by relevance.
5. Customer views result cards with product image, title, price, and availability status.

**Alternative Flows:**
- **2a.** Empty query → System returns trending/popular products.
- **4a.** No results found → System suggests spelling corrections and related categories.
- **4b.** OpenSearch unavailable → System falls back to RDS full-text search with degraded performance.

---

## UC-07: Manage Cart

**Primary Actor:** Customer
**Preconditions:** Customer is authenticated (or guest session exists).
**Postconditions:** Cart is updated with correct items, quantities, and pricing.

**Main Flow:**
1. Customer views current cart.
2. System validates each item's current availability and price against catalog.
3. System displays updated cart with current prices, tax, shipping, and discount.
4. Customer adds item (specifies variant and quantity).
5. System checks stock availability and adds item to cart.
6. System recalculates cart totals.

**Alternative Flows:**
- **2a.** Cart item price changed since added → System shows updated price with notification banner.
- **2b.** Cart item out of stock → System shows "Out of Stock" badge and disables checkout for that item.
- **4a.** Item quantity exceeds available stock → System caps quantity to available stock and shows warning.
- **5a.** Inventory reservation in progress (checkout TTL active) → System cannot add; shows "Item reserved by another customer."
- **Guest-to-auth merge:** On login, system merges guest cart with authenticated cart; if conflicts exist, uses the higher quantity.

---

## UC-09: Checkout

**Primary Actor:** Customer
**Preconditions:** Customer is authenticated; cart contains at least one available item; delivery address is set.
**Postconditions:** Order is created with status `Draft`; inventory is reserved; payment is initiated.

**Main Flow:**
1. Customer clicks "Proceed to Checkout" from cart.
2. System validates all cart items for current availability and pricing.
3. System validates delivery address against active delivery zones.
4. System calculates order total: line items + tax + shipping fee − discount.
5. Customer reviews order summary and selects payment method.
6. System reserves inventory with 15-minute TTL.
7. System creates order in `Draft` state and initiates payment via gateway.
8. On payment success, order transitions to `Confirmed`.
9. System emits `order.confirmed.v1` event and sends confirmation notification.

**Alternative Flows:**
- **2a.** Item out of stock → System removes item from cart, notifies customer, and recalculates total.
- **3a.** Address not serviceable → System prompts customer to select or add a serviceable address.
- **6a.** Inventory reservation fails (race condition) → System retries once; if still fails, shows stock error.
- **7a.** Payment fails → System releases inventory reservation, shows payment error, and offers retry.
- **7b.** Payment gateway timeout → System polls for payment status for 30 seconds before failing.

---

## UC-11: Track Order

**Primary Actor:** Customer
**Preconditions:** Customer is authenticated; order exists in their account.
**Postconditions:** Customer sees current status and milestone history.

**Main Flow:**
1. Customer navigates to order history.
2. Customer selects an order.
3. System loads order details: status, estimated delivery, line items, payment summary.
4. System loads milestone history with timestamps.
5. Customer views current status and progression.

**Alternative Flows:**
- **5a.** Order is `Delivered` → System shows POD link (signature + photo with presigned URL).
- **5b.** Order has failed delivery attempt → System shows failure reason and reschedule info.
- **5c.** Order is `ReturnedToWarehouse` → System shows return reason and refund eligibility.
- **5d.** Return initiated → System shows return status and refund estimate.
- **4a.** DynamoDB read fails → System shows current state from RDS without detailed milestones.
- **5a (sync pending).** POD images not yet uploaded → System shows "POD processing" placeholder.

---

## UC-14: Process Payment

**Primary Actor:** System (triggered by checkout)
**Preconditions:** Order exists in `Draft` state; valid payment method selected.
**Postconditions:** Payment is captured; order transitions to `Confirmed`.

**Main Flow:**
1. Payment Service receives payment request with order ID, amount, and idempotency key.
2. Service initiates authorization with primary payment gateway.
3. Gateway returns authorization token.
4. Service captures the authorized amount.
5. Service records transaction (gateway reference, amount, status, timestamp).
6. Service emits `payment.captured.v1` event.
7. Order Service transitions order to `Confirmed`.

**Alternative Flows:**
- **2a.** Primary gateway down → Service routes to secondary gateway (failover).
- **3a.** Authorization declined → Service returns decline reason to customer; no capture attempted.
- **4a.** Capture fails (transient) → Service retries with exponential backoff (base 1 s, max 60 s, 3 retries).
- **4b.** Capture fails (permanent) → Service releases reservation, notifies customer, logs for investigation.

---

## UC-17: View Pick List

**Primary Actor:** Warehouse Staff
**Preconditions:** Staff is authenticated; fulfillment tasks are assigned.
**Postconditions:** Staff has all info needed to start picking.

**Main Flow:**
1. Staff logs into warehouse dashboard.
2. System displays assigned tasks sorted by SLA deadline (colour-coded: green / yellow / red).
3. Staff selects a task to view details.
4. System shows: order ID, customer name, delivery zone, items list (product, variant, SKU, bin location, quantity), SLA countdown.
5. Staff starts the task.
6. System marks task as `IN_PROGRESS`; only one task can be in progress per staff member.

**Alternative Flows:**
- **3a.** No tasks assigned → Dashboard shows "No pending tasks."
- **5a.** Another task already in progress → System shows "Complete current task first."
- **SLA breach warning:** System sends push notification to supervisor if task is within 30 minutes of SLA deadline.

---

## UC-18: Verify Picks

**Primary Actor:** Warehouse Staff
**Preconditions:** Fulfillment task is `IN_PROGRESS`.
**Postconditions:** All items verified; task ready for packing.

**Main Flow:**
1. Staff scans first item barcode with device camera or scanner.
2. System looks up SKU from barcode.
3. System validates SKU matches expected pick item.
4. System increments scanned count for that item.
5. Staff repeats for all items.
6. Once all items scanned to expected quantities, system enables "Complete Picking" button.
7. Staff confirms picking complete.
8. System transitions task to `PICKED` state.

**Alternative Flows:**
- **3a.** SKU mismatch → System shows "Wrong Item!" with expected vs scanned; flags item for supervisor; staff must re-scan correct item.
- **4a.** Quantity overcounted → System shows "Already scanned max quantity."
- **6a.** Supervisor can override flagged mismatch → System records override with supervisor ID.

---

## UC-21: View Assignments

**Primary Actor:** Delivery Staff
**Preconditions:** Staff is authenticated; assignments exist for today.
**Postconditions:** Staff sees all delivery assignments for the day.

**Main Flow:**
1. Staff opens delivery app.
2. System loads assignments for today: customer name, delivery address, order summary, delivery window.
3. System sorts assignments by suggested sequence (delivery zone proximity).
4. Staff can view printable route sheet.
5. New assignments trigger push notification.

**Alternative Flows:**
- **2a.** No assignments for today → Dashboard shows "No deliveries assigned."
- **4a.** Reassignment occurs during shift → System sends push notification with updated assignment list.

---

## UC-22: Update Delivery Status

**Primary Actor:** Delivery Staff
**Preconditions:** Staff has assigned deliveries; order is in a state that allows the target transition.
**Postconditions:** Order state is updated; milestone recorded; customer notified.

**Main Flow:**
1. Staff selects an assigned delivery on their mobile dashboard.
2. Staff taps the next milestone button (e.g., "Mark as Picked Up").
3. System validates the transition is allowed from current state.
4. System records milestone: status, timestamp, staff ID, optional notes.
5. System updates order state in database.
6. System emits status change event via EventBridge.
7. Notification Service sends status update to customer.

**Alternative Flows:**
- **3a.** Invalid transition attempted (e.g., PickedUp → Delivered skipping OutForDelivery) → System rejects with error.
- **6a.** EventBridge publish fails → Event lands in DLQ; milestone is still recorded in database.

---

## UC-23: Capture Proof of Delivery

**Primary Actor:** Delivery Staff
**Preconditions:** Order is in `OutForDelivery` state; staff is at delivery location.
**Postconditions:** POD artifacts stored in S3; order transitions to `Delivered`.

**Main Flow:**
1. Staff taps "Complete Delivery" on the order.
2. System presents signature capture screen; recipient signs on device.
3. System presents camera interface; staff captures photo at delivery location.
4. Staff optionally adds delivery notes.
5. System uploads signature and photo to S3 with AES-256 encryption.
6. System records POD metadata (S3 keys, timestamp, staff ID) on the order.
7. Order transitions to `Delivered`; `order.delivered.v1` event emitted.
8. Customer receives delivery confirmation with POD download link.

**Alternative Flows:**
- **2a.** Recipient unavailable for signature → Staff records "left at door" with photo evidence only.
- **5a.** Device offline → POD stored locally; sync triggered when connectivity resumes.
- **5b.** S3 upload fails → System retries 3 times; after failure, alerts operations and keeps order in `OutForDelivery`.

---

## UC-25: Manage Delivery Zones

**Primary Actor:** Operations Manager
**Preconditions:** Admin or Ops Manager role; platform is active.
**Postconditions:** Delivery zone created/updated/deactivated.

**Main Flow (Create Zone):**
1. Ops Manager navigates to Delivery Zones.
2. Ops Manager selects Create New Zone.
3. Ops Manager fills in: name, postal codes (comma-separated), delivery fee, minimum order value, SLA target (hours).
4. System validates postal codes (no overlap with existing active zones).
5. System creates zone with effective date.

**Alternative Flows:**
- **4a.** Postal code overlap → System shows conflicting zone name; operator must resolve before saving.
- **Deactivate zone:** Ops Manager selects Deactivate → System marks zone inactive; existing active orders not affected; new orders to those postal codes rejected until re-assigned to another zone.
- **Edit zone:** Ops Manager updates fields → System versions the change with effective date.

---

## UC-26: Initiate Return

**Primary Actor:** Customer
**Preconditions:** Order is in `Delivered` state; current date is within return window.
**Postconditions:** Return request created; return pickup scheduled.

**Main Flow:**
1. Customer navigates to delivered order detail and clicks "Request Return".
2. System validates return eligibility: within return window, product category allows returns.
3. Customer selects return reason from predefined list.
4. Customer optionally uploads photo evidence.
5. System creates return request and schedules pickup assignment.
6. Customer receives return confirmation with estimated pickup date.

**Alternative Flows:**
- **2a.** Return window expired → System shows "Return period has ended" message with support contact.
- **2b.** Product category excluded from returns → System shows "This item is not eligible for return".
- **5a.** No delivery staff available in zone → System queues pickup and notifies operations manager.

---

## UC-28: Inspect Return

**Primary Actor:** Warehouse Staff
**Preconditions:** Return is in `PICKED_UP` state; item received at warehouse.
**Postconditions:** Inspection completed; refund initiated or rejection sent.

**Main Flow:**
1. Staff navigates to return inspection queue.
2. Staff selects pending return.
3. System shows: original order details, customer return reason, photo evidence (if any), expected item details.
4. Staff physically inspects item against original condition.
5. Staff records inspection result: Accept / Reject / Partial Accept.
6. Staff adds optional notes.
7. If Accept → System triggers automatic refund (full amount); updates inventory; sends notification to customer.
8. If Partial Accept → Staff specifies accepted items; system calculates partial refund; sends notification.
9. If Reject → Staff records rejection reason; system notifies customer with rejection reason and next steps.

**Alternative Flows:**
- **4a.** Item not arrived yet → Staff marks as "Not Received"; system updates return status.
- **7a.** Refund API call fails → System retries 3 times; if all fail, escalates to Finance role.
- **Wrong item returned:** Staff selects "Wrong Item" reason; operations manager notified for investigation.

---

## UC-30: Configure Settings

**Primary Actor:** Admin
**Preconditions:** Admin role.
**Postconditions:** Platform config updated; change versioned and audited.

**Main Flow:**
1. Admin navigates to Platform Configuration.
2. System shows current config values with descriptions and data types.
3. Admin selects config key to update.
4. Admin enters new value.
5. System validates value against data type and allowed ranges.
6. Admin confirms change.
7. System creates new config version; applies immediately (within 1 min via AppConfig).
8. System records AuditLog entry (actorId, key, oldValue, newValue, timestamp).

**Alternative Flows:**
- **5a.** Invalid value → System shows validation error with allowed range.
- **View history:** Admin views history → System shows version history (version, value, updatedBy, updatedAt).
- **Rollback:** Admin rolls back → System activates previous version; creates audit entry.
