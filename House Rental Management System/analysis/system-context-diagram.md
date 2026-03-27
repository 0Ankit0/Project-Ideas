# System Context Diagram

## Overview
The system context diagram defines the boundaries of the house rental management platform and its interactions with external actors and services.

---

## Main System Context Diagram

```mermaid
graph TB
    subgraph Actors
        Owner((Owner / Landlord))
        Tenant((Tenant))
        MaintStaff((Maintenance Staff))
        Admin((Admin))
    end

    subgraph ExternalSystems
        PG[Payment Providers<br>Stripe / PayPal / Bank Transfer]
        Email[Email Service<br>SendGrid / SES]
        SMS[SMS Provider<br>Twilio / SNS]
        Push[Push Notification<br>FCM / APNs]
        ESign[E-Signature Provider<br>DocuSign / Adobe Sign]
        Storage[Object Storage<br>S3 / GCS]
        BgCheck[Background Check<br>TransUnion / Experian]
        Maps[Maps Provider<br>Google Maps / OSM]
        Accounting[Accounting Export<br>QuickBooks / CSV]
    end

    subgraph "House Rental Management Platform"
        Platform[REST API + Web App]
    end

    Owner -->|manage properties, leases, rent, bills, maintenance| Platform
    Tenant -->|browse, apply, sign lease, pay rent, maintenance| Platform
    MaintStaff -->|view tasks, update status, log costs| Platform
    Admin -->|verify users, resolve disputes, configure platform| Platform

    Platform -->|process payments and refunds| PG
    Platform -->|transactional emails| Email
    Platform -->|SMS reminders and OTPs| SMS
    Platform -->|push notifications| Push
    Platform -->|send and receive signed documents| ESign
    Platform -->|store documents, photos, reports| Storage
    Platform -->|tenant background and credit checks| BgCheck
    Platform -->|property geolocation and maps| Maps
    Platform -->|export financial data| Accounting
```

---

## Detailed Context With Data Flows

```mermaid
graph LR
    subgraph Clients
        OwnerWeb[Owner Web Portal]
        TenantWeb[Tenant Web App]
        TenantMobile[Tenant Mobile App]
        MaintApp[Maintenance Staff App]
        AdminUI[Admin Dashboard]
    end

    subgraph Platform
        API[REST API]
        WS[WebSocket Manager]
    end

    subgraph Payments
        Stripe[Stripe]
        PayPal[PayPal]
        BankTransfer[Bank Transfer / ACH]
    end

    subgraph Messaging
        Email[Email Provider]
        SMS[SMS Gateway]
        Push[Push Provider]
    end

    subgraph Operations
        ESign[E-Signature API]
        BgCheck[Background Check API]
        Maps[Maps API]
        Storage[Object Storage]
    end

    OwnerWeb --> API
    TenantWeb --> API
    TenantMobile --> API
    MaintApp --> API
    AdminUI --> API

    API --> WS
    API --> Stripe
    API --> PayPal
    API --> BankTransfer
    API --> Email
    API --> SMS
    API --> Push
    API --> ESign
    API --> BgCheck
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
        BgCheck[Background Check]
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
    API -- TLS --> BgCheck
```

---

## External Dependency Notes

| System | Purpose | Priority |
|--------|---------|----------|
| Payment providers | Rent and bill payment processing, refunds | Core |
| Email provider | Transactional emails, lease documents | Core |
| SMS gateway | Rent reminders, OTP, emergency maintenance alerts | Core |
| E-signature provider | Digital lease signing | Core |
| Object storage | Property photos, lease PDFs, bill scans, report exports | Core |
| Push notifications | Real-time in-app alerts for tenants and owners | Core |
| Background check API | Tenant credit and rental history screening | Optional |
| Maps provider | Property geolocation, address autocomplete | Optional |
| Accounting export | Financial data export for external accounting tools | Optional |
