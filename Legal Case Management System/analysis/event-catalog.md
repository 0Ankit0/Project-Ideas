# Event Catalog — Legal Case Management System

This catalog is the authoritative reference for all domain events in the Legal Case Management
System. Every event represents an immutable fact. Producers guarantee at-least-once delivery;
consumers must be idempotent. All events are versioned and schema-validated at publish time.

---

## Contract Conventions

### Envelope Schema

Every event is wrapped in a standard envelope before being placed on the event bus, providing
routing, tracing, and schema-validation metadata.

```json
{
  "specVersion": "1.0",
  "eventId":     "<UUID v4>",
  "eventName":   "<DomainEvent>",
  "eventVersion": "1.0",
  "domain":      "<domain-slug>",
  "producedBy":  "<service-name>",
  "producedAt":  "<ISO-8601 UTC>",
  "correlationId": "<UUID v4>",
  "causationId": "<UUID v4 — ID of the command that caused this event>",
  "matterId":    "<UUID | null>",
  "tenantId":    "<UUID — law firm identifier for multi-tenant routing>",
  "payload":     { /* event-specific fields — see Domain Events section */ }
}
```

### Versioning Policy

| Rule | Detail |
|------|--------|
| **Semantic versioning** | `MAJOR.MINOR` — breaking payload changes bump MAJOR; additive changes bump MINOR |
| **Backward compatibility** | Consumers must tolerate unknown fields (additive changes are non-breaking) |
| **Breaking change process** | New MAJOR version published in parallel; old version deprecated with 90-day sunset; sunset date published in `eventDeprecations` registry |
| **Schema registry** | All schemas validated against the firm's Confluent Schema Registry or equivalent at publish time; invalid events are sent to a dead-letter topic |

### Delivery Guarantees and Ordering

- **Delivery**: At-least-once; consumers must implement idempotency keyed on `eventId`
- **Ordering**: Per-matter ordering guaranteed within the `matter.<matterId>` partition key
- **Dead-letter**: Events failing after 3 retries (backoff: 1s, 4s, 16s) are moved to `<topic>.dlq`
- **Event bus**: Apache Kafka; topic convention: `lcms.<domain>.<event-name-kebab-case>`

### Retention Policy Summary

| Retention Class | Duration | Examples |
|-----------------|----------|---------|
| `PERMANENT` | Indefinite | Trust transactions, privilege classifications, conflict checks |
| `MATTER_LIFETIME_PLUS_7Y` | Life of matter + 7 years | All matter-lifecycle events |
| `OPERATIONAL_90D` | 90 days | Deadline approaching reminders, notification acks |

### SLO Definitions

| Tier | P99 Publish Latency | Consumer Lag SLO | Alert Threshold |
|------|---------------------|------------------|-----------------|
| `CRITICAL` | < 500 ms | < 2 s | Immediate PagerDuty |
| `HIGH` | < 2 s | < 10 s | Slack + on-call |
| `STANDARD` | < 10 s | < 60 s | Slack channel |

---

## Domain Events

### MatterOpened

| Field | Detail |
|-------|--------|
| **Event Name** | `MatterOpened` |
| **Domain** | `matter-management` |
| **Version** | `1.0` |
| **Producer** | `matter-service` |
| **Consumers** | `conflict-check-service`, `billing-service` (rate initialization), `calendar-service` (SoL deadline seeding), `document-service` (folder scaffolding), `client-portal-service` (portal provisioning), `notification-service` |
| **Trigger Condition** | A matter has passed all pre-creation validations (conflict check cleared, responsible attorney assigned, client record exists) and been persisted with `status = OPEN` |
| **Retention** | `MATTER_LIFETIME_PLUS_7Y` |
| **SLO** | `CRITICAL` — downstream services must receive and process within 2 s to unblock attorney workflow |

**Payload Schema:**

