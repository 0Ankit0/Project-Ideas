# API Design — Education Management Information System

Complete REST API reference for all EMIS modules. All endpoints require a valid JWT `Authorization: Bearer <token>` header unless marked **Public**.

**Base URL:** `https://api.emis.example.edu/api/v1`

---

## Global Conventions

| Convention | Value |
|---|---|
| Authentication | JWT Bearer (access token, 15 min expiry) |
| Content-Type | `application/json` |
| Date format | ISO 8601: `YYYY-MM-DDTHH:MM:SSZ` |
| Pagination | `?page=1&page_size=20`; response includes `count`, `next`, `previous` |
| Soft deletes | Resources are deactivated, not hard-deleted |
| Error envelope | `{"error": {"code": "...", "message": "...", "details": {...}}}` |
| Idempotency | Unsafe write operations accept `Idempotency-Key` header |
| Versioning | URL path (`/api/v1/`) |

---

## Standard Error Codes

| HTTP Status | Error Code | Meaning |
|---|---|---|
| 400 | `VALIDATION_ERROR` | Request payload failed validation |
| 401 | `UNAUTHORIZED` | Missing or expired token |
| 401 | `INVALID_CREDENTIALS` | Wrong username/password |
| 401 | `INVALID_OTP` | MFA code incorrect |
| 401 | `TOKEN_EXPIRED` | Refresh token expired or revoked |
| 403 | `FORBIDDEN` | Insufficient role/permission |
| 403 | `FINANCIAL_HOLD` | Student has unpaid overdue invoice |
| 403 | `ADD_DROP_WINDOW_CLOSED` | Operation outside allowed window |
| 403 | `SUBMISSION_DEADLINE_PASSED` | Assignment deadline elapsed |
| 404 | `NOT_FOUND` | Resource does not exist |
| 409 | `CONFLICT` | State conflict (duplicate, seat full, etc.) |
| 409 | `NO_SEATS_AVAILABLE` | Course section has no open seats |
| 422 | `PREREQUISITE_NOT_MET` | Course prerequisite not satisfied |
| 422 | `MISSING_REQUIRED_DOCUMENTS` | Application documents incomplete |
| 422 | `TEACHING_LOAD_EXCEEDED` | Faculty teaching load limit breached |
| 422 | `INSUFFICIENT_LEAVE_BALANCE` | Leave balance insufficient |
| 429 | `RATE_LIMITED` | Too many requests |
| 500 | `INTERNAL_SERVER_ERROR` | Unexpected server fault |
| 503 | `SERVICE_UNAVAILABLE` | Downstream dependency unavailable |

---

## 1. Authentication

### POST `/auth/login/`
**Public.** Authenticate user and receive JWT tokens.

**Request:**
```json
{
  "email": "student@example.edu",
  "password": "S3cur3Pass!"
}
```

**Response 200 (no MFA):**
```json
{
  "access_token": "<jwt>",
  "refresh_token": "<jwt>",
  "user": {"id": "uuid", "role": "STUDENT", "full_name": "Priya Sharma"}
}
```

**Response 200 (MFA required):**
```json
{"mfa_required": true, "session_token": "<short-lived-token>"}
```

---

### POST `/auth/mfa/verify/`
**Public.** Submit MFA OTP to complete login.

**Request:** `{"session_token": "...", "otp": "123456"}`
**Response 200:** Same as login success (access + refresh tokens).

---

### POST `/auth/token/refresh/`
**Public.** Exchange a valid refresh token for a new access token.

**Request:** `{"refresh_token": "<jwt>"}`
**Response 200:** `{"access_token": "<jwt>", "refresh_token": "<jwt>"}`

---

### POST `/auth/logout/`
Revoke the provided refresh token.

**Request:** `{"refresh_token": "<jwt>"}`
**Response 204:** No content.

---

### POST `/auth/change-password/`
Change the authenticated user's password.

**Request:** `{"current_password": "...", "new_password": "..."}`
**Response 200:** `{"message": "Password changed successfully."}`

---

## 2. Students

### GET `/students/`
**Roles:** ADMIN, FACULTY (limited), HR_STAFF
List students with optional filters.

**Query params:** `?program_id=&batch=&status=ACTIVE&search=`
**Response 200:** Paginated list of student summaries.

---

### POST `/students/`
**Roles:** ADMIN
Manually create a student record (bulk import use case).

**Request:**
```json
{
  "user_id": "uuid",
  "program_id": "uuid",
  "batch": "2024",
  "admission_date": "2024-08-01",
  "expected_graduation_date": "2028-05-31"
}
```
**Response 201:** Full student object.

---

### GET `/students/{id}/`
**Roles:** ADMIN, FACULTY, STUDENT (own record), PARENT (linked record)

---

### PATCH `/students/{id}/`
**Roles:** ADMIN (full), STUDENT (profile fields only)

---

### GET `/students/{id}/grades/`
**Roles:** ADMIN, FACULTY (section-scoped), STUDENT (own), PARENT (if consent granted)

**Query params:** `?semester_id=&exam_type=`
**Response 200:** List of Grade objects with letter grade and grade points.

---

### GET `/students/{id}/transcript/`
**Roles:** ADMIN, STUDENT (own)
Returns a pre-signed S3 URL for the official PDF transcript.

**Response 200:** `{"url": "https://...", "expires_at": "..."}`

---

### POST `/students/{id}/parents/`
**Roles:** STUDENT (own)
Grant a parent portal access. Creates or links a Parent User account.

**Request:** `{"email": "parent@example.com", "relationship": "FATHER"}`
**Response 201:** `{"parent_id": "uuid", "portal_access": true}`

---

### DELETE `/students/{id}/parents/{parent_id}/`
**Roles:** STUDENT (own)
Revoke parent portal access and invalidate parent tokens.
**Response 204:** No content.

---

## 3. Admissions

### GET `/admissions/programs/`
**Public.** List programs open for applications.

---

### POST `/admissions/applications/`
**Public (authenticated applicant required).** Submit a new application.

**Request:**
```json
{
  "program_id": "uuid",
  "intake_year": 2025,
  "personal_details": {"first_name": "...", "last_name": "...", "dob": "2002-05-15", "email": "..."},
  "academic_history": [{"institution": "...", "grade": "A", "year": 2022}]
}
```
**Response 201:** `{"application_id": "uuid", "status": "DRAFT"}`

---

### PATCH `/admissions/applications/{id}/`
Update draft application or trigger status transitions.

**Trigger submission:** `{"action": "submit"}`
**Response 200:** Updated application object.

---

### POST `/admissions/applications/{id}/documents/`
Upload a required document.

**Multipart form data:** `doc_type=TRANSCRIPT&file=<binary>`
**Response 201:** `{"document_id": "uuid", "status": "PENDING_REVIEW"}`

---

### POST `/admissions/merit-lists/`
**Roles:** ADMIN
Generate a merit list for a program intake.

**Request:** `{"program_id": "uuid", "intake_year": 2025, "seat_count": 60}`
**Response 201:** `{"merit_list_id": "uuid", "total_ranked": 147}`

---

