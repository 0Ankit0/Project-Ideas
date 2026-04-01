# Event Management and Ticketing Platform — State Machine Diagrams

## Overview

This document defines four state machines governing the core lifecycle entities of the platform. Each machine is implemented as a persistent state column with database-level CHECK constraints, enforced transitions in the service layer, and domain events emitted on every transition.

---

## State Machine 1: Event Lifecycle

Events progress from internal drafting through a moderation gate before becoming publicly visible. Once live, they track sell-out, runtime, and completion automatically via scheduled jobs.

```mermaid
stateDiagram-v2
    [*] --> Draft : Organizer creates event\n(status = DRAFT)

    Draft --> PendingApproval : Organizer submits for review\nGuard: all required fields populated\nAction: notify moderation team

    Draft --> Published : Auto-publish enabled\nGuard: organizer.kyc_status = VERIFIED\nAction: index in search, send confirmation email

    PendingApproval --> Published : Admin approves\nAction: index in search engine, notify organizer\nemail, push notification sent

    PendingApproval --> Draft : Admin rejects with feedback\nAction: notify organizer with rejection reasons\nfeedback stored in event_review_notes

    Published --> SoldOut : available_count reaches 0\nGuard: ticket_inventory.available_count = 0\nAction: enable waitlist, notify organizer\nupdate search index

    SoldOut --> Published : Inventory restored\n(cancellation or capacity increase)\nGuard: available_count > 0\nAction: notify waitlist, update search index\npromote top waitlist entries

    Published --> Ongoing : Scheduled job fires at start_time\nGuard: NOW() >= event.start_time\nAction: send "event starting" push notifications\nenable check-in mode in scanner apps

    SoldOut --> Ongoing : Scheduled job fires at start_time\nGuard: NOW() >= event.start_time\nAction: send "event starting" push notifications

    Ongoing --> Completed : Scheduled job fires at end_time\nGuard: NOW() >= event.end_time\nAction: disable check-in, trigger payout calculation\nsend post-event survey, archive event

    Published --> Cancelled : Organizer cancels\nGuard: organizer confirms cancellation\nAction: trigger full refunds for all confirmed orders\nnotify all attendees, update search index

    SoldOut --> Cancelled : Organizer cancels\nAction: trigger full refunds, notify waitlist entries\nupdate search index

    Ongoing --> Cancelled : Emergency cancellation\nGuard: admin or organizer confirms\nAction: trigger full refunds, push notification to attendees\nsend urgent email

    Completed --> [*] : Terminal state — all obligations fulfilled
    Cancelled --> [*] : Terminal state — refunds processed
```

### Event State Transition Rules

| From | To | Guard Condition | Side Effects |
|------|----|-----------------|--------------|
| `DRAFT` | `PENDING_APPROVAL` | All required fields set | Moderation queue entry created |
| `DRAFT` | `PUBLISHED` | KYC verified + auto-publish flag | Search indexed, tickets on sale |
| `PENDING_APPROVAL` | `PUBLISHED` | Admin approval action | Organizer notified via email |
| `PENDING_APPROVAL` | `DRAFT` | Admin rejection | Rejection reason stored |
| `PUBLISHED` | `SOLD_OUT` | `available_count = 0` | Waitlist enabled |
| `SOLD_OUT` | `PUBLISHED` | `available_count > 0` | Waitlist promoted |
| `PUBLISHED` | `ONGOING` | `NOW() >= start_time` | Check-in mode activated |
| `ONGOING` | `COMPLETED` | `NOW() >= end_time` | Payout job triggered |
| `PUBLISHED` | `CANCELLED` | Organiser + confirmation | Full refunds issued |
| `ONGOING` | `CANCELLED` | Admin emergency | Full refunds + urgent notification |

---

## State Machine 2: Order Lifecycle

Orders begin in a short-lived PENDING state while payment is collected. The `expires_at` field (default: 15 minutes) acts as a soft guard; a background sweeper cancels un-paid orders that have timed out.

