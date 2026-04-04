# Requirements Document

## 1. Introduction

### 1.1 Purpose

This document defines the functional and non-functional requirements for an Order Management and Delivery System built on AWS services. The platform manages the complete order-to-delivery lifecycle using internal delivery personnel, without GPS tracking.

### 1.2 Scope

The system covers:
- Customer account management and self-service portal
- Product catalog with inventory tracking
- Cart, checkout, and payment processing
- Order lifecycle management with status-driven tracking
- Warehouse fulfillment (pick, pack, ship)
- Internal delivery assignment and milestone tracking
- Proof of delivery capture (signature, photo, notes)
- Returns, inspections, and refund processing
- Multi-channel notifications (email, SMS, push)
- Analytics, reporting, and dashboards
- Administrative operations and platform configuration

### 1.3 Definitions

| Term | Definition |
|------|------------|
| **OMS** | Order Management System — central platform for order lifecycle |
| **POD** | Proof of Delivery — signature, photo, and timestamp confirming delivery |
| **Fulfillment Task** | Pick-pack-ship work unit assigned to warehouse staff |
| **Delivery Assignment** | Binding of a fulfilled order to an internal delivery staff member |
| **Delivery Zone** | Geographic area serviced by the platform's internal delivery team |
| **Return Window** | Configurable period after delivery during which returns are accepted |
| **Idempotency Key** | Client-generated unique key ensuring duplicate requests are safely ignored |
| **SLA** | Service Level Agreement — contractual performance target |
| **DLQ** | Dead Letter Queue — holding area for failed event processing |

---

## 2. Functional Requirements

### 2.1 Customer Management Module

#### FR-CM-001: Customer Registration
- System shall allow customers to register using email or phone number
- System shall support social login via Google and Apple
- System shall verify email/phone via OTP before account activation
- System shall enforce unique email and phone constraints

#### FR-CM-002: Customer Profile
- Customers shall manage their profile (name, email, phone, avatar)
- Customers shall view their complete order history with status
- Customers shall manage notification preferences (email, SMS, push)

#### FR-CM-003: Address Management
- Customers shall save multiple delivery addresses with labels (Home, Work, etc.)
- System shall validate address serviceability against configured delivery zones
- System shall support setting a default delivery address
- System shall allow address editing and deletion when not linked to active orders

#### FR-CM-004: Authentication
- System shall implement JWT-based authentication via Amazon Cognito
- System shall support session management with configurable TTL
- System shall enforce password complexity policies (min 8 chars, mixed case, digit, symbol)
- System shall support multi-factor authentication for customer accounts

---

### 2.2 Product Catalog Module

#### FR-PC-001: Category Management
- System shall support hierarchical categories up to 3 levels deep
- Admin shall create, edit, reorder, and archive categories
- Categories shall support custom display attributes and images

#### FR-PC-002: Product Management
- Admin shall create products with title, description, images, specifications, and pricing
- Products shall support multiple variants (size, color, configuration)
- Each variant shall have independent SKU, price, and stock level
- System shall support bulk product import via CSV upload to S3

#### FR-PC-003: Inventory Management
- System shall track stock levels per SKU per warehouse location
- System shall support inventory reservations during checkout with configurable TTL (default 15 min)
- System shall release expired reservations automatically
- System shall prevent overselling by validating stock before order confirmation
- System shall send low-stock alerts when quantity falls below configurable threshold
- System shall support manual stock adjustments with audit trail

#### FR-PC-004: Search and Discovery
- System shall provide full-text product search via Amazon OpenSearch
- System shall support filters by category, price range, availability, and custom attributes
- System shall support sort by relevance, price, popularity, and newest
- System shall return search results within 500 ms at P95

---

### 2.3 Shopping Cart and Checkout Module

#### FR-SC-001: Cart Management
- Customers shall add, remove, and update quantities of cart items
- Cart shall persist across sessions via DynamoDB with ElastiCache hot-path
- System shall display real-time price updates reflecting current catalog prices
- System shall validate item availability on every cart view and at checkout
- System shall merge guest cart with authenticated cart on login

