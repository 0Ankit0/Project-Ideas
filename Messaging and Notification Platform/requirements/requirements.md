# Requirements — Messaging and Notification Platform

## Executive Summary

The Messaging and Notification Platform is a multi-tenant, multi-channel notification infrastructure that consolidates all outbound customer communication into a single, governed, and auditable system. It replaces ad-hoc, service-specific notification integrations with a platform that provides reliable delivery, regulatory compliance, provider redundancy, and full observability from a unified API surface.

The platform must support three traffic profiles — **transactional** (OTP, password reset, fraud alerts), **operational** (account updates, shipment notifications, reminders), and **promotional** (campaigns, newsletters, re-engagement) — each with independently enforced SLOs, queues, and compliance controls.

This document defines the complete functional and non-functional requirements, stakeholder goals, MVP scope, and a glossary of domain terms for implementation teams.

---

## Problem Statement

Modern product organisations face the following challenges in outbound notification:

1. **Fragmented integration landscape** – Multiple teams integrate directly with Twilio, SendGrid, FCM, and others, creating duplicated logic, inconsistent retry behaviour, and no shared suppression lists.
2. **Compliance gaps** – GDPR opt-out, TCPA consent, and CAN-SPAM obligations are implemented inconsistently or not at all, creating regulatory exposure.
3. **No provider resilience** – When a primary provider degrades, teams have no automatic failover. Incidents require manual re-routing and cause SLO breaches.
4. **Template chaos** – Message templates live in application code or unversioned databases, making it impossible to audit what was sent to whom and when.
5. **Poor observability** – No centralised view of delivery rates, bounces, or complaints across channels and tenants makes debugging delivery issues slow and expensive.
6. **No tenant isolation** – One tenant's campaign blast can starve another tenant's transactional traffic by competing on shared resources.

The platform addresses all of these problems with a purpose-built, event-driven notification engine.

---

## Stakeholder Analysis

| Stakeholder | Role | Primary Goals | Pain Points Addressed |
|---|---|---|---|
| **Product Engineer** | Integrates notifications into product features | Simple API, reliable delivery, minimal on-call burden | No need to manage provider SDKs or retry logic |
| **Notification Platform Team** | Owns and operates the platform | Reliability SLOs, operational efficiency, low incident rate | Centralised observability, provider health management |
| **Compliance Officer** | Ensures regulatory adherence | Provable consent records, opt-out enforcement, audit trails | Centralised suppression, GDPR erasure support, 7-year evidence |
| **Legal Counsel** | Manages regulatory risk | Defensible documentation of opt-in/opt-out events | Timestamped consent records with proof-of-consent artefacts |
| **Marketing Manager** | Runs promotional campaigns | High deliverability, A/B testing, segment targeting | Campaign engine with send-time optimisation and analytics |
| **SRE / DevOps** | Operates the infrastructure | High availability, observable failures, fast incident response | Per-message tracing, circuit breaker automation, DLQ tooling |
| **Data Privacy Officer** | Manages personal data governance | PII minimisation, erasure fulfilment, data residency | Tokenised PII logs, erasure workflow, regional data stores |
| **Finance / Billing Team** | Controls notification spend | Cost visibility, per-tenant attribution, budget controls | Provider spend tracking, per-tenant cost reporting |
| **Security Team** | Manages application security | No PII leakage, no SSRF, credential protection | Webhook signing, secret rotation, audit log immutability |
| **End User (Recipient)** | Receives notifications | Relevant, timely messages; easy opt-out | Preference centre, instant opt-out, channel selection |

---

## Functional Requirements

### FR-MSG: Message Sending

