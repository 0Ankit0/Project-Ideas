# Implementation Playbook — Survey and Feedback Platform

## Overview

This playbook defines the 28-week delivery plan for the Survey and Feedback Platform across five sequential phases. Each phase produces shippable, tested software and ends with explicit acceptance criteria signed off by the Product Manager and QA Engineer.

| Phase | Weeks | Focus Area | Key Output |
|-------|-------|------------|------------|
| 1 | 1–4 | Foundation & Infrastructure | Auth service, IaC, CI/CD |
| 2 | 5–10 | Core Survey Builder | Survey CRUD, 12 question types, builder UI |
| 3 | 11–16 | Distribution & Collection | Email campaigns, embed widget, offline PWA |
| 4 | 17–22 | Analytics & Reporting | Kinesis pipeline, real-time dashboard, exports |
| 5 | 23–28 | Integrations & Hardening | Webhooks, billing, load testing, GDPR audit |

**Total Timeline:** 28 weeks (7 months) | **Team Size:** 8 engineers + 1 PM | **Methodology:** Agile, 2-week sprints

---

## Phase 1: Foundation (Weeks 1–4)

### 1.1 Infrastructure Setup

Provision all AWS infrastructure as Infrastructure-as-Code using Terraform. No manual console configuration is permitted in any environment. All resources must be tagged with `project`, `env`, and `owner`.

**Terraform Modules:**
- `modules/vpc` — VPC with public/private subnets across 3 AZs, NAT Gateway, Internet Gateway, VPC Flow Logs
- `modules/ecs` — ECS Fargate cluster, task definitions, service auto-scaling (CPU and memory policies)
- `modules/rds` — RDS PostgreSQL 15 Multi-AZ, custom parameter group (pgvector enabled), subnet group, automated snapshots
- `modules/elasticache` — Redis 7 cluster mode, subnet group, auth token rotation via Secrets Manager
- `modules/s3` — Buckets for assets, exports, and backups with versioning, SSE-KMS, and lifecycle rules
- `modules/cloudfront` — CDN distribution with WAF association, custom error pages, Origin Access Control
- `modules/route53` — Hosted zone, A/ALIAS records, health checks with failover routing
- `modules/iam` — ECS task execution roles, OIDC provider for GitHub Actions, least-privilege policy documents
- `modules/secrets` — AWS Secrets Manager secrets for DB credentials, API keys, and JWT signing keys

**Environment Strategy:**

| Environment | AZs | RDS | ECS Min/Max | WAF |
|-------------|-----|-----|-------------|-----|
| dev | 1 | Single-AZ t3.medium | 1 / 2 | Disabled |
| staging | 2 | Single-AZ t3.large | 1 / 4 | Rules enabled, count mode |
| production | 3 | Multi-AZ r6g.large | 2 / 10 | Enabled, block mode |

### 1.2 CI/CD Pipeline

**GitHub Actions Workflow (`.github/workflows/api.yml`):**
1. **Test** — `pytest` with `--cov` enforcing ≥80% coverage threshold; `mypy --strict`; `ruff check`
2. **Build** — Docker multi-stage build (builder + runtime), push to Amazon ECR tagged with commit SHA and `latest`
3. **Security Scan** — Trivy container scan; pipeline fails on CRITICAL or HIGH CVEs
4. **Deploy Staging** — `aws ecs update-service --force-new-deployment` on every push to `main`
5. **Deploy Production** — Manual approval via GitHub Environments; ECS rolling deployment with health-check rollback

**Branch Protection Rules:**
- `main`: 2 approved reviews required; all status checks must pass; no force push
- Stale review dismissal on new commits is enabled

### 1.3 Auth Service Implementation

**JWT Configuration:**
- Access tokens: RS256, 15-minute expiry, claims include `sub`, `workspace_id`, `plan_tier`
- Refresh tokens: HS256, 7-day expiry, stored in Redis (`refresh:{jti}`) with atomic revocation
- Rotation: each refresh call issues a new refresh token; old token is immediately invalidated

**OAuth 2.0 Flows:**
- Google: authorization_code + PKCE; scopes: `openid email profile`
- Microsoft Azure AD v2: same flow; scopes: `openid email profile offline_access`
- Callback: `/auth/callback/{provider}` — validates state nonce from Redis (5-minute TTL, single-use)

