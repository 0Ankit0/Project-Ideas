| Property       | Value                                            |
| -------------- | ------------------------------------------------ |
| Document Title | Sequence Diagrams — Legal Case Management System |
| System         | Legal Case Management System                     |
| Version        | 1.0.0                                            |
| Status         | Approved                                         |
| Owner          | Architecture Team                                |
| Last Updated   | 2025-01-15                                       |

# Sequence Diagrams — Legal Case Management System

## Overview

These sequence diagrams document the principal inter-service communication patterns of the Legal Case Management System (LCMS) as deployed by mid-to-large law firms. Each diagram maps the precise sequence of synchronous HTTP calls, asynchronous Kafka events, and data-store interactions that together form a complete end-to-end workflow.

The LCMS decomposes responsibilities across bounded-context services — matter management, billing, court integration, trust accounting, and document management. Services communicate in two modes: synchronous REST calls mediated by Kong API Gateway for request/response workflows that require an immediate confirmation, and asynchronous Kafka events for work that can proceed independently without blocking the originating request. Keycloak issues short-lived JWTs for every service-to-service call, and each service validates the token's signature and claims before processing. Every `POST` request carries a client-supplied `Idempotency-Key` header, and Redis stores the associated response for 24 hours to protect against duplicate submissions on network retry.

Five key workflows are documented in this file:

1. **Matter Intake with Conflict Check** — automated conflict-of-interest screening and engagement letter delivery at matter creation time.
2. **Record and Submit Time Entry** — billable-time capture with billing rule enforcement and automatic submission.
3. **Generate LEDES Invoice** — aggregation of approved time entries into a LEDES 1998B-formatted invoice with partner sign-off.
4. **PACER Court Document Filing** — integration with PACER/CM-ECF for electronic court filing and automated deadline extraction.
5. **Trust Account Disbursement** — IOLTA disbursement with dual-control partner approval, atomic balance update, and immutable audit trail.

---

## 1. Matter Intake with Conflict Check

### Description

When an attorney submits a new matter intake form, the system performs an automated conflict-of-interest check by searching all existing clients, active matters, and their associated adverse parties for name or alias matches against the prospective client and opposing parties. If a potential conflict is detected, the matter record is saved with a `CONFLICT_CHECK` status and returned to the attorney with the full conflict detail so that a supervising partner can conduct a manual review before proceeding. If the conflict check is clear, the matter record is created with `PENDING_ENGAGEMENT` status, a `matter.matter.created` event is published to the Kafka event bus, and both a legal team notification and a DocuSign engagement letter envelope are dispatched asynchronously.

### Sequence Diagram

```mermaid
sequenceDiagram
    actor Attorney
    participant MatterController
    participant MatterService
    participant ConflictCheckService
    participant ClientRepository
    participant MatterRepository
    participant EventBus
    participant NotificationService
    participant DocuSignService

    Attorney->>MatterController: POST /v1/matters (intakePayload)
    activate MatterController
    Note over MatterController: Validates request body schema and<br/>extracts JWT claims (userId, firmId, role)
    MatterController->>MatterService: createMatter(dto)
    activate MatterService

    MatterService->>ConflictCheckService: performCheck(clientName, opposingParties, matterId)
    activate ConflictCheckService
    Note over ConflictCheckService: Searches all active and archived matters<br/>within the firm's tenant scope

    ConflictCheckService->>ClientRepository: findByNameOrAlias(clientName)
    activate ClientRepository
    ClientRepository-->>ConflictCheckService: matchingClients[]
    deactivate ClientRepository

    ConflictCheckService->>MatterRepository: findAdversePartyOverlap(opposingParties)
    activate MatterRepository
    MatterRepository-->>ConflictCheckService: overlappingMatters[]
    deactivate MatterRepository

    ConflictCheckService-->>MatterService: ConflictCheckResult (clear, conflicts[])
    deactivate ConflictCheckService

    alt Conflict detected
        Note over MatterService: At least one adverse party matches<br/>an existing client or active matter
        MatterService->>MatterRepository: save(matter, status=CONFLICT_CHECK)
        activate MatterRepository
        MatterRepository-->>MatterService: savedMatter (id, status)
        deactivate MatterRepository
        MatterService-->>MatterController: MatterResult (status=CONFLICT_CHECK, conflicts[])
        deactivate MatterService
        MatterController-->>Attorney: 202 Accepted — conflict details returned
        deactivate MatterController
    else No conflicts found
        Note over MatterService: Records conflict-clearance timestamp;<br/>sets status = PENDING_ENGAGEMENT
        MatterService->>MatterRepository: save(matter, status=PENDING_ENGAGEMENT)
        activate MatterRepository
        MatterRepository-->>MatterService: savedMatter (id, status)
        deactivate MatterRepository

        MatterService->>EventBus: publish(matter.matter.created, matterPayload)
        activate EventBus

        EventBus->>NotificationService: deliver(matter.matter.created)
        activate NotificationService
        Note over NotificationService: Sends in-app and email alerts to<br/>responsible attorney and paralegal
        NotificationService-->>EventBus: ack
        deactivate NotificationService

        EventBus->>DocuSignService: deliver(matter.matter.created)
        activate DocuSignService
        Note over DocuSignService: Creates engagement letter envelope<br/>and sends to client email address on record
        DocuSignService-->>EventBus: ack
        deactivate DocuSignService
        deactivate EventBus

        MatterService-->>MatterController: createdMatter (id, status, clientId)
        deactivate MatterService
        MatterController-->>Attorney: 201 Created — matter details
        deactivate MatterController
    end
```

