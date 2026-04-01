# State Machine Diagrams — Digital Banking Platform

All state machines are modelled as `stateDiagram-v2` using Mermaid. Each state includes entry/exit conditions, guard clauses, and regulatory constraints.

---

## Account Lifecycle State Machine

An account progresses from creation through identity verification, operational use, and eventual closure. Regulators mandate documented transitions, especially for dormancy and closure processes.

```mermaid
stateDiagram-v2
    [*] --> PendingKYC : Customer submits onboarding application\n[CIP requirements triggered — BSA §326]

    PendingKYC --> Active : KYC documents verified, risk rating LOW/MEDIUM\nID document authentic, watchlist clear, address confirmed\n[Account funded with opening deposit ≥ $25]

    PendingKYC --> Rejected : KYC verification failed — document fraud, sanctions hit,\nhigh-risk jurisdiction, or verification expired after 30 days\n[Adverse action notice sent — ECOA Reg B]

    PendingKYC --> PendingEDD : Risk rating = HIGH — PEP match, unusual source of funds,\nhigh-risk country of origin\n[Enhanced Due Diligence required — 30-day SLA]

    PendingEDD --> Active : EDD review completed, risk accepted by MLRO\n[EDD documentation archived 5 years — BSA record retention]

    PendingEDD --> Rejected : EDD review results in risk rejection\nor customer fails to respond within 30 days

    state Active {
        [*] --> NormalOperations
        NormalOperations --> SoftLimit : Daily transaction volume > 90% of limit\n[Proactive notification triggered]
        SoftLimit --> NormalOperations : Volume normalizes or limit increased
        NormalOperations --> PendingKYCRefresh : KYC record age > 2 years (standard)\nor > 1 year (high-risk customer)\n[Trigger periodic review — FinCEN guidance]
        PendingKYCRefresh --> NormalOperations : Periodic KYC refresh completed, risk rating maintained
        PendingKYCRefresh --> Frozen : Customer fails to respond to KYC refresh\nwithin 30-day grace period
    }

    Active --> Frozen : Compliance hold placed\n(AML alert, court order, fraud investigation,\nOFAC match, suspicious activity report filed)\n[Access to funds restricted, customer notified per legal constraints]

    Active --> Frozen : Customer-initiated lock (lost card concern, suspicious activity reported)

    Active --> Dormant : No customer-initiated transactions for 12 consecutive months\nAND balance < $50 OR no customer contact for 24 months\n[Dormancy notice sent 30 days prior — Unclaimed Property Law]

    Frozen --> Active : Compliance hold lifted by authorized compliance officer\n(investigation closed, no adverse finding)\n[Documented approval required — dual control]

    Frozen --> Dormant : Account remains frozen AND no activity for 12 months

    Frozen --> Closed : Regulatory instruction or court order mandating closure\nOR customer request after compliance hold lifted

    Dormant --> Active : Customer initiates any transaction\nOR contacts customer service with identity verification\n[KYC refresh required if dormant > 24 months]

    Dormant --> EscheatedToState : No customer contact for state-mandated abandonment period\n(3–7 years depending on jurisdiction)\n[Funds remitted to state unclaimed property office\n— annual filing required]

    Dormant --> Closed : Customer requests closure of dormant account

    EscheatedToState --> [*] : Funds transferred to state, account record retained 7 years

    Active --> PendingClosure : Customer submits account closure request\nOR product team initiates programmatic closure\n[30-day notice period for accounts with recurring payments]

    PendingClosure --> Closed : All pending transactions settled, recurring payments cancelled,\nlinked cards deactivated, direct deposit re-routed\n[Final statement generated, closing balance disbursed]

    PendingClosure --> Active : Customer cancels closure request within 30-day window

    Closed --> [*] : Account record retained 7 years per BSA/AML requirements\nPII minimized after retention period expires (GDPR/CCPA)

    Rejected --> [*] : Application record retained 5 years\nAdverse action notice retained 25 months (ECOA)
```

