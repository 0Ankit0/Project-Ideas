# Sequence Diagrams — Restaurant Management System

## Overview

These sequence diagrams model the end-to-end runtime behaviour of the Restaurant Management System across its core operational flows. They cover the complete order lifecycle from table seating through payment settlement, kitchen ticket orchestration across multiple stations, reservation handling and walk-in management, split-bill payment with loyalty point redemption, third-party delivery platform integration via webhooks, and automated inventory reorder triggers. Each diagram exposes the precise message contracts, state transitions, and branching logic that backend services must implement. Together they form a living specification that guides both API design and integration testing.

---

## 1. Complete Order Lifecycle — Table Seating to Payment

```mermaid
sequenceDiagram
    autonumber
    participant HT as HostTerminal
    participant WA as WaiterApp
    participant POS as POSBackend
    participant OS as OrderService
    participant MS as MenuService
    participant KS as KitchenService
    participant KDS as KDSDisplay
    participant NS as NotificationService
    participant BS as BillingService
    participant PG as PaymentGateway
    participant TS as TableService

    %% ── Host seats the party ──────────────────────────────────────────────
    HT->>TS: checkTableStatus(tableId=12)
    activate TS
    TS-->>HT: { status: "available", capacity: 4 }
    deactivate TS

    HT->>TS: seatParty(tableId=12, partySize=3, reservationId=null)
    activate TS
    TS->>TS: setStatus(tableId=12, "occupied")
    TS-->>HT: { tableId: 12, status: "occupied", sessionId: "sess_8821" }
    deactivate TS

    %% ── Waiter opens new order ───────────────────────────────────────────
    WA->>POS: openOrder(tableId=12, sessionId="sess_8821", waiterId="W04")
    activate POS
    POS->>OS: createDraftOrder(tableId=12, sessionId, waiterId)
    activate OS
    OS->>OS: generateOrderNumber("ORD-20240601-0047")
    OS->>OS: persist(order, state="draft")
    OS-->>POS: { orderId: "ord_991", orderNumber: "ORD-20240601-0047", state: "draft" }
    deactivate OS
    POS-->>WA: { orderId: "ord_991", orderNumber: "ORD-20240601-0047" }
    deactivate POS

    %% ── Waiter adds starter items ────────────────────────────────────────
    WA->>POS: addItem(orderId, itemId="ITEM-042", qty=2, modifiers=["no-onion"])
    activate POS
    POS->>MS: validateItem(itemId="ITEM-042", modifiers)
    activate MS
    MS->>MS: checkAvailability(itemId)
    MS->>MS: resolvePrice(itemId, modifiers)
    MS-->>POS: { available: true, unitPrice: 8.50, modifierDelta: 0.00 }
    deactivate MS
    POS->>OS: appendLineItem(orderId, itemId, qty=2, unitPrice=8.50, course=1)
    activate OS
    OS-->>POS: { lineItemId: "li_001", subtotal: 17.00 }
    deactivate OS
    POS-->>WA: { lineItemId: "li_001", subtotal: 17.00 }
    deactivate POS

    WA->>POS: addItem(orderId, itemId="ITEM-105", qty=1, modifiers=["extra-dressing"])
    activate POS
    POS->>MS: validateItem(itemId="ITEM-105", modifiers)
    activate MS
    MS-->>POS: { available: true, unitPrice: 7.00, modifierDelta: 0.50 }
    deactivate MS
    POS->>OS: appendLineItem(orderId, itemId, qty=1, unitPrice=7.50, course=1)
    activate OS
    OS-->>POS: { lineItemId: "li_002", subtotal: 7.50 }
    deactivate OS
    POS-->>WA: { lineItemId: "li_002", subtotal: 7.50 }
    deactivate POS

    %% ── Waiter adds main-course items ───────────────────────────────────
    WA->>POS: addItem(orderId, itemId="ITEM-210", qty=1, modifiers=["medium-rare"], course=2)
    activate POS
    POS->>MS: validateItem(itemId="ITEM-210", modifiers)
    activate MS
    MS-->>POS: { available: true, unitPrice: 24.00, modifierDelta: 0.00 }
    deactivate MS
    POS->>OS: appendLineItem(orderId, itemId, qty=1, unitPrice=24.00, course=2)
    activate OS
    OS-->>POS: { lineItemId: "li_003", subtotal: 24.00 }
    deactivate OS
    POS-->>WA: { lineItemId: "li_003" }
    deactivate POS

    WA->>POS: addItem(orderId, itemId="ITEM-310", qty=2, modifiers=[], course=3)
    activate POS
    POS->>MS: validateItem(itemId="ITEM-310", modifiers)
    activate MS
    MS-->>POS: { available: true, unitPrice: 6.50, modifierDelta: 0.00 }
    deactivate MS
    POS->>OS: appendLineItem(orderId, itemId, qty=2, unitPrice=6.50, course=3)
    activate OS
    OS-->>POS: { lineItemId: "li_004", subtotal: 13.00 }
    deactivate OS
    POS-->>WA: { lineItemId: "li_004" }
    deactivate POS

    %% ── Waiter submits order ─────────────────────────────────────────────
    WA->>POS: submitOrder(orderId="ord_991")
    activate POS
    POS->>OS: submitOrder(orderId, idempotencyKey="idem_ord991_submit")
    activate OS
    OS->>OS: validateAllLineItems()
    OS->>OS: calculateOrderTotals()
    OS->>OS: persist(order, state="submitted")
    OS->>KS: dispatchOrderToKitchen(orderId, lineItems, courseMap)
    activate KS
    KS->>KS: analyzeAndAssignStations(lineItems)
    KS->>KS: createTicket(station="grill", items=[li_003], course=2, priority=normal)
    KS->>KS: createTicket(station="salad", items=[li_001,li_002], course=1, priority=high)
    KS->>KS: createTicket(station="bar", items=[], course=1)
    KS->>KDS: displayTicket(station="salad", ticket)
    KDS-->>KS: ack
    KS->>KDS: displayTicket(station="grill", ticket)
    KDS-->>KS: ack
    KS-->>OS: { ticketIds: ["tkt_S01","tkt_G01"] }
    deactivate KS
    OS-->>POS: { orderId, state: "submitted", ticketIds }
    deactivate OS
    POS-->>WA: { state: "submitted", message: "Order sent to kitchen" }
    deactivate POS

    %% ── Course 1: Starters ready ─────────────────────────────────────────
    alt Chef accepts ticket on KDS
        KDS->>KS: ticketAccepted(ticketId="tkt_S01", chefId="C02")
        activate KS
        KS->>KS: setTicketStatus("tkt_S01", "in_preparation")
        KS->>KS: startPreparationTimer("tkt_S01")
        KS-->>KDS: ack
        deactivate KS
    end

    KDS->>KS: ticketReady(ticketId="tkt_S01")
    activate KS
    KS->>KS: setTicketStatus("tkt_S01", "ready")
    KS->>OS: courseReady(orderId, course=1)
    activate OS
    OS->>NS: notifyWaiter(waiterId="W04", message="Course 1 ready for ORD-20240601-0047")
    activate NS
    NS-->>OS: { notificationId: "ntf_01", channel: "app_push" }
    deactivate NS
    OS-->>KS: ack
    deactivate OS
    deactivate KS

    WA->>OS: markCourseServed(orderId, course=1)
    activate OS
    OS->>OS: setCourseStatus(orderId, course=1, "served")
    OS-->>WA: { orderId, course: 1, status: "served" }
    deactivate OS

    %% ── Course 2: Mains ready ────────────────────────────────────────────
    loop until all courses served
        KDS->>KS: ticketReady(ticketId="tkt_G01")
        activate KS
        KS->>KS: setTicketStatus("tkt_G01", "ready")
        KS->>OS: courseReady(orderId, course=2)
        activate OS
        OS->>NS: notifyWaiter(waiterId="W04", message="Course 2 ready")
        activate NS
        NS-->>OS: ack
        deactivate NS
        OS-->>KS: ack
        deactivate OS
        deactivate KS

        WA->>OS: markCourseServed(orderId, course=2)
        activate OS
        OS-->>WA: { orderId, course: 2, status: "served" }
        deactivate OS
    end

    %% ── Billing ──────────────────────────────────────────────────────────
    WA->>BS: openBill(orderId="ord_991")
    activate BS
    BS->>OS: getOrderDetails(orderId)
    activate OS
    OS-->>BS: { lineItems, totals }
    deactivate OS
    BS->>BS: calculateSubtotal(lineItems)
    BS->>BS: applyTax(rate=0.10)
    BS->>BS: applyServiceCharge(rate=0.05)
    BS->>BS: generateQRCode(billId)
    BS-->>WA: { billId: "bill_881", subtotal: 62.00, tax: 6.20, serviceCharge: 3.10, total: 71.30, qrCode: "<base64>" }
    deactivate BS

    WA->>PG: initiateCardPayment(billId, amount=71.30, cardToken="tok_visa_xxxx")
    activate PG
    PG->>PG: authorisePayment(amount, cardToken)

    alt Payment successful
        PG->>PG: capturePayment()
        PG-->>WA: { status: "success", transactionId: "txn_5521", amount: 71.30 }
        WA->>BS: markBillPaid(billId, transactionId="txn_5521")
        activate BS
        BS->>BS: setBillStatus("paid")
        BS-->>WA: { billId, status: "paid" }
        deactivate BS
        WA->>TS: releaseTable(tableId=12, reason="checkout")
        activate TS
        TS->>TS: setStatus(tableId=12, "cleaning")
        TS->>NS: notifyCleaningStaff(tableId=12)
        activate NS
        NS-->>TS: ack
        deactivate NS
        TS-->>WA: { tableId: 12, status: "cleaning" }
        deactivate TS
    else Payment failed
        PG-->>WA: { status: "failed", errorCode: "insufficient_funds" }
        WA->>BS: logPaymentFailure(billId, errorCode)
        activate BS
        BS-->>WA: { billId, status: "payment_pending" }
        deactivate BS
    end
    deactivate PG
```

