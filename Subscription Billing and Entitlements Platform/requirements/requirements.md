# Requirements — Subscription Billing and Entitlements Platform

## 1. Introduction

This document defines the complete set of functional and non-functional requirements for the Subscription Billing and Entitlements Platform. The platform enables SaaS businesses to manage subscription plan catalogs, automate recurring billing, meter usage-based charges, enforce feature entitlements, collect payments with automated dunning, and produce tax-compliant invoices across multiple jurisdictions.

The system serves Account Owners who subscribe to plans, Billing Admins who manage the plan catalog and billing operations, Developers who integrate entitlement checks and usage reporting into product surfaces, Finance Managers who produce revenue reports and manage recognition schedules, and Customer Success representatives who manage subscriber health.

Requirements in this document are the authoritative source of truth for design, implementation, and acceptance testing decisions.

---

## 2. Functional Requirements

### 2.1 Plan Management

**FR-001** — The system must allow Billing Admins to create a Plan with a name, description, billing interval (monthly, annual, quarterly, or custom day count), trial period duration in days, and default currency.

**FR-002** — The system must support the following Price models on a Plan: flat-rate (fixed amount per period), per-seat (amount multiplied by active seat count), tiered (price per unit decreases as quantity crosses thresholds), volume (entire quantity priced at the tier reached), package (fixed price per N units), and usage-based (price per unit of a metered dimension).

**FR-003** — The system must allow a single Plan to carry multiple Price entries, each associated with a distinct metering dimension or billing component (e.g., a base fee plus a usage fee per API call and a per-seat fee).

**FR-004** — The system must support multi-currency pricing, allowing a Plan to define separate Price amounts for each ISO 4217 currency code. Currency is resolved at subscription creation from the Account's billing currency.

**FR-005** — The system must implement Plan versioning. When a Billing Admin publishes changes to a Plan, a new immutable PlanVersion is created. The original PlanVersion remains accessible and linked to all subscriptions that originated from it.

**FR-006** — The system must assign each PlanVersion a monotonically increasing integer version number scoped to its parent Plan. The system must record the timestamp of publication and the identity of the Billing Admin who published the change.

**FR-007** — The system must support Plan lifecycle states: Draft, Published, Deprecated, and Archived. Only a Published PlanVersion may be selected by new subscribers. A Deprecated PlanVersion remains valid for existing subscriptions but is hidden from the public plan selection API.

**FR-008** — The system must allow a Billing Admin to attach Entitlement definitions to a PlanVersion, specifying the feature key, entitlement type (boolean access, numeric limit, or quota), and the value or limit.

**FR-009** — The system must allow a Billing Admin to add, remove, or modify feature flags and quotas in a new PlanVersion without affecting subscriptions locked to previous PlanVersions.

**FR-010** — The system must provide a Plan catalog API endpoint that returns all currently Published Plans with their current PlanVersion pricing and entitlement details, supporting filtering by billing interval and currency.

---

### 2.2 Subscription Lifecycle

**FR-011** — The system must allow an Account Owner to subscribe to a Published Plan. On subscription creation the system must record: the PlanVersion at time of subscription, the billing start date, the billing cycle anchor, the trial end date (if a trial is configured), and the selected payment method.

**FR-012** — The system must place a new subscription in the **Trialing** state when the selected Plan has a non-zero trial duration. The system must not generate a paid invoice or charge a payment method during the trial period.

**FR-013** — The system must automatically transition a subscription from **Trialing** to **Active** when the trial period ends, provided a valid payment method is attached. If no payment method is attached, the system must send a notification to the Account Owner and move the subscription to **Trialing** in a grace state awaiting payment method addition.

**FR-014** — The system must support mid-cycle plan upgrades and downgrades. On a plan change the system must: calculate proration for the unused portion of the current period, apply that proration as a credit line item, and generate a new charge for the new plan from the change date to the next billing date.

**FR-015** — The system must allow an Account Owner or Billing Admin to cancel a subscription. Cancellation modes must include: immediate (access revoked instantly, prorated refund issued if applicable) and at-period-end (access continues until the end of the current billing period).

**FR-016** — The system must allow an Account Owner or Billing Admin to pause a subscription. While paused, the system must not generate invoices or charge the payment method. Entitlements are revoked during the pause period unless the Plan explicitly grants pause-through entitlements.

**FR-017** — The system must allow resumption of a paused subscription. On resume, the system must restart the billing cycle either from the original anchor date (skip-billing model) or from the resume date (depending on the configured pause policy).