| ID | Title | Description | Priority | Dependencies |
|---|---|---|---|---|
| FR-MSG-01 | Single send API | The system SHALL expose a REST endpoint `POST /v1/messages` that accepts a tenant-scoped notification command including channel, recipient, template reference, variables, priority tier, and idempotency key. | High | — |
| FR-MSG-02 | Multi-channel dispatch | The system SHALL support dispatching a single logical message to one or more channels simultaneously (e.g., email + push) based on tenant configuration and contact preferences. | High | FR-MSG-01 |
| FR-MSG-03 | Idempotency enforcement | The system SHALL reject or de-duplicate any message submission that matches an existing idempotency key within the configured deduplication window (default 24 hours). Duplicate submissions MUST return `200 OK` with the original response. | High | FR-MSG-01 |
| FR-MSG-04 | Priority tier routing | The system SHALL route messages to the corresponding priority queue (P0/P1/P2) based on the `priority` field in the request. Each priority tier MUST have an independent worker pool and SLO. | High | FR-MSG-01 |
| FR-MSG-05 | Consent and suppression gate | The system SHALL evaluate consent status and suppression list membership synchronously before publishing a message to the dispatch queue. Messages for suppressed or non-consented recipients MUST be rejected with a `409 Conflict` response and an audit event. | High | FR-CNT-01 |
| FR-MSG-06 | Delivery status tracking | The system SHALL maintain a persistent status record for every accepted message covering the full lifecycle: `ACCEPTED → QUEUED → DISPATCHING → PROVIDER_ACCEPTED → DELIVERED / FAILED / EXPIRED`. Status transitions MUST be timestamped and queryable. | High | FR-MSG-01 |
| FR-MSG-07 | Delivery status query | The system SHALL expose `GET /v1/messages/{message_id}/status` returning the current status, all historical status transitions, provider message ID, and any error classification. | High | FR-MSG-06 |
| FR-MSG-08 | Batch message send | The system SHALL support a batch endpoint `POST /v1/messages/batch` accepting up to 1,000 message commands per request. Each command is processed independently; partial failure returns per-item status in the response. | Medium | FR-MSG-01 |
| FR-MSG-09 | Scheduled send | The system SHALL accept an optional `scheduled_at` ISO 8601 timestamp on any message send request and delay dispatch until that time, subject to a configurable maximum scheduling horizon (default 30 days). | Medium | FR-MSG-01 |
| FR-MSG-10 | Message cancellation | The system SHALL allow cancellation of a scheduled or queued message via `DELETE /v1/messages/{message_id}` provided the message has not yet reached `DISPATCHING` state. Cancellation MUST produce an audit event. | Medium | FR-MSG-06 |
| FR-MSG-11 | Retry on transient failure | The system SHALL automatically retry failed message dispatches for retryable error codes using capped exponential backoff with jitter. Non-retryable errors MUST skip retries and move directly to the DLQ. | High | FR-MSG-06 |
| FR-MSG-12 | Dead-letter queue | The system SHALL route messages that exhaust all retry attempts to a per-tenant DLQ, preserving the full envelope, error history, and trace identifiers for operator inspection and replay. | High | FR-MSG-11 |

---

### FR-TPL: Template Management

