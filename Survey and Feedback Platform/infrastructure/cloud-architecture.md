# Cloud Architecture — Survey and Feedback Platform

## Overview

The Survey and Feedback Platform is architected against the **AWS Well-Architected Framework**
(six pillars). Each pillar shapes concrete design decisions across the platform.

| Pillar | Application |
|---|---|
| **Operational Excellence** | IaC with Terraform, GitHub Actions CI/CD, CloudWatch dashboards, automated runbooks |
| **Security** | WAF, KMS encryption at rest, TLS 1.3 in transit, IAM least-privilege, Secrets Manager rotation |
| **Reliability** | Multi-AZ ECS + RDS, ElastiCache cluster failover, Route 53 health checks, Circuit Breaker on ECS |
| **Performance Efficiency** | ECS Fargate right-sizing, ElastiCache caching layer, CloudFront CDN, Kinesis streaming ingestion |
| **Cost Optimization** | Compute Savings Plans, RDS Reserved Instances, S3 Intelligent Tiering, Spot for Celery workers |
| **Sustainability** | Fargate eliminates idle EC2 capacity; auto-scaling matches capacity to demand |

---

## AWS Services Catalog

| Service | Purpose | Configuration | Est. Monthly Cost (USD) |
|---|---|---|---|
| **ECS Fargate** | Container orchestration for all microservices | 7 services × 2–4 tasks; 0.5–2 vCPU, 1–4 GB per task | $600–$1,200 |
| **Application Load Balancer (ALB)** | HTTP/HTTPS routing to ECS services, host-based rules | 1 ALB, HTTPS:443, HTTP→HTTPS redirect | $40–$80 |
| **RDS PostgreSQL 15 Multi-AZ** | Primary transactional database | `db.r6g.xlarge`, 500 GB gp3, Multi-AZ, 2 read replicas | $900–$1,100 |
| **ElastiCache Redis 7** | Session caching, pub/sub, Celery broker | Cluster mode, 3 shards, `cache.r6g.large` × 6 nodes | $400–$600 |
| **DynamoDB** | Analytics event store, time-series response data | On-demand capacity, global tables (us-east-1, us-west-2) | $100–$300 |
| **S3 — survey-platform-assets** | Survey media uploads, embedded survey JS, static frontend | Versioning enabled, CloudFront OAC, Intelligent Tiering | $20–$60 |
| **S3 — survey-platform-reports** | Generated PDF/CSV/XLSX reports | Private, presigned URL access, Intelligent Tiering, 90-day lifecycle | $10–$30 |
| **CloudFront** | CDN for static assets, survey embed widget, API caching | 2 distributions, price class all, custom domain + ACM | $50–$150 |
| **Route 53** | DNS hosting, health checks, failover routing | 1 hosted zone, ~10 records, 5 health checks | $5–$15 |
| **WAF** | Web application firewall | Attached to CloudFront + ALB; OWASP managed rule group, rate limit rule | $80–$150 |
| **ACM (Certificate Manager)** | TLS/SSL certificates | Wildcard cert `*.survey-platform.com`, auto-renewal | $0 (free) |
| **Kinesis Data Streams** | Real-time response ingestion pipeline | 4 shards, 24-hour data retention, enhanced fan-out | $80–$150 |
| **Lambda** | Stateless analytics processor consuming Kinesis | `analytics-processor`, 512 MB, 60s timeout, 5 concurrent | $10–$40 |
| **SES (Simple Email Service)** | Transactional email: survey invitations, magic links, reports | Sending domain verified, DKIM + DMARC configured | $20–$80 |
| **SNS** | Fan-out notifications: webhook triggers, internal alerts | Topics per event type, CloudWatch alarm integration | $5–$20 |
| **SQS** | Dead-letter queues for Celery, webhook retry queues | Standard queues, 14-day retention, DLQ after 3 attempts | $5–$15 |
| **Secrets Manager** | Credentials: DB passwords, OAuth client secrets, API keys | Auto-rotation every 30 days for DB credentials | $20–$50 |
| **Parameter Store (SSM)** | Non-secret application configuration (feature flags, URLs) | Standard tier for most; Advanced tier for large payloads | $5–$10 |
| **CloudWatch** | Metrics, logs, alarms, dashboards, Logs Insights | Custom dashboards per service; 90-day log retention | $100–$200 |
| **X-Ray** | Distributed tracing across FastAPI services and Lambda | Sampling rate 5% prod, 100% staging | $20–$50 |
| **ECR (Elastic Container Registry)** | Private Docker image registry | 1 repository per service, lifecycle: prune images >90 days | $10–$30 |
| **VPC** | Network isolation, private subnets, security groups | 1 VPC, 6 subnets (2 public, 2 private app, 2 private data) | $10–$30 |
| **IAM** | Service identity and access control | 1 role per ECS task + execution role, OIDC for CI/CD | $0 (free) |
| **KMS (Key Management Service)** | Encryption key management | CMKs for RDS, S3, DynamoDB, Secrets Manager | $15–$40 |

