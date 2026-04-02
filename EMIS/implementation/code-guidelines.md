# Code Guidelines — Education Management Information System

> **Version:** 1.0 | **Audience:** All engineers contributing to EMIS
> These guidelines are enforced by CI linting, architectural fitness functions, and code review. Non-compliance is a merge-blocking issue.

---

## 1. Project Structure

```
emis/
├── apps/
│   ├── core/               # Base models, utilities, middleware, mixins
│   ├── users/              # Auth, RBAC, JWT, session, permissions
│   ├── students/           # Student lifecycle management
│   ├── admissions/         # Application and enrollment workflow
│   ├── courses/            # Programs, courses, sections, enrollment
│   ├── faculty/            # Faculty profiles and management
│   ├── exams/              # Exam scheduling and grading
│   ├── attendance/         # Daily attendance tracking
│   ├── timetable/          # Class scheduling and room allocation
│   ├── lms/                # Learning management system
│   ├── finance/            # Fee management and invoicing
│   ├── payment/            # Payment gateway integration
│   ├── library/            # Library catalog and circulation
│   ├── hr/                 # HR, payroll, leave management
│   ├── hostel/             # Hostel and accommodation management
│   ├── transport/          # Transport routes and allocation
│   ├── inventory/          # Asset and stock management
│   ├── analytics/          # Analytics dashboards
│   ├── reports/            # Report generation
│   ├── notifications/      # Notification dispatch
│   ├── cms/                # Content management system
│   ├── seo/                # SEO tools
│   ├── calendar/           # Calendar management
│   ├── portal/             # Role-specific portals
│   └── files/              # File management
├── config/
│   ├── settings/
│   │   ├── base.py         # Shared settings
│   │   ├── development.py  # Dev overrides
│   │   ├── production.py   # Prod hardening
│   │   └── testing.py      # Test overrides
│   ├── urls.py
│   └── wsgi.py
├── static/                 # Static files
├── media/                  # User-uploaded files
├── templates/              # Django HTML templates
├── tests/
│   ├── conftest.py         # Global pytest fixtures
│   └── e2e/                # Playwright E2E tests
├── docker/
│   ├── Dockerfile
│   ├── Dockerfile.celery
│   └── nginx/nginx.conf
├── scripts/
│   ├── seed_data.py
│   └── create_superuser.py
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
├── .github/workflows/
│   ├── ci.yml
│   └── deploy.yml
├── manage.py
└── docker-compose.yml
```

Each `apps/*` app follows this internal layout:

```
students/
├── models.py           # Django ORM models
├── services.py         # Business logic (the authoritative layer)
├── tasks.py            # Celery async tasks
├── signals.py          # Django signals (side effects only)
├── admin.py            # Django admin configuration
├── forms.py            # Django form classes
├── views.py            # Django template views (HTML rendering)
├── urls.py             # URL patterns for template views
├── apps.py             # AppConfig
├── exceptions.py       # Domain-specific exceptions
├── constants.py        # Module-level constants and enumerations
├── api/
│   ├── serializers.py  # DRF serializers
│   ├── views.py        # DRF ViewSets
│   ├── urls.py         # DRF router URLs
│   ├── permissions.py  # Custom permission classes
│   └── filters.py      # django-filter filter classes
├── migrations/
│   └── 0001_initial.py
└── tests/
    ├── factories.py        # factory_boy model factories
    ├── test_models.py      # Unit tests for model methods
    ├── test_services.py    # Unit tests for service layer
    ├── test_api.py         # Integration tests for API endpoints
    └── test_views.py       # Integration tests for template views
```

---

## 2. Architecture Layers

### 2.1 Models Layer

**Purpose:** Data definition and database schema. Domain state and simple computed properties only.

