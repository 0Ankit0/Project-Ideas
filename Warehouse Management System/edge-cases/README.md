# Edge Cases - Warehouse Management System

This section contains implementation-ready failure playbooks for high-risk warehouse scenarios.

## Scope
- Receiving anomalies (ASN mismatch, damaged inbound, quarantine routing)
- Allocation/picking conflicts (bin contention, short picks, partial fulfillment)
- Device and integration disruptions (offline scanner replay, carrier outage)
- Security and compliance violations (unauthorized override, audit gaps)

## How to Use These Playbooks
1. **Design time:** incorporate the listed detection signals and resolution paths into API/state/worker design.
2. **Implementation time:** instrument required metrics/events and expose remediation commands.
3. **Operations time:** follow containment/recovery steps and complete verification checklist.

## Playbook Contract (Required in each file)
- Scenario + trigger conditions.
- Detection signals (metrics/events/log patterns).
- Immediate containment steps.
- Deterministic recovery procedure.
- Preventive controls and regression tests.

## Linked Playbooks
- [api-and-ui.md](./api-and-ui.md)
- [bin-conflicts.md](./bin-conflicts.md)
- [cycle-count-adjustments.md](./cycle-count-adjustments.md)
- [offline-scanner-sync.md](./offline-scanner-sync.md)
- [operations.md](./operations.md)
- [partial-picks-backorders.md](./partial-picks-backorders.md)
- [security-and-compliance.md](./security-and-compliance.md)

## Rule Linkage
- BR-3/BR-4: override governance and approval evidence.
- BR-5: idempotent retries and replay safety.
- BR-10: deterministic exception handling and auditability.
