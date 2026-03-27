# Inventory Availability Conflicts

## Failure Modes
- Double-booking due to race conditions between hold and confirm operations
- Late check-in/check-out updates that overstate available stock
- Availability cache staleness across channels

## Controls
- Optimistic locking + short hold TTL + conflict reason codes
- Deterministic inventory arbitration rules and queue ordering
- Real-time invalidation on booking lifecycle events
