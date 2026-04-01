# Insurance Management System — User Stories

**Project:** P&C Insurance SaaS Platform
**Version:** 1.0
**Personas:** Policyholder · Broker · Underwriter · Claims Adjuster · Actuary

---

## Policyholder Stories

---

**US-001 — Online Policy Application**
As a policyholder, I want to submit a policy application through a web portal so that I can obtain coverage without visiting an agent's office.

Acceptance Criteria:
- The application form captures all required fields for the selected line of business (personal auto, homeowners, etc.) and validates required fields before submission
- The applicant receives an application reference number and email confirmation within 60 seconds of submission
- Partially completed applications are saved as drafts and retrievable for up to 30 days
- The portal displays estimated premium before final submission based on entered data
- Submission triggers an underwriting evaluation and communicates an estimated decision timeline

---

**US-002 — Viewing Policy Documents**
As a policyholder, I want to access my declarations page, endorsements, and ID cards from my online account so that I can retrieve proof of insurance without contacting my broker.

Acceptance Criteria:
- All current and historical policy documents are accessible in the policyholder portal within 24 hours of issuance
- Each document is available for download as a PDF
- The portal displays policy effective date, expiration date, coverage summary, and insured details on the policy overview screen
- Documents can be shared via a secure, time-limited link valid for 48 hours
- Insurance ID cards for auto policies are downloadable and printable in wallet-card format

---

**US-003 — Premium Payment**
As a policyholder, I want to pay my insurance premium online using a credit card or bank account so that I can manage my payments conveniently and avoid coverage lapses.

Acceptance Criteria:
- The payment portal accepts Visa, Mastercard, American Express, and ACH bank transfers
- Saved payment methods are tokenized and displayed masked; full card numbers are never stored
- The policyholder receives a payment confirmation email within 5 minutes of a successful transaction
- The portal displays current balance, next payment due date, and payment history for the last 12 months
- AutoPay enrollment is available with configurable payment date selection within the billing cycle

---

**US-004 — Filing a Claim (FNOL)**
As a policyholder, I want to report a new claim online as soon as a loss occurs so that the claims process can begin without delay.

Acceptance Criteria:
- FNOL intake accepts date/time of loss, loss description, loss location, contact preference, and optional photo/document uploads
- The system confirms coverage is active at the date of loss and displays applicable deductibles before submission is finalized
- A unique claim number is assigned and communicated to the policyholder within 60 seconds of FNOL submission
- The assigned adjuster's name and contact information are communicated to the policyholder within one business day
- The policyholder can track claim status — open, under investigation, pending payment, closed — through the portal

---

**US-005 — Requesting a Policy Endorsement**
As a policyholder, I want to request a mid-term change to my policy online so that I can update my coverage without waiting for my policy's renewal date.

Acceptance Criteria:
- Common endorsement types (vehicle add/remove, address change, coverage limit adjustment, additional insured) are available via self-service in the portal
- The portal displays the premium impact of the endorsement before the policyholder confirms the change
- Endorsements within carrier-defined self-service thresholds are processed immediately; those requiring underwriter review are queued and the policyholder is notified of the timeline
- A revised declarations page reflecting the endorsement is available in the portal within one business day of processing
- The policyholder receives an email confirmation with the effective date and premium adjustment summary

---

**US-006 — Policy Renewal**
As a policyholder, I want to receive timely renewal notices and easily confirm or update my coverage so that my protection does not lapse at expiration.

Acceptance Criteria:
- The policyholder receives renewal notices by email at 90, 60, and 30 days before expiration
- The renewal offer clearly states the new premium, any rate changes, and changes to coverage terms
- The policyholder can accept the renewal offer with one click from the portal or email notification
- If the policyholder wants to make changes, they can initiate an endorsement request directly from the renewal confirmation screen
- The system confirms renewed coverage and issues a new declarations page upon renewal completion

---

**US-007 — Cancellation Request**
As a policyholder, I want to request cancellation of my policy and understand my refund amount so that I can make an informed decision when switching carriers.

Acceptance Criteria:
- The portal provides a cancellation request form capturing the requested cancellation date and reason
- The system calculates and displays the unearned premium refund using the applicable method (pro-rata or short-rate) before the policyholder confirms the request
- A cancellation confirmation and refund timeline are provided upon submission
- Refunds are issued within the timeframe required by the policy's state of domicile
- The policyholder receives a notice of cancellation document as confirmation

---

**US-008 — Claim Status Tracking**
As a policyholder, I want to check the status of my open claim online at any time so that I am not dependent on phone calls to stay informed.

