# C4 Context and Container Diagrams - Learning Management System

This document presents the C4 architecture model at the Context level (who uses the system and what it depends on) and the Container level (what the deployable units are and how they communicate).

---

## C4 Level 1 — System Context Diagram

Shows the LMS as a single system and all external actors and systems that interact with it.

```mermaid
flowchart TB
    subgraph users[People]
        L([Learner\nEnrols in courses,\ncompletes assessments,\nearns certificates])
        I([Instructor / Reviewer\nAuthors courses,\ngrades submissions,\nmanages cohorts])
        A([Admin / Tenant Admin\nManages users, roles,\ntenant settings, reports])
    end

    LMS[[Learning Management System\n\nMulti-tenant SaaS platform for\ncourse delivery, assessment,\nprogress tracking, and certification]]

    subgraph external[External Systems]
        IDP([Identity Provider\nOIDC / SAML 2.0\ne.g. Okta, Azure AD])
        LIVE([Live Session Provider\nVideo conferencing integration\ne.g. Zoom, Teams])
        EMAIL([Email / Notification Provider\nTransactional email + push\ne.g. SendGrid, FCM])
        BADGE([Credential / Badge Platform\nOpen Badges 2.0 / CLR\ne.g. Credly, Badgr])
        BI([Analytics / BI Platform\nAggregate reporting\ne.g. Snowflake, Looker])
        STOR([Cloud Object Storage\nContent + certificate PDFs\ne.g. S3, Azure Blob])
    end

    L -- "Browse catalog, enrol,\nconsume content, submit\nassessments, download certs\n[HTTPS]" --> LMS
    I -- "Author courses, review\nsubmissions, release grades,\nview cohort analytics\n[HTTPS]" --> LMS
    A -- "Configure tenant, manage\nusers, view audit logs,\nexport reports\n[HTTPS]" --> LMS

    LMS -- "Verify identity,\nfederate login\n[OIDC / SAML]" --> IDP
    IDP -- "ID tokens, user attributes" --> LMS

    LMS -- "Create sessions,\nfetch attendance\n[REST API]" --> LIVE
    LMS -- "Send transactional\nemail + push notifications\n[REST API]" --> EMAIL
    LMS -- "Issue credential assertions\n[Open Badges API]" --> BADGE
    LMS -- "Stream anonymised\nevent data\n[Kafka / S3 export]" --> BI
    LMS -- "Store / retrieve\ncontent and certificate PDFs\n[S3 API]" --> STOR
```

---

## C4 Level 2 — Container Diagram

Decomposes the LMS into its deployable containers and shows the key communication paths between them.

