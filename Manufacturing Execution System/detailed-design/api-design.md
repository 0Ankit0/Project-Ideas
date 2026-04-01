# API Design — Manufacturing Execution System

## Overview

This document specifies the REST API surface of the Manufacturing Execution System. All endpoints are versioned under `/api/v1`, authenticated via OAuth 2.0 Bearer tokens (Keycloak), and return JSON. The API is exposed through a Kong API Gateway that enforces authentication, rate limiting, and request logging before proxying to individual microservices.

Base URL (production): `https://mes.factory.example.com`

---

## API Principles

- **Resource-oriented design** — URIs represent domain resources; HTTP verbs express intent.
- **Versioning** — Path-based versioning (`/api/v1/`). Breaking changes introduce `/api/v2/`.
- **Idempotency** — `PUT` and `PATCH` are idempotent. `POST` operations accept a client-supplied `Idempotency-Key` header where natural idempotency is not guaranteed.
- **Pagination** — Collection endpoints use cursor-based pagination via `after` and `limit` query parameters. Responses include `meta.nextCursor`.
- **Partial updates** — `PATCH` uses JSON Merge Patch (RFC 7396).
- **Timestamps** — All timestamps are ISO 8601 UTC strings (e.g., `2024-03-15T08:30:00Z`).
- **Envelopes** — Successful responses wrap data in `{ "data": … }`. Error responses use `{ "error": { "code": …, "message": …, "details": […] } }`.

---

## Authentication and Authorization

All API requests must include a valid JWT Bearer token obtained from Keycloak.

```
Authorization: Bearer <access_token>
```

### Scopes and Roles

| Role               | Scopes Granted                                                  |
|--------------------|-----------------------------------------------------------------|
| `operator`         | `orders:read`, `work-centers:read`, `materials:write`           |
| `quality-engineer` | `quality:read`, `quality:write`, `orders:read`                  |
| `planner`          | `orders:write`, `schedules:write`, `work-centers:read`          |
| `maintenance`      | `work-centers:write`, `telemetry:read`                          |
| `mes-admin`        | All scopes                                                      |
| `erp-integration`  | `orders:write`, `materials:write`, `erp:sync`                   |

### Token Endpoint

```
POST /auth/realms/mes/protocol/openid-connect/token
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials&client_id=mes-client&client_secret=<secret>
```

---

## Production Orders API

### POST /api/v1/production-orders

**Description:** Creates a new production order from a planner-initiated or ERP-synced request.

**Required Scope:** `orders:write`

**Request Body:**
```json
{
  "externalOrderId": "SAP-MO-100042",
  "productCode": "FG-AXLE-200",
  "productDescription": "Front Drive Axle 200mm",
  "plannedQuantity": 150,
  "unit": "EA",
  "scheduledStartDate": "2024-03-20T06:00:00Z",
  "scheduledEndDate": "2024-03-20T22:00:00Z",
  "priority": 2,
  "routingId": "ROUTING-AXLE-V3",
  "bomId": "BOM-AXLE-200-R5",
  "workCenterId": "WC-LATHE-04",
  "notes": "Customer order CO-8821, expedite"
}
```

**Response `201 Created`:**
```json
{
  "data": {
    "id": "po-c3a1b2d4-e5f6-7890-abcd-ef1234567890",
    "externalOrderId": "SAP-MO-100042",
    "productCode": "FG-AXLE-200",
    "plannedQuantity": 150,
    "confirmedQuantity": 0,
    "scrapQuantity": 0,
    "status": "CREATED",
    "priority": 2,
    "routingId": "ROUTING-AXLE-V3",
    "workCenterId": "WC-LATHE-04",
    "scheduledStartDate": "2024-03-20T06:00:00Z",
    "scheduledEndDate": "2024-03-20T22:00:00Z",
    "createdAt": "2024-03-15T09:12:00Z",
    "updatedAt": "2024-03-15T09:12:00Z"
  }
}
```

**Errors:**

