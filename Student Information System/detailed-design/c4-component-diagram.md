# C4 Component Diagram

## Overview
Detailed C4 Level 3 component diagrams for core subsystems of the Student Information System.

---

## C4 Component Diagram - Enrollment and Scheduling Core

```mermaid
graph TB
    StudentClient[Student Client]
    FacultyClient[Faculty Client]
    AdminClient[Admin Client]

    subgraph "Enrollment and Scheduling System"
        EnrollRouter[Enrollment API Router]
        CourseRouter[Course Catalog Router]
        AdminCourseRouter[Admin Course Management Router]

        EnrollmentService[Enrollment Service<br>Validates and processes enrollment]
        PrerequisiteValidator[Prerequisite Validator<br>Checks course completion chain]
        ConflictChecker[Schedule Conflict Checker<br>Detects timetable conflicts]
        WaitlistManager[Waitlist Manager<br>Manages position and auto-promotion]
        TimetableService[Timetable Service<br>Builds student schedule view]
        EnrollmentEventPublisher[Enrollment Event Publisher<br>Triggers notifications on enrollment changes]
    end

    DB[(PostgreSQL)]
    Cache[(Redis)]
    NotificationModule[Notification Module]
    WS[Websocket Manager]

    StudentClient --> EnrollRouter
    StudentClient --> CourseRouter
    AdminClient --> AdminCourseRouter

    EnrollRouter --> EnrollmentService
    EnrollmentService --> PrerequisiteValidator
    EnrollmentService --> ConflictChecker
    EnrollmentService --> WaitlistManager
    CourseRouter --> TimetableService

    EnrollmentService --> EnrollmentEventPublisher
    WaitlistManager --> EnrollmentEventPublisher
    EnrollmentEventPublisher --> NotificationModule
    NotificationModule --> WS

    EnrollmentService --> DB
    WaitlistManager --> DB
    PrerequisiteValidator --> DB
    TimetableService --> DB
    CourseRouter --> Cache
    EnrollRouter --> Cache
```

---

## C4 Component Diagram - Academics and Records

```mermaid
graph TB
    FacultyClient[Faculty Client]
    RegistrarClient[Registrar Client]
    StudentClient[Student Client]

    subgraph "Academics and Records System"
        GradeRouter[Grade API Router]
        TranscriptRouter[Transcript API Router]

        GradeEntryService[Grade Entry Service<br>Validates and saves grade submissions]
        GradePublicationService[Grade Publication Service<br>Manages registrar approval and publish]
        GPAService[GPA and CGPA Service<br>Recalculates academic metrics on grade publish]
        AcademicStandingService[Academic Standing Service<br>Classifies students by standing]
        DegreeAuditService[Degree Audit Service<br>Maps courses to degree requirements]
        TranscriptService[Transcript Service<br>Generates, signs, and delivers transcripts]
        GradeAmendmentService[Grade Amendment Service<br>Handles faculty amendment requests]
    end

    DB[(PostgreSQL)]
    Storage[(Object Storage)]
    NotificationModule[Notification Module]

    FacultyClient --> GradeRouter
    RegistrarClient --> GradeRouter
    StudentClient --> TranscriptRouter

    GradeRouter --> GradeEntryService
    GradeRouter --> GradePublicationService
    GradeRouter --> GradeAmendmentService
    TranscriptRouter --> TranscriptService
    TranscriptRouter --> DegreeAuditService

    GradePublicationService --> GPAService
    GPAService --> AcademicStandingService
    GradePublicationService --> NotificationModule
    TranscriptService --> NotificationModule

    GradeEntryService --> DB
    GradePublicationService --> DB
    GPAService --> DB
    AcademicStandingService --> DB
    DegreeAuditService --> DB
    GradeAmendmentService --> DB
    TranscriptService --> DB
    TranscriptService --> Storage
```

---

## C4 Component Diagram - Attendance System

```mermaid
graph TB
    FacultyClient[Faculty Client]
    StudentClient[Student Client]

    subgraph "Attendance System"
        AttendanceRouter[Attendance API Router]
        LeaveRouter[Leave Management Router]

        SessionService[Session Management Service<br>Creates and manages class sessions]
        AttendanceMarkingService[Attendance Marking Service<br>Records and processes attendance]
        AttendanceCalculator[Attendance Calculator<br>Computes percentage per student per course]
        ThresholdAlertService[Threshold Alert Service<br>Detects below-threshold students and triggers alerts]
        QRCodeService[QR Code Service<br>Generates short-lived QR for self-attendance]
        LeaveService[Leave Service<br>Manages leave applications and approval]
        ExamEligibilityChecker[Exam Eligibility Checker<br>Determines hall ticket eligibility]
    end

    DB[(PostgreSQL)]
    NotificationModule[Notification Module]

    FacultyClient --> AttendanceRouter
    FacultyClient --> LeaveRouter
    StudentClient --> AttendanceRouter
    StudentClient --> LeaveRouter

    AttendanceRouter --> SessionService
    AttendanceRouter --> AttendanceMarkingService
    AttendanceRouter --> QRCodeService
    LeaveRouter --> LeaveService

    AttendanceMarkingService --> AttendanceCalculator
    AttendanceCalculator --> ThresholdAlertService
    ThresholdAlertService --> NotificationModule
    AttendanceMarkingService --> ExamEligibilityChecker

    SessionService --> DB
    AttendanceMarkingService --> DB
    AttendanceCalculator --> DB
    LeaveService --> DB
    ExamEligibilityChecker --> DB
```

---

## C4 Component Diagram - Fee and Payment System

```mermaid
graph TB
    StudentClient[Student Client]
    AdminClient[Admin Client]

    subgraph "Fee and Payment System"
        FeeRouter[Fee API Router]
        PaymentRouter[Payment API Router]
        AidRouter[Financial Aid Router]

        FeeInvoiceService[Fee Invoice Service<br>Generates and manages invoices]
        PaymentInitiationService[Payment Initiation Service<br>Creates gateway sessions]
        PaymentVerificationService[Payment Verification Service<br>Verifies gateway callbacks and webhooks]
        ReceiptService[Receipt Service<br>Generates payment receipts]
        AidService[Financial Aid Service<br>Processes aid applications and disbursements]
        FeeReportService[Fee Report Service<br>Generates collection and dues reports]
    end

    DB[(PostgreSQL)]
    Storage[(Object Storage)]
    PayGW[Payment Gateways]
    NotificationModule[Notification Module]
    ERPSystem[ERP / Finance System]

    StudentClient --> FeeRouter
    StudentClient --> PaymentRouter
    AdminClient --> AidRouter
    AdminClient --> FeeRouter

    FeeRouter --> FeeInvoiceService
    FeeRouter --> FeeReportService
    PaymentRouter --> PaymentInitiationService
    PaymentRouter --> PaymentVerificationService
    AidRouter --> AidService

    PaymentInitiationService --> PayGW
    PaymentVerificationService --> PayGW
    PaymentVerificationService --> ReceiptService
    FeeInvoiceService --> AidService
    FeeInvoiceService --> ERPSystem

    ReceiptService --> Storage
    PaymentVerificationService --> NotificationModule
    AidService --> NotificationModule

    FeeInvoiceService --> DB
    PaymentInitiationService --> DB
    PaymentVerificationService --> DB
    AidService --> DB
    ReceiptService --> DB
```
