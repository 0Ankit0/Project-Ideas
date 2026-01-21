# C4 Component Diagram - Anomaly Detection System

## Detection Service Components

```mermaid
graph TB
    subgraph "Detection Service"
        ORCH[Detection Orchestrator]
        FEATURE[Feature Extractor]
        STAT[Statistical Detector]
        ML[ML Detector]
        ENSEMBLE[Ensemble Scorer]
        EXPLAIN[Explainer]
    end
    
    subgraph "External"
        STREAM[Stream Processor]
        CACHE[(Redis)]
        MODELS[Model Registry]
        DB[(InfluxDB)]
    end
    
    STREAM --> ORCH
    ORCH --> FEATURE
    FEATURE --> CACHE
    FEATURE --> STAT
    FEATURE --> ML
    STAT --> ENSEMBLE
    ML --> ENSEMBLE
    ML --> MODELS
    ENSEMBLE --> EXPLAIN
    EXPLAIN --> DB
```

## Alert Service Components

```mermaid
graph TB
    subgraph "Alert Service"
        ROUTER[Alert Router]
        RULES[Rule Engine]
        DEDUP[Deduplicator]
        CHANNELS[Channel Dispatcher]
    end
    
    subgraph "Channels"
        SLACK[Slack Sender]
        EMAIL[Email Sender]
        WEBHOOK[Webhook Caller]
    end
    
    subgraph "External"
        DB[(PostgreSQL)]
    end
    
    ROUTER --> RULES
    ROUTER --> DEDUP
    DEDUP --> CHANNELS
    CHANNELS --> SLACK
    CHANNELS --> EMAIL
    CHANNELS --> WEBHOOK
    RULES --> DB
```

**Component Descriptions**:
- **Detection Orchestrator**: Coordinate detection pipeline
- **Feature Extractor**: Compute statistical features
- **Statistical Detector**: Z-score, IQR-based detection
- **ML Detector**: Isolation Forest, Autoencoder
- **Ensemble Scorer**: Combine multiple model scores
- **Explainer**: Generate human-readable explanations
- **Alert Router**: Match anomalies to rules
- **Rule Engine**: Evaluate alert conditions
- **Deduplicator**: Prevent duplicate alerts
