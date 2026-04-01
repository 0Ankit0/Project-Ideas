# Code Guidelines — Job Board and Recruitment Platform

## Technology Stack

| Layer           | Technology                                                      |
|-----------------|-----------------------------------------------------------------|
| Backend runtime | Node.js 20 LTS (TypeScript 5.x, strict mode)                   |
| Backend framework | NestJS 10                                                     |
| Frontend        | React 18, TypeScript, Vite 5, TailwindCSS 3                    |
| Mobile          | React Native 0.74, Expo SDK 51                                 |
| Database ORM    | Prisma 5                                                        |
| Message broker  | kafkajs 2 (KafkaJS)                                            |
| AI/ML backend   | FastAPI (Python 3.11), served via uvicorn                      |
| AI integration  | OpenAI API (GPT-4o for scoring), custom embedding model        |
| Testing         | Jest 29 (unit), Supertest (integration), Cypress 13 (E2E), k6 (load) |
| Monorepo        | NX 19 workspace                                                |
| Container       | Docker (multi-stage builds), Amazon ECR                        |
| IaC             | Terraform 1.8                                                  |

---

## Monorepo Project Structure

```
/
├── apps/
│   ├── web/                    # React 18 recruiter dashboard (Vite + TailwindCSS)
│   ├── mobile/                 # React Native candidate mobile app
│   ├── api-gateway/            # NestJS API gateway (routing, auth, rate limiting)
│   └── candidate-portal/       # React 18 public-facing candidate site
│
├── services/
│   ├── job-service/            # Job CRUD, approval workflow, board distribution
│   ├── application-service/    # Application ingestion, resume upload, tracking
│   ├── ats-service/            # Pipeline stages, scorecard, drag-drop board
│   ├── interview-service/      # Interview scheduling, calendar sync, scorecard
│   ├── offer-service/          # Offer generation, DocuSign, approval chain
│   ├── analytics-service/      # Hiring funnel metrics, diversity reports
│   ├── notification-service/   # Email, SMS, push notifications via SQS
│   ├── ai-service/             # Resume parsing, job matching, scoring (FastAPI)
│   ├── integration-service/    # LinkedIn, Indeed, Glassdoor, Checkr, Zoom
│   ├── gdpr-service/           # Data export, erasure, consent management
│   └── auth-service/           # JWT issuance, OAuth 2.0, RBAC
│
├── libs/
│   ├── shared/
│   │   ├── dto/                # DTOs shared across services (class-validator decorated)
│   │   ├── events/             # Kafka event contracts (Avro schemas + TS types)
│   │   ├── utils/              # Date helpers, pagination, crypto utilities
│   │   ├── errors/             # Custom error classes (AppError hierarchy)
│   │   └── types/              # Shared TypeScript interfaces and enums
│   └── testing/
│       ├── fixtures/           # Test data factories (faker-js based)
│       └── helpers/            # DB reset utilities, Kafka test consumers
│
├── infrastructure/
│   ├── terraform/              # All Terraform modules (vpc, ecs, rds, msk, etc.)
│   └── docker/                 # Service-specific Dockerfiles
│
├── .github/
│   └── workflows/              # GitHub Actions CI/CD pipelines
│
├── nx.json
├── tsconfig.base.json
└── package.json                # Root workspace package.json
```

Each service under `services/` follows an identical internal structure:

```
services/job-service/
├── src/
│   ├── domain/
│   │   ├── entities/           # Job, JobApproval, JobDistribution domain entities
│   │   ├── value-objects/      # Salary, Location, SkillTag value objects
│   │   ├── policies/           # DuplicateJobPolicy, ApprovalRequiredPolicy
│   │   └── events/             # JobPublishedEvent, JobClosedEvent (domain events)
│   ├── application/
│   │   ├── use-cases/          # CreateJobUseCase, ApproveJobUseCase, etc.
│   │   ├── commands/           # CQRS write commands
│   │   ├── queries/            # CQRS read queries
│   │   └── dtos/               # Request/response DTOs (service-specific)
│   ├── infrastructure/
│   │   ├── persistence/        # PrismaJobRepository
│   │   ├── messaging/          # KafkaJobEventPublisher
│   │   ├── http/               # NestJS controllers, modules, guards
│   │   └── external/           # LinkedIn API client, Indeed API client
│   └── main.ts
├── prisma/
│   └── schema.prisma
├── test/
│   ├── unit/
│   ├── integration/
│   └── e2e/
└── Dockerfile
```

---

## TypeScript Standards

### Strict Mode Configuration

Every `tsconfig.json` in the monorepo extends `tsconfig.base.json`:

```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "exactOptionalPropertyTypes": true,
    "forceConsistentCasingInFileNames": true,
    "moduleResolution": "bundler",
    "target": "ES2022",
    "lib": ["ES2022"]
  }
}
```

