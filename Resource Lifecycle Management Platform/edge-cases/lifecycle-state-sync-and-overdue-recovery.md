# Lifecycle State Sync and Overdue Recovery

## Failure Mode
Resource remains marked as in-use after check-in due to failed state event propagation.

## Impact
Availability is underreported, causing utilization loss and booking friction.

## Detection
State drift job identifies records where physical scan/check-in exists but lifecycle state is stale.

## Recovery / Mitigation
Trigger corrective state transition workflow, replay missing events, and notify impacted allocation services.
