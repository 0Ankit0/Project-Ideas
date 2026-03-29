# Retention Redaction

## Scenario
Retention policy conflicts with legal holds.

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

## Retention and Redaction Edge Narrative
Retention jobs must account for active incidents and legal holds before deletion/redaction.

```mermaid
flowchart LR
    J[Retention Job] --> L{Legal Hold?}
    L -- yes --> K[Skip + Audit]
    L -- no --> R{Redaction Needed?}
    R -- yes --> X[Field-level Redaction]
    R -- no --> D[Delete by Policy]
    X --> A[Append Audit Proof]
    D --> A
```

Queue/workflow linkage is preserved via surrogate IDs after redaction so SLA/postmortem analytics remain valid.

Operational coverage note: this artifact also specifies omnichannel controls for this design view.
