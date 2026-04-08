# Job Board and Recruitment Platform

A full-featured, enterprise-grade recruitment platform that unifies job posting distribution, applicant tracking, AI-assisted resume screening, structured interview workflows, offer management, and hiring analytics into a single cohesive system. Built for companies that need to scale hiring operations without sacrificing candidate experience or recruiter productivity.

---

## Documentation Structure

Project root artifact: [`traceability-matrix.md`](./traceability-matrix.md) provides cross-phase requirement-to-implementation linkage.


```
Job Board and Recruitment Platform/
├── README.md                          ← You are here
├── traceability-matrix.md
├── requirements/
│   ├── requirements-document.md       ← Functional & non-functional requirements (FR/NFR)
│   └── user-stories.md                ← Role-based user stories with acceptance criteria
├── architecture/
│   ├── system-design.md               ← High-level architecture, component diagrams
│   ├── data-model.md                  ← Entity-relationship diagrams, schema definitions
│   ├── api-design.md                  ← REST API contracts, endpoint specs
│   └── integration-map.md             ← Third-party service integrations
├── design/
│   ├── ux-flows.md                    ← User journey maps and screen flows
│   ├── wireframes/                    ← Lo-fi wireframes per module
│   └── design-system.md              ← Component library, color palette, typography
├── modules/
│   ├── job-posting.md                 ← Job creation, approval, and syndication
│   ├── candidate-portal.md            ← Candidate-facing features and portal UX
│   ├── ats-pipeline.md                ← Applicant tracking pipeline and stage logic
│   ├── interview-management.md        ← Scheduling, scorecards, feedback
│   ├── offer-management.md            ← Offer generation, signing, and counters
│   ├── analytics.md                   ← Reporting, dashboards, export
│   └── integrations.md               ← Calendar, e-sign, background check, job boards
├── compliance/
│   ├── gdpr.md                        ← Data privacy, consent, erasure workflows
│   ├── eeo-ofccp.md                   ← Equal employment, OFCCP compliance
│   └── pay-transparency.md            ← Salary disclosure law compliance
└── operations/
    ├── deployment.md                  ← Infrastructure, CI/CD, environment strategy
    ├── monitoring.md                  ← Observability, alerting, SLOs
    └── runbooks/                      ← Incident response and operational procedures
```

---

## Key Features

### Multi-Company Job Posting Management
The platform supports a multi-tenant architecture where each company operates in its own isolated workspace. Recruiters can create richly formatted job postings with structured data fields — title, department, location (including remote/hybrid designations), employment type, experience level, compensation range, and benefits. Jobs move through a configurable approval workflow before going live, ensuring hiring managers and legal teams can review postings before they reach candidates. Once approved, jobs are automatically syndicated to external job boards including LinkedIn, Indeed, Glassdoor, and ZipRecruiter via dedicated API integrations, eliminating the need for manual re-posting across platforms.

### AI-Powered Resume Parsing and Screening
Candidates upload resumes in PDF, DOCX, or plain-text format. An AI parsing engine (integrated with services such as Affinda, Sovren, or a self-hosted LLM pipeline) extracts structured data: contact information, work history with dates and responsibilities, education, skills, certifications, and links (GitHub, portfolio). The parsed data is stored in a searchable candidate database. Recruiters can run Boolean searches across the entire talent pool using field-specific filters and keyword operators. An optional AI-assist ranking layer scores incoming applications against the job description to surface the strongest candidates at the top of the queue, without making autonomous decisions that could introduce bias.

### ATS Pipeline Management
Every job opening gets its own configurable hiring pipeline with drag-and-drop Kanban-style stages. Default stages (Applied, Screened, Phone Screen, Technical Assessment, Interview, Offer, Hired, Rejected) can be customized per job or per company. Recruiters can move candidates between stages individually or in bulk, apply tags, leave internal notes, set follow-up reminders, and configure automatic transition triggers — for example, auto-advancing a candidate to "Phone Screen" when a recruiter marks a resume as shortlisted. Candidate pools allow sourcers to pre-populate a talent bench for roles that haven't officially opened yet.

