# User Stories — Digital Banking Platform

| Field | Value |
|---|---|
| Document ID | DBP-US-001 |
| Version | 1.0 |
| Status | Approved |
| Owner | Product Management |
| Last Updated | 2025-01-15 |

## Overview

This document defines the complete set of Agile user stories for the Digital Banking Platform. Stories span three primary personas — **Customer** (retail end-user of the mobile and web application), **Bank Admin** (back-office operator), and **Compliance Officer** (responsible for regulatory oversight and AML/KYC governance). All stories follow the standard Connextra format with Given/When/Then acceptance criteria and are prioritised using the MoSCoW framework, estimated in story points on a modified Fibonacci scale.

## Story Summary Table

| ID | Title | Persona | Priority | Points |
|---|---|---|---|---|
| US-001 | View Account Dashboard | Customer | Must Have | 3 |
| US-002 | Open New Current Account | Customer | Must Have | 8 |
| US-003 | View Transaction History | Customer | Must Have | 5 |
| US-004 | Download Account Statement | Customer | Should Have | 3 |
| US-005 | Close an Account | Customer | Could Have | 5 |
| US-006 | Make Internal Fund Transfer | Customer | Must Have | 5 |
| US-007 | Make Domestic Bank Transfer | Customer | Must Have | 8 |
| US-008 | Make International Wire Transfer | Customer | Must Have | 13 |
| US-009 | Schedule Recurring Transfer | Customer | Should Have | 5 |
| US-010 | Add and Manage Beneficiaries | Customer | Must Have | 5 |
| US-011 | Request Virtual Debit Card | Customer | Must Have | 5 |
| US-012 | Request Physical Debit Card | Customer | Must Have | 8 |
| US-013 | Freeze and Unfreeze Card | Customer | Must Have | 3 |
| US-014 | Set Card Spending Limits | Customer | Should Have | 5 |
| US-015 | Report Lost or Stolen Card | Customer | Must Have | 5 |
| US-016 | Register and Submit KYC Documents | Customer | Must Have | 8 |
| US-017 | Complete Liveness Verification | Customer | Must Have | 5 |
| US-018 | Track KYC Application Status | Customer | Should Have | 3 |
| US-019 | Upgrade KYC Tier | Customer | Should Have | 5 |
| US-020 | Re-submit Failed KYC Documents | Customer | Must Have | 3 |
| US-021 | Check Loan Eligibility | Customer | Must Have | 5 |
| US-022 | Apply for Personal Loan | Customer | Must Have | 13 |
| US-023 | View Loan Repayment Schedule | Customer | Should Have | 3 |
| US-024 | Make Early Loan Repayment | Customer | Should Have | 5 |
| US-025 | Receive Loan Offer Notification | Customer | Must Have | 3 |
| US-026 | Receive Fraud Alert Notification | Customer | Must Have | 5 |
| US-027 | Dispute a Transaction | Customer | Must Have | 8 |
| US-028 | Configure Alert Preferences | Customer | Should Have | 3 |
| US-029 | View Security Activity Log | Customer | Should Have | 3 |
| US-030 | Enable Two-Factor Authentication | Customer | Must Have | 5 |
| US-031 | Manage Customer Accounts | Bank Admin | Must Have | 8 |
| US-032 | Process Manual KYC Review | Compliance Officer | Must Have | 8 |
| US-033 | Generate AML Suspicious Activity Report | Compliance Officer | Must Have | 8 |
| US-034 | Configure Business Rules and Limits | Bank Admin | Must Have | 8 |
| US-035 | Export Regulatory Compliance Report | Compliance Officer | Must Have | 5 |

---

## Account Management

