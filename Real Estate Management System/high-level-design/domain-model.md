# Domain Model — Real Estate Management System

## Overview

The Real Estate Management System (REMS) is decomposed into six bounded contexts, each owning its data and communicating with other contexts through domain events published on Apache Kafka. This separation enforces clear ownership, independent deployability, and loose coupling.

---

## Bounded Contexts

### 1. Property Management Context
Owns the physical asset hierarchy — companies, agencies, property managers, properties, units, floors, amenities, listings, and listing photos. Responsible for all lifecycle transitions of a unit (vacant → listed → occupied → under-maintenance). Publishes events like `UnitListed`, `UnitActivated`, `ListingPublished`.

### 2. Tenant Management Context
Owns tenant profiles, applications, and screening results. Orchestrates the application pipeline: intake → background check → credit check → approval/rejection. Subscribes to `BackgroundCheckCompleted` and `CreditCheckCompleted` events from third-party webhooks. Publishes `ApplicationApproved`, `ApplicationRejected`, `TenantProfileCreated`.

### 3. Lease Management Context
Owns the entire lease lifecycle — creation, signing, renewal, and termination. Integrates with DocuSign for electronic signatures and the Document Service for PDF generation. Manages clauses, rent schedules, security deposits, and deposit refunds. Publishes `LeaseActivated`, `LeaseExpiringSoon`, `LeaseRenewed`, `LeaseTerminated`.

### 4. Financial Operations Context
Owns all financial records — rent invoices, payments, late fees, ledger entries, and owner statements. Subscribes to `LeaseActivated` to bootstrap the rent schedule, and to Stripe webhooks for payment confirmation. Uses event sourcing for the financial ledger to maintain a complete immutable audit trail. Publishes `RentInvoiceIssued`, `RentPaymentReceived`, `LateFeeAssessed`, `OwnerStatementGenerated`.

### 5. Maintenance & Inspections Context
Owns maintenance requests, assignments, contractors, inspections, and inspection items. Independent of the lease context — a property can have maintenance work regardless of tenancy status. Subscribes to `LeaseTerminated` to trigger a move-out inspection. Publishes `MaintenanceRequestCreated`, `MaintenanceCompleted`, `InspectionScheduled`, `InspectionCompleted`.

### 6. Owner Portal Context
A read-optimised projection context (CQRS read side) that aggregates data from all other contexts into owner-friendly views: occupancy rates, income statements, maintenance cost summaries, and unit performance metrics. Subscribes to financial and maintenance events to keep its materialized views current. Publishes `OwnerStatementReady`.

---

## Domain Class Diagram

