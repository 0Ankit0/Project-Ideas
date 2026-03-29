# Edge Cases - Document Ingestion

### 1.1. Corrupted File Upload
* **Scenario**: A user uploads a corrupted or partial PDF/image.
* **Impact**: OCR fails or produces empty output.
* **Solution**:
    * **Validation**: Verify file integrity and attempt basic parsing.
    * **UI**: Show a clear error and request re-upload.

### 1.2. Unsupported File Type
* **Scenario**: A file type outside the allowed list is uploaded.
* **Impact**: Processing fails and user confusion increases.
* **Solution**:
    * **Validation**: Enforce MIME type and extension checks.
    * **UI**: Display supported formats explicitly.

### 1.3. Oversized Batch Upload
* **Scenario**: A batch exceeds size or count limits.
* **Impact**: Queue overload and slow processing.
* **Solution**:
    * **Limits**: Enforce file count and size caps.
    * **UX**: Provide partial acceptance with a failure report.

### 1.4. Duplicate Document
* **Scenario**: The same document is uploaded multiple times.
* **Impact**: Redundant processing and duplicate records.
* **Solution**:
    * **Detection**: Hash documents to detect duplicates.
    * **Policy**: Mark duplicates and optionally skip processing.

### 1.5. Storage Outage
* **Scenario**: Object storage becomes temporarily unavailable.
* **Impact**: Uploads fail and documents are lost.
* **Solution**:
    * **Retry**: Use resumable uploads and exponential backoff.
    * **Fallback**: Queue uploads locally until storage is restored.
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

### Ingestion Extensions
- Add ingestion quarantine flow for corrupted/suspicious files and template-fingerprinting to route unknown layouts into controlled reviewer-first processing.
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

### Ingestion Hardening
- Add file fingerprinting, malware scanning, MIME consistency checks, and encrypted quarantine workflow.
- Deduplicate using hash + semantic near-duplicate checks to prevent replay and overbilling.
- Persist ingestion decisions with signed evidence for forensic investigations.