### POST `/admissions/merit-lists/{id}/dispatch-offers/`
**Roles:** ADMIN
Send offer letters to top-ranked applicants.

**Response 200:** `{"offers_sent": 60}`

---

### POST `/admissions/cycles/`
**Roles:** ADMIN, SUPER_ADMIN
Create a new admission cycle with open/close dates, program, seat limit, and eligibility criteria.

**Request:**
```json
{
  "program_id": "uuid",
  "open_date": "2026-06-01",
  "close_date": "2026-08-31",
  "seat_limit": 120,
  "eligibility_criteria": {"min_gpa": 3.0, "required_subjects": ["Mathematics", "Physics"]},
  "entrance_exam_required": true
}
```
**Response 201:**
```json
{
  "id": "uuid",
  "program": {"id": "uuid", "name": "BS Computer Science"},
  "status": "DRAFT",
  "open_date": "2026-06-01",
  "close_date": "2026-08-31",
  "seat_limit": 120,
  "entrance_exam_required": true,
  "created_at": "2026-05-01T10:00:00Z"
}
```

---

### PATCH `/admissions/cycles/{id}/publish/`
**Roles:** ADMIN
Publish admission cycle — makes it visible on the public portal to prospective students.

**Response 200:**
```json
{
  "id": "uuid",
  "status": "PUBLISHED",
  "published_at": "2026-05-15T09:30:00Z"
}
```

---

### PATCH `/admissions/cycles/{id}/close/`
**Roles:** ADMIN
Close admission cycle — stops accepting new applications.

**Response 200:**
```json
{
  "id": "uuid",
  "status": "CLOSED"
}
```

---

### POST `/admissions/cycles/{cycle_id}/entrance-exam/configure/`
**Roles:** ADMIN
Configure entrance exam for an admission cycle (question bank, duration, scoring).

**Request:**
```json
{
  "title": "Fall 2026 Entrance Exam — BS Computer Science",
  "duration_minutes": 120,
  "total_marks": 100,
  "passing_marks": 40,
  "question_bank_id": "uuid",
  "auto_score": true
}
```
**Response 201:**
```json
{
  "id": "uuid",
  "cycle_id": "uuid",
  "status": "CONFIGURED"
}
```

---

### POST `/admissions/entrance-exams/{exam_id}/schedule/`
**Roles:** ADMIN
Schedule exam date and assign applicants to examination halls.

**Request:**
```json
{
  "exam_date": "2026-09-10",
  "start_time": "09:00",
  "venue_assignments": [
    {"applicant_ids": ["uuid1", "uuid2"], "room_id": "uuid"}
  ]
}
```
**Response 200:**
```json
{
  "scheduled_count": 120,
  "venue_count": 3
}
```

---

### POST `/admissions/entrance-exams/{exam_id}/applicants/{applicant_id}/submit/`
**Roles:** APPLICANT
Submit entrance exam answers.

**Request:**
```json
{
  "answers": [
    {"question_id": "uuid", "selected_option": "B"},
    {"question_id": "uuid", "selected_option": "D"}
  ]
}
```
**Response 200:**
```json
{
  "submitted_at": "2026-09-10T11:45:00Z",
  "auto_score": 78.5
}
```
> `auto_score` is returned only if auto-scoring is enabled for the exam.

---

### POST `/admissions/entrance-exams/{exam_id}/finalize-scores/`
**Roles:** ADMIN
Finalize all scores — locks scores and enables merit list generation.

**Response 200:**
```json
{
  "total_applicants": 120,
  "scores_finalized": 118
}
```

---

### POST `/admissions/cycles/{cycle_id}/merit-list/generate/`
**Roles:** ADMIN
Auto-generate merit list ranked by entrance exam scores and configurable weightage.

**Request:**
```json
{
  "weightage": {"exam_score": 0.7, "academic_record": 0.2, "interview": 0.1},
  "seat_limit": 60
}
```
**Response 201:**
```json
{
  "id": "uuid",
  "cycle_id": "uuid",
  "total_ranked": 118,
  "cutoff_score": 62.5,
  "status": "DRAFT"
}
```

---

### PATCH `/admissions/merit-lists/{id}/publish/`
**Roles:** ADMIN
Publish merit list — visible to applicants on the portal.

**Response 200:**
```json
{
  "id": "uuid",
  "status": "PUBLISHED",
  "published_at": "2026-09-20T14:00:00Z"
}
```

---

### GET `/admissions/merit-lists/{id}/`
**Roles:** ADMIN, STAFF
Get merit list with ranked applicants.

**Response 200:**
```json
{
  "id": "uuid",
  "cycle_id": "uuid",
  "status": "PUBLISHED",
  "total_ranked": 118,
  "cutoff_score": 62.5,
  "ranked_applicants": [
    {"rank": 1, "applicant_id": "uuid", "name": "Ali Khan", "score": 95.2, "scholarship_eligible": true},
    {"rank": 2, "applicant_id": "uuid", "name": "Sara Ahmed", "score": 93.8, "scholarship_eligible": true}
  ]
}
```

---

### POST `/admissions/merit-lists/{id}/auto-award-scholarships/`
**Roles:** ADMIN
Auto-award scholarships to top N students from the merit list.

**Request:**
```json
{
  "scholarship_program_id": "uuid",
  "top_n_students": 10,
  "award_type": "FIXED_PER_SEMESTER",
  "amount_per_semester": 50000,
  "duration_semesters": 8
}
```
> `award_type` accepts `FIXED_PER_SEMESTER` (fixed amount each semester) or `FULL_COVERAGE` (covers full tuition).

**Response 200:**
```json
{
  "awards_created": 10,
  "total_amount": 4000000,
  "students": [
    {"student_id": "uuid", "name": "Ali Khan", "rank": 1, "amount": 50000},
    {"student_id": "uuid", "name": "Sara Ahmed", "rank": 2, "amount": 50000}
  ]
}
```
**Errors:**
- `409 MERIT_LIST_NOT_PUBLISHED` — Merit list must be published before awarding scholarships
- `422 INSUFFICIENT_SCHOLARSHIP_FUND` — Scholarship fund cannot cover the requested awards

---

### POST `/admissions/applications/{id}/convert-to-student/`
**Roles:** ADMIN, ADMISSIONS_STAFF
Convert an accepted applicant to a student. Validates that all bills are cleared, documents are verified, and the offer has been accepted.

**Request:**
```json
{
  "semester_id": "uuid",
  "classroom_id": "uuid",
  "enrollment_type": "REGULAR"
}
```
> `enrollment_type` accepts `REGULAR` or `LATERAL`.

**Response 200:**
```json
{
  "student_id": "STU-2026-00123",
  "enrollment_id": "uuid",
  "semester": {"id": "uuid", "name": "Fall 2026"},
  "classroom": {"id": "uuid", "name": "CS-A"},
  "status": "ENROLLED"
}
```
**Errors:**
- `422 APPLICATION_NOT_ACCEPTED` — Application must be in ACCEPTED status
- `422 OUTSTANDING_BILLS_EXIST` — All bills must be cleared before conversion
- `422 DOCUMENTS_NOT_VERIFIED` — All required documents must be verified
- `422 OFFER_NOT_ACCEPTED` — Applicant must have accepted the admission offer

