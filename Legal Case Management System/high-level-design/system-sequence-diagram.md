# System Sequence Diagrams — Legal Case Management System

| Field   | Value                                     |
|---------|-------------------------------------------|
| Version | 1.0.0                                     |
| Status  | Approved                                  |
| Date    | 2025-01-15                                |
| Owner   | Architecture & Engineering, LCMS Program  |

---

## Overview

This document captures the primary cross-system interaction sequences for the Legal Case Management System (LCMS). Each diagram models the message exchange between actors, internal microservices, and external systems for a key business workflow. Diagrams follow UML sequence diagram conventions rendered in Mermaid and are supplemented with numbered step-by-step explanations.

The flows documented here represent the highest-stakes business operations in a mid-to-large law firm: opening a new matter (with mandatory conflict screening), electronically filing with federal courts via PACER/CM-ECF, generating LEDES-formatted invoices and collecting payments, and disbursing funds from an IOLTA trust account. Together these four flows exercise every major microservice and all three external integration points.

---

## 1. Matter Intake with Conflict Check

### 1.1 Diagram

```mermaid
sequenceDiagram
    autonumber
    actor Client
    participant Portal       as Client Portal<br/>(React SPA)
    participant Gateway      as Kong API Gateway
    participant Auth         as Keycloak / Auth Service
    participant MatterSvc    as Matter Service
    participant ClientSvc    as Client Service
    participant ConflictSvc  as Conflict Check Service
    participant BarDB         as State Bar Database<br/>(External)
    participant OFAC          as OFAC Screening<br/>(External)
    participant DocuSign      as DocuSign API<br/>(External)
    participant BillingSvc   as Billing Service
    participant Kafka         as Apache Kafka
    participant NotifySvc    as Notification Service

    Client->>Portal: Submit new-matter intake form<br/>(client details, opposing party,<br/>matter type, fee arrangement)
    Portal->>Gateway: POST /api/v1/matters/intake<br/>(JWT bearer token)
    Gateway->>Auth: Validate JWT, check scope=matter:create
    Auth-->>Gateway: 200 OK — claims: {userId, firmId, role:attorney}
    Gateway->>MatterSvc: Forward intake request

    MatterSvc->>ClientSvc: POST /clients/lookup<br/>{name, email, SSN/EIN partial}
    ClientSvc-->>MatterSvc: 200 — {clientId, existing:true} OR 404 new client

    alt New client
        MatterSvc->>ClientSvc: POST /clients<br/>{name, address, contact, taxId}
        ClientSvc-->>MatterSvc: 201 — {clientId}
    end

    MatterSvc->>ConflictSvc: POST /conflict-check<br/>{clientName, opposingParty,<br/>relatedParties, matterType}

    ConflictSvc->>BarDB: Search attorney licensure &<br/>disciplinary records for all timekeepers
    BarDB-->>ConflictSvc: Attorney standing confirmed

    ConflictSvc->>OFAC: Sanctions screening request<br/>{clientName, opposingPartyName, DOB/EIN}
    OFAC-->>ConflictSvc: SDN list check result — no match

    ConflictSvc->>ConflictSvc: Cross-reference internal matter<br/>database for adverse relationships<br/>on same parties (7-year lookback)
    ConflictSvc-->>MatterSvc: 200 — {conflictStatus: "CLEAR",<br/>checkId, timestamp, analyst}

    MatterSvc->>MatterSvc: Assign matter number (YY-MM-SEQ),<br/>set status=PENDING_ENGAGEMENT,<br/>store conflict check artifact

    MatterSvc->>DocuSign: POST /envelopes<br/>{template: "engagement_letter",<br/>signers:[{clientEmail, clientName}],<br/>matterId, billingTerms}
    DocuSign-->>MatterSvc: 201 — {envelopeId, signingUrl}

    MatterSvc->>Portal: 201 — {matterId, status:"PENDING_ENGAGEMENT",<br/>signingUrl}
    Portal->>Client: Redirect to DocuSign embedded signing view

    Client->>DocuSign: Sign engagement letter
    DocuSign->>Gateway: Webhook POST /webhooks/docusign<br/>{envelopeId, status:"completed",<br/>signedAt, documentPDF}
    Gateway->>MatterSvc: Route DocuSign webhook

    MatterSvc->>MatterSvc: Update matter status → ACTIVE,<br/>store signed PDF reference (S3 key)

    MatterSvc->>Kafka: Publish matter.opened event<br/>{matterId, clientId, matterType,<br/>responsibleAttorneyId, openedAt}

    Kafka->>BillingSvc: Consume matter.opened<br/>→ create billing matter record,<br/>apply default UTBMS task codes,<br/>set billing cycle per engagement letter
    Kafka->>NotifySvc: Consume matter.opened<br/>→ send "Matter Opened" email/SMS<br/>to responsible attorney & paralegal
```

