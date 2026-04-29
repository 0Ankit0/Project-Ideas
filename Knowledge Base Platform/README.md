# Knowledge Base Platform

> **A unified internal and external knowledge management platform — team wikis, customer help centers, AI-powered semantic search, versioned articles, and contextual in-app help widgets.**

---

## Documentation Structure

Project root artifact: [`traceability-matrix.md`](./traceability-matrix.md) provides cross-phase requirement-to-implementation linkage.

```text
Knowledge Base Platform/
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
│   ├── api-design.md                         ← REST/GraphQL API contracts
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
    ├── content-authoring.md                 ← Content authoring and versioning edge cases
    ├── search-and-retrieval.md              ← Search and retrieval edge cases
    ├── access-and-permissions.md            ← Access control edge cases
    ├── ai-assistant.md                      ← AI assistant failure modes
    ├── security-and-compliance.md           ← Security threats and compliance violations
    └── operations.md                        ← Operational runbooks and incident response
```

---

## Key Features

- **Content Authoring** — Rich-text editing with TipTap, block-level components, slash commands, inline comments, collaborative real-time editing, autosave, and revision history.
- **Knowledge Organization** — Hierarchical spaces and collections, drag-and-drop reordering, tagging taxonomy, cross-linking, templates library, and table-of-contents generation.
- **Search** — Full-text search via Elasticsearch 8 with typo-tolerance, faceted filters, search-as-you-type, and pgvector hybrid semantic search for relevance-ranked results.
- **AI Assistant** — GPT-4o powered Q&A over your knowledge base, article summarization, auto-tagging, suggested related articles, gap detection, and draft generation from prompts.
- **Access Control** — Five-role RBAC (Author, Editor, Reader, Workspace Admin, Super Admin), article-level visibility (public/internal/private), SSO via SAML 2.0 / OIDC, and IP allowlisting.
- **In-App Help Widget** — Embeddable JS snippet with contextual article suggestions, smart search overlay, AI chat, feedback thumbs, and customizable branding per workspace.
- **Customer Feedback** — Per-article helpfulness ratings, inline comment threads, escalation to support tickets (Zendesk/Intercom), and automated low-score alerts.
- **Multi-workspace** — Isolated workspaces with custom domains, themes, and member directories; cross-workspace article sharing with permission inheritance.
- **Analytics Dashboard** — Article-level pageviews, search-no-result rates, deflection metrics, reader heatmaps, author contribution stats, and exportable CSV/PDF reports.
- **Integrations** — Slack (notify on publish), Zendesk (deflection sync), GitHub (embed code snippets), Jira (link issues to articles), Zapier webhooks, and REST + GraphQL APIs.

---

## Primary Roles

| Role | Description | Key Capabilities |
|---|---|---|
| **Author** | Content creator who drafts and maintains articles | Create/edit own drafts, submit for review, manage personal article library, view own analytics |
| **Editor** | Content reviewer who approves and publishes | All Author capabilities, approve/reject submissions, publish articles, bulk-edit metadata, manage tags |
| **Reader** | End-user consumer of published content | Read public and permitted articles, search, use AI assistant, submit feedback, rate articles |
| **Workspace Admin** | Manages a single workspace's settings and membership | All Editor capabilities, invite/remove members, configure SSO, manage custom domain, view workspace analytics |
| **Super Admin** | Platform-level administrator across all workspaces | All Workspace Admin capabilities, create/delete workspaces, manage billing, override permissions, access audit logs |

---

## Getting Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/knowledge-base-platform.git
   cd knowledge-base-platform
   ```

2. **Copy environment files**
   ```bash
   cp apps/backend/.env.example apps/backend/.env
   cp apps/frontend/.env.example apps/frontend/.env.local
   ```

3. **Fill in environment variables** — Set `DATABASE_URL`, `REDIS_URL`, `ELASTICSEARCH_URL`, `OPENAI_API_KEY`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `S3_BUCKET`, `JWT_SECRET`.

4. **Start infrastructure with Docker Compose**
   ```bash
   docker compose -f infrastructure/docker-compose.yml up -d
   ```

5. **Run database migrations**
   ```bash
   cd apps/backend && npm run migration:run
   ```

6. **Seed development data**
   ```bash
   npm run seed:dev
   ```

7. **Start backend development server**
   ```bash
   npm run start:dev   # NestJS on http://localhost:3001
   ```

8. **Start frontend development server**
   ```bash
   cd ../frontend && npm run dev   # Next.js on http://localhost:3000
   ```

9. **Open the application** — Navigate to `http://localhost:3000` and log in with seed credentials `admin@example.com / Password123!`.

10. **Configure your first workspace** — Go to Settings → Workspaces → New Workspace, set a name, slug, and custom domain, then invite team members.

11. **Embed the help widget** — Copy the snippet from Settings → Widget → Embed Code and paste it into your product's `<head>` tag.

