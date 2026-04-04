# C4 Code Diagram — Education Management Information System

This document maps EMIS code modules, their dependencies, and the runtime execution paths for the two most critical operations: student course enrollment and fee payment processing.

---

## 1. Code-Level Module Structure

```mermaid
flowchart TB
    subgraph Transport["Transport Layer — HTTP / HTMX / DRF"]
        URLRouter["URL Router\n(urls.py + DRF Router)"]
        ViewSets["DRF ViewSets\n(api/views.py)"]
        TemplateViews["Django Template Views\n(views.py)"]
        Serializers["DRF Serializers\n(api/serializers.py)"]
        Permissions["Permission Classes\n(api/permissions.py)"]
        Middleware["Auth Middleware\n(JWT + Session)"]
    end

    subgraph Application["Application Layer — Business Logic"]
        EnrollmentService["EnrollmentService\n(courses/services.py)"]
        GradeService["GradeService\n(exams/services.py)"]
        PaymentService["PaymentService\n(payment/services.py)"]
        NotificationService["NotificationService\n(notifications/services.py)"]
        ReportService["ReportService\n(reports/services.py)"]
        AttendanceService["AttendanceService\n(attendance/services.py)"]
        AdmissionsService["AdmissionsService\n(admissions/services.py)"]
        InvoiceService["InvoiceService\n(finance/services.py)"]
    end

    subgraph Domain["Domain Layer — Models & Business Rules"]
        StudentModel["Student Model\n(students/models.py)"]
        CourseModel["Course / Section Model\n(courses/models.py)"]
        EnrollmentModel["Enrollment Model\n(courses/models.py)"]
        ExamModel["Exam / Grade Model\n(exams/models.py)"]
        InvoiceModel["Invoice / Payment Model\n(finance/models.py)"]
        UserModel["User / Role Model\n(users/models.py)"]
        NotifModel["Notification Model\n(notifications/models.py)"]
    end

    subgraph Infrastructure["Infrastructure Layer — I/O Adapters"]
        ORM["Django ORM\n(PostgreSQL)"]
        RedisCache["Redis Cache\n(django-redis)"]
        CeleryTasks["Celery Task Dispatcher\n(.delay() / .apply_async())"]
        StripeAdapter["Stripe Adapter\n(payment/adapters/stripe.py)"]
        RazorpayAdapter["Razorpay Adapter\n(payment/adapters/razorpay.py)"]
        EmailAdapter["Email Adapter\n(SMTP via django.core.mail)"]
        SMSAdapter["SMS Adapter\n(notifications/adapters/sms.py)"]
        FileAdapter["File Storage Adapter\n(local / S3)"]
        PDFGenerator["PDF Generator\n(weasyprint / reportlab)"]
    end

    %% Transport → Application
    ViewSets --> Serializers
    ViewSets --> Permissions
    ViewSets --> Middleware
    ViewSets --> EnrollmentService
    ViewSets --> GradeService
    ViewSets --> PaymentService
    ViewSets --> InvoiceService
    ViewSets --> NotificationService
    ViewSets --> ReportService
    TemplateViews --> EnrollmentService
    TemplateViews --> GradeService

    %% Application → Domain
    EnrollmentService --> StudentModel
    EnrollmentService --> CourseModel
    EnrollmentService --> EnrollmentModel
    GradeService --> ExamModel
    GradeService --> StudentModel
    PaymentService --> InvoiceModel
    InvoiceService --> InvoiceModel
    InvoiceService --> StudentModel
    NotificationService --> NotifModel
    AdmissionsService --> StudentModel
    AttendanceService --> StudentModel

    %% Domain → Infrastructure
    StudentModel --> ORM
    CourseModel --> ORM
    EnrollmentModel --> ORM
    ExamModel --> ORM
    InvoiceModel --> ORM
    UserModel --> ORM
    NotifModel --> ORM

    %% Application → Infrastructure (direct)
    EnrollmentService --> RedisCache
    PaymentService --> StripeAdapter
    PaymentService --> RazorpayAdapter
    PaymentService --> CeleryTasks
    NotificationService --> EmailAdapter
    NotificationService --> SMSAdapter
    NotificationService --> CeleryTasks
    ReportService --> PDFGenerator
    ReportService --> CeleryTasks
    InvoiceService --> CeleryTasks
    GradeService --> CeleryTasks

    style Transport fill:#4A90E2,color:#fff,stroke:#357ABD
    style Application fill:#7B68EE,color:#fff,stroke:#6A5ACD
    style Domain fill:#27AE60,color:#fff,stroke:#229954
    style Infrastructure fill:#E67E22,color:#fff,stroke:#D35400
```

