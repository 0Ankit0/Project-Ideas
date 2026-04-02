# C4 Context and Container Diagram — Government Services Portal

## 1. Overview of the C4 Model

The C4 model (Context, Container, Component, Code) provides a hierarchical set of software architecture diagrams that progressively zoom in on the system. This document covers the first two levels:

- **Level 1 — Context Diagram:** Shows the system as a single black box and its relationships with the people and external systems that interact with it. Suitable for communicating with non-technical stakeholders, department heads, and project sponsors.
- **Level 2 — Container Diagram:** Zooms into the Government Services Portal system and shows the separately deployable units (containers) and how they communicate. Suitable for architects, senior engineers, DevOps, and security reviewers.

Levels 3 (Component) and 4 (Code) are covered in `detailed-design/component-diagrams.md` and the codebase itself.

**Key conventions used in this document:**
- Solid lines represent synchronous communication.
- Dashed lines represent asynchronous communication (event-driven or queue-based).
- All external system dependencies are highlighted with `System_Ext` notation.
- All containers within the portal boundary run on AWS infrastructure.

---

## 2. Level 1: C4 Context Diagram

```mermaid
C4Context
  title System Context — Government Services Portal

  Person(citizen, "Citizen", "A resident of the province who needs to apply for government services such as certificates, licences, permits, or social welfare schemes.")
  Person(field_officer, "Field Officer", "A government employee responsible for reviewing, verifying, and processing citizen applications within their department.")
  Person(dept_head, "Department Head", "A senior government official who oversees a department, configures services, approves high-value applications, and monitors SLA compliance.")
  Person(super_admin, "Super Admin", "A platform administrator responsible for system configuration, user management, fee schedules, and cross-department oversight.")
  Person(auditor, "Auditor", "A compliance officer with read-only access to all transactions, audit logs, payment records, and SLA reports for accountability and audit purposes.")

  System(portal, "Government Services Portal", "A digital platform enabling citizens to discover, apply for, track, and receive government services entirely online. Handles identity verification, document management, fee payment, workflow routing, and certificate issuance.")

  System_Ext(digilocker, "Nepal Document Wallet (NDW)", "National digital document wallet operated by MeitY. Citizens use it to share verified documents. The portal pushes issued certificates to a citizen's Nepal Document Wallet (NDW) account.")
  System_Ext(aadhaar, "NID / NASC (National Identity Management Centre)", "Unique Identification Authority of Nepal. Provides OTP-based identity authentication and e-KYC demographic data fetch using the citizen's NID number.")
  System_Ext(paygov, "ConnectIPS / Razorpay Govt", "Integrated Government Online Payment Platform. Processes fee payments for government services via net banking, eSewa/Khalti/ConnectIPS, credit/debit cards, and generates payment receipts.")
  System_Ext(sms_gateway, "SMS Gateway (MSG91)", "Third-party SMS delivery service used to send OTP codes, application status updates, and service notifications to citizens via mobile number.")
  System_Ext(ses, "AWS SES", "Amazon Simple Email Service used to send transactional emails: OTP codes, acknowledgement emails, approval/rejection notices, and certificate delivery notifications.")
  System_Ext(legacy_db, "Legacy Govt Database (NIC)", "Existing province government databases maintained by NIC. The portal reads legacy records (land records, ration card data, birth records) to pre-fill application forms and validate eligibility.")

  Rel(citizen, portal, "Discovers services, submits applications, uploads documents, makes payments, tracks status, downloads certificates", "HTTPS (Web Browser / Mobile PWA)")
  Rel(field_officer, portal, "Reviews applications, requests clarifications, approves or rejects applications, verifies offline payments", "HTTPS (Staff Portal)")
  Rel(dept_head, portal, "Configures services and SLAs, reviews escalated applications, monitors department performance", "HTTPS (Staff Portal)")
  Rel(super_admin, portal, "Manages departments, users, fee schedules, system configuration, and platform health", "HTTPS (Admin Console)")
  Rel(auditor, portal, "Reads audit logs, generates compliance reports, monitors SLA adherence and payment reconciliation", "HTTPS (Admin Console)")

  Rel(portal, digilocker, "Pushes issued digital certificates; pulls citizen-shared documents", "HTTPS / OAuth 2.0")
  Rel(portal, aadhaar, "Initiates NID OTP for authentication; fetches e-KYC demographic data with consent", "HTTPS / AUA API")
  Rel(portal, paygov, "Creates payment orders; receives payment callbacks; queries payment status", "HTTPS / REST")
  Rel(portal, sms_gateway, "Sends OTP SMS, status update SMS, and bulk notification SMS", "HTTPS / REST API")
  Rel(portal, ses, "Sends transactional emails via SMTP/TLS or SES API", "HTTPS / SMTP")
  Rel(portal, legacy_db, "Reads citizen reference data for form pre-fill and eligibility verification", "HTTPS / SFTP (read-only)")
```

