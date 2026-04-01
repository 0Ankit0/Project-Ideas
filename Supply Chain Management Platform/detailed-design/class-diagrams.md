# Class Diagrams — Supply Chain Management Platform

## Overview

This document presents the formal UML class diagrams for the Supply Chain Management (SCM) Platform, rendered using Mermaid notation. The diagrams define domain entity structures, public operation contracts, and inter-aggregate relationships across the procurement and supply chain lifecycle.

The model is organized according to Domain-Driven Design (DDD) principles. Each bounded context encapsulates a cohesive cluster of domain objects with clearly defined aggregate roots, supporting entities, and value objects. Cross-domain references are maintained via UUID foreign keys to ensure loose coupling between aggregates while preserving referential integrity at the application layer.

---

## Bounded Domain Contexts

The SCM Platform is partitioned into six primary bounded contexts, each with designated aggregate roots and supporting entities.

| Bounded Context      | Aggregate Root(s)                      | Supporting Entities                     |
|----------------------|----------------------------------------|-----------------------------------------|
| Supplier Management  | Supplier                               | SupplierContact, SupplierPerformance    |
| Procurement          | PurchaseRequisition, PurchaseOrder     | RequisitionLine, POLine                 |
| Sourcing             | RFQ, Quotation                         | QuotationLine                           |
| Receiving            | GoodsReceipt                           | GoodsReceiptLine                        |
| Finance              | Invoice, ThreeWayMatch                 | InvoiceLine                             |
| Contract Management  | Contract                               | ContractClause                          |

---

## Supplier Domain

The `Supplier` aggregate root governs the full lifecycle of an external trading partner, from prospective onboarding through active engagement to potential suspension or blacklisting. The `status` field tracks the current lifecycle state, while `riskTier` classifies supplier risk exposure and is used in downstream procurement approval routing.

`SupplierContact` maintains the directory of authorised personnel associated with a supplier. The `isPrimary` flag designates the principal point of contact, and `isPortalUser` controls supplier portal access provisioning. `SupplierPerformance` captures rolling scorecard metrics per evaluation period, feeding into risk tier re-evaluation and contract renewal decision workflows.

---

## Procurement Domain

The `PurchaseRequisition` aggregate initiates the procurement cycle. It progresses through a configurable multi-tier approval workflow based on total amount and spend category before conversion to a `PurchaseOrder`. `RequisitionLine` items carry item-level detail including category classification codes used for spend analytics and approval threshold routing.

The `RFQ` aggregate supports competitive sourcing when no pre-negotiated contract exists. `PurchaseOrder` represents the legally binding procurement instrument issued to a supplier, optionally referencing a `Contract` for pre-negotiated pricing and terms. `POLine` items track ordered versus received quantities to support partial fulfilment and backorder management.

---

## Sourcing Domain

The `RFQ` aggregate manages the competitive bidding process. Upon publication, invited suppliers submit `Quotation` aggregates through the supplier portal. Each `QuotationLine` captures unit pricing, lead times, and supplier-specific notes. The `evaluateBids()` operation applies weighted scoring against the `evaluationCriteria` to identify the optimal quotation for award. Unawarded quotations transition to a `Rejected` status upon RFQ closure.

---

## Goods Receipt and Invoice Domain

The `GoodsReceipt` aggregate is created by warehouse personnel upon physical receipt of goods. It records quantities received, accepted, and rejected per line to support partial acceptance workflows. Quality rejections are flagged against the relevant `SupplierPerformance` record for scorecard deduction.

The `Invoice` aggregate enters the system via supplier portal submission or automated OCR extraction from PDF attachments. The `match()` operation initiates three-way matching against the corresponding `PurchaseOrder` and `GoodsReceipt`. The `ThreeWayMatch` aggregate records variance calculations and determines whether manual review is required based on configurable tolerance thresholds.

---

## Contract Domain

The `Contract` aggregate governs the terms and conditions applicable to procurement activities with a specific supplier. It supports multiple contract types including Framework Agreements, Blanket Purchase Orders, and Service Level Agreements. `ContractClause` entities capture individual contractual provisions, including mandatory compliance clauses and optional commercial terms. The `isExpiring()` method drives proactive renewal notification workflows configured in days prior to expiry.

---

## Complete Class Hierarchy

The following diagram presents the unified class model across all bounded contexts, with cross-domain associations annotated with explicit cardinality multiplicity.

