# Implementation Guidelines

## Overview
This document provides implementation guidelines and best practices for building the Student Information System backend.

---

## Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| API Framework | FastAPI (Python) | Async support, automatic OpenAPI docs, type-safe |
| Database | PostgreSQL | Relational data, strong ACID compliance for academic records |
| ORM | SQLAlchemy + Alembic | Mature ORM with migration management |
| Cache | Redis | Session caching, enrollment window state, waitlist management |
| Object Storage | AWS S3 | Transcripts, documents, course materials |
| Task Queue | Celery + Redis | Async notification dispatch and report generation |
| Auth | JWT (PyJWT) | Stateless authentication with refresh token rotation |
| SSO/LDAP | python-ldap / authlib | Institutional identity integration |
| PDF Generation | ReportLab / WeasyPrint | Transcript and receipt generation |
| Email | Amazon SES / SMTP | Transactional email delivery |
| SMS | Amazon SNS / Twilio | OTP and critical alerts |
| Push | FCM / APNs | Mobile push notifications |
| Testing | pytest + httpx | Unit and integration tests |
| Containerization | Docker + Kubernetes | Cloud-native deployment |

---

## Project Structure

```
sis-backend/
├── app/
│   ├── core/
│   │   ├── config.py          # Environment and app settings
│   │   ├── security.py        # JWT and auth helpers
│   │   ├── database.py        # DB session management
│   │   └── redis.py           # Redis connection
│   ├── modules/
│   │   ├── auth/              # Authentication and IAM
│   │   ├── students/          # Student management
│   │   ├── faculty/           # Faculty management
│   │   ├── courses/           # Course catalog and curriculum
│   │   ├── enrollment/        # Enrollment and scheduling
│   │   ├── grades/            # Grades and academic records
│   │   ├── attendance/        # Attendance tracking
│   │   ├── fees/              # Fee management and payments
│   │   ├── exams/             # Exam management
│   │   ├── communication/     # Announcements and messaging
│   │   ├── reports/           # Reports and analytics
│   │   └── notifications/     # Notification service
│   ├── models/                # SQLAlchemy ORM models
│   ├── schemas/               # Pydantic request/response schemas
│   ├── repositories/          # Database access layer
│   └── main.py                # FastAPI app entry point
├── migrations/                # Alembic migration files
├── tests/                     # Test suite
├── docker/                    # Docker and compose files
└── requirements.txt
```

---

## Coding Conventions

### API Endpoint Naming

- Use plural nouns for resources: `/students`, `/courses`, `/enrollments`
- Use sub-resources for nested relationships: `/students/me/grades`, `/faculty/courses/{id}/grades`
- Use verbs for actions: `/auth/login`, `/auth/otp/enable`, `/grades/{id}/submit`
- Prefix admin routes: `/admin/students`, `/admin/reports/enrollment`
- Prefix faculty routes: `/faculty/courses/{id}/attendance`
- Prefix registrar routes: `/registrar/grades/pending`

### Response Format

```python
# Standard success response
{
    "success": True,
    "data": { ... },
    "message": "Enrollment confirmed"
}

# Paginated list response
{
    "success": True,
    "data": [ ... ],
    "pagination": {
        "page": 1,
        "perPage": 20,
        "total": 150,
        "totalPages": 8
    }
}

# Error response
{
    "success": False,
    "error": {
        "code": "PREREQUISITE_NOT_MET",
        "message": "You must complete CS101 before enrolling in CS201",
        "details": { "missingCourses": ["CS101"] }
    }
}
```

### Authentication and Authorization

```python
from app.core.security import require_role, get_current_user

# Protect route by role
@router.get("/admin/students")
async def list_students(
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    ...

# Allow multiple roles
@router.get("/courses/{id}/grades")
async def get_grades(
    current_user: User = Depends(require_roles([UserRole.FACULTY, UserRole.ADMIN]))
):
    ...
```

### Database Session Management

```python
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

@router.post("/enrollments")
async def enroll(
    enrollment_data: EnrollmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_student)
):
    service = EnrollmentService(db)
    result = await service.enroll_student(current_user.student_id, enrollment_data.section_id)
    return success_response(result)
```

---

## Enrollment Window Enforcement

The enrollment window is a critical business rule. All enrollment mutations must validate that the window is open before processing.

