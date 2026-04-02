# Architecture Diagram — Government Services Portal

## 1. Overview

The Government Services Portal is designed as a **modular monolith with asynchronous processing** — a deliberate architectural choice that balances operational simplicity with the scalability needs of a public-sector platform serving millions of citizens. Rather than distributing the domain across independently deployable microservices from day one, the backend is structured as a single deployable Django application organised into tightly bounded modules (Identity, Application, Payment, Document, Notification, Workflow, Audit, Certificate, Grievance, Admin). Module boundaries are enforced through Python package conventions and Django app isolation: no cross-module direct model imports are permitted; inter-module communication is mediated through well-defined service interfaces or Django signals.

Asynchronous processing is handled by Celery workers backed by Redis 7, which decouple time-consuming operations (document virus scanning, PDF generation, DSC signing, payment reconciliation, notification delivery, Nepal Document Wallet (NDW) synchronisation) from the synchronous HTTP request cycle. This ensures that API response times remain under SLA thresholds even when downstream integrations (NID NASC (National Identity Management Centre), ConnectIPS, Nepal Document Wallet (NDW)) experience latency.

The frontend is a Next.js 14 App Router application compiled to static assets and server-side rendered pages, served via AWS CloudFront CDN. A separate Admin Console (also Next.js) serves Field Officers, Department Heads, Super Admins, and Auditors through an isolated deployment.

The entire platform runs on AWS, using managed services (RDS, ElastiCache, S3, ECS Fargate, CloudFront, Route 53, WAF, Shield) to reduce operational burden on the engineering team and maximise availability guarantees.

---

## 2. High-Level Architecture Diagram

