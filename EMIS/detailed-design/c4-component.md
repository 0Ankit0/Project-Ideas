# C4 Component Diagram — Education Management Information System

C4 Level 3 component diagrams for the four primary EMIS containers, showing internal components, their responsibilities, and inbound/outbound communication paths.

---

## 1. Academic Core Container

```mermaid
C4Component
    title C4 Component — Academic Core Container

    Container_Boundary(academic, "Academic Core (Django API)") {
        Component(admissions_api, "Admissions API", "DRF ViewSet", "Handles application submission, document upload, merit-list generation, and offer dispatch")
        Component(enrollment_svc, "Enrollment Service", "Django Service Layer", "Processes course registration, pre-requisite checks, seat-limit enforcement, and add-drop window logic")
        Component(curriculum_mgr, "Curriculum Manager", "Django Service Layer", "Manages programs, courses, sections, and semester configurations")
        Component(timetable_engine, "Timetable Engine", "Django + Celery Task", "Generates and validates conflict-free class schedules; exposes read-only API for student portal")
        Component(attendance_tracker, "Attendance Tracker", "DRF ViewSet + Celery", "Records daily attendance, sends absence-threshold alerts, and aggregates attendance percentages")
        Component(grade_publisher, "Grade Publisher", "Django Service Layer", "Manages grade submission, publishing workflow, dispute handling, and GPA recalculation")
        Component(exam_scheduler, "Exam Scheduler", "Django Service Layer", "Creates exam definitions, assigns halls, generates admit cards, and enforces grading windows")
        Component(repo_layer, "Academic Repository", "Django ORM", "All DB read/write operations via Django ORM models (Program, Course, Section, Enrollment, Grade, Exam)")
        Component(cache_layer, "Academic Cache", "Redis Client", "Caches programme catalogs, timetable grids, and semester metadata")
        Component(event_emitter, "Domain Event Bus", "Celery + Redis", "Publishes events: enrollment.confirmed, grade.published, attendance.threshold_breached")
    }

    System_Ext(db_postgres, "PostgreSQL 15", "Primary relational data store")
    System_Ext(redis_cache, "Redis 7", "Cache and message broker")
    System_Ext(notification_container, "Notification Container", "Sends emails/SMS/push on academic events")
    System_Ext(finance_container, "Finance Container", "Creates fee invoices on admission/enrollment")
    System_Ext(lms_container, "LMS Container", "Mirrors course sections to learning space")
    System_Ext(storage_s3, "AWS S3", "Stores admit cards, transcripts, uploaded documents")

    Rel(admissions_api, repo_layer, "Reads/writes applications, documents, merit lists")
    Rel(enrollment_svc, repo_layer, "Reads/writes enrollments, checks seat counts")
    Rel(enrollment_svc, cache_layer, "Reads timetable and section data")
    Rel(grade_publisher, repo_layer, "Reads/writes grades, GPA records, disputes")
    Rel(exam_scheduler, repo_layer, "Reads/writes exams, hall assignments")
    Rel(timetable_engine, repo_layer, "Reads/writes timetable slots")
    Rel(attendance_tracker, repo_layer, "Reads/writes attendance records")
    Rel(curriculum_mgr, repo_layer, "Reads/writes programs, courses, sections")
    Rel(cache_layer, redis_cache, "GET / SET / DEL")
    Rel(repo_layer, db_postgres, "SQL queries via Django ORM")
    Rel(event_emitter, redis_cache, "PUBLISH domain events")
    Rel(notification_container, event_emitter, "SUBSCRIBE to academic events")
    Rel(finance_container, enrollment_svc, "Listens enrollment.confirmed → creates invoice")
    Rel(lms_container, curriculum_mgr, "Listens section.created → creates course space")
    Rel(exam_scheduler, storage_s3, "Generates and stores admit card PDF")
    Rel(grade_publisher, storage_s3, "Generates and stores transcript PDF")
```

---

