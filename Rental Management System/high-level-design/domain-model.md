# Domain Model

## Overview
The domain model shows the key business entities and their relationships in the rental management system. The model is asset-agnostic — it applies equally to car rentals, flat rentals, gear rentals, equipment rentals, and any other rentable category.

---

## Complete Domain Model

```mermaid
erDiagram
    USER ||--o{ ASSET : owns
    USER ||--o{ BOOKING : places
    USER ||--o{ RENTAL_AGREEMENT : party_to
    USER ||--o{ PAYMENT : makes
    USER ||--o{ REVIEW : writes
    USER ||--o{ NOTIFICATION : receives
    USER ||--o{ DOCUMENT : uploads

    ASSET_CATEGORY ||--o{ ASSET : classifies
    ASSET_CATEGORY ||--o{ CATEGORY_ATTRIBUTE : defines

    ASSET ||--o{ PRICING_RULE : has
    ASSET ||--o{ AVAILABILITY_BLOCK : has
    ASSET ||--o{ BOOKING : receives
    ASSET ||--o{ ASSET_PHOTO : has
    ASSET ||--o{ DOCUMENT : has
    ASSET ||--o{ MAINTENANCE_REQUEST : subject_of
    ASSET ||--o{ REVIEW : receives
    ASSET ||--o{ ASSET_ATTRIBUTE_VALUE : has

    BOOKING ||--o{ PAYMENT : paid_by
    BOOKING ||--|| RENTAL_AGREEMENT : has
    BOOKING ||--|| SECURITY_DEPOSIT : has
    BOOKING ||--o{ CONDITION_ASSESSMENT : has
    BOOKING ||--o{ ADDITIONAL_CHARGE : incurs
    BOOKING ||--o{ INVOICE : generates
    BOOKING ||--o{ BOOKING_EVENT : emits

    RENTAL_AGREEMENT ||--o{ DOCUMENT : generates
    RENTAL_AGREEMENT ||--o{ AGREEMENT_AMENDMENT : has

    SECURITY_DEPOSIT ||--o{ DEPOSIT_DEDUCTION : has

    CONDITION_ASSESSMENT ||--o{ ASSESSMENT_ITEM : contains
    CONDITION_ASSESSMENT ||--o{ ASSESSMENT_PHOTO : has

    INVOICE ||--o{ PAYMENT : paid_by

    MAINTENANCE_REQUEST ||--o{ REQUEST_EVENT : emits
    MAINTENANCE_REQUEST ||--o{ MAINTENANCE_PHOTO : has
    MAINTENANCE_REQUEST ||--|| MAINTENANCE_COST : has

    USER_PAYOUT ||--o{ BOOKING : settles
```

---

## User Domain

```mermaid
classDiagram
    class User {
        +UUID id
        +String email
        +String phone
        +String fullName
        +String passwordHash
        +UserRole role
        +UserStatus status
        +Boolean emailVerified
        +Boolean phoneVerified
        +DateTime createdAt
        +DateTime lastLoginAt
        +register()
        +login()
        +updateProfile()
        +resetPassword()
    }

    class OwnerProfile {
        +UUID id
        +UUID userId
        +String businessName
        +String tradingName
        +OwnerVerificationStatus verificationStatus
        +Decimal commissionRate
        +String bankAccountDetails
        +DateTime verifiedAt
        +getAssets()
        +getBookings()
        +getPortfolioSummary()
    }

    class CustomerProfile {
        +UUID id
        +UUID userId
        +CustomerVerificationStatus idVerificationStatus
        +String drivingLicenceNumber
        +String passportNumber
        +Decimal outstandingBalance
        +getActiveBookings()
        +getPaymentHistory()
    }

    class StaffProfile {
        +UUID id
        +UUID userId
        +UUID ownerUserId
        +String specialisation
        +Boolean isAvailable
        +getAssignedTasks()
        +setAvailability()
    }

    class Notification {
        +UUID id
        +UUID userId
        +String eventType
        +String title
        +String body
        +Boolean isRead
        +JSON payload
        +DateTime createdAt
    }

    User "1" --> "0..1" OwnerProfile
    User "1" --> "0..1" CustomerProfile
    User "1" --> "0..1" StaffProfile
    User "1" --> "*" Notification
```

---

## Asset Domain

