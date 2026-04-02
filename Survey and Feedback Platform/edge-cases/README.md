# Edge Cases — Survey and Feedback Platform

## Purpose and Scope

This directory catalogs all identified edge cases for the Survey and Feedback Platform. Each edge case
documents a specific failure mode, its potential impact, detection strategy, mitigation/recovery steps,
and prevention measures. These documents serve as the authoritative reference for:

- Engineering teams implementing resilience patterns and defensive code
- QA teams designing test scenarios and chaos engineering experiments
- On-call engineers responding to production incidents
- Product managers understanding system limits and risk boundaries
- Security and compliance teams auditing platform behavior

The platform is built on FastAPI (Python 3.11), async SQLAlchemy, Pydantic v2, PostgreSQL 15, MongoDB 7,
Redis 7, Celery, AWS ECS Fargate, RDS PostgreSQL, ElastiCache Redis, CloudFront, Route 53, WAF, and
AWS Kinesis → Lambda → DynamoDB for analytics.

---

## Edge Case ID Schema

All edge cases follow the format: **EC-DOMAIN-NNN**

| Domain Code | Domain Name              | Description                                      |
|-------------|--------------------------|--------------------------------------------------|
| `FORM`      | Form Builder             | Survey creation, logic, question management      |
| `RESPONSE`  | Response Collection      | Submission, validation, storage, replay          |
| `ANALYTICS` | Analytics and Reporting  | Aggregation, dashboards, NPS, exports            |
| `DIST`      | Distribution and Sharing | Email campaigns, embeds, SMS, QR codes           |
| `SEC`       | Security and Compliance  | Auth, XSS, IDOR, GDPR, SSRF, rate limiting       |
| `OPS`       | Operations               | Infrastructure, deployments, failovers, capacity |

NNN is a zero-padded three-digit integer (e.g., 001, 012).

---

## Severity Classification

| Level        | Criteria                                                                                       | Example                                          |
|--------------|------------------------------------------------------------------------------------------------|--------------------------------------------------|
| **Critical** | Service down, data loss, security breach, active compliance violation, financial exposure      | RDS primary failover with data loss, GDPR breach |
| **High**     | Feature significantly degraded, significant user impact, potential data corruption             | Kinesis lag >5 min, duplicate response records   |
| **Medium**   | Minor feature issue, workaround available, limited user impact, recoverable without data loss  | NPS calc on <10 responses, embed CORS failure    |
| **Low**      | Cosmetic or rare issue, no data integrity risk, minimal business impact                        | QR code printed for archived survey              |

---

## Complete Summary Table

### Form Builder (EC-FORM-001 to EC-FORM-008)

| ID           | Title                                                       | Domain | Severity | File                |
|--------------|-------------------------------------------------------------|--------|----------|---------------------|
| EC-FORM-001  | Circular Conditional Logic Reference                        | FORM   | High     | form-builder.md     |
| EC-FORM-002  | Maximum Question Limit Exceeded During Bulk Import          | FORM   | Medium   | form-builder.md     |
| EC-FORM-003  | Survey Published with Orphaned Logic Rules                  | FORM   | High     | form-builder.md     |
| EC-FORM-004  | Concurrent Team Member Edits Race Condition                 | FORM   | High     | form-builder.md     |
| EC-FORM-005  | File Upload Question with Malicious MIME Type Bypass        | FORM   | Critical | form-builder.md     |
| EC-FORM-006  | Matrix Question with 50+ Row/Column Combinations           | FORM   | Medium   | form-builder.md     |
| EC-FORM-007  | Survey Duplication with Broken S3 Media Attachments         | FORM   | Medium   | form-builder.md     |
| EC-FORM-008  | Question Position Reorder Collision                         | FORM   | Medium   | form-builder.md     |

### Response Collection (EC-RESPONSE-001 to EC-RESPONSE-010)

| ID               | Title                                                            | Domain   | Severity | File                     |
|------------------|------------------------------------------------------------------|----------|----------|--------------------------|
| EC-RESPONSE-001  | Duplicate Response Submission (double-click / network retry)     | RESPONSE | High     | response-collection.md   |
| EC-RESPONSE-002  | Response Session Expires After 7-Day Inactivity                 | RESPONSE | Medium   | response-collection.md   |
| EC-RESPONSE-003  | File Upload in Response Exceeds Tier Limit                       | RESPONSE | Medium   | response-collection.md   |
| EC-RESPONSE-004  | Survey Closed Mid-Response                                       | RESPONSE | Medium   | response-collection.md   |
| EC-RESPONSE-005  | Required Question Bypass via Direct API Manipulation             | RESPONSE | Critical | response-collection.md   |
| EC-RESPONSE-006  | Kinesis Shard Iterator Expiry                                    | RESPONSE | High     | response-collection.md   |
| EC-RESPONSE-007  | Offline PWA Response Sync Conflict                               | RESPONSE | High     | response-collection.md   |
| EC-RESPONSE-008  | Bot Flood (100+ responses/minute from rotating IPs)             | RESPONSE | Critical | response-collection.md   |
| EC-RESPONSE-009  | Response Data Loss During RDS Primary Failover                   | RESPONSE | Critical | response-collection.md   |
| EC-RESPONSE-010  | GDPR Subject Access Request — Respondent Was Anonymous          | RESPONSE | High     | response-collection.md   |

