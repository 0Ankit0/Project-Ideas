# User Stories — Slot Booking System

> **Version:** 2.0.0 | **Format:** As a [persona], I want [goal], so that [value]

---

## User Personas

| Persona | Description | Primary Goals |
|---------|-------------|---------------|
| **Guest** | Unauthenticated visitor browsing the platform | Discover resources, check availability, understand pricing |
| **Customer** | Registered end-user making reservations | Book slots, manage reservations, track payment history |
| **Corporate User** | Employee on a corporate account | Book on behalf of company, use corporate quota |
| **Staff** | Venue employee (instructor, receptionist) | View assigned schedule, check in customers |
| **Venue Admin** | Owner or manager of a venue | Configure resources, manage schedules, view revenue |
| **Corporate Admin** | Company account manager | Manage quota, approve excess bookings, view team usage |
| **Platform Admin** | System operator | Configure system rules, handle overrides, view analytics |

---

## Epic 1: Account Management

### US-1.1 — Customer Registration
**As a** guest  
**I want to** create an account with my email or mobile number  
**So that** I can make bookings and receive confirmation notifications

**Acceptance Criteria:**
- Guest registers with email + password (min 10 characters, one uppercase, one digit)
- Guest registers with mobile + OTP (6-digit, valid for 10 minutes)
- Duplicate email or phone rejected with `DUPLICATE_ACCOUNT` error
- Email verification link sent immediately; valid for 24 hours
- Account inactive until email verified

---

### US-1.2 — Social Login
**As a** guest  
**I want to** sign in with my Google or Apple account  
**So that** I can register without managing additional credentials

**Acceptance Criteria:**
- OAuth 2.0 PKCE flow for Google and Apple
- If email already exists, accounts are merged and customer is notified
- Profile fields pre-populated from OAuth provider
- Privacy consent captured before first social login

---

### US-1.3 — Profile Management
**As a** customer  
**I want to** manage my profile, notification preferences, and payment methods  
**So that** my bookings are personalised and payment is frictionless

**Acceptance Criteria:**
- Customer can update name, phone, and address
- Customer can set notification channel preferences (email/SMS/push) per event type
- Customer can view saved payment methods (token only; no PAN stored)
- Customer can view their no-show count and account flag status

---

## Epic 2: Resource Discovery

### US-2.1 — Search Resources
**As a** guest  
**I want to** search for bookable resources by location, type, date, and price  
**So that** I can find the most suitable option for my needs

**Acceptance Criteria:**
- Search by city, venue, resource type, date, time window, and price range
- Results sorted by relevance (default), price, and distance
- Each result shows resource name, venue, next available slot, and starting price
- Filters: amenities, capacity, indoor/outdoor, rating
- Results load in < 300 ms (p95)

---

### US-2.2 — View Resource Detail
**As a** guest  
**I want to** see detailed information about a resource including photos and availability  
**So that** I can make an informed booking decision

**Acceptance Criteria:**
- Resource page shows description, photos (up to 10), amenities, rules, and cancellation policy
- Interactive availability calendar showing available, booked, and blocked slots by day
- Pricing breakdown by time-of-day and day-of-week
- Customer reviews and aggregate rating displayed

---

### US-2.3 — View Real-Time Availability
**As a** customer  
**I want to** see which specific time slots are available for a resource on a selected date  
**So that** I can choose a time that fits my schedule

**Acceptance Criteria:**
- Availability grid shows 30-minute (or configured) increments from venue opening to closing
- Slot states shown: AVAILABLE (green), BOOKED (grey), BLOCKED (red), WAITLIST_ONLY (amber)
- Availability refreshes in real-time when another user books or cancels
- Timezone displayed in venue local time with UTC offset shown

---

## Epic 3: Booking Management

### US-3.1 — Create a Booking
**As a** customer  
**I want to** reserve an available slot and pay online  
**So that** my time is guaranteed at the chosen resource

**Acceptance Criteria:**
- Customer selects resource, date, and time slot
- System validates advance booking window (BR-01); rejects with `BOOKING_WINDOW_VIOLATION` if outside
- System locks slot for 10 minutes during checkout to prevent concurrent booking
- Customer enters or selects saved payment method
- On successful payment capture, booking status moves to `CONFIRMED`
- Confirmation email and SMS sent within 30 seconds

---

### US-3.2 — Book Multiple Consecutive Slots
**As a** customer  
**I want to** book a 2-hour session across two 60-minute slots in a single transaction  
**So that** I am charged correctly and do not risk losing one of the slots

**Acceptance Criteria:**
- Customer selects a start slot and desired total duration
- System automatically selects consecutive available slots for the resource
- All slots reserved atomically; if any slot is unavailable, the request fails
- Single `Booking` record created with two `BookingItem` records
- Combined price shown at checkout

---

### US-3.3 — Set Up Recurring Booking
**As a** customer  
**I want to** book a weekly tennis court session every Saturday at 9 AM for 3 months  
**So that** I have a guaranteed regular slot without rebooking each week

