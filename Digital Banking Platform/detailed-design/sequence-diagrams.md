# Sequence Diagrams — Digital Banking Platform

---

## Domestic Money Transfer with Fraud Check and AML Screening

This diagram captures the full lifecycle of a domestic money transfer, from customer initiation through fraud scoring, AML sanctions screening, core banking debit/credit, payment rail submission, and final notification delivery.

```mermaid
sequenceDiagram
    autonumber
    actor Customer
    participant TransferService
    participant AccountService
    participant FraudEngine
    participant AMLScreener
    participant CoreBankingSystem
    participant PaymentRail
    participant NotificationService

    Customer->>TransferService: POST /transfers (amount, source_account, destination_account, reference)
    activate TransferService

    TransferService->>TransferService: Validate request schema, generate idempotency_key
    TransferService->>AccountService: GET /accounts/{source_id}/balance-and-status
    activate AccountService
    AccountService-->>TransferService: { balance: 5000, status: "ACTIVE", daily_limit_remaining: 9500 }
    deactivate AccountService

    alt Insufficient balance or frozen account
        TransferService-->>Customer: 422 Unprocessable — Insufficient funds or account restricted
    end

    TransferService->>FraudEngine: POST /score { customer_id, amount, destination, device_fingerprint, ip, velocity_window }
    activate FraudEngine
    FraudEngine->>FraudEngine: Run ML gradient-boost model (300+ features)
    FraudEngine->>FraudEngine: Check velocity rules (same destination last 24h, unusual hour)
    FraudEngine->>FraudEngine: Check device reputation and geo-anomaly
    FraudEngine-->>TransferService: { fraud_score: 0.12, risk_band: "LOW", model_version: "v4.2.1" }
    deactivate FraudEngine

    alt fraud_score >= 0.85 (HIGH risk)
        TransferService->>TransferService: Set transaction status = FRAUD_BLOCKED
        TransferService->>NotificationService: PUBLISH fraud_alert { customer_id, transaction_ref, score }
        TransferService-->>Customer: 403 Forbidden — Transaction blocked by fraud controls
    else fraud_score >= 0.50 (MEDIUM risk)
        TransferService->>TransferService: Set transaction status = PENDING_REVIEW
        TransferService->>NotificationService: PUBLISH step_up_auth_required
        TransferService-->>Customer: 202 Accepted — Additional verification required (OTP/biometric)
        Customer->>TransferService: POST /transfers/{ref}/verify { otp_code }
        TransferService->>TransferService: Validate OTP, re-evaluate risk band → ACCEPTED
    end

    TransferService->>AMLScreener: POST /screen { beneficiary_name, destination_account, bank_bic, amount, currency }
    activate AMLScreener
    AMLScreener->>AMLScreener: Check OFAC SDN list
    AMLScreener->>AMLScreener: Check UN consolidated sanctions list
    AMLScreener->>AMLScreener: Check EU/HM Treasury lists
    AMLScreener->>AMLScreener: Check ComplyAdvantage PEP database
    AMLScreener->>AMLScreener: Apply fuzzy name matching (Jaro-Winkler threshold 0.92)
    AMLScreener-->>TransferService: { result: "CLEAR", match_count: 0, screen_id: "AML-20240601-7823" }
    deactivate AMLScreener

    alt AML result = HIT
        TransferService->>TransferService: Set transaction status = AML_HOLD
        TransferService->>NotificationService: PUBLISH aml_alert { transaction_ref, match_details }
        TransferService-->>Customer: 202 Accepted — Transfer under compliance review (up to 3 business days)
    end

    TransferService->>CoreBankingSystem: POST /ledger/debit { account_id: source, amount, currency, ref, memo }
    activate CoreBankingSystem
    CoreBankingSystem->>CoreBankingSystem: Acquire account row-level lock
    CoreBankingSystem->>CoreBankingSystem: Validate final balance (re-check after lock)
    CoreBankingSystem->>CoreBankingSystem: Write debit journal entry (double-entry: Dr Checking Cr Suspense)
    CoreBankingSystem->>CoreBankingSystem: Update available balance
    CoreBankingSystem-->>TransferService: { journal_id: "JRN-0048291", new_balance: 3500, timestamp: "2024-06-01T14:23:01Z" }
    deactivate CoreBankingSystem

    TransferService->>TransferService: Persist transfer record with status = PROCESSING

    alt Amount >= $1,000 and same-day (Fedwire eligible)
        TransferService->>PaymentRail: POST /fedwire/submit { imad, amount, sender_aba, receiver_aba, ref }
        activate PaymentRail
        PaymentRail->>PaymentRail: Format Fedwire message type 1000
        PaymentRail->>PaymentRail: Submit to Federal Reserve FedLine Advantage
        PaymentRail-->>TransferService: { omad: "20240601BANKUS33B000001", status: "ACCEPTED", settlement_time: "T+0" }
        deactivate PaymentRail
    else Standard ACH (Next-Day or Same-Day ACH)
        TransferService->>PaymentRail: POST /ach/originate { nacha_record, entry_class: "PPD", effective_date }
        activate PaymentRail
        PaymentRail->>PaymentRail: Build NACHA-formatted ACH file (94-byte fixed width)
        PaymentRail->>PaymentRail: Transmit to ODFI (Originating Depository Financial Institution)
        PaymentRail-->>TransferService: { trace_number: "021000021234567", batch_id: "BATCH-20240601-003", status: "SUBMITTED" }
        deactivate PaymentRail
    end

    PaymentRail->>CoreBankingSystem: EVENT payment_rail_settled { trace_number, amount, destination_account }
    activate CoreBankingSystem
    CoreBankingSystem->>CoreBankingSystem: Write credit journal entry (Dr Suspense Cr Destination Checking)
    CoreBankingSystem->>CoreBankingSystem: Update destination account available balance
    CoreBankingSystem->>CoreBankingSystem: Release suspense balance
    CoreBankingSystem-->>PaymentRail: { ack: true, credit_journal_id: "JRN-0048292" }
    deactivate CoreBankingSystem

    CoreBankingSystem->>TransferService: EVENT ledger_settled { transaction_ref, status: "COMPLETED" }
    TransferService->>TransferService: Update transfer record status = COMPLETED
    TransferService->>TransferService: Emit domain event TransferCompleted to Kafka topic transfers.completed

    TransferService->>NotificationService: PUBLISH transfer_completed { customer_id, amount, destination_masked, timestamp }
    activate NotificationService
    NotificationService->>NotificationService: Resolve notification preferences (push, SMS, email)
    NotificationService->>NotificationService: Render template with i18n locale
    NotificationService-->>Customer: Push notification: "Transfer of $1,500 sent to ****6789 — Ref: TXN-0048291"
    deactivate NotificationService

    TransferService-->>Customer: 200 OK { transfer_id, status: "COMPLETED", settlement_timestamp }
    deactivate TransferService
```

