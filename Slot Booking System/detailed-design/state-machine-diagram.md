# State Machine Diagram - Slot Booking System

> **Platform Independence**: State machines show object lifecycle independent of implementation.

---

## Overview

State Machine Diagrams show how key entities transition through various states during their lifecycle.

---

## 1. Booking State Machine

```mermaid
stateDiagram-v2
    [*] --> Draft: User selects slots
    
    Draft --> Pending: Slots locked successfully
    Draft --> Waitlisted: No slots available
    Draft --> [*]: Lock failed / Timeout
    
    Pending --> AwaitingPayment: Booking created
    
    AwaitingPayment --> Processing: Payment initiated
    AwaitingPayment --> Cancelled: User abandons / Timeout
    
    Processing --> Confirmed: Payment success
    Processing --> Failed: Payment failed
    
    Failed --> AwaitingPayment: User retries
    Failed --> Cancelled: User abandons
    
    Confirmed --> Completed: Slot time passed
    Confirmed --> Cancelled: User cancels
    Confirmed --> Rescheduled: User reschedules
    
    Rescheduled --> Confirmed: New slots confirmed
    
    Cancelled --> RefundPending: Refund applicable
    Cancelled --> [*]: No refund
    
    RefundPending --> Refunded: Refund processed
    Refunded --> [*]
    Waitlisted --> Pending: Slot becomes available
    
    Completed --> [*]
    
    note right of Draft: Slots temporarily<br/>locked (5 min TTL)
    note right of AwaitingPayment: Lock refreshed<br/>on page load
    note right of Confirmed: Reminders<br/>scheduled
    note right of Cancelled: Slots released<br/>back to pool
```

### Booking States Description

| State | Description | Entry Action | Exit Action |
|-------|-------------|--------------|-------------|
| **Draft** | User is selecting slots | Lock selected slots | - |
| **Pending** | Booking record created | Create booking, start payment | - |
| **AwaitingPayment** | Waiting for user to pay | Show payment form | - |
| **Processing** | Payment being processed | Submit to gateway | - |
| **Confirmed** | Booking is active | Send confirmation, schedule reminders | - |
| **Completed** | Booking fulfilled | Request review | - |
| **Cancelled** | Booking cancelled | Release slots, calculate refund | - |
| **RefundPending** | Refund in progress | Initiate refund | - |
| **Refunded** | Refund completed | Send refund confirmation | - |
| **Failed** | Payment failed | Notify user | - |
| **Rescheduled** | Change in progress | Lock new slots | Release old slots |

---

## 2. Slot State Machine

```mermaid
stateDiagram-v2
    [*] --> Available: Slot generated
    
    Available --> Locked: User selects
    Available --> Blocked: Provider blocks
    
    Locked --> Available: Lock expires / Released
    Locked --> Booked: Booking confirmed
    
    Booked --> Available: Booking cancelled
    Booked --> Completed: Time elapsed
    
    Blocked --> Available: Provider unblocks
    
    Completed --> [*]
    
    note right of Locked: 5-minute TTL<br/>Renewable once
    note right of Blocked: Maintenance,<br/>holidays, etc.
```

### Slot States Description

| State | Description | Can Transition To |
|-------|-------------|-------------------|
| **Available** | Open for booking | Locked, Blocked |
| **Locked** | Temporarily held for user | Available, Booked |
| **Booked** | Confirmed reservation | Available, Completed |
| **Blocked** | Unavailable by provider | Available |
| **Completed** | Time has passed | (Terminal) |

---

## 3. Payment State Machine

```mermaid
stateDiagram-v2
    [*] --> Initiated: Payment created
    
    Initiated --> Processing: User submits
    Initiated --> Abandoned: Timeout / User leaves
    
    Processing --> Authorized: Card authorized
    Processing --> Declined: Authorization failed
    Processing --> Pending3DS: 3DS required
    
    Pending3DS --> Authorized: 3DS verified
    Pending3DS --> Declined: 3DS failed
    
    Authorized --> Captured: Capture successful
    Authorized --> Voided: Capture cancelled
    
    Declined --> Initiated: Retry with new card
    Declined --> Abandoned: User gives up
    
    Captured --> PartialRefund: Partial refund issued
    Captured --> FullRefund: Full refund issued
    
    PartialRefund --> FullRefund: Remaining refunded
    
    Voided --> [*]
    Abandoned --> [*]
    FullRefund --> [*]
    
    note right of Processing: Sync call to<br/>payment gateway
    note right of Pending3DS: Redirect flow
    note right of Captured: Funds transferred
```

