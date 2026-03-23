# Data Flow Diagram - Library Management System

```mermaid
flowchart LR
    patron[Patron Portal] --> api[Application API]
    staff[Staff Workspace] --> api
    api --> catalog[Catalog Service]
    api --> circ[Circulation Service]
    api --> holds[Hold Service]
    api --> acq[Acquisitions Service]
    api --> reports[Reporting Service]
    catalog --> db[(PostgreSQL)]
    circ --> db
    holds --> db
    acq --> db
    catalog --> idx[(Search Index)]
    circ --> bus[(Event Bus)]
    holds --> bus
    acq --> bus
    bus --> notify[Notification Service]
    bus --> reports
```

## Data Flow Notes

1. Catalog metadata feeds the search index used by the patron portal and staff workspace.
2. Circulation, hold, acquisition, and inventory events feed notifications and reporting asynchronously.
3. Loan and availability states remain authoritative in the transactional store while the search layer provides fast discovery reads.
