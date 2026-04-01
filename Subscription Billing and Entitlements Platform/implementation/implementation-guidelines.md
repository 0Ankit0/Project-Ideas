# Implementation Guidelines — Subscription Billing and Entitlements Platform

## Overview

This document provides phased implementation guidance for building the Subscription Billing and Entitlements Platform from initial foundation through production-hardened deployment. The platform supports complex billing models — flat-rate, per-seat, usage-based, and hybrid — with full entitlement enforcement, tax compliance, and revenue recognition.

Each phase delivers a vertical slice of working, tested functionality. Teams should treat each phase as a production deployment milestone, not a waterfall stage.

---

## Technology Stack

| Component | Technology | Version | Rationale |
|-----------|-----------|---------|-----------|
| Primary Language | Go | 1.22 | High concurrency, low latency, strong typing; ideal for billing state machines |
| Relational Database | PostgreSQL | 15 | ACID compliance essential for financial records; native JSONB for plan metadata |
| Cache / Feature Flags | Redis | 7.2 | Sub-millisecond entitlement checks; atomic operations for idempotency keys |
| Message Broker | Apache Kafka | 3.6 | Durable, replayable usage event stream; exactly-once delivery for billing |
| API Gateway | Kong | 3.5 | Rate limiting, auth, routing across microservices |
| Container Runtime | Kubernetes | 1.29 | Horizontal pod autoscaling for usage ingestion spikes |
| Service Mesh | Istio | 1.20 | mTLS between services, traffic policies, circuit breaking |
| Object Storage | AWS S3 | — | Invoice PDF archival, usage file backups |
| Distributed Tracing | Jaeger | 1.54 | Full trace correlation across billing pipeline |
| Metrics | Prometheus + Grafana | 2.50 / 10.2 | SLO dashboards, alert rules, capacity planning |
| Secrets Management | HashiCorp Vault | 1.15 | PCI-scoped secret rotation, dynamic database credentials |
| CI/CD | GitHub Actions + ArgoCD | — | Branch-based promotion; GitOps deployment model |
| Infrastructure as Code | Terraform | 1.6 | Reproducible multi-region infrastructure |
| Tax Engine | Avalara AvaTax | REST v2 | Real-time tax calculation for 12,000+ jurisdictions |
| PDF Generation | Gotenberg | 7.9 | Headless Chrome-based PDF rendering from HTML templates |

---

## Testing Strategy

| Layer | Tool | Coverage Target | Notes |
|-------|------|----------------|-------|
| Unit Tests | Go `testing` + `testify` | 85% line coverage | All business logic, state machines, calculation engines |
| Integration Tests | `testcontainers-go` | All DB queries and repo methods | Spin up real PostgreSQL, Redis per test suite |
| Contract Tests | Pact | All payment gateway adapters | Consumer-driven; run against sandbox environments |
| End-to-End Tests | Playwright + custom Go harness | 15 critical billing flows | Full lifecycle: signup → billing → cancellation |
| Load Tests | k6 | 10x peak traffic | Usage ingestion: 50k events/sec; API: 5k req/sec |
| Mutation Tests | `go-mutesting` | Core billing logic | Ensures tests catch business logic regressions |
| Security Scans | Snyk + Trivy | All dependencies and images | Fail CI on critical CVEs |
| Performance Benchmarks | Go `testing.B` | Rating and proration engines | < 5ms p99 for invoice line item calculation |

---

## Phase 1: Foundation (Weeks 1–6)

### Objectives

Establish the data model, core APIs, and development environment. By end of Phase 1, the system accepts plan definitions, creates subscriptions, generates draft invoices manually, and stores tokenized payment methods.

### 1.1 Plan Catalog Service

The Plan Catalog Service owns the canonical definition of every billable product. Plans are immutable after activation; changes create a new `PlanVersion`. This preserves historical billing accuracy for existing subscribers.

**Data model highlights:**

