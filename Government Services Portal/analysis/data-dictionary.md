# Data Dictionary — Government Services Portal

## Overview

This data dictionary defines the canonical data structures for all primary entities in the Government Services Portal. Each entity includes field-level specifications covering data type, constraints, sensitivity classification, and regulatory notes.

**Data Sensitivity Classifications:**
- **Public** — No restrictions; safe to display without authentication.
- **Restricted** — Accessible to authorised users; logged on access.
- **Highly Sensitive PII** — NID, biometric, financial; encrypted at rest; access strictly controlled; NID Act/PDPA compliance mandatory.

---

## Entity: Citizen

| Field | Type | Max Length | Nullable | Unique | Sensitivity | Description |
|-------|------|-----------|----------|--------|-------------|-------------|
| `id` | UUID | — | No | Yes | Public | Internal primary key (UUID v4) |
| `citizen_id` | VARCHAR | 20 | No | Yes | Public | Human-readable ID (e.g., `CIT2024001234`) |
| `full_name` | VARCHAR | 200 | No | No | Restricted | Legal name from NID verification |
| `preferred_name` | VARCHAR | 100 | Yes | No | Restricted | Display name (editable by citizen) |
| `date_of_birth` | DATE | — | No | No | Highly Sensitive PII | From NID; used for age eligibility |
| `gender` | ENUM | — | No | No | Restricted | MALE / FEMALE / TRANSGENDER / PREFER_NOT_TO_SAY |
| `email` | VARCHAR | 255 | Yes | Yes (if set) | Restricted | Encrypted at rest; used for notifications |
| `phone_number` | VARCHAR | 15 | No | Yes | Restricted | NID-linked mobile; encrypted at rest |
| `alternate_phone` | VARCHAR | 15 | Yes | No | Restricted | Citizen-provided alternate contact |
| `address_line1` | VARCHAR | 255 | Yes | No | Restricted | From NID or self-declared |
| `address_line2` | VARCHAR | 255 | Yes | No | Restricted | Apartment, landmark |
| `city` | VARCHAR | 100 | Yes | No | Restricted | — |
| `district` | VARCHAR | 100 | Yes | No | Restricted | — |
| `province` | VARCHAR | 100 | Yes | No | Restricted | — |
| `pincode` | VARCHAR | 10 | Yes | No | Restricted | — |
| `account_status` | ENUM | — | No | No | Restricted | ACTIVE / SUSPENDED / PENDING_VERIFICATION / DELETED |
| `email_verified` | BOOLEAN | — | No | No | Restricted | — |
| `phone_verified` | BOOLEAN | — | No | No | Restricted | — |
| `aadhaar_verified` | BOOLEAN | — | No | No | Restricted | Set after successful NASC (National Identity Management Centre) OTP verification |
| `digilocker_linked` | BOOLEAN | — | No | No | Restricted | — |
| `profile_photo_url` | VARCHAR | 500 | Yes | No | Restricted | S3 pre-signed reference |
| `preferred_language` | VARCHAR | 10 | No | No | Public | ISO 639-1 code (default: `en`) |
| `created_at` | TIMESTAMP | — | No | No | Restricted | UTC timestamp |
| `updated_at` | TIMESTAMP | — | No | No | Restricted | — |
| `deleted_at` | TIMESTAMP | — | Yes | No | Restricted | Soft delete; PDPA erasure trigger |

**Indexes:** `citizen_id` (unique), `phone_number` (unique), `email` (unique, partial non-null), `province+district` (composite for geographic queries)

---

## Entity: CitizenIdentity

Stores NID verification evidence. Separate from Citizen to allow stricter access controls.

