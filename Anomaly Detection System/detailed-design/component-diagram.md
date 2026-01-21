# Component Diagram - Anomaly Detection System

```mermaid
graph TB
    subgraph "API Layer"
        API[REST API<br/>FastAPI]
        DASH[Dashboard<br/>React]
    end
    
    subgraph "Ingestion"
        KAFKA_CONS[Kafka Consumer<br/>Python]
        API_RECV[API Receiver<br/>FastAPI]
    end
    
    subgraph "Processing"
        STREAM[Stream Processor<br/>Flink/Python]
        FEATURE[Feature Engine<br/>Python]
    end
    
    subgraph "Detection"
        DETECTOR[Anomaly Detector<br/>Python ML]
        SCORER[Scoring Service<br/>Python]
    end
    
    subgraph "Alerting"
        ROUTER[Alert Router<br/>Python]
        SLACK_INT[Slack Integration]
        EMAIL_INT[Email Integration]
        WEBHOOK_INT[Webhook Integration]
    end
    
    subgraph "Storage"
        INFLUX[(InfluxDB)]
        PG[(PostgreSQL)]
        REDIS[(Redis)]
    end
    
    subgraph "ML Infrastructure"
        MLFLOW[MLflow Registry]
        TRAINER[Training Service]
    end
    
    KAFKA_CONS --> STREAM
    API_RECV --> STREAM
    STREAM --> FEATURE
    FEATURE --> REDIS
    FEATURE --> DETECTOR
    
    DETECTOR --> MLFLOW
    DETECTOR --> SCORER
    SCORER --> INFLUX
    SCORER --> ROUTER
    
    ROUTER --> SLACK_INT
    ROUTER --> EMAIL_INT
    ROUTER --> WEBHOOK_INT
    
    TRAINER --> MLFLOW
    API --> PG
    DASH --> API
```

## Component Responsibilities

| Component | Technology | Purpose |
|-----------|------------|---------|
| Kafka Consumer | Python | Consume data streams |
| Stream Processor | Flink/Python | Process streaming data |
| Feature Engine | Python | Compute features |
| Anomaly Detector | scikit-learn, TF | ML inference |
| Alert Router | Python | Route alerts to channels |
| Training Service | Python, MLflow | Train ML models |
| InfluxDB | Time-Series | Store metrics and anomalies |
| PostgreSQL | Database | Store metadata, config |
| Redis | Cache | Cache features, recent data |
