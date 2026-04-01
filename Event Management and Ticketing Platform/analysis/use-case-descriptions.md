# Use-Case Descriptions — Event Management and Ticketing Platform

## Overview

This document provides full structured descriptions for the eight key use cases of the Event Management and Ticketing Platform. Each use case is presented with complete detail to support system design and test planning.

---

## UC-01: Create Event

| Attribute | Value |
|---|---|
| **Use Case ID** | UC-01 |
| **Name** | Create Event |
| **Actors** | Organizer (primary), PlatformAdmin (secondary—approval in regulated markets) |
| **Preconditions** | Organizer account is active and approved. Organizer is authenticated. |
| **Trigger** | Organizer selects "Create New Event" from the organizer dashboard. |

### Main Flow

1. Organizer selects event type: in-person, virtual, or hybrid.
2. Organizer enters: event title, short description, full description (rich text), category, and sub-category.
3. Organizer enters event dates: start date/time, end date/time, and timezone.
4. For in-person or hybrid: organizer selects an existing venue or creates a new venue record.
5. Organizer uploads an event cover image (minimum 1200×630 px, maximum 5 MB).
6. System auto-saves the draft and assigns a unique event ID and URL slug.
7. Organizer configures the refund policy (full, partial, none) and sets a refund deadline.
8. Organizer sets visibility: Public, Private (link only), or Unlisted.
9. Organizer clicks "Save Draft" or proceeds to ticket type configuration.
10. System validates all required fields and displays field-level errors for any missing data.
11. Valid draft is stored with status = `DRAFT`.

### Alternative Flows

**AF-01A — Duplicate Event:**
- At step 2, organizer selects "Duplicate from existing event."
- System pre-fills all fields from the selected event.
- Organizer adjusts dates and any changed fields.
- Flow continues from step 6.

**AF-01B — Validation Failure:**
- At step 10, one or more required fields fail validation.
- System highlights failing fields with inline error messages.
- Draft remains unsaved.
- Flow returns to step 2 for correction.

**AF-01C — Venue Not Found:**
- At step 4, organizer searches for a venue that does not exist.
- Organizer selects "Add New Venue."
- System opens a venue creation sub-form (name, address, capacity, map coordinates).
- On save, the new venue is linked to the event.
- Flow continues from step 5.

### Postconditions

- Event record exists in the database with status `DRAFT`.
- Organizer is redirected to the event management dashboard for the new event.
- Event is not publicly visible until published.

---

## UC-02: Purchase Ticket

| Attribute | Value |
|---|---|
| **Use Case ID** | UC-02 |
| **Name** | Purchase Ticket |
| **Actors** | Attendee (primary), PaymentGateway (external), EmailSMSService (external), TaxService (external) |
| **Preconditions** | Event is in `PUBLISHED` state. Ticket type inventory is greater than zero. Attendee has a valid account or is proceeding as guest. |
| **Trigger** | Attendee clicks "Buy Tickets" on the event detail page. |

### Main Flow

1. System displays available ticket types with prices, descriptions, and remaining quantities.
2. Attendee selects ticket type(s) and quantity within per-order limits.
3. For reserved-seating events: attendee is redirected to the seat map to choose specific seats.
4. System holds selected seats/inventory for 10 minutes (session lock).
5. Attendee proceeds to the checkout form and enters personal details (name, email, phone).
6. Attendee optionally enters a promo code; system validates and applies discount.
7. System calls TaxService to calculate applicable taxes based on event location and attendee locale.
8. System displays order summary: items, subtotal, discount, tax, and total.
9. Attendee enters payment details in the hosted Stripe payment form.
10. System submits payment intent to PaymentGateway.
11. PaymentGateway confirms payment success.
12. System decrements inventory, releases the seat hold, and marks seats as sold.
13. System creates Order (status = `PAID`), OrderItems, and QR codes.
14. System publishes `OrderCompleted` and `TicketPurchased` domain events.
15. EmailSMSService sends a confirmation email with PDF ticket and QR code.
16. Attendee is redirected to the order confirmation page.

### Alternative Flows

**AF-02A — Payment Declined:**
- At step 11, PaymentGateway returns a decline code.
- System displays a specific error message (e.g., "Card declined—please try a different card").
- Held seats remain locked for the remaining session time.
- Flow returns to step 9.

**AF-02B — Promo Code Invalid:**
- At step 6, promo code is expired, usage-limit reached, or not applicable to selected tickets.
- System displays "Invalid or expired promo code."
- Order total reverts to undiscounted amount.
- Flow continues from step 7 without a discount.

