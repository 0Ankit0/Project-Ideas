# Use Case Descriptions — Digital Banking Platform

This document provides detailed structured descriptions for seven core use cases of the Digital
Banking Platform. Each description follows a standardized template covering actors, flows,
business rules, non-functional requirements, UI/UX considerations, and data requirements.
These descriptions serve as the primary input to development teams, QA engineers, and
compliance reviewers during system build and validation.

---

## UC-001: Open Account

### Summary

A prospective customer initiates the process to open a new retail banking account (current or
savings) through the mobile app or web portal. The process includes personal information capture,
identity document upload, KYC verification (UC-002 include), and account activation upon
successful verification.

---

### Actors

| Role              | Actor                   | Description                                                        |
|-------------------|-------------------------|--------------------------------------------------------------------|
| Primary Actor     | Customer                | Initiates the account opening process via self-service app/web     |
| Secondary Actor   | KYC Provider            | Onfido / Jumio — performs OCR, liveness, and identity verification |
| Secondary Actor   | Compliance Officer      | Reviews cases escalated for manual KYC adjudication               |
| Secondary Actor   | Bank Admin              | Monitors onboarding queue and resolves system exceptions           |

---

### Preconditions

1. The customer has downloaded the mobile app or accessed the web portal.
2. The customer has a valid government-issued photo identity document (passport, driver's
   license, or national ID).
3. The customer's email address and mobile phone number are not already registered in the system.
4. The system's KYC provider (Onfido/Jumio) is operational and accessible via API.

---

### Postconditions

**Success:**
1. A new bank account is created with a unique account number and IBAN/routing number.
2. The customer's KYC status is set to `VERIFIED` (Tier 1, 2, or 3 based on verification depth).
3. Default transaction limits are applied as per the customer's KYC tier.
4. A welcome notification is sent via email and push notification.
5. The customer's profile record is created in the core banking system.

**Failure:**
1. If KYC fails, no account is created and the application is recorded as `REJECTED`.
2. The customer receives a notification with the rejection reason (within regulatory constraints).

---

### Main Flow

1. **Launch Onboarding:** The customer opens the app and selects "Open Account." The system
   presents a product selector (current account, savings account, fixed deposit).
2. **Select Account Type:** The customer selects the desired account type. The system displays
   the terms and conditions, fee schedule, and eligibility criteria.
3. **Accept Terms:** The customer reviews and accepts the terms and conditions. The system
   records consent with a timestamp and IP address.
4. **Enter Personal Details:** The customer enters: full legal name, date of birth, residential
   address, SSN/TIN (or national equivalent), email address, and mobile phone number.
5. **Verify Contact Details:** The system sends an OTP to the provided mobile number and email.
   The customer enters both OTPs to verify contact channels.
6. **Upload Identity Documents:** The customer uploads a front/back photo of their government-
   issued ID and a selfie. The system validates file format, size, and image quality.
7. **KYC Processing:** The system invokes UC-002 (KYC Verification). OCR extracts document
   data, liveness detection runs on the selfie, and a PEP/sanctions check is executed.
8. **KYC Decision:** The system receives the KYC decision — Pass, Fail, or Manual Review.
   If Manual Review, a compliance queue case is created and the customer is notified of
   an estimated 24–48 hour review period.
9. **Account Creation:** Upon KYC Pass (automatic or manual approval), the system creates
   the account in the core banking system, assigns account number and IBAN, and sets
   default transaction limits based on KYC tier.
10. **Welcome Notification:** The system sends a welcome push notification and email containing
    account number, IBAN, and a link to the mobile banking guide. First login is enabled.

---

### Alternative Flows

**AF-001A — Manual Review Required (Step 8):**
If the automated KYC engine returns `MANUAL_REVIEW`, the system creates a compliance case.
The Compliance Officer reviews the submitted documents and identity data. If approved, the
flow resumes at Step 9. If more information is needed, the customer receives a request for
additional documents and may re-submit, returning to Step 6.

**AF-001B — Existing Email/Phone Detected (Step 4):**
If the email or phone number is already registered, the system presents an "Account already
exists" message with options to log in, reset password, or contact support. The onboarding
flow terminates without creating a duplicate record.

**AF-001C — Fixed Deposit Selected (Step 2):**
If the customer selects Fixed Deposit, the system additionally requires an existing current/
savings account (internal or external) to fund the FD. The flow adds a funding source capture
step after Step 4 and applies additional eligibility checks.

---

### Exception Flows

**EX-001A — KYC Provider Unavailable:**
If the KYC provider API is unavailable (timeout > 10 seconds or HTTP 5xx), the system saves
the document submission, queues the KYC request for retry, and notifies the customer that
verification is in progress. The customer does not need to re-submit documents.

**EX-001B — Document Quality Failure (Step 6):**
If the uploaded documents fail minimum quality thresholds (blurry, glare, cut-off edges,
expired document), the system returns a quality failure message with specific guidance.
The customer is allowed up to 3 re-upload attempts before the session is locked for 24 hours.

**EX-001C — Liveness Check Failure (Step 7):**
If the facial liveness check fails (spoof detection, no face detected), the customer is
prompted to retry in better lighting. After 3 consecutive failures, the application is
escalated to manual review rather than auto-rejected, to reduce false-positive abandonment.

---

### Business Rules

| Rule ID | Description                                                                        |
|---------|------------------------------------------------------------------------------------|
| BR-001  | A customer may not open more than 3 active accounts of the same product type       |
| BR-002  | KYC must be completed within 30 days of application initiation or it expires       |
| BR-003  | Tier 1 KYC: daily transfer limit $500; Tier 2: $10,000; Tier 3: $100,000           |
| BR-004  | Date of birth must indicate the customer is 18+ years of age                       |
| BR-005  | Customers on OFAC/SDN sanctions list must be rejected and a SAR filed              |
| BR-006  | All KYC data must be stored for a minimum of 7 years per BSA requirements          |