**Estimated Total Monthly Cost:** $2,505–$4,200 at moderate load (10,000 daily active respondents).

---

## Network Architecture

### VPC Design

| Component | Value |
|---|---|
| VPC CIDR | `10.0.0.0/16` |
| Region | `us-east-1` |
| Availability Zones | `us-east-1a`, `us-east-1b` |
| DNS Hostnames | Enabled |
| DNS Resolution | Enabled |
| Flow Logs | Enabled → CloudWatch Logs |

### Subnet Layout

| Subnet Name | AZ | CIDR | Tier | Contains |
|---|---|---|---|---|
| `public-1a` | us-east-1a | `10.0.1.0/24` | Public | ALB, NAT Gateway A, (Bastion) |
| `public-1b` | us-east-1b | `10.0.2.0/24` | Public | ALB (multi-AZ), NAT Gateway B |
| `private-app-1a` | us-east-1a | `10.0.10.0/24` | Private App | ECS Fargate tasks |
| `private-app-1b` | us-east-1b | `10.0.11.0/24` | Private App | ECS Fargate tasks |
| `private-data-1a` | us-east-1a | `10.0.20.0/24` | Private Data | RDS Primary, ElastiCache |
| `private-data-1b` | us-east-1b | `10.0.21.0/24` | Private Data | RDS Standby, ElastiCache replicas |

### Security Groups

| Security Group | Inbound | Outbound |
|---|---|---|
| `alb-sg` | 0.0.0.0/0 → TCP 443; 0.0.0.0/0 → TCP 80 | `ecs-sg` → TCP 8000–8099 |
| `ecs-survey-sg` | `alb-sg` → TCP 8000 | `rds-sg` → TCP 5432; `redis-sg` → TCP 6379; 0.0.0.0/0 → TCP 443 (HTTPS egress) |
| `ecs-response-sg` | `alb-sg` → TCP 8001 | `rds-sg` → TCP 5432; `redis-sg` → TCP 6379; `kinesis-vpce` → TCP 443 |
| `ecs-auth-sg` | `alb-sg` → TCP 8002 | `rds-sg` → TCP 5432; `redis-sg` → TCP 6379; 0.0.0.0/0 → TCP 443 |
| `ecs-analytics-sg` | `alb-sg` → TCP 8003 | `rds-sg` → TCP 5432; `dynamo-vpce` → TCP 443; `redis-sg` → TCP 6379 |
| `ecs-dist-sg` | `alb-sg` → TCP 8004 | `redis-sg` → TCP 6379; 0.0.0.0/0 → TCP 443 (SES) |
| `ecs-report-sg` | `alb-sg` → TCP 8005 | `rds-sg` → TCP 5432; `s3-vpce` → TCP 443; `dynamo-vpce` → TCP 443 |
| `ecs-webhook-sg` | `alb-sg` → TCP 8006 | 0.0.0.0/0 → TCP 443 (external webhook targets) |
| `rds-sg` | `ecs-*-sg` → TCP 5432; `lambda-sg` → TCP 5432 | None |
| `redis-sg` | `ecs-*-sg` → TCP 6379 | None |
| `lambda-sg` | None (Lambda triggers via Kinesis) | `rds-sg` → TCP 5432; `dynamo-vpce` → TCP 443 |

