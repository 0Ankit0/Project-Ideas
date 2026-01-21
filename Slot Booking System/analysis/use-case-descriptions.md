# Use Case Descriptions - Slot Booking System

> **Platform Independence**: Descriptions use generic terminology adaptable to any booking domain.

---

## UC-01: Register Account

| Field | Description |
|-------|-------------|
| **Use Case ID** | UC-01 |
| **Name** | Register Account |
| **Actor** | Guest |
| **Description** | Guest creates a new user account to access booking features |
| **Preconditions** | Guest is not logged in |
| **Postconditions** | New user account created; verification email sent |

### Main Flow
1. Guest navigates to registration page
2. Guest enters email, password, and profile information
3. System validates input data
4. System creates user account (inactive)
5. System sends verification email
6. Guest clicks verification link
7. System activates account
8. System redirects to login page

### Alternative Flows
- **3a. Social Registration**: Guest clicks social login → System fetches profile from OAuth provider → Continue from step 4
- **3b. Phone Registration**: Guest enters phone number → System sends OTP → Guest enters OTP → Continue from step 4

### Exception Flows
- **3e1. Invalid Email**: System displays error "Invalid email format"
- **3e2. Duplicate Email**: System displays error "Account already exists"
- **3e3. Weak Password**: System displays password requirements

---

## UC-02: Login

| Field | Description |
|-------|-------------|
| **Use Case ID** | UC-02 |
| **Name** | Login |
| **Actor** | User, Provider, Admin |
| **Description** | User authenticates to access their account |
| **Preconditions** | User has a verified account |
| **Postconditions** | User session created; user redirected to dashboard |

### Main Flow
1. User navigates to login page
2. User enters email/phone and password
3. System validates credentials
4. System creates session
5. System redirects to appropriate dashboard based on role

### Alternative Flows
- **2a. Social Login**: User clicks social login button → OAuth flow → Continue from step 4
- **2b. Remember Me**: System creates persistent session token

### Exception Flows
- **3e1. Invalid Credentials**: System displays error "Invalid email or password"
- **3e2. Account Locked**: System displays "Account locked. Try again in 30 minutes"
- **3e3. Account Not Verified**: System prompts to resend verification email

---

## UC-03: Book Slot

| Field | Description |
|-------|-------------|
| **Use Case ID** | UC-03 |
| **Name** | Book Slot |
| **Actor** | User |
| **Description** | User reserves an available time slot for a resource |
| **Preconditions** | User is logged in; slot is available |
| **Postconditions** | Booking created; payment processed; confirmation sent |

### Main Flow
1. User views resource details page
2. User selects date from calendar
3. System displays available slots
4. User selects desired slot(s)
5. System displays booking summary with price
6. User confirms booking details
7. System redirects to payment (UC-04)
8. User completes payment
9. System creates booking record
10. System sends confirmation notification
11. System displays booking confirmation

### Alternative Flows
- **4a. Multiple Slots**: User selects multiple consecutive slots → System calculates total → Continue from step 5
- **6a. Add Notes**: User adds special instructions → Continue from step 7
- **6b. Apply Promo**: User enters promo code → System validates and applies discount → Continue from step 7

### Exception Flows
- **4e1. Slot No Longer Available**: System displays "Slot was just booked" → Return to step 3
- **8e1. Payment Failed**: System displays error → User retries or cancels
- **9e1. Booking Conflict**: System performs double-check → Refund if conflict → Display error

### Business Rules
- Minimum booking notice: 1 hour before slot
- Maximum advance booking: 30 days
- Buffer time between bookings: configurable per resource

---

## UC-04: Make Payment

| Field | Description |
|-------|-------------|
| **Use Case ID** | UC-04 |
| **Name** | Make Payment |
| **Actor** | User |
| **Description** | User pays for a booking or service |
| **Preconditions** | Valid booking in progress |
| **Postconditions** | Payment processed; receipt generated |

### Main Flow
1. System displays payment form with order summary
2. User selects payment method
3. User enters payment details
4. System validates payment information
5. System processes payment with gateway
6. System receives confirmation from gateway
7. System marks booking as paid
8. System generates and sends receipt

### Alternative Flows
- **2a. Saved Card**: User selects saved payment method → Skip step 3
- **2b. Wallet Pay**: User selects digital wallet → Redirect to wallet app → Return with confirmation

### Exception Flows
- **5e1. Payment Declined**: System displays "Payment declined" → User enters different method
- **5e2. Gateway Timeout**: System displays "Payment processing" → Retry or get status
- **6e1. Fraudulent Activity**: System blocks payment → Notifies admin

---

## UC-05: Cancel Booking

