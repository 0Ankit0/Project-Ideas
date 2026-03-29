# Domain Model

## Overview
The Domain Model shows the key business entities and their relationships in the Student Information System.

---

## Complete Domain Model

```mermaid
erDiagram
    STUDENT ||--o{ ENROLLMENT : has
    STUDENT ||--o{ ATTENDANCE_RECORD : has
    STUDENT ||--o{ GRADE : receives
    STUDENT ||--o{ FEE_INVOICE : billed
    STUDENT ||--o{ PAYMENT : makes
    STUDENT ||--o{ TRANSCRIPT_REQUEST : submits
    STUDENT ||--o{ LEAVE_APPLICATION : applies
    STUDENT ||--o{ NOTIFICATION : receives
    STUDENT }o--|| DEGREE_PROGRAM : enrolled_in
    STUDENT }o--o| ACADEMIC_ADVISOR : assigned_to

    GUARDIAN ||--|| STUDENT : monitors

    FACULTY ||--o{ COURSE_SECTION : teaches
    FACULTY ||--o{ GRADE : enters
    FACULTY }o--|| DEPARTMENT : belongs_to

    COURSE ||--o{ COURSE_SECTION : has
    COURSE }o--|| DEPARTMENT : offered_by
    COURSE ||--o{ PREREQUISITE : requires
    COURSE }o--o| DEGREE_PROGRAM : part_of

    COURSE_SECTION ||--o{ ENROLLMENT : enrolls
    COURSE_SECTION ||--o{ ATTENDANCE_SESSION : has

    ATTENDANCE_SESSION ||--o{ ATTENDANCE_RECORD : generates
    ENROLLMENT ||--|| GRADE : yields

    DEGREE_PROGRAM ||--o{ DEGREE_REQUIREMENT : contains
    DEGREE_PROGRAM }o--|| DEPARTMENT : owned_by

    FEE_STRUCTURE ||--o{ FEE_INVOICE : generates
    FEE_INVOICE ||--o{ PAYMENT : paid_by
    FEE_INVOICE ||--o{ AID_APPLICATION : reduced_by

    EXAM ||--o{ EXAM_HALL_ALLOCATION : allocates
    EXAM }o--|| COURSE_SECTION : evaluates
    EXAM ||--o{ HALL_TICKET : issues

    ADMIN ||--o{ ADMIN_ROLE : has
    ADMIN_ROLE ||--o{ PERMISSION : grants
```

---

## Student Domain

```mermaid
classDiagram
    class Student {
        +UUID id
        +String studentId
        +String firstName
        +String lastName
        +String email
        +String phone
        +Date dateOfBirth
        +String gender
        +String address
        +StudentStatus status
        +DateTime enrolledAt
        +DateTime createdAt
        +updateProfile()
        +viewGrades()
        +viewAttendance()
        +downloadTranscript()
    }

    class Guardian {
        +UUID id
        +UUID studentId
        +String firstName
        +String lastName
        +String email
        +String phone
        +String relationship
        +Boolean isVerified
        +viewStudentGrades()
        +viewAttendance()
        +viewFeeStatus()
    }

    class AcademicAdvisor {
        +UUID id
        +UUID userId
        +String name
        +String department
        +List~UUID~ assignedStudentIds
        +viewStudentProgress()
        +approveEnrollmentOverride()
        +createImprovementPlan()
    }

    Student "1" --> "0..1" Guardian
    Student "*" --> "1" AcademicAdvisor
```

---

## Course Domain

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
    }

    class Course {
        +UUID id
        +String code
        +String name
        +String description
        +Integer credits
        +CourseLevel level
        +CourseStatus status
        +UUID departmentId
        +String syllabusUrl
        +addPrerequisite()
        +getSections()
        +getEnrolledStudents()
    }

    class Prerequisite {
        +UUID id
        +UUID courseId
        +UUID requiredCourseId
        +String minGrade
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
        +dropStudent()
        +getWaitlist()
    }

    class DegreeProgram {
        +UUID id
        +String name
        +String code
        +UUID departmentId
        +Integer totalCredits
        +Integer durationYears
        +ProgramStatus status
        +checkGraduationEligibility()
        +getDegreeRequirements()
    }

    class DegreeRequirement {
        +UUID id
        +UUID programId
        +UUID courseId
        +RequirementType type
        +Boolean isMandatory
    }

    Department "1" --> "*" Course
    Course "1" --> "*" Prerequisite
    Course "1" --> "*" CourseSection
    Department "1" --> "*" DegreeProgram
    DegreeProgram "1" --> "*" DegreeRequirement
