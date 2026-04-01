# Architecture Diagram - Learning Management System

This document describes the production architecture of the LMS across five views: the overall system architecture, request routing, data persistence, async event processing, and failure containment. Non-functional targets (SLOs/SLAs) and component responsibilities are also defined.

---

## 1. Overall System Architecture

```mermaid
flowchart TB
    subgraph access[Access Channels]
        LP[Learner Portal\nReact SPA]
        SW[Staff Workspace\nReact SPA]
        MOB[Mobile App\niOS / Android]
    end

    subgraph edge[Edge Layer]
        CDN[CDN\nStatic Assets + Media]
        GW[API Gateway\nAuth, Rate-Limit, Routing]
    end

    subgraph core[Core Services — Kubernetes]
        IDS[Identity &\nAccess Service]
        CRS[Course &\nAuthoring Service]
        ENS[Enrollment &\nCohort Service]
        ASS[Assessment Service]
        GRS[Grading &\nReview Service]
        PRS[Progress Tracking\nService]
        CES[Certification Service]
        NTS[Notification Service]
        RPS[Reporting &\nSearch Service]
    end

    subgraph workers[Async Workers — Kubernetes]
        GW2[Grading Worker]
        CW[Certificate Worker]
        NW[Notification Worker]
        PW[Projection Worker]
    end

    subgraph data[Data Layer]
        PG[(PostgreSQL\nPrimary + Read Replica)]
        ES[(Elasticsearch\nSearch Index)]
        S3[(Object Storage\nS3-compatible)]
        KF[(Kafka\nEvent Bus)]
        RD[(Redis\nCache + Sessions)]
    end

    subgraph ext[External Integrations]
        IDP[Identity Provider\nOIDC / SAML]
        LIVE[Live Session Provider]
        EMAIL[Email / SMS Provider]
        BADGE[Badge Platform]
        BI[Analytics / BI]
    end

    LP --> CDN
    SW --> CDN
    MOB --> GW
    CDN --> GW
    GW --> IDS
    GW --> CRS
    GW --> ENS
    GW --> ASS
    GW --> GRS
    GW --> PRS
    GW --> CES
    GW --> RPS

    IDS --> PG
    IDS --> RD
    IDS <--> IDP
    CRS --> PG
    CRS --> S3
    CRS --> KF
    ENS --> PG
    ENS --> KF
    ASS --> PG
    ASS --> RD
    ASS --> KF
    GRS --> PG
    GRS --> KF
    PRS --> PG
    PRS --> KF
    CES --> PG
    CES --> S3
    CES --> KF
    RPS --> ES

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
    NW --> PG
    PW --> PG
    PW --> ES

    CES --> BADGE
    RPS --> BI
    ASS --> LIVE
```

---

## 2. Request Routing Diagram

Shows how learner vs. staff vs. admin requests are authenticated, authorized, and routed to the appropriate service.

```mermaid
flowchart LR
    LR([Learner Request])
    SR([Staff Request])
    AR([Admin Request])

    subgraph gw[API Gateway]
        TLS[TLS Termination]
        RL[Rate Limiter\nper tenant + IP]
        JV[JWT Validation\n& Claims Extraction]
        TR[Tenant Resolver]
        RO[Route Dispatcher]
    end

    subgraph authz[Authorization Layer — per service]
        RBAC[RBAC Guard\nrole × resource × action]
        TG[Tenant Scope Guard\ntenantId injection]
        OWN[Ownership Guard\nresourceOwner check]
    end

    subgraph services[Backend Services]
        LSVC[Learner-facing APIs\nCatalog, Enrollment,\nProgress, Assessment]
        SSVC[Staff APIs\nAuthoring, Grading,\nCohort Management]
        ASVC[Admin APIs\nUser Mgmt, Config,\nAudit, Reports]
    end

    LR --> TLS --> RL --> JV --> TR --> RO
    SR --> TLS
    AR --> TLS

    RO --> RBAC --> TG --> OWN

    OWN -->|role=LEARNER| LSVC
    OWN -->|role=INSTRUCTOR,REVIEWER| SSVC
    OWN -->|role=ADMIN,SUPERADMIN| ASVC

    LSVC -->|401 Unauthenticated| LR
    SSVC -->|403 Forbidden| SR
    ASVC -->|403 Forbidden| AR
```

