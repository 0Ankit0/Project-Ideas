# Hotel Property Management System — System Sequence Diagrams

## Overview

System Sequence Diagrams (SSDs) capture the interactions between actors, front-end systems, and back-end services for the most operationally critical flows in the Hotel Property Management System (PMS). Each diagram tells the story of a single business process from trigger to completion, exposing every service boundary crossed, every data exchange made, and every failure path that must be handled. The three processes documented here — guest check-in, OTA booking synchronisation, and the nightly audit — together account for the majority of the PMS's real-time transactional load. Reading these diagrams alongside the domain model and data-flow diagrams gives architects and developers a complete picture of how the system behaves under normal operating conditions and what recovery actions are required when individual components fail.

---

## 1. Check-In Process

### 1.1 Prose Description

The check-in process begins the moment a guest arrives at the front desk (or initiates a mobile self-check-in). The front-desk agent opens the guest's reservation in **FrontDeskUI**, which calls **ReservationService** to retrieve and lock the reservation record, preventing concurrent modifications. ReservationService validates that the reservation is in `CONFIRMED` or `PRE_ASSIGNED` status and that the arrival date matches today's date. If the guest is a walk-in without a prior reservation, ReservationService creates a new same-day reservation inline.

Once the reservation is confirmed, **FolioService** is asked to initialise a new folio — an open billing ledger — linked to the reservation. This folio will accumulate room charges, taxes, incidental charges, and any pre-authorisation holds throughout the stay.

**RoomService** is then queried for the best available room matching the requested room type, floor preference, and any loyalty-tier upgrades. It applies the room-assignment algorithm (considering housekeeping status, maintenance flags, and VIP preferences) and tentatively assigns the room, marking it as `OCCUPIED`.

With a physical room number confirmed, **KeycardService** is instructed to encode one or more RFID keycards (or generate a mobile key payload) for the assigned room and any connected areas (pool, gym, parking). The keycard encoding result — including expiry tied to the checkout date — is returned to FrontDeskUI.

**FolioService** receives the final confirmation of room assignment and posts the first night's room charge and applicable taxes. A pre-authorisation hold is placed on the payment method on file.

Finally, **NotificationService** dispatches a welcome message via the guest's preferred channel (SMS, email, or in-app push) containing the room number, keycard instructions, Wi-Fi credentials, and a link to the digital folio portal. The front-desk agent completes the check-in flow, and the reservation status transitions to `CHECKED_IN`.

### 1.2 Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor Guest
    participant FrontDeskUI
    participant ReservationService
    participant RoomService
    participant KeycardService
    participant FolioService
    participant NotificationService

    Guest->>FrontDeskUI: Present ID + Reservation Confirmation Number
    FrontDeskUI->>ReservationService: GET /reservations/{confirmationNumber}
    ReservationService-->>FrontDeskUI: ReservationDetails {status: CONFIRMED, guestId, roomTypeId, rateplanId}

    FrontDeskUI->>ReservationService: POST /reservations/{id}/lock
    ReservationService-->>FrontDeskUI: 200 OK {lockToken}

    Note over FrontDeskUI,ReservationService: ID Verification
    FrontDeskUI->>ReservationService: POST /reservations/{id}/verify-id\n{documentType, documentNumber, expiryDate}
    ReservationService-->>FrontDeskUI: 200 OK {idVerified: true}

    FrontDeskUI->>RoomService: POST /rooms/assign\n{roomTypeId, arrivalDate, preferences, loyaltyTier}
    RoomService-->>FrontDeskUI: RoomAssignment {roomNumber, floor, wing, features}

    FrontDeskUI->>RoomService: PATCH /rooms/{roomNumber}/status\n{status: OCCUPIED, reservationId}
    RoomService-->>FrontDeskUI: 200 OK

    FrontDeskUI->>KeycardService: POST /keycards/encode\n{roomNumber, checkoutDate, guestId, accessZones}
    KeycardService-->>FrontDeskUI: KeycardPayload {keycardId, encodedData, mobileKeyDeeplink, expiresAt}

    FrontDeskUI->>FolioService: POST /folios\n{reservationId, guestId, paymentMethodToken, checkInDate, checkOutDate}
    FolioService-->>FrontDeskUI: Folio {folioId, status: OPEN, balance: 0.00}

    FolioService->>FolioService: POST /folios/{folioId}/charges\n{chargeType: ROOM_RATE, amount, taxAmount, date: today}
    Note right of FolioService: First night room + tax auto-posted

    FolioService->>FolioService: POST /folios/{folioId}/preauth\n{amount: incidentalHold, paymentToken}
    Note right of FolioService: Pre-auth hold placed on card

    FrontDeskUI->>ReservationService: PATCH /reservations/{id}/status\n{status: CHECKED_IN, roomNumber, folioId, lockToken}
    ReservationService-->>FrontDeskUI: 200 OK {reservation: CHECKED_IN}

    FrontDeskUI->>NotificationService: POST /notifications/send\n{guestId, channel: SMS+EMAIL, template: WELCOME_CHECKIN,\n data: {roomNumber, keycardInstructions, wifiCredentials, folioPortalUrl}}
    NotificationService-->>FrontDeskUI: 202 Accepted {notificationId}

    NotificationService-->>Guest: SMS: "Welcome! Room 412. Mobile key sent. Check folio at…"
    NotificationService-->>Guest: Email: Welcome package with PDF receipt

    FrontDeskUI-->>Guest: Keycard(s) + verbal welcome briefing