```mermaid
flowchart TD
    subgraph CLIENT["Client Layer"]
        CW["🌐 Citizens\n(Web Browser / PWA)"]
        CM["📱 Citizens\n(Mobile App)"]
        SMS_CLIENT["📟 SMS-Only Interface\n(Feature Phone Users)"]
        STAFF["🖥 Staff Portal\n(Officers / Admins)"]
    end

    subgraph CDN["CDN Layer — AWS CloudFront"]
        CF["☁️ CloudFront Distribution\n(Static Assets, SSR Cache)\nEdge Locations: Mumbai, Chennai, Delhi"]
    end

    subgraph WAF_LAYER["Security Layer"]
        WAF["🛡 AWS WAF\n(OWASP Top 10 Rules, Rate Limiting,\nGeo-restriction, IP Reputation)"]
        SHIELD["🔒 AWS Shield Advanced\n(DDoS Protection, L3/L4/L7)"]
        R53["🌍 Route 53\n(DNS, Health Checks, Failover)"]
    end

    subgraph ALB_LAYER["Load Balancer Layer"]
        ALB_FE["⚖️ ALB — Frontend\n(HTTPS:443, HTTP→HTTPS redirect)"]
        ALB_API["⚖️ ALB — API\n(HTTPS:443, Path-based routing)"]
    end

    subgraph APP["Application Layer — AWS ECS Fargate"]
        NEXTJS["⚛️ Next.js 14 Frontend\n(App Router, SSR + SSG)\nTask: 2 vCPU / 4 GB\nMin: 2 tasks | Max: 20 tasks"]
        NEXTJS_ADMIN["⚛️ Next.js Admin Console\n(Staff / Officer Portal)\nTask: 1 vCPU / 2 GB\nMin: 2 tasks | Max: 10 tasks"]
        DJANGO["🐍 Django 4.x API Server\n(DRF, Gunicorn + Uvicorn)\nTask: 2 vCPU / 4 GB\nMin: 3 tasks | Max: 30 tasks"]
    end

    subgraph QUEUE["Async Processing Layer"]
        REDIS_BROKER["📨 Redis 7 — Celery Broker\n(Task Queue, Priority Queues:\nhigh / default / low / bulk)"]
        CELERY_DEFAULT["⚙️ Celery Worker — Default\n(Notifications, Status Updates)\nTask: 1 vCPU / 2 GB\nMin: 2 | Max: 10"]
        CELERY_DOC["⚙️ Celery Worker — Documents\n(Virus Scan, PDF Gen, DSC Sign)\nTask: 2 vCPU / 4 GB\nMin: 2 | Max: 8"]
        CELERY_PAYMENT["⚙️ Celery Worker — Payment\n(Reconciliation, Challan Gen)\nTask: 1 vCPU / 2 GB\nMin: 2 | Max: 6"]
        CELERY_BEAT["⏰ Celery Beat Scheduler\n(Cron Jobs: SLA checks,\nArchival, Reports)"]
    end

    subgraph DATA["Data Layer"]
        RDS["🗄 RDS PostgreSQL 15\n(Multi-AZ, db.r6g.xlarge)\nPrimary + Read Replica\nEncrypted at rest (AES-256)"]
        ELASTICACHE["⚡ ElastiCache Redis 7\n(cache.r6g.large, Cluster Mode)\nSessions, App Cache, Rate Limits"]
        S3["🪣 AWS S3\n(Document Store)\nKMS-CMK Encryption\nVersioning + Object Lock\nLifecycle: S3 → Glacier (7yr)"]
    end

    subgraph EXTERNAL["External Integrations"]
        DIGILOCKER["📂 Nepal Document Wallet (NDW) API\n(Document Push/Pull,\nOAuth 2.0)"]
        AADHAAR["🪪 NID / NASC (National Identity Management Centre)\n(OTP Auth, e-KYC,\nBiometric Verify)"]
        PAYGOV["💳 ConnectIPS / Razorpay Govt\n(Payment Orders,\nCallbacks, Reconciliation)"]
        SMS_GW["📱 SMS Gateway\n(MSG91 / Textlocal)\n(OTP, Status SMS)"]
        SES["📧 AWS SES\n(Transactional Email,\nSPF/DKIM signed)"]
        LEGACY["🏛 Legacy Govt DB\n(Province NIC Systems,\nRead-only SFTP/API)"]
    end

    CW -->|HTTPS| CF
    CM -->|HTTPS| CF
    STAFF -->|HTTPS| CF
    SMS_CLIENT -->|SMS| SMS_GW

    R53 --> CF
    R53 --> WAF
    CF --> WAF
    WAF --> SHIELD
    SHIELD --> ALB_FE
    SHIELD --> ALB_API

    ALB_FE --> NEXTJS
    ALB_FE --> NEXTJS_ADMIN
    ALB_API --> DJANGO

    NEXTJS -->|REST/HTTPS| ALB_API
    NEXTJS_ADMIN -->|REST/HTTPS| ALB_API

    DJANGO -->|TCP 6379| REDIS_BROKER
    DJANGO -->|TCP 5432| RDS
    DJANGO -->|TCP 6379| ELASTICACHE
    DJANGO -->|HTTPS/AWS SDK| S3

    REDIS_BROKER --> CELERY_DEFAULT
    REDIS_BROKER --> CELERY_DOC
    REDIS_BROKER --> CELERY_PAYMENT
    CELERY_BEAT --> REDIS_BROKER

    CELERY_DEFAULT -->|TCP 5432| RDS
    CELERY_DOC -->|AWS SDK| S3
    CELERY_DOC -->|TCP 5432| RDS
    CELERY_PAYMENT -->|TCP 5432| RDS

    DJANGO -->|HTTPS| AADHAAR
    DJANGO -->|HTTPS| PAYGOV
    DJANGO -->|HTTPS| DIGILOCKER
    CELERY_DEFAULT -->|HTTPS| SMS_GW
    CELERY_DEFAULT -->|SMTP/TLS| SES
    CELERY_DOC -->|HTTPS| DIGILOCKER
    CELERY_PAYMENT -->|SFTP/API| LEGACY
```

---

## 3. Domain Architecture

The application is divided into ten bounded modules. Each module owns its models, services, serializers, and API views. No module directly imports models from another module; cross-module reads use published service interfaces.

