# API Design — Supply Chain Management Platform

This document defines the RESTful API contracts for all microservices in the Supply Chain Management Platform. The API layer is the primary integration surface for the internal web application, the supplier portal, and authorised third-party ERP and finance systems. Contracts are versioned, fully documented in OpenAPI 3.1 specifications generated from Spring Boot `@Operation` annotations, and published to the platform's internal developer portal on every successful CI pipeline run.

---

## API Design Principles

All platform APIs conform to a shared set of design principles enforced through Spring MVC configuration, shared request/response models in the `scm-api-commons` library, and automated contract tests using Spring Cloud Contract.

**Versioning** — All public APIs are versioned with a `v1` path prefix (e.g. `/api/v1/suppliers`). Breaking changes (field removal, type change, removal of an endpoint) require a new version path prefix (`v2`). Non-breaking additions (optional new fields, new endpoints) are released within the existing version. Both versions are served concurrently during a 90-day transition window before the older version is decommissioned.

**Content type** — All request and response bodies use `application/json`. Partial-update endpoints use `application/merge-patch+json` per RFC 7396. File upload endpoints use `multipart/form-data`.

**HATEOAS links** — Collection and detail responses include a `_links` object with `self`, `collection`, and contextually relevant action links (e.g. `approve`, `reject`, `issue`). Link availability is dynamically conditioned on the caller's roles and the resource's current state, enabling clients to drive UI rendering from the API response without duplicating state-machine logic.

**Pagination** — All collection endpoints use cursor-based pagination. Requests carry a `cursor` query parameter (base64-encoded opaque value) and a `pageSize` parameter (default 25, maximum 100). Responses include `nextCursor` and `previousCursor` fields in the `_pagination` object. Offset-based pagination is not supported due to inconsistency under concurrent data modification.

**Idempotency** — All `POST` endpoints creating a new resource accept an `Idempotency-Key` request header. The server caches the response for 24 hours keyed on this value and returns the cached response for duplicate requests with the same key, preventing duplicate document creation from client retries.

**Request tracing** — The API Gateway injects a `X-Correlation-ID` UUID into every inbound request. This header is echoed in all responses and propagated to all downstream service calls, enabling end-to-end request tracing in AWS X-Ray and log correlation in OpenSearch.

---

## Authentication and Authorisation

All endpoints require a valid Bearer JWT in the `Authorization` header. JWTs are issued by AWS Cognito and validated by APIGateway, which verifies the signature, expiry, audience (`scm-platform` for internal users, `scm-supplier-portal` for supplier users), and issuer. Validated claims are forwarded as HTTP headers to downstream services; services must not re-validate the JWT but must check the forwarded role claim for resource-level authorisation.

**RBAC Roles**

| Role | Description | Typical Principal |
|---|---|---|
| `PROCUREMENT_OFFICER` | Create and manage requisitions, purchase orders, and RFQs | Internal procurement team member |
| `APPROVER_L1` | Approve requisitions and POs up to $10,000 | Line manager |
| `APPROVER_L2` | Approve requisitions and POs up to $50,000 | Department director |
| `APPROVER_L3` | Approve requisitions and POs above $50,000 | CFO or delegated VP |
| `FINANCE_MANAGER` | Manage invoices, dispute resolution, payment runs | Finance operations team |
| `SUPPLIER_USER` | Supplier portal access; submit quotes, acknowledge POs, submit invoices | Supplier employee |
| `CONTRACT_MANAGER` | Create and manage supplier contracts | Procurement or legal team |
| `RECEIVING_CLERK` | Create and complete goods receipts | Warehouse / receiving team |
| `ADMIN` | Full platform access including configuration | Platform administration |

Row-level security is applied by each service: a `PROCUREMENT_OFFICER` can only view and edit requisitions they created, unless they hold a manager scope claim. A `SUPPLIER_USER` can only access records linked to their supplier account ID, extracted from the JWT `supplierId` claim.

---

## Supplier API

Base path: `/api/v1/suppliers`

### POST /api/v1/suppliers