```

---

## 2. OTA Booking Synchronisation

### 2.1 Prose Description

Online Travel Agency (OTA) synchronisation is a continuous, bidirectional process. In the outbound direction, whenever availability, rates, or inventory change inside the PMS (due to a new reservation, a cancellation, a manual rate adjustment, or a yield-management rule firing), the **ChannelManagerService** must push updated ARI (Availability, Rates, Inventory) data to every connected OTA within seconds to prevent overbooking or rate parity violations. In the inbound direction, when a guest books through Booking.com or Expedia, the OTA sends a booking notification to the channel manager, which translates it into a native PMS reservation.

The flow begins when the PMS detects a state change — for example, a reservation being created via the property's own website decrements inventory. **InventoryService** publishes an `INVENTORY_CHANGED` event, which **ChannelManagerService** consumes. It fetches the current net availability from **InventoryService** and the applicable rates from **RatePlanService**, then constructs an ARI update payload in the OTA's required format (OTA_HotelAvailNotifRQ for HTNG-based channels, or a REST payload for modern API partners). It pushes this update to Booking.com and Expedia concurrently and awaits their acknowledgements.

When a guest makes a booking on Booking.com, the OTA pushes a `NewReservation` notification to the channel manager endpoint. ChannelManagerService validates the property code, booking reference, rate plan code, and room type mapping, then calls **ReservationService** to create a new reservation record in `CONFIRMED` status. ReservationService decrements availability through **InventoryService**, ensuring no double-booking occurs under concurrent load (using optimistic locking). A confirmation number is generated and returned. ChannelManagerService sends the PMS confirmation number back to the OTA as acknowledgement, and **NotificationService** sends a booking confirmation to the guest.

### 2.2 Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    participant OTAChannel as OTAChannel\n(Booking.com / Expedia)
    participant ChannelManagerService
    participant ReservationService
    participant RatePlanService
    participant InventoryService
    participant NotificationService

    Note over InventoryService,ChannelManagerService: Outbound ARI Push (triggered by internal state change)

    InventoryService->>ChannelManagerService: EVENT inventory.changed\n{propertyId, roomTypeId, date, newAvailability}
    ChannelManagerService->>InventoryService: GET /inventory\n{propertyId, roomTypeId, dateRange}
    InventoryService-->>ChannelManagerService: InventorySnapshot {dates[], availability[], stopSell[]}

    ChannelManagerService->>RatePlanService: GET /rateplans\n{propertyId, roomTypeId, channelCodes:[BOOKINGCOM, EXPEDIA]}
    RatePlanService-->>ChannelManagerService: RatePlanMatrix {plans[], rates[], restrictions[]}

    par Push to Booking.com
        ChannelManagerService->>OTAChannel: POST /ari/update (Booking.com)\n{propertyCode, roomTypeCode, dates, rates, availability}
        OTAChannel-->>ChannelManagerService: 200 OK {updateId, status: ACCEPTED}
    and Push to Expedia
        ChannelManagerService->>OTAChannel: POST /ari/update (Expedia)\n{propertyCode, roomTypeCode, dates, rates, availability}
        OTAChannel-->>ChannelManagerService: 200 OK {updateId, status: ACCEPTED}
    end

    ChannelManagerService->>ChannelManagerService: Log ARI push audit record

    Note over OTAChannel,ChannelManagerService: Inbound Booking Receipt

    OTAChannel->>ChannelManagerService: POST /bookings/new\n{otaBookingRef, propertyCode, roomTypeCode,\n ratePlanCode, guestName, checkIn, checkOut, totalAmount}
    ChannelManagerService->>ChannelManagerService: Validate property + room type + rate plan mapping

    ChannelManagerService->>InventoryService: POST /inventory/hold\n{propertyId, roomTypeId, dateRange, requestId}
    InventoryService-->>ChannelManagerService: 200 OK {holdId, locked: true}

    ChannelManagerService->>ReservationService: POST /reservations\n{source: OTA, otaBookingRef, guestDetails,\n roomTypeId, ratePlanId, dateRange, holdId}
    ReservationService->>InventoryService: POST /inventory/confirm-hold\n{holdId, reservationId}
    InventoryService-->>ReservationService: 200 OK {newAvailability}
    ReservationService-->>ChannelManagerService: Reservation {reservationId, confirmationNumber, status: CONFIRMED}

    ChannelManagerService->>OTAChannel: POST /bookings/{otaBookingRef}/confirm\n{pmsConfirmationNumber, status: CONFIRMED}
    OTAChannel-->>ChannelManagerService: 200 OK {acknowledged: true}

    ChannelManagerService->>NotificationService: POST /notifications/send\n{guestEmail, template: BOOKING_CONFIRMATION,\n data: {confirmationNumber, property, dates, totalAmount}}
    NotificationService-->>ChannelManagerService: 202 Accepted

    ChannelManagerService->>InventoryService: POST /inventory/decrement\n{propertyId, roomTypeId, dateRange}
    InventoryService-->>ChannelManagerService: 200 OK {updatedAvailability}
```

