# Use Case Descriptions — Document Intelligence System

## UC-01 — Submit Document Batch

**Actor:** Document Processor, API Consumer
**Preconditions:**
- The caller is authenticated with a valid JWT bearing role `document_processor` or `api_consumer`.
- The target tenant has available storage quota.

**Main Flow:**
1. Caller sends `POST /batches` with multipart body: document files (PDF/TIFF/JPEG/PNG/DOCX/XLSX) and JSON metadata (`source`, `priority`, optional `workflow_config_id`).
2. System validates MIME types and file sizes (≤ 100 MB each, ≤ 1000 files total).
3. System computes SHA-256 hash of each file. Duplicates within the batch are rejected (BR-03).
4. System persists a `DocumentBatch` record with `status = RECEIVED` and stores each file in S3 at `{tenant_id}/{year}/{month}/{batch_id}/{doc_id}.{ext}`.
5. System publishes `BatchReceived` event to Kafka topic `document.events`.
6. System enqueues each document as a `DocumentQueued` event on `document.processing` topic.
7. System returns HTTP 202 with `batch_id` and `polling_url`.

**Alternate Flows:**
- **A1 — Invalid files:** Files failing MIME or size validation are rejected; valid files in the same batch continue processing. Response includes per-file error details.
- **A2 — Storage quota exceeded:** If the tenant's storage quota would be exceeded, the entire batch is rejected with HTTP 429 and a `QUOTA_EXCEEDED` error.

**Exceptions:**
- **E1 — S3 write failure:** If object storage is unavailable, documents are queued in a dead-letter store and an alert is sent. The batch status is `STORAGE_FAILED`.
- **E2 — Kafka unavailability:** If the event bus is unreachable, the batch is stored but not yet queued. A reconciliation job retries publishing every 30 seconds.

**Postconditions:**
- `DocumentBatch` record persisted with `status = RECEIVED`.
- Each valid document stored in S3 and queued for OCR.
- `BatchReceived` event published.

---

## UC-02 — OCR Processing

**Actor:** DIS OCR Worker (automated), Cloud OCR Provider
**Preconditions:**
- `DocumentQueued` event received from Kafka.
- Document binary retrievable from S3.

**Main Flow:**
1. OCR worker pulls `DocumentQueued` event from `document.processing` Kafka topic.
2. Worker downloads document from S3 and converts to page images (300 DPI for PDF/TIFF).
3. For each page, worker calls the configured OCR provider (AWS Textract or Google Vision API) with the page image.
4. Provider returns raw text, word-level bounding boxes, and confidence scores.
5. Worker creates one `OCRResult` record per page: `page_number`, `raw_text`, `word_level_bounding_boxes`, `confidence_score`, `provider`, `processing_time_ms`.
6. Worker computes document-level average confidence.
7. If avg confidence ≥ 0.95: document state → `OCR_COMPLETED`, `ClassificationQueued` event published.
8. If avg confidence in [0.80, 0.95): document state → `OCR_COMPLETED`, `ClassificationQueued` event published (low-confidence flag set).
9. If avg confidence < 0.80: `ReviewRequested` event published, document routed to review queue with `reason = LOW_OCR_CONFIDENCE` (BR-01).
10. `OCRCompleted` event published with `document_id`, `avg_confidence`, `page_count`, `provider`.

**Alternate Flows:**
- **A1 — Page rotation detected:** If a page's detected orientation angle > 2°, deskewing is applied before OCR. The `rotation_corrected` flag is set on the `OCRResult`.
- **A2 — Multi-language detected:** Language detection is run post-OCR. If no single language achieves > 85% confidence, `language = MULTI` is set and a `Q_MULTILINGUAL` queue entry is created.

**Exceptions:**
- **E1 — OCR provider timeout (> 30 s):** Request is retried once with 5 s delay. On second failure, the job falls back to Tesseract. If Tesseract also fails, document state → `OCR_FAILED`.
- **E2 — OCR provider circuit open:** Fallback to Tesseract immediately; `ocr_provider = tesseract_fallback` set on result.
- **E3 — Image conversion failure (corrupt PDF):** Document state → `PROCESSING_FAILED` with `failure_reason = CORRUPT_PAGE`. `DocumentRejected` event published.