---

## Card Payment with 3DS Authentication

This diagram covers the full card-not-present payment flow including 3D Secure 2.x authentication, authorization decision, and next-day settlement batch processing through card network rails.

```mermaid
sequenceDiagram
    autonumber
    actor Customer
    participant MerchantPOS
    participant AcquiringBank
    participant CardNetwork as VisaNet / Mastercard
    participant IssuingBank as IssuingBank (Our System)
    participant CardService
    participant FraudEngine
    participant ThreeDSServer as 3DS Server (EMVCo 2.2)
    participant CustomerMobile as Customer Mobile App
    participant AuthorizationEngine
    participant SettlementService

    Customer->>MerchantPOS: Enter card details (PAN, expiry, CVV) or tap NFC
    activate MerchantPOS
    MerchantPOS->>MerchantPOS: Tokenize PAN via payment SDK (Stripe/Adyen)
    MerchantPOS->>AcquiringBank: ISO 8583 Authorization Request (MTI 0100) { PAN_token, amount, MCC, merchant_id, terminal_id }
    deactivate MerchantPOS
    activate AcquiringBank

    AcquiringBank->>AcquiringBank: Validate merchant credentials, check daily volume limits
    AcquiringBank->>CardNetwork: Route authorization request via VisaNet/Banknet
    deactivate AcquiringBank
    activate CardNetwork

    CardNetwork->>CardNetwork: BIN lookup → route to IssuingBank
    CardNetwork->>CardNetwork: Apply network-level velocity checks
    CardNetwork->>IssuingBank: Forward ISO 8583 auth request + 3DS data elements
    deactivate CardNetwork
    activate IssuingBank

    IssuingBank->>CardService: Validate card { pan_token, expiry, cvv2, status }
    activate CardService
    CardService->>CardService: Verify CVV2 via HSM (CloudHSM PKCS#11 API)
    CardService->>CardService: Check card status (ACTIVE / BLOCKED / EXPIRED)
    CardService->>CardService: Check spending controls (category limits, geographic restrictions)
    CardService-->>IssuingBank: { card_valid: true, card_status: "ACTIVE", spending_controls_pass: true }
    deactivate CardService

    IssuingBank->>FraudEngine: POST /score/card { pan_token, merchant_id, amount, mcc, device_data, browser_data }
    activate FraudEngine
    FraudEngine->>FraudEngine: Real-time feature extraction (180ms SLA)
    FraudEngine->>FraudEngine: Evaluate merchant risk (MCC 6051 = high risk)
    FraudEngine->>FraudEngine: Check cardholder behavioral biometrics
    FraudEngine->>FraudEngine: Apply network consortium fraud signals
    FraudEngine-->>IssuingBank: { fraud_score: 0.34, recommendation: "CHALLENGE", model_id: "CRD-v3.1" }
    deactivate FraudEngine

    IssuingBank->>ThreeDSServer: POST /authenticate { pan_token, merchant_url, device_channel, amount, 3ds_requestor_id }
    activate ThreeDSServer

    alt Frictionless Flow (low risk, trusted device)
        ThreeDSServer->>ThreeDSServer: Evaluate device fingerprint + prior authentication history
        ThreeDSServer-->>IssuingBank: { authentication_value: "AAA....", eci: "05", status: "Y", flow: "FRICTIONLESS" }
    else Challenge Flow (medium risk — OTP required)
        ThreeDSServer->>ThreeDSServer: Initiate challenge (OTP via push notification)
        ThreeDSServer->>CustomerMobile: Send push: "Authorize payment $89.99 at Amazon? Tap Yes or enter 847291"
        activate CustomerMobile
        Customer->>CustomerMobile: Tap "Authorize" / Enter OTP 847291
        CustomerMobile->>ThreeDSServer: POST /challenge/response { challenge_data, otp }
        ThreeDSServer->>ThreeDSServer: Validate OTP (TOTP RFC 6238, window ±30s)
        ThreeDSServer-->>IssuingBank: { authentication_value: "BBB...", eci: "02", status: "Y", flow: "CHALLENGE" }
        deactivate CustomerMobile
    else Decoupled Authentication (high-risk, out-of-band)
        ThreeDSServer->>CustomerMobile: Push biometric challenge (FaceID/TouchID)
        Customer->>CustomerMobile: Biometric confirmation
        CustomerMobile->>ThreeDSServer: POST /decoupled/confirm { biometric_token }
        ThreeDSServer-->>IssuingBank: { authentication_value: "CCC...", eci: "02", status: "Y", flow: "DECOUPLED" }
    end
    deactivate ThreeDSServer

    IssuingBank->>AuthorizationEngine: Authorize { card_id, amount, eci, authentication_value, fraud_score }
    activate AuthorizationEngine
    AuthorizationEngine->>AuthorizationEngine: Check available credit / balance
    AuthorizationEngine->>AuthorizationEngine: Apply authorization holds
    AuthorizationEngine->>AuthorizationEngine: Write authorization record to ledger (hold)
    AuthorizationEngine-->>IssuingBank: { decision: "APPROVED", auth_code: "483920", available_credit_after: 2340.00 }
    deactivate AuthorizationEngine

    IssuingBank-->>CardNetwork: ISO 8583 Response (MTI 0110) { auth_code: "483920", response_code: "00" }
    activate CardNetwork
    CardNetwork-->>AcquiringBank: Forward approval response
    deactivate CardNetwork
    activate AcquiringBank
    AcquiringBank-->>MerchantPOS: Approval — Auth Code 483920
    deactivate AcquiringBank
    MerchantPOS-->>Customer: Payment approved — receipt generated
    deactivate IssuingBank

    Note over SettlementService, CardNetwork: End-of-day settlement batch (T+1)
    MerchantPOS->>AcquiringBank: Batch settlement file (all authorized transactions)
    AcquiringBank->>CardNetwork: Submit clearing file (ISO 8583 MTI 0220)
    CardNetwork->>IssuingBank: Settlement debit (net, multilateral)
    activate IssuingBank
    IssuingBank->>SettlementService: Convert authorization hold → posted transaction
    activate SettlementService
    SettlementService->>SettlementService: Write posting entry to ledger (Dr Cardholder Cr Nostro)
    SettlementService->>SettlementService: Release authorization hold, record interchange fee
    SettlementService->>SettlementService: Generate account statement entry
    SettlementService-->>IssuingBank: { posted_transaction_id: "TXN-POST-9912", status: "SETTLED" }
    deactivate SettlementService
    deactivate IssuingBank
```