### Error Handling

| Scenario                  | HTTP Status    | Error Code                 | Recovery Action                                                         |
| ------------------------- | -------------- | -------------------------- | ----------------------------------------------------------------------- |
| Conflict found            | 202 Accepted   | `CONFLICT_DETECTED`        | Manual review required by supervising partner before matter can proceed |
| Client not found          | 404 Not Found  | `CLIENT_NOT_FOUND`         | Create the client record first via `POST /v1/clients`                   |
| DocuSign delivery failure | 202 Accepted   | `ENGAGEMENT_LETTER_QUEUED` | Kafka consumer retries with exponential back-off up to five attempts    |
| Duplicate matter ref      | 409 Conflict   | `MATTER_REFERENCE_EXISTS`  | Provide a unique matter reference number in the request payload         |

---

## 2. Record and Submit Time Entry

### Description

An attorney or paralegal records billable time against an active matter by submitting hours worked, a narrative description, and UTBMS task and activity codes. The billing rule engine validates the entry against the matter's billing agreement — enforcing minimum time increments, applying any client-specific rate overrides, and checking remaining budget — before the entry is persisted as a draft. When the matter's billing agreement enables automatic submission, the entry advances immediately to `SUBMITTED` status and a `billing.time_entry.submitted` event is published for downstream billing workflows.

### Sequence Diagram

```mermaid
sequenceDiagram
    actor Timekeeper
    participant TimeEntryController
    participant TimeEntryService
    participant MatterService
    participant BillingRuleEngine
    participant TimeEntryRepository
    participant EventBus

    Timekeeper->>TimeEntryController: POST /v1/matters/{matterId}/time-entries
    activate TimeEntryController
    Note over TimeEntryController: Validates DTO fields and<br/>resolves matterId path parameter

    TimeEntryController->>TimeEntryService: createTimeEntry(matterId, dto, userId)
    activate TimeEntryService

    TimeEntryService->>MatterService: getMatter(matterId)
    activate MatterService
    MatterService-->>TimeEntryService: matter (status, billingAgreement)
    deactivate MatterService
    Note over TimeEntryService: Rejects immediately if matter status is not ACTIVE

    TimeEntryService->>BillingRuleEngine: applyRules(dto, matterBillingAgreement)
    activate BillingRuleEngine
    Note over BillingRuleEngine: Enforces 0.1-hour minimum increment,<br/>resolves rate override, validates UTBMS codes

    alt Budget cap warning threshold reached
        BillingRuleEngine-->>TimeEntryService: AdjustedDto (budgetWarning=true, remainingBudget)
        deactivate BillingRuleEngine
        Note over TimeEntryService: Entry saved with BUDGET_WARNING flag;<br/>responsible attorney notified asynchronously
    else Within budget
        BillingRuleEngine-->>TimeEntryService: AdjustedDto (budgetWarning=false)
        deactivate BillingRuleEngine
    end

    TimeEntryService->>TimeEntryRepository: save(timeEntry, status=DRAFT)
    activate TimeEntryRepository
    TimeEntryRepository-->>TimeEntryService: savedEntry (id, status, adjustedHours)
    deactivate TimeEntryRepository

    opt Billable entry and auto-submit enabled on billing agreement
        TimeEntryService->>TimeEntryRepository: updateStatus(entryId, SUBMITTED)
        activate TimeEntryRepository
        TimeEntryRepository-->>TimeEntryService: updated
        deactivate TimeEntryRepository

        TimeEntryService->>EventBus: publish(billing.time_entry.submitted, entryPayload)
        activate EventBus
        EventBus-->>TimeEntryService: ack
        deactivate EventBus
    end

    TimeEntryService-->>TimeEntryController: savedEntry (id, status, adjustedAmount)
    deactivate TimeEntryService
    TimeEntryController-->>Timekeeper: 201 Created — time entry details
    deactivate TimeEntryController
```

