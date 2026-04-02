# Implementation Playbook — Government Services Portal

## Overview and Playbook Purpose

This playbook is the authoritative, sprint-by-sprint execution guide for building the Government Services Portal (GSP). It is written for the development team, DevOps engineers, and technical project managers who are responsible for delivering a production-grade, citizen-facing digital government platform that complies with MeitY guidelines, GIGW 2.0 accessibility standards, and NIC security policy.

The portal aggregates services from multiple government departments into a single unified interface. Citizens authenticate using NID OTP or Nepal Document Wallet (NDW), apply for services such as income certificates, caste certificates, trade licences, and birth/death certificates, pay government fees through ConnectIPS, upload supporting documents, track application status in real time, and download digitally signed certificates upon approval.

The portal is built on Django 4.x + Python 3.11 (backend), Next.js 14 App Router + TypeScript (frontend), PostgreSQL 15 (primary database), Redis 7 (caching and queues), and runs entirely on AWS using ECS Fargate, RDS, ElastiCache, CloudFront, and WAF.

**How to use this playbook:**
- Each phase maps to one or two sprints (two-week iterations).
- Every phase has a task checklist, implementation notes, and acceptance criteria.
- Do not begin a phase until all acceptance criteria of the preceding phase are signed off.
- All environment variables must be provisioned in AWS Secrets Manager before their phase begins.
- Code review and merge gates enforce the guidelines in `code-guidelines.md`.

---

## Phase 0: Project Setup and Infrastructure (Sprint 1–2)

### Repository Setup

The project uses a **monorepo** layout managed with Git. The root contains both the Django backend and the Next.js frontend. A single `Makefile` provides developer convenience commands.

```
government-services-portal/
├── backend/                     # Django project
│   ├── config/                  # settings/, urls.py, wsgi.py, asgi.py
│   ├── apps/
│   │   ├── auth_app/
│   │   ├── core/
│   │   ├── services_catalog/
│   │   ├── applications/
│   │   ├── payments/
│   │   ├── documents/
│   │   ├── notifications/
│   │   ├── grievances/
│   │   ├── admin_console/
│   │   └── reports/
│   ├── requirements/
│   │   ├── base.txt
│   │   ├── dev.txt
│   │   └── prod.txt
│   ├── manage.py
│   ├── pytest.ini
│   ├── pyproject.toml           # Black, isort, flake8 config
│   └── Dockerfile
├── frontend/                    # Next.js 14 project
│   ├── src/
│   │   ├── app/                 # App Router pages
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── lib/
│   │   ├── types/
│   │   └── i18n/
│   ├── public/
│   ├── next.config.js
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── Dockerfile
├── infra/                       # Terraform / AWS CDK
│   ├── modules/
│   │   ├── ecs/
│   │   ├── rds/
│   │   ├── elasticache/
│   │   ├── s3/
│   │   ├── cloudfront/
│   │   ├── waf/
│   │   └── kms/
│   ├── environments/
│   │   ├── staging/
│   │   └── production/
│   └── main.tf
├── .github/
│   └── workflows/
│       ├── backend-ci.yml
│       ├── frontend-ci.yml
│       ├── infra-plan.yml
│       └── deploy.yml
├── docker-compose.yml           # Local development
├── Makefile
└── README.md
```

**Tasks:**
- [ ] Create GitHub repository with `main` and `develop` branch protection rules
- [ ] Enable required status checks: backend-ci, frontend-ci must pass before merge
- [ ] Configure branch protection: require 2 approvals, dismiss stale reviews
- [ ] Add CODEOWNERS file routing backend changes to backend-team, frontend to frontend-team
- [ ] Configure Dependabot for Python and npm dependency updates weekly
- [ ] Set up GitHub Environments: `staging` and `production` with required reviewers for production

### AWS Account Setup and Terraform Scaffolding

1. Create a dedicated AWS account within the organization using AWS Organizations.
2. Enable AWS CloudTrail in all regions, log to a dedicated S3 bucket with MFA-delete enabled.
3. Enable AWS Config for continuous compliance monitoring.
4. Bootstrap Terraform province:
   ```bash
   aws s3api create-bucket --bucket gsp-terraform-province-prod --region ap-south-1
   aws s3api put-bucket-versioning --bucket gsp-terraform-province-prod \
     --versioning-configuration Status=Enabled
   aws dynamodb create-table --table-name gsp-terraform-locks \
     --attribute-definitions AttributeName=LockID,AttributeType=S \
     --key-schema AttributeName=LockID,KeyType=HASH \
     --billing-mode PAY_PER_REQUEST
   ```
5. Apply base networking stack: VPC with 3 AZ public/private/data subnet tiers, NAT Gateways, VPC Endpoints for S3 and SSM.
6. Provision ECR repositories: `gsp-backend` and `gsp-frontend`.
7. Provision RDS PostgreSQL 15 Multi-AZ with automated backups (7-day retention, PITR enabled).
8. Provision ElastiCache Redis 7 cluster mode with 2 replicas.
9. Provision S3 buckets: documents, certificates, static assets — all with SSE-KMS and versioning.
10. Provision AWS KMS CMK for document encryption; rotate annually.
11. Provision WAF Web ACL attached to CloudFront: enable AWS Managed Rules (Common Rule Set, Known Bad Inputs, SQL database, PHP).

### CI/CD Pipeline — GitHub Actions

**backend-ci.yml:**
```yaml
name: Backend CI
on:
  push:
    paths: ['backend/**']
  pull_request:
    paths: ['backend/**']
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install black isort flake8 mypy
      - run: black --check backend/
      - run: isort --check-only backend/
      - run: flake8 backend/
      - run: mypy backend/ --ignore-missing-imports
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: gsp_test
          POSTGRES_USER: gsp
          POSTGRES_PASSWORD: testpassword
        options: >-
          --health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 5
      redis:
        image: redis:7-alpine
        options: --health-cmd "redis-cli ping" --health-interval 10s
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r backend/requirements/dev.txt
      - run: pytest backend/ --cov=backend --cov-report=xml --cov-fail-under=80
      - uses: codecov/codecov-action@v4
  build:
    needs: [lint, test]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: ap-south-1
      - uses: aws-actions/amazon-ecr-login@v2
      - run: |
          docker build -t gsp-backend backend/
          docker tag gsp-backend:latest ${{ secrets.ECR_REGISTRY }}/gsp-backend:${{ github.sha }}
          docker push ${{ secrets.ECR_REGISTRY }}/gsp-backend:${{ github.sha }}
```

