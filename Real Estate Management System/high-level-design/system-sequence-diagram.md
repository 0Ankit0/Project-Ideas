# System Sequence Diagrams — Real Estate Management System

This document captures the three primary end-to-end system-level sequence flows in the Real Estate Management System (REMS): the tenant application and lease signing lifecycle, the monthly automated rent collection cycle, and the maintenance request workflow.

---

## 1. Tenant Application & Lease Signing Sequence

This flow covers the complete journey from a prospective tenant submitting an application through background/credit checks, lease generation, DocuSign-based digital signing, and final activation of the tenancy.

```mermaid
sequenceDiagram
    autonumber
    actor TB as Tenant Browser
    participant GW as API Gateway
    participant AS as Application Service
    participant BCS as Background Check Service
    participant CCS as Credit Check Service
    participant CHK as Checkr / TransUnion API
    participant LS as Lease Service
    participant DS as Document Service
    participant DOCU as DocuSign API
    participant NS as Notification Service
    participant DB as PostgreSQL

    TB->>GW: POST /applications { unitId, personalInfo, SSN, income }
    GW->>GW: Validate JWT, rate-limit, schema check
    GW->>AS: forward createApplication(payload)
    AS->>DB: INSERT TenantApplication (status=PENDING)
    AS->>NS: emit APPLICATION_RECEIVED event
    NS-->>TB: Email "Application received — ref #APP-001"

    AS->>BCS: initiateBackgroundCheck(applicantId, ssn, dob)
    BCS->>CHK: POST /background-checks { ssn, dob, firstName, lastName }
    CHK-->>BCS: 202 Accepted { checkId: "chk_abc123" }
    BCS->>DB: INSERT BackgroundCheck (status=IN_PROGRESS, externalId=chk_abc123)

    AS->>CCS: initiateCreditCheck(applicantId, ssn)
    CCS->>CHK: POST /credit-checks { ssn, applicantId }
    CHK-->>CCS: 202 Accepted { reportId: "crd_xyz789" }
    CCS->>DB: INSERT CreditCheck (status=IN_PROGRESS, externalId=crd_xyz789)

    Note over CHK: Async processing — webhook callback

    CHK->>BCS: PATCH /webhooks/background { checkId, status=CLEAR, reportUrl }
    BCS->>DB: UPDATE BackgroundCheck (status=CLEAR, reportUrl)
    BCS->>AS: emit BACKGROUND_CHECK_COMPLETE { applicationId, result=CLEAR }

    CHK->>CCS: PATCH /webhooks/credit { reportId, score=720, status=APPROVED }
    CCS->>DB: UPDATE CreditCheck (status=APPROVED, score=720)
    CCS->>AS: emit CREDIT_CHECK_COMPLETE { applicationId, score=720 }

    AS->>AS: evaluateApplication(backgroundResult=CLEAR, creditScore=720)
    AS->>DB: UPDATE TenantApplication (status=APPROVED)
    AS->>NS: emit APPLICATION_APPROVED { applicationId, tenantId }
    NS-->>TB: Email "Congratulations! Your application is approved."

    TB->>GW: POST /leases/initiate { applicationId, moveInDate, term=12 }
    GW->>LS: createLease(applicationId, moveInDate, term)
    LS->>DB: SELECT Property, Unit, RentSchedule, StandardClauses
    LS->>DS: generateLeaseDocument(leaseData, clauses)
    DS->>DS: Render PDF with all LeaseClause entries
    DS-->>LS: documentId, s3Url

    LS->>DOCU: POST /envelopes { document: s3Url, signers: [tenant, pm] }
    DOCU-->>LS: 201 { envelopeId: "env_001", signingUrl }
    LS->>DB: INSERT Lease (status=PENDING_SIGNATURE, envelopeId=env_001)
    LS->>NS: emit LEASE_SENT_FOR_SIGNATURE { tenantId, pmId, signingUrl }
    NS-->>TB: Email + SMS "Please sign your lease — link expires in 48 hrs"

    TB->>DOCU: Open signing URL, review & sign lease
    DOCU->>DOCU: Capture electronic signature, timestamp
    DOCU->>GW: POST /webhooks/docusign { envelopeId, event=COMPLETED }
    GW->>LS: handleDocuSignWebhook(envelopeId, event=COMPLETED)
    LS->>DOCU: GET /envelopes/env_001/documents — download signed PDF
    LS->>DS: storeSignedDocument(signedPdf, leaseId)
    LS->>DB: UPDATE Lease (status=ACTIVE, signedDocumentId, activatedAt)
    LS->>DB: INSERT SecurityDeposit (leaseId, amount, status=PENDING_COLLECTION)
    LS->>NS: emit LEASE_ACTIVATED { leaseId, tenantId, pmId }
    NS-->>TB: Email "Your lease is active — move-in confirmation attached"
    NS-->>GW: Notify PM dashboard via WebSocket push
```