---

## 2. Critical Runtime Sequence: Student Course Registration

This sequence shows every internal component involved in a successful course registration, including the distributed lock, prerequisite check, timetable conflict detection, transactional enrollment creation, invoice update, and async notification dispatch.

```mermaid
sequenceDiagram
    autonumber
    actor Student
    participant Browser
    participant URLRouter as URL Router
    participant VS as EnrollmentViewSet\n(api/views.py)
    participant Auth as JWT Middleware
    participant SER as EnrollmentSerializer\n(api/serializers.py)
    participant ES as EnrollmentService\n(courses/services.py)
    participant Redis as Redis\n(Distributed Lock)
    participant PV as PrerequisiteValidator
    participant TCD as TimetableConflictDetector
    participant DB as PostgreSQL\n(Django ORM)
    participant IS as InvoiceService\n(finance/services.py)
    participant CT as Celery Task\n(notifications.tasks)

    Student->>Browser: Select course section, click "Register"
    Browser->>URLRouter: POST /api/v1/enrollments/
    URLRouter->>Auth: Validate JWT Bearer token
    Auth-->>URLRouter: student_id, role=STUDENT

    URLRouter->>VS: dispatch(request)
    VS->>SER: validate(request.data)
    SER->>SER: check required fields: section_id, semester_id
    alt Validation fails
        SER-->>VS: ValidationError
        VS-->>Browser: 400 {errors: {...}}
        Browser-->>Student: Show field errors
    else Validation passes
        SER-->>VS: validated_data
    end

    VS->>ES: enroll_student(student_id, section_id, semester_id)

    ES->>Redis: SET lock:enrollment:{student_id}:{section_id} EX=10s NX
    alt Lock already held (concurrent request)
        Redis-->>ES: null (lock exists)
        ES-->>VS: EnrollmentInProgressError
        VS-->>Browser: 409 {code: ENROLLMENT_IN_PROGRESS}
        Browser-->>Student: "Registration in progress, please wait"
    else Lock acquired
        Redis-->>ES: OK
    end

    ES->>DB: SELECT ... FOR UPDATE WHERE id = section_id
    Note over ES,DB: Pessimistic lock on section row
    DB-->>ES: CourseSection {seats_total, seats_used, course_id}

    alt No seats available
        ES->>Redis: DEL lock:enrollment:{student_id}:{section_id}
        ES-->>VS: CourseCapacityExceededError
        VS-->>Browser: 409 {code: COURSE_CAPACITY_EXCEEDED}
        Browser-->>Student: "This section is full"
    else Seats available
        ES->>PV: check_prerequisites(student_id, course_id)
        PV->>DB: SELECT completed course IDs for student
        DB-->>PV: {completed_course_ids: [...]}
        PV->>PV: diff(required_prerequisites, completed_courses)
        alt Prerequisites not met
            PV-->>ES: PrerequisiteNotMetError {missing: [CS101]}
            ES->>Redis: DEL lock
            ES-->>VS: PrerequisiteNotMetError
            VS-->>Browser: 422 {code: PREREQUISITES_NOT_MET, missing_courses: [...]}
            Browser-->>Student: "Complete CS101 before enrolling"
        else Prerequisites satisfied
            PV-->>ES: OK
        end

        ES->>TCD: check_conflict(student_id, section_id, semester_id)
        TCD->>DB: SELECT enrolled sections and their time slots for student
        DB-->>TCD: {existing_slots: [...]}
        TCD->>TCD: Overlap check against new section time slot
        alt Timetable conflict detected
            TCD-->>ES: TimetableConflictError {conflicting_section: "CS201-A"}
            ES->>Redis: DEL lock
            ES-->>VS: TimetableConflictError
            VS-->>Browser: 409 {code: TIMETABLE_CONFLICT}
            Browser-->>Student: "Schedule conflict with CS201-A"
        else No conflict
            TCD-->>ES: OK
        end

        Note over ES,DB: All checks passed — commit transaction
        ES->>DB: BEGIN TRANSACTION
        ES->>DB: INSERT INTO enrollments (student_id, section_id, semester_id, status=ACTIVE)
        ES->>DB: UPDATE course_sections SET seats_used = seats_used + 1
        ES->>DB: COMMIT
        DB-->>ES: Enrollment {id, student_id, section_id}

        ES->>IS: update_invoice_for_enrollment(student_id, semester_id, course_id)
        IS->>DB: SELECT or UPDATE fee_invoice for current semester
        DB-->>IS: Updated invoice total
        IS-->>ES: Invoice updated

        ES->>Redis: DEL lock:enrollment:{student_id}:{section_id}
        ES-->>VS: Enrollment object

        VS->>CT: send_enrollment_confirmation.delay(enrollment_id)
        Note over VS,CT: Fire-and-forget async task

        VS-->>Browser: 201 Created {enrollment_id, section, course, schedule}
        Browser-->>Student: "Successfully registered for CS301-A"
    end
```

