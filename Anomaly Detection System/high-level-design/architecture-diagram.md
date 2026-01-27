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
        VALIDATOR[Schema Validator]
    end
    
    subgraph "Detection Engine"
        FEATURE[Feature Engine<br/>Python]
        DETECTOR[ML Detector<br/>Isolation Forest/Autoencoder]
        EXPLAIN[Explainability Service]
    end
    
    subgraph "Alert System"
        ROUTER[Alert Router]
        RULES[Rule Engine]
        DEDUP[Alert Deduplicator]
        EMAIL[Email]
        SLACK[Slack]
        WEBHOOK[Webhooks]
    end
    
    subgraph "Storage"
        TS_DB[(InfluxDB<br/>Time-Series)]
        PG[(PostgreSQL<br/>Metadata)]
        REDIS[(Redis<br/>Cache)]
        AUDIT[(Audit Logs)]
        WH_REG[(Webhook Registry)]
    end
    
    subgraph "ML Infrastructure"
        REGISTRY[Model Registry<br/>MLflow]
        TRAINING[Training Service]
        MONITOR[Drift Monitor]
    end
    
    KAFKA --> VALIDATOR
    API_IN --> VALIDATOR
    POLL --> VALIDATOR
    VALIDATOR --> FLINK
    
    FLINK --> FEATURE
    FEATURE --> DETECTOR
    DETECTOR --> EXPLAIN
    DETECTOR --> TS_DB
    DETECTOR --> ROUTER
    
    ROUTER --> RULES
    RULES --> DEDUP
    DEDUP --> EMAIL
    DEDUP --> SLACK
    DEDUP --> WEBHOOK
    
    REGISTRY --> DETECTOR
    TRAINING --> REGISTRY
    MONITOR --> TRAINING
    
    DETECTOR --> PG
    FEATURE --> REDIS
    ROUTER --> PG
    ROUTER --> AUDIT
    WEBHOOK --> WH_REG
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
