# Order Management and Delivery System

An AWS-native, serverless order management platform covering the complete order-to-delivery lifecycle with internal delivery personnel. The system provides end-to-end visibility from order placement through fulfillment, internal staff delivery, and proof of delivery — without GPS tracking. Delivery transparency is achieved through status-driven milestone updates rather than continuous location monitoring.

## Domain Description

Businesses managing their own delivery operations need a unified system that bridges the gap between order capture, warehouse fulfillment, and last-mile delivery by internal staff. Unlike third-party logistics platforms, this system assumes a dedicated delivery team where assignments, routes, and delivery confirmations are managed internally. Customers expect accurate status updates and proactive notifications; operations managers require fulfillment SLA dashboards and delivery performance analytics; warehouse staff need clear pick-pack-ship workflows; and delivery personnel need a lightweight interface for status updates and proof of delivery.

**Core domain concepts:**
- **Order** — the primary aggregate: captures customer, line items, pricing, payment, fulfillment status, and delivery state.
- **Customer** — registered buyer with profile, addresses, order history, and notification preferences.
- **Product** — catalog item with variants, pricing tiers, images, and inventory tracking.
- **Inventory** — stock levels per product/variant per warehouse location with reservation and adjustment support.
- **Fulfillment Task** — pick-pack-ship work unit assigned to warehouse staff for a specific order.
- **Delivery Assignment** — binding of a fulfilled order to an internal delivery staff member with scheduled delivery window.
- **Proof of Delivery (POD)** — collection of delivery artifacts: recipient signature, timestamped photo, and delivery notes.
- **Return Request** — authorisation record for reverse flow: return pickup, inspection, and refund trigger.
- **Payment Transaction** — payment capture, refund, and settlement record linked to a payment gateway.

## Technology Stack

| Layer | Technology | Notes |
|---|---|---|
| API Gateway | Amazon API Gateway | REST APIs, JWT validation, rate limiting, usage plans |
| Compute | AWS Lambda + AWS Fargate | Lambda for event-driven handlers; Fargate for long-running services |
| Database (OLTP) | Amazon RDS (PostgreSQL 15) | Multi-AZ deployment, read replicas for reporting workloads |
| Database (NoSQL) | Amazon DynamoDB | Order status timeline, delivery milestones, session/cart data |
| Cache | Amazon ElastiCache (Redis) | Cart hot-path, session store, idempotency keys, rate-limit counters |
| Search | Amazon OpenSearch Service | Product full-text search, order search, analytics dashboards |
| Object Storage | Amazon S3 | POD photos, invoices, product images, report exports |
| Event Bus | Amazon EventBridge | Event-driven order lifecycle, cross-service communication |
| Workflow | AWS Step Functions | Fulfillment orchestration, return processing, payment reconciliation |
| Notification | Amazon SNS + SES + Pinpoint | SMS, email, and push notification delivery |
| Auth | Amazon Cognito | Customer and staff authentication, RBAC, MFA |
| CDN | Amazon CloudFront | Static assets, product images, customer-facing SPA |
| Monitoring | Amazon CloudWatch + AWS X-Ray | Metrics, structured logs, distributed tracing |
| IaC | AWS CDK (TypeScript) | Infrastructure as code with environment-aware stacks |
| CI/CD | AWS CodePipeline + CodeBuild | Automated testing, staging promotion, production deployment |

## Documentation Structure

Project root artifact: [`traceability-matrix.md`](./traceability-matrix.md) provides cross-phase requirement-to-implementation linkage.