**US-001 — View Account Dashboard**
- **As a** Customer
- **I want** to view a consolidated dashboard showing all my accounts and real-time balances
- **So that** I can quickly assess my overall financial position without navigating multiple screens
- **Priority:** Must Have | **Story Points:** 3
- **Acceptance Criteria:**
  - Given I am authenticated, when I navigate to the dashboard, then all accounts with current balances are displayed in real time with last-refresh timestamp.
  - Given I have multiple currency accounts, when the dashboard loads, then each account shows its native currency balance alongside a base-currency GBP equivalent.
  - Given a balance changes due to a posted transaction, when I refresh the dashboard, then the updated balance is reflected within 5 seconds.

**US-002 — Open New Current Account**
- **As a** Customer
- **I want** to open a new current account entirely within the mobile application
- **So that** I can access full banking services without visiting a physical branch
- **Priority:** Must Have | **Story Points:** 8
- **Acceptance Criteria:**
  - Given I am KYC-approved at Tier 2 or above, when I submit an account opening request, then the account is created within 60 seconds and a unique IBAN is assigned.
  - Given the account is created, when the provisioning completes, then I receive a push notification containing the new IBAN and account number.
  - Given my KYC status is not yet APPROVED, when I attempt to open an account, then I am redirected to the KYC onboarding flow with a clear contextual explanation.
  - Given account creation fails due to a downstream system error, when the error is caught, then I receive a user-friendly message and a support reference number.

**US-003 — View Transaction History**
- **As a** Customer
- **I want** to browse a paginated and filterable list of all transactions on any of my accounts
- **So that** I can track my spending patterns and reconcile my finances accurately
- **Priority:** Must Have | **Story Points:** 5
- **Acceptance Criteria:**
  - Given I am on the account detail screen, when I open the transaction list, then all transactions are shown in reverse chronological order with date, merchant name, category, and signed amount.
  - Given I apply a date range filter, when results are returned, then only transactions within the specified range are displayed and a running total is shown.
  - Given I search by merchant name or reference, when the search executes, then matching transactions are returned within 2 seconds regardless of pagination depth.

**US-004 — Download Account Statement**
- **As a** Customer
- **I want** to download an official PDF or CSV statement for any calendar month within the past 7 years
- **So that** I can use authoritative documentation for visa applications, tenancy agreements, or tax filings
- **Priority:** Should Have | **Story Points:** 3
- **Acceptance Criteria:**
  - Given I select a target month and output format, when I request the statement, then a correctly formatted document is generated and available for download within 10 seconds.
  - Given the statement is generated, when I open it, then it includes the platform logo, full account name, IBAN, sort code, opening balance, and closing balance with all transactions itemised.
  - Given no transactions occurred in the selected period, when the statement is generated, then it correctly displays a nil-movement statement noting the opening and closing balances.

**US-005 — Close an Account**
- **As a** Customer
- **I want** to initiate account closure through the app without speaking to an agent
- **So that** I can exit the service entirely at my own convenience
- **Priority:** Could Have | **Story Points:** 5
- **Acceptance Criteria:**
  - Given my account balance is zero and no pending transactions exist, when I confirm the closure request, then the account status is set to CLOSED within 24 hours and I receive written confirmation.
  - Given my account holds a non-zero balance, when I attempt to initiate closure, then I am prompted to transfer the remaining funds or provide a nominated external account before the request is accepted.
  - Given the account is closed, when I log in, then the closed account remains visible in a read-only archived state for 12 months to allow retrospective statement access.

---

## Money Transfers

**US-006 — Make Internal Fund Transfer**
- **As a** Customer
- **I want** to transfer funds instantly between any two of my own accounts on the platform
- **So that** I can rebalance my savings and current accounts without any processing delay
- **Priority:** Must Have | **Story Points:** 5
- **Acceptance Criteria:**
  - Given I select valid source and destination accounts that I own, when I confirm the transfer amount, then funds are moved instantly and both balances are updated atomically.
  - Given the source account has insufficient available funds, when I submit the transfer, then the request is rejected with a clear insufficient-funds message and no debit is applied.
  - Given the transfer succeeds, when it completes, then a credit and debit transaction record are created for the respective accounts and reflected in both transaction histories.

