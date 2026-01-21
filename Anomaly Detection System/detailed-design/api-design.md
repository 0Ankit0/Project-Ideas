# API Design - Anomaly Detection System

**Base URL**: `https://api.example.com/v1`  
**Auth**: Bearer Token

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

## Get Anomalies
**GET** `/anomalies`

**Query Params**:
- `severity`: low | medium | high | critical
- `status`: detected | acknowledged | resolved
- `start`: ISO timestamp
- `end`: ISO timestamp
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
  "page": 1
}
```

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

## Error Responses

| Code | HTTP | Description |
|------|------|-------------|
| INVALID_DATA | 400 | Invalid data format |
| SOURCE_NOT_FOUND | 404 | Data source not configured |
| MODEL_NOT_READY | 503 | Model not yet trained |
| RATE_LIMITED | 429 | Too many requests |
