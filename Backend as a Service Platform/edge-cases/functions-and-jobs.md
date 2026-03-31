# Edge Cases – Functions and Jobs

## Scenarios

| # | Scenario | Severity | Risk | Mitigation |
|---|----------|----------|------|-----------|
| 1 | Runtime backend has cold-start latency spikes | High | Unpredictable execution latency | Publish P99 cold-start profiles per runtime; support warm capacity reservations via binding config |
| 2 | Function execution exceeds configured timeout | Medium | Client hangs or receives misleading error | Hard timeout enforced by Functions Facade; execution moved to `timed-out` state; client receives `EXECUTION_TIMEOUT` |
| 3 | Function deployment artifact fails security scan | High | Malicious code deployed to production | All artifacts scanned before `scan-passed` state transition; blocked artifact gets `scan-failed` and deployment halted |
| 4 | Scheduled job skipped due to worker downtime | Medium | Silent missed execution | Track `scheduled_executions` with `expected_at`; missed jobs logged as `SCHEDULE_MISSED` events and re-fired if within tolerance window |
| 5 | Concurrent invocations exceed function concurrency limit | Medium | Provider-side throttling, failed executions | Functions Facade enforces concurrency limit via Redis atomic counter before dispatching; excess requests receive `EXECUTION_CONCURRENCY_LIMIT` |
| 6 | Function deployment to new provider fails mid-rollout | High | Old and new provider serve traffic simultaneously | Blue-green deployment: new provider only receives traffic after health probe succeeds; rollback to old provider on failure |
| 7 | Execution log storage full or unavailable | Low | Debugging blocked; executions still complete | Logs buffered in worker memory (512 KB); flushed asynchronously; client informed logs may be delayed |
| 8 | Function invoked with payload exceeding size limit | Low | Provider-level rejection with confusing error | Validate payload size (default 6 MB) at Functions Facade before forwarding; return `EXECUTION_PAYLOAD_TOO_LARGE` |

## Deep Edge Cases

### Timeout Enforcement
Functions Facade sets a deadline context before dispatching to the adapter:
```go
ctx, cancel := context.WithTimeout(ctx, time.Duration(fn.TimeoutSeconds)*time.Second)
defer cancel()
result, err := adapter.InvokeFunction(ctx, req)
if errors.Is(err, context.DeadlineExceeded) {
    updateExecutionState(execId, "timed-out")
    return nil, ErrExecutionTimeout
}
```

### Concurrent Invocation Guard
```typescript
const key = `concurrency:${functionId}`;
const current = await redis.incr(key);
await redis.expire(key, 60); // safety TTL
if (current > fn.maxConcurrency) {
  await redis.decr(key);
  return err(new ConcurrencyLimitError(fn.maxConcurrency));
}
// ... dispatch, then decr on completion
```

### Missed Schedule Recovery
- Scheduler worker checks every minute for `scheduled_executions` with `expected_at < NOW() - 1 minute` and `state = 'pending'`.
- If within `missed_tolerance_seconds` (configurable, default 300s): re-fire and mark `late`.
- If beyond tolerance: mark `missed`, emit `ScheduleMissed` event, notify owner.

## State Impact Summary

| Scenario | Execution State |
|----------|----------------|
| Successful execution | `queued` → `dispatched` → `running` → `completed` |
| Timeout | `running` → `timed-out` |
| Concurrency limit | Rejected before `queued` |
| Scan failure | `uploaded` → `scan-failed` (deployment halted) |
| Missed schedule | `pending` → `missed` (or `late` if re-fired) |