| Field | Type | Max Length | Nullable | Unique | Sensitivity | Description |
|-------|------|-----------|----------|--------|-------------|-------------|
| `id` | UUID | — | No | Yes | — | — |
| `citizen_id` | UUID | — | No | Yes | — | FK → Citizen.id (one-to-one) |
| `aadhaar_hash` | VARCHAR | 64 | No | Yes | Highly Sensitive PII | SHA-256(NID + platform_salt). Raw NID never stored |
| `aadhaar_last_four` | CHAR | 4 | No | No | Restricted | Last 4 digits for display only |
| `aadhaar_linked_name` | VARCHAR | 200 | No | No | Highly Sensitive PII | Name as returned by NASC (National Identity Management Centre); encrypted at rest |
| `aadhaar_linked_dob` | DATE | — | No | No | Highly Sensitive PII | DoB from NASC (National Identity Management Centre) response |
| `verification_timestamp` | TIMESTAMP | — | No | No | Restricted | UTC time of successful OTP verification |
| `uidai_transaction_id` | VARCHAR | 100 | No | No | Restricted | NASC (National Identity Management Centre) API transaction reference |
| `digilocker_oauth_token` | TEXT | — | Yes | No | Highly Sensitive PII | Encrypted OAuth refresh token for Nepal Document Wallet (NDW) |
| `digilocker_linked_at` | TIMESTAMP | — | Yes | No | Restricted | — |

**Access Policy:** Only accessible via CitizenIdentityService (not exposed via direct ORM queries in application code).

---

## Entity: ServiceDefinition

| Field | Type | Max Length | Nullable | Unique | Sensitivity | Description |
|-------|------|-----------|----------|--------|-------------|-------------|
| `id` | UUID | — | No | Yes | — | — |
| `service_code` | VARCHAR | 50 | No | Yes | Public | Unique department-assigned code (e.g., `RTO_DL_RENEWAL`) |
| `name` | VARCHAR | 200 | No | No | Public | Display name |
| `description` | TEXT | — | No | No | Public | Full description shown in catalog |
| `department_id` | UUID | — | No | No | Public | FK → Department.id |
| `category` | VARCHAR | 100 | No | No | Public | e.g., Transport, Health, Education |
| `jurisdiction_type` | ENUM | — | No | No | Public | NATIONAL / STATE / DISTRICT |
| `jurisdiction_value` | VARCHAR | 100 | Yes | No | Public | Province name or district name if jurisdiction is not national |
| `status` | ENUM | — | No | No | Public | DRAFT / PUBLISHED / SUSPENDED / ARCHIVED |
| `version` | INTEGER | — | No | No | Public | Incremented on each update |
| `base_fee` | DECIMAL(10,2) | — | No | No | Public | Fee before VAT (13%) |
| `gst_rate` | DECIMAL(5,2) | — | No | No | Public | Effective VAT (13%) rate at time of version |
| `fee_type` | ENUM | — | No | No | Public | FIXED / TIERED / FREE |
| `sla_working_days` | INTEGER | — | No | No | Public | Processing time in working days |
| `requires_field_visit` | BOOLEAN | — | No | No | Public | — |
| `bulk_processable` | BOOLEAN | — | No | No | Restricted | Whether bulk officer approval is permitted |
| `is_one_time_benefit` | BOOLEAN | — | No | No | Public | Prevent re-application after approval |
| `form_schema` | JSONB | — | No | No | Restricted | JSON Schema defining dynamic form fields |
| `eligibility_rules` | JSONB | — | Yes | No | Restricted | Rule engine configuration (JSON) |
| `required_documents` | JSONB | — | No | No | Public | List of required document types with constraints |
| `notification_templates` | JSONB | — | Yes | No | Restricted | Per-event SMS/email templates |
| `published_at` | TIMESTAMP | — | Yes | No | Public | — |
| `created_by` | UUID | — | No | No | Restricted | FK → DepartmentHead.id |
| `created_at` | TIMESTAMP | — | No | No | Restricted | — |

---

## Entity: Application

