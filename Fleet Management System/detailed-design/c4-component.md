# C4 Component Diagrams

## Overview

This document provides drill-down C4 Level 3 component diagrams for the two most architecturally significant services: the **Tracking Service**, which is the highest-throughput service in the system, and the **Trip Service**, which orchestrates the core business workflow. For each service, the diagram shows internal components, their relationships, and how they interact with stores and external containers. Interface contracts and applied design patterns are documented at the end to give implementors a precise implementation target.

The Tracking Service must sustain ingest rates of up to 50,000 GPS pings per second during peak hours across all tenants. The Trip Service is the primary orchestrator, coordinating Vehicle Service, Driver Service, and external mapping providers in a single transactional workflow. Both services are designed so that their read path (queries) and write path (commands) are independently scalable — a principle formalised by the CQRS pattern applied throughout.

---

## C4 Component Diagram — Tracking Service

The Tracking Service is a headless consumer service. It has no REST endpoints exposed to the API Gateway for writes; all data enters via the Kafka topic `gps.pings.raw` bridged from AWS IoT Core. It exposes a read-only REST API for live position queries, consumed by the Web Application and Mobile App via the API Gateway.

```mermaid
C4Component
    title C4 Component Diagram — Tracking Service

    Container_Boundary(trackingService, "Tracking Service (Node.js / TypeScript)") {
        Component(mqttConsumer, "MQTTConsumer", "kafkajs KafkaConsumer", "Polls gps.pings.raw Kafka topic in batches of up to 500 records with a 100ms timeout. Manages consumer group offsets and handles rebalance events.")

        Component(payloadValidator, "PayloadValidator", "Zod schema", "Validates each ping: coordinate bounds, timestamp staleness (<60s), device ID format, required fields. Forwards valid pings; routes invalid to dead-letter topic.")

        Component(pingEnricher, "PingEnricher", "In-process service", "Enriches validated pings with tenant ID (resolved from device registry), vehicle metadata, and reverse-geocoded address (cached). Adds server-receipt timestamp.")

        Component(timescaleWriter, "TimescaleDBWriter", "node-postgres (COPY protocol)", "Batch-inserts enriched GPS pings into the gps_pings hypertable. Uses PostgreSQL COPY for throughput. Flushes every 250ms or 1000 rows, whichever comes first.")

        Component(redisUpdater, "RedisPositionUpdater", "ioredis pipeline", "Writes current position to Redis hash vehicle:{vehicleId} with 90s TTL. Uses pipelining to batch Redis commands across the current consumer batch.")

        Component(kafkaPublisher, "KafkaPublisher", "kafkajs KafkaProducer", "Publishes enriched GpsPingProcessed events to fleet.tracking.processed topic. Used by downstream consumers (Alert Service, Compliance Service).")

        Component(geofenceEvaluator, "GeofenceEvaluator", "@turf/boolean-point-in-polygon", "Loads active geofence polygons per tenant from Redis (refreshed every 60s). Evaluates each ping; emits GeofenceEntered or GeofenceExited events when transition detected.")

        Component(speedDetector, "SpeedViolationDetector", "Rule engine + HERE Maps road cache", "Compares vehicle reported speed against road-segment speed limit (cached from HERE Maps, refreshed daily). Emits SpeedViolationDetected when exceeded by configurable threshold.")

        Component(alertPublisher, "AlertPublisher", "kafkajs KafkaProducer", "Publishes GeofenceBreach and SpeedViolation events to fleet.alerts Kafka topic, consumed by Alert Service.")

        Component(positionQueryHandler, "PositionQueryHandler", "Express.js Router", "Read-only REST endpoint GET /vehicles/{id}/position and GET /vehicles/positions (bulk). Reads from Redis; falls back to TimescaleDB on cache miss.")

        Component(deviceRegistry, "DeviceRegistry", "PostgreSQL read model", "In-memory cache (refreshed every 5 minutes) of device-ID to vehicleId/tenantId mappings. Used by PingEnricher to resolve tenant context without a per-ping DB query.")
    }

    ContainerDb(kafka, "Kafka (MSK)", "gps.pings.raw / fleet.alerts")
    ContainerDb(timescaledb, "TimescaleDB", "gps_pings hypertable")
    ContainerDb(redis, "Redis (ElastiCache)", "Live position hashes")
    ContainerDb(postgres, "PostgreSQL (RDS)", "Device registry, geofence configs")
    Container(apiGateway, "API Gateway (Kong)", "Routes position queries")

    Rel(kafka, mqttConsumer, "Kafka POLL", "kafkajs / TCP")
    Rel(mqttConsumer, payloadValidator, "passes raw ping")
    Rel(payloadValidator, pingEnricher, "passes validated ping")
    Rel(pingEnricher, deviceRegistry, "resolves tenantId / vehicleId")
    Rel(deviceRegistry, postgres, "reads device registry", "SQL on startup + 5min refresh")
    Rel(pingEnricher, timescaleWriter, "forwards enriched ping")
    Rel(pingEnricher, redisUpdater, "forwards enriched ping")
    Rel(pingEnricher, kafkaPublisher, "forwards enriched ping")
    Rel(timescaleWriter, timescaledb, "COPY INSERT", "TCP / SQL")
    Rel(redisUpdater, redis, "HSET pipeline", "RESP / TCP")
    Rel(kafkaPublisher, kafka, "PRODUCE to fleet.tracking.processed", "kafkajs")
    Rel(pingEnricher, geofenceEvaluator, "forwards enriched ping")
    Rel(geofenceEvaluator, redis, "reads geofence cache", "HGETALL")
    Rel(geofenceEvaluator, alertPublisher, "GeofenceBreach event")
    Rel(pingEnricher, speedDetector, "forwards enriched ping")
    Rel(speedDetector, alertPublisher, "SpeedViolation event")
    Rel(alertPublisher, kafka, "PRODUCE to fleet.alerts", "kafkajs")
    Rel(apiGateway, positionQueryHandler, "GET /vehicles/positions", "HTTP/2")
    Rel(positionQueryHandler, redis, "HGET vehicle:{id}", "RESP")
    Rel(positionQueryHandler, timescaledb, "fallback: SELECT latest ping", "SQL")
```