```json
{
  "matterId":           "UUID",
  "matterNumber":       "string — firm-formatted, e.g. 2025-LIT-00142",
  "matterType":         "string — LITIGATION | TRANSACTIONAL | REGULATORY | ADVISORY",
  "practiceArea":       "string — e.g. EMPLOYMENT, REAL_ESTATE, CORPORATE",
  "clientId":           "UUID",
  "clientName":         "string",
  "responsibleAttorneyId": "UUID",
  "billingPartnerId":   "UUID",
  "jurisdiction":       "string — ISO 3166-2 subdivision code",
  "openedAt":           "ISO-8601 UTC",
  "feeArrangement":     "string — HOURLY | FLAT_FEE | CONTINGENCY | HYBRID",
  "estimatedValue":     "decimal | null",
  "conflictCheckId":    "UUID — reference to cleared conflict check record",
  "retainerAmount":     "decimal | null — initial trust deposit if applicable"
}
```

---

### ConflictCheckPassed

| Field | Detail |
|-------|--------|
| **Event Name** | `ConflictCheckPassed` |
| **Domain** | `conflict-management` |
| **Version** | `1.0` |
| **Producer** | `conflict-check-service` |
| **Consumers** | `matter-service` (gates matter-open progression), `audit-service`, `notification-service` (intake coordinator confirmation) |
| **Trigger Condition** | A conflict check run completes with result `CLEARED`; or a `POTENTIAL_CONFLICT` result receives attorney sign-off; or a `CONFLICT` result receives a Managing Partner waiver |
| **Retention** | `PERMANENT` — bar disciplinary record |
| **SLO** | `CRITICAL` — matter creation is blocked until this event is consumed by `matter-service` |

**Payload Schema:**

```json
{
  "conflictCheckId":    "UUID",
  "matterId":           "UUID — prospective matter being opened",
  "clientId":           "UUID",
  "partiesChecked":     [
    {
      "partyName":      "string",
      "partyRole":      "string — CLIENT | ADVERSE | WITNESS | RELATED_ENTITY",
      "taxId":          "string | null",
      "matchResult":    "string — NO_MATCH | FUZZY_MATCH | EXACT_MATCH"
    }
  ],
  "checkResult":        "string — CLEARED | POTENTIAL_CONFLICT_WAIVED",
  "waiverId":           "UUID | null — populated if waiver was required",
  "waiverGrantedBy":    "UUID | null — Managing Partner actor ID",
  "reviewedBy":         "UUID — attorney who reviewed and signed off",
  "checkedAt":          "ISO-8601 UTC",
  "searchEngineVersion": "string — e.g. 2.4.1"
}
```

---

### DocumentFiled

| Field | Detail |
|-------|--------|
| **Event Name** | `DocumentFiled` |
| **Domain** | `document-management` |
| **Version** | `1.1` |
| **Producer** | `document-service` |
| **Consumers** | `privilege-classification-service` (blocks access if `UNCLASSIFIED`), `privilege-log-service` (auto-update log for `PRIVILEGED`/`WORK_PRODUCT`), `search-index-service`, `audit-service`, `client-portal-service` (publish `PUBLIC` docs to portal) |
| **Trigger Condition** | A document or document version is successfully persisted to object storage and its metadata record committed to the database |
| **Retention** | `MATTER_LIFETIME_PLUS_7Y` |
| **SLO** | `HIGH` |

**Payload Schema:**

```json
{
  "documentId":         "UUID",
  "versionId":          "UUID",
  "versionNumber":      "integer — 1-based",
  "matterId":           "UUID",
  "clientId":           "UUID",
  "fileName":           "string",
  "mimeType":           "string",
  "fileSizeBytes":      "integer",
  "storageKey":         "string — object storage path (not a public URL)",
  "uploadedBy":         "UUID — actor ID",
  "uploadedAt":         "ISO-8601 UTC",
  "privilegeClassification": "string — PRIVILEGED | WORK_PRODUCT | CONFIDENTIAL | PUBLIC | UNCLASSIFIED",
  "classifiedBy":       "UUID | null — null if auto-classified or pending",
  "documentCategory":   "string — PLEADING | CONTRACT | CORRESPONDENCE | EVIDENCE | BILLING | OTHER",
  "tags":               ["string"],
  "sourceSystem":       "string — UPLOAD | EMAIL_IMPORT | COURT_EFILING | SCAN"
}
```

---

### TimeEntryRecorded

