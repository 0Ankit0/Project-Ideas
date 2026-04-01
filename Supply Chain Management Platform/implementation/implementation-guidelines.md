# Implementation Guidelines — Supply Chain Management Platform

## Purpose

These guidelines govern how all engineering teams develop, test, and deploy the Supply Chain Management Platform (SCMP). All engineers, contractors, and contributors are expected to follow these conventions. Deviations require an Architecture Decision Record (ADR) reviewed by the platform lead.

---

## 1. Technology Stack

| Layer | Technology | Version | Rationale |
|---|---|---|---|
| Backend language | Java | 21 (LTS) | Virtual threads (Project Loom) for high-concurrency I/O workloads |
| Backend framework | Spring Boot | 3.2.x | Auto-configuration, native GraalVM support for fast cold starts |
| Build tool | Gradle (multi-project) | 8.x | Faster incremental builds than Maven for large monorepos |
| Frontend language | TypeScript | 5.x | Type safety across supplier portal and buyer console |
| Frontend framework | React | 18.x | Concurrent rendering; Zustand for state management |
| Frontend build | Vite | 5.x | Fast HMR; ES module bundling |
| Primary database | PostgreSQL | 15.x | JSONB for flexible supplier metadata; partitioning for PO history |
| DB migrations | Flyway | 9.x | Versioned, repeatable, and baseline migrations |
| Cache | Redis | 7.x (Lettuce client) | Reactive Redis commands; cluster mode |
| Messaging | Apache Kafka | 3.5.x (via Spring Kafka) | High-throughput domain event bus |
| API layer | Spring Web MVC + OpenAPI 3.1 | — | Synchronous REST; async via Kafka for long-running ops |
| Auth | Spring Security 6 + OAuth2 Resource Server | — | JWT validation; Keycloak as IdP |
| Containerization | Docker + Helm | — | Helm charts per microservice |
| Observability | OpenTelemetry SDK + Micrometer | — | Unified trace/metric/log pipeline |

---

## 2. Project Structure

The platform is organized as a single Gradle multi-project build under `scmp-platform/`:

```
scmp-platform/
├── build.gradle                    # Root build — shared dependency versions (BOM)
├── settings.gradle                 # All subproject declarations
├── gradle/
│   └── libs.versions.toml          # Gradle version catalog
├── services/
│   ├── supplier-service/
│   ├── po-service/
│   ├── receipt-service/
│   ├── matching-engine/
│   ├── invoice-service/
│   ├── payment-service/
│   ├── performance-service/
│   ├── rfq-service/
│   ├── contract-service/
│   ├── forecast-service/
│   ├── notification-service/
│   └── audit-service/
├── shared/
│   ├── scmp-domain/                # Shared domain types (Money, OrgId, etc.)
│   ├── scmp-events/                # Kafka event schemas (Avro + POJO)
│   ├── scmp-security/              # Security config, JWT utils
│   └── scmp-testing/               # Testcontainers fixtures, factories
└── frontend/
    ├── buyer-console/
    └── supplier-portal/
```

### Individual Service Internal Structure

```
po-service/
├── src/
│   ├── main/
│   │   ├── java/com/scmp/po/
│   │   │   ├── api/                  # REST controllers, DTOs, request/response mappers
│   │   │   ├── application/          # Use cases (CreatePOUseCase, etc.), command/query handlers
│   │   │   ├── domain/               # Entities, value objects, domain events, domain services
│   │   │   ├── infrastructure/       # JPA repositories, Kafka producers, Redis adapters
│   │   │   └── config/               # Spring configuration classes
│   │   └── resources/
│   │       ├── application.yml
│   │       └── db/migration/         # Flyway SQL files
│   └── test/
│       ├── java/com/scmp/po/
│       │   ├── unit/
│       │   ├── integration/
│       │   └── contract/
│       └── resources/
│           └── testcontainers/
```

---

## 3. Coding Standards

### Naming Conventions

