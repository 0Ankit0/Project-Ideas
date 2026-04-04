# User Stories

## 1. Customer Stories

### US-001: Customer Registration
**As a** customer, **I want to** register using my email or phone number **so that** I can place orders on the platform.

**Acceptance Criteria:**
- Customer can register with email + password or phone + OTP
- Social login via Google and Apple is supported
- Email/phone is verified via OTP before account activation
- Duplicate email/phone registrations are rejected with clear messaging
- Upon successful registration, customer is redirected to the homepage with a welcome notification

**Priority:** High | **Points:** 3

---

### US-002: Manage Delivery Addresses
**As a** customer, **I want to** save and manage multiple delivery addresses **so that** I can quickly select a delivery location during checkout.

**Acceptance Criteria:**
- Customer can add, edit, and delete addresses with labels (Home, Work, Custom)
- System validates address against configured delivery zones and shows serviceability status
- Customer can set one address as default; default is pre-selected at checkout
- Addresses linked to active orders cannot be deleted (soft-delete with warning)

**Priority:** High | **Points:** 3

---

### US-003: Browse and Search Products
**As a** customer, **I want to** search and browse products by category and keyword **so that** I can find items I want to purchase.

**Acceptance Criteria:**
- Full-text search returns results within 500 ms at P95
- Results can be filtered by category, price range, and availability
- Results can be sorted by relevance, price (low-high, high-low), popularity, and newest
- Out-of-stock items are shown with a clear "Out of Stock" badge and cannot be added to cart

**Priority:** High | **Points:** 5

---

### US-004: Add to Cart and Checkout
**As a** customer, **I want to** add items to my cart and proceed to checkout **so that** I can purchase products.

**Acceptance Criteria:**
- Customer can add items with selected variant and quantity
- Cart persists across sessions (authenticated users)
- Cart shows real-time prices, taxes, shipping fee, and discount breakdown
- At checkout, system validates stock availability and reserves inventory for 15 minutes
- Expired reservations are released and customer is notified if items become unavailable

**Priority:** High | **Points:** 8

---

### US-005: Apply Discount Coupon
**As a** customer, **I want to** apply a discount coupon at checkout **so that** I can save money on my order.

**Acceptance Criteria:**
- Customer enters coupon code and sees instant validation result (valid/invalid/expired)
- Valid coupons show the discount amount deducted from the total
- System enforces coupon rules: minimum order value, usage limits, validity period, applicable categories
- Only one coupon can be applied per order (unless stacking is explicitly configured)

**Priority:** Medium | **Points:** 3

---

### US-006: Track Order Status
**As a** customer, **I want to** view the real-time status and milestone history of my order **so that** I know when to expect delivery.

**Acceptance Criteria:**
- Order detail page shows current state and estimated delivery window
- Timestamped milestone history is displayed (e.g., Confirmed at 10:00, ReadyForDispatch at 14:00)
- Customer receives push/email/SMS notification at each major status change
- POD (signature + photo) is visible once order is delivered

**Priority:** High | **Points:** 5

---

### US-007: Cancel Order
**As a** customer, **I want to** cancel my order before it is picked up for delivery **so that** I receive a refund.

**Acceptance Criteria:**
- Cancel button is available for orders in `Confirmed` and `ReadyForDispatch` states
- Cancellation requires a reason code from a predefined list
- Refund is automatically initiated to original payment method
- Inventory reservation is released immediately
- Customer receives cancellation confirmation notification

**Priority:** High | **Points:** 5

---

### US-008: Initiate Return
**As a** customer, **I want to** request a return for a delivered order **so that** I can get a refund for unsatisfactory items.

**Acceptance Criteria:**
- Return option is available within the configured return window (default 7 days post-delivery)
- Customer selects return reason from predefined list and optionally uploads photo evidence
- System confirms return eligibility (within window, non-excluded category)
- Customer receives return request confirmation with estimated pickup date
- Return status is trackable on the order detail page

**Priority:** High | **Points:** 5

---

### US-009: View Order History
**As a** customer, **I want to** view my past orders **so that** I can reorder items or check delivery details.