---

## 2. Monthly Rent Collection Sequence

This flow describes the fully automated monthly rent cycle — from invoice generation triggered by the scheduler, through Stripe charge processing, payment reconciliation in the ledger, and late-fee assessment for overdue invoices.

```mermaid
sequenceDiagram
    autonumber
    participant SCH as Job Scheduler (Cron)
    participant RS as Rent Service
    participant DB as PostgreSQL
    participant STRIPE as Stripe API
    participant NS as Notification Service
    participant LED as Ledger Service
    actor TEN as Tenant
    participant OWN as Owner Portal

    SCH->>RS: triggerMonthlyRentCycle(billingDate=2025-08-01)
    RS->>DB: SELECT active RentSchedules WHERE nextDueDate = billingDate
    DB-->>RS: [ { leaseId, tenantId, unitId, amount, paymentMethodId } × N ]

    loop For each active RentSchedule
        RS->>DB: INSERT RentInvoice (leaseId, amount, dueDate, status=ISSUED)
        RS->>NS: emit RENT_INVOICE_CREATED { invoiceId, tenantId, amount, dueDate }
        NS-->>TEN: Email "Rent invoice #INV-2025-08 due on 2025-08-05 — $2,400"
    end

    Note over SCH: On due date — auto-charge attempt

    SCH->>RS: triggerAutoCharge(dueDate=2025-08-05)
    RS->>DB: SELECT RentInvoices WHERE dueDate = today AND status=ISSUED AND autoPayEnabled=true

    loop For each auto-pay invoice
        RS->>STRIPE: POST /payment_intents { amount, currency, customer, payment_method, confirm=true }
        alt Payment Successful
            STRIPE-->>RS: 200 { paymentIntentId, status=succeeded, chargedAt }
            RS->>DB: INSERT RentPayment (invoiceId, amount, stripeId, status=PAID, paidAt)
            RS->>DB: UPDATE RentInvoice (status=PAID)
            RS->>LED: recordPayment(leaseId, amount, type=RENT, referenceId=stripePaymentId)
            LED->>DB: INSERT LedgerEntry (credit, amount, category=RENT, date)
            RS->>NS: emit RENT_PAYMENT_CONFIRMED { tenantId, invoiceId, amount }
            NS-->>TEN: Email + SMS "Payment of $2,400 received — receipt attached"
        else Payment Failed (card declined)
            STRIPE-->>RS: 402 { error: card_declined, declineCode: insufficient_funds }
            RS->>DB: UPDATE RentInvoice (status=PAYMENT_FAILED, failureReason)
            RS->>DB: INSERT FailedPaymentAttempt (invoiceId, attemptedAt, reason)
            RS->>NS: emit RENT_PAYMENT_FAILED { tenantId, invoiceId, reason }
            NS-->>TEN: Email + SMS "Payment failed — update payment method to avoid late fees"
        end
    end

    Note over SCH: Grace period expires — late fee assessment

    SCH->>RS: assessLateFees(assessmentDate=2025-08-10)
    RS->>DB: SELECT RentInvoices WHERE dueDate < today-gracePeriod AND status IN (ISSUED, PAYMENT_FAILED)

    loop For each overdue invoice
        RS->>RS: calculateLateFee(policy=PERCENTAGE, rate=5%, baseAmount)
        RS->>DB: INSERT LateFee (invoiceId, amount, assessedAt, status=OUTSTANDING)
        RS->>DB: UPDATE RentInvoice (lateFeeApplied=true)
        RS->>NS: emit LATE_FEE_ASSESSED { tenantId, invoiceId, lateFeeAmount }
        NS-->>TEN: Email "Late fee of $120 applied to invoice #INV-2025-08"
    end

    Note over LED: End-of-month owner statement generation

    SCH->>LED: generateOwnerStatements(period=2025-08)
    LED->>DB: SELECT all LedgerEntries, RentPayments, LateFees, MaintenanceCosts for period
    LED->>DB: INSERT OwnerStatement (ownerId, period, grossIncome, expenses, netIncome)
    LED->>NS: emit OWNER_STATEMENT_READY { ownerId, statementId, period }
    NS-->>OWN: Email "Your August 2025 owner statement is ready — view now"
```

---

## 3. Maintenance Request Flow

This flow covers the full lifecycle of a maintenance request — from tenant submission through property manager triage, contractor assignment, work completion, and final tenant confirmation.

