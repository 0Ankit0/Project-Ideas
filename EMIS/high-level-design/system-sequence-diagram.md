# System Sequence Diagrams — Education Management Information System

This document captures the six primary cross-module system sequences that span multiple EMIS domains. Each sequence shows all participating actors, services, and external systems — covering the happy path and key error branches — along with the audit events emitted at critical steps.

---

## 1. Student Admissions Workflow

Covers the full lifecycle from online application submission through document verification, merit list generation, acceptance, and formal student enrollment.

```mermaid
sequenceDiagram
    autonumber
    actor Applicant
    actor AdmissionsOfficer
    participant Portal as Applicant Portal
    participant AdmSvc as Admissions Service
    participant DocSvc as Document Verification Service
    participant NotifSvc as Notification Service
    participant StudentSvc as Student Service
    participant UserSvc as User Service
    participant FinanceSvc as Finance Service
    participant AuditLog as Audit Log

    Applicant->>Portal: Fill application form + upload documents
    Portal->>AdmSvc: POST /admissions/applications/\n{program_id, personal_details, documents[]}
    AdmSvc->>AdmSvc: Validate application window open\n(BR-ADM-001)
    alt Application window closed
        AdmSvc-->>Portal: 422 APPLICATION_WINDOW_CLOSED
        Portal-->>Applicant: "Applications are closed for this intake"
    else Window open
        AdmSvc->>AuditLog: APPLICATION_SUBMITTED {application_id, applicant_id}
        AdmSvc->>NotifSvc: application.submitted.v1 → send confirmation email
        NotifSvc-->>Applicant: Email: "Application received — ref: APP-2024-00234"
        AdmSvc-->>Portal: 201 {application_id, status: SUBMITTED}
        Portal-->>Applicant: "Application submitted successfully"
    end

    Note over AdmissionsOfficer,DocSvc: Admissions officer reviews application

    AdmissionsOfficer->>Portal: Open application APP-2024-00234
    Portal->>AdmSvc: GET /admissions/applications/{id}/
    AdmSvc-->>Portal: Application details + document list
    Portal-->>AdmissionsOfficer: Show application with document previews

    AdmissionsOfficer->>DocSvc: Verify each document (identity, transcripts, photos)
    DocSvc->>AuditLog: DOCUMENT_VERIFIED {document_id, verified_by_id}
    DocSvc-->>AdmissionsOfficer: All documents verified

    AdmissionsOfficer->>AdmSvc: PATCH /admissions/applications/{id}/status/\n{status: SHORTLISTED}
    AdmSvc->>AuditLog: APPLICATION_STATUS_CHANGED {old: SUBMITTED, new: SHORTLISTED}
    AdmSvc->>NotifSvc: application.status_changed.v1 → shortlisting email
    NotifSvc-->>Applicant: Email: "Your application has been shortlisted"

    Note over AdmissionsOfficer,AdmSvc: Merit list generation

    AdmissionsOfficer->>AdmSvc: POST /admissions/merit-lists/generate/\n{program_id, intake_year, criteria}
    AdmSvc->>AdmSvc: Rank shortlisted applicants by configured criteria\n(test score weight, academic grade weight)
    AdmSvc->>AuditLog: MERIT_LIST_GENERATED {merit_list_id, candidate_count}
    AdmSvc-->>AdmissionsOfficer: Merit list preview with rankings

    AdmissionsOfficer->>AdmSvc: POST /admissions/merit-lists/{id}/publish/
    AdmSvc->>NotifSvc: merit_list.published.v1 → bulk acceptance emails
    loop For each accepted applicant
        NotifSvc-->>Applicant: Email: "Congratulations! Offer letter + enrollment deadline"
    end

    Note over Applicant,StudentSvc: Applicant accepts and completes enrollment

    Applicant->>Portal: Pay admission fee → enrollment confirmed
    AdmSvc->>StudentSvc: admissions.enrollment.initiated.v1
    StudentSvc->>UserSvc: Create student user account\n{email, temporary_password, role: STUDENT}
    UserSvc-->>StudentSvc: {user_id, credentials}
    StudentSvc->>StudentSvc: Create Student profile\n{student_id: STU-2024-00234, program, batch}
    StudentSvc->>FinanceSvc: Generate initial semester fee invoice
    FinanceSvc-->>StudentSvc: Invoice created
    StudentSvc->>NotifSvc: Send portal credentials email
    NotifSvc-->>Applicant: Email: "Welcome! Your student portal login: ..."
```

