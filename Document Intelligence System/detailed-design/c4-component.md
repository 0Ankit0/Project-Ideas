# C4 Component Diagram - Document Intelligence System

## Processing Worker Components

```mermaid
graph TB
    subgraph "Document Worker"
        ORCH[Processing Orchestrator]
        OCR_COMP[OCR Component]
        CLS_COMP[Classification Component]
        NER_COMP[NER Component]
        KV_COMP[KeyValue Component]
        VAL_COMP[Validation Component]
        REVIEW_COMP[Review Dispatcher]
    end
    
    subgraph "External"
        QUEUE[Message Queue]
        OCR_API[OCR API]
        MODELS[Model Registry]
        DB[(Database)]
        AUDIT[(Audit Logs)]
    end
    
    QUEUE --> ORCH
    ORCH --> OCR_COMP
    OCR_COMP --> OCR_API
    OCR_COMP --> CLS_COMP
    CLS_COMP --> MODELS
    CLS_COMP --> NER_COMP
    NER_COMP --> MODELS
    NER_COMP --> KV_COMP
    KV_COMP --> VAL_COMP
    VAL_COMP --> DB
    VAL_COMP --> REVIEW_COMP
    REVIEW_COMP --> AUDIT
```

## NER Service Components

```mermaid
graph TB
    subgraph "NER Service"
        NER_API[NER API Endpoint]
        TOKENIZER[Tokenizer]
        MODEL_LOADER[Model Loader]
        PREDICTOR[Entity Predictor]
        POST_PROC[Post-Processor]
    end
    
    subgraph "External"
        SPACY[spaCy Models]
        RULES[Custom Rules Config]
    end
    
    NER_API --> TOKENIZER
    TOKENIZER --> MODEL_LOADER
    MODEL_LOADER --> SPACY
    MODEL_LOADER --> PREDICTOR
    PREDICTOR --> POST_PROC
    POST_PROC --> RULES
```

**Component Descriptions**:
- **Processing Orchestrator**: Coordinate AI pipeline steps
- **OCR Component**: Extract text from images
- **Classification Component**: Identify document type
- **NER Component**: Extract named entities
- **KeyValue Component**: Extract field-value pairs
- **Validation Component**: Verify accuracy + confidence
- **Review Dispatcher**: Route low-confidence docs to review
- **Model Loader**: Load ML models from registry
- **Post-Processor**: Normalize and validate entities