---

## 3. Night Audit Process

### 3.1 Prose Description

The night audit is the most operationally critical scheduled job in any hotel PMS. It runs once every 24 hours — typically between 01:00 and 04:00 local time — and performs a series of financial and administrative actions that close the current business day and open the next. The process is orchestrated by **NightAuditScheduler**, a cron-driven service that coordinates all downstream services through a strict, sequenced workflow with checkpoint logging at every step, allowing the audit to be safely resumed after a failure without duplicating charges.

**Step 1 — Pre-audit validation:** The scheduler verifies that all earlier-in-day folios are balanced, no conflicting locks exist, and the system clock is correct. It also checks for any manual holds placed by management (e.g., "do not audit until GM approval").

**Step 2 — Date roll:** The business date advances from the current day to the next calendar day. This is a global state change that affects all subsequent operations. ReservationService timestamps the date-roll event in the audit log.

**Step 3 — Room and tax charge posting:** FolioService iterates over all in-house reservations (status `CHECKED_IN`) and posts a room rate charge and applicable tax charges (room tax, city tax, VAT) to each open folio. Rate amounts are sourced from the reservation's rate plan and rate calendar. This step is idempotent: charges tagged with the audit date are never double-posted.

**Step 4 — No-show processing:** ReservationService identifies all reservations with an arrival date equal to yesterday that are still in `CONFIRMED` status (i.e., the guest never arrived). For each no-show, a no-show charge is posted to the folio per the cancellation/no-show policy, the reservation status is set to `NO_SHOW`, and the room reverts to `AVAILABLE` in RoomService.

**Step 5 — Revenue recognition:** RevenueService aggregates the day's posted charges by category (accommodation, F&B, spa, other) and computes occupancy statistics (ADR, RevPAR, occupancy rate) for the property.

