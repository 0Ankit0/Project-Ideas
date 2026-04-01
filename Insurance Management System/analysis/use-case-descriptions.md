# Use Case Descriptions — Insurance Management System

## Overview

This document provides structured, template-driven descriptions for the eight key use cases of the
Insurance Management System (IMS). Each use case follows a standardised format covering actors,
pre- and post-conditions, the main success scenario, and both alternative and exception flows. These
descriptions serve as the primary input to functional test case design, API contract definition, and
developer acceptance criteria.

Use case IDs correspond to the entries in `use-case-diagram.md`. All external system interactions
referenced (payment gateways, fraud scoring service, credit bureau) are detailed in
`system-context-diagram.md`.

---

## UC-001: Get Insurance Quote

### Summary Table

| Field              | Details                                                                                         |
|--------------------|-------------------------------------------------------------------------------------------------|
| **Use Case ID**    | UC-001                                                                                          |
| **Name**           | Get Insurance Quote                                                                             |
| **Actor(s)**       | PolicyHolder (primary), Broker (primary), Agent (primary)                                      |
| **Preconditions**  | Actor is authenticated. Product line is active in the product catalog. Rating tables are loaded. |
| **Postconditions** | A premium estimate is generated and stored as a quote record (status: DRAFT) with a 30-day TTL. |

### Main Flow

1. Actor selects the insurance product line (life, health, auto, home, or commercial).
2. System presents the dynamic application form based on the selected product's data requirements.
3. Actor enters risk information: insured details, coverage amounts, deductible preferences, and
   any supplemental risk data (vehicle make/model/year for auto; property construction for home).
4. System validates mandatory fields and data type constraints in real time (client-side and
   server-side validation).
5. System submits risk data to the Rating Engine.
6. Rating Engine applies actuarial rate tables, territory factors, credit score adjustments, and
   claims history loadings to calculate the base premium.
7. System retrieves credit score from the Credit Bureau API (soft inquiry, non-impacting).
8. System applies credit-based insurance score (CBIS) factor to the base premium.
9. System calculates applicable taxes, levies, and policy fees.
10. System returns a fully itemised quote including base premium, loadings, taxes, and total annual
    and installment amounts.
11. System persists the quote record with a unique Quote Reference Number (QRN).
12. System presents the quote to the actor with option to Accept, Modify, or Save for Later.

### Alternative Flows

- **AF-1: Multi-Coverage Bundle** — If the actor requests a bundled product (e.g., home + auto),
  the system runs separate rating calls per coverage and applies the applicable multi-policy
  discount before presenting a combined quote.
- **AF-2: Broker Comparative Quote** — If the actor is a Broker with comparative rating access,
  the system presents quotes for multiple insurer products side-by-side using the broker portal
  integration, allowing selection before binding.
- **AF-3: Quote Retrieval** — If the actor provides an existing QRN, the system retrieves the
  saved quote rather than initiating a new rating cycle, provided the quote has not expired.

### Exception Flows

- **EF-1: Credit Bureau API Unavailable** — System proceeds with rating using a neutral credit
  factor (no surcharge, no discount) and logs a warning. A manual credit check flag is set on the
  resulting policy application.
- **EF-2: Rating Engine Timeout** — System retries the rating request up to three times with
  exponential back-off. After three failures, the system returns a referral quote and routes it to
  an Underwriter for manual rating.
- **EF-3: Risk Declined by Rules Engine** — If automated rules detect a non-acceptable risk
  (e.g., prior total loss, sanctions match), the system displays a declination message. No quote
  record is persisted. The actor may contact an Underwriter for a manual review.

---

## UC-002: Issue Policy

### Summary Table

| Field              | Details                                                                                               |
|--------------------|-------------------------------------------------------------------------------------------------------|
| **Use Case ID**    | UC-002                                                                                                |
| **Name**           | Issue Policy                                                                                          |
| **Actor(s)**       | Broker (primary), Agent (primary), Underwriter (secondary), Admin (secondary)                        |
| **Preconditions**  | A quote (QRN) exists in ACCEPTED status. First premium payment has been collected or is confirmed.    |
| **Postconditions** | A Policy Number is issued. Policy record is created in ACTIVE status. Policy documents are generated and dispatched. |

