# C4 Diagrams

## C1 - System Context
```mermaid
flowchart LR
    Operators[Warehouse Operators] --> WMS[WMS]
    Supervisors[Supervisors] --> WMS
    WMS <--> OMS[Order Management]
    WMS <--> ERP[ERP]
    WMS <--> Carrier[Carrier/TMS]
    WMS --> BI[Analytics Platform]
```

## C2 - Container View
```mermaid
flowchart TB
    UI[Scanner/Web Clients]
    BFF[API Gateway / BFF]
    CMD[Command Services]
    WRK[Async Workers]
    DB[(OLTP DB)]
    BUS[(Event Bus)]
    RM[Read Models]

    UI --> BFF --> CMD
    CMD --> DB
    CMD --> BUS
    WRK --> DB
    WRK --> BUS
    BUS --> RM
    RM --> UI
```

## C3 - Key Components (Allocation Container)
```mermaid
flowchart LR
    AllocAPI[Allocation API] --> ReservationEngine
    ReservationEngine --> PolicyEvaluator
    ReservationEngine --> StockGateway
    ReservationEngine --> OutboxWriter
    StockGateway --> DB[(Inventory Tables)]
    OutboxWriter --> Outbox[(Outbox Table)]
```

## Notes
- C1 clarifies ownership boundaries.
- C2 clarifies data flow and async split.
- C3 identifies implementation units for allocation critical path.
