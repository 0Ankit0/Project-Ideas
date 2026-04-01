# Edge Cases — Master Index and Governance

This directory is the authoritative reference for every non-happy-path scenario in the Healthcare Appointment System. Each document defines the exact failure mode, quantified business impact, detection signals, step-by-step recovery procedure, and the preventive engineering change required to eliminate or reduce recurrence.

**Owner:** Platform Engineering + Clinical Operations  
**Review cadence:** Monthly during incident review; mandatory update after any Sev-1/Sev-2 incident  
**Last reviewed:** See git log

---

## 1. Coverage Map

The matrix below rates every edge-case category by **Business Impact** (patient harm risk + revenue loss + regulatory exposure) and **Likelihood** (observed frequency in production or analogous healthcare SaaS systems). Cells contain the primary edge-case file and a short label.

| Category | Business Impact | Likelihood | Primary File | Critical EC Count |
|---|---|---|---|---|
| Slot Availability | 🔴 High — missed care, provider under-utilization | 🔴 High — concurrent traffic at peak hours | `slot-availability.md` | 10 |
| Booking & Payments | 🔴 High — revenue leakage, duplicate charges, PCI exposure | 🟠 Medium-High — gateway instability, retry storms | `booking-and-payments.md` | 10 |
| Cancellations & Refunds | 🟠 Medium-High — refund disputes, SLA breach, HIPAA audit | 🟠 Medium — seasonal no-show spikes | `cancellations-and-refunds.md` | 8 |
| Notifications | 🟠 Medium — missed reminders cause no-shows; consent violations | 🔴 High — external SMTP/SMS dependencies | `notifications.md` | 7 |
| Operations | 🔴 High — downtime during clinic hours, data inconsistency | 🟡 Low-Medium — planned maintenance windows | `operations.md` | 6 |
| Security & Compliance | 🔴 Critical — PHI breach, HIPAA penalty, license revocation | 🟡 Low — high consequence; must be near-zero | `security-and-compliance.md` | 8 |
| API & UI | 🟠 Medium — UX degradation, booking abandonment, duplicate submits | 🔴 High — mobile network issues, browser quirks | `api-and-ui.md` | 7 |

**Impact Scale:** 🔴 High / 🟠 Medium / 🟡 Low  
**Likelihood Scale:** 🔴 High (>1% of sessions) / 🟠 Medium (0.1–1%) / 🟡 Low (<0.1%)

---

## 2. Top Critical Edge Cases by File

### 2.1 `slot-availability.md`

| Rank | Edge Case ID | Name | Why Critical |
|---|---|---|---|
| 1 | EC-SLOT-001 | Concurrent booking race condition | Two patients book same slot; only one can be seen; the other travels needlessly |
| 2 | EC-SLOT-009 | Slot hold expiry during payment processing | Slow 3DS authentication releases slot between auth and capture, creating ghost booking |
| 3 | EC-SLOT-010 | DST fallback creates ambiguous duplicate hour | Automated slot generation creates overlapping or unreachable appointments at clock rollback |

### 2.2 `booking-and-payments.md`

| Rank | Edge Case ID | Name | Why Critical |
|---|---|---|---|
| 1 | EC-PAY-004 | Partial saga failure — slot reserved, appointment not created | Slot is blocked but patient has no record; provider has gap; revenue lost |
| 2 | EC-PAY-002 | Gateway timeout with unknown transaction outcome | System cannot determine if money moved; duplicate charge or missed payment both possible |
| 3 | EC-PAY-005 | Orphaned payment authorization | Pre-auth holds funds on patient card for days after appointment is cancelled |

### 2.3 `cancellations-and-refunds.md`

| Rank | Edge Case ID | Name | Why Critical |
|---|---|---|---|
| 1 | EC-CANCEL-003 | Refund issued after partial insurance settlement | Overpayment refunded to patient while insurer balance is outstanding |
| 2 | EC-CANCEL-001 | Cancellation within no-show fee window, fee disputed | Fee applied before policy acknowledgement is confirmed in audit trail |
| 3 | EC-CANCEL-007 | Provider-initiated cancellation not triggering patient refund | System skips compensation path when cancellation actor is provider, not patient |

### 2.4 `notifications.md`

