# Messaging and Notification Platform

> **Implementation-ready design documentation** for a multi-tenant, multi-channel notification platform supporting transactional, operational, and campaign traffic at scale. Built for teams that need to deliver billions of notifications across email, SMS, push, in-app, webhook, WhatsApp, and Slack with provider failover, template governance, opt-out compliance, and end-to-end observability.

---

## Project Overview

The **Messaging and Notification Platform** is an enterprise-grade, horizontally scalable notification engine that provides a single, unified API surface for all outbound communication channels. It abstracts the complexity of managing multiple third-party providers, enforces regulatory compliance (GDPR, CAN-SPAM, TCPA), and gives product teams a self-service interface for designing, approving, and sending templated messages at any scale.

### Core Design Goals

| Goal | Description |
|---|---|
| **Channel unification** | One API for email, SMS, push, in-app, webhook, WhatsApp, and Slack |
| **Tenant isolation** | Strict data partitioning — one tenant's traffic cannot affect another |
| **Delivery reliability** | At-least-once semantics with idempotency guarantees and DLQ recovery |
| **Regulatory compliance** | GDPR erasure, TCPA consent, CAN-SPAM opt-out enforced at platform level |
| **Operational transparency** | Per-message traceability from API call to provider ACK or final failure |
| **Provider resilience** | Circuit-breaker failover across multiple SMS, email, and push providers |
| **Template governance** | Versioned templates with dual-approval workflow for regulated content |

### Who Is This For?

- **Platform engineers** building or extending a notification infrastructure service
- **Product engineers** integrating notification triggers into application flows
- **DevOps / SRE teams** operating and monitoring large-scale message dispatch
- **Compliance and legal teams** auditing consent, suppression, and PII handling
- **Technical architects** evaluating design decisions before committing to implementation

---

## Key Features

### Multi-Channel Delivery
- **Email** – transactional and marketing email via SES, SendGrid, Mailgun, Postmark with DKIM/SPF/DMARC enforcement
- **SMS** – domestic and international delivery via Twilio, Vonage, AWS SNS with carrier-level error classification
- **Push Notifications** – iOS (APNs), Android (FCM), Web Push (VAPID) with rich payload and collapse-key support
- **In-App Notifications** – real-time delivery via WebSocket and SSE; persistent notification centre with read/unread state
- **Webhooks** – HTTPS POST delivery to tenant-configured endpoints with HMAC-SHA256 signature and retry logic
- **WhatsApp** – Business API integration via Meta Cloud API and approved message templates
- **Slack** – workspace and channel delivery via OAuth Bot tokens and Incoming Webhooks

### Priority Tiers and SLOs
- **P0 Transactional** – OTP, password reset, security alerts; enqueue < 1 s, provider handoff p95 < 5 s, 99.95% availability
- **P1 Operational** – account alerts, statement ready, shipping updates; enqueue < 5 s, handoff p95 < 30 s, 99.9% availability
- **P2 Promotional** – campaign blasts, newsletters; enqueue < 30 s, handoff p95 < 5 min, 99.5% availability

### Template Engine
- Handlebars/Mustache-compatible variable substitution with nested object support
- Versioned, immutable published templates — sends always pin an explicit version
- Dual-approval workflow for regulated or financial content templates
- Locale-aware rendering with fallback chains (e.g., `pt-BR → pt → en`)
- Safe HTML sanitisation and plain-text auto-generation for email
- Template preview API with mock variables for QA and designer review

### Provider Management and Failover
- Weighted primary/secondary routing per channel and geography
- Circuit breaker with half-open probing and gradual traffic ramp-back (10 % → 25 % → 50 % → 100 %)
- Active health probes plus rolling error-rate window for real-time provider scoring
- Provider spend and rate-limit tracking to prevent quota exhaustion

### Scheduling and Campaign Engine
- Send-at scheduling with timezone-aware delivery windows
- Recurring schedule support (cron-style) for digest and reminder notifications
- Audience segmentation with dynamic filter criteria evaluated at dispatch time
- Campaign throttling, send-time optimisation, and A/B split testing
- Drip sequence builder with event-triggered branching

