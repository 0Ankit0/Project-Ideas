# Hotel Property Management System — Edge Cases

## Purpose

This directory documents every known edge case, failure mode, and exceptional scenario that the Hotel Property Management System (HPMS) must handle gracefully. Edge cases are not afterthoughts — they represent the most expensive bugs in hospitality software. A double-booking at a 200-room hotel during a sold-out weekend is not a theoretical concern; it is a recurring operational reality that costs revenue, erodes guest trust, and triggers regulatory liability.

Each edge case in this library is written to a consistent template so that developers, QA engineers, operations staff, and hotel management can use the same document to understand a problem from every angle: the technical root cause, the guest-facing impact, the staff response workflow, the financial consequences, and the system-level prevention strategy.

This documentation is **living**. When a new edge case is discovered in production, a new entry is added within 48 hours. When a resolution changes, the entry is updated and the change is logged in the document's revision history.

---

## Edge Case Categories

| # | Category File | Edge Cases Covered | Primary Services Affected |
|---|---------------|--------------------|--------------------------|
| 1 | `reservation-management.md` | Double booking, overbooking, OTA sync conflict, VIP block conflict, group booking failure | ReservationService, InventoryService, ChannelManager |
| 2 | `check-in-and-check-out.md` | Early arrival, late checkout dispute, no-show, walk-in during full occupancy, express checkout failure, duplicate check-in | FrontDeskService, FolioService, RoomService |
| 3 | `room-assignment-and-housekeeping.md` | Room not ready, maintenance emergency, downgrade, housekeeper unavailability, status mismatch, VIP inspection failure | HousekeepingService, MaintenanceService, RoomService |
| 4 | `billing-and-invoicing.md` | Folio split failure, payment decline, city ledger dispute, tax error, voided charge, multi-currency exchange discrepancy | FolioService, PaymentService, AccountingService |
| 5 | `api-and-ui.md` | OTA sync failure, POS offline, keycard system failure, payment gateway timeout, duplicate webhook, channel manager outage | APIGateway, IntegrationService, ChannelManager |
| 6 | `security-and-compliance.md` | PCI-DSS log exposure, GDPR breach, keycard master key compromise, tokenisation failure, privileged access abuse, data retention violation | AuthService, AuditService, ComplianceService |
| 7 | `operations.md` | Night audit failure, database failover, channel manager outage, multi-property sync failure, backup restoration failure, cascading service failure | NightAuditService, DatabaseCluster, InfrastructureLayer |

---

## How to Use This Documentation

### For Developers

Read the *Trigger Conditions*, *Failure Mode*, and *Prevention* sections when designing new features. Before merging a pull request that touches reservation logic, billing, or room state transitions, verify that your implementation does not introduce a new trigger for any documented edge case. Run the linked *Test Cases* as part of your feature's test suite.

### For QA Engineers

Use each edge case entry as a structured test specification. The *Trigger Conditions* section describes how to reproduce the scenario. The *Expected System Behaviour* section describes the pass criteria. The *Failure Mode* section describes what a failing system looks like, which helps you write negative tests and chaos scenarios.

### For Operations / SRE Teams

The *Detection* section tells you which metrics, log lines, and alerts fire when this edge case occurs in production. The *Resolution* section gives the immediate runbook. Cross-reference with the `operations.md` file for infrastructure-level edge cases that span multiple services.

### For Hotel Management and Front Desk Supervisors

Each edge case includes a *Guest Experience* note explaining what the guest sees and a *Staff Workflow* note explaining the recommended front-desk procedure. These sections use plain language and avoid technical jargon. The *Compensation Policy* subsection (where applicable) describes the authorised remediation (room upgrade, F&B credit, waived charges) and the approval threshold required.

---

## Edge Case Template

Every edge case in this directory uses the following template. All fields are mandatory. If a field does not apply to a specific case, the field must still be present with the value `N/A — [reason]`.

---

**EC-XXX — [Title]**

*Category:* `[Category name, e.g., Reservation Management]`
*Severity:* `[Critical | High | Medium | Low]`
*Likelihood:* `[Very High | High | Medium | Low | Rare]`
*Affected Services:* `[Comma-separated list of services]`

**Description**
A plain-language description of the edge case in 2–5 sentences. Who is affected, what goes wrong, and what is the business consequence.

**Trigger Conditions**
A numbered list of the precise conditions that must be true simultaneously for this edge case to occur. Be specific about timing, data state, concurrent users, and external dependencies.

1. Condition A
2. Condition B
3. Condition C (optional: only required in variant X)

**Expected System Behaviour**
What a correctly implemented system does when this edge case is triggered. Written as a numbered sequence of system actions, each annotated with the expected response time or deadline where relevant.

1. System detects condition within N ms.
2. System executes X.
3. System returns Y to the caller.

**Failure Mode**
What actually happens in a broken system. Describe the incorrect state, the cascading effects, and the worst-case outcome if the failure propagates unchecked.

**Detection**
- *Monitoring:* Which Prometheus/Datadog metrics spike or drop.
- *Log Pattern:* The log line or structured log field that identifies this failure.
- *Alert:* The alert rule that fires (alert name, threshold, channel).
- *User-Reported:* How guests or staff typically report this failure before monitoring catches it.

**Resolution**
A step-by-step runbook, numbered and actionable. Distinguish between immediate containment (first 5 minutes), short-term fix (first hour), and full remediation (up to 24 hours).