**Key Regulatory Constraints:**
- Dormancy thresholds vary by US state (NY: 3 years, CA: 3 years, TX: 3 years).
- Escheatment filing is an annual obligation; late filing attracts penalties.
- Frozen accounts must have legal basis documented; blanket freezes without documented grounds expose the institution to liability.
- KYC refresh cadence is risk-based: standard customers every 2 years, high-risk annually, EDD customers reviewed on every material event.

---

## Transaction Lifecycle State Machine

Every transaction — domestic transfer, card payment, or bill pay — follows this state machine. The design ensures exactly-once processing semantics and provides clear audit points for reconciliation.

```mermaid
stateDiagram-v2
    [*] --> Initiated : Customer submits payment instruction\n[Idempotency key generated and persisted atomically]

    Initiated --> FraudReview : Fraud score >= 0.50 OR amount >= $10,000\nOR new payee first transaction\nOR unusual geo/time pattern\n[Async ML scoring — SLA 500ms]

    Initiated --> Processing : Fraud score < 0.50 AND no velocity triggers\nAND amount < transaction limit\n[Auto-approved, proceed to processing]

    FraudReview --> Processing : Fraud score < 0.85 AND no step-up required\nOR step-up authentication completed successfully\n[Fraud review decision logged for model feedback]

    FraudReview --> StepUpRequired : Fraud score 0.50–0.84 — challenge required\n[OTP sent to registered device]

    StepUpRequired --> FraudReview : Customer completes OTP/biometric challenge\n[Re-evaluate with step-up signal]

    StepUpRequired --> FraudBlocked : Customer fails 3 step-up attempts\nOR challenge timeout (10 minutes)\n[Suspicious activity flag set]

    FraudReview --> FraudBlocked : Fraud score >= 0.85\nOR known fraud pattern match\nOR device on blocklist\n[SAR consideration triggered if > $5,000]

    FraudBlocked --> Reversed : Fraud confirmed — funds recovered if debit already occurred\n[Chargeback or ACH return initiated]

    FraudBlocked --> [*] : Transaction record retained, customer notified

    Processing --> AMLHold : AML screening returns HIT\n(sanctions match, structuring pattern, PEP transaction)\n[Compliance officer review — up to 3 business days]

    AMLHold --> Processing : AML hold cleared by compliance officer\n[Documented decision, false positive logged]

    AMLHold --> Blocked : AML hold escalated — transaction permanently blocked\n[SAR filed if suspicious — FinCEN 30-day deadline]

    Blocked --> [*] : Funds returned to source account, record retained 5 years

    Processing --> PendingSettlement : Debit written to ledger, payment instruction submitted to rail\n(ACH file transmitted, Fedwire message sent, card auth placed)\n[Point of no return for ACH next-day]

    PendingSettlement --> Completed : Settlement confirmation received from payment rail\n(ACH RDFI acknowledgment, Fedwire OMAD received, card settled)\n[Credit written to destination, notification triggered]

    PendingSettlement --> PendingReturn : ACH return received (R01–R29)\nOR Fedwire rejection\nOR card dispute initiated\n[Reversal initiated within 2 business days]

    PendingReturn --> Reversed : Debit reversal written to source account\nOrigination fee refunded\n[Return entry submitted to ACH network]

    PendingReturn --> Disputed : Customer or counterparty initiates dispute\nChargeback / Reg E claim filed\n[60-day window for consumer to dispute (Reg E)]

    Disputed --> Reversed : Dispute resolved in favor of initiating party\n[Provisional credit made permanent, merchant charged back]

    Disputed --> Completed : Dispute resolved — transaction valid\n[Provisional credit reversed if applied]

    Completed --> Disputed : Customer files post-settlement dispute\n(Reg E unauthorized transaction claim — 60 days)\n[Provisional credit issued within 10 business days]

    Completed --> [*] : Transaction record immutable, retained 7 years

    Reversed --> [*] : Reversal record retained alongside original transaction
```

---

## Loan Lifecycle State Machine

Loan states capture the full origination, servicing, and resolution lifecycle with payment-tracking granularity required for GAAP loan loss provisioning and regulatory capital calculation (Basel III).

