# User Stories

Structured user stories for the **Resource Lifecycle Management Platform**, organized by actor. Each story follows the format: *As a [role], I want [capability] so that [value/outcome]*, and includes acceptance criteria and priority.

## Priority Legend
- **P1** – Must have for MVP
- **P2** – Should have for general availability
- **P3** – Nice to have / future phase

---

## Requestor Stories

| ID | Story | Acceptance Criteria | Priority |
|---|---|---|---|
| US-REQ-01 | As a **Requestor**, I want to search the resource catalog by category, availability window, and location so that I can find the right resource quickly. | Search returns results within 1 s; only available resources are surfaced for the requested window; results include condition grade and location. | P1 |
| US-REQ-02 | As a **Requestor**, I want to submit a reservation request for a specific resource and date/time window so that the resource is held for me. | Reservation is confirmed with a unique `reservation_id`; conflict results in a 409 with suggested alternatives; confirmation email/notification is sent. | P1 |
| US-REQ-03 | As a **Requestor**, I want to view the status of all my active and past reservations so that I can manage my commitments. | Dashboard shows state, due date, and resource details for all my reservations; past records are searchable. | P1 |
| US-REQ-04 | As a **Requestor**, I want to cancel a reservation before the checkout window opens so that unused capacity is returned to the pool. | Cancellation succeeds when resource is in `Reserved` state; cancellation event is published; any hold is released. | P1 |
| US-REQ-05 | As a **Requestor**, I want to extend an active allocation before it expires so that I do not incur an overdue penalty. | Extension request checks quota, policy, and absence of conflicting reservations; approved extension updates the due date and SLA timer. | P2 |
| US-REQ-06 | As a **Requestor**, I want to report a resource as lost or damaged during my allocation so that an incident case is opened promptly. | Loss/damage report creates an incident case within 30 s; case is linked to my allocation; I receive a case number and next-steps notification. | P1 |

---

## Resource Manager Stories

| ID | Story | Acceptance Criteria | Priority |
|---|---|---|---|
| US-MGR-01 | As a **Resource Manager**, I want to onboard new resources by uploading a CSV template so that bulk provisioning is fast and error-free. | CSV up to 1,000 rows processes atomically; rows with validation errors are reported per-row; successful rows are available in the catalog within 30 s. | P1 |
| US-MGR-02 | As a **Resource Manager**, I want to define allocation policies (quota, priority, time limits, eligibility rules) per resource category so that platform behavior is governed consistently. | Policies are stored as versioned rules; new allocations immediately use the latest active policy version; changes are audited. | P1 |
| US-MGR-03 | As a **Resource Manager**, I want to view a real-time utilization dashboard showing availability, active allocations, and overdue resources so that I can manage the fleet proactively. | Dashboard refreshes within 30 s; shows per-category counts, overdue rate, and SLA breach rate; drill-down to individual resource timeline. | P1 |
| US-MGR-04 | As a **Resource Manager**, I want to schedule preventive maintenance windows during which a resource is unavailable for reservation so that condition issues are resolved proactively. | Maintenance window blocks new reservations for the window period; existing reservations in the window are auto-cancelled with notification. | P2 |
| US-MGR-05 | As a **Resource Manager**, I want to approve high-value decommission requests so that assets are not disposed of without proper authorization. | Decommission workflow routes approval tasks to the assigned manager role; approval or rejection is recorded with reason; decommission proceeds only after approval. | P1 |
| US-MGR-06 | As a **Resource Manager**, I want to generate utilization and financial settlement reports for any date range so that I can support budget reviews and audits. | Reports export in CSV and PDF; data includes allocation count, days-in-use, settlement amounts, and condition grade distribution. | P2 |

---

## Custodian Stories

| ID | Story | Acceptance Criteria | Priority |
|---|---|---|---|
| US-CUST-01 | As a **Custodian**, I want to check out a resource by scanning its asset tag so that custody is transferred to me instantly. | Scan triggers a checkout command; system confirms or rejects within 2 s; accepted checkout transitions resource to `Allocated` and records my identity. | P1 |
| US-CUST-02 | As a **Custodian**, I want to check in a resource by scanning its tag and recording condition so that custody is transferred back and any condition issues are captured. | Check-in records `actor_id`, `timestamp`, and condition grade; condition delta is computed; resource transitions to `Inspection` state. | P1 |
| US-CUST-03 | As a **Custodian**, I want to receive automated reminders before my return deadline so that I do not inadvertently go overdue. | Reminder notifications are sent at 24 h and 2 h before due date; notifications include resource name, due date, and return instructions. | P1 |
| US-CUST-04 | As a **Custodian**, I want to transfer custody to another approved person so that temporary handoffs are tracked. | Transfer command verifies the receiving actor has allocation eligibility; creates a custody transfer record; both actors receive confirmation. | P2 |

