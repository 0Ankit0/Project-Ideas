# C4 Context & Container - Document Intelligence System

## Level 1: System Context

```mermaid
graph TB
    USER((Document Processor))
    REVIEWER((Reviewer))
    
    DIS["📄 Document Intelligence System<br/>[Software System]<br/>AI-powered document processing"]
    
    OCR_API[OCR Service API]
    STORAGE[Cloud Storage]
    
    USER -->|Uploads documents| DIS
    DIS -->|Extracted data| USER
    REVIEWER -->|Validates extractions| DIS
    
    DIS <-->|Text extraction| OCR_API
    DIS <-->|Store files| STORAGE
```

## Level 2: Container Diagram

```mermaid
graph TB
    subgraph "Document Intelligence System"
        WEB[Web Application<br/>React/Vue]
        API[API Service<br/>FastAPI]
        WORKER[Processing Worker<br/>Python/Celery]
        
        DB[(PostgreSQL<br/>Documents & Metadata)]
        MONGO[(MongoDB<br/>Extraction Results)]
        S3[S3 Bucket<br/>Document Files]
        QUEUE[RabbitMQ<br/>Job Queue]
    end
    
    subgraph "AI Services"
        OCR_SVC[OCR Service]
        NER_SVC[NER Service<br/>spaCy]
        CLS_SVC[Classifier Service]
    end
    
    USER((User)) -->|HTTPS| WEB
    WEB -->|REST API| API
    API --> DB
    API --> MONGO
    API --> S3
    API --> QUEUE
    
    QUEUE --> WORKER
    WORKER --> OCR_SVC
    WORKER --> NER_SVC
    WORKER --> CLS_SVC
    WORKER --> MONGO
```

## Container Descriptions

| Container | Technology | Purpose |
|-----------|------------|---------|
| Web Application | React/Vue | User interface for upload & review |
| API Service | FastAPI | Handle HTTP requests, orchestrate processing |
| Processing Worker | Python, Celery | Async document processing |
| PostgreSQL | Database |Store document metadata, users |
| MongoDB | NoSQL | Store JSON extraction results |
| S3 Bucket | Object Storage | Store uploaded documents |
| RabbitMQ | Message Queue | Distribute processing jobs |
| OCR Service | Tesseract/Cloud API | Text extraction |
| NER Service | spaCy | Entity extraction |
| Classifier Service | ML Model | Document classification |