```

---

## Enrollment Domain

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
        +getGrade()
    }

    class Waitlist {
        +UUID id
        +UUID studentId
        +UUID courseSectionId
        +Integer position
        +DateTime joinedAt
        +promoteToEnrollment()
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
    }

    Enrollment "*" --> "1" CourseSection
    Waitlist "*" --> "1" CourseSection
```

---

## Academics Domain

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
        +submit()
        +publish()
        +amend()
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
    }

    class StudentGPA {
        +UUID id
        +UUID studentId
        +Integer semester
        +Integer academicYear
        +Decimal sgpa
        +Decimal cgpa
        +AcademicStanding standing
        +recalculate()
    }

    class Transcript {
        +UUID id
        +UUID studentId
        +String purpose
        +TranscriptStatus status
        +String pdfUrl
        +String digitalSignatureRef
        +DateTime requestedAt
        +DateTime issuedAt
        +generate()
        +sign()
        +deliver()
    }

    class DegreeAudit {
        +UUID studentId
        +UUID programId
        +Integer creditsEarned
        +Integer creditsRequired
        +Integer creditsRemaining
        +List~UUID~ completedCourses
        +List~UUID~ remainingRequirements
        +Boolean isEligibleForGraduation
        +Date estimatedGraduationDate
        +generate()
    }

    Grade "1" --> "*" GradeAmendment
    Student "1" --> "*" StudentGPA
    Student "1" --> "*" Transcript
    Student "1" --> "1" DegreeAudit
```

---

## Attendance Domain

```mermaid
classDiagram
    class AttendanceSession {
        +UUID id
        +UUID courseSectionId
        +Date sessionDate
        +String topic
        +SessionType type
        +Boolean isMarked
        +DateTime createdAt
        +markAttendance()
        +getAttendanceSummary()
    }

    class AttendanceRecord {
        +UUID id
        +UUID sessionId
        +UUID studentId
        +AttendanceStatus status
        +String remarks
        +DateTime markedAt
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
        +approve()
        +reject()
    }

    AttendanceSession "1" --> "*" AttendanceRecord
    Student "1" --> "*" LeaveApplication
```

---

## Fee Domain

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
        +generateInvoice()
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
    }

    class Payment {
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
        +String supportingDocUrl
        +AidStatus status
        +Decimal approvedAmount
        +DateTime appliedAt
        +DateTime decidedAt
        +String adminComments
        +approve()
        +reject()
        +disburse()
    }

    FeeStructure "1" --> "*" FeeInvoice
    FeeInvoice "1" --> "*" Payment
    FeeInvoice "*" --> "*" AidApplication
```

---

## Enumeration Types

```mermaid
classDiagram
    class StudentStatus {
        <<enumeration>>
        APPLICANT
        ENROLLED
        ACTIVE
        SUSPENDED
        GRADUATED
        WITHDRAWN
    }

    class EnrollmentStatus {
        <<enumeration>>
        PENDING
        ENROLLED
        WAITLISTED
        DROPPED
        COMPLETED
        FAILED
    }

    class GradeStatus {
        <<enumeration>>
        DRAFT
        SUBMITTED
        PUBLISHED
        AMENDED
    }

    class AttendanceStatus {
        <<enumeration>>
        PRESENT
        ABSENT
        LATE
        EXCUSED
    }

    class InvoiceStatus {
        <<enumeration>>
        PENDING
        PARTIALLY_PAID
        PAID
        OVERDUE
        WAIVED
    }

    class AcademicStanding {
        <<enumeration>>
        GOOD_STANDING
        WARNING
        PROBATION
        SUSPENDED
        DISMISSED
    }
```

## Implementation-Ready Addendum for Domain Model

### Purpose in This Artifact
Adds aggregate invariants for enrollment attempts and grade versions.

### Scope Focus
- Domain invariants and aggregates
- Enrollment lifecycle enforcement relevant to this artifact
- Grading/transcript consistency constraints relevant to this artifact
- Role-based and integration concerns at this layer

#### Implementation Rules
- Enrollment lifecycle operations must emit auditable events with correlation IDs and actor scope.
- Grade and transcript actions must preserve immutability through versioned records; no destructive updates.
- RBAC must be combined with context constraints (term, department, assigned section, advisee).
- External integrations must remain contract-first with explicit versioning and backward-compatibility strategy.

#### Acceptance Criteria
1. Business rules are testable and mapped to policy IDs in this artifact.
2. Failure paths (authorization, policy window, downstream sync) are explicitly documented.
3. Data ownership and source-of-truth boundaries are clearly identified.
4. Diagram and narrative remain consistent for the scenarios covered in this file.