---

## Loan Application with Credit Bureau Pull

This diagram covers the full personal loan origination flow: identity verification, credit bureau inquiry, automated underwriting decisioning, offer presentation, customer acceptance, and loan disbursement to a linked deposit account.

```mermaid
sequenceDiagram
    autonumber
    actor Customer
    participant LoanService
    participant IdentityService
    participant CreditBureau as Credit Bureau (Experian)
    participant UnderwritingEngine
    participant AccountService
    participant NotificationService
    participant CoreBankingSystem

    Customer->>LoanService: POST /loans/apply { amount: 15000, term_months: 36, purpose: "HOME_IMPROVEMENT", ssn_last4, dob, annual_income }
    activate LoanService

    LoanService->>LoanService: Validate application schema, generate application_id = LOAN-2024-09182
    LoanService->>LoanService: Check applicant not already in default or active pending application
    LoanService->>LoanService: Persist application record status = APPLICATION_SUBMITTED

    LoanService->>IdentityService: POST /kyc/verify { customer_id, ssn_last4, dob, address, document_ref }
    activate IdentityService
    IdentityService->>IdentityService: Match customer record against onboarding KYC data
    IdentityService->>IdentityService: Run watchlist check (OFAC, PEP, adverse media)
    IdentityService->>IdentityService: Validate identity document not expired
    IdentityService->>IdentityService: Check CIP (Customer Identification Program) status
    IdentityService-->>LoanService: { kyc_status: "VERIFIED", risk_rating: "LOW", watchlist_clear: true, verification_id: "KYC-V-00293" }
    deactivate IdentityService

    alt KYC status = FAILED or watchlist HIT
        LoanService->>NotificationService: PUBLISH application_declined { reason: "IDENTITY_FAILURE" }
        LoanService-->>Customer: 200 OK — Application declined: identity verification failed
    end

    LoanService->>LoanService: Update application status = UNDERWRITING_IN_PROGRESS

    LoanService->>CreditBureau: POST /credit-report/pull { ssn, dob, address, permissible_purpose: "CREDIT_TRANSACTION", inquiry_type: "HARD" }
    activate CreditBureau
    CreditBureau->>CreditBureau: Authenticate via OAuth 2.0 client_credentials (mTLS)
    CreditBureau->>CreditBureau: Pull tri-merge credit file (Experian + Equifax + TransUnion)
    CreditBureau->>CreditBureau: Calculate FICO 9 score
    CreditBureau->>CreditBureau: Extract tradeline data: payment history, utilization, age of accounts, derogatory marks
    CreditBureau->>CreditBureau: Record hard inquiry on consumer's credit file
    CreditBureau-->>LoanService: { fico_score: 728, dti_ratio: 0.31, derogatory_count: 0, open_revolving_utilization: 0.24, report_id: "EXP-2024-884723" }
    deactivate CreditBureau

    LoanService->>UnderwritingEngine: POST /underwrite { application_id, fico_score: 728, dti: 0.31, income: 85000, loan_amount: 15000, term: 36, purpose: "HOME_IMPROVEMENT" }
    activate UnderwritingEngine
    UnderwritingEngine->>UnderwritingEngine: Apply policy waterfall (FICO >= 620 → eligible)
    UnderwritingEngine->>UnderwritingEngine: Calculate back-end DTI with proposed payment: 0.31 + (payment/income) = 0.37 (< 0.43 limit)
    UnderwritingEngine->>UnderwritingEngine: Determine risk tier: Tier B (FICO 700–750)
    UnderwritingEngine->>UnderwritingEngine: Price loan: base_rate 6.5% + risk_premium 1.25% = APR 7.75%
    UnderwritingEngine->>UnderwritingEngine: Calculate monthly payment: $470.69 on $15,000/36mo at 7.75%
    UnderwritingEngine->>UnderwritingEngine: Check concentration limits (total personal loan book exposure)
    UnderwritingEngine->>UnderwritingEngine: Log decision rationale for adverse action file (ECOA/Reg B)
    UnderwritingEngine-->>LoanService: { decision: "APPROVED", apr: 7.75, monthly_payment: 470.69, origination_fee: 150.00, conditions: [], decision_id: "UW-D-20240601-4421" }
    deactivate UnderwritingEngine

    LoanService->>LoanService: Update application status = APPROVED
    LoanService->>LoanService: Generate loan offer document (Truth-in-Lending Act disclosure, TILA box)

    LoanService->>NotificationService: PUBLISH loan_offer_ready { customer_id, application_id, apr, monthly_payment, expiry: "72h" }
    activate NotificationService
    NotificationService-->>Customer: Email + Push: "Congrats! Your $15,000 loan is approved at 7.75% APR — accept within 72 hours"
    deactivate NotificationService

    LoanService-->>Customer: 200 OK — Offer { loan_offer_id, apr: 7.75, monthly_payment: 470.69, origination_fee: 150, expiry_at }

    Customer->>LoanService: POST /loans/{application_id}/accept { loan_offer_id, disbursement_account_id, e_signature_token }
    activate LoanService
    LoanService->>LoanService: Validate e-signature token (DocuSign/HelloSign webhook verification)
    LoanService->>LoanService: Validate offer not expired
    LoanService->>LoanService: Create loan account record status = ACTIVE
    LoanService->>LoanService: Generate repayment schedule (amortization table, 36 entries)
    LoanService->>LoanService: Set up auto-debit mandate (ACH authorization)

    LoanService->>AccountService: GET /accounts/{disbursement_account_id}/validate
    activate AccountService
    AccountService-->>LoanService: { account_status: "ACTIVE", routing: "021000021", account_type: "CHECKING" }
    deactivate AccountService

    LoanService->>CoreBankingSystem: POST /ledger/loan-disburse { loan_id, amount: 14850.00, origination_fee: 150.00, destination_account }
    activate CoreBankingSystem
    CoreBankingSystem->>CoreBankingSystem: Write loan origination journal (Dr Loan Asset Cr Funding Pool)
    CoreBankingSystem->>CoreBankingSystem: Deduct origination fee (Dr Customer Cr Fee Revenue)
    CoreBankingSystem->>CoreBankingSystem: Credit net disbursement to checking account (Dr Funding Pool Cr Checking)
    CoreBankingSystem->>CoreBankingSystem: Set up loan ledger: principal outstanding, accrued interest tracking
    CoreBankingSystem-->>LoanService: { disbursement_id: "DISB-00441", credited_amount: 14850.00, effective_date: "2024-06-01" }
    deactivate CoreBankingSystem

    LoanService->>LoanService: Update loan status = ACTIVE, next_payment_date = 2024-07-01
    LoanService->>NotificationService: PUBLISH loan_disbursed { customer_id, loan_id, amount: 14850, account_last4: "4521" }
    activate NotificationService
    NotificationService-->>Customer: "Your loan of $14,850 has been deposited to your checking account ending 4521"
    deactivate NotificationService

    LoanService-->>Customer: 201 Created { loan_id, status: "ACTIVE", disbursed_amount: 14850, first_payment_date: "2024-07-01", monthly_payment: 470.69 }
    deactivate LoanService
```