**Prevention**
Architectural and procedural controls that reduce the likelihood of this edge case to an acceptable level. Reference specific design patterns (optimistic locking, idempotency keys, circuit breakers, saga pattern) where relevant.

**Test Cases**
- *TC-1:* [Happy-path variant — normal resolution]
- *TC-2:* [Failure-path variant — system fails correctly]
- *TC-3:* [Boundary variant — edge of the edge]

---

## Severity Classification

| Severity | Definition | Examples | Maximum Acceptable Time-to-Resolution |
|----------|-----------|---------|--------------------------------------|
| **Critical** | Direct financial loss, regulatory violation, or complete service unavailability affecting guests actively in the property. System cannot recover automatically. | Double booking confirmed to two guests, PCI data exposed in logs, payment charged but not recorded, night audit fails to run, database unavailable during check-in peak | 15 minutes to containment; 4 hours to full resolution |
| **High** | Significant guest experience degradation or financial discrepancy that requires staff intervention but does not block core operations. Automatic recovery is possible but not guaranteed. | OTA sync delayed >15 min, express checkout blocked, folio split fails, room assigned to wrong guest, channel manager down | 1 hour to containment; 8 hours to full resolution |
| **Medium** | Operational inefficiency or minor financial discrepancy that can be resolved during normal business hours. No direct guest impact at the time of occurrence. | Housekeeper assignment delayed, room status mismatch corrected on next sync, minor tax rounding error, stale keycard needing re-encoding | 4 hours to resolution |
| **Low** | Cosmetic issue, minor data inconsistency, or edge case so rare that it is handled entirely by existing manual procedures without new automation. | Incorrect room-type label in confirmation email, loyalty points delayed by one audit cycle, PDF invoice rendering issue | Next business day |

---

## Resolution Priority Matrix

The matrix below combines **Severity** (how bad is the impact?) with **Likelihood** (how often does it happen?) to produce a **Priority** that determines the order in which engineering resources are allocated.

```
                    LIKELIHOOD
                Rare    Low    Medium   High    Very High
              +-------+-------+-------+-------+---------+
SEVERITY      |       |       |       |       |         |
  Critical    |  P1   |  P1   |  P1   |  P1   |   P1    |
  High        |  P3   |  P2   |  P2   |  P1   |   P1    |
  Medium      |  P4   |  P3   |  P3   |  P2   |   P2    |
  Low         |  P4   |  P4   |  P4   |  P3   |   P3    |
              +-------+-------+-------+-------+---------+
```

**Priority Definitions:**

| Priority | Response SLA | Engineering Action |
|----------|-------------|-------------------|
| **P1** | Immediate (on-call paged within 5 min) | Drop current sprint work; hotfix deployed to production within 4 hours |
| **P2** | Same day (acknowledged within 1 hour) | Scheduled for current sprint; reviewed in next daily standup |
| **P3** | Within current sprint (3–5 days) | Backlog item created with full edge case documentation as acceptance criteria |
| **P4** | Backlog (no SLA) | Documented for awareness; addressed when capacity allows or when frequency increases |

---

## Cross-Cutting Concerns

Several edge cases across different categories share common root causes. The table below maps root causes to all edge cases they affect, helping engineers prioritise foundational fixes that resolve multiple issues simultaneously.

| Root Cause | Affected Edge Cases |
|------------|-------------------|
| Lack of distributed locking on inventory writes | EC-RES-001, EC-RES-002, EC-RES-003 |
| Eventual consistency between room state and booking state | EC-CHK-006, EC-HSK-005, EC-OPS-004 |
| Missing idempotency keys on payment requests | EC-BIL-002, EC-API-004, EC-API-005 |
| No circuit breaker on external API calls | EC-API-001, EC-API-006, EC-OPS-003 |
| Insufficient audit logging granularity | EC-BIL-005, EC-SEC-001, EC-SEC-005 |
| No offline fallback for critical guest-facing operations | EC-API-002, EC-API-003, EC-API-004 |
| Incomplete saga / compensating transaction pattern | EC-RES-005, EC-BIL-001, EC-OPS-006 |
| Missing GDPR data lifecycle management | EC-SEC-002, EC-SEC-006 |
| Night audit as a single point of failure | EC-OPS-001, EC-BIL-004 |
| Database single-region deployment | EC-OPS-002, EC-OPS-005 |

---

## Revision History

| Version | Date | Author | Change Summary |
|---------|------|--------|---------------|
| 1.0 | Initial release | Engineering Team | All seven category files created with baseline edge cases |

---

## Contributing a New Edge Case

When a new edge case is discovered — in production, during QA, or during a design review — follow this process:

1. **Check for duplicates.** Search this directory for keywords from the new scenario before creating a new entry.
2. **Assign an ID.** Use the next available sequential ID in the appropriate category prefix (EC-RES-006, EC-BIL-007, etc.).
3. **Fill in all template fields.** No field may be left as "TBD" or "TODO" before merging.
4. **Assign severity and likelihood.** Use the classification table above. If uncertain, default to one severity level higher than you think is correct — it is easier to downgrade than to miss a critical issue.
5. **Add test cases.** At minimum two test cases per edge case: one that verifies correct system behaviour and one that verifies graceful degradation.
6. **Update this README.** Add the new entry to the category table under the correct file.
7. **Submit a pull request** with the label `edge-case-documentation`.
