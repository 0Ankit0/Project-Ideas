# Activity Diagram - Document Intelligence System

## 1. Document Processing Pipeline

```mermaid
flowchart TD
    Start([Document Uploaded]) --> Validate{Valid<br/>File?}
    Validate -->|No| Error([Return Error])
    Validate -->|Yes| Store[Store in Cloud]
    
    Store --> Queue[Add to Processing Queue]
    Queue --> OCR[OCR: Extract Text]
    
    OCR --> Quality{Good<br/>OCR Quality?}
    Quality -->|No| ManualOCR[Flag for Manual Review]
    Quality -->|Yes| Classify[Classify Document Type]
    
    Classify --> KnownType{Known<br/>Type?}
    KnownType -->|No| Generic[Use Generic Extraction]
    KnownType -->|Yes| LoadRules[Load Type-Specific Rules]
    
    LoadRules --> NER[NER: Extract Entities]
    Generic --> NER
    
    NER --> KV[Extract Key-Value Pairs]
    KV --> Table[Detect & Extract Tables]
    
    Table --> Validate[Validate Extracted Data]
    Validate --> Confidence[Calculate Confidence Scores]
    
    Confidence --> LowConf{Confidence<br/>< 80%?}
    LowConf -->|Yes| FlagReview[Flag for Human Review]
    LowConf -->|No| AutoApprove[Auto-Approve]
    
    FlagReview --> Complete([Processing Complete])
    AutoApprove --> Complete
    ManualOCR --> Complete
```

---

## 2. Model Training Workflow

```mermaid
flowchart TD
    Start([Initiate Training]) --> LoadData[Load Labeled Dataset]
    LoadData --> Split[Train/Valid/Test Split]
    
    Split --> SelectModel{Model<br/>Type?}
    
    SelectModel -->|Classification| TrainCLS[Train Classifier]
    SelectModel -->|NER| TrainNER[Train NER Model]
    SelectModel -->|OCR| TrainOCR[Fine-tune OCR]
    
    TrainCLS --> Eval[Evaluate on Validation]
    TrainNER --> Eval
    TrainOCR --> Eval
    
    Eval --> Acceptable{Metrics<br/>Meet Target?}
    Acceptable -->|No| Tune[Adjust Hyperparameters]
    Tune --> SelectModel
    
    Acceptable -->|Yes| Test[Test on Hold-out Set]
    Test --> Deploy[Deploy to Production]
    Deploy --> Monitor[Monitor Performance]
    Monitor --> Drift{Performance<br/>Degraded?}
    
    Drift -->|Yes| Retrain[Schedule Retraining]
    Drift -->|No| Continue[Continue Monitoring]
    
    Retrain --> Start
    Continue --> Monitor
```

---

## 3. Human Review Process

```mermaid
flowchart TD
    Start([Document Flagged]) --> Load[Load Document & Extractions]
    Load --> Display[Show Side-by-Side View]
    
    Display --> ReviewField[Review Each Field]
    ReviewField --> Correct{Needs<br/>Correction?}
    
    Correct -->|Yes| Edit[Edit Field Value]
    Edit --> MarkManual[Mark as Manual Correction]
    MarkManual --> NextField{More<br/>Fields?}
    
    Correct -->|No| NextField
    NextField -->|Yes| ReviewField
    NextField -->|No| Approve[Approve Document]
    
    Approve --> Learn{Learning<br/>Enabled?}
    Learn -->|Yes| UpdateModel[Queue for Model Update]
    Learn -->|No| Save[Save Corrections]
    
    UpdateModel --> Save
    Save --> End([Document Complete])
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

### Activity Extensions
- Add swim paths for confidence gating, reviewer intervention, and retraining trigger approval to visualize operational feedback loops end to end.
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

### Mermaid: Detailed Processing Activity
```mermaid
flowchart TD
    A[Ingest] --> B[Preprocess]
    B --> C[OCR]
    C --> D[Classify]
    D --> E[Extract Fields]
    E --> F[Validate + Score]
    F --> G{Confidence Band}
    G -->|Auto| H[Publish]
    G -->|Review| I[Reviewer Queue]
    I --> J[Reviewer Decision]
    J --> H
    J --> K[Feedback Capture]
    K --> L[Retraining Backlog]
```

