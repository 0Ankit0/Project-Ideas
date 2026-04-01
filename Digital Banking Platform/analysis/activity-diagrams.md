# Activity Diagrams — Digital Banking Platform

| Field | Value |
|---|---|
| Document ID | DBP-AD-001 |
| Version | 1.0 |
| Status | Approved |
| Owner | Business Analysis |
| Last Updated | 2025-01-15 |

## Overview

This document presents four activity diagrams modelling the primary end-to-end workflows of the Digital Banking Platform. Each diagram is expressed in Mermaid flowchart notation and is followed by a detailed activity-node table identifying the responsible actor, the executing system component, and any applicable business rules or SLA constraints.

---

## Account Onboarding Flow

This diagram models the complete journey from application download through to active account creation, including all error and exception paths encountered during document processing and KYC verification.

```mermaid
flowchart TD
    START([Customer Downloads App]) --> REG[Register: Enter Email and Phone]
    REG --> OTP_SEND[Platform Sends OTP to Phone]
    OTP_SEND --> OTP_VERIFY{OTP Entered Correctly?}
    OTP_VERIFY -->|No - 3 attempts exceeded| OTP_LOCK[Account Locked for 15 Minutes]
    OTP_LOCK --> OTP_RETRY([Customer Retries After Cooldown])
    OTP_VERIFY -->|Yes| PROFILE[Customer Completes Personal Details Form]
    PROFILE --> DOC_CHOICE{Select Document Type}
    DOC_CHOICE -->|Passport| DOC_UP[Upload Passport Front Page]
    DOC_CHOICE -->|National ID| DOC_BOTH[Upload ID Front and Back]
    DOC_UP --> DOC_QUAL{Image Quality Check}
    DOC_BOTH --> DOC_QUAL
    DOC_QUAL -->|Fail: Blur or Glare| DOC_RETRY[Prompt: Retake with Guidance]
    DOC_RETRY --> DOC_UP
    DOC_QUAL -->|Pass| SELFIE[Selfie and Liveness Challenge]
    SELFIE --> LIVE_CHECK{Liveness Detection Result}
    LIVE_CHECK -->|Fail: Attempt 1 or 2| LIVE_RETRY[Prompt: Retry Liveness Check]
    LIVE_RETRY --> SELFIE
    LIVE_CHECK -->|Fail: 3rd Attempt| MANUAL_Q[Place Case in Manual Review Queue]
    MANUAL_Q --> COMPLIANCE_REVIEW[Compliance Officer Conducts Manual Review]
    COMPLIANCE_REVIEW --> MANUAL_DEC{Manual Decision}
    MANUAL_DEC -->|Reject| KYC_REJ[KYC Status Set to REJECTED]
    KYC_REJ --> REJECT_NOTIFY[Send Rejection Notification with Reason]
    REJECT_NOTIFY --> END_REJECT([End: Application Rejected])
    MANUAL_DEC -->|Approve| KYC_OK
    LIVE_CHECK -->|Pass| KYC_SUBMIT[Submit to KYC Provider: Onfido / Jumio]
    KYC_SUBMIT --> KYC_PROC[KYC Provider Runs OCR and Biometric Match]
    KYC_PROC --> KYC_DEC{KYC Provider Decision}
    KYC_DEC -->|Refer| REFER_Q[Place Case in Compliance Review Queue]
    REFER_Q --> COMPLIANCE_REVIEW
    KYC_DEC -->|Reject| KYC_REJ
    KYC_DEC -->|Approve| KYC_OK[KYC Status Set to APPROVED]
    KYC_OK --> ACC_CREATE[Core Banking: Create Account and Assign IBAN]
    ACC_CREATE --> VIRTUAL_CARD[Provision Virtual Debit Card]
    VIRTUAL_CARD --> WELCOME[Send Welcome Notification with IBAN and Card Details]
    WELCOME --> END_OK([End: Account Active])
```

