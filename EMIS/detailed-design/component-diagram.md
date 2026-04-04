# Component Diagram — Education Management Information System

This document shows internal component structure across EMIS containers, illustrating how Django apps, services, adapters, and infrastructure components interact.

---

## 1. Full Application Component Overview

All 25 Django apps grouped by domain, with inter-component dependencies.

```mermaid
flowchart TB
    subgraph Foundation["Foundation Layer"]
        core["core\nBaseModel · Audit · Middleware"]
        users["users\nAuth · RBAC · JWT · Permissions"]
    end

    subgraph Academic["Academic Layer"]
        admissions["admissions\nApplication · MeritList · Enrollment"]
        students["students\nProfile · Status · Progress"]
        courses["courses\nProgram · Course · Section · Enrollment"]
        faculty["faculty\nProfile · TeachingLoad · Leave"]
        timetable["timetable\nSlot · RoomAllocation · ConflictDetection"]
        exams["exams\nExam · Grade · GPA · Transcript"]
        attendance["attendance\nSession · Record · ThresholdMonitor"]
        lms["lms\nModule · Content · Assignment · Quiz · Certificate"]
    end

    subgraph Admin["Administrative Layer"]
        finance["finance\nFeeStructure · Invoice · Scholarship"]
        payment["payment\nGateway · Transaction · Receipt · Refund"]
        hr["hr\nEmployee · Payroll · Leave · Payslip"]
        inventory["inventory\nAsset · Stock · PurchaseOrder"]
    end

    subgraph Facilities["Facility Layer"]
        library["library\nCatalog · Circulation · Fine"]
        hostel["hostel\nRoom · Allocation · Mess · Complaint"]
        transport["transport\nRoute · Vehicle · Allocation"]
    end

    subgraph Output["Output & Communication Layer"]
        notifications["notifications\nDispatch · Template · Retry"]
        analytics["analytics\nDashboard · KPI · AtRisk"]
        reports["reports\nBuilder · Scheduler · Export"]
        cms["cms\nPage · Article · Media · Menu"]
        seo["seo\nMetaTag · Sitemap · Analytics"]
        calendar["calendar\nAcademicCalendar · Event · Personal"]
        portal["portal\nStudentPortal · FacultyPortal · ParentPortal"]
        files["files\nDocument · Storage · Version"]
    end

    %% Foundation
    users --> core
    admissions --> core & users
    students --> core & users & courses & admissions
    courses --> core & users
    faculty --> core & users
    timetable --> core & courses & faculty
    exams --> core & courses & students
    attendance --> core & courses & students
    lms --> core & courses & students

    finance --> core & students & courses
    payment --> core & finance
    hr --> core & users
    inventory --> core

    library --> core & users
    hostel --> core & students
    transport --> core & students

    notifications --> core & users
    analytics --> core & students & exams & attendance & finance
    reports --> core & students & exams & finance
    portal --> core & students & exams & finance & attendance & lms
    cms --> core
    seo --> core & cms
    calendar --> core
    files --> core
```

---

## 2. Academic Core Components — Detailed View

