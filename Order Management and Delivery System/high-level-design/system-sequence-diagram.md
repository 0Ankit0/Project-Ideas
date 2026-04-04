# System Sequence Diagram

## Overview

System Sequence Diagrams (SSD) show the key interactions between actors and the Order Management and Delivery System. Diagrams 1–5 show internal service-level flows; diagrams 6–11 treat OMS as a black box to highlight actor-facing behaviour.

---

## 1. Customer: Order Placement and Payment

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

## 2. Warehouse Staff: Fulfillment — Pick, Pack, Manifest

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

## 3. Delivery Staff: Delivery Assignment and Execution

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

## 4. Customer and Delivery Staff: Failed Delivery and Rescheduling

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

## 5. Customer: Return and Refund

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

---

## 6. Warehouse Staff: Fulfill Order

```mermaid
sequenceDiagram
    actor WS as Warehouse Staff
    participant OMS as OMS

    OMS-->>WS: pushNotification(newFulfillmentTaskAssigned)

    WS->>OMS: viewPickList(taskId)
    OMS-->>WS: pickListWithBinLocations

    WS->>OMS: startTask(taskId)
    OMS-->>WS: taskInProgress

    loop For Each Item
        WS->>OMS: scanBarcode(sku, qty)
        OMS-->>WS: scanResult(match | mismatch)

        alt Mismatch
            OMS-->>WS: flagAlertAndNotifySupervisor
        end
    end

    WS->>OMS: completePicking(taskId)
    OMS-->>WS: allItemsPicked

    WS->>OMS: packOrder(taskId, dimensions, weight)
    OMS-->>WS: packingComplete

    OMS-->>WS: generatedPackingSlip(pdfUrl)

    Note over OMS: Batches order into delivery manifest by zone

    OMS-->>WS: manifestReady(manifestId, orderCount, zone)
```

---

## 7. Operations Manager: Manage Delivery Operations

```mermaid
sequenceDiagram
    actor OM as Operations Manager
    participant OMS as OMS
    actor OrigStaff as Original Delivery Staff
    actor NewStaff as New Delivery Staff

    OM->>OMS: viewFulfillmentDashboard()
    OMS-->>OM: metrics(pendingFulfillment, readyForDispatch, inDelivery, deliveredToday, slaBreaches)

    OM->>OMS: getOrdersReadyForDispatch(zoneId)
    OMS-->>OM: orderList

    OM->>OMS: reassignDelivery(assignmentId, newStaffId)
    OMS-->>OM: assignment

    OMS-->>OrigStaff: pushNotification(removedFromDeliveryRun)
    OMS-->>NewStaff: pushNotification(newDeliveryAssigned)

    OM->>OMS: getDeliveryPerformanceReport(from, to)
    OMS-->>OM: report(onTimeRate, avgTime, failureRate, staffRanking)

    OM->>OMS: createDeliveryZone(zoneData)
    OMS-->>OM: zone
```

---

## 8. Admin: Configure Platform and View Audit Logs

```mermaid
sequenceDiagram
    actor Admin
    participant OMS as OMS
    actor Staff as New Staff Member

    Admin->>OMS: getConfig()
    OMS-->>Admin: currentConfig(allKeysAndValues)

    Admin->>OMS: updateConfig(key, value)
    Note over OMS: Versions config entry, records change in AuditLog
    OMS-->>Admin: updatedConfig

    Admin->>OMS: getConfigHistory(key)
    OMS-->>Admin: versionHistory

    Admin->>OMS: getAuditLogs(filters)
    OMS-->>Admin: pagedAuditLogs

    Admin->>OMS: exportReport(type, from, to, format)
    OMS-->>Admin: reportDownloadUrl

    Admin->>OMS: manageStaff(createStaffData)
    OMS-->>Admin: staffAccount

    OMS-->>Staff: welcomeNotification(tempPassword)
```

---

## 9. Finance: Payment Reconciliation

```mermaid
sequenceDiagram
    actor Finance as Finance Team Member
    participant OMS as OMS
    participant PG as Payment Gateway
    actor Customer

    Note over OMS: Scheduled trigger: generateReconciliationReport(yesterday)
    OMS->>PG: getSettlementReport(date)
    PG-->>OMS: gatewaySettlement

    Note over OMS: Compares captured payments vs gateway settlement
    Note over OMS: Flags discrepancies exceeding tolerance threshold

    Finance->>OMS: getReconciliationReport(date)
    OMS-->>Finance: report(captures, refunds, settlement, discrepancies)

    Finance->>OMS: reviewDiscrepancy(discrepancyId)
    OMS-->>Finance: discrepancyDetails

    Finance->>OMS: resolveDiscrepancy(discrepancyId, resolution)
    OMS-->>Finance: resolved

    Finance->>OMS: processManualRefund(orderId, amount, reason)
    OMS->>PG: initiateRefund(gatewayRef, amount)
    PG-->>OMS: refundId

    OMS-->>Finance: refundRecord
    OMS-->>Customer: notification(refundInitiated, amount, timeline)
```

---

## 10. System: Inventory Reservation Expiry

```mermaid
sequenceDiagram
    participant Timer as EventBridge Scheduler
    participant OMS as OMS
    actor Customer

    Timer->>OMS: trigger reservationExpiryCheck()

    OMS->>OMS: findExpiredReservations()
    OMS-->>OMS: expiredList

    loop For Each Expired Reservation
        OMS->>OMS: releaseInventory(reservationId)
        Note over OMS: Stock returned to available pool

        OMS->>OMS: updateCartItem(itemId, availabilityStatus=EXPIRED)

        OMS-->>Customer: notification(cartItemExpired, productName)
    end

    OMS->>OMS: cleanupExpiredIdempotencyKeys()
```

---

## 11. Customer: Failed Delivery and Reschedule

```mermaid
sequenceDiagram
    actor DS as Delivery Staff
    participant OMS as OMS
    actor Customer

    DS->>OMS: recordFailedDelivery(assignmentId, reason, notes)
    OMS-->>DS: failureRecorded

    OMS-->>Customer: notification(deliveryFailed, reason, attemptNumber, rescheduleOptions)

    Customer->>OMS: viewOrderStatus(orderId)
    OMS-->>Customer: orderDetails(status=FAILED_ATTEMPT_N)

    Customer->>OMS: requestReschedule(orderId, preferredDate)

    alt Attempt count < 3
        OMS-->>Customer: rescheduled(newDeliveryDate)
    else Attempt count >= 3
        Note over OMS: Transitions order to ReturnedToWarehouse
        OMS-->>Customer: notification(orderReturnedToWarehouse, refundInfo)
    end
```
