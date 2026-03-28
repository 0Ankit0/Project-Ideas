# Class Diagrams

## Overview
Detailed class diagrams for all major domain modules in the Student Information System.

---

## User and Authentication Classes

```mermaid
classDiagram
    class User {
        +UUID id
        +String email
        +String username
        +String hashedPassword
        +UserRole role
        +Boolean otpEnabled
        +Boolean otpVerified
        +DateTime createdAt
        +DateTime lastLoginAt
        +login()
        +logout()
        +resetPassword()
        +enableOTP()
        +verifyOTP()
    }

    class UserRole {
        <<enumeration>>
        STUDENT
        FACULTY
        ADMIN
        REGISTRAR
        ACADEMIC_ADVISOR
        PARENT
    }

    class AuthToken {
        +UUID id
        +UUID userId
        +String accessToken
        +String refreshToken
        +DateTime accessExpiresAt
        +DateTime refreshExpiresAt
        +refresh()
        +revoke()
    }

    User "1" --> "*" AuthToken
    User --> UserRole
```

---

## Student Management Classes

```mermaid
classDiagram
    class Student {
        +UUID id
        +UUID userId
        +String studentId
        +String firstName
        +String lastName
        +Date dateOfBirth
        +String gender
        +String phone
        +String address
        +UUID programId
        +UUID academicAdvisorId
        +StudentStatus status
        +DateTime enrolledAt
        +getProfile()
        +updateProfile()
        +getEnrollments()
        +viewGrades()
        +viewAttendance()
        +downloadTranscript()
        +viewDegreeAudit()
    }

    class Guardian {
        +UUID id
        +UUID userId
        +UUID studentId
        +String firstName
        +String lastName
        +String email
        +String phone
        +String relationship
        +Boolean isVerified
        +DateTime linkedAt
        +viewStudentProfile()
        +viewGrades()
        +viewAttendance()
        +viewFeeStatus()
    }

    class AcademicAdvisor {
        +UUID id
        +UUID userId
        +UUID facultyId
        +List~UUID~ assignedStudents
        +viewStudentProgress()
        +scheduleAdvisingSession()
        +approveEnrollmentOverride()
        +createImprovementPlan()
        +viewStudentDegreeAudit()
    }

    Student "1" --> "0..*" Guardian : monitored_by
    Student "*" --> "1" AcademicAdvisor : assigned_to
```

---

## Course and Curriculum Classes

```mermaid
classDiagram
    class Department {
        +UUID id
        +String name
        +String code
        +UUID headFacultyId
        +Boolean isActive
        +getCourses()
        +getFaculty()
        +getPrograms()
    }

    class Course {
        +UUID id
        +String code
        +String name
        +String description
        +Integer credits
        +CourseLevel level
        +UUID departmentId
        +String syllabusUrl
        +CourseStatus status
        +DateTime createdAt
        +addPrerequisite()
        +removePrerequisite()
        +getSections()
        +publish()
        +deactivate()
    }

    class Prerequisite {
        +UUID id
        +UUID courseId
        +UUID requiredCourseId
        +String minGrade
        +validate()
    }

    class CourseSection {
        +UUID id
        +UUID courseId
        +UUID facultyId
        +String sectionCode
        +Integer semester
        +Integer academicYear
        +Integer maxSeats
        +Integer enrolledCount
        +String schedule
        +String room
        +SectionStatus status
        +enroll()
        +drop()
        +getWaitlist()
        +isAvailable()
        +getRoster()
    }

    class DegreeProgram {
        +UUID id
        +String name
        +String code
        +UUID departmentId
        +Integer totalCredits
        +Integer durationYears
        +ProgramStatus status
        +addRequirement()
        +getRequirements()
        +checkGraduationEligibility()
    }

    class DegreeRequirement {
        +UUID id
        +UUID programId
        +UUID courseId
        +RequirementType type
        +Boolean isMandatory
        +Integer minCredits
    }

    Department "1" --> "*" Course
    Department "1" --> "*" DegreeProgram
    Course "1" --> "*" Prerequisite
    Course "1" --> "*" CourseSection
    DegreeProgram "1" --> "*" DegreeRequirement
```

---

## Enrollment Classes

```mermaid
classDiagram
    class Enrollment {
        +UUID id
        +UUID studentId
        +UUID courseSectionId
        +EnrollmentStatus status
        +Integer semester
        +Integer academicYear
        +DateTime enrolledAt
        +DateTime droppedAt
        +drop()
        +complete()
        +fail()
        +getGrade()
    }

    class Waitlist {
        +UUID id
        +UUID studentId
        +UUID courseSectionId
        +Integer position
        +DateTime joinedAt
        +promote()
        +remove()
    }

    class EnrollmentWindow {
        +UUID id
        +Integer semester
        +Integer academicYear
        +DateTime startDate
        +DateTime endDate
        +DateTime dropDeadline
        +Boolean isOpen
        +open()
        +close()
        +isWithinDropPeriod()
    }

    class EnrollmentService {
        +enrollStudent(studentId, sectionId)
        +dropCourse(enrollmentId)
        +joinWaitlist(studentId, sectionId)
        +processWaitlistPromotion(sectionId)
        +validatePrerequisites(studentId, courseId)
        +detectScheduleConflicts(studentId, sectionId)
    }

    Enrollment "*" --> "1" CourseSection
    Waitlist "*" --> "1" CourseSection
    EnrollmentService --> Enrollment
    EnrollmentService --> Waitlist
```

