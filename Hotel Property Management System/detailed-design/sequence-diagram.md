# Hotel Property Management System — Detailed Sequence Diagrams

This document describes the three most operationally critical workflows in the Hotel Property
Management System using detailed sequence diagrams. Each section opens with a thorough prose
description covering the full happy path, all identified error cases, and the business rules
that govern each decision point, followed by a complete Mermaid sequence diagram with
`alt`, `opt`, and `loop` blocks for branching logic.

---

## 1. OTA Booking Receipt

### Description

The OTA Booking Receipt workflow is triggered whenever a booking is submitted through an Online
Travel Agency (OTA) such as Booking.com, Expedia, Agoda, or MakeMyTrip. The message arrives at
the **ChannelManagerService** via a channel-specific adapter — either a real-time push (OTA API
webhook), a scheduled pull (OTA XML feed), or a direct API call from the OTA's connectivity layer.

**Step 1 — Channel authentication and deduplication.**  
The ChannelManagerService first validates the channel's API credentials (API key or OAuth token).
On success it constructs an `OTABooking` record and immediately checks for an existing record
matching the same `(otaName, otaReservationId)` pair. OTAs occasionally re-deliver the same
booking due to network timeouts or retry logic; without duplicate detection, the property would
end up double-booked and the guest would receive two confirmation emails.

**Step 2 — Availability verification.**  
`ReservationService` calls `InventoryService` to check the real-time available count for the
requested room type, property, and date range. Inventory is maintained as a count per
(property, room_type, date) cell and is decremented on each confirmed reservation. If the count
is zero, the booking is rejected immediately with a `ROOM_TYPE_UNAVAILABLE` error code so the
OTA can present alternative dates or room types to the guest.

**Step 3 — Rate plan validation.**  
`RatePlanService` verifies that the rate plan code sent by the OTA is active for the requested
dates and property, that all minimum-stay and advance-purchase restrictions are satisfied, and
that the rate value in the OTA message is within the expected tolerance of the HPMS-computed rate
(to catch mapping or currency errors). If the rate plan is expired, restricted, or the price is
outside tolerance, the booking is rejected with `INVALID_RATE_PLAN`.

**Step 4 — Guest profile management.**  
`GuestService.findOrCreate()` searches for an existing guest profile by email address. If found,
the profile is updated with any new information provided in the OTA message (phone, nationality,
special requests). If not found, a new `Guest` record is created. This step ensures guest
history and loyalty membership are attached to every reservation regardless of booking source.

**Step 5 — Reservation and folio creation.**  
`ReservationService.createReservation()` generates the confirmation number, creates the
`Reservation` aggregate with `CONFIRMED` status, builds `RoomAllocation` records, and calls
`FolioService.initializeFolio()` to open the financial ledger. On folio initialisation, a
nightly room-rate posting schedule is registered for the night-audit process.

**Step 6 — Inventory decrement.**  
`InventoryService.decrementAvailability()` atomically decrements the availability count for each
night of the stay. This operation uses a database-level compare-and-swap to prevent race
conditions when two bookings for the same room type arrive simultaneously.

**Step 7 — Notifications.**  
`NotificationService` dispatches a booking confirmation email to the guest with the HPMS
confirmation number. The ChannelManagerService then acknowledges the booking back to the OTA
channel with both the OTA's reservation ID and the HPMS confirmation number, closing the
acknowledgement loop and preventing the OTA from retrying the delivery.

**Error cases:**
- **Duplicate booking:** An `OTABooking` with the same `(otaName, otaReservationId)` already
  exists. Return the existing HPMS confirmation number to the OTA and mark the incoming message
  as a duplicate without creating a new reservation.
- **Room type unavailable:** Availability count is zero or a pre-existing confirmed reservation
  occupies all rooms of that type. Reject with `422 ROOM_TYPE_UNAVAILABLE`.
- **Invalid rate plan:** Rate plan code is unknown, expired, restricted for the requested dates,
  or the OTA-quoted price is outside the acceptable variance threshold. Reject with
  `422 INVALID_RATE_PLAN`.
- **Guest creation failure:** Email format invalid or ID document validation fails. Reject with
  `400 INVALID_GUEST_DATA`.
- **Inventory race condition:** Two concurrent bookings attempt to decrement below zero. The
  second booking is rolled back and rejected with `409 INVENTORY_CONFLICT`.

