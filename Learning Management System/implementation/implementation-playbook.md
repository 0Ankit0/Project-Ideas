# Implementation Playbook — Learning Management System

> Version: 1.0 | Status: Approved | Last Updated: 2025

---

## 1. Delivery Goal

Build and ship a production-ready, multi-tenant LMS covering course authoring, learner delivery, assessment and grading, progress analytics, and certificate issuance. The system enforces hard tenant isolation, targets 99.9% monthly uptime, and maintains regulatory-grade audit trails suitable for SOC 2 Type II and GDPR compliance.

---

## 2. Tech Stack Decisions

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Runtime | Node.js 20 LTS | Native async, low latency; strong ecosystem for streaming content events |
| Language | TypeScript 5 (strict) | Type safety across service boundaries; prevents entire class of multi-tenant guard-rail bugs |
| API Framework | Fastify 4 | JSON schema validation built-in; 30-40% lower overhead than Express under high RPS |
| Database | PostgreSQL 16 | JSONB for content metadata; row-level security for tenant isolation; declarative partitioning for audit/progress scale |
| Cache / Session | Redis 7 Cluster | Sub-millisecond session lookups; enrollment status cache; distributed rate limiting via Redis cell |
| Job Queue | BullMQ (Redis-backed) | Reliable enrollment processing, grade-release jobs, and certificate generation with configurable retry and dead-letter semantics |
| Object Storage | AWS S3 (or S3-compatible) | Presigned URL delivery for scoped learner access; server-side encryption at rest |
| Search | PostgreSQL full-text + `pg_trgm` | Avoids Elasticsearch operational overhead at startup scale; upgrade path to OpenSearch when corpus exceeds 1M rows |
| Authentication | JWT (15 min TTL) + Refresh Token rotation | Stateless verification; refresh rotation limits blast radius of token theft |
| SSO | SAML 2.0 + OIDC (passport.js) | Enterprise tenant requirement; OIDC covers Google Workspace and Azure AD out of the box |
| API Gateway | AWS API Gateway + WAF | Rate limiting, tenant routing, IP allow-listing, DDoS protection |
| Observability | OpenTelemetry → Grafana / Tempo / Loki | Unified traces, metrics, and logs; no vendor lock-in; correlate requests across services with a single trace ID |
| Infrastructure | Terraform + Kubernetes (EKS) | Reproducible multi-region deployments; namespace-level tenant isolation option |
| CI/CD | GitHub Actions → ArgoCD | PRs trigger lint, type-check, and test; ArgoCD handles GitOps promotion from staging to production |
| DB Migrations | Flyway | Versioned, repeatable migrations; rollback scripts required for every destructive change |

---

## 3. Team Structure and Responsibilities

| Role | Count | Responsibilities |
|------|-------|-----------------|
| Engineering Lead | 1 | Architecture decisions, cross-team unblocking, release gate sign-off |
| Backend Engineers | 3 | API services, DB migrations, queue workers, third-party integrations |
| Frontend Engineers | 2 | Learner portal, instructor authoring UI, tenant admin dashboard |
| DevOps / Platform Engineer | 1 | Kubernetes, CI/CD pipelines, observability stack, DR drills |
| QA Engineer | 1 | Test plans, integration and regression suite, load test scenarios |
| Product Manager | 1 | Acceptance criteria, stakeholder demos, scope arbitration |

**Decision authority:** Engineering Lead is accountable for all technical release gates. Product Manager is accountable for scope and schedule. Neither can override the other's gate unilaterally — escalation goes to VP Engineering.

---

## 4. Phase 1 — Foundation (Weeks 1–4)

### Duration
4 weeks

### Deliverables

1. **Tenant service** — Full CRUD for tenants including status lifecycle (`active → suspended → deleted`), branding config storage, and soft-delete with `deleted_at`.
2. **User service** — User CRUD scoped by tenant; role assignment; status transitions; external identity mapping for SSO.
3. **Authentication service** — JWT issuance and validation; refresh token rotation with Redis-backed revocation list; SAML 2.0 assertion consumption; OIDC token exchange.
4. **RBAC middleware** — Permission guards on all route handlers enforcing the six-role matrix; tenant-boundary checks on every request; role matrix documented and reviewed.
5. **Database baseline** — All 14 tables created via Flyway migrations with full indexes, CHECK constraints, UNIQUE constraints, FK relationships, and row-level security policies enabled.
6. **Local development stack** — Docker Compose with PostgreSQL 16, Redis 7, MinIO, and all services with hot-reload; one-command startup via `make dev`.
7. **CI pipeline** — ESLint, TypeScript type-check, unit tests, and Flyway migration smoke-test on every PR; build fails on any error.
8. **Observability skeleton** — OpenTelemetry SDK integrated in all services; structured JSON logging with trace-id correlation; `/health` and `/ready` endpoints on all services.

