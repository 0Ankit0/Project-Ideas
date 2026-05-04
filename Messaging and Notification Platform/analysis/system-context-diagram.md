# System Context Diagram

## Traceability
- Requirements baseline: [`../requirements/requirements.md`](../requirements/requirements.md)
- High-level topology: [`../high-level-design/architecture-diagram.md`](../high-level-design/architecture-diagram.md)
- External contracts: [`../detailed-design/api-design.md`](../detailed-design/api-design.md)
- Edge handling: [`../edge-cases/provider-failover.md`](../edge-cases/provider-failover.md)

## System Boundary

The Messaging and Notification Platform sits between internal producer systems, tenant operators, external delivery providers, and compliance/reporting stakeholders. Its boundary includes request admission, template governance, orchestration, dispatch, callback reconciliation, and evidence retention. It does **not** own the business events that trigger notifications or the downstream provider infrastructure.

## Context Diagram

```mermaid
flowchart TB
  subgraph Actors
    Apps[Product services / event producers]
    Ops[Tenant operators / campaign managers]
    Support[Support + compliance analysts]
  end

  subgraph Platform[Messaging and Notification Platform]
    API[Notification API + Portal]
    Template[Template + Preference Services]
    Orchestrator[Delivery Orchestrator]
    Audit[Audit + Analytics]
  end

  subgraph External
    Providers[Email / SMS / Push / Webhook / Chat providers]
    IdP[SSO / IAM]
    Data[BI warehouse / SIEM]
    Pref[External consent and CRM systems]
  end

  Apps --> API
  Ops --> API
  Support --> Audit
  IdP --> API
  API --> Template
  API --> Orchestrator
  Template --> Pref
  Orchestrator --> Providers
  Providers --> Orchestrator
  Orchestrator --> Audit
  Audit --> Data
```

## External Actors and Systems

| Actor/System | Relationship to platform | Key responsibilities outside platform |
|---|---|---|
| Product services | submit send requests or publish triggering business events | decide when a user should be notified |
| Tenant operators | manage templates, routing, policies, and campaign schedules | business messaging strategy and approvals |
| Compliance/support analysts | inspect audit trails, DLQ items, and evidence exports | legal review, customer support, replay approval |
| Delivery providers | accept channel-specific dispatch requests and send callbacks | actual last-mile delivery to recipient devices or inboxes |
| Identity provider | authenticate operators and service principals | SSO, MFA, role assertions |
| External CRM/consent systems | source of recipient preferences and contact updates | customer profile management outside messaging core |
| BI/SIEM platforms | consume delivery metrics and security evidence | reporting, alerting, forensics |

## Context Invariants

- The platform is the authoritative source for notification message state, but not for the business domain event that caused the send.
- Tenant operators cannot bypass compliance or suppression policy through the UI or API.
- Provider callbacks are advisory until correlated to a known dispatch attempt and validated against replay/signature controls.

## Operational acceptance criteria

- Every external boundary has an authenticated identity model and traceable correlation ID propagation.
- Loss of one delivery provider must not block message acceptance for unrelated channels or healthy fallback routes.

## Delivery, Reliability, and Compliance Baseline

### 1) Delivery semantics
- **Default guarantee:** At-least-once delivery for all async sends. Exactly-once is not assumed; business safety is achieved via idempotency.
- **Idempotency contract:** `idempotency_key = tenant_id + message_type + recipient + template_version + request_nonce`.
- **Latency tiers:**
  - `P0 Transactional` (OTP, password reset): enqueue < 1s, provider handoff p95 < 5s.
  - `P1 Operational` (alerts, statements): enqueue < 5s, handoff p95 < 30s.
  - `P2 Promotional` (campaign): enqueue < 30s, handoff p95 < 5m.
- **Status model:** `ACCEPTED -> QUEUED -> DISPATCHING -> PROVIDER_ACCEPTED -> DELIVERED|FAILED|EXPIRED`.

### 2) Queue and topic behavior
- **Topic split:** `notifications.transactional`, `notifications.operational`, `notifications.promotional`, plus channel suffixes.
- **Partition key:** `tenant_id:recipient_id:channel` to preserve recipient-level ordering without global lock contention.
- **Backpressure policy:** API returns `202 Accepted` once persisted; throttling starts at queue depth thresholds and adaptive worker concurrency.
- **Poison message isolation:** messages with schema/validation failures bypass retries and go directly to DLQ.

### 3) Retry and dead-letter handling
- **Retry policy:** capped exponential backoff with jitter (e.g., 30s, 2m, 10m, 30m, 2h max).
- **Retryable causes:** transport timeout, 429, 5xx, transient DNS/network faults.
- **Non-retryable causes:** invalid recipient, permanent provider policy reject, malformed template payload.
- **DLQ payload:** original envelope, error class/code, attempt history, provider response excerpt, trace IDs.
- **Redrive controls:** replay by batch, by tenant, by error class; replay requires approval in production.

### 4) Provider routing and failover
- **Routing mode:** weighted primary/secondary by channel and geography.
- **Health model:** active probes + rolling error-rate window + circuit breaker half-open testing.
- **Failover rule:** open circuit on sustained 5xx or timeout rates; route to standby while preserving idempotency keys.
- **Recovery:** gradual traffic ramp-back (10% -> 25% -> 50% -> 100%) with rollback guards.

### 5) Template management
- **Lifecycle:** `DRAFT -> REVIEW -> APPROVED -> PUBLISHED -> DEPRECATED -> RETIRED`.
- **Versioning:** immutable published versions; sends always pin explicit version.
- **Schema checks:** required variables, type validation, locale fallback chain, safe HTML sanitization.
- **Change control:** dual approval for regulated templates; rollback < 5 minutes.

### 6) Compliance and audit logging
- **Audit events:** consent evaluation, suppression decisions, template render inputs/outputs hash, provider requests/responses, operator actions.
- **PII policy:** log tokenized recipient identifiers; redact message body unless explicit legal-hold context.
- **Retention:** operational logs 90 days hot, 1 year warm; compliance evidence 7 years (policy configurable).
- **Forensics query keys:** `tenant_id`, `message_id`, `correlation_id`, `provider_message_id`, `recipient_token`, time range.

## Verification Checklist
- [ ] All interfaces include idempotency + correlation identifiers.
- [ ] Retryable vs non-retryable errors are explicitly classified.
- [ ] DLQ replay process is documented with approvals and guardrails.
- [ ] Provider failover policy defines trigger, action, and recovery criteria.
- [ ] Template versioning and approval workflow are enforceable in tooling.
- [ ] Compliance evidence can be queried by message_id and correlation_id.