```mermaid
sequenceDiagram
    autonumber
    participant OTA  as OTAChannel
    participant CMS  as ChannelManagerService
    participant RS   as ReservationService
    participant GS   as GuestService
    participant IS   as InventoryService
    participant RPS  as RatePlanService
    participant FS   as FolioService
    participant NS   as NotificationService

    OTA->>CMS: POST /channels/bookings<br/>{otaName, otaReservationId, propertyId,<br/>roomTypeCode, ratePlanCode, ratePlanPrice,<br/>guestInfo, checkIn, checkOut, adults, children,<br/>specialRequests, channelToken}

    CMS->>CMS: validateChannelCredentials(channelToken)

    alt Invalid channel credentials
        CMS-->>OTA: 401 Unauthorized {code: INVALID_CHANNEL_TOKEN}
    end

    CMS->>CMS: findOTABooking(otaName, otaReservationId)

    alt Duplicate booking detected
        CMS-->>OTA: 200 OK {code: DUPLICATE,<br/>existingConfirmationNumber, mappedReservationId}
        Note over CMS: No further processing — idempotent response
    end

    CMS->>IS: checkAvailability(propertyId, roomTypeCode, checkIn, checkOut)
    IS-->>CMS: {available: count, remainingRooms: [...]}

    alt Room type unavailable (count == 0)
        CMS->>CMS: updateOTABookingStatus(REJECTED)
        CMS-->>OTA: 422 Unprocessable Entity<br/>{code: ROOM_TYPE_UNAVAILABLE, roomTypeCode}
    end

    CMS->>RPS: validateRatePlan(propertyId, ratePlanCode, checkIn, checkOut, ratePlanPrice)
    RPS-->>CMS: {valid: bool, computedRate, variance, restrictions}

    alt Invalid rate plan or price out of tolerance
        CMS->>CMS: updateOTABookingStatus(REJECTED)
        CMS-->>OTA: 422 Unprocessable Entity<br/>{code: INVALID_RATE_PLAN, ratePlanCode, detail}
    end

    CMS->>GS: findOrCreate(email, firstName, lastName, phone, nationality, idType, idNumber)
    GS->>GS: lookupByEmail(email)

    alt Guest exists
        GS->>GS: mergeProfile(existingGuest, incomingData)
        GS-->>CMS: {guest, action: UPDATED}
    else New guest
        GS->>GS: createGuest(guestData)
        GS-->>CMS: {guest, action: CREATED}
    end

    CMS->>RS: createReservation({propertyId, guestId, roomTypeCode,<br/>ratePlanCode, checkIn, checkOut,<br/>adults, children, specialRequests, source: OTA})

    RS->>RS: generateConfirmationNumber(propertyCode)
    RS->>RS: buildRoomAllocations(roomTypeCode, nights, pricePerNight)

    RS->>IS: decrementAvailability(propertyId, roomTypeCode, checkIn, checkOut)

    alt Inventory race condition (optimistic lock failure)
        IS-->>RS: OptimisticLockException
        RS->>RS: rollbackReservation()
        RS-->>CMS: 409 Conflict {code: INVENTORY_CONFLICT}
        CMS-->>OTA: 409 Conflict {code: INVENTORY_CONFLICT}
    end

    IS-->>RS: {decremented: true, newAvailability}

    RS->>FS: initializeFolio(reservationId, guestId, propertyId, currency)
    FS->>FS: createFolio(status: OPEN)
    FS->>FS: registerNightlyPostingSchedule(reservationId, checkIn, checkOut)
    FS-->>RS: {folio}

    RS->>RS: persistReservation(status: CONFIRMED)
    RS-->>CMS: {reservation, confirmationNumber}

    CMS->>CMS: updateOTABooking(status: PROCESSED, mappedReservationId)

    par Notifications in parallel
        CMS->>NS: sendGuestConfirmation(guestId, reservationId, confirmationNumber)
        NS-->>CMS: {dispatched: true, channel: EMAIL}
    and
        CMS->>OTA: acknowledge(otaReservationId, hpmsConfirmationNumber, status: CONFIRMED)
        OTA-->>CMS: 200 OK {ackReceived: true}
    end

    opt Loyalty member detected
        CMS->>NS: sendLoyaltyWelcomeBack(guestId, loyaltyTier, pointsBalance)
    end

    Note over CMS: OTABooking record updated to PROCESSED.<br/>Reservation is CONFIRMED and inventory is decremented.
```

