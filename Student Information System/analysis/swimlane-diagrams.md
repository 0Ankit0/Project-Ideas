# Swimlane Diagrams

## Overview
Swimlane (BPMN-style) diagrams showing cross-department workflows in the Student Information System.

---

## Course Enrollment Process

```mermaid
sequenceDiagram
    participant STU as Student
    participant SIS as SIS Platform
    participant ADV as Academic Advisor
    participant REG as Registrar

    STU->>SIS: Browse course catalog
    SIS-->>STU: Display available courses

    STU->>SIS: Select course and request enrollment
    SIS->>SIS: Validate prerequisites
    SIS->>SIS: Check seat availability

    alt Prerequisites Not Met
        SIS-->>STU: Show missing prerequisites
    else Seats Full
        SIS-->>STU: Offer waitlist
        STU->>SIS: Join waitlist
        SIS-->>STU: Confirm waitlist position
    else Normal Enrollment
        SIS->>SIS: Create enrollment record
        SIS-->>STU: Send enrollment confirmation
        SIS-->>ADV: Notify advisor of enrollment update
    end

    Note over REG: Registrar monitors enrollment stats during window
    REG->>SIS: Review enrollment summary
    SIS-->>REG: Display enrollment statistics
```

---

## Grade Submission and Publication Workflow

```mermaid
sequenceDiagram
    participant FAC as Faculty
    participant SIS as SIS Platform
    participant REG as Registrar
    participant STU as Student
    participant PAR as Parent

    FAC->>SIS: Open grade entry for course
    SIS-->>FAC: Display student roster

    FAC->>SIS: Enter/upload grades
    SIS->>SIS: Validate grade format
    FAC->>SIS: Submit final grades

    SIS-->>REG: Notify grades submitted for review
    REG->>SIS: Review grade sheet

    alt Grades Rejected
        REG->>SIS: Return grades with comments
        SIS-->>FAC: Notify faculty of rejection
        FAC->>SIS: Revise and resubmit grades
    else Grades Approved
        REG->>SIS: Approve grade publication
        SIS->>SIS: Calculate GPA and CGPA
        SIS->>SIS: Update academic standing
        SIS-->>STU: Notify grade publication
        SIS-->>PAR: Notify parent/guardian
    end
```

---

## Attendance Alert and Intervention Workflow

```mermaid
sequenceDiagram
    participant FAC as Faculty
    participant SIS as SIS Platform
    participant STU as Student
    participant PAR as Parent
    participant ADV as Academic Advisor

    FAC->>SIS: Mark class attendance
    SIS->>SIS: Calculate attendance percentage

    alt Below Warning Threshold (below 80%)
        SIS-->>STU: Send attendance warning notification
        SIS-->>PAR: Send alert to parent/guardian
    end

    alt Below Critical Threshold (below 75%)
        SIS-->>STU: Send critical attendance warning
        SIS-->>ADV: Alert academic advisor
        SIS-->>PAR: Alert parent/guardian
        ADV->>SIS: Schedule intervention meeting with student
        ADV->>SIS: Log intervention notes
    end

    alt Exam Block Threshold (below 65%)
        SIS->>SIS: Flag student for exam block
        SIS-->>STU: Notify exam debarment warning
        STU->>SIS: Submit attendance condonation request
        ADV->>SIS: Review and approve/reject condonation
    end
```

---

## Financial Aid Application Workflow

```mermaid
sequenceDiagram
    participant STU as Student
    participant SIS as SIS Platform
    participant ADM as Admin Staff
    participant FIN as Finance Office

    STU->>SIS: Open financial aid application
    SIS-->>STU: Display aid programs and criteria

    STU->>SIS: Fill application form and upload documents
    STU->>SIS: Submit application

    SIS-->>ADM: Notify new aid application
    ADM->>SIS: Review application and documents

    alt Documents Incomplete
        ADM->>SIS: Request additional documents
        SIS-->>STU: Notify document request
        STU->>SIS: Upload requested documents
        ADM->>SIS: Re-review application
    end

    ADM->>SIS: Approve or reject application
    SIS-->>STU: Notify aid decision

    alt Aid Approved
        SIS-->>FIN: Notify finance office of aid approval
        FIN->>SIS: Process aid disbursement
        SIS->>SIS: Apply aid credit to student fee account
        SIS-->>STU: Notify aid applied to account
    end
```

---

## Student Admission and Onboarding Workflow

```mermaid
sequenceDiagram
    participant STU as Applicant/Student
    participant SIS as SIS Platform
    participant ADM as Admin Staff
    participant REG as Registrar
    participant ADV as Academic Advisor

    STU->>SIS: Submit admission application
    SIS-->>ADM: Notify new application

    ADM->>SIS: Review application and documents
    ADM->>SIS: Make admission decision

    alt Rejected
        SIS-->>STU: Send rejection notification
    else Accepted
        SIS-->>STU: Send admission offer
        STU->>SIS: Accept offer and pay confirmation fee

        SIS->>SIS: Create student account and assign ID
        SIS-->>REG: Notify new student registration
        REG->>SIS: Assign degree program and semester

        SIS->>SIS: Assign academic advisor
        SIS-->>ADV: Notify new student assignment
        SIS-->>STU: Send login credentials and orientation details

        ADV->>SIS: Schedule initial advising session
        SIS-->>STU: Notify enrollment window opening
    end
```

---

## Transcript Request and Issuance Workflow

```mermaid
sequenceDiagram
    participant STU as Student
    participant SIS as SIS Platform
    participant REG as Registrar

    STU->>SIS: Submit transcript request
    SIS->>SIS: Check for account holds

    alt Active Holds
        SIS-->>STU: Notify of holds blocking request
    else No Holds
        SIS-->>REG: Place transcript request in queue
        REG->>SIS: Review student academic record

        alt Records Incomplete
            REG->>SIS: Flag issue
            SIS-->>STU: Notify of record issue
        else Records Complete
            REG->>SIS: Approve transcript generation
            SIS->>SIS: Generate official transcript PDF
            SIS->>SIS: Apply digital signature

            alt Download
                SIS-->>STU: Notify transcript ready for download
            else Email Delivery
                SIS-->>STU: Send transcript via secure email
            end
        end
    end
```

---

## Exam Scheduling and Hall Allocation Workflow

```mermaid
sequenceDiagram
    participant ADM as Admin Staff
    participant SIS as SIS Platform
    participant FAC as Faculty
    participant STU as Student
    participant REG as Registrar

    ADM->>SIS: Create exam schedule for semester
    SIS->>SIS: Check for student exam conflicts
    SIS->>SIS: Allocate exam halls and seating

    alt Conflicts Found
        SIS-->>ADM: Show conflict report
        ADM->>SIS: Resolve conflicts and reschedule
    else No Conflicts
        ADM->>SIS: Publish exam schedule
        SIS-->>STU: Send exam schedule notification
        SIS-->>FAC: Notify faculty of invigilation duties
    end

    Note over STU: Student downloads hall ticket
    STU->>SIS: Request hall ticket
    SIS->>SIS: Check attendance eligibility
    alt Attendance Below Threshold
        SIS-->>STU: Block hall ticket; notify of debarment
    else Eligible
        SIS-->>STU: Generate and deliver hall ticket
    end

    REG->>SIS: Finalize exam register
    SIS-->>REG: Confirm all hall tickets issued
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

