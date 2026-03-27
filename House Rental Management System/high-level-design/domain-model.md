# Domain Model

## Overview
The Domain Model shows the key business entities and their relationships in the house rental management system.

---

## Complete Domain Model

```mermaid
erDiagram
    USER ||--o{ PROPERTY : owns
    USER ||--o{ APPLICATION : submits
    USER ||--o{ LEASE : party_to
    USER ||--o{ PAYMENT : makes
    USER ||--o{ MAINTENANCE_REQUEST : submits
    USER ||--o{ NOTIFICATION : receives
    USER ||--o{ DOCUMENT : uploads

    PROPERTY ||--o{ UNIT : contains
    PROPERTY ||--o{ PROPERTY_PHOTO : has
    PROPERTY ||--o{ DOCUMENT : has

    UNIT ||--o{ APPLICATION : receives
    UNIT ||--o{ LEASE : covered_by
    UNIT ||--o{ RENT_INVOICE : generates
    UNIT ||--o{ BILL : assigned
    UNIT ||--o{ MAINTENANCE_REQUEST : for
    UNIT ||--o{ UNIT_PHOTO : has
    UNIT ||--o{ INSPECTION : subject_of

    LEASE ||--o{ RENT_INVOICE : generates
    LEASE ||--o{ LEASE_EVENT : emits
    LEASE ||--|| SECURITY_DEPOSIT : has
    LEASE ||--o{ DOCUMENT : generates

    RENT_INVOICE ||--o{ PAYMENT : paid_by
    RENT_INVOICE ||--o{ INVOICE_EVENT : emits

    BILL ||--o{ PAYMENT : paid_by
    BILL ||--o{ BILL_DISPUTE : subject_of

    MAINTENANCE_REQUEST ||--o{ REQUEST_EVENT : emits
    MAINTENANCE_REQUEST ||--o{ MAINTENANCE_PHOTO : has
    MAINTENANCE_REQUEST ||--|| MAINTENANCE_COST : has
    MAINTENANCE_REQUEST }o--o| USER : assigned_to

    SECURITY_DEPOSIT ||--o{ DEPOSIT_DEDUCTION : has
    SECURITY_DEPOSIT ||--o{ PAYMENT : refunded_via

    INSPECTION ||--o{ INSPECTION_FINDING : has
    INSPECTION ||--o{ INSPECTION_PHOTO : has
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
        +UserRole role
        +UserStatus status
        +Boolean otpEnabled
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
        +OwnerStatus verificationStatus
        +DateTime verifiedAt
        +submitDocuments()
        +addProperty()
        +getPortfolioSummary()
    }

    class TenantProfile {
        +UUID id
        +UUID userId
        +String employerName
        +Decimal monthlyIncome
        +String emergencyContact
        +TenantStatus status
        +getActiveLeases()
        +getPaymentHistory()
    }

    class MaintenanceStaffProfile {
        +UUID id
        +UUID userId
        +UUID ownerUserId
        +String specialisation
        +StaffStatus status
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
    User "1" --> "0..1" TenantProfile
    User "1" --> "0..1" MaintenanceStaffProfile
    User "1" --> "*" Notification
```

---

## Property Domain

```mermaid
classDiagram
    class Property {
        +UUID id
        +UUID ownerUserId
        +String name
        +String addressLine1
        +String addressLine2
        +String city
        +String state
        +String postalCode
        +String country
        +PropertyType type
        +PropertyStatus status
        +Decimal latitude
        +Decimal longitude
        +create()
        +publish()
        +unpublish()
        +getOccupancyRate()
    }

    class Unit {
        +UUID id
        +UUID propertyId
        +String unitNumber
        +Integer floor
        +Decimal sizeSqFt
        +Integer bedrooms
        +Integer bathrooms
        +Decimal baseRent
        +UnitStatus status
        +JSON amenities
        +publish()
        +setOccupied()
        +setVacant()
        +getActiveLease()
    }

    class PropertyPhoto {
        +UUID id
        +UUID propertyId
        +UUID unitId
        +String url
        +Integer position
        +Boolean isPrimary
        +String caption
    }

    class Document {
        +UUID id
        +UUID ownerId
        +String referenceType
        +UUID referenceId
        +DocumentType type
        +String fileUrl
        +String fileName
        +DateTime uploadedAt
        +share()
        +revoke()
    }

    Property "1" --> "*" Unit
    Property "1" --> "*" PropertyPhoto
    Property "1" --> "*" Document
    Unit "1" --> "*" PropertyPhoto
    Unit "1" --> "*" Document
```

---

## Application & Lease Domain

```mermaid
classDiagram
    class Application {
        +UUID id
        +UUID unitId
        +UUID tenantUserId
        +ApplicationStatus status
        +String employerName
        +Decimal monthlyIncome
        +String references
        +String rejectionReason
        +DateTime appliedAt
        +DateTime reviewedAt
        +approve()
        +reject()
        +createLease()
    }

    class Lease {
        +UUID id
        +UUID unitId
        +UUID ownerUserId
        +UUID tenantUserId
        +UUID applicationId
        +LeaseType type
        +LeaseStatus status
        +Date startDate
        +Date endDate
        +Decimal monthlyRent
        +Decimal securityDepositAmount
        +Integer billingDayOfMonth
        +Integer noticePeriodDays
        +Decimal earlyTerminationFee
        +String policies
        +DateTime signedByTenantAt
        +DateTime signedByOwnerAt
        +String signedDocumentUrl
        +sendForSignature()
        +sign()
        +renew()
        +terminate()
    }

    class LeaseEvent {
        +UUID id
        +UUID leaseId
        +String eventType
        +String message
        +UUID actorUserId
        +DateTime createdAt
    }

    class SecurityDeposit {
        +UUID id
        +UUID leaseId
        +Decimal amount
        +DepositStatus status
        +Decimal heldAmount
        +Decimal refundedAmount
        +DateTime collectedAt
        +DateTime refundedAt
        +addDeduction()
        +processRefund()
    }

    class DepositDeduction {
        +UUID id
        +UUID depositId
        +String reason
        +Decimal amount
        +String evidenceUrl
        +DateTime createdAt
    }

    Application "1" --> "0..1" Lease
    Lease "1" --> "*" LeaseEvent
    Lease "1" --> "1" SecurityDeposit
    SecurityDeposit "1" --> "*" DepositDeduction
```

