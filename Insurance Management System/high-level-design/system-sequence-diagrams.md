# System Sequence Diagrams — Insurance Management System

This document presents the key system sequence diagrams for the Insurance Management System (IMS).
Each diagram captures the interaction between actors and services for a critical business flow,
illustrating message passing, service orchestration, and event propagation across the platform.
These diagrams serve as the authoritative reference for API contract design, integration testing,
and onboarding documentation for engineering teams.

---

## Diagram 1: Quote-to-Policy Issuance Flow

The Quote-to-Policy flow covers the complete journey from a customer submitting an insurance
application through a broker portal, through underwriting evaluation and risk pricing, to the
issuance of a bound policy. This flow spans multiple microservices and ensures that only eligible
applicants receive coverage at actuarially appropriate premium rates. The underwriting decision
incorporates real-time risk factor evaluation, and payment collection is completed before the
policy record reaches an `ACTIVE` state.

```mermaid
sequenceDiagram
    autonumber
    participant C as Customer
    participant BP as BrokerPortal
    participant AG as APIGateway
    participant PS as PolicyService
    participant UW as UnderwritingService
    participant PE as PricingEngine
    participant PAY as PaymentService
    participant NS as NotificationService

    C->>BP: Submit insurance application (personal details, coverage type, sum insured)
    BP->>AG: POST /api/v1/quotes (application payload + product code)
    AG->>AG: Validate JWT token, check rate limit, inspect request schema
    AG->>PS: Forward validated application request

    PS->>PS: Validate mandatory fields (DOB, NationalId, coverage amount, effective date)
    PS-->>AG: 400 Bad Request (if schema validation fails)
    AG-->>BP: Return validation error list
    BP-->>C: Display field-level validation errors

    PS->>UW: POST /underwriting/evaluate (applicant profile, product, requested coverage)
    UW->>UW: Load UnderwritingRule set for product line (life/auto/home/commercial)
    UW->>UW: Resolve RiskFactors (age band, claims history, location risk score, credit tier)
    UW->>UW: Execute rule engine — compute risk score, apply exclusions, determine loadings
    UW-->>PS: UnderwritingDecision {eligible, riskScore, exclusions[], loadings[], declineReasons[]}

    alt Underwriting declines application
        PS-->>AG: 422 Unprocessable Entity (decline reasons)
        AG-->>BP: Decline notice
        BP-->>C: Display decline reasons and appeal process information
    end

    PS->>PE: POST /pricing/calculate (riskScore, coverageAmount, term, deductibles, loadings)
    PE->>PE: Retrieve base rate tables for product/coverage combination
    PE->>PE: Apply risk loadings, no-claims discounts, bundling discounts
    PE->>PE: Compute gross premium, applicable taxes, broker commission, net payable
    PE-->>PS: PremiumQuote {basePremium, loadings, taxes, commissions, totalPremium, validUntil}

    PS->>PS: Persist Quote entity with status=PENDING_ACCEPTANCE and 30-day validity window
    PS-->>AG: QuoteResponse {quoteId, quoteNumber, premium, coverageTerms, exclusions, expiresAt}
    AG-->>BP: Forward quote response
    BP-->>C: Display quote summary, premium breakdown, terms, and exclusions

    Note over C,BP: Customer reviews quote — valid for 30 days per product configuration

    C->>BP: Accept quote and provide payment details (card token / bank account)
    BP->>AG: POST /api/v1/quotes/{quoteId}/accept (paymentMethodToken)
    AG->>PS: Forward acceptance with payment token

    PS->>PS: Validate quote is not expired and status is PENDING_ACCEPTANCE
    PS->>PAY: POST /payments/collect {quoteId, amount, currency, paymentToken, billingDetails}
    PAY->>PAY: Tokenize and vault payment instrument (PCI-DSS Level 1 vault)
    PAY->>PAY: Submit charge to payment network
    PAY-->>PS: PaymentResult {transactionId, status: SUCCESS, receiptNumber, processedAt}

    PS->>PS: Create Policy entity from accepted Quote (copy coverage terms, endorsements)
    PS->>PS: Generate unique policy number (format: POL-{YEAR}-{SEQ})
    PS->>PS: Create Premium record and generate PremiumSchedule entries for policy term
    PS->>PS: Persist Policy with status=ACTIVE, effectiveDate, expiryDate

    PS->>NS: Publish PolicyIssuedEvent {policyId, policyNumber, holderId, brokerId, effectiveDate}
    NS->>NS: Render policy schedule PDF and certificate of insurance
    NS->>NS: Render welcome letter with coverage summary
    NS->>C: Email policy documents, certificate of insurance, and payment receipt
    NS->>BP: Email broker policy confirmation and commission credit notice

    PS-->>AG: PolicyIssuedResponse {policyId, policyNumber, effectiveDate, expiryDate}
    AG-->>BP: Return policy confirmation
    BP-->>C: Display policy number and confirmation with document download links

    Note over PS,NS: PolicyIssuedEvent is also published to Kafka topic policy-lifecycle-events for BillingService and ReinsuranceService
```

