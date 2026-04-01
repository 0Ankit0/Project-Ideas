---
Document ID: DBP-SSD-008
Version: 1.0.0
Status: Approved
Owner: Platform Engineering — Core Banking
Last Updated: 2025-01-15
Classification: Internal
---

# System Sequence Diagrams — Digital Banking Platform

This document presents detailed system-level sequence diagrams for three critical user journeys:
money transfer end-to-end, KYC identity verification, and card payment authorization with 3DS
challenge flow. Each diagram is accompanied by a narrative description, key decision points
table, and an error handling specification.

---

## Money Transfer — End-to-End Flow

The money transfer flow covers the complete lifecycle from the customer's initial request
through authentication, fraud screening, balance verification, Core Banking ledger posting,
payment rail submission, asynchronous settlement, and final customer notification.

```mermaid
sequenceDiagram
    autonumber
    actor       Cust as Customer App
    participant AG   as API Gateway
    participant Auth as AuthService
    participant TS   as TransactionService
    participant FS   as FraudService
    participant AccS as AccountService
    participant CB   as Core Banking
    participant PR   as Payment Rail (ACH/SWIFT)
    participant KB   as Kafka
    participant NS   as NotificationService

    Cust->>AG: POST /v1/transfers {fromAccountId, toAccountId, amount, currency, note}
    AG->>Auth: Validate Bearer JWT {token}
    Auth-->>AG: 200 OK {userId, accountIds, kycTier, sessionId}
    AG->>TS: POST /internal/transfers {request + userId, correlationId}

    Note over TS: Generate transactionId (UUID v4); set status = INITIATED

    TS->>AccS: GET /internal/accounts/{fromAccountId}
    AccS-->>TS: 200 OK {balance: 5000.00, currency: USD, status: ACTIVE, kycTier: 2}

    Note over TS: Validate — balance >= amount + fees; kycTier >= minimum; account ACTIVE

    TS->>FS: POST /internal/fraud/pre-check {transactionId, fromAccountId, amount, ip, deviceFingerprint}
    FS-->>TS: 200 OK {riskScore: 0.12, recommendation: ALLOW, modelVersion: v3.2}

    Note over TS: riskScore < 0.5 ALLOW; 0.5–0.9 CHALLENGE; > 0.9 BLOCK

    TS->>AccS: POST /internal/accounts/{fromAccountId}/hold {amount, currency, transactionId}
    AccS-->>TS: 200 OK {holdId: HLD-001, heldAmount: 100.00}

    TS->>CB: POST /ledger/entries {debitAccount, creditAccount, amount, currency, reference}
    CB-->>TS: 200 OK {ledgerEntryId: LE-2025-001, status: POSTED}

    TS->>PR: POST /payments/submit {transactionId, routingNumber, amount, currency, type: ACH}
    PR-->>TS: 202 Accepted {railReference: ACH-TRN-001, estimatedSettlement: T+2}

    TS->>KB: Publish banking.transfer.initiated.v1
    TS-->>AG: 202 Accepted {transactionId, status: PROCESSING, estimatedSettlement}
    AG-->>Cust: 202 Accepted {transactionId, status: PROCESSING, estimatedSettlement}

    Note over PR,KB: Asynchronous Settlement — T+0 to T+2 business days

    PR-->>TS: Webhook POST /webhooks/rail/settlement {railReference, status: SETTLED, settledAt}
    TS->>AccS: DELETE /internal/holds/{holdId}
    TS->>AccS: POST /internal/accounts/{toAccountId}/credit {amount, currency, transactionId}
    AccS-->>TS: 200 OK {newBalance: credited}

    TS->>KB: Publish banking.transfer.completed.v1
    KB-->>NS: Consume banking.transfer.completed.v1
    NS->>Cust: Push notification — "Your transfer of $100.00 has been completed"
```

### Transfer Flow Narrative

The transfer flow employs a dual-phase commit pattern. The synchronous first phase validates
the request, performs fraud pre-screening, places a balance hold, posts the ledger entry in
Core Banking, and submits the payment to the rail. The HTTP 202 response to the customer
indicates acceptance for processing, not settlement.