### Error Handling

| Scenario              | HTTP Status           | Error Code              | Recovery Action                                                                |
| --------------------- | --------------------- | ----------------------- | ------------------------------------------------------------------------------ |
| Matter not active     | 422 Unprocessable     | `MATTER_NOT_ACTIVE`     | Verify matter status via `GET /v1/matters/{matterId}`; request reopening if needed |
| Invalid UTBMS code    | 400 Bad Request       | `INVALID_UTBMS_CODE`    | Consult the UTBMS code catalogue at `GET /v1/utbms/codes`                      |
| Rate not configured   | 422 Unprocessable     | `RATE_NOT_CONFIGURED`   | Configure a timekeeper rate in the matter billing agreement before recording time |
| Budget cap exceeded   | 422 Unprocessable     | `BUDGET_CAP_EXCEEDED`   | Obtain written client approval for a budget increase before submitting further time |

---

## 3. Generate LEDES Invoice

### Description

A billing coordinator triggers invoice generation for a specific matter and billing period. The system retrieves all approved, unbilled time entries within the period, validates every UTBMS task and activity code against the authoritative catalogue, and assembles the invoice record. The line items are formatted according to the LEDES 1998B specification and the resulting file is stored as a `LedesExport` artefact. Time entries are marked as billed to prevent double-invoicing, the invoice is routed to the billing partner via DocuSign for approval, and a `billing.invoice.generated` event is published to the event bus.

### Sequence Diagram

```mermaid
sequenceDiagram
    actor BillingCoordinator
    participant InvoiceController
    participant InvoiceService
    participant TimeEntryRepository
    participant UtbmsCatalog
    participant LedesFormatter
    participant InvoiceRepository
    participant DocuSignService
    participant EventBus

    BillingCoordinator->>InvoiceController: POST /v1/invoices/generate
    activate InvoiceController
    Note over InvoiceController: Validates matterId, periodStart, periodEnd;<br/>checks BILLING_COORDINATOR role claim

    InvoiceController->>InvoiceService: generateInvoice(matterId, periodStart, periodEnd)
    activate InvoiceService

    InvoiceService->>TimeEntryRepository: findApprovedUnbilled(matterId, periodStart, periodEnd)
    activate TimeEntryRepository
    TimeEntryRepository-->>InvoiceService: timeEntries[]
    deactivate TimeEntryRepository

    alt No approved unbilled time entries found
        InvoiceService-->>InvoiceController: InvoiceError (NO_UNBILLED_TIME)
        deactivate InvoiceService
        InvoiceController-->>BillingCoordinator: 422 Unprocessable — no billable time in period
        deactivate InvoiceController
    else Time entries present
        Note over InvoiceService: Creates Invoice record with status=DRAFT<br/>and assigns the next sequential invoice number

        loop Validate UTBMS codes for each time entry
            InvoiceService->>UtbmsCatalog: validate(taskCode, activityCode)
            activate UtbmsCatalog
            UtbmsCatalog-->>InvoiceService: ValidationResult (valid, description)
            deactivate UtbmsCatalog
        end

        InvoiceService->>LedesFormatter: format(invoice, lineItems, ledesVersion=1998B)
        activate LedesFormatter
        Note over LedesFormatter: Serialises fields per the LEDES 1998B column<br/>specification and validates maximum field widths
        LedesFormatter-->>InvoiceService: ledesFormattedString
        deactivate LedesFormatter

        InvoiceService->>TimeEntryRepository: markAsBilled(entryIds, invoiceId)
        activate TimeEntryRepository
        TimeEntryRepository-->>InvoiceService: updatedCount
        deactivate TimeEntryRepository

        InvoiceService->>InvoiceRepository: save(invoice, ledesExport)
        activate InvoiceRepository
        InvoiceRepository-->>InvoiceService: savedInvoice (id, ledesDownloadUrl)
        deactivate InvoiceRepository

        InvoiceService->>DocuSignService: sendForApproval(invoiceId, partnerEmail)
        activate DocuSignService
        Note over DocuSignService: Attaches LEDES file and invoice PDF;<br/>routes envelope to billing partner for e-signature
        DocuSignService-->>InvoiceService: envelopeId
        deactivate DocuSignService

        InvoiceService->>EventBus: publish(billing.invoice.generated, invoicePayload)
        activate EventBus
        EventBus-->>InvoiceService: ack
        deactivate EventBus

        InvoiceService-->>InvoiceController: invoice (id, status=PENDING_APPROVAL, ledesDownloadUrl)
        deactivate InvoiceService
        InvoiceController-->>BillingCoordinator: 201 Created — invoice details and LEDES download URL
        deactivate InvoiceController
    end
```