---

## C4 Component Diagram — Trip Service

The Trip Service exposes a REST API and orchestrates cross-service workflows. It uses the Outbox Pattern to guarantee that state changes and Kafka events are published atomically even if the broker is temporarily unavailable.

```mermaid
C4Component
    title C4 Component Diagram — Trip Service

    Container_Boundary(tripService, "Trip Service (Node.js / TypeScript)") {
        Component(tripAPIController, "TripAPIController", "Express.js Router", "Handles REST endpoints: POST /trips (create), PUT /trips/:id/start, PUT /trips/:id/end, PUT /trips/:id/cancel, GET /trips/:id. Validates JWT, extracts tenantId, delegates to TripApplicationService.")

        Component(tripAppService, "TripApplicationService", "Domain application service", "Orchestrates the full trip workflow: pre-flight HOS check, vehicle availability check, route optimisation, state machine advancement, outbox event emission. Wraps all writes in a PostgreSQL transaction.")

        Component(tripRepository, "TripRepository", "Repository pattern (pg)", "Encapsulates all SQL for the Trip aggregate. Implements optimistic concurrency via version column. Methods: findById, save, updateStatus, listByVehicle, listByDriver.")

        Component(hosService, "HOSService", "gRPC client → Driver Service", "Fetches remaining drive time and on-duty window for a driver before trip start. Enforces minimum rest hours. Returns HOSCheckResult with available hours and next reset timestamp.")

        Component(vehicleClient, "VehicleServiceClient", "REST client (axios) → Vehicle Service", "Checks vehicle state (must be available), confirms no open critical defects, retrieves vehicle type/dimensions for route constraints.")

        Component(driverClient, "DriverServiceClient", "REST client (axios) → Driver Service", "Retrieves driver qualifications, confirms CDL class matches vehicle type, fetches current duty status.")

        Component(routeOptimizer, "RouteOptimizer", "Google Maps / HERE Maps adapter", "Requests optimised route with waypoints. Returns polyline, ETA, distance. Falls back to HERE on primary failure. Caches result 15 minutes in Redis.")

        Component(outboxPublisher, "OutboxEventPublisher", "Outbox pattern (pg + cron)", "Writes domain events to outbox table in the same PostgreSQL transaction as the trip state change. Background relay process polls unpublished events and produces to Kafka, marks as published.")

        Component(tripQueryService, "TripQueryService", "Read model (pg)", "Serves read-heavy queries (active trips list, trip history, driver trip log) from a denormalised PostgreSQL read model updated via Kafka consumer. Bypasses write model for performance.")

        Component(tripSummaryBuilder, "TripSummaryBuilder", "Domain service", "On TripEnded: computes distance from GPS pings (TimescaleDB), fuel estimate, HOS consumed, on-time status. Attaches summary to TripCompleted outbox event.")
    }

    ContainerDb(postgres, "PostgreSQL (RDS)", "trips table, outbox table, trip_read_model")
    ContainerDb(redis, "Redis (ElastiCache)", "Route cache")
    ContainerDb(kafka, "Kafka (MSK)", "fleet.trips.events topic")
    ContainerDb(timescaledb, "TimescaleDB", "GPS pings for mileage calc")
    Container(driverService, "Driver Service", "gRPC + REST")
    Container(vehicleService, "Vehicle Service (Tracking)", "REST")
    System_Ext(googleMaps, "Google Maps API", "External")
    System_Ext(hereMaps, "HERE Maps API", "External")
    Container(apiGateway, "API Gateway (Kong)", "Routes trip API calls")

    Rel(apiGateway, tripAPIController, "REST calls", "HTTP/2")
    Rel(tripAPIController, tripAppService, "delegates command")
    Rel(tripAppService, tripRepository, "read/write trip aggregate")
    Rel(tripAppService, hosService, "checkHOS(driverId)")
    Rel(tripAppService, vehicleClient, "checkAvailability(vehicleId)")
    Rel(tripAppService, driverClient, "checkQualifications(driverId)")
    Rel(tripAppService, routeOptimizer, "optimiseRoute(origin, dest, waypoints)")
    Rel(tripAppService, outboxPublisher, "writeToOutbox(event) — same tx")
    Rel(tripAppService, tripSummaryBuilder, "buildSummary() on TripEnded")
    Rel(tripSummaryBuilder, timescaledb, "SELECT GPS pings for trip", "SQL")
    Rel(tripRepository, postgres, "SQL read/write", "TCP")
    Rel(outboxPublisher, postgres, "INSERT outbox + relay polling", "TCP")
    Rel(outboxPublisher, kafka, "PRODUCE events", "kafkajs")
    Rel(routeOptimizer, redis, "cache route result", "SET / GET")
    Rel(routeOptimizer, googleMaps, "GET /directions", "HTTPS")
    Rel(routeOptimizer, hereMaps, "GET /routing (fallback)", "HTTPS")
    Rel(hosService, driverService, "checkHOS RPC", "gRPC")
    Rel(vehicleClient, vehicleService, "GET /vehicles/:id/status", "HTTP/2")
    Rel(driverClient, driverService, "GET /drivers/:id/qualifications", "HTTP/2")
    Rel(tripAPIController, tripQueryService, "GET queries")
    Rel(tripQueryService, postgres, "SELECT from trip_read_model", "SQL")
```

