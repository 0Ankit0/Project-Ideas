# Data Flow Diagram

## Introduction

Data Flow Diagrams (DFDs) model how data moves through a system — where it comes from, how it is transformed, where it is stored, and where it goes. Unlike sequence diagrams that show time-ordered interactions between components, DFDs focus on **data in motion and data at rest**, making them the primary tool for data governance, GDPR compliance analysis, and security threat modelling.

This document uses a two-level DFD notation:

- **Level 0 (Context DFD)**: The entire platform as a single process. Shows all external entities and the top-level data flows crossing the system boundary.
- **Level 1 (Decomposed DFDs)**: The system opened up to reveal major processing functions, data stores, and the flows between them. Each Level 1 diagram covers a single major capability of the platform.

**Notation conventions used in Mermaid flowcharts**:
- Rounded rectangles (`([...])`) represent **external entities** (actors outside the system boundary)
- Rectangles (`[...]`) represent **processes** (transformations of data)
- Cylinders (`[(...)]}`) represent **data stores** (persistent storage)
- Arrows represent **data flows** with labels describing the data content
- Dashed borders indicate **offline / asynchronous** paths

---

## Level 0 — Context DFD

The entire Event Management and Ticketing Platform is represented as a single process node. All data that crosses the system boundary is shown as labelled flows.

```mermaid
flowchart TB
    subgraph External Entities
        ATT([Attendee])
        ORG([Event Organizer])
        PGW([Payment Gateway\nStripe])
        EMAIL([Email / SMS Provider\nSendGrid / Twilio])
        ANALYTICS([Analytics Platform\nMixpanel / Amplitude])
        SEARCH([Search Engine\nGoogle / App Store])
        CDN([CDN\nCloudFront])
    end

    PLATFORM["🎟️ Event Management\nand Ticketing Platform"]

    ORG -- "Event details, venue info,\nticket types, pricing rules" --> PLATFORM
    PLATFORM -- "Event dashboard, sales reports,\npayout summaries, attendee lists" --> ORG

    ATT -- "Ticket purchase request,\naccount registration, QR scan" --> PLATFORM
    PLATFORM -- "Order confirmation, QR ticket,\nrefund status, event updates" --> ATT

    PLATFORM -- "Payment authorisation request\n(tokenised card data)" --> PGW
    PGW -- "Payment authorisation result,\ncharge ID, refund confirmation" --> PLATFORM

    PLATFORM -- "Email/SMS payload\n(confirmation, cancellation, refund)" --> EMAIL
    EMAIL -- "Delivery status,\nbounce / unsubscribe events" --> PLATFORM

    PLATFORM -- "Behavioural event stream\n(page views, purchases, check-ins)" --> ANALYTICS
    ANALYTICS -- "Aggregated metrics,\nfunnel reports (optional)" --> PLATFORM

    PLATFORM -- "Structured event data\n(title, date, venue, availability)" --> SEARCH
    SEARCH -- "Search indexing confirmations" --> PLATFORM

    PLATFORM -- "Static assets, event page HTML,\nQR code images" --> CDN
    CDN -- "Cache invalidation confirmations,\norigin pull requests" --> PLATFORM
```

---

## Level 1 — Ticket Purchase Flow

This Level 1 DFD decomposes the ticket purchase process into its six core processing functions. Data stores show where data is read from and written to at each step.

