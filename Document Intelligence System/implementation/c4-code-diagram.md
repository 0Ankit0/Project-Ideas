# C4 Code Diagram

This document provides a detailed **code-level C4 view** for the Document Intelligence System.

## Code-Level Structure
```mermaid
flowchart TB
  subgraph Interface[Interface Layer]
    DocumentController
    ExtractionController
    ClassificationController
  end

  subgraph Application[Application Layer]
    DocumentAppService
    OCRAppService
    ExtractionAppService
    ClassificationAppService
    ValidationAppService
  end

  subgraph Domain[Domain Layer]
    DocumentAggregate
    PageEntity
    ExtractionResult
    ClassificationPolicy
    ValidationRuleSet
  end

  subgraph Infrastructure[Infrastructure Layer]
    DocumentRepository
    OCRAdapter
    NLPAdapter
    ModelAdapter
    StorageAdapter
    EventPublisher
  end

  DocumentController --> DocumentAppService --> DocumentAggregate
  ExtractionController --> ExtractionAppService --> ExtractionResult
  ClassificationController --> ClassificationAppService --> ClassificationPolicy

  DocumentAppService --> OCRAppService --> OCRAdapter
  OCRAppService --> StorageAdapter
  ExtractionAppService --> NLPAdapter
  ClassificationAppService --> ModelAdapter
  ValidationAppService --> ValidationRuleSet

  DocumentAppService --> DocumentRepository
  ExtractionAppService --> DocumentRepository
  ClassificationAppService --> DocumentRepository
  DocumentAppService --> EventPublisher
```

## Critical Runtime Sequence: Extract Structured Fields
```mermaid
sequenceDiagram
  autonumber
  participant API as ExtractionController
  participant DOC as DocumentAppService
  participant OCR as OCRAppService
  participant EXT as ExtractionAppService
  participant NLP as NLPAdapter
  participant VAL as ValidationAppService
  participant REPO as DocumentRepository

  API->>DOC: start extraction(documentId)
  DOC->>OCR: run OCR on pages
  OCR-->>DOC: text blocks + coordinates
  DOC->>EXT: extract entities/fields
  EXT->>NLP: infer entities
  NLP-->>EXT: structured candidates
  EXT->>VAL: validate against schema
  VAL-->>EXT: validated fields + issues
  EXT->>REPO: persist extraction result
  EXT-->>API: extraction output
```

## Module Responsibilities
- **DocumentAppService**: lifecycle orchestration for upload, processing, and status transitions.
- **OCR/Extraction/Classification services**: isolated ML-enabled concerns with clear interfaces.
- **Validation service**: business-rule and schema validation before final persistence.
- **Infrastructure adapters**: model execution, object storage, and event publication.

## Implementation Notes
- Persist page-level provenance (bounding boxes, confidence scores, model versions).
- Keep extraction schema versioned per document type.
- Use asynchronous processing for large documents; expose status polling endpoints.
