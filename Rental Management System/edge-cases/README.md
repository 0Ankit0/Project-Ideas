# Edge Cases — Rental Management System

This directory contains detailed edge-case documentation for the Rental Management System. Each file covers a specific domain, catalogues failure modes with criticality ratings, and specifies resolution strategies that must be implemented before production launch.

---

## How to Use These Documents

1. **Before writing a feature** — read the relevant edge-case file and confirm every listed scenario is handled in the implementation plan.
2. **During code review** — verify that the PR addresses the applicable edge cases and that unit/integration tests cover each P0 and P1 scenario.
3. **During QA** — use the edge-case IDs as test-case labels (e.g., `EC-INV-001`) to link test results back to requirements.
4. **During incident review** — reference the edge-case ID in post-mortems to close gaps or upgrade criticality ratings.
5. **Criticality changes** — any engineer can propose a criticality upgrade via PR. A P0 downgrade requires tech-lead approval.

---

## Criticality Rating Definitions

| Rating | Meaning | Response SLA |
|--------|---------|--------------|
| **P0** | Data loss, financial loss, security breach, complete service outage | Must be fixed before launch |
| **P1** | Significant user-facing defect, incorrect billing, booking failure | Must be fixed in current sprint |
| **P2** | Minor UX degradation, non-critical workflow failure | Fix in next sprint or backlog |

---

## Master Edge-Case Index

### Inventory & Availability

| ID | Category | Description | Criticality | Status | Linked File |
|----|----------|-------------|-------------|--------|-------------|
| EC-INV-001 | Concurrency | Two customers book the same asset simultaneously | P0 | Open | [inventory-availability-conflicts.md](./inventory-availability-conflicts.md) |
| EC-INV-002 | Concurrency | Double-booking despite row-level lock | P0 | Open | [inventory-availability-conflicts.md](./inventory-availability-conflicts.md) |
| EC-INV-003 | State | Asset locked for pickup but not checked out within grace period | P1 | Open | [inventory-availability-conflicts.md](./inventory-availability-conflicts.md) |
| EC-INV-004 | State | Asset marked available but actually in maintenance | P0 | Open | [inventory-availability-conflicts.md](./inventory-availability-conflicts.md) |
| EC-INV-005 | State | Asset breaks down after booking confirmed but before pickup | P1 | Open | [inventory-availability-conflicts.md](./inventory-availability-conflicts.md) |
| EC-INV-006 | Calculation | Fleet-wide availability window calculation includes maintenance overlap | P1 | Open | [inventory-availability-conflicts.md](./inventory-availability-conflicts.md) |
| EC-INV-007 | Resolution | No substitute asset available for displaced booking | P1 | Open | [inventory-availability-conflicts.md](./inventory-availability-conflicts.md) |

### Booking Extensions & Partial Returns

| ID | Category | Description | Criticality | Status | Linked File |
|----|----------|-------------|-------------|--------|-------------|
| EC-EXT-001 | Conflict | Extension conflicts with next confirmed booking | P0 | Open | [booking-extensions-and-partial-returns.md](./booking-extensions-and-partial-returns.md) |
| EC-EXT-002 | Pricing | Extension spans rate-period boundary (different daily rate) | P1 | Open | [booking-extensions-and-partial-returns.md](./booking-extensions-and-partial-returns.md) |
| EC-EXT-003 | Return | Partial return from multi-asset booking | P1 | Open | [booking-extensions-and-partial-returns.md](./booking-extensions-and-partial-returns.md) |
| EC-EXT-004 | Payment | Extension approved but payment capture fails | P0 | Open | [booking-extensions-and-partial-returns.md](./booking-extensions-and-partial-returns.md) |
| EC-EXT-005 | Timing | Extension request arrives after scheduled return time | P1 | Open | [booking-extensions-and-partial-returns.md](./booking-extensions-and-partial-returns.md) |
| EC-EXT-006 | Billing | Multiple consecutive extensions with cumulative pricing errors | P1 | Open | [booking-extensions-and-partial-returns.md](./booking-extensions-and-partial-returns.md) |
| EC-EXT-007 | Refund | Pro-rated refund on early return is calculated incorrectly | P1 | Open | [booking-extensions-and-partial-returns.md](./booking-extensions-and-partial-returns.md) |

### Damage Claims & Deposit Adjustments

