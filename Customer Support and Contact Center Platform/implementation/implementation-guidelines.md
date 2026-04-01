# Implementation Guidelines – Customer Support and Contact Center Platform

## 1. Technology Stack

| Service | Language | Framework | Key Libraries | Test Framework |
|---|---|---|---|---|
| TicketService | Java 21 | Spring Boot 3.2 | Spring Data JPA, Flyway, Kafka Clients, Resilience4j | JUnit 5, Mockito, Testcontainers |
| AgentService | Java 21 | Spring Boot 3.2 | Spring Security, Keycloak Adapter, MapStruct | JUnit 5, Mockito, Testcontainers |
| ContactService | Java 21 | Spring Boot 3.2 | Spring Data JPA, Elasticsearch REST client, Jackson | JUnit 5, Mockito |
| WorkforceService | Java 21 | Spring Boot 3.2 | Quartz Scheduler, Spring Data JPA | JUnit 5, Testcontainers |
| RoutingEngine | Go 1.22 | net/http + gorilla/mux | go-redis, sarama (Kafka), zap (logger), pgx | testing, testify, gomock |
| SLAService | Go 1.22 | net/http + chi | go-redis, pgx, zap | testing, testify, gomock |
| AuditService | Go 1.22 | net/http + chi | pgx, zap, opentelemetry-go | testing, testify |
| KnowledgeBaseService | Python 3.12 | FastAPI 0.111 | SQLAlchemy, alembic, elasticsearch-py, sentence-transformers | pytest, pytest-asyncio, httpx |
| BotEngine | Python 3.12 | FastAPI 0.111 | aiohttp, redis-py, openai, langchain | pytest, pytest-asyncio, respx |
| ReportingService | Python 3.12 | FastAPI 0.111 | pandas, sqlalchemy, apache-arrow, boto3 | pytest, pytest-asyncio |
| ChannelIngestionService | Node.js 20 | Express 4 / Fastify 4 | kafkajs, nodemailer, ioredis, axios, ws | Jest, Supertest, nock |
| AutomationEngine | Node.js 20 | Fastify 4 | kafkajs, ioredis, jsonata, ajv | Jest, Supertest |
| NotificationService | Node.js 20 | Fastify 4 | kafkajs, nodemailer, twilio, @slack/web-api | Jest, Supertest |

### Dependency Management
- **Java**: Maven 3.9 with BOM for Spring Boot; Dependabot for security patches.
- **Go**: Go modules (`go.mod`); `govulncheck` in CI for vulnerability scanning.
- **Python**: `poetry` for dependency management; `pip-audit` in CI.
- **Node.js**: `pnpm` workspaces; `npm audit` in CI.

---

## 2. Phase 1 – Foundation (Weeks 1–8)

### Deliverables

#### 2.1 Infrastructure Setup
- Provision EKS cluster (1.29) across 3 AZs in `us-east-1` using Terraform.
- Deploy Amazon RDS PostgreSQL 16 (Multi-AZ, `db.r7g.2xlarge`).
- Deploy Amazon ElastiCache Redis 7 (cluster mode, 3 shards × 2 replicas).
- Deploy Amazon MSK Kafka (3 brokers, `kafka.m5.2xlarge`).
- Deploy Amazon OpenSearch (3 data nodes, `r6g.2xlarge.search`).
- Configure Istio service mesh with mTLS in `STRICT` mode for `cs-system` namespace.
- Set up ArgoCD for GitOps deployment of all services.
- Configure Keycloak 24 with realm `cs-platform`, SAML/OIDC clients for agent workspace and supervisor console.
- Create foundational Helm charts for all services with environment-specific values.

**Acceptance Criteria:**
- All infrastructure provisioned via Terraform (no manual clicks).
- Keycloak SSO login works for a test agent and test supervisor.
- All services reachable via internal cluster DNS.
- Prometheus scraping metrics from all pods.
- ELK stack receiving structured JSON logs from all services.

**Team:** Platform Engineering (2 engineers, 8 weeks)

