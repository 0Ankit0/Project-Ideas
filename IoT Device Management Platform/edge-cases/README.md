# Edge Cases — IoT Device Management Platform

## Introduction

IoT edge cases are categorically harder to reason about than those in typical web applications. The failure surface spans physical hardware, constrained firmware, unreliable radio networks, and cloud-side infrastructure — all of which can degrade independently or in concert. A single misconfigured retry policy can cascade into a message storm; a partial flash write can brick a device in the field with no remote recovery path; a spurious alert triggered by out-of-order telemetry can wake an on-call engineer at 3 AM or, worse, trigger a physical actuator in a production environment.

The platform manages devices that interact with the physical world. Unlike a failed API call that a user retries, a failed OTA firmware update can render industrial equipment inoperable, a duplicated command to a valve controller can cause dangerous double-actuation, and a missed certificate rotation can lock an entire device fleet out of the network with no self-service recovery. These consequences elevate IoT edge cases beyond software reliability into safety-engineering territory.

At scale, IoT systems exhibit emergent failure modes absent from smaller deployments. Ten thousand devices coming online simultaneously after a grid outage create a thundering-herd provisioning storm. A firmware bug introduced in a batch of 50,000 devices manifests not as a single support ticket but as a fleet-wide outage with physical-world consequences. The platform is designed to anticipate and contain these failure modes — this document index is the operational record of that design.

The edge cases documented across this directory were derived from first-principles failure analysis, chaos engineering exercises in the staging environment, and post-incident reviews. Every mitigation described is implemented; every recovery procedure has been tested.

---

## Edge Case Category Index

| Category | File | Cases | Risk Level | Primary Mitigation |
|---|---|---|---|---|
| Device Provisioning | [device-provisioning.md](./device-provisioning.md) | 4 | High | Idempotent provisioning, quota enforcement |
| Telemetry Ingestion | [telemetry-ingestion.md](./telemetry-ingestion.md) | 5 | High | Schema validation, quarantine queue, backpressure |
| Firmware Updates | [firmware-updates.md](./firmware-updates.md) | 5 | Critical | Canary rollout, rollback automation, dual-bank flash |
| Device Offline Recovery | [device-offline-recovery.md](./device-offline-recovery.md) | 4 | Medium | Command queuing, stale data detection, reconnect protocol |
| API and SDK | [api-and-sdk.md](./api-and-sdk.md) | 5 | Medium | Rate limiting, circuit breakers, retry logic |
| Security and Compliance | [security-and-compliance.md](./security-and-compliance.md) | 6 | Critical | Certificate rotation, audit logging, IEC 62443 |
| Operations | [operations.md](./operations.md) | 7 | High | Runbooks, automation, on-call escalation |

**Risk Level Definitions**

- **Critical** — Failure can result in data loss, device bricking, safety incidents, or regulatory violations. Requires immediate P0/P1 response. Mitigations are mandatory, not advisory.
- **High** — Failure degrades platform reliability for multiple tenants or causes significant data integrity risk. Requires P1/P2 response. Mitigations are enforced by design.
- **Medium** — Failure affects individual tenants or specific device cohorts. Degraded experience, no data loss. Requires P2/P3 response. Mitigations reduce probability.

---

## Risk Assessment Framework

### Probability × Impact Matrix

IoT failure risk is scored on two axes: **probability** (how likely the condition is to occur at operating scale) and **impact** (the blast radius if it does occur). The product of the two scores determines the risk tier and the required response posture.

| Probability \ Impact | Low (1) | Medium (2) | High (3) | Catastrophic (4) |
|---|---|---|---|---|
| Rare (1) | 1 — Monitor | 2 — Monitor | 3 — Mitigate | 4 — Prevent |
| Unlikely (2) | 2 — Monitor | 4 — Prevent | 6 — Prevent | 8 — Prevent |
| Possible (3) | 3 — Mitigate | 6 — Prevent | 9 — Prevent | 12 — Prevent |
| Likely (4) | 4 — Prevent | 8 — Prevent | 12 — Prevent | 16 — Prevent |