The asynchronous second phase is triggered by the payment rail's settlement webhook. The system
releases the hold, credits the beneficiary account, publishes `banking.transfer.completed.v1`,
and drives downstream notifications, audit logging, and reporting.

### Transfer Flow — Key Decision Points

| Decision Point       | Condition                                                  | Outcome                                                             |
|----------------------|------------------------------------------------------------|---------------------------------------------------------------------|
| JWT validity         | Token expired or invalid signature                         | HTTP 401 Unauthorized; no further processing                        |
| Account ownership    | `fromAccountId` not owned by authenticated user            | HTTP 403 Forbidden                                                  |
| Account status       | Account is FROZEN or CLOSED                                | HTTP 422 Unprocessable Entity — account not eligible                |
| Balance sufficiency  | `balance < amount + applicable fees`                       | HTTP 422 Unprocessable Entity — insufficient funds                  |
| KYC tier             | Customer tier below minimum for the transfer type          | HTTP 403 Forbidden — KYC upgrade required                           |
| Fraud recommendation | `BLOCK` (riskScore > 0.9)                                  | HTTP 403 Forbidden — fraud block; `fraud.alert.raised.v1` published |
| Fraud recommendation | `CHALLENGE` (riskScore 0.5–0.9)                            | HTTP 202 + OTP step-up challenge initiated                          |
| Rail submission      | Payment rail returns rejection code                        | Transfer marked FAILED; hold released; failure event published      |

### Transfer Flow — Error Handling

| Error Scenario                              | Handling                                                           | Compensating Action                                              |
|---------------------------------------------|--------------------------------------------------------------------|------------------------------------------------------------------|
| Core Banking posting failure                | Retry 3× with exponential back-off; mark FAILED if all exhausted   | Release account hold; publish `banking.transfer.failed.v1`       |
| Payment rail timeout                        | Retry 3× at 30 s intervals using original idempotency key          | If rail confirms duplicate, treat as success; else mark FAILED   |
| Settlement webhook not received within SLA  | Polling job checks rail status every 4 h for 3 days               | Auto-expire; refund hold; notify customer of timeout             |
| Fraudulent webhook replay                   | Validate HMAC-SHA256 signature on all incoming webhooks            | Reject; log to audit trail; no state change applied              |

---

## KYC Verification Flow

The KYC verification flow handles document ingestion, secure S3 storage, external provider
submission, compliance risk assessment, status update, and multi-channel customer notification.

```mermaid
sequenceDiagram
    autonumber
    actor       Cust as Customer App
    participant AG   as API Gateway
    participant KS   as KYCService
    participant S3   as DocumentStore (S3)
    participant KYC  as KYC Provider (Onfido)
    participant CS   as ComplianceService
    participant KB   as Kafka
    participant NS   as NotificationService

    Cust->>AG: POST /v1/kyc/submit {documentType, frontImage, backImage, selfieVideo}
    AG->>KS: Forward KYC submission {customerId, documents}

    Note over KS: Generate kycRecordId (UUID); set status = DOCUMENTS_RECEIVED

    KS->>S3: PutObject documents/{customerId}/{kycRecordId}/front.jpg  [AES-256, SSE-S3]
    S3-->>KS: 200 OK {s3Key, versionId, etag}
    KS->>S3: PutObject documents/{customerId}/{kycRecordId}/back.jpg
    S3-->>KS: 200 OK {s3Key}
    KS->>S3: PutObject documents/{customerId}/{kycRecordId}/selfie.mp4
    S3-->>KS: 200 OK {s3Key}

    Note over KS: All documents stored — generate short-lived, HMAC-signed pre-signed S3 URLs

    KS->>KYC: POST /v3/checks {applicantId, documents: [presignedUrl1, presignedUrl2, presignedUrl3]}
    KYC-->>KS: 201 Created {checkId: CHK-001, status: IN_PROGRESS}

    KS-->>AG: 202 Accepted {kycRecordId, status: UNDER_REVIEW, estimatedCompletion: 5 min}
    AG-->>Cust: 202 Accepted {kycRecordId, status: UNDER_REVIEW}

    Note over KYC: Provider runs OCR, liveness detection, PEP/Sanctions screening (async)

    KYC-->>KS: Webhook POST /webhooks/kyc/result {checkId, result, breakdown}
    KS->>CS: POST /internal/compliance/assess {customerId, kycResult, watchlistResult}
    CS-->>KS: 200 OK {riskTier: 2, recommendation: APPROVED, pepMatch: false}

    Note over KS: Update KYC record — status = APPROVED, tier = 2, verifiedAt = now()

    KS->>KB: Publish identity.kyc.completed.v1 {customerId, kycRecordId, status: APPROVED, tier: 2}
    KB-->>NS: Consume identity.kyc.completed.v1
    NS->>Cust: Push notification — "Your identity has been verified successfully"
    NS->>Cust: Email with KYC tier confirmation and account capabilities summary
```