### Error Handling

| Scenario                    | HTTP Status           | Error Code              | Recovery Action                                                             |
| --------------------------- | --------------------- | ----------------------- | --------------------------------------------------------------------------- |
| No unbilled time entries    | 422 Unprocessable     | `NO_UNBILLED_TIME`      | Verify that time entries are in APPROVED status for the requested period    |
| Invalid UTBMS code on entry | 422 Unprocessable     | `INVALID_UTBMS_CODE`    | Correct the UTBMS code on the time entry and re-trigger invoice generation  |
| LEDES format error          | 500 Internal Error    | `LEDES_FORMAT_FAILURE`  | Review time entry narratives for non-printable characters; contact support  |
| DocuSign unavailable        | 202 Accepted          | `APPROVAL_QUEUED`       | Invoice stored; DocuSign delivery retried automatically via Kafka consumer  |

---

## 4. PACER Court Document Filing

### Description

An attorney initiates electronic filing of an approved court document through the PACER/CM-ECF integration. The system retrieves the document and validates its approval status before delegating to `PacerIntegrationService`, which authenticates using credentials stored in AWS Secrets Manager and submits the document bytes to the court's CM-ECF endpoint. Upon receiving the court's confirmation — including docket number, filing timestamp, and confirmation number — the service extracts any new deadlines from the Notice of Electronic Filing (NEF), creates corresponding calendar entries, and dispatches a notification to the full legal team. The document status is updated to `FILED` and a `court.document.filed` event is published to the event bus.

### Sequence Diagram

```mermaid
sequenceDiagram
    actor Attorney
    participant DocumentController
    participant DocumentService
    participant PacerIntegrationService
    participant CmEcfClient
    participant DocumentRepository
    participant CalendarService
    participant EventBus
    participant NotificationService

    Attorney->>DocumentController: POST /v1/documents/{docId}/file-with-court
    activate DocumentController
    Note over DocumentController: Validates filing request body;<br/>checks ATTORNEY role claim from JWT

    DocumentController->>DocumentService: fileWithCourt(docId, filingRequest)
    activate DocumentService

    DocumentService->>DocumentRepository: findById(docId)
    activate DocumentRepository
    DocumentRepository-->>DocumentService: document (status, currentVersion, bytes)
    deactivate DocumentRepository
    Note over DocumentService: Rejects with 409 if document status is not APPROVED

    DocumentService->>PacerIntegrationService: submitFiling(document, filingRequest)
    activate PacerIntegrationService
    Note over PacerIntegrationService: Retrieves court-specific PACER credentials<br/>from AWS Secrets Manager before authenticating

    alt PACER authentication fails
        PacerIntegrationService-->>DocumentService: FilingError (PACER_AUTH_FAILED)
        deactivate PacerIntegrationService
        DocumentService-->>DocumentController: FilingError (PACER_AUTH_FAILED)
        deactivate DocumentService
        DocumentController-->>Attorney: 502 Bad Gateway — PACER authentication error
        deactivate DocumentController
    else PACER authenticated successfully
        PacerIntegrationService->>CmEcfClient: submitDocument(documentBytes, caseNumber, filingType)
        activate CmEcfClient

        alt Court system unavailable or timeout
            CmEcfClient-->>PacerIntegrationService: Timeout or 503 error
            deactivate CmEcfClient
            Note over PacerIntegrationService: Schedules retry via Kafka dead-letter<br/>topic with exponential back-off
            PacerIntegrationService-->>DocumentService: FilingError (COURT_UNAVAILABLE, retryScheduled=true)
            deactivate PacerIntegrationService
            DocumentService-->>DocumentController: FilingError (COURT_UNAVAILABLE)
            deactivate DocumentService
            DocumentController-->>Attorney: 202 Accepted — filing queued for automatic retry
            deactivate DocumentController
        else Filing accepted by court
            CmEcfClient-->>PacerIntegrationService: FilingConfirmation (docketNumber, filingTimestamp, confirmationNumber)
            deactivate CmEcfClient
            Note over PacerIntegrationService: Creates CourtFiling record and parses<br/>NEF docket entry for new deadline items

            PacerIntegrationService-->>DocumentService: filingConfirmation
            deactivate PacerIntegrationService

            DocumentService->>DocumentRepository: updateStatus(docId, FILED, docketNumber)
            activate DocumentRepository
            DocumentRepository-->>DocumentService: updated
            deactivate DocumentRepository

            DocumentService->>CalendarService: createDeadlines(extractedDeadlines, matterId)
            activate CalendarService
            Note over CalendarService: Creates COURT_DEADLINE calendar entries<br/>with automated reminder rules applied
            CalendarService-->>DocumentService: createdDeadlines[]
            deactivate CalendarService

            DocumentService->>EventBus: publish(court.document.filed, filingPayload)
            activate EventBus
            EventBus->>NotificationService: deliver(court.document.filed)
            activate NotificationService
            Note over NotificationService: Sends filing confirmation and extracted<br/>deadlines to attorney, paralegal, and matter team
            NotificationService-->>EventBus: ack
            deactivate NotificationService
            deactivate EventBus

            DocumentService-->>DocumentController: CourtFiling (docketNumber, filingTimestamp, confirmationNumber)
            deactivate DocumentService
            DocumentController-->>Attorney: 200 OK — court filing confirmation details
            deactivate DocumentController
        end
    end
```

