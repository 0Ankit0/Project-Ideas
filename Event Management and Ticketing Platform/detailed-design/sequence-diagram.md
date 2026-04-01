
# Event Management and Ticketing Platform — Sequence Diagrams

## Overview

These sequence diagrams capture four critical flows in the platform: concurrent ticket purchasing with race-condition protection, dynamic pricing computation, badge printing at check-in, and post-event payout calculation.

---

## Sequence 1: Concurrent Ticket Purchase with Optimistic Locking

Two clients simultaneously attempt to purchase the last available ticket. Redis atomic operations (SETNX) and PostgreSQL optimistic locking together ensure exactly one purchase succeeds.

```mermaid
sequenceDiagram
    autonumber
    participant C1 as Client A
    participant C2 as Client B
    participant GW as API Gateway
    participant OS as OrderService
    participant IS as InventoryService
    participant RD as Redis
    participant PG as PostgreSQL
    participant PS as PaymentService
    participant NS as NotificationService

    par Client A and Client B race for last ticket
        C1->>GW: POST /api/v1/orders {ticket_type_id, qty:1, idempotency_key:abc}
        C2->>GW: POST /api/v1/orders {ticket_type_id, qty:1, idempotency_key:xyz}
    end

    GW->>OS: route order request (Client A)
    GW->>OS: route order request (Client B)

    OS->>IS: holdInventory(ticket_type_id, qty=1, session=abc)
    OS->>IS: holdInventory(ticket_type_id, qty=1, session=xyz)

    IS->>RD: SETNX hold:ticket_type_id:seat_101 "session=abc" EX 600
    Note over RD: Atomic SETNX — only one writer wins

    RD-->>IS: OK (Client A wins the hold)
    IS->>RD: SETNX hold:ticket_type_id:seat_101 "session=xyz" EX 600
    RD-->>IS: FAIL (key already exists)

    IS-->>OS: HoldBlock{hold_id, seat_id, expires_at} (Client A)
    IS-->>OS: 409 Conflict — no available seats (Client B)

    OS-->>GW: 409 {error: "SOLD_OUT", message: "No seats available"} (Client B)
    GW-->>C2: 409 Conflict — ticket no longer available

    OS->>PG: INSERT orders(order_id, status=PENDING, idempotency_key=abc, ...)
    OS-->>GW: 201 {order_id, status:pending, payment_intent_client_secret, expires_at}
    GW-->>C1: 201 Order created — proceed to payment

    C1->>PS: confirmPayment(payment_intent_id, card_token)
    PS->>PS: charge card via Stripe
    PS-->>C1: Payment accepted — awaiting webhook confirmation

    Note over PS: Stripe processes async
    PS->>GW: POST /webhooks/stripe {event:payment_intent.succeeded, payment_intent_id}
    GW->>PS: WebhookHandler.verify(signature)
    PS->>PS: IdempotencyChecker — ensure not processed before

    PS->>OS: notifyPaymentSucceeded(order_id, payment_intent_id)
    OS->>PG: UPDATE orders SET status=CONFIRMED WHERE order_id=? AND status=PENDING AND version=1
    Note over PG: Optimistic lock — version must match

    PG-->>OS: 1 row updated (version incremented to 2)

    OS->>IS: confirmHold(session=abc)
    IS->>PG: UPDATE ticket_inventory SET available_count = available_count - 1, sold_count = sold_count + 1 WHERE inventory_id = ? AND available_count >= 1
    PG-->>IS: 1 row updated

    IS->>RD: DEL hold:ticket_type_id:seat_101
    IS->>PG: INSERT tickets(ticket_id, order_item_id, status=ISSUED, qr_code_hash, issued_at)

    OS->>NS: publishEvent("order.confirmed", {order_id, attendee_email, tickets})
    NS->>NS: EmailTemplateRenderer.render("order_confirmation")
    NS-->>C1: Email — "Your tickets are confirmed" with PDF attachment
    NS->>NS: WalletPassGenerator.generate(ticket_id)
    NS-->>C1: Push notification — Apple/Google Wallet pass URL
```

