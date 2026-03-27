# Class Diagrams

## Overview
Detailed class diagrams with attributes, methods, and relationships for each major domain in the house rental management system.

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
        +DateTime createdAt
    }

    User "1" --> "*" AuthToken
    User "1" --> "*" AuditLog
```

---

## Property & Unit Domain

```mermaid
classDiagram
    class Property {
        +UUID id
        +UUID ownerUserId
        +String name
        +String description
        +PropertyType type
        +String addressLine1
        +String addressLine2
        +String city
        +String state
        +String postalCode
        +String country
        +Decimal latitude
        +Decimal longitude
        +PropertyStatus status
        +Integer totalUnits
        +DateTime createdAt
        +DateTime updatedAt
        +create(ownerUserId, data) Property
        +update(data) Property
        +getUnits() Unit[]
        +getOccupancyRate() Decimal
        +publish() void
        +unpublish() void
    }

    class Unit {
        +UUID id
        +UUID propertyId
        +String unitNumber
        +Integer floor
        +Decimal sizeSqFt
        +Integer bedrooms
        +Integer bathrooms
        +Integer parkingSpaces
        +Decimal baseRent
        +UnitStatus status
        +Boolean isPublished
        +JSON amenities
        +String petPolicy
        +String smokingPolicy
        +DateTime createdAt
        +DateTime updatedAt
        +setOccupied(leaseId) void
        +setVacant() void
        +setUnderMaintenance() void
        +getActiveLease() Lease
        +getApplications() Application[]
    }

    class PropertyPhoto {
        +UUID id
        +UUID propertyId
        +UUID unitId
        +String url
        +String thumbnailUrl
        +Integer position
        +Boolean isPrimary
        +String caption
        +upload(file) PropertyPhoto
        +delete() void
    }

    class Document {
        +UUID id
        +UUID uploadedByUserId
        +String referenceType
        +UUID referenceId
        +DocumentType type
        +String fileName
        +String fileUrl
        +Long fileSizeBytes
        +Boolean isShared
        +DateTime uploadedAt
        +share(userId) String
        +revoke() void
        +download() Blob
    }

    Property "1" --> "*" Unit
    Property "1" --> "*" PropertyPhoto
    Property "1" --> "*" Document
    Unit "1" --> "*" PropertyPhoto
    Unit "1" --> "*" Document
```

---

## Application & Screening Domain

```mermaid
classDiagram
    class Application {
        +UUID id
        +UUID unitId
        +UUID tenantUserId
        +ApplicationStatus status
        +String employerName
        +String jobTitle
        +Decimal monthlyIncome
        +String reference1Name
        +String reference1Contact
        +String reference2Name
        +String reference2Contact
        +String rejectionReason
        +DateTime appliedAt
        +DateTime reviewedAt
        +UUID reviewedByUserId
        +submit() void
        +approve(reviewerId) void
        +reject(reason, reviewerId) void
        +getDocuments() Document[]
    }

    class BackgroundCheckResult {
        +UUID id
        +UUID applicationId
        +String providerRef
        +Boolean creditCheckPassed
        +Integer creditScore
        +Boolean rentalHistoryPassed
        +Boolean identityVerified
        +JSON rawResult
        +DateTime checkedAt
        +isPassed() Boolean
    }

    Application "1" --> "0..1" BackgroundCheckResult
    Application "1" --> "*" Document
