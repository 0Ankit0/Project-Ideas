# Component Diagram - Slot Booking System

> **Platform Independence**: Shows software modules independent of technology choices.

---

## Overview

The Component Diagram shows how the system is divided into software components and their dependencies.

---

## High-Level Component View

```mermaid
graph TB
    subgraph "Presentation Layer"
        WEB[Web UI<br/>Component]
        MOBILE[Mobile UI<br/>Component]
        ADMIN[Admin UI<br/>Component]
    end
    
    subgraph "API Layer"
        GW[API Gateway<br/>Component]
        AUTH[Auth<br/>Middleware]
    end
    
    subgraph "Service Layer"
        USER_SVC[User<br/>Service]
        RESOURCE_SVC[Resource<br/>Service]
        SLOT_SVC[Slot<br/>Service]
        BOOKING_SVC[Booking<br/>Service]
        PAYMENT_SVC[Payment<br/>Service]
        NOTIFICATION_SVC[Notification<br/>Service]
        SEARCH_SVC[Search<br/>Service]
        WAITLIST_SVC[Waitlist<br/>Service]
        AUDIT_SVC[Audit<br/>Service]
        WEBHOOK_SVC[Webhook<br/>Service]
    end
    
    subgraph "Domain Layer"
        USER_DOM[User<br/>Domain]
        RESOURCE_DOM[Resource<br/>Domain]
        BOOKING_DOM[Booking<br/>Domain]
        PAYMENT_DOM[Payment<br/>Domain]
    end
    
    subgraph "Infrastructure Layer"
        DB_REPO[Database<br/>Repository]
        CACHE_REPO[Cache<br/>Repository]
        QUEUE_PUB[Message<br/>Publisher]
        EXT_PAY[Payment<br/>Gateway Adapter]
        EXT_NOTIF[Notification<br/>Provider Adapter]
        IDEMP_REPO[Idempotency<br/>Store]
        AUDIT_REPO[Audit Log<br/>Store]
    end
    
    WEB --> GW
    MOBILE --> GW
    ADMIN --> GW
    
    GW --> AUTH
    AUTH --> USER_SVC
    AUTH --> RESOURCE_SVC
    AUTH --> SLOT_SVC
    AUTH --> BOOKING_SVC
    AUTH --> PAYMENT_SVC
    AUTH --> SEARCH_SVC
    
    USER_SVC --> USER_DOM
    RESOURCE_SVC --> RESOURCE_DOM
    SLOT_SVC --> RESOURCE_DOM
    BOOKING_SVC --> BOOKING_DOM
    PAYMENT_SVC --> PAYMENT_DOM
    
    USER_DOM --> DB_REPO
    RESOURCE_DOM --> DB_REPO
    BOOKING_DOM --> DB_REPO
    BOOKING_DOM --> CACHE_REPO
    PAYMENT_DOM --> DB_REPO
    BOOKING_DOM --> IDEMP_REPO
    BOOKING_DOM --> AUDIT_REPO
    
    BOOKING_SVC --> QUEUE_PUB
    QUEUE_PUB --> NOTIFICATION_SVC
    PAYMENT_SVC --> EXT_PAY
    NOTIFICATION_SVC --> EXT_NOTIF
    WAITLIST_SVC --> DB_REPO
    WEBHOOK_SVC --> PAYMENT_SVC
```

---

## Detailed Component Breakdown

### API Gateway Component

```mermaid
graph LR
    subgraph "API Gateway"
        ROUTER[Request<br/>Router]
        RATE[Rate<br/>Limiter]
        AUTH[Auth<br/>Handler]
        CORS[CORS<br/>Handler]
        LOG[Request<br/>Logger]
        COMPRESS[Response<br/>Compressor]
    end
    
    IN((Incoming<br/>Request)) --> RATE
    RATE --> CORS
    CORS --> AUTH
    AUTH --> LOG
    LOG --> ROUTER
    ROUTER --> OUT((Service))
    OUT --> COMPRESS
    COMPRESS --> RES((Response))
```

### Booking Service Components