---

## 3. Level 2: C4 Container Diagram

```mermaid
C4Container
  title Container Diagram — Government Services Portal

  Person(citizen, "Citizen", "Applies for services via web or mobile browser")
  Person(staff, "Staff (Officer / Head / Admin / Auditor)", "Manages applications via staff portal")

  System_Boundary(portal_boundary, "Government Services Portal") {

    Container(nextjs_citizen, "Citizen Web App", "Next.js 14, TypeScript, Tailwind CSS", "Server-side rendered citizen-facing portal. Handles service discovery, application forms, document upload, payment flow, and status tracking. WCAG 2.1 AA compliant. Deployed on ECS Fargate behind CloudFront CDN.")

    Container(nextjs_admin, "Staff Admin Console", "Next.js 14, TypeScript, Tailwind CSS", "Internal portal for Field Officers, Department Heads, Super Admins, and Auditors. Application review queue, workflow management, configuration, reporting. Deployed on ECS Fargate, accessible only from within VPC or via VPN.")

    Container(django_api, "Django API Server", "Python 3.11, Django 4.x, Django REST Framework, Gunicorn + Uvicorn", "Core application server providing all REST API endpoints for both frontends. Implements business logic for identity, applications, payments, documents, certificates, grievances, and admin. Runs on ECS Fargate with PgBouncer sidecar for connection pooling.")

    Container(celery_worker, "Celery Worker Fleet", "Python 3.11, Celery 5.x, Redis 7 broker", "Asynchronous task workers organised into priority queues: high (OTP delivery, payment callbacks), default (notifications, status updates), document (virus scanning, PDF generation, DSC signing), bulk (reports, archival, reconciliation). Deployed on ECS Fargate with separate task definitions per queue.")

    Container(celery_beat, "Celery Beat Scheduler", "Python 3.11, Celery Beat, django-celery-beat (DB scheduler)", "Cron-like scheduler that publishes periodic tasks: SLA breach checks (every 15 minutes), payment reconciliation (twice daily), archival job (nightly), report generation (daily). Runs as a single ECS Fargate task (not horizontally scaled).")

    ContainerDb(postgres, "PostgreSQL Database", "PostgreSQL 15, AWS RDS Multi-AZ, db.r6g.xlarge", "Primary relational database for all application data: citizen profiles, applications, workflow states, payments, documents metadata, certificates, grievances, audit logs. Row-Level Security enforces department isolation. Encrypted at rest with AES-256.")

    ContainerDb(redis, "Redis Cache & Queue", "Redis 7, AWS ElastiCache Cluster Mode, cache.r6g.large × 3 shards", "Serves three roles: (1) Celery broker for async task queues, (2) application cache for service catalogue, eligibility rules, and session data, (3) rate-limiting counters and distributed locks. Keyspace: celery:*, session:*, cache:*, ratelimit:*, lock:*.")

    Container(s3_store, "Document & Asset Store", "AWS S3, KMS-CMK encryption, S3 Object Lock (WORM)", "Stores citizen-uploaded documents, generated PDF certificates, application acknowledgements, and report exports. Versioning enabled. Pre-signed URLs (15-minute TTL) used for direct browser upload and download without proxying through the API. Lifecycle: active → Standard-IA (90 days) → Glacier (2 years) → permanent archive (7 years).")
  }

  System_Ext(digilocker, "Nepal Document Wallet (NDW) API", "MeitY national document wallet")
  System_Ext(aadhaar, "NID NASC (National Identity Management Centre) API", "OTP auth and e-KYC")
  System_Ext(paygov, "ConnectIPS / Razorpay", "Government payment gateway")
  System_Ext(sms_gw, "SMS Gateway", "OTP and notification SMS")
  System_Ext(ses, "AWS SES", "Transactional email")

  Rel(citizen, nextjs_citizen, "Browses and interacts with the portal", "HTTPS")
  Rel(staff, nextjs_admin, "Manages applications and configuration", "HTTPS")

  Rel(nextjs_citizen, django_api, "Calls all API endpoints (auth, service, application, payment, document, certificate)", "HTTPS / JSON REST")
  Rel(nextjs_admin, django_api, "Calls admin and management API endpoints", "HTTPS / JSON REST")

  Rel(django_api, postgres, "Reads and writes all domain data using Django ORM via PgBouncer connection pool", "TCP 5432")
  Rel(django_api, redis, "Reads/writes cache, creates/manages sessions, enqueues Celery tasks, acquires distributed locks", "TCP 6379")
  Rel(django_api, s3_store, "Generates pre-signed upload/download URLs; writes generated PDFs and acknowledgements", "HTTPS (AWS SDK)")
  Rel(django_api, aadhaar, "Initiates OTP request; verifies OTP; fetches e-KYC data", "HTTPS")
  Rel(django_api, paygov, "Creates payment orders; verifies webhook signatures; queries transaction status", "HTTPS")
  Rel(django_api, digilocker, "Exchanges OAuth token; pulls citizen documents; initiates certificate push", "HTTPS")

  Rel(celery_worker, postgres, "Reads and updates application, payment, notification, and certificate records", "TCP 5432")
  Rel(celery_worker, redis, "Subscribes to task queues; updates task province; acquires locks for idempotency", "TCP 6379")
  Rel(celery_worker, s3_store, "Downloads citizen documents for virus scan; uploads signed PDFs and certificates", "HTTPS (AWS SDK)")
  Rel(celery_worker, sms_gw, "Dispatches OTP SMS and status notification SMS", "HTTPS")
  Rel(celery_worker, ses, "Sends transactional and notification emails", "HTTPS / SMTP TLS")
  Rel(celery_worker, digilocker, "Pushes issued certificates to citizen Nepal Document Wallet (NDW) account", "HTTPS")

  Rel(celery_beat, redis, "Publishes scheduled tasks to Celery queues", "TCP 6379")
```