```mermaid
flowchart LR
    subgraph HTTP["HTTP / HTMX Layer"]
        CoursesURLRouter["courses/urls.py\nDRF Router + Template URLs"]
        ExamsURLRouter["exams/urls.py\nDRF Router + Template URLs"]
        AttendanceURLRouter["attendance/urls.py\nDRF Router"]
    end

    subgraph API["DRF API Components"]
        CourseViewSet["CourseViewSet\nCRUD + filter + pagination"]
        EnrollmentViewSet["EnrollmentViewSet\nPOST: register / DELETE: drop"]
        GradeViewSet["GradeViewSet\nBulk submit + publish + amend"]
        AttendanceViewSet["AttendanceViewSet\nBulk mark + session + reports"]
        CourseSerializer["CourseSerializer\nInput validation + output formatting"]
        EnrollmentSerializer["EnrollmentSerializer\nPrerequisite error mapping"]
        GradeSerializer["GradeSerializer\nMarks → letter grade transform"]
    end

    subgraph Services["Business Logic Services"]
        EnrollmentSvc["EnrollmentService\nenroll_student()\ndrop_course()\ncheck_credit_hours()"]
        GradeSvc["GradeService\nsubmit_grades()\npublish_grades()\namend_grade()\ncalculate_gpa()"]
        AttendanceSvc["AttendanceService\nmark_bulk()\ncalculate_percentage()\ncheck_threshold()"]
        PrereqValidator["PrerequisiteValidator\ncheck_prerequisites()"]
        TimetableDetector["TimetableConflictDetector\ncheck_conflict()"]
    end

    subgraph Models["Django ORM Models"]
        CourseModel["Course Model\n+get_available_sections()"]
        EnrollmentModel["Enrollment Model\n+is_droppable()"]
        GradeModel["Grade Model\n+compute_letter_grade()\n+compute_grade_points()"]
        AttendanceModel["AttendanceRecord Model\n+get_percentage()"]
    end

    subgraph Tasks["Celery Async Tasks"]
        NotifyEnrollTask["notify_enrollment_confirmation\n(notifications queue)"]
        RecalcGPATask["recalculate_student_gpa\n(default queue)"]
        AttendanceAlertTask["check_attendance_threshold\n(scheduled queue, nightly)"]
        UpdateInvoiceTask["update_invoice_for_enrollment\n(default queue)"]
    end

    subgraph Infra["Infrastructure"]
        PostgreSQL[("PostgreSQL\nPrimary DB")]
        Redis[("Redis\nCache + Locks")]
    end

    CoursesURLRouter --> CourseViewSet & EnrollmentViewSet
    ExamsURLRouter --> GradeViewSet
    AttendanceURLRouter --> AttendanceViewSet

    CourseViewSet --> CourseSerializer --> CourseModel --> PostgreSQL
    EnrollmentViewSet --> EnrollmentSerializer --> EnrollmentSvc
    EnrollmentSvc --> PrereqValidator & TimetableDetector
    EnrollmentSvc --> EnrollmentModel --> PostgreSQL
    EnrollmentSvc --> Redis
    EnrollmentSvc --> NotifyEnrollTask & UpdateInvoiceTask

    GradeViewSet --> GradeSerializer --> GradeSvc
    GradeSvc --> GradeModel --> PostgreSQL
    GradeSvc --> RecalcGPATask

    AttendanceViewSet --> AttendanceSvc
    AttendanceSvc --> AttendanceModel --> PostgreSQL
    AttendanceAlertTask --> AttendanceSvc
```

---

## 3. Finance and Payment Components

