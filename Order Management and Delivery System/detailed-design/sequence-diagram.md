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
    participant DDB as DynamoDB
    participant PaySvc as Payment Service
    participant PG as Payment Gateway
    participant EB as EventBridge

    Client->>APIGW: POST /orders/checkout (Bearer JWT, Idempotency-Key)
    APIGW->>Auth: Validate JWT
    Auth-->>APIGW: Token valid (customer_id, roles)
    APIGW->>OrderSvc: ProcessCheckout(customer_id, cart_id, address_id, payment_method)

    OrderSvc->>Cache: GET idempotency:{key}
    alt Key exists (duplicate request)
        Cache-->>OrderSvc: Cached response
        OrderSvc-->>Client: 200 OK — cached response (order_id, order_number)
    else Key not found — first-time request
        OrderSvc->>DB: BEGIN TRANSACTION
        OrderSvc->>DB: SELECT cart_items WHERE customer_id AND cart_id
        DB-->>OrderSvc: Cart items with variant details and unit prices

        loop For each cart item
            OrderSvc->>InvSvc: ReserveStock(variant_id, qty, order_ref, ttl=15min)
            InvSvc->>DB: UPDATE inventory SET reserved = reserved + qty WHERE available >= qty
            InvSvc->>DDB: PutItem {reservationId, variantId, qty, orderId, expiresAt=TTL+15min}
            alt Insufficient stock
                InvSvc-->>OrderSvc: ReservationFailed(variant_id, available_qty)
                OrderSvc->>DB: ROLLBACK
                OrderSvc-->>Client: 409 Conflict — items unavailable (variant_id, available_qty)
            else Stock reserved
                InvSvc-->>OrderSvc: ReservationConfirmed(reservation_id, expiresAt)
            end
        end

        OrderSvc->>OrderSvc: CalculateTotal(items, tax, shipping, discount_codes)
        OrderSvc->>DB: INSERT orders (status=Draft, customer_id, address_id, total_amount)
        DB-->>OrderSvc: order_id

        OrderSvc->>PaySvc: CapturePayment(order_id, amount, payment_method, idemp_key)
        PaySvc->>PG: POST /charges (amount, token, idempotencyKey)

        alt Payment declined
            PG-->>PaySvc: Declined(reason, decline_code)
            PaySvc-->>OrderSvc: PaymentFailed(reason)
            OrderSvc->>InvSvc: ReleaseReservations(order_id)
            InvSvc->>DDB: DeleteItem reservation (reservationId)
            OrderSvc->>DB: ROLLBACK
            OrderSvc-->>Client: 402 Payment Required (reason)
        else Payment captured
            PG-->>PaySvc: Captured(gateway_ref, charge_id)
            PaySvc->>DB: INSERT payment_transactions (order_id, gateway_ref, status=CAPTURED)
            PaySvc-->>OrderSvc: PaymentCaptured(payment_id, gateway_ref)
            OrderSvc->>DB: UPDATE orders SET status=Confirmed, payment_id=payment_id
            OrderSvc->>DB: INSERT order_milestones (order_id, milestone=CONFIRMED, actor=system)
            OrderSvc->>DDB: PutItem {orderId, milestoneId=uuid, status=CONFIRMED, actorId=system, timestamp=ISO8601}
            OrderSvc->>DB: COMMIT
            OrderSvc->>EB: PutEvents {eventType: 'oms.order.confirmed.v1', orderId, customerId, totalAmount}
            OrderSvc->>Cache: SET idempotency:{key} = response (TTL 24h)
            OrderSvc-->>Client: 201 Created (order_id, order_number, estimated_delivery)
        end
    end