```mermaid
graph TB
    subgraph "Booking Service"
        CTRL[Booking<br/>Controller]
        BIZ[Booking<br/>Business Logic]
        SLOT[Slot<br/>Manager]
        PRICE[Price<br/>Calculator]
        LOCK[Lock<br/>Manager]
        VAL[Validator]
    end
    
    API((API Gateway)) --> CTRL
    CTRL --> VAL
    VAL --> BIZ
    BIZ --> SLOT
    BIZ --> PRICE
    BIZ --> LOCK
    
    SLOT --> SLOT_DB[(Slot DB)]
    LOCK --> CACHE[(Redis)]
```

### Payment Service Components

```mermaid
graph TB
    subgraph "Payment Service"
        PAY_CTRL[Payment<br/>Controller]
        PAY_PROC[Payment<br/>Processor]
        REF_PROC[Refund<br/>Processor]
        RECEIPT[Receipt<br/>Generator]
        WEBHOOK[Webhook<br/>Handler]
    end
    
    subgraph "Gateway Adapters"
        STRIPE[Stripe<br/>Adapter]
        PAYPAL[PayPal<br/>Adapter]
        RAZORPAY[Razorpay<br/>Adapter]
    end
    
    API((API)) --> PAY_CTRL
    PAY_CTRL --> PAY_PROC
    PAY_CTRL --> REF_PROC
    PAY_PROC --> RECEIPT
    
    PAY_PROC --> STRIPE
    PAY_PROC --> PAYPAL
    PAY_PROC --> RAZORPAY
    
    EXT((Payment Gateway)) --> WEBHOOK
    WEBHOOK --> PAY_PROC
```

### Notification Service Components

```mermaid
graph TB
    subgraph "Notification Service"
        DISPATCHER[Notification<br/>Dispatcher]
        TEMPLATE[Template<br/>Engine]
        PREFS[Preference<br/>Checker]
        SCHEDULER[Reminder<br/>Scheduler]
    end
    
    subgraph "Channel Providers"
        EMAIL[Email<br/>Provider]
        SMS[SMS<br/>Provider]
        PUSH[Push<br/>Provider]
    end
    
    QUEUE((Message Queue)) --> DISPATCHER
    DISPATCHER --> PREFS
    PREFS --> TEMPLATE
    
    TEMPLATE --> EMAIL
    TEMPLATE --> SMS
    TEMPLATE --> PUSH
    
    SCHEDULER --> DISPATCHER
```

---

## Component Dependencies Matrix

| Component | Depends On | Depended By |
|-----------|------------|-------------|
| API Gateway | Auth Middleware | All Services |
| User Service | User Repository | Booking, Auth |
| Resource Service | Resource Repository, Slot Manager | Booking, Search |
| Booking Service | Slot, Payment, Notification | API Gateway |
| Payment Service | Gateway Adapters | Booking |
| Notification Service | Provider Adapters | All Services |
| Search Service | Search Index | API Gateway |

---

## Package/Module Structure

```
src/
├── api/
│   ├── controllers/
│   │   ├── auth.controller.ts
│   │   ├── booking.controller.ts
│   │   ├── payment.controller.ts
│   │   ├── resource.controller.ts
│   │   └── user.controller.ts
│   ├── middleware/
│   │   ├── auth.middleware.ts
│   │   ├── validation.middleware.ts
│   │   └── rate-limit.middleware.ts
│   └── routes/
│
├── services/
│   ├── booking.service.ts
│   ├── payment.service.ts
│   ├── notification.service.ts
│   ├── resource.service.ts
│   ├── search.service.ts
│   └── user.service.ts
│
├── domain/
│   ├── entities/
│   ├── value-objects/
│   ├── events/
│   └── services/
│
├── infrastructure/
│   ├── database/
│   │   ├── repositories/
│   │   └── migrations/
│   ├── cache/
│   ├── queue/
│   └── external/
│       ├── payment-gateways/
│       └── notification-providers/
│
└── shared/
    ├── utils/
    ├── constants/
    └── types/
```

---

## Interface Contracts

| Interface | Methods | Implemented By |
|-----------|---------|----------------|
| `IBookingService` | createBooking, cancelBooking, getBooking | BookingService |
| `IPaymentGateway` | charge, refund, verify | StripeAdapter, PayPalAdapter |
| `INotificationProvider` | send, sendBulk | EmailProvider, SMSProvider |
| `IRepository<T>` | find, save, update, delete | All Repositories |
| `ICacheService` | get, set, delete, lock | RedisCacheService |
