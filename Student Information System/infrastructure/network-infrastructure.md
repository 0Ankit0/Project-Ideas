# Network Infrastructure

## Overview
Network and infrastructure diagrams showing the network topology, security zones, and connectivity for the Student Information System.

---

## Network Topology Diagram

```mermaid
graph TB
    subgraph "Internet"
        Users[Users / Clients]
        ExternalSystems[External Systems<br>Payment Gateways / LDAP / Library]
    end

    subgraph "AWS Cloud"
        subgraph "Edge / Public Layer"
            Route53[Route 53<br>DNS Resolution]
            CloudFront[CloudFront<br>CDN + Static Assets]
            WAF[AWS WAF<br>DDoS / Bot Protection]
        end

        subgraph "VPC - 10.0.0.0/16"
            subgraph "Public Subnet A - 10.0.1.0/24"
                ALB_A[Application Load Balancer A]
                NAT_A[NAT Gateway A]
                BastionA[Bastion Host A]
            end

            subgraph "Public Subnet B - 10.0.2.0/24"
                ALB_B[Application Load Balancer B]
                NAT_B[NAT Gateway B]
            end

            subgraph "Private Subnet A - App - 10.0.11.0/24"
                EKS_A[EKS Nodes A<br>SIS Application Pods]
            end

            subgraph "Private Subnet B - App - 10.0.12.0/24"
                EKS_B[EKS Nodes B<br>SIS Application Pods]
            end

            subgraph "Private Subnet A - Data - 10.0.21.0/24"
                RDS_Primary[(RDS Primary<br>PostgreSQL)]
                Redis_A[(ElastiCache<br>Redis Cluster A)]
            end

            subgraph "Private Subnet B - Data - 10.0.22.0/24"
                RDS_Standby[(RDS Standby)]
                Redis_B[(ElastiCache<br>Redis Cluster B)]
            end

            SecurityGroup_App[Security Group: App<br>Allow 8000 from ALB]
            SecurityGroup_DB[Security Group: DB<br>Allow 5432 from App SG]
        end

        S3[S3 Bucket<br>Documents / Transcripts]
        SES[Amazon SES<br>Transactional Email]
        SNS[Amazon SNS<br>SMS Notifications]
    end

    Users --> Route53
    Route53 --> CloudFront
    CloudFront --> WAF
    WAF --> ALB_A
    WAF --> ALB_B

    ALB_A --> EKS_A
    ALB_B --> EKS_B

    EKS_A --> RDS_Primary
    EKS_B --> RDS_Primary
    EKS_A --> Redis_A
    EKS_B --> Redis_B

    EKS_A --> S3
    EKS_B --> S3
    EKS_A --> SES
    EKS_A --> SNS

    RDS_Primary -.->|Multi-AZ Standby| RDS_Standby
    Redis_A <-.->|Cluster Replication| Redis_B

    EKS_A --> NAT_A
    EKS_B --> NAT_B
    NAT_A --> ExternalSystems
    NAT_B --> ExternalSystems
```

---

## Security Group Rules

### Application Layer Security Group

| Rule | Protocol | Port | Source | Purpose |
|------|----------|------|--------|---------|
| Inbound | HTTPS | 443 | ALB Security Group | API traffic |
| Inbound | HTTP | 8000 | ALB Security Group | Internal API |
| Outbound | TCP | 5432 | DB Security Group | PostgreSQL |
| Outbound | TCP | 6379 | Cache Security Group | Redis |
| Outbound | HTTPS | 443 | 0.0.0.0/0 via NAT | External services |

### Database Layer Security Group

| Rule | Protocol | Port | Source | Purpose |
|------|----------|------|--------|---------|
| Inbound | TCP | 5432 | App Security Group | PostgreSQL connections |
| Outbound | None | - | - | No outbound required |

---

## DNS and Routing

```mermaid
graph LR
    subgraph "DNS Structure"
        Domain[college.edu]
        SIS[sis.college.edu<br>Student Portal]
        Faculty[faculty.college.edu<br>Faculty Portal]
        Admin[admin.college.edu<br>Admin Dashboard]
        API[api.college.edu<br>REST API]
        Parent[parent.college.edu<br>Parent Portal]
    end

    subgraph "CloudFront Distributions"
        CF_Student[Student CDN]
        CF_Faculty[Faculty CDN]
        CF_Admin[Admin CDN]
        CF_API[API CDN / Pass-through]
    end

    Domain --> SIS
    Domain --> Faculty
    Domain --> Admin
    Domain --> API
    Domain --> Parent

    SIS --> CF_Student
    Faculty --> CF_Faculty
    Admin --> CF_Admin
    API --> CF_API
    Parent --> CF_Student
```

---

## Internal Service Mesh

```mermaid
graph TB
    subgraph "Kubernetes Cluster"
        subgraph "Service Mesh (Istio)"
            IngressGW[Istio Ingress Gateway]

            subgraph "Services"
                AuthSvc[auth-service:8000]
                StudentSvc[student-service:8000]
                CourseSvc[course-service:8000]
                EnrollSvc[enrollment-service:8000]
                GradeSvc[grade-service:8000]
                AttendanceSvc[attendance-service:8000]
                FeeSvc[fee-service:8000]
                NotifSvc[notification-service:8000]
            end
        end

        subgraph "Config and Secrets"
            ConfigMap[ConfigMap<br>App Configuration]
            Secrets[Kubernetes Secrets<br>DB Creds, API Keys]
        end
    end

    IngressGW --> AuthSvc
    IngressGW --> StudentSvc
    IngressGW --> CourseSvc
    IngressGW --> EnrollSvc
    IngressGW --> GradeSvc
    IngressGW --> AttendanceSvc
    IngressGW --> FeeSvc

    EnrollSvc --> NotifSvc
    GradeSvc --> NotifSvc
    AttendanceSvc --> NotifSvc
    FeeSvc --> NotifSvc

    AuthSvc --> Secrets
    FeeSvc --> Secrets
    StudentSvc --> ConfigMap
```

---

## Monitoring and Observability

```mermaid
graph TB
    subgraph "Application"
        SISApp[SIS Application Pods]
    end

    subgraph "Observability Stack"
        Prometheus[Prometheus<br>Metrics Collection]
        Grafana[Grafana<br>Dashboards]
        Jaeger[Jaeger<br>Distributed Tracing]
        ELK[ELK Stack<br>Log Aggregation]
    end

    subgraph "Alerting"
        AlertManager[Alert Manager]
        PagerDuty[PagerDuty<br>On-call Alerts]
    end

    SISApp -->|Metrics| Prometheus
    SISApp -->|Traces| Jaeger
    SISApp -->|Logs| ELK

    Prometheus --> Grafana
    Prometheus --> AlertManager
    AlertManager --> PagerDuty

    Jaeger --> Grafana
    ELK --> Grafana
```

---

## Backup and Disaster Recovery

| Component | Backup Strategy | RPO | RTO |
|-----------|----------------|-----|-----|
| PostgreSQL | Hourly incremental + daily full; Multi-AZ standby | 1 hour | 30 minutes |
| Redis | Multi-node cluster; point-in-time snapshots | 15 minutes | 15 minutes |
| S3 (Documents) | Cross-region replication; versioning enabled | Near-zero | Near-zero |
| Application Config | Git-managed; ArgoCD reconciliation | Minutes | Minutes |

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