---

## 3. Data Persistence Layer

Shows the read/write topology including replicas, caches, and which services access which stores.

```mermaid
flowchart LR
    subgraph writes[Write Path]
        IDS_W[Identity Service]
        CRS_W[Course Service]
        ENS_W[Enrollment Service]
        ASS_W[Assessment Service]
        GRS_W[Grading Service]
        PRS_W[Progress Service]
        CES_W[Cert Service]
    end

    subgraph pg[PostgreSQL Cluster]
        PG_P[(Primary\nRead-Write)]
        PG_R1[(Read Replica 1\nRead-Only)]
        PG_R2[(Read Replica 2\nRead-Only)]
        PG_P --> PG_R1
        PG_P --> PG_R2
    end

    subgraph cache[Redis Cluster]
        RD_S[(Redis — Sessions\nJWT + CSRF tokens)]
        RD_C[(Redis — Cache\nCourse metadata,\nseat counters)]
    end

    subgraph blob[Object Storage]
        S3_C[(Course Content\nBucket — private)]
        S3_CERT[(Certificate\nBucket — private)]
        S3_PUB[(Static Assets\nBucket — public + CDN)]
    end

    subgraph search[Search Layer]
        ES[(Elasticsearch\nCatalog + Reports Index)]
    end

    IDS_W --> PG_P
    IDS_W <--> RD_S
    CRS_W --> PG_P
    CRS_W --> S3_C
    ENS_W --> PG_P
    ENS_W <--> RD_C
    ASS_W --> PG_P
    ASS_W <--> RD_C
    GRS_W --> PG_P
    PRS_W --> PG_P
    CES_W --> PG_P
    CES_W --> S3_CERT

    PG_R1 -->|Reporting\nread queries| RPS[Reporting Service]
    PG_R2 -->|Progress\nread queries| PRS_R[Progress Service\nRead Path]
    ES -->|Catalog\nsearch| RPS
    RD_C -->|Seat counts,\nmetadata cache| ENS_W
```

---

## 4. Async Event Processing Pipeline

Shows the Kafka-based event pipeline from domain service producers to worker consumers and read-model projectors.

```mermaid
flowchart LR
    subgraph producers[Event Producers]
        ENS[Enrollment Service]
        ASS[Assessment Service]
        GRS[Grading Service]
        PRS[Progress Service]
        CES[Cert Service]
        CRS[Course Service]
    end

    subgraph kafka[Kafka Topics — partitioned by tenantId]
        T_ENR[enrollment-events]
        T_ASS[assessment-events]
        T_GRD[grading-events]
        T_PRG[progress-events]
        T_CRT[certificate-events]
        T_CAT[catalog-events]
        DLQ[dead-letter-queue]
    end

    subgraph consumers[Workers & Projectors]
        GW[Grading Worker\nAuto-grade, rubric agg]
        CW[Certificate Worker\nCompletion eval, PDF gen]
        NW[Notification Worker\nEmail, push, SMS]
        PW[Projection Worker\nES index, analytics]
    end

    ENS --> T_ENR
    ASS --> T_ASS
    GRS --> T_GRD
    PRS --> T_PRG
    CES --> T_CRT
    CRS --> T_CAT

    T_ENR --> NW
    T_ENR --> PW
    T_ASS --> GW
    T_ASS --> PW
    T_GRD --> CW
    T_GRD --> NW
    T_GRD --> PW
    T_PRG --> CW
    T_PRG --> PW
    T_CRT --> NW
    T_CRT --> PW
    T_CAT --> PW

    GW -- "on retry exhaustion" --> DLQ
    CW -- "on retry exhaustion" --> DLQ
    NW -- "on retry exhaustion" --> DLQ
    PW -- "on retry exhaustion" --> DLQ
```

---

## 5. Component Responsibility Matrix