```

## 2. Delivery Status Update

```mermaid
sequenceDiagram
    participant DelivApp as DeliveryApp
    participant APIGW as API Gateway
    participant DelSvc as DeliveryService (Fargate)
    participant OrdSvc as OrderService (Lambda)
    participant DDB as DynamoDB (milestones)
    participant DB as PostgreSQL (assignments)
    participant EB as EventBridge
    participant NotifSvc as NotificationService (Lambda)
    participant Notify as SES / SNS / Pinpoint

    DelivApp->>APIGW: PATCH /deliveries/assignments/{id}/status (Bearer JWT, Idempotency-Key)
    APIGW->>DelSvc: route request (assignmentId, newStatus, staffId from JWT)

    DelSvc->>DB: SELECT assignment WHERE id = assignmentId AND staffId = authenticatedStaff
    DB-->>DelSvc: assignment record (currentStatus, orderId, customerId)

    DelSvc->>DelSvc: OrderStateMachine.validate(currentStatus, newStatus)

    alt Invalid state transition
        DelSvc-->>APIGW: 409 Conflict {error: INVALID_TRANSITION, currentStatus, allowedTransitions[]}
        APIGW-->>DelivApp: 409 Conflict response
    else Valid transition
        DelSvc->>DB: UPDATE delivery_assignments SET status = newStatus, updatedAt = NOW() WHERE id = assignmentId
        DB-->>DelSvc: rows updated = 1

        DelSvc->>OrdSvc: UpdateOrderStatus(orderId, mappedOrderStatus)
        OrdSvc->>DB: UPDATE orders SET status = mappedOrderStatus WHERE id = orderId
        OrdSvc-->>DelSvc: 200 OK

        DelSvc->>DDB: PutItem {orderId, milestoneId=uuid, status=newStatus, actorId=staffId, timestamp=ISO8601}
        DDB-->>DelSvc: PutItem OK

        DelSvc->>EB: PutEvents {eventType: 'oms.delivery.status_updated.v1', assignmentId, orderId, newStatus, actorId, occurredAt}
        EB-->>DelSvc: EventId acknowledged

        EB->>NotifSvc: invoke via EventBridge rule (delivery.status_updated → notify_customer)
        NotifSvc->>DB: SELECT customer contact preferences WHERE customerId
        DB-->>NotifSvc: email, phone, push_token, preferred_channel
        NotifSvc->>Notify: send status update (email via SES / SMS via SNS / push via Pinpoint)
        Notify-->>NotifSvc: messageId

        DelSvc-->>APIGW: 200 OK {assignmentId, newStatus, milestoneRecordedAt}
        APIGW-->>DelivApp: 200 OK response
    end
