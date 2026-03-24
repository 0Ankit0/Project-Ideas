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