**Validation rules:** `application.status == ACCEPTED AND account.outstanding_balance == 0 AND all documents.status == VERIFIED AND offer.status == ACCEPTED`

---

## 4. Courses and Curriculum

### GET `/courses/`
List all courses. **Roles:** ADMIN, FACULTY, STUDENT (active only)

**Query params:** `?department_id=&is_elective=&search=`

---

### GET `/courses/{id}/sections/`
Get all sections for a course in a semester.

**Query params:** `?semester_id=`

---

### POST `/courses/sections/`
**Roles:** ADMIN
Create a new course section.

**Request:**
```json
{
  "course_id": "uuid",
  "section_code": "A",
  "faculty_id": "uuid",
  "semester_id": "uuid",
  "room_id": "uuid",
  "max_enrollment": 40
}
```

---

### PATCH `/courses/sections/{id}/`
**Roles:** ADMIN
Update section (including faculty assignment).

---

### POST `/courses/classroom-faculty-assignment/`
**Roles:** ADMIN, DEPT_HEAD
Assign faculty members to subjects for a specific classroom's semester.

**Request:**
```json
{
  "semester_id": "uuid",
  "classroom_id": "uuid",
  "assignments": [
    {"subject_id": "uuid", "faculty_id": "uuid"},
    {"subject_id": "uuid", "faculty_id": "uuid"}
  ]
}
```
**Response 200:**
```json
{
  "assigned": 6,
  "classroom": {"id": "uuid", "name": "CS-A"},
  "semester": {"id": "uuid", "name": "Fall 2026"},
  "assignments": [
    {"subject": {"id": "uuid", "name": "Data Structures"}, "faculty": {"id": "uuid", "name": "Dr. Smith"}},
    {"subject": {"id": "uuid", "name": "Algorithms"}, "faculty": {"id": "uuid", "name": "Dr. Khan"}}
  ]
}
```
**Errors:**
- `422 FACULTY_LOAD_EXCEEDED` — Faculty has reached maximum credit hours
- `409 TIMETABLE_CONFLICT` — Faculty has a timetable conflict in the assigned slot
- `422 FACULTY_NOT_QUALIFIED` — Faculty is not qualified to teach the assigned subject

---

### GET `/faculty/{faculty_id}/teaching-load/`
**Roles:** ADMIN, DEPT_HEAD, FACULTY (own)
Get current teaching load and remaining capacity for a faculty member.

**Response 200:**
```json
{
  "faculty_id": "uuid",
  "current_credits": 12,
  "max_credits": 18,
  "remaining": 6,
  "courses": [
    {"section_id": "uuid", "course_name": "Data Structures", "credits": 3, "classroom": "CS-A"},
    {"section_id": "uuid", "course_name": "Algorithms", "credits": 3, "classroom": "CS-B"}
  ]
}
```

---

## 5. Enrollment

### GET `/enrollment/available-sections/`
**Roles:** STUDENT
List sections available for registration in the current semester.

**Query params:** `?semester_id=`
**Response 200:** Sections with `seats_available`, `time_slots`, and `faculty_name`.

---

### POST `/enrollment/`
**Roles:** STUDENT
Register for one or more sections.

**Request:** `{"student_id": "uuid", "section_ids": ["uuid1", "uuid2"]}`
**Response 201:** `{"enrollments_created": [{"enrollment_id": "uuid", "section_id": "uuid"}]}`

---

### DELETE `/enrollment/{enrollment_id}/`
**Roles:** STUDENT (own), ADMIN
Drop an enrollment (within add-drop window).

**Response 204:** No content.

---

### POST `/enrollment/semester-progression/`
**Roles:** ADMIN
Assign students to the next semester or repeat a previous semester. Admin selects target semester for each student.

**Request:**
```json
{
  "assignments": [
    {"student_id": "uuid", "target_semester_id": "uuid", "is_repeat": false, "classroom_id": "uuid"},
    {"student_id": "uuid", "target_semester_id": "uuid", "is_repeat": true, "classroom_id": "uuid", "reason": "Failed core courses"}
  ]
}
```
**Response 200:**
```json
{
  "processed": 120,
  "enrolled": 118,
  "failed": 2,
  "failures": [
    {"student_id": "uuid", "error": "STUDENT_HAS_FINANCIAL_HOLD"}
  ]
}
```
**Errors:**
- `422 STUDENT_HAS_FINANCIAL_HOLD` — Student has outstanding financial obligations
- `422 ACADEMIC_STANDING_SUSPENDED` — Student's academic standing prevents progression

---

### GET `/enrollment/students/{student_id}/progression-eligibility/`
**Roles:** ADMIN, STUDENT (own)
Check if a student is eligible to progress to the next semester.

**Response 200:**
```json
{
  "eligible": true,
  "can_repeat": false,
  "outstanding_bills": 0,
  "academic_standing": "GOOD",
  "failed_courses": [],
  "max_duration_exceeded": false
}
```

---

### POST `/enrollment/repeat-semester/`
**Roles:** ADMIN
Enroll a student in a repeat of a previous semester.

**Request:**
```json
{
  "student_id": "uuid",
  "repeat_semester_number": 3,
  "target_semester_id": "uuid",
  "classroom_id": "uuid",
  "reason": "Failed 3 core courses in Semester 3"
}
```
**Response 200:**
```json
{
  "enrollment_id": "uuid",
  "semester": {"id": "uuid", "name": "Fall 2026"},
  "is_repeat": true,
  "repeat_of_semester_number": 3
}
```

---

## 6. Timetable

### GET `/timetable/`
**Roles:** All authenticated users
View the timetable for a semester.

**Query params:** `?semester_id=&section_id=&faculty_id=&student_id=`

---

### POST `/timetable/generate/`
**Roles:** ADMIN
Trigger automated timetable generation.

**Request:** `{"semester_id": "uuid"}`
**Response 201:** `{"timetable_id": "uuid", "slots_created": 240}` or 422 with conflict list.

---

### POST `/timetable/room-bookings/`
**Roles:** FACULTY, ADMIN
Book a room for a special event.

**Request:** `{"room_id": "uuid", "date": "2025-03-15", "start_time": "14:00", "end_time": "16:00", "purpose": "Department seminar"}`
**Response 201:** `{"booking_id": "uuid"}`

---

## 7. Attendance

### POST `/attendance/sessions/`
**Roles:** FACULTY
Record attendance for a class session.

**Request:**
```json
{
  "section_id": "uuid",
  "date": "2025-02-10",
  "records": [
    {"student_id": "uuid", "status": "PRESENT"},
    {"student_id": "uuid", "status": "ABSENT"}
  ]
}
```
**Response 201:** `{"session_id": "uuid", "records_created": 38}`

---

### GET `/attendance/summary/`
**Roles:** ADMIN, FACULTY (section-scoped), STUDENT (own), PARENT (linked student)

**Query params:** `?student_id=&section_id=&semester_id=`
**Response 200:** `{"student_id": "uuid", "section": "...", "total_classes": 40, "attended": 34, "percentage": 85.0}`

---

