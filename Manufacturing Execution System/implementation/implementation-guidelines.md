# Implementation Guidelines — Manufacturing Execution System

## Overview

This document defines the engineering standards, conventions, and implementation patterns for the Manufacturing Execution System (MES) serving discrete manufacturing operations. The MES orchestrates production orders, work center scheduling, OEE monitoring, quality management (SPC/inspection), material tracking, IoT/SCADA integration, and ERP (SAP) connectivity.

These guidelines apply to all engineers contributing to the platform. Adherence ensures consistency, maintainability, and production-grade reliability across a system that interacts with physical manufacturing assets.

**Technology Stack**

| Layer | Technology |
|---|---|
| Backend | Java 21 / Spring Boot 3.x (primary), Node.js 20 / TypeScript (edge adapters) |
| Frontend | React 18, TypeScript, Vite, TanStack Query |
| API Gateway | Spring Cloud Gateway |
| Messaging | Apache Kafka, MQTT (Mosquitto/HiveMQ) |
| Database | PostgreSQL 16 (transactional), TimescaleDB (time-series), Redis 7 (cache) |
| IoT/Edge | Node.js TypeScript edge agents, OPC-UA SDK |
| Search | OpenSearch |
| Observability | OpenTelemetry, Prometheus, Grafana |
| Deployment | Kubernetes (EKS), Helm, ArgoCD |

---

## Development Environment Setup

**Prerequisites**

| Tool | Minimum Version | Purpose |
|---|---|---|
| JDK | 21 (Temurin) | Backend services |
| Node.js | 20 LTS | Frontend, edge adapters |
| Docker Desktop | 4.x | Local containers |
| kubectl | 1.29+ | Cluster management |
| Helm | 3.14+ | Chart management |
| IntelliJ IDEA | 2024.1+ (Java) / VS Code | IDE |

**Local Stack Bootstrap**

```bash
# Clone and initialise submodules
git clone git@github.com:org/mes-platform.git
cd mes-platform
git submodule update --init --recursive

# Spin up local infrastructure (Postgres, Kafka, Redis, MQTT broker)
docker compose -f infra/docker-compose.dev.yml up -d

# Seed reference data (work centres, BOM, shift calendars)
./scripts/seed-dev-data.sh

# Start all backend services in watch mode
./scripts/dev-start.sh
```

**Environment Variables**

All secrets are managed via HashiCorp Vault in staging/production. Locally, copy `.env.example` to `.env.local` and populate values. Never commit `.env.local`. The `SPRING_PROFILES_ACTIVE` variable selects the Spring profile (`dev`, `staging`, `prod`).

---

## Coding Standards and Conventions

**Naming Conventions**

| Artifact | Convention | Example |
|---|---|---|
| Java package | `com.mes.<domain>.<layer>` | `com.mes.production.service` |
| Java class | PascalCase | `ProductionOrderService` |
| Java method | camelCase, verb-first | `calculateOee()`, `releaseOrder()` |
| REST endpoint | kebab-case nouns, plural | `/api/v1/production-orders` |
| Database table | snake_case, plural | `production_orders` |
| Database column | snake_case | `planned_start_time` |
| Kafka topic | `mes.<domain>.<event>` | `mes.production.order-released` |
| React component | PascalCase | `WorkCenterDashboard` |
| React hook | `use` prefix | `useOeeMetrics` |
| TypeScript interface | `I` prefix for contracts | `IProductionOrder` |
| Environment variable | SCREAMING_SNAKE_CASE | `SAP_RFC_CONNECTION_URL` |

**Commit Message Format** — Conventional Commits:

```
feat(production): add work-centre capacity check on order release
fix(oee): correct availability calculation for planned downtime
chore(deps): bump spring-boot to 3.3.2
```

**General Rules**

- Maximum method length: 30 lines. Extract to private helpers beyond this.
- Maximum class length: 300 lines. Beyond that, split responsibilities.
- No `null` returns from service methods — use `Optional<T>` or throw domain exceptions.
- All public APIs must have Javadoc / JSDoc.
- Logging uses SLF4J with structured arguments — no string concatenation in log calls.