```mermaid
flowchart TD
    subgraph IDENTITY["Identity Module\n(identity/)"]
        ID1["Citizen registration & profile"]
        ID2["NID OTP / Email OTP / SMS OTP"]
        ID3["Biometric verification"]
        ID4["JWT issuance & refresh"]
        ID5["Staff user management"]
    end

    subgraph APPLICATION["Application Module\n(application/)"]
        AP1["Service catalogue management"]
        AP2["Application lifecycle (DRAFT→SUBMITTED→REVIEW→APPROVED/REJECTED)"]
        AP3["Eligibility rule engine"]
        AP4["Form schema registry (JSON Schema)"]
        AP5["Acknowledgement generation"]
    end

    subgraph WORKFLOW["Workflow Module\n(workflow/)"]
        WF1["State machine definitions"]
        WF2["Step assignment & routing"]
        WF3["SLA tracking per step"]
        WF4["Escalation triggers"]
        WF5["Audit trail of transitions"]
    end

    subgraph PAYMENT["Payment Module\n(payment/)"]
        PA1["Fee calculation engine"]
        PA2["ConnectIPS / Razorpay integration"]
        PA3["Offline challan generation"]
        PA4["Payment reconciliation"]
        PA5["Refund processing"]
    end

    subgraph DOCUMENT["Document Module\n(document/)"]
        DO1["S3 pre-signed URL upload"]
        DO2["ClamAV virus scanning"]
        DO3["Metadata extraction (PyMuPDF)"]
        DO4["DSC digital signing"]
        DO5["Document versioning"]
    end

    subgraph CERTIFICATE["Certificate Module\n(certificate/)"]
        CE1["Certificate template registry"]
        CE2["PDF generation (WeasyPrint)"]
        CE3["DSC signing integration"]
        CE4["Nepal Document Wallet (NDW) push"]
        CE5["QR-code verification endpoint"]
    end

    subgraph NOTIFICATION["Notification Module\n(notification/)"]
        NO1["Multi-channel dispatch (SMS/Email/In-app)"]
        NO2["Template engine (Jinja2)"]
        NO3["Delivery tracking & retry"]
        NO4["Preference management"]
    end

    subgraph GRIEVANCE["Grievance Module\n(grievance/)"]
        GR1["Grievance submission"]
        GR2["Auto-routing to department"]
        GR3["Response management"]
        GR4["Escalation to higher authority"]
        GR5["CPGRAMS integration (planned)"]
    end

    subgraph AUDIT["Audit Module\n(audit/)"]
        AU1["Immutable event log"]
        AU2["PII access logging"]
        AU3["Admin action logging"]
        AU4["Report generation"]
        AU5["SIEM export (Splunk/ELK)"]
    end

    subgraph ADMIN["Admin Module\n(admin_console/)"]
        ADM1["Department management"]
        ADM2["Service configuration"]
        ADM3["User role assignment"]
        ADM4["System health dashboard"]
        ADM5["Fee schedule management"]
    end

    APPLICATION -->|"emits ApplicationEvents"| WORKFLOW
    WORKFLOW -->|"triggers notifications"| NOTIFICATION
    APPLICATION -->|"initiates fee"| PAYMENT
    PAYMENT -->|"payment confirmed event"| WORKFLOW
    DOCUMENT -->|"upload complete event"| APPLICATION
    WORKFLOW -->|"approval trigger"| CERTIFICATE
    CERTIFICATE -->|"cert issued event"| NOTIFICATION
    IDENTITY -->|"citizen context"| APPLICATION
    GRIEVANCE -->|"linked to application"| APPLICATION
    AUDIT -->|"subscribes to all events"| APPLICATION
    AUDIT -->|"subscribes to all events"| WORKFLOW
    AUDIT -->|"subscribes to all events"| PAYMENT
```

---

## 4. Component Interaction Matrix