#### 2.2 Core Authentication Service
- Keycloak integration via Spring Boot Keycloak Adapter.
- JWT validation middleware for all Java/Go/Python/Node.js services.
- Role definitions: `AGENT`, `SUPERVISOR`, `ADMIN`, `READ_ONLY`.
- Service-to-service auth: mTLS (Istio) + service account tokens.
- IRSA roles for all pods to access AWS Secrets Manager.

#### 2.3 Organization / Team / Agent Management
- `AgentService`: CRUD for agents, teams, organizations.
- Agent availability state machine: `AVAILABLE → BUSY → AWAY → OFFLINE`.
- Skill assignment: agent ↔ skill group many-to-many.
- REST endpoints: `POST /v1/agents`, `GET /v1/agents/{id}`, `PUT /v1/agents/{id}/availability`.
- Agent state persisted in Redis (`agent:presence:{agentId}`) with PostgreSQL as source of truth.

#### 2.4 Basic Ticket CRUD
- `TicketService`: create, read, update, list (paginated).
- Ticket status state machine: `NEW → OPEN → PENDING → RESOLVED → CLOSED`.
- Immutable audit event emitted on every status transition (outbox pattern → Kafka `ticket.events`).
- Correlation ID (`X-Correlation-ID` header) propagated through all calls.
- Idempotency: `POST /v1/tickets` accepts `X-Idempotency-Key` header; duplicate requests return existing ticket.

#### 2.5 Email Channel Ingestion (Basic IMAP Polling)
- `ChannelIngestionService` polls configured mailbox via IMAP every 60 seconds.
- Parses email headers: `From`, `To`, `Subject`, `Message-ID`, `In-Reply-To`, `References`.
- Normalizes to `ChannelMessage` DTO; publishes to Kafka `channel.inbound`.
- Deduplication: `Message-ID` stored in Redis with 7-day TTL.
- Thread detection: `In-Reply-To` and `References` headers used to link emails to existing tickets.

#### 2.6 Simple Round-Robin Routing
- `RoutingEngine`: assign ticket to next available agent in round-robin order.
- Agent queue state in Redis sorted set keyed by `routing:queue:{teamId}`.
- Fallback: if no agent available, ticket enters `QUEUED` state.
- REST endpoint: `POST /v1/routing/assign` (called by TicketService on ticket creation).

#### 2.7 Basic SLA Policy Framework
- `SLAService`: define SLA policies with `first_response_minutes` and `resolution_minutes`.
- SLA clock started when ticket moves to `OPEN`.
- SLA clock stored in Redis sorted set: `sla:clock:{tenantId}` with score = `breach_at_unix_ms`.
- `sla-timer-worker` polls every second; emits `SLAWarning` at 80%, `SLABreached` at 100%.

#### 2.8 REST API Foundation
- OpenAPI 3.1 spec-first development: all endpoints specified in YAML before implementation.
- Kong/Nginx API Gateway with JWT validation, rate limiting (100 req/min per client).
- Standard error response envelope: `{ "error": { "code": "TICKET_NOT_FOUND", "message": "...", "correlationId": "..." } }`.
- Pagination: cursor-based for lists; `?limit=20&cursor=<opaque>`.

### Phase 1 Milestones

| Milestone | Week | Deliverable | Acceptance Test |
|---|---|---|---|
| M1.1 – Infra Live | 2 | EKS + RDS + Redis + Kafka + OpenSearch deployed | All health checks green |
| M1.2 – Auth Working | 3 | Keycloak SSO; JWT validated in all services | Agent can log in; invalid JWT rejected |
| M1.3 – Ticket API | 5 | Ticket CRUD + status transitions | CRUD tests pass; audit events emitted |
| M1.4 – Email Ingestion | 6 | IMAP polling creates tickets from email | End-to-end: send email → ticket created |
| M1.5 – Routing + SLA | 8 | Round-robin routing; SLA clock running | SLA breach event emitted on schedule |

---

## 3. Phase 2 – Core Features (Weeks 9–16)

### Deliverables