```

## 3. Return and Refund Processing

```mermaid
sequenceDiagram
    participant CustApp as CustomerApp
    participant APIGW as API Gateway
    participant RetSvc as ReturnService (Fargate)
    participant InvSvc as InventoryService (Lambda)
    participant PaySvc as PaymentService (Lambda)
    participant PG as PaymentGateway
    participant DDB as DynamoDB
    participant DB as PostgreSQL
    participant EB as EventBridge
    participant NotifSvc as NotificationService

    Note over CustApp,NotifSvc: Phase 1 — Initiation and Eligibility Check
    CustApp->>APIGW: POST /returns (orderId, lineItems[], reason, Bearer JWT)
    APIGW->>RetSvc: CreateReturn(customerId, orderId, lineItems, reason)

    RetSvc->>DB: SELECT orders WHERE id = orderId AND customerId = customerId
    DB-->>RetSvc: order (status, deliveredAt, categoryIds)
    RetSvc->>RetSvc: validate eligibility (status=DELIVERED, within 30-day window, category returnable)

    alt Not eligible
        RetSvc-->>APIGW: 422 Unprocessable Entity {reason: NOT_ELIGIBLE, detail}
        APIGW-->>CustApp: 422 response
    else Eligible
        RetSvc->>DB: INSERT return_requests (orderId, customerId, lineItems, reason, status=PENDING)
        DB-->>RetSvc: returnId

        RetSvc->>EB: PutEvents {eventType: 'oms.return.created.v1', returnId, orderId, customerId}
        EB->>NotifSvc: trigger — notify customer (return registered, pickup to be scheduled)
        NotifSvc->>CustApp: push notification — return request received

        RetSvc-->>APIGW: 201 Created {returnId, status: PENDING}
        APIGW-->>CustApp: 201 response

        Note over CustApp,NotifSvc: Phase 2 — Pickup Assignment
        RetSvc->>DB: SELECT available_delivery_staff WHERE zone = customerZone
        DB-->>RetSvc: staffId
        RetSvc->>DB: INSERT return_assignments (returnId, staffId, pickupAddress, scheduledAt)
        RetSvc->>DB: UPDATE return_requests SET status = PICKUP_SCHEDULED
        RetSvc->>EB: PutEvents {eventType: 'oms.return.pickup_scheduled.v1', returnId, staffId, scheduledAt}
        EB->>NotifSvc: trigger — staff push notification (new pickup assigned)
        NotifSvc->>CustApp: push notification — pickup scheduled, ETA window

        Note over CustApp,NotifSvc: Phase 3 — Pickup Confirmation
        RetSvc->>DB: UPDATE return_requests SET status = PICKED_UP, pickedUpAt = NOW()
        RetSvc->>DDB: PutItem {returnId, milestone=PICKED_UP, actorId=staffId, timestamp=ISO8601}
        RetSvc->>EB: PutEvents {eventType: 'oms.return.picked_up.v1', returnId}
        EB->>NotifSvc: notify customer — item picked up, under inspection

        Note over CustApp,NotifSvc: Phase 4 — Warehouse Inspection
        RetSvc->>DB: SELECT return_requests JOIN order_line_items WHERE returnId
        DB-->>RetSvc: return with line items and original prices
        RetSvc->>RetSvc: CalculateRefundAmount(lineItems, condition, restocking_policy)
        RetSvc->>DB: UPDATE return_requests SET status = INSPECTED, refundAmount, inspectionNotes
        RetSvc->>EB: PutEvents {eventType: 'oms.return.inspected.v1', result=ACCEPT, returnId, refundAmount}

        EB->>InvSvc: consume inspected (result=ACCEPT) — restore inventory
        InvSvc->>DB: UPDATE inventory SET qty_on_hand = qty_on_hand + returnedQty WHERE variantId
        InvSvc->>DB: INSERT inventory_movements (returnId, type=RETURN_RECEIPT, qty)

        Note over CustApp,NotifSvc: Phase 5 — Refund Initiation
        EB->>PaySvc: consume inspected (result=ACCEPT, refundAmount)
        PaySvc->>DB: SELECT payment_transactions WHERE orderId AND status=CAPTURED
        DB-->>PaySvc: paymentRecord (gateway_ref, gatewayType)
        PaySvc->>PG: POST /v1/refunds (paymentRef=gateway_ref, amount=refundAmount, idempotencyKey)

        alt Refund initiated successfully
            PG-->>PaySvc: {refundId, status=PENDING}
            PaySvc->>DB: INSERT refund_records (returnId, refundId, amount, status=INITIATED, gatewayRef)
            PaySvc->>EB: PutEvents {eventType: 'oms.payment.refund.initiated.v1', refundId, customerId, amount, timeline: '3-5 business days'}
            EB->>NotifSvc: notify customer — refund initiated, timeline 3–5 business days
        else Gateway error
            PG-->>PaySvc: 5xx or timeout
            PaySvc->>DB: INSERT refund_records (returnId, status=FAILED)
            PaySvc->>PaySvc: ScheduleRetry(maxAttempts=3, backoff=exponential)
        end

        Note over CustApp,NotifSvc: Phase 6 — Async Refund Completion (Webhook)
        PG->>PaySvc: POST /webhooks/refund {event: refund.updated, status=succeeded, refundId}
        PaySvc->>PaySvc: verify webhook signature (HMAC)
        PaySvc->>DB: UPDATE refund_records SET status = COMPLETED, completedAt = NOW() WHERE refundId
        PaySvc->>DB: UPDATE return_requests SET status = REFUNDED WHERE returnId
        PaySvc->>EB: PutEvents {eventType: 'oms.payment.refund.completed.v1', refundId, customerId, amount}
        EB->>NotifSvc: final notification — refund credited to original payment method
        NotifSvc->>CustApp: push + email — refund of {amount} has been processed
    end