### Interview Scheduling and Structured Feedback
Interview rounds are created with structured formats: panel interviews, technical assessments, take-home projects, or one-on-one calls. The platform integrates with Google Calendar and Microsoft Outlook/Exchange to check interviewer availability in real time and propose time slots to candidates without requiring the recruiter to email back and forth. Confirmed interviews automatically generate calendar invites for all parties and include video conferencing links from Zoom or Microsoft Teams. Each interview round has an attached scorecard template with role-specific competency criteria. Interviewers submit ratings and written feedback directly in the platform before final hiring decisions are made, creating an auditable record.

### Offer Management and Digital Signing
When a hiring decision is reached, recruiters generate an offer letter from a company-managed template library. Offer letters are pre-populated with candidate and role data and routed through a configurable approval chain (e.g., Recruiter → Hiring Manager → Compensation → Legal). Once approved, the offer is sent to the candidate for digital signing via DocuSign or HelloSign integration. Candidates can accept, counter-propose, or decline through a branded candidate portal. Expiry dates are enforced automatically. Upon acceptance, the platform triggers background check initiation via the Checkr API and notifies HR to begin onboarding.

### Analytics and Hiring Intelligence
Executive dashboards and recruiter-facing reports deliver real-time visibility into the entire hiring funnel. Key metrics include time-to-fill, time-to-hire, application-to-interview conversion rate, offer acceptance rate, source attribution ROI (comparing cost-per-hire across job boards), diversity and EEO pipeline metrics, and individual recruiter performance. Reports can be filtered by department, location, recruiter, time range, and job level. Scheduled report delivery sends PDF or CSV exports to stakeholders on a recurring basis. EEO/OFCCP disposition data is captured throughout the pipeline to support federal compliance reporting.

### Candidate Experience Portal
Candidates interact with the platform through a dedicated, mobile-responsive portal. They can create a profile, apply to multiple roles with a single profile, track the status of each application, receive automated stage-change notifications, schedule their own interview slots from available windows, access and sign offer letters, and submit a right-of-erasure (GDPR) request. The portal is accessible (WCAG 2.1 AA) and fully localizable to support global hiring.

### Role-Based Access Control and Multi-Tenancy
The platform enforces a fine-grained RBAC model across five primary personas: **Candidates** (self-service portal only), **Recruiters** (job creation, pipeline management, scheduling), **Hiring Managers** (review candidates for their open roles, submit interview feedback), **HR Admins** (company-wide configuration, compliance reporting, data governance), and **Platform Super Admins** (multi-tenant configuration, billing, feature flags). Each role gets the minimum permissions required, and data isolation between tenants is enforced at the database and API layer.

---

## Getting Started

- Review [`traceability-matrix.md`](./traceability-matrix.md) first to navigate requirement-to-implementation coverage across phases.
### Prerequisites

| Dependency | Minimum Version | Purpose |
|---|---|---|
| Node.js | 20 LTS | API server and background workers |
| PostgreSQL | 15 | Primary relational datastore |
| Redis | 7 | Session cache, job queues (BullMQ) |
| Elasticsearch | 8.x | Candidate search and resume full-text index |
| Docker / Docker Compose | 24+ | Local development environment |
| AWS CLI / GCP SDK | Latest | Infrastructure provisioning |

### Local Development

```bash
# 1. Clone the repository
git clone https://github.com/your-org/job-board-platform.git
cd job-board-platform

# 2. Copy environment variables
cp .env.example .env
# Edit .env — fill in API keys for DocuSign, LinkedIn, Indeed, Zoom, Checkr, etc.

# 3. Start infrastructure services
docker compose up -d postgres redis elasticsearch

# 4. Install dependencies
npm install

# 5. Run database migrations
npm run db:migrate

# 6. Seed development data (companies, sample jobs, test candidates)
npm run db:seed

# 7. Start the API server (hot reload)
npm run dev:api

# 8. Start the candidate portal (Next.js)
npm run dev:portal

# 9. Start the recruiter dashboard (Next.js)
npm run dev:dashboard

# 10. Start background workers (BullMQ)
npm run dev:workers
```

The recruiter dashboard will be available at `http://localhost:3000`.  
The candidate portal will be available at `http://localhost:3001`.  
The API will be available at `http://localhost:4000/api/v1`.

### Key Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/recruitment_db
REDIS_URL=redis://localhost:6379
ELASTICSEARCH_URL=http://localhost:9200

