# Use Case Descriptions

---

## Make Reservation

**Use Case ID**: UC-001
**Use Case Name**: Make Reservation
**Version**: 1.0

**Actors**
Primary: Guest
Secondary: Front Desk Staff (agent-assisted channel), OTA Channel (external platform channel), Loyalty Platform (when guest is an enrolled member), Payment Gateway (when deposit policy applies)

**Preconditions**
- The hotel property is configured and active in the HPMS with a valid operational date.
- At least one room type with available inventory exists for the requested arrival and departure dates.
- At least one active rate plan is applicable to the booking channel (direct web, OTA, corporate code, or walk-in).
- If the guest is a known loyalty member, their profile is retrievable by email address or membership number.
- The payment gateway is reachable and responding for deposit-requiring rate plans.
- The OTA channel is active and authenticated for OTA-originated bookings.

**Postconditions**
- A confirmed reservation record persists in the HPMS with a unique alphanumeric confirmation number.
- Reservation status is set to CONFIRMED for guaranteed bookings or TENTATIVE for hold bookings awaiting deposit.
- An automated confirmation email and SMS is dispatched to the guest's registered contact details.
- If the rate plan requires a deposit, the payment has been authorised or fully charged and the token is stored.
- If the booking originated from an OTA, the channel manager has decremented available inventory on the originating channel and sent a booking acknowledgement.
- If the guest is a loyalty member, their profile is linked to the reservation and the Loyalty Platform has been notified of the pending earn event.
- An audit trail entry records the reservation creation with actor ID, timestamp, source channel, and IP address.

**Main Success Scenario**
1. Guest navigates to the hotel's web booking engine or mobile app and selects the desired check-in date, check-out date, and number of guests.
2. System queries the room inventory engine for available room types on the requested dates and returns a ranked list of options with accompanying rates, photos, and amenity descriptions.
3. Guest selects a room type and reviews the displayed rate plans, which include cancellation policy terms, deposit requirements, and inclusion details.
4. Guest selects a rate plan (Best Available Rate, Advance Purchase, Bed and Breakfast package, or applicable corporate rate code).
5. Guest enters personal details: full legal name, email address, mobile phone number, country of residence, and any special requests.
6. System validates the entered email address against the guest profile database. If a matching profile is found, the guest's loyalty membership number, tier, and prior stay history are retrieved and linked to the booking session.
7. System calculates the total stay amount including room rate, applicable taxes, service charges, and any deposit amount due at booking.
8. Guest enters payment card details through the PCI-DSS-compliant hosted payment form; card data is tokenised at the client side before transmission.
9. System submits a pre-authorisation or charge request to the Payment Gateway according to the deposit policy of the selected rate plan.
10. Payment Gateway returns a successful authorisation with a transaction reference number and masked card summary.
11. HPMS generates a unique alphanumeric confirmation number in the format HTL-YYYYMMDD-NNNNN.
12. System persists the reservation record with status CONFIRMED, stores the payment token reference, and records the source channel as DIRECT.
13. System dispatches a confirmation email containing the itinerary, room type, rate plan, cancellation policy, pre-arrival instructions, and hotel contact details.
14. System dispatches a confirmation SMS containing the confirmation number and check-in date.
15. If the guest is a loyalty member, System calls the Loyalty Platform API to register the pending booking and pre-estimate the points to be earned on the stay.
16. System displays the confirmation screen to the guest with the full booking summary and confirmation number.

**Alternative Flows**

AF-1: No Availability for Requested Dates
After step 2, if no room types are available for the selected dates:
a. System displays a "No rooms available" message alongside an availability calendar showing the nearest dates with open inventory.
b. Guest selects alternative dates from the calendar and the flow resumes from step 2.
c. If no alternative dates are acceptable to the guest, the flow terminates without a reservation being created.

AF-2: Agent-Assisted Reservation at Front Desk
In step 1, if a Front Desk Staff agent is making the booking on behalf of a guest:
a. Agent searches for an existing guest profile by name, email, or loyalty number and links it, or creates a new profile if none exists.
b. Agent selects room type, rate plan, and applies any negotiated corporate rate code or complimentary upgrade.
c. Deposit collection may be deferred to check-in at the agent's discretion depending on the property's agent-booking policy.
d. System records the source channel as FRONT-DESK and logs the agent's user ID in the audit trail alongside the guest-facing record.

AF-3: OTA-Originated Reservation
When the booking is initiated by the OTA Channel actor rather than directly by the guest:
a. OTA Channel transmits a NewReservation message to the HPMS via the HTNG 2.0 / OTA XML API endpoint.
b. HPMS validates the incoming message payload: channel code, rate plan code, room type mapping, arrival and departure dates, and guest details.
c. HPMS confirms inventory availability and decrements the OTA channel's allotment for the relevant room type and date range.
d. HPMS creates the reservation record with source channel set to the OTA code (e.g., BOOKINGCOM, EXPEDIA, AIRBNB).
e. HPMS returns a booking acknowledgement response with the internal confirmation number to the OTA Channel.
f. The guest receives the OTA platform's native booking confirmation; the HPMS may additionally send a property-branded pre-arrival communication.

AF-4: Waitlist Entry When Preferred Room Type Is Sold Out
After step 2, if the preferred room type is fully allocated but a waitlist option exists:
a. System presents a waitlist offer for the preferred room type.
b. Guest confirms the waitlist entry with no financial commitment.
c. System creates a WAITLISTED reservation record.
d. When inventory becomes available through a cancellation or no-show, the system automatically promotes the earliest-submitted waitlisted reservation to CONFIRMED status and notifies the guest via email and push notification.

**Exception Flows**

