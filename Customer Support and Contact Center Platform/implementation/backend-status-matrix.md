# Backend Capability Status Matrix – Customer Support and Contact Center Platform

This document tracks the implementation readiness of every backend capability, API endpoint, database table, external integration, and domain event across all four delivery phases.

**Status Legend:**
- 🔴 `NOT_STARTED` – Not yet implemented
- 🟡 `IN_PROGRESS` – Under active development
- 🟢 `DONE` – Implemented, tested, deployed to staging
- ✅ `PROD_READY` – Deployed to production, SLO verified
- ⏸️ `BLOCKED` – Blocked by dependency

---

## 1. API Endpoint Status Matrix

### TicketService (Java Spring Boot)

| Endpoint | Method | Description | Phase | Status | Notes |
|---|---|---|---|---|---|
| `/v1/tickets` | POST | Create ticket with idempotency key | P1 | ✅ | Outbox pattern; dedup via X-Idempotency-Key |
| `/v1/tickets/{id}` | GET | Get ticket by ID | P1 | ✅ | Row-level security enforced |
| `/v1/tickets` | GET | List tickets (paginated, filtered) | P1 | ✅ | Cursor-based pagination |
| `/v1/tickets/{id}` | PATCH | Update ticket fields (subject, priority, tags) | P1 | ✅ | Optimistic locking via `version` field |
| `/v1/tickets/{id}/status` | PUT | Transition ticket status | P1 | ✅ | State machine guard; audit event emitted |
| `/v1/tickets/{id}/assign` | POST | Assign ticket to agent | P1 | ✅ | Triggers routing confirmation |
| `/v1/tickets/{id}/unassign` | POST | Remove agent assignment | P2 | ✅ | Returns to queue |
| `/v1/tickets/{id}/threads` | GET | Get all message threads for ticket | P1 | ✅ | Includes bot transcript |
| `/v1/tickets/{id}/threads` | POST | Add message to thread | P1 | ✅ | Channel-aware outbound dispatch |
| `/v1/tickets/{id}/attachments` | POST | Upload attachment to S3 | P1 | ✅ | Pre-signed URL flow; max 25MB |
| `/v1/tickets/{id}/tags` | PUT | Replace ticket tags | P2 | ✅ | Bulk replace; tag validation |
| `/v1/tickets/{id}/custom-fields` | PATCH | Update custom field values | P4 | 🟢 | Dynamic schema; JSONB storage |
| `/v1/tickets/{id}/merge` | POST | Merge duplicate tickets | P2 | 🟢 | Supervisor-only; audit trail |
| `/v1/tickets/{id}/sla` | GET | Get current SLA clock state | P1 | ✅ | Real-time breach_at timestamp |
| `/v1/tickets/bulk` | POST | Bulk create tickets from import | P4 | 🟡 | CSV/JSON import; async job |
| `/internal/tickets/idempotency-cleanup` | POST | Purge expired idempotency keys | P1 | ✅ | Cron: daily |

### AgentService (Java Spring Boot)

| Endpoint | Method | Description | Phase | Status | Notes |
|---|---|---|---|---|---|
| `/v1/agents` | POST | Create agent | P1 | ✅ | Keycloak user provisioning |
| `/v1/agents/{id}` | GET | Get agent profile | P1 | ✅ | |
| `/v1/agents/{id}` | PATCH | Update agent profile | P1 | ✅ | |
| `/v1/agents/{id}/availability` | PUT | Set agent availability status | P1 | ✅ | Redis + PG sync |
| `/v1/agents/{id}/skills` | GET | List agent skills | P1 | ✅ | |
| `/v1/agents/{id}/skills` | PUT | Replace agent skills | P2 | ✅ | |
| `/v1/agents/{id}/workload` | GET | Current open ticket count | P2 | ✅ | From Redis |
| `/v1/teams` | POST | Create team | P1 | ✅ | |
| `/v1/teams/{id}` | GET | Get team details | P1 | ✅ | |
| `/v1/teams/{id}/agents` | GET | List agents in team | P1 | ✅ | |
| `/v1/teams/{id}/sla-policy` | PUT | Assign SLA policy to team | P1 | ✅ | |

