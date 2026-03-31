# Settlement and Incident Resolution

Edge cases covering financial charge failures, duplicate postings, disputed settlements, and reconciliation mismatches in the **Resource Lifecycle Management Platform**.

---

## EC-SET-01: Settlement Event Fails to Deliver to Financial Ledger

**Description**: The `rlmp.settlement.posted` event is published to the event bus, but the Financial Ledger consumer fails to process it. Settlement record stays in `APPROVED` state and journal entry is never created.

| Aspect | Detail |
|---|---|
| **Trigger** | Ledger consumer returns non-200; event moves to DLQ after 5 retries |
| **Detection** | DLQ depth > 0 for `settlement-ledger` topic; alert fires within 5 min; daily reconciliation detects APPROVED settlements with no `ledger_event_id` |
| **Containment** | Settlement charge is frozen (not voided); no duplicate charge risk; outbox pattern ensures exactly-once delivery attempt; DLQ holds the event |
| **Recovery** | SRE investigates Ledger availability; replays DLQ event with original `idempotency_key = settlement_id`; Ledger confirms idempotent receipt; settlement transitions to `POSTED` |
| **Evidence** | DLQ record; Ledger error log; settlement audit trail shows `APPROVED → POSTED` timestamp gap |
| **Owner** | SRE + Finance |
| **SLA** | DLQ alert within 5 min; resolution within 2 h |
| **Prevention** | Outbox uses `settlement_id` as idempotency key; Ledger consumer must be idempotent on this key |

---

## EC-SET-02: Duplicate Settlement Charge

**Description**: A race condition or retry loop causes two settlement records to be created for the same allocation and condition delta.

| Aspect | Detail |
|---|---|
| **Trigger** | Incident resolved event consumed twice (at-least-once delivery); Settlement Service processes twice |
| **Detection** | Duplicate settlement records detected in DB: same `case_id`, same `charge_type`, state = `PENDING` |
| **Containment** | Settlement Service uses `(case_id, charge_type)` unique constraint in DB → second INSERT fails with unique violation; first record is the canonical one |
| **Recovery** | DB constraint prevents duplicate; second attempt returns a conflict error that the consumer handles gracefully (idempotent); no financial impact |
| **Evidence** | Settlement audit log shows single successful INSERT; duplicate attempt logged with `UNIQUE_VIOLATION` |
| **Owner** | Platform Engineering |
| **SLA** | Automated prevention |
| **Prevention** | `UNIQUE(case_id, charge_type)` DB constraint + idempotency check in Settlement Service before INSERT |

---

## EC-SET-03: Settlement Disputed After Approval

**Description**: Finance approves a settlement charge. After posting to the ledger, the custodian discovers the charge and disputes it.

| Aspect | Detail |
|---|---|
| **Trigger** | Custodian submits dispute on a `POSTED` settlement |
| **Detection** | `POST /settlements/{id}/dispute` with state = `POSTED` |
| **Containment** | Dispute is rejected if settlement is already `POSTED` — a credit/reversal must be processed instead; system returns `422 SETTLEMENT_ALREADY_POSTED` with instructions to contact Finance |
| **Recovery** | Finance reviews the dispute; if upheld, Finance creates a reversal credit note in the ledger (outside the platform) and manually voids the settlement record (requires `compliance` role override) |
| **Evidence** | Settlement audit trail; dispute notes; Finance reversal reference; manual override audit entry |
| **Owner** | Finance + Compliance |
| **SLA** | Dispute acknowledged within 1 business day; resolved within 5 business days |

---

## EC-SET-04: Daily Reconciliation Detects Discrepancy

**Description**: The daily reconciliation job identifies that the number of `POSTED` settlement records does not match the number of journal entries in the Financial Ledger.

| Aspect | Detail |
|---|---|
| **Trigger** | Reconciliation job: `COUNT(settlements WHERE state=POSTED AND date=yesterday)` ≠ ledger API response count |
| **Detection** | `rlmp.reconciliation.completed` event with `discrepancy_count > 0`; CRITICAL alert fires immediately |
| **Containment** | Finance is alerted; new settlement postings for affected date range are suspended until investigation completes |
| **Recovery** | SRE cross-references settlement IDs vs ledger journal entry IDs; identifies missing or extra entries; for missing: replay DLQ or manually trigger posting; for extra: create reversal in ledger + void in platform |
| **Evidence** | Reconciliation report with per-settlement discrepancy list; exported CSV for Finance review |
| **Owner** | Finance + SRE |
| **SLA** | Containment within 1 h; resolution within 4 h |

---

## EC-SET-05: Incident SLA Breach Without Resolution

**Description**: An incident case passes its `sla_due_at` without reaching `RESOLVED` or `CLOSED` state.

| Aspect | Detail |
|---|---|
| **Trigger** | `incident.state IN (OPEN, IN_REVIEW)` and `current_time > sla_due_at` |
| **Detection** | Reconciliation job or real-time SLA monitor detects breach; alert to incident owner's manager |
| **Containment** | Severity is auto-escalated one level (e.g., `LOW → MEDIUM`); task re-assigned to manager; resource remains on hold |
| **Recovery** | Manager reviews and either resolves the case or assigns to a more senior resource for urgent action |
| **Evidence** | Audit trail shows SLA breach timestamp and auto-escalation event |
| **Owner** | Resource Manager (primary) → escalation to department head |
| **SLA** | Alert within 5 min of breach; re-assignment within 1 h |

---

## EC-SET-06: Rate Card Version Mismatch

**Description**: An allocation was created under rate card version v1, but by the time settlement is calculated, rate card has been updated to v2 with different damage rates.

| Aspect | Detail |
|---|---|
| **Trigger** | Rate card updated between allocation checkout and incident settlement calculation |
| **Detection** | Settlement Service records `rate_card_id` from the policy profile version **active at time of allocation checkout**, not at time of settlement |
| **Containment** | Settlement amounts are always calculated against the rate card version captured at checkout time (stored in `policy_profile.deposit_rate_card_id` at checkout) |
| **Recovery** | No recovery needed if implementation is correct; settlement is traceable to the exact rate card version |
| **Evidence** | `settlement_record.rate_card_id` matches the `policy_profile.deposit_rate_card_id` from the time of checkout (verifiable via audit trail) |
| **Owner** | Platform Engineering (design-time guarantee) |
| **SLA** | N/A – prevented by design |

---

## Settlement Flow with Failure Recovery

```mermaid
flowchart TD
  A[Incident Resolved] --> B[Settlement Service: Calculate Charge]
  B --> C{DB INSERT settlement\n(case_id, charge_type UNIQUE)}
  C -->|Duplicate| D[Return idempotent response\nNo double-charge]
  C -->|Success| E[Publish rlmp.settlement.calculated]
  E --> F[Finance Reviews]
  F --> G{Finance Decision}
  G -->|Approve| H[UPDATE settlement state=APPROVED\nINSERT outbox]
  H --> I[Outbox Relay → Event Bus → Ledger]
  I --> J{Ledger accepts?}
  J -->|Yes| K[UPDATE state=POSTED + ledger_event_id]
  J -->|No, retry 1-5| I
  J -->|Max retries - DLQ| L[DLQ: SRE Alert]
  L --> M{SRE investigates}
  M -->|Ledger recovered| N[Replay DLQ event with same idempotency_key]
  N --> I
  G -->|Dispute| O[UPDATE settlement state=DISPUTED]
  O --> P{Dispute resolved}
  P -->|Upheld| Q[UPDATE state=VOIDED\nPublish voided event]
  P -->|Rejected| G
```
