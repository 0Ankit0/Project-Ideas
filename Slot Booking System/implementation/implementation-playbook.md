# Implementation Playbook

## 1. Delivery Goal
Ship a production-ready system for **real-time slot discovery, booking, payment, cancellation, and notifications**.

### Target KPIs
- Booking success > 99%, Slot lock race failures < 0.1%, API p95 < 200ms
- Availability target: 99.9%
- Mean time to recovery (MTTR): < 30 minutes

## 2. Implementation Scope (Must-Have)
Core services to implement:
- Availability, Booking, Payment, Notification, Provider Management
- Admin and operator console
- Monitoring, alerting, and audit logging
- Security controls (authentication, authorization, encryption)

## 3. Environment Setup
### Local
1. Install runtime dependencies as listed in `implementation/code-guidelines.md` (or `implementation/implementation-guidelines.md`).
2. Start required infrastructure (DB, cache, queue, search, object store) using Docker Compose.
3. Configure `.env` with local credentials and feature flags.
4. Seed baseline data for development and demo scenarios.

### Non-Production / Production
1. Provision cloud resources from `infrastructure/cloud-architecture.md`.
2. Configure network, subnets, WAF, and private endpoints from `infrastructure/network-infrastructure.md`.
3. Deploy workloads according to `infrastructure/deployment-diagram.md`.
4. Enable centralized logs, metrics, and traces.

## 4. Build Plan by Workstream
### A) Backend APIs
- Implement all endpoints from `detailed-design/api-design.md`.
- Add request/response validation, idempotency, pagination, filtering, and error contracts.
- Add retries, circuit breakers, and timeouts for downstream dependencies.

### B) Data Layer
- Implement schema from `detailed-design/erd-database-schema.md`.
- Add migrations and rollback scripts.
- Add indexes for read-heavy and write-heavy paths.
- Define retention and archival policies.

### C) Domain Logic
- Implement lifecycle and transitions from `detailed-design/state-machine-diagram.md`.
- Implement orchestration from `detailed-design/sequence-diagram.md` (or equivalent diagrams).
- Enforce all rules from `analysis/business-rules.md`.

### D) Frontend / Consumer Integration
- Implement consumer journeys from `analysis/use-case-descriptions.md` and `analysis/activity-diagram.md` (or equivalent).
- Add optimistic UI states, loading states, and error states.
- Add accessibility and localization support where applicable.

### E) Security & Compliance
- Enforce least-privilege IAM and role-based access control.
- Encrypt data in transit (TLS 1.2+) and at rest.
- Add audit trails for privileged and business-critical operations.
- Implement controls from `edge-cases/security-and-compliance.md`.

### F) Reliability & Operations
- Implement operational safeguards from `edge-cases/operations.md`.
- Add SLO dashboards and alerting thresholds.
- Add runbooks for incident triage and service restoration.

## 5. Testing Strategy (Release Blocking)
- Unit tests for domain logic and adapters.
- Integration tests for DB/cache/queue/external provider integrations.
- API contract tests for all public endpoints.
- End-to-end tests for top business flows and edge-cases.
- Load and stress tests aligned with documented performance targets.
- Security tests: authz/authn checks, OWASP top risks, secrets scanning.

## 6. Data & Migration Readiness
- Initial seed strategy and synthetic data generation.
- Backfill and replay strategy for historical data.
- Zero-downtime migration approach (expand-and-contract).
- Verified restore drills for backups.

## 7. CI/CD & Release Management
- CI gates: lint, type checks, unit tests, integration tests, SAST.
- Build immutable artifacts and sign releases.
- Progressive rollout: canary/blue-green with automatic rollback.
- Post-deploy smoke tests and synthetic monitoring.

## 8. Go-Live Readiness Checklist
- [ ] All required APIs implemented and contract-validated.
- [ ] Database migrations verified in staging.
- [ ] Critical edge-cases validated from `edge-cases/` docs.
- [ ] On-call rotation, escalation matrix, and runbooks active.
- [ ] Backups and restore tested successfully.
- [ ] Security review and threat model sign-off completed.
- [ ] Performance/load targets achieved in pre-production.
- [ ] Observability dashboards and alerts operational.

