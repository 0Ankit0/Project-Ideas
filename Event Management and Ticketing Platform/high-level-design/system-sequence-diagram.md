# System Sequence Diagram

## Introduction

System Sequence Diagrams (SSDs) model the interactions between **external actors** and the **system boundary** for a specific use case scenario. Unlike internal sequence diagrams that expose service-to-service calls, SSDs treat the entire platform as a black box and focus on the contract between users (humans or external systems) and the platform. They are foundational to defining API contracts, SLA targets, and failure-handling obligations at the integration boundary.

In this document, each SSD maps a critical end-to-end scenario for the Event Management and Ticketing Platform. Actors sit outside the system boundary; services shown inside represent logical processing units, not necessarily independent deployable microservices in every diagram. Time flows top-to-bottom. `alt` and `loop` fragments capture conditional branching and iteration. `note` annotations carry non-functional requirements such as latency budgets and idempotency constraints.

---

## Scenario 1: Ticket Purchase with Payment Processing

This scenario covers the complete ticket purchase flow from the moment an attendee selects a ticket type through to receiving a confirmation email and downloadable QR-code ticket. The flow must handle concurrent purchases (inventory races), payment failures, and hold expiry gracefully.

```mermaid
sequenceDiagram
    autonumber
    actor Attendee
    participant App as MobileApp / WebApp
    participant GW as API Gateway
    participant INV as TicketInventoryService
    participant ORD as OrderService
    participant PAY as PaymentService
    participant STRIPE as Stripe (Payment Gateway)
    participant TKT as TicketService
    participant NOTIF as NotificationService

    Note over App,GW: All requests carry Authorization: Bearer <JWT>

    Attendee->>App: Selects event and desired ticket quantities
    App->>GW: GET /events/{eventId}/ticket-types
    GW->>INV: Forward request (JWT validated, rate-limit OK)
    INV-->>GW: 200 OK { ticketTypes: [{id, name, price, available, holdCount}] }
    GW-->>App: 200 OK ticket type catalog
    App-->>Attendee: Renders ticket picker with live availability counts

    Note over App,INV: Availability includes active hold deductions from Redis<br/>to prevent oversell race conditions

    Attendee->>App: Confirms cart (e.g. 2× GA, 1× VIP)
    App->>GW: POST /orders/hold { eventId, lineItems: [{ticketTypeId, qty}], attendeeId }
    GW->>ORD: Forward hold request (idempotency-key: UUID in header)
    ORD->>INV: ReserveInventory(eventId, lineItems, holdTTL=600s)
    INV->>INV: Atomic DECRBY in Redis per ticket type
    alt Sufficient inventory
        INV-->>ORD: HoldConfirmed { holdId, expiresAt (now + 600s) }
        ORD->>ORD: Persist Order { status: HOLD, holdId, expiresAt }
        ORD-->>GW: 201 Created { orderId, holdId, expiresAt, totalAmount }
        GW-->>App: 201 Created order hold response
        App-->>Attendee: Shows checkout timer countdown (10 min)
    else Insufficient inventory
        INV-->>ORD: InsufficientInventory { ticketTypeId, requested, available }
        ORD-->>GW: 409 Conflict { code: INSUFFICIENT_INVENTORY, detail }
        GW-->>App: 409 Conflict
        App-->>Attendee: "Sold out or not enough tickets — try fewer quantities"
    end

    Attendee->>App: Enters payment details (card number via Stripe.js)
    Note over App,STRIPE: Stripe.js tokenises card on client — raw card data never touches platform servers (PCI DSS scope reduction)
    App->>STRIPE: Stripe.js createPaymentMethod({ card })
    STRIPE-->>App: paymentMethodId (pm_xxxx)

    Attendee->>App: Submits payment
    App->>GW: POST /orders/{orderId}/pay { paymentMethodId, idempotencyKey: UUID }
    GW->>ORD: Forward pay request

    ORD->>ORD: Validate Order.status == HOLD and not expired
    alt Hold expired during payment entry
        ORD-->>GW: 409 Conflict { code: HOLD_EXPIRED, expiredAt }
        GW-->>App: 409 Conflict
        App-->>Attendee: "Your reservation expired. Please start over."
    else Hold still valid
        ORD->>PAY: ProcessPayment { orderId, paymentMethodId, amount, currency, idempotencyKey }
        PAY->>STRIPE: POST /v1/payment_intents { amount, currency, payment_method, confirm: true, idempotency_key }
        Note over PAY,STRIPE: Stripe idempotency key = orderId:paymentAttemptNum<br/>prevents double-charge on network retry

        alt Payment succeeds
            STRIPE-->>PAY: PaymentIntent { status: succeeded, chargeId }
            PAY-->>ORD: PaymentResult { success: true, chargeId, processedAt }
            ORD->>ORD: Transition Order.status → COMPLETED
            ORD->>ORD: Persist Payment record { chargeId, amount, gateway: STRIPE }
            ORD->>INV: ConfirmHold(holdId) — convert hold to sold inventory
            INV-->>ORD: HoldConfirmed (inventory committed)
            ORD->>ORD: Publish domain event OrderCompleted { orderId, eventId, attendeeId, lineItems }
            Note over ORD: Event published to Kafka topic orders.completed<br/>downstream services react asynchronously

            ORD-->>GW: 200 OK { orderId, status: COMPLETED, tickets: [...] }
            GW-->>App: 200 OK order confirmation

            TKT->>TKT: Consume OrderCompleted → generate Ticket records
            TKT->>TKT: Generate QR codes (SHA-256 HMAC hash of ticketId:secret)
            TKT->>TKT: Render PDF tickets and upload to S3
            TKT->>ORD: TicketsGenerated { orderId, ticketIds, qrUrls }

            NOTIF->>NOTIF: Consume OrderCompleted event
            NOTIF->>NOTIF: Render email template (order summary + QR attachments)
            NOTIF->>App: Send push notification "Your tickets are ready!"
            NOTIF-->>Attendee: Email: Booking Confirmation with PDF tickets attached

            App-->>Attendee: "Purchase complete! Check your email for tickets."

        else Payment declined
            STRIPE-->>PAY: PaymentIntent { status: requires_payment_method, last_payment_error }
            PAY-->>ORD: PaymentResult { success: false, errorCode, errorMessage }
            ORD->>ORD: Increment Order.paymentAttempts counter
            alt paymentAttempts < 3 (retry allowed)
                ORD-->>GW: 402 Payment Required { code: CARD_DECLINED, retryAllowed: true, message }
                GW-->>App: 402 Payment Required
                App-->>Attendee: "Card declined. Please try a different payment method. (Hold still active)"
            else paymentAttempts >= 3 (release hold)
                ORD->>INV: ReleaseHold(holdId)
                INV->>INV: Atomic INCRBY in Redis — restore inventory
                INV-->>ORD: HoldReleased
                ORD->>ORD: Transition Order.status → FAILED
                ORD-->>GW: 402 Payment Required { code: PAYMENT_FAILED_HOLD_RELEASED }
                GW-->>App: 402 Payment Required
                App-->>Attendee: "Payment could not be processed. Your reservation has been released."
            end

        else Stripe API timeout / network error
            STRIPE-->>PAY: Connection timeout after 30s
            PAY->>PAY: Retry POST to Stripe with same idempotency_key (exponential backoff: 1s, 2s, 4s)
            PAY-->>ORD: PaymentResult { success: false, errorCode: GATEWAY_TIMEOUT }
            ORD-->>GW: 503 Service Unavailable { code: PAYMENT_GATEWAY_UNAVAILABLE, retryAfter: 60 }
            GW-->>App: 503 Service Unavailable
            App-->>Attendee: "Payment service temporarily unavailable. Your hold is preserved. Try again shortly."
        end
    end
```

