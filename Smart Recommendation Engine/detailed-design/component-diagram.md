# Component Diagram - Smart Recommendation Engine

```mermaid
graph TB
    subgraph "API Layer"
        REC_API[Recommendation API<br/>FastAPI]
        ADMIN_API[Admin API<br/>FastAPI]
    end
    
    subgraph "ML Services"
        FEATURE_SVC[Feature Service<br/>Python]
        TRAINING_SVC[Training Service<br/>Python/MLflow]
        INFERENCE_SVC[Inference Service<br/>TF Serving/FastAPI]
        EXP_SVC[Experiment Service<br/>Python]
    end
    
    subgraph "Data Components"
        EVENT_PROC[Event Processor<br/>Kafka Consumer]
        FEATURE_ENG[Feature Engineer<br/>PySpark]
    end
    
    subgraph "External ML Infrastructure"
        FEATURE_STORE[Feature Store<br/>Feast]
        MODEL_REG[Model Registry<br/>MLflow]
        VECTOR_DB[Vector DB<br/>Milvus]
    end
    
    subgraph "Storage"
        DB[(PostgreSQL)]
        CACHE[(Redis)]
        STREAM[Kafka]
    end
    
    REC_API --> FEATURE_SVC
    REC_API --> INFERENCE_SVC
    REC_API --> CACHE
    
    ADMIN_API --> TRAINING_SVC
    ADMIN_API --> EXP_SVC
    
    TRAINING_SVC --> FEATURE_STORE
    TRAINING_SVC --> MODEL_REG
    
    INFERENCE_SVC --> MODEL_REG
    INFERENCE_SVC --> FEATURE_STORE
    INFERENCE_SVC --> VECTOR_DB
    
    EVENT_PROC --> STREAM
    EVENT_PROC --> FEATURE_ENG
    
    FEATURE_ENG --> FEATURE_STORE
    FEATURE_SVC --> FEATURE_STORE
    
    FEATURE_SVC --> DB
    EXP_SVC --> DB
```

## Component Responsibilities

| Component | Technology | Purpose |
|-----------|------------|---------|
| Recommendation API | FastAPI | Serve recommendations via REST |
| Feature Service | Python | Manage feature retrieval |
| Training Service | Python, MLflow | Train and evaluate models |
| Inference Service | TensorFlow Serving | Real-time ML predictions |
| Experiment Service | Python | Manage A/B tests |
| Event Processor | Kafka Consumer | Process user action events |
| Feature Engineer | PySpark | Compute features from raw data |
