# C4 Component Diagram - Learning Management System

This document presents the C4 Level 3 Component diagram for the API tier, plus supporting tables covering component descriptions, database interactions, event bus interactions, and golden signals for each component.

---

## C4 Level 3 — API Tier Component Diagram

Shows all internal components of the backend API application and their connections to data stores, the event bus, and external services.

```mermaid
flowchart TB
    LP([Learner Portal\nReact SPA])
    SW([Staff Workspace\nReact SPA])

    subgraph api[Backend API Application — Node.js · Kubernetes Deployment]

        subgraph auth_layer[Authentication & Authorization Layer]
            TLS_GW[TLS Termination\n& Rate Limiter\nNginx / Kong]
            JWT_V[JWT Validator\n& Claims Extractor]
            TENANT_R[Tenant Resolver\nslug → tenantId]
            RBAC_G[RBAC Guard\nrole × resource × action]
        end

        subgraph identity[Identity Component]
            USER_SVC[User Account\nManager]
            ROLE_SVC[Role Assignment\nService]
            IDP_ADPT[Identity Provider\nAdapter (OIDC/SAML)]
        end

        subgraph catalog[Catalog & Authoring Component]
            COURSE_SVC[Course Version\nLifecycle Service]
            MODULE_SVC[Module & Lesson\nManager]
            CONTENT_SVC[Content Upload\n& Delivery Service]
            PUB_SVC[Publication\nOrchestrator]
        end

        subgraph enrollment[Enrollment & Cohort Component]
            COHORT_SVC[Cohort\nManager]
            ENROLL_SVC[Enrollment\nOrchestrator]
            POLICY_SVC[Enrollment Policy\nEvaluator]
            SEAT_SVC[Seat Reservation\nService]
            IDEM_GUARD[Idempotency\nGuard]
        end

        subgraph assessment[Assessment Component]
            ATT_MGR[Attempt Lifecycle\nManager]
            Q_ENG[Question Delivery\nEngine]
            TIMER_SVC[Timer Service\n(Redis TTL)]
            ANS_STORE[Answer Persistence\nLayer]
            AUTOGRADE[Auto-Grading\nEngine]
            MR_QUEUE[Manual Review\nQueue]
        end

        subgraph grading[Grading & Feedback Component]
            REVIEW_SVC[Review Workflow\nService]
            RUBRIC_SVC[Rubric Scoring\nService]
            GRADE_MGR[Grade Record\nManager]
            OVERRIDE_SVC[Grade Override\nService]
        end

        subgraph progress[Progress Tracking Component]
            LESSON_SVC[Lesson Completion\nRecorder]
            PROG_PROJ[Progress\nProjector]
            COMP_EVAL[Completion\nEvaluator]
            RESUME_SVC[Resume State\nManager]
        end

        subgraph certification[Certification Component]
            CERT_EVAL[Completion Rule\nVerifier]
            CERT_GEN[Certificate\nGenerator]
            CERT_STORE[Certificate\nRepository]
            BADGE_ADPT[Badge Platform\nAdapter]
        end

        subgraph reporting[Reporting & Search Component]
            SEARCH_SVC[Catalog\nSearch Service]
            DASH_SVC[Dashboard\nQuery Service]
            EXPORT_SVC[Data Export\nService]
        end

        subgraph crosscut[Cross-Cutting Components]
            AUDIT_EVT[Audit Event\nEmitter]
            EVT_PUB[Domain Event\nPublisher\n(Kafka producer)]
            NOTIF_ADPT[Notification\nAdapter]
            CACHE_SVC[Cache Manager\n(Redis wrapper)]
        end
    end

    subgraph stores[Data Stores]
        PG[(PostgreSQL\nPrimary + Replica)]
        RD[(Redis\nSessions · Cache · Timers)]
        KF[(Kafka\nEvent Bus)]
        ES[(Elasticsearch)]
        S3[(Object Storage)]
    end

    subgraph ext[External Services]
        IDP([Identity Provider])
        EMAIL([Email / Push Provider])
        BADGE_EXT([Badge Platform])
    end

    LP --> TLS_GW
    SW --> TLS_GW
    TLS_GW --> JWT_V --> TENANT_R --> RBAC_G

    RBAC_G --> USER_SVC
    RBAC_G --> COURSE_SVC
    RBAC_G --> ENROLL_SVC
    RBAC_G --> ATT_MGR
    RBAC_G --> REVIEW_SVC
    RBAC_G --> LESSON_SVC
    RBAC_G --> CERT_EVAL
    RBAC_G --> SEARCH_SVC
    RBAC_G --> DASH_SVC

    USER_SVC --> PG
    USER_SVC --> CACHE_SVC
    ROLE_SVC --> PG
    IDP_ADPT --> IDP

    COURSE_SVC --> PG
    MODULE_SVC --> PG
    CONTENT_SVC --> S3
    PUB_SVC --> EVT_PUB
    PUB_SVC --> AUDIT_EVT

    COHORT_SVC --> PG
    ENROLL_SVC --> POLICY_SVC
    ENROLL_SVC --> SEAT_SVC
    ENROLL_SVC --> IDEM_GUARD
    ENROLL_SVC --> PG
    ENROLL_SVC --> EVT_PUB
    ENROLL_SVC --> AUDIT_EVT
    SEAT_SVC --> RD
    IDEM_GUARD --> RD

    ATT_MGR --> PG
    ATT_MGR --> Q_ENG
    ATT_MGR --> TIMER_SVC
    ATT_MGR --> AUTOGRADE
    ATT_MGR --> MR_QUEUE
    ATT_MGR --> EVT_PUB
    ATT_MGR --> AUDIT_EVT
    Q_ENG --> PG
    TIMER_SVC --> RD
    ANS_STORE --> PG
    AUTOGRADE --> PG
    MR_QUEUE --> PG

    REVIEW_SVC --> PG
    RUBRIC_SVC --> PG
    GRADE_MGR --> PG
    GRADE_MGR --> EVT_PUB
    GRADE_MGR --> AUDIT_EVT
    OVERRIDE_SVC --> PG
    OVERRIDE_SVC --> AUDIT_EVT

    LESSON_SVC --> PG
    LESSON_SVC --> EVT_PUB
    PROG_PROJ --> PG
    COMP_EVAL --> PG
    RESUME_SVC --> PG

    CERT_EVAL --> PG
    CERT_GEN --> S3
    CERT_GEN --> CERT_STORE
    CERT_STORE --> PG
    CERT_STORE --> EVT_PUB
    CERT_STORE --> AUDIT_EVT
    BADGE_ADPT --> BADGE_EXT

    SEARCH_SVC --> ES
    DASH_SVC --> PG
    EXPORT_SVC --> PG

    EVT_PUB --> KF
    NOTIF_ADPT --> EMAIL
    NOTIF_ADPT --> KF
    AUDIT_EVT --> PG
    CACHE_SVC --> RD
```

