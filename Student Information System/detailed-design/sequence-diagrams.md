# Sequence Diagrams

## Overview
Detailed internal sequence diagrams showing object interactions within the Student Information System for key operations.

---

## Course Enrollment Internal Sequence

```mermaid
sequenceDiagram
    participant Client
    participant EnrollmentRouter
    participant EnrollmentService
    participant PrerequisiteChecker
    participant ConflictDetector
    participant SectionRepository
    participant EnrollmentRepository
    participant WaitlistRepository
    participant NotificationService

    Client->>EnrollmentRouter: POST /enrollments {sectionId}
    EnrollmentRouter->>EnrollmentService: enrollStudent(studentId, sectionId)

    EnrollmentService->>SectionRepository: getSectionById(sectionId)
    SectionRepository-->>EnrollmentService: CourseSection

    EnrollmentService->>PrerequisiteChecker: validatePrerequisites(studentId, courseId)
    PrerequisiteChecker->>EnrollmentRepository: getCompletedCourses(studentId)
    EnrollmentRepository-->>PrerequisiteChecker: completedCourses
    PrerequisiteChecker-->>EnrollmentService: prerequisiteResult

    alt Prerequisites Not Met
        EnrollmentService-->>EnrollmentRouter: PrerequisiteError
        EnrollmentRouter-->>Client: 422 Prerequisites Not Met
    end

    EnrollmentService->>ConflictDetector: detectScheduleConflicts(studentId, sectionId)
    ConflictDetector-->>EnrollmentService: conflictResult

    alt Schedule Conflict
        EnrollmentService-->>EnrollmentRouter: ConflictError
        EnrollmentRouter-->>Client: 409 Schedule Conflict
    end

    EnrollmentService->>SectionRepository: checkSeats(sectionId)
    SectionRepository-->>EnrollmentService: availableSeats

    alt No Seats Available
        EnrollmentService->>WaitlistRepository: addToWaitlist(studentId, sectionId)
        WaitlistRepository-->>EnrollmentService: waitlistEntry
        EnrollmentService->>NotificationService: notifyWaitlistJoined(studentId, position)
        EnrollmentService-->>EnrollmentRouter: WaitlistResult
        EnrollmentRouter-->>Client: 200 Added to Waitlist
    else Seats Available
        EnrollmentService->>EnrollmentRepository: createEnrollment(studentId, sectionId)
        EnrollmentRepository-->>EnrollmentService: enrollment
        EnrollmentService->>SectionRepository: decrementSeats(sectionId)
        EnrollmentService->>NotificationService: notifyEnrollmentConfirmed(studentId, sectionId)
        EnrollmentService-->>EnrollmentRouter: EnrollmentResult
        EnrollmentRouter-->>Client: 201 Enrolled Successfully
    end
```

---

## Grade Submission Internal Sequence

```mermaid
sequenceDiagram
    participant Faculty
    participant GradeRouter
    participant GradeService
    participant GradeRepository
    participant GPACalculator
    participant NotificationService
    participant WebsocketManager

    Faculty->>GradeRouter: POST /faculty/courses/{sectionId}/grades
    GradeRouter->>GradeService: submitGrades(facultyId, sectionId, gradeData)

    GradeService->>GradeRepository: validateGradeData(gradeData)
    GradeRepository-->>GradeService: validationResult

    alt Validation Errors
        GradeService-->>GradeRouter: ValidationError
        GradeRouter-->>Faculty: 422 Validation Failed
    end

    GradeService->>GradeRepository: saveGrades(sectionId, gradeData)
    GradeRepository-->>GradeService: savedGrades

    GradeService->>NotificationService: notifyRegistrarForReview(sectionId)
    NotificationService->>WebsocketManager: pushRegistrarAlert()

    GradeService-->>GradeRouter: SubmissionResult
    GradeRouter-->>Faculty: 200 Grades Submitted for Review

    Note over GradeService: Registrar reviews and approves
    GradeService->>GradeRepository: publishGrades(sectionId)
    GradeRepository-->>GradeService: publishedGrades

    GradeService->>GPACalculator: recalculateGPA(affectedStudents)
    GPACalculator->>GradeRepository: getGrades(studentId)
    GradeRepository-->>GPACalculator: grades
    GPACalculator->>GPACalculator: calculateSGPA()
    GPACalculator->>GPACalculator: calculateCGPA()
    GPACalculator->>GradeRepository: updateStudentGPA(studentId, gpa)

    GradeService->>NotificationService: notifyGradePublication(affectedStudents)
    NotificationService->>WebsocketManager: pushStudentNotifications()
    NotificationService-->>GradeService: notificationsSent
```

---

## Fee Payment Internal Sequence