### Opt-Out and Compliance
- Per-channel, per-category suppression lists evaluated on every send
- Double opt-in workflow for email marketing channels
- Unsubscribe link injection and one-click List-Unsubscribe header (RFC 8058)
- GDPR erasure: soft delete contact data and tokenize PII in all logs
- TCPA express written consent store with timestamp and proof-of-consent document
- CAN-SPAM physical address and opt-out mechanism enforcement

### Analytics and Reporting
- Real-time delivery funnel: sent → delivered → opened → clicked → converted
- Bounce and complaint processing with automatic suppression trigger
- Per-tenant, per-campaign, per-channel dashboards with hourly granularity
- Provider comparison reports: delivery rate, latency, cost per message
- SLO compliance reports with breach alerting

### Developer Experience
- RESTful API with OpenAPI 3.1 specification and generated SDKs (TypeScript, Python, Go, Java)
- Idempotency keys on all mutation endpoints to prevent duplicate sends
- Webhook event streams for real-time delivery status integration
- Tenant self-service portal for provider credential management and template authoring
- Sandbox mode with mock providers for integration testing without live sends

---

## Documentation Structure

Project root artifact: [`traceability-matrix.md`](./traceability-matrix.md) provides cross-phase requirement-to-implementation linkage.


### Phase 1 — Requirements

| File | Description |
|---|---|
| [requirements/requirements.md](./requirements/requirements.md) | Full functional and non-functional requirements with 40+ FRs grouped by module, NFR targets, MVP scope, constraints, and glossary |
| [requirements/user-stories.md](./requirements/user-stories.md) | 40+ user stories across 8 epics with acceptance criteria, story points, and summary table |

### Phase 2 — Analysis

| File | Description |
|---|---|
| [analysis/use-case-diagram.md](./analysis/use-case-diagram.md) | UML use-case diagram covering all primary actors and system interactions |
| [analysis/use-case-descriptions.md](./analysis/use-case-descriptions.md) | Detailed use-case descriptions with pre/post conditions and main/alternate flows |
| [analysis/activity-diagrams.md](./analysis/activity-diagrams.md) | Activity diagrams for send flow, template approval, opt-out processing, and campaign dispatch |
| [analysis/swimlane-diagrams.md](./analysis/swimlane-diagrams.md) | Cross-team swimlane diagrams for escalation, DLQ replay, and provider onboarding |
| [analysis/system-context-diagram.md](./analysis/system-context-diagram.md) | System boundary diagram showing external actors, providers, and integration points |
| [analysis/data-dictionary.md](./analysis/data-dictionary.md) | Canonical field definitions for all domain entities with type, constraints, and examples |
| [analysis/business-rules.md](./analysis/business-rules.md) | Executable business rules for consent enforcement, idempotency, suppression, and routing |
| [analysis/event-catalog.md](./analysis/event-catalog.md) | Full event catalog with event names, schemas, producers, consumers, and retention policies |

### Phase 3 — High-Level Design

| File | Description |
|---|---|
| [high-level-design/architecture-diagram.md](./high-level-design/architecture-diagram.md) | Service topology and component interaction diagram with technology annotations |
| [high-level-design/c4-diagrams.md](./high-level-design/c4-diagrams.md) | C4 Level 1 (System Context) and Level 2 (Container) diagrams |
| [high-level-design/domain-model.md](./high-level-design/domain-model.md) | Domain model with aggregates, entities, value objects, and invariants |
| [high-level-design/data-flow-diagrams.md](./high-level-design/data-flow-diagrams.md) | DFD Level 0 and Level 1 showing data flows between processes and stores |
| [high-level-design/system-sequence-diagrams.md](./high-level-design/system-sequence-diagrams.md) | System-level sequence diagrams for transactional send, campaign dispatch, and opt-out |

### Phase 4 — Detailed Design