| ID | Category | Description | Criticality | Status | Linked File |
|----|----------|-------------|-------------|--------|-------------|
| EC-DAM-001 | Pre-existing | Customer claims damage was pre-existing but not documented | P1 | Open | [damage-claims-and-deposit-adjustments.md](./damage-claims-and-deposit-adjustments.md) |
| EC-DAM-002 | Financial | Damage cost exceeds security deposit (gap collection) | P0 | Open | [damage-claims-and-deposit-adjustments.md](./damage-claims-and-deposit-adjustments.md) |
| EC-DAM-003 | Dispute | Customer disputes damage within 72-hour window | P1 | Open | [damage-claims-and-deposit-adjustments.md](./damage-claims-and-deposit-adjustments.md) |
| EC-DAM-004 | Calculation | Multiple damage items on same rental, aggregate exceeds deposit | P1 | Open | [damage-claims-and-deposit-adjustments.md](./damage-claims-and-deposit-adjustments.md) |
| EC-DAM-005 | Insurance | Damage triggers insurance claim flow | P1 | Open | [damage-claims-and-deposit-adjustments.md](./damage-claims-and-deposit-adjustments.md) |
| EC-DAM-006 | Write-off | Total loss — asset must be written off | P0 | Open | [damage-claims-and-deposit-adjustments.md](./damage-claims-and-deposit-adjustments.md) |
| EC-DAM-007 | Financial | Rental + damage + late fee exceeds deposit; additional charge needed | P0 | Open | [damage-claims-and-deposit-adjustments.md](./damage-claims-and-deposit-adjustments.md) |
| EC-DAM-008 | Timing | Damage discovered after deposit already released | P0 | Open | [damage-claims-and-deposit-adjustments.md](./damage-claims-and-deposit-adjustments.md) |

### Offline Sync Conflicts

| ID | Category | Description | Criticality | Status | Linked File |
|----|----------|-------------|-------------|--------|-------------|
| EC-OFF-001 | Connectivity | Staff app goes offline mid-checkout | P0 | Open | [offline-checkin-checkout-sync-conflicts.md](./offline-checkin-checkout-sync-conflicts.md) |
| EC-OFF-002 | Conflict | Booking updated on server while staff device is offline | P1 | Open | [offline-checkin-checkout-sync-conflicts.md](./offline-checkin-checkout-sync-conflicts.md) |
| EC-OFF-003 | Data | Signature captured offline — sync lost on app crash | P0 | Open | [offline-checkin-checkout-sync-conflicts.md](./offline-checkin-checkout-sync-conflicts.md) |
| EC-OFF-004 | Media | Photos queued offline — partial upload on reconnect | P1 | Open | [offline-checkin-checkout-sync-conflicts.md](./offline-checkin-checkout-sync-conflicts.md) |
| EC-OFF-005 | Idempotency | Duplicate sync submission of same offline event | P1 | Open | [offline-checkin-checkout-sync-conflicts.md](./offline-checkin-checkout-sync-conflicts.md) |
| EC-OFF-006 | Conflict | Conflicting field values — client vs. server resolution rules | P1 | Open | [offline-checkin-checkout-sync-conflicts.md](./offline-checkin-checkout-sync-conflicts.md) |

### Payment Reconciliation

| ID | Category | Description | Criticality | Status | Linked File |
|----|----------|-------------|-------------|--------|-------------|
| EC-PAY-001 | Channel | Payment received via card but booking recorded as cash | P0 | Open | [payment-reconciliation-across-channels.md](./payment-reconciliation-across-channels.md) |
| EC-PAY-002 | Webhook | Stripe webhook arrives out of order | P1 | Open | [payment-reconciliation-across-channels.md](./payment-reconciliation-across-channels.md) |
| EC-PAY-003 | Idempotency | Duplicate payment submitted (double-charge risk) | P0 | Open | [payment-reconciliation-across-channels.md](./payment-reconciliation-across-channels.md) |
| EC-PAY-004 | Partial | Customer pays deposit only — balance unpaid | P1 | Open | [payment-reconciliation-across-channels.md](./payment-reconciliation-across-channels.md) |
| EC-PAY-005 | Refund | Refund to different payment method than original charge | P1 | Open | [payment-reconciliation-across-channels.md](./payment-reconciliation-across-channels.md) |
| EC-PAY-006 | Dispute | Card issuer initiates chargeback | P0 | Open | [payment-reconciliation-across-channels.md](./payment-reconciliation-across-channels.md) |
| EC-PAY-007 | FX | Multi-currency booking — FX rate changes between booking and settlement | P1 | Open | [payment-reconciliation-across-channels.md](./payment-reconciliation-across-channels.md) |
| EC-PAY-008 | Auth | Failed deposit pre-auth → booking cancellation | P0 | Open | [payment-reconciliation-across-channels.md](./payment-reconciliation-across-channels.md) |

### API & UI

| ID | Category | Description | Criticality | Status | Linked File |
|----|----------|-------------|-------------|--------|-------------|
| EC-API-001 | Rate Limit | Customer exceeds 100 req/min | P1 | Open | [api-and-ui.md](./api-and-ui.md) |
| EC-API-002 | Timeout | Upstream service unresponsive during booking | P0 | Open | [api-and-ui.md](./api-and-ui.md) |
| EC-API-003 | Webhook | Webhook delivery fails; retry exhausted | P1 | Open | [api-and-ui.md](./api-and-ui.md) |
| EC-API-004 | Idempotency | POST with duplicate X-Idempotency-Key | P0 | Open | [api-and-ui.md](./api-and-ui.md) |
| EC-API-005 | Pagination | Cursor becomes invalid due to deleted record | P2 | Open | [api-and-ui.md](./api-and-ui.md) |
| EC-API-006 | Upload | Image file exceeds 10 MB limit | P2 | Open | [api-and-ui.md](./api-and-ui.md) |
| EC-API-007 | UI | Double-click on booking submit button | P1 | Open | [api-and-ui.md](./api-and-ui.md) |
| EC-API-008 | Session | Session expires during multi-step booking flow | P1 | Open | [api-and-ui.md](./api-and-ui.md) |