| Field | Detail |
|-------|--------|
| **Event Name** | `TimeEntryRecorded` |
| **Domain** | `billing` |
| **Version** | `1.0` |
| **Producer** | `time-billing-service` |
| **Consumers** | `invoice-service` (accumulates unbilled time), `matter-service` (updates matter WIP balance), `reporting-service` (utilization metrics), `audit-service` |
| **Trigger Condition** | A time entry passes UTBMS code validation, billing rate resolution (BR-002), and is committed with `status = RECORDED` |
| **Retention** | `MATTER_LIFETIME_PLUS_7Y` |
| **SLO** | `STANDARD` |

**Payload Schema:**

```json
{
  "timeEntryId":        "UUID",
  "matterId":           "UUID",
  "clientId":           "UUID",
  "timekeeperId":       "UUID",
  "timekeeperRole":     "string — PARTNER | SENIOR_ASSOCIATE | ASSOCIATE | PARALEGAL | LAW_CLERK",
  "workDate":           "date — YYYY-MM-DD",
  "hoursWorked":        "decimal — to 2 decimal places (tenths of an hour minimum)",
  "narrative":          "string — description of work performed",
  "utbmsTaskCode":      "string — e.g. L110, L120, L210",
  "utbmsActivityCode":  "string — e.g. A101, A102, A103",
  "resolvedRate":       "decimal — hourly rate in USD applied per BR-002",
  "resolvedRateSource": "string — MATTER_OVERRIDE | CLIENT_OVERRIDE | ROLE_DEFAULT | FIRM_DEFAULT",
  "billedAmount":       "decimal — hoursWorked × resolvedRate",
  "billable":           "boolean",
  "invoiceId":          "UUID | null — populated once billed",
  "recordedAt":         "ISO-8601 UTC"
}
```

---

### InvoiceGenerated

| Field | Detail |
|-------|--------|
| **Event Name** | `InvoiceGenerated` |
| **Domain** | `billing` |
| **Version** | `1.0` |
| **Producer** | `invoice-service` |
| **Consumers** | `approval-workflow-service` (BR-007 routing), `trust-accounting-service` (check retainer coverage), `client-portal-service` (surface invoice to client), `notification-service`, `reporting-service` |
| **Trigger Condition** | An invoice covering one or more time entries and/or expenses is assembled, passes LEDES 98B format validation, and is persisted with `status = PENDING_APPROVAL` |
| **Retention** | `MATTER_LIFETIME_PLUS_7Y` |
| **SLO** | `HIGH` |

**Payload Schema:**

```json
{
  "invoiceId":          "UUID",
  "invoiceNumber":      "string — firm-formatted, e.g. INV-2025-004821",
  "matterId":           "UUID",
  "clientId":           "UUID",
  "billingPartnerId":   "UUID",
  "billingPeriodStart": "date",
  "billingPeriodEnd":   "date",
  "timeEntryIds":       ["UUID"],
  "expenseIds":         ["UUID"],
  "feesSubtotal":       "decimal",
  "expensesSubtotal":   "decimal",
  "adjustments":        "decimal — write-ups or write-downs",
  "taxAmount":          "decimal",
  "totalDue":           "decimal",
  "currency":           "string — ISO 4217, e.g. USD",
  "ledesFormat":        "string — LEDES_98B | LEDES_2000",
  "approvalThreshold":  "decimal — configured threshold at time of generation",
  "requiresApproval":   "boolean — totalDue > approvalThreshold",
  "generatedAt":        "ISO-8601 UTC",
  "dueDate":            "date"
}
```

---

### PaymentReceived

| Field | Detail |
|-------|--------|
| **Event Name** | `PaymentReceived` |
| **Domain** | `billing` |
| **Version** | `1.0` |
| **Producer** | `payment-service` |
| **Consumers** | `invoice-service` (marks invoice PAID or partially paid), `trust-accounting-service` (post to client trust ledger if trust payment), `reporting-service`, `notification-service` (receipt to client), `audit-service` |
| **Trigger Condition** | A payment is confirmed by the payment processor or manually posted by a billing administrator, and the transaction is committed |
| **Retention** | `PERMANENT` — financial record |
| **SLO** | `CRITICAL` — trust accounting must update synchronously |

**Payload Schema:**