```mermaid
flowchart TD
    ATT([Attendee]) -- "Ticket selection\n{eventId, ticketTypeId, qty}" --> P11

    P11["1.1 Validate Inventory"]
    P12["1.2 Create Hold"]
    P13["1.3 Process Payment"]
    P14["1.4 Confirm Order"]
    P15["1.5 Generate Tickets"]
    P16["1.6 Send Notifications"]

    D1[(D1 Events\nDB)]
    D2[(D2 TicketInventory\nRedis + DB)]
    D3[(D3 Orders\nDB)]
    D4[(D4 Tickets\nDB + S3)]
    D5[(D5 Attendees\nDB)]
    D6[(D6 Notifications\nDB)]

    %% Process 1.1 Validate Inventory
    P11 -- "Read event status and\nticket type details" --> D1
    D1 -- "Event record {status, salesWindow,\nvenueCapacity}" --> P11
    P11 -- "Read live inventory counts\n{available, held, sold}" --> D2
    D2 -- "Availability snapshot\n{available, holdTTL}" --> P11
    P11 -- "Availability response\n{ticketTypes with availability}" --> ATT

    %% Process 1.2 Create Hold
    ATT -- "Cart submission\n{lineItems, attendeeId}" --> P12
    P12 -- "Read attendee record\n(verify account)" --> D5
    D5 -- "Attendee {id, email, isVerified}" --> P12
    P12 -- "Atomic DECRBY per ticket type\n(Redis pipeline with WATCH)" --> D2
    D2 -- "Hold confirmation\n{holdId, expiresAt}" --> P12
    P12 -- "Write order record\n{status: HOLD, lineItems, holdId}" --> D3
    P12 -- "Hold created response\n{orderId, holdId, expiresAt, total}" --> ATT

    %% Process 1.3 Process Payment
    ATT -- "Payment submission\n{orderId, paymentMethodId}" --> P13
    P13 -- "Read order record\n(validate hold still active)" --> D3
    D3 -- "Order {status, holdExpiresAt, total}" --> P13
    P13 -- "Payment authorisation request\n{amount, currency, paymentMethodId, idempotencyKey}" --> STRIPE([Stripe API])
    STRIPE -- "Payment result\n{chargeId, status, errorCode}" --> P13
    P13 -- "Write payment record\n{chargeId, amount, status}" --> D3

    %% Process 1.4 Confirm Order
    P13 -- "Payment result\n(success or failure)" --> P14
    P14 -- "Update order status\n{HOLD → COMPLETED or FAILED}" --> D3
    P14 -- "Confirm hold: convert held → sold\n(Redis DECRBY held, inventory committed)" --> D2
    P14 -- "Order confirmed response\n{orderId, status, tickets}" --> ATT

    %% Process 1.5 Generate Tickets
    P14 -- "OrderCompleted event\n{orderId, lineItems, attendeeId}" --> P15
    P15 -- "Read order and ticket type details" --> D3
    D3 -- "Order details with line items" --> P15
    P15 -- "Write ticket records\n{ticketId, qrHash, status: ISSUED}" --> D4
    P15 -- "Write QR code PNG to S3\nWrite PDF to S3" --> D4
    D4 -- "Ticket records with S3 URLs" --> P15

    %% Process 1.6 Send Notifications
    P15 -- "TicketsGenerated event\n{orderId, ticketIds, pdfUrls}" --> P16
    P14 -- "OrderCompleted event" --> P16
    P16 -- "Read attendee contact details" --> D5
    D5 -- "Attendee {email, phone, pushToken}" --> P16
    P16 -- "Write notification record\n{status, channel, sentAt}" --> D6
    P16 -- "Email with PDF attachment\n(via SendGrid)" --> SENDGRID([SendGrid])
    P16 -- "Push notification\n(via Firebase)" --> FIREBASE([Firebase FCM])
    SENDGRID -- "Delivery status" --> P16
    FIREBASE -- "Delivery receipt" --> P16
    P16 -- "Confirmation notification" --> ATT
```

### Level 1 Ticket Purchase: Data Transformation Summary

