# Cycle Count Adjustments

## Scenario
Count variance occurs while active picks are in progress.

## Decision Matrix

| Condition | Action |
|---|---|
| Small variance within tolerance | supervisor approval + adjustment ledger |
| Large variance / suspected loss | quarantine bin + investigation case |
| Open pick tasks affected | pause impacted tasks + replan |

## Safe Adjustment Sequence
```mermaid
sequenceDiagram
    participant Counter
    participant INV as Inventory Service
    participant OPS as Operations Service

    Counter->>INV: submit recount result
    INV->>INV: compare with active reservations
    alt impacts active tasks
      INV->>OPS: create investigation case
      INV-->>Counter: tasks paused
    else no impact
      INV->>INV: write adjustment ledger
      INV-->>Counter: adjustment confirmed
    end
```
