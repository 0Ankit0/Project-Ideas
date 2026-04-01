# Edge Case Documentation — Event Management and Ticketing Platform

## Purpose

This directory contains structured edge case analyses for every high-risk scenario
identified in the Event Management and Ticketing Platform. Each document covers a
specific domain (event creation, ticket sales, payments, check-in, etc.) and follows a
consistent format: failure mode, business impact, detection signal, mitigation strategy,
recovery playbook, and long-term prevention.

These documents serve three audiences:

1. **Engineering** — implementation requirements and rollback procedures
2. **QA / Test Engineering** — test case derivation and fault injection scripts
3. **On-call SREs** — runbooks referenced during incident response

Edge case documents are living artifacts. They must be updated whenever a production
incident reveals a new failure mode, or when architecture changes invalidate a previous
mitigation.

---

## Risk Classification

| Priority | Label | Definition |
|----------|-------|------------|
| **P0** | Catastrophic | Direct revenue loss, data loss, or regulatory breach. Requires immediate hotfix. Incident bridge opened within 15 minutes. |
| **P1** | High | Major UX degradation affecting ≥ 5 % of users or a full feature area. Fix within one business day. |
| **P2** | Medium | Partial functionality loss; workaround exists. Fix within current sprint. |
| **P3** | Low | Minor inconvenience; cosmetic or edge-path only. Scheduled for backlog grooming. |

---

## Risk Matrix

| Scenario | Probability | Impact | Priority | Mitigation Status |
|----------|-------------|--------|----------|-------------------|
| Concurrent last-ticket race condition | High | Revenue / data integrity | P0 | ✅ Redis distributed lock + DB serializable isolation |
| Venue double-booking by two organizers | Medium | Revenue / legal liability | P0 | ✅ Venue reservation table with unique constraint |
| QR scanner offline at event gate | High | Operational disruption | P1 | ✅ Offline JWT validation bundle on scanner device |
| Refund requested after organizer payout already processed | Medium | Financial loss / fraud | P0 | ⚠️ Escrow hold period under review |
| Payment webhook delivered twice (duplicate charge) | Medium | Financial / trust | P0 | ✅ Idempotency key on all payment processor callbacks |
| Redis eviction of active seat hold under memory pressure | Medium | Inventory corruption | P1 | ✅ `allkeys-lru` policy + TTL ≥ session timeout; hold persisted to DB |
| Event cancellation with 10,000 existing ticketholders | Low | Mass refund SLA / comms | P1 | ⚠️ Bulk-refund job tested only to 1,000; scaling test pending |
| GDPR deletion request for past attendee with audit records | Low | Regulatory / legal | P1 | ✅ Pseudonymisation pipeline implemented; legal hold flag available |
| Flash sale — 50,000 concurrent purchase attempts | Low | Revenue / availability | P0 | ⚠️ Queue-based admission under load test; not yet in prod |
| Payout initiated to OFAC-listed entity | Very Low | Regulatory / criminal liability | P0 | ✅ OFAC screening on every payout via Stripe Radar + internal list |

---

## How to Use These Documents

Each edge case file is named after the domain it covers:

```
edge-cases/
├── README.md                            ← this file
├── event-creation-and-publishing.md
├── ticket-sales-and-allocation.md
├── payment-processing.md
├── check-in-and-access-control.md
├── refunds-and-cancellations.md
└── organizer-payouts.md
```

**When implementing a feature:** Read the relevant edge case file before writing code.
Each mitigation section describes the required implementation contract.

**When writing tests:** Each edge case identifier (e.g., `EC-03`) maps directly to a
test suite tag. Run `pytest -m EC-03` or `jest --testNamePattern="EC-03"` to execute
tests for a specific edge case.

**During incident response:** Search this directory for keywords related to the failure.
The Recovery section of each edge case describes the immediate remediation steps.

---

## Testing Approach

### Chaos Engineering — LitmusChaos

Chaos experiments are defined in `infra/chaos/` and target the following fault classes:

| Fault Class | LitmusChaos Experiment | Cadence |
|-------------|------------------------|---------|
| Redis pod kill | `pod-delete` on `redis-seat-cache` | Weekly in staging |
| PostgreSQL network partition | `network-loss` on DB subnet | Bi-weekly |
| Payment provider webhook delay | `http-latency` on webhook ingress | Weekly |
| Scanner service crash loop | `pod-cpu-hog` on `checkin-service` | Monthly |
| Mass concurrent load | k6 flash-sale script (50k VUs) | Pre-release |

### Fault Injection in Staging

The `scripts/fault-inject/` directory contains targeted fault scripts for individual
edge cases. Each script sets up preconditions, triggers the fault, and asserts the
expected system behaviour:

```bash
# Example: trigger the Redis eviction edge case
./scripts/fault-inject/redis-eviction-seat-hold.sh --seats 500 --eviction-pressure 95
```

All fault injection scripts must pass before a release is promoted from staging to
production.

---

## Monitoring and SLO Tracking

Datadog monitors for each risk are tagged with the edge case ID (e.g., `ec:EC-01`).
SLO dashboards are maintained in the `Event Platform — Edge Case SLOs` Datadog
dashboard.

| Edge Case | Datadog Monitor | SLO Target |
|-----------|-----------------|------------|
| Concurrent ticket race | `ticket.purchase.duplicate_order.count` | 0 duplicates per day |
| Redis seat hold eviction | `seat.hold.eviction.rate` | < 0.01 % of holds |
| Webhook duplicate processing | `payment.webhook.idempotency.collision.count` | 0 per day |
| Flash sale queue depth | `admission.queue.depth` | p99 wait < 5 s |
| OFAC payout screen | `payout.ofac.blocked.count` | Alert on any value > 0 |

Alerts page the on-call SRE for any P0 edge case monitor breach.

---

## Ownership

| Edge Case Category | Owning Team | Slack Channel | Oncall Rotation |
|--------------------|-------------|---------------|-----------------|
| Event creation / publishing | Platform Engineering | `#platform-eng` | `platform-oncall` |
| Ticket sales / inventory | Commerce Engineering | `#commerce-eng` | `commerce-oncall` |
| Payment processing | Payments Team | `#payments` | `payments-oncall` |
| Check-in / access control | Operations Engineering | `#ops-eng` | `ops-oncall` |
| Refunds / cancellations | Commerce + Payments | `#refunds` | `commerce-oncall` |
| Organizer payouts | Payments + Finance | `#payouts` | `payments-oncall` |
| GDPR / data compliance | Data Platform + Legal | `#data-compliance` | `data-oncall` |

---

## Change Log

| Date | Author | Change |
|------|--------|--------|
| 2024-01-15 | Platform Eng | Initial document — all P0/P1 scenarios from threat model |
| 2024-03-02 | Commerce Eng | Added EC-05 (capacity reduction) and EC-06 (organizer suspension) |
| 2024-05-10 | Payments Team | Updated OFAC mitigation status to ✅ after Stripe Radar integration |
