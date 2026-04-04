# Domain Model

## Overview

This document presents the high-level domain model for the Order Management and Delivery System, identifying core aggregates, value objects, and their relationships.

## Bounded Contexts

| Context | Responsibility | Core Aggregates |
|---|---|---|
| Customer Management | Registration, profiles, addresses, auth | Customer, Address |
| Product Catalog | Categories, products, variants, search | Category, Product, ProductVariant |
| Inventory | Stock tracking, reservations, adjustments | Inventory, InventoryReservation |
| Order | Order lifecycle, line items, state machine | Order, OrderLineItem, OrderMilestone |
| Payment | Capture, refund, reconciliation | PaymentTransaction, RefundRecord |
| Fulfillment | Pick, pack, manifest generation | FulfillmentTask, PackingSlip |
| Delivery | Assignment, status tracking, POD | DeliveryAssignment, ProofOfDelivery |
| Returns | Return requests, pickup, inspection | ReturnRequest, ReturnPickup, ReturnInspection |
| Notification | Template management, dispatch, tracking | NotificationTemplate, NotificationRecord |
| Analytics | Dashboards, reports, KPIs | SalesMetric, DeliveryMetric, InventoryMetric |
| Administration | RBAC, config, staff, audit | Staff, DeliveryZone, Warehouse, AuditLog, PlatformConfig |

## Domain Model Diagram

```mermaid
classDiagram
    class Customer {
        +UUID customerId
        +String email
        +String phone
        +String fullName
        +AuthProvider authProvider
        +NotificationPrefs notificationPrefs
        +Status status
        +addAddress(Address)
        +updateProfile(ProfileData)
    }

    class Address {
        +UUID addressId
        +String label
        +String line1
        +String line2
        +String city
        +String postalCode
        +Boolean isDefault
        +isServiceable() Boolean
    }

    class Category {
        +UUID categoryId
        +UUID parentId
        +String name
        +Integer displayOrder
        +Boolean returnable
    }

    class Product {
        +UUID productId
        +String title
        +String description
        +Money basePrice
        +Status status
        +addVariant(VariantData)
        +archive()
    }

    class ProductVariant {
        +UUID variantId
        +String sku
        +JSONB attributes
        +Money priceAdjustment
        +Integer weightGrams
        +effectivePrice() Money
    }

    class Inventory {
        +UUID inventoryId
        +Integer quantityOnHand
        +Integer quantityReserved
        +Integer lowStockThreshold
        +availableQuantity() Integer
        +reserve(qty, ttl)
        +release(qty)
        +adjust(qty, reason)
    }

    class Order {
        +UUID orderId
        +String orderNumber
        +OrderStatus status
        +Money subtotal
        +Money taxAmount
        +Money shippingFee
        +Money discountAmount
        +Money totalAmount
        +confirm(paymentId)
        +cancel(reason)
        +transitionTo(newStatus)
    }

    class OrderLineItem {
        +UUID lineItemId
        +Integer quantity
        +Money unitPrice
        +Money lineTotal
    }

    class DeliveryAssignment {
        +UUID assignmentId
        +TimeWindow scheduledWindow
        +Integer attemptCount
        +AssignmentStatus status
        +recordPickup()
        +startDelivery()
        +recordFailure(reason)
        +complete(podId)
    }

    class ProofOfDelivery {
        +UUID podId
        +String signatureS3Key
        +List~String~ photoS3Keys
        +String deliveryNotes
        +Timestamp capturedAt
    }

    class PaymentTransaction {
        +UUID paymentId
        +Money amount
        +String gatewayRef
        +PaymentStatus status
        +capture()
        +refund(amount)
    }

    class ReturnRequest {
        +UUID returnId
        +String reasonCode
        +ReturnStatus status
        +Money refundAmount
        +initiate()
        +assignPickup(staffId)
        +recordInspection(result)
    }

    class FulfillmentTask {
        +UUID taskId
        +TaskStatus status
        +startPicking()
        +scanItem(sku, qty)
        +completePacking(dimensions)
    }

    class Staff {
        +UUID staffId
        +String name
        +StaffRole role
        +UUID warehouseId
        +UUID deliveryZoneId
        +Boolean isActive
    }

    class DeliveryZone {
        +UUID zoneId
        +String name
        +List~String~ postalCodes
        +Money deliveryFee
        +Money minOrderValue
        +Duration slaTarget
    }

    class Warehouse {
        +UUID warehouseId
        +String name
        +String location
    }

    Customer "1" --> "*" Address
    Customer "1" --> "*" Order
    Category "1" --> "*" Product
    Category "1" --> "*" Category : parent
    Product "1" --> "*" ProductVariant
    ProductVariant "1" --> "*" Inventory
    Warehouse "1" --> "*" Inventory
    Order "1" --> "*" OrderLineItem
    OrderLineItem "*" --> "1" ProductVariant
    Order "1" --> "0..1" PaymentTransaction
    Order "1" --> "0..1" DeliveryAssignment
    Order "1" --> "0..1" ProofOfDelivery
    Order "1" --> "*" ReturnRequest
    Order "1" --> "1" FulfillmentTask
    DeliveryAssignment "*" --> "1" Staff
    DeliveryAssignment "*" --> "1" DeliveryZone
    Staff "*" --> "0..1" Warehouse
    Staff "*" --> "0..1" DeliveryZone
```