12. **Access the Super Admin panel** — Navigate to `http://localhost:3000/admin` using the Super Admin seed account.

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Backend Runtime** | Node.js 20 | Server-side JavaScript runtime |
| **Backend Framework** | NestJS (TypeScript) | Modular, decorator-driven REST + GraphQL API framework |
| **ORM** | TypeORM | Entity mapping, migrations, query builder for PostgreSQL |
| **Frontend Framework** | Next.js 14 (App Router) | SSR/SSG React framework with server components |
| **Frontend Language** | TypeScript | Static typing across client and server |
| **Rich Text Editor** | TipTap | ProseMirror-based extensible WYSIWYG editor |
| **Styling** | Tailwind CSS | Utility-first CSS framework |
| **Primary Database** | PostgreSQL 15 | Relational storage for articles, users, workspaces |
| **Vector Extension** | pgvector | Cosine similarity search on embeddings stored in Postgres |
| **Cache / Queue Broker** | Redis 7 | Session cache, rate limiting, BullMQ job broker |
| **Search Engine** | Elasticsearch 8 | Full-text, faceted, and autocomplete search |
| **AI Language Model** | OpenAI GPT-4o | Q&A, summarization, draft generation |
| **AI Embeddings** | text-embedding-3-small | Semantic vector embeddings for hybrid search |
| **AI Orchestration** | LangChain.js | Chains, retrieval-augmented generation (RAG), memory |
| **Job Queue** | BullMQ | Async indexing, email, embedding, report jobs |
| **Object Storage** | AWS S3 | Media, attachment, and export file storage |
| **CDN** | AWS CloudFront | Low-latency asset and widget delivery |
| **Container Orchestration** | AWS ECS Fargate | Serverless container hosting |
| **Managed Database** | AWS RDS PostgreSQL | Production-grade managed Postgres |
| **Managed Cache** | AWS ElastiCache Redis | Production Redis cluster |
| **Managed Search** | Amazon OpenSearch Service | Managed Elasticsearch-compatible search |
| **DNS** | AWS Route 53 | Domain routing and health checks |
| **WAF** | AWS WAF | Web application firewall, rate limiting, IP rules |

---

## Documentation Status

| # | File | Status |
|---|---|---|
| 1 | `README.md` | ✅ |
| 2 | `requirements/requirements-document.md` | ✅ |
| 3 | `requirements/user-stories.md` | ✅ |
| 4 | `analysis/competitive-analysis.md` | ✅ |
| 5 | `analysis/domain-model.md` | ✅ |
| 6 | `analysis/risk-register.md` | ✅ |
| 7 | `high-level-design/system-overview.md` | ✅ |
| 8 | `high-level-design/architecture-diagram.md` | ✅ |
| 9 | `high-level-design/data-flow.md` | ✅ |
| 10 | `high-level-design/api-contracts.md` | ✅ |
| 11 | `detailed-design/content-authoring-service.md` | ✅ |
| 12 | `detailed-design/search-service.md` | ✅ |
| 13 | `detailed-design/ai-assistant-service.md` | ✅ |
| 14 | `detailed-design/access-control-service.md` | ✅ |
| 15 | `detailed-design/widget-service.md` | ✅ |
| 16 | `detailed-design/analytics-service.md` | ✅ |
| 17 | `detailed-design/notification-service.md` | ✅ |
| 18 | `detailed-design/media-service.md` | ✅ |
| 19 | `detailed-design/feedback-service.md` | ✅ |
| 20 | `detailed-design/workspace-service.md` | ✅ |
| 21 | `infrastructure/aws-architecture.md` | ✅ |
| 22 | `infrastructure/docker-compose.yml` | ✅ |
| 23 | `infrastructure/ecs-task-definitions.md` | ✅ |
| 24 | `infrastructure/rds-schema.md` | ✅ |
| 25 | `infrastructure/elasticsearch-mappings.md` | ✅ |
| 26 | `infrastructure/redis-cache-strategy.md` | ✅ |
| 27 | `infrastructure/ci-cd-pipeline.md` | ✅ |
| 28 | `edge-cases/content-conflicts.md` | ✅ |
| 29 | `edge-cases/search-edge-cases.md` | ✅ |
| 30 | `edge-cases/ai-failure-modes.md` | ✅ |
| 31 | `edge-cases/access-control-edge-cases.md` | ✅ |
| 32 | `implementation/backend-setup.md` | ✅ |
| 33 | `implementation/frontend-setup.md` | ✅ |
| 34 | `implementation/database-migrations.md` | ✅ |
| 35 | `implementation/search-indexing.md` | ✅ |

---

## Delivery Blueprint

| Phase | Milestone | Duration | Deliverables |
|---|---|---|---|
| **1 — Discovery** | Requirements & Architecture Finalized | 2 weeks | Requirements doc, user stories, domain model, risk register, ADRs |
| **2 — Foundation** | Core Infrastructure & Auth Live | 3 weeks | NestJS scaffold, Next.js scaffold, Postgres schema v1, Redis/BullMQ integration, JWT + RBAC auth, CI/CD pipeline |
| **3 — Core Content** | Authoring & Search Operational | 4 weeks | TipTap editor, article CRUD + versioning, space/collection hierarchy, Elasticsearch indexing, basic full-text search, S3 media upload |
| **4 — AI & Widget** | AI Assistant & Help Widget Shipped | 4 weeks | GPT-4o Q&A chain, text-embedding-3-small indexing, hybrid search, pgvector similarity, embeddable widget JS bundle, contextual suggestions |
| **5 — Analytics & Integrations** | Dashboard & Third-party Integrations Live | 3 weeks | Analytics ingestion pipeline, dashboard UI, Slack/Zendesk/GitHub integrations, Zapier webhook support, REST + GraphQL API docs |
| **6 — Hardening & GA** | Production Launch | 2 weeks | Load testing, WAF rules, penetration test, GDPR compliance review, SLA monitoring, runbooks, GA release |