---

## 3. Critical Runtime Sequence: Fee Payment Processing

This sequence shows the complete payment saga including gateway session creation, webhook callback handling, idempotency checks, receipt generation, and audit logging.

```mermaid
sequenceDiagram
    autonumber
    actor Student
    participant Browser
    participant VS as PaymentViewSet\n(api/views.py)
    participant PS as PaymentService\n(payment/services.py)
    participant IRepo as InvoiceRepository\n(finance/models.py)
    participant GWAdapter as PaymentGatewayAdapter\n(Stripe / Razorpay)
    participant DB as PostgreSQL
    participant Redis as Redis\n(Idempotency Store)
    participant GW as External Payment Gateway
    participant CT as Celery Tasks

    Student->>Browser: Click "Pay Now" on fee invoice
    Browser->>VS: POST /api/v1/payments/initiate-gateway/\n{invoice_id, gateway="stripe", idempotency_key}

    VS->>Redis: GET idempotency:{invoice_id}:{idempotency_key}
    alt Duplicate request (key exists)
        Redis-->>VS: {session_url: "https://checkout.stripe.com/..."}
        VS-->>Browser: 200 {session_url} (replayed)
        Browser-->>Student: Redirect to existing Stripe session
    else New request
        Redis-->>VS: null
    end

    VS->>PS: initiate_payment(invoice_id, gateway, idempotency_key)
    PS->>IRepo: get_with_lock(invoice_id)
    IRepo->>DB: SELECT * FROM invoices WHERE id=? FOR UPDATE
    DB-->>IRepo: Invoice {amount, status, student_id}

    alt Invoice already PAID
        IRepo-->>PS: Invoice status=PAID
        PS-->>VS: InvoiceAlreadyPaidError
        VS-->>Browser: 409 {code: INVOICE_ALREADY_PAID}
        Browser-->>Student: "This invoice has already been paid"
    else Invoice status OK
        PS->>GWAdapter: create_checkout_session(amount, currency, invoice_id, return_url)
        GWAdapter->>GW: POST /v1/checkout/sessions (Stripe API)

        alt Gateway timeout or 5xx
            GW-->>GWAdapter: Timeout / 503
            GWAdapter-->>PS: GatewayTimeoutError
            PS-->>VS: 503 {code: GATEWAY_UNAVAILABLE, retry_after: 30}
            VS-->>Browser: 503 + retry suggestion
            Browser-->>Student: "Payment gateway unavailable, try again in 30s"
        else Session created
            GW-->>GWAdapter: {session_id, checkout_url}
            GWAdapter-->>PS: {session_id, checkout_url}
        end

        PS->>DB: INSERT INTO payment_sessions (invoice_id, session_id, gateway, status=PENDING)
        PS->>Redis: SET idempotency:{invoice_id}:{idempotency_key} = {session_url} EX=3600
        PS-->>VS: {checkout_url}
        VS-->>Browser: 200 {checkout_url}
        Browser-->>Student: Redirect to Stripe/Razorpay checkout page
    end

    Note over Student,GW: Student completes payment on gateway page

    GW->>VS: POST /api/v1/payments/webhook/ {event: payment_intent.succeeded, session_id}
    VS->>PS: handle_webhook(event_payload, signature)
    PS->>PS: verify_webhook_signature(signature, secret)

    alt Invalid signature
        PS-->>VS: 400 Reject
    else Valid signature
        PS->>Redis: GET processed:{session_id}
        alt Already processed (duplicate webhook)
            Redis-->>PS: "processed"
            PS-->>VS: 200 OK (idempotent)
        else First delivery
            PS->>DB: SELECT * FROM payment_sessions WHERE session_id=? FOR UPDATE
            DB-->>PS: PaymentSession {invoice_id, status=PENDING}

            PS->>DB: BEGIN TRANSACTION
            PS->>DB: UPDATE invoices SET status=PAID, paid_at=NOW()
            PS->>DB: INSERT INTO payment_transactions (session_id, amount, gateway_ref, status=SUCCESS)
            PS->>DB: COMMIT

            PS->>Redis: SET processed:{session_id} = "processed" EX=86400

            PS->>CT: generate_receipt_pdf.delay(payment_transaction_id)
            PS->>CT: send_payment_confirmation_email.delay(invoice_id)
            PS->>CT: update_student_academic_hold.delay(student_id)

            PS-->>VS: 200 OK
        end
    end

    Note over CT,Student: Async: PDF receipt generated and emailed

    CT->>DB: Fetch invoice, student, payment details
    CT->>CT: Render PDF receipt (WeasyPrint)
    CT->>CT: Save PDF to file storage
    CT->>DB: UPDATE payment_transactions SET receipt_url=...
    CT->>CT: send_email(to=student_email, attachment=receipt_pdf)
    CT-->>Student: Email: "Your payment receipt for INV-2024-001234"
```