**US-007 — Make Domestic Bank Transfer**
- **As a** Customer
- **I want** to send money to any UK bank account using Faster Payments or BACS
- **So that** I can pay bills, rent, and individuals digitally without needing cash or branch visits
- **Priority:** Must Have | **Story Points:** 8
- **Acceptance Criteria:**
  - Given I enter a valid sort code and account number, when I confirm the payment details, then the transfer instruction is submitted to the Faster Payments rail within 30 seconds of confirmation.
  - Given my cumulative daily outbound transfers exceed the limit for my KYC tier, when I attempt the transfer, then the transaction is declined and I am informed of my remaining daily allowance.
  - Given the Faster Payments rail confirms successful settlement, when the confirmation event is received, then I receive a push notification containing the payment reference and settlement timestamp.
  - Given the beneficiary account number and sort code combination is invalid per Confirmation of Payee, when the check runs, then the transfer is blocked before any funds are debited.

**US-008 — Make International Wire Transfer**
- **As a** Customer
- **I want** to send money internationally via SWIFT to any supported destination country
- **So that** I can support family abroad and settle international invoices without a bureau de change
- **Priority:** Must Have | **Story Points:** 13
- **Acceptance Criteria:**
  - Given I enter a valid IBAN and BIC/SWIFT code, when I request an FX quote, then the live mid-market rate, platform margin, all applicable fees, and recipient net amount are displayed before confirmation.
  - Given the transfer amount exceeds £10,000 and I am a Tier 3 customer, when I proceed, then enhanced due diligence questions are presented and must be completed before the instruction is submitted.
  - Given the destination country or beneficiary name matches an OFAC, HM Treasury, or EU consolidated sanctions list entry, when the check is evaluated, then the transfer is blocked and a compliance alert is raised.
  - Given the SWIFT instruction is successfully dispatched, when the acknowledgement is received, then I am provided with a UETR reference number for real-time GPI tracking.

**US-009 — Schedule Recurring Transfer**
- **As a** Customer
- **I want** to configure a standing order for a fixed amount payable at a regular interval
- **So that** I can automate recurring obligations such as rent contributions and savings deposits without manual intervention
- **Priority:** Should Have | **Story Points:** 5
- **Acceptance Criteria:**
  - Given I create a standing order specifying amount, frequency, and a future start date, when the first execution date arrives, then the payment is processed automatically without requiring any interaction.
  - Given a standing order execution fails due to insufficient funds, when the failure occurs, then I am notified immediately and the order is suspended pending my explicit action to resume or cancel.
  - Given I cancel a standing order at any point before its next scheduled execution, when the cancellation is confirmed, then no further payments are processed under that standing order.

**US-010 — Add and Manage Beneficiaries**
- **As a** Customer
- **I want** to maintain a saved address book of payee account details as named beneficiaries
- **So that** I can initiate repeat payments quickly without re-entering full account details each time
- **Priority:** Must Have | **Story Points:** 5
- **Acceptance Criteria:**
  - Given I enter a sort code and account number, when I save the beneficiary, then the payee name is validated via Confirmation of Payee and the confirmed name is displayed to me before the record is persisted.
  - Given I have saved beneficiaries in my address book, when I initiate a bank transfer, then I can select from the saved list and the account details are pre-populated automatically.
  - Given I delete a beneficiary from my address book, when the deletion is confirmed, then no future payments can be directed to that account entry without explicitly re-adding it.

---

## Card Management

