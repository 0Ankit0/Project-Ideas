# Component Diagram - Library Management System

```mermaid
flowchart LR
    ui[Patron Portal / Staff Workspace] --> api[API Layer]
    api --> auth[Access Control Component]
    api --> catalog[Catalog Component]
    api --> circulation[Circulation Component]
    api --> holds[Hold Queue Component]
    api --> fines[Fines and Payments Component]
    api --> acquisitions[Acquisitions and Inventory Component]
    api --> digital[Digital Lending Component]
    api --> reporting[Reporting Component]
    circulation --> policy[Policy Engine Component]
    holds --> policy
    fines --> policy
```

## Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| Access Control | Authentication, branch scoping, role evaluation |
| Catalog | Title metadata, search feeds, duplicate handling |
| Circulation | Loans, returns, renewals, copy states |
| Hold Queue | Reservations, pickup windows, queue transitions |
| Fines and Payments | Charges, waivers, payments, restrictions |
| Acquisitions and Inventory | Vendors, purchase orders, receiving, transfers, audits |
| Digital Lending | Provider integrations, digital loans, entitlement limits |
| Reporting | Dashboards, exports, operational metrics |