### RoutingEngine (Go)

| Endpoint | Method | Description | Phase | Status | Notes |
|---|---|---|---|---|---|
| `/v1/routing/assign` | POST | Assign ticket to best-matching agent | P1 | ✅ | Round-robin in P1; skill-based in P2 |
| `/v1/routing/queues` | GET | List all routing queues with depths | P2 | ✅ | Supervisor dashboard feed |
| `/v1/routing/queues/{id}/rebalance` | POST | Force rebalance queue assignments | P2 | 🟢 | Supervisor manual override |
| `/v1/routing/agents/{id}/queue` | GET | Get queue position for agent | P2 | ✅ | |
| `/internal/routing/algorithm` | PUT | Switch routing algorithm at runtime | P2 | 🟢 | Feature flag + LaunchDarkly |

### SLAService (Go)

| Endpoint | Method | Description | Phase | Status | Notes |
|---|---|---|---|---|---|
| `/v1/sla/policies` | POST | Create SLA policy | P1 | ✅ | |
| `/v1/sla/policies/{id}` | GET | Get SLA policy | P1 | ✅ | |
| `/v1/sla/policies/{id}` | PUT | Update SLA policy | P1 | ✅ | Immutable history; creates new version |
| `/v1/sla/clocks/{ticketId}` | GET | Get SLA clock state for ticket | P1 | ✅ | |
| `/v1/sla/clocks/{ticketId}/pause` | POST | Pause SLA clock | P1 | ✅ | On PENDING status transition |
| `/v1/sla/clocks/{ticketId}/resume` | POST | Resume SLA clock | P1 | ✅ | On customer reply |
| `/v1/sla/clocks/{ticketId}/override` | POST | Supervisor override SLA deadline | P2 | 🟢 | Requires supervisor role + reason |
| `/internal/sla/reconcile` | POST | Reconcile clock drift post-deploy | P1 | ✅ | Post-deployment runbook step |

### KnowledgeBaseService (Python FastAPI)

| Endpoint | Method | Description | Phase | Status | Notes |
|---|---|---|---|---|---|
| `/v1/kb/articles` | POST | Create KB article | P2 | ✅ | Indexed in OpenSearch on save |
| `/v1/kb/articles/{id}` | GET | Get article by ID | P2 | ✅ | |
| `/v1/kb/articles/{id}` | PUT | Update article | P2 | ✅ | Re-index in OpenSearch |
| `/v1/kb/articles/{id}` | DELETE | Archive article (soft delete) | P2 | ✅ | |
| `/v1/kb/articles/search` | GET | Full-text + semantic search | P2/P3 | ✅ | BM25 in P2; kNN vector in P3 |
| `/v1/kb/articles/{id}/feedback` | POST | Agent feedback on article relevance | P3 | 🟢 | Feeds ML relevance tuning |
| `/v1/kb/categories` | GET | List all article categories | P2 | ✅ | |

### BotEngine (Python FastAPI)

| Endpoint | Method | Description | Phase | Status | Notes |
|---|---|---|---|---|---|
| `/v1/bot/sessions` | POST | Start bot session | P3 | 🟢 | Returns sessionId and welcome message |
| `/v1/bot/sessions/{id}/message` | POST | Send message to bot | P3 | 🟢 | NLP intent classification |
| `/v1/bot/sessions/{id}/handoff` | POST | Initiate bot-to-human handoff | P3 | 🟡 | Context serialization + routing |
| `/v1/bot/sessions/{id}` | GET | Get session state | P3 | 🟢 | |
| `/v1/bot/sessions/{id}` | DELETE | End bot session | P3 | 🟢 | |
| `/internal/bot/intent-models/reload` | POST | Hot-reload NLP model | P3 | 🟡 | Zero-downtime model swap |

### NotificationService (Node.js)

| Endpoint | Method | Description | Phase | Status | Notes |
|---|---|---|---|---|---|
| `/v1/notifications/send` | POST | Send notification (email/SMS/push) | P1 | ✅ | |
| `/v1/notifications/templates` | POST | Create notification template | P2 | ✅ | Handlebars templating |
| `/v1/notifications/templates/{id}` | GET | Get template | P2 | ✅ | |
| `/v1/notifications/preferences/{userId}` | PUT | Update user notification prefs | P2 | 🟢 | |

