# Component Diagrams

## Overview
Component diagrams showing the software module structure and dependencies within the Student Information System.

---

## Overall System Component Diagram

```mermaid
graph TB
    subgraph "Client Applications"
        StudentApp[Student Web / Mobile App]
        FacultyPortal[Faculty Portal]
        AdminDashboard[Admin Dashboard]
        ParentPortal[Parent Portal]
    end

    subgraph "API Gateway Layer"
        Router[FastAPI Versioned Router<br>/api/v1]
        Auth[Auth Middleware<br>JWT Validation + RBAC]
    end

    subgraph "Domain Modules"
        IAMModule[IAM Module]
        StudentModule[Student Management Module]
        CourseModule[Course & Curriculum Module]
        EnrollmentModule[Enrollment Module]
        AcademicsModule[Academics & Grades Module]
        AttendanceModule[Attendance Module]
        FeeModule[Fee & Financial Aid Module]
        ExamModule[Exam Management Module]
        CommunicationModule[Communication Module]
        ReportModule[Reports & Analytics Module]
        NotifyModule[Notification Module]
    end

    subgraph "Infrastructure"
        DB[(PostgreSQL)]
        Redis[(Redis Cache)]
        Storage[(Object Storage)]
        WS[Websocket Manager]
    end

    subgraph "External Services"
        PayGW[Payment Gateways]
        LDAP[LDAP / SSO]
        Library[Library System]
        SMS[SMS / Email / Push]
    end

    StudentApp --> Router
    FacultyPortal --> Router
    AdminDashboard --> Router
    ParentPortal --> Router

    Router --> Auth
    Auth --> IAMModule
    Auth --> StudentModule
    Auth --> CourseModule
    Auth --> EnrollmentModule
    Auth --> AcademicsModule
    Auth --> AttendanceModule
    Auth --> FeeModule
    Auth --> ExamModule
    Auth --> CommunicationModule
    Auth --> ReportModule

    EnrollmentModule --> NotifyModule
    AcademicsModule --> NotifyModule
    AttendanceModule --> NotifyModule
    FeeModule --> NotifyModule
    ExamModule --> NotifyModule

    IAMModule --> DB
    StudentModule --> DB
    CourseModule --> DB
    EnrollmentModule --> DB
    AcademicsModule --> DB
    AttendanceModule --> DB
    FeeModule --> DB
    ExamModule --> DB
    CommunicationModule --> DB
    ReportModule --> DB
    NotifyModule --> DB

    IAMModule --> Redis
    EnrollmentModule --> Redis
    CourseModule --> Redis

    AcademicsModule --> Storage
    ReportModule --> Storage

    FeeModule --> PayGW
    IAMModule --> LDAP
    EnrollmentModule --> Library
    NotifyModule --> SMS
    NotifyModule --> WS
```

---

## Enrollment Module Component Diagram

```mermaid
graph TB
    Client[Authenticated Student]

    subgraph "Enrollment Module"
        EnrollRouter[Enrollment Router]
        EnrollService[Enrollment Service]
        WaitlistService[Waitlist Service]
        ConflictDetector[Schedule Conflict Detector]
        PrereqChecker[Prerequisite Checker]
        TimetableBuilder[Timetable Builder]
    end

    subgraph "Repositories"
        EnrollRepo[(Enrollment Repository)]
        WaitlistRepo[(Waitlist Repository)]
        SectionRepo[(Section Repository)]
        CourseRepo[(Course Repository)]
    end

    NotifyModule[Notification Module]
    DB[(PostgreSQL)]
    Redis[(Redis)]

    Client --> EnrollRouter
    EnrollRouter --> EnrollService
    EnrollService --> ConflictDetector
    EnrollService --> PrereqChecker
    EnrollService --> WaitlistService
    EnrollService --> TimetableBuilder

    PrereqChecker --> CourseRepo
    ConflictDetector --> SectionRepo
    EnrollService --> EnrollRepo
    WaitlistService --> WaitlistRepo

    EnrollRepo --> DB
    WaitlistRepo --> DB
    SectionRepo --> DB
    CourseRepo --> DB

    SectionRepo --> Redis
    EnrollService --> NotifyModule
    WaitlistService --> NotifyModule
```

---

## Academic Records Module Component Diagram

```mermaid
graph TB
    Faculty[Faculty]
    Registrar[Registrar]
    Student[Student]

    subgraph "Academics Module"
        GradeRouter[Grade Router]
        GradeService[Grade Service]
        GPACalculator[GPA Calculator]
        AcademicStandingChecker[Academic Standing Checker]
        TranscriptService[Transcript Service]
        DegreeAuditEngine[Degree Audit Engine]
    end

    subgraph "Repositories"
        GradeRepo[(Grade Repository)]
        GPARepo[(Student GPA Repository)]
        TranscriptRepo[(Transcript Repository)]
        EnrollRepo[(Enrollment Repository)]
    end

    PDFGen[PDF Generator]
    DigitalSigner[Digital Signer]
    StorageService[Object Storage]
    NotifyModule[Notification Module]
    DB[(PostgreSQL)]

    Faculty --> GradeRouter
    Registrar --> GradeRouter
    Student --> GradeRouter

    GradeRouter --> GradeService
    GradeRouter --> TranscriptService
    GradeRouter --> DegreeAuditEngine

    GradeService --> GPACalculator
    GPACalculator --> AcademicStandingChecker
    TranscriptService --> PDFGen
    PDFGen --> DigitalSigner
    DigitalSigner --> StorageService

    GradeService --> GradeRepo
    GPACalculator --> GPARepo
    TranscriptService --> TranscriptRepo
    DegreeAuditEngine --> EnrollRepo

    GradeRepo --> DB
    GPARepo --> DB
    TranscriptRepo --> DB
    EnrollRepo --> DB

    GradeService --> NotifyModule
    TranscriptService --> NotifyModule
```

---

## Fee and Financial Aid Module Component Diagram

```mermaid
graph TB
    Student[Student]
    Admin[Admin]

    subgraph "Fee Module"
        FeeRouter[Fee Router]
        FeeService[Fee Service]
        InvoiceEngine[Invoice Engine]
        PaymentService[Payment Service]
        AidService[Financial Aid Service]
        ReceiptGenerator[Receipt Generator]
    end

    subgraph "Repositories"
        InvoiceRepo[(Invoice Repository)]
        PaymentRepo[(Payment Repository)]
        AidRepo[(Aid Application Repository)]
        FeeStructRepo[(Fee Structure Repository)]
    end

    PayGW[Payment Gateway]
    StorageService[Object Storage]
    NotifyModule[Notification Module]
    ERPSystem[ERP / Finance System]
    DB[(PostgreSQL)]

    Student --> FeeRouter
    Admin --> FeeRouter

    FeeRouter --> FeeService
    FeeRouter --> AidService
    FeeService --> InvoiceEngine
    FeeService --> PaymentService
    PaymentService --> ReceiptGenerator

    InvoiceEngine --> FeeStructRepo
    InvoiceEngine --> InvoiceRepo
    PaymentService --> PayGW
    PaymentService --> PaymentRepo
    AidService --> AidRepo

    ReceiptGenerator --> StorageService
    FeeService --> ERPSystem

    InvoiceRepo --> DB
    PaymentRepo --> DB
    AidRepo --> DB
    FeeStructRepo --> DB

    PaymentService --> NotifyModule
    AidService --> NotifyModule
```
