# E-Commerce Edge Cases

This pack captures high-risk failure scenarios across checkout, inventory, shipping, and post-order settlement.

## Included Scenarios
- cart-checkout-and-payment-failures
- inventory-allocation-and-oversell
- shipping-and-delivery-exceptions
- returns-refunds-and-vendor-reconciliation
- api-and-ui
- security-and-compliance
- operations

Each scenario covers failure mode, impact, detection, and recovery/mitigation actions.

## Newly Emphasized Failure Patterns
- Double-charge prevention during retry storms
- Lost webhook replay for payment/order convergence
- Payment timeout after authorization
- Stale inventory race between cache and reservation source-of-truth
- Partial shipment/backorder refund integrity
- Refund reversal and compensating ledger controls
