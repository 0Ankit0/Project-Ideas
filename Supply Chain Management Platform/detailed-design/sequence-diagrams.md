# Sequence Diagrams — Supply Chain Management Platform

## Overview

This document presents the interaction sequence diagrams for the Supply Chain Management (SCM) Platform's key operational workflows. Each diagram captures the message exchange between actors, application services, and infrastructure components across the procurement and supply chain lifecycle.

The diagrams follow UML sequenceDiagram notation rendered via Mermaid, incorporating synchronous requests (`->>`), asynchronous responses (`-->>`), conditional branches (`alt/else`), iteration (`loop`), optional blocks (`opt`), and contextual notes. Service boundaries reflect the platform's microservices decomposition, with each service owning its domain data store.

---

## Purchase Requisition Creation and Approval

The purchase requisition workflow initiates the procurement cycle. A requester drafts a requisition with line items and submits it for multi-tier approval. The `ApprovalService` determines the approval chain based on configured amount thresholds—manager approval below $10,000, director approval up to $50,000, and CFO approval above that level. Each tier receives real-time notifications and must act within configured SLA windows before automatic escalation.

```mermaid
sequenceDiagram
    actor Requester
    actor Approver
    participant WebApp
    participant ProcurementService
    participant ApprovalService
    participant NotificationService
    participant DB as ProcurementDB

    Requester->>WebApp: Create requisition with line items
    WebApp->>ProcurementService: POST /requisitions
    ProcurementService->>DB: Save requisition (DRAFT)
    ProcurementService-->>WebApp: 201 Created {requisitionId}

    Requester->>WebApp: Submit requisition for approval
    WebApp->>ProcurementService: POST /requisitions/{id}/submit
    ProcurementService->>ProcurementService: Validate requisition completeness
    ProcurementService->>ApprovalService: InitiateApprovalWorkflow(requisitionId, amount)
    ApprovalService->>ApprovalService: Determine approver chain by amount threshold
    ApprovalService->>DB: Create approval record (PENDING)
    ApprovalService->>NotificationService: SendApprovalRequest(approverId, requisitionId)
    NotificationService-->>Approver: Email and in-app notification
    ProcurementService->>DB: Update status to SUBMITTED
    ProcurementService-->>WebApp: 200 OK {status: SUBMITTED}

    Approver->>WebApp: Review requisition and line items
    WebApp->>ProcurementService: GET /requisitions/{id}
    ProcurementService-->>WebApp: Requisition detail with lines

    alt Approver approves requisition
        Approver->>WebApp: Approve requisition
        WebApp->>ApprovalService: POST /approvals/{id}/approve
        ApprovalService->>ProcurementService: ApprovalGranted(requisitionId)
        ProcurementService->>DB: Update status to APPROVED
        ProcurementService->>NotificationService: NotifyRequester(requisitionId, approved)
        NotificationService-->>Requester: Approval confirmation notification
        ApprovalService-->>WebApp: 200 OK {status: APPROVED}
    else Approver rejects requisition
        Approver->>WebApp: Reject with reason
        WebApp->>ApprovalService: POST /approvals/{id}/reject {reason}
        ApprovalService->>ProcurementService: ApprovalRejected(requisitionId, reason)
        ProcurementService->>DB: Update status to REJECTED
        ProcurementService->>NotificationService: NotifyRequester(requisitionId, rejected, reason)
        NotificationService-->>Requester: Rejection notification with reason
    else Approver requests more information
        Approver->>WebApp: Request clarification
        WebApp->>ApprovalService: POST /approvals/{id}/request-info {comment}
        ApprovalService->>ProcurementService: InfoRequested(requisitionId)
        ProcurementService->>DB: Update status back to SUBMITTED
        ProcurementService->>NotificationService: NotifyRequester(infoRequired, comment)
        NotificationService-->>Requester: Clarification request notification
    end
```

---

## RFQ Process and Supplier Bidding

The RFQ (Request for Quotation) process supports competitive sourcing when no pre-negotiated contract is in place. The buyer publishes an RFQ with itemised requirements and a submission deadline. Invited suppliers receive portal notifications and submit structured quotations. Upon deadline closure, the procurement team evaluates bids using weighted scoring criteria and awards the contract to the winning supplier, triggering automatic PO creation.