**Magic Link:**
- 32-byte CSPRNG token, stored as SHA-256 hash in Redis with 10-minute TTL
- Single-use: Redis `GETDEL` atomically retrieves and deletes in one operation
- Delivered via SendGrid transactional template

### 1.4 Basic User and Workspace CRUD

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/register` | POST | Email + password registration, returns token pair |
| `/auth/login` | POST | Credential validation, returns token pair |
| `/auth/refresh` | POST | Refresh token rotation |
| `/auth/magic-link` | POST | Request passwordless link |
| `/auth/magic-link/verify` | GET | Consume link, return token pair |
| `/users/me` | GET | Current user profile |
| `/users/me` | PATCH | Update display name, avatar, timezone |
| `/workspaces` | POST | Create workspace with default Owner role |
| `/workspaces/{id}` | GET | Workspace details, member list |
| `/workspaces/{id}/members` | POST | Invite member by email, assign role |
| `/workspaces/{id}/members/{uid}` | PATCH | Update member role (Owner/Admin/Editor/Viewer) |
| `/workspaces/{id}/members/{uid}` | DELETE | Remove member |

### Phase 1 Deliverables

| Deliverable | Owner | Due Week |
|-------------|-------|----------|
| Terraform modules applied to dev and staging | DevOps | 2 |
| GitHub Actions pipeline green for all services | DevOps | 2 |
| Auth service: JWT + OAuth 2.0 + magic link | Backend Engineer 1 | 3 |
| User/Workspace CRUD endpoints + unit tests | Backend Engineer 2 | 4 |
| OpenAPI docs auto-generated and accessible | Backend Engineer 1 | 4 |
| Staging environment operational and smoke-tested | DevOps + QA | 4 |

### Phase 1 Acceptance Criteria

- [ ] All Terraform modules pass `terraform validate` and `terraform plan` with zero errors across all environments
- [ ] GitHub Actions pipeline completes end-to-end in under 8 minutes on a cold run
- [ ] JWT access token expiry is enforced; expired tokens return HTTP 401
- [ ] Refresh token rotation prevents replay: a used refresh token is rejected on second use
- [ ] Google and Microsoft OAuth flows complete successfully in staging environment
- [ ] Magic links expire after 10 minutes and cannot be reused (returns 410 Gone)
- [ ] Workspace role enforcement: Viewer cannot create surveys (returns 403)
- [ ] Test coverage ≥80% for auth service; zero mypy errors
- [ ] Trivy scan shows zero CRITICAL or HIGH CVEs in the API container image

---

## Phase 2: Core Survey Builder (Weeks 5–10)

### 2.1 Survey and Question CRUD APIs

Survey lifecycle states: `draft → published → closed → archived`. State transitions are validated server-side; invalid transitions return HTTP 409.

**Survey Endpoints:** `POST /surveys`, `GET /surveys` (paginated), `GET /surveys/{id}`, `PATCH /surveys/{id}`, `DELETE /surveys/{id}` (soft delete), `POST /surveys/{id}/duplicate`, `POST /surveys/{id}/publish`, `POST /surveys/{id}/close`, `GET /surveys/{id}/versions`

**Question Endpoints:** `POST /surveys/{id}/questions`, `PATCH /surveys/{id}/questions/{qid}`, `DELETE /surveys/{id}/questions/{qid}`, `POST /surveys/{id}/questions/reorder` (accepts ordered ID array)

### 2.2 All 12 Question Types

| # | Type Key | Storage Column | Validation |
|---|----------|---------------|------------|
| 1 | `single_choice` | `answer_text` (option ID) | Must be valid option ID from question definition |
| 2 | `multiple_choice` | `answer_json` (ID array) | Min/max selection count enforced |
| 3 | `rating` | `answer_numeric` | Integer within scale range (1–5 or 1–10) |
| 4 | `nps` | `answer_numeric` | Integer 0–10; no custom options allowed |
| 5 | `short_text` | `answer_text` | Max 500 characters |
| 6 | `long_text` | `answer_text` | Max 10,000 characters |
| 7 | `datetime` | `answer_text` (ISO 8601) | Valid date; optional min/max date constraint |
| 8 | `file_upload` | `answer_json` (S3 key array) | Max 10 MB per file; allowed MIME types configured |
| 9 | `matrix` | `answer_json` (row→choice map) | All required rows must be answered |
| 10 | `slider` | `answer_numeric` | Value within min/max; step divisibility checked |
| 11 | `ranking` | `answer_json` (ordered ID array) | All items present; no duplicates |
| 12 | `signature` | `answer_text` (S3 key) | Valid S3 key referencing an uploaded PNG/SVG |

### 2.3 Conditional Logic Engine

Rules are stored as JSONB in `questions.conditions`. Server-side evaluation is the authoritative truth; the React client replicates logic for UX only.

**Supported Operators:** `equals`, `not_equals`, `contains`, `not_contains`, `greater_than`, `less_than`, `greater_than_or_equal`, `less_than_or_equal`, `is_answered`, `is_skipped`

**Group Logic:** `AND` / `OR` groups supported with nesting up to 2 levels. Actions: `show_question`, `hide_question`, `skip_to_page`, `end_survey`.

### 2.4 Frontend: React Survey Builder

**Components:**
- `SurveyBuilder` — three-panel layout: question palette | canvas | properties panel
- `QuestionPalette` — categorized list of 12 question types; drag source via `@dnd-kit/draggable`
- `QuestionCanvas` — sortable drop zone using `@dnd-kit/sortable` with animated reorder
- `QuestionCard` — inline-editable card showing type icon, title, and required badge
- `PropertiesPanel` — right panel renders type-specific settings component
- `ConditionalLogicEditor` — visual rule builder with condition rows, group toggles, and action selectors
- `SurveyPreviewModal` — full-screen modal rendering the actual response form

**Auto-Save:** Zustand `isDirty` flag triggers a debounced (1500ms) `PATCH /surveys/{id}` call.

### Phase 2 Deliverables

| Deliverable | Owner | Due Week |
|-------------|-------|----------|
| Survey + Question CRUD API with validation | Backend Engineer 1 | 6 |
| All 12 question type validators + tests | Backend Engineer 2 | 7 |
| Conditional logic engine (server-side evaluation) | Backend Engineer 1 | 8 |
| Survey Builder React components (palette, canvas) | Frontend Engineer 1 | 9 |
| Drag-and-drop reorder with persistence | Frontend Engineer 2 | 9 |
| ConditionalLogicEditor UI | Frontend Engineer 1 | 10 |
| Survey preview modal + publish flow | Frontend Engineer 2 | 10 |

### Phase 2 Acceptance Criteria

- [ ] All 12 question types accept valid answers, reject invalid answers with descriptive errors
- [ ] Conditional logic correctly evaluates all 10 operator types in server-side unit tests
- [ ] `POST /surveys/{id}/publish` rejects surveys with zero questions or broken logic references
- [ ] Drag-and-drop reorder persists correctly after browser refresh
- [ ] Survey Builder renders without console errors on Chrome, Firefox, Safari, and Edge
- [ ] Auto-save triggers within 2 seconds of any change; a "Saved" indicator appears in the UI
- [ ] API p95 response time <200ms for Survey CRUD under 50 concurrent users (k6 spot test)

---

## Phase 3: Distribution and Collection (Weeks 11–16)

### 3.1 Email Campaign System

**SendGrid Integration:**
- API v3 via `sendgrid-python`; dynamic templates stored per workspace
- Custom domain authentication (DKIM, SPF, DMARC) configured per sending domain
- Webhook receiver at `POST /webhooks/sendgrid` processes delivery, bounce, unsubscribe, and spam events
- Idempotency: each email send records a `send_id` to prevent duplicate sends on worker retry

**Celery Workers:**
- `send_survey_campaign` — fan-out: creates per-recipient `send_survey_email` subtasks
- `send_survey_email` — personalized send with recipient name and unique survey link
- `process_email_event` — updates `contact_sends` table from SendGrid webhook payload
- Worker concurrency: 10 per ECS task; auto-scaled at SQS queue depth >500

### 3.2 Audience Management and Contact Import

- CSV import: async Celery task `process_contact_import`; max 50,000 rows per file
- Columns: `email` (required), `first_name`, `last_name`, `phone`, custom attributes (JSONB)
- Deduplication: case-insensitive email comparison within the workspace
- Audience segmentation: filter rules stored as JSONB; segments re-evaluated on campaign send
- Suppression list: unsubscribed contacts are excluded at send time, never deleted

### 3.3 Embed Widget

- Pure Vanilla JS, zero runtime dependencies, ≤2 KB gzip
- Modes: `inline`, `popup` (on delay/scroll/exit-intent), `slide-in`, `fullscreen`
- Initialized via `<script data-survey-id="xxx" src="https://cdn.surveyplatform.io/widget.js"></script>`
- PostMessage API for host page: `surveyCompleted`, `surveyClosed`, `surveyLoaded` events
- CSP-friendly: no inline scripts; supports `nonce` attribute on the script tag

### 3.4 Response Collection and Offline Support

**Collection Endpoints:**
- `POST /r/{slug}/start` — create session, return signed session token (JWT, 7-day expiry)
- `POST /r/{slug}/answers` — batch answer submission, supports partial save mid-survey
- `POST /r/{slug}/complete` — finalize session; triggers Kinesis event
- `GET /r/{slug}/resume/{token}` — retrieve partial session state for continuation

**Offline PWA:**
- Service Worker caches survey definition JSON on first `start` call
- Answers queued in IndexedDB when offline; Background Sync API triggers upload on reconnect
- Conflict resolution: server session `updated_at` timestamp wins; client notified via response body

**Deduplication:**
- Per-survey configurable window (1 hour to 30 days)
- Signals: IP address, email (if collected), browser fingerprint (canvas + UA hash)
- Redis sorted set per signal; ZADD with score = unix timestamp; ZRANGEBYSCORE for lookups

### Phase 3 Deliverables

| Deliverable | Owner | Due Week |
|-------------|-------|----------|
| SendGrid integration + campaign send API | Backend Engineer 2 | 12 |
| Celery email workers + retry logic | Backend Engineer 2 | 12 |
| Contact import (CSV, async, deduplication) | Backend Engineer 1 | 13 |
| Embed widget JS bundle (≤2 KB gzip) | Frontend Engineer 2 | 14 |
| QR code generation + S3 storage | Backend Engineer 1 | 14 |
| Partial response save and resume API | Backend Engineer 2 | 15 |
| Offline PWA (Service Worker + IndexedDB) | Frontend Engineer 1 | 15 |
| Response deduplication (Redis) | Backend Engineer 1 | 16 |

### Phase 3 Acceptance Criteria

- [ ] Campaign of 10,000 emails completes under 2 minutes with 2 worker ECS tasks running
- [ ] SendGrid delivery/bounce events update contact send status within 30 seconds
- [ ] CSV import of 50,000 contacts completes under 5 minutes; duplicates are skipped with a count in the job result
- [ ] Embed widget bundle measures ≤2 KB gzip via `gzip -c widget.js | wc -c`
- [ ] Partial response resumes with all previously entered answers intact after browser close
- [ ] Offline answers upload within 10 seconds of network reconnection
- [ ] Duplicate respondent (same IP within window) receives a "You have already responded" page

---

## Phase 4: Analytics and Reporting (Weeks 17–22)

### 4.1 Kinesis → Lambda → DynamoDB Pipeline

- `ResponseCompletedEvent` published to Kinesis Data Stream `response-events` on session completion
- Lambda consumer: batch size 100, parallelization factor 2, bisect-on-error enabled
- DynamoDB table `SurveyMetrics`: partition key `survey_id`, sort key `date#hour` (e.g., `2025-01-15#14`)
- Aggregated fields: `response_count`, `completion_rate`, `avg_time_seconds`, `nps_score`, `csat_score`
- DLQ: SQS queue `analytics-dlq` receives failed batches; alert triggers if depth >10