#### FR-SC-002: Checkout Process
- System shall validate all cart items for availability before proceeding
- System shall calculate line item totals, applicable taxes, and shipping fees
- System shall apply discount coupons and promotional offers with stacking rules
- System shall enforce minimum order value constraints per delivery zone
- System shall reserve inventory atomically upon checkout initiation

#### FR-SC-003: Discount and Coupon Engine
- Admin shall create coupons with configurable rules: percentage, fixed amount, free shipping
- Coupons shall support validity period, usage limits (global and per-customer), and minimum order value
- System shall validate coupon applicability at checkout and reject expired or exhausted coupons
- System shall support category-specific and product-specific discounts

---

### 2.4 Order Management Module

#### FR-OM-001: Order Creation
- System shall create orders upon successful payment capture
- System shall generate globally unique order IDs (prefixed, human-readable)
- System shall record complete order snapshot: items, prices, taxes, discounts, shipping, payment reference
- All mutating order endpoints shall require an `Idempotency-Key` header

#### FR-OM-002: Order Tracking
- Customers shall view real-time order status through all lifecycle states
- System shall display timestamped milestone history for each order
- System shall provide estimated delivery window based on fulfillment SLA and delivery zone
- Customers shall receive notifications at every major status transition

#### FR-OM-003: Order Cancellation
- Customers shall cancel orders in `Confirmed` or `ReadyForDispatch` states
- Cancellation of paid orders shall trigger automatic refund to original payment method
- Cancellation reason code shall be mandatory
- System shall release reserved inventory immediately upon cancellation
- Vendors/admin shall be notified of cancellations in real-time

#### FR-OM-004: Order Modification
- Customers shall modify delivery address before order reaches `PickedUp` state
- Address change shall trigger re-validation of delivery zone serviceability
- System shall log all modifications with before/after values and actor identity

---

### 2.5 Payment Module

#### FR-PM-001: Payment Gateway Integration
- System shall integrate with at least two payment gateways (e.g., Stripe, Khalti)
- System shall support credit/debit cards, digital wallets, and bank transfers
- System shall implement gateway failover: if primary fails, route to secondary

#### FR-PM-002: Payment Processing
- System shall perform payment authorization at checkout initiation
- System shall capture payment upon order confirmation
- System shall handle transient payment failures with exponential backoff (base 1 s, max 60 s, 3 retries)
- All payment operations shall be idempotent using gateway-provided idempotency keys
- System shall store payment transaction records with gateway reference IDs

#### FR-PM-003: Refund Processing
- System shall initiate refunds to original payment method on cancellation or return acceptance
- System shall support partial refunds for partial returns
- System shall track refund status (Initiated, Processing, Completed, Failed)
- Failed refunds shall be retried and escalated to admin after 3 attempts

#### FR-PM-004: Payment Reconciliation
- System shall reconcile payment captures against gateway settlement reports daily
- System shall flag discrepancies exceeding configurable tolerance for manual review
- System shall generate payment reconciliation reports accessible to finance role

---

### 2.6 Fulfillment and Picking Module

#### FR-FP-001: Fulfillment Task Creation
- System shall create fulfillment tasks automatically when orders are confirmed
- Tasks shall be assigned to the warehouse location with available stock
- System shall support manual task reassignment by warehouse supervisor

#### FR-FP-002: Pick-Pack Workflow
- Warehouse staff shall view assigned pick lists on their dashboard
- Staff shall scan item barcodes to verify correct picks
- System shall flag pick discrepancies (wrong item, wrong quantity) for supervisor review
- Staff shall mark orders as packed and record package dimensions and weight

#### FR-FP-003: Manifest and Handoff
- System shall generate packing slips with order details, item list, and delivery address
- System shall batch fulfilled orders into delivery manifests grouped by delivery zone
- System shall record warehouse-to-delivery handoff with staff identity and timestamp
- Order shall transition to `ReadyForDispatch` upon manifest generation

---

### 2.7 Delivery Management Module

#### FR-DM-001: Delivery Assignment
- System shall assign orders to available internal delivery staff based on delivery zone
- System shall consider staff capacity (max orders per run) when assigning
- System shall support manual reassignment by operations manager
- System shall notify assigned staff via push notification with delivery details

