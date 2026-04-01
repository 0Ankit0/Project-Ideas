# Code Guidelines

> **Version:** 2.0 | **Audience:** All engineers contributing to the Healthcare Appointment System  
> These guidelines are enforced by CI linting, architectural fitness functions, and code review. Non-compliance is a merge-blocking issue.

---

## 1. Project Structure

```
healthcare-appointment-system/
├── apps/
│   ├── scheduling-service/         # Slot management, booking, conflict resolution
│   ├── patient-service/            # Patient profiles, history, consent
│   ├── billing-service/            # Insurance, payments, claims
│   ├── notification-service/       # Channel routing, templates, delivery tracking
│   └── api-gateway/                # Edge auth, rate limiting, request routing
├── libs/
│   ├── domain/                     # Shared domain primitives (Value Objects, base classes)
│   ├── events/                     # Kafka event schemas (Avro/JSON Schema + TypeScript types)
│   ├── auth/                       # JWT validation, RBAC guards, MFA utilities
│   ├── observability/              # Logger factory, tracer, metrics helpers
│   ├── database/                   # Prisma client factory, transaction helpers
│   └── testing/                    # Test factories, Testcontainers helpers, Pact utils
├── infra/
│   ├── helm/                       # Helm charts per service
│   ├── terraform/                  # Cloud infrastructure (VPC, RDS, MSK, ElastiCache)
│   └── k8s/                        # Raw manifests and ArgoCD Application CRDs
├── docs/
│   ├── adr/                        # Architecture Decision Records
│   └── runbooks/                   # Operational runbooks
├── scripts/                        # Seed, migration, and ops scripts
├── .github/
│   └── workflows/                  # CI/CD pipeline definitions
├── pnpm-workspace.yaml
└── turbo.json
```

Each `apps/*` service follows an internal four-layer layout:

```
scheduling-service/
├── src/
│   ├── transport/          # HTTP controllers, Kafka consumers, WebSocket gateways
│   ├── application/        # Command handlers, query handlers, application services
│   ├── domain/             # Aggregates, Value Objects, Domain Events, domain services
│   └── infrastructure/     # Repositories, external clients, outbox publisher, mappers
├── test/
│   ├── unit/
│   ├── integration/
│   └── contract/
└── prisma/
    └── schema.prisma
```

---

## 2. Architecture Layers

### Transport Layer
- Owns HTTP controllers, Kafka consumer handlers, and WebSocket gateways.
- Responsible for: request deserialization, input validation (class-validator DTOs), authentication/authorization guards, and response serialization.
- Must not contain business logic. Delegates immediately to an Application Service or Command Handler.
- All controllers are versioned (`/v1/appointments`) and decorated with OpenAPI metadata.

### Application Layer
- Owns Command Handlers, Query Handlers, and Application Services.
- Orchestrates domain objects and infrastructure adapters to fulfill a use case.
- Enforces idempotency: every command handler checks for a prior execution record before mutating state.
- Manages transaction boundaries: a single unit of work wraps domain mutation + outbox event insert.
- Must not import Prisma models or HTTP primitives directly — uses repository interfaces and DTOs.

### Domain Layer
- Contains Aggregates, Value Objects, Domain Events, domain services, and policy objects.
- **Zero framework dependencies.** No NestJS, no Prisma, no HTTP, no Kafka imports.
- All domain state changes happen through named methods on Aggregates that enforce invariants and emit Domain Events.
- Domain Events are immutable records; once created, they are never mutated.

### Infrastructure Layer
- Implements repository interfaces defined in the domain layer.
- Owns Prisma queries, Redis client calls, external HTTP adapters, and Outbox publishers.
- Responsible for mapping between Prisma models (persistence shape) and domain entities.
- Exception translation: infrastructure exceptions are caught here and re-thrown as typed domain errors.

---

## 3. Domain-Specific Patterns

### Value Object Design
Value Objects encapsulate identity and enforce format invariants at construction time. They are immutable.

