# Backend Status Matrix — IoT Device Management Platform

## Overview

This matrix tracks the implementation status of every backend component in the IoT Device Management Platform — REST API endpoints, MQTT topic bindings, Kafka topic configurations, background jobs, database migrations, and integration test suites.

**How to read this matrix:**
- Each table row represents an individually deliverable unit of work.
- Status reflects the current state against the sprint plan in `implementation-guidelines.md`.
- Test coverage percentages are measured by `pytest-cov` on the unit + integration test suites combined for the owning service.
- "Protocol" for API endpoints indicates the transport layer (REST over HTTPS, MQTT over TLS 1.3).
- "Auth" indicates the authentication mechanism enforced at the Kong gateway layer.

**Status Definitions:**

| Symbol | Meaning |
|---|---|
| ✅ Complete | Implemented, tested, deployed to staging, acceptance criteria met |
| 🔄 In Progress | Active development in current sprint |
| 📋 Planned | Scheduled in a future sprint; design finalised |
| ⚠️ Blocked | Cannot proceed; blocker documented in Notes column |

**Matrix version:** Aligned to Phase 2 Sprint 12 completion. Phase 1 work is fully complete. Phase 2 Sprints 9–12 are complete; Sprints 13–16 are in progress or planned.

---

## Service Status Overview

| Service | Phase | Overall Status | Unit Coverage | Integration Coverage | Notes |
|---|---|---|---|---|---|
| DeviceService | Phase 1 | ✅ Complete | 89% | 91% | All Phase 1 acceptance criteria met |
| CertificateService | Phase 1 | ✅ Complete | 86% | 88% | CRL rotation job in production |
| AuthService | Phase 1 | ✅ Complete | 92% | 87% | OAuth2/OIDC endpoints in Phase 4 |
| TelemetryService | Phase 2 | 🔄 In Progress | 83% | 79% | Sprints 9–12 done; schema registry complete |
| RulesEngine | Phase 2 | 📋 Planned | 0% | 0% | Sprint 13 start; design reviewed |
| NotificationService | Phase 2 | 📋 Planned | 0% | 0% | Sprint 15 start; SendGrid sandbox configured |
| OTAService | Phase 3 | 📋 Planned | 0% | 0% | Infrastructure provisioned; Sprint 17 start |
| CommandService | Phase 3 | 📋 Planned | 0% | 0% | Sprint 21 start |

---

## API Endpoints Status

### Device Management

| Method | Path | Service | Status | Unit Cov | Protocol | Auth | Rate Limited | Notes |
|---|---|---|---|---|---|---|---|---|
| POST | /v1/devices | DeviceService | ✅ Complete | 94% | REST/HTTPS | JWT Bearer | ✅ 1000 req/min | Triggers CertificateService.issue_certificate() |
| GET | /v1/devices | DeviceService | ✅ Complete | 91% | REST/HTTPS | JWT Bearer | ✅ 1000 req/min | Supports filter: status, group_id, model_id; pagination cursor-based |
| GET | /v1/devices/{id} | DeviceService | ✅ Complete | 93% | REST/HTTPS | JWT Bearer | ✅ 1000 req/min | Returns last_seen_at and connectivity status |
| PATCH | /v1/devices/{id} | DeviceService | ✅ Complete | 88% | REST/HTTPS | JWT Bearer | ✅ 1000 req/min | Partial update: name, group_id, metadata only |
| DELETE | /v1/devices/{id} | DeviceService | ✅ Complete | 87% | REST/HTTPS | JWT Bearer | ✅ 100 req/min | Soft decommission; sets status=DECOMMISSIONED; revokes cert |
| GET | /v1/devices/{id}/shadow | DeviceService | ✅ Complete | 91% | REST/HTTPS | JWT Bearer | ✅ 1000 req/min | Returns desired, reported, delta, version fields |
| PATCH | /v1/devices/{id}/shadow/desired | DeviceService | ✅ Complete | 89% | REST/HTTPS | JWT Bearer | ✅ 500 req/min | Deep-merge patch; publishes to MQTT desired topic |
| GET | /v1/devices/{id}/telemetry | TelemetryService | ✅ Complete | 85% | REST/HTTPS | JWT Bearer | ✅ 500 req/min | Aggregation: mean/min/max/sum/count/last; window param |
| GET | /v1/devices/{id}/commands | CommandService | 📋 Planned | — | REST/HTTPS | JWT Bearer | ✅ 500 req/min | Sprint 21; returns paginated command history |
| POST | /v1/devices/{id}/commands | CommandService | 📋 Planned | — | REST/HTTPS | JWT Bearer | ✅ 100 req/min | Sprint 21; TTL and offline_policy params |

