# Backend Status Matrix

Feature-level readiness matrix for the **Resource Lifecycle Management Platform** backend. Used to track development, testing, and production promotion status for every capability.

---

## Status Legend

| Status | Meaning |
|---|---|
| 🔴 Not Started | No implementation begun |
| 🟡 In Progress | Active development; not yet passing all tests |
| 🟢 Feature Complete | All unit/integration tests pass; PR merged to main |
| 🔵 Staging Ready | Load tested; security scanned; rollback tested on staging |
| ✅ Production Ready | Runbook signed off; on-call handover complete; compliance attested |

---

## Phase 1 – Provisioning and Catalog

| Feature | API Endpoint | Unit Tests | Integration Tests | Staging | Production |
|---|---|---|---|---|---|
| Single resource provision | `POST /resources` | 🔴 | 🔴 | 🔴 | 🔴 |
| Bulk provision (CSV) | `POST /resources/bulk` | 🔴 | 🔴 | 🔴 | 🔴 |
| Get resource by ID | `GET /resources/{id}` | 🔴 | 🔴 | 🔴 | 🔴 |
| Search / filter catalog | `GET /resources` | 🔴 | 🔴 | 🔴 | 🔴 |
| Update resource metadata | `PATCH /resources/{id}` | 🔴 | 🔴 | 🔴 | 🔴 |
| Policy profile management | `POST/GET /policy-profiles` | 🔴 | 🔴 | 🔴 | 🔴 |
| Asset tag uniqueness enforcement | — | 🔴 | 🔴 | 🔴 | 🔴 |
| Mandatory field gate (PENDING → AVAILABLE) | — | 🔴 | 🔴 | 🔴 | 🔴 |

---

## Phase 2 – Reservation and Conflict Management

| Feature | API Endpoint | Unit Tests | Integration Tests | Staging | Production |
|---|---|---|---|---|---|
| Create reservation | `POST /reservations` | 🔴 | 🔴 | 🔴 | 🔴 |
| Window overlap check (GiST exclusion) | — | 🔴 | 🔴 | 🔴 | 🔴 |
| Idempotent reservation creation | — | 🔴 | 🔴 | 🔴 | 🔴 |
| Quota enforcement via Policy Engine | — | 🔴 | 🔴 | 🔴 | 🔴 |
| Priority ordering and displacement | — | 🔴 | 🔴 | 🔴 | 🔴 |
| Cancel reservation | `DELETE /reservations/{id}` | 🔴 | 🔴 | 🔴 | 🔴 |
| SLA timer for checkout window | — | 🔴 | 🔴 | 🔴 | 🔴 |
| Expire reservation on SLA breach | — | 🔴 | 🔴 | 🔴 | 🔴 |
| Concurrent reservation load test (50 RPS) | — | — | 🔴 | 🔴 | 🔴 |

---

## Phase 3 – Allocation and Custody

| Feature | API Endpoint | Unit Tests | Integration Tests | Staging | Production |
|---|---|---|---|---|---|
| Checkout (from reservation) | `POST /allocations` | 🔴 | 🔴 | 🔴 | 🔴 |
| Direct checkout (no reservation) | `POST /allocations` | 🔴 | 🔴 | 🔴 | 🔴 |
| Check-in with condition grade | `POST /allocations/{id}/checkin` | 🔴 | 🔴 | 🔴 | 🔴 |
| Condition delta computation | — | 🔴 | 🔴 | 🔴 | 🔴 |
| Allocation extension | `POST /allocations/{id}/extend` | 🔴 | 🔴 | 🔴 | 🔴 |
| Custody transfer | `POST /allocations/{id}/transfer` | 🔴 | 🔴 | 🔴 | 🔴 |
| Forced return | `POST /allocations/{id}/force-return` | 🔴 | 🔴 | 🔴 | 🔴 |
| Loss report | `POST /allocations/{id}/report-loss` | 🔴 | 🔴 | 🔴 | 🔴 |
| Idempotent checkout | — | 🔴 | 🔴 | 🔴 | 🔴 |

---

## Phase 4 – Overdue Detection and Escalation

| Feature | Owner | Unit Tests | Integration Tests | Staging | Production |
|---|---|---|---|---|---|
| Overdue detector cron job (5 min) | SRE / Platform | 🔴 | 🔴 | 🔴 | 🔴 |
| Mark allocation OVERDUE | — | 🔴 | 🔴 | 🔴 | 🔴 |
| Step 1 notification (T+0) | Platform | 🔴 | 🔴 | 🔴 | 🔴 |
| Step 2 warning (T+4h) | Platform | 🔴 | 🔴 | 🔴 | 🔴 |
| Step 3 manager escalation (T+24h) | Platform | 🔴 | 🔴 | 🔴 | 🔴 |
| Step 4 forced return eligible (T+48h) | Platform | 🔴 | 🔴 | 🔴 | 🔴 |
| Overdue accuracy test (1000 allocs) | — | — | 🔴 | 🔴 | 🔴 |

---

## Phase 5 – Incident and Settlement