### Main Flow

1. Actor retrieves the accepted quote by QRN.
2. System validates that the quote has not expired and all required documents have been uploaded
   (KYC proof, vehicle registration for auto, property survey for commercial).
3. System runs final sanctions and AML screening against the insured name and address.
4. System confirms first premium receipt from the Billing Engine (or processes payment if not yet
   collected).
5. System assigns a unique Policy Number following the configured numbering schema
   (line-of-business prefix + year + sequence).
6. System creates the policy record with status ACTIVE, effective date, expiry date, coverage
   details, deductibles, exclusions, and premium schedule.
7. System generates the Policy Schedule (Certificate of Insurance), Policy Wording document, and
   Direct Debit mandate or payment confirmation as a PDF package.
8. System dispatches documents to the policyholder via the configured channel (email, postal, portal
   download) and to the broker/agent record.
9. System notifies the Billing Engine to configure the instalment schedule.
10. System triggers the Reinsurance Ledger to evaluate treaty applicability for the new risk.

### Alternative Flows

- **AF-1: Underwriter Referral** — If the quote required manual underwriting and was approved with
  special conditions (e.g., endorsement restricting cover, higher excess), the policy is created
  with those special conditions appended to the wording and flagged on the policy record.
- **AF-2: Commercial Group Policy** — If a commercial broker is binding a group policy (e.g.,
  fleet of 50 vehicles), the system creates a master policy record with individual risk schedules
  attached rather than individual policies.

### Exception Flows

- **EF-1: Sanctions Match** — If the final AML/sanctions check returns a positive match, policy
  issuance is blocked. The case is escalated to the Compliance Officer queue. A Suspicious Activity
  Report (SAR) workflow is initiated. The actor receives a generic decline message without
  revealing the sanctions reason.
- **EF-2: Document Verification Failure** — If uploaded identity documents fail automated
  verification (e.g., expired passport, mismatched name), the system places the application in
  PENDING_DOCUMENTS status and notifies the actor via email with a list of outstanding requirements.
- **EF-3: Payment Failure** — If first premium payment fails at the point of binding, the system
  reverts the policy to QUOTE_ACCEPTED status and sends a payment retry notification. The policy
  is not issued until confirmed payment is received.

---

## UC-003: File Claim (FNOL)

### Summary Table

| Field              | Details                                                                                              |
|--------------------|------------------------------------------------------------------------------------------------------|
| **Use Case ID**    | UC-003                                                                                               |
| **Name**           | File Claim — First Notice of Loss (FNOL)                                                             |
| **Actor(s)**       | PolicyHolder (primary), ClaimsAdjuster (secondary)                                                   |
| **Preconditions**  | PolicyHolder has an active policy. The loss event date falls within the policy period.               |
| **Postconditions** | A Claim Reference Number (CRN) is created. A ClaimsAdjuster is assigned. A reserve is opened.       |

### Main Flow

1. PolicyHolder logs into the self-service portal or contacts the claims intake team.
2. PolicyHolder selects the policy against which the claim is being filed.
3. System validates that the policy is in ACTIVE status and the reported loss date is within the
   policy period.
4. PolicyHolder enters FNOL details: date of loss, time, location, description of incident,
   estimated loss value, and third-party information (where applicable for liability claims).
5. PolicyHolder uploads initial supporting evidence (photographs, police report reference, medical
   certificate).
6. System assigns a Claim Reference Number (CRN) and sets claim status to REGISTERED.
7. System opens an initial reserve based on the reported loss type and estimated value using
   standard reserve adequacy factors.
8. System applies assignment rules to select the most appropriate available ClaimsAdjuster based on
   claim type, value band, and workload balance.
9. System notifies the assigned adjuster via email and in-portal notification with the CRN and
   FNOL summary.