| Field | Type | Max Length | Nullable | Unique | Sensitivity | Description |
|-------|------|-----------|----------|--------|-------------|-------------|
| `id` | UUID | — | No | Yes | — | — |
| `arn` | VARCHAR | 30 | No | Yes | Public | Application Reference Number |
| `citizen_id` | UUID | — | No | No | Restricted | FK → Citizen.id |
| `service_id` | UUID | — | No | No | Public | FK → ServiceDefinition.id |
| `service_version` | INTEGER | — | No | No | Public | Captured form version at submission |
| `status` | ENUM | — | No | No | Restricted | See ApplicationStatus entity |
| `form_data` | JSONB | — | Yes | No | Highly Sensitive PII | Raw form responses (may contain PII) |
| `assigned_officer_id` | UUID | — | Yes | No | Restricted | FK → FieldOfficer.id |
| `assigned_at` | TIMESTAMP | — | Yes | No | Restricted | — |
| `sla_deadline` | DATE | — | Yes | No | Restricted | Working-day deadline |
| `submitted_at` | TIMESTAMP | — | Yes | No | Restricted | — |
| `approved_at` | TIMESTAMP | — | Yes | No | Restricted | — |
| `rejected_at` | TIMESTAMP | — | Yes | No | Restricted | — |
| `rejection_reason_code` | VARCHAR | 50 | Yes | No | Restricted | From predefined list |
| `rejection_remarks` | TEXT | — | Yes | No | Restricted | Officer free-text (min 50 chars) |
| `officer_internal_notes` | TEXT | — | Yes | No | Restricted | NOT exposed to citizen |
| `pending_info_deadline` | DATE | — | Yes | No | Restricted | Set when PENDING_INFO |
| `created_at` | TIMESTAMP | — | No | No | Restricted | — |
| `updated_at` | TIMESTAMP | — | No | No | Restricted | — |

**Indexes:** `arn` (unique), `citizen_id` (btree), `assigned_officer_id` (btree), `status` (btree), `sla_deadline` (btree for expiry queries)

---

## Entity: ApplicationStatus (Enum Reference)

| Value | Description | Actor Who Sets | Citizen Visible |
|-------|-------------|---------------|----------------|
| `DRAFT` | Saved but not submitted | Citizen (auto) | Yes |
| `PAYMENT_PENDING` | Awaiting fee payment | System (auto) | Yes |
| `SUBMITTED` | Submitted, awaiting assignment | System (auto) | Yes |
| `UNDER_REVIEW` | Assigned to and being reviewed by officer | System (auto) | Yes |
| `PENDING_INFO` | Officer requested additional information | Field Officer | Yes |
| `FIELD_VISIT_SCHEDULED` | Field visit required and scheduled | System | Yes |
| `FIELD_VISIT_COMPLETE` | Field visit conducted | Field Officer | Yes |
| `APPROVED` | Approved; certificate being generated | Field Officer / Dept Head | Yes |
| `CERTIFICATE_PENDING` | Certificate generation in progress / DSC pending | System | Yes (shown as "Processing") |
| `CERTIFICATE_ISSUED` | Certificate issued and available for download | System (auto) | Yes |
| `REJECTED` | Application rejected | Field Officer / Dept Head | Yes |
| `EXPIRED` | Draft or payment expired | System (auto) | Yes |
| `AUTO_CLOSED` | Citizen did not respond to PENDING_INFO | System (auto) | Yes |

---

## Entity: DocumentSubmission

