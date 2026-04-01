# Use Case Descriptions — Rental Management System

## Overview

This document provides detailed use case specifications for key flows in the Rental Management System. Each use case is described using a structured template covering actors, preconditions, postconditions, main success scenario, alternative flows, and exception flows.

---

## UC-02: Create Booking Request

### Use Case Specification

| Field | Value |
|---|---|
| **Use Case ID** | UC-02 |
| **Name** | Create Booking Request |
| **Version** | 1.0 |
| **Priority** | Critical |
| **Status** | Active |

### Actors

| Role | Actor | Type |
|---|---|---|
| Primary | Customer | Human |
| Secondary | System | Automated |
| Secondary | Payment Gateway (Stripe/PayPal) | External System |
| Secondary | Insurance Partner API | External System |

### Preconditions

1. Customer is authenticated with a verified session token.
2. Customer identity has been verified (UC-17 completed with VERIFIED status).
3. Customer has a valid, non-expired payment method on file (tokenized card).
4. The selected asset exists in the catalog with AVAILABLE status for the requested date range.
5. The requested start date is at least the system-configured minimum lead time from now (default: 2 hours).
6. No existing active or confirmed booking overlaps with the requested date range for the same asset.

### Postconditions

**Success:**
1. A Booking record is created with status `PENDING_CONFIRMATION`.
2. Deposit amount is pre-authorized against the customer's payment method (not captured).
3. The asset's availability calendar is updated to reflect the reservation hold.
4. A booking reference number (format: `RMS-YYYYMMDD-XXXXXX`) is generated and returned.
5. A confirmation email containing booking details and rental contract draft is dispatched.
6. An SMS confirmation is sent to the customer's registered mobile number.
7. An audit log entry records the booking creation event.

**Failure:**
1. No booking record is persisted if any critical step fails.
2. Any initiated payment pre-auth is voided if booking creation fails after pre-auth.

---

### Main Success Scenario

| Step | Actor | Action |
|---|---|---|
| 1 | Customer | Selects asset from search results (UC-01) and clicks "Book Now". |
| 2 | System | Displays booking form pre-filled with selected asset, dates, and base price. |
| 3 | Customer | Confirms rental dates (start datetime, end datetime) and pickup location. |
| 4 | System | Re-validates asset availability for the confirmed date range in real-time. |
| 5 | System | Calculates rental pricing: base rate × duration + applicable surcharges using active pricing rules (UC-18). |
| 6 | Customer | Reviews itemized pricing breakdown and selects optional add-ons (insurance plan, GPS, child seat, additional driver). |
| 7 | System | Recalculates total including add-on costs and applicable taxes. Displays deposit amount required. |
| 8 | Customer | Reviews total, accepts the rental terms and conditions, and confirms payment method. |
| 9 | Customer | Submits booking request. |
| 10 | System | Validates all booking parameters (date range, lead time, customer eligibility). |
| 11 | System | Calls Payment Gateway to pre-authorize the deposit amount against the customer's payment method. |
| 12 | Payment Gateway | Returns pre-authorization code and transaction ID. |
| 13 | System | Persists Booking record with status `PENDING_CONFIRMATION`, stores pre-auth transaction ID. |
| 14 | System | Publishes `booking.created` event to the event bus. |
| 15 | System | Generates booking reference number and draft rental contract PDF. |
| 16 | System | Dispatches confirmation email (with contract PDF) and SMS to customer. |
| 17 | System | Returns booking confirmation page with reference number and next steps to customer. |

---

### Alternative Flows

**AF-01: Asset Becomes Unavailable During Booking (Step 4)**
- 4a. System detects asset is no longer available (concurrent booking by another user).
- 4b. System displays "Asset no longer available" message with alternative suggestions.
- 4c. Customer selects an alternative asset and the flow resumes from Step 3, or abandons the booking.