```json
{
  "paymentId":          "UUID",
  "invoiceId":          "UUID | null — null for trust retainer deposits",
  "matterId":           "UUID",
  "clientId":           "UUID",
  "paymentType":        "string — OPERATING | TRUST_RETAINER | TRUST_REPLENISHMENT",
  "paymentMethod":      "string — ACH | WIRE | CHECK | CREDIT_CARD | CASH",
  "amount":             "decimal",
  "currency":           "string — ISO 4217",
  "checkNumber":        "string | null",
  "bankReference":      "string | null — ACH trace number or wire ref",
  "postedBy":           "UUID — actor ID (system or human)",
  "receivedAt":         "date — date funds were received",
  "postedAt":           "ISO-8601 UTC",
  "trustLedgerEntryId": "UUID | null — populated for trust payments",
  "appliedToBalance":   "decimal | null — amount applied to outstanding invoice balance"
}
```

---

### CourtDeadlineApproaching

| Field | Detail |
|-------|--------|
| **Event Name** | `CourtDeadlineApproaching` |
| **Domain** | `calendar-deadlines` |
| **Version** | `1.0` |
| **Producer** | `calendar-service` (scheduled job, runs hourly) |
| **Consumers** | `escalation-service` (BR-006 logic), `notification-service` (attorney/partner alerts), `matter-service` (update `escalationLevel`), `audit-service` |
| **Trigger Condition** | A scheduled job evaluates all open `CourtDeadline` records and emits this event when `hoursUntilDue` crosses a threshold: 720 h (30 d), 336 h (14 d), 168 h (7 d), 48 h, 24 h, 2 h. One event per threshold crossing per deadline |
| **Retention** | `OPERATIONAL_90D` |
| **SLO** | `CRITICAL` — malpractice risk; 48-h and 24-h events must be processed within 500 ms |

**Payload Schema:**

```json
{
  "courtDeadlineId":    "UUID",
  "matterId":           "UUID",
  "clientId":           "UUID",
  "responsibleAttorneyId": "UUID",
  "responsiblePartnerId":  "UUID",
  "deadlineType":       "string — STATUTE_OF_LIMITATIONS | FILING_DEADLINE | RESPONSE_DEADLINE | DISCOVERY_CUTOFF | TRIAL_DATE | HEARING",
  "deadlineLabel":      "string — human-readable description",
  "dueDateTime":        "ISO-8601 UTC",
  "hoursUntilDue":      "decimal",
  "thresholdTriggered": "integer — 720 | 336 | 168 | 48 | 24 | 2",
  "currentEscalationLevel": "string — NONE | ATTORNEY | PARTNER | ALL_PARTNERS",
  "deadlineStatus":     "string — OPEN | ACKNOWLEDGED | IN_PROGRESS",
  "courtName":          "string | null",
  "caseNumber":         "string | null",
  "jurisdiction":       "string — ISO 3166-2",
  "emittedAt":          "ISO-8601 UTC"
}
```

---

### MatterClosed

| Field | Detail |
|-------|--------|
| **Event Name** | `MatterClosed` |
| **Domain** | `matter-management` |
| **Version** | `1.0` |
| **Producer** | `matter-service` |
| **Consumers** | `billing-service` (freeze billing; final WIP report), `trust-accounting-service` (confirm zero balance; archive ledger), `document-service` (lock documents; initiate retention schedule), `calendar-service` (close all deadlines), `client-portal-service` (revoke access), `reporting-service` (matter profitability report), `audit-service`, `notification-service` (close notice to client) |
| **Trigger Condition** | All eight BR-008 close criteria have been satisfied (or explicitly overridden by Managing Partner) and the matter `status` transitions to `CLOSED` |
| **Retention** | `PERMANENT` |
| **SLO** | `HIGH` — downstream services must lock the matter before any new write is attempted |

**Payload Schema:**

