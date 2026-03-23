# Architecture Diagram - Library Management System

```mermaid
flowchart TB
    subgraph channels[Access Channels]
        portal[Patron Portal]
        staff[Staff Workspace]
    end

    subgraph platform[Core Platform]
        gateway[API Gateway]
        identity[Identity and Access]
        catalog[Catalog Service]
        circulation[Circulation Service]
        holds[Hold and Queue Service]
        policy[Policy Engine]
        acquisitions[Acquisitions and Inventory Service]
        digital[Digital Lending Service]
        notification[Notification Service]
        reporting[Reporting and Search Projection]
    end

    subgraph data[Data Layer]
        pg[(PostgreSQL)]
        search[(Search Index)]
        bus[(Message Bus)]
        object[(Object Storage)]
    end

    portal --> gateway
    staff --> gateway
    gateway --> identity
    gateway --> catalog
    gateway --> circulation
    gateway --> holds
    gateway --> acquisitions
    gateway --> digital
    circulation --> policy
    holds --> policy
    catalog --> pg
    circulation --> pg
    acquisitions --> pg
    digital --> pg
    catalog --> search
    circulation --> bus
    holds --> bus
    acquisitions --> bus
    digital --> bus
    bus --> notification
    bus --> reporting
    acquisitions --> object
```

## Responsibilities

| Component | Responsibility |
|-----------|----------------|
| Catalog Service | Bibliographic records, subjects, copies/items, metadata quality |
| Circulation Service | Issue, return, renew, due dates, status changes |
| Hold and Queue Service | Reservations, pickup windows, waitlists, branch fulfillment |
| Policy Engine | Borrowing rules, holidays, fines, patron eligibility, blocks |
| Acquisitions and Inventory Service | Vendors, orders, receiving, transfers, audits, repairs |
| Digital Lending Service | Licensed digital access and entitlement tracking |
| Reporting and Search Projection | Discovery index, dashboards, trend reporting |
