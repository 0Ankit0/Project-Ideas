# System Sequence Diagrams — Supply Chain Management Platform

These diagrams capture the system-level interactions between external actors and major
internal services. They are intentionally kept at the boundary level; detailed internal
service interactions are documented in `detailed-design/sequence-diagrams.md`.

---

## 1. Purchase Requisition to PO Issuance

A requester raises a purchase requisition through the procurement portal. The PR passes
through multi-level approval before the PO Service converts the approved PR into a
purchase order, sends it to the supplier portal, and notifies all stakeholders.

```mermaid
sequenceDiagram
    autonumber
    actor Requester as Requester<br/>(Procurement Portal)
    participant GW as API Gateway
    participant PRS as PR Service
    participant AE as Approval Engine
    participant POS as PO Service
    participant SP as Supplier Portal
    participant NS as Notification Service

    Requester->>GW: POST /v1/purchase-requests<br/>{ items, quantities, needed_by, cost_center }
    GW->>GW: Authenticate JWT / RBAC check
    GW->>PRS: createPurchaseRequest(payload)
    PRS->>PRS: Validate item catalog & UOM
    PRS->>PRS: Compute estimated total (price list lookup)
    PRS->>PRS: Persist PR with status=DRAFT
    PRS-->>GW: 201 Created { prId, status: DRAFT }
    GW-->>Requester: 201 { prId }

    Requester->>GW: POST /v1/purchase-requests/{prId}/submit
    GW->>PRS: submitPR(prId)
    PRS->>PRS: Validate completeness (all required fields)
    PRS->>AE: initiateApprovalWorkflow(prId, totalAmount, costCenter)
    AE->>AE: Resolve approval chain<br/>(amount thresholds + org hierarchy)
    AE->>AE: Assign Level-1 approver
    AE-->>PRS: workflowId, firstApprover
    PRS->>PRS: Update PR status=PENDING_APPROVAL
    PRS->>NS: publishEvent(PR_SUBMITTED, { prId, approver })
    NS->>NS: Route notification (email + in-app)
    NS-->>Requester: Email: "PR submitted, awaiting approval"
    PRS-->>GW: 200 { prId, status: PENDING_APPROVAL, workflowId }
    GW-->>Requester: 200 OK

    Note over AE: Level-1 Approver reviews in portal

    AE->>AE: Approver submits decision=APPROVED
    AE->>AE: Check if further approval levels required
    AE->>AE: Total > $50k → escalate to Level-2
    AE->>NS: publishEvent(PR_APPROVED_L1, { prId, nextApprover })
    NS-->>AE: Level-2 approver notified

    Note over AE: Level-2 Approver reviews and approves

    AE->>AE: All levels approved → set PR FULLY_APPROVED
    AE->>PRS: notifyFullApproval(prId)
    PRS->>PRS: Update PR status=APPROVED
    PRS->>NS: publishEvent(PR_FULLY_APPROVED, { prId, requester })
    NS-->>Requester: Email + push: "PR approved"

    PRS->>POS: convertToPO(prId)
    POS->>POS: Load approved PR lines
    POS->>POS: Determine sourcing (preferred supplier, price list)
    POS->>POS: Apply currency conversion if multi-entity
    POS->>POS: Persist PO with status=DRAFT
    POS->>POS: Run duplicate-PO check
    POS->>POS: Update PO status=PENDING_SUPPLIER_SEND
    POS->>SP: sendPO(poId, supplierPortalUserId)
    SP->>SP: Render PO in supplier-facing UI
    SP-->>POS: 202 Accepted (async delivery confirmation)
    POS->>NS: publishEvent(PO_SENT, { poId, supplierId })
    NS-->>Requester: Email: "PO #{poId} sent to supplier"
    POS-->>PRS: poId, status=SENT_TO_SUPPLIER
    PRS->>PRS: Link PR → PO (prId.poRef = poId)

    Note over SP: Supplier logs in, reviews PO

    SP->>GW: PUT /v1/purchase-orders/{poId}/acknowledge
    GW->>POS: acknowledgePO(poId, { confirmedDeliveryDate })
    POS->>POS: Update PO status=ACKNOWLEDGED
    POS->>NS: publishEvent(PO_ACKNOWLEDGED, { poId, confirmedDeliveryDate })
    NS-->>Requester: "Supplier confirmed delivery by {date}"
```

---