### 1.2 Step-by-Step Explanation

| Step | Actor / Service | Action |
|------|-----------------|--------|
| 1 | Client | Submits the new-matter intake form through the self-service Client Portal. The form captures client identification details (name, address, tax ID or SSN partial), the nature of the legal matter, all known opposing and related parties, and the proposed fee arrangement (hourly, flat, contingency). |
| 2–4 | Portal → Gateway → Auth | The portal forwards the authenticated request to the Kong API Gateway, which delegates token validation to Keycloak. The gateway enforces that the calling principal holds the `matter:create` scope before forwarding. |
| 5–7 | MatterSvc → ClientSvc | Matter Service resolves or creates the client record to ensure a canonical `clientId` exists before any conflict check is run against the internal database. |
| 8–13 | MatterSvc → ConflictSvc | A conflict-check request is dispatched to the Conflict Check Service, which performs three independent checks in parallel: attorney standing in the State Bar database, OFAC/SDN sanctions screening, and an internal adverse-relationship sweep across all active and closed matters for a seven-year lookback period. A `CLEAR` result with an immutable `checkId` is mandatory to proceed. |
| 14–15 | MatterSvc | On a clear conflict result, Matter Service mints a firm-unique matter number formatted as `YY-MM-SEQNNN` and sets the initial status to `PENDING_ENGAGEMENT`. The conflict check artifact is stored alongside the matter record for audit purposes. |
| 16–18 | MatterSvc → DocuSign | The engagement letter is dispatched via the DocuSign Envelopes API using a pre-configured firm template that merges matter-specific billing terms. The client receives an embedded signing URL. |
| 19–22 | Client → DocuSign → MatterSvc | Once the client signs, DocuSign posts a completion webhook. Matter Service transitions the matter status to `ACTIVE` and persists the signed PDF reference in Amazon S3. |
| 23–25 | MatterSvc → Kafka | A `matter.opened` domain event is published to the Kafka `lcms.matters` topic. Both Billing Service (to initialise the billing record and UTBMS code set) and Notification Service (to alert the responsible attorney) consume this event asynchronously. |

---

## 2. Court Filing via PACER / CM-ECF

### 2.1 Diagram