Acceptance Criteria:
- The claims portal displays current claim status, adjuster contact, last activity date, and pending action items
- Reserve amounts are not displayed to the policyholder; only status milestones are shown
- The policyholder can upload additional supporting documents directly to the claim record
- The portal notifies the policyholder via email or SMS when claim status changes
- Payment information — amount, method, and expected delivery date — is visible once a payment has been issued

---

## Broker Stories

---

**US-009 — New Business Submission**
As a broker, I want to submit a new insurance application on behalf of a client and receive an immediate bindable quote so that I can close new business quickly.

Acceptance Criteria:
- The broker portal pre-fills agency and producer information from the logged-in user profile
- The submission form dynamically adjusts required fields based on selected line of business and state
- STP-eligible submissions return a bindable quote within 30 seconds; non-STP submissions display an estimated referral turnaround time
- The quote displays premium breakdown by coverage part, applicable surcharges and credits, and payment plan options
- The broker can save the quote for up to 14 days and return to bind without re-entering application data

---

**US-010 — Binding Coverage**
As a broker, I want to bind coverage for an approved quote within my binding authority so that I can confirm protection for my client without waiting for carrier approval.

Acceptance Criteria:
- The system validates the broker's binding authority limits for the line of business, state, and premium amount before permitting binding
- Binding generates a binder document immediately with confirmation number, effective date, and coverage summary
- A policy number is assigned and the declarations page is available within one business day
- Risks that exceed binding authority are automatically submitted for underwriter approval with the existing quote data pre-populated in the referral
- The broker receives email confirmation of successful binding with document links

---

**US-011 — Issuing a Certificate of Insurance**
As a broker, I want to generate and issue a Certificate of Insurance for a client so that my client can satisfy a third-party's proof-of-insurance requirement without waiting for carrier processing.

Acceptance Criteria:
- The broker can issue ACORD 25 and ACORD 28 certificates for active policies within binding authority
- The broker can add certificate holders and additional insured endorsements during COI generation within carrier-configured rules
- The COI is generated as a PDF and delivered by email to specified recipients within 60 seconds
- The carrier receives a copy of every COI issued and can audit or revoke non-conforming certificates
- The system prevents COI issuance for policies with lapsed or cancelled status

---

**US-012 — Viewing Commission Statements**
As a broker, I want to view and download my commission statements so that I can reconcile my agency income and verify accuracy.

Acceptance Criteria:
- Commission statements are available monthly within 5 business days of billing cycle close
- Statements itemize commission earned by policy, transaction type (new business, renewal, endorsement), and any chargebacks for cancellations
- Statements are downloadable in PDF and CSV formats
- Year-to-date commission totals are displayed on the broker dashboard
- Disputed commission items can be flagged for carrier review from within the portal

---

**US-013 — Managing Expiring Policies**
As a broker, I want to see a list of my clients' expiring policies with renewal status so that I can proactively contact clients and prevent unwanted lapses.

Acceptance Criteria:
- The broker dashboard provides a filterable expiring policies report for 30, 60, and 90-day windows
- Each entry shows policy number, insured name, line of business, expiring premium, renewal offer status, and open claims
- The broker can initiate a renewal from the expiring policies list with one click
- Policies with material risk changes flagged by the system are highlighted for broker review
- Export to CSV is available for use in agency management system imports

---

**US-014 — Tracking Claim Status for a Client**
As a broker, I want to monitor the status of open claims for all my clients so that I can proactively manage client relationships during the claims process.

Acceptance Criteria:
- The broker portal shows all open claims for the broker's book of business with status, assigned adjuster, and last update
- The broker can view claim details, documents, and payment history for each claim
- The broker cannot modify claim records but can submit supplemental information or contact the adjuster through the portal
- Claim status change notifications are sent to the broker's configured email address
- Closed claims remain accessible in the broker's claim history view for 5 years

---

## Underwriter Stories

---

**US-015 — Reviewing a Referred Submission**
As an underwriter, I want to review all relevant risk data for a referred submission in a single screen so that I can make an informed decision without switching between multiple systems.

Acceptance Criteria:
- The referral screen displays application data, external data pull results (CLUE, MVR, credit score), prior policy history, loss history, and the automated risk score with factor breakdown
- External data pull status (retrieved, failed, cached) is visible with pull date and source
- The underwriter can approve, decline, or modify the quote terms from the referral screen with required reason code entry
- All underwriter actions — view, approve, decline, modify — are recorded in the audit trail with timestamp and user identity
- The referral queue supports priority sorting by premium size, expiration proximity, and submission age

