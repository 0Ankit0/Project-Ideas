# Code Guidelines — Survey and Feedback Platform

## Overview and Philosophy

These guidelines exist to ensure that every engineer on the team can read, understand, and modify any part of the codebase without context-switching overhead. Consistency is valued over personal preference. All style rules are enforced automatically by linters and type checkers in CI; no rule in this document requires subjective judgment at review time.

**Core Principles:**
- **Explicit over implicit** — types are always annotated; magic behavior is avoided
- **Fail loudly** — invalid state raises an exception; it is never silently ignored
- **Thin controllers, rich services** — routers handle HTTP concerns only; business logic lives in service classes
- **Dependency injection** — all external dependencies are injected, never instantiated inside functions
- **Test at the boundary** — unit-test service logic; integration-test HTTP endpoints

---

## Backend (FastAPI / Python) Guidelines

### Project Structure

```
services/
├── api/                          # FastAPI application
│   ├── routers/                  # HTTP route handlers (thin layer)
│   ├── services/                 # Business logic classes
│   ├── repositories/             # Database access layer
│   ├── schemas/                  # Pydantic v2 request/response models
│   ├── models/                   # SQLAlchemy ORM models
│   ├── workers/                  # Celery task definitions
│   ├── utils/                    # Shared utilities (crypto, cache, kinesis)
│   ├── core/                     # Config, database engine, dependencies
│   └── main.py                   # FastAPI app factory
├── tests/
│   ├── unit/                     # Service and utility unit tests
│   ├── integration/              # HTTP endpoint tests using AsyncClient
│   └── factories/                # factory_boy model factories
├── migrations/                   # Alembic migration scripts
├── pyproject.toml
└── Dockerfile
```

### FastAPI Router Pattern

Routers must use `APIRouter` with explicit `prefix` and `tags`. Route functions must be `async`, use typed parameters, and delegate all logic to the service layer. No database queries or business logic in route functions.

```python
from fastapi import APIRouter, Depends, status
from app.core.dependencies import get_session, get_current_user, require_plan
from app.surveys.schemas import SurveyCreateSchema, SurveyUpdateSchema, SurveySchema
from app.surveys.service import SurveyService
from app.users.models import User

router = APIRouter(prefix="/surveys", tags=["surveys"])


@router.post("", response_model=SurveySchema, status_code=status.HTTP_201_CREATED)
async def create_survey(
    body: SurveyCreateSchema,
    session=Depends(get_session),
    current_user: User = Depends(get_current_user),
    _plan: None = Depends(require_plan("free")),
) -> SurveySchema:
    return await SurveyService(session).create(
        owner_id=current_user.id, workspace_id=current_user.workspace_id, data=body
    )


@router.patch("/{survey_id}", response_model=SurveySchema)
async def update_survey(
    survey_id: str, body: SurveyUpdateSchema,
    session=Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> SurveySchema:
    return await SurveyService(session).update(survey_id=survey_id, actor=current_user, data=body)
```

### Pydantic v2 Schema Patterns

Use `model_validator` for cross-field validation and `field_validator` for single-field rules. Never use `validator` (v1 API). All schemas must define `model_config` explicitly.

```python
from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic import ConfigDict
from app.surveys.enums import QuestionType


class QuestionCreateSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, use_enum_values=True)

    type: QuestionType
    title: str = Field(min_length=1, max_length=500)
    required: bool = False
    options: list[str] | None = None
    settings: dict = Field(default_factory=dict)

    @field_validator("options")
    @classmethod
    def validate_options_for_choice_types(
        cls, v: list[str] | None, info
    ) -> list[str] | None:
        choice_types = {QuestionType.SINGLE_CHOICE, QuestionType.MULTIPLE_CHOICE, QuestionType.RANKING}
        if info.data.get("type") in choice_types and (not v or len(v) < 2):
            raise ValueError("Choice questions require at least 2 options")
        return v

    @model_validator(mode="after")
    def nps_has_no_options(self) -> "QuestionCreateSchema":
        if self.type == QuestionType.NPS and self.options is not None:
            raise ValueError("NPS questions do not accept custom options")
        return self
```

