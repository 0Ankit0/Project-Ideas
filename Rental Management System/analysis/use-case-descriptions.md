# Use Case Descriptions

## Overview
Detailed descriptions of primary use cases in the rental management system, applicable to any asset type.

---

## UC-001: Browse and Book a Rental Asset

| Attribute | Detail |
|-----------|--------|
| **Use Case ID** | UC-001 |
| **Name** | Browse and Book a Rental Asset |
| **Actor** | Customer / Renter |
| **Description** | A customer searches available listings, selects an asset, and submits a booking request |
| **Preconditions** | Customer is registered and logged in; at least one asset is published and available |
| **Postconditions** | Booking created with status PENDING (or CONFIRMED for instant booking); availability hold placed |

**Main Flow:**
1. Customer selects an asset category and enters the desired rental period (start and end date/time)
2. System displays available listings with pricing preview for the selected period
3. Customer applies optional filters (price range, location, attributes)
4. Customer clicks on a listing to view full asset details, photos, and availability calendar
5. Customer selects the rental period and reviews the pricing breakdown
6. Customer clicks "Book Now" and confirms personal details
7. System validates availability and calculates the total price including deposit
8. Customer completes the security deposit payment
9. System creates the booking record
10. If instant booking: booking status is set to CONFIRMED immediately; both parties notified
11. If manual confirmation: booking status is PENDING; owner is notified for review

**Alternative Flows:**
- *A1 – Asset unavailable for selected dates*: System shows the next available window
- *A2 – Deposit payment fails*: Booking is not created; customer is prompted to retry

---

## UC-002: Confirm Booking and Generate Rental Agreement

| Attribute | Detail |
|-----------|--------|
| **Use Case ID** | UC-002 |
| **Name** | Confirm Booking and Generate Rental Agreement |
| **Actor** | Owner (confirms), Customer (signs) |
| **Description** | Owner approves a booking request and generates a rental agreement for digital signing |
| **Preconditions** | Booking is in PENDING status (manual confirmation mode) |
| **Postconditions** | Booking CONFIRMED; agreement signed by both parties; asset calendar blocked |

**Main Flow:**
1. Owner receives a notification of a pending booking request
2. Owner reviews the customer's profile and uploaded documents
3. Owner clicks "Confirm Booking"
4. System updates booking status to CONFIRMED and blocks the asset calendar
5. Owner navigates to the booking and selects "Generate Agreement"
6. Owner selects an agreement template and reviews the pre-filled terms
7. Owner sends the agreement to the customer for signature
8. System dispatches a signature request via the e-signature provider
9. Customer opens the agreement, reviews all terms, and signs digitally
10. E-signature provider sends a webhook confirming the customer's signature
11. System notifies the owner to countersign
12. Owner countersigns
13. System retrieves the final signed PDF and stores it against the booking
14. Both parties receive the signed agreement via email

**Alternative Flows:**
- *A1 – Owner declines booking*: Status set to DECLINED; deposit refunded; customer notified
- *A2 – Customer requests amendment*: Customer adds a comment; owner revises and resends

---

## UC-003: Pre-Rental Condition Assessment

| Attribute | Detail |
|-----------|--------|
| **Use Case ID** | UC-003 |
| **Name** | Pre-Rental Condition Assessment |
| **Actor** | Staff (conducts), Customer (countersigns) |
| **Description** | Staff records the asset's condition with a category-specific checklist and photos before handover to the customer |
| **Preconditions** | Booking is CONFIRMED; rental period has not yet started |
| **Postconditions** | Pre-rental assessment completed, signed by customer; handover recorded |

**Main Flow:**
1. Staff opens the assigned assessment task for the booking
2. System presents a condition checklist tailored to the asset category (e.g., vehicle: tyres, bodywork, fuel level; camera: lens, sensor, accessories)
3. Staff works through each checklist item and marks condition (Good / Fair / Damaged)
4. Staff captures photos for each item showing current condition
5. Staff submits the completed assessment
6. System generates an assessment report and sends it to the customer
7. Customer reviews the report and photos
8. Customer countersigns the report to acknowledge the asset's condition at handover
9. System records the countersignature and marks the handover complete
10. Rental period officially begins

**Alternative Flows:**
- *A1 – Customer disagrees with a finding*: Customer adds a dispute note before signing; flagged for owner review

---

## UC-004: Return Asset and Post-Rental Assessment

