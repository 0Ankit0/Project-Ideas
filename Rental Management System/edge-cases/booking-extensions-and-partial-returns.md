# Booking Extensions and Partial Returns

## Failure Modes
- Extension approved despite conflicting future reservation
- Partial return billed as full return or vice versa
- Asset state split across units/components not reflected in contract

## Controls
- Extension pre-check against dependent reservations and buffers
- Unit-level return events and pro-rated billing adjustments
- Explicit partial-fulfillment/partial-return state model
## Implementation-Specific Addendum: Mid-rental change complexity

### Domain-level decisions
- Cover repricing, partial settlement, and residual asset availability updates.
- Capture booking lifecycle transition metadata (`actor`, `reason_code`, `request_id`, `policy_version`) for auditability.
- Keep pricing and deposit calculations reproducible from immutable snapshots to support dispute handling.

### Failure handling and recovery
- Define explicit compensation steps for payment success + booking write failure, including replay and operator tooling.
- Record availability conflict outcomes with deterministic winner selection and customer alternative suggestions.
- For maintenance interruptions, document swap/refund decision matrix with SLA-based customer communications.

### Implementation test vectors
- Concurrency: 50+ parallel hold requests on same asset/time window with deterministic outcomes.
- Financial: partial deposit capture + late fee + damage adjustment with tax correctness.
- Operations: offline check-in/check-out replay with out-of-order events and final state convergence.
