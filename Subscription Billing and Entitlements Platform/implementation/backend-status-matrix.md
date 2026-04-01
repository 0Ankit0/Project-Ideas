# Backend Status Matrix — Subscription Billing and Entitlements Platform

## Overview

This matrix tracks the implementation status of every backend component across all services. Status is updated at the end of each sprint. Test coverage targets are enforced in CI; PRs that reduce coverage below the target for a given component are blocked from merging.

**Status Legend:**

| Symbol | Meaning |
|--------|---------|
| ✅ Complete | Feature is implemented, tested, deployed to staging, and verified by QA |
| 🔄 In Progress | Actively being implemented in the current sprint |
| 📋 Planned | Scoped and estimated; scheduled for a future sprint |
| ❌ Blocked | Work cannot proceed; blocker is documented in the Notes column |

**Test Coverage Definition:** Line coverage measured by `go test -coverprofile`. Integration test coverage is binary (present / not present) rather than line-based.

---

## Plan Catalog Service

| # | Component | Service | Status | Test Coverage | Notes |
|---|-----------|---------|--------|---------------|-------|
| 1 | Plan CRUD API | Plan Catalog Service | ✅ Complete | 91% unit, integration ✅ | `POST /v1/plans`, `GET`, `PATCH`, `DELETE` fully operational. Draft/active/archived state machine enforced. Archived plans return 410 on new subscription attempts. |
| 2 | Plan Version Management | Plan Catalog Service | ✅ Complete | 88% unit, integration ✅ | Version immutability enforced after activation. `effective_from` and `effective_until` set correctly on version transitions. Historical versions retained indefinitely for billing audit. |
| 3 | Price Configuration | Plan Catalog Service | ✅ Complete | 86% unit, integration ✅ | Flat, graduated, volume, and package pricing models supported. Tier breakpoint validation enforced (strictly ascending, last tier `up_to = null`). Multi-currency support with ISO 4217 validation. |

---

## Subscription Service

| # | Component | Service | Status | Test Coverage | Notes |
|---|-----------|---------|--------|---------------|-------|
| 4 | Subscription Creation | Subscription Service | ✅ Complete | 93% unit, integration ✅ | Supports immediate activation and trial start. Validates plan is active before creating subscription. Default billing period derived from selected price. Idempotency key required. |
| 5 | Trial Management | Subscription Service | ✅ Complete | 87% unit, integration ✅ | Trial end date stored as `trial_end`. Scheduled job transitions `trialing` → `active` at trial expiry. Trial extension API available for customer success team. Trial without payment method allowed; payment method required before trial converts. |
| 6 | Subscription State Machine | Subscription Service | ✅ Complete | 95% unit, integration ✅ | States: `trialing → active → past_due → canceled / paused`. All state transitions validated against allowed transition matrix. Invalid transitions return HTTP 409 with current state in response body. State change events published to Kafka on every transition. |
| 7 | Plan Upgrade/Downgrade | Subscription Service | ✅ Complete | 89% unit, integration ✅ | Immediate and end-of-period change modes supported. Proration adjustment records created for immediate changes. Plan version locked at change time. Downgrade to incompatible billing model blocked with validation error. |
| 8 | Pause/Resume | Subscription Service | 🔄 In Progress | 72% unit, integration ❌ | Pause API implemented; billing suspension logic complete. Resume API pending. Entitlement suspension on pause not yet wired. Integration tests not written. Target: Sprint 8. |
| 9 | Cancellation | Subscription Service | ✅ Complete | 90% unit, integration ✅ | Supports immediate and end-of-period cancellation. `cancel_at_period_end` flag sets deferred cancellation. Cancellation reason captured. Revenue recognition notified via Kafka. Entitlements revoked immediately on cancellation. |

---

## Usage Metering Service