```mermaid
sequenceDiagram
    actor Buyer
    actor Supplier
    participant WebApp
    participant SupplierPortal
    participant ProcurementService
    participant NotificationService
    participant DB as ProcurementDB

    Buyer->>WebApp: Create RFQ from approved requisition
    WebApp->>ProcurementService: POST /rfqs
    ProcurementService->>DB: Save RFQ (DRAFT)
    ProcurementService-->>WebApp: 201 Created {rfqId}

    Buyer->>WebApp: Add invited suppliers and set submission deadline
    WebApp->>ProcurementService: POST /rfqs/{id}/publish
    ProcurementService->>DB: Update RFQ status to PUBLISHED
    ProcurementService->>NotificationService: NotifyInvitedSuppliers(rfqId, supplierIds, deadline)
    NotificationService-->>Supplier: RFQ invitation email with portal access link

    loop For each invited supplier before deadline
        Supplier->>SupplierPortal: Access and review RFQ requirements
        Supplier->>SupplierPortal: Prepare quotation with line pricing and lead times
        SupplierPortal->>ProcurementService: POST /rfqs/{id}/quotations
        ProcurementService->>DB: Save quotation (SUBMITTED)
        ProcurementService->>NotificationService: NotifyBuyer(quotationReceived, rfqId)
        NotificationService-->>Buyer: New quotation received notification
    end

    Buyer->>WebApp: Close RFQ at submission deadline
    WebApp->>ProcurementService: POST /rfqs/{id}/close
    ProcurementService->>DB: Update RFQ status to CLOSED

    Buyer->>WebApp: Initiate bid evaluation
    WebApp->>ProcurementService: POST /rfqs/{id}/evaluate
    ProcurementService->>ProcurementService: Apply weighted scoring to all submitted quotations
    ProcurementService->>DB: Update status to EVALUATED
    ProcurementService-->>WebApp: Ranked quotation list with evaluation scores

    Buyer->>WebApp: Award RFQ to winning supplier
    WebApp->>ProcurementService: POST /rfqs/{id}/award {supplierId, quotationId}
    ProcurementService->>DB: Update RFQ to AWARDED, winning Quotation to AWARDED
    ProcurementService->>ProcurementService: CreatePurchaseOrder(quotationId)
    ProcurementService->>NotificationService: NotifyWinningSupplier(supplierId, poId)
    ProcurementService->>NotificationService: NotifyUnsuccessfulSuppliers(rfqId)
    NotificationService-->>Supplier: Award or rejection notification
    ProcurementService-->>WebApp: 200 OK {poId}
```

---

## Purchase Order Creation and Confirmation

Following requisition approval or RFQ award, a Purchase Order is created and formally issued to the supplier. The supplier reviews the PO via the supplier portal and either confirms with a committed delivery date or requests an amendment. Confirmation creates a binding fulfilment commitment that triggers downstream receiving and scheduling workflows. Amendment requests are routed back to the buyer for review before the PO is re-issued.

```mermaid
sequenceDiagram
    actor Buyer
    actor Supplier
    participant WebApp
    participant SupplierPortal
    participant ProcurementService
    participant NotificationService
    participant DB as ProcurementDB

    Buyer->>WebApp: Create PO from approved requisition or quotation award
    WebApp->>ProcurementService: POST /purchase-orders
    ProcurementService->>DB: Save PO (DRAFT)
    ProcurementService-->>WebApp: 201 Created {poId}

    Buyer->>WebApp: Issue PO to supplier
    WebApp->>ProcurementService: POST /purchase-orders/{id}/issue
    ProcurementService->>DB: Update PO status to ISSUED
    ProcurementService->>NotificationService: NotifySupplier(supplierId, poId)
    NotificationService-->>Supplier: PO issued notification with portal link

    Note right of Supplier: SLA confirmation window starts

    Supplier->>SupplierPortal: Review PO line items, pricing, and delivery terms
    SupplierPortal->>ProcurementService: GET /purchase-orders/{id}
    ProcurementService-->>SupplierPortal: PO detail with all line items

    alt Supplier confirms PO
        Supplier->>SupplierPortal: Confirm PO with committed delivery date
        SupplierPortal->>ProcurementService: POST /purchase-orders/{id}/confirm {deliveryDate}
        ProcurementService->>DB: Update status to CONFIRMED, persist deliveryDate
        ProcurementService->>NotificationService: NotifyBuyer(poConfirmed, poId, deliveryDate)
        NotificationService-->>Buyer: PO confirmed with delivery commitment
        ProcurementService-->>SupplierPortal: 200 OK {status: CONFIRMED}
    else Supplier requests amendment
        Supplier->>SupplierPortal: Submit amendment request with justification
        SupplierPortal->>ProcurementService: POST /purchase-orders/{id}/amendments
        ProcurementService->>DB: Save amendment request (PENDING)
        ProcurementService->>NotificationService: NotifyBuyer(amendmentRequested, poId)
        NotificationService-->>Buyer: Amendment request notification

        Buyer->>WebApp: Review amendment details
        WebApp->>ProcurementService: GET /purchase-orders/{id}/amendments/{amendId}
        ProcurementService-->>WebApp: Amendment request details

        alt Buyer accepts amendment
            Buyer->>WebApp: Accept amendment
            WebApp->>ProcurementService: POST /purchase-orders/{id}/amendments/{amendId}/accept
            ProcurementService->>DB: Update PO with amended terms, reissue
            ProcurementService->>NotificationService: NotifySupplier(amendmentAccepted, poId)
            NotificationService-->>Supplier: Amendment accepted, updated PO available
        else Buyer rejects amendment
            Buyer->>WebApp: Reject amendment with reason
            WebApp->>ProcurementService: POST /purchase-orders/{id}/amendments/{amendId}/reject
            ProcurementService->>NotificationService: NotifySupplier(amendmentRejected, reason)
            NotificationService-->>Supplier: Amendment rejected, original PO stands
        end
    end
```