**AF-02: Customer Adds Insurance (Step 6)**
- 6a. Customer selects an insurance plan from the displayed options.
- 6b. System calls Insurance Partner API to retrieve current plan details and pricing.
- 6c. Insurance plan is added as a line item to the booking.
- 6d. Flow resumes at Step 7.

**AF-03: Customer Has No Saved Payment Method (Step 8)**
- 8a. Customer selects "Add new payment method".
- 8b. System presents payment tokenization UI (hosted by Payment Gateway).
- 8c. Customer enters card details; Payment Gateway returns a payment token.
- 8d. Token is saved to customer profile.
- 8e. Flow resumes at Step 9.

**AF-04: Operator Requires Manual Review (Step 13)**
- 13a. Booking is flagged by a risk rule (e.g., high-value asset, new customer, foreign license).
- 13b. Booking is created with status `PENDING_REVIEW` instead of `PENDING_CONFIRMATION`.
- 13c. Operator is notified to review the booking.
- 13d. Customer is informed that the booking is under review with an estimated response time.

---

### Exception Flows

**EF-01: Payment Pre-Authorization Fails (Step 11–12)**
- 11a. Payment Gateway returns a decline code (insufficient funds, expired card, fraud flag).
- 11b. System logs the failed pre-auth attempt.
- 11c. System displays a specific error message (e.g., "Card declined — please use a different payment method").
- 11d. Booking record is not created. Customer may retry with a different payment method.

**EF-02: Payment Gateway Timeout (Step 11)**
- 11a. Payment Gateway does not respond within the configured timeout (10 seconds).
- 11b. System places booking in `PAYMENT_PENDING` state.
- 11c. Background job polls for pre-auth status for up to 5 minutes.
- 11d. If resolved: booking proceeds normally. If not resolved after 5 minutes: booking is cancelled and customer is notified.

**EF-03: Pricing Calculation Error (Step 5)**
- 5a. Pricing engine returns an error (missing rate card for asset category/date).
- 5b. System logs the error and alerts the Operator.
- 5c. Customer is shown a "Pricing unavailable" message and directed to contact support.
- 5d. Booking is not created.

---

## UC-06: Checkout Asset

### Use Case Specification

| Field | Value |
|---|---|
| **Use Case ID** | UC-06 |
| **Name** | Checkout Asset |
| **Version** | 1.0 |
| **Priority** | Critical |
| **Status** | Active |

### Actors

| Role | Actor | Type |
|---|---|---|
| Primary | Staff | Human |
| Secondary | Customer | Human |
| Secondary | System | Automated |
| Secondary | ID Verification Service | External System |

### Preconditions

1. Booking is in `CONFIRMED` state.
2. Current time is within the permitted checkout window (e.g., within 2 hours of booking start time).
3. Customer is physically present at the pickup location.
4. Asset is physically available and in `AVAILABLE` status.
5. Deposit pre-authorization is active and not expired.
6. Staff member is authenticated and has the `checkout` permission.

### Postconditions

1. Booking status transitions to `ACTIVE`.
2. Asset status transitions to `RENTED`.
3. Pre-rental condition record created, with photos and measurements, linked to booking.
4. Checkout timestamp recorded.
5. Signed rental agreement linked to booking (digital signature or physical scan stored in document storage).
6. Customer's rental dashboard updated to show active rental.

---

### Main Success Scenario

| Step | Actor | Action |
|---|---|---|
| 1 | Staff | Opens checkout workflow, scans or enters booking reference. |
| 2 | System | Retrieves and displays booking details: customer info, asset, dates, add-ons, deposit status. |
| 3 | Staff | Checks in the customer and requests identity documents (passport/driving license). |
| 4 | Staff | Scans ID documents using the ID Verification Service integration. |
| 5 | ID Verification Service | Returns verification result (VERIFIED / REVIEW_REQUIRED). |
| 6 | System | Confirms identity verification passes. |
| 7 | Staff | Physically inspects asset and captures condition photos (minimum 4 angles). |
| 8 | Staff | Records pre-rental odometer reading, fuel level, and any pre-existing damage notes. |
| 9 | System | Creates pre-rental condition record linked to booking. |
| 10 | Staff | Reviews rental agreement with customer. Customer signs digitally on tablet or staff uploads scanned copy. |
| 11 | System | Stores signed agreement in document storage and links to booking. |
| 12 | Staff | Confirms checkout completion in the system. |
| 13 | System | Transitions booking to `ACTIVE`, asset to `RENTED`. Records checkout timestamp. |
| 14 | System | Sends "Your rental has started" notification to customer with return instructions. |
| 15 | Staff | Hands over asset keys/access to customer. |

