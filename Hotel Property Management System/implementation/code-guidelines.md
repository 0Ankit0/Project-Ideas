# Hotel Property Management System — Code Guidelines

## Technology Stack

The HPMS is a polyglot system. Each service runtime is chosen to match the service's dominant computational profile and the engineering team's domain expertise.

| Service                  | Runtime                    | Framework              | Rationale                                               |
|--------------------------|----------------------------|------------------------|---------------------------------------------------------|
| ReservationService       | Java 21 (virtual threads)  | Spring Boot 3.3        | Complex domain logic; transactional ACID guarantees     |
| FolioService             | Java 21 (virtual threads)  | Spring Boot 3.3        | Accounting rules; JVM ecosystem for decimal arithmetic  |
| LoyaltyService           | Java 21 (virtual threads)  | Spring Boot 3.3        | Points calculation; PCI-adjacent data handling          |
| RoomService              | Java 21 (virtual threads)  | Spring Boot 3.3        | Inventory management; tight RLS integration             |
| PropertyService          | Java 21 (virtual threads)  | Spring Boot 3.3        | Configuration management; admin CRUD                    |
| HousekeepingService      | Node.js 20                 | Fastify 4              | Real-time task updates; WebSocket for housekeeper app   |
| NotificationService      | Node.js 20                 | Fastify 4              | I/O-bound; event-driven SQS consumer                   |
| ChannelManagerService    | Go 1.22                    | net/http + chi         | High-throughput OTA XML/JSON parsing; concurrency       |
| RevenueService           | Python 3.12                | FastAPI 0.111          | Pricing algorithms; NumPy/pandas data analysis          |
| KeycardService           | Go 1.22                    | net/http + chi         | Low-latency, low-overhead hardware integration          |
| NightAuditProcessor      | Java 21 (virtual threads)  | Spring Batch 5         | Batch processing; robust retry and restart semantics    |
| Web Application          | TypeScript 5.5             | React 18 + Vite 5      | Component reuse; strong typing for form validation      |
| Mobile Application       | TypeScript 5.5             | React Native 0.74      | Code sharing with web; housekeeper task management      |

### Dependency Management

- **Java:** Maven 3.9 with a parent POM enforcing dependency versions. Dependabot raises PRs for patch-level updates weekly. Major version upgrades require an ADR.
- **Node.js:** pnpm workspaces. `.nvmrc` pins the exact Node version. Lockfile is committed.
- **Go:** Go modules. `go.sum` is committed. `govulncheck` runs in CI.
- **Python:** Poetry with `pyproject.toml`. `poetry.lock` is committed. Safety checks in CI.
- **Frontend:** pnpm. `package-lock.json` equivalent (`pnpm-lock.yaml`) is committed.

---

## Project Structure

### Java Microservice Structure (Spring Boot)

```
reservation-service/
├── src/
│   ├── main/
│   │   ├── java/com/hpms/reservation/
│   │   │   ├── controller/          # REST controllers, DTOs
│   │   │   ├── application/         # Application services, command handlers, use cases
│   │   │   ├── domain/
│   │   │   │   ├── model/           # Aggregates, value objects, enums
│   │   │   │   ├── service/         # Domain services
│   │   │   │   ├── events/          # Domain events
│   │   │   │   └── repository/      # Repository interfaces (ports)
│   │   │   └── infrastructure/
│   │   │       ├── persistence/     # JPA entities, repository adapters
│   │   │       ├── cache/           # Redis cache services
│   │   │       ├── messaging/       # Kafka producers, SQS consumers
│   │   │       └── client/          # Feign/RestClient adapters for other services
│   │   └── resources/
│   │       ├── application.yml
│   │       ├── db/migration/        # Flyway SQL migrations (V1__init.sql, V2__add_index.sql)
│   │       └── application-{profile}.yml
│   └── test/
│       ├── java/com/hpms/reservation/
│       │   ├── unit/                # Pure unit tests; no Spring context
│       │   ├── integration/         # @SpringBootTest + TestContainers
│       │   ├── contract/            # Pact consumer/provider tests
│       │   └── e2e/                 # Full flow tests against local Docker Compose stack
│       └── resources/
│           └── testdata/            # JSON fixtures for test scenarios
├── Dockerfile
├── pom.xml
└── k8s/
    ├── deployment.yaml
    ├── service.yaml
    ├── hpa.yaml
    └── configmap.yaml
```