**US-011 — Request Virtual Debit Card**
- **As a** Customer
- **I want** to receive an instantly provisioned virtual debit card linked to my current account
- **So that** I can begin making online and contactless purchases immediately after account approval
- **Priority:** Must Have | **Story Points:** 5
- **Acceptance Criteria:**
  - Given I am KYC-approved and my current account is in ACTIVE status, when I request a virtual card, then the card is provisioned and available for use within 60 seconds.
  - Given the card is provisioned, when I navigate to the card detail view, then the full 16-digit PAN, expiry date, and CVV2 are shown only after successful biometric authentication.
  - Given the virtual card is active, when I initiate tokenisation to Apple Pay or Google Pay, then the in-app provisioning flow completes and the wallet token is active within 2 minutes.

**US-012 — Request Physical Debit Card**
- **As a** Customer
- **I want** to order a physical debit card to be delivered to my registered address
- **So that** I can make in-store chip-and-PIN payments and ATM cash withdrawals
- **Priority:** Must Have | **Story Points:** 8
- **Acceptance Criteria:**
  - Given I submit a physical card request, when the request is received, then a card production order is raised with the card bureau within 1 hour and I receive a confirmation notification.
  - Given the card is dispatched by the bureau, when the dispatch event is received via webhook, then I receive a push notification stating the estimated delivery window.
  - Given the card arrives and I activate it via the app using the last 4 digits of the card and a one-time passcode, then the card transitions to ACTIVE within 30 seconds of activation.

**US-013 — Freeze and Unfreeze Card**
- **As a** Customer
- **I want** to instantly freeze any of my debit cards directly from the app
- **So that** I can prevent unauthorised use when I suspect a card is misplaced without permanently cancelling it
- **Priority:** Must Have | **Story Points:** 3
- **Acceptance Criteria:**
  - Given my card is ACTIVE, when I engage the freeze toggle in card settings, then the card enters FROZEN status and all new purchase authorisations are declined within 5 seconds.
  - Given my card is FROZEN, when I disengage the freeze toggle, then the card is immediately restored to ACTIVE and subsequent transactions are authorised normally.
  - Given the card is FROZEN, when a contactless, chip-and-PIN, or card-not-present transaction is attempted, then the terminal or gateway receives a card-declined response with reason code 62.

**US-014 — Set Card Spending Limits**
- **As a** Customer
- **I want** to configure personalised daily purchase and ATM withdrawal limits on each card
- **So that** I have granular control over my exposure and can limit potential fraud losses
- **Priority:** Should Have | **Story Points:** 5
- **Acceptance Criteria:**
  - Given I open card settings for an active card, when I set a daily POS limit at or below the maximum permitted for my KYC tier, then the new limit is applied to the card immediately.
  - Given I attempt to save a spending limit that exceeds the maximum for my KYC tier, when I submit, then the system rejects the value and displays the maximum permitted amount.
  - Given a custom daily limit is active, when a transaction would cause the day's total to exceed my configured limit, then the authorisation is declined with a limit-exceeded response code before any charges are applied.

**US-015 — Report Lost or Stolen Card**
- **As a** Customer
- **I want** to permanently cancel a lost or stolen card and request a replacement entirely within the app
- **So that** I can protect my finances immediately without waiting on hold with customer support
- **Priority:** Must Have | **Story Points:** 5
- **Acceptance Criteria:**
  - Given I report a card as lost or stolen and confirm the action, when confirmation is accepted, then the card status changes to CANCELLED and all future authorisations are declined within 10 seconds.
  - Given the card is cancelled, when the report is confirmed, then a replacement card production order is automatically raised to my registered address unless I explicitly opt out at the confirmation screen.
  - Given a replacement card is ordered, when it is produced by the bureau, then it carries a freshly generated PAN, expiry date, and CVV distinct from the cancelled card.

---

## KYC and Onboarding

