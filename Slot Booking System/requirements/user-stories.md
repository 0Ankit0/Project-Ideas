# User Stories - Slot Booking System

> **Platform Independence Notice**: Stories use generic terminology. 
> - **Resource** → Futsal Court, Room, Station, etc.
> - **Provider** → Venue Owner, Facility Manager, etc.

---

## User Personas

| Persona | Description | Goals |
|---------|-------------|-------|
| **Guest** | Unregistered visitor | Browse resources, view availability |
| **User** | Registered customer | Book slots, manage bookings |
| **Provider** | Resource owner/manager | List resources, manage bookings, earnings |
| **Admin** | Platform administrator | System config, user management, analytics |

---

## Epic 1: User Registration & Authentication

### US-1.1: User Registration
**As a** guest  
**I want to** create an account with my email or phone  
**So that** I can book slots and track my reservations

**Acceptance Criteria:**
- [ ] Guest can register with email + password
- [ ] Guest can register with phone + OTP
- [ ] Email verification is required before booking
- [ ] Password meets security requirements (8+ chars, mixed case, number)
- [ ] Duplicate email/phone is rejected with clear message

---

### US-1.2: Social Login
**As a** guest  
**I want to** sign up using my Google/Facebook/Apple account  
**So that** I can register quickly without creating new credentials

**Acceptance Criteria:**
- [ ] OAuth buttons displayed on registration page
- [ ] Profile info pre-filled from social account
- [ ] Account linked if email already exists
- [ ] Privacy consent shown before social login

---

### US-1.3: User Login
**As a** registered user  
**I want to** log in to my account  
**So that** I can access my bookings and profile

**Acceptance Criteria:**
- [ ] Login with email/phone + password
- [ ] Login with social accounts
- [ ] "Remember me" option persists session
- [ ] Failed login shows generic error (security)
- [ ] Account lockout after 5 failed attempts

---

### US-1.4: Password Reset
**As a** user who forgot my password  
**I want to** reset my password via email  
**So that** I can regain access to my account

**Acceptance Criteria:**
- [ ] Reset link sent to registered email
- [ ] Link expires after 1 hour
- [ ] User must set new password meeting requirements
- [ ] All sessions invalidated after reset

---

## Epic 2: Resource Discovery

### US-2.1: Browse Resources
**As a** user  
**I want to** browse available resources by category and location  
**So that** I can find what I'm looking for

**Acceptance Criteria:**
- [ ] Resources displayed in list/grid view
- [ ] Filter by category, location, price range
- [ ] Sort by price, rating, distance
- [ ] Pagination/infinite scroll for large results
- [ ] Resource cards show image, name, rating, price

---

### US-2.2: Search Resources
**As a** user  
**I want to** search for resources by name or keyword  
**So that** I can quickly find specific resources

**Acceptance Criteria:**
- [ ] Search bar prominently displayed
- [ ] Auto-suggest as user types
- [ ] Search by name, description, amenities
- [ ] Recent searches saved
- [ ] "No results" shows suggestions

---

### US-2.3: View Resource Details
**As a** user  
**I want to** view detailed information about a resource  
**So that** I can decide whether to book it

**Acceptance Criteria:**
- [ ] Photo gallery (multiple images)
- [ ] Description and amenities list
- [ ] Location with map
- [ ] Operating hours
- [ ] Pricing information
- [ ] Reviews and ratings
- [ ] Availability calendar preview

---

### US-2.4: View Availability
**As a** user  
**I want to** see available time slots for a specific date  
**So that** I can choose when to book

**Acceptance Criteria:**
- [ ] Calendar date picker
- [ ] Available slots shown with times
- [ ] Unavailable slots grayed out
- [ ] Price shown per slot
- [ ] Real-time availability updates

---

## Epic 3: Booking Management

### US-3.1: Book a Slot
**As a** user  
**I want to** book an available slot  
**So that** I can reserve the resource for my use

**Acceptance Criteria:**
- [ ] Select date and time slot
- [ ] Review booking summary (resource, time, price)
- [ ] Add optional notes
- [ ] Proceed to payment
- [ ] Confirmation displayed after payment
- [ ] Confirmation email/notification sent

---

### US-3.2: Book Multiple Slots
**As a** user  
**I want to** book multiple consecutive slots in one transaction  
**So that** I can reserve extended time

**Acceptance Criteria:**
- [ ] Select multiple adjacent slots
- [ ] Total price calculated correctly
- [ ] Discount for extended booking (if applicable)
- [ ] Single payment for all slots

---

### US-3.3: View My Bookings
**As a** user  
**I want to** view my upcoming and past bookings  
**So that** I can manage my schedule

**Acceptance Criteria:**
- [ ] Tabs for upcoming/past bookings
- [ ] Booking cards show resource, date, time, status
- [ ] Quick actions (cancel, reschedule, view details)
- [ ] Calendar view option
- [ ] Download/share booking confirmation