---

## 2. Payment Processing at Checkout

### Description

The payment-at-checkout workflow begins when a front-desk agent initiates guest departure from the
Property Management System UI. This is the most financially sensitive workflow in the system; every
step carries strict validation rules and clear rollback semantics to protect both the guest and the
property.

**Step 1 — Finalise charges.**  
`FolioService.finalizeCharges()` performs a late-charge sweep: it posts any room service, minibar,
or parking charges that were recorded against the reservation but not yet formally posted to the
folio. It also triggers the final night's room rate posting if the checkout occurs before the
night-audit scheduler has run.

**Step 2 — Tax calculation.**  
`FolioService.calculateTax()` applies the property's tax configuration to all unprocessed charges:
GST/VAT at applicable slab rates, city tax (where applicable), tourism levy, and service charge.
Tax entries are posted as separate `FolioCharge` records with `chargeType = ROOM_TAX` or
`CITY_TAX`, keeping the base rate and the tax portion individually visible on the invoice.

**Step 3 — Optional folio split.**  
If the guest has a corporate agreement covering room and tax while personal incidentals are
self-paid, the front-desk agent selects the incidental charges and triggers `FolioService.split()`.
This creates a second folio, transfers the selected charges, and updates both folio balances. Both
folios must reach zero balance before the reservation can be checked out.

**Step 4 — Payment collection.**  
The front-desk agent presents the balance to the guest and selects the payment method. For card
payments, the UI sends the tokenised card reference (PCI-compliant token, never the raw PAN) and
the amount to `PaymentGateway.charge()`. The gateway returns a transaction reference and
authorisation code on success.

**Step 5 — Partial payment handling.**  
If the guest tenders less than the full balance (e.g., uses points for part of the bill), a
partial payment is posted. The remaining balance must be settled before `close()` is called.
Multiple payments of different types (cash + card) are supported on a single folio.

**Step 6 — Folio close and reservation update.**  
On full payment, `FolioService.close()` sets `status = CLOSED` and `closedAt` to the current
timestamp. `ReservationService.updateStatus(CHECKED_OUT)` transitions the reservation, triggers
room release, and schedules a `CHECKOUT_SERVICE` housekeeping task at `HIGH` priority.

**Step 7 — Loyalty points award.**  
`LoyaltyService.awardPoints()` calculates the points earned from the stay based on the total
settled amount, tier multiplier, and any promotional earn campaigns active during the stay period.
Points are credited to the `LoyaltyAccount` and an upgrade check is performed.

**Step 8 — Receipt delivery.**  
`NotificationService.sendReceipt()` dispatches a digital invoice via email and, if opted in, an
SMS summary to the guest. The invoice carries the property's GST/VAT registration number, a
sequential fiscal invoice number, and an itemised charge breakdown.

**Error cases:**
- **Payment decline:** The payment gateway returns a decline code. The folio remains `OPEN` for
  retry with an alternative payment method. An error message is surfaced to the front-desk agent.
- **Partial payment:** Posting partial payment leaves a non-zero balance. The folio stays `OPEN`
  until the residual is settled. Multiple payments are accumulated until balance reaches zero.
- **Folio dispute:** After checkout, the guest disputes a charge. The folio transitions to
  `DISPUTED`. A supervisor must review and either void the charge (posting a credit) or reject the
  dispute, then transition the folio back to `CLOSED` or `ADJUSTED`.
- **Gateway timeout:** If the payment gateway call times out, the system checks for a
  pending-transaction record at the gateway before either confirming or reversing. Idempotency
  keys prevent double-charging on retry.

