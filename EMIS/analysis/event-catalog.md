# Event Catalog — Education Management Information System

**Version:** 1.0
**Status:** Approved
**Last Updated:** 2026-01-15

---

## Table of Contents

1. [Contract Conventions](#1-contract-conventions)
2. [Domain Events by Domain](#2-domain-events-by-domain)
3. [Publish and Consumption Sequence](#3-publish-and-consumption-sequence)
4. [Operational SLOs](#4-operational-slos)
5. [Operational Policy Addendum](#5-operational-policy-addendum)

---

## 1. Contract Conventions

### Event Naming
All EMIS domain events follow the pattern: `<domain>.<aggregate>.<action>.v<version>`

Examples:
- `admissions.application.submitted.v1`
- `finance.invoice.payment_received.v1`
- `academic.grade.published.v1`

### Required Metadata (all events)

| Field | Type | Description |
|---|---|---|
| `event_id` | UUID | Unique event identifier; used for deduplication |
| `event_type` | string | Full event name including version |
| `occurred_at` | ISO-8601 UTC | Timestamp when the domain action occurred |
| `correlation_id` | UUID | Traces a chain of causally related events |
| `producer` | string | Django app name that emitted the event (e.g., `admissions`) |
| `schema_version` | string | Semantic version of the event payload schema |
| `actor_id` | UUID | User who triggered the action (null for system-generated) |
| `tenant_context` | object | `{institution_id, institution_name}` |

### Delivery Mode
- All events are dispatched via Celery tasks using an outbox pattern: the event row is inserted into `core_event_outbox` within the same database transaction as the state change.
- A polling relay task reads committed outbox rows and dispatches them to the configured channel (Celery task queue, webhook, or internal signal).
- **Delivery guarantee**: at-least-once. Consumers must implement idempotency checks using `event_id`.

### Ordering Guarantee
- Per-aggregate ordering is maintained within a single Celery task chain.
- No global ordering guarantee across aggregates.
- Events from the same aggregate emitted in the same transaction are ordered by `occurred_at` and a monotonic `sequence_number` within the outbox.

### Schema Change Policy
- Backward-compatible changes (adding optional fields) may be made within the same version.
- Breaking changes (removing fields, changing field types, renaming fields) require a new version suffix (`.v2`).
- Previous versions remain supported for a minimum of 6 months after a new version is published.

---

## 2. Domain Events by Domain

### 2.1 Admissions Domain

| Event Name | Payload Highlights | Typical Consumers |
|---|---|---|
| `admissions.application.submitted.v1` | `application_id, applicant_user_id, program_id, intake_year, submitted_at` | notifications (confirmation email), analytics |
| `admissions.application.status_changed.v1` | `application_id, old_status, new_status, changed_by_id, reason_code` | notifications (status update email/SMS), analytics |
| `admissions.application.accepted.v1` | `application_id, applicant_user_id, program_id, enrollment_deadline` | notifications (acceptance email), student account provisioning task |
| `admissions.application.rejected.v1` | `application_id, applicant_user_id, rejection_reason_code` | notifications (rejection email) |
| `admissions.merit_list.published.v1` | `merit_list_id, program_id, intake_year, total_candidates, published_by_id` | notifications (bulk email to shortlisted candidates), analytics |
| `admissions.enrollment.initiated.v1` | `student_id, user_id, program_id, batch, enrollment_date` | students app (profile creation), users app (portal access activation), finance app (initial invoice generation) |
| `admissions.cycle.published.v1` | `cycle_id, program_id, open_date, close_date, seat_limit, published_by_id` | student portal (display open admissions), notifications (announcement to prospective students), analytics |
| `admissions.cycle.closed.v1` | `cycle_id, program_id, total_applications_received, closed_by_id` | student portal (remove from active admissions), notifications, analytics |
| `admissions.entrance_exam.scheduled.v1` | `exam_id, cycle_id, exam_date, start_time, venue_count, applicant_count` | notifications (exam schedule email to applicants), calendar app |
| `admissions.entrance_exam.completed.v1` | `exam_id, cycle_id, total_applicants, scores_finalized, average_score` | merit list generation task, analytics, notifications (results available) |
| `admissions.merit_list.generated.v1` | `merit_list_id, cycle_id, total_ranked, cutoff_score, generated_by_id` | admin dashboard, analytics |
| `admissions.scholarship.auto_awarded.v1` | `merit_list_id, scholarship_program_id, awards_count, total_amount, top_n_students` | finance (create scholarship ledger entries), notifications (award emails to students), analytics |
| `admissions.applicant.converted_to_student.v1` | `application_id, student_id, user_id, program_id, semester_id, classroom_id, converted_by_id, enrollment_type` | students app (profile creation), users app (portal access activation), finance app (initial invoice generation), notifications (welcome email) |

---

### 2.2 Academic Domain

| Event Name | Payload Highlights | Typical Consumers |
|---|---|---|
| `academic.enrollment.created.v1` | `enrollment_id, student_id, section_id, semester_id, enrolled_at` | finance (invoice update), timetable (schedule update), notifications (confirmation) |
| `academic.enrollment.dropped.v1` | `enrollment_id, student_id, section_id, semester_id, dropped_at, drop_type (WITHIN_WINDOW/WITHDRAWN/WF)` | finance (invoice adjustment), timetable (slot release), analytics |
| `academic.grade.submitted.v1` | `grade_id, enrollment_id, exam_id, submitted_by_id, marks_obtained, status=SUBMITTED` | notifications (faculty submission confirmation) |
| `academic.grade.published.v1` | `grade_id, enrollment_id, exam_id, letter_grade, grade_points, published_at` | students app (GPA recalculation), notifications (grade available email), analytics, portal (grade display update) |
| `academic.grade.amended.v1` | `grade_id, enrollment_id, old_marks, new_marks, amended_by_id, reason_code, amendment_approved_by_id` | students app (GPA recalculation), audit log, notifications |
| `academic.attendance.marked.v1` | `attendance_session_id, section_id, date, marked_by_id, present_count, absent_count, late_count` | analytics (attendance statistics), attendance threshold checker task |
| `academic.attendance.threshold_breached.v1` | `student_id, section_id, attendance_percentage, threshold, breach_type (WARNING/HOLD)` | notifications (student warning email), academic hold service |
| `academic.timetable.published.v1` | `semester_id, published_by_id, sections_count, published_at` | notifications (bulk email to students and faculty), portal (timetable update), calendar app |
| `academic.exam.scheduled.v1` | `exam_id, section_id, scheduled_date, start_time, hall_id, published_at` | notifications (exam schedule email), calendar app |
| `enrollment.semester_progression.assigned.v1` | `student_id, from_semester_id, target_semester_id, classroom_id, is_repeat, assigned_by_id` | finance (generate next semester invoice), notifications (enrollment confirmation), timetable, student portal |
| `enrollment.semester.repeated.v1` | `student_id, enrollment_id, repeat_of_semester_number, target_semester_id, classroom_id, reason` | academic standing (flag repeat), notifications (repeat notification to student and advisor), analytics |
| `enrollment.classroom.assigned.v1` | `student_id, classroom_id, semester_id, assigned_by_id` | timetable (update student schedule), notifications (classroom assignment email), student portal |
| `course.faculty.assigned_to_classroom.v1` | `faculty_id, subject_id, classroom_id, semester_id, assigned_by_id` | timetable (generate/update schedule), notifications (assignment notification to faculty), faculty portal |
| `course.faculty.load_exceeded_warning.v1` | `faculty_id, current_credits, max_credits, department_id` | department head (review assignment), notifications (warning to admin), analytics |

---

### 2.3 Finance Domain

| Event Name | Payload Highlights | Typical Consumers |
|---|---|---|
| `finance.invoice.generated.v1` | `invoice_id, invoice_number, student_id, semester_id, total_amount, due_date` | notifications (invoice email), portal (fee summary update) |
| `finance.invoice.payment_received.v1` | `invoice_id, payment_transaction_id, amount_paid, remaining_balance, new_status` | notifications (payment receipt email), academic hold release task, portal |
| `finance.invoice.payment_failed.v1` | `invoice_id, payment_transaction_id, failure_reason_code, gateway_error_code` | notifications (payment failure email to student), payment retry task |
| `finance.invoice.overdue.v1` | `invoice_id, student_id, overdue_amount, days_overdue` | notifications (overdue reminder), financial hold creation task, analytics |
| `finance.invoice.refunded.v1` | `invoice_id, refund_transaction_id, refund_amount, refunded_by_id, reason_code` | notifications (refund confirmation email), analytics |
| `finance.financial_hold.applied.v1` | `student_id, invoice_id, hold_reason, applied_at` | students app (status flag), notifications, portal |
| `finance.financial_hold.released.v1` | `student_id, released_by (system/manual), released_at` | students app (status flag removal), notifications |

---

### 2.4 LMS Domain

| Event Name | Payload Highlights | Typical Consumers |
|---|---|---|
| `lms.content.published.v1` | `content_id, section_id, content_type, title, published_by_id, published_at` | notifications (new content email to enrolled students) |
| `lms.assignment.created.v1` | `assignment_id, section_id, title, due_datetime, max_marks, late_submissions_allowed` | notifications (assignment created email to students), calendar app |
| `lms.assignment.submitted.v1` | `submission_id, assignment_id, student_id, submitted_at, is_late, file_count` | notifications (submission confirmation to student), plagiarism check task (if enabled) |
| `lms.assignment.graded.v1` | `submission_id, assignment_id, student_id, marks_obtained, feedback_available, graded_by_id` | notifications (grade feedback email to student), portal (grade update) |
| `lms.quiz.completed.v1` | `attempt_id, quiz_id, student_id, score, max_score, completed_at, attempt_number` | notifications (quiz result to student if auto-graded), analytics |
| `lms.certificate.issued.v1` | `certificate_id, student_id, course_id, issued_at, certificate_url` | notifications (certificate email with download link), portal |

---

### 2.5 HR Domain

| Event Name | Payload Highlights | Typical Consumers |
|---|---|---|
| `hr.employee.onboarded.v1` | `employee_id, user_id, department_id, designation, joining_date` | users app (account activation), notifications (welcome email), IT provisioning task |
| `hr.leave.applied.v1` | `leave_id, employee_id, leave_type, start_date, end_date, days_count` | notifications (application confirmation, manager approval request) |
| `hr.leave.approved.v1` | `leave_id, employee_id, approved_by_id, approved_at` | notifications (approval email to employee), attendance app (leave record) |
| `hr.leave.rejected.v1` | `leave_id, employee_id, rejected_by_id, rejection_reason` | notifications (rejection email to employee) |
| `hr.payroll.processed.v1` | `payroll_run_id, pay_period, employee_count, total_net_pay, processed_by_id` | notifications (payslip generation task), finance app (payroll expense record) |
| `hr.payroll.payslip_generated.v1` | `payslip_id, employee_id, pay_period, net_pay, payslip_url` | notifications (payslip email to employee) |

---

### 2.6 Notification Domain

| Event Name | Payload Highlights | Typical Consumers |
|---|---|---|
| `notifications.notification.sent.v1` | `notification_id, recipient_id, channel (EMAIL/SMS/IN_APP), delivered_at` | analytics (delivery rate tracking) |
| `notifications.notification.failed.v1` | `notification_id, recipient_id, channel, failure_reason, attempt_count` | ops alert (if attempt_count > 3), retry task |
| `notifications.notification.bounced.v1` | `notification_id, recipient_id, channel=EMAIL, bounce_type (HARD/SOFT)` | users app (flag invalid email), analytics |

---

## 3. Publish and Consumption Sequence

```mermaid
sequenceDiagram
    autonumber
    participant SVC as Service Layer\n(e.g., EnrollmentService)
    participant DB as PostgreSQL\n(Transaction)
    participant Outbox as core_event_outbox table
    participant Relay as Outbox Relay Task\n(Celery periodic)
    participant Bus as Celery Task Queue\n(Redis broker)
    participant Consumer as Consumer App\n(e.g., FinanceService)
    participant DLQ as Dead Letter Queue\n(Redis list)

    SVC->>DB: BEGIN TRANSACTION
    SVC->>DB: INSERT enrollment record
    SVC->>Outbox: INSERT event row\n{event_type, payload, status=PENDING}
    DB->>DB: COMMIT
    Note over SVC,Outbox: Event row committed atomically with state change

    Relay->>Outbox: SELECT * WHERE status=PENDING LIMIT 100
    Outbox-->>Relay: [event rows]
    Relay->>Outbox: UPDATE status=PROCESSING
    Relay->>Bus: send_task(consumer_handler, args=[event_payload])
    Relay->>Outbox: UPDATE status=DISPATCHED

    Bus-->>Consumer: Deliver event payload

    Consumer->>Consumer: Check idempotency: event_id already processed?
    alt Already processed
        Consumer->>Consumer: Log "duplicate, skip"
        Consumer-->>Bus: ACK
    else First delivery
        Consumer->>Consumer: Process event
        alt Processing succeeds
            Consumer-->>Bus: ACK
            Consumer->>DB: Write consumer-side side effects
        else Processing fails (transient)
            Consumer-->>Bus: NACK
            Bus-->>Consumer: Retry (exponential backoff)
        else Max retries exceeded
            Bus->>DLQ: Move event to DLQ
            Note over DLQ: Ops team alerted; manual triage required
        end
    end
```

---

## 4. Operational SLOs

| SLO | Target | Measurement |
|---|---|---|
| Outbox commit-to-dispatch P95 latency | < 5 seconds | Time from `PENDING` insert to `DISPATCHED` update |
| Consumer processing P95 latency | < 10 seconds for tier-1 events | Time from dispatch to consumer ACK |
| DLQ triage acknowledgement | < 15 minutes during business hours | Time from DLQ entry to ops team acknowledgement |
| Event delivery success rate | ≥ 99.5% (excluding consumer bugs) | (Successfully ACK'd / Total dispatched) per 24h |
| Schema compatibility | 100% backward compatible within major version | Validated by schema registry check in CI |
| Duplicate event rate | < 0.01% | Idempotency log hits / total deliveries |

**Tier-1 Events** (highest priority, immediate retry and DLQ escalation):
- `admissions.enrollment.initiated.v1` — triggers student account creation
- `finance.invoice.payment_received.v1` — triggers receipt generation and hold release
- `academic.grade.published.v1` — triggers GPA recalculation and student notification
- `hr.payroll.processed.v1` — triggers payslip generation

---

### 2.7 Academic Session Events

| Event Name | Payload Highlights | Typical Consumers |
|---|---|---|
| `session.academic_year.activated.v1` | `academic_year_id`, `name`, `start_date`, `end_date` | All modules, Calendar |
| `session.semester.status_changed.v1` | `semester_id`, `old_status`, `new_status`, `academic_year_id` | Enrollment, Finance, LMS, Notifications |
| `session.semester.registration_opened.v1` | `semester_id`, `registration_start`, `registration_end` | Student Portal, Notifications, Enrollment |
| `session.semester.closed.v1` | `semester_id`, `academic_year_id` | Grades, Standing, Finance, Analytics |
| `session.blackout_period.started.v1` | `period_type`, `start_date`, `end_date`, `blocked_operations` | All modules |
| `session.course_offering.published.v1` | `semester_id`, `course_count`, `section_count` | Student Portal, Enrollment |

---

### 2.8 Graduation Events

| Event Name | Payload Highlights | Typical Consumers |
|---|---|---|
| `graduation.application.submitted.v1` | `application_id`, `student_id`, `program_id` | Registrar, Degree Audit |
| `graduation.audit.completed.v1` | `audit_id`, `student_id`, `status` (PASSED/FAILED), `missing_requirements` | Graduation Workflow, Notifications |
| `graduation.application.approved.v1` | `application_id`, `student_id`, `honors_classification` | Finance (clearance), Diploma Gen, Notifications |
| `graduation.degree.conferred.v1` | `student_id`, `diploma_number`, `program_id`, `honors`, `conferred_at` | Alumni, Transcript, Notifications, Analytics |
| `graduation.diploma.generated.v1` | `diploma_number`, `student_id`, `file_id` | Notifications, Student Portal |
| `graduation.degree.revoked.v1` | `student_id`, `diploma_number`, `reason`, `revoked_by_id` | All modules, Legal, Audit |

---

### 2.9 Discipline Events

| Event Name | Payload Highlights | Typical Consumers |
|---|---|---|
| `discipline.case.created.v1` | `case_id`, `student_id`, `severity`, `violation_category` | Discipline Committee, Notifications |
| `discipline.hearing.scheduled.v1` | `case_id`, `hearing_date`, `panel_members` | Notifications, Calendar |
| `discipline.decision.issued.v1` | `case_id`, `student_id`, `sanction`, `appeal_deadline` | Enrollment (holds), Notifications, Audit |
| `discipline.appeal.submitted.v1` | `appeal_id`, `case_id`, `student_id`, `grounds` | Appeals Board, Notifications |
| `discipline.appeal.decided.v1` | `appeal_id`, `case_id`, `outcome`, `modified_sanction` | Enrollment, Notifications, Audit |
| `discipline.sanction.enforced.v1` | `case_id`, `student_id`, `sanction_type`, `effective_date` | Enrollment, Access Control, Finance |
| `discipline.record.sealed.v1` | `case_id`, `student_id`, `sealed_at` | Audit (internal only) |

---

### 2.10 Academic Standing Events

| Event Name | Payload Highlights | Typical Consumers |
|---|---|---|
| `standing.determined.v1` | `student_id`, `semester_id`, `standing`, `semester_gpa`, `cgpa` | Student Portal, Notifications, Advisor |
| `standing.probation.applied.v1` | `student_id`, `semester_id`, `restrictions` | Enrollment (credit limit), Advisor, Notifications |
| `standing.suspension.applied.v1` | `student_id`, `effective_date`, `return_eligible_date` | Enrollment (block), Notifications, Access Control |
| `standing.deans_list.awarded.v1` | `student_id`, `semester_id`, `semester_gpa` | Notifications, Analytics, Student Portal |
| `standing.improvement_plan.created.v1` | `student_id`, `plan_details`, `advisor_id` | Advisor, Student Portal |

---

### 2.11 Grade Appeal Events

| Event Name | Payload Highlights | Typical Consumers |
|---|---|---|
| `appeal.grade.submitted.v1` | `appeal_id`, `student_id`, `enrollment_id`, `original_grade` | Faculty, Notifications |
| `appeal.grade.escalated.v1` | `appeal_id`, `from_level`, `to_level`, `reason` | Next-level reviewer, Notifications |
| `appeal.grade.resolved.v1` | `appeal_id`, `student_id`, `outcome`, `new_grade` | Grades (recalculate GPA), Notifications, Audit |

---

### 2.12 Recruitment Events

| Event Name | Payload Highlights | Typical Consumers |
|---|---|---|
| `recruitment.posting.published.v1` | `posting_id`, `department_id`, `title`, `deadline` | Career Portal, Notifications |
| `recruitment.application.received.v1` | `application_id`, `posting_id`, `applicant_email` | HR, Auto-Screening |
| `recruitment.application.screened.v1` | `application_id`, `screening_passed`, `score` | HR Dashboard |
| `recruitment.interview.scheduled.v1` | `application_id`, `interview_date`, `panel_members` | Notifications, Calendar, Room Booking |
| `recruitment.offer.extended.v1` | `application_id`, `offer_details`, `deadline` | Notifications, HR |
| `recruitment.candidate.hired.v1` | `application_id`, `employee_id`, `joining_date` | HR Onboarding, IT (account creation), Payroll |
| `recruitment.posting.closed.v1` | `posting_id`, `total_applications`, `hired_count` | Analytics, HR |

---

### 2.13 Transfer Credit Events

| Event Name | Payload Highlights | Typical Consumers |
|---|---|---|
| `transfer.credit.submitted.v1` | `transfer_id`, `student_id`, `source_institution` | Registrar, Notifications |
| `transfer.credit.evaluated.v1` | `transfer_id`, `status`, `credits_awarded` | Degree Audit, Student Portal, Notifications |
| `transfer.credit.appealed.v1` | `transfer_id`, `student_id`, `appeal_reason` | Registrar, Notifications |

---

### 2.14 Scholarship Events

| Event Name | Payload Highlights | Typical Consumers |
|---|---|---|
| `scholarship.application.submitted.v1` | `award_id`, `student_id`, `scholarship_id` | Financial Aid Office, Notifications |
| `scholarship.awarded.v1` | `award_id`, `student_id`, `amount`, `scholarship_name` | Finance (invoice adjustment), Notifications, Student Portal |
| `scholarship.disbursed.v1` | `award_id`, `student_id`, `amount`, `method` | Finance, Notifications |
| `scholarship.renewal.warning.v1` | `award_id`, `student_id`, `reason` | Student Portal, Notifications, Advisor |
| `scholarship.revoked.v1` | `award_id`, `student_id`, `reason`, `effective_date` | Finance (reverse adjustment), Notifications |
| `scholarship.fund.depleted.v1` | `scholarship_id`, `fund_total`, `fund_utilized` | Financial Aid Admin, Notifications |

---

### 2.15 Facility Events

| Event Name | Payload Highlights | Typical Consumers |
|---|---|---|
| `facility.room.booked.v1` | `booking_id`, `room_id`, `date`, `start_time`, `end_time` | Calendar, Notifications |
| `facility.booking.cancelled.v1` | `booking_id`, `room_id`, `cancelled_by_id` | Calendar, Notifications |
| `facility.maintenance.scheduled.v1` | `room_id`, `start_date`, `end_date` | Timetable (reschedule), Notifications |

---

## 5. Operational Policy Addendum

### Academic Integrity Policies
- `academic.grade.published.v1` events are immutable once published; a subsequent `academic.grade.amended.v1` event must reference the original `grade_id` and include the approver identity and reason code.
- Grade event payloads contain `marks_obtained` and `letter_grade` values, but never the student's full name or personal details — only `student_id` and `enrollment_id`. Consumers are responsible for resolving student identity via the student service.
- The `academic.timetable.published.v1` event triggers the academic calendar update; consumers must not expose the timetable data to students until this event is received (not on draft save).

### Student Data Privacy Policies
- Event payloads must never include PII fields: student name, date of birth, national ID, email address, phone number, or financial account details.
- `student_id` and `enrollment_id` are allowed as correlation identifiers; consumers that need PII must fetch it from the student service using these identifiers via a secure, role-checked API call.
- Events that could expose grade information in payloads (`academic.grade.published.v1`) must be delivered only to consumers with an explicit `GRADE_READ` permission scope in their service credentials.

### Fee Collection Policies
- `finance.invoice.payment_received.v1` is the authoritative signal for confirming a payment. No financial hold may be released, and no receipt may be generated, until this event is received. The event is emitted only after the payment gateway's webhook confirmation is verified.
- `finance.invoice.overdue.v1` is generated by a Celery Beat scheduled task that runs daily at 00:01 UTC and checks for invoices past their `due_date` with status not in (PAID, WRITTEN_OFF). The task is idempotent: it will not create a duplicate event if one was already generated for the same invoice on the same day.

### System Availability During Academic Calendar
- During academic blackout periods (exam week, first week of semester), the outbox relay task frequency is increased from every 30 seconds to every 5 seconds to minimize notification latency.
- DLQ monitoring alerts are elevated from MEDIUM to HIGH severity during blackout periods.
- Event schema changes are frozen during blackout periods; deployments introducing new event types or schema changes require the change window to be after the blackout period ends.
