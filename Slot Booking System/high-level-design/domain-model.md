# Domain Model - Slot Booking System

> **Platform Independence**: Uses generic entity names adaptable to any booking domain.

---

## Overview

The Domain Model represents the key entities in the business domain and their relationships, independent of implementation details.

---

## Core Domain Model

```mermaid
erDiagram
    USER ||--o{ BOOKING : makes
    USER ||--o{ REVIEW : writes
    USER ||--o{ PAYMENT : initiates
    USER {
        string userId PK
        string email
        string phone
        string name
        string role
        datetime createdAt
    }
    
    PROVIDER ||--|{ RESOURCE : owns
    PROVIDER ||--o{ PAYOUT : receives
    PROVIDER {
        string providerId PK
        string userId FK
        string businessName
        string status
        json bankDetails
    }
    
    RESOURCE ||--|{ SLOT : has
    RESOURCE ||--o{ REVIEW : receives
    RESOURCE {
        string resourceId PK
        string providerId FK
        string name
        string description
        string category
        json location
        json amenities
        decimal basePrice
    }
    
    SLOT ||--o| BOOKING : bookedBy
    SLOT {
        string slotId PK
        string resourceId FK
        datetime startTime
        datetime endTime
        string status
        decimal price
    }
    
    BOOKING ||--|| PAYMENT : paidWith
    BOOKING {
        string bookingId PK
        string userId FK
        string slotId FK
        string status
        datetime bookedAt
        string notes
    }
    
    PAYMENT ||--o| REFUND : may_have
    PAYMENT {
        string paymentId PK
        string bookingId FK
        decimal amount
        string method
        string status
        datetime paidAt
    }
    
    REFUND {
        string refundId PK
        string paymentId FK
        decimal amount
        string reason
        datetime refundedAt
    }
    
    REVIEW {
        string reviewId PK
        string userId FK
        string resourceId FK
        int rating
        string comment
        datetime createdAt
    }
    
    PAYOUT {
        string payoutId PK
        string providerId FK
        decimal amount
        string status
        datetime scheduledAt
    }
```

---

## Simplified Domain Relationships

```mermaid
graph TB
    subgraph "User Domain"
        USR[User]
        GUEST[Guest]
        REG[Registered User]
        PROV[Provider]
        ADM[Admin]
    end
    
    subgraph "Resource Domain"
        RES[Resource]
        CAT[Category]
        AMEN[Amenity]
        LOC[Location]
        IMG[Image]
    end
    
    subgraph "Scheduling Domain"
        AVAIL[Availability]
        SLOT[Slot]
        SCHED[Schedule]
    end
    
    subgraph "Booking Domain"
        BOOK[Booking]
        RECUR[Recurring Booking]
        WAIT[Waitlist]
    end
    
    subgraph "Financial Domain"
        PAY[Payment]
        REF[Refund]
        PROMO[Promo Code]
        PRICE[Pricing Rule]
        PAYOUT[Payout]
    end
    
    subgraph "Feedback Domain"
        REV[Review]
        RATE[Rating]
    end
    
    GUEST --> REG
    REG --> PROV
    REG --> ADM
    
    PROV -->|owns| RES
    RES -->|has| CAT
    RES -->|has| AMEN
    RES -->|has| LOC
    RES -->|has| IMG
    
    RES -->|defines| AVAIL
    AVAIL -->|generates| SLOT
    RES -->|has| SCHED
    
    REG -->|makes| BOOK
    BOOK -->|reserves| SLOT
    BOOK -->|may be| RECUR
    SLOT -->|may have| WAIT
    
    BOOK -->|paid with| PAY
    PAY -->|may have| REF
    BOOK -->|uses| PROMO
    RES -->|has| PRICE
    PROV -->|receives| PAYOUT
    
    REG -->|writes| REV
    REV -->|about| RES
    REV -->|includes| RATE
```

---

## Entity Definitions

### Core Entities

| Entity | Description | Domain Example |
|--------|-------------|----------------|
| **User** | Any person interacting with the system | Customer, Guest, Provider, Admin |
| **Provider** | Business/individual offering bookable resources | Futsal venue owner, Event organizer |
| **Resource** | A bookable entity | Court, Room, Table, Equipment |
| **Slot** | A specific time window for a resource | 3:00 PM - 4:00 PM on Court A |
| **Booking** | A confirmed reservation | User X has Court A on Jan 20 at 3 PM |
| **Payment** | Financial transaction for a booking | $50 paid via Stripe |

