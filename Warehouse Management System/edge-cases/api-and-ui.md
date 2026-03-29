# API and UI Edge Cases

## API Failure Modes

| Case | Trigger | API Behavior | UI Behavior |
|---|---|---|---|
| Duplicate submit | Scanner retries after timeout | Return prior response by idempotency key | Show "already processed" with original timestamp |
| Version conflict | Stale task version | `409` with latest version metadata | Prompt user to refresh task and retry |
| Partial composite failure | Pack close succeeds, label fails | `202` with `PackingBlocked` status | Route operator to remediation queue |

## UI Consistency Rules
- UI must display backend authoritative state and last sync timestamp.
- Optimistic updates require rollback UI path when server rejects transition.
- Error toast includes `correlation_id` for support handoff.

## Contract Example
```json
{
  "code": "RESERVATION_MISMATCH",
  "retryable": false,
  "rule_id": "BR-7",
  "correlation_id": "c-123"
}
```