#### 3.1 Omni-Channel: Live Chat, SMS/WhatsApp, Social
- **Chat Widget**: WebSocket-based chat connector; React SDK for embedding in customer portals.
- **SMS/WhatsApp**: Twilio webhooks → `ChannelIngestionService` → Kafka `channel.inbound`.
- **Social Media**: Twitter/X and Facebook Messenger webhooks with OAuth2 token management.
- Channel-specific message normalization in `ChannelIngestionService` before `TicketService`.
- Outbound message routing: `NotificationService` dispatches via appropriate channel adapter.

#### 3.2 Skill-Based Routing Engine
- `RoutingEngine` upgraded from round-robin to skill-based matching algorithm:
  1. Identify required skills from ticket metadata and channel.
  2. Filter agents with all required skills and `AVAILABLE` status.
  3. Score candidates: skill proficiency weight × current workload penalty.
  4. Assign to highest-scored agent; update Redis availability state.
- `AgentSkillRepository` backed by PostgreSQL; cached in Redis with 5-minute TTL.
- Load balancing: max concurrent tickets per agent enforced (configurable per team).

#### 3.3 SLA Breach Detection and Auto-Escalation
- `sla-timer-worker` emits `SLABreached` event to Kafka `sla.events`.
- `EscalationService` consumes `SLABreached`; applies escalation rules from `EscalationRuleRepository`.
- Escalation actions: `REASSIGN_AGENT`, `REASSIGN_TEAM`, `NOTIFY_SUPERVISOR`, `INCREASE_PRIORITY`.
- Escalation chains: up to 3 levels; each level has own notification template.
- `NotificationService` dispatches email/SMS/in-app notification to supervisor on breach.

#### 3.4 Knowledge Base with Full-Text Search
- `KnowledgeBaseService` (Python FastAPI) stores articles in PostgreSQL; indexes in OpenSearch.
- Full-text search: OpenSearch query with BM25 scoring + synonym expansion.
- Article categories, tags, and access control (public vs. agent-only).
- REST: `GET /v1/kb/articles/search?q=<query>&category=<cat>`.
- Agent workspace shows suggested articles based on ticket subject/description (keyword match).

#### 3.5 Canned Responses and Automation Rules
- `AutomationEngine` (Node.js): JSON-rule-based automation triggered on ticket events.
- Rules: `IF ticket.channel == 'email' AND ticket.subject CONTAINS 'invoice' THEN assign_tag('billing')`.
- Canned response library: agent-scoped and team-scoped templates with variable substitution (`{{customer.name}}`).
- Automation rule evaluation order enforced; conflicts flagged at rule-creation time.

#### 3.6 CSAT/NPS Survey Dispatch
- `SurveyService`: configurable survey triggers (on ticket resolution, after 24h).
- Survey template: CSAT (1–5 stars) and NPS (0–10 scale).
- Dispatch via `NotificationService` (email or in-app).
- Survey response stored in PostgreSQL `survey_responses` table.
- `survey-worker` aggregates daily CSAT scores per team/agent.

#### 3.7 Real-Time Supervisor Dashboard
- `supervisor-console-api` streams real-time metrics via Server-Sent Events (SSE).
- Metrics: queue depth per channel, average handle time, agent utilization, SLA compliance %.
- Supervisor can force-reassign ticket, change priority, or add to watch list in real time.
- WebSocket connection to `agent-workspace-api` for live ticket feed.

#### 3.8 Contact 360° Profile with Merge
- `ContactService`: unified customer profile aggregated from all channel identities.
- Identity resolution: email, phone, external customer ID linked to single `Contact` record.
- Contact merge: supervisor initiates merge of duplicate contacts; immutable merge audit event.
- Contact 360° view: full ticket history, channel interactions, CSAT scores, notes.

### Phase 2 Milestones

| Milestone | Week | Deliverable | Acceptance Test |
|---|---|---|---|
| M2.1 – All Channels Live | 11 | Chat, SMS, WhatsApp, Social ingestion | Message from each channel creates ticket |
| M2.2 – Skill Routing | 12 | Skill-based routing live | Ticket with `billing` tag routed to billing-skilled agent |
| M2.3 – SLA Escalations | 13 | Auto-escalation on breach | SLA breach → supervisor notified within 30s |
| M2.4 – KB + Automation | 14 | KB search + automation rules | KB article surfaced; automation tag applied |
| M2.5 – Supervisor Dashboard | 16 | Real-time dashboard live | Queue depth and SLA shown; force-assign works |

