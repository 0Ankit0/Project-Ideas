# System Context Diagram - Document Intelligence System

```mermaid
graph TB
    subgraph "External Actors"
        USER((Document Processor))
        REVIEWER((Reviewer))
        DS((Data Scientist))
    end
    
    DIS["📄 Document Intelligence<br/>System<br/>[AI-Powered]<br/>OCR, NER, Classification"]
    
    subgraph "External Systems"
        HOST[Host Application<br/>ERP/CRM/HR System]
        OCR[OCR Service<br/>Textract/Vision API]
        STORAGE[Cloud Storage<br/>S3/GCS]
        QUEUE[Message Queue<br/>RabbitMQ/SQS]
    end
    
    USER -->|Upload documents| DIS
    DIS -->|Extracted data| USER
    
    REVIEWER -->|Corrections| DIS
    DS -->|Train models| DIS
    
    HOST <-->|API Integration| DIS
    DIS <-->|Text extraction| OCR
    DIS <-->|Store documents| STORAGE
    DIS --> |Processing jobs| QUEUE
    
    style DIS fill:#438dd5,color:#fff
```

## System Boundaries

### Inside the System
- Document upload & storage
- OCR text extraction
- Document classification
- NER entity extraction
- Key-value pair extraction
- Validation & confidence scoring
- Review UI
- Model training pipeline

### Outside the System
- User authentication (host app)
- Document creation (host app)
- Final data storage (host app database)
- Payment for cloud services
