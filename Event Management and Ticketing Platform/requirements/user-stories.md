# User Stories — Event Management and Ticketing Platform

## Overview

This document captures all user stories grouped by epic. Each story follows the standard format with acceptance criteria to guide implementation and QA.

---

## Epic 1: Event Organizer

**US-001**: As an organizer, I want to create a new event with a title, description, dates, and category so that I can publish it to potential attendees.
**Acceptance Criteria:**
- [ ] Form validates required fields: title, start date, end date, category, organizer name
- [ ] Organizer can select event type: in-person, virtual, or hybrid
- [ ] Draft is auto-saved every 30 seconds
- [ ] Event cannot have an end date before start date
- [ ] System generates a unique slug from the event title

**US-002**: As an organizer, I want to build a venue seat map with sections, rows, and individual seats so that I can assign ticket types to specific seats.
**Acceptance Criteria:**
- [ ] Drag-and-drop canvas allows placing sections on a floor plan
- [ ] Each section has configurable row count and seats per row
- [ ] Seats can be marked as accessible (wheelchair), premium, or restricted view
- [ ] Organizer can import a venue template or start from scratch
- [ ] Published seat map is locked from structural edits once tickets go on sale

**US-003**: As an organizer, I want to define multiple ticket types (e.g., VIP, General Admission, Early Bird) with distinct prices and quantities so that I can cater to different attendee segments.
**Acceptance Criteria:**
- [ ] Each ticket type has a name, description, price, quantity, and sale window
- [ ] VIP tickets can include perks (lounge access, priority entry)
- [ ] Early Bird tickets automatically deactivate after a specified date or quantity
- [ ] Organizer can set a per-order minimum and maximum per ticket type
- [ ] Hidden ticket types visible only via direct link are supported

**US-004**: As an organizer, I want to configure dynamic pricing rules so that ticket prices adjust automatically based on demand or time remaining.
**Acceptance Criteria:**
- [ ] Organizer can set price tiers that activate at specified inventory thresholds (e.g., price increases after 50% sold)
- [ ] Time-based pricing rules can increase prices as the event date approaches
- [ ] Dynamic pricing changes are logged with timestamp and trigger reason
- [ ] Attendees see the current price without historical pricing information
- [ ] Organizer receives a notification when a pricing tier activates

**US-005**: As an organizer, I want to create presale campaigns with unique access codes so that I can reward loyal attendees before public sale opens.
**Acceptance Criteria:**
- [ ] Presale period has configurable start and end times independent of general sale
- [ ] Each presale requires an access code to unlock ticket purchase
- [ ] Access codes can be single-use or multi-use with an optional cap
- [ ] Presale inventory is drawn from the same pool as general sale
- [ ] Organizer can view presale conversion statistics

**US-006**: As an organizer, I want to create and manage promo codes offering percentage or fixed discounts so that I can run promotions and partnerships.
**Acceptance Criteria:**
- [ ] Promo codes support: percentage discount, fixed amount, free ticket
- [ ] Codes can have an expiry date, usage limit, and minimum order value
- [ ] Codes can be restricted to specific ticket types
- [ ] Organizer dashboard shows code usage count and total discount value
- [ ] Expired or exhausted codes return a clear error to the attendee

**US-007**: As an organizer, I want to manage a waitlist for sold-out events so that I can automatically offer tickets to waitlisted attendees when spots open up.
**Acceptance Criteria:**
- [ ] Waitlist is activated per ticket type when inventory reaches zero
- [ ] Waitlisted attendees receive an email when a spot becomes available
- [ ] Attendees have a configurable time window (e.g., 24 hours) to claim the ticket
- [ ] Unclaimed spots cascade to the next person on the waitlist
- [ ] Organizer can manually promote waitlisted attendees

**US-008**: As an organizer, I want to publish the event and manage its visibility (draft, published, private, cancelled) so that I have full control over the event lifecycle.
**Acceptance Criteria:**
- [ ] State transitions are: Draft → Published, Draft → Cancelled, Published → Cancelled
- [ ] Private events are only accessible via a direct link
- [ ] Cancellation triggers automated notification to all ticket holders
- [ ] Cancelled events display a banner with refund information
- [ ] Organizer cannot unpublish an event that has active ticket sales