### Scenario 1: Key Design Decisions

| Concern | Decision | Rationale |
|---|---|---|
| Inventory race prevention | Redis atomic DECRBY with hold TTL | Eliminates DB-level pessimistic locking bottleneck under flash sale load |
| PCI DSS scope | Stripe.js client tokenisation | Raw card data never traverses platform servers — card data scope is Stripe only |
| Idempotency | Per-request UUID in header, forwarded to Stripe | Safe retry on mobile network drops without double-charge risk |
| Hold duration | 600 seconds (10 minutes) | Balances conversion rate against inventory lock-up; configurable per event |
| Payment retries | Max 3 attempts before hold release | Prevents indefinite inventory lock-up from repeatedly failing cards |

---

## Scenario 2: Event Cancellation with Bulk Refund Processing

When an organizer cancels an event, the platform must atomically void all inventory, compute refunds for every completed order, batch them for efficient gateway processing, and notify all affected attendees. This is a high-impact, low-frequency operation requiring careful idempotency and error handling.

```mermaid
sequenceDiagram
    autonumber
    actor Organizer as Event Organizer
    participant PORTAL as AdminPortal
    participant GW as API Gateway
    participant EVT as EventService
    participant MQ as MessageQueue (Kafka)
    participant INV as TicketInventoryService
    participant REF as RefundService
    participant STRIPE as Payment Gateway (Stripe)
    participant NOTIF as NotificationService

    Organizer->>PORTAL: Initiates event cancellation with cancellation reason
    PORTAL->>GW: POST /events/{eventId}/cancel { reason, cancellationPolicy }
    GW->>EVT: Forward cancellation request (requires ORGANIZER or ADMIN role JWT)

    EVT->>EVT: Validate caller is verified owner of event
    alt Caller does not own event
        EVT-->>GW: 403 Forbidden { code: NOT_EVENT_OWNER }
        GW-->>PORTAL: 403 Forbidden
        PORTAL-->>Organizer: "You do not have permission to cancel this event."
    else Caller is verified owner
        EVT->>EVT: Validate Event.status ∈ {DRAFT, PUBLISHED, SALES_OPEN}
        EVT->>EVT: Transition Event.status → CANCELLED
        EVT->>EVT: Record cancellation { reason, cancelledBy, cancelledAt }
        EVT->>MQ: Publish EventCancelled { eventId, cancelledAt, reason, refundPolicy }
        Note over EVT,MQ: Topic: events.cancelled | Partition key: eventId<br/>Ensures ordered processing of cancellation side-effects

        EVT-->>GW: 200 OK { eventId, status: CANCELLED, estimatedRefundTime: "3-5 business days" }
        GW-->>PORTAL: 200 OK
        PORTAL-->>Organizer: "Event cancelled. Refunds are being processed automatically."

        MQ-->>INV: EventCancelled event consumed
        INV->>INV: Query all active holds for eventId
        INV->>INV: Bulk void holds: SET hold:{holdId}:status = VOIDED for each
        INV->>INV: Reset inventory counters to 0 (event closed)
        INV->>MQ: Publish InventoryVoided { eventId, holdsVoided: N }

        MQ-->>REF: EventCancelled event consumed
        REF->>REF: Query all Orders WHERE eventId = X AND status = COMPLETED
        Note over REF: May return thousands of orders — processed in chunks of 1000

        REF->>REF: Create RefundBatch { batchId, eventId, totalOrders: N, status: PROCESSING }

        loop For each chunk of up to 1000 orders
            REF->>REF: Fetch chunk of order records with Payment.chargeId
            loop For each order in chunk
                REF->>REF: Calculate refund amount (full amount per policy)
                REF->>STRIPE: POST /v1/refunds { charge: chargeId, amount, reason: duplicate, idempotency_key: refundBatchId:orderId }
                alt Stripe refund succeeds
                    STRIPE-->>REF: Refund { id: re_xxx, status: succeeded, amount }
                    REF->>REF: Update Refund.status = SUCCEEDED
                    REF->>REF: Update Order.refundStatus = REFUNDED
                else Stripe returns rate limit (429)
                    REF->>REF: Backoff: wait 2^attempt seconds (1s → 2s → 4s)
                    REF->>STRIPE: Retry POST /v1/refunds (same idempotency_key)
                    Note over REF,STRIPE: Up to 3 retries with exponential backoff
                else Stripe timeout / 5xx error after 3 retries
                    REF->>REF: Mark Refund.status = FAILED
                    REF->>MQ: Publish RefundFailed { orderId, chargeId, error } → dead letter topic
                    Note over REF,MQ: Dead letter topic: refunds.failed<br/>Manual review queue for ops team
                end
            end
            REF->>REF: Update RefundBatch.processedChunks++
        end

        REF->>REF: Finalize RefundBatch { completedAt, succeeded: N, failed: M }
        REF->>MQ: Publish RefundBatchCompleted { batchId, eventId, succeeded, failed }

        MQ-->>NOTIF: EventCancelled event consumed
        NOTIF->>NOTIF: Query all attendee emails/phones for eventId
        loop For each attendee (batched in groups of 500)
            NOTIF->>NOTIF: Render cancellation email template with refund details
            NOTIF-->>Attendee: Email: "Event Cancelled — Your refund is on the way"
        end

        MQ-->>NOTIF: RefundBatchCompleted event consumed
        loop For each attendee with succeeded refund
            NOTIF-->>Attendee: Email: "Refund Confirmed — $XX.XX returned to your card"
        end

        loop For each attendee with failed refund
            NOTIF-->>Attendee: Email: "Action Required — Your refund needs attention" with support link
        end
    end
```

