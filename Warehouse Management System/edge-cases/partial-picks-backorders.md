# Partial Picks and Backorders

## Scenario
Picker cannot fulfill full reserved quantity due to shortage or damage.

## Policy
- Prefer alternate-bin reallocation before creating backorder.
- Preserve already-picked quantity and split remaining line.
- Customer promise date recalculated based on replenishment ETA.

## Handling Flow
```mermaid
flowchart TD
    A[Short pick reported] --> B[Check alternate bin]
    B --> C{Stock found?}
    C -- Yes --> D[Create follow-up pick task]
    C -- No --> E[Split line + backorder remainder]
    D --> F[Update order allocation]
    E --> F
    F --> G[Emit customer impact event]
```

## Required Outputs
- Updated reservation records.
- Backorder reason code and expected recovery date.
- SLA impact metric increment.
