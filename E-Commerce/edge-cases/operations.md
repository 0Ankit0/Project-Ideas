# Operations Edge Cases

## Failure Mode
Background jobs for order orchestration backlog after a messaging partition event.

## Impact
Delayed confirmations, stale tracking, and SLA breach risk.

## Detection
Queue lag and oldest-message age alerts exceed SLO thresholds.

## Recovery / Mitigation
Scale consumers, replay dead letters safely, and run controlled catch-up with customer communications prioritization.