| Rank | Edge Case ID | Name | Why Critical |
|---|---|---|---|
| 1 | EC-NOTIF-002 | Appointment reminder sent after cancellation | Patient travels to appointment that was cancelled; trust and safety issue |
| 2 | EC-NOTIF-005 | Consent withdrawal mid-delivery-retry | Notification retried after patient opted out; HIPAA violation risk |
| 3 | EC-NOTIF-006 | Template version mismatch renders wrong appointment data | Patient shown incorrect time/location; causes no-show |

### 2.5 `operations.md`

| Rank | Edge Case ID | Name | Why Critical |
|---|---|---|---|
| 1 | EC-OPS-001 | Write-queue replay creates duplicate appointments on recovery | Post-outage replay re-processes commands already committed before failure |
| 2 | EC-OPS-003 | Database failover during active booking transaction | In-flight saga loses coordinator; leaves locks and auth holds open indefinitely |
| 3 | EC-OPS-005 | Backfill job mutates live appointment records | Data migration script runs against production, corrupting active bookings |

### 2.6 `security-and-compliance.md`

| Rank | Edge Case ID | Name | Why Critical |
|---|---|---|---|
| 1 | EC-SEC-001 | PHI exposed in error response body | Stack trace includes patient name, DOB, or diagnosis code in 500 response logged by client |
| 2 | EC-SEC-004 | JWT expiry not enforced on long-running booking flow | Token issued at flow start expires mid-saga; subsequent steps execute with stale identity |
| 3 | EC-SEC-007 | HIPAA audit log write failure silently discarded | Compliance-required access log drops event under I/O pressure without alerting |

### 2.7 `api-and-ui.md`

| Rank | Edge Case ID | Name | Why Critical |
|---|---|---|---|
| 1 | EC-API-003 | Double-submit on slow network creates two bookings | Patient taps "Book" twice; two appointments created, two charges attempted |
| 2 | EC-API-001 | Missing idempotency key on POST /bookings | Retry on timeout re-creates booking; no deduplication without client-supplied key |
| 3 | EC-API-006 | Pagination cursor pointing to deleted slot record | Infinite loop in availability pagination when cursor anchor is soft-deleted |

---

## 3. Cross-Cutting Edge-Case Principles

These principles apply to **every** edge case across all categories. Every new edge case document must explicitly state which principles govern its mitigation strategy.

### P-01 — Idempotency by Default
Every mutating operation (booking, payment, cancellation, refund, notification dispatch) must accept and enforce a client-supplied idempotency key. The system must return the identical response for repeated requests with the same key within a 24-hour window. Idempotency records are stored in a dedicated `idempotency_log` table, not in the primary entity table, to avoid coupling.

### P-02 — Deterministic Error Codes
All error responses return a stable, documented error code (e.g., `SLOT_ALREADY_BOOKED`, `PAYMENT_AUTH_FAILED`, `CONSENT_WITHDRAWN`) alongside the HTTP status. Error codes are enumerated in the API contract and never changed without a deprecation period. Client applications and operator tooling key on error codes, not on message text or HTTP status alone.

### P-03 — Immutable Audit Trail
Every state transition on every aggregate (appointment, slot, payment, notification, user identity) is appended to an immutable audit log table. Records include: `actor_id`, `actor_role`, `action`, `from_state`, `to_state`, `reason_code`, `correlation_id`, `source_ip`, and `wall_clock_utc`. Audit records are never updated or deleted. HIPAA Business Associate Agreement (BAA) requires 6-year retention.

### P-04 — Human Override with Accountability
Operators may override system-enforced constraints (e.g., force-confirm a conflicted appointment, waive a cancellation fee) only through an explicit override API that requires: MFA re-authentication, a mandatory reason code, and a supervisor approval token for Sev-1 actions. All overrides are surfaced in the compliance dashboard within 5 minutes.

### P-05 — PHI Protection at Every Boundary
Protected Health Information must never appear in: log messages, error responses, analytics event payloads, notification metadata, or queue message bodies beyond the minimum necessary. PHI fields are identified in the data dictionary with a `phi: true` annotation. Automated linting rejects log statements that reference annotated PHI fields directly.