```mermaid
stateDiagram-v2
    [*] --> ApplicationSubmitted : Customer submits loan application\n[Hard credit inquiry authorized and executed]

    ApplicationSubmitted --> UnderwritingInProgress : Application passes initial eligibility\n(FICO pull successful, income stated, KYC verified)\n[24-hour SLA for automated decisions]

    ApplicationSubmitted --> Withdrawn : Customer withdraws application before decision\n[Hard inquiry already on credit file — disclosed at application]

    UnderwritingInProgress --> Approved : Automated decisioning engine approves\n(FICO >= 620, DTI <= 43%, no active default)\n[TILA disclosure generated — APR, fees, payment schedule]

    UnderwritingInProgress --> ConditionalApproval : Approved subject to conditions\n(income verification document, pay stubs, bank statements)\n[30-day window to fulfill conditions]

    UnderwritingInProgress --> Declined : Policy rejection — FICO below threshold, DTI too high,\nderogatory mark within 24 months, insufficient income\n[Adverse action notice mandatory — ECOA Reg B, 30-day SLA]

    ConditionalApproval --> Approved : All conditions satisfied and verified\n[Re-underwrite if income delta > 10%]

    ConditionalApproval --> Declined : Customer fails to fulfill conditions within 30 days\n[Adverse action notice sent]

    Approved --> OfferExpired : Customer does not accept offer within 72 hours\n[Hard inquiry remains on credit file]

    Approved --> Active : Customer accepts offer, signs disclosures electronically,\ndisbursement processed to linked account\n[Loan appears on credit bureau tradeline]

    OfferExpired --> [*] : Application archived, re-application allowed after 30 days

    Declined --> [*] : Adverse action notice sent and retained 25 months (ECOA)

    Withdrawn --> [*] : Application record retained 25 months

    state Active {
        [*] --> Current
        Current --> GracePeriod : Payment not received by due date\n[Reminder notification sent day 1]
        GracePeriod --> Current : Payment received within 15-day grace period\n[No credit bureau reporting of delinquency]
        GracePeriod --> PastDue30 : Payment not received within grace period\n[Delinquency reported to credit bureaus — 30 days past due]
        PastDue30 --> Current : All overdue payments plus late fee received\n[Credit bureau update — delinquency cured]
        PastDue30 --> PastDue60 : No payment for 60 days
        PastDue60 --> PastDue90 : No payment for 90 days\n[Collection escalation, hardship program offered]
    }

    Active --> PaidOff : Final scheduled payment received\nOR customer makes full prepayment\n[Lien released, collateral returned if secured loan\nCredit bureau updated — account closed in good standing]

    Active --> ChargedOff : Loan 120+ days past due\n(or 180 days for mortgage)\n[GAAP charge-off — removed from earning assets\nContinue collection attempts, 1099-C may be issued]

    Active --> Restructured : Customer hardship plan approved\n(rate reduction, payment deferral, term extension)\n[TDR accounting treatment if below market rate — GAAP ASC 310-40]

    Restructured --> Active : Customer completes restructure period successfully\n[Performing classification restored]

    Restructured --> ChargedOff : Customer defaults during restructure period

    ChargedOff --> RecoveryPartial : Partial recovery from collections agency or legal action\n[Recovery recognized in income statement]

    ChargedOff --> RecoveryFull : Full outstanding balance recovered\n[Rare — typically occurs within 12 months of charge-off]

    ChargedOff --> WrittenOff : No recovery after 7 years\n[Record archived per legal requirements]

    PaidOff --> [*] : Loan record retained 7 years\nCredit bureau tradeline retained per FCRA (7 years for delinquencies)

    WrittenOff --> [*] : Record retained 7 years from origination date
```

---

## Debit Card Lifecycle State Machine

Card state management is tightly coupled to card network (Visa/Mastercard) system of record updates. Every state change must be reflected in the card network's card management system within 2 minutes to prevent authorization inconsistencies.