| # | Component | Service | Status | Test Coverage | Notes |
|---|-----------|---------|--------|---------------|-------|
| 10 | Usage Event Ingestion | Usage Metering Service | ✅ Complete | 88% unit, integration ✅ | `POST /v1/usage/events` accepts single and batch payloads (up to 1,000 events per request). Events written to Kafka `usage.raw.v1`. Acknowledgment is async; HTTP 202 returned immediately. SDK clients available for Go, Python, Node.js, Ruby. |
| 11 | Usage Deduplication | Usage Metering Service | ✅ Complete | 91% unit, integration ✅ | Redis `SET NX EX` on `idempotency_key` with 90-day TTL. Dedup consumer reads from `usage.raw.v1` and forwards clean events to `usage.deduplicated.v1`. Duplicate rate metric exported to Prometheus. TTL set to cover longest billing period plus one renewal. |
| 12 | Usage Aggregation | Usage Metering Service | ✅ Complete | 85% unit, integration ✅ | Aggregates summed per `(account_id, subscription_id, feature_key, period_start, period_end)`. Upsert pattern on conflict. Aggregates exposed via `GET /v1/usage/aggregates` with period filtering. Consumer lag monitored; alert fires if lag exceeds 5 minutes. |

---

## Billing Engine

| # | Component | Service | Status | Test Coverage | Notes |
|---|-----------|---------|--------|---------------|-------|
| 13 | Invoice Draft Generation | Billing Engine | ✅ Complete | 92% unit, integration ✅ | Idempotency key format: `{subscriptionId}:{periodStart}:{periodEnd}`. Draft invoice created before any line item calculation. Distributed Redis lock prevents concurrent generation for same subscription. Scheduler CronJob runs every minute. |
| 14 | Usage Rating | Billing Engine | ✅ Complete | 94% unit, integration ✅ | All four pricing models implemented: flat, graduated, volume, package. Benchmark tests confirm p99 < 2ms for single subscription rating. Edge cases covered: zero usage, single-unit at tier boundary, quantity exactly at tier breakpoint. |
| 15 | Proration Calculation | Billing Engine | ✅ Complete | 90% unit, integration ✅ | Day-level precision for proration. Both upgrade (charge) and downgrade (credit) flows produce correct line items. Proration adjustments immutably recorded. Benchmark: p99 < 1ms for proration calculation. |
| 16 | Tax Calculation | Billing Engine (via Tax Service) | ✅ Complete | 83% unit, integration ✅ | Delegates to Tax Service which calls Avalara AvaTax. Fallback to cached jurisdiction rate on Avalara timeout (3s). Tax review queue populated when fallback used. Avalara `transactionCode` stored on invoice for reconciliation. |
| 17 | Discount/Coupon Application | Billing Engine | ✅ Complete | 88% unit, integration ✅ | Percentage and fixed-amount coupons supported. Stackability rules enforced. Duration modes: once, repeating (N cycles), forever. Redemption count incremented atomically. Expired and limit-reached coupons rejected. |
| 18 | Credit Application | Billing Engine | ✅ Complete | 86% unit, integration ✅ | Credits applied after discounts, before tax. Partial credit application supported (credit balance split across multiple invoices). Credit note application records created. Overapplication blocked with validation. |
| 19 | Invoice Finalization | Billing Engine | ✅ Complete | 91% unit, integration ✅ | Transitions invoice from `draft` to `open`. All totals recalculated and stored. `finalized_at` timestamp set. `InvoiceGenerated` Kafka event published. PDF generation and email notification triggered asynchronously post-finalization. |
| 28 | Credit Note Issuance | Billing Engine | ✅ Complete | 87% unit, integration ✅ | Full refund, partial refund, and goodwill credit types. Credit notes linked to source invoice where applicable. Account credit balance updated atomically. Credit note PDF generated and emailed to customer. Void flow supported with balance reversal. |

---

## Payment Service