---

## 4. Container Descriptions

| Container | Technology | Primary Responsibility | Team Owner | Horizontal Scaling |
|---|---|---|---|---|
| **Citizen Web App** | Next.js 14, TypeScript, Tailwind CSS, React 18 | Server-side rendering of citizen-facing pages; form orchestration; real-time application status via polling; accessibility (WCAG 2.1 AA); multilingual support (Hindi, English, regional language) | Frontend Team | ECS Fargate auto-scaling on ALB RequestCount; min 2 / max 20 tasks |
| **Staff Admin Console** | Next.js 14, TypeScript, Tailwind CSS, React Table | Application review queue; workflow action UI; department configuration; SLA and compliance dashboards; report export | Frontend Team | ECS Fargate auto-scaling; min 2 / max 10 tasks; VPN-restricted |
| **Django API Server** | Python 3.11, Django 4.x, DRF, Gunicorn, Uvicorn, PgBouncer (sidecar) | All business logic; REST API for both frontends; authentication (JWT, NID OTP); workflow state transitions; fee calculation; payment order creation; document metadata management | Backend Team | ECS Fargate auto-scaling on CPU (65%) and RequestCount; min 3 / max 30 tasks |
| **Celery Worker Fleet** | Python 3.11, Celery 5.x, four separate task definitions per queue | Async processing: document virus scan, PDF generation, DSC signing, notification dispatch, payment reconciliation, Nepal Document Wallet (NDW) sync, report generation, SLA checks, archival | Backend / Platform Team | Separate ECS Fargate auto-scaling per queue based on Redis queue depth CloudWatch metric |
| **Celery Beat Scheduler** | Python 3.11, Celery Beat, django-celery-beat | Cron scheduling: SLA breach detection, reconciliation, archival, nightly report | Backend / Platform Team | Single task — NOT horizontally scaled (uses distributed lock to prevent duplicate scheduling) |
| **PostgreSQL Database** | PostgreSQL 15, RDS Multi-AZ, db.r6g.xlarge (primary + 1 read replica) | Persistent store for all domain entities: citizens, applications, workflow steps, payments, documents metadata, certificates, audit events | Data / DBA Team | Vertical (instance class); read replica for read-heavy queries; no horizontal sharding at initial scale |
| **Redis Cache & Queue** | Redis 7, ElastiCache Cluster Mode, 3 shards × 1 replica | Celery broker (task queues + results), session store (citizen + staff), application cache (service catalogue, eligibility), rate limiting, distributed locks | Platform / Backend Team | ElastiCache Cluster Mode with 3 shards; shard scaling via AWS console; key namespace sharding |
| **Document & Asset Store** | AWS S3, KMS-CMK (separate keys per data classification), S3 Object Lock | Citizen uploaded documents, generated certificates, acknowledgement PDFs, exported reports, application attachments | Platform / Security Team | S3 is infinitely scalable; Object Lock prevents deletion; lifecycle policies for cost management |

