# User Stories — Payment Orchestration and Wallet Platform

**Document Version:** 1.0  
**Status:** Approved  
**Last Updated:** 2025-07-14  
**Owner:** Product Management  
**Classification:** Internal — Confidential

---

## Table of Contents

1. [Merchant Stories](#1-merchant-stories)
2. [Customer / Cardholder Stories](#2-customer--cardholder-stories)
3. [Finance Manager Stories](#3-finance-manager-stories)
4. [Risk Analyst Stories](#4-risk-analyst-stories)
5. [Integration Engineer Stories](#5-integration-engineer-stories)
6. [Platform Admin Stories](#6-platform-admin-stories)
7. [Compliance Officer Stories](#7-compliance-officer-stories)
8. [Treasury Analyst Stories](#8-treasury-analyst-stories)
9. [Traceability Matrix](#9-traceability-matrix)

---

## 1. Merchant Stories

**US-001**: As a **Merchant**, I want to create a payment intent via the API with amount, currency, and customer details, so that I can initiate a card payment flow and receive a client secret to present the payment form on my front end.

**Acceptance Criteria:**
- Given a valid API key and a well-formed request body (amount, currency, payment_method, idempotency_key), when I call `POST /v1/payment-intents`, then I receive HTTP 201 with a payment intent object containing a unique `payment_intent_id`, `status: CREATED`, and a `client_secret`.
- Given a duplicate request with the same `Idempotency-Key` within 24 hours, when I call the endpoint again, then I receive HTTP 200, the original response payload, and `X-Idempotent-Replayed: true` in the response header.
- Given an invalid currency code (not ISO 4217), when I call the endpoint, then I receive HTTP 422 with error code `INVALID_CURRENCY` and a descriptive message.
- Given a missing `amount` field, when I call the endpoint, then I receive HTTP 400 with error code `MISSING_REQUIRED_FIELD` identifying the `amount` field.
- The payment intent creation p99 latency SHALL be under 500 ms under normal load.

---

**US-002**: As a **Merchant**, I want the platform to automatically route my payment to the optimal PSP based on card BIN, currency, and authorization rate history, so that I can maximize my authorization rate without managing PSP selection logic in my own application.

**US-003**: As a **Merchant**, I want automatic PSP failover when my primary PSP returns a timeout or hard error, so that my customers are not shown a failure screen due to a single PSP outage.

**US-004**: As a **Merchant**, I want to capture a partial amount against an authorized payment intent, so that I can handle split-shipment scenarios where I only charge for items that have shipped.

**US-005**: As a **Merchant**, I want to issue a full or partial refund against a captured payment, so that I can honor customer return requests programmatically without logging into each PSP's dashboard.

**US-006**: As a **Merchant**, I want to configure split payment rules on a payment intent so that when a payment is captured, funds are automatically distributed to my sub-merchants and my platform fee is retained.

**US-007**: As a **Merchant**, I want to subscribe to webhook events for my payment lifecycle (created, authorized, captured, failed, refunded), so that my system can react to payment state changes in near-real-time without polling.

**US-008**: As a **Merchant**, I want webhook deliveries to be retried with exponential backoff if my endpoint is temporarily unavailable, so that I do not miss critical payment events during brief downtime of my webhook receiver.

**US-009**: As a **Merchant**, I want to verify the authenticity of incoming webhook payloads using an HMAC signature, so that I can reject spoofed requests and protect my system from fraudulent callbacks.

**US-010**: As a **Merchant**, I want to view a PSP performance dashboard showing authorization rates, latency, and error rates per PSP, so that I can make informed decisions about PSP preference configuration.

**US-011**: As a **Merchant**, I want to download a settlement report for each payout batch showing gross volume, fees, refunds, and net settlement, so that I can reconcile my internal accounting records.

**US-012**: As a **Merchant**, I want to put a captured payment into escrow mode and release it only after a delivery confirmation event, so that I can build a two-sided marketplace with buyer protection.

---

## 2. Customer / Cardholder Stories

**US-013**: As a **Customer**, I want to save my card to my account once and use a token for future purchases, so that I do not have to re-enter my card details on every checkout.

**US-014**: As a **Customer**, I want to complete a 3DS2 authentication challenge when my bank requires it, so that my card payment is processed securely and I benefit from the liability shift to the issuer.

**Acceptance Criteria (US-005)**: As a **Customer**, I want to complete 3DS2 authentication, so that my payment is secured and my bank approves the transaction.

- Given a card that requires 3DS2 SCA, when I submit payment, then the platform presents a 3DS2 device data collection step before forwarding to the issuer ACS.
- Given a frictionless authentication result from the ACS, when the result is received, then the authorization proceeds without interrupting the customer flow.
- Given a challenge-required result from the ACS, when the result is received, then the customer is redirected to the issuer challenge window with a valid `threeDSSessionData` parameter.
- Given a successful challenge completion, when the ACS posts back to the platform, then the authorization request is sent to the PSP with the authentication data embedded.
- Given a failed authentication (cardholder abandons challenge), when the session times out, then the payment intent transitions to `AUTHENTICATION_FAILED` and the merchant receives a `payment_intent.authentication_failed` webhook.

---

**US-015**: As a **Customer**, I want to top up my digital wallet via a bank transfer using a virtual IBAN, so that I can hold a spendable balance without entering card details.

**US-016**: As a **Customer**, I want to transfer funds from my wallet to another user's wallet instantly, so that I can send money to friends or family within the same platform.

**US-017**: As a **Customer**, I want to see my full wallet transaction history with date, amount, and description filters, so that I can track my spending and identify any unrecognized transactions.

**US-018**: As a **Customer**, I want to request a refund status update via email notification when my refund is processed, so that I know when to expect the funds back in my account.

---

## 3. Finance Manager Stories

**US-019**: As a **Finance Manager**, I want to run a daily three-way reconciliation between the internal ledger, PSP settlement files, and bank statements, so that I can identify and investigate any discrepancies before closing the books.

**Acceptance Criteria (US-012):**
- Given a completed settlement batch, when I trigger reconciliation for the settlement date, then the engine matches all internal ledger entries against the PSP file and bank statement.
- Given a fully matched record, when reconciliation completes, then the record is marked `RECONCILED` and does not appear in the discrepancy report.
- Given an amount mismatch between the ledger and PSP file, when detected, then a break record is created with category `AMOUNT_MISMATCH`, affected amount, and linked transaction IDs.
- Given a break exceeding the configured tolerance, when detected, then a HIGH-severity alert is sent to the Finance Manager's email and the PagerDuty on-call channel.
- Given a manual adjustment is needed, when I submit a `POST /v1/ledger/adjustments` request above $10,000, then the system requires a second approver before the adjustment is posted.

---

**US-020**: As a **Finance Manager**, I want to view a revenue dashboard showing gross transaction volume, processing fees, and net revenue by currency and time period, so that I can prepare accurate monthly financial reports.

**US-021**: As a **Finance Manager**, I want to export the full ledger audit trail for a given date range in CSV format, so that I can provide auditors with a complete transaction history during annual financial reviews.

**US-022**: As a **Finance Manager**, I want to receive automated alerts when a reconciliation break is detected above the configured monetary threshold, so that I can investigate immediately rather than discovering discrepancies during the next day's close.

**US-023**: As a **Finance Manager**, I want to post manual ledger adjustments with mandatory reason codes and dual-approval for high-value entries, so that all manual interventions are controlled and auditable.

**US-024**: As a **Finance Manager**, I want to schedule payout runs on a weekly cadence for all sub-merchants, so that I do not need to manually initiate payouts and sub-merchants receive funds predictably.

---

## 4. Risk Analyst Stories

**US-025**: As a **Risk Analyst**, I want to view the manual review queue showing all transactions with a `REVIEW` fraud decision, ordered by risk score and SLA deadline, so that I can prioritize my review workload and avoid breaching review SLAs.

**Acceptance Criteria (US-018):**
- Given a transaction that scores in the REVIEW band, when the fraud scorer returns the decision, then the transaction is placed in the review queue within 1 second.
- Given the review queue UI, when I open a queue item, then I see: risk score, triggered rule IDs, cardholder history (last 30 days), device fingerprint, IP geolocation, and the full transaction payload.
- Given I approve a REVIEW item, when I confirm the decision with a reason, then the payment intent proceeds to authorization and the audit log records my identity, timestamp, and reason.
- Given I decline a REVIEW item, when I confirm, then the payment intent transitions to `DECLINED` with reason code `MANUAL_REVIEW_DECLINED` and the merchant receives a webhook.
- Given a queue item whose SLA deadline is within 1 hour, when the threshold is reached, then an automated email alert is sent to the analyst and their supervisor.

---

**US-026**: As a **Risk Analyst**, I want to create and modify velocity rules (e.g., max 5 failed attempts per card per hour) via the rules engine UI without requiring a code deployment, so that I can respond to emerging fraud patterns within minutes.

**US-027**: As a **Risk Analyst**, I want to create a fraud case linking multiple suspicious transactions, attach evidence, and track the case through to resolution, so that I can manage investigations systematically and report outcomes.

**US-028**: As a **Risk Analyst**, I want to view chargeback rate trends by merchant and reason code, so that I can identify merchants with systematic fraud problems and take proactive action before card scheme thresholds are breached.

**US-029**: As a **Risk Analyst**, I want to configure A/B test traffic splits between fraud ML model versions, so that I can evaluate the impact of a new model in production before promoting it to 100% traffic.

---

## 5. Integration Engineer Stories

**US-030**: As an **Integration Engineer**, I want to test my payment integration in an isolated sandbox environment using test card numbers that simulate specific PSP responses, so that I can validate my implementation without touching production systems.

**Acceptance Criteria (US-025):**
- Given a sandbox API key and a test card number `4000000000003220`, when I create and confirm a payment intent, then the sandbox returns a 3DS2 challenge flow response.
- Given a sandbox API key and a test card number `4000000000000002`, when I create and confirm a payment intent, then the sandbox returns a `card_declined` error with reason `insufficient_funds`.
- Given a configured PSP simulator failure rate of 50%, when I send payment intents in the sandbox, then approximately 50% fail with a simulated timeout and the routing engine triggers failover.
- Given my sandbox webhook endpoint is configured, when a test payment completes, then a signed `payment_intent.succeeded` webhook is delivered to my endpoint within 5 seconds.
- Given the sandbox webhook inspector UI, when I view sent events, then I see the full payload, delivery status, and HTTP response code for each attempt.

---

**US-031**: As an **Integration Engineer**, I want to configure PSP simulator responses in the sandbox (latency, failure rate, specific error codes) via an API, so that I can test my failover and error-handling logic without waiting for real PSP failures.

**US-032**: As an **Integration Engineer**, I want to replay any sandbox webhook event from the last 72 hours via an API call, so that I can re-test my webhook handler logic after fixing a bug without re-creating the triggering transaction.

**US-033**: As an **Integration Engineer**, I want to look up BIN data (card network, type, issuing country, 3DS2 support) for any 6- or 8-digit BIN via a REST API, so that I can adapt my checkout UI dynamically based on the card entered.

**US-034**: As an **Integration Engineer**, I want the API to support at least two concurrent major versions simultaneously, so that I have sufficient time to migrate to a new API version without being forced into an emergency upgrade.

**US-035**: As an **Integration Engineer**, I want to register and manage card tokens (create, list, delete) for a customer profile via the API, so that I can build a saved-payment-methods feature in my checkout without handling raw card data.

---

## 6. Platform Admin Stories

**US-036**: As a **Platform Admin**, I want to configure PSP routing rules per merchant — specifying preferred PSP, fallback PSPs, BIN-based routing, and currency routing — via the admin UI and API, so that I can optimize routing without modifying application code.

**US-037**: As a **Platform Admin**, I want to freeze a merchant's wallet with a reason code and actor audit trail when a compliance hold is required, so that funds are protected while a compliance investigation is underway.

**US-038**: As a **Platform Admin**, I want to view a real-time PSP health dashboard showing uptime, current error rate, and last failover event for each configured PSP, so that I can monitor infrastructure health and respond to degradation proactively.

**US-039**: As a **Platform Admin**, I want to manage merchant account configuration (API keys, webhook endpoints, PSP credentials, FX markup tier, payout schedule) from a single admin UI, so that I can onboard and configure merchants without requiring engineering involvement.

**US-040**: As a **Platform Admin**, I want to trigger a manual settlement batch run for a specific merchant and date, so that I can reprocess failed settlements without waiting for the next scheduled batch.

---

## 7. Compliance Officer Stories

**US-041**: As a **Compliance Officer**, I want to export all personal data associated with a customer ID in a structured JSON format within 72 hours of a GDPR data access request, so that I can fulfill data subject access requests within the legally required timeframe.

**Acceptance Criteria (US-032):**
- Given a verified GDPR data subject access request, when I call `POST /v1/compliance/gdpr/export` with the customer ID, then the system queues the export job and returns a `202 Accepted` with a `job_id`.
- Given the export job completes, when the file is ready, then a notification is sent to the requesting compliance officer's email and the file is available via a signed download URL for 48 hours.
- Given the exported data package, when I inspect it, then it includes all transactions, wallet balances, stored card tokens (masked PAN only), webhook delivery logs, and audit log entries linked to the customer ID.
- Given a GDPR Right to Erasure request, when I call `POST /v1/compliance/gdpr/delete` with the customer ID, then personal data fields (name, email, IP address, device fingerprint) are pseudonymized within 30 calendar days.
- Given financial records subject to 7-year retention, when erasure is processed, then transaction amounts, currencies, and reference IDs are retained but PII fields are overwritten with anonymized placeholders.

---

**US-042**: As a **Compliance Officer**, I want to download the full audit log for a specified date range in CSV and JSON formats, so that I can provide regulators and auditors with evidence of operational controls.

**US-043**: As a **Compliance Officer**, I want to review and approve AML screening matches before releasing a blocked payout, so that I can prevent payments to sanctioned entities and document my review decision.

**US-044**: As a **Compliance Officer**, I want to configure data residency settings per merchant to ensure EU merchant data is stored and processed only within EU-region infrastructure, so that the platform complies with GDPR data transfer restrictions.

**US-045**: As a **Compliance Officer**, I want to receive an automated alert when a new chargeback pushes a merchant's chargeback rate above the card scheme warning threshold, so that I can initiate a merchant review before scheme penalties are applied.

---

## 8. Treasury Analyst Stories

**US-046**: As a **Treasury Analyst**, I want to view real-time multi-currency wallet balances for all merchant wallets across all currencies, so that I can monitor liquidity positions and identify funding gaps before they become operational blockers.

**US-047**: As a **Treasury Analyst**, I want to lock an FX rate for 30 minutes when quoting a cross-currency conversion to a merchant, so that the merchant sees a firm rate and I am not exposed to FX rate slippage during the confirmation window.

**US-048**: As a **Treasury Analyst**, I want to configure FX markup rates per currency pair per merchant tier via the admin API, so that the platform earns appropriate FX revenue without manual intervention per transaction.

**US-049**: As a **Treasury Analyst**, I want to view an FX conversion report showing conversion volume, applied rates, markups earned, and comparison to mid-market rates, so that I can track FX revenue performance and validate that rate locks are functioning correctly.

**US-050**: As a **Treasury Analyst**, I want to initiate a wallet-to-wallet transfer between two currency sub-wallets with an atomic debit/credit and a recorded exchange rate, so that internal fund movements are fully traceable on the ledger.

---

## 9. Traceability Matrix

The following table maps each user story to its corresponding functional requirement(s).

| User Story | Title (abbreviated) | Functional Requirement(s) |
|---|---|---|
| US-001 | Create payment intent | FR-001, FR-005 |
| US-002 | Intelligent PSP routing | FR-002 |
| US-003 | PSP failover | FR-003 |
| US-004 | Partial capture | FR-004 |
| US-005 | Full / partial refund | FR-027 |
| US-006 | Split payment rules | FR-033, FR-034 |
| US-007 | Webhook subscriptions | FR-047 |
| US-008 | Webhook retry | FR-048 |
| US-009 | HMAC webhook signing | FR-049 |
| US-010 | PSP performance dashboard | FR-061 |
| US-011 | Settlement report download | FR-058 |
| US-012 | Escrow hold and release | FR-035 |
| US-013 | Card tokenization | FR-017 |
| US-014 | 3DS2 authentication | FR-007 |
| US-015 | Wallet top-up via bank transfer | FR-015 |
| US-016 | Wallet-to-wallet transfer | FR-011 |
| US-017 | Transaction history | FR-013 |
| US-018 | Refund email notification | FR-052 |
| US-019 | Three-way reconciliation | FR-041, FR-042, FR-043 |
| US-020 | Revenue dashboard | FR-057 |
| US-021 | Ledger audit trail export | FR-046 |
| US-022 | Reconciliation break alert | FR-044 |
| US-023 | Manual ledger adjustment | FR-045 |
| US-024 | Payout scheduling | FR-036 |
| US-025 | Manual review queue | FR-025 |
| US-026 | Velocity rules configuration | FR-022, FR-023 |
| US-027 | Fraud case management | FR-026 |
| US-028 | Chargeback rate trends | FR-032, FR-059 |
| US-029 | ML model A/B testing | FR-024 |
| US-030 | Sandbox testing with test cards | FR-053, FR-054 |
| US-031 | PSP simulator configuration | FR-055 |
| US-032 | Webhook event replay | FR-051, FR-056 |
| US-033 | BIN lookup API | FR-019 |
| US-034 | API versioning | NFR-014 |
| US-035 | Card token management | FR-017, FR-020 |
| US-036 | PSP routing configuration | FR-002 |
| US-037 | Wallet freeze | FR-012 |
| US-038 | PSP health dashboard | FR-061 |
| US-039 | Merchant account admin | FR-002, FR-036, FR-039 |
| US-040 | Manual settlement batch run | FR-041 |
| US-041 | GDPR data export | FR-065 |
| US-042 | Audit log download | FR-067 |
| US-043 | AML screening review | FR-066 |
| US-044 | Data residency configuration | FR-068 |
| US-045 | Chargeback threshold alert | FR-032, FR-059 |
| US-046 | Multi-currency wallet balances | FR-009, FR-013 |
| US-047 | FX rate locking | FR-040 |
| US-048 | FX markup configuration | FR-039 |
| US-049 | FX conversion report | FR-038, FR-062 |
| US-050 | Wallet-to-wallet transfer | FR-011, FR-014 |