## 2. Finance and Payment Container

```mermaid
C4Component
    title C4 Component — Finance & Payment Container

    Container_Boundary(finance, "Finance & Payment (Django API)") {
        Component(invoice_svc, "Invoice Service", "Django Service Layer", "Generates, versions, and manages fee invoices; applies scholarships; triggers overdue workflow")
        Component(payment_api, "Payment API", "DRF ViewSet", "Exposes checkout initiation, Razorpay/Stripe webhook receiver, and payment-status endpoints")
        Component(gateway_client, "Gateway Client", "Python SDK Wrapper", "Abstracts Razorpay and Stripe SDK calls; handles idempotency keys and retries")
        Component(refund_engine, "Refund Engine", "Django Service Layer", "Processes refund requests, validates eligibility, calls gateway reverse API, updates transaction records")
        Component(scholarship_mgr, "Scholarship Manager", "Django Service Layer", "Evaluates student eligibility, applies discount rules, and creates scholarship ledger entries")
        Component(ledger_svc, "Ledger Service", "Django Service Layer", "Maintains double-entry accounting ledger; reconciles payments with invoices")
        Component(receipt_gen, "Receipt Generator", "Celery Task + WeasyPrint", "Generates signed PDF receipts; stores on S3; emails download link to student")
        Component(hold_enforcer, "Financial Hold Enforcer", "Django Middleware/Signal", "Blocks enrollment API if student has unpaid overdue invoice; releases hold on full payment")
        Component(finance_repo, "Finance Repository", "Django ORM", "All DB operations for invoices, transactions, refunds, scholarships, ledger")
        Component(finance_cache, "Finance Cache", "Redis Client", "Caches fee structures, scholarship rules, and student balance summaries")
    }

    System_Ext(razorpay_gw, "Razorpay", "Payment gateway for Indian market")
    System_Ext(stripe_gw, "Stripe", "Payment gateway for international students")
    System_Ext(db_postgres, "PostgreSQL 15", "Primary relational data store")
    System_Ext(redis_cache, "Redis 7", "Cache and message broker")
    System_Ext(storage_s3, "AWS S3", "Stores receipts and refund vouchers")
    System_Ext(notification_container, "Notification Container", "Sends payment confirmation and overdue notices")
    System_Ext(academic_container, "Academic Core Container", "Listens to fee hold to block enrollment")

    Rel(invoice_svc, finance_repo, "Reads/writes invoices, line items, scholarships")
    Rel(invoice_svc, finance_cache, "Caches fee structure lookups")
    Rel(payment_api, gateway_client, "Initiates checkout session / processes webhook")
    Rel(gateway_client, razorpay_gw, "API calls (create order, capture, refund)")
    Rel(gateway_client, stripe_gw, "API calls (create intent, confirm, refund)")
    Rel(refund_engine, gateway_client, "Calls gateway refund API")
    Rel(refund_engine, finance_repo, "Reads/writes refund records")
    Rel(scholarship_mgr, finance_repo, "Reads scholarship rules, writes discount entries")
    Rel(ledger_svc, finance_repo, "Writes debit/credit ledger entries")
    Rel(receipt_gen, storage_s3, "Uploads receipt PDF")
    Rel(receipt_gen, notification_container, "Triggers payment.receipt_ready event")
    Rel(hold_enforcer, finance_repo, "Reads overdue invoices")
    Rel(hold_enforcer, academic_container, "Raises financial hold flag via API")
    Rel(finance_repo, db_postgres, "SQL queries via Django ORM")
    Rel(finance_cache, redis_cache, "GET / SET / DEL")
```

---

## 3. LMS Container

