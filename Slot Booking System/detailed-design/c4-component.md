# C4 Component Diagram - Slot Booking System

> **Platform Independence**: C4 Level 3 showing components within containers.

---

## Overview

The C4 Component Diagram (Level 3) shows the internal structure of containers, breaking them down into components.

---

## Backend API Container - Components

```mermaid
graph TB
    subgraph "Backend API Container"
        direction TB
        
        subgraph "Controllers"
            AUTH_CTR[Auth Controller<br/>Handles login, register, tokens]
            USER_CTR[User Controller<br/>Profile management]
            RES_CTR[Resource Controller<br/>CRUD for resources]
            BOOK_CTR[Booking Controller<br/>Booking operations]
            PAY_CTR[Payment Controller<br/>Payment processing]
            SEARCH_CTR[Search Controller<br/>Search operations]
        end
        
        subgraph "Services"
            AUTH_SVC[Auth Service<br/>Authentication logic]
            USER_SVC[User Service<br/>User management]
            RES_SVC[Resource Service<br/>Resource logic]
            SLOT_SVC[Slot Service<br/>Slot management]
            BOOK_SVC[Booking Service<br/>Booking logic]
            PAY_SVC[Payment Service<br/>Payment logic]
            NOTIF_SVC[Notification Service<br/>Send notifications]
            SEARCH_SVC[Search Service<br/>Index and search]
            WAITLIST_SVC[Waitlist Service<br/>Queue handling]
            AUDIT_SVC[Audit Service<br/>Compliance logs]
        end
        
        subgraph "Repositories"
            USER_REPO[User Repository]
            RES_REPO[Resource Repository]
            SLOT_REPO[Slot Repository]
            BOOK_REPO[Booking Repository]
            PAY_REPO[Payment Repository]
            IDEMP_REPO[Idempotency Repository]
            AUDIT_REPO[Audit Repository]
        end
        
        subgraph "External Adapters"
            PAY_ADAPT[Payment Gateway<br/>Adapter]
            NOTIF_ADAPT[Notification<br/>Provider Adapter]
            SEARCH_ADAPT[Search Index<br/>Adapter]
        end
    end
    
    %% Controller to Service
    AUTH_CTR --> AUTH_SVC
    USER_CTR --> USER_SVC
    RES_CTR --> RES_SVC
    BOOK_CTR --> BOOK_SVC
    PAY_CTR --> PAY_SVC
    SEARCH_CTR --> SEARCH_SVC
    
    %% Service dependencies
    AUTH_SVC --> USER_REPO
    USER_SVC --> USER_REPO
    RES_SVC --> RES_REPO
    RES_SVC --> SLOT_SVC
    BOOK_SVC --> SLOT_SVC
    BOOK_SVC --> PAY_SVC
    BOOK_SVC --> NOTIF_SVC
    BOOK_SVC --> IDEMP_REPO
    BOOK_SVC --> AUDIT_REPO
    WAITLIST_SVC --> BOOK_REPO
    SLOT_SVC --> SLOT_REPO
    PAY_SVC --> PAY_REPO
    
    %% External adapters
    PAY_SVC --> PAY_ADAPT
    NOTIF_SVC --> NOTIF_ADAPT
    SEARCH_SVC --> SEARCH_ADAPT
    
    %% External connections
    PAY_ADAPT --> EXT_PAY((Payment Gateway))
    NOTIF_ADAPT --> EXT_NOTIF((Notification Services))
    SEARCH_ADAPT --> EXT_SEARCH((Elasticsearch))
    
    USER_REPO --> DB[(Database)]
    RES_REPO --> DB
    SLOT_REPO --> DB
    BOOK_REPO --> DB
    PAY_REPO --> DB
    IDEMP_REPO --> DB
    AUDIT_REPO --> DB
```

---

## Booking Service Component Detail

```mermaid
graph TB
    subgraph "Booking Service Component"
        direction TB
        
        FACADE[Booking Facade<br/>Public API]
        
        subgraph "Core Logic"
            CREATE[Create Booking<br/>Handler]
            CANCEL[Cancel Booking<br/>Handler]
            RESCHEDULE[Reschedule<br/>Handler]
            QUERY[Booking Query<br/>Handler]
        end
        
        subgraph "Support"
            VALIDATOR[Booking<br/>Validator]
            PRICER[Price<br/>Calculator]
            LOCKER[Slot Lock<br/>Manager]
        end
        
        subgraph "Events"
            PUBLISHER[Event<br/>Publisher]
        end
    end
    
    API((API Layer)) --> FACADE
    FACADE --> CREATE
    FACADE --> CANCEL
    FACADE --> RESCHEDULE
    FACADE --> QUERY
    
    CREATE --> VALIDATOR
    CREATE --> PRICER
    CREATE --> LOCKER
    CREATE --> PUBLISHER
    
    CANCEL --> VALIDATOR
    CANCEL --> PUBLISHER
    
    LOCKER --> CACHE((Redis))
    PUBLISHER --> QUEUE((Message Queue))
```

---

## Payment Service Component Detail