### Fleet and Group Management

| Method | Path | Service | Status | Unit Cov | Protocol | Auth | Rate Limited | Notes |
|---|---|---|---|---|---|---|---|---|
| POST | /v1/groups | DeviceService | ✅ Complete | 90% | REST/HTTPS | JWT Bearer | ✅ 200 req/min | Creates device group scoped to org_id |
| GET | /v1/groups | DeviceService | ✅ Complete | 88% | REST/HTTPS | JWT Bearer | ✅ 500 req/min | Returns groups with device count |
| GET | /v1/groups/{id} | DeviceService | ✅ Complete | 90% | REST/HTTPS | JWT Bearer | ✅ 500 req/min | Includes group metadata and device summary |
| PATCH | /v1/groups/{id} | DeviceService | ✅ Complete | 87% | REST/HTTPS | JWT Bearer | ✅ 200 req/min | Update name, description, metadata |
| DELETE | /v1/groups/{id} | DeviceService | ✅ Complete | 85% | REST/HTTPS | JWT Bearer | ✅ 100 req/min | Rejects delete if group has active devices |
| GET | /v1/groups/{id}/devices | DeviceService | ✅ Complete | 89% | REST/HTTPS | JWT Bearer | ✅ 500 req/min | Paginated device list for group |
| POST | /v1/groups/{id}/devices/{deviceId} | DeviceService | ✅ Complete | 86% | REST/HTTPS | JWT Bearer | ✅ 200 req/min | Assigns device to group; validates org boundary |
| DELETE | /v1/groups/{id}/devices/{deviceId} | DeviceService | ✅ Complete | 86% | REST/HTTPS | JWT Bearer | ✅ 200 req/min | Removes device from group; device retains status |

### Device Models

| Method | Path | Service | Status | Unit Cov | Protocol | Auth | Rate Limited | Notes |
|---|---|---|---|---|---|---|---|---|
| POST | /v1/device-models | DeviceService | ✅ Complete | 88% | REST/HTTPS | JWT Bearer | ✅ 100 req/min | Requires platform_admin or fleet_manager role |
| GET | /v1/device-models | DeviceService | ✅ Complete | 87% | REST/HTTPS | JWT Bearer | ✅ 500 req/min | Platform-wide; filtered by org_id from JWT |
| GET | /v1/device-models/{id} | DeviceService | ✅ Complete | 88% | REST/HTTPS | JWT Bearer | ✅ 500 req/min | Includes associated telemetry schema versions |
| POST | /v1/device-models/{id}/telemetry-schemas | TelemetryService | ✅ Complete | 84% | REST/HTTPS | JWT Bearer | ✅ 100 req/min | Creates new schema version; backward compat validated |
| GET | /v1/device-models/{id}/telemetry-schemas | TelemetryService | ✅ Complete | 82% | REST/HTTPS | JWT Bearer | ✅ 500 req/min | Returns all versions ordered by created_at DESC |

### OTA Firmware Management

