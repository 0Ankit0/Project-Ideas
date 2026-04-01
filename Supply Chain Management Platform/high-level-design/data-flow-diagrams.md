# Data Flow Diagrams — Supply Chain Management Platform

This document describes the movement of data across services, external systems, and
storage layers for the four principal workflows of the Supply Chain Management Platform.
Each diagram annotates both data in motion (Kafka events, REST payloads) and data at
rest (PostgreSQL schemas, Redis caches, Kafka topics, S3 buckets), together with the
actors who produce and consume each data element.

---

## Overview

| Flow | Initiating Actor | Terminal State | Primary Services |
|------|-----------------|----------------|-----------------|
| Procure-to-Pay | Procurement Officer | Payment Confirmed | ProcurementService, ReceivingService, InvoiceService, MatchingEngine, PaymentService |
| Supplier Onboarding | Supplier Representative | Supplier Activated | SupplierService, NotificationService |
| RFQ and Sourcing | Procurement Officer | Contract or PO Issued | RFQService, ProcurementService, ContractService |
| Performance Scoring | Platform Scheduler | Risk Tier Updated | PerformanceService, SupplierService, NotificationService |

All cross-service workflow progression is asynchronous via Kafka. Synchronous REST calls
through the API Gateway are reserved for user-facing queries and command submissions.
Services never call one another's REST APIs for workflow coordination.

---

## Procure-to-Pay Main Flow

The Procure-to-Pay (P2P) flow covers the complete lifecycle from an internal purchase
requisition raised by a procurement officer through goods receipt, invoice ingestion,
three-way matching, and final payment disbursement to the supplier.

```mermaid
flowchart TB
    subgraph actors["External Actors"]
        PO_USER([Procurement Officer])
        WH_USER([Warehouse Staff])
        FIN_USER([Finance Team])
        SUPPLIER([Supplier])
    end

    subgraph gw["API Layer"]
        APIGW[API Gateway\nJWT Validation]
    end

    subgraph services["Platform Services"]
        PROC[ProcurementService\nPR and PO Management]
        APPWF[Approval Workflow Engine\nMulti-level Rule Routing]
        RECV[ReceivingService\nGoods Receipt Recording]
        INVSVC[InvoiceService\nIngestion and OCR]
        MATCH[MatchingEngine\nThree-Way Match]
        PAYSVC[PaymentService\nScheduling and Dispatch]
        NOTIFY[NotificationService\nEmail and In-App]
    end

    subgraph storage["Data Stores"]
        DB_PROC[(PostgreSQL\nProcurement DB)]
        DB_FIN[(PostgreSQL\nFinance DB)]
        REDIS[(Redis\nApproval State Cache)]
        S3_INV[(S3\nInvoice Attachments)]
        KAFKA([Kafka\nEvent Bus])
    end

    subgraph external["External Systems"]
        ERP[ERP / SAP\nLedger Integration]
        BANK[Bank API\nPayment Rails]
        EMAIL[Email Gateway\nAWS SES]
    end

    PO_USER --> APIGW
    APIGW -->|Create PR| PROC
    PROC --> DB_PROC
    PROC -->|PurchaseRequisitionSubmitted| KAFKA
    KAFKA -->|PR Submitted| APPWF
    APPWF <--> REDIS
    APPWF -->|PurchaseRequisitionApproved| KAFKA
    KAFKA -->|PR Approved| PROC
    PROC -->|Issue PO| DB_PROC
    PROC -->|PurchaseOrderIssued| KAFKA
    KAFKA -->|PO Issued - Notify| NOTIFY
    NOTIFY --> EMAIL
    NOTIFY -.->|Supplier Notification| SUPPLIER

    WH_USER --> APIGW
    APIGW -->|Create Goods Receipt| RECV
    RECV --> DB_PROC
    RECV -->|GoodsReceiptCreated| KAFKA

    SUPPLIER --> APIGW
    APIGW -->|Submit Invoice| INVSVC
    INVSVC --> S3_INV
    INVSVC --> DB_FIN
    INVSVC -->|InvoiceReceived| KAFKA

    KAFKA -->|GR Created and Invoice Received| MATCH
    MATCH --> DB_FIN
    MATCH -->|ThreeWayMatchCompleted| KAFKA

    KAFKA -->|Match Approved| PAYSVC
    PAYSVC --> DB_FIN
    PAYSVC -->|PaymentDispatched| KAFKA
    PAYSVC --> BANK

    KAFKA -->|Payment Dispatched - ERP Sync| ERP
    KAFKA -->|Payment Confirmed - Notify| NOTIFY
    NOTIFY --> FIN_USER
```