### Scenario 2: Refund Batch Processing Architecture

The chunked batch processing pattern is chosen over a streaming approach because Stripe rate limits refund calls to 100 requests per second per account. Processing in 1000-order chunks with per-chunk pacing ensures the platform stays within gateway rate limits while providing progress visibility via the `RefundBatch` record.

| Metric | Value | Notes |
|---|---|---|
| Chunk size | 1000 orders | Balances memory usage vs DB round-trips |
| Stripe rate limit | 100 req/s | Requires pacing logic between chunks |
| Retry policy | 3 attempts, exponential backoff | Idempotency key guarantees no double-refund |
| Dead letter retention | 7 days | Ops team SLA for manual refund processing |
| Total estimated throughput | ~360,000 refunds/hour | At 100 req/s sustained |

---

## Scenario 3: Check-in at Venue

The check-in flow operates under field conditions: intermittent connectivity, high throughput (concerts may have 50,000 attendees arriving in 30 minutes), and the need to fail safely in the "let them in" direction to avoid attendee confrontation. The VenueStaffApp is an offline-capable Progressive Web App (PWA) that caches a signed QR manifest.

```mermaid
sequenceDiagram
    autonumber
    actor Attendee
    participant STAFF as VenueStaffApp (Offline PWA)
    participant GW as API Gateway
    participant CHECKIN as CheckInService
    participant TKT as TicketService
    participant ACS as AccessControlSystem
    participant NOTIF as NotificationService

    Note over STAFF: App pre-syncs signed QR manifest every 60 minutes<br/>Manifest: {qrHash → {ticketId, eventId, validUntil}} signed with HMAC-SHA256

    alt Device is ONLINE
        Attendee->>Attendee: Opens ticket QR code in wallet / email
        Attendee->>STAFF: Presents QR code to scanner (camera or Bluetooth scanner)
        STAFF->>STAFF: Decode QR code → extract qrHash
        STAFF->>GW: POST /check-in/validate { qrHash, deviceId, venueId }
        GW->>CHECKIN: Forward validate request (Staff JWT with STAFF role)

        CHECKIN->>TKT: GetTicketByQRHash(qrHash)
        TKT-->>CHECKIN: Ticket { ticketId, eventId, status, attendeeId, seat }

        CHECKIN->>CHECKIN: Validate: eventId matches expected event for today
        CHECKIN->>CHECKIN: Validate: Ticket.status == ISSUED (not CANCELLED or TRANSFERRED)
        CHECKIN->>CHECKIN: Validate: event date is today (within check-in window)

        alt Ticket is valid and not yet checked in
            CHECKIN->>CHECKIN: Atomically check + set CheckIn record (Redis SET NX for idempotency)
            CHECKIN->>TKT: UpdateTicketStatus(ticketId, CHECKED_IN, checkInTime: now)
            TKT-->>CHECKIN: StatusUpdated
            CHECKIN->>CHECKIN: Persist CheckIn { ticketId, staffId, deviceId, timestamp, method: ONLINE }
            CHECKIN->>CHECKIN: INCR Redis counter attendance:{eventId}:count
            CHECKIN->>ACS: OpenGate(gateId, durationMs: 3000)
            ACS-->>CHECKIN: GateOpened { gateId, openedAt }
            CHECKIN-->>GW: 200 OK { result: GRANTED, attendeeName, seat, welcomeMessage }
            GW-->>STAFF: 200 OK granted
            STAFF-->>Attendee: Screen flash GREEN + audio chime "Welcome!"

            NOTIF->>NOTIF: Consume AttendeeCheckedIn event (async)
            NOTIF-->>Attendee: Push notification "You're checked in! Enjoy the event 🎉"

        else Ticket already checked in (duplicate scan)
            CHECKIN-->>GW: 409 Conflict { code: ALREADY_CHECKED_IN, checkedInAt, checkedInByDevice }
            GW-->>STAFF: 409 Conflict
            STAFF-->>STAFF: Display YELLOW warning screen with first check-in details
            STAFF-->>Attendee: "Already scanned at [time]. May we see your physical ID?"
            Note over STAFF: Staff can trigger MANUAL_OVERRIDE to admit with supervisor code
            alt Staff enters supervisor override code
                STAFF->>GW: POST /check-in/override { qrHash, overrideCode, reason }
                GW->>CHECKIN: RecordOverride { qrHash, staffId, supervisorCode, reason }
                CHECKIN->>CHECKIN: Validate supervisor override code (TOTP-based)
                CHECKIN->>CHECKIN: Persist CheckIn with method: OVERRIDE, overrideReason
                CHECKIN-->>GW: 200 OK { result: GRANTED_OVERRIDE }
                GW-->>STAFF: Granted with override log entry
                STAFF-->>Attendee: Admitted with manual note in system
            end

        else Invalid QR code (hash not found)
            CHECKIN-->>GW: 404 Not Found { code: INVALID_QR }
            GW-->>STAFF: 404 Not Found
            STAFF-->>STAFF: RED screen, audio buzz
            STAFF-->>Attendee: "Ticket not recognised. Please visit the help desk."
            CHECKIN->>CHECKIN: Log security event { qrHash, deviceId, timestamp, eventType: INVALID_QR_SCAN }

        else Ticket is CANCELLED or TRANSFERRED
            CHECKIN-->>GW: 403 Forbidden { code: TICKET_INVALID, reason: status }
            GW-->>STAFF: 403 Forbidden
            STAFF-->>STAFF: RED screen with reason text
            STAFF-->>Attendee: "This ticket is no longer valid. Please visit the help desk."
            CHECKIN->>CHECKIN: Log security event { ticketId, status, deviceId, eventType: INVALID_TICKET_SCAN }
        end

    else Device is OFFLINE
        Note over STAFF: App uses locally cached signed QR manifest for validation
        Attendee->>STAFF: Presents QR code
        STAFF->>STAFF: Decode QR → extract qrHash
        STAFF->>STAFF: Look up qrHash in local IndexedDB manifest
        STAFF->>STAFF: Verify manifest HMAC-SHA256 signature (public key embedded in app)
        STAFF->>STAFF: Check local offline-denied set (already denied this session)

        alt QR hash found in manifest AND valid AND not in local denied set
            STAFF->>STAFF: Add qrHash to local scanned-offline set (prevents duplicate scans offline)
            STAFF->>STAFF: Queue CheckIn record in offline sync buffer
            STAFF->>ACS: OpenGate(gateId) via local Bluetooth/direct signal
            STAFF-->>Attendee: GREEN screen "Welcome! (Offline mode — confirmation pending)"
            Note over STAFF: Queued check-ins are synced to CheckInService on reconnect<br/>Conflict resolution: server CHECKIN record wins for duplicate detection

        else QR hash NOT found in manifest or manifest expired
            STAFF-->>Attendee: YELLOW screen "Cannot verify offline. Please show ID or wait for connectivity."
        end

        Note over STAFF: On reconnect, STAFF app flushes offline sync buffer
        STAFF->>GW: POST /check-in/sync { offlineCheckIns: [...] }
        GW->>CHECKIN: BulkRecordCheckIns(offlineCheckIns)
        CHECKIN->>CHECKIN: Upsert check-in records and deduplicate by ticketId
        CHECKIN-->>GW: 200 OK { processed, duplicates, conflicts }
        GW-->>STAFF: Sync result displayed to staff supervisor
    end
```

