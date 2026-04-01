# Data Flow Diagrams — Subscription Billing and Entitlements Platform

## Overview

This document presents three data flow diagrams (DFDs) for the most data-intensive pipelines in the billing platform. Each diagram shows the sources, processing stages, storage, and outputs using Mermaid `flowchart TD` notation. Narrative explanations accompany each diagram to clarify data transformations and decision points.

---

## DFD 1: Usage Ingestion and Rating Pipeline

This pipeline handles the path from a raw customer-emitted usage event to a rated billing line item ready for invoice assembly. It is the highest-throughput data path in the system, designed to handle millions of events per day.

```mermaid
flowchart TD
    subgraph Sources["Event Sources"]
        SDK[Client SDK\nclient-side event batching]
        WHK[Webhook Relay\nthird-party system events]
        API[Direct API Call\nserver-side event push]
    end

    subgraph Ingestion["Ingestion Layer — Usage Metering Service"]
        RECV[HTTP Receiver\nPOST /usage/events]
        AUTH_CHECK{JWT Valid?\nTenant Quota OK?}
        SCHEMA_VAL{Schema Valid?\nevent_id, subscription_id,\nmeter_key, quantity, occurred_at}
        DEDUP_CHECK{event_id in\nDedup Set?\nRedis SET with 24h TTL}
        DEDUP_STORE[Mark event_id\nin Redis Dedup Set]
    end

    subgraph Processing["Processing Layer"]
        ENRICH[Enrich Event\nadd ingested_at, tenant_id,\nlookup subscription billing period]
        SUB_VALID{Subscription\nActive + Period Open?}
        RATE_LIMIT_METER{Per-Subscription\nUsage within\nHard Cap?}
        COUNTER_INC[Increment Redis Counter\nusage_counter:{sub_id}:{period}:{meter_key}\nATOMIC INCR]
        PERSIST_RAW[Persist to\nusage_records table\nPostgreSQL async batch insert]
    end

    subgraph Aggregation["Aggregation Layer"]
        PERIOD_CLOSE_TRIGGER[Period Close Trigger\nbilling.cycle.due event from Kafka]
        FLUSH_COUNTERS[Flush Redis Counters\nto usage_aggregates table]
        RECONCILE[Reconcile: compare\nRedis counter vs\nsum of usage_records\n± tolerance check]
        AGGS_FINAL[Write usage_aggregates\n{subscription_id, meter_key,\nperiod, total_quantity, status=finalized}]
        CLOSE_PERIOD[Mark billing_period\nstatus = closed]
    end

    subgraph Rating["Rating Layer — Billing Engine"]
        FETCH_PRICE[Fetch Pricing Model\nfor meter_key from PlanVersion]
        APPLY_MODEL{Pricing Model Type}
        RATE_PER_UNIT[Per-Unit Rating\namount = quantity × unit_price]
        RATE_TIERED[Tiered Rating\namount = Σ tier_qty × tier_price]
        RATE_VOLUME[Volume Rating\namount = total_qty × price_of_bucket]
        RATE_STAIRSTEP[Stairstep Rating\nflat_rate = price of bucket\ncontaining total_qty]
        RATED_LINE_ITEM[Produce InvoiceLineItem\n{description, quantity,\nunit_amount, total_amount,\nsource=usage_aggregate_id}]
    end

    subgraph Storage["Data Stores"]
        REDIS_STORE[(Redis Cluster\nusage counters,\ndedup set,\nhot aggregates)]
        PG_USAGE[(PostgreSQL\nusage_records,\nusage_aggregates,\nbilling_periods)]
        KAFKA_BUS[(Kafka\nusage.events topic\nusage.period.closed topic)]
    end

    subgraph Output["Output"]
        INVOICE_ASSEMBLY[Invoice Assembly\nBilling Engine]
    end

    SDK --> RECV
    WHK --> RECV
    API --> RECV

    RECV --> AUTH_CHECK
    AUTH_CHECK -- Invalid --> REJECT_401[Return 401 / 429]
    AUTH_CHECK -- Valid --> SCHEMA_VAL
    SCHEMA_VAL -- Invalid --> REJECT_422[Return 422 with\nvalidation errors]
    SCHEMA_VAL -- Valid --> DEDUP_CHECK
    DEDUP_CHECK -- Duplicate --> ACCEPT_DUP[Return 200 OK\ncached response\nno processing]
    DEDUP_CHECK -- New event --> DEDUP_STORE

    DEDUP_STORE --> ENRICH
    ENRICH --> SUB_VALID
    SUB_VALID -- Inactive or\nPeriod Closed --> REJECT_PERIOD[Return 422\nperiod_closed error]
    SUB_VALID -- Active --> RATE_LIMIT_METER
    RATE_LIMIT_METER -- Exceeds Hard Cap --> KAFKA_BUS
    RATE_LIMIT_METER -- Within Limit --> COUNTER_INC

    COUNTER_INC --> REDIS_STORE
    COUNTER_INC --> PERSIST_RAW
    PERSIST_RAW --> PG_USAGE

    RATE_LIMIT_METER -- Cap Exceeded --> KAFKA_BUS
    KAFKA_BUS --> PERIOD_CLOSE_TRIGGER

    PERIOD_CLOSE_TRIGGER --> FLUSH_COUNTERS
    FLUSH_COUNTERS --> REDIS_STORE
    FLUSH_COUNTERS --> RECONCILE
    RECONCILE --> AGGS_FINAL
    AGGS_FINAL --> PG_USAGE
    AGGS_FINAL --> CLOSE_PERIOD
    CLOSE_PERIOD --> PG_USAGE
    CLOSE_PERIOD --> KAFKA_BUS

    KAFKA_BUS --> FETCH_PRICE
    FETCH_PRICE --> APPLY_MODEL
    APPLY_MODEL -- per_unit --> RATE_PER_UNIT --> RATED_LINE_ITEM
    APPLY_MODEL -- tiered --> RATE_TIERED --> RATED_LINE_ITEM
    APPLY_MODEL -- volume --> RATE_VOLUME --> RATED_LINE_ITEM
    APPLY_MODEL -- stairstep --> RATE_STAIRSTEP --> RATED_LINE_ITEM

    RATED_LINE_ITEM --> INVOICE_ASSEMBLY
```

