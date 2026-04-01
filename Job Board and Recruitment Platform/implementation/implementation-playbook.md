# Implementation Playbook — Job Board and Recruitment Platform

## Executive Summary

The Job Board and Recruitment Platform is built as a cloud-native, event-driven microservices system deployed on AWS ECS Fargate. The architecture consists of twelve independently deployable services — including dedicated services for authentication, job management, candidate applications, AI/ML resume parsing, interview scheduling, offer management, GDPR compliance, and analytics — all orchestrated within an NX 19 monorepo. Services communicate asynchronously via Apache Kafka (AWS MSK) and synchronously via REST through an API Gateway layer, ensuring both loose coupling and operational resilience.

The implementation follows a six-phase, 24-week rollout designed to deliver business value incrementally. Each phase ships a functional slice of the platform: Phase 1 establishes the infrastructure foundation and authentication; Phase 2 delivers the candidate portal and application tracking; Phase 3 introduces AI-powered resume parsing and scoring; Phase 4 adds interview scheduling with calendar integration; Phase 5 addresses compliance (GDPR, background checks) and offer management with e-signatures; and Phase 6 focuses on analytics, email campaign tooling, multi-region disaster recovery, and HRIS integrations. This sequencing ensures recruiters have a usable product from Week 8 onward, with AI augmentation layered on progressively.

The technology stack is anchored on **Node.js 20 LTS / TypeScript 5.x** (NestJS 10) for backend services, **React 18** for the recruiter portal, **React Native 0.74** for the candidate mobile app, **Prisma 5** as the ORM against Aurora PostgreSQL, and **FastAPI (Python 3.11)** for the AI/ML service. Infrastructure is fully codified in **Terraform 1.8**, with GitHub Actions providing CI/CD pipelines. OpenAI's GPT-4o and `text-embedding-3-small` models power resume parsing and semantic similarity scoring. The monorepo structure with NX enables shared TypeScript types across services, standardised build targets, and module boundary enforcement — reducing integration issues that commonly arise in polyrepo microservice architectures.

---

## Phase 1: Foundation (Weeks 1–4)

### Objectives
Establish the engineering foundation: monorepo, CI/CD, cloud infrastructure, authentication, and core job management.

### Deliverables

#### Week 1–2: Monorepo & Infrastructure Bootstrap
- Initialise NX 19 monorepo with `@nx/node`, `@nx/react`, `@nx/react-native` plugins
- Configure TypeScript 5.x strict mode (`strictNullChecks`, `noImplicitAny`, `exactOptionalPropertyTypes`)
- Set up GitHub Actions workflows: lint → test → build → push Docker image → deploy to ECS (staging)
- Terraform: VPC with public/private subnets (3 AZs), ECS Fargate cluster, ECR registries, Route 53 hosted zone, ACM SSL certificates
- Provision Aurora PostgreSQL 15 cluster (writer + 2 read replicas), ElastiCache Redis 7, MSK Kafka cluster (3 brokers)
- AWS Secrets Manager: store database credentials, JWT secrets, OAuth client secrets
- S3 buckets: resumes (private, KMS encrypted), offer-letters (private), assets (CDN-served)
- CloudWatch dashboards, alarms, X-Ray tracing enabled

#### Week 3–4: Auth Service & Job Service
- `auth-service` (NestJS): JWT RS256 access tokens (15m TTL) + refresh tokens (7d, Redis-stored), Google OAuth 2.0, LinkedIn OAuth 2.0, RBAC roles: `SUPER_ADMIN`, `HR_ADMIN`, `RECRUITER`, `HIRING_MANAGER`, `CANDIDATE`
- `job-service` (NestJS): Job CRUD, draft/published/closed state machine, approval workflow (RECRUITER → HR_ADMIN), job categories taxonomy, location + remote flags, salary range (with visibility toggle)
- Prisma schema: `User`, `Role`, `Job`, `JobApproval`, `Department`, `Location` tables with migrations
- React 18 web app shell: NX `apps/web` with React Router v6, TanStack Query, Tailwind CSS, component library setup (shadcn/ui)
- Basic recruiter dashboard: job listing, job creation form

### Acceptance Criteria — Phase 1