### Analytics and Reporting (EC-ANALYTICS-001 to EC-ANALYTICS-008)

| ID                  | Title                                                       | Domain    | Severity | File                          |
|---------------------|-------------------------------------------------------------|-----------|----------|-------------------------------|
| EC-ANALYTICS-001    | NPS Calculation with <10 Responses                          | ANALYTICS | Medium   | analytics-and-reporting.md    |
| EC-ANALYTICS-002    | Kinesis Consumer Lag >5 Minutes                             | ANALYTICS | High     | analytics-and-reporting.md    |
| EC-ANALYTICS-003    | Cross-Tabulation Query Timeout on 500K+ Response Dataset    | ANALYTICS | High     | analytics-and-reporting.md    |
| EC-ANALYTICS-004    | Report Generation OOM — Celery Worker Killed                | ANALYTICS | High     | analytics-and-reporting.md    |
| EC-ANALYTICS-005    | DynamoDB Hot Partition from Viral Survey                    | ANALYTICS | High     | analytics-and-reporting.md    |
| EC-ANALYTICS-006    | AWS Comprehend Throttle (500 TPS limit)                     | ANALYTICS | Medium   | analytics-and-reporting.md    |
| EC-ANALYTICS-007    | Scheduled Report Email Delivery Failure                     | ANALYTICS | Medium   | analytics-and-reporting.md    |
| EC-ANALYTICS-008    | Analytics Cache Poisoning (stale NPS score from Redis)      | ANALYTICS | High     | analytics-and-reporting.md    |

### Distribution and Sharing (EC-DIST-001 to EC-DIST-008)

| ID           | Title                                                       | Domain | Severity | File                          |
|--------------|-------------------------------------------------------------|--------|----------|-------------------------------|
| EC-DIST-001  | Campaign Sent to Unsubscribed Contacts                      | DIST   | Critical | distribution-and-sharing.md   |
| EC-DIST-002  | SendGrid Daily Volume Limit Reached Mid-Campaign            | DIST   | High     | distribution-and-sharing.md   |
| EC-DIST-003  | Embed Widget CORS Failure                                   | DIST   | Medium   | distribution-and-sharing.md   |
| EC-DIST-004  | Survey Short-Link Token Collision                           | DIST   | High     | distribution-and-sharing.md   |
| EC-DIST-005  | QR Code Rendered for Archived/Deleted Survey                | DIST   | Low      | distribution-and-sharing.md   |
| EC-DIST-006  | SMS Distribution to Disconnected/Ported Number             | DIST   | Medium   | distribution-and-sharing.md   |
| EC-DIST-007  | Bounce Rate Exceeds 5% (SendGrid Suspension Threshold)      | DIST   | Critical | distribution-and-sharing.md   |
| EC-DIST-008  | Open Redirect via Custom Thank-You URL                      | DIST   | Critical | distribution-and-sharing.md   |

### Security and Compliance (EC-SEC-001 to EC-SEC-008)

| ID          | Title                                                        | Domain | Severity | File                          |
|-------------|--------------------------------------------------------------|--------|----------|-------------------------------|
| EC-SEC-001  | JWT Token Replay After Logout                                | SEC    | Critical | security-and-compliance.md    |
| EC-SEC-002  | Stored XSS via Survey Question Text                          | SEC    | Critical | security-and-compliance.md    |
| EC-SEC-003  | IDOR — Analyst Accessing Another Workspace's Response Data   | SEC    | Critical | security-and-compliance.md    |
| EC-SEC-004  | Magic Link Token Brute Force                                 | SEC    | High     | security-and-compliance.md    |
| EC-SEC-005  | GDPR Bulk Data Export Causing OOM                            | SEC    | High     | security-and-compliance.md    |
| EC-SEC-006  | SSRF via Webhook URL to Internal VPC Metadata Endpoint       | SEC    | Critical | security-and-compliance.md    |
| EC-SEC-007  | Distributed Rate Limit Bypass via IP Rotation               | SEC    | High     | security-and-compliance.md    |
| EC-SEC-008  | PII Leakage in Cross-Tab Analytics (k-anonymity violation)   | SEC    | Critical | security-and-compliance.md    |

