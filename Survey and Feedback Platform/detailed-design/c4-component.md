# C4 Component Diagram — Survey and Feedback Platform

## Overview

This document presents C4 Level 3 (Component) diagrams for each backend microservice in the
Survey and Feedback Platform. C4 Level 3 zooms into the internal structure of a single
**Container** (a running process or deployable unit) to show its constituent **Components** —
discrete, well-scoped units of functionality with defined interfaces and responsibilities.

**Scope:** Four services are documented here — Survey Service, Response Service, Distribution
Service, and Analytics Service. Each diagram shows:

- Components within the service boundary
- External systems and data stores that the service communicates with directly
- Named relationships with protocol or mechanism labels

These diagrams are generated from the perspective of a developer implementing or debugging a
specific service. For system-wide context, refer to the C4 Container diagram. For deployment
topology, refer to the Infrastructure Architecture document.

---

## Survey Service — C4 Component Diagram

The Survey Service owns the survey authoring lifecycle: creation, question management,
conditional logic validation, version snapshotting, publication, and state transitions.
It is a FastAPI application deployed as an AWS ECS Fargate task.

```mermaid
C4Component
    title Component Diagram - Survey Service

    Person(admin, "Workspace Admin", "Creates and manages surveys")
    System_Ext(cdn, "CloudFront CDN", "Serves static frontend assets")

    Container_Boundary(survey_svc, "Survey Service (FastAPI / Python 3.11)") {
        Component(router, "SurveyRouter", "FastAPI APIRouter", "Registers HTTP routes; injects Pydantic v2 request schemas; auto-generates OpenAPI spec")
        Component(ctrl, "SurveyController", "Python Class", "Maps HTTP requests to service operations; handles HTTP-level error translation")
        Component(svc, "SurveyService", "Python Async Class", "Enforces survey lifecycle state machine; orchestrates question management and publication")
        Component(qsvc, "QuestionService", "Python Async Class", "CRUD for questions and options; bulk reorder; validates question type constraints")
        Component(logic, "LogicValidator", "Python Dataclass", "Validates conditional branch rules: checks referenced question IDs and answer value types")
        Component(version, "VersionManager", "Python Class", "Creates immutable version snapshots on publish; enables before/after diff for audit")
        Component(repo, "SurveyRepository", "async SQLAlchemy", "PostgreSQL read/write operations for surveys table; implements optimistic locking via version column")
        Component(qrepo, "QuestionRepository", "async SQLAlchemy", "PostgreSQL read/write for questions and question_options tables; bulk insert for reorder")
        Component(cache, "CacheManager", "aioredis Client", "TTL-based Redis cache for serialized survey definitions; invalidated on any mutation")
        Component(events, "EventPublisher", "aioredis XADD", "Publishes domain events to Redis Streams on state transitions")
    }

    System_Ext(pg, "PostgreSQL 15 (AWS RDS)", "Primary relational store for survey and question records")
    System_Ext(redis, "Redis 7 (ElastiCache)", "In-memory cache and Redis Streams event bus")

    Rel(admin, router, "Calls", "HTTPS / REST JSON")
    Rel(router, ctrl, "Delegates to", "In-process async call")
    Rel(ctrl, svc, "Invokes", "In-process async call")
    Rel(ctrl, qsvc, "Invokes", "In-process async call")
    Rel(svc, logic, "Validates rules via", "In-process call")
    Rel(svc, version, "Snapshots via", "In-process call on publish")
    Rel(svc, repo, "Persists surveys via", "async SQLAlchemy / psycopg3")
    Rel(svc, cache, "Reads and invalidates", "Redis GET / SET / DEL")
    Rel(svc, events, "Publishes state events", "Redis XADD")
    Rel(qsvc, qrepo, "Persists questions via", "async SQLAlchemy / psycopg3")
    Rel(qsvc, logic, "Validates rules via", "In-process call")
    Rel(repo, pg, "SQL read/write", "TLS / async psycopg3")
    Rel(qrepo, pg, "SQL read/write", "TLS / async psycopg3")
    Rel(cache, redis, "Cache operations", "Redis TCP / aioredis")
    Rel(events, redis, "Stream publish", "Redis XADD / aioredis")
```

---

## Response Service — C4 Component Diagram

The Response Service manages the respondent-facing answer collection lifecycle. It handles
session issuance, real-time answer saving, deduplication, GDPR masking, and streaming of
completed responses to the analytics pipeline.