---

## 2. Kitchen Ticket Processing Flow

```mermaid
sequenceDiagram
    autonumber
    participant WA as WaiterApp
    participant OS as OrderService
    participant KO as KitchenOrchestrator
    participant GS as GrillStation
    participant SS as SaladStation
    participant BAR as BarStation
    participant KDS as KDSDisplay
    participant NS as NotificationService

    OS->>KO: orderSubmittedEvent(orderId="ord_991", lineItems, courseMap)
    activate KO
    KO->>KO: parseLineItems(lineItems)
    KO->>KO: groupItemsByStation(lineItems)
    KO->>KO: buildCourseDAG(courseMap)

    Note over KO: Course dependency: course 1 tickets activate first,<br/>course 2 tickets hold until course 1 fully served

    KO->>KO: createTicket(station="salad", items, course=1, priority="high", slaMin=8)
    KO->>KO: createTicket(station="grill", items, course=2, priority="normal", slaMin=18)
    KO->>KO: createTicket(station="bar", items, course=1, priority="normal", slaMin=5)

    KO->>KDS: pushTicket(station="salad", ticketId="tkt_S01", items, course=1, slaMin=8)
    activate KDS
    KDS-->>KO: { displayed: true, timestamp: "T+0:00" }
    deactivate KDS

    KO->>KDS: pushTicket(station="bar", ticketId="tkt_B01", items, course=1, slaMin=5)
    activate KDS
    KDS-->>KO: { displayed: true }
    deactivate KDS

    Note over KO,GS: Grill ticket held until course 1 served
    KO->>KO: holdTicket(ticketId="tkt_G01", until="course_1_served")
    deactivate KO

    %% ── Station processing loop ──────────────────────────────────────────
    loop each station processes their ticket

        SS->>KDS: acceptTicket(ticketId="tkt_S01", chefId="C01")
        activate KDS
        KDS->>KO: ticketAccepted(ticketId="tkt_S01", chefId, acceptedAt="T+1:12")
        activate KO
        KO->>KO: setTicketStatus("tkt_S01", "in_preparation")
        KO->>KO: startSLATimer("tkt_S01", slaMin=8)
        KO-->>KDS: ack
        deactivate KO
        deactivate KDS

        BAR->>KDS: acceptTicket(ticketId="tkt_B01", chefId="C03")
        activate KDS
        KDS->>KO: ticketAccepted("tkt_B01", chefId, acceptedAt="T+1:30")
        activate KO
        KO->>KO: setTicketStatus("tkt_B01", "in_preparation")
        KO-->>KDS: ack
        deactivate KO
        deactivate KDS

        opt chef requests rush escalation
            SS->>KDS: requestRush(ticketId="tkt_S01", reason="VIP table")
            KDS->>KO: rushRequested(ticketId="tkt_S01")
            activate KO
            KO->>NS: alertKitchenManager(message="Rush requested: tkt_S01")
            activate NS
            NS-->>KO: ack
            deactivate NS
            KO->>KO: updatePriority("tkt_S01", "rush")
            deactivate KO
        end

        alt ticket becomes overdue (SLA breach)
            KO->>KO: slaTimerFired(ticketId="tkt_S01")
            activate KO
            KO->>NS: slaBreachAlert(ticketId, stationId="salad", overdueBy="2min")
            activate NS
            NS->>NS: sendAlert(channel="manager_app", severity="high")
            NS-->>KO: ack
            deactivate NS
            KO->>KDS: highlightTicket(ticketId="tkt_S01", highlight="overdue")
            activate KDS
            KDS-->>KO: ack
            deactivate KDS
            deactivate KO
        end

        SS->>KDS: markReady(ticketId="tkt_S01")
        activate KDS
        KDS->>KO: ticketReady(ticketId="tkt_S01", readyAt="T+7:45")
        activate KO
        KO->>KO: setTicketStatus("tkt_S01", "ready")
        KO->>KO: stopSLATimer("tkt_S01")
        deactivate KDS

        BAR->>KDS: markReady(ticketId="tkt_B01")
        KDS->>KO: ticketReady(ticketId="tkt_B01", readyAt="T+4:50")
        KO->>KO: setTicketStatus("tkt_B01", "ready")

        KO->>KO: checkCourseCompletion(course=1)
        Note over KO: Both tkt_S01 and tkt_B01 are ready → course 1 complete

        KO->>NS: notifyWaiter(waiterId="W04", message="Course 1 ready — ORD-20240601-0047")
        activate NS
        NS-->>KO: ack
        deactivate NS
        deactivate KO

        WA->>KO: courseServedConfirmed(orderId, course=1)
        activate KO
        KO->>KO: bumpTickets(course=1)
        KO->>KO: activateHeldTickets(course=2)
        KO->>KDS: pushTicket(station="grill", ticketId="tkt_G01", items, course=2, slaMin=18)
        activate KDS
        KDS-->>KO: { displayed: true }
        deactivate KDS
        deactivate KO

        GS->>KDS: acceptTicket(ticketId="tkt_G01", chefId="C02")
        KDS->>KO: ticketAccepted("tkt_G01", chefId)
        activate KO
        KO->>KO: setTicketStatus("tkt_G01", "in_preparation")
        KO->>KO: startSLATimer("tkt_G01", slaMin=18)
        deactivate KO

        GS->>KDS: markReady(ticketId="tkt_G01")
        KDS->>KO: ticketReady("tkt_G01")
        activate KO
        KO->>KO: setTicketStatus("tkt_G01", "ready")
        KO->>KO: checkCourseCompletion(course=2)
        KO->>NS: notifyWaiter(waiterId="W04", message="Course 2 ready")
        activate NS
        NS-->>KO: ack
        deactivate NS
        deactivate KO
    end
```