### 4.2 NPS, CSAT, and Sentiment Analytics

- **NPS Formula:** `((Promoters − Detractors) / Total) × 100`; Promoters = 9–10, Passives = 7–8, Detractors = 0–6
- **CSAT Formula:** `(Satisfied responses / Total responses) × 100`; satisfied = top 2 of scale
- **Sentiment:** AWS Comprehend `detect_sentiment` for open-text fields; results cached in DynamoDB
- **Word Cloud:** TF-IDF extraction via `scikit-learn` TfidfVectorizer; top 50 keywords returned as JSON

### 4.3 Real-Time Dashboard

- WebSocket: `GET /ws/surveys/{id}/metrics` — server sends metric update on each `ResponseCompletedEvent`
- SSE fallback: `GET /surveys/{id}/metrics/stream` for environments blocking WebSocket
- React dashboard uses Recharts: bar chart (responses per day), line chart (NPS trend), pie chart (sentiment split), NPS gauge component
- Dashboard auto-refreshes on tab focus using `document.visibilitychange`

### 4.4 Report Generation

| Format | Library | Notes |
|--------|---------|-------|
| PDF | WeasyPrint | Custom CSS template; header/footer with survey title and page number |
| Excel | openpyxl | Separate sheet per question type; conditional formatting for NPS bands |
| CSV | Python stdlib | RFC 4180, UTF-8 BOM for Excel compatibility |
| Scheduled | Celery Beat | Daily/weekly/monthly; delivered via SendGrid to configured recipients |

