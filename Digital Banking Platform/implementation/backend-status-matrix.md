---
document-id: DBP-IMPL-026
version: 1.0.0
status: Approved
owner: Backend Engineering Lead
created: 2025-01-15
last-updated: 2025-01-15
---

# Backend Status Matrix — Digital Banking Platform

## Overview

This document provides a consolidated view of every REST API endpoint across all
backend services in the Digital Banking Platform. It tracks implementation
completeness, automated test coverage, and outstanding gaps. Engineering leads
are expected to update this matrix at the close of each sprint. It is also
consulted during pre-release gate reviews to confirm that coverage thresholds
are met before promotion to production.

**Status legend**

| Symbol | Meaning |
|---|---|
| ✅ Complete | Implemented, code-reviewed, and merged to `main` |
| 🔄 In Progress | Active development in a feature branch |
| 📋 Planned | Scoped and estimated; not yet started |

**Test coverage legend**

| Symbol | Meaning |
|---|---|
| ✅ | Automated test exists and is passing in CI |
| ❌ | Test absent or persistently failing |
| 🔄 | Test written but not yet consistently passing |

---

## AccountService

The `AccountService` is the authoritative service for customer account state.
It governs account creation (subject to KYC clearance), status transitions
(freeze, unfreeze, close), balance enquiries, transaction history retrieval,
monthly statement generation, beneficiary management, and standing order
scheduling. Accounts are versioned with an optimistic lock (`version` column)
to prevent concurrent modification anomalies.

| Endpoint | Method | Path | Status | Unit Test | Integration Test | Notes |
|---|---|---|---|---|---|---|
| Create account | POST | `/api/v1/accounts` | ✅ Complete | ✅ | ✅ | KYC status APPROVED required; idempotency key mandatory |
| Get account | GET | `/api/v1/accounts/{id}` | ✅ Complete | ✅ | ✅ | Ownership enforced via JWT `sub` claim |
| List accounts | GET | `/api/v1/accounts` | ✅ Complete | ✅ | ✅ | Scoped to authenticated customer; paginated (cursor) |
| Update account status | PUT | `/api/v1/accounts/{id}/status` | ✅ Complete | ✅ | ✅ | Valid transitions: ACTIVE→FROZEN, FROZEN→ACTIVE, ACTIVE→CLOSED |
| Get balance | GET | `/api/v1/accounts/{id}/balance` | ✅ Complete | ✅ | ✅ | Returns available balance and ledger balance; cached 5 s |
| List transactions | GET | `/api/v1/accounts/{id}/transactions` | ✅ Complete | ✅ | ✅ | Offset and cursor pagination; date-range and type filters |
| Get statement | GET | `/api/v1/accounts/{id}/statements/{year}/{month}` | ✅ Complete | ✅ | ✅ | PDF + JSON; generated async, status polled separately |
| Add beneficiary | POST | `/api/v1/accounts/{id}/beneficiaries` | ✅ Complete | ✅ | ✅ | SCA required; duplicate IBAN rejected with 409 |
| List beneficiaries | GET | `/api/v1/accounts/{id}/beneficiaries` | ✅ Complete | ✅ | ✅ | Account numbers masked to last 4 digits |
| Delete beneficiary | DELETE | `/api/v1/accounts/{id}/beneficiaries/{beneficiaryId}` | ✅ Complete | ✅ | ✅ | Soft-delete; record retained for 7-year audit window |
| Create standing order | POST | `/api/v1/accounts/{id}/standing-orders` | 🔄 In Progress | ✅ | 🔄 | Recurrence engine integration pending; blocker: Sprint 14 |
| List standing orders | GET | `/api/v1/accounts/{id}/standing-orders` | 🔄 In Progress | ✅ | ❌ | Blocked on standing-order persistence model finalisation |

---

## TransactionService

The `TransactionService` handles the full payment lifecycle: initiation across
domestic and international rails (ACH, SWIFT, Faster Payments), real-time
status tracking, settlement webhook ingestion, dispute management, and
financial reporting exports. It enforces idempotency on every mutation and
integrates synchronously with FraudService before fund reservation.

