# C4 Code Diagram - Slot Booking System

> **Platform Independence**: C4 Level 4 showing class-level design (optional detail level).

---

## Overview

The C4 Code Diagram (Level 4) provides the most detailed view, showing the internal structure of components at the code/class level.

---

## Booking Service Code Structure

```mermaid
classDiagram
    class BookingController {
        -bookingService: IBookingService
        +createBooking(dto: CreateBookingDto)
        +getBooking(id: string)
        +cancelBooking(id: string)
        +getUserBookings(userId: string)
    }
    
    class IBookingService {
        <<interface>>
        +create(dto: CreateBookingDto): Booking
        +findById(id: string): Booking
        +cancel(id: string, reason: string): void
        +findByUser(userId: string): Booking[]
    }
    
    class BookingService {
        -slotService: ISlotService
        -paymentService: IPaymentService
        -notificationService: INotificationService
        -bookingRepo: IBookingRepository
        +create(dto: CreateBookingDto): Booking
        +findById(id: string): Booking
        +cancel(id: string, reason: string): void
    }
    
    class IBookingRepository {
        <<interface>>
        +save(booking: Booking): Booking
        +findById(id: string): Booking
        +update(id: string, data: Partial): Booking
    }
    
    class BookingRepository {
        -db: DatabaseConnection
        +save(booking: Booking): Booking
        +findById(id: string): Booking
    }
    
    class Booking {
        +id: string
        +userId: string
        +resourceId: string
        +status: BookingStatus
        +totalAmount: Money
        +confirm(): void
        +cancel(reason: string): void
    }
    
    class BookingStatus {
        <<enumeration>>
        PENDING
        CONFIRMED
        CANCELLED
        COMPLETED
    }
    
    BookingController --> IBookingService
    BookingService ..|> IBookingService
    BookingService --> IBookingRepository
    BookingService --> ISlotService
    BookingService --> IPaymentService
    BookingRepository ..|> IBookingRepository
    Booking --> BookingStatus
```

---

## Slot Management Code Structure

```mermaid
classDiagram
    class ISlotService {
        <<interface>>
        +getAvailable(resourceId, date): Slot[]
        +lock(slotIds, userId, ttl): boolean
        +unlock(slotIds): void
        +book(slotIds, bookingId): void
        +release(slotIds): void
    }
    
    class SlotService {
        -slotRepo: ISlotRepository
        -cacheService: ICacheService
        -lockTTL: number
        +getAvailable(resourceId, date): Slot[]
        +lock(slotIds, userId, ttl): boolean
    }
    
    class SlotLockManager {
        -cache: ICacheService
        -lockPrefix: string
        +acquireLock(slotId, userId): boolean
        +releaseLock(slotId): void
        +isLocked(slotId): boolean
        +refreshLock(slotId, userId): boolean
    }
    
    class Slot {
        +id: string
        +resourceId: string
        +startTime: DateTime
        +endTime: DateTime
        +price: Money
        +status: SlotStatus
        +isAvailable(): boolean
    }
    
    class SlotStatus {
        <<enumeration>>
        AVAILABLE
        LOCKED
        BOOKED
        BLOCKED
    }
    
    SlotService ..|> ISlotService
    SlotService --> SlotLockManager
    SlotService --> ISlotRepository
    Slot --> SlotStatus
```

---

## Payment Processing Code Structure

```mermaid
classDiagram
    class IPaymentService {
        <<interface>>
        +initiate(booking, method): PaymentIntent
        +process(paymentId): PaymentResult
        +refund(paymentId, amount): RefundResult
    }
    
    class PaymentService {
        -gatewayFactory: PaymentGatewayFactory
        -paymentRepo: IPaymentRepository
        +initiate(booking, method): PaymentIntent
        +process(paymentId): PaymentResult
    }
    
    class PaymentGatewayFactory {
        -gateways: Map~string, IPaymentGateway~
        +getGateway(type: string): IPaymentGateway
        +registerGateway(type, gateway): void
    }
    
    class IPaymentGateway {
        <<interface>>
        +charge(amount, details): GatewayResponse
        +refund(txnId, amount): GatewayResponse
        +verify(txnId): GatewayResponse
    }
    
    class StripeGateway {
        -stripeClient: Stripe
        +charge(amount, details): GatewayResponse
        +refund(txnId, amount): GatewayResponse
    }
    
    class PayPalGateway {
        -paypalClient: PayPal
        +charge(amount, details): GatewayResponse
    }
    
    class Payment {
        +id: string
        +bookingId: string
        +amount: Money
        +status: PaymentStatus
        +gatewayTxnId: string
    }
    
    PaymentService ..|> IPaymentService
    PaymentService --> PaymentGatewayFactory
    PaymentGatewayFactory --> IPaymentGateway
    StripeGateway ..|> IPaymentGateway
    PayPalGateway ..|> IPaymentGateway
```

---

## Notification Service Code Structure

```mermaid
classDiagram
    class INotificationService {
        <<interface>>
        +send(userId, type, data): void
        +sendBulk(userIds, type, data): void
        +scheduleReminder(booking): void
    }
    
    class NotificationService {
        -providers: Map~Channel, INotificationProvider~
        -preferenceRepo: IPreferenceRepository
        -templateEngine: ITemplateEngine
        +send(userId, type, data): void
    }
    
    class NotificationDispatcher {
        -queue: IMessageQueue
        +dispatch(notification): void
        +processQueue(): void
    }
    
    class INotificationProvider {
        <<interface>>
        +send(recipient, content): DeliveryResult
    }
    
    class EmailProvider {
        -client: SendGridClient
        +send(recipient, content): DeliveryResult
    }
    
    class SMSProvider {
        -client: TwilioClient
        +send(recipient, content): DeliveryResult
    }
    
    class PushProvider {
        -fcmClient: FCMClient
        +send(recipient, content): DeliveryResult
    }
    
    class ITemplateEngine {
        <<interface>>
        +render(template, data): RenderedContent
    }
    
    NotificationService ..|> INotificationService
    NotificationService --> NotificationDispatcher
    NotificationService --> INotificationProvider
    NotificationService --> ITemplateEngine
    EmailProvider ..|> INotificationProvider
    SMSProvider ..|> INotificationProvider
    PushProvider ..|> INotificationProvider
```

---

## Value Objects

```mermaid
classDiagram
    class Money {
        -amount: decimal
        -currency: string
        +add(other: Money): Money
        +subtract(other: Money): Money
        +multiply(factor: number): Money
        +equals(other: Money): boolean
        +format(): string
    }
    
    class TimeRange {
        -start: DateTime
        -end: DateTime
        +duration(): Duration
        +overlaps(other: TimeRange): boolean
        +contains(time: DateTime): boolean
    }
    
    class Address {
        -street: string
        -city: string
        -country: string
        -postalCode: string
        +format(): string
    }
    
    class Coordinates {
        -latitude: number
        -longitude: number
        +distanceTo(other: Coordinates): number
        +isValid(): boolean
    }
```

---

## Code Module Summary

| Module | Classes | Interfaces | Purpose |
|--------|---------|------------|---------|
| Booking | 3 | 2 | Booking lifecycle |
| Slot | 4 | 2 | Slot management |
| Payment | 5 | 3 | Payment processing |
| Notification | 6 | 3 | Multi-channel notifications |
| Domain | 10+ | - | Domain entities, value objects |