### Onboarding Activity Node Reference

| Node | Activity | Actor | System Component | Notes |
|---|---|---|---|---|
| Register | Capture email, phone, and password | Customer | Auth Service | Email uniqueness validated in real time |
| Send OTP | Generate and dispatch 6-digit OTP | Platform | Notification Service → SMS Provider | OTP valid for 10 minutes, max 3 resends |
| OTP Verify | Validate OTP against time-based hash | Platform | Auth Service | Lockout applied after 3 consecutive failures |
| Personal Details Form | Collect full name, DoB, address, nationality | Customer | Onboarding Service | Fields validated against ISO 3166 country codes |
| Document Upload | Capture front/back images of ID document | Customer | KYC Service | Resolution ≥ 640×480, file ≤ 10 MB per image |
| Image Quality Check | Assess blur, glare, cropping, and OCR readability | Platform | KYC Service (pre-check) | Synchronous; result returned in < 2 seconds |
| Liveness Challenge | Prompt customer to perform head-movement sequence | Customer | KYC Service | Random prompts to defeat replay attacks |
| KYC Provider Processing | OCR data extraction, face match, liveness scoring | KYC Provider | Onfido / Jumio | Async; webhook callback within 60 seconds |
| Manual Review | Compliance officer reviews evidence | Compliance Officer | Compliance Portal | SLA: decision within 2 business days |
| Account Creation | Open account ledger record and allocate IBAN | Platform | Core Banking Integration | Atomic; rolls back if card provisioning fails |
| Virtual Card Provision | Allocate PAN from VISA/MC BIN range, encrypt and store | Platform | Card Service | Card active within 60 seconds of account creation |
| Welcome Notification | Dispatch multi-channel welcome message | Platform | Notification Service | Push, email, and SMS dispatched simultaneously |

---

## Money Transfer Flow

This diagram covers all transfer types — internal between own accounts, domestic via Faster Payments, and international via SWIFT — including fraud screening, compliance gating, and failure paths.