```mermaid
C4Component
    title C4 Component — LMS Container

    Container_Boundary(lms, "LMS (Django API + HTMX)") {
        Component(course_space_mgr, "Course Space Manager", "Django Service Layer", "Creates and configures learning spaces for each section; manages member access per enrollment status")
        Component(content_api, "Content API", "DRF ViewSet", "Handles upload, versioning, and retrieval of learning materials (PDFs, videos, SCORM packages)")
        Component(assignment_engine, "Assignment Engine", "Django Service Layer + Celery", "Creates assignments, handles submission intake, triggers plagiarism check, manages late penalty rules")
        Component(quiz_engine, "Quiz Engine", "Django Service Layer", "Generates quizzes with time windows, randomized question order, per-attempt attempt limits, and auto-grading")
        Component(discussion_api, "Discussion Board API", "DRF ViewSet", "Threaded discussions; file attachments; faculty pinning; moderation queue")
        Component(progress_tracker, "Progress Tracker", "Django Signal Consumer", "Updates student progress metrics on content view, assignment submission, and quiz completion events")
        Component(plagiarism_client, "Plagiarism Client", "Python HTTP Client", "Submits assignment text to Turnitin API; polls for similarity score; triggers review flag")
        Component(scorm_runtime, "SCORM Runtime", "Django + JS xAPI Receiver", "Handles xAPI (Tin Can) statements from SCORM player; records completion and score")
        Component(lms_repo, "LMS Repository", "Django ORM", "All DB operations for course spaces, materials, assignments, submissions, quizzes, discussions")
        Component(media_store, "Media Store Client", "Boto3 S3 Client", "Streams and stores course videos and large files; generates pre-signed URLs for delivery via CloudFront")
    }

    System_Ext(db_postgres, "PostgreSQL 15", "Primary relational data store")
    System_Ext(redis_cache, "Redis 7", "Cache and message broker")
    System_Ext(storage_s3, "AWS S3 + CloudFront", "Stores and delivers LMS content")
    System_Ext(turnitin_api, "Turnitin API", "Plagiarism detection service")
    System_Ext(academic_container, "Academic Core Container", "Source of enrollment events; validates section membership")
    System_Ext(notification_container, "Notification Container", "Sends assignment-due, grade-posted, and discussion alerts")

    Rel(course_space_mgr, lms_repo, "Reads/writes course spaces and member lists")
    Rel(content_api, lms_repo, "Reads/writes content metadata")
    Rel(content_api, media_store, "Uploads and retrieves media files")
    Rel(assignment_engine, lms_repo, "Reads/writes assignments and submissions")
    Rel(assignment_engine, plagiarism_client, "Submits text on submission intake")
    Rel(plagiarism_client, turnitin_api, "HTTPS API calls")
    Rel(quiz_engine, lms_repo, "Reads/writes quizzes, questions, attempts")
    Rel(discussion_api, lms_repo, "Reads/writes threads and posts")
    Rel(progress_tracker, lms_repo, "Updates progress records")
    Rel(scorm_runtime, lms_repo, "Writes xAPI statements and completion flags")
    Rel(media_store, storage_s3, "PUT/GET object operations")
    Rel(assignment_engine, notification_container, "Fires assignment.due_soon, submission.received events")
    Rel(academic_container, course_space_mgr, "Pushes enrollment.confirmed event")
    Rel(lms_repo, db_postgres, "SQL queries via Django ORM")
```

---

## 4. Notification Container

