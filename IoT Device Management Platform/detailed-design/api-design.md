# API Design — IoT Device Management Platform

## Overview

The IoT Device Management Platform exposes three primary API surfaces:

- **REST API** — for management operations, portal integrations, and SDK usage
- **MQTT API** — for device-to-platform and platform-to-device messaging
- **WebSocket API** — for real-time event streaming to browser clients and dashboards

| Surface | Endpoint | Protocol |
|---|---|---|
| REST API | `https://api.iotplatform.example.com/v1` | HTTPS / TLS 1.3 |
| MQTT (TLS) | `mqtts://mqtt.iotplatform.example.com:8883` | MQTT 3.1.1 / 5.0 over TLS |
| MQTT (WebSocket) | `wss://ws.iotplatform.example.com:8084/mqtt` | MQTT over WebSocket/TLS |
| WebSocket Stream | `wss://ws.iotplatform.example.com/v1/stream` | WebSocket/TLS |

---

## Authentication

### REST API — JWT Bearer

All REST endpoints require an `Authorization` header with an RS256-signed JWT issued by the Auth Service:

```
Authorization: Bearer <jwt>
```

JWT claims:
```json
{
  "sub": "user-uuid",
  "org_id": "org-uuid",
  "roles": ["admin", "operator"],
  "scopes": ["devices:read", "devices:write", "ota:write"],
  "exp": 1700000000,
  "iss": "https://auth.iotplatform.example.com"
}
```

Token lifetime: 15 minutes. Refresh via POST `/auth/token/refresh` using a long-lived refresh token (30 days). Tokens are validated against the Auth Service public key fetched from `/.well-known/jwks.json` and cached for 5 minutes.

### MQTT — X.509 mTLS

Devices authenticate using client certificates issued by the Certificate Service. The EMQX broker validates the client certificate chain against the platform CA on every TLS handshake. The device's `CN` (Common Name) field must match the `deviceId`.

Alternative authentication methods:
- **PSK**: Pre-shared key configured per device at provisioning time. Used on constrained devices (MCUs) that cannot handle full X.509 handshake.
- **JWT (MQTT 5.0 Enhanced Auth)**: Device sends JWT in the `CONNECT` packet's `Authentication Data` property for lightweight connections.

### API Keys — SDK / Service Integrations

SDK clients and third-party integrations use long-lived API keys passed as:
```
X-API-Key: <api-key>
```

API keys are scoped to a specific organization and a set of permissions. They do not expire automatically but can be revoked via the portal or API.

---

## Versioning Strategy

The API uses URL-based versioning. The current stable version is **v1**. New breaking changes are introduced in **v2** with a minimum 6-month deprecation notice for v1.

Deprecation lifecycle:
1. Version marked deprecated in changelog with removal date.
2. `Deprecation` and `Sunset` response headers added to deprecated endpoints.
3. All calls to deprecated endpoints log a warning in the audit trail.
4. After sunset date, calls to deprecated version return `410 Gone`.

---

## Rate Limiting

Rate limits are applied per organization at the API Gateway (Kong). Limits are expressed in requests per minute (RPM).

Default limits:

| Plan | RPM (read) | RPM (write) | MQTT messages/s |
|---|---|---|---|
| Starter | 300 | 60 | 100 |
| Business | 3000 | 600 | 1000 |
| Enterprise | 30000 | 6000 | 10000 |

Rate limit headers in every response:

```
X-RateLimit-Limit: 3000
X-RateLimit-Remaining: 2947
X-RateLimit-Reset: 1700001234
X-RateLimit-Policy: org-business-plan
```

When a client exceeds its quota, the response is `429 Too Many Requests` with a `Retry-After` header.

---

## Common Response Envelope

All REST responses are wrapped in a standard envelope:

```json
{
  "data": {},
  "meta": {
    "requestId": "req_01HXYZ123",
    "timestamp": "2024-11-15T12:00:00.000Z",
    "page": 1,
    "limit": 50,
    "total": 248
  },
  "errors": []
}
```

On error, `data` is `null` and `errors` contains one or more error objects:

```json
{
  "data": null,
  "meta": { "requestId": "req_01HXYZ124", "timestamp": "2024-11-15T12:00:01.000Z" },
  "errors": [
    {
      "code": "DEVICE_NOT_FOUND",
      "message": "Device with id 'dev-abc123' does not exist in this organization.",
      "field": null
    }
  ]
}
```

### Platform Error Codes