```mermaid
sequenceDiagram
    autonumber
    actor Attorney
    participant Portal       as Attorney Portal<br/>(React SPA)
    participant Gateway      as Kong API Gateway
    participant Auth         as Keycloak / Auth Service
    participant DocSvc       as Document Service
    participant S3            as AWS S3<br/>(Document Store)
    participant Elastic       as Elasticsearch<br/>(Doc Index)
    participant PACER         as PACER Integration Service
    participant CMECF         as CM-ECF / Court System<br/>(External)
    participant Kafka         as Apache Kafka
    participant CalSvc       as Calendar Service
    participant TaskSvc      as Task Service
    participant NotifySvc    as Notification Service

    Attorney->>Portal: Initiate filing workflow<br/>{matterId, documentType:"MOTION",<br/>courtId, docketNumber}
    Portal->>Gateway: POST /api/v1/documents/filings<br/>(JWT — scope: filing:create)
    Gateway->>Auth: Validate JWT & role=attorney|paralegal
    Auth-->>Gateway: Claims validated

    Gateway->>DocSvc: Forward filing initiation request

    DocSvc->>DocSvc: Validate document: PDF/A compliance,<br/>page size (8.5×11), file size ≤ 50 MB,<br/>no password protection

    DocSvc->>DocSvc: Apply Bates numbering sequence<br/>for exhibit attachments,<br/>stamp cover page with filing metadata
    DocSvc->>S3: PUT s3://lcms-documents/{firmId}/{matterId}/{docId}.pdf
    S3-->>DocSvc: ETag, versionId

    DocSvc->>Elastic: Index document metadata<br/>{docId, matterId, title, batesRange,<br/>filingType, keywords, text extract}
    Elastic-->>DocSvc: Indexed

    DocSvc-->>Gateway: 201 — {docId, batesRange, s3Key, status:"READY_TO_FILE"}
    Gateway-->>Portal: 201 response forwarded
    Portal->>Attorney: Document validated and review & confirm filing

    Attorney->>Portal: Confirm filing submission
    Portal->>Gateway: POST /api/v1/filings/{docId}/submit
    Gateway->>PACER: Forward to PACER Integration Service

    PACER->>PACER: Authenticate with CM-ECF<br/>using firm PACER credentials (OAuth 2.0 PACER NextGen)
    PACER->>CMECF: POST /cgi-bin/login.pl → establish session
    CMECF-->>PACER: Session token
    PACER->>CMECF: Upload document (multipart/form-data),<br/>docket entry type, party filer, certificate of service
    CMECF-->>PACER: {receipt: {caseNumber, dateTime,<br/>docketEntryNumber, NEFEmailList, filingFee}}

    PACER->>Kafka: Publish filing.submitted event<br/>{docId, matterId, docketEntryNumber,<br/>caseNumber, courtId, filedAt, NEFList, filingFee}

    Kafka->>DocSvc: Consume filing.submitted<br/>→ update document record: status=FILED,<br/>docketEntryNumber, courtStamp
    Kafka->>CalSvc: Consume filing.submitted<br/>→ extract deadlines from NEF<br/>(response due, hearing dates)<br/>→ create CalendarEvent records with<br/>SOL/court-rule reminders
    Kafka->>TaskSvc: Consume filing.submitted<br/>→ auto-generate follow-up tasks:<br/>"Serve opposing counsel",<br/>"Calendar response deadline",<br/>"Update docket sheet"
    Kafka->>NotifySvc: Consume filing.submitted<br/>→ email attorney & paralegal<br/>the NEF confirmation with filing receipt

    PACER-->>Portal: 200 — {receipt, docketEntryNumber, filedAt}
    Portal->>Attorney: Display CM-ECF filing receipt<br/>and Notice of Electronic Filing
```

### 2.2 Step-by-Step Explanation

| Step | Actor / Service | Action |
|------|-----------------|--------|
| 1–4 | Attorney → DocSvc | The attorney initiates a filing workflow by specifying the matter, document type, target court, and docket/case number. Kong validates the JWT and ensures the caller holds the `filing:create` scope. |
| 5–9 | DocSvc | Document Service performs a series of pre-flight validations required by CM-ECF: PDF/A compliance check, page-dimension conformance, 50 MB per-document size cap, and absence of password protection. Exhibits receive a Bates stamp from the central Bates sequence for the matter. The validated file is written to S3 (versioned bucket) and its text is indexed in Elasticsearch for full-text search. |
| 10–13 | Portal ↔ Attorney | The validated document is previewed in the portal. The attorney reviews the CM-ECF docket entry metadata and confirms submission. |
| 14–18 | PACER Integration → CM-ECF | The PACER Integration Service authenticates using the firm's PACER NextGen OAuth credentials, constructs the CM-ECF multipart filing request (document, case number, docket entry type, party information, and certificate of service), and submits. CM-ECF returns a filing receipt containing the docket entry number, timestamp, filing fee, and the list of attorneys who will receive the Notice of Electronic Filing (NEF). |
| 19–24 | Kafka consumers | A `filing.submitted` event triggers three downstream consumers: Document Service records the docket entry number and marks the document `FILED`; Calendar Service parses response deadlines from the NEF and creates calendar events with automatic court-rule-based reminders; Task Service generates standard post-filing task checklist items; Notification Service delivers the NEF and receipt to the filing attorney and assigned paralegal. |

