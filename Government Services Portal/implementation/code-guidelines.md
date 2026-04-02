# Code Guidelines — Government Services Portal

## Overview and Coding Philosophy

These guidelines establish the non-negotiable standards for all code contributed to the Government Services Portal. Every line of code in this system is ultimately executed on behalf of Nepali citizens interacting with their government; therefore, three principles govern every design decision:

**Readability over cleverness.** Government software has long maintenance horizons. Code that a mid-level developer can understand, audit, and modify safely is more valuable than code that is clever or terse. Variable names should be unambiguous, functions should do one thing, and complex logic must be documented with inline comments explaining *why*, not *what*.

**Security by default.** The portal handles NID-linked identities, government-issued certificates, and financial transactions. Security is not a layer added at the end — it is a constraint that shapes every design choice from day one. Validate all inputs, encode all outputs, log no PII, assume all external APIs are hostile.

**Government compliance.** Code must comply with MeitY's GIGW 2.0 accessibility standards, the IT Act 2000, the Personal Data Protection framework, and NIC security policies. Compliance requirements are treated as hard requirements, not optional features.

---

## Python/Django Backend Guidelines

### Code Formatting and Style Enforcement

All Python code must be formatted with **Black** (line length 88), import-sorted with **isort** (Black-compatible profile), and linted with **flake8** (with `flake8-bugbear`). These checks run as required CI status checks; PRs failing these checks are not mergeable.

**`pyproject.toml` (project root):**
```toml
[tool.black]
line-length = 88
target-version = ["py311"]
include = '\.pyi?$'
exclude = '''/(migrations|\.venv)/'''

[tool.isort]
profile = "black"
known_first_party = ["apps", "config"]
skip = ["migrations"]

[tool.mypy]
python_version = "3.11"
strict = true
ignore_missing_imports = false
plugins = ["mypy_django_plugin.main", "mypy_drf_plugin.main"]

[mypy.plugins.django-stubs]
django_settings_module = "config.settings.base"
```

**`.flake8`:**
```ini
[flake8]
max-line-length = 88
extend-ignore = E203, W503
per-file-ignores =
    tests/*: S101
    */migrations/*: E501
```

### Type Hints (PEP 484) — Required for All Function Signatures

Every function and method must include full type annotations. This is enforced by mypy in strict mode. No `Any` types are permitted without a `# type: ignore[assignment]` comment explaining why it is unavoidable.

```python
# Correct
def calculate_fee(
    service: "Service",
    citizen: "CitizenProfile",
    *,
    apply_exemptions: bool = True,
) -> Decimal:
    ...

# Wrong — missing type hints, not acceptable
def calculate_fee(service, citizen, apply_exemptions=True):
    ...
```

Use `from __future__ import annotations` at the top of every Python file to enable PEP 563 deferred evaluation, avoiding circular import issues with type hints.

### Django App Structure

Every Django app follows this exact directory structure:

```
apps/{app_name}/
├── __init__.py
├── apps.py
├── admin.py
├── models.py
├── serializers.py
├── views.py
├── urls.py
├── permissions.py
├── services.py          # All business logic lives here
├── tasks.py             # Celery tasks
├── selectors.py         # Complex querysets / read operations
├── exceptions.py        # App-specific exception classes
├── validators.py        # Custom field / object validators
├── filters.py           # django-filter FilterSet classes
├── signals.py           # Django signals (use sparingly)
├── migrations/
└── tests/
    ├── __init__.py
    ├── test_models.py
    ├── test_views.py
    ├── test_services.py
    ├── test_serializers.py
    ├── test_tasks.py
    └── factories.py     # factory-boy model factories
```

The `services.py` / `selectors.py` split follows the HackSoftware Django styleguide. Services mutate province; selectors read province.

### Model Conventions

**Rule 1: Always use UUID primary keys.** Never use auto-increment integer PKs for citizen-facing models. This prevents enumeration attacks and simplifies federation.

**Rule 2: Always inherit from `TimeStampedModel`.** Every model must have `created_at` and `updated_at` fields.

**Rule 3: Always define `verbose_name` and `verbose_name_plural` in `Meta`.** This makes the Django admin readable.

**Rule 4: Never use `null=True` on string fields.** Use `blank=True, default=""` instead to avoid the two-empty-value problem.

**Rule 5: Always define `__str__`** returning a human-readable representation.

**Rule 6: Define `ordering` in `Meta`** to ensure deterministic query results.