```typescript
// libs/domain/src/appointment-id.value-object.ts
import { randomUUID } from 'crypto';

export class AppointmentId {
  private readonly value: string;

  private constructor(value: string) {
    if (!value || value.trim().length === 0) {
      throw new Error('AppointmentId cannot be empty');
    }
    // Enforce UUID v4 format
    const uuidV4Regex =
      /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
    if (!uuidV4Regex.test(value)) {
      throw new Error(`AppointmentId must be a valid UUID v4: ${value}`);
    }
    this.value = value;
  }

  static generate(): AppointmentId {
    return new AppointmentId(randomUUID());
  }

  static fromString(value: string): AppointmentId {
    return new AppointmentId(value);
  }

  toString(): string {
    return this.value;
  }

  equals(other: AppointmentId): boolean {
    return this.value === other.value;
  }
}
```

Apply the same pattern for `PatientId`, `ProviderId`, `SlotId`, `TenantId`, and all monetary amounts.

### Aggregate Design with State Machine

Aggregates own consistency boundaries and enforce all invariants. State transitions are named methods — never direct property mutation.

```typescript
// apps/scheduling-service/src/domain/appointment.aggregate.ts
import { AppointmentId } from '@libs/domain';
import { AppointmentStatus } from './appointment-status.enum';
import { AppointmentConfirmedEvent } from './events/appointment-confirmed.event';
import { AppointmentCancelledEvent } from './events/appointment-cancelled.event';
import { DomainEvent } from '@libs/domain';
import { InvalidTransitionError } from './errors/invalid-transition.error';

const ALLOWED_TRANSITIONS: Record<AppointmentStatus, AppointmentStatus[]> = {
  [AppointmentStatus.DRAFT]: [AppointmentStatus.PENDING_CONFIRMATION, AppointmentStatus.CANCELLED],
  [AppointmentStatus.PENDING_CONFIRMATION]: [AppointmentStatus.CONFIRMED, AppointmentStatus.CANCELLED, AppointmentStatus.EXPIRED],
  [AppointmentStatus.CONFIRMED]: [AppointmentStatus.CHECKED_IN, AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW],
  [AppointmentStatus.CHECKED_IN]: [AppointmentStatus.IN_CONSULTATION],
  [AppointmentStatus.IN_CONSULTATION]: [AppointmentStatus.COMPLETED],
  [AppointmentStatus.COMPLETED]: [],
  [AppointmentStatus.CANCELLED]: [],
  [AppointmentStatus.NO_SHOW]: [],
  [AppointmentStatus.EXPIRED]: [],
};

export class AppointmentAggregate {
  private readonly domainEvents: DomainEvent[] = [];

  private constructor(
    private readonly id: AppointmentId,
    private status: AppointmentStatus,
    private readonly patientId: string,
    private readonly providerId: string,
    private readonly slotId: string,
    private readonly version: number,
  ) {}

  static create(params: {
    id: AppointmentId;
    patientId: string;
    providerId: string;
    slotId: string;
  }): AppointmentAggregate {
    return new AppointmentAggregate(
      params.id,
      AppointmentStatus.DRAFT,
      params.patientId,
      params.providerId,
      params.slotId,
      0,
    );
  }

  confirm(actorId: string): void {
    this.transition(AppointmentStatus.CONFIRMED);
    this.addEvent(new AppointmentConfirmedEvent(this.id.toString(), actorId, new Date()));
  }

  cancel(actorId: string, reasonCode: string): void {
    this.transition(AppointmentStatus.CANCELLED);
    this.addEvent(new AppointmentCancelledEvent(this.id.toString(), actorId, reasonCode, new Date()));
  }

  private transition(next: AppointmentStatus): void {
    const allowed = ALLOWED_TRANSITIONS[this.status];
    if (!allowed.includes(next)) {
      throw new InvalidTransitionError(this.id.toString(), this.status, next);
    }
    this.status = next;
  }

  private addEvent(event: DomainEvent): void {
    this.domainEvents.push(event);
  }

  pullDomainEvents(): DomainEvent[] {
    return this.domainEvents.splice(0);
  }

  getId(): AppointmentId { return this.id; }
  getStatus(): AppointmentStatus { return this.status; }
  getVersion(): number { return this.version; }
}
```

