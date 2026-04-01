# Class Diagram — Real Estate Management System

## Overview

This document describes the domain model for the Real Estate Management System using a UML class diagram. The model covers all core entities from property ownership and management through tenant lifecycle, financial operations, maintenance, inspections, and owner reporting.

---

## Class Diagram

```mermaid
classDiagram
    class Company {
        +UUID id
        +String name
        +String subdomain
        +String email
        +String phone
        +String addressLine1
        +String city
        +String state
        +String zipCode
        +CompanyStatus status
        +PlanTier planTier
        +DateTime createdAt
        +DateTime updatedAt
        +addPropertyManager(pm: PropertyManager) void
        +addOwner(owner: Owner) void
        +getProperties() Property[]
        +generateBillingReport() BillingReport
    }

    class Agency {
        +UUID id
        +UUID companyId
        +String name
        +String licenseNumber
        +String address
        +String city
        +String state
        +AgencyStatus status
        +DateTime createdAt
        +addManager(pm: PropertyManager) void
        +getActiveManagers() PropertyManager[]
    }

    class PropertyManager {
        +UUID id
        +UUID companyId
        +UUID agencyId
        +String firstName
        +String lastName
        +String email
        +String phone
        +ManagerRole role
        +ManagerStatus status
        +DateTime createdAt
        +DateTime updatedAt
        +assignProperty(property: Property) void
        +createListing(unit: PropertyUnit) Listing
        +reviewApplication(app: TenantApplication) void
        +scheduleMaintenance(req: MaintenanceRequest) MaintenanceAssignment
    }

    class Owner {
        +UUID id
        +UUID companyId
        +String firstName
        +String lastName
        +String email
        +String phone
        +String taxId
        +OwnerStatus status
        +String bankAccountId
        +String bankRoutingNumber
        +DateTime createdAt
        +getProperties() Property[]
        +getStatements(period: DateRange) OwnerStatement[]
        +approveMaintenanceBudget(req: MaintenanceRequest, amount: Decimal) void
    }

    class Property {
        +UUID id
        +UUID companyId
        +UUID ownerId
        +UUID managerId
        +String name
        +PropertyType propertyType
        +String addressLine1
        +String addressLine2
        +String city
        +String state
        +String zipCode
        +String country
        +String latitude
        +String longitude
        +PropertyStatus status
        +Integer totalUnits
        +Integer occupiedUnits
        +Integer yearBuilt
        +DateTime createdAt
        +DateTime updatedAt
        +addUnit(unit: PropertyUnit) void
        +publishListing(unit: PropertyUnit) Listing
        +scheduleInspection(unit: PropertyUnit, date: Date) Inspection
        +generateOwnerStatement(period: DateRange) OwnerStatement
        +getOccupancyRate() Decimal
    }

    class PropertyUnit {
        +UUID id
        +UUID propertyId
        +UUID floorId
        +String unitNumber
        +UnitType unitType
        +Decimal monthlyRent
        +Integer bedrooms
        +Integer bathrooms
        +Decimal squareFeet
        +UnitStatus status
        +Boolean petFriendly
        +Boolean isAccessible
        +Date availableFrom
        +DateTime createdAt
        +activate() void
        +list(details: ListingDetails) Listing
        +assignLease(lease: Lease) void
        +getActiveLease() Lease
        +getCurrentTenant() Tenant
    }

    class Floor {
        +UUID id
        +UUID propertyId
        +Integer floorNumber
        +String name
        +Integer totalUnits
        +DateTime createdAt
        +getUnits() PropertyUnit[]
        +getOccupiedUnits() PropertyUnit[]
    }

    class Amenity {
        +UUID id
        +UUID propertyId
        +String name
        +AmenityCategory category
        +String description
        +Boolean isActive
        +DateTime createdAt
    }

    class Listing {
        +UUID id
        +UUID propertyId
        +UUID unitId
        +UUID managerId
        +String title
        +String description
        +Decimal rentAmount
        +Decimal depositAmount
        +Date availableDate
        +Integer leaseDurationMonths
        +ListingStatus status
        +Boolean mlsSynced
        +String mlsListingId
        +DateTime publishedAt
        +DateTime expiresAt
        +DateTime createdAt
        +publish() void
        +unpublish() void
        +syncToMLS() Boolean
        +addPhoto(photo: ListingPhoto) void
        +getApplicationCount() Integer
    }

    class ListingPhoto {
        +UUID id
        +UUID listingId
        +String url
        +String thumbnailUrl
        +Integer sortOrder
        +String caption
        +Integer fileSizeBytes
        +String mimeType
        +DateTime uploadedAt
        +delete() void
        +generateThumbnail() String
    }

    class Tenant {
        +UUID id
        +UUID companyId
        +String firstName
        +String lastName
        +String email
        +String phone
        +String ssnEncrypted
        +Date dateOfBirth
        +String currentAddress
        +Decimal annualIncome
        +String employerName
        +TenantStatus status
        +DateTime createdAt
        +DateTime updatedAt
        +applyForUnit(unit: PropertyUnit) TenantApplication
        +getActiveLeases() Lease[]
        +submitMaintenanceRequest(unit: PropertyUnit) MaintenanceRequest
        +makePayment(invoice: RentInvoice) RentPayment
    }

    class TenantApplication {
        +UUID id
        +UUID tenantId
        +UUID listingId
        +UUID unitId
        +UUID reviewerId
        +Decimal proposedRent
        +Date desiredMoveIn
        +Integer occupants
        +Boolean hasPets
        +ApplicationStatus status
        +String rejectionReason
        +DateTime submittedAt
        +DateTime reviewedAt
        +runBackgroundCheck() BackgroundCheck
        +runCreditCheck() CreditCheck
        +approve() Lease
        +reject(reason: String) void
    }

    class BackgroundCheck {
        +UUID id
        +UUID applicationId
        +String externalProviderId
        +String provider
        +BackgroundCheckStatus status
        +Boolean criminalRecordFound
        +Boolean evictionRecordFound
        +Boolean sexOffenderFound
        +JSON rawReport
        +DateTime initiatedAt
        +DateTime completedAt
        +initiate() void
        +fetchReport() JSON
        +getResult() BackgroundCheckResult
    }

    class CreditCheck {
        +UUID id
        +UUID applicationId
        +String externalReportId
        +String provider
        +CreditCheckStatus status
        +Integer creditScore
        +Decimal debtToIncomeRatio
        +Boolean bankruptcyFound
        +String bureau
        +JSON rawReport
        +DateTime initiatedAt
        +DateTime completedAt
        +initiate() void
        +fetchReport() JSON
        +getScore() Integer
    }

    class Lease {
        +UUID id
        +UUID tenantId
        +UUID unitId
        +UUID propertyId
        +UUID managerId
        +Date startDate
        +Date endDate
        +Decimal monthlyRent
        +Decimal securityDeposit
        +Integer gracePeriodDays
        +LeaseType leaseType
        +LeaseStatus status
        +String docuSignEnvelopeId
        +DateTime sentForSigningAt
        +DateTime signedAt
        +DateTime activatedAt
        +DateTime terminatedAt
        +createRentSchedule() RentSchedule
        +sendForSigning() String
        +activate() void
        +terminate(reason: String) LeaseTermination
        +renew(terms: RenewalTerms) LeaseRenewal
        +getDaysUntilExpiry() Integer
    }

    class LeaseClause {
        +UUID id
        +UUID leaseId
        +String title
        +String body
        +ClauseType clauseType
        +Boolean isStandard
        +Integer sortOrder
        +DateTime createdAt
    }

    class LeaseRenewal {
        +UUID id
        +UUID originalLeaseId
        +UUID newLeaseId
        +Date newStartDate
        +Date newEndDate
        +Decimal newMonthlyRent
        +Decimal rentIncreasePct
        +RenewalStatus status
        +DateTime offeredAt
        +DateTime respondedAt
        +DateTime acceptedAt
        +offer() void
        +accept() Lease
        +decline() void
    }

    class LeaseTermination {
        +UUID id
        +UUID leaseId
        +TerminationReason reason
        +String notes
        +Date moveOutDate
        +Decimal earlyTerminationFee
        +TerminationStatus status
        +DateTime initiatedAt
        +DateTime confirmedAt
        +calculateFee() Decimal
        +confirm() void
        +processDeposit() DepositRefund
    }

    class RentSchedule {
        +UUID id
        +UUID leaseId
        +Date firstDueDate
        +Integer dueDayOfMonth
        +Decimal amount
        +Integer gracePeriodDays
        +ScheduleStatus status
        +DateTime createdAt
        +generateInvoices(month: Date) RentInvoice[]
        +pause() void
        +resume() void
    }

    class RentInvoice {
        +UUID id
        +UUID scheduleId
        +UUID leaseId
        +UUID tenantId
        +Decimal amount
        +Decimal lateFeeAmount
        +Date dueDate
        +Date periodStart
        +Date periodEnd
        +InvoiceStatus status
        +DateTime generatedAt
        +DateTime paidAt
        +generatePaymentLink() String
        +applyLateFee(fee: LateFee) void
        +markPaid(payment: RentPayment) void
    }

    class RentPayment {
        +UUID id
        +UUID invoiceId
        +UUID tenantId
        +Decimal amount
        +PaymentMethod method
        +PaymentStatus status
        +String stripePaymentIntentId
        +String stripeChargeId
        +DateTime processedAt
        +DateTime failedAt
        +String failureReason
        +process() void
        +refund(amount: Decimal) void
        +getReceipt() Document
    }

    class LateFee {
        +UUID id
        +UUID invoiceId
        +UUID leaseId
        +Decimal amount
        +LateFeeType feeType
        +Decimal flatAmount
        +Decimal percentageRate
        +LateFeeStatus status
        +DateTime calculatedAt
        +DateTime appliedAt
        +calculate() Decimal
        +waive(reason: String) void
        +apply() void
    }

    class SecurityDeposit {
        +UUID id
        +UUID leaseId
        +UUID tenantId
        +Decimal amount
        +DepositStatus status
        +String stripePaymentIntentId
        +DateTime receivedAt
        +DateTime heldUntil
        +getRefundableAmount() Decimal
        +initiateRefund(amount: Decimal) DepositRefund
        +applyDeduction(reason: String, amount: Decimal) void
    }

    class DepositRefund {
        +UUID id
        +UUID depositId
        +UUID leaseId
        +Decimal totalDeposit
        +Decimal deductionAmount
        +Decimal refundAmount
        +String deductionNotes
        +RefundStatus status
        +String stripeTransferId
        +DateTime initiatedAt
        +DateTime completedAt
        +process() void
        +dispute(reason: String) void
    }

    class MaintenanceRequest {
        +UUID id
        +UUID unitId
        +UUID propertyId
        +UUID tenantId
        +UUID assignedContractorId
        +String title
        +String description
        +MaintenancePriority priority
        +MaintenanceCategory category
        +MaintenanceStatus status
        +Decimal estimatedCost
        +Decimal actualCost
        +Decimal ownerApprovedBudget
        +String[] photoUrls
        +DateTime submittedAt
        +DateTime resolvedAt
        +triage(priority: MaintenancePriority) void
        +assign(contractor: Contractor) MaintenanceAssignment
        +uploadPhoto(file: File) String
        +complete(notes: String) void
        +escalate() void
    }

    class MaintenanceAssignment {
        +UUID id
        +UUID requestId
        +UUID contractorId
        +DateTime scheduledAt
        +DateTime startedAt
        +DateTime completedAt
        +AssignmentStatus status
        +String completionNotes
        +Decimal laborCost
        +Decimal materialCost
        +confirm() void
        +start() void
        +complete(notes: String) void
    }

    class Contractor {
        +UUID id
        +UUID companyId
        +String name
        +String contactEmail
        +String contactPhone
        +String licenseNumber
        +ContractorStatus status
        +String[] specialties
        +Decimal hourlyRate
        +DateTime createdAt
        +getActiveAssignments() MaintenanceAssignment[]
        +isAvailable(date: Date) Boolean
    }

    class Inspection {
        +UUID id
        +UUID propertyId
        +UUID unitId
        +UUID inspectorId
        +InspectionType inspectionType
        +InspectionStatus status
        +Date scheduledDate
        +DateTime startedAt
        +DateTime completedAt
        +String notes
        +DateTime createdAt
        +addItems(template: InspectionTemplate) void
        +start() void
        +complete() void
        +generateReport() Document
    }

    class InspectionItem {
        +UUID id
        +UUID inspectionId
        +String area
        +String itemName
        +ItemCondition condition
        +String notes
        +String[] photoUrls
        +Boolean requiresRepair
        +DateTime recordedAt
        +addPhoto(url: String) void
        +markCondition(condition: ItemCondition) void
    }

    class Document {
        +UUID id
        +UUID companyId
        +String entityType
        +UUID entityId
        +String name
        +DocumentType documentType
        +String url
        +String mimeType
        +Integer fileSizeBytes
        +Boolean isConfidential
        +DateTime uploadedAt
        +DateTime expiresAt
        +download() String
        +delete() void
    }

    class Utility {
        +UUID id
        +UUID propertyId
        +UtilityType utilityType
        +String provider
        +String accountNumber
        +Boolean isTenantResponsible
        +DateTime createdAt
        +getRecords(period: DateRange) UtilityRecord[]
    }

    class UtilityRecord {
        +UUID id
        +UUID utilityId
        +UUID unitId
        +Date billingPeriodStart
        +Date billingPeriodEnd
        +Decimal amount
        +Decimal usage
        +String usageUnit
        +RecordStatus status
        +DateTime createdAt
    }

    class OwnerStatement {
        +UUID id
        +UUID ownerId
        +UUID propertyId
        +Date periodStart
        +Date periodEnd
        +Decimal totalRentCollected
        +Decimal totalExpenses
        +Decimal managementFee
        +Decimal managementFeeRate
        +Decimal netIncome
        +StatementStatus status
        +DateTime generatedAt
        +DateTime sentAt
        +generate() void
        +export(format: ExportFormat) Document
        +distribute() void
    }

    %% Relationships
    Company "1" --> "*" PropertyManager : employs
    Company "1" --> "*" Owner : has
    Company "1" --> "*" Property : owns
    Company "1" --> "*" Agency : manages
    Agency "1" --> "*" PropertyManager : contains
    Owner "1" --> "*" Property : owns
    Property "1" *-- "*" PropertyUnit : contains
    Property "1" *-- "*" Floor : has
    Property "1" --> "*" Amenity : provides
    Property "1" --> "*" Listing : advertises
    Floor "1" --> "*" PropertyUnit : contains
    PropertyUnit "1" --> "*" Listing : listed_as
    Listing "1" *-- "*" ListingPhoto : has
    Tenant "1" --> "*" TenantApplication : submits
    TenantApplication "1" --> "0..1" BackgroundCheck : triggers
    TenantApplication "1" --> "0..1" CreditCheck : triggers
    TenantApplication "0..1" --> "1" Lease : creates
    Lease "1" *-- "*" LeaseClause : contains
    Lease "1" --> "0..1" LeaseRenewal : renewed_by
    Lease "1" --> "0..1" LeaseTermination : ended_by
    Lease "1" *-- "0..1" RentSchedule : schedules
    Lease "1" *-- "0..1" SecurityDeposit : secured_by
    RentSchedule "1" --> "*" RentInvoice : generates
    RentInvoice "1" --> "*" RentPayment : paid_via
    RentInvoice "1" --> "*" LateFee : incurs
    SecurityDeposit "1" --> "0..1" DepositRefund : refunded_via
    PropertyUnit "1" --> "*" MaintenanceRequest : subject_of
    MaintenanceRequest "1" --> "*" MaintenanceAssignment : fulfilled_by
    Contractor "1" --> "*" MaintenanceAssignment : handles
    Property "1" --> "*" Inspection : inspected_via
    Inspection "1" *-- "*" InspectionItem : contains
    Property "1" --> "*" Utility : has
    Utility "1" --> "*" UtilityRecord : tracks
    Owner "1" --> "*" OwnerStatement : receives
    Lease "1" --> "1" Tenant : signed_by
    Lease "1" --> "1" PropertyUnit : for
```