| Criterion | Measurement | Target |
|---|---|---|
| Authentication flows | OAuth login + JWT refresh tested | Google + LinkedIn login working |
| Job CRUD | API integration tests | 100% CRUD operations pass |
| Infrastructure as Code | `terraform plan` shows 0 drift | All resources match state |
| CI/CD pipeline | GitHub Actions green | Lint + test + deploy < 8 min |
| Database migrations | `prisma migrate deploy` runs cleanly | 0 migration errors |
| API response time (P95) | k6 baseline load test (100 RPS) | < 200ms for job listing |
| Test coverage | Jest unit tests | ≥ 80% coverage on auth + job services |

---

## Phase 2: Candidate Portal & Applications (Weeks 5–8)

### Objectives
Enable candidates to discover jobs, apply, upload resumes, and track their application status.

### Deliverables

#### Week 5–6: Application Service & Resume Upload
- `application-service` (NestJS): Application state machine (`APPLIED` → `SCREENING` → `SHORTLISTED` → `INTERVIEW` → `OFFER` → `HIRED` / `REJECTED`)
- Resume upload flow: pre-signed S3 URL generation (5-minute TTL), multipart upload support (up to 5MB PDF/DOCX), virus scanning via ClamAV Lambda trigger on S3 event
- Kafka event: `application.submitted` published on new application; `application.resume.uploaded` on upload completion
- Duplicate application detection: prevent same candidate applying to same job twice (unique constraint + 409 response)
- Cover letter support: optional text or file upload

#### Week 7–8: Candidate Portal & Notifications
- `notification-service` (NestJS + AWS SES): Email templates (application confirmation, status updates), SendGrid fallback, bounce/complaint webhook handling
- Candidate portal (`apps/candidate-web`, React 18): Job search with filters (location, remote, salary, category), job detail page, application form, application tracker ("My Applications" with status timeline)
- React Native 0.74 (`apps/candidate-mobile`): Identical job search + apply flow, push notifications via Firebase FCM
- ATS board v1: Kanban view for recruiters — columns mapped to application states, candidate cards with name + role
- `api-gateway` (NestJS): Request routing, rate limiting (100 req/min per IP for public endpoints), CORS configuration, request/response logging

### Acceptance Criteria — Phase 2

| Criterion | Measurement | Target |
|---|---|---|
| Resume upload | E2E test: upload → S3 → virus scan → status update | < 10s end-to-end |
| Application submission | Load test: 500 concurrent applications | 0 data loss, < 2s P95 |
| Notification delivery | SES delivery rate | > 98% delivery within 60s |
| Candidate portal | Lighthouse performance score | ≥ 85 on mobile |
| ATS board | Recruiter smoke test | Kanban loads < 1.5s with 100 candidates |
| Duplicate prevention | Integration test | 409 on duplicate apply |
| Mobile app | iOS + Android build | App launches + applies successfully |

---

## Phase 3: AI Resume Processing (Weeks 9–12)

### Objectives
Deploy the AI/ML resume parsing pipeline, candidate scoring, and surface AI insights to recruiters.

### Deliverables

#### Week 9–10: AI/ML Service Foundation
- `ai-service` (FastAPI, Python 3.11): Containerised on ECS with GPU task definition, spaCy `en_core_web_trf` model bundled in Docker image
- Resume parsing pipeline: `PDFExtractor` (pdfplumber + pytesseract OCR for scanned PDFs), `DocxExtractor`, `SpacyNERExtractor` (skills, experience, education, contact info)
- OpenAI `text-embedding-3-small` integration: async client, 80K TPM rate limiter, exponential backoff retry
- `BiasFilter`: PII removal (names, addresses), gender-coded word stripping before embeddings
- Kafka consumer: consumes `application.resume.uploaded`, publishes `resume.parsed`

#### Week 11–12: Scoring & Recruiter Dashboard
- `ScoringEngine`: four-dimension scoring (skill 0.35, experience 0.25, education 0.10, semantic 0.30), composite score persisted to `CandidateScore` table
- AI Score dashboard: recruiter view showing ranked candidates per job with score breakdown (skills matched/missing, experience gap, semantic label)
- Automated screening filter: HR admin can set minimum composite score threshold (e.g., 0.60) per job — applications below threshold are auto-moved to `SCREENED_OUT`
- Re-parse capability: recruiter can trigger re-parse if candidate uploads updated resume
- Score explanation panel: expandable view showing which skills matched, which were missing, experience gap, and semantic match label

### Acceptance Criteria — Phase 3