**AF-02C — Inventory Sold Out During Hold:**
- Between steps 4 and 12, another transaction claims the last ticket for the same type.
- System detects conflict at step 12 during inventory decrement.
- System rolls back payment capture via PaymentGateway (void/refund).
- System notifies attendee: "Sorry, those tickets are no longer available."
- Flow terminates; attendee is offered the waitlist.

**AF-02D — Session Hold Expired:**
- At any step before step 11, the 10-minute hold timer expires.
- System releases held seats and invalidates the session.
- System displays: "Your session has expired. Please start again."
- Flow terminates; attendee may restart from step 1.

### Postconditions

- Order record exists with status `PAID`.
- Inventory decremented by the purchased quantity.
- QR codes generated and linked to Order and Attendee records.
- Confirmation email delivered within 60 seconds.

---

## UC-03: QR Check-in

| Attribute | Value |
|---|---|
| **Use Case ID** | UC-03 |
| **Name** | QR Check-in |
| **Actors** | CheckInStaff (primary), BadgeService (internal) |
| **Preconditions** | Staff member is authenticated in the Check-in app. Event has started or is within the pre-admission window. |
| **Trigger** | Staff member activates the QR scanner in the Check-in PWA. |

### Main Flow

1. Staff opens the Check-in app and selects the active event.
2. App displays the QR scanner view using the device camera.
3. Staff points the camera at the attendee's QR code (printed or on screen).
4. App decodes the QR payload (ticket ID and check-in token).
5. App sends a check-in request to CheckInService with the decoded payload.
6. CheckInService validates: ticket exists, token matches, ticket status is `PAID`, not previously checked in.
7. CheckInService creates a `CheckIn` record with timestamp, gate, and staff ID.
8. CheckInService marks the ticket as `CHECKED_IN`.
9. App displays a green success screen with the attendee's name and ticket type.
10. If badge printing is configured, CheckInService publishes `CheckInCompleted` event.
11. BadgeService subscribes to the event and sends a print job to the assigned printer.

### Alternative Flows

**AF-03A — Already Checked In:**
- At step 6, the ticket already has a `CheckIn` record.
- CheckInService returns error code `ALREADY_CHECKED_IN`.
- App displays a red screen: "Ticket already used — [datetime of first scan] at [gate]."
- Staff is prompted to consult a supervisor.

**AF-03B — Invalid Ticket:**
- At step 6, the token does not match or the ticket ID does not exist.
- App displays a red screen: "Invalid ticket — do not admit."

**AF-03C — Offline Mode:**
- Device loses network connectivity between steps 4 and 5.
- App checks the locally cached ticket database (synced at app launch).
- If found: performs offline check-in, stores locally, and syncs when connectivity restores.
- If not found: displays: "Cannot verify — please use manual lookup."

**AF-03D — Cancelled Ticket:**
- At step 6, ticket status is `CANCELLED` or `REFUNDED`.
- App displays a red screen: "Ticket cancelled — do not admit."

### Postconditions

- `CheckIn` record created for the valid ticket.
- Ticket status updated to `CHECKED_IN`.
- Badge print job queued (if configured).
- Scan event logged with timestamp and staff ID.

---

## UC-04: Process Refund

| Attribute | Value |
|---|---|
| **Use Case ID** | UC-04 |
| **Name** | Process Refund |
| **Actors** | Attendee (primary), FinanceAdmin (secondary), PaymentGateway (external), EmailSMSService (external) |
| **Preconditions** | Order exists with status `PAID`. Event has not yet occurred (or organizer has cancelled). |
| **Trigger** | Attendee clicks "Request Refund" on the order detail page, or organizer cancels the event. |

### Main Flow

1. Attendee navigates to their order page and selects "Request Refund."
2. System retrieves the applicable refund policy for the event.
3. System evaluates eligibility: checks current date against refund deadline.
4. System displays the refund amount (full or partial per policy) and terms.
5. Attendee confirms the refund request.
6. System creates a `Refund` record with status `PENDING`.
7. System publishes a `RefundRequested` event.
8. RefundService calls PaymentGateway to initiate the refund to the original payment method.
9. PaymentGateway confirms the refund is initiated.
10. RefundService updates Refund status to `PROCESSING`.
11. PaymentGateway sends a webhook confirming refund settlement (typically 5–10 business days).
12. RefundService updates Refund status to `COMPLETED`.
13. Ticket status is updated to `REFUNDED`.
14. EmailSMSService sends a refund confirmation email with the refund amount and timeline.

### Alternative Flows

**AF-04A — Outside Refund Window:**
- At step 3, the refund deadline has passed.
- System displays: "Refunds are no longer available for this event per the organiser's policy."
- Attendee cannot proceed with the self-service request.
- Attendee may contact support for a manual review.