### Scenario 3: Offline Architecture Notes

The VenueStaffApp downloads a signed QR manifest hourly during the event day. The manifest contains the HMAC-SHA256 hash of every valid ticket for the event, signed with a short-lived secret rotated per event. This prevents QR forgery while enabling fully offline validation. The manifest size for a 50,000-attendee event is approximately 4.5 MB (compressed), suitable for mobile caching.

---

## Non-Functional Considerations

### Response Time Budgets

| Scenario | Operation | P50 Target | P99 Target | Timeout |
|---|---|---|---|---|
| Ticket Purchase | GET ticket types | 50 ms | 120 ms | 5 s |
| Ticket Purchase | POST /orders/hold | 200 ms | 500 ms | 10 s |
| Ticket Purchase | POST /orders/{id}/pay | 1,500 ms | 3,000 ms | 30 s |
| Ticket Purchase | QR code generation | 800 ms | 2,000 ms | 15 s |
| Event Cancellation | POST /events/{id}/cancel | 300 ms | 800 ms | 15 s |
| Event Cancellation | Bulk refund (per order) | N/A | N/A | 60 s per chunk |
| Check-in (online) | POST /check-in/validate | 80 ms | 200 ms | 5 s |
| Check-in (offline) | Local manifest lookup | 5 ms | 15 ms | N/A (local) |