---

## 4. Django App Dependency Graph

This diagram shows which apps may import from which other apps. Arrows represent allowed imports. **Circular dependencies are prohibited.**

```mermaid
flowchart TB
    subgraph Foundation["Foundation (no upstream dependencies)"]
        core["core\n(BaseModel, utils, middleware)"]
        users["users\n(User, Role, Permission, RBAC)"]
    end

    subgraph Academic["Academic Core"]
        courses["courses\n(Program, Course, Section, Enrollment)"]
        students["students\n(Student, SemesterEnrollment)"]
        admissions["admissions\n(Application, MeritList)"]
        faculty["faculty\n(Faculty, TeachingLoad)"]
        timetable["timetable\n(Slot, RoomAllocation)"]
        academic_sessions["academic_sessions\n(AcademicYear, Semester, RegistrationWindow)"]
        departments["departments\n(Department, Program, CurriculumChange)"]
    end

    subgraph Assessment["Assessment"]
        exams["exams\n(Exam, Grade, GPA)"]
        attendance["attendance\n(AttendanceRecord, Leave)"]
    end

    subgraph AcademicLifecycle["Academic Lifecycle"]
        graduation["graduation\n(GraduationApplication, DegreeAudit, Diploma)"]
        academic_standing["academic_standing\n(StandingRecord, Probation, DeansList)"]
        grade_appeals["grade_appeals\n(GradeAppeal, Escalation, Resolution)"]
        transfer_credits["transfer_credits\n(TransferEvaluation, ArticulationAgreement)"]
    end

    subgraph Compliance["Compliance & Conduct"]
        discipline["discipline\n(DisciplinaryCase, Hearing, Sanction)"]
    end

    subgraph Finance["Finance & HR"]
        finance["finance\n(FeeStructure, Invoice)"]
        payment["payment\n(PaymentSession, Transaction)"]
        hr["hr\n(Employee, Payroll, Leave)"]
        inventory["inventory\n(Asset, Stock, PurchaseOrder)"]
        scholarships["scholarships\n(ScholarshipProgram, Application, Disbursement)"]
        recruitment["recruitment\n(JobPosting, Applicant, Interview, Offer)"]
    end

    subgraph Services["Service Modules"]
        lms["lms\n(Module, Content, Assignment, Quiz)"]
        library["library\n(Book, Issue, Fine)"]
        hostel["hostel\n(Room, Allocation, Mess)"]
        transport["transport\n(Route, Vehicle, Allocation)"]
        facilities["facilities\n(Room, Booking, MaintenanceRequest)"]
    end

    subgraph Output["Output & Communication"]
        notifications["notifications\n(Notification, Template)"]
        analytics["analytics\n(Dashboard, Metric)"]
        reports["reports\n(Report, Schedule)"]
        cms["cms\n(Page, Article, Media)"]
        seo["seo\n(MetaTag, Sitemap)"]
        calendar["calendar\n(Event, AcademicCalendar)"]
        portal["portal\n(StudentPortal, FacultyPortal)"]
        files["files\n(Document, StoredFile)"]
    end

    %% Foundation dependencies
    users --> core
    courses --> core
    courses --> users
    students --> core
    students --> users
    students --> courses
    admissions --> core
    admissions --> users
    admissions --> courses
    admissions --> students
    faculty --> core
    faculty --> users
    timetable --> core
    timetable --> courses
    timetable --> faculty

    %% Assessment dependencies
    exams --> core
    exams --> courses
    exams --> students
    exams --> timetable
    attendance --> core
    attendance --> courses
    attendance --> students

    %% Finance dependencies
    finance --> core
    finance --> students
    finance --> courses
    payment --> core
    payment --> finance
    hr --> core
    hr --> users
    inventory --> core

    %% Service module dependencies
    lms --> core
    lms --> courses
    lms --> students
    library --> core
    library --> users
    hostel --> core
    hostel --> students
    transport --> core
    transport --> students

    %% Academic Core extended dependencies
    academic_sessions --> core
    academic_sessions --> calendar
    departments --> faculty
    departments --> courses
    departments --> core

    %% Academic Lifecycle dependencies
    graduation --> students
    graduation --> courses
    graduation --> academic_standing
    graduation --> finance
    academic_standing --> students
    academic_standing --> courses
    academic_standing --> notifications
    grade_appeals --> students
    grade_appeals --> courses
    grade_appeals --> exams
    grade_appeals --> faculty
    transfer_credits --> students
    transfer_credits --> courses
    transfer_credits --> admissions

    %% Compliance dependencies
    discipline --> students
    discipline --> users
    discipline --> notifications

    %% Extended Finance & HR dependencies
    scholarships --> students
    scholarships --> finance
    scholarships --> academic_standing
    recruitment --> hr
    recruitment --> departments
    recruitment --> users

    %% Facilities dependencies
    facilities --> timetable
    facilities --> core
    facilities --> notifications

    %% Output dependencies
    notifications --> core
    notifications --> users
    analytics --> core
    analytics --> students
    analytics --> exams
    analytics --> attendance
    analytics --> finance
    reports --> core
    reports --> students
    reports --> exams
    reports --> finance
    portal --> core
    portal --> students
    portal --> exams
    portal --> finance
    portal --> attendance
    portal --> lms
    cms --> core
    seo --> core
    seo --> cms
    calendar --> core
    files --> core

    style Foundation fill:#27AE60,color:#fff
    style Academic fill:#4A90E2,color:#fff
    style Assessment fill:#7B68EE,color:#fff
    style AcademicLifecycle fill:#3498DB,color:#fff
    style Compliance fill:#C0392B,color:#fff
    style Finance fill:#E67E22,color:#fff
    style Services fill:#E74C3C,color:#fff
    style Output fill:#95A5A6,color:#fff
```