### POST `/attendance/corrections/`
**Roles:** STUDENT
Submit an attendance correction request.

**Request:** `{"record_id": "uuid", "reason": "Medical emergency", "supporting_doc_url": "..."}`
**Response 201:** `{"request_id": "uuid", "status": "PENDING"}`

---

## 8. Exams and Grades

### POST `/exams/`
**Roles:** ADMIN, FACULTY (own sections)
Schedule an exam.

**Request:**
```json
{
  "section_id": "uuid",
  "exam_type": "MIDTERM",
  "scheduled_date": "2025-03-20",
  "start_time": "09:00",
  "duration_minutes": 180,
  "total_marks": 100,
  "passing_marks": 40
}
```

---

### POST `/exams/{id}/admit-cards/generate/`
**Roles:** ADMIN
Batch-generate admit card PDFs and store on S3.

**Response 200:** `{"admit_cards_generated": 38}`

---

### PATCH `/grades/bulk/`
**Roles:** FACULTY (own exams only)
Submit draft grades for an exam.

**Request:** `{"grades": [{"enrollment_id": "uuid", "exam_id": "uuid", "marks_obtained": 75.5}]}`
**Response 200:** `{"grades_updated": 38}`

---

### POST `/grades/publish/`
**Roles:** FACULTY (own), ADMIN
Publish grades and trigger GPA recalculation.

**Query params:** `?exam_id=`
**Response 200:** `{"grades_published": 38}`

---

### POST `/grades/{id}/disputes/`
**Roles:** STUDENT (own grades)
Raise a grade dispute.

**Request:** `{"dispute_reason": "Calculation error in Q3", "expected_marks": 80}`
**Response 201:** `{"dispute_id": "uuid", "status": "OPEN"}`

---

## 9. LMS

### GET `/lms/course-spaces/`
**Roles:** FACULTY (assigned), STUDENT (enrolled)
List accessible course spaces.

---

### POST `/lms/content/`
**Roles:** FACULTY
Upload learning material.

**Multipart form data:** `course_space_id=uuid&content_type=PDF&title=Lecture+1&file=<binary>`
**Response 201:** `{"content_id": "uuid", "url": "https://...", "content_type": "PDF"}`

---

### POST `/lms/assignments/{id}/submissions/`
**Roles:** STUDENT
Submit assignment.

**Multipart form data:** `file=<binary>&comments=...`
**Response 201:** `{"submission_id": "uuid", "status": "SUBMITTED", "submitted_at": "..."}`

---

### GET `/lms/assignments/{id}/submissions/`
**Roles:** FACULTY (own assignment), ADMIN

---

### POST `/lms/quizzes/{id}/attempts/`
**Roles:** STUDENT
Start a quiz attempt.

**Response 200:** `{"attempt_id": "uuid", "questions": [...], "time_limit_seconds": 3600}`

---

### PATCH `/lms/attempts/{id}/answers/`
**Roles:** STUDENT (own attempt, in-progress only)
Save an answer during an attempt.

**Request:** `{"question_id": "uuid", "selected_option_id": "uuid"}`

---

### POST `/lms/attempts/{id}/submit/`
**Roles:** STUDENT
Finalise and auto-grade a quiz attempt.

**Response 200:** `{"score": 18, "max_score": 20, "percentage": 90.0, "pass": true}`

---

## 10. Finance

### GET `/finance/invoices/`
**Roles:** ADMIN, FINANCE_STAFF, STUDENT (own)

**Query params:** `?student_id=&semester_id=&status=`

---

### POST `/finance/invoices/generate/`
**Roles:** ADMIN, FINANCE_STAFF
Bulk-generate fee invoices for a cohort.

**Request:** `{"semester_id": "uuid", "program_id": "uuid"}`
**Response 200:** `{"invoices_created": 120, "total_value": "12000000.00"}`

---

### POST `/finance/payments/initiate/`
**Roles:** STUDENT (own invoices), FINANCE_STAFF
Initiate a gateway payment.

**Request:** `{"invoice_id": "uuid"}`
**Response 200:** `{"order_id": "...", "gateway_key": "...", "amount": "50000.00", "currency": "INR"}`

---

### POST `/finance/payments/webhook/`
**Public (HMAC-verified).** Receive payment gateway webhook events.

---

### POST `/finance/refunds/`
**Roles:** FINANCE_STAFF, ADMIN
Initiate a refund.

**Request:** `{"payment_transaction_id": "uuid", "refund_amount": "5000.00", "reason_code": "DROPOUT"}`
**Response 201:** `{"refund_id": "uuid", "status": "PROCESSING"}`

---

### GET `/finance/invoices/{id}/receipt/`
**Roles:** STUDENT (own), FINANCE_STAFF, ADMIN
Get pre-signed URL for payment receipt PDF.

**Response 200:** `{"url": "https://...", "expires_at": "..."}`

---

## 11. Notifications

### GET `/notifications/`
**Roles:** All authenticated users
Retrieve in-app notifications for the current user.

**Query params:** `?is_read=false&page=1`
**Response 200:** Paginated notification list.

---

### PATCH `/notifications/{id}/`
Mark notification as read.

**Request:** `{"is_read": true}`

---

### PATCH `/notifications/mark-all-read/`
Mark all unread notifications as read.
**Response 200:** `{"updated": 12}`

---

### GET `/notifications/preferences/`
Get current user's channel preferences.

---

### PATCH `/notifications/preferences/`
Update channel preferences.

**Request:**
```json
{
  "preferences": [
    {"event_type": "grade.published", "email": true, "sms": false, "push": true, "in_app": true},
    {"event_type": "attendance.threshold_breached", "email": true, "sms": true, "push": true, "in_app": true}
  ]
}
```

---

## 12. Analytics

### POST `/analytics/reports/`
**Roles:** ADMIN
Queue an analytics report job.

**Request:**
```json
{
  "report_type": "enrollment_summary",
  "filters": {"semester_id": "uuid", "program_id": "uuid"},
  "output_format": "XLSX"
}
```
**Response 202:** `{"report_job_id": "uuid", "status": "QUEUED"}`

---

### GET `/analytics/reports/{job_id}/`
Poll report status and retrieve download URL when ready.

**Response 200:** `{"status": "COMPLETED", "download_url": "...", "expires_at": "..."}` or `{"status": "PROCESSING"}`

---

### GET `/analytics/dashboards/`
**Roles:** ADMIN
Return pre-aggregated dashboard KPIs.

**Response 200:**
```json
{
  "total_enrolled_students": 2840,
  "avg_cgpa": 3.21,
  "attendance_compliance_pct": 88.4,
  "fee_collection_rate_pct": 94.2,
  "active_faculty": 187
}
```

---

## 13. CMS

### GET `/cms/announcements/`
**Public** for published announcements; all statuses for ADMIN.

**Query params:** `?audience=ALL&status=PUBLISHED`

---

### POST `/cms/announcements/`
**Roles:** ADMIN
Create an announcement.

**Request:** `{"title": "...", "content": "...", "audience": "ALL", "publish_at": "2025-02-01T09:00:00Z"}`

---

### PATCH `/cms/announcements/{id}/`
Update or trigger publish/unpublish.