**Acceptance Criteria:**
- Order history shows all orders with status, date, total, and item summary
- Orders are sorted by date (newest first) with pagination
- Customer can click into any order for full details including milestones and POD
- Customer can filter history by status (Active, Delivered, Cancelled, Returned)

**Priority:** Medium | **Points:** 3

---

### US-010: Manage Notification Preferences
**As a** customer, **I want to** control which notifications I receive **so that** I am not overwhelmed by messages.

**Acceptance Criteria:**
- Customer can toggle email, SMS, and push notifications independently
- Transactional notifications (OTP, order confirmation) cannot be disabled
- Promotional notifications have separate opt-in/opt-out controls
- Preference changes take effect within 1 minute

**Priority:** Low | **Points:** 2

---

## 2. Warehouse Staff Stories

### US-011: View Pick List
**As a** warehouse staff member, **I want to** see my assigned pick list **so that** I can efficiently locate and prepare order items.

**Acceptance Criteria:**
- Dashboard shows all assigned fulfillment tasks sorted by priority (SLA deadline)
- Each task shows order ID, items, quantities, warehouse location/bin, and SLA countdown
- Staff can start a task, which moves it to "In Progress" state
- Only one task can be in "In Progress" at a time per staff member

**Priority:** High | **Points:** 5

---

### US-012: Verify Picks via Barcode Scan
**As a** warehouse staff member, **I want to** scan item barcodes during picking **so that** pick accuracy is verified before packing.

**Acceptance Criteria:**
- Staff scans each item barcode; system validates against expected SKU and quantity
- Mismatched scans are flagged with an alert and logged for supervisor review
- All items must be scanned before the task can be marked as "Picked"
- System records pick accuracy rate per staff member

**Priority:** High | **Points:** 5

---

### US-013: Pack and Generate Manifest
**As a** warehouse staff member, **I want to** mark an order as packed and generate a packing slip **so that** it is ready for delivery handoff.

**Acceptance Criteria:**
- Staff records package dimensions and weight
- System generates a printable packing slip with order details, items, and delivery address
- Staff confirms packing complete; order transitions to `ReadyForDispatch`
- System generates delivery manifest grouped by delivery zone for handoff to delivery team

**Priority:** High | **Points:** 5

---

### US-014: Inspect Returned Items
**As a** warehouse staff member, **I want to** inspect returned items **so that** the system can determine whether to approve the refund.

**Acceptance Criteria:**
- Staff sees pending return inspections with original order details and customer-stated reason
- Staff records inspection result: Accept, Reject (with reason), or Partial Accept
- Accepted items are returned to stock; inventory levels are updated
- Rejected returns notify the customer with rejection reason
- Inspection results are auditable with staff identity and timestamp

**Priority:** Medium | **Points:** 5

---

## 3. Delivery Staff Stories

### US-015: View Delivery Assignments
**As a** delivery staff member, **I want to** see my assigned deliveries for the day **so that** I can plan my delivery run.

**Acceptance Criteria:**
- Dashboard shows all assigned deliveries with customer name, address, order summary, and delivery window
- Deliveries are sorted by suggested sequence based on delivery zone proximity
- Staff can view a printable route sheet
- New assignments trigger push notification

**Priority:** High | **Points:** 5

---

### US-016: Update Delivery Status
**As a** delivery staff member, **I want to** update order status as I progress through my delivery run **so that** customers and operations can track progress.

**Acceptance Criteria:**
- Staff updates status through milestones: `PickedUp` → `OutForDelivery` → `Delivered`
- Each status update records timestamp and staff identity
- System enforces milestone ordering — states cannot be skipped
- Status updates trigger customer notifications

**Priority:** High | **Points:** 3

---

### US-017: Capture Proof of Delivery
**As a** delivery staff member, **I want to** capture the recipient's signature and a photo **so that** delivery is confirmed and disputes are minimised.

**Acceptance Criteria:**
- Staff captures electronic signature on device screen
- Staff captures at least one photo at the delivery location
- POD is uploaded to S3 and linked to the order record
- If offline, POD is stored locally and synced when connectivity resumes
- POD upload failure triggers retry; after 3 failures, alert sent to operations

**Priority:** High | **Points:** 8

---

### US-018: Record Failed Delivery
**As a** delivery staff member, **I want to** record a failed delivery attempt with a reason **so that** the system can reschedule or process a return.