| ID | Title | Description | Priority | Dependencies |
|---|---|---|---|---|
| FR-TPL-01 | Template creation | The system SHALL allow authorised users to create message templates specifying channel, locale, subject (email), body (Handlebars syntax), and a variable schema defining required and optional substitution variables. | High | — |
| FR-TPL-02 | Template versioning | The system SHALL assign an immutable version number to each published template. Published templates MUST NOT be mutated. Edits create a new draft version. | High | FR-TPL-01 |
| FR-TPL-03 | Approval workflow | The system SHALL enforce a configurable approval workflow for templates before publication. Templates flagged as `regulated` MUST require dual approval (two distinct approvers with `template:approve` permission). | High | FR-TPL-01 |
| FR-TPL-04 | Template lifecycle | The system SHALL enforce the state machine: `DRAFT → REVIEW → APPROVED → PUBLISHED → DEPRECATED → RETIRED`. Transitions MUST be logged with actor, timestamp, and optional comment. | High | FR-TPL-01, FR-TPL-03 |
| FR-TPL-05 | Variable substitution | The system SHALL render templates at dispatch time by substituting variables from the message payload using Handlebars-compatible syntax. Missing required variables MUST cause the message to fail validation before queuing. | High | FR-TPL-01 |
| FR-TPL-06 | Locale and fallback | The system SHALL select the template locale matching the recipient's preferred language, falling back through a configured fallback chain (e.g., `pt-BR → pt → en`) if an exact locale match is unavailable. | Medium | FR-TPL-01 |
| FR-TPL-07 | HTML sanitisation | The system SHALL sanitise email HTML templates to strip disallowed tags and attributes before rendering, preventing XSS and malformed content delivery. | High | FR-TPL-05 |
| FR-TPL-08 | Template preview API | The system SHALL expose a preview endpoint `POST /v1/templates/{id}/preview` that renders the template with supplied mock variables and returns the rendered output without sending any message. | Medium | FR-TPL-05 |
| FR-TPL-09 | Template rollback | The system SHALL allow operators to republish a previous approved template version, making it the active version for new sends within 5 minutes of request. The rollback action MUST be logged and require `template:publish` permission. | Medium | FR-TPL-02 |
| FR-TPL-10 | Template search | The system SHALL provide a full-text search API over template names, tags, and body content, scoped to the requesting tenant. Results MUST include current lifecycle status and latest version number. | Low | FR-TPL-01 |

---

### FR-PRV: Provider Management

| ID | Title | Description | Priority | Dependencies |
|---|---|---|---|---|
| FR-PRV-01 | Provider configuration | The system SHALL allow platform operators to configure multiple providers per channel (email, SMS, push, WhatsApp) including API credentials, endpoint URLs, rate limits, and geographic scope. Credentials MUST be stored in a secrets manager, never in the database in plaintext. | High | — |
| FR-PRV-02 | Weighted routing | The system SHALL route outgoing messages across configured providers for a channel using a configurable weight (0–100) enabling primary/secondary and load-balanced configurations. | High | FR-PRV-01 |
| FR-PRV-03 | Provider health monitoring | The system SHALL continuously monitor provider health using active synthetic probes and a rolling error-rate window. Health scores MUST be updated at least every 30 seconds per provider. | High | FR-PRV-01 |
| FR-PRV-04 | Circuit breaker | The system SHALL implement a per-provider circuit breaker that opens when the error rate exceeds a configurable threshold (default 10% over 60-second window) or after 3 consecutive timeouts. Open circuits MUST divert traffic to the next healthy provider. | High | FR-PRV-03 |
| FR-PRV-05 | Automatic failover | The system SHALL automatically route messages to the standby provider when the primary provider's circuit is open, preserving the original idempotency key to prevent duplicate delivery when the primary recovers. | High | FR-PRV-04 |
| FR-PRV-06 | Gradual traffic recovery | The system SHALL ramp traffic back to a recovering provider in configurable increments (default: 5% → 10% → 25% → 50% → 100%) with a minimum dwell time at each step, rolling back immediately if error rate increases above threshold. | High | FR-PRV-04 |
| FR-PRV-07 | Provider callback ingestion | The system SHALL expose a webhook endpoint per provider for ingesting delivery receipt callbacks (delivery confirmations, bounces, complaints, opt-outs). Callbacks MUST be authenticated using provider-specific signing keys. | High | FR-PRV-01 |
| FR-PRV-08 | Provider spend tracking | The system SHALL track estimated cost per message dispatched per provider and expose per-tenant, per-channel cost reports. Budget alert thresholds SHALL be configurable per tenant. | Medium | FR-PRV-01 |
| FR-PRV-09 | Manual provider override | The system SHALL allow platform operators to manually force traffic to a specific provider for a tenant or globally, with an audit trail and automatic revert after a configurable duration. | Medium | FR-PRV-02 |

---

### FR-CNT: Contact & Subscription Management