---

## Rent & Bill Domain

```mermaid
classDiagram
    class RentInvoice {
        +UUID id
        +String invoiceNumber
        +UUID leaseId
        +UUID unitId
        +UUID tenantUserId
        +Decimal baseRent
        +Decimal lateFee
        +Decimal otherCharges
        +Decimal totalAmount
        +Decimal paidAmount
        +InvoiceStatus status
        +Date dueDate
        +Date billingPeriodStart
        +Date billingPeriodEnd
        +DateTime createdAt
        +DateTime paidAt
        +applyLateFee()
        +markPaid()
        +generateReceipt()
    }

    class Bill {
        +UUID id
        +UUID unitId
        +UUID propertyId
        +UUID createdByUserId
        +BillType type
        +Decimal amount
        +Decimal paidAmount
        +BillStatus status
        +Date billingPeriodStart
        +Date billingPeriodEnd
        +Date dueDate
        +String scanUrl
        +SplitMethod splitMethod
        +DateTime createdAt
        +addPayment()
        +splitAcrossUnits()
    }

    class BillDispute {
        +UUID id
        +UUID billId
        +UUID tenantUserId
        +String reason
        +DisputeStatus status
        +Decimal adjustedAmount
        +String resolutionNote
        +DateTime createdAt
        +DateTime resolvedAt
        +resolve()
        +escalate()
    }

    class Payment {
        +UUID id
        +String referenceType
        +UUID referenceId
        +UUID payerUserId
        +PaymentMethod method
        +PaymentStatus status
        +Decimal amount
        +String gatewayRef
        +String gatewayResponse
        +Boolean isOffline
        +DateTime createdAt
        +DateTime confirmedAt
        +process()
        +refund()
    }

    RentInvoice "1" --> "*" Payment
    Bill "1" --> "*" Payment
    Bill "1" --> "0..1" BillDispute
```

---

## Maintenance Domain

```mermaid
classDiagram
    class MaintenanceRequest {
        +UUID id
        +String requestNumber
        +UUID unitId
        +UUID tenantUserId
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
        +DateTime completedAt
        +DateTime closedAt
        +assign()
        +updateStatus()
        +complete()
        +close()
        +reopen()
    }

    class MaintenancePhoto {
        +UUID id
        +UUID requestId
        +String url
        +PhotoStage stage
        +DateTime uploadedAt
    }

    class MaintenanceCost {
        +UUID id
        +UUID requestId
        +CostCategory category
        +String description
        +Decimal amount
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
        +UUID assignedToUserId
        +String title
        +String description
        +TaskRecurrence recurrence
        +Date nextDueDate
        +TaskStatus status
        +schedule()
        +complete()
        +reschedule()
    }

    MaintenanceRequest "1" --> "*" MaintenancePhoto
    MaintenanceRequest "1" --> "0..1" MaintenanceCost
    MaintenanceRequest "1" --> "*" RequestEvent
```

---

## Inspection Domain

```mermaid
classDiagram
    class Inspection {
        +UUID id
        +UUID unitId
        +UUID leaseId
        +UUID conductedByUserId
        +InspectionType type
        +InspectionStatus status
        +Date scheduledDate
        +DateTime conductedAt
        +String notes
        +String reportUrl
        +conduct()
        +generateReport()
    }

    class InspectionFinding {
        +UUID id
        +UUID inspectionId
        +String area
        +String description
        +FindingSeverity severity
        +Boolean requiresRepair
        +Decimal estimatedCost
    }

    class InspectionPhoto {
        +UUID id
        +UUID inspectionId
        +String url
        +String caption
        +DateTime uploadedAt
    }

    Inspection "1" --> "*" InspectionFinding
    Inspection "1" --> "*" InspectionPhoto
```

---

## Enumeration Types

```mermaid
classDiagram
    class UserRole {
        <<enumeration>>
        OWNER
        TENANT
        MAINTENANCE_STAFF
        ADMIN
    }

    class UnitStatus {
        <<enumeration>>
        VACANT
        OCCUPIED
        UNDER_MAINTENANCE
        UNLISTED
    }

    class LeaseStatus {
        <<enumeration>>
        DRAFT
        PENDING_TENANT_SIGNATURE
        PENDING_OWNER_SIGNATURE
        ACTIVE
        EXPIRED
        TERMINATED
        DECLINED
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

    class RequestPriority {
        <<enumeration>>
        LOW
        MEDIUM
        HIGH
        EMERGENCY
    }

    class BillType {
        <<enumeration>>
        ELECTRICITY
        WATER
        GAS
        INTERNET
        MAINTENANCE_CHARGE
        OTHER
    }

    class InspectionType {
        <<enumeration>>
        MOVE_IN
        MID_TERM
        MOVE_OUT
        ROUTINE
    }
```