---

## 3. Reservation to Seating Flow

```mermaid
sequenceDiagram
    autonumber
    participant CA as CustomerApp
    participant RS as ReservationService
    participant TS as TableService
    participant NS as NotificationService
    participant HT as HostTerminal
    participant WI as WalkInService
    participant WLS as WaitlistService

    %% ── Availability check ───────────────────────────────────────────────
    CA->>RS: checkAvailability(date="2024-06-15", time="19:30", partySize=4)
    activate RS
    RS->>TS: queryAvailableSlots(date, time, partySize=4)
    activate TS
    TS->>TS: runCapacityQuery(date, time, partySize)
    TS-->>RS: { slots: [{ time:"19:00", tableId:8 }, { time:"19:30", tableId:12 }, { time:"20:00", tableId:5 }] }
    deactivate TS
    RS->>RS: applyBufferRules(slots)
    RS-->>CA: { availableSlots: [{ time:"19:30", estimatedTableId:12, indoorOutdoor:"indoor" }] }
    deactivate RS

    %% ── Customer creates reservation ─────────────────────────────────────
    CA->>RS: createReservation(slotId, partySize=4, name="Alice", phone="+1-555-0101", email="alice@example.com", notes="window seat preferred")
    activate RS
    RS->>RS: validateSlotStillAvailable(slotId)
    RS->>TS: softHoldTable(tableId=12, durationMin=5)
    activate TS
    TS-->>RS: { holdId: "hold_551", expiresAt: "T+5min" }
    deactivate TS
    RS->>RS: generateConfirmationCode("RES-240615-8801")
    RS->>RS: persist(reservation, state="confirmed", confirmationCode)
    RS->>NS: sendConfirmation(channel="sms", phone, confirmationCode, date, time)
    activate NS
    NS-->>RS: { messageId: "msg_221" }
    deactivate NS
    RS->>NS: sendConfirmation(channel="email", email, confirmationCode, details)
    activate NS
    NS-->>RS: { messageId: "msg_222" }
    deactivate NS
    RS-->>CA: { reservationId: "res_8801", confirmationCode: "RES-240615-8801", state: "confirmed" }
    deactivate RS

    %% ── Reminder (day-of) ────────────────────────────────────────────────
    RS->>NS: sendReminder(reservationId, channel="sms", hoursAhead=2)
    activate NS
    NS-->>RS: { messageId: "msg_330" }
    deactivate NS

    %% ── Customer arrives ─────────────────────────────────────────────────
    CA->>HT: checkIn(confirmationCode="RES-240615-8801")
    activate HT
    HT->>RS: lookupReservation(confirmationCode)
    activate RS
    RS-->>HT: { reservationId: "res_8801", partySize:4, tableId:12, name:"Alice", state:"confirmed" }
    deactivate RS

    HT->>TS: checkTableReady(tableId=12)
    activate TS
    TS-->>HT: { tableId:12, status: "available" }
    deactivate TS

    alt table is immediately available
        HT->>TS: seatParty(tableId=12, reservationId="res_8801", partySize=4)
        activate TS
        TS->>TS: setStatus(tableId=12, "occupied")
        TS-->>HT: { sessionId: "sess_9901" }
        deactivate TS
        HT->>RS: updateReservationStatus(reservationId, state="seated", tableId=12, seatedAt=now)
        activate RS
        RS-->>HT: { state: "seated" }
        deactivate RS
        HT->>NS: notifyWaiter(waiterId="W04", message="Party seated at table 12 — res_8801")
        activate NS
        NS-->>HT: ack
        deactivate NS
    else table not yet ready (still being cleared)
        HT->>WLS: addToWaitlist(reservationId, partySize=4, estimatedWaitMin=10)
        activate WLS
        WLS-->>HT: { waitlistPosition: 1, estimatedWaitMin: 10 }
        deactivate WLS
        HT->>NS: notifyGuest(phone, message="Table almost ready, est. 10 min")
        activate NS
        NS-->>HT: ack
        deactivate NS

        TS->>HT: tableReadyEvent(tableId=12)
        HT->>WLS: dequeueNext(tableId=12)
        activate WLS
        WLS-->>HT: { reservationId: "res_8801" }
        deactivate WLS
        HT->>TS: seatParty(tableId=12, reservationId, partySize=4)
        activate TS
        TS->>TS: setStatus(tableId=12, "occupied")
        TS-->>HT: { sessionId: "sess_9901" }
        deactivate TS
        HT->>RS: updateReservationStatus(reservationId, state="seated")
        activate RS
        RS-->>HT: ack
        deactivate RS
    end
    deactivate HT

    %% ── No-show handling ─────────────────────────────────────────────────
    opt no-show after 15-minute grace period
        RS->>RS: graceTimerFired(reservationId="res_8801")
        activate RS
        RS->>RS: updateReservationStatus(reservationId, state="no_show")
        RS->>TS: releaseTableHold(tableId=12)
        activate TS
        TS->>TS: setStatus(tableId=12, "available")
        TS-->>RS: ack
        deactivate TS
        RS->>NS: notifyManager(message="No-show: res_8801 — table 12 released")
        activate NS
        NS-->>RS: ack
        deactivate NS
        deactivate RS
    end
```

