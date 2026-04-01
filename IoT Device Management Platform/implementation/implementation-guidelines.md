# Implementation Guidelines — IoT Device Management Platform

## Overview

This document defines the phased implementation plan for the IoT Device Management Platform — a production-grade, multi-tenant system built on microservices. The plan spans 32 weeks across four phases, each delivering a shippable increment that can be validated against defined acceptance criteria before the next phase begins.

The platform is designed to operate at scale: 500K concurrent MQTT connections, 1M telemetry data points per minute ingested, and hundreds of organizations with isolated data planes. Each sprint is time-boxed to two weeks. Teams are expected to maintain test coverage above the stated thresholds before any sprint is considered complete.

---

## Technology Stack Summary

| Service | Language / Framework | Primary Database | Messaging | Key Libraries |
|---|---|---|---|---|
| DeviceService | Python 3.12 / FastAPI | PostgreSQL 15 (RDS) | Kafka, Redis | SQLAlchemy Core, asyncpg, aiokafka, aioredis |
| TelemetryService | Python 3.12 / Consumer | InfluxDB 2.x | Kafka | aiokafka, influxdb-client-python, jsonschema |
| OTAService | Python 3.12 / FastAPI | PostgreSQL 15 (RDS) | Kafka, MQTT | boto3 / minio, aiokafka, asyncpg |
| CommandService | Python 3.12 / FastAPI | PostgreSQL 15 (RDS) | Kafka, MQTT | aiokafka, asyncpg, aioredis |
| CertificateService | Python 3.12 / FastAPI | PostgreSQL 15 (RDS) | — | cryptography 42.x, asyncpg |
| AuthService | Python 3.12 / FastAPI | PostgreSQL 15 (RDS) | — | python-jose, passlib, asyncpg |
| RulesEngine | Python 3.12 / Consumer | Redis, InfluxDB 2.x | Kafka | aiokafka, aioredis, influxdb-client-python |
| NotificationService | Python 3.12 / Consumer | PostgreSQL 15 (RDS) | Kafka | sendgrid, twilio, httpx, aiokafka |

**Infrastructure:**  Kubernetes (EKS/GKE), EMQX MQTT broker cluster, Apache Kafka (MSK), InfluxDB OSS/Cloud, PostgreSQL on RDS, Redis on ElastiCache, MinIO/S3, Kong API Gateway, Prometheus + Grafana.

---

## Phase Implementation Milestones

| Phase | Weeks | Goal | Exit Criterion |
|---|---|---|---|
| Phase 1 | 1–8 | Device Registry and Connectivity | Devices provision, connect via mTLS, shadow syncs, RBAC enforced |
| Phase 2 | 9–16 | Telemetry and Alerting | End-to-end telemetry pipeline live, alerts fire, notifications delivered |
| Phase 3 | 17–24 | OTA Updates and Remote Commands | Firmware deployed to fleet with canary/rollback, commands executed |
| Phase 4 | 25–32 | Analytics, SDK, and Hardening | SDK published, 100K load test passes, security scan clean |

---

## Phase 1 — Device Registry and Connectivity (Weeks 1–8)

**Goals:** Establish the foundational device lifecycle — CRUD, X.509 certificate provisioning, MQTT broker connectivity with mutual TLS, and a functional device shadow for desired/reported state management.

### Sprint 1–2 — Infrastructure Setup

Provision all base infrastructure before any application code is written. All infrastructure is managed via Helm charts in the `infra/` directory.

**Kubernetes Cluster**
- 3-node cluster (m6i.xlarge for production, t3.medium for staging); namespace: `iot-platform`
- Enable Kubernetes Network Policies to isolate namespaces
- Install cert-manager for internal TLS certificate management
- Install KEDA (Kubernetes Event-driven Autoscaling) for consumer pod scaling
- Configure HPA for all stateless services (min 2 replicas, max 20)

**PostgreSQL**
- RDS PostgreSQL 15, Multi-AZ, `db.r6g.large`, 100 GB gp3 encrypted
- Alembic migration framework initialized; `alembic.ini` committed to repo
- Initial migration: create `organizations`, `device_models`, `device_groups`, `devices` tables