**Key observations:**
- The underwriting evaluation is synchronous for standard personal lines; complex commercial lines trigger an asynchronous manual underwriting workflow requiring a human underwriter decision.
- Quote validity (default 30 days) is configurable per product and jurisdiction in the `Product` entity.
- Payment failure at collection rolls back the Quote to `PENDING_ACCEPTANCE` and triggers a `PaymentFailedEvent`; the customer may retry with a different payment method.
- The `PolicyIssuedEvent` on Kafka enables the `ReinsuranceService` to check if the policy exceeds cession thresholds and automatically create `Reinsurance` records.

---

## Diagram 2: Claims First Notice of Loss (FNOL) Flow

The First Notice of Loss flow is initiated when a policyholder reports an insured loss event.
The system verifies active policy coverage for the reported loss date, scores the claim for
potential fraud using the ML-backed FraudService, assigns a qualified adjuster based on
specialization and geographic proximity, and dispatches acknowledgment communications.
Accurate FNOL capture is critical for claims reserve estimation and regulatory reporting under
Solvency II requirements.

```mermaid
sequenceDiagram
    autonumber
    participant PH as Policyholder
    participant CP as ClaimsPortal
    participant AG as APIGateway
    participant CS as ClaimsService
    participant POS as PolicyService
    participant FS as FraudService
    participant AAS as AdjusterAssignmentService
    participant NS as NotificationService

    PH->>CP: Submit FNOL form (policy number, loss date, loss type, loss description, estimated loss amount)
    CP->>CP: Client-side form validation (required fields, date sanity checks)
    CP->>AG: POST /api/v1/claims/fnol (FNOL payload + supporting document uploads)
    AG->>AG: Authenticate request via JWT or OTP verification for non-portal submissions
    AG->>CS: Route validated FNOL payload to ClaimsService

    CS->>CS: Assign FNOL reference number (format: CLM-{YEAR}-{SEQ})
    CS->>POS: GET /policies/{policyNumber}/coverage-check?lossDate={date}&lossType={type}
    POS->>POS: Verify policy status was ACTIVE on reported loss date
    POS->>POS: Validate requested coverage type exists within PolicyCoverage list
    POS->>POS: Check deductibles, sub-limits, territorial exclusions, and waiting periods
    POS-->>CS: CoverageVerification {covered: true, coverageId, deductible, subLimit, policyId}

    alt Policy inactive, coverage excluded, or loss pre-dates effective date
        CS-->>AG: 422 Unprocessable Entity {reason, contactDetails}
        AG-->>CP: Coverage denial message
        CP-->>PH: Display denial reason, recourse options, and complaints procedure
    end

    CS->>CS: Persist Claim entity with status=FNOL_RECEIVED, lossDate, claimedAmount
    CS->>CS: Persist LossEvent record (eventType, eventLocation, eventDate, description)
    CS->>CS: Create ClaimDocument records for each uploaded file (photos, police report, receipts)

    CS->>FS: POST /fraud/score {claimId, policyId, claimantId, lossAmount, lossType, priorClaims, submissionChannel}
    FS->>FS: Load FraudIndicator rules applicable to this claim type and product line
    FS->>FS: Execute ML fraud scoring model (gradient boosted classifier on 47 features)
    FS->>FS: Query claimant against Fraud Bureau external watchlist
    FS->>FS: Check claim for duplicate loss event patterns across the portfolio
    FS-->>CS: FraudScoreResult {fraudScore, riskLevel, flaggedIndicators[], watchlistMatch}

    Note over CS,FS: Fraud scores above 0.75 trigger automatic SIU (Special Investigations Unit) referral

    CS->>CS: Persist FraudIndicator records linked to Claim
    CS->>CS: Update Claim status to UNDER_INVESTIGATION (or SIU_REFERRAL if high fraud score)

    CS->>AAS: POST /adjusters/assign {claimId, claimType, lossAmount, region, urgency, specialization}
    AAS->>AAS: Query active adjusters with matching specialization license and regional coverage
    AAS->>AAS: Apply workload balancing rules (max caseload 45 open claims per adjuster)
    AAS->>AAS: Select optimal adjuster by proximity, availability, and expertise score
    AAS-->>CS: AssignmentResult {adjusterId, adjusterName, adjusterContact, estimatedContactDate}

    CS->>CS: Persist AdjustmentRecord linking selected Adjuster to Claim
    CS->>CS: Update Claim status to ADJUSTER_ASSIGNED

    CS->>NS: Publish ClaimFNOLAcknowledgedEvent {claimId, referenceNumber, adjusterId, policyId}
    NS->>PH: Email FNOL acknowledgment (claim reference, expected contact date, document checklist)
    NS->>AAS: Send adjuster SMS and email notification of new claim assignment with portal link
    NS->>CP: Push real-time portal notification to policyholder dashboard

    CS-->>AG: FNOLResponse {claimId, referenceNumber, status: ADJUSTER_ASSIGNED, estimatedContactDate}
    AG-->>CP: FNOL submission confirmation
    CP-->>PH: Display claim reference number, adjuster name, and next steps

    Note over CS,NS: ClaimFNOLAcknowledgedEvent is published to Kafka topic claim-events for ReportingService and audit
```

