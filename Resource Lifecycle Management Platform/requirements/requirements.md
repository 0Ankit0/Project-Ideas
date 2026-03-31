# Requirements

Implementation-ready functional and non-functional requirements for the **Resource Lifecycle Management Platform (RLMP)**. Every requirement is stated as a testable MUST/SHALL statement, linked to an owner team and a verification method.

## Scope

The RLMP governs the full lifespan of physical, virtual, and digital assets from first intake through final decommissioning. It supports enterprise IT assets (laptops, servers, peripherals), shared spaces (meeting rooms, labs), vehicles, tools, and any other managed resource that must be tracked, reserved, allocated, and eventually retired. The platform enforces policy gates at every lifecycle transition and produces a tamper-evident audit trail for compliance and financial reconciliation.

## Actors

| Actor | Description |
|---|---|
| **Requestor** | Any employee or system that submits a resource request or reservation |
| **Resource Manager** | Approves provisioning, manages catalog, and sets allocation policies |
| **Custodian** | Holds physical or logical custody of an allocated resource |
| **Operations / SRE** | Monitors platform health, operates exception runbooks |
| **Compliance Officer** | Reviews audit evidence, manages retention obligations |
| **Finance** | Handles deposit, damage assessment, and financial reconciliation |
| **System (automated)** | Scheduled jobs, policy engine, overdue detector |

---

## Functional Requirements

### Provisioning and Catalog

| ID | Requirement | Acceptance Criteria | Related Rules |
|---|---|---|---|
| FR-PROV-01 | The system SHALL validate tenant identity, entitlement scope, and resource template integrity before creating a resource record. | Invalid provisioning attempts are rejected with a structured error code within 2 s; no partial resource record is persisted on failure. | BR-1, BR-2 |
| FR-PROV-02 | The system SHALL assign a globally unique, immutable `resource_id` at provisioning time. | No two resources share the same `resource_id` across any tenant or environment; ID is present in all downstream events. | BR-1 |
| FR-PROV-03 | The system SHALL capture intake metadata including category, condition grade, serial/asset tag, and responsible cost centre at registration time. | All mandatory fields pass schema validation; record is searchable by tag within 5 s of creation. | BR-2 |
| FR-PROV-04 | The system SHALL support template-based bulk provisioning for up to 1,000 resources in a single operation with transactional rollback on partial failure. | Batch import either commits all records or rolls back entirely; a per-record error report is returned on failure. | BR-1, BR-5 |
| FR-PROV-05 | The system SHALL emit a `resource.provisioned` domain event upon successful catalog entry. | Event is observable on the event bus within 500 ms; contains `resource_id`, `category`, `tenant_id`, `correlation_id`. | BR-5 |

### Reservation and Allocation

| ID | Requirement | Acceptance Criteria | Related Rules |
|---|---|---|---|
| FR-ALLOC-01 | The system SHALL enforce no-overlap reservation windows for the same resource; conflicting requests MUST be rejected with a 409 and a retry token. | Concurrent reservations for the same resource and overlapping time windows never both succeed; the losing request receives a structured 409 within 1 s. | BR-3, BR-6 |
| FR-ALLOC-02 | The system SHALL enforce per-tenant and per-requestor resource quotas defined in policy. | Requests exceeding configured quota are denied at policy evaluation time; quota state is updated atomically with reservation creation. | BR-3 |
| FR-ALLOC-03 | The system SHALL support priority-ordered allocation so higher-priority requestors can displace lower-priority pending reservations, subject to policy. | Priority displacement produces an audit event for both affected reservations; displaced requestor receives a notification within 30 s. | BR-3, BR-4 |
| FR-ALLOC-04 | The system SHALL attach an SLA timer to every reservation; approaching and breached SLAs SHALL trigger escalation events. | SLA timer state is persisted; 80% SLA elapsed triggers a warning event; 100% triggers an escalation event with assigned owner. | BR-3 |
| FR-ALLOC-05 | The system SHALL transition a resource from `Reserved` to `Allocated` upon confirmed checkout, recording `actor_id`, `checkout_time`, and condition snapshot. | Checkout confirmation is idempotent; duplicate confirms do not alter state or duplicate events; condition snapshot is stored. | BR-5, BR-7 |

### Custody and Condition Tracking

| ID | Requirement | Acceptance Criteria | Related Rules |
|---|---|---|---|
| FR-CUST-01 | The system SHALL record custody transfers with actor identity and timestamp at every handoff event. | Every custody record includes `from_actor`, `to_actor`, `timestamp`, and `correlation_id`; transfer events are immutable. | BR-5, BR-7 |
| FR-CUST-02 | The system SHALL capture condition assessment (grade A–D, free-text notes, optional photo evidence reference) at checkout and check-in. | Condition delta between checkout and check-in is computed and stored; delta is surfaced in the incident/settlement workflow when grade degrades. | BR-7, BR-8 |
| FR-CUST-03 | The system SHALL support scheduled and ad-hoc inspections, recording inspector identity, timestamp, and result. | Inspection creates an `inspection.completed` event; failed inspection triggers a maintenance or incident workflow. | BR-7 |

### Overdue and Lifecycle Recovery

