# Activity Diagrams

## Overview
Activity diagrams showing the business process flows for key operations in the Student Information System.

---

## Course Enrollment Flow

```mermaid
flowchart TD
    Start([Student opens enrollment portal]) --> CheckWindow{Enrollment<br>Window Open?}
    CheckWindow -->|No| ShowDates[Display Registration Dates]
    ShowDates --> End1([Cannot Enroll])

    CheckWindow -->|Yes| BrowseCatalog[Browse Course Catalog]
    BrowseCatalog --> SearchFilter{Search or<br>Browse?}
    SearchFilter -->|Search| SearchResults[View Search Results]
    SearchFilter -->|Browse| DeptList[View Department Courses]
    SearchResults --> SelectCourse[Select Course]
    DeptList --> SelectCourse

    SelectCourse --> ViewDetails[View Course Details]
    ViewDetails --> CheckPrereq{Prerequisites<br>Met?}
    CheckPrereq -->|No| ShowPrereq[Show Missing Prerequisites]
    ShowPrereq --> BrowseCatalog
    CheckPrereq -->|Yes| CheckSeats{Seats<br>Available?}

    CheckSeats -->|No| OfferWaitlist{Join<br>Waitlist?}
    OfferWaitlist -->|No| BrowseCatalog
    OfferWaitlist -->|Yes| JoinWaitlist[Join Waitlist]
    JoinWaitlist --> WaitlistConfirm[Show Waitlist Position]
    WaitlistConfirm --> End2([Waitlisted])

    CheckSeats -->|Yes| CheckConflict{Schedule<br>Conflict?}
    CheckConflict -->|Yes| ShowConflict[Show Timetable Conflict]
    ShowConflict --> BrowseCatalog
    CheckConflict -->|No| ConfirmEnroll[Confirm Enrollment]

    ConfirmEnroll --> ProcessEnroll[Create Enrollment Record]
    ProcessEnroll --> DecrementSeat[Decrement Seat Count]
    DecrementSeat --> UpdateTimetable[Update Student Timetable]
    UpdateTimetable --> SendConfirmation[Send Confirmation Email]
    SendConfirmation --> ShowSuccess[Display Success Message]
    ShowSuccess --> End3([Enrolled Successfully])
```

---

## Grade Recording and Publication Flow

```mermaid
flowchart TD
    Start([Faculty opens grade entry]) --> SelectCourse[Select Course]
    SelectCourse --> OpenGradeWindow{Grade Entry<br>Window Open?}
    OpenGradeWindow -->|No| ShowClosed[Show Closed Message]
    ShowClosed --> End1([Cannot Enter Grades])

    OpenGradeWindow -->|Yes| ViewRoster[View Student Roster]
    ViewRoster --> EntryMethod{Entry<br>Method}
    EntryMethod -->|Manual| EnterManually[Enter Grades Individually]
    EntryMethod -->|CSV| UploadCSV[Upload Grade CSV]

    UploadCSV --> ValidateCSV{CSV Valid?}
    ValidateCSV -->|No| ShowErrors[Show Validation Errors]
    ShowErrors --> UploadCSV
    ValidateCSV -->|Yes| PreviewGrades[Preview Imported Grades]

    EnterManually --> ReviewGrades[Review All Grades]
    PreviewGrades --> ReviewGrades

    ReviewGrades --> AnyMissing{Any Missing<br>Grades?}
    AnyMissing -->|Yes| MarkIncomplete[Mark as Incomplete]
    MarkIncomplete --> ReviewGrades
    AnyMissing -->|No| SaveDraft{Save Draft<br>or Submit?}

    SaveDraft -->|Save Draft| DraftSaved[Draft Saved]
    DraftSaved --> End2([Continue Later])

    SaveDraft -->|Submit| SubmitGrades[Submit Final Grades]
    SubmitGrades --> NotifyRegistrar[Notify Registrar]
    NotifyRegistrar --> RegistrarReview[Registrar Reviews Grades]

    RegistrarReview --> GradesApproved{Approved?}
    GradesApproved -->|No| ReturnForCorrection[Return to Faculty]
    ReturnForCorrection --> ReviewGrades
    GradesApproved -->|Yes| PublishGrades[Publish Grades]

    PublishGrades --> CalculateGPA[Calculate GPA/CGPA]
    CalculateGPA --> UpdateStanding[Update Academic Standing]
    UpdateStanding --> NotifyStudents[Notify Students]
    NotifyStudents --> NotifyParents[Notify Parents]
    NotifyParents --> End3([Grades Published])
```