```json
{
  "matterId":           "UUID",
  "matterNumber":       "string",
  "clientId":           "UUID",
  "closedBy":           "UUID — actor ID",
  "closedAt":           "ISO-8601 UTC",
  "closeType":          "string — NORMAL | FORCE_CLOSE",
  "checklistResults": {
    "allTasksComplete":           "boolean",
    "trustBalanceZero":           "boolean",
    "finalInvoiceIssued":         "boolean",
    "documentsArchivedAndClassified": "boolean",
    "noOpenCourtDeadlines":       "boolean",
    "conflictCheckPresent":       "boolean",
    "clientPortalRevoked":        "boolean",
    "fileRetentionNoticeSent":    "boolean"
  },
  "forceCloseExceptions": [
    {
      "criterion":     "string",
      "justification": "string",
      "authorizedBy":  "UUID"
    }
  ],
  "totalFeesBilled":    "decimal",
  "totalFeesCollected": "decimal",
  "totalHoursWorked":   "decimal",
  "matterOpenedAt":     "ISO-8601 UTC",
  "retentionSchedule":  "string — e.g. DESTROY_AFTER_2032-01-01"
}
```

---

## Publish and Consumption Sequence

```mermaid
sequenceDiagram
    actor Attorney
    participant MatterSvc as matter-service
    participant ConflictSvc as conflict-check-service
    participant BillingSvc as time-billing-service
    participant InvoiceSvc as invoice-service
    participant ApprovalSvc as approval-workflow-service
    participant PaymentSvc as payment-service
    participant TrustSvc as trust-accounting-service
    participant DocSvc as document-service
    participant CalendarSvc as calendar-service
    participant EscalationSvc as escalation-service
    participant PortalSvc as client-portal-service
    participant NotifySvc as notification-service
    participant AuditSvc as audit-service

    Attorney->>MatterSvc: MatterOpenRequest (parties, type, jurisdiction)
    MatterSvc->>ConflictSvc: Run conflict check
    ConflictSvc-->>MatterSvc: ✔ ConflictCheckPassed [v1.0]
    ConflictSvc-->>AuditSvc: ConflictCheckPassed (permanent retention)

    MatterSvc-->>BillingSvc: MatterOpened [v1.0] — initialize rates (BR-002)
    MatterSvc-->>CalendarSvc: MatterOpened [v1.0] — seed SoL deadline (BR-003)
    MatterSvc-->>DocSvc: MatterOpened [v1.0] — scaffold folder structure
    MatterSvc-->>PortalSvc: MatterOpened [v1.0] — provision client portal
    MatterSvc-->>NotifySvc: MatterOpened [v1.0] — notify intake coordinator
    MatterSvc-->>AuditSvc: MatterOpened [v1.0]

    Attorney->>DocSvc: Upload pleading (UNCLASSIFIED)
    DocSvc-->>AuditSvc: DocumentFiled [v1.1]
    DocSvc-->>NotifySvc: DocumentFiled — classify reminder (UNCLASSIFIED)
    Attorney->>DocSvc: Classify as PRIVILEGED
    DocSvc-->>AuditSvc: DocumentFiled [v1.1] — privilege log updated

    Attorney->>BillingSvc: Submit time entry (3.5 hrs, L210/A101)
    BillingSvc->>BillingSvc: Resolve rate via BR-002 hierarchy
    BillingSvc-->>InvoiceSvc: TimeEntryRecorded [v1.0] — add to WIP
    BillingSvc-->>AuditSvc: TimeEntryRecorded [v1.0]

    InvoiceSvc->>InvoiceSvc: Assemble invoice; validate LEDES 98B
    InvoiceSvc-->>ApprovalSvc: InvoiceGenerated [v1.0] — route per BR-007
    InvoiceSvc-->>TrustSvc: InvoiceGenerated [v1.0] — check retainer coverage
    InvoiceSvc-->>AuditSvc: InvoiceGenerated [v1.0]

    ApprovalSvc->>ApprovalSvc: totalDue > threshold → route to Billing Partner
    ApprovalSvc-->>NotifySvc: Invoice approval request sent to partner
    ApprovalSvc-->>PortalSvc: InvoiceGenerated — publish to client portal (after approval)

    PaymentSvc-->>InvoiceSvc: PaymentReceived [v1.0] — mark invoice PAID
    PaymentSvc-->>TrustSvc: PaymentReceived [v1.0] — post to trust ledger
    PaymentSvc-->>NotifySvc: PaymentReceived [v1.0] — send receipt to client
    PaymentSvc-->>AuditSvc: PaymentReceived [v1.0] (permanent retention)

    CalendarSvc-->>EscalationSvc: CourtDeadlineApproaching [v1.0] thresholdTriggered=48
    EscalationSvc-->>NotifySvc: Alert responsible attorney (BR-006 Level 1)
    EscalationSvc-->>MatterSvc: Update escalationLevel = ATTORNEY
    EscalationSvc-->>AuditSvc: Escalation event recorded

    CalendarSvc-->>EscalationSvc: CourtDeadlineApproaching [v1.0] thresholdTriggered=24
    EscalationSvc-->>NotifySvc: Alert responsible partner (BR-006 Level 2)
    EscalationSvc-->>MatterSvc: Update escalationLevel = PARTNER, set MalpracticeRiskFlag

    Attorney->>MatterSvc: MatterCloseRequest
    MatterSvc->>MatterSvc: Run BR-008 checklist (all 8 criteria)
    MatterSvc-->>BillingSvc: MatterClosed [v1.0] — freeze billing
    MatterSvc-->>TrustSvc: MatterClosed [v1.0] — confirm zero balance, archive ledger
    MatterSvc-->>DocSvc: MatterClosed [v1.0] — lock documents, start retention schedule
    MatterSvc-->>CalendarSvc: MatterClosed [v1.0] — close all open deadlines
    MatterSvc-->>PortalSvc: MatterClosed [v1.0] — revoke client access
    MatterSvc-->>NotifySvc: MatterClosed [v1.0] — close notice to client
    MatterSvc-->>AuditSvc: MatterClosed [v1.0] (permanent retention)
```