| Field | Description |
|-------|-------------|
| **Use Case ID** | UC-05 |
| **Name** | Cancel Booking |
| **Actor** | User |
| **Description** | User cancels an existing booking |
| **Preconditions** | User has an active booking; within cancellation window |
| **Postconditions** | Booking cancelled; refund processed per policy |

### Main Flow
1. User navigates to My Bookings
2. User selects booking to cancel
3. System displays booking details and cancellation policy
4. System shows refund amount based on policy
5. User confirms cancellation
6. System cancels booking
7. System processes refund (if applicable)
8. System releases slot to availability
9. System sends cancellation confirmation

### Alternative Flows
- **4a. No Refund**: Outside refund window → System displays "No refund applicable"
- **5a. Cancel with Reason**: User provides cancellation reason (optional)

### Exception Flows
- **3e1. Past Booking**: Cannot cancel past bookings
- **3e2. Already Cancelled**: Booking already cancelled
- **7e1. Refund Failed**: Log for manual processing → Notify admin

### Business Rules
```
Cancellation Policy:
- >48 hours before: 100% refund
- 24-48 hours before: 50% refund
- <24 hours before: No refund
```

---

## UC-06: Manage Resource (Provider)

| Field | Description |
|-------|-------------|
| **Use Case ID** | UC-06 |
| **Name** | Manage Resource |
| **Actor** | Provider |
| **Description** | Provider creates or updates resource listing |
| **Preconditions** | Provider is logged in and verified |
| **Postconditions** | Resource created/updated and available for booking |

### Main Flow (Create)
1. Provider navigates to resource management
2. Provider clicks "Add Resource"
3. System displays resource form
4. Provider enters basic information (name, description, category)
5. Provider uploads images
6. Provider sets location (address, map pin)
7. Provider defines capacity and amenities
8. Provider sets pricing rules
9. Provider configures availability schedule
10. Provider submits for review
11. System validates and saves resource
12. Resource becomes visible to users

### Alternative Flow (Update)
1. Provider selects existing resource
2. System displays current details
3. Provider modifies fields
4. System saves changes
5. System notifies if approval needed for major changes

### Exception Flows
- **4e1. Duplicate Name**: Warning for similar existing resource
- **5e1. Invalid Image**: Image doesn't meet requirements
- **11e1. Validation Error**: Display specific field errors

---

## UC-07: View Availability & Manage Schedule (Provider)

| Field | Description |
|-------|-------------|
| **Use Case ID** | UC-07 |
| **Name** | Manage Availability |
| **Actor** | Provider |
| **Description** | Provider sets and updates resource availability |
| **Preconditions** | Provider has at least one resource |
| **Postconditions** | Availability updated; affects slot generation |

### Main Flow
1. Provider selects resource
2. System displays current availability calendar
3. Provider defines weekly recurring schedule
4. Provider sets slot duration and buffer time
5. Provider adds special dates (holidays, events)
6. Provider blocks maintenance periods
7. System generates slots based on rules
8. System saves availability

### Alternative Flows
- **3a. Copy Schedule**: Copy settings from another resource
- **5a. Bulk Update**: Apply changes to date range

---

## UC-08: Handle Dispute (Admin)

| Field | Description |
|-------|-------------|
| **Use Case ID** | UC-08 |
| **Name** | Handle Dispute |
| **Actor** | Admin |
| **Description** | Admin resolves a conflict between user and provider |
| **Preconditions** | Dispute raised by user or provider |
| **Postconditions** | Dispute resolved; actions taken |

### Main Flow
1. Admin views dispute queue
2. Admin selects dispute to review
3. System displays dispute details and conversation
4. Admin reviews evidence from both parties
5. Admin attempts mediation (optional)
6. Admin makes decision
7. Admin issues refund or penalty as needed
8. Admin documents resolution
9. System notifies both parties
10. System closes dispute

### Alternative Flows
- **5a. Request More Info**: Admin asks for additional evidence
- **6a. Escalate**: Admin escalates to senior admin

---

## Use Case Relationship Matrix

| Use Case | Extends | Includes |
|----------|---------|----------|
| UC-01 Register | - | Send Verification Email |
| UC-02 Login | Social Login | Create Session |
| UC-03 Book Slot | Apply Promo Code | UC-04 Make Payment |
| UC-04 Make Payment | Use Saved Card | Generate Receipt |
| UC-05 Cancel Booking | - | Process Refund |
| UC-06 Manage Resource | - | Upload Images, Set Location |
| UC-07 Manage Availability | - | Generate Slots |
| UC-08 Handle Dispute | - | Issue Refund, Apply Penalty |
