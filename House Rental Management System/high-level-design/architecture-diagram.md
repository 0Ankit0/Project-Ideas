# High-Level Architecture Diagram

## Overview
This document describes the high-level architecture of the house rental management platform — a modular API application backed by a relational database, object storage, async workers, and WebSocket fanout for real-time notifications.

---

## System Architecture Overview

```mermaid
graph TB
    subgraph "Clients"
        OwnerWeb[Owner Web Portal]
        TenantWeb[Tenant Web App]
        TenantMobile[Tenant Mobile App]
        MaintApp[Maintenance Staff App]
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
            PropertyMgmt[Properties & Units]
            ApplicationMgmt[Applications & Screening]
            LeaseMgmt[Leases & Deposits]
            RentMgmt[Rent Invoicing & Payments]
            BillMgmt[Bills & Utilities]
            MaintMgmt[Maintenance & Inspections]
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
        PaymentGW[Payment Providers]
        ESignProvider[E-Signature Provider]
        BgCheckProvider[Background Check API]
        Maps[Maps Provider]
        Messaging[Email / SMS / Push]
    end

    OwnerWeb --> CDN
    TenantWeb --> CDN
    TenantMobile --> CDN
    MaintApp --> CDN
    AdminApp --> CDN

    CDN --> WAF
    WAF --> LB
    LB --> API

    API --> IAM
    API --> PropertyMgmt
    API --> ApplicationMgmt
    API --> LeaseMgmt
    API --> RentMgmt
    API --> BillMgmt
    API --> MaintMgmt
    API --> Reporting
    API --> Notify

    IAM --> DB
    PropertyMgmt --> DB
    ApplicationMgmt --> DB
    LeaseMgmt --> DB
    RentMgmt --> DB
    BillMgmt --> DB
    MaintMgmt --> DB
    Reporting --> DB
    Notify --> DB

    IAM --> Redis
    PropertyMgmt --> Redis
    RentMgmt --> Redis

    PropertyMgmt --> Storage
    LeaseMgmt --> Storage
    MaintMgmt --> Storage
    Reporting --> Storage

    RentMgmt --> PaymentGW
    BillMgmt --> PaymentGW
    LeaseMgmt --> ESignProvider
    ApplicationMgmt --> BgCheckProvider
    PropertyMgmt --> Maps
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

    Domain --> Event[Domain Event / Notification]
    Event --> Notify[Notification Dispatcher]
    Notify --> WS[WebSocket Manager]
    Notify --> Msg[Email / SMS / Push]

    Domain --> External[Payment / E-Sign / BgCheck / Maps]
    Domain --> Storage[Object Storage]
```

---

## Key Backend Responsibilities

| Module | Main Responsibilities |
|--------|-----------------------|
| IAM | JWT auth, OTP, RBAC, session management, admin audit log |
| Properties & Units | Property CRUD, unit management, listing publish/unpublish, photo storage |
| Applications | Application submission, document upload, background check integration, screening |
| Leases & Deposits | Lease creation from templates, e-signature flow, deposit tracking, renewal/termination |
| Rent Invoicing | Automated invoice generation, payment gateway integration, late fees, receipt generation |
| Bills & Utilities | Bill creation, common-area split, dispute lifecycle, payment reconciliation |
| Maintenance | Request lifecycle (open → close), staff assignment, cost logging, preventive tasks |
| Inspections | Move-in/out inspection records, finding logs, photo storage, report generation |
| Reports & Analytics | Rent roll, income/expense reports, tax summaries, occupancy analytics |
| Notifications | Persisted notifications, WebSocket fanout, email/SMS/push dispatch |

---

## Current Constraints

- The architecture is designed as a modular monolith; each module can be extracted into an independent service if scale demands it.
- Background check and e-signature integrations are pluggable; the platform supports adapter patterns for multiple providers.
- Real-time tracking of maintenance staff location is outside the current scope; future upgrade.