## 2. Three-Way Invoice Matching

The supplier submits an invoice via the portal. The Matching Engine correlates the
invoice against the corresponding purchase order and goods receipt. On a clean match the
invoice is auto-approved and queued for payment; on a discrepancy a dispute ticket is
raised.

```mermaid
sequenceDiagram
    autonumber
    actor Supplier as Supplier<br/>(Supplier Portal)
    participant GW as API Gateway
    participant IS as Invoice Service
    participant ME as Matching Engine
    participant POS as PO Service
    participant RS as Receipt Service
    participant APD as AP Dashboard<br/>(Buyer)
    participant PS as Payment Service
    participant NS as Notification Service

    Supplier->>GW: POST /v1/invoices<br/>{ poId, lines[], totalAmount, invoiceDate, currency }
    GW->>GW: Authenticate supplier JWT
    GW->>IS: createInvoice(payload)
    IS->>IS: Validate invoice number uniqueness
    IS->>IS: Validate currency & tax codes
    IS->>IS: Persist Invoice status=RECEIVED
    IS->>ME: triggerMatch(invoiceId)
    IS-->>GW: 201 { invoiceId, status: RECEIVED }
    GW-->>Supplier: 201 Created

    ME->>POS: getPODetails(poId)
    POS-->>ME: { poLines[], unitPrices[], tolerances[], currency }
    ME->>RS: getReceiptsByPO(poId)
    RS-->>ME: { receipts[], receivedQty[], qualityStatus[] }

    ME->>ME: Perform three-way match
    ME->>ME: Check 1: Invoice qty ≤ PO qty
    ME->>ME: Check 2: Invoice price within tolerance (±2%)
    ME->>ME: Check 3: Received qty covers invoice qty
    ME->>ME: Check 4: Quality inspections passed

    alt All checks pass — clean match
        ME->>ME: Set match status=MATCHED, confidence=100%
        ME->>IS: updateInvoiceStatus(invoiceId, MATCHED)
        IS->>IS: Persist match result
        ME->>NS: publishEvent(INVOICE_MATCHED, { invoiceId, poId })
        NS-->>APD: AP Dashboard notification: "Invoice auto-approved"
        APD->>PS: schedulePayment(invoiceId, dueDate)
        PS->>PS: Calculate due date (net-30 / early-pay discount check)
        PS->>PS: Create payment run record status=SCHEDULED
        PS->>NS: publishEvent(PAYMENT_SCHEDULED, { invoiceId, amount, dueDate })
        NS-->>Supplier: "Invoice accepted. Payment scheduled for {date}"
    else Price variance within tolerance but flagged
        ME->>ME: Set match status=MATCHED_WITH_VARIANCE
        ME->>IS: updateInvoiceStatus(invoiceId, MATCHED_WITH_VARIANCE)
        ME->>NS: publishEvent(INVOICE_VARIANCE, { invoiceId, varianceAmount })
        NS-->>APD: "Review required — price variance ${amount}"
        APD->>IS: manualApprove(invoiceId, approverId)
        IS->>IS: Status → APPROVED
        IS->>PS: schedulePayment(invoiceId, dueDate)
        PS-->>NS: PAYMENT_SCHEDULED event
        NS-->>Supplier: Payment confirmation
    else Hard mismatch — raise dispute
        ME->>ME: Set match status=MISMATCH
        ME->>IS: updateInvoiceStatus(invoiceId, DISPUTED)
        ME->>IS: createDispute(invoiceId, { reason, discrepancyLines[] })
        IS->>NS: publishEvent(INVOICE_DISPUTED, { invoiceId, supplierId, reason })
        NS-->>Supplier: "Invoice disputed: {reason}. Please review."
        NS-->>APD: "Dispute raised on invoice #{invoiceId}"
    end

    Note over PS: On payment due date (scheduled job)

    PS->>PS: Execute payment run
    PS->>PS: Call bank / payment gateway API
    PS->>PS: Update payment status=PAID
    PS->>IS: markInvoicePaid(invoiceId, paymentRef)
    IS->>IS: Update Invoice status=PAID
    PS->>NS: publishEvent(PAYMENT_EXECUTED, { invoiceId, paymentRef, amount })
    NS-->>Supplier: "Payment of ${amount} executed. Ref: {paymentRef}"
```

---

## 3. Supplier Performance Scoring