```mermaid
graph TB
    subgraph "Payment Service Component"
        direction TB
        
        PAY_FACADE[Payment Facade]
        
        subgraph "Processors"
            CHARGE[Charge<br/>Processor]
            REFUND[Refund<br/>Processor]
            VERIFY[Verification<br/>Handler]
        end
        
        subgraph "Gateways"
            GW_FACTORY[Gateway<br/>Factory]
            STRIPE[Stripe<br/>Adapter]
            PAYPAL[PayPal<br/>Adapter]
            RAZORPAY[Razorpay<br/>Adapter]
        end
        
        subgraph "Support"
            RECEIPT[Receipt<br/>Generator]
            WEBHOOK[Webhook<br/>Handler]
        end
    end
    
    API((API)) --> PAY_FACADE
    PAY_FACADE --> CHARGE
    PAY_FACADE --> REFUND
    PAY_FACADE --> VERIFY
    
    CHARGE --> GW_FACTORY
    REFUND --> GW_FACTORY
    
    GW_FACTORY --> STRIPE
    GW_FACTORY --> PAYPAL
    GW_FACTORY --> RAZORPAY
    
    CHARGE --> RECEIPT
    
    EXT((Gateway Webhook)) --> WEBHOOK
    WEBHOOK --> VERIFY
```

---

## Component Responsibilities

| Component | Responsibility | Interfaces |
|-----------|----------------|------------|
| **Auth Controller** | Handle auth HTTP requests | REST endpoints |
| **Auth Service** | Token generation, validation | IAuthService |
| **User Service** | User CRUD, profile mgmt | IUserService |
| **Resource Service** | Resource CRUD, image handling | IResourceService |
| **Slot Service** | Slot generation, locking | ISlotService |
| **Booking Service** | Booking lifecycle | IBookingService |
| **Payment Service** | Payment orchestration | IPaymentService |
| **Notification Service** | Multi-channel dispatch | INotificationService |
| **Search Service** | Indexing, searching | ISearchService |

---

## Component Interaction Example

```mermaid
sequenceDiagram
    participant C as Controller
    participant BS as Booking Service
    participant SS as Slot Service
    participant PS as Payment Service
    participant NS as Notification Service
    participant Q as Message Queue
    
    C->>+BS: createBooking(dto)
    BS->>+SS: lockSlots(slotIds)
    SS-->>-BS: locked
    BS->>+PS: initiatePayment(booking)
    PS-->>-BS: paymentIntent
    BS-->>-C: bookingPending
    
    Note over C,Q: After payment confirmation...
    
    C->>+BS: confirmBooking(bookingId)
    BS->>+SS: confirmSlots(slotIds)
    SS-->>-BS: confirmed
    BS->>Q: publish(BookingCreated)
    Q->>NS: consume(BookingCreated)
    NS->>NS: sendConfirmation()
    BS-->>-C: bookingConfirmed
```

---

## Technology Mapping

| Component | Technology Options |
|-----------|-------------------|
| Controllers | Express.js, FastAPI, Spring MVC |
| Services | TypeScript classes, Python classes |
| Repositories | TypeORM, Prisma, SQLAlchemy |
| Event Publisher | RabbitMQ client, Kafka producer |
| Payment Adapters | Stripe SDK, PayPal SDK |
| Notification Adapters | SendGrid SDK, Twilio SDK |

---
## Implementation-Ready C4 Component

### Slot allocation rules in this document's context
- Allocation decisions must be based on **resource calendar + operational policy + channel limits** before any payment action is attempted.
- All provisional allocations require an explicit **hold record with expiry**, and expiry must be visible to clients.
- Shared-capacity resources must use atomic decrement semantics; exclusive resources must enforce single-active-booking constraints.

### Conflict resolution in this document's context
- Competing writes must use deterministic conflict handling (optimistic version checks or transactional locks as documented here).
- API and admin paths must converge on one canonical conflict reason taxonomy (`SLOT_TAKEN`, `STALE_VERSION`, `PROVIDER_BLOCKED`, `PAYMENT_STATE_MISMATCH`).
- Every conflict rejection must emit structured audit telemetry including actor, correlation ID, and rule version.

### Payment coupling / decoupling behavior
- **Coupled flow**: booking moves to confirmed only after successful authorization/capture.
- **Decoupled flow**: booking can be confirmed with `PAYMENT_PENDING`, but with a bounded grace window and auto-cancel guardrail.
- Compensation is mandatory for split-brain outcomes (payment succeeded but booking failed, or inverse).

### Cancellation and refund policy detail
- Refund outcomes depend on lead time, policy tier, no-show status, and jurisdiction-specific fee constraints.
- Refund processing must be idempotent and expose lifecycle states (`REQUESTED`, `INITIATED`, `SETTLED`, `FAILED`, `MANUAL_REVIEW`).
- Cancellation side effects must include slot reallocation and downstream notification consistency.

### Observability and incident playbook focus
- Monitor: availability latency, hold expiry lag, conflict rate, payment callback success, refund aging.
- Alerts must map to operator runbooks with first-response steps and data reconciliation queries.
- Post-incident review must record policy gaps and required control changes for this documentation area.

### Detailed implementation contracts
- Transaction boundaries for hold, confirm, cancel, and refund actions.
- Outbox/inbox idempotency strategy for webhook and event replay safety.
- Data model constraints and indexes required to prevent overlap anomalies.


### Mermaid C4 component-level view
```mermaid
flowchart LR
  Client --> ApiComp[Booking API Component]
  ApiComp --> AllocComp[Allocation Component]
  ApiComp --> ConflictComp[Conflict Component]
  ApiComp --> PayComp[Payment Component]
  ApiComp --> CancelComp[Cancellation Component]
  PayComp --> PSP[External PSP]
  ApiComp --> ObsComp[Observability Component]
```