---

## 4. Split Bill Payment Flow

```mermaid
sequenceDiagram
    autonumber
    participant WA as WaiterApp
    participant BS as BillingService
    participant PG as PaymentGateway
    participant LS as LoyaltyService
    participant NS as NotificationService
    participant CD as CashDrawerService

    WA->>BS: requestBill(orderId="ord_991", tableId=12)
    activate BS
    BS->>BS: calculateSubtotal(lineItems)
    BS->>BS: applyTax(rate=0.10)
    BS->>BS: applyServiceCharge(rate=0.05)
    BS-->>WA: { billId:"bill_881", subtotal:62.00, tax:6.20, serviceCharge:3.10, total:71.30 }
    deactivate BS

    WA->>BS: splitBill(billId="bill_881", splitType="by_items")
    activate BS

    alt split evenly (N guests)
        BS->>BS: divideTotal(total=71.30, guests=3)
        BS->>BS: createSplitPayments([{ guestRef:1, amount:23.77 }, { guestRef:2, amount:23.77 }, { guestRef:3, amount:23.76 }])
    else split by items
        BS->>BS: assignLineItems(guest=1, items=["li_001","li_003"])
        BS->>BS: assignLineItems(guest=2, items=["li_002"])
        BS->>BS: assignLineItems(guest=3, items=["li_004"])
        BS->>BS: calculateSplitTotals(applyTaxProRata=true)
        BS->>BS: createSplitPayments([{ guestRef:1, amount:35.09 }, { guestRef:2, amount:13.13 }, { guestRef:3, amount:23.08 }])
    end
    BS-->>WA: { splits: [{ splitId:"sp_1", amount:35.09 }, { splitId:"sp_2", amount:13.13 }, { splitId:"sp_3", amount:23.08 }] }
    deactivate BS

    %% ── Guest 1: credit card ─────────────────────────────────────────────
    WA->>PG: authorisePayment(splitId="sp_1", amount=35.09, cardToken="tok_mc_g1")
    activate PG
    PG->>PG: runAuthorisationCheck(cardToken, amount)
    PG->>PG: capturePayment()
    PG-->>WA: { status:"success", transactionId:"txn_001", amount:35.09 }
    deactivate PG

    WA->>BS: recordSplitPayment(splitId="sp_1", transactionId="txn_001", method="card")
    activate BS
    BS->>BS: setSplitStatus("sp_1", "paid")
    BS-->>WA: ack
    deactivate BS

    %% ── Guest 2: partial loyalty + card ─────────────────────────────────
    WA->>LS: getPointsBalance(guestId="G002")
    activate LS
    LS-->>WA: { points:500, monetaryValue:5.00, redemptionRate:0.01 }
    deactivate LS

    WA->>LS: redeemPoints(guestId="G002", points=500, splitId="sp_2")
    activate LS
    LS->>LS: validateRedemption(guestId, points, monetaryValue=5.00)
    LS->>LS: deductPoints(guestId, points=500)
    LS->>LS: recordTransaction(guestId, type="redemption", amount=-5.00, splitId)
    LS-->>WA: { redeemed:true, monetaryValue:5.00, remainingBalance:8.13 }
    deactivate LS

    WA->>PG: authorisePayment(splitId="sp_2", amount=8.13, cardToken="tok_visa_g2")
    activate PG
    PG->>PG: capturePayment()
    PG-->>WA: { status:"success", transactionId:"txn_002", amount:8.13 }
    deactivate PG

    WA->>BS: recordSplitPayment(splitId="sp_2", transactionId="txn_002", loyaltyApplied=5.00, method="card+loyalty")
    activate BS
    BS->>BS: setSplitStatus("sp_2", "paid")
    BS-->>WA: ack
    deactivate BS

    %% ── Guest 3: cash ────────────────────────────────────────────────────
    WA->>CD: recordCashPayment(splitId="sp_3", amountTendered=25.00, changeGiven=1.92)
    activate CD
    CD->>CD: openDrawer()
    CD->>CD: recordTransaction(splitId, tendered=25.00, change=1.92)
    CD-->>WA: { transactionId:"cash_003", drawerBalance: "+25.00" }
    deactivate CD

    WA->>BS: recordSplitPayment(splitId="sp_3", transactionId="cash_003", method="cash")
    activate BS
    BS->>BS: setSplitStatus("sp_3", "paid")
    BS->>BS: checkAllSplitsPaid(billId="bill_881")
    BS->>BS: setBillStatus("paid")
    BS-->>WA: { billId:"bill_881", status:"paid", allSplitsPaid:true }
    deactivate BS

    %% ── Award loyalty points ─────────────────────────────────────────────
    BS->>LS: awardPoints(guestId="G001", amount=35.09, billId)
    activate LS
    LS->>LS: calculatePoints(amount=35.09, rate=1pt_per_dollar)
    LS->>LS: creditPoints(guestId="G001", points=35)
    LS-->>BS: { guestId:"G001", pointsAwarded:35 }
    deactivate LS

    BS->>LS: awardPoints(guestId="G002", amount=13.13, billId)
    activate LS
    LS->>LS: creditPoints(guestId="G002", points=13)
    LS-->>BS: ack
    deactivate LS

    BS->>LS: awardPoints(guestId="G003", amount=23.08, billId)
    activate LS
    LS->>LS: creditPoints(guestId="G003", points=23)
    LS-->>BS: ack
    deactivate LS

    %% ── Receipts ─────────────────────────────────────────────────────────
    BS->>NS: sendReceipts(billId, splits, channel="email")
    activate NS
    NS->>NS: sendEmail(guest="G001", receipt)
    NS->>NS: sendEmail(guest="G002", receipt)
    NS->>NS: sendEmail(guest="G003", receipt)
    NS-->>BS: { sent:3, failed:0 }
    deactivate NS
```