### Go Service Structure (ChannelManagerService)

```
channel-manager-service/
├── cmd/
│   └── server/
│       └── main.go                  # Entry point; dependency wiring
├── internal/
│   ├── handler/                     # HTTP handlers
│   ├── service/                     # Business logic
│   ├── adapter/
│   │   ├── bookingcom/              # Booking.com API client
│   │   └── expedia/                 # Expedia API client
│   ├── messaging/                   # Kafka producer/consumer
│   ├── repository/                  # Database access
│   └── model/                       # Domain types
├── pkg/
│   └── hmac/                        # Shared HMAC verification utility
├── api/
│   └── openapi.yaml                 # OpenAPI 3.1 spec
├── Dockerfile
└── go.mod
```

### Frontend Structure (React + TypeScript)

```
web-app/
├── src/
│   ├── features/
│   │   ├── reservations/            # Reservation list, create, modify
│   │   ├── checkin/                 # Check-in workflow
│   │   ├── folio/                   # Folio view, charges, payment
│   │   ├── housekeeping/            # Room status board
│   │   └── revenue/                 # Rate plan management UI
│   ├── shared/
│   │   ├── components/              # Reusable UI components
│   │   ├── hooks/                   # Custom React hooks
│   │   ├── api/                     # TanStack Query hooks + Axios config
│   │   └── types/                   # Shared TypeScript types (generated from OpenAPI)
│   ├── store/                       # Zustand global state
│   └── main.tsx
├── vite.config.ts
└── package.json
```

---

## Hotel Domain Patterns

### Aggregate Root Pattern

Every domain object is either an Aggregate Root or belongs to exactly one aggregate. Domain rules are enforced within the aggregate boundary; no code outside the aggregate modifies its internal state directly.

```java
// CORRECT — aggregate root enforces invariants
public class Reservation {
    public void checkin(LocalDate actualDate, String roomNumber) {
        if (this.status != ReservationStatus.CONFIRMED) {
            throw new InvalidReservationStateException(
                "Cannot check-in a reservation in status: " + this.status);
        }
        if (actualDate.isBefore(this.checkInDate.minusDays(1))) {
            throw new EarlyCheckinException("Early check-in not permitted without pre-approval");
        }
        this.status = ReservationStatus.CHECKED_IN;
        this.actualCheckInAt = Instant.now();
        this.roomAllocation.assignRoom(roomNumber);
        registerEvent(new CheckInCompletedEvent(this.id, roomNumber, actualDate));
    }
}

// WRONG — status manipulation from outside the aggregate
reservation.setStatus(ReservationStatus.CHECKED_IN); // Never do this
```

### Repository Pattern

Repositories are defined as interfaces in the domain layer. Infrastructure adapters implement them. This keeps the domain free of persistence concerns and enables swapping persistence mechanisms in tests.

```java
// Domain layer — pure interface, no JPA annotations
public interface ReservationRepository {
    Optional<Reservation> findById(UUID reservationId);
    List<Reservation> findByPropertyAndDateRange(UUID propertyId, LocalDate from, LocalDate to);
    Reservation save(Reservation reservation);
    void publishEvents(Reservation reservation); // Outbox pattern
}

// Infrastructure layer — JPA adapter
@Repository
@RequiredArgsConstructor
public class ReservationRepositoryAdapter implements ReservationRepository {
    private final ReservationJpaRepository jpaRepository;
    private final ReservationMapper mapper;
    private final OutboxRepository outboxRepository;

    @Override
    @Transactional
    public Reservation save(Reservation reservation) {
        ReservationJpaEntity entity = mapper.toEntity(reservation);
        ReservationJpaEntity saved = jpaRepository.save(entity);
        return mapper.toDomain(saved);
    }

    @Override
    @Transactional
    public void publishEvents(Reservation reservation) {
        reservation.getDomainEvents().forEach(event ->
            outboxRepository.store(new OutboxEntry(event))
        );
        reservation.clearEvents();
    }
}
```

