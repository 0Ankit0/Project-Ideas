# Customer Relationship Management Platform

**Version:** 1.0 | **Status:** Approved | **Last Updated:** 2025-07-15

---

## Project Description

The **Enterprise Customer Relationship Management (CRM) Platform** is a purpose-built SaaS solution that centralises lead capture, contact and account management, opportunity pipeline tracking, territory management, campaign execution, revenue forecasting, and full activity history for B2B sales organisations. It serves as the single source of truth for every customer-facing interaction, enabling sales teams to close deals faster, managers to forecast with confidence, and operations teams to maintain data integrity at scale.

The platform is designed around a multi-tenant architecture supporting thousands of concurrent users, with strict data isolation, GDPR-compliant data handling, and enterprise-grade integrations with ERP, marketing automation, and communication tools.

---

## Key Features

- **Lead Capture & Scoring** — Ingest leads via embeddable web forms, REST API webhooks, and bulk CSV import; automatically score each lead 0–100 using a configurable rule engine based on firmographic, demographic, and behavioural signals.
- **Pipeline Management** — Configure unlimited named pipelines with custom stages and entry/exit gate criteria; enforce stage-progression rules and track deal velocity, age, and stagnation alerts.
- **Contact & Account 360 View** — Unified record page surfacing all activities, open and closed deals, email threads, meeting history, tasks, notes, and custom field data for any Contact or Account.
- **Email & Calendar Sync** — Bidirectional OAuth 2.0 integration with Google Workspace and Microsoft 365; automatic email thread association to Contact/Deal records; meeting creation sync with calendar invites.
- **Activity Timeline** — Chronological, filterable log of every call, email, meeting, task, and note across all CRM objects; searchable full-text across content and participants.
- **Revenue Forecasting** — Rep-level committed/best-case/pipeline submissions rolled up to manager and VP layers; weighted probability forecast, historical accuracy tracking, and snapshot locking for period-end auditing.
- **Territory Management** — Rule-based territory assignment by geography, industry, account size, or custom criteria; territory hierarchy with ownership inheritance; conflict resolution workflow and annual rebalancing tools.
- **Campaign Management** — Multi-step email campaign builder with segment-based targeting; A/B variant support; open/click/bounce tracking; automated drip sequences; CAN-SPAM and GDPR unsubscribe handling.
- **Deduplication Engine** — Probabilistic matching on name, email, phone, and domain fields; automated merge for high-confidence duplicates; human-review queue for medium-confidence matches; merge audit trail.
- **Custom Fields & Objects** — Tenant-configurable fields on all core objects (text, number, date, picklist, multi-select, formula, lookup); field-level permissions; schema versioning with migration history.
- **Integrations** — Native connectors for Slack and Microsoft Teams (deal alerts, task reminders), Google Workspace and Microsoft 365 (email/calendar), ERP systems via REST webhooks, and extensible integration framework for custom third-party connections.

---

## Actors

| Actor | Role Description |
|---|---|
| **Sales Rep** | Day-to-day user who captures leads, manages contacts, progresses deals through pipeline stages, logs activities, and submits individual forecasts. |
| **Sales Manager** | Oversees a team of Sales Reps; reviews pipeline health, approves forecast submissions, manages territory assignments, and coaches reps via activity reports. |
| **RevOps Analyst** | Designs pipeline stages, configures assignment rules, manages territory hierarchies, builds reports and dashboards, and ensures data quality across the tenant. |
| **CRM Administrator** | Manages tenant configuration including custom fields, integrations, user permissions, role-based access control, and data import/export operations. |
| **Marketing Manager** | Creates audience segments, builds and launches email campaigns, monitors campaign analytics, manages unsubscribe lists, and coordinates lead handoff rules with Sales. |
| **System Integrator** | Configures and maintains integrations with external systems (ERP, marketing automation, identity provider, billing); manages API credentials and webhook subscriptions. |

---

## Documentation Structure