### Async SQLAlchemy Patterns

The database engine and session factory are created once at application startup in `core/database.py`. Use `async with` context manager for session lifecycle. Never use `session.commit()` inside a repository method; commit is the service layer's responsibility (Unit of Work).

```python
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=5,
    pool_pre_ping=True,
    echo=settings.SQL_ECHO,
)

AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False)
```

### Repository Pattern

Every model has an abstract repository interface and a SQLAlchemy concrete implementation. This allows test code to inject in-memory fakes.

```python
from abc import ABC, abstractmethod
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.surveys.models import Survey


class AbstractSurveyRepository(ABC):
    @abstractmethod
    async def get_by_id(self, survey_id: UUID) -> Survey | None: ...

    @abstractmethod
    async def create(self, data: dict) -> Survey: ...

    @abstractmethod
    async def update(self, survey_id: UUID, data: dict) -> Survey | None: ...


class SQLAlchemySurveyRepository(AbstractSurveyRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, survey_id: UUID) -> Survey | None:
        result = await self._session.execute(
            select(Survey).where(
                Survey.id == survey_id,
                Survey.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def create(self, data: dict) -> Survey:
        survey = Survey(**data)
        self._session.add(survey)
        await self._session.flush()
        await self._session.refresh(survey)
        return survey
```

### Error Handling

Define custom exception classes in `core/exceptions.py`. Register FastAPI exception handlers in `main.py`. All error responses follow the envelope: `{"error_code": str, "message": str, "details": dict}`.

```python
# core/exceptions.py
from uuid import UUID


class AppError(Exception):
    error_code: str = "INTERNAL_ERROR"
    status_code: int = 500
    message: str = "An unexpected error occurred"


class SurveyNotFoundError(AppError):
    error_code = "SURVEY_NOT_FOUND"
    status_code = 404

    def __init__(self, survey_id: UUID) -> None:
        self.message = f"Survey {survey_id} not found"
        super().__init__(self.message)


# core/handlers.py
from fastapi import Request
from fastapi.responses import JSONResponse


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.error_code,
            "message": exc.message,
            "details": {},
        },
    )
```

### Logging

Use `structlog` with JSON output. Inject `correlation_id` via a `BaseHTTPMiddleware` that calls `structlog.contextvars.bind_contextvars(correlation_id=..., path=..., method=...)` at the start of each request and propagates the ID in the response header `X-Correlation-ID`. Log levels: `DEBUG` for dev, `INFO` for production. Never log PII field values directly.

### Testing

All tests use `pytest-asyncio`. HTTP endpoint tests use `httpx.AsyncClient` with `ASGITransport`. Fixtures use `factory_boy`. Never test against a real production database.

```python
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import create_app


@pytest.mark.asyncio
async def test_create_survey_returns_201(client, auth_headers):
    payload = {"title": "Customer Satisfaction Q4", "description": "Annual survey"}
    response = await client.post("/surveys", json=payload, headers=auth_headers)
    assert response.status_code == 201
    assert response.json()["status"] == "draft"
```

---

## Frontend (React / TypeScript) Guidelines

### TypeScript Conventions

- **Strict mode** is enabled in `tsconfig.json`; `"strict": true`, `"noUncheckedIndexedAccess": true`
- Never use `any`; use `unknown` and narrow explicitly
- Use `zod` for all runtime input validation (API responses, form values)
- Prefer `type` over `interface` for object shapes; use `interface` only when extending

