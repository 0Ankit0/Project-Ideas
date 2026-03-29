# Inventory Allocation and Wave Planning

## Problem Scope
Define deterministic allocation and wave planning behavior under high throughput and partial-failure conditions.

## Allocation Policy Model

| Policy Dimension | Strategy | Default |
|---|---|---|
| Stock rotation | FIFO / FEFO | FEFO for lot-controlled SKUs |
| Zone preference | Nearest pick zone first | Enabled |
| Priority | SLA tier then order age | SLA tier > age |
| Split policy | Minimize carton splits | Enabled with max-split threshold |

## Core Invariants
1. Reservable ATP never negative after commit.
2. Allocation writes and reservation events commit atomically.
3. Wave generation is deterministic for same input snapshot and policy version.

## Execution Steps
1. Build candidate stock set by `warehouse_id`, SKU, and eligibility filters.
2. Score candidates using policy weights.
3. Reserve stock with optimistic concurrency (`version` check).
4. Generate pick tasks grouped by zone/path optimization.
5. Emit allocation and wave events through outbox.

## Failure and Compensation
- Concurrency conflict -> retry with fresh snapshot and bounded attempts.
- Mid-wave stock loss -> deallocate impacted lines and trigger replan.
- Worker crash after DB commit -> outbox relay guarantees downstream event publication.

## Operational Metrics
- Reservation conflict rate by SKU and warehouse.
- Wave plan build latency and task-count distribution.
- Replan frequency due to short picks or damaged stock.

## Rule and Artifact Mapping
- BR-7: reservation + ATP protection.
- BR-5: idempotent retries and compensation safety.
- BR-10: deterministic recovery for short picks/replans.