```mermaid
C4Component
    title Component Diagram - Response Service

    Person(respondent, "Survey Respondent", "Completes survey forms via browser or embedded link")

    Container_Boundary(resp_svc, "Response Service (FastAPI / Python 3.11)") {
        Component(rrouter, "ResponseRouter", "FastAPI APIRouter", "HTTP routes for session start, answer save, session complete, and admin response retrieval")
        Component(rctrl, "ResponseController", "Python Class", "HTTP handler: issues session tokens, validates auth, translates service errors to HTTP status codes")
        Component(rsvc, "ResponseService", "Python Async Class", "Orchestrates session state transitions; coordinates deduplication, processing, GDPR, and persistence")
        Component(dedup, "DeduplicationEngine", "Python Class", "Checks Redis set of IP+fingerprint hashes; enforces one-response-per-survey policy")
        Component(proc, "AnswerProcessor", "Python Class", "Coerces raw answer payloads to typed values; validates answer against question config schema")
        Component(gdpr, "GDPRFilter", "Python Class", "Masks or drops PII fields (name, email, IP) based on workspace GDPR configuration before storage")
        Component(rrepo, "ResponseRepository", "Motor Async Driver", "MongoDB upsert of response documents; queries for admin export and pagination")
        Component(kinesis, "KinesisProducer", "boto3 Kinesis Client", "Publishes completed response records to Kinesis Data Streams for the analytics pipeline")
        Component(ws, "WebSocketManager", "FastAPI WebSocket", "Maintains WS connections; broadcasts real-time response arrival events to analytics dashboards")
    }

    System_Ext(mongo, "MongoDB 7 (DocumentDB)", "Stores response session documents with nested answer arrays")
    System_Ext(redis2, "Redis 7 (ElastiCache)", "Deduplication fingerprint sets and WebSocket connection registry")
    System_Ext(kstream, "AWS Kinesis Data Streams", "Durable ordered stream of completed response events for the analytics pipeline")

    Rel(respondent, rrouter, "Submits answers", "HTTPS / REST JSON")
    Rel(rrouter, rctrl, "Delegates to", "In-process async call")
    Rel(rctrl, rsvc, "Invokes session ops", "In-process async call")
    Rel(rsvc, dedup, "Checks fingerprint", "In-process call before session creation")
    Rel(rsvc, proc, "Processes answers", "In-process call on each save")
    Rel(rsvc, gdpr, "Filters PII", "In-process call before persistence")
    Rel(rsvc, rrepo, "Persists session", "Motor async / MongoDB Wire Protocol")
    Rel(rsvc, kinesis, "Streams completion event", "boto3 PutRecord / HTTPS")
    Rel(rsvc, ws, "Notifies live clients", "In-process broadcast")
    Rel(dedup, redis2, "Reads/writes fingerprint set", "Redis SADD / SISMEMBER")
    Rel(rrepo, mongo, "Document read/write", "TLS / MongoDB Wire Protocol")
    Rel(kinesis, kstream, "Publishes records", "AWS SDK / HTTPS")
    Rel(ws, redis2, "Stores connection state", "Redis HSET / HDEL")
```

---

## Distribution Service — C4 Component Diagram

The Distribution Service manages campaign creation, audience targeting, and the bulk delivery
of survey invitations via email and SMS. All delivery work is performed asynchronously by
Celery workers to avoid blocking the API.