```mermaid
classDiagram
    direction TB

    class Company {
        +UUID id
        +String name
        +String taxId
        +String subscriptionPlan
        +String billingEmail
        +CompanyStatus status
        +DateTime createdAt
        +addAgency(agency)
        +updateSubscription(plan)
    }

    class Agency {
        +UUID id
        +UUID companyId
        +String name
        +String licenseNumber
        +Address address
        +String phone
        +DateTime createdAt
    }

    class PropertyManager {
        +UUID id
        +UUID agencyId
        +String firstName
        +String lastName
        +String email
        +String phone
        +String role
        +assignProperty(propertyId)
        +approveApplication(applicationId)
    }

    class Property {
        +UUID id
        +UUID agencyId
        +UUID managerId
        +String name
        +PropertyType type
        +Address address
        +Decimal latitude
        +Decimal longitude
        +Integer totalUnits
        +PropertyStatus status
        +DateTime builtYear
        +createListing()
        +addUnit(unit)
        +addAmenity(amenity)
    }

    class PropertyUnit {
        +UUID id
        +UUID propertyId
        +UUID floorId
        +String unitNumber
        +UnitType type
        +Integer bedrooms
        +Integer bathrooms
        +Decimal squareFeet
        +Decimal monthlyRent
        +UnitStatus status
        +activate()
        +deactivate()
        +markOccupied()
        +markVacant()
    }

    class Floor {
        +UUID id
        +UUID propertyId
        +Integer floorNumber
        +String label
        +Integer unitCount
    }

    class Amenity {
        +UUID id
        +UUID propertyId
        +String name
        +AmenityCategory category
        +Boolean isShared
    }

    class Listing {
        +UUID id
        +UUID unitId
        +UUID managerId
        +Decimal listedRent
        +Date availableFrom
        +ListingStatus status
        +String description
        +DateTime publishedAt
        +publish()
        +deactivate()
        +addPhoto(photo)
    }

    class ListingPhoto {
        +UUID id
        +UUID listingId
        +String s3Url
        +Integer sortOrder
        +Boolean isPrimary
        +DateTime uploadedAt
    }

    class Tenant {
        +UUID id
        +String firstName
        +String lastName
        +String email
        +String phone
        +String nationalId
        +DateTime dateOfBirth
        +TenantStatus status
        +DateTime createdAt
        +submitApplication(unitId)
    }

    class TenantApplication {
        +UUID id
        +UUID unitId
        +UUID tenantId
        +Decimal declaredIncome
        +Integer occupantsCount
        +ApplicationStatus status
        +String rejectionReason
        +DateTime submittedAt
        +DateTime decidedAt
        +approve()
        +reject(reason)
    }

    class BackgroundCheck {
        +UUID id
        +UUID applicationId
        +String externalCheckId
        +CheckStatus status
        +String reportUrl
        +DateTime initiatedAt
        +DateTime completedAt
    }

    class CreditCheck {
        +UUID id
        +UUID applicationId
        +String externalReportId
        +CheckStatus status
        +Integer creditScore
        +String reportUrl
        +DateTime initiatedAt
        +DateTime completedAt
    }

    class Lease {
        +UUID id
        +UUID applicationId
        +UUID unitId
        +UUID tenantId
        +UUID managerId
        +Date startDate
        +Date endDate
        +Decimal monthlyRent
        +Decimal securityDepositAmount
        +String docuSignEnvelopeId
        +String signedDocumentUrl
        +LeaseStatus status
        +DateTime activatedAt
        +activate()
        +renew(newEndDate)
        +terminate(reason)
    }

    class LeaseClause {
        +UUID id
        +UUID leaseId
        +String title
        +String body
        +Integer sortOrder
        +Boolean isMandatory
    }

    class LeaseRenewal {
        +UUID id
        +UUID originalLeaseId
        +UUID newLeaseId
        +Date renewalDate
        +Decimal newMonthlyRent
        +RenewalStatus status
    }

    class LeaseTermination {
        +UUID id
        +UUID leaseId
        +TerminationType type
        +String reason
        +Date noticeDate
        +Date vacateDate
        +TerminationStatus status
    }

    class RentSchedule {
        +UUID id
        +UUID leaseId
        +Integer dayOfMonth
        +Decimal amount
        +String currency
        +Boolean autoPayEnabled
        +String stripePaymentMethodId
        +Date nextDueDate
    }

    class RentInvoice {
        +UUID id
        +UUID leaseId
        +UUID tenantId
        +Decimal amount
        +Date dueDate
        +Date paidDate
        +InvoiceStatus status
        +Boolean lateFeeApplied
        +DateTime issuedAt
    }

    class RentPayment {
        +UUID id
        +UUID invoiceId
        +Decimal amount
        +String stripePaymentIntentId
        +PaymentStatus status
        +String failureReason
        +DateTime paidAt
    }

    class LateFee {
        +UUID id
        +UUID invoiceId
        +Decimal amount
        +LateFeeStatus status
        +DateTime assessedAt
        +DateTime paidAt
    }

    class SecurityDeposit {
        +UUID id
        +UUID leaseId
        +Decimal amount
        +DepositStatus status
        +String stripePaymentIntentId
        +DateTime collectedAt
    }

    class DepositRefund {
        +UUID id
        +UUID depositId
        +Decimal refundedAmount
        +Decimal deductions
        +String deductionReason
        +RefundStatus status
        +DateTime processedAt
    }

    class MaintenanceRequest {
        +UUID id
        +UUID unitId
        +UUID tenantId
        +String category
        +RequestPriority priority
        +String description
        +RequestStatus status
        +Integer tenantRating
        +DateTime openedAt
        +DateTime closedAt
        +assign(contractorId)
        +complete()
        +close(rating)
    }

    class MaintenanceAssignment {
        +UUID id
        +UUID requestId
        +UUID contractorId
        +Date scheduledDate
        +AssignmentStatus status
        +Decimal estimatedCost
        +Decimal actualCost
        +Decimal laborHours
        +DateTime assignedAt
        +DateTime completedAt
    }

    class Contractor {
        +UUID id
        +UUID agencyId
        +String companyName
        +String contactName
        +String email
        +String phone
        +String[] specialties
        +ContractorStatus status
        +Decimal hourlyRate
    }

    class Inspection {
        +UUID id
        +UUID propertyId
        +UUID unitId
        +UUID inspectorId
        +InspectionType type
        +InspectionStatus status
        +Date scheduledDate
        +DateTime conductedAt
        +String reportUrl
        +schedule()
        +complete(items)
    }

    class InspectionItem {
        +UUID id
        +UUID inspectionId
        +String area
        +String description
        +ItemCondition condition
        +String notes
        +String[] photoUrls
    }

    class Owner {
        +UUID id
        +UUID companyId
        +String firstName
        +String lastName
        +String email
        +String taxId
        +OwnerStatus status
    }

    class OwnerStatement {
        +UUID id
        +UUID ownerId
        +String period
        +Decimal grossIncome
        +Decimal managementFees
        +Decimal maintenanceCosts
        +Decimal otherExpenses
        +Decimal netIncome
        +DateTime generatedAt
    }

    %% Relationships
    Company "1" --> "many" Agency
    Agency "1" --> "many" PropertyManager
    Agency "1" --> "many" Property
    Property "1" --> "many" PropertyUnit
    Property "1" --> "many" Floor
    Property "1" --> "many" Amenity
    Floor "1" --> "many" PropertyUnit
    PropertyUnit "1" --> "0..1" Listing
    Listing "1" --> "many" ListingPhoto
    TenantApplication "1" --> "1" BackgroundCheck
    TenantApplication "1" --> "1" CreditCheck
    Tenant "1" --> "many" TenantApplication
    TenantApplication "1" --> "0..1" Lease
    Lease "1" --> "many" LeaseClause
    Lease "1" --> "0..1" LeaseRenewal
    Lease "1" --> "0..1" LeaseTermination
    Lease "1" --> "1" RentSchedule
    Lease "1" --> "many" RentInvoice
    RentInvoice "1" --> "many" RentPayment
    RentInvoice "1" --> "0..1" LateFee
    Lease "1" --> "1" SecurityDeposit
    SecurityDeposit "1" --> "0..1" DepositRefund
    PropertyUnit "1" --> "many" MaintenanceRequest
    MaintenanceRequest "1" --> "many" MaintenanceAssignment
    MaintenanceAssignment "many" --> "1" Contractor
    Property "1" --> "many" Inspection
    Inspection "1" --> "many" InspectionItem
    Owner "1" --> "many" Property
    Owner "1" --> "many" OwnerStatement
```