---

## Sequence 2: Dynamic Pricing Calculation

The platform supports surge pricing based on inventory utilisation. Price tiers are computed on demand and cached in Redis with a 60-second TTL to avoid hammering the database on every GET /ticket-types request.

```mermaid
sequenceDiagram
    autonumber
    participant C as Client
    participant PS as PricingService
    participant IS as InventoryService
    participant RD as Redis

    C->>PS: GET /api/v1/events/{event_id}/ticket-types/{type_id}/price

    PS->>RD: GET price:ticket_type_id:{type_id}
    RD-->>PS: nil (cache miss)

    PS->>IS: getInventoryStats(ticket_type_id)
    IS->>IS: SELECT total_capacity, sold_count, held_count FROM ticket_inventory
    IS-->>PS: {total: 1000, sold: 830, held: 45, available: 125}

    PS->>PS: capacity_pct = (sold + held) / total = 87.5%

    alt capacity_pct < 50%
        PS->>PS: computed_price = base_price
        Note over PS: No surge — standard price applies
    else capacity_pct >= 50% and < 80%
        PS->>PS: computed_price = base_price * 1.10
        Note over PS: Low surge — 10% premium
    else capacity_pct >= 80% and < 95%
        PS->>PS: computed_price = base_price * 1.25
        Note over PS: Medium surge — 25% premium (current case: 87.5%)
    else capacity_pct >= 95%
        PS->>PS: computed_price = base_price * 1.50
        PS->>PS: computed_price = MIN(computed_price, ceiling_price)
        Note over PS: High surge — 50% premium, ceiling cap applied
    end

    PS->>PS: expires_at = NOW() + 60s
    PS->>RD: SETEX price:ticket_type_id:{type_id} 60 {price, computed_at, expires_at}
    RD-->>PS: OK

    PS-->>C: 200 {price: 156.25, currency: "USD", surge_active: true, surge_multiplier: 1.25, base_price: 125.00, expires_at: "2025-06-01T14:35:00Z"}

    Note over C: 60 seconds later — cache expires
    C->>PS: GET /api/v1/events/{event_id}/ticket-types/{type_id}/price
    PS->>RD: GET price:ticket_type_id:{type_id}
    RD-->>PS: nil (TTL expired)
    PS->>IS: getInventoryStats(ticket_type_id)
    IS-->>PS: {total: 1000, sold: 945, held: 10, available: 45}
    PS->>PS: capacity_pct = 95.5% → tier: HIGH SURGE → base * 1.50
    PS->>PS: computed_price = MIN(187.50, ceiling_price=175.00) = 175.00
    PS->>RD: SETEX price:ticket_type_id:{type_id} 60 {price: 175.00, ...}
    PS-->>C: 200 {price: 175.00, surge_active: true, surge_multiplier: 1.50, ceiling_applied: true, expires_at: "..."}
```

---

## Sequence 3: Badge Printing at Check-In

Staff scan the attendee's QR code. The system validates the ticket, fetches the attendee profile, generates a personalised badge PDF, and sends it to the nearest Zebra printer.