```mermaid
sequenceDiagram
    autonumber
    participant FDA  as FrontDeskAgent (UI)
    participant FS   as FolioService
    participant PG   as PaymentGateway
    participant RS   as ReservationService
    participant LS   as LoyaltyService
    participant NS   as NotificationService
    participant HKS  as HousekeepingService

    FDA->>FS: initiateCheckout(reservationId, agentId)
    FS->>FS: loadFolio(reservationId)
    FS->>FS: postPendingCharges(folioId)<br/>Room service, minibar, parking, phone
    FS->>FS: postFinalNightRoomRate(folioId)<br/>if nightAudit hasn't run
    FS->>FS: calculateAndPostTax(folioId)<br/>GST, city tax, service charge
    FS-->>FDA: {folio, balance, currency, chargeBreakdown}

    opt Corporate split folio requested
        FDA->>FS: splitFolio(folioId, incidentalChargeIds)
        FS->>FS: createSplitFolio(guestId, selectedCharges)
        FS->>FS: recalculateBalances(primaryFolio, splitFolio)
        FS-->>FDA: {primaryFolio, splitFolio, balances}
        Note over FDA,FS: Both folios must be settled independently
    end

    FDA->>FS: getFinalBalance(folioId)
    FS-->>FDA: {amountDue, currency, lineItems}

    FDA->>PG: charge(tokenizedCard, amount, currency,<br/>idempotencyKey, propertyMerchantId)

    alt Payment declined
        PG-->>FDA: {status: DECLINED, declineCode, message}
        FDA->>FDA: displayDeclineMessage(declineCode)
        Note over FDA: Folio remains OPEN — agent may retry<br/>with different card or cash
        FDA->>PG: charge(alternativePaymentToken, amount, currency, idempotencyKey2)
    end

    alt Gateway timeout
        PG-->>FDA: HTTP 504 Timeout
        FDA->>PG: getTransactionStatus(idempotencyKey)
        alt Transaction found at gateway
            PG-->>FDA: {status: CAPTURED, transactionRef}
        else Transaction not found
            PG-->>FDA: {status: NOT_FOUND}
            Note over FDA: Safe to retry with same idempotencyKey
        end
    end

    PG-->>FDA: {status: CAPTURED, transactionRef, authCode, settledAmount}

    FDA->>FS: postPayment(folioId, {type: CARD, transactionRef,<br/>authCode, amount, currency, postedBy: agentId})
    FS->>FS: recordPayment(folioId, paymentDetails)
    FS->>FS: recalculateBalance(folioId)

    opt Partial payment (balance still > 0)
        FS-->>FDA: {status: PARTIAL, remainingBalance}
        Note over FDA,FS: Agent collects remaining balance by alternate method
        FDA->>FS: postPayment(folioId, {type: CASH, amount: remainingBalance})
        FS->>FS: recalculateBalance(folioId)
    end

    FS->>FS: verifyZeroBalance(folioId)
    FS->>FS: closeFolio(folioId, closedAt: now)
    FS-->>FDA: {status: CLOSED, invoiceId}

    FS->>RS: updateReservationStatus(reservationId, CHECKED_OUT, checkOutTime: now)
    RS->>RS: releaseRoomAllocation(reservationId)
    RS-->>FS: {updated: true}

    RS->>HKS: scheduleCheckoutService(roomId, priority: HIGH,<br/>scheduledTime: now + 15min)
    HKS-->>RS: {taskId, assignedTo}

    opt Guest has loyalty account
        FS->>LS: awardPoints(guestId, settledAmount, stayNights, rateCode)
        LS->>LS: computePoints(amount, tierMultiplier, earnRate)
        LS->>LS: creditPoints(guestId, points)
        LS->>LS: checkTierUpgrade(guestId)
        LS-->>FS: {pointsAwarded, newBalance, tierChanged, newTier}
    end

    FS->>NS: sendCheckoutReceipt(guestId, invoiceId, {email, sms})
    NS-->>FS: {dispatched: true, channels: [EMAIL, SMS]}

    opt Dispute raised post-checkout
        FDA->>FS: raiseDispute(folioId, chargeId, reason)
        FS->>FS: transitionFolioStatus(DISPUTED)
        FS-->>FDA: {status: DISPUTED, ticketId}

        alt Dispute approved — void charge
            FDA->>FS: voidChargeAndCredit(chargeId, supervisorId, voidReason)
            FS->>FS: voidCharge(chargeId)
            FS->>FS: postCredit(folioId, amount)
            FS->>FS: transitionFolioStatus(ADJUSTED)
            FS->>NS: sendAdjustedInvoice(guestId, invoiceId)
        else Dispute rejected
            FDA->>FS: rejectDispute(folioId, reason)
            FS->>FS: transitionFolioStatus(CLOSED)
            FS-->>FDA: {status: CLOSED, disputeResolution: REJECTED}
        end
    end

    FDA-->>FDA: displayCheckoutSuccess(confirmationNumber, invoiceId, pointsAwarded)
```

---

## 3. Night Audit Process

### Description

The Night Audit is a scheduled batch process that runs once per hotel calendar day, typically at
23:59 in the property's local timezone. It is the backbone of hotel accounting: it posts nightly
room revenue, advances the business date, processes no-shows, activates next-day rate plans, and
generates the management reports that the General Manager reviews first thing each morning.