**Postconditions:**
- `OCRResult` records created for all pages.
- Document state is `OCR_COMPLETED` or `REVIEW_QUEUED` or `OCR_FAILED`.
- `OCRCompleted` event published.

---

## UC-03 — Classify Document

**Actor:** DIS Classification Service (automated)
**Preconditions:**
- `ClassificationQueued` event received.
- `OCRResult` records available for the document.

**Main Flow:**
1. Classification service receives `ClassificationQueued` event.
2. Service loads the production `ModelVersion` for the `classification` model from MLflow.
3. Service constructs the model input: concatenated OCR text and layout features from `word_level_bounding_boxes`.
4. LayoutLM model inference produces a probability distribution over document classes.
5. Service selects the top class as `document_class` and records `confidence_score`, `model_version_id`, and `alternative_classes` (top-3).
6. A `ClassificationResult` record is persisted.
7. If confidence ≥ 0.70: `ClassificationCompleted` event published, `ExtractionQueued` event published.
8. If confidence < 0.70: `ReviewRequested` event published, document routed to review queue with `reason = LOW_CLASSIFICATION_CONFIDENCE`.

**Alternate Flows:**
- **A1 — Medical record classified:** If `document_class = medical_record`, access control flags are set on the document. Subsequent review tasks are restricted to `physician`, `nurse`, `compliance_officer` roles (BR-06).
- **A2 — Multi-document file:** If the classifier detects page-level heterogeneity (multiple classes with > 0.60 confidence on different page ranges), a `SPLIT_REQUIRED` flag is set for human review.

**Exceptions:**
- **E1 — Model not available:** If the production model cannot be loaded from MLflow, classification is retried after 60 seconds up to 3 times. On persistent failure, an alert is raised and the document is queued for review.
- **E2 — Inference timeout (> 10 s):** Document is re-queued with a 5-minute delay and `retry_count` incremented. After 3 retries, document state → `CLASSIFICATION_FAILED`.

**Postconditions:**
- `ClassificationResult` record persisted.
- Document state is `CLASSIFIED` or `REVIEW_QUEUED`.
- `ClassificationCompleted` event published.

---

## UC-04 — Extract Fields

**Actor:** DIS Extraction Service (automated)
**Preconditions:**
- `ExtractionQueued` event received.
- `ClassificationResult` available.
- An active `ExtractionSchema` exists for the document's `document_class`.

**Main Flow:**
1. Extraction service receives `ExtractionQueued` event.
2. Service loads the active `ExtractionSchema` for the classified document class.
3. For each field in the schema, the service runs extraction using the appropriate method: model-based (Donut/LayoutLMv3), template zone-based, or regex pattern.
4. Each extracted value is normalized (date to ISO 8601, currency to normalized decimal with currency code).
5. NER model scans all extracted values for PII (SSN, DOB, bank account). Detected PII is auto-redacted unless `compliance_override` is active (BR-05).
6. An `ExtractedField` record is created for each field with `field_name`, `extracted_value`, `normalized_value`, `confidence_score`, `bounding_box`, `extraction_method`, `is_pii`.
7. Fields with confidence below threshold are flagged: critical fields (invoice_total, tax_id) require ≥ 0.92; standard fields ≥ 0.75 (BR-02).
8. `ExtractionCompleted` event published.
9. `ValidationQueued` event published.

**Alternate Flows:**
- **A1 — Table spanning multiple pages:** The table reconstruction algorithm merges column headers from page N with data rows from pages N+1 through N+k. Merged rows are stored as structured JSON in the `extracted_value` field.
- **A2 — Missing mandatory fields:** If a mandatory field is not found, `extracted_value = null` and `confidence_score = 0.0`. The field is flagged `NEEDS_REVIEW`.

**Exceptions:**
- **E1 — No schema for document class:** If no active `ExtractionSchema` exists for the classified document class, `ExtractionCompleted` is published with no fields extracted and the document is flagged for template creation.
- **E2 — NER model failure:** PII detection failure does not block extraction but sets `pii_scan_status = FAILED`. An alert is raised and the document is flagged for manual PII review.