---

## Backend Implementation Guidelines

**Package Structure (Java/Spring Boot)**

```
com.mes.production
  ├── api/               # REST controllers, request/response DTOs
  ├── application/       # Use-case orchestrators (ApplicationService)
  ├── domain/            # Entities, value objects, domain events, repository interfaces
  ├── infrastructure/    # JPA repositories, Kafka producers, SAP adapters
  └── config/            # Spring configuration, beans
```

**Production Order Service — Example**

```java
@Service
@Transactional
@Slf4j
public class ProductionOrderService {

    private final ProductionOrderRepository repository;
    private final WorkCenterService workCenterService;
    private final MaterialReservationService materialService;
    private final ApplicationEventPublisher eventPublisher;

    public ProductionOrder releaseOrder(String orderId) {
        ProductionOrder order = repository.findById(orderId)
            .orElseThrow(() -> new ProductionOrderNotFoundException(orderId));

        order.validate(); // domain invariant check
        workCenterService.checkCapacity(order.getWorkCenterId(), order.getPlannedStartTime());
        materialService.reserveMaterials(order.getBillOfMaterials(), order.getQuantity());

        order.release(); // transitions state machine: PLANNED → RELEASED
        repository.save(order);

        eventPublisher.publishEvent(new ProductionOrderReleasedEvent(order));
        log.info("Production order released orderId={} workCenter={}", orderId, order.getWorkCenterId());
        return order;
    }
}
```

**OEE Calculator — Example**

```java
@Component
public class OeeCalculator {

    /**
     * Calculates OEE components for a given shift window.
     * OEE = Availability × Performance × Quality
     */
    public OeeResult calculate(OeeInput input) {
        Duration plannedProductionTime = input.getShiftDuration()
            .minus(input.getPlannedDowntime());

        Duration actualRunTime = plannedProductionTime
            .minus(input.getUnplannedDowntime());

        double availability = safeDivide(
            actualRunTime.toMinutes(),
            plannedProductionTime.toMinutes()
        );

        double performance = safeDivide(
            (double) input.getActualCycles() * input.getIdealCycleTimeSeconds(),
            actualRunTime.toSeconds()
        );

        double quality = safeDivide(
            input.getGoodParts(),
            input.getTotalParts()
        );

        double oee = availability * performance * quality;

        return OeeResult.builder()
            .availability(availability)
            .performance(performance)
            .quality(quality)
            .oee(oee)
            .calculatedAt(Instant.now())
            .build();
    }

    private double safeDivide(double numerator, double denominator) {
        return denominator == 0 ? 0.0 : numerator / denominator;
    }
}
```

**Error Handling**

Domain exceptions extend `MesDomainException`. A global `@RestControllerAdvice` maps them to structured RFC 7807 `ProblemDetail` responses. Never expose stack traces to API consumers.

**Validation**

Bean Validation (`@Valid`) on controllers. Domain objects enforce invariants in constructors and mutators, throwing `IllegalArgumentException` for programming errors and domain exceptions for business rule violations.

---

## Frontend Implementation Guidelines

**Project Structure**

```
src/
  ├── features/               # Feature slices (production, quality, oee, materials)
  │   └── production/
  │       ├── api/            # TanStack Query hooks wrapping Axios
  │       ├── components/     # Feature-specific React components
  │       ├── hooks/          # Custom hooks (useProductionOrder, useWorkCenter)
  │       ├── stores/         # Zustand slices for local UI state
  │       └── types/          # TypeScript interfaces matching backend DTOs
  ├── shared/                 # Design system atoms, shared utilities
  ├── layouts/                # Shell, sidebar, header components
  └── pages/                  # Route-level page components
```

**Data Fetching Pattern**

Use TanStack Query for all server state. Keep Zustand only for UI state (selected rows, panel open/closed). Never store server data in Zustand.

