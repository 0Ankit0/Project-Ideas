# Offline Check-in/Check-out Sync Conflicts

## Failure Modes
- Staff device records events offline with stale contract version
- Duplicate sync on reconnect produces double transitions
- Clock skew causes out-of-order event application

## Controls
- Event versioning and conflict resolution by authoritative timeline
- Idempotent event keys and sync acknowledgements
- Manual reconciliation queue for unresolved conflicts
## Implementation-Specific Addendum: Offline sync reconciliation

### Domain-level decisions
- Resolve divergent timelines with deterministic merge and audit traces.
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
