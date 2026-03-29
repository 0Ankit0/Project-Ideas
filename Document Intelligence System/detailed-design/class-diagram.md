# Class Diagram - Document Intelligence System

## Python AI Classes

```mermaid
classDiagram
    class DocumentProcessor {
        -OCREngine ocrEngine
        -Classifier classifier
        -NERPipeline nerPipeline
        -Validator validator
        +processDocument(documentId) ExtractionResult
        +getStatus(documentId) ProcessingStatus
    }
    
    class OCREngine {
        <<interface>>
        +extractText(imagePath) OCRResult
    }
    
    class TesseractOCR {
        -tesseractPath str
        -language str
        +extractText(imagePath) OCRResult
        +setLanguage(lang)
    }
    
    class CloudOCR {
        -apiKey str
        -service str
        +extractText(imagePath) OCRResult
        -callAPI(image) Response
    }
    
    class DocumentClassifier {
        -model Any
        -labelEncoder LabelEncoder
        +classify(text) str, float
        +train(texts, labels)
        +save(path)
        +load(path)
    }
    
    class NERPipeline {
        -spacyModel spacy.Language
        -customRules Dict
        +extractEntities(text, docType) List~Entity~
        +addCustomRule(pattern, label)
        -postProcess(entities) List~Entity~
    }
    
    class KeyValueExtractor {
        -patterns Dict
        -mlModel Optional
        +extractPairs(text, docType) List~KeyValue~
        +addPattern(docType, pattern)
    }
    
    class TableDetector {
        -cvModel Any
        +detectTables(imagePath) List~Table~
        +extractTableData(tableRegion) DataFrame
    }
    
    class Validator {
        -rules Dict
        +validate(extraction) ValidationResult
        +calculateConfidence(extraction) float
        +checkBusinessRules(data, docType) List~Error~
    }
    
    OCREngine <|-- TesseractOCR
    OCREngine <|-- CloudOCR
    DocumentProcessor --> OCREngine
    DocumentProcessor --> DocumentClassifier
    DocumentProcessor --> NERPipeline
    DocumentProcessor --> KeyValueExtractor
    DocumentProcessor --> TableDetector
    DocumentProcessor --> Validator
```

## Data Classes

```mermaid
classDiagram
    class Document {
        +str documentId
        +str filename
        +str fileUrl
        +str documentType
        +ProcessingStatus status
        +DateTime uploadedAt
    }
    
    class OCRResult {
        +str text
        +float confidence
        +List~BoundingBox~ boxes
        +Dict metadata
    }
    
    class Entity {
        +str entityType
        +str value
        +float confidence
        +BoundingBox location
        +int startChar
        +int endChar
    }
    
    class KeyValue {
        +str key
        +str value
        +float confidence
        +bool manuallyVerified
    }
    
    class Table {
        +List~str~ headers
        +List~List~str~~ rows
        +int pageNumber
        +BoundingBox location
    }
    
    class ExtractionResult {
        +str documentId
        +str documentType
        +List~Entity~ entities
        +List~KeyValue~ keyValues
        +List~Table~ tables
        +float avgConfidence
        +ValidationResult validation
    }
```

**Key Python Libraries**:
- Tesseract-OCR: Open-source OCR
- spaCy: Industrial-strength NLP
- Hugging Face Transformers: Pre-trained NER models
- OpenCV: Image processing
- pdfplumber: PDF text extraction
- pandas: Data manipulation
---

## AI/ML Operations Addendum

### Extraction & Classification Pipeline Detail
- Ingestion normalizes PDFs/images (de-skew, orientation correction, denoise, page splitting) before OCR inference, and preserves page-level provenance (`document_id`, `page_no`, `checksum`) for reproducibility.
- OCR outputs word-level tokens with bounding boxes and confidence, then layout reconstruction builds reading order, sections, tables, and key-value candidates for downstream models.
- Classification runs as a two-stage ensemble: coarse document family classifier followed by template/domain subtype classifier; routing controls which extraction graph, validation rules, and post-processors execute.
- Extraction combines multiple strategies (template anchors, layout-aware transformer NER, regex/rule validators, and table parsers) with conflict resolution and source attribution at field level.