```tsx
// features/oee/api/useOeeMetrics.ts
export function useOeeMetrics(workCenterId: string, shiftDate: string) {
  return useQuery({
    queryKey: ['oee', workCenterId, shiftDate],
    queryFn: () => oeeApi.getMetrics(workCenterId, shiftDate),
    refetchInterval: 30_000, // live dashboard refresh
    staleTime: 15_000,
  });
}
```

**Real-Time Updates**

WebSocket connections (SockJS + STOMP) subscribe to work-centre topics for live OEE and alarm feeds. Use a dedicated `useWebSocket` hook that handles reconnection, backoff, and cleanup on component unmount.

**Accessibility**

All interactive elements must meet WCAG 2.1 AA. Use semantic HTML. Chart components (Recharts/Victory) must include `aria-label` descriptions and tabular data alternatives.

---

## Database Implementation Guidelines

**Schema Conventions**

- Every table includes `id UUID PRIMARY KEY DEFAULT gen_random_uuid()`, `created_at TIMESTAMPTZ DEFAULT NOW()`, `updated_at TIMESTAMPTZ DEFAULT NOW()`, `version BIGINT DEFAULT 0` (optimistic locking).
- Soft deletes via `deleted_at TIMESTAMPTZ NULL`. Active-only queries use a partial index: `CREATE INDEX idx_production_orders_active ON production_orders(work_center_id) WHERE deleted_at IS NULL`.
- Foreign keys are always declared; cascades require explicit review approval.

**Time-Series Data (TimescaleDB)**

Machine telemetry, OEE snapshots, and SPC measurements are written to TimescaleDB hypertables partitioned by 1-hour chunks. Use continuous aggregates for shift and daily rollups — never compute aggregations in application code for reporting queries.

```sql
-- Hypertable for machine telemetry
CREATE TABLE machine_telemetry (
    time         TIMESTAMPTZ NOT NULL,
    machine_id   UUID        NOT NULL,
    metric_name  TEXT        NOT NULL,
    value        DOUBLE PRECISION,
    quality_code SMALLINT    DEFAULT 0
);
SELECT create_hypertable('machine_telemetry', 'time', chunk_time_interval => INTERVAL '1 hour');
CREATE INDEX ON machine_telemetry (machine_id, time DESC);

-- Continuous aggregate: hourly OEE rollup
CREATE MATERIALIZED VIEW oee_hourly
WITH (timescaledb.continuous) AS
SELECT time_bucket('1 hour', time) AS bucket,
       machine_id,
       AVG(value) FILTER (WHERE metric_name = 'oee') AS avg_oee
FROM machine_telemetry
GROUP BY bucket, machine_id;
```

**Migrations**

Flyway manages all schema changes. Scripts are named `V{version}__{description}.sql`. Migrations must be backward-compatible for zero-downtime deployments — use expand/contract pattern for column changes.

---

## IoT/Edge Implementation Guidelines

**MQTT Subscriber — Node.js/TypeScript**

```typescript
import mqtt, { MqttClient } from 'mqtt';
import { KafkaProducer } from './kafka/KafkaProducer';
import { TelemetryPayload } from './types';
import { logger } from './logger';

export class MqttSubscriber {
  private client: MqttClient;

  constructor(
    private readonly brokerUrl: string,
    private readonly kafkaProducer: KafkaProducer,
  ) {}

  start(): void {
    this.client = mqtt.connect(this.brokerUrl, {
      clientId: `mes-edge-${process.env.EDGE_UNIT_ID}`,
      clean: false,
      reconnectPeriod: 5_000,
    });

    this.client.on('connect', () => {
      logger.info('MQTT connected', { broker: this.brokerUrl });
      this.client.subscribe('factory/+/telemetry/#', { qos: 1 });
    });

    this.client.on('message', async (topic, payload) => {
      await this.handleMessage(topic, payload);
    });

    this.client.on('error', (err) =>
      logger.error('MQTT error', { err: err.message }),
    );
  }

  private async handleMessage(topic: string, raw: Buffer): Promise<void> {
    const data: TelemetryPayload = JSON.parse(raw.toString());
    await this.kafkaProducer.send('mes.telemetry.raw', {
      key: data.machineId,
      value: data,
    });
  }
}
```