**AF-04B — Admin Override Refund:**
- FinanceAdmin accesses the order and selects "Issue Override Refund."
- Admin enters a mandatory reason and specifies the refund amount (partial or full).
- Flow continues from step 6 with an admin override flag set.
- Audit log captures admin user ID, reason, and timestamp.

**AF-04C — Event Cancellation Refund:**
- Organizer cancels the event.
- System queries all `PAID` orders for the event.
- For each order, the full refund flow executes automatically (steps 6–14).
- Attendees receive a cancellation and refund notification.

**AF-04D — PaymentGateway Failure:**
- At step 8, PaymentGateway returns an error (e.g., timeout, declined).
- RefundService sets Refund status to `FAILED` with the error code.
- System retries up to 3 times with exponential backoff.
- If all retries fail, an alert is sent to the FinanceAdmin for manual intervention.

### Postconditions

- Refund record exists with status `COMPLETED`.
- Ticket status is `REFUNDED`.
- Original payment method has been credited.
- Confirmation email delivered to attendee.
- Inventory is restored for the refunded ticket quantity.

---

## UC-05: Manage Waitlist

| Attribute | Value |
|---|---|
| **Use Case ID** | UC-05 |
| **Name** | Manage Waitlist |
| **Actors** | Attendee (primary), Organizer (secondary), EmailSMSService (external) |
| **Preconditions** | Event ticket type inventory is zero (sold out). Waitlist is enabled by the organizer. |
| **Trigger** | Attendee clicks "Join Waitlist" on the sold-out ticket type. |

### Main Flow

1. Attendee clicks "Join Waitlist" on the ticket type row.
2. System displays a waitlist form requesting: name, email, and optional phone.
3. Attendee submits the form.
4. System creates a `Waitlist` entry with a queue position and timestamp.
5. System sends a waitlist confirmation email with the attendee's position.
6. When a ticket becomes available (cancellation or refund), WaitlistService detects the inventory increase.
7. WaitlistService identifies the first eligible attendee in the queue (earliest timestamp).
8. System sends an offer email with a unique claim link and a 24-hour expiry timer.
9. Attendee clicks the link and lands on a pre-populated checkout page.
10. Attendee completes payment; flow follows UC-02 from step 9.
11. On successful payment, the waitlist entry is marked `CLAIMED`.
12. System promotes the next attendee if additional spots exist.

### Alternative Flows

**AF-05A — Offer Expires:**
- At step 9, the 24-hour window expires before the attendee completes checkout.
- System marks the waitlist entry as `EXPIRED`.
- WaitlistService advances to the next person in the queue.
- The original offer link is invalidated.

**AF-05B — Attendee Removes Themselves:**
- Attendee clicks "Leave Waitlist" from the confirmation email or attendee portal.
- System marks the waitlist entry as `WITHDRAWN`.
- No further notifications are sent to this entry.

**AF-05C — Organizer Manually Promotes:**
- Organizer navigates to the waitlist management page.
- Organizer selects one or more attendees and clicks "Promote."
- System sends offer emails to the promoted attendees.
- Offer expiry timer starts.

### Postconditions

- Waitlist entry exists with status `CLAIMED` for successful purchases.
- Inventory correctly reflects the new owner.
- Remaining waitlist queue is intact for future availability.

---

## UC-06: Apply Promo Code

| Attribute | Value |
|---|---|
| **Use Case ID** | UC-06 |
| **Name** | Apply Promo Code |
| **Actors** | Attendee (primary) |
| **Preconditions** | Attendee has selected tickets and is on the order summary step. A valid promo code exists. |
| **Trigger** | Attendee enters a code in the promo code field and clicks "Apply." |

### Main Flow

1. Attendee enters a promo code string in the promo code input field.
2. System sends a validation request to PromotionService with: code, event ID, ticket type IDs, and order total.
3. PromotionService checks: code exists, is active, has not exceeded usage limit, is not expired, and minimum order value is met.
4. PromotionService checks ticket type restrictions (if any).
5. PromotionService returns the discount type (percentage/fixed) and value.
6. System calculates the discounted amount and updates the order summary display.
7. Discount record is associated with the pending order.
8. On payment completion, PromotionService increments the code's usage count atomically.

### Alternative Flows

**AF-06A — Expired Code:**
- At step 3, the code's expiry date has passed.
- System displays: "This promo code has expired."

**AF-06B — Usage Limit Reached:**
- At step 3, usage count equals the maximum allowed.
- System displays: "This promo code is no longer available."

**AF-06C — Minimum Order Not Met:**
- At step 3, order total is below the minimum threshold.
- System displays: "This code requires a minimum order of $[amount]."

**AF-06D — Wrong Ticket Type:**
- At step 4, the code applies only to VIP tickets but attendee selected General Admission.
- System displays: "This code is not valid for the selected ticket types."

### Postconditions