---

## Component Interface Contracts

| Component | Interface | Method Signature | Contract |
|---|---|---|---|
| `PayloadValidator` | Synchronous validate | `validate(raw: unknown): Result<ValidatedPing, ValidationError>` | Returns `Ok(ValidatedPing)` if all fields pass; `Err(ValidationError)` with field-level error details if any field fails. Never throws. |
| `GeofenceEvaluator` | Synchronous evaluate | `evaluate(ping: EnrichedPing, fences: Geofence[]): GeofenceEvent[]` | Returns an array of `GeofenceEntered` or `GeofenceExited` events; empty array if no transition detected. Pure function; no side effects. |
| `RedisPositionUpdater` | Async write | `updatePosition(ping: EnrichedPing): Promise<void>` | Writes to Redis; silently logs and continues on Redis error (position cache is best-effort). Must complete within 50ms p99. |
| `TripRepository` | Async CRUD | `save(trip: Trip): Promise<Trip>` | Persists trip aggregate; throws `ConcurrencyError` if `version` mismatch detected. Caller must retry with fresh load. |
| `HOSService` | Async gRPC | `checkHOS(driverId: string): Promise<HOSCheckResult>` | Returns `{ availableDriveHours, availableOnDutyHours, nextResetAt }`. Throws `HOSInsufficientError` if less than 1 hour of drive time remains. |
| `RouteOptimizer` | Async optimise | `optimiseRoute(req: RouteRequest): Promise<OptimisedRoute>` | Returns route with `polyline`, `distanceMetres`, `durationSeconds`, `waypoints`. Throws `RoutingServiceUnavailableError` only if both Google Maps and HERE Maps fail after retries. |
| `OutboxEventPublisher` | Async write | `publish(event: DomainEvent, tx: DbTransaction): Promise<void>` | Writes event to `outbox` table within provided transaction. Does NOT produce to Kafka directly; relay process handles Kafka produce asynchronously. Idempotency guaranteed via `event.id` unique constraint. |
| `TripSummaryBuilder` | Async build | `buildSummary(tripId: string, startedAt: Date, endedAt: Date): Promise<TripSummary>` | Queries TimescaleDB for GPS pings in window; computes Haversine distance sum, max speed, average speed. Returns summary struct. Best-effort: returns partial summary if GPS data is missing. |
| `AlertPublisher` | Async publish | `publishAlert(event: AlertEvent): Promise<void>` | Produces to `fleet.alerts` with vehicle's `tenantId` as partition key for ordered delivery per tenant. At-least-once delivery guaranteed; consumers must be idempotent. |
| `PositionQueryHandler` | REST GET | `GET /vehicles/:id/position → PositionResponse` | Returns position from Redis within 10ms p95. Falls back to TimescaleDB (last known position) if Redis cache miss; indicates staleness via `cacheHit: false` flag. Returns 404 if vehicle unknown. |

