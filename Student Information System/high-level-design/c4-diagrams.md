# C4 Diagrams

## Overview
These C4 diagrams describe the Student Information System architecture at multiple levels: context, container, and component.

---

## Level 1: System Context Diagram

```mermaid
graph TB
    Student((Student))
    Faculty((Faculty))
    Admin((Admin Staff))
    Registrar((Registrar))
    Parent((Parent/Guardian))

    subgraph "Student Information System"
        System[SIS Platform<br>Modular monolith for academic management, enrollment, grades, attendance, fees, and reporting]
    end

    PaymentGW[Payment Providers<br>Online Banking / Cards / UPI]
    LDAPProvider[LDAP / SSO Provider]
    LibrarySystem[Library System]
    NotificationProviders[Email / SMS / Push]
    ERPSystem[ERP / Finance System]
    BiometricSystem[Biometric Attendance Devices]

    Student -->|enroll, view grades, pay fees, download transcript| System
    Faculty -->|manage courses, enter grades, mark attendance| System
    Admin -->|manage users, courses, fees, schedule exams| System
    Registrar -->|publish grades, issue transcripts, graduation| System
    Parent -->|view grades, attendance, fee status| System

    System -->|collect fee payments| PaymentGW
    System <-->|authenticate institutional users| LDAPProvider
    System <-->|book catalog, borrowing records| LibrarySystem
    System -->|send notifications and alerts| NotificationProviders
    System <-->|sync financial records| ERPSystem
    System <-->|capture biometric attendance| BiometricSystem
```

---

## Level 2: Container Diagram

```mermaid
graph TB
    Student((Student))
    Faculty((Faculty))
    Admin((Admin))
    Registrar((Registrar))
    Parent((Parent))

    subgraph "Student Information System"
        StudentUI[Student Web / Mobile]
        FacultyUI[Faculty Portal]
        AdminUI[Admin Dashboard]
        ParentUI[Parent Portal]

        API[FastAPI Application<br>Versioned routers and domain modules]
        WS[Websocket Manager]
        Worker[Async Notification / Task Worker]

        DB[(PostgreSQL)]
        Redis[(Redis)]
        Storage[(Object Storage)]
    end

    PaymentGW[Payment Providers]
    LDAP[LDAP / SSO]
    Msg[Email / SMS / Push]
    Library[Library System]
    ERP[ERP / Finance]

    Student --> StudentUI
    Faculty --> FacultyUI
    Admin --> AdminUI
    Registrar --> AdminUI
    Parent --> ParentUI

    StudentUI --> API
    FacultyUI --> API
    AdminUI --> API
    ParentUI --> API

    API --> WS
    API --> Worker
    API --> DB
    API --> Redis
    API --> Storage

    API --> PaymentGW
    API --> LDAP
    API --> Library
    API --> ERP
    Worker --> Msg
```

---

## Level 3: Component Diagram - Academic Core

```mermaid
graph TB
    Client[Authenticated Client]

    subgraph "FastAPI Academic Core"
        EnrollmentAPI[Enrollment / Registration Routers]
        CourseAPI[Course / Curriculum Routers]
        AcademicsAPI[Grades / Records Routers]

        EnrollmentEngine[Enrollment Validation Engine]
        PrerequisiteChecker[Prerequisite Checker]
        WaitlistManager[Waitlist Manager]
        GradeCalculator[GPA / CGPA Calculator]
        DegreeAudit[Degree Audit Engine]
        Notify[Academic Event Notifier]
    end

    DB[(PostgreSQL)]
    Cache[(Redis)]
    WS[Websocket Manager]

    Client --> EnrollmentAPI
    Client --> CourseAPI
    Client --> AcademicsAPI

    EnrollmentAPI --> EnrollmentEngine
    EnrollmentAPI --> WaitlistManager
    EnrollmentEngine --> PrerequisiteChecker
    AcademicsAPI --> GradeCalculator
    AcademicsAPI --> DegreeAudit

    EnrollmentEngine --> Notify
    GradeCalculator --> Notify
    WaitlistManager --> Notify

    PrerequisiteChecker --> DB
    EnrollmentEngine --> DB
    WaitlistManager --> DB
    GradeCalculator --> DB
    DegreeAudit --> DB
    EnrollmentAPI --> Cache
    Notify --> WS
    Notify --> DB
```

---

## Level 3: Component Diagram - Administration and Fees

```mermaid
graph TB
    Operator[Admin / Registrar / Finance Staff]

    subgraph "Administration Components"
        AdminAPI[Admin / Registrar Routers]
        FeeAPI[Fee Management Routers]
        ReportAPI[Reporting Routers]
        ExamAPI[Exam Management Routers]

        FeeEngine[Fee Billing and Invoicing Engine]
        AidService[Financial Aid Service]
        TranscriptService[Transcript Generation Service]
        GraduationService[Graduation Clearance Service]
        ReportEngine[Report and Analytics Engine]
        Notify[Notification and Websocket Fanout]
    end

    DB[(PostgreSQL)]
    Storage[(Object Storage)]
    PayGW[Payment Providers]
    WS[Websocket Manager]

    Operator --> AdminAPI
    Operator --> FeeAPI
    Operator --> ReportAPI
    Operator --> ExamAPI

    FeeAPI --> FeeEngine
    FeeAPI --> AidService
    AdminAPI --> TranscriptService
    AdminAPI --> GraduationService
    ReportAPI --> ReportEngine

    FeeEngine --> PayGW
    FeeEngine --> DB
    AidService --> DB
    TranscriptService --> Storage
    TranscriptService --> DB
    GraduationService --> DB
    ReportEngine --> DB
    ReportEngine --> Storage
    Notify --> WS
    Notify --> DB
```

---

## Architecture Boundary Summary

| Area | Current Design |
|------|----------------|
| Architecture | Modular monolith |
| Authentication | Local JWT + LDAP/SSO integration |
| Notifications | Persisted notifications + websocket fanout |
| Payments | Online banking, cards, UPI |
| Attendance | Manual, QR code, and biometric integration |
| Transcripts | PDF generation with digital signature |

## Implementation-Ready Addendum for C4 Diagrams

### Purpose in This Artifact
Adds policy/contract responsibilities to context and container levels.

### Scope Focus
- C4 governance overlays
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