### Domain Events

All state transitions in an aggregate root produce domain events. Events are not published directly to Kafka — they are stored in an Outbox table within the same transaction as the aggregate save, then published asynchronously by the Outbox processor. This guarantees at-least-once delivery without distributed transactions.

```java
public abstract class AggregateRoot {
    private final List<DomainEvent> domainEvents = new ArrayList<>();

    protected void registerEvent(DomainEvent event) {
        this.domainEvents.add(event);
    }

    public List<DomainEvent> getDomainEvents() {
        return Collections.unmodifiableList(domainEvents);
    }

    public void clearEvents() {
        this.domainEvents.clear();
    }
}
```

### CQRS for Availability Queries

Availability search is read-heavy (estimated 95% of traffic). A separate read model is maintained for availability queries, updated asynchronously from the write model via Kafka events. This prevents availability queries from competing with reservation writes on the primary database.

```java
// Command side — write model (PostgreSQL via JPA)
@Transactional
public ReservationId createReservation(CreateReservationCommand cmd) {
    // Writes to reservations table; triggers Kafka event
}

// Query side — read model (Redis-first, PostgreSQL fallback)
public AvailabilityResult queryAvailability(AvailabilityQuery query) {
    return inventoryCacheService
        .getAvailability(query.propertyId(), query.roomTypeId(), query.date())
        .orElseGet(() -> availabilityReadRepository.query(query));
}
```

---

## Multi-Property Data Isolation

Multi-property data isolation is the most critical data governance requirement in HPMS. A bug that allows property A to read or write property B's reservation data would be a severe business and privacy violation.

### Layer 1 — Application-Level Tenancy (Spring Security)

A custom `@PropertyScoped` annotation triggers a Spring Security aspect that:

1. Extracts `propertyId` from the authenticated JWT (`claims.propertyId` or `claims.allowedPropertyIds`).
2. Stores it in a `PropertyContext` thread-local before the controller method executes.
3. Injects it into all downstream service calls as a method parameter.
4. Clears the context after request completion (in a finally block).

```java
@PropertyScoped
@GetMapping("/reservations/{id}")
public ReservationResponse getReservation(@PathVariable UUID id) {
    UUID propertyId = PropertyContext.current(); // Set by @PropertyScoped aspect
    return reservationService.findById(id, propertyId);
}
```

The aspect logs a `SECURITY_VIOLATION` audit event and throws `AccessDeniedException` if the requested resource's `property_id` does not match the JWT's property scope.

### Layer 2 — Repository Enforcement

Every repository method that retrieves data includes a `propertyId` parameter. There is no `findById(UUID id)` method — only `findById(UUID id, UUID propertyId)`. The `@PropertyScoped` aspect and code review checklist enforce this at development time.

```java
// CORRECT
Optional<Reservation> findById(UUID reservationId, UUID propertyId);

// WRONG — never allowed
Optional<Reservation> findById(UUID reservationId);
```

### Layer 3 — PostgreSQL Row-Level Security

RLS policies in PostgreSQL ensure that even direct SQL queries (via bastion host or BI tools) respect property boundaries. The application sets the `app.current_property_id` session variable at connection checkout from the RDS Proxy pool.

```sql
-- Applied to every table with property_id column
CREATE POLICY property_rls ON reservations
  FOR ALL
  USING (property_id = current_setting('app.current_property_id')::uuid);

ALTER TABLE reservations ENABLE ROW LEVEL SECURITY;
ALTER TABLE reservations FORCE ROW LEVEL SECURITY; -- applies even to table owner
```

### Layer 4 — Multi-Property Token Scope

Hotel group administrators managing multiple properties receive a JWT with `allowedPropertyIds: ["PROP-001", "PROP-002"]`. These users can explicitly switch property context via `POST /api/v1/auth/switch-property`. Single-property tokens contain exactly one `propertyId` and can never access another property's data regardless of API call parameters.

---

