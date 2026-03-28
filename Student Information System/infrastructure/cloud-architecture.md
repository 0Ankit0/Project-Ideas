# Cloud Architecture

## Overview
Cloud architecture diagrams showing the AWS infrastructure design for the Student Information System, including compute, storage, databases, networking, and managed services.

---

## AWS Cloud Architecture Overview

```mermaid
graph TB
    subgraph "Users"
        Students[Students]
        Faculty[Faculty]
        Admin[Admin Staff]
        Parents[Parents]
    end

    subgraph "Edge Services"
        Route53[Route 53<br>DNS]
        CloudFront[CloudFront<br>CDN + WAF]
        Certificate[ACM<br>SSL/TLS]
    end

    subgraph "AWS Region - ap-southeast-1"
        subgraph "Compute - EKS"
            EKS[EKS Cluster<br>SIS Application]
            Workers[Worker Node Group<br>m6i.large x 4-8 nodes]
            HPA[Horizontal Pod Autoscaler]
        end

        subgraph "Load Balancing"
            ALB[Application Load Balancer<br>Multi-AZ]
        end

        subgraph "Database Tier"
            RDS[RDS PostgreSQL<br>db.r6g.xlarge Multi-AZ]
            RDS_Read[RDS Read Replica<br>db.r6g.large x 2]
        end

        subgraph "Caching Tier"
            ElastiCache[ElastiCache Redis<br>cache.r6g.large Cluster]
        end

        subgraph "Storage"
            S3_Docs[S3 Bucket<br>Documents / Transcripts]
            S3_Static[S3 Bucket<br>Static Assets]
            S3_Backups[S3 Bucket<br>Database Backups]
        end

        subgraph "Messaging"
            SES[SES<br>Transactional Email]
            SNS[SNS<br>SMS / Push Notifications]
            SQS[SQS<br>Async Task Queue]
        end

        subgraph "Security"
            IAM_AWS[IAM<br>Roles and Policies]
            KMS[KMS<br>Encryption Keys]
            SecretsManager[Secrets Manager<br>DB Creds / API Keys]
            WAF_Service[WAF<br>Web Application Firewall]
        end

        subgraph "Monitoring"
            CloudWatch[CloudWatch<br>Logs / Metrics / Alarms]
            XRay[X-Ray<br>Distributed Tracing]
        end
    end

    Students --> CloudFront
    Faculty --> CloudFront
    Admin --> CloudFront
    Parents --> CloudFront

    CloudFront --> Certificate
    CloudFront --> Route53
    CloudFront --> WAF_Service
    WAF_Service --> ALB
    ALB --> EKS

    EKS --> Workers
    Workers --> HPA

    EKS --> RDS
    EKS --> RDS_Read
    EKS --> ElastiCache
    EKS --> S3_Docs
    EKS --> S3_Static
    EKS --> SES
    EKS --> SNS
    EKS --> SQS

    EKS --> SecretsManager
    EKS --> KMS
    EKS --> IAM_AWS

    EKS --> CloudWatch
    EKS --> XRay

    RDS -.->|Automated Backup| S3_Backups
    RDS -->|Replication| RDS_Read
```

---

## Auto-Scaling Architecture

```mermaid
graph LR
    subgraph "Load Triggers"
        Enrollment[Enrollment Window<br>High Traffic]
        ExamPeriod[Exam Period<br>Result Viewing]
        Regular[Regular Day<br>Normal Traffic]
    end

    subgraph "Scaling Policies"
        HPA[Kubernetes HPA<br>Pod Autoscaling<br>CPU > 70%]
        CA[Cluster Autoscaler<br>Node Autoscaling<br>Pending Pods]
    end

    subgraph "Infrastructure"
        Pods[Application Pods<br>2-10 per service]
        Nodes[Worker Nodes<br>2-8 nodes]
    end

    Enrollment -->|Scale Up| HPA
    ExamPeriod -->|Scale Up| HPA
    Regular -->|Scale Down| HPA
    HPA --> Pods
    Pods -->|Node Pressure| CA
    CA --> Nodes
```

---

## Data Residency and Compliance Architecture