### ReportingService (Python FastAPI)

| Endpoint | Method | Description | Phase | Status | Notes |
|---|---|---|---|---|---|
| `/v1/reports/tickets` | POST | Generate ticket volume report | P3 | 🟢 | Date range, grouping, export format |
| `/v1/reports/sla` | POST | SLA compliance report | P3 | 🟢 | Per team, per policy |
| `/v1/reports/agents` | POST | Agent performance report | P3 | 🟢 | Handle time, CSAT, resolution rate |
| `/v1/reports/export` | POST | Export report as Parquet to S3 | P4 | 🟡 | Async job; webhook on complete |
| `/v1/reports/scheduled` | POST | Create scheduled report | P4 | 🔴 | Email delivery on schedule |

### WorkforceService (Java Spring Boot)

| Endpoint | Method | Description | Phase | Status | Notes |
|---|---|---|---|---|---|
| `/v1/workforce/schedules` | POST | Create agent shift schedule | P4 | 🟡 | |
| `/v1/workforce/schedules/{id}` | GET | Get schedule | P4 | 🟡 | |
| `/v1/workforce/adherence/{agentId}` | GET | Real-time schedule adherence | P4 | 🔴 | |
| `/v1/workforce/forecast` | POST | Capacity forecast (Erlang-C) | P4 | 🔴 | |

---

## 2. Service Readiness Matrix

| Service | Version | Status | Key Dependencies | Health Check URL | SLO Target | Owner Team |
|---|---|---|---|---|---|---|
| ticket-svc | 1.4.2 | ✅ PROD | RDS, Kafka, Redis | `/healthz/ready` | 99.9% avail, P99 < 300ms | Core Platform |
| agent-svc | 1.2.1 | ✅ PROD | RDS, Redis, Keycloak | `/healthz/ready` | 99.9% avail | Core Platform |
| contact-svc | 1.1.0 | ✅ PROD | RDS, OpenSearch | `/healthz/ready` | 99.9% avail | Core Platform |
| routing-engine | 2.1.0 | ✅ PROD | Redis, RDS | `/healthz/ready` | 99.9% avail, P99 < 200ms | Routing Team |
| sla-svc | 1.3.0 | ✅ PROD | Redis, RDS | `/healthz/ready` | 99.95% clock accuracy | SLA Team |
| sla-timer-worker | 1.3.0 | ✅ PROD | Redis, Kafka | `/healthz/ready` | 99.95% tick accuracy | SLA Team |
| escalation-svc | 1.1.0 | ✅ PROD | Kafka, RDS | `/healthz/ready` | 99.5% avail | SLA Team |
| channel-ingestion-svc | 1.5.0 | ✅ PROD | Kafka, Redis, ticket-svc (gRPC) | `/healthz/ready` | 99.5% message delivery | Channel Team |
| email-connector | 1.2.0 | ✅ PROD | IMAP, Kafka, Redis | `/healthz/ready` | 99.5% delivery | Channel Team |
| chat-connector | 1.4.0 | ✅ PROD | WebSocket, Kafka, Redis | `/healthz/ready` | 99.9% connection | Channel Team |
| voice-connector | 1.1.0 | 🟢 STAGING | Twilio, Kafka | `/healthz/ready` | 99.5% call handling | Channel Team |
| social-connector | 1.0.0 | 🟢 STAGING | Twitter/Facebook API, Kafka | `/healthz/ready` | 99% delivery | Channel Team |
| sms-connector | 1.2.0 | ✅ PROD | Twilio, Kafka | `/healthz/ready` | 99.5% delivery | Channel Team |
| whatsapp-connector | 0.9.0 | 🟡 IN_PROGRESS | WA Business API, Kafka | `/healthz/ready` | 99.5% delivery | Channel Team |
| knowledge-svc | 1.2.0 | 🟢 STAGING | RDS, OpenSearch | `/healthz/ready` | 99% avail | AI/ML Team |
| bot-engine | 0.8.0 | 🟡 IN_PROGRESS | Redis, OpenAI API, knowledge-svc | `/healthz/ready` | 95% intent accuracy | AI/ML Team |
| notification-svc | 1.3.0 | ✅ PROD | Kafka, SendGrid, Twilio | `/healthz/ready` | 99.5% delivery | Platform Team |
| audit-svc | 1.1.0 | ✅ PROD | RDS (append-only), Kafka | `/healthz/ready` | 99.99% durability | Security Team |
| reporting-svc | 0.7.0 | 🟡 IN_PROGRESS | RDS, S3 | `/healthz/ready` | 99% avail | Analytics Team |
| workforce-svc | 0.3.0 | 🔴 NOT_STARTED | RDS | `/healthz/ready` | 99% avail | Operations Team |
| survey-svc | 1.0.0 | 🟢 STAGING | Kafka, RDS | `/healthz/ready` | 99% avail | Analytics Team |
| automation-engine | 1.1.0 | ✅ PROD | Kafka, Redis | `/healthz/ready` | 99.5% avail | Platform Team |