| Criterion | Measurement | Target |
|---|---|---|
| Parse accuracy | Manual review of 200 resumes | > 90% skill extraction accuracy |
| Parse latency (P95) | End-to-end Kafka to score | < 15s per resume |
| Scoring consistency | Same resume scored 3× | Variance < 0.02 on composite score |
| Bias audit | t-test on score distribution by gender proxy | No statistically significant disparity (p > 0.05) |
| Throughput | Queue drain test: 500 resumes | Fully scored within 30 minutes |
| OpenAI cost | Estimate per-parse cost | < $0.004 per resume |
| Screening filter | Automation test | Auto-moves below-threshold applications correctly |

---

## Phase 4: Interview & Collaboration (Weeks 13–16)

### Objectives
Enable structured interview scheduling, scorecards, hiring manager collaboration, and the full ATS drag-drop board.

### Deliverables

#### Week 13–14: Interview Service & Calendar Integration
- `interview-service` (NestJS): Interview creation, slot proposal, confirmation, cancellation, reschedule. States: `PROPOSED` → `CONFIRMED` → `COMPLETED` / `CANCELLED`
- Google Calendar API integration: OAuth 2.0 per recruiter, automatic calendar event creation on interview confirmation, attendee invitations, `.ics` fallback
- Outlook/Microsoft Graph API integration: same capability for organisations using Microsoft 365
- Zoom OAuth integration: auto-generate Zoom meeting links for virtual interviews, embed in calendar invite
- Interviewer assignment: up to 5 interviewers per interview round, role-based (RECRUITER, HIRING_MANAGER, PEER)

#### Week 15–16: Scorecards & ATS Board v2
- Interview scorecard system: customisable scorecard templates per job (competencies, ratings 1–5, hire recommendation Yes/Partial/No), scorecard submission with deadline enforcement
- Hiring manager collaboration: shared notes, @mention notifications, decision thread on candidate profile
- ATS drag-drop board (full): react-beautiful-dnd implementation, optimistic UI updates, WebSocket-based real-time sync across recruiter sessions, conflict resolution (last-write-wins with toast notification)
- Bulk actions: move multiple candidates, bulk reject with templated email
- Candidate timeline: full audit trail of all stage changes, interview outcomes, notes, and AI scores

### Acceptance Criteria — Phase 4

| Criterion | Measurement | Target |
|---|---|---|
| Calendar event creation | E2E: schedule → Google Calendar event created | < 5s |
| Zoom link generation | E2E: confirm interview → Zoom link in invite | Works for all interview types |
| Scorecard submission | Functional test: submit + retrieve | Score persists correctly |
| ATS drag-drop | Multi-user concurrency test (2 users) | State consistent after conflict |
| Interview count per day | Load test | 200 interviews schedulable/day |
| WebSocket sync | Test: 2 tabs update simultaneously | Update propagates < 500ms |

---

## Phase 5: Offer & Compliance (Weeks 17–20)

### Objectives
Implement the full offer lifecycle, background checks, GDPR compliance, diversity analytics, and job board syndication.

### Deliverables

#### Week 17–18: Offer Service & Background Checks
- `offer-service` (NestJS): Offer creation with multi-step approval workflow (RECRUITER → HR_ADMIN → DIRECTOR), offer letter PDF generation (Puppeteer), DocuSign eSignature integration (envelope creation, webhook callbacks), offer states: `DRAFT` → `PENDING_APPROVAL` → `APPROVED` → `SENT` → `SIGNED` → `FULLY_EXECUTED` / `DECLINED` / `RESCINDED`
- Salary approval guard: offer cannot transition to `APPROVED` until all approvers have signed off — prevents race condition via distributed lock (Redis)
- Checkr background check integration: trigger on `FULLY_EXECUTED` offers, webhook handler for `CLEAR` / `CONSIDER` / `ADVERSE_ACTION` statuses, automatic recruiter alert on `CONSIDER`
- Offer expiry: configurable signing deadline (default 5 days), automated reminder emails at D-2 and D-1, auto-expire via scheduled job

#### Week 19–20: GDPR, Diversity & Integrations
- `gdpr-service` (NestJS): GDPR Article 17 erasure request handling (with legal hold check), Article 15 data export (JSON export of all candidate data), consent management (marketing emails opt-in/out), data retention policies (auto-delete stale applications after 12 months)
- Diversity analytics dashboard: EEO voluntary self-identification form (race, gender, disability, veteran status), funnel conversion rates by demographic group (anonymised, aggregate-only display), disparate impact analysis with statistical significance indicator
- `integration-service` (NestJS): LinkedIn Job Posting API (create/update/close jobs), Indeed Job Feed (XML sitemap), Glassdoor Company Connect API, webhook registry for outbound integrations
- Email campaign system (sourcing outreach): template builder, segment definition (skills, location, experience level), send scheduling, open/click tracking via SendGrid webhooks

