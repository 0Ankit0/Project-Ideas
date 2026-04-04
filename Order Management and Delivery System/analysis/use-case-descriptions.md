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
**Preconditions:** Customer has at least one existing order.
**Postconditions:** Current order status and milestone history are displayed.

**Main Flow:**
1. Customer navigates to order detail page.
2. System retrieves order aggregate from database.
3. System retrieves milestone history from DynamoDB status timeline.
4. System displays current state, estimated delivery window, and timestamped milestones.
5. If order is delivered, system displays POD (signature image + delivery photo).

**Alternative Flows:**
- **3a.** DynamoDB read fails → System shows current state from RDS without detailed milestones.
- **5a.** POD images not yet uploaded (sync pending) → System shows "POD processing" placeholder.

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
**Preconditions:** Staff is authenticated and assigned to a warehouse location.
**Postconditions:** Staff sees all pending fulfillment tasks.

**Main Flow:**
1. Staff opens fulfillment dashboard.
2. System retrieves all tasks assigned to staff's warehouse in `Pending` or `InProgress` state.
3. System sorts tasks by SLA deadline (most urgent first).
4. Each task displays: order ID, items with quantities, bin locations, and SLA countdown.
5. Staff selects a task and clicks "Start Picking".
6. System transitions task to `InProgress` and locks it to the staff member.

**Alternative Flows:**
- **2a.** No pending tasks → System displays "All caught up" message.
- **5a.** Staff already has a task in progress → System warns and requires completing or releasing current task.

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
- **5a.** Device offline → POD stored locally; sync triggered when connectivity resumes.
- **5b.** S3 upload fails → System retries 3 times; after failure, alerts operations and keeps order in `OutForDelivery`.
- **2a.** Recipient unavailable for signature → Staff records "left at door" with photo evidence only.

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
**Preconditions:** Returned item is received at warehouse.
**Postconditions:** Inspection result recorded; refund triggered (if accepted) or rejection sent (if rejected).

**Main Flow:**
1. Staff opens pending inspection queue.
2. Staff selects the return and reviews original order details and customer-stated reason.
3. Staff physically inspects the returned item.
4. Staff records inspection result: Accept, Reject (with reason), or Partial Accept.
5. System processes result:
   - Accept → Refund initiated; item returned to stock.
   - Reject → Customer notified with rejection reason.
   - Partial Accept → Partial refund initiated; customer notified.
6. System emits `return.inspected.v1` event.

**Alternative Flows:**
- **4a.** Item not matching order (wrong item returned) → Staff selects "Wrong Item" reason; operations manager notified for investigation.
