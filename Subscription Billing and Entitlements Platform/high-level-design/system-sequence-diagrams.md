# System Sequence Diagrams — Subscription Billing and Entitlements Platform

## Overview

This document captures the detailed interaction sequences for three critical business flows: subscription creation with a trial period, the monthly billing cycle, and the failed payment dunning flow. Each diagram is expressed in Mermaid `sequenceDiagram` notation and accompanied by detailed narrative descriptions of each step.

---

## Flow 1: Subscription Creation with Trial Period

This flow covers the end-to-end process a new customer follows when subscribing to a plan that includes a trial period. It spans validation, plan resolution, trial period setup, entitlement provisioning, and customer notification.

```mermaid
sequenceDiagram
    autonumber
    actor AO as Account Owner
    participant AG as API Gateway
    participant SS as Subscription Service
    participant PS as Plan Service
    participant ENT as Entitlement Service
    participant NOTIF as Notification Service
    participant PG as PostgreSQL
    participant REDIS as Redis
    participant KAFKA as Kafka

    AO->>AG: POST /subscriptions\n{plan_id, payment_method_id, coupon_code?}
    AG->>AG: Validate JWT (RS256)\nExtract account_id, tenant_id
    AG->>AG: Check rate limit (Redis token bucket)
    AG->>SS: Forward request + X-Account-ID, X-Tenant-ID

    SS->>SS: Validate Idempotency-Key (Redis lookup)
    SS->>PG: Check existing active subscriptions\nfor account + plan
    PG-->>SS: No active subscription found

    SS->>PS: GET /plans/{plan_id}/version/active
    PS->>REDIS: Lookup plan:{plan_id}:active
    REDIS-->>PS: Cache miss
    PS->>PG: SELECT plan_version WHERE plan_id=? AND status='published'
    PG-->>PS: PlanVersion { version_id, trial_days=14, prices[], features[] }
    PS->>REDIS: SET plan:{plan_id}:active TTL=300s
    PS-->>SS: PlanVersion response

    SS->>SS: Validate plan is published\nValidate account is eligible for trial\n(no prior trial for this plan)

    SS->>PG: BEGIN TRANSACTION
    SS->>PG: INSERT subscription {\n  status='trialing',\n  trial_start=now(),\n  trial_end=now()+14d,\n  current_period_start=now()+14d,\n  current_period_end=now()+14d+1month,\n  plan_version_id, account_id\n}
    SS->>PG: INSERT subscription_line_items\n(base plan price, quantity=1)
    SS->>PG: COMMIT TRANSACTION

    SS->>KAFKA: Publish subscription.created {\n  subscription_id, account_id,\n  plan_version_id, status='trialing',\n  trial_end, entitlement_grants[]\n}

    KAFKA-->>ENT: Consume subscription.created
    ENT->>PG: SELECT features WHERE plan_version_id=?
    PG-->>ENT: Feature grants []
    ENT->>PG: INSERT entitlement_grants\n(one row per feature in plan version)
    ENT->>REDIS: HSET entitlement:{account_id}\n{feature_key: limit_value, ...}
    ENT->>KAFKA: Publish entitlement.granted {\n  account_id, grants[]\n}

    KAFKA-->>NOTIF: Consume subscription.created
    NOTIF->>NOTIF: Render "welcome_trial" email template\n{customer_name, plan_name,\n trial_end_date, features_list}
    NOTIF->>NOTIF: Send via SendGrid
    NOTIF->>PG: INSERT notification_log\n{type='email', status='delivered'}

    SS-->>AG: 201 Created {\n  subscription_id,\n  status='trialing',\n  trial_end,\n  current_period_start,\n  current_period_end,\n  entitlements[]\n}
    AG-->>AO: 201 Created (subscription details)

    Note over SS: Idempotency-Key cached in Redis\nfor 24 hours

    Note over NOTIF: Trial expiry reminder scheduled:\nD-7 and D-1 emails via Kafka delayed event
```

### Narrative

