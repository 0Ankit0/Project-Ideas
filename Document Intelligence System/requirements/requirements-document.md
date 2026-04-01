# Requirements Document — Document Intelligence System

## 1. Introduction

### 1.1 Purpose
This document defines the complete functional and non-functional requirements for the Document Intelligence System (DIS), an enterprise platform that automates the ingestion, OCR processing, classification, structured data extraction, validation, human review, and ERP export of business documents.

### 1.2 Scope
DIS processes documents submitted via REST API or scheduled batch imports. It supports PDF, TIFF, JPEG, PNG, DOCX, and XLSX formats. Processed data is exported to SAP, Oracle ERP, or arbitrary REST/SFTP endpoints. The system maintains full audit trails and complies with GDPR, HIPAA, and SOC-2 Type II.

### 1.3 Stakeholders

| Stakeholder | Role |
|---|---|
| Document Processor | Submits batches, monitors processing status |
| Human Reviewer | Reviews low-confidence extractions, resolves exceptions |
| System Administrator | Manages users, roles, OCR providers, templates |
| Data Scientist | Trains and evaluates classification and extraction models |
| Compliance Officer | Audits PII handling, retention policies, export manifests |
| ERP Integration Team | Consumes exported structured data |

---

## 2. Functional Requirements

### FR-01 — Batch Document Submission
The system shall accept a multipart HTTP POST to `/batches` containing one or more document files (PDF, TIFF, JPEG, PNG, DOCX, XLSX) and a JSON metadata payload specifying `source`, `priority` (P1/P2/P3), and optional `workflow_config_id`.

### FR-02 — File Validation on Ingestion
The system shall validate each submitted file: maximum file size 100 MB per file, maximum 1 000 documents per batch, allowed MIME types enforced. Files failing validation shall be rejected with HTTP 422 and a structured error listing each invalid file.

### FR-03 — Duplicate Detection
The system shall compute SHA-256 hash of each document's binary content. If a document with the same hash already exists within the same batch, it shall be rejected with status `DUPLICATE` and a reference to the original document ID (BR-03).

### FR-04 — Document Storage
Validated documents shall be stored in object storage (S3 or GCS) with server-side AES-256 encryption. The storage path pattern shall be `{tenant_id}/{year}/{month}/{batch_id}/{document_id}.{ext}`.

### FR-05 — Asynchronous Processing Queue
After ingestion, each document shall be enqueued to a task queue (Kafka topic `document.queued`) for asynchronous OCR processing. The API response shall return HTTP 202 with `batch_id` and a polling URL.

### FR-06 — OCR Processing
The system shall extract text and layout information from each document page using a configured OCR provider (AWS Textract, Google Cloud Vision, or Tesseract). For each page, an `OCRResult` record shall be created containing: `page_number`, `raw_text`, `word_level_bounding_boxes` (JSON), `confidence_score` (0.0–1.0), `provider`, `processing_time_ms`.

### FR-07 — OCR Confidence Routing
Documents with average OCR confidence < 0.80 shall be routed to the human review queue with priority equal to or higher than the document's batch priority (BR-01). Documents with average OCR confidence ≥ 0.95 shall be auto-accepted without mandatory review.

### FR-08 — Document Classification
After OCR, each document shall be classified using a fine-tuned LayoutLM model. The classification result shall include: `document_class` (e.g., `invoice`, `contract`, `receipt`, `medical_record`, `tax_form`, `id_document`, `purchase_order`), `confidence_score`, `model_version_id`, `alternative_classes` (top-3 ranked).

### FR-09 — Classification Confidence Routing
If classification confidence < 0.70, the document shall be routed to human review for manual classification. The review task shall include the top-3 candidate classes and their confidence scores.

### FR-10 — Template-Based Extraction
The system shall support named extraction templates that define a list of `ExtractedField` targets: `field_name`, `field_type` (string, number, date, currency, boolean), `extraction_region` (bounding box or zone label), `is_mandatory`, `validation_rules` references.