---

## 2. Course Registration Workflow

Covers the complete course registration flow with prerequisite validation, seat availability check, timetable conflict detection, and fee invoice update.

```mermaid
sequenceDiagram
    autonumber
    actor Student
    participant Portal as Student Portal
    participant EnrollSvc as Enrollment Service
    participant PrereqChk as Prerequisite Validator
    participant CapChk as Capacity Checker
    participant TimetableChk as Timetable Conflict Detector
    participant FinanceSvc as Finance Service
    participant NotifSvc as Notification Service
    participant DB as PostgreSQL

    Student->>Portal: Navigate to Course Registration
    Portal->>EnrollSvc: GET /api/v1/courses/available/?semester={id}&student={id}
    EnrollSvc->>DB: Fetch available sections filtered by student's program and semester
    DB-->>EnrollSvc: Available sections with seat counts
    EnrollSvc-->>Portal: Course catalog with availability indicators
    Portal-->>Student: Show course list with filters

    Student->>Portal: Select CS301 — Section A, click "Register"
    Portal->>EnrollSvc: POST /api/v1/enrollments/\n{section_id, semester_id, idempotency_key}

    EnrollSvc->>EnrollSvc: Check registration window open (BR-ENROLL-001)
    alt Registration window closed
        EnrollSvc-->>Portal: 422 REGISTRATION_WINDOW_CLOSED
        Portal-->>Student: "Registration period has closed"
    end

    EnrollSvc->>EnrollSvc: Check financial hold (BR-ENROLL-006)
    alt Student has financial hold
        EnrollSvc-->>Portal: 422 FINANCIAL_HOLD_ACTIVE
        Portal-->>Student: "Clear outstanding balance to register"
    end

    EnrollSvc->>PrereqChk: check_prerequisites(student_id, course_id)
    PrereqChk->>DB: SELECT completed course IDs with passing grade
    DB-->>PrereqChk: Completed courses
    PrereqChk->>PrereqChk: Diff against course prerequisites
    alt Prerequisites not met
        PrereqChk-->>EnrollSvc: PREREQUISITES_NOT_MET {missing: [CS201]}
        EnrollSvc-->>Portal: 422 {code: PREREQUISITES_NOT_MET, missing_courses: ["CS201"]}
        Portal-->>Student: "Complete CS201 before enrolling in CS301"
    else Prerequisites satisfied
        PrereqChk-->>EnrollSvc: OK
    end

    EnrollSvc->>CapChk: check_capacity(section_id)
    CapChk->>DB: SELECT FOR UPDATE section — check seats_used < max_enrollment
    alt No seats available
        CapChk-->>EnrollSvc: COURSE_CAPACITY_EXCEEDED
        EnrollSvc-->>Portal: 409 COURSE_CAPACITY_EXCEEDED
        Portal-->>Student: "Section A is full. Other sections available."
    else Seats available
        CapChk-->>EnrollSvc: OK {available_seats: 3}
    end

    EnrollSvc->>TimetableChk: check_conflict(student_id, section_id, semester_id)
    TimetableChk->>DB: Fetch student's enrolled time slots
    TimetableChk->>TimetableChk: Overlap check with new section
    alt Conflict detected
        TimetableChk-->>EnrollSvc: TIMETABLE_CONFLICT {conflicting_section: "CS201-A"}
        EnrollSvc-->>Portal: 409 TIMETABLE_CONFLICT
        Portal-->>Student: "Schedule conflict with CS201-A (Mon 10:00-11:30)"
    else No conflict
        TimetableChk-->>EnrollSvc: OK
    end

    Note over EnrollSvc,DB: All checks passed — commit atomically

    EnrollSvc->>DB: BEGIN TRANSACTION
    EnrollSvc->>DB: INSERT enrollment {student_id, section_id, status: ACTIVE}
    EnrollSvc->>DB: UPDATE section SET seats_used = seats_used + 1
    EnrollSvc->>DB: COMMIT

    EnrollSvc->>FinanceSvc: Async: update_invoice_for_new_enrollment(student_id, course_id)
    FinanceSvc->>DB: Add course-based fee line item to semester invoice
    EnrollSvc->>NotifSvc: Async: send_enrollment_confirmation(enrollment_id)
    NotifSvc-->>Student: Email: "Enrolled in CS301-A — Mon/Wed 10:00-11:30, Room 205"

    EnrollSvc-->>Portal: 201 {enrollment_id, section, schedule, credit_hours: 3}
    Portal-->>Student: "Successfully registered for CS301 — Section A"
```