Registers a new supplier in the platform. The supplier is created in `PENDING_QUALIFICATION` status. A qualification workflow is initiated asynchronously. Accessible by `PROCUREMENT_OFFICER` and `ADMIN`.

**Request body:**

| Field | Type | Required | Description |
|---|---|---|---|
| `legalName` | string | Yes | Registered legal entity name |
| `tradingName` | string | No | Operating or DBA name |
| `taxId` | string | Yes | Tax registration number (EIN/VAT/GST) |
| `country` | string | Yes | ISO 3166-1 alpha-2 country code |
| `currency` | string | Yes | Preferred payment currency (ISO 4217) |
| `primaryContactEmail` | string | Yes | Primary contact email for portal invitation |
| `spendCategories` | string[] | Yes | Array of category codes this supplier serves |
| `bankDetails` | object | No | Bank account details for payment setup |

**Response:** `201 Created` with supplier resource including `id`, `status`, `qualificationWorkflowId`, and `_links`.

**Status codes:** `201 Created`, `400 Bad Request` (validation failure), `409 Conflict` (duplicate tax ID), `403 Forbidden` (insufficient role).

### GET /api/v1/suppliers/{id}

Returns the full supplier profile including qualification status, active contracts count, and latest performance scorecard summary. Accessible by `PROCUREMENT_OFFICER`, `FINANCE_MANAGER`, `CONTRACT_MANAGER`, `ADMIN`.

**Response:** `200 OK` with full supplier object. `404 Not Found` if supplier does not exist or caller lacks access.

### PUT /api/v1/suppliers/{id}/status

Updates the supplier's lifecycle status. Valid transitions: `ACTIVE → SUSPENDED`, `SUSPENDED → ACTIVE`, `ACTIVE → BLACKLISTED`. Requires `ADMIN` role. A reason string is mandatory for `SUSPENDED` and `BLACKLISTED` transitions.

**Request body:** `{ "status": "SUSPENDED", "reason": "string", "effectiveDate": "ISO 8601 date" }`

**Response:** `200 OK`. `409 Conflict` if the transition is not permitted from the current status.

### POST /api/v1/suppliers/{id}/qualify

Submits a qualification decision for a supplier in `DOCUMENTS_SUBMITTED` status. Accessible by `ADMIN` and `CONTRACT_MANAGER`.

**Request body:** `{ "decision": "APPROVE" | "REJECT", "notes": "string", "qualifiedCategories": ["string"] }`

**Response:** `200 OK` with updated supplier status. `409 Conflict` if supplier is not in a qualifiable state.

### GET /api/v1/suppliers/{id}/performance

Returns the supplier's performance scorecard for a specified evaluation period. Accessible by all internal roles.

**Query parameters:** `period` (ISO 8601 year-month, e.g. `2024-Q3`), `includeHistory` (boolean, default false).

**Response:** `200 OK` with scorecard object containing `onTimeDeliveryRate`, `qualityAcceptanceRate`, `invoiceAccuracyRate`, `responsiveness`, `compositeScore`, `tier`, and `previousPeriodComparison`.

---

## Purchase Requisition API

Base path: `/api/v1/requisitions`

### POST /api/v1/requisitions

Creates a requisition in `DRAFT` status. Accessible by `PROCUREMENT_OFFICER`.

**Request body key fields:** `title`, `requiredByDate`, `costCentreCode`, `lines[]` (each with `itemCode`, `description`, `quantity`, `estimatedUnitPrice`, `currency`, `spendCategory`).

**Response:** `201 Created` with requisition ID and `DRAFT` status.

### GET /api/v1/requisitions/{id}

Returns full requisition detail including all lines, current approval stage, and approval history. Accessible by the requisition owner, current approvers, and `ADMIN`.

### PUT /api/v1/requisitions/{id}/submit

Submits a `DRAFT` requisition for approval. Triggers budget validation and approval chain determination. `PROCUREMENT_OFFICER` only.

**Response:** `200 OK` with updated status `PENDING_APPROVAL` and the first approver's details. `422 Unprocessable Entity` with `BUDGET_INSUFFICIENT` error code if budget check fails.

