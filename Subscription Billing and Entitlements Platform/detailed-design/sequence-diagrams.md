# Sequence Diagrams — Subscription Billing and Entitlements Platform

## Overview

This document describes the three most critical operational flows in the platform using UML sequence diagrams. Each diagram captures participant interactions, asynchronous boundaries, error handling, and data contracts at the message level.

---

## Flow 1: Usage Metering Ingestion

### Description

Usage events are submitted by client SDKs (server-side or browser-side) and must be ingested with exactly-once semantics. The ingestion pipeline is split into a synchronous acknowledgement path (API → Redis dedup check → Kafka publish) and an asynchronous aggregation path (Kafka consumer → aggregator → PostgreSQL). This separation ensures low-latency acknowledgement to the caller while decoupling the storage write from the hot path.

### Idempotency Strategy

Each event carries a client-assigned `idempotencyKey` (format: `{subscriptionId}:{metricName}:{eventTimestamp}:{clientBatchId}`). Redis holds a 48-hour TTL bloom filter per subscription to reject duplicate keys before they reach Kafka. A secondary deduplication check is performed by the aggregator against the `usage_records` table's unique constraint on `idempotency_key`.

```mermaid
sequenceDiagram
    autonumber
    participant SDK as Client SDK
    participant GW as API Gateway
    participant US as Usage Service
    participant RD as Redis (Dedup)
    participant KF as Kafka
    participant UA as Usage Aggregator
    participant DB as PostgreSQL

    SDK->>GW: POST /v1/usage-events<br/>{subscriptionId, metricName,<br/> quantity, recordedAt, idempotencyKey}
    GW->>GW: Validate JWT, extract accountId
    GW->>GW: Validate request schema
    GW->>US: ForwardUsageEvent(event)

    US->>RD: EXISTS usage:dedup:{idempotencyKey}
    alt Key already exists (duplicate)
        RD-->>US: 1 (exists)
        US-->>GW: 200 OK {status: "ACCEPTED_DUPLICATE"}
        GW-->>SDK: 200 OK {status: "ACCEPTED_DUPLICATE",<br/> message: "Event already recorded"}
        Note over SDK,DB: Duplicate suppressed — no downstream processing
    else Key is new
        RD-->>US: 0 (not found)
        US->>RD: SET usage:dedup:{idempotencyKey} 1 EX 172800
        Note over RD: TTL = 48 hours; covers client retry windows

        US->>KF: Produce UsageEventMessage<br/>{usageId: uuid(), subscriptionId,<br/> metricName, quantity, recordedAt,<br/> idempotencyKey, ingestedAt}
        KF-->>US: ACK (offset committed)

        US-->>GW: 202 Accepted {usageId, status: "QUEUED"}
        GW-->>SDK: 202 Accepted<br/>{usageId, status: "QUEUED"}
    end

    Note over KF,DB: Asynchronous aggregation path

    KF->>UA: Consume UsageEventMessage (at-least-once)
    UA->>DB: SELECT 1 FROM usage_records<br/> WHERE idempotency_key = ?
    alt Record already in DB (late duplicate via Kafka retry)
        DB-->>UA: Row exists
        UA->>KF: Commit offset (idempotent discard)
    else Record not in DB
        DB-->>UA: No row
        UA->>DB: INSERT INTO usage_records<br/>(usage_id, subscription_id, metric_name,<br/> quantity, recorded_at, idempotency_key)
        DB-->>UA: INSERT OK

        UA->>DB: UPDATE usage_aggregates<br/>SET total_quantity = total_quantity + quantity<br/>WHERE subscription_id = ? AND metric_name = ?<br/> AND period_start <= ? AND period_end >= ?
        Note over UA,DB: Atomic upsert on aggregates table<br/>using ON CONFLICT DO UPDATE

        DB-->>UA: UPDATE OK
        UA->>KF: Commit offset
    end

    Note over SDK,DB: Billing engine reads usage_aggregates<br/>at invoice finalization time
```

