# Payment Reconciliation Across Channels

## Failure Modes
- Card, wallet, and bank-transfer settlements arriving asynchronously
- Gateway fee adjustments not reflected in internal ledger
- Refund/cancellation mismatch across sub-ledgers

## Controls
- Daily three-way reconciliation (bookings, gateway reports, GL)
- Adjustment journal entries with approval workflow
- Exception dashboard with aging SLA and ownership
## Implementation-Specific Addendum: Multi-channel settlement drift

### Domain-level decisions
- Reconcile branch POS, web, and gateway events to canonical ledger state.
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