---

### US-3.4: Cancel Booking
**As a** user  
**I want to** cancel my booking  
**So that** I can free up the slot if plans change

**Acceptance Criteria:**
- [ ] Cancel button on booking details
- [ ] Cancellation policy clearly displayed
- [ ] Refund amount shown before confirmation
- [ ] Confirmation required before cancellation
- [ ] Refund processed per policy
- [ ] Cancellation notification sent

---

### US-3.5: Reschedule Booking
**As a** user  
**I want to** reschedule my booking to a different time  
**So that** I can adjust to schedule changes

**Acceptance Criteria:**
- [ ] Reschedule option on booking details
- [ ] Show available alternative slots
- [ ] Price difference handled (pay more or partial refund)
- [ ] Original slot freed immediately
- [ ] New confirmation sent

---

### US-3.6: Recurring Booking
**As a** user  
**I want to** set up a recurring booking (weekly/monthly)  
**So that** I don't have to book the same slot repeatedly

**Acceptance Criteria:**
- [ ] Recurring option during booking
- [ ] Set frequency (daily, weekly, monthly)
- [ ] Set end date or number of occurrences
- [ ] View all recurring instances
- [ ] Cancel single instance or entire series

---

## Epic 4: Payment

### US-4.1: Make Payment
**As a** user  
**I want to** pay for my booking securely  
**So that** my reservation is confirmed

**Acceptance Criteria:**
- [ ] Multiple payment methods (card, wallet, UPI)
- [ ] Secure payment form (PCI compliant)
- [ ] Order summary with price breakdown
- [ ] Payment processing indicator
- [ ] Success/failure feedback
- [ ] Receipt emailed

---

### US-4.2: Apply Promo Code
**As a** user  
**I want to** apply a promotional code  
**So that** I can get a discount on my booking

**Acceptance Criteria:**
- [ ] Promo code input field
- [ ] Validation with clear error messages
- [ ] Discount applied and shown in summary
- [ ] Code restrictions enforced (min amount, dates)

---

### US-4.3: View Payment History
**As a** user  
**I want to** view my payment history  
**So that** I can track my expenses

**Acceptance Criteria:**
- [ ] List of all transactions
- [ ] Transaction details (amount, date, status)
- [ ] Download invoice/receipt
- [ ] Filter by date range

---

## Epic 5: Notifications

### US-5.1: Booking Reminders
**As a** user  
**I want to** receive reminders before my booking  
**So that** I don't forget my appointments

**Acceptance Criteria:**
- [ ] Reminder 24 hours before
- [ ] Reminder 1 hour before
- [ ] Push notification and email
- [ ] Reminder includes booking details and location

---

### US-5.2: Notification Preferences
**As a** user  
**I want to** manage my notification settings  
**So that** I only receive relevant notifications

**Acceptance Criteria:**
- [ ] Toggle for each notification type
- [ ] Choose channel (email, push, SMS)
- [ ] Set quiet hours
- [ ] Save preferences

---

## Epic 6: Reviews & Ratings

### US-6.1: Rate and Review
**As a** user who completed a booking  
**I want to** rate and review the resource  
**So that** I can share my experience with others

**Acceptance Criteria:**
- [ ] Rating prompt after booking completion
- [ ] 1-5 star rating
- [ ] Optional text review
- [ ] Photo upload option
- [ ] Review visible on resource page

---

### US-6.2: View Reviews
**As a** user  
**I want to** read reviews from other users  
**So that** I can make informed booking decisions

**Acceptance Criteria:**
- [ ] Reviews displayed on resource page
- [ ] Average rating shown prominently
- [ ] Sort by recent, highest, lowest
- [ ] Provider responses visible
- [ ] Mark reviews as helpful

---

## Epic 7: Provider Management

### US-7.1: Provider Registration
**As a** resource owner  
**I want to** register as a provider  
**So that** I can list my resources on the platform

**Acceptance Criteria:**
- [ ] Provider registration form
- [ ] Business verification process
- [ ] Bank account for payouts
- [ ] Terms acceptance required
- [ ] Admin approval workflow

---

### US-7.2: Add Resource
**As a** provider  
**I want to** add my resources to the platform  
**So that** users can book them

**Acceptance Criteria:**
- [ ] Resource creation form
- [ ] Upload multiple images
- [ ] Set description and amenities
- [ ] Set location with map picker
- [ ] Define pricing rules
- [ ] Set availability schedule

---

### US-7.3: Manage Availability
**As a** provider  
**I want to** set and update my resource availability  
**So that** slots are only shown when the resource is available

**Acceptance Criteria:**
- [ ] Weekly schedule template
- [ ] Override specific dates
- [ ] Block time for maintenance
- [ ] Holiday schedule
- [ ] Bulk availability updates