**Step 1 — Scheduler trigger.**  
`NightAuditScheduler` is a cron-driven service that queries `PropertyService` for all active
properties that have reached their audit time threshold based on their individual IANA timezones.
A property-level advisory lock (using `pg_advisory_lock` in PostgreSQL) prevents two concurrent
audit runs from executing for the same property.

**Step 2 — Nightly room rate posting.**  
For every reservation currently in `CHECKED_IN` status at the property, `FolioService` posts a
`ROOM_RATE` charge and a corresponding `ROOM_TAX` charge to the active folio. The charge amount
is taken from the `RoomAllocation.pricePerNight` snapshot — not recalculated from the live rate
plan — ensuring consistency with the confirmed booking price. If the property has a board-basis
inclusion (breakfast, half-board), the cost of those inclusions is also posted as a separate
`F_AND_B` charge.

**Step 3 — No-show processing.**  
`ReservationService.processNoShows()` identifies all reservations with `status = CONFIRMED` and
`checkInDate = auditDate` (today) where the guest did not check in before the property's
no-show processing deadline (configurable, default 22:00 local time). These reservations are
transitioned to `NO_SHOW` status. The applicable no-show penalty is calculated from the rate
plan's cancellation policy and posted as a `FolioCharge`. The folio is flagged for review and
a notification is sent to the revenue manager.

**Step 4 — Rate plan activation.**  
`RateService.activateNextDayRates(propertyId, nextDate)` evaluates all rate plans with a
`startDate` equal to `nextDate` and sets `isActive = true`. It simultaneously deactivates rate
plans whose `endDate` equals `auditDate` (today). This ensures that promotional rates, seasonal
rates, and event-based rates transition on the exact calendar day they are scheduled, without
requiring manual intervention.

**Step 5 — Report generation.**  
`ReportService` generates three standard nightly reports:
- **Occupancy Report:** Rooms occupied, rooms available, occupancy percentage, average daily rate
  (ADR), revenue per available room (RevPAR), and arrivals and departures count.
- **Revenue Report:** Breakdown of revenue by department (rooms, food and beverage, spa, other),
  payment method (cash, card, OTA), and rate plan type.
- **Pickup Report:** Reservations created in the prior 24 hours, cancellations in the prior 24
  hours, and the net booking pace versus the same period in the prior year.

**Step 6 — Rollback on failure.**  
If any step within a property's audit run fails, the entire audit transaction for that property
is rolled back to a clean state. The property is flagged with an `AUDIT_FAILED` status and a
critical alert is sent to the system administrator and the property's General Manager. The night
audit for other properties continues unaffected. Failed audits are retried after a configurable
back-off period, and the system can replay individual steps once the root cause is resolved.

**Step 7 — Completion notification.**  
Once all properties have completed their audit, the scheduler posts a summary to
`NotificationService`, which sends each property's management team a formatted morning report
containing the nightly KPIs, the no-show count, and the pickup metrics for the upcoming seven days.

**Business rules:**
- Night audit runs at most once per property per calendar day. A re-run flag must be explicitly
  set by a supervisor to trigger a second pass.
- Room rate posting uses the allocation snapshot price, never the live rate plan.
- No-show processing only applies to reservations that were CONFIRMED on arrival date and remain
  so past the no-show deadline; reservations that were cancelled before audit time are excluded.
- Rate plan activation is idempotent: running it twice produces the same result.
- Reports are generated after all charge postings are committed, ensuring figures are consistent.