| ID | Title | Description | Priority | Dependencies |
|---|---|---|---|---|
| FR-CNT-01 | Contact record | The system SHALL maintain a contact record per tenant per recipient containing channel addresses (email, phone, push tokens, device IDs), consent state per channel per category, and suppression flags. | High | — |
| FR-CNT-02 | Consent recording | The system SHALL record explicit consent events with actor, timestamp, consent method (double opt-in, API, import), source IP, and proof-of-consent document reference. Consent records MUST be immutable (append-only). | High | FR-CNT-01 |
| FR-CNT-03 | Opt-out processing | The system SHALL process opt-out requests received via API, unsubscribe link, SMS reply (STOP), email List-Unsubscribe header, or provider callback, and update the contact suppression state within the SLO (transactional-channel opt-out: < 10 s; all channels: < 24 h). | High | FR-CNT-01 |
| FR-CNT-04 | Suppression list management | The system SHALL maintain a per-tenant suppression list covering hard bounces, spam complaints, explicit opt-outs, and platform-level blocks. The list MUST be checked synchronously on every send. | High | FR-CNT-01 |
| FR-CNT-05 | Double opt-in workflow | The system SHALL support a configurable double opt-in flow for email marketing channels, sending a confirmation message and only recording active consent upon link click within the configured expiry window (default 48 hours). | Medium | FR-CNT-02, FR-MSG-01 |
| FR-CNT-06 | Preference centre API | The system SHALL expose an API for tenants to build a recipient preference centre, allowing recipients to select preferred channels and message categories, and update notification frequency preferences. | Medium | FR-CNT-01 |
| FR-CNT-07 | Contact import | The system SHALL support bulk contact import via CSV upload with configurable field mapping, deduplication by email/phone, consent status assignment, and an import job status tracking API. | Medium | FR-CNT-01 |
| FR-CNT-08 | GDPR erasure | The system SHALL support a GDPR erasure request that removes or permanently tokenises all PII associated with a contact record within 72 hours, including historical log entries, across all data stores, while preserving anonymised analytics data. | High | FR-CNT-01 |
| FR-CNT-09 | Contact segmentation | The system SHALL support dynamic segment definitions based on contact attributes, consent state, engagement history, and custom properties, evaluated at campaign dispatch time. | Medium | FR-CNT-01 |

---

### FR-CAM: Campaign Management

| ID | Title | Description | Priority | Dependencies |
|---|---|---|---|---|
| FR-CAM-01 | Campaign creation | The system SHALL allow authorised users to create a campaign specifying name, audience segment, template, channel, send schedule (immediate or scheduled), and per-campaign throttle rate (messages/second). | High | FR-TPL-01, FR-CNT-09 |
| FR-CAM-02 | Campaign dispatch | The system SHALL dispatch campaign messages by expanding the audience segment at send time, applying suppression checks for each recipient, and publishing each message to the P2 promotional queue at the configured throttle rate. | High | FR-CAM-01, FR-MSG-05 |
| FR-CAM-03 | Campaign pause and resume | The system SHALL allow operators to pause a running campaign, halting further dispatch, and resume it within 5 minutes. Pausing MUST not lose progress — already-dispatched messages are unaffected. | High | FR-CAM-02 |
| FR-CAM-04 | A/B split testing | The system SHALL support A/B/n testing within a campaign by distributing audience recipients across up to 5 variants with configurable percentage splits. A winning variant MAY be automatically promoted based on a configurable metric (open rate, click rate) after a test window. | Medium | FR-CAM-01 |
| FR-CAM-05 | Send-time optimisation | The system SHALL optionally delay per-recipient send time to the historically highest-engagement time window for that recipient based on prior engagement data, within a configurable delivery window (e.g., 9 am–8 pm local time). | Low | FR-CAM-01, FR-ANL-01 |
| FR-CAM-06 | Drip sequence | The system SHALL support multi-step drip sequences where subsequent messages are triggered by elapsed time or recipient events (opened, clicked, not opened) following an initial message. | Medium | FR-CAM-01, FR-MSG-09 |
| FR-CAM-07 | Campaign analytics | The system SHALL provide real-time and historical analytics per campaign including sent, delivered, opened, clicked, unsubscribed, bounced, and conversion counts with rates and funnel visualisation. | High | FR-CAM-02, FR-ANL-01 |