**frontend-ci.yml** follows the same structure with `next build`, `jest --coverage`, and ESLint steps.

### Development Environment Setup

**Prerequisites:** Docker 24+, Python 3.11, Node.js 20 LTS, AWS CLI v2, Terraform 1.7+

```bash
# Clone repository
git clone git@github.com:your-org/government-services-portal.git
cd government-services-portal

# Start all local services
docker-compose up -d postgres redis mailhog minio

# Backend setup
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements/dev.txt
cp .env.example .env          # Fill in required variables
python manage.py migrate
python manage.py createsuperuser
python manage.py loaddata fixtures/departments.json
celery -A config worker -l info &
celery -A config beat -l info &
python manage.py runserver

# Frontend setup (separate terminal)
cd ../frontend
npm install
cp .env.local.example .env.local  # Fill in NEXT_PUBLIC_API_URL etc.
npm run dev
```

### Required Environment Variables

The following variables must be provisioned. In production, all secrets are stored in AWS Secrets Manager and injected as environment variables into ECS task definitions. Non-secret configuration is stored in AWS SSM Parameter Store.

| Variable | Description | Example / Source |
|---|---|---|
| `SECRET_KEY` | Django secret key (50+ chars) | AWS Secrets Manager |
| `DEBUG` | Enable Django debug mode | `False` in prod |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts | `portal.example.gov.in` |
| `DATABASE_URL` | PostgreSQL DSN | `postgres://user:pass@host:5432/gsp` |
| `REDIS_URL` | Redis connection string | `redis://:pass@host:6379/0` |
| `CELERY_BROKER_URL` | Celery broker (Redis) | `redis://:pass@host:6379/1` |
| `CELERY_RESULT_BACKEND` | Celery results (Redis) | `redis://:pass@host:6379/2` |
| `AWS_S3_BUCKET_DOCUMENTS` | S3 bucket for citizen documents | `gsp-documents-prod` |
| `AWS_S3_BUCKET_CERTIFICATES` | S3 bucket for issued certificates | `gsp-certificates-prod` |
| `AWS_KMS_KEY_ID` | KMS CMK ARN for document encryption | `arn:aws:kms:...` |
| `AWS_SES_FROM_EMAIL` | SES verified sender address | `noreply@portal.example.gov.in` |
| `AWS_SNS_SMS_ORIGINATOR` | SMS sender ID | `GOVPRT` |
| `NASC (National Identity Management Centre)_AUA_CODE` | NID AUA code from NASC (National Identity Management Centre) | From NASC (National Identity Management Centre) onboarding |
| `NASC (National Identity Management Centre)_ASA_CODE` | NID ASA code | From NASC (National Identity Management Centre) onboarding |
| `NASC (National Identity Management Centre)_API_KEY` | NASC (National Identity Management Centre) API key | AWS Secrets Manager |
| `NASC (National Identity Management Centre)_BASE_URL` | NASC (National Identity Management Centre) OTP API base URL | `https://developer.uidai.gov.in` |
| `NASC (National Identity Management Centre)_PUBLIC_KEY_PATH` | Path to NASC (National Identity Management Centre) public key file | `/etc/gsp/uidai_public.cer` |
| `DIGILOCKER_CLIENT_ID` | Nepal Document Wallet (NDW) OAuth client ID | From Nepal Document Wallet (NDW) sandbox |
| `DIGILOCKER_CLIENT_SECRET` | Nepal Document Wallet (NDW) OAuth client secret | AWS Secrets Manager |
| `DIGILOCKER_REDIRECT_URI` | OAuth callback URL | `https://portal.../auth/digilocker/callback` |
| `PAYGOV_MERCHANT_ID` | ConnectIPS merchant identifier | From ConnectIPS onboarding |
| `PAYGOV_API_KEY` | ConnectIPS API key | AWS Secrets Manager |
| `PAYGOV_BASE_URL` | ConnectIPS API base URL | `https://paygov.gov.in/api/v1` |
| `PAYGOV_WEBHOOK_SECRET` | HMAC secret for webhook verification | AWS Secrets Manager |
| `RAZORPAY_KEY_ID` | Razorpay key ID (fallback gateway) | AWS Secrets Manager |
| `RAZORPAY_KEY_SECRET` | Razorpay key secret | AWS Secrets Manager |
| `DSC_SERVICE_URL` | Internal DSC signing service URL | `http://dsc-service:8080` |
| `DSC_CERT_PATH` | DSC certificate file path | `/etc/gsp/dsc.pfx` |
| `DSC_CERT_PASSWORD` | DSC certificate passphrase | AWS Secrets Manager |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | JWT access token TTL | `15` |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | JWT refresh token TTL | `7` |
| `OTP_EXPIRY_SECONDS` | OTP validity window | `300` |
| `OTP_MAX_ATTEMPTS` | Max OTP attempts per session | `5` |
| `CLAMAV_HOST` | ClamAV daemon host | `clamav` |
| `CLAMAV_PORT` | ClamAV daemon port | `3310` |
| `SENTRY_DSN` | Sentry error reporting DSN | AWS Secrets Manager |
| `CORS_ALLOWED_ORIGINS` | Allowed CORS origins | `https://portal.example.gov.in` |
| `NEXT_PUBLIC_API_URL` | Frontend API base URL | `https://api.portal.example.gov.in` |
| `NEXT_PUBLIC_DIGILOCKER_CLIENT_ID` | Nepal Document Wallet (NDW) client ID (public) | From Nepal Document Wallet (NDW) sandbox |

---

## Phase 1: Authentication and Citizen Identity (Sprint 3–4)

### Task Checklist