---

## Goods Receipt Recording

Upon physical arrival of goods at the warehouse, receiving staff record actual quantities delivered against the open PO. The `ReceivingService` validates receipt quantities against ordered quantities and applies configurable tolerance thresholds. Discrepancies trigger notification workflows to procurement and quality teams, while accepted receipts emit domain events to signal invoice matching readiness to the finance domain.

```mermaid
sequenceDiagram
    actor WarehouseStaff
    actor FinanceTeam
    actor Buyer
    participant WarehouseApp
    participant ReceivingService
    participant ProcurementService
    participant NotificationService
    participant DB as WarehouseDB

    WarehouseStaff->>WarehouseApp: Scan barcode or enter PO reference
    WarehouseApp->>ReceivingService: GET /purchase-orders/{id}/expected-receipt
    ReceivingService->>DB: Fetch open PO lines and expected quantities
    ReceivingService-->>WarehouseApp: Expected receipt detail with line items

    WarehouseStaff->>WarehouseApp: Record received quantities and batch numbers per line
    WarehouseApp->>ReceivingService: POST /goods-receipts {poId, lines[], carrierName, trackingNumber}
    ReceivingService->>ReceivingService: Compare received qty against ordered qty per line

    alt All quantities within configured tolerance
        ReceivingService->>DB: Save GoodsReceipt (VERIFIED)
        ReceivingService->>ProcurementService: GoodsReceivedEvent(poId, receiptId)
        ProcurementService->>DB: Update PO status to PartiallyReceived or FullyReceived
        ReceivingService->>NotificationService: NotifyFinance(receiptReadyForMatching, receiptId)
        NotificationService-->>FinanceTeam: Invoice matching readiness notification
        ReceivingService-->>WarehouseApp: 201 Created {receiptId, status: VERIFIED}
    else Quantity discrepancy detected
        ReceivingService->>DB: Save GoodsReceipt (DISCREPANCY)
        ReceivingService->>NotificationService: NotifyProcurement(discrepancyDetected, poId, variance)
        NotificationService-->>Buyer: Discrepancy alert with line-level variance detail
        WarehouseStaff->>WarehouseApp: Document discrepancy reason per affected line
        WarehouseApp->>ReceivingService: POST /goods-receipts/{id}/discrepancy-report
        ReceivingService->>DB: Persist discrepancy report against receipt
        ReceivingService-->>WarehouseApp: 201 Created {receiptId, status: DISCREPANCY}
    end

    Note over ReceivingService: Partial receipts trigger incremental PO status updates
```

---

## Three-Way Match and Invoice Processing

Invoice processing begins upon receipt of a supplier invoice, either via structured portal submission or PDF upload with OCR extraction. The `MatchingService` executes a three-way match across the invoice, purchase order, and goods receipt. Variances within configured tolerance thresholds result in automatic approval and payment scheduling. Variances exceeding tolerance route the invoice to the finance manager for manual review and resolution.

