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

### Code Architecture Extensions
- Reflect bounded modules for OCR adapters, classifier/extractor orchestration, policy evaluation, and feedback ingestion to support independent releases.
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

### Mermaid: Code-Level Module Boundaries
```mermaid
flowchart LR
    Controllers --> Application
    Application --> Domain
    Application --> MLAdapters
    Application --> PolicyEngine
    Application --> ReviewIntegration
    MLAdapters --> ExternalProviders
```