---

### Non-Functional Requirements

| Category    | Requirement                                                                  |
|-------------|------------------------------------------------------------------------------|
| Performance | KYC API response must complete within 30 seconds (P95)                       |
| Availability| Onboarding flow must be available 99.9% uptime (excluding KYC provider SLA)  |
| Security    | All uploaded documents encrypted at rest (AES-256) and in transit (TLS 1.3) |
| Compliance  | Consent timestamps stored immutably with IP address and device fingerprint   |
| Scalability | Must support 500 concurrent onboarding sessions without degradation          |

---

### UI/UX Notes

- Progress indicator showing onboarding steps (5-step stepper component)
- Document upload supports both camera capture (mobile) and file upload (web)
- Inline validation on all form fields — no batch submission errors
- Clear, plain-language error messages without technical jargon
- Estimated time to complete prominently displayed: "Takes about 5 minutes"
- Accessibility: WCAG 2.1 AA compliance, screen-reader compatible

---

### Data Requirements

| Field                  | Type    | Source          | Validation                          |
|------------------------|---------|-----------------|--------------------------------------|
| Full Legal Name        | String  | Customer input  | Min 2 chars, max 120, regex name     |
| Date of Birth          | Date    | Customer input  | ISO 8601, must be 18+ years ago      |
| Residential Address    | Object  | Customer input  | Address verification API             |
| SSN / National ID      | String  | Customer input  | Luhn / format validation, encrypted  |
| Email Address          | String  | Customer input  | RFC 5322 format, OTP verified        |
| Mobile Phone           | String  | Customer input  | E.164 format, OTP verified           |
| Identity Document      | File    | Customer upload | JPEG/PNG/PDF, max 10MB, min 300 DPI  |
| Selfie / Liveness      | File    | Customer camera | JPEG, min 640×480, face detected     |
| KYC Decision           | Enum    | KYC Provider    | PASS / FAIL / MANUAL_REVIEW          |
| Account Number         | String  | System-generated| Unique, 10-digit numeric             |

---

## UC-002: KYC Verification

### Summary

The KYC Verification use case validates the identity of a customer using document OCR, facial
liveness checks, and PEP/sanctions screening (UC-016 include). It is invoked during account
opening (UC-001) and periodically during re-KYC reviews (UC-020). The outcome determines the
customer's KYC tier and whether the account proceeds to activation or escalates for manual review.

---

### Actors

| Role            | Actor                | Description                                                              |
|-----------------|----------------------|--------------------------------------------------------------------------|
| Primary Actor   | Compliance Officer   | Reviews cases escalated to manual adjudication                           |
| Primary Actor   | Customer             | Submits identity documents and completes liveness check                  |
| Secondary Actor | KYC Provider         | Onfido / Jumio — performs document OCR, liveness detection, screening    |
| Secondary Actor | Bank Admin           | Monitors KYC queue metrics and SLA compliance                            |

---

### Preconditions

1. The customer has initiated the account opening process (UC-001) or a re-KYC has been triggered.
2. The customer has uploaded a valid government-issued photo identity document.
3. The KYC provider's API endpoint is reachable and returning healthy status codes.
4. The customer has consented to identity verification and biometric data processing.

---

### Postconditions

**Success:**
1. The customer's KYC status is updated to `VERIFIED` with the appropriate tier (1/2/3).
2. Extracted identity data (name, DOB, document number) is stored against the customer profile.
3. A PEP/sanctions check result is recorded as `CLEAR` or `FLAGGED`.
4. The KYC event is written to the immutable audit log with timestamp and decision details.

**Manual Review:**
1. A case is created in the compliance management system with all submitted documents attached.
2. The customer's account status remains `PENDING_KYC` until the officer makes a decision.

---

### Main Flow

1. **Receive KYC Request:** The system receives a KYC verification trigger from the account
   opening flow (UC-001) or re-KYC workflow (UC-020). A unique KYC session ID is generated.
2. **Document OCR:** The system submits the customer's uploaded identity document to the KYC
   provider API. The provider performs OCR to extract: name, date of birth, document number,
   expiry date, and nationality.
3. **Document Authenticity Check:** The KYC provider runs forgery detection algorithms
   (MRZ validation, hologram checks, microprint analysis). A document authenticity score is
   returned.
4. **Liveness Check:** The customer is prompted to complete a liveness check (a short
   instructed selfie video). The KYC provider verifies that the submitted selfie is a live
   person and matches the document photo using facial biometrics.
5. **PEP & Sanctions Screening (UC-016 include):** The extracted name and date of birth are
   run against PEP lists, OFAC SDN, UN sanctions lists, and EU consolidated lists. Results
   are returned as CLEAR, POTENTIAL_MATCH, or CONFIRMED_MATCH.
6. **Risk Scoring:** The system computes an aggregate KYC risk score based on document
   authenticity, liveness confidence, PEP result, and country risk.
7. **Decision Engine:** Based on the risk score and pre-defined thresholds:
   - Score ≥ 80: Auto-PASS (KYC Tier assigned based on document type)
   - Score 50–79: MANUAL_REVIEW escalated to Compliance Officer
   - Score < 50: Auto-FAIL
8. **Record Outcome:** The decision, score, extracted data, and document references are stored
   in the KYC audit database. The result is returned to the calling use case (UC-001/UC-020).
9. **Notify Customer:** An appropriate notification is sent: "Verification successful," "Under
   review," or "Verification failed" — via push notification and email.

---

### Alternative Flows

**AF-002A — Potential PEP Match (Step 5):**
If the PEP check returns `POTENTIAL_MATCH` (name similarity above threshold), the case is
automatically escalated to Manual Review regardless of the document/liveness score. The
Compliance Officer must determine if the match is a true positive or false positive before
the account can proceed.