**IoT-Specific Risk Factors That Elevate Scores**

- **Physical-world actuation** — Any device that controls a physical process (valve, relay, motor) elevates impact score by +1.
- **Fleet size > 10,000** — Edge cases that are rare per-device become near-certain at fleet scale. Probability score elevated by +1 for fleet-level failure modes.
- **Remote-only access** — Devices with no physical access path (e.g., infrastructure sensors in remote locations) elevate impact score for any failure requiring on-site recovery by +2.
- **Safety-critical classification** — Medical, industrial safety, or infrastructure devices: impact floor is High (3) regardless of function.
- **Multi-tenant blast radius** — Failures in shared infrastructure (Kafka, EMQX, PostgreSQL) affecting multiple organizations elevate impact by +1.

### Risk Register (Summary)

| Edge Case | Probability | Impact | Risk Score | Tier |
|---|---|---|---|---|
| Mass provisioning storm | Likely (4) | Medium (2) | 8 | Prevent |
| OTA interrupted mid-flash | Possible (3) | Catastrophic (4) | 12 | Prevent |
| Firmware incompatibility at scale | Unlikely (2) | Catastrophic (4) | 8 | Prevent |
| Certificate rotation failure | Possible (3) | High (3) | 9 | Prevent |
| Telemetry queue overflow | Likely (4) | High (3) | 12 | Prevent |
| Duplicate command execution | Possible (3) | High (3) | 9 | Prevent |
| Out-of-order timestamp alert | Likely (4) | Medium (2) | 8 | Prevent |
| Rollback firmware deleted | Unlikely (2) | Catastrophic (4) | 8 | Prevent |

---

## General Mitigation Patterns

The following patterns are applied platform-wide and referenced throughout the individual edge case documents. Understanding these patterns is prerequisite to understanding any specific edge case mitigation.

### Idempotency Keys for Provisioning and Command Dispatch

Every state-mutating operation — device provisioning, OTA deployment creation, command dispatch — accepts a client-supplied `idempotency_key` header (UUID v4). The platform stores `(idempotency_key, operation_type, result)` in PostgreSQL with a 24-hour TTL. Duplicate requests with the same key return the cached result without re-executing the operation. This prevents double-provisioning and double-command-execution even when clients retry aggressively on network failure.

Manufacturing line software must generate the idempotency key from the device serial number and operation type (e.g., `SHA-256(serial_number + ":provision")`), ensuring idempotency across factory-line reboots.

### Exactly-Once Semantics via Kafka Transactions

The TelemetryService and CommandService use Kafka producer transactions. A single logical write — consume from input topic, transform, produce to output topic, commit InfluxDB write — is wrapped in a `beginTransaction() / commitTransaction()` block. If any step fails, the entire transaction is aborted and retried from the Kafka offset. Combined with InfluxDB's idempotent write semantics (duplicate points at the same timestamp overwrite), this achieves effectively-once delivery for telemetry data.

Consumer groups for different criticality levels are isolated: `telemetry-raw-critical-cg` (safety/alarm telemetry) runs on dedicated consumer instances with higher priority scheduling and smaller batch sizes for lower latency; `telemetry-raw-bulk-cg` (routine metrics) runs on shared instances with larger batches for throughput efficiency.

### Circuit Breakers (Hystrix Pattern)

Every service-to-service call and every external resource call (PostgreSQL, InfluxDB, Redis, S3, EMQX admin API) is wrapped in a circuit breaker. Parameters for each dependency:

| Dependency | Failure Threshold | Open Duration | Half-Open Probe Interval |
|---|---|---|---|
| PostgreSQL | 5 consecutive failures | 30s | 10s |
| InfluxDB | 10 failures in 60s window | 60s | 15s |
| Redis | 3 consecutive failures | 10s | 5s |
| S3/MinIO | 5 consecutive failures | 60s | 20s |
| EMQX Admin API | 3 consecutive failures | 30s | 10s |

When a circuit opens, the calling service falls back to a defined degraded behavior (described per-case) rather than propagating failures upstream.

### Exponential Backoff with Jitter

All retry logic uses the "full jitter" variant of exponential backoff:

```
sleep = random(0, min(cap, base × 2^attempt))
```

Where `base = 1s`, `cap = 60s`. This prevents synchronized retry storms from multiple concurrent clients or consumer threads. All device SDK retry logic uses the same formula to prevent thundering-herd reconnects after EMQX restarts.

### Bulkhead Pattern: Separate Consumer Groups by Criticality

The Kafka topic `telemetry-raw` is consumed by three separate consumer groups:
- `telemetry-alerts-cg` — feeds the rules engine for condition evaluation; 8 partitions, 8 consumers, SLA 500ms p99
- `telemetry-timeseries-cg` — feeds InfluxDB writers; 16 partitions, auto-scaled via KEDA, SLA 5s p99
- `telemetry-audit-cg` — feeds the immutable audit log in S3; 4 partitions, best-effort, no SLA

Isolation prevents alert processing from being starved by InfluxDB write slowdowns. Each consumer group has independent lag monitoring and alerting thresholds.

### Dead-Letter Queues with Human-Readable Rejection Reasons

Every Kafka consumer that processes messages has a corresponding dead-letter topic:

| Source Topic | Dead-Letter Topic | Retention |
|---|---|---|
| `telemetry-raw` | `telemetry-raw-dlq` | 7 days |
| `device-commands` | `device-commands-dlq` | 30 days |
| `provisioning-events` | `provisioning-events-dlq` | 30 days |
| `ota-events` | `ota-events-dlq` | 30 days |

Every DLQ message includes an `error_context` envelope:

```json
{
  "original_topic": "telemetry-raw",
  "original_partition": 7,
  "original_offset": 198234,
  "rejection_reason": "SCHEMA_VALIDATION_FAILED",
  "rejection_detail": "Field 'temperature' expected float64, got string 'hot'",
  "rejected_at": "2024-11-15T14:23:01.882Z",
  "device_id": "d-7f3a9b12",
  "organization_id": "org-acme-corp",
  "retry_count": 3
}
```

DLQ consumers surface rejection reasons in the DeviceService dashboard under `Devices > {id} > Diagnostics > Message Errors`.

### Health Check Endpoints

Every service exposes two HTTP endpoints on its management port (default: 8081):

- `GET /health` — Liveness probe. Returns `200 OK` if the process is running and not deadlocked. Returns `503` if the service is in a fatal state requiring restart. Does not check external dependencies.
- `GET /ready` — Readiness probe. Returns `200 OK` only when all required dependencies (database connections, Kafka connectivity, cache warm) are healthy. Returns `503` if the service should be removed from load balancer rotation. Kubernetes uses this to gate traffic during startup and rolling deploys.

Response body for `/ready`:

```json
{
  "status": "ready",
  "dependencies": {
    "postgres": "healthy",
    "kafka": "healthy",
    "redis": "healthy",
    "influxdb": "degraded"
  },
  "degraded_reason": "InfluxDB write latency p99 = 4800ms, threshold = 2000ms"
}
```

---

## Testing Approach for Edge Cases

### Chaos Engineering

The staging environment runs Chaos Monkey-equivalent fault injection on a 6-hour cycle during business hours. Fault types include:

- **Process kill** — Random service instance killed with SIGKILL (not SIGTERM, bypassing graceful shutdown). Validates Kubernetes restart policies and in-flight request handling.
- **Network partition** — `tc netem` rules injected to simulate 500ms latency, 20% packet loss, and complete partition between specific service pairs. Validates circuit breaker open/close cycles and Kafka producer retry behavior.
- **Disk full simulation** — InfluxDB data volume filled to 95% capacity. Validates write failure handling and circuit breaker response.
- **Clock skew** — System clock advanced or retarded by 60 seconds on individual pods. Validates timestamp handling in telemetry ingestion and JWT expiry logic.
- **Kafka broker failure** — One of three Kafka brokers stopped. Validates partition leadership election and consumer rebalancing without message loss.

Chaos experiments are recorded with before/after metrics dashboards (Grafana) and reviewed weekly. Any experiment that reveals a gap in mitigation triggers a P2 issue and runbook update.