**FR-018** — The system must support subscription trial extensions. A Billing Admin may extend an active trial by a specified number of days. The extension must be audited with the initiating admin's identity and reason.

**FR-019** — The system must enforce seat limits defined in the PlanVersion's Entitlement. When a subscription attempts to exceed its seat entitlement, the system must return an error response with the current seat count and the plan limit.

**FR-020** — The system must generate a subscription event record for every state transition (Trialing, Active, PastDue, Paused, Cancelled, Expired), capturing the previous state, new state, transition timestamp, and initiating actor (system or user identity).

---

### 2.3 Usage Metering

**FR-021** — The system must expose a usage ingestion API endpoint that accepts usage events containing: subscription ID, dimension name, quantity (decimal), idempotency key, and event timestamp. The endpoint must acknowledge receipt with HTTP 202 and process events asynchronously.

**FR-022** — The system must guarantee exactly-once processing of usage events using the provided idempotency key. Duplicate submissions of the same idempotency key must be silently deduplicated; a duplicate must not be double-counted.

**FR-023** — The system must support ingestion throughput of at least 50,000 usage events per second without degrading API response latency below the SLA defined in NFR-001.

**FR-024** — The system must aggregate usage events per subscription, per dimension, and per billing period. Aggregation strategies must include: sum, maximum, and distinct count.

**FR-025** — The system must provide a real-time usage summary API endpoint that returns the current period's aggregated usage per dimension for a given subscription, with a maximum staleness of 60 seconds.

**FR-026** — The system must apply the pricing model defined in the PlanVersion to the aggregated usage at billing period close to produce a rated usage charge. The rating must honour tier boundaries, volume breaks, and minimum charge floors defined in the Price.

**FR-027** — The system must retain raw usage event records for a minimum of 13 months to support billing disputes, audits, and re-rating scenarios.

**FR-028** — The system must support usage backdating, allowing events with timestamps up to 24 hours in the past to be submitted and included in the current billing period. Events older than 24 hours must be rejected with a 422 response and a descriptive error.

**FR-029** — The system must allow a Billing Admin to define usage caps per dimension per subscription. When a cap is reached, the system must emit a webhook event and optionally block further usage (hard cap) or allow overage billing at a configured overage rate (soft cap).

**FR-030** — The system must expose a usage export API that returns paginated raw usage records for a subscription within a date range, supporting CSV and JSON formats.

---

### 2.4 Billing and Invoicing

**FR-031** — The system must automatically generate a draft Invoice at the close of each billing period for every Active subscription. The invoice must include: all recurring flat charges, rated usage charges, proration adjustments from any mid-cycle plan changes, applied discounts from active CouponCodes, account credits, and calculated tax.

**FR-032** — The system must finalise a draft Invoice before initiating payment collection. Finalisation makes the invoice immutable. The finalised invoice must be assigned a sequential invoice number unique within the tenant, a PDF must be rendered asynchronously, and the invoice must be made available via a secure download URL.

**FR-033** — The system must calculate invoice tax amounts by sending invoice line items to the Tax Service, providing the Account's billing address, the line item's product tax code, and the invoice date. The returned tax amounts and jurisdiction codes must be stored on each InvoiceLineItem.

**FR-034** — The system must apply any active DiscountApplications before tax calculation, reducing the taxable base by the discount amount where applicable under the tax jurisdiction's rules.

**FR-035** — The system must support manual invoice creation by a Billing Admin, allowing one-time charges to be added with a description, amount, currency, and tax code outside of the automatic billing cycle.

**FR-036** — The system must allow a Billing Admin to issue a CreditNote against a finalised invoice, specifying the reason (billing error, SLA credit, goodwill, refund), the amount to credit (full or partial), and the credit disposition (apply to next invoice or refund to payment method).

**FR-037** — The system must track Account-level credit balances. When an invoice is generated, available credits must be automatically applied to reduce the invoice balance before charging the payment method. The credit application must be recorded as an InvoiceLineItem of type CREDIT.

**FR-038** — The system must support invoice void by a Billing Admin for invoices in Draft or Finalised (unpaid) state. A void invoice must be replaced by a corrected invoice where required. Void invoices must be retained for audit purposes with a VOID status and cannot be deleted.

**FR-039** — The system must email the finalised invoice PDF to the Account Owner's billing email address within 5 minutes of finalisation.

**FR-040** — The system must provide an invoice list API endpoint that supports filtering by Account, status (Draft, Finalised, Paid, Void, Uncollectible), date range, and currency.

---

### 2.5 Payment and Dunning