```mermaid
flowchart TD
    START([Customer Initiates Transfer]) --> AUTH[Authenticate: Biometric or PIN]
    AUTH --> AUTH_OK{Authentication Passed?}
    AUTH_OK -->|No| AUTH_FAIL[Show Authentication Error]
    AUTH_FAIL --> AUTH_LOCK{Max Attempts Reached?}
    AUTH_LOCK -->|Yes| SESSION_END([Session Terminated])
    AUTH_LOCK -->|No| AUTH
    AUTH_OK -->|Yes| TRANS_TYPE{Select Transfer Type}
    TRANS_TYPE -->|Internal| INT_ACCS[Select Source and Destination Accounts]
    TRANS_TYPE -->|Domestic| DOM_BEN[Enter Sort Code and Account Number]
    TRANS_TYPE -->|International| INTL_BEN[Enter IBAN and BIC / SWIFT Code]
    INT_ACCS --> AMOUNT[Enter Amount]
    DOM_BEN --> COP[Confirmation of Payee Check]
    COP --> COP_DEC{Payee Name Matched?}
    COP_DEC -->|No Match| COP_WARN[Display Warning: Name Mismatch]
    COP_WARN --> COP_CONF{Customer Confirms to Proceed?}
    COP_CONF -->|No| CANCEL([Transfer Cancelled])
    COP_CONF -->|Yes| AMOUNT
    COP_DEC -->|Match| AMOUNT
    INTL_BEN --> FX_QUOTE[Request Live FX Rate and Fee Quote]
    FX_QUOTE --> FX_SHOW[Display Exchange Rate, Fee, and Net Amount]
    FX_SHOW --> AMOUNT
    AMOUNT --> REVIEW[Customer Reviews Transfer Summary]
    REVIEW --> OTP2[Confirm with OTP or Biometric Second Factor]
    OTP2 --> SCA_OK{SCA Passed?}
    SCA_OK -->|No| SCA_FAIL[Reject: SCA Failed]
    SCA_FAIL --> END_SCA([End: Transfer Not Submitted])
    SCA_OK -->|Yes| FUND_CHECK{Sufficient Available Funds?}
    FUND_CHECK -->|No| INSUF[Reject: Insufficient Funds Notification]
    INSUF --> END_INSUF([End: Transfer Declined])
    FUND_CHECK -->|Yes| BRE_CHECK[Business Rule Engine: Apply Tier Limits and Velocity Rules]
    BRE_CHECK --> BRE_DEC{Rules Passed?}
    BRE_DEC -->|Fail: Limit Exceeded| LIMIT_REJ[Reject: Daily Limit Message]
    LIMIT_REJ --> END_LIMIT([End: Transfer Declined])
    BRE_DEC -->|Pass| FRAUD_CHECK[Fraud Engine: Score Transaction]
    FRAUD_CHECK --> FRAUD_DEC{Fraud Score}
    FRAUD_DEC -->|High Risk: Block| FRAUD_BLOCK[Block Transfer and Raise Alert]
    FRAUD_BLOCK --> FRAUD_NOTIFY[Send Fraud Alert to Customer]
    FRAUD_NOTIFY --> END_FRAUD([End: Transfer Blocked])
    FRAUD_DEC -->|Low Risk: Proceed| SANCTIONS[Sanctions Screening: OFAC and HM Treasury]
    SANCTIONS --> SANC_DEC{Sanctions Match Found?}
    SANC_DEC -->|Match| SANC_BLOCK[Block Transfer and Raise Compliance Alert]
    SANC_BLOCK --> END_SANC([End: Transfer Blocked])
    SANC_DEC -->|Clear| SUBMIT_CBS[Post Debit to Core Banking Ledger]
    SUBMIT_CBS --> RAIL_ROUTE{Route to Payment Rail}
    RAIL_ROUTE -->|Internal| CBS_CREDIT[Post Credit to Destination Account]
    CBS_CREDIT --> CONFIRM_INT[Create Transaction Records]
    RAIL_ROUTE -->|Domestic| FPS_SUBMIT[Submit to Faster Payments Service]
    FPS_SUBMIT --> FPS_CONFIRM[Receive Settlement Confirmation]
    FPS_CONFIRM --> CONFIRM_DOM[Update Transaction Status to SETTLED]
    RAIL_ROUTE -->|International| SWIFT_MSG[Compose and Dispatch SWIFT MT103]
    SWIFT_MSG --> SWIFT_ACK[Receive UETR Tracking Reference]
    SWIFT_ACK --> CONFIRM_INTL[Update Transaction Status to SENT]
    CONFIRM_INT --> NOTIFY_OK[Send Transfer Confirmation Notification]
    CONFIRM_DOM --> NOTIFY_OK
    CONFIRM_INTL --> NOTIFY_OK
    NOTIFY_OK --> END_OK([End: Transfer Complete])
```

### Money Transfer Activity Node Reference

| Node | Activity | Actor | System Component | SLA / Rule |
|---|---|---|---|---|
| Authenticate | Biometric or PIN challenge | Customer | Auth Service | Session token valid 15 minutes |
| Transfer Type Selection | Choose internal, domestic, or international | Customer | Payment UI | Route determines downstream processing path |
| Confirmation of Payee | Lookup beneficiary name against sort code and account | Platform | Payment Service → CoP API | Synchronous; < 2 s |
| FX Quote | Fetch live rate from FX pricing engine | Platform | FX Service | Quote valid for 30 seconds |
| SCA Challenge | OTP or biometric strong customer authentication | Customer / Platform | Auth Service | Mandatory per PSD2 SCA requirements |
| Funds Check | Verify available balance minus pending holds | Platform | Core Banking Integration | Synchronous balance read |
| Business Rule Engine | Evaluate daily limit, velocity, and tier rules | Platform | BRE | Synchronous; < 100 ms |
| Fraud Engine | Score transaction against ML model | Platform | Fraud Engine | Synchronous; < 200 ms |
| Sanctions Screening | Check names and IBANs against sanctions lists | Platform | Compliance Service | Synchronous; < 500 ms; updated lists every 4 h |
| CBS Debit Posting | Reserve and post debit on source account ledger | Platform | Core Banking Integration | Must succeed before rail submission |
| FPS Submission | Send Faster Payments instruction | Platform | Payment Rail Adapter | Settlement confirmed < 20 s |
| SWIFT MT103 Dispatch | Compose and send international payment message | Platform | SWIFT Gateway | UETR returned within 5 s of dispatch |
| Confirmation Notification | Dispatch settlement confirmation to customer | Platform | Notification Service | Within 30 s of settlement |