---

### FR-ANL: Analytics & Reporting

| ID | Title | Description | Priority | Dependencies |
|---|---|---|---|---|
| FR-ANL-01 | Delivery event ingestion | The system SHALL ingest delivery events (sent, delivered, failed, bounced, opened, clicked, unsubscribed, complained) from providers and in-app tracking pixels, normalising them to the platform event schema and storing them for analytics queries. | High | FR-PRV-07 |
| FR-ANL-02 | Real-time delivery dashboard | The system SHALL provide a per-tenant dashboard showing real-time delivery funnel metrics (sent, delivered, opened, clicked, bounced) with 1-minute refresh granularity and channel breakdown. | High | FR-ANL-01 |
| FR-ANL-03 | SLO compliance report | The system SHALL generate a daily SLO compliance report per tenant per priority tier showing p50/p95/p99 delivery latency, delivery success rate, and any SLO breach windows with root cause annotations. | High | FR-ANL-01 |
| FR-ANL-04 | Provider performance report | The system SHALL expose a provider performance comparison report showing delivery rate, average latency, bounce rate, complaint rate, and estimated cost per message for each configured provider over a configurable time window. | Medium | FR-ANL-01 |
| FR-ANL-05 | Engagement analytics export | The system SHALL support export of raw engagement event data (deduplicated and anonymised for GDPR compliance) in CSV and JSON Lines format for ingestion into tenant data warehouses. | Medium | FR-ANL-01 |
| FR-ANL-06 | Anomaly alerting | The system SHALL detect and alert on anomalous delivery metrics — including sudden spikes in bounce rate (> 5%), complaint rate (> 0.1%), or delivery latency (> 2x baseline) — via configured alert channels (email, PagerDuty, Slack) within 5 minutes of anomaly detection. | High | FR-ANL-01 |

---

### FR-WBH: Webhooks & Integrations

| ID | Title | Description | Priority | Dependencies |
|---|---|---|---|---|
| FR-WBH-01 | Outbound webhook delivery | The system SHALL support delivery of notification events to tenant-configured HTTPS webhook endpoints, signing each payload with HMAC-SHA256 using a tenant-managed signing secret. | High | — |
| FR-WBH-02 | Webhook retry | The system SHALL retry failed webhook deliveries (non-2xx responses or timeouts) using exponential backoff up to 5 attempts over 24 hours before marking the event as undeliverable. | High | FR-WBH-01 |
| FR-WBH-03 | Webhook event filtering | The system SHALL allow tenants to configure which event types are delivered to each webhook endpoint (e.g., `message.delivered`, `message.failed`, `contact.unsubscribed`) rather than receiving all events. | Medium | FR-WBH-01 |
| FR-WBH-04 | Webhook endpoint management | The system SHALL provide an API for tenants to create, update, test, and delete webhook endpoints. A test delivery SHALL send a synthetic event payload to verify endpoint reachability. | Medium | FR-WBH-01 |
| FR-WBH-05 | SSRF protection | The system SHALL validate webhook destination URLs against a blocklist of private IP ranges (RFC 1918, loopback, link-local) and cloud metadata endpoints to prevent SSRF attacks. | High | FR-WBH-01 |
| FR-WBH-06 | Slack integration | The system SHALL support native Slack delivery via Bot token or Incoming Webhook URL, with configurable channel routing and rich message block formatting. | Medium | — |
| FR-WBH-07 | WhatsApp integration | The system SHALL support WhatsApp Business API delivery via Meta Cloud API using pre-approved message templates, with delivery receipt tracking. | Medium | — |