**Step 6 — Report generation:** ReportService generates the Daily Revenue Report, Arrival/Departure Report, Manager's Flash Report, and the Accounts Receivable Ageing summary. Reports are stored in the document store and made available through the reporting portal.

**Step 7 — Manager summary notification:** NotificationService sends the nightly Flash Report digest to the General Manager, Revenue Manager, and Front Office Manager via email, with a dashboard deep-link.

### 3.2 Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    participant NightAuditScheduler
    participant FolioService
    participant ReservationService
    participant RevenueService
    participant ReportService
    participant NotificationService

    NightAuditScheduler->>NightAuditScheduler: Trigger at 02:00 local time (cron)
    NightAuditScheduler->>ReservationService: GET /audit/preflight-check\n{businessDate: today}
    ReservationService-->>NightAuditScheduler: PreflightResult {allFoliosBalanced: true, openLocks: 0, holdActive: false}

    Note over NightAuditScheduler,ReservationService: Step 1 — Pre-Audit Validation Passed

    NightAuditScheduler->>ReservationService: POST /audit/roll-date\n{fromDate: today, toDate: tomorrow}
    ReservationService-->>NightAuditScheduler: 200 OK {newBusinessDate: tomorrow, auditId}

    Note over NightAuditScheduler,FolioService: Step 2 — Business Date Rolled

    NightAuditScheduler->>FolioService: POST /audit/post-room-charges\n{auditId, businessDate: today}
    FolioService->>ReservationService: GET /reservations?status=CHECKED_IN&propertyId={id}
    ReservationService-->>FolioService: [Reservation] list of all in-house guests

    loop For each in-house reservation
        FolioService->>FolioService: POST /folios/{folioId}/charges\n{type: ROOM_RATE, amount, ratePlanId, date: today}
        FolioService->>FolioService: POST /folios/{folioId}/charges\n{type: ROOM_TAX, amount: taxCalc, date: today}
        FolioService->>FolioService: POST /folios/{folioId}/charges\n{type: CITY_TAX, amount: cityTaxCalc, date: today}
    end

    FolioService-->>NightAuditScheduler: RoomChargeResult {foliosPosted: 142, errors: 0}

    Note over NightAuditScheduler,ReservationService: Step 3 — Room + Tax Charges Posted

    NightAuditScheduler->>ReservationService: GET /reservations?status=CONFIRMED&arrivalDate=yesterday
    ReservationService-->>NightAuditScheduler: [Reservation] no-show candidates list

    loop For each no-show reservation
        NightAuditScheduler->>FolioService: POST /folios/{folioId}/charges\n{type: NO_SHOW_FEE, amount: policy.noShowCharge, date: today}
        FolioService-->>NightAuditScheduler: 200 OK
        NightAuditScheduler->>ReservationService: PATCH /reservations/{id}/status\n{status: NO_SHOW, auditId}
        ReservationService-->>NightAuditScheduler: 200 OK
        NightAuditScheduler->>ReservationService: POST /rooms/{roomNumber}/release\n{reason: NO_SHOW}
        ReservationService-->>NightAuditScheduler: 200 OK
    end

    Note over NightAuditScheduler,RevenueService: Step 4 — No-Shows Processed

    NightAuditScheduler->>RevenueService: POST /revenue/recognise\n{auditId, businessDate: today}
    RevenueService->>FolioService: GET /folios/charges-summary\n{businessDate: today, propertyId}
    FolioService-->>RevenueService: ChargesSummary {roomRevenue, fbRevenue, spaRevenue, otherRevenue, totalRevenue}
    RevenueService->>RevenueService: Calculate ADR, RevPAR, OccupancyRate
    RevenueService-->>NightAuditScheduler: RevenueRecord {totalRevenue, ADR, RevPAR, occupancyPct}

    Note over NightAuditScheduler,ReportService: Step 5 — Revenue Recognised

    NightAuditScheduler->>ReportService: POST /reports/generate\n{auditId, types:[DAILY_REVENUE, ARRIVALS_DEPARTURES, FLASH, AR_AGEING]}
    ReportService->>FolioService: GET /folios/daily-summary
    ReportService->>ReservationService: GET /reservations/arrivals-departures-summary
    ReportService->>RevenueService: GET /revenue/daily-stats
    ReportService-->>NightAuditScheduler: ReportBundle {reportIds[], storageUrls[], generatedAt}

    Note over NightAuditScheduler,NotificationService: Step 6 — Reports Generated

    NightAuditScheduler->>NotificationService: POST /notifications/send\n{recipients:[GM, RevenueMgr, FOManager],\n template: NIGHT_AUDIT_FLASH,\n data: {auditId, revenueSummary, occupancy, reportLinks[]}}
    NotificationService-->>NightAuditScheduler: 202 Accepted

    NightAuditScheduler->>NightAuditScheduler: PATCH /audits/{auditId}/status {status: COMPLETED, completedAt}

    Note over NightAuditScheduler: Audit complete — system ready for next business day