# Authentication
JWT_SECRET=your-jwt-secret-min-32-chars
SESSION_SECRET=your-session-secret

# Email
SENDGRID_API_KEY=SG.xxxxx
FROM_EMAIL=noreply@yourplatform.com

# Resume Parsing
AFFINDA_API_KEY=your-affinda-key

# E-Signature
DOCUSIGN_INTEGRATION_KEY=your-docusign-key
DOCUSIGN_ACCOUNT_ID=your-account-id
HELLOSIGN_API_KEY=your-hellosign-key

# Calendar Integration
GOOGLE_OAUTH_CLIENT_ID=your-google-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-google-client-secret
MICROSOFT_CLIENT_ID=your-ms-client-id
MICROSOFT_CLIENT_SECRET=your-ms-client-secret

# Video Conferencing
ZOOM_CLIENT_ID=your-zoom-client-id
ZOOM_CLIENT_SECRET=your-zoom-client-secret

# Job Board Syndication
LINKEDIN_JOBS_API_KEY=your-linkedin-key
INDEED_PUBLISHER_ID=your-indeed-id
GLASSDOOR_API_KEY=your-glassdoor-key

# Background Checks
CHECKR_API_KEY=your-checkr-key

# Storage
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_S3_BUCKET=recruitment-assets
AWS_REGION=us-east-1

# Feature Flags
FEATURE_AI_RANKING=true
FEATURE_VIDEO_INTERVIEWS=true
FEATURE_DIVERSITY_REPORTING=true
```

### Running Tests

```bash
# Unit tests
npm run test

# Integration tests (requires running Docker services)
npm run test:integration

# End-to-end tests (Playwright)
npm run test:e2e

