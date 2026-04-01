# Edge Cases — Warehouse Management System

## Overview and Purpose

This directory contains implementation-ready failure playbooks for every high-risk scenario identified in the WMS design. Each playbook is an operational contract: it defines the exact trigger, observable signals, role-specific response steps, deterministic recovery procedure, and preventive architectural controls. Engineers use these playbooks at design time to build correct systems; operators use them at runtime to contain and recover from incidents without ambiguity.

---

## Failure Taxonomy

| # | Edge Case File | Category | Primary Risk |
|---|---|---|---|
| 1 | `bin-conflicts.md` | Inventory Conflicts | ATP goes negative, duplicate picks |
| 2 | `partial-picks-backorders.md` | Inventory Conflicts | Order SLA breach, backorder debt |
| 3 | `cycle-count-adjustments.md` | Inventory Conflicts | Adjustment invalidates active reservations |
| 4 | `offline-scanner-sync.md` | Device / Connectivity | Replay conflicts, ghost movements |
| 5 | `api-and-ui.md` | Integration Failures | Duplicate submits, stale UI state |
| 6 | `operations.md` | Integration Failures | Carrier outage, orphaned reservations |
| 7 | `security-and-compliance.md` | Security / Compliance | Fraud, insider abuse, audit gaps |

---

## Linked Playbooks

| Playbook | One-Line Description |
|---|---|
| [api-and-ui.md](./api-and-ui.md) | Handles duplicate submits, version conflicts, partial composite failures, and stale UI state |
| [bin-conflicts.md](./bin-conflicts.md) | Resolves concurrent pick/putaway races that over-commit a bin beyond its ATP |
| [cycle-count-adjustments.md](./cycle-count-adjustments.md) | Safe inventory adjustment procedure when active picks/reservations are in flight |
| [offline-scanner-sync.md](./offline-scanner-sync.md) | Replay and conflict resolution when a scanner reconnects after a dead-zone outage |
| [operations.md](./operations.md) | Carrier API outage, event bus lag, DB replication lag, wave planner crash |
| [partial-picks-backorders.md](./partial-picks-backorders.md) | Short-pick handling: alternate bin search, partial fulfillment, and backorder creation |
| [security-and-compliance.md](./security-and-compliance.md) | Compromised credentials, insider abuse, bulk adjustment fraud, audit log tampering |

---

## How to Use These Playbooks

### Design Teams
1. Review the **Failure Mode** section of each relevant playbook before finalising data models or API contracts.
2. Add the listed **Detection** metrics to your observability plan.
3. Map each prevention control to a specific architectural decision record (ADR).

### Implementation Teams
1. Instrument every **Detection** metric and log pattern listed before the feature ships.
2. Implement the **Prevention** controls (locks, idempotency keys, approval gates) as acceptance criteria.
3. Add all **Test Scenarios** listed in each playbook to the automated regression suite.

### Operations Teams
1. During an incident, open the relevant playbook and follow **Mitigation** steps in numbered order.
2. Use **Recovery** steps to restore normal state; do not skip verification checkpoints.
3. After incident closure, complete a post-incident review referencing the playbook's **Prevention** section.

---

## Severity Classification

| Severity | Definition | Initial Response SLA | Update Cadence |
|---|---|---|---|
| **Sev-1** | Production outage or data integrity breach affecting >10% of orders | 5 minutes | Every 15 min |
| **Sev-2** | Degraded throughput or SLA breach risk for active orders | 15 minutes | Every 30 min |
| **Sev-3** | Non-critical feature impaired; workaround exists | 1 hour | Every 2 hours |
| **Sev-4** | Cosmetic or low-impact issue; no live orders affected | Next business day | Daily |

---

## On-Call Escalation Matrix

| Role | Contact | Response Time (Sev-1) | Response Time (Sev-2) |
|---|---|---|---|
| On-call Engineer | PagerDuty primary rotation | 5 min | 15 min |
| Warehouse Operations Lead | Ops on-call channel | 10 min | 30 min |
| Inventory Manager | Secondary PagerDuty | 15 min | 1 hour |
| Security Team | SIEM alert + Slack `#security-incidents` | Immediate (auto) | 30 min |
| Engineering Manager | Escalation after 20 min unacknowledged | 20 min | 1 hour |

---

## Business Rule Linkage

| Playbook | Related Business Rules |
|---|---|
| `bin-conflicts.md` | BR-11 (no negative ATP), BR-05 (idempotent reservations) |
| `partial-picks-backorders.md` | BR-09 (backorder policy), BR-11 (ATP guard) |
| `cycle-count-adjustments.md` | BR-08 (adjustment approval), BR-11 (ATP guard) |
| `offline-scanner-sync.md` | BR-05 (idempotency), BR-10 (deterministic exception handling) |
| `api-and-ui.md` | BR-05 (idempotency), BR-07 (version conflict policy) |
| `operations.md` | BR-10 (exception handling), BR-06 (carrier fallback) |
| `security-and-compliance.md` | BR-03 (override governance), BR-04 (approval evidence), BR-10 (auditability) |

---

## Monitoring Coverage Summary

| Edge Case | Detection Metric | Alert Name | SLO Threshold |
|---|---|---|---|
| Bin conflicts | `reservation_conflict_rate` per bin/min | `BinConflictRateHigh` | > 5 conflicts/min |
| Partial picks | short-pick rate % of picks/hour | `ShortPickRateHigh` | > 2% |
| Cycle count variance | `|variance_pct|` per bin | `CycleCountVarianceAlert` | > 2% |
| Offline scanner | device offline duration (seconds) | `ScannerOfflineTooLong` | > 60 s |
| API duplicate submit | idempotency key duplicate hit rate | `IdempotencyKeyHitRate` | > 1% |
| Carrier outage | carrier API error rate % | `CarrierAPIErrorHigh` | > 10% |
| Event bus lag | consumer group lag (seconds) | `EventBusLagHigh` | > 30 s |
| Security anomaly | picks outside shift hours | `AnomalousPickPattern` | Any hit |

---

## Playbook Contract (Required Sections per File)

Every playbook in this directory must contain:

- **Failure Mode** — exact scenario description with trigger conditions
- **Impact** — business, user, and operational impact including SLA and financial exposure
- **Detection** — monitoring alerts, log patterns, SLO breach indicators, metric thresholds
- **Mitigation** — numbered, role-specific immediate response steps
- **Recovery** — numbered steps to restore normal state with verification checkpoints
- **Prevention** — architectural and process controls to prevent recurrence
- A **mermaid diagram** showing failure/recovery flow
- **Related Business Rules** and **Test Scenarios to Add**