```mermaid
C4Component
    title C4 Component — Notification Container

    Container_Boundary(notif, "Notification Container (Celery Workers)") {
        Component(event_consumer, "Domain Event Consumer", "Celery Consumer", "Subscribes to all domain events from Redis Pub/Sub; routes to appropriate handler based on event type")
        Component(template_engine, "Template Engine", "Django Templates + Jinja2", "Renders notification content from parameterized templates; supports HTML email and plain-text SMS")
        Component(channel_router, "Channel Router", "Python Strategy Pattern", "Selects delivery channel (email, SMS, push, in-app) based on user preference, event type, and fallback rules")
        Component(email_sender, "Email Sender", "Celery Task + SES Client", "Delivers HTML/text emails via AWS SES; handles bounces and complaints via SNS webhooks")
        Component(sms_sender, "SMS Sender", "Celery Task + Twilio Client", "Sends OTP and transactional SMS via Twilio; implements send-rate throttle and DND filter")
        Component(push_sender, "Push Notification Sender", "Celery Task + FCM Client", "Sends mobile push notifications via Firebase Cloud Messaging; manages device-token registry")
        Component(in_app_store, "In-App Notification Store", "DRF ViewSet + Django ORM", "Persists in-app notifications; exposes read/unread/delete endpoints for student and faculty portals")
        Component(preference_store, "Preference Store", "Django ORM + Cache", "Stores per-user channel preferences and per-event-type opt-in/out settings")
        Component(delivery_log, "Delivery Log", "Django ORM", "Records every notification attempt: channel, status (sent/failed/bounced), timestamp, event_id")
        Component(retry_scheduler, "Retry Scheduler", "Celery Beat + Exponential Backoff", "Re-queues failed notifications with exponential back-off up to 5 retries; escalates to fallback channel after max attempts")
    }

    System_Ext(redis_bus, "Redis 7 Pub/Sub", "Domain event source")
    System_Ext(aws_ses, "AWS SES", "Email delivery")
    System_Ext(twilio, "Twilio", "SMS delivery")
    System_Ext(fcm, "Firebase Cloud Messaging", "Mobile push delivery")
    System_Ext(db_postgres, "PostgreSQL 15", "In-app notifications and delivery log persistence")

    Rel(event_consumer, redis_bus, "SUBSCRIBE *")
    Rel(event_consumer, template_engine, "Passes event context for rendering")
    Rel(event_consumer, channel_router, "Requests channel selection")
    Rel(channel_router, preference_store, "Reads user preferences")
    Rel(channel_router, email_sender, "Routes email notifications")
    Rel(channel_router, sms_sender, "Routes SMS notifications")
    Rel(channel_router, push_sender, "Routes push notifications")
    Rel(channel_router, in_app_store, "Persists in-app messages")
    Rel(email_sender, aws_ses, "SMTP/API calls")
    Rel(sms_sender, twilio, "REST API calls")
    Rel(push_sender, fcm, "HTTP v1 API calls")
    Rel(email_sender, delivery_log, "Records attempt result")
    Rel(sms_sender, delivery_log, "Records attempt result")
    Rel(push_sender, delivery_log, "Records attempt result")
    Rel(retry_scheduler, delivery_log, "Reads failed attempts for retry")
    Rel(delivery_log, db_postgres, "SQL writes via Django ORM")
    Rel(in_app_store, db_postgres, "SQL reads/writes via Django ORM")
```

---

## 5. Graduation & Academic Progress Container

