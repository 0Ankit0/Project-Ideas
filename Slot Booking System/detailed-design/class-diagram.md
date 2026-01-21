# Class Diagram - Slot Booking System

> **Platform Independence**: Class diagrams use language-agnostic notation adaptable to any OOP language.

---

## Overview

The Class Diagram shows the detailed structure of the system including classes, their attributes, methods, and relationships.

---

## Core Domain Classes

```mermaid
classDiagram
    class User {
        -String userId
        -String email
        -String phone
        -String passwordHash
        -String name
        -UserRole role
        -UserStatus status
        -DateTime createdAt
        -DateTime lastLoginAt
        +register(email, password, name)
        +login(email, password)
        +updateProfile(data)
        +changePassword(oldPwd, newPwd)
        +requestPasswordReset()
        +verifyEmail(token)
    }
    
    class UserRole {
        <<enumeration>>
        GUEST
        USER
        PROVIDER
        ADMIN
    }
    
    class UserStatus {
        <<enumeration>>
        PENDING
        ACTIVE
        SUSPENDED
        DELETED
    }
    
    class Provider {
        -String providerId
        -String userId
        -String businessName
        -String description
        -ProviderStatus status
        -BankDetails bankDetails
        -DateTime verifiedAt
        +applyForProvider(businessInfo)
        +updateBankDetails(details)
        +getEarnings(dateRange)
        +getResources()
        +getBookings(filters)
    }
    
    class ProviderStatus {
        <<enumeration>>
        PENDING
        APPROVED
        REJECTED
        SUSPENDED
    }
    
    User "1" --> "0..1" Provider : becomes
    User --> UserRole
    User --> UserStatus
    Provider --> ProviderStatus
```

---

## Resource and Slot Classes

```mermaid
classDiagram
    class Resource {
        -String resourceId
        -String providerId
        -String name
        -String description
        -Category category
        -Location location
        -List~Image~ images
        -List~Amenity~ amenities
        -int capacity
        -Money basePrice
        -ResourceStatus status
        -DateTime createdAt
        +create(data)
        +update(data)
        +addImage(image)
        +removeImage(imageId)
        +setAvailability(schedule)
        +getPriceForSlot(slot)
        +getAvailableSlots(date)
        +activate()
        +deactivate()
    }
    
    class ResourceStatus {
        <<enumeration>>
        DRAFT
        PENDING_REVIEW
        ACTIVE
        INACTIVE
    }
    
    class Category {
        -String categoryId
        -String name
        -String icon
        -Category parent
    }
    
    class Location {
        -String address
        -String city
        -String country
        -double latitude
        -double longitude
        +format()
        +distanceTo(other)
    }
    
    class Image {
        -String imageId
        -String url
        -int order
        -boolean isPrimary
    }
    
    class Amenity {
        -String amenityId
        -String name
        -String icon
    }
    
    class Schedule {
        -String scheduleId
        -String resourceId
        -List~TimeSlotTemplate~ weeklyTemplate
        -List~SpecialDate~ specialDates
        -Duration slotDuration
        -Duration bufferTime
        +generateSlots(dateRange)
        +blockDate(date, reason)
        +unblockDate(date)
    }
    
    class TimeSlotTemplate {
        -DayOfWeek dayOfWeek
        -Time startTime
        -Time endTime
        -boolean isActive
    }
    
    class Slot {
        -String slotId
        -String resourceId
        -DateTime startTime
        -DateTime endTime
        -Money price
        -SlotStatus status
        +isAvailable()
        +lock(userId, ttl)
        +unlock()
        +book(bookingId)
        +release()
    }
    
    class SlotStatus {
        <<enumeration>>
        AVAILABLE
        LOCKED
        BOOKED
        BLOCKED
    }
    
    Resource --> ResourceStatus
    Resource --> Category
    Resource --> Location
    Resource "1" --> "*" Image
    Resource "*" --> "*" Amenity
    Resource "1" --> "1" Schedule
    Resource "1" --> "*" Slot
    Schedule "1" --> "*" TimeSlotTemplate
    Slot --> SlotStatus
```

---

## Booking and Payment Classes

```mermaid
classDiagram
    class Booking {
        -String bookingId
        -String userId
        -String resourceId
        -List~Slot~ slots
        -BookingStatus status
        -String notes
        -Money totalAmount
        -Money discountAmount
        -String promoCodeUsed
        -DateTime bookedAt
        -DateTime cancelledAt
        -String cancellationReason
        +create(userId, slots)
        +confirm(paymentId)
        +cancel(reason)
        +reschedule(newSlots)
        +getDetails()
        +generateConfirmation()
    }
    
    class BookingStatus {
        <<enumeration>>
        PENDING
        CONFIRMED
        CANCELLED
        COMPLETED
        NO_SHOW
    }
    
    class RecurringBooking {
        -String recurringId
        -String userId
        -String resourceId
        -RecurrencePattern pattern
        -DateTime startDate
        -DateTime endDate
        -List~Booking~ instances
        +generateInstances()
        +cancelSeries()
        +cancelInstance(date)
        +modifyPattern(newPattern)
    }
    
    class RecurrencePattern {
        -Frequency frequency
        -int interval
        -List~DayOfWeek~ daysOfWeek
        -int occurrences
    }
    
    class Payment {
        -String paymentId
        -String bookingId
        -String userId
        -Money amount
        -PaymentMethod method
        -PaymentStatus status
        -String gatewayTransactionId
        -DateTime paidAt
        -Map metadata
        +initiate(amount, method)
        +process()
        +verify()
        +getReceipt()
    }
    
    class PaymentStatus {
        <<enumeration>>
        PENDING
        PROCESSING
        COMPLETED
        FAILED
        REFUNDED
        PARTIALLY_REFUNDED
    }
    
    class PaymentMethod {
        <<enumeration>>
        CARD
        WALLET
        UPI
        BANK_TRANSFER
    }
    
    class Refund {
        -String refundId
        -String paymentId
        -Money amount
        -RefundReason reason
        -RefundStatus status
        -DateTime refundedAt
        +initiate(amount, reason)
        +process()
    }
    
    class PromoCode {
        -String code
        -String description
        -DiscountType discountType
        -decimal discountValue
        -Money minOrderAmount
        -int maxUses
        -int usedCount
        -DateTime validFrom
        -DateTime validTo
        -boolean isActive
        +validate(booking)
        +apply(booking)
        +incrementUsage()
    }
    
    Booking --> BookingStatus
    Booking "1" --> "1..*" Slot
    Booking "1" --> "0..1" Payment
    Booking "*" --> "0..1" PromoCode
    RecurringBooking "1" --> "*" Booking
    Payment --> PaymentStatus
    Payment --> PaymentMethod
    Payment "1" --> "0..1" Refund
```