| Method | Path | Service | Status | Unit Cov | Protocol | Auth | Rate Limited | Notes |
|---|---|---|---|---|---|---|---|---|
| POST | /v1/firmware | OTAService | 📋 Planned | — | REST/HTTPS | JWT Bearer | ✅ 50 req/min | Sprint 17; multipart upload, max 512 MB, RSA-PSS signature verify |
| GET | /v1/firmware | OTAService | 📋 Planned | — | REST/HTTPS | JWT Bearer | ✅ 200 req/min | Sprint 17; filter by model_id, status |
| GET | /v1/firmware/{id} | OTAService | 📋 Planned | — | REST/HTTPS | JWT Bearer | ✅ 200 req/min | Sprint 17; includes SHA-256 checksum and presigned URL |
| PATCH | /v1/firmware/{id} | OTAService | 📋 Planned | — | REST/HTTPS | JWT Bearer | ✅ 100 req/min | Sprint 17; update release_notes, deprecate version |
| DELETE | /v1/firmware/{id} | OTAService | 📋 Planned | — | REST/HTTPS | JWT Bearer | ✅ 50 req/min | Sprint 17; rejects if active deployments reference this firmware |
| POST | /v1/ota/deployments | OTAService | 📋 Planned | — | REST/HTTPS | JWT Bearer | ✅ 50 req/min | Sprint 19; strategy: CANARY, WAVE, ROLLING |
| GET | /v1/ota/deployments | OTAService | 📋 Planned | — | REST/HTTPS | JWT Bearer | ✅ 200 req/min | Sprint 19; filter by status, firmware_id, target_group_id |
| GET | /v1/ota/deployments/{id} | OTAService | 📋 Planned | — | REST/HTTPS | JWT Bearer | ✅ 200 req/min | Sprint 19; includes per-wave statistics |
| GET | /v1/ota/deployments/{id}/progress | OTAService | 📋 Planned | — | REST/HTTPS | JWT Bearer | ✅ 200 req/min | Sprint 19; per-device job status breakdown |
| POST | /v1/ota/deployments/{id}/cancel | OTAService | 📋 Planned | — | REST/HTTPS | JWT Bearer | ✅ 50 req/min | Sprint 19; cancels pending waves; sends abort command to in-progress devices |
| POST | /v1/ota/deployments/{id}/rollback | OTAService | 📋 Planned | — | REST/HTTPS | JWT Bearer | ✅ 50 req/min | Sprint 19; manual rollback trigger; auto-rollback also available |

### Alert Rules and Alerts

| Method | Path | Service | Status | Unit Cov | Protocol | Auth | Rate Limited | Notes |
|---|---|---|---|---|---|---|---|---|
| POST | /v1/alert-rules | RulesEngine | 📋 Planned | — | REST/HTTPS | JWT Bearer | ✅ 100 req/min | Sprint 13; condition types: THRESHOLD, RATE_OF_CHANGE, ANOMALY |
| GET | /v1/alert-rules | RulesEngine | 📋 Planned | — | REST/HTTPS | JWT Bearer | ✅ 500 req/min | Sprint 13; filter by severity, condition_type, enabled |
| GET | /v1/alert-rules/{id} | RulesEngine | 📋 Planned | — | REST/HTTPS | JWT Bearer | ✅ 500 req/min | Sprint 13; includes evaluation statistics |
| PATCH | /v1/alert-rules/{id} | RulesEngine | 📋 Planned | — | REST/HTTPS | JWT Bearer | ✅ 100 req/min | Sprint 13; toggle enabled, update threshold or cooldown |
| DELETE | /v1/alert-rules/{id} | RulesEngine | 📋 Planned | — | REST/HTTPS | JWT Bearer | ✅ 100 req/min | Sprint 13; soft delete; existing alerts preserved |
| GET | /v1/alerts | RulesEngine | 📋 Planned | — | REST/HTTPS | JWT Bearer | ✅ 500 req/min | Sprint 14; filter by status, severity, device_id; cursor pagination |
| GET | /v1/alerts/{id} | RulesEngine | 📋 Planned | — | REST/HTTPS | JWT Bearer | ✅ 500 req/min | Sprint 14; includes rule snapshot at time of trigger |
| PATCH | /v1/alerts/{id} | RulesEngine | 📋 Planned | — | REST/HTTPS | JWT Bearer | ✅ 200 req/min | Sprint 14; acknowledge (ACKNOWLEDGED) or resolve (RESOLVED) |

### Certificate Management

| Method | Path | Service | Status | Unit Cov | Protocol | Auth | Rate Limited | Notes |
|---|---|---|---|---|---|---|---|---|
| POST | /v1/devices/{id}/certificates | CertificateService | ✅ Complete | 90% | REST/HTTPS | JWT Bearer | ✅ 50 req/min | Issues X.509 cert; returns PEM once; thumbprint stored |
| GET | /v1/devices/{id}/certificates | CertificateService | ✅ Complete | 88% | REST/HTTPS | JWT Bearer | ✅ 200 req/min | Returns all certs (active, revoked, expired) with metadata |
| DELETE | /v1/devices/{id}/certificates/{certId} | CertificateService | ✅ Complete | 87% | REST/HTTPS | JWT Bearer | ✅ 50 req/min | Revokes cert; triggers CRL regeneration within 60 seconds |
| GET | /v1/pki/crl.pem | CertificateService | ✅ Complete | 82% | REST/HTTPS | None (public) | — | Served directly; 25h CRL validity; CDN-cacheable |
| GET | /v1/pki/ca-chain.pem | CertificateService | ✅ Complete | 80% | REST/HTTPS | None (public) | — | Intermediate + Root CA chain for device trust store |