```mermaid
sequenceDiagram
    autonumber
    participant SA as ScannerApp
    participant CS as CheckInService
    participant TS as TicketService
    participant BS as BadgeService
    participant ZP as ZebraPrinter

    SA->>CS: POST /api/v1/check-ins {qr_code_hash, event_id, staff_id, device_id, scanned_at}

    CS->>TS: validateTicket(qr_code_hash, event_id)
    TS->>TS: SELECT * FROM tickets WHERE qr_code_hash = ? AND event_id = ?
    TS->>TS: verifyHMAC(qr_code_hash, ticket_id, event_id, issued_at, secret)

    alt HMAC invalid or ticket not found
        TS-->>CS: ValidationResult{status: INVALID_QR}
        CS-->>SA: 200 {status: "invalid", message: "QR code not recognised"}
    else ticket already checked in
        TS-->>CS: ValidationResult{status: ALREADY_CHECKED_IN, checked_in_at}
        CS-->>SA: 200 {status: "already_checked_in", checked_in_at, attendee_name}
    else ticket for wrong event
        TS-->>CS: ValidationResult{status: WRONG_EVENT, expected_event_title}
        CS-->>SA: 200 {status: "wrong_event", message: "Ticket is for a different event"}
    else ticket valid
        TS-->>CS: ValidationResult{status: SUCCESS, ticket_id, attendee_id, ticket_type}
    end

    CS->>TS: fetchAttendeeProfile(attendee_id)
    TS-->>CS: {first_name, last_name, email, company, job_title, dietary_requirements, accessibility_needs}

    CS->>CS: INSERT check_ins(checkin_id, ticket_id, staff_id, device_id, scanned_at)
    CS->>TS: markCheckedIn(ticket_id, staff_id, scanned_at)
    TS->>TS: UPDATE tickets SET status=CHECKED_IN, checked_in_at=NOW() WHERE ticket_id=?

    CS->>BS: generateBadge(ticket_id, attendee_profile, event_id)
    BS->>BS: fetchBadgeTemplate(event_id, ticket_type)
    BS->>BS: renderBadgePDF({name: "Jane Smith", title: "Senior Engineer", company: "Acme Corp", ticket_type: "VIP", event_name: "TechConf 2025", event_date: "June 10, 2025", seat: "Section A Row 3 Seat 12", qr_code_hash})
    BS->>BS: embedQRCode(qr_code_hash, 300x300px)
    BS-->>CS: {badge_pdf_bytes, badge_id}

    CS->>CS: INSERT badge_prints(badge_id, ticket_id, print_status=QUEUED, printer_id, template_id)

    CS->>ZP: printBadge(printer_id, badge_pdf_bytes, copies=1)
    ZP->>ZP: Render ZPL label from PDF
    ZP-->>CS: {ack: true, print_job_id, estimated_seconds: 3}

    CS->>CS: UPDATE badge_prints SET print_status=PRINTING, print_job_id=?

    ZP-->>CS: printComplete(print_job_id) [async callback]
    CS->>CS: UPDATE badge_prints SET print_status=PRINTED, printed_at=NOW()

    CS-->>SA: 200 {status: "success", attendee: {name: "Jane Smith", company: "Acme Corp"}, ticket_type: "VIP", seat: "A3-12", badge_printed: true, check_in_count: 847, total_capacity: 1200}
```

---

## Sequence 4: Payout Calculation After Event

After an event concludes, the payout scheduler triggers a calculation job that aggregates revenue, deducts fees and refunds, screens through OFAC, and initiates a bank transfer.