```sql
CREATE TABLE plans (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id   TEXT UNIQUE NOT NULL,          -- human-readable slug
    name          TEXT NOT NULL,
    description   TEXT,
    status        TEXT NOT NULL DEFAULT 'draft', -- draft | active | archived
    billing_model TEXT NOT NULL,                 -- flat_rate | per_seat | usage_based | hybrid
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE plan_versions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id         UUID NOT NULL REFERENCES plans(id),
    version_number  INTEGER NOT NULL,
    effective_from  TIMESTAMPTZ NOT NULL,
    effective_until TIMESTAMPTZ,
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (plan_id, version_number)
);

CREATE TABLE prices (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_version_id  UUID NOT NULL REFERENCES plan_versions(id),
    currency         CHAR(3) NOT NULL,
    billing_period   TEXT NOT NULL, -- monthly | quarterly | annual
    pricing_model    TEXT NOT NULL, -- flat | graduated | volume | package
    unit_amount      BIGINT,        -- in cents; NULL for tiered models
    tiers            JSONB,         -- array of {up_to, unit_amount, flat_amount}
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**API endpoints:**

- `POST /v1/plans` — Create a plan in `draft` state
- `GET /v1/plans/{planId}` — Retrieve plan with current active version
- `PATCH /v1/plans/{planId}` — Update plan metadata (draft only)
- `POST /v1/plans/{planId}/activate` — Transition plan to `active`
- `POST /v1/plans/{planId}/versions` — Create a new plan version (triggers version lock on prior version)
- `GET /v1/plans/{planId}/versions` — List all versions with effective date ranges
- `POST /v1/plans/{planId}/prices` — Add a price to the active version
- `GET /v1/prices/{priceId}` — Retrieve a specific price configuration

**Business rules enforced:**

- A plan must have at least one price before it can be activated.
- Currency + billing period combination must be unique per plan version.
- Archived plans reject new subscription creation but continue billing existing subscribers.
- Price tier breakpoints must be strictly ascending; the last tier must have `up_to = null`.

### 1.2 Basic Subscription Management

Subscriptions track the lifecycle of a customer's relationship with a plan. The state machine is central to all downstream billing behavior.

**Subscription states:** `trialing` → `active` → `past_due` → `canceled` / `paused`

```sql
CREATE TABLE subscriptions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id          UUID NOT NULL,
    plan_version_id     UUID NOT NULL REFERENCES plan_versions(id),
    status              TEXT NOT NULL DEFAULT 'trialing',
    current_period_start TIMESTAMPTZ NOT NULL,
    current_period_end  TIMESTAMPTZ NOT NULL,
    trial_end           TIMESTAMPTZ,
    canceled_at         TIMESTAMPTZ,
    cancel_at_period_end BOOLEAN NOT NULL DEFAULT false,
    metadata            JSONB NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**API endpoints:**

- `POST /v1/subscriptions` — Create subscription, optionally with trial period
- `GET /v1/subscriptions/{subscriptionId}` — Retrieve subscription with plan details
- `GET /v1/accounts/{accountId}/subscriptions` — List all subscriptions for an account
- `POST /v1/subscriptions/{subscriptionId}/cancel` — Cancel immediately or at period end
- `GET /v1/subscriptions/{subscriptionId}/upcoming-invoice` — Preview next invoice

### 1.3 Manual Invoice Generation

Invoices in Phase 1 are triggered manually. Automated scheduling is introduced in Phase 2.

**Invoice states:** `draft` → `open` → `paid` / `void` / `uncollectible`

Line items are individually typed: `subscription`, `usage`, `proration`, `credit`, `tax`, `discount`.