### FR-11 — Model-Based Field Extraction
The system shall run a trained field extraction model to extract structured values from classified documents. For each field, an `ExtractedField` record shall be created with: `field_name`, `extracted_value`, `normalized_value`, `confidence_score`, `bounding_box`, `extraction_method` (model | template | regex).

### FR-12 — Per-Field Confidence Enforcement
Critical fields (`invoice_total`, `tax_id`, `contract_value`, `patient_id`) must achieve confidence ≥ 0.92. Standard fields must achieve confidence ≥ 0.75. Fields below threshold shall be flagged as `NEEDS_REVIEW` and included in the review task payload (BR-02).

### FR-13 — PII Detection and Redaction
The system shall run a Named Entity Recognition (NER) model to detect PII fields: SSN, date of birth, bank account numbers, credit card numbers, passport numbers. Detected PII shall be redacted (replaced with `[REDACTED_<TYPE>]`) in stored extracted values unless the document has a `compliance_override` flag set by a `compliance_officer` role (BR-05).

### FR-14 — Validation Rules Engine
The system shall evaluate configurable `ValidationRule` records against extracted fields. Rule types supported: `regex` (value matches pattern), `range` (numeric value within min/max), `lookup` (value exists in reference table), `cross_field` (relationship between two fields, e.g., `line_total = quantity * unit_price`), `date_format` (ISO 8601 or custom format), `not_empty` (mandatory field check).

### FR-15 — Validation Result Recording
Each rule evaluation shall produce a `ValidationResult` record with: `rule_id`, `field_id`, `status` (PASS | FAIL | WARNING), `actual_value`, `expected_pattern`, `message`. A document with any FAIL result on a mandatory rule shall be routed to the review queue.

### FR-16 — Review Queue Management
The system shall maintain prioritized review queues: `Q_MEDICAL_LEGAL` (P1, SLA 4 h), `Q_FINANCIAL` (P2, SLA 24 h), `Q_GENERAL` (P3, SLA 72 h). Each queue entry shall be a `ReviewTask` with `assigned_to`, `due_at`, `status`, and the document's OCR, classification, extraction, and validation data attached.

### FR-17 — Review Task Assignment
Review tasks shall be assigned to reviewers based on role and document class. Medical records shall only be visible to `physician`, `nurse`, and `compliance_officer` roles (BR-06). Unassigned tasks shall be surfaced in a pool for self-assignment.

### FR-18 — Human Review Interface Data
The system shall expose via API: the rendered document pages (signed S3 URLs), extracted field values with confidence overlays, validation failure messages, and an editable field form. Corrections shall be stored as `ReviewDecision` records referencing the original `ExtractedField`.

### FR-19 — Review Completion and SLA Tracking
On review completion, all corrected fields shall update the document's extraction record with `source = HUMAN_CORRECTION`. Documents overdue (current time > `due_at`) shall be escalated: auto-reassigned to the queue manager and a notification sent. SLA breach events shall be emitted.

### FR-20 — Export to ERP
The system shall support export of approved documents to SAP via IDOC/RFC, Oracle via REST API, and generic endpoints via REST or SFTP. Each export shall produce a signed manifest (SHA-256 of payload) stored in `export_records`. Export requires `signed_manifest` and creates an `AuditLog` entry (BR-09).

### FR-21 — Export Filtering and Scheduling
Exports may be configured to run on a schedule (cron expression) or triggered on-demand. Filters available: `document_class`, `batch_id`, `date_range`, `status = APPROVED`.

### FR-22 — Audit Log
Every state transition for a document, every review decision, every export, every model inference, and every PII access shall produce an immutable `AuditLog` entry with: `entity_type`, `entity_id`, `event_type`, `actor_id`, `actor_role`, `timestamp`, `before_state`, `after_state`, `ip_address`.

