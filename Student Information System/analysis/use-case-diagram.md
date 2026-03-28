# Use Case Diagram

## Overview
This document contains use case diagrams for all major actors in the Student Information System.

---

## Complete System Use Case Diagram

```mermaid
graph TB
    subgraph Actors
        Student((Student))
        Faculty((Faculty))
        Advisor((Academic Advisor))
        Admin((Admin Staff))
        Registrar((Registrar))
        Parent((Parent/Guardian))
        PaymentGW((Payment Gateway))
        SMSProvider((SMS Provider))
        EmailProvider((Email Provider))
    end

    subgraph "Student Information System"
        UC1[Browse Course Catalog]
        UC2[Enroll in Courses]
        UC3[View Grades]
        UC4[View Attendance]
        UC5[Pay Fees]
        UC6[Download Transcript]
        UC7[View Timetable]
        UC8[Manage Profile]

        UC10[Manage Course Content]
        UC11[Record Grades]
        UC12[Mark Attendance]
        UC13[View Student Reports]
        UC14[Send Announcements]

        UC20[View Student Progress]
        UC21[Approve Overrides]
        UC22[Create Improvement Plans]

        UC30[Manage Users]
        UC31[Manage Courses]
        UC32[Manage Fee Structures]
        UC33[View Analytics]
        UC34[Manage Calendar]

        UC40[Publish Grades]
        UC41[Issue Transcripts]
        UC42[Manage Graduation]
    end

    Student --> UC1
    Student --> UC2
    Student --> UC3
    Student --> UC4
    Student --> UC5
    Student --> UC6
    Student --> UC7
    Student --> UC8

    Faculty --> UC10
    Faculty --> UC11
    Faculty --> UC12
    Faculty --> UC13
    Faculty --> UC14

    Advisor --> UC20
    Advisor --> UC21
    Advisor --> UC22

    Admin --> UC30
    Admin --> UC31
    Admin --> UC32
    Admin --> UC33
    Admin --> UC34

    Registrar --> UC40
    Registrar --> UC41
    Registrar --> UC42

    Parent --> UC3
    Parent --> UC4
    Parent --> UC5

    UC5 --> PaymentGW
    UC5 --> SMSProvider
    UC6 --> EmailProvider
```

---

## Student Use Cases

```mermaid
graph LR
    Student((Student))

    subgraph "Account Management"
        UC1[Register Account]
        UC2[Login/Logout]
        UC3[Manage Profile]
        UC4[Reset Password]
        UC5[Link Parent Account]
    end

    subgraph "Course Enrollment"
        UC6[Browse Course Catalog]
        UC7[View Course Details]
        UC8[Enroll in Course]
        UC9[Drop Course]
        UC10[Join Waitlist]
        UC11[View My Enrollments]
    end

    subgraph "Academics"
        UC12[View Grades]
        UC13[View CGPA]
        UC14[View Degree Audit]
        UC15[Download Transcript]
        UC16[View Exam Schedule]
        UC17[View Hall Ticket]
    end

    subgraph "Attendance"
        UC18[View Attendance Records]
        UC19[Apply for Leave]
        UC20[Track Leave Status]
    end

    subgraph "Fee Management"
        UC21[View Fee Invoice]
        UC22[Pay Fees Online]
        UC23[View Payment History]
        UC24[Download Receipt]
        UC25[Apply for Financial Aid]
    end

    subgraph "Communication"
        UC26[View Announcements]
        UC27[Message Faculty]
        UC28[Manage Notification Preferences]
    end

    Student --> UC1
    Student --> UC2
    Student --> UC3
    Student --> UC4
    Student --> UC5
    Student --> UC6
    Student --> UC7
    Student --> UC8
    Student --> UC9
    Student --> UC10
    Student --> UC11
    Student --> UC12
    Student --> UC13
    Student --> UC14
    Student --> UC15
    Student --> UC16
    Student --> UC17
    Student --> UC18
    Student --> UC19
    Student --> UC20
    Student --> UC21
    Student --> UC22
    Student --> UC23
    Student --> UC24
    Student --> UC25
    Student --> UC26
    Student --> UC27
    Student --> UC28
```

---

## Faculty Use Cases

```mermaid
graph LR
    Faculty((Faculty))

    subgraph "Profile & Schedule"
        UC1[Manage Faculty Profile]
        UC2[View Teaching Schedule]
        UC3[View Course Roster]
        UC4[Set Office Hours]
    end

    subgraph "Course Management"
        UC5[View Assigned Courses]
        UC6[Upload Course Materials]
        UC7[Manage Course Content]
        UC8[View Syllabus]
    end

    subgraph "Grade Management"
        UC9[Enter Student Grades]
        UC10[Bulk Import Grades]
        UC11[Submit Final Grades]
        UC12[Request Grade Amendment]
        UC13[View Grade Distribution]
    end

    subgraph "Attendance Management"
        UC14[Mark Class Attendance]
        UC15[View Attendance Summary]
        UC16[Generate Attendance Report]
        UC17[Review Leave Requests]
    end

    subgraph "Communication"
        UC18[Post Announcement]
        UC19[Reply to Student Messages]
        UC20[Send Course Notifications]
    end

    subgraph "Reports"
        UC21[View Student Performance]
        UC22[View Course Analytics]
        UC23[Export Reports]
    end

    Faculty --> UC1
    Faculty --> UC2
    Faculty --> UC3
    Faculty --> UC4
    Faculty --> UC5
    Faculty --> UC6
    Faculty --> UC7
    Faculty --> UC8
    Faculty --> UC9
    Faculty --> UC10
    Faculty --> UC11
    Faculty --> UC12
    Faculty --> UC13
    Faculty --> UC14
    Faculty --> UC15
    Faculty --> UC16
    Faculty --> UC17
    Faculty --> UC18
    Faculty --> UC19
    Faculty --> UC20
    Faculty --> UC21
    Faculty --> UC22
    Faculty --> UC23
```