**Acceptance Criteria:**
- Staff selects failure reason from predefined list (customer unavailable, wrong address, refused, access issue)
- Staff can add optional notes
- System notifies customer of failed attempt with reschedule options
- After 3 failed attempts, system transitions order to `ReturnedToWarehouse`

**Priority:** High | **Points:** 5

---

### US-019: Collect Return Pickups
**As a** delivery staff member, **I want to** view and execute assigned return pickups **so that** returned items are brought back to the warehouse.

**Acceptance Criteria:**
- Return pickups appear on the delivery dashboard alongside regular deliveries
- Staff confirms item collection from customer
- Staff records collected item condition notes
- System updates return status to `PickedUp` and generates return manifest

**Priority:** Medium | **Points:** 3

---

## 4. Operations Manager Stories

### US-020: Monitor Fulfillment Dashboard
**As an** operations manager, **I want to** view a real-time fulfillment dashboard **so that** I can identify bottlenecks and SLA risks.

**Acceptance Criteria:**
- Dashboard shows: orders pending fulfillment, orders ready for dispatch, orders in delivery, completed today
- SLA countdown is visible for each pending order with colour-coded urgency (green/yellow/red)
- Manager can filter by warehouse, delivery zone, and date range
- Dashboard auto-refreshes every 30 seconds

**Priority:** High | **Points:** 5

---

### US-021: Reassign Delivery Staff
**As an** operations manager, **I want to** reassign deliveries to different staff members **so that** I can balance workload or handle staff absences.

**Acceptance Criteria:**
- Manager can select one or more orders and reassign to another available staff member
- Reassignment is allowed only for orders in `ReadyForDispatch` or `PickedUp` states
- Original staff member is notified of reassignment
- New staff member receives the delivery details via push notification
- Reassignment is logged in the audit trail

**Priority:** High | **Points:** 5

---

### US-022: View Delivery Performance Reports
**As an** operations manager, **I want to** view delivery performance reports **so that** I can identify improvement areas and high performers.

**Acceptance Criteria:**
- Reports show: on-time delivery rate, average delivery time, failed delivery rate, staff utilisation
- Reports can be filtered by staff member, delivery zone, and date range
- Staff performance ranking is available with key metrics
- Reports can be exported in CSV and PDF formats

**Priority:** Medium | **Points:** 5

---

### US-023: Manage Delivery Zones
**As an** operations manager, **I want to** configure delivery zones **so that** the system knows which areas we service and the associated fees.

**Acceptance Criteria:**
- Manager can create, edit, and deactivate delivery zones
- Each zone has: name, geographic boundary (PIN codes or polygon), delivery fee, min order value, SLA target
- Deactivating a zone prevents new orders to that area but does not affect active orders
- Zone changes are versioned with effective date

**Priority:** Medium | **Points:** 5

---

## 5. Admin Stories

### US-024: Manage Product Catalog
**As an** admin, **I want to** manage the product catalog **so that** customers can browse and purchase current products.

**Acceptance Criteria:**
- Admin can create, edit, and archive products and categories
- Bulk product upload via CSV is supported with validation and error reporting
- Product changes are reflected in search results within 5 seconds
- Archived products are hidden from search but retained for historical order references

**Priority:** High | **Points:** 5

---

### US-025: Manage Coupons and Promotions
**As an** admin, **I want to** create and manage discount coupons **so that** I can run marketing campaigns.

**Acceptance Criteria:**
- Admin can create coupons with: code, discount type, value, min order, validity dates, usage limits
- Admin can view coupon usage statistics (times used, revenue impact)
- Admin can deactivate coupons immediately
- Coupon creation and changes are audited

**Priority:** Medium | **Points:** 3

---

### US-026: Manage Staff Accounts
**As an** admin, **I want to** onboard and manage warehouse and delivery staff accounts **so that** they can access their operational dashboards.

**Acceptance Criteria:**
- Admin can create staff accounts with role (Warehouse Staff, Delivery Staff, Operations Manager)
- Admin can assign staff to warehouse locations or delivery zones
- Admin can deactivate staff accounts (soft delete, preserving audit trail)
- Staff account changes are audited with admin identity and timestamp