```mermaid
sequenceDiagram
    autonumber
    participant NAS  as NightAuditScheduler
    participant PS   as PropertyService
    participant FS   as FolioService
    participant RS   as ReservationService
    participant RTS  as RateService
    participant RPT  as ReportService
    participant NS   as NotificationService
    participant DB   as Database (pg_advisory_lock)

    NAS->>NAS: evaluateAuditThreshold()<br/>Check properties at 23:59 local time

    NAS->>PS: getPropertiesDueForAudit(currentUTCTime)
    PS-->>NAS: [property1, property2, ..., propertyN]

    loop For each property in audit queue
        NAS->>DB: acquireAdvisoryLock(propertyId)

        alt Lock already held (concurrent run in progress)
            DB-->>NAS: LOCK_NOT_ACQUIRED
            NAS->>NAS: skipProperty(propertyId)<br/>log: CONCURRENT_AUDIT_IN_PROGRESS
        end

        DB-->>NAS: LOCK_ACQUIRED

        NAS->>NAS: beginAuditTransaction(propertyId, auditDate)

        %% Step 1: Post nightly room and tax charges
        NAS->>FS: postNightlyRoomCharges(propertyId, auditDate)
        FS->>FS: loadCheckedInReservations(propertyId)

        loop For each checked-in reservation
            FS->>FS: loadAllocation(reservationId, auditDate)
            FS->>FS: postCharge(folioId, ROOM_RATE, pricePerNight, auditDate)
            FS->>FS: postCharge(folioId, ROOM_TAX, taxAmount, auditDate)

            opt Board basis includes meals
                FS->>FS: postCharge(folioId, F_AND_B, mealPlanAmount, auditDate)
            end
        end

        alt Room charge posting failed
            FS-->>NAS: ChargePostingException {reservationId, reason}
            NAS->>NAS: rollbackAuditTransaction(propertyId)
            NAS->>NS: sendAuditFailureAlert(propertyId, step: ROOM_CHARGES, error)
            NAS->>DB: releaseAdvisoryLock(propertyId)
            NAS->>NAS: markPropertyAuditFailed(propertyId)
            Note over NAS: Proceed to next property — do not abort entire run
        end

        FS-->>NAS: {chargesPosted: count, totalRoomRevenue}

        %% Step 2: No-show processing
        NAS->>RS: processNoShows(propertyId, auditDate)
        RS->>RS: findConfirmedArrivalsNotCheckedIn(propertyId, auditDate)

        loop For each no-show reservation
            RS->>RS: transitionStatus(reservationId, NO_SHOW)
            RS->>FS: postNoShowPenalty(folioId, penaltyAmount, cancellationPolicy)
            FS-->>RS: {chargeId, penaltyPosted}
            RS->>NS: notifyRevenueManager(propertyId, reservationId, NO_SHOW)
        end

        RS-->>NAS: {noShowCount, penaltyRevenue}

        %% Step 3: Activate next-day rates
        NAS->>RTS: activateNextDayRates(propertyId, auditDate + 1 day)
        RTS->>RTS: deactivateExpiredRatePlans(propertyId, auditDate)
        RTS->>RTS: activateScheduledRatePlans(propertyId, auditDate + 1 day)
        RTS-->>NAS: {deactivated: count, activated: count}

        %% Step 4: Advance the property business date
        NAS->>PS: advanceBusinessDate(propertyId, auditDate + 1 day)
        PS-->>NAS: {newBusinessDate}

        %% Step 5: Generate reports
        par Report generation in parallel
            NAS->>RPT: generateOccupancyReport(propertyId, auditDate)
            RPT-->>NAS: {occupancyPct, adr, revpar, arrivals, departures}
        and
            NAS->>RPT: generateRevenueReport(propertyId, auditDate)
            RPT-->>NAS: {roomRevenue, fnbRevenue, otherRevenue, totalRevenue, byPaymentType}
        and
            NAS->>RPT: generatePickupReport(propertyId, auditDate, nextSevenDays)
            RPT-->>NAS: {newReservations, cancellations, netPickup, paceVsLastYear}
        end

        alt Report generation failed
            RPT-->>NAS: ReportGenerationException {reportType, reason}
            NAS->>NAS: logReportFailure(propertyId, reportType)<br/>do not rollback charges — non-critical
            NAS->>NS: sendReportFailureAlert(propertyId, reportType)
        end

        %% Step 6: Commit and release
        NAS->>NAS: commitAuditTransaction(propertyId)
        NAS->>NAS: markPropertyAuditComplete(propertyId, auditDate)
        NAS->>DB: releaseAdvisoryLock(propertyId)

        %% Step 7: Send morning report
        NAS->>NS: sendMorningManagerReport(propertyId, {<br/>occupancyReport,<br/>revenueReport,<br/>pickupReport,<br/>noShowCount,<br/>nextDayArrivals<br/>})
        NS-->>NAS: {dispatched: true, recipients: [GM, RevManager, FrontOfficeManager]}

        Note over NAS: Property audit complete. Business date advanced.
    end

    NAS->>NAS: logNightAuditRunSummary({<br/>totalProperties: N,<br/>succeeded: N,<br/>failed: 0,<br/>duration: ms<br/>})
```