| Attribute | Detail |
|-----------|--------|
| **Use Case ID** | UC-004 |
| **Name** | Return Asset and Post-Rental Assessment |
| **Actor** | Customer (initiates return), Staff (conducts assessment), Owner (approves charges) |
| **Description** | Customer returns the asset; staff conducts a post-rental condition assessment; any damage or late-return fees are calculated |
| **Preconditions** | Booking is in ACTIVE status; rental period has started |
| **Postconditions** | Post-rental assessment recorded; additional charges raised if applicable; deposit refund initiated |

**Main Flow:**
1. Customer initiates a return via the app, logging the actual return date and time
2. System notifies staff to prepare for asset inspection
3. Staff completes the post-rental condition checklist and captures photos
4. System displays a side-by-side comparison of pre- and post-rental conditions
5. If no discrepancies and return is on time:
   - System marks the rental as RETURNED
   - System initiates the full security deposit refund
   - System generates the final invoice
6. If damage discrepancies found:
   - Owner is notified with the comparison report
   - Owner itemises damage charges with evidence
   - Customer is notified of proposed charges
7. If return is late:
   - System auto-calculates overdue fees based on the asset's hourly/daily rate
   - Overdue fee added to final invoice
8. Customer pays the final invoice (including any additional charges)
9. System releases the asset back to available status on the calendar
10. Rental is marked CLOSED

**Alternative Flows:**
- *A1 – Customer disputes damage charge*: Dispute submitted; admin can mediate

---

## UC-005: Flexible Pricing Calculation

| Attribute | Detail |
|-----------|--------|
| **Use Case ID** | UC-005 |
| **Name** | Flexible Pricing Calculation |
| **Actor** | System (automated), Customer (views breakdown) |
| **Description** | System calculates the rental fee for any asset across hourly, daily, weekly, and monthly rate tiers including peak pricing |
| **Preconditions** | Asset has at least one pricing rule configured |
| **Postconditions** | Total rental fee displayed and stored on the booking |

**Main Flow:**
1. Customer selects a rental period (e.g., 5 days)
2. System identifies all applicable pricing rules for the asset and period
3. System applies peak pricing windows if the period overlaps peak dates
4. System selects the most cost-effective rate tier combination (e.g., 1 week rate is cheaper than 7 daily rates)
5. System calculates taxes based on the asset category and jurisdiction
6. System displays the full pricing breakdown to the customer:
   - Base rental fee (with tier and rate shown)
   - Peak pricing surcharge (if applicable)
   - Tax
   - Security deposit (held separately)
   - Total due now

---

## UC-006: Maintenance Request Lifecycle

| Attribute | Detail |
|-----------|--------|
| **Use Case ID** | UC-006 |
| **Name** | Maintenance Request Lifecycle |
| **Actor** | Owner (logs/assigns/approves), Staff (executes) |
| **Description** | Full lifecycle of an asset maintenance request from logging to resolution |
| **Preconditions** | Owner is authenticated; asset exists |
| **Postconditions** | Maintenance completed and approved; asset returned to available; costs logged |

**Main Flow:**
1. Owner logs a maintenance request with a description, priority, and photos
2. System creates the request (OPEN) and blocks the asset's availability calendar
3. Owner assigns the request to a staff member
4. Staff receives a notification and accepts the assignment (status: ASSIGNED)
5. Staff begins work; updates status to IN_PROGRESS
6. Staff adds work notes, photos of completed work, and logs materials used
7. Staff marks the task as COMPLETED
8. Owner reviews the completion evidence
9. Owner approves; status changes to CLOSED
10. Owner logs the total maintenance cost
11. System unblocks the asset's availability calendar

**Alternative Flows:**
- *A1 – Staff declines*: Owner is notified; reassigns to another staff member
- *A2 – Owner reopens*: Status reverts to IN_PROGRESS with reopen reason

---

## UC-007: Security Deposit Settlement

| Attribute | Detail |
|-----------|--------|
| **Use Case ID** | UC-007 |
| **Name** | Security Deposit Settlement |
| **Actor** | Owner (settles), Customer (receives) |
| **Description** | Owner reviews post-rental assessment and settles the deposit — full refund or partial deduction |
| **Preconditions** | Post-rental assessment completed; rental is in PENDING_CLOSURE status |
| **Postconditions** | Deposit refunded or deducted; rental CLOSED |

**Main Flow:**
1. Owner navigates to the completed booking
2. Owner reviews the post-rental assessment report
3. If no damage: Owner confirms full deposit release
4. If damage found: Owner itemises deductions with description, amount, and evidence photos for each item
5. System calculates the net refund amount (deposit minus deductions)
6. Owner submits the settlement
7. Customer is notified of the settlement details
8. Customer may accept or dispute within the configured window
9. On acceptance (or after the dispute window): System processes the refund to the customer's original payment method
10. System records the settlement and generates a deposit statement