```mermaid
classDiagram
    class AssetCategory {
        +UUID id
        +String name
        +String slug
        +String description
        +String iconUrl
        +UUID parentCategoryId
        +Boolean isActive
        +getAttributes()
        +getAssets()
    }

    class CategoryAttribute {
        +UUID id
        +UUID categoryId
        +String name
        +String slug
        +AttributeType type
        +Boolean isRequired
        +Boolean isFilterable
        +JSON options
        +Integer displayOrder
    }

    class Asset {
        +UUID id
        +UUID ownerUserId
        +UUID categoryId
        +String name
        +String description
        +AssetStatus status
        +Boolean isPublished
        +String locationAddress
        +Decimal locationLat
        +Decimal locationLng
        +Decimal depositAmount
        +Integer minRentalDurationHours
        +Integer maxRentalDurationDays
        +Integer bookingLeadTimeHours
        +Decimal averageRating
        +Integer reviewCount
        +DateTime createdAt
        +publish()
        +unpublish()
        +checkAvailability(start, end)
        +calculatePrice(start, end)
    }

    class AssetAttributeValue {
        +UUID id
        +UUID assetId
        +UUID attributeId
        +String value
    }

    class AssetPhoto {
        +UUID id
        +UUID assetId
        +String url
        +String thumbnailUrl
        +Integer position
        +Boolean isCover
        +String caption
    }

    class PricingRule {
        +UUID id
        +UUID assetId
        +RateType rateType
        +Decimal rateAmount
        +String currency
        +Boolean isPeakRate
        +Date peakStartDate
        +Date peakEndDate
        +DayOfWeek[] peakDaysOfWeek
        +Decimal discountPercentage
        +Integer minUnitsForDiscount
        +isApplicable(period) Boolean
        +calculateCost(units) Decimal
    }

    class AvailabilityBlock {
        +UUID id
        +UUID assetId
        +AvailabilityBlockType type
        +DateTime startAt
        +DateTime endAt
        +String reason
        +UUID bookingId
        +UUID maintenanceRequestId
        +create()
        +release()
    }

    AssetCategory "1" --> "*" AssetCategory : parentOf
    AssetCategory "1" --> "*" CategoryAttribute
    AssetCategory "1" --> "*" Asset
    Asset "1" --> "*" AssetAttributeValue
    Asset "1" --> "*" AssetPhoto
    Asset "1" --> "*" PricingRule
    Asset "1" --> "*" AvailabilityBlock
```

---

## Booking Domain

```mermaid
classDiagram
    class Booking {
        +UUID id
        +String bookingNumber
        +UUID assetId
        +UUID customerUserId
        +UUID ownerUserId
        +BookingStatus status
        +DateTime rentalStartAt
        +DateTime rentalEndAt
        +DateTime actualReturnAt
        +Decimal baseFee
        +Decimal peakSurcharge
        +Decimal taxAmount
        +Decimal totalFee
        +Decimal depositAmount
        +String cancellationReason
        +DateTime cancelledAt
        +DateTime createdAt
        +confirm()
        +cancel(reason)
        +modify(newStart, newEnd)
        +initiateReturn()
        +close()
    }

    class BookingEvent {
        +UUID id
        +UUID bookingId
        +String eventType
        +String message
        +UUID actorUserId
        +JSON metadata
        +DateTime createdAt
    }

    class SecurityDeposit {
        +UUID id
        +UUID bookingId
        +Decimal amount
        +DepositStatus status
        +String gatewayRef
        +Decimal deductionTotal
        +Decimal refundAmount
        +DateTime collectedAt
        +DateTime settledAt
        +addDeduction(reason, amount, evidence)
        +processRefund()
        +getTotalDeductions()
    }

    class DepositDeduction {
        +UUID id
        +UUID depositId
        +String reason
        +Decimal amount
        +String evidenceUrl
        +DateTime createdAt
    }

    class RentalAgreement {
        +UUID id
        +UUID bookingId
        +UUID templateId
        +AgreementStatus status
        +String eSignRequestId
        +String signedDocumentUrl
        +DateTime sentAt
        +DateTime customerSignedAt
        +String customerSignatureIp
        +DateTime ownerSignedAt
        +String ownerSignatureIp
        +Integer version
        +send()
        +customerSign(ip)
        +ownerSign(ip)
        +amend(changes)
    }

    class AgreementAmendment {
        +UUID id
        +UUID agreementId
        +String reason
        +String amendedDocumentUrl
        +AgreementStatus status
        +DateTime createdAt
        +DateTime signedAt
    }

    Booking "1" --> "*" BookingEvent
    Booking "1" --> "1" SecurityDeposit
    Booking "1" --> "1" RentalAgreement
    SecurityDeposit "1" --> "*" DepositDeduction
    RentalAgreement "1" --> "*" AgreementAmendment
```

---

## Invoice & Payment Domain