**Example — `CitizenProfile` model:**
```python
from __future__ import annotations

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel


class CitizenProfileQuerySet(models.QuerySet["CitizenProfile"]):
    def verified_aadhaar(self) -> "CitizenProfileQuerySet":
        return self.filter(is_aadhaar_verified=True)

    def active(self) -> "CitizenProfileQuerySet":
        return self.filter(is_active=True)


class CitizenProfileManager(models.Manager["CitizenProfile"]):
    def get_queryset(self) -> CitizenProfileQuerySet:
        return CitizenProfileQuerySet(self.model, using=self._db)

    def verified_aadhaar(self) -> CitizenProfileQuerySet:
        return self.get_queryset().verified_aadhaar()


class LastLoginMethod(models.TextChoices):
    AADHAAR = "AADHAAR", _("NID OTP")
    EMAIL = "EMAIL", _("Email OTP")
    SMS = "SMS", _("SMS OTP")
    DIGILOCKER = "DIGILOCKER", _("Nepal Document Wallet (NDW)")


class CitizenProfile(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    aadhaar_hash = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        verbose_name=_("NID hash"),
        help_text=_("SHA-256 of the NID number. Never store raw NID."),
    )
    phone_number = models.CharField(
        max_length=15,
        unique=True,
        verbose_name=_("Mobile number"),
        help_text=_("E.164 format, e.g. +9779876543210"),
    )
    email = models.EmailField(
        blank=True,
        default="",
        verbose_name=_("Email address"),
    )
    full_name = models.CharField(max_length=100, verbose_name=_("Full name"))
    digilocker_uid = models.CharField(
        max_length=64,
        blank=True,
        default="",
        db_index=True,
        verbose_name=_("Nepal Document Wallet (NDW) UID"),
    )
    is_phone_verified = models.BooleanField(default=False, verbose_name=_("Phone verified"))
    is_email_verified = models.BooleanField(default=False, verbose_name=_("Email verified"))
    is_aadhaar_verified = models.BooleanField(default=False, verbose_name=_("NID verified"))
    aadhaar_verified_at = models.DateTimeField(null=True, blank=True)
    last_login_method = models.CharField(
        max_length=20,
        choices=LastLoginMethod.choices,
        blank=True,
        default="",
        verbose_name=_("Last login method"),
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))

    objects: CitizenProfileManager = CitizenProfileManager()

    class Meta:
        verbose_name = _("Citizen Profile")
        verbose_name_plural = _("Citizen Profiles")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["phone_number"], name="idx_citizen_phone"),
            models.Index(fields=["aadhaar_hash"], name="idx_citizen_aadhaar_hash"),
        ]

    def __str__(self) -> str:
        return f"{self.full_name} ({self.phone_number})"
```

### QuerySet Optimization — Avoiding N+1 Queries

**Rule:** Every view that returns a list of objects must use `select_related` (for ForeignKey/OneToOne) and `prefetch_related` (for ManyToMany/reverse FK).

**Rule:** Use Django Debug Toolbar in development and the `django-silk` query profiler. Any endpoint making more than 10 SQL queries must be optimized before merge.

**Correct:**
```python
# selectors.py
def get_applications_for_officer(officer_id: uuid.UUID) -> QuerySet["Application"]:
    return (
        Application.objects.filter(assigned_officer_id=officer_id)
        .select_related("service__department", "citizen")
        .prefetch_related("documents", "state_history__actor")
        .only(
            "id", "reference_number", "province", "created_at", "updated_at",
            "service__name", "service__department__name",
            "citizen__full_name", "citizen__phone_number",
        )
    )
```

**Wrong — triggers N+1 queries:**
```python
applications = Application.objects.filter(assigned_officer_id=officer_id)
for app in applications:
    print(app.service.name)  # Each iteration hits the database
```

### Security Coding Rules

**Never log PII.** The following identifiers must never appear in logs, error messages, or Sentry events: NID number, OTP value, full phone number (mask as `+977XXXXXX4321`), full name, email address, bank account number.

**Always use parameterized queries.** The Django ORM uses parameterized queries by default. If raw SQL is unavoidable (should be extremely rare), use `cursor.execute(sql, params)` — never f-strings or `.format()` in SQL.

**Validate all external inputs.** Every API request body is validated through a DRF serializer before the service layer is called. Never access `request.data["field"]` directly in a view without prior serializer validation.

**Hash NID before storage:**
```python
import hashlib

def hash_aadhaar(aadhaar_number: str) -> str:
    """Return SHA-256 hex digest of the NID number."""
    return hashlib.sha256(aadhaar_number.encode("utf-8")).hexdigest()
```

### Service Layer Pattern

Business logic belongs in `services.py`, not in views or models. Views are responsible only for: parsing and validating the request, calling the service function, and returning the serialized response.

**View (thin):**
```python
class ApplicationSubmitView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsCitizenUser]

    def post(self, request: Request, application_id: uuid.UUID) -> Response:
        application = get_object_or_404(Application, id=application_id, citizen=request.citizen)
        serializer = ApplicationSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = ApplicationService.submit_application(
            application=application,
            submitted_by=request.citizen,
        )
        return Response(ApplicationDetailSerializer(result).data, status=status.HTTP_200_OK)
```