### Error Handling

| Scenario                         | HTTP Status           | Error Code                  | Recovery Action                                                              |
| -------------------------------- | --------------------- | --------------------------- | ---------------------------------------------------------------------------- |
| PACER authentication failed      | 502 Bad Gateway       | `PACER_AUTH_FAILED`         | Rotate PACER credentials in AWS Secrets Manager and retry                    |
| CM-ECF submission error          | 422 Unprocessable     | `CMECF_SUBMISSION_ERROR`    | Review court-returned error message; correct document metadata and refile    |
| Document not in APPROVED status  | 409 Conflict          | `DOCUMENT_NOT_APPROVED`     | Complete the document approval workflow before initiating a court filing     |
| Court system timeout             | 202 Accepted          | `COURT_SYSTEM_UNAVAILABLE`  | Filing queued in Kafka dead-letter topic; retry scheduled automatically       |

---

## 5. Trust Account Disbursement

### Description

An accounts manager initiates a disbursement from an IOLTA trust account by submitting the payee, amount, and description. The system enforces a dual-control approval workflow: the transaction is created with `PENDING` status and a supervising partner is notified to review and approve via a separate authenticated request. Only after the partner grants approval does the system proceed — atomically deducting the balance with a row-level `FOR UPDATE` lock to prevent concurrent overdrafts, synchronising the transaction to the external accounting system, advancing the transaction to `CLEARED` status, publishing the event, and writing an immutable audit log entry with a cryptographic hash chain.

### Sequence Diagram

