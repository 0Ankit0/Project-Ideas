# Cloud Architecture - Library Management System

## Reference Cloud Mapping (AWS Example)

| Capability | Reference Service |
|------------|-------------------|
| Patron and staff frontend hosting | CloudFront + S3 / Amplify |
| Public protection | AWS WAF |
| API and workers | ECS/Fargate or EKS |
| Database | Amazon RDS for PostgreSQL |
| Search | Amazon OpenSearch |
| Messaging | Amazon SQS / EventBridge |
| Object storage | Amazon S3 |
| Notifications | Amazon SES / SNS |
| Monitoring | CloudWatch + OpenTelemetry |
| Identity federation | IAM Identity Center / external IdP |

## Architecture Notes
- Separate production and non-production environments to protect patron data and operational integrity.
- Retain backups and recovery procedures for circulation records, hold queues, and financial events.
- Keep search indexing asynchronous but monitor freshness to avoid stale availability information.

## Borrowing & Reservation Lifecycle, Consistency, Penalties, and Exception Patterns

### Artifact focus: Cloud deployment requirements

This section is intentionally tailored for this specific document so implementation teams can convert architecture and analysis into build-ready tasks.

### Implementation directives for this artifact
- Define managed service choices for relational DB, queue/bus, cache, and secrets.
- Specify network segmentation and private connectivity for payment providers.
- Include autoscaling and backup/restore RPO-RTO targets for circulation data.

### Lifecycle controls that must be reflected here
- Borrowing must always enforce policy pre-checks, deterministic copy selection, and atomic loan/copy updates.
- Reservation behavior must define queue ordering, allocation eligibility re-checks, and pickup expiry/no-show outcomes.
- Fine and penalty flows must define accrual formula, cap behavior, and lost/damage adjudication paths.
- Exception handling must define idempotency, conflict semantics, outbox reliability, and operator recovery procedures.

### Traceability requirements
- Every major rule in this document should map to at least one API contract, domain event, or database constraint.
- Include policy decision codes and audit expectations wherever staff override or monetary adjustment is possible.

### Definition of done for this artifact
- Content is specific to this artifact type and not a generic duplicate.
- Rules are testable (unit/integration/contract) and reference concrete data/events/errors.
- Diagram semantics (if present) are consistent with textual constraints and lifecycle behavior.