| Source Component | Target Component | Interaction Type | Protocol | Direction |
|---|---|---|---|---|
| Next.js Frontend | Django API | REST API calls | HTTPS/JSON | →  |
| Django API | PostgreSQL RDS | ORM queries | TCP 5432 | ↔ |
| Django API | ElastiCache Redis | Cache get/set, session store | TCP 6379 | ↔ |
| Django API | Redis Broker | Enqueue Celery tasks | TCP 6379 | → |
| Django API | AWS S3 | Pre-signed URL generation, object metadata | HTTPS (AWS SDK) | ↔ |
| Django API | NID NASC (National Identity Management Centre) | OTP initiate, OTP verify | HTTPS/JSON | → |
| Django API | ConnectIPS | Create order, verify signature | HTTPS/JSON | ↔ |
| Django API | Nepal Document Wallet (NDW) | OAuth token exchange, document push | HTTPS/JSON | ↔ |
| Celery Worker | PostgreSQL RDS | Task result persistence, model updates | TCP 5432 | ↔ |
| Celery Worker | AWS S3 | Document read, PDF write, signed cert upload | HTTPS (AWS SDK) | ↔ |
| Celery Worker | SMS Gateway | OTP and status SMS delivery | HTTPS/JSON | → |
| Celery Worker | AWS SES | Transactional email dispatch | SMTP/TLS or HTTPS API | → |
| Celery Worker | Nepal Document Wallet (NDW) API | Issued certificate push | HTTPS/JSON | → |
| Celery Beat | Redis Broker | Scheduled task publication | TCP 6379 | → |
| Admin Console (Next.js) | Django API | Admin REST API calls | HTTPS/JSON | → |
| Django API | Legacy Govt DB | Citizen data pre-fill lookup | SFTP / REST (read-only) | → |
| CloudFront | ALB Frontend | Origin fetch (cache miss) | HTTPS | → |
| WAF | ALB Frontend / API | Filtered traffic forwarding | HTTPS | → |

---

## 5. Architecture Decisions

| # | Decision | Rationale | Alternatives Considered |
|---|---|---|---|
| AD-001 | **Modular monolith over microservices** | Reduces operational complexity, eliminates distributed transaction problems (saga pattern), enables easier refactoring. Team size and maturity justify this choice at initial scale. | Microservices (rejected: premature complexity), serverless functions (rejected: cold start latency unacceptable for citizen-facing flows) |
| AD-002 | **Django DRF as API backend** | Strong ORM, mature ecosystem, government sector precedent (NIC uses Django widely), built-in admin, excellent security defaults (CSRF, SQL injection protection). Python 3.11 performance improvements are significant. | FastAPI (rejected: less mature ecosystem for admin and auth), Spring Boot (rejected: team expertise, slower iteration) |
| AD-003 | **Next.js 14 App Router with TypeScript** | SSR support for accessibility and SEO, incremental static regeneration for service catalogue, strong TypeScript tooling for frontend correctness, WCAG 2.1 AA compliance easier with server components. | Create React App (rejected: no SSR), Nuxt.js (rejected: smaller talent pool in Nepal), plain Django templates (rejected: poor UX for complex forms) |
| AD-004 | **PostgreSQL 15 as primary database** | ACID compliance for financial and civic records, JSONB for flexible form data, Row Level Security for tenant isolation, excellent full-text search for service catalogue, strong government sector audit trail via triggers. | MySQL (rejected: weaker JSONB, no RLS), DynamoDB (rejected: eventual consistency unacceptable for payments), Oracle (rejected: cost, vendor lock-in) |
| AD-005 | **Redis 7 for cache, sessions, and Celery broker** | Single technology for three purposes reduces ops overhead. Redis Cluster for HA. Keyspace notifications for session invalidation. Sorted sets for rate limiting. Stream support for audit events. | RabbitMQ (rejected: separate system for broker), Memcached (rejected: no persistence, no pub/sub), Kafka (rejected: operational overhead, overkill at this scale) |
| AD-006 | **AWS S3 + KMS-CMK for document storage** | MEITY-approved cloud vendor, server-side encryption with customer-managed keys, S3 Object Lock for immutability (legal compliance), lifecycle policies for 7-year retention, pre-signed URLs avoid proxying large files through application tier. | On-premise NAS (rejected: operational burden, no geo-redundancy), Azure Blob (rejected: not on MEITY approved list for this workload) |
| AD-007 | **NID OTP as primary authentication** | Complies with Government of Nepal Digital Nepal mandate, legally valid identity verification for e-governance services, reduces friction for citizens who already have NID. Email+SMS OTP as fallback. | Username/password only (rejected: weak identity assurance), SAML federation (rejected: no government IdP available at province level) |
| AD-008 | **Celery for async task processing** | Mature Python task queue, priority queue support for urgent notifications vs. bulk reports, robust retry logic with exponential backoff, visibility into task province via Flower. | Django Q (rejected: smaller community), Dramatiq (rejected: less Redis integration), AWS SQS + Lambda (rejected: breaks monolith deployment model) |
| AD-009 | **ECS Fargate over EC2 self-managed** | No instance management, automatic scaling per task, IAM task roles for fine-grained S3/KMS access, integration with ALB for zero-downtime deploys, pay-per-task-second pricing suits variable government traffic patterns. | EKS Kubernetes (rejected: operational complexity, team not Kubernetes-native), EC2 Auto Scaling (rejected: bin-packing overhead, slower scaling), Lambda (rejected: cold starts, 15-minute timeout) |
| AD-010 | **DSC-based digital signing of certificates** | Legal validity under IT Act 2000 and subsequent amendments, required for certificates to be accepted by government departments. Controller of Certifying Authorities (CCA) compliant. | Self-signed certificates (rejected: no legal standing), NID-based eSign (considered: will be added in Phase 2 as alternative signing method) |

