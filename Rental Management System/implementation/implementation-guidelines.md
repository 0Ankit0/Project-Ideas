# Implementation Guidelines

## Overview
Implementation guidelines, technology stack, coding standards, and best practices for building the rental management system.

---

## Technology Stack

### Backend Services

| Component | Technology | Version |
|-----------|------------|---------|
| Runtime | Python | 3.11+ |
| Framework | FastAPI | Latest stable |
| API Layer | REST | OpenAPI 3.0 |
| Database ORM | SQLAlchemy | 2.x (async) |
| Validation | Pydantic | 2.x |
| Task Queue | Celery | Latest |
| Testing | pytest + httpx | Latest |
| Async Runtime | asyncio + uvicorn | Latest |

### Database

| Environment | Technology | Purpose |
|-------------|------------|---------|
| Production | PostgreSQL 15+ | Primary relational store |
| Testing | SQLite / PostgreSQL | Unit and integration tests |
| Caching & Queues | Redis 7 | Session cache, availability locks, task queue |

### Frontend Applications

| Application | Technology |
|-------------|------------|
| Owner Web Portal | Next.js 14 |
| Customer Web App | Next.js 14 |
| Admin Dashboard | Next.js / React |
| Staff Mobile App | Flutter / React Native |
| Customer Mobile App | Flutter / React Native |

### Infrastructure

| Component | Technology |
|-----------|------------|
| Containers | Docker |
| Orchestration | Kubernetes (EKS) |
| CI/CD | GitHub Actions + ArgoCD |
| IaC | Terraform |

---

## Project Structure

```
/services
├── api/
│   ├── app/
│   │   ├── api/            # Routers and endpoint handlers
│   │   ├── core/           # Config, security, dependencies, events
│   │   ├── models/         # SQLAlchemy ORM models
│   │   ├── schemas/        # Pydantic request/response schemas
│   │   ├── services/       # Business logic layer
│   │   ├── repositories/   # Data access layer
│   │   ├── adapters/       # External service adapters (payment, esign, etc.)
│   │   └── utils/          # Helpers and utilities
│   ├── tests/
│   │   ├── unit/
│   │   └── integration/
│   ├── alembic/            # Database migrations
│   ├── Dockerfile
│   └── pyproject.toml
│
├── worker/
│   ├── app/
│   │   ├── jobs/           # Celery task definitions
│   │   └── handlers/       # Business logic for async jobs
│   ├── Dockerfile
│   └── pyproject.toml

/apps
├── owner-portal/           # Next.js owner web portal
├── customer-web/           # Next.js customer web app
├── admin-dashboard/        # Next.js admin dashboard
└── mobile-app/             # Flutter / React Native app

/infrastructure
├── terraform/              # IaC definitions
├── k8s/                    # Kubernetes manifests
└── docker/                 # Docker Compose for local dev
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

[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N", "W", "UP"]
ignore = ["E501"]

[tool.ruff.per-file-ignores]
"tests/*" = ["S101"]
```

---

## API Implementation Pattern

### Router Layer

```python
# app/api/routers/bookings.py
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_customer
from app.schemas.booking import BookingCreate, BookingResponse
from app.services.booking_service import BookingService
from app.models.user import User

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking_data: BookingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_customer),
) -> BookingResponse:
    """Submit a new booking request for an available asset."""
    service = BookingService(db)
    return await service.create_booking(
        customer_id=current_user.id,
        data=booking_data,
    )
```

### Service Layer