---

## 3. Invoice Generation and Payment Collection

### 3.1 Diagram

```mermaid
sequenceDiagram
    autonumber
    actor BillingSpec  as Billing Specialist
    participant Portal       as Staff Portal<br/>(React SPA)
    participant Gateway      as Kong API Gateway
    participant BillingSvc   as Billing Service
    participant MatterSvc    as Matter Service
    participant LEDES         as LEDES Formatter<br/>(internal lib)
    participant S3            as AWS S3
    participant Kafka         as Apache Kafka
    participant NotifySvc    as Notification Service
    participant ClientPortal  as Client Portal
    actor Client
    participant PayGW         as Payment Gateway<br/>(Stripe/LawPay)
    participant TrustSvc     as Trust Accounting Service
    participant QB            as QuickBooks / Aderant<br/>(External)

    BillingSpec->>Portal: Open pre-bill review for matter<br/>{matterId, billingPeriod}
    Portal->>Gateway: GET /api/v1/billing/pre-bill/{matterId}?period=2025-01
    Gateway->>BillingSvc: Forward request
    BillingSvc->>MatterSvc: GET /matters/{matterId}/timekeepers<br/>→ validate billing arrangements
    MatterSvc-->>BillingSvc: {billingType:HOURLY, rates:{partner:650, associate:380, paralegal:175}}

    BillingSvc->>BillingSvc: Aggregate unbilled time entries &<br/>disbursements for period and<br/>apply UTBMS task/activity codes and<br/>apply billing rules (minimum increments,<br/>rate caps per engagement letter)

    BillingSvc-->>Portal: Pre-bill summary<br/>{totalHours:42.3, totalFees:$18,420,<br/>disbursements:$1,240, adjustments:-$500}
    BillingSpec->>Portal: Review, apply write-downs, add narrative,<br/>approve for invoicing

    Portal->>Gateway: POST /api/v1/billing/invoices<br/>{matterId, period, approvedLineItems}
    Gateway->>BillingSvc: Create invoice
    BillingSvc->>LEDES: Generate LEDES 1998B file<br/>{timekeeper codes, UTBMS codes,<br/>line item detail, client/matter identifiers}
    LEDES-->>BillingSvc: LEDES file content (ASCII)
    BillingSvc->>S3: PUT invoice PDF + LEDES file to<br/>s3://lcms-billing/{firmId}/{invoiceId}/
    S3-->>BillingSvc: Stored

    BillingSvc->>Kafka: Publish invoice.created event<br/>{invoiceId, matterId, clientId,<br/>totalDue:$19,160, dueDate:2025-02-14,<br/>ledesS3Key}

    Kafka->>NotifySvc: Consume invoice.created<br/>→ email client invoice PDF + LEDES file,<br/>include secure payment link
    NotifySvc->>ClientPortal: Deliver invoice notification<br/>with in-portal payment CTA

    Client->>ClientPortal: View invoice, click "Pay Now"
    ClientPortal->>Gateway: POST /api/v1/payments<br/>{invoiceId, amount:$19160,<br/>paymentMethod:{type:ACH, ...}}
    Gateway->>BillingSvc: Process payment request
    BillingSvc->>PayGW: Charge request (LawPay/Stripe)<br/>{amount, currency:USD, metadata:{invoiceId}}
    PayGW-->>BillingSvc: {chargeId, status:succeeded, settledAt}

    BillingSvc->>BillingSvc: Mark invoice PAID,<br/>record receipt, update A/R ledger

    alt Trust retainer was held
        BillingSvc->>TrustSvc: POST /trust/disbursements<br/>{matterId, amount:$19160,<br/>from:IOLTA, to:operatingAccount,<br/>invoiceId, description:"Fee earned"}
        TrustSvc-->>BillingSvc: Disbursement confirmed, trustLedgerEntry created
    end

    BillingSvc->>Kafka: Publish payment.received event<br/>{invoiceId, chargeId, amount, paidAt}

    Kafka->>QB: Consume payment.received<br/>→ POST journal entry to QuickBooks/Aderant<br/>(debit A/R, credit revenue, record payment)
    QB-->>Kafka: ACK (async webhook callback)

    Kafka->>NotifySvc: Consume payment.received<br/>→ send payment confirmation receipt to client
```