```mermaid
graph TB
    subgraph "Primary Region"
        AppTier[Application Tier<br>SIS Services]
        DataTier[Data Tier<br>Student Records]
        BackupTier[Backup Tier<br>Automated Backups]
    end

    subgraph "DR Region"
        DR_Data[DR Data Tier<br>Cross-region replica]
        DR_Backup[DR Backup Storage]
    end

    subgraph "Compliance Controls"
        FERPA[FERPA Compliance<br>Student Data Privacy]
        Encrypt[Encryption at Rest<br>KMS-managed keys]
        Audit[Audit Logging<br>CloudTrail + CloudWatch]
        AccessControl[Access Control<br>IAM + RBAC]
    end

    AppTier --> DataTier
    DataTier --> BackupTier
    DataTier -.->|Async Replication| DR_Data
    BackupTier -.->|Cross-region Copy| DR_Backup

    AppTier --> FERPA
    DataTier --> Encrypt
    AppTier --> Audit
    AppTier --> AccessControl
```

---

## External Integration Architecture

```mermaid
graph TB
    subgraph "SIS Platform"
        FeeModule[Fee Module]
        IAMModule[IAM Module]
        AttendanceModule[Attendance Module]
        NotificationModule[Notification Module]
        EnrollmentModule[Enrollment Module]
    end

    subgraph "External Services"
        PaymentGW[Payment Gateways<br>Bank / Cards / UPI]
        LDAP_EXT[LDAP / AD<br>Institutional SSO]
        Biometric[Biometric Devices<br>Attendance API]
        LibraryAPI[Library System<br>REST API]
        ERPSystem[ERP / Finance<br>Fee Sync]
        EmailProv[Email Provider<br>SES / SendGrid]
        SMSProv[SMS Provider<br>SNS / Twilio]
        PushProv[Push Provider<br>FCM / APNs]
    end

    FeeModule -->|HTTPS| PaymentGW
    IAMModule -->|LDAPS| LDAP_EXT
    AttendanceModule -->|REST API| Biometric
    EnrollmentModule -->|REST API| LibraryAPI
    FeeModule -->|REST API| ERPSystem
    NotificationModule -->|SMTP/API| EmailProv
    NotificationModule -->|API| SMSProv
    NotificationModule -->|API| PushProv
```

---

## Cloud Cost Optimization Strategy

| Service | Strategy | Expected Saving |
|---------|----------|----------------|
| EKS Nodes | Reserved instances for baseline; Spot for burst | 30-40% |
| RDS | Reserved instances with 1-year commitment | 35-40% |
| ElastiCache | Reserved nodes | 30-35% |
| S3 | Intelligent-Tiering for infrequent documents | 15-20% |
| CloudFront | Cache optimization for static assets | Reduced origin costs |
| SQS/SNS | On-demand; low base cost | Pay-per-use |

## Enrollment, Academic Integrity, Access Control, and Integration Contracts (Implementation-Ready)

### 1) Enrollment Lifecycle Rules (Authoritative)

#### 1.1 Lifecycle States and Transitions
| State | Entry Criteria | Exit Criteria | Allowed Actors | Terminal? |
|---|---|---|---|---|
| Prospect | Lead captured or inquiry created | Application submitted | Admissions CRM, Applicant | No |
| Applicant | Complete application + required docs | Admitted or Rejected | Applicant, Admissions Officer | No |
| Admitted | Admission decision = accepted | Matriculated or Offer Expired | Admissions, Registrar | No |
| Matriculated | Identity + eligibility checks passed | Enrolled for a term | Registrar | No |
| Enrolled (Term-Scoped) | Registered in >=1 credit-bearing section | Dropped all sections, Term Completed | Student, Advisor, Registrar | No |
| Active (Institution-Scoped) | Student is not graduated/withdrawn/dismissed | Graduated, Withdrawn, Dismissed | SIS policy engine | No |
| Leave of Absence | Approved leave request in valid window | Reinstated, Withdrawn, Dismissed | Student, Advisor, Registrar | No |
| Graduated | Degree audit complete + conferral approved | N/A | Registrar | Yes |
| Withdrawn | Approved withdrawal workflow complete | Reinstated (rare policy path) | Student, Registrar | Yes* |
| Dismissed | Policy or disciplinary action finalized | Reinstated by exception | Registrar, Academic Board | Yes* |

> *Terminal under normal policy; reinstatement requires exceptional workflow and two-party approval (advisor + registrar/board).