10. System sends a claim acknowledgement to the PolicyHolder confirming the CRN, adjuster contact
    details, and expected response timeline per SLA.
11. System logs the FNOL event in the claims audit trail.

### Alternative Flows

- **AF-1: Third-Party FNOL** — If the claim is filed by a third party (e.g., third party injured
  in an auto accident), the system routes the intake to the liability claims queue and creates a
  third-party claimant record linked to the at-fault policy.
- **AF-2: Catastrophe Event Triage** — If a CAT event flag is active (e.g., declared flood zone
  event), the system routes all new FNOLs in the affected territory to the CAT claims team and
  applies the expedited SLA profile.

### Exception Flows

- **EF-1: Policy Not Found** — If no active policy can be matched to the provided details, the
  system prompts the user to verify the policy number or contact the customer service team.
- **EF-2: Loss Date Outside Policy Period** — System rejects the FNOL with an explanation that the
  reported date of loss falls outside the active coverage period and displays the policy effective
  and expiry dates.
- **EF-3: Duplicate Claim Detection** — If the system detects a claim record already exists for the
  same policy, loss date, and incident description (fuzzy match), it surfaces a duplication warning.
  The adjuster must confirm whether to proceed as a new claim or merge with the existing record.

---

## UC-004: Process and Settle Claim

### Summary Table

| Field              | Details                                                                                              |
|--------------------|------------------------------------------------------------------------------------------------------|
| **Use Case ID**    | UC-004                                                                                               |
| **Name**           | Process and Settle Claim                                                                             |
| **Actor(s)**       | ClaimsAdjuster (primary), Finance (secondary), Reinsurer (external)                                  |
| **Preconditions**  | A Claim (CRN) exists in REGISTERED or UNDER_INVESTIGATION status. Adjuster is assigned.             |
| **Postconditions** | Claim is settled (CLOSED_SETTLED) or denied (CLOSED_DENIED). Payment is released or denial letter sent. |

### Main Flow

1. ClaimsAdjuster reviews the FNOL submission, initial evidence, and reserve adequacy.
2. Adjuster validates coverage: confirms the claimed loss type is within covered perils and that no
   applicable exclusion applies.
3. Adjuster requests additional evidence as needed (repair estimates, medical records via HL7 FHIR,
   police report).
4. System triggers Fraud Scoring Engine (UC-009) and returns a fraud probability score and flag
   category (Low / Medium / High).
5. If fraud score is Low, adjuster proceeds directly to valuation.
6. Adjuster quantifies the loss: repair or replacement cost, medical expenses, lost earnings, or
   agreed-value sum insured.
7. Adjuster sets the settlement quantum, net of applicable deductibles and sub-limits.
8. Adjuster submits settlement recommendation within delegated authority or escalates to supervisor.
9. Finance checks reserve adequacy and determines reinsurance treaty applicability.
10. If settlement exceeds reinsurance treaty threshold, system generates a bordereaux notification
    to the reinsurer via the Reinsurance Clearinghouse API and awaits co-settlement confirmation.
11. Finance releases payment via the Payment Gateway to the policyholder's nominated bank account.
12. System updates claim status to CLOSED_SETTLED and closes the reserve.
13. System generates and dispatches the settlement letter to the policyholder.

### Alternative Flows

- **AF-1: Repair-in-Kind Settlement** — For auto and property claims, if the insurer elects
  repair-in-kind, the system creates a repair order linked to an approved repairer network member
  and tracks repair completion before closing the claim.
- **AF-2: Partial Settlement** — For complex claims with multiple heads of loss, adjuster may
  approve partial interim payments while investigation of remaining heads continues. Each partial
  settlement is tracked against the total reserve.

### Exception Flows

- **EF-1: High Fraud Score** — If fraud score is High, claim is flagged and routed to the Special
  Investigations Unit (SIU) queue. Adjuster cannot proceed to settlement until SIU clears or
  confirms fraud. If fraud confirmed, claim is declined and insurer initiates recovery action.