| HTTP Status | Code                       | Description                                       |
|-------------|----------------------------|---------------------------------------------------|
| 400         | `INVALID_ROUTING`          | Routing ID does not exist                         |
| 400         | `INVALID_WORK_CENTER`      | Work center ID does not exist                     |
| 409         | `DUPLICATE_EXTERNAL_ORDER` | `externalOrderId` already exists                  |
| 422         | `INVALID_DATE_RANGE`       | `scheduledEndDate` is before `scheduledStartDate` |

---

### GET /api/v1/production-orders

**Description:** Lists production orders with optional filtering by status, work center, or date range.

**Required Scope:** `orders:read`

**Query Parameters:**

| Parameter      | Type     | Description                                                                    |
|----------------|----------|--------------------------------------------------------------------------------|
| `status`       | string   | Filter: `CREATED`, `RELEASED`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`        |
| `workCenterId` | string   | Filter by work center                                                          |
| `from`         | ISO 8601 | Start of scheduled date range                                                  |
| `to`           | ISO 8601 | End of scheduled date range                                                    |
| `limit`        | integer  | Max results per page (default 50, max 200)                                     |
| `after`        | string   | Cursor for next page                                                           |

**Response `200 OK`:**
```json
{
  "data": [
    {
      "id": "po-c3a1b2d4-...",
      "externalOrderId": "SAP-MO-100042",
      "productCode": "FG-AXLE-200",
      "status": "IN_PROGRESS",
      "plannedQuantity": 150,
      "confirmedQuantity": 72,
      "scheduledStartDate": "2024-03-20T06:00:00Z",
      "workCenterId": "WC-LATHE-04"
    }
  ],
  "meta": { "count": 1, "nextCursor": null }
}
```

---

### PATCH /api/v1/production-orders/{id}/status

**Description:** Transitions a production order through its lifecycle states.

**Required Scope:** `orders:write`

**Request Body:**
```json
{
  "status": "RELEASED",
  "reason": "Material confirmed available by warehouse"
}
```

**Valid Transitions:**

| From          | To            |
|---------------|---------------|
| `CREATED`     | `RELEASED`    |
| `RELEASED`    | `IN_PROGRESS` |
| `IN_PROGRESS` | `COMPLETED`   |
| `CREATED`     | `CANCELLED`   |
| `RELEASED`    | `CANCELLED`   |

**Response `200 OK`:** Returns the updated production order object.

**Errors:**

| HTTP Status | Code                 | Description                        |
|-------------|----------------------|------------------------------------|
| 404         | `ORDER_NOT_FOUND`    | Production order ID not found      |
| 422         | `INVALID_TRANSITION` | Status transition is not permitted |

---

## Work Centers API

### GET /api/v1/work-centers

**Description:** Returns all configured work centers with their current availability state.

**Required Scope:** `work-centers:read`

**Response `200 OK`:**
```json
{
  "data": [
    {
      "id": "WC-LATHE-04",
      "name": "CNC Lathe Line 4",
      "type": "MACHINE",
      "department": "MACHINING",
      "capacityUnit": "HOURS",
      "dailyCapacityHours": 20.0,
      "currentState": "RUNNING",
      "currentOrderId": "po-c3a1b2d4-...",
      "oeeLastShift": 0.782,
      "updatedAt": "2024-03-20T09:45:00Z"
    }
  ]
}
```

---

### GET /api/v1/work-centers/{id}/capacity

**Description:** Returns capacity availability windows for a work center over a specified date range, accounting for shift calendars and planned downtime.

**Required Scope:** `work-centers:read`

**Query Parameters:** `from` (ISO 8601), `to` (ISO 8601)

**Response `200 OK`:**
```json
{
  "data": {
    "workCenterId": "WC-LATHE-04",
    "from": "2024-03-20T00:00:00Z",
    "to": "2024-03-22T23:59:59Z",
    "slots": [
      {
        "date": "2024-03-20",
        "shift": "MORNING",
        "availableHours": 7.5,
        "allocatedHours": 6.0,
        "remainingHours": 1.5
      }
    ]
  }
}
```

---

### PATCH /api/v1/work-centers/{id}/state

**Description:** Manually overrides the state of a work center (e.g., planned downtime, shift change).

**Required Scope:** `work-centers:write`

**Request Body:**
```json
{
  "state": "PLANNED_DOWNTIME",
  "reason": "Preventive maintenance PM-2024-03-20",
  "expectedResumptionAt": "2024-03-20T12:00:00Z"
}
```

**Response `200 OK`:** Returns updated work center object.

**Errors:**

| HTTP Status | Code                    | Description                               |
|-------------|-------------------------|-------------------------------------------|
| 404         | `WORK_CENTER_NOT_FOUND` | Work center ID not found                  |
| 422         | `INVALID_STATE`         | Requested state is not a valid enum value |

---

## Operations API

### POST /api/v1/operations/start

**Description:** Signals the start of an operation at a work center against a production order routing step.

**Required Scope:** `orders:write`

**Request Body:**
```json
{
  "productionOrderId": "po-c3a1b2d4-...",
  "operationId": "OP-030-TURNING",
  "workCenterId": "WC-LATHE-04",
  "operatorId": "op-user-7712",
  "actualStartTime": "2024-03-20T06:05:00Z"
}
```

**Response `201 Created`:**
```json
{
  "data": {
    "operationExecutionId": "oe-aa11bb22-...",
    "productionOrderId": "po-c3a1b2d4-...",
    "operationId": "OP-030-TURNING",
    "status": "IN_PROGRESS",
    "actualStartTime": "2024-03-20T06:05:00Z"
  }
}
```

---

### POST /api/v1/operations/complete

**Description:** Records completion of an operation, including quantity produced and scrap.

**Required Scope:** `orders:write`

**Request Body:**
```json
{
  "operationExecutionId": "oe-aa11bb22-...",
  "actualEndTime": "2024-03-20T14:30:00Z",
  "confirmedQuantity": 148,
  "scrapQuantity": 2,
  "scrapReasonCode": "DIMENSION_OUT_OF_SPEC"
}
```

**Response `200 OK`:** Returns updated operation execution with duration and yield calculations.

---

### GET /api/v1/operations/{operationExecutionId}

**Description:** Retrieves the details of a specific operation execution record.

**Required Scope:** `orders:read`

**Response `200 OK`:**
```json
{
  "data": {
    "operationExecutionId": "oe-aa11bb22-...",
    "productionOrderId": "po-c3a1b2d4-...",
    "operationId": "OP-030-TURNING",
    "workCenterId": "WC-LATHE-04",
    "operatorId": "op-user-7712",
    "status": "COMPLETED",
    "actualStartTime": "2024-03-20T06:05:00Z",
    "actualEndTime": "2024-03-20T14:30:00Z",
    "durationMinutes": 505,
    "confirmedQuantity": 148,
    "scrapQuantity": 2,
    "yieldPercent": 98.67
  }
}
```

---

## Quality Management API

### POST /api/v1/inspections

**Description:** Creates an inspection record for a lot or serialised unit against an inspection plan.

**Required Scope:** `quality:write`

**Request Body:**
```json
{
  "productionOrderId": "po-c3a1b2d4-...",
  "inspectionPlanId": "IP-AXLE-200-V2",
  "lotId": "LOT-2024-0320-001",
  "inspectorId": "qe-user-3301",
  "sampleSize": 10,
  "measurements": [
    {
      "characteristicId": "DIA-OUTER",
      "values": [200.1, 200.0, 199.9, 200.2, 200.0, 199.8, 200.1, 200.3, 200.0, 199.9]
    },
    {
      "characteristicId": "SURFACE-ROUGHNESS",
      "values": [0.8, 0.9, 0.8, 0.7, 0.8, 0.9, 0.8, 0.8, 0.7, 0.9]
    }
  ]
}
```

**Response `201 Created`:**
```json
{
  "data": {
    "inspectionId": "insp-ff33ee44-...",
    "status": "ACCEPTED",
    "spcResults": [
      {
        "characteristicId": "DIA-OUTER",
        "mean": 200.03,
        "stdDev": 0.158,
        "cpk": 1.82,
        "inControl": true
      }
    ],
    "createdAt": "2024-03-20T10:15:00Z"
  }
}
```

---

### POST /api/v1/ncr

**Description:** Raises a Non-Conformance Report for a failed inspection or production defect.

**Required Scope:** `quality:write`

**Request Body:**
```json
{
  "inspectionId": "insp-ff33ee44-...",
  "defectCode": "DIM-OUTER-OOS",
  "severity": "MAJOR",
  "affectedLotId": "LOT-2024-0320-001",
  "affectedQuantity": 5,
  "dispositionRequest": "REWORK",
  "description": "Outer diameter exceeds upper control limit on CNC Lathe 4 post tool-change."
}
```

**Response `201 Created`:** Returns NCR object with auto-assigned NCR number and workflow state `OPEN`.

**Errors:**

| HTTP Status | Code                      | Description                                  |
|-------------|---------------------------|----------------------------------------------|
| 404         | `INSPECTION_NOT_FOUND`    | Inspection ID does not exist                 |
| 400         | `INVALID_DEFECT_CODE`     | Defect code not in quality catalogue         |
| 422         | `QUANTITY_EXCEEDS_SAMPLE` | Affected quantity exceeds inspection sample  |

---

### GET /api/v1/spc/control-charts/{characteristicId}

**Description:** Returns X-bar and R-chart data points for a quality characteristic over a time range.

**Required Scope:** `quality:read`

**Query Parameters:** `from`, `to`, `workCenterId` (optional)

**Response `200 OK`:**
```json
{
  "data": {
    "characteristicId": "DIA-OUTER",
    "ucl": 200.47,
    "lcl": 199.53,
    "centreLine": 200.0,
    "points": [
      {
        "subgroupId": "insp-ff33ee44-...",
        "mean": 200.03,
        "range": 0.5,
        "timestamp": "2024-03-20T10:15:00Z",
        "outOfControl": false
      }
    ]
  }
}
```

**Errors:**

| HTTP Status | Code                       | Description                                  |
|-------------|----------------------------|----------------------------------------------|
| 404         | `CHARACTERISTIC_NOT_FOUND` | Characteristic ID not configured             |
| 400         | `INSUFFICIENT_DATA`        | Fewer than 25 subgroups available for limits |

---

## Material Tracking API

### POST /api/v1/materials/consume

**Description:** Records material consumption from a lot against a production order operation.

**Required Scope:** `materials:write`

**Request Body:**
```json
{
  "productionOrderId": "po-c3a1b2d4-...",
  "operationId": "OP-030-TURNING",
  "consumptions": [
    {
      "lotId": "RM-LOT-20240319-042",
      "materialCode": "RM-BAR-STEEL-40",
      "quantity": 150,
      "unit": "KG"
    }
  ]
}
```

**Response `200 OK`:**
```json
{
  "data": {
    "transactionId": "mt-tx-66778899-...",
    "consumptions": [
      {
        "lotId": "RM-LOT-20240319-042",
        "materialCode": "RM-BAR-STEEL-40",
        "quantity": 150,
        "remainingStock": 350
      }
    ],
    "timestamp": "2024-03-20T06:10:00Z"
  }
}
```

**Errors:**

| HTTP Status | Code                   | Description                                   |
|-------------|------------------------|-----------------------------------------------|
| 404         | `LOT_NOT_FOUND`        | Material lot does not exist                   |
| 422         | `LOT_ON_HOLD`          | Lot is in HOLD status pending quality review  |
| 422         | `INSUFFICIENT_STOCK`   | Requested quantity exceeds remaining lot stock|

---

### GET /api/v1/materials/lots/{lotId}

**Description:** Retrieves full details and transaction history for a material lot.

**Required Scope:** `materials:read`

**Response `200 OK`:**
```json
{
  "data": {
    "lotId": "RM-LOT-20240319-042",
    "materialCode": "RM-BAR-STEEL-40",
    "supplierLotNumber": "SUP-2024-XB-01",
    "receivedDate": "2024-03-19T14:00:00Z",
    "quantity": 500,
    "remainingQuantity": 350,
    "unit": "KG",
    "status": "AVAILABLE",
    "qualityStatus": "APPROVED",
    "transactions": [
      {
        "type": "CONSUMPTION",
        "quantity": 150,
        "productionOrderId": "po-c3a1b2d4-...",
        "timestamp": "2024-03-20T06:10:00Z"
      }
    ]
  }
}
```

---

### GET /api/v1/materials/traceability/{serialNo}

**Description:** Returns the complete forward and backward traceability tree for a serialised finished good.

**Required Scope:** `materials:read`

**Response `200 OK`:**
```json
{
  "data": {
    "serialNo": "FG-AXLE-200-SN-00148",
    "productCode": "FG-AXLE-200",
    "productionOrderId": "po-c3a1b2d4-...",
    "producedAt": "2024-03-20T14:30:00Z",
    "componentLots": [
      {
        "materialCode": "RM-BAR-STEEL-40",
        "lotId": "RM-LOT-20240319-042",
        "quantity": 1,
        "unit": "EA"
      }
    ],
    "inspections": ["insp-ff33ee44-..."],
    "shipmentId": null
  }
}
```

---

## OEE API

### GET /api/v1/oee/{workCenterId}

**Description:** Returns OEE metrics for a work center for the current or specified shift.

**Required Scope:** `oee:read`

**Query Parameters:** `date` (ISO 8601 date), `shift` (`MORNING` | `AFTERNOON` | `NIGHT`)

**Response `200 OK`:**
```json
{
  "data": {
    "workCenterId": "WC-LATHE-04",
    "date": "2024-03-20",
    "shift": "MORNING",
    "plannedProductionTime": 450,
    "availability": {
      "uptime": 412,
      "downtime": 38,
      "value": 0.9156
    },
    "performance": {
      "idealCycleTime": 3.0,
      "totalPiecesRun": 118,
      "value": 0.861
    },
    "quality": {
      "totalPieces": 118,
      "goodPieces": 116,
      "value": 0.983
    },
    "oee": 0.775,
    "lossAnalysis": {
      "availabilityLossMin": 38,
      "performanceLossMin": 16.2,
      "qualityLossUnits": 2
    }
  }
}
```

---

### GET /api/v1/oee/trends

**Description:** Returns OEE trend data aggregated by day or week for one or more work centers.

**Required Scope:** `oee:read`

**Query Parameters:** `workCenterIds` (comma-separated), `from`, `to`, `granularity` (`DAY` | `WEEK`)

**Response `200 OK`:**
```json
{
  "data": [
    {
      "workCenterId": "WC-LATHE-04",
      "period": "2024-03-20",
      "oee": 0.775,
      "availability": 0.916,
      "performance": 0.861,
      "quality": 0.983
    }
  ]
}
```

---

### GET /api/v1/oee/losses/{workCenterId}

**Description:** Returns a Pareto-ranked list of downtime and speed loss reasons for a work center over a date range.

**Required Scope:** `oee:read`

**Response `200 OK`:**
```json
{
  "data": {
    "workCenterId": "WC-LATHE-04",
    "from": "2024-03-01",
    "to": "2024-03-20",
    "losses": [
      {
        "code": "TOOL_CHANGE",
        "description": "Unplanned tool change",
        "totalMinutes": 480,
        "occurrences": 24
      },
      {
        "code": "MATERIAL_WAIT",
        "description": "Waiting for material",
        "totalMinutes": 210,
        "occurrences": 10
      }
    ]
  }
}
```

---

## IoT / Telemetry API

### POST /api/v1/telemetry/ingest

**Description:** Accepts a batch of telemetry data points from edge gateways or SCADA adapters (HTTP fallback; primary path is Kafka).

**Required Scope:** `telemetry:write`

**Request Body:**
```json
{
  "assetId": "ASSET-WC-LATHE-04",
  "readings": [
    {
      "tag": "spindle_speed_rpm",
      "value": 1500.0,
      "quality": "GOOD",
      "timestamp": "2024-03-20T09:00:00Z"
    },
    {
      "tag": "spindle_load_percent",
      "value": 62.4,
      "quality": "GOOD",
      "timestamp": "2024-03-20T09:00:00Z"
    }
  ]
}
```

**Response `202 Accepted`:** Telemetry batch accepted for asynchronous processing.

**Errors:**

| HTTP Status | Code                  | Description                                     |
|-------------|-----------------------|-------------------------------------------------|
| 400         | `UNKNOWN_ASSET`       | `assetId` not registered in asset registry      |
| 413         | `BATCH_TOO_LARGE`     | Batch exceeds 1,000 readings per request        |
| 422         | `FUTURE_TIMESTAMP`    | One or more timestamps are more than 60s ahead  |

---

### GET /api/v1/telemetry/{assetId}

**Description:** Retrieves historical telemetry readings for a specific asset and tag, with time-based aggregation.

**Required Scope:** `telemetry:read`

**Query Parameters:** `tag`, `from`, `to`, `resolution` (`1m`, `5m`, `1h`)

**Response `200 OK`:**
```json
{
  "data": {
    "assetId": "ASSET-WC-LATHE-04",
    "tag": "spindle_speed_rpm",
    "resolution": "5m",
    "points": [
      {
        "timestamp": "2024-03-20T09:00:00Z",
        "avg": 1498.2,
        "min": 1450.0,
        "max": 1520.0
      }
    ]
  }
}
```

---

### GET /api/v1/telemetry/{assetId}/live (WebSocket)

**Description:** WebSocket endpoint that streams real-time telemetry for a specified asset. Clients send a subscription message with desired tags; the server pushes updates at 1-second intervals.

**Protocol:** `WSS`

**Subscribe Message:**
```json
{ "action": "subscribe", "tags": ["spindle_speed_rpm", "spindle_load_percent"] }
```

**Server Push Message:**
```json
{
  "assetId": "ASSET-WC-LATHE-04",
  "tag": "spindle_speed_rpm",
  "value": 1502.1,
  "timestamp": "2024-03-20T09:01:05Z"
}
```

---

## ERP Integration API

### POST /erp/inbound/production-orders

**Description:** Receives production order payloads from SAP S/4HANA via the ERP Integration Service. Triggers creation or update of production orders in the MES. Authenticated with mutual TLS in addition to Bearer token.

**Required Scope:** `erp:sync`

**Request Body:**
```json
{
  "sapMfgOrderNumber": "000001000042",
  "material": "FG-AXLE-200",
  "totalQuantity": 150,
  "unit": "EA",
  "basicStartDate": "2024-03-20",
  "basicFinishDate": "2024-03-20",
  "routingGroup": "50000123",
  "plant": "1010",
  "productionVersion": "0001"
}
```

**Response `202 Accepted`:** Order queued for MES upsert.

---

### POST /erp/outbound/confirmations

**Description:** Sends operation confirmations and goods movements back to SAP upon production order completion.

**Required Scope:** `erp:sync`

**Request Body:**
```json
{
  "sapMfgOrderNumber": "000001000042",
  "operationNumber": "0030",
  "confirmationQuantity": 148,
  "scrapQuantity": 2,
  "yieldUnit": "EA",
  "actualWorkHours": 8.4,
  "postingDate": "2024-03-20",
  "finalConfirmation": true
}
```

**Response `200 OK`:** SAP confirmation document number returned.

**Errors:**

| HTTP Status | Code                    | Description                                       |
|-------------|-------------------------|---------------------------------------------------|
| 404         | `ORDER_NOT_FOUND`       | SAP order number not found in MES                 |
| 409         | `ALREADY_CONFIRMED`     | Final confirmation already posted for this order  |
| 503         | `SAP_UNAVAILABLE`       | SAP RFC endpoint not reachable; retry with backoff|

---

### GET /erp/sync/status

**Description:** Returns the current status of the ERP integration sync job, including last successful sync timestamp and error queue depth.

**Required Scope:** `erp:sync`

**Response `200 OK`:**
```json
{
  "data": {
    "lastSyncAt": "2024-03-20T08:00:00Z",
    "pendingInbound": 0,
    "pendingOutbound": 3,
    "lastError": null,
    "status": "HEALTHY"
  }
}
```

---

## Error Handling

All error responses follow a standard envelope:

```json
{
  "error": {
    "code": "INVALID_ROUTING",
    "message": "Routing ID 'ROUTING-AXLE-V99' does not exist.",
    "traceId": "trace-abc123def456",
    "timestamp": "2024-03-20T09:12:00Z",
    "details": [
      { "field": "routingId", "issue": "Resource not found" }
    ]
  }
}
```

### Standard HTTP Status Codes

| Status | Usage                                                                 |
|--------|-----------------------------------------------------------------------|
| 200    | Successful GET, PATCH, PUT                                           |
| 201    | Resource created successfully (POST)                                  |
| 202    | Request accepted for asynchronous processing                          |
| 400    | Malformed request, invalid field values                               |
| 401    | Missing or invalid Bearer token                                       |
| 403    | Authenticated but insufficient scope                                  |
| 404    | Resource not found                                                    |
| 409    | Conflict — duplicate resource or state violation                      |
| 413    | Payload too large                                                     |
| 422    | Semantically invalid request (business rule violation)                |
| 429    | Rate limit exceeded                                                   |
| 500    | Unexpected server error (include `traceId` for support)               |
| 503    | Upstream dependency unavailable                                       |

---

## Rate Limiting and Throttling

Rate limits are enforced at the Kong API Gateway per client ID (derived from JWT `sub` claim).

| Client Type        | Requests / Minute | Burst Limit | Concurrent WebSocket Connections |
|--------------------|-------------------|-------------|----------------------------------|
| `operator`         | 300               | 50          | 5                                |
| `planner`          | 200               | 30          | 2                                |
| `quality-engineer` | 200               | 30          | 2                                |
| `erp-integration`  | 600               | 100         | N/A                              |
| `iot-gateway`      | 6,000             | 500         | 50                               |
| `mes-admin`        | 1,200             | 200         | 20                               |

When a rate limit is exceeded, the gateway returns:

```
HTTP 429 Too Many Requests
Retry-After: 15
X-RateLimit-Limit: 300
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1710925920
```

Telemetry batch ingest via `POST /api/v1/telemetry/ingest` is separately throttled at 1,000 readings per request and uses a dedicated high-throughput rate limit tier.

---

## API Versioning

### Strategy

Path-based versioning is used. The current stable version is `v1`. A new version (`v2`) is introduced only when a breaking change cannot be served via backward-compatible extension.

### Breaking vs. Non-Breaking Changes

| Change Type                                  | Breaking | Handling              |
|----------------------------------------------|----------|-----------------------|
| Adding optional request fields               | No       | Backward compatible   |
| Adding new response fields                   | No       | Clients must tolerate |
| Removing or renaming existing fields         | Yes      | New version required  |
| Changing field types                         | Yes      | New version required  |
| Changing HTTP status codes                   | Yes      | New version required  |
| Adding new endpoints                         | No       | Backward compatible   |
| Changing URI structure of existing endpoints | Yes      | New version required  |

### Lifecycle Policy

| Version | Status     | Sunset Date  |
|---------|------------|--------------|
| v1      | Active     | —            |
| v2      | Planned    | —            |

When a version is deprecated, a `Deprecation` header is added to all responses from that version:

```
Deprecation: true
Sunset: Sat, 01 Mar 2026 00:00:00 GMT
Link: <https://mes.factory.example.com/api/v2>; rel="successor-version"
```

Clients have a minimum 12-month migration window after deprecation before a version is decommissioned.