```
Order Management and Delivery System/
├── traceability-matrix.md
├── requirements/
│   ├── requirements-document.md   ← Full functional & non-functional requirements
│   └── user-stories.md            ← 35+ user stories with acceptance criteria
├── analysis/
│   ├── use-case-diagram.md        ← UML use case diagram with all actors
│   ├── use-case-descriptions.md   ← Detailed flows with pre/post conditions
│   ├── system-context-diagram.md  ← C4 Level-0 system boundary
│   ├── activity-diagram.md        ← Order, fulfillment, delivery, return workflows
│   ├── bpmn-swimlane-diagram.md   ← Cross-functional handoff diagrams
│   ├── data-dictionary.md         ← Entity definitions, constraints, relationships
│   ├── business-rules.md          ← Invariants, policies, enforcement rules
│   └── event-catalog.md           ← Domain event catalogue with schemas
├── high-level-design/
│   ├── system-sequence-diagram.md ← Key flows as sequence diagrams
│   ├── domain-model.md            ← Core aggregates and relationships
│   ├── data-flow-diagram.md       ← Data movement and retention
│   ├── architecture-diagram.md    ← AWS solution architecture
│   └── c4-context-container.md    ← C4 context and container diagrams
├── detailed-design/
│   ├── class-diagram.md           ← Detailed classes, methods, attributes
│   ├── sequence-diagram.md        ← Internal service interactions
│   ├── state-machine-diagram.md   ← Order and delivery lifecycle FSM
│   ├── erd-database-schema.md     ← Full database schema with indexes
│   ├── component-diagram.md       ← Software module dependencies
│   ├── api-design.md              ← REST API endpoint catalogue
│   └── c4-component.md            ← C4 component diagrams per service
├── infrastructure/
│   ├── deployment-diagram.md      ← AWS topology and scaling policies
│   ├── network-infrastructure.md  ← VPC, subnets, security groups, WAF
│   └── cloud-architecture.md      ← Multi-AZ, DR, backup strategy
├── edge-cases/
│   ├── README.md                  ← Scenario-to-response matrix
│   ├── order-lifecycle-and-payment.md
│   ├── inventory-and-fulfillment.md
│   ├── delivery-and-proof.md
│   ├── returns-and-refunds.md
│   ├── api-and-ui.md
│   ├── security-and-compliance.md
│   └── operations.md
└── implementation/
    ├── code-guidelines.md         ← Development standards, conventions
    ├── c4-code-diagram.md         ← Code-level C4 diagrams
    └── implementation-playbook.md ← Sprint plan, ADRs, cutover checklist
```

## Key Features

- **Complete order lifecycle management** with 9 explicit states and guarded transitions — from Draft through Delivered, with cancellation and return paths.
- **Product catalog with inventory tracking** supporting categories, variants, images, pricing tiers, and real-time stock level synchronisation across warehouse locations.
- **Integrated cart and checkout** with persistent cart, real-time price calculation, tax computation, discount/coupon application, and address serviceability validation.
- **Multi-gateway payment processing** with payment capture, authorization hold, automatic refund on cancellation, and retry with exponential backoff on transient failures.
- **Warehouse fulfillment workflow** with pick list generation, pack verification, manifest creation, and handoff to delivery queue — all driven by Step Functions orchestration.
- **Internal delivery management** with staff assignment, delivery window scheduling, route sheet generation, and status-driven milestone tracking (no GPS dependency).
- **Proof of Delivery (POD)** capturing electronic signature, timestamped photo, and delivery notes — uploaded to S3 with server-side encryption and linked to the order record.
- **Returns and reverse logistics** with configurable return window, return pickup by internal staff, goods inspection workflow, and automated refund trigger on acceptance.
- **Event-driven notification engine** dispatching email (SES), SMS (SNS), and push (Pinpoint) notifications at every order milestone with template management and delivery tracking.
- **Real-time analytics and reporting** with sales dashboards, delivery performance KPIs, inventory reports, and staff performance scoring via OpenSearch and CloudWatch.
- **Role-based access control** via Cognito with distinct permission sets for customers, warehouse staff, delivery staff, operations managers, and platform administrators.
- **Serverless-first AWS architecture** with Lambda for event handling, Fargate for sustained workloads, EventBridge for decoupled communication, and CDK for reproducible infrastructure.

## Getting Started

- Review [`traceability-matrix.md`](./traceability-matrix.md) first to navigate requirement-to-implementation coverage across phases.
1. **Read requirements first** — `requirements/requirements-document.md` defines all functional requirements across 11 modules and non-functional requirements for performance, security, and availability.
2. **Review user stories** — `requirements/user-stories.md` provides role-based acceptance criteria for feature implementation and QA.
3. **Understand the domain** — `analysis/use-case-diagram.md` maps actors to capabilities; `analysis/data-dictionary.md` defines all entities and constraints; `analysis/business-rules.md` captures invariants.
4. **Study the event contracts** — `analysis/event-catalog.md` is the authoritative schema catalogue; all services produce and consume events conforming to this catalogue.
5. **Architecture overview** — `high-level-design/architecture-diagram.md` shows the AWS solution architecture; `high-level-design/c4-context-container.md` provides C4 context and container views.
6. **API and schema** — `detailed-design/api-design.md` and `detailed-design/erd-database-schema.md` are the implementation source of truth for REST endpoints and data models.
7. **State machine** — `detailed-design/state-machine-diagram.md` defines every guard, action, and side-effect for order and delivery lifecycle transitions.
8. **Deploy** — follow `infrastructure/cloud-architecture.md` for AWS topology, then `implementation/implementation-playbook.md` for sprint plan and cutover checklist.
9. **Validate edge cases** — review `edge-cases/` playbooks in staging before production rollout to verify degraded-mode behaviour and recovery procedures.