---

### Alternative Flows

**AF-01: ID Verification Returns REVIEW_REQUIRED (Step 5)**
- 5a. ID Verification Service flags the document for manual review (blurry scan, unrecognized format).
- 5b. Staff performs manual visual verification of the physical document.
- 5c. Staff records manual verification override with justification notes.
- 5d. Flow resumes at Step 7.

**AF-02: Pre-Auth Expired (Step 2)**
- 2a. System detects deposit pre-auth has expired (> 7 days for most card networks).
- 2b. System prompts re-authorization of deposit.
- 2c. Staff informs customer; customer approves new pre-auth.
- 2d. System calls Payment Gateway for fresh pre-auth.
- 2e. Flow resumes at Step 3.

**AF-03: Customer Requests Add-On at Checkout (Step 3)**
- 3a. Customer requests an add-on not included in original booking (e.g., GPS device).
- 3b. Staff adds the add-on in the system; pricing is recalculated.
- 3c. Additional pre-auth amount is processed if deposit needs to increase.
- 3d. Booking is updated and flow resumes at Step 4.

---

### Exception Flows

**EF-01: Customer Fails Identity Verification (Step 5)**
- 5a. ID Verification Service returns FAILED (document fraudulent, identity mismatch).
- 5b. System flags the booking for Operator review.
- 5c. Checkout is blocked. Customer is informed politely.
- 5d. Booking status set to `IDENTITY_FAILED`. Operator decides on cancellation or manual exception.

**EF-02: Asset Not in Expected Condition (Step 7)**
- 7a. Staff discovers significant undocumented damage on the asset prior to checkout.
- 7b. Staff records damage and sets asset status to `MAINTENANCE_REQUIRED`.
- 7c. Checkout is halted. Operator is notified.
- 7d. Operator either re-accommodates customer with an alternative asset (booking modified — UC-05) or cancels with full refund.

---

## UC-07: Return Asset

### Use Case Specification

| Field | Value |
|---|---|
| **Use Case ID** | UC-07 |
| **Name** | Return Asset |
| **Version** | 1.0 |
| **Priority** | Critical |
| **Status** | Active |

### Preconditions

1. Booking is in `ACTIVE` state.
2. Asset is physically returned to the designated return location.
3. Staff member is authenticated and present.

### Postconditions

1. Return timestamp recorded.
2. Post-rental condition record created with photos and measurements.
3. Final rental charges calculated (late return, extra mileage, fuel, etc.).
4. If no damage: deposit release workflow initiated (UC-09).
5. If damage found: damage assessment workflow initiated (UC-08).
6. Asset status set to `RETURNED` (pending inspection) or `AVAILABLE` (if clean).
7. Booking status set to `RETURNED`.

---

### Main Success Scenario

| Step | Actor | Action |
|---|---|---|
| 1 | Customer | Returns asset to designated location and presents keys/access. |
| 2 | Staff | Opens return workflow, scans or enters booking reference. |
| 3 | System | Retrieves booking details and pre-rental condition record for comparison. |
| 4 | Staff | Records return odometer reading. |
| 5 | System | Calculates extra mileage charges if mileage exceeds allowance. |
| 6 | Staff | Records return fuel level. |
| 7 | System | Calculates fuel surcharge if below agreed level. |
| 8 | Staff | Captures post-rental condition photos (minimum 4 angles). |
| 9 | Staff | Compares post-rental state to pre-rental condition record. |
| 10 | System | Calculates late return fee if return is after the scheduled end time. |
| 11 | Staff | Confirms no damage is present and submits return record. |
| 12 | System | Creates return record, records all surcharges, transitions booking to `RETURNED`. |
| 13 | System | Sets asset status to `AVAILABLE`. |
| 14 | System | Initiates deposit release workflow (UC-09). |
| 15 | System | Sends return confirmation and charge summary to customer. |