---

## 4. Phase 3 – Intelligence Layer (Weeks 17–24)

### Deliverables

#### 4.1 AI Chatbot Integration with NLP
- `BotEngine` (Python FastAPI): integrates Dialogflow CX or custom LLM via OpenAI API.
- Intent classification: 95%+ accuracy threshold for production deployment.
- Entity extraction: customer account number, order ID, product SKU.
- Conversation context stored in Redis `bot:session:{sessionId}` with 30-minute TTL.
- Bot resolution rate target: 40% of incoming chat tickets resolved without human agent.

#### 4.2 Bot-to-Human Handoff with Full Context Transfer
- Handoff trigger: low confidence score (< 0.7), explicit customer request, or max turn limit exceeded.
- Context serialization: full conversation transcript, extracted entities, predicted intent, customer sentiment score.
- Atomic handoff: bot session frozen → ticket created (or existing ticket updated) → agent assigned → transcript delivered to agent workspace.
- Handoff SLA: agent assigned within 2 minutes; if no agent available, bot holds with "connecting you to an agent" message and queued handoff.
- Failed handoff (no agent after 5 min): bot resumes with "callback scheduled" fallback.

#### 4.3 AI-Powered Knowledge Base Search
- Semantic search using sentence-transformers (`all-MiniLM-L6-v2`) with vector embeddings stored in OpenSearch kNN index.
- Hybrid search: BM25 keyword + kNN vector with RRF (Reciprocal Rank Fusion) for re-ranking.
- KB article auto-suggestion: bot uses semantic search to retrieve top-3 articles per intent.
- Feedback loop: agent accepts/rejects suggestion → updates article relevance score.

#### 4.4 Predictive Routing (ML Model Integration)
- ML model served via `ReportingService` FastAPI: predicts best agent for ticket based on historical CSAT, resolution time, and ticket topic.
- Features: ticket topic embedding, time of day, agent recent performance, current queue depth.
- Model retrained weekly on last 30 days of resolved tickets.
- A/B test: 20% of tickets use predictive routing; 80% use skill-based routing. Compare CSAT and resolution time.

#### 4.5 Advanced Analytics and Custom Reports
- `ReportingService`: custom report builder with metric selection, grouping, and date ranges.
- Metrics: first response time, resolution time, re-open rate, CSAT, NPS, SLA compliance, bot resolution rate.
- Scheduled reports: daily/weekly email delivery via `NotificationService`.
- Data warehouse export: Parquet to S3 for BI tool integration (Tableau, Looker).

#### 4.6 Voice Channel: Call Recording and Transcript
- `voice-connector`: records calls to S3 `cs-voice-recordings-prod` via FreeSWITCH/Twilio recording.
- Transcription: AWS Transcribe job triggered on `VoiceCallEnded` event; transcript stored in PostgreSQL.
- Transcript indexed in OpenSearch for agent search and compliance review.
- PII redaction in transcript: card numbers, SSNs masked before storage.

#### 4.7 IVR Integration
- IVR menu definition stored in `WorkforceService` as configurable JSON tree.
- Twilio IVR/Studio integration via TwiML webhook served by `voice-connector`.
- IVR data (menu selections, account lookup result) attached to ticket on agent answer.

### Phase 3 Milestones

| Milestone | Week | Deliverable | Acceptance Test |
|---|---|---|---|
| M3.1 – Bot Live | 19 | Bot resolves 30%+ chat tickets | Bot resolution rate ≥ 30% in staging |
| M3.2 – Handoff | 20 | Bot-to-human handoff with context | Agent receives full context; no repeated questions |
| M3.3 – Semantic KB | 21 | Vector search live | Top-3 KB suggestions for test intents match expected |
| M3.4 – Voice + IVR | 23 | Call recording + transcript + IVR | Recording in S3; transcript in OpenSearch |
| M3.5 – Analytics | 24 | Custom report builder + Parquet export | Report matches manual SQL validation |

---

## 5. Phase 4 – Enterprise Features (Weeks 25–32)

