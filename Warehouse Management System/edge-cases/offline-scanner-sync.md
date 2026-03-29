# Offline Scanner Sync

## Scenario
Scanner reconnects and uploads buffered events that may conflict with current state.

## Replay Rules
- Events must be ordered by device sequence number.
- Each event uses deterministic idempotency key (`device_id + sequence_no`).
- Version conflicts generate review tasks, never silent overwrite.

## Conflict Resolution Flow
```mermaid
flowchart TD
    A[Device reconnects] --> B[Upload buffered events]
    B --> C[Validate sequence + signature]
    C --> D{State version matches?}
    D -- Yes --> E[Apply event]
    D -- No --> F[Create replay conflict case]
    F --> G[Supervisor resolve merge/compensate]
    G --> H[Apply approved action]
```

## Verification
- Post-sync invariant check: no negative ATP, no duplicate ledger rows.
- Device receives reconciliation summary for operator confirmation.