| Element | Convention | Example |
|---|---|---|
| Java class | PascalCase | `PurchaseOrderService` |
| Java method | camelCase | `calculateTotalAmount` |
| Java constant | UPPER_SNAKE_CASE | `MAX_PO_LINE_ITEMS` |
| Java package | lowercase.dot.separated | `com.scmp.po.domain` |
| REST endpoint path | lowercase-kebab-case | `/purchase-orders/{id}/change-orders` |
| Kafka topic | dot-separated, past tense noun | `scmp.po.purchase-order.created` |
| Kafka consumer group | `{service}-{topic-suffix}-consumer` | `matching-engine-invoice-received-consumer` |
| Database table | snake_case, plural | `purchase_orders`, `po_lines` |
| Database column | snake_case | `created_at`, `supplier_id` |
| TypeScript component | PascalCase | `PurchaseOrderDetail` |
| TypeScript hook | camelCase, `use` prefix | `usePurchaseOrder` |
| TypeScript type | PascalCase | `PurchaseOrderStatus` |

### Spring Patterns

- **Controller**: Only handles HTTP concerns (request parsing, response mapping, status codes). No business logic.
- **Use Case / Application Service**: Orchestrates domain logic. One public method per use case. Annotated `@Transactional` only at this layer.
- **Domain Service**: Pure business logic; no Spring beans, no I/O. Testable without a container.
- **Repository Interface**: Defined in `domain/` package (port). Implemented in `infrastructure/` (adapter).
- **Domain Events**: Published via `ApplicationEventPublisher` within the transaction, then forwarded to Kafka via a transactional outbox pattern.

### Exception Handling Hierarchy

```
ScmpException (abstract)
├── ScmpValidationException       → HTTP 400
├── ScmpNotFoundException         → HTTP 404
├── ScmpConflictException         → HTTP 409  (e.g., duplicate PO, version conflict)
├── ScmpForbiddenException        → HTTP 403
└── ScmpProcessingException       → HTTP 422  (e.g., matching rule failure)
```

A `@RestControllerAdvice` class (`GlobalExceptionHandler`) maps all `ScmpException` subtypes to the standard error response format. Never let Spring's default `DefaultHandlerExceptionResolver` produce responses.

---

## 4. Database Conventions

### Table Standards

- All tables include: `id UUID PRIMARY KEY DEFAULT gen_random_uuid()`, `org_id UUID NOT NULL`, `created_at TIMESTAMPTZ NOT NULL DEFAULT now()`, `updated_at TIMESTAMPTZ NOT NULL DEFAULT now()`, `created_by UUID`, `updated_by UUID`, `is_deleted BOOLEAN NOT NULL DEFAULT FALSE`.
- Soft deletes only: never `DELETE` business records. Set `is_deleted = TRUE` and `deleted_at = now()`.
- All `org_id` columns have an index; all `status` columns used in WHERE clauses are indexed.
- Foreign keys are declared but constraint enforcement uses `DEFERRABLE INITIALLY DEFERRED` for batch imports.
- Large text fields (supplier notes, PO terms) use `TEXT`; structured variant data uses `JSONB`.

### Flyway Migration Naming

```
V{n}__{short_description}.sql         # Versioned (schema changes, data backfills)
R__{name}.sql                         # Repeatable (views, stored procedures)
B__baseline.sql                       # Baseline (existing schema snapshot for new environments)
```

Examples:
```
V1__create_purchase_orders.sql
V2__add_currency_to_po_lines.sql
V15__backfill_supplier_performance_tier.sql
R__vw_po_summary.sql
```

### Indexes Policy

- Always create a compound index on `(org_id, status)` for high-query tables (`purchase_orders`, `invoices`).
- Use partial indexes for soft deletes: `WHERE is_deleted = FALSE`.
- Avoid indexes on low-cardinality boolean columns unless combined with high-cardinality columns.
- New indexes must be created `CONCURRENTLY` in production migrations.

---

## 5. API Standards

### RESTful Conventions

- Resource names are plural nouns: `/purchase-orders`, `/suppliers`, `/rfqs`.
- Sub-resources represent ownership: `/purchase-orders/{id}/lines`, `/purchase-orders/{id}/change-orders`.
- Actions that are not CRUD are expressed as sub-resources with verbs: `POST /purchase-orders/{id}/approve`, `POST /purchase-orders/{id}/cancel`.

### Versioning

- All APIs are versioned via URL prefix: `/api/v1/`, `/api/v2/`.
- A new major version is created only for breaking changes. Deprecation period is minimum 6 months.
- `Sunset` and `Deprecation` headers are added to deprecated endpoints.

### Pagination

All list endpoints support two pagination modes:

```json
// Offset-based (simple UIs)
GET /purchase-orders?page=0&size=25&sort=createdAt,desc

// Cursor-based (real-time feeds, large datasets)
GET /purchase-orders?cursor=eyJpZCI6IjEyMyJ9&limit=25
```