**US-009**: As an organizer, I want to add speakers to an event with their bio, photo, and session details so that attendees know who is presenting.
**Acceptance Criteria:**
- [ ] Speaker profile includes: name, title, company, bio (up to 500 characters), headshot, social links
- [ ] Speakers can be linked to specific sessions in the event schedule
- [ ] Speaker profiles are publicly visible on the event page
- [ ] Organizer can invite a speaker who self-completes their own profile via a unique link
- [ ] Duplicate speaker entries are flagged

**US-010**: As an organizer, I want to manage sponsor packages and display sponsor branding on the event page and badges so that sponsors receive their promised visibility.
**Acceptance Criteria:**
- [ ] Sponsor tiers (Gold, Silver, Bronze) have configurable benefits
- [ ] Sponsor logo appears on event page, confirmation emails, and badge templates
- [ ] Sponsor data includes: company name, tier, logo URL, website, contact person
- [ ] Organizer can upload sponsor logos in SVG or PNG format
- [ ] Sponsors are rendered in tier order on the event page

**US-011**: As an organizer, I want to configure streaming integration (Zoom or Microsoft Teams) for virtual or hybrid events so that online attendees can join remotely.
**Acceptance Criteria:**
- [ ] Organizer connects their Zoom/Teams account via OAuth
- [ ] Unique meeting link is generated per attendee upon ticket purchase
- [ ] Meeting links are included in confirmation emails and the attendee portal
- [ ] Organizer can test the stream link before event day
- [ ] Recording settings (if enabled) are configurable per event

**US-012**: As an organizer, I want to define a refund policy per event so that attendees know the terms before purchasing.
**Acceptance Criteria:**
- [ ] Refund policies include: full refund, partial refund (percentage), no refund
- [ ] Policy can specify a deadline (e.g., no refunds within 48 hours of event)
- [ ] Policy is displayed prominently during checkout
- [ ] If the organizer cancels the event, automatic full refund is applied regardless of policy
- [ ] Attendees receive an email with refund details upon cancellation

**US-013**: As an organizer, I want to configure the badge template for an event so that printed badges include attendee name, ticket type, QR code, and sponsor logos.
**Acceptance Criteria:**
- [ ] Badge editor supports drag-and-drop layout for fields
- [ ] Standard fields: attendee name, ticket type, company, QR code, event logo
- [ ] Badge size defaults to A6 landscape (105×148 mm) with custom size option
- [ ] Preview renders with sample data before saving
- [ ] Badge template can be duplicated across event editions

**US-014**: As an organizer, I want to view real-time event analytics (ticket sales, revenue, check-in rate) so that I can monitor event performance.
**Acceptance Criteria:**
- [ ] Dashboard updates at most 60 seconds behind real time
- [ ] Metrics shown: tickets sold, gross revenue, net revenue (after fees), check-in count
- [ ] Revenue chart is broken down by ticket type
- [ ] Organizer can export data as CSV
- [ ] Analytics are restricted to the organizer's own events

**US-015**: As an organizer, I want to manage organizer payouts so that I receive event revenue minus platform fees in a timely manner.
**Acceptance Criteria:**
- [ ] Payout is initiated T+2 business days after the event ends
- [ ] Payout amount equals gross ticket revenue minus platform fee and payment processing fee
- [ ] Organizer sees a detailed fee breakdown before payout
- [ ] Payout supports: bank transfer (ACH/SEPA), PayPal
- [ ] Organizer receives a payout confirmation email and downloadable invoice

**US-016**: As an organizer, I want to create event editions (e.g., annual conferences) under a parent event so that I can manage recurring events with shared settings.
**Acceptance Criteria:**
- [ ] An event can have multiple editions (e.g., "TechConf 2024", "TechConf 2025")
- [ ] Settings (refund policy, badge template, sponsors) can be inherited from parent or overridden
- [ ] Attendee history is preserved across editions
- [ ] Edition-specific analytics are available alongside aggregate stats
- [ ] Editions share the same event page URL structure