### Key Event Payloads

| Stage | Kafka Event | Core Fields |
|-------|-------------|-------------|
| PR Creation | `PurchaseRequisitionSubmitted` | prId, requesterId, costCenter, lines[], totalAmount, currency |
| PR Approval | `PurchaseRequisitionApproved` | prId, approverId, approvedAt, approvalTier |
| PO Issuance | `PurchaseOrderIssued` | poId, prId, supplierId, lines[], deliveryDate, paymentTerms |
| Goods Receipt | `GoodsReceiptCreated` | grId, poId, receivedLines[], receivedAt, warehouseId |
| Invoice Submission | `InvoiceReceived` | invoiceId, supplierId, poId, lines[], invoiceDate, dueDate |
| Match Result | `ThreeWayMatchCompleted` | matchId, invoiceId, poId, grId, status, varianceAmount |
| Payment Dispatch | `PaymentDispatched` | paymentId, invoiceId, amount, currency, bankReference |

---

## Supplier Onboarding Data Flow

The supplier onboarding flow manages data collection, document verification, tax identity
checks, and risk assessment before a supplier is activated. Verification steps run in
parallel where data dependencies allow, with SupplierService acting as the saga
orchestrator that waits for all stage confirmations before enabling final qualification
review.

```mermaid
flowchart TB
    subgraph actors2["Actors"]
        SUP_REP([Supplier Representative])
        PROC_OFF([Procurement Officer])
    end

    subgraph portal["Supplier Portal"]
        REG_UI[Registration Form\nReact SPA]
        DOC_UI[Document Upload\nReact SPA]
    end

    subgraph svc2["Services"]
        SUPSVC[SupplierService\nOnboarding Orchestrator]
        NOTIFY2[NotificationService]
    end

    subgraph verify["Verification Adapters"]
        TAX_CHK[Tax ID Verifier\nExternal Registry API]
        DOC_CHK[Document Verifier\nOCR and Rules Engine]
        RISK_CHK[Risk Assessor\nCredit Bureau and Sanctions]
    end

    subgraph store2["Data Stores"]
        DB_SUP[(PostgreSQL\nSupplier DB)]
        S3_DOCS[(S3\nSupplier Documents)]
        REDIS_OB[(Redis\nOnboarding State)]
        KAFKA2([Kafka\nEvent Bus])
    end

    SUP_REP --> REG_UI
    REG_UI -->|POST /suppliers/register| SUPSVC
    SUPSVC --> DB_SUP
    SUPSVC -->|SupplierRegistered| KAFKA2

    SUP_REP --> DOC_UI
    DOC_UI -->|Upload Documents| SUPSVC
    SUPSVC --> S3_DOCS
    SUPSVC -->|DocumentsUploaded| KAFKA2

    KAFKA2 -->|Trigger Tax Verification| TAX_CHK
    KAFKA2 -->|Trigger Document Verification| DOC_CHK
    KAFKA2 -->|Trigger Risk Assessment| RISK_CHK

    TAX_CHK -->|TaxVerificationCompleted| KAFKA2
    DOC_CHK -->|DocumentVerificationCompleted| KAFKA2
    RISK_CHK -->|RiskAssessmentCompleted| KAFKA2

    KAFKA2 -->|All Checks Complete| SUPSVC
    SUPSVC <--> REDIS_OB
    SUPSVC -->|Qualification Ready - Notify Officer| NOTIFY2
    NOTIFY2 --> PROC_OFF

    PROC_OFF -->|Approve or Reject| SUPSVC
    SUPSVC -->|SupplierActivated| KAFKA2
    SUPSVC --> DB_SUP
    KAFKA2 -->|Notify Outcome| NOTIFY2
    NOTIFY2 --> SUP_REP
```