## Customer Management Domain

```mermaid
classDiagram
    class Customer {
        +UUID customerId
        +String email
        +String phone
        +String fullName
        +AuthProvider authProvider
        +String cognitoSub
        +CustomerStatus status
        +Timestamp createdAt
        +register()
        +updateProfile(data)
        +deactivate()
    }

    class Address {
        +UUID addressId
        +UUID customerId
        +String label
        +String line1
        +String line2
        +String city
        +String state
        +String postalCode
        +String country
        +Boolean isDefault
        +validate()
        +isServiceable() Boolean
        +setAsDefault()
    }

    class NotificationPreference {
        +UUID prefId
        +UUID customerId
        +Boolean emailEnabled
        +Boolean smsEnabled
        +Boolean pushEnabled
        +Boolean marketingOptIn
        +Timestamp updatedAt
        +update(prefs)
        +canReceive(channel) Boolean
    }

    Customer "1" --> "*" Address
    Customer "1" --> "1" NotificationPreference
```

## Product Catalog Domain

```mermaid
classDiagram
    class Category {
        +UUID categoryId
        +UUID parentId
        +String name
        +Integer displayOrder
        +Boolean returnable
        +CategoryStatus status
        +getChildren() List~Category~
        +getPath() List~Category~
        +archive()
    }

    class Product {
        +UUID productId
        +UUID categoryId
        +String title
        +String description
        +Money basePrice
        +JSONB images
        +JSONB specifications
        +ProductStatus status
        +addVariant(variantData)
        +archive()
        +isAvailable() Boolean
    }

    class ProductVariant {
        +UUID variantId
        +UUID productId
        +String sku
        +JSONB attributes
        +Money priceAdjustment
        +Integer weightGrams
        +effectivePrice() Money
        +checkAvailability() Boolean
    }

    class ProductImage {
        +UUID imageId
        +UUID productId
        +String s3Key
        +String altText
        +Integer position
        +Boolean isPrimary
    }

    class Inventory {
        +UUID inventoryId
        +UUID variantId
        +UUID warehouseId
        +Integer quantityOnHand
        +Integer quantityReserved
        +Integer lowStockThreshold
        +Timestamp updatedAt
        +availableQuantity() Integer
        +reserve(qty, ttl)
        +release(qty)
        +adjust(qty, reason)
        +isLowStock() Boolean
    }

    class InventoryReservation {
        +UUID reservationId
        +UUID inventoryId
        +UUID orderId
        +Integer quantity
        +Timestamp expiresAt
        +ReservationStatus status
        +isExpired() Boolean
        +commit()
        +release()
    }

    Category "1" --> "*" Product
    Product "1" --> "*" ProductVariant
    Product "1" --> "*" ProductImage
    ProductVariant "1" --> "*" Inventory
    Inventory "1" --> "*" InventoryReservation
```