---

## 6. Scaling Strategy

The platform is designed for horizontal scaling at every tier, with no shared mutable province in application processes.

**Frontend (Next.js):** ECS Fargate tasks scale based on ALB `RequestCountPerTarget` metric. Target: 1,000 requests/task/minute. Auto-scaling group with a 3-minute cooldown. Static assets are served entirely from CloudFront edge, eliminating origin load for the majority of traffic (>70% cache hit rate expected). New task startup time is approximately 45 seconds, so proactive scale-out is triggered at 70% of the target metric.

**Django API:** ECS Fargate tasks scale on both `RequestCountPerTarget` (target: 500 requests/task/minute for compute-heavy API calls) and CPU utilisation (target: 65%). Gunicorn runs 4 workers per task with Uvicorn worker class for async support. Database connection pooling via PgBouncer (deployed as a sidecar within the ECS task) caps connections to RDS at `(max_connections / (api_tasks × workers))` ≈ 8 connections per worker process at peak 30 tasks.

**Celery Workers:** Separate auto-scaling groups per queue (document, payment, default) based on Redis queue depth via a custom CloudWatch metric exported by a Prometheus-to-CloudWatch adapter. Document workers scale more aggressively during citizen rush hours (9 AM – 1 PM IST). Payment workers maintain minimum 2 replicas 24/7 for reconciliation jobs.

**Database:** RDS PostgreSQL Multi-AZ with a read replica in the same region. Read-heavy operations (service catalogue, application status lookup) are routed to the read replica via Django's database router. Write operations always hit the primary. PgBouncer in transaction pooling mode on each API task reduces connection pressure. At anticipated peak (50,000 concurrent users), read replica traffic absorbs approximately 60% of query load.

**Redis:** ElastiCache Redis 7 in Cluster Mode with 3 shards × 1 read replica each. Session data is sharded by citizen ID. Cache keys use consistent hashing to minimise resharding impact. Rate-limiting counters use Redis atomic `INCR` + `EXPIRE`. Celery task queues reside in a dedicated cluster node group separate from the application cache to prevent cache evictions affecting task delivery.

**CDN / Static:** CloudFront with origin shield in Mumbai region absorbs the bulk of citizen-facing traffic. Cache TTLs: static assets (JS/CSS/images) 1 year with content-hash filenames; HTML pages 30 seconds with `stale-while-revalidate`; API responses (service catalogue) 5 minutes; application status — not cached.

---

## 7. Deployment Architecture Overview

The deployment architecture is described in detail in `infrastructure/aws-infrastructure.md`. In summary:

- **Two environments:** `staging` (single-AZ, reduced instance sizes) and `production` (Multi-AZ, full capacity).
- **Deployment pipeline:** GitHub Actions → ECR image push → ECS rolling deployment (25% min healthy, 200% max). Zero-downtime deploys enforced by ALB connection draining (30-second drain timeout).
- **Database migrations:** Run as a one-off ECS task pre-deployment, gated by a migration compatibility check (Django `--check` flag). Backwards-compatible migrations are required; destructive changes require a two-phase deployment.
- **Secrets management:** AWS Secrets Manager for database credentials, API keys (NID, ConnectIPS, Nepal Document Wallet (NDW)). Injected as environment variables into ECS tasks at runtime. Rotation is automated for database credentials every 30 days.
- **Infrastructure as Code:** Terraform 1.6+ for all AWS resources. Province stored in S3 with DynamoDB lock table. Separate Terraform workspaces per environment.

---

## 8. Operational Policy Addendum

### 8.1 Citizen Data Privacy Policy