---

## 5. Communication Protocols

| Source Container | Target Container | Protocol | Port | Auth Method | Data Format | Notes |
|---|---|---|---|---|---|---|
| Citizen Web App | Django API Server | HTTPS REST | 443 | JWT Bearer Token (access token 15 min TTL) | JSON | All API calls include `X-Request-ID` header for distributed tracing |
| Staff Admin Console | Django API Server | HTTPS REST | 443 | JWT Bearer Token (staff role, 8 hr TTL) | JSON | Staff JWT payload includes `role`, `department_id`, `permissions[]` claims |
| Django API Server | PostgreSQL | TCP/TLS | 5432 | PgBouncer authenticates via scram-sha-256; application uses role `portal_app` | PostgreSQL wire protocol | Connection pooling: transaction mode, max 200 pooled connections |
| Django API Server | Redis | TCP (TLS in production) | 6379 | AUTH password + TLS client cert on ElastiCache | Redis RESP protocol | Keyspace isolation by prefix; separate DB indexes for cache/session/broker |
| Django API Server | AWS S3 | HTTPS | 443 | IAM Task Role (ECS) — no long-lived credentials | AWS SDK v2 (Python boto3) | Pre-signed URLs for client-direct upload; 15-minute TTL |
| Django API Server | NID NASC (National Identity Management Centre) | HTTPS | 443 | AUA credentials (client cert + API key), request signed with RSA-2048 | XML (AUA format) / JSON (newer API) | Credentials stored in AWS Secrets Manager |
| Django API Server | ConnectIPS / Razorpay | HTTPS | 443 | HMAC-SHA256 webhook signature; API key + secret from Secrets Manager | JSON | Idempotency key sent on every order creation request |
| Django API Server | Nepal Document Wallet (NDW) | HTTPS | 443 | OAuth 2.0 Authorization Code Flow; access token per citizen session | JSON | Token refresh handled transparently; citizen must consent on first use |
| Celery Worker | PostgreSQL | TCP/TLS | 5432 | Same PgBouncer pool as API server | PostgreSQL wire protocol | Workers use a separate PgBouncer pool to avoid competing with API |
| Celery Worker | Redis | TCP (TLS) | 6379 | AUTH password + TLS | Redis RESP | Workers subscribe to named queues: high, default, document, bulk |
| Celery Worker | S3 | HTTPS | 443 | IAM Task Role (separate ECS task role with S3 write permission) | AWS SDK boto3 | Worker task role has KMS decrypt permission for reading citizen docs |
| Celery Worker | SMS Gateway (MSG91) | HTTPS | 443 | API key from Secrets Manager, TLS 1.3 | JSON | Retry 3× with exponential backoff; fallback to secondary Nepal Telecom / Sparrow SMS gateway |
| Celery Worker | AWS SES | HTTPS / SMTP TLS | 443 / 587 | IAM Task Role (ses:SendEmail permission) | MIME email / JSON (SES API) | DKIM signed, SPF configured; bounce and complaint webhooks to API |
| Celery Worker | Nepal Document Wallet (NDW) | HTTPS | 443 | OAuth 2.0 bearer token (stored in PostgreSQL per citizen) | JSON | Push certificate to citizen's Nepal Document Wallet (NDW) namespace |
| Celery Beat | Redis | TCP (TLS) | 6379 | AUTH password | Redis RESP | Reads schedule from PostgreSQL via django-celery-beat; publishes to broker |
| ALB | Django API Server | HTTP (internal) | 8000 | None (ALB listener performs TLS termination; internal VPC traffic) | HTTP/1.1 | Health check: `GET /api/health/` — expects 200 within 5 seconds |
| CloudFront | ALB Frontend | HTTPS | 443 | Origin Access Policy (OAP) with shared secret header `X-CloudFront-Secret` | HTTPS | Viewer Protocol Policy: Redirect HTTP to HTTPS |