| # | Component | Service | Status | Test Coverage | Notes |
|---|-----------|---------|--------|---------------|-------|
| 20 | Payment Processing (Stripe) | Payment Service | ✅ Complete | 89% unit, contract ✅ | PaymentIntent API used for SCA/3DS2 compliance. Webhook handler validates `Stripe-Signature` header. Handles `payment_intent.succeeded`, `payment_intent.payment_failed`, `charge.dispute.created` events. Pact contract tests run against Stripe sandbox. |
| 21 | Payment Processing (PayPal) | Payment Service | ✅ Complete | 84% unit, contract ✅ | PayPal Orders API v2. Billing Agreement tokens stored for recurring charges. Webhook signature validation using PayPal cert verification. Handles `PAYMENT.CAPTURE.COMPLETED`, `PAYMENT.CAPTURE.DENIED` events. |
| 22 | Payment Processing (Braintree) | Payment Service | 🔄 In Progress | 67% unit, contract ❌ | Braintree client token flow implemented. Vault storage for credit cards and PayPal accounts. Transaction submission implemented. Webhook handler in progress. Contract tests not yet written. Target completion: Sprint 9. |

---

## Dunning Service

| # | Component | Service | Status | Test Coverage | Notes |
|---|-----------|---------|--------|---------------|-------|
| 23 | Dunning Orchestration | Dunning Service | ✅ Complete | 88% unit, integration ✅ | State machine: `pending → scheduled → processing → succeeded / failed → escalated`. Configurable retry schedules stored per plan (override) or global default. All state transitions logged to `dunning_attempt_log`. Final failure transitions subscription to `past_due`. |
| 24 | Dunning Retry Scheduler | Dunning Service | ✅ Complete | 85% unit, integration ✅ | Go worker queries `dunning_attempts` where `next_attempt_at <= now()` and `status = 'scheduled'`. Distributed Redis lock per attempt prevents double-processing. Exponential backoff for transient gateway errors. Manual override endpoint for customer success team. |

---

## Entitlement Service

| # | Component | Service | Status | Test Coverage | Notes |
|---|-----------|---------|--------|---------------|-------|
| 25 | Entitlement Checking | Entitlement Service | ✅ Complete | 93% unit, integration ✅ | gRPC `CheckEntitlement` endpoint returns `ALLOWED`, `ALLOWED_WITH_OVERAGE`, or `DENIED`. Redis is primary store; PostgreSQL is source of truth. Cache miss triggers PostgreSQL read and cache warm. p99 latency < 3ms measured in load test. |
| 26 | Entitlement Granting/Revoking | Entitlement Service | ✅ Complete | 89% unit, integration ✅ | Grants triggered by subscription creation, plan upgrade, and manual admin override. Revocations triggered by cancellation, downgrade, and dunning final failure. Both PostgreSQL and Redis updated atomically within the same operation using a write-through pattern. |
| 27 | Overage Detection | Entitlement Service | ✅ Complete | 86% unit, integration ✅ | Soft-cap overages detected at `increment` time. Overage events published to Kafka `entitlement.overage.v1`. Billing Engine subscribes and queues overage charges for next invoice. 80% and 95% threshold alerts sent to Notification Service. Hard cap blocks at 100%. |

---

## Tax Service

| # | Component | Service | Status | Test Coverage | Notes |
|---|-----------|---------|--------|---------------|-------|
| 29 | Tax Integration (Avalara) | Tax Service | ✅ Complete | 83% unit, integration ✅ | AvaTax REST v2 `POST /api/v2/transactions/create` with `SalesInvoice` type. Tax amounts returned per line item, broken down by jurisdiction. `VoidTransaction` called on invoice void. Fallback cache has 24-hour TTL. Tax review queue populated when fallback is used. Monitoring alert fires if fallback rate is used > 1% of invoices. |

---

## Notification Service

| # | Component | Service | Status | Test Coverage | Notes |
|---|-----------|---------|--------|---------------|-------|
| 30 | Email Notifications | Notification Service | ✅ Complete | 85% unit, integration ✅ | SendGrid Dynamic Templates used for all email types. Templates versioned in source control. Supported events: invoice ready, payment succeeded, payment failed, dunning reminder, trial ending, card expiring, subscription canceled, credit note issued, entitlement limit approaching. Unsubscribe links compliant with CAN-SPAM. |
| 31 | Webhook Dispatch | Notification Service | ✅ Complete | 87% unit, integration ✅ | HMAC-SHA256 signature on all webhook payloads using account-specific secret. Retry schedule: 5 attempts with exponential backoff (1s, 5s, 25s, 125s, 625s). Dead-letter queue after 5 failures. Webhook delivery log queryable by account. `POST /v1/webhooks/test` endpoint for customer integration validation. |

