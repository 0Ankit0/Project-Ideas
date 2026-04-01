# C4 Level 3 — Billing Engine Component Diagram

## Overview

This document provides a C4 Model Level 3 (Component) diagram for the **Billing Engine**, the core subsystem responsible for generating, rating, and finalizing invoices. Level 3 drills inside the container boundary to show the individual components, their responsibilities, and their interactions with each other and with external systems.

The Billing Engine is a container within the broader Subscription Billing and Entitlements Platform. It is invoked on a scheduled basis at the end of each billing cycle and on-demand for proration events triggered by subscription changes.

---

## C4 Component Diagram

```mermaid
C4Component
    title C4 Level 3 — Billing Engine

    Container_Boundary(billingEngine, "Billing Engine") {
        Component(idb, "InvoiceDraftBuilder", "Service Component", "Fetches subscription data and the pinned plan version. Constructs the invoice shell with billing period metadata and account details.")
        Component(ure, "UsageRatingEngine", "Service Component", "Retrieves aggregated usage for the billing period. Applies flat, tiered, volume, and package pricing models to produce rated usage line items.")
        Component(pc, "ProrationCalculator", "Service Component", "Computes day-weighted credit and charge adjustments for mid-cycle plan changes. Returns proration line items for both the outgoing and incoming plan.")
        Component(ca, "CreditApplicator", "Service Component", "Queries the credit ledger and applies available, non-expired account credits to the invoice in FIFO order. Records each credit application for audit.")
        Component(de, "DiscountEngine", "Service Component", "Evaluates attached coupons and promotional discounts. Applies percentage and fixed-amount discounts in the correct sequence and validates redemption limits.")
        Component(tia, "TaxIntegrationAdapter", "Service Component", "Routes tax calculation requests to the configured external provider (Avalara or TaxJar) or falls back to the LocalRuleEngine. Returns per-line-item tax breakdown.")
        Component(if, "InvoiceFinalizer", "Service Component", "Assembles all line items into the complete invoice. Assigns an invoice number, locks the invoice, persists it, publishes domain events, and triggers PDF rendering.")
    }

    ContainerDb(postgres, "PostgreSQL", "Relational Database", "Stores subscriptions, plan versions, prices, invoices, credits, and dunning records.")
    Container(taxService, "TaxCalculator Service", "Internal Service", "Wraps Avalara and TaxJar. Provides a unified tax computation interface.")
    ContainerDb(redis, "Redis", "In-Memory Store", "Caches plan version and price data. Stores idempotency keys for usage events.")
    Container(kafka, "Kafka", "Message Broker", "Receives InvoiceGenerated and InvoiceFinalized events for downstream consumers.")
    System_Ext(avalara, "Avalara AvaTax", "External Tax Service", "Provides real-time multi-jurisdiction tax calculation.")
    System_Ext(taxjar, "TaxJar SmartCalcs", "External Tax Service", "Alternative real-time tax calculation provider.")
    ContainerDb(s3, "Amazon S3", "Object Storage", "Stores rendered PDF invoices.")

    Rel(idb, postgres, "Reads subscription and plan version data", "JDBC/SQL")
    Rel(idb, redis, "Reads cached plan version and prices", "Redis GET")
    Rel(ure, postgres, "Reads aggregated usage records for the billing period", "JDBC/SQL")
    Rel(ure, redis, "Reads cached pricing tiers", "Redis GET")
    Rel(pc, postgres, "Reads plan change events and cycle boundaries", "JDBC/SQL")
    Rel(ca, postgres, "Reads and writes credit ledger entries", "JDBC/SQL")
    Rel(de, postgres, "Reads coupon definitions and redemption counts", "JDBC/SQL")
    Rel(tia, taxService, "Delegates tax calculation", "gRPC / HTTP")
    Rel(taxService, avalara, "Calls AvaTax API", "HTTPS REST")
    Rel(taxService, taxjar, "Calls SmartCalcs API (fallback)", "HTTPS REST")
    Rel(if, postgres, "Writes finalized invoice and line items", "JDBC/SQL")
    Rel(if, kafka, "Publishes InvoiceGenerated and InvoiceFinalized events", "Kafka Produce")
    Rel(if, s3, "Uploads rendered PDF invoice", "S3 PutObject")

    Rel(idb, ure, "Passes InvoiceDraft for usage rating", "In-process call")
    Rel(idb, pc, "Passes InvoiceDraft for proration calculation", "In-process call")
    Rel(ure, tia, "Passes draft with usage line items for tax computation", "In-process call")
    Rel(pc, tia, "Passes draft with proration line items for tax computation", "In-process call")
    Rel(tia, ca, "Passes draft with tax line items for credit application", "In-process call")
    Rel(ca, de, "Passes draft after credit application for discount evaluation", "In-process call")
    Rel(de, if, "Passes fully assembled draft for finalization", "In-process call")
```

---