### Operations (EC-OPS-001 to EC-OPS-008)

| ID          | Title                                                           | Domain | Severity | File           |
|-------------|-----------------------------------------------------------------|--------|----------|----------------|
| EC-OPS-001  | RDS PostgreSQL Primary Failover During Peak                     | OPS    | Critical | operations.md  |
| EC-OPS-002  | ElastiCache Redis Node Failure                                  | OPS    | High     | operations.md  |
| EC-OPS-003  | ECS Fargate Task OOM Kill During Large Report Generation        | OPS    | High     | operations.md  |
| EC-OPS-004  | Kinesis Shard Throttle During Viral Survey                      | OPS    | High     | operations.md  |
| EC-OPS-005  | Celery Queue Backlog >10K Tasks                                 | OPS    | High     | operations.md  |
| EC-OPS-006  | S3 Bucket Policy Misconfiguration Exposing Report Files        | OPS    | Critical | operations.md  |
| EC-OPS-007  | Database Migration Failure During Rolling Deploy               | OPS    | Critical | operations.md  |
| EC-OPS-008  | AWS Availability Zone Outage (50% ECS Tasks Lost)              | OPS    | Critical | operations.md  |

---

## How to Use

Each file in this directory covers one domain of edge cases. Navigate directly to the relevant file:

- **[form-builder.md](form-builder.md)** — EC-FORM-001 through EC-FORM-008: Survey creation failures,
  logic conflicts, bulk import limits, and concurrent edit race conditions.

- **[response-collection.md](response-collection.md)** — EC-RESPONSE-001 through EC-RESPONSE-010:
  Duplicate submissions, session expiry, API manipulation, bot floods, and GDPR handling for anonymous respondents.

- **[analytics-and-reporting.md](analytics-and-reporting.md)** — EC-ANALYTICS-001 through EC-ANALYTICS-008:
  Kinesis lag, OOM report generation, DynamoDB hot partitions, and cache poisoning.

- **[distribution-and-sharing.md](distribution-and-sharing.md)** — EC-DIST-001 through EC-DIST-008:
  CAN-SPAM violations, SendGrid limits, CORS failures, token collisions, and open redirects.

- **[security-and-compliance.md](security-and-compliance.md)** — EC-SEC-001 through EC-SEC-008:
  JWT replay, XSS, IDOR, SSRF, GDPR export OOM, and k-anonymity violations.

- **[operations.md](operations.md)** — EC-OPS-001 through EC-OPS-008:
  RDS failover, Redis node loss, ECS OOM, Kinesis throttle, Celery backlog, S3 misconfiguration, migration failure, AZ outage.

Each edge case is documented using a consistent 5-section table:

```
### EC-DOMAIN-NNN: [Title]

| Field                     | Details |
|---------------------------|---------|
| Failure Mode              | ...     |
| Impact                    | ...     |
| Detection                 | ...     |
| Mitigation / Recovery     | ...     |
| Prevention                | ...     |
```

---

## Monitoring Coverage

The following edge cases have corresponding CloudWatch alarms configured in the infrastructure
(see `/infrastructure/monitoring.tf` and `/infrastructure/cloudwatch-alarms.tf`):

| EC ID             | CloudWatch Alarm Name                             | Threshold / Condition                               |
|-------------------|---------------------------------------------------|-----------------------------------------------------|
| EC-RESPONSE-001   | `SurveyPlatform-DuplicateSubmissionRate`          | > 1% of submissions in 5 min                        |
| EC-RESPONSE-008   | `SurveyPlatform-BotFloodDetection`                | ResponseSubmissionRate > 100/min per survey_id      |
| EC-RESPONSE-009   | `SurveyPlatform-RDSConnectionDrop`                | DatabaseConnections < 5 for 2 consecutive minutes   |
| EC-ANALYTICS-002  | `SurveyPlatform-KinesisConsumerLag`               | GetRecords.IteratorAgeMilliseconds > 300000 ms      |
| EC-ANALYTICS-004  | `SurveyPlatform-CeleryWorkerOOM`                  | ECS MemoryUtilization > 90% for 3 minutes           |
| EC-ANALYTICS-005  | `SurveyPlatform-DynamoDBHotPartition`             | ConsumedWriteCapacityUnits per partition > 80%      |
| EC-DIST-007       | `SurveyPlatform-SendGridBounceRate`               | Bounce rate > 4% (warning) / > 5% (critical)        |
| EC-OPS-001        | `SurveyPlatform-RDSFailover`                      | RDS event: RDS-EVENT-0006 (failover)                |
| EC-OPS-002        | `SurveyPlatform-RedisNodeFailure`                 | CacheNodeStatus != available for any node           |
| EC-OPS-004        | `SurveyPlatform-KinesisShardThrottle`             | WriteProvisionedThroughputExceeded > 0 per minute   |
| EC-OPS-005        | `SurveyPlatform-CeleryQueueDepth`                 | Celery queue length > 5000 tasks                    |
| EC-OPS-006        | `SurveyPlatform-S3PublicBucketAlert`              | AWS Config rule: s3-bucket-public-read-prohibited   |
| EC-OPS-008        | `SurveyPlatform-ECSTaskHealthDrop`                | Running ECS task count < 50% of desired             |
| EC-SEC-006        | `SurveyPlatform-SSRFWebhookAttempt`               | WAF rule `BlockPrivateIPRanges` match count > 0     |