---

### US-7.4: View Bookings Calendar
**As a** provider  
**I want to** see all my bookings in a calendar view  
**So that** I can manage my schedule

**Acceptance Criteria:**
- [ ] Day/week/month calendar views
- [ ] All resources in single view (color-coded)
- [ ] Click booking for details
- [ ] Quick actions (cancel, contact user)
- [ ] Export calendar (iCal)

---

### US-7.5: View Earnings
**As a** provider  
**I want to** view my earnings and payouts  
**So that** I can track my revenue

**Acceptance Criteria:**
- [ ] Earnings dashboard
- [ ] Breakdown by resource
- [ ] Pending vs completed payouts
- [ ] Transaction history
- [ ] Download statements

---

### US-7.6: Respond to Reviews
**As a** provider  
**I want to** respond to user reviews  
**So that** I can address feedback publicly

**Acceptance Criteria:**
- [ ] Reply option on each review
- [ ] One response per review
- [ ] Response visible to all users
- [ ] Notification when new review received

---

## Epic 8: Admin Management

### US-8.1: User Management
**As an** admin  
**I want to** manage user accounts  
**So that** I can maintain platform integrity

**Acceptance Criteria:**
- [ ] View all users with filters
- [ ] Suspend/activate accounts
- [ ] View user activity history
- [ ] Reset user passwords
- [ ] Delete accounts (GDPR)

---

### US-8.2: Provider Approval
**As an** admin  
**I want to** review and approve provider applications  
**So that** only legitimate providers are on the platform

**Acceptance Criteria:**
- [ ] Queue of pending applications
- [ ] View verification documents
- [ ] Approve/reject with notes
- [ ] Notification to provider

---

### US-8.3: Platform Analytics
**As an** admin  
**I want to** view platform-wide analytics  
**So that** I can monitor business performance

**Acceptance Criteria:**
- [ ] Dashboard with KPIs
- [ ] Bookings over time
- [ ] Revenue metrics
- [ ] User growth
- [ ] Top resources/providers
- [ ] Export reports

---

### US-8.4: Handle Disputes
**As an** admin  
**I want to** manage booking disputes  
**So that** I can resolve user/provider conflicts

**Acceptance Criteria:**
- [ ] View reported disputes
- [ ] Communication with both parties
- [ ] Issue full/partial refunds
- [ ] Apply penalties to violators
- [ ] Resolution documentation

---

## Story Map Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER JOURNEY                                    │
├─────────────┬─────────────┬─────────────┬─────────────┬─────────────────────┤
│   DISCOVER  │    BOOK     │     PAY     │    USE      │      REVIEW         │
├─────────────┼─────────────┼─────────────┼─────────────┼─────────────────────┤
│ US-2.1      │ US-3.1      │ US-4.1      │ US-5.1      │ US-6.1              │
│ Browse      │ Book Slot   │ Make Payment│ Reminders   │ Rate & Review       │
├─────────────┼─────────────┼─────────────┼─────────────┼─────────────────────┤
│ US-2.2      │ US-3.2      │ US-4.2      │ US-5.2      │ US-6.2              │
│ Search      │ Multi-Slot  │ Promo Code  │ Preferences │ View Reviews        │
├─────────────┼─────────────┼─────────────┼─────────────┼─────────────────────┤
│ US-2.3      │ US-3.3      │ US-4.3      │             │                     │
│ View Details│ My Bookings │ Pay History │             │                     │
├─────────────┼─────────────┼─────────────┼─────────────┼─────────────────────┤
│ US-2.4      │ US-3.4      │             │             │                     │
│ Availability│ Cancel      │             │             │                     │
├─────────────┼─────────────┼─────────────┼─────────────┼─────────────────────┤
│             │ US-3.5      │             │             │                     │
│             │ Reschedule  │             │             │                     │
├─────────────┼─────────────┼─────────────┼─────────────┼─────────────────────┤
│             │ US-3.6      │             │             │                     │
│             │ Recurring   │             │             │                     │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────────────────┘
```

---

## Priority Matrix (MoSCoW)

| Must Have | Should Have | Could Have | Won't Have (v1) |
|-----------|-------------|------------|-----------------|
| US-1.1, 1.3, 1.4 | US-1.2 | US-3.6 | Social features |
| US-2.1, 2.3, 2.4 | US-2.2 | US-6.2 | Live chat |
| US-3.1, 3.3, 3.4 | US-3.2, 3.5 | US-4.2 | Marketplace |
| US-4.1 | US-4.3 | | |
| US-5.1 | US-5.2 | | |
| US-7.1, 7.2, 7.3, 7.4, 7.5 | US-7.6 | | |
| US-8.1, 8.2, 8.3 | US-8.4 | | |
