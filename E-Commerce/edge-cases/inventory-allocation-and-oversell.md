# Inventory Allocation and Oversell

## Failure Mode
Parallel checkout sessions reserve the same low-stock SKU due to stale cache and delayed lock propagation.

## Impact
Oversell causes cancellation risk, vendor trust erosion, and fulfillment churn.

## Detection
Allocation monitor detects negative available-to-promise counts or backorder spikes post-payment.

## Recovery / Mitigation
Use atomic stock reservation with expiration, prioritize earliest paid order, and trigger substitution/compensation playbooks.

---

## Failure Mode
Stale inventory race: cache reports in-stock while source-of-truth reservation just consumed the final units.

## Impact
Checkout failures at payment stage, poor conversion, and inconsistent customer trust.

## Detection
Mismatch alert on cache ATP vs database ATP beyond threshold and spike in reservation-conflict errors.

## Recovery / Mitigation
Treat cache as advisory only, enforce DB-backed atomic reservation at checkout, and invalidate cache on reservation/commit/release events.