---

**US-016 — Configuring Underwriting Rules**
As an underwriter, I want to update acceptance criteria and rate modification rules without a software release so that I can respond quickly to loss experience or market changes.

Acceptance Criteria:
- The rules engine UI allows addition, modification, and deactivation of rules without code changes
- Rule changes require a future effective date and cannot be applied retroactively to bound policies
- A simulated impact analysis shows how the rule change would affect the last 90 days of submissions before activation
- Changes require dual approval (maker/checker) before becoming active
- All rule changes are version-controlled with change history and rollback capability

---

**US-017 — Overriding an Automatic Declination**
As a senior underwriter, I want to override an automatic declination and bind coverage for a risk that I believe is acceptable so that we do not lose business on eligible risks the system incorrectly scores.

Acceptance Criteria:
- Override is only available to users with senior underwriter or above role assignment
- The override form requires selection of a reason code and entry of a free-text justification
- Supporting documents can be attached to the override record
- The override and its justification become a permanent part of the policy's underwriting record
- Overrides are reportable in an override audit report available to compliance and management

---

**US-018 — Monitoring Underwriting Performance**
As an underwriting manager, I want to view real-time underwriting metrics so that I can identify workflow bottlenecks and production trends.

Acceptance Criteria:
- The dashboard displays hit ratio, STP rate, referral queue depth, average referral age, and declination reason breakdown
- Metrics are filterable by line of business, state, producer, and date range
- Written premium, policy count, and average premium trends are displayed with prior-period comparison
- Referrals older than a configurable threshold (default: 48 hours) are highlighted as aged
- The dashboard is exportable as a PDF or CSV management report

---

**US-019 — Setting Appetite Restrictions by Territory**
As an underwriter, I want to restrict new business in high-risk territories so that we can control accumulation in catastrophe-exposed zones.

Acceptance Criteria:
- Territory restrictions can be set at ZIP code, county, or state level per line of business
- Restrictions can be configured as hard stop (automatic declination) or soft stop (referral required)
- The effective date of restrictions is configurable and restrictions cannot be backdated
- Brokers submitting from restricted territories receive a clear, configurable declination or referral message
- Accumulation exposure in restricted territories is reportable against defined capacity limits

---

**US-020 — Reviewing Reinsurance Threshold Flags**
As an underwriter, I want to be notified when a submission exceeds facultative reinsurance thresholds so that I can initiate placement before binding.

Acceptance Criteria:
- The system flags submissions automatically when total insured value or coverage limit exceeds configured facultative thresholds
- The flag generates a facultative placement referral with the risk schedule, quote terms, and limit excess amount pre-populated
- The policy cannot be bound until the facultative referral is either placed or explicitly waived by an authorized underwriter
- Waiver requires documented justification and creates an audit record
- Placed facultative certificates are attached to the policy record and visible in the reinsurance module

---

## Claims Adjuster Stories

---

**US-021 — Processing a New FNOL**
As a claims adjuster, I want to receive a new claim assignment with complete FNOL data and verified coverage information so that I can begin investigation without duplicating data entry.

Acceptance Criteria:
- The new claim record displays FNOL data, coverage verification results, deductible, limits, and any fraud indicator flags
- The adjuster can contact the policyholder directly from the claim record using click-to-call or email templates
- Required initial actions — acknowledgment letter, reserve setting, inspection scheduling — are listed as task checklist items
- The adjuster can escalate the claim to SIU, legal, or large-loss unit from the claim screen with a single action
- Assignment notifications are delivered to the adjuster via email and in-platform notification within 15 minutes of routing

---

**US-022 — Setting and Updating Reserves**
As a claims adjuster, I want to set initial reserves and update them as claim facts develop so that the company's financial statements accurately reflect the expected cost of open claims.

Acceptance Criteria:
- Reserves can be set for indemnity, allocated loss adjustment expense (ALAE), and unallocated expense separately per coverage part
- Reserve increases within the adjuster's authority level are applied immediately; increases above authority require supervisor approval
- Every reserve change records the prior reserve, new reserve, change amount, effective date, reason code, and user
- The system calculates a reserve-to-payment ratio and flags claims where reserves appear potentially inadequate based on payment activity
- Reserve history is fully visible in an audit timeline on the claim record

---

**US-023 — Managing Investigation Tasks**
As a claims adjuster, I want to track all investigation tasks — inspections, statements, reports — in a structured checklist so that nothing falls through the cracks on complex claims.