### 3.2 Step-by-Step Explanation

| Step | Actor / Service | Action |
|------|-----------------|--------|
| 1–6 | BillingSpec → BillingSvc | The billing specialist opens the pre-bill review dashboard for a specific matter and billing period. Billing Service fetches the matter's rate schedule from Matter Service and aggregates all unbilled time entries and disbursements, applying firm billing rules such as minimum time increments (typically 0.1-hour tenths), rate caps specified in the engagement letter, and UTBMS task/activity code mappings. |
| 7–8 | Portal → BillingSpec | The pre-bill summary is presented for human review. The specialist can apply write-downs, add narrative descriptions, and remove any entries before finalising. |
| 9–13 | BillingSvc → LEDES | Upon approval, Billing Service invokes the internal LEDES 1998B formatter to produce the machine-readable billing file required by most corporate clients and insurance carriers. Both the formatted invoice PDF and the LEDES file are stored in S3 under a versioned key. |
| 14–16 | Kafka → NotifySvc | The `invoice.created` event triggers Notification Service to deliver the invoice to the client via email and through the client portal, including a secure one-time payment link. |
| 17–21 | Client → PayGW | The client pays through the portal using ACH or card via LawPay or Stripe. Billing Service records the payment, marks the invoice `PAID`, and updates the accounts-receivable ledger. |
| 22–24 | Trust disbursement (conditional) | If fees were drawn against a held retainer in the IOLTA trust account, Billing Service instructs Trust Accounting Service to execute the disbursement from the IOLTA account to the firm's operating account with a proper ledger entry. |
| 25–27 | Kafka → QuickBooks | The `payment.received` event is consumed by the accounting integration, which posts the corresponding journal entry to QuickBooks or Aderant, ensuring the firm's financial system of record remains synchronised. |

---

## 4. Trust Account Disbursement

### 4.1 Diagram