## End-to-End Order Flow

### Phase 1 — Browse and Cart

1. Customer browses product catalog; OpenSearch powers full-text search with filters.
2. Customer adds items to cart; cart state persisted in DynamoDB with ElastiCache hot-path.
3. System validates stock availability in real-time and reserves inventory on checkout initiation.

### Phase 2 — Checkout and Payment

4. Customer selects delivery address; system validates address serviceability against configured delivery zones.
5. System calculates order total: line items + tax + shipping fee − discount/coupon.
6. Customer selects payment method; API Gateway forwards to Payment Service with `Idempotency-Key`.
7. Payment Service initiates capture via payment gateway; on success, order transitions `Draft → Confirmed`.
8. EventBridge emits `order.confirmed.v1`; Notification Service sends order confirmation email/SMS.

### Phase 3 — Fulfillment

9. Fulfillment Service consumes `order.confirmed.v1` and creates a pick-pack task for the assigned warehouse.
10. Warehouse staff receives task on their dashboard; picks items, scans barcodes for verification.
11. Staff marks order as packed; system generates packing slip and manifest.
12. Order transitions `Confirmed → ReadyForDispatch`; EventBridge emits `order.ready_for_dispatch.v1`.

### Phase 4 — Delivery

13. Delivery Assignment Service assigns order to an available internal delivery staff member based on delivery zone and capacity.
14. Delivery staff receives assignment notification with delivery details and route sheet.
15. Staff picks up package from warehouse; order transitions `ReadyForDispatch → PickedUp`.
16. Staff updates status to `OutForDelivery` when starting the delivery run.
17. At destination, staff captures recipient signature + timestamped photo as proof of delivery.
18. POD uploaded to S3; order transitions `OutForDelivery → Delivered`; EventBridge emits `order.delivered.v1`.
19. Customer receives delivery confirmation with POD download link.

### Phase 5 — Exception and Recovery

20. Any failed delivery attempt triggers `order.delivery_failed.v1` with reason code.
21. System reschedules delivery or contacts customer for alternate instructions.
22. After 3 failed attempts, order transitions to `ReturnedToWarehouse` and initiates return-to-stock workflow.

### Phase 6 — Returns

23. Customer initiates return within the configurable return window via self-service portal.
24. Return pickup assigned to internal delivery staff; staff collects item from customer.
25. Warehouse receives returned item; inspection determines accept/reject.
26. On acceptance, refund triggered to original payment method; `order.refunded.v1` emitted.

## Canonical State Machine Summary

| State | Entry Criteria | Allowed Next States | Exit Event | Notes |
|---|---|---|---|---|
| `Draft` | Cart checkout initiated, items reserved | `Confirmed`, `Cancelled` | `order.confirmed` | Inventory reserved; 15-min reservation TTL. |
| `Confirmed` | Payment captured successfully | `ReadyForDispatch`, `Cancelled` | `order.ready_for_dispatch` | SLA clock starts; cancellation triggers refund. |
| `ReadyForDispatch` | Pick-pack complete, manifest generated | `PickedUp`, `Cancelled` | `order.picked_up` | Delivery assignment must happen within SLA window. |
| `PickedUp` | Delivery staff confirms package custody | `OutForDelivery` | `order.out_for_delivery` | Staff identity and timestamp recorded. |
| `OutForDelivery` | Delivery run started | `Delivered`, `DeliveryFailed` | `order.delivered` | Max 3 attempts before auto-return. |
| `Delivered` | POD accepted and recorded | `ReturnRequested` | `order.closed` | Immutable post-delivery; return window starts. |
| `DeliveryFailed` | Delivery attempt unsuccessful | `OutForDelivery`, `ReturnedToWarehouse` | `order.delivery_rescheduled` | Reason code mandatory; customer contacted. |
| `ReturnRequested` | Customer requests return within window | `ReturnPickedUp` | `order.return_picked_up` | Return reason and evidence required. |
| `ReturnPickedUp` | Staff collects returned item | `Refunded`, `ReturnRejected` | `order.refunded` | Inspection determines outcome. |
| `Refunded` | Refund processed to original method | *(terminal)* | `order.closed` | Settlement and analytics triggered. |
| `ReturnedToWarehouse` | Failed delivery, item back in warehouse | *(terminal)* | `order.closed` | Stock restored; customer notified. |
| `Cancelled` | Order cancelled before delivery | *(terminal)* | `order.closed` | Cancellation reason required; refund if paid. |