### Deliverables

#### 5.1 Workforce Management
- `WorkforceService`: agent shift scheduling, break management, capacity forecasting.
- Schedule adherence monitoring: compare actual agent availability vs. scheduled hours in real time.
- Erlang-C capacity model: forecast required agents per hour based on historical ticket volume and target SLA.
- Supervisor schedule editor: drag-and-drop calendar UI backed by `WorkforceService` REST API.

#### 5.2 GDPR/CCPA Privacy Controls
- Right-to-Erasure workflow: `ContactService` redacts all PII fields; linked ticket content sanitized.
- Data redaction catalog: all PII fields tagged in schema (`@PII(category=EMAIL)` annotation on JPA entities).
- Two-phase redaction: flag → supervisor approval → execute → immutable redaction audit event.
- Legal hold: retention job skips records with active legal hold flag.
- Data portability: `POST /v1/contacts/{id}/export` generates GDPR data export ZIP.

#### 5.3 Custom Fields Framework
- Tenants define custom fields (text, number, date, enum, boolean) per ticket, contact, or agent record.
- Custom field values stored in `custom_field_values` JSONB column (PostgreSQL).
- Custom fields indexed in OpenSearch for search/filter.
- Custom field validation: regex patterns, required/optional, visibility (agent-only vs. public).

#### 5.4 Multi-Language Support
- All UI strings externalized to i18n resource bundles (Java: `messages.properties`; Node.js: `i18next`; Python: `Babel`).
- Language detected from browser `Accept-Language` header or explicit customer preference.
- Knowledge base articles in multiple languages; language-specific OpenSearch indices.
- Bot NLP models: language-specific intent classifiers.

#### 5.5 CRM Integrations: Salesforce and HubSpot
- `AutomationEngine` integration adapters: Salesforce REST API and HubSpot API.
- Bidirectional sync: contact and ticket data synced on creation/update.
- Field mapping configuration per tenant stored in `integration_configs` table.
- Webhook-based sync: Salesforce/HubSpot pushes changes to platform via registered webhooks.
- OAuth2 token management with auto-refresh stored in Secrets Manager.

#### 5.6 Performance Optimization and Load Testing
- k6 load test suite: 500 concurrent agents, 5000 concurrent customers, 10,000 tickets/hour.
- Performance targets: ticket creation P99 < 300ms; routing assignment P99 < 200ms; SLA breach detection latency < 5s.
- Database connection pooling: PgBouncer sidecar for Java services (pool size = 10 per pod).
- Redis pipeline batching for SLA clock operations (batch 100 clock reads per tick).
- OpenSearch query caching for repeated KB searches (5-minute result cache in Redis).

### Phase 4 Milestones

| Milestone | Week | Deliverable | Acceptance Test |
|---|---|---|---|
| M4.1 – Workforce Mgmt | 27 | Schedule editor + adherence live | Supervisor creates schedule; adherence tracked |
| M4.2 – GDPR Controls | 28 | Right-to-erasure end-to-end | Erasure request redacts all PII; audit log preserved |
| M4.3 – Custom Fields | 29 | Custom field CRUD + search | Custom field on ticket; searchable in KB |
| M4.4 – CRM Integration | 30 | Salesforce/HubSpot bidirectional sync | Contact created in SF; synced to platform |
| M4.5 – Load Test Pass | 32 | All perf targets met under load | k6: P99 < 300ms at 10k tickets/hour |

---

## 6. Coding Standards

### 6.1 Java (Spring Boot Services)

