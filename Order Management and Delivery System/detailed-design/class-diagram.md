# Class Diagram

## Overview

Detailed UML class diagrams for the Order Management and Delivery System, covering all bounded contexts with attributes, methods, and relationships.

---

## Customer Domain

```mermaid
classDiagram
    class Customer {
        -UUID customerId
        -String email
        -String phone
        -String fullName
        -String passwordHash
        -String cognitoSub
        -String authProvider
        -CustomerStatus status
        -Timestamp createdAt
        -Timestamp updatedAt
        -Timestamp lastLoginAt
        +register(email, phone) Customer
        +login() AuthToken
        +logout() void
        +updateProfile(data) Customer
        +requestPasswordReset(email) void
        +verifyOTP(code) boolean
        +updateNotificationPrefs(prefs) void
        +deactivate() void
    }

    class Address {
        -UUID addressId
        -UUID customerId
        -String label
        -String line1
        -String line2
        -String city
        -String state
        -String postalCode
        -String country
        -Boolean isDefault
        -Timestamp createdAt
        +validate() boolean
        +isServiceable() boolean
        +setAsDefault() void
        +canDelete() boolean
    }

    class NotificationPreference {
        -UUID prefId
        -UUID customerId
        -Boolean emailEnabled
        -Boolean smsEnabled
        -Boolean pushEnabled
        -Boolean marketingEnabled
        -Timestamp updatedAt
        +update(prefs) void
        +canSend(channel, type) boolean
    }

    Customer "1" --> "*" Address : has
    Customer "1" --> "1" NotificationPreference : configures
```

---

## Cart and Coupon Context

```mermaid
classDiagram
    class Cart {
        -UUID cartId
        -UUID customerId
        -String sessionId
        -Timestamp updatedAt
        +addItem(variantId, qty) CartItem
        +removeItem(itemId) void
        +updateQuantity(itemId, qty) void
        +clear() void
        +getTotal() CartTotal
        +applyCoupon(code) DiscountResult
        +removeCoupon() void
        +validateAvailability() boolean
        +mergeGuestCart(guestCartId) void
        +checkout() Order
    }

    class CartItem {
        -UUID itemId
        -UUID cartId
        -UUID variantId
        -Integer quantity
        -Money priceAtAdd
        -Timestamp reservedUntil
        -Timestamp addedAt
        +getLineTotal() Money
        +isAvailable() boolean
        +isReservationExpired() boolean
    }

    class CartTotal {
        -Money subtotal
        -Money taxAmount
        -Money shippingFee
        -Money discountAmount
        -Money totalAmount
        -String couponCode
        +recalculate() void
    }

    class Coupon {
        -UUID couponId
        -String code
        -String name
        -DiscountType discountType
        -Decimal discountValue
        -Money minOrderValue
        -Money maxDiscountAmount
        -Timestamp validFrom
        -Timestamp validTo
        -Integer usageLimit
        -Integer usageCount
        -Integer perCustomerLimit
        -List~String~ applicableCategories
        -Boolean isActive
        +validate(cartTotal, customerId) ValidationResult
        +apply(cart) DiscountResult
        +incrementUsage() void
        +isExpired() boolean
        +isExhausted() boolean
    }

    Cart "1" --> "*" CartItem : contains
    Cart "1" --> "1" CartTotal : summarises
    Cart "1" --> "0..1" Coupon : applies
```