---

## 3. End-of-Semester Grade Processing

Covers faculty grade entry, department head review, grade lock, GPA recalculation, transcript update, and notifications to students and parents.

```mermaid
sequenceDiagram
    autonumber
    actor Faculty
    actor DeptHead
    actor Student
    actor Parent
    participant Portal as Faculty Portal
    participant GradeSvc as Grade Service
    participant ExamSvc as Exam Service
    participant StudentSvc as Student Service
    participant NotifSvc as Notification Service
    participant AuditLog as Audit Log

    Note over Faculty,ExamSvc: Grading window opens (triggered by Exam Controller)

    ExamSvc->>ExamSvc: Open grading window for exam
    ExamSvc->>NotifSvc: Notify faculty: grading window open, deadline in 5 days
    NotifSvc-->>Faculty: Email: "Grade submission open for CS301 — due {date}"

    Faculty->>Portal: Navigate to Grade Entry → CS301 Final Exam
    Portal->>GradeSvc: GET /api/v1/grades/?exam_id={id}&section_id={id}
    GradeSvc-->>Portal: Student roster with empty grade fields
    Portal-->>Faculty: Grade entry form with student list

    loop For each enrolled student
        Faculty->>Portal: Enter marks_obtained for student
    end

    Faculty->>Portal: Click "Submit Grades"
    Portal->>GradeSvc: POST /api/v1/grades/bulk/\n{exam_id, grades: [{enrollment_id, marks_obtained}]}
    GradeSvc->>GradeSvc: Check grading window is open (BR-ACAD-001)
    GradeSvc->>GradeSvc: Compute letter_grade and grade_points for each entry
    GradeSvc->>AuditLog: GRADES_SUBMITTED {exam_id, faculty_id, student_count}
    GradeSvc-->>Portal: 201 {grades_submitted: 45, status: SUBMITTED}
    Portal-->>Faculty: "Grades submitted. Awaiting department head review."

    Note over DeptHead,GradeSvc: Department head reviews and publishes grades

    GradeSvc->>NotifSvc: Notify department head: grades ready for review
    NotifSvc-->>DeptHead: Email: "CS301 Final grades submitted by Dr. Ahmed — review required"

    DeptHead->>Portal: Review grade distribution, check for anomalies
    DeptHead->>GradeSvc: POST /api/v1/grades/publish/?exam_id={id}
    GradeSvc->>GradeSvc: Lock grades (status → PUBLISHED)
    GradeSvc->>AuditLog: GRADES_PUBLISHED {exam_id, published_by_id: DeptHead}

    GradeSvc->>StudentSvc: Emit academic.grade.published.v1 for each grade
    StudentSvc->>StudentSvc: Recalculate semester GPA for each affected student
    StudentSvc->>StudentSvc: Recalculate CGPA
    StudentSvc->>StudentSvc: Update transcript record

    GradeSvc->>NotifSvc: Send grade notification to students
    loop For each student
        NotifSvc-->>Student: Email/In-app: "CS301 Final grade published — Login to view"
    end

    Note over Student,Parent: Students and parents view results

    Student->>Portal: View grades and updated GPA
    Portal->>GradeSvc: GET /api/v1/grades/?enrollment_id={id}
    GradeSvc-->>Portal: Published grade + letter grade + GPA impact
    Portal-->>Student: Shows CS301: B+ (3.3/4.0), Semester GPA: 3.42

    alt Parent portal enabled
        NotifSvc-->>Parent: Email: "Grade report available for {child_student_id}"
        Parent->>Portal: View child's semester report
    end

    alt Student disputes a grade
        Student->>Portal: Submit grade appeal for CS301
        GradeSvc->>GradeSvc: Create GradeDispute record (grade remains PUBLISHED, not changed)
        GradeSvc->>NotifSvc: Notify faculty and dept head of dispute
    end
```

