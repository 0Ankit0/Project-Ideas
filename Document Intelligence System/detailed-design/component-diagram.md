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
    end
    
    subgraph "Storage & Queue"
        S3[Document Storage<br/>S3]
        DB[(PostgreSQL)]
        QUEUE[Job Queue<br/>RabbitMQ]
        CACHE[(Redis)]
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
    WORKER --> DB
    
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
| Training Pipeline | Python, MLflow | Model training & evaluation |
