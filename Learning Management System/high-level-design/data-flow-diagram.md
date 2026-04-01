# Data Flow Diagram - Learning Management System

This document describes data flows at three levels of abstraction: the system context (Level 0), the main internal processes (Level 1), and the assessment and grading sub-process in detail (Level 2). Security classifications and data store descriptions are also provided.

---

## Level-0 DFD — Context Diagram

Shows the LMS as a single process interacting with external entities. No internal structure is visible at this level.

```mermaid
flowchart LR
    L([Learner])
    S([Instructor / Staff])
    A([Admin])
    IDP([Identity Provider\nOIDC / SAML])
    LIVE([Live Session Provider\ne.g. Zoom / Teams])
    NOTIF([Notification Provider\nEmail / SMS / Push])
    BI([Analytics / BI Platform])
    BADGE([Badge / Credential Platform])

    L -- "Course requests,\nsubmissions, progress" --> LMS[( Learning Management\nSystem )]
    S -- "Course authoring,\nreview, grading" --> LMS
    A -- "Tenant config,\nuser management" --> LMS
    LMS -- "Catalog, grades,\ncertificates, dashboards" --> L
    LMS -- "Grading queues,\ncourse analytics" --> S
    LMS -- "Audit logs,\nreporting" --> A
    LMS -- "Auth tokens\n(OAuth 2.0 / OIDC)" --> IDP
    IDP -- "Identity assertion" --> LMS
    LMS -- "Session join links,\nattendance hooks" --> LIVE
    LMS -- "Notification payloads\n(email, push, SMS)" --> NOTIF
    LMS -- "Event streams\n(anonymised)" --> BI
    LMS -- "Certificate assertions\n(Open Badges / CLR)" --> BADGE
```

---

## Level-1 DFD — Main Processes

Decomposes the LMS into its seven primary processing nodes and shows the data flows between them and the data stores.

```mermaid
flowchart TB
    L([Learner])
    S([Instructor / Staff])
    A([Admin])

    subgraph processes[Core Processes]
        P1[1. Identity &\nAccess Control]
        P2[2. Catalog &\nAuthoring]
        P3[3. Enrollment &\nCohort Management]
        P4[4. Content Delivery &\nProgress Tracking]
        P5[5. Assessment &\nGrading]
        P6[6. Certification]
        P7[7. Reporting &\nSearch]
    end

    subgraph stores[Data Stores]
        DS1[(D1: User & Tenant Store\nPostgreSQL)]
        DS2[(D2: Course Catalog Store\nPostgreSQL + Object Storage)]
        DS3[(D3: Enrollment Store\nPostgreSQL)]
        DS4[(D4: Progress Store\nPostgreSQL)]
        DS5[(D5: Assessment Store\nPostgreSQL)]
        DS6[(D6: Certificate Store\nPostgreSQL + Object Storage)]
        DS7[(D7: Search Index\nElasticsearch)]
        DS8[(D8: Event Bus\nKafka / SQS)]
    end

    L -- "Login credentials" --> P1
    S -- "Login credentials" --> P1
    A -- "Admin credentials" --> P1
    P1 -- "Validated identity,\ntenant context" --> P2
    P1 -- "Validated identity" --> P3
    P1 -- "Validated identity" --> P4
    P1 -- "Validated identity" --> P5
    P1 <--> DS1

    S -- "Course content,\nmetadata" --> P2
    P2 -- "Published catalog" --> DS2
    P2 -- "Catalog events" --> DS8
    P2 -- "Indexed catalog" --> DS7
    L -- "Course discovery\nqueries" --> P7
    P7 -- "Search results" --> L

    L -- "Enrollment request" --> P3
    P3 -- "Enrollment record" --> DS3
    P3 -- "Enrollment events" --> DS8

    L -- "Lesson interactions,\ncheckpoints" --> P4
    P4 <--> DS4
    P4 -- "Progress events" --> DS8

    L -- "Assessment answers,\nsubmission" --> P5
    S -- "Rubric scores,\nfeedback" --> P5
    P5 <--> DS5
    P5 -- "Grade events" --> DS8

    DS8 -- "Grade events" --> P6
    DS8 -- "Progress events" --> P6
    P6 -- "Certificate record + PDF" --> DS6
    P6 -- "Certificate events" --> DS8

    DS8 -- "All domain events" --> P7
    P7 <--> DS7
    P7 -- "Dashboards,\nreports, exports" --> S
    P7 -- "Dashboards,\nreports, exports" --> A
```

---

## Level-2 DFD — Assessment and Grading Sub-Process

Zooms into Process 5 (Assessment & Grading) to show its internal data flows in detail.

