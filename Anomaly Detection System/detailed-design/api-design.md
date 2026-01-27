# API Design - Anomaly Detection System

**Base URL**: `https://api.example.com/v1`  
**Auth**: Bearer Token (OAuth2/JWT)

---

## API Principles

- **Versioning**: URI versioning (`/v1`) with backwards-compatible changes only.
- **Idempotency**: `Idempotency-Key` supported for POST/PATCH endpoints.
- **Pagination**: Cursor-based pagination for large collections.
- **Correlation**: `X-Request-Id` echoed on all responses.

## Standard Headers

| Header | Description |
|--------|-------------|
| Authorization | Bearer token |
| Idempotency-Key | Client-generated UUID |
| X-Request-Id | Correlation id |
| X-Tenant-Id | Optional tenant scoping |

## Error Response Format

```json
{
  "type": "https://errors.example.com/invalid-data",
  "title": "Invalid data format",
  "status": 400,
  "detail": "Missing required field: values.cpu",
  "instance": "/v1/data",
  "requestId": "req-123"
}
```

---

## Push Data Point
**POST** `/data`

```json
{
  "sourceId": "server-01",
  "values": {"cpu": 85.5, "memory": 72.3},
  "timestamp": "2024-01-20T10:00:00Z",
  "metadata": {"region": "us-east"}
}
```

**Response**: `202 Accepted`
```json
{
  "dataPointId": "uuid",
  "anomalyScore": 0.92,
  "isAnomaly": true,
  "severity": "high"
}
```

---

## Register Data Source
**POST** `/sources`

```json
{
  "name": "prod-kafka-cpu",
  "type": "kafka",
  "schema": {
    "values.cpu": "number",
    "values.memory": "number"
  },
  "tags": ["prod", "infra"]
}
```

**Response**: `201 Created`

---

## List Data Sources
**GET** `/sources`

**Query Params**:
- `status`: active | disabled
- `cursor`: pagination cursor
- `limit`: int (default: 50)

---

## Get Anomalies
**GET** `/anomalies`

**Query Params**:
- `severity`: low | medium | high | critical
- `status`: detected | acknowledged | resolved
- `start`: ISO timestamp
- `end`: ISO timestamp
- `cursor`: pagination cursor
- `limit`: int (default: 100)

**Response**: `200 OK`
```json
{
  "anomalies": [
    {
      "id": "uuid",
      "sourceId": "server-01",
      "score": 0.92,
      "severity": "high",
      "detectedAt": "2024-01-20T10:00:00Z",
      "explanation": "CPU 3.5 std above normal"
    }
  ],
  "total": 150,
  "nextCursor": "cursor-abc"
}
```

---

## Get Alerts
**GET** `/alerts`

**Query Params**:
- `status`: open | acknowledged | resolved | suppressed
- `severity`: low | medium | high | critical
- `cursor`: pagination cursor
- `limit`: int (default: 50)

---

## Acknowledge Alert
**PATCH** `/alerts/{alertId}/acknowledge`

```json
{
  "notes": "Investigating spike in CPU usage",
  "isFalsePositive": false
}
```

**Response**: `200 OK`

---

## Resolve Alert
**PATCH** `/alerts/{alertId}/resolve`

```json
{
  "resolution": "root cause fixed",
  "notes": "scaled service"
}
```

**Response**: `200 OK`

---

## Train Model
**POST** `/models/train`

```json
{
  "algorithm": "isolation_forest",
  "hyperparameters": {
    "contamination": 0.01,
    "n_estimators": 100
  },
  "dataRange": {
    "start": "2024-01-01",
    "end": "2024-01-20"
  }
}
```

**Response**: `202 Accepted`
```json
{
  "jobId": "train-123",
  "status": "queued"
}
```

---

## Deploy Model Version
**POST** `/models/{modelId}/deploy`

```json
{
  "environment": "production",
  "rollout": "canary",
  "trafficPercent": 10
}
```

**Response**: `202 Accepted`

---

## Get Model Metrics
**GET** `/models/{modelId}/metrics`

**Response**: `200 OK`
```json
{
  "modelId": "uuid",
  "algorithm": "isolation_forest",
  "version": "v2.1.0",
  "metrics": {
    "precision": 0.92,
    "recall": 0.95,
    "f1": 0.93,
    "auc": 0.97
  }
}
```

---

## Configure Alert Rule
**POST** `/alert-rules`

```json
{
  "name": "Critical CPU Alert",
  "severity": "critical",
  "conditions": {
    "metric": "cpu",
    "threshold": 0.9
  },
  "channels": ["slack", "pagerduty"],
  "escalation": {
    "timeout": 300,
    "escalateTo": "manager"
  }
}
```

---

## Register Webhook
**POST** `/webhooks`

```json
{
  "name": "pagerduty-alerts",
  "url": "https://events.pagerduty.com/v2/enqueue",
  "events": ["alert.created", "alert.resolved"],
  "secret": "webhook-signing-secret"
}
```

**Response**: `201 Created`

---

## Submit Feedback Label
**POST** `/anomalies/{anomalyId}/feedback`

```json
{
  "label": "false_positive",
  "notes": "expected seasonal spike"
}
```

**Response**: `200 OK`

---

## Health Check
**GET** `/health`

**Response**: `200 OK`

---

## Error Responses

| Code | HTTP | Description |
|------|------|-------------|
| INVALID_DATA | 400 | Invalid data format |
| SOURCE_NOT_FOUND | 404 | Data source not configured |
| MODEL_NOT_READY | 503 | Model not yet trained |
| RATE_LIMITED | 429 | Too many requests |
| UNAUTHORIZED | 401 | Missing or invalid token |
| FORBIDDEN | 403 | Insufficient permissions |

## Rate Limiting

- Default limit: 1000 requests/minute per tenant.
- `429` responses include `Retry-After` header.

## Webhook Delivery Guarantees

- At-least-once delivery with exponential backoff.
- Requests signed with `X-Signature` HMAC.
- Dead-letter queue for failed deliveries.
