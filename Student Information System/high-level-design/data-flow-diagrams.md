# Data Flow Diagrams

## Overview
Data flow diagrams showing how data moves through the Student Information System.

---

## Level 0: Context DFD (System Overview)

```mermaid
graph LR
    Student((Student))
    Faculty((Faculty))
    Admin((Admin))
    Registrar((Registrar))
    Parent((Parent))
    PayGW((Payment<br>Gateway))
    LDAP((LDAP / SSO))

    subgraph SIS ["Student Information System"]
        Process[SIS Processing]
    end

    Student -->|Registration, enrollment requests, fee payments| Process
    Process -->|Confirmation, grades, transcripts, receipts| Student

    Faculty -->|Grade entries, attendance data, announcements| Process
    Process -->|Course rosters, reports, approvals| Faculty

    Admin -->|User management, course config, fee structures| Process
    Process -->|Reports, dashboards, system status| Admin

    Registrar -->|Grade approvals, transcript issuance| Process
    Process -->|Student records, audit reports| Registrar

    Parent -->|View requests| Process
    Process -->|Grade/attendance/fee summaries| Parent

    Process -->|Payment initiation| PayGW
    PayGW -->|Payment confirmation/failure| Process

    Process -->|Authentication requests| LDAP
    LDAP -->|Auth tokens, user attributes| Process
```

---

## Level 1: DFD - Student Academic Workflow

```mermaid
graph LR
    Student((Student))

    subgraph "SIS Processes"
        P1[1.0 Enrollment Process]
        P2[2.0 Grade Management]
        P3[3.0 Attendance Tracking]
        P4[4.0 Fee Processing]
        P5[5.0 Transcript Generation]
    end

    subgraph "Data Stores"
        DS1[(Enrollment Records)]
        DS2[(Academic Records)]
        DS3[(Attendance Records)]
        DS4[(Fee Records)]
        DS5[(Document Store)]
    end

    Student -->|Enrollment request| P1
    P1 -->|Enrollment confirmation| Student
    P1 -->|Enrollment data| DS1
    DS1 -->|Student roster| P2

    P2 -->|Grade notification| Student
    P2 -->|Grade data| DS2
    DS2 -->|Grade history| P5

    P3 -->|Attendance alert| Student
    P3 -->|Attendance data| DS3

    Student -->|Fee payment| P4
    P4 -->|Receipt| Student
    P4 -->|Payment records| DS4

    Student -->|Transcript request| P5
    P5 -->|Official transcript| Student
    P5 -->|Transcript document| DS5
```

---

## Level 1: DFD - Faculty and Academic Operations

```mermaid
graph LR
    Faculty((Faculty))
    Registrar((Registrar))

    subgraph "Processes"
        P1[1.0 Course Management]
        P2[2.0 Grade Entry]
        P3[3.0 Attendance Marking]
        P4[4.0 Grade Review & Publication]
    end

    subgraph "Data Stores"
        DS1[(Course Catalog)]
        DS2[(Student Roster)]
        DS3[(Grade Records)]
        DS4[(Attendance Records)]
    end

    Faculty -->|Course material upload| P1
    P1 -->|Course details| Faculty
    P1 <-->|Course data| DS1
    DS1 -->|Enrolled students| DS2

    DS2 -->|Student list| P2
    Faculty -->|Grade submission| P2
    P2 -->|Draft/final grades| DS3
    DS3 -->|Grades for review| P4

    Faculty -->|Attendance marks| P3
    P3 -->|Attendance records| DS4
    DS4 -->|Attendance summary| Faculty

    Registrar -->|Approval action| P4
    P4 -->|Published grades| DS3
    P4 -->|Grade notification| Faculty
```

---

## Level 1: DFD - Fee and Financial Operations

```mermaid
graph LR
    Student((Student))
    Admin((Admin))
    Finance((Finance Office))
    PayGW((Payment Gateway))

    subgraph "Processes"
        P1[1.0 Fee Structure Management]
        P2[2.0 Invoice Generation]
        P3[3.0 Payment Processing]
        P4[4.0 Financial Aid Management]
    end

    subgraph "Data Stores"
        DS1[(Fee Structures)]
        DS2[(Invoices)]
        DS3[(Payment Records)]
        DS4[(Aid Applications)]
    end

    Admin -->|Fee configuration| P1
    P1 -->|Fee structure data| DS1

    DS1 -->|Fee rules| P2
    Student -->|Trigger invoice| P2
    P2 -->|Invoice details| Student
    P2 -->|Invoice records| DS2

    Student -->|Payment initiation| P3
    P3 -->|Payment request| PayGW
    PayGW -->|Payment confirmation| P3
    P3 -->|Receipt| Student
    P3 -->|Payment data| DS3

    Student -->|Aid application| P4
    Finance -->|Aid approval| P4
    P4 -->|Aid credit| DS2
    P4 -->|Aid decision| Student
    P4 -->|Aid data| DS4
```

---

## Level 2: DFD - Enrollment Validation Sub-Process

```mermaid
graph LR
    Student((Student))

    subgraph "Enrollment Validation"
        P1[1.1 Check Enrollment Window]
        P2[1.2 Validate Prerequisites]
        P3[1.3 Check Seat Availability]
        P4[1.4 Detect Schedule Conflicts]
        P5[1.5 Create Enrollment Record]
    end

    DS1[(Enrollment Windows)]
    DS2[(Prerequisite Rules)]
    DS3[(Course Sections)]
    DS4[(Student Timetable)]
    DS5[(Enrollment Records)]

    Student -->|Enrollment request| P1
    DS1 -->|Window dates| P1
    P1 -->|Window valid| P2

    DS2 -->|Prerequisite rules| P2
    P2 -->|Prerequisites met| P3

    DS3 -->|Seat data| P3
    P3 -->|Seat available| P4

    DS4 -->|Existing schedule| P4
    P4 -->|No conflict| P5

    P5 -->|Enrollment confirmation| Student
    P5 -->|Enrollment record| DS5
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

