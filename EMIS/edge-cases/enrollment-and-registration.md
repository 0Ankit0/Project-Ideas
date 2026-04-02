# Edge Cases — Enrollment and Registration

Domain-specific failure modes, impact assessments, and mitigation strategies for student enrollment and course registration workflows.

Edge case IDs in this file are permanent: **EC-ENROLL-001 through EC-ENROLL-010**.

---

## EC-ENROLL-001 — Seat Oversubscription Race Condition

| Field | Detail |
|---|---|
| **Failure Mode** | Two students simultaneously attempt to enroll in the last available seat in a section. Both read `seats_available = 1`, both pass the seat check, and both proceed to create an Enrollment record — resulting in enrollment count exceeding `max_enrollment`. |
| **Impact** | Section is overenrolled. Faculty may be obligated to teach more students than planned. Room capacity may be violated. |
| **Detection** | Database constraint `CHECK (current_enrollment <= max_enrollment)` on CourseSection table. API catches IntegrityError and returns 409. |
| **Mitigation / Recovery** | (1) Seat reservation uses `UPDATE course_section SET current_enrollment = current_enrollment + 1 WHERE id = %s AND current_enrollment < max_enrollment RETURNING id` atomic SQL — returns 0 rows if no seat available. (2) If 0 rows returned, API responds 409 `NO_SEATS_AVAILABLE`. (3) If overenrollment is discovered post-facto, registrar reviews and can manually drop the last enrollee (most recent timestamp) with notification and waitlist offer. |
| **Prevention** | Database-level atomic increment with conditional update. Integration tests use concurrent threads to simulate race. |

---

## EC-ENROLL-002 — Enrollment During Closed Registration Window

| Field | Detail |
|---|---|
| **Failure Mode** | Student submits an enrollment request slightly after the registration window closes. Due to clock skew between the application server and the database server, the request is accepted. |
| **Impact** | Student is enrolled after the official deadline. Creates equity concern (other students could not enroll after deadline). |
| **Detection** | Registration window check uses `NOW()` from PostgreSQL (`SELECT CURRENT_TIMESTAMP`), not the application server clock, to eliminate clock skew. |
| **Mitigation / Recovery** | (1) Enrollment service always fetches the current timestamp from the database for window validation. (2) If a post-window enrollment is discovered, registrar reviews and may void the enrollment with written justification. |
| **Prevention** | NTP synchronisation is enforced on all ECS Fargate tasks. All time-sensitive business logic uses database-side timestamp evaluation. End-to-end tests mock database time to validate boundary conditions. |

---

## EC-ENROLL-003 — Student Enrolled in Two Sections of the Same Course

| Field | Detail |
|---|---|
| **Failure Mode** | A student registers for Section A of CS101 and, using a concurrent request or a bulk registration call, also registers for Section B of the same course in the same semester. |
| **Impact** | Student occupies two seats in the same course. GPA calculation receives two grade entries for the same course, producing incorrect CGPA. |
| **Detection** | Database UNIQUE constraint on `(student_id, course_id, semester_id)` at the Enrollment level (not section level). |
| **Mitigation / Recovery** | (1) 409 `DUPLICATE_COURSE_ENROLLMENT` response includes existing enrollment ID. (2) If duplicate is discovered in live data, registrar drops one enrollment (lower-priority section) and notifies student. |
| **Prevention** | Unique constraint enforced at database level. Enrollment service also checks before insert in application layer for a user-friendly error message before hitting the DB constraint. |

---

## EC-ENROLL-004 — Financial Hold Lifted Mid-Registration Transaction