---

## Epic 2: Attendee

**US-017**: As an attendee, I want to discover events by category, date, location, or keyword so that I can find events that interest me.
**Acceptance Criteria:**
- [ ] Search supports: keyword, city, date range, category filter
- [ ] Results are paginated (20 per page) and sortable by date or relevance
- [ ] Each result card shows: event name, date, location, price range, available tickets
- [ ] Free events are labelled "Free"
- [ ] Virtual events are labelled "Online"

**US-018**: As an attendee, I want to view full event details (schedule, speakers, venue map, ticket types) so that I can make an informed purchase decision.
**Acceptance Criteria:**
- [ ] Event detail page renders within 2 seconds (p95)
- [ ] Schedule shows sessions with speaker names and times
- [ ] Interactive seat map shows available, reserved, and sold seats
- [ ] Ticket prices and remaining quantities are shown
- [ ] Page is mobile-responsive

**US-019**: As an attendee, I want to select seats on an interactive venue map and add tickets to a cart so that I can choose my preferred location.
**Acceptance Criteria:**
- [ ] Available seats are shown in green; reserved in grey; selected in blue
- [ ] Selected seats are held for 10 minutes during checkout
- [ ] Cart shows seat number, section, row, ticket type, and price
- [ ] Attendee can deselect a seat before proceeding to checkout
- [ ] Cart persists across page refreshes for the same session

**US-020**: As an attendee, I want to apply a promo code at checkout to receive a discount so that I can benefit from promotions.
**Acceptance Criteria:**
- [ ] Promo code field is visible on the order summary step
- [ ] Valid code shows the discount amount applied in real time
- [ ] Invalid or expired codes display a specific error message
- [ ] Only one promo code can be applied per order
- [ ] Discount is reflected in the final payment amount

**US-021**: As an attendee, I want to pay securely for my tickets using a credit card, debit card, or digital wallet so that I can complete my purchase.
**Acceptance Criteria:**
- [ ] Payment form is PCI DSS compliant (hosted fields via Stripe)
- [ ] Supported methods: Visa, Mastercard, Amex, Apple Pay, Google Pay
- [ ] Payment is processed within 5 seconds under normal conditions
- [ ] Failed payment shows a clear error without losing cart contents
- [ ] Successful payment redirects to a confirmation page

**US-022**: As an attendee, I want to receive a digital ticket (QR code) via email immediately after purchase so that I can access the event.
**Acceptance Criteria:**
- [ ] Confirmation email is sent within 60 seconds of successful payment
- [ ] Email contains: event details, ticket type, QR code image, and download link
- [ ] QR code is unique per attendee and encodes the ticket ID and check-in token
- [ ] Attendee can view and download tickets from their profile
- [ ] PDF ticket can be saved to Apple Wallet / Google Wallet

**US-023**: As an attendee, I want to join the waitlist for a sold-out event so that I am notified if a ticket becomes available.
**Acceptance Criteria:**
- [ ] Waitlist button replaces "Buy Tickets" when event is sold out
- [ ] Attendee provides email address and optionally a phone number
- [ ] Waitlist position is shown to the attendee
- [ ] Attendee can remove themselves from the waitlist at any time
- [ ] Waitlist entries expire 7 days after the event date

**US-024**: As an attendee, I want to request a refund for my ticket according to the event's refund policy so that I can recover my payment if plans change.
**Acceptance Criteria:**
- [ ] Refund request is available from the attendee's order page
- [ ] System checks the refund policy and eligibility before allowing the request
- [ ] Ineligible refunds show the policy reason clearly
- [ ] Eligible refunds are processed within 5–10 business days
- [ ] Attendee receives a refund confirmation email with the amount

**US-025**: As an attendee, I want to transfer my ticket to another person so that someone else can attend if I cannot.
**Acceptance Criteria:**
- [ ] Transfer requires: recipient's email address and name
- [ ] Recipient receives a new QR code; the original is invalidated
- [ ] Organizer can disable transfers on a per-event basis
- [ ] Transfer is not allowed within 2 hours of the event start
- [ ] Transfer history is logged for audit