- **EF-2: Reinsurer Non-Response** — If the reinsurance co-settlement confirmation is not received
  within the SLA window, Finance may release payment from net retention and log the reinsurer
  recovery as a receivable pending collection.
- **EF-3: Claimant Payment Details Invalid** — If the bank account details on file are rejected by
  the payment gateway, Finance places the payment in PENDING_BANK_DETAILS status and requests
  updated details from the policyholder via secure message.

---

## UC-005: Collect Premium Payment

### Summary Table

| Field              | Details                                                                                               |
|--------------------|-------------------------------------------------------------------------------------------------------|
| **Use Case ID**    | UC-005                                                                                                |
| **Name**           | Collect Premium Payment                                                                               |
| **Actor(s)**       | PolicyHolder (primary), Agent (secondary)                                                             |
| **Preconditions**  | Policy is in ACTIVE status. A billing schedule exists with at least one instalment due.               |
| **Postconditions** | Premium instalment is recorded as PAID in the billing ledger. Policy coverage continues uninterrupted. |

### Main Flow

1. Billing Engine identifies upcoming premium due dates and generates payment reminders 30 days and
   7 days before the due date.
2. System dispatches payment reminder notifications to the PolicyHolder via email and/or SMS
   (channel per preference on file).
3. On the due date, if Direct Debit is configured, Billing Engine initiates an automated collection
   request to the Payment Gateway.
4. Payment Gateway processes the transaction and returns a success or failure response.
5. On success, Billing Engine marks the instalment as PAID, posts the premium to the accounting
   ledger (earned vs. unearned split per IFRS 17), and issues an electronic receipt to the
   PolicyHolder.
6. System updates the Next Due Date and remains in ACTIVE status.
7. PolicyHolder may view the payment history and download receipts from the self-service portal.

### Alternative Flows

- **AF-1: Manual Portal Payment** — PolicyHolder logs into the portal and initiates a manual
  card payment. System processes the card via the Payment Gateway (PCI-DSS tokenised) and records
  the payment against the outstanding instalment.
- **AF-2: Agent-Assisted Payment** — Agent enters payment details on behalf of the policyholder
  using the agency portal, applying the payment to the correct policy and instalment record.
- **AF-3: Partial Payment** — If PolicyHolder pays less than the full instalment amount, the system
  records a partial payment, generates a shortfall notice, and reduces the outstanding balance. Full
  coverage is maintained for the grace period.

### Exception Flows

- **EF-1: NSF / Insufficient Funds** — Payment Gateway returns an NSF decline. System sends an
  NSF notification to PolicyHolder and enters the policy into the GRACE_PERIOD state (30-day
  default, configurable by product). A retry attempt is made after 3 business days.
- **EF-2: Grace Period Expiry** — If no payment is received by the end of the grace period, the
  Billing Engine triggers a policy suspension. Coverage is suspended and a lapse notice is
  dispatched. A reinstatement workflow is made available to the PolicyHolder.
- **EF-3: Payment Gateway Outage** — If the Payment Gateway is unavailable, the system queues the
  collection attempt and retries when the gateway is available. The PolicyHolder receives a
  communication confirming the delay and confirming no lapse will occur during the outage window.

---

## UC-006: Policy Renewal

### Summary Table

| Field              | Details                                                                                              |
|--------------------|------------------------------------------------------------------------------------------------------|
| **Use Case ID**    | UC-006                                                                                               |
| **Name**           | Policy Renewal                                                                                       |
| **Actor(s)**       | PolicyHolder (primary), Broker (primary)                                                             |
| **Preconditions**  | Policy is ACTIVE and within the renewal processing window (typically 60 days before expiry).        |
| **Postconditions** | A renewal policy record is created and activated, or the expiring policy is marked NON_RENEWED.     |

### Main Flow

1. Billing Engine identifies policies entering the renewal window (60 days before expiry date).
2. System triggers the Renewal Rating process: re-rates the risk using updated actuarial tables,
   current claims history (bonus/malus), and any index-linked or experience-rated adjustments.