#### FR-DM-002: Delivery Execution
- Delivery staff shall update order status through milestones: `PickedUp`, `OutForDelivery`, `Delivered`
- Status updates shall record timestamp, staff identity, and optional notes
- System shall not require GPS location for status updates
- System shall enforce milestone ordering — no skipping from `PickedUp` to `Delivered`

#### FR-DM-003: Proof of Delivery
- Delivery staff shall capture electronic signature from recipient
- Delivery staff shall capture at least one timestamped photo at delivery location
- System shall upload POD artifacts to S3 with server-side encryption (AES-256)
- POD shall be linked to the order record and accessible to customer and admin
- System shall support offline POD capture with sync-on-reconnect

#### FR-DM-004: Failed Delivery Handling
- Delivery staff shall record failed delivery reason (customer unavailable, wrong address, refused)
- System shall reschedule failed deliveries for next available delivery window
- Customer shall be notified of failed attempt with reschedule options
- After 3 failed attempts, order shall transition to `ReturnedToWarehouse`
- System shall initiate return-to-stock workflow for returned orders

#### FR-DM-005: Delivery Zone Management
- Admin shall configure delivery zones with geographic boundaries (polygon or PIN-code list)
- Admin shall set delivery fees, minimum order values, and SLA targets per zone
- System shall validate customer addresses against active delivery zones

---

### 2.8 Returns and Refunds Module

#### FR-RR-001: Return Initiation
- Customers shall initiate returns within the configurable return window (default 7 days)
- Return requests shall require reason code and optional photo evidence
- System shall validate return eligibility (within window, non-excluded category, order delivered)

#### FR-RR-002: Return Pickup
- System shall assign return pickup to internal delivery staff in the customer's delivery zone
- Staff shall confirm item collection and update return status to `PickedUp`
- System shall generate return manifest for warehouse receiving

#### FR-RR-003: Inspection and Resolution
- Warehouse staff shall inspect returned items against the original order
- Staff shall record inspection result: Accept, Reject (with reason), or Partial Accept
- Accepted returns shall trigger automatic refund processing
- Rejected returns shall notify customer with rejection reason and next steps

---

### 2.9 Notification Module

#### FR-NM-001: Email Notifications
- System shall send transactional emails via Amazon SES (order confirmation, shipping, delivery, refund)
- System shall support HTML email templates with dynamic content injection
- System shall track email delivery and bounce rates

#### FR-NM-002: SMS Notifications
- System shall send SMS via Amazon SNS for OTP, order status, and delivery updates
- System shall respect customer opt-out preferences
- System shall enforce per-customer SMS rate limits

#### FR-NM-003: Push Notifications
- System shall send push notifications via Amazon Pinpoint to customer and staff mobile apps
- System shall support notification categories (transactional, promotional) with separate opt-in controls
- System shall record push delivery receipts

#### FR-NM-004: Notification Templates
- Admin shall manage notification templates for each event type and channel
- Templates shall support variable substitution (order ID, customer name, delivery window)
- System shall version templates and support rollback to previous versions

---

### 2.10 Analytics and Reporting Module

#### FR-AR-001: Sales Dashboard
- System shall provide real-time sales metrics: total orders, revenue, average order value, conversion rate
- Dashboard shall support date range filters and comparisons (day, week, month, year)
- System shall break down sales by product, category, and delivery zone

#### FR-AR-002: Delivery Performance
- System shall track delivery KPIs: on-time delivery rate, average delivery time, failed delivery rate
- System shall rank delivery staff by performance metrics
- System shall flag SLA breaches and generate escalation reports

#### FR-AR-003: Inventory Reports
- System shall generate stock-level reports with low-stock and out-of-stock highlights
- System shall provide inventory turnover analysis by product and category
- System shall support scheduled report generation and email delivery

#### FR-AR-004: Export
- System shall support report export in CSV and PDF formats
- System shall store generated reports in S3 with configurable retention (default 90 days)

---

### 2.11 Admin and Operations Module

#### FR-AM-001: Role-Based Access Control
- System shall enforce RBAC with roles: Customer, Warehouse Staff, Delivery Staff, Operations Manager, Finance, Admin
- Admin shall configure permissions per role at the API endpoint level
- System shall maintain audit logs for all admin actions