```

---

## Lease Domain

```mermaid
classDiagram
    class Lease {
        +UUID id
        +UUID unitId
        +UUID ownerUserId
        +UUID tenantUserId
        +UUID applicationId
        +UUID templateId
        +LeaseType type
        +LeaseStatus status
        +Date startDate
        +Date endDate
        +Decimal monthlyRent
        +Decimal securityDepositAmount
        +Integer billingDayOfMonth
        +Integer noticePeriodDays
        +Decimal earlyTerminationFee
        +String petPolicy
        +String smokingPolicy
        +String additionalTerms
        +String eSignRequestId
        +String signedDocumentUrl
        +DateTime sentForSignatureAt
        +DateTime signedByTenantAt
        +String tenantSignatureIp
        +DateTime signedByOwnerAt
        +String ownerSignatureIp
        +DateTime terminatedAt
        +String terminationReason
        +DateTime createdAt
        +send() void
        +tenantSign(ip) void
        +ownerSign(ip) void
        +generateRentSchedule() RentSchedule
        +renew(newTerms) Lease
        +terminate(reason, terminationDate) void
        +calculateEarlyFees(date) Decimal
    }

    class LeaseTemplate {
        +UUID id
        +UUID createdByAdminId
        +String name
        +String description
        +String templateContent
        +Boolean isActive
        +Integer version
        +DateTime createdAt
        +render(params) String
    }

    class LeaseEvent {
        +UUID id
        +UUID leaseId
        +String eventType
        +String message
        +UUID actorUserId
        +JSON metadata
        +DateTime createdAt
    }

    class SecurityDeposit {
        +UUID id
        +UUID leaseId
        +Decimal amount
        +DepositStatus status
        +Decimal deductionTotal
        +Decimal refundAmount
        +DateTime collectedAt
        +UUID collectionPaymentId
        +DateTime refundInitiatedAt
        +UUID refundPaymentId
        +addDeduction(reason, amount, evidence) DepositDeduction
        +finaliseRefund() Payment
        +getTotalDeductions() Decimal
    }

    class DepositDeduction {
        +UUID id
        +UUID depositId
        +String reason
        +Decimal amount
        +String evidenceUrl
        +UUID createdByUserId
        +DateTime createdAt
    }

    Lease "*" --> "1" LeaseTemplate
    Lease "1" --> "*" LeaseEvent
    Lease "1" --> "1" SecurityDeposit
    SecurityDeposit "1" --> "*" DepositDeduction
```

---

## Rent Invoice Domain

```mermaid
classDiagram
    class RentSchedule {
        +UUID id
        +UUID leaseId
        +RentScheduleStatus status
        +Integer billingDayOfMonth
        +Date nextBillingDate
        +generateNextInvoice() RentInvoice
        +pause() void
        +resume() void
    }

    class RentInvoice {
        +UUID id
        +String invoiceNumber
        +UUID leaseId
        +UUID unitId
        +UUID tenantUserId
        +UUID ownerUserId
        +Decimal baseRent
        +Decimal lateFee
        +Decimal adjustments
        +Decimal totalAmount
        +Decimal paidAmount
        +InvoiceStatus status
        +Date dueDate
        +Date billingPeriodStart
        +Date billingPeriodEnd
        +Boolean isProrated
        +DateTime createdAt
        +DateTime lastReminderSentAt
        +DateTime paidAt
        +applyLateFee(amount) void
        +addAdjustment(amount, reason) void
        +recordPayment(paymentId) void
        +generateReceipt() Document
        +getOutstandingAmount() Decimal
    }

    class LateFeeRule {
        +UUID id
        +UUID leaseId
        +Integer gracePeriodDays
        +LateFeeType feeType
        +Decimal feeValue
        +Decimal maxFee
        +calculate(daysOverdue, rentAmount) Decimal
    }

    RentSchedule "1" --> "*" RentInvoice
    RentInvoice "*" --> "1" LateFeeRule
```

---

## Maintenance Domain

```mermaid
classDiagram
    class MaintenanceRequest {
        +UUID id
        +String requestNumber
        +UUID unitId
        +UUID propertyId
        +UUID tenantUserId
        +UUID ownerUserId
        +UUID assignedToUserId
        +RequestPriority priority
        +RequestStatus status
        +String title
        +String description
        +String resolutionNotes
        +Integer rating
        +String ratingComment
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
        +rate(rating, comment) void
        +getTotalCost() Decimal
    }

    class MaintenancePhoto {
        +UUID id
        +UUID requestId
        +String url
        +PhotoStage stage
        +String caption
        +DateTime uploadedAt
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

    class RequestEvent {
        +UUID id
        +UUID requestId
        +String eventType
        +String message
        +UUID actorUserId
        +DateTime createdAt
    }

    class PreventiveTask {
        +UUID id
        +UUID propertyId
        +UUID unitId
        +UUID createdByUserId
        +UUID assignedToUserId
        +String title
        +String description
        +TaskRecurrence recurrence
        +Integer recurrenceIntervalDays
        +Date nextDueDate
        +TaskStatus status
        +DateTime createdAt
        +schedule() void
        +complete(notes) void
        +reschedule(date) void
        +generateNext() PreventiveTask
    }

    MaintenanceRequest "1" --> "*" MaintenancePhoto
    MaintenanceRequest "1" --> "0..1" MaintenanceCost
    MaintenanceRequest "1" --> "*" RequestEvent
```