---

## 5. Celery Task Execution Flow

```mermaid
flowchart TB
    subgraph Django["Django Application Process"]
        Service["Service Layer\n(services.py)"]
        TaskCall[".delay() / .apply_async()\nwith task args (entity IDs only)"]
        Service --> TaskCall
    end

    subgraph Broker["Redis Broker"]
        HiQueue["Queue: high_priority\n(payment, grade lock)"]
        DefQueue["Queue: default\n(notifications, reports)"]
        SchedQueue["Queue: scheduled\n(celery-beat tasks)"]
        TaskCall --> HiQueue
        TaskCall --> DefQueue
        SchedQueue
    end

    subgraph Workers["Celery Worker Pool"]
        W1["Worker 1\n(high_priority consumer)"]
        W2["Worker 2\n(default consumer)"]
        W3["Worker 3\n(default consumer)"]
        WB["Celery Beat\n(scheduled consumer)"]
        HiQueue --> W1
        DefQueue --> W2
        DefQueue --> W3
        SchedQueue --> WB
    end

    subgraph Execution["Task Execution"]
        Fetch["Re-fetch entity from DB\n(never pass model instances)"]
        IdempCheck["Idempotency Check\n(has this already been processed?)"]
        Logic["Execute Task Logic\n(send email, generate PDF, etc.)"]
        Success["Mark task complete\nUpdate DB status"]
        W1 --> Fetch --> IdempCheck
        W2 --> Fetch
        W3 --> Fetch
        WB --> Fetch
        IdempCheck -->|Already done| Skip["Return early (skip)"]
        IdempCheck -->|Not done| Logic --> Success
    end

    subgraph Retry["Retry & Error Handling"]
        RetryDelay["Exponential backoff\n(base 2s, max 300s, jitter)"]
        MaxRetries["Max retries exceeded\n(default: 5)"]
        DLQ["Dead Letter Queue\n(Redis list: celery.dead_letters)"]
        AlertOps["Alert: ops team\n(Sentry + PagerDuty)"]
        Logic -->|Exception| RetryDelay --> Logic
        RetryDelay -->|max_retries exceeded| MaxRetries --> DLQ --> AlertOps
    end

    subgraph ResultStore["Result Store (Redis)"]
        TaskResult["Task result stored 1 hour\nfor status polling"]
        Success --> TaskResult
    end
```

---

## 6. Architectural Invariants

The following rules must **never** be violated. They are checked in code review and via architectural fitness functions in CI.

1. **Services never import from the API layer.** `services.py` must not import from `api/views.py`, `api/serializers.py`, or `api/permissions.py`. The dependency arrow is strictly one-way: Transport → Application → Domain → Infrastructure.

