# User Stories — Document Intelligence System

## Personas

| Persona | Description |
|---|---|
| **Document Processor (DP)** | Operations team member who uploads document batches and monitors pipeline status |
| **Human Reviewer (HR)** | Subject-matter expert who reviews low-confidence extractions and resolves exceptions |
| **System Administrator (SA)** | Manages platform configuration: OCR providers, templates, user roles, retention policies |
| **Data Scientist (DS)** | Trains, evaluates, and deploys classification and extraction models |
| **Compliance Officer (CO)** | Audits PII handling, export manifests, retention compliance, and access logs |
| **API Consumer (AC)** | External system (ERP, RPA bot) consuming structured extraction results via API |

---

## User Stories

### US-01 — Submit Document Batch
**Persona:** Document Processor
**Priority:** Must Have

> As a Document Processor, I want to submit a batch of documents via a single API call so that I can trigger automated processing without manually uploading files one by one.

**Acceptance Criteria:**
- AC1: `POST /batches` accepts 1–1000 files per request in formats: PDF, TIFF, JPEG, PNG, DOCX, XLSX.
- AC2: The API validates file types and sizes before queuing; invalid files are rejected with HTTP 422 and a list of errors.
- AC3: The API responds within 5 seconds with HTTP 202 and a `batch_id`.
- AC4: A `BatchReceived` event is published to the event bus within 1 second of successful ingestion.
- AC5: The caller can poll `GET /batches/{batch_id}` to see per-document status.

---

### US-02 — Monitor Processing Status
**Persona:** Document Processor
**Priority:** Must Have

> As a Document Processor, I want to see real-time status for every document in a batch so that I can identify bottlenecks and failures without checking individual documents.

**Acceptance Criteria:**
- AC1: `GET /batches/{batch_id}` returns aggregate counts: total, queued, processing, completed, failed, in_review, exported.
- AC2: Status updates are reflected within 30 seconds of a state transition.
- AC3: Failed documents include a structured `failure_reason` field with error code and human-readable message.
- AC4: Webhook notifications are delivered to registered subscriber URLs for `OCRCompleted`, `ExtractionCompleted`, and `ValidationFailed` events.

---

### US-03 — View OCR Results
**Persona:** Document Processor
**Priority:** Must Have

> As a Document Processor, I want to view OCR results for each document page so that I can verify text extraction quality before downstream processing.

**Acceptance Criteria:**
- AC1: `GET /ocr/{document_id}` returns per-page OCR results including `raw_text`, `confidence_score`, and `word_level_bounding_boxes`.
- AC2: Pages with `confidence_score < 0.80` are flagged with `needs_review: true`.
- AC3: Response includes the OCR provider used and processing time in milliseconds.

---

### US-04 — Review Low-Confidence Extraction
**Persona:** Human Reviewer
**Priority:** Must Have

> As a Human Reviewer, I want to be presented with extracted field values alongside the document image so that I can correct incorrect extractions efficiently.

**Acceptance Criteria:**
- AC1: `GET /review-tasks/{id}` returns the task payload including: signed document page URLs, extracted field values with confidence scores and bounding boxes, validation failure messages.
- AC2: Reviewers can submit corrections via `POST /review-tasks/{id}/decisions` specifying corrected field values.
- AC3: Corrections are stored as `ReviewDecision` records with `actor_id`, `timestamp`, and the original vs. corrected value.
- AC4: After correction submission, the document state transitions to `APPROVED` and downstream validation is re-run.

---

### US-05 — View and Manage Review Queue
**Persona:** Human Reviewer
**Priority:** Must Have

> As a Human Reviewer, I want to see my assigned review tasks sorted by SLA due time so that I can prioritize the most urgent reviews.

**Acceptance Criteria:**
- AC1: `GET /review-queues/{queue_id}/tasks` returns tasks ordered by `due_at` ascending, with `is_overdue` flag set when `current_time > due_at`.
- AC2: Self-assignment of unassigned tasks is supported via `PATCH /review-tasks/{id}` with `assigned_to = current_user`.
- AC3: Medical record review tasks are only visible to users with roles `physician`, `nurse`, or `compliance_officer` (BR-06).
- AC4: Overdue tasks are visually flagged and an escalation notification is sent to the queue manager.

---

### US-06 — Create Extraction Template
**Persona:** System Administrator
**Priority:** Must Have

> As a System Administrator, I want to define extraction templates specifying which fields to extract from a document class so that I can customize extraction without retraining the ML model.

**Acceptance Criteria:**
- AC1: `POST /templates` accepts a template definition including `document_class`, a list of fields with `field_name`, `field_type`, `is_mandatory`, `zone_definition`, and `validation_rule_ids`.
- AC2: Templates are versioned; updating a template creates a new version and does not modify past extractions.
- AC3: Templates can be associated with one or more document classes.
- AC4: Inactive templates cannot be selected for new processing jobs.