- All Personally Identifiable Information (PII) stored in PostgreSQL is classified as **Restricted** and encrypted at rest using AES-256 (RDS encryption with AWS-managed keys). Fields containing NID numbers, biometric hashes, and financial data are additionally encrypted at the application layer using a KMS-derived data encryption key (envelope encryption pattern).
- NID numbers stored in the system are **tokenised** using the Virtual ID (VID) mechanism; the actual NID number is never persisted in the database. Only the NID-seeded token and e-KYC demographic data (name, DoB, gender, address) are stored after explicit citizen consent.
- Citizens have the right to request a data export (all their application records, documents, and audit logs) within 30 days of request, fulfilling obligations under the Digital Personal Data Protection Act (DPDPA) 2023.
- PII access by staff users is logged in the immutable audit module. Every access to a citizen's profile, application, or documents by an officer is recorded with timestamp, officer ID, and purpose code.
- Data subject deletion requests result in the pseudonymisation of citizen records (replacing PII with anonymised tokens) after all legally mandated retention periods have elapsed. Financial and legal records are retained for 7 years per Govt. of Nepal record retention rules before pseudonymisation.

### 8.2 Service Delivery SLA Policy

- Every service available on the portal must have a defined **statutory processing time** (e.g., "Domicile Certificate: 15 working days from complete application"). This SLA is configured per-service in the service catalogue by the Department Head.
- The workflow engine automatically triggers an SLA breach alert (to the Field Officer's supervisor and Department Head) when a pending application step exceeds 80% of the allocated processing time.
- Applications that breach their statutory deadline are automatically flagged in the Department Head dashboard and generate a compliance report entry. Citizens receive an automated notification and a revised expected delivery date.
- The Auditor role has read-only access to an SLA compliance dashboard showing per-department, per-service breach rates, average processing times, and trend analysis over rolling 30/90-day windows.
- The platform targets **99.5% of applications processed within their statutory time** as measured monthly. Departments failing to meet this target for two consecutive months trigger an administrative escalation workflow to the Super Admin.

### 8.3 Fee and Payment Policy

- All service fees are configured in the fee schedule by the Super Admin and are version-controlled: fee changes take effect from a specified effective date, and historical applications always reference the fee at the time of submission, not the current fee.
- Payment proof (ConnectIPS transaction ID, amount, timestamp, challan number for offline payments) is stored immutably in the Payment record. No payment record can be deleted or modified once confirmed; adjustments are handled via a Refund record linked to the original Payment.
- Offline challan payments must be verified by a Field Officer within 5 working days. Unverified challans trigger a reminder to the officer and, after 10 working days, escalate to the Department Head.
- Partial fee waivers (for BPL cardholders, disabled persons, ex-servicemen per province policy) are configured per-service per-category by the Department Head. The system automatically applies the waiver upon verification of the supporting document at submission time.
- Payment reconciliation with ConnectIPS/Razorpay is performed twice daily by the Celery payment worker. Discrepancies (callbacks received but no order in system, or orders marked pending for >24 hours) generate an alert to the Finance Officer role and are logged in the audit module.

### 8.4 System Availability and Incident Policy

- The production environment targets **99.9% monthly availability** (≤ 43.8 minutes downtime/month) for citizen-facing services and **99.5%** for staff-facing (admin portal).
- Planned maintenance windows are scheduled between **01:00 and 05:00 IST Sunday mornings** and announced to citizens via the portal banner and SMS at least 48 hours in advance.
- AWS CloudWatch alarms are configured for: API 5xx error rate > 1% (P1 — 5-minute response), P95 API latency > 3 seconds (P2 — 30-minute response), RDS CPU > 80% for 5 minutes (P2), Redis memory > 75% (P3), S3 upload failure rate > 2% (P2).
- All P1 incidents trigger PagerDuty escalation to the on-call engineer (24/7 rotation) and the System Admin. P1 resolution target: 30 minutes. P2: 4 hours. Post-incident review is mandatory for P1 and P2 incidents, with findings published to the internal engineering wiki within 5 working days.
- Disaster Recovery: RDS automated backups retained for 35 days. S3 documents are versioned and cross-region replicated to `ap-south-2` (Hyderabad). Recovery Time Objective (RTO): 4 hours. Recovery Point Objective (RPO): 1 hour. DR drills are conducted quarterly.
