# Component Diagram - Restaurant Management System

```mermaid
flowchart LR
    ui[Guest Touchpoints / POS / Backoffice / KDS] --> api[API Layer]
    api --> auth[Access Control Component]
    api --> seating[Reservation and Seating Component]
    api --> menu[Menu and Pricing Component]
    api --> order[Order and Service Component]
    api --> kitchen[Kitchen Routing Component]
    api --> inventory[Inventory and Recipe Component]
    api --> procurement[Procurement Component]
    api --> billing[Billing and Settlement Component]
    api --> workforce[Shift and Attendance Component]
    api --> reporting[Reporting Component]
    order --> kitchen
    order --> inventory
    billing --> reporting
```

## Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| Access Control | Authentication, branch scoping, approval gates |
| Reservation and Seating | Reservations, walk-ins, waitlist, table assignment |
| Menu and Pricing | Menus, modifiers, taxes, discounts, availability |
| Order and Service | Order capture, table checks, service events |
| Kitchen Routing | Station routing, prep states, readiness signals |
| Inventory and Recipe | Ingredients, recipe usage, stock movements |
| Procurement | Vendors, POs, receipts, discrepancies |
| Billing and Settlement | Bills, payments, refunds, drawer sessions |
| Shift and Attendance | Scheduling, attendance, staffing visibility |
| Reporting | Sales, delays, variance, operational dashboards |

## Component Interaction Diagram for Operational Flows

```mermaid
flowchart TB
    POS[Host/Waiter/Cashier Apps] --> OrderC[Order Component]
    POS --> SeatC[Seating Component]
    POS --> BillC[Billing Component]
    POS --> PolicyC[Policy/Approval Component]

    OrderC --> KitchenC[Kitchen Component]
    OrderC --> InventoryC[Inventory Component]
    SeatC --> LoadC[Load Control Component]
    KitchenC --> LoadC
    BillC --> LoadC

    OrderC --> EventC[(Event Stream)]
    KitchenC --> EventC
    BillC --> EventC
    PolicyC --> EventC
    LoadC --> EventC

    EventC --> AuditC[Audit Component]
    EventC --> NotifyC[Notification Component]
    EventC --> ReportC[Reporting Component]
```

## Component Contracts (Minimum)

| Producer -> Consumer | Contract Requirement |
|----------------------|----------------------|
| Order -> Kitchen | station-ready ticket bundle with dependency metadata |
| Kitchen -> POS projection | line-level state transition with station and ETA context |
| Billing -> Reconciliation | immutable settlement rows with tender breakdown |
| Policy -> Domain services | decision object with scope, threshold, and approval lineage |
| Load Control -> Seating/Menu/Kitchen | tiered throttle directives with effective window |