---

### FR-SEC: Security & Compliance

| ID | Title | Description | Priority | Dependencies |
|---|---|---|---|---|
| FR-SEC-01 | Authentication and authorisation | The system SHALL authenticate all API requests using OAuth 2.0 Bearer tokens or API keys scoped to a tenant. Every endpoint SHALL enforce role-based access control (RBAC) with the minimum required permission. | High | — |
| FR-SEC-02 | Tenant data isolation | The system SHALL enforce strict data isolation so that no API request can read or modify data belonging to a different tenant. All database queries MUST include a `tenant_id` predicate enforced at the ORM/query layer. | High | FR-SEC-01 |
| FR-SEC-03 | PII tokenisation in logs | The system SHALL tokenise recipient PII (email address, phone number, name) in all log entries and audit events, storing only an opaque token that can be resolved to plaintext by authorised operators through a dedicated token resolution API. | High | — |
| FR-SEC-04 | Audit trail | The system SHALL produce an immutable audit log for all security-relevant events including: API key creation/revocation, consent events, suppression changes, template approval actions, DLQ replay operations, and operator administrative actions. Audit logs MUST be write-once and queryable by `tenant_id`, `actor_id`, `event_type`, and time range. | High | — |
| FR-SEC-05 | Encryption | The system SHALL encrypt all data in transit using TLS 1.2 or higher, and all data at rest using AES-256 with KMS-managed keys. Provider API credentials and webhook signing secrets MUST be stored in a dedicated secrets manager with key rotation support. | High | — |
| FR-SEC-06 | GDPR compliance controls | The system SHALL support: (a) data portability export of all contact data within 72 hours; (b) erasure of PII across all data stores within 72 hours; (c) data residency configuration to restrict processing to a specified geographic region. | High | FR-CNT-08 |
| FR-SEC-07 | Rate limiting | The system SHALL enforce per-tenant rate limits on the send API (configurable; default 1,000 req/s) and return `429 Too Many Requests` with a `Retry-After` header when limits are exceeded. | High | FR-MSG-01 |

---

## Non-Functional Requirements

### Performance

| NFR-ID | Metric | Target |
|---|---|---|
| NFR-PERF-01 | API ingestion throughput | 50,000 message commands/second aggregated across all tenants |
| NFR-PERF-02 | P0 transactional API latency | p95 < 200 ms for `POST /v1/messages` response |
| NFR-PERF-03 | P0 provider handoff latency | p95 < 5 s from API acceptance to provider acknowledgement |
| NFR-PERF-04 | P1 provider handoff latency | p95 < 30 s from API acceptance to provider acknowledgement |
| NFR-PERF-05 | Delivery status query | p95 < 50 ms for `GET /v1/messages/{id}/status` |
| NFR-PERF-06 | Consent lookup | < 10 ms for suppression and consent evaluation per recipient |
| NFR-PERF-07 | Template render | p99 < 20 ms for template variable substitution and HTML sanitisation |
| NFR-PERF-08 | Dashboard query | < 2 s for delivery funnel dashboard at hourly granularity |

### Scalability

| NFR-ID | Dimension | Target |
|---|---|---|
| NFR-SCAL-01 | Tenant count | 10,000+ active tenants with no cross-tenant performance impact |
| NFR-SCAL-02 | Contact records | 500 million contact records with < 10 ms p99 lookup |
| NFR-SCAL-03 | Template versions | 1 million+ published template versions |
| NFR-SCAL-04 | Concurrent campaigns | 1,000+ concurrent active campaigns without mutual interference |
| NFR-SCAL-05 | Horizontal scaling | All stateless services scale horizontally by adding pods/instances; no manual intervention required |
| NFR-SCAL-06 | Queue depth | System sustains stable throughput at 10 million queued messages |

### Availability and Reliability

