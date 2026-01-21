# Architecture Diagram - Anomaly Detection System

## Stream Processing Architecture

```mermaid
graph TB
    subgraph "Data Sources"
        KAFKA[Kafka Topics]
        API_IN[REST API]
        POLL[DB Polling]
    end
    
    subgraph "Stream Processing"
        FLINK[Apache Flink<br/>Stream Processor]
    end
    
    subgraph "Detection Engine"
        FEATURE[Feature Engine<br/>Python]
        DETECTOR[ML Detector<br/>Isolation Forest/Autoencoder]
    end
    
    subgraph "Alert System"
        ROUTER[Alert Router]
        EMAIL[Email]
        SLACK[Slack]
        WEBHOOK[Webhooks]
    end
    
    subgraph "Storage"
        TS_DB[(InfluxDB<br/>Time-Series)]
        PG[(PostgreSQL<br/>Metadata)]
        REDIS[(Redis<br/>Cache)]
    end
    
    subgraph "ML Infrastructure"
        REGISTRY[Model Registry<br/>MLflow]
        TRAINING[Training Service]
    end
    
    KAFKA --> FLINK
    API_IN --> FLINK
    POLL --> FLINK
    
    FLINK --> FEATURE
    FEATURE --> DETECTOR
    DETECTOR --> TS_DB
    DETECTOR --> ROUTER
    
    ROUTER --> EMAIL
    ROUTER --> SLACK
    ROUTER --> WEBHOOK
    
    REGISTRY --> DETECTOR
    TRAINING --> REGISTRY
    
    DETECTOR --> PG
    FEATURE --> REDIS
```

## Layered Architecture

```
┌─────────────────────────────────────────┐
│      Presentation Layer                 │
│  (Dashboard, REST API)                  │
└───────────────┬─────────────────────────┘
                │
┌───────────────▼─────────────────────────┐
│      Processing Layer                   │
│  (Stream Processing, Feature Eng)       │
└───────────────┬─────────────────────────┘
                │
┌───────────────▼─────────────────────────┐
│      Detection Layer                    │
│  (ML Models, Scoring, Thresholds)       │
└───────────────┬─────────────────────────┘
                │
┌───────────────▼─────────────────────────┐
│      Alert Layer                        │
│  (Routing, Channels, Escalation)        │
└───────────────┬─────────────────────────┘
                │
┌───────────────▼─────────────────────────┐
│      Data Layer                         │
│  (Time-Series DB, Metadata, Cache)      │
└─────────────────────────────────────────┘
```

## Technology Recommendations

| Component | Technology Options |
|-----------|-------------------|
| Stream Processing | Apache Flink, Kafka Streams, Spark Streaming |
| Detection | scikit-learn (Isolation Forest), TensorFlow (Autoencoder) |
| Time-Series DB | InfluxDB, TimescaleDB, Prometheus |
| API | FastAPI |
| Queue | Kafka, RabbitMQ |
| Alerting | PagerDuty, Slack, Custom webhooks |