#### 1.2 Deterministic State Machine
```mermaid
stateDiagram-v2
    [*] --> Prospect
    Prospect --> Applicant: submitApplication
    Applicant --> Admitted: admissionAccepted
    Applicant --> [*]: admissionRejected
    Admitted --> Matriculated: identityVerified + docsCleared
    Matriculated --> Enrolled: registerForTerm
    Enrolled --> Active: termStart
    Active --> Enrolled: nextTermRegistration
    Active --> LeaveOfAbsence: approvedLeave
    LeaveOfAbsence --> Active: reinstatementApproved
    Active --> Graduated: conferralApproved
    Active --> Withdrawn: withdrawalFinalized
    Active --> Dismissed: dismissalFinalized
```

#### 1.3 Enrollment/Registration Enforcement Rules
- **EL-001 Window Governance:** add/drop/withdraw windows are configured per term, program, and campus timezone; requests outside windows require override reason code.
- **EL-002 Seat Allocation:** seat release follows deterministic priority `(cohortPriority DESC, waitlistTimestamp ASC, randomTieBreakerSeed ASC)`.
- **EL-003 Prerequisite Resolution:** prerequisite checks run against canonical attempt history with in-progress and transfer-credit handling flags.
- **EL-004 Conflict Detection:** section enrollment is rejected if timetable overlap, credit overload, hold, or missing approval constraints fail.
- **EL-005 Downstream Consistency:** enrollment state changes emit events for LMS roster sync, fee recalculation, attendance eligibility, and aid re-evaluation.
- **EL-006 Re-Enrollment Gate:** reinstatement requires cleared financial/disciplinary holds and advisor + registrar approvals.

### 2) Grading and Transcript Consistency Constraints

#### 2.1 Grade Lifecycle and Versioning
- **GC-001 Immutable Posting:** once a grade version is `POSTED`, it is immutable.
- **GC-002 Amendment Model:** corrections create a new version linked by `supersedesGradeVersionId`; no in-place edits.
- **GC-003 Reason Codes:** every amendment must provide standardized reason (`CALCULATION_ERROR`, `LATE_SUBMISSION_APPROVED`, `INCOMPLETE_RESOLUTION`, etc.).
- **GC-004 Effective Dating:** transcript rendering always uses latest `effective=true` grade version at render time.

#### 2.2 Canonical Consistency Rules
| Rule ID | Constraint | Failure Handling |
|---|---|---|
| TR-001 | Transcript rows derive only from canonical course-attempt + grade-version records | Block issuance and raise registrar task |
| TR-002 | GPA/CGPA computed from policy-bound grade points and repeat/forgiveness rules | Recompute job queued; stale cache invalidated |
| TR-003 | Standing/honors/SAP updates run after each posted or amended grade event | Trigger synchronous policy check + async reconciliation |
| TR-004 | Official transcript issuance requires registrar sign-off + tamper-evident hash | Refuse release if signature or hash missing |
| TR-005 | Retroactive grade changes require impact statements (prereq, audit, aid, standing) | Hold change in `PENDING_IMPACT_REVIEW` |

#### 2.3 Grade Correction Sequence (Required)
```mermaid
sequenceDiagram
    participant F as Faculty
    participant SIS as SIS API
    participant R as Registrar
    participant GP as Grade Policy Engine
    participant TX as Transcript Service
    participant AU as Audit Log

    F->>SIS: Submit grade amendment (attemptId, newGrade, reasonCode)
    SIS->>GP: Validate policy window + authority + reason
    GP-->>SIS: Validation result
    alt valid
        SIS->>AU: Append immutable audit event
        SIS->>SIS: Create new gradeVersion (supersedes old)
        SIS->>TX: Recompute transcript/GPA/standing deltas
        TX-->>R: Impact report + approval task
        R->>SIS: Approve correction
        SIS-->>F: Amendment finalized
    else invalid
        SIS-->>F: Reject with machine-readable errors
    end
```

### 3) Role-Based Access Specifics (RBAC + ABAC)

#### 3.1 Access Model
- **RBAC baseline** grants capability by role.
- **ABAC overlays** constrain by context attributes: campus, department, term, section assignment, advisee linkage, data sensitivity, legal hold.
- **Break-glass access** is time-bound, ticket-linked, and dual-approved.