---

## Loan Application Flow

This diagram covers the complete personal loan journey from eligibility check through to active loan disbursement, including soft credit pull, full application, counter-offer, and rejection paths.

```mermaid
flowchart TD
    START([Customer Opens Loan Section]) --> ELIG_CHECK[Run Soft Credit Enquiry: No File Impact]
    ELIG_CHECK --> ELIG_DEC{Eligibility Assessment}
    ELIG_DEC -->|Ineligible| INELIG_MSG[Display Ineligibility Reason and Improvement Tips]
    INELIG_MSG --> END_INEL([End: Customer Advised])
    ELIG_DEC -->|Eligible| SHOW_INDIC[Display Indicative Loan Ranges and APRs]
    SHOW_INDIC --> APPLY_DEC{Customer Proceeds to Full Application?}
    APPLY_DEC -->|No| END_BROWSE([End: Customer Exits])
    APPLY_DEC -->|Yes| LOAN_DETAILS[Customer Enters: Amount, Purpose, Term]
    LOAN_DETAILS --> INCOME[Capture Income and Employment Details]
    INCOME --> HARD_PULL[Perform Hard Credit Pull: Equifax / Experian]
    HARD_PULL --> INT_SCORE[Internal Credit Scoring and Affordability Model]
    INT_SCORE --> SCORE_DEC{Lending Decision}
    SCORE_DEC -->|Decline: Below Threshold| DECLINE[Generate Decline Decision]
    DECLINE --> DECLINE_NOTIFY[Notify Customer with Primary Reason and Cooling-Off Guidance]
    DECLINE_NOTIFY --> END_DEC([End: Application Declined])
    SCORE_DEC -->|Counter Offer: Reduced Amount or Higher Rate| COUNTER[Generate Counter-Offer]
    COUNTER --> COUNTER_SHOW[Present Counter-Offer to Customer]
    COUNTER_SHOW --> COUNTER_DEC{Customer Accepts Counter-Offer?}
    COUNTER_DEC -->|No| END_COUNTER([End: Offer Declined by Customer])
    COUNTER_DEC -->|Yes| OFFER_GEN
    SCORE_DEC -->|Approve| OFFER_GEN[Generate Binding Loan Offer: APR, Instalment, Total Cost]
    OFFER_GEN --> KYC_RECHECK{KYC Status Still Valid?}
    KYC_RECHECK -->|No: Expired or Downgraded| KYC_BLOCK[Block Offer Pending KYC Refresh]
    KYC_BLOCK --> KYC_NOTIFY[Notify Customer to Re-verify KYC]
    KYC_NOTIFY --> END_KYC([End: Awaiting KYC Refresh])
    KYC_RECHECK -->|Yes| SHOW_OFFER[Present Binding Offer to Customer]
    SHOW_OFFER --> CUST_DEC{Customer Decision}
    CUST_DEC -->|Decline Offer| OFFER_DECLINE([End: Offer Declined])
    CUST_DEC -->|Accept Offer| SIGN[Customer Signs Digital Loan Agreement]
    SIGN --> AGREEMENT_REC[Record Executed Agreement with Timestamp]
    AGREEMENT_REC --> DISBURSE[Disburse Principal to Current Account via CBS]
    DISBURSE --> LOAN_CREATE[Create Active Loan Record with Repayment Schedule]
    LOAN_CREATE --> DISBURSE_NOTIFY[Send Disbursement Confirmation to Customer]
    DISBURSE_NOTIFY --> END_OK([End: Loan Active])
```