---

## 14. Calendar

### GET `/calendar/events/`
**Public.** List academic calendar events.

**Query params:** `?year=2025&event_type=EXAM_PERIOD`

---

### POST `/calendar/events/`
**Roles:** ADMIN
Create a calendar event.

**Request:** `{"name": "Mid-Semester Break", "event_type": "HOLIDAY", "start_date": "2025-03-17", "end_date": "2025-03-21"}`

---

## 15. File Management

### POST `/files/upload/`
Upload any file (generic endpoint used by all modules).

**Multipart form data:** `file=<binary>&context=admission_document&content_type=application/pdf`
**Response 201:** `{"file_id": "uuid", "url": "...", "size_bytes": 204800}`

---

### GET `/files/{id}/`
Get file metadata and a pre-signed download URL.

**Response 200:** `{"file_id": "uuid", "url": "...", "expires_at": "...", "original_filename": "..."}`

---

## 16. Academic Session & Semester Management

### POST `/academic-years/`
**Roles:** ADMIN, SUPER_ADMIN
Create a new academic year.

**Request:**
```json
{
  "name": "2025-2026",
  "start_date": "2025-09-01",
  "end_date": "2026-06-30"
}
```

**Response 201:**
```json
{
  "id": "uuid",
  "name": "2025-2026",
  "start_date": "2025-09-01",
  "end_date": "2026-06-30",
  "status": "PLANNING",
  "is_current": false
}
```

---

### GET `/academic-years/`
**Roles:** ALL (authenticated)
List academic years with optional status filter.

**Query params:** `?status=ACTIVE&page=1&page_size=10`

---

### PATCH `/academic-years/{id}/activate/`
**Roles:** SUPER_ADMIN
Activate an academic year. Requires previous year to be COMPLETED. Only one year can be ACTIVE.

**Response 200:** `{"id": "uuid", "status": "ACTIVE", "is_current": true}`

**Error responses:**
- `409 ACADEMIC_YEAR_CONFLICT` — Another year is already active

---

### POST `/semesters/`
**Roles:** ADMIN
Create a semester within an academic year.

**Request:**
```json
{
  "academic_year_id": "uuid",
  "semester_type": "FALL",
  "start_date": "2025-09-01",
  "end_date": "2025-12-20",
  "registration_start": "2025-08-15",
  "registration_end": "2025-09-10",
  "add_drop_deadline": "2025-09-15",
  "grading_open_date": "2025-12-21",
  "grading_close_date": "2026-01-10"
}
```

**Response 201:** Full semester object with all dates.

---

### GET `/semesters/`
**Roles:** ALL (authenticated)
List semesters with filters.

**Query params:** `?academic_year_id=uuid&is_current=true&status=ACTIVE`

---

### PATCH `/semesters/{id}/status/`
**Roles:** ADMIN
Transition semester status (PLANNING → REGISTRATION_OPEN → ACTIVE → EXAM_PERIOD → GRADING → COMPLETED → ARCHIVED).

**Request:** `{"status": "ACTIVE"}`

**Error responses:**
- `422 INVALID_SEMESTER_TRANSITION` — Invalid state transition
- `422 SEMESTER_CLOSURE_BLOCKED` — Grades not all submitted

---

### POST `/semesters/{id}/course-offerings/`
**Roles:** ADMIN, DEPARTMENT_HEAD
Configure course offerings for a semester.

**Request:**
```json
{
  "course_id": "uuid",
  "sections": [
    {
      "section_code": "A",
      "faculty_id": "uuid",
      "room_id": "uuid",
      "schedule": {"days": ["MON", "WED"], "start_time": "09:00", "end_time": "10:30"},
      "max_enrollment": 60
    }
  ]
}
```

**Response 201:** Created course offering with sections.

---

### GET `/semesters/{id}/course-offerings/`
**Roles:** ALL (authenticated)
List all course offerings for a semester.

**Query params:** `?department_id=uuid&search=algorithm`

---

## 17. Graduation & Degree Conferral

### POST `/graduation/applications/`
**Roles:** STUDENT
Submit a graduation application.

**Request:**
```json
{
  "expected_graduation_date": "2026-06-15",
  "ceremony_attendance": true
}
```

**Response 201:**
```json
{
  "id": "uuid",
  "application_number": "GRAD-2026-000142",
  "student_id": "uuid",
  "program_id": "uuid",
  "status": "SUBMITTED",
  "applied_at": "2026-04-01T10:00:00Z"
}
```

**Error responses:**
- `422 GRADUATION_ELIGIBILITY_FAILED` — Student does not meet requirements
- `403 FINANCIAL_HOLD` — Outstanding fees block graduation

---

### GET `/graduation/applications/`
**Roles:** STUDENT (own), ADMIN, REGISTRAR
List graduation applications with filters.

**Query params:** `?status=SUBMITTED&program_id=uuid&semester_id=uuid`

---

### GET `/graduation/applications/{id}/`
**Roles:** STUDENT (own), ADMIN, REGISTRAR
Get application details including degree audit results.

---

### PATCH `/graduation/applications/{id}/`
**Roles:** REGISTRAR, ADMIN
Update application status (approve/reject).

**Request:**
```json
{
  "status": "APPROVED",
  "honors_classification": "MAGNA_CUM_LAUDE"
}
```

**Error responses:**
- `422 DEGREE_AUDIT_INCOMPLETE` — Pending audit requirements

---

### POST `/graduation/degree-audits/`
**Roles:** REGISTRAR, ADMIN
Run a degree audit for a student.

**Request:** `{"student_id": "uuid"}`

**Response 201:**
```json
{
  "id": "uuid",
  "student_id": "uuid",
  "program_id": "uuid",
  "status": "PASSED",
  "total_credits_required": 120,
  "total_credits_completed": 124,
  "total_credits_transferred": 12,
  "required_courses_met": true,
  "elective_credits_met": true,
  "cgpa_requirement_met": true,
  "residency_requirement_met": true,
  "holds_cleared": true,
  "missing_requirements": []
}
```

---

### POST `/graduation/degree-audits/batch/`
**Roles:** REGISTRAR
Run batch degree audit for all applicants in a graduation cycle.

**Request:** `{"semester_id": "uuid"}`

**Response 202:** `{"job_id": "uuid", "total_students": 145, "status": "QUEUED"}`

---

### POST `/graduation/diplomas/generate/`
**Roles:** REGISTRAR
Generate diplomas for approved graduates.

**Request:** `{"application_ids": ["uuid1", "uuid2"]}`

**Response 202:** `{"job_id": "uuid", "count": 2, "status": "PROCESSING"}`

---

### GET `/graduation/diplomas/{diploma_number}/verify/`
**Public.** Verify a diploma by its number.

**Response 200:**
```json
{
  "valid": true,
  "student_name": "Jane Doe",
  "program": "Bachelor of Science in Computer Science",
  "honors": "Magna Cum Laude",
  "conferred_date": "2026-06-15",
  "institution": "Example University"
}
```

---

## 18. Student Discipline & Conduct

### POST `/discipline/cases/`
**Roles:** FACULTY, ADMIN, STAFF
Report a disciplinary incident and create a case.