```python
# app/services/booking_service.py
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.schemas.booking import BookingCreate
from app.repositories.booking_repository import BookingRepository
from app.repositories.availability_repository import AvailabilityRepository
from app.services.pricing_engine import PricingEngine
from app.services.deposit_service import DepositService
from app.core.events import EventPublisher


class BookingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.booking_repo = BookingRepository(db)
        self.availability_repo = AvailabilityRepository(db)
        self.pricing_engine = PricingEngine(db)
        self.deposit_service = DepositService(db)
        self.event_publisher = EventPublisher()

    async def create_booking(
        self, customer_id: UUID, data: BookingCreate
    ) -> Booking:
        # Check availability
        available = await self.availability_repo.is_available(
            data.asset_id, data.rental_start_at, data.rental_end_at
        )
        if not available:
            raise BookingUnavailableError("Asset is not available for selected dates")

        # Calculate price
        pricing = await self.pricing_engine.calculate(
            data.asset_id, data.rental_start_at, data.rental_end_at
        )

        # Collect deposit
        deposit_ref = await self.deposit_service.hold(
            customer_id, pricing.deposit_amount, data.payment_method_id
        )

        # Lock availability
        await self.availability_repo.create_block(
            data.asset_id, data.rental_start_at, data.rental_end_at
        )

        # Persist booking
        booking = Booking(
            asset_id=data.asset_id,
            customer_user_id=customer_id,
            rental_start_at=data.rental_start_at,
            rental_end_at=data.rental_end_at,
            total_fee=pricing.total_fee,
            deposit_amount=pricing.deposit_amount,
        )
        saved = await self.booking_repo.save(booking)

        # Publish domain event
        await self.event_publisher.publish(
            "booking.created",
            {"booking_id": str(saved.id), "owner_id": str(saved.owner_user_id)},
        )
        return saved
```

### Repository Pattern

```python
# app/repositories/booking_repository.py
from uuid import UUID
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.booking import Booking


class BookingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_by_id(self, id: UUID) -> Optional[Booking]:
        query = (
            select(Booking)
            .where(Booking.id == id)
            .options(selectinload(Booking.asset))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def save(self, booking: Booking) -> Booking:
        self.db.add(booking)
        await self.db.commit()
        await self.db.refresh(booking)
        return booking

    async def find_active_past_end_time(self, current_time) -> List[Booking]:
        query = select(Booking).where(
            Booking.status == "ACTIVE",
            Booking.rental_end_at < current_time,
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
```

---

## Error Handling

### Custom Exceptions

```python
# app/core/exceptions.py
class AppException(Exception):
    def __init__(self, code: str, message: str, status_code: int = 500):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class BookingUnavailableError(AppException):
    def __init__(self, message: str = "Asset is not available for the selected dates"):
        super().__init__("BOOKING_UNAVAILABLE", message, 409)


class NotFoundException(AppException):
    def __init__(self, resource: str):
        super().__init__("NOT_FOUND", f"{resource} not found", 404)


class PaymentFailedError(AppException):
    def __init__(self, message: str = "Payment could not be processed"):
        super().__init__("PAYMENT_FAILED", message, 402)


class ForbiddenError(AppException):
    def __init__(self, message: str = "Access denied"):
        super().__init__("FORBIDDEN", message, 403)
```

---

## Database Models & Migrations

### SQLAlchemy Model Example

```python
# app/models/booking.py
import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import ForeignKey, String, Numeric, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class BookingStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    ACTIVE = "ACTIVE"
    PENDING_CLOSURE = "PENDING_CLOSURE"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"
    DECLINED = "DECLINED"


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    booking_number: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assets.id"), index=True
    )
    customer_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True
    )
    status: Mapped[BookingStatus] = mapped_column(
        SQLEnum(BookingStatus), default=BookingStatus.PENDING, index=True
    )
    rental_start_at: Mapped[datetime] = mapped_column(DateTime)
    rental_end_at: Mapped[datetime] = mapped_column(DateTime)
    total_fee: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    deposit_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    asset: Mapped["Asset"] = relationship(back_populates="bookings")
    customer: Mapped["User"] = relationship(back_populates="bookings")
    events: Mapped[list["BookingEvent"]] = relationship(back_populates="booking")
```

### Alembic Migration Commands

```bash
# Create a new migration
pipenv run alembic revision --autogenerate -m "add_bookings_table"

# Apply migrations
pipenv run alembic upgrade head

# Rollback one step
pipenv run alembic downgrade -1
```

---

## Testing Strategy

### Unit Test Example