EF-1: Payment Gateway Decline or Timeout
At step 9, if the Payment Gateway returns a decline response or a connection timeout:
a. System displays a masked error message ("Payment could not be processed. Please try a different card or contact your bank.").
b. System retains all guest-entered data in the session so the guest does not need to re-enter personal details.
c. Guest may attempt the booking with a different payment card; up to three attempts are permitted.
d. After three consecutive payment failures, the booking session is terminated, a reservation-attempt audit log entry is created, and no reservation record is persisted.

EF-2: Duplicate Reservation Detection
At step 6, if the system detects that an existing reservation for the same guest profile, same property, and an overlapping date range already exists in CONFIRMED or TENTATIVE status:
a. System displays a prominent duplicate warning with a summary of the existing reservation.
b. Guest can choose to proceed with the new reservation or navigate to manage the existing one.
c. If the guest proceeds, both reservations are created independently and a DUPLICATE flag is set on both records for front desk awareness.

**Business Rules Referenced**
- BR-001: Minimum advance booking window per rate plan (Advance Purchase requires booking at least 7 days before arrival).
- BR-002: Deposit policy per rate plan (non-refundable rate requires full pre-payment at booking; BAR requires credit card guarantee only).
- BR-003: Cancellation policy window defines the deadline for penalty-free cancellation (e.g., 48 hours before arrival).
- BR-004: Maximum room occupancy per room type must not be exceeded as defined in room configuration.
- BR-005: Channel-specific rate plan restrictions determine which rate plans are available on which booking channels.
- BR-006: Loyalty tier eligibility may grant access to exclusive member rates not visible to non-members.

**Non-Functional Requirements**
- Availability query response time must be under 1.5 seconds for up to 500 concurrent users.
- Payment tokenisation must comply with PCI-DSS Level 1 merchant standards.
- Confirmation email and SMS must be dispatched within 30 seconds of reservation confirmation.
- Reservation data must be written to at least two geographically separated database replicas before confirmation is returned to the guest.

---

## Check In Guest

**Use Case ID**: UC-002
**Use Case Name**: Check In Guest
**Version**: 1.0

**Actors**
Primary: Front Desk Staff
Secondary: Guest, Keycard System, Payment Gateway, Loyalty Platform

**Preconditions**
- A confirmed reservation exists in the HPMS for the guest with a status of CONFIRMED or DUE-IN for the current business date.
- At least one clean and inspected room matching the booked room type is available in inventory.
- The payment terminal is connected and initialised.
- The keycard encoder is online and loaded with sufficient blank key material.
- The HPMS business date matches or is within the valid check-in window defined for the reservation.

**Postconditions**
- The reservation status is updated to IN-HOUSE.
- A specific room number is assigned to the reservation and that room's status transitions from CLEAN/INSPECTED to OCCUPIED.
- A physical or digital keycard has been encoded and issued to the guest.
- A folio is open on the reservation and any advance charges, early check-in fees, or deposit transfers have been posted to it.
- The guest's contact details have been verified and updated in the guest profile record.
- A welcome communication has been dispatched via the guest's preferred channel.
- If the guest is a loyalty member, the check-in event has been recorded with the Loyalty Platform for milestone and earn tracking.

**Main Success Scenario**
1. Guest arrives at the front desk and presents their booking confirmation reference or provides their name.
2. Front Desk Staff opens the arrivals dashboard in the HPMS and locates the reservation by confirmation number, guest name, or room type.
3. Staff retrieves the full reservation record and verifies the guest's government-issued photo ID against the name, nationality, and date of birth on the reservation.
4. Staff confirms the room type, rate plan, length of stay, and any recorded special requests with the guest, making amendments as needed.
5. System performs an automated pre-check-in validation: confirms the reservation status is not cancelled, verifies the business date falls within the arrival window, and checks that no duplicate in-house record exists for the confirmation number.
6. Staff initiates room assignment; the system queries the room inventory engine for available, clean, inspected rooms matching the booked room type and any recorded preferences.
7. Staff confirms the system-suggested room assignment or manually selects a specific room; the system acquires an exclusive lock on the chosen room record.
8. Staff requests a payment method from the guest for folio settlement and incidental charges.
9. The payment terminal performs a pre-authorisation of the estimated folio value plus a property-configured incidental hold amount per night.
10. System posts any applicable advance charges to the guest folio: resort fee, early check-in surcharge, packages or upgrades included in the rate plan.
11. Staff places a blank keycard in the hardware encoder and initiates keycard encoding from within the HPMS check-in workflow.
12. System transmits the room number, door access permissions, stay start and end dates, and any shared access rules to the keycard system via the vendor SDK.
13. Keycard system encodes the physical card and returns a success confirmation to the HPMS.
14. Staff hands the encoded keycard to the guest along with the registration card, a hotel map, dining and amenity information, and any welcome amenity vouchers.
15. System updates the reservation status to IN-HOUSE, sets the room status to OCCUPIED, and records the exact check-in timestamp.
16. System dispatches a welcome SMS and email to the guest containing the room number, departure date, outlet operating hours, and hotel service highlights.
17. If the guest is a loyalty member, System notifies the Loyalty Platform of the check-in event to initiate milestone tracking and any tier-specific welcome benefits.

**Alternative Flows**

AF-1: Room Not Ready at Arrival Time
At step 6, if no clean and inspected room of the required type is currently available:
a. Front Desk Staff adds the guest to the room-ready waitlist for the booked room type in the HPMS.
b. Guest is directed to hotel amenities — lobby lounge, restaurant, spa, or pool — while their room is prepared.
c. When a room becomes available and passes housekeeping inspection, the HPMS sends an automated workstation alert to front desk staff and, if the guest has opted in, a push notification to the hotel mobile app.
d. Staff resumes the check-in workflow from step 7 once the room is assigned.