Alarms without explicit coverage are detected via application-level logging to CloudWatch Logs groups
`/survey-platform/api-service`, `/survey-platform/worker-service`, and `/survey-platform/analytics-service`.

---

## Operational Policy Addendum

### 1. Response Data Privacy Policies

**GDPR Compliance:**
All survey response data containing personally identifiable information (PII) is classified as personal
data under GDPR Article 4. The platform acts as a data processor on behalf of workspace owners (data
controllers). Respondents have the following rights enforced by the platform:
- **Right of Access (Article 15):** SAR API endpoint returns all stored data within 30 days.
- **Right to Erasure (Article 17):** Respondent deletion cascade removes all response records,
  partial sessions, and derived analytics within 72 hours.
- **Data Minimisation (Article 5(1)(c)):** IP addresses are truncated to /24 (IPv4) or /48 (IPv6)
  after 30 days. Full IPs are never stored beyond 30 days.
- **Breach Notification (Article 33):** Security incidents are assessed within 24 hours; DPA
  notification occurs within 72 hours if a breach affecting personal data is confirmed.

**CCPA Compliance:**
California residents may request deletion of personal data or opt-out of data sale. The platform does
not sell personal data. Opt-out is recorded in the `privacy_preferences` table and propagated to all
downstream systems within 24 hours.

**PII Handling:** All PII fields (name, email, phone) are encrypted at rest using AES-256-GCM via
AWS KMS. PII fields are never included in log output or analytics aggregations.

### 2. Survey Distribution Policies

**CAN-SPAM / CASL Compliance:**
- Every outbound survey email includes a visible, one-click unsubscribe link.
- Unsubscribe requests are honoured within 10 business days (CAN-SPAM) and 10 days (CASL).
- Physical mailing address of the sending organisation is included in every email footer.
- Transactional vs. commercial emails are classified at send time; commercial emails require prior
  consent for CASL recipients.

**Anti-Spam:**
- SendGrid domain authentication (DKIM, SPF, DMARC) is required before any campaign can be sent.
- Bounce and complaint rates are monitored continuously. Campaigns are auto-paused if bounce rate
  exceeds 4% or complaint rate exceeds 0.1%.
- Contact lists are validated against suppression lists before every send.

### 3. Analytics and Retention Policies

**Data Retention by Tier:**
- **Free tier:** Response data retained for 12 months; exports available for 6 months.
- **Business tier:** Response data retained for 36 months; exports available for 24 months.
- **Enterprise tier:** Configurable retention up to 84 months; custom export schedules.

**Anonymisation:**
Response data is anonymised (email hashed, IP truncated, free-text fields NLP-scrubbed) after the
retention period expires. Anonymised aggregate statistics are retained indefinitely.

**Aggregation:**
Analytics aggregations (NPS, CSAT, completion rates) are pre-computed and cached in DynamoDB. Raw
response records are not exposed in analytics APIs; only aggregated results are returned.

### 4. System Availability Policies

**SLAs:**
- Survey submission endpoint: 99.9% monthly uptime (≤43.8 min downtime/month).
- Analytics dashboard: 99.5% monthly uptime (≤3.65 hr downtime/month).
- Email distribution: 99% monthly uptime (≤7.2 hr downtime/month).

**RTO / RPO:**
- RTO (Recovery Time Objective): 15 minutes for all Critical-severity incidents.
- RPO (Recovery Point Objective): 5 minutes (RDS automated backups every 5 minutes via PITR).

**Maintenance Windows:**
- Scheduled maintenance: Tuesdays 02:00–04:00 UTC and Saturdays 02:00–06:00 UTC.
- Emergency maintenance: On-call team notified via PagerDuty; status page updated within 5 minutes.
- Customers are notified of planned maintenance at least 72 hours in advance via status page and email.
