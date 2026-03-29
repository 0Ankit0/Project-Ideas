# Edge Cases - Extraction (NER/KV/Tables)

### 4.1. Overlapping Entities
* **Scenario**: Entities overlap (e.g., date within address string).
* **Impact**: Entity boundaries are wrong and fields are mis-mapped.
* **Solution**:
    * **Rules**: Apply entity precedence and boundary constraints.
    * **Review**: Highlight overlaps for manual correction.

### 4.2. Missing Required Fields
* **Scenario**: Mandatory fields are not found.
* **Impact**: Incomplete output and downstream failures.
* **Solution**:
    * **Validation**: Flag missing fields and route to review.
    * **UI**: Prompt reviewers to fill required fields.

### 4.3. Table Split Across Pages
* **Scenario**: Tables span multiple pages.
* **Impact**: Rows are duplicated or misaligned.
* **Solution**:
    * **Detection**: Track headers and continue table across pages.
    * **Normalization**: Merge rows using column alignment rules.

### 4.4. Non-Standard Layouts
* **Scenario**: Fields appear in unusual positions.
* **Impact**: Key-value extraction fails.
* **Solution**:
    * **Modeling**: Use layout-aware models and spatial features.
    * **Fallback**: Trigger manual review when layout confidence is low.

### 4.5. Currency and Date Ambiguity
* **Scenario**: Ambiguous formats like 01/02/2026 or $ vs €.
* **Impact**: Incorrect normalization and reporting.
* **Solution**:
    * **Locale**: Use document metadata or tenant locale to parse.
    * **Validation**: Flag ambiguous values for confirmation.
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

### Extraction Extensions
- Track field-level provenance (token spans, table cell coordinates, rule/model source) and enforce critical-field confidence floors before downstream publication.
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

### Extraction Quality Engineering
- Define deterministic post-processing transforms (date normalization, currency parsing, unit conversion).
- Add cross-field rule engine (subtotal + tax ~= total, date consistency, party identity constraints).
- Publish error taxonomy for extraction failures: detection, localization, normalization, semantic mismatch.