---

## Component Descriptions Table

| Component | Layer | Description | Owns |
|---|---|---|---|
| TLS Termination & Rate Limiter | Auth | Terminates TLS, enforces per-tenant and per-IP rate limits, forwards requests | Connection security, rate quotas |
| JWT Validator & Claims Extractor | Auth | Validates RS256 JWT, extracts `userId`, `tenantId`, `roles[]`, `exp` | Token verification |
| Tenant Resolver | Auth | Resolves tenant from JWT claim or subdomain slug; injects `tenantId` into request context | Tenant context |
| RBAC Guard | Auth | Enforces role-based access control on every route; rejects 403 on missing permission | Authorization decisions |
| User Account Manager | Identity | CRUD for user accounts; password reset; account status management | `users` table |
| Role Assignment Service | Identity | Assigns and revokes roles with scope (course, cohort, tenant); validates role hierarchy | `role_assignments` table |
| Identity Provider Adapter | Identity | OIDC/SAML federation adapter; maps external identity to internal user | IDP integration |
| Course Version Lifecycle Service | Catalog | Manages `CourseVersion` state machine: draft → review → published → archived | `course_versions` table |
| Module & Lesson Manager | Catalog | CRUD for modules and lessons; enforces ordering and sequence constraints | `modules`, `lessons` tables |
| Content Upload & Delivery Service | Catalog | Generates presigned S3 upload URLs; serves presigned download/stream URLs | Object storage objects |
| Publication Orchestrator | Catalog | Coordinates publish workflow: validates structure, emits events, updates search | Cross-aggregate publication |
| Cohort Manager | Enrollment | CRUD for cohorts; manages seat capacity and delivery windows | `cohorts` table |
| Enrollment Orchestrator | Enrollment | Entry point for all enrollment mutations; delegates to policy, seat, idempotency sub-components | `enrollments` table |
| Enrollment Policy Evaluator | Enrollment | Pure policy check: prerequisites, window, seat; returns `PolicyOutcome` | Policy logic (no writes) |
| Seat Reservation Service | Enrollment | Atomic seat reservation using Redis WATCH/MULTI; falls back to DB optimistic lock | Seat counters in Redis |
| Idempotency Guard | Enrollment | Checks and stores idempotency keys in Redis; prevents duplicate write effects | `idempotency:{tenantId}:{key}` Redis keys |
| Attempt Lifecycle Manager | Assessment | Enforces attempt state machine; validates limits; delegates to sub-components | `attempts` table |
| Question Delivery Engine | Assessment | Fetches questions for an attempt; applies randomisation seed per learner | Question delivery |
| Timer Service | Assessment | Creates Redis TTL for attempt timer; fires expiry callback | Redis timer keys |
| Answer Persistence Layer | Assessment | Idempotent upsert of answers; rejects writes on expired/submitted attempts | `answer_artifacts` table |
| Auto-Grading Engine | Assessment | Scores MCQ, T/F, matching, fill-in answers against answer key | Auto-grading logic |
| Manual Review Queue | Assessment | Queues submissions for manual review; implements claim/lock to prevent duplicate reviews | `grading_queue` table |
| Review Workflow Service | Grading | Manages reviewer assignment, draft scoring, and grade release workflow | `grading_queue`, draft state |
| Rubric Scoring Service | Grading | Aggregates per-criterion scores into final weighted total | Rubric aggregation |
| Grade Record Manager | Grading | Append-only grade record writes; enforces revision numbering; triggers events on release | `grade_records` table |
| Grade Override Service | Grading | Supervisor-initiated grade overrides; creates new revision; enforces audit trail | `grade_records` overrides |
| Lesson Completion Recorder | Progress | Idempotent lesson completion ingest; validates enrollment is active | `lesson_progress` table |
| Progress Projector | Progress | Recalculates `ProgressRecord` from lesson and grade events; updates percentage | `progress_records` table |
| Completion Evaluator | Progress | Evaluates `ProgressRecord` against `CompletionRule`; returns unmet criteria list | Completion determination |
| Resume State Manager | Progress | Tracks last-watched position per lesson; serves resume point | `lesson_progress.progressSeconds` |
| Completion Rule Verifier | Certification | Verifies all completion criteria before certificate issuance; idempotent check | Completion gate |
| Certificate Generator | Certification | Builds certificate PDF payload; stores in S3; records object URL | PDF generation |
| Certificate Repository | Certification | Persists `Certificate` records; enforces one-per-enrollment constraint | `certificates` table |
| Badge Platform Adapter | Certification | Issues Open Badge assertions to external badge platforms | Badge integration |
| Catalog Search Service | Reporting | Full-text course search using Elasticsearch | ES catalog index |
| Dashboard Query Service | Reporting | Aggregated learner and cohort dashboards from read replica | Reporting queries |
| Data Export Service | Reporting | Paginated CSV/JSON exports of enrollment and grade data | Bulk exports |
| Audit Event Emitter | Cross-cutting | Writes structured audit records for every domain mutation | `audit_logs` table |
| Domain Event Publisher | Cross-cutting | Kafka producer; ensures `acks=all`, idempotent; wraps all domain event publishing | Kafka topic writes |
| Notification Adapter | Cross-cutting | Publishes notification events to Kafka; consumed by Notification Worker | Notification dispatch |
| Cache Manager | Cross-cutting | Redis wrapper for metadata cache, session cache, hot-path data | Redis cache keys |