---

## Class Descriptions

| Class | Responsibility |
|-------|---------------|
| **Company** | Top-level SaaS tenant. Owns all data for a property management company including managers, owners, and properties. Controls plan tier and billing. |
| **Agency** | A real estate agency or brokerage associated with a Company. Groups PropertyManagers under a licensed entity. |
| **PropertyManager** | An employee or agent who manages day-to-day operations: creating listings, reviewing applications, handling maintenance. |
| **Owner** | The legal owner of one or more properties. Receives financial statements and sets maintenance budget limits. |
| **Property** | A physical building or complex. Contains multiple units, floors, and amenities. The root aggregate for most operations. |
| **PropertyUnit** | A leasable unit within a Property (apartment, suite, commercial space). Tracks rent amount, status, and size. |
| **Floor** | A level within a Property building. Used to group units for elevator/stairwell assignments and inspections. |
| **Amenity** | A shared facility offered by a Property (gym, pool, parking, laundry). Associated with listings. |
| **Listing** | A published advertisement for a vacant unit. Can be synced to MLS/Zillow. Collects applications. |
| **ListingPhoto** | A photo asset attached to a Listing. Stores URL, thumbnail, sort order, and file metadata. |
| **Tenant** | A person who applies for and occupies a unit. Holds encrypted PII. Has an account in the tenant portal. |
| **TenantApplication** | A rental application submitted by a Tenant for a specific unit. Tracks income, occupants, and decision status. |
| **BackgroundCheck** | A third-party (Checkr) background screening for a TenantApplication. Stores criminal, eviction, and sex offender results. |
| **CreditCheck** | A credit bureau pull (TransUnion/Equifax) for a TenantApplication. Stores score, DTI, and raw bureau report. |
| **Lease** | The legal rental agreement between a Tenant and a PropertyUnit. The central financial entity — drives rent scheduling and deposit collection. |
| **LeaseClause** | An individual clause within a Lease (pet policy, parking, utilities). Standard or custom text. |
| **LeaseRenewal** | A formal offer to extend a Lease beyond its end date, potentially with new rent terms. |
| **LeaseTermination** | Records an early or normal termination of a Lease. Calculates early termination fees and triggers deposit refund. |
| **RentSchedule** | Defines when and how much rent is due each month. Drives the monthly invoice generation job. |
| **RentInvoice** | A monthly rent bill generated for a Tenant. Tracks due date, late fee accrual, and payment status. |
| **RentPayment** | A payment transaction made against a RentInvoice via Stripe. Tracks charge ID, status, and failure reason. |
| **LateFee** | A fee charged when rent is paid after the grace period. Can be flat or percentage-based. Can be waived by a manager. |
| **SecurityDeposit** | The upfront deposit collected at lease signing, held until move-out. Subject to state legal limits. |
| **DepositRefund** | The return of a SecurityDeposit at move-out, minus any itemized deductions for damages or unpaid rent. |
| **MaintenanceRequest** | A repair or service request submitted by a Tenant or PropertyManager. Tracks priority, category, cost, and photos. |
| **MaintenanceAssignment** | The assignment of a MaintenanceRequest to a specific Contractor, with scheduling and cost tracking. |
| **Contractor** | An external vendor authorized to perform maintenance work. Has specialties, hourly rate, and license. |
| **Inspection** | A scheduled walkthrough of a unit (move-in, move-out, routine, annual). Generates an itemized report. |
| **InspectionItem** | A single checklist item within an Inspection (e.g., "Kitchen Sink — Fair"). Supports photos and repair flags. |
| **Document** | A file asset (PDF, image) associated with any entity. Stores URL, type, size, and confidentiality flag. |
| **Utility** | A utility service (electric, gas, water) attached to a Property, either owner-paid or tenant-paid. |
| **UtilityRecord** | A monthly billing record for a Utility on a specific unit. Used to split utility charges to tenants. |
| **OwnerStatement** | A monthly financial summary sent to an Owner. Shows rent collected, expenses, management fees, and net income. |