**Package Structure:**
```
ticket-service/
├── api/                        # REST controllers, request/response DTOs, OpenAPI annotations
│   ├── TicketController.java
│   ├── dto/
│   │   ├── CreateTicketRequest.java
│   │   └── TicketResponse.java
├── application/                # Application services, use case orchestrators
│   ├── TicketApplicationService.java
│   └── command/
│       ├── CreateTicketCommand.java
│       └── UpdateTicketStatusCommand.java
├── domain/                     # Domain entities, value objects, domain services, domain events
│   ├── ticket/
│   │   ├── Ticket.java          # Aggregate root
│   │   ├── TicketId.java        # Value object
│   │   ├── TicketStatus.java    # Enum with transition guard
│   │   └── TicketFactory.java
│   ├── sla/
│   │   ├── SLAPolicy.java
│   │   └── SLAClock.java
│   └── event/
│       └── TicketCreatedEvent.java
├── infrastructure/             # Spring Data JPA repos, Kafka producers, external adapters
│   ├── persistence/
│   │   └── TicketJpaRepository.java
│   ├── messaging/
│   │   └── KafkaEventPublisher.java
│   └── client/
│       └── RoutingEngineClient.java
└── config/                     # Spring @Configuration, beans, security, Flyway
    ├── SecurityConfig.java
    └── KafkaConfig.java
```

**Conventions:**
- Use `record` for DTOs (Java 16+); no setters on domain entities.
- Domain objects never depend on infrastructure; use repository interfaces in `domain/`.
- All public API methods documented with JavaDoc; internal methods only if non-obvious.
- Prefer `Optional<T>` over null returns in service layer.
- Use `@Transactional` only at application service layer (never domain or infrastructure).

### 6.2 Go (RoutingEngine, SLAService, AuditService)

**Package Structure:**
```
routing-engine/
├── cmd/server/main.go          # Entry point; wire dependencies
├── internal/
│   ├── handler/                # HTTP handlers (thin — delegate to service)
│   ├── service/                # Business logic
│   │   ├── routing_service.go
│   │   └── skill_matcher.go
│   ├── repository/             # Data access (pgx, redis)
│   ├── model/                  # Domain structs (no ORM tags)
│   └── event/                  # Kafka producer/consumer
├── pkg/
│   ├── health/                 # Health check handler
│   └── middleware/             # Auth, logging, tracing middleware
└── config/                     # Viper config loading
```

**Conventions:**
- Standard library preferred; minimize third-party dependencies.
- Explicit error handling: never ignore errors; wrap with `fmt.Errorf("context: %w", err)`.
- Goroutine patterns: use `errgroup` for concurrent operations; cancel contexts on shutdown.
- Prefer `context.Context` as first parameter for all functions with I/O.
- Use `sync.Mutex` sparingly; prefer channel-based communication.
- Structured logging with `zap`; log fields as key-value pairs (no string formatting).

### 6.3 Python (FastAPI Services)

**Package Structure:**
```
knowledge-base-service/
├── app/
│   ├── main.py                 # FastAPI app factory; router registration
│   ├── api/v1/
│   │   └── articles.py         # Route handlers (thin — delegate to service)
│   ├── schemas/                # Pydantic models for request/response
│   │   └── article.py
│   ├── services/               # Business logic; async
│   │   └── article_service.py
│   ├── repositories/           # SQLAlchemy async sessions
│   │   └── article_repository.py
│   ├── models/                 # SQLAlchemy ORM models
│   │   └── article.py
│   └── core/
│       ├── config.py           # Pydantic Settings
│       ├── security.py         # JWT verification
│       └── elasticsearch.py    # AsyncElasticsearch client
├── alembic/                    # Database migrations
├── tests/
│   ├── unit/
│   └── integration/
└── pyproject.toml
```

**Conventions:**
- Use `async/await` throughout; no blocking calls in async routes.
- Pydantic v2 models for all request/response schemas; use `model_config = ConfigDict(from_attributes=True)`.
- Dependency injection via FastAPI `Depends()` for DB sessions, auth, and config.
- All DB operations use `AsyncSession` from SQLAlchemy 2.0+.
- Alembic for all schema migrations; never mutate schema manually.
- Type hints required on all public functions.

### 6.4 Node.js (Channel/Automation/Notification Services)

**Conventions:**
- TypeScript (strict mode) for all Node.js services; no `any` types.
- Use Fastify over Express for performance (2× faster JSON serialization).
- KafkaJS for Kafka; ioredis for Redis; prisma for ORM.
- Use `async/await`; no callback-based code.
- Environment variables via `dotenv` + Zod schema validation at startup.
- Use `pino` for structured logging (compatible with ELK).

### 6.5 Shared Standards

