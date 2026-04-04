# Edge Cases — Returns and Refunds

## EC-RR-001: Return Request at Window Boundary

**Scenario:** Customer initiates return at 23:59:59 on the last day of the return window.

**Trigger:** Timezone edge case; customer in different timezone from server.

**Expected Behaviour:**
- Return window calculated using server timezone (UTC)
- `delivered_at + return_window_days` compared against request timestamp in UTC
- If request arrives before deadline (even by 1 second) → accepted
- If request arrives after → rejected with clear message showing expiry timestamp
- No grace period — deadline is strict

**Severity:** Low

---

## EC-RR-002: Return for Partially Delivered Order

**Scenario:** Order had multiple items but one was out of stock and removed during fulfillment. Customer wants to return remaining items.

**Trigger:** Partial fulfillment scenario.

**Expected Behaviour:**
- Return request shows only items actually delivered (from fulfillment task records)
- Customer can select which delivered items to return
- Refund calculated based on selected items' prices
- Items that were removed pre-fulfillment are already refunded/not charged

**Severity:** Medium

---

## EC-RR-003: Wrong Item Returned by Customer

**Scenario:** Customer returns a completely different item than what was ordered.

**Trigger:** Customer error or fraud attempt.

**Expected Behaviour:**
- Warehouse staff selects inspection result: "Reject — Wrong Item"
- System notifies customer: "Return rejected — item does not match order"
- Operations manager receives alert for potential fraud review
- Original item's return eligibility is preserved (window doesn't reset)
- Wrong item held at warehouse for customer pickup or disposal per policy

**Severity:** Medium

---

## EC-RR-004: Refund Gateway Failure

**Scenario:** Payment gateway returns an error when processing the refund.

**Trigger:** Gateway downtime, card issuer rejection, or network failure.

**Expected Behaviour:**
- Payment Service retries with exponential backoff (base 1 s, 3 retries)
- If all retries fail → refund record status set to `failed`
- Alert sent to finance team for manual processing
- Customer notified: "Refund is being processed manually; please allow 5-7 business days"
- Finance can process manual refund via alternative method

**Severity:** High

---

## EC-RR-005: Return Pickup Staff Cannot Locate Customer

**Scenario:** Delivery staff goes to collect return but customer is unavailable.

**Trigger:** Customer not at address or unresponsive.

**Expected Behaviour:**
- Staff records "Customer Unavailable" for return pickup
- System reschedules pickup for next available window
- After 3 failed pickup attempts → return request cancelled
- Customer notified to drop off item at designated location (if applicable)
- Return window does NOT extend during pickup retry period

**Severity:** Medium

---

## EC-RR-006: Concurrent Return and Refund Processing

**Scenario:** Finance initiates manual refund for an order while automated return inspection also triggers a refund.

**Trigger:** Race condition between manual and automated refund paths.

**Expected Behaviour:**
- Refund operations use optimistic locking on payment transaction
- Total refunded amount tracked: `SUM(refund_records.amount) WHERE payment_id = ?`
- Guard: `new_refund_amount + total_already_refunded <= original_capture_amount`
- If guard fails → second refund attempt rejected with "Refund exceeds original amount"
- Both refund records preserved in audit trail for investigation

**Severity:** Critical
