# High-Level Architecture Diagram

## Overview
The rental management platform is designed as a modular API application. Each domain module (assets, bookings, agreements, payments, maintenance) is independently testable and can be extracted to a separate service if scale demands it.

---

## System Architecture Overview

```mermaid
graph TB
    subgraph "Clients"
        OwnerWeb[Owner Web Portal]
        CustomerWeb[Customer Web App]
        CustomerMobile[Customer Mobile App]
        StaffApp[Staff Mobile App]
        AdminApp[Admin Dashboard]
    end

    subgraph "Edge"
        CDN[CDN]
        WAF[WAF]
        LB[Load Balancer]
    end

    subgraph "Application"
        API[REST API Application]

        subgraph "Backend Modules"
            IAM[IAM & Auth]
            AssetMgmt[Asset & Listing Management]
            BookingMgmt[Booking & Reservation]
            AgreementMgmt[Rental Agreements]
            PricingEngine[Pricing Engine]
            PaymentMgmt[Payments & Invoices]
            DepositMgmt[Deposit & Charges]
            AssessmentMgmt[Condition Assessments]
            MaintMgmt[Maintenance & Servicing]
            Reporting[Reports & Analytics]
            Notify[Notifications & WebSocket]
        end
    end

    subgraph "Data"
        DB[(PostgreSQL)]
        Redis[(Redis)]
        Storage[(Object Storage)]
    end

    subgraph "External Services"
        PaymentGW[Payment Providers<br>Stripe / PayPal / Bank]
        ESign[E-Signature Provider<br>DocuSign / Adobe Sign]
        IDVerify[Identity Verification<br>Onfido / Jumio]
        Maps[Maps Provider]
        Messaging[Email / SMS / Push]
    end

    OwnerWeb --> CDN
    CustomerWeb --> CDN
    CustomerMobile --> CDN
    StaffApp --> CDN
    AdminApp --> CDN

    CDN --> WAF
    WAF --> LB
    LB --> API

    API --> IAM
    API --> AssetMgmt
    API --> BookingMgmt
    API --> AgreementMgmt
    API --> PricingEngine
    API --> PaymentMgmt
    API --> DepositMgmt
    API --> AssessmentMgmt
    API --> MaintMgmt
    API --> Reporting
    API --> Notify

    IAM --> DB
    AssetMgmt --> DB
    BookingMgmt --> DB
    AgreementMgmt --> DB
    PricingEngine --> DB
    PaymentMgmt --> DB
    DepositMgmt --> DB
    AssessmentMgmt --> DB
    MaintMgmt --> DB
    Reporting --> DB
    Notify --> DB

    IAM --> Redis
    BookingMgmt --> Redis
    PricingEngine --> Redis

    AssetMgmt --> Storage
    AgreementMgmt --> Storage
    AssessmentMgmt --> Storage
    Reporting --> Storage

    PaymentMgmt --> PaymentGW
    DepositMgmt --> PaymentGW
    AgreementMgmt --> ESign
    IAM --> IDVerify
    AssetMgmt --> Maps
    Notify --> Messaging
```

---

## Runtime Interaction Model

```mermaid
graph LR
    Client[Client Request] --> API[API Router]
    API --> Domain[Domain Service / Repository]
    Domain --> DB[(PostgreSQL)]
    Domain --> Redis[(Redis)]

    Domain --> Event[Domain Event / Notification Record]
    Event --> Notify[Notification Dispatcher]
    Notify --> WS[WebSocket Manager]
    Notify --> Msg[Email / SMS / Push]

    Domain --> External[Payment / E-Sign / IDVerify / Maps]
    Domain --> Storage[Object Storage]
    Worker[Async Worker] --> Domain
    Worker --> Notify
```

---

## Key Backend Responsibilities

| Module | Main Responsibilities |
|--------|-----------------------|
| IAM | JWT auth, OTP, RBAC, ID verification integration, audit log |
| Asset & Listing | Asset CRUD, custom category attributes, photo storage, availability calendar, publish/unpublish |
| Booking & Reservation | Booking creation, availability locking, instant vs manual confirmation, modification, cancellation |
| Rental Agreements | Template rendering, e-signature dispatch, signing webhooks, PDF storage, versioning |
| Pricing Engine | Multi-tier rate calculation (hourly/daily/weekly/monthly), peak pricing, discounts, tax rules |
| Payments & Invoices | Invoice generation, payment gateway integration, receipt generation, late fees, payout processing |
| Deposit & Charges | Deposit hold/release, damage deductions, dispute handling, settlement |
| Condition Assessments | Pre/post rental checklists, photo capture, comparison reports, customer countersignature |
| Maintenance | Request lifecycle, staff assignment, cost logging, preventive scheduling, calendar blocking |
| Reports & Analytics | Revenue reports, utilisation reports, tax summaries, payout history |
| Notifications | Persisted notifications, WebSocket fanout, email/SMS/push dispatch |

---

## Async Worker Responsibilities

| Job | Trigger | Action |
|-----|---------|--------|
| Booking reminder | 24h before rental start | Send reminder to customer and owner |
| Overdue return detection | Polling every 15 min | Detect late returns; apply fees; notify parties |
| Payout batch processing | Scheduled (daily/weekly) | Aggregate closed rentals; process bank transfers |
| Availability expiry | On booking timeout | Release availability hold if deposit not paid |
| Preventive service reminders | Scheduled | Alert owner of upcoming scheduled service |
| Report generation | On-demand or scheduled | Build and store report exports |