```typescript
import { z } from 'zod'

export const surveySchema = z.object({
  id: z.string().uuid(),
  title: z.string().min(1).max(200),
  status: z.enum(['draft', 'published', 'closed', 'archived']),
  questionCount: z.number().int().min(0),
  createdAt: z.string().datetime(),
})

export type Survey = z.infer<typeof surveySchema>

// Runtime validation of API response
export function parseSurvey(raw: unknown): Survey {
  return surveySchema.parse(raw)
}
```

### Zustand Store Pattern

Use the slice pattern with `immer` middleware for immutable updates and `devtools` for Redux DevTools support. Each feature owns one store file.

```typescript
import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import { immer } from 'zustand/middleware/immer'
import type { Survey, Question } from '@/features/surveys/types'

interface SurveyBuilderState {
  survey: Survey | null
  questions: Question[]
  isDirty: boolean
  isSaving: boolean
}

interface SurveyBuilderActions {
  setSurvey: (survey: Survey) => void
  addQuestion: (question: Question) => void
  updateQuestion: (id: string, patch: Partial<Question>) => void
  reorderQuestions: (orderedIds: string[]) => void
  markClean: () => void
}

export const useSurveyBuilderStore = create<SurveyBuilderState & SurveyBuilderActions>()(
  devtools(
    immer((set) => ({
      survey: null,
      questions: [],
      isDirty: false,
      isSaving: false,

      setSurvey: (survey) =>
        set((state) => {
          state.survey = survey
          state.isDirty = false
        }),

      addQuestion: (question) =>
        set((state) => {
          state.questions.push(question)
          state.isDirty = true
        }),

      updateQuestion: (id, patch) =>
        set((state) => {
          const idx = state.questions.findIndex((q) => q.id === id)
          if (idx !== -1) {
            Object.assign(state.questions[idx], patch)
            state.isDirty = true
          }
        }),

      reorderQuestions: (orderedIds) =>
        set((state) => {
          const map = new Map(state.questions.map((q) => [q.id, q]))
          state.questions = orderedIds.map((id) => map.get(id)!).filter(Boolean)
          state.isDirty = true
        }),

      markClean: () => set((state) => { state.isDirty = false }),
    }))
  )
)
```

### react-hook-form Pattern

Always use `FormProvider` at the feature level. Child components access the form context via `useFormContext`. All schema validation is handled by `zodResolver`.

```typescript
import { FormProvider, useForm, useFormContext } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

const surveySettingsSchema = z.object({
  title: z.string().min(1, 'Title is required').max(200),
  description: z.string().max(2000).optional(),
  allowAnonymous: z.boolean(),
  closeDate: z.string().datetime().optional(),
})

type SurveySettingsValues = z.infer<typeof surveySettingsSchema>

export function SurveySettingsForm({ defaultValues }: { defaultValues: SurveySettingsValues }) {
  const methods = useForm<SurveySettingsValues>({
    resolver: zodResolver(surveySettingsSchema),
    defaultValues,
    mode: 'onBlur',
  })

  return (
    <FormProvider {...methods}>
      <form onSubmit={methods.handleSubmit(handleSave)}>
        <TitleField />
        <button type="submit" disabled={methods.formState.isSubmitting}>Save Settings</button>
      </form>
    </FormProvider>
  )
}
```

### API Layer

All HTTP calls go through a single axios instance with auth interceptor. React Query is used for server state; Zustand is used for UI/local state only.

```typescript
// api/client.ts
import axios from 'axios'
import { useAuthStore } from '@/store/authStore'
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 10_000,
})

apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

apiClient.interceptors.response.use(
  (res) => res,
  async (error) => {
    if (error.response?.status === 401) {
      await useAuthStore.getState().refreshTokens()
      return apiClient(error.config)
    }
    return Promise.reject(error)
  }
)
```

---

## Database Guidelines

### Migration Strategy

All schema changes must have a corresponding Alembic migration. Migrations must be reversible; the `downgrade()` function is required and tested against a staging database snapshot before the PR is merged. Migration files are named `{timestamp}_{short_description}.py` and stored in `migrations/versions/`.