### KYC Flow Narrative

Documents are never transmitted to Onfido directly from the client. They are stored in S3 with
server-side AES-256 encryption first, and only time-limited, HMAC-signed pre-signed URLs are
shared with the provider. This approach prevents PII leakage in transit and maintains a complete
chain-of-custody audit trail for regulatory purposes.

The ComplianceService combines the provider's document and biometric results with internal
PEP and sanctions database checks to produce the final KYC tier determination. The tier drives
account transaction limits and product eligibility.

### KYC Flow — Key Decision Points

| Decision Point          | Condition                                                  | Outcome                                                           |
|-------------------------|------------------------------------------------------------|-------------------------------------------------------------------|
| Document quality        | Image resolution below 300 DPI or invalid aspect ratio     | Reject upload; HTTP 422 with actionable error detail              |
| File size               | Single file exceeds 10 MB                                  | HTTP 413 Request Too Large                                        |
| Document type           | Unsupported or expired document type                       | HTTP 422 Unprocessable Entity                                     |
| Provider result         | Document CLEAR, facial similarity > 80%                    | Proceed to ComplianceService risk assessment                      |
| PEP match               | Name matches PEP database with confidence score > 0.9      | Status set to PENDING_REVIEW; manual compliance review triggered  |
| Sanctions match         | Exact or fuzzy match on OFAC / EU Consolidated List        | Automatic rejection; compliance team and Compliance Officer alerted |
| Liveness failure        | Selfie fails liveness detection (injected image suspected) | Reject; request fresh selfie re-submission                        |

### KYC Flow — Error Handling

| Error Scenario                    | Handling                                                       | Compensating Action                                              |
|-----------------------------------|----------------------------------------------------------------|------------------------------------------------------------------|
| S3 upload failure                 | Retry 3× with exponential back-off                             | If persistent, return HTTP 503; customer retries later           |
| Provider API timeout              | Circuit breaker after 5 consecutive failures; fallback to manual review | KYC status set to PENDING_MANUAL_REVIEW               |
| Webhook delivery failure          | Provider retries up to 10× over 24 h                          | KYCService polls provider every 30 min if no webhook within 1 h  |
| ComplianceService unavailable     | Retry 5× with exponential back-off                             | Queue assessment; process when service recovers                  |

---

## Card Payment Authorization — 3DS Flow

The 3DS 2.0 authorization flow governs card-not-present transactions, providing risk-based
authentication with a step-up challenge when the fraud score warrants it.