### Payment States Description

| State | Description | Triggers |
|-------|-------------|----------|
| **Initiated** | Payment record created | Booking submission |
| **Processing** | Being processed | User confirms |
| **Pending3DS** | 3D Secure verification | Gateway requires |
| **Authorized** | Funds authorized | Gateway success |
| **Captured** | Funds transferred | Auto or manual capture |
| **Declined** | Payment rejected | Gateway decline |
| **Voided** | Authorization cancelled | Before capture |
| **PartialRefund** | Part of amount refunded | Partial cancellation |
| **FullRefund** | Full amount refunded | Full cancellation |
| **Abandoned** | User never completed | Timeout |

---

## 4. User Account State Machine

```mermaid
stateDiagram-v2
    [*] --> Registered: User signs up
    
    Registered --> PendingVerification: Email sent
    
    PendingVerification --> Active: Email verified
    PendingVerification --> Expired: Verification timeout
    
    Expired --> PendingVerification: Resend verification
    
    Active --> Suspended: Admin suspends
    Active --> Deleted: User requests deletion
    
    Suspended --> Active: Admin reactivates
    Suspended --> Deleted: Admin deletes
    
    Deleted --> [*]
    
    note right of PendingVerification: 24-hour validity
    note right of Suspended: Cannot login<br/>Bookings cancelled
    note right of Deleted: Data anonymized<br/>per GDPR
```

---

## 5. Provider Application State Machine

```mermaid
stateDiagram-v2
    [*] --> Draft: Provider starts application
    
    Draft --> Submitted: Application submitted
    
    Submitted --> UnderReview: Admin starts review
    
    UnderReview --> MoreInfoRequired: Additional docs needed
    UnderReview --> Approved: Admin approves
    UnderReview --> Rejected: Admin rejects
    
    MoreInfoRequired --> UnderReview: Provider provides info
    MoreInfoRequired --> Withdrawn: Provider gives up
    
    Approved --> Active: Account activated
    
    Rejected --> Draft: Provider reapplies
    
    Active --> Suspended: Policy violation
    
    Suspended --> Active: Suspension lifted
    Suspended --> Terminated: Serious violation
    
    Withdrawn --> [*]
    Terminated --> [*]
    
    note right of UnderReview: Background checks,<br/>document verification
    note right of Active: Can list resources
```

---

## 6. Resource State Machine

```mermaid
stateDiagram-v2
    [*] --> Draft: Provider starts creation
    
    Draft --> PendingReview: Provider submits
    Draft --> Discarded: Provider discards
    
    PendingReview --> Approved: Admin approves
    PendingReview --> Rejected: Admin rejects
    PendingReview --> Draft: Returned for edits
    
    Approved --> Active: Auto-publish or manual
    
    Rejected --> Draft: Provider edits & resubmits
    
    Active --> Inactive: Provider deactivates
    Active --> UnderReview: Reported / Flagged
    Active --> Suspended: Policy violation
    
    Inactive --> Active: Provider reactivates
    Inactive --> Deleted: Provider deletes
    
    UnderReview --> Active: Cleared
    UnderReview --> Suspended: Violation confirmed
    
    Suspended --> Active: Suspension lifted
    Suspended --> Deleted: Permanently removed
    
    Discarded --> [*]
    Deleted --> [*]
    
    note right of Active: Visible in search<br/>Slots bookable
    note right of Inactive: Hidden from search<br/>Existing bookings valid
```

---

## 7. Review State Machine

```mermaid
stateDiagram-v2
    [*] --> Pending: User submits review
    
    Pending --> Published: Auto-moderation passed
    Pending --> FlaggedForReview: Auto-moderation flagged
    
    FlaggedForReview --> Published: Admin approves
    FlaggedForReview --> Rejected: Admin rejects
    
    Published --> Reported: User reports
    Published --> Responded: Provider responds
    
    Reported --> UnderReview: Admin investigates
    
    UnderReview --> Published: Report dismissed
    UnderReview --> Hidden: Review hidden
    UnderReview --> Deleted: Review deleted
    
    Responded --> Published: (remains published with response)
    
    Rejected --> [*]
    Hidden --> [*]
    Deleted --> [*]
    
    note right of Published: Visible to all users
    note right of Hidden: Only author can see
```