---

## Flow 2: Invoice Finalization with Tax Calculation

### Description

At the end of each billing period, the Billing Scheduler triggers invoice finalization for all subscriptions whose `currentPeriodEnd` has passed. The Billing Engine assembles line items from subscription fees and usage charges, delegates tax calculation to Avalara (external tax API), finalizes the invoice, generates a PDF, and dispatches a notification to the customer.

### Key Invariants

- Invoice status transitions from `DRAFT` → `OPEN` → `FINALIZED` atomically within a database transaction.
- If the Avalara API call fails, the invoice is finalized with a zero-tax fallback and a `TAX_CALCULATION_FAILED` flag is recorded for manual review.
- PDF generation is asynchronous; the invoice is considered finalized before the PDF is available.
- The notification is fire-and-forget; failures are retried by the Notification Service independently.

```mermaid
sequenceDiagram
    autonumber
    participant SCH as Billing Scheduler
    participant BE as Billing Engine
    participant USVC as Usage Service
    participant PS as Plan Service
    participant TAX as Tax Service (Avalara)
    participant IR as Invoice Repository
    participant PDF as PDF Service
    participant NS as Notification Service

    SCH->>BE: TriggerInvoiceFinalization<br/>{subscriptionId, periodStart, periodEnd}

    BE->>IR: GetDraftInvoice(subscriptionId, periodStart)
    alt Draft invoice not yet created
        IR-->>BE: null
        BE->>IR: CreateDraftInvoice(subscriptionId, accountId,<br/> periodStart, periodEnd, currency)
        IR-->>BE: Invoice{invoiceId, status: DRAFT}
    else Draft invoice exists
        IR-->>BE: Invoice{invoiceId, status: DRAFT}
    end

    BE->>PS: GetPlanVersion(subscription.planVersionId)
    PS-->>BE: PlanVersion{prices[], trialDays, features}

    BE->>BE: BuildSubscriptionFeeLineItem(price, period)
    Note over BE: Calculates proration if period is partial<br/>e.g., mid-cycle upgrade or trial conversion

    BE->>USVC: GetAggregatedUsage(subscriptionId, periodStart, periodEnd)
    USVC-->>BE: UsageAggregates[]{metricName, totalQuantity}[]

    loop For each metered price in plan version
        BE->>BE: CalculateUsageCharge(price, aggregate.totalQuantity)
        Note over BE: Applies TIERED / VOLUME / PER_UNIT model<br/>Returns lineItem{description, quantity, unitPrice, amount}
    end

    BE->>BE: ApplyActiveDiscounts(accountId, invoiceId)
    Note over BE: Looks up active DiscountApplications<br/>and DiscountLineItem entries

    BE->>IR: UpsertLineItems(invoiceId, lineItems[])
    IR-->>BE: OK — line items persisted

    BE->>BE: ComputeSubtotal(lineItems)

    BE->>TAX: CalculateTax(TaxRequest{<br/> accountId, address, lineItems,<br/> currency, invoiceDate})

    alt Avalara responds successfully
        TAX-->>BE: TaxResponse{<br/> totalTax, lineItemTaxes[],<br/> jurisdictions[], transactionCode}
        BE->>IR: UpsertTaxLineItems(invoiceId, lineItemTaxes[])
        IR-->>BE: OK
        BE->>BE: SetTaxAmount(taxResponse.totalTax)
    else Avalara timeout or 5xx error
        TAX-->>BE: Error / Timeout
        BE->>BE: SetTaxAmount(0)<br/>FlagInvoice(TAX_CALCULATION_FAILED)
        Note over BE: Invoice proceeds with zero tax;<br/>ops team alerted for manual recalculation
    end

    BE->>IR: FinalizeInvoice(invoiceId,<br/> subtotal, taxAmount, total, finalizedAt)
    Note over IR: Atomic status transition DRAFT → OPEN → FINALIZED<br/>with optimistic lock check on invoice version

    IR-->>BE: Invoice{status: FINALIZED, total, amountDue}

    BE->>PDF: EnqueuePdfGeneration(invoiceId)
    Note over PDF: Async — PDF generated from invoice template,<br/>uploaded to object storage, URL stored on invoice

    PDF-->>BE: 202 Accepted {jobId}

    BE->>NS: PublishInvoiceReadyEvent({<br/> accountId, invoiceId, total,<br/> currency, dueDate, periodStart, periodEnd})

    NS->>NS: RenderEmailTemplate(invoice_finalized)
    NS-->>BE: 202 Accepted

    Note over SCH,NS: Customer receives email with invoice summary<br/>and link to customer portal
```