### Fault Injection in Staging

Beyond infrastructure chaos, the platform supports application-level fault injection via environment variable flags:

- `FAULT_INJECT_CERT_DB_FAILURE=0.05` — CertificateService fails PostgreSQL writes with 5% probability. Used to verify saga rollback in provisioning.
- `FAULT_INJECT_INFLUX_SLOWDOWN=2000` — Adds 2000ms artificial delay to InfluxDB writes. Used to verify backpressure propagation and circuit breaker timing.
- `FAULT_INJECT_S3_404=firmwareId` — S3 GET requests for a specific firmware ID return 404. Used to verify rollback failure handling.
- `FAULT_INJECT_MQTT_DELAY=500` — Adds 500ms delay to MQTT PUBACK. Used to verify device-side backpressure and telemetry buffering behavior.

Fault injection flags are disabled in production via config-map and are only accessible from internal management network in staging.

---

## Incident Severity Levels

### P0 — Platform Down

Complete loss of platform functionality affecting all tenants or a critical safety incident.

**IoT examples:**
- EMQX cluster unreachable: all devices disconnected, no telemetry or command capability
- PostgreSQL primary failure with no automatic failover: all API operations fail
- Security breach: unauthorized command execution to device fleet
- OTA deployment bricking >100 devices simultaneously

**Response SLA:** Page on-call immediately, escalate to incident commander within 5 minutes, customer communication within 15 minutes.

### P1 — Significant Degradation

Partial loss of functionality affecting multiple tenants or a single tenant's entire fleet.

**IoT examples:**
- Kafka consumer lag > 10 minutes for `telemetry-alerts-cg` (alert rules not evaluating)
- OTA deployment stuck with >10% devices in FAILED state and no auto-rollback progress
- InfluxDB write failure rate > 10% (telemetry data loss)
- Mass provisioning queue depth > 50,000 (factory line halted)

**Response SLA:** Page on-call within 5 minutes, begin mitigation within 15 minutes, customer communication if impact > 30 minutes.

### P2 — Degraded Performance

Reduced performance or reliability for a subset of tenants or device cohorts.

**IoT examples:**
- Provisioning p99 latency > 5s (slower than SLA but functional)
- Telemetry consumer lag > 1 minute for `telemetry-timeseries-cg`
- OTA deployment stalled for a single tenant's fleet
- DLQ message volume > 1,000 in 1 hour (elevated error rate but no data loss for valid messages)

**Response SLA:** Notify on-call within 15 minutes, acknowledge within 30 minutes, resolve within 4 hours.

### P3 — Minor Issue

Cosmetic, low-impact, or single-device issues with workaround available.

**IoT examples:**
- Single device repeatedly failing checksum validation (device hardware issue)
- DLQ message from a single misbehaving device
- Orphaned certificate detected by reconciliation job (no active connection impact)
- API rate limit hit by a single poorly-configured client

**Response SLA:** Ticket created, resolved in next sprint or on-call shift.

---

## On-Call Runbook Index

| Edge Case | Runbook Reference | Severity Floor |
|---|---|---|
| Mass provisioning storm | OPS-RB-001: Provisioning Queue Overflow | P1 |
| Certificate rotation failure | OPS-RB-002: Orphaned Certificate Remediation | P2 |
| Device claims conflict | OPS-RB-003: Serial Number Conflict Resolution | P3 |
| Telemetry queue overflow | OPS-RB-004: Kafka Consumer Lag Recovery | P1 |
| Out-of-order telemetry alert storm | OPS-RB-005: Spurious Alert Suppression | P2 |
| InfluxDB write failure | OPS-RB-006: Time-Series Write Recovery | P1 |
| OTA interrupted mid-flash | OPS-RB-007: Bricked Device Recovery | P1 |
| OTA rollback firmware missing | OPS-RB-008: Emergency Firmware Re-upload | P0 |
| Simultaneous fleet OTA storm | OPS-RB-009: OTA Deployment Throttling | P1 |
| Firmware incompatibility at scale | OPS-RB-010: Emergency OTA Suspension | P0 |
| Device offline command backlog | OPS-RB-011: Stale Command Purge | P3 |
| Reconnect storm | OPS-RB-012: EMQX Connection Rate Limiting | P1 |
| Certificate expiry storm | OPS-RB-013: Bulk Certificate Renewal | P1 |
| Kafka broker failure | OPS-RB-014: Kafka Broker Recovery | P0 |