**Postconditions:**
- `ExtractedField` records created for all schema fields.
- PII fields redacted in storage.
- `ExtractionCompleted` event published.

---

## UC-05 — Validate Extraction

**Actor:** DIS Validation Engine (automated)
**Preconditions:**
- `ExtractionCompleted` event received.
- `ExtractedField` records available.
- `ValidationRule` records active for the document class.

**Main Flow:**
1. Validation engine loads all active `ValidationRule` records for the document class.
2. For each rule, the engine evaluates the specified field(s) against the rule definition.
3. Rule types evaluated: `not_empty`, `regex`, `range`, `date_format`, `lookup` (against reference table), `cross_field` (e.g., `invoice_total == sum(line_totals) ± 0.01`).
4. A `ValidationResult` record is created for each rule evaluation with `status` (PASS | FAIL | WARNING).
5. If all mandatory rules PASS: document state → `VALIDATED`, `ExportQueued` event published (if auto-export configured).
6. If any ERROR-severity rule FAIL: `ValidationFailed` event published, document routed to review queue.
7. WARNING-severity failures set the `has_warnings` flag but do not block export.

**Alternate Flows:**
- **A1 — No validation rules configured:** Document state transitions to `VALIDATED` with a note `no_rules_evaluated`. A system warning is logged.

**Exceptions:**
- **E1 — Conflicting rules:** If two rules produce contradictory results for the same field (e.g., one requires non-empty, another requires null for specific document types), a `RULE_CONFLICT` validation result is generated and the document is routed to review.
- **E2 — Lookup table unavailable:** If a `lookup` rule's reference table is unreachable, the rule is skipped and a `WARNING` result is generated with `reason = LOOKUP_SERVICE_UNAVAILABLE`.

**Postconditions:**
- `ValidationResult` records created for all evaluated rules.
- Document state is `VALIDATED` or `REVIEW_QUEUED`.
- `ValidationFailed` event published if applicable.

---

## UC-06 — Human Review

**Actor:** Human Reviewer
**Preconditions:**
- A `ReviewTask` exists in the review queue with `status = PENDING`.
- The reviewer's role permits access to the document class.

**Main Flow:**
1. Reviewer calls `GET /review-queues/{queue_id}/tasks` to see pending tasks sorted by `due_at`.
2. Reviewer self-assigns or is assigned a task via `PATCH /review-tasks/{id}` with `assigned_to = reviewer_id`. Task status → `IN_PROGRESS`.
3. Reviewer calls `GET /review-tasks/{id}` to load the full task payload: signed document page URLs, extracted field values with confidence and bounding boxes, validation failure messages.
4. Reviewer inspects each flagged field and provides corrections or confirmations.
5. Reviewer submits `POST /review-tasks/{id}/decisions` with: `decision` (APPROVE | REJECT | ESCALATE), `field_corrections` (array of field_id + corrected_value), `notes`.
6. System stores a `ReviewDecision` record.
7. If APPROVE: corrected `ExtractedField` values updated with `source = HUMAN_CORRECTION`. Document state → `REVIEW_COMPLETED`. `ReviewCompleted` event published.
8. If REJECT: document state → `REJECTED`. `DocumentRejected` event published.
9. If ESCALATE: task is re-assigned to `compliance_officer` or senior reviewer with elevated priority.

**Alternate Flows:**
- **A1 — SLA breach during review:** If `current_time > due_at` and task is still `IN_PROGRESS`, an escalation notification is sent. The task is flagged `is_overdue = true`. The queue manager receives an alert.
- **A2 — Reviewer reassignment:** A reviewer can release an unfinished task (`PATCH /review-tasks/{id}` with `assigned_to = null`), returning it to the unassigned pool.

**Exceptions:**
- **E1 — Concurrent edit conflict:** If two reviewers attempt to submit decisions for the same task simultaneously, the system uses optimistic locking (`version` field on `ReviewTask`). The second submission returns HTTP 409 with `CONCURRENT_EDIT_CONFLICT`.
- **E2 — Document page unavailable:** If the signed S3 URL has expired, the system generates a new presigned URL transparently.

**Postconditions:**
- `ReviewDecision` record persisted.
- `ExtractedField` records updated with human corrections.
- Document state is `REVIEW_COMPLETED`, `REJECTED`, or `ESCALATED`.
- `ReviewCompleted` event published.

