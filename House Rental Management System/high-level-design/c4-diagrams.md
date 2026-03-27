# C4 Diagrams

## Overview
C4 model diagrams for the house rental management system: Context (Level 1) and Container (Level 2).

---

## Level 1 – System Context Diagram

```mermaid
graph TB
    Owner["Owner / Landlord
    [Person]
    Manages properties, tenants,
    leases, rent, bills, maintenance"]

    Tenant["Tenant
    [Person]
    Browses units, applies for lease,
    pays rent, submits maintenance requests"]

    MaintStaff["Maintenance Staff
    [Person]
    Receives and resolves
    maintenance tasks"]

    Admin["Platform Admin
    [Person]
    Manages users, verifies docs,
    resolves disputes"]

    HRMS["House Rental Management System
    [Software System]
    Full-stack rental management platform
    with web and mobile interfaces"]

    PG["Payment Gateway
    [External System]
    Stripe / PayPal / Bank Transfer"]

    ESign["E-Signature Provider
    [External System]
    DocuSign / Adobe Sign"]

    BgCheck["Background Check API
    [External System]
    Credit & rental history screening"]

    Notify["Messaging Services
    [External System]
    Email / SMS / Push notifications"]

    Owner -->|"manage properties, leases, reports"| HRMS
    Tenant -->|"browse, apply, pay, request"| HRMS
    MaintStaff -->|"view tasks, update status"| HRMS
    Admin -->|"oversee platform, manage users"| HRMS

    HRMS -->|"process payments"| PG
    HRMS -->|"send documents for signing"| ESign
    HRMS -->|"screen tenants"| BgCheck
    HRMS -->|"send email, SMS, push"| Notify
```

---

## Level 2 – Container Diagram

```mermaid
graph TB
    Owner["Owner Portal
    [Web Application]
    Next.js"]

    TenantWeb["Tenant Web App
    [Web Application]
    Next.js"]

    TenantMobile["Tenant Mobile App
    [Mobile Application]
    Flutter / React Native"]

    MaintApp["Maintenance App
    [Mobile Application]
    Flutter / React Native"]

    AdminUI["Admin Dashboard
    [Web Application]
    Next.js / React"]

    subgraph "House Rental Management System"
        API["REST API
        [Container: FastAPI / Node.js]
        Handles all business logic,
        authentication, and data access"]

        Worker["Async Worker
        [Container: Celery / BullMQ]
        Billing cycles, notifications,
        report generation"]

        WS["WebSocket Server
        [Container]
        Real-time push to connected clients"]

        DB["Primary Database
        [Container: PostgreSQL]
        Core relational data store"]

        Redis["Cache & Queue
        [Container: Redis]
        Session cache, task queue,
        rate limiting"]

        Storage["Object Storage
        [Container: S3 / GCS]
        Documents, photos, signed PDFs,
        report exports"]
    end

    PG["Payment Gateway
    [External System]"]

    ESign["E-Signature Provider
    [External System]"]

    Notify["Messaging Services
    [External System]"]

    Owner -->|"HTTPS"| API
    TenantWeb -->|"HTTPS"| API
    TenantMobile -->|"HTTPS"| API
    MaintApp -->|"HTTPS"| API
    AdminUI -->|"HTTPS"| API

    TenantWeb -->|"WSS"| WS
    TenantMobile -->|"WSS"| WS
    Owner -->|"WSS"| WS

    API -->|"read/write"| DB
    API -->|"cache"| Redis
    API -->|"store/retrieve"| Storage
    API -->|"enqueue jobs"| Redis

    Worker -->|"read/write"| DB
    Worker -->|"read queue"| Redis
    Worker -->|"send"| Notify
    Worker -->|"store exports"| Storage

    WS -->|"read notifications"| DB

    API -->|"HTTPS"| PG
    API -->|"HTTPS"| ESign
    Worker -->|"HTTPS"| Notify
```

---

## Level 2 – Container Interaction Detail

| Container | Technology | Role |
|-----------|------------|------|
| REST API | FastAPI / Node.js | Core request handler; all business modules |
| Async Worker | Celery / BullMQ | Scheduled billing, notification dispatch, report generation |
| WebSocket Server | FastAPI WebSocket / Socket.io | Real-time notifications to connected browser/app clients |
| Primary Database | PostgreSQL | Source of truth for all entities |
| Cache & Queue | Redis | JWT block list, rate-limit counters, async task queue |
| Object Storage | AWS S3 / GCS | Property photos, lease PDFs, bill scans, inspection reports |
