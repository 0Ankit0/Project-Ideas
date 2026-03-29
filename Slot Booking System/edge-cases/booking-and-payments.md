# Edge Cases - Booking & Payments

### 2.1. Double Booking Due to Race Conditions
* **Scenario**: Two users try to book the same slot simultaneously.
* **Impact**: Duplicate confirmations and disputes.
* **Solution**:
    * **Locking**: Use atomic reservation with short TTL.
    * **Idempotency**: Enforce idempotency keys on booking creation.

### 2.2. Payment Authorized but Booking Not Confirmed
* **Scenario**: Payment succeeds but booking confirmation fails.
* **Impact**: Customer charged without a booking.
* **Solution**:
    * **Transactions**: Use outbox pattern for booking/payment consistency.
    * **Recovery**: Auto-refund if confirmation fails.

### 2.3. Price Changes After Reservation
* **Scenario**: Provider updates price after slot is reserved.
* **Impact**: Mismatched totals.
* **Solution**:
    * **Policy**: Lock price for reservation TTL.
    * **UI**: Prompt user if price changes after TTL.

---
## Implementation-Ready Booking And Payments

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