```mermaid
flowchart TB
    L([Learner])
    I([Instructor / Staff])
    A([Admin])

    subgraph frontend[Frontend Containers]
        LP[Learner Portal\nReact SPA\nHosted on CDN]
        SW[Staff Workspace\nReact SPA\nHosted on CDN]
    end

    subgraph api[API Tier — Kubernetes]
        GW[API Gateway\nNginx + Kong\nTLS termination, rate limiting,\nJWT validation, routing]
        IDS[Identity & Access Service\nNode.js / Go\nAuth, RBAC, tenant resolution]
        CRS[Course & Authoring Service\nNode.js\nCatalog, versions, content]
        ENS[Enrollment & Cohort Service\nNode.js\nSeats, schedules, policies]
        ASS[Assessment Service\nNode.js\nAttempts, timers, submissions]
        GRS[Grading & Review Service\nNode.js\nRubrics, scoring, release]
        PRS[Progress Tracking Service\nNode.js\nLesson events, completion]
        CES[Certification Service\nNode.js\nCompletion eval, PDF issuance]
        RPS[Reporting & Search Service\nNode.js\nDashboards, catalog search]
    end

    subgraph workers[Worker Tier — Kubernetes Jobs]
        GW2[Grading Worker\nConsumes assessment-events\nAuto-grades objective questions]
        CW[Certificate Worker\nConsumes progress-events\nEvaluates completion, generates PDFs]
        NW[Notification Worker\nConsumes all domain events\nDispatches email / push / SMS]
        PW[Projection Worker\nConsumes all domain events\nBuilds Elasticsearch projections]
    end

    subgraph stores[Data Stores]
        PG[(PostgreSQL\nPrimary + Read Replica\nTransactional data)]
        RD[(Redis Cluster\nSessions, seat counters,\ntimer state, hot cache)]
        KF[(Kafka\nEvent Bus\nDomain event streams)]
        ES[(Elasticsearch\nSearch & analytics\nread models)]
        S3[(Object Storage\nCourse content,\ncertificate PDFs)]
    end

    subgraph ext[External Services]
        IDP([Identity Provider])
        EMAIL([Email / Push Provider])
        BADGE([Badge Platform])
        BI([Analytics / BI])
    end

    L --> LP --> GW
    I --> SW --> GW
    A --> SW --> GW

    GW --> IDS
    GW --> CRS
    GW --> ENS
    GW --> ASS
    GW --> GRS
    GW --> PRS
    GW --> CES
    GW --> RPS

    IDS <--> PG
    IDS <--> RD
    IDS <--> IDP

    CRS <--> PG
    CRS --> S3
    CRS --> KF

    ENS <--> PG
    ENS <--> RD
    ENS --> KF

    ASS <--> PG
    ASS <--> RD
    ASS --> KF

    GRS <--> PG
    GRS --> KF

    PRS <--> PG
    PRS --> KF

    CES <--> PG
    CES --> S3
    CES --> KF
    CES --> BADGE

    RPS --> ES
    RPS --> PG

    KF --> GW2
    KF --> CW
    KF --> NW
    KF --> PW

    GW2 --> PG
    GW2 --> KF
    CW --> PG
    CW --> S3
    CW --> KF
    NW --> EMAIL
    PW --> ES
    PW --> BI
```

---

## Container Responsibility Table

| Container | Technology | Responsibility | Scales By |
|---|---|---|---|
| Learner Portal | React SPA, CDN | Course discovery, enrollment, content consumption, assessment, certificates | CDN edge nodes |
| Staff Workspace | React SPA, CDN | Course authoring, cohort management, grading, analytics | CDN edge nodes |
| API Gateway | Nginx + Kong | TLS termination, JWT validation, rate limiting, request routing | Horizontal (stateless) |
| Identity & Access Service | Node.js | User auth, OIDC federation, RBAC enforcement, tenant scoping | Horizontal (stateless) |
| Course & Authoring Service | Node.js | Course CRUD, version lifecycle, module/lesson management, content upload | Horizontal (stateless) |
| Enrollment & Cohort Service | Node.js | Seat reservation, policy evaluation, cohort scheduling, access windows | Horizontal (stateless) |
| Assessment Service | Node.js | Attempt lifecycle, question delivery, timer management, submission handling | Horizontal (stateless) |
| Grading & Review Service | Node.js | Rubric scoring, draft/release workflow, grade override, reviewer assignment | Horizontal (stateless) |
| Progress Tracking Service | Node.js | Lesson completion events, progress aggregation, resume state | Horizontal (stateless) |
| Certification Service | Node.js | Completion rule evaluation, certificate generation and storage | Horizontal (stateless) |
| Reporting & Search Service | Node.js | Catalog search, learner/staff dashboards, exports | Horizontal (stateless) |
| Grading Worker | Node.js Job | Async auto-grading from `assessment-events` topic | Queue depth |
| Certificate Worker | Node.js Job | Async completion checks and PDF generation | Queue depth |
| Notification Worker | Node.js Job | Dispatches email/push/SMS from all domain event topics | Queue depth |
| Projection Worker | Node.js Job | Builds and updates Elasticsearch search and analytics indices | Queue depth |
| PostgreSQL | PostgreSQL 15 | Authoritative transactional store for all domain aggregates | Read replicas |
| Redis Cluster | Redis 7 | JWT session cache, seat counters, timer state, hot metadata cache | Cluster sharding |
| Kafka | Apache Kafka 3 | Ordered, durable, partitioned domain event streams | Partition count |
| Elasticsearch | Elasticsearch 8 | Full-text catalog search, aggregated reporting read models | Index sharding |
| Object Storage | S3-compatible | Binary content (lesson media, certificate PDFs, exports) | Unlimited |