```mermaid
C4Component
    title C4 Component — Graduation & Academic Progress Container

    Container_Boundary(graduation, "Graduation & Academic Progress (Django API)") {
        Component(graduation_api, "Graduation API", "DRF ViewSet", "Handles graduation applications, degree conferral, and certificate generation")
        Component(degree_audit_engine, "Degree Audit Engine", "Django Service Layer", "Evaluates student records against program requirements; identifies deficiencies and generates audit reports")
        Component(academic_standing_svc, "Academic Standing Service", "Django Service Layer", "Evaluates GPA and credit thresholds; applies probation, suspension, or dismissal classifications")
        Component(transfer_credit_svc, "Transfer Credit Service", "Django Service Layer", "Processes transfer credit requests; maps course equivalencies; applies credits to student records")
        Component(cert_generator, "Certificate Generator", "Celery Task + WeasyPrint", "Generates graduation certificates and degree documents in PDF format")
        Component(grad_repo, "Graduation Repository", "Django ORM", "All DB operations for graduation applications, audits, standing records, and transfer credits")
        Component(grad_cache, "Graduation Cache", "Redis Client", "Caches program requirements, equivalency mappings, and audit results")
    }

    System_Ext(db_postgres, "PostgreSQL 15", "Primary relational data store")
    System_Ext(redis_cache, "Redis 7", "Cache and message broker")
    System_Ext(storage_s3, "AWS S3", "Stores graduation certificates and audit reports")
    System_Ext(academic_container, "Academic Core Container", "Source of enrollment and grade data")
    System_Ext(notification_container, "Notification Container", "Sends graduation status and standing alerts")

    Rel(graduation_api, degree_audit_engine, "Triggers audit on graduation application")
    Rel(graduation_api, grad_repo, "Reads/writes graduation applications and conferrals")
    Rel(degree_audit_engine, grad_repo, "Reads program requirements, writes audit results")
    Rel(degree_audit_engine, academic_container, "Reads enrollment and grade records")
    Rel(academic_standing_svc, grad_repo, "Reads/writes standing classifications and probation records")
    Rel(academic_standing_svc, academic_container, "Reads GPA and credit data")
    Rel(transfer_credit_svc, grad_repo, "Reads/writes transfer credits and equivalency mappings")
    Rel(cert_generator, storage_s3, "Uploads generated certificate PDFs")
    Rel(cert_generator, notification_container, "Triggers graduation.certificate_ready event")
    Rel(grad_repo, db_postgres, "SQL queries via Django ORM")
    Rel(grad_cache, redis_cache, "GET / SET / DEL")
```

---

## 6. HR & Recruitment Container

```mermaid
C4Component
    title C4 Component — HR & Recruitment Container

    Container_Boundary(hr_recruitment, "HR & Recruitment (Django API)") {
        Component(recruitment_api, "Recruitment API", "DRF ViewSet", "Handles job posting creation, application intake, interview scheduling, and offer management")
        Component(applicant_tracker, "Applicant Tracker", "Django Service Layer", "Tracks applicant pipeline stages; ranks candidates; generates shortlists based on configurable criteria")
        Component(onboarding_svc, "Onboarding Service", "Django Service Layer", "Manages onboarding checklists, task assignments, document collection, and system access provisioning")
        Component(dept_admin_svc, "Department Admin Service", "Django Service Layer", "Manages department metadata, program assignments, faculty allocation, and curriculum review workflows")
        Component(hr_repo, "HR Repository", "Django ORM", "All DB operations for postings, applications, onboarding plans, and department records")
        Component(hr_cache, "HR Cache", "Redis Client", "Caches department hierarchies and active posting lists")
    }

    System_Ext(db_postgres, "PostgreSQL 15", "Primary relational data store")
    System_Ext(redis_cache, "Redis 7", "Cache and message broker")
    System_Ext(notification_container, "Notification Container", "Sends application status updates and onboarding reminders")
    System_Ext(users_container, "User Management Container", "Provisions accounts for new hires")

    Rel(recruitment_api, applicant_tracker, "Routes applications through pipeline")
    Rel(recruitment_api, hr_repo, "Reads/writes job postings and applications")
    Rel(applicant_tracker, hr_repo, "Reads/writes applicant rankings and shortlists")
    Rel(applicant_tracker, notification_container, "Triggers application.status_changed event")
    Rel(onboarding_svc, hr_repo, "Reads/writes onboarding plans and task completions")
    Rel(onboarding_svc, users_container, "Provisions system accounts on onboarding completion")
    Rel(onboarding_svc, notification_container, "Triggers onboarding.task_due event")
    Rel(dept_admin_svc, hr_repo, "Reads/writes department and program records")
    Rel(hr_repo, db_postgres, "SQL queries via Django ORM")
    Rel(hr_cache, redis_cache, "GET / SET / DEL")
```

---

## 7. Facility Management Container