## Component Responsibilities

### InvoiceDraftBuilder

**Purpose:** Entry point for the Billing Engine. Initializes the billing run for a given subscription.

**Responsibilities:**
- Loads the `Subscription` record from PostgreSQL, including account ID, plan version pin, billing cycle dates, currency, and collection method.
- Resolves the pinned `PlanVersion` from the `CatalogCache` (Redis). Falls back to PostgreSQL on a cache miss and warms the cache.
- Constructs the `InvoiceDraft` struct with billing period, empty line-item list, account reference, and tax configuration.
- Detects whether a plan change event has occurred within the billing period to trigger the `ProrationCalculator`.

**Interfaces Consumed:**
- `SubscriptionRepository.getById(subscriptionId): Subscription`
- `CatalogCache.getVersion(versionId): PlanVersion`

**Outputs:**
- `InvoiceDraft` — the mutable work-in-progress invoice object passed to downstream components.

---

### UsageRatingEngine

**Purpose:** Converts raw usage aggregates into monetary line items using the plan's pricing rules.

**Responsibilities:**
- Queries `AggregationWorker`'s output in PostgreSQL for all usage metrics registered on the plan during the billing period.
- Applies the pricing model for each metric:
  - **Flat:** `quantity × unit_price`
  - **Tiered:** iterates through pricing tiers; each tier applies to the portion of usage within its range.
  - **Volume:** selects the single tier that matches total volume; applies that unit price to all units.
  - **Package:** rounds usage up to the nearest package size; applies package price.
- Produces one `UsageLineItem` per metric.

**Interfaces Consumed:**
- `UsageRepository.getAggregates(subscriptionId, metricName, from, to): UsageAggregate`
- `PriceRepository.getPricesByVersion(versionId): Price[]`

**Outputs:**
- `UsageLineItem[]` appended to `InvoiceDraft.lineItems`

---

### ProrationCalculator

**Purpose:** Computes mid-cycle billing adjustments when a plan change (upgrade or downgrade) occurs.

**Responsibilities:**
- Receives the `PlanChangeEvent` recorded at plan-change time (old plan, new plan, change timestamp).
- Computes:
  - `D_remaining = billing_cycle_end - change_timestamp` (in fractional days)
  - `D_total = billing_cycle_end - billing_cycle_start`
  - `credit = (D_remaining / D_total) × old_plan_price`
  - `new_charge = (D_remaining / D_total) × new_plan_price`
- Handles same-day changes: if change occurs on cycle boundary, skips proration entirely.
- Handles annual plan mid-year: uses 365-day denominator with day-precise numerator.
- Produces one credit line item (negative amount) and one charge line item (positive amount).

**Interfaces Consumed:**
- `SubscriptionRepository.getPlanChangeEvents(subscriptionId, cycleStart, cycleEnd): PlanChangeEvent[]`
- `PlanVersionRepository.getById(versionId): PlanVersion`

**Outputs:**
- `ProrationLineItem[]` appended to `InvoiceDraft.lineItems`

---

### TaxIntegrationAdapter

**Purpose:** Abstracts the external tax calculation call from the rest of the billing pipeline.

**Responsibilities:**
- Receives the `InvoiceDraft` with all fixed, usage, and proration line items assembled.
- Resolves the customer's billing address and applicable tax-exempt status.
- Selects the tax provider based on account configuration (`avalara` | `taxjar` | `local`).
- Sends the transaction request to `TaxCalculator` service (which wraps the external providers).
- Parses the response and maps external tax codes to internal `TaxLineItem` objects.
- Falls back to `LocalRuleEngine` if the external provider returns a non-retriable error.

**Interfaces Consumed:**
- `TaxCalculatorService.compute(transaction: TaxRequest): TaxResult`

**Outputs:**
- `TaxLineItem[]` appended to `InvoiceDraft.lineItems`

---

### CreditApplicator

**Purpose:** Reduces the invoice balance using available customer account credits.

**Responsibilities:**
- Queries the credit ledger for the account, filtering to credits with status `ACTIVE` and non-expired `expires_at`.
- Applies credits in FIFO order (oldest first) up to the invoice total.
- Records a `CreditApplicationRecord` for each credit consumed, noting the amount applied and remaining balance.
- Produces a `CreditLineItem` (negative amount) on the draft for audit and display purposes.

**Interfaces Consumed:**
- `CreditRepository.getActiveCredits(accountId): Credit[]`
- `CreditRepository.applyCredit(creditId, amount): void`

**Outputs:**
- `CreditLineItem[]` appended to `InvoiceDraft.lineItems`
- Updated `InvoiceDraft.credit_applied` total

---

### DiscountEngine

**Purpose:** Applies promotional and contractual discounts to the invoice.