```

---

## Summary

| Process | Actors Involved | Critical Failure Points | Recovery Strategy |
|---|---|---|---|
| Check-In | Guest, FrontDeskUI, 6 services | Keycard encoding failure, folio creation failure | Retry keycard; manual folio fallback; paper key issued |
| OTA Booking Sync | OTA, 5 services | Inventory hold race condition, OTA timeout | Optimistic lock retry; OTA webhook retry with idempotency key |
| Night Audit | Scheduler, 5 services | Partial charge posting, date-roll conflict | Idempotency keys on all charge posts; checkpoint resume from last successful step |

All three flows are designed with idempotency as a first-class concern. Every mutating API call carries a unique idempotency key so that retries after partial failures cannot result in duplicate charges, double room assignments, or phantom reservations.

---

## 4. Error Handling and Alternate Flows

### 4.1 Check-In — Alternate Flows

#### 4.1.1 Room Not Ready (Housekeeping Still In Progress)

```mermaid
sequenceDiagram
    autonumber
    actor Guest
    participant FrontDeskUI
    participant RoomService
    participant NotificationService

    Guest->>FrontDeskUI: Arrive for check-in
    FrontDeskUI->>RoomService: POST /rooms/assign {roomTypeId, preferences}
    RoomService-->>FrontDeskUI: 409 Conflict {reason: ROOM_NOT_READY, estimatedReadyTime: 14:30}

    FrontDeskUI-->>Guest: "Room not yet ready. Estimated ready at 14:30. Bags stored at concierge."

    FrontDeskUI->>NotificationService: POST /notifications/schedule\n{guestId, template: ROOM_READY_ALERT, triggerEvent: ROOM_STATUS_CHANGED, roomTypeId}
    NotificationService-->>FrontDeskUI: 202 Accepted {scheduledNotificationId}

    Note over NotificationService: Notification fires when RoomService\npublishes RoomStatusChanged event
    NotificationService-->>Guest: SMS: "Your room is ready! Please return to the front desk."
```

#### 4.1.2 ID Verification Failure

```mermaid
sequenceDiagram
    autonumber
    actor Guest
    participant FrontDeskUI
    participant ReservationService

    Guest->>FrontDeskUI: Present expired ID document
    FrontDeskUI->>ReservationService: POST /reservations/{id}/verify-id\n{documentType, documentNumber, expiryDate: past}
    ReservationService-->>FrontDeskUI: 422 Unprocessable\n{idVerified: false, reason: DOCUMENT_EXPIRED}

    FrontDeskUI-->>Guest: "ID document has expired. Please provide a valid document."
    Note over FrontDeskUI,Guest: Front desk agent requests alternative ID.\nReservation lock is maintained for 10 minutes.

    Guest->>FrontDeskUI: Present alternative valid ID
    FrontDeskUI->>ReservationService: POST /reservations/{id}/verify-id\n{documentType: PASSPORT, documentNumber, expiryDate: future}
    ReservationService-->>FrontDeskUI: 200 OK {idVerified: true}