| Endpoint | Method | Path | Status | Unit Test | Integration Test | Notes |
|---|---|---|---|---|---|---|
| Initiate transfer | POST | `/api/v1/transactions/transfer` | ✅ Complete | ✅ | ✅ | `X-Idempotency-Key` required; fraud check synchronous P99 < 200 ms |
| Get transaction | GET | `/api/v1/transactions/{id}` | ✅ Complete | ✅ | ✅ | Ownership enforced; includes full status timeline |
| List transactions | GET | `/api/v1/transactions` | ✅ Complete | ✅ | ✅ | Filter by status, dateRange, counterparty, amount range |
| Cancel transaction | POST | `/api/v1/transactions/{id}/cancel` | ✅ Complete | ✅ | ✅ | Cancellable only in INITIATED or PROCESSING state |
| Raise dispute | POST | `/api/v1/transactions/{id}/dispute` | ✅ Complete | ✅ | ✅ | Creates dispute case; routes to manual review queue |
| Export CSV | GET | `/api/v1/transactions/export` | 🔄 In Progress | ✅ | ❌ | Async job; max 50 000 rows; delivery via signed S3 URL |
| Settlement webhook | POST | `/api/v1/internal/transactions/settle` | ✅ Complete | ✅ | ✅ | HMAC-SHA256 signed; ingests rail settlement notifications |
| Spending summary | GET | `/api/v1/transactions/summary` | 📋 Planned | ❌ | ❌ | Requires ML categorisation service; scheduled Sprint 15 |

---

## CardService

The `CardService` manages virtual and physical payment card issuance,
real-time spending controls, and the integration with the VISA network
authorisation and settlement APIs. It also exposes the EMV 3-D Secure 2.2
enrollment and status endpoints required for PSD2 SCA compliance for
card-not-present transactions.

| Endpoint | Method | Path | Status | Unit Test | Integration Test | Notes |
|---|---|---|---|---|---|---|
| Issue card | POST | `/api/v1/cards` | ✅ Complete | ✅ | ✅ | Virtual: immediate; physical: 3–5 business days dispatch |
| Get card | GET | `/api/v1/cards/{id}` | ✅ Complete | ✅ | ✅ | PAN masked to BIN + last 4; tokenised PAN in separate field |
| Update card status | PUT | `/api/v1/cards/{id}/status` | ✅ Complete | ✅ | ✅ | ACTIVE↔FROZEN reversible; CANCELLED is terminal |
| Update spending limits | PUT | `/api/v1/cards/{id}/limits` | ✅ Complete | ✅ | ✅ | Daily, monthly, per-transaction, and MCC-category limits |
| List card transactions | GET | `/api/v1/cards/{id}/transactions` | ✅ Complete | ✅ | ✅ | Authorisations and cleared transactions shown separately |
| Initiate PIN change | POST | `/api/v1/cards/{id}/pin-change` | 🔄 In Progress | ✅ | 🔄 | OTP-verified; HSM-based PIN block; sandbox being provisioned |
| Replace card | POST | `/api/v1/cards/{id}/replace` | 🔄 In Progress | ✅ | ❌ | Lost/stolen reasons; previous card cancelled atomically |
| Network authorise | POST | `/api/v1/internal/cards/authorize` | ✅ Complete | ✅ | ✅ | Real-time; < 200 ms SLA; ISO 8583 message mapped to REST |
| Settle authorisation | POST | `/api/v1/internal/cards/settle-auth` | ✅ Complete | ✅ | ✅ | Matches auth by ARQC; posts to account ledger |
| 3DS enrollment status | GET | `/api/v1/cards/{id}/3ds-status` | 📋 Planned | ❌ | ❌ | EMV 3DS 2.2 required by VISA network rules Q3 2025 |

---

## KYCService

The `KYCService` orchestrates customer identity verification via Onfido,
managing document capture, biometric liveness checks, PEP and sanctions
screening, and back-office decisioning workflows. It supports both automated
real-time decisions (< 3 minutes) and manual review queues for complex cases.

| Endpoint | Method | Path | Status | Unit Test | Integration Test | Notes |
|---|---|---|---|---|---|---|
| Initiate KYC | POST | `/api/v1/kyc/initiate` | ✅ Complete | ✅ | ✅ | Returns Onfido SDK token for mobile onboarding flow |
| Upload documents | POST | `/api/v1/kyc/{id}/documents` | ✅ Complete | ✅ | ✅ | Multipart; max 10 MB; virus-scanned before S3 storage |
| Get KYC status | GET | `/api/v1/kyc/{id}/status` | ✅ Complete | ✅ | ✅ | Polled by mobile app; SSE alternative at `/kyc/{id}/stream` |
| Submit for review | POST | `/api/v1/kyc/{id}/submit` | ✅ Complete | ✅ | ✅ | Dispatches to Onfido; fully idempotent |
| Admin decision | PUT | `/api/v1/kyc/{id}/decision` | ✅ Complete | ✅ | ✅ | APPROVED/REJECTED/REFER; 4-eyes approval enforced |
| Provider webhook | POST | `/api/v1/internal/kyc/webhook` | ✅ Complete | ✅ | ✅ | HMAC-SHA256 verified; maps Onfido outcome to platform status |

---

## LoanService

The `LoanService` handles consumer loan applications, credit bureau
underwriting, conditional offer generation, disbursement, and scheduled
repayment tracking. All loan state transitions are recorded in an immutable
audit log for SOX compliance.