---

## Container-to-Container Communication

| Source Container | Target Container | Protocol | Sync / Async | Data Exchanged | Auth Method |
|---|---|---|---|---|---|
| API Gateway | Identity Service | HTTP/2 (gRPC) | Sync | JWT claims, tenant context | mTLS |
| API Gateway | All domain services | HTTP/1.1 REST | Sync | Validated HTTP requests | mTLS + forwarded JWT |
| Identity Service | Identity Provider | OIDC / SAML | Sync | Auth codes, ID tokens | Client credentials + TLS |
| Course Service | Object Storage | S3 API (HTTPS) | Sync | Content upload / presigned URLs | IAM role / service account |
| Enrollment Service | Redis | Redis protocol | Sync | Seat counter reads/writes | Password + TLS |
| Assessment Service | Redis | Redis protocol | Sync | Timer state, attempt locks | Password + TLS |
| All domain services | Kafka | Kafka protocol | Async (produce) | Domain event messages | SASL/SCRAM + TLS |
| Grading Worker | Kafka | Kafka protocol | Async (consume) | `assessment-events` | SASL/SCRAM + TLS |
| Certificate Worker | Kafka | Kafka protocol | Async (consume) | `progress-events`, `grading-events` | SASL/SCRAM + TLS |
| Notification Worker | Kafka | Kafka protocol | Async (consume) | All domain event topics | SASL/SCRAM + TLS |
| Notification Worker | Email/Push Provider | HTTPS REST | Async | Notification payloads | API key |
| Projection Worker | Kafka | Kafka protocol | Async (consume) | All domain event topics | SASL/SCRAM + TLS |
| Projection Worker | Elasticsearch | HTTPS REST | Sync (bulk index) | Projected read-model documents | API key + TLS |
| Certification Service | Badge Platform | HTTPS REST | Sync | Open Badge assertions | API key |
| Reporting Service | Elasticsearch | HTTPS REST | Sync | Search / aggregation queries | API key + TLS |
| Projection Worker | Analytics / BI | Kafka / S3 export | Async | Anonymised event streams | IAM role |

---

## External Dependency Table

| External System | Purpose | Protocol | Criticality | Failure Mode | Circuit Breaker |
|---|---|---|---|---|---|
| Identity Provider (OIDC/SAML) | User authentication, SSO federation | OIDC / SAML 2.0 over HTTPS | **Critical** | Fall back to local auth if configured; else deny login | Yes — 30 s open window |
| Email / Push Provider | Transactional notifications | HTTPS REST | **High** | Queue notification, retry for 24 h; learner sees pending state | Yes — 60 s open window |
| Live Session Provider | Scheduled live sessions | HTTPS REST | **Medium** | Display join-link fallback message; flag session as degraded | Yes — 30 s open window |
| Credential / Badge Platform | Issue verifiable credentials | HTTPS REST (Open Badges) | **Low** | Certificate still issued internally; badge issuance retried async | Yes — 60 s open window |
| Analytics / BI Platform | Aggregate reporting beyond LMS | Kafka / S3 export | **Low** | Export buffered in S3; no learner-facing impact | No — async buffer |
| Cloud Object Storage | Lesson content + certificate PDFs | S3 API (HTTPS) | **Critical** | Content delivery degraded; certificate issuance retried | Yes — 15 s open window |
