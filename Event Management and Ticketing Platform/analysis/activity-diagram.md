# Activity Diagram — Event Management and Ticketing Platform

## Overview

This document presents activity diagrams for the two most complex operational flows in the Event Management and Ticketing Platform: the Ticket Purchase Flow and the Event Check-in Flow. Each diagram is accompanied by a detailed narrative explaining the decisions and parallel activities involved.

---

## 1. Ticket Purchase Flow

### Narrative

The ticket purchase flow begins when an attendee visits an event page. It encompasses seat selection (optional), cart management, identity resolution, promo code application, tax calculation, payment processing, and post-purchase fulfilment. The flow branches at multiple decision points: seat availability, session timeout, promo code validity, and payment outcome. On success, the system performs multiple parallel fulfilment tasks.

```mermaid
flowchart TD
    A([Attendee visits event page]) --> B{Event status?}
    B -- "CANCELLED" --> B1[Display cancellation notice and refund info]
    B -- "PUBLISHED" --> C[Display ticket types with prices and availability]
    B -- "SOLD OUT" --> D[Display Sold Out banner]
    D --> D1{Waitlist enabled?}
    D1 -- "Yes" --> D2[Show Join Waitlist button]
    D1 -- "No" --> D3[Display sold out message only]

    C --> E[Attendee selects ticket type and quantity]
    E --> F{Reserved seating event?}
    F -- "Yes" --> G[Load interactive seat map]
    G --> H[Attendee selects seats on map]
    H --> I{Seats still available?}
    I -- "No" --> I1[Notify attendee - seats taken]
    I1 --> G
    I -- "Yes" --> J[System acquires 10-minute inventory hold lock]
    F -- "No" --> J

    J --> K[Display checkout form - personal details]
    K --> L[Attendee enters name, email, phone]
    L --> M{Promo code entered?}
    M -- "Yes" --> N[Validate promo code via PromotionService]
    N --> O{Code valid?}
    O -- "No" --> P[Display error message]
    P --> M
    O -- "Yes" --> Q[Apply discount to order]
    M -- "No" --> Q

    Q --> R[Call TaxService to calculate applicable taxes]
    R --> S[Display order summary - items, discount, tax, total]
    S --> T{Hold timer expired?}
    T -- "Yes" --> T1[Release holds - display session expired]
    T1 --> A
    T -- "No" --> U[Attendee reviews and confirms order]

    U --> V[Attendee enters payment details - Stripe hosted fields]
    V --> W[Submit PaymentIntent to Stripe]
    W --> X{Payment result?}
    X -- "Declined" --> X1[Display decline error - card details retained]
    X1 --> V
    X -- "Error/Timeout" --> X2[Log error - offer retry or alternative payment]
    X2 --> V
    X -- "Success" --> Y[Stripe confirms charge]

    Y --> Z[Atomic inventory decrement transaction]
    Z --> Z1{Decrement successful?}
    Z1 -- "No - race condition" --> Z2[Void/refund Stripe charge]
    Z2 --> Z3[Notify attendee - tickets unavailable]
    Z3 --> D2
    Z1 -- "Yes" --> AA[Create Order record - status PAID]
    AA --> AB[Create OrderItems and Attendee records]
    AB --> AC[Generate unique QR codes per ticket]

    AC --> AD{Parallel fulfilment}
    AD --> AE[Send confirmation email via SendGrid]
    AD --> AF[Publish TicketPurchased domain event to Kafka]
    AD --> AG{Streaming event?}
    AG -- "Yes" --> AH[Generate unique meeting join link via Zoom/Teams API]
    AG -- "No" --> AI[Skip]
    AH --> AJ[Include join link in confirmation email]
    AE --> AK([Attendee receives confirmation email with QR code])
    AF --> AL[Downstream services update analytics, waitlist, etc.]
```

### Key Decision Points

| Decision | Options | Consequence |
|---|---|---|
| Event status | Published / Sold Out / Cancelled | Routes to appropriate experience |
| Reserved seating | Yes / No | Triggers seat map interaction |
| Seats available | Yes / No | Proceeds or returns to map |
| Promo code | Entered / Not entered | Validates or skips discount |
| Hold timer expired | Yes / No | Restarts flow or proceeds |
| Payment result | Success / Declined / Error | Continues or retries |
| Inventory decrement | Success / Race condition | Creates order or triggers refund |

---

## 2. Event Check-in Flow

### Narrative

The check-in flow covers the complete experience from a staff member arriving at the venue through to admitting an attendee and optionally printing their badge. A critical aspect of this flow is the offline capability: the Check-in app caches event data at startup so that connectivity loss does not halt operations. Scan events are queued locally and synchronised when connectivity is restored.