**Service (thick):**
```python
# applications/services.py
class ApplicationService:
    @staticmethod
    def submit_application(
        application: Application,
        submitted_by: CitizenProfile,
    ) -> Application:
        if application.province != ApplicationState.DRAFT:
            raise InvalidStateTransitionError(
                f"Cannot submit application in province {application.province!r}"
            )
        ApplicationValidator.validate_all_documents_uploaded(application)
        ApplicationValidator.validate_required_fields_complete(application)

        with transaction.atomic():
            application.province = ApplicationState.SUBMITTED
            application.submitted_at = timezone.now()
            application.save(update_fields=["province", "submitted_at", "updated_at"])
            ApplicationStateHistory.objects.create(
                application=application,
                from_state=ApplicationState.DRAFT,
                to_state=ApplicationState.SUBMITTED,
                actor_type=ActorType.CITIZEN,
                actor_id=submitted_by.id,
            )

        send_submission_confirmation.delay(str(application.id))
        return application
```

### Exception Handling

Define custom exception classes in `exceptions.py` for each app:

```python
# core/exceptions.py
from rest_framework.exceptions import APIException
from rest_framework import status

class GSPBaseException(APIException):
    """Base exception for all GSP custom exceptions."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "A service error occurred."
    error_code = "UNKNOWN_ERROR"

    def __init__(self, detail: str | None = None, error_code: str | None = None) -> None:
        self.detail = detail or self.default_detail
        if error_code:
            self.error_code = error_code

class InvalidStateTransitionError(GSPBaseException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "This state transition is not permitted."
    error_code = "INVALID_STATE_TRANSITION"

class OTPRateLimitExceededError(GSPBaseException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = "Too many OTP attempts. Please wait 15 minutes."
    error_code = "OTP_RATE_LIMIT_EXCEEDED"

class DocumentVirusScanFailedError(GSPBaseException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "Uploaded document failed virus scan and has been quarantined."
    error_code = "DOCUMENT_VIRUS_DETECTED"
```

### Celery Task Code Pattern

```python
# applications/tasks.py
from __future__ import annotations
import logging
import uuid
from celery import shared_task
from django.db import transaction

logger = logging.getLogger(__name__)

@shared_task(
    bind=True,
    name="applications.tasks.send_submission_confirmation",
    max_retries=3,
    default_retry_delay=60,
    queue="notification_tasks",
    acks_late=True,
)
def send_submission_confirmation(self, application_id: str) -> None:
    """Send email and SMS confirmation after successful application submission."""
    from apps.applications.models import Application
    from apps.notifications.services import NotificationService

    try:
        application = Application.objects.select_related("citizen", "service").get(
            id=uuid.UUID(application_id)
        )
        NotificationService.send_submission_confirmation(application)
        logger.info("Submission confirmation sent for application %s", application_id)
    except Application.DoesNotExist:
        logger.error("Application %s not found, cannot send confirmation", application_id)
        # Do not retry for missing objects
    except Exception as exc:
        logger.warning(
            "Failed to send confirmation for application %s: %s", application_id, exc
        )
        raise self.retry(exc=exc)
```

---

## TypeScript/Next.js Frontend Guidelines

### TypeScript Configuration

TypeScript strict mode is mandatory. Every type check must pass with zero errors before a PR can merge.

**`tsconfig.json` (strict settings):**
```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "exactOptionalPropertyTypes": true,
    "target": "ES2022",
    "lib": ["dom", "dom.iterable", "esnext"],
    "module": "esnext",
    "moduleResolution": "bundler",
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

Use `unknown` instead of `any` for values of unknown type; narrow with type guards before use.

### Component Structure

Every React component lives in its own directory following this structure:

```
src/components/ApplicationStatusBadge/
├── index.tsx          # Component implementation
├── types.ts           # Props interface and related types
└── ApplicationStatusBadge.test.tsx  # Unit tests
```

For complex components that require CSS beyond Tailwind utility classes:
```
src/components/DocumentUploader/
├── index.tsx
├── types.ts
├── styles.module.css
└── DocumentUploader.test.tsx
```

**Component rules:**
- No default exports — use named exports. This enables better refactoring tooling.
- Props interfaces are always named `{ComponentName}Props`.
- Every component that renders inside a page must be wrapped by the page's error boundary.
- Client components (`'use client'`) must be minimized; data fetching happens in Server Components.

### Example Component — `ApplicationStatusBadge`

```typescript
// src/components/ApplicationStatusBadge/types.ts
export type ApplicationState =
  | 'DRAFT'
  | 'SUBMITTED'
  | 'PAYMENT_PENDING'
  | 'PAYMENT_COMPLETE'
  | 'UNDER_REVIEW'
  | 'PENDING_CLARIFICATION'
  | 'DOCUMENT_VERIFICATION'
  | 'APPROVED'
  | 'CERTIFICATE_GENERATION'
  | 'COMPLETED'
  | 'REJECTED'
  | 'WITHDRAWN';