### Supporting Entities

| Entity | Description |
|--------|-------------|
| **Category** | Classification of resources (e.g., Indoor, Outdoor) |
| **Amenity** | Features of a resource (e.g., Lights, AC, Parking) |
| **Location** | Physical address with coordinates |
| **Availability** | Operating schedule for a resource |
| **PricingRule** | Time-based or conditional pricing |
| **PromoCode** | Discount codes for bookings |
| **Review** | User feedback with rating and comment |
| **Notification** | System messages to users |
| **Payout** | Provider earnings disbursement |

---

## Domain Aggregates

```mermaid
graph TB
    subgraph "User Aggregate"
        USER_ROOT((User))
        PROFILE[Profile]
        PREFS[Preferences]
        TOKENS[Auth Tokens]
        USER_ROOT --> PROFILE
        USER_ROOT --> PREFS
        USER_ROOT --> TOKENS
    end
    
    subgraph "Resource Aggregate"
        RES_ROOT((Resource))
        IMAGES[Images]
        AMENITIES[Amenities]
        PRICING[Pricing Rules]
        SCHEDULE[Schedule]
        RES_ROOT --> IMAGES
        RES_ROOT --> AMENITIES
        RES_ROOT --> PRICING
        RES_ROOT --> SCHEDULE
    end
    
    subgraph "Booking Aggregate"
        BOOK_ROOT((Booking))
        SLOTS_REF[Slot References]
        PAYMENT_REF[Payment]
        NOTES[Notes]
        BOOK_ROOT --> SLOTS_REF
        BOOK_ROOT --> PAYMENT_REF
        BOOK_ROOT --> NOTES
    end
    
    subgraph "Provider Aggregate"
        PROV_ROOT((Provider))
        BANK[Bank Details]
        RESOURCES[Resources]
        EARNINGS[Earnings]
        PROV_ROOT --> BANK
        PROV_ROOT --> RESOURCES
        PROV_ROOT --> EARNINGS
    end
```

---

## Domain Events

| Event | Triggered When | Subscribers |
|-------|----------------|-------------|
| `UserRegistered` | New user signs up | Email service, Analytics |
| `BookingCreated` | Booking confirmed | Notification, Calendar, Analytics |
| `BookingCancelled` | Booking cancelled | Notification, Refund service, Slot service |
| `PaymentCompleted` | Payment successful | Booking service, Receipt generator |
| `PaymentFailed` | Payment declined | Notification, Booking service |
| `SlotReleased` | Slot becomes available | Waitlist service |
| `ReviewPosted` | User posts review | Notification (provider), Ranking service |
| `ResourceCreated` | Provider adds resource | Admin notification (if approval needed) |
| `ProviderApproved` | Admin approves provider | Notification, Welcome flow |

---

## Domain Services

| Service | Responsibility |
|---------|----------------|
| **AvailabilityService** | Calculate available slots based on schedule and existing bookings |
| **BookingService** | Orchestrate booking creation, validation, conflict detection |
| **PricingService** | Calculate prices based on rules, time, promos |
| **PaymentService** | Handle payment processing, refunds |
| **NotificationService** | Dispatch notifications across channels |
| **SearchService** | Index and search resources |
| **SchedulingService** | Manage recurring bookings, reminders |

---

## Value Objects

| Value Object | Description | Example |
|--------------|-------------|---------|
| `TimeRange` | Start and end time | 3:00 PM - 4:00 PM |
| `Money` | Amount and currency | $50.00 USD |
| `Address` | Physical location | 123 Main St, City |
| `Coordinates` | Latitude/Longitude | 27.7172, 85.3240 |
| `Rating` | Numeric rating value | 4.5 / 5 |
| `Duration` | Time period | 1 hour |

---

## Invariants / Business Rules

| Rule | Description |
|------|-------------|
| **No Double Booking** | A slot can only be booked by one user at a time |
| **Booking Window** | Bookings must be made within allowed advance time |
| **Cancellation Policy** | Refund amount depends on time before slot |
| **Minimum Duration** | Resources have minimum booking duration |
| **Provider Verification** | Providers must be verified before going live |
| **Review Eligibility** | Only users who completed bookings can review |
