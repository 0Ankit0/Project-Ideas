# Architecture Diagram - Document Intelligence System

## AI Processing Pipeline

```mermaid
graph TB
    subgraph "Upload Layer"
        WEB[Web Upload]
        API[REST API]
    end
    
    subgraph "Storage"
        S3[Document Storage<br/>S3/GCS]
    end
    
    subgraph "Processing Queue"
        QUEUE[Message Queue<br/>RabbitMQ/SQS]
    end
    
    subgraph "AI Pipeline"
        OCR[OCR Engine<br/>Tesseract/Textract]
        CLASSIFIER[Document Classifier<br/>ML Model]
        NER[NER Pipeline<br/>spaCy/Transformers]
        KV[Key-Value Extractor<br/>Rule-based + ML]
        TABLE[Table Detector<br/>CV Model]
        VALIDATOR[Validator<br/>Confidence Scoring]
    end
    
    subgraph "Data Layer"
        DB[(PostgreSQL<br/>Metadata)]
        RESULTS[(MongoDB<br/>Extractions)]
    end
    
    subgraph "ML Infrastructure"
        MODELS[Model Registry<br/>MLflow]
        TRAINING[Training Pipeline<br/>Python]
    end
    
    WEB --> API
    API --> S3
    API --> QUEUE
    
    QUEUE --> OCR
    OCR --> CLASSIFIER
    CLASSIFIER --> NER
    NER --> KV
    NER --> TABLE
    KV --> VALIDATOR
    TABLE --> VALIDATOR
    
    VALIDATOR --> RESULTS
    API --> DB
    
    MODELS --> CLASSIFIER
    MODELS --> NER
    TRAINING --> MODELS
```

## Layered Architecture

```
┌─────────────────────────────────────────┐
│      Presentation Layer                 │
│  (Web UI, REST API)                     │
└───────────────┬─────────────────────────┘
                │
┌───────────────▼─────────────────────────┐
│      Service Layer                      │
│  (Document Processing, Extraction)      │
└───────────────┬─────────────────────────┘
                │
┌───────────────▼─────────────────────────┐
│      AI/ML Layer                        │
│  (OCR, NER, Classification)             │
└───────────────┬─────────────────────────┘
                │
┌───────────────▼─────────────────────────┐
│      Data Layer                         │
│  (Storage, Database, Queue)             │
└─────────────────────────────────────────┘
```

## Technology Recommendations

| Component | Technology Options |
|-----------|-------------------|
| OCR | Tesseract (open-source), AWS Textract, Google Vision API |
| NER | spaCy, Hugging Face Transformers (BERT, RoBERTa) |
| Classification | scikit-learn, TensorFlow, PyTorch |
| API | FastAPI, Flask |
| Storage | S3, Google Cloud Storage, Azure Blob |
| Database | PostgreSQL (metadata), MongoDB (JSON extractions) |
| Queue | RabbitMQ, AWS SQS, Google Pub/Sub |
| Model Registry | MLflow, Weights & Biases |
