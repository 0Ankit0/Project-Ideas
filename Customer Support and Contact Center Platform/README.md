# Customer Support and Contact Center Platform

![Status](https://img.shields.io/badge/status-production--ready-brightgreen)
![Documentation](https://img.shields.io/badge/docs-complete-blue)
![Architecture](https://img.shields.io/badge/architecture-microservices-orange)
![Compliance](https://img.shields.io/badge/compliance-GDPR%20%7C%20CCPA%20%7C%20HIPAA-red)
![Channels](https://img.shields.io/badge/channels-omnichannel-purple)

> A production-grade, cloud-native Customer Support and Contact Center Platform that unifies every customer interaction — email, live chat, voice, social media, SMS, and WhatsApp — into a single intelligent workspace. The platform delivers AI-powered routing, real-time SLA governance, conversational bots with seamless human handoff, a self-service knowledge base, and a 360° customer profile, enabling support teams to resolve issues faster, maintain compliance, and continuously improve service quality through rich workforce analytics.

---

## Table of Contents

- [Key Features](#key-features)
- [System Actors](#system-actors)
- [Architecture Overview](#architecture-overview)
- [Technology Stack](#technology-stack)
- [Documentation Structure](#documentation-structure)
- [Key Design Decisions](#key-design-decisions)
- [Getting Started](#getting-started)
- [Documentation Status](#documentation-status)

---

## Key Features

### 🎫 Omni-Channel Ticket Management
- Unified inbox aggregating tickets from **email, live chat, voice/telephony, social media (Twitter/Facebook/Instagram), SMS, and WhatsApp** into a single normalized conversation model.
- Full **thread deduplication** — replies to the same email thread or conversation ID are automatically merged into one ticket rather than spawning duplicates.
- **Ticket lifecycle management**: create, update, assign, merge, split, tag, close, and reopen with full immutable audit trail on every state transition.
- Secure **attachment handling** (images, documents, audio recordings) with virus scanning, size limits, and per-tenant storage quotas.
- **Bulk operations**: mass assign, mass close, mass tag, and mass export for supervisor efficiency.

### 🔀 Intelligent Routing & Assignment
- **Skill-based routing**: tickets are matched to agents whose skill profiles (language, product line, technical tier) satisfy the ticket's requirements.
- **Availability-aware routing**: the engine checks agent status (Online, Busy, Away, Offline) and current workload before assignment.
- **Round-robin and load-balancing** modes configurable per queue to distribute volume evenly.
- **Overflow routing**: when a queue breaches a configurable depth or wait-time threshold, tickets spill over to a secondary queue or on-call pool.
- **Auto-assignment rules** with priority multipliers based on customer tier, product, and topic.

### ⏱️ SLA Tracking & Auto-Escalation
- Policy-driven **SLA contracts** per customer tier, channel, and topic: first-response time, next-response time, and resolution time.
- Real-time **SLA clock** with pause/resume support for pending-customer or business-hours-only policies.
- Proactive **warning alerts** at configurable thresholds (e.g., 75% of SLA window elapsed) surfaced to agents and supervisors.
- **Auto-escalation workflows**: breach-risk tickets are automatically reassigned or flagged to a supervisor with an escalation note.
- Full SLA reporting with breach-rate trends per queue, agent, and channel.

### 🤖 AI Chatbot with NLP & Human Handoff
- **Conversational bot flows** built on intent-based NLP supporting multi-turn dialogues, entity extraction, and contextual slot filling.
- **Confidence threshold handoff**: when intent confidence drops below a configurable threshold the bot gracefully transfers the session to a live agent, passing the full conversation transcript.
- **Bot-authored draft responses** suggested to human agents after handoff to accelerate reply time.
- IVR integration for voice channel with DTMF and speech recognition; IVR tree maps to the same intent model as the chat bot.
- Bot session analytics: containment rate, deflection rate, escalation rate, and CSAT per bot flow.

### 📚 Knowledge Base with AI-Powered Search
- Structured **article authoring** with rich text, code blocks, images, and video embeds; full version history and rollback.
- **AI semantic search** returns ranked results based on query meaning, not just keyword match, reducing agent time-to-answer.
- **In-ticket article suggestions**: the platform automatically surfaces the top-3 relevant KB articles as an agent types a reply.
- **Customer-facing self-service portal** with category browse, search, and article rating (helpful/not helpful).
- Article feedback loop: low-rated articles are flagged for review; trending search terms with no results generate gap reports.

### 👤 Customer 360° Profile
- Unified customer record aggregating contact details, company, lifetime conversation history, purchase history (via CRM integration), open tickets, and preferences.
- **Contact deduplication and merge** to handle the same customer reaching out across multiple channels or email addresses.
- CSAT and NPS survey response history visible on the profile for holistic sentiment tracking.
- Timeline view showing every touchpoint — ticket, chat, call, bot session, survey — in chronological order.

### 📊 CSAT / NPS Surveys
- **Automated CSAT surveys** triggered on ticket close via email, SMS, or in-app; configurable delay and exclusion rules.
- **NPS surveys** delivered on a rolling schedule with configurable cadence per customer segment.
- Responses linked to the specific agent, ticket, and queue for granular performance attribution.
- Real-time CSAT and NPS dashboard with trend charts, agent leaderboards, and drill-down to verbatim comments.

### 🗓️ Workforce Management & Scheduling
- Agent **shift scheduling** with daily/weekly schedule templates, time-off requests, and shift swap approvals.
- Real-time **occupancy and adherence** tracking — how closely agents stick to their scheduled activities.
- **Staffing forecasts** based on historical volume patterns by hour, day of week, and channel.
- Workload heatmaps and capacity planning views for workforce managers.

### 🖥️ Real-Time Supervisor Dashboard
- Live queue view showing ticket counts, wait times, SLA risk indicators, and per-agent status at a glance.
- **Agent monitoring panel**: current ticket, handle time, status duration, and today's CSAT score per agent.
- **Silent monitoring** and **whisper coaching** hooks for voice calls (supervisor can listen in or coach without the customer hearing).
- One-click **forced requeue** and **emergency escalation** controls for supervisors to intervene instantly.

### 📞 Call Recording & Transcription
- All inbound and outbound voice calls recorded with secure, encrypted storage and configurable retention policies.
- Automatic **speech-to-text transcription** with speaker diarization (agent vs customer) and confidence scores.
- Transcripts indexed for full-text search; surfaced on ticket timeline alongside the audio recording.
- Redaction pipeline strips PCI/PII tokens (card numbers, SSNs) from transcripts per GDPR/CCPA compliance rules.

### 🔒 Privacy, GDPR & Data Retention
- Configurable **data retention policies** per region and data class; automated purge jobs with cryptographic deletion confirmation.
- **Right-to-erasure** (GDPR Article 17) workflows: customer data redacted from tickets, transcripts, and search indexes while preserving anonymized aggregate analytics.
- **Consent management** for recording, survey, and marketing communications.
- Full **audit log** of every data access, export, redaction, and privilege escalation event, immutable and exportable for regulatory inspection.

### 📈 Reports & Analytics
- **Real-time operational dashboard** with configurable widgets: queue depth, SLA health, agent availability, CSAT trend.
- **Historical reporting** with date-range filters, group-by dimensions (agent, team, channel, topic, customer tier), and exportable CSV/PDF.
- **Custom report builder** allowing non-technical users to assemble ad hoc reports from a curated metric catalog.
- Pre-built **SLA compliance reports**, **agent performance scorecards**, and **channel volume trend** reports.

### 🔗 CRM & Third-Party Integrations
- Native connectors for **Salesforce, HubSpot, Zendesk (migration)**, and generic REST/webhook CRM adapters.
- Bidirectional sync: tickets update CRM case records; CRM opportunity data enriches customer profiles.
- **Zapier / webhook outbound** triggers on ticket events for lightweight no-code integrations.
- OAuth 2.0-secured API for custom integrations with rate-limit tiers per tenant.

---

## System Actors

| Actor | Role | Primary Interactions |
|---|---|---|
| **Customer** | End-user seeking support | Submits tickets via any channel, receives responses, completes surveys, uses self-service KB and bot |
| **Support Agent** | Frontline responder | Manages assigned tickets, responds via unified inbox, uses KB suggestions, handles chat/voice |
| **Team Lead** | First-level escalation owner | Reviews queue health, handles escalated tickets, coaches agents, approves KB articles |
| **Supervisor** | Operational controller | Monitors real-time dashboard, intervenes on SLA-at-risk tickets, pulls reports, manages queues |
| **Workforce Manager** | Capacity and scheduling owner | Builds agent schedules, runs forecasts, tracks adherence, manages time-off requests |
| **Knowledge Manager** | KB content owner | Authors, reviews, publishes, and retires KB articles; monitors search gap reports |
| **Bot / IVR** | Automated first-contact handler | Handles initial customer contact, resolves routine intents, escalates to agents with context |
| **System Administrator** | Platform configuration owner | Manages tenants, RBAC roles, SLA policies, custom fields, integrations, audit log access |

---

## Architecture Overview

The platform is built as a **microservices mesh** deployed on Kubernetes, fronted by an API Gateway, and backed by a combination of relational (PostgreSQL), document (Elasticsearch), and event-streaming (Kafka) stores.

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Gateway / BFF                         │
└──────┬──────────┬──────────┬──────────┬──────────┬──────────────┘
       │          │          │          │          │
 ┌─────▼──┐ ┌────▼───┐ ┌────▼───┐ ┌────▼───┐ ┌────▼──────┐
 │Ticket  │ │Channel │ │Routing │ │  SLA   │ │  Bot /    │
 │Service │ │Adapter │ │Engine  │ │Service │ │  IVR Svc  │
 └────────┘ └────────┘ └────────┘ └────────┘ └───────────┘
 ┌─────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌───────────┐
 │Knowledge│ │Customer│ │Notify  │ │Report  │ │Workforce  │
 │Base Svc │ │Profile │ │Service │ │Service │ │Mgmt Svc   │
 └─────────┘ └────────┘ └────────┘ └────────┘ └───────────┘
                    │              │
            ┌───────▼──────┐  ┌───▼──────────┐
            │  Kafka (Event│  │ PostgreSQL +  │
            │   Streaming) │  │ Elasticsearch │
            └──────────────┘  └──────────────┘
```

All inter-service communication uses **async events over Kafka** for write operations and **gRPC** for synchronous queries. Each service owns its own database schema (Database-per-Service pattern).

---

## Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **API Gateway** | Kong / AWS API Gateway | Rate limiting, auth, routing, observability |
| **Backend Services** | Node.js (TypeScript) / Go | Business logic microservices |
| **Real-Time Messaging** | WebSocket (Socket.IO) | Live chat, supervisor dashboard updates |
| **Event Streaming** | Apache Kafka | Async inter-service events, audit log, SLA clock |
| **Primary Database** | PostgreSQL 15 | Tickets, agents, SLA policies, schedules |
| **Search & Analytics** | Elasticsearch 8 | KB search, full-text ticket search, transcripts |
| **Cache** | Redis 7 | Session state, routing state, rate limits |
| **Object Storage** | AWS S3 / GCS | Attachments, recordings, transcripts |
| **NLP / AI** | AWS Lex / Dialogflow / OpenAI API | Bot intent recognition, KB semantic search |
| **Telephony** | Twilio / Amazon Connect | Voice, SMS, WhatsApp channel adapter |
| **Container Orchestration** | Kubernetes (EKS/GKE) | Service deployment, scaling, health management |
| **Service Mesh** | Istio | mTLS, circuit breakers, traffic policies |
| **Observability** | Prometheus + Grafana + Jaeger | Metrics, tracing, alerting |
| **CI/CD** | GitHub Actions + ArgoCD | Build, test, deploy pipelines |
| **Secrets Management** | HashiCorp Vault / AWS Secrets Manager | Credentials, API keys, certificates |

---

## Documentation Structure

### Phase 1 — Requirements

| File | Description |
|---|---|
| [`requirements/requirements.md`](./requirements/requirements.md) | Functional requirements (FR-001–FR-060+), NFRs, MVP/Phase 2/Phase 3 scope table, acceptance criteria, system constraints |
| [`requirements/user-stories.md`](./requirements/user-stories.md) | 40+ user stories grouped by epic with acceptance criteria and story points |

### Phase 2 — Analysis

| File | Description |
|---|---|
| [`analysis/system-context-diagram.md`](./analysis/system-context-diagram.md) | C4 Level 1 — platform boundary, external actors, and system integrations |
| [`analysis/use-case-diagram.md`](./analysis/use-case-diagram.md) | UML use-case diagram for all actors and primary use cases |
| [`analysis/use-case-descriptions.md`](./analysis/use-case-descriptions.md) | Structured use-case descriptions with pre/post conditions and alternate flows |
| [`analysis/activity-diagrams.md`](./analysis/activity-diagrams.md) | Activity diagrams for ticket lifecycle, bot handoff, SLA escalation, and scheduling |
| [`analysis/swimlane-diagrams.md`](./analysis/swimlane-diagrams.md) | Cross-actor swimlane flows for omnichannel intake, routing, and escalation |
| [`analysis/business-rules.md`](./analysis/business-rules.md) | Catalogued business rules governing SLA, routing, KB publishing, and data retention |
| [`analysis/data-dictionary.md`](./analysis/data-dictionary.md) | Field-level data dictionary for all core entities |
| [`analysis/event-catalog.md`](./analysis/event-catalog.md) | Domain event catalog with payload schemas and publishing contracts |

### Phase 3 — High-Level Design

| File | Description |
|---|---|
| [`high-level-design/architecture-diagram.md`](./high-level-design/architecture-diagram.md) | Annotated system architecture diagram with service boundaries and data flows |
| [`high-level-design/c4-diagrams.md`](./high-level-design/c4-diagrams.md) | C4 Level 1 and Level 2 diagrams (System Context and Container) |
| [`high-level-design/domain-model.md`](./high-level-design/domain-model.md) | Core domain model with bounded contexts and aggregate roots |
| [`high-level-design/data-flow-diagrams.md`](./high-level-design/data-flow-diagrams.md) | DFDs for ticket ingestion, routing decisions, SLA evaluation, and reporting pipeline |
| [`high-level-design/system-sequence-diagrams.md`](./high-level-design/system-sequence-diagrams.md) | System-level sequence diagrams for critical happy-path and failure scenarios |

### Phase 4 — Detailed Design

| File | Description |
|---|---|
| [`detailed-design/erd-database-schema.md`](./detailed-design/erd-database-schema.md) | Full ERD with all tables, columns, indexes, foreign keys, and partition strategies |
| [`detailed-design/api-design.md`](./detailed-design/api-design.md) | REST API specification (OpenAPI 3.0) for all service endpoints |
| [`detailed-design/class-diagrams.md`](./detailed-design/class-diagrams.md) | UML class diagrams for domain objects, services, and repositories |
| [`detailed-design/sequence-diagrams.md`](./detailed-design/sequence-diagrams.md) | Component-level sequence diagrams for ticket creation, routing, SLA check, bot handoff |
| [`detailed-design/state-machine-diagrams.md`](./detailed-design/state-machine-diagrams.md) | State machine diagrams for Ticket, SLA Clock, Bot Session, and Agent Status |
| [`detailed-design/component-diagrams.md`](./detailed-design/component-diagrams.md) | Internal component diagrams for Routing Engine, SLA Service, and KB Service |
| [`detailed-design/c4-component-diagram.md`](./detailed-design/c4-component-diagram.md) | C4 Level 3 component diagrams for the Ticket Service and Routing Engine |
| [`detailed-design/routing-and-workforce-management.md`](./detailed-design/routing-and-workforce-management.md) | Deep-dive design of the routing engine and workforce scheduling subsystem |

### Phase 5 — Infrastructure

| File | Description |
|---|---|
| [`infrastructure/cloud-architecture.md`](./infrastructure/cloud-architecture.md) | Cloud resource topology, multi-AZ layout, managed service choices, and cost model |
| [`infrastructure/deployment-diagram.md`](./infrastructure/deployment-diagram.md) | Kubernetes deployment diagram with namespaces, services, ingress, and HPA config |
| [`infrastructure/network-infrastructure.md`](./infrastructure/network-infrastructure.md) | VPC design, subnet segmentation, firewall rules, WAF, DDoS protection, and VPN |

### Phase 6 — Implementation

| File | Description |
|---|---|
| [`implementation/implementation-guidelines.md`](./implementation/implementation-guidelines.md) | Coding standards, service scaffolding, branching strategy, and release checklist |
| [`implementation/backend-status-matrix.md`](./implementation/backend-status-matrix.md) | Feature-by-feature backend implementation status matrix |
| [`implementation/c4-code-diagram.md`](./implementation/c4-code-diagram.md) | C4 Level 4 code diagrams for critical modules |

### Phase 7 — Edge Cases

| File | Description |
|---|---|
| [`edge-cases/README.md`](./edge-cases/README.md) | Index and categorization of all documented edge cases |
| [`edge-cases/sla-escalation.md`](./edge-cases/sla-escalation.md) | Edge cases for SLA clock pausing, timezone changes, policy version switches mid-ticket |
| [`edge-cases/bot-human-handoff.md`](./edge-cases/bot-human-handoff.md) | Edge cases for bot session timeout, agent unavailability at handoff, context loss recovery |
| [`edge-cases/thread-deduplication.md`](./edge-cases/thread-deduplication.md) | Edge cases for duplicate email detection, reply-all storms, and loop prevention |
| [`edge-cases/retention-redaction.md`](./edge-cases/retention-redaction.md) | Edge cases for GDPR erasure during open ticket, partial redaction, and audit preservation |
| [`edge-cases/security-and-compliance.md`](./edge-cases/security-and-compliance.md) | Edge cases for privilege escalation attempts, data export abuse, and consent withdrawal |
| [`edge-cases/api-and-ui.md`](./edge-cases/api-and-ui.md) | Edge cases for concurrent ticket updates, optimistic lock conflicts, and session expiry |
| [`edge-cases/operations.md`](./edge-cases/operations.md) | Edge cases for Kafka consumer lag, DB failover during high load, and replay safety |

---

## Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| **Service communication** | Kafka for writes, gRPC for queries | Decouples services for independent scaling; gRPC provides typed, low-latency reads |
| **Ticket storage** | PostgreSQL with JSONB custom fields | Relational integrity for core fields; JSONB flexibility for tenant-defined custom attributes |
| **SLA clock** | Event-sourced via Kafka with Redis TTL trigger | Enables accurate replay, business-hours-aware pause/resume, and sub-second alerting |
| **Routing state** | In-memory Redis sorted sets with PostgreSQL persistence | Low-latency routing decisions with durable fallback on restart |
| **Search** | Elasticsearch semantic index | Handles full-text, fuzzy, and ML-vector KB search at scale |
| **Multi-tenancy** | Row-level tenant isolation in PostgreSQL | Simpler operational model than schema-per-tenant while maintaining strict data separation |
| **Idempotency** | All mutating APIs require `Idempotency-Key` header | Safe retries from clients and event consumers without double-processing |
| **Audit log** | Append-only Kafka topic with S3 archival | Immutable, tamper-evident, cheap long-term storage; no DELETE permissions on topic |

---

## Getting Started

Follow these steps to onboard to the documentation and begin development planning:

1. **Understand the domain** — Read [`requirements/requirements.md`](./requirements/requirements.md) in full. Pay particular attention to the FR modules (Ticket Management, Routing, SLA, Bot) and the MVP scope table to confirm what is in scope for the first release.

2. **Review user stories** — Read [`requirements/user-stories.md`](./requirements/user-stories.md) to understand the platform from each actor's perspective. Stories include acceptance criteria that feed directly into QA test plans.

3. **Trace the architecture** — Read [`high-level-design/architecture-diagram.md`](./high-level-design/architecture-diagram.md) and the C4 diagrams to understand service boundaries. Then review [`high-level-design/domain-model.md`](./high-level-design/domain-model.md) for the bounded-context breakdown.

4. **Study detailed design** — Read [`detailed-design/erd-database-schema.md`](./detailed-design/erd-database-schema.md) and [`detailed-design/api-design.md`](./detailed-design/api-design.md) for schema and contract details. Use [`detailed-design/routing-and-workforce-management.md`](./detailed-design/routing-and-workforce-management.md) for the most complex subsystem deep-dive.

5. **Check infrastructure** — Review [`infrastructure/cloud-architecture.md`](./infrastructure/cloud-architecture.md) and [`infrastructure/deployment-diagram.md`](./infrastructure/deployment-diagram.md) to understand the target deployment environment before provisioning any resources.

6. **Pre-empt edge cases** — Read every file in [`edge-cases/`](./edge-cases/) before writing the first line of implementation code. Each file contains specific detection, mitigation, and recovery logic that must be baked into the initial delivery.

7. **Track implementation progress** — Use [`implementation/backend-status-matrix.md`](./implementation/backend-status-matrix.md) to coordinate team effort, mark features complete, and surface blockers during sprint reviews.

---

## Documentation Status

| Phase | File | Status |
|---|---|---|
| Requirements | `requirements/requirements.md` | ✅ Complete |
| Requirements | `requirements/user-stories.md` | ✅ Complete |
| Analysis | `analysis/system-context-diagram.md` | ✅ Complete |
| Analysis | `analysis/use-case-diagram.md` | ✅ Complete |
| Analysis | `analysis/use-case-descriptions.md` | ✅ Complete |
| Analysis | `analysis/activity-diagrams.md` | ✅ Complete |
| Analysis | `analysis/swimlane-diagrams.md` | ✅ Complete |
| Analysis | `analysis/business-rules.md` | ✅ Complete |
| Analysis | `analysis/data-dictionary.md` | ✅ Complete |
| Analysis | `analysis/event-catalog.md` | ✅ Complete |
| High-Level Design | `high-level-design/architecture-diagram.md` | ✅ Complete |
| High-Level Design | `high-level-design/c4-diagrams.md` | ✅ Complete |
| High-Level Design | `high-level-design/domain-model.md` | ✅ Complete |
| High-Level Design | `high-level-design/data-flow-diagrams.md` | ✅ Complete |
| High-Level Design | `high-level-design/system-sequence-diagrams.md` | ✅ Complete |
| Detailed Design | `detailed-design/erd-database-schema.md` | ✅ Complete |
| Detailed Design | `detailed-design/api-design.md` | ✅ Complete |
| Detailed Design | `detailed-design/class-diagrams.md` | ✅ Complete |
| Detailed Design | `detailed-design/sequence-diagrams.md` | ✅ Complete |
| Detailed Design | `detailed-design/state-machine-diagrams.md` | ✅ Complete |
| Detailed Design | `detailed-design/component-diagrams.md` | ✅ Complete |
| Detailed Design | `detailed-design/c4-component-diagram.md` | ✅ Complete |
| Detailed Design | `detailed-design/routing-and-workforce-management.md` | ✅ Complete |
| Infrastructure | `infrastructure/cloud-architecture.md` | ✅ Complete |
| Infrastructure | `infrastructure/deployment-diagram.md` | ✅ Complete |
| Infrastructure | `infrastructure/network-infrastructure.md` | ✅ Complete |
| Implementation | `implementation/implementation-guidelines.md` | ✅ Complete |
| Implementation | `implementation/backend-status-matrix.md` | ✅ Complete |
| Implementation | `implementation/c4-code-diagram.md` | ✅ Complete |
| Edge Cases | `edge-cases/README.md` | ✅ Complete |
| Edge Cases | `edge-cases/sla-escalation.md` | ✅ Complete |
| Edge Cases | `edge-cases/bot-human-handoff.md` | ✅ Complete |
| Edge Cases | `edge-cases/thread-deduplication.md` | ✅ Complete |
| Edge Cases | `edge-cases/retention-redaction.md` | ✅ Complete |
| Edge Cases | `edge-cases/security-and-compliance.md` | ✅ Complete |
| Edge Cases | `edge-cases/api-and-ui.md` | ✅ Complete |
| Edge Cases | `edge-cases/operations.md` | ✅ Complete |

---

> **Diagram tooling:** All diagrams are authored in [Mermaid](https://mermaid.js.org/). Render them using the VS Code Mermaid Preview extension, [mermaid.live](https://mermaid.live), or the Mermaid CLI (`mmdc`). Export targets are SVG for documentation sites and PNG for presentations.