---

## Cross-Cutting Failure Cascades

Certain edge cases do not occur in isolation — they trigger cascades across multiple subsystems. Understanding these cascade paths is essential for accurate impact assessment during incidents.

### Cascade: Mass Provisioning Storm → Telemetry Overload → Command Queue Backlog

When a large device fleet (10,000+) provisions simultaneously, it typically also begins publishing telemetry within seconds of connecting. The EMQX connection storm is followed immediately by a message storm to `telemetry-raw`. If the Kafka consumer group for telemetry-timeseries cannot keep pace, consumer lag grows. Simultaneously, devices that have been offline send buffered commands and receive queued command dispatches, adding to the MQTT message volume. The combined effect is elevated end-to-end latency for all three subsystems simultaneously.

**Detection signal:** Simultaneous spike in all three metrics — EMQX connection rate, Kafka `telemetry-raw` consumer lag, and MQTT publish rate for `device-commands`.

**Response:** OPS-RB-001 covers provisioning throttling; OPS-RB-004 covers consumer lag. Both runbooks must be executed concurrently, with the provisioning rate limit applied first to cap the source of new load.

### Cascade: Bad Firmware Deployment → Crash Loop → EMQX Reconnect Storm

A firmware update that causes crash loops generates MQTT connect/disconnect events at high frequency (device reboots every 30–120 seconds, each cycle generating a connect + LWT disconnect). For a fleet of 1,000 devices in crash loops, this generates 1,000 MQTT connection events per minute — enough to stress EMQX connection handling and pollute the audit log with noise, making it difficult to identify the root-cause firmware issue.

**Detection signal:** MQTT `client.connect` events correlated to the OTA deployment ID exceed 10× normal rate within 1 hour of deployment activation.

**Response:** OPS-RB-009 (suspend deployment) must be executed before OPS-RB-010 (firmware incompatibility), because the reconnect storm must be stopped before the fleet state can be assessed accurately.

### Cascade: InfluxDB Failure → Rules Engine Staleness → False Alert Suppression

When InfluxDB write latency exceeds the rules engine evaluation window, the rules engine begins querying stale or incomplete data. This has two dangerous failure modes: (1) real threshold violations that occurred during the outage window are not evaluated, suppressing real alerts; (2) when InfluxDB recovers and the delayed batch writes land, the rules engine may evaluate historical data as current and fire delayed alerts — confusing on-call engineers who see alerts for conditions that have already resolved.

**Detection signal:** Rules engine `last_evaluated_at` timestamp diverging from wall clock by > 2× evaluation interval.

**Response:** OPS-RB-006 must note the outage window. Alert rules with `require_recent_data: true` (configurable per rule) automatically suppress evaluation if the most recent data point for the device is older than `max_data_age_seconds`. Operators should review alert history after InfluxDB recovery to identify suppressed alerts that may represent real events.

### Cascade: Certificate Expiry Storm → Mass Provisioning → Duplicate Device Records

If certificate rotation automation fails for a large cohort of devices, certificates may reach their expiry date simultaneously. Devices whose certificates expire disconnect from EMQX and, depending on firmware implementation, attempt full re-provisioning (treating expiry as a factory-reset condition). This triggers a provisioning storm with the additional complexity that device records already exist in PostgreSQL — creating the risk of duplicate or conflicting device records if the idempotency layer is not functioning correctly.

**Detection signal:** `cert_expiry_within_24h` metric spikes above normal (expected: gradual, rolling expiry pattern).

**Response:** OPS-RB-013 (bulk certificate renewal) must be triggered proactively when `cert_expiry_within_24h > 500 devices`. Waiting until certificates actually expire converts a scheduled maintenance window into a P0 incident.