### POST /api/v1/requisitions/{id}/approve

Records an approval decision at the caller's approval tier. Accessible by `APPROVER_L1`, `APPROVER_L2`, `APPROVER_L3` depending on the current tier.

**Request body:** `{ "comments": "string" }`. No body fields required; the approver identity is taken from the JWT subject claim.

**Response:** `200 OK`. If this was the final required approval tier, status transitions to `APPROVED`. Otherwise status remains `PENDING_APPROVAL` with the next approver populated.

### POST /api/v1/requisitions/{id}/reject

Rejects the requisition at the caller's tier, returning it to `REJECTED` status and notifying the requester.

**Request body:** `{ "reason": "string" }` (mandatory).

**Response:** `200 OK` with `REJECTED` status.

---

## Purchase Order API

Base path: `/api/v1/purchase-orders`

### POST /api/v1/purchase-orders

Creates a purchase order from an approved requisition or directly (for pre-approved spend). Accessible by `PROCUREMENT_OFFICER`.

**Request body key fields:** `requisitionId` (optional), `supplierId`, `deliveryAddress`, `paymentTerms`, `lines[]` (each with `requisitionLineId`, `itemCode`, `quantity`, `agreedUnitPrice`, `currency`, `deliveryDate`), `contractId` (optional, references a framework agreement).

**Response:** `201 Created` with PO number and `DRAFT` status.

### PUT /api/v1/purchase-orders/{id}/issue

Issues the purchase order to the supplier, transitioning status to `ISSUED` and triggering portal notification. Requires `PROCUREMENT_OFFICER` and will fail if any required approval is outstanding.

**Response:** `200 OK` with `ISSUED` status. `409 Conflict` with `PO_ALREADY_CLOSED` if the PO has been closed.

### POST /api/v1/purchase-orders/{id}/confirm

Supplier acknowledgement endpoint. Records supplier confirmation or rejection with reason. Accessible by `SUPPLIER_USER` only. Updates status to `CONFIRMED` or `SUPPLIER_REJECTED`.

**Request body:** `{ "decision": "CONFIRM" | "REJECT", "reason": "string", "confirmedDeliveryDate": "ISO 8601 date" }`

### POST /api/v1/purchase-orders/{id}/change-orders

Creates a change order against an issued PO. Permitted changes: quantity adjustment, delivery date extension, and addition of new lines. Status reverts to `PENDING_RECONFIRMATION` and a new supplier acknowledgement is required.

**Request body:** `{ "changeType": "QUANTITY" | "DATE" | "ADD_LINE", "changes": [...], "reason": "string" }`

---

## RFQ API

Base path: `/api/v1/rfqs`

### POST /api/v1/rfqs

Creates a new RFQ in `DRAFT` status. Accessible by `PROCUREMENT_OFFICER`.

**Request body key fields:** `title`, `description`, `submissionDeadline`, `evaluationCriteria[]` (name, weight), `invitedSupplierIds[]`, `lines[]` (itemCode, description, quantity, targetUnit).

**Response:** `201 Created` with RFQ ID.

### POST /api/v1/rfqs/{id}/publish

Publishes the RFQ, notifying all invited suppliers and locking the specification. Status transitions to `OPEN`. Accessible by `PROCUREMENT_OFFICER`.

### GET /api/v1/rfqs/{id}/quotations

Returns all quotations submitted against this RFQ. Accessible by `PROCUREMENT_OFFICER` only (not visible to `SUPPLIER_USER` to prevent bid visibility before award).

**Query parameters:** `status` (SUBMITTED, SHORTLISTED, AWARDED, REJECTED), `supplierId`.

**Response:** `200 OK` with paginated list of quotation summaries including composite evaluation scores.

### POST /api/v1/rfqs/{id}/award

Records the award decision, selecting a winning quotation and notifying all participating suppliers. Status transitions to `AWARDED`. Optionally creates a PO or contract from the winning quotation. Accessible by `PROCUREMENT_OFFICER` and `CONTRACT_MANAGER`.