**Key observations:**
- FNOL may be submitted via web portal, mobile app, broker portal, or inbound call centre (IVR to agent transcription); all channels converge at the API Gateway.
- The fraud scoring model runs synchronously for claims under $50,000; claims above this threshold invoke an async enrichment pipeline that collects additional data from third-party data providers before scoring.
- SIU referrals bypass standard adjuster assignment and route directly to the Special Investigations Unit queue; the policyholder is notified that additional information is required without revealing the SIU investigation.
- All FNOL events feed the `ClaimReserveService` (part of `ClaimsService`) which establishes initial IBNR (Incurred But Not Reported) reserves for Solvency II capital adequacy calculations.

---

## Diagram 3: Scheduled Premium Collection Flow

Premium collection is a system-initiated process triggered by the BillingService on each billing
due date. The service retrieves all `PremiumSchedule` records due for collection, processes
payments via the Payment Gateway, updates policy payment standing, and dispatches receipts or
failure notices. Retry logic and lapse management are governed by product-level grace period
configurations and statutory requirements per jurisdiction.

```mermaid
sequenceDiagram
    autonumber
    participant SCH as Scheduler (Cron)
    participant BS as BillingService
    participant PGW as PaymentGateway
    participant POS as PolicyService
    participant NS as NotificationService

    SCH->>BS: Trigger DailyPremiumCollectionJob at 06:00 UTC (runDate: today)
    BS->>BS: Query PremiumSchedule WHERE dueDate <= today AND status = PENDING AND retryCount < maxRetries
    BS->>BS: Partition records into processing batches of 500 for parallel execution

    loop For each PremiumSchedule batch record
        BS->>BS: Load PolicyHolder tokenized payment method from vault reference
        BS->>BS: Validate policy status is ACTIVE or GRACE_PERIOD before attempting charge

        BS->>PGW: POST /v1/payments/charge {vaultToken, amount, currency, idempotencyKey, policyReference}
        PGW->>PGW: Resolve vault token to payment instrument
        PGW->>PGW: Submit authorization to card network or bank ACH processor
        PGW->>PGW: Await authorization response (timeout: 30 seconds)

        alt Payment Authorized Successfully
            PGW-->>BS: ChargeResult {status: SUCCESS, transactionId, authCode, processedAt}
            BS->>BS: Create PaymentRecord with status=COMPLETED, amount, transactionId
            BS->>BS: Update PremiumSchedule status to PAID, set paidAt timestamp
            BS->>POS: PATCH /policies/{policyId}/billing-standing {lastPaymentDate, paidThrough, status: CURRENT}
            POS->>POS: Update Policy payment standing and clear any grace period flag
            BS->>NS: Publish PremiumCollectedEvent {policyId, scheduleId, amount, transactionId}
            NS->>NS: Render premium receipt document
            NS->>PH: Send premium receipt via email and push notification

        else Payment Declined or Network Failure
            PGW-->>BS: ChargeResult {status: FAILED, failureCode, failureReason, retryable}
            BS->>BS: Create PaymentRecord with status=FAILED, failureCode, attempt number
            BS->>BS: Increment PremiumSchedule retryCount

            alt retryCount equals 1 — First Failure
                BS->>BS: Schedule retry for T+3 days (next business day adjusted)
                BS->>POS: PATCH /policies/{policyId}/billing-standing {status: GRACE_PERIOD, gracePeriodEnds}
                POS->>POS: Set Policy to GRACE_PERIOD status (coverage remains active)
                BS->>NS: Publish PaymentFailedEvent {policyId, attempt: 1, nextRetryDate}
                NS->>PH: Send payment failure notice with retry date and update-payment-method link

            else retryCount equals 2 — Second Failure
                BS->>BS: Schedule final retry for T+7 days from original due date
                BS->>NS: Publish PaymentFailedEvent {policyId, attempt: 2, nextRetryDate, urgencyLevel: HIGH}
                NS->>PH: Send urgent payment reminder — final notice before lapse

            else retryCount equals 3 — Retry Limit Exceeded
                BS->>POS: PATCH /policies/{policyId}/status {status: LAPSED, lapsedAt, reason: NON_PAYMENT}
                POS->>POS: Update Policy status to LAPSED, suspend coverage
                BS->>NS: Publish PolicyLapsedEvent {policyId, lapsedAt, outstandingBalance}
                NS->>PH: Send lapse notice with reinstatement instructions and outstanding amount
                NS->>BP: Notify assigned broker of policy lapse for client follow-up
            end
        end
    end

    BS->>BS: Compile DailyCollectionReport (totalProcessed, totalCollected, failureCount, lapseCount)
    BS->>POS: POST /internal/reports/daily-collection (report payload for reconciliation)
    BS->>NS: Publish CollectionCompletedEvent to trigger operations dashboard refresh

    Note over SCH,NS: All PaymentRecord entries are streamed to Elasticsearch for real-time reconciliation dashboards
```