---

## Fee Payment Flow

```mermaid
flowchart TD
    Start([Student views fee invoice]) --> CheckDue{Fees Due?}
    CheckDue -->|No| ShowPaid[Show Paid Status]
    ShowPaid --> End1([No Action Required])

    CheckDue -->|Yes| SelectPayment[Select Payment Method]
    SelectPayment --> PaymentChoice{Payment<br>Method}

    PaymentChoice -->|Full Payment| FullAmount[Pay Full Amount]
    PaymentChoice -->|Installment| CheckInstallment{Installment<br>Plan Available?}

    CheckInstallment -->|No| FullAmount
    CheckInstallment -->|Yes| SelectInstallment[Choose Installment Plan]
    SelectInstallment --> InstallmentAmount[Set Installment Amount]

    FullAmount --> ChooseGateway[Choose Payment Gateway]
    InstallmentAmount --> ChooseGateway

    ChooseGateway --> RedirectGateway[Redirect to Gateway]
    RedirectGateway --> ProcessPayment{Payment<br>Success?}

    ProcessPayment -->|No| PaymentFailed[Show Failure Message]
    PaymentFailed --> RetryOption{Retry?}
    RetryOption -->|Yes| SelectPayment
    RetryOption -->|No| End2([Payment Abandoned])

    ProcessPayment -->|Yes| RecordPayment[Record Payment in System]
    RecordPayment --> UpdateInvoice[Update Invoice Status]
    UpdateInvoice --> GenerateReceipt[Generate Receipt]
    GenerateReceipt --> SendNotification[Send Email/SMS Receipt]
    SendNotification --> CheckScholarship{Scholarship<br>Applied?}

    CheckScholarship -->|Yes| ApplyAid[Apply Financial Aid Credit]
    ApplyAid --> End3([Payment Complete])
    CheckScholarship -->|No| End3
```

---

## Attendance Marking Flow

```mermaid
flowchart TD
    Start([Faculty opens class session]) --> SelectSession[Select Course and Date]
    SelectSession --> CheckSession{Session<br>Exists?}
    CheckSession -->|No| CreateSession[Create Session Record]
    CreateSession --> DisplayRoster
    CheckSession -->|Yes| DisplayRoster[Display Student Roster]

    DisplayRoster --> MarkingMethod{Attendance<br>Method}

    MarkingMethod -->|Manual| ManualMark[Mark Each Student Manually]
    MarkingMethod -->|QR Code| GenerateQR[Generate QR Code]
    MarkingMethod -->|Biometric| ReadBiometric[Read Biometric Data]

    GenerateQR --> Studentscan[Students Scan QR]
    Studentscan --> AutoMark[Auto-mark Present]
    AutoMark --> FacultyReview[Faculty Reviews Marks]

    ReadBiometric --> AutoProcess[Auto-process Biometric]
    AutoProcess --> FacultyReview

    ManualMark --> ReviewMarks[Review Attendance Marks]
    FacultyReview --> ReviewMarks

    ReviewMarks --> SaveAttendance{Save<br>Attendance}
    SaveAttendance -->|Cancel| End1([Attendance Not Saved])
    SaveAttendance -->|Confirm| RecordAttendance[Save Attendance Records]

    RecordAttendance --> CalculatePercent[Calculate Attendance %]
    CalculatePercent --> CheckThreshold{Below 75%<br>Threshold?}

    CheckThreshold -->|No| End2([Attendance Saved])
    CheckThreshold -->|Yes| SendStudentAlert[Alert Student]
    SendStudentAlert --> SendParentAlert[Alert Parent/Guardian]
    SendParentAlert --> AlertAdvisor[Notify Academic Advisor]
    AlertAdvisor --> End3([Attendance Saved + Alerts Sent])
```