---

### Alternative Flows

**AF-01: Damage Detected During Return Inspection (Step 9–11)**
- 9a. Staff identifies damage not present in pre-rental condition record.
- 9b. Staff marks damage detected in return form.
- 9c. System launches Damage Assessment workflow (UC-08) as an extension.
- 9d. Asset status set to `DAMAGE_ASSESSMENT` pending resolution.
- 9e. Deposit release is deferred until assessment is complete.

**AF-02: Early Return (Step 1)**
- 1a. Customer returns asset before scheduled end date.
- 1b. System calculates refund for unused rental days per the pricing policy (some policies are non-refundable).
- 1c. Partial refund is processed if policy allows.
- 1d. Flow resumes at Step 4.

**AF-03: Late Return (Step 10)**
- 10a. Return timestamp exceeds scheduled end time by more than the grace period (default: 30 minutes).
- 10b. System calculates late return penalty per the pricing rules.
- 10c. Late fee is added to the final charge summary.
- 10d. Flow resumes at Step 11.

---

### Exception Flows

**EF-01: Asset Returned to Wrong Location**
- 2a. Staff at the return location discovers the booking specifies a different location.
- 2b. Staff records the incorrect return location.
- 2c. System applies a wrong-location surcharge per the pricing rules.
- 2d. Flow continues with return processing at the current location.

---

## UC-08: Assess Damage

### Use Case Specification

| Field | Value |
|---|---|
| **Use Case ID** | UC-08 |
| **Name** | Assess Damage |
| **Version** | 1.0 |
| **Priority** | High |
| **Status** | Active |

### Actors

| Role | Actor | Type |
|---|---|---|
| Primary | Staff | Human |
| Secondary | System | Automated |
| Secondary | Customer | Human (notified) |
| Secondary | Insurance Partner | External System |

### Preconditions

1. Asset has been returned (booking in `RETURNED` state) or damage was reported during active rental.
2. Staff has the `damage_assessment` permission.
3. Pre-rental condition photos exist for comparison.

### Postconditions

1. Damage report created with photos, description, damage type, and cost estimate.
2. Customer notified of damage findings and cost estimate.
3. Dispute window opened (default: 48 hours).
4. Deposit hold maintained.
5. If insured: insurance claim reference logged.

---

### Main Success Scenario

| Step | Actor | Action |
|---|---|---|
| 1 | Staff | Opens damage assessment form linked to the booking. |
| 2 | Staff | Selects damage location on an asset diagram (interactive map). |
| 3 | Staff | Captures damage photos (minimum 3 photos per damage item). |
| 4 | Staff | Selects damage type from taxonomy (Scratch, Dent, Crack, Tire, Mechanical, Missing Part, Other). |
| 5 | Staff | Enters damage description and estimated repair cost. |
| 6 | Staff | Indicates whether damage is covered by the customer's insurance plan. |
| 7 | System | Checks insurance plan coverage if customer purchased insurance. |
| 8 | Insurance Partner | Returns coverage confirmation and liability split. |
| 9 | System | Calculates net customer liability (damage cost minus insurance coverage). |
| 10 | Staff | Reviews and submits the damage report. |
| 11 | System | Persists damage report, stores photos in document storage. |
| 12 | System | Sends damage notification to customer with photos, description, and estimated charge. |
| 13 | System | Opens 48-hour dispute window for the customer. |
| 14 | System | Places deposit hold for the estimated damage amount. |

---

### Alternative Flows