**Request:**
```json
{
  "student_id": "uuid",
  "incident_date": "2026-03-15",
  "violation_category": "ACADEMIC_INTEGRITY",
  "severity": "MAJOR",
  "description": "Student found using unauthorized materials during midterm exam.",
  "evidence_file_ids": ["uuid1", "uuid2"]
}
```

**Response 201:**
```json
{
  "id": "uuid",
  "case_number": "DISC-2026-000034",
  "status": "REPORTED",
  "student_id": "uuid",
  "reported_by_id": "uuid",
  "created_at": "2026-03-15T14:30:00Z"
}
```

---

### GET `/discipline/cases/`
**Roles:** ADMIN, DISCIPLINE_COMMITTEE
List disciplinary cases with filters.

**Query params:** `?status=REPORTED&severity=MAJOR&student_id=uuid`

---

### GET `/discipline/cases/{id}/`
**Roles:** ADMIN, DISCIPLINE_COMMITTEE, STUDENT (own case only)
Get case details including timeline and evidence.

---

### PATCH `/discipline/cases/{id}/`
**Roles:** ADMIN, DISCIPLINE_COMMITTEE
Update case status, assign committee, schedule hearing, issue decision.

**Request (schedule hearing):**
```json
{
  "status": "HEARING_SCHEDULED",
  "hearing_date": "2026-03-25",
  "hearing_time": "14:00",
  "hearing_room_id": "uuid",
  "panel_member_ids": ["uuid1", "uuid2", "uuid3"]
}
```

**Request (issue decision):**
```json
{
  "status": "DECISION_ISSUED",
  "sanction": "SUSPENSION",
  "sanction_details": {"duration_semesters": 1, "effective_date": "2026-04-01"},
  "decision_rationale": "Detailed reasoning..."
}
```

---

### POST `/discipline/cases/{id}/appeals/`
**Roles:** STUDENT (own case only)
Submit an appeal against a disciplinary decision.

**Request:**
```json
{
  "grounds": "DISPROPORTIONATE_SANCTION",
  "appeal_statement": "I believe the sanction is disproportionate because...",
  "evidence_file_ids": ["uuid3"]
}
```

**Error responses:**
- `403 APPEAL_WINDOW_CLOSED` — Past the 10-business-day deadline

---

### PATCH `/discipline/appeals/{id}/`
**Roles:** APPEALS_BOARD
Decide on an appeal.

**Request:**
```json
{
  "status": "DECIDED",
  "outcome": "MODIFIED",
  "modified_sanction": "PROBATION",
  "decision_rationale": "Panel determined suspension was disproportionate..."
}
```

---

## 19. Academic Standing & Progress

### GET `/students/{id}/standing/`
**Roles:** STUDENT (own), FACULTY (advisees), ADMIN
Get a student's current academic standing and history.

**Response 200:**
```json
{
  "current_standing": "GOOD_STANDING",
  "current_cgpa": 3.42,
  "deans_list": false,
  "standing_history": [
    {
      "semester": "Fall 2025",
      "semester_gpa": 3.50,
      "cgpa": 3.42,
      "standing": "GOOD_STANDING",
      "deans_list": true,
      "credits_attempted": 15,
      "credits_earned": 15
    }
  ],
  "degree_progress": {
    "total_required": 120,
    "completed": 75,
    "in_progress": 15,
    "remaining": 30,
    "percentage": 62.5
  },
  "restrictions": [],
  "max_completion_date": "2028-06-30"
}
```

---

### GET `/students/{id}/standing/at-risk/`
**Roles:** FACULTY (advisees), ADMIN
Get at-risk assessment for a student.

**Response 200:**
```json
{
  "risk_level": "MEDIUM",
  "risk_factors": [
    {"factor": "GPA_DECLINE", "detail": "GPA dropped from 3.2 to 2.8 over 2 semesters"},
    {"factor": "ATTENDANCE_LOW", "detail": "72% attendance in current semester (threshold: 75%)"}
  ],
  "interventions": [
    {"type": "ADVISING_SESSION", "date": "2026-03-01", "notes": "Discussed course load reduction"}
  ]
}
```

---

### POST `/standing/batch-calculate/`
**Roles:** ADMIN, REGISTRAR
Trigger batch academic standing calculation for all students in a semester.

**Request:** `{"semester_id": "uuid"}`

**Response 202:**
```json
{
  "job_id": "uuid",
  "total_students": 2500,
  "status": "QUEUED"
}
```

---

### GET `/standing/deans-list/`
**Roles:** ALL (authenticated)
Get Dean's List for a semester.

**Query params:** `?semester_id=uuid&program_id=uuid`

**Response 200:**
```json
{
  "semester": "Fall 2025",
  "students": [
    {"student_id": "uuid", "name": "Jane Doe", "program": "BSCS", "semester_gpa": 3.95}
  ],
  "total_count": 142
}
```

---

### POST `/students/{id}/interventions/`
**Roles:** FACULTY (advisees), ADMIN
Record an intervention for an at-risk student.

**Request:**
```json
{
  "type": "ADVISING_SESSION",
  "notes": "Discussed time management strategies. Referred to tutoring center.",
  "follow_up_date": "2026-04-15"
}
```

---

## 20. Grade Dispute & Appeal

### POST `/grade-appeals/`
**Roles:** STUDENT
Submit a grade appeal.

**Request:**
```json
{
  "enrollment_id": "uuid",
  "exam_id": "uuid",
  "original_grade": "C+",
  "requested_action": "REVALUATION",
  "justification": "I believe my essay answer for Q3 was not fully evaluated...",
  "evidence_file_ids": ["uuid1"]
}
```

**Response 201:**
```json
{
  "id": "uuid",
  "appeal_number": "GAPP-2026-000023",
  "status": "SUBMITTED",
  "current_level": "FACULTY",
  "deadline_was": "2026-02-14T23:59:59Z",
  "filed_at": "2026-02-10T09:15:00Z"
}
```

**Error responses:**
- `403 APPEAL_DEADLINE_PASSED` — More than 15 days since grade publication

---

### GET `/grade-appeals/`
**Roles:** STUDENT (own), FACULTY (assigned), DEPARTMENT_HEAD, ADMIN
List grade appeals with filters.

**Query params:** `?status=SUBMITTED&current_level=FACULTY&semester_id=uuid`

---

### GET `/grade-appeals/{id}/`
**Roles:** STUDENT (own), FACULTY (assigned), DEPARTMENT_HEAD, ADMIN
Get appeal details with full timeline.

---

### PATCH `/grade-appeals/{id}/`
**Roles:** FACULTY, DEPARTMENT_HEAD, APPEALS_COMMITTEE
Process a grade appeal at the current level.

**Request (faculty resolves):**
```json
{
  "outcome": "GRADE_MODIFIED",
  "new_grade": "B",
  "resolution_notes": "Re-examined essay Q3. Student's analysis was valid. Grade adjusted."
}
```

**Request (escalate):**
```json
{
  "action": "ESCALATE",
  "reason": "Student disagrees with faculty assessment. Escalating to Department Head."
}
```