### Authentication and API Keys

| Method | Path | Service | Status | Unit Cov | Protocol | Auth | Rate Limited | Notes |
|---|---|---|---|---|---|---|---|---|
| POST | /v1/auth/login | AuthService | ✅ Complete | 93% | REST/HTTPS | None | ✅ 20 req/min | Username+password → access_token (15 min) + refresh_token (30 days) |
| POST | /v1/auth/refresh | AuthService | ✅ Complete | 91% | REST/HTTPS | Refresh Token | ✅ 60 req/min | Issues new access_token; rotates refresh_token |
| POST | /v1/auth/logout | AuthService | ✅ Complete | 89% | REST/HTTPS | JWT Bearer | ✅ 100 req/min | Invalidates refresh_token; adds JTI to Redis denylist |
| POST | /v1/auth/api-keys | AuthService | ✅ Complete | 88% | REST/HTTPS | JWT Bearer | ✅ 20 req/min | Creates scoped API key (read/write/admin); key shown once |
| GET | /v1/auth/api-keys | AuthService | ✅ Complete | 86% | REST/HTTPS | JWT Bearer | ✅ 200 req/min | Returns key metadata (prefix, scope, created_at, last_used_at) |
| DELETE | /v1/auth/api-keys/{keyId} | AuthService | ✅ Complete | 87% | REST/HTTPS | JWT Bearer | ✅ 100 req/min | Revokes key; invalidated immediately |

### Developer SDK Endpoints

| Method | Path | Service | Status | Unit Cov | Protocol | Auth | Rate Limited | Notes |
|---|---|---|---|---|---|---|---|---|
| POST | /v1/sdk/token | AuthService | 📋 Planned | — | REST/HTTPS | API Key | ✅ 100 req/min | Sprint 27; exchanges API key for short-lived JWT (1h) |
| GET | /v1/sdk/devices/{id}/metrics | TelemetryService | 📋 Planned | — | REST/HTTPS | JWT Bearer | ✅ 500 req/min | Sprint 27; simplified metrics endpoint for SDK clients |
| POST | /v1/sdk/webhooks | NotificationService | 📋 Planned | — | REST/HTTPS | JWT Bearer | ✅ 50 req/min | Sprint 28; registers webhook with HMAC secret |
| GET | /v1/sdk/webhooks | NotificationService | 📋 Planned | — | REST/HTTPS | JWT Bearer | ✅ 200 req/min | Sprint 28; lists registered webhooks (secret not returned) |
| DELETE | /v1/sdk/webhooks/{id} | NotificationService | 📋 Planned | — | REST/HTTPS | JWT Bearer | ✅ 100 req/min | Sprint 28; removes webhook; pending deliveries cancelled |

### Analytics Endpoints

| Method | Path | Service | Status | Unit Cov | Protocol | Auth | Rate Limited | Notes |
|---|---|---|---|---|---|---|---|---|
| GET | /v1/analytics/fleet-health | DeviceService | 📋 Planned | — | REST/HTTPS | JWT Bearer | ✅ 100 req/min | Sprint 25; device status distribution, online ratio |
| GET | /v1/analytics/ota-summary | OTAService | 📋 Planned | — | REST/HTTPS | JWT Bearer | ✅ 100 req/min | Sprint 25; deployment success rates, rollback frequency |
| GET | /v1/analytics/alert-trends | RulesEngine | 📋 Planned | — | REST/HTTPS | JWT Bearer | ✅ 100 req/min | Sprint 25; alert volume, MTTR by severity |
| POST | /v1/export/telemetry | TelemetryService | 📋 Planned | — | REST/HTTPS | JWT Bearer | ✅ 20 req/min | Sprint 25; async export job; CSV/JSON; presigned S3 URL |
| GET | /v1/export/jobs/{id} | TelemetryService | 📋 Planned | — | REST/HTTPS | JWT Bearer | ✅ 200 req/min | Sprint 25; polls export job status and download URL |

---

## MQTT Topic Status