**AF-01: Multiple Damage Items**
- 2a. Staff identifies multiple distinct damage items.
- 2b. Staff adds each as a separate damage item in the report.
- 2c. System aggregates total damage cost across all items.
- 2d. Single notification sent to customer with full itemized damage list.

**AF-02: Customer Disputes Damage Immediately**
- 13a. Customer immediately initiates a dispute (UC-14) upon receiving notification.
- 13b. Dispute window is not required to expire; active dispute is logged.
- 13c. Deposit hold is maintained pending dispute resolution.

---

### Exception Flows

**EF-01: Insurance API Unavailable (Step 8)**
- 8a. Insurance Partner API returns an error or timeout.
- 8b. System logs the error and flags the damage report for manual insurance processing.
- 8c. Staff is notified to manually confirm coverage with the insurance provider.
- 8d. Report is submitted without insurance offset; Finance Officer manually updates when confirmed.

---

## UC-09: Process Deposit Release

### Use Case Specification

| Field | Value |
|---|---|
| **Use Case ID** | UC-09 |
| **Name** | Process Deposit Release |
| **Version** | 1.0 |
| **Priority** | High |
| **Status** | Active |

### Actors

| Role | Actor | Type |
|---|---|---|
| Primary | System | Automated |
| Secondary | Finance Officer | Human (manual override) |
| Secondary | Payment Gateway | External System |
| Secondary | Customer | Human (notified) |

### Preconditions

1. Booking is in `RETURNED` state.
2. One of the following is true:
   - No damage was assessed (clean return).
   - Damage assessment is complete AND dispute window (48 hours) has expired without a dispute.
   - A dispute was filed and has been resolved by the Operator.
3. No active holds from other charges (late return, fuel) remain unprocessed.

### Postconditions

1. Deposit pre-authorization voided (clean return) or partial capture processed (damage case).
2. Final invoice generated (UC-12) and delivered.
3. Customer notified of deposit release or deduction details.
4. Financial record updated and exported to accounting system.
5. Booking status transitions to `CLOSED`.

---

### Main Success Scenario (Clean Return — Full Deposit Release)

| Step | Actor | Action |
|---|---|---|
| 1 | System | Triggered by `return.completed` event (clean return) or `dispute_window.expired` event. |
| 2 | System | Retrieves booking and verifies no outstanding charges or unresolved holds. |
| 3 | System | Calculates net refundable deposit (deposit amount minus any final fees already applied). |
| 4 | System | Calls Payment Gateway to void the pre-authorization hold. |
| 5 | Payment Gateway | Confirms void processed; pre-auth released (funds unblocked on customer card). |
| 6 | System | Creates DepositRelease financial record. |
| 7 | System | Generates final invoice (UC-12) with all charges and zero or negative balance. |
| 8 | System | Sends "Your deposit has been released" notification to customer with invoice. |
| 9 | System | Exports transaction to accounting system. |
| 10 | System | Sets booking status to `CLOSED`. |

---

### Alternative Flows

**AF-01: Partial Deposit Deduction (Damage Case)**
- 3a. Damage fees are assessed and dispute window has expired.
- 3b. System calculates: `deduction = min(damage_cost_net, deposit_amount)`.
- 3c. System calls Payment Gateway to capture `deduction` amount from the pre-auth.
- 3d. If `deduction < deposit_amount`: void the remaining pre-auth balance.
- 3e. If `deduction > deposit_amount`: additional charge is processed against saved payment method.
- 3f. Flow resumes at Step 6.

**AF-02: Manual Override by Finance Officer**
- System flags deposit for manual review (e.g., dispute resolution requires human judgment).
- Finance Officer reviews the case and enters the release/deduction amounts manually.
- Finance Officer approves the transaction in the Finance dashboard.
- Flow resumes at Step 4 with the manually specified amounts.

---

### Exception Flows

**EF-01: Payment Gateway Rejects Void Operation**
- 4a. Gateway returns an error (pre-auth already expired, gateway error).
- 4b. System logs the error and creates an alert for Finance Officer.
- 4c. Finance Officer investigates and processes manually via the gateway's dashboard.
- 4d. Finance Officer marks the deposit release as processed in the system.

