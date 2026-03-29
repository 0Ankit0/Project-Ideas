# Implementation Guidelines

## Overview
This document provides implementation guidelines, coding standards, and best practices for developing the Finance Management System. Given the regulatory and accuracy requirements of financial software, these guidelines place particular emphasis on data integrity, audit trail completeness, idempotency, and security.

---

## Technology Stack

### Backend Services

| Component | Technology | Version |
|-----------|------------|---------|
| Runtime | Python | 3.11+ |
| Framework | FastAPI | Latest |
| API Layer | REST | OpenAPI 3.0 |
| Database ORM | SQLAlchemy | 2.x |
| Validation | Pydantic | 2.x |
| Task Queue | Celery | 5.x |
| Testing | pytest + httpx | Latest |
| Async | asyncio + uvicorn | Latest |

### Database

| Environment | Technology | Purpose |
|-------------|------------|---------|
| Production | PostgreSQL 15+ | Primary transactional database |
| Audit | PostgreSQL 15+ (separate instance) | Append-only audit log |
| Testing | SQLite | Unit/integration tests |
| Caching | Redis | Sessions, FX rates, report cache |

### Frontend Applications

| Application | Technology |
|-------------|------------|
| Finance Web App | Next.js 14 |
| Admin Dashboard | Next.js / React |
| Mobile App (Expense) | Flutter |

### Infrastructure

| Component | Technology |
|-----------|------------|
| Container | Docker |
| Orchestration | Kubernetes (EKS) |
| CI/CD | GitHub Actions + ArgoCD |
| IaC | Terraform |

---

## Project Structure

```
/backend
├── src/
│   ├── api/
│   │   ├── routers/          # FastAPI routers per module
│   │   │   ├── auth.py
│   │   │   ├── gl.py
│   │   │   ├── ap.py
│   │   │   ├── ar.py
│   │   │   ├── budgeting.py
│   │   │   ├── expenses.py
│   │   │   ├── payroll.py
│   │   │   ├── assets.py
│   │   │   ├── tax.py
│   │   │   └── reports.py
│   │   └── deps.py           # Shared dependencies (db, auth, RBAC)
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py       # JWT, hashing
│   │   ├── rbac.py           # Permission enforcement
│   │   ├── database.py       # Async SQLAlchemy engine
│   │   ├── audit.py          # Audit log writer
│   │   └── exceptions.py     # Custom exception classes
│   ├── models/               # SQLAlchemy ORM models
│   │   ├── gl.py
│   │   ├── ap.py
│   │   ├── ar.py
│   │   ├── budget.py
│   │   ├── expense.py
│   │   ├── payroll.py
│   │   ├── asset.py
│   │   ├── tax.py
│   │   └── user.py
│   ├── schemas/              # Pydantic request/response models
│   ├── services/             # Business logic per module
│   ├── repositories/         # Data access layer
│   ├── workers/              # Celery task definitions
│   │   ├── report_tasks.py
│   │   ├── payroll_tasks.py
│   │   └── notification_tasks.py
│   └── utils/
│       ├── fx_rates.py       # FX rate fetching and caching
│       ├── pdf.py            # Pay stub and invoice PDF generation
│       └── bank_file.py      # ACH/NEFT file generation
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── alembic/                  # Database migrations
├── Dockerfile
└── pyproject.toml
```

---

## Coding Standards

### Python Configuration (pyproject.toml)