**Priority:** High | **Points:** 3

---

### US-027: View Platform Analytics
**As an** admin, **I want to** view platform-wide analytics **so that** I can make data-driven business decisions.

**Acceptance Criteria:**
- Dashboard shows: total revenue, order volume, average order value, customer growth, return rate
- Metrics support day/week/month/year comparison
- Admin can drill down by product, category, delivery zone
- Dashboard data refreshes at most every 5 minutes

**Priority:** Medium | **Points:** 5

---

### US-028: Configure Platform Settings
**As an** admin, **I want to** configure global platform settings **so that** business rules are enforced consistently.

**Acceptance Criteria:**
- Admin can configure: tax rates, default shipping fee, return window duration, reservation TTL, max delivery attempts
- Configuration changes are versioned with rollback capability
- Changes take effect within 1 minute without service restart
- All configuration changes are audited

**Priority:** Medium | **Points:** 3

---

### US-029: Manage Notification Templates
**As an** admin, **I want to** manage notification templates **so that** customer and staff communications are consistent and professional.

**Acceptance Criteria:**
- Admin can create and edit templates for each event type (order confirmed, shipped, delivered, etc.) and channel (email, SMS, push)
- Templates support variable placeholders ({{order_id}}, {{customer_name}}, etc.)
- Templates are versioned with rollback to previous version
- Admin can preview templates with sample data before publishing

**Priority:** Low | **Points:** 3

---

### US-030: View Audit Logs
**As an** admin, **I want to** view audit logs **so that** I can investigate incidents and ensure compliance.

**Acceptance Criteria:**
- Audit log captures: actor, action, resource, timestamp, before/after values
- Logs are searchable by actor, action type, resource type, and date range
- Logs are immutable — no edit or delete capability
- Logs are retained for at least 1 year

**Priority:** Medium | **Points:** 3

---

## 6. Finance Stories

### US-031: View Payment Reconciliation
**As a** finance team member, **I want to** view daily payment reconciliation reports **so that** I can ensure all payments are accounted for.

**Acceptance Criteria:**
- Report shows: payment captures, refunds, net settlement, discrepancies
- Discrepancies exceeding configured tolerance are flagged for manual review
- Report can be filtered by date range and payment gateway
- Report can be exported in CSV format

**Priority:** Medium | **Points:** 5

---

### US-032: Process Manual Refunds
**As a** finance team member, **I want to** process manual refunds for edge cases **so that** customers receive their money in exceptional situations.

**Acceptance Criteria:**
- Finance can initiate refund for any order with mandatory reason and supervisor approval
- System validates refund amount does not exceed original payment
- Manual refund is logged in audit trail with approver identity
- Customer receives refund confirmation notification

**Priority:** Medium | **Points:** 3

---

## 7. Cross-Cutting Stories

### US-033: Receive Real-Time Notifications
**As a** user (customer, staff, or admin), **I want to** receive timely notifications for relevant events **so that** I stay informed and can act promptly.

**Acceptance Criteria:**
- Notifications are dispatched within 60 seconds of the triggering event (P95)
- Failed notification delivery is retried up to 3 times with 30-second intervals
- Notification delivery receipts are recorded for audit
- Users can control their notification preferences

**Priority:** High | **Points:** 5

---

### US-034: Idempotent API Operations
**As a** developer, **I want** all mutating API operations to be idempotent **so that** retries and network failures do not cause duplicate side effects.

**Acceptance Criteria:**
- All POST/PUT/PATCH endpoints require `Idempotency-Key` header
- Duplicate requests within 24-hour TTL return cached response without re-executing business logic
- Idempotency scope is `(user_id, route, key)`
- Expired idempotency keys are cleaned up automatically

**Priority:** High | **Points:** 5

---

### US-035: Event-Driven Architecture
**As a** developer, **I want** all state changes to emit domain events via EventBridge **so that** services are decoupled and the system is extensible.

**Acceptance Criteria:**
- Every order state transition emits a domain event with event type, payload, and correlation ID
- Events are published within 2 seconds of the state change (P95)
- Failed event delivery lands in DLQ for manual redrive
- Event consumers are idempotent — duplicate events are safely ignored

**Priority:** High | **Points:** 8