### Dependencies

- Cloud account provisioned with VPC, subnets, and IAM roles; infrastructure code merged to `main`.
- SSO provider credentials from at least one pilot enterprise tenant available for integration testing.
- Role and permission matrix agreed with Product and signed off before development starts.

### Testing Approach

- Unit tests for all RBAC guard logic targeting 100% branch coverage on permission checks.
- Integration tests for tenant and user CRUD, login, token refresh, token revocation, and SAML/OIDC assertion flows.
- Migration tests: `flyway migrate` on a clean PostgreSQL instance must complete with zero errors and zero warnings.
- Tenant isolation smoke tests: authenticated request from Tenant A must receive `HTTP 403` on every Tenant B resource endpoint.

### Exit Criteria

- All 14 Flyway migrations apply cleanly to a fresh database with no manual intervention.
- Login, token refresh, and role-scoped access verified for all six roles in integration tests.
- Zero high-severity TypeScript errors or ESLint violations in CI.
- Tenant isolation tests pass across all resource types.
- P50 auth endpoint latency < 50 ms at 100 RPS on a local load test.

---

## 5. Phase 2 — Core Learning Features (Weeks 5–10)

### Duration
6 weeks

### Deliverables

1. **Course catalog service** — Create, update, publish, and archive courses; course version state machine (`draft → in_review → published → archived`) enforced with guard conditions.
2. **Content structure API** — Module and lesson CRUD; drag-and-drop sequence management; content file upload to S3 with presigned URL generation scoped to enrollment status.
3. **Cohort management** — Create cohorts with schedule, seat limit, and enrollment policy; assign instructors; cohort status automation (`scheduled → active → completed`).
4. **Enrollment service** — Individual and bulk enrollment; invite flow with email notification; idempotency key enforcement; expiry scheduler via BullMQ repeatable job.
5. **Learner progress service** — Ingest progress events (start, heartbeat, complete); upsert `progress_records`; compute per-enrollment completion percentage; handle concurrent updates with optimistic locking.
6. **Learner dashboard API** — Active enrollments with progress summary, upcoming cohort schedule, resume-state per lesson.
7. **Instructor dashboard API** — Cohort roster with per-learner progress, completion funnel, overdue learner identification.
8. **Background workers** — Enrollment expiry checker (daily cron); cohort status updater (hourly cron); dead-letter queue monitor with Slack alerting.

### Dependencies

- Phase 1 exit criteria met and all Phase 1 migrations stable.
- S3 bucket policies, CORS configuration, and per-tenant upload path conventions approved by security.
- Maximum content file size agreed with Product (default: 2 GB per file; overridable by plan).

### Testing Approach

- Integration tests covering the full enroll → progress → completion lifecycle for both mandatory-only and mixed mandatory/optional lesson sets.
- Contract tests for presigned URL generation confirming correct bucket, key prefix, expiry, and HTTP method.
- Load test: 500 concurrent learners simultaneously updating progress records; p99 response time < 200 ms; zero deadlocks logged.
- Tenant isolation: learner from Tenant A must receive `HTTP 403` on all Tenant B course, enrollment, and progress endpoints.
- Idempotency: enrolling the same learner twice with the same `idempotency_key` must return the existing enrollment without creating a duplicate.

### Exit Criteria

- Full end-to-end flow verified: create course → publish version → create cohort → enroll learner → complete all lessons → enrollment status becomes `completed`.
- Bulk enrollment of 1,000 learners processes within 60 seconds via queue worker.
- All tenant isolation integration tests passing with zero leakage.
- Instructor dashboard reflects accurate progress data within 5 seconds of a learner event.
- Load test passes at target RPS with no p99 regressions.

---

## 6. Phase 3 — Advanced Features (Weeks 11–16)

### Duration
6 weeks

### Deliverables

1. **Assessment engine** — Quiz and exam creation with structured question bank (MCQ, true/false, short answer); question shuffle; time-limit enforcement via server-side expiry timer stored in Redis.
2. **Attempt lifecycle management** — Start, answer, submit, and time-out flows; `max_attempts` enforcement with pessimistic lock on `(assessment_id, enrollment_id)`; idempotent submission preventing duplicate scoring.
3. **Auto-grading service** — Immediate score computation for MCQ and true/false questions on submission; `grade_record` created atomically with `grade_source = 'auto'`.
4. **Manual grading workflow** — Reviewer assignment queue; rubric display with scoring cells; score entry with required feedback; grade release with `release_rule` enforcement.
5. **Grade override and revision** — Authorised overrides by `tenant_admin` or `platform_admin`; `override_reason` required; new `grade_record` revision appended; audit log entry created in the same transaction.
6. **Certificate issuance service** — Trigger on enrollment `completed`; ULID serial number generation; PDF rendering via Puppeteer with tenant branding; verification URL pointing to public endpoint; idempotency enforcement via `certificates.idempotency_key`.
7. **Notification service** — Email (SES/SendGrid) and in-app notifications for: enrollment invite, cohort reminders (T−7, T−1 days), grade released, certificate issued; per-tenant template overrides.
8. **Analytics API** — Course completion rates, assessment pass rates, learner time-on-platform by cohort; served from read replica; results cached in Redis with 5-minute TTL.
9. **Webhook framework** — Configurable per-tenant outbound webhooks for `enrollment.completed`, `grade.released`, and `certificate.issued` events; HMAC-SHA256 signing; exponential-backoff retry with dead-letter after 5 failures.