```mermaid
C4Component
    title Component Diagram - Distribution Service

    Person(marketer, "Workspace Admin", "Creates campaigns and sends survey invitations")

    Container_Boundary(dist_svc, "Distribution Service (FastAPI + Celery / Python 3.11)") {
        Component(dctr, "CampaignController", "FastAPI APIRouter + Class", "HTTP handlers for campaign CRUD, schedule, send-now, pause, cancel operations")
        Component(csvc, "CampaignService", "Python Async Class", "Campaign lifecycle state machine; audience snapshot locking; Celery task dispatch")
        Component(email_wkr, "EmailCampaignWorker", "Celery Task", "Processes email batch: iterates audience chunk, renders template, sends via SendGrid SDK")
        Component(sms_wkr, "SMSCampaignWorker", "Celery Task", "Processes SMS batch: iterates audience chunk, formats message, sends via Twilio SDK")
        Component(audience, "AudienceSelector", "Python Class", "Builds filtered SQLAlchemy query from audience segment definition and applies exclusion rules")
        Component(unsub, "UnsubscribeManager", "Python Class", "Maintains global and per-survey unsubscribe lists; enforced at row-by-row dispatch time")
        Component(qr, "QRCodeGenerator", "Python Class", "Generates QR code PNG for survey sharing URL; uploads image to S3 and returns CDN URL")
        Component(crepo, "ContactRepository", "async SQLAlchemy", "PostgreSQL CRUD for contacts, audience_lists, audience_contacts, and unsubscribe_entries tables")
    }

    System_Ext(sg, "SendGrid API", "Transactional email delivery provider with delivery webhooks")
    System_Ext(twilio, "Twilio API", "SMS delivery provider with delivery status callbacks")
    System_Ext(celery_redis, "Redis 7 (Celery Broker)", "Message broker for Celery task queue and result backend")
    System_Ext(pg3, "PostgreSQL 15 (AWS RDS)", "Contact and campaign relational data store")
    System_Ext(s3, "AWS S3", "Object storage for QR code images and CSV audience imports")

    Rel(marketer, dctr, "Manages campaigns", "HTTPS / REST JSON")
    Rel(dctr, csvc, "Delegates to", "In-process async call")
    Rel(csvc, audience, "Builds audience query", "In-process call")
    Rel(csvc, email_wkr, "Enqueues email task", "Celery apply_async")
    Rel(csvc, sms_wkr, "Enqueues SMS task", "Celery apply_async")
    Rel(csvc, qr, "Requests QR code", "In-process call on campaign create")
    Rel(email_wkr, unsub, "Checks unsubscribe status", "In-process call per contact")
    Rel(email_wkr, sg, "Delivers email", "SendGrid REST API / HTTPS")
    Rel(sms_wkr, unsub, "Checks unsubscribe status", "In-process call per contact")
    Rel(sms_wkr, twilio, "Delivers SMS", "Twilio REST API / HTTPS")
    Rel(audience, crepo, "Queries contacts", "async SQLAlchemy / psycopg3")
    Rel(unsub, crepo, "Reads unsubscribe list", "async SQLAlchemy / psycopg3")
    Rel(qr, s3, "Uploads QR image", "boto3 S3 PutObject / HTTPS")
    Rel(email_wkr, celery_redis, "Task queue", "Redis LPUSH / BRPOP")
    Rel(sms_wkr, celery_redis, "Task queue", "Redis LPUSH / BRPOP")
    Rel(crepo, pg3, "SQL read/write", "TLS / async psycopg3")
```

---

## Analytics Service — C4 Component Diagram

The Analytics Service provides on-demand metric computation, pre-computed dashboard summaries,
cross-tabulation, and real-time WebSocket streaming. It reads from DynamoDB (written by the
Kinesis → Lambda pipeline) and Redis (short-TTL metric cache).