```toml
[tool.black]
line-length = 100
target-version = ['py311']

[tool.isort]
profile = "black"
line_length = 100

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

### Ruff Linter Configuration

```toml
[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N", "W", "UP", "S", "B"]
ignore = ["E501"]

[tool.ruff.per-file-ignores]
"tests/*" = ["S101"]
```

---

## API Implementation Pattern

### Router Layer (FastAPI)

```python
# src/api/routers/gl.py
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db, require_permission
from src.schemas.journal import JournalEntryCreate, JournalEntryResponse
from src.services.journal_service import JournalEntryService
from src.models.user import User

router = APIRouter(prefix="/gl/journal-entries", tags=["general-ledger"])


@router.post(
    "/",
    response_model=JournalEntryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_journal_entry(
    data: JournalEntryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("gl:journal:create")),
) -> JournalEntryResponse:
    """Create and post a journal entry to the General Ledger."""
    service = JournalEntryService(db)
    entry = await service.create_entry(user_id=current_user.id, data=data)
    return entry
```

### Service Layer

```python
# src/services/journal_service.py
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.gl import JournalEntry, JournalEntryStatus
from src.schemas.journal import JournalEntryCreate
from src.repositories.journal_repository import JournalRepository
from src.repositories.period_repository import PeriodRepository
from src.core.audit import AuditService
from src.core.exceptions import ValidationException, PeriodClosedException


class JournalEntryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.journal_repo = JournalRepository(db)
        self.period_repo = PeriodRepository(db)
        self.audit = AuditService(db)

    async def create_entry(
        self, user_id: int, data: JournalEntryCreate
    ) -> JournalEntry:
        # Validate balanced entry
        self._validate_balanced(data.lines)

        # Validate period is open
        period = await self.period_repo.find_by_date(data.entry_date, data.entity_id)
        if not period or period.status not in ("OPEN", "SOFT_CLOSED"):
            raise PeriodClosedException(data.entry_date)

        entry = JournalEntry(
            entity_id=data.entity_id,
            period_id=period.id,
            entry_date=data.entry_date,
            description=data.description,
            status=JournalEntryStatus.POSTED,
            prepared_by_user_id=user_id,
        )
        saved = await self.journal_repo.save(entry, data.lines)

        await self.audit.log(
            user_id=user_id,
            action="CREATE",
            entity_type="JOURNAL_ENTRY",
            entity_id=saved.id,
            before=None,
            after=saved.to_dict(),
        )
        return saved

    @staticmethod
    def _validate_balanced(lines: list) -> None:
        total_debit = sum(line.debit_amount or Decimal(0) for line in lines)
        total_credit = sum(line.credit_amount or Decimal(0) for line in lines)
        if total_debit != total_credit:
            raise ValidationException(
                "Journal entry is not balanced",
                details={"debit": str(total_debit), "credit": str(total_credit)},
            )
```

### Repository Pattern

```python
# src/repositories/journal_repository.py
from typing import Optional
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.gl import JournalEntry, JournalLine


class JournalRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_by_id(self, id: int) -> Optional[JournalEntry]:
        query = (
            select(JournalEntry)
            .where(JournalEntry.id == id)
            .options(
                selectinload(JournalEntry.lines),
                selectinload(JournalEntry.attachments),
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def save(self, entry: JournalEntry, lines: list) -> JournalEntry:
        self.db.add(entry)
        await self.db.flush()
        for line_data in lines:
            line = JournalLine(journal_entry_id=entry.id, **line_data.model_dump())
            self.db.add(line)
        await self.db.commit()
        await self.db.refresh(entry)
        return entry

    async def get_account_balance(
        self, account_id: int, as_of_date: date
    ) -> Decimal:
        # Sum all posted journal lines for the account up to the given date
        ...
```

---

## Audit Logging Pattern

Every service method that mutates financial data must call the audit logger. The audit log writes to an append-only database with an INSERT-only connection role.

```python
# src/core/audit.py
from typing import Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.audit import AuditLog


class AuditService:
    def __init__(self, db: AsyncSession):
        # This db session connects to the append-only audit database
        self.db = db

    async def log(
        self,
        user_id: int,
        action: str,
        entity_type: str,
        entity_id: int,
        before: Optional[dict],
        after: Optional[dict],
        ip_address: Optional[str] = None,
    ) -> None:
        log_entry = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            before_value_json=before,
            after_value_json=after,
            ip_address=ip_address,
        )
        self.db.add(log_entry)
        await self.db.commit()
```

---

## RBAC Permission Enforcement

```python
# src/api/deps.py
from fastapi import Depends, HTTPException, status
from src.core.rbac import RBACService
from src.core.security import get_current_user


def require_permission(permission: str):
    async def check(
        current_user=Depends(get_current_user),
        rbac: RBACService = Depends(get_rbac_service),
    ):
        if not await rbac.has_permission(current_user.id, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {permission}",
            )
        return current_user
    return check
```

---

## Idempotency for Financial Mutations

Payment run submissions and payroll disbursements must be idempotent. Use the `Idempotency-Key` header pattern:

```python
# src/api/middleware/idempotency.py
from fastapi import Request, Response
from redis.asyncio import Redis


async def idempotency_middleware(request: Request, call_next):
    idem_key = request.headers.get("Idempotency-Key")
    if idem_key and request.method == "POST":
        redis: Redis = request.app.state.redis
        cached = await redis.get(f"idem:{idem_key}")
        if cached:
            return Response(
                content=cached,
                media_type="application/json",
                status_code=200,
            )

    response = await call_next(request)

    if idem_key and response.status_code in (200, 201):
        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        await redis.setex(f"idem:{idem_key}", 86400, body)  # 24h TTL
        return Response(content=body, status_code=response.status_code, ...)

    return response
```

---

## Financial Calculation Rules

- **All monetary values** are stored as `NUMERIC(18, 4)` in PostgreSQL and handled as Python `Decimal`, never `float`
- **Exchange rate conversions** are always performed at posting time using the daily rate; the rate used is recorded on every foreign-currency journal line
- **Tax calculations** are always performed server-side using the configured tax rate table; client-provided tax amounts are rejected
- **Depreciation** is computed using the formula appropriate for each method and rounded to 2 decimal places; rounding differences are posted to a rounding adjustment account

---

## Testing Strategy

### Unit Tests

```python
# tests/unit/services/test_journal_service.py
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock
from src.services.journal_service import JournalEntryService
from src.schemas.journal import JournalEntryCreate, JournalLineCreate
from src.core.exceptions import ValidationException


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def journal_service(mock_db):
    service = JournalEntryService(mock_db)
    service.journal_repo = AsyncMock()
    service.period_repo = AsyncMock()
    service.audit = AsyncMock()
    return service


class TestJournalEntryService:
    @pytest.mark.asyncio
    async def test_create_entry_balanced(self, journal_service):
        # Arrange: balanced lines
        lines = [
            JournalLineCreate(account_id=1, debit_amount=Decimal("1000.00")),
            JournalLineCreate(account_id=2, credit_amount=Decimal("1000.00")),
        ]
        journal_service.period_repo.find_by_date.return_value = MockPeriod(status="OPEN")

        # Act
        result = await journal_service.create_entry(user_id=1, data=...)

        # Assert
        journal_service.journal_repo.save.assert_called_once()
        journal_service.audit.log.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_entry_imbalanced_raises(self, journal_service):
        lines = [
            JournalLineCreate(account_id=1, debit_amount=Decimal("1000.00")),
            JournalLineCreate(account_id=2, credit_amount=Decimal("900.00")),
        ]
        with pytest.raises(ValidationException) as exc_info:
            JournalEntryService._validate_balanced(lines)

        assert "not balanced" in str(exc_info.value)
```

### Integration Tests

```python
# tests/integration/test_gl_api.py
import pytest
from httpx import AsyncClient
from src.main import app
from tests.utils import get_test_token


@pytest.fixture(scope="module")
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


class TestJournalEntryAPI:
    @pytest.mark.asyncio
    async def test_create_balanced_entry_returns_201(self, client):
        token = await get_test_token(role="accountant")
        response = await client.post(
            "/api/v1/gl/journal-entries",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "entity_id": "ent-001",
                "entry_date": "2024-01-15",
                "description": "January rent accrual",
                "lines": [
                    {"account_id": "acct-rent-exp", "debit_amount": "5000.00"},
                    {"account_id": "acct-rent-payable", "credit_amount": "5000.00"},
                ],
            },
        )
        assert response.status_code == 201
        assert response.json()["data"]["status"] == "POSTED"
```

---

## CI/CD Pipeline

```yaml
# .github/workflows/ci.yml
name: Finance System CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: test_finance
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: pip install -e ".[dev]"
      - name: Lint
        run: ruff check . && mypy src
      - name: Run tests
        run: pytest --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v4
```

---

## Security Best Practices

1. **Never store financial credentials or bank keys in code** — use AWS Secrets Manager
2. **Use parameterized queries via SQLAlchemy ORM** — never build raw SQL with user input
3. **Validate all monetary inputs as Decimal** — reject any non-numeric or negative values for amounts
4. **Enforce RBAC at the service layer** — not just at the router level, to prevent privilege escalation via internal calls
5. **Write to the audit log in the same transaction** as the mutating operation — never async/fire-and-forget
6. **Use short-lived presigned URLs for bank files** — never expose direct S3 paths to clients
7. **Rate-limit financial mutation endpoints** — 10 req/min for payment submissions, 100 req/min for reads
8. **Validate idempotency keys are UUIDs** — to prevent key collision attacks

---

## Performance Guidelines

1. **Use database read replicas** for all reporting queries
2. **Cache FX rates in Redis** — refresh daily, serve all intra-day queries from cache
3. **Queue large report jobs** via Celery — never block the API for reports over 5 seconds
4. **Paginate all list endpoints** — maximum 100 records per page
5. **Use database-level aggregations** for trial balance and financial statements — avoid fetching all rows into memory
6. **Add composite indexes** on `(entity_id, period_id)`, `(account_id, entry_date)`, `(vendor_id, status)`, and `(user_id, entity_type)` for the most common query patterns

## Implementation-Ready Finance Control Expansion

### 1) Accounting Rule Assumptions (Detailed)
- Ledger model is strictly double-entry with balanced journal headers and line-level dimensional tagging (entity, cost-center, project, product, counterparty).
- Posting policies are versioned and time-effective; historical transactions are evaluated against the rule version active at transaction time.
- Currency handling requires transaction currency, functional currency, and optional reporting currency; FX revaluation and realized/unrealized gains are separated.
- Materiality thresholds are explicit and configurable; below-threshold variances may auto-resolve only when policy explicitly allows.

### 2) Transaction Invariants and Data Contracts
- Every command/event must include `transaction_id`, `idempotency_key`, `source_system`, `event_time_utc`, `actor_id/service_principal`, and `policy_version`.
- Mutations affecting posted books are append-only. Corrections use reversal + adjustment entries with causal linkage to original posting IDs.
- Period invariant checks: no unapproved journals in closing period, all sub-ledger control accounts reconciled, and close checklist fully attested.
- Referential invariants: every ledger line links to a provenance artifact (invoice/payment/payroll/expense/asset/tax document).

### 3) Reconciliation and Close Strategy
- Continuous reconciliation cadence:
  - **T+0/T+1** operational reconciliation (gateway, bank, processor, payroll outputs).
  - **Daily** sub-ledger to GL tie-out.
  - **Monthly/Quarterly** close certification with controller sign-off.
- Exception taxonomy is mandatory: timing mismatch, mapping/config error, duplicate, missing source event, external counterparty variance, FX rounding.
- Close blockers are machine-detectable and surfaced on a close dashboard with ownership, ETA, and escalation policy.

### 4) Failure Handling and Operational Recovery
- Posting pipeline uses outbox/inbox patterns with deterministic retries and dead-letter quarantine for non-retriable payloads.
- Duplicate delivery and partial failure scenarios must be proven safe through idempotency and compensating accounting entries.
- Incident runbooks require: containment decision, scope quantification, replay/rebuild method, reconciliation rerun, and financial controller approval.
- Recovery drills must be executed periodically with evidence retained for audit.

### 5) Regulatory / Compliance / Audit Expectations
- Controls must support segregation of duties, least privilege, and end-to-end tamper-evident audit trails.
- Retention strategy must satisfy jurisdictional requirements for financial records, tax documents, and payroll artifacts.
- Sensitive data handling includes classification, masking/tokenization for non-production, and secure export controls.
- Every policy override (manual journal, reopened period, emergency access) requires reason code, approver, and expiration window.

### 6) Data Lineage & Traceability (Requirements → Implementation)
- Maintain an explicit traceability matrix for this artifact (`implementation/implementation-guidelines.md`):
  - `Requirement ID` → `Business Rule / Event` → `Design Element` (API/schema/diagram component) → `Code Module` → `Test Evidence` → `Control Owner`.
- Lineage metadata minimums: source event ID, transformation ID/version, posting rule version, reconciliation batch ID, and report consumption path.
- Any change touching accounting semantics must include impact analysis across upstream requirements and downstream close/compliance reports.
- Documentation updates are blocking for release when they alter financial behavior, posting logic, or reconciliation outcomes.

### 7) Phase-Specific Implementation Readiness
- Require feature flags for risky accounting behaviors (auto-post, auto-close, auto-writeoff) with dual-control enablement.
- Instrument critical paths with domain metrics (unposted queue depth, reconciliation break count, close blockers, duplicate suppression).
- Provide migration and rollback playbooks for rule-engine, chart-of-accounts, and tax-rate changes.

### 8) Implementation Checklist for `implementation guidelines`
- [ ] Control objectives and success/failure criteria are explicit and testable.
- [ ] Data contracts include mandatory identifiers, timestamps, and provenance fields.
- [ ] Reconciliation logic defines cadence, tolerances, ownership, and escalation.
- [ ] Operational runbooks cover retries, replay, backfill, and close re-certification.
- [ ] Compliance evidence artifacts are named, retained, and linked to control owners.