**Rules:**
- `any` is forbidden without an `// eslint-disable` comment co-authored with a reason. Each suppression requires code review approval.
- Use `unknown` for values coming from external sources (API responses, Kafka messages) and narrow the type explicitly.
- Prefer `type` aliases over `interface` for union and intersection types; use `interface` for object shapes that may be extended.
- Never use non-null assertion (`!`) without a preceding null check in code comments.

### Naming Conventions

| Construct             | Convention               | Example                              |
|-----------------------|--------------------------|--------------------------------------|
| Classes               | PascalCase               | `ApplicationService`                 |
| Interfaces            | PascalCase, no `I` prefix| `ApplicationRepository`              |
| Types                 | PascalCase               | `CreateApplicationDto`               |
| Enums                 | PascalCase, UPPER values | `ApplicationStatus.UNDER_REVIEW`     |
| Functions/methods     | camelCase                | `findByJobId()`                      |
| Variables/constants   | camelCase                | `applicationCount`                   |
| Module-level constants| SCREAMING_SNAKE_CASE     | `MAX_RESUME_SIZE_MB`                 |
| Files                 | kebab-case               | `create-application.use-case.ts`     |
| Kafka topic names     | dot.notation             | `application.created.v1`             |

---

## Domain-Driven Design

### Layers and Responsibilities

**Domain Layer** (pure business logic, no framework dependencies):
- **Entities**: Have identity, encapsulate invariants, expose domain methods. Never expose setters; mutate state through named methods.
- **Value Objects**: Immutable, equality by value. Validated in constructor; throws `DomainError` if invariant violated.
- **Domain Events**: Immutable records of something that happened. Carry only the data needed by consumers.
- **Domain Policies**: Stateless rules evaluated against entities (e.g., `DuplicateApplicationPolicy.evaluate(candidate, job)`).

**Application Layer** (use cases, orchestration):
- Use cases are single-responsibility classes with one public `execute()` method.
- Use cases receive DTOs (validated), operate on domain entities, persist via repository interfaces, and publish domain events.
- Use cases do not contain business logic — they delegate to domain entities and policies.

**Infrastructure Layer** (framework, DB, external APIs):
- Prisma repository implementations, Kafka publisher implementations, NestJS HTTP controllers.
- Controllers only validate input, call a single use case, and format the response. No business logic in controllers.

### CQRS Pattern

Commands and queries are explicitly separated at the application layer:
- **Commands**: Mutate state. Return `void` or the created entity's ID only.
- **Queries**: Return data. Never mutate state. Queries may bypass the domain model and query the read model (Prisma `findMany` with specific `select`) directly for performance.

```typescript
// Command example
export class CreateApplicationCommand {
  constructor(
    public readonly jobId: string,
    public readonly candidateId: string,
    public readonly resumeKey: string,
    public readonly coverLetter: string | null,
  ) {}
}

// Query example — returns read model, not domain entity
export class GetApplicationsByJobQuery {
  constructor(
    public readonly jobId: string,
    public readonly pagination: PaginationParams,
    public readonly filters: ApplicationFilterParams,
  ) {}
}
```

---

## Repository Pattern with Prisma

Define repository interfaces in the domain layer:

```typescript
export interface ApplicationRepository {
  findById(id: string): Promise<Application | null>;
  findByJobAndCandidate(jobId: string, candidateId: string): Promise<Application | null>;
  save(application: Application): Promise<void>;
  update(application: Application): Promise<void>;
}
```

Implement in the infrastructure layer using Prisma:

```typescript
@Injectable()
export class PrismaApplicationRepository implements ApplicationRepository {
  constructor(private readonly prisma: PrismaClient) {}

  async findById(id: string): Promise<Application | null> {
    const record = await this.prisma.application.findUnique({
      where: { id },
      include: { resume: true, screeningScore: true },
    });
    return record ? ApplicationMapper.toDomain(record) : null;
  }

  async save(application: Application): Promise<void> {
    const data = ApplicationMapper.toPersistence(application);
    await this.prisma.application.create({ data });
  }
}
```

All Prisma queries must specify explicit `select` fields on read paths to prevent over-fetching. Never use `findMany` without a `take` limit. Default page size: 20; maximum: 100.

---

## DTO Validation

All incoming HTTP request bodies are validated with `class-validator`:

```typescript
export class CreateApplicationDto {
  @IsUUID()
  jobId: string;

  @IsString()
  @MaxLength(5000)
  @IsOptional()
  coverLetter?: string;

  @IsString()
  @Matches(/^resumes\/[a-z0-9\-]+\.(pdf|docx)$/, {
    message: 'resumeKey must be a valid S3 key in the resumes/ prefix',
  })
  resumeKey: string;
}
```

