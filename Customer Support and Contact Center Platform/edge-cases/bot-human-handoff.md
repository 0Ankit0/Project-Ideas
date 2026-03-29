# Bot Human Handoff

## Scenario
Context transfer failures between bot and agent.

## Detection Signals
- Error-rate and latency anomalies on affected services.
- Data integrity checks (duplicate keys, missing transitions, imbalance alerts).
- Queue lag or webhook retry saturation above SLO thresholds.

## Immediate Containment
- Pause risky automation path via feature flag/runbook switch.
- Route affected records into review queue with owner assignment.
- Notify operations channel with incident context and blast radius.

## Recovery Steps
- Reconcile canonical state from source-of-truth events and logs.
- Apply deterministic compensating updates with audit annotations.
- Backfill downstream projections and verify invariant checks pass.

## Prevention
- Add contract tests and chaos scenarios for this edge condition.
- Instrument specific leading indicators and alert tuning.

## Bot-to-Human Handoff Deep Dive
Handoff is treated as a transactional workflow: bot context capture, queue assignment, SLA carryover, and human acknowledgment.

```mermaid
flowchart LR
    B[Bot Session] --> C[Collect Context + Intent]
    C --> Q[Create Queue Item]
    Q --> H[Assign Human Agent]
    H --> A{Agent Acknowledged?}
    A -- yes --> T[Transfer Transcript]
    A -- no --> E[Escalate to Backup Queue]
```

- First-response SLA continues from original customer message, not handoff timestamp.
- Transcript redactions must happen before human exposure when policy flags require it.
- Failed handoffs emit high-priority incident telemetry.

Operational coverage note: this artifact also specifies omnichannel controls for this design view.