Schema for core tables:
```sql
CREATE TABLE organizations (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,
    slug        TEXT UNIQUE NOT NULL,
    max_devices INT NOT NULL DEFAULT 1000,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE devices (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id              UUID NOT NULL REFERENCES organizations(id),
    serial_number       TEXT NOT NULL,
    name                TEXT NOT NULL,
    device_model_id     UUID NOT NULL REFERENCES device_models(id),
    group_id            UUID REFERENCES device_groups(id),
    status              TEXT NOT NULL DEFAULT 'PENDING_PROVISIONING',
    provisioning_method TEXT NOT NULL,
    last_seen_at        TIMESTAMPTZ,
    metadata            JSONB NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (org_id, serial_number)
);
CREATE INDEX idx_devices_org_id ON devices (org_id);
CREATE INDEX idx_devices_status ON devices (org_id, status);
CREATE INDEX idx_devices_group_id ON devices (group_id);
```

**Redis**
- 3-node Redis 7 cluster in sentinel mode (ElastiCache `cache.r7g.large`)
- Keyspace: `shadow:{device_id}`, `session:{token_id}`, `ratelimit:{org_id}`, `alert_cooldown:{rule_id}:{device_id}`
- `maxmemory-policy: allkeys-lru`

**EMQX**
- 2-node EMQX 5 cluster deployed via the EMQX Kubernetes Operator
- Enable mTLS on port 8883; disable plaintext MQTT port 1883 in production
- Configure EMQX Dashboard with Prometheus metrics endpoint
- Hook endpoint configured for authentication callbacks to CertificateService

**Kong API Gateway**
- Deploy Kong via Helm (`kong/kong` chart)
- JWT plugin enabled globally; rate limiting plugin enabled per-route
- Configure routes for all upstream microservices
- Enable Prometheus metrics plugin

**Kafka**
- 3-broker MSK cluster, Kafka 3.5, `kafka.m5.xlarge`
- Topics created at bootstrap (via `kafka-topics.sh` or Terraform):
  - `telemetry-raw` (6 partitions, replication factor 3)
  - `telemetry-enriched` (6 partitions, replication factor 3)
  - `telemetry-quarantine` (3 partitions, replication factor 3)
  - `commands` (6 partitions, replication factor 3)
  - `ota-jobs` (6 partitions, replication factor 3)
  - `ota-progress` (6 partitions, replication factor 3)
  - `alert-events` (6 partitions, replication factor 3)
  - `audit-events` (3 partitions, replication factor 3)
  - `device-events` (6 partitions, replication factor 3)
  - `dead-letter` (3 partitions, replication factor 3)
- Enable topic-level retention: `telemetry-raw` 48h, all others 7 days

---

### Sprint 3–4 — Device Service Core

Implement the full device lifecycle API including CRUD, organization management, fleet grouping, RBAC middleware, and device shadow.

**Device CRUD API**

Routes served under `/v1/devices`. All endpoints require a valid JWT with the appropriate RBAC role claim.

| Method | Path | Required Role |
|---|---|---|
| POST | /v1/devices | fleet_manager, platform_admin |
| GET | /v1/devices | fleet_manager, device_operator, viewer |
| GET | /v1/devices/{id} | fleet_manager, device_operator, viewer |
| PATCH | /v1/devices/{id} | fleet_manager, platform_admin |
| DELETE | /v1/devices/{id} | platform_admin |

**RBAC Middleware**

Roles are stored as a claim `roles: ["fleet_manager"]` in the JWT payload. The middleware extracts the `org_id` from the JWT `sub` claim and enforces that all resource access is scoped to that organization. Cross-tenant access is rejected with HTTP 403 regardless of role.

Four roles are defined:
- `platform_admin` — full access across all resources for the organization
- `fleet_manager` — manage devices, groups, OTA deployments, alert rules
- `device_operator` — read devices, issue commands, acknowledge alerts
- `viewer` — read-only access to all resources

**Device Shadow Implementation**

The shadow document is stored in Redis as a JSON object with the following schema:

```json
{
  "device_id": "uuid",
  "desired": {},
  "reported": {},
  "delta": {},
  "version": 42,
  "desired_version": 42,
  "reported_version": 41,
  "last_updated_at": "ISO8601"
}
```

`GET /v1/devices/{id}/shadow` returns the full shadow document including the computed delta (keys present in `desired` but absent or differing in `reported`). `PATCH /v1/devices/{id}/shadow/desired` merges the provided object into `desired` and increments `desired_version`. Delta is recomputed on every write and stored alongside.