### Retry Strategies

```mermaid
flowchart LR
    A[Initial Request] --> B{Success?}
    B -- Yes --> Z[Done]
    B -- No --> C{Attempt #}
    C -- "1 (wait 1s)" --> D[Retry]
    C -- "2 (wait 2s)" --> D
    C -- "3 (wait 4s)" --> D
    D --> B
    C -- "4+ → DLQ" --> E[Dead Letter Queue]
    E --> F[Alert Ops / Manual Review]
```

| Service | Retry Policy | Max Attempts | Backoff | DLQ |
|---|---|---|---|---|
| PaymentService → Stripe | Exponential | 3 | 1s, 2s, 4s | Yes (payments.failed) |
| RefundService → Stripe | Exponential | 3 | 2s, 4s, 8s | Yes (refunds.failed) |
| NotificationService → SendGrid | Linear | 5 | 30s | Yes (notifications.failed) |
| CheckInService → DB | Exponential | 3 | 100ms, 200ms, 400ms | No (fail open) |

### Circuit Breaker Placement

Circuit breakers (implemented via Resilience4j or equivalent) are placed at every synchronous external integration boundary:

- **PaymentService → Stripe**: Opens after 5 failures in 10s sliding window. Half-open probe every 30s. Downstream: OrderService receives 503 and holds the order (does not release inventory) to allow retry.
- **NotificationService → SendGrid/Twilio**: Opens after 10 failures in 30s. Half-open probe every 60s. Downstream: Notification queued for retry — non-blocking for purchase flow.
- **CheckInService → PostgreSQL**: Opens after 3 failures in 5s. Half-open probe every 10s. Downstream: Falls back to Redis-only validation (degraded mode, online check-in uses cached state).