---

## 6. Container Security Boundaries

The system is divided into three security zones enforced by AWS VPC security groups and network ACLs:

### Zone 1: Public DMZ (Internet-Facing)
CloudFront distributions, Route 53 DNS, and AWS WAF operate in AWS-managed infrastructure outside the VPC. No application containers reside here. WAF rules enforce: rate limiting (100 req/sec/IP for API, 500 req/sec/IP for static assets), OWASP Core Rule Set, AWS Managed IP Reputation list, SQL injection protection, and geofencing (requests from embargoed countries are blocked). Shield Advanced provides automatic DDoS response at Layers 3, 4, and 7.

### Zone 2: Application Tier (Private Subnets — App VPC)
All ECS Fargate tasks (Citizen Web App, Admin Console, Django API, Celery Workers, Celery Beat) run in private subnets. They have no inbound internet access; they receive traffic exclusively from ALBs. Outbound internet access for calling external APIs (NID, ConnectIPS, Nepal Document Wallet (NDW), SMS Gateway, SES) is routed through a NAT Gateway with a fixed Elastic IP address — this IP is registered with NASC (National Identity Management Centre) and ConnectIPS as the authorised source IP for API calls.

Security group rules: API containers accept inbound 8000 only from ALB security group. Celery workers accept no inbound connections. All containers accept outbound 443 (HTTPS) and TCP 5432/6379 to Data Tier security groups only.

### Zone 3: Data Tier (Isolated Private Subnets — Data VPC)
RDS PostgreSQL and ElastiCache Redis reside in isolated private subnets with no route to the internet. Security groups accept inbound TCP 5432 / 6379 only from App Tier security groups. RDS has deletion protection enabled. ElastiCache has at-rest encryption and in-transit TLS enabled. Backups are encrypted and stored in a separate S3 bucket with cross-account replication to the DR account.