**OPC-UA Integration**

Use the `node-opcua` SDK for direct PLC connectivity. Tag mappings are stored in the `edge_tag_config` database table and reloaded without restart via a config watch mechanism. Dead-band filtering suppresses noise — only publish when a value changes beyond the configured threshold.

**Edge Reliability**

Edge agents operate in store-and-forward mode. When Kafka is unreachable, messages are buffered to a local SQLite queue (max 100k records / 24h TTL). On reconnection, buffered messages replay in order before live data resumes.

---

## Integration Implementation Guidelines

**SAP ERP Integration**

Communication uses SAP JCo (Java Connector) for RFC calls and IDocs via SAP PI/PO or direct RFC. A dedicated `SapIntegrationService` wraps all RFC calls with circuit breaker (Resilience4j) and retry logic.

```java
@Service
public class SapProductionOrderAdapter {

    @CircuitBreaker(name = "sap", fallbackMethod = "fallbackOrderSync")
    @Retry(name = "sap")
    public void confirmProductionOrder(String sapOrderNumber, BigDecimal confirmedQty) {
        JCoFunction function = sapDestination.getRepository()
            .getFunction("BAPI_PRODORD_CONFIRM_CREATE");
        function.getImportParameterList().setValue("ORDERID", sapOrderNumber);
        function.getImportParameterList().setValue("YIELD", confirmedQty);
        function.execute(sapDestination);
        // Check RETURN bapiret2 table for errors
        checkBapiReturn(function.getTableParameterList().getTable("RETURN"));
    }

    private void fallbackOrderSync(String sapOrderNumber, BigDecimal qty, Exception ex) {
        log.warn("SAP circuit open — queuing confirmation sapOrder={}", sapOrderNumber);
        outboxRepository.save(new OutboxEvent("SAP_CONFIRM", sapOrderNumber, qty));
    }
}
```

**SCADA Integration**

SCADA systems publish data via OPC-UA or MQTT. The MES edge layer normalises payloads to the internal `TelemetryPayload` schema before forwarding to Kafka. Never allow raw SCADA payloads into the core domain model.

**Outbox Pattern**

All integration events (SAP confirmations, EWM goods movements) use the transactional outbox pattern. Events are written to `integration_outbox` within the same database transaction as the domain change, then a dedicated relay process polls and publishes to Kafka/SAP.

---

## Testing Strategy

**Coverage Targets**

| Module | Unit % | Integration % | E2E % |
|---|---|---|---|
| Production Orders | 90 | 80 | 60 |
| OEE Engine | 95 | 85 | 50 |
| Quality / SPC | 90 | 80 | 60 |
| Material Tracking | 85 | 75 | 50 |
| SAP Integration | 80 | 70 | 40 |
| SCADA / MQTT | 80 | 65 | 40 |
| Edge Agents | 85 | 70 | — |

**Unit Tests**

JUnit 5 + Mockito for Java. Vitest for TypeScript. Test domain logic in isolation — no Spring context, no database. OEE calculator and SPC algorithms have property-based tests using jqwik.

**Integration Tests**

Spring Boot's `@SpringBootTest` with Testcontainers (PostgreSQL, Kafka, Redis). Tests cover full service → repository → database round trips. MQTT integration uses an embedded Mosquitto container.

**OT Simulation**

A `PLCSimulator` test utility replays recorded MQTT/OPC-UA capture files to simulate machine cycles, alarms, and fault events without physical hardware. Used in the CI pipeline to validate edge agent behaviour.

**E2E Tests**

Playwright drives the React frontend against a full Docker Compose stack with seeded data. Critical paths: release production order → scan materials → record operations → complete order → verify SAP confirmation sent.

---

