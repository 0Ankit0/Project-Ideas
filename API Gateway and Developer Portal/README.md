# API Gateway and Developer Portal

> One platform to publish, secure, rate-limit, transform, and monetize your APIs — with a first-class developer experience.

## Overview

The **API Gateway and Developer Portal** is a production-grade platform that sits at the entry point of every API call your organisation exposes. It handles traffic routing, authentication, rate limiting, request/response transformation, and metric collection — while the companion Developer Portal gives external and internal developers a self-service experience: interactive docs, API key management, subscription plans, and usage analytics.

Built on Node.js 20 + Fastify for raw throughput, Next.js 14 (App Router) for the portal, PostgreSQL 15 + Redis 7 for persistence and caching, and deployed on AWS ECS Fargate behind CloudFront and WAF, the system is designed to sustain 10 000+ RPS with p99 latency under 50 ms.

---

## Documentation Structure

Project root artifact: [`traceability-matrix.md`](./traceability-matrix.md) provides cross-phase requirement-to-implementation linkage.

```text
API Gateway and Developer Portal/
├── README.md                                  ← This file — project overview and navigation
├── traceability-matrix.md                     ← Cross-phase requirement-to-implementation linkage
│
├── requirements/
│   ├── requirements-document.md              ← Functional and non-functional requirements
│   └── user-stories.md                       ← User stories with acceptance criteria
│
├── analysis/
│   ├── use-case-diagram.md                   ← Actor/use-case relationships
│   ├── use-case-descriptions.md              ← Detailed use case specifications
│   ├── system-context-diagram.md             ← System boundary and external actors
│   ├── activity-diagram.md                   ← Key workflow activity flows
│   ├── bpmn-swimlane-diagram.md              ← BPMN process flows with swimlanes
│   ├── data-dictionary.md                    ← Canonical data entities and attributes
│   ├── business-rules.md                     ← Enforceable business rules and exceptions
│   └── event-catalog.md                      ← Domain events, contracts, and SLOs
│
├── high-level-design/
│   ├── architecture-diagram.md               ← System architecture overview
│   ├── c4-context-container.md               ← C4 context and container diagrams
│   ├── data-flow-diagram.md                  ← Data flow across components
│   ├── domain-model.md                       ← Domain entities and relationships
│   └── system-sequence-diagram.md            ← System-level sequence flows
│
├── detailed-design/
│   ├── api-design.md                         ← REST/gRPC API contracts
│   ├── c4-component.md                       ← C4 component-level design
│   ├── class-diagram.md                      ← Class and type diagrams
│   ├── component-diagram.md                  ← Component interaction diagram
│   ├── erd-database-schema.md                ← Database ERD and schema definitions
│   ├── sequence-diagram.md                   ← Detailed sequence diagrams
│   └── state-machine-diagram.md              ← State machine for key entities
│
├── infrastructure/
│   ├── cloud-architecture.md                 ← Cloud provider architecture
│   ├── deployment-diagram.md                 ← Deployment topology
│   └── network-infrastructure.md             ← Network layout and security groups
│
├── implementation/
│   ├── c4-code-diagram.md                    ← C4 code-level diagrams
│   ├── code-guidelines.md                    ← Coding standards and conventions
│   └── implementation-playbook.md            ← Step-by-step build and deploy playbook
│
└── edge-cases/
    ├── README.md                             ← Edge case registry and classification
    ├── routing-and-traffic.md               ← Routing failures and traffic anomalies
    ├── authentication-and-keys.md           ← Auth failures and key lifecycle edge cases
    ├── rate-limiting-and-quotas.md          ← Rate limit and quota enforcement edge cases
    ├── developer-portal.md                  ← Developer portal failure modes
    ├── api-and-ui.md                        ← API and UI layer resilience edge cases
    ├── security-and-compliance.md           ← Security threats and compliance violations
    └── operations.md                        ← Operational runbooks and incident response
```

---

## Key Features