**Steps 1–3:** The account owner submits a subscription creation request. The API Gateway validates the JWT, extracts the `account_id` and `tenant_id`, and enforces rate limiting.

**Steps 4–5:** The Subscription Service checks the idempotency key to guard against duplicate submissions. It then verifies that no conflicting active subscription already exists for this account and plan combination.

**Steps 6–11:** The Subscription Service fetches the active plan version from the Plan Service. The Plan Service checks its Redis cache first; on a miss, it queries PostgreSQL and populates the cache with a 5-minute TTL.

**Steps 12–13:** The Subscription Service validates that the plan is published and that this account has not previously received a trial for this plan (preventing abuse).

**Steps 14–19:** Within a PostgreSQL transaction, the service inserts the subscription in `trialing` status, sets `trial_end` to `now() + trial_days`, and inserts the subscription line items. The transaction commits atomically.

**Steps 20–24:** A `subscription.created` event is published to Kafka. The Entitlement Service consumes it, reads the plan features, inserts `entitlement_grants`, and writes the entitlement hash to Redis for low-latency checks.

**Steps 25–28:** The Notification Service consumes the same `subscription.created` event, renders the welcome/trial email template, dispatches it via SendGrid, and logs the notification.

**Steps 29–30:** The Subscription Service returns the created subscription details (including entitlements) to the API Gateway, which forwards the 201 response to the account owner.

---

## Flow 2: Monthly Billing Cycle

This flow describes the automated monthly billing run. It starts with a scheduled trigger and proceeds through usage aggregation, invoice generation, tax calculation, finalization, payment collection, and customer notification.

```mermaid
sequenceDiagram
    autonumber
    participant SCHED as Billing Scheduler\n(Cron Job)
    participant UMS as Usage Metering Service
    participant BE as Billing Engine
    participant TAX as Tax Service
    participant SS as Subscription Service
    participant PAY as Payment Service
    participant NOTIF as Notification Service
    actor AO as Account Owner
    participant PG as PostgreSQL
    participant REDIS as Redis
    participant KAFKA as Kafka
    participant S3 as Object Storage (S3)
    participant STRIPE as Stripe

    SCHED->>KAFKA: Publish billing.cycle.due {\n  subscription_id[],\n  billing_date,\n  batch_id\n}

    KAFKA-->>UMS: Consume billing.cycle.due
    UMS->>REDIS: Read usage_counter:{sub_id}:{period}\n(real-time accumulator)
    REDIS-->>UMS: Partial counters
    UMS->>PG: SELECT usage_records WHERE\n  subscription_id=? AND\n  period=? AND status='open'
    PG-->>UMS: Raw usage records
    UMS->>UMS: Aggregate by meter_key\n(SUM / MAX / unique_count)
    UMS->>PG: INSERT usage_aggregates {\n  subscription_id, meter_key,\n  period, total_quantity,\n  status='finalized'\n}
    UMS->>PG: UPDATE billing_period\n  SET status='closed'\nWHERE subscription_id=? AND period=?
    UMS->>KAFKA: Publish usage.period.closed {\n  subscription_id,\n  aggregates[]\n}

    KAFKA-->>BE: Consume usage.period.closed
    BE->>PG: SELECT subscription + line_items\n + active plan version prices
    PG-->>BE: Subscription, SubscriptionLineItems,\nPrices, PlanVersion
    BE->>PG: SELECT usage_aggregates\n  WHERE subscription_id=? AND period=?
    PG-->>BE: UsageAggregates[]
    BE->>BE: Calculate fixed charges\n(subscription base fee × quantity)
    BE->>BE: Rate metered usage\n(UsageRatingService: apply\ntier/volume/stairstep pricing)
    BE->>BE: Calculate proration credits\n(for mid-cycle changes this period)
    BE->>BE: Apply coupons / account credits

    BE->>TAX: POST /tax/calculate {\n  line_items[],\n  customer_address,\n  tax_exemptions\n}
    TAX->>REDIS: GET tax_rate:{jurisdiction}:{code}
    REDIS-->>TAX: Cache hit (or miss → Avalara API call)
    TAX-->>BE: TaxBreakdown { tax_amounts[] }

    BE->>PG: BEGIN TRANSACTION
    BE->>PG: INSERT invoice {\n  status='draft',\n  account_id, subscription_id,\n  billing_period, subtotal, tax_total, total\n}
    BE->>PG: INSERT invoice_line_items[]\n(fixed charges + metered charges\n+ proration + discounts)
    BE->>PG: INSERT tax_rates[]\n(per line item)
    BE->>PG: COMMIT TRANSACTION
    BE->>KAFKA: Publish invoice.drafted { invoice_id }

    BE->>BE: Validate invoice totals\n(subtotal + taxes − discounts = total)
    BE->>PG: UPDATE invoice SET status='finalized',\n  finalized_at=now(),\n  invoice_number=NEXTVAL(seq)
    BE->>S3: PUT invoices/{tenant_id}/{invoice_id}.pdf\n(rendered PDF from template)
    BE->>KAFKA: Publish invoice.finalized {\n  invoice_id, account_id,\n  amount_due, currency, due_date\n}

    KAFKA-->>PAY: Consume invoice.finalized
    PAY->>PG: SELECT payment_methods\n  WHERE account_id=? AND is_default=true
    PG-->>PAY: PaymentMethod { gateway_token }
    PAY->>STRIPE: POST /v1/payment_intents {\n  amount, currency,\n  customer, payment_method,\n  idempotency_key\n}
    STRIPE-->>PAY: PaymentIntent { status='succeeded' }
    PAY->>PG: INSERT payment {\n  invoice_id, amount,\n  status='succeeded',\n  gateway_ref\n}
    PAY->>PG: UPDATE invoice SET\n  status='paid',\n  amount_paid=amount_due,\n  paid_at=now()
    PAY->>KAFKA: Publish payment.succeeded {\n  invoice_id, subscription_id,\n  amount_paid\n}

    KAFKA-->>NOTIF: Consume payment.succeeded
    NOTIF->>S3: GET invoice PDF URL (pre-signed, 7-day expiry)
    NOTIF->>NOTIF: Render "payment_receipt" email\n{invoice_number, amount, period,\n pdf_download_url}
    NOTIF->>NOTIF: Send via SendGrid
    NOTIF-->>AO: Email: Payment Receipt + Invoice PDF link
```