```mermaid
sequenceDiagram
    autonumber
    actor TEN as Tenant
    participant GW as API Gateway
    participant MS as Maintenance Service
    participant DB as PostgreSQL
    participant PMD as PM Dashboard
    participant NS as Notification Service
    actor PM as Property Manager
    participant CA as Contractor App
    actor CON as Contractor
    participant IS as Inspection Service
    participant MEDIA as Document/Media Service

    TEN->>GW: POST /maintenance-requests { unitId, category, priority, description, photos[] }
    GW->>GW: Authenticate JWT, validate schema
    GW->>MEDIA: uploadPhotos(photos[]) — store to S3
    MEDIA-->>GW: [ { photoId, s3Url } ]
    GW->>MS: createMaintenanceRequest(payload + photoUrls)
    MS->>DB: INSERT MaintenanceRequest (unitId, tenantId, category, priority=HIGH, status=OPEN)
    MS->>NS: emit MAINTENANCE_REQUEST_CREATED { requestId, unitId, pmId }
    NS-->>TEN: Email + SMS "Request #MR-0042 received — we'll be in touch within 24 hrs"
    NS-->>PMD: WebSocket push — new maintenance request badge

    PM->>PMD: Open request #MR-0042, review description + photos
    PMD->>GW: GET /maintenance-requests/MR-0042
    GW->>MS: getRequestDetail(MR-0042)
    MS->>DB: SELECT MaintenanceRequest JOIN Photos JOIN Unit JOIN Tenant
    DB-->>MS: full request detail
    MS-->>PMD: request detail payload

    PM->>PMD: Assign to contractor { contractorId: "CON-007", scheduledDate, estimatedCost }
    PMD->>GW: PATCH /maintenance-requests/MR-0042/assign { contractorId, scheduledDate }
    GW->>MS: assignContractor(requestId, contractorId, scheduledDate)
    MS->>DB: INSERT MaintenanceAssignment (requestId, contractorId, scheduledDate, status=ASSIGNED)
    MS->>DB: UPDATE MaintenanceRequest (status=ASSIGNED, assignedAt)
    MS->>NS: emit MAINTENANCE_ASSIGNED { requestId, contractorId, tenantId, scheduledDate }
    NS-->>TEN: Email + SMS "Technician scheduled for Aug 3, 2025 between 10am–2pm"
    NS-->>CA: Push notification to contractor app "New job #MR-0042 assigned"

    CON->>CA: Accept job, view details + photos
    CA->>GW: PATCH /maintenance-assignments/{id}/accept
    GW->>MS: updateAssignmentStatus(assignmentId, ACCEPTED)
    MS->>DB: UPDATE MaintenanceAssignment (status=ACCEPTED)

    CON->>CA: Arrive on site, start work — check-in
    CA->>GW: PATCH /maintenance-assignments/{id}/start { arrivedAt }
    GW->>MS: updateAssignmentStatus(assignmentId, IN_PROGRESS, arrivedAt)
    MS->>DB: UPDATE MaintenanceRequest (status=IN_PROGRESS)
    MS->>NS: emit MAINTENANCE_IN_PROGRESS { requestId, tenantId }
    NS-->>TEN: SMS "Your technician has arrived and work has begun"

    CON->>CA: Complete work — upload completion photos + notes
    CA->>MEDIA: uploadCompletionPhotos(photos[])
    MEDIA-->>CA: [ { photoId, s3Url } ]
    CA->>GW: PATCH /maintenance-assignments/{id}/complete { completionNotes, photoUrls, laborHours, partsUsed }
    GW->>MS: completeAssignment(assignmentId, completionPayload)
    MS->>DB: UPDATE MaintenanceAssignment (status=COMPLETED, completedAt, laborHours, actualCost)
    MS->>DB: UPDATE MaintenanceRequest (status=COMPLETED_PENDING_REVIEW)
    MS->>NS: emit MAINTENANCE_WORK_COMPLETED { requestId, tenantId, pmId }
    NS-->>TEN: Email + SMS "Work completed — please confirm and rate the service"

    TEN->>GW: PATCH /maintenance-requests/MR-0042/confirm { rating=5, comment="Great work!" }
    GW->>MS: confirmCompletion(requestId, rating, comment)
    MS->>DB: UPDATE MaintenanceRequest (status=CLOSED, closedAt, tenantRating=5)
    MS->>NS: emit MAINTENANCE_CLOSED { requestId, pmId, contractorId }
    NS-->>PMD: WebSocket "Request #MR-0042 closed — rated 5/5"
```

---

*Last updated: 2025 | Real Estate Management System v1.0*
