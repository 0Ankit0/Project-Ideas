# Sequence Diagram - Document Intelligence System

## SD-01: Complete Document Processing

```mermaid
sequenceDiagram
    participant Worker as Processing Worker
    participant OCR as OCR Engine
    participant CLS as Classifier
    participant NER as NER Pipeline
    participant KV as KeyValue Extractor
    participant VAL as Validator
    participant DB as Database
    
    Worker->>Worker: dequeueDocument()
    Worker->>+OCR: extractText(documentPath)
    OCR-->>-Worker: ocrResult{text, confidence}
    
    Worker->>+CLS: classify(text)
    CLS-->>-Worker: docType, confidence
    
    Worker->>+NER: extractEntities(text, docType)
    NER-->>-Worker: entities[]
    
    Worker->>+KV: extractPairs(text, docType)
    KV-->>-Worker: keyValues[]
    
    Worker->>+VAL: validate(extraction)
    VAL-->>-Worker: validationResult
    
    Worker->>+DB: saveExtraction(result)
    DB-->>-Worker: saved
    
    Worker->>Worker: notifyComplete()
```

## SD-04: Review & Correction

```mermaid
sequenceDiagram
    participant Reviewer
    participant API as Review API
    participant Review as Review Service
    participant DB as Database
    participant Audit as Audit Logger
    
    Reviewer->>+API: openReviewTask(documentId)
    API->>+Review: getExtraction(documentId)
    Review->>+DB: SELECT extraction
    DB-->>-Review: data
    Review-->>-API: extraction
    API-->>-Reviewer: showReviewUI
    
    Reviewer->>+API: submitCorrections(edits)
    API->>+Review: saveCorrections(edits)
    Review->>+DB: INSERT corrections
    DB-->>-Review: saved
    Review->>+Audit: record("review.completed", documentId)
    Audit-->>-Review: logged
    Review-->>-API: ok
    API-->>-Reviewer: 200 OK
```

## SD-05: Export Extracted Data

```mermaid
sequenceDiagram
    participant Analyst
    participant API as Export API
    participant Export as Export Service
    participant DB as Database
    participant Notify as Notification Service
    
    Analyst->>+API: requestExport(documentIds, format)
    API->>+Export: createExportJob()
    Export->>+DB: INSERT export_job
    DB-->>-Export: jobId
    Export-->>-API: jobQueued
    API-->>-Analyst: 202 Accepted
    
    Export->>+DB: fetchExtractions(documentIds)
    DB-->>-Export: data
    Export->>Export: generateFile()
    Export->>+Notify: exportReady(userId, link)
    Notify-->>-Export: sent
```

## SD-02: NER Entity Extraction

```mermaid
sequenceDiagram
    participant NER as NER Pipeline
    participant Tokenizer
    participant Model as spaCy Model
    participant Rules as Custom Rules
    participant Post as Post-Processor
    
    NER->>+Tokenizer: tokenize(text)
    Tokenizer-->>-NER: tokens[]
    
    NER->>+Model: predict(tokens)
    Model-->>-NER: rawEntities[]
    
    NER->>+Rules: applyCustomRules(text, docType)
    Rules-->>-NER: ruleBasedEntities[]
    
    NER->>NER: mergeEntities()
    NER->>+Post: normalize(entities)
    Post-->>-NER: normalizedEntities[]
```

## SD-03: Table Extraction

```mermaid
sequenceDiagram
    participant TD as Table Detector
    participant CV as CV Model
    participant Parser as Table Parser
    
    TD->>+CV: detectRegions(image)
    CV-->>-TD: tableRegions[]
    
    loop For each table region
        TD->>+Parser: extractData(region)
        Parser-->>Parser: detectRows()
        Parser-->>Parser: detectColumns()
        Parser-->>+Parser: parseCell()
        Parser-->>-TD: {headers, rows}
    end
```
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

### Sequence Extensions
- Include explicit branches for auto-accept vs review-required vs reject, plus asynchronous feedback ingestion and retraining trigger orchestration.
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

### Mermaid: Detailed Service Sequence
```mermaid
sequenceDiagram
    participant Orchestrator
    participant OCR
    participant CLS
    participant EXT
    participant POLICY
    Orchestrator->>OCR: extractText
    OCR-->>Orchestrator: tokens
    Orchestrator->>CLS: classify
    CLS-->>Orchestrator: docType
    Orchestrator->>EXT: extract(docType,tokens)
    EXT-->>Orchestrator: fields+confidence
    Orchestrator->>POLICY: evaluate
    POLICY-->>Orchestrator: decision
```