```mermaid
C4Component
    title Component Diagram - Analytics Service

    Person(analyst, "Workspace Admin / Analyst", "Views survey analytics, exports reports")

    Container_Boundary(anl_svc, "Analytics Service (FastAPI / Python 3.11)") {
        Component(arouter, "AnalyticsRouter", "FastAPI APIRouter", "HTTP and WebSocket routes for summary, NPS, CSAT, trend, crosstab, and live-stream endpoints")
        Component(actrl, "AnalyticsController", "Python Class", "Routes analytics queries to appropriate engine; enforces survey ownership authorization")
        Component(aqs, "AnalyticsQueryService", "Python Async Class", "Orchestrates metric computation: cache-first strategy with DynamoDB fallback")
        Component(nps, "NPSEngine", "Python Class", "Computes Net Promoter Score: percentage of promoters (9-10) minus detractors (0-6)")
        Component(csat, "CSATEngine", "Python Class", "Computes Customer Satisfaction Score: satisfied responses divided by total responses")
        Component(sentiment, "SentimentService", "Python Class", "Invokes AWS Comprehend for open-text sentiment scoring; caches results per response batch")
        Component(crosstab, "CrossTabEngine", "Python Class + NumPy", "Builds cross-tabulation matrices segmented by answer values; supports chi-square significance testing")
        Component(mcache, "MetricsCacheService", "aioredis Client", "Reads and writes pre-computed metrics with 5-minute TTL; cache key includes survey_id and metric type")
        Component(dynamo, "DynamoDBReader", "boto3 DynamoDB Client", "Reads aggregated metric records written by the Kinesis Lambda aggregation function")
    }

    System_Ext(ddb, "DynamoDB", "NoSQL store for aggregated analytics metrics written by Lambda pipeline")
    System_Ext(redis3, "Redis 7 (ElastiCache)", "Short-TTL metric cache; WebSocket connection registry for live analytics")
    System_Ext(comprehend, "AWS Comprehend", "Managed NLP service for sentiment analysis of open-text responses")

    Rel(analyst, arouter, "Queries analytics", "HTTPS / REST JSON + WebSocket")
    Rel(arouter, actrl, "Delegates to", "In-process async call")
    Rel(actrl, aqs, "Invokes query", "In-process async call")
    Rel(aqs, mcache, "Cache-first read", "Redis GET / SETEX")
    Rel(aqs, dynamo, "Fallback read", "boto3 GetItem / Query")
    Rel(aqs, nps, "Computes NPS", "In-process call with score array")
    Rel(aqs, csat, "Computes CSAT", "In-process call with rating array")
    Rel(aqs, sentiment, "Analyzes open text", "In-process call per batch")
    Rel(aqs, crosstab, "Builds cross-tab matrix", "In-process call with segment params")
    Rel(sentiment, comprehend, "NLP inference", "AWS SDK / HTTPS")
    Rel(mcache, redis3, "Cache read/write", "Redis TCP / aioredis")
    Rel(dynamo, ddb, "Table scan/query", "AWS SDK / HTTPS")
```

---

## Component Descriptions

### Survey Service

| Component | Responsibility | Technology | Interface |
|---|---|---|---|
| `SurveyRouter` | HTTP routing and Pydantic v2 validation | FastAPI `APIRouter` | HTTP endpoints |
| `SurveyController` | Request/response translation and error mapping | Python class | Called by router |
| `SurveyService` | Survey lifecycle state machine, CRUD orchestration | Python async class | Called by controller |
| `QuestionService` | Question CRUD, ordering, type validation | Python async class | Called by controller |
| `LogicValidator` | Branch rule consistency and reference validation | Python dataclass | Called by services |
| `VersionManager` | Immutable survey snapshots on publish | Python class | Called by `SurveyService` |
| `SurveyRepository` | PostgreSQL survey table operations | async SQLAlchemy | Called by `SurveyService` |
| `QuestionRepository` | PostgreSQL question table operations | async SQLAlchemy | Called by `QuestionService` |
| `CacheManager` | Redis TTL cache for survey definitions | `aioredis` | Called by `SurveyService` |
| `EventPublisher` | Domain event publishing to Redis Streams | `aioredis` XADD | Called by `SurveyService` |

### Response Service

| Component | Responsibility | Technology | Interface |
|---|---|---|---|
| `ResponseRouter` | Session and answer HTTP routes | FastAPI `APIRouter` | HTTP endpoints |
| `ResponseController` | Session token issuance and HTTP translation | Python class | Called by router |
| `ResponseService` | Session state machine orchestration | Python async class | Called by controller |
| `DeduplicationEngine` | IP + fingerprint one-response enforcement | Python class + Redis | Called by `ResponseService` |
| `AnswerProcessor` | Raw answer coercion and schema validation | Python class | Called by `ResponseService` |
| `GDPRFilter` | PII field masking before storage | Python class | Called by `ResponseService` |
| `ResponseRepository` | MongoDB response document persistence | Motor async driver | Called by `ResponseService` |
| `KinesisProducer` | Completed response streaming to Kinesis | boto3 | Called by `ResponseService` |
| `WebSocketManager` | Real-time analytics WebSocket broadcast | FastAPI WebSocket | Called by `ResponseService` |

### Distribution Service

| Component | Responsibility | Technology | Interface |
|---|---|---|---|
| `CampaignController` | Campaign HTTP CRUD and action routes | FastAPI + Python class | HTTP endpoints |
| `CampaignService` | Campaign lifecycle state machine | Python async class | Called by controller |
| `EmailCampaignWorker` | Async email batch delivery | Celery task + SendGrid | Celery queue |
| `SMSCampaignWorker` | Async SMS batch delivery | Celery task + Twilio | Celery queue |
| `AudienceSelector` | Segment-based contact query builder | SQLAlchemy query | Called by `CampaignService` |
| `UnsubscribeManager` | Opt-out enforcement at send time | Python class | Called by delivery workers |
| `QRCodeGenerator` | Survey QR code generation and S3 upload | `qrcode` + boto3 | Called by `CampaignService` |
| `ContactRepository` | PostgreSQL contact and audience CRUD | async SQLAlchemy | Called by multiple components |