---

## 5. Delivery Order Integration Flow

```mermaid
sequenceDiagram
    autonumber
    participant DP as DeliveryPlatform
    participant DWH as DeliveryWebhookHandler
    participant DS as DeliveryService
    participant OS as OrderService
    participant KS as KitchenService
    participant NS as NotificationService
    participant DD as DeliveryDriver

    DP->>DWH: POST /webhooks/delivery/new-order (payload, X-Signature: hmac_sha256)
    activate DWH
    DWH->>DWH: validateHMACSignature(payload, secret, receivedSig)
    DWH->>DWH: parsePayload(payload)
    DWH->>DS: processNewDeliveryOrder(platformOrderId="DLV-9901", payload)
    activate DS

    DS->>DS: checkIdempotency(platformOrderId)
    DS->>DS: createDeliveryOrder(platformOrderId, externalRef, estimatedPickupMin=25)
    DS->>OS: createLinkedOrder(deliveryOrderId, items=payload.items, source="delivery_platform")
    activate OS
    OS->>OS: generateOrderNumber("ORD-DEL-20240601-0012")
    OS->>OS: createLineItems(items)
    OS->>OS: persist(order, state="submitted", type="delivery")
    OS->>KS: dispatchOrderToKitchen(orderId, items, priority="delivery")
    activate KS
    KS->>KS: createTickets(items, flagDelivery=true)
    KS-->>OS: { ticketIds: ["tkt_DEL_01"] }
    deactivate KS
    OS-->>DS: { orderId: "ord_del_001", orderNumber }
    deactivate OS

    DS->>DP: sendAcknowledgment(platformOrderId, status="accepted", estimatedPickupMin=25)
    activate DP
    DP-->>DS: { ackId: "ack_9901" }
    deactivate DP
    DS-->>DWH: { deliveryOrderId:"dlvord_001", linked: true }
    deactivate DS
    DWH-->>DP: HTTP 200 OK
    deactivate DWH

    %% ── Kitchen prepares order ───────────────────────────────────────────
    Note over KS,NS: KDS displays order with 🛵 delivery flag

    KS->>NS: notifyKitchenDisplay(ticketId="tkt_DEL_01", flag="delivery", estimatedPickupMin=25)
    activate NS
    NS-->>KS: ack
    deactivate NS

    KS->>DS: ticketReady(ticketId="tkt_DEL_01", orderId)
    activate DS
    DS->>DS: setDeliveryOrderStatus("dlvord_001", "ready_for_pickup")
    DS->>DP: notifyPlatformOrderReady(platformOrderId="DLV-9901")
    activate DP
    DP-->>DS: ack
    deactivate DP
    DS->>NS: notifyStaff(message="Delivery order DLV-9901 ready for pickup")
    activate NS
    NS-->>DS: ack
    deactivate NS
    deactivate DS

    %% ── Driver arrives ───────────────────────────────────────────────────
    DD->>DS: driverArrived(deliveryOrderId="dlvord_001", driverId="DRV-441")
    activate DS
    DS->>DS: recordDriverArrival(deliveryOrderId, driverId, arrivedAt=now)
    DS-->>DD: { orderId: "dlvord_001", items: [...], pickupCode: "8821" }
    deactivate DS

    DD->>DS: confirmPickup(deliveryOrderId, pickupCode="8821")
    activate DS
    DS->>DS: verifyPickupCode(deliveryOrderId, pickupCode)
    DS->>DS: setDeliveryOrderStatus("dlvord_001", "picked_up")
    DS->>OS: updateOrderStatus(orderId, state="out_for_delivery")
    activate OS
    OS-->>DS: ack
    deactivate OS
    DS-->>DD: { confirmed: true, customerAddress: "123 Main St" }
    deactivate DS

    %% ── Delivery events ──────────────────────────────────────────────────
    DD->>DP: updateDeliveryStatus(platformOrderId, status="out_for_delivery")
    activate DP
    DP-->>DD: ack
    deactivate DP

    DP->>DWH: POST /webhooks/delivery/status-update (platformOrderId, status="delivered")
    activate DWH
    DWH->>DWH: validateHMACSignature(payload, secret, receivedSig)
    DWH->>DS: processStatusUpdate(platformOrderId, status="delivered")
    activate DS
    DS->>DS: setDeliveryOrderStatus("dlvord_001", "delivered")
    DS->>OS: completeOrder(orderId, completedAt=now)
    activate OS
    OS->>OS: setOrderStatus(orderId, "completed")
    OS-->>DS: ack
    deactivate OS
    DS->>NS: sendDeliveryConfirmation(customerId, message="Your order has been delivered!")
    activate NS
    NS-->>DS: ack
    deactivate NS
    DS-->>DWH: processed
    deactivate DS
    DWH-->>DP: HTTP 200 OK
    deactivate DWH

    %% ── Failed delivery ──────────────────────────────────────────────────
    alt failed delivery webhook received
        DP->>DWH: POST /webhooks/delivery/status-update (status="failed", reason="customer_not_found")
        activate DWH
        DWH->>DS: processStatusUpdate(platformOrderId, status="failed")
        activate DS
        DS->>DS: setDeliveryOrderStatus("dlvord_001", "failed")
        DS->>OS: markOrderFailed(orderId, reason="delivery_failed")
        activate OS
        OS-->>DS: ack
        deactivate OS
        DS->>NS: initiateRefundAlert(platformOrderId, customerId, amount)
        activate NS
        NS-->>DS: ack
        deactivate NS
        DS-->>DWH: processed
        deactivate DS
        DWH-->>DP: HTTP 200 OK
        deactivate DWH
    end
```