**Acceptance Criteria:**
- Customer configures cadence (WEEKLY), day (Saturday), time (09:00), duration (60 min), and end date
- System validates all occurrences against BR-02 and BR-06 before confirming the series
- Conflicting occurrences identified and returned; entire series rejected if any occurrence conflicts
- Series stored as a `RecurringRule` linked to individual `Booking` records
- Customer can cancel individual occurrences or the entire series
- Payment collected per occurrence on the day of the booking (or all upfront — configurable)

---

### US-3.4 — Cancel a Booking
**As a** customer  
**I want to** cancel a confirmed booking  
**So that** I can free up the slot and receive any applicable refund

**Acceptance Criteria:**
- Customer cancels via booking detail page or mobile app
- System computes refund amount per BR-03 (100% if > 24h; 50% if ≤ 24h; 0% for no-show)
- Refund amount and any penalty clearly shown before confirmation
- Cancellation confirmation email sent with refund ETA (3–5 business days)
- Slot released to availability and waitlist promotion triggered (BR-05)

---

### US-3.5 — Reschedule a Booking
**As a** customer  
**I want to** move my confirmed booking to a different available slot  
**So that** I don't lose my booking when my schedule changes

**Acceptance Criteria:**
- Customer selects "Reschedule" on a confirmed booking
- Availability picker shows valid slots within the same resource
- If new slot is cheaper: partial refund issued; if more expensive: additional charge collected
- Old slot released; new slot reserved atomically
- Confirmation email sent for new booking time

---

### US-3.6 — Join Waitlist
**As a** customer  
**I want to** join the waitlist for a fully-booked slot  
**So that** I automatically get a booking if someone cancels

**Acceptance Criteria:**
- "Join Waitlist" button visible on `WAITLIST_ONLY` or `BOOKED` slots
- Customer sees current queue position
- On promotion (BR-05), customer receives push/email/SMS with 30-minute confirmation link
- If customer does not confirm within 30 minutes, next person in queue is promoted
- Customer can withdraw from waitlist at any time

---

## Epic 4: Staff Workflows

### US-4.1 — View Daily Schedule
**As a** staff member  
**I want to** see my assigned slots for today and tomorrow  
**So that** I know which customers to expect and when

**Acceptance Criteria:**
- Staff dashboard shows chronological list of assigned slots
- Each slot shows customer name, contact, booking details, and special notes
- Status indicators: upcoming, in-progress, completed, no-show
- Mobile-optimised view

---

### US-4.2 — Check In Customer
**As a** staff member  
**I want to** mark a customer as checked in when they arrive  
**So that** the system records attendance and prevents a no-show being recorded

**Acceptance Criteria:**
- Staff taps "Check In" on a confirmed booking
- Booking status moves to `CHECKED_IN`
- No-show background job skips `CHECKED_IN` bookings (BR-09)
- Check-in timestamp recorded; visible to venue admin

---

## Epic 5: Venue Administration

### US-5.1 — Create Resource and Schedule
**As a** venue admin  
**I want to** configure a new tennis court with its schedule and pricing  
**So that** customers can start discovering and booking it

**Acceptance Criteria:**
- Venue admin creates a `ResourceType` (if not existing) with duration rules and overbooking settings
- Creates a `Resource` with name, capacity, amenities, and images
- Creates a `Schedule` defining operating hours and days
- Creates `SlotTemplate` records for peak and off-peak pricing
- System auto-generates slots on the rolling 90-day horizon

---

### US-5.2 — Apply a Block Rule
**As a** venue admin  
**I want to** block bookings on Court A on 2024-12-25 for annual maintenance  
**So that** no customer can make a booking on that day

**Acceptance Criteria:**
- Venue admin creates a `BlockRule` with start/end time, resource scope, and reason
- Existing confirmed bookings in the block window are listed for review
- Admin can choose to cancel affected bookings with full refund and notification
- Blocked periods shown in the availability calendar as unavailable

---

### US-5.3 — View Occupancy Reports
**As a** venue admin  
**I want to** see weekly occupancy rates and revenue by resource  
**So that** I can identify peak hours and optimise pricing

**Acceptance Criteria:**
- Report shows occupancy percentage per resource per hour of day
- Revenue breakdown by resource, payment method, and booking channel
- No-show and cancellation rates per resource
- Date range filter (up to 12 months); exportable to CSV

---

## Epic 6: Platform Administration

### US-6.1 — Apply Manual Override
**As a** platform admin  
**I want to** override the advance booking window rule for a VIP customer  
**So that** I can honour a last-minute executive request

**Acceptance Criteria:**
- Admin calls `POST /admin/overrides` with `booking_id`, `rule_id`, `reason`, and `approver_id`
- Override is recorded in `AuditEvent` with full detail
- Override applies for a single booking only (single-use)
- Alert raised if > 5 overrides of the same rule in 30 days

---

### US-6.2 — Declare Force Majeure
**As a** platform admin  
**I want to** declare a force majeure event affecting all bookings at a flooded venue  
**So that** affected customers are automatically refunded and notified

**Acceptance Criteria:**
- Admin triggers force-majeure declaration for a venue and date range via admin console
- All confirmed bookings in scope cancelled with `FORCE_MAJEURE` reason
- Full refunds issued regardless of cancellation policy
- Mass notification sent to affected customers within 15 minutes
- Affected no-shows excluded from BR-09 rolling count