### Idempotency Keys per Operation

| Operation | Idempotency Key | Scope | Storage |
|---|---|---|---|
| POST /orders/hold | Client-generated UUID in `Idempotency-Key` header | Per hold request | Redis with 24h TTL |
| POST /orders/{id}/pay | `{orderId}:{paymentAttemptNumber}` | Per payment attempt | Passed to Stripe API |
| POST /v1/refunds (Stripe) | `{refundBatchId}:{orderId}` | Per refund within batch | Passed to Stripe API |
| POST /check-in/validate | `{qrHash}:{eventId}` (Redis SET NX) | Per ticket per event | Redis with event-duration TTL |
| POST /check-in/sync (offline) | `{deviceId}:{qrHash}:{timestamp}` | Per offline scan record | PostgreSQL upsert by composite key |

### Kafka Topic Design

| Topic | Partitioning Key | Retention | Consumers |
|---|---|---|---|
| `orders.completed` | orderId | 7 days | TicketService, NotificationService, AnalyticsService |
| `events.cancelled` | eventId | 30 days | TicketInventoryService, RefundService, NotificationService |
| `refunds.failed` | orderId | 90 days | Ops alert system, manual review dashboard |
| `checkins.recorded` | eventId | 7 days | AnalyticsService, NotificationService |
| `notifications.failed` | notificationId | 14 days | Notification retry worker |
