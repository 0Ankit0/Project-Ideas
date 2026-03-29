# C4 Code Diagram - Restaurant Management System

```mermaid
flowchart TB
    subgraph api[apps/api]
        controllers[Controllers]
        guards[Auth Guards]
        commands[Command Handlers]
        queries[Query Handlers]
    end

    subgraph domain[packages/domain]
        access[Access Module]
        seating[Seating Module]
        menu[Menu Module]
        orders[Orders Module]
        kitchen[Kitchen Module]
        inventory[Inventory Module]
        procurement[Procurement Module]
        billing[Billing Module]
        workforce[Workforce Module]
        reporting[Reporting Module]
    end

    subgraph worker[apps/worker]
        notifications[Notification Jobs]
        stockProjection[Stock Projection Jobs]
        accountingExports[Accounting Export Jobs]
        reportingProjector[Reporting Projector]
    end

    controllers --> guards
    controllers --> commands
    controllers --> queries
    commands --> access
    commands --> seating
    commands --> menu
    commands --> orders
    commands --> kitchen
    commands --> inventory
    commands --> procurement
    commands --> billing
    commands --> workforce
    queries --> seating
    queries --> orders
    queries --> inventory
    queries --> reporting
    notifications --> orders
    stockProjection --> inventory
    accountingExports --> billing
    reportingProjector --> reporting
```

## Code-Level Boundaries for Requested Flows

| Module | Interfaces to Implement | Key Tests |
|--------|--------------------------|-----------|
| orders | `submitOrder`, `mergeOrderConflicts`, `emitOrderEvents` | concurrency + idempotency |
| kitchen | `routeTickets`, `updateTicketState`, `handleRefire` | routing and SLA timing |
| billing | `splitCheck`, `captureIntent`, `reversePayment` | settlement integrity |
| seating | `quoteSlot`, `confirmSlot`, `releaseTable` | no-overbook and ETA |
| policy | `evaluateAction`, `requireApproval`, `recordDecision` | approval matrix coverage |
| load-control | `evaluateTier`, `applyTierPolicies`, `recoverTier` | tier transition correctness |

## Internal Command/Event Flow

```mermaid
flowchart TD
    C[Controller] --> G[Guard + Policy Check]
    G --> H[Command Handler]
    H --> D[Domain Aggregate]
    D --> O[Outbox Writer]
    O --> W[Worker Relay]
    W --> E[Event Bus]
    E --> P[Projectors + Notifications + Audit]
```
