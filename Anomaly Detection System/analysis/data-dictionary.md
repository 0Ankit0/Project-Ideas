# Data Dictionary - Anomaly Detection System

## Core Entities

### DataPoint
- **id**: UUID
- **sourceId**: string
- **timestamp**: ISO 8601 (UTC)
- **values**: map<string, number>
- **metadata**: map<string, string>

### FeatureVector
- **id**: UUID
- **dataPointId**: UUID
- **features**: map<string, number>
- **window**: string (e.g., 5m, 1h)
- **version**: string

### Anomaly
- **id**: UUID
- **dataPointId**: UUID
- **score**: float (0–1)
- **severity**: low | medium | high | critical
- **modelVersion**: string
- **detectedAt**: ISO 8601
- **explanation**: string

### Alert
- **id**: UUID
- **anomalyId**: UUID
- **status**: open | acknowledged | resolved | suppressed
- **channel**: email | slack | webhook | pagerduty
- **createdAt**: ISO 8601
- **resolvedAt**: ISO 8601 (nullable)

### Model
- **id**: UUID
- **algorithm**: string
- **version**: string
- **status**: training | ready | deprecated
- **metrics**: map<string, float>

### AlertRule
- **id**: UUID
- **name**: string
- **severity**: low | medium | high | critical
- **conditions**: json
- **channels**: list<string>
- **enabled**: boolean

### DataSource
- **id**: UUID
- **name**: string
- **type**: kafka | api | batch
- **schema**: json
- **status**: active | disabled

### Feedback
- **id**: UUID
- **anomalyId**: UUID
- **label**: true_positive | false_positive | unknown
- **notes**: string