## Cart and Order Domain

```mermaid
classDiagram
    class Cart {
        +UUID cartId
        +UUID customerId
        +String sessionId
        +Timestamp updatedAt
        +addItem(variantId, qty)
        +removeItem(itemId)
        +updateQuantity(itemId, qty)
        +applyCoupon(code)
        +clear()
        +getTotal() Money
        +checkout()
    }

    class CartItem {
        +UUID itemId
        +UUID cartId
        +UUID variantId
        +Integer quantity
        +Money priceAtAdd
        +Timestamp addedAt
        +getLineTotal() Money
        +isAvailable() Boolean
    }

    class Coupon {
        +UUID couponId
        +String code
        +CouponType discountType
        +Decimal discountValue
        +Money minOrderValue
        +Timestamp validFrom
        +Timestamp validTo
        +Integer usageLimit
        +Integer usageCount
        +validate(cartTotal) Boolean
        +apply(cart) Money
        +isExpired() Boolean
        +isExhausted() Boolean
    }

    class Order {
        +UUID orderId
        +String orderNumber
        +UUID customerId
        +UUID deliveryAddressId
        +OrderStatus status
        +Money subtotal
        +Money taxAmount
        +Money shippingFee
        +Money discountAmount
        +Money totalAmount
        +UUID couponId
        +UUID paymentId
        +String idempotencyKey
        +Timestamp estimatedDelivery
        +Timestamp createdAt
        +Timestamp updatedAt
        +confirm(paymentId)
        +cancel(reason)
        +transitionTo(newStatus)
        +calculateTotal() Money
    }

    class OrderLineItem {
        +UUID lineItemId
        +UUID orderId
        +UUID variantId
        +String productTitle
        +String variantLabel
        +Integer quantity
        +Money unitPrice
        +Money lineTotal
        +calculateLineTotal() Money
    }

    class OrderMilestone {
        +UUID milestoneId
        +UUID orderId
        +OrderStatus status
        +UUID actorId
        +String actorRole
        +String notes
        +Timestamp recordedAt
    }

    Cart "1" --> "*" CartItem
    Cart "0..1" --> "*" Coupon
    Order "1" --> "*" OrderLineItem
    Order "1" --> "*" OrderMilestone
```

## Payment Domain

```mermaid
classDiagram
    class PaymentTransaction {
        +UUID paymentId
        +UUID orderId
        +Money amount
        +String currency
        +String gatewayName
        +String gatewayRef
        +String idempotencyKey
        +PaymentStatus status
        +Timestamp createdAt
        +Timestamp capturedAt
        +capture()
        +refund(amount)
        +canRefund() Boolean
        +totalRefunded() Money
    }

    class RefundRecord {
        +UUID refundId
        +UUID paymentId
        +UUID orderId
        +Money amount
        +String reason
        +String gatewayRef
        +RefundStatus status
        +Integer retryCount
        +Timestamp createdAt
        +Timestamp completedAt
        +process()
        +retry()
        +isCompleted() Boolean
    }

    class ReconciliationReport {
        +UUID reportId
        +Date date
        +Timestamp periodStart
        +Timestamp periodEnd
        +Money totalCaptures
        +Money totalRefunds
        +Money netSettlement
        +Integer discrepancyCount
        +Timestamp generatedAt
        +generate()
        +export(format) Blob
        +hasDiscrepancies() Boolean
    }

    PaymentTransaction "1" --> "*" RefundRecord
```

## Fulfillment Domain