---

## Security Architecture

### Encryption at Rest

| Resource | Encryption Method | Key |
|---|---|---|
| RDS PostgreSQL | AES-256 via AWS KMS | CMK `survey-platform/rds` |
| S3 — assets bucket | SSE-KMS | CMK `survey-platform/s3-assets` |
| S3 — reports bucket | SSE-KMS | CMK `survey-platform/s3-reports` |
| DynamoDB | AES-256 via AWS KMS | CMK `survey-platform/dynamodb` |
| ElastiCache Redis | In-transit TLS + at-rest encryption | AWS managed key |
| ECS Task Secrets | Secrets Manager + KMS | CMK `survey-platform/secrets` |
| CloudWatch Logs | KMS log group encryption | CMK `survey-platform/logs` |

### Encryption in Transit

- All external traffic is **TLS 1.3** only (TLS 1.0 and 1.1 disabled via CloudFront security policy `TLSv1.2_2021`).
- ALB to ECS communication uses HTTPS (self-signed or ACM private CA cert for internal traffic).
- ECS to RDS uses SSL enforced via `rds.force_ssl=1` PostgreSQL parameter.
- ECS to ElastiCache uses TLS (`--tls` flag; Redis `tls-port 6380`).
- ECS to MongoDB Atlas uses TLS 1.2+ with certificate pinning on the driver.
- Lambda to DynamoDB uses VPC endpoint (no public internet traversal).

### WAF Rules

| Rule Group | Action | Purpose |
|---|---|---|
| `AWSManagedRulesCommonRuleSet` | Block | OWASP Top 10: SQLi, XSS, RFI, LFI |
| `AWSManagedRulesSQLiRuleSet` | Block | SQL injection patterns |
| `AWSManagedRulesKnownBadInputsRuleSet` | Block | Log4j, Spring4Shell, SSRF patterns |
| `AWSManagedRulesBotControlRuleSet` | Count (then block) | Bot traffic identification |
| Custom: Rate Limit — API | Block | >500 requests per 5 minutes per IP |
| Custom: Rate Limit — Survey Submit | Block | >10 submissions per minute per IP |
| Custom: Geo Block | Block | Countries listed in compliance policy |
| Custom: Survey Embed Allow | Allow | CloudFront embedded widget bypass |

### Secrets Rotation Policy

| Secret | Rotation Period | Rotation Lambda |
|---|---|---|
| RDS master password | 30 days | `SecretsManagerRDSPostgreSQLRotationSingleUser` |
| RDS app user password | 30 days | `SecretsManagerRDSPostgreSQLRotationSingleUser` |
| MongoDB Atlas API key | 90 days | Custom Lambda (`rotate-mongodb-key`) |
| OAuth client secrets | 180 days | Manual (coordinated with SSO providers) |
| JWT signing key | 90 days | Custom Lambda (`rotate-jwt-key`) with key overlap period |
| SES SMTP credentials | 90 days | Custom Lambda |

### IAM Least-Privilege Roles

Each ECS service has a dedicated Task Role granting only what the service requires:

| Role | Key Permissions |
|---|---|
| `ecs-survey-service-task-role` | `s3:PutObject` (assets), `secretsmanager:GetSecretValue`, `xray:PutTraceSegments` |
| `ecs-response-service-task-role` | `kinesis:PutRecord`, `kinesis:PutRecords`, `secretsmanager:GetSecretValue` |
| `ecs-analytics-service-task-role` | `dynamodb:Query`, `dynamodb:GetItem`, `dynamodb:BatchGetItem` |
| `ecs-report-service-task-role` | `s3:PutObject`, `s3:GetObject` (reports), `dynamodb:Query` |
| `ecs-auth-service-task-role` | `secretsmanager:GetSecretValue`, `ses:SendEmail` |
| `ecs-dist-service-task-role` | `ses:SendEmail`, `sns:Publish`, `s3:GetObject` (assets) |
| `ecs-webhook-service-task-role` | `secretsmanager:GetSecretValue`, `sqs:SendMessage` (DLQ) |
| `lambda-analytics-role` | `kinesis:GetRecords`, `dynamodb:PutItem`, `dynamodb:BatchWriteItem`, `logs:CreateLogGroup` |

---

## High Availability and Disaster Recovery

### Multi-AZ Deployment

Every production service runs tasks in both `us-east-1a` and `us-east-1b`. The ALB distributes
traffic across both AZs with cross-zone load balancing enabled. ECS placement strategy:
`spread` across AZs, then `binpack` on CPU within each AZ.

### RDS Automated Failover

RDS Multi-AZ maintains a synchronous standby replica in `us-east-1b`. Failover is automatic
and DNS-based:
- **Trigger:** Primary instance becomes unavailable (health check failure, AZ outage).
- **Failover time:** Typically 60–120 seconds; target SLA <60 seconds with Multi-AZ.
- **No application code change required** — CNAME of the RDS endpoint updates to standby.
- **Post-failover:** Original primary becomes new standby after recovery.

### ElastiCache Redis Cluster Failover

With cluster mode and 3 shards (each with 1 primary + 1 replica):
- Primary node failure triggers automatic promotion of the replica within ~30 seconds.
- Data in transit during failover may be lost (Redis is not a durable store — acceptable
  for cache and session data).
- Application uses `cluster=True` mode Redis client with read-from-replica for read-heavy
  workloads.

### Recovery Objectives

| Metric | Target |
|---|---|
| **RTO (Recovery Time Objective)** | 4 hours (full region failure scenario) |
| **RPO (Recovery Point Objective)** | 1 hour |
| **MTTR (Mean Time to Recovery — AZ failure)** | <15 minutes |
| **RTO — Service-level degradation** | <5 minutes (ECS auto-recovery) |

### Backup Schedule

| Resource | Backup Method | Frequency | Retention | Cross-Region |
|---|---|---|---|---|
| RDS PostgreSQL | Automated snapshots + PITR | Daily at 03:00 UTC | 30 days | Yes — us-west-2 (AWS Backup) |
| DynamoDB | On-demand backup + PITR | Continuous (PITR enabled) | 35 days | Yes — global tables |
| S3 — reports | Versioning + cross-region replication | Continuous | 90 days | Yes — us-west-2 |
| S3 — assets | Versioning | Continuous | 30 days versions | No (recoverable from build) |
| ElastiCache | Automatic snapshots | Daily at 04:00 UTC | 5 days | No |
| MongoDB Atlas | Atlas automated backups | Daily | 30 days | Atlas cross-region snapshot |

### Cross-Region DR Runbook (Summary)

In the event of a full `us-east-1` failure:
1. Promote RDS read replica in `us-west-2` to standalone primary.
2. Deploy ECS task definitions to `us-west-2` ECS cluster (pre-provisioned, zero tasks).
3. Update Route 53 failover routing records to point to `us-west-2` ALB.
4. Estimated activation time: 2–4 hours (within RTO).

---

## Cost Optimization

### Compute

- **ECS Fargate Compute Savings Plan** (1-year, no upfront): Covers 70% of baseline Fargate
  vCPU/memory usage, saving approximately 20% vs on-demand.
- **Celery Worker Spot Strategy:** `report-celery` and `distribution-celery` tasks use
  Fargate Spot with a fallback to on-demand if Spot capacity is interrupted. Celery's
  `acks_late=True` and task retry ensure idempotent safe interruption.