```mermaid
sequenceDiagram
    participant Student
    participant FeeRouter
    participant FeeService
    participant InvoiceRepository
    participant PaymentGateway
    participant PaymentRepository
    participant NotificationService

    Student->>FeeRouter: POST /fees/payments/initiate {invoiceId, gateway}
    FeeRouter->>FeeService: initiatePayment(studentId, invoiceId, gateway)

    FeeService->>InvoiceRepository: getInvoice(invoiceId)
    InvoiceRepository-->>FeeService: invoice

    FeeService->>InvoiceRepository: validateOwnership(studentId, invoiceId)
    InvoiceRepository-->>FeeService: valid

    FeeService->>PaymentRepository: createPaymentRecord(invoiceId, gateway)
    PaymentRepository-->>FeeService: paymentRecord

    FeeService->>PaymentGateway: createSession(amount, gateway, metadata)
    PaymentGateway-->>FeeService: paymentURL

    FeeService-->>FeeRouter: PaymentSession {paymentURL}
    FeeRouter-->>Student: 200 Redirect to Gateway

    Note over Student: Student completes payment on gateway
    PaymentGateway->>FeeRouter: POST /fees/payments/webhooks/{gateway}
    FeeRouter->>FeeService: verifyPayment(gatewayData)
    FeeService->>PaymentGateway: verifyTransaction(transactionId)
    PaymentGateway-->>FeeService: transactionStatus

    alt Payment Successful
        FeeService->>PaymentRepository: updatePaymentStatus(paymentId, PAID)
        FeeService->>InvoiceRepository: updateInvoiceStatus(invoiceId, PAID)
        FeeService->>FeeService: generateReceipt(paymentId)
        FeeService->>NotificationService: sendReceiptNotification(studentId, receiptUrl)
    else Payment Failed
        FeeService->>PaymentRepository: updatePaymentStatus(paymentId, FAILED)
        FeeService->>NotificationService: sendFailureNotification(studentId)
    end
```

---

## Attendance Alert Internal Sequence

```mermaid
sequenceDiagram
    participant Faculty
    participant AttendanceRouter
    participant AttendanceService
    participant AttendanceRepository
    participant StudentRepository
    participant NotificationService

    Faculty->>AttendanceRouter: POST /faculty/sessions/{sessionId}/attendance
    AttendanceRouter->>AttendanceService: markAttendance(sessionId, attendanceData)

    AttendanceService->>AttendanceRepository: saveAttendanceRecords(sessionId, data)
    AttendanceRepository-->>AttendanceService: saved

    AttendanceService->>AttendanceRepository: calculateAttendancePercentage(studentIds, sectionId)
    AttendanceRepository-->>AttendanceService: attendanceStats

    loop For each student
        AttendanceService->>AttendanceService: checkThreshold(studentPercentage)

        alt Below Critical Threshold (< 75%)
            AttendanceService->>StudentRepository: getAdvisorId(studentId)
            AttendanceService->>StudentRepository: getGuardianId(studentId)
            AttendanceService->>NotificationService: sendCriticalAlert(studentId, advisorId, guardianId)
        else Below Warning Threshold (< 80%)
            AttendanceService->>NotificationService: sendWarningAlert(studentId, guardianId)
        end
    end

    AttendanceService-->>AttendanceRouter: AttendanceResult
    AttendanceRouter-->>Faculty: 200 Attendance Marked
```

---

## Transcript Generation Internal Sequence

```mermaid
sequenceDiagram
    participant Student
    participant TranscriptRouter
    participant TranscriptService
    participant HoldChecker
    participant GradeRepository
    participant PDFGenerator
    participant DigitalSigner
    participant StorageService
    participant NotificationService

    Student->>TranscriptRouter: POST /students/me/transcripts {purpose, deliveryMethod}
    TranscriptRouter->>TranscriptService: requestTranscript(studentId, purpose, deliveryMethod)

    TranscriptService->>HoldChecker: checkHolds(studentId)
    HoldChecker-->>TranscriptService: holds

    alt Active Holds
        TranscriptService-->>TranscriptRouter: HoldError
        TranscriptRouter-->>Student: 422 Account Has Active Holds
    end

    TranscriptService->>TranscriptService: createTranscriptRequest(studentId)
    TranscriptService-->>TranscriptRouter: RequestCreated
    TranscriptRouter-->>Student: 201 Request Submitted

    Note over TranscriptService: Registrar reviews and approves request
    TranscriptService->>GradeRepository: getAllPublishedGrades(studentId)
    GradeRepository-->>TranscriptService: grades

    TranscriptService->>PDFGenerator: generateTranscriptPDF(studentId, grades)
    PDFGenerator-->>TranscriptService: pdfContent

    TranscriptService->>DigitalSigner: signDocument(pdfContent, registrarKeyRef)
    DigitalSigner-->>TranscriptService: signedPDF

    TranscriptService->>StorageService: uploadTranscript(signedPDF)
    StorageService-->>TranscriptService: transcriptUrl

    TranscriptService->>TranscriptService: updateTranscriptRecord(url, issuedAt)
    TranscriptService->>NotificationService: notifyTranscriptReady(studentId, transcriptUrl)
    NotificationService-->>Student: Email/SMS notification sent
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