**Request body:** `{ "winningQuotationId": "uuid", "awardNotes": "string", "createPurchaseOrder": true, "createContract": false }`

---

## Goods Receipt API

Base path: `/api/v1/goods-receipts`

### POST /api/v1/goods-receipts

Creates a goods receipt record for a delivery against a purchase order. Accessible by `RECEIVING_CLERK`.

**Request body key fields:** `purchaseOrderId`, `supplierDeliveryNote`, `receivedDate`, `lines[]` (poLineId, quantityReceived, quantityAccepted, quantityRejected, rejectionReason).

**Response:** `201 Created` with goods receipt ID in `OPEN` status.

### POST /api/v1/goods-receipts/{id}/complete

Marks the goods receipt as complete and triggers a `GoodsReceiptCompleted` event, initiating the matching engine evaluation for any pending invoices referencing this PO. Accessible by `RECEIVING_CLERK`.

**Response:** `200 OK` with `COMPLETED` status. `409 Conflict` if the receipt is already completed.

### POST /api/v1/goods-receipts/{id}/discrepancies

Records a formal discrepancy report for a completed goods receipt, for example a quantity shortage or damaged goods claim. Accessible by `RECEIVING_CLERK` and `PROCUREMENT_OFFICER`.

**Request body:** `{ "discrepancyType": "SHORT_DELIVERY" | "DAMAGED" | "WRONG_ITEM", "affectedLines": [...], "notes": "string", "photosUploaded": true }`

---

## Invoice API

Base path: `/api/v1/invoices`

### POST /api/v1/invoices

Submits a new invoice for matching. Accessible by `SUPPLIER_USER` via the supplier portal and by `FINANCE_MANAGER` for manual entry of paper invoices.

**Request body key fields:** `supplierInvoiceNumber`, `purchaseOrderId`, `invoiceDate`, `dueDate`, `currency`, `lines[]` (poLineId, description, quantity, unitPrice, lineAmount), `taxAmount`, `totalAmount`.

**Response:** `201 Created` with platform invoice ID, idempotency guard on `supplierInvoiceNumber + supplierId`. Status `SUBMITTED`. `409 Conflict` with `INVOICE_DUPLICATE` if duplicate detected.

### GET /api/v1/invoices/{id}/match-result

Returns the three-way match result for this invoice. Available once MatchingEngine has processed the invoice. Accessible by `FINANCE_MANAGER` and the submitting `SUPPLIER_USER`.

**Response:** `200 OK` with match result including `matchStatus` (APPROVED, DISCREPANCY, PENDING), per-dimension variance details, and applicable tolerance thresholds.

### POST /api/v1/invoices/{id}/dispute

Raises a formal dispute on an invoice in `DISCREPANCY` status. Either party (buyer or supplier) may raise a dispute.

**Request body:** `{ "disputeType": "QUANTITY" | "PRICE" | "TAX" | "DUPLICATE", "description": "string", "supportingDocuments": ["s3-key"] }`

**Response:** `200 OK` with status `DISPUTED` and a `disputeId`. `409 Conflict` if invoice is already in dispute.

---

## Payment API

Base path: `/api/v1/payment-runs`

### POST /api/v1/payment-runs

Creates a manual payment run. System-scheduled runs are created automatically. Accessible by `FINANCE_MANAGER`.

**Request body:** `{ "currency": "USD", "paymentDate": "ISO 8601 date", "includeInvoiceIds": ["uuid"], "enableDynamicDiscounting": true }`

**Response:** `201 Created` with payment run ID, total invoice count, total gross amount, and `PENDING_APPROVAL` status.

### GET /api/v1/payment-runs/{id}

Returns the full payment run detail including line-level payment status per invoice and per banking rail. Accessible by `FINANCE_MANAGER` and `ADMIN`.

### POST /api/v1/payment-runs/{id}/execute

Triggers execution of an approved payment run, dispatching banking instructions to the configured rails. Requires `FINANCE_MANAGER` and dual-control approval for runs above the configured threshold. Accessible by `FINANCE_MANAGER`.