```python
# tests/unit/services/test_booking_service.py
import pytest
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import datetime, timedelta

from app.services.booking_service import BookingService
from app.schemas.booking import BookingCreate
from app.core.exceptions import BookingUnavailableError


@pytest.fixture
def booking_service(mocker):
    service = BookingService(db=AsyncMock())
    service.availability_repo = AsyncMock()
    service.pricing_engine = AsyncMock()
    service.deposit_service = AsyncMock()
    service.booking_repo = AsyncMock()
    service.event_publisher = AsyncMock()
    return service


class TestBookingService:
    @pytest.mark.asyncio
    async def test_create_booking_success(self, booking_service):
        booking_service.availability_repo.is_available.return_value = True
        booking_service.pricing_engine.calculate.return_value = AsyncMock(
            total_fee=220.00, deposit_amount=500.00
        )
        booking_service.booking_repo.save.return_value = AsyncMock(
            id=uuid4(), owner_user_id=uuid4()
        )

        data = BookingCreate(
            asset_id=uuid4(),
            rental_start_at=datetime.utcnow() + timedelta(days=1),
            rental_end_at=datetime.utcnow() + timedelta(days=4),
            payment_method_id="pm_test",
        )
        result = await booking_service.create_booking(uuid4(), data)

        assert result is not None
        booking_service.event_publisher.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_booking_unavailable(self, booking_service):
        booking_service.availability_repo.is_available.return_value = False

        data = BookingCreate(
            asset_id=uuid4(),
            rental_start_at=datetime.utcnow() + timedelta(days=1),
            rental_end_at=datetime.utcnow() + timedelta(days=4),
            payment_method_id="pm_test",
        )
        with pytest.raises(BookingUnavailableError):
            await booking_service.create_booking(uuid4(), data)
```

---

## Pricing Engine Implementation Notes

The pricing engine applies the following algorithm for every `calculatePrice(assetId, start, end)` call:

1. Load all pricing rules for the asset
2. Compute the total duration in hours
3. For each rate type combination (hourly, daily, weekly, monthly), calculate the total cost
4. Select the combination that produces the lowest total cost (customer-friendly)
5. Apply any applicable peak pricing surcharge (where the period overlaps configured peak windows)
6. Apply discount if duration meets the minimum units threshold
7. Calculate tax based on asset category and jurisdiction rules
8. Return the full `PriceBreakdown` with all components

---

## Security Best Practices

### Input Validation (Pydantic v2)

```python
from pydantic import BaseModel, UUID4, field_validator
from datetime import datetime
from decimal import Decimal


class BookingCreate(BaseModel):
    asset_id: UUID4
    rental_start_at: datetime
    rental_end_at: datetime
    payment_method_id: str

    @field_validator("rental_end_at")
    @classmethod
    def end_must_be_after_start(cls, v, info):
        if "rental_start_at" in info.data and v <= info.data["rental_start_at"]:
            raise ValueError("rental_end_at must be after rental_start_at")
        return v
```

### RBAC Dependency

```python
# app/core/deps.py
from fastapi import Depends, HTTPException, status
from app.models.user import User, UserRole


def require_role(*roles: UserRole):
    async def checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user
    return checker


get_current_owner = require_role(UserRole.OWNER, UserRole.ADMIN)
get_current_customer = require_role(UserRole.CUSTOMER)
get_current_staff = require_role(UserRole.STAFF, UserRole.OWNER)
```

---

## CI/CD Pipeline

```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -e ".[dev]"

      - name: Lint
        run: ruff check . && black --check .

      - name: Type check
        run: mypy app/

      - name: Run tests
        run: pytest --cov=app tests/

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build Docker image
        run: docker build -t $ECR_REGISTRY/rental-api:$GITHUB_SHA .

      - name: Push to ECR
        run: |
          aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_REGISTRY
          docker push $ECR_REGISTRY/rental-api:$GITHUB_SHA

  deploy:
    needs: build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Update EKS deployment
        run: |
          kubectl set image deployment/rental-api \
            rental-api=$ECR_REGISTRY/rental-api:$GITHUB_SHA
```

---

## Performance Guidelines

1. **Availability checks** — use Redis atomic operations (SET NX with TTL) for booking availability locks to prevent double-booking race conditions
2. **Pricing engine** — cache computed pricing rules in Redis (TTL: 5 minutes) to avoid repeated DB lookups during search
3. **Asset search** — use database indexes on `category_id`, `status`, `is_published`, and `location_lat/lng` (PostGIS or bounding box queries)
4. **Pagination** — all list endpoints use cursor-based pagination; avoid large OFFSET queries
5. **Database** — route all reporting/analytics queries to RDS read replicas
6. **N+1 prevention** — use `selectinload` and `joinedload` in SQLAlchemy for relationship loading
7. **File uploads** — generate S3 pre-signed URLs and upload directly from clients; do not route binary data through the API
8. **WebSocket** — use Redis Pub/Sub to broadcast events to all WebSocket server instances in the cluster