- [ ] Create `auth_app` Django application with proper app config
- [ ] Implement `CitizenProfile` model with NID hash, phone, email, Nepal Document Wallet (NDW) UID
- [ ] Implement `OTPAttempt` model for rate limiting and audit trail
- [ ] Implement `NIDOTPService` — request and verify OTP via NASC (National Identity Management Centre) API
- [ ] Implement `EmailOTPService` — generate TOTP, send via SES
- [ ] Implement `SMSOTPService` — generate TOTP, send via SNS
- [ ] Configure djangorestframework-simplejwt with custom claims (citizen_id, aadhaar_verified)
- [ ] Implement JWT refresh endpoint with Redis-backed token blacklist
- [ ] Implement Nepal Document Wallet (NDW) OAuth2 flow (authorization code + PKCE)
- [ ] Implement Redis session store for OTP province
- [ ] Write auth middleware that validates JWT and attaches citizen to `request.citizen`
- [ ] Frontend: `/login` page with OTP method selection
- [ ] Frontend: OTP input component (6-digit, auto-advance, resend timer)
- [ ] Frontend: Nepal Document Wallet (NDW) redirect handler
- [ ] Frontend: JWT storage in httpOnly cookie (not localStorage)
- [ ] Write unit tests for all service methods (>90% coverage for auth_app)
- [ ] Write API integration tests for all auth endpoints

### Django App: `auth_app` — Artifacts to Implement

**Models (`auth_app/models.py`):**
- `CitizenProfile`: UUID PK, `aadhaar_hash` (SHA-256 of NID number, never store raw), `phone_number` (E.164), `email`, `full_name`, `digilocker_uid`, `is_phone_verified`, `is_email_verified`, `is_aadhaar_verified`, `aadhaar_verified_at`, `last_login_method` (enum: AADHAAR/EMAIL/SMS/DIGILOCKER), `created_at`, `updated_at`.
- `OTPAttempt`: UUID PK, `citizen` (FK nullable — before citizen exists), `phone_or_email` (anonymised), `otp_method` (enum), `is_successful`, `ip_address`, `user_agent`, `created_at`. Used for rate limiting (max 5 attempts per 15 minutes per identifier).

**Views (`auth_app/views.py`):**
- `NIDOTPRequestView` — POST `/api/v1/auth/aadhaar/otp/request/`
- `NIDOTPVerifyView` — POST `/api/v1/auth/aadhaar/otp/verify/`
- `EmailOTPRequestView` — POST `/api/v1/auth/email/otp/request/`
- `EmailOTPVerifyView` — POST `/api/v1/auth/email/otp/verify/`
- `SMSOTPRequestView` — POST `/api/v1/auth/sms/otp/request/`
- `SMSOTPVerifyView` — POST `/api/v1/auth/sms/otp/verify/`
- `Nepal Document Wallet (NDW)AuthView` — GET `/api/v1/auth/digilocker/authorize/`
- `Nepal Document Wallet (NDW)CallbackView` — GET `/api/v1/auth/digilocker/callback/`
- `TokenRefreshView` — POST `/api/v1/auth/token/refresh/`
- `LogoutView` — POST `/api/v1/auth/logout/` (blacklist refresh token)
- `CitizenProfileView` — GET/PATCH `/api/v1/auth/profile/`

### NASC (National Identity Management Centre)/NID Integration Steps

1. Complete NASC (National Identity Management Centre) AUA onboarding; obtain AUA code, ASA code, and API license key.
2. Download NASC (National Identity Management Centre) public key certificate from NASC (National Identity Management Centre) portal; store in ECS task secret mount.
3. Encrypt NID number using NASC (National Identity Management Centre) public key (RSA/OAEP) before sending in API request.
4. Generate a session key (AES-256), encrypt NID number with session key, encrypt session key with NASC (National Identity Management Centre) public key — standard NASC (National Identity Management Centre) OTP API protocol.
5. Call `POST https://developer.uidai.gov.in/otp/2.5/{AUA_CODE}/{UID_HASH}/{ASA_CODE}` with XML payload.
6. Parse response: check `ret="y"` for success, extract `txn` field for later verification.
7. Store `txn` in Redis with 5-minute TTL: `SET otp:txn:{phone_hash} {txn} EX 300`.
8. On OTP verify, call NASC (National Identity Management Centre) auth API with `txn` and OTP.
9. On successful verification, upsert `CitizenProfile`, issue JWT.
10. **Important:** Never log the NID number, OTP value, or txn outside of encrypted audit logs.

### JWT Configuration (djangorestframework-simplejwt)

```python
# config/settings/base.py
from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(env("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", default=15))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(env("JWT_REFRESH_TOKEN_LIFETIME_DAYS", default=7))),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "RS256",
    "SIGNING_KEY": env("JWT_PRIVATE_KEY"),      # RSA private key
    "VERIFYING_KEY": env("JWT_PUBLIC_KEY"),     # RSA public key
    "TOKEN_OBTAIN_SERIALIZER": "auth_app.serializers.CitizenTokenObtainSerializer",
    "TOKEN_USER_CLASS": "auth_app.models.CitizenProfile",
}
```

Use RS256 (asymmetric) rather than HS256; the frontend can verify tokens without the private key.

### Redis Session Store Setup

```python
# config/settings/base.py
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "sessions"

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_URL"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {"max_connections": 50},
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
        },
    },
    "sessions": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_URL").replace("/0", "/3"),
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    },
}
```

OTP province (transaction ID, attempt counter) is stored in the `default` cache with short TTLs.

### Phase 1 Acceptance Criteria

- A citizen can request an NID OTP and receive a 6-digit code via their NASC (National Identity Management Centre)-registered mobile.
- A citizen can verify the OTP and receive a JWT access token (15-minute expiry) and refresh token.
- JWT contains custom claims: `citizen_id`, `aadhaar_verified`, `phone_verified`, `email_verified`.
- Rate limiting: more than 5 OTP requests per 15 minutes per NID is rejected with HTTP 429.
- The refresh endpoint rotates the refresh token and blacklists the old one.
- Logout blacklists the current refresh token; subsequent use returns HTTP 401.
- All auth endpoints return structured error responses (see `code-guidelines.md`).
- Unit test coverage for `auth_app` ≥ 90%.
- OWASP Top 10 review completed for all auth endpoints.

---

## Phase 2: Service Catalog and Core Infrastructure (Sprint 5–6)

### Tasks