Response envelope:
```json
{
  "data": [...],
  "pagination": {
    "totalElements": 1234,
    "totalPages": 50,
    "currentPage": 0,
    "pageSize": 25,
    "nextCursor": "eyJpZCI6IjE0OCJ9"
  }
}
```

### Standard Error Response

```json
{
  "error": {
    "code": "PO_VERSION_CONFLICT",
    "message": "Purchase order has been modified since last read.",
    "details": [
      { "field": "version", "issue": "Expected 3, found 4" }
    ],
    "traceId": "4bf92f3577b34da6a3ce929d0e0e4736",
    "timestamp": "2024-03-15T14:32:00Z"
  }
}
```

### Idempotency

- All `POST` endpoints that create or mutate state accept an `Idempotency-Key: <uuid>` header.
- Keys are stored in Redis with a 24-hour TTL. Duplicate requests within the window return the original response.
- If a request is still processing, return HTTP 202 with a `Retry-After` header.

---

## 6. Event-Driven Design

### Kafka Topic Naming

Format: `{domain}.{aggregate}.{event-name}` — all lowercase, hyphenated.

```
scmp.po.purchase-order.created
scmp.po.purchase-order.approved
scmp.po.purchase-order.change-order.issued
scmp.receipt.goods-receipt.posted
scmp.invoice.invoice.received
scmp.matching.match.completed
scmp.matching.discrepancy.raised
scmp.supplier.qualification.approved
scmp.payment.payment.executed
```

### Event Schema (JSON — CloudEvents 1.0 envelope)

```json
{
  "specversion": "1.0",
  "id": "8d3e6f01-2b4c-4a8e-9c1d-7f2e3a4b5c6d",
  "source": "scmp/po-service",
  "type": "scmp.po.purchase-order.approved",
  "datacontenttype": "application/json",
  "time": "2024-03-15T14:32:00Z",
  "data": {
    "orgId": "550e8400-e29b-41d4-a716-446655440000",
    "purchaseOrderId": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "poNumber": "PO-2024-00842",
    "supplierId": "...",
    "totalAmount": { "amount": 48500.00, "currency": "USD" },
    "approvedBy": "user-id",
    "approvedAt": "2024-03-15T14:32:00Z"
  }
}
```

### Consumer Patterns

- Every consumer group is named `{service-name}-{topic-suffix}-consumer`.
- Consumers are **idempotent**: all handlers check if the event has already been processed (via `processed_events` table keyed on `event.id`).
- Failed messages after 3 retries (exponential backoff: 1s, 5s, 30s) are routed to `{original-topic}.dlq`.
- DLQ consumers alert via PagerDuty and store events in `dead_letter_events` table for manual replay.
- Avoid Kafka transactions for read-process-write patterns across multiple topics; use the outbox pattern instead.

---

## 7. Testing Strategy

### Pyramid Breakdown

| Layer | Framework | Scope | Target Coverage |
|---|---|---|---|
| Unit | JUnit 5 + Mockito | Domain logic, use cases, value objects | 90%+ |
| Integration | Testcontainers (PostgreSQL + Redis + Kafka) | Repository, Kafka producer/consumer, cache | 70%+ |
| Contract | Pact (consumer-driven) | API contracts between services | All inter-service calls |
| E2E | Playwright (TypeScript) | Critical buyer/supplier user journeys | Top 10 flows |

### Minimum Coverage Requirement

- **Overall**: 80% line coverage measured by JaCoCo.
- **Domain layer**: 95%+ (enforced in CI via JaCoCo rule on `com.scmp.*.domain` package).
- Coverage reports are published to SonarCloud on every PR. PRs cannot be merged below threshold.

### Test Data

- Use the `TestDataFactory` class from `scmp-testing` module (builder pattern) — never construct entities manually in tests.
- Integration tests use `@Sql` scripts to seed data; never rely on test execution order.
- No production data in test environments. Synthetic data generators (`Faker` library) for realistic-looking values.

---

## 8. Security

### Authentication & Authorization

- All APIs are protected by Spring Security OAuth2 Resource Server validating RS256-signed JWTs.
- Keycloak is the Identity Provider. Tokens expire in 15 minutes; refresh tokens in 8 hours.
- Roles are embedded in the JWT `realm_access.roles` claim: `ROLE_BUYER`, `ROLE_APPROVER`, `ROLE_SUPPLIER`, `ROLE_FINANCE`, `ROLE_ADMIN`.
- Use `@PreAuthorize("hasRole('APPROVER')")` at the use case level — not the controller.