| File | Description |
|---|---|
| [detailed-design/api-design.md](./detailed-design/api-design.md) | Full REST API specification with endpoint definitions, request/response schemas, and error codes |
| [detailed-design/erd-database-schema.md](./detailed-design/erd-database-schema.md) | Entity-relationship diagram and full DDL for all tables with indexes and partitioning strategy |
| [detailed-design/class-diagrams.md](./detailed-design/class-diagrams.md) | UML class diagrams for core domain objects, repositories, and service interfaces |
| [detailed-design/component-diagrams.md](./detailed-design/component-diagrams.md) | Internal component breakdown for each microservice with interfaces and dependencies |
| [detailed-design/sequence-diagrams.md](./detailed-design/sequence-diagrams.md) | Detailed sequence diagrams for all critical paths including failover, retry, and DLQ flows |
| [detailed-design/state-machine-diagrams.md](./detailed-design/state-machine-diagrams.md) | State machines for message lifecycle, template lifecycle, provider circuit breaker, and campaign states |
| [detailed-design/c4-component-diagram.md](./detailed-design/c4-component-diagram.md) | C4 Level 3 component diagrams for the Notification Engine and Template Service |
| [detailed-design/delivery-orchestration-and-template-system.md](./detailed-design/delivery-orchestration-and-template-system.md) | Deep-dive on dispatch worker design, template rendering pipeline, and provider adapter pattern |

### Phase 5 — Infrastructure

| File | Description |
|---|---|
| [infrastructure/cloud-architecture.md](./infrastructure/cloud-architecture.md) | Cloud-native architecture with AWS/GCP service mapping, IAM policy model, and cost estimates |
| [infrastructure/deployment-diagram.md](./infrastructure/deployment-diagram.md) | Kubernetes deployment topology with namespace layout, resource quotas, and HPA configuration |
| [infrastructure/network-infrastructure.md](./infrastructure/network-infrastructure.md) | VPC design, subnet layout, security groups, WAF rules, and private link configurations |

### Phase 6 — Implementation

| File | Description |
|---|---|
| [implementation/implementation-guidelines.md](./implementation/implementation-guidelines.md) | Coding standards, service bootstrapping guide, dependency injection patterns, and testing strategy |
| [implementation/backend-status-matrix.md](./implementation/backend-status-matrix.md) | Feature-by-feature readiness matrix tracking design, implementation, and test status |
| [implementation/c4-code-diagram.md](./implementation/c4-code-diagram.md) | C4 Level 4 code-level diagrams for critical modules |

### Phase 7 — Edge Cases

| File | Description |
|---|---|
| [edge-cases/README.md](./edge-cases/README.md) | Overview of all documented edge cases with severity ratings and mitigation status |
| [edge-cases/provider-failover.md](./edge-cases/provider-failover.md) | Detailed failover scenarios: circuit open, half-open probing, provider degradation, split-brain |
| [edge-cases/opt-out-compliance.md](./edge-cases/opt-out-compliance.md) | Edge cases for concurrent opt-out, in-flight message interception, and cross-channel suppression |
| [edge-cases/rate-limiting.md](./edge-cases/rate-limiting.md) | Tenant rate limiting, provider quota exhaustion, burst handling, and backpressure propagation |
| [edge-cases/delayed-deduplicated-delivery.md](./edge-cases/delayed-deduplicated-delivery.md) | Deduplication window edge cases, clock skew, and idempotency key collision scenarios |
| [edge-cases/api-and-ui.md](./edge-cases/api-and-ui.md) | API edge cases: malformed payloads, oversized templates, concurrent mutations, and timeout handling |
| [edge-cases/operations.md](./edge-cases/operations.md) | Operational edge cases: DLQ overflow, schema migration during live traffic, and key rotation |
| [edge-cases/security-and-compliance.md](./edge-cases/security-and-compliance.md) | Security edge cases: SSRF via webhook, credential leakage, PII in logs, and tenant data isolation |

---

## Getting Started

- Review [`traceability-matrix.md`](./traceability-matrix.md) first to navigate requirement-to-implementation coverage across phases.
### Architecture Decisions

Before diving into implementation, understand these foundational decisions:

1. **Event-driven core** – The platform uses an event streaming backbone (Kafka or AWS Kinesis) to decouple ingestion from dispatch. This enables independent scaling of the API layer and worker fleet, and provides a durable replay capability for DLQ recovery.