| Field | Type | Max Length | Nullable | Unique | Sensitivity | Description |
|-------|------|-----------|----------|--------|-------------|-------------|
| `id` | UUID | — | No | Yes | — | — |
| `application_id` | UUID | — | No | No | Restricted | FK → Application.id |
| `document_type` | VARCHAR | 100 | No | No | Restricted | e.g., AADHAAR_CARD, INCOME_CERT, PHOTO |
| `source` | ENUM | — | No | No | Restricted | UPLOAD / DIGILOCKER |
| `file_name` | VARCHAR | 255 | No | No | Restricted | Original file name |
| `file_size_bytes` | INTEGER | — | No | No | Restricted | — |
| `mime_type` | VARCHAR | 100 | No | No | Restricted | application/pdf, image/jpeg, image/png |
| `s3_key` | VARCHAR | 500 | No | No | Highly Sensitive PII | S3 object key; never exposed directly to clients |
| `checksum_sha256` | CHAR | 64 | No | No | Restricted | For tamper detection |
| `scan_status` | ENUM | — | No | No | Restricted | PENDING / CLEAN / INFECTED / QUARANTINED |
| `scan_completed_at` | TIMESTAMP | — | Yes | No | Restricted | — |
| `officer_verified` | BOOLEAN | — | No | No | Restricted | Physical verification flag |
| `officer_verified_by` | UUID | — | Yes | No | Restricted | FK → FieldOfficer.id |
| `officer_verified_at` | TIMESTAMP | — | Yes | No | Restricted | — |
| `status` | ENUM | — | No | No | Restricted | ACTIVE / SUPERSEDED / DELETED |
| `digilocker_doc_id` | VARCHAR | 200 | Yes | No | Restricted | Nepal Document Wallet (NDW) document identifier |
| `digilocker_issued_on` | DATE | — | Yes | No | Restricted | Issue date from Nepal Document Wallet (NDW) metadata |
| `uploaded_at` | TIMESTAMP | — | No | No | Restricted | — |

---

## Entity: FeeInvoice

| Field | Type | Max Length | Nullable | Unique | Sensitivity | Description |
|-------|------|-----------|----------|--------|-------------|-------------|
| `id` | UUID | — | No | Yes | — | — |
| `invoice_number` | VARCHAR | 30 | No | Yes | Public | Format: `INV/{YYYY-MM}/{SEQ}` |
| `application_id` | UUID | — | No | Yes | Restricted | FK → Application.id (one-to-one per application) |
| `citizen_id` | UUID | — | No | No | Restricted | FK → Citizen.id |
| `base_amount` | DECIMAL(10,2) | — | No | No | Restricted | Pre-VAT (13%) fee |
| `gst_rate` | DECIMAL(5,2) | — | No | No | Restricted | Rate at invoice generation |
| `gst_amount` | DECIMAL(10,2) | — | No | No | Restricted | Calculated VAT (13%) |
| `total_amount` | DECIMAL(10,2) | — | No | No | Restricted | Base + VAT (13%) |
| `waiver_applied` | BOOLEAN | — | No | No | Restricted | — |
| `waiver_reason` | VARCHAR | 200 | Yes | No | Restricted | — |
| `waiver_approved_by` | UUID | — | Yes | No | Restricted | FK → DepartmentHead.id |
| `status` | ENUM | — | No | No | Restricted | UNPAID / PAID / EXPIRED / WAIVED / REFUNDED |
| `payment_deadline` | DATE | — | No | No | Restricted | Invoice date + 7 days |
| `paid_at` | TIMESTAMP | — | Yes | No | Restricted | — |
| `fee_schedule_version` | INTEGER | — | No | No | Restricted | Version of fee schedule used |
| `created_at` | TIMESTAMP | — | No | No | Restricted | — |

---

## Entity: PaymentTransaction