### Narrative

**Steps 1–2:** The Billing Scheduler publishes a `billing.cycle.due` event for all subscriptions whose billing anchor date has been reached. The batch may contain thousands of subscriptions, partitioned by `account_id` across Kafka partitions.

**Steps 3–11:** The Usage Metering Service reads real-time Redis counters and cross-checks with the raw usage records in PostgreSQL. It computes final aggregates per meter key, writes them to `usage_aggregates` with `status='finalized'`, closes the billing period, and publishes `usage.period.closed`.

**Steps 12–23:** The Billing Engine picks up the usage period closure event. It retrieves the subscription's plan prices and line items, rates the metered usage using the `UsageRatingService`, computes proration for any mid-cycle plan changes, and applies coupons and account credits.

**Steps 24–27:** Tax calculation is delegated to the Tax Service, which uses cached rates where available and calls Avalara for misses. The result is an itemized tax breakdown per line item.

**Steps 28–35:** The Billing Engine assembles the invoice within a database transaction. After commit, it validates the totals, finalizes the invoice, generates a PDF and stores it in S3, then publishes `invoice.finalized`.

**Steps 36–44:** The Payment Service charges the account's default payment method via Stripe, records the outcome, updates the invoice to `paid`, and publishes `payment.succeeded`.

**Steps 45–49:** The Notification Service generates a payment receipt email with a pre-signed link to the invoice PDF and delivers it to the account owner.

---

## Flow 3: Failed Payment Dunning Flow

This flow handles the scenario where a payment fails and the platform must apply a configurable retry schedule, manage the subscription's grace period, and eventually either recover the payment or cancel the subscription.