```mermaid
sequenceDiagram
    autonumber
    participant SCH as PayoutScheduler
    participant PYS as PayoutService
    participant ORS as OrderService
    participant RFS as RefundService
    participant FES as FeeService
    participant TXS as TaxService
    participant OFC as OFACService
    participant BTS as BankTransferService
    participant ACS as AccountingService

    SCH->>SCH: CRON: 0 2 * * * — run nightly for completed events
    SCH->>PYS: triggerPayoutCalculation(event_id, organizer_id)

    PYS->>ORS: getConfirmedOrders(event_id)
    ORS->>ORS: SELECT * FROM orders WHERE event_id=? AND status=CONFIRMED
    ORS-->>PYS: orders[] (e.g. 1 842 orders)

    PYS->>PYS: gross_revenue = SUM(orders.total) = $184,200.00

    PYS->>RFS: getProcessedRefunds(event_id)
    RFS->>RFS: SELECT * FROM refunds WHERE order_id IN (...) AND status=COMPLETED
    RFS-->>PYS: refunds[] → refunds_total = $3,150.00

    PYS->>FES: calculatePlatformFee(organizer_id, gross_revenue)
    FES->>FES: SELECT platform_fee_pct FROM organizers WHERE organizer_id=?
    FES->>FES: platform_fee = gross_revenue * (fee_pct / 100) = $184,200 * 0.05 = $9,210.00
    FES-->>PYS: {platform_fee: 9210.00, fee_rate: 0.05}

    PYS->>TXS: calculateWithholding(organizer_id, gross_revenue, country_code)
    TXS->>TXS: Lookup W-9 / W-8BEN status
    TXS->>TXS: withholding_rate = 0% (US organizer, W-9 on file)
    TXS-->>PYS: {tax_withheld: 0.00, withholding_rate: 0.00, tax_form: "W-9"}

    PYS->>PYS: net_amount = gross_revenue - refunds_total - platform_fee - tax_withheld
    PYS->>PYS: net_amount = $184,200 - $3,150 - $9,210 - $0 = $171,840.00

    PYS->>OFC: screenOrganizer(organizer_id, business_name, bank_account_id)
    OFC->>OFC: Query OFAC SDN list and PEP databases
    OFC-->>PYS: {clear: true, screened_at: "2025-06-01T02:15:33Z", reference: "OFAC-88271"}

    alt OFAC match found
        OFC-->>PYS: {clear: false, match_type: "SDN", hold_reason: "Sanctions match"}
        PYS->>PYS: INSERT payouts(status=HOLD, hold_reason="OFAC_MATCH")
        PYS->>ACS: flagPayoutForReview(payout_id, reason="OFAC_MATCH")
        Note over PYS: Payout paused — compliance team alerted
    else OFAC clear
        PYS->>PYS: INSERT payouts(payout_id, organizer_id, event_id, gross_revenue, platform_fee, tax_withheld, refunds_deducted, net_amount, status=HOLD)
        Note over PYS: Hold period = organizer.payout_hold_days (default: 7)
    end

    PYS->>SCH: schedulePayout(payout_id, release_at = NOW() + 7 days)

    Note over SCH: 7 days later
    SCH->>PYS: releasePayout(payout_id)
    PYS->>PYS: UPDATE payouts SET status=APPROVED WHERE payout_id=?

    PYS->>BTS: initiateBankTransfer(bank_account_id, amount=171840.00, currency="USD", reference=payout_id)
    BTS->>BTS: POST /v1/payouts to Stripe/Plaid/ACH gateway
    BTS-->>PYS: {transfer_id: "tr_1abc", estimated_arrival: "2025-06-09", status: "pending"}

    PYS->>PYS: UPDATE payouts SET status=INITIATED, transfer_reference="tr_1abc", initiated_at=NOW()

    BTS-->>PYS: webhookCallback(transfer.paid, transfer_id="tr_1abc")
    PYS->>PYS: UPDATE payouts SET status=COMPLETED, completed_at=NOW()

    PYS->>ACS: recordPayoutJournalEntry(payout_id, {debit: "Revenue Payable", credit: "Cash", amount: 171840.00, event_id, organizer_id, transfer_reference: "tr_1abc"})
    ACS-->>PYS: {journal_entry_id: "JE-29104", recorded_at: "2025-06-09T09:00:00Z"}

    PYS->>PYS: publishEvent("payout.completed", {payout_id, organizer_id, net_amount: 171840.00})
    Note over PYS: Organizer receives email with payout receipt
```

---

## Cross-Cutting Concerns

| Concern | Implementation |
|---------|---------------|
| **Idempotency** | All mutation endpoints accept `Idempotency-Key` header; stored in DB to prevent duplicate processing |
| **Distributed tracing** | All services propagate `X-Trace-ID` and `X-Span-ID` headers; spans emitted to Jaeger |
| **Rate limiting** | API Gateway enforces per-IP and per-token limits; 429 returned with `Retry-After` header |
| **Circuit breaking** | PaymentService and InventoryService calls wrapped in Resilience4J circuit breakers |
| **Audit logging** | Every state transition (order, ticket, payout) appended to an append-only audit_log table |