---

## 4. Fee Payment Workflow

Covers invoice viewing, payment gateway initiation, confirmation via webhook, receipt generation, and financial hold release.

```mermaid
sequenceDiagram
    autonumber
    actor Student
    participant Portal as Student Portal
    participant PaymentSvc as Payment Service
    participant InvoiceSvc as Invoice Service
    participant GWAdapter as Payment Gateway Adapter
    participant Gateway as External Gateway\n(Stripe / Razorpay)
    participant NotifSvc as Notification Service
    participant HoldSvc as Academic Hold Service
    participant AuditLog as Audit Log

    Student->>Portal: Navigate to Fee → View Invoices
    Portal->>InvoiceSvc: GET /api/v1/invoices/?student_id={id}&status=UNPAID
    InvoiceSvc-->>Portal: [{invoice_id, invoice_number, total_amount, due_date, status: ISSUED}]
    Portal-->>Student: Shows INV-2024-001234 — PKR 45,000 — Due 15 Jan

    Student->>Portal: Click "Pay Now"
    Portal->>PaymentSvc: POST /api/v1/payments/initiate-gateway/\n{invoice_id, gateway: "stripe", idempotency_key}

    PaymentSvc->>InvoiceSvc: Verify invoice is UNPAID and belongs to student
    InvoiceSvc-->>PaymentSvc: Invoice valid

    PaymentSvc->>GWAdapter: create_checkout_session(amount, currency, invoice_id, return_url)
    GWAdapter->>Gateway: POST /v1/checkout/sessions

    alt Gateway unavailable
        Gateway-->>GWAdapter: 503 Service Unavailable
        GWAdapter-->>PaymentSvc: GatewayUnavailableError
        PaymentSvc-->>Portal: 503 {code: GATEWAY_UNAVAILABLE, retry_after: 30}
        Portal-->>Student: "Payment gateway temporarily unavailable. Try again in 30 seconds."
    else Session created
        Gateway-->>GWAdapter: {session_id, checkout_url}
        GWAdapter-->>PaymentSvc: {session_id, checkout_url}
        PaymentSvc->>AuditLog: PAYMENT_INITIATED {invoice_id, session_id, amount}
        PaymentSvc-->>Portal: 200 {checkout_url}
        Portal-->>Student: Redirect to Stripe/Razorpay checkout page
    end

    Student->>Gateway: Complete card payment
    Gateway->>PaymentSvc: POST /api/v1/payments/webhook/\n{event: payment_intent.succeeded, session_id}
    PaymentSvc->>PaymentSvc: Verify webhook signature

    alt Invalid webhook signature
        PaymentSvc-->>Gateway: 400 Reject
    else Valid signature — check idempotency
        PaymentSvc->>PaymentSvc: Was this session_id already processed?
        alt Duplicate webhook
            PaymentSvc-->>Gateway: 200 OK (idempotent)
        else First delivery
            PaymentSvc->>InvoiceSvc: Confirm payment\n{invoice_id, gateway_txn_id, amount}
            InvoiceSvc->>InvoiceSvc: Mark invoice PAID, record amount_paid
            InvoiceSvc->>AuditLog: INVOICE_PAID {invoice_id, amount, gateway_txn_id}

            PaymentSvc->>NotifSvc: Async: generate_receipt_and_email(payment_transaction_id)
            PaymentSvc->>HoldSvc: Async: check_and_release_financial_hold(student_id)
            PaymentSvc-->>Gateway: 200 OK
        end
    end

    Note over NotifSvc,Student: Async: Receipt generated and emailed

    NotifSvc->>NotifSvc: Generate PDF receipt (WeasyPrint)
    NotifSvc->>NotifSvc: Store PDF to file storage
    NotifSvc-->>Student: Email: "Payment confirmed — Receipt attached\nINV-2024-001234 — PKR 45,000"

    Portal-->>Student: Payment success page with receipt download link
```