```mermaid
C4Component
    title C4 Component — Facility Management Container

    Container_Boundary(facility, "Facility Management (Django API)") {
        Component(room_api, "Room & Booking API", "DRF ViewSet", "Handles room registration, availability queries, booking creation, and cancellation")
        Component(room_booking_svc, "Room Booking Service", "Django Service Layer", "Processes room reservations; enforces capacity limits; manages recurring schedules")
        Component(facility_mgr, "Facility Manager", "Django Service Layer", "Registers facilities, tracks utilization metrics, and manages room features and equipment")
        Component(conflict_detector, "Schedule Conflict Detector", "Django Service Layer", "Validates booking requests against existing reservations; detects and prevents double-booking")
        Component(maintenance_svc, "Maintenance Service", "Django Service Layer", "Manages maintenance requests, crew assignments, and resolution tracking")
        Component(facility_repo, "Facility Repository", "Django ORM", "All DB operations for rooms, bookings, facilities, and maintenance records")
        Component(facility_cache, "Facility Cache", "Redis Client", "Caches room availability grids and facility metadata")
    }

    System_Ext(db_postgres, "PostgreSQL 15", "Primary relational data store")
    System_Ext(redis_cache, "Redis 7", "Cache and message broker")
    System_Ext(timetable_container, "Timetable Engine", "Source of class schedule data for conflict detection")
    System_Ext(notification_container, "Notification Container", "Sends booking confirmations and maintenance updates")

    Rel(room_api, room_booking_svc, "Delegates booking operations")
    Rel(room_api, facility_mgr, "Delegates facility CRUD operations")
    Rel(room_booking_svc, conflict_detector, "Validates against existing bookings")
    Rel(room_booking_svc, facility_repo, "Reads/writes bookings and schedules")
    Rel(room_booking_svc, notification_container, "Triggers booking.confirmed event")
    Rel(facility_mgr, facility_repo, "Reads/writes room and facility records")
    Rel(conflict_detector, facility_repo, "Reads existing bookings for overlap check")
    Rel(conflict_detector, timetable_container, "Reads class schedules for conflict detection")
    Rel(maintenance_svc, facility_repo, "Reads/writes maintenance requests and logs")
    Rel(maintenance_svc, notification_container, "Triggers maintenance.resolved event")
    Rel(facility_repo, db_postgres, "SQL queries via Django ORM")
    Rel(facility_cache, redis_cache, "GET / SET / DEL")
```

---

## 8. Scholarship & Financial Aid Container

```mermaid
C4Component
    title C4 Component — Scholarship & Financial Aid Container

    Container_Boundary(scholarship, "Scholarship & Financial Aid (Django API)") {
        Component(scholarship_api, "Scholarship API", "DRF ViewSet", "Handles scholarship CRUD, application intake, eligibility queries, and award management")
        Component(scholarship_svc, "Scholarship Service", "Django Service Layer", "Creates scholarships, evaluates student eligibility against criteria, and manages award lifecycle")
        Component(aid_disbursement_engine, "Aid Disbursement Engine", "Django Service Layer", "Calculates award amounts, processes scheduled disbursements, and generates award letters")
        Component(stacking_validator, "Stacking Validator", "Django Service Layer", "Enforces stacking rules across multiple awards; detects over-award situations; caps total aid at tuition")
        Component(scholarship_repo, "Scholarship Repository", "Django ORM", "All DB operations for scholarships, applications, awards, and disbursement records")
        Component(scholarship_cache, "Scholarship Cache", "Redis Client", "Caches eligibility criteria and fund balances")
    }

    System_Ext(db_postgres, "PostgreSQL 15", "Primary relational data store")
    System_Ext(redis_cache, "Redis 7", "Cache and message broker")
    System_Ext(finance_container, "Finance Container", "Applies scholarship discounts to invoices")
    System_Ext(academic_container, "Academic Core Container", "Source of GPA and enrollment data for eligibility")
    System_Ext(notification_container, "Notification Container", "Sends award notifications and disbursement confirmations")

    Rel(scholarship_api, scholarship_svc, "Delegates scholarship and application operations")
    Rel(scholarship_api, aid_disbursement_engine, "Triggers disbursement processing")
    Rel(scholarship_svc, stacking_validator, "Validates award stacking before approval")
    Rel(scholarship_svc, scholarship_repo, "Reads/writes scholarships, applications, and awards")
    Rel(scholarship_svc, academic_container, "Reads GPA and enrollment status for eligibility")
    Rel(aid_disbursement_engine, scholarship_repo, "Reads/writes disbursement records and schedules")
    Rel(aid_disbursement_engine, finance_container, "Creates invoice discount on disbursement")
    Rel(aid_disbursement_engine, notification_container, "Triggers aid.disbursed event")
    Rel(stacking_validator, scholarship_repo, "Reads all active awards for stacking check")
    Rel(scholarship_repo, db_postgres, "SQL queries via Django ORM")
    Rel(scholarship_cache, redis_cache, "GET / SET / DEL")
```