- **Gateway Core** — High-throughput reverse proxy built on Fastify with a plugin-based extensibility model, supporting HTTP/1.1, HTTP/2, and WebSocket proxying with zero-downtime hot-reload of route configuration from PostgreSQL.
- **Authentication & Authorization** — Multi-scheme auth layer supporting HMAC-SHA256 API keys, OAuth 2.0 (authorisation code, client credentials, PKCE), and JWT validation with configurable JWKS endpoint caching and multi-issuer support.
- **Rate Limiting & Quotas** — Token-bucket and sliding-window algorithms backed by Redis 7; per-key, per-IP, per-plan, and per-endpoint limits; soft and hard quota enforcement with configurable overage behaviour and automated 80%-threshold warnings.
- **Request/Response Transformation** — Header injection/removal, body rewriting (JSON ↔ XML ↔ form-data via JSONata), URL rewriting, query-parameter mapping, and conditional transformation pipelines defined as JSON policy documents.
- **Developer Portal** — Next.js 14 App Router portal with interactive OpenAPI 3.1 / Swagger UI, self-service API key generation, subscription management, usage dashboards, and full onboarding tutorial flow.
- **Analytics & Observability** — OpenTelemetry-based distributed tracing via Jaeger, Prometheus metrics scraped by Grafana (15-second interval), structured JSON logs, and real-time per-key/per-endpoint drill-down dashboards.
- **Subscription Plans** — Flexible plan tiers (Free, Basic, Pro, Enterprise) with per-plan rate limits, quota budgets, feature flags, trial periods, and Stripe-compatible billing webhooks; self-service upgrade/downgrade from the portal.
- **Webhook Management** — Developer-configurable outbound webhooks with HMAC-SHA256 signatures, BullMQ-backed at-least-once delivery, exponential backoff retry (up to 5 attempts), dead-letter queue, and delivery log UI.
- **API Versioning** — Semantic versioning with header-based (`API-Version`) and URL-path strategies; automated `Deprecation` and `Sunset` response headers; sunset date enforcement returning `HTTP 410 Gone`; migration-guide link injection.
- **Admin Console** — Operator-facing dashboard for multi-tenant management, API catalogue publishing workflow (draft → review → active), plan configuration, traffic policy editor, audit log viewer, and system health monitoring.

---

## Primary Roles

| Role | Description | Key Capabilities |
|------|-------------|-----------------|
| **API Provider** | Organisation or team that publishes APIs through the gateway | Publish OpenAPI specs, configure routing & versioning, set rate-limit and transformation policies, view per-API analytics, manage webhook event types, define subscription plan eligibility |
| **Developer** | External or internal consumer who integrates with published APIs | Self-service registration, API key generation and rotation, browse and search the API catalogue, subscribe to plans, view personal usage & quota dashboards, register webhooks, access interactive docs |
| **Admin** | Platform operator responsible for the gateway infrastructure | Manage tenant organisations and user roles, configure global policies, approve API publishing requests, enforce compliance rules, review immutable audit logs, operate the admin console, manage infrastructure settings |
| **Analyst** | Business or technical stakeholder who analyses platform traffic | Access aggregated and per-key metrics, generate and export usage reports, view SLA compliance charts, compare consumption across plan tiers, identify error-rate trends and anomaly patterns |

---

## Getting Started

1. **Clone the repository**

   ```bash
   git clone https://github.com/your-org/api-gateway-portal.git
   cd api-gateway-portal
   ```

2. **Install dependencies**

   ```bash
   # Gateway runtime (Node.js 20 + Fastify)
   cd gateway && npm ci

   # Developer Portal (Next.js 14)
   cd ../portal && npm ci
   ```

3. **Configure environment**

   ```bash
   cp gateway/.env.example gateway/.env
   cp portal/.env.example portal/.env
   # Edit both files — set DB_URL, REDIS_URL, JWT_SECRET, JWKS_ENDPOINT,
   # STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, SENDGRID_API_KEY, etc.
   ```

4. **Start the gateway**

   ```bash
   cd gateway
   npm run dev        # development mode with hot-reload on :4000
   # — or —
   npm run build && npm run start   # production build
   ```

5. **Start the developer portal**

   ```bash
   cd portal
   npm run dev        # Next.js dev server on :3000
   # — or —
   npm run build && npm run start   # production build
   ```

