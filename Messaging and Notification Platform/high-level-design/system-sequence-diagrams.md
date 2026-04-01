# System Sequence Diagrams

## Overview

This document captures system-level sequence diagrams for the Messaging and Notification Platform. Each diagram shows the ordered interactions between internal services and external systems for a specific business scenario. These diagrams are the primary reference for understanding runtime behaviour, integration contracts, and failure-handling logic across the platform.

---

## 1. Send Transactional Email

**Business context:** A client application (e.g., an e-commerce checkout service) calls the platform API to send a single transactional email — for example, an order confirmation. The platform must validate the request, enforce opt-out rules, apply rate limits, render the template, route to the correct email provider, record the delivery attempt, and surface delivery events back to the caller via webhooks.

```mermaid
sequenceDiagram
    autonumber
    participant Client as Client App
    participant GW as API Gateway
    participant MS as MessageService
    participant TE as TemplateEngine
    participant OO as OptOutService
    participant RL as RateLimiter
    participant PR as ProviderRouter
    participant SG as SendGrid
    participant AS as AnalyticsService
    participant WH as WebhookService

    Client->>GW: POST /v1/messages {to, templateId, variables, channel: "email"}
    GW->>GW: Authenticate API key, validate tenant
    GW->>MS: CreateMessage(request, tenantId)

    MS->>OO: IsOptedOut(tenantId, recipient, channel="email")
    OO-->>MS: false (not opted out)

    MS->>RL: CheckLimit(tenantId, channel="email")
    RL-->>MS: allowed (remaining: 4321)

    MS->>TE: RenderTemplate(templateId, variables, locale)
    TE->>TE: Fetch template version (published)
    TE->>TE: Compile Handlebars template
    TE->>TE: Inject variables, apply HTML sanitisation
    TE-->>MS: RenderedContent {subject, htmlBody, textBody}

    MS->>MS: Persist Message record (status=QUEUED)
    MS-->>GW: 202 Accepted {messageId, status: "queued"}
    GW-->>Client: 202 Accepted {messageId}

    MS->>PR: Route(message, channel="email", tenantConfig)
    PR->>PR: Select provider (SendGrid — primary)
    PR->>PR: Inject tenant SMTP credentials

    PR->>SG: POST /v3/mail/send {from, to, subject, html, text}
    SG-->>PR: 202 Accepted {messageId: "sg-abc123"}

    PR->>MS: DeliveryAttemptRecorded(messageId, provider="sendgrid", status=SENT, providerRef="sg-abc123")
    MS->>MS: Update Message status → SENT

    MS->>AS: RecordUsage(tenantId, channel="email", messageId, ts)
    AS-->>MS: ack

    SG-->>GW: POST /webhooks/sendgrid {event: "delivered", messageId: "sg-abc123"}
    GW->>MS: HandleProviderEvent(providerRef, event="delivered")
    MS->>MS: Update Message status → DELIVERED
    MS->>WH: DispatchEvent(tenantId, "message.delivered", {messageId})
    WH->>Client: POST {tenantWebhookUrl} {event: "message.delivered", messageId, ts}
    Client-->>WH: 200 OK
```

**Key notes:**
- Steps 4–5 (opt-out and rate-limit checks) happen synchronously before any provider call, ensuring no message is sent in violation of preferences or quotas.
- The API returns `202 Accepted` before provider delivery completes; actual delivery status arrives via webhook (step 24).
- `AnalyticsService` is updated asynchronously to avoid blocking the critical path.

---

## 2. Multi-Channel Campaign Execution

**Business context:** A marketing team schedules a promotional campaign to send emails, SMS messages, and push notifications to a segmented audience of 200,000 contacts. The platform must fan-out the campaign across three delivery channels concurrently while tracking per-channel progress and emitting a completion event when all channels finish.