AF-2: Walk-In Guest Without Prior Reservation
If no reservation exists for the arriving guest:
a. Staff creates a new reservation directly in the HPMS with the source channel set to WALK-IN.
b. Staff selects an available room type and applies the walk-in house rate or BAR as per the revenue manager's current pricing instruction.
c. Full payment authorisation is required at walk-in check-in unless the property's walk-in policy specifies otherwise.
d. The flow continues from step 8 using the newly created reservation record.

AF-3: Express Pre-Check-In via Mobile App
If the guest completed self-service pre-check-in through the hotel mobile app before arrival:
a. The system has already verified the guest's digital ID via an integrated identity verification service, collected and tokenised the payment method, and pre-assigned a room based on preferences.
b. Staff retrieves the pre-checked-in reservation from the priority express lane on the arrivals dashboard.
c. Staff confirms the pre-assigned room and encodes the physical keycard (or validates mobile key issuance through the keycard system).
d. The full check-in process completes in under 60 seconds.

AF-4: Loyalty Member Complimentary Upgrade
At step 6, if the guest is a Platinum or Gold tier loyalty member and a higher room category is available at no additional charge under the property's upgrade policy:
a. System flags the upgrade eligibility on the room assignment screen with the eligible upgrade category displayed.
b. Staff offers the upgrade to the guest verbally.
c. If accepted, the upgraded room is assigned, the rate remains unchanged at the original booked category rate, and the upgrade event is recorded in the guest's loyalty profile.

**Exception Flows**

EF-1: Identity Verification Failure
At step 3, if the guest cannot produce a valid government-issued photo ID or the name on the ID does not correspond to the reservation:
a. Staff escalates to the Front Desk Manager for guest identity resolution.
b. If identity cannot be confirmed through an alternative document or verification method, check-in is refused and the reservation is flagged with a SECURITY-REVIEW status.
c. The incident is fully logged in the HPMS audit trail with the staff user ID and timestamp.

EF-2: Payment Pre-Authorisation Failure
At step 9, if the payment terminal fails to authorise the pre-authorisation hold amount:
a. Staff informs the guest of the decline in a discreet manner and requests an alternative payment method.
b. If no alternative payment method is provided and the reservation requires a financial guarantee, check-in cannot proceed and the reservation is placed on PENDING-PAYMENT hold status.
c. The Duty Manager is immediately notified via HPMS alert.

**Business Rules Referenced**
- BR-010: A room cannot be assigned to an arriving guest unless its housekeeping status is CLEAN and its inspection status is INSPECTED.
- BR-011: The pre-authorisation hold amount equals the total estimated folio value plus a property-configured incidental hold (default USD 100 per night).
- BR-012: Early check-in surcharge applies when check-in occurs before the property's standard check-in time (typically 15:00 local time).
- BR-013: Maximum room occupancy per room type as defined in the room configuration must never be exceeded during assignment.
- BR-014: Loyalty upgrade eligibility is determined by the member's current tier, room availability, and the property's defined upgrade priority matrix.

**Non-Functional Requirements**
- The arrivals dashboard must load and display the full list of same-day arrivals within 2 seconds even when 200 or more arrivals are due.
- Keycard encoding must complete within 5 seconds of the confirmation command being issued.
- The room assignment distributed lock must prevent concurrent assignment of the same room; lock timeout is set to 30 seconds to prevent deadlocks.
- All payment terminal interactions must be logged with PCI-compliant tokenised references; no clear card data may be stored in the HPMS.

---

## Check Out Guest

**Use Case ID**: UC-003
**Use Case Name**: Check Out Guest
**Version**: 1.0

**Actors**
Primary: Front Desk Staff
Secondary: Guest, Payment Gateway, Loyalty Platform, Accounting System

**Preconditions**
- The guest's reservation is in IN-HOUSE status.
- The guest's folio is open and accessible in the HPMS.
- All department charges (F&B, spa, minibar, laundry, parking) have been posted to the folio prior to checkout initiation.
- The HPMS operational date matches the guest's scheduled departure date, or an early or late checkout has been authorised by the Duty Manager.
- The payment terminal is operational and connected to the Payment Gateway.

**Postconditions**
- The folio is fully settled with a zero outstanding balance.
- A final, itemised invoice (with applicable GST or VAT breakdowns) has been generated and delivered to the guest via their preferred channel.
- The reservation status is updated to CHECKED-OUT.
- The room status is updated to VACANT-DIRTY, automatically triggering a housekeeping cleaning task in the housekeeper's queue.
- The Payment Gateway has processed a successful capture of the authorised amount or a new charge for outstanding balances.
- Loyalty points earned during the stay have been posted to the Loyalty Platform based on eligible folio charges.
- Financial transaction data is queued for export to the Accounting System in the next scheduled batch.