| Field | Detail |
|---|---|
| **Failure Mode** | Student's financial hold is checked at the start of a multi-section enrollment batch request. Between the check and the enrollment creation, the hold is re-applied (e.g., another invoice becomes overdue). The student completes enrollment in a now-held state. |
| **Impact** | Student is enrolled despite having an unpaid overdue balance, bypassing the institutional policy. |
| **Detection** | Hold check is repeated within the same database transaction, immediately before each Enrollment record is created (check-then-act within atomic transaction). |
| **Mitigation / Recovery** | (1) If hold is detected mid-transaction, the entire batch is rolled back and 403 `FINANCIAL_HOLD` is returned. (2) Any enrollments already committed in a previous partial batch must be voided — enrollments from the same batch share a `batch_id` field for easy identification. |
| **Prevention** | All multi-step enrollment logic runs within a single `@transaction.atomic` block. Hold re-evaluation at the start of the atomic block using `SELECT FOR UPDATE` on the student's invoice to prevent concurrent hold-lift races. |

---

## EC-ENROLL-005 — Add-Drop Resulting in Zero Enrolled Credits

| Field | Detail |
|---|---|
| **Failure Mode** | Student drops a course during the add-drop window, leaving them enrolled in fewer credit hours than the minimum required for their program (e.g., below 12 credit hours for a full-time student). |
| **Impact** | Student falls below full-time status. May affect financial aid eligibility, scholarship conditions, and visa status (for international students). |
| **Detection** | Drop endpoint validates remaining credit hours post-drop against `Program.min_credit_hours_per_semester`. |
| **Mitigation / Recovery** | (1) If drop would breach minimum credits, API returns 422 `MINIMUM_CREDITS_BREACH` with remaining credits and minimum threshold. (2) Student must add another course before or simultaneously with the drop. (3) Admin can grant a credit-hour waiver for special circumstances with mandatory documentation. |
| **Prevention** | Drop and add operations are processed atomically when submitted together in the same request. UI shows live credit-hour counter and highlights minimum-credit warning. |

---

## EC-ENROLL-006 — Prerequisite Waiver Granted But Not Recorded

| Field | Detail |
|---|---|
| **Failure Mode** | A faculty member verbally grants a student a prerequisite waiver, but it is never recorded in the system. The enrollment API still blocks the student. Student is frustrated and the faculty member escalates to IT. |
| **Impact** | Legitimate enrollment is blocked. Faculty and IT support burden increases. Student misses registration deadline while the issue is resolved. |
| **Detection** | This is a process failure, not a system failure. Detected via support ticket volume during registration windows. |
| **Mitigation / Recovery** | Admin can create a `PrerequisiteWaiver` record (`student_id`, `course_id`, `granted_by`, `reason`, `expires_at`) that the enrollment service checks before blocking on unmet prerequisite. |
| **Prevention** | Faculty-facing interface provides a "Grant Prerequisite Waiver" action. Waiver creation sends a notification to the student and is logged in AuditLog. Waivers expire at the end of the semester. |

---

## EC-ENROLL-007 — Enrollment Confirmation Email Not Delivered

| Field | Detail |
|---|---|
| **Failure Mode** | Student successfully enrolls but the `enrollment.confirmed` event is lost in the Celery queue (worker restart, Redis failover), so the confirmation email is never sent. |
| **Impact** | Student is uncertain whether enrollment was successful. May attempt to re-enroll, causing duplicate error. May contact support. |
| **Detection** | Celery task result backend records task state. A monitoring job checks for `enrollment.confirmed` events older than 10 minutes with no corresponding `notification.sent` record. |
| **Mitigation / Recovery** | (1) Enrollment API response includes a definitive `{status: "ACTIVE", enrollments_created: [...]}` payload — student can verify enrollment directly without relying on email. (2) Failed notification tasks are retried with exponential back-off (up to 5 attempts). (3) After 5 failures, a system alert is raised and ops team manually triggers resend. |
| **Prevention** | Celery tasks use `acks_late=True` and `reject_on_worker_lost=True` to prevent task loss on worker crash. Redis persistence (`appendonly yes`) ensures queue durability across restarts. |

---

## EC-ENROLL-008 — Mass Enrollment Import with Partial Failures

