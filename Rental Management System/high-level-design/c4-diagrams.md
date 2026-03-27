# C4 Diagrams

## Overview
C4 model diagrams for the rental management system: Context (Level 1) and Container (Level 2). The platform is asset-agnostic, supporting cars, flats, gear, equipment, and more.

---

## Level 1 – System Context Diagram

```mermaid
graph TB
    Owner["Owner / Operator
    [Person]
    Lists and manages rentable assets,
    reviews bookings, oversees payments
    and maintenance"]

    Customer["Customer / Renter
    [Person]
    Searches assets, makes bookings,
    signs agreements, pays invoices,
    returns assets"]

    Staff["Staff
    [Person]
    Conducts condition assessments,
    performs maintenance tasks"]

    Admin["Platform Admin
    [Person]
    Manages users, resolves disputes,
    configures platform"]

    RMS["Rental Management System
    [Software System]
    Asset-agnostic rental management platform
    supporting any rentable category"]

    PG["Payment Gateway
    [External System]
    Stripe / PayPal / Bank Transfer"]

    ESign["E-Signature Provider
    [External System]
    DocuSign / Adobe Sign"]

    IDVerify["Identity Verification
    [External System]
    Onfido / Jumio"]

    Notify["Messaging Services
    [External System]
    Email / SMS / Push"]

    Owner -->|"manage assets, bookings, reports, payouts"| RMS
    Customer -->|"search, book, pay, assess, return, review"| RMS
    Staff -->|"assessments, maintenance tasks"| RMS
    Admin -->|"platform oversight and configuration"| RMS

    RMS -->|"process payments, deposits, refunds"| PG
    RMS -->|"send and receive signed documents"| ESign
    RMS -->|"verify customer identity"| IDVerify
    RMS -->|"email, SMS, push notifications"| Notify
```

---

## Level 2 – Container Diagram

```mermaid
graph TB
    OwnerPortal["Owner Web Portal
    [Web App: Next.js]
    Asset management, bookings,
    reports, maintenance"]

    CustomerWeb["Customer Web App
    [Web App: Next.js]
    Search, book, pay, agreements,
    assessments, reviews"]

    CustomerMobile["Customer Mobile App
    [Mobile: Flutter / React Native]
    Full customer experience on mobile"]

    StaffApp["Staff Mobile App
    [Mobile: Flutter / React Native]
    Condition assessments,
    maintenance task management"]

    AdminUI["Admin Dashboard
    [Web App: Next.js / React]
    User management, disputes,
    platform configuration"]

    subgraph "Rental Management System"
        API["REST API
        [Container: FastAPI / Node.js]
        Core business logic, auth,
        routing to domain modules"]

        Worker["Async Worker
        [Container: Celery / BullMQ]
        Booking reminders, overdue detection,
        payout batching, report generation"]

        WS["WebSocket Server
        [Container]
        Real-time push to connected clients"]

        DB["Primary Database
        [Container: PostgreSQL]
        All persistent rental domain data"]

        Redis["Cache & Task Queue
        [Container: Redis]
        Session cache, availability locks,
        task queue, rate limiting"]

        Storage["Object Storage
        [Container: S3 / GCS]
        Asset photos, signed agreements,
        assessment reports, export files"]
    end

    PG["Payment Gateway
    [External System]"]

    ESign["E-Signature Provider
    [External System]"]

    IDVerify["Identity Verification
    [External System]"]

    Notify["Messaging Services
    [External System]"]

    OwnerPortal -->|"HTTPS/REST"| API
    CustomerWeb -->|"HTTPS/REST"| API
    CustomerMobile -->|"HTTPS/REST"| API
    StaffApp -->|"HTTPS/REST"| API
    AdminUI -->|"HTTPS/REST"| API

    CustomerWeb -->|"WSS"| WS
    CustomerMobile -->|"WSS"| WS
    OwnerPortal -->|"WSS"| WS

    API -->|"read/write"| DB
    API -->|"cache + lock"| Redis
    API -->|"store/retrieve files"| Storage
    API -->|"enqueue async jobs"| Redis

    Worker -->|"read/write"| DB
    Worker -->|"dequeue jobs"| Redis
    Worker -->|"send"| Notify
    Worker -->|"store exports"| Storage

    WS -->|"read notifications"| DB

    API -->|"HTTPS"| PG
    API -->|"HTTPS"| ESign
    API -->|"HTTPS"| IDVerify
    Worker -->|"HTTPS"| Notify
```

---

## Level 2 – Container Responsibilities

| Container | Technology | Role |
|-----------|------------|------|
| REST API | FastAPI / Node.js | Core request handler; all domain modules exposed as REST endpoints |
| Async Worker | Celery / BullMQ | Booking reminders, overdue return detection, payout batching, report generation |
| WebSocket Server | FastAPI WS / Socket.io | Real-time notifications to browser and mobile app clients |
| Primary Database | PostgreSQL | Source of truth for all rental entities; JSONB for flexible asset attributes |
| Cache & Queue | Redis | JWT block list, availability locks, rate-limit counters, task queue |
| Object Storage | AWS S3 / GCS | Asset photos, signed agreement PDFs, assessment reports, financial export files |