Acceptance Criteria:
- Investigation tasks can be created, assigned, prioritized, and marked complete within the claim record
- Task types include: field inspection, recorded statement, independent appraisal, IME referral, police report request, and subrogation demand
- External vendor assignments (appraisers, IME companies) generate assignment letters from templates and track completion status
- Overdue tasks trigger configurable alerts to the adjuster and supervisor
- Completed tasks are time-stamped and locked against modification

---

**US-024 — Processing a Claim Payment**
As a claims adjuster, I want to issue a settlement payment to a claimant directly from the claim record so that payment is processed quickly and documentation is complete.

Acceptance Criteria:
- Payments can be issued by check, ACH, or virtual card from within the claim payment screen
- The system validates payee information against OFAC SDN list before releasing payment
- Duplicate payment checks prevent re-issuance of amounts already paid on the same coverage part
- Payments above the adjuster's authority threshold require supervisor countersignature
- A payment confirmation — amount, method, expected delivery date — is automatically sent to the payee and stored in the claim record

---

**US-025 — Identifying Subrogation Opportunities**
As a claims adjuster, I want to flag a claim for subrogation when a third party's negligence caused the loss so that the company can pursue recovery and reduce net claim cost.

Acceptance Criteria:
- The FNOL and claim investigation screens include a subrogation indicator with prompt to document the liable third party
- Flagging a claim for subrogation generates a subrogation task and optionally assigns it to a dedicated recovery unit
- The system tracks demand letter issuance date, response received date, negotiation status, and recovery amounts received
- Recovery amounts are automatically applied to reduce net incurred loss on the claim record
- Subrogation recovery reports are available by line of business, recovery stage, and recovery unit

---

**US-026 — Handling a Fraudulent Claim**
As a claims adjuster, I want to refer a claim to the Special Investigations Unit when fraud indicators are present so that the company can protect against illegitimate losses.

Acceptance Criteria:
- The system automatically highlights fraud indicator flags detected at FNOL and during investigation
- The adjuster can add manual fraud indicators with supporting documentation from the claim record
- SIU referral is a single-action workflow that notifies the assigned SIU investigator and logs the referral
- Claims in SIU review cannot be paid or closed without SIU clearance
- SIU outcome — cleared, confirmed fraud, referred to law enforcement — is recorded on the claim and triggers workflow actions

---

## Actuary Stories

---

**US-027 — Exporting Loss Data for Reserving Analysis**
As an actuary, I want to export granular claim and premium data by accident year and development period so that I can perform loss triangle analysis in my actuarial modeling tools.

Acceptance Criteria:
- The data export produces claim records with accident date, report date, paid losses, case reserves, ALAE, and earned exposure by policy year
- Exports are available in CSV and Parquet formats with configurable field selection
- The export can be filtered by line of business, state, claim type, and date range
- Data is exported with a reconciliation control total matching the system's ledger to verify completeness
- Exports of data older than the current accident year are available within 24 hours of request via asynchronous job

---

**US-028 — Analyzing Loss Ratios by Segment**
As an actuary, I want to view earned premium, incurred losses, and loss ratios segmented by territory, class, and underwriting year so that I can identify profitable and unprofitable segments for rate action.

Acceptance Criteria:
- The analytics dashboard displays earned premium, paid loss, case reserve, IBNR (imported), and loss ratio by configurable segment dimensions
- Segments are available at territory (state, county, ZIP), class code, construction type, policy year, and accident year levels
- Loss ratio trends are displayed as 3-year and 5-year rolling averages with current period highlighted
- Breakeven loss ratio (calculated from loaded expense ratio) is shown as a target reference line
- The analysis is exportable as an Excel workbook with raw data and pivot-ready formatting

---

**US-029 — Reviewing Reinsurance Recoverable Aging**
As an actuary, I want to review the aging of reinsurance recoverables by treaty and reinsurer so that I can assess collectability and flag impaired reinsurers for additional reserve consideration.

Acceptance Criteria:
- The reinsurance recoverable report categorizes outstanding amounts by reinsurer, treaty, and aging bucket (0–30, 31–90, 91–180, 181+ days)
- Reinsurers with credit ratings below investment grade or on negative watch are flagged automatically based on AM Best rating feed
- The actuary can mark specific recoverables as potentially uncollectible and document the rationale
- Uncollectible markings flow into a recoverable impairment reserve report for statutory reporting
- The report is producible as of any historical quarter-end date for prior-period comparison

---

**US-030 — Catastrophe Accumulation Review**
As an actuary, I want to view total insured value (TIV) and policy count aggregated by geographic zone and peril so that I can assess catastrophe exposure against modeled probable maximum loss (PML) estimates.