| HTTP Status | Error Code | Description |
|---|---|---|
| 400 | `VALIDATION_ERROR` | Request body or query parameter failed validation |
| 400 | `INVALID_PROVISIONING_METHOD` | Unknown provisioning method specified |
| 400 | `OTA_JOB_CONFLICT` | Another OTA deployment is already active for the target group |
| 400 | `FIRMWARE_CHECKSUM_MISMATCH` | Uploaded firmware SHA256 does not match provided checksum |
| 400 | `SHADOW_VERSION_CONFLICT` | Shadow update version does not match current version (optimistic lock) |
| 400 | `CERTIFICATE_ALREADY_REVOKED` | Attempted to revoke an already-revoked certificate |
| 401 | `AUTHENTICATION_REQUIRED` | Missing or expired Bearer token or API key |
| 401 | `TOKEN_EXPIRED` | JWT has passed its expiration time |
| 403 | `INSUFFICIENT_SCOPE` | JWT scopes do not permit this operation |
| 403 | `ORGANIZATION_MISMATCH` | Resource does not belong to the authenticated organization |
| 404 | `DEVICE_NOT_FOUND` | Device ID not found |
| 404 | `GROUP_NOT_FOUND` | Device group ID not found |
| 404 | `FIRMWARE_NOT_FOUND` | Firmware version ID not found |
| 404 | `DEPLOYMENT_NOT_FOUND` | OTA deployment ID not found |
| 404 | `RULE_NOT_FOUND` | Alert rule ID not found |
| 404 | `CERTIFICATE_NOT_FOUND` | Certificate ID not found |
| 409 | `DEVICE_ALREADY_EXISTS` | Serial number already registered in this organization |
| 409 | `GROUP_HIERARCHY_DEPTH_EXCEEDED` | Adding this group would exceed the maximum hierarchy depth of 5 |
| 410 | `DEVICE_DECOMMISSIONED` | Operation rejected; device has been decommissioned |
| 422 | `CERTIFICATE_REVOKED` | Device certificate is revoked; operation rejected |
| 429 | `RATE_LIMIT_EXCEEDED` | Organization request quota exhausted |
| 500 | `INTERNAL_ERROR` | Unexpected internal service error |
| 503 | `SERVICE_UNAVAILABLE` | Dependent service temporarily unavailable (includes retry guidance) |

---

## Device Management

### Provision New Device

**POST /devices**

Required scope: `devices:write`

Registers and provisions a new device within the authenticated organization. For `x509` provisioning, the Certificate Service issues a client certificate automatically. For `psk`, a pre-shared key is returned in the response and must be stored securely — it is never returned again.