---

## 21. Faculty Recruitment

### POST `/recruitment/postings/`
**Roles:** HR_ADMIN
Create a job posting.

**Request:**
```json
{
  "title": "Assistant Professor - Computer Science",
  "department_id": "uuid",
  "designation": "ASSISTANT_PROFESSOR",
  "employment_type": "FULL_TIME",
  "description": "Teaching and research in AI/ML...",
  "qualifications": {
    "required": {"degree": "PhD", "field": "Computer Science or related", "experience_years": 2},
    "preferred": {"publications": 5, "grants": true}
  },
  "experience_years_min": 2,
  "salary_range_min": 80000,
  "salary_range_max": 120000,
  "vacancies": 1,
  "application_deadline": "2026-05-31T23:59:59Z",
  "is_internal_only": false
}
```

**Response 201:** Full posting object with `position_number` and `status: "DRAFT"`.

---

### GET `/recruitment/postings/`
**Roles:** HR_ADMIN, PUBLIC (published only)
List job postings.

**Query params:** `?status=PUBLISHED&department_id=uuid`

---

### PATCH `/recruitment/postings/{id}/publish/`
**Roles:** HR_ADMIN
Publish a draft posting (requires budget approval).

**Error responses:**
- `422 POSITION_NOT_APPROVED` — Budget not approved

---

### POST `/recruitment/postings/{id}/applications/`
**Roles:** PUBLIC
Submit a job application.

**Request:**
```json
{
  "applicant_name": "Dr. John Smith",
  "applicant_email": "john.smith@example.com",
  "applicant_phone": "+1234567890",
  "resume_file_id": "uuid",
  "cover_letter": "I am excited to apply for...",
  "qualifications": {
    "highest_degree": "PhD",
    "field": "Computer Science",
    "university": "MIT",
    "graduation_year": 2020,
    "experience_years": 5,
    "publications_count": 12
  }
}
```

**Response 201:**
```json
{
  "id": "uuid",
  "application_number": "JAPP-2026-000089",
  "status": "APPLIED",
  "screening_score": null,
  "applied_at": "2026-04-15T10:00:00Z"
}
```

---

### GET `/recruitment/applications/`
**Roles:** HR_ADMIN
List applications with filters.

**Query params:** `?posting_id=uuid&status=SHORTLISTED&screening_passed=true`

---

### PATCH `/recruitment/applications/{id}/`
**Roles:** HR_ADMIN
Update application status (screen, shortlist, schedule interview, offer, hire, reject).

**Request (shortlist):**
```json
{
  "status": "SHORTLISTED"
}
```

**Request (schedule interview):**
```json
{
  "status": "INTERVIEW_SCHEDULED",
  "interview_date": "2026-05-10T10:00:00Z",
  "interview_room_id": "uuid",
  "panel_member_ids": ["uuid1", "uuid2", "uuid3"]
}
```

**Error responses:**
- `422 INVALID_PANEL_COMPOSITION` — Panel doesn't meet requirements

**Request (extend offer):**
```json
{
  "status": "OFFERED",
  "offer_details": {
    "salary": 95000,
    "benefits": "Standard faculty benefits package",
    "joining_date": "2026-08-01",
    "probation_months": 12
  }
}
```

---

### POST `/recruitment/applications/{id}/evaluations/`
**Roles:** FACULTY (panel member)
Submit interview evaluation.

**Request:**
```json
{
  "teaching_score": 8,
  "research_score": 9,
  "domain_knowledge_score": 8,
  "communication_score": 7,
  "overall_score": 8.2,
  "comments": "Strong research background. Good teaching demo.",
  "recommendation": "HIRE"
}
```

---

## 22. Department & Program Administration

### GET `/departments/`
**Roles:** ALL (authenticated)
List departments with optional hierarchy.

**Query params:** `?parent_faculty=Engineering&include_positions=true`

---

### POST `/departments/`
**Roles:** SUPER_ADMIN
Create a new department.

**Request:**
```json
{
  "code": "CS",
  "name": "Computer Science",
  "parent_faculty": "Faculty of Engineering",
  "sanctioned_positions": 25
}
```

---

### PATCH `/departments/{id}/`
**Roles:** ADMIN, SUPER_ADMIN
Update department details or assign head.

**Request:** `{"head_id": "uuid", "head_term_start": "2026-01-01", "head_term_end": "2028-12-31"}`

---

### POST `/curriculum/proposals/`
**Roles:** DEPARTMENT_HEAD, FACULTY
Submit a curriculum change proposal.

**Request:**
```json
{
  "program_id": "uuid",
  "change_type": "ADD_COURSE",
  "description": "Add CS450 Machine Learning as core course for BSCS program",
  "justification": "Industry demand for ML skills. Advisory board recommendation.",
  "effective_semester_id": "uuid"
}
```

**Response 201:**
```json
{
  "id": "uuid",
  "proposal_number": "CCP-2026-000012",
  "status": "DRAFT",
  "created_at": "2026-04-01T10:00:00Z"
}
```

---

### PATCH `/curriculum/proposals/{id}/`
**Roles:** DEPARTMENT_HEAD, ACADEMIC_BOARD, SENATE
Approve or reject a curriculum proposal at the current level.

**Request:** `{"status": "ACADEMIC_BOARD", "approval_notes": "Approved by department. Forwarding to academic board."}`

---

### GET `/departments/{id}/statistics/`
**Roles:** ADMIN, DEPARTMENT_HEAD
Get department statistics.

**Response 200:**
```json
{
  "department": "Computer Science",
  "total_students": 450,
  "total_faculty": 22,
  "sanctioned_positions": 25,
  "filled_positions": 22,
  "programs": 3,
  "courses_offered_current_semester": 28,
  "average_class_size": 42,
  "faculty_student_ratio": "1:20"
}
```

---

## 23. Room & Facility Management

### GET `/rooms/`
**Roles:** ALL (authenticated)
List rooms with filters.

**Query params:** `?building=Block-A&room_type=CLASSROOM&min_capacity=50&amenities=projector,AC&is_wheelchair_accessible=true`

---

### POST `/rooms/`
**Roles:** ADMIN, FACILITY_MANAGER
Register a new room.

**Request:**
```json
{
  "room_code": "BLD-A-301",
  "building": "Block A",
  "floor": 3,
  "room_number": "301",
  "room_type": "CLASSROOM",
  "capacity": 60,
  "amenities": ["projector", "whiteboard", "AC", "speakers"],
  "is_wheelchair_accessible": true
}
```

---

### POST `/room-bookings/`
**Roles:** FACULTY, STAFF, ADMIN
Book a room.

**Request:**
```json
{
  "room_id": "uuid",
  "booking_type": "MEETING",
  "purpose": "Faculty research committee meeting",
  "date": "2026-04-10",
  "start_time": "14:00",
  "end_time": "16:00",
  "expected_attendees": 12,
  "is_recurring": false
}
```

**Response 201:**
```json
{
  "id": "uuid",
  "room_code": "BLD-A-301",
  "status": "CONFIRMED",
  "date": "2026-04-10",
  "start_time": "14:00",
  "end_time": "16:00"
}
```