| Feature | API Endpoint | Unit Tests | Integration Tests | Staging | Production |
|---|---|---|---|---|---|
| Auto-open incident on condition delta | — | 🔴 | 🔴 | 🔴 | 🔴 |
| Manual incident creation | `POST /incidents` | 🔴 | 🔴 | 🔴 | 🔴 |
| Incident assignment | `PATCH /incidents/{id}` | 🔴 | 🔴 | 🔴 | 🔴 |
| Incident resolution | `POST /incidents/{id}/resolve` | 🔴 | 🔴 | 🔴 | 🔴 |
| Settlement charge calculation (rate card) | — | 🔴 | 🔴 | 🔴 | 🔴 |
| Settlement approval | `POST /settlements/{id}/approve` | 🔴 | 🔴 | 🔴 | 🔴 |
| Settlement dispute | `POST /settlements/{id}/dispute` | 🔴 | 🔴 | 🔴 | 🔴 |
| Settlement void | `POST /settlements/{id}/void` | 🔴 | 🔴 | 🔴 | 🔴 |
| Settlement posting to ledger (outbox) | — | 🔴 | 🔴 | 🔴 | 🔴 |
| Daily reconciliation job | — | 🔴 | 🔴 | 🔴 | 🔴 |

---

## Phase 6 – Decommissioning and Archive

| Feature | API Endpoint | Unit Tests | Integration Tests | Staging | Production |
|---|---|---|---|---|---|
| Decommission precondition checks | `POST /resources/{id}/decommission` | 🔴 | 🔴 | 🔴 | 🔴 |
| High-value approval workflow | — | 🔴 | 🔴 | 🔴 | 🔴 |
| Transition to DECOMMISSIONING | — | 🔴 | 🔴 | 🔴 | 🔴 |
| Archive job (cold storage write) | — | 🔴 | 🔴 | 🔴 | 🔴 |
| Archive manifest generation | — | 🔴 | 🔴 | 🔴 | 🔴 |
| Transition to DECOMMISSIONED (terminal) | — | 🔴 | 🔴 | 🔴 | 🔴 |

---

## Phase 7 – Cross-Cutting and Infrastructure

| Feature | Owner | Unit Tests | Integration Tests | Staging | Production |
|---|---|---|---|---|---|
| Transactional outbox + relay job | Platform | 🔴 | 🔴 | 🔴 | 🔴 |
| Idempotency store (Redis) | Platform | 🔴 | 🔴 | 🔴 | 🔴 |
| Audit trail (hash-chained) | Platform / Compliance | 🔴 | 🔴 | 🔴 | 🔴 |
| Policy Engine (OPA sidecar) | Platform | 🔴 | 🔴 | 🔴 | 🔴 |
| Search indexer (Elasticsearch) | Platform | 🔴 | 🔴 | 🔴 | 🔴 |
| Structured logging + tracing (OTel) | SRE | 🔴 | 🔴 | 🔴 | 🔴 |
| Metrics and dashboards | SRE | 🔴 | 🔴 | 🔴 | 🔴 |
| Alert rules (5 critical alerts) | SRE | 🔴 | 🔴 | 🔴 | 🔴 |
| DLQ monitoring and replay | SRE | 🔴 | 🔴 | 🔴 | 🔴 |
| Load test suite (k6) | Platform | 🔴 | 🔴 | 🔴 | 🔴 |
| Database migrations (numbered SQL) | Platform | 🔴 | 🔴 | 🔴 | 🔴 |

---

## Release Readiness Checklist

### Feature Complete Gate
- [ ] All Phase 1–7 features show 🟢 Feature Complete
- [ ] Unit test coverage ≥ 90% on domain layer
- [ ] Integration test coverage for all command handlers
- [ ] No critical or high CodeQL security alerts
- [ ] OpenAPI spec generated and linted
- [ ] Schema migration tested on production-clone dataset

### Staging Gate
- [ ] Load test: P95 command latency < 500 ms at 200 RPS
- [ ] Concurrent reservation test: 50 concurrent requests → exactly 1 success
- [ ] Outbox relay tested under Kafka downtime (messages queued, no loss)
- [ ] Rollback tested: last migration reverted and service still functional
- [ ] Security scan: OWASP ZAP or equivalent; no high findings
- [ ] Overdue detector accuracy: 100% detection within 10 min of breach

### Production Gate
- [ ] All runbooks reviewed and signed off by on-call lead
- [ ] On-call handover: primary + secondary designates confirmed
- [ ] Compliance attestation: audit trail integrity test passed
- [ ] 5 critical alerts configured and fire-tested in staging
- [ ] Blast-radius analysis completed for partition failure and outbox lag
- [ ] Daily reconciliation job validated for financial accuracy

---

## Cross-References

- Implementation guidelines: [implementation-guidelines.md](./implementation-guidelines.md)
- Edge cases (detection/recovery): [../edge-cases/README.md](../edge-cases/README.md)
- Infrastructure topology: [../infrastructure/deployment-diagram.md](../infrastructure/deployment-diagram.md)