**US-016 — Register and Submit KYC Documents**
- **As a** Customer
- **I want** to complete identity verification by photographing and uploading my passport or government-issued ID
- **So that** I can gain full platform access and unlock the transaction limits associated with a verified account
- **Priority:** Must Have | **Story Points:** 8
- **Acceptance Criteria:**
  - Given I select a document type, when I capture and upload images, then each image is validated for acceptable resolution, absence of glare, and full border visibility before submission is allowed.
  - Given images pass initial quality validation, when they are submitted to the KYC provider, then an acknowledgement containing a case reference number is returned to me within 5 seconds.
  - Given the document quality is insufficient for automated reading, when the check fails, then I am prompted with specific guidance on correcting lighting, angle, or distance before re-attempting the upload.

**US-017 — Complete Liveness Verification**
- **As a** Customer
- **I want** to complete a biometric liveness challenge using my device camera
- **So that** the platform can confirm I am a real, present person whose face matches the submitted identity document
- **Priority:** Must Have | **Story Points:** 5
- **Acceptance Criteria:**
  - Given I reach the liveness verification step, when I complete the randomised facial motion sequence, then the captured biometric data is transmitted to the KYC provider within 3 seconds.
  - Given the liveness check returns a positive result, when the result is received, then my KYC record status is updated to LIVENESS_PASSED and I am advanced to the next onboarding step.
  - Given the liveness check fails three consecutive times within one session, when the third failure is recorded, then my account is placed in MANUAL_REVIEW status and I receive a notification explaining next steps.

**US-018 — Track KYC Application Status**
- **As a** Customer
- **I want** to view the real-time status of my KYC application with clear per-step progress indicators
- **So that** I know precisely which steps are complete and can take action on any that are outstanding
- **Priority:** Should Have | **Story Points:** 3
- **Acceptance Criteria:**
  - Given I navigate to the onboarding status screen, when it loads, then each step (document upload, liveness check, identity review) displays one of: Pending, In Progress, Completed, or Action Required.
  - Given my application is under manual review, when I view the status screen, then the expected review duration (up to 2 business days) is shown alongside a reference number for support queries.
  - Given any status transitions, when the change is recorded in the system, then a push notification is dispatched to my device within 60 seconds.

**US-019 — Upgrade KYC Tier**
- **As a** Customer
- **I want** to voluntarily upgrade from Tier 1 to Tier 2 by providing additional documentary evidence
- **So that** I can unlock higher daily transaction limits and become eligible for lending products
- **Priority:** Should Have | **Story Points:** 5
- **Acceptance Criteria:**
  - Given I am a Tier 1 customer in good standing, when I initiate a tier upgrade, then I am presented with the specific document types and evidence standards required for Tier 2 approval.
  - Given I submit all required documents and the KYC provider verification is positive, when the result is processed, then my tier is upgraded immediately and new limits are applied to all subsequent transactions.
  - Given my tier upgrade is approved, when the change takes effect, then I receive a confirmation notification explicitly itemising my new daily transfer, card spending, and ATM withdrawal limits.

**US-020 — Re-submit Failed KYC Documents**
- **As a** Customer
- **I want** to correct and re-submit my KYC documents after an initial rejection without restarting the entire application
- **So that** I can resolve document issues and complete onboarding with the least possible friction
- **Priority:** Must Have | **Story Points:** 3
- **Acceptance Criteria:**
  - Given my KYC status is REFER, when I open the onboarding screen, then the exact failure reason is displayed alongside specific, actionable guidance for producing acceptable document images.
  - Given I re-submit corrected documents, when the new submission is received, then a fresh KYC verification case is opened and cross-referenced to the prior case for audit continuity.
  - Given three consecutive document rejections are recorded for a single customer, when the third rejection is logged, then the case is automatically escalated to the compliance review queue with no further self-service option available.

---

## Loans and Credit

**US-021 — Check Loan Eligibility**
- **As a** Customer
- **I want** to receive an indicative eligibility assessment for a personal loan without any credit file impact
- **So that** I can explore borrowing options confidently before committing to a formal application
- **Priority:** Must Have | **Story Points:** 5
- **Acceptance Criteria:**
  - Given I request an eligibility check, when the soft credit enquiry is executed, then a result is returned within 10 seconds and no hard footprint is registered on my credit file.
  - Given I am assessed as eligible, when the result screen loads, then indicative loan ranges, representative APRs, and available term options are presented clearly.
  - Given I am assessed as ineligible, when the result is displayed, then the primary reason for ineligibility is communicated and constructive improvement steps are suggested.