```

## 4. Payment Capture with Gateway Failover

```mermaid
sequenceDiagram
    participant ChkSvc as CheckoutService (Lambda)
    participant CB as CircuitBreaker
    participant Stripe as StripeGateway
    participant Khalti as KhaltiGateway
    participant PayRepo as PaymentRepository (RDS)
    participant InvSvc as InventoryService (Lambda)
    participant EB as EventBridge

    ChkSvc->>CB: checkState(gateway=STRIPE)
    CB-->>ChkSvc: state=CLOSED — proceed with primary

    alt Alt A — Stripe success
        ChkSvc->>Stripe: POST /charges {idempotencyKey, amount, currency, token, customerId}
        Stripe-->>ChkSvc: 200 {chargeId, status=succeeded, gatewayRef}
        CB->>CB: recordSuccess(STRIPE)
        ChkSvc->>PayRepo: INSERT payment_transactions (orderId, gatewayRef=chargeId, gateway=STRIPE, status=CAPTURED, amount)
        PayRepo-->>ChkSvc: paymentId
        ChkSvc->>EB: PutEvents {eventType: 'oms.payment.captured.v1', orderId, paymentId, gateway=STRIPE, amount}

    else Alt B — Stripe timeout or 5xx
        Stripe-->>ChkSvc: 503 / timeout
        CB->>CB: recordFailure(STRIPE) — threshold reached → OPEN circuit
        Note over CB: Circuit OPEN — Stripe bypassed for next 60 s
        ChkSvc->>CB: checkState(gateway=KHALTI)
        CB-->>ChkSvc: state=CLOSED — proceed with fallback
        ChkSvc->>Khalti: POST /payment/initiate {idempotencyKey, amount, orderId, returnUrl}
        Khalti-->>ChkSvc: 200 {pidx, payment_url, expiresAt}
        ChkSvc->>PayRepo: INSERT payment_transactions (orderId, gatewayRef=pidx, gateway=KHALTI, status=PENDING_REDIRECT, amount)
        PayRepo-->>ChkSvc: paymentId
        ChkSvc->>EB: PutEvents {eventType: 'oms.payment.redirect_required.v1', orderId, payment_url, gateway=KHALTI}

        Note over Khalti,ChkSvc: [After customer completes Khalti payment — webhook]
        Khalti->>ChkSvc: POST /webhooks/khalti {pidx, status=Completed, transaction_id}
        ChkSvc->>PayRepo: UPDATE payment_transactions SET status=CAPTURED, gatewayRef=transaction_id WHERE pidx
        ChkSvc->>EB: PutEvents {eventType: 'oms.payment.captured.v1', orderId, paymentId, gateway=KHALTI, amount}

    else Alt C — Both gateways fail
        Stripe-->>ChkSvc: failure
        Khalti-->>ChkSvc: failure
        ChkSvc->>PayRepo: INSERT payment_transactions (orderId, status=FAILED, failureReason)
        ChkSvc->>InvSvc: ReleaseReservations(orderId)
        InvSvc-->>ChkSvc: reservations released
        ChkSvc->>EB: PutEvents {eventType: 'oms.payment.failed.v1', orderId, customerId, reason}
        EB->>ChkSvc: route to NotificationService — customer notified of payment failure
    end