6. **Run smoke tests**

   ```bash
   # From the repository root
   npm run test:smoke
   # Verifies: gateway health endpoints, API key auth flow, rate-limit headers,
   # OAuth token validation, portal page loads, and admin console reachability.
   ```

7. **Access the admin console**

   Open [http://localhost:3000/admin](http://localhost:3000/admin) in your browser.
   Default dev credentials: `admin@example.com` / `changeme123`

   > ⚠️ **Change the default password immediately.** The `ADMIN_INITIAL_PASSWORD` env var controls the seed value; rotate it before any shared environment deployment.

---

## Documentation Status

| # | File | Status |
|---|------|--------|
| 1 | `README.md` | ✅ |
| 2 | `requirements/requirements-document.md` | ✅ |
| 3 | `requirements/user-stories.md` | ✅ |
| 4 | `design/system-architecture.md` | ✅ |
| 5 | `design/database-schema.md` | ✅ |
| 6 | `design/api-design.md` | ✅ |
| 7 | `design/security-model.md` | ✅ |
| 8 | `gateway/overview.md` | ✅ |
| 9 | `gateway/plugin-architecture.md` | ✅ |
| 10 | `gateway/routing.md` | ✅ |
| 11 | `gateway/middleware.md` | ✅ |
| 12 | `auth/api-key-management.md` | ✅ |
| 13 | `auth/oauth2-flows.md` | ✅ |
| 14 | `auth/jwt-validation.md` | ✅ |
| 15 | `rate-limiting/rate-limiting-design.md` | ✅ |
| 16 | `rate-limiting/quota-management.md` | ✅ |
| 17 | `rate-limiting/throttling-policies.md` | ✅ |
| 18 | `transformation/request-transformation.md` | ✅ |
| 19 | `transformation/response-transformation.md` | ✅ |
| 20 | `transformation/protocol-translation.md` | ✅ |
| 21 | `developer-portal/portal-overview.md` | ✅ |
| 22 | `developer-portal/api-catalog.md` | ✅ |
| 23 | `developer-portal/onboarding-flow.md` | ✅ |
| 24 | `developer-portal/developer-dashboard.md` | ✅ |
| 25 | `analytics/metrics-and-monitoring.md` | ✅ |
| 26 | `analytics/distributed-tracing.md` | ✅ |
| 27 | `analytics/reporting.md` | ✅ |
| 28 | `subscription-plans/plan-management.md` | ✅ |
| 29 | `subscription-plans/billing-integration.md` | ✅ |
| 30 | `subscription-plans/entitlements.md` | ✅ |
| 31 | `webhooks/webhook-management.md` | ✅ |
| 32 | `webhooks/delivery-guarantees.md` | ✅ |
| 33 | `versioning/api-versioning-strategy.md` | ✅ |
| 34 | `versioning/deprecation-policy.md` | ✅ |
| 35 | `admin/admin-console.md` | ✅ |

---

## Delivery Blueprint

| Phase | Deliverable | Owner | Status |
|-------|-------------|-------|--------|
| **Phase 0 — Foundation** | Repository setup, GitHub Actions CI/CD pipeline, AWS CDK infrastructure (ECS, RDS, ElastiCache, CloudFront, Route 53, WAF, S3) | Platform Eng | ✅ Complete |
| **Phase 0 — Foundation** | Database schema design and migrations, Redis key-space design, OpenTelemetry collector setup, local dev environment | Platform Eng | ✅ Complete |
| **Phase 1 — Gateway Core** | Fastify reverse proxy with plugin loader, health-check endpoints (`/health/live`, `/health/ready`), basic HTTP routing | Gateway Team | ✅ Complete |
| **Phase 1 — Gateway Core** | WebSocket proxying, `X-Request-ID` propagation, structured JSON access logging | Gateway Team | ✅ Complete |
| **Phase 2 — Auth & Security** | API key issuance (HMAC-SHA256 hashing), validation middleware, Redis cache layer, key rotation endpoint | Auth Team | ✅ Complete |
| **Phase 2 — Auth & Security** | OAuth 2.0 server (authorisation code + client credentials + PKCE), JWT validation middleware with JWKS caching | Auth Team | ✅ Complete |
| **Phase 2 — Auth & Security** | Scope-based authorisation, WAF rule set, IP allowlist/denylist, bot-detection policies | Security Team | ✅ Complete |
| **Phase 3 — Rate Limiting** | Token-bucket rate limiter (Redis-backed), per-key and per-plan enforcement, `X-RateLimit-*` header injection | Gateway Team | ✅ Complete |
| **Phase 3 — Rate Limiting** | Sliding-window monthly quota tracking, 80%-threshold email alerts, BullMQ quota-reset scheduled jobs, overage flow | Gateway Team | ✅ Complete |
| **Phase 3 — Rate Limiting** | Per-endpoint throttling policies, admin API for policy CRUD without gateway restart | Gateway Team | ✅ Complete |
| **Phase 4 — Transformation** | Header transformation pipeline (add/remove/set on request and response), JSON policy document schema | Gateway Team | ✅ Complete |
| **Phase 4 — Transformation** | JSONata body transformation, JSON↔XML protocol translation, URL and query-parameter rewriting | Gateway Team | ✅ Complete |
| **Phase 5 — Developer Portal** | Next.js 14 portal scaffold, public API catalogue with OpenAPI 3.1 renderer, developer self-registration | Portal Team | ✅ Complete |
| **Phase 5 — Developer Portal** | Email verification flow, plan selection onboarding, first API key generation, getting-started tutorial | Portal Team | ✅ Complete |
| **Phase 5 — Developer Portal** | Developer dashboard (usage charts, key management UI, subscription management, quota consumption bar) | Portal Team | ✅ Complete |
| **Phase 5 — Developer Portal** | Interactive "Try it" API console authenticated with developer's own key | Portal Team | ✅ Complete |
| **Phase 6 — Subscriptions** | Plan tier management in admin console (Free/Basic/Pro/Enterprise, feature flags, trial periods) | Platform Eng | ✅ Complete |
| **Phase 6 — Subscriptions** | Stripe billing integration — subscription lifecycle, Stripe webhook processor, invoice download | Platform Eng | ✅ Complete |
| **Phase 6 — Subscriptions** | Self-service upgrade/downgrade/cancel flows with proration, grace-period handling on payment failure | Platform Eng | ✅ Complete |
| **Phase 7 — Analytics** | Prometheus metrics exporter, Grafana dashboards (request rate, error rate, p99 latency per route/plan) | Observability | ✅ Complete |
| **Phase 7 — Analytics** | OpenTelemetry instrumentation, Jaeger trace export, per-developer usage dashboard with CSV export | Observability | ✅ Complete |
| **Phase 8 — Webhooks** | Webhook CRUD API, HMAC-SHA256 signing, BullMQ delivery queue, exponential backoff retry | Platform Eng | ✅ Complete |
| **Phase 8 — Webhooks** | Dead-letter queue, delivery log UI, manual retry from portal, webhook dead-letter email notification | Platform Eng | ✅ Complete |
| **Phase 9 — Versioning** | Header-based and URL-path versioning strategies, default version fallback, `HTTP 400` on missing version | Gateway Team | ✅ Complete |
| **Phase 9 — Versioning** | `Deprecation`/`Sunset`/`Link` header injection, `HTTP 410 Gone` enforcement, version lifecycle state machine | Gateway Team | ✅ Complete |
| **Phase 10 — Admin Console** | Multi-tenant management, user role assignment, API publishing workflow (draft → review → active) | Admin Team | ✅ Complete |
| **Phase 10 — Admin Console** | Audit log viewer (immutable, WORM S3 stream), RBAC, system health dashboard with BullMQ queue depth | Admin Team | ✅ Complete |
| **Phase 11 — Hardening** | Load testing at 10 k RPS (k6), p99 latency tuning, chaos engineering (AZ failure, Redis failover, rolling deploy) | SRE | ✅ Complete |
| **Phase 11 — Hardening** | Security penetration test, OWASP Top-10 remediation, Spectral API linting in CI, SOC 2 evidence collection | Security Team | ✅ Complete |

---

## Operational Policy Addendum

### API Governance Policies

All APIs published through the gateway must conform to the platform's governance framework before being made publicly available.

**Publication Standards**

- Every API must ship a valid OpenAPI 3.1 specification that passes Spectral linting against the platform style guide (naming conventions, required response schemas, `x-rate-limit` and `x-quota-budget` extension fields, no secrets in examples).
- Breaking changes to a published API require a new major version. The previous version must remain accessible for a minimum sunset period of **90 days**, with a `Deprecation: true` and `Sunset: <date>` response header included on every request to deprecated endpoints.
- Non-breaking additions (new optional fields, new endpoints) may be deployed after standard code review. Breaking changes (field removal, type change, security-requirement addition) require the full versioning lifecycle.
- Emergency breaking changes (security patches) may bypass the 90-day sunset period, but require **immediate notification** to all active subscribers via email and an in-portal alert banner before deployment.

**Review and Approval Workflow**

- New APIs and breaking version changes require sign-off from at least one designated API Design Reviewer and the platform security team before activation.
- The gateway admin console enforces a four-state publishing workflow: `draft → in-review → approved → active`. Transitions are audit-logged with actor identity and timestamp.
- APIs that have been `active` for more than 12 months with zero requests in the last 90 days are flagged for deprecation review by an automated job.

**Backward Compatibility Commitment**

- `active` API versions will not receive breaking changes. Providers who need to introduce a breaking change must cut a new version and follow the deprecation process for the previous version.
- Schema registry validation prevents the publication of a new `active` version that shares the same version identifier as an existing `active` or `deprecated` version.

---

### Developer Data Privacy Policies

The platform processes developer account data, API usage logs, and request metadata. The following policies govern how that data is handled in compliance with GDPR and the platform's privacy commitments.

**Data Minimisation**

- Request and response body payloads are **never** stored in the analytics pipeline. Only request metadata (HTTP method, path, status code, latency, key ID, tenant ID, timestamp, and geographic region) is written to the analytics store.
- PII detected in URL paths or query parameters (email addresses, national ID patterns, credit card patterns) is redacted before writing to any log or analytics table, using a configurable regex-based redaction rule set maintained by the security team.
- IP addresses written to logs are truncated to /24 (IPv4) or /48 (IPv6) precision after 30 days to reduce PII exposure over time.

**Retention Schedule**

- Raw request log records (metadata only) are retained for **90 days**, then deleted by a scheduled BullMQ job.
- Hourly and daily aggregated usage roll-ups are retained for **24 months**.
- Developer account data (profile, keys, billing history) is retained for the lifetime of the account plus **30 days** after deletion (for billing reconciliation), then permanently and irreversibly purged.
- Audit log entries are retained for **7 years** in an append-only S3 WORM bucket to satisfy financial-services regulatory requirements.

**Access Control**

- Developers may view **only** their own usage data. Cross-tenant data isolation is enforced at the database query layer via PostgreSQL Row-Level Security (RLS) policies; application-layer tenant ID checks are an additional defence-in-depth layer, not a primary control.
- Analysts have read-only access to aggregated, anonymised data only. Access to individual developer records requires explicit admin grant, which is logged in the audit trail.
- All platform-employee access to production data is logged with actor identity, timestamp, query, and justification, and reviewed quarterly.

**Data Subject Rights**

- Developers may request a full export of their account data via the portal Settings → Privacy → Export Data page (GDPR Article 20 — right to data portability). Exports are delivered as a signed S3 download link within 24 hours.
- Account deletion requests are processed within **30 days**; a confirmation receipt is emailed to the developer and the deletion is logged in the audit trail.
- Developers may request correction of inaccurate account data directly from the portal or by emailing privacy@platform.example.

---

### Monetization and Quota Policies

**Plan Tiers**

| Tier | Monthly Rate Limit | Monthly API Quota | Max API Keys | Price |
|------|--------------------|-------------------|--------------|-------|
| Free | 60 req/min | 10 000 calls | 2 | $0 |
| Basic | 300 req/min | 500 000 calls | 5 | $49/month |
| Pro | 1 000 req/min | 5 000 000 calls | 10 | $199/month |
| Enterprise | Custom | Custom | Unlimited | Negotiated |

**Quota Enforcement**

- When a developer's monthly quota reaches **80%**, an automated warning email is sent and an in-portal quota banner is displayed with a prominent upgrade call-to-action.
- At **100%** quota consumption the gateway returns `HTTP 429 Too Many Requests` with a `Retry-After` header set to the ISO 8601 timestamp of the start of the next billing period (first day of next calendar month at 00:00 UTC).
- Overage access (Basic and Pro only) can be enabled from the portal billing settings at **$0.001 per additional API call**, billed at end of month. Overage is capped at 2× the plan's quota by default; the cap is configurable for Pro plans.
- Free tier accounts do not have access to overage. When the Free quota is exhausted, the account is blocked for the remainder of the billing period.

**Billing**

- Billing is processed on the **1st of each month** via Stripe using the card on file. Payment failures trigger a **3-day grace period** during which API access continues at current entitlements; after the grace period, the account is automatically downgraded to the Free tier until payment is resolved.
- All invoices are available for download in the portal under Settings → Billing → Invoice History.
- Enterprise customers are invoiced monthly with **Net-30 payment terms** by a platform finance contact. Usage data for reconciliation is available via a dedicated analytics export API.
- Upgrades are billed immediately with proration for the remainder of the current billing period. Downgrades take effect at the end of the current billing period with no refund for the current period.

---

### System Availability and SLA Policies

**Uptime Targets**

| Component | SLA Target | Measurement Window | Credits Threshold |
|-----------|------------|--------------------|-------------------|
| Gateway data plane | 99.99% | Rolling 30 days | < 99.9% triggers 10% service credit |
| Developer Portal | 99.9% | Rolling 30 days | < 99.5% triggers 10% service credit |
| Admin Console | 99.5% | Rolling 30 days | < 99.0% triggers 5% service credit |
| Analytics Pipeline | 99.5% | Rolling 30 days | < 99.0% triggers 5% service credit |

Uptime is measured at the CloudFront distribution level via synthetic canary checks every 60 seconds from three AWS regions.

**Incident Severity and Response Times**

- **P0 — Gateway data-plane outage (> 0.1% error rate sustained for 2 min):** PagerDuty alert within 1 minute; SRE on-call response within 5 minutes; customer-facing status-page update within 10 minutes; incident postmortem published within 48 hours of resolution.
- **P1 — Portal or auth degradation (elevated error rate, slow auth):** Alert within 5 minutes; acknowledged response within 15 minutes; status-page update within 30 minutes.
- **P2 — Analytics lag, BullMQ backlog, non-critical feature degradation:** Alert within 15 minutes; response within 1 business hour; no immediate status-page update required unless customer-visible.
- **P3 — Cosmetic, low-impact, single-user-reported issues:** Triaged within 1 business day; resolved in next scheduled release cycle.

**Maintenance Windows**

- Planned maintenance is scheduled between **02:00–04:00 UTC on the first Sunday of each month**. Advance notice of at least **72 hours** is posted on the status page and emailed to all API Providers and Enterprise-tier developers.
- Zero-downtime rolling ECS task deployments are used for all routine releases. Maintenance windows are reserved for PostgreSQL schema migrations and infrastructure changes that require brief connection draining.
- Emergency security patches may be deployed outside the maintenance window without advance notice, with a post-deployment notification sent within 1 hour.

**Disaster Recovery**

- **RTO (Recovery Time Objective):** 30 minutes for P0 events involving full gateway data-plane failure.
- **RPO (Recovery Point Objective):** 5 minutes — achieved via continuous WAL archiving to S3 for PostgreSQL (RDS automated backups + point-in-time recovery) and Redis AOF persistence with 1-second `fsync`.
- Cross-region warm standby (eu-central-1) is available to Enterprise plan customers under a separately negotiated addendum. Failover to the DR region is a manual runbook procedure with an estimated execution time of 15 minutes.
- Database backups are verified weekly by an automated restore-and-smoke-test job that spins up an isolated RDS instance, restores the latest snapshot, and runs a schema-validation query suite.
