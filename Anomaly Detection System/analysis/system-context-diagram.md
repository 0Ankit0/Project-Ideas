# System Context Diagram - Anomaly Detection System

```mermaid
graph TB
    subgraph "External Actors"
        OP((Operator))
        DS((Data Scientist))
    end
    
    ADS["🚨 Anomaly Detection<br/>System<br/>[AI-Powered]<br/>Real-time anomaly detection"]
    
    subgraph "Data Sources"
        KAFKA[Kafka<br/>Event Stream]
        API_SRC[REST API<br/>Data Push]
        DB_SRC[Database<br/>Polling]
    end
    
    subgraph "Alert Channels"
        EMAIL[Email]
        SLACK[Slack]
        PAGER[PagerDuty]
        WEBHOOK[Webhooks]
    end
    
    subgraph "External Systems"
        TS_DB[Time-Series DB<br/>InfluxDB]
        MODEL_REG[Model Registry<br/>MLflow]
    end
    
    KAFKA --> ADS
    API_SRC --> ADS
    DB_SRC --> ADS
    
    OP -->|Monitor| ADS
    DS -->|Train models| ADS
    
    ADS --> EMAIL
    ADS --> SLACK
    ADS --> PAGER
    ADS --> WEBHOOK
    
    ADS <--> TS_DB
    ADS <--> MODEL_REG
    
    style ADS fill:#e74c3c,color:#fff
```

## System Boundaries

### Inside the System
- Data ingestion & processing
- Feature engineering
- Anomaly detection (ML models)
- Alert generation & routing
- Dashboard & visualization
- Model training & deployment

### Outside the System
- Data source management
- Root cause remediation
- User authentication (SSO)
- Third-party integrations