# Test coverage report
npm run test:coverage
```

### Deployment

The platform is containerized and deployable to any Kubernetes cluster. Helm charts are provided in the `infra/helm/` directory. A GitHub Actions CI/CD pipeline handles:

1. Linting and type-checking
2. Unit and integration test execution
3. Docker image build and push to ECR/Artifact Registry
4. Helm chart deployment to staging on every merge to `main`
5. Manual promotion gate to production

Refer to `operations/deployment.md` for full infrastructure documentation including auto-scaling policies, database failover configuration, and blue/green deployment strategy.

---

## Target Users

### Recruiters
Internal talent acquisition professionals who own the end-to-end hiring process for assigned requisitions. They create and post jobs, source and screen candidates, manage the ATS pipeline, coordinate interviews, generate offers, and report on pipeline health. The platform is their primary workbench — they spend the majority of their working day inside the recruiter dashboard.

### Hiring Managers
Department leaders and team leads who raise hiring requisitions and collaborate with recruiters to evaluate candidates for their team. They review candidate profiles, participate in interview scorecards, make final hire/no-hire recommendations, and track open requisitions. They need focused, low-friction access to the candidates relevant to their roles without being overwhelmed by platform-wide configuration options.

### Candidates
Job seekers — both active and passive — who discover job openings through the company careers page, job boards, or referrals. They apply online, upload their resume, complete assessments if required, schedule their own interviews, and receive offer letters. A positive, transparent candidate experience is a core product goal: candidates always know where they stand and receive timely communications.

### HR Administrators
HR operations professionals responsible for platform configuration, compliance, data governance, and user management. They define approval workflows, manage offer letter templates, configure RBAC roles, run EEO/OFCCP compliance reports, handle GDPR data requests, and maintain integrations with HRIS systems like Workday or BambooHR. They are power users who access every corner of the platform.

### Executives and Talent Ops
VP of Talent, CHRO, and Talent Operations leads who consume analytics dashboards without performing day-to-day recruiting tasks. They need high-level funnel metrics, headcount plan progress, source ROI, diversity trajectory, and recruiter productivity data delivered through executive dashboards and scheduled reports.

---

## Tech Stack Overview

### Backend
- **Runtime:** Node.js 20 LTS with TypeScript
- **API Framework:** Fastify (high-performance REST API layer)
- **ORM:** Drizzle ORM with PostgreSQL
- **Queue System:** BullMQ (Redis-backed) for async jobs (resume parsing, email delivery, job syndication)
- **Search:** Elasticsearch 8 for candidate and job full-text search
- **Authentication:** JWT access tokens + refresh token rotation, OAuth 2.0 for calendar/social integrations
- **File Storage:** AWS S3 with pre-signed URLs for resume and document storage

### Frontend
- **Framework:** Next.js 14 (App Router) with TypeScript
- **UI Library:** Tailwind CSS + shadcn/ui component library
- **State Management:** TanStack Query (server state) + Zustand (client state)
- **Forms:** React Hook Form with Zod schema validation
- **Data Tables:** TanStack Table for pipeline and candidate grids
- **Drag and Drop:** dnd-kit for Kanban pipeline management

### Data & Analytics
- **Primary Database:** PostgreSQL 15 with row-level security for multi-tenancy
- **Cache:** Redis 7 (session cache, rate limiting, real-time pipeline counts)
- **Analytics Store:** ClickHouse for high-cardinality time-series event data (funnel events, source attribution)
- **Search Index:** Elasticsearch 8 for resume full-text and Boolean search

### Infrastructure
- **Container Platform:** Kubernetes (EKS / GKE)
- **IaC:** Terraform for all cloud resources
- **CI/CD:** GitHub Actions
- **Monitoring:** OpenTelemetry → Grafana + Tempo + Loki + Prometheus
- **Error Tracking:** Sentry
- **CDN:** CloudFront for static assets and resume file delivery

### Key Third-Party Integrations
| Category | Provider | Purpose |
|---|---|---|
| Resume Parsing | Affinda / Sovren | Extract structured data from resumes |
| E-Signature | DocuSign, HelloSign | Offer letter digital signing |
| Background Check | Checkr | Criminal, employment, education verification |
| Video Conferencing | Zoom, Microsoft Teams | Auto-generate meeting links |
| Calendar | Google Calendar, Microsoft Outlook | Availability check, invite generation |
| Job Distribution | LinkedIn, Indeed, Glassdoor, ZipRecruiter | Automated job syndication |
| Email Delivery | SendGrid | Transactional emails to candidates and interviewers |
| HRIS | Workday, BambooHR | Employee sync, onboarding handoff |
| Payments | Stripe | Platform subscription billing |
| Analytics | Mixpanel, Amplitude | Product usage analytics |

---

## Documentation Status

- ✅ Traceability coverage is available via [`traceability-matrix.md`](./traceability-matrix.md).
| Document | Status | Last Updated |
|---|---|---|
| README.md | ✅ Complete | 2025-01 |
| requirements/requirements-document.md | ✅ Complete | 2025-01 |
| requirements/user-stories.md | ✅ Complete | 2025-01 |
| architecture/system-design.md | 🔲 Planned | — |
| architecture/data-model.md | 🔲 Planned | — |
| architecture/api-design.md | 🔲 Planned | — |
| architecture/integration-map.md | 🔲 Planned | — |
| design/ux-flows.md | 🔲 Planned | — |
| modules/job-posting.md | 🔲 Planned | — |
| modules/candidate-portal.md | 🔲 Planned | — |
| modules/ats-pipeline.md | 🔲 Planned | — |
| modules/interview-management.md | 🔲 Planned | — |
| modules/offer-management.md | 🔲 Planned | — |
| modules/analytics.md | 🔲 Planned | — |
| modules/integrations.md | 🔲 Planned | — |
| compliance/gdpr.md | 🔲 Planned | — |
| compliance/eeo-ofccp.md | 🔲 Planned | — |
| compliance/pay-transparency.md | 🔲 Planned | — |
| operations/deployment.md | 🔲 Planned | — |
| operations/monitoring.md | 🔲 Planned | — |

---

## Contributing

1. Fork the repository and create a feature branch: `git checkout -b feature/your-feature-name`
2. Follow the TypeScript and ESLint configuration enforced by the project
3. Write unit tests for all new business logic; maintain ≥ 80% coverage on changed files
4. Run `npm run lint && npm run test` before opening a pull request
5. Reference the relevant requirement ID (e.g., `FR-12`, `NFR-05`) in your PR description where applicable
6. Request review from at least one platform owner and one domain expert (recruiting ops)

---

## License

This project is proprietary software. All rights reserved. See `LICENSE` for details.