```mermaid
classDiagram
    class FulfillmentTask {
        +UUID taskId
        +UUID orderId
        +UUID warehouseId
        +UUID assignedStaffId
        +FulfillmentTaskStatus status
        +Timestamp slaDeadline
        +Timestamp createdAt
        +Timestamp startedAt
        +Timestamp completedAt
        +start()
        +scanItem(sku, qty)
        +completePicking()
        +startPacking()
        +completePacking()
    }

    class PickItem {
        +UUID pickItemId
        +UUID taskId
        +UUID variantId
        +String sku
        +String warehouseBin
        +Integer expectedQty
        +Integer scannedQty
        +PickItemStatus status
        +scan(barcode)
        +isMismatch() Boolean
    }

    class PackingSlip {
        +UUID slipId
        +UUID taskId
        +UUID orderId
        +String pdfS3Key
        +Timestamp generatedAt
        +generate()
        +getDownloadUrl(expiry) String
    }

    class DeliveryManifest {
        +UUID manifestId
        +UUID warehouseId
        +UUID deliveryZoneId
        +Date date
        +ManifestStatus status
        +Integer taskCount
        +addTask(taskId)
        +seal()
        +dispatch()
    }

    FulfillmentTask "1" --> "*" PickItem
    FulfillmentTask "1" --> "1" PackingSlip
    DeliveryManifest "*" --> "*" FulfillmentTask
```

## Delivery Domain

```mermaid
classDiagram
    class DeliveryAssignment {
        +UUID assignmentId
        +UUID orderId
        +UUID staffId
        +UUID deliveryZoneId
        +Timestamp scheduledWindowStart
        +Timestamp scheduledWindowEnd
        +Integer attemptCount
        +DeliveryAssignmentStatus status
        +recordPickup()
        +startDelivery()
        +recordFailure(reason)
        +complete(podId)
        +canRetry() Boolean
    }

    class ProofOfDelivery {
        +UUID podId
        +UUID orderId
        +UUID staffId
        +String signatureS3Key
        +List~String~ photoS3Keys
        +String deliveryNotes
        +Timestamp capturedAt
        +Timestamp uploadedAt
        +isComplete() Boolean
        +getSignatureUrl(expiry) String
        +getPhotoUrls(expiry) List~String~
    }

    class DeliveryZone {
        +UUID zoneId
        +String name
        +List~String~ postalCodes
        +Money deliveryFee
        +Money minOrderValue
        +Duration slaTarget
        +Boolean isActive
        +containsPostalCode(code) Boolean
        +deactivate()
    }

    class Staff {
        +UUID staffId
        +String name
        +String email
        +String phone
        +StaffRole role
        +UUID warehouseId
        +UUID deliveryZoneId
        +Boolean isActive
        +Timestamp createdAt
        +assignToZone(zoneId)
        +assignToWarehouse(whId)
        +deactivate()
    }

    DeliveryAssignment "*" --> "1" Staff
    DeliveryAssignment "*" --> "1" DeliveryZone
    DeliveryAssignment "1" --> "0..1" ProofOfDelivery
```

## Returns Domain

```mermaid
classDiagram
    class ReturnRequest {
        +UUID returnId
        +UUID orderId
        +UUID customerId
        +String reasonCode
        +JSONB evidenceS3Keys
        +ReturnStatus status
        +Money refundAmount
        +Timestamp createdAt
        +Timestamp resolvedAt
        +isEligible(order) Boolean
        +assignPickup(staffId)
        +recordInspection(result, notes)
        +calculateRefund() Money
    }

    class ReturnPickup {
        +UUID pickupId
        +UUID returnId
        +UUID staffId
        +PickupStatus status
        +String conditionNotes
        +Timestamp collectedAt
        +confirmCollection(notes)
        +recordFailure(reason)
    }

    class ReturnInspection {
        +UUID inspectionId
        +UUID returnId
        +UUID staffId
        +InspectionResult result
        +String notes
        +Integer itemsAccepted
        +Integer itemsRejected
        +String rejectionReason
        +Timestamp inspectedAt
        +record(result, notes)
        +triggerRefund()
    }

    ReturnRequest "1" --> "0..1" ReturnPickup
    ReturnRequest "1" --> "0..1" ReturnInspection
```

## Notification Domain