---

## 8. Notification State Machine

```mermaid
stateDiagram-v2
    [*] --> Queued: Notification created
    
    Queued --> Sending: Worker picks up
    
    Sending --> Sent: All channels delivered
    Sending --> PartiallySent: Some channels failed
    Sending --> Failed: All channels failed
    
    PartiallySent --> Retry: Retry failed channels
    Failed --> Retry: Schedule retry
    
    Retry --> Sending: Retry attempt
    Retry --> PermanentlyFailed: Max retries exceeded
    
    Sent --> Read: User opens/clicks
    PartiallySent --> Read: User sees via successful channel
    
    Read --> [*]
    PermanentlyFailed --> [*]
    
    note right of Sending: Email, Push, SMS<br/>processed in parallel
    note right of Retry: Exponential backoff
```

---

## State Transition Events Summary

| Entity | Key Events | Business Impact |
|--------|-----------|-----------------|
| **Booking** | Created, Confirmed, Cancelled, Completed | Core revenue flow |
| **Slot** | Locked, Booked, Released | Inventory management |
| **Payment** | Authorized, Captured, Refunded | Financial transactions |
| **User** | Verified, Suspended, Deleted | Access control |
| **Provider** | Approved, Suspended, Terminated | Supply side |
| **Resource** | Published, Deactivated, Deleted | Catalog management |
| **Review** | Published, Reported, Hidden | Content moderation |
| **Notification** | Sent, Read, Failed | User communication |

---
## Implementation-Ready State Machine Diagram

### Slot allocation rules in this document's context
- Allocation decisions must be based on **resource calendar + operational policy + channel limits** before any payment action is attempted.
- All provisional allocations require an explicit **hold record with expiry**, and expiry must be visible to clients.
- Shared-capacity resources must use atomic decrement semantics; exclusive resources must enforce single-active-booking constraints.

### Conflict resolution in this document's context
- Competing writes must use deterministic conflict handling (optimistic version checks or transactional locks as documented here).
- API and admin paths must converge on one canonical conflict reason taxonomy (`SLOT_TAKEN`, `STALE_VERSION`, `PROVIDER_BLOCKED`, `PAYMENT_STATE_MISMATCH`).
- Every conflict rejection must emit structured audit telemetry including actor, correlation ID, and rule version.

### Payment coupling / decoupling behavior
- **Coupled flow**: booking moves to confirmed only after successful authorization/capture.
- **Decoupled flow**: booking can be confirmed with `PAYMENT_PENDING`, but with a bounded grace window and auto-cancel guardrail.
- Compensation is mandatory for split-brain outcomes (payment succeeded but booking failed, or inverse).

### Cancellation and refund policy detail
- Refund outcomes depend on lead time, policy tier, no-show status, and jurisdiction-specific fee constraints.
- Refund processing must be idempotent and expose lifecycle states (`REQUESTED`, `INITIATED`, `SETTLED`, `FAILED`, `MANUAL_REVIEW`).
- Cancellation side effects must include slot reallocation and downstream notification consistency.

### Observability and incident playbook focus
- Monitor: availability latency, hold expiry lag, conflict rate, payment callback success, refund aging.
- Alerts must map to operator runbooks with first-response steps and data reconciliation queries.
- Post-incident review must record policy gaps and required control changes for this documentation area.

### Detailed implementation contracts
- Transaction boundaries for hold, confirm, cancel, and refund actions.
- Outbox/inbox idempotency strategy for webhook and event replay safety.
- Data model constraints and indexes required to prevent overlap anomalies.


### Mermaid composite booking/payment states
```mermaid
stateDiagram-v2
  [*] --> Available
  Available --> Held: hold created
  Held --> BookedPendingPayment: decoupled confirm
  Held --> BookedPaid: coupled confirm + auth
  Held --> Available: hold timeout
  BookedPendingPayment --> BookedPaid: payment received
  BookedPendingPayment --> CancelledExpired: grace timeout
  BookedPaid --> CancelledRefundPending: cancel
  CancelledRefundPending --> CancelledRefunded: refund settled
```
