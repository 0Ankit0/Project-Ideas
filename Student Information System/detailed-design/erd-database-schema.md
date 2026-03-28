# ERD / Database Schema

## Overview
This ERD reflects the database design for the Student Information System, covering student records, courses, enrollment, grades, attendance, fees, exams, and communication.

---

## Full Database ERD

```mermaid
erDiagram
    users {
        int id PK
        varchar email
        varchar username
        varchar hashed_password
        varchar role
        boolean otp_enabled
        boolean otp_verified
        datetime created_at
        datetime updated_at
    }

    students {
        int id PK
        int user_id FK
        varchar student_id
        varchar first_name
        varchar last_name
        date date_of_birth
        varchar gender
        varchar phone
        text address
        int program_id FK
        int academic_advisor_id FK
        varchar status
        datetime enrolled_at
    }

    guardians {
        int id PK
        int student_id FK
        varchar first_name
        varchar last_name
        varchar email
        varchar phone
        varchar relationship
        boolean is_verified
        datetime linked_at
    }

    faculty {
        int id PK
        int user_id FK
        varchar first_name
        varchar last_name
        varchar employee_id
        int department_id FK
        varchar designation
        varchar qualification
        varchar specialization
        varchar office_hours
        datetime joined_at
    }

    departments {
        int id PK
        varchar name
        varchar code
        int head_faculty_id FK
        boolean is_active
    }

    degree_programs {
        int id PK
        varchar name
        varchar code
        int department_id FK
        int total_credits
        int duration_years
        varchar status
    }

    degree_requirements {
        int id PK
        int program_id FK
        int course_id FK
        varchar requirement_type
        boolean is_mandatory
        int min_credits
    }

    courses {
        int id PK
        varchar code
        varchar name
        text description
        int credits
        varchar level
        int department_id FK
        varchar syllabus_url
        varchar status
        datetime created_at
    }

    course_prerequisites {
        int id PK
        int course_id FK
        int required_course_id FK
        varchar min_grade
    }

    course_sections {
        int id PK
        int course_id FK
        int faculty_id FK
        varchar section_code
        int semester
        int academic_year
        int max_seats
        int enrolled_count
        varchar schedule
        varchar room
        varchar status
    }

    enrollment_windows {
        int id PK
        int semester
        int academic_year
        datetime start_date
        datetime end_date
        datetime drop_deadline
        boolean is_open
    }

    enrollments {
        int id PK
        int student_id FK
        int course_section_id FK
        varchar status
        int semester
        int academic_year
        datetime enrolled_at
        datetime dropped_at
    }

    waitlists {
        int id PK
        int student_id FK
        int course_section_id FK
        int position
        datetime joined_at
    }

    grades {
        int id PK
        int enrollment_id FK
        int student_id FK
        int course_section_id FK
        int faculty_id FK
        varchar letter_grade
        decimal percentage
        decimal grade_points
        varchar status
        text remarks
        datetime submitted_at
        datetime published_at
    }

    grade_amendments {
        int id PK
        int grade_id FK
        varchar previous_grade
        varchar new_grade
        text reason
        varchar status
        int requested_by_faculty_id FK
        int approved_by_registrar_id FK
        datetime requested_at
        datetime resolved_at
    }

    student_gpas {
        int id PK
        int student_id FK
        int semester
        int academic_year
        decimal sgpa
        decimal cgpa
        varchar academic_standing
        datetime calculated_at
    }

    attendance_sessions {
        int id PK
        int course_section_id FK
        date session_date
        varchar topic
        varchar session_type
        boolean is_marked
        datetime created_at
    }

    attendance_records {
        int id PK
        int session_id FK
        int student_id FK
        varchar status
        text remarks
        datetime marked_at
    }

    leave_applications {
        int id PK
        int student_id FK
        date from_date
        date to_date
        text reason
        varchar document_url
        varchar status
        int approved_by_faculty_id FK
        datetime applied_at
        datetime resolved_at
    }

    fee_structures {
        int id PK
        int program_id FK
        int semester
        int academic_year
        decimal total_amount
        json components_json
        boolean is_active
    }

    fee_invoices {
        int id PK
        int student_id FK
        int fee_structure_id FK
        varchar invoice_number
        decimal total_amount
        decimal discount_amount
        decimal aid_amount
        decimal net_payable
        varchar status
        date due_date
        datetime generated_at
    }

    payments {
        int id PK
        int invoice_id FK
        int student_id FK
        varchar gateway
        varchar status
        decimal amount
        varchar gateway_transaction_id
        datetime initiated_at
        datetime completed_at
    }

    aid_programs {
        int id PK
        varchar name
        varchar type
        text criteria
        decimal max_amount
        boolean is_active
    }

    aid_applications {
        int id PK
        int student_id FK
        int aid_program_id FK
        varchar document_url
        varchar status
        decimal approved_amount
        text admin_comments
        datetime applied_at
        datetime decided_at
    }

    transcripts {
        int id PK
        int student_id FK
        varchar purpose
        varchar delivery_method
        varchar status
        varchar pdf_url
        varchar digital_signature_ref
        datetime requested_at
        datetime issued_at
    }

    exams {
        int id PK
        int course_section_id FK
        varchar exam_type
        date exam_date
        varchar start_time
        varchar end_time
        varchar room
        varchar status
        datetime created_at
    }

    exam_hall_allocations {
        int id PK
        int exam_id FK
        int student_id FK
        varchar hall
        varchar seat_number
        datetime allocated_at
    }

    hall_tickets {
        int id PK
        int student_id FK
        int exam_id FK
        varchar ticket_url
        boolean is_eligible
        datetime generated_at
    }

    announcements {
        int id PK
        int created_by_user_id FK
        varchar title
        text body
        varchar target_group
        varchar category
        boolean is_published
        datetime published_at
    }

    messages {
        int id PK
        int sender_id FK
        int recipient_id FK
        text body
        boolean is_read
        datetime sent_at
    }

    notifications {
        int id PK
        int user_id FK
        varchar event_type
        varchar title
        text body
        boolean is_read
        json payload_json
        datetime created_at
    }

    users ||--o{ students : has
    users ||--o{ faculty : is
    students ||--o{ guardians : monitored_by
    students }o--|| degree_programs : enrolled_in
    students }o--o| faculty : advised_by

    departments ||--o{ courses : offers
    departments ||--o{ degree_programs : owns
    departments ||--o{ faculty : employs

    courses ||--o{ course_prerequisites : requires
    courses ||--o{ course_sections : has
    degree_programs ||--o{ degree_requirements : specifies

    course_sections ||--o{ enrollments : contains
    course_sections ||--o{ waitlists : has
    course_sections ||--o{ attendance_sessions : generates
    course_sections ||--o{ exams : has

    enrollments ||--o{ grades : produces
    grades ||--o{ grade_amendments : amended_by

    students ||--o{ student_gpas : tracks
    students ||--o{ transcripts : requests
    students ||--o{ leave_applications : submits
    students ||--o{ attendance_records : has
    students ||--o{ fee_invoices : billed
    students ||--o{ aid_applications : applies

    attendance_sessions ||--o{ attendance_records : records

    fee_structures ||--o{ fee_invoices : generates
    fee_invoices ||--o{ payments : paid_by
    aid_programs ||--o{ aid_applications : receives

    exams ||--o{ exam_hall_allocations : allocates
    exams ||--o{ hall_tickets : issues
```

---

## Key Design Notes

| Area | Design Decision |
|------|----------------|
| User identity | Single `users` table with role-based separation into `students` and `faculty` |
| Enrollment | Tracks semester and year for historical records |
| Grades | Separate `grade_amendments` table with registrar approval workflow |
| GPA | Pre-calculated and stored in `student_gpas` for performance; recalculated on grade publish |
| Attendance | Session-level granularity supports per-session tracking and leave matching |
| Fees | JSON `components_json` in fee structure supports flexible fee component definitions |
| Transcripts | PDF stored in object storage; reference URL and signature stored in DB |
| Notifications | Persisted in `notifications` table for inbox and websocket fanout |

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