### Dependencies

- Phase 2 exit criteria met.
- Email provider credentials (SES/SendGrid) provisioned and sandbox-tested.
- Certificate PDF template designs signed off by Product before rendering implementation begins.
- Webhook secret rotation policy and retry SLA agreed with security team.

### Testing Approach

- Unit tests for all scoring logic, attempt-limit enforcement, and grade-source assignment targeting 95% branch coverage.
- Integration tests covering the full assessment lifecycle: create → start attempt → submit answers → auto-grade → release → learner notified.
- Manual grading workflow tested end-to-end with reviewer role assignment, rubric scoring, and override flow including audit log verification.
- Certificate idempotency: issuing twice with the same `idempotency_key` must return the identical certificate record without creating a duplicate row.
- Webhook delivery test: simulate 100 concurrent completion events; verify all webhooks delivered within 5 s; simulate endpoint downtime and verify retry exhaustion creates dead-letter entries.

### Exit Criteria

- Auto-graded assessments produce correct `grade_records` within 2 seconds of submission under normal load.
- Manual grading workflow signed off in QA-run UAT session with Product.
- Certificate PDF renders correctly across three tenant branding configurations; verification URL resolves to correct learner details.
- Analytics completion-rate query returns in < 500 ms for tenants with 10,000 enrollments.
- Webhook delivery achieves < 5 s end-to-end latency for completion events at 1,000 events/min.

---

## 7. Phase 4 — Production Hardening (Weeks 17–20)

### Duration
4 weeks

### Deliverables

1. **Security audit remediation** — All critical and high findings from external penetration test resolved before go-live; medium/low findings documented with accepted-risk sign-off.
2. **Multi-region DR validation** — Cross-region replica lag measured under production-equivalent load; failover drill executed, timed, and documented against RTO ≤ 4 hours and RPO ≤ 15 minutes targets.
3. **Production-scale load test** — Sustained 5,000 concurrent learners; 500 simultaneous assessment submissions; enrollment burst of 10,000 in 5 minutes; all p99 latencies within SLO.
4. **Runbook library** — Written and rehearsed runbooks for: DB primary failover, BullMQ queue drain and replay, certificate re-issuance, tenant suspension, enrollment bulk-import recovery, and PII erasure request.
5. **Alerting and on-call configuration** — PagerDuty routing rules for P1/P2/P3 alert tiers; synthetic Playwright monitors for the critical enroll → learn → assess → certify flow running every 5 minutes in production; on-call rotation with documented escalation path.
6. **GDPR and data compliance** — Right-to-erasure API endpoint that anonymises PII fields within 72 hours; data map reviewed and signed off by legal; data-retention jobs tested end-to-end in staging.
7. **Tenant onboarding automation** — CLI tool for provisioning a new tenant (DB RLS policy, Redis namespace, S3 prefix, initial admin user seeding); dry-run mode verified.
8. **Go-live cutover plan** — Pilot-tenant data migration script tested on production-scale data copy; DNS cutover checklist; rollback decision tree with explicit trigger conditions and owner assignments.

### Dependencies

- Phase 3 exit criteria met.
- External penetration test engagement booked, scoped, and executed with findings report delivered.
- GDPR / SOC 2 scope review completed by legal and signed off.
- Production Kubernetes cluster, RDS instances, and monitoring stack provisioned and validated by DevOps.

### Testing Approach

- Load test with k6: 5,000 concurrent virtual users, 10,000 enrollments/minute burst, p99 API latency SLO < 500 ms across all core endpoints.
- DR drill: simulate primary database failure by promoting the cross-region replica; measure actual RTO against the 4-hour target; verify zero data loss beyond the 15-minute RPO window.
- Chaos engineering: forcefully stop one Kubernetes pod per service during sustained load; verify graceful degradation (circuit breakers open, queues buffer, learners see degraded-mode UI not hard errors).
- GDPR erasure test: trigger erasure for a test user in staging populated with production-scale data; confirm all PII fields nulled or anonymised within 72 hours.
- Synthetic monitor validation: verify the Playwright end-to-end monitor triggers a P2 alert within 3 minutes of a simulated API outage.

### Exit Criteria