Unit test coverage target: **85%** before sprint review.

---

### Sprint 5–6 — Certificate Service and Provisioning

**Internal CA Setup**

Use the Python `cryptography` library (v42+) to implement a two-tier CA hierarchy:
- Root CA: RSA 4096-bit, 10-year validity, stored encrypted on disk (KMS-encrypted private key in production)
- Intermediate CA: RSA 4096-bit or EC P-384, 3-year validity, signed by Root CA, used for all device certificate issuance
- Intermediate CA certificate and CRL URL embedded in issued device certificates

**X.509 Certificate Issuance**

`POST /v1/devices/{id}/certificates` accepts a Certificate Signing Request (CSR) or generates a key pair server-side based on the `provisioning_method` field:
- `X509_CSR`: device submits CSR; service validates CSR signature, issues cert
- `X509_SERVER_GENERATED`: service generates RSA-2048 or EC P-256 key pair, issues cert, returns private key once (stored nowhere after response)

Issued certificate Subject:
```
CN=<device_id>, OU=devices, O=<org_slug>, C=US
```
Certificate validity: 365 days. SHA-256 thumbprint stored in `device_certificates` table.

**CRL Generation**

The CRL is regenerated on every certificate revocation and also on a 24-hour schedule. The CRL is served at a well-known HTTP endpoint (`/v1/pki/crl.pem`) and the URL is embedded as the `cRLDistributionPoints` extension in all issued certificates.

**EMQX mTLS Configuration**

EMQX authenticates connecting devices using their client certificate. The EMQX authentication hook calls `CertificateService` with the certificate thumbprint. The service looks up the certificate in the database and verifies: (a) not expired, (b) not revoked, (c) `device_id` in certificate CN matches the MQTT client ID.

**Provisioning Flow Integration Test**

```
device → POST /v1/devices (register) 
       → POST /v1/devices/{id}/certificates (issue cert) 
       → MQTT connect on port 8883 with client cert 
       → EMQX auth hook → CertificateService validates 
       → MQTT CONNACK accepted
```

---

### Sprint 7–8 — MQTT Integration and Device Shadow Sync

**EMQX Kafka Bridge**

Configure the EMQX Kafka bridge plugin to forward:
- `devices/+/telemetry` → Kafka topic `telemetry-raw` (key: `device_id` extracted from topic)
- `devices/+/telemetry/batch` → Kafka topic `telemetry-raw` (exploded by worker)
- `devices/+/events` → Kafka topic `device-events`
- `devices/+/shadow/update/reported` → Kafka topic `telemetry-enriched` (shadow update path)

**MQTT ACL Rules**

Each device is restricted to its own topic subtree. EMQX ACL rules (loaded from the auth hook response):
```
allow publish  devices/{device_id}/telemetry
allow publish  devices/{device_id}/telemetry/batch
allow publish  devices/{device_id}/shadow/update/reported
allow publish  devices/{device_id}/commands/ack
allow publish  devices/{device_id}/ota/progress
allow publish  devices/{device_id}/events
allow subscribe devices/{device_id}/commands/+
allow subscribe devices/{device_id}/shadow/update/desired
allow subscribe devices/{device_id}/ota/job
allow subscribe devices/{device_id}/config
deny  all
```

**LWT (Last Will and Testament)**

Devices connect with an LWT message on `devices/{device_id}/events` with payload `{"type": "offline", "device_id": "..."}`. EMQX delivers this on abnormal disconnect. The DeviceService consumes `device-events` from Kafka and updates `last_seen_at` and `status` accordingly.

**Shadow Desired → Device Sync**

When a server-side `PATCH /v1/devices/{id}/shadow/desired` is called, the DeviceService publishes the new desired state to `devices/{device_id}/shadow/update/desired` via the EMQX MQTT publish API (HTTP). The device applies the delta and publishes its new reported state to `devices/{device_id}/shadow/update/reported`.

---

## Phase 2 — Telemetry and Alerting (Weeks 9–16)

**Goals:** Full end-to-end telemetry ingestion pipeline with schema validation, enrichment, InfluxDB storage with downsampling, rules-based alerting, and multi-channel notifications.

### Sprint 9–10 — Telemetry Pipeline

**Kafka Consumer Group**

Consumer group `telemetry-ingestion` subscribes to `telemetry-raw` with 6 consumer pods (one per partition). Consumers use manual offset commit — `enable.auto.commit=false`. Offset is committed only after the InfluxDB write succeeds or the record is routed to the quarantine queue.