---

## 6. Inventory Reorder Flow

```mermaid
sequenceDiagram
    autonumber
    participant OS as OrderService
    participant IS as InventoryService
    participant SM as StockMonitor
    participant SS as SupplierService
    participant POS as PurchaseOrderService
    participant NS as NotificationService
    participant BM as BranchManager
    participant SUP as Supplier

    OS->>IS: orderSubmittedEvent(orderId="ord_991", lineItems)
    activate IS
    IS->>IS: lookupRecipes(lineItems)
    IS->>IS: deductIngredients(recipe="burger", qty=2, ingredients=[{ id:"ING-001", deduct:0.4kg }, { id:"ING-022", deduct:0.1kg }])
    IS->>IS: deductIngredients(recipe="salad", qty=1, ingredients=[{ id:"ING-045", deduct:0.08kg }])
    IS->>IS: persist(stockMovements, type="consumption", orderId)
    IS->>SM: checkStockLevels(ingredientIds=["ING-001","ING-022","ING-045"])
    activate SM
    deactivate IS

    SM->>SM: evaluateLevels([{ id:"ING-001", current:1.2kg, reorderPoint:2.0kg, reorderQty:10kg }, ...])
    SM->>SM: identifyBelowReorderPoint(ING-001)
    SM->>NS: lowStockAlert(ingredientId="ING-001", name="Ground Beef", current:1.2kg, reorderPoint:2.0kg)
    activate NS
    NS->>BM: sendAlert(channel="manager_app", message="Low stock: Ground Beef 1.2kg remaining")
    BM-->>NS: alertReceived
    NS-->>SM: ack
    deactivate NS

    opt auto-reorder enabled for ING-001
        SM->>SS: getPreferredSupplier(ingredientId="ING-001")
        activate SS
        SS->>SS: lookupSupplierContract(ingredientId)
        SS-->>SM: { supplierId:"SUP-12", name:"FreshMeats Co.", unitCost:4.50, minOrderKg:5, leadDays:2 }
        deactivate SS

        SM->>POS: createDraftPO(supplierId="SUP-12", branchId, requestedBy="auto_reorder")
        activate POS
        POS->>POS: generatePONumber("PO-20240602-0018")
        POS->>POS: persist(po, state="draft")
        POS-->>SM: { poId:"po_0018", poNumber:"PO-20240602-0018" }
        deactivate POS

        SM->>POS: addPOItem(poId, ingredientId="ING-001", qty=10kg, unitCost=4.50, totalCost=45.00)
        activate POS
        POS->>POS: appendLineItem(poId, ingredientId, qty, unitCost)
        POS-->>SM: { poLineId:"pol_001", totalCost:45.00 }
        deactivate POS

        SM->>POS: submitPO(poId="po_0018", requiresApproval=true)
        activate POS
        POS->>POS: setPOStatus("po_0018", "pending_approval")
        POS->>NS: requestManagerApproval(poId, managerId="MGR-01", totalCost=45.00)
        activate NS
        NS->>BM: sendApprovalRequest(poId, details)
        BM-->>NS: approved(poId)
        NS-->>POS: { approved:true, approvedBy:"MGR-01", approvedAt:now }
        deactivate NS
        POS->>POS: setPOStatus("po_0018", "approved")
        deactivate POS

        POS->>SS: transmitPO(poId="po_0018", supplierId="SUP-12")
        activate SS
        SS->>SUP: sendPOEmail(poId, poNumber, items, deliveryDate)
        SUP-->>SS: { confirmation: "SUP-CONF-7721", expectedDelivery:"2024-06-04" }
        SS-->>POS: { transmitted:true, supplierRef:"SUP-CONF-7721", expectedDelivery:"2024-06-04" }
        deactivate SS

        POS->>POS: setPOStatus("po_0018", "sent_to_supplier")
        POS->>NS: notifyManager(message="PO-20240602-0018 sent to FreshMeats Co. Expected 2024-06-04")
        activate NS
        NS-->>POS: ack
        deactivate NS
    end
    deactivate SM

    %% ── Goods receipt on delivery day ────────────────────────────────────
    BM->>POS: receiveGoods(poId="po_0018", items=[{ ingredientId:"ING-001", receivedQty:10kg, unitCost:4.50 }], receivedBy="STF-03")
    activate POS
    POS->>POS: createGoodsReceipt(poId, items, receivedAt=now)
    POS->>POS: setPOStatus("po_0018", "received")
    POS->>IS: updateIngredientStock(ingredientId="ING-001", deltaQty=+10kg, type="purchase_receipt", poId)
    activate IS
    IS->>IS: addStockQuantity("ING-001", 10kg)
    IS->>IS: updateAverageCost("ING-001", unitCost=4.50)
    IS->>IS: persist(stockMovement, type="purchase_receipt", poId, qty=10kg, cost=4.50)
    IS->>SM: reevaluateStockLevels(ingredientIds=["ING-001"])
    activate SM
    SM->>SM: checkLevels([{ id:"ING-001", current:11.2kg, reorderPoint:2.0kg }])
    SM->>SM: clearLowStockFlag(ingredientId="ING-001")
    SM->>NS: clearAlert(ingredientId="ING-001", message="Stock replenished: Ground Beef now 11.2kg")
    activate NS
    NS-->>SM: ack
    deactivate NS
    SM-->>IS: levelsOk
    deactivate SM
    IS-->>POS: { updated:true, newLevel:11.2kg }
    deactivate IS
    POS-->>BM: { poId:"po_0018", status:"received", goodsReceiptId:"GR-0018" }
    deactivate POS
```