### Confidence Thresholding Logic
- Every predicted artifact (doc type, entity, field, table cell) carries calibrated confidence; calibration is maintained per model version using held-out reliability sets (temperature scaling/isotonic).
- Thresholds are policy-driven and tiered: **auto-accept**, **review-required**, and **reject/reprocess** bands, configurable per document type and field criticality (e.g., totals, IDs, legal dates).
- Composite confidence uses weighted signals: model probability, OCR quality, extraction-rule agreement, cross-field consistency checks, and historical drift indicators.
- Dynamic threshold overrides apply during incidents (e.g., OCR degradation or new template rollout) with explicit expiry, audit log entries, and rollback playbooks.

### Human-in-the-Loop Review Flow
- Low-confidence or policy-flagged documents enter a reviewer queue with SLA tiers, reason codes, and pre-highlighted spans/bounding boxes to minimize correction time.
- Reviewer edits are captured as structured feedback (`before`, `after`, `reason`, `reviewer_role`) and linked to model/version metadata for supervised retraining datasets.
- Dual-review and adjudication is required for high-risk fields or regulated document classes; disagreements are labeled and retained for error analysis.
- Review outcomes feed active-learning samplers that prioritize uncertain/novel templates while enforcing PII minimization and role-based masking in annotation tools.

### Model Lifecycle Governance
- Model registry tracks lineage across datasets, feature pipelines, prompts/config, evaluation reports, approval status, and deployment environment.
- Promotion gates enforce quality thresholds (classification F1, field-level precision/recall, calibration error, latency/cost SLOs) plus fairness and security checks before production release.
- Runtime monitoring covers drift (input schema, token distributions, template novelty), confidence shifts, reviewer override rates, and business KPI regressions with automated alerts.
- Rollout strategy uses canary/shadow deployments, version pinning per tenant/workflow, and deterministic rollback with incident postmortems and governance sign-off.

### Domain Model Extensions
- Add core entities like `ThresholdPolicy`, `ModelArtifact`, `ReviewTask`, and `FeedbackLabel` with clear ownership boundaries and lifecycle methods.
---


## Implementation-Ready Deep Dive

### Operational Control Objectives
| Objective | Target | Owner | Evidence |
|---|---|---|---|
| Straight-through processing rate | >= 75% for baseline templates | ML Ops Lead | Weekly quality report |
| Critical-field precision | >= 99% on regulated fields | Applied ML Engineer | Offline eval + reviewer sample audit |
| Reviewer turnaround SLA | P95 < 2 business hours | Review Ops Manager | Queue dashboard + SLA breach alerts |
| Rollback readiness | < 15 min rollback execution | Platform SRE | Change ticket + rollback drill logs |

### Implementation Backlog (Must-Have)
1. Implement per-field threshold policy engine with policy versioning and tenant/document-type overrides.
2. Add calibrated confidence tracking table and nightly reliability job with ECE/Brier drift alarms.
3. Introduce reviewer work allocation service (skill-based routing, dual-review for high-risk forms).
4. Create retraining dataset contracts (gold labels, weak labels, rejected examples, hard-negative mining).
5. Establish model governance workflow (proposal -> validation -> canary -> promotion -> archive).

### Production Acceptance Checklist
- [ ] End-to-end traceability from uploaded file to exported structured payload.
- [ ] Full audit trail for every manual correction and model/policy decision.
- [ ] Canary release + rollback automation validated in staging and production-like data.
- [ ] Drift/quality SLO dashboards wired to paging policy and incident template.
- [ ] Security controls for PII redaction, purpose-limited access, and retention enforcement.

### Mermaid: Core Class Relationships
```mermaid
classDiagram
    class ProcessingOrchestrator
    class ClassificationService
    class ExtractionService
    class ThresholdService
    class ReviewService
    ProcessingOrchestrator --> ClassificationService
    ProcessingOrchestrator --> ExtractionService
    ProcessingOrchestrator --> ThresholdService
    ThresholdService --> ReviewService
```

