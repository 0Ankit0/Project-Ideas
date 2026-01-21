# Use Case Diagram - Anomaly Detection System

```mermaid
graph TB
    subgraph Actors
        OP((Operator))
        DS((Data Scientist))
        ADMIN((Admin))
        API((API Consumer))
    end
    
    subgraph "Anomaly Detection System"
        UC1[View Anomaly Feed]
        UC2[Investigate Anomaly]
        UC3[Acknowledge Alert]
        UC4[Train Model]
        UC5[Deploy Model]
        UC6[Configure Thresholds]
        UC7[Set Alert Rules]
        UC8[API: Get Anomalies]
        UC9[API: Push Data]
    end
    
    OP --> UC1
    OP --> UC2
    OP --> UC3
    DS --> UC4
    DS --> UC5
    ADMIN --> UC6
    ADMIN --> UC7
    API --> UC8
    API --> UC9
```

## Actor Summary

| Actor | Primary Actions |
|-------|----------------|
| Operator | Monitor anomalies, acknowledge alerts |
| Data Scientist | Train and deploy ML models |
| System Admin | Configure thresholds, alert routing |
| API Consumer | Integrate via REST API |