### Repository Interface (Domain Layer)

The domain layer defines the contract; the infrastructure layer fulfills it.

```typescript
// apps/scheduling-service/src/domain/ports/appointment.repository.ts
import { AppointmentAggregate } from '../appointment.aggregate';
import { AppointmentId } from '@libs/domain';

export interface AppointmentRepository {
  findById(id: AppointmentId): Promise<AppointmentAggregate | null>;
  findByPatientId(patientId: string, options?: { limit: number; offset: number }): Promise<AppointmentAggregate[]>;
  save(appointment: AppointmentAggregate): Promise<void>;
  saveWithVersion(appointment: AppointmentAggregate, expectedVersion: number): Promise<void>;
}

// Token for NestJS DI
export const APPOINTMENT_REPOSITORY = Symbol('APPOINTMENT_REPOSITORY');
```

### Command Handler with Idempotency

```typescript
// apps/scheduling-service/src/application/commands/book-appointment.handler.ts
import { CommandHandler, ICommandHandler } from '@nestjs/cqrs';
import { Inject } from '@nestjs/common';
import { BookAppointmentCommand } from './book-appointment.command';
import { AppointmentRepository, APPOINTMENT_REPOSITORY } from '../../domain/ports/appointment.repository';
import { IdempotencyStore } from '@libs/database';
import { AppointmentAggregate } from '../../domain/appointment.aggregate';
import { AppointmentId } from '@libs/domain';

@CommandHandler(BookAppointmentCommand)
export class BookAppointmentHandler implements ICommandHandler<BookAppointmentCommand> {
  constructor(
    @Inject(APPOINTMENT_REPOSITORY)
    private readonly appointments: AppointmentRepository,
    private readonly idempotency: IdempotencyStore,
  ) {}

  async execute(command: BookAppointmentCommand): Promise<string> {
    // Idempotency check — return prior result if command was already processed
    const prior = await this.idempotency.get(command.idempotencyKey);
    if (prior) return prior.appointmentId;

    const id = AppointmentId.generate();
    const appointment = AppointmentAggregate.create({
      id,
      patientId: command.patientId,
      providerId: command.providerId,
      slotId: command.slotId,
    });

    appointment.confirm(command.actorId);

    // save() in the infrastructure layer wraps slot lock + appointment insert + outbox insert in one transaction
    await this.appointments.save(appointment);
    await this.idempotency.set(command.idempotencyKey, { appointmentId: id.toString() });

    return id.toString();
  }
}
```

### Outbox Pattern Publisher

The Outbox pattern guarantees that domain events are published even if the process crashes after DB commit.

```typescript
// apps/scheduling-service/src/infrastructure/outbox/outbox.publisher.ts
import { Injectable, Logger } from '@nestjs/common';
import { PrismaService } from '@libs/database';
import { KafkaProducer } from '@libs/events';
import { Cron, CronExpression } from '@nestjs/schedule';

@Injectable()
export class OutboxPublisher {
  private readonly logger = new Logger(OutboxPublisher.name);

  constructor(
    private readonly prisma: PrismaService,
    private readonly kafka: KafkaProducer,
  ) {}

  @Cron(CronExpression.EVERY_5_SECONDS)
  async publishPendingEvents(): Promise<void> {
    const events = await this.prisma.outboxEvent.findMany({
      where: { publishedAt: null },
      orderBy: { createdAt: 'asc' },
      take: 100,
    });

    for (const event of events) {
      try {
        await this.kafka.publish({
          topic: event.topic,
          key: event.aggregateId,
          value: event.payload,
          headers: { eventType: event.eventType, schemaVersion: event.schemaVersion },
        });
        await this.prisma.outboxEvent.update({
          where: { id: event.id },
          data: { publishedAt: new Date() },
        });
      } catch (err) {
        this.logger.error({ msg: 'Outbox publish failed', eventId: event.id, error: err });
        // Will retry on next tick; exponential backoff managed by retry_count column
      }
    }
  }
}
```

