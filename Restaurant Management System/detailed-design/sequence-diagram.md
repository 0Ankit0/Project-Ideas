# Sequence Diagram - Restaurant Management System

```mermaid
sequenceDiagram
    participant Host as Host
    participant POS as POS UI
    participant Seating as Seating Service
    participant Waiter as Waiter
    participant Order as Order Service
    participant Kitchen as Kitchen Service
    participant Cashier as Cashier
    participant Billing as Billing Service

    Host->>POS: Seat party
    POS->>Seating: assign table
    Waiter->>POS: capture order
    POS->>Order: submit order
    Order->>Kitchen: create kitchen tickets
    Kitchen-->>POS: ready updates
    Cashier->>POS: close bill
    POS->>Billing: settle bill
```

## Reconciliation Sequence

```mermaid
sequenceDiagram
    participant Cashier as Cashier
    participant Backoffice as Backoffice UI
    participant Settlement as Settlement Service
    participant Export as Accounting Export Service
    participant Manager as Branch Manager

    Cashier->>Backoffice: close drawer session
    Backoffice->>Settlement: record session totals
    Settlement->>Export: prepare export batch
    Manager->>Backoffice: approve day close
```

## Detailed Order Lifecycle with Kitchen Orchestration and Settlement

```mermaid
sequenceDiagram
    participant Waiter as Waiter Tablet
    participant POS as POS Backend
    participant Menu as Menu/Pricing Service
    participant Orchestrator as Kitchen Orchestrator
    participant KDS as Station KDS
    participant Table as Table Service
    participant Bill as Billing Service
    participant Pay as Payment Adapter

    Waiter->>POS: Create draft order (table, seats, items, notes)
    POS->>Menu: Validate pricing/modifiers/availability
    Menu-->>POS: Validation result + effective prices
    POS-->>Waiter: Draft accepted (version n)
    Waiter->>POS: Submit order version n
    POS->>Orchestrator: Fan-out station tasks + course dependencies
    Orchestrator->>KDS: Push station tickets with SLA clocks
    KDS-->>Orchestrator: accepted/in_prep/ready updates
    Orchestrator-->>POS: Consolidated readiness by course
    POS-->>Waiter: Fire/pickup guidance
    Waiter->>Bill: Request settlement
    Bill->>Pay: Create/capture payment intents (multi-tender)
    Pay-->>Bill: Authorized/failed per intent
    Bill->>Table: Close check and release table pipeline
    Table-->>POS: Table moves to cleaning/ready states
```

## Peak-Load Control Loop

```mermaid
sequenceDiagram
    participant Metrics as Runtime Metrics
    participant Control as Peak Control Service
    participant Slot as Reservation/Waitlist
    participant Menu as Menu Availability
    participant KDS as Kitchen Router
    participant POS as POS Policy Engine

    Metrics->>Control: Queue depth + SLA risk + payment wait + table occupancy
    Control->>Control: Compute load tier (normal/watch/surge/critical)
    alt Surge or critical
        Control->>Slot: Apply slot throttling and ETA inflation
        Control->>Menu: Enable surge menu profile
        Control->>KDS: Cap concurrent long-prep items
        Control->>POS: Enforce surge approval rules
    else Back to normal
        Control->>Slot: Remove throttles
        Control->>Menu: Restore full menu
        Control->>KDS: Reset station caps
        Control->>POS: Disable surge rules
    end
```

## Implementation Contracts for Sequences

### A) Order Submit Command (logical contract)
```json
{
  "branch_id": "br_001",
  "table_id": "tbl_12",
  "order_id": "ord_456",
  "expected_version": 7,
  "items": [
    {
      "line_id": "ln_1",
      "menu_item_id": "mi_pasta",
      "qty": 2,
      "seat_no": 3,
      "modifier_ids": ["mod_no_cheese"],
      "course": "main",
      "notes": "allergy: peanuts"
    }
  ],
  "submitted_by": "usr_waiter_14",
  "submitted_at": "2026-03-28T18:22:54Z"
}
```

### B) Kitchen Ticket Event (logical contract)
```json
{
  "event_type": "kitchen.ticket.created",
  "event_id": "evt_998",
  "ticket_id": "kt_73",
  "order_id": "ord_456",
  "station_id": "grill",
  "priority_band": "standard",
  "promised_ready_at": "2026-03-28T18:35:00Z",
  "course_dependency": ["starter_complete"],
  "correlation_id": "corr_abc"
}
```

### C) Cancellation/Reversal Decision Object
```json
{
  "decision_id": "dec_101",
  "scope": "payment_reversal",
  "target_id": "pay_332",
  "reason_code": "item_quality_issue",
  "approved": true,
  "approved_by": "usr_manager_2",
  "requires_dual_approval": false,
  "compensations": ["refund_intent", "audit_entry"]
}
```

## Persistence and Idempotency Notes
- Sequence commands must use optimistic concurrency (`expected_version`) for order and table aggregates.
- Payment capture/void/refund endpoints must be idempotent on `(branch_id, check_id, idempotency_key)`.
- Ticket updates are append-only events; read models can be rebuilt from event stream.
- Peak-load tier transition writes must be deduplicated by `(branch_id, tier, 5-minute window)`.

## Stateful Lifecycle Diagrams (Mermaid)

### Order Line Lifecycle
```mermaid
stateDiagram-v2
    [*] --> draft
    draft --> submitted: submit(valid)
    draft --> draft: save_draft
    submitted --> queued: route_to_station
    queued --> in_preparation: station_accept
    in_preparation --> ready: prep_complete
    ready --> served: waiter_serve
    submitted --> voided: pre_fire_cancel
    queued --> voided: approved_cancel
    in_preparation --> voided: approved_void_with_reason
    voided --> [*]
    served --> [*]
```

### Table Lifecycle
```mermaid
stateDiagram-v2
    [*] --> available
    available --> reserved: hold_slot
    reserved --> occupied: seat_party
    reserved --> available: no_show_or_cancel
    occupied --> cleaning: check_closed
    cleaning --> available: housekeeping_done
    occupied --> blocked: incident_or_unpaid_exception
    blocked --> available: manager_clear
```

### Check and Payment Lifecycle
```mermaid
stateDiagram-v2
    [*] --> open
    open --> partially_paid: partial_capture
    partially_paid --> partially_paid: additional_partial_capture
    open --> paid: full_capture
    partially_paid --> paid: settle_balance
    paid --> refund_pending: refund_requested
    refund_pending --> refunded: refund_success
    refund_pending --> paid: refund_rejected
    open --> voided: pre_settlement_void
    voided --> [*]
    refunded --> [*]
    paid --> [*]
```