---

## Operations / SRE Stories

| ID | Story | Acceptance Criteria | Priority |
|---|---|---|---|
| US-OPS-01 | As an **Operations engineer**, I want to view a live event stream for all lifecycle state transitions so that I can diagnose issues in real time. | Event stream UI shows latest 1,000 events with filter by resource, actor, event type, and state; latency < 5 s. | P1 |
| US-OPS-02 | As an **Operations engineer**, I want to initiate a forced-return for an overdue allocation with a mandatory justification so that the resource is recovered even when the custodian is unresponsive. | Forced-return requires approver identity and reason code; creates `allocation.forced_return` event; resource transitions to `Inspection`; custodian and manager are notified. | P1 |
| US-OPS-03 | As an **Operations engineer**, I want automated alerts when DLQ depth exceeds a threshold so that unprocessed events are actioned immediately. | Alert fires within 5 min of DLQ depth crossing 10 messages; alert contains queue name, depth, and link to runbook. | P1 |
| US-OPS-04 | As an **Operations engineer**, I want to replay a failed command from the DLQ with a new idempotency key so that transient failures are resolved without data loss. | Replay operation is audited; replayed command is treated as a new command with traceability back to original; duplicate protection prevents double-processing. | P2 |

---

## Compliance Officer Stories

| ID | Story | Acceptance Criteria | Priority |
|---|---|---|---|
| US-COMP-01 | As a **Compliance Officer**, I want to pull a full audit trail for any resource from provisioning to decommissioning so that I can satisfy an external audit. | Audit trail API returns all lifecycle events, actor identities, timestamps, and condition records within 5 s; data is tamper-evident (hash-chained). | P1 |
| US-COMP-02 | As a **Compliance Officer**, I want to configure retention periods per resource category so that data is retained according to applicable regulations. | Retention rules prevent deletion of records until the period expires; expired records are archived, not deleted, and remain accessible with elevated privileges. | P1 |
| US-COMP-03 | As a **Compliance Officer**, I want to receive a report of all policy override events in the past 90 days so that I can identify governance gaps. | Override report lists all manual-override commands with approver, reason, expiry, and linked resource; exportable as CSV. | P2 |

---

## Finance Stories

| ID | Story | Acceptance Criteria | Priority |
|---|---|---|---|
| US-FIN-01 | As a **Finance** team member, I want to view all open settlement cases with amounts owed so that collections are actioned promptly. | Settlement dashboard shows case ID, resource, allocation window, amount, and status; filterable by date range and status. | P1 |
| US-FIN-02 | As a **Finance** team member, I want deposit hold events published to the financial ledger automatically so that manual journal entries are eliminated. | Every deposit hold and release is published as an exactly-once financial event; reconciliation report shows zero discrepancies daily. | P1 |
| US-FIN-03 | As a **Finance** team member, I want to dispute a damage charge with supporting evidence so that the amount can be adjusted. | Dispute workflow requires supporting notes; disputed charge is frozen until resolved; resolution records approver, adjusted amount, and reason. | P2 |

---

## System (Automated) Stories

| ID | Story | Acceptance Criteria | Priority |
|---|---|---|---|
| US-SYS-01 | As the **Overdue Detector**, I want to scan all active allocations every 5 minutes so that no overdue breach goes undetected for more than 10 minutes. | Detector job runs on schedule; `allocation.overdue` event is emitted within 10 min of breach; escalation ladder is triggered. | P1 |
| US-SYS-02 | As the **Policy Engine**, I want to evaluate every allocation request against the current policy set so that no unauthorized allocation succeeds. | Policy evaluation result is cached for 60 s; every evaluation result (permit/deny) is logged with matched policy ID and version. | P1 |
| US-SYS-03 | As the **Archive Job**, I want to move decommissioned resource records to cold storage within 24 hours of decommission approval so that the operational database remains lean. | Archive job runs nightly; completed archive produces a manifest; manifest is queryable from the compliance API. | P2 |

---

## Traceability

- Requirements: [requirements.md](./requirements.md)
- Business rules: [../analysis/business-rules.md](../analysis/business-rules.md)
- Use case descriptions: [../analysis/use-case-descriptions.md](../analysis/use-case-descriptions.md)