---

## 4. Error Handling

### Typed Domain Errors

Every domain error has a unique code, an HTTP status mapping, and a safe user-facing message.

```typescript
// libs/domain/src/errors/domain-error.ts
export abstract class DomainError extends Error {
  abstract readonly code: string;
  abstract readonly httpStatus: number;

  constructor(message: string) {
    super(message);
    this.name = this.constructor.name;
  }
}

// apps/scheduling-service/src/domain/errors/slot-already-booked.error.ts
export class SlotAlreadyBookedError extends DomainError {
  readonly code = 'SLOT_ALREADY_BOOKED';
  readonly httpStatus = 409;

  constructor(slotId: string, alternatives: string[]) {
    super(`Slot ${slotId} is no longer available.`);
    this.alternatives = alternatives;
  }

  readonly alternatives: string[];
}

// apps/scheduling-service/src/domain/errors/invalid-transition.error.ts
export class InvalidTransitionError extends DomainError {
  readonly code = 'INVALID_STATE_TRANSITION';
  readonly httpStatus = 422;

  constructor(appointmentId: string, from: string, to: string) {
    super(`Cannot transition appointment ${appointmentId} from ${from} to ${to}.`);
  }
}
```

### Global Exception Filter

```typescript
// libs/observability/src/filters/domain-exception.filter.ts
import { ExceptionFilter, Catch, ArgumentsHost, Logger } from '@nestjs/common';
import { DomainError } from '@libs/domain';
import { Response } from 'express';

@Catch(DomainError)
export class DomainExceptionFilter implements ExceptionFilter {
  private readonly logger = new Logger(DomainExceptionFilter.name);

  catch(error: DomainError, host: ArgumentsHost): void {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();

    this.logger.warn({ msg: 'Domain error', code: error.code, detail: error.message });

    response.status(error.httpStatus).json({
      error: { code: error.code, message: error.message },
    });
  }
}
```

Never expose stack traces, internal identifiers, or PHI in error responses sent to clients.

---

## 5. Testing Standards

### Coverage Targets

| Test Type | Minimum Coverage | Tooling |
|---|---|---|
| Unit | 85% line, 80% branch | Jest |
| Integration | All repository methods, all command handlers | Jest + Testcontainers |
| Contract | All public API endpoints, all Kafka event schemas | Pact |
| E2E | All critical user paths (book, cancel, check-in) | Playwright |
| Load | p99 booking < 500ms @ 1,000 VUs | k6 |

### Unit Test Guidelines
- Test state machine transitions exhaustively: every allowed and every disallowed transition.
- Use `AppointmentAggregate.create()` factories — never construct raw objects.
- Mock all repository and external adapters; inject via NestJS Testing module.
- Name tests with the `given/when/then` convention:
  ```typescript
  it('given a CONFIRMED appointment, when cancelled, then status is CANCELLED and event is emitted', () => { ... });
  ```

### Integration Test Guidelines
- Spin up real PostgreSQL and Redis using `@testcontainers/postgresql` and `@testcontainers/redis`.
- Run schema migrations against the container before each test suite.
- Use `prisma.$transaction` rollback in `afterEach` for test isolation.
- Test the full command handler → repository → database → outbox round-trip.

### Contract Test Guidelines
- Consumer tests define expected request/response shapes and publish to Pact Broker.
- Provider tests fetch contracts from Pact Broker and verify them against a running service instance.
- Breaking changes to API or event schemas fail the provider test gate.
- All Kafka event schemas are stored in the `libs/events` package with JSON Schema validation.

### Load Test Guidelines
- k6 scripts live in `tests/load/`. Each script is documented with target metrics.
- Separate scripts for: availability search, booking, cancellation, and notification throughput.
- Run load tests against a dedicated load-test environment; never against production.
- Results are archived in CI artifacts for trend analysis.

---

## 6. Observability

### Structured Logging Schema

Every log entry must include the following fields:

```json
{
  "timestamp": "2024-01-15T10:23:45.123Z",
  "level": "info",
  "service": "scheduling-service",
  "version": "1.4.2",
  "trace_id": "4bf92f3577b34da6",
  "span_id": "00f067aa0ba902b7",
  "correlation_id": "req-abc-123",
  "tenant_id": "tenant-xyz",
  "actor_id": "user-456",
  "msg": "Appointment confirmed",
  "appointment_id": "appt-789",
  "duration_ms": 42
}
```

Rules:
- **Never log PHI/PII values** (patient name, DOB, SSN, contact details). Log opaque identifiers only.
- Log at `warn` for recoverable domain errors; log at `error` for infrastructure failures.
- Do not log at `debug` in production unless dynamically enabled via feature flag for incident diagnosis.

### Metrics to Collect

| Metric | Type | Labels |
|---|---|---|
| `appointments_booked_total` | Counter | `tenant_id`, `appointment_type`, `channel` |
| `appointments_cancelled_total` | Counter | `tenant_id`, `reason_code` |
| `slot_conflicts_total` | Counter | `tenant_id`, `resolution` |
| `booking_duration_ms` | Histogram (p50/p95/p99) | `tenant_id`, `status` |
| `notification_delivery_total` | Counter | `channel`, `status`, `event_type` |
| `outbox_pending_events` | Gauge | `service` |
| `kafka_consumer_lag` | Gauge | `consumer_group`, `topic`, `partition` |
| `db_query_duration_ms` | Histogram | `operation`, `table` |

### Trace Context Propagation

- Use OpenTelemetry SDK; configure the NestJS app with `@opentelemetry/sdk-node`.
- Propagate `traceparent` / `tracestate` headers on all outbound HTTP calls and Kafka message headers.
- Ensure `trace_id` and `span_id` are injected into every log entry via `AsyncLocalStorage` / NestJS CLS.
- All Kafka consumer handlers extract and restore trace context from message headers before processing.

---

## 7. Security Coding Standards

### Input Validation
- Every Transport Layer DTO uses `class-validator` decorators. The global `ValidationPipe` is configured with `whitelist: true` and `forbidNonWhitelisted: true`.
- Validate all enum values, UUID formats, date ranges, and string lengths at the DTO level.
- Never pass raw user input to Prisma queries. Use parameterized queries exclusively — Prisma's type-safe API prevents SQL injection by construction.
- Reject requests with unexpected fields rather than silently ignoring them.

### PHI Handling
- PHI fields (patient name, DOB, contact details, diagnosis codes) are stored in encrypted columns using application-level encryption before they reach the database.
- Use a dedicated `PhiEncryptionService` that wraps a KMS-backed key. The service is injected only into infrastructure adapters — never into domain or application layers.
- Export jobs that include PHI must log the access event, require an explicit purpose code, and produce a de-identified output by default.
- All PHI-handling code paths are tagged with `@PhiAccess` decorator for automatic audit logging.

### Secret Management
- All secrets are injected via environment variables sourced from Vault / AWS Secrets Manager at pod startup.
- No secrets in code, configuration files, or Git history. Enforce with `gitleaks` pre-commit hook.
- Database credentials use Vault dynamic secrets with a 1-hour TTL; the application renews before expiry.
- Rotate all credentials on a quarterly schedule and immediately on any suspected compromise.

### SQL Injection Prevention
- Prisma's type-safe query builder is mandatory. Raw SQL (`prisma.$queryRaw`) is prohibited unless reviewed and approved in an ADR.
- Any approved raw query must use parameterized syntax (`Prisma.sql` template literal tag).
- Repository tests include SQL injection payloads in string inputs to verify parameterization.

### Authentication and Authorization Guards
- Every controller route is decorated with `@UseGuards(JwtAuthGuard, RolesGuard)`.
- The `@Roles()` decorator enforces the minimum required role at the route level.
- Sensitive operations (export, admin impersonation, production data access) additionally require `@RequiresMfa()`.
- Authorization failures are logged at `warn` with actor ID and resource ID for anomaly detection.

---

## 8. Performance Guidelines