### FR-23 — Template Management
Administrators shall be able to create, update, version, and deactivate extraction templates via the `/templates` API. Templates support field zone definitions in JSON. Template versions are immutable once used in production.

### FR-24 — Model Registry Integration
The system shall integrate with MLflow Model Registry. Each `ModelVersion` record shall store: `model_name`, `version`, `stage` (Staging | Production | Archived), `metrics` (F1, precision, recall), `training_dataset_id`, `artifact_uri`.

### FR-25 — Retraining Pipeline
The system shall support triggering a retraining job via `POST /models/retrain`. Retraining requires ≥ 500 validated samples per document class with ≥ 80% inter-annotator agreement (BR-08). The pipeline shall: sample training data, train model, evaluate on held-out test set, log to MLflow, and transition to Staging if F1 ≥ 0.92.

### FR-26 — Document Retention and Deletion
The system shall enforce retention policies: standard documents retained 7 years, medical records 10 years. At the end of the retention window, documents shall be queued for deletion. GDPR right-to-erasure requests shall delete PII fields for records outside mandatory retention windows (BR-04).

### FR-27 — Webhook Notifications
The system shall deliver webhook events to registered subscriber URLs for: `BatchReceived`, `OCRCompleted`, `ClassificationCompleted`, `ExtractionCompleted`, `ValidationFailed`, `ReviewCompleted`, `DocumentExported`. Delivery shall be retried up to 3 times with exponential backoff.

### FR-28 — Multi-Tenancy
The system shall enforce tenant isolation: all queries, storage paths, and API responses scoped to the authenticated tenant. Cross-tenant data access shall be prevented at the database row level using `tenant_id` predicates on all tables.

### FR-29 — Role-Based Access Control
The system shall enforce RBAC with roles: `admin`, `document_processor`, `human_reviewer`, `data_scientist`, `compliance_officer`, `physician`, `nurse`, `api_consumer`. Each API endpoint has a minimum required role documented in the API specification.

### FR-30 — Batch Status Polling and Webhooks
Clients shall be able to poll `GET /batches/{batch_id}` for status. The response shall include per-document status summary: total, queued, processing, completed, failed, in_review, exported.

### FR-31 — Page-Level OCR Granularity
The system shall process each page of a multi-page document independently. Page-level OCR results shall be accessible via `GET /documents/{id}/pages`. Page rotation correction shall be applied automatically when the detected angle exceeds 2 degrees.

### FR-32 — Extraction Schema Versioning
Each `ExtractionSchema` shall be versioned. When a template is updated, existing documents retain their extraction results linked to the schema version active at processing time.

### FR-33 — Confidence Score Aggregation
The system shall compute document-level confidence scores as the weighted average of OCR confidence (weight 0.3) and extraction field confidence (weight 0.7), excluding fields with `is_mandatory = false`.

### FR-34 — Language Detection
The system shall detect the primary language of each document using `langdetect`. Multi-language documents (confidence for a single language < 0.85) shall be flagged with `language = MULTI` and routed to specialized review.

### FR-35 — Classification Access Control
Documents classified as `medical_record` shall only be readable by users with roles `physician`, `nurse`, or `compliance_officer`. Attempts by other roles to retrieve classification or extraction results for medical records shall return HTTP 403 (BR-06).

---

## 3. Non-Functional Requirements

### NFR-01 — OCR Throughput
The system shall sustain ≥ 100 pages per minute OCR throughput under normal load (≤ 80% CPU utilization) measured over a 10-minute window. This requires horizontal scaling of the OCR worker pool.

### NFR-02 — Classification Accuracy
The document classification model shall achieve ≥ 95% macro-F1 score on the production holdout test set across all supported document classes. This metric shall be evaluated after each retraining cycle.

### NFR-03 — Extraction Accuracy
For critical fields (`invoice_total`, `tax_id`), the field-level extraction accuracy shall be ≥ 92% on validated ground truth. For standard fields, accuracy shall be ≥ 85%.