```mermaid
sequenceDiagram
    actor AccountsManager
    actor Partner
    participant TrustController
    participant TrustService
    participant ApprovalWorkflow
    participant PartnerNotificationService
    participant TrustRepository
    participant AccountingAdapter
    participant EventBus
    participant AuditLogger

    AccountsManager->>TrustController: POST /v1/trust-accounts/{id}/transactions
    activate TrustController
    Note over TrustController: Validates disbursement request body;<br/>checks ACCOUNTS_MANAGER role claim

    TrustController->>TrustService: initiateDisbursement(trustAccountId, request)
    activate TrustService

    TrustService->>TrustRepository: findById(trustAccountId, FOR UPDATE)
    activate TrustRepository
    TrustRepository-->>TrustService: trustAccount (balance, status)
    deactivate TrustRepository

    alt Insufficient balance or account not ACTIVE
        Note over TrustService: Requested amount exceeds available balance<br/>or account is suspended or closed
        TrustService-->>TrustController: DisbursementError (INSUFFICIENT_BALANCE)
        deactivate TrustService
        TrustController-->>AccountsManager: 422 Unprocessable — insufficient funds
        deactivate TrustController
    else Sufficient balance and account ACTIVE
        Note over TrustService: Validates amount is greater than zero;<br/>creates TrustTransaction with status=PENDING

        TrustService->>TrustRepository: save(transaction, status=PENDING)
        activate TrustRepository
        TrustRepository-->>TrustService: pendingTransaction (id, status)
        deactivate TrustRepository

        TrustService->>ApprovalWorkflow: requestApproval(transactionId, requiredApproverRole=PARTNER)
        activate ApprovalWorkflow
        ApprovalWorkflow->>PartnerNotificationService: notifyForApproval(partnerUsers, transactionId)
        activate PartnerNotificationService
        Note over PartnerNotificationService: Sends approval request to all partners<br/>with PARTNER role within the firm
        PartnerNotificationService-->>ApprovalWorkflow: notified
        deactivate PartnerNotificationService
        ApprovalWorkflow-->>TrustService: approvalRequestId
        deactivate ApprovalWorkflow

        TrustService-->>TrustController: pendingTransaction (id, status=PENDING, approvalRequestId)
        deactivate TrustService
        TrustController-->>AccountsManager: 202 Accepted — awaiting partner approval
        deactivate TrustController

        Note over Partner: Partner reviews transaction details<br/>and submits decision via approval endpoint

        Partner->>TrustController: POST /v1/approvals/{transactionId}/approve
        activate TrustController
        TrustController->>ApprovalWorkflow: approve(transactionId, partnerUserId)
        activate ApprovalWorkflow

        alt Approval rejected by partner
            ApprovalWorkflow-->>TrustController: ApprovalResult (rejected, reason)
            deactivate ApprovalWorkflow
            TrustController->>TrustService: rejectDisbursement(transactionId)
            activate TrustService
            TrustService->>TrustRepository: updateStatus(transactionId, REJECTED)
            activate TrustRepository
            TrustRepository-->>TrustService: updated
            deactivate TrustRepository
            TrustService-->>TrustController: rejectedTransaction (id, status=REJECTED)
            deactivate TrustService
            TrustController-->>Partner: 200 OK — disbursement rejected
            deactivate TrustController
        else Approval granted by partner
            ApprovalWorkflow-->>TrustController: ApprovalResult (approved)
            deactivate ApprovalWorkflow

            TrustController->>TrustService: processDisbursement(transactionId)
            activate TrustService

            TrustService->>TrustRepository: updateBalance(trustAccountId, debitAmount)
            activate TrustRepository
            Note over TrustRepository: Atomic UPDATE WHERE balance >= amount<br/>prevents overdraft under concurrent load
            TrustRepository-->>TrustService: updatedBalance
            deactivate TrustRepository

            TrustService->>AccountingAdapter: postTransaction(transaction)
            activate AccountingAdapter
            Note over AccountingAdapter: Synchronises to external accounting system<br/>via REST; retries on transient errors
            AccountingAdapter-->>TrustService: accountingRef
            deactivate AccountingAdapter

            TrustService->>TrustRepository: updateStatus(transactionId, CLEARED)
            activate TrustRepository
            TrustRepository-->>TrustService: clearedTransaction
            deactivate TrustRepository

            TrustService->>EventBus: publish(trust.disbursement.completed, transactionPayload)
            activate EventBus
            EventBus-->>TrustService: ack
            deactivate EventBus

            TrustService->>AuditLogger: log(disbursementAuditRecord)
            activate AuditLogger
            Note over AuditLogger: Writes immutable entry to append-only<br/>audit_log table with SHA-256 hash chain
            AuditLogger-->>TrustService: auditEntryId
            deactivate AuditLogger

            TrustService-->>TrustController: clearedTransaction (id, status=CLEARED, accountingRef)
            deactivate TrustService
            TrustController-->>Partner: 200 OK — disbursement cleared
            deactivate TrustController
        end
    end
```

### Error Handling

