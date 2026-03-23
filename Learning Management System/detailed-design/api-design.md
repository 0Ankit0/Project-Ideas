# API Design - Learning Management System

## API Style
- RESTful JSON APIs with tenant-aware authorization and role-based access checks.
- Cursor pagination for activity-heavy collections such as enrollments, attempts, and notifications.
- Idempotency keys for enrollment creation, grading publication, and certificate issuance actions.
- Learner-facing reads optimize for freshness on progress and grade visibility, while reporting remains projection-based.

## Core Endpoints

| Area | Method | Endpoint | Purpose |
|------|--------|----------|---------|
| Catalog | GET | `/api/v1/courses` | Search or list published courses |
| Catalog | POST | `/api/v1/courses` | Create course |
| Catalog | PATCH | `/api/v1/courses/{courseId}/publish` | Publish a course version |
| Enrollments | POST | `/api/v1/enrollments` | Enroll learner |
| Cohorts | POST | `/api/v1/cohorts` | Create cohort |
| Lessons | GET | `/api/v1/lessons/{lessonId}` | Retrieve learner lesson content |
| Progress | POST | `/api/v1/progress/events` | Record progress checkpoint |
| Assessments | POST | `/api/v1/assessments/{assessmentId}/attempts` | Start or submit attempt |
| Grading | POST | `/api/v1/attempts/{attemptId}/grade` | Grade attempt |
| Certificates | GET | `/api/v1/certificates/{certificateId}` | Retrieve certificate metadata |
| Reports | GET | `/api/v1/reports/cohort-performance` | Cohort analytics summary |
| Admin | PATCH | `/api/v1/admin/policies/{policyId}` | Update tenant or platform policy |

## Example: Enrollment Request

```json
{
  "tenantId": "ten_01",
  "learnerId": "usr_2001",
  "courseId": "course_44",
  "cohortId": "cohort_2026_spring",
  "enrolledBy": "usr_admin_7"
}
```

## Example: Progress Event

```json
{
  "lessonId": "lesson_900",
  "learnerId": "usr_2001",
  "eventType": "lesson_completed",
  "percentComplete": 100,
  "recordedAt": "2026-03-23T10:00:00Z"
}
```

## Authorization Notes
- Learners may access only their own enrollment, progress, assessments, and certificates.
- Staff access is scoped by tenant and role to authoring, instruction, review, or administrative surfaces.
- Grade overrides, certificate reissues, and tenant policy changes require elevated permissions and full audit logging.
