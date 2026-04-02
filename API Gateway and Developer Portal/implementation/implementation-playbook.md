# Implementation Playbook — API Gateway and Developer Portal

---

## Table of Contents

1. [Overview and Phased Delivery Strategy](#1-overview-and-phased-delivery-strategy)
2. [Phase 0: Foundation](#2-phase-0-foundation-2-weeks)
3. [Phase 1: Gateway Core](#3-phase-1-gateway-core-4-weeks)
4. [Phase 2: Authentication and Authorization](#4-phase-2-authentication-and-authorization-3-weeks)
5. [Phase 3: Developer Portal](#5-phase-3-developer-portal-3-weeks)
6. [Phase 4: Analytics and Observability](#6-phase-4-analytics-and-observability-2-weeks)
7. [Phase 5: Subscription Plans and Monetization](#7-phase-5-subscription-plans-and-monetization-2-weeks)
8. [Phase 6: Webhook Management](#8-phase-6-webhook-management-2-weeks)
9. [Phase 7: Advanced Features](#9-phase-7-advanced-features-3-weeks)
10. [Phase 8: Production Hardening](#10-phase-8-production-hardening-2-weeks)
11. [Sprint Breakdown](#11-sprint-breakdown)
12. [Team Structure](#12-team-structure)
13. [Testing Strategy](#13-testing-strategy)
14. [Deployment Pipeline](#14-deployment-pipeline)
15. [Definition of Done](#15-definition-of-done)
16. [Risk Register](#16-risk-register)

---

## 1. Overview and Phased Delivery Strategy

### Product Vision

The API Gateway and Developer Portal is a production-grade platform that provides unified API management, developer self-service onboarding, and full lifecycle control over API consumers. The gateway handles authentication, rate limiting, routing, and observability. The portal allows consumers to register, manage API keys, explore interactive documentation, monitor usage, and manage subscriptions.

### Guiding Principles

- **Incremental value delivery**: Each phase ships a working, deployable increment with measurable business value.
- **Infrastructure as Code from day zero**: All AWS resources are provisioned via Terraform before any application code is written.
- **Security at every layer**: Auth, secrets management, and least-privilege access are built in from Phase 0 — not bolted on later.
- **Observability-driven development**: Structured logs, traces, and metrics are woven in as features are built, not added at the end.
- **Test-first discipline**: Each feature ships with unit, integration, and (where relevant) E2E tests meeting coverage gates.

### Phased Delivery Overview

| Phase | Name                              | Duration | Cumulative Weeks |
|-------|-----------------------------------|----------|-----------------|
| 0     | Foundation                        | 2 weeks  | 2               |
| 1     | Gateway Core                      | 4 weeks  | 6               |
| 2     | Authentication and Authorization  | 3 weeks  | 9               |
| 3     | Developer Portal                  | 3 weeks  | 12              |
| 4     | Analytics and Observability       | 2 weeks  | 14              |
| 5     | Subscription Plans and Monetization | 2 weeks | 16             |
| 6     | Webhook Management                | 2 weeks  | 18              |
| 7     | Advanced Features                 | 3 weeks  | 21              |
| 8     | Production Hardening              | 2 weeks  | 23              |

**Total estimated calendar duration:** 23 weeks (~6 months) with a team of 8–10 engineers.

---

## 2. Phase 0: Foundation (2 Weeks)

### Goals

Establish the monorepo skeleton, CI/CD pipeline, baseline AWS infrastructure, and local development environment so every subsequent phase can begin immediately with zero friction.

### Key Deliverables

| Deliverable                         | Owner               | Acceptance Criteria                                           |
|-------------------------------------|---------------------|---------------------------------------------------------------|
| Turborepo monorepo scaffold         | Platform Team       | `pnpm install && pnpm build` succeeds from root              |
| ESLint + Prettier + TypeScript base | Platform Team       | `pnpm lint` and `pnpm typecheck` pass with zero errors       |
| GitHub Actions CI pipeline          | Platform Team       | Pipeline runs on every PR: lint → typecheck → test → build  |
| Terraform AWS baseline              | Platform Team       | VPC, ECS cluster, RDS, ElastiCache, S3, CloudFront provisioned |
| Base Fastify app (apps/gateway)     | Gateway Team        | Health check endpoint returns 200, deploys to ECS staging    |
| Next.js 14 portal scaffold          | Portal Team         | App Router skeleton with auth layout deployed to ECS staging |
| PostgreSQL migration tooling        | Platform Team       | `pnpm db:migrate` runs Flyway-style migrations via node-pg-migrate |
| Secrets management                  | Platform Team       | AWS Secrets Manager integrated; no secrets in code or env files checked in |
| Pre-commit hooks                    | Platform Team       | Husky + lint-staged run on every commit                      |

### Dependencies

- AWS account with appropriate IAM roles provisioned by DevOps
- Domain registered in Route 53 (`gateway.example.com`, `portal.example.com`)
- GitHub repository with branch protection rules on `main`

### Exit Criteria

- [ ] `pnpm build` succeeds for all packages and apps
- [ ] CI pipeline runs green on a sample PR
- [ ] `terraform apply` produces a working staging environment
- [ ] Health check endpoint is reachable at `https://gateway-staging.example.com/health`
- [ ] Portal scaffold is reachable at `https://portal-staging.example.com`
- [ ] Zero secrets in source code (confirmed by `git-secrets` scan in CI)

---

## 3. Phase 1: Gateway Core (4 Weeks)

### Goals

Build the production-ready Fastify plugin architecture, dynamic request routing, health/readiness probes, API key authentication foundation, Redis-backed rate limiting, and structured request/response logging.

### Key Deliverables

| Deliverable                          | Owner         | Acceptance Criteria                                                |
|--------------------------------------|---------------|--------------------------------------------------------------------|
| Fastify plugin architecture          | Gateway Team  | Core plugins load in correct order; `fastify-plugin` encapsulation enforced |
| Dynamic route registration           | Gateway Team  | Routes loaded from DB at startup; hot-reload via admin API        |
| Liveness and readiness probes        | Gateway Team  | `/health/live` and `/health/ready` exposed; ECS health check passes |
| API key authentication (basic)       | Gateway Team  | HMAC-SHA256 key validation; invalid key returns 401               |
| Redis rate limiting (sliding window) | Gateway Team  | Per-key rate limits enforced; 429 with `Retry-After` header returned |
| Request/response logging (Pino)      | Gateway Team  | JSON logs with correlation ID, method, path, status, duration      |
| Request schema validation            | Gateway Team  | AJV JSON Schema validation on all routes; 400 on invalid input    |
| Admin route management API           | Gateway Team  | CRUD endpoints for routes under `/admin/v1/routes`                |
| Integration test suite               | QA Team       | Supertest tests cover all gateway routes; 80% coverage gate       |

### Dependencies

- Phase 0 complete (monorepo + infra)
- PostgreSQL schema for `routes` and `api_keys` tables migrated
- Redis ElastiCache cluster reachable from ECS tasks

### Exit Criteria

- [ ] All routes validate schemas; unvalidated routes fail CI
- [ ] Rate limiting tested at 2x limit — excess requests receive 429
- [ ] P99 latency on health endpoint < 5 ms under 500 RPS (verified with k6 smoke test)
- [ ] Pino logs include `correlationId` on every request
- [ ] Integration test suite passes; coverage >= 80%

---

## 4. Phase 2: Authentication and Authorization (3 Weeks)

### Goals

Implement production-grade OAuth 2.0 Authorization Code flow with PKCE, JWT validation, mutual TLS support, and a Redis-backed token cache for sub-millisecond token lookups.

### Key Deliverables

| Deliverable                        | Owner        | Acceptance Criteria                                               |
|------------------------------------|--------------|-------------------------------------------------------------------|
| OAuth 2.0 Authorization Server     | Gateway Team | `/oauth/authorize`, `/oauth/token`, `/oauth/revoke` endpoints work end-to-end |
| PKCE flow support                  | Gateway Team | Authorization Code + PKCE verified; code_challenge validated      |
| JWT issuance and validation        | Gateway Team | RS256 JWTs issued; signature validation with JWKS endpoint        |
| mTLS client certificate validation | Gateway Team | Mutual TLS configured at ALB + validated in Fastify plugin        |
| Token caching in Redis             | Gateway Team | Token lookup hits Redis first; DB fallback on cache miss          |
| Token introspection endpoint       | Gateway Team | `/oauth/introspect` returns active/inactive with claims           |
| Scope-based authorization          | Gateway Team | Routes protected by required scopes; 403 on insufficient scope   |
| Refresh token rotation             | Gateway Team | Refresh token single-use; rotation generates new pair             |
| Auth plugin unit tests             | QA Team      | 100% coverage on `packages/auth/` module                         |

### Dependencies

- Phase 1 complete (route registration + API key auth)
- RSA key pair provisioned in AWS Secrets Manager
- ACM certificates for mTLS issued

### Exit Criteria

- [ ] Full OAuth 2.0 Authorization Code + PKCE flow tested with Playwright E2E test
- [ ] JWT validation rejects expired, invalid-signature, and wrong-audience tokens
- [ ] mTLS rejects connections without a valid client certificate
- [ ] Token cache hit rate > 90% under steady-state load
- [ ] 100% test coverage on auth package (enforced by Vitest coverage gate)

---

## 5. Phase 3: Developer Portal (3 Weeks)

### Goals

Build the consumer-facing Next.js 14 portal with self-service registration, API key provisioning and rotation, interactive Swagger UI documentation, and a real-time usage dashboard.

### Key Deliverables

| Deliverable                         | Owner       | Acceptance Criteria                                              |
|-------------------------------------|-------------|------------------------------------------------------------------|
| Consumer registration and login     | Portal Team | Email/password + OAuth SSO signup; email verification flow      |
| API key management UI               | Portal Team | Create, view (masked), rotate, revoke keys; confirmation dialogs |
| Interactive API documentation       | Portal Team | Swagger UI rendered from OpenAPI spec; "Try it" works against staging |
| Usage dashboard                     | Portal Team | Charts for request volume, error rates, latency by time range    |
| Plan selection UI                   | Portal Team | Consumers can view and select plans (free/basic/pro)             |
| Consumer settings and profile       | Portal Team | Update name, email, password; delete account flow               |
| Admin portal (basic)                | Portal Team | List/search consumers; view API key details; suspend consumer    |
| Server-side rendering + auth guard  | Portal Team | All dashboard pages server-rendered; unauthenticated redirect    |
| Playwright E2E test suite           | QA Team     | Key registration, key creation, and docs flows covered           |

### Dependencies

- Phase 2 complete (OAuth 2.0 + JWT for portal auth)
- OpenAPI spec generated from Fastify routes (fastify-swagger)
- Analytics read API available (can mock with fixture data)

### Exit Criteria

- [ ] Consumer can register, log in, create an API key, and make a successful gateway request end-to-end
- [ ] API key is never shown in full after initial creation
- [ ] Usage dashboard renders without errors with 30 days of fixture data
- [ ] Playwright E2E suite passes on CI against staging environment
- [ ] Lighthouse accessibility score >= 90 on portal home page

---

## 6. Phase 4: Analytics and Observability (2 Weeks)

### Goals

Integrate OpenTelemetry tracing across gateway and portal, build a BullMQ analytics event pipeline, expose Prometheus metrics, configure Grafana dashboards, and set up Jaeger distributed tracing.

### Key Deliverables

| Deliverable                          | Owner          | Acceptance Criteria                                             |
|--------------------------------------|----------------|-----------------------------------------------------------------|
| OpenTelemetry SDK integration        | Platform Team  | Every Fastify request creates a span; spans exported to Jaeger  |
| BullMQ analytics event pipeline      | Gateway Team   | Every API request enqueues an analytics event; worker persists to DB |
| Prometheus metrics endpoint          | Gateway Team   | `/metrics` exposes request counts, latency histograms, error rates |
| Grafana dashboards                   | Platform Team  | Gateway overview, consumer usage, rate-limit dashboard deployed |
| Jaeger UI accessible                 | Platform Team  | Traces searchable by traceId, service, operation               |
| Correlation ID propagation           | Gateway Team   | `X-Trace-Id` header forwarded to upstream; appears in all logs  |
| Alerting rules                       | Platform Team  | P99 latency > 500 ms and error rate > 1% trigger PagerDuty alerts |
| Log aggregation                      | Platform Team  | CloudWatch Logs receiving structured JSON from all ECS tasks    |

### Dependencies

- Phase 3 complete (portal live, consumers generating traffic)
- Jaeger all-in-one deployed to ECS (or AWS X-Ray if preferred)
- Prometheus + Grafana deployed to monitoring ECS service

### Exit Criteria

- [ ] Distributed trace visible in Jaeger for a full request from portal → gateway → upstream
- [ ] Grafana dashboard shows real request data (not mocked)
- [ ] Alert fires in test scenario (manually spike error rate)
- [ ] BullMQ dead-letter queue monitored; failed events alerted

---

## 7. Phase 5: Subscription Plans and Monetization (2 Weeks)

### Goals

Build the plan management system, integrate Stripe for payment collection, enforce quota limits at the gateway level, and implement upgrade/downgrade flows with proration.

### Key Deliverables

| Deliverable                          | Owner        | Acceptance Criteria                                              |
|--------------------------------------|--------------|------------------------------------------------------------------|
| Plan schema and CRUD API             | Gateway Team | `plans` table with rate limits, quotas, price; admin CRUD API    |
| Consumer plan assignment             | Gateway Team | Consumers assigned a plan; plan cached in Redis for enforcement  |
| Quota enforcement at gateway         | Gateway Team | Monthly request quota enforced; 429 with quota-exceeded code     |
| Stripe subscription integration      | Portal Team  | Stripe Checkout creates subscription; webhook updates DB plan    |
| Upgrade/downgrade flow               | Portal Team  | Proration calculated; immediate plan switch on upgrade           |
| Stripe webhook handler               | Gateway Team | `invoice.paid`, `customer.subscription.deleted` events handled  |
| Billing history UI                   | Portal Team  | Portal shows invoices and next billing date from Stripe          |
| Plan overage notifications           | Platform Team | Email/Slack alert at 80% and 100% quota consumption             |

### Dependencies

- Phase 4 complete (analytics pipeline tracking usage counts)
- Stripe account with test + prod keys in AWS Secrets Manager
- Phase 3 portal UI for plan selection wired to real API

### Exit Criteria

- [ ] Consumer on free plan blocked after quota exceeded
- [ ] Stripe webhook end-to-end tested in staging with Stripe CLI
- [ ] Plan upgrade immediately lifts rate limit (Redis cache invalidated)
- [ ] Billing page shows correct invoice history

---

## 8. Phase 6: Webhook Management (2 Weeks)

### Goals

Build a full webhook subscription and delivery system — allowing consumers to register HTTPS endpoints, subscribe to event types, and receive reliable deliveries with exponential-backoff retry via BullMQ.

### Key Deliverables

| Deliverable                          | Owner        | Acceptance Criteria                                              |
|--------------------------------------|--------------|------------------------------------------------------------------|
| Webhook subscription API             | Gateway Team | CRUD for webhook endpoints with secret signing                   |
| BullMQ webhook delivery pipeline     | Gateway Team | Events enqueued; worker POSTs to consumer endpoint               |
| HMAC-SHA256 signature headers        | Gateway Team | `X-Webhook-Signature` header computed and verifiable by consumer |
| Exponential backoff retry            | Gateway Team | 5 retries with 1 min → 32 min backoff; moves to DLQ on failure  |
| Delivery logs and status             | Gateway Team | Each delivery attempt recorded with HTTP status and latency      |
| Webhook delivery UI                  | Portal Team  | Portal shows delivery history, retry button, test-send button    |
| Webhook event catalog                | Portal Team  | All publishable event types documented in portal                 |
| Webhook security validation          | QA Team      | Replayed requests (duplicate `webhook-id`) rejected             |

### Dependencies

- Phase 4 complete (BullMQ worker infrastructure running)
- Phase 3 portal for webhook UI

### Exit Criteria

- [ ] Webhook delivered successfully to ngrok test endpoint from staging
- [ ] Retry fires after 1-minute delay on simulated 500 from consumer endpoint
- [ ] Duplicate delivery prevented (idempotency key check)
- [ ] Delivery logs visible in portal UI within 5 seconds of delivery

---

## 9. Phase 7: Advanced Features (3 Weeks)

### Goals

Implement API versioning strategy, request/response transformation pipeline, protocol translation (REST↔gRPC), and a searchable API catalog for consumers.

### Key Deliverables

| Deliverable                           | Owner        | Acceptance Criteria                                              |
|---------------------------------------|--------------|------------------------------------------------------------------|
| URI-based API versioning              | Gateway Team | `/v1/` and `/v2/` routes independently configured               |
| Request header transformation         | Gateway Team | Plugin injects/removes/renames headers per route config          |
| Response body filtering               | Gateway Team | Fields removed/mapped per consumer plan (e.g., PII fields hidden)|
| JSON schema coercion                  | Gateway Team | Request body transformed to match upstream schema               |
| gRPC↔REST protocol bridge             | Gateway Team | REST request proxied to gRPC upstream via `@grpc/grpc-js`       |
| API catalog with search               | Portal Team  | Consumers browse and search APIs; filter by category, version   |
| API deprecation notices               | Portal Team  | Deprecated versions shown with sunset date in portal and headers |
| Version migration guide generator     | Portal Team  | Diff between v1 and v2 schemas shown in portal                  |

### Dependencies

- Phase 2 complete (auth plugins must support versioned routes)
- Phase 5 complete (plan-based field filtering requires plan context)

### Exit Criteria

- [ ] v1 and v2 routes return different responses for same path
- [ ] Header transformation verified with integration tests
- [ ] gRPC bridge tested with sample gRPC service in staging
- [ ] API catalog search returns relevant results with < 200 ms latency

---

## 10. Phase 8: Production Hardening (2 Weeks)

### Goals

Conduct load testing, security audit, disaster recovery testing, and create comprehensive runbooks before production launch.

### Key Deliverables

| Deliverable                          | Owner          | Acceptance Criteria                                              |
|--------------------------------------|----------------|------------------------------------------------------------------|
| k6 load test suite                   | QA Team        | Gateway sustains 10,000 RPS at P99 < 200 ms with no errors      |
| OWASP ZAP security scan              | QA + Security  | Zero critical, zero high findings after remediation              |
| Penetration test                     | External       | Third-party pen test report with all findings addressed          |
| Chaos engineering scenarios          | Platform Team  | RDS failover, Redis failover, ECS task kill handled gracefully   |
| Disaster recovery runbook            | Platform Team  | RTO < 30 min, RPO < 5 min verified with DR drill                |
| Operational runbooks                 | Platform Team  | Runbooks for: deploy, rollback, scale, incident response        |
| CDK/Terraform drift detection        | Platform Team  | Scheduled job alerts on infrastructure drift                     |
| Rate limit and quota tuning          | Gateway Team   | Production rate limits reviewed and adjusted based on load tests |
| Launch checklist sign-off            | All Teams      | All Definition of Done items verified by team leads              |

### Dependencies

- All Phases 0–7 complete
- Production AWS environment provisioned (separate from staging)
- DNS cutover plan approved

### Exit Criteria

- [ ] Load test at 10,000 RPS passes without errors
- [ ] Zero OWASP ZAP critical/high findings
- [ ] DR drill completed — recovery within RTO/RPO targets
- [ ] All runbooks reviewed and approved
- [ ] Production launch checklist signed off by engineering lead and product owner

---

## 11. Sprint Breakdown

Sprints are 2 weeks each. Point estimates use Fibonacci (1, 2, 3, 5, 8, 13).

### Sprint 1–2 (Phase 0: Foundation)

| Story                                      | Points |
|--------------------------------------------|--------|
| Turborepo + pnpm workspace setup           | 3      |
| TypeScript + ESLint + Prettier config      | 2      |
| GitHub Actions CI pipeline (lint/test/build)| 5     |
| Terraform VPC + networking                 | 8      |
| Terraform ECS cluster + task definitions  | 8      |
| Terraform RDS PostgreSQL + ElastiCache     | 5      |
| Terraform CloudFront + Route 53 + WAF      | 5      |
| Base Fastify app with health check         | 3      |
| Next.js 14 App Router scaffold             | 3      |
| node-pg-migrate setup + initial schema     | 3      |
| AWS Secrets Manager integration            | 3      |
| Pre-commit hooks (Husky + lint-staged)     | 2      |
| **Sprint Total**                           | **50** |

### Sprint 3–4 (Phase 1: Gateway Core — Part 1)

| Story                                      | Points |
|--------------------------------------------|--------|
| Fastify plugin architecture skeleton       | 8      |
| Dynamic route loader from PostgreSQL       | 8      |
| JSON Schema AJV validation plugin          | 5      |
| API key hash lookup from DB                | 5      |
| HMAC-SHA256 key validation utility         | 3      |
| Redis sliding window rate limiter          | 8      |
| **Sprint Total**                           | **37** |

### Sprint 5–6 (Phase 1: Gateway Core — Part 2)

| Story                                      | Points |
|--------------------------------------------|--------|
| Pino structured logging integration        | 3      |
| Correlation ID middleware                  | 3      |
| Admin routes CRUD API                      | 5      |
| Liveness/readiness probe endpoints         | 2      |
| Hot-reload route config via admin API      | 5      |
| Supertest integration test suite           | 8      |
| CI coverage gate (80%)                     | 2      |
| **Sprint Total**                           | **28** |

### Sprint 7–9 (Phase 2: Authentication and Authorization)

| Story                                      | Points |
|--------------------------------------------|--------|
| OAuth 2.0 authorization endpoint           | 8      |
| OAuth 2.0 token endpoint + PKCE            | 8      |
| OAuth 2.0 revoke + introspect              | 5      |
| RS256 JWT issuance with JWKS endpoint      | 8      |
| JWT validation middleware plugin           | 5      |
| Refresh token rotation                     | 5      |
| Scope-based authorization middleware       | 5      |
| mTLS client certificate validation         | 8      |
| Redis token cache                          | 5      |
| 100% auth package test coverage            | 5      |
| **Sprint Total**                           | **62** |

### Sprint 10–12 (Phase 3: Developer Portal)

| Story                                      | Points |
|--------------------------------------------|--------|
| Consumer registration + email verification | 8      |
| Login with OAuth SSO (Google)              | 5      |
| API key management UI (create/revoke/rotate)| 8     |
| Swagger UI integration with live spec      | 5      |
| Usage dashboard (charts with recharts)     | 8      |
| Plan selection UI                          | 5      |
| Consumer profile and settings              | 3      |
| Admin consumer management UI               | 5      |
| Playwright E2E test suite                  | 8      |
| **Sprint Total**                           | **55** |

### Sprint 13–14 (Phase 4: Analytics and Observability)

| Story                                      | Points |
|--------------------------------------------|--------|
| OpenTelemetry SDK + Fastify instrumentation| 8      |
| BullMQ analytics event worker              | 5      |
| Prometheus metrics endpoint                | 5      |
| Grafana dashboards (gateway + consumer)    | 8      |
| Jaeger integration + trace search          | 5      |
| CloudWatch log aggregation                 | 3      |
| PagerDuty alerting rules                   | 5      |
| **Sprint Total**                           | **39** |

### Sprint 15–16 (Phase 5: Monetization)

| Story                                      | Points |
|--------------------------------------------|--------|
| Plan schema + admin CRUD API               | 5      |
| Quota enforcement in gateway               | 8      |
| Stripe Checkout integration                | 8      |
| Stripe webhook handler                     | 5      |
| Upgrade/downgrade flow with proration      | 8      |
| Billing history UI                         | 5      |
| Overage email notifications                | 3      |
| **Sprint Total**                           | **42** |

### Sprint 17–18 (Phase 6: Webhooks)

| Story                                      | Points |
|--------------------------------------------|--------|
| Webhook subscription CRUD API              | 5      |
| BullMQ delivery worker + retry logic       | 8      |
| HMAC-SHA256 signature on delivery          | 3      |
| DLQ monitoring and alerting                | 3      |
| Delivery log persistence                   | 3      |
| Webhook UI in portal                       | 5      |
| Idempotency key deduplication              | 5      |
| **Sprint Total**                           | **32** |

### Sprint 19–21 (Phase 7: Advanced Features)

| Story                                      | Points |
|--------------------------------------------|--------|
| URI-based versioning (v1/v2)               | 5      |
| Request header transformer plugin          | 5      |
| Response body filter plugin                | 8      |
| JSON schema coercion transformer           | 5      |
| gRPC↔REST protocol bridge                  | 13     |
| API catalog with full-text search          | 8      |
| API deprecation notices (headers + UI)     | 5      |
| Version migration diff UI                  | 5      |
| **Sprint Total**                           | **54** |

### Sprint 22–23 (Phase 8: Hardening)

| Story                                      | Points |
|--------------------------------------------|--------|
| k6 load test suite (10k RPS)               | 8      |
| OWASP ZAP scan + remediation               | 8      |
| Chaos engineering scenarios (3 scenarios)  | 8      |
| DR drill and runbook                       | 5      |
| Operational runbook set                    | 5      |
| CDK/Terraform drift detection job          | 3      |
| Launch checklist sign-off                  | 3      |
| **Sprint Total**                           | **40** |

---

## 12. Team Structure

### Gateway Team (3 engineers)

Responsible for all Fastify plugin development, routing engine, auth plugins, rate limiting, transformation pipeline, protocol bridge, and gateway admin API.

- **Senior Engineer (Tech Lead):** Plugin architecture, auth, rate limiting
- **Mid Engineer:** Route management, transformation, versioning
- **Mid Engineer:** Analytics pipeline, BullMQ workers, webhook delivery

### Portal Team (2 engineers)

Responsible for the Next.js 14 developer portal, admin UI, and Stripe integration.

- **Senior Engineer (Tech Lead):** App Router architecture, auth flows, dashboard
- **Mid Engineer:** API key management, webhook UI, billing UI

### Platform / Infra Team (2 engineers)

Responsible for Terraform infrastructure, CI/CD pipelines, observability stack, and secrets management.

- **Senior DevOps Engineer:** Terraform, ECS, RDS, ElastiCache, CloudFront, WAF
- **SRE / Observability Engineer:** OpenTelemetry, Prometheus, Grafana, Jaeger, alerting

### QA Team (1–2 engineers)

Responsible for integration test suite (Supertest), E2E suite (Playwright), load tests (k6), and security scans (OWASP ZAP).

- **QA Engineer:** Test strategy, Supertest suite, Playwright E2E, coverage enforcement
- **Security / QA Engineer (Part-time):** OWASP ZAP, pen test coordination, chaos engineering

---

## 13. Testing Strategy

### Unit Tests (Vitest)

- Colocated with source files as `*.test.ts`
- Run on every commit via pre-commit hook (fast subset) and full suite in CI
- Coverage gates: **80% overall**, **100% for `packages/auth/` and `packages/rate-limit/`**
- Pure functions tested in isolation; side effects mocked with `vi.mock()`
- Test naming convention: `describe('ComponentName', () => { it('should [behavior] when [condition]', ...) })`

### Integration Tests (Supertest)

- Located in `apps/gateway/test/integration/`
- Each Fastify plugin has a corresponding integration test file
- Tests spin up a real Fastify instance with test database (via Testcontainers)
- Redis tested with a real Testcontainers Redis instance
- Run in CI after unit tests; parallelized across plugin suites

### End-to-End Tests (Playwright)

- Located in `apps/portal/e2e/`
- Test critical consumer journeys: register → create key → call gateway → view usage
- Run against deployed staging environment in CI
- Fixtures used for predictable test data (seeded via migration scripts)
- Visual regression tests for portal dashboard and API docs pages

### Load Tests (k6)

- Scripts located in `tests/load/`
- Scenarios: ramp-up to 1k/5k/10k RPS, spike test, soak test (1 hour at 5k RPS)
- Pass criteria: P99 < 200 ms at 10k RPS, zero errors at sustained 5k RPS
- Run manually before each phase release and automatically on Phase 8 hardening

### Chaos Engineering

- **Scenario 1: RDS failover** — promote read replica, verify gateway reconnects < 30 s
- **Scenario 2: Redis cluster failure** — stop ElastiCache primary; rate limiter must degrade gracefully (fail-open with warning log)
- **Scenario 3: ECS task kill** — kill 50% of gateway tasks; ALB routes around unhealthy tasks with zero request loss

---

## 14. Deployment Pipeline

### GitHub Actions Workflow Stages

```
PR Opened
    │
    ▼
[lint]          ── ESLint + Prettier check (all packages)
    │
    ▼
[typecheck]     ── tsc --noEmit (all packages)
    │
    ▼
[unit-test]     ── Vitest with coverage gate (parallel by package)
    │
    ▼
[integration-test] ── Supertest with Testcontainers (parallel by app)
    │
    ▼
[build]         ── Docker image build for gateway + portal (multi-stage)
    │
    ▼
[security-scan] ── npm audit (fail on critical); Trivy container scan
    │
    ▼
PR Merged to main
    │
    ▼
[deploy-staging] ── Push images to ECR; update ECS task definitions; ECS rolling deploy
    │
    ▼
[smoke-test]    ── Playwright smoke suite against staging (5 critical flows)
    │
    ▼
[deploy-prod]   ── Manual approval gate → ECS blue/green deploy to production
    │
    ▼
[post-deploy]   ── Cloudwatch synthetic canary runs for 5 min; auto-rollback on failure
```

### Deployment Configuration

- **ECS Strategy:** Blue/green via AWS CodeDeploy for zero-downtime production deploys
- **Rollback:** Automatic on health check failure within 5 minutes of deploy
- **Environment promotion:** Staging → Production requires explicit GitHub environment approval
- **Image tagging:** Semantic version + short SHA (`v1.2.3-abc1234`)
- **Secrets:** Injected at runtime from AWS Secrets Manager via ECS task role

---

## 15. Definition of Done

Every feature, regardless of size, must satisfy all items on this checklist before it is considered complete and eligible for merge to `main`.

### Code Quality

- [ ] TypeScript strict mode — zero `any` types without explicit `// eslint-disable` comment with justification
- [ ] ESLint passes with zero warnings or errors
- [ ] Prettier formatting applied
- [ ] No new `TODO` or `FIXME` comments without an associated JIRA ticket reference

### Testing

- [ ] Unit tests written and passing; coverage does not decrease from baseline
- [ ] Integration tests updated to cover new code paths
- [ ] E2E test added or updated for any user-facing feature
- [ ] Test assertions are deterministic (no flaky tests merged)

### Security

- [ ] No sensitive data (API keys, tokens, PII) in logs
- [ ] All user input validated at schema level before use
- [ ] `npm audit` shows zero critical or high vulnerabilities
- [ ] `crypto.timingSafeEqual` used for any secret comparison
- [ ] Secrets sourced from environment variables / AWS Secrets Manager only

### Observability

- [ ] New Fastify routes emit OpenTelemetry spans
- [ ] Structured log lines include `correlationId`
- [ ] New error conditions log at appropriate level with context
- [ ] Metrics counter/histogram added for new operations (if applicable)

### Documentation

- [ ] OpenAPI spec updated for any new or changed endpoint
- [ ] README in affected package updated if public interface changed
- [ ] ADR written for any significant architectural decision

### Deployment

- [ ] Docker build succeeds for affected apps
- [ ] Terraform plan shows no unintended infrastructure changes
- [ ] Feature flag added for any risky feature rollout (if applicable)
- [ ] Smoke test passes on staging after deploy

---

## 16. Risk Register

| # | Risk                                             | Probability | Impact   | Mitigation                                                                                     |
|---|--------------------------------------------------|-------------|----------|-----------------------------------------------------------------------------------------------|
| 1 | Redis ElastiCache failure causes total outage    | Low         | Critical | Implement fail-open rate limiting; circuit breaker falls back to in-memory counter with TTL  |
| 2 | OAuth 2.0 implementation has security flaw       | Medium      | Critical | External pen test in Phase 8; use established library (`oauth2orize`) not hand-rolled auth   |
| 3 | PostgreSQL RDS connection pool exhaustion         | Medium      | High     | PgBouncer connection pooler in front of RDS; monitor pool usage with Prometheus alert        |
| 4 | BullMQ worker lag causes analytics delay         | Medium      | Medium   | Horizontal scaling of worker ECS tasks; dead-letter queue with alert on queue depth > 10,000 |
| 5 | Stripe webhook replay attack                     | Low         | High     | Verify Stripe signature + timestamp; reject events older than 300 seconds                    |
| 6 | gRPC↔REST bridge performance degradation         | Medium      | Medium   | Benchmark in Phase 7; fall back to direct REST proxy if P99 > 50 ms penalty                |
| 7 | Third-party dependency supply chain attack       | Low         | Critical | npm audit in CI; Dependabot PRs auto-created; Trivy image scan blocks on critical CVE       |
| 8 | AWS ECS task scheduling failures during scale-up | Low         | High     | Pre-warm ECS capacity providers; configure ECS capacity provider with target tracking       |
| 9 | Consumer data migration issues during schema change | Medium   | High     | All migrations backward-compatible (expand/contract pattern); tested on staging with prod-sized data |
| 10| Team velocity slower than estimated               | High        | Medium   | Buffer sprints built into Phase 8; Phase 7 advanced features are de-scopable if needed      |

---

*Last updated: Phase 0 kickoff. Owned by Engineering Lead. Review at start of each phase.*
