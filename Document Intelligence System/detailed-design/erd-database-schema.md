# ERD / Database Schema - Document Intelligence System

```mermaid
erDiagram
    documents ||--o{ pages : contains
    documents ||--|| extractions : has
    extractions ||--o{ entities : contains
    extractions ||--o{ key_values : contains
    extractions ||--o{ tables : contains
    users ||--o{ documents : uploads
    users ||--o{ corrections : makes
    users ||--o{ review_tasks : assigned
    users ||--o{ audit_logs : performs
    documents ||--o{ review_tasks : requires
    documents ||--o{ export_jobs : exported
    
    documents {
        uuid id PK
        uuid userId FK
        string filename
        string fileUrl
        string documentType
        string status
        timestamp uploadedAt
    }
    
    pages {
        uuid id PK
        uuid documentId FK
        int pageNumber
        string imageUrl
        text ocrText
        jsonb ocrMetadata
    }
    
    extractions {
        uuid id PK
        uuid documentId FK
        string documentType
        float avgConfidence
        string status
        timestamp extractedAt
    }
    
    entities {
        uuid id PK
        uuid extractionId FK
        string entityType
        string value
        float confidence
        jsonb boundingBox
    }
    
    key_values {
        uuid id PK
        uuid extractionId FK
        string key
        string value
        float confidence
        boolean manuallyVerified
    }
    
    tables {
        uuid id PK
        uuid extractionId FK
        jsonb headers
        jsonb rows
        int pageNumber
    }
    
    users {
        uuid id PK
        string email
        string name
        string role
    }
    
    corrections {
        uuid id PK
        uuid keyValueId FK
        uuid userId FK
        string oldValue
        string newValue
        timestamp correctedAt
    }

    review_tasks {
        uuid id PK
        uuid documentId FK
        uuid assignedTo FK
        string status
        timestamp createdAt
    }

    export_jobs {
        uuid id PK
        uuid documentId FK
        string format
        string status
        timestamp createdAt
    }

    audit_logs {
        uuid id PK
        uuid actorId FK
        string action
        jsonb metadata
        timestamp createdAt
    }
```

## Table Definitions

### documents
```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    filename VARCHAR(255) NOT NULL,
    file_url VARCHAR(500) NOT NULL,
    document_type VARCHAR(50),
    status VARCHAR(20) DEFAULT 'uploaded',
    uploaded_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_user_status (user_id, status),
    INDEX idx_type (document_type)
);
```

### extractions
```sql
CREATE TABLE extractions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id),
    document_type VARCHAR(50),
    avg_confidence FLOAT,
    status VARCHAR(20) DEFAULT 'pending',
    extracted_at TIMESTAMP DEFAULT NOW()
);
```

### entities
```sql
CREATE TABLE entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    extraction_id UUID NOT NULL REFERENCES extractions(id),
    entity_type VARCHAR(50) NOT NULL,  -- 'person', 'date', 'amount', etc.
    value TEXT NOT NULL,
    confidence FLOAT NOT NULL,
    bounding_box JSONB,  -- {x, y, width, height}
    INDEX idx_extraction (extraction_id),
    INDEX idx_type (entity_type)
);
```

### key_values
```sql
CREATE TABLE key_values (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    extraction_id UUID NOT NULL REFERENCES extractions(id),
    key VARCHAR(100) NOT NULL,
    value TEXT,
    confidence FLOAT NOT NULL,
    manually_verified BOOLEAN DEFAULT FALSE,
    INDEX idx_extraction (extraction_id),
    INDEX idx_key (key)
);
```

### review_tasks
```sql
CREATE TABLE review_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id),
    assigned_to UUID REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'open',
    created_at TIMESTAMP DEFAULT NOW()
);
```

### export_jobs
```sql
CREATE TABLE export_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id),
    format VARCHAR(10) NOT NULL,
    status VARCHAR(20) DEFAULT 'queued',
    created_at TIMESTAMP DEFAULT NOW()
);
```

### audit_logs
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Enum Definitions

| Enum | Values |
|------|--------|
| document_status | uploaded, queued, processing, completed, failed, needs_review |
| extraction_status | pending, completed, reviewed, approved |
| entity_type | person, organization, date, amount, address, email, phone |
| user_role | processor, reviewer, admin, data_scientist |
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

### Schema Governance Extensions
- Add normalized tables for model registry, threshold policies, calibration artifacts, review sessions, and feedback labels with retention and lineage constraints.
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

### Mermaid: Governance ERD Extension
```mermaid
erDiagram
    DOCUMENT ||--o{ PREDICTION : has
    PREDICTION }o--|| MODEL_SNAPSHOT : produced_by
    PREDICTION }o--|| THRESHOLD_POLICY : evaluated_with
    PREDICTION ||--o| REVIEW_TASK : may_require
    REVIEW_TASK ||--o{ FEEDBACK_LABEL : yields
```