---

## Operational Policy Addendum

### Content Governance Policies

**Article Lifecycle**
Every article follows a defined lifecycle: `Draft → In Review → Approved → Published → Archived`. No article may transition directly from Draft to Published without passing through the In Review and Approved states unless the author also holds the Editor role or above. Archived articles are read-only and are retained for a minimum of 12 months before being eligible for permanent deletion.

**Editorial Workflow**
Editors are responsible for reviewing submitted articles within 5 business days. Articles idle in the In Review state for more than 10 business days are automatically flagged and an escalation notification is sent to the Workspace Admin. All review decisions (approve, reject, request-changes) must include a written comment of at least 20 characters.

**Content Retention**
Published article versions are retained indefinitely by default. Workspace Admins may configure a retention policy (minimum 6 months) that archives and optionally purges article versions older than the configured window. Audit logs for all content mutations are retained for 24 months and are non-deletable by Workspace Admins — only Super Admins may initiate a log purge with mandatory approval workflow.

---

### Reader Data Privacy Policies

**GDPR / CCPA Compliance**
Reader personally identifiable information (PII) — including email addresses, IP addresses, device fingerprints, and session identifiers — is processed only with a valid legal basis. For authenticated readers, the legal basis is contractual necessity. For anonymous widget users, the legal basis is legitimate interest, limited strictly to aggregate analytics. No Reader PII is sold or shared with third parties except as required by law or with explicit opt-in consent.

**Analytics Anonymization**
All analytics events are anonymized at ingestion: IP addresses are truncated to /24 (IPv4) or /48 (IPv6) before storage. User-agent strings are parsed for OS and browser family only. Session identifiers are salted and hashed daily so that cross-day linkage is not possible. Workspace Admins may access only aggregate metrics; individual reader journey data is accessible only to Super Admins for fraud investigation.

**Cookie Consent**
The help widget and public knowledge base must display a GDPR-compliant cookie banner on first load for visitors from EU/EEA/UK jurisdictions. Analytics tracking cookies are not set until consent is granted. Functional cookies (session, CSRF token) are exempt from consent as they are strictly necessary.

---

### AI Usage Policies

**LLM Data Handling**
All content sent to OpenAI APIs is governed by the OpenAI Enterprise Data Processing Agreement. Article content used for AI Q&A and summarization is transmitted over TLS 1.3 and is not used by OpenAI to train its models under the enterprise agreement. The platform does not store raw OpenAI API responses beyond the request lifecycle unless explicitly cached for performance.

**Opt-Out**
Workspace Admins may disable AI features on a per-workspace basis via Settings → AI → Enable AI Features toggle. When disabled, no article content is sent to OpenAI APIs and the AI chat interface is hidden from all users in that workspace. Authors may individually mark articles as "AI-excluded" to prevent their content from being included in RAG retrieval chains.

**No PII in Prompts**
The platform's prompt construction pipeline strips detected PII (email addresses, phone numbers, national ID patterns) from article content before sending to the LLM using a regex + NER pre-processing step. Prompts are logged to an internal audit table (not to OpenAI) with the PII-stripped version only. Developers must not add prompt construction logic that reintroduces PII fields from user profiles.

---

### System Availability Policies

**SLA Targets**
The platform commits to 99.9% monthly uptime for the API and frontend (≤ 43.8 minutes downtime/month). The AI Assistant feature targets 99.5% uptime independently, as it depends on the OpenAI API which is outside our infrastructure boundary. The help widget CDN bundle (CloudFront) targets 99.99% availability. SLA credits are issued for breaches as per the service agreement.

**RTO / RPO**
Recovery Time Objective (RTO): ≤ 1 hour for full API/frontend restore following a catastrophic failure.  
Recovery Point Objective (RPO): ≤ 15 minutes for PostgreSQL data (achieved via RDS Multi-AZ + point-in-time recovery with 5-minute WAL shipping).  
Elasticsearch indices can be rebuilt from PostgreSQL in < 2 hours and are therefore excluded from the RPO calculation.

**Incident Escalation**
Severity 1 (full outage): PagerDuty alert → on-call engineer within 5 minutes → incident channel opened → status page updated within 10 minutes → customer communication within 30 minutes.  
Severity 2 (degraded performance): PagerDuty alert → on-call engineer within 15 minutes → root cause analysis within 4 hours.  
Severity 3 (minor issues): Ticket created → triaged within 1 business day → resolved within 5 business days.  
Post-incident reviews are mandatory for all Severity 1 and 2 events and must be published internally within 5 business days.