```mermaid
sequenceDiagram
    autonumber
    participant PAY as Payment Service
    participant DUN as Dunning Service
    participant ENT as Entitlement Service
    participant SS as Subscription Service
    participant NOTIF as Notification Service
    actor AO as Account Owner
    participant PG as PostgreSQL
    participant KAFKA as Kafka
    participant STRIPE as Stripe

    PAY->>STRIPE: POST /v1/payment_intents\n(charge attempt)
    STRIPE-->>PAY: PaymentIntent { status='requires_payment_action'\n  or decline_code='insufficient_funds' }
    PAY->>PG: INSERT payment {\n  status='failed',\n  failure_reason,\n  attempt_count=1\n}
    PAY->>PG: UPDATE invoice SET status='past_due'
    PAY->>KAFKA: Publish payment.failed {\n  invoice_id, subscription_id,\n  account_id, failure_reason,\n  attempt_count=1\n}

    KAFKA-->>DUN: Consume payment.failed
    DUN->>PG: INSERT dunning_cycle {\n  subscription_id, invoice_id,\n  status='active',\n  attempt_count=1,\n  started_at=now(),\n  next_retry_at=now()+1d\n}
    DUN->>SS: PATCH /subscriptions/{id}/status\n{ status: 'past_due' }
    SS->>PG: UPDATE subscription SET status='past_due'
    SS->>KAFKA: Publish subscription.updated\n{ status: 'past_due' }
    DUN->>KAFKA: Publish dunning.started {\n  subscription_id, account_id,\n  invoice_id, next_retry_at\n}

    KAFKA-->>NOTIF: Consume dunning.started
    NOTIF->>NOTIF: Render "payment_failed_action_required"\nemail template
    NOTIF-->>AO: Email: Payment failed — please update\nyour payment method

    Note over DUN: Day 1 — Retry attempt 2
    DUN->>KAFKA: Publish dunning.retry.scheduled\n{ attempt=2, scheduled_at=now()+1d }
    DUN->>PAY: POST /internal/charges {\n  invoice_id, subscription_id,\n  attempt_number=2\n}
    PAY->>STRIPE: POST /v1/payment_intents (retry)
    STRIPE-->>PAY: PaymentIntent { status='failed' }
    PAY->>PG: UPDATE payment attempt_count=2
    PAY->>KAFKA: Publish payment.failed { attempt_count=2 }

    KAFKA-->>DUN: Consume payment.failed (attempt 2)
    DUN->>PG: UPDATE dunning_cycle\n  SET attempt_count=2,\n  next_retry_at=now()+3d

    Note over DUN: Day 3 — Retry attempt 3
    DUN->>PAY: POST /internal/charges { attempt=3 }
    PAY->>STRIPE: POST /v1/payment_intents (retry)
    STRIPE-->>PAY: PaymentIntent { status='failed' }
    PAY->>KAFKA: Publish payment.failed { attempt_count=3 }
    DUN->>PG: UPDATE dunning_cycle\n  SET attempt_count=3,\n  next_retry_at=now()+7d

    Note over DUN: Day 7 — Grace period begins
    DUN->>PG: UPDATE dunning_cycle\n  SET status='grace_period',\n  grace_period_end=now()+7d
    DUN->>KAFKA: Publish dunning.grace_period.started {\n  subscription_id, account_id,\n  grace_period_end\n}

    KAFKA-->>ENT: Consume dunning.grace_period.started
    ENT->>PG: UPDATE entitlement_grants\n  SET restricted=true\n  (downgrade to read-only or\n   disable premium features)
    ENT->>REDIS: HSET entitlement:{account_id}\n  { restricted: true }
    ENT->>KAFKA: Publish entitlement.restricted {\n  account_id, reason='grace_period'\n}

    KAFKA-->>NOTIF: Consume dunning.grace_period.started
    NOTIF->>NOTIF: Render "grace_period_warning" email\n{grace_period_end, features_restricted}
    NOTIF-->>AO: Email: Access restricted — 7 days to\nresolve payment before cancellation

    Note over DUN: Day 7 grace — Retry attempt 4
    DUN->>PAY: POST /internal/charges { attempt=4 }
    PAY->>STRIPE: POST /v1/payment_intents (retry)
    STRIPE-->>PAY: PaymentIntent { status='succeeded' }
    PAY->>PG: INSERT payment { status='succeeded' }
    PAY->>PG: UPDATE invoice SET status='paid'
    PAY->>KAFKA: Publish payment.succeeded {\n  invoice_id, subscription_id\n}

    alt Payment Recovered
        KAFKA-->>DUN: Consume payment.succeeded
        DUN->>PG: UPDATE dunning_cycle\n  SET status='resolved_recovered',\n  resolved_at=now()
        DUN->>SS: PATCH /subscriptions/{id}/status\n{ status: 'active' }
        SS->>PG: UPDATE subscription SET status='active'
        DUN->>KAFKA: Publish dunning.completed.recovered {\n  subscription_id, account_id\n}
        KAFKA-->>ENT: Consume dunning.completed.recovered
        ENT->>PG: UPDATE entitlement_grants\n  SET restricted=false
        ENT->>REDIS: HSET entitlement:{account_id}\n  { restricted: false }
        KAFKA-->>NOTIF: Consume dunning.completed.recovered
        NOTIF-->>AO: Email: Payment successful —\nfull access restored

    else All Retries Exhausted (Day 14)
        DUN->>PG: UPDATE dunning_cycle\n  SET status='failed_cancelled'
        DUN->>SS: PATCH /subscriptions/{id}/status\n{ status: 'cancelled',\n  cancellation_reason='dunning_exhausted' }
        SS->>PG: UPDATE subscription\n  SET status='cancelled',\n  cancelled_at=now(),\n  ended_at=now()
        SS->>KAFKA: Publish subscription.cancelled {\n  reason='dunning_exhausted'\n}
        KAFKA-->>ENT: Consume subscription.cancelled
        ENT->>PG: UPDATE entitlement_grants\n  SET revoked_at=now()
        ENT->>REDIS: DEL entitlement:{account_id}
        DUN->>KAFKA: Publish dunning.completed.cancelled {\n  subscription_id, account_id,\n  reason='payment_failure'\n}
        KAFKA-->>NOTIF: Consume dunning.completed.cancelled
        NOTIF-->>AO: Email: Subscription cancelled —\nreactivation instructions included
    end
```

