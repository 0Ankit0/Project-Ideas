# System Sequence Diagram

## Overview

This document presents system-level sequence diagrams showing the key interactions between actors, the Order Management and Delivery System, and external services.

## 1. Order Placement and Payment

```mermaid
sequenceDiagram
    actor C as Customer
    participant API as API Gateway
    participant OS as Order Service
    participant IS as Inventory Service
    participant PS as Payment Service
    participant PG as Payment Gateway
    participant EB as EventBridge
    participant NS as Notification Service

    C->>API: POST /orders/checkout (cart_id, address_id, payment_method, idempotency_key)
    API->>API: Validate JWT, rate limit
    API->>OS: Forward checkout request
    OS->>IS: ReserveInventory(items, ttl=15min)
    IS-->>OS: ReservationConfirmed(reservation_id)
    OS->>OS: Calculate total (items + tax + shipping - discount)
    OS->>PS: CapturePayment(amount, method, idempotency_key)
    PS->>PG: POST /v1/charges (amount, token)
    PG-->>PS: ChargeResponse(gateway_ref, status=captured)
    PS-->>OS: PaymentCaptured(payment_id, gateway_ref)
    OS->>OS: CreateOrder(status=Confirmed)
    OS->>EB: Publish oms.order.confirmed.v1
    OS-->>API: 201 Created (order_id, order_number)
    API-->>C: Order confirmation response
    EB->>NS: Consume confirmed event
    NS->>C: Email + SMS: Order confirmed
```

## 2. Fulfillment — Pick, Pack, Manifest

```mermaid
sequenceDiagram
    actor WS as Warehouse Staff
    participant API as API Gateway
    participant FS as Fulfillment Service
    participant DB as PostgreSQL
    participant EB as EventBridge
    participant NS as Notification Service
    actor C as Customer

    EB->>FS: Consume oms.order.confirmed.v1
    FS->>DB: CreateFulfillmentTask(order_id, warehouse_id)
    WS->>API: GET /fulfillment/tasks (warehouse_id)
    API->>FS: Get assigned tasks
    FS-->>API: TaskList (sorted by SLA deadline)
    API-->>WS: Task list response
    WS->>API: POST /fulfillment/tasks/{task_id}/start
    FS->>DB: UpdateTask(status=InProgress)
    WS->>API: POST /fulfillment/tasks/{task_id}/scan (sku, quantity)
    FS->>FS: ValidateScan(expected vs actual)
    FS-->>API: ScanResult(match=true)
    WS->>API: POST /fulfillment/tasks/{task_id}/pack (dimensions, weight)
    FS->>DB: UpdateTask(status=Packed)
    FS->>DB: UpdateOrder(status=ReadyForDispatch)
    FS->>EB: Publish oms.order.ready_for_dispatch.v1
    EB->>NS: Consume ready_for_dispatch
    NS->>C: Email: Order dispatched
```

## 3. Delivery Assignment and Execution

```mermaid
sequenceDiagram
    actor DS as Delivery Staff
    participant API as API Gateway
    participant DAS as Delivery Assignment Service
    participant DSvc as Delivery Service
    participant S3 as Amazon S3
    participant EB as EventBridge
    participant NS as Notification Service
    actor C as Customer

    EB->>DAS: Consume oms.order.ready_for_dispatch.v1
    DAS->>DAS: FindAvailableStaff(zone, capacity)
    DAS->>DAS: CreateAssignment(order_id, staff_id)
    DAS->>NS: Push notification to delivery staff
    DS->>API: GET /deliveries/assignments
    API->>DSvc: Get my assignments
    DSvc-->>API: AssignmentList
    API-->>DS: Assignment details
    DS->>API: PATCH /deliveries/{assignment_id}/status (picked_up)
    DSvc->>EB: Publish oms.order.picked_up.v1
    DS->>API: PATCH /deliveries/{assignment_id}/status (out_for_delivery)
    DSvc->>EB: Publish oms.order.out_for_delivery.v1
    EB->>NS: Consume out_for_delivery
    NS->>C: Push: Out for delivery
    DS->>API: POST /deliveries/{assignment_id}/pod (signature, photo)
    DSvc->>S3: Upload POD artifacts (AES-256)
    S3-->>DSvc: Upload confirmed (s3_keys)
    DSvc->>DSvc: RecordPOD(order_id, s3_keys)
    DSvc->>DSvc: UpdateOrder(status=Delivered)
    DSvc->>EB: Publish oms.order.delivered.v1
    EB->>NS: Consume delivered
    NS->>C: Email: Delivered with POD link
```

## 4. Failed Delivery and Rescheduling

```mermaid
sequenceDiagram
    actor DS as Delivery Staff
    participant API as API Gateway
    participant DSvc as Delivery Service
    participant RS as Rescheduling Service
    participant IS as Inventory Service
    participant EB as EventBridge
    participant NS as Notification Service
    actor C as Customer

    DS->>API: POST /deliveries/{assignment_id}/fail (reason_code)
    DSvc->>DSvc: IncrementAttemptCount
    DSvc->>EB: Publish oms.order.delivery_failed.v1

    alt Attempt count < 3
        EB->>RS: Consume delivery_failed
        RS->>RS: CalculateNextWindow
        RS->>EB: Publish oms.order.delivery_rescheduled.v1
        EB->>NS: Consume rescheduled
        NS->>C: SMS: Delivery rescheduled for [date]
    else Attempt count >= 3
        EB->>RS: Consume delivery_failed
        RS->>DSvc: TransitionOrder(ReturnedToWarehouse)
        DSvc->>EB: Publish oms.order.returned_to_warehouse.v1
        EB->>IS: Consume returned_to_warehouse
        IS->>IS: RestoreStock(items)
        EB->>NS: Consume returned_to_warehouse
        NS->>C: Email: Order returned, contact support
    end
```

## 5. Return and Refund

```mermaid
sequenceDiagram
    actor C as Customer
    participant API as API Gateway
    participant RS as Return Service
    participant DAS as Delivery Assignment Service
    actor DS as Delivery Staff
    participant WS as Warehouse Service
    participant PS as Payment Service
    participant PG as Payment Gateway
    participant EB as EventBridge
    participant NS as Notification Service

    C->>API: POST /returns (order_id, reason, evidence_photos)
    API->>RS: CreateReturnRequest
    RS->>RS: ValidateEligibility(within_window, category_allowed)
    RS->>EB: Publish oms.return.requested.v1
    RS-->>API: 201 Created (return_id)
    API-->>C: Return request confirmed
    EB->>DAS: Consume return.requested
    DAS->>DAS: AssignReturnPickup(zone, staff)
    DAS->>NS: Push notification to pickup staff
    DS->>API: PATCH /returns/{return_id}/pickup (collected)
    RS->>EB: Publish oms.return.picked_up.v1
    Note over WS: Item arrives at warehouse
    WS->>API: POST /returns/{return_id}/inspect (result, notes)
    RS->>EB: Publish oms.return.inspected.v1

    alt Result = Accepted
        EB->>PS: Consume inspected (accepted)
        PS->>PG: POST /v1/refunds (payment_id, amount)
        PG-->>PS: RefundConfirmed
        PS->>EB: Publish oms.payment.refund_completed.v1
        EB->>NS: Consume refund_completed
        NS->>C: Email: Refund processed
    else Result = Rejected
        EB->>NS: Consume inspected (rejected)
        NS->>C: Email: Return rejected with reason
    end
```
