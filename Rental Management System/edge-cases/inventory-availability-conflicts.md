# Inventory Availability Conflicts

## Failure Modes
- Double-booking due to race conditions between hold and confirm operations
- Late check-in/check-out updates that overstate available stock
- Availability cache staleness across channels

## Controls
- Optimistic locking + short hold TTL + conflict reason codes
- Deterministic inventory arbitration rules and queue ordering
- Real-time invalidation on booking lifecycle events
## Implementation-Specific Addendum: Oversubscription contention

### Domain-level decisions
- Detail lock conflict outcomes and substitute asset recommendation policy.
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