```sql
CREATE TABLE invoices (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id       UUID NOT NULL,
    subscription_id  UUID REFERENCES subscriptions(id),
    status           TEXT NOT NULL DEFAULT 'draft',
    currency         CHAR(3) NOT NULL,
    subtotal         BIGINT NOT NULL DEFAULT 0, -- cents
    tax_amount       BIGINT NOT NULL DEFAULT 0,
    discount_amount  BIGINT NOT NULL DEFAULT 0,
    credit_applied   BIGINT NOT NULL DEFAULT 0,
    total            BIGINT NOT NULL DEFAULT 0,
    due_date         DATE,
    period_start     TIMESTAMPTZ,
    period_end       TIMESTAMPTZ,
    idempotency_key  TEXT UNIQUE,
    finalized_at     TIMESTAMPTZ,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**API endpoints:**

- `POST /v1/invoices` — Create a draft invoice for a subscription period
- `GET /v1/invoices/{invoiceId}` — Retrieve invoice with all line items
- `POST /v1/invoices/{invoiceId}/finalize` — Transition draft to open; triggers payment collection
- `POST /v1/invoices/{invoiceId}/void` — Void an open invoice with reason
- `GET /v1/accounts/{accountId}/invoices` — List invoices with pagination and status filter

### 1.4 Payment Method Storage

Payment methods are never stored natively. The platform stores gateway tokens only. Stripe is the initial integration; PayPal and Braintree adapters are added in Phase 2.

**Integration pattern:**

1. Client calls `POST /v1/payment-methods/setup-intent` to obtain a Stripe SetupIntent client secret.
2. Client collects card data directly in Stripe.js; Stripe returns a `PaymentMethod` ID.
3. Client calls `POST /v1/payment-methods` with the Stripe `PaymentMethod` ID.
4. Platform confirms the payment method with Stripe, stores the token and card metadata (last 4, brand, expiry month/year).

```sql
CREATE TABLE payment_methods (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id      UUID NOT NULL,
    gateway         TEXT NOT NULL,          -- stripe | paypal | braintree
    gateway_token   TEXT NOT NULL,          -- opaque gateway reference
    type            TEXT NOT NULL,          -- card | bank_account | wallet
    last_four       CHAR(4),
    card_brand      TEXT,
    exp_month       SMALLINT,
    exp_year        SMALLINT,
    is_default      BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 1.5 Basic Entitlement Framework

Entitlements define what features or quantities a subscriber is allowed to use. Phase 1 establishes the data model and check API; enforcement logic is hardened in Phase 3.

```sql
CREATE TABLE entitlements (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id      UUID NOT NULL,
    subscription_id UUID REFERENCES subscriptions(id),
    feature_key     TEXT NOT NULL,
    enforcement     TEXT NOT NULL, -- hard_cap | soft_cap | metered
    limit_value     BIGINT,        -- NULL = unlimited
    current_usage   BIGINT NOT NULL DEFAULT 0,
    reset_at        TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**API endpoints:**

- `GET /v1/entitlements/{accountId}/{featureKey}` — Check entitlement with current usage
- `POST /v1/entitlements/{accountId}/{featureKey}/increment` — Increment usage counter atomically

### Phase 1 Deliverables

- Fully functional Plan Catalog API with version management
- Subscription lifecycle API (create, retrieve, cancel)
- Manual invoice generation with line item support
- Payment method tokenization flow with Stripe
- Entitlement data model and check API
- PostgreSQL schema with migrations (using `golang-migrate`)
- Redis connection pool for entitlement caching
- Docker Compose environment for local development
- Unit test suite with ≥ 85% coverage on all service packages
- Integration tests using `testcontainers-go` for all repository methods

---

## Phase 2: Core Billing (Weeks 7–14)

### Objectives

Automate the full billing cycle. Usage events flow from ingestion through aggregation into rated invoice line items. Payment collection is automated with dunning for failed payments.

### 2.1 Usage Metering Service

The Usage Metering Service receives raw usage events from client SDKs and internal services, deduplicates them, and aggregates them per billing period.

**Ingestion pipeline:**

1. Client sends usage event to `POST /v1/usage/events` with an `idempotency_key`.
2. API layer writes event to Kafka topic `usage.raw.v1` and acknowledges immediately.
3. Consumer group `usage-dedup` reads from `usage.raw.v1`, checks Redis for the `idempotency_key` (TTL: 90 days), discards duplicates, and forwards to `usage.deduplicated.v1`.
4. Consumer group `usage-aggregator` reads from `usage.deduplicated.v1`, upserts into `usage_aggregates` table.

**Kafka topic design:**

| Topic | Partitions | Retention | Key |
|-------|-----------|-----------|-----|
| `usage.raw.v1` | 32 | 7 days | `account_id` |
| `usage.deduplicated.v1` | 32 | 7 days | `account_id` |
| `billing.events.v1` | 16 | 30 days | `subscription_id` |
| `invoice.generated.v1` | 8 | 30 days | `invoice_id` |
| `payment.events.v1` | 16 | 30 days | `account_id` |

**Deduplication:** Redis `SET idempotency:{key} 1 EX 7776000 NX` — returns 0 if key already exists.

**Aggregation:** Sum events by `(account_id, subscription_id, feature_key, period_start, period_end)`.

### 2.2 Automated Billing Scheduler

A Go worker (deployed as a Kubernetes CronJob) runs every minute and queries for subscriptions whose `current_period_end <= now() + 1 hour`. For each matched subscription it:

1. Acquires a distributed lock in Redis: `SET billing-lock:{subscriptionId} 1 EX 3600 NX`.
2. Creates an invoice draft with an idempotency key of `{subscriptionId}:{periodStart}:{periodEnd}`.
3. Populates line items: subscription fees, rated usage, proration adjustments.
4. Calls the Tax Service for applicable taxes.
5. Applies available credits and active coupons.
6. Finalizes the invoice and triggers payment collection.
7. Advances `current_period_start` and `current_period_end` on the subscription.
8. Publishes `InvoiceGenerated` event to `invoice.generated.v1`.

The idempotency key on the invoice prevents duplicate generation if the scheduler fires multiple times (clock skew, pod restart).

### 2.3 Payment Gateway Adapters

All gateway adapters implement the `PaymentGateway` interface:

```go
type PaymentGateway interface {
    ChargePaymentMethod(ctx context.Context, req ChargeRequest) (*ChargeResult, error)
    RefundCharge(ctx context.Context, chargeID string, amount int64) (*RefundResult, error)
    CreateSetupIntent(ctx context.Context, accountID string) (*SetupIntentResult, error)
    GetPaymentMethod(ctx context.Context, token string) (*PaymentMethodDetails, error)
    ValidateWebhookSignature(payload []byte, signature string) error
}
```

**Stripe adapter:** Uses `github.com/stripe/stripe-go/v76`. Handles 3DS2 authentication redirects; records `payment_intent_id` for audit.

**PayPal adapter:** Uses PayPal Orders API v2. Maps PayPal order states to platform `ChargeResult` states.

**Braintree adapter:** Uses `github.com/braintree/braintree-go`. Supports PayPal vault tokens and credit cards.

All gateway errors are mapped to a platform-internal `PaymentError` type with `Code`, `DeclineCode`, `Retryable bool`, and `GatewayMessage` fields.

### 2.4 Dunning Engine

The Dunning Engine manages the retry lifecycle for failed payments via a configurable state machine.

**Default retry schedule (configurable per plan or account):**

| Attempt | Delay After Previous Failure | Action |
|---------|----------------------------|--------|
| 1 | Immediate | Retry charge |
| 2 | 3 days | Retry charge + send reminder email |
| 3 | 5 days | Retry charge + send final warning email |
| 4 | 7 days | Retry charge; on failure → mark subscription `past_due`, suspend entitlements |
| 5 | 14 days | Final retry; on failure → mark subscription `canceled`, issue cancellation notice |

The dunning scheduler is a Go worker that queries `dunning_attempts` for entries where `next_attempt_at <= now()` and status = `scheduled`. It respects soft delete on subscriptions (does not retry a manually canceled subscription).

### 2.5 Proration Engine

When a subscriber changes plans mid-cycle, the Proration Engine calculates the credit for unused time on the old plan and the charge for the remaining time on the new plan.

**Calculation:**

```
days_remaining = (period_end - change_date).days
days_in_period = (period_end - period_start).days
credit_amount  = (old_plan_price / days_in_period) * days_remaining
charge_amount  = (new_plan_price / days_in_period) * days_remaining
proration_net  = charge_amount - credit_amount
```

Proration adjustments are added as line items of type `proration_credit` and `proration_charge` on the next invoice. The proration calculation is recorded immutably in `proration_adjustments` for audit purposes.

### Phase 2 Deliverables

- Usage Metering Service with Kafka-backed ingestion and Redis deduplication
- Automated billing scheduler with distributed locking
- Stripe, PayPal, and Braintree payment gateway adapters
- Dunning engine with configurable retry schedules and state machine
- Proration engine for mid-cycle plan changes
- End-to-end automated billing cycle from subscription renewal to payment collection
- Contract tests (Pact) for all three payment gateway adapters against sandbox environments
- Load test: usage ingestion sustains 50,000 events/second at p99 < 100ms

---

## Phase 3: Advanced Features (Weeks 15–22)

### Objectives

Add compliance-critical features: tax calculation, entitlement enforcement, revenue recognition, and customer-facing billing communications.

### 3.1 Entitlement Enforcement

Phase 3 hardens entitlement enforcement with three modes:

**Hard cap:** Reject the action when `current_usage >= limit_value`. Returns HTTP 402 with `X-Entitlement-Exceeded` header.

**Soft cap:** Allow the action but flag the overage. The billing engine rates overage units at the overage price tier on the next invoice.

**Metered:** No upfront limit; all usage is rated at end of period. Used for pure usage-based features.

Enforcement uses Redis as the primary store for low-latency checks. Redis is populated from PostgreSQL at subscription creation and invalidated on plan changes, cancellations, and entitlement grants.

The `CheckEntitlement` gRPC endpoint returns:
- `ALLOWED` — within limit
- `ALLOWED_WITH_OVERAGE` — soft cap exceeded; overage will be billed
- `DENIED` — hard cap reached

### 3.2 Tax Integration (Avalara AvaTax)

The Tax Service wraps the Avalara AvaTax REST API v2. It is called during invoice finalization.

**Integration flow:**

1. Collect `ship_to` address (customer billing address), `ship_from` address (platform nexus address), and line items.
2. Call `POST /api/v2/transactions/create` with `type: SalesInvoice`.
3. Avalara returns tax amounts per line item, broken down by jurisdiction.
4. Persist the Avalara `transactionCode` on the invoice for audit/reconciliation.
5. On invoice void, call `POST /api/v2/transactions/{code}/void`.

**Fallback behavior:** If Avalara returns a 5xx or times out (threshold: 3 seconds), the billing engine applies the cached tax rate for the customer's jurisdiction (stored in `tax_rate_cache` with 24-hour TTL). If no cached rate exists, tax is recorded as $0 and flagged for manual review in `tax_review_queue`.

### 3.3 Credit Notes

Credit notes are formal reductions to an account's balance, issued when a customer is due a refund or adjustment.

**Types:**
- `full_refund` — credits 100% of the original invoice total
- `partial_refund` — credits a specified amount
- `goodwill` — manually issued adjustment not tied to a specific invoice

Credit notes reduce the account's outstanding balance. When a new invoice is generated, the `CreditApplicator` checks for open credit notes and applies them up to the invoice total, creating a `credit_applied` line item.

### 3.4 Coupon and Discount Management

Coupons are configured with the following properties:

- **Type:** `percentage` (e.g., 20% off) or `fixed_amount` (e.g., $50 off)
- **Duration:** `once`, `repeating` (for N billing cycles), or `forever`
- **Max redemptions:** optional cap on total uses
- **Stackability:** whether the coupon can be combined with other active coupons
- **Plan restriction:** optionally limit to specific plan IDs

The `DiscountEngine` validates coupon eligibility (expiry, redemption limits, plan restrictions) and calculates the discount amount. Discounts are applied after usage rating and proration but before tax calculation and credit application.

### 3.5 Revenue Recognition (ASC 606)

The Revenue Recognition module tracks deferred revenue to comply with ASC 606 (IFRS 15). Prepaid annual subscriptions are deferred and recognized monthly.

**Recognition schedule:**

For an annual subscription billed $1,200 upfront:
- Month 1–12: recognize $100/month
- Deferred balance decreases by $100/month
- On cancellation: recognize remaining deferred balance as of cancellation date; refund unearned portion per refund policy

```sql
CREATE TABLE revenue_recognition_entries (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id          UUID NOT NULL REFERENCES invoices(id),
    subscription_id     UUID NOT NULL REFERENCES subscriptions(id),
    recognition_date    DATE NOT NULL,
    recognized_amount   BIGINT NOT NULL,
    deferred_amount     BIGINT NOT NULL,
    entry_type          TEXT NOT NULL, -- initial_deferral | monthly_recognition | cancellation_adjustment
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 3.6 Notification Service

The Notification Service delivers billing events to customers via email, SMS, and webhooks.

**Supported notification types:**

| Event | Channel | Trigger |
|-------|---------|---------|
| Invoice finalized | Email + Webhook | Invoice transitions to `open` |
| Payment succeeded | Email + Webhook | Charge succeeds |
| Payment failed | Email + Webhook | Charge fails; includes retry schedule |
| Dunning reminder | Email + SMS | Day 3 and Day 5 of dunning cycle |
| Subscription canceled | Email + Webhook | Cancellation confirmed |
| Trial ending soon | Email | 3 days before trial_end |
| Card expiring soon | Email | 30 days before card expiry |
| Entitlement limit approaching | Email + Webhook | Usage at 80% and 95% of limit |
| Credit note issued | Email + Webhook | Credit note created |

Webhooks are delivered with HMAC-SHA256 signatures. Retry logic: 5 attempts with exponential backoff (1s, 5s, 25s, 125s, 625s). Failed webhook deliveries are stored in `webhook_delivery_log` for manual retry.

### Phase 3 Deliverables

- Hard/soft cap entitlement enforcement with Redis-backed low-latency checks
- Avalara AvaTax integration with jurisdiction lookup and fallback caching
- Credit note lifecycle (issuance, application, voiding)
- Full coupon engine with stackability rules and redemption tracking
- ASC 606 revenue recognition with deferred revenue schedule generation
- Email (SendGrid), SMS (Twilio), and webhook notification delivery
- End-to-end tests covering: trial → conversion → upgrade → cancellation lifecycle
- End-to-end tests covering: coupon application, proration, tax, and credit note flows

---

## Phase 4: Production Hardening (Weeks 23–30)

### Objectives

Prepare the system for production traffic, regulatory audit, and long-term operational stability.

### 4.1 PCI DSS Level 1 Compliance

- **Scope reduction:** All cardholder data is handled exclusively by the payment gateway (Stripe/Braintree); the platform stores only gateway tokens. Scope is limited to the tokenization flow and network segments that touch gateway webhooks.
- **Network segmentation:** Payment service pods run in a dedicated namespace with NetworkPolicy restricting ingress to the API gateway and egress to gateway endpoints only.
- **Audit logging:** All access to payment method records is logged to an append-only audit log (PostgreSQL table with RLS enforcing write-only for service accounts).
- **Encryption:** All data encrypted at rest (AWS KMS-managed keys) and in transit (TLS 1.2+ enforced at Istio ingress).
- **Penetration testing:** External PCI-qualified security assessor (QSA) performs network and application penetration test.
- **SAQ-D submission:** Complete Self-Assessment Questionnaire D with QSA attestation.

### 4.2 SOC 2 Type II Evidence Collection

Evidence collection covers the Trust Services Criteria: Security, Availability, Processing Integrity, Confidentiality, and Privacy.

- **Access control:** All production access via Vault-issued short-lived credentials; RBAC enforced on Kubernetes namespaces.
- **Change management:** All deployments via ArgoCD with PR-based approval gates; deployment history retained in Git.
- **Incident response:** PagerDuty integration with documented escalation paths; incident post-mortems stored in Confluence.
- **Monitoring:** Prometheus alert rules for SLO breaches exported to SOC 2 evidence bucket monthly.
- **Vulnerability management:** Snyk scans run on every merge to main; critical CVEs block deployment.

### 4.3 MRR/ARR Analytics and Revenue Dashboards

Analytics are derived from the `revenue_recognition_entries` and `subscriptions` tables.

**Key metrics computed:**

- **MRR:** Sum of monthly normalized revenue for all `active` and `past_due` subscriptions
- **ARR:** MRR × 12
- **Net Revenue Retention (NRR):** (Starting MRR + Expansion − Contraction − Churn) / Starting MRR × 100
- **Churn Rate:** Subscriptions canceled in period / subscriptions at start of period
- **Average Revenue Per User (ARPU):** MRR / active account count
- **Plan distribution:** MRR breakdown by plan

Dashboards are built in Grafana using PostgreSQL data source queries. A dedicated `analytics_replica` read replica prevents dashboard queries from impacting billing transaction performance.

### 4.4 Admin Console

The Admin Console is a React (TypeScript) single-page application backed by an internal admin API. It provides:

- **Account management:** View account details, billing history, active subscriptions, payment methods, credit balance
- **Subscription management:** Manually advance billing cycle, override next billing date, apply plan changes with proration preview
- **Invoice management:** View, void, and re-finalize invoices; download PDF; trigger manual payment retry
- **Dunning management:** View current dunning state per subscription, override retry schedule, mark as uncollectible
- **Coupon management:** Create, deactivate, and report on coupons; view redemption history
- **Entitlement management:** View and override entitlement limits per account
- **Audit log viewer:** Search and export audit logs by account, action type, and date range

Admin API authentication uses internal OAuth 2.0 with MFA-enforced identity provider. All admin actions are logged to `admin_audit_log`.

### 4.5 Observability

**Distributed Tracing (Jaeger):**

Every request carries an OpenTelemetry `traceparent` header. Spans are created for each service boundary, database query, Kafka produce/consume, and external API call (Avalara, Stripe). Traces are sampled at 100% for billing-critical paths (invoice generation, payment collection) and 10% for read-heavy paths.

**Metrics (Prometheus):**

Key metrics instrumented:

| Metric | Type | Alerting Threshold |
|--------|------|--------------------|
| `billing_invoice_generation_duration_seconds` | Histogram | p99 > 10s → page |
| `billing_payment_attempt_total` | Counter (by status) | failure rate > 5% → warn |
| `usage_ingestion_kafka_lag_seconds` | Gauge | > 300s → page |
| `entitlement_check_duration_seconds` | Histogram | p99 > 10ms → warn |
| `dunning_active_subscriptions` | Gauge | trend alert |
| `revenue_mrr_dollars` | Gauge | > 10% drop week-over-week → alert |

**Grafana Dashboards:**

- Billing Pipeline Health: invoice generation rate, payment success rate, dunning funnel
- Usage Ingestion: Kafka consumer lag, dedup rate, aggregation throughput
- Revenue Overview: MRR/ARR, churn, expansion/contraction waterfall
- Infrastructure: pod CPU/memory, PostgreSQL connection pool, Redis hit rate

### 4.6 Load Testing

Load tests are conducted using k6 against a production-replica staging environment.

**Scenarios:**

| Scenario | Target RPS / Throughput | Success Criteria |
|----------|------------------------|-----------------|
| Usage event ingestion | 50,000 events/sec | p99 < 100ms, 0% data loss |
| Invoice generation burst | 10,000 invoices in 1 hour | All invoices finalized within SLA |
| Entitlement check | 10,000 req/sec | p99 < 5ms |
| API gateway (mixed) | 5,000 req/sec | p99 < 200ms, error rate < 0.1% |
| Dunning scheduler | 5,000 concurrent subscriptions | All attempts processed within window |

### 4.7 Disaster Recovery

**RTO target:** 30 minutes | **RPO target:** 5 minutes

- PostgreSQL is replicated synchronously to a standby in a secondary AZ; async replication to a tertiary region with 5-minute lag.
- Kafka is configured with replication factor 3; minimum in-sync replicas = 2.
- Redis uses Redis Sentinel for automatic failover (< 30 seconds).
- DR drill is conducted monthly: primary region is intentionally isolated; traffic is rerouted to secondary region; recovery time and data loss are measured and documented.
- Runbooks for all failure scenarios are maintained in the Reconciliation and Recovery Playbook.

### Phase 4 Deliverables

- PCI DSS Level 1 SAQ-D completed with QSA attestation
- SOC 2 Type II audit evidence package prepared
- MRR/ARR Grafana dashboards operational
- Admin Console deployed with full billing management capabilities
- Jaeger tracing with 100% sampling on billing-critical paths
- Prometheus metrics with alerting rules for all key SLOs
- Load test results documented: system validated at 10x expected peak traffic
- DR drill completed: RTO 28 minutes, RPO 4 minutes measured and documented
- Complete operational runbooks published in reconciliation-and-recovery-playbook.md