**AF-002B — Expired Document (Step 3):**
If the OCR extracts an expiry date that is in the past, the system immediately rejects the
document and prompts the customer to upload a valid, non-expired document. The KYC session
remains open for 7 days to allow re-submission.

**AF-002C — Document Type Mismatch (Step 2):**
If the customer submits a document type not on the accepted list for their jurisdiction, the
system returns an error message specifying accepted document types and prompts re-upload
without consuming a KYC attempt.

---

### Exception Flows

**EX-002A — KYC Provider Timeout:**
If the KYC API does not respond within 30 seconds, the system queues the request for async
retry (up to 3 attempts with exponential backoff). If all retries fail, the case is escalated
to manual review with a `PROVIDER_UNAVAILABLE` flag and the customer is notified of the delay.

**EX-002B — Biometric Data Processing Failure:**
If the facial recognition service returns an error (server fault, invalid image format), the
system logs the error, allows the customer to retry the liveness step up to 2 additional times,
and escalates to manual review after max retries.

**EX-002C — Confirmed Sanctions Match:**
If a CONFIRMED_MATCH is returned from the sanctions screening, the system: (1) immediately
blocks account creation, (2) does NOT notify the customer of the reason (tipping-off
prevention per BSA), (3) automatically files a draft SAR in the compliance system, and (4)
alerts the Compliance Officer for urgent review and SAR submission within 24 hours.

---

### Business Rules

| Rule ID | Description                                                                           |
|---------|---------------------------------------------------------------------------------------|
| BR-007  | Manual review must be completed within 2 business days per regulatory SLA             |
| BR-008  | All biometric data (liveness photos) deleted from KYC provider after 90 days          |
| BR-009  | PEP screening must run against at minimum: OFAC SDN, UN, EU, HMT lists               |
| BR-010  | KYC documents retained for 7 years minimum (BSA/AML record-keeping)                  |
| BR-011  | Customers with CONFIRMED sanctions match must never receive tipping-off notification  |
| BR-012  | KYC tier upgrade requires full re-verification — partial document updates not allowed |

---

### Non-Functional Requirements

| Category    | Requirement                                                                   |
|-------------|-------------------------------------------------------------------------------|
| Performance | End-to-end KYC automated decision: < 30 seconds P95                          |
| Security    | Biometric data processed in isolated secure enclave; not stored in app DB     |
| Privacy     | GDPR/CCPA compliant — explicit consent logged, data deletion supported        |
| Audit       | Every KYC event immutably logged with actor, timestamp, decision, and score   |
| Resilience  | KYC provider outage must not block all onboarding — fallback to manual queue  |

---

### UI/UX Notes

- Liveness check includes animated guidance overlay (turn left, blink, smile)
- Document upload screen provides real-time quality feedback before submission
- Manual review status page shows estimated wait time and allows document re-upload
- All status updates delivered proactively — customer does not need to poll

---

### Data Requirements

| Field               | Type    | Source        | Notes                                       |
|---------------------|---------|---------------|---------------------------------------------|
| KYC Session ID      | UUID    | System        | Unique per KYC attempt                      |
| Document Type       | Enum    | Customer      | PASSPORT / DRIVERS_LICENSE / NATIONAL_ID    |
| OCR Extracted Name  | String  | KYC Provider  | Must fuzzy-match customer-entered name      |
| OCR Extracted DOB   | Date    | KYC Provider  | Must match customer-entered DOB             |
| Document Number     | String  | KYC Provider  | Stored encrypted                            |
| Liveness Score      | Float   | KYC Provider  | 0.0–1.0 confidence score                    |
| PEP Result          | Enum    | Sanctions DB  | CLEAR / POTENTIAL_MATCH / CONFIRMED_MATCH   |
| KYC Risk Score      | Integer | System        | 0–100 composite score                       |
| KYC Decision        | Enum    | System        | PASS / FAIL / MANUAL_REVIEW                 |
| KYC Tier            | Enum    | System        | TIER_1 / TIER_2 / TIER_3                   |

---

## UC-003: Domestic Transfer

### Summary

A verified customer initiates a domestic fund transfer to a beneficiary within the same country
via the ACH network or internal ledger (for same-bank transfers). The transfer includes MFA
re-authentication, compliance screening, fraud scoring, balance validation, and real-time or
next-business-day settlement depending on the selected rail.

---

### Actors

| Role            | Actor              | Description                                                              |
|-----------------|--------------------|--------------------------------------------------------------------------|
| Primary Actor   | Customer           | Initiates the transfer via mobile app or web portal                      |
| Secondary Actor | Payment Rail (ACH) | Processes the NACHA file and settles funds to the destination account    |
| Secondary Actor | Fraud Service      | Provides real-time ML-based fraud risk scoring                           |
| Secondary Actor | Core Banking       | Executes debit/credit against ledger accounts                            |

---

### Preconditions

1. The customer is authenticated and their session is active.
2. The customer's account is in `ACTIVE` status (not frozen or blocked).
3. The customer has at least one validated beneficiary on file, or adds one during this flow.
4. The transfer amount does not exceed the customer's daily/monthly transaction limit.
5. The destination bank is reachable via ACH or internal routing.

---

### Postconditions

**Success:**
1. The source account is debited for the transfer amount plus any applicable fees.
2. A transaction record is created with a unique reference ID and status `PROCESSING`.
3. An ACH NACHA file entry is submitted to the ACH network (or internal ledger updated).
4. The customer receives a debit confirmation push notification and email receipt.
5. Upon settlement, the transaction status is updated to `SETTLED` and both parties notified.

**Failure:**
1. If the transfer fails (insufficient funds, fraud block, compliance hold), no debit occurs.
2. The transaction is recorded as `FAILED` with a failure reason code for audit purposes.

---

### Main Flow

