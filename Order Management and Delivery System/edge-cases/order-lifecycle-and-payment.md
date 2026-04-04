# Edge Cases — Order Lifecycle and Payment

## EC-OLP-001: Concurrent Checkout for Same Inventory

**Scenario:** Two customers attempt checkout simultaneously for the last unit of a product.

**Trigger:** Race condition during inventory reservation.

**Expected Behaviour:**
- Inventory uses optimistic locking: `UPDATE inventory SET qty_reserved = qty_reserved + 1 WHERE qty_on_hand - qty_reserved >= 1`
- First transaction succeeds; second receives `409 Conflict: insufficient stock`
- No overselling occurs; database constraint enforces non-negative available quantity

**Severity:** Critical

---

## EC-OLP-002: Payment Gateway Timeout During Capture

**Scenario:** Payment gateway does not respond within 30 seconds during capture.

**Trigger:** Network partition or gateway overload.

**Expected Behaviour:**
- Payment Service waits 30 seconds (HTTP client timeout)
- On timeout, Service polls gateway for payment status using the idempotency key
- If gateway confirms capture → proceed normally
- If gateway confirms no capture → release reservation, return payment error to customer
- If gateway is unreachable → release reservation, emit `payment.timeout.v1` for manual investigation

**Severity:** Critical

---

## EC-OLP-003: Duplicate Checkout Request (Network Retry)

**Scenario:** Client retries checkout due to network error, sending the same `Idempotency-Key`.

**Trigger:** Client-side timeout followed by automatic retry.

**Expected Behaviour:**
- Idempotency Guard checks ElastiCache for the key
- If found → return cached response (200 OK with original order details)
- No duplicate order, payment, or inventory reservation created
- Idempotency key TTL: 24 hours

**Severity:** High

---

## EC-OLP-004: Payment Captured but Order Service Crashes Before DB Commit

**Scenario:** Payment gateway confirms capture, but Order Service crashes before persisting `Confirmed` status.

**Trigger:** Process crash, Lambda timeout, or OOM kill.

**Expected Behaviour:**
- Database transaction rolls back; order remains in `Draft` state
- Reservation TTL (15 min) will eventually expire and release stock
- `payment.captured.v1` event was NOT emitted (crash occurred before publish)
- Daily reconciliation job detects orphaned captures (captured but no confirmed order) and flags for manual review
- Resolution: Manual refund via finance portal or order reconstruction

**Severity:** Critical

---

## EC-OLP-005: Order Cancellation During Fulfillment Race

**Scenario:** Customer cancels order at the exact moment warehouse staff marks it as `ReadyForDispatch`.

**Trigger:** Concurrent state transitions from `Confirmed`.

**Expected Behaviour:**
- State machine uses optimistic locking: `UPDATE orders SET status = 'Cancelled' WHERE status = 'Confirmed' AND version = ?`
- One transition wins; the other receives `409 Conflict`
- If cancellation wins → inventory released, refund initiated
- If dispatch wins → cancellation rejected; customer informed order has been dispatched

**Severity:** High

---

## EC-OLP-006: Partial Payment Capture

**Scenario:** Gateway captures less than the full order amount due to insufficient funds (split capture scenario).

**Trigger:** Card has partial balance.

**Expected Behaviour:**
- System does NOT support partial captures; authorization is all-or-nothing
- On insufficient funds → gateway declines authorization; capture never attempted
- Order remains in `Draft`; reservation released; customer prompted to use different payment method

**Severity:** Medium

---

## EC-OLP-007: Coupon Applied After Price Change

**Scenario:** Product price changes between cart addition and checkout, affecting coupon eligibility.

**Trigger:** Admin updates product price while customer has item in cart.

**Expected Behaviour:**
- At checkout, system recalculates all prices from current catalog (not cached cart prices)
- Coupon minimum order value re-evaluated against new total
- If new total < coupon minimum → coupon rejected with message: "Order no longer meets minimum value"
- Customer sees updated breakdown before confirming

**Severity:** Medium

---

## EC-OLP-008: Refund to Expired or Closed Payment Method

**Scenario:** Customer's credit card expires or account is closed between payment and refund.

**Trigger:** Cancellation or return occurs weeks after original payment.

**Expected Behaviour:**
- System initiates refund to original payment method via gateway
- Gateway handles expired cards differently by provider:
  - Stripe: Refund still processed to the bank; card issuer routes funds
  - If gateway rejects: system retries up to 3 times, then flags for manual resolution
- Finance team processes manual refund (store credit or alternative method)

**Severity:** Medium

---

## EC-OLP-009: Order Modification After Payment But Before Dispatch

**Scenario:** Customer wants to change delivery address after order is confirmed.

**Trigger:** Customer requests address change via self-service or support.

**Expected Behaviour:**
- Address changes allowed only in `Confirmed` and `ReadyForDispatch` states
- New address validated against delivery zones; if not serviceable → change rejected
- Zone change may affect shipping fee:
  - If new fee ≠ old → system does NOT charge/refund the difference (business decision: original fee stands)
  - Operation logged with before/after values in audit trail
- If status is `PickedUp` or later → change rejected

**Severity:** Medium
