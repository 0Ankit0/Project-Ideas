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
