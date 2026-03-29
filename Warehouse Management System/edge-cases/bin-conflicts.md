# Bin Conflicts

## Scenario
Concurrent picks/reservations target same bin causing over-commit risk.

## Detection
- Reservation conflict rate per bin exceeds threshold.
- Negative ATP guard attempted (blocked) events increase.

## Resolution Workflow
```mermaid
flowchart TD
    A[Conflict detected] --> B[Lock bin partition]
    B --> C[Recompute eligible stock]
    C --> D{Alternate bin available?}
    D -- Yes --> E[Reallocate task]
    D -- No --> F[Create backorder/hold]
    E --> G[Audit + notify operator]
    F --> G
```

## Preventive Controls
- Bin-level hot-spot monitoring.
- Dynamic wave throttling for over-subscribed zones.
- Reservation conflict chaos tests in CI.