2. **Models never call Services.** Django model methods may compute derived values from their own fields, but must never call service layer functions or Celery tasks. Side effects belong in `signals.py` (for framework-level reactions) or `services.py` (for business-triggered reactions).

3. **Tasks are always idempotent.** Every Celery task must handle the case where it is executed more than once with the same input. The first execution produces the side effect; subsequent executions detect the prior execution and return early without repeating the side effect.

4. **Tasks receive only IDs, never model instances.** Model instances are not serializable across process boundaries. Tasks always receive UUIDs/strings and re-fetch the entity inside the task body.

5. **No circular app imports.** The dependency graph above is the law. If app A imports from app B, then app B must not import from app A directly or transitively. Violations are caught by `import-linter` in CI.

6. **Transaction.atomic wraps all multi-table writes.** Any service operation that writes to more than one database table must be wrapped in `django.db.transaction.atomic()`. Partial writes that leave the database in an inconsistent state are not acceptable.

7. **All database writes to sensitive tables are audited.** Writes to: `grades`, `gpa_records`, `fee_invoices`, `payments`, `student_status_history`, `user_roles`, `payroll_records` must insert a corresponding row into `core_audit_log` within the same transaction.

---

## 7. Code-Level Component Diagrams — New Modules

### 7.1 Graduation App

```mermaid
flowchart TB
    subgraph GraduationTransport["Transport Layer"]
        GradViewSet["GraduationApplicationViewSet\n(api/views.py)"]
        GradSerializer["GraduationSerializer\n(api/serializers.py)"]
        GradPermissions["GraduationPermissions\n(api/permissions.py)"]
        GradTemplateView["GraduationTemplateView\n(views.py)"]
    end

    subgraph GraduationApp["Application Layer"]
        GraduationService["GraduationService\n(graduation/services.py)"]
        DegreeAuditEngine["DegreeAuditEngine\n(graduation/services.py)"]
        DiplomaGenerator["DiplomaGenerator\n(graduation/services.py)"]
        HonorsCalculator["HonorsCalculator\n(graduation/services.py)"]
    end

    subgraph GraduationDomain["Domain Layer"]
        GradApplication["GraduationApplication\n(graduation/models.py)"]
        DegreeAudit["DegreeAuditResult\n(graduation/models.py)"]
        Diploma["Diploma\n(graduation/models.py)"]
        HonorsAward["HonorsAward\n(graduation/models.py)"]
    end

    subgraph GraduationInfra["Infrastructure Layer"]
        GradORM["Django ORM\n(PostgreSQL)"]
        GradCelery["Celery Tasks\n(graduation/tasks.py)"]
        GradPDF["PDF Generator\n(weasyprint)"]
    end

    GradViewSet --> GradSerializer
    GradViewSet --> GradPermissions
    GradViewSet --> GraduationService
    GradTemplateView --> GraduationService

    GraduationService --> DegreeAuditEngine
    GraduationService --> DiplomaGenerator
    GraduationService --> HonorsCalculator
    GraduationService --> GradApplication
    DegreeAuditEngine --> DegreeAudit
    DiplomaGenerator --> Diploma
    HonorsCalculator --> HonorsAward

    GradApplication --> GradORM
    DegreeAudit --> GradORM
    Diploma --> GradORM
    GraduationService --> GradCelery
    DiplomaGenerator --> GradPDF

    style GraduationTransport fill:#4A90E2,color:#fff,stroke:#357ABD
    style GraduationApp fill:#7B68EE,color:#fff,stroke:#6A5ACD
    style GraduationDomain fill:#27AE60,color:#fff,stroke:#229954
    style GraduationInfra fill:#E67E22,color:#fff,stroke:#D35400
```

### 7.2 Discipline App