---

## Student Registration Flow

```mermaid
flowchart TD
    Start([New Student Applies]) --> FillApplication[Fill Admission Application]
    FillApplication --> UploadDocuments[Upload Required Documents]
    UploadDocuments --> PayAdmissionFee[Pay Admission Fee]
    PayAdmissionFee --> SubmitApplication[Submit Application]

    SubmitApplication --> AdminReview[Admin Reviews Application]
    AdminReview --> DocumentsVerified{Documents<br>Valid?}
    DocumentsVerified -->|No| RequestDocs[Request Missing Documents]
    RequestDocs --> UploadDocuments
    DocumentsVerified -->|Yes| AdmissionDecision{Admission<br>Decision}

    AdmissionDecision -->|Rejected| NotifyRejection[Notify Rejection with Reason]
    NotifyRejection --> End1([Application Rejected])

    AdmissionDecision -->|Accepted| SendOffer[Send Admission Offer]
    SendOffer --> StudentAccepts{Student<br>Accepts Offer?}
    StudentAccepts -->|No| End2([Offer Declined])
    StudentAccepts -->|Yes| PayConfirmation[Pay Confirmation Fee]

    PayConfirmation --> CreateAccount[Create Student Account]
    CreateAccount --> AssignStudentID[Assign Student ID]
    AssignStudentID --> AssignProgram[Assign Degree Program]
    AssignProgram --> AssignAdvisor[Assign Academic Advisor]
    AssignAdvisor --> SendCredentials[Send Login Credentials]
    SendCredentials --> OpenEnrollment[Open Course Enrollment]
    OpenEnrollment --> End3([Registration Complete])
```

---

## Transcript Request Flow

```mermaid
flowchart TD
    Start([Student requests transcript]) --> CheckHolds{Account<br>Holds?}
    CheckHolds -->|Yes| ShowHolds[Show Active Holds]
    ShowHolds --> ResolveHolds[Resolve Holds]
    ResolveHolds --> CheckHolds

    CheckHolds -->|No| SelectPurpose[Select Transcript Purpose]
    SelectPurpose --> SelectDelivery[Select Delivery Method]
    SelectDelivery --> PayFee{Transcript<br>Fee Required?}
    PayFee -->|Yes| MakePayment[Make Payment]
    MakePayment --> SubmitRequest[Submit Request]
    PayFee -->|No| SubmitRequest

    SubmitRequest --> RegistrarQueue[Registrar Review Queue]
    RegistrarQueue --> VerifyRecords{Records<br>Complete?}

    VerifyRecords -->|No| NotifyStudent[Notify Student of Issue]
    NotifyStudent --> End1([Request On Hold])

    VerifyRecords -->|Yes| GeneratePDF[Generate Transcript PDF]
    GeneratePDF --> ApplySignature[Apply Digital Signature]
    ApplySignature --> DeliveryMethod{Delivery<br>Method}

    DeliveryMethod -->|Download| UploadSecure[Upload to Secure Portal]
    UploadSecure --> NotifyDownload[Notify Student to Download]

    DeliveryMethod -->|Email| SendEmail[Send via Secure Email]

    DeliveryMethod -->|Physical| QueuePrint[Queue for Printing]
    QueuePrint --> PostDelivery[Post/Courier Dispatch]

    NotifyDownload --> End2([Transcript Issued])
    SendEmail --> End2
    PostDelivery --> End2
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