---

## Sequence Flow Notes

### Idempotency

All mutating operations exposed via API (order submit, payment capture, goods receipt) accept an `idempotency_key` header. The backend persists the key and result for 24 hours. Duplicate requests within that window receive the cached response without re-executing side effects. This protects against network retries causing duplicate charges or double-deductions.

### Event-Driven Communication

Services communicate via domain events published to an internal message broker (e.g., Kafka topics). `order.submitted`, `ticket.ready`, `bill.paid`, and `stock.low` are canonical events. Consumers subscribe independently, allowing the kitchen orchestrator, notification service, and inventory service to react to order submission without synchronous coupling to the OrderService request path.

### Optimistic Locking

`Order` and `Bill` records carry a `version` integer. Concurrent updates (e.g., two waiters modifying the same order) must include the last-known `version`. The backend rejects updates where `version` does not match the current row, returning `409 Conflict`. Clients retry after re-fetching the latest state.

### SLA Monitoring

Each kitchen ticket records `accepted_at` and `sla_minutes`. A background scheduler evaluates in-progress tickets every 30 seconds. Tickets that exceed 80% of their SLA trigger a **warning** notification; tickets that breach 100% trigger a **critical** alert routed to the kitchen manager's dashboard and mobile app.

### Webhook Retry Policy