### Loan Application Activity Node Reference

| Node | Activity | Actor | System Component | Notes |
|---|---|---|---|---|
| Soft Credit Enquiry | Request indicative credit profile without hard footprint | Platform | Loan Service → Credit Bureau | No impact on customer credit file |
| Eligibility Assessment | Evaluate score, account history, and active defaults | Platform | Loan Service / Scoring Engine | Rule BR-005 applied |
| Loan Detail Capture | Amount, purpose, requested term | Customer | Loan Application UI | Purpose codes per Consumer Credit Act schedule |
| Hard Credit Pull | Formal credit enquiry, leaves footprint | Platform | Credit Bureau Integration | Requires customer explicit consent |
| Internal Scoring | Affordability model combining bureau data and internal history | Platform | Credit Decisioning Engine | Proprietary ML model, updated quarterly |
| Counter-Offer Generation | Produce reduced-amount or adjusted-rate alternative offer | Platform | Loan Service | Requires risk committee threshold approval |
| Binding Offer | Compliant offer including APR, APRC, monthly instalment, total repayable | Platform | Loan Service | Consumer Credit Act pre-contractual disclosure |
| KYC Re-check | Confirm KYC tier still valid and not expired | Platform | KYC Service | Loan disbursement blocked if KYC status changed |
| Digital Agreement Sign | Customer accepts and e-signs SECCI and loan agreement | Customer | Document Service | Qualified electronic signature, stored immutably |
| Disbursement | Transfer principal to nominated current account | Platform | Core Banking Integration | Completed within 2 hours of agreement execution |
| Loan Record Creation | Persist loan, repayment schedule, and lien against account | Platform | Loan Service / CBS | Amortisation schedule generated at creation |

---

## Card Issuance Flow

This diagram models both the virtual and physical card issuance journeys from customer request through BIN allocation, card record creation, delivery, and activation.