```mermaid
classDiagram
    class Supplier {
        +UUID supplierId
        +String supplierCode
        +String legalName
        +String tradeName
        +String taxId
        +String countryCode
        +String currencyCode
        +SupplierStatus status
        +RiskTier riskTier
        +DateTime onboardedAt
        +String paymentTerms
        +Decimal creditLimit
        +create() Supplier
        +update() void
        +activate() void
        +suspend(reason: String) void
        +blacklist(reason: String) void
        +getPerformanceScore() Decimal
    }

    class SupplierContact {
        +UUID contactId
        +UUID supplierId
        +String firstName
        +String lastName
        +String email
        +String phone
        +String role
        +Boolean isPrimary
        +Boolean isPortalUser
        +create() SupplierContact
        +update() void
        +deactivate() void
    }

    class SupplierPerformance {
        +UUID performanceId
        +UUID supplierId
        +Date periodStart
        +Date periodEnd
        +Decimal deliveryScore
        +Decimal qualityScore
        +Decimal priceScore
        +Decimal responsivenessScore
        +Decimal overallScore
        +Int totalOrders
        +Int onTimeDeliveries
        +Int qualityRejections
        +calculate() void
        +getScoreCard() ScoreCard
        +flagForReview() void
    }

    class PurchaseRequisition {
        +UUID requisitionId
        +String requisitionNumber
        +UUID requesterId
        +UUID departmentId
        +Decimal totalAmount
        +String currency
        +RequisitionStatus status
        +Priority priority
        +Date neededByDate
        +String justification
        +List~RequisitionLine~ lines
        +create() PurchaseRequisition
        +submit() void
        +approve() void
        +reject(reason: String) void
        +convertToPO() PurchaseOrder
        +addLine(line: RequisitionLine) void
    }

    class RequisitionLine {
        +UUID lineId
        +UUID requisitionId
        +Int lineNumber
        +String itemCode
        +String description
        +Decimal quantity
        +String unitOfMeasure
        +Decimal unitPrice
        +Decimal lineTotal
        +String categoryCode
        +update() void
        +delete() void
    }

    class RFQ {
        +UUID rfqId
        +String rfqNumber
        +UUID requisitionId
        +Date submissionDeadline
        +Date evaluationDate
        +RFQStatus status
        +Int minQuoteCount
        +String evaluationCriteria
        +List~Quotation~ quotations
        +create() RFQ
        +publish() void
        +close() void
        +evaluateBids() Quotation
        +awardTo(supplierId: UUID) void
    }

    class PurchaseOrder {
        +UUID poId
        +String poNumber
        +UUID requisitionId
        +UUID supplierId
        +UUID contractId
        +Decimal totalAmount
        +String currency
        +POStatus status
        +String paymentTerms
        +Date deliveryDate
        +String shipToAddress
        +String incoterms
        +List~POLine~ lines
        +create() PurchaseOrder
        +issue() void
        +confirm() void
        +cancel(reason: String) void
        +receiveGoods() GoodsReceipt
        +addLine(line: POLine) void
    }

    class POLine {
        +UUID lineId
        +UUID poId
        +Int lineNumber
        +String itemCode
        +String description
        +Decimal orderedQty
        +Decimal receivedQty
        +String unitOfMeasure
        +Decimal unitPrice
        +Decimal lineTotal
        +Date promisedDate
        +update() void
    }

    class Quotation {
        +UUID quotationId
        +UUID rfqId
        +UUID supplierId
        +Decimal totalAmount
        +String currency
        +Date validityDate
        +QuotationStatus status
        +DateTime submittedAt
        +List~QuotationLine~ lines
        +submit() void
        +withdraw() void
        +award() void
        +reject() void
    }

    class QuotationLine {
        +UUID lineId
        +UUID quotationId
        +Int lineNumber
        +String itemCode
        +Decimal quantity
        +String unitOfMeasure
        +Decimal unitPrice
        +Decimal lineTotal
        +Int leadTimeDays
        +String notes
    }

    class GoodsReceipt {
        +UUID receiptId
        +String receiptNumber
        +UUID poId
        +UUID receivedBy
        +UUID warehouseId
        +Date receiptDate
        +ReceiptStatus status
        +String carrierName
        +String trackingNumber
        +List~GoodsReceiptLine~ lines
        +create() GoodsReceipt
        +record() void
        +verify() void
        +reportDiscrepancy() void
        +accept() void
    }

    class GoodsReceiptLine {
        +UUID lineId
        +UUID receiptId
        +UUID poLineId
        +Int lineNumber
        +String itemCode
        +Decimal receivedQty
        +Decimal acceptedQty
        +Decimal rejectedQty
        +String rejectionReason
        +String batchNumber
        +String serialNumbers
        +record() void
        +reportQualityIssue() void
    }

    class Invoice {
        +UUID invoiceId
        +String invoiceNumber
        +String externalInvoiceNumber
        +UUID supplierId
        +UUID poId
        +Decimal totalAmount
        +Decimal taxAmount
        +String currency
        +InvoiceStatus status
        +Date invoiceDate
        +Date dueDate
        +String paymentMethod
        +List~InvoiceLine~ lines
        +receive() void
        +validate() void
        +match() ThreeWayMatch
        +approve() void
        +dispute(reason: String) void
        +schedulePayment() void
    }

    class InvoiceLine {
        +UUID lineId
        +UUID invoiceId
        +UUID poLineId
        +Int lineNumber
        +String itemCode
        +Decimal invoicedQty
        +Decimal unitPrice
        +Decimal lineTotal
        +Decimal taxAmount
        +update() void
    }

    class ThreeWayMatch {
        +UUID matchId
        +UUID invoiceId
        +UUID poId
        +UUID receiptId
        +MatchStatus matchStatus
        +Decimal varianceAmount
        +Decimal variancePercent
        +DateTime matchedAt
        +String exceptions
        +execute() void
        +getVariance() Decimal
        +requiresManualReview() Boolean
        +approve() void
        +reject(reason: String) void
    }

    class Contract {
        +UUID contractId
        +String contractNumber
        +UUID supplierId
        +ContractType contractType
        +ContractStatus status
        +Date effectiveDate
        +Date expiryDate
        +Decimal totalValue
        +String currency
        +Boolean autoRenew
        +Int renewalNoticeDays
        +List~ContractClause~ clauses
        +create() Contract
        +submit() void
        +approve() void
        +activate() void
        +terminate(reason: String) void
        +renew() Contract
        +isExpiring(daysAhead: Int) Boolean
    }

    class ContractClause {
        +UUID clauseId
        +UUID contractId
        +String clauseNumber
        +ClauseType clauseType
        +String title
        +String content
        +Boolean isMandatory
        +Date effectiveDate
        +addToContract() void
        +update() void
        +remove() void
    }

    %% Supplier Domain Relationships
    Supplier "1" --> "many" SupplierContact : has
    Supplier "1" --> "many" SupplierPerformance : evaluated by
    Supplier "1" --> "many" PurchaseOrder : fulfils
    Supplier "1" --> "many" Quotation : submits
    Supplier "1" --> "many" Contract : governed by

    %% Procurement Domain Relationships
    PurchaseRequisition "1" --> "many" RequisitionLine : contains
    PurchaseRequisition "1" --> "0..1" PurchaseOrder : converts to
    PurchaseRequisition "1" --> "0..1" RFQ : initiates

    %% Sourcing Relationships
    RFQ "1" --> "many" Quotation : receives

    %% Purchase Order Relationships
    PurchaseOrder "1" --> "many" POLine : contains
    PurchaseOrder "1" --> "many" GoodsReceipt : fulfilled by
    PurchaseOrder "1" --> "many" Invoice : billed via

    %% Receiving and Finance Relationships
    GoodsReceipt "1" --> "many" GoodsReceiptLine : records
    Invoice "1" --> "many" InvoiceLine : itemised by
    Invoice "1" --> "0..1" ThreeWayMatch : validated by

    %% Contract Relationships
    Contract "1" --> "many" ContractClause : governed by
```