**Rules:**
- All models inherit from `core.models.BaseModel` which provides: `id` (UUID PK), `created_at`, `updated_at`, `is_active`.
- Use `UUIDField(primary_key=True, default=uuid.uuid4, editable=False)` — never integer auto-increment PKs.
- Always define `__str__`, `class Meta` with `ordering`, `verbose_name`, and `verbose_name_plural`.
- Field naming: `lowercase_snake_case`. Avoid abbreviations (use `student_registration_number` not `reg_no`).
- **Never** use `null=True` on `CharField` or `TextField`. Use `blank=True, default=""`.
- **Always** index `ForeignKey` fields (Django does this automatically) and add `db_index=True` to any field used in `.filter()` or `.order_by()`.
- Use `choices=` with `TextChoices` or `IntegerChoices` enums for status fields — never raw string literals.
- Custom querysets and managers belong in `models.py` as a `ModelNameQuerySet` and `ModelNameManager`.
- Model methods that compute derived values are allowed (e.g., `student.calculate_cgpa()`); methods that call external services or write to other models are **not** allowed — put those in `services.py`.

**Example:**
```python
import uuid
from django.db import models
from apps.core.models import BaseModel


class StudentStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    ON_LEAVE = "ON_LEAVE", "On Leave"
    GRADUATED = "GRADUATED", "Graduated"
    WITHDRAWN = "WITHDRAWN", "Withdrawn"
    SUSPENDED = "SUSPENDED", "Suspended"
    EXPELLED = "EXPELLED", "Expelled"


class Student(BaseModel):
    student_id = models.CharField(max_length=20, unique=True, db_index=True)
    user = models.OneToOneField("users.User", on_delete=models.PROTECT, related_name="student_profile")
    program = models.ForeignKey("courses.Program", on_delete=models.PROTECT, related_name="students")
    batch = models.CharField(max_length=10)
    status = models.CharField(max_length=20, choices=StudentStatus.choices, default=StudentStatus.ACTIVE, db_index=True)
    date_of_birth = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["student_id"]
        verbose_name = "Student"
        verbose_name_plural = "Students"
        indexes = [
            models.Index(fields=["program", "batch", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.student_id} — {self.user.get_full_name()}"

    def is_eligible_for_registration(self) -> bool:
        return self.status == StudentStatus.ACTIVE and not self.has_financial_hold()
```

---

### 2.2 Services Layer

**Purpose:** Business logic. All decisions, validations, and orchestration live here.

**Rules:**
- Services are plain Python classes or module-level functions — **no** Django request/response objects.
- Each service method performs exactly one well-defined operation.
- Use `django.db.transaction.atomic()` as a context manager (not decorator) for any operation that writes to more than one table.
- Raise domain-specific exceptions defined in `exceptions.py` (e.g., `PrerequisiteNotMetError`, `CourseCapacityExceededError`).
- Services **never** import from `api/` (serializers, viewsets) or `views.py`.
- Return domain objects (model instances, dataclasses) — never raw querysets from services that are called from the API.
- Log important business events at `INFO` level with structured context (student_id, action, outcome) — **never** log PII values (names, emails, DOB, grades) directly.

**Example:**
```python
# apps/courses/services.py
import logging
from django.db import transaction
from apps.courses.models import Enrollment, CourseSection
from apps.courses.exceptions import (
    CourseCapacityExceededError,
    PrerequisiteNotMetError,
    EnrollmentWindowClosedError,
    TimetableConflictError,
)

logger = logging.getLogger(__name__)


class EnrollmentService:

    @transaction.atomic
    def enroll_student(self, student_id: str, section_id: str, semester_id: str) -> Enrollment:
        section = CourseSection.objects.select_for_update().get(id=section_id)

        if not section.has_available_seats():
            raise CourseCapacityExceededError(f"Section {section_id} is full")

        if not self._prerequisites_met(student_id, section.course):
            raise PrerequisiteNotMetError(f"Prerequisites not satisfied for course {section.course.code}")

        if self._has_timetable_conflict(student_id, section, semester_id):
            raise TimetableConflictError(f"Schedule conflict detected for section {section_id}")

        enrollment = Enrollment.objects.create(
            student_id=student_id,
            section=section,
            semester_id=semester_id,
        )
        section.increment_enrollment_count()

        logger.info(
            "student_enrolled",
            extra={"student_id": student_id, "section_id": section_id, "enrollment_id": str(enrollment.id)},
        )
        return enrollment
```