| Field | Detail |
|---|---|
| **Failure Mode** | Admin imports a CSV of 200 student-section assignments. 190 succeed but 10 fail (prerequisite not met, section full, student inactive). The system processes the whole file without clear failure reporting. |
| **Impact** | 10 students are not enrolled but admin believes all were processed. Enrollment discrepancy discovered only at start of semester. |
| **Detection** | Bulk import endpoint returns a structured response with per-row success/failure status and error codes. |
| **Mitigation / Recovery** | (1) Bulk import uses a "report and continue" strategy: process all rows, collect per-row results. (2) Response: `{"succeeded": 190, "failed": 10, "failures": [{"row": 45, "student_id": "...", "error": "NO_SEATS_AVAILABLE"}, ...]}`. (3) Admin can download a failure report CSV and re-process failed rows after resolving issues. |
| **Prevention** | Import process includes a dry-run mode (`?dry_run=true`) that validates all rows and returns the full failure report without persisting any changes. Admin is encouraged to run dry-run first. |

---

## EC-ENROLL-009 — Enrollment After Student Status Change to SUSPENDED

| Field | Detail |
|---|---|
| **Failure Mode** | A student's status is changed to SUSPENDED for disciplinary reasons. However, if the status update and the open registration window overlap, the student may still successfully enroll before the suspension is reflected. |
| **Impact** | Suspended student gains access to course sections, LMS content, and exam scheduling contrary to institutional policy. |
| **Detection** | Enrollment service checks `student.status == ACTIVE` at the start of every enrollment request. |
| **Mitigation / Recovery** | (1) All active enrollments for a suspended student are automatically cancelled when the suspension is recorded. (2) Cancellation event triggers a notification to the student and copies the registrar. (3) LMS course-space access is revoked immediately via `enrollment.cancelled` event. |
| **Prevention** | Student status update is processed within an atomic transaction that also cancels active enrollments and publishes `enrollment.cancelled` events. Status field has a database-level CHECK constraint to prevent invalid state transitions. |

---

## EC-ENROLL-010 — Late Withdrawal Without W Grade Recording

| Field | Detail |
|---|---|
| **Failure Mode** | Student submits a late withdrawal request after the census date. The withdrawal is processed without recording a W (Withdrawn) grade, so the course simply disappears from the transcript as if the student was never enrolled. |
| **Impact** | Transcript does not accurately reflect the student's academic history. Accreditation body and scholarship committees expect W grades to be recorded for post-census withdrawals. Financial aid recalculation may be incorrect. |
| **Detection** | Withdrawal endpoint branches on `AcademicCalendar.get_current_phase(semester_id)`: before census → `status=DROPPED` (no grade), after census → `status=WITHDRAWN` + create `Grade(letter_grade='W')`. |
| **Mitigation / Recovery** | (1) Registrar runs a semester-end audit comparing enrollment records with grades to detect any missing W entries. (2) Missing W grades are added via a grade amendment with `reason_code='AUDIT_CORRECTION'`. |
| **Prevention** | Withdrawal service has comprehensive unit tests covering pre-census, post-census, and post-final-exam scenarios. The census date is a required academic calendar event that raises a validation error during semester setup if absent. |

---

## Operational Policy Addendum

### Academic Integrity Policies
All enrollment overrides (bypassing prerequisite check, credit-hour minimum waiver, post-window enrollment) require explicit ADMIN action with a mandatory reason code. These overrides are logged in AuditLog and are available in the Registrar's override report. No automated process may perform overrides without human approval.

### Student Data Privacy Policies
Bulk enrollment imports may only be performed by ADMIN and REGISTRAR roles. Imported CSV files are processed in memory and not persisted to disk. Failure reports containing student IDs are generated as temporary pre-signed S3 URLs with a 1-hour expiry. All bulk import actions are recorded in AuditLog.

### Fee Collection Policies
Dropping a course within the refund window (typically first 7 days of semester) triggers an automatic partial refund calculation. The refund amount is computed by the Invoice Service based on the prorated tuition for the dropped credit hours. Finance staff review and approve refunds > INR 10,000 before processing.

### System Availability During Academic Calendar
The enrollment API is classified as Mission-Critical during `REGISTRATION_WINDOW` and `ADD_DROP_WINDOW` calendar events. Load tests are run before each registration window. ECS task count is pre-scaled (manual scaling override) before registration opens to handle peak concurrency.
