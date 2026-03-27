# API and UI Edge Cases

## Failure Mode
UI submits stale reservation versions leading to silent overwrite or conflict loops.

## Impact
User confusion, duplicate retries, and inconsistent lifecycle timelines.

## Detection
Client/server conflict metrics show elevated optimistic-lock failures.

## Recovery / Mitigation
Expose explicit conflict payloads, enable guided merge/retry UX, and enforce version-based writes.