---

## 3. Database Schema Status

| Table | Service Owner | Migration File | Status | Row Count (Prod) | Notes |
|---|---|---|---|---|---|
| `tenants` | agent-svc | `V1__init.sql` | ✅ PROD | ~50 | Multi-tenant root table |
| `organizations` | agent-svc | `V1__init.sql` | ✅ PROD | ~200 | |
| `agents` | agent-svc | `V1__init.sql` | ✅ PROD | ~5,000 | |
| `teams` | agent-svc | `V1__init.sql` | ✅ PROD | ~300 | |
| `agent_teams` | agent-svc | `V2__agent_teams.sql` | ✅ PROD | ~8,000 | Many-to-many |
| `skills` | agent-svc | `V2__agent_teams.sql` | ✅ PROD | ~120 | Skill taxonomy |
| `agent_skills` | agent-svc | `V2__agent_teams.sql` | ✅ PROD | ~15,000 | |
| `contacts` | contact-svc | `V1__init.sql` | ✅ PROD | ~500K | PII — RLS enabled |
| `contact_identities` | contact-svc | `V2__identities.sql` | ✅ PROD | ~750K | Email, phone, social |
| `tickets` | ticket-svc | `V1__init.sql` | ✅ PROD | ~2M | Partitioned by `created_at` |
| `ticket_threads` | ticket-svc | `V1__init.sql` | ✅ PROD | ~8M | |
| `ticket_messages` | ticket-svc | `V2__messages.sql` | ✅ PROD | ~25M | |
| `ticket_attachments` | ticket-svc | `V3__attachments.sql` | ✅ PROD | ~1.5M | S3 key references |
| `ticket_tags` | ticket-svc | `V4__tags.sql` | ✅ PROD | ~10M | |
| `custom_fields` | ticket-svc | `V8__custom_fields.sql` | 🟢 STAGING | ~5K def | Schema definitions |
| `custom_field_values` | ticket-svc | `V8__custom_fields.sql` | 🟢 STAGING | ~2M | JSONB |
| `sla_policies` | sla-svc | `V1__init.sql` | ✅ PROD | ~200 | Immutable versions |
| `sla_clocks` | sla-svc | `V1__init.sql` | ✅ PROD | ~500K active | Authoritative source |
| `sla_transitions` | sla-svc | `V2__transitions.sql` | ✅ PROD | ~4M | Immutable audit |
| `escalation_rules` | escalation-svc | `V1__init.sql` | ✅ PROD | ~800 | |
| `escalation_events` | escalation-svc | `V1__init.sql` | ✅ PROD | ~150K | |
| `routing_queues` | routing-engine | `V1__init.sql` | ✅ PROD | ~300 | |
| `routing_assignments` | routing-engine | `V1__init.sql` | ✅ PROD | ~2M | |
| `kb_articles` | knowledge-svc | `V1__init.sql` | 🟢 STAGING | ~10K | |
| `kb_article_versions` | knowledge-svc | `V2__versioning.sql` | 🟢 STAGING | ~25K | |
| `bot_sessions` | bot-engine | `V1__init.sql` | 🟡 IN_PROGRESS | — | |
| `handoff_events` | bot-engine | `V1__init.sql` | 🟡 IN_PROGRESS | — | |
| `survey_responses` | survey-svc | `V1__init.sql` | 🟢 STAGING | ~200K | |
| `audit_events` | audit-svc | `V1__init.sql` | ✅ PROD | ~50M | Append-only; no UPDATE/DELETE |
| `outbox_events` | ticket-svc | `V5__outbox.sql` | ✅ PROD | — | Cleared after publish |
| `idempotency_keys` | ticket-svc | `V6__idempotency.sql` | ✅ PROD | — | TTL 24h |
| `agent_schedules` | workforce-svc | `V1__init.sql` | 🔴 NOT_STARTED | — | |
| `agent_adherence` | workforce-svc | `V1__init.sql` | 🔴 NOT_STARTED | — | |
| `gdpr_redaction_log` | contact-svc | `V7__gdpr.sql` | 🟡 IN_PROGRESS | — | Immutable redaction audit |
| `legal_holds` | contact-svc | `V7__gdpr.sql` | 🟡 IN_PROGRESS | — | |