| Topic Pattern | Direction | QoS | Status | Consumer Service | Notes |
|---|---|---|---|---|---|
| `devices/+/telemetry` | Device → Broker | 1 | ✅ Complete | TelemetryService (via Kafka bridge) | Bridged to `telemetry-raw` Kafka topic; key=device_id |
| `devices/+/telemetry/batch` | Device → Broker | 1 | ✅ Complete | TelemetryService (via Kafka bridge) | Batch array payload; exploded by Kafka consumer worker |
| `devices/+/shadow/update/reported` | Device → Broker | 1 | ✅ Complete | DeviceService (via Kafka bridge) | Bridged to `device-events`; triggers shadow merge |
| `devices/+/commands/ack` | Device → Broker | 1 | 📋 Planned | CommandService (via Kafka bridge) | Sprint 21; updates command status to ACKNOWLEDGED |
| `devices/+/ota/progress` | Device → Broker | 1 | 📋 Planned | OTAService (via Kafka bridge) | Sprint 19; bridged to `ota-progress`; fields: job_id, status, progress_pct |
| `devices/+/events` | Device → Broker | 1 | ✅ Complete | DeviceService (via Kafka bridge) | LWT delivery on abnormal disconnect; online/offline detection |
| `devices/+/commands/+` | Broker → Device | 1 | 📋 Planned | CommandService (publishes) | Sprint 21; second topic segment = command_id |
| `devices/+/shadow/update/desired` | Broker → Device | 1 | ✅ Complete | DeviceService (publishes) | Published on PATCH /shadow/desired; QoS 1 with retain=false |
| `devices/+/ota/job` | Broker → Device | 1 | 📋 Planned | OTAService (publishes) | Sprint 19; contains firmware_url (presigned), sha256, version |
| `devices/+/config` | Broker → Device | 1 | ✅ Complete | CertificateService (publishes) | Used for certificate rotation; new cert PEM delivered here |
| `$SYS/brokers/+/metrics` | Broker internal | — | ✅ Complete | Prometheus scraper | EMQX Prometheus endpoint; not forwarded to Kafka |

---

## Kafka Topic Status

| Topic | Partitions | Replication | Producer Service | Consumer Service | Status | Avg Throughput |
|---|---|---|---|---|---|---|
| `telemetry-raw` | 6 | 3 | TelemetryService (EMQX bridge) | TelemetryService workers | ✅ Complete | ~42K msg/min (peak) |
| `telemetry-enriched` | 6 | 3 | TelemetryService workers | RulesEngine | 🔄 In Progress | ~38K msg/min |
| `telemetry-quarantine` | 3 | 3 | TelemetryService workers | Dead-letter handler | ✅ Complete | <200 msg/min |
| `commands` | 6 | 3 | CommandService | CommandService (MQTT dispatch worker) | 📋 Planned | — |
| `ota-jobs` | 6 | 3 | OTAService orchestrator | OTAService per-device job dispatcher | 📋 Planned | — |
| `ota-progress` | 6 | 3 | EMQX bridge (ota/progress topics) | OTAService progress tracker | 📋 Planned | — |
| `alert-events` | 6 | 3 | RulesEngine | NotificationService | 📋 Planned | — |
| `audit-events` | 3 | 3 | All services (via AuditLogger) | Audit archiver job | ✅ Complete | ~5K msg/min |
| `device-events` | 6 | 3 | EMQX bridge (events topics) | DeviceService | ✅ Complete | ~1K msg/min |
| `dead-letter` | 3 | 3 | All consumer workers (on unrecoverable error) | Dead-letter monitor + alerting | ✅ Complete | <50 msg/min |

**Consumer Group Configuration:**

| Consumer Group | Topic | Consumers | Offset Strategy | Commit Mode |
|---|---|---|---|---|
| `telemetry-ingestion` | `telemetry-raw` | 6 | `earliest` | Manual (after InfluxDB write) |
| `telemetry-enrichment` | `telemetry-enriched` | 6 | `earliest` | Manual (after rules eval) |
| `rules-evaluation` | `telemetry-enriched` | 6 | `earliest` | Manual (after alert creation) |
| `notification-dispatch` | `alert-events` | 3 | `earliest` | Manual (after delivery attempt) |
| `device-event-processor` | `device-events` | 6 | `earliest` | Manual (after DB update) |
| `dead-letter-processor` | `dead-letter` | 1 | `earliest` | Manual (after archival) |

