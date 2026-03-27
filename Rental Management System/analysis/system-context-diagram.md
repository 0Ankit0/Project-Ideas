# System Context Diagram

## Overview
System context diagrams defining the boundaries of the rental management platform and its interactions with external actors and services, applicable to any asset type (cars, flats, gear, equipment, etc.).

---

## Main System Context Diagram

```mermaid
graph TB
    subgraph Actors
        Owner((Owner / Operator))
        Customer((Customer / Renter))
        Staff((Staff))
        Admin((Admin))
    end

    subgraph ExternalSystems
        PG[Payment Providers<br>Stripe / PayPal / Bank Transfer]
        Email[Email Service<br>SendGrid / SES]
        SMS[SMS Provider<br>Twilio / SNS]
        Push[Push Notifications<br>FCM / APNs]
        ESign[E-Signature Provider<br>DocuSign / Adobe Sign]
        Storage[Object Storage<br>S3 / GCS]
        Maps[Maps Provider<br>Google Maps / OSM]
        ID[Identity Verification<br>Onfido / Jumio]
        Accounting[Accounting Export<br>QuickBooks / Xero / CSV]
    end

    subgraph "Rental Management Platform"
        Platform[REST API + Web & Mobile App]
    end

    Owner -->|manage assets, bookings, agreements, payments, maintenance| Platform
    Customer -->|search, book, sign, pay, return, review| Platform
    Staff -->|assess assets, update maintenance tasks| Platform
    Admin -->|verify users, resolve disputes, configure platform| Platform

    Platform -->|process payments and refunds| PG
    Platform -->|transactional emails| Email
    Platform -->|SMS reminders and OTPs| SMS
    Platform -->|push and WebSocket notifications| Push
    Platform -->|send and retrieve signed documents| ESign
    Platform -->|store assets photos, agreements, assessments, reports| Storage
    Platform -->|asset geolocation and pickup/return maps| Maps
    Platform -->|customer identity verification| ID
    Platform -->|export financial data| Accounting
```

---

## Detailed Context With Data Flows

```mermaid
graph LR
    subgraph Clients
        OwnerWeb[Owner Web Portal]
        CustomerWeb[Customer Web App]
        CustomerMobile[Customer Mobile App]
        StaffApp[Staff Mobile App]
        AdminUI[Admin Dashboard]
    end

    subgraph Platform
        API[REST API]
        WS[WebSocket Manager]
    end

    subgraph Payments
        Stripe[Stripe]
        PayPal[PayPal]
        Bank[Bank Transfer / ACH]
    end

    subgraph Messaging
        Email[Email Provider]
        SMS[SMS Gateway]
        Push[Push Provider]
    end

    subgraph Operations
        ESign[E-Signature API]
        ID[Identity Verification API]
        Maps[Maps API]
        Storage[Object Storage]
    end

    OwnerWeb --> API
    CustomerWeb --> API
    CustomerMobile --> API
    StaffApp --> API
    AdminUI --> API

    API --> WS
    API --> Stripe
    API --> PayPal
    API --> Bank
    API --> Email
    API --> SMS
    API --> Push
    API --> ESign
    API --> ID
    API --> Maps
    API --> Storage
```

---

## Security Boundaries

```mermaid
graph TB
    subgraph "Public Zone"
        Internet[Internet]
        CDN[CDN / Static Assets]
    end

    subgraph "Edge Zone"
        WAF[Web Application Firewall]
        LB[Load Balancer]
    end

    subgraph "Application Zone"
        API[REST API Application]
        Redis[Redis Cache]
        Worker[Async Task Worker]
        WS[WebSocket Manager]
    end

    subgraph "Data Zone"
        DB[(Primary Database)]
        Storage[(Object Storage)]
    end

    subgraph "External Services"
        PG[Payment Providers]
        Notify[Email / SMS / Push]
        ESign[E-Signature Provider]
        ID[Identity Verification]
    end

    Internet --> CDN
    CDN --> WAF
    WAF --> LB
    LB --> API
    API --> Redis
    API --> Worker
    API --> WS
    API --> DB
    API --> Storage
    API -- TLS --> PG
    API -- TLS --> Notify
    API -- TLS --> ESign
    API -- TLS --> ID
```

---

## External Dependency Notes

| System | Purpose | Priority |
|--------|---------|----------|
| Payment providers | Booking payment, deposit hold, refunds, additional charges | Core |
| Email provider | Transactional emails, agreement documents | Core |
| SMS gateway | Booking reminders, OTP, overdue alerts | Core |
| E-signature provider | Digital rental agreement signing | Core |
| Object storage | Asset photos, signed PDFs, assessment reports, exports | Core |
| Push notifications | Real-time in-app alerts for all actors | Core |
| Identity verification | Customer ID check (driving licence, passport) | High |
| Maps provider | Asset geolocation, pickup/return location display | Optional |
| Accounting export | Financial data export to accounting tools | Optional |
