# Cloud Architecture - Ticketing and Project Management System

## Reference Cloud Mapping (AWS Example)

| Capability | Reference Service |
|------------|-------------------|
| Frontend hosting | CloudFront + S3 or Amplify |
| Public protection | AWS WAF |
| API and workers | ECS/Fargate or EKS |
| Database | Amazon RDS for PostgreSQL |
| Object storage | Amazon S3 |
| Messaging | Amazon SQS / EventBridge |
| Search | Amazon OpenSearch |
| Identity federation | IAM Identity Center / external IdP |
| Malware scanning | Lambda + antivirus pipeline |
| Monitoring | CloudWatch + OpenTelemetry |

## Architecture Notes
- Use separate accounts or projects for production and non-production environments.
- Replicate database backups and object storage policies according to retention requirements.
- Emit workflow and audit events to centralized logging and observability systems.

## Delivery Topology and Scaling Blueprint

### Notification Delivery Topology
1. **Producer path**: ticket/project/sla services publish `NotificationRequested` domain events to Kafka (partition key: `tenant_id + ticket_id`).
2. **Orchestrator path**: notification-orchestrator consumes events, resolves audience/locale/channel policy, and writes immutable notification intents to PostgreSQL (`notification_intent` table).
3. **Fan-out path**: orchestrator emits channel jobs to SQS queues:
   - `notify-email.fifo`
   - `notify-push.fifo`
   - `notify-chat-standard`
   - `notify-webhook-standard`
4. **Worker path**: channel-specific workers send messages through SES/SNS/Slack/Teams/webhook providers and persist provider receipt IDs.
5. **Feedback path**: provider callbacks (bounce, delivery, read, throttle) flow through API Gateway to callback processor, update status projections, and publish `NotificationDeliveryUpdated`.
6. **Retry path**: transient failures are retried with exponential backoff and per-channel DLQs (`maxReceiveCount=5`), with dead-letter replay tooling.

**Reliability controls**
- Idempotency key = `intent_id + channel + recipient_hash`.
- FIFO queues only for channels where ordering is contractually required (email threads, in-app timeline).
- Rate limiter tokens per provider account to prevent global throttling.
- Quiet-hours policy evaluated before final send; deferred sends are parked in `scheduled_notifications`.

### Attachment Storage and Security Model

| Concern | Design Decision | Control Mechanism |
|---|---|---|
| Storage boundary | Tenant-scoped prefix in S3 (`org/{orgId}/ticket/{ticketId}/...`) | IAM policy + bucket policy conditions on prefix |
| Upload flow | Browser direct upload via pre-signed POST | 5-minute URL TTL + content-length limit + MIME allow-list |
| Object encryption | Encrypt every object with KMS CMK | SSE-KMS with key rotation every 365 days |
| Malware scanning | Async scan pipeline | S3 event → scan queue → scanner worker → verdict tag + quarantine move |
| Download access | Time-bounded signed URL via attachment service | Policy check before signing + 60-second URL TTL |
| Data lifecycle | Retention and legal hold support | S3 lifecycle + Glacier archival + hold metadata table |

**Security states for attachments**
- `uploaded_pending_scan` → cannot be downloaded by non-privileged users.
- `scan_clean` → downloadable based on RBAC/ABAC.
- `scan_suspect` → quarantined; only SecOps role can retrieve.
- `scan_failed` → retry scheduled; alert if >15 minutes pending.

### Search and Indexing Architecture
- **Source of truth**: PostgreSQL for transactional writes.
- **Change capture**: outbox table (`search_projection_outbox`) populated in same transaction as ticket/comment update.
- **Projector workers** consume outbox events and update OpenSearch indices:
  - `tickets_v1`
  - `comments_v1`
  - `projects_v1`
- **Versioned aliases** (`tickets_current`) support zero-downtime reindex.
- **Index consistency objective**: p95 projection lag < 30s.

**Reindex strategy**
1. Create new index version (`tickets_v2`) with updated mapping.
2. Backfill from PostgreSQL snapshot + incremental CDC catch-up.
3. Run parity checks (doc count and sampled query equivalence).
4. Swap alias atomically.
5. Retain prior index for 7 days for rollback.