| Field | Type | Max Length | Nullable | Unique | Sensitivity | Description |
|-------|------|-----------|----------|--------|-------------|-------------|
| `id` | UUID | — | No | Yes | — | — |
| `invoice_id` | UUID | — | No | No | Restricted | FK → FeeInvoice.id |
| `paygov_order_id` | VARCHAR | 100 | No | Yes | Restricted | ConnectIPS-assigned order ID |
| `paygov_transaction_id` | VARCHAR | 100 | Yes | Yes | Restricted | ConnectIPS transaction reference (set on payment) |
| `payment_mode` | ENUM | — | No | No | Restricted | eSewa/Khalti/ConnectIPS / NET_BANKING / DEBIT_CARD / CREDIT_CARD / CHALLAN |
| `amount` | DECIMAL(10,2) | — | No | No | Restricted | Amount charged |
| `currency` | CHAR | 3 | No | No | Restricted | NPR |
| `status` | ENUM | — | No | No | Restricted | INITIATED / SUCCESS / FAILURE / REFUNDED / PENDING |
| `webhook_received_at` | TIMESTAMP | — | Yes | No | Restricted | Time ConnectIPS webhook was received |
| `webhook_signature_valid` | BOOLEAN | — | Yes | No | Restricted | — |
| `raw_webhook_payload` | JSONB | — | Yes | No | Restricted | Stored for audit/reconciliation |
| `initiated_at` | TIMESTAMP | — | No | No | Restricted | — |
| `completed_at` | TIMESTAMP | — | Yes | No | Restricted | — |

---

## Entity: Certificate

| Field | Type | Max Length | Nullable | Unique | Sensitivity | Description |
|-------|------|-----------|----------|--------|-------------|-------------|
| `id` | UUID | — | No | Yes | — | — |
| `certificate_number` | VARCHAR | 50 | No | Yes | Public | Format: `{DEPT}/{YYYY}/{SVC}/{SEQ}` |
| `application_id` | UUID | — | No | Yes | Restricted | FK → Application.id |
| `citizen_id` | UUID | — | No | No | Restricted | FK → Citizen.id |
| `service_id` | UUID | — | No | No | Public | FK → ServiceDefinition.id |
| `issued_by_officer_id` | UUID | — | No | No | Restricted | FK → FieldOfficer.id |
| `issue_date` | DATE | — | No | No | Public | — |
| `expiry_date` | DATE | — | Yes | No | Public | Null for lifetime certificates |
| `template_version` | INTEGER | — | No | No | Restricted | Certificate template version used |
| `s3_key` | VARCHAR | 500 | No | No | Restricted | S3 object key for PDF |
| `dsc_signature_ref` | VARCHAR | 255 | No | No | Restricted | DSC signature reference number |
| `qr_verification_url` | VARCHAR | 500 | No | No | Public | Public verification URL embedded in QR |
| `status` | ENUM | — | No | No | Public | ISSUED / REVOKED / EXPIRED |
| `revocation_reason` | TEXT | — | Yes | No | Restricted | — |
| `revoked_by` | UUID | — | Yes | No | Restricted | FK → DepartmentHead.id |
| `revoked_at` | TIMESTAMP | — | Yes | No | Restricted | — |
| `download_count` | INTEGER | — | No | No | Restricted | Total citizen downloads |
| `created_at` | TIMESTAMP | — | No | No | Restricted | — |

---

## Entity: Grievance

| Field | Type | Max Length | Nullable | Unique | Sensitivity | Description |
|-------|------|-----------|----------|--------|-------------|-------------|
| `id` | UUID | — | No | Yes | — | — |
| `grn` | VARCHAR | 30 | No | Yes | Public | Grievance Reference Number |
| `citizen_id` | UUID | — | No | No | Restricted | FK → Citizen.id |
| `application_id` | UUID | — | Yes | No | Restricted | FK → Application.id (optional link) |
| `department_id` | UUID | — | No | No | Restricted | FK → Department.id |
| `category` | ENUM | — | No | No | Restricted | REJECTION_DISPUTE / SERVICE_DELAY / OFFICER_CONDUCT / TECHNICAL / OTHER |
| `description` | TEXT | — | No | No | Restricted | 50–1000 characters |
| `status` | ENUM | — | No | No | Restricted | OPEN / ASSIGNED / IN_PROGRESS / PENDING_CITIZEN_INPUT / RESOLVED / ESCALATED / CLOSED |
| `assigned_to` | UUID | — | Yes | No | Restricted | FK → FieldOfficer.id or DepartmentHead.id |
| `assigned_at` | TIMESTAMP | — | Yes | No | Restricted | — |
| `sla_deadline` | DATE | — | No | No | Restricted | Filed date + 30 days |
| `resolution_notes` | TEXT | — | Yes | No | Restricted | Shared with citizen on RESOLVED |
| `internal_notes` | TEXT | — | Yes | No | Restricted | Not shared with citizen |
| `resolved_at` | TIMESTAMP | — | Yes | No | Restricted | — |
| `escalated_at` | TIMESTAMP | — | Yes | No | Restricted | — |
| `citizen_rating` | SMALLINT | — | Yes | No | Public | 1–5 satisfaction score |
| `filed_at` | TIMESTAMP | — | No | No | Restricted | — |