### Acceptance Criteria — Phase 5

| Criterion | Measurement | Target |
|---|---|---|
| DocuSign envelope delivery | E2E test | Envelope delivered < 30s after send |
| Approval workflow | Race condition test (concurrent approvals) | Only one offer sent if not all approved |
| Background check webhook | Checkr mock webhook test | Status updates correctly in < 60s |
| GDPR erasure | Erasure request E2E | All PII deleted (verified by data export) |
| Legal hold block | Test erasure on held record | Erasure blocked with correct reason |
| LinkedIn syndication | API integration test | Job posted to LinkedIn < 2 min |
| Diversity dashboard | Data anonymity test | No individual records exposed |

---

## Phase 6: Analytics & Scale (Weeks 21–24)

### Objectives
Deliver operational analytics, validate platform scale, harden security, and enable multi-region DR and HRIS integrations.

### Deliverables

#### Week 21–22: Analytics Service & Email Campaigns
- `analytics-service` (NestJS + Kafka streams): Time-to-hire (days from application to offer accepted), funnel conversion rates by stage, source ROI (LinkedIn vs Indeed vs direct vs referral), recruiter productivity metrics, offer acceptance rate, pipeline velocity
- Pre-built dashboards: Executive summary (time-to-hire trend), Recruiter dashboard (open pipeline, upcoming interviews), Source effectiveness chart
- Email campaign system completion: A/B testing support, unsubscribe compliance (CAN-SPAM / GDPR), campaign analytics (open rate, click rate, reply rate, conversion to application)

#### Week 23–24: Scale, Security & DR
- Load testing: k6 scripts targeting 10,000 concurrent candidates (job search, apply, resume upload), validate auto-scaling ECS task count, validate Aurora read replica offloading
- Security penetration testing: OWASP Top 10 checklist, dependency vulnerability scan (`npm audit`, `safety check` for Python), IAM least-privilege audit, S3 bucket policy review
- Multi-region DR: Terraform replication to `us-west-2`, Aurora Global Database replication (RPO < 5min), Route 53 health-check failover policy, runbook for manual failover
- HRIS integrations: Workday RAAS integration (new hire data push on `FULLY_EXECUTED` offers), BambooHR API (employee record creation), Merge.dev unified HRIS API as fallback
- Production readiness review: final performance baseline, alert threshold tuning, on-call runbook completion

### Acceptance Criteria — Phase 6

| Criterion | Measurement | Target |
|---|---|---|
| Load test: 10K concurrent | k6 peak load run | P95 < 2s, error rate < 0.1% |
| Auto-scaling | ECS scale-out during load test | Tasks scale within 3 minutes |
| Security pen test | Findings count | 0 critical, 0 high findings |
| DR failover time | Simulated regional failure | RTO < 30 minutes |
| Analytics accuracy | Time-to-hire calculation spot check | < 1-day variance from manual count |
| HRIS push | Workday new hire push E2E | Record created < 5 min after offer accepted |
| Campaign compliance | Unsubscribe E2E test | Removed from segment within 1 hour |

---

## Team Composition

| Role | Count | Responsibilities |
|---|---|---|
| Tech Lead | 1 | Architecture decisions, PR reviews, cross-team coordination, ADR authorship |
| Backend Engineers | 4 | Microservice development (NestJS/TypeScript), Kafka consumers/producers, Prisma migrations, API design |
| ML Engineer | 1 | FastAPI AI service, spaCy NER pipeline, OpenAI integration, scoring algorithm, bias testing |
| Frontend Engineers | 2 | React 18 recruiter portal, React Native mobile app, ATS board, candidate portal |
| DevOps/Platform Engineer | 1 | Terraform, GitHub Actions CI/CD, ECS task definitions, MSK/Aurora provisioning, observability |
| QA Engineer | 1 | Test strategy, E2E test suite (Playwright), load testing (k6), regression suite |
| Product Manager | 1 | Sprint planning, stakeholder communication, acceptance criteria definition, UAT coordination |
| **Total** | **11** | |

---

## Technology Decisions Log (ADRs)