---

## UC-07 — Export to ERP

**Actor:** API Consumer, Document Processor
**Preconditions:**
- Document state is `APPROVED` or `REVIEW_COMPLETED` (with APPROVE decision).
- An export configuration exists for the target ERP system.
- For medical records: compliance officer approval token required.

**Main Flow:**
1. Caller sends `POST /exports` with `target_system`, `document_ids`, `export_config_id`, and optionally `compliance_approval_token`.
2. System verifies document states are exportable and caller has `document_processor` or `api_consumer` role.
3. System constructs the export payload: structured JSON with extracted field values (PII fields redacted or encrypted per compliance override).
4. System computes SHA-256 hash of the payload to produce the signed manifest.
5. System delivers the payload to the target ERP: SAP (IDOC/RFC), Oracle (REST), or generic REST/SFTP.
6. On successful delivery, an `ExportRecord` is created with `export_id`, `manifest_hash`, `target_system`, `document_ids`, `exported_at`, `exported_by`.
7. An `AuditLog` entry is created for each exported document (BR-09).
8. `DocumentExported` event published for each document.

**Alternate Flows:**
- **A1 — Partial export failure:** If some documents in the batch fail to export (ERP timeout, validation rejection), successful exports proceed. Failed documents are listed in the `ExportRecord` with `failure_reason`.
- **A2 — Scheduled export:** Exports configured with a cron schedule are triggered by the export scheduler service without a caller request.

**Exceptions:**
- **E1 — ERP system unavailable:** Export is retried 3 times with exponential backoff. On persistent failure, `ExportRecord.status = FAILED`. An alert is sent to the integration team.
- **E2 — Medical record without approval token:** HTTP 403 returned with `COMPLIANCE_APPROVAL_REQUIRED`. The attempt is logged in `AuditLog`.

**Postconditions:**
- `ExportRecord` persisted with `status = COMPLETED` or `FAILED`.
- Document state → `EXPORTED`.
- `DocumentExported` event published.
- `AuditLog` entries created.

---

## UC-08 — Retrain Model

**Actor:** Data Scientist
**Preconditions:**
- ≥ 500 validated samples exist per target document class (BR-08).
- Inter-annotator agreement ≥ 80% verified on the training dataset.
- Data Scientist has `data_scientist` or `admin` role.

**Main Flow:**
1. Data Scientist calls `POST /models/retrain` with `model_type` (`classification` | `extraction`), `document_class`, and optional hyperparameter overrides.
2. System validates sample count and inter-annotator agreement. Fails with HTTP 422 if thresholds not met.
3. System creates a `TrainingDataset` record sampling validated `ExtractedField` and `ReviewDecision` records.
4. System triggers the ML training pipeline (SageMaker Training Job or Vertex AI Custom Job).
5. Training job logs metrics to MLflow: F1, precision, recall, accuracy, inference time per class.
6. If training completes with F1 ≥ 0.92 on held-out test set: `ModelVersion` transitions to `Staging` in MLflow.
7. `ModelRetrained` event published with `model_id`, `version`, `metrics`, `training_dataset_id`.
8. Data Scientist reviews metrics via `GET /models/compare?v1={staging_id}&v2={production_id}`.
9. Data Scientist promotes to Production via `POST /models/{id}/promote`.

**Alternate Flows:**
- **A1 — Training job fails:** Training infrastructure error triggers an alert. `ModelVersion.stage = FAILED`. The previous production model remains active.
- **A2 — F1 below threshold:** If F1 < 0.92 on test set, the model is registered with `stage = Archived` and not promoted to Staging. A report is sent to the Data Scientist.

**Exceptions:**
- **E1 — GPU pool exhausted:** Training job is queued until GPU capacity is available. Job stays in `PENDING` state; Data Scientist receives notification when training starts.
- **E2 — Training data drift detected:** If the training set distribution diverges significantly from the production distribution (KL divergence > 0.1), a warning is included in the training report.

**Postconditions:**
- `TrainingDataset` and `ModelVersion` records persisted.
- New model staged in MLflow.
- `ModelRetrained` event published.