**API Design:**
- OpenAPI 3.1 spec written first; controllers generated or validated against spec.
- Versioning: URL-based (`/v1/`); no breaking changes without version bump.
- All mutating operations require `X-Idempotency-Key` header.
- All requests emit `X-Correlation-ID` (generate if not present); log in every service.
- Standard error codes: `TICKET_NOT_FOUND`, `AGENT_UNAVAILABLE`, `SLA_POLICY_CONFLICT`, etc.

**Git Workflow:**
- Branch naming: `feat/<ticket-id>-<description>`, `fix/<ticket-id>-<description>`, `chore/<description>`.
- Semantic commit messages: `feat(ticket): add custom field support`, `fix(sla): correct timezone offset calculation`.
- PR requirements: 1 approval from code owner + all CI checks green; no direct pushes to `main`.
- Squash merge to `main`; linear history enforced.

**Testing Pyramid:**
| Level | Coverage Target | Tools | Run In |
|---|---|---|---|
| Unit | ≥ 80% line coverage | JUnit5/Mockito, pytest, Jest, testify | Every commit (local + CI) |
| Integration | All repository + kafka + REST adapter paths | Testcontainers (Java/Go/Python), Supertest (Node) | CI on every PR |
| Contract | All service pairs (Pact provider + consumer tests) | Pact Broker, pact-jvm, pact-go, pact-python | CI on every PR |
| E2E | 10 critical paths (ticket create, route, SLA breach, bot handoff, etc.) | Playwright + k6 | Staging on every deployment |
| Load | 10,000 tickets/hour, P99 < 300ms | k6 | Pre-prod promotion gate |

---

## 7. Deployment Pipeline

### 7.1 CI/CD with GitHub Actions

```yaml
# .github/workflows/ticket-svc.yml (abbreviated)
name: ticket-svc CI/CD
on:
  push:
    paths: ['services/ticket-svc/**']
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run unit + integration tests
        run: mvn verify -pl services/ticket-svc --no-transfer-progress
      - name: Upload coverage to SonarCloud
        run: mvn sonar:sonar
  build-push:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Build Docker image
        run: docker build -t $ECR_REGISTRY/cs/ticket-svc:$GITHUB_SHA .
      - name: Push to ECR
        run: docker push $ECR_REGISTRY/cs/ticket-svc:$GITHUB_SHA
      - name: Update Helm values (dev)
        run: |
          yq e ".image.tag = \"$GITHUB_SHA\"" -i helm/ticket-svc/values-dev.yaml
          git commit -am "chore(deploy): ticket-svc $GITHUB_SHA to dev"
          git push
```

### 7.2 Environment Promotion Gates

```
Dev → Staging:
  - All unit + integration + contract tests pass
  - No CRITICAL SonarCloud issues
  - Docker image vulnerability scan (Trivy): no CRITICAL CVEs
  - Manual trigger by engineer

Staging → Production:
  - Load test P99 < 300ms at 500 concurrent users
  - E2E critical paths 100% pass
  - Manual approval from tech lead + on-call engineer
  - Deployment runbook reviewed and signed off
```

### 7.3 Database Migrations
- **Java services**: Flyway (`db/migration/V1__init.sql`, `V2__add_custom_fields.sql`).
- **Python services**: Alembic with autogenerate; always reviewed before merge.
- Migration rules: never drop columns in same release as code change (2-phase: deprecate → delete).
- Rollback: each migration has corresponding rollback script in `db/rollback/`.
- Staging migration dry-run performed before every production deployment.

### 7.4 Feature Flags (LaunchDarkly)
- Feature flags for all new Phase 2/3/4 features; never ship code that is always-on on day 1.
- Flag naming: `cs.<service>.<feature>` (e.g., `cs.routing.predictive`, `cs.bot.enabled`).
- Gradual rollout: 1% → 10% → 50% → 100% with monitoring at each step.
- Kill-switch flags for high-risk features: `cs.sla.auto-escalation.enabled`.

---

## 8. Observability

### 8.1 Metrics (Prometheus + Grafana)

Every service exposes `GET /metrics` (Prometheus format). Key custom metrics:

| Metric | Type | Labels | Service |
|---|---|---|---|
| `cs_ticket_created_total` | Counter | `channel`, `tenant_id` | ticket-svc |
| `cs_ticket_status_transition_total` | Counter | `from_status`, `to_status` | ticket-svc |
| `cs_routing_assignment_duration_seconds` | Histogram | `algorithm`, `skill_group` | routing-engine |
| `cs_sla_clock_active` | Gauge | `tenant_id`, `policy_type` | sla-timer-worker |
| `cs_sla_breach_total` | Counter | `tenant_id`, `policy_type`, `breach_type` | sla-timer-worker |
| `cs_bot_handoff_total` | Counter | `reason`, `outcome` | bot-engine |
| `cs_channel_ingest_duration_seconds` | Histogram | `channel` | channel-ingestion-svc |
| `cs_queue_depth` | Gauge | `team_id`, `channel` | routing-engine |

### 8.2 Distributed Tracing (OpenTelemetry → Jaeger)
- All services instrumented with OpenTelemetry SDK (Java: `opentelemetry-spring-boot`, Go: `opentelemetry-go`, Python: `opentelemetry-fastapi`, Node: `@opentelemetry/sdk-node`).
- Trace context propagated via W3C `traceparent` header.
- Sampling: 5% for normal traffic; 100% for errors and slow requests (> 1s).
- Key spans: `TicketService.createTicket`, `RoutingEngine.assignAgent`, `SLAService.startClock`, `BotEngine.processMessage`.
- Jaeger UI available at `https://jaeger.internal.cs-platform.com`.

### 8.3 Structured Logging (JSON → ELK)
- All services log JSON to stdout; Fluent Bit DaemonSet ships logs to OpenSearch.
- Mandatory log fields: `timestamp`, `level`, `service`, `correlationId`, `tenantId`, `userId`, `traceId`, `spanId`, `message`.
- Log levels: `DEBUG` (dev only), `INFO` (normal operations), `WARN` (degraded), `ERROR` (failures), `FATAL` (service unable to start).
- Sensitive data never logged: no passwords, tokens, PII, card numbers.
- Log retention: 30 days in OpenSearch hot tier; 90 days in warm tier; 1 year in S3 cold archive.

### 8.4 Alerting (AlertManager → PagerDuty)

| Alert | Condition | Severity | Notification |
|---|---|---|---|
| `HighSLABreachRate` | `cs_sla_breach_total rate > 5% for 5m` | SEV2 | PagerDuty + Slack #incidents |
| `KafkaConsumerLagHigh` | `kafka_consumer_lag{topic="sla.events"} > 2000 for 3m` | SEV2 | PagerDuty |
| `TicketServiceErrorRate` | `error_rate{service="ticket-svc"} > 1% for 2m` | SEV2 | PagerDuty |
| `RoutingLatencyHigh` | `cs_routing_assignment_duration_seconds p99 > 2s for 5m` | SEV3 | Slack #alerts |
| `RDSConnectionsHigh` | `rds_connections > 450 for 5m` | SEV3 | Slack #alerts |
| `SLATimerWorkerDown` | `up{job="sla-timer-worker"} == 0 for 1m` | SEV1 | PagerDuty (immediate page) |
| `BotHandoffFailureRate` | `cs_bot_handoff_total{outcome="failed"} rate > 10% for 10m` | SEV3 | Slack #alerts |

### 8.5 SLO Dashboard (Error Budgets)

| Service | SLO | Error Budget (30-day) | Burn Rate Alert |
|---|---|---|---|
| `ticket-svc` | 99.9% availability | 43.2 minutes downtime | 5× burn rate → page |
| `routing-engine` | 99.9% availability; P99 < 500ms | 43.2 minutes | 5× burn rate → page |
| `sla-timer-worker` | 99.95% accuracy (clocks within 5s) | 21.6 minutes | 2× burn rate → page |
| `bot-engine` | 95% intent classification accuracy | 5% misclassification | Weekly review |
| `channel-ingestion-svc` | 99.5% message delivery | 3.6 hours | 10× burn rate → page |
| End-to-end ticket create | P99 < 300ms | N/A | Grafana alert |