**US-022 — Apply for Personal Loan**
- **As a** Customer
- **I want** to complete a full personal loan application and receive a binding credit decision entirely within the app
- **So that** I can access credit and receive disbursement without any branch interaction
- **Priority:** Must Have | **Story Points:** 13
- **Acceptance Criteria:**
  - Given I submit a complete loan application, when the hard credit check is executed, then a binding lending decision is returned within 60 seconds.
  - Given a loan is approved, when the offer is generated, then the APR, total amount payable, monthly instalment, and total cost of credit are stated in compliance with Consumer Credit Act requirements.
  - Given I accept the offer and sign the digital loan agreement, when the executed agreement is received, then the approved principal is disbursed to my nominated current account within 2 hours.
  - Given my application is declined, when the decision is communicated, then I receive the primary reason code and information on requesting a full manual review.

**US-023 — View Loan Repayment Schedule**
- **As a** Customer
- **I want** to view a full amortisation table for my active loan
- **So that** I can plan my monthly budget with full visibility of principal, interest, and outstanding balance at each period
- **Priority:** Should Have | **Story Points:** 3
- **Acceptance Criteria:**
  - Given I have at least one active loan, when I open the loan detail screen, then a month-by-month schedule shows the payment date, principal amount, interest charged, and closing balance for every remaining period.
  - Given I have made an overpayment, when I view the schedule, then future instalments are recalculated to reflect the reduced principal balance.
  - Given I select the export option, when the export completes, then a PDF amortisation table is generated referencing the loan agreement number.

**US-024 — Make Early Loan Repayment**
- **As a** Customer
- **I want** to submit a partial or full early repayment against my outstanding loan principal
- **So that** I can reduce total interest costs by paying down the balance ahead of the scheduled term
- **Priority:** Should Have | **Story Points:** 5
- **Acceptance Criteria:**
  - Given I request a settlement quote, when the quote is calculated, then any early repayment charges, the outstanding principal, accrued interest, and total settlement amount are itemised clearly.
  - Given I confirm an early repayment, when the payment is processed, then the outstanding balance is reduced and a revised repayment schedule reflecting the new principal is issued immediately.
  - Given an early repayment fully clears the outstanding balance, when the settlement is processed, then the loan status transitions to SETTLED and any associated account charges or liens are released.

**US-025 — Receive Loan Offer Notification**
- **As a** Customer
- **I want** to receive a proactive in-app and push notification when a pre-approved loan offer is generated for my profile
- **So that** I can benefit from timely, personalised credit offers without actively searching for them
- **Priority:** Must Have | **Story Points:** 3
- **Acceptance Criteria:**
  - Given a pre-approved offer is created for my customer profile, when the offer record is written, then a push notification is dispatched within 30 seconds and an in-app inbox message is created.
  - Given I open the notification, when the offer detail screen loads, then the offered principal, APR, available terms, monthly cost, and expiry date are all clearly displayed.
  - Given the offer passes its expiry date without acceptance, when expiry is evaluated, then the offer is removed from the in-app inbox and no further promotional messages are sent for that specific offer.

---

## Fraud and Alerts

**US-026 — Receive Fraud Alert Notification**
- **As a** Customer
- **I want** to receive an immediate push notification when my fraud engine flags a suspicious transaction
- **So that** I can confirm or refute the transaction instantly and contain any potential financial loss
- **Priority:** Must Have | **Story Points:** 5
- **Acceptance Criteria:**
  - Given the fraud engine assigns a high-risk score to a transaction, when the flag is raised, then a push notification is dispatched within 30 seconds containing the merchant name, amount, and transaction time.
  - Given I respond to the alert by selecting "Not Me", when my response is recorded, then the associated card is frozen and a fraud dispute case is opened within 5 seconds.
  - Given I respond to the alert by selecting "This was me", when my confirmation is logged, then the transaction is approved, the flag is cleared, and no further action is taken on my account.