| NFR-ID | Metric | Target |
|---|---|---|
| NFR-AVAIL-01 | Transactional tier availability | 99.95% monthly uptime (< 22 min/month downtime) |
| NFR-AVAIL-02 | Operational tier availability | 99.9% monthly uptime (< 44 min/month downtime) |
| NFR-AVAIL-03 | Promotional tier availability | 99.5% monthly uptime |
| NFR-AVAIL-04 | Message durability | Zero acknowledged-message loss under single-AZ failure |
| NFR-AVAIL-05 | Recovery time objective (RTO) | < 5 minutes for transactional tier on provider failover |
| NFR-AVAIL-06 | Recovery point objective (RPO) | Zero for message metadata (synchronous DB write); < 1 s for event stream |
| NFR-AVAIL-07 | Deployment | Zero-downtime rolling deployments; blue/green for major schema changes |

### Security

| NFR-ID | Requirement | Standard |
|---|---|---|
| NFR-SEC-01 | Transport security | TLS 1.2 minimum for all external and internal communication |
| NFR-SEC-02 | Data at rest | AES-256 encryption with AWS KMS or equivalent |
| NFR-SEC-03 | Authentication | OAuth 2.0 / API key with per-key scope and expiry |
| NFR-SEC-04 | Vulnerability management | SAST + DAST in CI pipeline; no high/critical CVEs in production images |
| NFR-SEC-05 | Penetration testing | Annual third-party pen test; findings remediated within SLA |
| NFR-SEC-06 | Secret rotation | Provider API keys and signing secrets rotatable without service restart |

### Compliance

| NFR-ID | Regulation | Requirement |
|---|---|---|
| NFR-COMP-01 | GDPR | Consent records, erasure fulfilment, data portability, DPA within EU |
| NFR-COMP-02 | CAN-SPAM | Physical address in commercial email, functional opt-out, no deceptive headers |
| NFR-COMP-03 | TCPA | Express written consent stored with proof before SMS marketing send |
| NFR-COMP-04 | CASL | Documented express or implied consent for Canadian recipients |
| NFR-COMP-05 | PCI DSS | No payment card data in message payloads; audit log access controls |

### Observability

| NFR-ID | Capability | Requirement |
|---|---|---|
| NFR-OBS-01 | Distributed tracing | Every message carries a `correlation_id` and `trace_id` propagated through all services |
| NFR-OBS-02 | Metrics | Cardinality-safe Prometheus metrics for delivery rate, latency, error rate per channel/provider/tier |
| NFR-OBS-03 | Logging | Structured JSON logs with severity, `correlation_id`, `tenant_id`, and no PII in default log level |
| NFR-OBS-04 | Alerting | PagerDuty / OpsGenie integration for SLO breach, provider circuit open, DLQ depth threshold |

---

## MVP vs Phase 2 vs Phase 3 Scope

| Feature Area | MVP (Phase 1) | Phase 2 | Phase 3 |
|---|---|---|---|
| **Channels** | Email, SMS, Push (FCM + APNs) | In-App, Webhook | WhatsApp, Slack |
| **Priority tiers** | P0, P1, P2 queues | — | — |
| **Template engine** | Basic variable substitution, versioning | Approval workflow, dual sign-off | A/B template testing |
| **Provider management** | Single provider per channel | Multi-provider weighted routing | Circuit breaker, auto-failover |
| **Consent/suppression** | Basic opt-out list, API | Double opt-in, preference centre | TCPA consent store, CASL |
| **Campaign engine** | Basic scheduled blast | Throttling, pause/resume | A/B split, send-time optimisation, drip |
| **Analytics** | Delivery status query | Real-time dashboard, bounce tracking | Provider comparison, SLO reports, export |
| **Integrations** | — | Webhook outbound events | Slack, WhatsApp, Zapier |
| **Security** | API key auth, TLS, tenant isolation | OAuth 2.0, RBAC | GDPR erasure, PII tokenisation, audit log |
| **Infrastructure** | Single region, Kubernetes | Multi-AZ, auto-scaling | Multi-region active-active |