**Schema Validation**

Each device model has an associated `TelemetrySchema` (JSON Schema Draft-07) stored in PostgreSQL and cached in Redis (TTL 60s). On each message, the consumer:
1. Resolves the device's `device_model_id` (from Redis cache, fallback to PostgreSQL)
2. Fetches the schema for that model
3. Validates the payload against the schema
4. Routes invalid payloads to `telemetry-quarantine` with rejection reason

**Clock Skew Validation**

Reject telemetry with a timestamp more than 24 hours in the past or more than 5 minutes in the future. Store original device timestamp in InfluxDB as a field (`device_ts`); use server-received time as the InfluxDB point timestamp.

**Unit Normalization**

Applied before writing to InfluxDB:
- Temperature: `°C → K` (K = °C + 273.15), `°F → K` (K = (°F − 32) × 5/9 + 273.15)
- Pressure: `hPa → Pa` (multiply by 100), `bar → Pa` (multiply by 100000), `psi → Pa` (multiply by 6894.76)
- Humidity: stored as fraction (0–1), converted from percentage if value > 1

**InfluxDB Measurement Schema**

```
measurement: device_telemetry
tags:
  org_id:     <uuid>
  device_id:  <uuid>
  model_id:   <uuid>
  fleet_id:   <uuid | "none">
fields:
  <metric_name>: float64
  device_ts:     int64 (unix nano)
  schema_version: integer
timestamp: server ingestion time (unix nano)
```

Batch writer: 500 points per batch, 100 ms flush interval, using `influxdb-client-python` async write API.

**Retention Policies**

| Bucket | Retention | Downsampling |
|---|---|---|
| `telemetry_raw` | 30 days | none |
| `telemetry_1h` | 365 days | 1-hour mean/min/max/last |
| `telemetry_1d` | 5 years | 1-day mean/min/max/last |

**Telemetry Query API**

`GET /v1/devices/{id}/telemetry` parameters:
- `metric` — metric name (required)
- `from` / `to` — ISO 8601 timestamps
- `aggregation` — `mean`, `min`, `max`, `sum`, `count`, `last` (default: `mean`)
- `window` — Flux duration string: `5m`, `1h`, `1d` (default: `1h`)
- `limit` — max 10,000 points

---

### Sprint 11–12 — Schema Registry and Enrichment

**TelemetrySchema CRUD API**

Schemas are versioned: `POST /v1/device-models/{id}/telemetry-schemas` creates a new version. Backward compatibility validation checks that all fields present in the previous version exist in the new version (no field removal). Breaking changes require a new `device_model_id`.

**Device Metadata Enrichment**

Before writing to InfluxDB, the consumer enriches each message with `org_id`, `model_id`, and `fleet_id`. These are fetched from Redis using key `device:meta:{device_id}` (TTL 60s). On cache miss, the worker queries PostgreSQL and repopulates the cache.

**Quarantine Queue**

Invalid telemetry is written to `telemetry-quarantine` with fields:
- `rejection_reason`: one of `SCHEMA_VALIDATION_FAILED`, `CLOCK_SKEW_EXCEEDED`, `UNKNOWN_DEVICE`, `UNIT_NORMALIZATION_ERROR`
- `raw_payload`: base64-encoded original bytes
- `device_id`, `received_at`

**Consumer Lag Monitoring**

Prometheus metric `kafka_consumer_group_lag{group, topic, partition}` is exposed by a dedicated lag exporter sidecar. Alert fires when lag exceeds 50,000 for more than 5 minutes.

---

### Sprint 13–14 — Rules Engine

**Alert Rule Model**

```python
class AlertRule(BaseModel):
    id: UUID
    org_id: UUID
    name: str
    condition_type: Literal["THRESHOLD", "RATE_OF_CHANGE", "ANOMALY"]
    metric: str
    device_scope: Literal["ALL", "GROUP", "DEVICE"]
    scope_id: Optional[UUID]  # group_id or device_id
    operator: Literal["GT", "GTE", "LT", "LTE", "EQ", "NEQ"]
    threshold: Optional[float]
    window_seconds: Optional[int]
    cooldown_seconds: int = 300
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
    enabled: bool = True
```

**Condition Evaluation**