---

## 5. LMS Assignment Lifecycle

Covers assignment creation by faculty, student submissions, plagiarism check, grading, and grade sync with the exam module.

```mermaid
sequenceDiagram
    autonumber
    actor Faculty
    actor Student
    participant LMSPortal as LMS Portal
    participant AssignSvc as Assignment Service
    participant FileSvc as File Storage Service
    participant PlagSvc as Plagiarism Checker\n(async)
    participant GradeSvc as Grade Service
    participant NotifSvc as Notification Service

    Faculty->>LMSPortal: Create Assignment for CS301
    LMSPortal->>AssignSvc: POST /api/v1/lms/assignments/\n{section_id, title, description, due_datetime,\n max_marks, late_submission_days: 2, late_penalty: 10%}
    AssignSvc->>AssignSvc: Save assignment with status DRAFT
    AssignSvc-->>LMSPortal: 201 {assignment_id}
    Faculty->>LMSPortal: Click "Publish Assignment"
    AssignSvc->>AssignSvc: Set status PUBLISHED
    AssignSvc->>NotifSvc: Async: notify all enrolled students
    NotifSvc-->>Student: Email/In-app: "New assignment: CS301 Project — Due {due_datetime}"
    LMSPortal-->>Faculty: "Assignment published and students notified"

    Note over Student,AssignSvc: Student submits before deadline

    Student->>LMSPortal: Open CS301 assignment
    LMSPortal->>AssignSvc: GET /api/v1/lms/assignments/{id}/
    AssignSvc-->>LMSPortal: Assignment details, submission status: NOT_SUBMITTED
    Student->>LMSPortal: Upload project files (PDF + ZIP)
    LMSPortal->>FileSvc: Upload files with size and type validation
    FileSvc-->>LMSPortal: {file_ids, storage_paths}
    Student->>LMSPortal: Click "Submit"
    LMSPortal->>AssignSvc: POST /api/v1/lms/submissions/\n{assignment_id, file_ids, idempotency_key}
    AssignSvc->>AssignSvc: Check deadline — is_late = (now > due_datetime)
    alt After late window (no more submissions)
        AssignSvc-->>LMSPortal: 422 ASSIGNMENT_SUBMISSION_CLOSED
        LMSPortal-->>Student: "Submission window has closed for this assignment"
    else Before or within late window
        AssignSvc->>AssignSvc: Create submission {status: SUBMITTED, is_late: false}
        AssignSvc->>PlagSvc: Async: run_plagiarism_check(submission_id)
        AssignSvc->>NotifSvc: Async: submission_confirmation_email(student_id)
        NotifSvc-->>Student: Email: "Submission confirmed — CS301 Project"
        AssignSvc-->>LMSPortal: 201 {submission_id, submitted_at, is_late: false}
        LMSPortal-->>Student: "Submitted successfully"
    end

    Note over Faculty,GradeSvc: Faculty grades submission

    Faculty->>LMSPortal: View all submissions for CS301 Project
    LMSPortal->>AssignSvc: GET /api/v1/lms/assignments/{id}/submissions/
    AssignSvc-->>LMSPortal: Submission list with plagiarism flags
    Faculty->>LMSPortal: Open student's submission, download files, enter grade
    LMSPortal->>AssignSvc: PATCH /api/v1/lms/submissions/{id}/grade/\n{marks_obtained, feedback}
    AssignSvc->>AssignSvc: Apply late penalty if is_late\n(marks_obtained * (1 - penalty_rate))
    AssignSvc->>GradeSvc: Sync grade to exam module\n{enrollment_id, exam_type: ASSIGNMENT, marks_obtained}
    GradeSvc->>GradeSvc: Update grade record
    AssignSvc->>NotifSvc: Async: grade_feedback_notification(student_id)
    NotifSvc-->>Student: Email/In-app: "CS301 Project graded — Login to view feedback"
    AssignSvc-->>LMSPortal: 200 {submission_id, marks_obtained, letter_grade}
    LMSPortal-->>Faculty: Grade saved and student notified
```

