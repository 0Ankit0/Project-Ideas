# C4 Code Diagram

## Overview

C4 Code-level diagrams showing the internal class structure and key code-level relationships for the most critical service implementations.

## Order Service — Code Level

```mermaid
classDiagram
    class OrderHandler {
        <<Lambda Handler>>
        -orderService: IOrderService
        -idempotencyGuard: IIdempotencyGuard
        +handleCheckout(event): APIResponse
        +handleCancel(event): APIResponse
        +handleGetOrder(event): APIResponse
        +handleListOrders(event): APIResponse
        +handleUpdateAddress(event): APIResponse
    }

    class IOrderService {
        <<Interface>>
        +checkout(cmd: CheckoutCommand): Order
        +cancel(orderId: UUID, reason: string): Order
        +getById(orderId: UUID, customerId: UUID): Order
        +listByCustomer(customerId: UUID, cursor: string): Page~Order~
        +updateAddress(orderId: UUID, addressId: UUID): Order
    }

    class OrderServiceImpl {
        -orderRepo: IOrderRepository
        -inventoryClient: IInventoryClient
        -paymentClient: IPaymentClient
        -eventPublisher: IEventPublisher
        -milestoneWriter: IMilestoneWriter
        -priceCalculator: PriceCalculator
        -stateMachine: OrderStateMachine
        +checkout(cmd): Order
        +cancel(orderId, reason): Order
    }

    class IOrderRepository {
        <<Interface>>
        +create(order: Order): Order
        +findById(id: UUID): Order
        +findByCustomer(customerId: UUID, cursor): Page~Order~
        +updateStatus(id: UUID, status, version): Order
        +updateAddress(id: UUID, addressId): Order
    }

    class PostgresOrderRepository {
        -pool: Pool
        +create(order): Order
        +findById(id): Order
        +updateStatus(id, status, version): Order
    }

    class OrderStateMachine {
        -transitions: Map~string, string[]~
        +canTransition(from, to): boolean
        +validate(from, to): void
        +getAllowedTransitions(current): string[]
    }

    class PriceCalculator {
        +calculate(items, taxRate, shippingFee, discount): OrderTotal
        +validateCoupon(coupon, subtotal): boolean
    }

    class IEventPublisher {
        <<Interface>>
        +publish(eventType: string, payload: object): void
    }

    class EventBridgePublisher {
        -client: EventBridgeClient
        -busName: string
        +publish(eventType, payload): void
    }

    class IIdempotencyGuard {
        <<Interface>>
        +check(key: string): CachedResponse
        +store(key: string, response: object, ttl: number): void
    }

    class RedisIdempotencyGuard {
        -redis: Redis
        +check(key): CachedResponse
        +store(key, response, ttl): void
    }

    OrderHandler --> IOrderService
    OrderHandler --> IIdempotencyGuard
    IOrderService <|.. OrderServiceImpl
    OrderServiceImpl --> IOrderRepository
    OrderServiceImpl --> OrderStateMachine
    OrderServiceImpl --> PriceCalculator
    OrderServiceImpl --> IEventPublisher
    IOrderRepository <|.. PostgresOrderRepository
    IEventPublisher <|.. EventBridgePublisher
    IIdempotencyGuard <|.. RedisIdempotencyGuard
```

## Delivery Service — Code Level

```mermaid
classDiagram
    class DeliveryController {
        <<Fargate Controller>>
        -assignmentService: IAssignmentService
        -podService: IPODService
        -statusService: IStatusService
        +getAssignments(req): Response
        +updateStatus(req): Response
        +submitPOD(req): Response
        +recordFailure(req): Response
    }

    class IAssignmentService {
        <<Interface>>
        +assign(orderId, zoneId): Assignment
        +reassign(assignmentId, newStaffId): Assignment
        +getByStaff(staffId): Assignment[]
    }

    class AssignmentServiceImpl {
        -assignmentRepo: IAssignmentRepository
        -staffRepo: IStaffRepository
        -eventPublisher: IEventPublisher
        +assign(orderId, zoneId): Assignment
        +reassign(assignmentId, newStaffId): Assignment
    }

    class IPODService {
        <<Interface>>
        +submit(assignmentId, signature, photo, notes): POD
        +getByOrder(orderId): POD
    }

    class PODServiceImpl {
        -podRepo: IPODRepository
        -s3Client: IS3Client
        -assignmentRepo: IAssignmentRepository
        -eventPublisher: IEventPublisher
        +submit(assignmentId, signature, photo, notes): POD
    }

    class IStatusService {
        <<Interface>>
        +updateStatus(assignmentId, newStatus): Assignment
        +recordFailure(assignmentId, reason): Assignment
    }

    class StatusServiceImpl {
        -assignmentRepo: IAssignmentRepository
        -orderClient: IOrderClient
        -milestoneWriter: IMilestoneWriter
        -eventPublisher: IEventPublisher
        -rescheduleEngine: IRescheduleEngine
        +updateStatus(assignmentId, newStatus): Assignment
        +recordFailure(assignmentId, reason): Assignment
    }

    class IS3Client {
        <<Interface>>
        +upload(key, body, encryption): S3Result
        +generatePresignedUrl(key, expiry): string
    }

    DeliveryController --> IAssignmentService
    DeliveryController --> IPODService
    DeliveryController --> IStatusService
    IAssignmentService <|.. AssignmentServiceImpl
    IPODService <|.. PODServiceImpl
    IStatusService <|.. StatusServiceImpl
    PODServiceImpl --> IS3Client
```

## Payment Service — Code Level

```mermaid
classDiagram
    class PaymentHandler {
        <<Lambda Handler>>
        -captureService: ICaptureService
        -refundService: IRefundService
        +handleCapture(event): APIResponse
        +handleRefund(event): APIResponse
        +handleReconciliation(event): APIResponse
    }

    class ICaptureService {
        <<Interface>>
        +capture(orderId, amount, method, idempKey): PaymentTransaction
    }

    class CaptureServiceImpl {
        -paymentRepo: IPaymentRepository
        -gatewayRouter: IGatewayRouter
        -eventPublisher: IEventPublisher
        +capture(orderId, amount, method, idempKey): PaymentTransaction
    }

    class IGatewayRouter {
        <<Interface>>
        +route(request: GatewayRequest): GatewayResponse
    }

    class FailoverGatewayRouter {
        -primary: IPaymentGateway
        -secondary: IPaymentGateway
        -circuitBreaker: CircuitBreaker
        +route(request): GatewayResponse
    }

    class IPaymentGateway {
        <<Interface>>
        +authorize(amount, token): AuthResult
        +capture(authId): CaptureResult
        +refund(captureId, amount): RefundResult
    }

    class StripeGateway {
        -client: Stripe
        +authorize(amount, token): AuthResult
        +capture(authId): CaptureResult
        +refund(captureId, amount): RefundResult
    }

    PaymentHandler --> ICaptureService
    ICaptureService <|.. CaptureServiceImpl
    CaptureServiceImpl --> IGatewayRouter
    IGatewayRouter <|.. FailoverGatewayRouter
    FailoverGatewayRouter --> IPaymentGateway
    IPaymentGateway <|.. StripeGateway
```