```mermaid
classDiagram
    class NotificationTemplate {
        +UUID templateId
        +String name
        +String eventType
        +NotificationChannel channel
        +String subjectTemplate
        +String bodyTemplate
        +List~String~ variables
        +Boolean isActive
        +Integer version
        +Timestamp createdAt
        +render(vars) String
        +publish()
        +rollback()
    }

    class NotificationRecord {
        +UUID recordId
        +UUID recipientId
        +NotificationChannel channel
        +String eventType
        +UUID templateId
        +String subject
        +String body
        +NotificationStatus status
        +String externalRef
        +Integer retryCount
        +Timestamp createdAt
        +Timestamp sentAt
        +markSent(ref)
        +markDelivered()
        +markFailed(reason)
        +retry()
    }

    NotificationTemplate "1" --> "*" NotificationRecord
```

## Admin and Audit Domain

```mermaid
classDiagram
    class AuditLog {
        +UUID logId
        +UUID actorId
        +String actorRole
        +String action
        +String resourceType
        +UUID resourceId
        +JSONB beforeValue
        +JSONB afterValue
        +String ipAddress
        +String correlationId
        +Timestamp timestamp
    }

    class PlatformConfig {
        +UUID configId
        +String key
        +String value
        +String dataType
        +String description
        +Integer version
        +Boolean isActive
        +UUID updatedBy
        +Timestamp updatedAt
        +getValue() Any
        +update(value, actorId)
        +rollback(version)
        +getHistory() List~PlatformConfig~
    }

    note for AuditLog "Immutable append-only log.\nNo mutation methods — records are\nwritten once and never updated."
```

## Enumeration Types

```mermaid
classDiagram
    class OrderStatus {
        <<enumeration>>
        CONFIRMED
        READY_FOR_DISPATCH
        PICKED_UP
        OUT_FOR_DELIVERY
        DELIVERED
        CANCELLED
        RETURNED_TO_WAREHOUSE
    }

    class PaymentStatus {
        <<enumeration>>
        PENDING
        AUTHORIZED
        CAPTURED
        FAILED
        REFUNDED
        PARTIALLY_REFUNDED
    }

    class ReturnStatus {
        <<enumeration>>
        REQUESTED
        PICKUP_ASSIGNED
        PICKED_UP
        INSPECTING
        ACCEPTED
        REJECTED
        PARTIALLY_ACCEPTED
    }

    class StaffRole {
        <<enumeration>>
        WAREHOUSE_STAFF
        DELIVERY_STAFF
        OPERATIONS_MANAGER
        FINANCE
        ADMIN
    }

    class DeliveryAssignmentStatus {
        <<enumeration>>
        ASSIGNED
        PICKED_UP
        OUT_FOR_DELIVERY
        DELIVERED
        FAILED
        RETURNED_TO_WAREHOUSE
    }

    class FulfillmentTaskStatus {
        <<enumeration>>
        PENDING
        IN_PROGRESS
        PICKED
        PACKED
        DISPATCHED
    }

    class CouponType {
        <<enumeration>>
        PERCENTAGE
        FIXED_AMOUNT
        FREE_SHIPPING
    }

    class NotificationChannel {
        <<enumeration>>
        EMAIL
        SMS
        PUSH
    }
```

## Aggregate Boundaries

| Aggregate Root | Entities Inside Boundary | Invariants |
|---|---|---|
| Order | OrderLineItem, OrderMilestone | Total = sum(line_totals) + tax + shipping - discount; state transitions follow FSM |
| Product | ProductVariant | At least one variant per product; SKU globally unique |
| Inventory | InventoryReservation | qty_on_hand >= 0; qty_reserved <= qty_on_hand; reservation has TTL |
| DeliveryAssignment | (standalone) | attempt_count <= max_attempts; zone must match address zone |
| ReturnRequest | ReturnPickup, ReturnInspection | Return within window; refund_amount <= original payment |
| PaymentTransaction | RefundRecord | Refund total <= capture amount; idempotent operations |
| FulfillmentTask | (standalone) | All items scanned before pack complete; one active task per staff |