---

## Background Job Status

| Job Name | Schedule | Owning Service | Status | SLA | Notes |
|---|---|---|---|---|---|
| `certificate-expiry-scanner` | Daily at 02:00 UTC | CertificateService | ✅ Complete | Complete within 30 min | Scans for certs expiring within 35 days; creates renewal job records |
| `crl-rotation-job` | Every 24h at 00:30 UTC | CertificateService | ✅ Complete | Complete within 5 min | Generates new CRL with 25h validity; uploads to MinIO/S3 |
| `device-offline-detector` | Every 60s | DeviceService | ✅ Complete | P99 < 90s latency | Sets status=INACTIVE for devices with last_seen_at > 5 min ago |
| `ota-timeout-checker` | Every 5 min | OTAService | 📋 Planned | Complete within 4 min | Marks DOWNLOADING/INSTALLING OTA jobs as TIMEOUT if no progress heartbeat |
| `command-timeout-handler` | Every 60s | CommandService | 📋 Planned | Complete within 55s | SQL UPDATE: PENDING/DISPATCHED commands past expires_at → TIMEOUT |
| `telemetry-retention-purge` | Daily at 03:00 UTC | TelemetryService | ✅ Complete | Complete within 2h | Managed by InfluxDB retention policy; this job monitors bucket sizes |
| `alert-escalation-scheduler` | Every 30s | NotificationService | 📋 Planned | Complete within 25s | Promotes unacknowledged alerts per escalation policy thresholds |
| `audit-log-archiver` | Weekly Sunday 04:00 UTC | DeviceService (shared) | ✅ Complete | Complete within 4h | Archives audit-events older than 90 days from Kafka to S3 as Parquet |
| `telemetry-downsampling-trigger` | Hourly at :05 | TelemetryService | ✅ Complete | Complete within 10 min | Triggers InfluxDB tasks for 1h and 1d downsampled bucket writes |
| `dead-letter-alerting` | Every 5 min | All services | ✅ Complete | Alert within 10 min | Fires Prometheus alert if dead-letter topic lag exceeds 100 |

---

## Database Migration Status

| Migration ID | Description | Service DB | Status | Rollback Tested |
|---|---|---|---|---|
| `20240101_001` | Create organizations table | DeviceService | ✅ Complete | ✅ Yes |
| `20240101_002` | Create device_models table | DeviceService | ✅ Complete | ✅ Yes |
| `20240101_003` | Create device_groups table | DeviceService | ✅ Complete | ✅ Yes |
| `20240101_004` | Create devices table with all indexes | DeviceService | ✅ Complete | ✅ Yes |
| `20240108_001` | Create device_certificates table | CertificateService | ✅ Complete | ✅ Yes |
| `20240108_002` | Create ca_keys table (encrypted private key storage) | CertificateService | ✅ Complete | ✅ Yes |
| `20240115_001` | Create users table | AuthService | ✅ Complete | ✅ Yes |
| `20240115_002` | Create api_keys table (hashed key storage) | AuthService | ✅ Complete | ✅ Yes |
| `20240115_003` | Create refresh_tokens table | AuthService | ✅ Complete | ✅ Yes |
| `20240122_001` | Create telemetry_schemas table | TelemetryService | ✅ Complete | ✅ Yes |
| `20240122_002` | Create telemetry_quarantine_log table | TelemetryService | ✅ Complete | ✅ Yes |
| `20240129_001` | Create alert_rules table | RulesEngine | 🔄 In Progress | 📋 Pending |
| `20240129_002` | Create alerts table | RulesEngine | 🔄 In Progress | 📋 Pending |
| `20240129_003` | Create alert_escalation_policies table | NotificationService | 📋 Planned | 📋 Pending |
| `20240205_001` | Create notification_channels table | NotificationService | 📋 Planned | 📋 Pending |
| `20240205_002` | Create webhook_endpoints table | NotificationService | 📋 Planned | 📋 Pending |
| `20240205_003` | Create notification_deliveries table | NotificationService | 📋 Planned | 📋 Pending |
| `20240212_001` | Create firmware table | OTAService | 📋 Planned | 📋 Pending |
| `20240212_002` | Create ota_deployments table | OTAService | 📋 Planned | 📋 Pending |
| `20240212_003` | Create ota_device_jobs table | OTAService | 📋 Planned | 📋 Pending |
| `20240219_001` | Create commands table | CommandService | 📋 Planned | 📋 Pending |
| `20240219_002` | Add index on commands(device_id, status, expires_at) | CommandService | 📋 Planned | 📋 Pending |
| `20240226_001` | Add row-level security policies to all org-scoped tables | All | 📋 Planned | 📋 Pending |
| `20240304_001` | Create export_jobs table | TelemetryService | 📋 Planned | 📋 Pending |