Cross-tabulation engine: compare any response field against any demographic or question answer; results returned as a 2D matrix JSON for frontend rendering.

### Phase 4 Deliverables

| Deliverable | Owner | Due Week |
|-------------|-------|----------|
| Kinesis stream + Lambda consumer deployed | Backend 1 + DevOps | 18 |
| DynamoDB metrics table + TTL policy | Backend Engineer 1 | 18 |
| NPS/CSAT calculation service + unit tests | Backend Engineer 2 | 19 |
| AWS Comprehend sentiment integration | Backend Engineer 2 | 20 |
| WebSocket real-time metrics API | Backend Engineer 1 | 20 |
| Recharts dashboard components | Frontend Engineers 1 + 2 | 21 |
| PDF/Excel/CSV export endpoints | Backend Engineer 2 | 22 |
| Scheduled reports via Celery Beat | Backend Engineer 1 | 22 |

### Phase 4 Acceptance Criteria

- [ ] Kinesis pipeline processes 1,000 events/second without dropped records (measured by `GetRecords.IteratorAgeMilliseconds` CloudWatch metric)
- [ ] Lambda DLQ depth remains zero under sustained 500 events/second for 30 minutes
- [ ] NPS score matches manual calculation to 2 decimal places across 10 test datasets
- [ ] WebSocket dashboard reflects completed response within 2 seconds of submission
- [ ] PDF report for a 500-response survey generates in under 10 seconds
- [ ] Excel export correctly handles Unicode characters and all 12 question types