```mermaid
stateDiagram-v2
    [*] --> Requested : Customer requests new debit card via app/web/branch\nOR replacement requested for damaged/expired card\n[Card personalization data sent to card bureau]

    Requested --> ProductionQueued : Card bureau accepts order\n[Physical card enters production queue — 3–5 business days]

    ProductionQueued --> Shipped : Card personalized, mailed via USPS First Class\n[Tracking number generated, shipment notification sent]

    Shipped --> PendingActivation : Card delivered (tracking confirmed OR estimated delivery +2 days)\n[Customer prompted to activate via app, IVR, or ATM]

    PendingActivation --> Active : Customer activates card — validates last 4 SSN and billing ZIP\nOR PIN set at ATM\n[Card network: status = 00 ACTIVE\nVelocity limits initialized]

    PendingActivation --> Expired : Card reaches expiry date without activation\n[Replacement card auto-issued if account in good standing]

    Requested --> Cancelled : Customer cancels card request before production\nOR account closed before card shipped\n[Card bureau notified to halt production]

    state Active {
        [*] --> UnderLimit
        UnderLimit --> ApproachingLimit : Daily spend > 80% of limit\n[Advisory notification sent]
        ApproachingLimit --> UnderLimit : New day reset OR limit increased
        UnderLimit --> TravelMode : Customer enables travel notification\n[Geographic restrictions relaxed for declared countries]
        TravelMode --> UnderLimit : Travel period expires
    }

    Active --> TemporarilyBlocked : Customer locks card via mobile app (self-service)\n[Card network: status = 41 PICK UP — lost\nAll new authorizations declined]

    TemporarilyBlocked --> Active : Customer unlocks card via mobile app\n[Verification required: PIN or biometric]

    Active --> Blocked : Fraud detected — card compromised\n(confirmed card-present skimming, CNP fraud pattern)\nOR customer reports card lost/stolen\n[Card network: status = 41/43 — immediate effect\nReplacement card auto-ordered]

    Active --> Blocked : Compliance hold on account (AML/OFAC)\n[All card authorizations declined]

    Blocked --> ReplacementIssued : Replacement card requested\n[Blocked card permanently disabled in card network\nNew PAN generated, tokens updated via VISA/MC token service]

    ReplacementIssued --> Requested : New card enters production cycle\n[Old card PANs invalidated in all payment wallets]

    Active --> Expired : Card reaches expiry date (last day of expiry month)\n[Auto-renewal card issued 45 days prior if account active\nExpiring card continues to work until end of month]

    Expired --> Requested : Renewal card auto-issued\n[New PAN or same PAN with new expiry — based on product config]

    Active --> Cancelled : Customer closes account OR product cancellation\nOR regulatory instruction\n[Card network notified immediately\nLinked digital wallets (Apple Pay, Google Pay) tokens revoked]

    Blocked --> Cancelled : Account closed while card in blocked state

    Cancelled --> [*] : Card record retained 7 years\nPAN data purged per PCI-DSS after retention period

    Expired --> [*] : If no renewal — record retained 7 years

    ReplacementIssued --> [*] : Old card record linked to new card issuance record
```

---

## KYC Record Lifecycle State Machine

KYC records are independent entities from accounts — a single customer may have multiple KYC records (initial, periodic refresh, EDD). Each record has its own state and validity period.

