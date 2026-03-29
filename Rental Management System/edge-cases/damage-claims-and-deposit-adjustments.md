# Damage Claims and Deposit Adjustments

## Failure Modes
- Claim created without evidence package integrity
- Deposit release executed before inspection closure
- Dispute lifecycle not synchronized with settlement status

## Controls
- Evidence bundle requirements (photos, timestamps, checklist)
- Policy-guarded hold/release state machine
- Human-review checkpoint for high-value claims
## Implementation-Specific Addendum: Claims adjudication flow

### Domain-level decisions
- Define evidence requirements, approval chain, and deposit adjustment constraints.
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