**Request Body:**
```json
{
  "serial_number": "SN-20241115-00042",
  "device_model_id": "mdl-rpi4-sensor-v2",
  "name": "Warehouse Temp Sensor 42",
  "group_id": "grp-warehouse-floor-a",
  "provisioning_method": "x509",
  "tags": {
    "location": "rack-12-slot-4",
    "environment": "production"
  },
  "metadata": {
    "manufacturer_batch": "2024-Q3",
    "hardware_revision": "1.2"
  }
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| serial_number | string | Yes | Globally unique per organization, 1–256 chars |
| device_model_id | string | Yes | Must reference an existing device model |
| name | string | Yes | Human-readable display name, 1–128 chars |
| group_id | string | No | Assign to a device group on creation |
| provisioning_method | enum | Yes | `x509`, `psk`, or `jwt` |
| tags | object | No | Key/value string pairs, max 50 tags |
| metadata | object | No | Arbitrary metadata, max 4KB |

**Response — 201 Created:**
```json
{
  "data": {
    "device_id": "dev-01HXYZ789",
    "serial_number": "SN-20241115-00042",
    "name": "Warehouse Temp Sensor 42",
    "status": "PENDING",
    "device_model_id": "mdl-rpi4-sensor-v2",
    "group_id": "grp-warehouse-floor-a",
    "org_id": "org-acme-corp",
    "provisioning_method": "x509",
    "certificate": {
      "certificate_id": "cert-01HABCD",
      "pem": "-----BEGIN CERTIFICATE-----\nMIIB...\n-----END CERTIFICATE-----",
      "fingerprint_sha256": "AA:BB:CC:...",
      "expires_at": "2026-11-15T12:00:00Z"
    },
    "mqtt_endpoint": "mqtts://mqtt.iotplatform.example.com:8883",
    "created_at": "2024-11-15T12:00:00Z"
  },
  "meta": { "requestId": "req_01HXYZ001", "timestamp": "2024-11-15T12:00:00Z" },
  "errors": []
}
```

**Status codes:** 201 Created, 400 VALIDATION_ERROR, 409 DEVICE_ALREADY_EXISTS, 404 GROUP_NOT_FOUND

---

### List Devices

**GET /devices**

Required scope: `devices:read`

**Query Parameters:**

| Parameter | Type | Description |
|---|---|---|
| status | enum | Filter by device status: `PENDING`, `ACTIVE`, `INACTIVE`, `QUARANTINE`, `DECOMMISSIONED` |
| group_id | string | Filter by group (includes descendants when `include_descendants=true`) |
| model_id | string | Filter by device model |
| search | string | Full-text search on name and serial_number |
| page | integer | Page number, default 1 |
| limit | integer | Page size, 1–100, default 50 |
| sort | string | Field and direction: `created_at:desc`, `name:asc`, `status:asc` |
| tags | string | Tag filter, format `key:value`, repeatable |

**Response — 200 OK:**
```json
{
  "data": [
    {
      "device_id": "dev-01HXYZ789",
      "serial_number": "SN-20241115-00042",
      "name": "Warehouse Temp Sensor 42",
      "status": "ACTIVE",
      "device_model_id": "mdl-rpi4-sensor-v2",
      "group_id": "grp-warehouse-floor-a",
      "last_seen_at": "2024-11-15T11:58:30Z",
      "firmware_version": "2.1.4",
      "created_at": "2024-11-15T10:00:00Z"
    }
  ],
  "meta": { "requestId": "req_01HXYZ002", "timestamp": "2024-11-15T12:00:05Z", "page": 1, "limit": 50, "total": 1247 },
  "errors": []
}
```

---

### Get Device Details

**GET /devices/{deviceId}**

Required scope: `devices:read`

**Response — 200 OK:**
```json
{
  "data": {
    "device_id": "dev-01HXYZ789",
    "serial_number": "SN-20241115-00042",
    "name": "Warehouse Temp Sensor 42",
    "status": "ACTIVE",
    "device_model_id": "mdl-rpi4-sensor-v2",
    "group_id": "grp-warehouse-floor-a",
    "org_id": "org-acme-corp",
    "provisioning_method": "x509",
    "tags": { "location": "rack-12-slot-4", "environment": "production" },
    "metadata": { "manufacturer_batch": "2024-Q3", "hardware_revision": "1.2" },
    "firmware_version": "2.1.4",
    "connectivity": { "protocol": "mqttv5", "ip_address": "10.0.4.23", "connected": true },
    "last_seen_at": "2024-11-15T11:58:30Z",
    "created_at": "2024-11-15T10:00:00Z",
    "updated_at": "2024-11-15T11:00:00Z"
  }
}
```

---

### Update Device

**PATCH /devices/{deviceId}**

Required scope: `devices:write`

**Request Body (all fields optional):**
```json
{
  "name": "Warehouse Temp Sensor 42 - Relocated",
  "group_id": "grp-warehouse-floor-b",
  "tags": { "location": "rack-01-slot-2" },
  "status": "INACTIVE"
}
```

**Status codes:** 200 OK, 400 VALIDATION_ERROR, 404 DEVICE_NOT_FOUND, 410 DEVICE_DECOMMISSIONED

---

### Decommission Device

**DELETE /devices/{deviceId}**

Required scope: `devices:delete`

Permanently marks device as `DECOMMISSIONED`. All active certificates are revoked. The device is excluded from future OTA deployments and command queues. Telemetry history is retained per data retention policy. This action is irreversible.

**Response — 204 No Content**

**Status codes:** 204 No Content, 404 DEVICE_NOT_FOUND, 409 (active OTA job in progress — complete or cancel first)

---

### Get Device Shadow

**GET /devices/{deviceId}/shadow**

Required scope: `devices:read`

**Response — 200 OK:**
```json
{
  "data": {
    "device_id": "dev-01HXYZ789",
    "version": 42,
    "desired": {
      "reporting_interval_seconds": 30,
      "threshold_temp_celsius": 75.0
    },
    "reported": {
      "reporting_interval_seconds": 30,
      "threshold_temp_celsius": 72.5,
      "firmware_version": "2.1.4"
    },
    "delta": {
      "threshold_temp_celsius": 75.0
    },
    "updated_at": "2024-11-15T11:55:00Z"
  }
}
```

---

### Update Shadow Desired State

**PATCH /devices/{deviceId}/shadow/desired**

Required scope: `devices:write`

Performs a partial merge into the desired state. Provide the `version` field for optimistic concurrency control.

**Request Body:**
```json
{
  "version": 42,
  "desired": {
    "reporting_interval_seconds": 60
  }
}
```

**Response — 200 OK:** Returns updated shadow (version incremented to 43).

**Status codes:** 200 OK, 400 SHADOW_VERSION_CONFLICT, 404 DEVICE_NOT_FOUND

---

### Query Device Telemetry

**GET /devices/{deviceId}/telemetry**

Required scope: `telemetry:read`

**Query Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| metric | string | Yes | Metric name, e.g. `temperature`, `humidity` |
| start | ISO 8601 | Yes | Start of time range |
| end | ISO 8601 | Yes | End of time range. Max range 30 days |
| aggregation | enum | No | `mean`, `max`, `min`, `sum`, `count`. Raw if omitted |
| interval | string | No | Aggregation interval: `1m`, `5m`, `1h`, `1d` |

**Response — 200 OK:**
```json
{
  "data": {
    "device_id": "dev-01HXYZ789",
    "metric": "temperature",
    "unit": "celsius",
    "points": [
      { "timestamp": "2024-11-15T11:00:00Z", "value": 21.4 },
      { "timestamp": "2024-11-15T11:05:00Z", "value": 21.6 }
    ]
  },
  "meta": { "requestId": "req_01HXYZ010", "timestamp": "2024-11-15T12:00:00Z" }
}
```

---

### Dispatch Command to Device

**POST /devices/{deviceId}/commands**

Required scope: `commands:write`

Commands are delivered to online devices immediately. For offline devices, the command is queued (Redis list, TTL = `ttl_seconds`) and delivered on reconnect.

**Request Body:**
```json
{
  "command_type": "REBOOT",
  "payload": {
    "delay_seconds": 10,
    "reason": "scheduled-maintenance"
  },
  "ttl_seconds": 3600
}
```

**Response — 202 Accepted:**
```json
{
  "data": {
    "command_id": "cmd-01HXYZ999",
    "device_id": "dev-01HXYZ789",
    "command_type": "REBOOT",
    "status": "QUEUED",
    "ttl_seconds": 3600,
    "expires_at": "2024-11-15T13:00:00Z",
    "created_at": "2024-11-15T12:00:00Z"
  }
}
```

---

## Fleet Management

### Create Device Group

**POST /groups**

Required scope: `groups:write`

```json
{
  "name": "Warehouse Floor A",
  "parent_group_id": "grp-warehouse",
  "description": "All sensors on warehouse floor A",
  "metadata": {}
}
```

**Response — 201 Created:** Returns group object with `group_id`, `path` (e.g. `/org-root/warehouse/floor-a`), `depth` (1–5), `device_count: 0`.

---

### List Groups

**GET /groups**

Query params: `parent_group_id`, `search`, `page`, `limit`. Returns flat list of groups the caller has access to. Use `parent_group_id=root` to fetch top-level groups.

---

### Get Group Details

**GET /groups/{groupId}**

Returns group metadata, `device_count`, `child_group_count`, and full path string.

---

### List Devices in Group

**GET /groups/{groupId}/devices**

Same query parameters as `GET /devices`. Optionally include `include_descendants=true` to include devices in all child groups.

---

### Add Device to Group

**POST /groups/{groupId}/devices/{deviceId}**

No request body. Moves device to this group (a device belongs to exactly one group at a time).

**Response — 204 No Content**

---

### Remove Device from Group

**DELETE /groups/{groupId}/devices/{deviceId}**

Removes device from group; device is placed in the organization root group.

**Response — 204 No Content**

---

## OTA Firmware Management

### Upload Firmware Version

**POST /firmware**

Required scope: `firmware:write`

Multipart form data upload:

| Field | Type | Description |
|---|---|---|
| file | binary | Firmware binary, max 512 MB |
| version | string | Semantic version, e.g. `2.2.0` |
| device_model_id | string | Target device model |
| changelog | string | Human-readable release notes |
| signing_key_id | string | ID of the signing key to use for firmware signature |
| min_device_firmware | string | Minimum current firmware version for upgrade eligibility |
| checksum_sha256 | string | Expected SHA256 of the binary (hex) |

**Response — 201 Created:**
```json
{
  "data": {
    "firmware_id": "fw-01HABC123",
    "version": "2.2.0",
    "device_model_id": "mdl-rpi4-sensor-v2",
    "file_size_bytes": 8388608,
    "checksum_sha256": "a3b4c5...",
    "signature_status": "VERIFIED",
    "status": "AVAILABLE",
    "changelog": "Bug fixes and performance improvements",
    "created_at": "2024-11-15T12:00:00Z"
  }
}
```

---

### Create OTA Deployment

**POST /ota/deployments**

Required scope: `ota:write`

**Request Body:**
```json
{
  "firmware_version_id": "fw-01HABC123",
  "target_group_id": "grp-warehouse-floor-a",
  "strategy": "canary",
  "canary_percentage": 5,
  "wave_size": 50,
  "auto_rollback": true,
  "rollback_threshold_failure_pct": 10,
  "canary_success_rate_threshold_pct": 95,
  "canary_evaluation_window_minutes": 30,
  "scheduled_at": "2024-11-16T02:00:00Z",
  "notification_webhook_url": "https://hooks.example.com/ota-updates"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| firmware_version_id | string | Yes | Must be in AVAILABLE status |
| target_group_id | string | Yes | All eligible devices in this group (and descendants if configured) |
| strategy | enum | Yes | `immediate`, `canary`, `scheduled` |
| canary_percentage | integer | For canary | % of devices in first wave, 1–20 |
| wave_size | integer | No | Devices per progressive wave after canary, default 50 |
| auto_rollback | boolean | No | Automatically roll back if failure threshold exceeded |
| rollback_threshold_failure_pct | integer | No | Failure % that triggers auto-rollback, default 10 |
| canary_success_rate_threshold_pct | integer | No | Success % required to advance beyond canary, default 95 |
| canary_evaluation_window_minutes | integer | No | How long to observe canary before advancing, default 30 |
| scheduled_at | ISO 8601 | For scheduled | Deployment start time (UTC) |

**Response — 202 Accepted:** Returns deployment object with `deployment_id`, `status: SCHEDULED`, `device_count`, wave breakdown.

---

### Get Deployment Status

**GET /ota/deployments/{deploymentId}**

```json
{
  "data": {
    "deployment_id": "dep-01HDEF456",
    "firmware_version_id": "fw-01HABC123",
    "target_group_id": "grp-warehouse-floor-a",
    "strategy": "canary",
    "status": "IN_PROGRESS",
    "wave_current": 2,
    "wave_total": 6,
    "device_count": 300,
    "progress": {
      "pending": 200,
      "downloading": 15,
      "applying": 5,
      "success": 75,
      "failed": 5
    },
    "success_rate_pct": 93.75,
    "started_at": "2024-11-16T02:00:00Z",
    "estimated_completion_at": "2024-11-16T03:45:00Z"
  }
}
```

---

### Cancel Deployment

**POST /ota/deployments/{deploymentId}/cancel**

No request body. Stops issuing new jobs; devices already in DOWNLOADING or APPLYING states are allowed to complete or fail naturally.

**Response — 202 Accepted**

---

### Trigger Manual Rollback

**POST /ota/deployments/{deploymentId}/rollback**

```json
{
  "reason": "High error rate observed in monitoring dashboard",
  "target_scope": "all_updated"
}
```

`target_scope` options: `all_updated` (reverts all devices that applied the new firmware), `failed_only` (targets only devices in FAILED state).

**Response — 202 Accepted**

---

## Alert Rules

### Create Alert Rule

**POST /alert-rules**

Required scope: `rules:write`

```json
{
  "name": "High Temperature Alert",
  "device_group_id": "grp-warehouse-floor-a",
  "metric_name": "temperature",
  "condition_type": "threshold",
  "operator": "gt",
  "threshold_value": 80.0,
  "window_seconds": 0,
  "severity": "critical",
  "cooldown_seconds": 900,
  "notification_channels": [
    { "type": "email", "target": "ops-team@acme.com" },
    { "type": "webhook", "target": "https://hooks.example.com/alerts" },
    { "type": "sms", "target": "+15551234567" }
  ]
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| name | string | Yes | Display name |
| device_group_id | string | Yes | Scope of rule evaluation |
| metric_name | string | Yes | Metric field name in telemetry payload |
| condition_type | enum | Yes | `threshold`, `window_avg`, `window_max`, `rate_of_change`, `anomaly` |
| operator | enum | Threshold | `gt`, `lt`, `gte`, `lte`, `eq`, `neq` |
| threshold_value | number/string | Threshold | Comparison value |
| window_seconds | integer | Window rules | Evaluation window duration |
| severity | enum | Yes | `info`, `warning`, `critical` |
| cooldown_seconds | integer | Yes | Minimum seconds between consecutive alert fires for same device |
| notification_channels | array | Yes | At least one channel required |

**Response — 201 Created:** Returns rule with `rule_id`, `status: ACTIVE`.

---

### Acknowledge Alert

**PATCH /alerts/{alertId}**

```json
{
  "action": "acknowledge",
  "comment": "Investigating — likely sensor calibration drift"
}
```

`action` options: `acknowledge`, `resolve`. Acknowledged alerts remain open; resolved alerts are closed.

**Response — 200 OK**

---

## Certificate Management

### Issue Certificate for Device

**POST /devices/{deviceId}/certificates**

Required scope: `certificates:write`

```json
{
  "validity_days": 365,
  "key_algorithm": "EC_P256"
}
```

Returns the signed PEM certificate and private key. **The private key is only returned once.**

**Response — 201 Created:**
```json
{
  "data": {
    "certificate_id": "cert-01HXYZ555",
    "device_id": "dev-01HXYZ789",
    "pem": "-----BEGIN CERTIFICATE-----\nMIIB...",
    "private_key_pem": "-----BEGIN EC PRIVATE KEY-----\nMHQ...",
    "fingerprint_sha256": "AA:BB:CC:...",
    "key_algorithm": "EC_P256",
    "issued_at": "2024-11-15T12:00:00Z",
    "expires_at": "2025-11-15T12:00:00Z",
    "status": "ACTIVE"
  }
}
```

---

### Revoke Certificate

**DELETE /devices/{deviceId}/certificates/{certId}**

```json
{
  "revocation_reason": "KEY_COMPROMISE"
}
```

`revocation_reason` options (RFC 5280 CRL reasons): `UNSPECIFIED`, `KEY_COMPROMISE`, `CA_COMPROMISE`, `AFFILIATION_CHANGED`, `SUPERSEDED`, `CESSATION_OF_OPERATION`.

Certificate is added to the OCSP responder's revocation list and the EMQX ACL is updated within 30 seconds via Kafka event.

**Response — 204 No Content**

---

## MQTT API

### Connection Parameters

```
Host:       mqtt.iotplatform.example.com
Port:       8883 (TLS 1.3, X.509 mTLS)
Port:       8084 (WebSocket/TLS)
Client ID:  {deviceId}   (must match CN in client certificate)
Clean Session: false (MQTT 3.1.1) | Session Expiry Interval: 86400 (MQTT 5.0)
Keep Alive: 60 seconds
```

**Last Will and Testament (LWT) — configured at CONNECT:**
```
Topic:   devices/{deviceId}/events
Payload: {"event_type":"DISCONNECT","reason":"unexpected","timestamp":""}
QoS:     1
Retain:  true
```

The platform uses the retained LWT message to detect unexpected disconnects and update device `last_seen_at` and connectivity status.

---

### Device-Published Topics

#### Telemetry — Single Point

**Topic:** `devices/{deviceId}/telemetry`
**QoS:** 1 (at-least-once)
**Direction:** Device → Platform

```json
{
  "ts": "2024-11-15T12:00:00.000Z",
  "metrics": {
    "temperature": 21.4,
    "humidity": 58.2,
    "pressure_pa": 101325
  },
  "seq": 1042
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| ts | ISO 8601 | Yes | Device-side timestamp (UTC) |
| metrics | object | Yes | Key/value metric readings |
| seq | integer | No | Sequence number for gap detection |

#### Telemetry — Batch

**Topic:** `devices/{deviceId}/telemetry/batch`
**QoS:** 1
**Max batch size:** 500 points per message

```json
{
  "points": [
    { "ts": "2024-11-15T11:59:30Z", "metrics": { "temperature": 21.2 }, "seq": 1040 },
    { "ts": "2024-11-15T11:59:45Z", "metrics": { "temperature": 21.3 }, "seq": 1041 },
    { "ts": "2024-11-15T12:00:00Z", "metrics": { "temperature": 21.4 }, "seq": 1042 }
  ]
}
```

#### Shadow Reported State Update

**Topic:** `devices/{deviceId}/shadow/update/reported`
**QoS:** 1

```json
{
  "state": {
    "reporting_interval_seconds": 30,
    "firmware_version": "2.1.4",
    "threshold_temp_celsius": 72.5
  }
}
```

#### Command Acknowledgment

**Topic:** `devices/{deviceId}/commands/ack`
**QoS:** 1

```json
{
  "command_id": "cmd-01HXYZ999",
  "status": "SUCCESS",
  "result": { "reboot_time_ms": 4250 },
  "error": null,
  "ts": "2024-11-15T12:00:10Z"
}
```

`status` values: `SUCCESS`, `FAILURE`, `TIMEOUT`, `REJECTED`

#### OTA Progress Report

**Topic:** `devices/{deviceId}/ota/progress`
**QoS:** 1

```json
{
  "job_id": "otajob-01HXYZ888",
  "deployment_id": "dep-01HDEF456",
  "firmware_version": "2.2.0",
  "status": "DOWNLOADING",
  "progress_pct": 45,
  "bytes_received": 3774873,
  "bytes_total": 8388608,
  "ts": "2024-11-15T12:01:00Z"
}
```

`status` values: `DOWNLOADING`, `VERIFYING`, `APPLYING`, `SUCCESS`, `FAILED`, `ROLLED_BACK`

#### Device Events

**Topic:** `devices/{deviceId}/events`
**QoS:** 1

```json
{
  "event_type": "REBOOT",
  "reason": "watchdog_reset",
  "firmware_version": "2.1.4",
  "uptime_seconds": 86412,
  "ts": "2024-11-15T12:00:00Z"
}
```

`event_type` values: `BOOT`, `REBOOT`, `DISCONNECT`, `ERROR`, `CONFIG_APPLIED`, `OTA_STARTED`, `OTA_COMPLETED`

---

### Platform-Published Topics (Device Subscribes)

#### Command Dispatch

**Topic:** `devices/{deviceId}/commands/{commandId}`
**QoS:** 1 (guaranteed delivery)

```json
{
  "command_id": "cmd-01HXYZ999",
  "command_type": "REBOOT",
  "payload": { "delay_seconds": 10, "reason": "scheduled-maintenance" },
  "ttl_seconds": 3600,
  "issued_at": "2024-11-15T12:00:00Z",
  "expires_at": "2024-11-15T13:00:00Z"
}
```

Devices must publish an `ack` to `devices/{deviceId}/commands/ack` within `ttl_seconds`. Commands not acknowledged before `expires_at` are marked `TIMEOUT`.

#### Shadow Desired State Delta

**Topic:** `devices/{deviceId}/shadow/update/desired`
**QoS:** 1
**Retained:** true (last desired state is always available on reconnect)

```json
{
  "version": 43,
  "state": {
    "reporting_interval_seconds": 60
  }
}
```

#### OTA Job Notification

**Topic:** `devices/{deviceId}/ota/job`
**QoS:** 1

```json
{
  "job_id": "otajob-01HXYZ888",
  "deployment_id": "dep-01HDEF456",
  "firmware_version": "2.2.0",
  "download_url": "https://firmware.iotplatform.example.com/fw-01HABC123?X-Amz-Expires=3600&X-Amz-Signature=...",
  "checksum_sha256": "a3b4c5...",
  "file_size_bytes": 8388608,
  "min_free_space_bytes": 20971520,
  "issued_at": "2024-11-15T12:00:00Z",
  "expires_at": "2024-11-15T18:00:00Z"
}
```

`download_url` is a MinIO/S3 pre-signed URL valid for 6 hours. Device must verify the SHA256 checksum after download.

#### Configuration Push

**Topic:** `devices/{deviceId}/config`
**QoS:** 1
**Retained:** true

```json
{
  "version": "v12",
  "config": {
    "mqtt_keepalive_seconds": 60,
    "telemetry_topics": ["devices/{deviceId}/telemetry"],
    "log_level": "WARNING"
  },
  "pushed_at": "2024-11-15T12:00:00Z"
}
```

---

## WebSocket Streaming API

### Connection

```
wss://ws.iotplatform.example.com/v1/stream?token=<jwt>
```

The JWT must have scope `stream:read`. The connection is authenticated on upgrade. Unauthenticated upgrades receive `401` and the WebSocket handshake is rejected.

### Subscribe to Telemetry Stream

**Client → Server:**
```json
{
  "action": "subscribe",
  "channel": "telemetry",
  "filters": {
    "device_ids": ["dev-01HXYZ789", "dev-01HXYZ790"],
    "metrics": ["temperature", "humidity"],
    "group_id": "grp-warehouse-floor-a"
  },
  "subscription_id": "sub-001"
}
```

**Server → Client (stream messages):**
```json
{
  "subscription_id": "sub-001",
  "channel": "telemetry",
  "device_id": "dev-01HXYZ789",
  "ts": "2024-11-15T12:00:00Z",
  "metrics": { "temperature": 21.4 }
}
```

### Subscribe to Alert Events Stream

```json
{
  "action": "subscribe",
  "channel": "alerts",
  "filters": {
    "severity": ["critical", "warning"],
    "group_id": "grp-warehouse-floor-a"
  },
  "subscription_id": "sub-002"
}
```

### Unsubscribe

```json
{
  "action": "unsubscribe",
  "subscription_id": "sub-001"
}
```

### Heartbeat / Ping

Server sends a ping frame every 30 seconds. Clients must respond with pong within 10 seconds or the connection is closed. Clients may also send:

```json
{ "action": "ping", "ts": "2024-11-15T12:00:00Z" }
```

Server responds:
```json
{ "action": "pong", "ts": "2024-11-15T12:00:00Z" }
```

### Message Envelope

All server-pushed messages follow this envelope:

```json
{
  "subscription_id": "sub-001",
  "channel": "telemetry",
  "event_id": "evt-01HXYZ456",
  "ts": "2024-11-15T12:00:00Z",
  "payload": {}
}
```

Connection limit: 1000 concurrent subscriptions per organization. Each subscription may filter up to 100 device IDs.

---

## SDK Endpoints

These endpoints are intended for SDK clients and third-party integrations. They require API key authentication via the `X-API-Key` header.

### Exchange API Key for JWT

**POST /sdk/token**

```json
{
  "api_key": "sk-live-xxxxxxxxxxxxxxxxxxxxxxxx"
}
```

**Response — 200 OK:**
```json
{
  "data": {
    "access_token": "<jwt>",
    "token_type": "Bearer",
    "expires_in": 900,
    "scopes": ["devices:read", "telemetry:read"]
  }
}
```

JWT lifetime: 15 minutes. API key does not expire but can be rotated or revoked. Use the returned JWT for subsequent REST calls.

---

### Query Device Metrics (Simplified)

**GET /sdk/devices/{deviceId}/metrics**

Query params: `metric`, `start`, `end`. Returns a flat array of `{ts, value}` objects without the full response envelope. Designed for embedded use in SDK helper methods.

**Response — 200 OK:**
```json
[
  { "ts": "2024-11-15T11:00:00Z", "value": 21.4 },
  { "ts": "2024-11-15T11:05:00Z", "value": 21.6 }
]
```

---

### Register Webhook

**POST /sdk/webhooks**

```json
{
  "url": "https://your-backend.example.com/iot-events",
  "events": ["device.status_changed", "alert.fired", "ota.deployment_completed"],
  "secret": "whsec_xxxxxxxx"
}
```

The platform signs every webhook payload with HMAC-SHA256 using the provided `secret`. The signature is included in the `X-Platform-Signature` header:

```
X-Platform-Signature: sha256=<hex-digest>
```

**Response — 201 Created:**
```json
{
  "data": {
    "webhook_id": "wh-01HXYZ111",
    "url": "https://your-backend.example.com/iot-events",
    "events": ["device.status_changed", "alert.fired", "ota.deployment_completed"],
    "status": "ACTIVE",
    "created_at": "2024-11-15T12:00:00Z"
  }
}
```

---

### List Webhooks

**GET /sdk/webhooks**

Returns all registered webhooks for the organization with their delivery statistics (last 24h: attempted, succeeded, failed).

---

### Delete Webhook

**DELETE /sdk/webhooks/{webhookId}**

**Response — 204 No Content**

---

## Pagination

All list endpoints support cursor-based pagination for large result sets. Include `cursor` (returned as `meta.next_cursor` in the previous response) instead of `page` for stable pagination across large datasets:

```
GET /devices?cursor=eyJpZCI6ImRldi0wMUhYWVo3ODkiLCJkaXIiOiJuZXh0In0=&limit=50
```

Page-based pagination (`page` + `limit`) is also supported and is the default for compatibility.

---

## Request Tracing

Every request receives a unique `X-Request-ID` header in the response (generated by Kong if not provided by the caller). Callers may send their own `X-Request-ID` to correlate requests across systems. This ID propagates through all downstream service calls via HTTP headers and Kafka message headers, enabling end-to-end distributed tracing (Jaeger/OpenTelemetry).