---

## Enumeration Reference

The following enumeration types are referenced across the domain model. All enumerations are defined as sealed types within their respective bounded context packages and are versioned alongside their owning aggregate.

### SupplierStatus

`Prospective | UnderReview | Approved | Active | Suspended | Blacklisted`

### RiskTier

`Low | Medium | High | Critical`

### RequisitionStatus

`Draft | Submitted | UnderReview | Approved | Rejected | POCreated | Cancelled | Closed`

### POStatus

`Draft | Issued | Confirmed | PartiallyReceived | FullyReceived | Invoiced | Paid | Closed | Cancelled`

### RFQStatus

`Draft | Published | Closed | Evaluated | Awarded | Cancelled`

### QuotationStatus

`Draft | Submitted | UnderEvaluation | Awarded | Rejected | Withdrawn`

### ReceiptStatus

`Pending | PartiallyReceived | FullyReceived | Discrepancy | Verified`

### InvoiceStatus

`Received | UnderReview | Matched | Disputed | Approved | Paid | Cancelled`

### MatchStatus

`Pending | Matched | VarianceDetected | ManualReviewRequired | Approved | Rejected`

### ContractStatus

`Draft | UnderReview | Approved | Active | Expiring | Expired | Terminated`

### ContractType

`Framework | SpotPurchase | BlanketOrder | ServiceLevelAgreement | ConsignmentAgreement`

### ClauseType

`PaymentTerms | DeliveryTerms | WarrantyTerms | PenaltyClause | Confidentiality | Termination | ForceMajeure | IntellectualProperty`

### Priority

`Low | Medium | High | Critical`
