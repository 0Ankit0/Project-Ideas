# ERD and Database Schema - Restaurant Management System

```mermaid
erDiagram
    BRANCH ||--o{ TABLE : contains
    BRANCH ||--o{ STAFF_USER : staffs
    BRANCH ||--o{ SHIFT : plans
    BRANCH ||--o{ MENU_ITEM : sells
    BRANCH ||--o{ INGREDIENT : stocks
    BRANCH ||--o{ ORDER : serves
    BRANCH ||--o{ PURCHASE_ORDER : creates
    BRANCH ||--o{ CASH_DRAWER_SESSION : opens
    TABLE ||--o{ ORDER : hosts
    ORDER ||--o{ ORDER_ITEM : contains
    ORDER_ITEM ||--o{ KITCHEN_TICKET : creates
    MENU_ITEM ||--o{ ORDER_ITEM : references
    MENU_ITEM ||--o{ RECIPE : defines
    INGREDIENT ||--o{ STOCK_LEDGER_ENTRY : records
    BILL ||--o{ SETTLEMENT : receives
    ORDER ||--|| BILL : bills
```

## Table Notes

| Table | Notes |
|-------|-------|
| branches | Branch identity, tax context, and operational scope |
| tables | Physical seating resources and state |
| reservations | Reservation and guest arrival records |
| waitlist_entries | Walk-in queue and promotion state |
| orders | Top-level order records for dine-in, takeaway, or delivery |
| order_items | Line items with modifiers, notes, and course timing |
| kitchen_tickets | Station-level preparation work units |
| menu_items | Sellable menu definitions |
| recipes | BOM/ingredient usage mapping |
| ingredients | Stock masters and thresholds |
| stock_ledger_entries | Inventory event history |
| bills | Financial closure records for orders |
| settlements | Payment and split-bill outcomes |
| cash_drawer_sessions | Cashier open/close and balancing sessions |
| accounting_exports | Reconciliation handoff artifacts |

## Extended Tables for Implementation Readiness

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| payment_intents | provider-facing payment lifecycle | id, check_id, provider_ref, status, idempotency_key, amount |
| policy_decisions | approval outcomes for protected operations | id, scope, outcome, approver_id, reason_code, decided_at |
| cancellation_requests | lifecycle-aware cancellation/reversal requests | id, scope, target_id, reason_code, status, decision_id |
| load_tier_snapshots | branch load state and trigger metrics | id, branch_id, tier, queue_lag_score, evaluated_at |

## ERD Extension (Mermaid)

```mermaid
erDiagram
    BILL ||--o{ PAYMENT_INTENT : has
    CANCELLATION_REQUEST }o--|| POLICY_DECISION : resolved_by
    BRANCH ||--o{ LOAD_TIER_SNAPSHOT : records
    CANCELLATION_REQUEST }o--|| ORDER : targets
```