---

## Grade Management Classes

```mermaid
classDiagram
    class Grade {
        +UUID id
        +UUID enrollmentId
        +UUID studentId
        +UUID courseSectionId
        +UUID facultyId
        +String letterGrade
        +Decimal percentage
        +Decimal gradePoints
        +GradeStatus status
        +String remarks
        +DateTime submittedAt
        +DateTime publishedAt
        +submitDraft()
        +submitFinal()
        +publish()
        +requestAmendment()
    }

    class GradeAmendment {
        +UUID id
        +UUID gradeId
        +String previousGrade
        +String newGrade
        +String reason
        +AmendmentStatus status
        +UUID requestedByFacultyId
        +UUID approvedByRegistrarId
        +DateTime requestedAt
        +DateTime resolvedAt
        +approve()
        +reject()
    }

    class GPACalculator {
        +calculateSGPA(studentId, semester, year) Decimal
        +calculateCGPA(studentId) Decimal
        +calculateAcademicStanding(cgpa) AcademicStanding
        +updateStudentGPA(studentId)
    }

    class Transcript {
        +UUID id
        +UUID studentId
        +String purpose
        +String deliveryMethod
        +TranscriptStatus status
        +String pdfUrl
        +String digitalSignatureRef
        +DateTime requestedAt
        +DateTime issuedAt
        +generate()
        +applyDigitalSignature()
        +deliver()
    }

    class DegreeAuditEngine {
        +generateAudit(studentId) DegreeAudit
        +checkGraduationEligibility(studentId) Boolean
        +getCompletedCourses(studentId) List~Course~
        +getRemainingRequirements(studentId) List~DegreeRequirement~
        +estimateGraduationDate(studentId) Date
    }

    Grade "1" --> "*" GradeAmendment
    GPACalculator --> Grade
    DegreeAuditEngine --> Enrollment
```

---

## Attendance Classes

```mermaid
classDiagram
    class AttendanceSession {
        +UUID id
        +UUID courseSectionId
        +Date sessionDate
        +String topic
        +SessionType sessionType
        +Boolean isMarked
        +DateTime createdAt
        +markAttendance()
        +getAttendanceSummary()
        +generateQRCode()
    }

    class AttendanceRecord {
        +UUID id
        +UUID sessionId
        +UUID studentId
        +AttendanceStatus status
        +String remarks
        +DateTime markedAt
        +mark()
        +updateStatus()
    }

    class AttendanceService {
        +calculateAttendancePercentage(studentId, sectionId) Decimal
        +checkThresholdBreach(studentId, sectionId) AttendanceAlert
        +sendLowAttendanceAlert(studentId, sectionId)
        +processLeaveApplication(leaveId)
        +markExamEligibility(sectionId)
    }

    class LeaveApplication {
        +UUID id
        +UUID studentId
        +Date fromDate
        +Date toDate
        +String reason
        +String documentUrl
        +LeaveStatus status
        +UUID approvedByFacultyId
        +DateTime appliedAt
        +DateTime resolvedAt
        +submit()
        +approve()
        +reject()
    }

    AttendanceSession "1" --> "*" AttendanceRecord
    AttendanceService --> AttendanceRecord
    AttendanceService --> LeaveApplication
```

---

## Fee Management Classes

```mermaid
classDiagram
    class FeeStructure {
        +UUID id
        +UUID programId
        +Integer semester
        +Integer academicYear
        +List~FeeComponent~ components
        +Decimal totalAmount
        +Boolean isActive
        +generateInvoice(studentId)
        +applyDiscount(discountId)
    }

    class FeeComponent {
        +String name
        +String type
        +Decimal amount
        +Boolean isOptional
    }

    class FeeInvoice {
        +UUID id
        +UUID studentId
        +UUID feeStructureId
        +String invoiceNumber
        +Decimal totalAmount
        +Decimal discountAmount
        +Decimal aidAmount
        +Decimal netPayable
        +InvoiceStatus status
        +Date dueDate
        +DateTime generatedAt
        +applyDiscount()
        +applyAid()
        +markPaid()
        +generateReceipt()
    }

    class FeePayment {
        +UUID id
        +UUID invoiceId
        +UUID studentId
        +String gateway
        +PaymentStatus status
        +Decimal amount
        +String gatewayTransactionId
        +DateTime initiatedAt
        +DateTime completedAt
        +initiate()
        +verify()
        +getReceipt()
    }

    class AidApplication {
        +UUID id
        +UUID studentId
        +UUID aidProgramId
        +String documentUrl
        +AidStatus status
        +Decimal approvedAmount
        +String adminComments
        +DateTime appliedAt
        +DateTime decidedAt
        +submit()
        +approve()
        +reject()
        +disburse()
    }

    FeeStructure "1" --> "*" FeeComponent
    FeeStructure "1" --> "*" FeeInvoice
    FeeInvoice "1" --> "*" FeePayment
    AidApplication "*" --> "1" FeeInvoice
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

