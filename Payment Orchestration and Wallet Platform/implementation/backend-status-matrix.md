# Backend Status Matrix — Payment Orchestration and Wallet Platform

This matrix is the implementation planning view for backend delivery. It defines the recommended build order, readiness gates, and evidence required before each domain is considered production-ready.

## 1. Status Definitions

| Status | Meaning |
|---|---|
| `FOUNDATION_READY` | Architecture, APIs, schemas, and runbooks are documented. Work may begin. |
| `BLOCKED_BY_DEPENDENCY` | Domain cannot start until prerequisite service or infrastructure is available. |
| `BUILD_READY` | Dependency gates are met and implementation can start in parallel with adjacent domains. |
| `INTEGRATION_READY` | Service contract tests, event contracts, and partner simulators are available. |
| `GO_LIVE_READY` | Operational controls, compliance evidence, and disaster recovery checks passed. |

## 2. Recommended Build Waves

| Wave | Scope | Reason |
|---|---|---|
| Wave 0 | Platform foundation, auth, gateway, observability, idempotency store, event bus | Required by every later service |
| Wave 1 | Payment orchestration, first PSP adapter, webhook ingest, refund basics | Enables online checkout MVP |
| Wave 2 | Ledger service, wallet service, merchant balance projections | Provides accounting truth and wallet movements |
| Wave 3 | Settlement service, reconciliation service, payout service | Unlocks finance close and merchant cash-out |
| Wave 4 | Additional PSP adapters, chargebacks, risk review queue, KYC and AML gates | Hardens production controls |
| Wave 5 | FX, rate locks, split payments, escrow, advanced reporting | Expands monetization and treasury features |

## 3. Domain Matrix

| Domain | Owning Services | Target Wave | Current Planning Status | Hard Dependencies | Entry Gate | Exit Evidence |
|---|---|---|---|---|---|---|
| API Gateway and Auth | Gateway, Auth | Wave 0 | FOUNDATION_READY | None | JWT, API key, RBAC model approved | Auth tests, rate limit tests, audit log verification |
| Idempotent command infrastructure | Gateway plugins, Redis, common command lib | Wave 0 | FOUNDATION_READY | Gateway and Redis | Request fingerprinting schema defined | Duplicate request replay test and in-flight collision test |
| Payment orchestration | Orchestration, first PSP adapter | Wave 1 | BUILD_READY | Wave 0 stack, vault token API, risk contract | Payment state machine, routing rules, attempt schema approved | Online auth tests, fallback tests, ambiguous outcome runbook |
| PSP adapters | Stripe, Adyen, Braintree, Checkout.com adapters | Wave 1 then Wave 4 | BUILD_READY | Orchestration framework | Adapter contract, sandbox simulator, timeout policy | Provider certification, webhook dedupe tests, failover drills |
| Ledger core | Ledger service, chart of accounts, journal API | Wave 2 | BUILD_READY | Wave 0 stack | Account model, invariants, posting recipes approved | Double-entry test suite, replay tests, finance sign-off |
| Wallet core | Wallet service, balance projections | Wave 2 | BLOCKED_BY_DEPENDENCY | Ledger core | Bucket model and freeze logic approved | Transfer atomicity tests, available-vs-reserved scenarios |
| Refunds and disputes | Refund service, dispute service, evidence store | Wave 4 | BLOCKED_BY_DEPENDENCY | Orchestration, ledger, webhook ingest | Refund and chargeback state machines approved | Partial refund tests, chargeback reserve tests, evidence SLA alerts |
| Settlement | Settlement service, fee aggregation | Wave 3 | BLOCKED_BY_DEPENDENCY | Ledger core, orchestration, object storage | Batch key design and provider file contracts approved | Stable rerun tests, fee accounting verification |
| Reconciliation | Reconciliation service, break queue | Wave 3 | BLOCKED_BY_DEPENDENCY | Settlement, ledger, bank file ingest | Match rules, break taxonomy, alert thresholds approved | Three-way sample data tests, finance attestation workflow |
| Payouts | Payout service, bank adapters | Wave 3 | BLOCKED_BY_DEPENDENCY | Wallet, ledger, KYC and AML hooks | Reserve model and bank dispatch contract approved | Duplicate payout prevention tests, bank return replay tests |
| Risk and fraud | Risk scoring, manual review, case management | Wave 4 | BUILD_READY | Wave 0 stack | Decision schema, velocity counters, ops queue defined | Sync scoring latency test, review workflow test, audit completeness |
| KYC and AML gating | Merchant config, compliance adapters | Wave 4 | BLOCKED_BY_DEPENDENCY | Payouts, wallet, operator console | Merchant onboarding state model approved | Sanctions hold tests, stale KYC payout block tests |
| FX and treasury | FX service, rate locks, conversion posting | Wave 5 | BLOCKED_BY_DEPENDENCY | Wallet, ledger | Rate source contracts and rounding policy approved | Expired rate lock tests, FX PnL validation |
| Reporting and exports | Reporting, GL export, audit export | Wave 5 | BLOCKED_BY_DEPENDENCY | Ledger, recon, payouts | Data mart schema approved | Report accuracy reconciliation, export retention checks |

## 4. Service Readiness Gates

| Gate | Required Before Marking `GO_LIVE_READY` |
|---|---|
| Contract gate | OpenAPI or protobuf contract frozen, versioned, and consumer-tested |
| Data gate | Schema migrations reviewed, rollback path documented, retention policy defined |
| Financial correctness gate | Posting recipes and invariants approved by finance engineering |
| Operations gate | Alerts, dashboards, runbooks, replay tooling, and on-call ownership defined |
| Security gate | IAM, secrets, key rotation, dependency scanning, and audit logging verified |
| Compliance gate | PCI boundary review complete for in-scope services, AML and KYC evidence paths approved |

## 5. End-to-End Milestones

| Milestone | Minimum domains complete | Acceptance evidence |
|---|---|---|
| Online payment MVP | Gateway, auth, orchestration, Stripe adapter, webhook ingest, refund basics | Successful auth, capture, refund, webhook replay in sandbox and staging |
| Wallet and ledger release | Ledger core, wallet core, payout reserve logic | Wallet credit, debit, transfer, freeze, and replay-safe ledger posting |
| Finance close release | Settlement, reconciliation, payout service, dispute reserve logic | Batch rerun determinism, three-way recon pass on seeded data, payout hold release checks |
| Compliance hardening release | PCI zone, KYC and AML gating, audit export | PCI boundary test, sanctions block test, immutable audit export sample |

## 6. Do Not Start Until

- No payout implementation before wallet reserve semantics and ledger posting recipes are approved.
- No multi-PSP fallback before ambiguous authorization handling is implemented.
- No chargeback auto-debit before merchant reserve model is live.
- No advanced reporting before reconciliation source-of-truth contracts are stable.