#### 3.2 Permission Matrix (Minimum Required)
| Capability | Student | Faculty | Advisor | Registrar/Admin | Notes |
|---|---:|---:|---:|---:|---|
| View own transcript | ✅ | ❌ | ❌ | ✅ | Student self-service allowed |
| Submit final grades | ❌ | ✅* | ❌ | ✅ | *Assigned sections + open window only |
| Amend posted grade | ❌ | Request | ❌ | ✅ | Registrar finalizes amendments |
| Approve overload/waiver petition | ❌ | ❌ | ✅ | ✅ | Program-scoped |
| Release official transcript | ❌ | ❌ | ❌ | ✅ | Requires digital signature policy |
| View disciplinary records | Limited | ❌ | Limited | Scoped | Enhanced logging required |

#### 3.3 Security and Audit Controls
- **AC-001** least privilege defaults; deny-by-default policy on all privileged endpoints.
- **AC-002** MFA required for registrar/admin and any user performing grade or transcript actions.
- **AC-003** field-level masking for PII/financial attributes in UI, exports, and logs.
- **AC-004** all read/write of sensitive records generate audit events with `actorId`, `scope`, `justification`, `requestId`.
- **AC-005** periodic entitlement recertification (at least once per term).

### 4) Integration Contracts for External Systems

#### 4.1 Contract-First Standards
- APIs must publish OpenAPI/AsyncAPI artifacts with JSON Schema references and semantic versions.
- Breaking changes require version increment and migration window policy.
- Event contracts are backward-compatible for at least one full term unless emergency exception approved.

#### 4.2 External Integration Surface
| System | Direction | Contract Type | SLA/SLO | Idempotency Key |
|---|---|---|---|---|
| LMS | Bi-directional | REST + Events | Roster sync < 5 min | `termId:sectionId:studentId:eventType` |
| IdP/SSO | Inbound auth + outbound provisioning | SAML/OIDC + SCIM | Login p95 < 2s | `provisioningRequestId` |
| Payment Gateway | Outbound payment + inbound webhook | REST + Signed Webhooks | Payment callback < 60s | `invoiceId:attemptNo` |
| Financial Aid | Bi-directional | REST + Batch SFTP (optional) | Aid status < 15 min | `aidApplicationId:termId` |
| Library | Bi-directional | REST | Borrowing status < 10 min | `studentId:loanId:eventType` |
| Regulatory Reporting | Outbound | Secure file/API | Deadline-bound batch | `reportPeriod:studentId:recordType` |

#### 4.3 Event Contract Baseline
```mermaid
flowchart LR
    A[Enrollment/Grade Change in SIS] --> B[Outbox Event Store]
    B --> C[Event Publisher]
    C --> D[LMS]
    C --> E[Billing/Payments]
    C --> F[Financial Aid]
    C --> G[Analytics Warehouse]
    C --> H[Notification Service]
```

Required event metadata fields:
- `eventId`, `eventType`, `schemaVersion`, `occurredAt`, `sourceSystem`, `correlationId`, `idempotencyKey`
- domain IDs: `studentId`, `termId`, `courseOfferingId`, `attemptId`, `gradeVersionId` (as applicable)

#### 4.4 Reliability, Security, and Drift Controls
- **IC-001** retries use exponential backoff + jitter; dead-letter queues mandatory.
- **IC-002** all webhook callbacks must be signed and timestamp-validated.
- **IC-003** encryption in transit (TLS 1.2+) and at rest for replicated payload stores.
- **IC-004** contract tests + sandbox certification are release gates for enrollment/grade/transcript/billing changes.
- **IC-005** schema drift detection runs continuously and blocks incompatible deploys.

### 5) Operational Readiness and Acceptance Criteria

#### 5.1 Observability and SLOs
- Enrollment action API p95 latency <= 400ms during peak registration.
- Grade posting-to-transcript consistency <= 2 minutes (p99).
- LMS roster propagation <= 5 minutes (p99).
- Audit event durability >= 99.999% persisted write success.

#### 5.2 Data Retention and Compliance
- Grade versions and transcript issuance records are retained per institutional and statutory policy (minimum 7 years where applicable).
- Audit logs for sensitive operations retained in immutable storage tier with legal hold support.
- Data subject access/deletion requests must preserve legally required academic records with redaction-by-policy.

#### 5.3 Implementation-Ready Test Scenarios
1. Waitlist promotion tie-breaker determinism under concurrent seat release.
2. Retroactive grade correction impact on prerequisites and degree audit.
3. Unauthorized faculty grade amendment blocked with explicit error code.
4. Payment webhook replay handled idempotently without duplicate ledger entries.
5. Transcript signature/hash verification fails on tampered artifact.
6. Re-enrollment blocked when financial hold exists; succeeds after hold clearance.