## Operational SLOs

### Per-Event SLO Table

| Event | Topic | Tier | P99 Publish Latency | Consumer Lag SLO | Retention | Alert |
|-------|-------|------|---------------------|------------------|-----------|-------|
| `MatterOpened` | `lcms.matter-management.matter-opened` | CRITICAL | < 500 ms | < 2 s | Matter + 7 yr | PagerDuty |
| `ConflictCheckPassed` | `lcms.conflict-management.conflict-check-passed` | CRITICAL | < 500 ms | < 2 s | Permanent | PagerDuty |
| `DocumentFiled` | `lcms.document-management.document-filed` | HIGH | < 2 s | < 10 s | Matter + 7 yr | Slack + on-call |
| `TimeEntryRecorded` | `lcms.billing.time-entry-recorded` | STANDARD | < 10 s | < 60 s | Matter + 7 yr | Slack |
| `InvoiceGenerated` | `lcms.billing.invoice-generated` | HIGH | < 2 s | < 10 s | Matter + 7 yr | Slack + on-call |
| `PaymentReceived` | `lcms.billing.payment-received` | CRITICAL | < 500 ms | < 2 s | Permanent | PagerDuty |
| `CourtDeadlineApproaching` | `lcms.calendar-deadlines.court-deadline-approaching` | CRITICAL | < 500 ms | < 2 s | 90 days | PagerDuty |
| `MatterClosed` | `lcms.matter-management.matter-closed` | HIGH | < 2 s | < 10 s | Permanent | Slack + on-call |

### Dead-Letter Queue Policy

| Step | Policy |
|------|--------|
| Retry 1 | 1 second after initial failure |
| Retry 2 | 4 seconds after Retry 1 |
| Retry 3 | 16 seconds after Retry 2 |
| DLQ move | After 3 failed retries, message routed to `.dlq` topic |
| DLQ alert | Ops alert fired within 60 seconds of first DLQ arrival |
| DLQ reprocessing | Manual trigger via ops runbook; automated replay for STANDARD-tier only |
| CRITICAL DLQ | Requires on-call engineer acknowledgment before replay |

### Idempotency Requirements

On receipt, check `processed_events(eventId)`; if present, discard; if not, process and insert
`eventId` atomically in the same transaction. Keys retained ≥ 7 days.

### Consumer Health

Consumers expose `/health/events` reporting `currentLag`, `dlqDepth`, and `status`
(`HEALTHY` | `DEGRADED` | `CRITICAL`). `DEGRADED` when lag exceeds 2× SLO; `CRITICAL` when lag
exceeds 5× SLO or DLQ depth > 10. `CRITICAL` status triggers immediate PagerDuty regardless of
event tier.