Project root artifact: [`traceability-matrix.md`](./traceability-matrix.md) provides cross-phase requirement-to-implementation linkage.


| # | Document | Path | Description |
|---|---|---|---|
| 1 | Requirements Specification | [requirements/requirements.md](requirements/requirements.md) | Functional (FR-001–FR-035) and non-functional requirements (NFR-001–NFR-015) with priority and acceptance criteria |
| 2 | User Stories | [requirements/user-stories.md](requirements/user-stories.md) | Persona-based user stories (US-001–US-045) with Given/When/Then acceptance criteria |
| 3 | Use Case Diagram | [analysis/use-case-diagram.md](analysis/use-case-diagram.md) | Mermaid use case diagram covering UC-001–UC-012 with actor associations |
| 4 | Use Case Descriptions | [analysis/use-case-descriptions.md](analysis/use-case-descriptions.md) | Detailed flows for UC-001–UC-006 including main, alternative, and exception flows |
| 5 | System Context Diagram | [analysis/system-context-diagram.md](analysis/system-context-diagram.md) | C4-style context diagram showing CRM boundary and all external integrations |
| 6 | Activity Diagrams | [analysis/activity-diagrams.md](analysis/activity-diagrams.md) | Mermaid flowcharts for lead capture, opportunity progression, and territory reassignment |
| 7 | Swimlane Diagrams | [analysis/swimlane-diagrams.md](analysis/swimlane-diagrams.md) | Cross-service sequence diagrams for lead conversion and forecast approval |
| 8 | Data Dictionary | [analysis/data-dictionary.md](analysis/data-dictionary.md) | Field-level definitions for all core CRM entities |
| 9 | Business Rules | [analysis/business-rules.md](analysis/business-rules.md) | Enumerated business rules referenced by use cases and requirements |
| 10 | Event Catalog | [analysis/event-catalog.md](analysis/event-catalog.md) | Domain events with payload schemas and consumer mappings |
| 11 | Architecture Diagram | [high-level-design/architecture-diagram.md](high-level-design/architecture-diagram.md) | High-level system architecture showing service boundaries and infrastructure layers |
| 12 | Domain Model | [high-level-design/domain-model.md](high-level-design/domain-model.md) | Conceptual domain model with aggregate roots and bounded contexts |
| 13 | Data Flow Diagrams | [high-level-design/data-flow-diagrams.md](high-level-design/data-flow-diagrams.md) | DFD Level-0 and Level-1 for core CRM processes |
| 14 | System Sequence Diagrams | [high-level-design/system-sequence-diagrams.md](high-level-design/system-sequence-diagrams.md) | System-level sequence diagrams for primary workflows |
| 15 | C4 Diagrams (L1–L2) | [high-level-design/c4-diagrams.md](high-level-design/c4-diagrams.md) | C4 System Context and Container diagrams |
| 16 | Class Diagrams | [detailed-design/class-diagrams.md](detailed-design/class-diagrams.md) | UML class diagrams for all domain aggregates and services |
| 17 | Sequence Diagrams | [detailed-design/sequence-diagrams.md](detailed-design/sequence-diagrams.md) | Detailed inter-service sequence diagrams for complex workflows |
| 18 | State Machine Diagrams | [detailed-design/state-machine-diagrams.md](detailed-design/state-machine-diagrams.md) | State machines for Lead, Deal, Campaign, and Task lifecycles |
| 19 | ERD & Database Schema | [detailed-design/erd-database-schema.md](detailed-design/erd-database-schema.md) | Complete entity-relationship diagram and DDL schema definitions |
| 20 | Component Diagrams | [detailed-design/component-diagrams.md](detailed-design/component-diagrams.md) | Internal component breakdown of each microservice |
| 21 | API Design | [detailed-design/api-design.md](detailed-design/api-design.md) | OpenAPI-aligned endpoint specifications with request/response schemas |
| 22 | C4 Component Diagram (L3) | [detailed-design/c4-component-diagram.md](detailed-design/c4-component-diagram.md) | C4 Component-level diagram for the CRM API Gateway and core services |
| 23 | Lead Scoring & Deduplication | [detailed-design/lead-scoring-and-deduplication.md](detailed-design/lead-scoring-and-deduplication.md) | Algorithm specifications for the scoring engine and probabilistic dedup matcher |
| 24 | Deployment Diagram | [infrastructure/deployment-diagram.md](infrastructure/deployment-diagram.md) | Production deployment topology on Kubernetes with ingress, services, and storage |
| 25 | Network Infrastructure | [infrastructure/network-infrastructure.md](infrastructure/network-infrastructure.md) | VPC layout, subnet design, security groups, and network policies |
| 26 | Cloud Architecture | [infrastructure/cloud-architecture.md](infrastructure/cloud-architecture.md) | AWS/GCP reference architecture with managed services and HA configuration |
| 27 | Implementation Guidelines | [implementation/implementation-guidelines.md](implementation/implementation-guidelines.md) | Coding standards, branching strategy, API conventions, and error handling patterns |
| 28 | C4 Code Diagram (L4) | [implementation/c4-code-diagram.md](implementation/c4-code-diagram.md) | C4 Code-level diagram for the Lead Scoring Engine |
| 29 | Backend Status Matrix | [implementation/backend-status-matrix.md](implementation/backend-status-matrix.md) | Implementation status of all API endpoints and background jobs |
| 30 | Edge Cases Overview | [edge-cases/README.md](edge-cases/README.md) | Index and severity classification of all documented edge cases |
| 31 | Dedupe & Merge Conflicts | [edge-cases/dedupe-merge-conflicts.md](edge-cases/dedupe-merge-conflicts.md) | Edge cases in contact deduplication, merge ordering, and conflict resolution |
| 32 | Territory Reassignment | [edge-cases/territory-reassignment.md](edge-cases/territory-reassignment.md) | Edge cases for mid-cycle territory changes, orphaned records, and rep transitions |
| 33 | Forecast Integrity | [edge-cases/forecast-integrity.md](edge-cases/forecast-integrity.md) | Edge cases for concurrent forecast edits, period close, and rollup inconsistency |
| 34 | Email & Calendar Sync | [edge-cases/email-calendar-sync.md](edge-cases/email-calendar-sync.md) | Edge cases for OAuth token expiry, duplicate events, and partial sync failures |
| 35 | API & UI Edge Cases | [edge-cases/api-and-ui.md](edge-cases/api-and-ui.md) | Rate limit handling, pagination edge cases, and UI race conditions |
| 36 | Security & Compliance | [edge-cases/security-and-compliance.md](edge-cases/security-and-compliance.md) | GDPR erasure race conditions, permission escalation, and audit log tampering |
| 37 | Operations Edge Cases | [edge-cases/operations.md](edge-cases/operations.md) | Deployment rollback, database migration failures, and backup restoration |