## OTA Sync Patterns

### Idempotent Processing (Upsert by OTA Reservation ID)

OTA webhooks are not exactly-once; retries are common. All OTA reservation events are processed idempotently using an upsert operation keyed on `ota_reservation_id`:

```java
@Transactional
public void processOtaReservation(OtaReservationEvent event) {
    String dedupKey = "ota-dedup:" + event.otaName() + ":" + event.otaReservationId();

    // Redis deduplication check (60-second window for in-flight dedup)
    if (redisTemplate.hasKey(dedupKey)) {
        log.info("Duplicate OTA event ignored: {}", event.otaReservationId());
        return;
    }
    redisTemplate.opsForValue().set(dedupKey, "1", Duration.ofSeconds(86400));

    Optional<Reservation> existing = reservationRepository
        .findByOtaReservationId(event.otaName(), event.otaReservationId());

    if (existing.isPresent()) {
        applyOtaModification(existing.get(), event);
    } else {
        createFromOtaEvent(event);
    }
}
```

### Conflict Resolution Rules

When there is a conflict between OTA data and PMS data:

| Field                | Winner    | Rationale                                                     |
|----------------------|-----------|---------------------------------------------------------------|
| Booking price / rate | OTA wins  | OTA contracted rate is legally binding                        |
| Room assignment      | PMS wins  | Hotel controls physical room allocation                       |
| Guest name / contact | OTA wins  | Guest data source of truth is OTA at booking time             |
| Check-in/out dates   | OTA wins  | Itinerary change comes from guest via OTA                     |
| Special requests     | Merge     | Combine PMS and OTA special requests (deduplicated)           |
| Cancellation         | First wins| First cancellation signal (either source) triggers cancel     |

### Retry with Exponential Backoff

OTA API calls (push ARI updates to Booking.com, Expedia) use exponential backoff with jitter:

```go
func (c *OTAClient) PushARI(ctx context.Context, payload ARIPayload) error {
    backoff := 500 * time.Millisecond
    maxRetries := 3
    for attempt := 0; attempt <= maxRetries; attempt++ {
        err := c.httpClient.Push(ctx, payload)
        if err == nil {
            return nil
        }
        if !isRetryable(err) || attempt == maxRetries {
            return fmt.Errorf("OTA push failed after %d attempts: %w", attempt+1, err)
        }
        jitter := time.Duration(rand.Int63n(int64(backoff) / 2))
        time.Sleep(backoff + jitter)
        backoff *= 2
    }
    return nil
}
```

### Dead-Letter Queue Handling

Messages that fail all retry attempts land in the DLQ. An alerting Lambda monitors each DLQ and:

1. Raises a P2 PagerDuty alert with the message payload and failure reason.
2. Writes the failure to the `ota_sync_errors` table for operational review.
3. For OTA cancellations in the DLQ, escalates to P1 and pages the on-call engineer immediately (missed cancellation = potential overbooking).

---

## API Development Standards

### RESTful API Conventions

- **URL format:** `/api/v{n}/{resource}` — plural nouns, lowercase, hyphens for multi-word resources.
- **Versioning:** URL-based (`/api/v1/`, `/api/v2/`). New breaking versions are introduced with a 6-month deprecation notice and `Sunset` header on deprecated endpoints.
- **HTTP methods:** GET (read, idempotent), POST (create), PUT (full replace), PATCH (partial update — JSON Merge Patch RFC 7396), DELETE (soft delete — sets `deleted_at`).
- **HTTP status codes:** 200 (OK), 201 (Created + `Location` header), 202 (Accepted — async operation), 204 (No Content — successful DELETE), 400 (Validation error), 401 (Authentication required), 403 (Insufficient scope), 404 (Not found), 409 (Conflict — booking race condition), 422 (Business rule violation), 429 (Rate limited), 500 (Unexpected error).
- **Error response format:**

```json
{
  "type": "https://hpms.hotel/errors/room-not-available",
  "title": "Room Not Available",
  "status": 409,
  "detail": "Room type KING is fully booked for 2025-08-15 to 2025-08-18.",
  "instance": "/api/v1/reservations",
  "traceId": "4bf92f3577b34da6a3ce929d0e0e4736",
  "timestamp": "2025-08-10T14:23:01Z"
}
```