```mermaid
sequenceDiagram
    autonumber
    participant MA as MarketingApp
    participant CS as CampaignService
    participant SEG as AudienceSegmentation
    participant MQ as MessageQueue
    participant EW as EmailWorker
    participant SW as SMSWorker
    participant PW as PushWorker
    participant SG as SendGrid
    participant TW as Twilio
    participant FCM as FCM/APNS
    participant AS as AnalyticsService
    participant WH as WebhookService

    MA->>CS: POST /v1/campaigns/{id}/launch
    CS->>CS: Validate campaign (status=SCHEDULED, sendAt <= now)
    CS->>SEG: ResolveAudience(segmentId, tenantId)
    SEG->>SEG: Query contacts, apply filter rules
    SEG-->>CS: ContactList [200,000 contacts]

    CS->>CS: Split list by channel subscription
    CS->>CS: Create CampaignRun record (status=IN_PROGRESS)

    par Email fan-out
        CS->>MQ: Enqueue EmailBatch(campaignRunId, contacts[email], templateId)
    and SMS fan-out
        CS->>MQ: Enqueue SMSBatch(campaignRunId, contacts[sms], templateId)
    and Push fan-out
        CS->>MQ: Enqueue PushBatch(campaignRunId, contacts[push], templateId)
    end

    MA-->>CS: 202 Accepted {campaignRunId}

    loop Email batches (1,000 per batch)
        MQ->>EW: ConsumeBatch(emailBatch)
        EW->>EW: Render template for each contact
        EW->>SG: POST /v3/mail/batch/send
        SG-->>EW: 202 Accepted
        EW->>AS: RecordBatchProgress(campaignRunId, channel="email", sent=1000)
    end

    loop SMS batches (500 per batch)
        MQ->>SW: ConsumeBatch(smsBatch)
        SW->>SW: Render SMS template
        SW->>TW: POST /2010-04-01/Accounts/{sid}/Messages.json (bulk)
        TW-->>SW: 201 Created
        SW->>AS: RecordBatchProgress(campaignRunId, channel="sms", sent=500)
    end

    loop Push batches (2,000 per batch)
        MQ->>PW: ConsumeBatch(pushBatch)
        PW->>PW: Build FCM/APNS payload
        PW->>FCM: POST /v1/projects/{id}/messages:sendEach
        FCM-->>PW: 200 OK (multicast result)
        PW->>AS: RecordBatchProgress(campaignRunId, channel="push", sent=2000)
    end

    AS->>CS: AllBatchesComplete(campaignRunId)
    CS->>CS: Update CampaignRun status → COMPLETED
    CS->>WH: DispatchEvent(tenantId, "campaign.completed", {campaignRunId, stats})
    WH->>MA: POST {webhookUrl} {event: "campaign.completed", sent, failed, ts}
```

**Key notes:**
- Fan-out across channels is parallel (the `par` block); workers consume independently and report progress to `AnalyticsService`.
- Batch sizes are configurable per provider to respect their bulk API limits.
- `CampaignService` learns of completion via an event from `AnalyticsService` once all enqueued batches have been acknowledged.

---

## 3. Provider Failover

**Business context:** The primary email provider (SendGrid) returns a `503 Service Unavailable` error. The platform must detect the failure, retry with a secondary provider (Mailgun), record both attempts, and publish a provider-health event so the routing table can be updated automatically.

```mermaid
sequenceDiagram
    autonumber
    participant MS as MessageService
    participant PR as ProviderRouter
    participant PC as ProviderCircuitBreaker
    participant SG as SendGrid
    participant MG as Mailgun
    participant EQ as EventQueue
    participant Alert as AlertingService

    MS->>PR: Route(message, channel="email")
    PR->>PC: GetHealthyProvider(channel="email", tenantId)
    PC-->>PR: provider=SendGrid (circuit=CLOSED)

    PR->>SG: POST /v3/mail/send {payload}
    SG-->>PR: 503 Service Unavailable

    PR->>PR: Record attempt #1 (provider=SendGrid, status=FAILED, error=503)
    PR->>PC: RecordFailure(provider=SendGrid)
    PC->>PC: Increment failure counter (3/5 threshold)

    PR->>PR: Evaluate retry policy (attempt 1 of 3, backoff=0s)
    PR->>SG: POST /v3/mail/send {payload}  [retry #1]
    SG-->>PR: 503 Service Unavailable

    PR->>PC: RecordFailure(provider=SendGrid)
    PC->>PC: Increment failure counter (4/5 threshold)

    PR->>PR: Evaluate retry policy (attempt 2 of 3, backoff=1s)
    Note over PR: Wait 1 second
    PR->>SG: POST /v3/mail/send {payload}  [retry #2]
    SG-->>PR: 503 Service Unavailable

    PR->>PC: RecordFailure(provider=SendGrid)
    PC->>PC: OPEN circuit for SendGrid (5/5 threshold reached)
    PC->>EQ: Publish ProviderDegraded(provider=SendGrid, channel=email)
    EQ->>Alert: Notify on-call (PagerDuty)

    PR->>PC: GetHealthyProvider(channel="email", tenantId) [failover]
    PC-->>PR: provider=Mailgun (circuit=CLOSED)

    PR->>MG: POST /v3/{domain}/messages {payload}
    MG-->>PR: 200 OK {id: "mg-xyz789"}

    PR->>PR: Record attempt #4 (provider=Mailgun, status=SENT)
    PR-->>MS: DeliveryResult(status=SENT, provider=Mailgun, ref="mg-xyz789", attemptCount=4)
    MS->>MS: Update Message (status=SENT, provider=Mailgun)
```