---

## Getting Started

- Review [`traceability-matrix.md`](./traceability-matrix.md) first to navigate requirement-to-implementation coverage across phases.
### Prerequisites

- Node.js 20 LTS or later
- PostgreSQL 15+ (primary datastore)
- Redis 7+ (session cache, queue broker)
- Docker and Docker Compose (local development)

### Quick Start (Local Development)

```bash
# 1. Clone the repository
git clone https://github.com/your-org/crm-platform.git
cd crm-platform

# 2. Copy environment template and configure
cp .env.example .env
# Edit .env with your database credentials, OAuth client IDs, and SMTP settings

# 3. Start infrastructure services
docker compose up -d postgres redis

# 4. Install dependencies and run database migrations
npm install
npm run db:migrate

# 5. Seed reference data (pipeline templates, default roles)
npm run db:seed

# 6. Start the development server
npm run dev
# API available at http://localhost:3000
# Web UI available at http://localhost:5173
```

### Environment Variables

| Variable | Description | Required |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `REDIS_URL` | Redis connection string | Yes |
| `JWT_SECRET` | 256-bit secret for JWT signing | Yes |
| `GOOGLE_OAUTH_CLIENT_ID` | Google Workspace OAuth client ID | Optional |
| `GOOGLE_OAUTH_CLIENT_SECRET` | Google Workspace OAuth client secret | Optional |
| `MICROSOFT_OAUTH_CLIENT_ID` | Microsoft 365 OAuth client ID | Optional |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook URL | Optional |
| `SMTP_HOST` | Outbound email relay host | Yes |

