# State Machine Diagrams

## Overview
State machine diagrams for the key stateful entities in the rental management system.

---

## Booking State Machine

```mermaid
stateDiagram-v2
    [*] --> PENDING : Customer submits booking + pays deposit

    PENDING --> CONFIRMED : Owner approves (manual mode)
    PENDING --> CONFIRMED : Auto-confirmed (instant booking mode)
    PENDING --> DECLINED : Owner declines booking
    PENDING --> CANCELLED : Customer cancels before owner reviews

    CONFIRMED --> ACTIVE : Rental start time reached + pre-rental assessment done
    CONFIRMED --> CANCELLED : Customer or owner cancels before rental starts

    ACTIVE --> PENDING_CLOSURE : Customer initiates return
    ACTIVE --> ACTIVE : Booking modified (dates extended with approval)

    PENDING_CLOSURE --> CLOSED : Post-rental assessment completed + final invoice settled
    PENDING_CLOSURE --> ACTIVE : Late return detected - rental continues (fees applied)

    CANCELLED --> [*] : Refund processed per policy
    DECLINED --> [*] : Deposit refunded in full
    CLOSED --> [*] : Rental complete
```

---

## Asset State Machine

```mermaid
stateDiagram-v2
    [*] --> DRAFT : Owner creates asset

    DRAFT --> AVAILABLE : Owner publishes listing

    AVAILABLE --> BOOKED : Booking confirmed for asset
    AVAILABLE --> UNDER_MAINTENANCE : Maintenance request logged
    AVAILABLE --> DRAFT : Owner unpublishes

    BOOKED --> ACTIVE_RENTAL : Rental period begins
    BOOKED --> AVAILABLE : Booking cancelled before rental starts

    ACTIVE_RENTAL --> PENDING_RETURN : Customer initiates return
    ACTIVE_RENTAL --> ACTIVE_RENTAL : Late return (overdue - stays active)

    PENDING_RETURN --> AVAILABLE : Return completed + assessment done + no maintenance needed
    PENDING_RETURN --> UNDER_MAINTENANCE : Post-rental assessment reveals damage

    UNDER_MAINTENANCE --> AVAILABLE : Maintenance approved and completed
    UNDER_MAINTENANCE --> RETIRED : Asset deemed beyond repair

    AVAILABLE --> RETIRED : Owner manually retires asset
    RETIRED --> [*]
```

---

## Rental Agreement State Machine

```mermaid
stateDiagram-v2
    [*] --> DRAFT : Owner generates agreement from template

    DRAFT --> PENDING_CUSTOMER_SIGNATURE : Owner sends for signature

    PENDING_CUSTOMER_SIGNATURE --> PENDING_OWNER_SIGNATURE : Customer signs digitally
    PENDING_CUSTOMER_SIGNATURE --> DRAFT : Customer requests amendment

    PENDING_OWNER_SIGNATURE --> SIGNED : Owner countersigns
    PENDING_OWNER_SIGNATURE --> PENDING_CUSTOMER_SIGNATURE : Owner requests amendment

    SIGNED --> AMENDED : Amendment issued and re-signed
    AMENDED --> SIGNED : Amendment fully signed

    SIGNED --> TERMINATED : Booking cancelled or rental closed
    AMENDED --> TERMINATED : Booking cancelled or rental closed

    TERMINATED --> [*]
```

---

## Security Deposit State Machine

```mermaid
stateDiagram-v2
    [*] --> HELD : Deposit collected on booking confirmation

    HELD --> FULLY_REFUNDED : No damage, on-time return
    HELD --> PARTIALLY_REFUNDED : Damage deductions applied; remainder refunded
    HELD --> FULLY_DEDUCTED : Deductions equal or exceed deposit amount
    HELD --> DISPUTED : Customer disputes proposed deductions

    DISPUTED --> PARTIALLY_REFUNDED : Dispute resolved; partial refund agreed
    DISPUTED --> FULLY_REFUNDED : Dispute upheld; all charges waived
    DISPUTED --> FULLY_DEDUCTED : Dispute rejected; full deduction upheld

    FULLY_REFUNDED --> [*]
    PARTIALLY_REFUNDED --> [*]
    FULLY_DEDUCTED --> [*]
```

---

## Maintenance Request State Machine

```mermaid
stateDiagram-v2
    [*] --> OPEN : Owner or system logs maintenance request
    note right of OPEN : Asset calendar blocked

    OPEN --> ASSIGNED : Owner assigns to staff member

    ASSIGNED --> IN_PROGRESS : Staff accepts and starts work
    ASSIGNED --> OPEN : Staff declines - reassignment needed

    IN_PROGRESS --> COMPLETED : Staff marks task complete

    COMPLETED --> CLOSED : Owner approves completion
    COMPLETED --> IN_PROGRESS : Owner reopens with reason (rework needed)

    CLOSED --> [*]
    note right of CLOSED : Asset calendar unblocked; cost logged
```

---

## Additional Charge State Machine

```mermaid
stateDiagram-v2
    [*] --> RAISED : Owner raises additional charge post-rental

    RAISED --> ACCEPTED : Customer accepts charge
    RAISED --> DISPUTED : Customer disputes charge
    RAISED --> WAIVED : Owner waives the charge

    DISPUTED --> ACCEPTED : Dispute rejected by owner or admin; charge stands
    DISPUTED --> WAIVED : Dispute upheld; charge removed
    DISPUTED --> PARTIALLY_ACCEPTED : Admin mediates; partial charge agreed

    ACCEPTED --> PAID : Customer pays the charge
    PARTIALLY_ACCEPTED --> PAID : Customer pays the agreed partial amount

    PAID --> [*]
    WAIVED --> [*]
```

---

## Invoice State Machine

```mermaid
stateDiagram-v2
    [*] --> DRAFT : Invoice auto-generated

    DRAFT --> SENT : Invoice dispatched to customer

    SENT --> PARTIALLY_PAID : Partial payment received
    SENT --> PAID : Full payment received
    SENT --> OVERDUE : Due date passed with no payment

    PARTIALLY_PAID --> PAID : Remaining balance paid
    PARTIALLY_PAID --> OVERDUE : Due date passed with balance still outstanding

    OVERDUE --> PAID : Late payment (with late fee applied)

    PAID --> [*]
    SENT --> WAIVED : Owner waives invoice (e.g., goodwill)
    WAIVED --> [*]
```