### Worker Queue Scaling Model

| Queue Type | Trigger | Scaling Signal | Target |
|---|---|---|---|
| SLA timer queue | backlog growth | KEDA on queue length + oldest message age | < 2 min oldest age |
| Attachment scan queue | upload spikes | queue length + scanner CPU | clear backlog < 10 min |
| Notification queue | burst campaigns/incidents | queue length + provider throttle feedback | p95 send latency < 60s |
| Search projection queue | write bursts | lag in outbox sequence | p95 projection lag < 30s |

**Scale policy**
- Baseline min replicas per worker: 2 (multi-AZ redundancy).
- Max replicas derived from load test envelope and provider quotas.
- Circuit breaker pauses non-critical queues during incident mode to protect SLA timers.
- Priority classes: `critical` (SLA/escalation), `high` (notifications), `normal` (search projection), `low` (exports).

## Cross-Cutting Workflow and Operational Governance

### Cloud Architecture: Document-Specific Scope
- Primary focus for this artifact: **cloud controls, reliability posture, and operational observability**.
- Implementation handoff expectation: this document must be sufficient for an engineer/architect/operator to implement without hidden assumptions.
- Traceability anchor: `INFRASTRUCTURE_CLOUD_ARCHITECTURE` should be referenced in backlog items, design reviews, and release checklists when this artifact changes.

### Workflow and State Machine Semantics (INFRASTRUCTURE_CLOUD_ARCHITECTURE)
- For this document, workflow guidance must **guarantee durable event flow and timer precision for workflow execution**.
- Transition definitions must include trigger, actor, guard, failure code, side effects, and audit payload contract.
- Any asynchronous transition path must define idempotency key strategy and replay safety behavior.

### SLA and Escalation Rules (INFRASTRUCTURE_CLOUD_ARCHITECTURE)
- For this document, SLA guidance must **ensure queue/scheduler reliability and time synchronization guarantees**.
- Escalation must explicitly identify owner, dwell-time threshold, notification channel, and acknowledgement requirement.
- Breach and near-breach states must be queryable in reporting without recomputing from free-form notes.

### Permission Boundaries (INFRASTRUCTURE_CLOUD_ARCHITECTURE)
- For this document, permission guidance must **implement IAM/network boundaries and privileged-access controls**.
- Privileged actions require reason codes, actor identity, and immutable audit entries.
- Client-visible payloads must be explicitly redacted from internal-only and regulated fields.

### Reporting and Metrics (INFRASTRUCTURE_CLOUD_ARCHITECTURE)
- For this document, reporting guidance must **ensure telemetry durability/retention for ops and compliance reporting**.
- Metric definitions must include numerator/denominator, time window, dimensional keys, and null/missing-data behavior.
- Each metric should map to raw events/tables so results are reproducible during audits.

### Operational Edge-Case Handling (INFRASTRUCTURE_CLOUD_ARCHITECTURE)
- For this document, operational guidance must **codify failover, backup restore, and game-day validation procedures**.
- Partial failure handling must identify what is rolled back, compensated, or deferred.
- Recovery completion criteria must be measurable (not subjective) and tied to dashboard/alert signals.

### Implementation Readiness Checklist (INFRASTRUCTURE_CLOUD_ARCHITECTURE)
| Checklist Item | This Document Must Provide | Validation Evidence |
|---|---|---|
| Workflow Contract Completeness | All relevant states, transitions, and invalid paths for `infrastructure/cloud-architecture.md` | Scenario walkthrough + transition test mapping |
| SLA/ Escalation Determinism | Timer, pause, escalation, and override semantics | Policy table review + simulated timer run |
| Authorization Correctness | Role scope, tenant scope, and field visibility boundaries | Auth matrix review + API/UI parity checks |
| Reporting Reproducibility | KPI formulas, dimensions, and source lineage | Recompute KPI from event data sample |
| Operations Recoverability | Degraded-mode and compensation runbook steps | Tabletop/game-day evidence and postmortem template |
