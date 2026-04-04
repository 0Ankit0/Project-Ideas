# Backend Status Matrix

This matrix reflects the backend implementation status of the Order Management and Delivery System. The system is built on Node.js 20 / TypeScript 5 with an AWS-native serverless-first architecture: Lambda for event-driven workloads, Fargate for sustained services, PostgreSQL 15 (RDS) as the primary relational store, DynamoDB for high-throughput document storage, ElastiCache Redis for caching and idempotency, and OpenSearch for search. EventBridge carries domain events across bounded contexts. Cognito manages identity. S3 stores proof-of-delivery artifacts. SES, SNS, and Pinpoint handle outbound notifications.

Status labels:

- `core`: fundamental capability present from the start; foundational to all other areas
- `complete`: fully implemented including edge cases, error handling, and operational concerns
- `in progress`: partially implemented; primary path works but secondary cases or hardening remain
- `future`: documented and designed but intentionally not implemented in the current phase

| Area | Capability | Status |
|------|------------|--------|
| Auth | Cognito User Pool for customers, Staff Pool for internal users | `core` |
| Auth | JWT verification middleware on all protected routes | `core` |
| Auth | Role-based access control — 6 roles: Customer, DeliveryStaff, WarehouseStaff, OpsManager, Finance, SuperAdmin | `core` |
| Auth | MFA enforcement for Admin and Staff pool users | `complete` |
| Auth | Token refresh and session revocation | `complete` |
| Customer Management | Registration via email, phone number, or social OAuth (Google / Facebook) | `complete` |
| Customer Management | OTP verification for phone-based registration and login | `complete` |
| Customer Management | Customer profile read and update | `complete` |
| Customer Management | Multiple saved addresses with default selection | `complete` |
| Customer Management | Per-customer notification channel preferences (email / SMS / push) | `complete` |
| Customer Management | Account deactivation and GDPR-aligned data deletion | `complete` |
| Product Catalog | Category CRUD with 3-level hierarchy (root → sub → leaf) | `complete` |
| Product Catalog | Product CRUD with rich metadata (description, tags, attributes) | `complete` |
| Product Catalog | Variant management (size, color, or any custom dimension) per product | `complete` |
| Product Catalog | Product image upload to S3 with CDN URL generation | `complete` |
| Product Catalog | Bulk product import via CSV with row-level validation results | `complete` |
| Product Catalog | Category-scoped availability and publish/unpublish controls | `complete` |
| Search | OpenSearch full-text search across product name, description, and tags | `complete` |
| Search | Filter by category, price range, and in-stock availability | `complete` |
| Search | Sort options: relevance, price ascending/descending, newest | `complete` |
| Search | P95 search response ≤ 500 ms under normal load | `complete` |
| Search | Autocomplete / typeahead suggestions | `complete` |
| Inventory | Stock level tracking per SKU per warehouse | `core` |
| Inventory | Inventory reservation with 15-minute TTL on checkout initiation | `complete` |
| Inventory | Auto-expiry of stale reservations via scheduled Lambda | `complete` |
| Inventory | Low-stock alerts when quantity falls below configurable threshold | `complete` |
| Inventory | Manual stock adjustment with mandatory reason and audit trail | `complete` |
| Inventory | Multi-warehouse stock aggregation for availability display | `complete` |
| Cart | Persistent cart stored in DynamoDB (survives browser close) | `core` |
| Cart | Anonymous-to-authenticated cart merge on login | `complete` |
| Cart | Real-time price recalculation on cart view | `complete` |
| Cart | Per-item availability check on cart view with out-of-stock flagging | `complete` |
| Cart | Cart TTL cleanup for abandoned sessions | `complete` |
| Coupon Engine | Coupon CRUD (create, activate, deactivate, archive) | `complete` |
| Coupon Engine | Discount types: percentage, fixed amount, free shipping | `complete` |
| Coupon Engine | Global usage limit and per-customer usage limit enforcement | `complete` |
| Coupon Engine | Validity period (start date / expiry date) enforcement | `complete` |
| Coupon Engine | Category-scoped coupons (applies only to items in specified categories) | `complete` |
| Coupon Engine | Minimum order value requirement | `complete` |
| Coupon Engine | Coupon usage analytics (redemption count, revenue influenced) | `complete` |
| Checkout | Inventory reservation at checkout initiation | `core` |
| Checkout | Delivery zone validation against customer address | `complete` |
| Checkout | Tax and shipping fee calculation based on zone and cart weight | `complete` |
| Checkout | Coupon code application and discount computation | `complete` |
| Checkout | Idempotency guard via ElastiCache (duplicate submission prevention) | `complete` |
| Checkout | Order summary snapshot persisted before payment to prevent price drift | `complete` |
| Order Management | Order creation triggered by payment capture event | `core` |
| Order Management | Unique human-readable order number generation (e.g. OMS-20240601-0001) | `core` |
| Order Management | Order state machine — 7 states: Pending → Confirmed → Processing → ReadyForPickup → OutForDelivery → Delivered → Cancelled | `core` |
| Order Management | Milestone tracking per order stored in DynamoDB with timestamps | `complete` |
| Order Management | Cancellation flow with automatic refund trigger | `complete` |
| Order Management | Delivery address modification allowed while order is in Pending or Confirmed state | `complete` |
| Order Management | Idempotent order creation and state-transition endpoints | `complete` |
| Order Management | Order history and detail view for customer and admin | `complete` |
| Payment | Stripe integration (card payments) | `core` |
| Payment | Khalti integration (local wallet / card) | `core` |
| Payment | Gateway failover — secondary gateway attempted on primary failure | `complete` |
| Payment | Exponential backoff retry on transient failures (base 1 s, max 60 s, 3 attempts) | `complete` |
| Payment | Webhook HMAC signature verification for Stripe and Khalti | `complete` |
| Payment | Payment reconciliation job (daily Lambda, flags mismatches) | `complete` |
| Payment | Payment audit log (immutable record of every gateway interaction) | `complete` |
| Refunds | Automatic refund initiated on order cancellation | `complete` |
| Refunds | Partial refund on partial return acceptance | `complete` |
| Refunds | Refund status tracking — 4 states: Initiated, Processing, Completed, Failed | `complete` |
| Refunds | Manual refund initiation by Finance role | `complete` |
| Refunds | Failed refund retry with escalation alert to Finance | `complete` |
| Fulfillment | Automatic fulfillment task creation on order.confirmed event | `core` |
| Fulfillment | Warehouse assignment based on stock availability and zone proximity | `complete` |
| Fulfillment | Pick list generation for warehouse staff dashboard | `complete` |
| Fulfillment | Barcode scan verification during picking | `complete` |
| Fulfillment | Item mismatch flagging and hold workflow | `complete` |
| Fulfillment | Packing step with dimensions and weight capture | `complete` |
| Fulfillment | Packing slip PDF generation stored to S3 | `complete` |
| Fulfillment | Delivery manifest generation grouped by delivery zone | `complete` |
| Fulfillment | Step Functions orchestration of pick → pack → manifest pipeline | `complete` |
| Delivery | Delivery zone-based staff assignment | `core` |
| Delivery | Staff capacity check before assignment | `complete` |
| Delivery | Push notification to assigned delivery staff via Pinpoint | `complete` |
| Delivery | Status milestone updates: PickedUp → OutForDelivery → Delivered | `complete` |
| Delivery | Milestone ordering enforcement (out-of-sequence updates rejected) | `complete` |
| Delivery | Manual reassignment by Ops Manager | `complete` |
| Delivery | Estimated delivery window communicated to customer on assignment | `complete` |
| POD | Electronic signature capture from customer | `complete` |
| POD | Photo capture (minimum 1 photo required) | `complete` |
| POD | S3 upload with AES-256 SSE encryption | `complete` |
| POD | Offline queue with sync-on-reconnect for low-connectivity areas | `complete` |
| POD | Presigned URL generation for customer and admin view | `complete` |
| Failed Delivery | Failed delivery reason recording — 4 predefined reasons: CustomerAbsent, AddressNotFound, AccessDenied, CustomerRefused | `complete` |
| Failed Delivery | 3-attempt limit per order before escalation | `complete` |
| Failed Delivery | Auto-reschedule to next available delivery window on first/second failure | `complete` |
| Failed Delivery | Customer notification on each failed attempt | `complete` |
| Failed Delivery | ReturnedToWarehouse state transition on 3rd consecutive failure | `complete` |
| Failed Delivery | Automatic stock restore on ReturnedToWarehouse transition | `complete` |
| Returns | Return eligibility check: 7-day return window, excluded category list | `complete` |
| Returns | Return request with mandatory reason and photo evidence | `complete` |
| Returns | Return pickup assignment to delivery staff | `complete` |
| Returns | Warehouse inspection with Accept / Reject / Partial Accept outcomes | `complete` |
| Returns | Refund trigger on return acceptance | `complete` |
| Returns | Inventory restore on accepted return | `complete` |
| Returns | Return status visibility for customer | `complete` |
| Notifications | SES transactional emails for order lifecycle events | `core` |
| Notifications | SNS SMS for OTP delivery and critical order updates | `core` |
| Notifications | Pinpoint push notifications for customer app (order updates) and staff app (assignments) | `complete` |
| Notifications | Versioned notification templates with variable substitution | `complete` |
| Notifications | Delivery receipts tracked per notification | `complete` |
| Notifications | Per-customer channel preference enforcement (email / SMS / push) | `complete` |
| Notifications | Rate limiting to prevent notification spam per customer | `complete` |
| Analytics | Real-time sales metrics via CloudWatch dashboards backed by RDS aggregates | `complete` |
| Analytics | Delivery performance KPIs (on-time rate, attempt rate, failure rate by zone) | `complete` |
| Analytics | Staff performance ranking (deliveries completed, failure rate, POD compliance) | `complete` |
| Analytics | Inventory reports (stock levels, movement, shrinkage) | `complete` |
| Analytics | Report export in CSV and PDF formats | `complete` |
| Analytics | Scheduled report generation and delivery via SES | `complete` |
| Analytics | Report artifacts retained on S3 for 90 days | `complete` |
| Analytics | ML-based demand forecasting and predictive reorder | `future` |
| Admin | RBAC enforcement across all admin endpoints (6 roles) | `core` |
| Admin | Platform configuration management with version history and rollback | `complete` |
| Admin | Staff onboarding and offboarding (account creation, deactivation, zone assignment) | `complete` |
| Admin | Warehouse and delivery zone management | `complete` |
| Admin | Coupon management (create, edit, deactivate) | `complete` |
| Admin | Notification template management (create, version, activate) | `complete` |
| Audit | Immutable audit log for all admin and finance actions | `core` |
| Audit | Audit log searchable by actor, action type, resource ID, and date range | `complete` |
| Audit | 1-year audit log retention with S3 archival after 90 days (RDS) | `complete` |
| Event Architecture | EventBridge custom event bus: `oms.events` | `core` |
| Event Architecture | Domain events published for all order, delivery, payment, and inventory state transitions | `core` |
| Event Architecture | Dead-letter queue (SQS DLQ) for failed event deliveries with alerting | `complete` |
| Event Architecture | Event schema registry (EventBridge Schema Registry) | `complete` |
| Event Architecture | Idempotent event consumers using deduplication keys in ElastiCache | `complete` |
| Event Architecture | Event replay capability for DLQ reprocessing | `complete` |
| Infrastructure (CDK) | Environment-aware CDK stacks: dev, staging, prod | `core` |
| Infrastructure (CDK) | Lambda reserved concurrency per critical function | `complete` |
| Infrastructure (CDK) | Fargate auto-scaling for sustained-load services (search indexer, report generator) | `complete` |
| Infrastructure (CDK) | RDS Multi-AZ deployment for PostgreSQL | `complete` |
| Infrastructure (CDK) | DynamoDB Point-in-Time Recovery (PITR) enabled | `complete` |
| Infrastructure (CDK) | Blue-green deployment for staging environment | `complete` |
| Infrastructure (CDK) | Canary (10 % → 100 %) deployment for production Lambda updates | `complete` |
| Infrastructure (CDK) | VPC with private subnets for RDS, Redis, and Fargate services | `complete` |
| Infrastructure (CDK) | Multi-currency support (ISO 4217 currency codes, exchange-rate service) | `future` |
| Infrastructure (CDK) | Third-party carrier API integration (DHL, FedEx, Aramex) | `future` |

## Requirement Coverage Notes

- **Internal delivery only.** The system manages its own delivery staff and fleet. No third-party carrier APIs (DHL, FedEx, Aramex) are integrated in the current phase. Carrier integration is documented and deferred to a future phase.
- **No real-time GPS tracking.** Delivery location is communicated through discrete status milestones (PickedUp → OutForDelivery → Delivered) rather than a continuous GPS feed. Live map tracking is a future enhancement.
- **Single currency (MVP).** The MVP operates in a single configured currency (NPR by default, configurable at deploy time via platform config). Multi-currency support with ISO 4217 currency codes and an exchange-rate service is designed and deferred to a future phase.
- **Single merchant model.** The system is designed for a single merchant / operator. There is no vendor marketplace, multi-seller catalog, or seller payout logic. A marketplace extension is out of scope for this phase.
- **ML analytics deferred.** Operational analytics (KPIs, reports, dashboards) are implemented using CloudWatch and RDS aggregates. ML-based demand forecasting and predictive reorder recommendations are documented as future work.