#### FR-AM-002: Platform Configuration
- Admin shall configure global settings: tax rates, shipping fees, return window, reservation TTL
- Admin shall manage delivery zones, warehouse locations, and staff assignments
- Configuration changes shall be versioned with rollback capability

#### FR-AM-003: Staff Management
- Admin shall onboard and offboard warehouse and delivery staff accounts
- Admin shall assign staff to warehouse locations or delivery zones
- System shall track staff activity: tasks completed, hours active, performance score

#### FR-AM-004: Content Management
- Admin shall manage promotional banners, announcements, and static pages
- Admin shall schedule promotional campaigns with start/end dates
- System shall support A/B testing for promotional content

---

## 3. Non-Functional Requirements

### 3.1 Performance

| Requirement | Target |
|-------------|--------|
| API response time | < 500 ms (P95) |
| Product search results | < 500 ms (P95) |
| Order confirmation latency | < 3 seconds end-to-end |
| Concurrent users | 10,000+ |
| Orders per minute | 500+ |
| POD photo upload | < 5 seconds for 5 MB image |

### 3.2 Scalability
- Lambda functions auto-scale with concurrency limits per function
- Fargate services auto-scale based on CPU/memory utilisation (target 70 %)
- DynamoDB on-demand capacity mode for unpredictable workloads
- RDS read replicas for reporting and analytics queries
- ElastiCache cluster mode for horizontal cache scaling
- S3 scales automatically with no provisioning required

### 3.3 Availability
- 99.9 % platform availability (rolling 30 days)
- Multi-AZ deployment for RDS, ElastiCache, and Fargate
- API Gateway and Lambda are inherently multi-AZ
- Zero-downtime deployments via blue-green and canary strategies
- Graceful degradation: payment gateway failover, notification retry, read-replica promotion

### 3.4 Security
- HTTPS/TLS 1.3 for all communications
- PCI-DSS compliance for payment data (tokenisation, no raw card storage)
- Data encryption at rest (S3 SSE-S3, RDS encryption, DynamoDB encryption)
- Data encryption in transit (TLS for all internal service communication)
- WAF rules on API Gateway for OWASP Top 10 protection
- Cognito MFA support for admin and staff accounts
- VPC isolation with private subnets for compute and data layers
- Regular security audits and penetration testing

### 3.5 Reliability
- Automated daily RDS snapshots with 30-day retention
- DynamoDB continuous backups with point-in-time recovery (PITR)
- S3 versioning and cross-region replication for POD artifacts
- EventBridge delivery retry with DLQ for failed event processing
- Circuit breaker pattern for payment gateway and notification calls

### 3.6 Maintainability
- AWS CDK infrastructure as code with environment-aware stacks (dev, staging, prod)
- Structured JSON logging with correlation IDs via CloudWatch
- Distributed tracing via AWS X-Ray across Lambda, Fargate, and API Gateway
- Health check endpoints for all services
- Feature flags via AWS AppConfig for gradual rollouts

### 3.7 Usability
- Mobile-responsive customer portal (React SPA on CloudFront)
- Lightweight mobile-optimised interface for delivery and warehouse staff
- WCAG 2.1 AA accessibility compliance
- Multi-language support (i18n) with locale-aware formatting

---

## 4. System Constraints

### 4.1 Technical Constraints
- AWS-native services only (no third-party infrastructure)
- Serverless-first: Lambda for event-driven, Fargate for sustained workloads
- Event-driven architecture via EventBridge for cross-service communication
- API-first design with OpenAPI 3.1 specification
- PostgreSQL 15 for OLTP; DynamoDB for high-throughput key-value access

### 4.2 Business Constraints
- Internal delivery team only — no third-party carrier integration
- No GPS tracking — status-driven milestone updates only
- Single-currency support in MVP; multi-currency in future phase
- Delivery zones must be explicitly configured before orders can be accepted

### 4.3 Regulatory Constraints
- Consumer protection compliance for returns and refunds
- Data privacy compliance (encryption, access controls, audit trails)
- Payment regulations (PCI-DSS tokenisation, no raw card data storage)
- Electronic signature compliance for proof of delivery