Use `ValidationPipe` globally in every NestJS application with `whitelist: true` and `forbidNonWhitelisted: true` to strip and reject unexpected properties.

---

## Error Handling

### Custom Error Hierarchy

```typescript
// libs/shared/errors/app-error.ts
export abstract class AppError extends Error {
  abstract readonly code: string;
  abstract readonly httpStatus: number;
  constructor(message: string, public readonly context?: Record<string, unknown>) {
    super(message);
    this.name = this.constructor.name;
  }
}

export class NotFoundError extends AppError {
  readonly code = 'NOT_FOUND';
  readonly httpStatus = 404;
}

export class DuplicateApplicationError extends AppError {
  readonly code = 'DUPLICATE_APPLICATION';
  readonly httpStatus = 409;
}

export class ExternalServiceError extends AppError {
  readonly code = 'EXTERNAL_SERVICE_UNAVAILABLE';
  readonly httpStatus = 503;
}
```

### Global Exception Filter

A NestJS `ExceptionFilter` maps `AppError` subclasses to HTTP responses with a consistent body:

```typescript
{
  "error": {
    "code": "DUPLICATE_APPLICATION",
    "message": "Candidate has already applied to this job",
    "requestId": "x-amzn-trace-id value",
    "timestamp": "2024-11-15T10:30:00Z"
  }
}
```

Never leak stack traces, internal IDs, or database error messages to API responses. Log the full error (including stack) to CloudWatch with a structured log entry including `requestId`, `userId`, `service`, and `traceId`.

---

## AI/ML Integration Patterns

### Resume Parsing

Resume parsing is **fully asynchronous**. On `POST /applications`, the controller:
1. Validates the request and saves the application with status `RESUME_PARSING_PENDING`.
2. Responds immediately with `202 Accepted` and the application ID.
3. The S3 `ObjectCreated` event triggers a Lambda that enqueues a message on SQS `ai-parse-queue`.
4. `ai-service` polls SQS, calls the FastAPI parsing endpoint, and publishes `resume.parsed` to Kafka.
5. `application-service` consumes `resume.parsed` and updates the application with extracted skills, experience, and education.

**Timeout and Fallback**: If the AI service does not respond within 30 seconds, the circuit breaker opens and the SQS message is re-queued. After 3 retries (with exponential backoff: 30s, 60s, 120s), the message moves to the DLQ and the application status is set to `REQUIRES_MANUAL_REVIEW`. A Slack alert fires for the operations team.

### Job Matching Score

```typescript
async computeMatchScore(jobId: string, candidateId: string): Promise<number> {
  const [jobEmbedding, candidateEmbedding] = await Promise.all([
    this.embeddingCache.get(`job:${jobId}`) ?? this.aiClient.embed(jobRequirements),
    this.embeddingCache.get(`candidate:${candidateId}`) ?? this.aiClient.embed(candidateSkills),
  ]);
  return cosineSimilarity(jobEmbedding, candidateEmbedding);
}
```

Match scores are cached in Redis with TTL 1 hour. Embeddings are pre-computed on job publish and candidate profile update via Kafka consumers, not on-demand during search.

### Circuit Breaker

Use `opossum` library for circuit breaker wrapping all AI service HTTP calls:

```typescript
const breaker = new CircuitBreaker(aiHttpCall, {
  timeout: 30_000,
  errorThresholdPercentage: 50,
  resetTimeout: 60_000,
  volumeThreshold: 10,
});
breaker.fallback(() => ({ status: 'FALLBACK', score: null }));
```

---

## GDPR Compliance Implementation

### PII Encryption

PII fields (full name, email, phone, address, date of birth) are encrypted at the application layer before writing to the database using AWS KMS Data Key Encryption:

```typescript
const encryptedEmail = await this.kmsService.encrypt(candidateEmail, {
  context: { table: 'candidates', field: 'email', tenantId: companyId },
});
```

Encrypted fields are stored as `bytea` in PostgreSQL. The KMS data key is fetched and cached in-memory per service instance for 5 minutes to minimize KMS API calls.

### Soft Delete and Erasure

Candidates are never hard-deleted. On GDPR erasure request:
1. All PII fields are overwritten with `[GDPR_ERASED]` placeholder.
2. `is_gdpr_erased` flag set to `true`.
3. S3 resume file deleted permanently.
4. `gdpr_erased_at` timestamp recorded.
5. `GdprErasureCompletedEvent` published to Kafka for downstream services.
6. Audit log entry created with operator ID, timestamp, and legal basis.

### Data Retention