## 9. Handover Artifacts
- Architecture decision records (ADRs)
- API collections and schema definitions
- Operational runbooks and incident playbooks
- Environment variable catalog and secrets ownership
- Release checklist and rollback SOP

## 10. Definition of Done
System is considered implementation-ready and production-capable when:
1. Functional and non-functional requirements are traceable to tests.
2. All critical paths and edge-cases have automated test coverage.
3. Deployment and rollback are fully automated and repeatable.
4. Security, reliability, and operational controls are verified in staging.
5. Stakeholders sign off on KPI and acceptance criteria.

---
## Implementation-Ready Implementation Playbook

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

### Build-ready engineering guidance
- Reference command handler boundaries and invariants for each state transition.
- Add deterministic integration tests for race, timeout, and compensation paths.
- Enforce trace propagation and correlation IDs in all external calls.

## 11. Distributed Booking Control Model

### 11.1 Slot-hold expiration mechanics
- Every reserve attempt creates a `slot_hold` record with fields: `hold_id`, `booking_id`, `slot_id`, `expires_at_utc`, `fencing_token`, `state`.
- Hold TTL baseline: **5 minutes**, configurable per resource policy.
- Expiration is enforced by **dual-path cleanup**:
  1. Passive expiry check on every read/write path (`now_utc > expires_at_utc`).
  2. Active sweeper job running every 5-15 seconds that emits `SlotExpired` and releases counters.
- Expiry transition must be idempotent: `HELD -> EXPIRED` succeeds once; retries are no-op.
- Client response for reserve includes `hold_expires_at_utc` and `server_now_utc` for countdown rendering.

### 11.2 Deduplication and idempotency handling
- Public write APIs (`reserve`, `confirm`, `cancel`, `refund`) require `Idempotency-Key`.
- Request fingerprint (`actor_id + route + normalized_payload_hash`) must match prior key usage.
- Idempotency store SLA:
  - TTL >= 24h for booking writes.
  - Persist terminal response envelope (status + body + correlation ID).
- Async consumer dedup uses `processed_messages` table keyed by (`consumer_name`, `message_id`).
- Payment webhooks dedup by provider event ID + signature verification + monotonic received timestamp.

### 11.3 Payment coupling/decoupling model
- **Coupled mode (strict)**
  - Confirm booking only inside confirm transaction after payment authorization/capture success.
  - On payment timeout/failure, hold is released and booking marked `PAYMENT_FAILED`.
- **Decoupled mode (grace window)**
  - Booking moves to `CONFIRMED_PAYMENT_PENDING` if policy allows deferred settlement.
  - Grace window (e.g., 15 minutes) tracked by scheduler; expiry auto-cancels booking if unpaid.
- Required compensation cases:
  - `payment_success + booking_not_confirmed` => refund saga.
  - `booking_confirmed + payment_reversed` => downgrade to `PAYMENT_REVERSED` and trigger manual or automatic cancellation policy.

### 11.4 Race-condition mitigation
- Use atomic slot-hold acquisition (`SET NX PX`/CAS/Lua) with fencing token validation.
- Validate version fields on booking and slot rows to reject stale updates.
- Serialize high-contention operations by shard key (`resource_id + time_bucket`) in worker queue.
- Enforce bounded retries with jittered backoff; return deterministic conflict codes when retries exhausted.
- Add Jepsen-style fault tests for concurrent reserve/confirm/cancel with injected delay and reorder.

## 12. Non-functional Acceptance Criteria (Release Gates)

### Throughput
- Reserve attempts: **>= 2,000 req/s** sustained for 15 minutes in primary region.
- Confirm/capture completions: **>= 500 req/s** sustained with webhook load.
- Cancel+refund requests: **>= 300 req/s** sustained including async refund processing.

### Latency (p95)
- `GET /availability`: **<= 120ms**.
- `POST /bookings/reserve`: **<= 180ms**.
- `POST /bookings/{id}/confirm`: **<= 250ms** excluding external PSP latency; include internal state commit.
- `POST /bookings/{id}/cancel`: **<= 180ms** for booking cancellation acknowledgement.

### Consistency window
- Availability projection lag to source-of-truth ledger: **<= 2s normal**, **<= 10s degraded**.
- Hold expiry enforcement lag: **<= 3s p95** from TTL expiration to slot re-open.
- Payment-to-booking state convergence: **<= 30s p95** after webhook receipt.