**Main Success Scenario**
1. Guest approaches the front desk (or initiates express checkout via the hotel mobile app) and requests checkout.
2. Staff locates the guest's reservation in the HPMS by room number, guest name, or confirmation number.
3. System retrieves and displays the full folio with an itemised breakdown of all posted charges: nightly room rate, applicable taxes and service charges, F&B outlet postings, spa and recreation charges, minibar consumption, laundry, telephone, and any credits or adjustments.
4. Staff presents the folio to the guest on screen or as a printed preview for review.
5. Guest reviews all charges and confirms they are correct.
6. Staff initiates folio settlement, selecting the appropriate payment method from the options: credit card on file (token capture), new card presented by guest, cash, corporate direct bill, or approved split payment.
7. For card-on-file payment, system submits a settlement capture request to the Payment Gateway using the stored pre-authorisation token linked to the reservation.
8. Payment Gateway confirms the capture and returns a settlement reference number and authorisation confirmation.
9. System marks the folio status as SETTLED, generates a unique invoice number in the format INV-YYYYMMDD-NNNNN, and locks the folio against further postings.
10. System renders the final invoice as a PDF document including all line items, tax breakdown per department, payment method, authorisation code, and hotel regulatory registration details.
11. System dispatches the final invoice via the guest's preferred channel: email, hotel mobile app in-box, or physical printout at the desk.
12. System updates the reservation status to CHECKED-OUT with an exact departure timestamp.
13. System updates the room status to VACANT-DIRTY and automatically creates a housekeeping cleaning task assigned to the housekeeping supervisor's queue for the departed room.
14. System calculates the loyalty points earned during the stay based on eligible settled charges and posts them to the Loyalty Platform API.
15. Settled folio data is serialised and queued for the next scheduled export batch to the Accounting System general ledger.
16. Staff thanks the guest, requests the return of any physical keycards, and the checkout process is complete.

**Alternative Flows**

AF-1: Guest Disputes a Folio Charge
At step 5, if the guest disputes one or more charges on the folio:
a. Staff investigates the disputed charge by drilling into the posting detail screen, which shows the originating department, posting agent ID, POS reference, and timestamp.
b. Staff contacts the originating outlet (restaurant, spa, minibar) via internal communication to verify the charge if the posting detail does not resolve the dispute.
c. If the charge is confirmed as an error, staff posts a correction credit to the folio with a documented reason code and obtains Duty Manager override if required.
d. The folio balance is recalculated to reflect the adjustment and the checkout flow resumes from step 6.
e. If the dispute cannot be resolved within a reasonable time, the Duty Manager takes ownership and the guest may be asked to check out with a provisional settlement while the investigation continues.

AF-2: Express Checkout via Mobile App
Before approaching the front desk, the guest initiates the checkout process through the hotel mobile app:
a. System presents the full folio to the guest within the app for review and approval.
b. Guest reviews all charges and approves them by confirming within the app.
c. System automatically processes the folio settlement using the tokenised card linked to the reservation.
d. Final invoice is generated and dispatched to the guest's email without any front desk interaction required.
e. Guest's room keycard (physical or mobile) is deactivated in the keycard system.
f. The departures dashboard on the front desk workstation updates to reflect the completed express checkout.

AF-3: Corporate Direct Bill Settlement
At step 6, if the guest's company holds a pre-approved direct billing account with the hotel:
a. Staff selects the direct bill account as the settlement method and confirms the account code.
b. System validates that the folio charges fall within the scope of the corporate billing agreement (e.g., room and tax only; no personal incidentals).
c. System transfers the in-scope folio balance to the corporate accounts receivable ledger entry.
d. The final invoice is generated addressed to the corporate entity and dispatched to the company's accounts payable contact email.

**Exception Flows**

EF-1: Card Settlement Capture Failure
At step 7, if the Payment Gateway declines the capture of the pre-authorisation:
a. Staff informs the guest discreetly and requests an alternative payment method.
b. If no alternative payment method is provided, the folio remains open with an UNSETTLED status and an accounts receivable flag is created for the Finance Manager.
c. The Duty Manager is alerted via HPMS notification and an incident record is logged.
d. The room status is still transitioned to VACANT-DIRTY regardless of folio settlement outcome to allow housekeeping to commence room preparation.

EF-2: Late Department Charge Posted After Checkout Initiation
If a department charge (e.g., late minibar scan, delayed spa posting) is transmitted to the folio after checkout initiation but before the folio has been locked:
a. System includes the late posting in the final folio calculation and recalculates the settlement amount.
b. If the folio has already been settled and locked, system creates a secondary adjustment folio for the outstanding charge and attempts to settle it using the stored card token.

**Business Rules Referenced**
- BR-020: Late checkout fee applies when departure occurs after the property's standard checkout time (typically 12:00 local time) unless waived by the Duty Manager.
- BR-021: Direct bill transfers require the room charges to fall within the explicitly defined corporate billing agreement scope.
- BR-022: Loyalty points are earned exclusively on eligible charges; taxes, third-party charges, and fee items are excluded from point calculation.
- BR-023: A folio must reach a zero settled balance before the reservation can transition to CHECKED-OUT status.

**Non-Functional Requirements**
- Folio retrieval and display must complete within 3 seconds for folios containing up to 500 line items.
- Final invoice PDF rendering and email dispatch must complete within 10 seconds of settlement confirmation.
- Card settlement capture must complete within the industry-standard 5-second payment gateway response window.

---

## Assign Room

**Use Case ID**: UC-004
**Use Case Name**: Assign Room
**Version**: 1.0

**Actors**
Primary: Front Desk Staff
Secondary: System (HPMS Room Inventory Engine), Housekeeper (indirect dependency — must have cleaned and inspected the room)

**Preconditions**
- A reservation exists in CONFIRMED or DUE-IN status for the current or a future date.
- At least one room matching the reserved room type is in CLEAN and INSPECTED status in the inventory engine.
- The selected room has no active maintenance block or out-of-order flag.
- No concurrent assignment session holds an exclusive lock on the chosen room.

**Postconditions**
- The reservation record contains a specific assigned room number.
- The assigned room's inventory status transitions from CLEAN/INSPECTED to ASSIGNED.
- The room is exclusively locked to this reservation, preventing concurrent double-assignment.
- The assignment event is recorded in the audit trail with the staff user ID, timestamp, and the previous and new room status.