| Endpoint | Method | Path | Status | Unit Test | Integration Test | Notes |
|---|---|---|---|---|---|---|
| Submit application | POST | `/api/v1/loans/applications` | ✅ Complete | ✅ | ✅ | Triggers Experian credit bureau check asynchronously |
| Get application | GET | `/api/v1/loans/applications/{id}` | ✅ Complete | ✅ | ✅ | Includes underwriting rationale and decision factors |
| Accept offer | POST | `/api/v1/loans/applications/{id}/accept` | ✅ Complete | ✅ | ✅ | SCA required; disbursement to nominated account initiated |
| Decline offer | POST | `/api/v1/loans/applications/{id}/decline` | ✅ Complete | ✅ | ✅ | Decline reason logged; credit bureau notified |
| Get loan | GET | `/api/v1/loans/{id}` | ✅ Complete | ✅ | ✅ | Outstanding balance, next payment date, interest accrued |
| Make repayment | POST | `/api/v1/loans/{id}/repayment` | 🔄 In Progress | ✅ | 🔄 | Early repayment fee calculation logic under legal review |
| Repayment schedule | GET | `/api/v1/loans/{id}/schedule` | ✅ Complete | ✅ | ✅ | Full amortisation table; supports interest-only period |
| List active loans | GET | `/api/v1/loans` | ✅ Complete | ✅ | ✅ | Scoped to customer; filter by status and product type |

---

## FraudService

The `FraudService` provides synchronous real-time fraud risk scoring,
asynchronous alert lifecycle management, and rules administration for the
compliance team. It combines ML model scoring with a deterministic rules engine
and maintains a feedback loop from analyst decisions back to model training.

| Endpoint | Method | Path | Status | Unit Test | Integration Test | Notes |
|---|---|---|---|---|---|---|
| Assess transaction | POST | `/api/v1/internal/fraud/assess` | ✅ Complete | ✅ | ✅ | P99 < 50 ms combined ML + rules score; internal only |
| List fraud alerts | GET | `/api/v1/fraud/alerts` | ✅ Complete | ✅ | ✅ | Analyst-facing; filter by status, severity, date range |
| Resolve alert | PUT | `/api/v1/fraud/alerts/{id}/resolve` | ✅ Complete | ✅ | ✅ | Requires `FRAUD_ANALYST` role; resolution reason required |
| List active rules | GET | `/api/v1/fraud/rules` | 🔄 In Progress | ✅ | ❌ | Rules admin UI integration in progress; API contract stable |

---

## NotificationService

The `NotificationService` routes transactional notifications across push
(Firebase), SMS (Twilio), and email (SES) channels. Channel selection is
governed by per-customer preferences and message priority. The customer inbox
provides an in-app persistent notification log.

| Endpoint | Method | Path | Status | Unit Test | Integration Test | Notes |
|---|---|---|---|---|---|---|
| Send notification | POST | `/api/v1/internal/notifications/send` | ✅ Complete | ✅ | ✅ | Internal service call only; channel routing from preferences |
| Customer inbox | GET | `/api/v1/notifications` | ✅ Complete | ✅ | ✅ | Cursor-paginated; filter by read/unread, type, date |
| Mark as read | PUT | `/api/v1/notifications/{id}/read` | ✅ Complete | ✅ | ✅ | Bulk mark-read via array in request body also supported |
| Get preferences | GET | `/api/v1/notifications/preferences` | 📋 Planned | ❌ | ❌ | Per-channel, per-event-type preferences; Sprint 15 |

---

## Coverage Summary

| Service | Total Endpoints | ✅ Complete | 🔄 In Progress | 📋 Planned | Unit Test % | Integration Test % |
|---|---|---|---|---|---|---|
| AccountService | 12 | 10 | 2 | 0 | 100% | 83% |
| TransactionService | 8 | 6 | 1 | 1 | 88% | 63% |
| CardService | 10 | 6 | 2 | 2 | 90% | 70% |
| KYCService | 6 | 6 | 0 | 0 | 100% | 100% |
| LoanService | 8 | 7 | 1 | 0 | 100% | 88% |
| FraudService | 4 | 3 | 1 | 0 | 100% | 75% |
| NotificationService | 4 | 3 | 0 | 1 | 75% | 75% |
| **Total** | **52** | **41 (79%)** | **7 (13%)** | **4 (8%)** | **93%** | **79%** |

---

## Known Gaps and Risks

The following gaps require resolution before the platform can be declared
production-ready. Each item is tracked in the engineering backlog with an
associated risk rating.

