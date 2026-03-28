# Deployment Diagram

## Overview
Deployment diagrams showing the mapping of software components to hardware and infrastructure for the Student Information System.

---

## Production Deployment Architecture

```mermaid
graph TB
    subgraph "Internet"
        Users[Users/Clients]
    end

    subgraph "Edge Layer"
        DNS[Route 53 DNS]
        CloudFront[CloudFront CDN]
        WAF[AWS WAF]
    end

    subgraph "AWS Region - Primary"
        subgraph "VPC - Production"
            subgraph "Public Subnet AZ-A"
                ALB_A[Application Load Balancer]
                NAT_A[NAT Gateway]
            end

            subgraph "Public Subnet AZ-B"
                ALB_B[Application Load Balancer]
                NAT_B[NAT Gateway]
            end

            subgraph "Private Subnet AZ-A - Application"
                EKS_A[EKS Worker Nodes]
            end

            subgraph "Private Subnet AZ-B - Application"
                EKS_B[EKS Worker Nodes]
            end

            subgraph "Private Subnet AZ-A - Data"
                RDS_Primary[(RDS Primary)]
                ElastiCache_A[(ElastiCache)]
            end

            subgraph "Private Subnet AZ-B - Data"
                RDS_Standby[(RDS Standby)]
                ElastiCache_B[(ElastiCache)]
            end
        end

        EKS_Control[EKS Control Plane<br>AWS Managed]
        S3[S3 Buckets<br>Documents/Transcripts]
        SES[Amazon SES<br>Email Service]
        SNS[Amazon SNS<br>SMS and Push]
    end

    Users --> DNS
    DNS --> CloudFront
    CloudFront --> WAF
    WAF --> ALB_A
    WAF --> ALB_B

    ALB_A --> EKS_A
    ALB_B --> EKS_B

    EKS_A --> RDS_Primary
    EKS_B --> RDS_Primary
    EKS_A --> ElastiCache_A
    EKS_B --> ElastiCache_B

    EKS_A --> S3
    EKS_B --> S3
    EKS_A --> SES
    EKS_A --> SNS

    RDS_Primary -.-> RDS_Standby
    ElastiCache_A <-.-> ElastiCache_B

    EKS_Control --> EKS_A
    EKS_Control --> EKS_B
```

---

## Kubernetes Deployment

```mermaid
graph TB
    subgraph "EKS Cluster"
        subgraph "Ingress"
            Ingress[NGINX Ingress Controller]
        end

        subgraph "API Layer"
            Gateway[Kong API Gateway<br>2 replicas]
        end

        subgraph "Services Namespace"
            subgraph "Auth Domain"
                AuthSvc[Auth Service<br>2 replicas]
            end

            subgraph "Student Domain"
                StudentSvc[Student Service<br>3 replicas]
                AdvisorSvc[Advisor Service<br>2 replicas]
            end

            subgraph "Academic Domain"
                CourseSvc[Course Service<br>3 replicas]
                EnrollSvc[Enrollment Service<br>3 replicas]
                GradeSvc[Grade Service<br>3 replicas]
            end

            subgraph "Attendance Domain"
                AttendanceSvc[Attendance Service<br>2 replicas]
            end

            subgraph "Fee Domain"
                FeeSvc[Fee Service<br>2 replicas]
                PaymentSvc[Payment Service<br>2 replicas]
            end

            subgraph "Communication Domain"
                NotifSvc[Notification Service<br>2 replicas]
                MsgSvc[Messaging Service<br>2 replicas]
            end

            subgraph "Reporting Domain"
                ReportSvc[Report Service<br>2 replicas]
            end
        end

        subgraph "Workers Namespace"
            NotifWorker[Notification Worker<br>2 replicas]
            ReportWorker[Report Worker<br>2 replicas]
        end

        subgraph "Monitoring Namespace"
            Prometheus[Prometheus]
            Grafana[Grafana]
            Jaeger[Jaeger]
        end
    end

    Ingress --> Gateway
    Gateway --> AuthSvc
    Gateway --> StudentSvc
    Gateway --> CourseSvc
    Gateway --> EnrollSvc
    Gateway --> GradeSvc
    Gateway --> AttendanceSvc
    Gateway --> FeeSvc
    Gateway --> PaymentSvc
    Gateway --> NotifSvc
    Gateway --> ReportSvc
```