---

### US-07 — Configure Validation Rules
**Persona:** System Administrator
**Priority:** Must Have

> As a System Administrator, I want to configure field validation rules so that extracted data quality is enforced automatically before export.

**Acceptance Criteria:**
- AC1: Supported rule types: `regex`, `range`, `lookup`, `cross_field`, `date_format`, `not_empty`.
- AC2: Rules can be marked `severity = ERROR` (blocks export) or `severity = WARNING` (flags but does not block).
- AC3: Rules are evaluated after extraction and results stored in `validation_results`.
- AC4: Validation rules can be tested via a dry-run API endpoint against a sample document.

---

### US-08 — Export Approved Documents to ERP
**Persona:** Document Processor / API Consumer
**Priority:** Must Have

> As an API Consumer, I want to trigger export of approved documents to our SAP system so that extracted invoice data populates our accounts payable module without manual data entry.

**Acceptance Criteria:**
- AC1: `POST /exports` accepts `target_system` (`sap`, `oracle`, `generic_rest`, `sftp`), `document_ids`, and `export_config_id`.
- AC2: Export produces a signed manifest (SHA-256 of payload) stored in `export_records`.
- AC3: An `AuditLog` entry is created for each export operation.
- AC4: Failed exports include a `failure_reason` and can be retried via `POST /exports/{id}/retry`.
- AC5: Export of medical records requires a compliance officer approval token.

---

### US-09 — Trigger Model Retraining
**Persona:** Data Scientist
**Priority:** Should Have

> As a Data Scientist, I want to trigger retraining of the classification model using newly validated documents so that the model improves accuracy over time.

**Acceptance Criteria:**
- AC1: `POST /models/retrain` accepts `model_type` (`classification` | `extraction`), `document_class`, and optional hyperparameter overrides.
- AC2: The system validates that ≥ 500 validated samples exist per document class before starting training (BR-08).
- AC3: Inter-annotator agreement ≥ 80% is verified on the training set; if not met, training is rejected with HTTP 422 and an agreement breakdown report.
- AC4: Training progress is streamed via a webhook or polled via `GET /models/retrain/{job_id}`.
- AC5: The new model version is registered in MLflow and transitions to Staging automatically if F1 ≥ 0.92.

---

### US-10 — Compare Model Versions
**Persona:** Data Scientist
**Priority:** Should Have

> As a Data Scientist, I want to compare performance metrics between model versions so that I can make an informed decision before promoting a new model to production.

**Acceptance Criteria:**
- AC1: `GET /models?stage=Staging` returns all staging model versions with metrics: F1, precision, recall, accuracy, avg inference time.
- AC2: The API supports a comparison endpoint `GET /models/compare?v1={id}&v2={id}` returning a side-by-side metric diff.
- AC3: Model promotion to Production requires an explicit `POST /models/{id}/promote` call by a `data_scientist` or `admin` role.

---

### US-11 — Audit PII Access
**Persona:** Compliance Officer
**Priority:** Must Have

> As a Compliance Officer, I want to audit who accessed PII-containing documents and when so that I can demonstrate GDPR compliance.

**Acceptance Criteria:**
- AC1: Every access to a document with PII fields creates an `AuditLog` entry with `actor_id`, `actor_role`, `timestamp`, `ip_address`, and `fields_accessed`.
- AC2: `GET /audit-logs?entity_type=document&event_type=PII_ACCESSED` returns a paginated, filterable audit trail.
- AC3: Audit logs are exported to SIEM within 5 seconds of event creation.
- AC4: Audit log tampering is detectable via cryptographic chaining (SHA-256 of previous entry embedded in each record).

---

### US-12 — Process GDPR Erasure Request
**Persona:** Compliance Officer
**Priority:** Must Have

> As a Compliance Officer, I want to process a GDPR right-to-erasure request so that PII is permanently deleted for data subjects who request it.

**Acceptance Criteria:**
- AC1: `POST /gdpr/erasure` accepts `data_subject_id` and initiates erasure of PII fields in `extracted_fields` where `is_pii = true`.
- AC2: Documents within mandatory retention windows (standard: 7 years, medical: 10 years) are exempt from erasure; the response lists exempt documents.
- AC3: Erasure is completed within 30 days; an `AuditLog` entry records the erasure event.
- AC4: After erasure, `GET /documents/{id}` returns the document with PII fields replaced by `[ERASED]`.

---

### US-13 — Manage Document Retention Policies
**Persona:** System Administrator
**Priority:** Must Have

> As a System Administrator, I want to configure retention policies per document class so that documents are automatically deleted at the end of their retention period.