| Component | Reads From | Writes To | Emits Events | Consumes Events |
|---|---|---|---|---|
| Identity Service | User/Tenant Store, Redis (sessions) | User/Tenant Store, Redis | — | — |
| Course Service | Course Store, Object Storage | Course Store, Object Storage | `catalog-events` | — |
| Enrollment Service | Enrollment Store, Redis (seats) | Enrollment Store | `enrollment-events` | `catalog-events` (seat validation) |
| Assessment Service | Assessment Store, Redis (timers) | Assessment Store | `assessment-events` | `catalog-events` |
| Grading Service | Assessment Store | Assessment Store | `grading-events` | `assessment-events` |
| Progress Service | Progress Store | Progress Store | `progress-events` | `grading-events`, `assessment-events` |
| Certification Service | Progress Store, Cert Store | Cert Store, Object Storage | `certificate-events` | `progress-events`, `grading-events` |
| Notification Service | — | Notification log | — | `enrollment-events`, `grading-events`, `certificate-events` |
| Reporting Service | Read Replica, Elasticsearch | Elasticsearch | — | All event topics (projector) |

---

## 6. SLO / SLA per Component

| Component | Availability SLO | p95 Latency | p99 Latency | Error Rate Budget | RTO | RPO |
|---|---|---|---|---|---|---|
| API Gateway | 99.99% | < 50 ms | < 100 ms | < 0.01% | 1 min | 0 |
| Identity Service | 99.99% | < 100 ms | < 200 ms | < 0.01% | 2 min | 0 |
| Course Service | 99.9% | < 300 ms | < 600 ms | < 0.1% | 5 min | 1 min |
| Enrollment Service | 99.9% | < 500 ms | < 1 s | < 0.1% | 5 min | 1 min |
| Assessment Service | 99.9% | < 700 ms | < 1.5 s | < 0.1% | 5 min | 30 s |
| Grading Service | 99.5% | < 2 s (sync) | < 5 s | < 0.5% | 10 min | 1 min |
| Progress Service | 99.5% | < 400 ms | < 800 ms | < 0.5% | 5 min | 30 s |
| Certification Service | 99.5% | < 10 s (async) | < 30 s | < 0.5% | 15 min | 1 min |
| Notification Service | 99.0% | < 30 s (async) | < 120 s | < 1% | 30 min | 5 min |
| Reporting Service | 99.0% | < 1 s (queries) | < 3 s | < 1% | 30 min | 15 min |
| Kafka Event Bus | 99.9% | < 10 ms (publish) | < 50 ms | < 0.01% | 5 min | 0 |
| PostgreSQL Primary | 99.99% | < 10 ms (OLTP) | < 50 ms | < 0.001% | 1 min | 0 |

---

## 7. Failure Containment Boundaries

```mermaid
flowchart TB
    subgraph zone_a[Failure Zone A — Learner Experience Critical]
        GW[API Gateway]
        IDS[Identity Service]
        LP[Learner Portal CDN]
    end

    subgraph zone_b[Failure Zone B — Core Learning]
        CRS[Course Service]
        ENS[Enrollment Service]
        ASS[Assessment Service]
        PRS[Progress Service]
    end

    subgraph zone_c[Failure Zone C — Grading & Cert]
        GRS[Grading Service]
        CES[Certification Service]
        GW2[Grading Worker]
        CW[Certificate Worker]
    end

    subgraph zone_d[Failure Zone D — Async Outputs]
        NTS[Notification Service]
        RPS[Reporting Service]
        PW[Projection Worker]
    end

    zone_a -->|Circuit Breaker| zone_b
    zone_b -->|Circuit Breaker| zone_c
    zone_c -->|Async, at-least-once| zone_d
```

| Zone | Components | Isolation Mechanism | Degraded Mode |
|---|---|---|---|
| A — Learner Experience | API Gateway, Identity, CDN | Redundant multi-AZ, health checks | Serve cached static assets; reject auth requests gracefully |
| B — Core Learning | Course, Enrollment, Assessment, Progress | Circuit breaker on inter-service calls | Read-only catalog; queue enrollment writes |
| C — Grading & Cert | Grading, Certification, Workers | Async queue buffers; retry with backoff | Submissions accepted; grading delayed; learners notified |
| D — Async Outputs | Notification, Reporting, Projection | At-least-once Kafka; dead-letter queues | Notifications delayed; dashboards stale; no data loss |
