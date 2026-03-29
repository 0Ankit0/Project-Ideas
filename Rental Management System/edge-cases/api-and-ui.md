# API and UI Edge Cases

- Duplicate booking submission under flaky mobile networks
- Calendar stale views during concurrent holds and confirmations
- Quote-to-contract mismatch after pricing rule changes
- Return workflow interruptions with offline staff tablets
## Implementation-Specific Addendum: Client/server consistency failures

### Domain-level decisions
- Handle stale client state, concurrent edits, and optimistic UI rollbacks.
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