The rules engine consumer reads from `telemetry-enriched`. For each message, it loads all enabled `AlertRule` records for the device's org that match the device's scope. Evaluation:
- `THRESHOLD`: compare `metric_value` against `threshold` using `operator`
- `RATE_OF_CHANGE`: query InfluxDB for the same metric over `window_seconds`; compute rate = (current − oldest) / window_seconds
- `ANOMALY`: query InfluxDB for mean ± 3σ over the past 24h; fire if current value exceeds bounds

**Cooldown Enforcement**

```python
cooldown_key = f"alert_cooldown:{rule_id}:{device_id}"
acquired = await redis.set(cooldown_key, "1", nx=True, ex=rule.cooldown_seconds)
if not acquired:
    return  # still in cooldown, skip
```

**Alert Event Publication**

On rule match (and outside cooldown), an `AlertEvent` is published to `alert-events` Kafka topic:
```json
{
  "alert_id": "uuid",
  "rule_id": "uuid",
  "device_id": "uuid",
  "org_id": "uuid",
  "metric": "temperature",
  "metric_value": 95.3,
  "threshold": 90.0,
  "severity": "HIGH",
  "triggered_at": "ISO8601"
}
```

---

### Sprint 15–16 — Notification Service

**Notification Channels**

| Channel | Provider | Template Engine |
|---|---|---|
| Email | SendGrid | Jinja2 HTML templates |
| SMS | Twilio | Plain text, <160 chars |
| Webhook | HTTP POST | JSON payload, HMAC-SHA256 signed |

**Webhook Delivery**

Signature header: `X-IoT-Signature: sha256=<hex>`. HMAC computed over the raw JSON body using the organization's webhook secret. Retry policy: 3 attempts with backoff at 1 min, 5 min, 15 min. After final failure, the alert event is written to `dead-letter`.

**Escalation Engine**

Escalation policies are stored in PostgreSQL. A background job (`alert-escalation-scheduler`) runs every 30 seconds and promotes unacknowledged alerts from `TRIGGERED` → `ESCALATED` → `CRITICAL_ESCALATED` based on configurable timeout thresholds per severity.

**End-to-End Integration Test**

Verified test scenario: device publishes a temperature value of 95°C → `telemetry-raw` → enriched → `RulesEngine` evaluates threshold rule (threshold 90°C, GT operator) → alert created → `alert-events` → `NotificationService` → SendGrid sandbox API receives email request → test asserts HTTP 202 from SendGrid.

---

## Phase 3 — OTA Updates and Remote Commands (Weeks 17–24)

**Goals:** Production-grade firmware update pipeline with canary/wave deployments and auto-rollback; async command execution with offline queuing; automated certificate lifecycle management.

### Sprint 17–18 — Firmware Management

**Firmware Upload API**

`POST /v1/firmware` accepts `multipart/form-data` with:
- `file`: binary firmware blob (max 512 MB enforced by Kong `client_max_body_size`)
- `version`: SemVer string (e.g., `1.4.2`)
- `device_model_id`: target model
- `release_notes`: Markdown string

Upload process:
1. Stream file to S3/MinIO bucket `iot-firmware` under key `{org_id}/{model_id}/{version}/{sha256}.bin`
2. Compute SHA-256 checksum during streaming (no buffering entire file in memory)
3. Verify firmware RSA-PSS signature (2048-bit) against the organization's signing public key
4. Store metadata in `firmware` PostgreSQL table
5. Return presigned download URL valid for 1 hour (extended per-deployment as needed)

**Firmware Signature Verification**

```python
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

def verify_firmware_signature(
    public_key: RSAPublicKey,
    firmware_bytes: bytes,
    signature: bytes,
) -> None:
    public_key.verify(
        signature,
        firmware_bytes,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )
```

---

### Sprint 19–20 — OTA Deployment Orchestration

**Deployment Strategies**

- `CANARY`: deploy to `canary_percentage`% (default 5%) of the target fleet first. After `canary_bake_time_minutes` with success rate ≥ threshold, promote to full fleet. On failure, auto-rollback the canary devices.
- `WAVE`: divide fleet into N waves; deploy one wave at a time with `wave_interval_minutes` between waves.
- `ROLLING`: rolling update across all devices, max concurrency configurable.

**Progress Tracking**