**Main Success Scenario**
1. Front Desk Staff opens the room assignment panel within the check-in workflow or via the standalone room management dashboard.
2. System retrieves the reservation's booked room type, bed configuration preference, floor preference, connecting room requests, and any accessibility requirements.
3. System presents a list of eligible rooms: all rooms of the matching type that are currently CLEAN, INSPECTED, and unassigned for the full duration of the requested stay dates.
4. System optionally ranks the eligible rooms using the assignment optimisation algorithm, which balances floor walk-distance for the housekeeping team, minimises cross-category inventory consumption, and honours loyalty tier preferences.
5. Staff selects a room from the presented list or overrides the suggestion by choosing a specific room number manually.
6. Staff confirms the assignment; system acquires an exclusive distributed lock on the selected room record with a 30-second lock expiry.
7. System validates the assignment in full: confirms room type compatibility, maximum occupancy compliance, absence of maintenance block, and that the stay dates do not overlap any other confirmed assignment.
8. System updates the room assignment field on the reservation, changes the room status to ASSIGNED, releases the lock after confirmation, and returns success.
9. Assignment event is persisted in the audit log with full change detail.

**Alternative Flows**

AF-1: Complimentary Upgrade Assignment
At step 4, if the guest's loyalty tier or a revenue-driven upgrade rule qualifies the reservation for a complimentary upgrade:
a. System flags available higher-category rooms that meet the upgrade eligibility criteria alongside the standard eligible rooms.
b. Staff offers the upgrade to the guest verbally; if accepted, the higher-category room is selected, the billing rate remains unchanged, and the upgrade reason is recorded on the reservation.

AF-2: Accessible Room Requirement
At step 2, if the reservation includes an accessibility flag (mobility-accessible, hearing-accessible, or roll-in shower requirement):
a. System filters the eligible room list to display only rooms matching the specific accessibility configuration.
b. Staff assigns from the filtered accessible room list; standard rooms are hidden from the selection.

**Exception Flows**

EF-1: Concurrent Assignment Lock Conflict
At step 6, if the system fails to acquire the exclusive lock because another concurrent session locked the room within the same millisecond window:
a. System displays an Assignment Conflict alert indicating the room is no longer available.
b. Staff selects the next most suitable room from the remaining eligible list and re-attempts the assignment.

EF-2: No Available Rooms of Required Type
At step 3, if no clean and inspected rooms of the required type are available at the time of assignment:
a. System presents an inventory shortage alert clearly indicating the type and count shortfall.
b. Staff reviews available rooms in adjacent or upgrade categories for a complimentary reclassification.
c. If no suitable alternative is available, the guest is added to the room-ready waitlist and notified when a room becomes available.

**Business Rules Referenced**
- BR-010: A room must be in CLEAN and INSPECTED status to be eligible for guest assignment.
- BR-030: Accessible rooms are reserved exclusively for guests with documented accessibility requirements until the same-day arrival list is fully processed.
- BR-031: Room assignment distributed locks expire automatically after 10 minutes of inactivity to prevent inventory deadlocks.

**Non-Functional Requirements**
- The assignment screen must load and display the eligible room list within 1 second.
- Distributed lock acquisition must complete within 200 milliseconds; the lock expires after 10 minutes.

---

## Night Audit

**Use Case ID**: UC-005
**Use Case Name**: Night Audit
**Version**: 1.0

**Actors**
Primary: Night Auditor
Secondary: System (Automated Charge Engine, Report Generator, Backup Manager)

**Preconditions**
- All front desk cashier shifts for the current business day have been formally closed.
- No unposted batch transactions exist in any hotel department.
- The HPMS operational date matches the calendar date being audited.
- The Night Auditor is authenticated with an account holding the Night Auditor or Property Manager role.
- A backup destination (cloud storage or local NAS) is configured, reachable, and has sufficient capacity.

**Postconditions**
- All room charges and applicable taxes for the current night have been posted to every IN-HOUSE guest folio.
- No-show reservations have been processed according to the applicable cancellation and no-show policy.
- Advance deposits on no-show and cancelled reservations have been reviewed and transferred to revenue or retained on ledger as appropriate.
- The HPMS business date has been rolled forward to the next calendar day.
- The full suite of end-of-day management reports has been generated and archived.
- A compressed and encrypted backup of the property database has been created and integrity-verified.
- All reports have been distributed via email to the management distribution list.

**Main Success Scenario**
1. Night Auditor authenticates into the Night Audit console and initiates the pre-audit system health check.
2. System validates all pre-conditions: all cashier shifts closed, no unposted batch transactions, no open or in-progress check-in sessions, and payment terminal connectivity confirmed.
3. Night Auditor reviews the pre-audit checklist on screen and resolves any flagged open items, manually closing any unclosed shifts with supervisor co-approval where required.
4. Night Auditor initiates the trial balance run; the system calculates total debits and credits across all revenue and settlement accounts for the current business day.
5. System presents the trial balance result with a debit total, credit total, and variance. Auditor reviews the figures for any discrepancy.
6. If variances exist, Night Auditor drills into the transaction detail view to identify the source: unposted charges, duplicate entries, currency rounding differences, or voided transaction mismatches.
7. Night Auditor posts any necessary manual correction entries with a documented reason code and confirms the trial balance is balanced within accepted tolerance.
8. Night Auditor initiates automated room and tax charge posting; system iterates through all IN-HOUSE reservations and posts the nightly room rate, applicable room taxes, and service charges to each open guest folio, dated as the current business day.
9. System identifies all DUE-IN reservations that have not checked in (no-shows) and processes them per the rate plan's no-show policy: charging the no-show fee to the credit card guarantee on file, or cancelling the reservation without charge.
10. System presents a review screen of all advance deposits on no-show and cancelled reservations flagged as potentially forfeit under the cancellation policy.
11. Night Auditor reviews each flagged deposit case and authorises forfeiture or retention based on the applicable policy and any manual override instructions from the Revenue Manager.
12. System transfers approved forfeit deposit amounts to the revenue account and documents the forfeiture with a reason code.
13. Night Auditor initiates report generation for all standard end-of-day reports: occupancy and RevPAR report, daily revenue summary by department, trial balance report, accounts receivable aging report, cashier shift reconciliation summary, and no-show and cancellation report.
14. All reports are rendered as searchable PDF documents and archived in the HPMS document store.
15. Night Auditor reviews key metrics on the summary dashboard screen for anomalies — RevPAR variance, unexpected high-value adjustments, or AR balance spikes.
16. Night Auditor confirms readiness and initiates the system date rollover.
17. System closes the current business date atomically, opens the new business date, and rolls forward all open reservation dates, rate plan effectivities, and channel distribution schedules.
18. System performs an automated encrypted database backup and verifies backup integrity via SHA-256 checksum comparison.
19. System distributes all generated reports as email attachments to the configured management distribution list (General Manager, Revenue Manager, Finance Manager, and Operations Manager).
20. System activates any rate plans, restrictions, or pricing rules scheduled to take effect on the newly opened business date.