### Running Tests

```bash
npm run test:unit        # Unit tests (Jest)
npm run test:integration # Integration tests against test database
npm run test:e2e         # End-to-end tests (Playwright)
npm run test:coverage    # Full coverage report
```

---

## Documentation Status

- ✅ Traceability coverage is available via [`traceability-matrix.md`](./traceability-matrix.md).
| Document | Status | Last Reviewed |
|---|---|---|
| requirements/requirements.md | Approved | 2025-07-15 |
| requirements/user-stories.md | Approved | 2025-07-15 |
| analysis/use-case-diagram.md | Approved | 2025-07-15 |
| analysis/use-case-descriptions.md | Approved | 2025-07-15 |
| analysis/system-context-diagram.md | Approved | 2025-07-15 |
| analysis/activity-diagrams.md | Approved | 2025-07-15 |
| analysis/swimlane-diagrams.md | Approved | 2025-07-15 |
| analysis/data-dictionary.md | Approved | 2025-07-15 |
| analysis/business-rules.md | Approved | 2025-07-15 |
| analysis/event-catalog.md | Approved | 2025-07-15 |
| high-level-design/architecture-diagram.md | Approved | 2025-07-15 |
| high-level-design/domain-model.md | Approved | 2025-07-15 |
| high-level-design/data-flow-diagrams.md | Approved | 2025-07-15 |
| high-level-design/system-sequence-diagrams.md | Approved | 2025-07-15 |
| high-level-design/c4-diagrams.md | Approved | 2025-07-15 |
| detailed-design/class-diagrams.md | Approved | 2025-07-15 |
| detailed-design/sequence-diagrams.md | Approved | 2025-07-15 |
| detailed-design/state-machine-diagrams.md | Approved | 2025-07-15 |
| detailed-design/erd-database-schema.md | Approved | 2025-07-15 |
| detailed-design/component-diagrams.md | Approved | 2025-07-15 |
| detailed-design/api-design.md | Approved | 2025-07-15 |
| detailed-design/c4-component-diagram.md | Approved | 2025-07-15 |
| detailed-design/lead-scoring-and-deduplication.md | Approved | 2025-07-15 |
| infrastructure/deployment-diagram.md | Approved | 2025-07-15 |
| infrastructure/network-infrastructure.md | Approved | 2025-07-15 |
| infrastructure/cloud-architecture.md | Approved | 2025-07-15 |
| implementation/implementation-guidelines.md | Approved | 2025-07-15 |
| implementation/c4-code-diagram.md | Approved | 2025-07-15 |
| implementation/backend-status-matrix.md | Approved | 2025-07-15 |
| edge-cases/README.md | Approved | 2025-07-15 |
| edge-cases/dedupe-merge-conflicts.md | Approved | 2025-07-15 |
| edge-cases/territory-reassignment.md | Approved | 2025-07-15 |
| edge-cases/forecast-integrity.md | Approved | 2025-07-15 |
| edge-cases/email-calendar-sync.md | Approved | 2025-07-15 |
| edge-cases/api-and-ui.md | Approved | 2025-07-15 |
| edge-cases/security-and-compliance.md | Approved | 2025-07-15 |
| edge-cases/operations.md | Approved | 2025-07-15 |

---

*For questions or contributions, open an issue or pull request against the `main` branch. All documentation changes require review from a RevOps Analyst or CRM Administrator before merge.*
