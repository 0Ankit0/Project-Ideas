# Requirements — Payment Orchestration and Wallet Platform

**Document Version:** 1.0  
**Status:** Approved  
**Last Updated:** 2025-07-14  
**Owner:** Product & Architecture  
**Classification:** Internal — Confidential

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Scope](#3-scope)
4. [Functional Requirements](#4-functional-requirements)
5. [Non-Functional Requirements](#5-non-functional-requirements)
6. [Phased Delivery Plan](#6-phased-delivery-plan)
7. [Constraints and Assumptions](#7-constraints-and-assumptions)
8. [Dependencies](#8-dependencies)

---

## 1. Executive Summary

The **Payment Orchestration and Wallet Platform** (POWP) is a cloud-native, API-first financial infrastructure layer designed to unify payment acceptance, digital wallet management, multi-currency settlement, and fraud prevention under a single programmable platform. It exposes RESTful and event-driven APIs to merchants, marketplaces, and embedded-finance operators, enabling them to accept payments from any channel — card, bank transfer, wallet, and alternative payment methods — while abstracting the operational complexity of managing multiple Payment Service Providers (PSPs).

The platform targets digital-native businesses, SaaS companies with billing requirements, marketplace operators handling split payments, and financial institutions building embedded-finance products. By providing a single integration point with intelligent routing across PSPs, the platform eliminates vendor lock-in and reduces payment failure rates through automated failover. The wallet module supports multi-currency balances, real-time FX conversion, and programmatic ledger posting, enabling treasury teams to move funds globally with full auditability and without manual reconciliation overhead.

The primary business value delivered by POWP is threefold: (1) improved authorization rates through dynamic PSP routing and 3DS2 orchestration; (2) operational cost reduction through automated three-way reconciliation and dispute management; and (3) regulatory risk mitigation through built-in PCI DSS Level 1 compliance, PSD2 SCA support, AML screening integration, and GDPR data lifecycle controls. The platform is designed for a peak throughput of 10,000 TPS with horizontal scalability to 50,000 TPS, targeting 99.99% availability for payment-critical APIs.

---

## 2. Problem Statement

### 2.1 Multi-PSP Complexity

Businesses operating at scale require relationships with multiple PSPs to achieve geographic coverage, redundancy, and cost optimization. Managing these relationships today requires separate integrations, credential management, reconciliation processes, and monitoring setups per PSP. When a PSP experiences an outage or degrades in authorization rate, engineers are paged manually to reroute traffic — a slow, error-prone process that directly causes lost revenue.

### 2.2 Manual Reconciliation Overhead

Settlement reconciliation today is largely manual: finance teams download PSP settlement files, match them against internal transaction records and bank statements in spreadsheets, and manually investigate breaks. This process is time-consuming, error-prone, and creates a T+2 or longer lag before financial books are accurate. Discrepancies go undetected for days, and there is no systematic audit trail for manual adjustments.

### 2.3 Fraud Losses and Reactive Controls

Fraud teams rely on static rule engines applied post-authorization, meaning fraudulent transactions are often approved and only detected during chargeback review. Chargeback rates above 1% trigger card scheme penalties. Without real-time velocity checking, ML scoring integration, and automated evidence submission, businesses absorb avoidable losses and operational overhead in dispute management.

### 2.4 Wallet and FX Fragmentation

Businesses operating in multiple currencies maintain separate ledger systems for wallet balances, use manual FX rate feeds, and lack programmatic APIs for fund movements. This creates treasury blind spots, delayed payout cycles, and currency mismatch losses when FX rates are not locked at transaction time.

---

## 3. Scope

### 3.1 In-Scope / Out-of-Scope

| # | Feature Area | In Scope | Out of Scope |
|---|---|---|---|
| 1 | Payment Processing | Card, bank transfer, wallet payments via PSP routing | Physical POS terminal hardware |
| 2 | PSP Integrations | Stripe, Adyen, Braintree, Checkout.com (configurable) | Proprietary issuer-direct integrations |
| 3 | Wallet Management | Multi-currency digital wallets, transfers, FX conversion | Consumer retail banking accounts |
| 4 | Card Vaulting | PCI DSS Level 1 card vault with tokenization | Issuer card management (PIN change, block) |
| 5 | Fraud & Risk | Real-time scoring, velocity checks, rule engine, ML integration | KYC/identity document verification |
| 6 | Refunds & Disputes | Full/partial refunds, chargeback lifecycle management | Legal representation in arbitration |
| 7 | Split Payments | Marketplace splits, escrow hold, payout scheduling | Tax calculation and withholding |
| 8 | FX & Currency | Live rates, conversion, markup, rate locking | Derivatives or hedging instruments |
| 9 | Settlement & Reconciliation | Daily batch, PSP file matching, three-way recon | Bank ledger posting on behalf of merchants |
| 10 | Webhooks & Notifications | Event subscriptions, HMAC-signed delivery, retry | Real-time push via WebSocket (Phase 2) |
| 11 | Sandbox & Testing | Isolated environment, test cards, simulated PSPs | Load testing infrastructure provisioning |
| 12 | Reporting & Analytics | Pre-built reports, custom date ranges, CSV export | BI warehouse pipeline (Snowflake/Redshift) |
| 13 | Compliance | PCI DSS L1, PSD2 SCA, GDPR, AML screening hooks | DORA, ISO 27001 certification management |
| 14 | Merchant Onboarding | API-driven merchant account creation and configuration | Full KYB (Know Your Business) document review |

---

## 4. Functional Requirements

### 4.1 Payment Processing (FR-001 – FR-008)

**FR-001 — Payment Intent Creation**  
The system SHALL accept a `POST /v1/payment-intents` request containing amount, currency, payment method, merchant ID, and idempotency key. It SHALL return a payment intent object with a unique `payment_intent_id`, initial status `CREATED`, and a client secret for front-end confirmation. The creation latency p99 SHALL be under 500 ms.

**FR-002 — Intelligent PSP Routing**  
The routing engine SHALL select the optimal PSP for each payment intent based on configurable criteria including: merchant preference, card BIN country, currency support, PSP real-time health score, historic authorization rate per BIN range, and transaction cost. Routing rules SHALL be configurable per merchant via a UI and API without code deployments.

**FR-003 — PSP Failover and Re-routing**  
If the primary PSP returns a network timeout, 5xx error, or soft decline within a configurable retry window (default: 3 seconds), the system SHALL automatically re-route the payment to the next-ranked PSP. The failover SHALL be transparent to the customer and SHALL preserve the original idempotency key. Failover SHALL complete within 5 seconds of the primary failure detection.

**FR-004 — Partial Capture**  
The system SHALL support partial capture of authorized amounts. A `POST /v1/payment-intents/{id}/capture` request SHALL accept an optional `amount` parameter less than or equal to the authorized amount. Uncaptured amounts SHALL be released back to the cardholder according to card scheme rules (default: 7 days). Partial captures SHALL generate a distinct ledger entry.

**FR-005 — Idempotency Enforcement**  
All mutating payment API endpoints SHALL enforce idempotency via a client-supplied `Idempotency-Key` header (UUID v4 format). Duplicate requests with the same key within a 24-hour window SHALL return the original response with HTTP 200 and an `X-Idempotent-Replayed: true` header. The idempotency store SHALL be backed by a distributed cache with TTL.

**FR-006 — Inbound Webhook Processing**  
The system SHALL receive and process webhook events from all configured PSPs. It SHALL validate event signatures using the PSP-specific HMAC or RSA scheme. Events SHALL be persisted to an append-only event store before processing, ensuring at-least-once delivery semantics. Duplicate events SHALL be deduplicated using event IDs.

**FR-007 — 3DS2 Orchestration**  
For card payments requiring Strong Customer Authentication under PSD2, the system SHALL orchestrate the 3DS2 flow: device data collection, authentication request to the issuer ACS, challenge handling, and authentication result embedding into the authorization request. The system SHALL support both frictionless and challenge flows. 3DS2 SHALL be bypassed for MIT (Merchant-Initiated Transactions) and whitelisted merchant categories.

**FR-008 — Authorization Expiry Management**  
The system SHALL track authorization expiry for all authorized payment intents. When an authorization approaches expiry (configurable threshold, default: 24 hours before expiry), the system SHALL emit an `authorization.expiring` event. If the merchant does not capture before expiry, the system SHALL automatically void the authorization and transition the payment intent to `EXPIRED` status, releasing the reserved funds.

---

### 4.2 Wallet Management (FR-009 – FR-015)

**FR-009 — Multi-Currency Wallet Creation**  
The system SHALL allow merchants and customers to hold digital wallet balances in multiple currencies (ISO 4217). Each wallet SHALL have a unique `wallet_id` and SHALL support sub-wallets per currency. Wallet balances SHALL be maintained using a double-entry ledger. Creating a wallet SHALL require identity verification credentials tied to the owning account.

**FR-010 — Credit and Debit Operations**  
The system SHALL expose `POST /v1/wallets/{id}/credit` and `POST /v1/wallets/{id}/debit` endpoints. Debit operations SHALL enforce a non-negative balance constraint (configurable overdraft limit per wallet). All credit/debit operations SHALL be idempotent and SHALL produce an immutable ledger entry with `journal_id`, timestamp, amount, currency, and reason code.

**FR-011 — Wallet-to-Wallet Transfer**  
The system SHALL support same-currency and cross-currency wallet-to-wallet transfers via `POST /v1/wallets/transfers`. Transfers SHALL be atomic: both the debit of the source wallet and the credit of the destination wallet SHALL succeed or both SHALL be rolled back. Cross-currency transfers SHALL use the real-time FX rate at time of transfer (see FR-038).

**FR-012 — Wallet Freeze and Unfreeze**  
Authorized platform administrators and compliance officers SHALL be able to freeze a wallet via `POST /v1/wallets/{id}/freeze`, preventing all debit operations while allowing credit operations unless a full freeze flag is set. Freeze events SHALL emit a `wallet.frozen` event and SHALL require a reason code and actor ID for audit purposes. Unfreeze SHALL require dual-approval above a configurable balance threshold.

**FR-013 — Transaction History**  
The system SHALL provide a paginated `GET /v1/wallets/{id}/transactions` endpoint returning the full ledger history for a wallet, filterable by date range, currency, transaction type, and status. Responses SHALL include cursor-based pagination and SHALL support up to 10,000 records per export request.

**FR-014 — FX Conversion**  
The system SHALL support programmatic FX conversion between any two supported currency pairs via `POST /v1/wallets/{id}/convert`. The conversion SHALL debit the source currency sub-wallet and credit the target currency sub-wallet atomically. The applied rate SHALL be recorded on the ledger entry. Configurable FX markup (basis points) SHALL be applied per merchant tier.

**FR-015 — Virtual Account Assignment**  
The system SHALL support assigning virtual IBANs or virtual account numbers to wallets for receiving bank transfers. Each virtual account SHALL be associated with exactly one wallet. Inbound transfers to a virtual account SHALL automatically credit the linked wallet and emit a `wallet.credited` event with the originating bank reference.

---

### 4.3 Card Vaulting & Tokenization (FR-016 – FR-020)

**FR-016 — PCI DSS Level 1 Card Vault**  
The system SHALL maintain a dedicated card vault service that stores Primary Account Numbers (PANs) in encrypted form using AES-256 at rest, isolated in a PCI DSS Level 1 compliant network segment. Raw PANs SHALL never traverse application-layer services. The vault SHALL pass annual PCI DSS QSA assessment and support key rotation without service interruption.

**FR-017 — Tokenization**  
The system SHALL replace all PANs with network-agnostic tokens (format: `tok_[32-char-hex]`) upon card registration. Tokens SHALL be bound to the merchant that created them (merchant-scoped tokens). Cross-merchant token use SHALL require explicit sharing consent. The tokenization service SHALL return the token within 100 ms p99.

**FR-018 — Card Fingerprinting**  
The system SHALL generate a deterministic card fingerprint for each unique PAN, independent of expiry date and CVV. The fingerprint SHALL allow merchants to detect duplicate card registrations across different cardholders or registration events without exposing the PAN. Fingerprints SHALL be stored in the vault and returned alongside tokens.

**FR-019 — BIN Lookup**  
The system SHALL provide a `GET /v1/bins/{bin}` endpoint returning: card network (Visa, Mastercard, Amex), card type (credit/debit/prepaid), issuing bank name, issuing country (ISO 3166), and 3DS2 support flag. BIN data SHALL be sourced from a licensed BIN database updated at minimum monthly.

**FR-020 — Token Refresh**  
The system SHALL support token lifecycle management: tokens SHALL expire 12 months after last use (configurable). The system SHALL support network tokenization (Visa Token Service, Mastercard MDES) for improved authorization rates. Network token updates (PAR changes, expiry updates) SHALL be propagated to stored tokens automatically via account updater integration.

---

### 4.4 Fraud & Risk (FR-021 – FR-026)

**FR-021 — Real-Time Fraud Scoring**  
The system SHALL invoke a fraud scoring service synchronously during payment intent authorization, completing within 150 ms p99. The scorer SHALL return a risk score (0–1000), a decision (`ALLOW`, `REVIEW`, `DECLINE`), and a list of triggered rule IDs. Decisions SHALL be embedded in the payment intent object and audit log.

**FR-022 — Velocity Checks**  
The system SHALL enforce configurable velocity rules on payment attempts, including: maximum transactions per card per time window, maximum spend per card per time window, maximum attempts per IP address, and maximum failed attempts per merchant account. Velocity rules SHALL be evaluated in real time using a sliding window counter backed by Redis.

**FR-023 — Rules Engine**  
The system SHALL provide a configurable fraud rules engine with a UI and API for creating, updating, enabling, disabling, and testing rules without code deployments. Rules SHALL support conditions on: amount range, currency, card BIN, issuing country, device fingerprint, velocity counts, IP geolocation, and time-of-day. Rules SHALL support priority ordering and short-circuit evaluation.

**FR-024 — ML Model Integration**  
The system SHALL expose an integration interface for external ML model inference endpoints (REST, gRPC). The fraud service SHALL call the configured model endpoint with a standardized feature set and incorporate the model score into the composite risk decision. The integration SHALL support model versioning and A/B testing with configurable traffic splits.

**FR-025 — Manual Review Queue**  
Transactions with a `REVIEW` decision SHALL be placed in a manual review queue accessible to Risk Analysts via the operations console and API. Queue items SHALL display: transaction details, risk score, triggered rules, cardholder history, and device data. Analysts SHALL be able to approve (allow), decline, or escalate queue items. SLA timers SHALL alert when items exceed the configured review window (default: 4 hours).

**FR-026 — Case Management**  
The system SHALL support fraud case creation, linking multiple related transactions, attaching evidence (screenshots, logs, IP data), assigning cases to analysts, and tracking case status through `OPEN`, `UNDER_REVIEW`, `RESOLVED_FRAUD`, `RESOLVED_LEGITIMATE`, and `ESCALATED`. All case actions SHALL be audit-logged with actor, timestamp, and reason.

---

### 4.5 Refunds & Disputes (FR-027 – FR-032)

**FR-027 — Full and Partial Refunds**  
The system SHALL support full and partial refunds via `POST /v1/payment-intents/{id}/refunds`. Partial refund amounts SHALL not exceed the captured amount less any previously refunded amount. Refunds SHALL be submitted to the originating PSP and SHALL produce a ledger reversal entry. The system SHALL enforce idempotency on refund requests using a client-supplied idempotency key.

**FR-028 — Chargeback Intake**  
The system SHALL receive chargeback notifications from PSPs via webhooks and SHALL automatically create a dispute record linked to the originating transaction. Dispute records SHALL capture: reason code, amount, currency, card scheme dispute ID, response deadline, and PSP-supplied evidence requirements.

**FR-029 — Evidence Submission**  
The system SHALL allow merchants to upload dispute evidence (invoices, delivery confirmations, screenshots, terms of service acceptance logs) via `POST /v1/disputes/{id}/evidence`. Evidence SHALL be assembled into a structured package conforming to card scheme submission requirements and submitted to the PSP before the response deadline. Automated evidence pre-population SHALL include: transaction receipt, customer IP, device fingerprint, and fraud score.

**FR-030 — Dispute Timeline Tracking**  
The system SHALL maintain a chronological timeline for each dispute: creation, merchant response, issuer ruling, representment, pre-arbitration, and arbitration. Deadline-based SLA alerts SHALL be sent to the responsible team (email + ops console notification) at configurable thresholds (e.g., 48 hours before response deadline).

**FR-031 — Automated Reversal**  
When a dispute is lost (issuer rules in favor of the cardholder), the system SHALL automatically debit the merchant's wallet or settlement account for the chargeback amount plus any applicable fee, post the compensating ledger entry, and update the payment intent status to `CHARGEBACK_LOST`. This SHALL occur within 1 hour of receiving the final ruling webhook from the PSP.

**FR-032 — Chargeback Analytics**  
The system SHALL provide a chargeback analytics dashboard displaying: chargeback rate by MCC, chargeback rate by PSP, chargeback reason code distribution, win/loss ratio, and trend over time. Merchants approaching card scheme chargeback thresholds (0.9% for Visa, 1% for Mastercard) SHALL receive automated alerts.

---

### 4.6 Split Payments (FR-033 – FR-036)

**FR-033 — Split Rules Configuration**  
The system SHALL allow merchants to define payment split rules specifying the percentage or fixed-amount allocation to each sub-merchant or connected account for a given payment. Split rules SHALL be configurable per payment at the API level (`split_config` object on the payment intent) or as default merchant-level rules.

**FR-034 — Marketplace Payout**  
After a payment is captured and the clearing period has elapsed, the system SHALL distribute the split amounts to the respective sub-merchant wallets. Each sub-merchant SHALL receive a distinct ledger credit and payout notification. The marketplace platform fee SHALL be retained as a separate ledger entry in the platform wallet.

**FR-035 — Escrow Hold**  
The system SHALL support an escrow mode where captured funds are held in a platform-controlled escrow wallet pending a release condition (configurable: time-based, manual approval, or delivery confirmation webhook). Escrow holds SHALL be visible in the payment intent status as `ESCROWED`. Release SHALL be triggered via `POST /v1/escrow/{id}/release`.

**FR-036 — Payout Scheduling**  
The system SHALL support configurable payout schedules for sub-merchants: daily, weekly, bi-weekly, or monthly. Scheduled payouts SHALL aggregate all cleared balances and initiate bank transfer or wallet credit on the scheduled date. Sub-merchants SHALL be able to request an instant payout subject to available balance and risk score, with a configurable instant payout fee.

---

### 4.7 FX & Currency (FR-037 – FR-040)

**FR-037 — Live FX Rate Feed**  
The system SHALL integrate with at least two FX rate providers (primary and fallback) to maintain a real-time rate feed for all supported currency pairs. Rates SHALL be refreshed at a configurable interval (default: 30 seconds). Stale rates (older than 2 minutes) SHALL trigger an alert and SHALL cause FX operations to fail with a `FX_RATE_STALE` error until rates are refreshed.

**FR-038 — Currency Conversion**  
The system SHALL convert amounts between supported currencies using the mid-market rate at time of conversion plus the configured merchant markup (in basis points). Conversion calculations SHALL use banker's rounding to the target currency's minor unit. Both the mid-market rate, markup applied, and final converted amount SHALL be stored on the ledger entry.

**FR-039 — FX Markup Configuration**  
Platform administrators SHALL be able to configure FX markup rates per currency pair per merchant tier via the admin API and UI. Markups SHALL be expressed in basis points (1 bps = 0.01%). Markup changes SHALL take effect for new conversions immediately and SHALL not affect in-flight transactions.

**FR-040 — Rate Locking**  
The system SHALL support FX rate locking for a configurable duration (default: 30 minutes) to allow customers to see and confirm a quoted rate before completing a payment. A `POST /v1/fx/rate-locks` endpoint SHALL return a `rate_lock_id` and the locked rate. Payments referencing an active `rate_lock_id` SHALL use the locked rate. Expired rate locks SHALL return a `RATE_LOCK_EXPIRED` error.

---

### 4.8 Settlement & Reconciliation (FR-041 – FR-046)

**FR-041 — Daily Settlement Batch**  
The system SHALL run a daily settlement batch job that aggregates all captured transactions by PSP, currency, and merchant for the settlement date. The batch SHALL generate a settlement summary report and submit payout instructions to the corresponding PSP or bank. The batch SHALL be idempotent: re-running for the same date SHALL produce the same output.

**FR-042 — PSP Settlement File Matching**  
The system SHALL ingest PSP settlement files (CSV, MT940, CAMT.054) via SFTP or API. Each PSP transaction line SHALL be matched against the internal ledger using: transaction ID, amount, currency, and settlement date. Matched records SHALL be marked `RECONCILED`. Unmatched records SHALL be flagged for investigation.

**FR-043 — Three-Way Reconciliation**  
The reconciliation engine SHALL perform a three-way match across: (1) internal ledger, (2) PSP settlement file, and (3) bank statement. The engine SHALL classify discrepancies into categories: `TIMING` (expected to clear), `AMOUNT_MISMATCH`, `MISSING_FROM_PSP`, `MISSING_FROM_LEDGER`, `DUPLICATE`. A tolerance threshold (configurable per merchant/currency) SHALL be applied before raising a break.

**FR-044 — Break Detection and Alerting**  
When a reconciliation break is detected and exceeds the configured tolerance, the system SHALL create a break record with severity (`LOW`, `MEDIUM`, `HIGH`), root cause category, affected amount, and linked transaction IDs. High-severity breaks SHALL trigger immediate alerts to the Finance Manager and on-call engineer via email and PagerDuty integration.

**FR-045 — Manual Adjustment**  
Authorized Finance Managers SHALL be able to post manual ledger adjustments via `POST /v1/ledger/adjustments` with a mandatory reason code, supporting document attachment, and dual-approval requirement for adjustments above a configurable threshold (default: $10,000). All manual adjustments SHALL be audit-logged with approver identities.

**FR-046 — Ledger Audit Trail**  
The system SHALL maintain an immutable, append-only ledger audit trail for all financial events. Each ledger entry SHALL record: `journal_id`, `created_at`, `amount`, `currency`, `debit_account`, `credit_account`, `transaction_reference`, `actor_id`, and `event_type`. The audit trail SHALL be exportable in JSON and CSV formats for regulatory review.

---

### 4.9 Webhooks & Notifications (FR-047 – FR-052)

**FR-047 — Event Subscriptions**  
The system SHALL allow merchants to subscribe to specific event types via `POST /v1/webhooks/subscriptions`. Supported event categories SHALL include: payment lifecycle, wallet operations, dispute events, refund events, settlement events, and fraud events. Each subscription SHALL specify an endpoint URL, event types, and an optional event filter (e.g., by currency or merchant sub-account).

**FR-048 — Delivery Retry with Backoff**  
Failed webhook deliveries (non-2xx response or timeout after 5 seconds) SHALL be retried using an exponential backoff schedule: 30 seconds, 5 minutes, 30 minutes, 2 hours, 6 hours, 24 hours. After 6 failed attempts, the event SHALL be marked `DEAD_LETTER` and an alert SHALL be sent to the merchant's configured notification email.

**FR-049 — HMAC Payload Signing**  
All outbound webhook payloads SHALL be signed using HMAC-SHA256 with a merchant-specific secret. The signature SHALL be included in the `X-Powp-Signature` header as `sha256={hex_digest}`. Merchants SHALL be able to rotate their webhook signing secret via the API with a configurable overlap period (default: 24 hours) during which both old and new secrets are valid.

**FR-050 — Delivery Log**  
The system SHALL maintain a delivery log for each webhook event attempt, recording: event ID, endpoint URL, request headers, request payload hash, HTTP status code, response body (up to 1 KB), attempt number, and timestamp. Delivery logs SHALL be queryable via `GET /v1/webhooks/deliveries` and SHALL be retained for 90 days.

**FR-051 — Event Replay**  
The system SHALL support manual replay of any webhook event within the last 72 hours via `POST /v1/webhooks/deliveries/{id}/replay`. Replayed events SHALL include an `X-Powp-Replay: true` header. Bulk replay for a time range SHALL be supported for incident recovery scenarios.

**FR-052 — Email and SMS Notifications**  
The system SHALL send configurable email and SMS notifications to merchants and customers for: successful payment, failed payment, refund initiated, refund completed, dispute opened, and payout processed. Notification templates SHALL be merchant-customizable via the dashboard. Notification preferences SHALL respect GDPR consent flags.

---

### 4.10 Sandbox & Testing (FR-053 – FR-056)

**FR-053 — Isolated Sandbox Environment**  
The system SHALL provide a fully isolated sandbox environment with separate API credentials, databases, and PSP simulators. Sandbox data SHALL not be accessible from production and vice versa. The sandbox SHALL mirror the production API surface with the same versioning, authentication, and response schemas.

**FR-054 — Test Card Numbers**  
The sandbox SHALL support a documented set of test card numbers that trigger deterministic responses: successful authorization, decline (insufficient funds), decline (do not honor), 3DS2 frictionless flow, 3DS2 challenge flow, network error, and authorization timeout. Test cards SHALL cover Visa, Mastercard, American Express, and Discover BIN ranges.

**FR-055 — Simulated PSP Responses**  
The sandbox SHALL include configurable PSP simulators that can be set to return specific response codes, simulate latency (configurable delay in ms), simulate partial outages (configurable failure rate %), and simulate webhook events at a configurable delay after authorization. Simulation parameters SHALL be configurable per API key.

**FR-056 — Sandbox Webhooks**  
The sandbox SHALL deliver webhook events to merchant-configured endpoints with the same signing and retry logic as production. The sandbox SHALL support a webhook event inspector UI showing all events sent, their payloads, and delivery status, to assist integration engineers during development.

---

### 4.11 Reporting & Analytics (FR-057 – FR-062)

**FR-057 — Revenue Reports**  
The system SHALL provide a revenue report showing: gross transaction volume (GTV), net revenue (GTV minus refunds and chargebacks), processing fees, FX revenue, and platform fees — aggregated by day, week, month, and custom date ranges. Reports SHALL be filterable by merchant, currency, PSP, and payment method. Export to CSV and PDF SHALL be supported.

**FR-058 — Settlement Reports**  
The system SHALL generate per-merchant settlement reports for each settlement batch, showing: settled transactions, settlement amount by currency, PSP fees deducted, net payout amount, and settlement date. Settlement reports SHALL be delivered automatically to the configured merchant email and SHALL be accessible via `GET /v1/reports/settlements`.

**FR-059 — Chargeback Rate Monitoring**  
The system SHALL calculate and display chargeback rates (chargebacks / total transactions) by merchant, MCC, card network, and PSP. The report SHALL highlight merchants approaching or exceeding card scheme thresholds and SHALL provide drill-down to individual chargeback records. Trend charts SHALL display a rolling 3-month view.

**FR-060 — Refund Rate Analytics**  
The system SHALL calculate refund rates by merchant, product category, and time period. Anomaly detection SHALL flag merchants whose refund rate exceeds a configurable threshold (default: 5%). Refund reason code distribution SHALL be displayed to identify systematic issues.

**FR-061 — PSP Performance Dashboard**  
The system SHALL provide a PSP performance dashboard displaying: authorization rate by PSP, average latency by PSP, error rate by PSP, failover event count, and settlement timeliness. The dashboard SHALL update in near-real-time (refresh interval: 60 seconds) and SHALL be accessible to Platform Admins and Integration Engineers.

**FR-062 — Custom Date Range Reports**  
All reporting endpoints SHALL accept ISO 8601 date range parameters (`date_from`, `date_to`). The maximum date range per single report request SHALL be 12 months. Reports for ranges exceeding 30 days SHALL be processed asynchronously, with the merchant notified via webhook and email when the report is ready for download.

---

### 4.12 Compliance (FR-063 – FR-068)

**FR-063 — PCI DSS Level 1 Compliance**  
The platform SHALL achieve and maintain PCI DSS Level 1 compliance (the highest tier, required for processors handling over 6 million transactions/year). This SHALL include: network segmentation for cardholder data environment (CDE), quarterly internal vulnerability scans, annual external penetration testing, and an annual QSA on-site assessment. PCI DSS compliance scope SHALL be minimized using tokenization (FR-017).

**FR-064 — PSD2 Strong Customer Authentication**  
For transactions processed on behalf of EU-based merchants or EU-issued cards, the system SHALL enforce PSD2 SCA requirements by orchestrating 3DS2 (FR-007). The system SHALL correctly apply SCA exemptions including: low-value transactions (< €30), merchant-initiated transactions, trusted beneficiary whitelist, and low-risk transaction exemption based on transaction risk analysis (TRA).

**FR-065 — GDPR Data Export and Deletion**  
The system SHALL support GDPR data subject rights: (1) Right of Access — export all personal data associated with a customer identifier within 72 hours of request via `POST /v1/compliance/gdpr/export`; (2) Right to Erasure — anonymize or delete personal data within 30 days of a verified deletion request via `POST /v1/compliance/gdpr/delete`, subject to financial record retention requirements (minimum 7 years for transaction records).

**FR-066 — AML Screening Integration**  
The system SHALL integrate with a configurable AML/sanctions screening provider. All new wallet creations and payouts above a configurable threshold SHALL be screened against sanctions lists (OFAC SDN, EU Consolidated, UN Consolidated). Screening matches SHALL trigger a `REVIEW` hold and SHALL notify the Compliance Officer. The system SHALL support manual review override with documented justification.

**FR-067 — Audit Logs**  
The system SHALL maintain immutable, tamper-evident audit logs for all security-relevant events including: user authentication, authorization decisions, data access, configuration changes, and financial operations. Audit logs SHALL include: timestamp (UTC), actor ID, actor IP, action, resource type, resource ID, outcome, and correlation ID. Logs SHALL be retained for a minimum of 7 years and SHALL be exportable for regulatory review.

**FR-068 — Data Residency Controls**  
The system SHALL support configurable data residency for merchant accounts, ensuring that cardholder data and transaction records for merchants in regulated jurisdictions (EU, UK, India) are stored and processed within the designated geographic region. Data residency configuration SHALL be enforced at the infrastructure level (region-pinned database clusters) and SHALL be auditable.

---

## 5. Non-Functional Requirements

| ID | Category | Requirement | Target | Measurement Method |
|---|---|---|---|---|
| NFR-001 | Availability | Payment API uptime | 99.99% monthly | Synthetic monitoring (every 30s), monthly SLO report |
| NFR-002 | Latency | Payment intent creation p99 | < 500 ms | APM distributed trace percentiles, 30-day rolling |
| NFR-003 | Latency | End-to-end authorization p99 | < 2,000 ms | APM trace from API receipt to PSP response return |
| NFR-004 | Throughput | Sustained peak TPS | 10,000 TPS | Load test (monthly), production traffic burst metrics |
| NFR-005 | Security | PCI DSS compliance level | Level 1 | Annual QSA assessment report |
| NFR-006 | Regulatory | PSD2 SCA enforcement | 100% of in-scope EU transactions | Compliance audit, exemption application rate report |
| NFR-007 | Regulatory | GDPR Article 17 erasure | Within 30 calendar days | Automated deletion SLA monitoring, quarterly audit |
| NFR-008 | Resilience | RPO / RTO | RPO < 1 min / RTO < 5 min | Quarterly DR drill, failover test report |
| NFR-009 | Security | Encryption at rest and in transit | AES-256 at rest, TLS 1.3 in transit | Annual pen test, certificate scan, encryption audit |
| NFR-010 | Scalability | Horizontal scalability ceiling | 50,000 TPS | Capacity planning load test, autoscaling stress test |
| NFR-011 | Observability | Audit log completeness | 100% of security events logged | Log pipeline integrity check, gap analysis report |
| NFR-012 | Resilience | Multi-region active-active | 2+ AWS/GCP regions | Chaos engineering monthly test, region failover drill |
| NFR-013 | Correctness | Idempotency guarantee | Zero duplicate charges | Automated idempotency test suite, production anomaly scan |
| NFR-014 | Maintainability | API versioning | Minimum 2 major versions supported concurrently | API gateway version routing metrics, deprecation notice log |
| NFR-015 | Security | OWASP Top 10 compliance | No critical or high unmitigated vulnerabilities | Quarterly DAST scan (OWASP ZAP), annual pen test |

---

## 6. Phased Delivery Plan

| Feature | MVP (Phase 1) | Phase 2 | Phase 3 |
|---|---|---|---|
| Card payment acceptance (Visa/MC) | ✅ | | |
| Single PSP integration (Stripe) | ✅ | | |
| Basic PSP routing (single PSP) | ✅ | | |
| Idempotency and webhook ingest | ✅ | | |
| Simple refunds (full only) | ✅ | | |
| Sandbox environment | ✅ | | |
| Basic fraud rules engine | ✅ | | |
| Multi-PSP routing and failover | | ✅ | |
| Partial capture | | ✅ | |
| 3DS2 orchestration (PSD2 SCA) | | ✅ | |
| Multi-currency wallet with ledger | | ✅ | |
| Wallet-to-wallet transfers | | ✅ | |
| Partial refunds | | ✅ | |
| Chargeback intake and evidence submission | | ✅ | |
| Daily settlement batch | | ✅ | |
| PSP settlement file reconciliation | | ✅ | |
| Card vaulting and tokenization (PCI L1) | | ✅ | |
| BIN lookup service | | ✅ | |
| Real-time ML fraud scoring integration | | | ✅ |
| FX rate feed and conversion | | | ✅ |
| Rate locking | | | ✅ |
| Split payments and marketplace payout | | | ✅ |
| Escrow hold and release | | | ✅ |
| Three-way reconciliation engine | | | ✅ |
| AML screening integration | | | ✅ |
| GDPR data export and deletion API | | | ✅ |
| Data residency controls | | | ✅ |
| Custom reporting and analytics | | | ✅ |
| Virtual account assignment | | | ✅ |
| Network tokenization (VTS/MDES) | | | ✅ |

---

## 7. Constraints and Assumptions

1. **Regulatory Scope**: The platform itself does not hold an e-money license; it operates as a technology layer on top of licensed PSPs. Merchants are responsible for their own regulatory compliance in their jurisdictions.
2. **PSP Contracts**: Merchant onboarding to specific PSPs (Stripe, Adyen, etc.) is outside the platform's scope. The platform assumes merchants have valid PSP agreements with appropriate MCC codes.
3. **PCI DSS Scope Reduction**: It is assumed that all card data from the front end will be collected directly by the vault service or via PSP-hosted fields, ensuring the primary application servers remain out of PCI scope.
4. **Banking Infrastructure**: Virtual account IBANs and bank transfer capabilities depend on a banking partner (e.g., ClearBank, Modulr) providing the underlying banking rails. The platform does not provide banking infrastructure directly.
5. **FX Rate Providers**: The platform will integrate with a licensed FX data provider (e.g., Open Exchange Rates, XE Business). The accuracy of FX rates is subject to the provider's SLA.
6. **AML Provider**: Integration with an AML screening provider (e.g., ComplyAdvantage, Refinitiv World-Check) is required for Phase 3. The platform provides the integration interface; the AML provider maintains the sanctions list data.
7. **Event Ordering**: Downstream consumers of the event stream must handle out-of-order delivery. The platform guarantees at-least-once delivery, not strict ordering, except within a single transaction's event chain.
8. **Browser/SDK Support**: The 3DS2 orchestration requires the merchant to integrate the platform's JavaScript SDK or mobile SDK. Native app integrations using the raw API will require merchant-side 3DS2 handling.
9. **Database Technology**: The ledger database is assumed to be a serializable-isolation RDBMS (PostgreSQL). NoSQL databases are not acceptable for financial ledger storage.
10. **Multi-Region Latency**: Active-active multi-region deployment assumes < 80 ms inter-region replication latency. Higher latency regions may require active-passive fallback.
11. **Card Scheme Rules**: All card scheme rules (Visa, Mastercard) change periodically. The platform will review and update compliance annually or upon formal card scheme notification.
12. **Soft Deletes Only**: Financial records (transactions, ledger entries, disputes) SHALL never be hard-deleted. GDPR erasure is implemented via pseudonymization of personal data fields while retaining the financial record structure.

---

## 8. Dependencies

### 8.1 External PSP Dependencies

| Provider | Integration Type | Purpose | SLA Dependency |
|---|---|---|---|
| Stripe | REST API + Webhooks | Primary PSP (card, wallet, ACH) | Stripe API SLA (99.99%) |
| Adyen | REST API + Webhooks | Secondary PSP, marketplace payouts | Adyen SLA (99.95%) |
| Braintree | REST API + Webhooks | Tertiary PSP (PayPal, Venmo) | Braintree SLA (99.9%) |
| Checkout.com | REST API + Webhooks | Regional PSP (MENA, APAC) | Checkout.com SLA (99.95%) |

### 8.2 Infrastructure Dependencies

| Service | Provider | Purpose |
|---|---|---|
| Card Vault | Internal (PCI L1 segment) | PAN storage and tokenization |
| FX Rate Feed | Open Exchange Rates / XE Business | Live FX rates |
| AML Screening | ComplyAdvantage | Sanctions and PEP screening |
| Virtual Accounts | ClearBank / Modulr | IBAN assignment and bank transfers |
| Email Delivery | SendGrid / AWS SES | Transactional email notifications |
| SMS Delivery | Twilio | SMS notifications and OTP |
| Fraud ML | Internal ML Platform | Real-time fraud model inference |
| PagerDuty | PagerDuty | On-call alerting for P1/P2 incidents |

### 8.3 Internal Platform Dependencies

| Service | Dependency Type | Notes |
|---|---|---|
| Identity & Access Management | Synchronous (auth) | All API requests authenticated via IAM service |
| Notification Service | Asynchronous (event) | Consumes platform events for email/SMS dispatch |
| Audit Logging Service | Asynchronous (event) | Consumes all security events for immutable log storage |
| Data Warehouse | Asynchronous (CDC) | Receives CDC feed for reporting and analytics |

