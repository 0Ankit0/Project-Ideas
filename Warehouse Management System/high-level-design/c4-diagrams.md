# C4 Diagrams

## C1 Context
```mermaid
flowchart LR
    Operators[Warehouse Operators] --> WMS[Warehouse Management System]
    WMS <--> OMS[Order Management]
    WMS <--> ERP[ERP]
    WMS <--> TMS[Transport Mgmt]
    WMS --> BI[Analytics]
```

## C2 Containers
```mermaid
flowchart TB
    UI[Warehouse UI/Scanner Clients]
    API[WMS API]
    Core[Core WMS Services]
    Worker[Async Worker]
    DB[(WMS DB)]
    MQ[(Event Bus)]

    UI --> API --> Core
    Core --> DB
    Core --> MQ
    Worker --> DB
    Worker --> MQ
```