```

> **Note:** The same `idempotencyKey` is forwarded to both the primary and fallback gateway calls. Each gateway treats it independently via its own idempotency header, ensuring no duplicate charge even if the client retries the checkout request.

## 5. POD Upload with Offline Sync

```mermaid
sequenceDiagram
    participant DelivApp as DeliveryApp
    participant SQ as SyncQueue (local SQLite)
    participant APIGW as API Gateway
    participant DelSvc as DeliveryService (Fargate)
    participant S3 as Amazon S3
    participant DB as PostgreSQL
    participant DDB as DynamoDB
    participant EB as EventBridge

    alt Online path — network available
        DelivApp->>APIGW: POST /deliveries/assignments/{id}/pod (multipart: signature.jpg, photo.jpg, notes, capturedAt)
        APIGW->>DelSvc: SubmitPOD(assignmentId, staffId from JWT, artifacts)

        DelSvc->>DB: SELECT delivery_assignments WHERE id = assignmentId AND staffId = staffId
        DB-->>DelSvc: assignment (status=OUT_FOR_DELIVERY, orderId)
        DelSvc->>DelSvc: validate — status must be OUT_FOR_DELIVERY, staffId must match

        DelSvc->>S3: PutObject(key=pod/{orderId}/signature.jpg, body=signatureBytes, SSE=AES-256)
        S3-->>DelSvc: ETag, signatureKey

        DelSvc->>S3: PutObject(key=pod/{orderId}/photo.jpg, body=photoBytes, SSE=AES-256)
        S3-->>DelSvc: ETag, photoKey

        DelSvc->>DB: INSERT proof_of_delivery (podId=uuid, assignmentId, orderId, signatureKey, photoKey, notes, capturedAt, uploadedAt=NOW())
        DB-->>DelSvc: podId

        DelSvc->>DB: UPDATE delivery_assignments SET status = DELIVERED, completedAt = NOW() WHERE id = assignmentId
        DelSvc->>DB: UPDATE orders SET status = DELIVERED, deliveredAt = NOW() WHERE id = orderId

        DelSvc->>DDB: PutItem {orderId, milestoneId=uuid, milestone=DELIVERED, actorId=staffId, timestamp=ISO8601, podId}
        DDB-->>DelSvc: PutItem OK

        DelSvc->>EB: PutEvents {eventType: 'oms.order.delivered.v1', orderId, podId, staffId, deliveredAt}
        EB-->>DelSvc: EventId acknowledged

        DelSvc-->>APIGW: 200 OK {podId, status: DELIVERED, deliveredAt}
        APIGW-->>DelivApp: 200 OK — mark assignment complete in local state

    else Offline path — no network
        DelivApp->>SQ: store POD locally (assignmentId, signatureBytes, photoBytes, notes, capturedAt, retryCount=0)
        SQ-->>DelivApp: queued (localId)
        Note over DelivApp,SQ: App shows "Saved offline — will sync when connected"

        Note over DelivApp,APIGW: [On network reconnect — background flush]
        DelivApp->>SQ: getUnsynced() — fetch pending queue items
        SQ-->>DelivApp: [{localId, assignmentId, artifacts}]

        DelivApp->>APIGW: POST /deliveries/assignments/{id}/pod (same payload + Idempotency-Key=localId)
        APIGW->>DelSvc: SubmitPOD(assignmentId, staffId, artifacts, idempotencyKey=localId)

        alt Server accepts (first successful sync)
            DelSvc-->>APIGW: 200 OK {podId, status: DELIVERED}
            APIGW-->>DelivApp: 200 OK
            DelivApp->>SQ: markSynced(localId)
        else Duplicate — already delivered by another path (409 Conflict)
            DelSvc-->>APIGW: 409 Conflict {error: ALREADY_DELIVERED, existingPodId}
            APIGW-->>DelivApp: 409 response
            DelivApp->>SQ: markResolved(localId, reason=ALREADY_DELIVERED)
            Note over DelivApp: App reconciles local state — shows delivered status
        end
    end
```