---

## 4. Integration Status

| Integration | Type | Direction | Protocol | Status | Owner | Notes |
|---|---|---|---|---|---|---|
| SendGrid | Email delivery | Outbound | REST API | ✅ PROD | Channel Team | DKIM+SPF configured |
| SMTP/IMAP | Email ingestion | Inbound | IMAP polling | ✅ PROD | Channel Team | 60s poll interval |
| Twilio SMS | SMS delivery + ingestion | Both | REST + Webhook | ✅ PROD | Channel Team | |
| Twilio Voice | Voice calls + IVR | Both | SIP + REST | 🟢 STAGING | Channel Team | |
| WhatsApp Business API | WhatsApp messaging | Both | REST + Webhook | 🟡 IN_PROGRESS | Channel Team | Template approval pending |
| Twitter/X API v2 | Social DMs + mentions | Both | REST + Webhook | 🟢 STAGING | Channel Team | OAuth2 PKCE |
| Facebook Messenger | Social messaging | Both | Graph API + Webhook | 🟢 STAGING | Channel Team | |
| Keycloak 24 | SSO / Auth | Both | OIDC/SAML | ✅ PROD | Security Team | Realm: cs-platform |
| OpenAI API (GPT-4o) | Bot NLP | Outbound | REST | 🟡 IN_PROGRESS | AI/ML Team | Fallback to local model |
| Dialogflow CX | Bot NLU alternative | Outbound | gRPC | 🔴 NOT_STARTED | AI/ML Team | P3 alternative |
| Salesforce | CRM sync | Both | REST + Webhook | 🔴 NOT_STARTED | Integrations Team | P4 |
| HubSpot | CRM sync | Both | REST + Webhook | 🔴 NOT_STARTED | Integrations Team | P4 |
| PagerDuty | Incident alerting | Outbound | REST | ✅ PROD | Platform Team | |
| LaunchDarkly | Feature flags | Outbound | SDK (server) | ✅ PROD | Platform Team | |
| AWS Transcribe | Voice transcription | Async | S3 trigger | 🟢 STAGING | AI/ML Team | |
| ClamAV | Malware scanning | Sync | ICAP | 🟡 IN_PROGRESS | Security Team | Attachment scan before storage |
| Prometheus/Grafana | Metrics + dashboards | Pull | Prometheus scrape | ✅ PROD | Platform Team | |
| OpenTelemetry/Jaeger | Distributed tracing | Push | OTLP | ✅ PROD | Platform Team | 5% sampling |
| ELK Stack | Log aggregation | Push | Fluent Bit | ✅ PROD | Platform Team | |

---

## 5. Domain Event Contract Status