- Discount record linked to the order.
- Order total reflects the discounted price.
- Promo code usage count incremented on payment completion.

---

## UC-07: Organizer Payout

| Attribute | Value |
|---|---|
| **Use Case ID** | UC-07 |
| **Name** | Organizer Payout |
| **Actors** | Organizer (primary), FinanceAdmin (secondary), PaymentGateway (external), EmailSMSService (external) |
| **Preconditions** | Event has concluded (event end date + T+2 business days elapsed). Total net revenue is positive. Organizer bank account details are on file and verified. No open disputes on the event's orders. |
| **Trigger** | PayoutScheduler job runs nightly and identifies eligible events. |

### Main Flow

1. PayoutScheduler identifies events where `end_date + 2 business days <= today` and no payout has been initiated.
2. System calculates gross revenue (sum of all `PAID` OrderItems for the event).
3. System deducts: platform service fee, payment processing fees, and any refunds issued.
4. System creates a `Payout` record with status `PENDING` and itemised fee breakdown.
5. FinanceAdmin receives a notification to review the payout queue.
6. FinanceAdmin reviews the payout details and clicks "Approve."
7. System updates Payout status to `APPROVED`.
8. System calls PaymentGateway (Stripe Connect or bank transfer API) to initiate the transfer.
9. PaymentGateway confirms transfer initiation.
10. Payout status is updated to `PROCESSING`.
11. PaymentGateway webhook confirms settlement.
12. Payout status is updated to `COMPLETED`.
13. EmailSMSService sends the organizer a payout confirmation with a downloadable invoice.

### Alternative Flows

**AF-07A — Admin Rejects Payout:**
- At step 6, FinanceAdmin finds a discrepancy and clicks "Reject."
- Admin provides a mandatory rejection reason.
- Payout status is set to `REJECTED`.
- Organizer receives an email with the rejection reason and next steps.

**AF-07B — Bank Transfer Failure:**
- At step 8, PaymentGateway returns an error (invalid bank details, account closed).
- Payout status is set to `FAILED` with the error details.
- FinanceAdmin is alerted to contact the organizer for updated bank details.
- Organizer updates bank details; admin retries the payout.

**AF-07C — Open Dispute Holds Payout:**
- At step 1, the event has one or more unresolved chargebacks.
- Payout for the event is placed on hold until disputes are resolved.
- Organizer and FinanceAdmin are notified.

### Postconditions

- Payout record with status `COMPLETED`.
- Net amount transferred to organizer's bank account.
- Invoice generated and available for download.
- Payout confirmation email sent to organizer.

---

## UC-08: Stream Event

| Attribute | Value |
|---|---|
| **Use Case ID** | UC-08 |
| **Name** | Stream Event |
| **Actors** | Organizer (primary), Attendee (primary), StreamingProvider (external—Zoom/Teams) |
| **Preconditions** | Event is virtual or hybrid. Organizer has connected a streaming provider account. Attendee holds a valid ticket. |
| **Trigger** | Attendee clicks "Join Stream" on the event detail page or in the confirmation email. |

### Main Flow

1. Organizer connects their Zoom or Teams account via OAuth during event setup.
2. System (StreamingService) calls the provider API to create a meeting/webinar with the event schedule.
3. StreamingService stores the meeting ID and generates unique per-attendee join links.
4. On ticket purchase, the unique join link is embedded in the confirmation email.
5. On event day, attendee clicks "Join Stream" in the attendee portal.
6. System validates: ticket is `PAID` and not `REFUNDED`, event is within the stream window.
7. System retrieves the attendee's unique join URL from the database.
8. System redirects the attendee to the StreamingProvider join page.
9. Attendee enters the virtual event via the provider's interface.
10. After the event, StreamingService polls the provider API for attendance data and recording URL.
11. Organizer can share the recording URL with registered attendees if recording is enabled.

### Alternative Flows

**AF-08A — Join Before Event Starts:**
- At step 6, the current time is more than 15 minutes before the event start time.
- System displays: "The stream opens 15 minutes before the event. Please return at [time]."

**AF-08B — Streaming Provider Outage:**
- At step 8, the provider's join URL returns a 5xx error or timeout.
- System detects the failure and displays a status page with the incident details.
- Organizer is notified immediately via email and Slack webhook (if configured).
- System retries the provider API every 2 minutes for 30 minutes.

**AF-08C — Teams Integration:**
- At step 1, organizer selects Microsoft Teams instead of Zoom.
- StreamingService calls the Teams Graph API to create a live event.
- All subsequent steps follow the same flow with Teams-specific URLs.

### Postconditions

- Attendee has joined the virtual event.
- Join event logged with timestamp and attendee ID.
- Recording URL stored (if applicable) and shared with attendees post-event.