```mermaid
classDiagram
    class Invoice {
        +UUID id
        +String invoiceNumber
        +UUID bookingId
        +UUID customerUserId
        +UUID ownerUserId
        +InvoiceType type
        +Decimal subtotal
        +Decimal taxAmount
        +Decimal totalAmount
        +Decimal paidAmount
        +InvoiceStatus status
        +Date dueDate
        +DateTime createdAt
        +DateTime paidAt
        +addLineItem(description, amount)
        +recordPayment(paymentId)
        +generateReceipt()
        +getOutstandingAmount()
    }

    class InvoiceLineItem {
        +UUID id
        +UUID invoiceId
        +String description
        +LineItemType type
        +Decimal amount
        +Decimal taxRate
    }

    class AdditionalCharge {
        +UUID id
        +UUID bookingId
        +AdditionalChargeType type
        +String description
        +Decimal amount
        +String evidenceUrl
        +ChargeStatus status
        +String disputeReason
        +DateTime createdAt
        +DateTime resolvedAt
        +dispute(reason)
        +approve()
        +waive()
    }

    class Payment {
        +UUID id
        +String referenceType
        +UUID referenceId
        +UUID payerUserId
        +PaymentMethod method
        +PaymentStatus status
        +Decimal amount
        +String currency
        +String gatewayRef
        +JSON gatewayResponse
        +Boolean isOffline
        +DateTime createdAt
        +DateTime confirmedAt
        +process()
        +refund()
    }

    class OwnerPayout {
        +UUID id
        +UUID ownerUserId
        +Decimal grossAmount
        +Decimal commissionAmount
        +Decimal netAmount
        +PayoutStatus status
        +String bankRef
        +String batchId
        +DateTime periodStart
        +DateTime periodEnd
        +DateTime processedAt
        +calculate()
        +process()
    }

    Invoice "1" --> "*" InvoiceLineItem
    Invoice "1" --> "*" Payment
    Booking "1" --> "*" AdditionalCharge
```

---

## Condition Assessment Domain

```mermaid
classDiagram
    class ConditionAssessment {
        +UUID id
        +UUID bookingId
        +UUID assetId
        +UUID conductedByUserId
        +AssessmentType type
        +AssessmentStatus status
        +String notes
        +String reportUrl
        +DateTime scheduledAt
        +DateTime conductedAt
        +DateTime customerSignedAt
        +String customerSignatureIp
        +conduct(checklist, photos)
        +generateReport()
        +compareWithPreRental()
    }

    class AssessmentItem {
        +UUID id
        +UUID assessmentId
        +String area
        +String description
        +ItemCondition condition
        +Boolean hasDamage
        +String damageDescription
    }

    class AssessmentPhoto {
        +UUID id
        +UUID assessmentId
        +UUID assessmentItemId
        +String url
        +String caption
        +DateTime uploadedAt
    }

    ConditionAssessment "1" --> "*" AssessmentItem
    ConditionAssessment "1" --> "*" AssessmentPhoto
```

---

## Maintenance Domain

```mermaid
classDiagram
    class MaintenanceRequest {
        +UUID id
        +String requestNumber
        +UUID assetId
        +UUID ownerUserId
        +UUID assignedToUserId
        +RequestPriority priority
        +RequestStatus status
        +String title
        +String description
        +String resolutionNotes
        +DateTime createdAt
        +DateTime assignedAt
        +DateTime startedAt
        +DateTime completedAt
        +DateTime closedAt
        +assign(staffUserId)
        +start()
        +complete(notes, photos)
        +approve()
        +reopen(reason)
        +getTotalCost()
    }

    class MaintenanceCost {
        +UUID id
        +UUID requestId
        +CostCategory category
        +String description
        +Decimal amount
        +DateTime recordedAt
    }

    class PreventiveService {
        +UUID id
        +UUID assetId
        +UUID assignedToUserId
        +String title
        +String description
        +ServiceRecurrence recurrence
        +Integer intervalDays
        +Date nextDueDate
        +TaskStatus status
        +schedule()
        +complete(notes)
        +generateNext()
    }

    MaintenanceRequest "1" --> "0..1" MaintenanceCost
```

---

## Enumeration Types

```mermaid
classDiagram
    class UserRole {
        <<enumeration>>
        OWNER
        CUSTOMER
        STAFF
        ADMIN
    }

    class AssetStatus {
        <<enumeration>>
        DRAFT
        AVAILABLE
        BOOKED
        UNDER_MAINTENANCE
        RETIRED
    }

    class BookingStatus {
        <<enumeration>>
        PENDING
        CONFIRMED
        ACTIVE
        PENDING_CLOSURE
        CLOSED
        CANCELLED
        DECLINED
    }

    class AgreementStatus {
        <<enumeration>>
        DRAFT
        PENDING_CUSTOMER_SIGNATURE
        PENDING_OWNER_SIGNATURE
        SIGNED
        AMENDED
        TERMINATED
    }

    class InvoiceStatus {
        <<enumeration>>
        DRAFT
        SENT
        PARTIALLY_PAID
        PAID
        OVERDUE
        WAIVED
    }

    class RequestStatus {
        <<enumeration>>
        OPEN
        ASSIGNED
        IN_PROGRESS
        COMPLETED
        CLOSED
        REOPENED
        CANCELLED
    }

    class RateType {
        <<enumeration>>
        HOURLY
        DAILY
        WEEKLY
        MONTHLY
    }

    class AssessmentType {
        <<enumeration>>
        PRE_RENTAL
        POST_RENTAL
        ROUTINE
    }

    class AdditionalChargeType {
        <<enumeration>>
        DAMAGE
        LATE_RETURN
        CLEANING
        FUEL
        EXCESS_MILEAGE
        OTHER
    }
```