```mermaid
flowchart TB
    L([Learner])
    S([Instructor / Reviewer])
    DS5[(D5: Assessment Store)]
    DS4[(D4: Progress Store)]
    DS8[(D8: Event Bus)]

    subgraph P5[Process 5: Assessment & Grading]
        P5_1[5.1 Attempt\nLifecycle Manager]
        P5_2[5.2 Question\nDelivery Engine]
        P5_3[5.3 Answer\nPersistence]
        P5_4[5.4 Timer\nService]
        P5_5[5.5 Auto-Grading\nEngine]
        P5_6[5.6 Manual Review\nQueue]
        P5_7[5.7 Rubric\nScoring Service]
        P5_8[5.8 Grade Record\nManager]
    end

    L -- "Start attempt" --> P5_1
    P5_1 -- "Attempt record\n{attemptId, startedAt}" --> DS5
    P5_1 -- "Start timer" --> P5_4
    P5_1 -- "Fetch questions" --> P5_2
    P5_2 -- "Question set\n(shuffled/ordered)" --> L
    P5_4 -- "Timer context\n{expiresAt}" --> L

    L -- "Answer payload\n{questionId, answerValue}" --> P5_3
    P5_3 -- "AnswerArtifact rows" --> DS5

    L -- "Submit signal" --> P5_1
    P5_4 -- "Expiry signal" --> P5_1
    P5_1 -- "SUBMITTED status" --> DS5

    P5_1 -- "Route by gradingMode" --> P5_5
    P5_1 -- "Route by gradingMode" --> P5_6

    P5_5 -- "Read answer key" --> DS5
    P5_5 -- "Scored questions\n{questionId, earnedPoints}" --> P5_8

    S -- "Claim review task" --> P5_6
    P5_6 -- "Attempt + rubric\n+ answers" --> S
    S -- "Criterion scores\n+ feedback" --> P5_7
    P5_7 -- "Aggregated score\n{criterionScores[], total}" --> P5_8

    P5_8 -- "GradeRecord\n{revisionNo, finalScore,\nstatus, releasedAt}" --> DS5
    P5_8 -- "GRADE_RELEASED event" --> DS8
    DS8 -- "GRADE_RELEASED" --> DS4
    DS4 -- "Trigger progress\nrecalculation" --> DS4
```

---

## Data Flow Security Classification

| Data Flow | Classification | Transport Encryption | Auth Requirement | PII Present | Retention |
|---|---|---|---|---|---|
| Learner login credentials → Identity | **RESTRICTED** | TLS 1.3 | None (pre-auth) | Yes (email) | Not stored |
| JWT → API services | **CONFIDENTIAL** | TLS 1.3 | Bearer token | Yes (userId) | Token TTL only |
| Course content → Object Storage | **INTERNAL** | TLS 1.3 | Service-to-service mTLS | No | Course lifetime |
| Answer artifacts → Assessment Store | **CONFIDENTIAL** | TLS 1.3 | User-scoped JWT | Yes (learner answers) | 7 years |
| Grade records → Progress Store | **CONFIDENTIAL** | TLS 1.3 | Service-to-service mTLS | Yes (score, userId) | 7 years |
| Events → Event Bus | **INTERNAL** | TLS 1.3 | Service credentials | Pseudonymised | 90 days |
| Events → Analytics / BI | **INTERNAL** | TLS 1.3 | Service credentials | Anonymised | 3 years |
| Certificate PDF → Object Storage | **CONFIDENTIAL** | TLS 1.3 | Service-to-service mTLS | Yes (learner name) | Permanent |
| Certificate assertions → Badge Platforms | **PUBLIC** | TLS 1.3 | API key | Learner-consented | Permanent |
| Audit logs → Audit Store | **RESTRICTED** | TLS 1.3 | Privileged service only | Yes | 7 years |
| Anonymised events → BI | **PUBLIC** | TLS 1.3 | API key | No | 3 years |

---

## Data Store Descriptions

| Store ID | Name | Technology | Consistency Model | Primary Owner | Description |
|---|---|---|---|---|---|
| D1 | User & Tenant Store | PostgreSQL | Strong (ACID) | Identity Service | User accounts, role assignments, tenant configuration, audit subjects |
| D2 | Course Catalog Store | PostgreSQL + S3-compatible | Strong (metadata), eventual (blobs) | Course Service | Course/version/module/lesson metadata; lesson content blobs in object storage |
| D3 | Enrollment Store | PostgreSQL | Strong (ACID) | Enrollment Service | Enrollment records, cohort seat counters (optimistic locking), idempotency keys |
| D4 | Progress Store | PostgreSQL | Strong writes, eventual reads | Progress Service | `LessonProgress` rows, `ProgressRecord` summaries; updated on grade/lesson events |
| D5 | Assessment Store | PostgreSQL | Strong (ACID) | Assessment + Grading Services | Attempts, answer artifacts, grade records, rubric definitions, answer keys |
| D6 | Certificate Store | PostgreSQL + S3-compatible | Strong (metadata), eventual (PDFs) | Certification Service | Certificate records, verification codes, PDF object URLs |
| D7 | Search Index | Elasticsearch | Eventual | Reporting Service | Catalog search, learner-facing course discovery, staff reporting projections |
| D8 | Event Bus | Kafka / AWS SQS+SNS | At-least-once delivery | Platform-wide | Domain events; partitioned by `tenantId`; consumers maintain idempotency |
