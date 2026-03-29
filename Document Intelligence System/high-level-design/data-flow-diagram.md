# Data Flow Diagram - Document Intelligence System

## Level 0: Context

```mermaid
flowchart LR
    USER((User)) -->|Document| DIS[Document<br/>Intelligence<br/>System]
    DIS -->|Structured Data| USER
```

## Level 1: Main Processes

```mermaid
flowchart TB
    USER((User))
    
    P1[1.0<br/>Document<br/>Ingestion]
    P2[2.0<br/>OCR<br/>Processing]
    P3[3.0<br/>AI<br/>Classification]
    P4[4.0<br/>Entity<br/>Extraction]
    P5[5.0<br/>Validation]
    P6[6.0<br/>Review &<br/>Correction]
    P7[7.0<br/>Export]
    P8[8.0<br/>Audit &<br/>Compliance]
    
    D1[(Documents)]
    D2[(OCR Text)]
    D3[(Extractions)]
    D4[(ML Models)]
    D5[(Review Tasks)]
    D6[(Export Jobs)]
    D7[(Audit Logs)]
    
    USER -->|Upload| P1
    P1 -->|File| D1
    D1 -->|Image/PDF| P2
    P2 -->| Text| D2
    D2 -->|Text| P3
    P3 -->|Type| P4
    D4 -->|Models| P3
    D4 -->|Models| P4
    P4 -->|Entities| P5
    P5 -->|Validated Data| D3
    P5 -->|Low Confidence| P6
    P6 -->|Corrections| D3
    P6 -->|Review Task| D5
    D3 -->|Export Request| P7
    P7 -->|Export Files| D6
    D6 -->|Results| USER
    P1 -->|Audit Event| P8
    P5 -->|Audit Event| P8
    P6 -->|Audit Event| P8
    P7 -->|Audit Event| P8
    P8 -->|Records| D7
```

## Level 2: Entity Extraction (4.0)

```mermaid
flowchart TB
    P4_1[4.1<br/>Load NER<br/>Model]
    P4_2[4.2<br/>Tokenize<br/>Text]
    P4_3[4.3<br/>Run<br/>NER]
    P4_4[4.4<br/>Extract<br/>Key-Values]
    P4_5[4.5<br/>Detect<br/>Tables]
    
    D2[(OCR Text)]
    D3[(Extractions)]
    D4[(ML Models)]
    
    D2 --> P4_2
    D4 --> P4_1
    P4_1 --> P4_3
    P4_2 --> P4_3
    P4_3 --> P4_4
    P4_3 --> P4_5
    P4_4 --> D3
    P4_5 --> D3
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

### Data Flow Extensions
- Add confidence-score propagation, threshold decision nodes, and reviewer correction loops as first-class flows with lineage metadata attached.
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

### Mermaid: Data Flow with Governance Signals
```mermaid
flowchart LR
    Raw[(Raw Docs)] --> Pre[Preprocess]
    Pre --> Ocr[(OCR Tokens)]
    Ocr --> Pred[Predictions + Confidence]
    Pred --> Pol[Policy Decision]
    Pol --> Out[(Structured Output)]
    Pol --> Rev[(Review Queue)]
    Rev --> Fb[(Feedback Labels)]
    Fb --> Train[Training Pipeline]
```