---

## Flow 3: Dunning Step Execution

### Description

When an invoice payment fails, the Dunning Service initiates a retry campaign. Each step is scheduled with an increasing delay (e.g., +3 days, +5 days, +7 days). At each step, the Payment Service attempts to re-charge the invoice. On success, the subscription is reinstated and the customer is notified. On failure, the next step is scheduled unless the maximum retry threshold is reached, at which point the subscription is cancelled.

### Step Delays (Default Policy)

| Step | Delay from Previous Failure |
|---|---|
| Step 1 | Immediately (same day) |
| Step 2 | +3 days |
| Step 3 | +5 days |
| Step 4 | +7 days |
| Abandon | After Step 4 fails |

### Entitlement Degradation

When a subscription enters `PAST_DUE`, entitlements are not immediately revoked. Feature access continues in degraded mode (soft-cap enforcement converts to hard-cap) until the dunning cycle either resolves or is abandoned.

```mermaid
sequenceDiagram
    autonumber
    participant DSCH as Dunning Scheduler
    participant DS as Dunning Service
    participant PSVC as Payment Service
    participant SG as Stripe Gateway
    participant IR as Invoice Repository
    participant SS as Subscription Service
    participant ES as Entitlement Service
    participant NS as Notification Service

    DSCH->>DS: TriggerDunningStep(dunningCycleId, stepNumber)

    DS->>IR: GetInvoice(dunningCycle.invoiceId)
    IR-->>DS: Invoice{invoiceId, amountDue, currency,<br/> accountId, status: FINALIZED}

    DS->>DS: GetDefaultPaymentMethod(accountId)
    alt No default payment method on file
        DS->>NS: PublishDunningEvent({<br/> type: NO_PAYMENT_METHOD,<br/> accountId, invoiceId, stepNumber})
        NS-->>DS: 202 Accepted
        DS->>DS: ScheduleNextStep(dunningCycleId, stepNumber + 1)
        Note over DS: Customer notified to add payment method;<br/>step retried after configured delay
    else Payment method available
        DS->>PSVC: AttemptPayment({<br/> invoiceId, paymentMethodId,<br/> amount: invoice.amountDue,<br/> currency, idempotencyKey: attemptId})

        PSVC->>SG: POST /v1/payment_intents<br/>{amount, currency, payment_method,<br/> customer, confirm: true,<br/> idempotency_key}

        alt Stripe returns success
            SG-->>PSVC: PaymentIntent{status: succeeded,<br/> id: pi_xxx, charges[]}
            PSVC->>IR: RecordPaymentAttempt({<br/> attemptId, invoiceId, paymentMethodId,<br/> status: SUCCEEDED, gatewayTransactionId})
            IR-->>PSVC: OK

            PSVC->>IR: MarkInvoicePaid(invoiceId, paidAt)
            IR-->>PSVC: Invoice{status: PAID}

            PSVC-->>DS: PaymentResult{status: SUCCESS, attemptId}

            DS->>DS: ResolveDunningCycle(dunningCycleId, reason: PAYMENT_COLLECTED)

            DS->>SS: ReactivateSubscription(subscriptionId)
            SS-->>DS: Subscription{status: ACTIVE}

            DS->>ES: RestoreEntitlements(subscriptionId)
            Note over ES: Converts hard-cap enforcement back<br/>to plan-defined soft/hard caps
            ES-->>DS: OK

            DS->>NS: PublishPaymentSucceededEvent({<br/> accountId, invoiceId, amount,<br/> currency, paidAt, subscriptionId})
            NS->>NS: RenderPaymentConfirmationEmail()
            NS-->>DS: 202 Accepted

        else Stripe returns card_declined or insufficient_funds
            SG-->>PSVC: PaymentIntent{status: requires_payment_method,<br/> last_payment_error.code: card_declined}
            PSVC->>IR: RecordPaymentAttempt({<br/> attemptId, invoiceId, paymentMethodId,<br/> status: FAILED, failureCode: card_declined})
            IR-->>PSVC: OK
            PSVC-->>DS: PaymentResult{status: FAILED,<br/> failureCode: card_declined, retriable: true}

            DS->>DS: RecordStepResult(stepId, FAILED, failureCode)

            alt Step is below max retry threshold (step < 4)
                DS->>DS: ScheduleNextStep(dunningCycleId, stepNumber + 1, delay)
                DS->>NS: PublishDunningEvent({<br/> type: PAYMENT_FAILED,<br/> accountId, invoiceId, stepNumber,<br/> nextRetryDate})
                NS->>NS: RenderPaymentRetryNotificationEmail()
                NS-->>DS: 202 Accepted
                Note over DS,NS: Customer informed of failure and<br/>upcoming retry date
            else Max retries reached (stepNumber == 4)
                DS->>DS: AbandonDunningCycle(dunningCycleId)
                DS->>SS: CancelSubscription(subscriptionId,<br/> reason: DUNNING_FAILED, immediately: true)
                SS-->>DS: Subscription{status: CANCELLED}

                DS->>ES: RevokeEntitlements(subscriptionId)
                Note over ES: All feature access immediately removed
                ES-->>DS: OK

                DS->>NS: PublishSubscriptionCancelledEvent({<br/> accountId, subscriptionId, invoiceId,<br/> reason: NON_PAYMENT})
                NS->>NS: RenderSubscriptionCancelledEmail()
                NS-->>DS: 202 Accepted
            end

        else Stripe returns retriable network error or 5xx
            SG-->>PSVC: HTTP 500 or timeout
            PSVC->>IR: RecordPaymentAttempt({<br/> status: FAILED, failureCode: gateway_error})
            IR-->>PSVC: OK
            PSVC-->>DS: PaymentResult{status: FAILED,<br/> failureCode: gateway_error, retriable: true}

            DS->>DS: ScheduleImmediateRetry(dunningCycleId,<br/> stepNumber, backoffSeconds: 300)
            Note over DS: Gateway errors retry the same step<br/>without advancing the step counter;<br/>max 3 gateway retries per step
        end
    end
```

---

## Diagram Notes

### Asynchronous Boundaries

| Flow | Async Boundary | Mechanism |
|---|---|---|
| Usage Ingestion | Kafka publish ↔ Aggregation | Kafka consumer group with at-least-once semantics |
| Invoice Finalization | PDF generation | Internal job queue (e.g., Sidekiq / BullMQ) |
| Invoice Finalization | Customer notification | Event bus publish (Notification Service subscribes) |
| Dunning Execution | Retry scheduling | Scheduled jobs with persistent state in `dunning_steps` table |

### Error Handling Philosophy

All three flows implement the **fail-safe defaults** principle:
- Usage ingestion acknowledges the SDK immediately; downstream failures do not surface to the client.
- Invoice finalization proceeds with zero tax if Avalara is unavailable, flagging the invoice for operator review.
- Dunning execution schedules retries for gateway errors; it does not penalise the customer for infrastructure transience.

### Idempotency Guarantees

Every mutating operation carries an idempotency key at the API boundary:
- Usage events: client-provided `idempotencyKey`
- Payment attempts: `attemptId` UUID passed as Stripe's `idempotency_key` header
- Invoice finalization: guarded by invoice `status` check and optimistic locking on `version` column