- [ ] Create `core` Django app with shared base models (`TimeStampedModel`, `UUIDModel`)
- [ ] Create `services_catalog` Django app
- [ ] Implement `Department` model: UUID PK, name, slug, code (unique), logo, description, contact_email, is_active
- [ ] Implement `Service` model: UUID PK, department (FK), name, slug, code (unique), description, category (enum), `form_schema` (JSONB), `document_requirements` (JSONB), `fee_structure` (JSONB), processing_days_sla, is_active, is_online
- [ ] Implement `ServiceCategory` model: name, slug, icon, sort_order
- [ ] Design JSONB schema standards for form_schema, document_requirements, fee_structure
- [ ] Configure Django Admin for Department and Service with inline document requirements
- [ ] Implement service catalog API endpoints (list, detail, search, filter by department/category)
- [ ] Frontend: `/services` page — grid of service categories
- [ ] Frontend: `/services/[department]/[service]` — service detail with fee table and document checklist
- [ ] Frontend: Search and filter component with debounced API calls
- [ ] Seed data: 10 sample services across 3 departments

### JSONB Schema Design

**form_schema** defines the multi-step application form dynamically:
```json
{
  "version": "1.0",
  "steps": [
    {
      "id": "personal_details",
      "title": "Personal Details",
      "fields": [
        {
          "id": "full_name",
          "type": "text",
          "label": "Full Name (as per NID)",
          "required": true,
          "max_length": 100,
          "pre_fill_from": "citizen_profile.full_name"
        },
        {
          "id": "dob",
          "type": "date",
          "label": "Date of Birth",
          "required": true,
          "validation": { "min_age": 18 }
        }
      ]
    }
  ]
}
```

**fee_structure** JSONB:
```json
{
  "base_fee": 100,
  "currency": "NPR",
  "breakup": [
    { "label": "Application Fee", "amount": 80 },
    { "label": "Processing Charge", "amount": 20 }
  ],
  "exemptions": [
    { "condition": "citizen.category == 'BPL'", "discount_percentage": 100 }
  ]
}
```

### Service Catalog API Endpoints

| Method | URL | Description |
|---|---|---|
| GET | `/api/v1/services/categories/` | List all service categories |
| GET | `/api/v1/services/departments/` | List all departments |
| GET | `/api/v1/services/` | List services (filter: dept, category, search) |
| GET | `/api/v1/services/{slug}/` | Service detail with full form schema |
| GET | `/api/v1/services/{slug}/documents/` | Required document checklist |
| GET | `/api/v1/services/{slug}/fee/` | Fee calculation for citizen |

All list endpoints support cursor-based pagination and `fields` sparse fieldsets.

### Phase 2 Acceptance Criteria

- Service catalog lists all active services, filterable by department and category.
- Service detail returns form schema, document requirements, and calculated fee (with BPL exemption applied if citizen profile indicates BPL card).
- Django admin allows department staff to create/edit services without code deployment.
- Frontend renders service catalog accessibly (WCAG 2.1 AA): keyboard navigable, screen reader compatible.

---

## Phase 3: Application Workflow Engine (Sprint 7–9)

### Custom State Machine Implementation

The application state machine is implemented as a pure Python class with no external FSM library dependency, ensuring testability and auditability.

**Provinces:**
```
DRAFT → SUBMITTED → PAYMENT_PENDING → PAYMENT_COMPLETE →
UNDER_REVIEW → PENDING_CLARIFICATION → DOCUMENT_VERIFICATION →
APPROVED → CERTIFICATE_GENERATION → COMPLETED
                ↓
             REJECTED
                ↓
            WITHDRAWN
```

**`apps/applications/state_machine.py`:**
```python
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class ApplicationState(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    PAYMENT_PENDING = "PAYMENT_PENDING"
    PAYMENT_COMPLETE = "PAYMENT_COMPLETE"
    UNDER_REVIEW = "UNDER_REVIEW"
    PENDING_CLARIFICATION = "PENDING_CLARIFICATION"
    DOCUMENT_VERIFICATION = "DOCUMENT_VERIFICATION"
    APPROVED = "APPROVED"
    CERTIFICATE_GENERATION = "CERTIFICATE_GENERATION"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"

@dataclass
class Transition:
    from_state: ApplicationState
    to_state: ApplicationState
    actor: str            # "citizen" | "officer" | "system"
    action: str           # human-readable action name
    validators: List[Callable]
    side_effects: List[str]  # Celery task names to dispatch

ALLOWED_TRANSITIONS: List[Transition] = [
    Transition(ApplicationState.DRAFT, ApplicationState.SUBMITTED,
               "citizen", "submit", ["validate_documents_complete"], ["send_submission_confirmation"]),
    Transition(ApplicationState.SUBMITTED, ApplicationState.PAYMENT_PENDING,
               "system", "initiate_payment", ["fee_calculation_complete"], ["create_payment_order"]),
    # ... full transition table
]
```

### Celery Setup

```python
# config/celery.py
from celery import Celery
from celery.schedules import crontab

app = Celery("gsp")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.task_routes = {
    "applications.tasks.*": {"queue": "application_tasks"},
    "notifications.tasks.*": {"queue": "notification_tasks"},
    "documents.tasks.*": {"queue": "document_tasks"},
    "payments.tasks.*": {"queue": "payment_tasks"},
}

app.conf.beat_schedule = {
    "expire-stale-drafts": {
        "task": "applications.tasks.expire_stale_drafts",
        "schedule": crontab(hour=2, minute=0),
    },
    "retry-failed-notifications": {
        "task": "notifications.tasks.retry_failed_notifications",
        "schedule": crontab(minute="*/15"),
    },
}
```

**Worker configuration for ECS:** Run 4 separate ECS services — `worker-application`, `worker-notification`, `worker-document`, `worker-payment` — each consuming a single dedicated queue.

### Task Queue Design

**application_tasks queue:**
- `validate_submission(application_id)` — validate required fields and documents
- `create_payment_order(application_id)` — call payment gateway, store order ID
- `assign_to_officer(application_id)` — round-robin assignment to available officers
- `expire_stale_drafts()` — mark applications in DRAFT province older than 30 days as WITHDRAWN
- `generate_reference_number(application_id)` — generate human-readable ref no.