| Process | Input Data | Transformation | Output Data |
|---|---|---|---|
| 1.1 Validate Inventory | Raw attendee selection | Join with live Redis counts and DB event metadata | Enriched availability catalog |
| 1.2 Create Hold | Cart line items | Atomic Redis DECRBY + Order record creation | holdId with TTL, orderId |
| 1.3 Process Payment | orderId + paymentMethodId | Payment gateway authorisation | chargeId or error |
| 1.4 Confirm Order | Payment result | Order state transition + inventory commit | Confirmed order record |
| 1.5 Generate Tickets | OrderCompleted event | QR hash generation, PDF rendering, S3 upload | Ticket records with URLs |
| 1.6 Send Notifications | TicketsGenerated event | Template rendering, channel selection | Email + push delivery |

---

## Level 1 — Check-in Flow

The check-in flow has an offline-first architecture. Data flows bifurcate based on device connectivity, with offline paths relying on a locally cached QR manifest.

```mermaid
flowchart TD
    STAFF([Venue Staff\nScanner App]) -- "QR code scan\n{qrHash, deviceId}" --> P21

    P21["2.1 Scan QR Code\n(Client-side decode)"]
    P22["2.2 Validate Ticket\n(Server or Local Cache)"]
    P23["2.3 Check Duplicate\n(Redis SET NX)"]
    P24["2.4 Record Check-in"]
    P25["2.5 Update Attendance Count"]
    P26["2.6 Trigger Access Control"]

    D4[(D4 Tickets\nDB)]
    D7[(D7 CheckIns\nDB)]
    D8[(D8 Offline Cache\nIndexedDB on device)]
    D9[(D9 Redis\nAttendance counter)]

    ATT([Attendee])
    ACS([Access Control\nSystem])

    P21 -- "Decoded QR hash\n{qrHash}" --> P22

    %% Online path
    P22 -- "Lookup ticket by QR hash\n(online path)" --> D4
    D4 -- "Ticket {ticketId, status,\neventId, attendeeId, seat}" --> P22
    P22 -- "Validated ticket data" --> P23

    %% Offline path
    P22 -. "Manifest lookup\n(offline path)" .-> D8
    D8 -. "Cached {qrHash → ticketId,\nvalidUntil, hmacSignature}" .-> P22
    Note1["Device validates HMAC\nsignature locally — no server call"]

    %% Duplicate check
    P23 -- "SET NX checkin:{ticketId}\n(atomic, Redis)" --> D9
    D9 -- "SET result: OK (first scan)\nor nil (already scanned)" --> P23
    P23 -- "Validation result\n{GRANTED, DENIED_DUPLICATE,\nDENIED_INVALID}" --> P24

    %% Record check-in
    P24 -- "Write check-in record\n{ticketId, staffId, method,\ncheckedInAt, gateId}" --> D7
    P24 -. "Queue offline check-in record\n(if offline)" .-> D8
    P24 -- "Update ticket status\n{ISSUED → CHECKED_IN}" --> D4

    %% Attendance count
    P24 -- "Check-in recorded signal" --> P25
    P25 -- "INCR attendance:{eventId}:count" --> D9
    D9 -- "Updated count" --> P25
    P25 -- "Real-time count" --> DASHBOARD([Organizer\nLive Dashboard])

    %% Access control
    P24 -- "Gate open signal\n{gateId, durationMs}" --> P26
    P26 -- "Open gate command" --> ACS
    ACS -- "Gate opened confirmation" --> P26

    %% Attendee feedback
    P26 -- "Check-in result\n(GREEN/RED screen + audio)" --> STAFF
    STAFF -- "Staff shows result to attendee" --> ATT

    %% Offline sync
    D8 -. "Sync on reconnect:\nPOST /check-in/sync\n{offlineCheckIns[]}" .-> D7
    Note2["Server deduplicates by\nticketId on sync — offline\ncheck-ins win for entry\nbut server resolves conflicts"]
```

### Check-in Offline Data Flow Detail

The offline-first architecture requires careful data lifecycle management:

```mermaid
flowchart LR
    subgraph Server Side
        CHECKIN_SVC["CheckInService"]
        TICKET_DB[(Tickets DB)]
        MANIFEST_GEN["QR Manifest\nGenerator"]
        CDN_STORE[(Manifest CDN\nSigned URL)]
    end

    subgraph Device Side
        APP["VenueStaffApp\n(PWA)"]
        IDB[(IndexedDB\nOffline Cache)]
        SYNC_Q[(Sync Queue\nPending check-ins)]
    end

    TICKET_DB -- "All ISSUED tickets\nfor event (qrHash, ticketId)" --> MANIFEST_GEN
    MANIFEST_GEN -- "Signed manifest\n(HMAC-SHA256, JSON compressed)" --> CDN_STORE
    CDN_STORE -- "Hourly manifest download\n(~4.5 MB for 50k attendees)" --> APP
    APP -- "Parse and cache\nmanifest to IndexedDB" --> IDB

    APP -- "Offline scan validation\n(lookup in IDB)" --> IDB
    IDB -- "Ticket validity result" --> APP
    APP -- "Record offline check-in" --> SYNC_Q

    APP -- "On reconnect: flush sync queue\nPOST /check-in/sync" --> CHECKIN_SVC
    CHECKIN_SVC -- "Deduplication result\n{processed, duplicates}" --> APP
    CHECKIN_SVC -- "Persist to Tickets DB" --> TICKET_DB
```

---

## Level 1 — Analytics Data Flow

The analytics pipeline processes both real-time streams (for organizer live dashboards) and batch data (for historical reports and machine learning).

```mermaid
flowchart TD
    subgraph Event Sources
        ORDER_SVC["OrderService"]
        TICKET_SVC["TicketService"]
        CHECKIN_SVC["CheckInService"]
        SEARCH_SVC["SearchService"]
        WEB_APP["Web / Mobile App\n(client-side events)"]
    end

    subgraph Stream Processing
        P31["3.1 Capture Event Stream\n(Kafka Producer)"]
        P32["3.2 Real-time Aggregation\n(Kafka Streams)"]
    end

    subgraph Batch Processing
        P33["3.3 Batch ETL\n(AWS Glue / Spark)"]
        P34["3.4 Dashboard Queries\n(Redshift / BigQuery)"]
    end

    D10[(D10 Event Stream\nKafka Topics)]
    D11[(D11 OLAP Store\nRedshift / BigQuery)]
    D12[(D12 Organizer Reports\nMaterialized Views)]
    D13[(D13 Real-time KV\nRedis)]

    ORGANIZER([Event Organizer\nDashboard])
    ML_PLATFORM([ML Platform\nRecommendation Engine])

    %% Event capture
    ORDER_SVC -- "OrderCompleted, OrderCancelled\nevents (Kafka producer)" --> P31
    TICKET_SVC -- "TicketIssued, TicketTransferred\nevents" --> P31
    CHECKIN_SVC -- "AttendeeCheckedIn events" --> P31
    SEARCH_SVC -- "SearchPerformed, EventViewed\nevents" --> P31
    WEB_APP -- "PageView, AddToCart,\nPaymentStarted client events\n(HTTPS + batched)" --> P31
    P31 -- "Produce to Kafka topics\n(partitioned by eventId)" --> D10

    %% Real-time aggregation
    D10 -- "Consume from Kafka topics\n(Kafka Streams consumer group)" --> P32
    P32 -- "Rolling window aggregates\n(1-min, 5-min windows)" --> D13
    D13 -- "Live metrics:\n{ticketsSold, revenue,\ncheckInRate}" --> ORGANIZER
    P32 -- "Real-time alerts\n(capacity threshold, refund spike)" --> ORGANIZER

    %% Batch ETL
    D10 -- "Hourly Kafka → S3 export\n(Kafka Connect S3 sink)" --> P33
    P33 -- "Transform, clean, deduplicate\nJoin with Tickets and Events DB" --> P33
    P33 -- "COPY into Redshift\n(partitioned by event_date)" --> D11

    %% Dashboard queries
    D11 -- "SQL aggregation queries\n(sales by ticket type, hourly revenue)" --> P34
    P34 -- "Refresh materialised views\nevery 15 minutes" --> D12
    D12 -- "Report data\n(revenue, attendance, conversions)" --> ORGANIZER

    %% ML pipeline
    D11 -- "Training data export\n(purchase history, browse patterns)" --> ML_PLATFORM
    ML_PLATFORM -- "Personalisation scores\n(user → event affinity)" --> D11
```