### Onboarding Stages and Data Requirements

| Stage | Data Collected | Validation Rule | Owner |
|-------|---------------|----------------|-------|
| Registration | Legal name, tax ID, country, currency, bank details | Tax ID format, no duplicate entity | SupplierService |
| Document Upload | Incorporation cert, bank confirmation letter, insurance | File type, expiry date, OCR confidence above 85% | SupplierService |
| Tax Verification | Tax ID cross-referenced against national registry | Status active, no outstanding liabilities | External Registry API |
| Document Verification | OCR-extracted entity name and registration number | Name matches registration record, similarity above 90% | Internal Rules Engine |
| Risk Assessment | Credit score, sanctions list screening, adverse media scan | Risk score below HIGH threshold | External Credit Bureau |
| Qualification Review | Aggregated verification results displayed to officer | Manual approval required for HIGH-risk classification | Procurement Officer |
| Activation | Supplier status set to ACTIVE, portal credentials provisioned | All prior stages must be PASSED | SupplierService |

---

## RFQ and Sourcing Data Flow

The RFQ flow supports competitive sourcing when no pre-negotiated contract is available.
It progresses from a procurement officer creating a sourcing event through supplier bid
submission, weighted evaluation, award decision, and onward conversion to either a
purchase order or a new contract in ContractService.

```mermaid
flowchart LR
    subgraph int_actors["Internal Actors"]
        PROC_OFF2([Procurement Officer])
        EVAL_COM([Evaluation Committee])
    end

    subgraph sup_portal["Supplier Portal"]
        BID_UI[Bid Submission\nReact SPA]
    end

    subgraph svc3["Services"]
        RFQSVC[RFQService\nRFQ Lifecycle]
        PROCSVC2[ProcurementService\nPO Generation]
        CONTSVC[ContractService\nContract Generation]
        NOTIFY3[NotificationService]
    end

    subgraph store3["Data Stores"]
        DB_RFQ[(PostgreSQL\nSourcing DB)]
        DB_PROC2[(PostgreSQL\nProcurement DB)]
        S3_RFQ[(S3\nRFQ Attachments)]
        KAFKA3([Kafka\nEvent Bus])
        REDIS_EVAL[(Redis\nEvaluation Score Cache)]
    end

    PROC_OFF2 -->|Create Sourcing Request| RFQSVC
    RFQSVC --> DB_RFQ
    RFQSVC -->|RFQPublished| KAFKA3
    KAFKA3 -->|Invite Suppliers| NOTIFY3
    NOTIFY3 --> BID_UI

    BID_UI -->|Submit Bid| RFQSVC
    RFQSVC --> DB_RFQ
    RFQSVC --> S3_RFQ
    RFQSVC -->|BidReceived| KAFKA3
    KAFKA3 -->|Scoring Trigger| RFQSVC
    RFQSVC <--> REDIS_EVAL

    EVAL_COM -->|Score and Rank Bids| RFQSVC
    RFQSVC -->|BidEvaluated| KAFKA3
    RFQSVC -->|Award Decision| DB_RFQ
    RFQSVC -->|RFQAwarded| KAFKA3

    KAFKA3 -->|Award via PO Path| PROCSVC2
    KAFKA3 -->|Award via Contract Path| CONTSVC
    PROCSVC2 --> DB_PROC2
    CONTSVC --> DB_RFQ
    KAFKA3 -->|Notify All Participants| NOTIFY3
```

### RFQ Event Sequence