2. **Microservice decomposition** – Core services are decomposed by domain: Notification API, Template Service, Contact & Subscription Service, Delivery Orchestrator, Provider Adapter Fleet, Analytics Ingestion, and Compliance/Audit Service. Each owns its data store.

3. **Provider adapter pattern** – All third-party providers are wrapped behind a common `ChannelProvider` interface. Swapping or adding providers requires no change to the dispatch core.

4. **Shared-nothing tenancy** – Tenant data is isolated by `tenant_id` partition keys at the database and queue level. No cross-tenant data access is possible through the API.

5. **Compliance first** – Consent checks and suppression lookups happen synchronously before any message is queued. There is no "bypass compliance for performance" fast path.

### Technology Stack

| Layer | Technology | Rationale |
|---|---|---|
| **API Gateway** | Kong / AWS API Gateway | Rate limiting, auth, request routing at edge |
| **Backend Services** | Node.js (TypeScript) / Go | TypeScript for business logic, Go for high-throughput workers |
| **Message Broker** | Apache Kafka (or AWS Kinesis) | Durable, ordered, replayable event streaming |
| **Primary Database** | PostgreSQL (RDS Aurora) | Relational integrity for messages, templates, contacts |
| **Cache** | Redis (ElastiCache) | Idempotency key store, consent cache, rate limit counters |
| **Search / Analytics** | Elasticsearch / OpenSearch | Full-text template search, delivery analytics queries |
| **Object Storage** | S3 | Audit log archival, email attachment storage |
| **Push Provider** | FCM + APNs + Web Push | Native mobile and browser push delivery |
| **Email Providers** | AWS SES, SendGrid, Mailgun | Multi-provider email with automatic failover |
| **SMS Providers** | Twilio, Vonage, AWS SNS | Multi-provider SMS with geographic routing |
| **Container Runtime** | Kubernetes (EKS / GKE) | Horizontal scaling, rolling deployments, namespace isolation |
| **Service Mesh** | Istio / Linkerd | mTLS, traffic shaping, circuit breaking at infra level |
| **Observability** | OpenTelemetry + Jaeger + Prometheus + Grafana | Distributed tracing, metrics, alerting |
| **Secrets Management** | AWS Secrets Manager / HashiCorp Vault | Provider API keys, webhook signing secrets |
| **CI/CD** | GitHub Actions + ArgoCD | Automated testing, container builds, GitOps deployments |

### System Requirements

| Requirement | Target |
|---|---|
| **Throughput** | 50,000 messages/second peak (aggregated across all channels) |
| **P0 Latency** | API to provider handoff p95 < 5 s for transactional traffic |
| **Availability** | 99.95% for transactional tier; 99.9% for operational tier |
| **Message Durability** | Zero acknowledged-message loss under single-AZ failure |
| **Tenant Scale** | Support 10,000+ active tenants with strict isolation |
| **Template Volume** | 1 million+ published template versions |
| **Contact Scale** | 500 million+ contact records with sub-10 ms consent lookup |
| **Audit Retention** | 90-day hot, 1-year warm, 7-year cold for compliance evidence |
| **RTO** | < 5 minutes for transactional tier on provider failover |
| **RPO** | Zero for message metadata (synchronous write); < 1 s for event stream |

### Recommended Reading Order

Follow this sequence for a new team member onboarding:

```
1. requirements/requirements.md          ← understand what the system must do
2. requirements/user-stories.md          ← understand user goals and acceptance criteria
3. analysis/business-rules.md            ← understand the non-negotiable invariants
4. analysis/event-catalog.md             ← understand the event-driven contract
5. high-level-design/architecture-diagram.md  ← understand service topology
6. high-level-design/domain-model.md     ← understand the data model
7. detailed-design/api-design.md         ← understand the external API contract
8. detailed-design/erd-database-schema.md     ← understand persistence design
9. detailed-design/delivery-orchestration-and-template-system.md  ← dispatch internals
10. infrastructure/cloud-architecture.md  ← understand deployment environment
11. implementation/implementation-guidelines.md  ← start coding
12. edge-cases/                           ← handle the hard cases
```

---

## Documentation Status