A nightly scheduled job triggers the Performance Service to recompute KPI scores for
all active suppliers. Scores are persisted, surfaced on the supplier portal, and alerts
are sent for suppliers breaching SLA thresholds.

```mermaid
sequenceDiagram
    autonumber
    participant SCH as Scheduler Job<br/>(Cron/Airflow)
    participant PFS as Performance Service
    participant POS as PO Service
    participant RS as Receipt Service
    participant KPI as KPI Calculator
    participant DB as Performance DB
    participant SP as Supplier Portal
    participant NS as Notification Service

    SCH->>PFS: triggerScoringRun(runDate, scope=ALL_ACTIVE_SUPPLIERS)
    PFS->>PFS: Fetch list of active suppliers (last 90 days activity)
    PFS->>PFS: Initialize scoring run record

    loop For each supplier
        PFS->>POS: getPOsForSupplier(supplierId, period=last90days)
        POS-->>PFS: { orders[], confirmedDeliveryDates[], actualDeliveryDates[] }

        PFS->>RS: getReceiptsForSupplier(supplierId, period=last90days)
        RS-->>PFS: { receipts[], qualityPassRate[], rejectedQty[] }

        PFS->>KPI: calculateOTD(orders, receipts)
        KPI->>KPI: OTD = (on-time deliveries / total deliveries) * 100
        KPI->>KPI: Weight late penalties by days-late buckets
        KPI-->>PFS: { otdScore, onTimeCount, lateCount, avgDaysLate }

        PFS->>KPI: calculateQualityScore(receipts)
        KPI->>KPI: Quality = (accepted qty / total received qty) * 100
        KPI->>KPI: Apply DPPM (defects per million parts) if available
        KPI-->>PFS: { qualityScore, acceptedQty, rejectedQty, dppm }

        PFS->>KPI: calculateComplianceScore(supplierId)
        KPI->>KPI: Check document expiry (certs, insurance, audits)
        KPI->>KPI: Check PO acknowledgment rate
        KPI->>KPI: Check invoice accuracy rate
        KPI-->>PFS: { complianceScore, expiredDocs[], ackRate, invoiceAccuracy }

        PFS->>KPI: computeCompositeScore(otdScore, qualityScore, complianceScore)
        KPI->>KPI: Weighted avg: OTD(40%) + Quality(35%) + Compliance(25%)
        KPI-->>PFS: { compositeScore, tier: GOLD|SILVER|BRONZE|AT_RISK }

        PFS->>DB: upsertPerformanceRecord(supplierId, runDate, scores)
        DB-->>PFS: persisted

        PFS->>PFS: Compare composite score against SLA thresholds
        alt Score < SLA minimum threshold (e.g., < 70)
            PFS->>NS: publishEvent(SUPPLIER_AT_RISK, { supplierId, compositeScore, breachedKPIs })
            NS-->>SP: In-portal alert for supplier: "Performance below threshold"
            NS->>NS: Email procurement manager: "Supplier {name} at risk"
        else Score improved crossing GOLD tier boundary
            PFS->>NS: publishEvent(SUPPLIER_TIER_UPGRADE, { supplierId, newTier: GOLD })
            NS-->>SP: Badge update + notification for supplier
        end

        PFS->>SP: publishScorecard(supplierId, { scores, trends, benchmarks })
        SP->>SP: Update supplier-facing scorecard UI
    end

    PFS->>PFS: Finalize scoring run, set status=COMPLETED
    PFS->>NS: publishEvent(SCORING_RUN_COMPLETE, { runDate, suppliersScored, atRiskCount })
    NS->>NS: Send daily digest to procurement leadership
    SCH-->>SCH: Log run completion, schedule next run
```

---

## Summary

| Diagram | Key Integration Points | Async Events Published |
|---|---|---|
| PR → PO Issuance | PR Service, Approval Engine, PO Service | PR_SUBMITTED, PR_FULLY_APPROVED, PO_SENT, PO_ACKNOWLEDGED |
| Three-Way Matching | Invoice Service, Matching Engine, PO/Receipt | INVOICE_MATCHED, INVOICE_DISPUTED, PAYMENT_SCHEDULED, PAYMENT_EXECUTED |
| Performance Scoring | Performance Service, KPI Calculator, Supplier Portal | SUPPLIER_AT_RISK, SUPPLIER_TIER_UPGRADE, SCORING_RUN_COMPLETE |
