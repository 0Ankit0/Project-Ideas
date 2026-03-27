# API and UI Edge Cases

## Failure Mode
API accepts update while UI displays stale order/payment states due to cached query mismatch.

## Impact
Users retry actions, causing duplicate submissions and inconsistent expectations.

## Detection
Client telemetry identifies repeated action attempts following stale-state responses.

## Recovery / Mitigation
Adopt ETag/versioned resources, explicit conflict responses, and forced client refetch on critical transitions.