**Key observations:**
- Grace periods are product and jurisdiction specific; life insurance products in regulated markets require minimum 30-day grace periods by statute before a policy may be lapsed.
- Raw card data never enters the IMS; all payment instruments are referenced by opaque vault tokens managed by the PCI-DSS Level 1 compliant Payment Gateway.
- The `idempotencyKey` on each charge request prevents duplicate charges if the BillingService retries due to a network timeout after a successful gateway charge.
- Lapsed policies enter a reinstatement workflow where the `PolicyService` accepts backdated premium payment and restores `ACTIVE` status within the reinstatement window (configurable, typically 90 days).

---

## Diagram 4: Policy Renewal Flow

Policy renewal is initiated 60 days before expiry through a system-scheduled job. The system
re-underwrites the policy using updated risk data, generates a renewal premium quote incorporating
claims history adjustments (no-claims discounts or adverse claims loadings), and notifies the
customer and broker. The policyholder may accept, request modifications, or allow the policy to
lapse. Auto-renewal with pre-authorized payment is supported for policyholders who opt in at
inception.

```mermaid
sequenceDiagram
    autonumber
    participant SCH as System (Scheduler)
    participant POS as PolicyService
    participant UW as UnderwritingService
    participant PE as PricingEngine
    participant C as Customer
    participant BP as BrokerPortal
    participant NS as NotificationService

    SCH->>POS: Trigger RenewalNoticeJob (query: expiryDate = today + 60 days AND status = ACTIVE)
    POS->>POS: Retrieve eligible policies and filter out non-renewal-flagged records

    loop For each renewable Policy
        POS->>UW: POST /underwriting/renew-evaluate {policyId, renewalTerm, claimsHistory}
        UW->>UW: Reload risk profile with updated data (current age, renewal year, credit refresh)
        UW->>UW: Analyse claim frequency and severity from prior policy term
        UW->>UW: Apply renewal underwriting rules (automatic non-renewal triggers: 3+ at-fault claims)
        UW-->>POS: RenewalDecision {eligible, updatedRiskScore, coverageChanges[], exclusionChanges[]}

        alt Underwriting mandates non-renewal
            POS->>POS: Flag Policy as NON_RENEWAL_PENDING
            NS->>C: Issue statutory non-renewal notice (60-day advance as required by regulation)
            NS->>BP: Notify broker of non-renewal to facilitate alternative placement
        end

        POS->>PE: POST /pricing/renewal-quote {policyId, updatedRiskScore, renewalTerm, claimsData}
        PE->>PE: Retrieve current renewal rate tables (may differ from inception rates)
        PE->>PE: Apply No-Claims Discount (NCD) if claim-free in prior term
        PE->>PE: Apply adverse claims loading if claims exceeded threshold
        PE->>PE: Compute renewal gross premium, taxes, and net payable
        PE-->>POS: RenewalPremiumQuote {renewalPremium, priorPremium, changePercent, ncdApplied, validUntil}

        POS->>POS: Create RenewalQuote entity linked to expiring Policy
        POS->>NS: Publish RenewalNoticeEvent {policyId, renewalPremium, expiryDate, changePercent}
        NS->>C: Email 60-day renewal notice (premium comparison, coverage changes, endorsements)
        NS->>BP: Email broker renewal pack with commission projection and client summary
    end

    Note over C,BP: Customer has until 30 days before expiry to respond — auto-renewal skips this window

    C->>BP: Open broker portal to review renewal quote details
    BP->>POS: GET /policies/{policyId}/renewal-quote
    POS-->>BP: RenewalQuote details with coverage comparison table

    alt Customer accepts renewal without changes
        C->>BP: Confirm renewal acceptance
        BP->>POS: POST /policies/{policyId}/renew/accept {paymentMethodToken}
        POS->>POS: Validate renewal quote is not expired (30-day validity)
        POS->>BS: POST /billing/collect-renewal-premium {policyId, amount, paymentToken}
        BS->>PGW: Process renewal premium payment
        PGW-->>BS: PaymentResult {status: SUCCESS, transactionId}
        BS-->>POS: PaymentConfirmed {transactionId, paidAt}

        POS->>POS: Create new Policy entity for renewal period (linked to parent policy chain)
        POS->>POS: Set new effectiveDate (= old expiryDate + 1 day), new expiryDate
        POS->>POS: Archive expiring Policy version with status=EXPIRED
        POS->>POS: Carry forward active PolicyRider and PolicyEndorsement records

        POS->>NS: Publish PolicyRenewedEvent {newPolicyId, parentPolicyId, effectiveDate, expiryDate}
        NS->>C: Email renewed policy schedule, updated certificate of insurance, and receipt
        NS->>BP: Email policy renewal confirmation and commission credit

    else Customer requests coverage modifications before renewing
        C->>BP: Submit endorsement changes (increase sum insured, add rider, change deductible)
        BP->>POS: POST /policies/{policyId}/renewal-endorsement {endorsementDetails}
        POS->>UW: Re-evaluate underwriting with proposed endorsement changes
        UW-->>POS: Revised underwriting decision
        POS->>PE: Recalculate renewal premium incorporating endorsement delta
        PE-->>POS: Revised RenewalPremiumQuote {revisedPremium, endorsementPremium}
        POS->>NS: Publish RevisedRenewalQuoteEvent {policyId, revisedPremium}
        NS->>C: Email revised renewal offer with updated premium and coverage schedule

    else Customer declines or no response by 30-day deadline
        POS->>POS: Mark Policy as NON_RENEWAL at expiry date
        NS->>C: Send 30-day non-renewal reminder with market comparison offer
        NS->>BP: Notify broker of client non-renewal for retention follow-up
    end

    Note over POS,NS: PolicyRenewedEvent triggers ReinsuranceService to update treaty cession records for new policy period
```

**Key observations:**
- Auto-renewal with pre-authorized payment bypasses the explicit acceptance step; the customer receives a notification rather than a quote awaiting response, with a cancellation window of 14 days post-renewal.
- Renewal premium increases exceeding 20% above the prior year's premium trigger a mandatory broker review workflow before the notice is dispatched to the customer.
- No-Claims Discount (NCD) is tracked on the `Policy` entity as a running field and transferred to the renewal quote automatically by the `PricingEngine`.
- All renewal lifecycle events are published to Kafka topic `policy-lifecycle-events` for consumption by the `ReportingService` for IFRS 17 contract boundary and premium allocation calculations.

---

*Document version: 1.0 | Domain: Insurance Management System | Classification: Internal Architecture Reference*