### NFR-04 — API Response Time (p99)
API endpoints for document status, review task retrieval, and export status shall respond within 500 ms at p99 under a load of 500 concurrent users.

### NFR-05 — Batch Ingestion Latency
From `POST /batches` submission to `DocumentQueued` event publication, the latency shall be ≤ 5 seconds for batches of up to 50 documents.

### NFR-06 — Availability
The system shall achieve 99.9% availability (≤ 8.7 hours downtime per year) for the API layer and review workflow. OCR processing has a relaxed SLA of 99.5% availability, with graceful degradation to Tesseract when cloud OCR providers are unavailable.

### NFR-07 — Data Durability
Document binaries stored in S3 shall have 11 nines (99.999999999%) durability via cross-region replication. Database backups shall be taken every 6 hours with point-in-time recovery enabled.

### NFR-08 — Security — Encryption
All data in transit shall use TLS 1.3. All data at rest shall use AES-256 encryption. PII fields (`ssn`, `dob`, `bank_account`) shall be additionally encrypted at the field level using a tenant-specific encryption key managed by AWS KMS or GCP KMS.

### NFR-09 — Security — Authentication
All API calls shall require a JWT bearer token issued by the IAM service with a maximum lifetime of 1 hour. Service-to-service calls shall use short-lived OIDC tokens (15-minute lifetime).

### NFR-10 — GDPR Compliance
The system shall support GDPR Articles 17 (right to erasure), 20 (data portability), and 30 (records of processing activities). PII erasure requests shall be processed within 30 days. Audit logs of erasure events shall be retained for 5 years.

### NFR-11 — HIPAA Compliance
Documents classified as `medical_record` shall be handled under HIPAA requirements: access restricted to authorized roles (BR-06), audit logs for every access, automatic logoff after 15 minutes of reviewer inactivity, and PHI encryption at rest and in transit.

### NFR-12 — Scalability
The system shall scale horizontally. OCR worker pods shall auto-scale (HPA) based on Kafka consumer lag: scale up when lag > 500 messages, scale down when lag < 50 messages. Maximum pod count: 50 OCR workers.

### NFR-13 — Observability
The system shall emit structured JSON logs (correlation ID on every log line), Prometheus metrics (throughput, error rate, latency histograms, queue depth, model inference time), and OpenTelemetry distributed traces for every document processing pipeline execution.

### NFR-14 — Disaster Recovery
RPO (Recovery Point Objective): ≤ 1 hour. RTO (Recovery Time Objective): ≤ 4 hours. Failover to a secondary region shall be automated using DNS failover and database replication.

### NFR-15 — Audit and Compliance Logging
Audit logs shall be append-only, cryptographically chained (each log entry includes the SHA-256 hash of the previous entry), and exported to a SIEM (Splunk/Elasticsearch) in real time. Log retention: 7 years minimum.

---

## 4. Constraints

| Constraint | Description |
|---|---|
| C-01 | Cloud OCR spend cap: $0.005 per page maximum (switch to Tesseract if exceeded) |
| C-02 | No training data leaves the tenant's cloud region (data residency) |
| C-03 | Model artifacts must be versioned in MLflow before deployment to production |
| C-04 | All exports to external ERPs require compliance officer approval for medical records |
| C-05 | Maximum document retention 10 years; no indefinite storage |

---

## 5. Assumptions

1. OCR providers (Textract, Vision API) are available with < 2% error rate in the target region.
2. PostgreSQL is used as the primary relational store; Redis for caching and task queuing.
3. The Kafka cluster is pre-provisioned with adequate partition count for target throughput.
4. ML model training infrastructure (GPU nodes) is available via Kubernetes node pools or managed ML services.
5. Tenant onboarding and IAM integration are handled by an external Identity and Access Management Platform.