**Error responses:**
- `409 ROOM_ALREADY_BOOKED` — Time slot conflict
- `422 ROOM_CAPACITY_EXCEEDED` — Attendees exceed room capacity
- `409 ACADEMIC_SCHEDULE_CONFLICT` — Conflicts with class timetable

---

### GET `/room-bookings/`
**Roles:** ALL (authenticated)
List room bookings with filters.

**Query params:** `?room_id=uuid&date=2026-04-10&booking_type=MEETING`

---

### DELETE `/room-bookings/{id}/`
**Roles:** BOOKING_OWNER, ADMIN
Cancel a room booking.

---

### GET `/rooms/{id}/availability/`
**Roles:** ALL (authenticated)
Check room availability for a date range.

**Query params:** `?start_date=2026-04-10&end_date=2026-04-14`

**Response 200:**
```json
{
  "room_code": "BLD-A-301",
  "available_slots": [
    {"date": "2026-04-10", "start_time": "08:00", "end_time": "10:00"},
    {"date": "2026-04-10", "start_time": "16:00", "end_time": "18:00"}
  ],
  "booked_slots": [
    {"date": "2026-04-10", "start_time": "10:00", "end_time": "16:00", "booking_type": "ACADEMIC_CLASS"}
  ]
}
```

---

### GET `/rooms/utilization/`
**Roles:** ADMIN, FACILITY_MANAGER
Get facility utilization report.

**Query params:** `?building=Block-A&start_date=2026-03-01&end_date=2026-03-31`

**Response 200:**
```json
{
  "building": "Block A",
  "period": "March 2026",
  "rooms_total": 45,
  "average_utilization_percent": 72.5,
  "peak_hours": "09:00-12:00",
  "underutilized_rooms": [
    {"room_code": "BLD-A-501", "utilization_percent": 15.0}
  ]
}
```

---

## 24. Transfer Credits & Course Equivalency

### POST `/transfer-credits/`
**Roles:** STUDENT
Submit a transfer credit application.

**Request:**
```json
{
  "source_institution": "State University",
  "courses": [
    {
      "source_course_code": "CS201",
      "source_course_name": "Data Structures",
      "source_credits": 3,
      "source_grade": "A",
      "transcript_file_id": "uuid",
      "syllabus_file_id": "uuid"
    }
  ]
}
```

**Response 201:**
```json
{
  "transfer_ids": ["uuid1"],
  "status": "SUBMITTED",
  "submitted_at": "2026-04-01T10:00:00Z"
}
```

---

### GET `/transfer-credits/`
**Roles:** STUDENT (own), REGISTRAR, ADMIN
List transfer credit applications.

**Query params:** `?student_id=uuid&status=UNDER_REVIEW`

---

### PATCH `/transfer-credits/{id}/`
**Roles:** REGISTRAR
Evaluate a transfer credit.

**Request:**
```json
{
  "status": "APPROVED",
  "equivalent_course_id": "uuid",
  "credits_awarded": 3,
  "counts_toward_gpa": false,
  "counts_toward_graduation": true,
  "evaluation_notes": "Syllabus covers 80%+ of our CS201 content. Approved."
}
```

**Error responses:**
- `422 TRANSFER_CREDIT_LIMIT_EXCEEDED` — Exceeds 40% maximum
- `422 TRANSFER_GRADE_INSUFFICIENT` — Below minimum B grade
- `422 RESIDENCY_REQUIREMENT_NOT_MET` — Would violate 60% residency rule

---

### GET `/transfer-credits/articulation-agreements/`
**Roles:** REGISTRAR, ADMIN
List articulation agreements.

---

### POST `/transfer-credits/articulation-agreements/`
**Roles:** REGISTRAR
Create an articulation agreement.

**Request:**
```json
{
  "institution_name": "State University",
  "effective_date": "2025-01-01",
  "expiry_date": "2028-12-31",
  "course_mappings": [
    {
      "external_course_code": "CS201",
      "external_course_name": "Data Structures",
      "internal_course_id": "uuid",
      "credits_awarded": 3
    }
  ]
}
```

---

## 25. Scholarship & Financial Aid

### GET `/scholarships/`
**Roles:** ALL (authenticated)
List available scholarship programs.

**Query params:** `?type=MERIT&program_id=uuid&is_active=true`

**Response 200:**
```json
{
  "results": [
    {
      "id": "uuid",
      "name": "Dean's Merit Scholarship",
      "type": "MERIT",
      "award_amount": 50000,
      "eligibility_criteria": {"min_gpa": 3.7, "programs": ["BSCS", "BSEE"]},
      "application_deadline": "2026-05-01T23:59:59Z",
      "is_auto_award": false
    }
  ]
}
```

---

### POST `/scholarships/{id}/apply/`
**Roles:** STUDENT
Apply for a scholarship.

**Request:**
```json
{
  "supporting_documents": ["uuid1", "uuid2"],
  "statement": "I am applying for this scholarship because..."
}
```

**Response 201:**
```json
{
  "id": "uuid",
  "scholarship_name": "Dean's Merit Scholarship",
  "status": "APPLIED",
  "applied_at": "2026-04-01T10:00:00Z"
}
```

---

### GET `/scholarship-awards/`
**Roles:** STUDENT (own), FINANCIAL_AID_ADMIN
List scholarship awards.

**Query params:** `?student_id=uuid&status=AWARDED&semester_id=uuid`

---

### PATCH `/scholarship-awards/{id}/`
**Roles:** FINANCIAL_AID_ADMIN
Process scholarship award (approve, reject, disburse, revoke).

**Request (award):**
```json
{
  "status": "AWARDED",
  "award_amount": 50000,
  "disbursement_method": "FEE_ADJUSTMENT"
}
```

**Request (disburse):**
```json
{
  "status": "DISBURSED",
  "linked_invoice_id": "uuid"
}
```

**Error responses:**
- `422 INSUFFICIENT_SCHOLARSHIP_FUND` — Fund depleted
- `422 SCHOLARSHIP_EXCEEDS_FEE` — Total scholarships exceed fee amount

---

### POST `/scholarships/`
**Roles:** FINANCIAL_AID_ADMIN
Create a new scholarship program.

**Request:**
```json
{
  "name": "Dean's Merit Scholarship",
  "scholarship_type": "MERIT",
  "description": "Awarded to top performers...",
  "eligibility_criteria": {"min_gpa": 3.7, "programs": ["BSCS", "BSEE"]},
  "award_amount": 50000,
  "max_recipients": 20,
  "fund_total": 1000000,
  "renewal_criteria": {"min_gpa": 3.5, "min_credits": 12},
  "is_auto_award": false,
  "academic_year_id": "uuid"
}
```

---

### GET `/scholarships/fund-report/`
**Roles:** FINANCIAL_AID_ADMIN, ADMIN
Get fund utilization report.

**Response 200:**
```json
{
  "total_funds": 5000000,
  "total_utilized": 3200000,
  "total_remaining": 1800000,
  "by_scholarship": [
    {"name": "Dean's Merit Scholarship", "fund": 1000000, "utilized": 750000, "recipients": 15}
  ]
}
```