---

## Analytics Service

| # | Component | Service | Status | Test Coverage | Notes |
|---|-----------|---------|--------|---------------|-------|
| 33 | Revenue Recognition | Analytics Service | 🔄 In Progress | 71% unit, integration ❌ | ASC 606 deferred revenue schedule generation implemented for flat-rate annual subscriptions. Monthly recognition job implemented. Cancellation adjustment calculation in progress. Integration tests pending. Usage-based and hybrid plan recognition logic not yet implemented. Target: Sprint 12. |
| 34 | MRR/ARR Dashboards | Analytics Service | 📋 Planned | — | Grafana dashboards with PostgreSQL data source. MRR, ARR, NRR, churn rate, ARPU, plan distribution metrics defined. Queries designed; dashboard JSON not yet built. Depends on Revenue Recognition completion. Dedicated analytics read replica not yet provisioned. Target: Sprint 14. |

---

## Frontend

| # | Component | Service | Status | Test Coverage | Notes |
|---|-----------|---------|--------|---------------|-------|
| 32 | Admin Console UI | Frontend | 📋 Planned | — | React (TypeScript) SPA. Wireframes approved. Component library selected (shadcn/ui). Features scoped: account management, subscription management, invoice management, dunning overrides, coupon management, entitlement overrides, audit log viewer. Backend admin API stubs available. Target: Sprint 15–18. |

---

## Summary

| Status | Count |
|--------|-------|
| ✅ Complete | 26 |
| 🔄 In Progress | 3 |
| 📋 Planned | 2 |
| ❌ Blocked | 0 |
| **Total** | **34** |

---

## Coverage Targets by Service

| Service | Target Line Coverage | Current | Status |
|---------|---------------------|---------|--------|
| Plan Catalog Service | 85% | 88% | ✅ Above target |
| Subscription Service | 85% | 89% | ✅ Above target |
| Usage Metering Service | 85% | 88% | ✅ Above target |
| Billing Engine | 90% | 90% | ✅ At target |
| Payment Service | 85% | 84% | ⚠️ 1% below (Braintree in progress) |
| Dunning Service | 85% | 87% | ✅ Above target |
| Entitlement Service | 90% | 89% | ⚠️ 1% below target |
| Tax Service | 80% | 83% | ✅ Above target |
| Notification Service | 80% | 86% | ✅ Above target |
| Analytics Service | 80% | 71% | ❌ Below target (in progress) |

---

## Blockers and Dependencies

No components are currently in ❌ Blocked status. The following cross-component dependencies are being tracked:

| Dependent Component | Depends On | Dependency Type | Expected Resolution |
|--------------------|-----------|----------------|-------------------|
| MRR/ARR Dashboards (#34) | Revenue Recognition (#33) | Functional dependency | Sprint 12 completion |
| Admin Console UI (#32) | All backend services | API completeness | Sprint 14 (all backend complete) |
| Revenue Recognition — usage-based plans (#33) | Usage Aggregation (#12) | Data model alignment | Sprint 11 |
| Braintree contract tests (#22) | Braintree sandbox credentials | Infrastructure | Sprint 9 (credentials requested) |

---

## Test Coverage Enforcement

Coverage is enforced in CI using the following gates:

```yaml
# .github/workflows/test.yml (excerpt)
- name: Check coverage thresholds
  run: |
    go test ./... -coverprofile=coverage.out
    go tool cover -func=coverage.out | grep -E "^total" | awk '{if ($3 < 85.0) exit 1}'
```

Individual service thresholds are enforced via per-package coverage checks in the `Makefile`. PRs reducing any service below its target trigger a CI failure and require explicit override from the engineering lead.

Contract tests (Pact) run in a separate CI stage that requires access to gateway sandbox credentials. They are not blocking for feature branches but are required to pass before any release branch merge.