```mermaid
flowchart TD
    START([Check-in Staff opens Check-in App]) --> A[Staff authenticates with credentials]
    A --> B[App fetches event list for today]
    B --> C[Staff selects active event and gate]
    C --> D[App downloads attendee manifest to local cache]
    D --> E[App activates QR scanner]

    E --> F{Network status?}
    F -- "Online" --> G[Online scan mode active]
    F -- "Offline" --> H[Offline scan mode - using local cache]

    G --> I[Attendee presents QR code]
    H --> I

    I --> J[App decodes QR payload - ticket ID + token]
    J --> K{Scan mode?}
    K -- "Online" --> L[Send check-in request to CheckInService API]
    K -- "Offline" --> M[Validate against local cache]

    L --> N{API response?}
    N -- "Valid - not checked in" --> O[Mark as CHECKED_IN in API]
    N -- "Already checked in" --> P[Display RED screen - Already Used]
    P --> Q[Show first scan timestamp and gate]
    Q --> E
    N -- "Invalid ticket / token mismatch" --> R[Display RED screen - Invalid Ticket]
    R --> E
    N -- "Cancelled / Refunded" --> S[Display RED screen - Ticket Cancelled]
    S --> E
    N -- "API timeout" --> T[Fallback to offline cache validation]
    T --> M

    M --> U{Found in local cache?}
    U -- "No" --> V[Display YELLOW warning - Cannot verify - supervisor needed]
    V --> E
    U -- "Yes" --> W{Local status?}
    W -- "Already marked checked in locally" --> P
    W -- "Valid" --> X[Mark checked in locally - queue sync event]
    X --> O

    O --> Y[Display GREEN screen - attendee name and ticket type]
    Y --> Z{Badge printing configured?}
    Z -- "Yes" --> AA[Publish CheckInCompleted event]
    Z -- "No" --> AB[Log scan event]
    AA --> AC[BadgeService receives event]
    AC --> AD[Send print job to network printer]
    AD --> AE{Print success?}
    AE -- "Yes" --> AF[Display print confirmation on screen]
    AE -- "No - printer offline" --> AG[Display print error - retry or skip]
    AF --> E
    AG --> AH{Manual reprint later?}
    AH -- "Yes" --> AI[Queue reprint request]
    AH -- "No" --> E
    AB --> E

    subgraph SyncProcess["Background Sync Process"]
        SYNC1[Every 30 seconds - sync offline check-in queue]
        SYNC2{Items in queue?}
        SYNC3[POST queued check-ins to CheckInService]
        SYNC4{Conflict detected?}
        SYNC5[Log conflict for supervisor review]
        SYNC6[Clear synced items from local queue]
        SYNC1 --> SYNC2
        SYNC2 -- "Yes" --> SYNC3
        SYNC2 -- "No" --> SYNC1
        SYNC3 --> SYNC4
        SYNC4 -- "Yes" --> SYNC5
        SYNC4 -- "No" --> SYNC6
        SYNC5 --> SYNC6
        SYNC6 --> SYNC1
    end
```

### Check-in Status Codes

| Status Code | Screen Colour | Message | Action Required |
|---|---|---|---|
| `VALID` | Green | Attendee name + ticket type | Admit attendee |
| `ALREADY_CHECKED_IN` | Red | "Already used — [datetime]" | Do not admit; escalate if disputed |
| `INVALID_TOKEN` | Red | "Invalid ticket" | Do not admit |
| `CANCELLED` | Red | "Ticket cancelled" | Do not admit; direct to help desk |
| `REFUNDED` | Red | "Ticket refunded" | Do not admit; direct to help desk |
| `NOT_FOUND_OFFLINE` | Yellow | "Cannot verify — needs supervisor" | Hold attendee; supervisor lookup |
| `API_TIMEOUT` | Yellow | "Falling back to offline mode" | Verify against local cache |

### Offline Mode Considerations

The Check-in app is designed to remain operational during network outages, which are common in large venues. Key design decisions:

1. **Manifest pre-loading**: At app launch, the full attendee list (ticket IDs, QR tokens, names, ticket types) is downloaded and stored in the device's IndexedDB.
2. **Optimistic offline check-in**: A check-in performed offline is immediately reflected locally to prevent double-admit.
3. **Sync conflict resolution**: If a ticket was checked in at another gate during offline period, the conflict is logged but the second check-in is not reversed (the supervisor sees the conflict log).
4. **Manifest refresh**: Staff can manually trigger a manifest refresh when connectivity is restored.
5. **Security note**: The local cache does not store payment information or full personal data—only the minimum needed for check-in validation.
