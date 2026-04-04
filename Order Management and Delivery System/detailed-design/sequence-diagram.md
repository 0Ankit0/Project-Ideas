# Sequence Diagram

## Overview

Detailed inter-service sequence diagrams showing internal object interactions for the most complex flows in the system.

## 1. Checkout with Inventory Reservation and Payment

```mermaid
sequenceDiagram
    participant Client
    participant APIGW as API Gateway
    participant Auth as Cognito Authorizer
    participant Cache as ElastiCache
    participant OrderSvc as Order Service
    participant InvSvc as Inventory Service
    participant DB as PostgreSQL
    participant PaySvc as Payment Service
    participant PG as Payment Gateway
    participant EB as EventBridge

    Client->>APIGW: POST /orders/checkout (idempotency_key)
    APIGW->>Auth: Validate JWT
    Auth-->>APIGW: Token valid (customer_id, roles)
    APIGW->>OrderSvc: ProcessCheckout(customer_id, cart_id, address_id, payment_method)

    OrderSvc->>Cache: GET idempotency:{key}
    alt Key exists
        Cache-->>OrderSvc: Cached response
        OrderSvc-->>Client: Return cached response (200)
    else Key not found
        OrderSvc->>DB: BEGIN TRANSACTION
        OrderSvc->>DB: SELECT cart_items WHERE customer_id
        DB-->>OrderSvc: Cart items with variant details

        loop For each cart item
            OrderSvc->>InvSvc: ReserveStock(variant_id, qty, ttl=15min)
            InvSvc->>DB: UPDATE inventory SET reserved = reserved + qty WHERE available >= qty
            alt Insufficient stock
                InvSvc-->>OrderSvc: ReservationFailed(variant_id)
                OrderSvc->>DB: ROLLBACK
                OrderSvc-->>Client: 409 Conflict (items unavailable)
            else Stock available
                InvSvc-->>OrderSvc: ReservationConfirmed(reservation_id)
            end
        end

        OrderSvc->>OrderSvc: CalculateTotal(items, tax, shipping, discount)
        OrderSvc->>DB: INSERT order (status=Draft)
        OrderSvc->>PaySvc: CapturePayment(order_id, amount, method, idemp_key)
        PaySvc->>PG: POST /charges (amount, token, idemp_key)

        alt Payment declined
            PG-->>PaySvc: Declined(reason)
            PaySvc-->>OrderSvc: PaymentFailed(reason)
            OrderSvc->>InvSvc: ReleaseReservations(order_id)
            OrderSvc->>DB: ROLLBACK
            OrderSvc-->>Client: 402 Payment Required
        else Payment captured
            PG-->>PaySvc: Captured(gateway_ref)
            PaySvc->>DB: INSERT payment_transaction
            PaySvc-->>OrderSvc: PaymentCaptured(payment_id)
            OrderSvc->>DB: UPDATE order SET status=Confirmed, payment_id
            OrderSvc->>DB: INSERT order_milestone (Confirmed)
            OrderSvc->>DB: COMMIT
            OrderSvc->>EB: Publish oms.order.confirmed.v1
            OrderSvc->>Cache: SET idempotency:{key} = response (TTL 24h)
            OrderSvc-->>Client: 201 Created (order_id, order_number)
        end
    end
```

## 2. Three-Phase Delivery with POD Upload

```mermaid
sequenceDiagram
    participant Staff as Delivery Staff App
    participant APIGW as API Gateway
    participant DelSvc as Delivery Service
    participant DB as PostgreSQL
    participant DDB as DynamoDB
    participant S3 as Amazon S3
    participant EB as EventBridge

    Note over Staff,EB: Phase 1 — Pickup
    Staff->>APIGW: PATCH /deliveries/{id}/status (picked_up)
    APIGW->>DelSvc: UpdateStatus(assignment_id, picked_up)
    DelSvc->>DB: SELECT assignment WHERE id AND status=assigned
    DelSvc->>DB: UPDATE assignment SET status=picked_up
    DelSvc->>DB: UPDATE order SET status=PickedUp
    DelSvc->>DDB: PUT milestone (order_id, PickedUp, timestamp)
    DelSvc->>EB: Publish oms.order.picked_up.v1
    DelSvc-->>Staff: 200 OK

    Note over Staff,EB: Phase 2 — Out for Delivery
    Staff->>APIGW: PATCH /deliveries/{id}/status (out_for_delivery)
    APIGW->>DelSvc: UpdateStatus(assignment_id, out_for_delivery)
    DelSvc->>DB: UPDATE assignment SET status=out_for_delivery
    DelSvc->>DB: UPDATE order SET status=OutForDelivery
    DelSvc->>DDB: PUT milestone (order_id, OutForDelivery, timestamp)
    DelSvc->>EB: Publish oms.order.out_for_delivery.v1
    DelSvc-->>Staff: 200 OK

    Note over Staff,EB: Phase 3 — POD and Completion
    Staff->>APIGW: POST /deliveries/{id}/pod (signature, photo, notes)
    APIGW->>DelSvc: SubmitPOD(assignment_id, artifacts)
    DelSvc->>S3: PutObject(signature, SSE-AES256)
    S3-->>DelSvc: ETag, s3_key
    DelSvc->>S3: PutObject(photo, SSE-AES256)
    S3-->>DelSvc: ETag, s3_key
    DelSvc->>DB: INSERT proof_of_delivery (order_id, s3_keys, notes)
    DelSvc->>DB: UPDATE assignment SET status=delivered
    DelSvc->>DB: UPDATE order SET status=Delivered, delivered_at=NOW()
    DelSvc->>DDB: PUT milestone (order_id, Delivered, timestamp)
    DelSvc->>EB: Publish oms.order.delivered.v1
    DelSvc-->>Staff: 200 OK (pod_id)
```

## 3. Return Inspection to Refund

```mermaid
sequenceDiagram
    participant WStaff as Warehouse Staff
    participant APIGW as API Gateway
    participant RetSvc as Return Service
    participant DB as PostgreSQL
    participant InvSvc as Inventory Service
    participant PaySvc as Payment Service
    participant PG as Payment Gateway
    participant EB as EventBridge

    WStaff->>APIGW: POST /returns/{id}/inspect (result=accepted, notes)
    APIGW->>RetSvc: RecordInspection(return_id, result, notes)
    RetSvc->>DB: SELECT return_request JOIN order WHERE return_id
    RetSvc->>RetSvc: CalculateRefundAmount(line_items)
    RetSvc->>DB: UPDATE return_request SET status=accepted, refund_amount
    RetSvc->>EB: Publish oms.return.inspected.v1 (result=accepted)

    EB->>InvSvc: Consume inspected (accepted)
    InvSvc->>DB: UPDATE inventory SET qty_on_hand += returned_qty

    EB->>PaySvc: Consume inspected (accepted, refund_amount)
    PaySvc->>DB: SELECT payment_transaction WHERE order_id
    PaySvc->>PG: POST /refunds (payment_ref, refund_amount)

    alt Refund successful
        PG-->>PaySvc: RefundConfirmed(refund_ref)
        PaySvc->>DB: INSERT refund_record (status=completed)
        PaySvc->>EB: Publish oms.payment.refund_completed.v1
    else Refund failed
        PG-->>PaySvc: RefundFailed(reason)
        PaySvc->>DB: INSERT refund_record (status=failed)
        PaySvc->>PaySvc: ScheduleRetry(3 attempts, backoff)
    end

    RetSvc-->>WStaff: 200 OK (inspection recorded)
```