```python
class EnrollmentService:
    async def enroll_student(self, student_id: UUID, section_id: UUID):
        # Always check enrollment window first
        window = await self.window_repo.get_active_window()
        if not window or not window.is_open:
            raise EnrollmentWindowClosed("Enrollment is not currently open")

        # Proceed with validation chain
        await self.validate_prerequisites(student_id, section_id)
        await self.check_conflicts(student_id, section_id)
        await self.check_seats(section_id)
        ...
```

---

## GPA Calculation Rules

| Grade | Grade Points |
|-------|-------------|
| A+ | 10.0 |
| A | 9.0 |
| B+ | 8.0 |
| B | 7.0 |
| C+ | 6.0 |
| C | 5.0 |
| D | 4.0 |
| F | 0.0 |

**SGPA Formula:**
```
SGPA = Σ(Credit Hours × Grade Points) / Σ(Credit Hours)
```

**CGPA Formula:**
```
CGPA = Σ(All Semester SGPA × Semester Credits) / Σ(All Semester Credits)
```

**Academic Standing Classification:**

| CGPA Range | Standing |
|-----------|----------|
| ≥ 7.0 | Good Standing |
| 5.0 – 6.99 | Warning |
| 4.0 – 4.99 | Probation |
| < 4.0 | Suspended |

---

## Attendance Threshold Rules

| Threshold | Action |
|-----------|--------|
| < 80% | Send warning to student and parent |
| < 75% | Send critical alert; notify academic advisor |
| < 65% | Flag for exam debarment; block hall ticket |

Attendance percentage is calculated per course section per student:

```
Attendance % = (Sessions Present + Sessions Late × 0.5 + Excused Sessions) / Total Sessions × 100
```

---

## Notification Events

All domain events that trigger notifications must be published through the `NotificationService`. Do not send notifications directly from business logic services.

| Event | Channels | Recipients |
|-------|---------|-----------|
| Enrollment confirmed | Email, push | Student |
| Enrollment waitlisted | Email, push | Student |
| Grade published | Email, push, websocket | Student, Parent |
| Attendance warning | Email, SMS, push | Student, Parent |
| Attendance critical | Email, SMS, push | Student, Parent, Advisor |
| Fee invoice generated | Email | Student, Parent |
| Fee payment confirmed | Email, SMS | Student |
| Transcript ready | Email, push | Student |
| Exam schedule published | Email, push | Student, Faculty |
| Financial aid decision | Email, push | Student |

---

## Error Handling

Use domain-specific exception classes. Never expose raw database or internal errors to API responses.

```python
# Domain exceptions
class EnrollmentWindowClosed(SISException): ...
class PrerequisiteNotMet(SISException): ...
class SectionFull(SISException): ...
class ScheduleConflict(SISException): ...
class GradeNotPublished(SISException): ...
class AccountHold(SISException): ...

# Global exception handler in main.py
@app.exception_handler(SISException)
async def sis_exception_handler(request, exc: SISException):
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(exc.code, exc.message, exc.details)
    )
```

---

## Security Guidelines

1. **Input Validation**: Use Pydantic models for all request body and query parameter validation
2. **SQL Injection**: Use SQLAlchemy parameterized queries; never raw SQL with user input
3. **File Upload**: Validate file type and size; store in S3 with server-side encryption
4. **Rate Limiting**: Apply rate limiting to auth endpoints (login, OTP) and public APIs
5. **Sensitive Data**: Never log student ID numbers, grades, or financial data in plain text
6. **JWT Tokens**: Use short-lived access tokens (15 min) and longer refresh tokens (7 days)
7. **Document Access**: Transcripts and receipts should be served via time-limited signed URLs
8. **FERPA Compliance**: Enforce role-based data access; log all accesses to sensitive student records

---

## Testing Strategy

```
tests/
├── unit/
│   ├── test_gpa_calculator.py
│   ├── test_prerequisite_validator.py
│   ├── test_attendance_threshold.py
│   └── test_fee_invoice_engine.py
├── integration/
│   ├── test_enrollment_api.py
│   ├── test_grade_submission_api.py
│   ├── test_fee_payment_api.py
│   └── test_transcript_api.py
└── e2e/
    ├── test_student_journey.py
    └── test_faculty_grade_flow.py
```

All critical calculations (GPA, attendance percentage, fee invoicing) must have comprehensive unit tests covering edge cases including zero-credit courses, failed grades, excused absences, and partial aid applications.