### Naming Conventions

| Object | Convention | Example |
|--------|------------|---------|
| Tables | plural, snake_case | `survey_questions` |
| Primary keys | `id` (UUID) | `id UUID DEFAULT gen_random_uuid()` |
| Foreign keys | `{table_singular}_id` | `survey_id UUID NOT NULL` |
| Indexes | `idx_{table}_{column(s)}` | `idx_surveys_workspace_id` |
| Unique constraints | `uq_{table}_{column(s)}` | `uq_users_email` |
| Check constraints | `ck_{table}_{rule}` | `ck_answers_numeric_range` |

### Schema Standards

- **UUIDs as primary keys:** `id UUID PRIMARY KEY DEFAULT gen_random_uuid()`
- **Soft deletes:** All core tables include `deleted_at TIMESTAMPTZ NULL`; queries must always filter `WHERE deleted_at IS NULL`
- **Timestamps:** Every table has `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()` and `updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`; an `updated_at` trigger fires on every row update
- **Never `SELECT *`:** Always name columns explicitly in queries and ORM `.options(load_only(...))`
- **JSONB with GIN index:** Flexible settings columns use `JSONB`; add a GIN index when the column is queried with `@>` or `?` operators

Example `surveys` table: `id UUID PRIMARY KEY DEFAULT gen_random_uuid()`, `workspace_id UUID NOT NULL REFERENCES workspaces(id)`, `title VARCHAR(200) NOT NULL`, `status VARCHAR(20) NOT NULL DEFAULT 'draft'`, `settings JSONB NOT NULL DEFAULT '{}'`, `deleted_at TIMESTAMPTZ`, timestamps. Add `CREATE INDEX idx_surveys_workspace_id ON surveys(workspace_id)` and a partial index `WHERE deleted_at IS NULL` for status lookups.

---

## API Design Standards

### RESTful Resource Naming

- Resources are plural nouns: `/surveys`, `/questions`, `/workspaces`
- Nested resources indicate ownership: `/surveys/{id}/questions`
- Actions that don't map to CRUD use verb suffixes: `/surveys/{id}/publish`, `/surveys/{id}/duplicate`
- Query parameters for filtering: `?status=published&page=1&per_page=25`

### HTTP Status Codes

| Scenario | Code |
|----------|------|
| Resource created | 201 Created |
| Successful read or update | 200 OK |
| Successful delete | 204 No Content |
| Async task accepted | 202 Accepted |
| Validation error | 422 Unprocessable Entity |
| Authentication required | 401 Unauthorized |
| Insufficient permissions | 403 Forbidden |
| Resource not found | 404 Not Found |
| Conflict (e.g., duplicate email) | 409 Conflict |
| Plan upgrade required | 402 Payment Required |
| Rate limit exceeded | 429 Too Many Requests |

### Idempotency

All `POST` endpoints that create or trigger actions must accept an `Idempotency-Key` header. The key is stored in Redis with a 24-hour TTL; duplicate requests return the cached response with HTTP 200.

---

## Security Coding Standards

### Input Sanitization

- Use `bleach.clean()` for any user-supplied HTML content (survey descriptions, email templates)
- All database queries use SQLAlchemy ORM or parameterized `text()` — raw string interpolation into SQL is strictly prohibited
- File uploads: validate MIME type server-side using `python-magic` (not the client-supplied Content-Type header); scan with ClamAV before storing to S3

### Secrets Management

```python
import boto3
import json
from functools import lru_cache

@lru_cache(maxsize=None)
def get_secret(secret_name: str) -> dict:
    client = boto3.client("secretsmanager", region_name="us-east-1")
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response["SecretString"])
```

Never hardcode secrets. Never commit `.env` files with real credentials. Use `python-dotenv` only in local development with `.env.example` as the template.

### Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, storage_uri=settings.REDIS_URL)