```mermaid
flowchart TB
    subgraph DisciplineTransport["Transport Layer"]
        DiscViewSet["DisciplinaryCaseViewSet\n(api/views.py)"]
        DiscSerializer["DisciplinaryCaseSerializer\n(api/serializers.py)"]
        DiscPermissions["DisciplinePermissions\n(api/permissions.py)"]
        DiscTemplateView["DisciplineTemplateView\n(views.py)"]
    end

    subgraph DisciplineApp["Application Layer"]
        DisciplineService["DisciplineService\n(discipline/services.py)"]
        HearingManager["HearingManager\n(discipline/services.py)"]
        SanctionEngine["SanctionEngine\n(discipline/services.py)"]
        AppealHandler["AppealHandler\n(discipline/services.py)"]
        RecordSealingService["RecordSealingService\n(discipline/services.py)"]
    end

    subgraph DisciplineDomain["Domain Layer"]
        DiscCase["DisciplinaryCase\n(discipline/models.py)"]
        Hearing["Hearing\n(discipline/models.py)"]
        Sanction["Sanction\n(discipline/models.py)"]
        DiscAppeal["DisciplineAppeal\n(discipline/models.py)"]
    end

    subgraph DisciplineInfra["Infrastructure Layer"]
        DiscORM["Django ORM\n(PostgreSQL)"]
        DiscCelery["Celery Tasks\n(discipline/tasks.py)"]
        DiscNotif["NotificationService\n(notifications/services.py)"]
    end

    DiscViewSet --> DiscSerializer
    DiscViewSet --> DiscPermissions
    DiscViewSet --> DisciplineService
    DiscTemplateView --> DisciplineService

    DisciplineService --> HearingManager
    DisciplineService --> SanctionEngine
    DisciplineService --> AppealHandler
    DisciplineService --> RecordSealingService
    DisciplineService --> DiscCase
    HearingManager --> Hearing
    SanctionEngine --> Sanction
    AppealHandler --> DiscAppeal

    DiscCase --> DiscORM
    Hearing --> DiscORM
    Sanction --> DiscORM
    DiscAppeal --> DiscORM
    DisciplineService --> DiscCelery
    DisciplineService --> DiscNotif

    style DisciplineTransport fill:#4A90E2,color:#fff,stroke:#357ABD
    style DisciplineApp fill:#7B68EE,color:#fff,stroke:#6A5ACD
    style DisciplineDomain fill:#27AE60,color:#fff,stroke:#229954
    style DisciplineInfra fill:#E67E22,color:#fff,stroke:#D35400
```

### 7.3 Academic Sessions App

```mermaid
flowchart TB
    subgraph SessionTransport["Transport Layer"]
        SessionViewSet["SessionViewSet\n(api/views.py)"]
        SessionSerializer["SessionSerializer\n(api/serializers.py)"]
        SessionPermissions["SessionPermissions\n(api/permissions.py)"]
        SessionTemplateView["SessionTemplateView\n(views.py)"]
    end

    subgraph SessionApp["Application Layer"]
        SessionService["SessionService\n(academic_sessions/services.py)"]
        RegistrationWindowManager["RegistrationWindowManager\n(academic_sessions/services.py)"]
        CalendarSyncService["CalendarSyncService\n(academic_sessions/services.py)"]
        SemesterLifecycleEngine["SemesterLifecycleEngine\n(academic_sessions/services.py)"]
    end

    subgraph SessionDomain["Domain Layer"]
        AcademicYear["AcademicYear\n(academic_sessions/models.py)"]
        Semester["Semester\n(academic_sessions/models.py)"]
        RegWindow["RegistrationWindow\n(academic_sessions/models.py)"]
        CalendarEvent["SessionCalendarEvent\n(academic_sessions/models.py)"]
    end

    subgraph SessionInfra["Infrastructure Layer"]
        SessORM["Django ORM\n(PostgreSQL)"]
        SessCelery["Celery Tasks\n(academic_sessions/tasks.py)"]
        SessCache["Redis Cache\n(django-redis)"]
    end

    SessionViewSet --> SessionSerializer
    SessionViewSet --> SessionPermissions
    SessionViewSet --> SessionService
    SessionTemplateView --> SessionService

    SessionService --> RegistrationWindowManager
    SessionService --> CalendarSyncService
    SessionService --> SemesterLifecycleEngine
    SessionService --> AcademicYear
    SessionService --> Semester
    RegistrationWindowManager --> RegWindow
    CalendarSyncService --> CalendarEvent

    AcademicYear --> SessORM
    Semester --> SessORM
    RegWindow --> SessORM
    CalendarEvent --> SessORM
    SessionService --> SessCelery
    SessionService --> SessCache

    style SessionTransport fill:#4A90E2,color:#fff,stroke:#357ABD
    style SessionApp fill:#7B68EE,color:#fff,stroke:#6A5ACD
    style SessionDomain fill:#27AE60,color:#fff,stroke:#229954
    style SessionInfra fill:#E67E22,color:#fff,stroke:#D35400
```

### 7.4 Scholarships App