---

## Service Deployment Specifications

### Deployment YAML Example

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: enrollment-service
  namespace: services
spec:
  replicas: 3
  selector:
    matchLabels:
      app: enrollment-service
  template:
    metadata:
      labels:
        app: enrollment-service
    spec:
      containers:
      - name: enrollment-service
        image: ecr.aws/sis/enrollment-service:v1.0.0
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: service-config
              key: redis-url
```

---

## Deployment Environment Matrix

| Service | Dev | Staging | Production |
|---------|-----|---------|------------|
| Auth Service | 1 replica | 2 replicas | 2 replicas |
| Student Service | 1 replica | 2 replicas | 3 replicas |
| Course Service | 1 replica | 2 replicas | 3 replicas |
| Enrollment Service | 1 replica | 2 replicas | 3 replicas |
| Grade Service | 1 replica | 2 replicas | 3 replicas |
| Attendance Service | 1 replica | 1 replica | 2 replicas |
| Fee Service | 1 replica | 1 replica | 2 replicas |
| Payment Service | 1 replica | 2 replicas | 2 replicas |
| Notification Service | 1 replica | 2 replicas | 2 replicas |
| Report Service | 1 replica | 1 replica | 2 replicas |

---

## Database Deployment

```mermaid
graph TB
    subgraph "RDS Deployment"
        subgraph "Primary Region"
            RDS_Primary[(Primary<br>db.r6g.xlarge<br>Multi-AZ)]
            ReadReplica1[(Read Replica 1<br>db.r6g.large)]
            ReadReplica2[(Read Replica 2<br>db.r6g.large)]
        end

        subgraph "DR Region"
            RDS_DR[(DR Replica<br>db.r6g.xlarge)]
        end
    end

    RDS_Primary -->|Sync Replication| ReadReplica1
    RDS_Primary -->|Sync Replication| ReadReplica2
    RDS_Primary -.->|Async Replication| RDS_DR

    subgraph "Application"
        WriteOps[Write Operations<br>Grade submit, Enrollment, Payment]
        ReadOps[Read Operations<br>Reports, Dashboards, Catalog]
    end

    WriteOps --> RDS_Primary
    ReadOps --> ReadReplica1
    ReadOps --> ReadReplica2
```

---

## CI/CD Pipeline

```mermaid
graph LR
    subgraph "Development"
        Dev[Developer]
        Git[GitHub Repository]
    end

    subgraph "CI/CD Pipeline"
        Actions[GitHub Actions]
        Build[Build & Test]
        Scan[Security Scan]
        Push[Push to ECR]
    end

    subgraph "Container Registry"
        ECR[Amazon ECR]
    end

    subgraph "Deployment"
        ArgoCD[ArgoCD]
        DevCluster[Dev Cluster]
        StagingCluster[Staging Cluster]
        ProdCluster[Production Cluster]
    end

    Dev --> Git
    Git --> Actions
    Actions --> Build
    Build --> Scan
    Scan --> Push
    Push --> ECR
    ECR --> ArgoCD
    ArgoCD --> DevCluster
    ArgoCD --> StagingCluster
    ArgoCD --> ProdCluster
```

---

## Resource Allocation

| Component | Instance Type | vCPU | Memory | Storage |
|-----------|---------------|------|--------|---------|
| EKS Worker (App) | m6i.large | 2 | 8 GB | 50 GB |
| EKS Worker (Workers) | m6i.medium | 1 | 4 GB | 30 GB |
| RDS Primary | db.r6g.xlarge | 4 | 32 GB | 500 GB |
| RDS Replica | db.r6g.large | 2 | 16 GB | 500 GB |
| ElastiCache | cache.r6g.large | 2 | 13 GB | - |
| S3 (Documents/Transcripts) | Standard | - | - | Unlimited |

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