```

### 4.2 OTA Booking Sync — Alternate Flows

#### 4.2.1 Overbooking Attempt (No Availability)

```mermaid
sequenceDiagram
    autonumber
    participant OTAChannel as OTAChannel (Booking.com)
    participant ChannelManagerService
    participant ReservationService
    participant InventoryService

    OTAChannel->>ChannelManagerService: POST /bookings/new\n{roomTypeCode: DELUXE, checkIn: 2025-07-04, checkOut: 2025-07-07}
    ChannelManagerService->>InventoryService: POST /inventory/hold\n{roomTypeId, dateRange}
    InventoryService-->>ChannelManagerService: 409 Conflict {reason: NO_AVAILABILITY, availability: 0}

    ChannelManagerService->>OTAChannel: POST /bookings/{ref}/reject\n{reason: NO_AVAILABILITY, message: "Room type sold out for requested dates"}
    OTAChannel-->>ChannelManagerService: 200 OK {acknowledged: true}

    Note over ChannelManagerService: Log overbook attempt for revenue analysis
    ChannelManagerService->>ChannelManagerService: POST /sync-log\n{event: OVERBOOK_ATTEMPT, roomTypeId, dates, channel: BOOKINGCOM}
```

#### 4.2.2 ARI Push Failure with Retry

```mermaid
sequenceDiagram
    autonumber
    participant ChannelManagerService
    participant OTAChannel as OTAChannel (Expedia)

    ChannelManagerService->>OTAChannel: POST /ari/update {propertyCode, rates, availability}
    OTAChannel-->>ChannelManagerService: 503 Service Unavailable

    Note over ChannelManagerService: Retry 1 — wait 1 second
    ChannelManagerService->>OTAChannel: POST /ari/update (retry 1)
    OTAChannel-->>ChannelManagerService: 503 Service Unavailable

    Note over ChannelManagerService: Retry 2 — wait 2 seconds
    ChannelManagerService->>OTAChannel: POST /ari/update (retry 2)
    OTAChannel-->>ChannelManagerService: 200 OK {updateId, status: ACCEPTED}

    ChannelManagerService->>ChannelManagerService: Log ARI push success after 2 retries
```

### 4.3 Night Audit — Alternate Flows

#### 4.3.1 Night Audit Interrupted — Safe Resume

```mermaid
sequenceDiagram
    autonumber
    participant NightAuditScheduler
    participant FolioService
    participant ReservationService

    NightAuditScheduler->>FolioService: POST /audit/post-room-charges\n{auditId, businessDate: today}
    Note over FolioService: Process fails at reservation #78 of 142\n(database connection timeout)
    FolioService-->>NightAuditScheduler: 500 Internal Server Error\n{lastSuccessfulReservationId: 77, progress: 77/142}

    NightAuditScheduler->>NightAuditScheduler: Save checkpoint {auditId, lastSuccessfulReservationId: 77}

    Note over NightAuditScheduler: Alert sent to on-call engineer\nScheduler waits 60 seconds and retries

    NightAuditScheduler->>FolioService: POST /audit/post-room-charges\n{auditId, businessDate: today, resumeFromId: 77}
    FolioService->>FolioService: Skip reservations 1–77 (charges already posted, idempotency key matched)
    FolioService-->>NightAuditScheduler: RoomChargeResult {foliosPosted: 142, errors: 0, skipped: 77}
```

---

## 5. Sequence Design Principles Applied

| Principle | Application in These Diagrams |
|---|---|
| **Optimistic Locking** | Reservation lock token acquired before check-in modifications; prevents concurrent edits by two agents |
| **Idempotency Keys** | All POST calls (charge posting, booking creation, ARI push) carry unique keys; safe retry on timeout |
| **Parallel Execution** | OTA ARI pushes to Booking.com and Expedia happen in parallel (`par` block) to minimise latency |
| **Saga Pattern** | Check-in is a multi-step saga; each step is independently rollback-able (e.g., keycard failure → release room assignment) |
| **Inventory Hold-Then-Confirm** | Inventory is held before reservation creation, then confirmed on success or released on failure — prevents phantom bookings |
| **Checkpoint Resume** | Night audit stores progress checkpoints; failures resume from last successful step without duplicating charges |