### Database

- **RDS Reserved Instance** (`db.r6g.xlarge`, 1-year, partial upfront): ~40% savings vs
  on-demand pricing.
- **Read Replica Sizing:** Read replicas use `db.r6g.large` (smaller than primary) since
  they serve analytical read queries only.
- **ElastiCache Reserved Nodes** (`cache.r6g.large` × 6, 1-year): ~30% savings.

### Storage

- **S3 Intelligent Tiering** enabled on both buckets. Objects >128 KB are automatically
  transitioned to Frequent Access → Infrequent Access → Archive Instant Access tiers.
- **S3 Lifecycle Rules:**
  - `survey-platform-reports`: Move to Glacier Instant Retrieval after 90 days; expire after 2 years.
  - `survey-platform-assets`: Delete non-current versions after 30 days.
- **ECR Lifecycle:** Delete untagged images immediately; retain only the 10 most recent tagged images per repo.

### Networking

- NAT Gateway charges are minimized by routing S3, DynamoDB, ECR, and Secrets Manager
  traffic through **VPC Gateway/Interface Endpoints** (no NAT traversal for these services).
- CloudFront compression (gzip + Brotli) reduces data transfer charges from origin.

### Monitoring Cost Controls

- CloudWatch detailed metrics (1-minute resolution) enabled only for `response-service` and
  `rds-sg`; all others use 5-minute standard metrics.
- Log retention set to 90 days; debug-level logs disabled in production (INFO minimum).
- X-Ray sampling set to 5% in production to control trace storage costs.

---

## Observability Stack

### CloudWatch Dashboards

| Dashboard | Key Widgets |
|---|---|
| `survey-platform-overview` | ECS task count, ALB request rate, RDS connections, Redis memory, error rate 5xx |
| `survey-platform-response-pipeline` | Kinesis shard iterator lag, Lambda invocations, Lambda errors, DynamoDB write latency |
| `survey-platform-database` | RDS CPU, IOPS, free storage, replication lag, slow query count |
| `survey-platform-auth` | Login success/failure rate, magic link delivery rate, OAuth callback errors |
| `survey-platform-cost` | AWS Cost Explorer embedded widget, daily spend by service |

### CloudWatch Alarms (Critical)

| Alarm | Metric | Threshold | Action |
|---|---|---|---|
| ALB 5xx Error Rate | `HTTPCode_ELB_5XX_Count` | >50/min for 2 min | SNS → PagerDuty P2 |
| RDS CPU | `CPUUtilization` | >85% for 5 min | SNS → PagerDuty P2 |
| RDS Free Storage | `FreeStorageSpace` | <50 GB | SNS → PagerDuty P1 |
| ECS Task Stopped | `RunningTaskCount` | < min capacity | SNS → PagerDuty P1 |
| Kinesis Iterator Age | `GetRecords.IteratorAgeMilliseconds` | >60,000 ms | SNS → PagerDuty P2 |
| Redis Memory | `DatabaseMemoryUsagePercentage` | >80% | SNS → Slack alert |
| Lambda Errors | `Errors` | >10/min | SNS → PagerDuty P2 |

### X-Ray Distributed Tracing

All FastAPI services instrument with `aws-xray-sdk-python`. The `XRayMiddleware` captures:
- HTTP request/response metadata (status code, URL, user-agent).
- Downstream calls to RDS (via SQLAlchemy patch), Redis (via redis-py patch), S3, and SES.
- Custom subsegments for business logic: survey validation, response scoring, report generation.

Trace maps are accessible in the X-Ray console, showing service dependencies and P50/P95/P99
latency for each service hop.

### CloudWatch Logs Insights Queries

