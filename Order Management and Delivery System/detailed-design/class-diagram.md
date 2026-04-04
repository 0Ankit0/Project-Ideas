# Class Diagram

## Overview

Detailed UML class diagrams for the Order Management and Delivery System, covering all bounded contexts with attributes, methods, and relationships.

## Order Bounded Context

```mermaid
classDiagram
    class Order {
        -UUID orderId
        -String orderNumber
        -UUID customerId
        -UUID deliveryAddressId
        -OrderStatus status
        -Money subtotal
        -Money taxAmount
        -Money shippingFee
        -Money discountAmount
        -Money totalAmount
        -UUID couponId
        -UUID paymentId
        -String cancellationReason
        -Timestamp estimatedDelivery
        -Timestamp deliveredAt
        -String idempotencyKey
        -Timestamp createdAt
        -Timestamp updatedAt
        +confirm(paymentId) void
        +cancel(reason) void
        +transitionTo(newStatus) void
        +canTransitionTo(target) boolean
        +calculateTotal() Money
        +addLineItem(item) void
        +removeLineItem(itemId) void
    }

    class OrderLineItem {
        -UUID lineItemId
        -UUID orderId
        -UUID variantId
        -String productTitle
        -String variantLabel
        -Integer quantity
        -Money unitPrice
        -Money lineTotal
        +calculateLineTotal() Money
    }

    class OrderMilestone {
        -UUID milestoneId
        -UUID orderId
        -OrderStatus status
        -UUID actorId
        -String actorRole
        -String notes
        -Timestamp recordedAt
    }

    class OrderStateMachine {
        +getAllowedTransitions(current) List~OrderStatus~
        +validate(current, target) boolean
        +apply(order, target, actor) void
    }

    Order "1" --> "*" OrderLineItem : contains
    Order "1" --> "*" OrderMilestone : tracks
    OrderStateMachine ..> Order : validates transitions
```

## Product and Inventory Context

```mermaid
classDiagram
    class Category {
        -UUID categoryId
        -UUID parentId
        -String name
        -Integer displayOrder
        -Boolean returnable
        -Status status
        +addChild(category) void
        +archive() void
    }

    class Product {
        -UUID productId
        -UUID categoryId
        -String title
        -String description
        -Money basePrice
        -String currency
        -JSONB images
        -JSONB specifications
        -Status status
        +addVariant(data) ProductVariant
        +archive() void
        +isAvailable() boolean
    }

    class ProductVariant {
        -UUID variantId
        -UUID productId
        -String sku
        -JSONB attributes
        -Money priceAdjustment
        -Integer weightGrams
        -Status status
        +effectivePrice() Money
    }

    class Inventory {
        -UUID inventoryId
        -UUID variantId
        -UUID warehouseId
        -Integer quantityOnHand
        -Integer quantityReserved
        -Integer lowStockThreshold
        -Timestamp updatedAt
        +availableQuantity() Integer
        +reserve(qty, ttl) InventoryReservation
        +release(qty) void
        +adjust(qty, reason) void
        +isLowStock() boolean
    }

    class InventoryReservation {
        -UUID reservationId
        -UUID inventoryId
        -UUID orderId
        -Integer quantity
        -Timestamp expiresAt
        -ReservationStatus status
        +isExpired() boolean
        +release() void
        +confirm() void
    }

    Category "1" --> "*" Category : children
    Category "1" --> "*" Product : contains
    Product "1" --> "*" ProductVariant : has
    ProductVariant "1" --> "*" Inventory : tracked at
    Inventory "1" --> "*" InventoryReservation : reservations
```

## Delivery and POD Context

```mermaid
classDiagram
    class DeliveryAssignment {
        -UUID assignmentId
        -UUID orderId
        -UUID staffId
        -UUID deliveryZoneId
        -Timestamp scheduledWindowStart
        -Timestamp scheduledWindowEnd
        -Integer attemptCount
        -AssignmentStatus status
        -Timestamp createdAt
        +recordPickup() void
        +startDelivery() void
        +recordFailure(reason) void
        +complete(podId) void
        +canRetry() boolean
    }

    class ProofOfDelivery {
        -UUID podId
        -UUID orderId
        -UUID staffId
        -String signatureS3Key
        -List~String~ photoS3Keys
        -String deliveryNotes
        -Timestamp capturedAt
        -Timestamp uploadedAt
        +isComplete() boolean
        +getSignatureUrl(expiry) String
        +getPhotoUrls(expiry) List~String~
    }

    class DeliveryZone {
        -UUID zoneId
        -String name
        -List~String~ postalCodes
        -Money deliveryFee
        -Money minOrderValue
        -Duration slaTarget
        -Boolean isActive
        +containsPostalCode(code) boolean
        +deactivate() void
    }

    class Staff {
        -UUID staffId
        -String name
        -String email
        -String phone
        -StaffRole role
        -UUID warehouseId
        -UUID deliveryZoneId
        -Boolean isActive
        -Timestamp createdAt
        +assignToZone(zoneId) void
        +assignToWarehouse(whId) void
        +deactivate() void
    }

    DeliveryAssignment "*" --> "1" Staff : assigned to
    DeliveryAssignment "*" --> "1" DeliveryZone : within
    DeliveryAssignment "1" --> "0..1" ProofOfDelivery : completed with
```

## Payment Context

```mermaid
classDiagram
    class PaymentTransaction {
        -UUID paymentId
        -UUID orderId
        -Money amount
        -String currency
        -String gatewayName
        -String gatewayRef
        -PaymentStatus status
        -String idempotencyKey
        -Timestamp createdAt
        -Timestamp updatedAt
        +capture() void
        +refund(amount) RefundRecord
        +canRefund() boolean
        +totalRefunded() Money
    }

    class RefundRecord {
        -UUID refundId
        -UUID paymentId
        -UUID orderId
        -Money amount
        -String reason
        -String gatewayRef
        -RefundStatus status
        -Timestamp createdAt
        +isCompleted() boolean
    }

    PaymentTransaction "1" --> "*" RefundRecord : refunds
```

## Return Context

```mermaid
classDiagram
    class ReturnRequest {
        -UUID returnId
        -UUID orderId
        -UUID customerId
        -String reasonCode
        -JSONB evidenceS3Keys
        -ReturnStatus status
        -String inspectionResult
        -Money refundAmount
        -Timestamp createdAt
        -Timestamp resolvedAt
        +isEligible(order) boolean
        +assignPickup(staffId) void
        +recordInspection(result, notes) void
        +calculateRefund(lineItems) Money
    }

    class ReturnPickup {
        -UUID pickupId
        -UUID returnId
        -UUID staffId
        -PickupStatus status
        -String conditionNotes
        -Timestamp collectedAt
        +confirmCollection() void
    }

    ReturnRequest "1" --> "0..1" ReturnPickup : pickup
```