---

## Entity: FieldOfficer

| Field | Type | Max Length | Nullable | Unique | Sensitivity | Description |
|-------|------|-----------|----------|--------|-------------|-------------|
| `id` | UUID | — | No | Yes | — | — |
| `employee_id` | VARCHAR | 50 | No | Yes | Restricted | Government employee ID |
| `user_id` | UUID | — | No | Yes | Restricted | FK → User.id (Django auth) |
| `department_id` | UUID | — | No | No | Restricted | FK → Department.id |
| `full_name` | VARCHAR | 200 | No | No | Restricted | — |
| `designation` | VARCHAR | 100 | No | No | Restricted | — |
| `zone` | VARCHAR | 100 | Yes | No | Restricted | Geographic zone assignment |
| `role` | ENUM | — | No | No | Restricted | BASIC_OFFICER / SENIOR_OFFICER / GRIEVANCE_OFFICER |
| `dsc_certificate_ref` | VARCHAR | 255 | Yes | No | Restricted | Reference to DSC in certificate store |
| `dsc_expiry_date` | DATE | — | Yes | No | Restricted | Alert generated 30 days before expiry |
| `is_active` | BOOLEAN | — | No | No | Restricted | — |
| `last_login` | TIMESTAMP | — | Yes | No | Restricted | — |
| `created_at` | TIMESTAMP | — | No | No | Restricted | — |

---

## Entity: Department

| Field | Type | Max Length | Nullable | Unique | Sensitivity | Description |
|-------|------|-----------|----------|--------|-------------|-------------|
| `id` | UUID | — | No | Yes | — | — |
| `department_code` | VARCHAR | 20 | No | Yes | Public | e.g., `MH-RTO`, `GOI-MHA` |
| `name` | VARCHAR | 200 | No | No | Public | Full department name |
| `parent_department_id` | UUID | — | Yes | No | Public | FK → Department.id (self-referential hierarchy) |
| `type` | ENUM | — | No | No | Public | CENTRAL / STATE / DISTRICT |
| `province` | VARCHAR | 100 | Yes | No | Public | — |
| `district` | VARCHAR | 100 | Yes | No | Public | — |
| `head_officer_id` | UUID | — | Yes | No | Restricted | FK → User.id (department head) |
| `contact_email` | VARCHAR | 255 | Yes | No | Restricted | — |
| `is_active` | BOOLEAN | — | No | No | Public | — |
| `created_at` | TIMESTAMP | — | No | No | Restricted | — |

---

## Entity: AuditLog