### Key Processing Notes

**Deduplication:** Every usage event carries a customer-supplied `event_id` (UUID v4). On ingestion, the service performs a Redis `SETNX event_id 1 EX 86400` operation. If the key exists, the event is silently accepted (HTTP 200) but not processed further. After 24 hours, long-term deduplication is backed by a PostgreSQL unique index on `usage_records(event_id)` to cover replay scenarios.

**Atomic Counters:** The Redis counter increment is a single `HINCRBY` on a hash key `usage_counter:{subscription_id}:{period}` in microseconds, making the hot path lock-free. This supports burst ingestion up to 50,000 events/second per service instance.

**Reconciliation:** When flushing counters at period close, the aggregation layer compares the Redis-accumulated total against the `SUM(quantity)` from `usage_records`. A discrepancy above 0.01% triggers an alert and a manual reconciliation job. Discrepancies can occur due to Redis eviction under memory pressure (mitigated by setting `maxmemory-policy allkeys-lfu`).

**Rating Model Support:** The `UsageRatingService` applies the pricing model defined on the `Price` record linked to the meter. Tiered and volume models require an ordered list of tier boundaries; the service validates these at plan publication time.

---

## DFD 2: Invoice Generation Pipeline

This pipeline transforms a closed billing period into a finalized, deliverable invoice. It combines fixed subscription charges, rated usage, proration adjustments, discount applications, and tax calculations into a single authoritative document.

