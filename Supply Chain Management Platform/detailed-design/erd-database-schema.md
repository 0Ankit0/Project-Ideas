# Supply Chain Management Platform - Entity Relationship Diagram & Schema

## Database Overview

PostgreSQL relational schema with 15+ core tables covering procurement-to-payment workflow.

## Core Tables

### suppliers
- `supplier_id` (UUID, PK)
- `supplier_name` (VARCHAR, indexed)
- `supplier_code` (VARCHAR, unique, indexed)
- `email` (VARCHAR)
- `phone` (VARCHAR)
- `country` (VARCHAR)
- `status` (ENUM: Invited, QualificationInProgress, Approved, Active, Suspended, Blacklisted)
- `kyc_status` (ENUM: Pending, Verified, Failed)
- `kyc_verified_at` (TIMESTAMP)
- `created_at` (TIMESTAMP, default: now())
- `updated_at` (TIMESTAMP, default: now())
- `created_by` (UUID, FK: users)

**Indexes**: supplier_code, status, country

### purchase_requisitions
- `requisition_id` (UUID, PK)
- `requisition_number` (VARCHAR, unique, indexed)
- `requester_id` (UUID, FK: users)
- `department_id` (UUID, FK: departments)
- `status` (ENUM: Draft, SubmittedForApproval, Approved, RFQIssued, POCreated, Rejected, Cancelled)
- `title` (VARCHAR)
- `description` (TEXT)
- `budget_amount` (DECIMAL(12,2))
- `cost_center_code` (VARCHAR, FK: cost_centers in SAP)
- `submitted_at` (TIMESTAMP)
- `approved_by` (UUID, FK: users)
- `approved_at` (TIMESTAMP)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

**Indexes**: requisition_number, status, requester_id, approved_at

### requisition_line_items
- `line_item_id` (UUID, PK)
- `requisition_id` (UUID, FK: purchase_requisitions)
- `material_id` (UUID, FK: materials)
- `quantity` (DECIMAL(10,2))
- `unit_of_measure` (VARCHAR)
- `estimated_unit_price` (DECIMAL(10,4))
- `estimated_line_total` (DECIMAL(12,2)) -- calculated: qty * price
- `delivery_date` (DATE)
- `notes` (TEXT)

**Indexes**: requisition_id, material_id

### purchase_orders
- `po_id` (UUID, PK)
- `po_number` (VARCHAR, unique, indexed)
- `requisition_id` (UUID, FK: purchase_requisitions)
- `supplier_id` (UUID, FK: suppliers, indexed)
- `status` (ENUM: Draft, SentToSupplier, Confirmed, PartiallyReceived, FullyReceived, Cancelled)
- `po_date` (DATE)
- `delivery_date` (DATE)
- `payment_terms` (VARCHAR) -- e.g., "Net 30", "2/10 Net 30"
- `po_total_amount` (DECIMAL(12,2))
- `tax_amount` (DECIMAL(12,2))
- `shipping_amount` (DECIMAL(12,2))
- `grand_total` (DECIMAL(12,2))
- `currency_code` (VARCHAR, default: 'USD')
- `exchange_rate` (DECIMAL(10,6))
- `created_by` (UUID, FK: users)
- `sent_to_supplier_at` (TIMESTAMP)
- `supplier_confirmed_at` (TIMESTAMP)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

**Indexes**: po_number, supplier_id, status, po_date

### po_line_items
- `po_line_item_id` (UUID, PK)
- `po_id` (UUID, FK: purchase_orders)
- `material_id` (UUID, FK: materials)
- `quantity_ordered` (DECIMAL(10,2))
- `quantity_received` (DECIMAL(10,2), default: 0)
- `unit_of_measure` (VARCHAR)
- `unit_price` (DECIMAL(10,4))
- `line_total` (DECIMAL(12,2)) -- calculated: qty * price
- `tax_code` (VARCHAR)
- `glAccount_code` (VARCHAR, FK: GL accounts in SAP)
- `delivery_date` (DATE)

**Indexes**: po_id, material_id

### quotations
- `quotation_id` (UUID, PK)
- `rfq_id` (UUID, FK: rfqs)
- `supplier_id` (UUID, FK: suppliers)
- `quoted_by` (VARCHAR) -- supplier contact name
- `quote_date` (DATE)
- `valid_until` (DATE)
- `quotation_total` (DECIMAL(12,2))
- `tax_amount` (DECIMAL(12,2))
- `delivery_lead_time_days` (INT)
- `payment_terms` (VARCHAR)
- `status` (ENUM: Submitted, Selected, Rejected)
- `received_at` (TIMESTAMP)
- `evaluated_at` (TIMESTAMP)
- `created_at` (TIMESTAMP)

**Indexes**: rfq_id, supplier_id, status

### quotation_items
- `quotation_item_id` (UUID, PK)
- `quotation_id` (UUID, FK: quotations)
- `material_id` (UUID, FK: materials)
- `quoted_quantity` (DECIMAL(10,2))
- `quoted_unit_price` (DECIMAL(10,4))
- `quoted_line_total` (DECIMAL(12,2))
- `unit_of_measure` (VARCHAR)

### goods_receipts
- `grn_id` (UUID, PK)
- `grn_number` (VARCHAR, unique, indexed)
- `po_id` (UUID, FK: purchase_orders)
- `supplier_id` (UUID, FK: suppliers)
- `received_date` (DATE)
- `received_by` (UUID, FK: users)
- `warehouse_location` (VARCHAR)
- `goods_receipt_total` (DECIMAL(12,2))
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

**Indexes**: grn_number, po_id, supplier_id, received_date