**Alternative Flows**

AF-1: Late Carry-Over Transactions from F&B
At step 2, if an F&B department has not closed its outlet shift (e.g., the bar is still open at 01:00):
a. Night Auditor waits for the department to finalise its outlet shift, or the outlet supervisor manually closes the shift from the POS terminal.
b. Any charges posted to guest folios after the audit commences are recorded against the new business date.

AF-2: Trial Balance Discrepancy Investigation
At step 5, if the trial balance does not reconcile within the accepted variance threshold:
a. System highlights the specific accounts exhibiting the discrepancy.
b. Night Auditor investigates through the drill-down transaction log, checking for unmatched reversals, duplicate posting references, or tax calculation rounding on long-stay folios.
c. Correction entries are posted with full documentation, and the trial balance is re-run to confirm reconciliation before proceeding.

**Exception Flows**

EF-1: Database Backup Failure
At step 18, if the backup process fails to complete successfully:
a. System retries the backup automatically up to three times with exponential back-off intervals of 2, 4, and 8 minutes.
b. If all retries fail, the Night Auditor receives an on-screen alert and an SMS notification.
c. The HPMS audit record marks the audit as complete from a financial perspective but raises a BACKUP-FAILED critical flag.
d. IT Operations are notified immediately via the system's alerting infrastructure.

EF-2: Room Charge Posting Error on Individual Folio
At step 8, if the automated charge posting fails for a specific folio (folio in locked state, rate plan data missing, tax configuration error):
a. System skips the affected reservation, logs the posting failure with a descriptive error code, and continues posting charges for all remaining in-house folios.
b. A Posting Exceptions report is generated listing all reservations where automated posting failed.
c. Night Auditor reviews the exceptions report and manually posts the affected nightly charges.

**Business Rules Referenced**
- BR-040: Room charges must be posted to every IN-HOUSE reservation folio every night; no reservation may be skipped.
- BR-041: No-show fee processing must reference the exact cancellation and no-show policy code attached to the reservation's rate plan.
- BR-042: The system date rollover must not commence until the trial balance has been reviewed and explicitly approved by the Night Auditor.
- BR-043: The database backup must be completed and integrity-verified before the audit workflow is marked as finalised.

**Non-Functional Requirements**
- Automated room charge posting for 500 simultaneously in-house reservations must complete within 3 minutes.
- Full report generation for all standard reports must complete within 5 minutes of initiation.
- Backup and checksum verification must complete within 15 minutes under normal storage throughput conditions.
- The date rollover is an atomic database operation; any partial completion must trigger an automatic rollback to the pre-rollover state.

---

## OTA Sync

**Use Case ID**: UC-006
**Use Case Name**: OTA Sync
**Version**: 1.0

**Actors**
Primary: Revenue Manager (manual trigger), System (automated scheduled trigger)
Secondary: OTA Channel

**Preconditions**
- At least one OTA channel is configured and in active status in the channel manager.
- Room type mappings between HPMS room category codes and the OTA's room type identifiers are fully configured.
- Rate plan mappings between HPMS rate codes and corresponding OTA rate identifiers are in place.
- OTA channel API credentials are valid and have not expired.
- The target OTA channel is accepting requests and is not in a scheduled maintenance window.

**Postconditions**
- The OTA channel reflects the current available inventory count for each room type and each date combination within the sync scope.
- The OTA channel reflects the current applicable rates for all mapped rate plans and date combinations.
- All active restrictions (minimum stay, stop sell, closed to arrival, maximum stay, advance booking window) are applied on the OTA channel.
- A sync log entry is created recording the channel code, scope, timestamp, record count, and outcome.

**Main Success Scenario**
1. Revenue Manager navigates to the Channel Distribution console within the HPMS rate management module.
2. Revenue Manager selects the target OTA channel or channels and defines the sync scope: date range, room type subset, and rate plan subset.
3. System computes the current available inventory for each room type and each date combination within the defined scope, applying channel allotment limits.
4. System retrieves the applicable rates for each mapped rate plan for all dates within the scope, accounting for any override rates, derived rates, or LOS pricing.
5. System applies all active restrictions to the appropriate room type and date combinations: stop-sell flags set to zero availability, minimum stay requirements, closed-to-arrival restrictions, and advance booking window controls.
6. System formats the availability, rate, and restriction data into an OTA XML ARI (Availability, Rates, and Inventory) message conforming to the HTNG 2.0 schema.
7. System transmits the ARI message to the OTA channel's API endpoint using the stored credentials.
8. OTA channel processes the message and returns a success acknowledgement response containing a processing reference ID.
9. System records the completed sync event in the channel distribution audit log including the channel code, date range, number of room-date combinations updated, and the OTA-returned reference.
10. System displays the sync confirmation summary to the Revenue Manager on the distribution console.

