# Rental Management System — Requirements Specification

**Document Version:** 1.0  
**Status:** Approved  
**Last Updated:** 2025-01-01  
**Owner:** Product Team

---

## Table of Contents

1. [Overview](#1-overview)
2. [Stakeholders](#2-stakeholders)
3. [Functional Requirements](#3-functional-requirements)
4. [Non-Functional Requirements](#4-non-functional-requirements)
5. [Constraints](#5-constraints)
6. [Assumptions](#6-assumptions)
7. [Glossary](#7-glossary)

---

## 1. Overview

### 1.1 Purpose

This document specifies the complete requirements for the **Rental Management System (RMS)** — a platform that enables rental operators to manage their asset fleet, pricing, bookings, contracts, payments, and maintenance while providing customers with a seamless self-service rental experience across web, mobile, and agent-assisted channels.

### 1.2 Scope

The system covers the full rental lifecycle:

- **Fleet management** — asset catalog, categories, availability, GPS tracking, maintenance scheduling
- **Booking lifecycle** — search, reservation, modification, cancellation, extension
- **Rental operations** — contract generation, digital signature, checkout, return, damage assessment
- **Financial operations** — dynamic pricing, promo codes, deposit holds, payment processing, invoicing, refunds
- **Customer management** — profiles, ID verification, insurance selection, dispute resolution, blacklisting
- **Reporting and analytics** — utilization, revenue, maintenance cost, KPI dashboards
- **Notifications** — email and SMS for all key lifecycle events

### 1.3 Intended Audience

- Engineering teams building and maintaining the platform
- QA teams writing and executing test cases
- Product managers validating scope and completeness
- Operations teams understanding system capabilities
- Compliance and security teams reviewing controls

### 1.4 Business Context

Rental operators today manage fleets ranging from automobiles and motorcycles to equipment and recreational vehicles. Manual processes, disconnected tools, and lack of real-time visibility lead to double bookings, revenue leakage, and poor customer experience. This system consolidates all operational workflows into a single platform with an API-first architecture that supports integration with third-party insurance providers, payment gateways, GPS telematics, and ID verification services.

### 1.5 High-Level Goals

| Goal | Success Metric |
|------|----------------|
| Eliminate double bookings | Zero double-booking incidents post-launch |
| Increase fleet utilization | Utilization rate improvement of 15% within 6 months |
| Reduce checkout/return time | Staff checkout time under 5 minutes |
| Improve payment recovery | Damage fee collection rate above 90% |
| Customer self-service | 70%+ bookings completed without agent assistance |

---

## 2. Stakeholders

| Role | Responsibility |
|------|----------------|
| **Owner / Operator** | Manages fleet, pricing, policies, and staff |
| **Customer / Renter** | Searches, books, and rents assets |
| **Staff / Agent** | Processes checkouts, returns, and walk-in bookings |
| **System Administrator** | Configures business rules, roles, and monitors platform health |
| **Finance Team** | Reviews invoices, refunds, and financial reports |
| **Compliance Officer** | Ensures PCI-DSS, GDPR, and data retention policy adherence |

---

## 3. Functional Requirements

### FR-01: Asset Catalog Management

**Priority:** P0  
**Actor:** Owner / Operator

Operators must be able to create, update, and retire individual rental assets (vehicles, equipment, etc.) with complete metadata to support search, booking, and operational workflows.

**Detailed Requirements:**

- FR-01.1: Operator can create a new asset record with the following mandatory fields: asset name, category, make, model, year, color, license plate / serial number, VIN (for vehicles), and daily base rate.
- FR-01.2: Operator can attach optional metadata: description, feature tags (e.g., "GPS", "Bluetooth", "Child Seat"), seating capacity, fuel type, transmission type, and odometer reading.
- FR-01.3: Operator can upload up to 20 photos per asset; photos are stored in cloud object storage with CDN delivery.
- FR-01.4: Operator can define per-asset rate overrides that take precedence over category-level rates.
- FR-01.5: Operator can set asset status to one of: `available`, `rented`, `maintenance`, `reserved`, `retired`.
- FR-01.6: Setting status to `retired` removes the asset from all future availability searches but preserves all historical rental records.
- FR-01.7: The system assigns a unique system-generated asset ID upon creation.
- FR-01.8: All asset changes are recorded in the audit log with actor, timestamp, and diff.

**Acceptance Criteria:**
- An asset created with all mandatory fields is immediately searchable by operators.
- A retired asset does not appear in customer-facing availability search results.
- Asset photo URLs are accessible via CDN within 10 seconds of upload.

---

### FR-02: Asset Category Management

**Priority:** P0  
**Actor:** Owner / Operator

Operators must be able to define asset categories and attach category-level policies that apply to all assets in that category.

**Detailed Requirements:**

- FR-02.1: Operator can create a category with a name, description, icon, and sort order.
- FR-02.2: Operator can assign category-level policies: minimum rental duration, maximum rental duration, minimum renter age, required license type.
- FR-02.3: Operator can set category-level base rate, which individual assets can override.
- FR-02.4: Operator can define category-level security deposit amount.
- FR-02.5: Operator can nest categories up to two levels deep (parent → child) for hierarchical display.
- FR-02.6: Deleting a category is only permitted if no active or future bookings reference assets in that category.
- FR-02.7: Category changes propagate to all assets in the category unless the asset has an explicit override.

**Acceptance Criteria:**
- A category with minimum age of 25 years blocks bookings from customers under 25 during the booking creation flow.
- Category deletion is rejected with a validation error when active bookings exist.

---

### FR-03: Online Availability Search

**Priority:** P0  
**Actor:** Customer / Renter

Customers must be able to search for available assets using filters before booking.

**Detailed Requirements:**

- FR-03.1: Customer provides pickup date/time, return date/time, and pickup location to initiate a search.
- FR-03.2: System returns only assets whose status is `available` and that have no confirmed, pending, or reserved bookings overlapping the requested dates.
- FR-03.3: Customer can filter results by: category, price range, features (multi-select), fuel type, transmission type, and seating capacity.
- FR-03.4: Customer can sort results by: price (asc/desc), name (asc/desc), and relevance.
- FR-03.5: Search results display asset name, primary photo, key specs, and computed price for the requested duration using the dynamic pricing engine.
- FR-03.6: Search results are paginated: 20 items per page by default, configurable up to 50.
- FR-03.7: System supports fuzzy location matching: if a customer searches by city or ZIP code, the system resolves the nearest configured pickup location.
- FR-03.8: Search results are cached for 60 seconds to reduce database load; availability re-checked at booking creation.

**Acceptance Criteria:**
- An asset with a confirmed booking from Day 3–7 does not appear in search results for Day 5–9.
- A search returning 0 results displays a user-friendly empty state with suggestions.
- Search API p95 response time is under 200ms.

---

### FR-04: Booking Creation

**Priority:** P0  
**Actor:** Customer / Renter

Customers must be able to create a booking request through any supported channel.

**Detailed Requirements:**

- FR-04.1: Customer selects a specific asset from search results to begin booking creation.
- FR-04.2: Customer specifies: pickup location, dropoff location (may differ from pickup for one-way rentals), pickup date/time, return date/time.
- FR-04.3: System displays a full price breakdown before confirmation: base rate, duration discount, seasonal modifier, demand surcharge, insurance premium (if selected), taxes, and total amount.
- FR-04.4: Customer can optionally select an insurance option from available partner offerings.
- FR-04.5: Customer must be authenticated; unauthenticated users are prompted to log in or register.
- FR-04.6: System validates: customer age meets category minimum, customer has verified ID if required by category, customer is not blacklisted, asset is still available.
- FR-04.7: Customer applies an optional promo code; system validates and applies discount in real-time.
- FR-04.8: Customer provides or confirms a payment method on file for deposit pre-authorization.
- FR-04.9: A booking request is held in `pending` status for 10 minutes while payment processing completes; the asset is soft-locked during this window.
- FR-04.10: If payment fails or the 10-minute window expires, the booking is cancelled and the asset is released.

**Acceptance Criteria:**
- Booking creation fails with a descriptive error if the asset is taken by a concurrent booking during the hold window.
- The price breakdown matches the confirmed invoice to the cent.
- A blacklisted customer sees an error message and cannot proceed past validation.

---

### FR-05: Booking Confirmation

**Priority:** P0  
**Actor:** System

Upon successful payment authorization, the system must confirm the booking and notify all parties.

**Detailed Requirements:**

- FR-05.1: System transitions booking status from `pending` to `confirmed` upon successful deposit pre-authorization.
- FR-05.2: Asset status is updated to `reserved` for the duration of the confirmed booking.
- FR-05.3: System generates a unique booking reference number in format `RMS-YYYYMMDD-XXXXX`.
- FR-05.4: System sends booking confirmation email to customer within 30 seconds containing: booking reference, asset details, pickup instructions, dates, price summary, and cancellation policy.
- FR-05.5: System sends booking confirmation SMS to customer's verified phone number with booking reference and pickup date/time.
- FR-05.6: Operator receives an in-app notification of the new confirmed booking.
- FR-05.7: Confirmation email includes a calendar invite (.ics attachment) for pickup and return dates.
- FR-05.8: System records the confirmation timestamp in the booking audit trail.

**Acceptance Criteria:**
- Confirmation email is delivered within 30 seconds of payment authorization.
- Asset status transitions from `available` to `reserved` atomically — no concurrent booking can claim the same asset in the same window.
- Booking reference is unique across the system.

---

### FR-06: Booking Modification

**Priority:** P1  
**Actor:** Customer / Renter, Staff / Agent

Customers and staff must be able to modify existing bookings within permitted parameters.

**Detailed Requirements:**

- FR-06.1: Customer can modify pickup/return dates and pickup/dropoff locations.
- FR-06.2: Modifications are permitted up to the operator-configured cutoff time before pickup (default: 24 hours).
- FR-06.3: If the modification extends the rental duration, the price difference is calculated and charged to the payment method on file.
- FR-06.4: If the modification shortens the duration, the difference is credited to the customer's wallet or refunded per the refund policy.
- FR-06.5: System re-checks asset availability for the new date range; if the asset is unavailable, the modification is rejected with an explanation.
- FR-06.6: Staff agents can modify bookings without the cutoff time restriction with an audit note.
- FR-06.7: System sends modification confirmation email and SMS to customer.
- FR-06.8: Each modification creates a new revision record in the booking history.

**Acceptance Criteria:**
- A modification that extends booking duration triggers a charge for the delta within 60 seconds.
- A modification attempted within the cutoff window fails with an actionable error message directing the customer to contact support.

---

### FR-07: Booking Cancellation

**Priority:** P1  
**Actor:** Customer / Renter, Staff / Agent

Customers must be able to cancel bookings with refunds calculated per the active cancellation policy.

**Detailed Requirements:**

- FR-07.1: Customer can cancel a confirmed booking from their booking history page or confirmation email link.
- FR-07.2: Refund amount is determined by the cancellation policy tiers configured by the operator:
  - Tier 1: Cancellation > 72 hours before pickup → 100% refund
  - Tier 2: Cancellation 24–72 hours before pickup → 50% refund
  - Tier 3: Cancellation < 24 hours before pickup → 0% refund (or operator-defined minimum)
- FR-07.3: Security deposit pre-authorization is voided immediately upon cancellation regardless of tier.
- FR-07.4: Refund is initiated to the original payment method within 5 business days.
- FR-07.5: Asset status reverts to `available` immediately upon cancellation.
- FR-07.6: System sends cancellation confirmation email with refund amount and expected timeline.
- FR-07.7: Staff can override refund percentage with a documented reason (subject to audit log).
- FR-07.8: Cancelled bookings are retained in the system for reporting and audit purposes.

**Acceptance Criteria:**
- Cancellation 72+ hours before pickup results in a full refund initiated within 1 minute.
- Asset is immediately available for new bookings after cancellation.
- Cancellation policy terms are displayed to customer before they confirm cancellation.

---

### FR-08: Dynamic Pricing

**Priority:** P0  
**Actor:** System

The system must calculate rental prices dynamically based on configurable factors.

**Detailed Requirements:**

- FR-08.1: Base price formula: `Total = BaseDailyRate × Days × SeasonModifier × DemandFactor × DurationDiscount`
- FR-08.2: **Season Modifier**: Operator defines date ranges with a multiplier (e.g., peak season July–August = 1.3×, off-season November–February = 0.85×).
- FR-08.3: **Duration Discount**: Operator defines stepped discounts by duration (e.g., 7–14 days = 10% off, 15–30 days = 15% off, 30+ days = 20% off).
- FR-08.4: **Demand Factor**: System applies a configurable surcharge (up to 1.5×) when fleet utilization for the requested period exceeds a configurable threshold (default: 80%).
- FR-08.5: **Weekend Rate**: Operator can define a separate rate for bookings spanning Friday through Sunday.
- FR-08.6: Price breakdown must be itemized and returned via API for display on the frontend.
- FR-08.7: Pricing engine recalculates on every booking modification.
- FR-08.8: Locked-in price at booking confirmation is not affected by subsequent rate changes.

**Acceptance Criteria:**
- A 10-day booking during peak season with 80%+ utilization returns the correct price matching the formula.
- Price computed during search matches the price at booking confirmation (within the same pricing rule version).

---

### FR-09: Promo Code Management

**Priority:** P1  
**Actor:** Owner / Operator

Operators must be able to create and manage promotional discount codes.

**Detailed Requirements:**

- FR-09.1: Operator creates a promo code with: code string, discount type (fixed amount or percentage), discount value, start date, end date, maximum total uses, maximum uses per customer, and minimum booking value.
- FR-09.2: Promo codes can be restricted to specific asset categories.
- FR-09.3: System validates promo code in real-time during booking creation: checks expiry, usage limits, category restrictions, and minimum booking value.
- FR-09.4: Applied discount is shown as a line item in the price breakdown.
- FR-09.5: Operator can deactivate a promo code before its expiry date.
- FR-09.6: System tracks total redemptions and per-customer usage for each code.
- FR-09.7: Promo codes are case-insensitive during validation.

**Acceptance Criteria:**
- A promo code that has reached its maximum uses returns an error "Code limit reached."
- A percentage discount of 15% on a $200 booking results in a $170 charge.
- Deactivated codes are rejected immediately.

---

### FR-10: Rental Contract Generation

**Priority:** P0  
**Actor:** System, Staff / Agent

The system must generate a legally binding rental contract at the time of asset pickup.

**Detailed Requirements:**

- FR-10.1: Contract is generated as a PDF document using a template configured by the operator.
- FR-10.2: Contract includes: rental reference number, customer full name, ID number, asset details (VIN/serial, make, model, year, license plate), pickup date/time, agreed return date/time, pickup location, dropoff location, rate breakdown, total amount, security deposit amount, insurance details, fuel policy, mileage policy, damage liability terms, cancellation terms, and operator legal entity details.
- FR-10.3: Pre-filled contract is generated from the confirmed booking data; staff reviews and confirms at pickup.
- FR-10.4: Contract template is customizable by the operator (logo, colors, legal text).
- FR-10.5: Generated contracts are stored in cloud storage and accessible by authorized users for 7 years per legal retention requirements.
- FR-10.6: Contract includes a QR code linking to the digital copy.

**Acceptance Criteria:**
- A contract generated for a confirmed booking contains all required fields.
- Contract PDF is generated within 10 seconds of triggering.

---

### FR-11: Digital Signature Capture

**Priority:** P0  
**Actor:** Customer / Renter

The system must capture customer digital signatures on rental contracts at pickup.

**Detailed Requirements:**

- FR-11.1: Staff presents the contract for signature via tablet or web interface at the pickup counter.
- FR-11.2: Customer signs using a touch/stylus input on a dedicated signature pad or mobile device.
- FR-11.3: Signature is cryptographically embedded into the contract PDF and a signature hash is stored in the booking record.
- FR-11.4: Customer receives a signed copy via email immediately after signing.
- FR-11.5: Remote signing option is available for pre-arranged rentals: customer receives a signing link via email valid for 2 hours.
- FR-11.6: A contract cannot be finalized (rental status cannot move to `active`) without a captured signature.

**Acceptance Criteria:**
- Attempting to mark a rental as active without a signature returns a validation error.
- Signed PDF contains an embedded audit certificate with signer name, IP address, and timestamp.

---

### FR-12: Asset Checkout

**Priority:** P0  
**Actor:** Staff / Agent

Staff must record the asset's condition at the point of customer pickup.

**Detailed Requirements:**

- FR-12.1: Staff opens the checkout workflow for a confirmed booking.
- FR-12.2: Staff records current odometer reading (for vehicles) or runtime hours (for equipment).
- FR-12.3: Staff records fuel level on a standardized scale (Empty, 1/4, 1/2, 3/4, Full).
- FR-12.4: Staff captures at least 4 condition photos (front, rear, left, right) and can add up to 20 additional detail photos.
- FR-12.5: Staff marks any pre-existing damage on an interactive vehicle diagram with damage type and description.
- FR-12.6: All checkout data is timestamped and associated with the booking and staff member's identity.
- FR-12.7: Upon completing checkout, booking status transitions from `confirmed` to `active` and asset status transitions from `reserved` to `rented`.
- FR-12.8: Checkout workflow is available offline on the mobile app; data syncs when connectivity is restored.

**Acceptance Criteria:**
- Checkout without at least 4 photos shows a blocking validation warning.
- Checkout data is synced within 30 seconds of connectivity restoration.
- Asset status transitions to `rented` only after checkout is completed.

---

### FR-13: Rental Extension

**Priority:** P1  
**Actor:** Customer / Renter

Customers must be able to request an extension of their active rental.

**Detailed Requirements:**

- FR-13.1: Customer can request a rental extension from the active booking detail screen up to 2 hours before the scheduled return time.
- FR-13.2: System checks that the asset has no confirmed bookings starting within the requested extension period.
- FR-13.3: System calculates the additional charge for the extension period using the dynamic pricing engine.
- FR-13.4: Customer must approve the additional charge before the extension is confirmed.
- FR-13.5: Upon confirmation, the additional charge is processed immediately to the payment method on file.
- FR-13.6: If payment fails, the extension is not confirmed; customer is notified with next steps.
- FR-13.7: System sends extension confirmation email and SMS with the new return date/time.
- FR-13.8: The rental contract is amended to reflect the new return date and additional charges.

**Acceptance Criteria:**
- An extension request on an asset with an upcoming confirmed booking within the extension period is rejected.
- Extension charge is processed within 60 seconds of customer approval.

---

### FR-14: Asset Return Processing

**Priority:** P0  
**Actor:** Staff / Agent

Staff must record the asset's condition and mileage at the point of return.

**Detailed Requirements:**

- FR-14.1: Staff opens the return workflow by scanning the booking QR code or searching the booking reference.
- FR-14.2: Staff records return odometer reading or runtime hours.
- FR-14.3: Staff records return fuel level.
- FR-14.4: Staff captures return condition photos (minimum 4).
- FR-14.5: System computes mileage used = return odometer − checkout odometer and checks against the included mileage allowance.
- FR-14.6: If mileage exceeds the allowance, system calculates excess mileage charge at the configured per-mile/km rate.
- FR-14.7: System computes fuel refill charge if return fuel level is below checkout fuel level, based on the configured fuel price per unit.
- FR-14.8: System calculates late return fee if return is after the agreed return date/time (see FR-18).
- FR-14.9: Staff reviews and confirms the final charges before completing return.
- FR-14.10: Upon return completion, asset status transitions from `rented` to `available` (or `maintenance` if damage is logged).

**Acceptance Criteria:**
- Return with 10 excess miles at $0.25/mile adds a $2.50 excess mileage charge to the final invoice.
- Asset transitions to `maintenance` status when damage is flagged during return.

---

### FR-15: Damage Assessment

**Priority:** P0  
**Actor:** Staff / Agent

Staff must be able to log and document damage discovered at return.

**Detailed Requirements:**

- FR-15.1: Staff can add one or more damage entries to a return, each with: damage type (scratch, dent, crack, broken part, missing item), severity (minor, moderate, major), location on vehicle diagram, description, and photos (minimum 2 per entry).
- FR-15.2: Staff enters an estimated repair cost per damage entry.
- FR-15.3: System computes total damage cost across all entries.
- FR-15.4: System compares return condition photos against checkout condition photos using a side-by-side view to help staff identify new damage.
- FR-15.5: If total damage cost exceeds the security deposit amount, the system flags the rental for financial review.
- FR-15.6: Damage record is linked to the booking and permanently associated with the customer profile for history.
- FR-15.7: System checks that logged damage was not pre-existing (recorded at checkout) before charging the customer.

**Acceptance Criteria:**
- A damage entry without at least 2 photos returns a validation error.
- Pre-existing damage (marked at checkout) is excluded from new damage charges automatically.

---

### FR-16: Security Deposit Hold

**Priority:** P0  
**Actor:** System

The system must place a hold on the customer's payment instrument for the security deposit amount.

**Detailed Requirements:**

- FR-16.1: At booking confirmation, the system initiates a payment gateway pre-authorization for the configured security deposit amount.
- FR-16.2: Pre-authorization amount is: category-level deposit unless overridden by asset-level deposit.
- FR-16.3: System stores the pre-authorization token and expiry from the payment gateway.
- FR-16.4: If the pre-authorization expiry approaches (within 7 days) and the rental is still active, the system automatically re-authorizes.
- FR-16.5: Customer can see their deposit hold status in their booking detail view.
- FR-16.6: Deposit holds are clearly labeled on the customer's booking summary as "Hold — not a charge."

**Acceptance Criteria:**
- Deposit pre-authorization is initiated within 60 seconds of booking confirmation.
- A failed deposit pre-authorization transitions the booking back to `pending` and triggers customer notification to update payment method.

---

### FR-17: Security Deposit Release

**Priority:** P0  
**Actor:** System

The system must release or partially capture the deposit upon rental completion.

**Detailed Requirements:**

- FR-17.1: If no damage and no outstanding charges at return, the system auto-releases the full deposit hold within 48 hours of return completion.
- FR-17.2: If damage charges are confirmed, the system captures the damage amount from the deposit hold, and releases the remaining balance.
- FR-17.3: If damage charges exceed the deposit amount, the excess is charged to the customer's payment method; if this fails, the booking is flagged for collections.
- FR-17.4: Deposit release is logged with timestamp, amount released, and reason.
- FR-17.5: Customer receives email/SMS notification when deposit is released or captured.
- FR-17.6: Partial deposit capture generates an itemized invoice showing damage charges deducted.

**Acceptance Criteria:**
- A rental returned with no damage has its deposit released within 48 hours without manual intervention.
- A partial capture of $150 from a $500 deposit releases $350 and generates an invoice for $150.

---

### FR-18: Late Return Fee Calculation

**Priority:** P1  
**Actor:** System

The system must calculate and apply late return fees automatically.

**Detailed Requirements:**

- FR-18.1: If return timestamp exceeds the agreed return time by more than the grace period (default: 30 minutes), a late fee is applied.
- FR-18.2: Late fee calculation: for each partial hour beyond the grace period, apply the hourly rate (= daily rate ÷ 24). If beyond 24 hours late, apply the full day rate per additional day.
- FR-18.3: Operator can configure the grace period (0–120 minutes) and a late fee cap (e.g., maximum 2× daily rate).
- FR-18.4: Late fee is itemized on the final return invoice.
- FR-18.5: System notifies the customer via SMS/email at the agreed return time if the rental is still active.
- FR-18.6: If the customer has requested and received an extension (FR-13), the extension's return time is used for late fee calculation.

**Acceptance Criteria:**
- A return 90 minutes late with a 30-minute grace period and $80/day rate incurs a $5.00 late fee (1 hour at $80/24 = $3.33 rounded per operator config).
- A return 48 hours late incurs 2 full day charges (capped at operator maximum).

---

### FR-19: Payment Processing

**Priority:** P0  
**Actor:** Customer / Renter, Staff / Agent

The system must support multiple payment methods and processing scenarios.

**Detailed Requirements:**

- FR-19.1: Supported payment methods: credit/debit card (Visa, Mastercard, Amex), bank transfer (ACH/SEPA), cash (logged manually by staff), and in-app wallet balance.
- FR-19.2: Card payments are processed through the configured PCI-DSS compliant payment gateway (e.g., Stripe).
- FR-19.3: Card data is tokenized; the system never stores raw card numbers.
- FR-19.4: Customers can store multiple payment methods in their profile.
- FR-19.5: All payment transactions are recorded with: amount, currency, method, gateway reference, status, and timestamp.
- FR-19.6: Failed payment transactions trigger automatic retry up to 3 times with exponential backoff before marking as failed.
- FR-19.7: Cash payments are logged by staff with a receipt number; not subject to automatic retry.
- FR-19.8: Wallet top-up via card or bank transfer; wallet balance earns no interest.

**Acceptance Criteria:**
- A card payment that fails on first attempt is retried twice before the transaction is marked failed.
- Wallet balance is deducted atomically; concurrent deductions cannot result in a negative balance.

---

### FR-20: Invoice Generation

**Priority:** P0  
**Actor:** System

The system must generate PDF invoices for every billable payment event.

**Detailed Requirements:**

- FR-20.1: Invoices are generated for: booking confirmation (rental cost + deposit notice), rental completion (final charges), damage assessment charges, and refunds (credit note).
- FR-20.2: Each invoice contains: invoice number, issue date, due date, customer details, operator/company details, VAT/tax registration number, line items, tax breakdown, and total.
- FR-20.3: Invoice numbering follows the format `INV-YYYY-XXXXXXX` (sequential per year).
- FR-20.4: Invoices are emailed to the customer automatically within 2 minutes of the triggering event.
- FR-20.5: Invoices are stored in cloud storage for 7 years per accounting retention requirements.
- FR-20.6: Operators can download invoices from the operator portal.
- FR-20.7: Invoice template includes operator logo and is customizable per brand.

**Acceptance Criteria:**
- Invoice is generated within 2 minutes of the payment event.
- Invoice line items sum to the total amount on the payment record.

---

### FR-21: Refund Processing

**Priority:** P1  
**Actor:** System, Staff / Agent

The system must process partial and full refunds to the original payment method.

**Detailed Requirements:**

- FR-21.1: Refunds are triggered by: booking cancellation (per policy), booking modification with duration reduction, operator goodwill credits, and dispute resolutions.
- FR-21.2: Refund is processed to the original payment method used for that charge.
- FR-21.3: For wallet-funded bookings, refund is credited back to wallet instantly.
- FR-21.4: For card-funded bookings, refund is initiated via payment gateway; settlement takes 3–5 business days.
- FR-21.5: Refunds exceeding the original charge amount are blocked at the system level.
- FR-21.6: Each refund generates a credit note (see FR-20).
- FR-21.7: Staff can issue manual refunds up to their authorized limit; higher amounts require manager approval.
- FR-21.8: Refund status (initiated, processing, settled) is visible to both customer and operator.

**Acceptance Criteria:**
- A wallet refund of $50 is credited to wallet balance within 10 seconds.
- A refund amount larger than the original charge is rejected with an error.

---

### FR-22: Customer Profile Management

**Priority:** P1  
**Actor:** Customer / Renter

Customers must be able to manage their personal information, documents, and payment methods through a self-service portal.

**Detailed Requirements:**

- FR-22.1: Customer can update: full name, email address, phone number, date of birth, and home address.
- FR-22.2: Email and phone changes require re-verification via OTP.
- FR-22.3: Customer can upload/update driver's license, passport, or national ID document.
- FR-22.4: Customer can add, update, and remove payment methods.
- FR-22.5: Customer can view full rental history with booking details, invoices, and contracts.
- FR-22.6: Customer can download any invoice or contract from their history.
- FR-22.7: Customer can set default payment method and default pickup location preferences.
- FR-22.8: Customer can request account deletion (GDPR right to erasure); personal data is anonymized within 30 days.

**Acceptance Criteria:**
- Email change is only committed after the new email address has been verified via OTP.
- Account deletion request triggers data anonymization within 30 days.

---

### FR-23: ID Verification

**Priority:** P0  
**Actor:** Customer / Renter

The system must verify customer government-issued IDs before allowing bookings for categories that require it.

**Detailed Requirements:**

- FR-23.1: Customer uploads front and back photos of a government-issued ID (driver's license, passport, or national ID).
- FR-23.2: System integrates with a third-party ID verification provider to perform: document authenticity check, face match against selfie, and extraction of name, DOB, and ID number.
- FR-23.3: Verification result is stored with: status (verified, pending, failed), verification timestamp, and provider reference.
- FR-23.4: Unverified customers see a prompt during booking creation for categories that require verification.
- FR-23.5: Operator can manually override verification status with an audit note.
- FR-23.6: ID data is stored encrypted; only authorized staff can view raw ID details.

**Acceptance Criteria:**
- A customer with a `failed` verification cannot complete a booking for a category requiring ID verification.
- Operator manual override creates an audit log entry with the approving operator's identity.

---

### FR-24: Insurance Integration

**Priority:** P1  
**Actor:** Customer / Renter

Customers must be able to view and select insurance options from integrated partners.

**Detailed Requirements:**

- FR-24.1: System fetches available insurance products from partner APIs at booking time, passing asset category, rental duration, and customer age.
- FR-24.2: Insurance options are displayed with: provider name, coverage type, coverage limits, exclusions, and premium cost.
- FR-24.3: Customer selects one insurance option or explicitly declines coverage.
- FR-24.4: Selected insurance premium is added as a line item in the price breakdown.
- FR-24.5: Upon booking confirmation, system sends customer data and booking details to the insurance partner API to issue a policy.
- FR-24.6: Policy number and certificate are stored against the booking record and included in the confirmation email.
- FR-24.7: If the insurance partner API is unavailable, the booking can proceed with the customer explicitly acknowledging no insurance is selected.

**Acceptance Criteria:**
- Insurance premium is displayed within 3 seconds of loading the booking form.
- A confirmed booking with insurance contains the policy number in the booking record.

---

### FR-25: Maintenance Scheduling

**Priority:** P1  
**Actor:** Staff / Agent, Owner / Operator

Operators and staff must be able to schedule maintenance windows that block asset availability.

**Detailed Requirements:**

- FR-25.1: Operator or staff creates a maintenance schedule entry with: asset ID, maintenance type, start date/time, estimated end date/time, description, and assigned technician.
- FR-25.2: Upon scheduling, the system checks for conflicting confirmed bookings in the maintenance window and warns the operator.
- FR-25.3: Asset status transitions to `maintenance` at the scheduled start time.
- FR-25.4: Asset is excluded from availability search results during the maintenance window.
- FR-25.5: Operator can set maintenance as recurring (e.g., every 5,000 km or every 3 months).
- FR-25.6: System sends reminder to the assigned technician 24 hours before scheduled start.
- FR-25.7: Maintenance schedule is visible on the availability calendar (FR-28).

**Acceptance Criteria:**
- Scheduling maintenance on a date with a confirmed booking generates a conflict warning before saving.
- Asset becomes unsearchable immediately upon maintenance schedule activation.

---

### FR-26: Maintenance Job Tracking

**Priority:** P1  
**Actor:** Staff / Agent

Staff must be able to track the progress and costs of maintenance jobs.

**Detailed Requirements:**

- FR-26.1: Staff logs maintenance job status: `scheduled`, `in_progress`, `completed`, `cancelled`.
- FR-26.2: Staff logs parts used: part name, part number, quantity, and unit cost.
- FR-26.3: Staff logs labor hours and labor rate per hour.
- FR-26.4: System computes total job cost = parts cost + labor cost.
- FR-26.5: Staff records actual start and end timestamps.
- FR-26.6: Upon completing a maintenance job, the asset status reverts to `available` unless another job is scheduled.
- FR-26.7: Job records feed into fleet reporting (FR-27) for cost analysis per asset and per category.

**Acceptance Criteria:**
- Completing a maintenance job with no subsequent scheduled maintenance transitions asset to `available`.
- Total job cost is calculated correctly from parts and labor entries.

---

### FR-27: Fleet Reporting

**Priority:** P1  
**Actor:** Owner / Operator

Operators must have access to fleet performance reports.

**Detailed Requirements:**

- FR-27.1: **Utilization Report**: percentage of time each asset was in `rented` status over a date range; fleet-level aggregate.
- FR-27.2: **Revenue Report**: total rental revenue, damage revenue, late fee revenue, and refunds by asset, category, and time period.
- FR-27.3: **Maintenance Cost Report**: total maintenance cost per asset and per category over a date range; breakdown by parts and labor.
- FR-27.4: **Booking Funnel Report**: searches → bookings created → bookings confirmed → cancellations (with reasons).
- FR-27.5: Reports can be exported as CSV or PDF.
- FR-27.6: Reports can be scheduled for automatic weekly/monthly email delivery.
- FR-27.7: All reports are filterable by: date range, category, specific asset, and pickup location.

**Acceptance Criteria:**
- Utilization report for an asset rented 15 out of 30 days shows 50.0% utilization.
- CSV export of a revenue report contains all line items present in the UI view.

---

### FR-28: Availability Calendar

**Priority:** P1  
**Actor:** Owner / Operator, Staff / Agent

Operators must have a calendar view of all asset bookings and availability.

**Detailed Requirements:**

- FR-28.1: Calendar displays a Gantt-style view with assets on rows and dates on columns.
- FR-28.2: Bookings are shown as color-coded bars: confirmed (blue), active/rented (green), maintenance (orange), reserved/pending (yellow).
- FR-28.3: Calendar supports day, week, and month views.
- FR-28.4: Operator can click a booking bar to view booking details and navigate to the full booking record.
- FR-28.5: Operator can drag-and-drop a booking on the calendar to initiate a date modification (subject to FR-06 rules).
- FR-28.6: Calendar data refreshes in real-time (WebSocket or polling every 30 seconds).

**Acceptance Criteria:**
- A newly confirmed booking appears on the calendar within 30 seconds without a page refresh.
- Calendar renders up to 500 assets in the fleet view without performance degradation.

---

### FR-29: Multi-Channel Booking

**Priority:** P1  
**Actor:** All

The system must accept bookings through multiple channels.

**Detailed Requirements:**

- FR-29.1: **Web Application**: Full-featured booking, management, and self-service portal accessible via modern browsers.
- FR-29.2: **Mobile Application**: iOS and Android apps with full booking and rental management capabilities including offline checkout/return.
- FR-29.3: **Phone Agent**: Staff can create bookings on behalf of customers through the agent portal, capturing customer ID and payment method verbally.
- FR-29.4: **API (B2B)**: REST API with OAuth 2.0 authentication for third-party partners and aggregators to search availability and create bookings programmatically.
- FR-29.5: All channels share the same booking engine and inventory; a booking created on any channel is immediately visible on all others.
- FR-29.6: API consumers receive the same real-time price and availability data as direct customers.

**Acceptance Criteria:**
- A booking created via API appears on the operator calendar within 30 seconds.
- Agent-created bookings are tagged with the creating agent's ID for audit purposes.

---

### FR-30: Customer Notification

**Priority:** P0  
**Actor:** System

The system must send timely, actionable notifications to customers at key lifecycle events.

**Detailed Requirements:**

- FR-30.1: **Booking Confirmation**: Email + SMS immediately after booking is confirmed.
- FR-30.2: **Pickup Reminder**: Email + SMS 24 hours before pickup date/time.
- FR-30.3: **Return Reminder**: Email + SMS 2 hours before agreed return date/time.
- FR-30.4: **Return Overdue Alert**: SMS at the agreed return time if rental is still active; repeat every hour for 3 hours.
- FR-30.5: **Deposit Release Notification**: Email + SMS when deposit is released or captured.
- FR-30.6: **Invoice Available**: Email with PDF attachment for every invoice generated.
- FR-30.7: **Modification Confirmation**: Email + SMS when booking is modified.
- FR-30.8: **Cancellation Confirmation**: Email + SMS with refund details.
- FR-30.9: Customers can opt out of SMS notifications; email notifications remain mandatory for transactional events.
- FR-30.10: Notification delivery status (sent, delivered, failed) is tracked per message.

**Acceptance Criteria:**
- Pickup reminder SMS is sent within 5 minutes of the 24-hour mark before pickup.
- Customers who opt out of SMS receive no SMS but still receive all transactional emails.

---

### FR-31: Damage Dispute Handling

**Priority:** P1  
**Actor:** Customer / Renter

Customers must be able to dispute damage assessments they believe are incorrect.

**Detailed Requirements:**

- FR-31.1: Customer can open a damage dispute within 72 hours of receiving the damage charge notification.
- FR-31.2: Dispute form requires: reason for dispute, supporting evidence (photos or documents), and customer statement.
- FR-31.3: Dispute is routed to the operator's dispute resolution queue.
- FR-31.4: Damage charge is placed on hold pending dispute resolution; deposit capture is paused.
- FR-31.5: Operator must respond to the dispute within 5 business days.
- FR-31.6: Dispute resolution outcomes: `upheld` (charge stands), `reversed` (charge cancelled, deposit released), `partial` (reduced charge amount agreed).
- FR-31.7: Customer is notified via email of the resolution outcome.
- FR-31.8: Unresolved disputes after 10 business days escalate to a system admin flag.

**Acceptance Criteria:**
- A dispute opened within 72 hours of damage notification pauses the deposit capture.
- Dispute opened after the 72-hour window is rejected with an appropriate message.

---

### FR-32: Blacklist Management

**Priority:** P1  
**Actor:** Owner / Operator

Operators must be able to prevent specific customers from making bookings.

**Detailed Requirements:**

- FR-32.1: Operator can add a customer to the blacklist with: reason (fraud, damage non-payment, policy violation, other), reference booking ID, and supporting notes.
- FR-32.2: Blacklisted customers receive a generic "Unable to complete booking" message and are not told the reason.
- FR-32.3: Blacklist entries are private to the operator; not visible to the customer.
- FR-32.4: Operator can remove a customer from the blacklist with an audit note.
- FR-32.5: Staff and agents attempting to create a booking for a blacklisted customer see a clear warning with the blacklist reason.
- FR-32.6: Blacklist entries are included in the system audit log.

**Acceptance Criteria:**
- A blacklisted customer who attempts to book receives "Unable to complete booking" with no additional detail.
- Staff creating a booking for a blacklisted customer sees the blacklist reason and must confirm override (if permitted).

---

### FR-33: Rate Modifier Management

**Priority:** P1  
**Actor:** Owner / Operator

Operators must be able to define and manage a full schedule of rate modifiers.

**Detailed Requirements:**

- FR-33.1: Operators can create seasonal rate rules with: name, start date, end date, asset category (or all), and multiplier.
- FR-33.2: Operators can create long-term discount schedules with: minimum rental days, maximum rental days, and discount percentage.
- FR-33.3: Operators can create weekend surcharge rules: day-of-week (Fri–Sun), surcharge percentage.
- FR-33.4: Multiple rate rules can be active simultaneously; the system applies them in a defined precedence order: asset-level override > category override > global rule.
- FR-33.5: Rate modifier changes take effect only for new bookings; confirmed bookings retain their locked price.
- FR-33.6: Operators can preview the effective price for a given asset, date range, and customer segment before publishing a new rule.

**Acceptance Criteria:**
- Two overlapping seasonal rules with different categories each apply only to their respective category.
- A new rate modifier does not change the price of a booking already confirmed.

---

### FR-34: GPS Tracking Integration

**Priority:** P2  
**Actor:** Owner / Operator, Staff / Agent

For GPS-equipped assets, the system must display real-time location data during active rentals.

**Detailed Requirements:**

- FR-34.1: System integrates with configured GPS telematics provider API via webhook or polling.
- FR-34.2: Live location (latitude, longitude, speed, heading) is stored per asset at configurable intervals (default: every 60 seconds while rented).
- FR-34.3: Operator can view a map of all GPS-enabled assets currently on rent with live positions.
- FR-34.4: System raises an alert if a rented asset leaves the configured geographic boundary (geofence).
- FR-34.5: Location history for a rental is stored for 90 days post-return.
- FR-34.6: GPS tracking is an opt-in feature per asset; non-GPS assets are unaffected.
- FR-34.7: Location data is not exposed to customers; accessible only by operators and authorized staff.

**Acceptance Criteria:**
- An asset exiting its geofence triggers an operator alert within 2 minutes.
- Location data query for a completed rental returns full track history for the rental period.

---

### FR-35: Reporting Dashboard

**Priority:** P1  
**Actor:** Owner / Operator, System Admin

The system must provide a real-time KPI dashboard for business performance monitoring.

**Detailed Requirements:**

- FR-35.1: Dashboard KPIs (default 30-day window, configurable): Total Revenue, Active Rentals, Fleet Utilization Rate (%), Average Rental Duration (days), Total Bookings, Cancellation Rate (%), Damage Incident Rate (%), Top 5 Most Rented Assets.
- FR-35.2: Dashboard refreshes every 5 minutes automatically.
- FR-35.3: KPIs support drill-down by category, pickup location, and time period.
- FR-35.4: Dashboard includes a revenue trend chart (daily/weekly/monthly toggle).
- FR-35.5: Operators can configure which KPIs appear on their dashboard and in what order.
- FR-35.6: Dashboard data is computed from pre-aggregated materialized views refreshed every 5 minutes to avoid query performance impact.

**Acceptance Criteria:**
- Dashboard loads within 2 seconds with pre-aggregated data.
- Fleet Utilization Rate matches the Utilization Report (FR-27) for the same date range.

---

## 4. Non-Functional Requirements

### NFR-01: Availability

- The system must achieve **99.9% uptime** (≤ 8.76 hours downtime per year).
- Planned maintenance windows are scheduled during off-peak hours with at least 72 hours advance notice.
- The system must support graceful degradation: if a non-critical service (e.g., GPS, insurance API) is unavailable, core booking flows continue unaffected.

### NFR-02: Performance

- Read API endpoints (search, availability, booking detail): **p95 ≤ 200ms**
- Write API endpoints (booking creation, payment, checkout): **p95 ≤ 500ms**
- PDF generation (contract, invoice): **≤ 10 seconds**
- Dashboard load time: **≤ 2 seconds** with pre-aggregated data
- Bulk report export (CSV, 10,000 rows): **≤ 30 seconds**

### NFR-03: Notification Delivery

- Booking confirmation email and SMS delivered within **30 seconds** of triggering event.
- All other transactional notifications delivered within **5 minutes**.
- Notification delivery failures are retried up to 3 times with exponential backoff.

### NFR-04: Scalability

- System must support **10,000 concurrent users** without degradation.
- Horizontal scaling via containerized microservices (Kubernetes).
- Database read replicas for read-heavy workloads (search, reporting).
- Auto-scaling policies respond to CPU/memory thresholds within 60 seconds.

### NFR-05: Payment Security (PCI-DSS)

- System achieves and maintains **PCI-DSS Level 1** compliance.
- Raw card data is never stored; all card data is tokenized via the payment gateway.
- Card data is never logged or transmitted in plain text.
- Payment processing scope is isolated in a dedicated PCI-compliant network zone.
- Quarterly vulnerability scans and annual penetration tests on payment components.

### NFR-06: Data Privacy (GDPR)

- GDPR-compliant data handling for all EU customer data.
- Customers can request data export (right of access) fulfilled within 72 hours.
- Customers can request account deletion (right to erasure) fulfilled within 30 days.
- Data processing purposes are documented in a Data Processing Agreement (DPA).
- Consent is obtained for marketing communications; revocable at any time.
- Data retention schedule: active customer data retained for the duration of the account; anonymized 2 years after account deletion.

### NFR-07: Data Encryption

- All data at rest encrypted with **AES-256**.
- All data in transit encrypted with **TLS 1.3** minimum.
- Database backups are encrypted before storage.
- Encryption keys managed via a dedicated key management service (KMS).
- ID documents and sensitive customer data stored in a dedicated encrypted bucket with restricted access policies.

### NFR-08: Accessibility and Usability

- Web UI is **WCAG 2.1 AA** compliant.
- Web UI is fully **mobile-responsive** (320px minimum viewport width).
- UI supports right-to-left (RTL) layouts for Arabic and Hebrew locales.
- Application is internationalizable (i18n); strings are externalized.

### NFR-09: Offline Capability

- Mobile app supports **offline checkout and return processing**: staff can complete checkout/return workflows without network connectivity.
- Offline data is queued and synced within **30 seconds** of connectivity restoration.
- Offline mode covers: booking lookup by reference, checkout form completion, return form completion, condition photo capture.
- Conflict resolution: server state takes precedence if a booking was modified online while staff was offline.

### NFR-10: Audit Logging

- All state changes on bookings, payments, customer profiles, and assets are recorded in an immutable audit log.
- Each audit entry includes: entity type, entity ID, old state, new state, actor identity, actor IP address, and timestamp.
- Audit logs are stored separately from application data in a write-once storage system.
- Audit logs are retained for **7 years**.
- Audit logs are searchable by entity ID, actor identity, date range, and event type.

### NFR-11: Backup and Recovery

- Database full backup every **24 hours**; incremental backup every **6 hours**.
- **RTO (Recovery Time Objective): 4 hours** for full system failure.
- **RPO (Recovery Point Objective): 6 hours** maximum data loss.
- Backups are stored in a geographically separate region.
- Backup restore procedures tested quarterly.
- Point-in-time recovery (PITR) enabled with 7-day retention.

---

## 5. Constraints

### Technical Constraints

- C-01: The system is a cloud-native application deployed on a major cloud provider (AWS, GCP, or Azure) using managed services where possible.
- C-02: The backend API follows REST principles with JSON payloads; GraphQL may be used for the admin reporting layer.
- C-03: Payment gateway integration is limited to the provider specified in the infrastructure agreement (default: Stripe).
- C-04: PDF generation must not rely on external SaaS services for documents containing PII; PDFs are generated server-side.
- C-05: The mobile application is built as a cross-platform React Native application to maintain a single codebase.
- C-06: The system must support PostgreSQL 15+ as the primary relational database.
- C-07: All background jobs are processed via a durable message queue (e.g., RabbitMQ or AWS SQS) to ensure at-least-once delivery.

### Regulatory Constraints

- C-08: Rental contracts must comply with the local jurisdiction's consumer protection laws for the operator's country of operation.
- C-09: Personal data of EU residents must be stored within EU data centers unless explicit cross-border transfer mechanisms (SCCs) are in place.
- C-10: Financial records (invoices, receipts, payment records) must be retained for a minimum of 7 years per standard accounting regulations.
- C-11: ID documents uploaded by customers must not be retained beyond 90 days after account deletion per data minimization principles.

### Operational Constraints

- C-12: The system supports a maximum fleet size of 50,000 assets per operator instance.
- C-13: File uploads (photos, documents) are limited to 10 MB per file; 20 MB per batch upload.
- C-14: API rate limits apply to B2B API consumers: 1,000 requests/minute per API key.
- C-15: The system is operated as a multi-tenant SaaS platform; data isolation between tenants is enforced at the database row level using tenant ID scoping.

---

## 6. Assumptions

- A-01: Operators configure their business rules (pricing, policies, cancellation tiers) before go-live; the system does not provide default configurations for operator-specific policies.
- A-02: The payment gateway provides webhook callbacks for payment events (authorization, capture, refund, failure); the system is not designed for polling-based payment status.
- A-03: The ID verification provider returns a result (verified/failed) within 60 seconds; async verification via webhook is supported for cases exceeding this threshold.
- A-04: GPS telematics data is the responsibility of the telematics provider to supply; the system consumes it via a documented API contract.
- A-05: Insurance partner APIs follow a standard request/response format as documented in the integration specification; partner-specific deviations require a custom adapter.
- A-06: All monetary values are stored and processed in the operator's configured base currency; multi-currency conversion is out of scope for v1.
- A-07: Customers are responsible for ensuring their browser/device supports the minimum requirements (modern browser with JavaScript enabled; iOS 14+ / Android 10+ for the mobile app).
- A-08: Email delivery is handled via a transactional email service (e.g., SendGrid, AWS SES); deliverability rates are the responsibility of the email provider.
- A-09: The system assumes operators manage a single geographic region per tenant instance in v1; multi-region operations are a future enhancement.
- A-10: Phone-agent bookings assume the agent has independently verified the customer's identity per the operator's verbal verification procedure.

---

## 7. Glossary

| Term | Definition |
|------|------------|
| **Asset** | A rentable item in the fleet (vehicle, equipment, etc.) |
| **Booking** | A reservation of an asset for a specific date range |
| **Rental** | An active booking where the asset has been checked out |
| **Checkout** | The process of handing the asset to the customer at pickup |
| **Return** | The process of receiving the asset back from the customer |
| **Deposit** | A refundable security amount held at booking confirmation |
| **Pre-authorization** | A hold placed on a payment instrument without immediate capture |
| **Promo Code** | An alphanumeric code that applies a discount to a booking |
| **Season Modifier** | A multiplier applied to base rates during configured date ranges |
| **Demand Factor** | A dynamic surcharge applied based on fleet utilization levels |
| **Utilization Rate** | Percentage of time assets are actively rented vs. available |
| **RTO** | Recovery Time Objective — maximum acceptable system downtime after failure |
| **RPO** | Recovery Point Objective — maximum acceptable data loss window |
| **PCI-DSS** | Payment Card Industry Data Security Standard |
| **GDPR** | General Data Protection Regulation (EU) |
| **VIN** | Vehicle Identification Number — unique manufacturer serial number for vehicles |
| **Geofence** | A virtual geographic boundary for GPS-tracked assets |