```mermaid
flowchart TB
    subgraph ScholarshipTransport["Transport Layer"]
        ScholViewSet["ScholarshipViewSet\n(api/views.py)"]
        ScholSerializer["ScholarshipSerializer\n(api/serializers.py)"]
        ScholPermissions["ScholarshipPermissions\n(api/permissions.py)"]
        ScholTemplateView["ScholarshipTemplateView\n(views.py)"]
    end

    subgraph ScholarshipApp["Application Layer"]
        ScholarshipService["ScholarshipService\n(scholarships/services.py)"]
        DisbursementEngine["DisbursementEngine\n(scholarships/services.py)"]
        StackingValidator["StackingValidator\n(scholarships/services.py)"]
        RenewalEvaluator["RenewalEvaluator\n(scholarships/services.py)"]
    end

    subgraph ScholarshipDomain["Domain Layer"]
        ScholProgram["ScholarshipProgram\n(scholarships/models.py)"]
        ScholApplication["ScholarshipApplication\n(scholarships/models.py)"]
        Disbursement["Disbursement\n(scholarships/models.py)"]
        StackingRule["StackingRule\n(scholarships/models.py)"]
    end

    subgraph ScholarshipInfra["Infrastructure Layer"]
        ScholORM["Django ORM\n(PostgreSQL)"]
        ScholCelery["Celery Tasks\n(scholarships/tasks.py)"]
    end

    ScholViewSet --> ScholSerializer
    ScholViewSet --> ScholPermissions
    ScholViewSet --> ScholarshipService
    ScholTemplateView --> ScholarshipService

    ScholarshipService --> DisbursementEngine
    ScholarshipService --> StackingValidator
    ScholarshipService --> RenewalEvaluator
    ScholarshipService --> ScholProgram
    ScholarshipService --> ScholApplication
    DisbursementEngine --> Disbursement
    StackingValidator --> StackingRule

    ScholProgram --> ScholORM
    ScholApplication --> ScholORM
    Disbursement --> ScholORM
    StackingRule --> ScholORM
    ScholarshipService --> ScholCelery

    style ScholarshipTransport fill:#4A90E2,color:#fff,stroke:#357ABD
    style ScholarshipApp fill:#7B68EE,color:#fff,stroke:#6A5ACD
    style ScholarshipDomain fill:#27AE60,color:#fff,stroke:#229954
    style ScholarshipInfra fill:#E67E22,color:#fff,stroke:#D35400
```

### 7.5 Recruitment App

```mermaid
flowchart TB
    subgraph RecruitmentTransport["Transport Layer"]
        RecViewSet["RecruitmentViewSet\n(api/views.py)"]
        RecSerializer["RecruitmentSerializer\n(api/serializers.py)"]
        RecPermissions["RecruitmentPermissions\n(api/permissions.py)"]
        RecTemplateView["RecruitmentTemplateView\n(views.py)"]
    end

    subgraph RecruitmentApp["Application Layer"]
        RecruitmentService["RecruitmentService\n(recruitment/services.py)"]
        InterviewScheduler["InterviewScheduler\n(recruitment/services.py)"]
        OfferManager["OfferManager\n(recruitment/services.py)"]
        ApplicantTracker["ApplicantTracker\n(recruitment/services.py)"]
    end

    subgraph RecruitmentDomain["Domain Layer"]
        JobPosting["JobPosting\n(recruitment/models.py)"]
        Applicant["Applicant\n(recruitment/models.py)"]
        Interview["Interview\n(recruitment/models.py)"]
        Offer["Offer\n(recruitment/models.py)"]
    end

    subgraph RecruitmentInfra["Infrastructure Layer"]
        RecORM["Django ORM\n(PostgreSQL)"]
        RecCelery["Celery Tasks\n(recruitment/tasks.py)"]
        RecNotif["NotificationService\n(notifications/services.py)"]
    end

    RecViewSet --> RecSerializer
    RecViewSet --> RecPermissions
    RecViewSet --> RecruitmentService
    RecTemplateView --> RecruitmentService

    RecruitmentService --> InterviewScheduler
    RecruitmentService --> OfferManager
    RecruitmentService --> ApplicantTracker
    RecruitmentService --> JobPosting
    ApplicantTracker --> Applicant
    InterviewScheduler --> Interview
    OfferManager --> Offer

    JobPosting --> RecORM
    Applicant --> RecORM
    Interview --> RecORM
    Offer --> RecORM
    RecruitmentService --> RecCelery
    RecruitmentService --> RecNotif

    style RecruitmentTransport fill:#4A90E2,color:#fff,stroke:#357ABD
    style RecruitmentApp fill:#7B68EE,color:#fff,stroke:#6A5ACD
    style RecruitmentDomain fill:#27AE60,color:#fff,stroke:#229954
    style RecruitmentInfra fill:#E67E22,color:#fff,stroke:#D35400
```