### P-06 — Graceful Degradation with Explicit Modes
The system operates in three declared modes: `FULL`, `DEGRADED`, and `READ_ONLY`. Each mode is documented in a runbook with the exact set of write operations that are disabled and the user-facing message template. Downstream services receive a `X-System-Mode` header on every response so clients can adapt their UX. Mode transitions are gated behind feature flags and require a manual acknowledge step.

### P-07 — Retry Safety and Backoff Contracts
All internal service calls and outbound webhook deliveries must implement exponential backoff with jitter (base 200 ms, cap 30 s, max 8 retries). Retried requests must include the original idempotency key and a `X-Retry-Count` header. Services must never retry on 4xx client errors (except 408, 429). Circuit breakers open after 5 consecutive 5xx responses within 10 seconds and half-open after 30 seconds.

### P-08 — Compensation Transactions for Distributed Sagas
Every multi-step saga (book, reschedule, cancel, refund) must define a compensation sequence for every possible partial-failure point. Compensation steps are idempotent, logged, and verifiable. The saga orchestrator persists its step journal in the database; on restart it resumes from the last confirmed step. Compensation is never a fire-and-forget async task—it blocks the saga from entering a terminal state until all compensations are confirmed or escalated to a human queue.

### P-09 — Observability-First Design
Every edge case handling path must emit: a structured log event at `WARN` or `ERROR` level with `correlation_id`, `edge_case_id`, and `resolution_action` fields; a counter metric increment on `edge_case.triggered{id=EC-XXX-NNN}`; and a span annotation if the request is traced. Alert thresholds for each edge case are defined in `monitoring/alerts.yaml` and reviewed quarterly.

### P-10 — Policy Versioning
All business-rule parameters that govern edge cases (cancellation fee windows, slot hold durations, retry limits, refund eligibility periods) are stored as versioned policy records in the `policy_versions` table, not as code constants. Each appointment records the `policy_version_id` active at booking time. Policy changes are applied prospectively only, never retroactively, unless a migration with an explicit approval trail is executed.

### P-11 — Timezone Canonicalization
All datetime values stored in the database and exchanged in APIs are UTC. Conversion to local time occurs exclusively at the API response serialization layer and the notification rendering layer. Slot records store both `slot_start_utc` and `timezone_id` (IANA zone name). DST transitions are detected at slot generation time and flagged with `dst_ambiguous: true` for human review.

### P-12 — Eventual Consistency Contracts
Read projections (availability cache, reporting dashboards) are eventually consistent and declare their staleness SLA (e.g., "availability cache is consistent within 5 seconds of a slot mutation"). APIs that read from projections must return a `X-Data-Freshness-Utc` header. Clients that require strong consistency (e.g., the final booking confirmation step) must call the command-side read endpoint, which reads from the primary write replica.

---

## 4. Edge Case Testing Strategy

### 4.1 Chaos Engineering
Chaos tests are defined in `tests/chaos/` and run in the staging environment on a weekly schedule using the Chaos Toolkit framework.

| Experiment | Target | Expected Behavior |
|---|---|---|
| Kill slot-service mid-reservation | Slot service pod | Saga compensates, slot released within 60 s |
| Inject 5s latency on payment gateway | Payment adapter | 3DS timeout triggers slot hold extension or release |
| Drop 30% of notification queue messages | SNS/SQS topic | Retry worker recovers delivery within 10 min |
| Corrupt cache entry for provider schedule | Redis availability cache | Read-through to DB, stale entry evicted, no wrong data served |
| Fail DB write for audit log | Audit log DB | Transaction rolls back; primary operation fails with 500; PHI not leaked |

### 4.2 Load and Concurrency Testing
- **Concurrent slot booking:** 1,000 simultaneous `POST /bookings` for the same slot. Expected: exactly one success (`201`), remainder receive `409 SLOT_ALREADY_BOOKED` with alternatives.
- **Availability cache stampede:** 500 concurrent requests during cache expiry window. Expected: single cache-fill request reaches DB (via distributed lock), all others wait and receive warm cache response.
- **Payment saga under load:** 200 concurrent booking sagas with simulated gateway 503 on step 2. Expected: all sagas compensate correctly; zero orphaned slot holds after 5 minutes.