```mermaid
flowchart LR
    subgraph API["Finance API Layer"]
        InvoiceViewSet["InvoiceViewSet\nGET list/detail\nPOST generate-bulk"]
        PaymentViewSet["PaymentViewSet\nPOST initiate-gateway\nPOST webhook\nGET receipt"]
        RefundViewSet["RefundViewSet\nPOST request\nPOST approve"]
    end

    subgraph FinanceSvc["Finance Services"]
        InvoiceSvc["InvoiceService\ngenerate_semester_invoices()\nadd_line_item()\napply_scholarship()\ncompute_totals()"]
        FeeCalculator["FeeCalculator\ncalculate_fee_for_student()\napply_discounts()"]
        ReconciliationSvc["ReconciliationService\nreconcile_gateway_statement()\ndetect_discrepancies()"]
    end

    subgraph PaymentSvc["Payment Services"]
        PaymentProcessor["PaymentProcessor\ninitiate_payment()\nconfirm_payment()\nhandle_webhook()"]
        IdempotencyStore["IdempotencyStore\ncheck_key()\nstore_key()"]
        GatewayFactory["GatewayAdapterFactory\nget_adapter(gateway_name)"]
    end

    subgraph Adapters["Payment Gateway Adapters"]
        StripeAdapter["StripeAdapter\ncreate_checkout_session()\nverify_webhook()"]
        RazorpayAdapter["RazorpayAdapter\ncreate_order()\nverify_signature()"]
        BankTransferAdapter["BankTransferAdapter\nmanual confirmation"]
    end

    subgraph External["External Systems"]
        StripeGW["Stripe Gateway\n(HTTPS REST API)"]
        RazorpayGW["Razorpay Gateway\n(HTTPS REST API)"]
    end

    subgraph Models["Finance Models"]
        InvoiceModel["FeeInvoice\nFeeLineItem\nFeeStructure"]
        PaymentModel["PaymentTransaction\nPaymentSession\nRefund"]
    end

    subgraph Tasks["Async Tasks"]
        GenerateInvoiceBulkTask["generate_semester_invoices_bulk\n(scheduled: semester start)"]
        OverdueCheckTask["check_overdue_invoices\n(scheduled: nightly)"]
        ReceiptTask["generate_and_send_receipt\n(default queue)"]
        HoldTask["apply_or_release_financial_hold\n(default queue)"]
    end

    subgraph Infra["Infra"]
        PDFGen["PDF Generator\n(WeasyPrint)"]
        FileStore["File Storage\n(Local / S3)"]
        Redis[("Redis\nIdempotency Cache")]
        DB[("PostgreSQL")]
    end

    InvoiceViewSet --> InvoiceSvc --> FeeCalculator
    InvoiceSvc --> InvoiceModel --> DB
    PaymentViewSet --> PaymentProcessor
    PaymentProcessor --> IdempotencyStore --> Redis
    PaymentProcessor --> GatewayFactory
    GatewayFactory --> StripeAdapter --> StripeGW
    GatewayFactory --> RazorpayAdapter --> RazorpayGW
    PaymentProcessor --> PaymentModel --> DB
    PaymentProcessor --> ReceiptTask & HoldTask
    ReceiptTask --> PDFGen --> FileStore
    GenerateInvoiceBulkTask --> InvoiceSvc
    OverdueCheckTask --> InvoiceSvc --> HoldTask
    RefundViewSet --> PaymentProcessor
    ReconciliationSvc --> DB
```

---

## 4. Infrastructure Components

```mermaid
flowchart TB
    subgraph Client["Client Layer"]
        Browser["Browser\n(Bootstrap 5 + HTMX)"]
        MobileApp["Mobile Browser\n(Responsive)"]
        APIClient["API Client\n(Mobile App / Integrations)"]
    end

    subgraph Edge["Edge / Reverse Proxy"]
        Nginx["Nginx\n· SSL Termination\n· Static File Serving\n· Rate Limiting\n· gzip Compression\n· Upstream Load Balance"]
    end

    subgraph AppServer["Application Server Pool"]
        Gunicorn1["Gunicorn Worker 1\n(4 sync workers)"]
        Gunicorn2["Gunicorn Worker 2\n(4 sync workers)"]
        DjangoApp["Django Application\n25 Apps · DRF · HTMX\nSession + JWT Auth"]
    end

    subgraph CeleryLayer["Background Processing"]
        CeleryBeat["Celery Beat\n(1 instance)\nScheduled tasks:\n· Nightly attendance check\n· Invoice overdue check\n· Report generation\n· Outbox relay"]
        CeleryWorkerHi["Celery Worker\nhigh_priority queue\n(payment, grade lock)"]
        CeleryWorkerDef["Celery Worker\ndefault queue\n(notifications, reports)"]
        CeleryWorkerSched["Celery Worker\nscheduled queue\n(beat tasks)"]
    end

    subgraph Data["Data Layer"]
        PostgresPrimary[("PostgreSQL Primary\n(Write + Read)")]
        PostgresReplica[("PostgreSQL Read Replica\n(Reports + Analytics)")]
        Redis[("Redis\n· Session Store\n· Cache\n· Celery Broker\n· Idempotency Store\n· Distributed Locks")]
    end

    subgraph Storage["Storage"]
        LocalFS["Local Filesystem\n(Media / Uploads)"]
        S3["AWS S3\n(Production Media)"]
    end

    subgraph Monitoring["Observability"]
        Prometheus["Prometheus\n(django-prometheus)"]
        Grafana["Grafana\nDashboards"]
        Sentry["Sentry\nException Tracking"]
    end

    Browser & MobileApp & APIClient --> Nginx
    Nginx --> Gunicorn1 & Gunicorn2
    Gunicorn1 & Gunicorn2 --> DjangoApp
    DjangoApp --> PostgresPrimary
    DjangoApp --> Redis
    DjangoApp --> LocalFS & S3
    DjangoApp --> CeleryWorkerHi & CeleryWorkerDef
    CeleryBeat --> CeleryWorkerSched
    CeleryWorkerHi & CeleryWorkerDef & CeleryWorkerSched --> Redis
    CeleryWorkerHi & CeleryWorkerDef & CeleryWorkerSched --> PostgresPrimary
    DjangoApp --> Prometheus
    Prometheus --> Grafana
    DjangoApp --> Sentry
    PostgresReplica -.->|replication| PostgresPrimary
```