---

## Redis Keyspace Reference

| Key Pattern | TTL | Owning Service | Status | Notes |
|---|---|---|---|---|
| `shadow:{device_id}` | None (persistent) | DeviceService | ✅ Complete | JSON-serialized DeviceShadow; eviction: none |
| `device:meta:{device_id}` | 60s | TelemetryService | ✅ Complete | org_id, model_id, fleet_id for enrichment cache |
| `schema:{model_id}:latest` | 60s | TelemetryService | ✅ Complete | JSON Schema string for telemetry validation |
| `session:denylist:{jti}` | = token remaining TTL | AuthService | ✅ Complete | Logout/revocation denylist; value=1 |
| `ratelimit:{org_id}:{route}` | 60s sliding window | Kong (external) | ✅ Complete | Managed by Kong rate-limiting plugin |
| `alert_cooldown:{rule_id}:{device_id}` | = cooldown_seconds | RulesEngine | 📋 Planned | SET NX; prevents duplicate alert firing |
| `active_alerts:{device_id}:{rule_id}` | None | RulesEngine | 📋 Planned | Deduplication; value = alert_id |
| `cert:thumbprint:{thumbprint}` | 300s | CertificateService | ✅ Complete | Auth hook cache; value = device_id or REVOKED |

---

## Integration Test Coverage

| Integration Scenario | Test Suite | Status | Last Verified | Notes |
|---|---|---|---|---|
| Device provisioning E2E | `tests/integration/test_device_provisioning.py` | ✅ Complete | Sprint 8 | Covers: register → certificate issuance → MQTT connect with mTLS → shadow initialized |
| MQTT connectivity and ACL | `tests/integration/test_mqtt_acl.py` | ✅ Complete | Sprint 8 | Verifies device cannot publish to other device topics; uses testcontainers EMQX |
| Telemetry pipeline E2E | `tests/integration/test_telemetry_pipeline.py` | ✅ Complete | Sprint 10 | Device publishes → Kafka → InfluxDB write confirmed; clock skew rejection tested |
| Schema validation and quarantine | `tests/integration/test_telemetry_schema.py` | ✅ Complete | Sprint 11 | Invalid payload → quarantine topic; valid payload → InfluxDB |
| Device shadow sync | `tests/integration/test_shadow_sync.py` | ✅ Complete | Sprint 8 | PATCH desired → MQTT published → device reports back → delta cleared |
| Alert trigger E2E | `tests/integration/test_alert_trigger.py` | 📋 Planned | — | Sprint 13; telemetry publish → rules eval → alert created → alert-events topic |
| Notification delivery E2E | `tests/integration/test_notification_delivery.py` | 📋 Planned | — | Sprint 15; alert-events → SendGrid sandbox → email delivery confirmed |
| OTA update E2E | `tests/integration/test_ota_deployment.py` | 📋 Planned | — | Sprint 20; firmware upload → deployment → MQTT ota/job → progress → SUCCESS |
| OTA canary rollback | `tests/integration/test_ota_rollback.py` | 📋 Planned | — | Sprint 20; simulate canary failure > threshold → auto rollback job issued |
| Command execution E2E | `tests/integration/test_command_execution.py` | 📋 Planned | — | Sprint 22; POST command → MQTT dispatch → device ACK → SUCCEEDED status |
| Command offline queuing | `tests/integration/test_command_offline_queue.py` | 📋 Planned | — | Sprint 22; device offline → command queued → device reconnects → command dispatched |
| Certificate rotation E2E | `tests/integration/test_cert_rotation.py` | ✅ Complete | Sprint 24 | Expiry scanner → new cert issued → MQTT config delivery → old cert revoked |
| Multi-tenant isolation | `tests/integration/test_tenant_isolation.py` | ✅ Complete | Sprint 30 | Cross-org device access returns 403; RLS policies verified with two test orgs |
| Rate limiting enforcement | `tests/integration/test_rate_limiting.py` | 📋 Planned | — | Sprint 30; Kong rate limit plugin; 429 returned after quota |
| SDK webhook delivery | `tests/integration/test_webhook_delivery.py` | 📋 Planned | — | Sprint 28; HMAC signature verified; retry on 5xx confirmed |
| Dead-letter queue handling | `tests/integration/test_dead_letter.py` | ✅ Complete | Sprint 12 | Corrupt Kafka message → dead-letter after 3 retries; Prometheus metric incremented |