- All P0 and P1 penetration test findings resolved; external auditor sign-off received.
- DR drill completed within RTO; recovery verified by read-back of the last known write before simulated failure.
- Load test passed: p99 < 500 ms across all core endpoints at 5,000 concurrent users; no database deadlocks; queue depth stable.
- All runbooks reviewed, rehearsed, and signed off by on-call engineers.
- GDPR erasure flow verified; legal sign-off on data map.
- Go-live checklist signed by Engineering Lead, Product Manager, and DevOps Engineer.

---

## 8. Deployment and Rollout Strategy

### Environment Topology

| Environment | Purpose | Deployment Trigger | Approval Required |
|-------------|---------|-------------------|-------------------|
| local | Developer sandbox | Docker Compose, manual | None |
| preview | Per-PR feature validation | PR opened or updated | None |
| staging | Integration, QA, and load testing | Merge to `main` | None (auto) |
| production | Live system | Tag `v*` on `main` | Engineering Lead |

### Release Models

**Blue-Green** is used for schema migrations and major service version releases. The new (green) version is deployed alongside the current (blue). Traffic is shifted after automated smoke tests pass. Blue is kept warm for a 15-minute rollback window, then terminated.

**Canary** is used for stateless API changes. 5% of production traffic is routed to the canary pod for 30 minutes. Auto-promotion occurs if the canary error rate remains below 0.1% and p99 latency stays within 10% of the baseline. Automatic rollback triggers if either threshold is breached.

**Feature flags** gate all Phase 3 features during rollout, enabling per-tenant activation before a full release. LaunchDarkly or Unleash (self-hosted) are both supported via the feature-flag adapter interface.

### Database Migration Policy

- All migrations are forward-only `V{n}__description.sql` Flyway scripts.
- Every migration with a destructive change (DROP, NOT NULL addition, index removal) requires a corresponding `V{n}__down.sql` rollback script reviewed in the PR.
- Migrations run in a pre-deployment Kubernetes init container before the new application pod starts.
- All migrations must be backward-compatible with the previous application version to support safe blue-green rollbacks.

### Rollback Procedure

1. Trigger ArgoCD image rollback to the previous tag — completes within 2 minutes.
2. If a migration was applied and must be reversed, the on-call engineer executes the `V{n}__down.sql` script manually after Engineering Lead approval.
3. Incident record created in the tracking system within 15 minutes; post-mortem scheduled within 5 business days.

---

## 9. Risk Register

| ID | Risk | Probability | Impact | Mitigation |
|----|------|-------------|--------|------------|
| R-01 | Tenant data leakage through a missing RLS policy on a newly created table | Medium | Critical | Automated test asserts `row_security = on` for every user-data table; CI migration linter rejects any `CREATE TABLE` without a corresponding `ALTER TABLE ... ENABLE ROW LEVEL SECURITY` in the same migration |
| R-02 | Assessment attempt race condition allowing a learner to exceed `max_attempts` | Medium | High | Pessimistic advisory lock on `(assessment_id, enrollment_id)` acquired at attempt-creation time; attempt count re-checked inside the lock before insert; `idempotency_key` UNIQUE constraint provides a final database-level guard |
| R-03 | Duplicate certificate issuance caused by retry storms on the completion event queue | Low | High | `certificates.idempotency_key` carries a UNIQUE constraint; BullMQ job uses at-most-once delivery; failed issuance jobs land in a dead-letter queue for manual review rather than retrying indefinitely |
| R-04 | Progress event write throughput exceeds PostgreSQL capacity during simultaneous large-cohort launches | Medium | High | Progress events buffered in Redis with a 1-second flush window before bulk-upsert to PostgreSQL; reads served from replica; PgBouncer connection pooling limits connection spikes; load-tested at 10K events/min before go-live |
| R-05 | SAML assertion replay attack enabling unauthorised session creation | Low | Critical | SAML assertion `ID` stored in Redis with TTL equal to the assertion validity period (typically 5 minutes); duplicate assertion ID returns `HTTP 400 Bad Request` without issuing a token |
| R-06 | Grade override applied without a traceable audit record | Low | High | All `grade_record` inserts route through the grading service; `grade_source = 'override'` requires a non-empty `override_reason`; an `audit_log` entry is created atomically in the same database transaction as the grade insert |
| R-07 | Presigned content URL shared or reused beyond the intended learner session | Medium | Medium | Presigned URLs expire after 15 minutes; URL generated only after real-time enrollment status check; for video streams, CDN signed cookies scoped to the learner session token are used as an alternative |
| R-08 | Third-party SSO provider outage blocking all enterprise tenant logins | Low | High | Local username/password fallback credentials pre-provisioned for tenant admins; circuit breaker around SSO provider calls fails open to the fallback login form with a clear user-facing message; incident playbook includes provider support contact details |