**Key notes:**
- The circuit breaker opens after 5 consecutive failures, preventing further calls to SendGrid until a health-check recovers it.
- All delivery attempts (including failures) are recorded for audit and analytics.
- The `ProviderDegraded` event triggers automated alerting independently of the delivery path.

---

## 4. Webhook Event Delivery

**Business context:** An email provider (SendGrid) sends a delivery status event (e.g., "bounce") to the platform's inbound webhook endpoint. The platform must validate the signature, parse the event, update message status, and re-dispatch the event to the tenant's registered outbound webhook URL with HMAC authentication. If the client's webhook returns an error, the platform must retry with exponential backoff.

```mermaid
sequenceDiagram
    autonumber
    participant SG as SendGrid
    participant IW as InboundWebhookController
    participant EP as EventProcessor
    participant MS as MessageService
    participant OWS as OutboundWebhookService
    participant RQ as RetryQueue
    participant CW as Client Webhook

    SG->>IW: POST /webhooks/inbound/sendgrid\n[X-Twilio-Email-Event-Webhook-Signature header]
    IW->>IW: Verify ECDSA signature (SendGrid public key)
    IW-->>SG: 200 OK (fast-ack, process async)

    IW->>EP: ProcessEvents([{event:"bounced", email, messageId, ts}])

    EP->>EP: Resolve internalMessageId from providerRef
    EP->>MS: UpdateDeliveryStatus(messageId, status=BOUNCED, reason, ts)
    MS->>MS: Update Message record
    MS-->>EP: ack

    EP->>EP: Resolve tenant webhook config for event type "message.bounced"
    EP->>OWS: Dispatch(tenantId, "message.bounced", {messageId, email, reason, ts})

    OWS->>OWS: Sign payload with tenant HMAC secret
    OWS->>OWS: Set X-Webhook-Signature header (HMAC-SHA256)
    OWS->>CW: POST {tenantWebhookUrl} {event: "message.bounced", ...}\n[X-Webhook-Signature]
    CW-->>OWS: 500 Internal Server Error

    OWS->>RQ: Enqueue retry (attempt=1, nextAt=now+30s, payload)

    Note over RQ,OWS: 30 seconds later
    RQ->>OWS: DequeueRetry(attempt=1)
    OWS->>CW: POST {tenantWebhookUrl} {event: "message.bounced", ...}
    CW-->>OWS: 500 Internal Server Error
    OWS->>RQ: Enqueue retry (attempt=2, nextAt=now+60s, payload)

    Note over RQ,OWS: 60 seconds later
    RQ->>OWS: DequeueRetry(attempt=2)
    OWS->>CW: POST {tenantWebhookUrl} {event: "message.bounced", ...}
    CW-->>OWS: 200 OK

    OWS->>OWS: Mark delivery attempt SUCCEEDED (attempt=3)
    OWS->>EP: WebhookDelivered(webhookDeliveryId)
```

**Key notes:**
- The inbound webhook controller returns `200 OK` immediately after signature verification; all processing is asynchronous so providers do not time out.
- Outbound retry schedule: 30 s → 60 s → 120 s → 300 s → 600 s (5 attempts max). After all attempts fail, the event is moved to the dead-letter store and an alert is raised.
- HMAC signing lets client applications verify that events originated from the platform.

---

## 5. Template Versioning Lifecycle