```mermaid
stateDiagram-v2
    [*] --> DocumentSubmitted : Customer uploads identity documents\nvia secure upload portal or mobile SDK\n[Documents encrypted at rest — AES-256\nAudit log entry created]

    DocumentSubmitted --> OCRProcessing : Document images queued for automated extraction\n[Jumio/Onfido API called — SLA 60 seconds]

    OCRProcessing --> UnderReview : OCR extraction successful\nDocument data extracted: name, DOB, document number, expiry\n[Automated checks initiated]

    OCRProcessing --> DocumentRejected : OCR failure — poor image quality, unsupported document type,\nglare/obstruction, document too small\n[Customer prompted to re-upload]

    DocumentRejected --> DocumentSubmitted : Customer re-submits improved document images\n[3 attempts allowed before manual review required]

    DocumentRejected --> ManualReview : 3 automated OCR failures\n[Escalated to KYC analyst]

    state UnderReview {
        [*] --> LivenessCheck
        LivenessCheck --> FaceMatch : Liveness challenge passed (active liveness — head turn, blink)\n[Deepfake detection model score < 0.3]
        LivenessCheck --> LivenessFailed : Passive liveness failed OR deepfake score >= 0.3\n[Fraud flag raised]
        FaceMatch --> DocumentAuthenticity : Face matches document photo (similarity >= 85%)\n[Biometric comparison via ISO 30107-3 compliant engine]
        FaceMatch --> FaceMatchFailed : Face match score < 85%\n[Potential impersonation — escalate]
        DocumentAuthenticity --> WatchlistScreen : Document security features validated\n(holograms, MRZ checksum, UV features)\n[ML classifier confidence >= 0.90]
        DocumentAuthenticity --> DocumentSuspect : Security feature validation failed\n[Possible document fraud]
        WatchlistScreen --> AddressVerification : OFAC / UN / EU / HMT / PEP / Adverse Media clear\n[Fuzzy match threshold 0.92]
        WatchlistScreen --> SanctionsHit : Watchlist match found\n[Escalate to compliance officer immediately]
        AddressVerification --> ReviewComplete : Address verified via credit bureau / utility bill / bank statement\n[Full residential address confirmed]
        AddressVerification --> AddressFailed : Address unverifiable — PO Box, non-standard format,\naddress not matching document\n[Request alternate proof of address]
    }

    UnderReview --> AdditionalInfoRequired : Automated checks incomplete — borderline results,\nexpired document (< 30 days), address mismatch,\nname variation requiring explanation\n[Customer notified with specific requirements\n14-day response window]

    AdditionalInfoRequired --> UnderReview : Customer provides additional information or documents\n[Review clock resets]

    AdditionalInfoRequired --> Abandoned : Customer fails to respond within 14 days\n[Account creation blocked until KYC completed]

    Abandoned --> DocumentSubmitted : Customer re-initiates KYC process\n[Previous submission archived]

    UnderReview --> ManualReview : Automated review inconclusive\nOR EDD triggered (PEP, high-risk country, high transaction volume)\nOR watchlist near-match requires human judgment\n[Senior KYC analyst assigned — 72-hour SLA for standard\n24-hour SLA for time-sensitive account opening]

    ManualReview --> Approved : KYC analyst clears — identity confirmed, watchlist clear,\nrisk rating assigned (LOW/MEDIUM/HIGH)\n[Approval recorded with analyst ID and timestamp]

    ManualReview --> AdditionalInfoRequired : Analyst requires more documentation\n[Formal information request sent]

    ManualReview --> Rejected : Identity could not be verified, document fraud confirmed,\nsanctions hit confirmed, risk unacceptable\n[Adverse action letter sent\nApplication archived for 5 years — BSA requirements]

    UnderReview --> Approved : All automated checks passed — straight-through processing\n[Risk rating = LOW, no manual intervention needed]

    SanctionsHit --> Rejected : Confirmed sanctions match after compliance review\n[SAR consideration — FinCEN guidance]

    LivenessFailed --> Rejected : Confirmed presentation attack — fraud flagged\n[IP/device blacklisted, referral to fraud team]

    Approved --> Expired : KYC record age exceeds refresh cadence:\nLOW risk: 2 years, MEDIUM risk: 18 months, HIGH risk: 12 months\n[Periodic review triggered]

    Expired --> DocumentSubmitted : Customer re-enters KYC refresh flow\n[Account may be restricted pending refresh completion]

    Approved --> Superseded : Newer KYC record approved for same customer\n[Previous record archived, superseded status set]

    Rejected --> [*] : Record retained 5 years (BSA) with rejection reason and evidence

    Abandoned --> [*] : Record retained 2 years

    Approved --> [*] : Record retained for duration of customer relationship + 7 years post-closure
```