| Event | Producer | Consumers | Key Payload Fields |
|-------|----------|-----------|-------------------|
| `RFQPublished` | RFQService | NotificationService | rfqId, title, deadline, invitedSupplierIds[] |
| `BidReceived` | RFQService | RFQService (scoring) | rfqId, supplierId, quotationId, totalValue |
| `BidDeadlineReached` | RFQService (scheduled) | RFQService (lock bids) | rfqId, totalBidsReceived |
| `BidEvaluated` | RFQService | RFQService (ranking) | rfqId, quotationId, weightedScore, scoreBreakdown |
| `RFQAwarded` | RFQService | ProcurementService, ContractService, NotificationService | rfqId, awardedSupplierId, quotationId, awardType |
| `ContractGenerated` | ContractService | ProcurementService, NotificationService | contractId, supplierId, startDate, endDate, value |

---

## Performance Scoring Data Flow

The performance scoring flow runs as a continuous Kafka Streams pipeline, aggregating
transaction events emitted by ReceivingService, InvoiceService, MatchingEngine, and
ContractService into rolling KPI counters. PerformanceService publishes scorecards on
a scheduled basis (daily and quarterly), triggering risk tier reclassification in
SupplierService and downstream ERP synchronisation.

```mermaid
flowchart TB
    subgraph event_src["Transaction Event Sources"]
        RECV_EV[ReceivingService\nDelivery events]
        INV_EV[InvoiceService\nInvoice processing events]
        MATCH_EV[MatchingEngine\nMatch result events]
        CONT_EV[ContractService\nCompliance events]
    end

    subgraph scoring["PerformanceService Pipeline"]
        AGGR[Event Aggregator\nKafka Streams Consumer]
        CALC[Score Calculator\nWeighted KPI Engine]
        TIER[Risk Tier Classifier\nThreshold Rules]
        PERF[Scorecard Publisher]
    end

    subgraph store4["Data Stores"]
        DB_PERF[(PostgreSQL\nPerformance DB)]
        REDIS_KPI[(Redis\nLive KPI Counters)]
        KAFKA4([Kafka\nEvent Bus])
        S3_RPT[(S3\nScorecard Reports)]
    end

    subgraph downstream["Downstream Consumers"]
        SUPSVC2[SupplierService\nRisk Tier Update]
        NOTIFY4[NotificationService\nAlerts and Reports]
        ERP2[ERP Integration\nVendor Master Sync]
    end

    RECV_EV -->|DeliveryOnTime, DeliveryLate| KAFKA4
    INV_EV -->|InvoiceAccepted, InvoiceDisputed| KAFKA4
    MATCH_EV -->|MatchPassed, MatchFailed| KAFKA4
    CONT_EV -->|ContractCompliancePassed, ContractBreached| KAFKA4

    KAFKA4 --> AGGR
    AGGR --> REDIS_KPI
    AGGR --> DB_PERF

    REDIS_KPI -->|Daily Snapshot Trigger| CALC
    CALC -->|Weighted Score| TIER
    TIER -->|ScorecardGenerated| KAFKA4
    TIER --> DB_PERF
    TIER --> S3_RPT

    KAFKA4 -->|ScorecardGenerated| SUPSVC2
    SUPSVC2 -->|SupplierRiskTierUpdated| KAFKA4
    KAFKA4 -->|Risk Tier Changed| NOTIFY4
    KAFKA4 -->|Metrics Updated| ERP2
```

### KPI Weights and Scoring Dimensions

| KPI Dimension | Weight | Source Event | Measurement Formula |
|---------------|--------|-------------|---------------------|
| On-Time Delivery Rate | 30% | `DeliveryOnTime`, `DeliveryLate` | On-time deliveries / total deliveries |
| Quality Acceptance Rate | 25% | `GoodsReceiptCompleted` acceptance qty | Accepted qty / total received qty |
| Invoice Accuracy Rate | 20% | `ThreeWayMatchCompleted` first-pass flag | First-pass match count / total invoices |
| Responsiveness | 15% | `BidReceived` vs `RFQPublished` timing | Responses within deadline / invitations sent |
| Contract Compliance | 10% | `ContractCompliancePassed` per milestone | Compliant milestones / total milestones |