### Preventing N+1 Queries
- Use Prisma `include` to eager-load related entities in a single query when the relation is always needed.
- For variable relation loading, use DataLoader (batching) — never load relations in a loop.
- All repository methods that return lists must accept pagination parameters (`limit`, `cursor`) and must not return unbounded result sets.

### Connection Pooling
- Configure `PgBouncer` in transaction-pooling mode in front of PostgreSQL.
- Set `DATABASE_POOL_MAX` per service based on load test results; default is 20 connections per pod.
- Monitor `db.pool.waitingCount` metric; alert if the wait queue exceeds 10 for > 30 seconds.

### Caching Strategy

| Data | Cache | TTL | Invalidation |
|---|---|---|---|
| Slot availability (read) | Redis | 30 s | On slot reservation or calendar change |
| Provider directory | Redis | 5 min | On provider profile update |
| Patient profile | Redis | 2 min | On profile update |
| System configuration | In-memory + Redis | 10 min | On config change event |

- Cache keys must include `tenant_id` to prevent cross-tenant data leakage.
- Cache-aside pattern only — never write-through from domain code directly.
- All cache reads must fall back gracefully to the database on cache miss or error.

### Async Processing
- Long-running operations (bulk schedule imports, claim submission batches, PDF generation) are offloaded to background workers via Kafka or BullMQ.
- HTTP handlers must return within 500ms. If an operation takes longer, accept it immediately, return `202 Accepted`, and deliver the result via webhook or polling endpoint.

---

## 9. Operational Policy Addendum

### Scheduling Conflict Policies
- Double-booking is prevented through atomic slot reservation (`provider_id + location_id + slot_start`) with optimistic locking (`slot_version`) and idempotency keys per booking command.
- Concurrent requests targeting one slot: the first committed reservation succeeds; subsequent requests return `409 SLOT_ALREADY_BOOKED` with the top three alternative slots.
- Provider calendar updates (leave, clinic closure, emergency blocks) trigger revalidation and move impacted appointments to `REBOOK_REQUIRED`.
- Unresolved conflicts older than 15 minutes create an operations incident and outreach task.

### Patient/Provider Workflow States
- Patient lifecycle: `DRAFT → PENDING_CONFIRMATION → CONFIRMED → CHECKED_IN → IN_CONSULTATION → COMPLETED` with terminal states `CANCELLED`, `NO_SHOW`, `EXPIRED`.
- Provider slot lifecycle: `AVAILABLE → RESERVED → LOCKED_FOR_VISIT → RELEASED`; exceptional states are `BLOCKED` and `SUSPENDED`.
- Every state transition records actor, timestamp, reason code, and correlation ID in immutable audit logs.
- Invalid transitions are rejected and never mutate billing, notification, or reporting projections.

### Notification Guarantees
- Channel order is configurable (in-app, email, SMS if consented). Delivery is at-least-once; consumers enforce idempotency using message keys.
- Critical events (`CONFIRMED`, `RESCHEDULED`, `CANCELLED`, `REBOOK_REQUIRED`) retry with exponential backoff for 24 hours.
- Failed deliveries create `NOTIFICATION_ATTENTION_REQUIRED` tasks for manual outreach.
- Template versions are pinned to event schema versions for deterministic rendering and compliance review.

### Privacy Requirements
- PHI/PII encryption: TLS 1.2+ in transit, AES-256 at rest, and customer-managed key support for regulated tenants.
- Access control: least-privilege RBAC/ABAC, MFA for privileged roles, and just-in-time elevation for production support.
- Auditability: all create/read/update/export actions on clinical or billing data are logged with actor, purpose, and source IP.
- Data minimization is mandatory for analytics exports, notifications, and non-production datasets.

### Downtime Fallback Procedures
- In degraded mode, read operations remain available while write commands are queued with ordering guarantees.
- Clinics operate from offline rosters and manual check-in forms, then reconcile after recovery.
- Recovery pipeline replays commands, revalidates slot conflicts, and issues reconciliation notifications.
- Incident closure requires backlog drain, consistency checks, and a postmortem with corrective actions.