---

## 9. Discipline & Conduct Container

```mermaid
C4Component
    title C4 Component — Discipline & Conduct Container

    Container_Boundary(discipline, "Discipline & Conduct (Django API)") {
        Component(discipline_api, "Discipline API", "DRF ViewSet", "Handles incident reporting, case management, and sanction tracking")
        Component(discipline_svc, "Discipline Service", "Django Service Layer", "Processes incident reports, manages investigations, and applies sanctions based on conduct policy")
        Component(hearing_mgr, "Hearing Manager", "Django Service Layer", "Schedules disciplinary hearings, records testimony and evidence, and captures hearing outcomes")
        Component(appeal_processor, "Appeal Processor", "Django Service Layer", "Manages appeal submissions, assigns reviewers, and processes appeal decisions with escalation rules")
        Component(grade_appeal_svc, "Grade Appeal Service", "Django Service Layer", "Handles grade dispute submissions, coordinates faculty review, and applies approved grade changes")
        Component(discipline_repo, "Discipline Repository", "Django ORM", "All DB operations for incidents, hearings, sanctions, appeals, and grade disputes")
        Component(discipline_cache, "Discipline Cache", "Redis Client", "Caches active sanctions and appeal deadlines")
    }

    System_Ext(db_postgres, "PostgreSQL 15", "Primary relational data store")
    System_Ext(redis_cache, "Redis 7", "Cache and message broker")
    System_Ext(academic_container, "Academic Core Container", "Reads grades for dispute context; applies grade changes on appeal resolution")
    System_Ext(notification_container, "Notification Container", "Sends hearing notices, sanction letters, and appeal decisions")
    System_Ext(users_container, "User Management Container", "Applies account restrictions for active sanctions")

    Rel(discipline_api, discipline_svc, "Delegates incident and sanction operations")
    Rel(discipline_api, appeal_processor, "Delegates appeal submissions")
    Rel(discipline_api, grade_appeal_svc, "Delegates grade dispute submissions")
    Rel(discipline_svc, hearing_mgr, "Schedules hearing when investigation warrants")
    Rel(discipline_svc, discipline_repo, "Reads/writes incidents, investigations, and sanctions")
    Rel(discipline_svc, users_container, "Applies account restrictions for sanctions")
    Rel(hearing_mgr, discipline_repo, "Reads/writes hearings, participants, and outcomes")
    Rel(hearing_mgr, notification_container, "Triggers hearing.scheduled and hearing.outcome events")
    Rel(appeal_processor, discipline_repo, "Reads/writes appeals, reviews, and decisions")
    Rel(appeal_processor, notification_container, "Triggers appeal.decision event")
    Rel(grade_appeal_svc, discipline_repo, "Reads/writes grade appeals and evidence")
    Rel(grade_appeal_svc, academic_container, "Reads original grade; applies grade change on approval")
    Rel(discipline_repo, db_postgres, "SQL queries via Django ORM")
    Rel(discipline_cache, redis_cache, "GET / SET / DEL")
```