## Security Implementation Guidelines

- **Authentication**: OAuth 2.0 / OIDC via Keycloak. All API calls require a valid JWT bearer token.
- **Authorisation**: RBAC enforced via Spring Security method-level annotations (`@PreAuthorize`). Roles: `MES_OPERATOR`, `MES_SUPERVISOR`, `MES_ENGINEER`, `MES_ADMIN`, `MES_READONLY`.
- **Secrets Management**: HashiCorp Vault with dynamic database credentials. No static passwords in environment variables or config files in staging/production.
- **Network Isolation**: OT network (SCADA/PLCs) is isolated from IT. Edge agents are the only components allowed to bridge the DMZ, communicating inbound to Kafka only.
- **Input Validation**: All external inputs validated at controller layer. SAP IDoc payloads and MQTT messages are schema-validated before processing.
- **Audit Logging**: All production-impacting actions (order state changes, quality disposition, material movements) are written to an immutable `audit_log` table signed with HMAC.
- **TLS**: All inter-service communication uses mutual TLS (mTLS) within the cluster. MQTT brokers require client certificates for edge agents.

---

## Performance Guidelines

**API Response Targets**

| Endpoint Category | p50 | p99 |
|---|---|---|
| Production order read | < 50 ms | < 200 ms |
| OEE dashboard query | < 200 ms | < 800 ms |
| SPC chart data | < 300 ms | < 1 000 ms |
| Material scan (write path) | < 100 ms | < 400 ms |

**Design Principles**

- Cache reference data (work centres, BOM, shift calendars) in Redis with a 5-minute TTL. Invalidate on update events.
- Kafka consumers use batch processing (max 500 records/poll) for telemetry ingestion. Avoid per-message database writes — use COPY or batched INSERTs.
- Database queries on reporting paths use read replicas exclusively. Write path uses the primary.
- Paginate all list APIs (default page size 50, max 200). Cursor-based pagination for time-series endpoints.

---

## Deployment Guidelines

**Environments**

| Environment | Purpose | Promotion Gate |
|---|---|---|
| `dev` | Feature development | Automated CI pass |
| `staging` | Integration, UAT | Manual approval |
| `production` | Live manufacturing | Change Advisory Board |

**Release Process**

Trunk-based development. Feature flags (Unleash) gate incomplete features. Releases are tagged semver. ArgoCD applies Helm charts on Git push to the `release/*` branch after a staging green build.

**Zero-Downtime Deployments**

Rolling updates with `maxSurge: 1, maxUnavailable: 0`. Database migrations run as pre-upgrade Helm hooks with a readiness probe ensuring the new pod only receives traffic after health checks pass. The Flyway `outOfOrder: false` setting enforces migration sequence.

**Observability**

Every service exports Prometheus metrics on `/actuator/prometheus`. The standard dashboard includes: JVM memory, GC pause, HTTP request rate/latency (p50/p95/p99), Kafka consumer lag, and custom OEE metrics. Alert thresholds are defined in `infra/alerting/rules/`.

---

## Code Review Process

**Pull Request Requirements**

| Criterion | Requirement |
|---|---|
| Branch naming | `feat/<ticket>-description`, `fix/<ticket>-description` |
| PR size | < 400 lines of production code change |
| Reviewers | Minimum 2 approvals; 1 must be a domain owner |
| CI gates | Build, unit tests, integration tests, SAST scan must pass |
| Coverage delta | Must not decrease below module target |
| Migration review | DB migrations require DBA or senior engineer approval |

**Review Checklist**

Reviewers verify: domain invariants are enforced in the domain layer (not just controllers), no raw SQL in service classes, integration points are wrapped with circuit breakers, secrets not hardcoded, OT-related changes reviewed by the controls/automation engineer, and Kafka schema changes are backward-compatible.

**Hotfix Process**

Hotfixes branch from the production tag, are reviewed by at least one senior engineer, deployed to staging for a smoke test, then cherry-picked back to the main trunk within 24 hours of production deployment.