### IAM Boundaries
Each ECS task has a dedicated IAM Task Role with least-privilege permissions:
- **API Task Role:** `s3:GetObject`, `s3:PutObject` (specific bucket), `kms:Decrypt` (specific key), `secretsmanager:GetSecretValue` (specific secret ARNs).
- **Celery Document Task Role:** `s3:GetObject`, `s3:PutObject`, `kms:Decrypt`, `kms:GenerateDataKey`.
- **Celery Worker Task Role:** `ses:SendEmail`, `secretsmanager:GetSecretValue`.
- No task role has `s3:DeleteObject`, `iam:*`, or EC2 management permissions.

---

## 7. Operational Policy Addendum

### 7.1 Container Deployment and Release Policy

- All container images are built from verified base images: `python:3.11-slim-bookworm` (Django/Celery) and `node:20-alpine3.19` (Next.js). Base images are scanned weekly via Amazon ECR Image Scanning (powered by Snyk). Critical CVEs block deployment via the CI pipeline quality gate.
- Images are tagged with the Git SHA and semantic version (e.g., `portal-api:v2.4.1-abc1234`). The `latest` tag is never used in production task definitions.
- Container images do not contain secrets. All secrets are injected at runtime from AWS Secrets Manager via the ECS `secrets` field in task definitions.
- Blue-green deployments are used for the Django API to ensure zero-downtime releases. The new task version is started, health-checked, ALB target weight is shifted 10% at a time over 5 minutes, and the old version is drained and stopped.
- Container images are stored in Amazon ECR with lifecycle policies: `untagged` images deleted after 7 days; `release` tagged images retained for 180 days; `latest` on dev branches retained for 30 days.

### 7.2 Inter-Container Communication Security Policy

- All communication between containers and the data tier (RDS, ElastiCache) is encrypted in transit using TLS 1.3. TLS certificates are managed by AWS Certificate Manager (ACM). Self-signed certificates are not used in production.
- JWT tokens issued by Django API are signed using RS256 (asymmetric RSA-2048). The public key is published at `/.well-known/jwks.json` for potential future federated verification. The private key is stored in AWS Secrets Manager, not in the container file system.
- Inter-service calls within the VPC use the internal ALB DNS name, not direct container IPs, allowing security group rules to be enforced consistently.
- Rate limiting is enforced at two layers: AWS WAF (IP-based, 100 req/sec) and Django middleware (user-based, using Redis atomic counters). API endpoints for OTP initiation are additionally throttled to 5 requests per mobile number per 10 minutes.

### 7.3 Data Container Backup and Recovery Policy

- RDS automated backups are enabled with a 35-day retention period. Manual snapshots are taken before every production deployment and retained for 90 days.
- ElastiCache Redis is configured with AOF (Append-Only File) persistence enabled for data durability. Snapshotting occurs every 6 hours to S3.
- S3 document bucket versioning is enabled. Object Lock is configured in Compliance mode for certificates and payment records (retention: 10 years). Regular documents are protected by versioning only.
- Backup restoration is tested quarterly as part of DR drills. The drill involves restoring RDS to a point-in-time 24 hours in the past and verifying all application functionality in the staging environment.

### 7.4 Monitoring and Observability Policy

- Distributed tracing is implemented using AWS X-Ray. Every incoming HTTP request generates a trace ID, propagated as `X-Amzn-Trace-Id` header across all container-to-container calls, logged in CloudWatch and queryable in the X-Ray console.
- Structured JSON logging is mandatory for all containers. Log fields: `timestamp`, `level`, `request_id`, `user_id` (hashed for PII compliance), `event`, `duration_ms`, `status_code`. Logs are shipped to CloudWatch Logs with 90-day retention, then archived to S3 for 7 years.
- Application metrics (custom business metrics: applications submitted per minute, payments processed, OTP success rate, workflow completion time) are published to CloudWatch Custom Metrics every minute via a StatsD agent on each ECS task.
- A Grafana dashboard (deployed on ECS, pulling from CloudWatch) provides real-time visibility into: active ECS task count, API P50/P95/P99 latency, error rates, queue depths, database connection counts, and Redis memory usage.
