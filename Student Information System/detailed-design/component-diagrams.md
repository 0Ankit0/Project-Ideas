# Component Diagrams

## Overview
Component diagrams showing the software module structure and dependencies within the Student Information System.

---

## Overall System Component Diagram

```mermaid
graph TB
    subgraph "Client Applications"
        StudentApp[Student Web / Mobile App]
        FacultyPortal[Faculty Portal]
        AdminDashboard[Admin Dashboard]
        ParentPortal[Parent Portal]
    end

    subgraph "API Gateway Layer"
        Router[FastAPI Versioned Router<br>/api/v1]
        Auth[Auth Middleware<br>JWT Validation + RBAC]
    end

    subgraph "Domain Modules"
        IAMModule[IAM Module]
        StudentModule[Student Management Module]
        CourseModule[Course & Curriculum Module]
        EnrollmentModule[Enrollment Module]
        AcademicsModule[Academics & Grades Module]
        AttendanceModule[Attendance Module]
        FeeModule[Fee & Financial Aid Module]
        ExamModule[Exam Management Module]
        CommunicationModule[Communication Module]
        ReportModule[Reports & Analytics Module]
        NotifyModule[Notification Module]
    end

    subgraph "Infrastructure"
        DB[(PostgreSQL)]
        Redis[(Redis Cache)]
        Storage[(Object Storage)]
        WS[Websocket Manager]
    end

    subgraph "External Services"
        PayGW[Payment Gateways]
        LDAP[LDAP / SSO]
        Library[Library System]
        SMS[SMS / Email / Push]
    end

    StudentApp --> Router
    FacultyPortal --> Router
    AdminDashboard --> Router
    ParentPortal --> Router

    Router --> Auth
    Auth --> IAMModule
    Auth --> StudentModule
    Auth --> CourseModule
    Auth --> EnrollmentModule
    Auth --> AcademicsModule
    Auth --> AttendanceModule
    Auth --> FeeModule
    Auth --> ExamModule
    Auth --> CommunicationModule
    Auth --> ReportModule

    EnrollmentModule --> NotifyModule
    AcademicsModule --> NotifyModule
    AttendanceModule --> NotifyModule
    FeeModule --> NotifyModule
    ExamModule --> NotifyModule

    IAMModule --> DB
    StudentModule --> DB
    CourseModule --> DB
    EnrollmentModule --> DB
    AcademicsModule --> DB
    AttendanceModule --> DB
    FeeModule --> DB
    ExamModule --> DB
    CommunicationModule --> DB
    ReportModule --> DB
    NotifyModule --> DB

    IAMModule --> Redis
    EnrollmentModule --> Redis
    CourseModule --> Redis

    AcademicsModule --> Storage
    ReportModule --> Storage

    FeeModule --> PayGW
    IAMModule --> LDAP
    EnrollmentModule --> Library
    NotifyModule --> SMS
    NotifyModule --> WS
```

---

## Enrollment Module Component Diagram

```mermaid
graph TB
    Client[Authenticated Student]

    subgraph "Enrollment Module"
        EnrollRouter[Enrollment Router]
        EnrollService[Enrollment Service]
        WaitlistService[Waitlist Service]
        ConflictDetector[Schedule Conflict Detector]
        PrereqChecker[Prerequisite Checker]
        TimetableBuilder[Timetable Builder]
    end

    subgraph "Repositories"
        EnrollRepo[(Enrollment Repository)]
        WaitlistRepo[(Waitlist Repository)]
        SectionRepo[(Section Repository)]
        CourseRepo[(Course Repository)]
    end

    NotifyModule[Notification Module]
    DB[(PostgreSQL)]
    Redis[(Redis)]

    Client --> EnrollRouter
    EnrollRouter --> EnrollService
    EnrollService --> ConflictDetector
    EnrollService --> PrereqChecker
    EnrollService --> WaitlistService
    EnrollService --> TimetableBuilder

    PrereqChecker --> CourseRepo
    ConflictDetector --> SectionRepo
    EnrollService --> EnrollRepo
    WaitlistService --> WaitlistRepo

    EnrollRepo --> DB
    WaitlistRepo --> DB
    SectionRepo --> DB
    CourseRepo --> DB

    SectionRepo --> Redis
    EnrollService --> NotifyModule
    WaitlistService --> NotifyModule
```

---

## Academic Records Module Component Diagram

```mermaid
graph TB
    Faculty[Faculty]
    Registrar[Registrar]
    Student[Student]

    subgraph "Academics Module"
        GradeRouter[Grade Router]
        GradeService[Grade Service]
        GPACalculator[GPA Calculator]
        AcademicStandingChecker[Academic Standing Checker]
        TranscriptService[Transcript Service]
        DegreeAuditEngine[Degree Audit Engine]
    end

    subgraph "Repositories"
        GradeRepo[(Grade Repository)]
        GPARepo[(Student GPA Repository)]
        TranscriptRepo[(Transcript Repository)]
        EnrollRepo[(Enrollment Repository)]
    end

    PDFGen[PDF Generator]
    DigitalSigner[Digital Signer]
    StorageService[Object Storage]
    NotifyModule[Notification Module]
    DB[(PostgreSQL)]

    Faculty --> GradeRouter
    Registrar --> GradeRouter
    Student --> GradeRouter

    GradeRouter --> GradeService
    GradeRouter --> TranscriptService
    GradeRouter --> DegreeAuditEngine

    GradeService --> GPACalculator
    GPACalculator --> AcademicStandingChecker
    TranscriptService --> PDFGen
    PDFGen --> DigitalSigner
    DigitalSigner --> StorageService

    GradeService --> GradeRepo
    GPACalculator --> GPARepo
    TranscriptService --> TranscriptRepo
    DegreeAuditEngine --> EnrollRepo

    GradeRepo --> DB
    GPARepo --> DB
    TranscriptRepo --> DB
    EnrollRepo --> DB

    GradeService --> NotifyModule
    TranscriptService --> NotifyModule
```

---

## Fee and Financial Aid Module Component Diagram

```mermaid
graph TB
    Student[Student]
    Admin[Admin]

    subgraph "Fee Module"
        FeeRouter[Fee Router]
        FeeService[Fee Service]
        InvoiceEngine[Invoice Engine]
        PaymentService[Payment Service]
        AidService[Financial Aid Service]
        ReceiptGenerator[Receipt Generator]
    end

    subgraph "Repositories"
        InvoiceRepo[(Invoice Repository)]
        PaymentRepo[(Payment Repository)]
        AidRepo[(Aid Application Repository)]
        FeeStructRepo[(Fee Structure Repository)]
    end

    PayGW[Payment Gateway]
    StorageService[Object Storage]
    NotifyModule[Notification Module]
    ERPSystem[ERP / Finance System]
    DB[(PostgreSQL)]

    Student --> FeeRouter
    Admin --> FeeRouter

    FeeRouter --> FeeService
    FeeRouter --> AidService
    FeeService --> InvoiceEngine
    FeeService --> PaymentService
    PaymentService --> ReceiptGenerator

    InvoiceEngine --> FeeStructRepo
    InvoiceEngine --> InvoiceRepo
    PaymentService --> PayGW
    PaymentService --> PaymentRepo
    AidService --> AidRepo

    ReceiptGenerator --> StorageService
    FeeService --> ERPSystem

    InvoiceRepo --> DB
    PaymentRepo --> DB
    AidRepo --> DB
    FeeStructRepo --> DB

    PaymentService --> NotifyModule
    AidService --> NotifyModule
```

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

