# Subscription Billing and Entitlements Platform

A production-grade, multi-tenant platform for managing subscription plans, billing cycles, usage metering, entitlement enforcement, and revenue operations at scale. Designed to handle millions of subscribers with sub-second entitlement checks, automated dunning, tax compliance, and revenue recognition reporting.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Actors and Stakeholders](#actors-and-stakeholders)
3. [Architecture Overview](#architecture-overview)
4. [Domain Entities](#domain-entities)
5. [Key Features](#key-features)
6. [Core Terms Glossary](#core-terms-glossary)
7. [Getting Started](#getting-started)
8. [Documentation Structure](#documentation-structure)
9. [Documentation Status](#documentation-status)

---

## System Overview

The Subscription Billing and Entitlements Platform provides the full financial and access-control backbone for SaaS, usage-based, and hybrid subscription businesses. It handles the complete lifecycle from a prospect selecting a plan, trialing the product, converting to a paid subscription, consuming metered resources, being invoiced automatically, paying via stored payment methods, and having entitlements enforced in real time across every API call.

The platform is built around immutable plan versioning so that existing subscribers are never broken by plan changes, automated dunning pipelines that recover failed payments without human intervention, proration logic for mid-cycle plan changes, credit note issuance, tax calculation via jurisdiction-aware rules and external tax service integration, and SOC 2 / PCI DSS-compliant data handling.

It exposes a REST API consumed by product surfaces, a webhook system for downstream integrations, and an event stream for analytics and revenue recognition pipelines.

---

## Actors and Stakeholders

| Actor | Type | Responsibilities |
|---|---|---|
| **Account Owner** | Internal Human | Owns the billing account; selects plans, manages payment methods, authorises seats |
| **Billing Admin** | Internal Human | Configures plan catalog, applies coupons, issues credit notes, manages dunning policies |
| **Developer** | Internal Human / System | Integrates entitlement checks via API, reports usage events, manages webhooks |
| **Finance Manager** | Internal Human | Reviews revenue reports, manages revenue recognition schedules, exports invoices |
| **Customer Success** | Internal Human | Monitors customer subscription health, initiates plan changes, resolves payment failures |
| **Payment Gateway** | External System | Processes card charges, ACH, and SEPA; returns authorisation results and dispute events |
| **Tax Service** | External System | Calculates tax amounts per line item by jurisdiction; returns tax codes and rates |

---

## Architecture Overview

The platform is decomposed into purpose-built microservices that communicate via synchronous REST for request/response flows and asynchronous events (Kafka) for high-throughput pipelines.

```
Client Applications
        |
        v
  +-------------+
  | API Gateway |  -- JWT auth, rate limiting, tenant routing
  +------+------+
         |
  +------+-------------------------------------------------------------------+
  |                        Internal Service Mesh                             |
  |                                                                          |
  |  +--------------+   +---------------------+   +---------------------+   |
  |  | Plan Service |   | Subscription Service|   | Usage Metering Svc  |   |
  |  |              |   |                     |   |                     |   |
  |  | * Plan CRUD  |   | * Lifecycle mgmt    |   | * Ingest events     |   |
  |  | * Versioning |   | * Trial handling    |   | * Aggregate usage   |   |
  |  | * Pricing    |   | * Pause / Resume    |   | * Rate metered use  |   |
  |  +--------------+   +---------------------+   +---------------------+   |
  |                                                                          |
  |  +---------------+   +-----------------+   +------------------------+   |
  |  | Billing Engine|   | Payment Service |   | Dunning Service        |   |
  |  |               |   |                 |   |                        |   |
  |  | * Invoicing   |   | * Charge cards  |   | * Retry schedule       |   |
  |  | * Proration   |   | * Refunds       |   | * Subscriber alerts    |   |
  |  | * Credits     |   | * Dispute mgmt  |   | * Cancel on exhaustion |   |
  |  +---------------+   +-----------------+   +------------------------+   |
  |                                                                          |
  |  +--------------------+   +--------------+   +----------------------+   |
  |  | Entitlement Service|   |  Tax Service |   | Notification Service |   |
  |  |                    |   |  (Adapter)   |   |                      |   |
  |  | * Grant / Revoke   |   | * Jurisdictn |   | * Email / SMS        |   |
  |  | * Real-time check  |   | * Tax codes  |   | * Webhooks           |   |
  |  | * Usage limits     |   | * Exemptions |   | * In-app push        |   |
  |  +--------------------+   +--------------+   +----------------------+   |
  +--------------------------------------------------------------------------+
         |                      |
  +------+------+        +------+----------+
  |  PostgreSQL  |        |  Kafka Topics   |
  |  (primary)   |        |  (event stream) |
  +-------------+        +-----------------+
```

### Service Responsibilities

| Service | Primary Responsibility |
|---|---|
| **API Gateway** | Authentication (JWT/API key), rate limiting, tenant header injection, TLS termination |
| **Plan Service** | Plan and pricing catalog CRUD, version management, deprecation workflows |
| **Subscription Service** | Subscription lifecycle state machine, trial management, pause/resume, cancellations |
| **Usage Metering Service** | High-throughput event ingestion (50k events/sec), aggregation, usage-based rating |
| **Billing Engine** | Invoice generation, proration calculations, credit application, line item assembly |
| **Payment Service** | Payment method vault, gateway abstraction, charge execution, refund processing |
| **Dunning Service** | Failed-payment retry scheduling, subscriber communication, escalation to cancellation |
| **Entitlement Service** | Real-time feature/seat/quota checks, grant management, cache-backed low-latency reads |
| **Tax Service** | Jurisdiction detection, tax rate lookup, exemption certificate management |
| **Notification Service** | Outbound email/SMS/webhook delivery, template rendering, delivery tracking |

---

## Domain Entities

### Core Billing Entities

| Entity | Description |
|---|---|
| **Account** | A billing account representing a customer organisation; root tenant unit |
| **Subscription** | A binding between an Account and a PlanVersion with lifecycle state and billing dates |
| **Plan** | A named product offering with pricing tiers and feature entitlements |
| **PlanVersion** | An immutable snapshot of a Plan at a point in time; subscriptions lock to a version |
| **Price** | A pricing rule attached to a PlanVersion (flat, per-seat, tiered, volume, usage-based) |
| **UsageRecord** | A single metered consumption event with timestamp, quantity, and dimension |
| **Invoice** | A billing statement generated at period end or on demand; contains line items |
| **InvoiceLineItem** | A single charge or credit entry on an Invoice with amount, tax, and description |
| **PaymentMethod** | A tokenised payment instrument (card, ACH, SEPA) stored in the payment vault |
| **PaymentAttempt** | A single charge execution record with gateway response, status, and timestamps |
| **Credit** | A monetary credit balance on an Account applied against future invoices |
| **CreditNote** | A formal document reducing the value of a previously issued invoice |

### Entitlement Entities

| Entity | Description |
|---|---|
| **Entitlement** | A feature or resource access rule attached to a PlanVersion |
| **EntitlementGrant** | An active grant of an Entitlement to a Subscription with effective dates and limits |

### Promotion Entities

| Entity | Description |
|---|---|
| **CouponCode** | A promotional code defining discount type, amount, duration, and redemption limits |
| **DiscountApplication** | A record of a CouponCode being applied to a Subscription with effective dates |

### Tax and Compliance Entities

| Entity | Description |
|---|---|
| **TaxRate** | A tax percentage applicable to a jurisdiction and product tax code combination |
| **TaxJurisdiction** | A geographic or legal taxing authority (country, state, province, county) |

### Dunning Entities

| Entity | Description |
|---|---|
| **DunningCycle** | A configured retry schedule defining attempt timings, escalation steps, and cancellation threshold |

---

## Key Features

### Plan and Pricing Catalog
Create and manage a rich catalog of subscription plans with support for flat-rate, per-seat, tiered, volume, and usage-based pricing models. Plans support multiple currencies, billing intervals (monthly, annual, custom), and can have free trials attached. Every published plan creates an immutable PlanVersion ensuring backward compatibility.

### Subscription Lifecycle Management
Full state machine covering **Trialing -> Active -> PastDue -> Paused -> Cancelled -> Expired**. Supports immediate and scheduled cancellations, prorated refunds, trial extensions, and mid-cycle plan upgrades/downgrades with automatic proration calculations. Subscribers are never moved to a new plan version without explicit consent or administrative action.

### Usage Metering and Rating
Ingest usage events at 50,000 events per second via a high-throughput API. Supports multiple metering dimensions (API calls, storage GB, active seats, compute minutes). Aggregates usage within billing periods and applies configurable rating rules to convert raw usage into invoice charges.

### Invoice Generation
Automated invoice generation at billing period end, on plan changes, or on demand. Invoices include flat charges, usage-based charges, prorations, discounts, and tax line items. PDF rendering, secure download URLs, and email delivery are built in. Invoices are immutable once finalised; adjustments create CreditNotes.

### Payment Collection with Dunning
Charges stored payment methods automatically at invoice finalisation. On failure, a configurable DunningCycle governs retry attempts (e.g., Day 3, Day 7, Day 14) with automated subscriber communications. Subscriptions transition to **PastDue** during the dunning window and to **Cancelled** if all retries are exhausted. Manual payment links and hosted payment pages are available for self-service recovery.

### Credit Notes and Proration
Issue CreditNotes against finalised invoices for full or partial refunds, service credits, or SLA compensation. Proration logic automatically calculates partial-period charges when a subscription plan changes mid-cycle, crediting unused time and charging only for the new plan from the change date.

### Entitlement Enforcement
Real-time entitlement checks via a low-latency (<10ms p99) API that confirms whether a subscriber has access to a feature, has remaining quota, or has exceeded a usage limit. Entitlements are automatically granted when a subscription activates and revoked when it cancels. Cache-backed reads serve millions of checks per second.

### Tax Calculation
Automatic tax determination using the subscriber's billing address and the product's tax code. Integrates with external tax services (Avalara, TaxJar) for jurisdiction-aware rate lookup. Supports tax exemptions via certificate upload, reverse-charge VAT for B2B EU transactions, and tax-inclusive pricing display.

### Coupon Management
Create time-limited or perpetual coupon codes with fixed or percentage discounts. Configure per-account redemption limits, total redemption caps, minimum order values, and plan restrictions. Track redemption history and discount attribution for revenue reporting.

### Revenue Recognition
Generate revenue recognition schedules that spread deferred revenue across service periods in compliance with ASC 606 / IFRS 15. Export recognition events to accounting systems via webhook or CSV. Supports annual prepaid, monthly recurring, and usage-based revenue recognition models.

---

## Core Terms Glossary

| Term | Definition |
|---|---|
| **Plan** | A product offering in the catalog with a name, description, features, and pricing structure |
| **PlanVersion** | An immutable snapshot of a Plan at a specific version number. Subscriptions lock to a PlanVersion at purchase and are not automatically migrated when the Plan changes |
| **Proration** | The calculation of a partial-period charge or credit when a subscription changes mid-billing-cycle. Calculated as `(days_remaining / days_in_period) x price_difference` |
| **Entitlement** | A rule defining what features, seats, or resource quotas a subscriber has access to under a specific PlanVersion |
| **DunningCycle** | A configured schedule of payment retry attempts and subscriber notifications triggered after an initial payment failure |
| **UsageRecord** | A single usage event submitted by an application, capturing dimension name, quantity, idempotency key, and timestamp |
| **Invoice** | A finalised billing statement for a period, containing all charges, credits, discounts, and tax. Immutable once issued |
| **CreditNote** | A formal document that partially or fully offsets a previously issued Invoice. Creates a credit balance on the Account |
| **PaymentAttempt** | A single execution of a charge against a PaymentMethod, recording the gateway request, response code, amount, and timestamp |

---

## Getting Started

1. **Read the Requirements** — Start with [`requirements/requirements.md`](requirements/requirements.md) to understand all functional and non-functional requirements. Review [`requirements/user-stories.md`](requirements/user-stories.md) for role-based feature expectations.

2. **Review Plan Versioning Rules** — Read [`requirements/plan-versioning-and-lifecycle-requirements.md`](requirements/plan-versioning-and-lifecycle-requirements.md) to understand how plan changes interact with existing subscriptions and the grandfathering model.

3. **Study the Analysis** — Review the domain model, event storming outputs, and bounded context maps in [`analysis/`](analysis/).

4. **Review High-Level Design** — The [`high-level-design/`](high-level-design/) folder contains system architecture diagrams, service decomposition, and integration patterns.

5. **Examine Detailed Design** — Service-level designs, API contracts, database schemas, and state machine specifications live in [`detailed-design/`](detailed-design/).

6. **Review Infrastructure Design** — Deployment topology, Kubernetes configuration, data tier design, and observability setup are in [`infrastructure/`](infrastructure/).

7. **Implementation Guide** — Language/framework choices, coding standards, testing strategy, and CI/CD pipeline definitions are in [`implementation/`](implementation/).

8. **Edge Cases** — Critical edge cases for billing correctness, idempotency, and failure recovery are documented in [`edge-cases/`](edge-cases/).

---

## Documentation Structure

| Folder | Contents | Status |
|---|---|---|
| [`requirements/`](requirements/) | Functional requirements, user stories, plan versioning rules, non-functional requirements | Complete |
| [`analysis/`](analysis/) | Domain model, bounded contexts, event storming, entity-relationship diagrams | Complete |
| [`high-level-design/`](high-level-design/) | System architecture, service topology, integration patterns, data flow diagrams | Complete |
| [`detailed-design/`](detailed-design/) | API specifications, database schemas, state machines, sequence diagrams | Complete |
| [`infrastructure/`](infrastructure/) | Kubernetes manifests, cloud architecture, database replication, observability | Complete |
| [`implementation/`](implementation/) | Tech stack, coding standards, testing strategy, CI/CD, deployment runbooks | Complete |
| [`edge-cases/`](edge-cases/) | Billing edge cases, idempotency guarantees, failure recovery scenarios | Complete |

### Requirements Files

| File | Description |
|---|---|
| [`requirements/requirements.md`](requirements/requirements.md) | Full functional (FR-001 to FR-062) and non-functional (NFR-001 to NFR-020) requirements |
| [`requirements/user-stories.md`](requirements/user-stories.md) | 20+ user stories with acceptance criteria across all roles |
| [`requirements/plan-versioning-and-lifecycle-requirements.md`](requirements/plan-versioning-and-lifecycle-requirements.md) | Detailed plan versioning and subscription lifecycle rules (PVL-001 to PVL-030) |

---

## Documentation Status

| Document | Status | Last Updated |
|---|---|---|
| README.md | Complete | 2025 |
| requirements/requirements.md | Complete | 2025 |
| requirements/user-stories.md | Complete | 2025 |
| requirements/plan-versioning-and-lifecycle-requirements.md | Complete | 2025 |
| analysis/ | Complete | 2025 |
| high-level-design/ | Complete | 2025 |
| detailed-design/ | Complete | 2025 |
| infrastructure/ | Complete | 2025 |
| implementation/ | Complete | 2025 |
| edge-cases/ | Complete | 2025 |

---

## Contributing

All documentation follows the project's [Documentation Completion Checklist](../Documentation-Completion-Checklist.md). Before submitting changes:

- Ensure no placeholder text (TODO, TBD, N/A) remains in any file.
- Verify all cross-references point to existing files and sections.
- Confirm all requirement IDs are unique and sequentially numbered.
- Validate that domain entity names are consistent across all documents.