---

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
        +getTimeline() List~OrderMilestone~
        +requestReturn(lineItemIds) ReturnRequest
    }

    class OrderLineItem {
        -UUID lineItemId
        -UUID orderId
        -UUID variantId
        -String productTitle
        -String variantLabel
        -String sku
        -String imageUrl
        -Integer quantity
        -Money unitPrice
        -Money lineTotal
        -Boolean isReturnable
        +calculateLineTotal() Money
        +isEligibleForReturn() boolean
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

---

## Product and Inventory Context

```mermaid
classDiagram
    class Category {
        -UUID categoryId
        -UUID parentId
        -String name
        -String slug
        -String description
        -String imageUrl
        -Integer displayOrder
        -Boolean returnable
        -Status status
        -Timestamp createdAt
        +addChild(category) void
        +getSubcategories() List~Category~
        +getProducts(filters) List~Product~
        +archive() void
    }

    class Product {
        -UUID productId
        -UUID categoryId
        -String title
        -String slug
        -String description
        -String shortDescription
        -Money basePrice
        -String currency
        -JSONB images
        -JSONB specifications
        -Decimal avgRating
        -Integer reviewCount
        -Status status
        -Timestamp createdAt
        -Timestamp updatedAt
        +addVariant(data) ProductVariant
        +removeVariant(variantId) void
        +archive() void
        +publish() void
        +isAvailable() boolean
        +getPriceRange() PriceRange
    }

    class ProductVariant {
        -UUID variantId
        -UUID productId
        -String sku
        -String name
        -JSONB attributes
        -Money mrp
        -Money sellingPrice
        -Money costPrice
        -Integer weightGrams
        -JSONB dimensions
        -Boolean isDefault
        -Status status
        -Timestamp createdAt
        +effectivePrice() Money
        +getDiscountPercent() Decimal
        +getAvailableStock() Integer
    }

    class Inventory {
        -UUID inventoryId
        -UUID variantId
        -UUID warehouseId
        -Integer quantityOnHand
        -Integer quantityReserved
        -Integer lowStockThreshold
        -Integer reorderLevel
        -Integer reorderQuantity
        -Timestamp lastRestockedAt
        -Timestamp updatedAt
        +availableQuantity() Integer
        +reserve(qty, ttl) InventoryReservation
        +release(qty) void
        +adjust(qty, reason) void
        +deduct(qty) void
        +restock(qty) void
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

---

## Fulfillment Context

```mermaid
classDiagram
    class FulfillmentTask {
        -UUID taskId
        -UUID orderId
        -UUID warehouseId
        -UUID assignedStaffId
        -FulfillmentStatus status
        -Timestamp createdAt
        -Timestamp startedAt
        -Timestamp completedAt
        +start() void
        +scanItem(sku, qty) PickItem
        +flagMismatch(sku, expected, actual) void
        +completePicking() void
        +startPacking(dimensions, weight) void
        +completePacking() PackingSlip
    }

    class PickItem {
        -UUID pickItemId
        -UUID taskId
        -UUID variantId
        -String sku
        -Integer expectedQty
        -Integer scannedQty
        -String warehouseBin
        -PickStatus status
        +scan(barcode) void
        +isMismatch() boolean
    }

    class PackingSlip {
        -UUID slipId
        -UUID taskId
        -UUID orderId
        -String pdfS3Key
        -Timestamp generatedAt
        +generate() void
        +getDownloadUrl(expiry) String
    }

    class DeliveryManifest {
        -UUID manifestId
        -UUID warehouseId
        -UUID deliveryZoneId
        -Date date
        -ManifestStatus status
        -Integer itemCount
        -Timestamp createdAt
        -Timestamp sealedAt
        -Timestamp dispatchedAt
        +addTask(taskId) void
        +seal() void
        +dispatch() void
        +getTasks() List~FulfillmentTask~
    }

    FulfillmentTask "1" --> "*" PickItem : contains
    FulfillmentTask "1" --> "1" PackingSlip : generates
    DeliveryManifest "*" --> "*" FulfillmentTask : bundles
```

---

## Delivery and POD Context

```mermaid
classDiagram
    class DeliveryAssignment {
        -UUID assignmentId
        -UUID orderId
        -UUID staffId
        -UUID deliveryZoneId
        -UUID manifestId
        -Timestamp scheduledWindowStart
        -Timestamp scheduledWindowEnd
        -Integer attemptCount
        -Integer maxAttempts
        -AssignmentStatus status
        -String failureReason
        -Timestamp createdAt
        -Timestamp pickedUpAt
        -Timestamp completedAt
        +recordPickup() void
        +startDelivery() void
        +recordFailure(reason) void
        +complete(podId) void
        +canRetry() boolean
        +reschedule(windowStart, windowEnd) void
        +returnToWarehouse(reason) void
    }

    class ProofOfDelivery {
        -UUID podId
        -UUID orderId
        -UUID assignmentId
        -UUID staffId
        -String signatureS3Key
        -List~String~ photoS3Keys
        -String recipientName
        -String deliveryNotes
        -Float latitude
        -Float longitude
        -Timestamp capturedAt
        -Timestamp uploadedAt
        +isComplete() boolean
        +getSignatureUrl(expiry) String
        +getPhotoUrls(expiry) List~String~
        +hasLocation() boolean
    }

    class DeliveryZone {
        -UUID zoneId
        -String name
        -List~String~ postalCodes
        -Money deliveryFee
        -Money minOrderValue
        -Duration slaTargetHours
        -Integer maxAttempts
        -Boolean isActive
        -Timestamp createdAt
        +containsPostalCode(code) boolean
        +activate() void
        +deactivate() void
        +addPostalCode(code) void
        +removePostalCode(code) void
        +getActiveAssignments() List~DeliveryAssignment~
    }

    class Staff {
        -UUID staffId
        -String name
        -String email
        -String phone
        -String passwordHash
        -StaffRole role
        -UUID warehouseId
        -UUID deliveryZoneId
        -Boolean isActive
        -Timestamp createdAt
        -Timestamp updatedAt
        +assignToZone(zoneId) void
        +assignToWarehouse(whId) void
        +deactivate() void
        +activate() void
        +getActiveAssignments() List~DeliveryAssignment~
        +getPerformanceStats(period) StaffPerformance
    }

    DeliveryAssignment "*" --> "1" Staff : assigned to
    DeliveryAssignment "*" --> "1" DeliveryZone : within
    DeliveryAssignment "1" --> "0..1" ProofOfDelivery : completed with
```

---

## Payment Context

```mermaid
classDiagram
    class PaymentTransaction {
        -UUID paymentId
        -UUID orderId
        -Money amount
        -String currency
        -String gatewayName
        -String gatewayOrderId
        -String gatewayRef
        -PaymentStatus status
        -String idempotencyKey
        -JSONB gatewayResponse
        -String failureReason
        -Timestamp createdAt
        -Timestamp authorisedAt
        -Timestamp capturedAt
        -Timestamp failedAt
        -Timestamp updatedAt
        +authorise() AuthResult
        +capture() CaptureResult
        +refund(amount) RefundRecord
        +canRefund() boolean
        +totalRefunded() Money
        +getStatus() PaymentStatus
    }

    class RefundRecord {
        -UUID refundId
        -UUID paymentId
        -UUID orderId
        -UUID returnId
        -Money amount
        -String reason
        -String gatewayRef
        -RefundStatus status
        -JSONB gatewayResponse
        -Timestamp createdAt
        -Timestamp processedAt
        -Timestamp failedAt
        +isCompleted() boolean
        +process() RefundResult
        +getStatus() RefundStatus
    }

    class PaymentGatewayAdapter {
        <<interface>>
        +createOrder(amount, currency) GatewayOrder
        +verifyPayment(paymentId) VerifyResult
        +capturePayment(paymentId) CaptureResult
        +refundPayment(paymentId, amount) RefundResult
    }

    class RazorpayAdapter {
        -String apiKey
        -String apiSecret
        +createOrder(amount, currency) GatewayOrder
        +verifyPayment(paymentId) VerifyResult
        +capturePayment(paymentId) CaptureResult
        +refundPayment(paymentId, amount) RefundResult
    }

    class StripeAdapter {
        -String apiKey
        +createOrder(amount, currency) GatewayOrder
        +verifyPayment(paymentId) VerifyResult
        +capturePayment(paymentId) CaptureResult
        +refundPayment(paymentId, amount) RefundResult
    }

    class CashOnDeliveryAdapter {
        +createOrder(amount, currency) GatewayOrder
        +verifyPayment(paymentId) VerifyResult
        +capturePayment(paymentId) CaptureResult
        +refundPayment(paymentId, amount) RefundResult
    }

    PaymentTransaction "1" --> "*" RefundRecord : refunds
    PaymentGatewayAdapter <|.. RazorpayAdapter
    PaymentGatewayAdapter <|.. StripeAdapter
    PaymentGatewayAdapter <|.. CashOnDeliveryAdapter
```

---

## Return Context

```mermaid
classDiagram
    class ReturnRequest {
        -UUID returnId
        -UUID orderId
        -UUID customerId
        -List~UUID~ lineItemIds
        -String reasonCode
        -String reasonDescription
        -JSONB evidenceS3Keys
        -ReturnStatus status
        -String inspectionNotes
        -String inspectionResult
        -Money refundAmount
        -UUID refundId
        -Timestamp createdAt
        -Timestamp resolvedAt
        +isEligible(order) boolean
        +assignPickup(staffId) ReturnPickup
        +recordInspection(result, notes) void
        +calculateRefund(lineItems) Money
        +approve(refundAmount) void
        +reject(reason) void
        +partiallyAccept(acceptedItems, refundAmount) void
    }

    class ReturnPickup {
        -UUID pickupId
        -UUID returnId
        -UUID staffId
        -PickupStatus status
        -String conditionNotes
        -List~String~ photoS3Keys
        -Timestamp scheduledAt
        -Timestamp collectedAt
        +confirmCollection() void
        +uploadPhotos(s3Keys) void
        +recordCondition(notes) void
    }

    ReturnRequest "1" --> "0..1" ReturnPickup : pickup
```

---

## Notification Context

```mermaid
classDiagram
    class NotificationTemplate {
        -UUID templateId
        -String name
        -String eventType
        -NotificationChannel channel
        -String subjectTemplate
        -String bodyTemplate
        -Boolean isActive
        -Integer version
        -Timestamp createdAt
        -Timestamp updatedAt
        +render(variables) RenderedNotification
        +publish() void
        +rollback() void
    }

    class NotificationRecord {
        -UUID recordId
        -UUID recipientId
        -String recipientType
        -NotificationChannel channel
        -String eventType
        -UUID templateId
        -String subject
        -String body
        -NotificationStatus status
        -String externalRef
        -String failureReason
        -Integer retryCount
        -Timestamp createdAt
        -Timestamp sentAt
        -Timestamp deliveredAt
        +markSent(externalRef) void
        +markDelivered() void
        +markFailed(reason) void
        +retry() void
    }

    class NotificationQueue {
        -String queueArn
        -String dlqArn
        +enqueue(event, recipient, data) void
        +process() void
        +retry(recordId) void
    }

    NotificationTemplate "1" --> "*" NotificationRecord : instantiates
    NotificationQueue ..> NotificationRecord : processes
```

---

## Admin and Audit Context

```mermaid
classDiagram
    class AuditLog {
        -UUID logId
        -UUID actorId
        -String actorRole
        -String action
        -String resourceType
        -UUID resourceId
        -JSONB beforeValue
        -JSONB afterValue
        -String ipAddress
        -String correlationId
        -Timestamp timestamp
    }

    class PlatformConfig {
        -UUID configId
        -String key
        -String value
        -ConfigDataType dataType
        -String description
        -UUID updatedBy
        -Timestamp updatedAt
        -Integer version
        +get(key) String
        +set(key, value, actorId) void
        +getHistory(key) List~PlatformConfig~
        +rollback(key, version) void
    }

    class Warehouse {
        -UUID warehouseId
        -String name
        -String addressLine
        -String city
        -String state
        -String postalCode
        -String contactName
        -String contactPhone
        -Boolean isActive
        -Timestamp createdAt
        +activate() void
        +deactivate() void
        +getStaff() List~Staff~
        +getInventory() List~Inventory~
    }

    class StaffPerformance {
        -UUID staffId
        -String period
        -Integer tasksCompleted
        -Integer deliveriesAttempted
        -Integer deliveriesSuccessful
        -Integer failedDeliveries
        -Integer returnPickups
        -Duration avgDeliveryTime
        -Decimal performanceScore
        +calculate() void
        +getReport() PerformanceReport
    }

    AuditLog ..> PlatformConfig : records changes to
    Warehouse "1" --> "*" Staff : employs
    Staff "1" --> "*" StaffPerformance : evaluated by
```

---

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
        REFUNDED
    }

    class StaffRole {
        <<enumeration>>
        WAREHOUSE_STAFF
        DELIVERY_STAFF
        OPERATIONS_MANAGER
        FINANCE
        ADMIN
    }

    class AssignmentStatus {
        <<enumeration>>
        ASSIGNED
        PICKED_UP
        OUT_FOR_DELIVERY
        DELIVERED
        FAILED
        RETURNED_TO_WAREHOUSE
    }

    class DiscountType {
        <<enumeration>>
        PERCENTAGE
        FIXED
        FREE_SHIPPING
    }

    class NotificationChannel {
        <<enumeration>>
        EMAIL
        SMS
        PUSH
    }

    class NotificationStatus {
        <<enumeration>>
        PENDING
        SENT
        DELIVERED
        FAILED
        BOUNCED
    }

    class FulfillmentStatus {
        <<enumeration>>
        PENDING
        IN_PROGRESS
        PICKED
        PACKED
        DISPATCHED
    }

    class ManifestStatus {
        <<enumeration>>
        DRAFT
        SEALED
        DISPATCHED
    }

    class ConfigDataType {
        <<enumeration>>
        STRING
        NUMBER
        BOOLEAN
        JSON
    }
```