- ✅ Traceability coverage is available via [`traceability-matrix.md`](./traceability-matrix.md).
| Phase | Folder | Files | Status | Coverage Notes |
|---|---|---|---|---|
| 1 – Requirements | `requirements/` | 2 | ✅ Complete | FR/NFR, 40+ requirements, user stories with ACs |
| 2 – Analysis | `analysis/` | 8 | ✅ Complete | Use cases, business rules, event catalog, data dictionary |
| 3 – High-Level Design | `high-level-design/` | 5 | ✅ Complete | Architecture, domain model, C4 L1/L2, DFD, sequence diagrams |
| 4 – Detailed Design | `detailed-design/` | 8 | ✅ Complete | API spec, ERD, class/component diagrams, state machines |
| 5 – Infrastructure | `infrastructure/` | 3 | ✅ Complete | Cloud architecture, Kubernetes deployment, network design |
| 6 – Implementation | `implementation/` | 3 | ✅ Complete | Guidelines, readiness matrix, C4 L4 code diagrams |
| 7 – Edge Cases | `edge-cases/` | 8 | ✅ Complete | Failover, opt-out, rate limiting, security, operations |

---

## Delivery Baseline Reference

### Message Priority Tiers

| Tier | Label | Examples | Enqueue SLO | Handoff SLO p95 | Availability SLO |
|---|---|---|---|---|---|
| P0 | Transactional | OTP, password reset, fraud alert | < 1 s | < 5 s | 99.95% |
| P1 | Operational | Statement ready, shipment update, alert | < 5 s | < 30 s | 99.9% |
| P2 | Promotional | Campaign blast, newsletter, re-engagement | < 30 s | < 5 min | 99.5% |

### Message Status Lifecycle

```
ACCEPTED → QUEUED → DISPATCHING → PROVIDER_ACCEPTED → DELIVERED
                                                     → FAILED → (retry) → DELIVERED
                                                                         → DLQ
                                                     → EXPIRED
```

### Idempotency Contract

```
idempotency_key = SHA-256(tenant_id + ":" + message_type + ":" + recipient_id + ":" + template_id + ":" + template_version + ":" + nonce)
```
- Keys are stored in Redis with a 24-hour TTL for transactional, 72-hour for promotional
- Duplicate submissions within the window return `200 OK` with the cached response
- Keys are invalidated on explicit cancel or permanent failure

### Retry Policy

| Attempt | Delay | Max Total Time |
|---|---|---|
| 1st retry | 30 s + jitter | — |
| 2nd retry | 2 min + jitter | — |
| 3rd retry | 10 min + jitter | — |
| 4th retry | 30 min + jitter | — |
| 5th retry | 2 h + jitter | ~3 h from first attempt |
| Exhausted | → DLQ | — |

### Provider Circuit Breaker States

```
CLOSED (healthy) → OPEN (failing) → HALF-OPEN (probing) → CLOSED (recovered)
                                                         → OPEN (still failing)
```
- **Open trigger**: error rate > 10% over 60-second rolling window, or > 3 consecutive timeouts
- **Half-open probe**: 5% of traffic routed to provider every 30 seconds
- **Recovery ramp**: 5% → 10% → 25% → 50% → 100% over 10-minute windows with rollback guard

---

## Verification Checklist

- [ ] All API endpoints include `idempotency_key` and `correlation_id` parameters
- [ ] Consent and suppression checks are synchronous and block queuing
- [ ] Retryable vs non-retryable errors are explicitly classified per provider
- [ ] DLQ replay requires operator approval and produces audit events
- [ ] Provider failover defines trigger thresholds, failover action, and recovery criteria
- [ ] Template versioning prevents mutation of published versions
- [ ] Template approval workflow requires dual sign-off for regulated content
- [ ] All PII in logs is tokenized; message body is redacted unless under legal hold
- [ ] Compliance evidence is queryable by `message_id`, `correlation_id`, and `recipient_token`
- [ ] GDPR erasure deletes or tokenizes all contact PII within 72 hours of request
- [ ] Opt-out is honoured in < 10 seconds for transactional and < 24 hours for all channels