---

## UC-10: Extend Rental

### Use Case Specification

| Field | Value |
|---|---|
| **Use Case ID** | UC-10 |
| **Name** | Extend Rental |
| **Version** | 1.0 |
| **Priority** | Medium |
| **Status** | Active |

### Actors

| Role | Actor | Type |
|---|---|---|
| Primary | Customer | Human |
| Secondary | Staff | Human |
| Secondary | System | Automated |
| Secondary | Payment Gateway | External System |

### Preconditions

1. Booking is in `ACTIVE` state.
2. Extension request is submitted before the current end date (or within the grace window).
3. No confirmed booking for the same asset starts within the requested extension period.
4. Customer's payment method is valid.

### Postconditions

1. Booking end date updated to the new extended date.
2. Extension fee calculated and charged immediately.
3. Deposit hold verified sufficient for the extended period; additional pre-auth processed if required.
4. Customer notified of extension confirmation and charges.
5. Updated rental contract sent to customer.

---

### Main Success Scenario

| Step | Actor | Action |
|---|---|---|
| 1 | Customer | Requests rental extension via mobile app/web, specifying new desired return date. |
| 2 | System | Checks asset availability for the extension period (current end → new end date). |
| 3 | System | Confirms no conflicting bookings exist for the asset in the extension window. |
| 4 | System | Calculates extension fee using current pricing rules. |
| 5 | Customer | Reviews extension fee and confirms the extension request. |
| 6 | System | Charges extension fee immediately against the customer's payment method. |
| 7 | Payment Gateway | Confirms charge success. |
| 8 | System | Updates booking end date and recalculates deposit requirement. |
| 9 | System | If additional deposit required: processes supplementary pre-auth. |
| 10 | System | Sends extension confirmation notification to customer. |
| 11 | System | Generates updated rental contract and delivers to customer. |

---

### Alternative Flows