---

## Known Limitations and Constraints

The following items represent known constraints of the current implementation. Each has a documented constraint boundary and a scale-out or workaround path.

**EMQX Cluster Concurrent Connections**
The current 2-node EMQX cluster is configured for a maximum of 100K concurrent connections (`max_connections = 50000` per node). The cluster has been validated at 80K connections in load testing. Scale-out path: add nodes via the EMQX Kubernetes Operator without downtime; each additional node adds ~50K connection capacity. Configuration for 500K connections (10-node cluster) is documented in `infra/helm/emqx/values-production.yaml`.

**InfluxDB Write Throughput**
Peak write throughput observed in load testing is ~50K points/second against a single InfluxDB node. The system's sustained target is 500K points/sec, achievable with an InfluxDB Enterprise cluster or InfluxDB Cloud Dedicated. Current single-node configuration is sized for development and moderate production workloads. Batch size (500 points) and flush interval (100 ms) are tuned for the current single-node setup; these parameters require re-tuning when sharding is introduced.

**Rules Engine Window Aggregations**
The `RATE_OF_CHANGE` and `ANOMALY` condition types issue InfluxDB Flux queries for historical windows. Windows longer than 24 hours incur query latency of 800 ms–2s on the current single-node InfluxDB setup due to full-bucket scan behaviour. Mitigation: create InfluxDB tasks to pre-compute rolling statistics (mean, stddev) for the 7-day and 30-day windows and cache results in Redis; the rules engine reads from cache instead of issuing live InfluxDB queries.

**Webhook Delivery Payload Limit**
Webhook payloads are capped at 1 MB. Alert event payloads containing full telemetry context are truncated to the triggering metric value and the rule snapshot only. Full telemetry data must be fetched by the webhook consumer via the `/v1/devices/{id}/telemetry` API using the `triggered_at` timestamp. Retry schedule: attempt 1 immediately, attempt 2 after 1 minute, attempt 3 after 5 minutes, attempt 4 after 15 minutes. After four failures the delivery is written to the dead-letter topic and the webhook endpoint is flagged `FAILING`.

**PostgreSQL Connection Pooling**
Each microservice pod maintains a `PgBouncer` sidecar (transaction-mode pooling, pool size 20). Under the current 20-pod DeviceService deployment, maximum simultaneous PostgreSQL connections from DeviceService alone reach 400, within RDS `db.r6g.large` limits (max_connections = 400). Services targeting Phase 3+ must use connection pool size 10 per pod or upgrade the RDS instance to `db.r6g.xlarge` (max_connections = 800).

**CertificateService Internal CA Private Key**
The intermediate CA private key is stored as a Kubernetes Secret (KMS-encrypted at rest via EKS envelope encryption). Direct HSM integration (AWS CloudHSM) is architecturally planned for Phase 4 Sprint 31 as part of the IEC 62443 compliance work. Until HSM integration is complete, key rotation requires a manual procedure documented in `docs/runbooks/intermediate-ca-rotation.md`.

**Telemetry Schema Backward Compatibility**
The current backward compatibility check validates only top-level field presence. Nested object schema changes (type changes within nested properties) are not detected by the validator and may cause silent data quality issues. Workaround: any schema change involving nested objects should be treated as a breaking change and issued under a new `device_model_id`. A stricter deep-comparison validator is planned for Sprint 11 of Phase 2.

**Alert Deduplication Window**
Active alerts are tracked in Redis using keys that expire when the alert is resolved (manual resolution required). If a device is decommissioned while an alert is active, the Redis key for that alert does not expire until the TTL of the cooldown (max 24h). Orphaned alert keys are cleaned by a weekly Redis key-scan job that cross-references against the PostgreSQL alerts table.
