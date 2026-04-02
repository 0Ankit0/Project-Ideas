# Survey and Feedback Platform

> Enterprise-grade survey, form-builder, and feedback intelligence platform — enabling teams to design, distribute, and deeply analyze surveys at scale with real-time analytics, white-label reporting, and seamless CRM integrations.

---

## Table of Contents

- [Key Features](#key-features)
- [Primary Roles](#primary-roles)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Directory Structure](#directory-structure)
- [Documentation Status](#documentation-status)
- [Delivery Blueprint](#delivery-blueprint)
- [Operational Policy Addendum](#operational-policy-addendum)

---

## Key Features

1. **Form Builder** — Drag-and-drop survey designer with 20+ question types, conditional logic, branching paths, skip logic, piping, and page-level display rules. Supports multilingual forms.
2. **Survey Distribution** — Multi-channel distribution via email campaigns, shareable links, iframe embeds, QR codes, and SMS (Twilio). Supports throttling, scheduling, and reminders.
3. **Response Collection** — Anonymous and identified response modes, partial save and resume, offline-capable Progressive Web App (PWA), and deduplication via fingerprinting + cookie tracking.
4. **Real-Time Analytics** — Live dashboards with NPS trend tracking, CSAT/CES scoring, sentiment analysis (AWS Comprehend), cross-tabulation pivot tables, and word cloud generation.
5. **Report Generation** — Export reports as PDF, Excel (XLSX), and CSV. Schedule recurring reports, apply white-label branding, and deliver via email or webhook.
6. **Audience Management** — Import and manage contact lists, define dynamic segments with attribute filters, manage GDPR consent records, and track opt-in/opt-out history.
7. **Template Library** — Curated library of 100+ industry-specific survey templates (NPS, CSAT, HR, Education, Healthcare). Supports custom organizational templates and sharing.
8. **Webhook & API Integration** — Native integrations with Slack (survey notifications), HubSpot (contact sync), Salesforce (response push), and Zapier. Full REST API with OpenAPI spec.
9. **Multi-Workspace & Team Collaboration** — Isolated workspaces per team/client. Role-based access, survey commenting, version history, co-editing notifications, and activity audit log.
10. **Subscription Plans** — Free, Starter ($29/mo), Business ($99/mo), and Enterprise (custom) tiers. Usage-based billing (responses, seats, storage) with Stripe integration.

---

## Primary Roles

| Role | Description | Key Permissions |
|---|---|---|
| **Survey Creator** | Designs and publishes surveys, manages distribution campaigns, views own survey analytics | Create/edit/delete surveys, manage distributions, view own responses and reports, use templates |
| **Respondent** | Completes surveys via link, embed, email, QR, or SMS. May be anonymous or authenticated | Submit responses, save progress, update partial submissions, withdraw consent |
| **Analyst** | Views, filters, and exports analytics across assigned workspaces; creates scheduled reports | Read all responses in workspace, export data, create dashboards, run cross-tabulation, access raw data exports |
| **Workspace Admin** | Manages workspace settings, members, billing, integrations, and audience lists for their workspace | All Creator/Analyst permissions + manage members, configure integrations, manage contact lists, manage subscription |
| **Super Admin** | Platform-level administrator with full access to all workspaces, tenants, system config, and audit logs | Full system access: manage tenants, impersonate users, view global audit logs, manage platform config and feature flags |

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | FastAPI (Python 3.11), async SQLAlchemy 2.x, Pydantic v2, Alembic |
| **Frontend** | React 18 + TypeScript 5, Zustand, react-hook-form, Recharts, DnD Kit |
| **Primary DB** | PostgreSQL 15 (AWS RDS Multi-AZ) |
| **Document Store** | MongoDB 7 (Atlas / self-hosted) |
| **Cache / Queue Broker** | Redis 7 (AWS ElastiCache) |
| **Task Queue** | Celery 5 + Redis |
| **Auth** | JWT (RS256), OAuth 2.0 (Google, Microsoft SSO), Magic Link via SendGrid |
| **Storage** | AWS S3 + CloudFront CDN |
| **Infrastructure** | AWS ECS Fargate, RDS, ElastiCache, Route 53, WAF, ACM |
| **Analytics Pipeline** | AWS Kinesis Data Streams → Lambda → DynamoDB |
| **Email** | SendGrid (transactional), Amazon SES (bulk) |
| **SMS** | Twilio |
| **Monitoring** | AWS CloudWatch, Sentry, Datadog |

---

## Getting Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/survey-feedback-platform.git
   cd survey-feedback-platform
   ```

2. **Set up environment variables**
   ```bash
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env
   # Edit backend/.env with your DB credentials, AWS keys, JWT secret, SendGrid key, Twilio SID
   # Edit frontend/.env with VITE_API_URL and VITE_GOOGLE_CLIENT_ID
   ```

3. **Start infrastructure services (Docker Compose)**
   ```bash
   docker compose -f docker/docker-compose.dev.yml up -d
   # Starts: PostgreSQL 15, MongoDB 7, Redis 7
   ```

4. **Install backend dependencies**
   ```bash
   cd backend
   python -m venv venv && source venv/bin/activate
   pip install -r requirements.txt
   ```

5. **Run database migrations**
   ```bash
   alembic upgrade head
   # Seeds initial roles, plan tiers, and default templates
   python scripts/seed_data.py
   ```

6. **Start the backend API server**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   # API available at http://localhost:8000
   # OpenAPI docs at http://localhost:8000/docs
   ```

7. **Install frontend dependencies and start dev server**
   ```bash
   cd ../frontend
   npm install
   npm run dev
   # App available at http://localhost:5173
   ```

8. **Start Celery workers (for background tasks)**
   ```bash
   cd backend
   celery -A app.celery_app worker --loglevel=info -Q default,reports,emails
   celery -A app.celery_app beat --loglevel=info
   ```

9. **Run the test suite**
   ```bash
   # Backend
   cd backend && pytest --cov=app --cov-report=term-missing -v
   # Frontend
   cd frontend && npm run test
   ```

10. **Access the platform**
    - Frontend: http://localhost:5173
    - API: http://localhost:8000
    - API Docs (Swagger): http://localhost:8000/docs
    - API Docs (Redoc): http://localhost:8000/redoc
    - Flower (Celery monitor): http://localhost:5555

---

## Directory Structure

```
survey-feedback-platform/
├── README.md
├── docker/
│   ├── docker-compose.dev.yml
│   ├── docker-compose.prod.yml
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
├── backend/
│   ├── .env.example
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/
│   │   └── versions/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── celery_app.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── workspace.py
│   │   │   ├── survey.py
│   │   │   ├── question.py
│   │   │   ├── response.py
│   │   │   ├── distribution.py
│   │   │   ├── contact.py
│   │   │   ├── template.py
│   │   │   └── subscription.py
│   │   ├── schemas/
│   │   │   ├── survey.py
│   │   │   ├── response.py
│   │   │   ├── user.py
│   │   │   └── analytics.py
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   ├── surveys.py
│   │   │   ├── questions.py
│   │   │   ├── responses.py
│   │   │   ├── distributions.py
│   │   │   ├── analytics.py
│   │   │   ├── reports.py
│   │   │   ├── contacts.py
│   │   │   ├── templates.py
│   │   │   ├── workspaces.py
│   │   │   ├── webhooks.py
│   │   │   └── billing.py
│   │   ├── services/
│   │   │   ├── auth_service.py
│   │   │   ├── survey_service.py
│   │   │   ├── response_service.py
│   │   │   ├── distribution_service.py
│   │   │   ├── analytics_service.py
│   │   │   ├── report_service.py
│   │   │   ├── contact_service.py
│   │   │   ├── template_service.py
│   │   │   ├── notification_service.py
│   │   │   ├── integration_service.py
│   │   │   └── billing_service.py
│   │   ├── tasks/
│   │   │   ├── email_tasks.py
│   │   │   ├── report_tasks.py
│   │   │   ├── analytics_tasks.py
│   │   │   └── cleanup_tasks.py
│   │   ├── core/
│   │   │   ├── security.py
│   │   │   ├── permissions.py
│   │   │   ├── exceptions.py
│   │   │   └── middleware.py
│   │   └── utils/
│   │       ├── s3.py
│   │       ├── kinesis.py
│   │       ├── pdf_generator.py
│   │       └── excel_generator.py
│   └── tests/
│       ├── conftest.py
│       ├── test_surveys.py
│       ├── test_responses.py
│       ├── test_analytics.py
│       └── test_auth.py
├── frontend/
│   ├── .env.example
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── public/
│   │   └── manifest.json
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── store/
│   │   │   ├── authStore.ts
│   │   │   ├── surveyStore.ts
│   │   │   └── workspaceStore.ts
│   │   ├── pages/
│   │   │   ├── auth/
│   │   │   ├── builder/
│   │   │   ├── dashboard/
│   │   │   ├── analytics/
│   │   │   ├── reports/
│   │   │   ├── contacts/
│   │   │   ├── templates/
│   │   │   └── settings/
│   │   ├── components/
│   │   │   ├── builder/
│   │   │   │   ├── DragDropCanvas.tsx
│   │   │   │   ├── QuestionBlock.tsx
│   │   │   │   ├── LogicEditor.tsx
│   │   │   │   └── PreviewPane.tsx
│   │   │   ├── analytics/
│   │   │   │   ├── NPSChart.tsx
│   │   │   │   ├── SentimentGauge.tsx
│   │   │   │   ├── CrossTabTable.tsx
│   │   │   │   └── WordCloud.tsx
│   │   │   └── ui/
│   │   ├── hooks/
│   │   ├── api/
│   │   ├── types/
│   │   └── utils/
│   └── tests/
├── infrastructure/
│   ├── terraform/
│   │   ├── main.tf
│   │   ├── ecs.tf
│   │   ├── rds.tf
│   │   ├── elasticache.tf
│   │   ├── cloudfront.tf
│   │   ├── waf.tf
│   │   └── variables.tf
│   └── k8s/   (optional)
├── scripts/
│   ├── seed_data.py
│   ├── migrate_responses.py
│   └── backfill_analytics.py
└── docs/
    ├── requirements/
    ├── high-level-design/
    ├── detailed-design/
    ├── analysis/
    ├── edge-cases/
    ├── implementation/
    └── infrastructure/
```

---

## Documentation Status

| # | File | Category | Status |
|---|---|---|---|
| 1 | `README.md` | Overview | ✅ Complete |
| 2 | `requirements/requirements-document.md` | Requirements | ✅ Complete |
| 3 | `requirements/user-stories.md` | Requirements | ✅ Complete |
| 4 | `high-level-design/system-architecture.md` | HLD | ✅ Complete |
| 5 | `high-level-design/data-models.md` | HLD | ✅ Complete |
| 6 | `high-level-design/api-design.md` | HLD | ✅ Complete |
| 7 | `high-level-design/auth-flow.md` | HLD | ✅ Complete |
| 8 | `high-level-design/analytics-pipeline.md` | HLD | ✅ Complete |
| 9 | `detailed-design/form-builder.md` | DLD | ✅ Complete |
| 10 | `detailed-design/response-collection.md` | DLD | ✅ Complete |
| 11 | `detailed-design/distribution-engine.md` | DLD | ✅ Complete |
| 12 | `detailed-design/analytics-engine.md` | DLD | ✅ Complete |
| 13 | `detailed-design/report-generation.md` | DLD | ✅ Complete |
| 14 | `detailed-design/audience-management.md` | DLD | ✅ Complete |
| 15 | `detailed-design/webhook-integrations.md` | DLD | ✅ Complete |
| 16 | `detailed-design/billing-subscriptions.md` | DLD | ✅ Complete |
| 17 | `detailed-design/template-library.md` | DLD | ✅ Complete |
| 18 | `detailed-design/workspace-collaboration.md` | DLD | ✅ Complete |
| 19 | `analysis/competitive-analysis.md` | Analysis | ✅ Complete |
| 20 | `analysis/risk-analysis.md` | Analysis | ✅ Complete |
| 21 | `analysis/scalability-analysis.md` | Analysis | ✅ Complete |
| 22 | `analysis/security-analysis.md` | Analysis | ✅ Complete |
| 23 | `edge-cases/form-builder-edge-cases.md` | Edge Cases | ✅ Complete |
| 24 | `edge-cases/response-collection-edge-cases.md` | Edge Cases | ✅ Complete |
| 25 | `edge-cases/distribution-edge-cases.md` | Edge Cases | ✅ Complete |
| 26 | `edge-cases/analytics-edge-cases.md` | Edge Cases | ✅ Complete |
| 27 | `edge-cases/billing-edge-cases.md` | Edge Cases | ✅ Complete |
| 28 | `implementation/backend-setup.md` | Implementation | ✅ Complete |
| 29 | `implementation/frontend-setup.md` | Implementation | ✅ Complete |
| 30 | `implementation/celery-workers.md` | Implementation | ✅ Complete |
| 31 | `implementation/api-reference.md` | Implementation | ✅ Complete |
| 32 | `infrastructure/aws-architecture.md` | Infrastructure | ✅ Complete |
| 33 | `infrastructure/terraform-guide.md` | Infrastructure | ✅ Complete |
| 34 | `infrastructure/ci-cd-pipeline.md` | Infrastructure | ✅ Complete |
| 35 | `infrastructure/monitoring-alerting.md` | Infrastructure | ✅ Complete |
| 36 | `infrastructure/disaster-recovery.md` | Infrastructure | ✅ Complete |

---

## Delivery Blueprint

| Phase | Name | Deliverables | Timeline |
|---|---|---|---|
| **Phase 1** | Foundation | Auth (JWT + OAuth + Magic Link), workspace management, user roles, subscription tiers, PostgreSQL schema, Redis setup, CI/CD pipeline | Weeks 1–4 |
| **Phase 2** | Core Survey Engine | Form builder (drag-and-drop, conditional logic), question types (20+), template library, response collection (anonymous + identified), partial save, deduplication | Weeks 5–10 |
| **Phase 3** | Distribution & Collection | Email distribution (SendGrid), shareable links, iframe embeds, QR code generation, SMS via Twilio, offline PWA, Kinesis response ingestion pipeline | Weeks 11–16 |
| **Phase 4** | Analytics & Reporting | Real-time dashboards, NPS/CSAT/CES scoring, sentiment analysis, cross-tabulation, word cloud, PDF/Excel/CSV export, scheduled reports, white-label branding | Weeks 17–22 |
| **Phase 5** | Integrations & Launch | Webhooks (Slack, HubSpot, Salesforce, Zapier), REST API public release, audience management with GDPR consent, rate limiting, WAF tuning, load testing, production cutover | Weeks 23–28 |

---

## Operational Policy Addendum

### 1. Response Data Privacy Policies

**GDPR Compliance (EU Regulation 2016/679)**
- All personally identifiable information (PII) collected via identified survey responses is stored in EU-region AWS infrastructure (eu-west-1) for EU-resident respondents by default, with region selection available to workspace admins.
- Respondents have the right to access, rectify, and erase their data. A self-service data subject request (DSR) portal is available at `/privacy/requests`.
- Consent is collected at the point of survey entry for identified surveys. Consent records are stored immutably with timestamp, IP address (hashed), and consent text version.
- Data processing agreements (DPAs) are available for all Business and Enterprise plan customers.
- Data retention: identified response data is retained for the duration of the workspace subscription plus a 90-day grace period. Anonymous response data may be retained indefinitely in aggregated form.

**CCPA Compliance (California Consumer Privacy Act)**
- California residents may opt out of the sale of their personal information. No survey response data is sold to third parties.
- A "Do Not Sell My Personal Information" link is available on all public-facing survey pages.
- Upon request, all personal data associated with a respondent's email address will be compiled and delivered within 45 days.

**Data Minimization**
- Surveys are configured to collect only the minimum data necessary. Admins are warned during survey creation if optional PII fields (phone, location) are added without a documented justification.
- IP addresses captured during response collection are hashed (SHA-256 + workspace salt) before storage. Raw IPs are never persisted.

---

### 2. Survey Distribution Policies

**Anti-Spam Policy**
- Email distribution is subject to CAN-SPAM Act and GDPR email consent requirements. Survey invitations may only be sent to contacts who have provided affirmative opt-in consent or have an established business relationship with the survey owner.
- Rate limits: Free plan — 500 emails/month. Starter — 10,000/month. Business — 100,000/month. Enterprise — custom.
- Workspace admins receive automated alerts when bounce rates exceed 5% or spam complaint rates exceed 0.1% on any email campaign.
- SendGrid domain authentication (SPF, DKIM, DMARC) is enforced for all sending domains.

**Unsubscribe & Opt-Out**
- Every survey invitation email must include a one-click unsubscribe link. This is enforced at the system level and cannot be removed by users.
- Unsubscribed contacts are automatically suppressed from all future distributions within the workspace.
- QR code and SMS distributions include an opt-out mechanism on the survey completion page.

**Consent for SMS**
- SMS survey invitations require prior TCPA-compliant written consent from the recipient. Workspace admins must confirm consent compliance before enabling SMS distribution.
- Opt-out keywords (STOP, UNSUBSCRIBE) are honored within 10 minutes and suppress the contact from all future SMS distributions in the workspace.

---

### 3. Analytics and Retention Policies

**Data Retention Periods**

| Data Type | Retention Period | Archival Policy |
|---|---|---|
| Identified survey responses | Subscription term + 90 days | Archived to S3 Glacier on workspace deactivation |
| Anonymous responses | 36 months (aggregated) | Anonymized aggregates retained indefinitely |
| Audit logs | 24 months | Exported to S3, encrypted at rest |
| Email campaign logs | 12 months | Purged after expiry |
| Analytics snapshots (DynamoDB) | 18 months rolling | Hot data: 6 months; warm: 12 months in S3 |
| User account data | Account lifetime + 30 days | GDPR erasure request: 7-day SLA |

**Anonymization Standards**
- Before export or sharing outside the platform, any dataset containing fewer than 5 responses for a given segment is suppressed to prevent re-identification (k-anonymity threshold of 5).
- Free-text responses undergone sentiment analysis are processed ephemerally; raw text is never sent to third-party ML services without workspace admin consent.
- Differential privacy techniques are applied to aggregate analytics exports on Enterprise plans.

**Analytics Pipeline**
- Response events are streamed to AWS Kinesis Data Streams (retention: 24 hours) and processed by Lambda functions into DynamoDB for real-time dashboard queries.
- Daily batch jobs aggregate raw Kinesis data into PostgreSQL for historical trend analysis.

---

### 4. System Availability Policies

**Service Level Agreements (SLAs)**

| Plan | Uptime SLA | Support Response | Scheduled Maintenance |
|---|---|---|---|
| Free | 99.5% (best effort) | Community forum | Anytime |
| Starter | 99.7% | Email (48h) | Sundays 02:00–06:00 UTC |
| Business | 99.9% | Email (8h) + Chat (business hours) | Sundays 02:00–04:00 UTC |
| Enterprise | 99.95% | Dedicated (1h) + Phone | Coordinated 4-week notice |

**Recovery Objectives**

| Metric | Target |
|---|---|
| Recovery Time Objective (RTO) | ≤ 30 minutes (database failover via RDS Multi-AZ automatic promotion) |
| Recovery Point Objective (RPO) | ≤ 5 minutes (RDS automated backups every 5 minutes via PITR; Redis AOF persistence) |
| Mean Time to Detect (MTTD) | ≤ 3 minutes (CloudWatch alarms + PagerDuty) |
| Mean Time to Recover (MTTR) | ≤ 20 minutes for P1 incidents |

**Incident Management**
- P1 (platform down): acknowledged within 15 minutes, active remediation within 30 minutes, status page updated every 15 minutes.
- P2 (major feature unavailable): acknowledged within 1 hour, resolved within 4 hours.
- P3 (degraded performance): acknowledged within 4 hours, resolved within 24 hours.
- Post-incident RCA published within 5 business days for P1/P2 incidents on Business and Enterprise plans.
- Status page: https://status.surveyplatform.io (powered by Statuspage.io)

**Backup Policy**
- PostgreSQL: automated daily snapshots retained for 35 days; point-in-time recovery (PITR) enabled with 5-minute granularity.
- MongoDB Atlas: continuous backups with point-in-time recovery up to 7 days.
- S3 (file uploads, reports): cross-region replication to secondary region; versioning enabled on all buckets.
- Redis: AOF + RDB persistence; ElastiCache Multi-AZ with automatic failover.