---

### 2.3 API Layer (Django REST Framework)

**Purpose:** HTTP request/response translation. Delegates to services immediately; contains no business logic.

**Rules:**
- Use `ViewSet` classes with DRF routers — do not write URL patterns manually for CRUD operations.
- All list endpoints **must** use pagination (`PageNumberPagination` or `CursorPagination` with `page_size=50, max_page_size=100`).
- Use `django-filter` for filtering; never accept arbitrary query parameters without validation.
- Permissions: every viewset must declare `permission_classes`; never rely on `DEFAULT_PERMISSION_CLASSES` alone.
- Serializers validate input; `validate_<field>` and `validate()` methods for cross-field validation.
- Catch domain exceptions in viewsets and map them to standardized HTTP error responses.
- All API responses use the envelope format: `{"success": bool, "data": {}, "message": "", "errors": {}}`.
- Version all API URLs: `/api/v1/` prefix; add `/api/v2/` only when breaking changes are required.

**Response Envelope:**
```python
# apps/core/api/mixins.py
class StandardResponseMixin:
    def success_response(self, data, message="", status=200):
        return Response({"success": True, "data": data, "message": message, "errors": {}}, status=status)

    def error_response(self, errors, message="", status=400):
        return Response({"success": False, "data": None, "message": message, "errors": errors}, status=status)
```

**Error Response Format:**
```json
{
  "success": false,
  "data": null,
  "message": "Course registration failed",
  "errors": {
    "code": "PREREQUISITES_NOT_MET",
    "detail": "You must complete CS101 before enrolling in CS201",
    "missing_courses": ["CS101"]
  }
}
```

---

### 2.4 Tasks Layer (Celery)

**Purpose:** Async and scheduled background processing. All tasks must be idempotent.

**Rules:**
- All Celery tasks use `bind=True` for access to `self.request.id` and `self.retry()`.
- Define `max_retries`, `retry_backoff=True`, and `retry_jitter=True` on every task.
- Tasks are **always** idempotent: re-running the same task with the same arguments must produce the same result with no duplicate side effects.
- Log task start, completion, and failure with `task_id` and input identifiers (entity IDs only — no PII).
- Never pass model instances to tasks — pass PKs/UUIDs and re-fetch in the task body.
- Route tasks to appropriate queues: `high_priority` (payment confirmations, grade locks), `default` (notifications, reports), `scheduled` (celery-beat periodic tasks).

**Example:**
```python
# apps/notifications/tasks.py
from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=5,
    retry_backoff=True,
    retry_jitter=True,
    queue="default",
    name="notifications.send_email_notification",
)
def send_email_notification(self, notification_id: str) -> dict:
    from apps.notifications.models import Notification
    from apps.notifications.services import EmailDispatchService

    logger.info("send_email_notification.started", extra={"task_id": self.request.id, "notification_id": notification_id})

    try:
        notification = Notification.objects.get(id=notification_id, status="PENDING")
        result = EmailDispatchService().dispatch(notification)
        logger.info("send_email_notification.completed", extra={"notification_id": notification_id, "result": result})
        return {"notification_id": notification_id, "status": "sent"}
    except Notification.DoesNotExist:
        logger.warning("send_email_notification.skipped", extra={"notification_id": notification_id, "reason": "already_processed_or_not_found"})
        return {"notification_id": notification_id, "status": "skipped"}
    except Exception as exc:
        logger.error("send_email_notification.failed", extra={"notification_id": notification_id, "error": str(exc)})
        raise self.retry(exc=exc)
```

---

## 3. Django Model Conventions

### BaseModel
Every model in every app must inherit from `BaseModel`:

```python
# apps/core/models.py
import uuid
from django.db import models


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        abstract = True
```

### Naming Conventions