---

## 5. Notification System Components

```mermaid
flowchart LR
    subgraph Triggers["Event Triggers"]
        DomainEvents["Domain Events\n(outbox relay)"]
        DirectCalls["Direct Service Calls\n(from other services)"]
        BeatTasks["Scheduled Tasks\n(Celery Beat)"]
    end

    subgraph NotifRouter["Notification Router"]
        Router["NotificationRouter\nDetermines channel(s)\nbased on:\n· event type\n· user preferences\n· consent status"]
        PrefStore["UserPreferences\n(DB table)"]
        ConsentStore["ConsentRegistry\n(DB table)"]
    end

    subgraph Channels["Delivery Channels"]
        EmailChannel["Email Channel\ndjango.core.mail\n(SMTP)"]
        SMSChannel["SMS Channel\nHTTPS API\n(Twilio / local gateway)"]
        InAppChannel["In-App Channel\nStored in notifications_notification\nPolled by portal via API"]
    end

    subgraph Templates["Template Engine"]
        TemplateRenderer["Template Renderer\nDjango template engine\nvariable substitution\nlanguage/locale support"]
        TemplateStore["NotificationTemplate\n(DB table, versioned)"]
    end

    subgraph RetryInfra["Retry Infrastructure"]
        RetryTask["Celery Retry\nExponential backoff\nmax 5 retries"]
        DLQ["Dead Letter Queue\n(Redis list)"]
        OpsAlert["Ops Alert\n(Sentry + on-call)"]
    end

    subgraph Infra["Infrastructure"]
        SMTPServer["SMTP Server\n(SendGrid / SES / local)"]
        SMSGateway["SMS Gateway\n(Twilio / Telenor API)"]
        DB[("PostgreSQL\nNotification records")]
        Redis[("Redis\nTask queue")]
    end

    DomainEvents & DirectCalls & BeatTasks --> Router
    Router --> PrefStore & ConsentStore
    Router --> TemplateRenderer
    TemplateRenderer --> TemplateStore
    Router --> EmailChannel & SMSChannel & InAppChannel
    EmailChannel --> SMTPServer
    SMSChannel --> SMSGateway
    InAppChannel --> DB
    EmailChannel & SMSChannel -->|On failure| RetryTask --> Redis
    RetryTask -->|Max retries| DLQ --> OpsAlert
```

---

## 6. Graduation & Academic Progress Components

