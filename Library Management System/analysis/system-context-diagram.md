# System Context Diagram - Library Management System

```mermaid
flowchart LR
    patrons[Patrons]
    staff[Library Staff]
    vendors[Book and Media Vendors]
    payment[Payment Provider]
    notify[Email / SMS Services]
    digital[Digital Content Provider]
    devices[Barcode / RFID Devices]

    subgraph lms[Library Management System]
        portal[Patron Portal]
        workspace[Staff Workspace]
        api[Application API]
        search[Catalog Search]
    end

    patrons --> portal
    staff --> workspace
    portal --> api
    workspace --> api
    api --> vendors
    api --> payment
    api --> notify
    api --> digital
    api --> devices
    api --> search
```

## Context Notes

- Patrons mainly interact through discovery, holds, and account-management workflows.
- Staff use operational tools for circulation, cataloging, acquisitions, inventory, and reporting.
- The platform may integrate with payments, notifications, RFID/barcode tooling, and digital-content vendors.