Acceptance Criteria:
- The accumulation report aggregates TIV by ZIP code, county, coastal zone, and earthquake fault zone
- Policy counts and average TIV by zone are displayed alongside imported PML estimates for comparison
- The report can be exported in RMS, AIR, or vendor-neutral CSV formats for input to catastrophe models
- Accumulations update in near-real-time as policies are bound and endorsed
- Treaty attachment point and limit are displayed alongside accumulation data to show proximity to reinsurance protection layers

---

**US-031 — Producing Rate Level Indication**
As an actuary, I want to calculate an indicated rate change by line and state using the platform's loss and premium data so that I can support rate filing submissions with defensible indications.

Acceptance Criteria:
- The rate indication module ingests earned premium (at current rate level), ultimate losses, trend factors (user-input), and expense loadings to calculate indicated change
- On-level factor calculation is supported using parallelogram method applied to historical premium data
- Indication results are produced by state and line with a fully documented data exhibit traceable to source records
- The output is formatted as a rate filing support exhibit suitable for SERFF submission
- Sensitivity analysis can be run by varying trend, loss development, and credibility weighting assumptions

---

**US-032 — Reviewing Statistical Reporting Submissions**
As an actuary, I want to review and validate statistical unit data before submission to ISO or NCCI so that bureau submissions are accurate and avoid costly correction cycles.

Acceptance Criteria:
- The statistical reporting module produces a pre-submission validation report identifying edit failures by rule code and record count
- The actuary can drill into failing records to identify the source policy or claim and the specific field error
- Corrected records can be reprocessed and re-validated before final submission
- Submission confirmation numbers and bureau acknowledgment files are stored in the platform
- Historical submission files are archived and retrievable for bureau re-submission or audit purposes

---

## Cross-Persona Stories

---

**US-033 — Endorsement Triggering Reinsurance Cession Update**
As an underwriter, I want endorsements that increase insured values above reinsurance thresholds to automatically update cession calculations so that reinsurance coverage remains accurate mid-term.

Acceptance Criteria:
- Any endorsement changing total insured value, coverage limit, or coverage type triggers a recalculation of applicable cession amounts
- Updated cession data is reflected in the bordereaux and reinsurance ledger as of the endorsement effective date
- If an endorsement creates a new facultative placement need, an automatic referral is generated
- The underwriter is notified of the reinsurance implication before confirming the endorsement
- Net and ceded premium adjustments from the endorsement are posted to the reinsurance accounting records

---

**US-034 — Regulatory Filing Triggered by Rate Change**
As a compliance officer, I want rate changes to automatically generate the required state filing so that rate increases are not applied before regulatory approval is obtained in prior-approval states.

Acceptance Criteria:
- Rate table updates include a jurisdiction-aware workflow step that identifies prior-approval vs. file-and-use states
- For prior-approval states, the new rate table is placed in pending status and cannot be applied to new quotes until filing approval is received
- The system generates a SERFF filing package with the required actuarial memorandum template, rate exhibits, and form revisions pre-populated from platform data
- SERFF approval confirmation received via API automatically activates the rate table in the platform
- For file-and-use states, the rate is activated on the effective date with concurrent SERFF notification filing

---

**US-035 — Broker Receiving Claim Update Notification**
As a broker, I want to receive automatic notifications when a claim status changes on a policy in my book so that I can keep my client informed and manage expectations proactively.

Acceptance Criteria:
- Notifications are triggered for: claim assignment, reserve increase exceeding a configurable threshold, SIU referral, payment issued, and claim closure
- Notification content includes claim number, policy number, insured name, status change, and adjuster contact
- Brokers can configure notification preferences — email, SMS, or in-portal only — and opt out of non-mandatory notifications
- Notifications do not expose reserve amounts or privileged claims handling information
- Notification delivery status is logged and undelivered notifications trigger a retry within one hour

---

**US-036 — Policyholder Receiving Cancellation Warning**
As a policyholder, I want to receive advance warning before my policy is cancelled for non-payment so that I have enough time to make a payment and avoid a coverage lapse.

Acceptance Criteria:
- The first notice of cancellation is sent at the number of days prior to the cancellation effective date required by the state of domicile
- The notice clearly states the outstanding balance, cancellation date, and payment options including a direct payment link
- A reminder notice is sent 48 hours before the cancellation effective date if payment has not been received
- Payment made before the cancellation effective date automatically cancels the pending cancellation and sends a confirmation
- If cancellation proceeds, the policyholder receives a notice of cancellation with the final cancellation date and any applicable refund amount
