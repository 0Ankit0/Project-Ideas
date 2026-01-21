# System Context Diagram - Slot Booking System

> **Platform Independence**: External systems shown are representative; actual integrations depend on deployment.

---

## Overview

The System Context Diagram shows the Slot Booking System (the system under design) and its interactions with external actors and systems.

---

## System Context Diagram

```mermaid
graph TB
    subgraph External Actors
        User((User))
        Provider((Provider))
        Admin((Admin))
    end
    
    subgraph "Slot Booking System"
        SBS[Slot Booking<br/>System]
    end
    
    subgraph External Systems
        PG[Payment Gateway<br/>Stripe / PayPal / Razorpay]
        Email[Email Service<br/>SendGrid / SES / SMTP]
        SMS[SMS Provider<br/>Twilio / Vonage]
        Push[Push Notification<br/>FCM / APNs]
        Maps[Maps API<br/>Google Maps / Mapbox]
        OAuth[OAuth Providers<br/>Google / Facebook / Apple]
        Storage[File Storage<br/>S3 / Cloud Storage]
        Analytics[Analytics<br/>Google Analytics / Mixpanel]
    end
    
    %% Actor interactions
    User -->|Browse, Book,<br/>Pay, Review| SBS
    Provider -->|Manage Resources,<br/>View Bookings| SBS
    Admin -->|Configure System,<br/>Manage Users| SBS
    
    SBS -->|Confirmation,<br/>Receipts| User
    SBS -->|Booking Alerts,<br/>Reports| Provider
    SBS -->|Alerts,<br/>Reports| Admin
    
    %% External system interactions
    SBS <-->|Process Payments,<br/>Refunds| PG
    SBS -->|Send Emails| Email
    SBS -->|Send SMS| SMS
    SBS -->|Send Push| Push
    SBS <-->|Geocoding,<br/>Maps| Maps
    SBS <-->|Authentication| OAuth
    SBS <-->|Store/Retrieve<br/>Files| Storage
    SBS -->|Track Events| Analytics
    
    style SBS fill:#2196f3,color:#fff
```

---

## Detailed Context with Data Flows

```mermaid
flowchart TB
    subgraph Users
        U1[End User]
        U2[Resource Provider]
        U3[Platform Admin]
    end
    
    subgraph "Slot Booking System Boundary"
        direction TB
        WEB[Web Application]
        MOB[Mobile Apps]
        API[API Gateway]
        CORE[Core System]
        
        WEB --> API
        MOB --> API
        API --> CORE
    end
    
    subgraph "External Services"
        direction TB
        
        subgraph "Payment"
            PAY1[Stripe]
            PAY2[PayPal]
            PAY3[Local Gateway]
        end
        
        subgraph "Communication"
            MAIL[Email Provider]
            SMSP[SMS Provider]
            PUSHP[Push Service]
        end
        
        subgraph "Third Party"
            MAPS[Maps Service]
            AUTH[OAuth Provider]
            CDN[CDN / Storage]
        end
    end
    
    U1 <-->|HTTP/HTTPS| WEB
    U1 <-->|HTTPS| MOB
    U2 <-->|HTTP/HTTPS| WEB
    U3 <-->|HTTP/HTTPS| WEB
    
    CORE <-->|REST API| PAY1
    CORE <-->|REST API| PAY2
    CORE <-->|REST API| PAY3
    
    CORE -->|SMTP/API| MAIL
    CORE -->|REST API| SMSP
    CORE -->|REST API| PUSHP
    
    CORE <-->|REST API| MAPS
    CORE <-->|OAuth 2.0| AUTH
    CORE <-->|S3 API| CDN
```

---

## External System Details

| System | Purpose | Protocol | Data Exchanged |
|--------|---------|----------|----------------|
| **Payment Gateway** | Process payments, refunds | REST API | Payment requests, transaction status, webhooks |
| **Email Service** | Transactional emails | SMTP/REST | Booking confirmations, receipts, notifications |
| **SMS Provider** | SMS notifications, OTP | REST API | Text messages, delivery status |
| **Push Service** | Mobile push notifications | REST API | Push messages, device tokens |
| **Maps API** | Location services | REST API | Geocoding, map tiles, directions |
| **OAuth Providers** | Social authentication | OAuth 2.0 | User identity, profile data |
| **File Storage** | Store images, documents | S3/REST | Resource images, invoices |
| **Analytics** | Usage tracking | JavaScript/REST | User events, page views |

---

## System Boundaries

### What's Inside the System
- User registration and authentication
- Resource and slot management
- Booking lifecycle management
- Payment orchestration
- Notification dispatching
- Reporting and analytics aggregation
- Admin configuration

### What's Outside the System
- Actual payment processing (delegated to gateways)
- Email/SMS delivery (delegated to providers)
- File storage (delegated to cloud storage)
- Map rendering (delegated to map services)
- Identity verification (delegated to OAuth providers)

---

## Integration Points

```mermaid
graph LR
    subgraph "Inbound"
        A1[User Requests]
        A2[Provider Requests]
        A3[Admin Requests]
        A4[Payment Webhooks]
        A5[OAuth Callbacks]
    end
    
    SBS((Slot Booking<br/>System))
    
    subgraph "Outbound"
        B1[Payment Requests]
        B2[Email Dispatch]
        B3[SMS Dispatch]
        B4[Push Dispatch]
        B5[Map Queries]
        B6[File Operations]
    end
    
    A1 --> SBS
    A2 --> SBS
    A3 --> SBS
    A4 --> SBS
    A5 --> SBS
    
    SBS --> B1
    SBS --> B2
    SBS --> B3
    SBS --> B4
    SBS --> B5
    SBS --> B6
```

---

## Trust Boundaries

| Boundary | Inside | Outside | Protection |
|----------|--------|---------|------------|
| **Public Internet** | External Users | System | TLS, WAF, Rate Limiting |
| **API Gateway** | Internal Services | External APIs | API Keys, OAuth |
| **Database Layer** | Application | Data Store | Connection Encryption, RBAC |
| **Payment Zone** | System | Payment Gateway | PCI DSS, Tokenization |