| Field | Type | Max Length | Nullable | Unique | Sensitivity | Description |
|-------|------|-----------|----------|--------|-------------|-------------|
| `id` | BIGINT | — | No | Yes | — | Auto-increment sequence |
| `event_id` | UUID | — | No | Yes | Restricted | UUID per event (for correlation) |
| `timestamp` | TIMESTAMP | — | No | No | Restricted | UTC, microsecond precision |
| `actor_id` | UUID | — | No | No | Restricted | User ID (citizen or officer or system) |
| `actor_role` | VARCHAR | 50 | No | No | Restricted | CITIZEN / FIELD_OFFICER / DEPT_HEAD / SUPER_ADMIN / AUDITOR / SYSTEM |
| `action_type` | VARCHAR | 100 | No | No | Restricted | e.g., APPLICATION_SUBMITTED, CERTIFICATE_ISSUED |
| `entity_type` | VARCHAR | 100 | No | No | Restricted | e.g., Application, Certificate, Citizen |
| `entity_id` | UUID | — | No | No | Restricted | ID of the affected entity |
| `ip_address` | INET | — | Yes | No | Restricted | Client IP (masked after 90 days) |
| `user_agent` | TEXT | — | Yes | No | Restricted | Browser/device info |
| `change_delta` | JSONB | — | Yes | No | Restricted | Before/after values for update events |
| `chain_hash` | CHAR | 64 | No | No | Restricted | SHA-256 hash of (previous_hash + event_id + timestamp + actor_id + action_type) for tamper detection |
| `previous_hash` | CHAR | 64 | No | No | Restricted | Hash of the preceding AuditLog entry |

**Note:** AuditLog is append-only. No UPDATE or DELETE is permitted at the database level (enforced via DB trigger).

---

## Entity: Notification

| Field | Type | Max Length | Nullable | Unique | Sensitivity | Description |
|-------|------|-----------|----------|--------|-------------|-------------|
| `id` | UUID | — | No | Yes | — | — |
| `recipient_id` | UUID | — | No | No | Restricted | FK → Citizen.id or FieldOfficer.id |
| `recipient_type` | ENUM | — | No | No | Restricted | CITIZEN / OFFICER |
| `channel` | ENUM | — | No | No | Restricted | SMS / EMAIL / IN_PORTAL |
| `event_type` | VARCHAR | 100 | No | No | Restricted | e.g., APPLICATION_APPROVED, GRIEVANCE_FILED |
| `template_id` | VARCHAR | 100 | No | No | Restricted | Notification template reference |
| `content_rendered` | TEXT | — | No | No | Restricted | Final rendered message (PII masked for log) |
| `status` | ENUM | — | No | No | Restricted | QUEUED / SENT / DELIVERED / FAILED |
| `gateway_message_id` | VARCHAR | 200 | Yes | No | Restricted | Nepal Telecom / Sparrow SMS gateway / SES message ID |
| `sent_at` | TIMESTAMP | — | Yes | No | Restricted | — |
| `delivered_at` | TIMESTAMP | — | Yes | No | Restricted | — |
| `failure_reason` | VARCHAR | 500 | Yes | No | Restricted | — |
| `retry_count` | SMALLINT | — | No | No | Restricted | Default 0 |
| `created_at` | TIMESTAMP | — | No | No | Restricted | — |

---

## Operational Policy Addendum

### Section 1 — PII Field Handling
All fields classified as **Highly Sensitive PII** must be:
1. Encrypted at the application layer (AES-256 via Django's `encrypted-fields` library or equivalent) before being written to the database.
2. Excluded from Django model `__str__` representations to prevent accidental log leakage.
3. Masked in all API responses to roles below Super Admin (e.g., NID shown as `XXXX-XXXX-1234`).

### Section 2 — Database Schema Governance
1. Schema changes require a migration review by the data steward before deployment.
2. New PII fields must be declared in this data dictionary before the corresponding migration is approved.
3. Column renames or type changes to sensitive fields require an impact assessment across all API consumers.

### Section 3 — Data Lineage
Citizens can request a data lineage report showing every system that has processed their data, as required under PDPA 2023. The `AuditLog` entity is the system of record for this.

### Section 4 — Index and Performance Notes
High-traffic queries on `Application` table use partial indexes on `(status, sla_deadline)` for SLA monitoring and `(citizen_id, service_id)` for duplicate detection. Full-text search on service catalog uses PostgreSQL `GIN` index on `tsvector` column.