Devices publish OTA progress to `devices/{device_id}/ota/progress` with payloads:
```json
{"job_id": "uuid", "status": "DOWNLOADING|VERIFYING|INSTALLING|REBOOTING|SUCCESS|FAILED", "progress_pct": 75}
```
EMQX bridges these to `ota-progress` Kafka topic. The OTAService consumer updates `ota_device_jobs` table and recalculates deployment health.

**Auto-Rollback**

If the failure rate among deployed devices exceeds `failure_threshold_pct` (default 10%), the orchestrator:
1. Sets deployment status to `ROLLING_BACK`
2. Publishes rollback OTA job for each failed device (pointing to previous firmware version)
3. Updates deployment status to `ROLLED_BACK` when all rollback jobs complete

---

### Sprint 21–22 — Command Execution Service

**Command Lifecycle**

States: `PENDING` → `DISPATCHED` → `ACKNOWLEDGED` → `EXECUTING` → `SUCCEEDED` / `FAILED` / `TIMEOUT`

Offline queuing: commands with `offline_policy: QUEUE` are stored in PostgreSQL with `status=PENDING`. When a device-connect event is received on `device-events`, the CommandService fetches all pending commands for that device and dispatches them in creation order.

**TTL Management**

`expires_at = created_at + interval(ttl_seconds)`. A background job (`command-timeout-handler`) runs every 60 seconds and executes:
```sql
UPDATE commands
SET status = 'TIMEOUT', updated_at = NOW()
WHERE status IN ('PENDING', 'DISPATCHED')
  AND expires_at < NOW();
```

**MQTT Dispatch**

Commands are published to `devices/{device_id}/commands/{command_id}` at QoS 1. The device responds on `devices/{device_id}/commands/ack` with:
```json
{"command_id": "uuid", "status": "ACKNOWLEDGED", "device_ts": "ISO8601"}
```

---

### Sprint 23–24 — Certificate Lifecycle Automation

**Expiry Monitoring**

A daily background job (`certificate-expiry-scanner`) queries:
```sql
SELECT * FROM device_certificates
WHERE not_after BETWEEN NOW() AND NOW() + INTERVAL '35 days'
  AND status = 'ACTIVE';
```
For each certificate, a renewal job is created.

**Auto-Renewal Workflow**

1. 30 days before expiry: issue a new certificate for the device
2. Publish the new certificate PEM to `devices/{device_id}/config` via MQTT
3. Device installs and reconnects with new certificate
4. Old certificate revoked and CRL regenerated

**CRL Rotation**

CRL is regenerated every 24 hours regardless of revocations. The `crl-rotation-job` generates the CRL with 25-hour validity (1-hour overlap to prevent EMQX from seeing a briefly expired CRL) and uploads it to S3/MinIO for serving via CDN.

---

## Phase 4 — Analytics, SDK, and Hardening (Weeks 25–32)

**Goals:** Fleet analytics APIs, developer-facing Python SDK, per-tenant rate limiting, KMS integration, load testing at 100K concurrent MQTT connections, and security scan clearance.

### Sprint 25–26 — Analytics and Reporting

**Fleet Health Dashboard API**

`GET /v1/analytics/fleet-health` returns:
- Device status distribution (count per `ACTIVE`, `INACTIVE`, `DECOMMISSIONED`, `PENDING_PROVISIONING`)
- Online/offline ratio (devices with `last_seen_at` within last 5 minutes)
- Telemetry ingestion rate (InfluxDB query: count of points per minute, last 1h)
- Top 10 devices by telemetry volume

**Data Export API**

`POST /v1/export/telemetry` creates an async export job. The worker queries InfluxDB for the specified time range and device scope, writes CSV/JSON to S3, and returns a presigned URL valid for 24 hours. Job status polled via `GET /v1/export/jobs/{job_id}`.

---

### Sprint 27–28 — Developer SDK

**Python SDK (`iot-platform-python`)**

Published to PyPI. Covers:
- `DeviceClient`: register device, update shadow, publish telemetry
- `OTAClient`: acknowledge OTA job, report progress, complete/fail
- `CommandHandler`: decorator-based command handler registration
- `WebhookVerifier`: verify HMAC-SHA256 signature on incoming webhook requests
- `ShadowHandler`: local shadow cache with merge logic

SDK authentication: exchange API key for short-lived JWT via `POST /v1/sdk/token`. SDK handles token refresh transparently.

---

### Sprint 29–30 — Multi-Tenant Hardening

