# Use Case Descriptions - Document Intelligence System

## UC-01: Upload Document
**Primary Actor**: Document Processor  
**Description**: Upload document for automated processing

**Preconditions**:
- User is authenticated
- File type and size limits are known

**Main Flow**:
1. User selects file (PDF/image)
2. System validates file type and size
3. System uploads to storage
4. System generates document ID
5. System queues for processing
6. User receives confirmation with document ID

**Alternate Flows**:
- A1: Invalid file type → reject with supported types
- A2: File too large → reject with max size guidance

**Exceptions**:
- E1: Storage unavailable → retry and notify user

**Postconditions**:
- Document stored and queued

**Success Criteria**: Document uploaded and queued for processing

---

## UC-02: Process Document (System Internal)
**Trigger**: Document uploaded  
**Description**: AI pipeline processes document

**Preconditions**:
- Document exists in storage
- OCR and extraction services are available

**Main Flow**:
1. System retrieves document from queue
2. **OCR Engine** extracts text from images
3. **Document Classifier** identifies document type
4. **NER Pipeline** extracts entities
5. **Key-Value Extractor** maps fields to schema
6. **Validator** checks accuracy, assigns confidence scores
7. System saves extracted data
8. System notifies user of completion

**Alternate Flows**:
- A1: OCR confidence low → route to review
- A2: Ambiguous document type → request human selection

**Exceptions**:
- E1: OCR fails → mark as failed and notify
- E2: Downstream service unavailable → retry with backoff

**Postconditions**:
- Structured data stored with confidence scores

**Success Criteria**: Data extracted with confidence scores

---

## UC-03: Review & Correct Extractions
**Primary Actor**: Reviewer  
**Description**: Validate and fix extraction errors

**Preconditions**:
- Review task exists
- Reviewer has appropriate permissions

**Main Flow**:
1. Reviewer opens document in review UI
2. System displays side-by-side: document image + extracted fields
3. System highlights low-confidence fields
4. Reviewer edits incorrect values
5. System marks fields as manually corrected
6. Reviewer approves document
7. System updates extraction data

**Alternate Flows**:
- A1: Reviewer rejects document → send back to processing

**Exceptions**:
- E1: Document not found → show error and requeue

**Postconditions**:
- Corrections stored and audit logged

**Success Criteria**: Corrections saved, document approved

---

## UC-04: Train Custom NER Model
**Primary Actor**: Data Scientist  
**Description**: Improve entity extraction accuracy

**Preconditions**:
- Labeled data available
- Training environment accessible

**Main Flow**:
1. Data Scientist prepares labeled training data
2. Selects NER architecture (spaCy, Transformers)
3. Configures hyperparameters
4. System trains model on labeled data
5. System evaluates on test set
6. Data Scientist reviews metrics (precision, recall, F1)
7. Deploys model to production

**Alternate Flows**:
- A1: Metrics below threshold → reject model

**Exceptions**:
- E1: Training failure → capture logs and notify

**Postconditions**:
- Model registered and versioned

**Success Criteria**: New model deployed with improved accuracy

---

## UC-05: Configure Document Types
**Primary Actor**: System Admin  
**Description**: Define schemas and required fields per document type

**Preconditions**:
- Admin permissions available

**Main Flow**:
1. Admin creates document type
2. Defines required fields and validation rules
3. Saves schema and activates type

**Postconditions**:
- New document type is available in processing pipeline

**Success Criteria**: New type becomes selectable and valid

---

## UC-06: Export Extracted Data
**Primary Actor**: Analyst  
**Description**: Export structured data for downstream systems

**Preconditions**:
- Documents processed successfully

**Main Flow**:
1. Analyst selects documents and format
2. System creates export job
3. Export completes and link is provided

**Postconditions**:
- Export file stored and audit logged

**Success Criteria**: Data exported in requested format
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

### Use Case Extensions
- Expand main and alternate flows for low-confidence handling, escalation, and reviewer adjudication outcomes including SLA breach paths.
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