### Analytics Latency Characteristics

| Pipeline Stage | Input | Processing | Latency | Output |
|---|---|---|---|---|
| Kafka produce | Service domain events | Fire-and-forget async | < 5 ms | Kafka topic |
| Kafka Streams aggregate | Kafka topic | Rolling window (1 min) | 60–90 s end-to-end | Redis real-time KV |
| Kafka → S3 sink | Kafka topic | Micro-batch every 5 min | 5–10 min | S3 Parquet files |
| Glue ETL job | S3 Parquet | Hourly incremental | 60–90 min | Redshift |
| Dashboard refresh | Redshift | Materialised view refresh | 15 min | Dashboard |

---

## Data Classification

Every data element in the system is classified by sensitivity, storage encryption requirements, transit requirements, and GDPR scope. This table is the source of truth for the platform's data governance policy.

| Data Element | Classification | Storage Encryption | Transit Encryption | Retention Period | GDPR Personal Data |
|---|---|---|---|---|---|
| Attendee.email | PII | AES-256 (column-level) | TLS 1.3 required | 7 years (tax) | Yes — subject to erasure |
| Attendee.firstName, lastName | PII | AES-256 (column-level) | TLS 1.3 required | 7 years (tax) | Yes — subject to erasure |
| Attendee.phone | PII | AES-256 (column-level) | TLS 1.3 required | 7 years (tax) | Yes — subject to erasure |
| Attendee.dateOfBirth | PII-Sensitive | AES-256 (column-level) | TLS 1.3 required | 7 years (tax) | Yes — subject to erasure |
| Attendee.billingAddress | PII | AES-256 (column-level) | TLS 1.3 required | 7 years (tax) | Yes — subject to erasure |
| Payment.gatewayChargeId | Financial | AES-256 at rest | TLS 1.3 required | 7 years (tax/audit) | No (pseudonymous ref) |
| Payment.amount, currency | Financial | Standard DB encryption | TLS 1.3 required | 7 years (tax/audit) | No |
| Ticket.qrCodeHash | Operational | Standard DB encryption | TLS 1.3 required | 2 years after event | No |
| Ticket.pdfUrl | Operational | S3 SSE-S3 | TLS 1.3 + pre-signed URL | 1 year after event | No |
| Order.totalAmount | Financial | Standard DB encryption | TLS 1.3 required | 7 years (tax/audit) | No |
| CheckIn.checkedInAt | Operational | Standard DB encryption | TLS 1.3 required | 3 years | No |
| CheckIn.deviceId | Operational | Standard DB encryption | TLS 1.3 required | 3 years | No |
| Event.title, description | Public | None required | TLS 1.3 | Indefinite | No |
| OrganizerProfile.bankAccount | Financial-Sensitive | AES-256 (column-level) | TLS 1.3 required | 7 years (tax) | Yes (natural person only) |
| SessionToken (JWT) | Security | Redis TTL-expiry | TLS 1.3 required | 1 hour (token TTL) | No |
| Kafka event stream | Operational | MSK at-rest encryption | TLS 1.3 (MSK) | 7 days | Minimised (IDs only) |
| Redshift analytics | Operational + PII-derived | Redshift cluster encryption | TLS 1.3 | 3 years | Pseudonymised (attendeeId hash) |
| CloudWatch logs | Operational | AWS managed | TLS 1.3 | 90 days | No PII in logs (enforced) |

