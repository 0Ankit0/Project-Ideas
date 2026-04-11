# Cart, Checkout, and Payment Failures

## Failure Mode
Payment authorization succeeds at provider edge but checkout service times out before order confirmation is persisted.

## Impact
Customers may be charged without visible orders; support volume and abandonment increase.

## Detection
Reconciliation job flags unmatched successful payment intents without corresponding confirmed orders.

## Recovery / Mitigation
Implement idempotent checkout tokens, provider webhook replay, and auto-order reconstruction workflow with customer notification.

---

## Failure Mode
Duplicate charge risk when client retries checkout while first attempt succeeded but response was lost.

## Impact
Customer billed multiple times, increased refund workload, regulatory complaint exposure.

## Detection
Charge monitor flags same customer + cart fingerprint + amount charged multiple times within a short window.

## Recovery / Mitigation
Enforce end-to-end idempotency keys (client, API, provider), auto-void secondary authorizations, and notify customer with single canonical order.

---

## Failure Mode
Payment authorization succeeds but capture times out; order remains pending near SLA boundary.

## Impact
Inventory stays locked, fulfillment blocked, and customer sees uncertain payment status.

## Detection
Authorization aging job finds intents in `AUTHORIZED` beyond capture timeout threshold.

## Recovery / Mitigation
Run capture retry policy with bounded attempts, then auto-void authorization and release reservation if capture does not complete.

---

## Failure Mode
Lost payment webhook prevents confirmation despite successful provider processing.

## Impact
Order can remain in limbo and customer support contacts increase.

## Detection
Scheduled reconciliation compares provider success events against internal payment/order states and detects orphaned transactions.

## Recovery / Mitigation
Use webhook replay endpoint + provider polling fallback + dead-letter queue redrive with idempotent event handlers.