---

## Constraints and Assumptions

### Constraints
- **Provider contracts**: The platform must not violate provider Terms of Service (e.g., FCM prohibits sending to tokens older than 270 days without validation).
- **Regulatory jurisdiction**: For initial MVP, data residency is US-only. EU data residency requires a separate deployment region with dedicated infrastructure.
- **SMS character limits**: SMS messages exceeding 160 GSM-7 characters will be split into multi-part messages. The platform charges per segment, not per send.
- **WhatsApp template approval**: WhatsApp message templates must be pre-approved by Meta. The platform cannot send free-form WhatsApp messages to users who have not initiated a conversation within 24 hours.
- **Email warm-up**: Newly provisioned sending domains and IPs require a warm-up period of 4–8 weeks. Campaign volumes must be ramped gradually to avoid deliverability damage.

### Assumptions
- Tenants are responsible for obtaining valid consent from recipients before sending marketing communications. The platform enforces consent checks but does not independently verify the legal basis.
- Phone number and email address validation (format only) is performed at ingestion time. The platform does not guarantee that an address will result in delivery.
- Push notification token management (registration, invalidation) is the responsibility of the tenant's mobile application. The platform consumes tokens as provided.
- All provider credentials supplied by tenants are assumed to be valid and to have sufficient quota for the expected message volume.

---

## Glossary

| Term | Definition |
|---|---|
| **Tenant** | An isolated organisational account on the platform. All data is partitioned by tenant. |
| **Channel** | The delivery mechanism for a notification: email, SMS, push, in-app, webhook, WhatsApp, Slack. |
| **Priority Tier** | A classification of message urgency: P0 (transactional), P1 (operational), P2 (promotional). Each tier has independent queues and SLOs. |
| **Idempotency Key** | A client-supplied or system-generated key that prevents a message from being sent more than once, even under retry or replay. |
| **Suppression List** | A per-tenant list of recipients who must not receive messages, covering hard bounces, spam complaints, and explicit opt-outs. |
| **Circuit Breaker** | A resilience pattern that stops sending to a provider when its error rate exceeds a threshold, allowing recovery before traffic resumes. |
| **DLQ (Dead-Letter Queue)** | A holding queue for messages that have exhausted all retry attempts, awaiting operator inspection and replay. |
| **Template Version** | An immutable snapshot of a template's content at a point in time. Published versions cannot be modified. |
| **Consent** | An explicit record that a recipient has agreed to receive a specified category of messages via a specified channel. |
| **Opt-Out** | A recipient request to stop receiving messages. May be channel-specific or universal. |
| **Hard Bounce** | A permanent delivery failure caused by an invalid or non-existent recipient address. Hard-bounced addresses are automatically suppressed. |
| **Soft Bounce** | A temporary delivery failure (e.g., mailbox full). Soft bounces are retried; repeated soft bounces may trigger suppression. |
| **Spam Complaint** | A recipient marking a message as spam. Complaints are automatically fed back via provider feedback loops and trigger suppression. |
| **DKIM/SPF/DMARC** | Email authentication standards used to establish sender identity and improve deliverability. |
| **Webhook** | An HTTP callback — a notification sent to a tenant-configured URL when an event occurs on the platform. |
| **Correlation ID** | A unique identifier that threads together all log entries, trace spans, and events for a single logical operation. |
| **Trace ID** | A distributed tracing identifier propagated across all services for a single end-to-end request. |
| **Drip Sequence** | A series of messages automatically sent over time or triggered by recipient events, used for onboarding, nurture, and re-engagement flows. |
| **Send-Time Optimisation (STO)** | Delaying send time to the individual recipient's historically highest-engagement time window. |
| **Provider Adapter** | A service component that wraps a third-party messaging provider API behind a common interface. |