A daily EventBridge cron triggers a Lambda that:
1. Queries `candidates` where `created_at < NOW() - retention_period_days` and `is_gdpr_erased = false`.
2. For candidates who have not applied to any job in 2 years and whose account is inactive, triggers the erasure workflow automatically.
3. Companies can configure custom retention periods (default: 2 years) via the GDPR settings panel.

---

## Calendar Sync Implementation

### OAuth Token Refresh

Refresh tokens are stored encrypted in Secrets Manager (not the database). The `integration-service` maintains an in-memory token cache with 5-minute buffer before expiry:

```typescript
async getValidAccessToken(userId: string, provider: 'google' | 'outlook'): Promise<string> {
  const tokenRecord = await this.tokenStore.get(userId, provider);
  if (tokenRecord.expiresAt.getTime() - Date.now() < 5 * 60 * 1000) {
    const refreshed = await this.oauthClient.refresh(tokenRecord.refreshToken);
    await this.tokenStore.save(userId, provider, refreshed);
    return refreshed.accessToken;
  }
  return tokenRecord.accessToken;
}
```

### Conflict Detection

Before scheduling an interview slot, the service performs an O(n) scan of the interviewer's busy slots for the requested day. Slots are pre-fetched and cached in Redis per interviewer per day (TTL: 15 minutes). A slot is considered conflicting if `requestedStart < existingEnd && requestedEnd > existingStart` (standard interval overlap).

---

## Security Standards

### RBAC

Roles: `SUPER_ADMIN`, `COMPANY_ADMIN`, `RECRUITER`, `HIRING_MANAGER`, `INTERVIEWER`, `CANDIDATE`. Each NestJS route is decorated with `@Roles(...)` and protected by `RolesGuard`, which reads the role from the JWT payload.

### Row-Level Security

PostgreSQL RLS is enabled on all multi-tenant tables. A `SET LOCAL app.current_company_id = $1` statement is issued at the beginning of each database transaction, and RLS policies enforce `company_id = current_setting('app.current_company_id')::uuid`. This prevents data leakage between tenants even if application-layer filtering is bypassed.

### Rate Limiting

`@nestjs/throttler` is configured at the module level with Redis store for distributed rate limiting:

| Route group                    | Limit               | Window  |
|--------------------------------|---------------------|---------|
| Public job search              | 200 req             | 1 min   |
| Candidate application submission | 10 req            | 1 hour  |
| Recruiter API                  | 1000 req            | 1 min   |
| Auth endpoints (login, register) | 20 req            | 15 min  |
| AI resume analysis             | 50 req              | 1 hour  |

---

## Testing Strategy

### Unit Tests (Jest)
- Target: **80%+ line coverage** for all `application/use-cases/` and `domain/` directories.
- Use `jest.mock()` for all infrastructure dependencies (repository, event publisher, HTTP clients).
- Domain entity tests must be deterministic — no external dependencies, no async.
- Run with: `nx test <service-name> --coverage`

### Integration Tests (Jest + Supertest)
- Spin up real PostgreSQL and Kafka via Docker Compose (`docker-compose.test.yml`).
- Test the full NestJS application in-process using `@nestjs/testing` `TestingModule`.
- Each test suite resets the database using `prisma.$executeRaw` truncate before each test.
- Run with: `nx run <service-name>:test:integration`

### E2E Tests (Cypress)
- Cover all critical hiring flows: job creation → application submission → ATS stage advancement → offer sent → offer signed.
- Run against the staging environment after every deployment.
- Custom `cy.loginAs(role)` command handles authentication setup.
- Run with: `nx e2e web-e2e --baseUrl https://staging.jobplatform.com`

### Load Tests (k6)
- Scenarios: 10,000 concurrent job searches, 1,000 simultaneous application submissions.
- Thresholds: p95 < 500ms, error rate < 0.1%.
- Run before each production release from the staging environment.
- Run with: `k6 run infrastructure/k6/job-search-load-test.js`

### Contract Tests (Pact)
- Consumer-driven contract tests for all service-to-service HTTP calls.
- Pact broker deployed at `https://pact.jobplatform.internal`.
- Every service that calls another service owns the consumer contract.
- Provider verification runs in CI before any service deployment.

---

## Code Review Checklist

Before approving a pull request, reviewers must confirm:

- [ ] No `any` types without explicit justification comment
- [ ] All new public methods have JSDoc describing parameters and return values
- [ ] No secrets, credentials, or PII in code or test fixtures
- [ ] Database migrations are backwards-compatible (no column drops or renames without a two-phase migration)
- [ ] New Kafka topics have Avro schema registered in `libs/shared/events/`
- [ ] New PII fields are encrypted and included in the GDPR erasure workflow
- [ ] Unit test coverage does not decrease
- [ ] No direct Prisma calls in use-case or domain layer files
- [ ] API response bodies follow the standard envelope format
- [ ] Rate limiting applied to any new public endpoints