**Response:** `200 OK` with `EXECUTING` status. `409 Conflict` with `PAYMENT_RUN_NOT_APPROVED` if secondary approval is pending.

---

## Error Response Schema

All error responses use a consistent envelope structure regardless of the HTTP status code.

```json
{
  "error": {
    "code": "INVOICE_DUPLICATE",
    "message": "An invoice with the same supplier invoice number already exists for this supplier.",
    "details": [
      {
        "field": "supplierInvoiceNumber",
        "issue": "INV-2024-00987 was previously submitted on 2024-11-01",
        "existingResourceId": "3f8a2b1c-..."
      }
    ],
    "traceId": "X-Ray trace ID",
    "correlationId": "request correlation UUID",
    "timestamp": "2024-11-15T09:23:41Z"
  }
}
```

**Standard error codes:**

| Code | HTTP Status | Description |
|---|---|---|
| `SUPPLIER_NOT_ACTIVE` | 422 | Operation requires supplier status ACTIVE; current status returned in details |
| `PO_ALREADY_CLOSED` | 409 | Purchase order is in CLOSED or CANCELLED status and cannot be modified |
| `INVOICE_DUPLICATE` | 409 | Invoice number already exists for this supplier; existing ID returned in details |
| `MATCH_TOLERANCE_EXCEEDED` | 422 | Invoice variance exceeds configured tolerance; dimension details returned |
| `BUDGET_INSUFFICIENT` | 422 | Requisition amount exceeds available budget on the cost centre |
| `APPROVAL_CHAIN_INCOMPLETE` | 409 | Operation requires all approval tiers to be resolved first |
| `PAYMENT_RUN_NOT_APPROVED` | 409 | Payment run requires secondary FINANCE_MANAGER approval before execution |
| `QUALIFICATION_NOT_COMPLETE` | 422 | Supplier must be fully qualified before a PO can be issued to them |
| `CONTRACT_EXPIRED` | 422 | Referenced contract has passed its expiry date; renewal required |
| `RFQ_ALREADY_AWARDED` | 409 | RFQ has already been awarded; no further quotations can be submitted |
| `GR_ALREADY_COMPLETED` | 409 | Goods receipt is already in COMPLETED status |
| `INVALID_CURSOR` | 400 | Pagination cursor value is malformed or has expired |
| `IDEMPOTENCY_KEY_CONFLICT` | 409 | Idempotency key matched an existing request with different body content |

---

## Webhook Events

The platform publishes webhook notifications to registered external system endpoints (ERP, finance system, WMS) for key business events. Webhooks are delivered via HTTPS POST with a shared-secret HMAC-SHA256 signature in the `X-SCM-Signature` header. Failed deliveries are retried up to 5 times with exponential backoff before the endpoint is marked inactive and an alert is raised.

| Event Name | Trigger | Typical Subscriber |
|---|---|---|
| `purchase_order.issued` | PO status transitions to ISSUED | ERP (creates PO in financial ledger) |
| `goods_receipt.completed` | GR marked complete | WMS (closes inbound shipment) |
| `invoice.approved` | Invoice match approved, queued for payment | Finance system (accrual posting) |
| `invoice.disputed` | Invoice dispute raised | ERP (places payment on hold) |
| `payment.settled` | Payment confirmed settled by bank | ERP (marks liability as paid) |
| `supplier.qualified` | Supplier qualification approved | ERP (creates vendor master record) |
| `supplier.suspended` | Supplier suspended | ERP (blocks supplier on vendor master) |
| `contract.expiring` | Contract within configured warning window | Contract management system |
| `po.change_order.issued` | Change order issued to supplier | ERP (updates PO commitment) |
| `match.discrepancy.raised` | Three-way match discrepancy created | Finance system (dispute workflow trigger) |

Webhook payload envelopes include `eventId`, `eventType`, `timestamp`, `resourceId`, `resourceType`, and a `data` object containing the full serialised resource at the time of the event. Subscribers must respond with HTTP `2xx` within 10 seconds; longer processing must be handled asynchronously by the subscriber.