---

## Component-to-Database Interaction Table

| Component | Table(s) / Store | Operation | Consistency Requirement |
|---|---|---|---|
| User Account Manager | `users`, `tenants` | Read, Insert, Update | Strong (primary) |
| Role Assignment Service | `role_assignments` | Read, Insert, Soft-delete | Strong (primary) |
| Course Version Lifecycle | `courses`, `course_versions`, `completion_rules` | Read, Insert, Update | Strong (primary) |
| Module & Lesson Manager | `modules`, `lessons` | Read, Insert, Update, Delete | Strong (primary) |
| Cohort Manager | `cohorts` | Read, Insert, Update | Strong (primary) |
| Enrollment Orchestrator | `enrollments`, `cohorts.seatsUsed` | Insert + Update (single transaction) | Serializable isolation |
| Seat Reservation Service | Redis `seats:{cohortId}` | INCR / DECR / WATCH | Atomic (Redis transaction) |
| Idempotency Guard | Redis `idempotency:{tenantId}:{key}` | GET / SET with TTL | At-most-once SET |
| Attempt Lifecycle Manager | `attempts` | Insert, Update | Serializable (FOR UPDATE) |
| Answer Persistence Layer | `answer_artifacts` | Insert or Replace | Read-committed |
| Auto-Grading Engine | `questions`, `answer_artifacts`, `grade_records` | Read, Insert | Strong read, strong write |
| Manual Review Queue | `grading_queue` | Insert, Update | Strong (primary) |
| Grade Record Manager | `grade_records`, `grade_criterion_scores` | Insert (append-only) | Strong (primary) |
| Lesson Completion Recorder | `lesson_progress` | Insert (idempotent) | Read-committed |
| Progress Projector | `lesson_progress`, `progress_records` | Read, Update | Read replica for reads, primary for writes |
| Completion Evaluator | `progress_records`, `completion_rules` | Read only | Read replica |
| Completion Rule Verifier | `progress_records`, `completion_rules`, `certificates` | Read only | Read replica |
| Certificate Repository | `certificates` | Insert (one per enrollment) | Serializable (unique constraint) |
| Dashboard Query Service | `enrollments`, `progress_records`, `grade_records` | Read only | Read replica |
| Audit Event Emitter | `audit_logs` | Insert (append-only) | Async — best effort, fire-and-forget |