### Security & Compliance

| ID | Category | Description | Criticality | Status | Linked File |
|----|----------|-------------|-------------|--------|-------------|
| EC-SEC-001 | PCI-DSS | Raw card number logged in application logs | P0 | Open | [security-and-compliance.md](./security-and-compliance.md) |
| EC-SEC-002 | GDPR | Right to erasure request for active rental customer | P0 | Open | [security-and-compliance.md](./security-and-compliance.md) |
| EC-SEC-003 | PII | ID document not deleted after 90-day retention window | P0 | Open | [security-and-compliance.md](./security-and-compliance.md) |
| EC-SEC-004 | Fraud | High-velocity booking attempts from same customer | P1 | Open | [security-and-compliance.md](./security-and-compliance.md) |
| EC-SEC-005 | Auth | Refresh token reuse after rotation | P0 | Open | [security-and-compliance.md](./security-and-compliance.md) |
| EC-SEC-006 | AuthZ | Customer accesses another customer's booking via IDOR | P0 | Open | [security-and-compliance.md](./security-and-compliance.md) |
| EC-SEC-007 | Audit | State change event missing from audit log | P1 | Open | [security-and-compliance.md](./security-and-compliance.md) |

### Operations

| ID | Category | Description | Criticality | Status | Linked File |
|----|----------|-------------|-------------|--------|-------------|
| EC-OPS-001 | SLO | Booking API p95 latency exceeds 200ms threshold | P1 | Open | [operations.md](./operations.md) |
| EC-OPS-002 | Incident | Payment service completely unavailable | P0 | Open | [operations.md](./operations.md) |
| EC-OPS-003 | Database | RDS failover during peak booking window | P0 | Open | [operations.md](./operations.md) |
| EC-OPS-004 | Queue | Kafka consumer lag spike — notifications delayed | P1 | Open | [operations.md](./operations.md) |
| EC-OPS-005 | Capacity | ECS task CPU reaches 70% sustained — scale-out not triggered | P1 | Open | [operations.md](./operations.md) |

---

## Risk Area Summary

### Financial Risk (P0 Priority)
- Gap collection when damage exceeds deposit
- Double-charge via duplicate payment submission
- Extension payment failure leaving rental in limbo state
- Damage discovered after deposit release (no recourse path)

**Mitigation:** Idempotency keys on all payment mutations; two-phase deposit hold; 72-hour damage window enforced in code; gap collection flow via secondary charge.

### Data Integrity Risk (P0 Priority)
- Race condition on concurrent bookings for same asset
- Offline sync creating conflicting state records
- Webhook out-of-order processing corrupting payment state

**Mitigation:** Database-level advisory locks + optimistic locking with version columns; idempotency tables for all webhook handlers; event sourcing for payment state machine.

### Security & Compliance Risk (P0 Priority)
- PII/card data leakage in logs or unencrypted fields
- IDOR attacks exposing other customers' rental records
- ID document retention violation under GDPR

**Mitigation:** Structured logging with PII scrubbing middleware; resource-level ownership checks in every controller; automated S3 lifecycle rules for ID documents.

### Availability Risk (P0/P1 Priority)
- Payment gateway downtime blocking all new bookings
- Database failover causing partial write loss
- Offline staff app unable to check out assets

**Mitigation:** Circuit breaker on payment service; RDS Multi-AZ with automatic failover; offline-first mobile app with local SQLite queue.

---

## Document Index

| File | Domain | Line Count |
|------|--------|------------|
| [inventory-availability-conflicts.md](./inventory-availability-conflicts.md) | Inventory | 300+ |
| [booking-extensions-and-partial-returns.md](./booking-extensions-and-partial-returns.md) | Bookings | 300+ |
| [damage-claims-and-deposit-adjustments.md](./damage-claims-and-deposit-adjustments.md) | Damage | 300+ |
| [offline-checkin-checkout-sync-conflicts.md](./offline-checkin-checkout-sync-conflicts.md) | Offline Sync | 300+ |
| [payment-reconciliation-across-channels.md](./payment-reconciliation-across-channels.md) | Payments | 300+ |
| [api-and-ui.md](./api-and-ui.md) | API / UI | 300+ |
| [security-and-compliance.md](./security-and-compliance.md) | Security | 300+ |
| [operations.md](./operations.md) | Operations | 300+ |

---

*Last updated: 2025. Owner: Platform Engineering. Review cadence: quarterly or after any P0 incident.*
