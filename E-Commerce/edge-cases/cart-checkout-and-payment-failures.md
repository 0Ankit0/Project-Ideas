# Cart, Checkout, and Payment Failures

## Failure Mode
Payment authorization succeeds at provider edge but checkout service times out before order confirmation is persisted.

## Impact
Customers may be charged without visible orders; support volume and abandonment increase.

## Detection
Reconciliation job flags unmatched successful payment intents without corresponding confirmed orders.

## Recovery / Mitigation
Implement idempotent checkout tokens, provider webhook replay, and auto-order reconstruction workflow with customer notification.