**Acceptance Criteria:**
- AC1: Retention policies specify `document_class`, `retention_years`, and `deletion_action` (hard_delete | anonymize).
- AC2: A scheduled job runs daily to identify documents past their retention date and queues them for deletion.
- AC3: Deletion actions are logged in `AuditLog` with full details.
- AC4: Medical records have a minimum retention of 10 years enforced at the application level, not overrideable by configuration.

---

### US-14 — Handle OCR Provider Failover
**Persona:** System Administrator
**Priority:** Should Have

> As a System Administrator, I want the system to automatically fail over to Tesseract when the primary cloud OCR provider is unavailable so that document processing continues without manual intervention.

**Acceptance Criteria:**
- AC1: Circuit breaker opens after 5 consecutive OCR provider errors within 60 seconds.
- AC2: Fallback to Tesseract is automatic; documents processed via fallback are tagged with `ocr_provider = tesseract_fallback`.
- AC3: An alert is sent to PagerDuty when the circuit breaker opens.
- AC4: The primary OCR provider is automatically retried every 60 seconds; the circuit closes when two consecutive calls succeed.

---

### US-15 — Receive Webhook Notifications
**Persona:** API Consumer
**Priority:** Should Have

> As an API Consumer, I want to register webhook endpoints so that my system is notified when document processing completes, eliminating the need for polling.

**Acceptance Criteria:**
- AC1: `POST /webhooks` registers a subscriber URL with event type filters and an optional HMAC secret for signature verification.
- AC2: Webhook payloads include `event_type`, `batch_id`, `document_id`, `timestamp`, and a signature header `X-DIS-Signature`.
- AC3: Failed deliveries are retried up to 3 times with exponential backoff (30s, 2m, 10m).
- AC4: `GET /webhooks/{id}/deliveries` shows delivery history with status and response codes.

---

### US-16 — Access Document Class Restricted to Authorized Roles
**Persona:** Human Reviewer
**Priority:** Must Have

> As a Human Reviewer without medical clearance, I should not be able to access medical record documents so that PHI is only visible to authorized personnel.

**Acceptance Criteria:**
- AC1: Accessing a medical record document with an unauthorized role returns HTTP 403 with error code `INSUFFICIENT_ROLE`.
- AC2: The access attempt is logged in `AuditLog` with `event_type = UNAUTHORIZED_ACCESS_ATTEMPT`.
- AC3: A SIEM alert is triggered after 3 unauthorized access attempts from the same user within 1 hour.

---

### US-17 — View Extraction Confidence Breakdown
**Persona:** Document Processor
**Priority:** Should Have

> As a Document Processor, I want to see per-field extraction confidence scores so that I can assess data quality before exporting to ERP.

**Acceptance Criteria:**
- AC1: `GET /extractions/{document_id}` returns all extracted fields with `confidence_score`, `extraction_method`, and `needs_review` flag.
- AC2: Fields below the confidence threshold are highlighted with `status = NEEDS_REVIEW`.
- AC3: The response includes a document-level `overall_confidence` computed as weighted average per FR-33.

---

### US-18 — Override PII Redaction for Compliance
**Persona:** Compliance Officer
**Priority:** Could Have

> As a Compliance Officer, I want to grant a compliance override so that certain documents can retain unredacted PII for legal purposes.

**Acceptance Criteria:**
- AC1: `POST /documents/{id}/compliance-override` requires `compliance_officer` role and records `justification`, `granted_by`, and `expires_at`.
- AC2: Overrides are logged in `AuditLog` and visible in the compliance dashboard.
- AC3: Overrides have a maximum validity of 90 days; expired overrides revert to default redaction.

---

### US-19 — Manage Multi-language Documents
**Persona:** Document Processor
**Priority:** Should Have

> As a Document Processor, I want the system to detect and flag multi-language documents so that they can be routed to reviewers with the appropriate language skills.

**Acceptance Criteria:**
- AC1: Documents with detected language confidence < 0.85 for any single language are flagged `language = MULTI`.
- AC2: Multi-language documents are routed to a `Q_MULTILINGUAL` review queue.
- AC3: Review tasks include detected language distribution (e.g., 60% English, 40% Spanish).

---

### US-20 — Generate Processing Analytics Report
**Persona:** System Administrator
**Priority:** Could Have

> As a System Administrator, I want to view processing analytics (throughput, accuracy, review rates, SLA compliance) so that I can identify performance bottlenecks and optimization opportunities.

**Acceptance Criteria:**
- AC1: `GET /analytics/summary?from={date}&to={date}` returns: total documents processed, OCR accuracy distribution, classification accuracy, extraction accuracy, review rate, SLA breach rate, export success rate.
- AC2: Data is aggregated by day and document class.
- AC3: Analytics data is available with a maximum 1-hour delay from real-time.
