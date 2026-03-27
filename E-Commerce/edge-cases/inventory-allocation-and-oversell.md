# Inventory Allocation and Oversell

## Failure Mode
Parallel checkout sessions reserve the same low-stock SKU due to stale cache and delayed lock propagation.

## Impact
Oversell causes cancellation risk, vendor trust erosion, and fulfillment churn.

## Detection
Allocation monitor detects negative available-to-promise counts or backorder spikes post-payment.

## Recovery / Mitigation
Use atomic stock reservation with expiration, prioritize earliest paid order, and trigger substitution/compensation playbooks.
