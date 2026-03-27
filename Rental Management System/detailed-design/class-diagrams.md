# Class Diagrams

## Overview
Detailed class diagrams with attributes, methods, and relationships for each major domain in the rental management system.

---

## User & Auth Domain

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
        +Boolean otpEnabled
        +DateTime createdAt
        +DateTime updatedAt
        +register(email, phone, password) User
        +login(credential, password) Token
        +verifyOTP(code) Boolean
        +resetPassword(token, newPassword) void
        +updateProfile(data) User
    }

    class AuthToken {
        +UUID id
        +UUID userId
        +String accessToken
        +String refreshToken
        +DateTime accessExpiresAt
        +DateTime refreshExpiresAt
        +Boolean isRevoked
        +refresh() AuthToken
        +revoke() void
    }

    class AuditLog {
        +UUID id
        +UUID userId
        +String action
        +String resourceType
        +UUID resourceId
        +JSON changes
        +String ipAddress
        +String userAgent
        +DateTime createdAt
    }

    User "1" --> "*" AuthToken
    User "1" --> "*" AuditLog
```

---

## Asset & Category Domain

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
        +Integer displayOrder
        +getAttributes() CategoryAttribute[]
        +getAssets() Asset[]
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
        +validate(value) Boolean
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
        +Boolean instantBookingEnabled
        +Decimal averageRating
        +Integer reviewCount
        +DateTime createdAt
        +DateTime updatedAt
        +publish() void
        +unpublish() void
        +checkAvailability(start, end) Boolean
        +calculatePrice(start, end) PriceBreakdown
        +getActiveMaintenance() MaintenanceRequest
    }

    class AssetAttributeValue {
        +UUID id
        +UUID assetId
        +UUID attributeId
        +String value
        +update(value) void
    }

    class AssetPhoto {
        +UUID id
        +UUID assetId
        +String url
        +String thumbnailUrl
        +Integer position
        +Boolean isCover
        +String caption
        +upload(file) AssetPhoto
        +reorder(position) void
        +delete() void
    }

    AssetCategory "1" --> "*" AssetCategory : parentOf
    AssetCategory "1" --> "*" CategoryAttribute
    AssetCategory "1" --> "*" Asset
    Asset "1" --> "*" AssetAttributeValue
    Asset "1" --> "*" AssetPhoto
```

---

## Pricing Domain

```mermaid
classDiagram
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
        +isApplicable(start, end) Boolean
        +calculateCost(durationUnits) Decimal
    }

    class PricingEngine {
        +calculatePrice(assetId, start, end) PriceBreakdown
        +applyPeakSurcharge(baseFee, rules) Decimal
        +applyDiscount(baseFee, rule) Decimal
        +calculateTax(subtotal, categoryId, jurisdiction) Decimal
        +getBestRateCombination(durationHours, rules) RateCombo[]
    }

    class PriceBreakdown {
        +Decimal baseFee
        +RateType rateType
        +Integer rateUnits
        +Decimal peakSurcharge
        +Decimal discountAmount
        +Decimal taxAmount
        +Decimal depositAmount
        +Decimal totalDue
        +String currency
    }

    PricingEngine --> PricingRule
    PricingEngine --> PriceBreakdown
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
        +confirm() void
        +decline(reason) void
        +modify(newStart, newEnd) PriceDiff
        +cancel(reason) RefundAmount
        +initiateReturn(actualReturnAt) void
        +close() void
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
        +create() void
        +release() void
    }

    class CancellationPolicy {
        +UUID id
        +UUID assetId
        +String name
        +Integer freeCancellationHours
        +Integer partialRefundHours
        +Decimal partialRefundPercent
        +calculateRefund(booking, cancellationAt) Decimal
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

    Booking "1" --> "*" BookingEvent
    Booking "1" --> "*" AvailabilityBlock
    Booking "*" --> "1" CancellationPolicy
```

---

## Agreement Domain

```mermaid
classDiagram
    class AgreementTemplate {
        +UUID id
        +UUID createdByAdminId
        +UUID categoryId
        +String name
        +String templateContent
        +Boolean isActive
        +Integer version
        +DateTime createdAt
        +render(params) String
    }

    class RentalAgreement {
        +UUID id
        +UUID bookingId
        +UUID templateId
        +AgreementStatus status
        +String renderedContent
        +String eSignRequestId
        +String signedDocumentUrl
        +DateTime sentAt
        +DateTime customerSignedAt
        +String customerSignatureIp
        +DateTime ownerSignedAt
        +String ownerSignatureIp
        +Integer version
        +send() void
        +customerSign(ip) void
        +ownerSign(ip) void
        +amend(reason, content) AgreementAmendment
    }

    class AgreementAmendment {
        +UUID id
        +UUID agreementId
        +Integer amendmentNumber
        +String reason
        +String renderedContent
        +String signedDocumentUrl
        +AgreementStatus status
        +DateTime createdAt
        +DateTime signedAt
    }

    RentalAgreement "*" --> "1" AgreementTemplate
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
        +addLineItem(description, amount, type) void
        +recordPayment(paymentId) void
        +generateReceipt() Document
        +getOutstandingAmount() Decimal
    }

    class InvoiceLineItem {
        +UUID id
        +UUID invoiceId
        +LineItemType type
        +String description
        +Decimal amount
        +Decimal taxRate
        +Decimal taxAmount
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
        +dispute(reason) void
        +approve() void
        +waive(reason) void
        +escalateToAdmin() void
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
        +process() void
        +refund(amount) Refund
    }

    class Refund {
        +UUID id
        +UUID paymentId
        +String gatewayRef
        +Decimal amount
        +RefundStatus status
        +String reason
        +DateTime initiatedAt
        +DateTime completedAt
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
        +calculate() void
        +process() void
    }

    Invoice "1" --> "*" InvoiceLineItem
    Invoice "1" --> "*" Payment
    Payment "1" --> "*" Refund
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
        +String overallNotes
        +String reportUrl
        +DateTime scheduledAt
        +DateTime conductedAt
        +DateTime customerSignedAt
        +String customerSignatureIp
        +conduct(items, photos) void
        +generateReport() Document
        +compareWith(preAssessmentId) ComparisonResult
        +customerCountersign(ip) void
    }

    class AssessmentItem {
        +UUID id
        +UUID assessmentId
        +String area
        +String description
        +ItemCondition condition
        +Boolean hasDamage
        +String damageDescription
        +Decimal estimatedRepairCost
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
        +assign(staffUserId) void
        +start() void
        +complete(notes, photos) void
        +approve() void
        +reopen(reason) void
        +cancel() void
        +getTotalCost() Decimal
    }

    class MaintenanceCost {
        +UUID id
        +UUID requestId
        +CostCategory category
        +String description
        +Decimal amount
        +UUID recordedByUserId
        +DateTime recordedAt
    }

    class PreventiveService {
        +UUID id
        +UUID assetId
        +UUID createdByUserId
        +UUID assignedToUserId
        +String title
        +String description
        +ServiceRecurrence recurrence
        +Integer intervalDays
        +Date nextDueDate
        +TaskStatus status
        +DateTime lastCompletedAt
        +schedule() void
        +complete(notes) void
        +reschedule(date) void
        +generateNext() PreventiveService
    }

    MaintenanceRequest "1" --> "0..1" MaintenanceCost
```