```mermaid
sequenceDiagram
    actor FinanceClerk
    actor FinanceManager
    actor Supplier
    participant FinanceApp
    participant InvoiceService
    participant OCRService
    participant MatchingService
    participant NotificationService
    participant DB as FinanceDB

    alt Invoice received as PDF attachment
        FinanceClerk->>FinanceApp: Upload supplier invoice PDF
        FinanceApp->>OCRService: ExtractInvoiceData(pdfFile)
        OCRService-->>InvoiceService: Structured invoice fields {invoiceNumber, lines, totals}
    else Invoice submitted via supplier portal
        Supplier->>FinanceApp: POST /invoices {structured payload}
        FinanceApp->>InvoiceService: ReceiveInvoice(payload)
    end

    InvoiceService->>DB: Save invoice (RECEIVED)
    InvoiceService->>InvoiceService: Validate mandatory fields and PO reference
    InvoiceService->>DB: Update status to UNDER_REVIEW

    InvoiceService->>MatchingService: InitiateThreeWayMatch(invoiceId, poId)
    MatchingService->>DB: Fetch Invoice, PurchaseOrder, and GoodsReceipt records
    MatchingService->>MatchingService: Compare invoice qty vs PO qty vs received qty
    MatchingService->>MatchingService: Compare invoice unit price vs PO unit price
    MatchingService->>MatchingService: Calculate varianceAmount and variancePercent
    MatchingService->>DB: Persist ThreeWayMatch record with variance details

    alt Variance within configured tolerance
        MatchingService->>InvoiceService: MatchSuccessful(invoiceId)
        InvoiceService->>DB: Update Invoice status to MATCHED
        InvoiceService->>DB: Update ThreeWayMatch matchStatus to APPROVED
        InvoiceService->>InvoiceService: SchedulePayment(invoiceId, dueDate)
        InvoiceService->>NotificationService: NotifyFinance(invoiceScheduledForPayment, invoiceId)
        NotificationService-->>FinanceClerk: Invoice approved and payment scheduled
    else Variance exceeds configured tolerance
        MatchingService->>InvoiceService: VarianceDetected(invoiceId, varianceDetails)
        InvoiceService->>DB: Update Invoice status to DISPUTED
        InvoiceService->>NotificationService: NotifyFinanceManager(manualReviewRequired, invoiceId)
        NotificationService-->>FinanceManager: Manual review alert with variance breakdown

        FinanceManager->>FinanceApp: Review invoice and variance details
        FinanceApp->>InvoiceService: GET /invoices/{id}/match-details
        InvoiceService-->>FinanceApp: Three-way match result with line-level variance

        alt Finance manager approves with override
            FinanceManager->>FinanceApp: Approve invoice with override justification
            FinanceApp->>InvoiceService: POST /invoices/{id}/approve {override: true, justification}
            InvoiceService->>DB: Update status to APPROVED with audit record
            InvoiceService->>InvoiceService: SchedulePayment(invoiceId, dueDate)
        else Finance manager raises formal dispute
            FinanceManager->>FinanceApp: Dispute invoice with reason
            FinanceApp->>InvoiceService: POST /invoices/{id}/dispute {reason}
            InvoiceService->>NotificationService: NotifySupplier(invoiceDisputed, reason)
            NotificationService-->>Supplier: Invoice dispute notification with details
        end
    end
```

---

## Supplier Performance Review

Supplier performance reviews are triggered quarterly by a scheduled job. The `PerformanceService` collects KPI data from the procurement and receiving domains, computes weighted scores per dimension, and generates a scorecard. Suppliers scoring below the configured threshold are flagged for a formal review meeting with the procurement manager. Persistent underperformance may result in a risk tier escalation, which affects downstream approval routing thresholds.

```mermaid
sequenceDiagram
    actor ProcurementManager
    actor SupplierContact
    participant Scheduler
    participant PerformanceService
    participant ProcurementService
    participant SupplierService
    participant NotificationService
    participant DB as AnalyticsDB

    Scheduler->>PerformanceService: TriggerQuarterlyReview(periodStart, periodEnd)

    PerformanceService->>ProcurementService: GetDeliveryMetrics(supplierId, period)
    ProcurementService-->>PerformanceService: On-time delivery counts and late delivery data

    PerformanceService->>ProcurementService: GetQualityRejections(supplierId, period)
    ProcurementService-->>PerformanceService: Goods receipt rejection lines and reasons

    PerformanceService->>ProcurementService: GetPriceVariances(supplierId, period)
    ProcurementService-->>PerformanceService: Invoice price compliance data

    PerformanceService->>PerformanceService: CalculateKPIScores(delivery, quality, price, responsiveness)
    PerformanceService->>PerformanceService: ComputeWeightedOverallScore()
    PerformanceService->>DB: Persist SupplierPerformance record for period

    alt Overall score below minimum threshold
        PerformanceService->>NotificationService: NotifyProcurementManager(lowScore, supplierId, scorecard)
        NotificationService-->>ProcurementManager: Performance review alert with scorecard summary

        ProcurementManager->>PerformanceService: GET /suppliers/{id}/performance/{periodId}
        PerformanceService-->>ProcurementManager: Full scorecard with KPI breakdown

        ProcurementManager->>PerformanceService: POST /suppliers/{id}/performance/schedule-review
        PerformanceService->>NotificationService: NotifySupplier(reviewMeetingScheduled, supplierId)
        NotificationService-->>SupplierContact: Performance review meeting invitation

        opt Risk tier escalation required
            ProcurementManager->>PerformanceService: POST /suppliers/{id}/risk-tier {newTier}
            PerformanceService->>SupplierService: UpdateRiskTier(supplierId, newTier)
            SupplierService->>DB: Persist updated Supplier.riskTier
            PerformanceService->>NotificationService: NotifyProcurementTeam(riskTierChanged, supplierId)
        end
    else Score meets or exceeds threshold
        PerformanceService->>NotificationService: DistributeScorecard(supplierId, scorecard)
        NotificationService-->>SupplierContact: Quarterly performance scorecard report
    end

    Note over PerformanceService: Risk tier changes propagate to approval routing engine
```