| Decision | Chosen | Alternatives Considered | Rationale |
|---|---|---|---|
| ADR-001: Backend Framework | NestJS 10 | Express.js, Fastify, Hono | NestJS provides first-class DI, decorators-based routing, modular architecture, and built-in support for Kafka, Redis, and Prisma via community modules — reducing boilerplate and enforcing structure across 12 services |
| ADR-002: Event Streaming | Apache Kafka (AWS MSK) | AWS SQS/SNS, RabbitMQ | Kafka provides ordered, durable, replayable event streams essential for ATS state machine audits and resume.parsed → downstream fan-out. SQS lacks consumer group replay. Kafka partitions allow parallel processing per job_id |
| ADR-003: AI Service Language | FastAPI (Python 3.11) | NestJS with TensorFlow.js | Python has a vastly superior ML ecosystem (spaCy, transformers, numpy). FastAPI's async support and Pydantic validation make it production-suitable. Running Python AI service alongside TypeScript services is a well-understood polyglot pattern |
| ADR-004: Primary Database | Aurora PostgreSQL 15 | MongoDB Atlas, DynamoDB | ATS pipeline data is highly relational (jobs → applications → interviews → offers → candidates). PostgreSQL's JSONB support handles semi-structured data (scorecard responses). Aurora provides managed HA + read replicas without operational overhead |
| ADR-005: ORM | Prisma 5 | TypeORM, Drizzle, raw pg | Prisma's type-safe client generation from schema eliminates an entire class of runtime SQL errors. Migration workflow integrates cleanly with CI/CD. Prisma Studio accelerates local debugging. Performance is acceptable for our query patterns |
| ADR-006: Repository Structure | NX 19 Monorepo | Polyrepo (one repo/service) | Shared TypeScript types across 12 services (e.g., `ApplicationStatus` enum) prevent contract drift. NX's affected-build optimisation runs only changed service pipelines. Module boundaries enforced via `@nx/enforce-module-boundaries` lint rule |

---

## Risk Register

| # | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| R-01 | **OpenAI API cost overrun** — high resume volume (100K/month) with GPT-4o and embeddings exceeds budget | Medium | High | Use `text-embedding-3-small` (not GPT-4o) for all scoring. GPT-4o only for structured data extraction from complex resumes. Implement per-job cost caps. Cache embeddings for identical job descriptions. Set AWS Budget alert at 80% of monthly OpenAI allocation |
| R-02 | **LinkedIn API rate limits** — LinkedIn's Job Posting API limits to 500 requests/day per app | High | Medium | Implement request queue with debounce. Batch job updates. Cache LinkedIn job IDs for updates vs creates. Apply for elevated rate limit tier. Implement graceful degradation: queue failed posts for next-day retry |
| R-03 | **GDPR compliance complexity** — multi-jurisdiction data residency, right-to-erasure conflicting with audit trail requirements | Low | Critical | Engage Data Protection Officer from project start. Implement pseudonymisation (not anonymisation) for audit logs. Legal hold mechanism blocks erasure on disputed applications. GDPR service tested by independent DPA counsel before Phase 5 go-live |
| R-04 | **Resume parsing accuracy below 90% threshold** — spaCy NER misses non-standard resume formats | Medium | High | Curate test dataset of 500 diverse resume formats before Phase 3. Implement confidence scoring; flag low-confidence parses for manual review. Fallback to GPT-4o structured extraction for < 0.7 confidence resumes (with cost guard). Continuous model evaluation pipeline |
| R-05 | **Calendar OAuth token refresh failures** — Google/Microsoft refresh tokens expire after 30 days of inactivity | High | Medium | Proactive token refresh every 25 days via background job. Detect 401 responses and prompt re-authorization via in-app notification. Store token expiry metadata and alert recruiters 3 days before expiry |
| R-06 | **DocuSign SLA dependency** — platform offer workflow completely blocked if DocuSign API is degraded | Low | High | Implement circuit breaker on DocuSign client (Hystrix pattern). Fallback: allow email-based offer acceptance with manual DocuSign re-send later. Monitor DocuSign status page via synthetic monitoring |
| R-07 | **AI bias in resume scoring** — scoring model produces disparate impact on protected groups | Medium | Critical | BiasFilter strips names, addresses, gender-coded words before embeddings. Quarterly disparate impact analysis (80% rule). Score distributions audited by demographic proxies. Human review required for all auto-screened-out candidates. Scoring model version-controlled for full auditability |
| R-08 | **Kafka consumer rebalance during deployment** — rolling ECS deployment triggers consumer group rebalances causing message processing delays | High | Medium | Use `cooperative-sticky` partition assignment strategy. Set `session.timeout.ms` to 45s. Implement idempotent consumers (deduplication by event ID). Monitor consumer group lag in CloudWatch |
| R-09 | **Multi-tenant data isolation failure** — a query bug returns candidates from the wrong company | Low | Critical | Row-Level Security (RLS) on all candidate/application tables in PostgreSQL, enforced at the database layer independent of application code. Automated test suite: cross-tenant data leakage tests run on every PR |
| R-10 | **React Native app store rejection** — Apple/Google reject due to data privacy policy, tracking, or UI guideline violations | Medium | Medium | Privacy manifest compliance for iOS 17+ (`NSPrivacyAccessedAPITypes`). No third-party analytics SDKs in mobile app. Dedicated app store submission checklist in Phase 2 acceptance criteria. 2-week buffer before Phase 2 deadline for resubmission |