---

## Domain Event Flows Between Bounded Contexts

| Event | Producer Context | Consumer Context(s) | Purpose |
|---|---|---|---|
| `UnitListed` | Property Management | Tenant Management | Enable unit to appear in application flow |
| `ApplicationApproved` | Tenant Management | Lease Management | Trigger lease generation |
| `LeaseActivated` | Lease Management | Financial Operations | Bootstrap rent schedule + deposit collection |
| `LeaseTerminated` | Lease Management | Financial Operations, Maintenance | Stop rent schedule; trigger move-out inspection |
| `RentInvoiceIssued` | Financial Operations | Notification Service | Send invoice email/SMS to tenant |
| `RentPaymentReceived` | Financial Operations | Owner Portal | Update income projections |
| `LateFeeAssessed` | Financial Operations | Notification Service | Alert tenant to outstanding late fee |
| `MaintenanceCompleted` | Maintenance | Financial Operations | Record maintenance cost against property |
| `InspectionCompleted` | Maintenance | Lease Management | Attach inspection report to lease record |
| `OwnerStatementGenerated` | Financial Operations | Owner Portal | Publish monthly statement to owner dashboard |
| `LeaseExpiringSoon` | Lease Management | Notification Service | Send renewal prompt to tenant and PM |

---

*Last updated: 2025 | Real Estate Management System v1.0*