@router.post("/auth/login")
@limiter.limit("10/minute")
async def login(request: Request, body: LoginSchema) -> TokenSchema:
    ...
```

### CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,  # explicit allowlist, never ["*"]
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Correlation-ID", "Idempotency-Key"],
)
```

---

## Git Workflow

### Branch Naming

| Type | Pattern | Example |
|------|---------|---------|
| Feature | `feature/TICKET-short-description` | `feature/SFP-142-conditional-logic-engine` |
| Bug fix | `fix/TICKET-short-description` | `fix/SFP-203-nps-score-off-by-one` |
| Chore | `chore/description` | `chore/upgrade-pydantic-v2` |
| Release | `release/v{major}.{minor}` | `release/v1.2` |

### Commit Message Format (Conventional Commits)

```
<type>(<scope>): <short summary>

<optional body: what and why>

<optional footer: BREAKING CHANGE or issue reference>
```

Types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `perf`, `ci`

Examples:
```
feat(surveys): add conditional logic engine with AND/OR group support

fix(auth): prevent refresh token replay after rotation

perf(analytics): add composite index on responses(survey_id, created_at)
```

### PR Template

Every pull request must complete the following checklist before requesting review:

- [ ] Description explains **what** changed and **why**
- [ ] Linked to a Jira/Linear ticket in the PR body
- [ ] Unit tests added or updated for all changed logic
- [ ] `mypy` and `ruff` pass locally before pushing
- [ ] Database migrations included if schema changed
- [ ] OpenAPI docs updated if endpoint contracts changed
- [ ] No `TODO` comments left without a ticket reference

### Required CI Checks

All of the following must pass before a PR can be merged into `main`:

| Check | Tool | Failure Threshold |
|-------|------|-------------------|
| Linting | `ruff check` | Any violation |
| Type checking | `mypy --strict` | Any error |
| Unit tests | `pytest` | Any failure or coverage <80% |
| Security scan | Trivy | Any CRITICAL or HIGH CVE |
| Frontend type check | `tsc --noEmit` | Any error |
| Frontend lint | `eslint` | Any error |
| Frontend tests | `vitest` | Any failure |

---

## Operational Policy Addendum

### A.1 Code Review Policy

All production code changes require at least one peer review. Changes to authentication, authorization, billing, and data deletion flows require two reviewers, one of whom must be the Lead Architect or a Senior Backend Engineer. Reviewers are responsible for checking correctness, security, test coverage, and adherence to these guidelines. Style-only comments (formatting, naming) should use the "Suggested change" feature; they do not block merge. Reviews must be completed within 1 business day for P1 fixes, 2 business days for features.

### A.2 Technical Debt Management

Technical debt is tracked as Jira issues with the label `tech-debt`. Each sprint allocates 15% of capacity to tech-debt items, prioritized by the Lead Architect. A `# TODO(SFP-NNN)` comment in source code is valid only when a linked ticket exists; unlinked `TODO` comments fail the CI lint check. Debt items older than 90 days without a sprint assignment are reviewed by the PM and Lead Architect for escalation or explicit deferral.

### A.3 Dependency and Security Policy

All Python and JavaScript dependencies are managed via `pyproject.toml` / `package.json` with pinned exact versions in lock files (`poetry.lock`, `package-lock.json`). Dependabot is configured to raise PRs for security patches within 48 hours. Major version upgrades require a dedicated spike ticket, regression testing in staging, and Lead Architect approval. Dependencies with known critical CVEs that have no upstream patch must be raised as a P2 incident and tracked to resolution.

### A.4 Code Documentation Standards

Public functions and classes must have docstrings following the Google style. Internal/private functions do not require docstrings but should have inline comments for non-obvious logic. Every Alembic migration must have a comment block at the top stating the purpose, the affected tables, and whether the migration is destructive. Complex SQL queries (more than 3 joins or subqueries) must have a comment explaining the business purpose and any performance considerations such as index usage.