### OpenAPI Specification

Every service maintains an OpenAPI 3.1 spec (`api/openapi.yaml`). The spec is the contract; code is generated from it (not the other way around). Client SDKs (TypeScript types, Go client) are generated from the spec during the build.

### Pagination

All list endpoints support cursor-based pagination:

```
GET /api/v1/reservations?propertyId=PROP-001&cursor=eyJpZCI6MTIzfQ&limit=50
```

Response includes:

```json
{
  "data": [...],
  "pagination": {
    "nextCursor": "eyJpZCI6MTczfQ",
    "hasMore": true,
    "total": 847
  }
}
```

Offset-based pagination is not used for large datasets due to the `OFFSET n` performance penalty at high page numbers.

---

## Testing Standards

### Test Pyramid

| Level               | Coverage Target | Tools                                   | Scope                                           |
|---------------------|-----------------|------------------------------------------|-------------------------------------------------|
| Unit                | ≥ 80% line      | JUnit 5, Mockito, pytest, Vitest         | Domain model, application service, domain rules |
| Integration         | All repositories| TestContainers (PostgreSQL, Redis, Kafka)| Repository adapters, cache services, consumers  |
| Contract (Consumer) | All OTA clients | Pact JVM                                 | ChannelManagerService consuming OTA webhooks    |
| Contract (Provider) | All APIs        | Pact JVM                                 | Verify ReservationService API matches consumers |
| E2E                 | Critical flows  | Playwright (web), Detox (mobile)         | Check-in, check-out, OTA booking flow           |
| Performance         | Availability API| Gatling                                  | 1000 RPS with p99 < 200 ms                     |
| Security            | OWASP Top 10    | OWASP ZAP, Snyk                          | API endpoints, dependency vulnerabilities       |

### Key Unit Test Requirements

Every aggregate root method must have a unit test for:
- Happy path with valid inputs.
- All domain exception paths (invalid state, business rule violations).
- Domain event registration (verify the correct event is registered after state transition).

```java
@Test
void checkin_shouldTransitionStatusAndRegisterEvent() {
    Reservation reservation = ReservationFixture.confirmedReservation();
    reservation.checkin(LocalDate.now(), "512");
    assertThat(reservation.getStatus()).isEqualTo(ReservationStatus.CHECKED_IN);
    assertThat(reservation.getDomainEvents())
        .hasSize(1)
        .first().isInstanceOf(CheckInCompletedEvent.class);
}

@Test
void checkin_whenNotConfirmed_shouldThrowInvalidStateException() {
    Reservation reservation = ReservationFixture.cancelledReservation();
    assertThatThrownBy(() -> reservation.checkin(LocalDate.now(), "512"))
        .isInstanceOf(InvalidReservationStateException.class);
}
```

### Performance Testing — Availability Search

The availability search endpoint (`GET /api/v1/availability`) must handle 1,000 requests per second with p99 latency under 200 ms. The Gatling test simulates:

- 50% cache hits (warm availability cache)
- 30% cache misses (PostgreSQL read replica fallback)
- 20% near-real-time queries (current day, always DB-fresh)

The test runs in the CI pipeline nightly against a staging environment with production-equivalent data volumes (12 months of availability data across 200 room types).

---

## Security Guidelines

### Input Validation

- All controller input is validated using Bean Validation (Jakarta Validation 3.0) before reaching the application layer.
- SQL injection prevention: use parameterised queries exclusively; no string concatenation in SQL.
- Use `@Size`, `@NotNull`, `@Pattern` annotations on all request DTOs.
- Strip all HTML/script tags from free-text fields (guest special requests) using OWASP Java HTML Sanitizer.

### Authentication and Authorisation