export interface ApplicationStatusBadgeProps {
  province: ApplicationState;
  showIcon?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}
```

```typescript
// src/components/ApplicationStatusBadge/index.tsx
import { CheckCircle, Clock, AlertCircle, XCircle, FileText } from 'lucide-react';
import { clsx } from 'clsx';
import type { ApplicationStatusBadgeProps, ApplicationState } from './types';

const STATE_CONFIG: Record<
  ApplicationState,
  { label: string; classes: string; icon: React.ComponentType<{ className?: string }> }
> = {
  DRAFT: { label: 'Draft', classes: 'bg-gray-100 text-gray-700', icon: FileText },
  SUBMITTED: { label: 'Submitted', classes: 'bg-blue-100 text-blue-700', icon: Clock },
  PAYMENT_PENDING: { label: 'Payment Pending', classes: 'bg-yellow-100 text-yellow-700', icon: AlertCircle },
  PAYMENT_COMPLETE: { label: 'Payment Complete', classes: 'bg-blue-100 text-blue-700', icon: CheckCircle },
  UNDER_REVIEW: { label: 'Under Review', classes: 'bg-indigo-100 text-indigo-700', icon: Clock },
  PENDING_CLARIFICATION: { label: 'Pending Clarification', classes: 'bg-orange-100 text-orange-700', icon: AlertCircle },
  DOCUMENT_VERIFICATION: { label: 'Verifying Documents', classes: 'bg-purple-100 text-purple-700', icon: Clock },
  APPROVED: { label: 'Approved', classes: 'bg-green-100 text-green-700', icon: CheckCircle },
  CERTIFICATE_GENERATION: { label: 'Generating Certificate', classes: 'bg-teal-100 text-teal-700', icon: Clock },
  COMPLETED: { label: 'Completed', classes: 'bg-green-100 text-green-800', icon: CheckCircle },
  REJECTED: { label: 'Rejected', classes: 'bg-red-100 text-red-700', icon: XCircle },
  WITHDRAWN: { label: 'Withdrawn', classes: 'bg-gray-100 text-gray-500', icon: XCircle },
};

const SIZE_CLASSES = { sm: 'px-2 py-0.5 text-xs', md: 'px-3 py-1 text-sm', lg: 'px-4 py-1.5 text-base' };

export function ApplicationStatusBadge({
  province,
  showIcon = true,
  size = 'md',
  className,
}: ApplicationStatusBadgeProps) {
  const config = STATE_CONFIG[province];
  const Icon = config.icon;
  return (
    <span
      role="status"
      aria-label={`Application status: ${config.label}`}
      className={clsx(
        'inline-flex items-center gap-1.5 rounded-full font-medium',
        config.classes,
        SIZE_CLASSES[size],
        className,
      )}
    >
      {showIcon && <Icon className="h-3.5 w-3.5" aria-hidden="true" />}
      {config.label}
    </span>
  );
}
```

### Custom Hooks for API Calls

```typescript
// src/hooks/useApplicationStatus.ts
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/apiClient';
import type { Application } from '@/types/application';

interface UseApplicationStatusOptions {
  applicationId: string;
  pollingIntervalMs?: number;
}

interface UseApplicationStatusResult {
  application: Application | undefined;
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
  refetch: () => void;
}

export function useApplicationStatus({
  applicationId,
  pollingIntervalMs,
}: UseApplicationStatusOptions): UseApplicationStatusResult {
  const { data, isLoading, isError, error, refetch } = useQuery<Application, Error>({
    queryKey: ['application', applicationId],
    queryFn: () =>
      apiClient.get<Application>(`/api/v1/applications/${applicationId}/`),
    enabled: !!applicationId,
    refetchInterval: pollingIntervalMs,
    staleTime: 30_000,
  });

  return { application: data, isLoading, isError, error: error ?? null, refetch };
}
```

### API Client — Typed Fetch Wrapper with JWT Refresh

```typescript
// src/lib/apiClient.ts
import { getSession, signOut } from 'next-auth/react';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? '';

class ApiClient {
  private async getHeaders(): Promise<Record<string, string>> {
    const session = await getSession();
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (session?.accessToken) {
      headers['Authorization'] = `Bearer ${session.accessToken}`;
    }
    return headers;
  }

  async get<T>(path: string): Promise<T> {
    return this.request<T>('GET', path);
  }

  async post<T>(path: string, body: unknown): Promise<T> {
    return this.request<T>('POST', path, body);
  }

  async patch<T>(path: string, body: unknown): Promise<T> {
    return this.request<T>('PATCH', path, body);
  }

  async delete<T>(path: string): Promise<T> {
    return this.request<T>('DELETE', path);
  }

