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