### Multi-Tenant Row-Level Security

- Every database query must include `AND org_id = :orgId` predicated by the authenticated user's `orgId` claim.
- A Spring `HandlerInterceptor` extracts `orgId` from the JWT and stores it in a `TenantContext` `ThreadLocal`.
- All JPA repositories extend `OrgScopedRepository<T>` which auto-applies the tenant filter via Hibernate filters.
- **Never** skip the `org_id` filter. Violations must trigger a security alert.

### Input Validation

- All request DTOs use Jakarta Bean Validation annotations (`@NotNull`, `@Size`, `@Pattern`).
- Custom validators enforce business rules (e.g., `@ValidCurrencyCode`, `@ValidUOM`).
- Validated at the controller layer via `@Valid`; validation errors produce 400 with field-level detail.
- SQL injection: all queries use Spring Data JPA / named parameters. Native queries are reviewed in code review. No string concatenation in SQL.

---

## 9. Performance

### Connection Pooling (HikariCP)

```yaml
spring.datasource.hikari:
  maximum-pool-size: 20
  minimum-idle: 5
  connection-timeout: 20000      # 20 seconds
  idle-timeout: 600000           # 10 minutes
  max-lifetime: 1800000          # 30 minutes
  leak-detection-threshold: 60000
```

### Redis Caching Strategy

| Cache | TTL | Eviction Strategy | Key Pattern |
|---|---|---|---|
| Supplier profile | 10 minutes | LRU | `supplier:{orgId}:{supplierId}` |
| Item master / UOM | 60 minutes | LRU | `item:{orgId}:{itemId}` |
| Price list (active) | 5 minutes | LRU | `pricelist:{orgId}:{supplierId}:{currency}` |
| PO approval workflow state | Session TTL | Explicit delete | `po:approval:{poId}` |
| Idempotency key | 24 hours | TTL expiry | `idempotency:{key}` |

### Async Processing

- Long-running operations (bulk PO import, 3-way matching batch, supplier scoring recalculation) are processed asynchronously via Kafka.
- API returns HTTP 202 Accepted with a `Location: /jobs/{jobId}` header. Client polls or subscribes to WebSocket for completion.
- Batch jobs (nightly forecast recalculation, monthly KPI aggregation) run via Spring Batch on dedicated EKS job pods.

---

## 10. Observability

### Structured Logging (Logback + JSON)

Every log entry includes:
```json
{
  "timestamp": "2024-03-15T14:32:00.123Z",
  "level": "INFO",
  "service": "po-service",
  "traceId": "4bf92f3577b34da6a3ce929d0e0e4736",
  "spanId": "a2fb4a1d1a96d312",
  "orgId": "550e8400-e29b-41d4-a716-446655440000",
  "userId": "user-uuid",
  "message": "Purchase order approved",
  "poId": "7c9e6679...",
  "duration_ms": 45
}
```

- Log level `INFO` for all business events. `DEBUG` only in dev/staging.
- Never log PII (supplier contact names, bank details). Log IDs only.
- Log aggregation: CloudWatch Logs → Kinesis Firehose → S3 → Athena for long-term querying.

### Prometheus Metrics (via Micrometer)

Key metrics to instrument:

```
scmp_po_created_total{org_id, currency}                  # Counter
scmp_po_approval_duration_seconds{org_id, status}        # Histogram
scmp_matching_result_total{org_id, result}               # Counter: matched/partial/exception
scmp_invoice_processing_lag_seconds{org_id}              # Gauge
scmp_kafka_consumer_lag{consumer_group, topic}           # Gauge (via JMX exporter)
scmp_db_query_duration_seconds{service, query_name}      # Histogram
```

### Alerting Thresholds (PagerDuty)

| Alert | Condition | Severity |
|---|---|---|
| PO creation error rate | > 1% over 5 minutes | P1 |
| Matching engine queue depth | > 1000 messages for > 10 minutes | P2 |
| DB connection pool exhaustion | Available connections < 2 | P1 |
| JWT validation failure spike | > 50 failures/minute | P2 |
| DLQ message count | Any message in DLQ | P3 |
| Supplier portal 5xx rate | > 2% over 2 minutes | P1 |
