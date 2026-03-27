# Operations Edge Cases

## Failure Mode
Regional outage prevents live check-in/check-out updates for field teams.

## Impact
Operational backlog, delayed availability refresh, and potential allocation errors.

## Detection
Heartbeat and sync-lag monitors identify prolonged offline mode thresholds by region.

## Recovery / Mitigation
Enable offline queueing with signed local events, controlled replay windows, and post-recovery reconciliation runbooks.