| ID | Requirement | Acceptance Criteria | Related Rules |
|---|---|---|---|
| FR-OVER-01 | The system SHALL automatically detect overdue allocations when the agreed return date passes without a check-in event. | Overdue detector runs at maximum 5-minute intervals; `allocation.overdue` event is emitted within 10 minutes of breach. | BR-4 |
| FR-OVER-02 | The system SHALL support a configurable escalation ladder: notify → warn → escalate to manager → forced-return workflow. | Each escalation step has a configurable delay; all steps are logged; escalation state is visible in the operations dashboard. | BR-4, BR-9 |
| FR-OVER-03 | The system SHALL allow operations to initiate a forced-return with mandatory justification, transferring custody back to the platform without custodian action. | Forced-return requires approver role + reason code; produces an `allocation.forced_return` event and initiates inspection. | BR-4, BR-9 |

### Settlement and Incident Resolution

| ID | Requirement | Acceptance Criteria | Related Rules |
|---|---|---|---|
| FR-SETT-01 | The system SHALL create an incident case when a condition delta, overdue breach, or loss report is detected. | Incident cases are created within 30 s of trigger; linked to `resource_id`, `allocation_id`, and responsible actor. | BR-8, BR-9 |
| FR-SETT-02 | The system SHALL support configurable deposit hold and damage charge calculations based on condition grade and policy rate cards. | Settlement amounts are traceable to the rate card version active at time of allocation; all calculations are auditable. | BR-8 |
| FR-SETT-03 | The system SHALL integrate with the financial ledger via an outbox-based event to record charges, refunds, and deposit releases. | Financial events are exactly-once delivered to the ledger; reconciliation report confirms no missing or duplicate charges daily. | BR-5, BR-8 |

### Decommissioning

| ID | Requirement | Acceptance Criteria | Related Rules |
|---|---|---|---|
| FR-DECOM-01 | The system SHALL require financial closure (zero outstanding charges) and retention lock release before a resource can transition to `Decommissioned`. | Decommission command fails if open settlement cases or retention holds exist; error code identifies the blocking condition. | BR-10 |
| FR-DECOM-02 | The system SHALL require approval authority sign-off for decommission of high-value resources (configurable cost threshold). | Approval workflow is triggered when asset value exceeds threshold; decommission cannot proceed without an approval record. | BR-10 |
| FR-DECOM-03 | The system SHALL archive all resource and lifecycle records to cold storage with retention metadata before physical disposal. | Archive job completes within 24 h of decommission approval; archive manifest is stored and accessible for compliance audit. | BR-10 |

### Audit and Observability

| ID | Requirement | Acceptance Criteria | Related Rules |
|---|---|---|---|
| FR-AUDIT-01 | The system SHALL record every state-changing command with `actor_id`, `correlation_id`, `reason_code`, `timestamp`, and `before/after state`. | 100 % of state changes have complete audit records queryable within 1 s. | BR-1 |
| FR-AUDIT-02 | The system SHALL expose a compliance report API returning full audit trails for any resource across its entire lifecycle. | Report API returns data within 5 s for any single resource; response includes all transitions, actors, and events. | BR-1 |
| FR-AUDIT-03 | The system SHALL stream all domain events to a SIEM-compatible sink with no loss under normal operation. | Zero event loss under P99 load; event lag to SIEM sink is < 10 s. | BR-5 |

---

## Non-Functional Requirements

| ID | Requirement | Target |
|---|---|---|
| NFR-AVAIL-01 | Platform API availability (provisioning, allocation, checkout, checkin command APIs) | ≥ 99.9 % monthly |
| NFR-LAT-01 | P95 command-path latency (reserve, checkout, checkin) | ≤ 500 ms |
| NFR-LAT-02 | P95 query-path latency (resource search, audit trail) | ≤ 1,000 ms |
| NFR-CONS-01 | Allocation consistency model | Serializable per `(resource_id, window)` pair; no dirty reads |
| NFR-SCALE-01 | Concurrent active allocations per tenant | ≥ 100,000 |
| NFR-SCALE-02 | Resource catalog entries per deployment | ≥ 5,000,000 |
| NFR-DR-01 | Recovery Point Objective (RPO) | ≤ 5 minutes |
| NFR-DR-02 | Recovery Time Objective (RTO) | ≤ 30 minutes |
| NFR-SEC-01 | All data at rest and in transit | AES-256 + TLS 1.3 minimum |
| NFR-RET-01 | Audit log retention | ≥ 7 years (configurable per compliance profile) |
| NFR-OBS-01 | Structured logging coverage | 100 % of all service boundaries |
| NFR-OBS-02 | P99 event-bus consumer lag (overdue detector, settlement worker) | ≤ 60 s |

---

## Exception Handling Requirements

- Every failed command MUST return a structured error body with `error_code`, `correlation_id`, and `retry_after` where applicable.
- Retried operations MUST reuse the original `idempotency_key` to prevent duplicate business effects.
- Compensating transactions MUST be idempotent and auditable.
- DLQ messages MUST include original payload, failure reason, retry count, and first-failure timestamp.
- Every exception type (validation, policy, concurrency, financial, timeout) MUST have a named runbook entry in the operations guide.

---

## Traceability

- Business rule definitions: [../analysis/business-rules.md](../analysis/business-rules.md)
- Use case descriptions: [../analysis/use-case-descriptions.md](../analysis/use-case-descriptions.md)
- API specification: [../detailed-design/api-design.md](../detailed-design/api-design.md)
- Lifecycle state machine: [../detailed-design/state-machine-diagrams.md](../detailed-design/state-machine-diagrams.md)

## Implementation Checklist

- [x] Functional requirements decomposed to testable acceptance criteria
- [x] Non-functional targets specified with numeric bounds
- [x] Exception handling requirements defined
- [ ] Requirements reviewed by engineering, operations, and governance stakeholders
- [ ] Traceability links verified against design artifacts
- [ ] Acceptance tests authored for each FR