1. **Initiate Transfer:** The customer navigates to "Transfer Money" and selects "Domestic
   Transfer." The system displays the customer's active accounts as source options.
2. **Select Source Account:** The customer selects the source account. The system displays
   the current available balance and daily limit remaining.
3. **Select Beneficiary:** The customer selects an existing validated beneficiary or initiates
   Add Beneficiary (UC-011 include). New beneficiaries require a 24-hour cooling period
   (BR-013) before the first transfer can be executed.
4. **Enter Transfer Details:** The customer enters the transfer amount, currency (domestic),
   and an optional reference/memo. The system displays applicable fees inline.
5. **MFA Re-Authentication:** For transfers above $500, the system requires step-up
   authentication via OTP (SMS/email) or biometric confirmation.
6. **Compliance Check:** The system runs an AML compliance check against the transaction
   details. The beneficiary account is checked against sanctions lists. High-risk transactions
   are held for compliance review.
7. **Fraud Scoring:** The ML fraud engine evaluates the transaction against behavioral
   patterns. Score > threshold triggers additional authentication; very high score blocks
   the transfer.
8. **Balance Validation:** The system verifies the source account has sufficient available
   balance. Minimum balance requirements are enforced per account type.
9. **Confirmation Screen:** The customer reviews the full transfer summary (amount, fee,
   beneficiary, ETA) and confirms. A 10-second cancellation window is available post-confirm.
10. **Execute Transfer:** The system debits the source account, creates an ACH NACHA file
    entry (or credits the internal ledger for same-bank), and updates the transaction ledger.
11. **Notification & Receipt:** Both the sender (debit confirmation) and receiver (credit
    advisory, if enabled) are notified. A transaction receipt is generated as PDF.

---

### Alternative Flows

**AF-003A — Same-Bank Internal Transfer (Step 10):**
If the destination account is at the same bank, the transfer bypasses the ACH network entirely.
The internal ledger performs a real-time debit/credit within a single atomic database transaction.
Settlement is immediate. The customer sees "Transferred Instantly" on the confirmation screen.

**AF-003B — New Beneficiary During Transfer (Step 3):**
If the customer selects "New Beneficiary," the system invokes UC-011 (Add Beneficiary). The
beneficiary is added with a 24-hour cooling period. The current transfer can be scheduled for
the next day (UC-012) or the customer is informed to initiate a new transfer after the cooling
period expires.

**AF-003C — Transfer Scheduled for Future Date (Customer Choice):**
If the customer selects a future execution date, the system saves the transfer as a scheduled
transaction (UC-012 include) rather than executing immediately. The confirmation screen shows
"Scheduled for [date]" and a management link.

---

### Exception Flows

**EX-003A — Insufficient Funds:**
If the balance check fails, the system returns an "Insufficient funds" error with the current
available balance displayed. The transfer is not debited. The customer is offered options to
transfer a lesser amount or top up their account.

**EX-003B — ACH Network Unavailable:**
If the ACH network is unavailable at time of submission, the system queues the NACHA entry
for submission at the next available ACH processing window. The transaction status is set
to `QUEUED`. The customer is notified of the delay with an updated ETA.

**EX-003C — Compliance Hold:**
If the AML/sanctions check flags the transaction, the transfer is placed in a `COMPLIANCE_HOLD`
status. The customer is notified only that the transfer is "under review" (tipping-off rules
apply). The Compliance Officer reviews and either approves or rejects the hold within 24 hours.

---

### Business Rules

| Rule ID | Description                                                                         |
|---------|-------------------------------------------------------------------------------------|
| BR-013  | New beneficiary cooling period: 24 hours before first transfer is allowed           |
| BR-014  | Step-up MFA required for transfers > $500 per transaction                           |
| BR-015  | Daily transfer limit: $10,000 (Tier 2 KYC); $100,000 (Tier 3 KYC)                  |
| BR-016  | ACH cut-off time: 3:00 PM ET for same-day ACH; next-day for submissions after       |
| BR-017  | Minimum account balance of $0 must be maintained (no overdraft for retail accounts) |
| BR-018  | All transaction data retained for 7 years for regulatory audit purposes             |

---

### Non-Functional Requirements

| Category    | Requirement                                                                   |
|-------------|-------------------------------------------------------------------------------|
| Performance | Transfer initiation to confirmation: < 3 seconds P99                         |
| Availability| Payment service uptime: 99.95% (4.4 hours downtime/year max)                 |
| Security    | All transfer data encrypted in transit (TLS 1.3); fraud scoring isolated      |
| Idempotency | Transfer API is idempotent — duplicate requests identified via client TxnID   |
| Audit       | Every transfer attempt (success and failure) written to immutable audit log   |

---

### UI/UX Notes

- Transfer form shows remaining daily limit dynamically updating as amount is typed
- Beneficiary list shows most-recently-used accounts at the top for quick access
- 10-second cancellation toast appears immediately after confirmation
- Transaction receipt downloadable as PDF from the transaction history screen

---

### Data Requirements

| Field             | Type    | Source     | Validation                                     |
|-------------------|---------|------------|------------------------------------------------|
| Source Account ID | UUID    | System     | Must belong to authenticated customer          |
| Beneficiary ID    | UUID    | Customer   | Must be a validated beneficiary on file        |
| Amount            | Decimal | Customer   | > 0, ≤ daily limit, max 2 decimal places       |
| Currency          | String  | System     | ISO 4217 — domestic currency only for this UC  |
| Reference Memo    | String  | Customer   | Optional, max 140 chars                        |
| Client TxnID      | UUID    | Client App | Idempotency key for deduplication              |
| Transaction ID    | UUID    | System     | Unique transaction identifier                  |
| ACH Trace Number  | String  | ACH Network| 15-digit NACHA trace number post-submission    |

---

## UC-004: International Wire Transfer