---

## Definition of Done

| Phase | Criteria |
|---|---|
| **Phase 1** | ✅ All Terraform resources created and state clean · ✅ Auth service passes OWASP auth tests · ✅ Job CRUD + approval workflow E2E tests green · ✅ GitHub Actions pipeline deploys to staging automatically · ✅ ≥ 80% test coverage on all Phase 1 services |
| **Phase 2** | ✅ Candidate can search, apply, and track application in web + mobile · ✅ Resume upload → virus scan → S3 storage E2E working · ✅ ATS Kanban board functional for recruiters · ✅ Notification emails delivered via SES with > 98% delivery rate · ✅ API Gateway rate limiting verified |
| **Phase 3** | ✅ AI service parses resumes with > 90% skill extraction accuracy · ✅ Composite score computed and stored for all applications · ✅ Bias audit passes (no statistically significant disparate impact) · ✅ Scoring explainability panel visible to recruiters · ✅ Auto-screening filter operational |
| **Phase 4** | ✅ Interview scheduled with Google/Outlook calendar event created · ✅ Zoom link auto-generated for virtual interviews · ✅ Scorecard submitted and retrievable · ✅ ATS drag-drop board syncs across 2+ concurrent users · ✅ Hiring manager can collaborate on candidate decisions |
| **Phase 5** | ✅ DocuSign offer envelope delivered and status webhooks working · ✅ Background check webhook updating offer record · ✅ GDPR erasure removes all PII (verified by data export) · ✅ LinkedIn syndication posts job within 2 minutes · ✅ Diversity dashboard showing aggregate EEO data |
| **Phase 6** | ✅ k6 load test: 10K concurrent, P95 < 2s, error rate < 0.1% · ✅ Zero critical/high findings from pen test · ✅ Multi-region DR failover tested with RTO < 30 min · ✅ Workday/BambooHR integration delivers new hire on offer acceptance · ✅ Production on-call runbook complete and reviewed by team |

---

## Appendix: Key Kafka Topics

| Topic | Producer | Consumers | Purpose |
|---|---|---|---|
| `application.submitted` | application-service | ats-service, notification-service | New application created |
| `application.resume.uploaded` | application-service | ai-service | Resume file ready for parsing |
| `resume.parsed` | ai-service | application-service, analytics-service | Parsing + scoring complete |
| `stage.changed` | ats-service | notification-service, analytics-service | ATS pipeline stage updated |
| `interview.scheduled` | interview-service | notification-service, calendar (via integration-service) | Interview confirmed |
| `interview.completed` | interview-service | ats-service, analytics-service | Interview outcome recorded |
| `offer.sent` | offer-service | notification-service, background-check (via integration-service) | Offer dispatched via DocuSign |
| `offer.accepted` | offer-service | notification-service, hris (via integration-service) | Candidate signed offer |
| `background-check.updated` | integration-service | offer-service, notification-service | Checkr result received |
| `gdpr.erasure.requested` | gdpr-service | All services (fan-out) | PII deletion across all services |

---

## Appendix: Environment Topology

| Environment | Purpose | ECS Cluster Size | Database |
|---|---|---|---|
| `dev` | Developer feature testing | 1 task/service, shared | Aurora Serverless v2 (auto-pause) |
| `staging` | QA, integration tests, UAT | 2 tasks/service | Aurora t3.medium (1 writer) |
| `production` | Live traffic | 2–10 tasks/service (auto-scale) | Aurora r6g.large (1 writer + 2 replicas) |
| `dr` (us-west-2) | Disaster recovery standby | 0 tasks (cold), scales on failover | Aurora Global Database secondary |