---

## Review and Notification Classes

```mermaid
classDiagram
    class Review {
        -String reviewId
        -String userId
        -String resourceId
        -String bookingId
        -int rating
        -String comment
        -List~String~ imageUrls
        -DateTime createdAt
        -String providerResponse
        -DateTime respondedAt
        +create(rating, comment)
        +addImages(images)
        +respond(response)
        +markHelpful(userId)
        +report(reason)
    }
    
    class Notification {
        -String notificationId
        -String userId
        -NotificationType type
        -String title
        -String body
        -Map data
        -List~NotificationChannel~ channels
        -NotificationStatus status
        -DateTime sentAt
        -DateTime readAt
        +send()
        +markAsRead()
        +retry()
    }
    
    class NotificationType {
        <<enumeration>>
        BOOKING_CONFIRMED
        BOOKING_CANCELLED
        BOOKING_REMINDER
        PAYMENT_RECEIVED
        REFUND_PROCESSED
        REVIEW_REQUEST
        PROVIDER_APPROVED
    }
    
    class NotificationChannel {
        <<enumeration>>
        EMAIL
        SMS
        PUSH
        IN_APP
    }
    
    class NotificationPreference {
        -String userId
        -Map~NotificationType, List~NotificationChannel~~ preferences
        -Time quietStart
        -Time quietEnd
        +updatePreference(type, channels)
        +isQuietTime()
        +getChannelsFor(type)
    }
    
    Review --> User
    Review --> Resource
    Notification --> NotificationType
    Notification --> NotificationChannel
    NotificationPreference --> NotificationType
    NotificationPreference --> NotificationChannel
```

---

## Service Classes

```mermaid
classDiagram
    class BookingService {
        -BookingRepository bookingRepo
        -SlotService slotService
        -PaymentService paymentService
        -NotificationService notificationService
        +createBooking(userId, slotIds, promoCode)
        +confirmBooking(bookingId, paymentId)
        +cancelBooking(bookingId, reason)
        +rescheduleBooking(bookingId, newSlotIds)
        +getBookingHistory(userId, filters)
        +getUpcomingBookings(userId)
    }
    
    class SlotService {
        -SlotRepository slotRepo
        -CacheService cache
        +generateSlots(resourceId, dateRange)
        +getAvailableSlots(resourceId, date)
        +lockSlot(slotId, userId, ttl)
        +unlockSlot(slotId)
        +bookSlot(slotId, bookingId)
        +releaseSlot(slotId)
    }
    
    class PaymentService {
        -PaymentGateway gateway
        -PaymentRepository paymentRepo
        +initiatePayment(booking, method)
        +processPayment(paymentId)
        +verifyPayment(gatewayTxnId)
        +initiateRefund(paymentId, amount, reason)
        +processRefund(refundId)
    }
    
    class PricingService {
        -PricingRuleRepository ruleRepo
        -PromoCodeRepository promoRepo
        +calculatePrice(resource, slots)
        +applyPromoCode(booking, code)
        +validatePromoCode(code, booking)
        +getPricingRules(resourceId)
    }
    
    class NotificationService {
        -EmailProvider emailProvider
        -SMSProvider smsProvider
        -PushProvider pushProvider
        -NotificationRepository notifRepo
        +send(userId, type, data)
        +sendBulk(userIds, type, data)
        +scheduleReminder(booking)
        +getPreferences(userId)
        +updatePreferences(userId, prefs)
    }
    
    class SearchService {
        -SearchIndex searchIndex
        +searchResources(query, filters)
        +indexResource(resource)
        +removeFromIndex(resourceId)
        +getSuggestions(prefix)
    }
    
    BookingService --> SlotService
    BookingService --> PaymentService
    BookingService --> NotificationService
    BookingService --> PricingService
```

---

## Class Relationships Summary

| Relationship | Classes | Type | Cardinality |
|--------------|---------|------|-------------|
| User → Provider | User, Provider | Association | 1 to 0..1 |
| Provider → Resource | Provider, Resource | Composition | 1 to many |
| Resource → Slot | Resource, Slot | Composition | 1 to many |
| Slot → Booking | Slot, Booking | Association | many to 0..1 |
| Booking → Payment | Booking, Payment | Association | 1 to 0..1 |
| User → Review | User, Review | Association | 1 to many |
| Resource → Review | Resource, Review | Association | 1 to many |
