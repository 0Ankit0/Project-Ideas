# System Context Diagram - Restaurant Management System

```mermaid
flowchart LR
    guests[Guests / Customers]
    staff[Hosts, Waiters, Chefs, Cashiers, Managers]
    payment[Payment Provider]
    accounting[External Accounting System]
    vendors[Suppliers / Vendors]
    delivery[Delivery Aggregator / Channel]
    devices[POS Devices, KDS, Printers]

    subgraph rms[Restaurant Management System]
        guestTouchpoints[Guest Touchpoints]
        staffApps[Staff POS and Backoffice]
        api[Application API]
        reporting[Reporting and Analytics]
    end

    guests --> guestTouchpoints
    staff --> staffApps
    guestTouchpoints --> api
    staffApps --> api
    api --> payment
    api --> accounting
    api --> vendors
    api --> delivery
    api --> devices
    api --> reporting
```

## Context Notes

- Guests interact through lightweight reservation, waitlist, and order-status touchpoints rather than a full guest application stack.
- Staff use branch operational tools for front-of-house, kitchen, inventory, cashiering, and management workflows.
- The system integrates with payments, accounting exports, supplier processes, delivery channels, and restaurant devices.

## Context-Level Non-Functional Boundaries

| External Actor/System | Data Exchanged | Critical Constraint |
|-----------------------|----------------|---------------------|
| Payment Provider | payment intents, captures, voids, refunds | idempotent retries + signed callbacks |
| Accounting System | settlement exports, tax summaries, reconciliation batches | immutable export lineage |
| Vendors/Suppliers | purchase orders, receipts, discrepancy records | branch-level authorization and traceability |
| Delivery Channels | order ingestion/status sync | source-of-truth mapping and deduplication |
| Devices (POS/KDS/Printers) | ticket updates, print jobs, health telemetry | degraded-mode fallback for branch outages |

## Context Risk Flow (Mermaid)

```mermaid
flowchart TD
    A[External integration call] --> B{Trusted + valid contract?}
    B -- No --> C[Reject + security/audit event]
    B -- Yes --> D[Process in domain service]
    D --> E{Side effects generated?}
    E -- Yes --> F[Emit domain + audit events]
    E -- No --> G[Return deterministic response]
    F --> H[Notify dependent contexts]
```
