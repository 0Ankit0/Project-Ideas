# Edge Cases Overview

This directory documents all failure scenarios for the **Resource Lifecycle Management Platform**. Each file covers a category of edge cases with: detection signals, immediate containment, recovery path, SLA, owner, and verification method.

---

## Edge Case Categories

| File | Category | Scenarios |
|---|---|---|
| [reservation-and-allocation-conflicts.md](./reservation-and-allocation-conflicts.md) | Concurrency, contention | Double-booking, quota race, priority displacement conflict |
| [checkout-checkin-and-condition-disputes.md](./checkout-checkin-and-condition-disputes.md) | Custody integrity | Disputed checkout/checkin conditions, missing scan, photo evidence gaps |
| [lifecycle-state-sync-and-overdue-recovery.md](./lifecycle-state-sync-and-overdue-recovery.md) | State consistency | State drift, overdue detector failure, escalation ladder gap |
| [settlement-and-incident-resolution.md](./settlement-and-incident-resolution.md) | Financial integrity | Ledger posting failure, double-charge, disputed settlement, reconciliation mismatch |
| [api-and-ui.md](./api-and-ui.md) | Interface failures | Malformed input, duplicate idempotency keys, scanner outage, rate limit abuse |
| [security-and-compliance.md](./security-and-compliance.md) | Security | Unauthorized access, policy bypass, audit log gap, token replay |
| [operations.md](./operations.md) | Ops and infrastructure | DB failover, Kafka lag, DLQ overflow, outbox relay failure |

---

## Global Response Matrix

| Scenario Type | Detection Signal | Immediate Containment | Recovery Path | Owner | SLA |
|---|---|---|---|---|---|
| Policy violation | denied decision / drift alert | Freeze unsafe transition; emit `policy.violation` event | Correct policy context + replay command from DLQ | Platform Engineering | 30 min |
| State mismatch | Reconciliation mismatch event | Quarantine resource to `EXCEPTION` state | Reconcile source-of-truth; backfill missing events | SRE | 2 h |
| Financial inconsistency | Ledger mismatch in daily reconciliation | Suspend settlement posting; alert Finance | Rerun reconciliation; manual approval for corrections | Finance + SRE | 4 h |
| Concurrency conflict | 409 returned; optimistic lock fail counter spike | Return 409 with retry instructions; no state change | Client retry with same idempotency key; exponential backoff | Platform Engineering | Immediate |
| Data loss / corruption | Audit hash chain break; record count mismatch | Halt writes to affected resource; alert Compliance | Restore from point-in-time backup; replay event log | SRE + Compliance | 1 h |

---

## Cross-References

- Business rules (governing each edge case): [../analysis/business-rules.md](../analysis/business-rules.md)
- State machine (valid transitions): [../detailed-design/state-machine-diagrams.md](../detailed-design/state-machine-diagrams.md)
- Lifecycle orchestration (compensation patterns): [../detailed-design/lifecycle-orchestration.md](../detailed-design/lifecycle-orchestration.md)
