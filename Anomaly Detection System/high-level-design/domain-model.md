# Domain Model - Anomaly Detection System

```mermaid
erDiagram
    DATA_SOURCE ||--o{ DATA_POINT : produces
    DATA_POINT ||--o| ANOMALY : becomes
    ANOMALY ||--o{ ALERT : triggers
    ML_MODEL ||--o{ ANOMALY : detects
    USER ||--o{ ALERT : acknowledges
    
    DATA_SOURCE {
        uuid id PK
        string name
        string type
        json config
        boolean active
    }
    
    DATA_POINT {
        uuid id PK
        uuid sourceId FK
        json values
        json features
        float anomalyScore
        timestamp timestamp
    }
    
    ANOMALY {
        uuid id PK
        uuid dataPointId FK
        uuid modelId FK
        string severity
        float score
        json explanation
        timestamp detectedAt
    }
    
    ML_MODEL {
        uuid id PK
        string algorithm
        string version
        json hyperparameters
        json metrics
        string status
        timestamp trainedAt
    }
    
    ALERT {
        uuid id PK
        uuid anomalyId FK
        string channel
        string status
        uuid acknowledgedBy FK
        timestamp sentAt
        timestamp acknowledgedAt
    }
    
    ALERT_RULE {
        uuid id PK
        string name
        string severity
        json conditions
        json channels
        boolean active
    }
    
    USER {
        uuid id PK
        string email
        string role
    }
```

**Key Entities**:
- **Data Source**: Origin of monitoring data (Kafka, API, DB)
- **Data Point**: Single measurement with features
- **Anomaly**: Detected unusual data point
- **ML Model**: Trained detection algorithm
- **Alert**: Notification sent to operator
- **Alert Rule**: Configuration for alert routing