```mermaid
flowchart LR
    subgraph API["Graduation & Progress API Layer"]
        GradAuditViewSet["DegreeAuditViewSet\nGET audit-report\nPOST run-audit"]
        GradViewSet["GraduationViewSet\nPOST apply\nGET status\nPOST confer"]
        StandingViewSet["AcademicStandingViewSet\nGET status\nPOST evaluate"]
        TransferViewSet["TransferCreditViewSet\nPOST submit\nGET equivalencies"]
    end

    subgraph Services["Business Logic Services"]
        GraduationSvc["GraduationService\napply_for_graduation()\nconfer_degree()\ngenerate_certificate()"]
        DegreeAuditEngine["DegreeAuditEngine\nrun_audit()\ncheck_requirements()\nidentify_deficiencies()"]
        AcademicStandingSvc["AcademicStandingService\nevaluate_standing()\napply_probation()\ncheck_dismissal()"]
        TransferCreditSvc["TransferCreditService\nevaluate_credits()\nmap_equivalencies()\napply_transfer()"]
    end

    subgraph Models["Django ORM Models"]
        GradModel["GraduationApplication\nDegreeConferral\nCertificate"]
        AuditModel["DegreeAudit\nRequirementCheck\nDeficiency"]
        StandingModel["AcademicStanding\nProbationRecord\nProgressReport"]
        TransferModel["TransferCredit\nCourseEquivalency\nArticulationAgreement"]
    end

    subgraph Tasks["Celery Async Tasks"]
        BatchAuditTask["batch_degree_audit\n(scheduled: semester end)"]
        StandingEvalTask["evaluate_academic_standing\n(scheduled: after grade publish)"]
        CertGenTask["generate_graduation_certificate\n(default queue)"]
    end

    subgraph Infra["Infrastructure"]
        DB[("PostgreSQL")]
        FileStore["File Storage\n(Local / S3)"]
        PDFGen["PDF Generator\n(WeasyPrint)"]
    end

    GradAuditViewSet --> DegreeAuditEngine
    GradViewSet --> GraduationSvc
    StandingViewSet --> AcademicStandingSvc
    TransferViewSet --> TransferCreditSvc
    DegreeAuditEngine --> AuditModel --> DB
    GraduationSvc --> DegreeAuditEngine
    GraduationSvc --> GradModel --> DB
    GraduationSvc --> CertGenTask --> PDFGen --> FileStore
    AcademicStandingSvc --> StandingModel --> DB
    TransferCreditSvc --> TransferModel --> DB
    BatchAuditTask --> DegreeAuditEngine
    StandingEvalTask --> AcademicStandingSvc
```

---

## 7. HR & Recruitment Components

```mermaid
flowchart LR
    subgraph API["HR & Recruitment API Layer"]
        RecruitmentViewSet["RecruitmentViewSet\nPOST create-posting\nGET applications\nPOST shortlist"]
        OnboardingViewSet["OnboardingViewSet\nPOST initiate\nGET checklist\nPOST complete-step"]
        DeptViewSet["DepartmentViewSet\nCRUD departments\nGET faculty-list"]
    end

    subgraph Services["Business Logic Services"]
        RecruitmentSvc["RecruitmentService\ncreate_posting()\nreview_application()\nschedule_interview()\nextend_offer()"]
        ApplicantTracker["ApplicantTracker\ntrack_status()\nrank_candidates()\ngenerate_shortlist()"]
        OnboardingSvc["OnboardingService\ninitiate_onboarding()\nassign_tasks()\ntrack_completion()\nprovision_access()"]
        DeptAdminSvc["DepartmentAdminService\nmanage_programs()\nassign_faculty()\nreview_curriculum()"]
    end

    subgraph Models["Django ORM Models"]
        JobModel["JobPosting\nApplication\nInterviewSchedule\nOffer"]
        OnboardModel["OnboardingPlan\nOnboardingTask\nTaskCompletion"]
        DeptModel["Department\nProgram\nCurriculumReview"]
    end

    subgraph Tasks["Celery Async Tasks"]
        NotifyApplicantTask["notify_applicant_status\n(default queue)"]
        OnboardReminderTask["send_onboarding_reminder\n(scheduled: daily)"]
        PostingExpiryTask["check_posting_expiry\n(scheduled: nightly)"]
    end

    subgraph Infra["Infrastructure"]
        DB[("PostgreSQL")]
        EmailSvc["Email Service\n(SMTP)"]
    end

    RecruitmentViewSet --> RecruitmentSvc
    OnboardingViewSet --> OnboardingSvc
    DeptViewSet --> DeptAdminSvc
    RecruitmentSvc --> ApplicantTracker
    RecruitmentSvc --> JobModel --> DB
    ApplicantTracker --> JobModel
    RecruitmentSvc --> NotifyApplicantTask --> EmailSvc
    OnboardingSvc --> OnboardModel --> DB
    OnboardReminderTask --> OnboardingSvc
    DeptAdminSvc --> DeptModel --> DB
    PostingExpiryTask --> RecruitmentSvc
```