---

## Phase 5: Integrations and Hardening (Weeks 23–28)

### 5.1 Webhook Delivery System

- Webhook registration: URL, event types, secret (HMAC-SHA256 signature header `X-Signature-256`)
- Delivery via `DeliverWebhookTask`: max 5 retries, exponential backoff (1s, 2s, 4s, 8s, 16s)
- Delivery log retained 30 days; UI shows status, HTTP response code, and latency
- Supported events: `response.completed`, `survey.published`, `survey.closed`, `contact.unsubscribed`

### 5.2 Third-Party Integrations

| Integration | Auth Method | Key Capability |
|-------------|-------------|----------------|
| Zapier | API Key | REST Hook trigger on `response.completed`; polling fallback |
| HubSpot | OAuth 2.0 | Sync contacts; submit response data as HubSpot form submission |
| Salesforce | OAuth 2.0 JWT | Push responses as Lead or Case records via REST API |
| Slack | OAuth Token | Post response digest to channel; instant alert on low NPS |

### 5.3 Developer REST API and Billing

**External API:** API key authentication (workspace-scoped); versioning at `/api/v1/`; rate limit 1,000 req/minute per key; `Retry-After` header on 429 responses; OpenAPI 3.1 spec published at `/api/v1/docs`.

**Stripe Billing:**

| Feature | Free | Pro | Business | Enterprise |
|---------|------|-----|----------|------------|
| Surveys | 3 | 25 | Unlimited | Unlimited |
| Responses/month | 100 | 1,000 | 10,000 | Custom |
| Team members | 1 | 5 | 20 | Custom |
| API access | No | No | Yes | Yes |
| Custom domain | No | No | Yes | Yes |

Feature gating via FastAPI `Depends(require_plan("business"))` — checks `workspace.plan_tier` and raises HTTP 402 with `upgrade_url`.

### 5.4 Security Hardening

- **WAF:** OWASP Core Rule Set (managed), rate-based rule (2,000 req per 5 min per IP), geo-blocking for sanctioned regions
- **Penetration Testing:** Bugcrowd private program; CRITICAL findings remediated within 7 days, HIGH within 30 days
- **k6 Load Tests:** Baseline (500 VU, 10,000 RPM for 10 min); soak (300 VU for 2 hours); spike (0→1,000 VU in 30s)
- **GDPR/CCPA:** Data subject request endpoints `GET /users/me/data` and `DELETE /users/me/data`; consent logs in PostgreSQL; data retention enforced by `pg_cron` scheduled deletion job