### Summary

A verified customer initiates an international wire transfer to a foreign beneficiary bank
account using the SWIFT network (MT103 or ISO 20022). The flow includes mandatory FX
conversion (UC-008 include), enhanced AML screening for cross-border transactions, SWIFT
message generation, and correspondent banking routing.

---

### Actors

| Role            | Actor               | Description                                                          |
|-----------------|---------------------|----------------------------------------------------------------------|
| Primary Actor   | Customer            | Initiates the international wire via app or web                      |
| Secondary Actor | Payment Rail (SWIFT)| Routes and settles the wire via SWIFT MT103 messaging                |
| Secondary Actor | FX Rate Provider    | Provides real-time exchange rates and executes FX conversion         |
| Secondary Actor | Compliance Officer  | Reviews high-value or high-risk international wires if flagged       |

---

### Preconditions

1. The customer has Tier 2 or Tier 3 KYC (international wires not available at Tier 1).
2. The customer has a sufficient source account balance including transfer amount and fees.
3. The destination country is not on the platform's prohibited jurisdiction list.
4. The beneficiary's IBAN/SWIFT BIC is validated and on the approved correspondent banking list.
5. The transfer amount is within the customer's international wire limit.

---

### Postconditions

**Success:**
1. FX conversion is locked at the quoted rate and executed.
2. A SWIFT MT103 message is generated and submitted to the SWIFT network.
3. The source account is debited for the converted amount plus all fees (SWIFT fee, correspondent fee).
4. A unique SWIFT UETR (End-to-End Transaction Reference) is assigned.
5. The customer receives a confirmation with the UETR and estimated delivery date (1–5 business days).

---

### Main Flow

1. **Select International Wire:** The customer navigates to "Transfer Money → International Wire."
2. **Enter Destination Details:** The customer enters beneficiary name, IBAN, SWIFT BIC, destination
   bank name, and country. The system validates the BIC against the SWIFT directory.
3. **Enter Amount and Purpose:** The customer enters the transfer amount in source currency (or
   destination currency), and selects a transfer purpose code (required for regulatory reporting).
4. **FX Conversion (UC-008 include):** The system fetches a live exchange rate. The customer
   is shown the indicative rate, converted amount, total fees, and the rate-lock duration (60 seconds).
5. **Accept Rate:** The customer accepts the FX rate. The rate is locked. If the customer does
   not confirm within 60 seconds, the rate expires and a fresh quote is fetched.
6. **Enhanced Compliance Check:** The system runs enhanced due diligence (EDD) checks:
   sanctions screening on both sender and beneficiary, country risk scoring, and large-value
   wire reporting checks (>$10,000 triggers CTR filing consideration).
7. **MFA Re-Authentication:** The customer confirms with step-up authentication (OTP/biometric).
8. **Confirmation Screen:** The customer reviews all details: beneficiary, IBAN, BIC, converted
   amount, exchange rate, fees, and estimated delivery date. A 30-second cancellation window.
9. **Execute Wire:** The system debits the source account, generates a SWIFT MT103 message with
   all required fields (50K, 59A, 70, 71A, 32A), and submits to the SWIFT network via the
   platform's correspondent bank relationship.
10. **Track and Notify:** The UETR is stored. The customer can track the wire status via gpi
    (SWIFT Global Payments Innovation) tracker. Status notifications are sent at each status
    change (PROCESSING → IN_CORRESPONDENT_BANK → COMPLETED).

---

### Alternative Flows

**AF-004A — Destination Currency Mismatch (Step 4):**
If the customer enters an amount in the destination currency, the system calculates the
equivalent source currency debit and displays it prominently. The customer can toggle between
"I want to send X [source currency]" and "Recipient receives Y [destination currency]."

**AF-004B — Prohibited Jurisdiction (Step 2):**
If the selected destination country is on the prohibited list (e.g., OFAC embargoed countries),
the system immediately terminates the flow with an "International wire not available to this
destination" message. No details are captured, and the event is logged for compliance review.

---

### Exception Flows

**EX-004A — SWIFT Network Unavailable:**
If the SWIFT network connection is unavailable, the MT103 message is queued and retried within
the SWIFT daily window. The customer's source account is debited and the status is set to
`QUEUED_SWIFT`. The customer is notified with the expected retry window.

**EX-004B — Correspondent Bank Rejection:**
If a correspondent bank rejects the MT103 (invalid IBAN, beneficiary bank not reachable), the
system receives a SWIFT MT103-Return message. The debit is reversed, the customer is notified
with the rejection reason (where legally disclosable), and a support ticket is auto-generated.

---

### Business Rules

| Rule ID | Description                                                                                  |
|---------|----------------------------------------------------------------------------------------------|
| BR-019  | International wires require Tier 2+ KYC — Tier 1 customers cannot initiate wires            |
| BR-020  | Wire purpose code is mandatory (SWIFT field 70) for all international transfers              |
| BR-021  | Transfers > $10,000 USD equivalent trigger Currency Transaction Report (CTR) assessment      |
| BR-022  | FX rate lock expires after 60 seconds — customer must reconfirm if expired                  |
| BR-023  | Correspondent bank list reviewed quarterly — transfers only to approved correspondents       |

---

### Non-Functional Requirements

| Category    | Requirement                                                                      |
|-------------|----------------------------------------------------------------------------------|
| Performance | MT103 submission to SWIFT acknowledgment: < 10 seconds                          |
| Compliance  | SWIFT gpi mandatory for all international wires — tracking code assigned at send |
| Security    | SWIFT message signing and encryption per SWIFT CSP (Customer Security Programme) |
| Audit       | Full SWIFT message logs retained for 10 years per SWIFT and BSA requirements    |

---

### UI/UX Notes