3. System generates a renewal quote and renewal invitation letter.
4. System dispatches renewal invitation to PolicyHolder and their assigned Broker/Agent 60 days
   before expiry, followed by reminder communications at 30 days and 14 days.
5. PolicyHolder or Broker reviews the renewal terms and either accepts, modifies, or declines.
6. On acceptance, the system creates a new policy record (RENEWAL term) linked to the parent policy,
   applying any mid-term changes requested at renewal.
7. System updates the expiry date, collects the first renewal premium, and confirms renewal to the
   PolicyHolder and Broker.
8. Renewal policy documents are generated and dispatched.

### Alternative Flows

- **AF-1: Renewal with Changes** — If the actor requests coverage changes at renewal (adding a
  vehicle, increasing sum insured), the system re-rates the modified risk before generating the
  renewal quote.
- **AF-2: Auto-Renewal** — If the policy has an auto-renewal mandate and no changes are required,
  the system automatically binds the renewal 21 days before expiry if the Direct Debit first
  payment clears, without requiring explicit actor confirmation.

### Exception Flows

- **EF-1: Risk Declination at Renewal** — If re-underwriting reveals the risk is no longer within
  appetite (e.g., significant claims history, lapsed certifications), an Underwriter review is
  triggered. The Underwriter may issue a renewal with additional loadings or decline to renew.
- **EF-2: No Response by Expiry** — If neither acceptance nor declination is received by the
  expiry date, the system marks the policy as LAPSED and sends a final non-renewal notice. A
  30-day run-off period applies for any notified claims under the expiring policy.
- **EF-3: Renewal Premium Collection Failure** — If the first renewal premium cannot be collected
  on the renewal effective date, the renewal is held in RENEWAL_PENDING_PAYMENT status and the
  expiring policy is extended for 7 days pending resolution.

---

## UC-007: Fraud Detection Scoring

### Summary Table

| Field              | Details                                                                                              |
|--------------------|------------------------------------------------------------------------------------------------------|
| **Use Case ID**    | UC-007                                                                                               |
| **Name**           | Fraud Detection Scoring                                                                             |
| **Actor(s)**       | ClaimsAdjuster (primary), Fraud Detection Service (external system)                                  |
| **Preconditions**  | A claim (CRN) exists in REGISTERED or UNDER_INVESTIGATION status.                                   |
| **Postconditions** | A fraud score, risk band (Low/Medium/High), and flag rationale are attached to the claim record.    |

### Main Flow

1. System automatically invokes the Fraud Scoring Engine when a claim transitions to
   UNDER_INVESTIGATION status (triggered by UC-003 FNOL completion or UC-004 investigation start).
2. System compiles the fraud scoring payload: claim details, insured profile, policy tenure, prior
   claims history, FNOL submission metadata (time-of-day, device fingerprint, IP geolocation),
   reported loss description (NLP features), and third-party claimant data.
3. System submits the payload to the external Fraud Detection Service via REST API (TLS 1.3,
   OAuth 2.0 client credentials).
4. Fraud Detection Service applies an ensemble ML model (gradient boosting + network graph analysis
   for linked-party fraud rings) and returns a fraud probability score (0.00–1.00), a risk band
   (Low / Medium / High), and a list of triggered fraud indicators with weighting.
5. System persists the fraud score result on the claim record and surfaces it in the ClaimsAdjuster
   workbench with a human-readable explanation of triggered indicators.
6. If risk band is Low, the adjuster is notified and the claim proceeds normally.
7. If risk band is Medium, the adjuster must document a manual review decision before proceeding.
8. If risk band is High, the claim is automatically routed to the SIU queue and adjuster access
   to approve settlement is blocked pending SIU clearance.

### Alternative Flows

- **AF-1: Manual Re-Score** — ClaimsAdjuster may trigger a manual re-score after submitting new
  evidence (e.g., updated repair estimate, police report). System resubmits the payload with the
  new evidence metadata and updates the claim record with the revised score.