**US-027 — Dispute a Transaction**
- **As a** Customer
- **I want** to raise a formal dispute against any unrecognised, duplicate, or incorrectly charged transaction
- **So that** I can seek a chargeback or resolution without having to escalate outside the platform
- **Priority:** Must Have | **Story Points:** 8
- **Acceptance Criteria:**
  - Given I select a specific transaction and submit a dispute with a reason category, when the case is created, then a unique case reference number is returned to me within 5 seconds.
  - Given my dispute is accepted, when the case is opened, then I receive an acknowledgement stating the maximum resolution timeline of 15 business days under the Payment Services Regulations.
  - Given the dispute is resolved in my favour, when the decision is finalised, then the disputed amount is provisionally credited to my account within 2 business days of the decision.
  - Given the dispute is not upheld, when the decision is communicated, then I receive a written explanation and information on escalation to the Financial Ombudsman Service.

**US-028 — Configure Alert Preferences**
- **As a** Customer
- **I want** to define which event types trigger notifications and via which channel (push, SMS, or email)
- **So that** I receive only alerts that are relevant to my needs and avoid unnecessary notification fatigue
- **Priority:** Should Have | **Story Points:** 3
- **Acceptance Criteria:**
  - Given I open the alerts preferences screen, when I toggle a channel for a specific event type, then the preference is persisted and applied to all subsequent qualifying events within 30 seconds.
  - Given I set a minimum threshold below which transaction alerts are suppressed, when a transaction below my threshold occurs, then no notification is sent for that event.
  - Given a security or regulatory notification is triggered (fraud alert, 2FA challenge, account restriction), when it occurs, then it is dispatched immediately regardless of any personal notification preferences.

**US-029 — View Security Activity Log**
- **As a** Customer
- **I want** to review a chronological log of all authentication events and security changes on my account
- **So that** I can promptly detect any signs of unauthorised access or account compromise
- **Priority:** Should Have | **Story Points:** 3
- **Acceptance Criteria:**
  - Given I open the security activity log, when the page loads, then all login events from the past 90 days are shown with device fingerprint, approximate geolocation, IP address, and UTC timestamp.
  - Given I identify a login event on an unrecognised device, when I select it, then I am offered the option to immediately terminate that session and change my password.
  - Given there are no login events in the queried period, when the log loads, then a confirmation message states that no authentication activity was recorded during that period.

**US-030 — Enable Two-Factor Authentication**
- **As a** Customer
- **I want** to enable two-factor authentication using a TOTP authenticator application or SMS one-time passcode
- **So that** my account remains secure even if my primary password is ever compromised
- **Priority:** Must Have | **Story Points:** 5
- **Acceptance Criteria:**
  - Given I navigate to the security settings, when I enable TOTP-based 2FA, then I am presented with a scannable QR code and must supply a valid code from my authenticator app to confirm setup.
  - Given 2FA is active on my account, when I complete a login with valid credentials, then I am required to supply a current one-time code before access is granted.
  - Given I declare loss of access to my registered 2FA device, when I request a recovery, then my identity is re-verified via an alternative trusted channel before 2FA configuration is reset.

---

## Administration and Compliance