### Phase 5 Deliverables

| Deliverable | Owner | Due Week |
|-------------|-------|----------|
| Webhook delivery system + UI logs | Backend Engineer 2 | 24 |
| Zapier integration | Backend Engineer 1 | 24 |
| HubSpot + Salesforce integrations | Backend Engineers 1 + 2 | 25 |
| Slack integration | Backend Engineer 1 | 25 |
| External REST API + API key management | Backend Engineer 2 | 25 |
| Stripe billing + webhook handlers | Backend Engineer 2 | 26 |
| Feature gating middleware | Backend Engineer 1 | 26 |
| WAF rules + pen test scope | DevOps | 27 |
| k6 load test suites (all 3 scenarios) | QA Engineer | 27 |
| Pen test findings remediated | All engineers | 28 |
| GDPR audit passed, DSR endpoints verified | PM + Backend | 28 |

### Phase 5 Acceptance Criteria

- [ ] Webhook delivery achieves ≥99.9% success rate across 10,000 test deliveries
- [ ] Failed webhooks retry with visible exponential delay in the delivery log
- [ ] Zapier trigger fires within 30 seconds of a response being submitted
- [ ] External API returns HTTP 429 with `Retry-After` header when rate limit is exceeded
- [ ] Stripe plan downgrade immediately removes access to gated features
- [ ] k6 baseline test: p95 API response time <500ms at 500 concurrent virtual users
- [ ] WAF blocks automated SQLi and XSS payloads from OWASP test suite (zero bypass)
- [ ] Data subject deletion removes all PII from PostgreSQL, MongoDB, and S3 within 30 days

---

## Team Structure

| Role | Count | Primary Responsibilities |
|------|-------|--------------------------|
| Lead Architect | 1 | System design, ADRs, cross-service technical decisions, final code review sign-off |
| Backend Engineer | 2 | FastAPI services, Celery workers, Lambda functions, database schema design |
| Frontend Engineer | 2 | React components, TypeScript, Zustand stores, Recharts dashboards, PWA |
| DevOps Engineer | 1 | Terraform IaC, GitHub Actions, ECS/RDS/Redis ops, CloudWatch + Datadog monitoring |
| QA Engineer | 1 | Test plans, Playwright E2E tests, k6 load tests, regression suites, pen test coordination |
| Product Manager | 1 | Backlog grooming, stakeholder communication, acceptance criteria sign-off |

**RACI Matrix:**

| Activity | Lead Arch | Backend | Frontend | DevOps | QA | PM |
|----------|-----------|---------|----------|--------|----|----|
| Architecture decisions | R/A | C | C | C | I | I |
| Feature implementation | C | R/A | R/A | I | I | I |
| Infrastructure changes | A | I | I | R | I | I |
| Test sign-off | I | C | C | I | R/A | I |
| Release to production | A | C | C | C | C | R |
| GDPR/compliance tasks | A | R | I | C | C | R |

---

## Definition of Done

A story or feature is considered **Done** when all of the following conditions are met:

- [ ] Code reviewed and approved by at least 1 engineer (2 approvals required for auth, billing, and data deletion paths)
- [ ] Unit test coverage ≥80% for all new code in the changeset
- [ ] Integration tests pass for all affected endpoints
- [ ] `mypy --strict` passes with zero errors
- [ ] `ruff check` passes with zero violations
- [ ] Pydantic v2 schemas cover all request/response contracts with field-level validation
- [ ] OpenAPI documentation reflects the new or changed endpoints
- [ ] Database migrations are reversible; `alembic downgrade -1` tested against a staging snapshot
- [ ] No new CRITICAL or HIGH CVEs introduced (Trivy + Dependabot alerts checked)
- [ ] Logging includes `correlation_id` and all relevant business context fields
- [ ] Error responses follow the standard envelope: `{error_code, message, details}`
- [ ] Performance validated: p95 <200ms for read endpoints, <500ms for write endpoints under expected load
- [ ] Deployed to staging; smoke tests pass; QA signed off
- [ ] PM has accepted the feature against the agreed acceptance criteria
- [ ] CHANGELOG entry added for any user-facing change

---

## Risk Register