```mermaid
flowchart TD
    START([Customer Requests New Debit Card]) --> KYC_CHECK{KYC Status Check}
    KYC_CHECK -->|Not Approved| KYC_BLOCK[Block Card Request: Redirect to KYC Onboarding]
    KYC_BLOCK --> END_KYC([End: KYC Required])
    KYC_CHECK -->|Approved| CARD_TYPE{Virtual or Physical Card?}

    CARD_TYPE -->|Virtual| VIRT_BRE[Apply BRE: Virtual Card Limit per KYC Tier]
    VIRT_BRE --> BRE_DEC_V{Limit Check Passed?}
    BRE_DEC_V -->|No| VIRT_LIMIT([End: Card Limit Reached])
    BRE_DEC_V -->|Yes| BIN_ALLOC_V[Request BIN Allocation from VISA / Mastercard]
    BIN_ALLOC_V --> PAN_GEN_V[Generate PAN, Expiry, and CVV2 in HSM]
    PAN_GEN_V --> ENCRYPT_V[Encrypt Card Credentials in Vault]
    ENCRYPT_V --> CARD_REC_V[Create Card Record: Status ACTIVE]
    CARD_REC_V --> TOKEN_V[Provision Digital Wallet Token]
    TOKEN_V --> VIRT_NOTIFY[Push Notification: Card Ready in App]
    VIRT_NOTIFY --> SHOW_CARD[Display Masked Card in App Behind Biometric Lock]
    SHOW_CARD --> END_VIRT([End: Virtual Card Active])

    CARD_TYPE -->|Physical| PHYS_BRE[Apply BRE: Physical Card Limit per KYC Tier]
    PHYS_BRE --> BRE_DEC_P{Limit Check Passed?}
    BRE_DEC_P -->|No| PHYS_LIMIT([End: Card Limit Reached])
    BRE_DEC_P -->|Yes| ADDR_CONFIRM[Confirm Delivery Address with Customer]
    ADDR_CONFIRM --> BIN_ALLOC_P[Request BIN Allocation from VISA / Mastercard]
    BIN_ALLOC_P --> PROD_ORDER[Send Card Production Order to Card Bureau]
    PROD_ORDER --> CARD_REC_P[Create Card Record: Status INACTIVE Pending Activation]
    CARD_REC_P --> PRINT_DISPATCH[Card Bureau Prints and Dispatches Card]
    PRINT_DISPATCH --> DISPATCH_EVENT[Webhook: Dispatch Confirmation Received]
    DISPATCH_EVENT --> DISPATCH_NOTIFY[Push Notification: Card Dispatched with ETA]
    DISPATCH_NOTIFY --> ARRIVAL[Card Arrives at Customer Address]
    ARRIVAL --> ACTIVATE_REQ[Customer Initiates Activation in App]
    ACTIVATE_REQ --> VERIFY_DIGITS[Verify Last 4 Digits Match Card Record]
    VERIFY_DIGITS --> VERIFY_DEC{Digits Verified?}
    VERIFY_DEC -->|No| ACT_FAIL[Activation Failed: Retry Prompt]
    ACT_FAIL --> ACTIVATE_REQ
    VERIFY_DEC -->|Yes| OTP_ACT[Send Activation OTP to Registered Phone]
    OTP_ACT --> OTP_DEC{OTP Valid?}
    OTP_DEC -->|No| OTP_FAIL[OTP Failure: Retry or Request New Code]
    OTP_FAIL --> OTP_ACT
    OTP_DEC -->|Yes| CARD_ACTIVATE[Set Card Status to ACTIVE]
    CARD_ACTIVATE --> PHYS_NOTIFY[Send Activation Confirmation Notification]
    PHYS_NOTIFY --> END_PHYS([End: Physical Card Active])
```

### Card Issuance Activity Node Reference

| Node | Activity | Actor | System Component | Notes |
|---|---|---|---|---|
| KYC Status Check | Verify customer KYC tier is APPROVED before card issuance | Platform | Card Service → KYC Service | Cards blocked for PENDING or REJECTED KYC status |
| Card Type Selection | Customer selects virtual or physical product | Customer | Card Request UI | Both paths trigger BRE evaluation |
| BRE Limit Check | Verify customer has not exceeded maximum cards per tier | Platform | Business Rule Engine | Tier 1: max 1 virtual; Tier 2+: 1 virtual + 1 physical |
| BIN Allocation | Request and reserve a card number from the VISA/MC BIN range | Platform | Card Service → VISA/MC | BIN range pre-allocated under bank's sponsorship agreement |
| PAN and CVV Generation | Generate cryptographically secure card credentials in HSM | Platform | Card Service / HSM | PAN stored encrypted; CVV never stored in plain text |
| Card Record Creation | Persist card metadata linked to account | Platform | Card Service / Database | Card record includes PAN hash, expiry, status, and network |
| Digital Wallet Token | Request network token for Apple Pay / Google Pay | Platform | Token Service → VISA/MC TDES | Token maps to PAN without exposing real PAN to wallet |
| Production Order | Instruct card bureau to emboss and mail physical card | Platform | Card Production Adapter | Bureau SLA: dispatch within 2 business days of order |
| Activation Verification | Match customer-entered digits against card record | Platform | Card Service | Digit match + OTP constitutes strong customer authentication |
| Card Activation | Transition card status from INACTIVE to ACTIVE in ledger | Platform | Card Service / Core Banking | CBS notified of card activation for limit and limit-checking |
