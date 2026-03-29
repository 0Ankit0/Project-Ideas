# Thread Deduplication

## Scenario
Duplicate case detection across channels.

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

## Thread Deduplication Edge Narrative
Deduplication must prevent fragmented queues and double SLA penalties when external systems retry.

```mermaid
flowchart TD
    E[Inbound Event] --> K[Build Dedup Key]
    K --> D{Seen Before?}
    D -- yes --> M[Merge into Existing Thread]
    D -- no --> N[Create New Thread]
    M --> A[Audit Merge Decision]
    N --> A
```

Use multi-signal keys (`customer_identity`, normalized subject, channel message ID, ±time window) and keep manual split/merge audit trails.

Operational coverage note: this artifact also specifies omnichannel controls for this design view.