---

## 8. Facility & Scheduling Components

```mermaid
flowchart LR
    subgraph API["Facility API Layer"]
        RoomViewSet["RoomViewSet\nCRUD rooms\nGET availability"]
        BookingViewSet["BookingViewSet\nPOST reserve\nDELETE cancel\nGET schedule"]
        MaintenanceViewSet["MaintenanceViewSet\nPOST request\nPOST resolve"]
    end

    subgraph Services["Business Logic Services"]
        RoomBookingSvc["RoomBookingService\nreserve_room()\ncancel_booking()\ncheck_availability()"]
        FacilityMgr["FacilityManager\nregister_facility()\nupdate_capacity()\ntrack_utilization()"]
        ConflictDetector["ScheduleConflictDetector\ncheck_conflicts()\nresolve_overlap()\nvalidate_booking()"]
        MaintenanceSvc["MaintenanceService\nsubmit_request()\nassign_crew()\nmark_resolved()"]
    end

    subgraph Models["Django ORM Models"]
        RoomModel["Room\nFacility\nRoomFeature"]
        BookingModel["Booking\nRecurringSchedule\nBookingConflict"]
        MaintModel["MaintenanceRequest\nMaintenanceLog"]
    end

    subgraph Tasks["Celery Async Tasks"]
        BookingReminderTask["send_booking_reminder\n(scheduled: 1hr before)"]
        UtilizationReportTask["generate_utilization_report\n(scheduled: weekly)"]
    end

    subgraph Infra["Infrastructure"]
        DB[("PostgreSQL")]
        Redis[("Redis\nAvailability Cache")]
    end

    RoomViewSet --> RoomBookingSvc
    BookingViewSet --> RoomBookingSvc
    MaintenanceViewSet --> MaintenanceSvc
    RoomBookingSvc --> ConflictDetector
    RoomBookingSvc --> BookingModel --> DB
    RoomBookingSvc --> Redis
    FacilityMgr --> RoomModel --> DB
    ConflictDetector --> BookingModel
    MaintenanceSvc --> MaintModel --> DB
    BookingReminderTask --> RoomBookingSvc
    UtilizationReportTask --> FacilityMgr
```

---

## 9. Scholarship & Aid Components