- JWT tokens are issued by the IdentityService (OAuth2/OIDC compliant, Keycloak 24).
- Token lifetime: 15 minutes access token, 8 hours refresh token.
- Scopes encode property access and role: `reservation:read`, `reservation:write`, `folio:read`, `folio:write`, `housekeeping:write`, `admin:all`.
- Kong API Gateway validates JWT signature and expiry on every request before forwarding to backend services.
- Backend services additionally verify the JWT `propertyId` claim matches the requested resource via the `@PropertyScoped` aspect.

### Sensitive Data Handling

- Guest passport/ID numbers are encrypted at the field level before persistence using KMS envelope encryption. The plaintext value is never logged.
- Payment card data is never stored. Stripe payment tokens (format `tok_...`) are the only payment identifier stored.
- Guest date-of-birth is stored as a SHA-256 hash for matching purposes; the plaintext is not retained after check-in.
- All PII fields are annotated with `@SensitiveData` which suppresses their values in log output.

---

## Observability Standards

### Structured Logging

All services log in JSON format. Log events include:

```json
{
  "timestamp": "2025-08-10T14:23:01.456Z",
  "level": "INFO",
  "service": "reservation-service",
  "traceId": "4bf92f3577b34da6a3ce929d0e0e4736",
  "spanId": "00f067aa0ba902b7",
  "propertyId": "PROP-001",
  "reservationId": "RES-2025-089342",
  "operation": "createReservation",
  "durationMs": 47,
  "message": "Reservation created successfully"
}
```

`traceId` and `spanId` are injected by the OpenTelemetry SDK and correlate log events with distributed traces in Grafana Tempo.

### Metrics

Each service exposes a `/metrics` endpoint in OpenTelemetry Prometheus format. Required metrics for every service:

- `http_requests_total` (counter) — by `method`, `path`, `status`
- `http_request_duration_seconds` (histogram) — by `method`, `path`
- `db_query_duration_seconds` (histogram) — by `query_name`
- `kafka_messages_published_total` (counter) — by `topic`
- `kafka_consumer_lag` (gauge) — by `topic`, `consumer_group`

### SLOs

| Service               | Availability SLO | Latency SLO (p99)     | Error Rate SLO |
|-----------------------|------------------|-----------------------|----------------|
| ReservationService    | 99.9%            | 500 ms                | < 0.1%         |
| FolioService          | 99.9%            | 1000 ms               | < 0.1%         |
| AvailabilitySearch    | 99.9%            | 200 ms                | < 0.1%         |
| CheckIn Flow          | 99.9%            | 2000 ms (end-to-end)  | < 0.5%         |

---

## Code Review Checklist

Before approving any PR touching backend services, reviewers must verify:

**Data Isolation:**
- [ ] All repository methods include `propertyId` as a parameter.
- [ ] No new query bypasses the `PropertyContext`.
- [ ] No raw SQL concatenates `propertyId` as a string; uses parameterised queries.

**Domain Rules:**
- [ ] Business rules are enforced inside the aggregate, not in the application service.
- [ ] State transitions register domain events via `registerEvent()`.
- [ ] No `setStatus()` calls directly on aggregates from outside the domain layer.

**OTA Integration:**
- [ ] All OTA event handlers are idempotent (upsert, not insert).
- [ ] Retry logic includes exponential backoff and a max retry count.
- [ ] Failed events are forwarded to the DLQ with a descriptive failure reason.

**Security:**
- [ ] No sensitive data (PII, payment tokens) appears in log output.
- [ ] JWT claims are verified at the service layer, not just at the gateway.
- [ ] Input validation annotations are present on all request DTOs.

**Testing:**
- [ ] Unit tests cover happy path and all exception paths for new domain logic.
- [ ] New repository methods have integration tests using TestContainers.
- [ ] New OTA webhook handlers have Pact consumer tests.

**Observability:**
- [ ] New operations emit structured log events with `traceId` and `propertyId`.
- [ ] New slow operations (> 100 ms expected) are measured with a histogram metric.
- [ ] New failure modes emit a specific error counter metric for alerting.

**Performance:**
- [ ] No new N+1 query patterns introduced (verify with `spring.jpa.show-sql=true` in tests).
- [ ] New cache keys follow the documented TTL strategy.
- [ ] New Kafka consumers include a consumer group and explicit offset commit strategy.