### Narrative

**Steps 1–5:** The Payment Service makes the initial charge attempt. Stripe declines it (insufficient funds, card expired, or authentication required). The service records the failed payment, marks the invoice as `past_due`, and publishes `payment.failed`.

**Steps 6–12:** The Dunning Service consumes the failure event and opens a dunning cycle. It sets the next retry for Day 1 and updates the subscription status to `past_due`. A `dunning.started` event is published.

**Step 13:** The Notification Service sends a "payment failed" email prompting the account owner to update their payment method.

**Steps 14–20:** Day 1 retry attempt fails. The dunning cycle records attempt 2 and advances the next retry to Day 3.

**Steps 21–25:** Day 3 retry attempt also fails. Next retry scheduled for Day 7.

**Steps 26–34:** At Day 7, the dunning service transitions the cycle to `grace_period`. The Entitlement Service receives the `dunning.grace_period.started` event and downgrades the account's entitlements to restricted mode (disabling premium features while allowing read access). A grace period warning email is sent.

**Steps 35–39:** Day 7 within the grace period — a 4th charge attempt succeeds.

**Recovery Branch (Steps 40–48):** The dunning cycle resolves as `recovered`. The subscription returns to `active`. The Entitlement Service lifts restrictions. The customer receives a payment success and access restoration email.

**Cancellation Branch (Steps 49–60):** If the Day 14 retry (final attempt) also fails, the dunning cycle marks itself as `failed_cancelled`. The Subscription Service cancels the subscription immediately. The Entitlement Service revokes all grants and removes the Redis entitlement hash. A cancellation email with reactivation instructions is sent to the account owner.