- FX rate prominently displayed with countdown timer showing rate lock remaining time
- Estimated delivery date shown as a range (e.g., "2–4 business days") with disclaimer
- SWIFT UETR shown on confirmation for customer reference
- Wire tracker accessible from transaction history using UETR

---

### Data Requirements

| Field             | Type    | Source     | Validation                                  |
|-------------------|---------|------------|---------------------------------------------|
| Beneficiary IBAN  | String  | Customer   | ISO 13616 IBAN format validation            |
| Beneficiary BIC   | String  | Customer   | ISO 9362 BIC validation against SWIFT dir.  |
| Transfer Amount   | Decimal | Customer   | > $0, ≤ international wire daily limit      |
| Source Currency   | String  | System     | ISO 4217                                    |
| Destination Curr. | String  | Customer   | ISO 4217                                    |
| FX Rate           | Decimal | FX Provider| Locked rate, 6 decimal places               |
| Purpose Code      | Enum    | Customer   | SWIFT Category Purpose Codes                |
| SWIFT UETR        | UUID    | System     | RFC 4122 UUID v4, SWIFT format              |
| MT103 Message     | String  | System     | Full SWIFT MT103 formatted message          |

---

## UC-005: Card Freeze / Unfreeze

### Summary

A customer can instantly freeze (temporarily block) or unfreeze their debit or credit card
through the mobile app to prevent unauthorized transactions. Card freeze is a self-service
operation executed in near-real-time. When frozen, all card-present and card-not-present
transactions are declined. Unfreezing re-enables the card without requiring re-issuance.

---

### Actors

| Role            | Actor        | Description                                                             |
|-----------------|--------------|-------------------------------------------------------------------------|
| Primary Actor   | Customer     | Initiates freeze/unfreeze via mobile app or web portal                  |
| Secondary Actor | Card Service | Processes the status change instruction and updates authorization rules |
| Secondary Actor | Bank Admin   | Can override card status in exceptional cases (e.g., force freeze)     |

---

### Preconditions

1. The customer is authenticated with an active session.
2. The customer holds at least one active debit or credit card on the platform.
3. The card to be frozen is in `ACTIVE` or `FROZEN` status (not `CANCELLED` or `EXPIRED`).

---

### Postconditions

**Freeze Success:**
1. The card status is updated to `FROZEN` in the card management system within 5 seconds.
2. All subsequent authorization requests for this card are declined with decline code `62`.
3. The customer receives an immediate push notification and email confirming the card freeze.
4. The freeze action is logged in the audit trail.

**Unfreeze Success:**
1. The card status reverts to `ACTIVE`.
2. Authorization requests resume being processed normally.
3. The customer receives an unfreeze confirmation notification.

---

### Main Flow

1. **Navigate to Card Management:** The customer navigates to "Cards" in the app and selects
   the card they wish to freeze.
2. **View Card Details:** The system displays the card details screen showing: card type,
   masked card number (last 4 digits), expiry date, card status, and spending summary.
3. **Toggle Freeze Switch:** The customer toggles the "Freeze Card" switch from Active to
   Frozen (or vice versa for unfreeze).
4. **Confirm Action:** A confirmation dialog appears: "Freeze this card? All transactions
   will be declined until you unfreeze." The customer confirms or cancels.
5. **Process Request:** The system sends an instant card status update instruction to the
   card management service, which propagates the status change to the authorization engine.
6. **Confirmation:** The card status indicator updates in real-time on the card details screen.
   A notification is dispatched (push + email). The action is written to the audit log.

---

### Alternative Flows

**AF-005A — Freeze All Cards:**
If the customer selects "Freeze All Cards" (panic mode), the system applies a freeze to every
active card on the account simultaneously. A single confirmation dialog covers all cards. This
is designed for situations where the customer's wallet or phone is stolen.

**AF-005B — Scheduled Freeze (Future Use):**
A future enhancement (Phase 3) allows scheduling a freeze for a future date/time (e.g., before
international travel). This flow creates a scheduled job rather than an immediate status update.

---

### Exception Flows

**EX-005A — Card Service Unavailable:**
If the card management service does not respond within 3 seconds, the system displays an error
and instructs the customer to call the emergency card helpline (24/7). The system queues the
freeze request and retries every 30 seconds for up to 5 minutes, notifying the customer when
eventually processed.

**EX-005B — Already in Target State:**
If the customer attempts to freeze an already-frozen card (or unfreeze an active card), the
system displays the current status prominently and does not generate a duplicate request.

---

### Business Rules

| Rule ID | Description                                                                        |
|---------|------------------------------------------------------------------------------------|
| BR-024  | Card freeze takes effect within 5 seconds of customer confirmation (P99)           |
| BR-025  | Customers can freeze/unfreeze unlimited times with no penalty                      |
| BR-026  | Freeze does not affect scheduled/recurring payments (direct debits continue)       |
| BR-027  | A bank-admin-initiated freeze requires Compliance Officer co-approval to lift      |

---

### Non-Functional Requirements

| Category    | Requirement                                                               |
|-------------|---------------------------------------------------------------------------|
| Performance | Card status propagation to auth engine: < 5 seconds P99                  |
| Availability| Card management API: 99.99% uptime — card freeze is a safety-critical UX |
| Security    | Status change requires active authenticated session — no anonymous calls  |

---

### UI/UX Notes

- Toggle switch with clear visual state: green (Active) / grey with snowflake icon (Frozen)
- Immediate visual feedback — no loading spinner; optimistic UI update then server confirmation
- Emergency "Freeze All" button accessible from the main dashboard for speed

---

### Data Requirements

| Field      | Type      | Source    | Notes                                             |
|------------|-----------|-----------|---------------------------------------------------|
| Card ID    | UUID      | System    | Internal card identifier                          |
| Action     | Enum      | Customer  | FREEZE / UNFREEZE                                 |
| Reason     | String    | Customer  | Optional — "Lost card," "Suspicious activity," etc|
| Timestamp  | DateTime  | System    | ISO 8601 UTC timestamp of status change           |
| Actor ID   | UUID      | System    | Customer ID or Admin ID performing the action     |

