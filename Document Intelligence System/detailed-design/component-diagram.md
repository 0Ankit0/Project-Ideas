# Component Diagram - Document Intelligence System

```mermaid
graph TB
    subgraph "API Layer"
        API[REST API<br/>FastAPI]
        WEB_UI[Review UI<br/>React]
    end
    
    subgraph "Processing Services"
        WORKER[Document Worker<br/>Celery]
        OCR_SVC[OCR Service<br/>Tesseract/Cloud]
        CLS_SVC[Classifier Service<br/>Python]
        NER_SVC[NER Service<br/>spaCy]
        KV_SVC[Key-Value Service<br/>Python]
        TABLE_SVC[Table Service<br/>CV]
        VALIDATOR[Validation Service]
        REVIEW_SVC[Review Service]
        EXPORT_SVC[Export Service]
        NOTIF_SVC[Notification Service]
    end
    
    subgraph "Storage & Queue"
        S3[Document Storage<br/>S3]
        DB[(PostgreSQL)]
        QUEUE[Job Queue<br/>RabbitMQ]
        CACHE[(Redis)]
        AUDIT[(Audit Logs)]
    end
    
    subgraph "ML Infrastructure"
        MODELS[Model Store<br/>MLflow]
        TRAINING[Training Pipeline<br/>Python]
    end
    
    API --> QUEUE
    API --> DB
    API --> S3
    WEB_UI --> API
    
    QUEUE --> WORKER
    WORKER --> OCR_SVC
    WORKER --> CLS_SVC
    WORKER --> NER_SVC
    WORKER --> KV_SVC
    WORKER --> TABLE_SVC
    WORKER --> VALIDATOR
    WORKER --> DB
    VALIDATOR --> REVIEW_SVC
    REVIEW_SVC --> DB
    REVIEW_SVC --> AUDIT
    EXPORT_SVC --> DB
    EXPORT_SVC --> NOTIF_SVC
    
    CLS_SVC --> MODELS
    NER_SVC --> MODELS
    TRAINING --> MODELS
```

## Component Responsibilities

| Component | Technology | Purpose |
|-----------|------------|---------|
| REST API | FastAPI | Handle HTTP requests, serve data |
| Review UI | React | Human review interface |
| Document Worker | Celery | Async document processing |
| OCR Service | Tesseract, AWS Textract | Text extraction |
| Classifier Service | scikit-learn, TensorFlow | Document type classification |
| NER Service | spaCy, Transformers | Entity extraction |
| Key-Value Service | Rule-based + ML | Field-value extraction |
| Table Service | CV | Table detection & extraction |
| Validation Service | Python | Confidence checks & rules |
| Review Service | Python | Human review workflow |
| Export Service | Python | Export structured data |
| Notification Service | Email/SMS | User notifications |
| Training Pipeline | Python, MLflow | Model training & evaluation |