| Gap | Service | Risk | Target Sprint | Mitigation |
|---|---|---|---|---|
| Spending summary requires ML categorisation | TransactionService | Medium | Sprint 15 | Manual category labels shipped as fallback |
| Standing order recurrence engine not integrated | AccountService | High | Sprint 14 | Cron-based workaround active; must not go to GA |
| CSV export lacks integration test | TransactionService | Medium | Sprint 13 | Manual QA sign-off accepted for current release |
| EMV 3-D Secure 2.2 enrollment missing | CardService | High | Sprint 14 | VISA network rules mandate Q3 2025; exemption requested |
| Notification preferences endpoint absent | NotificationService | Low | Sprint 15 | Mobile app settings manage preferences as interim |
| FraudService rules admin has no integration test | FraudService | Medium | Sprint 13 | Admin UI not in customer-critical path |
| PIN change HSM sandbox not provisioned | CardService | Medium | Sprint 13 | Infrastructure team tracking; no customer impact yet |
| Early repayment fee logic pending legal review | LoanService | High | Sprint 14 | Early repayment blocked in production until resolved |

---

## Authentication and Authorisation Requirements

Every endpoint enforces authentication and authorisation as follows:

| Category | Authentication | Authorisation | Notes |
|---|---|---|---|
| Customer endpoints | Bearer JWT (access token) | JWT `sub` must match resource owner | Tokens issued by Identity Service; 15-minute expiry |
| Admin/analyst endpoints | Bearer JWT | Role claim: `ADMIN`, `FRAUD_ANALYST`, `COMPLIANCE_OFFICER` | Accessed via back-office portal only |
| Internal service endpoints | mTLS + service JWT | Service identity in JWT `client_id` claim | Not reachable from public internet; VPC-internal only |
| Open Banking endpoints | OAuth2 Bearer (TPP token) | Consent scope validated per PSD2 | 90-day consent window; SCA required for initiation |

---

## Error Response Standards

All endpoints return errors conforming to RFC 7807 (Problem Details for HTTP
APIs). The error response body contains `type`, `title`, `status`, `detail`,
and a platform-specific `errorCode` field used for client-side localisation
and support case triage.

| HTTP Status | When Used | Example `errorCode` |
|---|---|---|
| 400 Bad Request | Validation failure, malformed request | `INVALID_AMOUNT`, `MISSING_CURRENCY` |
| 401 Unauthorized | Missing or expired token | `TOKEN_EXPIRED`, `TOKEN_INVALID` |
| 403 Forbidden | Insufficient permissions or resource ownership | `ACCESS_DENIED`, `INSUFFICIENT_SCOPE` |
| 404 Not Found | Resource does not exist | `ACCOUNT_NOT_FOUND`, `CARD_NOT_FOUND` |
| 409 Conflict | Duplicate resource or invalid state transition | `DUPLICATE_IDEMPOTENCY_KEY`, `INVALID_STATE_TRANSITION` |
| 422 Unprocessable Entity | Business rule violation | `INSUFFICIENT_FUNDS`, `KYC_NOT_APPROVED` |
| 429 Too Many Requests | Rate limit exceeded | `RATE_LIMIT_EXCEEDED` |
| 500 Internal Server Error | Unexpected server error | `INTERNAL_ERROR` |
| 503 Service Unavailable | Dependency unavailable | `DEPENDENCY_UNAVAILABLE` |

---

## Non-Functional Endpoint Checklist

Every service must expose the following non-functional endpoints prior to
production promotion. These are consumed by Kubernetes liveness and readiness
probes, Prometheus scraping, and the API gateway health router.

| Service | `/health` liveness | `/ready` readiness | `/metrics` Prometheus | Readiness Checks |
|---|---|---|---|---|
| AccountService | ✅ | ✅ | ✅ | DB connectivity, Redis reachability |
| TransactionService | ✅ | ✅ | ✅ | DB connectivity, Kafka producer, FraudService reachability |
| CardService | ✅ | ✅ | ✅ | DB connectivity, VISA gateway reachability |
| KYCService | ✅ | ✅ | ✅ | DB connectivity, Onfido API reachability |
| LoanService | ✅ | ✅ | ✅ | DB connectivity, credit bureau reachability |
| FraudService | ✅ | ✅ | ✅ | DB connectivity, ML model loaded and responsive |
| NotificationService | ✅ | ✅ | ✅ | Kafka consumer lag < threshold, Twilio reachability |

All `/health` endpoints return `HTTP 200 {"status":"UP"}` when the service
process is alive. All `/ready` endpoints return `HTTP 503` when a critical
dependency is unreachable, preventing traffic routing to the pod during cold
start or dependency degradation. All `/metrics` endpoints expose
Prometheus-format metrics including JVM heap usage, HTTP request latency
histograms (p50, p95, p99), active connection pool gauges, and custom business
counters (transactions per second, authorisations per second, fraud alerts
raised per minute).

The `/ready` check is deliberately stricter than `/health`. A pod that is alive
but cannot reach its database should not receive traffic; returning 503 on
`/ready` ensures Kubernetes removes it from the service endpoint set within one
probe cycle (configured at 10-second intervals with a 3-failure threshold).
