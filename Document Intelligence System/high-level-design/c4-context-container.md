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

### Context/Container Extensions
- Highlight external dependencies for OCR providers, foundation-model endpoints, governance tooling, and human review workbench with failure isolation paths.
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

### Mermaid: Context + Containers
```mermaid
flowchart TB
    Client --> Gateway
    Gateway --> Orchestrator
    Orchestrator --> OCR
    Orchestrator --> NLP
    Orchestrator --> Policy
    Policy --> ReviewApp
    Orchestrator --> DataStore
    ReviewApp --> DataStore
    Training --> Registry
    Registry --> NLP
```

