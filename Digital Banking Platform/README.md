# Digital Banking Platform

A cloud-native, microservices-based neobank platform built for modern financial institutions and fintech startups. The platform provides a full-stack digital banking experience — from KYC-gated account opening and multi-currency wallets to virtual card issuance, cross-border SWIFT/SEPA payments, credit scoring, and real-time fraud detection — all delivered at carrier-grade 99.99% availability on a Kubernetes-native infrastructure. Every service is designed around domain-driven boundaries, event-sourced state, and immutable audit trails to satisfy PCI-DSS Level 1, GDPR, CCPA, BSA/AML, and Open Banking (PSD2) regulatory requirements out of the box.

---

## Documentation Structure

Project root artifact: [`traceability-matrix.md`](./traceability-matrix.md) provides cross-phase requirement-to-implementation linkage.


| File | Description |
|------|-------------|
| **requirements/** | |
| `requirements/requirements.md` | Full functional and non-functional requirements specification, stakeholder matrix, constraints, assumptions, and out-of-scope items |
| `requirements/user-stories.md` | Agile user stories in As-a/I-want/So-that format with Given/When/Then acceptance criteria, MoSCoW priority, and story points |
| **analysis/** | |
| `analysis/domain-model.md` | Core domain entities, aggregates, value objects, and domain events modelled in DDD; entity-relationship overview |
| `analysis/event-storming.md` | Event storming output: domain events, commands, aggregates, policies, and bounded context boundaries |
| `analysis/competitive-analysis.md` | Comparison with Revolut, N26, Monzo, Starling Bank across features, technology choices, regulatory coverage, and pricing |
| `analysis/data-flow.md` | End-to-end data flow diagrams for account opening, payment processing, card authorisation, and loan disbursement |
| **high-level-design/** | |
| `high-level-design/system-architecture.md` | Cloud-native microservices architecture overview, bounded contexts, API gateway topology, and inter-service communication patterns |
| `high-level-design/bounded-contexts.md` | Detailed bounded context map with context relationships (Shared Kernel, Customer-Supplier, Anticorruption Layer) |
| `high-level-design/technology-choices.md` | ADR-style justification for every major technology selection — database, messaging, service mesh, observability stack |
| `high-level-design/security-model.md` | Threat model, trust boundaries, defence-in-depth layers, encryption strategy, and secrets management |
| **detailed-design/** | |
| `detailed-design/account-service.md` | Account microservice: API contracts, data model, state machine, sequence diagrams, idempotency keys, and error handling |
| `detailed-design/card-service.md` | Card microservice: virtual/physical issuance flows, card lifecycle FSM, 3DS integration, PIN management, and BIN routing |
| `detailed-design/payment-service.md` | Payment microservice: ACH, SWIFT, SEPA, internal transfer flows, FX conversion, idempotency, and reconciliation |
| `detailed-design/kyc-service.md` | KYC microservice: document ingestion pipeline, OCR → liveness → database check → PEP/sanctions screening orchestration |
| `detailed-design/fraud-detection-service.md` | Real-time and batch fraud detection: rule engine, ML feature pipeline, velocity checks, device fingerprinting |
| `detailed-design/loan-service.md` | Loan origination microservice: application intake, credit bureau integration, scoring model, offer engine, disbursement, repayment |
| `detailed-design/notification-service.md` | Multi-channel notification service: push, SMS (Twilio), email (SendGrid), in-app, webhook delivery with at-least-once guarantees |
| `detailed-design/api-gateway.md` | API Gateway design: rate limiting, authentication (OAuth2/OIDC), request routing, circuit breakers, and developer portal |
| **infrastructure/** | |
| `infrastructure/deployment-architecture.md` | Multi-region Kubernetes deployment: EKS cluster topology, Istio service mesh, Helm chart structure, and GitOps pipeline |
| `infrastructure/database-design.md` | PostgreSQL schema designs per service, Cassandra time-series layout for transactions, Redis caching strategy, and migration patterns |
| `infrastructure/observability.md` | Three pillars of observability: distributed tracing (Jaeger), structured logging (ELK), and metrics/alerting (Prometheus/Grafana/PagerDuty) |
| `infrastructure/disaster-recovery.md` | Multi-region DR strategy: active-passive failover, RPO/RTO targets, runbook automation, and chaos engineering programme |
| `infrastructure/ci-cd-pipeline.md` | GitHub Actions pipeline: build, SAST/DAST, container scanning, Helm deployment, canary releases, and automated rollback |
| **implementation/** | |
| `implementation/coding-standards.md` | Language-specific coding standards (Java/Go/TypeScript), package structure conventions, error handling patterns, and logging contracts |
| `implementation/api-contracts.md` | OpenAPI 3.1 specifications for all public-facing and internal service APIs with example request/response payloads |
| `implementation/testing-strategy.md` | Testing pyramid: unit, integration, contract (Pact), E2E, performance (k6), chaos, and compliance testing strategy |
| `implementation/data-migration.md` | Data migration playbook for onboarding existing bank customers: transformation rules, rollback plan, and reconciliation checks |
| **edge-cases/** | |
| `edge-cases/payment-edge-cases.md` | Edge cases for payments: duplicate detection, partial SWIFT failures, SEPA R-transactions, FX rate expiry, and timeout handling |
| `edge-cases/fraud-edge-cases.md` | Fraud edge cases: mule account detection, SIM-swap attacks, card-not-present fraud, account takeover via social engineering |
| `edge-cases/kyc-edge-cases.md` | KYC edge cases: expired documents, name-change handling, politically exposed persons, stateless individuals, minor accounts |
| `edge-cases/system-edge-cases.md` | System-level edge cases: split-brain scenarios, idempotency failures, event out-of-order delivery, database failover mid-transaction |

---

## Key Features

- **Multi-Currency Accounts**
  - Hold balances in 30+ currencies (USD, EUR, GBP, JPY, AUD, CAD, SGD, AED, and more) within a single account
  - Real-time interbank FX rates via integration with Refinitiv/ECB feed with configurable spread markup
  - Instant in-app currency conversion with lock-in rates valid for 30 seconds
  - Separate IBAN/account number per currency pocket for receiving international wires

- **Domestic & International Transfers**
  - **ACH** — NACHA-compliant same-day ACH (SD-ACH) and next-day ACH origination and receipt; batch file processing; return code handling (R01–R85)
  - **SWIFT** — ISO 20022 MX message format (pacs.008, pacs.009) for international wires; correspondent banking network; GPI tracker integration for real-time status
  - **SEPA** — SCT (Credit Transfer) and SCT Inst (Instant) for EUR-zone payments; SEPA Direct Debit (SDD Core, SDD B2B); pain.001/pain.002/camt.054 message support
  - **Faster Payments (UK)** — direct CHAPS and Faster Payments connectivity for GBP transfers
  - Internal transfers between accounts settled in sub-second via ledger double-entry bookkeeping

- **Virtual & Physical Card Issuance**
  - Visa and Mastercard virtual card instant issuance via card processing network API (Marqeta/Galileo)
  - Physical card production with personalisation; shipped within 3–5 business days
  - Tokenisation (MDES/VTS) for Apple Pay, Google Pay, Samsung Pay support
  - Dynamic CVV (dCVV2) for virtual cards refreshing every 30 minutes
  - Real-time card controls: freeze/unfreeze, category-based spending blocks (e.g., gambling), geographic restrictions
  - 3-D Secure 2.2 (3DS2) integration with risk-based authentication

- **KYC/AML Onboarding**
  - Automated document verification: passport, national ID, driver's licence via Onfido/Jumio OCR pipeline
  - Biometric liveness detection to prevent spoofing attacks
  - Database cross-check against credit reference agencies (Experian, Equifax, TransUnion)
  - Real-time PEP (Politically Exposed Persons) and sanctions screening against OFAC SDN, UN, EU, HMT consolidated lists via Dow Jones/LexisNexis
  - Configurable risk-tier assignment (Standard, Enhanced, High Risk) driving ongoing monitoring frequency
  - Enhanced Due Diligence (EDD) workflow for high-risk customers including source-of-funds documentation
  - Re-KYC triggers on risk events, regulatory updates, and periodic refresh (annual for high-risk, triennial for standard)

- **Personal Loans & Credit Scoring**
  - End-to-end digital loan origination from application to disbursement in under 3 minutes
  - Integration with Experian and Equifax credit bureaus via REST and SFTP batch APIs
  - In-house credit scoring model combining bureau data, transaction behaviour, and alternative data signals
  - Loan offers with multiple tenure options (6–84 months) and risk-based pricing engine
  - Automated disbursement to linked account via internal transfer on e-sign completion
  - Dynamic repayment schedule with early repayment, partial prepayment, and payment holiday options

- **Real-Time Fraud Detection**
  - Sub-100ms fraud scoring on every card authorisation and payment initiation
  - Hybrid rule engine (velocity, pattern, geolocation anomaly) + ML gradient-boosting model
  - Device fingerprinting, behavioural biometrics, and IP reputation scoring
  - Card-not-present fraud controls: 3DS2 risk-based authentication step-up
  - Transaction monitoring for AML typologies: structuring, layering, round-tripping, mule account detection
  - Automatic card/account block with immediate customer notification on high-confidence fraud signals
  - Dispute management workflow with chargeback initiation via card network API

- **Compliance & Security**
  - PCI-DSS Level 1 certified: cardholder data isolated in dedicated CDE vault (HashiCorp Vault), network segmentation, quarterly ASV scans
  - GDPR & CCPA: data subject rights portal, consent management, right-to-erasure workflow for non-financial PII, DPA registers
  - ISO 27001 information security management system
  - SOC 2 Type II annual audit
  - TLS 1.3 in transit; AES-256-GCM at rest; field-level encryption for PAN and PII
  - mTLS for all internal service-to-service communication via Istio service mesh
  - RBAC with Zero Trust network model; no implicit trust between services

- **Platform & Operations**
  - 99.99% SLA (< 52 minutes unplanned downtime per year) backed by multi-region active-passive deployment
  - Horizontal auto-scaling to handle 1M+ concurrent sessions and 10,000 TPS peak payment throughput
  - Immutable audit log (append-only Apache Kafka topic + S3 Glacier archival) for all state-changing operations
  - Open Banking / PSD2 compliant REST APIs with OAuth2 PKCE for TPP access
  - Full observability: distributed tracing (Jaeger), structured logs (ELK), metrics & alerting (Prometheus + Grafana + PagerDuty)

---

## Technology Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | React 18, TypeScript 5, React Query, Redux Toolkit, Tailwind CSS, React Native (iOS/Android mobile app) |
| **Backend** | Java 21 (Spring Boot 3, Spring Security), Go 1.22 (high-throughput payment services), Node.js 20 (notification & webhook service) |
| **API Gateway** | Kong Gateway (OSS/Enterprise), OAuth2/OIDC via Keycloak, rate limiting, circuit breaker (Resilience4j) |
| **Data — OLTP** | PostgreSQL 16 (per-service databases, logical replication), PgBouncer (connection pooling) |
| **Data — Time-Series / Ledger** | Apache Cassandra 4.1 (transaction history, audit log — write-heavy, append-only) |
| **Data — Cache** | Redis Cluster 7.2 (session store, idempotency keys, FX rate cache, rate-limit counters) |
| **Data — Search** | Elasticsearch 8 (transaction search, customer search, AML case management) |
| **Data — Analytics** | Apache Spark, dbt, Snowflake (data warehouse for BI, credit scoring features, regulatory reporting) |
| **Messaging** | Apache Kafka 3.7 (event backbone — domain events, audit trail, fraud signals, notification triggers) |
| **Infrastructure** | AWS (primary): EKS, RDS Aurora PostgreSQL, ElastiCache, MSK (Kafka), S3, KMS, WAF, Shield Advanced |
| **Container Orchestration** | Kubernetes 1.30, Helm 3, Kustomize, Argo CD (GitOps), KEDA (event-driven autoscaling) |
| **Service Mesh** | Istio 1.22 (mTLS, traffic management, observability, circuit breaking) |
| **Security** | HashiCorp Vault (secrets, PKI, dynamic credentials), AWS KMS (envelope encryption), Falco (runtime threat detection) |
| **Observability** | Prometheus, Grafana, Jaeger (tracing), ELK Stack (Elasticsearch + Logstash + Kibana), PagerDuty |
| **CI/CD** | GitHub Actions, Trivy (container scanning), SonarQube (SAST), OWASP ZAP (DAST), ArgoCD |
| **Card Processing** | Marqeta (card issuing processor), Visa DPS / Mastercard MDES (network connectivity), PCIvault (PAN tokenisation) |
| **KYC/AML** | Onfido (document & biometric), Dow Jones Risk & Compliance (PEP/sanctions), Experian CrossCore |
| **Payments** | Finastra Universal Payments Hub (SWIFT/SEPA gateway), Moov ACH (NACHA processing), Stripe (fallback card acquiring) |

---

## Architecture Overview

The platform is decomposed into **10 core microservices**, each owning its bounded context, database, and event contract. Services communicate asynchronously over Apache Kafka for domain events (eventual consistency) and synchronously over gRPC (mTLS) for low-latency request-response within bounded context boundaries. External clients (web, mobile, partner TPPs) reach services exclusively through the Kong API Gateway, which handles authentication token validation, rate limiting, and routing.

```
[Mobile App / Web SPA]
         │  HTTPS / OAuth2 Bearer
         ▼
[Kong API Gateway]  ── rate limit, auth, routing, WAF
         │
    ┌────┴────────────────────────────────────┐
    │          gRPC / REST (internal)         │
    ▼          ▼          ▼          ▼        ▼
[Account]  [Card]  [Payment]  [KYC]  [Loan]  [Fraud]  [Notification]
    │          │          │          │        │
    └──────────┴──────────┴──────────┴────────┘
                         │ Kafka Domain Events
                         ▼
                 [Event Store / Audit Log]
                 [Notification Service]
                 [Analytics Pipeline]
```

A dedicated **Card Processing Domain** bridges the internal card service to external Visa/Mastercard networks and Marqeta's issuer API. The **Payment Domain** integrates with Finastra for SWIFT/SEPA and Moov for ACH, using outbox-pattern guaranteed delivery. All PAN data is handled exclusively within the PCI-scoped CDE network segment with hardware security module (HSM) backed encryption keys.

---

## Getting Started

- Review [`traceability-matrix.md`](./traceability-matrix.md) first to navigate requirement-to-implementation coverage across phases.
### Prerequisites

- Docker Desktop 4.28+ with 8 GB RAM allocated
- Docker Compose v2.24+
- Java 21 (GraalVM recommended for native builds)
- Go 1.22+
- Node.js 20 LTS
- kubectl 1.30+
- Helm 3.14+
- AWS CLI v2 (for cloud deployment)
- `make` (GNU Make 4.x)

### Local Development Setup

```bash
# 1. Clone the repository
git clone https://github.com/your-org/digital-banking-platform.git
cd digital-banking-platform

# 2. Copy and configure environment variables
cp .env.example .env
# Edit .env with your local secrets (never commit .env to git)

# 3. Start the local infrastructure stack (Postgres, Kafka, Redis, Keycloak, Kong)
docker-compose -f docker-compose.infra.yml up -d

# 4. Wait for infrastructure health
make wait-healthy

# 5. Apply database migrations for all services
make db-migrate-all

# 6. Seed reference data (currencies, country codes, BIN ranges)
make seed-reference-data

# 7. Start all microservices in development mode
docker-compose -f docker-compose.services.yml up -d

# 8. Verify all services are running
make health-check

# 9. Access developer portal
open http://localhost:8080/developer-portal

# 10. Access Grafana dashboards
open http://localhost:3000  # admin / admin (change on first login)

# 11. Run smoke tests against local environment
make test-smoke
```

### Key Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@localhost:5432/banking` |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka broker addresses | `localhost:9092` |
| `REDIS_URL` | Redis cluster endpoint | `redis://localhost:6379` |
| `KEYCLOAK_ISSUER_URI` | OIDC issuer for token validation | `http://localhost:8180/realms/banking` |
| `VAULT_ADDR` | HashiCorp Vault address | `http://localhost:8200` |
| `ONFIDO_API_KEY` | Onfido KYC API key | `sandbox_xxxx` |
| `MARQETA_BASE_URL` | Marqeta sandbox endpoint | `https://sandbox-api.marqeta.com/v3` |
| `ENCRYPTION_KEY_ARN` | AWS KMS key ARN for envelope encryption | `arn:aws:kms:us-east-1:123:key/abc` |

### Running Tests

```bash
# Unit tests
make test-unit

# Integration tests (requires running infra stack)
make test-integration

# Contract tests (Pact)
make test-contracts

# Performance tests (k6 — requires deployed environment)
make test-performance ENV=staging
```

---

## Documentation Status

- ✅ Traceability coverage is available via [`traceability-matrix.md`](./traceability-matrix.md).
| Document | Status | Last Updated | Owner |
|----------|--------|--------------|-------|
| `requirements/requirements.md` | ✅ Complete | 2025-01-15 | Product |
| `requirements/user-stories.md` | ✅ Complete | 2025-01-15 | Product |
| `analysis/domain-model.md` | 📝 Draft | 2025-01-10 | Architecture |
| `analysis/event-storming.md` | 📝 Draft | 2025-01-10 | Architecture |
| `analysis/competitive-analysis.md` | 📝 Draft | 2025-01-08 | Product |
| `analysis/data-flow.md` | 📝 Draft | 2025-01-10 | Architecture |
| `high-level-design/system-architecture.md` | 📝 Draft | 2025-01-12 | Architecture |
| `high-level-design/bounded-contexts.md` | 📝 Draft | 2025-01-12 | Architecture |
| `high-level-design/technology-choices.md` | 📝 Draft | 2025-01-09 | Architecture |
| `high-level-design/security-model.md` | ⬜ Pending | — | Security |
| `detailed-design/account-service.md` | ⬜ Pending | — | Engineering |
| `detailed-design/card-service.md` | ⬜ Pending | — | Engineering |
| `detailed-design/payment-service.md` | ⬜ Pending | — | Engineering |
| `detailed-design/kyc-service.md` | ⬜ Pending | — | Engineering |
| `detailed-design/fraud-detection-service.md` | ⬜ Pending | — | Engineering |
| `detailed-design/loan-service.md` | ⬜ Pending | — | Engineering |
| `detailed-design/notification-service.md` | ⬜ Pending | — | Engineering |
| `detailed-design/api-gateway.md` | ⬜ Pending | — | Engineering |
| `infrastructure/deployment-architecture.md` | ⬜ Pending | — | DevOps |
| `infrastructure/database-design.md` | ⬜ Pending | — | Engineering |
| `infrastructure/observability.md` | ⬜ Pending | — | DevOps |
| `infrastructure/disaster-recovery.md` | ⬜ Pending | — | DevOps |
| `infrastructure/ci-cd-pipeline.md` | ⬜ Pending | — | DevOps |
| `implementation/coding-standards.md` | ⬜ Pending | — | Engineering |
| `implementation/api-contracts.md` | ⬜ Pending | — | Engineering |
| `implementation/testing-strategy.md` | ⬜ Pending | — | Engineering |
| `implementation/data-migration.md` | ⬜ Pending | — | Engineering |
| `edge-cases/payment-edge-cases.md` | ⬜ Pending | — | Engineering |
| `edge-cases/fraud-edge-cases.md` | ⬜ Pending | — | Security |
| `edge-cases/kyc-edge-cases.md` | ⬜ Pending | — | Compliance |
| `edge-cases/system-edge-cases.md` | ⬜ Pending | — | Engineering |

**Legend:** ✅ Complete &nbsp;|&nbsp; 📝 Draft &nbsp;|&nbsp; ⬜ Pending

---

## Contributing

### Branch Strategy

- `main` — protected; reflects production-ready documentation and code
- `develop` — integration branch; all feature branches merge here first
- `feature/<ticket-id>-short-description` — for new features or documentation
- `fix/<ticket-id>-short-description` — for bug fixes
- `docs/<ticket-id>-short-description` — for documentation-only changes

### Contribution Workflow

1. Create an issue or pick an existing one from the backlog
2. Branch from `develop`: `git checkout -b feature/DBP-123-account-closure-flow`
3. Make changes, ensuring all tests pass: `make test-all`
4. Run linter and formatter: `make lint && make format`
5. Submit a pull request to `develop` with a filled-out PR template
6. Two approvals required (one from Architecture for design changes)
7. All CI checks must pass before merge
8. Documentation PRs require Compliance review for any changes affecting regulated functionality

### Code Standards Summary

- Follow the coding standards defined in `implementation/coding-standards.md`
- Every public API change requires an OpenAPI specification update
- New services must include a runbook in `infrastructure/runbooks/`
- Commit messages follow Conventional Commits: `feat(payment): add SEPA instant payment support`
- No secrets in code — use Vault or environment variables exclusively

### Security Reporting

Do **not** file public GitHub issues for security vulnerabilities. Report them via the private security advisory at `security@yourbank.io`. Critical vulnerabilities will be acknowledged within 24 hours and patched within 72 hours under our responsible disclosure policy.

---

*Digital Banking Platform — Internal Technical Documentation*
*Classification: CONFIDENTIAL — For Internal Use Only*
*© 2025 Your Bank Ltd. All rights reserved.*