## Monitoring, SLOs, and Alerting

### SLO Targets

| SLO | Target | Measurement Window |
|---|---|---|
| Platform availability | 99.9 % | Rolling 30 days |
| P95 API response time | < 500 ms | Rolling 1 hour |
| P95 order-confirmation latency | < 3 seconds | Rolling 24 hours |
| P95 event publish latency (EventBridge) | < 2 seconds | Rolling 1 hour |
| P95 notification dispatch | < 60 seconds | Rolling 24 hours |
| POD upload success rate | > 99.5 % | Rolling 7 days |
| Daily DLQ redrive success rate | > 99 % within 4 hours | Daily |

### Alert Severity Policy

| Severity | Trigger Condition | Response Time | Escalation |
|---|---|---|---|
| SEV-1 | Payment service down; order pipeline halted; API Gateway 5xx > 5 % for 5 min | Immediate page | On-call engineer + engineering manager |
| SEV-2 | DLQ depth growing > threshold for 15 min; fulfillment SLA breach rate > 10 %; notification failures > 5 % | 15-minute response | On-call engineer |
| SEV-3 | Non-critical service degradation; SLO budget < 20 % remaining; elevated error rate on non-critical path | Next business day | Team Slack channel |

## Documentation Status

- ✅ Traceability coverage is available via [`traceability-matrix.md`](./traceability-matrix.md).
| Document | Status | Last Updated |
|---|---|---|
| `requirements/requirements-document.md` | ✅ Complete | Current |
| `requirements/user-stories.md` | ✅ Complete | Current |
| `analysis/use-case-diagram.md` | ✅ Complete | Current |
| `analysis/use-case-descriptions.md` | ✅ Complete | Current |
| `analysis/system-context-diagram.md` | ✅ Complete | Current |
| `analysis/activity-diagram.md` | ✅ Complete | Current |
| `analysis/bpmn-swimlane-diagram.md` | ✅ Complete | Current |
| `analysis/data-dictionary.md` | ✅ Complete | Current |
| `analysis/business-rules.md` | ✅ Complete | Current |
| `analysis/event-catalog.md` | ✅ Complete | Current |
| `high-level-design/system-sequence-diagram.md` | ✅ Complete | Current |
| `high-level-design/domain-model.md` | ✅ Complete | Current |
| `high-level-design/data-flow-diagram.md` | ✅ Complete | Current |
| `high-level-design/architecture-diagram.md` | ✅ Complete | Current |
| `high-level-design/c4-context-container.md` | ✅ Complete | Current |
| `detailed-design/class-diagram.md` | ✅ Complete | Current |
| `detailed-design/sequence-diagram.md` | ✅ Complete | Current |
| `detailed-design/state-machine-diagram.md` | ✅ Complete | Current |
| `detailed-design/erd-database-schema.md` | ✅ Complete | Current |
| `detailed-design/component-diagram.md` | ✅ Complete | Current |
| `detailed-design/api-design.md` | ✅ Complete | Current |
| `detailed-design/c4-component.md` | ✅ Complete | Current |
| `infrastructure/deployment-diagram.md` | ✅ Complete | Current |
| `infrastructure/network-infrastructure.md` | ✅ Complete | Current |
| `infrastructure/cloud-architecture.md` | ✅ Complete | Current |
| `edge-cases/*` | ✅ Complete | Current |
| `implementation/code-guidelines.md` | ✅ Complete | Current |
| `implementation/c4-code-diagram.md` | ✅ Complete | Current |
| `implementation/implementation-playbook.md` | ✅ Complete | Current |