**Responsibilities:**
- Loads coupons attached to the subscription (via `SubscriptionCoupon` join table).
- Validates each coupon: checks `valid_from`, `valid_until`, `max_redemptions`, and `duration_in_months` window.
- Applies discounts in sequence:
  1. Percentage discounts applied first to subtotal.
  2. Fixed-amount discounts applied to remaining balance after percentage discounts.
- Increments the redemption counter for `duration: "once"` coupons.
- Produces a `DiscountLineItem` per applied coupon.

**Interfaces Consumed:**
- `CouponRepository.getCouponsForSubscription(subscriptionId): SubscriptionCoupon[]`
- `CouponRepository.incrementRedemption(couponId): void`

**Outputs:**
- `DiscountLineItem[]` appended to `InvoiceDraft.lineItems`
- Updated `InvoiceDraft.discount_total`

---

### InvoiceFinalizer

**Purpose:** Commits the fully assembled invoice and triggers all downstream side effects.

**Responsibilities:**
- Assigns a sequential human-readable invoice number (e.g., `INV-2024-00423`).
- Transitions invoice status from `DRAFT` to `OPEN`.
- Persists the `Invoice` record and all associated `LineItem` records to PostgreSQL within a single database transaction.
- Publishes `InvoiceGenerated` event to Kafka topic `billing-events` (payload includes invoice ID, account ID, amount, currency, due date).
- Triggers `PDFRenderer` asynchronously to generate the invoice PDF; stores the returned S3 URL on the invoice record.
- Publishes `InvoiceFinalized` event after PDF URL is stored.

**Interfaces Consumed:**
- `InvoiceRepository.create(invoice, lineItems): Invoice` (transactional)
- `KafkaProducer.publish(topic, event)`
- `PDFRenderer.render(invoice): S3URL`

**Outputs:**
- Persisted `Invoice` entity returned to the orchestrating billing scheduler.

---

## Data Flow Summary

```mermaid
sequenceDiagram
    participant Scheduler as Billing Scheduler
    participant IDB as InvoiceDraftBuilder
    participant URE as UsageRatingEngine
    participant PC as ProrationCalculator
    participant TIA as TaxIntegrationAdapter
    participant CA as CreditApplicator
    participant DE as DiscountEngine
    participant IF as InvoiceFinalizer
    participant PG as PostgreSQL
    participant Redis as Redis
    participant Avalara as Avalara/TaxJar
    participant Kafka as Kafka
    participant S3 as S3

    Scheduler->>IDB: buildDraft(subscriptionId, cycleStart, cycleEnd)
    IDB->>Redis: getVersion(versionId)
    IDB->>PG: getSubscription(subscriptionId)
    IDB-->>URE: InvoiceDraft (shell)
    URE->>PG: getAggregates(subscriptionId, period)
    URE-->>PC: InvoiceDraft + UsageLineItems
    PC->>PG: getPlanChangeEvents(subscriptionId, period)
    PC-->>TIA: InvoiceDraft + ProrationLineItems
    TIA->>Avalara: POST /transactions/create
    Avalara-->>TIA: TaxResult
    TIA-->>CA: InvoiceDraft + TaxLineItems
    CA->>PG: getActiveCredits(accountId)
    CA-->>DE: InvoiceDraft + CreditLineItems
    DE->>PG: getCouponsForSubscription(subscriptionId)
    DE-->>IF: InvoiceDraft (fully assembled)
    IF->>PG: INSERT invoice + line_items (transaction)
    IF->>Kafka: publish InvoiceGenerated
    IF->>S3: putObject(invoice.pdf)
    IF->>Kafka: publish InvoiceFinalized
    IF-->>Scheduler: Invoice{id, status: OPEN}
```

---

## External System Interactions

| External System | Interaction | Protocol | Failure Handling |
|-----------------|-------------|----------|-----------------|
| **PostgreSQL** | Read subscriptions, plan versions, usage aggregates, credits, coupons. Write invoices, line items, credit applications. | JDBC over TCP | Retry 3× with exponential backoff. Transactions roll back on failure. |
| **Redis** | Read cached plan versions and prices. Write idempotency keys. | Redis Protocol | Cache miss falls back to PostgreSQL. Redis unavailability is non-fatal. |
| **Avalara AvaTax** | POST `/transactions/create` with line items and customer address. | HTTPS REST | Falls back to TaxJar. If both fail, falls back to `LocalRuleEngine`. |
| **TaxJar SmartCalcs** | POST `/taxes` as secondary tax provider. | HTTPS REST | Falls back to `LocalRuleEngine` on failure. |
| **Kafka** | Publish `InvoiceGenerated` and `InvoiceFinalized` to `billing-events` topic. | Kafka Producer API | Retry with producer retries=3. Non-blocking: PDF rendering proceeds independently. |
| **Amazon S3** | `PutObject` with rendered invoice PDF. URL stored on invoice record. | AWS SDK (HTTPS) | Retry 3× with exponential backoff. PDF URL stored asynchronously; invoice status is not blocked. |