**Alternative Flows**

AF-1: Automated Delta Sync Triggered by Inventory Change
Instead of a manual Revenue Manager trigger:
a. A reservation creation, cancellation, modification, or no-show processing event triggers an inventory change event in the HPMS.
b. The system's real-time sync scheduler detects the change and determines which channels are affected.
c. System performs a delta sync containing only the changed room type and date combinations rather than a full range.
d. Results are recorded in the automated sync log without any Revenue Manager interaction required.

AF-2: Full Inventory Refresh
When a comprehensive reset of OTA inventory is required (e.g., following a major rate restructuring, a system recovery, or a detected sync desync):
a. Revenue Manager selects the Full Refresh option in the distribution console.
b. System compiles a complete ARI message covering all active room types, all published rate plans, and up to 365 days forward.
c. System transmits the full ARI message; the OTA channel replaces its entire cached inventory with the refreshed data.

**Exception Flows**

EF-1: OTA Channel API Unreachable
At step 7, if the OTA channel API endpoint is unreachable or returns an HTTP 5xx error:
a. System retries the transmission with exponential back-off: attempts at 0, 2, and 5 minutes.
b. If all retries fail, system raises a Channel Distribution Alert visible on the revenue manager's dashboard.
c. Revenue Manager is notified via email and SMS with the channel name and failure timestamp.
d. The pending sync payload is queued and automatically re-attempted when the channel API returns to availability.

EF-2: Unmapped Rate Plan in Sync Scope
At step 5, if a rate plan within the defined scope has no corresponding OTA rate code mapping configured:
a. System flags the unmapped rate plan in the sync preview and excludes it from the transmitted ARI message.
b. Revenue Manager receives an inline warning identifying the unmapped rate plan codes.
c. The sync proceeds successfully for all correctly mapped plans.

**Business Rules Referenced**
- BR-050: The inventory count pushed to any OTA channel must never exceed the channel-specific allotment configured in the inventory management console.
- BR-051: Rates pushed to OTA channels must honour rate parity agreements where contractually configured for the channel.
- BR-052: Stop-sell restriction codes override any positive inventory count for the affected room type and date, setting the published count to zero regardless of physical availability.

**Non-Functional Requirements**
- A delta sync across up to 10 active OTA channels must complete within 30 seconds end-to-end.
- A full inventory refresh for a single channel covering 365 days must complete within 5 minutes.
- All sync operations must be idempotent; receiving the same ARI message twice must not alter inventory counts beyond the intended update.

---

## Post Folio Charge

**Use Case ID**: UC-007
**Use Case Name**: Post Folio Charge
**Version**: 1.0

**Actors**
Primary: Front Desk Staff, F&B Cashier, System (automated postings)
Secondary: Night Auditor (manual corrections)

**Preconditions**
- The target guest's folio is open (reservation is in IN-HOUSE or DUE-IN status).
- The charge code being posted exists in the HPMS charge code library with an associated revenue account and tax class.
- The acting user holds write access to the folio posting function.
- For POS-originated charges, the POS-to-HPMS integration is active and authenticated.

**Postconditions**
- A new line item appears on the guest folio containing: posting date, department code, charge description, quantity, unit price, tax amount, and total.
- The folio outstanding balance is updated in real time to reflect the new charge.
- The revenue account associated with the charge code is incremented.
- An audit trail entry records the posting with the originating actor's user ID, session ID, timestamp, and full charge detail.

**Main Success Scenario**
1. Front Desk Staff opens the guest's folio from within the reservation record.
2. Staff selects the Post Charge function and chooses the applicable charge code from the charge code library (e.g., MINIBAR-BEER, LAUNDRY-EXPRESS, PHONE-INTL, RESORT-FEE, PARKING-DAILY).
3. Staff enters the quantity and reviews the pre-populated unit price sourced from the charge code configuration (editable with elevated permission if pricing adjustment is warranted).
4. Staff optionally adds a description note for clarity on the folio line item (e.g., "Bottle of Chardonnay — Room Service 22:15").
5. Staff confirms the posting and reviews the pre-submission summary showing the gross amount, tax breakdown, and updated folio balance.
6. System validates the posting: confirms the charge code is active, the folio is open, and the posting does not violate any folio business rules.
7. System posts the charge to the folio, updating the balance in real time and assigning a unique posting reference number.
8. The folio display refreshes to show the new line item with full detail.

**Alternative Flows**

AF-1: POS-Originated Charge via Integration
When the charge originates from an F&B POS terminal:
a. F&B Cashier closes a restaurant check to a room account by entering the guest's room number at the POS terminal.
b. POS system transmits a charge posting request to the HPMS folio posting API with the check details, room number, POS reference, and amount.
c. HPMS validates the room number, confirms the folio is open, and posts the charge automatically without any front desk interaction.
d. POS terminal receives a posting confirmation response and prints a receipt noting "Charged to Room Account."

AF-2: Package Inclusion Gross-Net Posting
When a charge is a component included in the guest's rate plan package (e.g., daily breakfast):
a. System posts the charge at the full published rate to correctly record the revenue in the F&B department.
b. System immediately posts an offsetting package credit of equal value against the room folio.
c. The net financial impact on the guest's folio balance is zero, but the departmental revenue statistics are captured at the full gross rate for management reporting.

**Exception Flows**