Inbound webhooks (delivery platform, payment gateway callbacks) must respond with HTTP 200 within 5 seconds. If the handler cannot process synchronously, it enqueues the payload and returns 200 immediately. Outbound webhook calls to suppliers and delivery platforms use exponential back-off: 5 s → 25 s → 125 s → 625 s, with a maximum of 5 attempts before routing the message to a dead letter queue (DLQ).

### Dead Letter Queue Handling

Messages that exhaust all retry attempts are routed to a DLQ topic (`rms.dlq`). A monitoring alert fires when DLQ depth exceeds 10 messages. On-call engineers inspect failed payloads via an admin UI, correct the root cause, and replay messages individually or in bulk. DLQ messages retain the original headers (idempotency key, correlation ID) to ensure safe replay.

### Table State Machine

Tables transition through `available → occupied → cleaning → available`. The `cleaning` state is only exited by an explicit staff confirmation via the HostTerminal. Attempting to seat a party at a table in `cleaning` state returns `409 Table Not Ready`. This prevents accidental double-seating during turnaround.

### Reservation Grace Period

The no-show grace timer is set per-venue configuration (default 15 minutes). The timer starts when the reservation time passes and no `arrived` event has been received. The timer is cancelled immediately on customer check-in. No-show records are retained for analytics and can trigger automated follow-up communications via the NotificationService.

### Delivery Order Prioritisation

Orders originating from delivery platforms carry `priority: "delivery"` and are flagged on the KDS with a distinct visual indicator. Kitchen SLAs for delivery tickets are tighter (typically 20–25 minutes end-to-end) to account for driver wait time and thermal degradation during transit.

### Loyalty Point Award Timing

Points are awarded after `bill.paid` event is emitted — not at payment authorisation. This prevents awarding points for payments that are later reversed. Redemptions are validated against the live balance at the time of the split payment request to avoid over-redemption from concurrent sessions.