**US-026**: As an attendee, I want to access a self-service portal to view all my upcoming and past events so that I can manage my event participation.
**Acceptance Criteria:**
- [ ] Portal shows: upcoming events, past events, cancelled orders
- [ ] Each entry shows ticket type, order ID, payment amount, and status
- [ ] Attendee can download invoices for past purchases
- [ ] Portal is accessible on mobile and desktop
- [ ] Attendee can update their profile (name, company, dietary preferences)

**US-027**: As an attendee, I want to receive event reminders (email and SMS) before the event so that I do not forget to attend.
**Acceptance Criteria:**
- [ ] Reminder sent 7 days before event (email)
- [ ] Reminder sent 24 hours before event (email + optional SMS)
- [ ] Reminders include: event name, location/join link, QR code, parking information
- [ ] Attendee can opt out of reminders per event
- [ ] SMS requires explicit opt-in at checkout

**US-028**: As an attendee, I want to add an event to my calendar (Google Calendar, Apple Calendar, Outlook) so that it appears in my schedule.
**Acceptance Criteria:**
- [ ] "Add to Calendar" button appears on the confirmation page and in the email
- [ ] Supports: .ics file download, Google Calendar link, Outlook Web link
- [ ] Calendar entry includes: event name, date/time, location (or join link), organizer contact
- [ ] Virtual event calendar entries include the meeting join URL
- [ ] Calendar entries handle timezone correctly based on attendee's locale

---

## Epic 3: Check-in Staff

**US-029**: As a check-in staff member, I want to scan an attendee's QR code using a mobile device so that I can quickly verify their ticket and grant entry.
**Acceptance Criteria:**
- [ ] QR scanner works on iOS and Android via the Check-in app (PWA)
- [ ] Scan result is displayed within 1 second (online) or 3 seconds (offline)
- [ ] Valid ticket shows a green screen with attendee name and ticket type
- [ ] Invalid or already-used ticket shows a red screen with reason
- [ ] All scan events are logged with timestamp and staff member ID

**US-030**: As a check-in staff member, I want to manually search for an attendee by name or order ID so that I can assist attendees who cannot display their QR code.
**Acceptance Criteria:**
- [ ] Search by: first name, last name, email, or order number
- [ ] Results show ticket status (not checked in / checked in / cancelled)
- [ ] Staff can manually check in an attendee with a reason note
- [ ] Manual check-in is logged separately from QR scan check-in
- [ ] Search works offline with the last synced data set

**US-031**: As a check-in staff member, I want to print an on-demand badge for an attendee at the venue so that attendees who forgot their badge can still participate.
**Acceptance Criteria:**
- [ ] Badge print is triggered from the attendee's check-in record
- [ ] Badge includes: name, company, ticket type, QR code, event branding
- [ ] Print job is sent to a configured network printer
- [ ] Staff sees a print success/failure status on screen
- [ ] Reprint is possible with a reason log entry

**US-032**: As a check-in staff member, I want to view a live dashboard of check-in counts per session so that I can manage crowd flow.
**Acceptance Criteria:**
- [ ] Dashboard shows: total registered, checked in, pending, and no-shows
- [ ] Filter by: ticket type, session, time slot
- [ ] Dashboard refreshes every 10 seconds automatically
- [ ] Staff can export the current check-in list as CSV
- [ ] Dashboard is accessible on tablet and laptop screens

---

## Epic 4: Finance / Admin

**US-033**: As a finance admin, I want to review all organizer payout requests and approve or reject them so that I can ensure accurate revenue distribution.
**Acceptance Criteria:**
- [ ] Payout queue lists: organizer name, event name, gross revenue, fee deductions, net payout
- [ ] Admin can view itemised transaction detail for each payout
- [ ] Approved payouts are initiated to the payment provider within 1 business day
- [ ] Rejected payouts trigger an email to the organizer with the reason
- [ ] Payout records are immutable once approved