| # | Risk | Probability | Impact | Mitigation Strategy |
|---|------|-------------|--------|---------------------|
| R-01 | AWS service quota limits block provisioning (ECS tasks, Elastic IPs) | Medium | High | File quota increase requests in Week 1; track via AWS Support case with 5-day SLA |
| R-02 | SendGrid deliverability issues (domain flagged as spam) | Medium | High | Warm up sending domain over 2 weeks; configure DKIM/SPF/DMARC before first send |
| R-03 | Kinesis Lambda consumer falls behind under load (high IteratorAge) | Low | High | Set CloudWatch alarm on IteratorAge >60s; configure Lambda reserved concurrency; implement DLQ |
| R-04 | GDPR compliance gaps discovered in Phase 5 audit after data is live | Low | Critical | Engage DPO in Phase 3; run internal compliance checklist in Phase 4; schedule external audit in Phase 5 |
| R-05 | Google or Microsoft breaks OAuth flow with API changes | Medium | Medium | Abstract OAuth provider behind interface; subscribe to Google Identity and Azure AD developer changelogs |
| R-06 | Stripe API breaking changes during billing implementation | Low | Medium | Pin `stripe-python` API version in client constructor; follow migration guide before upgrading |
| R-07 | Key engineer unavailability (illness, attrition) | Low | High | Cross-train all critical paths; maintain detailed onboarding runbooks; no single-person knowledge silos |
| R-08 | k6 load test uncovers architectural bottleneck post-Phase 3 build | Low | Critical | Run informal 100-VU spot tests from Phase 2 onwards; track p95 response time weekly in Datadog |

---

## Operational Policy Addendum

### A.1 On-Call and Incident Response

Production incidents are classified by severity: **P1** (complete service outage) requires page acknowledgment within 5 minutes and incident commander assignment within 10 minutes; target resolution is 2 hours. **P2** (major feature degradation, data pipeline lag >5 minutes) requires acknowledgment within 15 minutes; resolution within 8 hours. **P3** (minor UI issues, non-critical feature failure) is handled during business hours with no SLA pager. The on-call rotation covers all backend engineers and the DevOps engineer on a 7-day cycle managed in PagerDuty. Post-mortems are mandatory for P1 and P2 incidents; they must be published to the team within 48 hours of resolution, use a blameless format, and include at least one action item with an owner and due date.

### A.2 Change Management

All changes to production infrastructure and application code follow a gated promotion process. **Low-risk changes** (environment variable updates, static asset deploys, configuration flag changes) require 1 peer approval and a 30-minute observation window post-deploy. **High-risk changes** (database schema migrations, ECS task definition updates, IAM policy changes, Kinesis stream reconfiguration) require 2 approvals (including Lead Architect), a written rollback plan referenced in the PR, and a 4-hour monitoring window with an engineer on standby. **Emergency changes** during an active P1 incident may bypass the approval gate with verbal authorization from the Lead Architect, but must be documented in the incident timeline and formalized within 24 hours.

### A.3 Data Privacy and Compliance

All survey response data is classified as potentially containing Personally Identifiable Information (PII) and must be treated accordingly. Data at rest is encrypted using AES-256: RDS uses AWS-managed KMS keys with automated annual rotation; S3 buckets use SSE-KMS with customer-managed keys. Data in transit must use TLS 1.2 minimum; TLS 1.3 is enforced at the CloudFront and ALB layer. The default data retention period is 2 years from the date of collection, configurable per workspace within permitted ranges. GDPR data subject requests (access, rectification, erasure, portability) must be fulfilled within 30 calendar days of receipt. A Data Processing Agreement (DPA) template is maintained by the PM and provided to all Business and Enterprise customers before survey data collection begins.

### A.4 Documentation Standards

All API endpoints must be documented in OpenAPI 3.1 format; FastAPI's auto-generated `/docs` and `/redoc` are the primary references and must always reflect the current deployed version. Architecture Decision Records (ADRs) are stored in `docs/adr/` using the MADR template; any significant design choice (database selection, queue choice, auth mechanism) must have a corresponding ADR committed before implementation begins. Operational runbooks for routine tasks (RDS failover test, Redis flush, ECS service force-restart, Kinesis shard rebalance) are maintained in `docs/runbooks/` and reviewed at the start of each phase. Documentation items that have not been reviewed or updated in 90 days are automatically flagged via a weekly GitHub Actions job that checks `git log` timestamps.