Risk tier thresholds applied by the classifier:

| Score Range | Risk Tier | Effect |
|-------------|-----------|--------|
| 85 – 100 | PREFERRED | Expedited payment terms, auto-approval for low-value POs |
| 70 – 84 | STANDARD | Normal approval workflow |
| 50 – 69 | MONITORED | Enhanced review required for POs above USD 10,000 |
| 0 – 49 | HIGH_RISK | All POs require CFO approval, sourcing team alerted |

---

## Data Classification

All data traversing the platform is assigned to one of three tiers governing encryption
requirements, API response masking, and retention periods.

### Classification Tiers

| Tier | Label | Description | Examples |
|------|-------|-------------|---------|
| Tier 1 | PII | Personally identifiable information | Supplier contact names, email addresses, bank account numbers, signatory details |
| Tier 2 | Financial | Commercially sensitive financial data | Invoice amounts, payment references, contract pricing, credit limits, negotiated rates |
| Tier 3 | Operational | Business process and transaction metadata | PO identifiers, delivery dates, GR quantities, match statuses, RFQ IDs |

### Controls by Tier

| Control | Tier 1 — PII | Tier 2 — Financial | Tier 3 — Operational |
|---------|-------------|-------------------|---------------------|
| Encryption at rest | AES-256, column-level encryption | AES-256, table-level encryption | AES-256, volume-level |
| Encryption in transit | TLS 1.3 mandatory | TLS 1.3 mandatory | TLS 1.3 mandatory |
| Kafka message protection | Field-level encryption before produce | Payload encryption | Standard TLS transport |
| API response masking | PII fields masked for non-owning roles | Financial fields restricted by role | Full access for authorised roles |
| Retention period | 7 years (regulatory obligation) | 10 years (financial audit trail) | 3 years operational |
| S3 storage class | Intelligent-Tiering + SSE-KMS | Intelligent-Tiering + SSE-KMS | S3 Standard |
| Access control | Row-level security scoped to org_id | Column-level permissions by role | Standard RBAC |

### Kafka Topic Data Classification

| Topic | Classification | PII Present | Protection |
|-------|---------------|------------|-----------|
| `scm.procurement.pr.events` | Tier 3 | No | TLS transport |
| `scm.procurement.po.events` | Tier 2 | No | Payload encryption |
| `scm.supplier.onboarding.events` | Tier 1 | Yes | Field-level encryption |
| `scm.finance.invoice.events` | Tier 2 | No | Payload encryption |
| `scm.finance.payment.events` | Tier 2 | Yes | Field-level encryption |
| `scm.performance.scorecard.events` | Tier 3 | No | TLS transport |
| `scm.notification.dispatch.events` | Tier 1 | Yes | Field-level encryption |
| `scm.sourcing.rfq.events` | Tier 2 / Tier 3 | No | Payload encryption |
| `scm.contract.lifecycle.events` | Tier 2 | No | Payload encryption |

### S3 Bucket Classification

| Bucket | Purpose | Classification | Lifecycle Policy |
|--------|---------|---------------|-----------------|
| `scm-supplier-documents` | KYC documents, certificates of incorporation | Tier 1 / Tier 2 | Transition to Glacier after 1 year |
| `scm-invoice-attachments` | PDF invoices, OCR extraction outputs | Tier 2 | Transition to Glacier after 2 years |
| `scm-rfq-attachments` | RFQ specifications, bid response documents | Tier 2 / Tier 3 | Delete after 7 years |
| `scm-performance-reports` | Supplier scorecards and trend reports | Tier 3 | Delete after 5 years |
| `scm-audit-exports` | Compliance audit packages and exports | Tier 2 | Glacier Deep Archive after 1 year |
| `scm-contract-documents` | Signed contracts and amendments | Tier 2 | Glacier after 3 years, delete after 15 years |
