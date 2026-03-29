# System Sequence Diagram - Restaurant Management System

## Table Order to Settlement Sequence

```mermaid
sequenceDiagram
    participant Guest as Guest
    participant POS as Staff POS
    participant Order as Order Service
    participant Kitchen as Kitchen Service
    participant Billing as Billing Service
    participant Payment as Payment Provider
    participant Export as Accounting Export Service

    Guest->>POS: Place dine-in order via waiter
    POS->>Order: Create and submit order
    Order->>Kitchen: Route kitchen tickets
    Kitchen-->>POS: Ready status updates
    POS->>Billing: Request bill closure
    Billing->>Payment: Capture payment
    Billing->>Export: Queue operational accounting export
```

## Procurement to Inventory Availability Sequence

```mermaid
sequenceDiagram
    participant PM as Purchase Manager
    participant Backoffice as Backoffice App
    participant Procurement as Procurement Service
    participant Inventory as Inventory Service
    participant Reporting as Reporting Service

    PM->>Backoffice: Create purchase order
    Backoffice->>Procurement: Submit PO
    PM->>Backoffice: Receive goods
    Backoffice->>Inventory: Record receipt and stock movement
    Inventory->>Reporting: Publish updated stock and variance data
```

## Reservation Slot to Seating Under Peak Load

```mermaid
sequenceDiagram
    participant Guest as Guest
    participant HostUI as Host Console
    participant Slot as Slot Service
    participant Queue as Waitlist Service
    participant Ops as Load Control Service

    Guest->>HostUI: Request table for party/time
    HostUI->>Slot: Query available slots
    Slot->>Ops: Fetch current load index
    Ops-->>Slot: Load state + throttling policy
    Slot-->>HostUI: Offer slots with ETA/confidence
    alt Slot accepted
        HostUI->>Slot: Confirm reservation
        Slot-->>Guest: Confirmation + arrival window
    else No feasible slot
        HostUI->>Queue: Add to waitlist
        Queue-->>Guest: Waitlist token + live ETA
    end
```

## Cancellation and Payment Reversal Sequence

```mermaid
sequenceDiagram
    participant Staff as Host/Waiter/Cashier
    participant Policy as Policy Service
    participant Order as Order Service
    participant Kitchen as Kitchen Service
    participant Billing as Billing Service
    participant Pay as Payment Provider
    participant Audit as Audit Service

    Staff->>Policy: Request cancellation/refund with reason
    Policy-->>Staff: Decision + required approvals
    alt Approved pre-fire cancellation
        Staff->>Order: Cancel order lines
        Order->>Kitchen: Cancel linked tickets
    else Approved post-payment reversal
        Staff->>Billing: Initiate void/refund
        Billing->>Pay: Reverse payment intent
        Pay-->>Billing: Reversal status
    end
    Billing->>Audit: Persist financial and policy trail
    Order->>Audit: Persist operational trail
```

## Cross-Flow Responsibility Boundaries

| Capability | System of Record | Decision Owner | Fallback Behavior |
|------------|------------------|----------------|-------------------|
| Slot allocation and ETA | Slot/Waitlist Service | Host + Load Control | Switch to conservative ETA and throttle bookings |
| Ticket sequencing and station routing | Kitchen Orchestrator | Expediter + Policy Engine | Freeze reroute and prioritize shortest prep items |
| Split settlement and reversal | Billing Service | Cashier + Manager policy | Enter pending reconcile queue with manual review |
| Cancellation approval | Policy Service | Role/threshold matrix | Defer to manager queue if policy ambiguity detected |
| Surge-mode toggling | Load Control Service | Automated thresholds + manager override | Auto-recover after stable window |

## Sequence-Level NFR Budgets
- Host UI slot query end-to-end budget: **<= 800 ms p95**.
- Order submit acknowledgment budget: **<= 1200 ms p95**.
- Kitchen status fan-out freshness budget: **<= 2 s** from station change.
- Payment status propagation budget: **<= 3 s** from provider callback.
- Cancellation decision budget (no escalation): **<= 1 s**.

## Cross-Flow Service Collaboration Map

```mermaid
flowchart LR
    subgraph FOH[Front of House]
        Host[Host Console]
        Waiter[Waiter POS]
        Cashier[Cashier POS]
    end

    subgraph Core[Core Domain Services]
        Slot[Slot & Waitlist Service]
        Order[Order Service]
        Orch[Kitchen Orchestrator]
        Bill[Billing Service]
        Policy[Policy & Approval Service]
        Load[Peak Load Control Service]
    end

    subgraph Ops[Operational Backbone]
        Bus[Event Bus]
        Audit[Audit Service]
        Notify[Notification Service]
        Analytics[Reporting/Analytics]
    end

    Host --> Slot
    Waiter --> Order
    Order --> Orch
    Cashier --> Bill
    Host --> Policy
    Waiter --> Policy
    Cashier --> Policy
    Slot --> Load
    Orch --> Load
    Bill --> Load
    Order --> Bus
    Orch --> Bus
    Bill --> Bus
    Policy --> Bus
    Bus --> Audit
    Bus --> Notify
    Bus --> Analytics
```

## Peak-Load Tier State Model

```mermaid
stateDiagram-v2
    [*] --> normal
    normal --> watch: threshold_warn
    watch --> surge: threshold_surge
    surge --> critical: sustained_sla_breach
    critical --> surge: partial_recovery
    surge --> watch: stable_recovery_window
    watch --> normal: sustained_normal_window
    critical --> watch: emergency_mitigation_success
```