**GDPR Erasure Implementation**: When an attendee submits a deletion request, the following fields are overwritten with null or anonymised tokens: `firstName`, `lastName`, `email`, `phone`, `dateOfBirth`, `billingAddress`. The `attendeeId` UUID is retained as a foreign key to preserve financial audit trails, but is no longer linkable to the individual. The erasure is propagated to all Kafka consumer systems via an `AttendeeDataErased` event.

---

## Data Lineage

### Ticket.qrCodeHash Lineage

The QR code hash is a security-critical data element. Its full lifecycle from generation through validation and eventual invalidation must be traceable for security audits and dispute resolution.

```mermaid
flowchart TD
    A["OrderCompleted Event\n{orderId, lineItems, attendeeId}"] --> B

    B["TicketService\nOrderFulfillmentService.fulfillOrder()"]
    B --> C["Generate HMAC-SHA256\nhmac(SHA256, ticketId:eventId:issuedAt, eventSecret)\nResult: 64-char hex string"]
    C --> D["Write to Tickets DB\ntickets.qr_code_hash = hash\ntickets.status = ISSUED"]
    C --> E["Write QR PNG to S3\ns3://tickets/{eventId}/{ticketId}/qr.png\nACL: private, pre-signed 1yr URL"]
    C --> F["Included in PDF ticket\nEmbedded as base64 data URI\nPDF stored in S3"]
    D --> G["Publish TicketIssued Event\n{ticketId, qrHash} → Kafka"]

    G --> H["QRManifestGenerator\n(CheckInService)"]
    H --> I["Add to hourly QR manifest\n{qrHash: {ticketId, eventId, validUntil}}"]
    I --> J["Sign manifest with event HMAC key\nCompress (gzip), upload to CDN"]
    J --> K["VenueStaffApp downloads manifest\nCaches in IndexedDB"]

    D --> L["CheckInService\nValidate POST /check-in/validate"]
    L --> M{"qrHash found in DB\nAND status == ISSUED?"}
    M -- Yes --> N["Record CheckIn\n{ticketId, checkedInAt}\nUpdate ticket status CHECKED_IN"]
    M -- No --> O["Log InvalidScanAttempted\nReturn 403/404"]

    N --> P["qrHash remains in DB\nbut ticket.status = CHECKED_IN\nFurther scans → ALREADY_CHECKED_IN"]

    subgraph Invalidation Paths
        Q["TicketTransferred Event"]
        R["TicketService generates NEW qrHash\nOld hash retained with status=TRANSFERRED\nNew hash issued to new owner"]
        Q --> R
        R --> S["Old qrHash → invalid on next manifest refresh"]

        T["EventCancelled Event"]
        U["TicketService voids all tickets\nAll qrHashes status=VOIDED"]
        T --> U
        U --> V["Manifest regenerated without\nvoid ticket hashes\nDevices re-sync within 60 min"]
    end
```

### Data Lineage: Attendee Purchase to Payout

For financial audit purposes, the complete chain from attendee payment to organizer payout must be traceable:

```mermaid
flowchart LR
    A["Attendee card payment\nStripe charge {chargeId}"] --> B["Payment record\n{chargeId, amount, orderId}"]
    B --> C["Order record\n{orderId, totalAmount, eventId}"]
    C --> D["OrderItem records\n{ticketTypeId, qty, unitPrice}"]
    D --> E["Ticket records\n{ticketId, qrHash}"]
    C --> F["Organizer revenue ledger\n(Platform fee deducted)"]
    F --> G["Stripe Connect payout\nto OrganizerProfile.bankAccount"]
    G --> H["PayoutRecord\n{payoutId, amount, settledAt}"]
```

Every hop in this chain has a foreign key reference enabling point-in-time reconstruction of the full financial audit trail. Kafka event replay from the `orders.completed` topic can reconstruct the ledger independently of the database for audit reconciliation.