```mermaid
sequenceDiagram
    autonumber
    participant MT   as Merchant Terminal
    participant CN   as Card Network (VISA)
    participant CS   as CardService
    participant FS   as FraudService
    participant AccS as AccountService
    participant ThDS as 3DS Server
    participant Cust as Customer App
    participant KB   as Kafka
    participant NS   as NotificationService

    MT->>CN: Authorization Request ISO 8583 {PAN, amount, merchantId, terminalId, CVV2}
    CN->>CS: POST /v1/authorize {cardToken, amount, currency, merchantId, mcc, 3dsData}

    Note over CS: Tokenize PAN to cardToken; look up card record by token

    CS->>FS: POST /internal/fraud/card-check {cardId, amount, merchantId, mcc, ipCountry, deviceId}
    FS-->>CS: 200 OK {riskScore: 0.65, recommendation: CHALLENGE, velocity: {txnCount: 3, window: 1h}}

    Note over CS: riskScore 0.5–0.9 — trigger 3DS challenge flow

    CS->>ThDS: POST /3ds/initiate {cardId, amount, merchantId, transactionId, acsUrl}
    ThDS-->>CS: 200 OK {threeDSServerTransID, acsUrl, acsTransID, challengeRequired: true}

    CS-->>CN: 202 Pending {threeDSServerTransID, acsUrl — redirect customer to ACS}
    CN-->>MT: Challenge required — redirect to ACS challenge page
    MT->>Cust: Redirect browser / SDK to ACS challenge UI

    Note over Cust,ThDS: Out-of-band step-up authentication

    Cust->>ThDS: Submit OTP / biometric response
    ThDS-->>CS: Webhook: 3DS result {transStatus: Y, eci: 05, authenticationValue}

    Note over CS: transStatus Y — authenticated; proceed to authorization

    CS->>AccS: POST /internal/accounts/{accountId}/authorize-hold {amount, currency, transactionId}
    AccS-->>CS: 200 OK {holdId: HOLD-001, availableBalance: 2400.00}

    Note over CS: Balance sufficient — generate authorization code

    CS->>KB: Publish banking.card.authorized.v1 {cardId, transactionId, amount, merchantId, authCode}
    CS-->>CN: 200 OK {authCode, responseCode: 00, eci: 05}
    CN-->>MT: Authorization Approved ISO 8583 0110 {authCode: AUTH-9821}

    KB-->>NS: Consume banking.card.authorized.v1
    NS->>Cust: Push notification — "Card payment of $45.00 approved at MerchantName"
```

### Card Payment Authorization Narrative

The 3DS 2.0 integration employs risk-based authentication (RBA) upstream of the challenge step.
Low-risk transactions (score < 0.5) are approved frictionlessly without a customer challenge.
Medium-risk transactions (0.5–0.9) trigger a 3DS step-up challenge via the issuer's ACS.
High-risk transactions (> 0.9) are declined outright and a `fraud.alert.raised.v1` event is
published.

The balance hold placed at authorization is released at clearing time when the merchant submits
the capture message. Uncaptured holds are auto-released after 7 calendar days to prevent
long-term balance lock.

### Card Authorization — Key Decision Points

| Decision Point       | Condition                                            | Outcome                                                              |
|----------------------|------------------------------------------------------|----------------------------------------------------------------------|
| Card status          | Card is FROZEN, EXPIRED, or BLOCKED                  | ISO 8583 response code 62 — Restricted card                          |
| CVV2 validation      | CVV2 mismatch                                        | Response code 82; increment failed CVV2 counter; lock after 3 fails  |
| Fraud score          | score > 0.9                                          | Decline response code 05; publish `fraud.alert.raised.v1`            |
| Fraud score          | score 0.5–0.9                                        | Trigger 3DS step-up challenge                                        |
| Fraud score          | score < 0.5                                          | Frictionless authentication — no customer interaction                |
| 3DS result           | transStatus N — not authenticated                    | Decline; response code 65                                            |
| Balance hold         | Available balance < authorization amount             | Decline; response code 51 — Insufficient funds                       |
| Daily spend limit    | Transaction would exceed customer daily limit        | Decline; response code 61 — Exceeds withdrawal limit                 |

### Card Authorization — Error Handling

| Error Scenario                   | Handling                                                              | Compensating Action                                               |
|----------------------------------|-----------------------------------------------------------------------|-------------------------------------------------------------------|
| 3DS server unavailable           | Fallback to static 3DS (password-based); raise fraud threshold        | Log event; alert on-call engineering team via PagerDuty           |
| Card network timeout             | Retry once with identical ISO 8583 message and same STAN              | If second attempt fails, return response code 96 System malfunction |
| AccountService unavailable       | Circuit breaker; cached balance for low-value txns (< $50)            | High-value transactions declined until service recovers           |
| Authorization hold failure       | Do not issue approval code under any circumstances                    | Return response code 51; no partial authorization permitted       |