- **AF-2: SIU Clearance** — After SIU investigation, if the SIU officer marks the claim as
  FRAUD_NOT_CONFIRMED, the fraud flag is lifted, the claim returns to the normal adjudication
  workflow, and a SIU clearance note is appended to the audit trail.

### Exception Flows

- **EF-1: Fraud API Unavailable** — If the Fraud Detection Service is unavailable after three
  retries, the system assigns a default Medium score, adds a FRAUD_SCORE_UNAVAILABLE flag to the
  claim, and requires the adjuster to perform a manual fraud checklist before proceeding.
- **EF-2: Score Confidence Below Threshold** — If the fraud model returns a score with a confidence
  interval wider than the configured threshold (model uncertainty flag), the system treats the
  result as Medium and requires manual review regardless of the numeric score.

---

## UC-008: Generate Regulatory Report

### Summary Table

| Field              | Details                                                                                              |
|--------------------|------------------------------------------------------------------------------------------------------|
| **Use Case ID**    | UC-008                                                                                               |
| **Name**           | Generate Regulatory Report                                                                           |
| **Actor(s)**       | Actuary (primary), Admin (secondary), RegulatorAPI (external system)                                 |
| **Preconditions**  | Reporting period is closed. Actuarial data (reserves, CSM, RA) has been finalised and signed off.  |
| **Postconditions** | Report is generated, validated, submitted to the RegulatorAPI, and a submission receipt is recorded. |

### Main Flow

1. Actuary or Admin initiates report generation from the Regulatory Reporting module, selecting the
   report type (IFRS 17 Disclosure, Solvency II QRT, Domestic Premium Bordereau) and reporting
   period.
2. System retrieves the finalised actuarial inputs: insurance contract liability measurements (BEL,
   RA, CSM under IFRS 17), claims development triangles, earned/unearned premium split, loss ratios
   by product line, and reinsurance recoverables.
3. System applies the applicable regulatory schema (XBRL taxonomy for Solvency II, IFRS disclosure
   templates, jurisdiction-specific XML schemas).
4. System generates the report artefact and runs automated validation rules (completeness checks,
   cross-report consistency tests, prior-period variance thresholds).
5. Validation results are presented to the Actuary for review. Any validation exceptions must be
   acknowledged and annotated before submission is permitted.
6. Actuary approves the report for submission.
7. System submits the report to the RegulatorAPI endpoint via authenticated HTTPS.
8. System receives and records the submission acknowledgement (timestamp, submission reference
   number, regulator status code).
9. System updates the report record to SUBMITTED status and notifies the Actuary and Admin.

### Alternative Flows

- **AF-1: Scheduled Automated Submission** — For jurisdictions requiring automated monthly/quarterly
  bordereau submissions, the system executes steps 1–8 automatically at the configured schedule
  without requiring manual Actuary initiation, pending prior-period data finalisation.
- **AF-2: Amended Resubmission** — If the regulator returns a rejection or requests amendment, the
  Actuary may correct the underlying data and initiate a resubmission, which creates a new version
  of the report linked to the original submission record.

### Exception Flows

- **EF-1: Regulatory API Rejection** — If the RegulatorAPI returns a validation error (e.g.,
  taxonomy mismatch, missing mandatory field), the system logs the error code and description,
  updates the report status to SUBMISSION_FAILED, and notifies the Actuary with the error detail.
- **EF-2: Data Finalisation Not Complete** — If the period-end actuarial data has not been signed
  off, the system blocks report generation and displays the list of outstanding data sign-off items.
- **EF-3: Submission Deadline Breach** — If the submission is initiated within 48 hours of the
  regulatory filing deadline, the system sends a breach-risk alert to the Actuary and Compliance
  Officer, escalating to the Chief Risk Officer if within 24 hours.

---

*Document Version: 1.0 | Last Updated: 2025 | Owner: Business Analysis | Status: Baselined*