**Business context:** A developer creates a new email template, iterates on the content via a preview/test cycle, then publishes the template to production. Once published, the version is immutable; future edits create a new draft version. This sequence shows the full draft → publish lifecycle and the version-lock invariant enforcement.

```mermaid
sequenceDiagram
    autonumber
    participant Dev as Developer
    participant GW as API Gateway
    participant TS as TemplateService
    participant TE as TemplateEngine
    participant DB as TemplateDB
    participant MS as MessageService

    Dev->>GW: POST /v1/templates {name, channel, content, variables}
    GW->>TS: CreateTemplate(tenantId, request)
    TS->>DB: INSERT Template (status=DRAFT, version=1)
    DB-->>TS: templateId, versionId
    TS-->>GW: 201 Created {templateId, versionId, status: "draft"}
    GW-->>Dev: 201 Created

    Dev->>GW: PUT /v1/templates/{id}/versions/{vId} {content}
    GW->>TS: UpdateDraftVersion(templateId, versionId, content)
    TS->>TS: Assert version.status == DRAFT (mutable)
    TS->>DB: UPDATE TemplateVersion content
    DB-->>TS: ok
    TS-->>GW: 200 OK {versionId, updatedAt}
    GW-->>Dev: 200 OK

    Dev->>GW: POST /v1/templates/{id}/versions/{vId}/preview {variables}
    GW->>TS: PreviewTemplate(templateId, versionId, variables)
    TS->>TE: RenderPreview(draftContent, variables)
    TE-->>TS: RenderedHTML + RenderedText
    TS-->>GW: 200 OK {html, text, spamScore, warnings[]}
    GW-->>Dev: 200 OK {rendered preview}

    Dev->>GW: POST /v1/templates/{id}/versions/{vId}/publish
    GW->>TS: PublishVersion(templateId, versionId)
    TS->>TS: Assert version.status == DRAFT
    TS->>TS: Assert required variables declared
    TS->>DB: UPDATE TemplateVersion status → PUBLISHED, lockedAt=now()
    TS->>DB: UPDATE Template activeVersionId → versionId
    DB-->>TS: ok
    TS-->>GW: 200 OK {versionId, status: "published", lockedAt}
    GW-->>Dev: 200 OK

    Note over Dev,DB: Template version is now immutable

    Dev->>GW: POST /v1/templates/{id}/versions {basedOn: versionId}
    GW->>TS: CreateNewDraft(templateId, baseVersionId)
    TS->>DB: INSERT TemplateVersion (status=DRAFT, version=2, content copied from v1)
    DB-->>TS: newVersionId
    TS-->>GW: 201 Created {newVersionId, status: "draft", version: 2}
    GW-->>Dev: 201 Created

    MS->>TS: GetPublishedContent(templateId)
    TS->>DB: SELECT version WHERE activeVersionId AND status=PUBLISHED
    DB-->>TS: TemplateVersion{content, variables}
    TS-->>MS: TemplateContent (immutable snapshot)
```

**Key notes:**
- `PublishVersion` sets `lockedAt` and changes status to `PUBLISHED`; any subsequent `UpdateDraftVersion` call on a published version is rejected with `409 Conflict`.
- Creating a new draft (step 27) copies the published content as a starting point, incrementing the version counter.
- `MessageService` always fetches the `activeVersionId` snapshot at render time, ensuring in-flight messages are never affected by template edits.

## Scope
- Multi-tenant, multi-channel notifications (email, SMS, push, webhook).
- Transactional, operational, and campaign traffic profiles.
## Mermaid Diagram
```mermaid
sequenceDiagram
  participant Client
  participant API
  participant Orchestrator
  participant Topic as PriorityTopic
  participant Worker
  participant Provider
  participant Callback
  Client->>API: POST /notifications (idempotency-key)
  API->>Orchestrator: validate + persist
  Orchestrator->>Topic: publish dispatch message
  Worker->>Topic: consume
  Worker->>Provider: send payload
  Provider-->>Worker: accepted/provider_message_id
  Provider-->>Callback: delivery status webhook
  Callback->>Orchestrator: update final status
```
- End-to-end controls from API ingestion to provider callbacks and compliance evidence.

## Coverage
This document is part of the implementation-ready set and should stay synchronized with requirements, design, and runbooks.

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