---

## UC-006: Apply for Loan

### Summary

A verified customer applies for a personal loan through the digital banking platform. The
process includes eligibility pre-screening, credit bureau pull (UC-024 include), internal risk
scoring, automated offer generation, e-signature of the loan agreement, and disbursement to
the customer's linked account.

---

### Actors

| Role            | Actor          | Description                                                          |
|-----------------|----------------|----------------------------------------------------------------------|
| Primary Actor   | Customer       | Applies for the loan and accepts/rejects loan offers                 |
| Secondary Actor | Credit Bureau  | Provides credit score and credit history report                      |
| Secondary Actor | Risk Engine    | Computes internal credit score and DTI ratio                         |
| Secondary Actor | Bank Admin     | Oversees loan origination queue and manual underwriting escalations  |

---

### Preconditions

1. The customer has Tier 2+ KYC (loan products require enhanced identity verification).
2. The customer's account has been active for at least 30 days (anti-fraud policy).
3. The customer does not have an existing active loan in arrears (BR-028).
4. The requested loan amount is within the product's minimum/maximum range.
5. The customer's age is between 21–65 years (product eligibility criteria).

---

### Postconditions

**Success:**
1. A loan account is created in the core banking system with a unique loan account number.
2. The loan amount is disbursed to the customer's nominated current account.
3. A repayment schedule (EMI calendar) is generated and displayed to the customer.
4. An auto-debit mandate is set up for monthly EMI collection.
5. The customer receives a push notification and email with loan agreement and repayment schedule.

**Rejection:**
1. The application is recorded as `REJECTED` with the reason code.
2. The customer receives a declination notice (following adverse action notice requirements).

---

### Main Flow

1. **Access Loan Products:** The customer navigates to "Loans" and views available loan products
   (personal loan, home improvement, education). Product details (interest rates, tenure, amounts)
   are displayed.
2. **Eligibility Pre-Check:** The customer enters desired loan amount and tenure. The system
   runs a soft pre-eligibility check (no hard bureau pull) based on internal account data and
   returns an indicative eligibility result.
3. **Formal Application:** The customer confirms intent to apply. The system captures: purpose
   of loan, employment type, monthly income, and existing liabilities.
4. **Credit Bureau Pull (UC-024 include):** A hard inquiry is placed with the credit bureau.
   The FICO/credit score and credit history are retrieved. This inquiry is recorded on the
   customer's credit file.
5. **Internal Scoring:** The risk engine computes the internal credit score, debt-to-income
   (DTI) ratio, and payment behavior score from internal transaction data.
6. **Eligibility Decision:** If the composite score meets auto-approval thresholds, the system
   generates loan offers. If the score is in the manual range, the application goes to
   underwriting. If below minimum, the application is auto-rejected.
7. **Generate Loan Offers:** The system generates up to 3 loan offers varying in: tenure (12/24/36
   months), interest rate, and monthly EMI. The APR is clearly displayed for each offer.
8. **Customer Selects Offer:** The customer reviews the three offers and selects one. The
   selected offer's full amortization schedule is displayed.
9. **e-Sign Agreement:** The customer digitally signs the loan agreement via e-signature
   (DocuSign or equivalent). The signed document is stored in the document management system.
10. **Loan Disbursement:** Upon e-signature completion, the system: creates the loan account,
    generates the disbursement transaction, and credits the customer's current account within
    2 business hours.
11. **Setup Auto-Debit:** The system establishes an EMI auto-debit mandate against the
    customer's primary account. The first EMI date is set to 30 days from disbursement.
12. **Notification:** The customer receives a push notification and email with the loan account
    number, disbursed amount, EMI amount, first EMI date, and a PDF copy of the signed agreement.

---

### Alternative Flows

**AF-006A — Manual Underwriting (Step 6):**
If the credit score falls in the manual review band (600–720), the application is routed to
the underwriting queue. An underwriter reviews income documents, bank statements (90-day
history), and the application. The underwriter may approve with adjusted terms, reject, or
request additional documentation.

**AF-006B — Counter-Offer Acceptance (Step 8):**
If the customer initially rejects all three generated offers, they are presented with an option
to request a different combination (longer tenure for lower EMI). The system generates a revised
offer set based on the customer's preference input.

---

### Exception Flows

**EX-006A — Credit Bureau Unavailable:**
If the credit bureau API fails, the system queues the application and retries within 30 minutes.
The customer is notified that the application is under review. If retry fails after 3 attempts,
the application is escalated to manual underwriting with available internal data only.

**EX-006B — e-Sign Timeout:**
If the customer does not complete the e-signature within 72 hours (session expiry), the loan
offer expires. The customer must re-initiate the application (a new hard credit pull is not
required within 30 days — a cached bureau result may be used).

---

### Business Rules

| Rule ID | Description                                                                         |
|---------|-------------------------------------------------------------------------------------|
| BR-028  | Customer cannot apply for a new loan if existing loan is >30 days in arrears        |
| BR-029  | Maximum DTI ratio allowed: 50% of verified monthly income                           |
| BR-030  | Adverse action notice must be sent within 30 days of rejection (ECOA compliance)   |
| BR-031  | Hard credit inquiry must be recorded on customer's credit file                      |
| BR-032  | Disbursement must occur within 2 business hours of completed e-signature            |
| BR-033  | APR displayed to customer must comply with TILA disclosure requirements             |

---

### Non-Functional Requirements

| Category    | Requirement                                                                   |
|-------------|-------------------------------------------------------------------------------|
| Performance | Credit bureau response integrated within application flow: < 5 seconds        |
| Security    | Signed loan agreements stored encrypted; tamper-evident digital signatures    |
| Compliance  | TILA, ECOA, FCRA — disclosures, adverse action notices, consent management    |
| Audit       | Full audit trail: application inputs, scores, offer generated, selection made |

