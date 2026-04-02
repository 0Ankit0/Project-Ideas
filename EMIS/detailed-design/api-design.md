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