| Event | Producer | Consumers | Kafka Topic | Schema Version | Contract Test | Notes |
|---|---|---|---|---|---|---|
| `TicketCreated` | ticket-svc | routing-engine, sla-svc, audit-svc, notification-svc | `ticket.events` | v3 | ✅ Pact | Critical path |
| `TicketStatusChanged` | ticket-svc | sla-svc, audit-svc, analytics-worker | `ticket.events` | v3 | ✅ Pact | |
| `TicketAssigned` | ticket-svc | agent-svc, notification-svc, audit-svc | `ticket.events` | v2 | ✅ Pact | |
| `TicketMerged` | ticket-svc | contact-svc, audit-svc | `ticket.events` | v1 | 🟡 In progress | |
| `SLAWarning` | sla-timer-worker | notification-svc, audit-svc | `sla.events` | v2 | ✅ Pact | |
| `SLABreached` | sla-timer-worker | escalation-svc, notification-svc, audit-svc | `sla.events` | v2 | ✅ Pact | Critical path |
| `EscalationTriggered` | escalation-svc | notification-svc, audit-svc | `escalation.events` | v2 | ✅ Pact | |
| `BotHandoffRequested` | bot-engine | ticket-svc, routing-engine, notification-svc | `bot.events` | v1 | 🟡 In progress | |
| `BotSessionEnded` | bot-engine | audit-svc, analytics-worker | `bot.events` | v1 | 🔴 Not started | |
| `ChannelMessageReceived` | channel-ingestion-svc | ticket-svc | `channel.inbound` | v4 | ✅ Pact | |
| `AgentAvailabilityChanged` | agent-svc | routing-engine, audit-svc | `agent.events` | v2 | ✅ Pact | |
| `SurveyDispatched` | survey-svc | notification-svc | `survey.events` | v1 | 🟢 Done | |
| `SurveyResponseReceived` | survey-svc | analytics-worker, audit-svc | `survey.events` | v1 | 🟢 Done | |
| `ContactMerged` | contact-svc | ticket-svc, audit-svc | `contact.events` | v1 | 🟡 In progress | |
| `GDPRRedactionCompleted` | contact-svc | ticket-svc, audit-svc | `compliance.events` | v1 | 🔴 Not started | |
| `VoiceCallEnded` | voice-connector | channel-ingestion-svc, audit-svc | `voice.events` | v1 | 🟢 Done | |

---

## 6. Testing Coverage Matrix

| Service | Unit Coverage | Integration Tests | Contract Tests (Pact) | E2E Tests | Load Test | Last Tested |
|---|---|---|---|---|---|---|
| ticket-svc | 87% | ✅ All repo/kafka/http paths | ✅ Provider verified | ✅ 3 critical paths | ✅ P99 < 280ms | 2024-07-01 |
| agent-svc | 82% | ✅ All repo/http paths | ✅ Provider verified | ✅ 2 critical paths | 🟡 Planned | 2024-07-01 |
| contact-svc | 79% | ✅ All repo paths | 🟡 In progress | 🟡 1 path | 🔴 Not started | 2024-06-15 |
| routing-engine | 91% | ✅ Redis + DB paths | ✅ Provider verified | ✅ Routing decision | ✅ P99 < 150ms | 2024-07-01 |
| sla-svc | 88% | ✅ Redis + DB + timer | ✅ Provider verified | ✅ SLA breach flow | ✅ 5000 clocks | 2024-07-01 |
| sla-timer-worker | 84% | ✅ Redis tick + Kafka | ✅ Consumer verified | ✅ Breach detection | ✅ 10K clocks | 2024-07-01 |
| escalation-svc | 80% | ✅ Kafka consumer | ✅ Consumer verified | 🟡 1 path | 🔴 Not started | 2024-06-20 |
| channel-ingestion-svc | 85% | ✅ All connectors | ✅ Consumer verified | ✅ Email/Chat/SMS | 🟡 Planned | 2024-07-01 |
| knowledge-svc | 76% | ✅ OpenSearch + DB | 🟡 In progress | 🟡 1 path | 🔴 Not started | 2024-06-25 |
| bot-engine | 68% | 🟡 In progress | 🔴 Not started | 🔴 Not started | 🔴 Not started | 2024-06-10 |
| notification-svc | 81% | ✅ Kafka consumer | ✅ Consumer verified | ✅ Email dispatch | 🔴 Not started | 2024-06-28 |
| audit-svc | 90% | ✅ DB append-only | ✅ Consumer verified | ✅ Audit trail | 🔴 Not started | 2024-07-01 |
| reporting-svc | 65% | 🟡 In progress | 🔴 Not started | 🔴 Not started | 🔴 Not started | 2024-06-01 |
| workforce-svc | 0% | 🔴 Not started | 🔴 Not started | 🔴 Not started | 🔴 Not started | — |
| survey-svc | 78% | ✅ DB + Kafka | 🟡 In progress | 🔴 Not started | 🔴 Not started | 2024-06-20 |
| automation-engine | 83% | ✅ Kafka + Redis | ✅ Consumer verified | 🟡 1 path | 🔴 Not started | 2024-06-28 |