---

## 6. Attendance-to-Academic-Hold Workflow

Covers daily attendance marking, cumulative threshold monitoring, warning issuance, and automatic academic hold enforcement.

```mermaid
sequenceDiagram
    autonumber
    actor Faculty
    actor Student
    actor DeptHead
    participant AttendPortal as Attendance Portal
    participant AttendSvc as Attendance Service
    participant ThresholdChk as Threshold Monitor\n(Celery Beat - Daily)
    participant HoldSvc as Academic Hold Service
    participant NotifSvc as Notification Service
    participant EnrollSvc as Enrollment Service
    participant AuditLog as Audit Log

    Note over Faculty,AttendSvc: Faculty marks attendance after each class

    Faculty->>AttendPortal: Open CS301 — Today's class roster
    AttendPortal->>AttendSvc: GET /api/v1/attendance/sessions/?section={id}&date=today
    AttendSvc-->>AttendPortal: Class roster with enrolled students
    Faculty->>AttendPortal: Mark each student: Present / Absent / Late
    Faculty->>AttendPortal: Submit attendance
    AttendPortal->>AttendSvc: POST /api/v1/attendance/bulk-mark/\n{session_id, records: [{student_id, status}]}
    AttendSvc->>AuditLog: ATTENDANCE_MARKED {section_id, date, faculty_id, counts}
    AttendSvc-->>AttendPortal: 201 {session_id, marked_count: 45}
    AttendPortal-->>Faculty: "Attendance recorded"

    Note over ThresholdChk: Nightly batch job (00:30 UTC daily)

    ThresholdChk->>AttendSvc: Compute attendance percentage for each student/section pair
    AttendSvc->>AttendSvc: attendance_pct = classes_attended / total_classes_held * 100

    loop For each student with attendance_pct below threshold (75%)
        alt First breach — below 75%
            AttendSvc->>AttendSvc: Record WARNING status in AttendanceAlert
            AttendSvc->>NotifSvc: academic.attendance.threshold_breached.v1 (WARNING)
            NotifSvc-->>Student: Email: "Attendance warning: CS301 — 68.5% (below 75% threshold)"
            NotifSvc-->>DeptHead: Email: "Attendance warning issued to {student_id} in CS301"
        else Second consecutive breach — below 65%
            AttendSvc->>HoldSvc: Create academic hold for student/section
            HoldSvc->>EnrollSvc: Flag enrollment: exam_registration_blocked = True
            HoldSvc->>AuditLog: ACADEMIC_HOLD_APPLIED {student_id, section_id, attendance_pct}
            AttendSvc->>NotifSvc: academic.attendance.threshold_breached.v1 (HOLD)
            NotifSvc-->>Student: Email: "ACADEMIC HOLD: CS301 exam registration blocked (54.2% attendance). Contact department head."
            NotifSvc-->>DeptHead: Email: "Academic hold applied to {student_id} — CS301"
        end
    end

    Note over Student,DeptHead: Student resolves hold

    Student->>DeptHead: Submit leave documents / medical certificate
    DeptHead->>AttendPortal: Review case, approve attendance exception
    DeptHead->>AttendSvc: POST /api/v1/attendance/exceptions/\n{student_id, section_id, approved_classes, reason}
    AttendSvc->>AttendSvc: Recalculate attendance with approved exception
    AttendSvc->>AuditLog: ATTENDANCE_EXCEPTION_GRANTED {student_id, section_id, approved_by_id}

    alt Attendance now above threshold
        AttendSvc->>HoldSvc: Release academic hold
        HoldSvc->>EnrollSvc: Clear exam_registration_blocked flag
        HoldSvc->>AuditLog: ACADEMIC_HOLD_RELEASED {student_id, released_by: DeptHead}
        HoldSvc->>NotifSvc: Notify student: hold lifted
        NotifSvc-->>Student: Email: "Academic hold lifted — CS301 exam registration is now available"
    end
```