| Element | Convention | Example |
|---|---|---|
| Model class | PascalCase | `SemesterEnrollment` |
| Field name | snake_case | `date_of_birth`, `registration_number` |
| ForeignKey field | `<related_model>` (singular) | `program`, `course_section` |
| ManyToMany field | `<related_model>s` (plural) | `prerequisites`, `enrolled_students` |
| Related name | `<source_model>s` | `related_name="enrollments"` |
| Manager | `<Model>Manager` | `StudentManager` |
| QuerySet | `<Model>QuerySet` | `StudentQuerySet` |

### Status Fields
Always use `TextChoices`:
```python
class ApplicationStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    SUBMITTED = "SUBMITTED", "Submitted"
    UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
    SHORTLISTED = "SHORTLISTED", "Shortlisted"
    ACCEPTED = "ACCEPTED", "Accepted"
    REJECTED = "REJECTED", "Rejected"
```

---

## 4. API Design Conventions

### URL Patterns
```
/api/v1/students/                       GET (list), POST (create)
/api/v1/students/{id}/                  GET, PATCH, DELETE
/api/v1/students/{id}/academic-history/ GET (custom action)
/api/v1/students/{id}/status/           POST (state transition)
/api/v1/enrollments/                    GET (list), POST (create)
/api/v1/enrollments/{id}/               GET, DELETE
```

### Throttle Classes
```python
# config/settings/base.py
REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "60/hour",
        "user": "1000/hour",
        "login": "10/minute",       # Applied to auth/login/
        "password_reset": "5/hour", # Applied to auth/password/reset/
    },
}
```

### Custom Exception Handler
```python
# apps/core/api/exception_handler.py
from rest_framework.views import exception_handler
from apps.courses.exceptions import (
    CourseCapacityExceededError,
    PrerequisiteNotMetError,
)

EXCEPTION_MAP = {
    CourseCapacityExceededError: ("COURSE_CAPACITY_EXCEEDED", 409),
    PrerequisiteNotMetError: ("PREREQUISITES_NOT_MET", 422),
}

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if type(exc) in EXCEPTION_MAP:
        code, status = EXCEPTION_MAP[type(exc)]
        return Response(
            {"success": False, "data": None, "message": str(exc), "errors": {"code": code}},
            status=status,
        )
    return response
```

---

## 5. Security Rules

All of the following are **mandatory**. Violations block merges.

1. **Never log PII.** Student names, email addresses, phone numbers, dates of birth, and grade values must not appear in log output. Log entity IDs only.
2. **Parameterized queries only.** Never construct SQL with string formatting. Django ORM enforces this; raw SQL must use `cursor.execute(sql, [params])`.
3. **File upload validation.** Every file upload endpoint must: validate MIME type against whitelist, enforce size limit (configurable per context), and scan using ClamAV or equivalent.
4. **Double authorization.** Every view must check both authentication (`@login_required`) and authorization (permission check). Never assume authenticated == authorized.
5. **Production settings.** `settings/production.py` must set: `DEBUG=False`, `SECURE_SSL_REDIRECT=True`, `SECURE_HSTS_SECONDS=31536000`, `SECURE_CONTENT_TYPE_NOSNIFF=True`, `X_FRAME_OPTIONS="DENY"`, `SESSION_COOKIE_SECURE=True`, `CSRF_COOKIE_SECURE=True`.
6. **Secrets from environment.** `SECRET_KEY`, database passwords, payment gateway keys, email credentials, and Redis passwords must be loaded from environment variables or a secrets manager. Never hardcode.
7. **Rate limiting on auth endpoints.** Login, password reset, and token refresh endpoints must apply throttle classes from the security rate limits above.
8. **CSRF on all state-changing views.** Template views using forms must include `{% csrf_token %}`. API endpoints using session authentication must enforce CSRF (DRF default behavior when `SessionAuthentication` is in use).
9. **Restrict Django admin URL.** Change from `/admin/` to a non-guessable path. Enforce 2FA for admin users.
10. **Audit log all privileged actions.** Grade amendments, student status changes, fee waivers, payroll approvals, and user role changes must write to the audit log with actor, action, timestamp, and reason.

---

## 6. Testing Standards

