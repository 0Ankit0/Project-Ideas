## Fleet Management System — Edge Cases Overview

This directory documents edge cases, failure modes, and recovery strategies for the Fleet Management System. Each file targets a specific domain within the platform and provides structured analysis covering failure detection, impact assessment, and mitigation patterns. These cases are drawn from real-world operational scenarios involving GPS telemetry, HOS compliance, route optimization, and fleet operations at scale on the Node.js/TypeScript + PostgreSQL/TimescaleDB + Kafka + Kubernetes stack.

## Table of Contents

| File | Domain | Cases |
|------|--------|-------|
| [vehicle-tracking.md](./vehicle-tracking.md) | GPS telemetry ingestion, geofence events, Redis position cache, signal loss, spoofing, ping floods | EC-01 – EC-06 |
| [maintenance-scheduling.md](./maintenance-scheduling.md) | DVIR workflows, service intervals, odometer anomalies, offline technician app, overlapping schedules | EC-01 – EC-06 |
| [driver-management.md](./driver-management.md) | HOS/FMCSA violations, CDL expiry, vehicle type authorization, multi-driver conflicts, termination handoff | EC-01 – EC-06 |
| [route-optimization.md](./route-optimization.md) | Google Maps/HERE API failures, weight restrictions, mid-trip reroutes, HOS-constrained routing, toll mismatch | EC-01 – EC-06 |
| [api-and-ui.md](./api-and-ui.md) | Stale map positions, duplicate trip creation, report timeouts, offline HOS sync, WebSocket reconnection | EC-01 – EC-06 |
| [security-and-compliance.md](./security-and-compliance.md) | JWT theft, FMCSA audits, data breaches, GPS privacy, RLS misconfiguration, insider threat exports | EC-01 – EC-06 |
| [operations.md](./operations.md) | TimescaleDB disk exhaustion, Kafka lag spikes, MQTT overload, batch job failures, connection pool saturation | EC-01 – EC-06 |

## Risk Classification

| Risk Level | Criteria | Response SLA | Example |
|------------|----------|-------------|---------|
| **Critical** | Safety risk, regulatory violation, data breach, complete service outage | Immediate — < 15 minutes | DVIR safety defect ignored; HOS violation allowing fatigued driver; personal data breach |
| **High** | Significant data loss, major feature unavailable, compliance reporting failure | < 1 hour | GPS tracking down for entire fleet; nightly HOS batch job failure; Kafka consumer lag > 100k messages |
| **Medium** | Degraded performance, partial feature outage, data inconsistency affecting operations | < 4 hours | Route optimization API unavailable; Redis cache eviction for position data; report page timeout |
| **Low** | Minor UX issue, non-critical data gap, cosmetic inconsistency | < 24 hours | Out-of-order GPS ping; toll cost mismatch; offline DVIR sync delay |

## Common Failure Patterns

### GPS Signal Loss and Stale Position Data

GPS signal interruptions are the most frequent failure class in the platform. Tunnels, underground parking structures, dense urban canyons, and GPS jamming all produce gaps in the telemetry stream. The system must distinguish intentional device shutdown from signal loss, surface a `gps_signal_lost` status to dispatchers within a configurable timeout (default 5 minutes), and resume normal tracking on the next valid ping without requiring manual intervention. Stale position data in the Redis live-position cache compounds this: TTL misconfiguration or Redis eviction under memory pressure can present outdated coordinates on the dispatcher map long after signal has been restored.

### HOS Calculation Drift

Hours-of-Service calculations accumulate floating-point drift and timezone edge cases over long duty periods. The FMCSA 11-hour driving / 14-hour on-duty / 70-hour/8-day rules each require precise boundary calculations. Common failure modes include: clock skew between the driver mobile app and the server causing log entries to be rejected as future-dated; offline HOS records syncing out of order and producing incorrect cumulative totals; and exemption flags (short-haul, adverse driving conditions) being applied inconsistently when multiple drivers share a vehicle. The HOS engine must be idempotent and replay-safe so that re-processing historical logs always produces the same result.

### Maintenance Record Gaps

Service interval triggers depend on accurate, continuous odometer data from GPS pings. When a GPS device malfunctions, is replaced, or a vehicle crosses a cellular dead zone for an extended period, odometer values may jump or reset, causing the interval calculator to either miss a due service or fire false alarms. DVIR defect records present a related gap: technicians working offline may not sync their completed inspections until hours after the vehicle has departed the yard, leaving a window during which the vehicle appears to have no valid DVIR on file.

### Route Recalculation Failures

The route optimization engine calls external APIs (Google Maps Platform, HERE Routing API) that are subject to quota exhaustion, regional outages, and latency spikes during peak hours. When recalculation fails mid-trip due to a traffic incident, the driver receives no updated guidance and may follow a route that is now significantly longer or impassable. A cascading failure occurs when the fallback to the cached route is itself stale (cached before a road closure), leaving the driver with no valid path. The system must detect API failures within the request timeout, fall back gracefully, and surface the degraded state to the dispatcher.

## Testing and Validation

### Chaos Engineering with Chaos Monkey

The platform uses [Chaos Monkey for Kubernetes (kube-monkey)](https://github.com/asobti/kube-monkey) to randomly terminate pods in the `fleet-prod` namespace during business hours. Each edge case in this directory has a corresponding chaos experiment label (`chaos/target: true`) on the relevant Deployment. Chaos experiments are run every Tuesday and Thursday between 10:00–14:00 UTC to validate that circuit breakers, retries, and fallback paths behave as documented. Results are published to the `#fleet-chaos` Slack channel and reviewed in the weekly SRE sync.

### Load Testing with k6

GPS ingestion throughput, route optimization concurrency, and API gateway capacity are load-tested with [k6](https://k6.io/) scripts located in `tests/load/`. The baseline scenario simulates 500 vehicles pinging every 30 seconds (≈ 1,000 req/s to the telemetry ingest endpoint). The stress scenario scales to 5,000 vehicles at 10-second intervals to validate TimescaleDB hypertable performance and Kafka producer throughput. Load tests run in CI on every release candidate branch and must maintain p99 latency < 500 ms before a release is approved.

### HOS Simulation Suite

A dedicated HOS simulation suite in `tests/hos-simulation/` replays 90-day HOS log sequences for 200 synthetic drivers covering all FMCSA exemption categories. The suite validates that cumulative hour totals, restart provisions, and sleeper-berth splits are calculated identically by the server-side engine and the mobile app offline engine. Any divergence greater than 1 minute in a duty period triggers a test failure. The simulation runs nightly in CI and its output is archived for 6 months to support FMCSA audit readiness.

### Integration Testing with Testcontainers

Service-level integration tests use [Testcontainers](https://testcontainers.com/) to spin up PostgreSQL + TimescaleDB, Redis, and a single-node Kafka cluster for each test run. This ensures that TimescaleDB hypertable partitioning, PostgreSQL Row-Level Security policies, and Kafka topic configurations are exercised against real infrastructure rather than mocks. Tests covering EC cases tagged `@integration` must pass before any PR is merged to `main`.