### 4.3 Contract Testing
- Provider-consumer contract tests (Pact) are maintained for every integration: `booking-service → payment-adapter`, `slot-service → notification-service`, `cancellation-service → refund-service`.
- Contracts are verified in CI on every pull request to either consumer or provider.
- Breaking changes to error codes or response schemas require a contract version bump and a coordinated deployment plan.

### 4.4 Regression Suite for Edge Cases
Each documented edge case has a corresponding integration test tagged `@edge-case` and `@EC-XXX-NNN`. The test must reproduce the failure mode, assert the detection signal fires, and verify the mitigation path resolves cleanly. Tests are run in a full-stack environment (Docker Compose) on every merge to `main`.

---

## 5. Monitoring and Alert Coverage

All alerts are defined in `monitoring/alerts.yaml` and deployed via Terraform to the observability platform. The table below maps edge case categories to their primary alert rules.

| Alert Name | Metric / Log Query | Threshold | Severity | Runbook |
|---|---|---|---|---|
| `slot.conflict.rate.high` | `rate(edge_case.triggered{id="EC-SLOT-001"}[5m])` | > 2% of booking attempts | P2 | `runbooks/slot-conflict.md` |
| `slot.cache.staleness` | `max(slot_cache_age_seconds)` | > 60 s | P2 | `runbooks/cache-stale.md` |
| `slot.hold.expired.mid.payment` | `count(edge_case.triggered{id="EC-SLOT-009"})` | > 10 / 10 min | P2 | `runbooks/slot-hold-expiry.md` |
| `payment.saga.orphan` | `count(saga_state="COMPENSATING" AND age > 15m)` | > 0 | P1 | `runbooks/orphan-saga.md` |
| `payment.gateway.timeout.rate` | `rate(edge_case.triggered{id="EC-PAY-002"}[5m])` | > 1% | P2 | `runbooks/gateway-timeout.md` |
| `duplicate.booking.detected` | `count(edge_case.triggered{id="EC-PAY-003"})` | > 0 | P1 | `runbooks/duplicate-booking.md` |
| `notification.post.cancel.sent` | `count(edge_case.triggered{id="EC-NOTIF-002"})` | > 0 | P1 | `runbooks/notif-post-cancel.md` |
| `audit.log.write.failure` | `count(edge_case.triggered{id="EC-SEC-007"})` | > 0 | P1 | `runbooks/audit-log-failure.md` |
| `phi.in.error.response` | Log pattern: `error_body contains phi_field` | Any match | P1 | `runbooks/phi-leak.md` |
| `dst.ambiguous.slot.unreviewed` | `count(slots WHERE dst_ambiguous=true AND reviewed=false)` | > 0 at 23:00 local | P2 | `runbooks/dst-slots.md` |
| `saga.compensation.stuck` | `count(saga_compensation_steps WHERE age > 30m)` | > 0 | P1 | `runbooks/saga-stuck.md` |
| `api.double.submit` | `count(edge_case.triggered{id="EC-API-003"})` | > 5 / 10 min | P3 | `runbooks/double-submit.md` |

**PagerDuty escalation policy:** P1 pages on-call immediately; P2 pages on-call within 5 minutes if unacknowledged; P3 creates a ticket in the ops backlog.

---

## 6. Document Conventions

Every edge case document in this directory follows a consistent structure:

```
### EC-[DOMAIN]-[NNN]: [Descriptive Name]
- **Failure Mode:** What exactly goes wrong (system state, data corruption, user impact)
- **Impact:** Business and user impact, quantified where possible (revenue, SLA, regulatory)
- **Detection:** Monitoring query, alert name, log pattern, threshold
- **Mitigation/Recovery:** Numbered step-by-step procedure for the on-call engineer
- **Prevention:** The specific code, infrastructure, or process change to eliminate or reduce recurrence
```

Edge case IDs are permanent. If an edge case is retired, its ID is marked `[RETIRED]` and the entry is kept for audit history. IDs are never reused.

---

## 7. Contributing

To add a new edge case:
1. Open a pull request targeting this directory.
2. Assign the next sequential ID in the relevant domain.
3. Complete all five sections of the standard template.
4. Add a corresponding `@edge-case` integration test.
5. Add or update the alert rule in `monitoring/alerts.yaml`.
6. Link the new edge case in the coverage map table in this file.
7. Tag the PR with `edge-case` and request review from `@platform-engineering` and `@clinical-ops`.