**Row-Level Security**

All tables with an `org_id` column have RLS policies enabled:
```sql
ALTER TABLE devices ENABLE ROW LEVEL SECURITY;
CREATE POLICY device_org_isolation ON devices
  USING (org_id = current_setting('app.current_org_id')::uuid);
```

The application sets `app.current_org_id` at the start of each database transaction using `SET LOCAL`.

**Per-Organization Rate Limiting**

Kong rate limiting plugin configured per route with organization-scoped counters:
- Telemetry ingest: 10,000 data points/minute
- Device CRUD: 1,000 requests/minute
- OTA deployment creation: 100/hour

Quotas stored in Kong's Redis-backed rate-limiting storage, keyed by `org_id` extracted from JWT claim.

**API Key Scoping**

API keys carry a `scope` claim: `read`, `write`, or `admin`. Middleware enforces scope against route-level required scope. Keys are hashed with BLAKE2b before storage; plaintext is returned once on creation.

---

### Sprint 31–32 — Performance and Security Hardening

**Load Testing**

Use k6 and a custom MQTT load generator (based on Eclipse Paho / EMQX `emqtt-bench`):
- Ramp to 100K concurrent MQTT connections over 30 minutes
- Sustain 1M telemetry points/minute for 60 minutes
- Measure: EMQX message latency (p99 < 500ms), Kafka consumer lag (< 10K), InfluxDB write latency (p95 < 200ms)

**EMQX Tuning**

```hocon
node {
  max_connections = 500000
  process_limit = 2000000
}
listener.ssl.default {
  max_connections = 250000
  acceptors = 64
  handshake_timeout = 15s
}
```

**Security**

- OWASP ZAP baseline scan against Kong API Gateway; all HIGH findings resolved
- Trivy image scan on all container images; no CRITICAL CVEs in final images
- IEC 62443-3-3 compliance checklist completed (Security Level 2 target)
- Penetration test scope: MQTT broker authentication bypass, REST API authorization bypass, tenant isolation

---

## Coding Standards and Patterns

**Python**
- Type hints required on all public functions and methods. Use `from __future__ import annotations` for forward references.
- All request and response bodies modeled as `pydantic.BaseModel` subclasses with strict mode enabled (`model_config = ConfigDict(strict=True)`).
- All I/O operations (database, Redis, Kafka, HTTP) must use `async/await`. Synchronous I/O in async context is a blocker during code review.

**Error Handling**
- Never use bare `except:` or `except Exception: pass`. All exceptions must be logged with the correlation ID before re-raising or converting to HTTP responses.
- Custom exception hierarchy: `IotPlatformError` → `ValidationError`, `AuthorizationError`, `ResourceNotFoundError`, `ConflictError`, `QuotaExceededError`.

**Logging**
- Structured JSON logging via `structlog`. Every log entry includes: `org_id`, `device_id` (when applicable), `request_id` (from `X-Request-ID` header, generated if absent), `service`, `level`, `timestamp`.
- Never log: certificate PEM content, private keys, PSK values, JWT tokens, or API key plaintext.

**Database**
- Always use parameterized queries. String concatenation in SQL is a security-critical code review blocker.
- Use SQLAlchemy Core (not ORM) for all performance-critical queries. ORM is acceptable only for simple admin/background scripts.
- All migrations must have a corresponding `downgrade()` function. Rollback must be tested in CI.

**Kafka**
- Commit offset only after successful processing. On unrecoverable errors (schema deserialization failure after 3 retries), write to `dead-letter` topic and commit offset.
- Consumer poll timeout: 1000ms. Max records per poll: 500.

**Testing**
- `pytest` with `pytest-asyncio` for async tests. All async test functions decorated with `@pytest.mark.asyncio`.
- Test data created via `factory_boy` factories. No hardcoded UUIDs in tests.
- Integration tests use `testcontainers` to spin up real PostgreSQL, Redis, and Kafka instances.
- Minimum coverage gate: 85% for services in Phase 1 and 2; 80% for services in Phase 3 and 4.

**Security**
- All secrets injected via Kubernetes Secrets mounted as environment variables. No secrets in `ConfigMap`, Helm values files, or source code.
- Container images run as non-root (`runAsUser: 1000`, `allowPrivilegeEscalation: false`).
- All service-to-service communication within the cluster uses mutual TLS via Istio sidecar proxies.