### gr_line_items
- `gr_line_item_id` (UUID, PK)
- `grn_id` (UUID, FK: goods_receipts)
- `po_line_item_id` (UUID, FK: po_line_items)
- `material_id` (UUID, FK: materials)
- `quantity_received` (DECIMAL(10,2))
- `quantity_accepted` (DECIMAL(10,2))
- `quantity_rejected` (DECIMAL(10,2))
- `unit_price` (DECIMAL(10,4))
- `inspection_result` (ENUM: Accepted, Accepted with Notes, Rejected)
- `inspection_notes` (TEXT)
- `batch_number` (VARCHAR)
- `expiry_date` (DATE)

### invoices
- `invoice_id` (UUID, PK)
- `invoice_number` (VARCHAR, unique, indexed)
- `supplier_id` (UUID, FK: suppliers)
- `po_id` (UUID, FK: purchase_orders)
- `invoice_date` (DATE)
- `due_date` (DATE)
- `invoice_total` (DECIMAL(12,2))
- `tax_amount` (DECIMAL(12,2))
- `discount_amount` (DECIMAL(12,2))
- `net_amount` (DECIMAL(12,2))
- `status` (ENUM: Received, UnderReview, OnHold, Matched, Disputed, ApprovedForPayment, Paid, Rejected)
- `3way_match_status` (ENUM: Pending, Passed, Failed)
- `currency_code` (VARCHAR)
- `payment_method` (VARCHAR) -- ACH, Wire, Check
- `paid_date` (TIMESTAMP)
- `received_at` (TIMESTAMP)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

**Indexes**: invoice_number, supplier_id, po_id, status, due_date

### invoice_line_items
- `invoice_line_id` (UUID, PK)
- `invoice_id` (UUID, FK: invoices)
- `po_line_item_id` (UUID, FK: po_line_items)
- `material_id` (UUID, FK: materials)
- `invoice_quantity` (DECIMAL(10,2))
- `invoice_unit_price` (DECIMAL(10,4))
- `invoice_line_total` (DECIMAL(12,2))
- `po_quantity` (DECIMAL(10,2))
- `grn_quantity` (DECIMAL(10,2))
- `variance_qty` (DECIMAL(10,2)) -- calculated: invoice_qty - grn_qty
- `variance_pct` (DECIMAL(5,2)) -- calculated: (invoice_qty - grn_qty) / grn_qty * 100
- `tax_code` (VARCHAR)

### contracts
- `contract_id` (UUID, PK)
- `contract_number` (VARCHAR, unique, indexed)
- `supplier_id` (UUID, FK: suppliers)
- `contract_type` (VARCHAR) -- e.g., "Master Service Agreement", "Volume Commitment"
- `start_date` (DATE)
- `end_date` (DATE)
- `renewal_date` (DATE)
- `auto_renew` (BOOLEAN, default: false)
- `payment_terms` (VARCHAR)
- `price_escalation_pct` (DECIMAL(5,2)) -- annual escalation
- `min_order_amount` (DECIMAL(12,2))
- `max_order_amount` (DECIMAL(12,2))
- `contract_value` (DECIMAL(12,2))
- `s3_document_url` (VARCHAR)
- `status` (ENUM: Active, Expiring Soon, Expired, Terminated)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

**Indexes**: supplier_id, end_date, status

### supplier_performance_metrics
- `metric_id` (UUID, PK)
- `supplier_id` (UUID, FK: suppliers)
- `measurement_period` (VARCHAR) -- e.g., "2024-01"
- `on_time_delivery_pct` (DECIMAL(5,2))
- `quality_acceptance_pct` (DECIMAL(5,2))
- `invoice_accuracy_pct` (DECIMAL(5,2))
- `responsiveness_score` (INT, 1-5)
- `compliance_status` (VARCHAR) -- Compliant, Non-Compliant
- `performance_tier` (ENUM: Strategic, Preferred, Standard, At-Risk)
- `calculated_at` (TIMESTAMP)

**Indexes**: supplier_id, measurement_period

### approval_workflows
- `workflow_id` (UUID, PK)
- `requisition_id` (UUID, FK: purchase_requisitions)
- `approval_level` (INT) -- 1, 2, 3 (escalating approvers)
- `approver_id` (UUID, FK: users)
- `status` (ENUM: Pending, Approved, Rejected, Escalated)
- `approval_amount_limit` (DECIMAL(12,2))
- `submitted_at` (TIMESTAMP)
- `approved_at` (TIMESTAMP)
- `rejection_reason` (TEXT)

**Indexes**: requisition_id, approver_id, status

### audit_logs
- `audit_id` (UUID, PK)
- `entity_type` (VARCHAR) -- e.g., "purchase_order", "invoice"
- `entity_id` (UUID)
- `action` (VARCHAR) -- "CREATE", "UPDATE", "DELETE", "STATUS_CHANGE"
- `old_values` (JSONB)
- `new_values` (JSONB)
- `changed_by` (UUID, FK: users)
- `change_reason` (TEXT)
- `timestamp` (TIMESTAMP, indexed)
- `ip_address` (VARCHAR)

**Indexes**: entity_type, entity_id, timestamp, changed_by

---

## Key Constraints & Validations

1. **Referential Integrity**: All FKs have DELETE RESTRICT (no orphaned records)
2. **Unique Constraints**: po_number, invoice_number, contract_number, supplier_code
3. **Check Constraints**:
   - PO total = SUM(line_items.line_total) + tax + shipping
   - GRN qty_accepted ≤ qty_received
   - Invoice due_date ≥ invoice_date
4. **Audit Trail**: All state-changing operations logged to audit_logs

## Indexes Summary

Total indexes: 20+ (balance between query performance and write performance)
Frequently queried:
- supplier_id (all tables referencing suppliers)
- po_id (line items, receipts, invoices)
- status (workflow filtering)
- dates (range queries for reporting)