### Coverage Requirements
- Minimum **80% line and branch coverage** per app, enforced by CI gate.
- Critical paths (grade submission, fee payment, enrollment) must have **≥95% coverage**.
- Coverage reports are uploaded to CI artifacts on every run.

### Test Organization
```
tests/
├── conftest.py               # Shared fixtures: db, client, users per role
factories.py (per app)        # factory_boy factories for all models
test_models.py                # Unit tests: model methods, validators, __str__
test_services.py              # Unit tests: service layer (mock external deps)
test_api.py                   # Integration tests: full request/response cycle
test_views.py                 # Integration tests: template view rendering
```

### Naming Convention
`test_<method_or_feature>_<scenario>_<expected_outcome>`

Examples:
- `test_enroll_student_when_course_full_raises_capacity_exceeded_error`
- `test_calculate_gpa_with_repeated_course_uses_latest_grade`
- `test_fee_payment_gateway_timeout_retries_and_returns_pending_status`

### Factory Usage (factory_boy)
```python
# apps/students/tests/factories.py
import factory
from apps.students.models import Student, StudentStatus
from apps.users.tests.factories import UserFactory
from apps.courses.tests.factories import ProgramFactory


class StudentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Student

    user = factory.SubFactory(UserFactory)
    program = factory.SubFactory(ProgramFactory)
    student_id = factory.Sequence(lambda n: f"STU-2024-{n:05d}")
    batch = "2024"
    status = StudentStatus.ACTIVE
```

### Mocking External Services
```python
# Always mock payment gateways, email, SMS in tests
from unittest.mock import patch, MagicMock

@patch("apps.payment.services.StripeAdapter.create_payment_intent")
def test_initiate_payment_returns_client_secret(mock_stripe, student_factory, invoice_factory):
    mock_stripe.return_value = MagicMock(client_secret="pi_test_secret_xyz")
    ...
```

---

## 7. Performance Rules

### N+1 Query Prevention
Every list view and list API endpoint must use `select_related()` / `prefetch_related()`:
```python
# BAD — N+1: one query per student to get their program
students = Student.objects.filter(status="ACTIVE")

# GOOD
students = Student.objects.select_related("user", "program").prefetch_related("semester_enrollments").filter(status="ACTIVE")
```

Use Django Debug Toolbar in development to catch N+1 queries before they reach PR review.

### Query Budgets
| View Type | Max DB Queries Allowed |
|---|---|
| List view (paginated) | ≤ 5 queries |
| Detail view | ≤ 10 queries |
| Dashboard | ≤ 20 queries (use Redis for aggregates) |
| Report generation | No limit (runs in Celery task) |

### Caching Strategy
```python
from django.core.cache import cache

def get_course_catalog(program_id: str) -> list:
    cache_key = f"course_catalog:{program_id}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    data = list(Course.objects.filter(program_id=program_id).values())
    cache.set(cache_key, data, timeout=300)  # 5 minutes
    return data
```

Cache these views for at least 5 minutes: course catalog, timetable, academic calendar, program list.
Invalidate cache on relevant model saves via Django signals.

---

## 8. Git Commit and PR Standards

### Commit Message Format (Conventional Commits)
```
<type>(<scope>): <short description>

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`, `security`

Examples:
```
feat(students): add bulk enrollment API with prerequisite validation
fix(finance): prevent double invoice generation on concurrent requests
test(exams): add grade submission idempotency tests
security(auth): enforce rate limiting on password reset endpoint
perf(courses): add select_related to course list API to eliminate N+1
```

### PR Checklist (enforced via PR template)
- [ ] Tests added or updated for all changed code
- [ ] Coverage not reduced below 80%
- [ ] No new N+1 queries (verified with Django Debug Toolbar)
- [ ] No PII in logs (grep for common patterns)
- [ ] Database migrations are backward-compatible
- [ ] API changes are backward-compatible or versioned
- [ ] Security scan passes (`bandit`, `safety`)
- [ ] Code follows the 4-layer architecture (no business logic in views/serializers)
- [ ] All new Celery tasks are idempotent
- [ ] CHANGELOG entry added for user-facing changes