**FR-041** — The system must support storage of payment methods including credit/debit cards (via payment gateway tokenisation), ACH bank accounts, and SEPA direct debit mandates. Card numbers must never be stored in the platform's own database; only the gateway-issued token is retained.

**FR-042** — The system must initiate a payment charge against the Account's default payment method within 1 minute of an invoice being finalised with a positive balance. The charge attempt must be recorded as a PaymentAttempt with status (Pending, Succeeded, Failed, Disputed), gateway transaction ID, and timestamp.

**FR-043** — The system must handle payment gateway failures by transitioning the subscription to **PastDue** and initiating the configured DunningCycle. The system must not immediately cancel the subscription on the first payment failure.

**FR-044** — The system must support configurable DunningCycles with the following parameters: list of retry intervals in days from the initial failure (e.g., 3, 7, 14), a maximum number of retry attempts, subscriber email notification templates per attempt, and the action on exhaustion (cancel subscription or mark as uncollectible).

**FR-045** — The system must send a payment failure notification to the Account Owner immediately after each failed payment attempt, including the failure reason (insufficient funds, card expired, do-not-honour), the invoice amount, a link to update the payment method, and the next retry date.

**FR-046** — The system must automatically succeed the DunningCycle and return the subscription to **Active** if a payment succeeds at any retry attempt. Any accrued dunning hold on entitlements must be lifted immediately upon payment success.

**FR-047** — The system must provide a hosted payment update page accessible via a time-limited, tokenised URL that allows an Account Owner to update their payment method without logging in. The token must expire after 72 hours or after first successful use.

**FR-048** — The system must support partial payments. If a partial payment is recorded (e.g., via bank transfer), the invoice balance must be reduced by the received amount, and dunning must continue for the remaining balance.

**FR-049** — The system must record and handle payment disputes (chargebacks). On receiving a dispute webhook from the payment gateway, the system must: mark the PaymentAttempt as Disputed, freeze any pending refunds against that charge, and notify the Billing Admin with dispute details and evidence submission deadline.

**FR-050** — The system must expose a payment history API endpoint returning all PaymentAttempts for an Account, with filtering by invoice ID, status, and date range.

---

### 2.6 Entitlements

**FR-051** — The system must provide a real-time entitlement check API endpoint that accepts a subscription ID and a feature key, and returns: whether access is granted, the current usage against the limit (for quota-type entitlements), and the limit value. The endpoint must respond within 10ms at p99 under normal load.

**FR-052** — The system must automatically create EntitlementGrant records for all Entitlements defined in the PlanVersion when a subscription transitions from Trialing to Active, or when a plan upgrade completes.

**FR-053** — The system must revoke all EntitlementGrants when a subscription is cancelled, paused (unless the plan specifies pause-through access), or suspended due to dunning exhaustion.

**FR-054** — The system must support out-of-band entitlement grants. A Billing Admin may manually grant an Entitlement to a specific subscription for a defined date range, independent of the subscription's PlanVersion. Manual grants must be audited.

**FR-055** — The system must expose an entitlement list API endpoint that returns all current active EntitlementGrants for a subscription, including feature key, grant source (plan or manual), effective start date, end date, limit, and current usage.

---

### 2.7 Tax and Compliance

**FR-056** — The system must determine the applicable tax jurisdiction for each invoice based on the Account's billing address (country, state/province, postal code). For digital services, the jurisdiction is the customer's location, not the vendor's.

**FR-057** — The system must integrate with at least one external tax calculation service via an adapter interface. The adapter must be swappable to support Avalara AvaTax, TaxJar, or a manual rate table without changing the billing engine.

**FR-058** — The system must support tax exemption certificates. An Account Owner or Billing Admin must be able to upload a tax exemption certificate (PDF) for a specific jurisdiction. Once uploaded and approved, that jurisdiction's tax must not be applied to the Account's invoices until the certificate expires.

**FR-059** — The system must support zero-rated and exempt invoice scenarios for B2B EU VAT reverse-charge transactions. When the Account has a valid EU VAT number and is not in the vendor's country, the system must apply 0% VAT and annotate the invoice line with the applicable reverse-charge note.

**FR-060** — The system must store the tax amount, tax rate, tax jurisdiction code, and tax transaction ID (returned by the tax service) on each InvoiceLineItem for audit purposes.

**FR-061** — The system must generate a tax report exportable in CSV format, showing per-invoice, per-jurisdiction tax amounts collected in a configurable date range. The report must be suitable for VAT/GST filing.