**US-031 — Manage Customer Accounts**
- **As a** Bank Admin
- **I want** to search, view, and modify customer profiles and account details from the back-office portal
- **So that** I can resolve operational queries accurately and maintain the integrity of customer data
- **Priority:** Must Have | **Story Points:** 8
- **Acceptance Criteria:**
  - Given I search by customer ID, email address, or phone number, when results load, then the full customer profile including KYC status, linked accounts, cards, and last 30 transactions is displayed.
  - Given I modify a customer's contact details, when the change is saved, then an immutable audit log entry is created recording my admin user ID, changed field names, old and new values, and the UTC timestamp.
  - Given I apply a debit restriction to a customer account, when the restriction is activated, then all outbound transactions are declined in real time and the customer receives a notification informing them to contact support.

**US-032 — Process Manual KYC Review**
- **As a** Compliance Officer
- **I want** to adjudicate KYC applications that have been escalated for manual review
- **So that** customers in the REFER queue are assessed promptly and consistently against regulatory standards
- **Priority:** Must Have | **Story Points:** 8
- **Acceptance Criteria:**
  - Given a KYC case is in REFER status, when I open the compliance review interface, then the document images, OCR extraction output, liveness result, and automated risk score are presented side by side.
  - Given I reach a decision, when I attempt to save it, then I am required to supply a written justification of at least 20 characters before the decision can be submitted.
  - Given I approve the case, when the approval is saved, then the customer's KYC status is set to APPROVED, transaction limits are adjusted to the approved tier, and a welcome notification is dispatched.
  - Given I reject the case, when the rejection is saved, then the customer receives a notification with the specific grounds for rejection and instructions for accessing the formal appeals process.

**US-033 — Generate AML Suspicious Activity Report**
- **As a** Compliance Officer
- **I want** to prepare and electronically submit a Suspicious Activity Report for any customer flagged under AML monitoring rules
- **So that** the institution meets its statutory obligation to report under the Proceeds of Crime Act and associated regulations
- **Priority:** Must Have | **Story Points:** 8
- **Acceptance Criteria:**
  - Given I identify a customer for SAR filing, when I initiate the report, then the system auto-populates the SAR template with all relevant transaction data, account identifiers, and verified personal details.
  - Given I review and submit the completed SAR, when submission is processed, then a submission reference number, filing timestamp, and gateway acknowledgement are recorded against the customer record.
  - Given a SAR is submitted, when the record is updated, then a SAR flag is applied to the customer profile, enhanced monitoring rules are activated, and no disclosure of the filing is surfaced to the customer or any unauthorised party.

**US-034 — Configure Business Rules and Limits**
- **As a** Bank Admin
- **I want** to update transaction limits, velocity thresholds, and business rule parameters via the administration portal without requiring a software deployment
- **So that** the platform can respond quickly to changing risk appetites and emerging regulatory requirements
- **Priority:** Must Have | **Story Points:** 8
- **Acceptance Criteria:**
  - Given I update a transaction limit for a specific KYC tier, when the change is saved, then the new limit is propagated to the business rule engine and applied to all subsequent transactions within 60 seconds.
  - Given I submit a rule parameter change, when the change is received, then a four-eyes approval workflow is triggered and a second authorised admin must independently confirm before the change takes effect.
  - Given I query the rules change history, when the audit trail loads, then all historical parameter values, effective dates, and the admin user ID responsible for each change are visible.

**US-035 — Export Regulatory Compliance Report**
- **As a** Compliance Officer
- **I want** to generate a structured compliance report covering transaction volumes, SAR counts, KYC approval rates, and AML velocity metrics for any defined period
- **So that** I can fulfil scheduled submission obligations to the FCA, FINRA, or other applicable regulators accurately and on time
- **Priority:** Must Have | **Story Points:** 5
- **Acceptance Criteria:**
  - Given I select a reporting period and report type, when I generate the report, then it is produced within 30 seconds containing all data fields mandated for the relevant regulatory template.
  - Given the report is generated, when I choose to export, then it is available for download in both a human-readable PDF and a machine-processable CSV format.
  - Given I configure a recurring report schedule, when the scheduled generation time arrives, then the report is automatically produced and delivered to the designated compliance distribution email address.