**Coverage targets:** Unit ≥ 80%, Integration: all I/O paths, Contract: all service pairs in production.

---

## 7. Infrastructure Readiness Checklist

| Category | Item | Status | Notes |
|---|---|---|---|
| **Compute** | EKS cluster 1.29, managed node groups | ✅ | 3 AZs, us-east-1 |
| **Compute** | HPA configured for all P0 services | ✅ | CPU + custom Kafka metrics |
| **Compute** | PodDisruptionBudgets for all P0 services | ✅ | minAvailable: 2 |
| **Compute** | Spot instance node group for workers | 🟡 | In progress |
| **Database** | RDS PostgreSQL 16 Multi-AZ | ✅ | db.r7g.2xlarge |
| **Database** | Read replica (analytics) | ✅ | us-east-1 |
| **Database** | DR read replica (us-west-2) | ✅ | Cross-region |
| **Database** | Connection pooling (PgBouncer) | 🟡 | Sidecar deployment in progress |
| **Cache** | ElastiCache Redis 7 cluster mode | ✅ | 3 shards × 2 replicas |
| **Messaging** | MSK Kafka 3 brokers | ✅ | 7-day retention, TLS |
| **Search** | Amazon OpenSearch 3 data nodes | ✅ | UltraWarm configured |
| **Storage** | S3 attachments bucket + lifecycle | ✅ | SSE-KMS, versioning |
| **Storage** | S3 voice recordings bucket | ✅ | SSE-KMS, Glacier 90d |
| **Auth** | Keycloak 24, realm configured | ✅ | OIDC + SAML |
| **Auth** | IRSA roles for all services | ✅ | Least privilege |
| **Auth** | JWT validation middleware in all services | ✅ | |
| **Network** | Istio mTLS STRICT mode | ✅ | cs-system + cs-workers |
| **Network** | Istio AuthorizationPolicies | 🟡 | Partially configured |
| **Network** | Kubernetes NetworkPolicies | ✅ | Per namespace |
| **Security** | AWS WAF v2 + Shield Advanced | ✅ | |
| **Security** | ClamAV attachment scanning | 🟡 | Integration in progress |
| **Security** | Row-level security on all tenant tables | ✅ | PostgreSQL RLS |
| **CI/CD** | GitHub Actions pipelines for all services | ✅ | |
| **CI/CD** | ArgoCD GitOps for all 3 environments | ✅ | dev/staging/prod |
| **CI/CD** | Helm charts for all services | ✅ | Environment-specific values |
| **CI/CD** | Trivy image scanning in CI | ✅ | Block on CRITICAL CVEs |
| **Observability** | Prometheus + Grafana | ✅ | All services instrumented |
| **Observability** | OpenTelemetry → Jaeger tracing | ✅ | 5% sampling |
| **Observability** | ELK (Fluent Bit → OpenSearch) | ✅ | |
| **Observability** | AlertManager → PagerDuty | ✅ | SEV1/SEV2 on-call |
| **Observability** | SLO dashboards and error budgets | 🟡 | Partially complete |
| **DR** | Route 53 health-check failover | ✅ | 60s TTL |
| **DR** | Kafka MirrorMaker 2 to us-west-2 | 🟡 | In progress |
| **DR** | DR runbook tested | 🔴 | Planned Q3 2024 |
| **Compliance** | GDPR erasure workflow | 🟡 | In progress |
| **Compliance** | Legal hold mechanism | 🟡 | In progress |
| **Compliance** | PII field tagging complete | 🟢 | Schema audit done |
| **Compliance** | SOC2 controls evidence collection | 🔴 | Planned Q4 2024 |