```mermaid
flowchart TD
    subgraph Triggers["Pipeline Triggers"]
        CYCLE_END[billing.cycle.due\nKafka event]
        MANUAL_TRIG[Manual Invoice\nAdmin API trigger]
    end

    subgraph Retrieval["Data Retrieval Phase — Billing Engine"]
        FETCH_SUB[Fetch Subscription\n+ SubscriptionLineItems\n+ PlanVersion]
        FETCH_USAGE[Fetch usage_aggregates\nfor billing period\n(status=finalized)]
        FETCH_CREDITS[Fetch Account Credits\n(unexpired, currency-matched)]
        FETCH_COUPONS[Fetch Applied Coupons\n(not yet redeemed, not expired)]
        FETCH_PRORATION[Fetch Proration Records\n(mid-cycle changes in period)]
    end

    subgraph Calculation["Calculation Phase"]
        CALC_FIXED[Calculate Fixed Charges\nbase_price × quantity\nper SubscriptionLineItem]
        CALC_USAGE[Rate Metered Usage\nUsageRatingService\n→ InvoiceLineItems]
        CALC_PRORATION[Apply Proration\nProrationCalculator\ncredits + new charges]
        SUBTOTAL[Compute Subtotal\nΣ(fixed + usage + proration)]
        APPLY_COUPONS[Apply Coupons\npercentage or fixed amount\nrespect coupon currency + min_amount]
        APPLY_CREDITS[Apply Account Credits\nreduce amount_due\nmark credits as consumed]
        POST_DISCOUNT[Post-Discount Total\nsubtotal − coupons − credits]
    end

    subgraph TaxCalc["Tax Calculation Phase — Tax Service"]
        BUILD_TAX_REQ[Build Tax Request\n{line_items[], customer_address,\nexemptions[], product_codes[]}]
        CHECK_EXEMPT{Account\nTax Exempt?}
        APPLY_ZERO[Apply zero-rate tax\nrecord exemption reference]
        CALL_AVALARA[Call Avalara AvaTax API\nor use cached rates\nper jurisdiction+product_code]
        TAX_BREAKDOWN[TaxBreakdown\n{per_line_item: jurisdiction,\nrate, tax_type, amount}]
    end

    subgraph Assembly["Invoice Assembly Phase"]
        CREATE_DRAFT[Create Invoice Draft\n{status=draft, account_id,\nsubscription_id, billing_period,\nsubtotal, tax_total, total}]
        INSERT_LINES[Insert InvoiceLineItems\n(fixed, usage, proration, discount)]
        INSERT_TAX[Insert TaxRate rows\nper line item]
        VALIDATE_TOTALS{Validate: subtotal +\ntax_total − discounts\n= total ± $0.01?}
        VALIDATION_FAIL[Alert + hold invoice\nfor manual review]
        ASSIGN_NUMBER[Assign Invoice Number\nSELECT NEXTVAL(invoice_number_seq)\ntenant-scoped, gap-free]
        FINALIZE[UPDATE invoice\nSET status=finalized,\nfinalized_at=now()]
    end

    subgraph Delivery["Delivery Phase"]
        GEN_PDF[Generate PDF\nHTMLToPDF from Jinja2 template\n{invoice_number, line_items,\ntax breakdown, payment_terms}]
        UPLOAD_S3[Upload to S3\ninvoices/{tenant_id}/{year}/{month}/{invoice_id}.pdf]
        PUBLISH_FINALIZED[Publish invoice.finalized\nKafka event]
        NOTIFY_PAYMENT[Payment Service\nconsumes invoice.finalized]
        NOTIFY_CUSTOMER[Notification Service\nsends invoice email\n+ PDF link]
    end

    subgraph DataStores["Data Stores"]
        PG_SUB[(PostgreSQL\nsubscriptions\nsubscription_line_items\nplan_versions, prices)]
        PG_USAGE[(PostgreSQL\nusage_aggregates)]
        PG_BILLING[(PostgreSQL\ninvoices\ninvoice_line_items\ntax_rates\ndiscounts)]
        REDIS_TAX[(Redis\ntax rate cache\njurisdiction+product_code)]
        S3_STORE[(S3\nPDF invoice storage)]
    end

    CYCLE_END --> FETCH_SUB
    MANUAL_TRIG --> FETCH_SUB

    FETCH_SUB --> FETCH_USAGE
    FETCH_SUB --> FETCH_CREDITS
    FETCH_SUB --> FETCH_COUPONS
    FETCH_SUB --> FETCH_PRORATION

    FETCH_SUB --> PG_SUB
    PG_SUB --> FETCH_SUB
    FETCH_USAGE --> PG_USAGE
    PG_USAGE --> FETCH_USAGE

    FETCH_SUB --> CALC_FIXED
    FETCH_USAGE --> CALC_USAGE
    FETCH_PRORATION --> CALC_PRORATION

    CALC_FIXED --> SUBTOTAL
    CALC_USAGE --> SUBTOTAL
    CALC_PRORATION --> SUBTOTAL

    SUBTOTAL --> APPLY_COUPONS
    FETCH_COUPONS --> APPLY_COUPONS
    APPLY_COUPONS --> APPLY_CREDITS
    FETCH_CREDITS --> APPLY_CREDITS
    APPLY_CREDITS --> POST_DISCOUNT

    POST_DISCOUNT --> BUILD_TAX_REQ
    BUILD_TAX_REQ --> CHECK_EXEMPT
    CHECK_EXEMPT -- Exempt --> APPLY_ZERO
    CHECK_EXEMPT -- Taxable --> CALL_AVALARA
    CALL_AVALARA --> REDIS_TAX
    REDIS_TAX --> CALL_AVALARA
    CALL_AVALARA --> TAX_BREAKDOWN
    APPLY_ZERO --> TAX_BREAKDOWN

    TAX_BREAKDOWN --> CREATE_DRAFT
    POST_DISCOUNT --> CREATE_DRAFT

    CREATE_DRAFT --> INSERT_LINES
    INSERT_LINES --> INSERT_TAX
    INSERT_TAX --> VALIDATE_TOTALS

    CREATE_DRAFT --> PG_BILLING
    INSERT_LINES --> PG_BILLING
    INSERT_TAX --> PG_BILLING

    VALIDATE_TOTALS -- Invalid --> VALIDATION_FAIL
    VALIDATE_TOTALS -- Valid --> ASSIGN_NUMBER
    ASSIGN_NUMBER --> FINALIZE
    FINALIZE --> PG_BILLING

    FINALIZE --> GEN_PDF
    GEN_PDF --> UPLOAD_S3
    UPLOAD_S3 --> S3_STORE
    UPLOAD_S3 --> PUBLISH_FINALIZED
    PUBLISH_FINALIZED --> NOTIFY_PAYMENT
    PUBLISH_FINALIZED --> NOTIFY_CUSTOMER
```