---

## Component-to-Event-Bus Interaction Table

| Component | Topic | Produces / Consumes | Event Types | Partition Key |
|---|---|---|---|---|
| Enrollment Orchestrator | `enrollment-events` | Produces | `ENROLLMENT_CREATED`, `ENROLLMENT_DROPPED`, `ENROLLMENT_EXPIRED`, `ENROLLMENT_COMPLETED` | `tenantId` |
| Publication Orchestrator | `catalog-events` | Produces | `COURSE_VERSION_PUBLISHED`, `COURSE_VERSION_ARCHIVED` | `tenantId` |
| Attempt Lifecycle Manager | `assessment-events` | Produces | `ATTEMPT_STARTED`, `ATTEMPT_SUBMITTED`, `ATTEMPT_EXPIRED` | `tenantId` |
| Grade Record Manager | `grading-events` | Produces | `GRADE_RELEASED`, `GRADE_OVERRIDDEN`, `MANUAL_REVIEW_QUEUED` | `tenantId` |
| Lesson Completion Recorder | `progress-events` | Produces | `LESSON_COMPLETED`, `PROGRESS_UPDATED` | `enrollmentId` |
| Certificate Repository | `certificate-events` | Produces | `CERTIFICATE_ISSUED`, `CERTIFICATE_REVOKED`, `CERTIFICATE_EXPIRED` | `tenantId` |
| Notification Adapter | All topics above | Consumes | All domain events | `tenantId` |
| Projection Worker | All topics above | Consumes | All domain events | `tenantId` |
| Grading Worker | `assessment-events` | Consumes | `ATTEMPT_SUBMITTED` | `tenantId` |
| Certificate Worker | `progress-events`, `grading-events` | Consumes | `PROGRESS_UPDATED`, `GRADE_RELEASED` | `enrollmentId` |

---

## Component Golden Signals

| Component | Latency (p95 target) | Error Rate (budget) | Throughput (expected) | Saturation Signal |
|---|---|---|---|---|
| TLS Termination & Rate Limiter | < 5 ms | < 0.01% | 5,000 req/s per node | CPU > 70% |
| JWT Validator | < 10 ms | < 0.01% | 5,000 req/s | Cache miss rate > 5% |
| RBAC Guard | < 5 ms | < 0.01% | 5,000 req/s | Policy eval time > 10 ms |
| Enrollment Orchestrator | < 500 ms | < 0.1% | 200 req/s | DB lock wait > 50 ms |
| Seat Reservation Service | < 10 ms | < 0.01% | 200 req/s | Redis contention > 5% |
| Attempt Lifecycle Manager | < 300 ms | < 0.1% | 500 req/s | DB FOR UPDATE wait > 100 ms |
| Timer Service | < 5 ms | < 0.01% | 500 starts/s | Redis key creation errors > 0 |
| Answer Persistence Layer | < 100 ms | < 0.1% | 2,000 saves/s | DB write latency > 50 ms |
| Auto-Grading Engine | < 500 ms | < 0.1% | 300 grades/s | CPU > 80% on grading worker |
| Manual Review Queue | < 100 ms | < 0.1% | 50 claims/s | Queue depth > 500 |
| Grade Record Manager | < 200 ms | < 0.1% | 200 releases/s | DB write latency > 100 ms |
| Progress Projector | < 200 ms | < 0.1% | 1,000 updates/s | DB replica lag > 1 s |
| Completion Evaluator | < 50 ms | < 0.01% | 500 evals/s | Read replica lag > 2 s |
| Certificate Generator | < 8 s (async) | < 0.5% | 50 certs/s | S3 write errors > 0 |
| Catalog Search Service | < 300 ms | < 0.1% | 2,000 queries/s | ES CPU > 70%; index lag > 5 min |
| Dashboard Query Service | < 1 s | < 0.5% | 200 queries/s | Read replica lag > 5 s |
| Domain Event Publisher | < 10 ms | < 0.01% | 2,000 events/s | Kafka producer queue depth > 1,000 |
| Audit Event Emitter | < 5 ms (async) | < 1% | 2,000 events/s | `audit_logs` write failures > 0 |