### Analytics Service

| Component | Responsibility | Technology | Interface |
|---|---|---|---|
| `AnalyticsRouter` | HTTP and WebSocket analytics routes | FastAPI `APIRouter` | HTTP + WS endpoints |
| `AnalyticsController` | Query routing and authorization | Python class | Called by router |
| `AnalyticsQueryService` | Cache-first metric orchestration | Python async class | Called by controller |
| `NPSEngine` | Net Promoter Score computation | Python | Called by `AnalyticsQueryService` |
| `CSATEngine` | Customer Satisfaction Score computation | Python | Called by `AnalyticsQueryService` |
| `SentimentService` | Open-text sentiment analysis via AWS Comprehend | boto3 | Called by `AnalyticsQueryService` |
| `CrossTabEngine` | Cross-tabulation matrix generation | Python + NumPy | Called by `AnalyticsQueryService` |
| `MetricsCacheService` | 5-minute TTL pre-computed metric cache | `aioredis` | Called by `AnalyticsQueryService` |
| `DynamoDBReader` | Reads Lambda-aggregated metrics from DynamoDB | boto3 | Called by `AnalyticsQueryService` |

---

## Inter-Service Communication

Services communicate via two mechanisms: **synchronous REST** (for user-facing request/response
flows) and **asynchronous events** (for decoupled state propagation).

### Synchronous REST Calls

| Caller | Callee | Endpoint | Trigger |
|---|---|---|---|
| Response Service | Survey Service | `GET /internal/surveys/{id}` | Validate survey is ACTIVE before accepting session |
| Distribution Service | Survey Service | `GET /internal/surveys/{id}/share-url` | Retrieve embeddable survey link for campaign |
| Analytics Service | Response Service | `GET /internal/surveys/{id}/responses/export` | Bulk response export for heavy cross-tab queries |

### Asynchronous Event Bus (Redis Streams)

| Producer | Stream Key | Event Type | Consumers |
|---|---|---|---|
| Survey Service | `survey.events` | `survey.published`, `survey.closed`, `survey.archived` | Analytics Service, Notification Service |
| Response Service | `response.events` | `response.completed`, `session.expired` | Analytics Service, Notification Service |
| Distribution Service | `campaign.events` | `campaign.sent`, `campaign.failed` | Notification Service, Billing Service |

### Analytics Pipeline (Kinesis → Lambda → DynamoDB)

The Response Service publishes each completed response to **AWS Kinesis Data Streams**. An
**AWS Lambda** function (triggered by Kinesis) aggregates metrics per survey in real-time and
writes results to **DynamoDB**. The Analytics Service reads these pre-aggregated records to
serve low-latency dashboard queries, bypassing full MongoDB scans.

---

## Operational Policy Addendum

### OPA-1: Service Boundary Enforcement

No service may connect to another service's data store directly. All cross-service data access
goes through the owning service's internal REST API or via the shared Redis Streams event bus.
Violations are detectable via network policy in AWS ECS and enforced as merge-blocking review
findings.

### OPA-2: Component Versioning and Backwards Compatibility

Internal REST API paths prefixed with `/internal/` are not subject to the public API versioning
contract but must maintain backwards-compatible request/response schemas for at least one release
cycle. Any breaking change to an internal endpoint requires simultaneous deployment of all
services that consume it (coordinated release).

### OPA-3: Health and Readiness Probes

Each service exposes `GET /health/live` (liveness: is the process running?) and
`GET /health/ready` (readiness: can it serve traffic? — checks DB connection, Redis ping, and
queue worker status). ECS Fargate uses these probes for zero-downtime rolling deployments and
automatic task replacement on failure.

### OPA-4: Secret and Configuration Management

All service credentials (database passwords, AWS keys, SendGrid API key, Twilio auth token,
JWT signing secret) are injected as environment variables from AWS Secrets Manager at container
start time. No secrets are baked into container images. Components access configuration via a
central `Settings` Pydantic model (pydantic-settings) that validates all required variables at
startup, causing the container to fail fast with a descriptive error if any credential is missing.