---

## Admin Use Cases

```mermaid
graph LR
    Admin((Admin Staff))

    subgraph "User Management"
        UC1[Manage Students]
        UC2[Manage Faculty]
        UC3[Manage Admin Roles]
        UC4[Handle Account Issues]
    end

    subgraph "Academic Administration"
        UC5[Manage Course Catalog]
        UC6[Manage Departments]
        UC7[Manage Degree Programs]
        UC8[Configure Enrollment Windows]
        UC9[Manage Classroom Allocation]
    end

    subgraph "Fee Administration"
        UC10[Define Fee Structures]
        UC11[Apply Scholarships]
        UC12[View Collection Reports]
        UC13[Process Financial Aid]
        UC14[Manage Refunds]
    end

    subgraph "Academic Calendar"
        UC15[Create Academic Calendar]
        UC16[Schedule Exams]
        UC17[Manage Events]
        UC18[Publish Holiday List]
    end

    subgraph "Reporting"
        UC19[View Institution Dashboard]
        UC20[Generate Custom Reports]
        UC21[Monitor System Usage]
        UC22[Export Data]
    end

    subgraph "System Settings"
        UC23[Manage System Configuration]
        UC24[View Audit Logs]
        UC25[Manage Integrations]
        UC26[Backup & Restore]
    end

    Admin --> UC1
    Admin --> UC2
    Admin --> UC3
    Admin --> UC4
    Admin --> UC5
    Admin --> UC6
    Admin --> UC7
    Admin --> UC8
    Admin --> UC9
    Admin --> UC10
    Admin --> UC11
    Admin --> UC12
    Admin --> UC13
    Admin --> UC14
    Admin --> UC15
    Admin --> UC16
    Admin --> UC17
    Admin --> UC18
    Admin --> UC19
    Admin --> UC20
    Admin --> UC21
    Admin --> UC22
    Admin --> UC23
    Admin --> UC24
    Admin --> UC25
    Admin --> UC26
```

---

## Registrar Use Cases

```mermaid
graph LR
    Registrar((Registrar))

    subgraph "Grade Management"
        UC1[Review Submitted Grades]
        UC2[Publish Final Grades]
        UC3[Approve Grade Amendments]
        UC4[Lock Grade Records]
    end

    subgraph "Transcript Management"
        UC5[Process Transcript Requests]
        UC6[Issue Official Transcripts]
        UC7[Digitally Sign Transcripts]
        UC8[Manage Transcript Delivery]
    end

    subgraph "Enrollment Oversight"
        UC9[View Enrollment Statistics]
        UC10[Override Enrollment Rules]
        UC11[Manage Enrollment Deadlines]
    end

    subgraph "Graduation"
        UC12[Process Graduation Applications]
        UC13[Verify Degree Completion]
        UC14[Manage Graduation Clearance]
        UC15[Generate Graduation List]
    end

    subgraph "Records"
        UC16[Manage Student Records]
        UC17[Archive Historical Records]
        UC18[Respond to Verification Requests]
    end

    Registrar --> UC1
    Registrar --> UC2
    Registrar --> UC3
    Registrar --> UC4
    Registrar --> UC5
    Registrar --> UC6
    Registrar --> UC7
    Registrar --> UC8
    Registrar --> UC9
    Registrar --> UC10
    Registrar --> UC11
    Registrar --> UC12
    Registrar --> UC13
    Registrar --> UC14
    Registrar --> UC15
    Registrar --> UC16
    Registrar --> UC17
    Registrar --> UC18
```

---

## Use Case Relationships

```mermaid
graph TB
    subgraph "Include Relationships"
        Enroll[Enroll in Course] -->|includes| CheckPrerequisites[Check Prerequisites]
        Enroll -->|includes| CheckSeatAvailability[Check Seat Availability]
        Enroll -->|includes| UpdateEnrollmentRecord[Update Enrollment Record]

        PayFees[Pay Fees] -->|includes| GenerateInvoice[Generate Invoice]
        PayFees -->|includes| ProcessPayment[Process via Gateway]

        IssueTranscript[Issue Transcript] -->|includes| VerifyGrades[Verify All Grades]
        IssueTranscript -->|includes| ApplyDigitalSignature[Apply Digital Signature]
    end

    subgraph "Extend Relationships"
        ViewGrades[View Grades] -.->|extends| DownloadGradeCard[Download Grade Card]
        ViewGrades -.->|extends| ViewGPABreakdown[View GPA Breakdown]

        MarkAttendance[Mark Attendance] -.->|extends| SendLowAttendanceAlert[Send Low Attendance Alert]
        MarkAttendance -.->|extends| BlockFromExam[Block from Exam]

        EnrollCourse[Enroll Course] -.->|extends| JoinWaitlist[Join Waitlist]
    end
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