```mermaid
stateDiagram-v2
    [*] --> Pending : Order created by attendee\nAction: reserve inventory hold\ncreate payment_intent via Stripe\nset expires_at = NOW() + 15min

    Pending --> PaymentProcessing : Attendee submits payment\nGuard: order.expires_at > NOW()\nAction: record payment_intent_id\nmark order payment_processing

    Pending --> Cancelled : Order expires (no payment submitted)\nGuard: NOW() > order.expires_at\nAction: release inventory hold\nbackground sweeper fires

    PaymentProcessing --> Confirmed : Payment gateway webhook received\n(payment_intent.succeeded)\nAction: confirm hold → sold\nissue tickets, send confirmation email\ngenerate PDF + wallet pass

    PaymentProcessing --> Cancelled : Payment failed or timed out\n(payment_intent.payment_failed)\nAction: release inventory hold\nnotify attendee of failure

    Confirmed --> PartiallyRefunded : Partial refund approved\nGuard: refund_amount < order.total\nAction: update order.discount\nreimburse via payment gateway\ncancel affected tickets

    Confirmed --> FullyRefunded : Full refund approved\nGuard: refund_amount = order.total\nAction: cancel all tickets\nreimburse full amount via gateway\nrelease seats back to inventory

    Confirmed --> Cancelled : Event cancelled by organizer\nAction: automatically trigger full refund flow\nsend cancellation email to attendee

    PartiallyRefunded --> FullyRefunded : Remaining balance refunded\nGuard: total refunded = order.total\nAction: cancel remaining tickets

    FullyRefunded --> [*] : Terminal state
    Cancelled --> [*] : Terminal state
```

### Order State Transition Rules

| From | To | Guard | Side Effects |
|------|----|-------|--------------|
| `PENDING` | `PAYMENT_PROCESSING` | `expires_at > NOW()` | `payment_intent_id` stored |
| `PENDING` | `CANCELLED` | `expires_at < NOW()` | Inventory hold released |
| `PAYMENT_PROCESSING` | `CONFIRMED` | Gateway webhook success | Tickets issued, emails sent |
| `PAYMENT_PROCESSING` | `CANCELLED` | Gateway webhook failure | Hold released, attendee notified |
| `CONFIRMED` | `PARTIALLY_REFUNDED` | Partial refund processed | Affected tickets cancelled |
| `CONFIRMED` | `FULLY_REFUNDED` | Full refund processed | All tickets cancelled, seats freed |
| `CONFIRMED` | `CANCELLED` | Event cancelled | Full refund auto-triggered |
| `PARTIALLY_REFUNDED` | `FULLY_REFUNDED` | Remaining amount refunded | All tickets cancelled |

---

## State Machine 3: Ticket Lifecycle

Each ticket follows the order that spawned it. Once issued, it can be independently transferred, checked in, or cancelled. The `qr_code_hash` is regenerated on transfer to invalidate the old code.

```mermaid
stateDiagram-v2
    [*] --> Reserved : Seat hold placed\n(order created, payment pending)\nAction: seat.status = HELD\ncreate hold_block record

    Reserved --> Issued : Order confirmed, payment received\nGuard: order.status = CONFIRMED\nAction: generate qr_code_hash (HMAC-SHA256)\ncreate ticket record\ngenerate PDF + wallet pass\nemail ticket to attendee

    Reserved --> Cancelled : Hold expired or order cancelled\nGuard: hold expired OR order.status = CANCELLED\nAction: seat.status = AVAILABLE\ndelete hold_block\nincrement available_count

    Issued --> Transferred : Owner initiates transfer\nGuard: ticket_type.is_transferable = true\nEvent not started (start_time > NOW())\nAction: generate transfer_token (30min TTL)\ninvalidate old qr_code_hash on acceptance\ngenerate new qr_code_hash for new owner

    Issued --> CheckedIn : QR code scanned at venue\nGuard: valid HMAC\nNOW() within event window\nAction: create check_in record\nticket.checked_in_at = NOW()\noptionally trigger badge print

    Transferred --> CheckedIn : Transferred ticket scanned\nGuard: valid HMAC for new owner\nAction: create check_in record\n(same validation as issued ticket)

    Issued --> Cancelled : Event cancelled\nGuard: event.status = CANCELLED\nAction: trigger refund flow\nseat.status = AVAILABLE

    Transferred --> Cancelled : Event cancelled after transfer\nAction: refund to current ticket holder

    Issued --> Refunded : Refund approved on order\nGuard: refund.status = COMPLETED\nAction: ticket.status = REFUNDED\nseat.status = AVAILABLE\ninvalidate qr_code_hash

    CheckedIn --> [*] : Event completed\nAction: archive ticket, final state
```

### Ticket State Transition Rules

| From | To | Guard | Side Effects |
|------|----|-------|--------------|
| _(new)_ | `RESERVED` | Order created | `seat.status = HELD` |
| `RESERVED` | `ISSUED` | `order.status = CONFIRMED` | QR hash generated, PDF emailed |
| `RESERVED` | `CANCELLED` | Hold expired | `available_count` incremented |
| `ISSUED` | `TRANSFERRED` | Transferable + before event | Old QR invalidated, new QR issued |
| `ISSUED` | `CHECKED_IN` | Valid HMAC + event window | `check_in` record created |
| `TRANSFERRED` | `CHECKED_IN` | Valid HMAC | `check_in` record created |
| `ISSUED` | `REFUNDED` | `refund.status = COMPLETED` | QR invalidated, seat freed |
| `ISSUED` | `CANCELLED` | Event cancelled | Auto-refund flow triggered |

