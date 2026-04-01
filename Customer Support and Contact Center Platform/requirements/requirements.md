# Requirements — Customer Support and Contact Center Platform

## Executive Summary

The Customer Support and Contact Center Platform is a cloud-native, multi-tenant SaaS product that consolidates every customer interaction — regardless of channel — into a unified workspace for support agents, supervisors, and workforce managers. It replaces fragmented point solutions (separate email helpdesk, standalone chat, siloed phone system) with a single platform that enforces consistent SLAs, routes intelligently using agent skill graphs, automates routine contacts via NLP-powered bots, and surfaces actionable analytics for continuous service improvement. The platform is designed to comply with GDPR, CCPA, and HIPAA data-handling requirements and to scale horizontally to hundreds of concurrent agents and millions of tickets per month.

---

## Table of Contents

1. [Scope and Goals](#1-scope-and-goals)
2. [Functional Requirements](#2-functional-requirements)
   - 2.1 [Ticket & Case Management](#21-ticket--case-management)
   - 2.2 [Channel Integration](#22-channel-integration)
   - 2.3 [Routing & Assignment](#23-routing--assignment)
   - 2.4 [SLA Management](#24-sla-management)
   - 2.5 [Agent & Team Management](#25-agent--team-management)
   - 2.6 [Knowledge Base](#26-knowledge-base)
   - 2.7 [Bot & Automation](#27-bot--automation)
   - 2.8 [Customer Profile](#28-customer-profile)
   - 2.9 [Reporting & Analytics](#29-reporting--analytics)
   - 2.10 [Administration](#210-administration)
3. [Non-Functional Requirements](#3-non-functional-requirements)
4. [Release Scope](#4-release-scope)
5. [System Constraints](#5-system-constraints)
6. [Acceptance Criteria for Critical FRs](#6-acceptance-criteria-for-critical-frs)

---

## 1. Scope and Goals

### In Scope
- Omni-channel ticket and case management (email, live chat, voice, social, SMS, WhatsApp)
- Intelligent routing engine with skill-based, availability, round-robin, and load-balancing modes
- SLA policy engine with real-time tracking, warnings, and auto-escalation
- AI/NLP chatbot with IVR integration and seamless human handoff
- Agent-facing knowledge base with AI semantic search and inline article suggestions
- Customer 360° profile with conversation history, CSAT/NPS records, and CRM data
- Workforce management: scheduling, adherence, forecasting
- Supervisor real-time dashboard with intervention controls
- Call recording, transcription, and PII redaction
- CSAT and NPS survey engine with attribution to agent and ticket
- Reporting and analytics with custom report builder
- Administration: tenants, RBAC, custom fields, SLA policy management, audit logs
- GDPR/CCPA/HIPAA compliance controls: retention, erasure, consent, audit export

### Out of Scope (current version)
- Full CRM functionality (contacts are read from CRM integration, not owned by this platform)
- Billing and subscription management
- Native mobile SDK for customer-facing apps (REST API is available for mobile integration)
- Video call support

### Goals
| Goal | Success Metric |
|---|---|
| Reduce first-response time | Median FRT < 4 hours for email; < 2 minutes for chat |
| Improve SLA compliance | SLA breach rate < 5% across all tiers |
| Increase agent productivity | Average handle time reduced by 20% within 6 months |
| Achieve bot containment | Bot self-service containment rate ≥ 40% of chat volume |
| Ensure compliance | Zero regulatory findings on GDPR/CCPA audit |
| Improve CSAT | CSAT score ≥ 4.2 / 5.0 within 3 months of go-live |

---

## 2. Functional Requirements

### 2.1 Ticket & Case Management

**FR-001 — Create Ticket**
The system shall allow tickets to be created from any configured channel (email, chat, voice, social, SMS, WhatsApp) and via manual creation by agents. Each ticket shall have a unique, immutable ticket ID, a subject, a body, a status, a priority, a source channel, a creation timestamp, and references to the associated customer and queue.

**FR-002 — Update Ticket**
Agents and supervisors shall be able to update ticket fields including subject, priority, status, assigned agent, assigned queue, tags, and custom fields. Each update shall be recorded as an immutable audit event with actor ID, timestamp, old value, and new value.

**FR-003 — Assign and Reassign Tickets**
Agents with appropriate permissions shall be able to manually assign a ticket to themselves or another agent. Supervisors and the routing engine shall be able to reassign tickets. All assignment changes shall trigger a notification to the newly assigned agent.

**FR-004 — Merge Tickets**
An agent or supervisor shall be able to merge two or more tickets from the same customer about the same issue into a primary ticket. The merged tickets' conversation threads, attachments, and timeline events shall be consolidated under the primary ticket. Merged tickets shall be marked as `merged` and linked to the primary ticket ID.

**FR-005 — Split Ticket**
An agent or supervisor shall be able to split a multi-issue ticket into two or more separate tickets, each retaining a copy of the original subject, customer reference, and relevant conversation context.

**FR-006 — Conversation Threading**
All responses (inbound from customer, outbound from agent, system notes) shall be organized as an ordered thread under the ticket. Inbound replies matching the ticket's conversation reference ID (email Message-ID chain, chat session ID, etc.) shall be automatically appended to the correct thread without creating a new ticket.

**FR-007 — Attachment Handling**
Customers and agents shall be able to attach files (images, documents, audio, video) to tickets and replies. Attachments shall be scanned for malware before storage. Maximum individual file size: 25 MB. Maximum total attachments per ticket: 250 MB. Supported MIME types shall be configurable by tenant administrators.

**FR-008 — Bulk Operations**
Supervisors and agents with bulk-action permission shall be able to select multiple tickets and apply the following operations in a single action: assign to agent, move to queue, change status, add/remove tag, close, and export to CSV.

---

### 2.2 Channel Integration

**FR-009 — Email Ingestion**
The system shall ingest emails from one or more configured support mailboxes via IMAP/POP3 polling or SMTP forwarding. Inbound emails shall be parsed into tickets, with `From`, `Subject`, `Body`, `CC`, and attachments mapped to ticket fields. Reply threading shall use `In-Reply-To` and `References` headers.

**FR-010 — Live Chat Widget**
The system shall provide an embeddable JavaScript chat widget for customer-facing websites. The widget shall support: pre-chat form (name, email, topic), real-time message exchange with typing indicators, file attachment up to 10 MB, automatic session timeout after configurable idle period, and post-chat CSAT prompt.

**FR-011 — Voice / Telephony Channel**
The system shall integrate with a telephony provider (Twilio or Amazon Connect) to handle inbound and outbound voice calls. Each call shall create or associate with a ticket. Call metadata (caller ID, duration, hold time, disposition) shall be stored on the ticket. Call recordings shall be captured and linked to the ticket timeline.

**FR-012 — Social Media Channel**
The system shall ingest mentions, direct messages, and comments from configured Twitter/X, Facebook Page, and Instagram Business accounts via their respective APIs. Social messages shall be normalized into the ticket model with source-channel metadata preserved.

**FR-013 — SMS and WhatsApp Channel**
The system shall support two-way SMS and WhatsApp messaging via a configured gateway (Twilio, MessageBird). Inbound messages shall create or append to existing tickets correlated by the sender's phone number. Outbound messages sent by agents shall be delivered through the same gateway.

**FR-014 — Channel Normalization**
Regardless of source channel, all tickets shall conform to a canonical ticket schema. Channel-specific metadata (email headers, social post IDs, call SIDs, message IDs) shall be stored in a typed extension field per channel. Cross-channel linking shall be possible when the same customer contacts via multiple channels about the same issue.

**FR-015 — Attachment Handling Across Channels**
The system shall accept file attachments from all channels that support them (email, chat, WhatsApp) and store them in a unified attachment store. Attachment virus scanning, size enforcement, and MIME-type filtering shall apply uniformly regardless of source channel.

---

### 2.3 Routing & Assignment

**FR-016 — Skill-Based Routing**
The system shall route incoming tickets to agents whose skill profiles satisfy the ticket's required skills. Skills are configured per agent (e.g., `language:Spanish`, `tier:2`, `product:BillingModule`). Required skills on a ticket are derived from the channel, topic classification, and configurable mapping rules. If no agent with all required skills is available, the ticket shall enter a queue and wait.

**FR-017 — Availability-Based Routing**
Before assigning a ticket, the routing engine shall check each candidate agent's real-time status (Online, Busy, Away, Offline) and current open-ticket count against their configured concurrency limit. Agents at capacity or not Online shall not receive new automatic assignments.

**FR-018 — Round-Robin Routing**
When a queue is configured in round-robin mode, tickets shall be assigned to eligible agents in rotation, skipping agents who are at capacity or unavailable. The rotation pointer shall be persisted to survive service restarts.

**FR-019 — Load-Balancing Routing**
When a queue is configured in load-balancing mode, tickets shall be assigned to the eligible agent with the lowest current open-ticket count. Ties are broken by longest idle time since last ticket assignment.

**FR-020 — Queue Management**
Administrators shall be able to create, configure, and deactivate queues. Each queue shall have: a name, a routing mode (skill-based, round-robin, load-balancing), a set of required skills, a priority level (1–5), business hours, an SLA policy, and overflow configuration (target queue or escalation group).

**FR-021 — Overflow Routing**
When a queue's wait time or depth exceeds its configured overflow threshold, the system shall automatically route incoming tickets to a designated overflow queue or escalation group. Overflow events shall be logged and visible on the supervisor dashboard.

**FR-022 — Auto-Assignment Rules**
Administrators shall be able to define rule sets that automatically set ticket priority, assign required skills, select a target queue, and apply tags based on ticket attributes (channel, subject keywords, customer tier, time of day). Rules shall be evaluated in priority order; the first matching rule wins.

---

### 2.4 SLA Management

**FR-023 — SLA Policy Creation**
Administrators shall be able to create named SLA policies with the following configurable targets: first-response time, next-response time, and resolution time. Targets shall be specifiable in minutes, hours, or business hours. Policies shall be associable with queues, customer tiers, channels, or ticket priority levels.

**FR-024 — First-Response SLA Clock**
Upon ticket creation, the system shall start the first-response SLA clock. The clock shall stop when the first agent response (outbound message or status change to `In Progress`) is recorded. If no response is recorded before the first-response target elapses, the ticket shall be marked as SLA breached and an escalation event shall fire.

**FR-025 — Resolution SLA Clock**
The resolution SLA clock shall start at ticket creation and stop when the ticket status transitions to `Resolved` or `Closed`. The clock shall pause when the ticket is in `Pending Customer` status and resume when the customer replies or an agent manually resumes it.

**FR-026 — SLA Warning Alerts**
The system shall generate a warning alert when a ticket's SLA clock reaches a configurable threshold (default: 75% of target elapsed). Warnings shall be delivered to the assigned agent via in-app notification and to the queue supervisor via the real-time dashboard. Warning thresholds shall be configurable per SLA policy.

**FR-027 — Auto-Escalation on Breach**
When an SLA clock reaches 100% of target without the required action, the system shall automatically: increment an escalation counter on the ticket, notify the assigned agent and their team lead, optionally reassign the ticket to an escalation queue or supervisor, and append a system note to the ticket thread with escalation reason and timestamp.

**FR-028 — SLA Pause and Resume**
Agents and automation rules shall be able to pause the SLA clock for legitimate reasons: awaiting customer response (`Pending Customer`), awaiting third-party action (`Pending Vendor`), or business-hours-only policies outside of business hours. Each pause shall record the reason, actor, start timestamp, and end timestamp. Resumed clock time shall exclude all pause intervals.

---

### 2.5 Agent & Team Management

**FR-029 — Agent Profile**
Each agent shall have a profile containing: full name, email, phone, avatar, role(s), team membership(s), language proficiencies, skill set with proficiency levels (1–5), timezone, shift schedule, and capacity (maximum concurrent tickets). Profiles shall be manageable by system administrators and team leads.

**FR-030 — Skill Management**
Administrators shall be able to create, update, and deactivate skills in a skill catalog. Skills shall be categorized (e.g., Language, Product, Technical Tier). Agents shall be assigned skills with proficiency levels. Skill assignments shall take effect immediately for new routing decisions.

**FR-031 — Shift Scheduling**
Workforce managers shall be able to create weekly schedule templates per agent or team, specifying shift start time, shift end time, break windows, and days of week. Agents shall be able to view their schedules and submit time-off requests. Workforce managers shall be able to approve or reject time-off requests.

**FR-032 — Agent Status Management**
Agents shall be able to set their real-time status: Online, Busy, Away (with reason), or Offline. Supervisors shall be able to override an agent's status. The system shall automatically set an agent to Away after a configurable idle period and to Offline at the end of their scheduled shift if they have not manually set their status.

**FR-033 — Team Hierarchy**
The system shall support an organizational hierarchy of teams with a team lead. Agents belong to one or more teams. Teams can be nested (sub-teams). Routing and reporting shall be filterable by team.

**FR-034 — Supervisor Controls**
Supervisors shall be able to: view all agents' real-time status and current ticket assignments, forcibly reassign any ticket, put any queue on hold or in overflow mode, see real-time SLA risk indicators, and access a live wall board showing queue depth, wait time, and agent availability.

**FR-035 — Agent Performance Metrics**
The system shall compute and store per-agent performance metrics at daily and weekly granularity: tickets handled, average first-response time, average handle time, tickets resolved, SLA compliance rate, and CSAT score. These metrics shall be visible on agent scorecards and exportable by supervisors and workforce managers.

---

### 2.6 Knowledge Base

**FR-036 — Article Creation and Publishing**
Knowledge managers and authorized agents shall be able to create KB articles with a title, category path, rich-text body (supporting headings, lists, code blocks, images, embedded video), tags, and visibility (internal-only or customer-facing). Articles shall go through a draft → review → published workflow before appearing to agents or customers.

**FR-037 — Article Versioning**
Every published change to a KB article shall create a new version. Version history shall be accessible to authors and knowledge managers. Any previous version shall be restorable as the current version. The current and previous version shall be diffable side by side.

**FR-038 — AI-Powered Search**
The KB search engine shall combine keyword (BM25) and semantic (vector embedding) retrieval to return ranked results. Customer-facing search shall search only published, customer-visible articles. Agent-facing search shall additionally include internal-only articles. Search results shall include article title, category, an excerpt highlighting the matched passage, and a relevance score.

**FR-039 — Agent Article Suggestion**
As an agent composes a reply in the ticket editor, the system shall perform a real-time background search against the KB using the ticket's subject and the content being typed, and surface the top-3 most relevant articles in a suggestion panel. The agent can insert an article link or copy a passage directly into the reply.

**FR-040 — Article Feedback**
Customers shall be able to rate each KB article (Helpful / Not Helpful) and submit an optional comment. Agents shall be able to flag an article for review. Low-rated articles (< 60% helpful over the last 30 days) shall appear on a knowledge manager review queue. Search queries that return zero results shall be logged for gap analysis.

---

### 2.7 Bot & Automation

**FR-041 — Bot Flow Creation**
Administrators and knowledge managers shall be able to create and edit conversational bot flows using a visual flow editor. Flows shall support: intent triggers, conditional branches, slot collection forms, API call actions, KB article lookup actions, and terminal actions (resolve, escalate to agent).

**FR-042 — NLP Intent Recognition**
The bot engine shall integrate with a configurable NLP provider (AWS Lex, Dialogflow, or OpenAI) to classify customer intents from free-text input. The system shall support multi-turn dialogues with entity/slot memory. Intent recognition confidence shall be logged with each interaction for tuning purposes.

**FR-043 — Human Handoff**
When bot intent confidence falls below a configurable threshold, the customer explicitly requests a human agent, or the bot exhausts its retry limit, the system shall perform a graceful human handoff: notify the agent of the incoming transfer, pass the full bot conversation transcript and extracted slots as ticket context, and maintain channel continuity (the customer stays in the same chat or call session).

**FR-044 — Automation Rules**
Administrators shall be able to create event-triggered automation rules that fire when specific ticket conditions are met (e.g., "ticket created AND channel = email AND subject contains 'invoice' → set tag billing, set priority High, assign to billing queue"). Rules shall support conditions with AND/OR logic and multiple consequent actions.

**FR-045 — Canned Responses**
Agents shall be able to save and use canned response templates for common replies. Templates shall support dynamic variables (e.g., `{{customer.firstName}}`, `{{ticket.id}}`). Templates shall be organized by category and searchable. Supervisors shall be able to manage the shared canned response library.

**FR-046 — Auto-Tagging**
The system shall use keyword and ML classifiers to automatically suggest tags on new tickets based on subject and body content. Auto-tags shall be applied as `suggested` status; agents can accept or reject them. Confirmed auto-tags shall be used as training feedback to improve classifier accuracy over time.

---

### 2.8 Customer Profile

**FR-047 — 360° Customer View**
The agent workspace shall display a 360° customer panel showing: contact details (name, email, phone, company), CRM-linked data (account value, products owned, open opportunities), full ticket history (all channels), all bot session summaries, all CSAT/NPS responses, and notes added by agents or supervisors.

**FR-048 — Contact Deduplication and Merge**
The system shall detect potential duplicate customer records based on matching email, phone, or name. Administrators and supervisors shall be able to review and confirm merges. Upon merge, all tickets, conversations, and survey responses from the merged records shall be consolidated under the surviving record, and the merged record shall be marked inactive.

**FR-049 — Conversation History**
Agents shall be able to view the complete, chronological conversation history for a customer across all channels and tickets, including closed and resolved tickets. Each history entry shall show: date, channel icon, ticket ID, subject, handling agent, and resolution status.

**FR-050 — CSAT Surveys**
Upon ticket closure, the system shall automatically send a CSAT survey to the customer via the ticket's source channel (email or in-chat prompt). The survey shall present a 1–5 rating and an optional free-text comment field. Survey sending shall be configurable: delay (0–24 hours after close), exclusion rules (e.g., do not survey customers more than once per 7 days), and minimum ticket age (do not survey tickets closed within 5 minutes).

**FR-051 — NPS Surveys**
The system shall deliver Net Promoter Score surveys to customers on a configurable recurring schedule (e.g., every 90 days per customer). NPS surveys shall be delivered via email. Responses (0–10 score + optional comment) shall be stored and attributed to the customer record. NPS detractor responses shall optionally trigger a follow-up ticket creation for recovery outreach.

---

### 2.9 Reporting & Analytics

**FR-052 — Real-Time Operational Dashboard**
The system shall provide a real-time dashboard refreshing at ≤ 5-second intervals, showing: total open tickets, tickets per queue, tickets per agent, average queue wait time, SLA compliance rate, CSAT average (rolling 7-day), agent availability breakdown (Online/Busy/Away/Offline counts), and active bot sessions.

**FR-053 — Historical Reports**
The system shall provide pre-built historical reports with configurable date ranges, filterable by agent, team, queue, channel, priority, topic, and customer tier. Standard reports shall include: Ticket Volume by Period, First Response Time Distribution, Resolution Time Distribution, Ticket Reopened Rate, and Channel Volume Share.

**FR-054 — SLA Compliance Reports**
The system shall generate SLA compliance reports showing: total tickets subject to SLA, tickets resolved within SLA, breach rate per queue, breach rate per agent, top breached SLA policies, and trend over selected date range. Reports shall be exportable as CSV and PDF.

**FR-055 — Agent Performance Reports**
The system shall generate individual and comparative agent performance reports including: tickets handled, average handle time, average first-response time, SLA compliance rate, CSAT score, NPS attribution, and KB article usage rate. Reports shall support peer comparison (anonymized or named, configurable by supervisor role).

**FR-056 — Custom Report Builder**
The system shall provide a drag-and-drop custom report builder allowing authorized users to: select metrics from a catalog, add dimension filters, choose visualization type (table, bar chart, line chart, pie chart), set a date range, schedule automated delivery (email PDF/CSV), and save report configurations.

---

### 2.10 Administration

**FR-057 — Organization Settings**
System administrators shall be able to configure: organization name, logo, support email addresses, business hours (per timezone, per day-of-week), holiday calendar, default language, and tenant-level data retention policies.

**FR-058 — Custom Fields**
Administrators shall be able to add custom fields to the Ticket, Customer, and Agent entities. Custom field types shall include: text (single-line, multi-line), number, dropdown (single/multi-select), date, checkbox, and URL. Custom fields shall be available as columns in reports and filters in routing rules.

**FR-059 — Role-Based Access Control (RBAC)**
The system shall enforce RBAC with at minimum the following built-in roles: Customer (self-service portal only), Support Agent, Senior Agent, Team Lead, Supervisor, Workforce Manager, Knowledge Manager, System Administrator, and Read-Only Auditor. Each role shall have a defined permission set. Custom roles with configurable permissions shall be supported.

**FR-060 — Audit Logs**
The system shall maintain an immutable audit log capturing: actor ID, actor role, action type, resource type, resource ID, timestamp (UTC), IP address, and change delta (old/new values for mutations). Audit logs shall be queryable by administrators and read-only auditors, exportable as CSV/JSON, and retained for a minimum of 7 years.

---

## 3. Non-Functional Requirements

### 3.1 Availability & Reliability

| Requirement | Target |
|---|---|
| Tier-1 API availability (ticket CRUD, agent workspace) | 99.9% monthly uptime |
| Real-time dashboard availability | 99.5% monthly uptime |
| Planned maintenance window | ≤ 4 hours/month, notified 72 hours in advance |
| RTO (Recovery Time Objective) | ≤ 30 minutes for Tier-1 services |
| RPO (Recovery Point Objective) | ≤ 5 minutes (WAL streaming replication) |
| Kafka consumer lag threshold before alert | > 10,000 messages or > 60 seconds behind |

### 3.2 Performance

| Requirement | Target |
|---|---|
| Ticket create API p99 latency | ≤ 300 ms under normal load |
| Routing decision latency | ≤ 500 ms from ticket creation event to assignment |
| SLA threshold event latency | ≤ 2 seconds from threshold crossing to alert generation |
| KB search p95 latency | ≤ 500 ms |
| Live chat message delivery latency | ≤ 200 ms (WebSocket, same region) |
| Dashboard refresh cycle | ≤ 5 seconds end-to-end |
| Report generation (90-day range) | ≤ 30 seconds for pre-built reports |

### 3.3 Scalability

- The platform shall support **up to 500 concurrent agents** per tenant instance without degradation.
- The ticket ingestion pipeline shall handle bursts of **10,000 inbound events per minute**.
- The system shall support **100,000 concurrent queued tickets** with deterministic FIFO ordering within each queue.
- All stateless services shall scale horizontally via Kubernetes HPA triggered on CPU and custom Kafka consumer-lag metrics.
- The Elasticsearch index shall be designed for sharding across a minimum of 3 nodes, supporting up to **500 million indexed documents** per tenant cluster.

### 3.4 Security

- All data in transit shall be encrypted using **TLS 1.2+**; TLS 1.0 and 1.1 shall be disabled.
- All data at rest shall be encrypted using **AES-256** (database storage encryption and object storage SSE).
- Authentication shall use **OAuth 2.0 / OpenID Connect** with MFA required for all privileged roles (Supervisor, Administrator).
- Passwords shall be hashed using **bcrypt** (cost factor ≥ 12) or **Argon2id**.
- API keys shall be stored as hashed values; plaintext keys shall never be persisted after initial display.
- All services shall run with least-privilege identities (Kubernetes ServiceAccounts, IAM roles with minimal permissions).
- Inbound payloads shall be validated against strict JSON schema before processing; oversized or malformed payloads shall be rejected with HTTP 400.
- The platform shall support **IP allowlisting** per tenant for API and admin console access.

### 3.5 Compliance

| Regulation | Requirement |
|---|---|
| **GDPR** | Lawful basis for processing, consent management, right-to-access export, right-to-erasure (Article 17), data portability (Article 20), breach notification < 72 hours |
| **CCPA** | Opt-out of sale of personal information, right to know, right to delete, privacy notice |
| **HIPAA** | PHI handling controls (if healthcare tenant): minimum necessary access, encryption, audit logs, BAA support |
| **PCI-DSS** | Card data never stored in the platform; transcripts and messages auto-redacted for card numbers via regex/ML pipeline |
| **SOC 2 Type II** | Controls for Security, Availability, Confidentiality, and Processing Integrity trust service criteria |

### 3.6 Data Retention

- Default ticket retention: **7 years** (configurable per tenant, subject to regulatory minimums).
- Call recordings retention: **90 days** default, configurable up to **7 years**.
- Audit logs retention: **7 years** minimum, stored in immutable append-only storage.
- Soft-delete with 30-day recycle bin before hard purge; hard purge generates a cryptographic deletion confirmation receipt.
- GDPR erasure requests shall be executed within **30 days** of verified request; partial redaction (PII removal from ticket body, transcript, and KB article) preferred over full record deletion where tickets must be preserved for litigation hold.

### 3.7 Integrations

- **CRM**: REST webhooks or native connectors for Salesforce and HubSpot; bidirectional ticket-to-case sync.
- **Telephony**: Twilio or Amazon Connect via configurable provider adapter.
- **NLP / AI**: AWS Lex, Dialogflow, or OpenAI GPT via configurable provider adapter with fallback.
- **Email**: IMAP/POP3 polling, SMTP inbound forwarding, SendGrid/Mailgun for outbound.
- **SSO**: SAML 2.0 and OIDC for enterprise identity provider integration.
- **Webhook Outbound**: Configurable webhook triggers on ticket events (created, updated, closed, SLA breached) with HMAC-SHA256 signatures.
- **Zapier**: Native Zapier app with triggers and actions for no-code workflow integration.

---

## 4. Release Scope

| Feature Area | MVP (Phase 1) | Phase 2 | Phase 3 |
|---|---|---|---|
| Email channel | ✅ | | |
| Live chat widget | ✅ | | |
| Voice / telephony (basic) | ✅ | | |
| SMS channel | ✅ | | |
| WhatsApp channel | | ✅ | |
| Social media (Twitter/Facebook) | | ✅ | |
| Skill-based routing | ✅ | | |
| Round-robin routing | ✅ | | |
| Load-balancing routing | | ✅ | |
| SLA policy engine | ✅ | | |
| SLA auto-escalation | ✅ | | |
| SLA pause/resume | | ✅ | |
| Knowledge base (basic) | ✅ | | |
| KB AI semantic search | | ✅ | |
| KB agent suggestion panel | | ✅ | |
| Bot flow builder (scripted) | ✅ | | |
| NLP intent recognition | | ✅ | |
| IVR integration | | ✅ | |
| Human handoff | ✅ | | |
| CSAT surveys | ✅ | | |
| NPS surveys | | ✅ | |
| Customer 360° profile | ✅ | | |
| Contact merge/deduplication | | ✅ | |
| Call recording + transcription | | ✅ | |
| PII redaction pipeline | | ✅ | |
| Real-time supervisor dashboard | ✅ | | |
| Workforce scheduling | | ✅ | |
| Staffing forecasts | | | ✅ |
| Custom report builder | | ✅ | |
| Pre-built SLA & performance reports | ✅ | | |
| RBAC (built-in roles) | ✅ | | |
| Custom roles | | ✅ | |
| Audit log (basic) | ✅ | | |
| Audit log export + immutable archival | | ✅ | |
| GDPR erasure workflow | | ✅ | |
| Salesforce CRM integration | | ✅ | |
| HubSpot CRM integration | | | ✅ |
| Custom field builder | | ✅ | |
| Auto-tagging (ML) | | | ✅ |
| Sentiment analysis on tickets | | | ✅ |
| Predictive CSAT scoring | | | ✅ |

---

## 5. System Constraints

- **Multi-tenancy**: The platform is multi-tenant SaaS; tenant data must be strictly isolated at the database row level and the application layer. Cross-tenant data access is prohibited and must be enforced by middleware.
- **Time zones**: All timestamps stored in UTC; displayed in the user's configured timezone. SLA business-hours calculations must correctly handle timezone rules including DST transitions.
- **Idempotency**: All write APIs must accept and honour an `Idempotency-Key` request header to safely support client retries without duplicate processing.
- **Backward compatibility**: API changes must be versioned (e.g., `/api/v1/`, `/api/v2/`). Breaking changes to existing API versions are not permitted; deprecated fields must remain functional for a minimum of 6 months after deprecation notice.
- **Resilience**: The routing engine must continue assigning tickets from its Redis state if the primary PostgreSQL database becomes temporarily unavailable. All Kafka consumers must be idempotent and support at-least-once delivery semantics.
- **Accessibility**: The agent web application must meet **WCAG 2.1 Level AA** accessibility standards.
- **Browser support**: The agent workspace must support the latest two major versions of Chrome, Firefox, Safari, and Edge.
- **Localization**: The agent UI must support at minimum English, Spanish, French, German, and Portuguese. The KB customer portal must support the same languages.

---

## 6. Acceptance Criteria for Critical FRs

### FR-001 — Create Ticket
1. Given a valid inbound email, the system creates a ticket within 10 seconds of receipt.
2. The ticket has a unique ID, the correct `From` address mapped to a customer record, the email subject as ticket subject, and status `New`.
3. A `ticket.created` domain event is published to the Kafka topic within 1 second of ticket persistence.
4. Submitting the same email twice (identical `Message-ID`) produces only one ticket (idempotency).
5. An invalid/malformed email (no `From` header) is moved to a dead-letter queue with an error code, not silently dropped.

### FR-016 — Skill-Based Routing
1. Given a ticket with required skills `[language:French, tier:2]`, the routing engine only assigns it to an agent whose skill profile includes both skills at proficiency ≥ 1.
2. Given no eligible agent is Online and available, the ticket enters the queue and is assigned within 30 seconds of an eligible agent becoming available.
3. Given an agent becomes unavailable (status → Away) after assignment, the ticket is not reassigned automatically; a supervisor alert is raised if it is SLA at-risk.
4. The routing decision and rationale are logged for every assignment attempt.

### FR-024 — First-Response SLA Clock
1. The SLA clock starts at ticket creation timestamp (UTC) accurate to the millisecond.
2. The first-response clock stops the moment the agent sends an outbound message; it does not restart on subsequent replies.
3. A warning notification is delivered to the assigned agent and supervisor when 75% of the first-response target elapses, verified by integration test.
4. On 100% elapsed without response, a `sla.first_response.breached` event fires within 2 seconds, and the ticket is marked breached in the UI within the next dashboard refresh cycle (≤ 5 s).

### FR-043 — Human Handoff
1. When bot confidence < threshold, the session is transferred to the routing engine within 500 ms; the customer does not experience a gap > 3 seconds before receiving an agent greeting.
2. The agent's workspace displays the full bot transcript and all extracted slots before they send their first message.
3. If no agent is available at handoff time, the customer receives an estimated wait time message and the bot session context is held for up to 10 minutes.
4. Handoff events are logged with: bot session ID, confidence score at handoff, extracted slots, wait time to agent assignment, and agent ID.

### FR-059 — RBAC
1. A Support Agent cannot access the Administration panel; attempting to do so returns HTTP 403.
2. A Read-Only Auditor can export audit logs but cannot modify any ticket, agent, or configuration resource; all mutating API calls return HTTP 403.
3. Role assignments take effect within 60 seconds of change without requiring the affected user to log out.
4. A custom role with only `ticket.read` and `kb.read` permissions cannot invoke any write endpoint, verified by automated permission matrix test suite.