---

### UI/UX Notes

- EMI calculator visible throughout the application with sliders for amount/tenure
- Offer comparison table with APR, monthly EMI, total repayable amount, and tenure
- Signed agreement immediately downloadable as PDF on confirmation screen
- Repayment schedule visualized as timeline and downloadable calendar entries

---

### Data Requirements

| Field              | Type    | Source        | Notes                                       |
|--------------------|---------|---------------|---------------------------------------------|
| Loan Amount        | Decimal | Customer      | Min $1,000; Max $50,000 (personal loan)     |
| Tenure             | Integer | Customer      | 12 / 24 / 36 / 48 / 60 months              |
| Purpose Code       | Enum    | Customer      | PERSONAL / HOME_IMPROVEMENT / EDUCATION     |
| Monthly Income     | Decimal | Customer      | Self-declared; verified via bank statements |
| FICO Score         | Integer | Credit Bureau | 300–850 range                               |
| Internal Score     | Integer | Risk Engine   | 0–1000 composite internal score             |
| Approved Rate      | Decimal | System        | Annual interest rate as APR                 |
| Loan Account No.   | String  | System        | Unique loan account number                  |
| Disbursement TxnID | UUID    | System        | Transaction ID for the disbursement entry   |

---

## UC-007: View Statement

### Summary

A customer or Bank Admin views the transaction statement for a selected account over a
specified date range. The statement displays all credits, debits, opening/closing balances,
and transaction metadata. Statements are generated in real-time from the core banking ledger.

---

### Actors

| Role            | Actor       | Description                                                           |
|-----------------|-------------|-----------------------------------------------------------------------|
| Primary Actor   | Customer    | Views their own account statement via mobile app or web portal        |
| Primary Actor   | Bank Admin  | Views any customer's account statement for operational or audit needs |
| Secondary Actor | Core Banking| Provides the transaction ledger data for statement generation         |

---

### Preconditions

1. The requester is authenticated (customer session or admin session).
2. The customer account exists and the requester has authorisation to view it.
3. The selected date range is within the available statement history (last 7 years).
4. The core banking system API is available.

---

### Postconditions

1. The statement is displayed on-screen with all transactions in chronological order.
2. A running balance is shown after each transaction.
3. An on-screen download option is available to export as PDF (UC-014).
4. The statement view event is logged in the audit trail (for admin access particularly).

---

### Main Flow

1. **Navigate to Statements:** The customer selects an account and taps "Statement / History."
2. **Select Date Range:** The customer selects a preset range (Last 30 days, Last 3 months,
   Last year) or a custom date range using a date picker.
3. **Fetch Transactions:** The system queries the core banking ledger for all transactions
   within the selected date range for the account.
4. **Display Statement:** The system renders the statement with: opening balance, each
   transaction (date, description, debit/credit amount, balance after), and closing balance.
5. **Filter and Search:** The customer can filter by transaction type (debit/credit/all),
   search by description keyword, or filter by amount range.
6. **Transaction Detail Drill-Down:** Tapping a transaction shows full details: merchant name,
   category, reference ID, transaction channel, and status.
7. **Export Option:** A "Download PDF" button invokes UC-014 (Download Statement).

---

### Alternative Flows

**AF-007A — No Transactions in Range:**
If no transactions exist for the selected date range, the system displays a "No transactions
found" message with an option to widen the date range.

**AF-007B — Bank Admin View:**
When a Bank Admin accesses a customer statement via the admin portal, the system logs the
access with the admin's user ID, justification (required field), and timestamp. The admin
can view statements up to 7 years back and can see internal reference codes not visible
to the customer.

---

### Exception Flows

**EX-007A — Core Banking API Timeout:**
If the core banking API does not respond within 5 seconds, the system falls back to a cached
statement (up to 15 minutes stale) with a banner: "Showing recently cached data — refresh for
latest transactions." The stale indicator prevents customer confusion.

---

### Business Rules

| Rule ID | Description                                                                     |
|---------|---------------------------------------------------------------------------------|
| BR-034  | Customer can view up to 7 years of statement history (BSA retention requirement)|
| BR-035  | Admin access to customer statements requires a documented justification          |
| BR-036  | Statements display amounts in account's base currency; FX transactions show both|

---

### Non-Functional Requirements

| Category    | Requirement                                                                  |
|-------------|------------------------------------------------------------------------------|
| Performance | Statement load (30-day range): < 2 seconds P95; 12-month: < 5 seconds P95   |
| Security    | Customer can only view their own accounts; admin access fully audited         |
| Caching     | Statement data cached for 15 minutes with stale-while-revalidate pattern     |

---

### UI/UX Notes

- Infinite scroll or pagination (50 transactions per page) for long statement ranges
- Color-coded transactions: green for credits, red for debits
- Category icons next to each transaction for quick visual scanning
- Running balance sparkline chart at the top for overview

---

### Data Requirements

| Field           | Type     | Source       | Notes                                     |
|-----------------|----------|--------------|-------------------------------------------|
| Account ID      | UUID     | System       | Account for which statement is requested  |
| Date Range From | Date     | Customer     | ISO 8601 date; max 7 years ago            |
| Date Range To   | Date     | Customer     | ISO 8601 date; ≤ today                    |
| Transactions    | Array    | Core Banking | Array of transaction objects              |
| Opening Balance | Decimal  | Core Banking | Balance at start of selected date range   |
| Closing Balance | Decimal  | Core Banking | Balance at end of selected date range     |
| Currency        | String   | System       | ISO 4217 account base currency            |

---

*Document Version: 1.0 | Project: Digital Banking Platform | Classification: Internal*