**notification_tasks queue:**
- `send_submission_confirmation(application_id)` — email + SMS to citizen
- `send_status_update(application_id, old_state, new_state)` — email + SMS
- `send_payment_receipt(payment_id)` — email receipt PDF attachment
- `send_officer_assignment(application_id, officer_id)` — email to officer
- `retry_failed_notifications()` — replay notifications in FAILED province

### Multi-Step Form Builder

The frontend multi-step form is driven entirely by the service's `form_schema` JSONB. The `FormBuilder` React component recursively renders fields based on the `type` property, supporting: `text`, `number`, `date`, `select`, `multiselect`, `file_upload`, `address`, `aadhaar_input` (masked), `radio`, `checkbox_group`.

Progress is auto-saved to the backend as a DRAFT application every 30 seconds using the `PATCH /api/v1/applications/{id}/draft/` endpoint.

### Document Upload Flow

1. Frontend calls `POST /api/v1/applications/{id}/documents/presign/` with `{ "document_type": "aadhaar_card", "file_name": "aadhaar.pdf", "content_type": "application/pdf", "file_size": 524288 }`.
2. Backend validates file type (PDF, JPG, PNG only), size (max 5 MB), and returns a presigned S3 PUT URL valid for 5 minutes.
3. Frontend uploads directly to S3 using the presigned URL.
4. Frontend calls `POST /api/v1/applications/{id}/documents/confirm/` with the S3 key.
5. Backend enqueues `documents.tasks.scan_document(document_id)` — ClamAV scan.
6. On clean result, document status → VERIFIED. On threat found, document status → QUARANTINED, citizen notified.

### Phase 3 Acceptance Criteria

- A citizen can create a multi-step application, auto-save progress, and submit it.
- On submission, a unique reference number is generated (format: `{DEPT_CODE}/{YEAR}/{SEQUENCE}`).
- The state machine correctly enforces allowed transitions; invalid transitions return HTTP 409.
- Every state transition is recorded in `ApplicationStateHistory` with actor, timestamp, and note.
- Document uploads go through S3 presigned URLs; files are virus-scanned before being accepted.
- All state transitions trigger appropriate Celery notifications within 60 seconds.
- Celery workers are monitored via Flower; dead letter queue alerts sent to Slack.

---

## Phase 4: Payments (Sprint 10–11)

### ConnectIPS Integration Steps

1. Complete ConnectIPS merchant onboarding via NIC; receive `MERCHANT_ID` and API key.
2. Implement `create_order` — call `POST /api/v1/txn` with amount, merchant reference, callback URL.
3. ConnectIPS returns an `order_id`; store in `Payment` model with status `INITIATED`.
4. Redirect citizen to ConnectIPS payment page with `order_id`.
5. ConnectIPS calls webhook `POST /api/v1/payments/webhook/paygov/` on completion.
6. Verify webhook signature (HMAC-SHA256) before processing — reject unverified webhooks immediately.
7. Update `Payment` status to `COMPLETED` or `FAILED`; trigger application state transition.
8. Implement Razorpay Government as fallback gateway — activated via feature flag if ConnectIPS is unavailable.

### Idempotency Key Implementation

Every payment creation request requires an `X-Idempotency-Key` header (UUID v4 generated by the client). The backend:
1. Checks Redis for `idem:{key}` before calling the payment gateway.
2. If found, returns the cached response (prevents duplicate orders on retry).
3. If not found, processes the request and stores the response in Redis with 24-hour TTL.
4. `IdempotencyKeyManager` stores `{ order_id, status, response_body }` in Redis.

### Webhook Handler Security

```python
# payments/views.py
import hashlib, hmac
from django.conf import settings

def verify_paygov_signature(payload: bytes, received_sig: str) -> bool:
    expected = hmac.new(
        settings.PAYGOV_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, received_sig)

class ConnectIPSWebhookView(APIView):
    authentication_classes = []   # No JWT for webhooks
    permission_classes = []

    def post(self, request):
        sig = request.headers.get("X-ConnectIPS-Signature", "")
        if not verify_paygov_signature(request.body, sig):
            return Response({"error": "Invalid signature"}, status=403)
        # ... process event
```

Webhook endpoint is on an IP allowlist (ConnectIPS NAT IPs) enforced at WAF level.

### Challan Generation (PDF)

On payment initiation, a Government Revenue Challan (GRN) PDF is generated using ReportLab. The challan includes: department logo, citizen name, service name, amount breakup, challan number, payment due date, and a QR code linking to the payment portal. The challan is stored in S3 and the download URL is sent to the citizen via email.

### Refund Workflow

- Refunds are applicable when an application is rejected after payment or withdrawn within 24 hours.
- Implement `POST /api/v1/payments/{payment_id}/refund/` (officer role only).
- Call ConnectIPS refund API; store `Refund` record with `INITIATED` status.
- ConnectIPS webhooks call `/api/v1/payments/webhook/paygov/` with refund event type.
- Update `Refund` status; notify citizen via email and SMS.
- Refund SLA: 7 working days as per government policy.

### Phase 4 Acceptance Criteria

- Payment order created idempotently; duplicate requests return same order.
- Challan PDF generated, uploaded to S3, URL emailed to citizen within 30 seconds.
- Webhook signature validation rejects tampered webhooks with HTTP 403.
- Successful payment triggers application state transition to `PAYMENT_COMPLETE` via Celery.
- Refund API accessible only to officer role with `can_initiate_refund` permission.

---

## Phase 5: Document Vault and Certificates (Sprint 12–13)

### S3 Bucket Setup and KMS Configuration

- **Documents bucket** (`gsp-documents-prod`): versioning enabled, lifecycle policy moves to Glacier after 7 years, SSE-KMS with CMK, object-level logging to CloudTrail.
- **Certificates bucket** (`gsp-certificates-prod`): versioning enabled, public access blocked, SSE-KMS, bucket policy restricts access to ECS task role and CloudFront OAC.
- **KMS CMK**: key policy grants ECS task role `kms:GenerateDataKey` and `kms:Decrypt`. Annual automatic rotation enabled. Access logged via CloudTrail.

### ClamAV Virus Scanning Integration

Deploy ClamAV as an ECS sidecar container in the `worker-document` task definition:

```yaml
# ECS task definition excerpt
- name: clamav
  image: clamav/clamav:1.3
  environment:
    - CLAMAV_NO_FRESHCLAMD=false
  mountPoints:
    - sourceVolume: clamav-defs
      containerPath: /var/lib/clamav
  portMappings:
    - containerPort: 3310
```

The `ClamAVScanner` service class uses `pyclamd` to stream the downloaded S3 object to the ClamAV daemon. Virus definitions are updated daily via `freshclam`.

### Nepal Document Wallet (NDW) API Integration

Nepal Document Wallet (NDW) is used for two purposes: citizen authentication (OAuth2 login) and document pull (fetching NID XML, PAN, Driving Licence from the citizen's Nepal Document Wallet (NDW)).

**Document pull flow:**
1. Citizen consents to document access on the application form.
2. Frontend redirects to Nepal Document Wallet (NDW) OAuth2 authorization URL with requested document URIs.
3. Nepal Document Wallet (NDW) calls `GET /api/v1/auth/digilocker/callback/?code=...&province=...`.
4. Backend exchanges code for access token; fetches documents using Nepal Document Wallet (NDW) Pull API.
5. Fetched documents are stored in S3 under the citizen's document namespace.
6. Document records are created with `source=DIGILOCKER`, `is_verified=True` (Nepal Document Wallet (NDW) documents are pre-verified).

### DSC Signing Service Setup

Digital Signature Certificate signing is performed by a dedicated internal microservice (`dsc-service`) running on the same VPC:

- Built on Spring Boot (Java), uses `Bouncy Castle` library for PKCS#7 / CAdES signatures.
- The DSC private key is stored in AWS KMS (external key store / CloudHSM for production).
- GSP backend calls `POST http://dsc-service:8080/sign` with the certificate PDF bytes.
- The DSC service returns the signed PDF with an embedded digital signature.
- The signed PDF is stored in the certificates S3 bucket.

### Certificate PDF Generation (ReportLab/WeasyPrint)

```python
# documents/certificate_generator.py
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table
from reportlab.lib.styles import getSampleStyleSheet

class CertificateGenerator:
    def generate(self, application: "Application") -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                topMargin=72, bottomMargin=72,
                                leftMargin=72, rightMargin=72)
        styles = getSampleStyleSheet()
        story = []
        # Government emblem, department name, certificate title, citizen details,
        # certificate content, issue date, officer name, QR code for verification
        # ...
        doc.build(story, onFirstPage=self._add_header_footer,
                  onLaterPages=self._add_header_footer)
        return buffer.getvalue()
```

### Phase 5 Acceptance Criteria

- All citizen documents are encrypted at rest using KMS CMK.
- Virus scanning completes within 30 seconds; infected files are quarantined with citizen notification.
- Nepal Document Wallet (NDW) documents are fetched and stored with `is_verified=True` automatically.
- Issued certificates are digitally signed with DSC; PDF signature is verifiable by Adobe Reader.
- Certificate verification URL (QR code) resolves to a public verification endpoint returning certificate validity.

---

## Phase 6: Admin Console and Reports (Sprint 14–15)

### Department Admin Portal Features

The admin console is a protected Next.js route group (`/admin`) accessible only to users with `is_staff=True` and department-specific role assignments.

**Features:**
- Application queue view: list of applications assigned to the logged-in officer, filterable by province, service, date range.
- Application detail view: citizen details, uploaded documents (inline viewer), form data, province history timeline.
- State transition actions: approve, reject, request clarification — with mandatory notes.
- Document verification checklist: officer marks each required document as verified/rejected with remarks.
- Bulk actions: assign selected applications to another officer, bulk request clarification.
- Department-level dashboard: pending count, average processing time, SLA breach count.

### Report Generation (CSV/PDF)

Implement `reports` Django app with background report generation:

- `POST /api/v1/admin/reports/` — create report job (parameters: report_type, date_range, filters)
- Report job is enqueued as a Celery task; status polled via `GET /api/v1/admin/reports/{job_id}/`
- Supported report types: `applications_summary`, `payment_reconciliation`, `sla_compliance`, `document_status`, `officer_performance`.
- CSV reports use `csv` standard library with streaming response.
- PDF reports use WeasyPrint with government-standard templates.
- Generated reports are stored in S3 with 30-day expiry; download link returned on completion.

### Analytics Dashboard

Real-time analytics for department heads:
- Applications received vs. completed (daily/weekly/monthly chart) — Chart.js
- Average processing time per service — horizontal bar chart
- SLA compliance rate (% completed within SLA) — KPI card with trend
- Top bottleneck provinces (where applications spend the most time) — Sankey diagram
- Data is pre-computed by a Celery beat task running hourly and stored in Redis with 2-hour TTL.

---

## Phase 7: Grievance, Notifications, Accessibility (Sprint 16–17)

### Grievance Redressal Workflow

- Citizen can file a grievance against any application via `POST /api/v1/grievances/`.
- `Grievance` model: UUID PK, application (FK), citizen (FK), subject, description, grievance_type (enum: DELAY / CORRUPTION / QUALITY / OTHER), status (OPEN → ACKNOWLEDGED → UNDER_INVESTIGATION → RESOLVED → ESCALATED), assigned_officer, resolution_notes, resolved_at.
- Grievance SLA: acknowledge within 24 hours, resolve within 15 working days (as per CPGRAMS guidelines).
- Auto-escalation: Celery beat task checks for grievances nearing SLA breach; escalates to senior officer.
- Grievance tracking portal: citizen can track grievance status via reference number without login.

### Multi-Channel Notifications

All notifications are sent by the `notifications` app. Each notification type has a template in all 12 supported languages.

```python
# notifications/tasks.py
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_notification(self, notification_id: str) -> None:
    notification = Notification.objects.get(id=notification_id)
    try:
        channel = notification.channel  # EMAIL | SMS | IN_APP
        if channel == NotificationChannel.EMAIL:
            EmailBackend().send(notification)
        elif channel == NotificationChannel.SMS:
            SNSBackend().send(notification)
        elif channel == NotificationChannel.IN_APP:
            InAppBackend().send(notification)
        notification.status = NotificationStatus.SENT
        notification.sent_at = timezone.now()
        notification.save(update_fields=["status", "sent_at"])
    except Exception as exc:
        notification.status = NotificationStatus.FAILED
        notification.save(update_fields=["status"])
        raise self.retry(exc=exc)
```

**SMS via SNS:** Use AWS SNS with transactional message type; sender ID `GOVPRT`. Maximum 160 characters; use URL shortener for links.

**Email via SES:** Use SES with DKIM and DMARC configured for the domain. HTML templates use MJML, compiled to inline-CSS HTML. Bounce and complaint notifications forwarded to SNS topic.

### i18n Setup (12 Languages)

Languages supported: English, Hindi, Tamil, Telugu, Kannada, Malayalam, Marathi, Bengali, Gujarati, Punjabi, Odia, Assamese.

```typescript
// frontend/src/i18n/routing.ts
import { defineRouting } from 'next-intl/routing';

export const routing = defineRouting({
  locales: ['en', 'hi', 'ta', 'te', 'kn', 'ml', 'mr', 'bn', 'gu', 'pa', 'or', 'as'],
  defaultLocale: 'en',
  localePrefix: 'always',
});
```

Translation files are stored in `frontend/src/i18n/messages/{locale}.json`. All UI strings are parameterised; no hardcoded English strings outside of message files.

### WCAG 2.1 AA Audit

Conduct automated audit using `axe-core` integrated into Playwright E2E tests:
```typescript
import AxeBuilder from '@axe-core/playwright';
test('service catalog page has no accessibility violations', async ({ page }) => {
    await page.goto('/services');
    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations).toEqual([]);
});
```

Manual audit checklist:
- [ ] All interactive elements focusable and operable by keyboard
- [ ] Colour contrast ratio ≥ 4.5:1 for normal text, ≥ 3:1 for large text
- [ ] All form fields have programmatically associated labels
- [ ] Error messages are announced by screen readers (ARIA live regions)
- [ ] Skip-to-content link on every page
- [ ] No content relies solely on colour to convey meaning
- [ ] All images have descriptive alt text; decorative images have `alt=""`
- [ ] Focus order is logical and consistent with visual order
- [ ] Timeout warnings are announced 20 seconds before session expiry

---

## Phase 8: Security Hardening and Launch (Sprint 18–20)

### Security Audit Checklist

**Authentication and Authorization:**
- [ ] JWT expiry ≤ 15 minutes for access tokens
- [ ] Refresh token rotation on every use
- [ ] Refresh token blacklist implemented in Redis
- [ ] OTP brute-force protection: lock after 5 failed attempts, 15-minute lockout
- [ ] NID number never stored in plain text; only SHA-256 hash
- [ ] All API endpoints require authentication except explicitly public ones
- [ ] Role-based permissions enforced at view level, not just URL routing
- [ ] Horizontal privilege escalation check: citizens cannot access other citizens' data

**Input Validation and Output Encoding:**
- [ ] All user inputs validated with DRF serializers before database write
- [ ] File upload: MIME type validated server-side (not just extension), max size enforced
- [ ] SQL injection: ORM used everywhere; zero raw SQL with string interpolation
- [ ] XSS: DRF response content-type is `application/json`; frontend uses React (no `dangerouslySetInnerHTML`)
- [ ] Path traversal: S3 keys are generated server-side from UUIDs, never from user input
- [ ] SSRF: external HTTP calls only to allowlisted domains (NASC (National Identity Management Centre), Nepal Document Wallet (NDW), ConnectIPS)

**Transport Security:**
- [ ] TLS 1.2+ enforced; TLS 1.0/1.1 disabled at CloudFront and ALB
- [ ] HSTS header with `max-age=31536000; includeSubDomains; preload`
- [ ] All cookies: `Secure`, `HttpOnly`, `SameSite=Strict`
- [ ] CORS: only `portal.example.gov.in` allowed

**Infrastructure Security:**
- [ ] ECS tasks run as non-root user (UID 1000)
- [ ] ECS task role follows least privilege principle
- [ ] RDS not publicly accessible; in private subnet only
- [ ] Security groups: ECS → RDS on port 5432 only; ECS → Redis on port 6379 only
- [ ] WAF rules: rate limiting (1000 req/5min per IP), SQL injection, XSS, bad bots
- [ ] VPC Flow Logs enabled; anomaly detection via GuardDuty
- [ ] ECR image scanning enabled; critical CVEs fail deployment pipeline
- [ ] Secrets Manager rotation enabled for database credentials (30-day rotation)
- [ ] MFA enforced for all AWS console access

**Compliance:**
- [ ] Data retention policy implemented: auto-delete citizen PII after 7 years
- [ ] Right-to-erasure: `DELETE /api/v1/auth/account/` pseudonymises citizen data
- [ ] Audit log for every data access operation (view/modify citizen data)
- [ ] Penetration test completed by CERT-In empanelled agency

### Performance Testing

**Target:** 1,000 concurrent users, P95 response time < 2 seconds for all citizen-facing APIs.

**Locust load test configuration:**
```python
# load_tests/locustfile.py
from locust import HttpUser, task, between

class CitizenUser(HttpUser):
    wait_time = between(1, 5)

    def on_start(self):
        response = self.client.post("/api/v1/auth/sms/otp/verify/",
                                    json={"phone": "+9779999999999", "otp": "123456"})
        self.token = response.json()["access"]

    @task(5)
    def browse_service_catalog(self):
        self.client.get("/api/v1/services/", headers={"Authorization": f"Bearer {self.token}"})

    @task(3)
    def view_application_status(self):
        self.client.get("/api/v1/applications/", headers={"Authorization": f"Bearer {self.token}"})

    @task(1)
    def check_notification(self):
        self.client.get("/api/v1/notifications/", headers={"Authorization": f"Bearer {self.token}"})
```

Run from Locust master with 10 workers: `locust --headless -u 1000 -r 50 --run-time 10m`.

### Go-Live Checklist

- [ ] DNS cutover plan documented; DNS TTL reduced to 60 seconds 48 hours before launch
- [ ] CloudFront distribution tested with production domain and SSL certificate
- [ ] RDS Multi-AZ failover tested and verified (< 60 seconds failover time)
- [ ] ElastiCache automatic failover tested
- [ ] ECS service auto-scaling tested (scale-out at 70% CPU, scale-in after 5 minutes below 40%)
- [ ] CloudWatch alarms configured: 5xx error rate > 1%, P95 latency > 3s, CPU > 80%
- [ ] Runbook for common failure scenarios documented in Confluence
- [ ] On-call rotation set up in PagerDuty
- [ ] Database backup restore tested end-to-end (PITR to 1 minute before)
- [ ] All secrets rotated to production values; dev credentials revoked
- [ ] Sentry configured with production DSN; error alerting to on-call channel
- [ ] Smoke tests pass against production environment
- [ ] Pen test report reviewed; all critical and high findings remediated
- [ ] Government security audit (STQC) clearance obtained
- [ ] Disaster recovery drill completed (RTO < 4 hours, RPO < 1 hour)

---

## Dependency Installation Commands

### Backend (Python)

```bash
# Base production dependencies
pip install \
  Django==4.2.13 \
  djangorestframework==3.15.2 \
  djangorestframework-simplejwt==5.3.1 \
  django-cors-headers==4.4.0 \
  django-environ==0.11.2 \
  django-redis==5.4.0 \
  django-filter==24.3 \
  django-storages[s3]==1.14.4 \
  psycopg[binary]==3.1.19 \
  celery[redis]==5.4.0 \
  kombu==5.3.7 \
  boto3==1.35.0 \
  botocore==1.35.0 \
  Pillow==10.4.0 \
  reportlab==4.2.2 \
  weasyprint==62.3 \
  pyclamd==0.4.1 \
  qrcode[pil]==8.0 \
  cryptography==43.0.0 \
  pyjwt==2.9.0 \
  requests==2.32.3 \
  lxml==5.3.0 \
  gunicorn==23.0.0 \
  uvicorn[standard]==0.31.0 \
  whitenoise==6.8.2 \
  sentry-sdk[django]==2.14.0 \
  django-audit-log==0.7.0

# Development dependencies
pip install \
  pytest==8.3.3 \
  pytest-django==4.9.0 \
  pytest-cov==5.0.0 \
  pytest-asyncio==0.24.0 \
  factory-boy==3.3.1 \
  faker==30.3.0 \
  freezegun==1.5.1 \
  responses==0.25.3 \
  black==24.8.0 \
  isort==5.13.2 \
  flake8==7.1.1 \
  flake8-bugbear==24.8.19 \
  mypy==1.11.2 \
  django-stubs==5.1.0 \
  djangorestframework-stubs==3.15.1
```

### Frontend (Node.js / npm)

```bash
# Core dependencies
npm install \
  next@14.2.14 \
  react@18.3.1 \
  react-dom@18.3.1 \
  typescript@5.6.2 \
  tailwindcss@3.4.13 \
  @tailwindcss/forms@0.5.9 \
  @tailwindcss/typography@0.5.15 \
  next-intl@3.21.1 \
  react-hook-form@7.53.0 \
  @hookform/resolvers@3.9.0 \
  zod@3.23.8 \
  @tanstack/react-query@5.59.0 \
  axios@1.7.7 \
  date-fns@4.1.0 \
  clsx@2.1.1 \
  lucide-react@0.447.0 \
  @headlessui/react@2.1.10 \
  recharts@2.13.0

# Development dependencies
npm install --save-dev \
  @types/react@18.3.11 \
  @types/node@22.7.4 \
  eslint@8.57.1 \
  eslint-config-next@14.2.14 \
  @typescript-eslint/eslint-plugin@8.7.0 \
  @typescript-eslint/parser@8.7.0 \
  jest@29.7.0 \
  jest-environment-jsdom@29.7.0 \
  @testing-library/react@16.0.1 \
  @testing-library/jest-dom@6.5.0 \
  @testing-library/user-event@14.5.2 \
  @axe-core/playwright@4.10.0 \
  @playwright/test@1.47.2 \
  postcss@8.4.47 \
  autoprefixer@10.4.20
```

---

## Operational Policy Addendum

### 1. Citizen Data Privacy Policies

- NID numbers are never stored in plain text. Only a SHA-256 hash is persisted to the database for deduplication purposes.
- Citizen PII (name, phone, email, address) is encrypted at the database column level using application-layer AES-256 encryption with keys stored in AWS Secrets Manager.
- Audit logs record every access to citizen data by name of the accessing officer, timestamp, and the specific data fields accessed.
- Data retention: citizen application records are retained for 7 years in compliance with government records rules; after which PII fields are pseudonymised and the record is archived.
- Citizens have the right to request an export of their data (`GET /api/v1/auth/data-export/`) and the right to erasure (`DELETE /api/v1/auth/account/`), subject to pending application completion.

### 2. Service Delivery SLA Policies

- Services with defined processing_days_sla have automated SLA tracking; applications breaching SLA are escalated automatically by Celery beat tasks.
- SLA clock pauses when an application is in `PENDING_CLARIFICATION` province (waiting for citizen action).
- SLA breach notifications are sent to the department head and the assigned officer via email.
- Monthly SLA compliance reports are automatically generated on the first of each month and sent to department heads.

### 3. Fee and Payment Policies

- Service fees are defined in the service's `fee_structure` JSONB and cannot be overridden by officers.
- BPL card holders receive 100% fee exemption as mandated by government policy; the system verifies BPL status automatically via the citizen profile.
- All payment transactions are logged with merchant reference, gateway transaction ID, amount, and timestamp for audit.
- Refunds must be approved by an officer with `can_initiate_refund` permission and are processed within 7 working days.
- Failed payments are retried automatically by the Celery `retry_failed_payments` task up to 3 times before the application returns to `PAYMENT_PENDING` province with a citizen notification.

### 4. System Availability Policies

- Target uptime: 99.9% monthly (excluding planned maintenance windows).
- Planned maintenance windows: Sundays 2:00 AM – 4:00 AM IST. Maintenance notice published 48 hours in advance via the portal banner.
- CloudWatch alarms trigger PagerDuty on-call alert for: 5xx error rate > 1% over 5 minutes, P95 API latency > 3 seconds over 5 minutes, ECS service health < 50%.
- RTO: 4 hours (major infrastructure failure). RPO: 1 hour (based on RDS PITR capability).
- Disaster recovery drill is conducted every 6 months; results documented in the DR runbook.