EF-1: Folio Already Settled or Closed
If the target folio has already been settled and locked (guest has checked out):
a. System blocks the posting attempt and displays an error indicating the folio is closed.
b. Staff must create a post-departure adjustment folio for the departed guest, which requires Duty Manager approval.

EF-2: Charge Code Not Found in Library
If the entered charge code does not exist in the active charge code library:
a. System returns an error indicating the code is unrecognised.
b. Staff may search the charge code library by keyword or department to find the correct code.
c. If the required charge code does not exist, staff escalates to the Finance Manager for charge code creation.

**Business Rules Referenced**
- BR-060: All folio postings must use predefined, active charge codes from the library; free-text charges are not permitted without documented Duty Manager override.
- BR-061: Posting a charge to a closed or checked-out folio requires Duty Manager authorisation and a documented reason code.
- BR-062: Tax amounts are calculated automatically as a separate line item based on the tax class assigned to the charge code; tax rates cannot be manually overridden at the posting level.

**Non-Functional Requirements**
- Folio charge posting must complete and the folio balance must update within 500 milliseconds of confirmation.
- The POS-to-HPMS charge posting API must handle 200 concurrent posting requests without degradation in response time.

---

## Process Payment

**Use Case ID**: UC-008
**Use Case Name**: Process Payment
**Version**: 1.0

**Actors**
Primary: Front Desk Staff, Night Auditor, F&B Cashier
Secondary: Payment Gateway, Guest

**Preconditions**
- The guest's folio has a non-zero outstanding balance.
- The payment terminal is connected, initialised, and in communication with the Payment Gateway.
- The Payment Gateway is reachable and responding.
- For stored-token payments, a valid PCI-compliant payment token exists on the reservation or guest profile.
- The acting user holds a payment processing permission within the HPMS.

**Postconditions**
- The outstanding folio balance is reduced by the payment amount applied.
- A payment line item appears on the folio as a credit entry with the tender type, amount, and authorisation reference.
- The Payment Gateway has confirmed the transaction with an authorisation or settlement reference.
- A payment receipt is generated and available for physical printing or email delivery.
- The payment is recorded in the active cashier shift report for the acting user.
- If the folio balance reaches zero, the folio is flagged as SETTLED and locked against further postings.

**Main Success Scenario**
1. Staff opens the guest folio and selects the Process Payment function.
2. Staff selects the payment method from the available options: credit or debit card (card present or stored token), cash, cheque, hotel voucher, or corporate direct bill transfer.
3. For a card-present transaction, the guest inserts, taps, or swipes their card on the connected payment terminal.
4. The payment terminal encrypts the card data at the hardware level and transmits the authorisation request to the Payment Gateway.
5. The Payment Gateway processes the transaction against the card issuer and returns an authorisation code with the approved amount.
6. HPMS receives the authorisation response, posts the payment as a folio credit line item, and updates the outstanding balance.
7. System generates a payment receipt containing the authorisation code, masked card number (last four digits), amount, tender type, currency, transaction timestamp, and hotel contact details.
8. Staff presents the receipt to the guest as a physical printout or dispatches it via email per the guest's preference.
9. If the folio balance reaches zero following the payment, system marks the folio as SETTLED and restricts further postings without manager override.

**Alternative Flows**

AF-1: Cash Payment Processing
At step 2, if the guest tenders cash:
a. Staff enters the cash amount tendered by the guest into the HPMS payment screen.
b. System calculates the change due and displays it prominently on screen.
c. Staff collects the cash, issues the correct change from the float, and confirms the transaction in the HPMS.
d. System posts the cash payment to the folio with the tender type CASH and the exact amount.

AF-2: Split Payment Across Multiple Tender Types
If the guest wishes to pay using more than one payment method (e.g., USD 200 by card and the remaining balance in cash):
a. Staff initiates a partial payment for the first tender type and enters the partial amount.
b. System posts the partial payment credit and displays the remaining outstanding balance.
c. Staff processes the second tender type for the remaining balance.
d. Each payment tender appears as a separate line item on the folio with its own authorisation reference.

**Exception Flows**

EF-1: Payment Declined by Gateway
At step 5, if the Payment Gateway returns a decline response:
a. System displays a generic decline message to the staff member without revealing the specific issuer decline reason to the guest ("Your card could not be processed. Please try a different payment method.").
b. Staff discreetly requests an alternative payment method from the guest.
c. If the guest cannot provide an alternative, the folio remains open and an UNSETTLED flag is set for Finance Manager follow-up.

EF-2: Payment Terminal Offline
If the payment terminal is not communicating with the Payment Gateway:
a. Staff activates the terminal's offline transaction mode if available, which stores the transaction locally for later submission.
b. Terminal queues the offline transaction and submits it to the gateway automatically when network connectivity is restored.
c. Staff notes the offline transaction reference and monitors for the deferred settlement confirmation.

**Business Rules Referenced**
- BR-070: Cash payments exceeding the property-configured high-value cash threshold (default USD 3,000 per transaction) require Duty Manager co-approval before posting.
- BR-071: Change due to the guest must be returned as physical cash; the change amount must not be processed as a refund through the payment terminal.
- BR-072: All card data in transit must be encrypted using TLS 1.2 or higher; clear card numbers must never be transmitted to or stored within the HPMS at any point.
- BR-073: Every payment transaction must be associated with an active cashier session for audit trail and shift reconciliation purposes.

**Non-Functional Requirements**
- Card payment authorisation must complete within 5 seconds under normal gateway response conditions.
- Payment receipts must be generated and ready for printing within 3 seconds of gateway confirmation.
- All payment data in transit must be encrypted using TLS 1.2 minimum; TLS 1.3 is the preferred standard.
- Payment terminal hardware must comply with PCI PTS (PIN Transaction Security) standards for all cardholder-present transactions.