  private async request<T>(method: string, path: string, body?: unknown): Promise<T> {
    const headers = await this.getHeaders();
    const response = await fetch(`${BASE_URL}${path}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      credentials: 'include',
    });

    if (response.status === 401) {
      await signOut({ redirect: true, callbackUrl: '/login' });
      throw new Error('Session expired. Please log in again.');
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiError(response.status, errorData);
    }

    if (response.status === 204) return undefined as T;
    return response.json() as Promise<T>;
  }
}

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly data: Record<string, unknown>,
  ) {
    super(`API error ${status}`);
    this.name = 'ApiError';
  }
}

export const apiClient = new ApiClient();
```

### Form Handling — react-hook-form + zod

```typescript
// src/components/OTPVerifyForm/index.tsx
'use client';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const otpSchema = z.object({
  otp: z
    .string()
    .length(6, 'OTP must be exactly 6 digits')
    .regex(/^\d{6}$/, 'OTP must contain only digits'),
});

type OTPFormValues = z.infer<typeof otpSchema>;

interface OTPVerifyFormProps {
  onVerify: (otp: string) => Promise<void>;
  isLoading: boolean;
}

export function OTPVerifyForm({ onVerify, isLoading }: OTPVerifyFormProps) {
  const { register, handleSubmit, formState: { errors } } = useForm<OTPFormValues>({
    resolver: zodResolver(otpSchema),
  });

  const onSubmit = async (values: OTPFormValues) => {
    await onVerify(values.otp);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate aria-label="OTP verification form">
      <div>
        <label htmlFor="otp" className="block text-sm font-medium text-gray-700">
          Enter OTP
        </label>
        <input
          {...register('otp')}
          id="otp"
          type="text"
          inputMode="numeric"
          autoComplete="one-time-code"
          maxLength={6}
          aria-describedby={errors.otp ? 'otp-error' : undefined}
          aria-invalid={!!errors.otp}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
        />
        {errors.otp && (
          <p id="otp-error" role="alert" className="mt-1 text-sm text-red-600">
            {errors.otp.message}
          </p>
        )}
      </div>
      <button type="submit" disabled={isLoading} aria-busy={isLoading}>
        {isLoading ? 'Verifying...' : 'Verify OTP'}
      </button>
    </form>
  );
}
```

### Accessibility Requirements

Every PR that touches frontend components must satisfy:
- All interactive elements (buttons, links, inputs) are operable by keyboard (Tab, Enter, Space, arrow keys where appropriate).
- Every `<input>` and `<select>` has a programmatically associated `<label>` (via `htmlFor`/`id`, not `aria-label` unless absolutely necessary).
- Colour is never the sole means of conveying information (error provinces also use icons and text, not just red colour).
- Modal dialogs trap focus using `@headlessui/react`'s `Dialog` component.
- All images that convey information have descriptive `alt` text.
- All ARIA roles and properties must be used correctly (do not add `role="button"` to a `<div>` — use an actual `<button>`).
- ARIA live regions (`aria-live="polite"`) are used for dynamic content updates (toast notifications, status changes).

---

## Testing Standards

### Backend Testing (pytest-django)

**Coverage requirement:** Minimum 80% line coverage for all apps. Auth app requires 90%.

**Required test types for every Django app:**
1. **Unit tests** (`test_services.py`, `test_models.py`) — test functions in isolation with mocked dependencies.
2. **Integration tests** (`test_views.py`) — test API endpoints end-to-end against the test database using `APIClient`.
3. **Task tests** (`test_tasks.py`) — test Celery tasks with `CELERY_TASK_ALWAYS_EAGER=True` and mocked external calls.

**Test naming convention:** All test functions must follow `test_should_{expected_behavior}_when_{condition}`.

**Example test suite:**
```python
# apps/auth_app/tests/test_services.py
import pytest
from unittest.mock import MagicMock, patch
from freezegun import freeze_time
from apps.auth_app.services import NIDOTPService
from apps.auth_app.exceptions import OTPRateLimitExceededError
from apps.auth_app.tests.factories import CitizenProfileFactory

@pytest.mark.django_db
class TestNIDOTPService:

    def test_should_request_otp_when_aadhaar_is_valid(
        self, mock_uidai_client: MagicMock
    ) -> None:
        mock_uidai_client.request_otp.return_value = {"txn": "txn-123", "ret": "y"}
        service = NIDOTPService()
        result = service.request_otp(aadhaar_number="999941057058")
        assert result.transaction_id == "txn-123"
        mock_uidai_client.request_otp.assert_called_once()

    def test_should_raise_rate_limit_error_when_attempts_exceeded(
        self, redis_mock: MagicMock
    ) -> None:
        redis_mock.get.return_value = "5"  # 5 attempts already recorded
        service = NIDOTPService()
        with pytest.raises(OTPRateLimitExceededError):
            service.request_otp(aadhaar_number="999941057058")

    def test_should_return_jwt_when_otp_is_correct(
        self, mock_uidai_client: MagicMock
    ) -> None:
        mock_uidai_client.verify_otp.return_value = {"ret": "y", "name": "RAJU KUMAR"}
        citizen = CitizenProfileFactory(is_aadhaar_verified=False)
        service = NIDOTPService()
        tokens = service.verify_otp(
            aadhaar_number="999941057058",
            otp="123456",
            transaction_id="txn-123",
        )
        citizen.refresh_from_db()
        assert citizen.is_aadhaar_verified is True
        assert "access" in tokens
        assert "refresh" in tokens

    @freeze_time("2024-01-15 10:00:00")
    def test_should_not_reuse_expired_otp_when_ttl_has_passed(
        self, redis_mock: MagicMock
    ) -> None:
        redis_mock.get.return_value = None  # TTL expired, key deleted
        service = NIDOTPService()
        with pytest.raises(ValueError, match="OTP session expired"):
            service.verify_otp(
                aadhaar_number="999941057058",
                otp="123456",
                transaction_id="txn-expired",
            )
```

**`conftest.py` fixtures:**
```python
# apps/auth_app/tests/conftest.py
import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture
def mock_uidai_client():
    with patch("apps.auth_app.services.UIDaiApiClient") as mock:
        yield mock.return_value

@pytest.fixture
def redis_mock():
    with patch("apps.auth_app.services.cache") as mock:
        yield mock

@pytest.fixture
def api_client_authenticated(client, citizen_profile):
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(citizen_profile)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
    return client
```

### Frontend Testing (Jest + React Testing Library)

**Required test types:**
1. **Component unit tests** — render each component with all prop variations; test behaviour on user interaction.
2. **Hook tests** — test custom hooks using `renderHook` with mocked API responses.
3. **Page integration tests** — test full page renders with mocked API layer using `msw` (Mock Service Worker).

**Example component test:**
```typescript
// src/components/ApplicationStatusBadge/ApplicationStatusBadge.test.tsx
import { render, screen } from '@testing-library/react';
import { ApplicationStatusBadge } from './index';

describe('ApplicationStatusBadge', () => {
  it('should render the correct label when province is SUBMITTED', () => {
    render(<ApplicationStatusBadge province="SUBMITTED" />);
    expect(screen.getByRole('status', { name: /application status: submitted/i })).toBeInTheDocument();
  });

  it('should not render icon when showIcon is false', () => {
    const { container } = render(<ApplicationStatusBadge province="APPROVED" showIcon={false} />);
    expect(container.querySelector('svg')).not.toBeInTheDocument();
  });

  it('should apply large size classes when size is lg', () => {
    render(<ApplicationStatusBadge province="COMPLETED" size="lg" />);
    const badge = screen.getByRole('status');
    expect(badge).toHaveClass('px-4', 'py-1.5', 'text-base');
  });
});
```

### End-to-End Testing (Playwright)

Playwright tests cover these critical flows. Every flow must pass before a production deployment:
1. **Citizen authentication** — NID OTP request → OTP entry → JWT cookie set → redirect to dashboard.
2. **Application submission** — select service → complete multi-step form → upload document → submit → confirm reference number.
3. **Payment flow** — view challan → pay via ConnectIPS → webhook received → status updated to PAYMENT_COMPLETE.
4. **Certificate download** — approved application → download signed certificate PDF → verify PDF opens.
5. **Grievance filing** — file grievance against application → receive acknowledgement number.

---

## Git Workflow

### Branch Naming Convention

All branches must follow the pattern: `{type}/GSP-{ticket_number}-{short-description}`.

| Type | Usage |
|---|---|
| `feature/` | New feature or enhancement |
| `fix/` | Bug fix |
| `hotfix/` | Critical production fix |
| `refactor/` | Code restructure without behaviour change |
| `docs/` | Documentation only changes |
| `test/` | Adding or improving tests |
| `chore/` | Dependency updates, tooling configuration |

**Examples:**
- `feature/GSP-142-aadhaar-otp-integration`
- `fix/GSP-201-payment-webhook-signature`
- `hotfix/GSP-215-jwt-expiry-race-condition`

### Commit Message Format — Conventional Commits

```
<type>(<scope>): <short summary in imperative mood>

[Optional body: explain WHY the change was made, not WHAT]

[Optional footer: BREAKING CHANGE: <description>, Closes #GSP-XXX]
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`, `ci`, `build`

**Examples:**
```
feat(auth): add NID OTP rate limiting via Redis

Rate-limit OTP requests to 5 per 15 minutes per NID hash.
Uses Redis sorted sets for sliding window counter.
Previously, the endpoint had no rate limiting and was vulnerable
to OTP brute-force attacks.

Closes #GSP-142
```
```
fix(payments): verify ConnectIPS webhook HMAC signature before processing

Webhooks were previously processed without signature validation,
allowing spoofed events. Added HMAC-SHA256 verification using the
shared secret from Secrets Manager.

BREAKING CHANGE: Webhooks without X-ConnectIPS-Signature header now return 403.
Closes #GSP-198
```

### Pull Request Requirements

All PRs must include:
1. **Title** in Conventional Commits format.
2. **Description** explaining what changed and why.
3. **Testing** section: how was this tested? What test cases were added?
4. **Screenshots** for frontend changes (before/after).
5. **Checklist** confirming code review checklist items.
6. Link to Jira ticket: `Closes GSP-XXX`.

### Code Review Checklist (15 Items)

Reviewers must verify each item before approving:

1. **Correctness** — Does the code do what the PR description says it does?
2. **Type safety** — Are all type hints present and correct? Does mypy pass?
3. **Test coverage** — Are new code paths covered by tests? Does coverage not regress?
4. **N+1 queries** — Does any new view/selector introduce N+1 database queries?
5. **Security — auth** — Are all new endpoints protected by appropriate authentication and permission classes?
6. **Security — PII** — Does any new logging statement risk logging PII (names, phone numbers, NID)?
7. **Security — validation** — Are all external inputs validated before use?
8. **Service layer** — Is business logic in `services.py`, not in views or serializers?
9. **Error handling** — Are exceptions caught at the right level? Do errors return the structured error format?
10. **Accessibility** — Do new frontend components meet WCAG 2.1 AA requirements?
11. **i18n** — Are new frontend strings externalized to i18n message files?
12. **Migrations** — If database migrations are included, are they reversible? Are they safe to run on production without downtime?
13. **Celery tasks** — Are Celery tasks idempotent? Do they handle retries correctly?
14. **Documentation** — Are complex functions commented? Is the public API documented in the openapi spec?
15. **Dependencies** — Are any new dependencies introduced? Are they approved, maintained, and license-compatible?

---

## API Design Standards

### REST Conventions

- **URL structure:** `/api/v1/{resource}/{uuid}/{sub-resource}/`
- Resources are **plural nouns**: `/applications/`, not `/application/` or `/getApplications/`.
- Use HTTP methods semantically: GET (read), POST (create), PUT (full replace), PATCH (partial update), DELETE (delete).
- URLs are lowercase with hyphens for multi-word segments: `/service-categories/`, not `/serviceCategories/`.
- All responses are `application/json`. No XML.
- API version is in the URL path (not header): `/api/v1/`.

### HTTP Status Codes

| Status | Usage |
|---|---|
| 200 OK | Successful GET, PATCH, PUT |
| 201 Created | Successful POST that creates a resource |
| 204 No Content | Successful DELETE |
| 400 Bad Request | Validation error (invalid request body) |
| 401 Unauthorized | Missing or invalid authentication token |
| 403 Forbidden | Authenticated but not permitted |
| 404 Not Found | Resource does not exist |
| 409 Conflict | Business logic conflict (e.g., invalid state transition) |
| 422 Unprocessable Entity | Semantically invalid (e.g., virus-infected document) |
| 429 Too Many Requests | Rate limit exceeded |
| 500 Internal Server Error | Unexpected server error (should trigger Sentry alert) |

### Pagination Standard (Cursor-Based)

All list endpoints use cursor-based pagination to support stable ordering with large datasets:

```json
{
  "results": [...],
  "pagination": {
    "next_cursor": "eyJpZCI6Mzh9",
    "previous_cursor": null,
    "has_next": true,
    "has_previous": false,
    "count": 1247
  }
}
```

Default page size is 20; maximum is 100. Clients request the next page with `?cursor=eyJpZCI6Mzh9`.

### Error Response Format

All error responses return a consistent JSON structure:

```json
{
  "error": {
    "code": "INVALID_STATE_TRANSITION",
    "message": "Cannot submit an application that is already submitted.",
    "details": {
      "current_state": "SUBMITTED",
      "attempted_transition": "submit"
    },
    "request_id": "req-550e8400-e29b-41d4-a716-446655440000"
  }
}
```

The `request_id` is injected by middleware from the `X-Request-ID` header (or generated if absent) and is included in all logs for correlation.

---

## Security Coding Standards

### Input Validation Rules

1. All string fields must have explicit `max_length` enforced in the serializer.
2. All enum fields must use `ChoiceField` with an explicit choices list.
3. File uploads must validate: MIME type against an allowlist (`image/jpeg`, `image/png`, `application/pdf`), file size ≤ 5 MB, and pass ClamAV scan before being marked valid.
4. Phone numbers must be validated as E.164 format using the `phonenumbers` library.
5. NID numbers must be validated using the Verhoeff checksum algorithm before any API call.

### Secrets Management

**Never hardcode secrets.** All secrets must be loaded from environment variables at runtime:

```python
# Correct
PAYGOV_API_KEY: str = env("PAYGOV_API_KEY")

# Wrong — never do this
PAYGOV_API_KEY = "sk_live_abcdef1234567890"
```

In production, all secrets are stored in AWS Secrets Manager. The ECS task definition references secrets as environment variables injected at launch time. The `SECRET_KEY`, all API keys, and all database credentials must never appear in plaintext in source code, configuration files, Docker images, or CI/CD logs.

### Audit Logging Requirements

Every write operation that modifies citizen data or application province must emit a structured audit log entry to a dedicated `audit_logs` table and to CloudWatch Logs:

```python
# core/audit.py
import logging
from dataclasses import dataclass, asdict
from typing import Any

audit_logger = logging.getLogger("gsp.audit")

@dataclass
class AuditEvent:
    event_type: str         # "APPLICATION_STATE_CHANGED", "DOCUMENT_ACCESSED", etc.
    actor_id: str           # UUID of officer or citizen performing action
    actor_type: str         # "CITIZEN" | "OFFICER" | "SYSTEM"
    resource_type: str      # "Application", "Document", etc.
    resource_id: str        # UUID of affected resource
    request_id: str         # Correlation ID
    ip_address: str
    extra: dict[str, Any]   # Event-specific data (no PII)

def log_audit_event(event: AuditEvent) -> None:
    audit_logger.info("AUDIT", extra=asdict(event))
```

---

## Performance Guidelines

### Database Query Limits

- No endpoint may execute more than 20 SQL queries per request. Enforce this in tests with `django-assert-num-queries`.
- All queries on large tables (`applications`, `documents`) must use indexed columns in WHERE clauses. Add a DB index for any column used in filters.
- Full-text search on application notes uses PostgreSQL `tsvector`/`tsquery`; do not use `ILIKE '%term%'` on large tables.
- Bulk operations (e.g., updating 100 applications) must use `bulk_update`, never a loop of individual `.save()` calls.

### Caching Strategy

| Data | Cache Key | TTL | Invalidation |
|---|---|---|---|
| Service catalog (all services) | `services:all` | 1 hour | On Service model save signal |
| Department list | `departments:all` | 6 hours | On Department model save signal |
| Citizen profile | `citizen:{uuid}` | 5 minutes | On CitizenProfile save |
| Application state | `application:state:{uuid}` | 30 seconds | On state transition |
| Analytics dashboard data | `analytics:{dept_id}:{date}` | 2 hours | Celery beat recalculation |
| Service fee for citizen | `fee:{service_id}:{citizen_id}` | 15 minutes | On citizen profile update |

### Pagination Limits

- Maximum page size: 100 items per request (enforced in `DEFAULT_PAGINATION_CLASS`).
- Default page size: 20 items per request.
- List endpoints must never return all records without pagination.
- Celery tasks that process large querysets must use `.iterator(chunk_size=500)` to avoid loading everything into memory.

---

## Operational Policy Addendum

### 1. Citizen Data Privacy Policies

- No function, view, or service may log a citizen's NID number, raw OTP value, unmasked phone number, or full name to application logs, Sentry events, or CloudWatch Logs.
- Database access by ORM must go through the `CitizenProfile` manager's `active()` queryset; soft-deleted profiles (is_active=False) must not be returned to any API caller.
- All code that reads citizen PII (name, email, phone) must emit an audit log event with the accessor's identity.
- Frontend code must never store the JWT access token in `localStorage`; it must be stored in an `httpOnly` cookie managed by the Next.js API route layer.

### 2. Service Delivery SLA Policies

- Every API endpoint that performs a state transition must validate the new province against the allowed transition table in `state_machine.py`. No ad-hoc state assignments in `views.py` or `services.py`.
- SLA fields (`sla_due_at`) must be set at submission time based on the service's `processing_days_sla`; they must account for public holidays using the `workalendar` library configured for the relevant Nepali province.
- Service code must not hardcode SLA durations; all durations are read from the `Service.processing_days_sla` field.

### 3. Fee and Payment Policies

- Fee amounts must never be accepted from the frontend. The fee is always calculated server-side from the service's `fee_structure` JSONB.
- Payment amounts in the database must be stored as `Decimal` (Django `DecimalField`); float arithmetic is strictly forbidden for monetary calculations.
- Every payment-related function must be wrapped in `django.db.transaction.atomic()` to prevent partial writes.
- All payment gateway credentials must be loaded from Secrets Manager; they must never appear in code, `.env` files committed to Git, or CI/CD logs.

### 4. System Availability Policies

- No migration may lock a table for more than 5 seconds on production. Use `django-pg-zero-downtime-migrations` for all schema changes on large tables.
- All Celery tasks must be idempotent: running a task twice with the same arguments must produce the same result without side effects. Use database-level unique constraints to enforce this where applicable.
- Every external API call (NASC (National Identity Management Centre), Nepal Document Wallet (NDW), ConnectIPS) must have a timeout set (connect: 5s, read: 30s) and must fail gracefully with a logged error and a user-facing error message rather than an uncaught exception.
- Background jobs must not hold database transactions open while calling external APIs. Fetch data, close the transaction, then call the external API.
