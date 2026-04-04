# Edge Cases — Inventory and Fulfillment

## EC-INV-001: Reservation Expiry During Payment Processing

**Scenario:** Customer's 15-minute reservation expires while payment is still processing (slow gateway response).

**Trigger:** Payment gateway takes > 15 minutes or customer abandons checkout.

**Expected Behaviour:**
- System timer releases expired reservations every 60 seconds
- If payment later succeeds after reservation release:
  - Order Service re-checks stock before confirming
  - If stock still available → re-reserve and confirm
  - If stock no longer available → refund payment, cancel order, notify customer
- Reconciliation catches orphaned payments

**Severity:** High

---

## EC-INV-002: Concurrent Stock Adjustments

**Scenario:** Admin performs manual stock adjustment while checkout reservations are being made.

**Trigger:** Admin reduces stock count; concurrent reservation attempts.

**Expected Behaviour:**
- All inventory operations use optimistic locking with version column
- Manual adjustment: `UPDATE inventory SET qty_on_hand = ?, version = version + 1 WHERE version = ?`
- Concurrent reservation retries on version conflict (max 3 retries)
- Stock can never go negative (CHECK constraint)

**Severity:** High

---

## EC-INV-003: Low Stock Alert Storm

**Scenario:** Flash sale causes many products to hit low stock threshold simultaneously, generating a flood of alerts.

**Trigger:** High-volume checkout activity.

**Expected Behaviour:**
- Low stock alert is debounced: only one alert per variant per 30-minute window
- Alert cooldown tracked in ElastiCache with TTL
- If alert notification delivery fails, alert is not retried to avoid queue flooding
- Operations dashboard shows low-stock products in real-time regardless of alert status

**Severity:** Medium

---

## EC-INV-004: Pick Discrepancy — Wrong Item Scanned

**Scenario:** Warehouse staff scans incorrect barcode during picking.

**Trigger:** Human error — staff picks wrong item from shelf.

**Expected Behaviour:**
- System compares scanned SKU against expected SKU in fulfillment task
- Mismatch flagged immediately with audio/visual alert on device
- Staff cannot proceed until correct item is scanned
- If correct item is out of stock at the expected bin location:
  - Task status set to `Blocked` with reason "Item not found at bin"
  - Supervisor notified for investigation (misplaced stock or count error)
  - Supervisor can reassign to different bin or cancel the line item (partial fulfillment)

**Severity:** Medium

---

## EC-INV-005: Split Fulfillment — Multi-Warehouse Order

**Scenario:** Order contains items spanning two warehouse locations.

**Trigger:** Variant A available in Warehouse 1; Variant B in Warehouse 2.

**Expected Behaviour:**
- MVP does not support split fulfillment — all items must be available in a single warehouse
- If items span warehouses, system picks the warehouse with the most items available
- Unavailable items are flagged: customer can proceed with partial order or wait for stock transfer
- Future phase: automatic inter-warehouse stock transfer followed by single-warehouse fulfillment

**Severity:** Medium

---

## EC-INV-006: Bulk Import Failures

**Scenario:** Admin uploads CSV with 10,000 products; 50 rows have validation errors.

**Trigger:** malformed CSV data (missing required fields, invalid prices, duplicate SKUs).

**Expected Behaviour:**
- Import processes all valid rows; rejects invalid rows
- System returns summary: `{ "imported": 9950, "failed": 50, "errors": [...] }`
- Failed rows include line number, column, and validation error
- Import is NOT transactional — partial success is the expected mode
- Admin can download error report and fix/resubmit failed rows

**Severity:** Low
