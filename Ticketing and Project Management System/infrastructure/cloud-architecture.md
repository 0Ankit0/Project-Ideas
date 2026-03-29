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