### Key Processing Notes

**Invoice Number Assignment:** Invoice numbers are assigned using a PostgreSQL sequence scoped to each tenant (`invoice_number_seq_{tenant_id}`). The `SELECT NEXTVAL` call occurs inside the same transaction as the `FINALIZE` update, guaranteeing gap-free, sequential numbering. Numbers take the format `INV-{YYYY}-{tenant_prefix}-{sequence}`.

**Total Validation:** Before finalizing, the Billing Engine computes the expected total independently from the stored line items and compares it to the sum stored in the draft invoice. A tolerance of ±$0.01 accounts for rounding differences in multi-currency scenarios. Mismatches above tolerance hold the invoice in a `review_required` status and alert the on-call engineer.

**Credit Application Order:** Coupons are applied first (as they may have minimum order amounts or product restrictions). Account credits are applied last against the remaining balance. Both reductions are recorded as distinct `InvoiceLineItem` rows with negative amounts for full auditability.

---

## DFD 3: Payment and Dunning Flow

This pipeline handles everything from a finalized invoice through payment collection, outcome processing, dunning cycle management, and retry scheduling.

```mermaid
flowchart TD
    subgraph Input["Input"]
        INV_FINALIZED[invoice.finalized\nKafka event\n{invoice_id, account_id,\namount_due, currency, due_date}]
    end

    subgraph PaymentLookup["Payment Method Resolution — Payment Service"]
        FETCH_PM[Fetch Default Payment Method\nSELECT WHERE account_id=?\nAND is_default=true\nAND NOT expired]
        PM_EXISTS{Payment Method\nFound?}
        NO_PM[Mark invoice status='uncollectable'\nPublish payment.failed\n{reason='no_payment_method'}]
        EXPIRED_CHECK{Payment Method\nExpired?}
        MARK_EXPIRED[Notify customer of\nexpired card\nPublish payment.failed\n{reason='card_expired'}]
    end

    subgraph GatewayCall["Payment Gateway Call — Stripe"]
        BUILD_INTENT[Build PaymentIntent\n{amount_cents, currency,\ncustomer_id, payment_method_id,\nidempotency_key=invoice_id+attempt_count}]
        CALL_STRIPE[POST /v1/payment_intents\nor charge stored PaymentMethod]
        STRIPE_RESP{Stripe Response\nStatus?}
        STRIPE_3DS[Requires 3DS Auth\nSend auth email to customer\nSet status=awaiting_action]
        STRIPE_SUCCESS[status=succeeded\ncharge_id, amount_received]
        STRIPE_FAIL[status=failed\ndecline_code, error_message]
    end

    subgraph ResultProcessing["Result Processing"]
        RECORD_SUCCESS[INSERT payment\n{status=succeeded, gateway_ref,\namount, invoice_id}]
        UPDATE_INV_PAID[UPDATE invoice\nSET status=paid,\namount_paid, paid_at=now()]
        RECORD_FAIL[INSERT payment\n{status=failed, failure_reason,\nattempt_count}]
        UPDATE_INV_PASTDUE[UPDATE invoice\nSET status=past_due]
        PUB_SUCCESS[Publish payment.succeeded\n{invoice_id, subscription_id,\namount_paid}]
        PUB_FAIL[Publish payment.failed\n{invoice_id, subscription_id,\nfailure_reason, attempt_count}]
    end

    subgraph DunningDecision["Dunning Decision — Dunning Service"]
        CONSUME_FAIL[Consume payment.failed]
        CHECK_CYCLE{Active Dunning\nCycle Exists?}
        CREATE_CYCLE[Create dunning_cycle\n{attempt_count=1,\nstatus=active,\nnext_retry_at=now()+1d}]
        UPDATE_CYCLE[Increment attempt_count\nUpdate next_retry_at]
        CHECK_SCHEDULE{Which Retry\nSchedule Step?}
        SCHED_D1[Schedule Day 1 Retry\nnext_retry_at = started_at + 1d]
        SCHED_D3[Schedule Day 3 Retry\nnext_retry_at = started_at + 3d]
        SCHED_D7[Schedule Day 7 Retry\nnext_retry_at = started_at + 7d\nStart grace period]
        SCHED_D14[Schedule Day 14 Retry\nnext_retry_at = started_at + 14d\nFinal attempt]
        MAX_ATTEMPTS{All 4 retries\nexhausted?}
    end

    subgraph GracePeriodMgmt["Grace Period Management"]
        START_GRACE[UPDATE dunning_cycle\nSET status=grace_period\ngrace_period_end=now()+7d]
        RESTRICT_ENT[Entitlement Service:\nRestrict premium features\nreduce to grace-tier access]
        NOTIFY_GRACE[Notify customer:\naccount restricted,\nX days to resolve payment]
    end

    subgraph Resolution["Resolution"]
        CANCEL_SUB[Cancel Subscription\nstatus=cancelled\nreason=dunning_exhausted]
        REVOKE_ENT[Revoke all entitlements\nClear Redis entitlement hash]
        PUB_CANCELLED[Publish dunning.completed.cancelled\n+ subscription.cancelled]
        NOTIFY_CANCEL[Notify customer:\nsubscription cancelled\nreactivation link included]
        RESOLVE_RECOVERED[UPDATE dunning_cycle\nSET status=resolved_recovered]
        RESTORE_SUB[Restore subscription\nstatus=active]
        RESTORE_ENT[Remove entitlement restrictions\nRestore full access]
        PUB_RECOVERED[Publish dunning.completed.recovered]
        NOTIFY_RECOVERED[Notify customer:\npayment received,\nfull access restored]
    end

    subgraph DataStores["Data Stores"]
        PG_PM[(PostgreSQL\npayment_methods)]
        PG_PAY[(PostgreSQL\npayments\ninvoices)]
        PG_DUN[(PostgreSQL\ndunning_cycles\ndunning_attempts)]
        KAFKA_BUS[(Kafka\npayment.events\ndunning.events)]
    end

    INV_FINALIZED --> FETCH_PM
    FETCH_PM --> PG_PM
    PG_PM --> PM_EXISTS
    PM_EXISTS -- Not Found --> NO_PM
    PM_EXISTS -- Found --> EXPIRED_CHECK
    EXPIRED_CHECK -- Expired --> MARK_EXPIRED
    EXPIRED_CHECK -- Valid --> BUILD_INTENT

    BUILD_INTENT --> CALL_STRIPE
    CALL_STRIPE --> STRIPE_RESP
    STRIPE_RESP -- 3DS Required --> STRIPE_3DS
    STRIPE_RESP -- Succeeded --> STRIPE_SUCCESS
    STRIPE_RESP -- Failed --> STRIPE_FAIL

    STRIPE_SUCCESS --> RECORD_SUCCESS
    STRIPE_SUCCESS --> UPDATE_INV_PAID
    RECORD_SUCCESS --> PG_PAY
    UPDATE_INV_PAID --> PG_PAY
    UPDATE_INV_PAID --> PUB_SUCCESS
    PUB_SUCCESS --> KAFKA_BUS

    STRIPE_FAIL --> RECORD_FAIL
    STRIPE_FAIL --> UPDATE_INV_PASTDUE
    RECORD_FAIL --> PG_PAY
    UPDATE_INV_PASTDUE --> PG_PAY
    UPDATE_INV_PASTDUE --> PUB_FAIL
    NO_PM --> PUB_FAIL
    MARK_EXPIRED --> PUB_FAIL
    PUB_FAIL --> KAFKA_BUS

    KAFKA_BUS --> CONSUME_FAIL
    CONSUME_FAIL --> CHECK_CYCLE
    CHECK_CYCLE -- No cycle --> CREATE_CYCLE
    CHECK_CYCLE -- Cycle exists --> UPDATE_CYCLE
    CREATE_CYCLE --> PG_DUN
    UPDATE_CYCLE --> PG_DUN

    CREATE_CYCLE --> CHECK_SCHEDULE
    UPDATE_CYCLE --> CHECK_SCHEDULE

    CHECK_SCHEDULE -- attempt=1 --> SCHED_D1
    CHECK_SCHEDULE -- attempt=2 --> SCHED_D3
    CHECK_SCHEDULE -- attempt=3 --> SCHED_D7
    CHECK_SCHEDULE -- attempt=4 --> SCHED_D14

    SCHED_D7 --> START_GRACE
    START_GRACE --> PG_DUN
    START_GRACE --> RESTRICT_ENT
    START_GRACE --> NOTIFY_GRACE

    SCHED_D14 --> MAX_ATTEMPTS
    MAX_ATTEMPTS -- Yes, exhausted --> CANCEL_SUB
    MAX_ATTEMPTS -- Retry --> CALL_STRIPE

    CANCEL_SUB --> REVOKE_ENT
    REVOKE_ENT --> PUB_CANCELLED
    PUB_CANCELLED --> KAFKA_BUS
    PUB_CANCELLED --> NOTIFY_CANCEL

    KAFKA_BUS --> RESOLVE_RECOVERED
    RESOLVE_RECOVERED --> RESTORE_SUB
    RESTORE_SUB --> RESTORE_ENT
    RESTORE_ENT --> PUB_RECOVERED
    PUB_RECOVERED --> NOTIFY_RECOVERED
```

### Key Processing Notes

**Idempotency on Retry:** Each payment attempt builds a unique `idempotency_key` from `{invoice_id}:{attempt_count}`. This ensures that if the Payment Service crashes after calling Stripe but before recording the result, the retry will get the same Stripe response rather than creating a duplicate charge.

**3DS Authentication Handling:** When Stripe returns `requires_action`, the platform sends an authentication email to the customer with a Stripe-hosted payment confirmation URL. The invoice is held in `awaiting_action` status for 48 hours. If no action is taken, the invoice reverts to `past_due` and the dunning flow continues.

**Dunning Schedule Configuration:** The retry intervals (Day 1, 3, 7, 14) are tenant-configurable. Each tenant can define their own `DunningConfig` record specifying the number of retries, intervals (in hours), and grace period length. The Dunning Service reads this configuration at cycle creation time and stores the computed schedule in the `dunning_cycle` row.

**Partial Payment Recovery:** If an account owner pays part of the outstanding balance by adding an account credit (e.g., via admin override), the Dunning Service re-evaluates the `amount_due` on the next retry. If the credit covers the full remaining balance, the dunning cycle is resolved without a gateway call.