**AF-01: Conflicting Booking Exists**
- 2a. System detects a confirmed booking starting within the requested extension period.
- 2b. System calculates the maximum available extension (up to the conflicting booking's start minus buffer).
- 2c. System presents the maximum extension date to the customer.
- 2d. Customer accepts the reduced extension or abandons.

**AF-02: Extension Requested by Staff on Behalf of Customer**
- 1a. Staff opens the booking in the staff portal and initiates extension on behalf of customer.
- 1b. Staff enters the new end date as requested by the customer over the phone.
- 1c. Flow resumes at Step 2.

---

### Exception Flows

**EF-01: Extension Fee Charge Fails**
- 6a. Payment Gateway declines the extension fee charge.
- 6b. System notifies customer of payment failure.
- 6c. Extension is not applied.
- 6d. System sends a late return risk notification: "Return your rental by [original end time] to avoid late fees."

---

## UC-14: File Damage Dispute

### Use Case Specification

| Field | Value |
|---|---|
| **Use Case ID** | UC-14 |
| **Name** | File Damage Dispute |
| **Version** | 1.0 |
| **Priority** | Medium |
| **Status** | Active |

### Actors

| Role | Actor | Type |
|---|---|---|
| Primary | Customer | Human |
| Secondary | System | Automated |
| Secondary | Operator | Human |
| Secondary | Insurance Partner | External System |

### Preconditions

1. A damage report exists and is linked to the customer's booking.
2. Customer has received damage notification.
3. Customer is within the dispute window (default: 48 hours from notification timestamp).
4. Customer is authenticated.

### Postconditions

1. Dispute record created, linked to damage report and booking.
2. Deposit deduction paused pending dispute outcome.
3. Operator notified with full context (booking, damage report, photos, customer evidence).
4. Customer receives dispute acknowledgement with reference number and SLA timeframe.

---

### Main Success Scenario

| Step | Actor | Action |
|---|---|---|
| 1 | Customer | Opens damage notification and clicks "Dispute This Charge". |
| 2 | System | Displays dispute form showing damage details, photos, and estimated charge. |
| 3 | Customer | Selects dispute reason from list (Pre-existing damage, Damage not caused by me, Incorrect cost estimate, Other). |
| 4 | Customer | Enters written statement describing their position. |
| 5 | Customer | Uploads supporting evidence (photos taken during/before rental, witnesses, etc.). |
| 6 | Customer | Submits the dispute. |
| 7 | System | Creates Dispute record with status `UNDER_REVIEW`. |
| 8 | System | Pauses the scheduled deposit deduction. |
| 9 | System | Sends dispute confirmation to customer with a dispute reference and SLA (e.g., 5 business days). |
| 10 | System | Notifies Operator with full dispute context. |
| 11 | Operator | Reviews dispute, pre-rental and post-rental photos, staff notes, and customer evidence. |
| 12 | Operator | Issues resolution: UPHELD (charge stands), REDUCED (partial charge), WAIVED (no charge). |
| 13 | System | Updates damage report with resolution. |
| 14 | System | Notifies customer of dispute resolution with explanation. |
| 15 | System | Proceeds with deposit deduction per resolution outcome (UC-09). |

---

### Exception Flows

**EF-01: Dispute Submitted After Window Expires**
- 1a. Customer attempts to open the dispute form after the 48-hour window.
- 1b. System displays a message: "The dispute window for this charge has expired."
- 1c. System does not allow dispute creation.
- 1d. Customer is directed to contact support for exceptional review.

---

## UC-15: Generate Fleet Report

### Use Case Specification

| Field | Value |
|---|---|
| **Use Case ID** | UC-15 |
| **Name** | Generate Fleet Report |
| **Version** | 1.0 |
| **Priority** | Medium |
| **Status** | Active |

### Actors

| Role | Actor | Type |
|---|---|---|
| Primary | Operator | Human |
| Secondary | Admin | Human |
| Secondary | System | Automated |
| Secondary | GPS Tracking Platform | External System |

### Preconditions

1. User has `OPERATOR` or `ADMIN` role.
2. At least one completed rental or maintenance event exists for the selected period.
3. GPS Platform connection is active (for telemetry-enhanced reports).

### Postconditions

1. Report generated in requested format (PDF, CSV, or Excel).
2. Report archived in document storage with access log entry.
3. Report emailed to requesting user and optionally to additional recipients.

---

### Main Success Scenario

| Step | Actor | Action |
|---|---|---|
| 1 | Operator | Navigates to Reports module and selects "Fleet Report". |
| 2 | Operator | Configures report parameters: date range, asset group or specific assets, report type (Utilization, Revenue, Maintenance, Damage), output format. |
| 3 | System | Validates parameters and estimates report size. |
| 4 | System | Queries rental, maintenance, and damage records for the specified period. |
| 5 | System | Fetches GPS telemetry data for mileage accuracy validation. |
| 6 | System | Computes fleet utilization rate per asset (rental days / available days × 100%). |
| 7 | System | Computes revenue per asset, per category, and fleet totals. |
| 8 | System | Computes maintenance costs, downtime days, and damage frequency per asset. |
| 9 | System | Renders the report with charts and tables in the requested format. |
| 10 | System | Stores report in document storage and records access log entry. |
| 11 | System | Emails report to the requesting Operator and any additional recipients specified. |
| 12 | Operator | Downloads or opens the report from the Reports dashboard. |

---

### Alternative Flows

**AF-01: Scheduled Report**
- 0a. Operator configures a recurring report schedule (weekly/monthly).
- 0b. System automatically generates and delivers the report on schedule.
- 0c. Flow resumes at Step 3.

**AF-02: Large Report Set**
- 3a. System estimates report will take over 30 seconds to generate.
- 3b. System accepts report request and returns immediately with a job ID.
- 3c. Operator is notified via email when the report is ready.
- 3d. Flow resumes at Step 10.

---

*Document version: 1.0 | Last updated: 2025 | System: Rental Management System*
