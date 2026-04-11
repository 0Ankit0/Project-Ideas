# Edge Cases & Mitigations - Slot Booking System

This folder captures edge cases across availability, booking, cancellations, notifications, API/UI, security, and operations.

## Contents

- Slot availability: see [edge-cases/slot-availability.md](edge-cases/slot-availability.md)
- Booking & payments: see [edge-cases/booking-and-payments.md](edge-cases/booking-and-payments.md)
- Cancellations & refunds: see [edge-cases/cancellations-and-refunds.md](edge-cases/cancellations-and-refunds.md)
- Notifications: see [edge-cases/notifications.md](edge-cases/notifications.md)
- API & UI: see [edge-cases/api-and-ui.md](edge-cases/api-and-ui.md)
- Security & compliance: see [edge-cases/security-and-compliance.md](edge-cases/security-and-compliance.md)
- Operations: see [edge-cases/operations.md](edge-cases/operations.md)

---
## Implementation-Ready Readme

### Slot allocation rules in this document's context
- Allocation decisions must be based on **resource calendar + operational policy + channel limits** before any payment action is attempted.
- All provisional allocations require an explicit **hold record with expiry**, and expiry must be visible to clients.
- Shared-capacity resources must use atomic decrement semantics; exclusive resources must enforce single-active-booking constraints.

### Conflict resolution in this document's context
- Competing writes must use deterministic conflict handling (optimistic version checks or transactional locks as documented here).
- API and admin paths must converge on one canonical conflict reason taxonomy (`SLOT_TAKEN`, `STALE_VERSION`, `PROVIDER_BLOCKED`, `PAYMENT_STATE_MISMATCH`).
- Every conflict rejection must emit structured audit telemetry including actor, correlation ID, and rule version.

### Payment coupling / decoupling behavior
- **Coupled flow**: booking moves to confirmed only after successful authorization/capture.
- **Decoupled flow**: booking can be confirmed with `PAYMENT_PENDING`, but with a bounded grace window and auto-cancel guardrail.
- Compensation is mandatory for split-brain outcomes (payment succeeded but booking failed, or inverse).

### Cancellation and refund policy detail
- Refund outcomes depend on lead time, policy tier, no-show status, and jurisdiction-specific fee constraints.
- Refund processing must be idempotent and expose lifecycle states (`REQUESTED`, `INITIATED`, `SETTLED`, `FAILED`, `MANUAL_REVIEW`).
- Cancellation side effects must include slot reallocation and downstream notification consistency.

### Observability and incident playbook focus
- Monitor: availability latency, hold expiry lag, conflict rate, payment callback success, refund aging.
- Alerts must map to operator runbooks with first-response steps and data reconciliation queries.
- Post-incident review must record policy gaps and required control changes for this documentation area.

### Edge-case verification checklist
- Duplicate client retries and duplicate payment callbacks.
- Boundary-time cancellations (exact cutoff minute, timezone shifts, DST transitions).
- Partial outage handling for notification and payment provider dependencies.

## Additional Distributed-Flow Edge Cases

### 1) Concurrent booking collisions
- **Case**: Multiple users reserve the same high-demand slot within milliseconds.
- **Mitigation**: Atomic hold + fencing tokens + deterministic conflict response (`409 SLOT_TAKEN`).
- **Validation**: Load test with synchronized clients and conflict-rate SLO monitoring.

### 2) Clock skew across clients/services
- **Case**: Client clock or one service node drifts, causing incorrect hold countdown or premature expiry actions.
- **Mitigation**: Treat server UTC as authority; include `server_now_utc` in all reserve/confirm responses; enforce NTP alarms.
- **Validation**: Chaos test with +/-120s injected skew on selected nodes.

### 3) Payment success after slot timeout
- **Case**: PSP callback arrives after hold expired and slot was reallocated.
- **Mitigation**: Never auto-confirm on stale hold; route to compensation saga (refund or operator intervention).
- **Validation**: Simulate delayed webhook and verify `PAYMENT_LATE_AFTER_TIMEOUT` handling path.

### 4) Stale availability reads
- **Case**: User sees slot available from cache snapshot but slot was just taken.
- **Mitigation**: Reserve call remains source of truth; include freshness metadata (`as_of_utc`) in availability responses.
- **Validation**: Ensure stale read still leads to safe reserve rejection without double-booking.

### 5) No-show penalty disputes
- **Case**: Customer disputes no-show charge due to check-in proof mismatch.
- **Mitigation**: Immutable audit trail for reminder notifications, check-in scans, geofence/device evidence, and policy version at booking time.
- **Validation**: Replay dispute packet and verify reproducible policy decision outcome.