```mermaid
sequenceDiagram
    autonumber
    actor Attorney
    participant Portal       as Staff Portal<br/>(React SPA)
    participant Gateway      as Kong API Gateway
    participant Auth         as Keycloak / Auth Service
    participant TrustSvc     as Trust Accounting Service
    participant MatterSvc    as Matter Service
    participant BillingSvc   as Billing Service
    participant Kafka         as Apache Kafka
    participant NotifySvc    as Notification Service
    actor Supervisor         as Managing Partner<br/>(Approver)
    participant QB            as QuickBooks / Aderant<br/>(External)
    participant BankAPI       as Bank ACH API<br/>(External)

    Attorney->>Portal: Request trust disbursement<br/>{matterId, amount:$5000,<br/>disbursementType: COST_ADVANCE,<br/>payee:"Expert Witness Inc.",<br/>description:"Expert witness retainer"}
    Portal->>Gateway: POST /api/v1/trust/disbursements<br/>(JWT — scope: trust:request)
    Gateway->>Auth: Validate — role must be attorney|paralegal
    Auth-->>Gateway: Claims valid

    Gateway->>TrustSvc: Forward disbursement request
    TrustSvc->>MatterSvc: GET /matters/{matterId}/trust-balance
    MatterSvc-->>TrustSvc: {trustBalance:$18,500, currency:USD,<br/>ioltaAccountId:"IOLTA-2024-007"}

    TrustSvc->>TrustSvc: Validate:<br/>• Sufficient balance ($5000 ≤ $18,500) ✓<br/>• Payee not on OFAC list ✓<br/>• Disbursement type permitted by<br/>  engagement letter ✓
    TrustSvc->>TrustSvc: Create disbursement record<br/>status=PENDING_APPROVAL,<br/>freeze $5,000 in ledger (soft hold)

    TrustSvc->>Kafka: Publish trust.disbursement.pending event<br/>{disbursementId, matterId, amount,<br/>payee, requestedBy, requestedAt}

    Kafka->>NotifySvc: Consume → notify Supervisor<br/>via email + in-app alert:<br/>"Trust disbursement requires approval"
    NotifySvc->>Supervisor: Approval request with disbursement details

    Supervisor->>Portal: Review disbursement request
    Portal->>Gateway: POST /api/v1/trust/disbursements/{id}/approve<br/>(JWT — scope: trust:approve, role:managing_partner)
    Gateway->>Auth: Validate supervisor role
    Auth-->>Gateway: Approved — supervisor claims

    Gateway->>TrustSvc: Approve disbursement

    TrustSvc->>TrustSvc: Record approval: approvedBy, approvedAt<br/>Transition status → APPROVED<br/>Finalise ledger debit entry

    TrustSvc->>BankAPI: POST /ach/credit-transfers<br/>{from:IOLTA-2024-007,<br/>to:{routingNumber, accountNumber},<br/>amount:5000.00, memo:"Expert Witness Inc.<br/>— Matter 25-01-0042 cost advance"}
    BankAPI-->>TrustSvc: {transferId, estimatedSettlement:"2025-01-17",<br/>status:INITIATED}

    TrustSvc->>TrustSvc: Post final trust ledger entry:<br/>DEBIT IOLTA $5,000,<br/>reference: transferId, disbursementId<br/>Update client trust ledger card

    TrustSvc->>Kafka: Publish trust.disbursement.completed event<br/>{disbursementId, transferId, amount,<br/>settledAt, ioltaAccountId, matterId}

    Kafka->>BillingSvc: Consume → record cost advance<br/>on matter billing record<br/>(disbursement line item for future invoicing)
    Kafka->>QB: Consume → post journal entry<br/>DEBIT: Trust Liability / IOLTA<br/>CREDIT: Trust Asset / Bank ACH<br/>Record payee disbursement in A/P
    Kafka->>NotifySvc: Consume → notify attorney & client<br/>of completed disbursement with<br/>updated trust balance statement

    TrustSvc-->>Portal: 200 — {disbursementId, status:COMPLETED,<br/>transferId, newTrustBalance:$13,500}
    Portal->>Attorney: Display trust disbursement confirmation<br/>and updated IOLTA ledger card
```

### 4.2 Step-by-Step Explanation

| Step | Actor / Service | Action |
|------|-----------------|--------|
| 1–4 | Attorney → TrustSvc | The attorney submits a trust disbursement request specifying the matter, amount, disbursement type (cost advance, earned-fee transfer, or third-party payment), payee details, and a description for the trust ledger. Kong validates the JWT and confirms the `trust:request` scope. |
| 5–6 | TrustSvc → MatterSvc | Trust Accounting Service fetches the current IOLTA trust balance for the matter to confirm sufficient funds are available before any ledger holds are placed. |
| 7–8 | TrustSvc (validation) | Three concurrent validations are performed: balance sufficiency, OFAC sanctions screening of the payee, and verification that the disbursement type is permitted under the client's engagement letter terms. A soft ledger hold is placed on the requested amount to prevent double-spending during the approval window. |
| 9–11 | Kafka → Supervisor | A `trust.disbursement.pending` event routes an approval notification to the managing partner or designated trust account supervisor via both email and the in-app notification centre. The approval request includes the full disbursement context and a direct link to the approval workflow. |
| 12–15 | Supervisor → TrustSvc | The supervising attorney reviews and approves the disbursement from the portal. Keycloak enforces that only principals holding the `trust:approve` scope and the `managing_partner` role can issue approvals. Trust Service transitions the disbursement record to `APPROVED` and finalises the ledger debit entry. |
| 16–18 | TrustSvc → Bank ACH | The service initiates an ACH credit transfer from the IOLTA account to the payee's bank account via the firm's banking API. The estimated settlement date (typically next business day for same-day ACH) is recorded. |
| 19–23 | Kafka consumers | The `trust.disbursement.completed` event triggers: Billing Service records the cost advance as a disbursement line item on the matter for future invoicing; QuickBooks receives the journal entry debiting the IOLTA trust liability and crediting the bank asset; Notification Service sends the attorney and client an updated IOLTA ledger card reflecting the new trust balance and the disbursement transaction. |