---

## Design Patterns Used

### Repository Pattern

All database access in every service is encapsulated behind a typed Repository interface. Application services depend on the interface, not the concrete implementation. This enables unit testing with in-memory fakes and allows the underlying database or query strategy to change without touching business logic. Example: `TripRepository` hides all SQL including hypertable joins and the optimistic concurrency `WHERE version = $n` clause.

### CQRS — Command Query Responsibility Segregation

The Tracking Service and Trip Service separate their write path (commands: ingest ping, start trip, end trip) from their read path (queries: get live position, list active trips). Write handlers advance state and emit events; query handlers read from denormalised read models (Redis, PostgreSQL `trip_read_model` table, or TimescaleDB continuous aggregates). This segregation allows the live map endpoint to serve sub-10ms responses from Redis while the write path handles complex validation without impacting read performance.

### Outbox Pattern

The Trip Service must guarantee that when a trip state change is persisted to PostgreSQL, the corresponding Kafka event (e.g., `TripStarted`) is also published — even if the Kafka broker is temporarily unavailable. The Outbox Pattern achieves this by writing the event to an `outbox` table in the same PostgreSQL transaction as the state change. A lightweight relay process polls the `outbox` table for unpublished events and produces them to Kafka, marking them published on success. This eliminates the dual-write problem and ensures exactly-once state transitions with at-least-once event delivery.

### Circuit Breaker — External GPS Device / Mapping Calls

The `RouteOptimizer` and any outbound HTTP call to third-party APIs (Google Maps, HERE Maps, FMCSA) are wrapped in a circuit breaker using the `opossum` library. When the failure rate exceeds the configured threshold (5 failures per 30-second window), the circuit OPENS and subsequent calls return a cached fallback immediately without attempting the network call. This prevents a degraded mapping provider from cascading into trip creation failures and exhausting HTTP connection pool threads.

| Pattern | Applied In | Problem Solved |
|---|---|---|
| Repository | All services (TripRepository, DriverRepository, etc.) | Decouples business logic from SQL; enables unit testing with fakes |
| CQRS | Tracking Service, Trip Service | Separates high-throughput read path from write path; independent scaling |
| Outbox | Trip Service, Driver Service | Guarantees atomic state change + event publish; eliminates dual-write problem |
| Circuit Breaker | RouteOptimizer, ELDRegistrySync, all external HTTP clients | Prevents cascading failures from external API degradation |
| Consumer Group | All Kafka consumers | Allows multiple services to independently consume the same events |
| Dead Letter Queue | PayloadValidator, NotificationService | Isolates poison-pill messages; enables manual replay without blocking main pipeline |
