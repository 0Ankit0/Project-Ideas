# Implementation Playbook

## Overview

Sprint plan, architecture decision records, and cutover checklist for the Order Management and Delivery System.

## Sprint Plan

### Phase 1 — Foundation (Sprints 1-2, 4 weeks)

| Sprint | Focus | Deliverables |
|---|---|---|
| Sprint 1 | Infrastructure + Auth | VPC, RDS, DynamoDB, ElastiCache, Cognito, CDK stacks, CI/CD pipeline |
| Sprint 2 | Core Domain | Customer Service, Product Catalog, Inventory Service, OpenSearch sync |

**Exit Criteria:**
- Infrastructure deployed to dev environment
- Customer registration and login functional
- Product CRUD and search operational
- Inventory tracking with reservation logic

---

### Phase 2 — Order and Payment (Sprints 3-4, 4 weeks)

| Sprint | Focus | Deliverables |
|---|---|---|
| Sprint 3 | Cart + Checkout + Payment | Cart Service (DynamoDB), checkout flow, payment gateway integration (Stripe), idempotency guard |
| Sprint 4 | Order Lifecycle | Order state machine, milestone tracking, cancellation flow, EventBridge event pipeline |

**Exit Criteria:**
- End-to-end checkout working
- Payment capture and refund functional
- Order state machine enforcing all guards
- Events flowing through EventBridge with DLQ

---

### Phase 3 — Fulfillment and Delivery (Sprints 5-7, 6 weeks)

| Sprint | Focus | Deliverables |
|---|---|---|
| Sprint 5 | Fulfillment | Pick-pack workflow, barcode scanning, manifest generation, Step Functions orchestration |
| Sprint 6 | Delivery Core | Delivery zone management, staff assignment engine, status tracking, delivery milestones |
| Sprint 7 | POD + Failed Delivery | POD capture (signature + photo), S3 upload with offline sync, failed delivery flow, rescheduling |

**Exit Criteria:**
- Full order-to-delivery flow working
- POD capture and upload working (including offline)
- Failed delivery with 3-attempt retry logic
- Delivery zone-based assignment

---

### Phase 4 — Returns and Notifications (Sprints 8-9, 4 weeks)

| Sprint | Focus | Deliverables |
|---|---|---|
| Sprint 8 | Returns | Return eligibility, return pickup assignment, inspection workflow, automated refund trigger |
| Sprint 9 | Notifications | Notification templates, SES/SNS/Pinpoint integration, preference management, delivery tracking |

**Exit Criteria:**
- Complete return flow: request → pickup → inspection → refund
- Multi-channel notifications at all order milestones
- Template management for admin

---

### Phase 5 — Analytics, Admin, and Polish (Sprints 10-12, 6 weeks)

| Sprint | Focus | Deliverables |
|---|---|---|
| Sprint 10 | Analytics | Sales dashboard, delivery performance KPIs, inventory reports, report export (CSV/PDF) |
| Sprint 11 | Admin Portal | RBAC management, platform configuration, staff management, coupon management, audit logs |
| Sprint 12 | Polish + Testing | E2E test suite, load testing, security audit, documentation review, staging validation |

**Exit Criteria:**
- All dashboard metrics operational
- Admin portal fully functional
- E2E tests pass for all critical flows
- Load test validates 500 orders/min target
- Security audit findings resolved

---

## Architecture Decision Records (ADRs)

### ADR-001: Serverless-First with Lambda + Fargate Hybrid

**Status:** Accepted

**Context:** Need to balance cost efficiency for low-traffic periods with sustained throughput for fulfillment and delivery services.

**Decision:** Use Lambda for event-driven, short-lived operations (order, payment, inventory, notification). Use Fargate for sustained-connection services (fulfillment, delivery, return, analytics).

**Consequences:**
- Lambda: pay-per-invocation, auto-scaling, cold start trade-off
- Fargate: predictable performance, long-lived connections to RDS, higher baseline cost
- Provisioned concurrency on critical Lambda functions mitigates cold starts

---

### ADR-002: PostgreSQL + DynamoDB Dual Database Strategy

**Status:** Accepted

**Context:** Order and product data requires relational integrity (foreign keys, transactions). Cart and milestone data requires high-throughput key-value access.

**Decision:** RDS PostgreSQL for OLTP (orders, products, payments, staff). DynamoDB for high-velocity data (cart items, order milestones, session state).

**Consequences:**
- Relational integrity for critical business data
- Single-digit millisecond reads for hot-path data
- Increased operational complexity (two database technologies)
- Clear data ownership per database: no cross-database joins

---

### ADR-003: EventBridge Over SQS/SNS for Event Routing

**Status:** Accepted

**Context:** Multiple services need to react to domain events. Need flexible routing without point-to-point wiring.

**Decision:** Use EventBridge custom bus for all domain events. Event rules route to Lambda/Fargate consumers. SQS used only for DLQ.

**Consequences:**
- Content-based routing via event rules (no code changes to add consumers)
- Schema registry for event contract management
- Built-in retry with DLQ on failure
- Cost: $1.00 per million events published (negligible at expected volume)

---

### ADR-004: Status-Driven Delivery Over GPS Tracking

**Status:** Accepted

**Context:** System uses internal delivery staff, not third-party drivers. GPS tracking adds significant complexity (MQTT, Kinesis, geofencing) without proportional value.

**Decision:** Delivery visibility via milestone status updates (PickedUp, OutForDelivery, Delivered) rather than continuous GPS location.

**Consequences:**
- Dramatically simpler architecture (no real-time location infrastructure)
- Lower mobile app battery consumption
- Customers see status milestones, not a map pin
- Sufficient for internal operations where staff is trusted and managed

---

### ADR-005: Idempotency via ElastiCache

**Status:** Accepted

**Context:** Network retries and Lambda retriggers can cause duplicate order creation and payment capture.

**Decision:** All mutating endpoints require `Idempotency-Key` header. Key looked up in ElastiCache before processing. Response cached for 24 hours.

**Consequences:**
- No duplicate orders or payments even with aggressive retries
- ElastiCache adds sub-millisecond latency for key lookup
- Client must generate and persist idempotency keys
- 24-hour key TTL balances safety with storage efficiency

---

## Cutover Checklist

### Pre-Production

- [ ] All CDK stacks deploy successfully to staging
- [ ] E2E test suite passes in staging (checkout, delivery, return)
- [ ] Load test validates 500 orders/min with P95 < 500 ms
- [ ] Security audit findings resolved (OWASP, dependency scan)
- [ ] RDS Multi-AZ failover tested
- [ ] DLQ redrive runbook tested
- [ ] Monitoring dashboards configured and validated
- [ ] All CloudWatch alarms firing correctly in test scenarios
- [ ] Runbooks documented for SEV-1 and SEV-2 scenarios
- [ ] On-call rotation and PagerDuty escalation configured

### Production Deploy

- [ ] DNS cutover via Route 53 weighted routing (10% canary)
- [ ] Monitor canary metrics for 10 minutes
- [ ] If error rate < 1% → promote to 100%
- [ ] If error rate >= 1% → automatic rollback to previous deployment
- [ ] Verify CloudWatch dashboards showing production traffic
- [ ] Verify X-Ray traces showing correct service map
- [ ] Confirm notification channels working (send test email/SMS/push)

### Post-Deploy

- [ ] Monitor DLQ depth for 24 hours (expect 0)
- [ ] Verify first real orders flow through complete lifecycle
- [ ] Confirm payment reconciliation runs successfully next day
- [ ] Review CloudWatch Logs for unexpected errors
- [ ] Performance baseline established (P95, P99 latency snapshots)