**FR-062** — The system must retain all invoice, tax, and payment records for a minimum of 7 years to meet financial record-keeping requirements in applicable jurisdictions.

---

## 3. Non-Functional Requirements

### 3.1 Performance

**NFR-001** — The billing API (plan, subscription, invoice read endpoints) must respond at p99 latency under 200ms for requests served from primary data regions, measured at the API Gateway.

**NFR-002** — The entitlement check API must respond at p99 latency under 10ms under steady-state load of 10,000 requests per second, served from an in-process or sidecar cache backed by Redis.

**NFR-003** — Invoice generation, including usage aggregation, proration calculation, discount application, and tax calculation, must complete within 5 seconds for subscriptions with up to 1 million usage events in the billing period.

**NFR-004** — The usage ingestion endpoint must sustain 50,000 events per second with p99 write-acknowledgement latency under 50ms. The ingestion pipeline is allowed to process events asynchronously after acknowledgement.

**NFR-005** — PDF invoice rendering must complete within 10 seconds for invoices with up to 500 line items. Rendering is performed asynchronously and the PDF URL must be available within 60 seconds of invoice finalisation.

**NFR-006** — Dunning retry execution for up to 100,000 subscriptions in PastDue state must complete within a 15-minute processing window on the scheduled retry date.

### 3.2 Availability

**NFR-007** — The billing and subscription APIs must maintain 99.95% monthly uptime (allowing no more than 21.9 minutes of downtime per month), excluding scheduled maintenance windows announced at least 48 hours in advance.

**NFR-008** — The entitlement check API must maintain 99.99% monthly uptime, as it is on the critical path of every API request served by integrated product surfaces.

**NFR-009** — The platform must implement active-passive failover for the primary PostgreSQL cluster with automated promotion in under 30 seconds using a consensus-based health check (Patroni or equivalent).

**NFR-010** — Usage event ingestion must degrade gracefully under database unavailability by buffering events in Kafka for up to 24 hours without data loss, then replaying once the database recovers.

### 3.3 Security

**NFR-011** — The platform must comply with PCI DSS Level 1. No raw card data (PAN, CVV, expiry) may be stored, logged, or transmitted through platform-owned systems. All cardholder data must pass through the payment gateway's tokenisation flow.

**NFR-012** — All API endpoints must require authentication. Internal service-to-service calls must use short-lived JWT tokens (expiry 15 minutes) signed with RSA-256. External client API calls must use per-account API keys with configurable IP allowlisting.

**NFR-013** — All data at rest must be encrypted using AES-256. Database encryption must be enforced at the storage layer (cloud provider managed keys) with optional customer-managed keys (BYOK) for enterprise tiers.

**NFR-014** — All data in transit must be encrypted using TLS 1.2 or higher. TLS 1.0 and 1.1 must be disabled. Certificate rotation must be automated with zero downtime.

**NFR-015** — The platform must implement row-level multi-tenant isolation at the database layer. Every query against tenant-scoped tables must include a tenant_id predicate enforced by ORM middleware, not application code alone.

### 3.4 Scalability

**NFR-016** — All platform services must be horizontally scalable by adding stateless instances behind a load balancer. No service may hold session state in local memory; all shared state must be stored in Redis or the primary database.

**NFR-017** — The platform must support at least 10 million active subscriptions per deployment, with billing batch jobs completing within the nightly processing window without requiring downtime.

**NFR-018** — Database schema migrations must be backwards-compatible and executed without table locks using online schema change tools (pt-online-schema-change or equivalent). Zero-downtime deployments must be the default release mode.

### 3.5 Compliance and Auditability

**NFR-019** — The platform must achieve and maintain SOC 2 Type II certification covering Security, Availability, and Confidentiality trust service criteria. Audit log records must be immutable, tamper-evident, and retained for 12 months online and 7 years in cold storage.

**NFR-020** — The platform must comply with GDPR and CCPA for personal data handling. Account Owners must be able to request data export (all records related to their account) within 30 days and data deletion (right to erasure) within 30 days, subject to financial record-keeping retention obligations.

**NFR-021** — Revenue recognition schedules produced by the platform must comply with ASC 606 (US GAAP) and IFRS 15 (international) standards. The recognition schedule for a 12-month prepaid subscription must spread revenue evenly across the 12 months of service delivery.

**NFR-022** — All state-modifying API operations must produce an immutable audit log entry capturing: operation type, actor identity (user or service), timestamp, source IP, request ID, previous state, and new state. Audit logs must be queryable by Finance Managers and Billing Admins via the admin portal.