---

## State Machine 4: Waitlist Entry Lifecycle

When inventory reaches zero, attendees can join the waitlist. Entries are position-ordered. When a ticket becomes available (through cancellation), the top entry is promoted and given a 30-minute exclusive purchase window.

```mermaid
stateDiagram-v2
    [*] --> Active : Attendee joins waitlist\nGuard: event.status = SOLD_OUT\nticket_type on the waitlist\nAction: assign position\nsend confirmation email\n"You are #12 on the waitlist"

    Active --> Promoted : Ticket becomes available\n(cancellation or capacity increase)\nGuard: entry is at position 1\nAction: set exclusive_window_expires_at = NOW() + 30min\nsend email + push notification\n"A ticket is available — buy within 30 minutes"

    Promoted --> Purchased : Attendee completes purchase\nGuard: NOW() < exclusive_window_expires_at\nAction: create order for attendee\nmark waitlist entry as PURCHASED\nadvance remaining queue positions

    Promoted --> Expired : 30-minute window elapsed\nGuard: NOW() >= exclusive_window_expires_at\nwithout purchase\nAction: promote next entry in queue\nsend "offer expired" notification

    Expired --> Active : Re-queued by configuration\nGuard: event.waitlist_requeue_enabled = true\nAction: append to end of queue\nsend re-queue notification

    Active --> Withdrawn : Attendee cancels waitlist entry\nGuard: entry.status = ACTIVE\nAction: remove from queue\nadvance positions of entries below\nsend withdrawal confirmation

    Purchased --> [*] : Terminal state — ticket acquired
    Withdrawn --> [*] : Terminal state — attendee opted out
```

### Waitlist State Transition Rules

| From | To | Guard | Side Effects |
|------|----|-------|--------------|
| _(new)_ | `ACTIVE` | Event sold out | Position assigned, email sent |
| `ACTIVE` | `PROMOTED` | Position 1 and ticket available | 30-min window set, notification sent |
| `PROMOTED` | `PURCHASED` | Within window | Order created at original price |
| `PROMOTED` | `EXPIRED` | Window elapsed | Next entry promoted |
| `EXPIRED` | `ACTIVE` | Re-queue enabled | Moved to end of queue |
| `ACTIVE` | `WITHDRAWN` | Attendee cancels | Queue positions shifted |

---

## Implementation Notes

### Database Enforcement
All status columns use PostgreSQL CHECK constraints:
```sql
status VARCHAR(30) NOT NULL CHECK (status IN ('DRAFT','PENDING_APPROVAL','PUBLISHED','SOLD_OUT','ONGOING','COMPLETED','CANCELLED'))
```

### Service-Layer Enforcement
Each service uses a transition validation map before executing state changes:

```python
VALID_TRANSITIONS = {
    ("DRAFT", "PENDING_APPROVAL"),
    ("DRAFT", "PUBLISHED"),
    ("PENDING_APPROVAL", "PUBLISHED"),
    ("PENDING_APPROVAL", "DRAFT"),
    ("PUBLISHED", "SOLD_OUT"),
    ("PUBLISHED", "ONGOING"),
    ("PUBLISHED", "CANCELLED"),
    ("SOLD_OUT", "PUBLISHED"),
    ("SOLD_OUT", "ONGOING"),
    ("SOLD_OUT", "CANCELLED"),
    ("ONGOING", "COMPLETED"),
    ("ONGOING", "CANCELLED"),
}

def transition(entity, new_status, actor_id):
    if (entity.status, new_status) not in VALID_TRANSITIONS:
        raise InvalidTransitionError(entity.status, new_status)
    entity.status = new_status
    audit_log.append(entity.id, actor_id, new_status)
    event_bus.publish(f"{entity.type}.{new_status.lower()}", entity)
```

### Domain Events Published on Transitions

| Transition | Domain Event |
|------------|-------------|
| Event → PUBLISHED | `event.published` |
| Event → SOLD_OUT | `event.capacity.sold_out` |
| Event → CANCELLED | `event.cancelled` |
| Order → CONFIRMED | `order.confirmed` |
| Order → CANCELLED | `order.cancelled` |
| Ticket → ISSUED | `ticket.issued` |
| Ticket → CHECKED_IN | `ticket.checked_in` |
| Ticket → TRANSFERRED | `ticket.transferred` |
| Waitlist → PROMOTED | `waitlist.promoted` |
| Payout → COMPLETED | `payout.completed` |