| Scenario                        | HTTP Status           | Error Code                   | Recovery Action                                                                 |
| ------------------------------- | --------------------- | ---------------------------- | ------------------------------------------------------------------------------- |
| Insufficient balance            | 422 Unprocessable     | `INSUFFICIENT_BALANCE`       | Verify current balance via `GET /v1/trust-accounts/{id}/balance`                |
| Approval rejected               | 200 OK                | `DISBURSEMENT_REJECTED`      | Resubmit with corrected details after consulting with the approving partner      |
| Accounting system sync failure  | 500 Internal Error    | `ACCOUNTING_SYNC_FAILED`     | Transaction held in `PENDING_ACCOUNTING` status; ops team alerted via PagerDuty |
| Concurrent disbursement attempt | 409 Conflict          | `ACCOUNT_LOCKED`             | Account row is locked by an in-progress transaction; retry after completion      |

---

## Common Patterns and Conventions

### Authentication and Authorisation

All service-to-service calls within the LCMS cluster carry an internal JWT issued by Keycloak. When a client request arrives at Kong API Gateway, Kong validates the client-facing access token and attaches a signed internal service token to the forwarded request. Each downstream service verifies the internal token's signature against the Keycloak public key and inspects the `role`, `firmId`, and `sub` claims before processing any operation. Requests that lack a valid internal JWT are rejected with `401 Unauthorized` at the receiving service boundary, even when they originate from within the cluster.

Role claims gate both coarse-grained route access (enforced by Kong plugins) and fine-grained business logic (enforced inside each service). For example, only principals holding the `BILLING_COORDINATOR` role may trigger invoice generation, and only principals holding the `PARTNER` role may approve trust disbursements.

### Kafka Topic Naming Convention

All asynchronous events follow the three-segment naming scheme `{domain}.{entity}.{event}`. The domain segment groups topics by bounded context, making it straightforward to assign consumer groups and configure topic-level ACLs in isolation.

| Domain    | Entity          | Event       | Full Topic Name                   |
| --------- | --------------- | ----------- | --------------------------------- |
| `matter`  | `matter`        | `created`   | `matter.matter.created`           |
| `billing` | `time_entry`    | `submitted` | `billing.time_entry.submitted`    |
| `billing` | `invoice`       | `generated` | `billing.invoice.generated`       |
| `court`   | `document`      | `filed`     | `court.document.filed`            |
| `court`   | `deadline`      | `created`   | `court.deadline.created`          |
| `trust`   | `disbursement`  | `completed` | `trust.disbursement.completed`    |

Consumer groups are named `{serviceName}-{topicName}-consumer` to ensure independent offset tracking per consumer and to allow replaying events from a known offset during incident recovery.

### Idempotency

Every `POST` request to the LCMS API must include an `Idempotency-Key` header containing a client-generated UUID v4. Kong API Gateway stores the key together with the serialised response in Redis using a 24-hour TTL. If the gateway receives a second request carrying the same key within the TTL window, it returns the cached response immediately without forwarding the request to the upstream service. This pattern is essential for critical flows — trust disbursements, invoice generation, and court filings — where a network-layer retry must never produce a duplicate record or financial transaction.

### Optimistic and Pessimistic Locking

Read-heavy, low-contention flows use PostgreSQL optimistic locking via a `version` column (incremented on every write). If two writers read the same version and both attempt to commit, the losing writer receives a `409 Conflict` and is expected to re-fetch and retry. High-stakes financial writes — specifically trust account balance updates — use PostgreSQL `SELECT ... FOR UPDATE` (pessimistic locking) because the cost of a race condition outweighs the throughput penalty of holding a row lock. The trade-off is deliberate: financial correctness takes precedence over concurrency.

### Saga Pattern for Distributed Transactions

Workflows that span multiple services — invoice generation (which must atomically mark time entries as billed and persist the LEDES export), and court filing (which must update document status and create calendar entries as a single logical unit) — are implemented as choreography-based sagas. Each participating service listens for a trigger event, performs its local transaction, and emits a success or failure event. Compensating transactions subscribe to failure events and roll back their local changes. The Kafka event log provides the durable, ordered record that makes saga state recoverable after any partial failure, and the `Idempotency-Key` on each compensation ensures compensating actions are also idempotent.

### Dead-Letter and Retry Strategy

Failed Kafka consumer deliveries are routed to a dead-letter topic named `{originalTopic}.dlq`. A dedicated retry consumer reads from each DLQ and republishes messages with an exponential back-off schedule: 5 seconds, 30 seconds, 2 minutes, 10 minutes, and 1 hour. After five consecutive failed retries the message is moved to a poison topic named `{originalTopic}.poison` and a PagerDuty alert is raised for manual investigation. The original message offset, consumer group, and exception stack trace are attached as Kafka message headers to aid diagnosis.