**US-034**: As a finance admin, I want to configure platform fee structures (flat fee, percentage, or hybrid) per organizer tier so that platform revenue is correctly calculated.
**Acceptance Criteria:**
- [ ] Fee configuration supports: per-ticket flat fee, percentage of ticket price, or both
- [ ] Fee profiles can be assigned to individual organizers or organizer tiers
- [ ] Fee changes are prospective (do not affect existing orders)
- [ ] Fee preview tool shows impact on example order values
- [ ] All fee changes are audit-logged with admin user and timestamp

**US-035**: As a finance admin, I want to generate financial reports (revenue, refunds, payouts, fees) for any date range so that I can reconcile accounts.
**Acceptance Criteria:**
- [ ] Reports available: gross revenue, net revenue, refund totals, fee income, payout totals
- [ ] Filters: date range, organizer, event, currency, payment method
- [ ] Reports export in CSV and PDF formats
- [ ] Reports show multi-currency breakdown with exchange rates used
- [ ] Scheduled report delivery to email is configurable

**US-036**: As a finance admin, I want to process refunds on behalf of an attendee so that I can resolve disputes escalated from customer support.
**Acceptance Criteria:**
- [ ] Admin can override the event's refund policy in exceptional cases
- [ ] Override requires a mandatory reason field
- [ ] Refund amount is customisable (partial or full)
- [ ] Admin override is logged in the audit trail
- [ ] Attendee receives the refund confirmation email

---

## Epic 5: Platform Admin

**US-037**: As a platform admin, I want to review and approve new organizer accounts so that only legitimate organisers can publish events.
**Acceptance Criteria:**
- [ ] New organiser accounts are placed in a "Pending Approval" state
- [ ] Admin reviews: business name, tax ID, contact details, and website
- [ ] Approval or rejection triggers an email notification to the organiser
- [ ] Rejected accounts can be re-applied after 30 days
- [ ] Admin can flag accounts for further KYC/verification

**US-038**: As a platform admin, I want to manage event categories (create, edit, deactivate) so that events are properly classified.
**Acceptance Criteria:**
- [ ] Categories support a two-level hierarchy (parent → sub-category)
- [ ] Deactivated categories cannot be selected for new events
- [ ] Existing events retain their category if it is deactivated
- [ ] Category names are unique within the same level
- [ ] Categories have an optional icon and colour code for the UI

**US-039**: As a platform admin, I want to view a system health dashboard (API latency, error rates, queue depths) so that I can identify and respond to incidents.
**Acceptance Criteria:**
- [ ] Dashboard shows: API p50/p95/p99 latency, error rate (5xx), Kafka consumer lag
- [ ] Alerts trigger when error rate exceeds 1% over a 5-minute window
- [ ] Service dependency map is visible with live health status
- [ ] Metrics are retained for 90 days
- [ ] Dashboard is role-restricted to admin users

**US-040**: As a platform admin, I want to manage tax rate configurations per jurisdiction so that the correct tax is applied to ticket purchases.
**Acceptance Criteria:**
- [ ] Tax rates are configurable per country and state/province
- [ ] Tax rate includes: rate percentage, tax name (VAT, GST, sales tax), effective date
- [ ] Future-dated rate changes are scheduled and auto-applied
- [ ] Tax calculation supports both inclusive and exclusive pricing
- [ ] Tax amounts are shown separately in invoices

**US-041**: As a platform admin, I want to temporarily suspend an event or an organiser account so that I can act on policy violations quickly.
**Acceptance Criteria:**
- [ ] Suspension disables the event page and halts ticket sales immediately
- [ ] Suspended events show a "Not available" message to attendees
- [ ] Active orders are preserved; no automatic refunds on suspension
- [ ] Suspension includes a mandatory reason and optional public message
- [ ] Admin can lift the suspension and restore the event to its previous state

**US-042**: As a platform admin, I want to configure global email and SMS notification templates so that all transactional communications are consistent.
**Acceptance Criteria:**
- [ ] Template editor supports Markdown/HTML with variable placeholders
- [ ] Variables include: attendee_name, event_name, event_date, ticket_type, qr_code_url
- [ ] Preview renders with sample data before saving
- [ ] Template changes are versioned; rollback to previous version is possible
- [ ] Templates are available in multiple languages (at minimum English and Spanish)