```mermaid
flowchart LR
    subgraph API["Scholarship API Layer"]
        ScholarshipViewSet["ScholarshipViewSet\nCRUD scholarships\nGET eligible-students"]
        AidAppViewSet["AidApplicationViewSet\nPOST apply\nGET status\nPOST review"]
        DisbursementViewSet["DisbursementViewSet\nPOST disburse\nGET history"]
    end

    subgraph Services["Business Logic Services"]
        ScholarshipSvc["ScholarshipService\ncreate_scholarship()\nevaluate_eligibility()\naward_scholarship()"]
        AidDisbursementEngine["AidDisbursementEngine\ncalculate_award()\nprocess_disbursement()\ngenerate_letter()"]
        StackingValidator["StackingValidator\nvalidate_stacking_rules()\ncheck_max_aid_cap()\ndetect_over_award()"]
    end

    subgraph Models["Django ORM Models"]
        ScholarshipModel["Scholarship\nEligibilityCriteria\nScholarshipFund"]
        AidAppModel["AidApplication\nAidAward\nAidDocument"]
        DisbursementModel["Disbursement\nDisbursementSchedule"]
    end

    subgraph Tasks["Celery Async Tasks"]
        EligibilityCheckTask["batch_eligibility_check\n(scheduled: semester start)"]
        DisbursementTask["process_scheduled_disbursements\n(scheduled: monthly)"]
        AidNotifyTask["notify_aid_decision\n(default queue)"]
    end

    subgraph Infra["Infrastructure"]
        DB[("PostgreSQL")]
        FinanceSvc["Finance Container\n(Invoice adjustment)"]
    end

    ScholarshipViewSet --> ScholarshipSvc
    AidAppViewSet --> ScholarshipSvc
    DisbursementViewSet --> AidDisbursementEngine
    ScholarshipSvc --> StackingValidator
    ScholarshipSvc --> ScholarshipModel --> DB
    ScholarshipSvc --> AidAppModel --> DB
    AidDisbursementEngine --> DisbursementModel --> DB
    AidDisbursementEngine --> FinanceSvc
    StackingValidator --> ScholarshipModel
    EligibilityCheckTask --> ScholarshipSvc
    DisbursementTask --> AidDisbursementEngine
    AidNotifyTask --> ScholarshipSvc
```

---

## 10. Discipline & Appeals Components

```mermaid
flowchart LR
    subgraph API["Discipline & Appeals API Layer"]
        DisciplineViewSet["DisciplineViewSet\nPOST report-incident\nGET cases\nPOST resolve"]
        HearingViewSet["HearingViewSet\nPOST schedule\nPOST record-outcome"]
        AppealViewSet["AppealViewSet\nPOST submit-appeal\nGET status\nPOST decide"]
        GradeAppealViewSet["GradeAppealViewSet\nPOST submit\nGET status\nPOST resolve"]
    end

    subgraph Services["Business Logic Services"]
        DisciplineSvc["DisciplineService\nreport_incident()\ninvestigate()\napply_sanction()"]
        HearingMgr["HearingManager\nschedule_hearing()\nrecord_testimony()\nrecord_outcome()"]
        AppealProcessor["AppealProcessor\nsubmit_appeal()\nassign_reviewer()\nprocess_decision()"]
        GradeAppealSvc["GradeAppealService\nsubmit_grade_appeal()\nreview_evidence()\napply_grade_change()"]
    end

    subgraph Models["Django ORM Models"]
        IncidentModel["DisciplineIncident\nInvestigation\nSanction"]
        HearingModel["Hearing\nHearingParticipant\nHearingOutcome"]
        AppealModel["Appeal\nAppealReview\nAppealDecision"]
        GradeAppealModel["GradeAppeal\nGradeEvidence\nGradeChange"]
    end

    subgraph Tasks["Celery Async Tasks"]
        HearingNotifyTask["notify_hearing_schedule\n(default queue)"]
        AppealDeadlineTask["check_appeal_deadlines\n(scheduled: daily)"]
        SanctionEnforceTask["enforce_active_sanctions\n(scheduled: daily)"]
    end

    subgraph Infra["Infrastructure"]
        DB[("PostgreSQL")]
        NotifSvc["Notification Container"]
    end

    DisciplineViewSet --> DisciplineSvc
    HearingViewSet --> HearingMgr
    AppealViewSet --> AppealProcessor
    GradeAppealViewSet --> GradeAppealSvc
    DisciplineSvc --> HearingMgr
    DisciplineSvc --> IncidentModel --> DB
    HearingMgr --> HearingModel --> DB
    HearingMgr --> HearingNotifyTask --> NotifSvc
    AppealProcessor --> AppealModel --> DB
    AppealProcessor --> DisciplineSvc
    GradeAppealSvc --> GradeAppealModel --> DB
    AppealDeadlineTask --> AppealProcessor
    SanctionEnforceTask --> DisciplineSvc
```