```
# P95 API response latency by endpoint (last 1 hour)
fields @timestamp, endpoint, duration_ms
| filter service = "survey-service"
| stats pct(duration_ms, 95) as p95_latency by endpoint
| sort p95_latency desc
| limit 20

# Error rate by service (last 24 hours)
fields @timestamp, service, level, message
| filter level = "ERROR"
| stats count() as error_count by service
| sort error_count desc

# Failed survey submissions (last 1 hour)
fields @timestamp, survey_id, user_id, error_code, message
| filter service = "response-service" and level = "ERROR"
| filter ispresent(survey_id)
| sort @timestamp desc
| limit 100

# Kinesis consumer lag tracking
fields @timestamp, shard_id, iterator_age_ms
| filter service = "analytics-lambda"
| stats max(iterator_age_ms) as max_lag by shard_id
| sort max_lag desc
```

---

## Operational Policy Addendum

### 1. Infrastructure as Code Governance

All AWS resources are provisioned and managed exclusively through **Terraform** (v1.6+).
Terraform modules are organized per service layer (`vpc`, `ecs`, `rds`, `redis`, `s3`,
`waf`, `cdn`). State is stored in `s3://survey-platform-tfstate-<account>` with
DynamoDB locking table `survey-platform-tf-locks`.

- **Drift Detection:** Weekly scheduled `terraform plan` run via GitHub Actions; any detected
  drift creates a GitHub Issue and pages the infra on-call.
- **Module Versioning:** All internal modules are pinned by Git tag. External provider
  versions are locked in `versions.tf`.
- **Sensitive Outputs:** Marked as `sensitive = true`; never printed in CI/CD logs.
- **Workspace Strategy:** Separate Terraform workspaces for `staging` and `production`.

### 2. Compliance and Data Governance

The platform handles survey responses that may contain PII. Compliance obligations:

- **GDPR (EU):** Data minimization enforced; respondent email stored separately from
  response data with a reference token. Right-to-erasure endpoint available.
- **CCPA (California):** Opt-out webhook for data deletion requests integrated with the
  `webhook-service`.
- **Data Residency:** All production data resides in `us-east-1`. EU customer data isolated
  in a separate deployment (see `survey-platform-eu` environment).
- **Audit Logs:** All `DELETE` and administrative operations are logged to an immutable
  CloudTrail trail stored in a separate S3 bucket with Object Lock (WORM, 7-year retention).

### 3. Capacity Planning

Capacity reviews are conducted quarterly based on CloudWatch metric trends:

- **Response Service** is the most write-intensive service. Capacity target: 5,000 responses/second
  peak throughput with <200ms P95 latency.
- **Kinesis Shards:** Each shard supports 1 MB/s write. 4 shards = 4 MB/s = ~10,000 small
  events/second. Shard count reviewed if `PutRecords.ThrottledRecords` exceeds 1% for 3 days.
- **RDS Connections:** PgBouncer pooling limits to 500 active connections. If P95 wait time
  exceeds 5ms for connection acquisition, evaluate vertical scale or additional replicas.
- **MongoDB Atlas:** M30 supports ~4,000 operations/second. Upgrade path: M30 → M50 → M80
  (no downtime with Atlas live migration).

### 4. Security Operations

- **Penetration Testing:** Annual third-party penetration test against staging environment;
  findings tracked to resolution in security Jira board.
- **Vulnerability Scanning:** ECR images scanned on push via **Amazon Inspector**; CRITICAL
  vulnerabilities block deployment via CI/CD gate. HIGH vulnerabilities create Jira tickets.
- **SAST/DAST:** `bandit` (Python SAST) and `eslint-plugin-security` run in CI/CD pipeline.
  OWASP ZAP DAST scan runs weekly against staging.
- **Secret Scanning:** `trufflehog` runs in GitHub Actions on every push to detect
  accidentally committed secrets. Any detection fails the build and triggers a P1 incident.
- **SOC 2 Type II Readiness:** Evidence collection for CC6 (logical access) and CC7
  (system operations) controls is automated via AWS Config rules and monthly reports.
