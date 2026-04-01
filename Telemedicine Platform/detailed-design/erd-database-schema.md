# Telemedicine Platform Entity Relationship Diagram & PostgreSQL Schema

This document defines the PostgreSQL database schema for the telemedicine platform, with emphasis on PHI (Protected Health Information) encryption, HIPAA compliance, and relational integrity for clinical workflows.

## Schema Overview

The schema is divided into five functional domains:
1. **Patient & Provider Management**: Core identity and credentials
2. **Appointments & Consultations**: Scheduling and clinical sessions
3. **Clinical Documentation**: SOAP notes, vital signs, lab/prescription orders
4. **Insurance & Billing**: Claims, eligibility, EOB tracking
5. **Security & Audit**: Encryption keys, audit logs, access controls

---

## 1. Patients Table

```sql
CREATE TABLE patients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Medical Record Number (MRN) - unique within health system
    mrn VARCHAR(50) NOT NULL UNIQUE,
    
    -- PII encrypted at rest (AES-256, encryption key in KMS)
    first_name_encrypted TEXT NOT NULL,
    last_name_encrypted TEXT NOT NULL,
    dob_encrypted TEXT NOT NULL,
    gender VARCHAR(20),
    
    -- Contact information encrypted
    phone_encrypted TEXT,
    email_encrypted TEXT,
    
    -- Address encrypted
    street_encrypted TEXT,
    city_encrypted TEXT,
    state VARCHAR(2),
    zip_encrypted VARCHAR(20),
    
    -- Insurance information
    insurance_id UUID REFERENCES insurance_payers(id) ON DELETE SET NULL,
    group_number_encrypted TEXT,
    member_id_encrypted TEXT,
    
    -- Emergency contact
    emergency_contact_name_encrypted TEXT,
    emergency_contact_phone_encrypted TEXT,
    
    -- Clinical metadata
    primary_language VARCHAR(50) DEFAULT 'en',
    preferred_pronouns VARCHAR(50),
    
    -- HIPAA compliance
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    consent_to_contact_date TIMESTAMPTZ,
    
    INDEX idx_patients_mrn (mrn),
    INDEX idx_patients_state (state),
    INDEX idx_patients_insurance_id (insurance_id)
);

COMMENT ON TABLE patients IS 'Patient demographics with PHI encrypted per HIPAA Security Rule § 164.312(a)(2)(ii).';
COMMENT ON COLUMN patients.first_name_encrypted IS 'Encrypted under KMS key patient_pii_key. Decryption available only to authenticated clinicians with viewing privilege.';
COMMENT ON COLUMN patients.dob_encrypted IS 'Encrypted date of birth; re-encrypted annually for key rotation per 45 CFR 164.312(e)(2)(ii).';
COMMENT ON COLUMN patients.consent_to_contact_date IS 'Date patient gave HIPAA-compliant consent to use email/SMS for appointment reminders.';
```

---

## 2. Doctors Table

```sql
CREATE TABLE doctors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Credentials
    npi VARCHAR(10) NOT NULL UNIQUE,
    dea_number_encrypted TEXT UNIQUE,
    medical_license_number_encrypted TEXT,
    
    -- Identity (not encrypted for provider directory)
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(20),
    
    -- License information
    license_states TEXT[] DEFAULT ARRAY[]::TEXT[],
    specialties TEXT[] DEFAULT ARRAY[]::TEXT[],
    board_certifications TEXT[] DEFAULT ARRAY[]::TEXT[],
    
    -- DEA scheduling authority (for controlled substance prescribing)
    dea_schedules_authorized TEXT[] DEFAULT ARRAY[]::TEXT[],
    
    -- Telemedicine registration per state regulations
    state_telehealth_registrations JSONB,  -- e.g. {"CA": {"registered": true, "registration_id": "..."}, ...}
    
    -- Calendar integration
    calendar_id VARCHAR(255),  -- AWS Chime Calendar ID or EHR system
    timezone VARCHAR(50) DEFAULT 'America/New_York',
    
    -- Practice information
    practice_name VARCHAR(255),
    npi_practice_name VARCHAR(255),
    
    -- Compliance flags
    is_active BOOLEAN DEFAULT true,
    background_check_date TIMESTAMPTZ,
    malpractice_insurance_verified_date TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_doctors_npi (npi),
    INDEX idx_doctors_email (email),
    INDEX idx_doctors_states (license_states)
);

COMMENT ON TABLE doctors IS 'Provider credentials and telemedicine licensing per state boards.';
COMMENT ON COLUMN doctors.dea_number_encrypted IS 'DEA registration number (Schedule I authority), encrypted for security. Verified against DEA CSOS annually.';
COMMENT ON COLUMN doctors.license_states IS 'Array of state abbreviations where provider holds active medical license. Telehealth limited to licensed states per §152.012 (TX telehealth).';
COMMENT ON COLUMN doctors.dea_schedules_authorized IS 'Controlled substance schedules (II, III, IV, V) authorized. Schedule I requires DEA research protocol.';
COMMENT ON COLUMN doctors.state_telehealth_registrations IS 'JSONB storing state-specific telemedicine registration IDs, renewal dates. Some states require registration to prescribe via telemedicine.';
```

---

## 3. Appointments Table

```sql
CREATE TABLE appointments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Foreign keys
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE RESTRICT,
    doctor_id UUID NOT NULL REFERENCES doctors(id) ON DELETE RESTRICT,
    
    -- Scheduling
    scheduled_at TIMESTAMPTZ NOT NULL,
    start_time TIMESTAMPTZ,
    end_time TIMESTAMPTZ,
    duration_minutes INT,
    timezone VARCHAR(50) DEFAULT 'America/New_York',
    
    -- Visit details
    visit_type VARCHAR(50) NOT NULL,  -- 'telehealth', 'in-person', 'hybrid'
    chief_complaint TEXT,  -- Patient's reason for visit (up to 500 chars)
    reason_for_visit VARCHAR(500),
    
    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'scheduled',
    -- statuses: scheduled, confirmed, waiting_room, in_session, completed, cancelled, no_show, abandoned
    
    -- Appointment cancellation metadata
    cancelled_at TIMESTAMPTZ,
    cancellation_reason VARCHAR(255),
    cancellation_reason_code VARCHAR(50),
    
    -- Reminders
    reminder_sent_at TIMESTAMPTZ,
    reminder_method VARCHAR(50),  -- 'email', 'sms', 'both'
    
    -- Insurance pre-authorization
    prior_auth_number VARCHAR(50),
    prior_auth_verified_at TIMESTAMPTZ,
    
    -- HIPAA compliance
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id UUID,
    
    INDEX idx_appointments_patient_id (patient_id),
    INDEX idx_appointments_doctor_id (doctor_id),
    INDEX idx_appointments_scheduled_at (scheduled_at),
    INDEX idx_appointments_status (status),
    INDEX idx_appointments_created_at (created_at)
);

COMMENT ON TABLE appointments IS 'Telemedicine appointment scheduling. Status transitions governed by state machine per detailed-design/state-machine-diagram.md.';
COMMENT ON COLUMN appointments.scheduled_at IS 'Appointment date/time in patient timezone. Converted to UTC for storage.';
COMMENT ON COLUMN appointments.chief_complaint IS 'Reason for visit, limited to unstructured text. ICD-10 diagnosis codes added post-visit in consultation record.';
COMMENT ON COLUMN appointments.prior_auth_number IS 'Prior authorization ID from insurance payer (if required). Used for claims submission.';
```

---

## 4. Consultations Table

```sql
CREATE TABLE consultations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Foreign key
    appointment_id UUID NOT NULL UNIQUE REFERENCES appointments(id) ON DELETE CASCADE,
    
    -- Video session metadata
    video_session_id VARCHAR(255),  -- AWS Chime conversation ID
    video_recording_s3_path VARCHAR(500),  -- s3://bucket/consultation_id.mp4
    video_recording_encrypted BOOLEAN DEFAULT true,
    
    -- Clinical documentation (SOAP note) - encrypted
    soap_note_encrypted TEXT,
    assessment_encrypted TEXT,
    plan_encrypted TEXT,
    
    -- Clinical coding
    icd10_codes TEXT[] DEFAULT ARRAY[]::TEXT[],  -- e.g., {"E11.9", "J44.9"}
    cpt_codes TEXT[] DEFAULT ARRAY[]::TEXT[],    -- e.g., {"99213", "99214"} for visit complexity
    
    -- Consultation duration
    duration_seconds INT,
    
    -- Clinician signature (digital)
    signed_at TIMESTAMPTZ,
    signed_by UUID REFERENCES doctors(id) ON DELETE RESTRICT,
    signature_algorithm VARCHAR(50),  -- 'RSA-SHA256', 'ECDSA'
    
    -- Vital signs captured during session
    systolic_bp INT,
    diastolic_bp INT,
    heart_rate INT,
    temperature_c NUMERIC(5, 2),
    respiratory_rate INT,
    spo2 INT,
    weight_kg NUMERIC(6, 2),
    
    -- Assessment method
    assessment_method VARCHAR(100),  -- 'in-person', 'audio-only', 'video', 'async'
    
    -- Photo/document attachments
    attachment_count INT DEFAULT 0,
    has_photo_consent BOOLEAN,
    
    -- HIPAA compliance
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_consultations_appointment_id (appointment_id),
    INDEX idx_consultations_signed_by (signed_by),
    INDEX idx_consultations_icd10 (icd10_codes),
    INDEX idx_consultations_signed_at (signed_at)
);

COMMENT ON TABLE consultations IS 'Clinical documentation for a single telemedicine consultation. SOAP note encrypted per HIPAA Security Rule.';
COMMENT ON COLUMN consultations.soap_note_encrypted IS 'Subjective, Objective Assessment, Plan notes encrypted with consultation-specific key rotation.';
COMMENT ON COLUMN consultations.signed_at IS 'Timestamp of clinician''s digital signature. Signature attestation for medical-legal purposes.';
COMMENT ON COLUMN consultations.video_session_id IS 'AWS Chime conversation ID for video session retrieval and compliance recording.';
COMMENT ON COLUMN consultations.video_recording_encrypted IS 'Video recording encrypted at rest in S3. Encryption key managed by KMS.';
```

---

## 5. Vital Signs Table

```sql
CREATE TABLE vital_signs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Foreign key
    appointment_id UUID NOT NULL REFERENCES appointments(id) ON DELETE CASCADE,
    consultation_id UUID REFERENCES consultations(id) ON DELETE SET NULL,
    
    -- Measurement timestamp
    recorded_at TIMESTAMPTZ NOT NULL,
    
    -- Vital measurements
    systolic_bp INT,
    diastolic_bp INT,
    mean_arterial_pressure INT,
    heart_rate INT,
    rhythm VARCHAR(50),  -- 'regular', 'irregular', 'sinus', etc.
    
    temperature_c NUMERIC(5, 2),
    temperature_f NUMERIC(5, 2),
    
    respiratory_rate INT,
    oxygen_saturation_percent INT,
    
    weight_kg NUMERIC(6, 2),
    height_cm INT,
    bmi NUMERIC(5, 2),
    
    -- Device information
    source VARCHAR(100),  -- 'bluetooth_device', 'manual_entry', 'ehr_import', 'wearable'
    device_id VARCHAR(255),
    device_manufacturer VARCHAR(100),
    
    -- Quality assessment
    measurement_quality VARCHAR(50),  -- 'excellent', 'good', 'fair', 'poor'
    clinician_reviewed BOOLEAN DEFAULT false,
    
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_vital_signs_appointment_id (appointment_id),
    INDEX idx_vital_signs_recorded_at (recorded_at),
    INDEX idx_vital_signs_consultation_id (consultation_id)
);

COMMENT ON TABLE vital_signs IS 'Vital sign measurements captured during or before telemedicine consultation.';
COMMENT ON COLUMN vital_signs.source IS 'Origin of measurement: bluetooth-connected device (BP cuff), manual entry by patient/clinician, EHR system import, or wearable.';
```

---

## 6. Prescriptions Table

```sql
CREATE TABLE prescriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Foreign key
    consultation_id UUID NOT NULL REFERENCES consultations(id) ON DELETE RESTRICT,
    
    -- Medication details
    medication_name VARCHAR(255) NOT NULL,
    medication_rxnorm_code VARCHAR(20),
    
    -- Dosage
    dose_value NUMERIC(10, 2),
    dose_unit VARCHAR(50),  -- 'mg', 'ml', 'units', etc.
    frequency VARCHAR(100),  -- 'once daily', 'twice daily', 'as needed', etc.
    route VARCHAR(50),  -- 'oral', 'intramuscular', 'transdermal', etc.
    
    -- DEA scheduling (for controlled substances)
    dea_schedule VARCHAR(5),  -- 'I', 'II', 'III', 'IV', 'V'
    dea_authorization_required BOOLEAN,
    
    -- Prescription details
    quantity INT NOT NULL,
    refills_allowed INT DEFAULT 0,
    days_supply INT,
    
    -- Pharmacy routing
    pharmacy_ncpdp_id VARCHAR(50),
    pharmacy_name VARCHAR(255),
    pharmacy_phone VARCHAR(20),
    
    -- E-Prescription (EPCS) information
    epcs_eligible BOOLEAN DEFAULT true,
    epcs_transmission_method VARCHAR(50),  -- 'surescripts', 'fax', 'print'
    
    -- Status tracking
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    -- statuses: draft, signed, transmitted, failed, dispensed, expired, voided
    
    signed_at TIMESTAMPTZ,
    transmitted_at TIMESTAMPTZ,
    dispensed_at TIMESTAMPTZ,
    voided_at TIMESTAMPTZ,
    expiration_date DATE,
    
    -- Drug interaction checks
    interaction_check_performed BOOLEAN DEFAULT false,
    interaction_alerts_dismissed_by_clinician BOOLEAN DEFAULT false,
    
    -- HIPAA compliance
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_prescriptions_consultation_id (consultation_id),
    INDEX idx_prescriptions_status (status),
    INDEX idx_prescriptions_pharmacy_ncpdp_id (pharmacy_ncpdp_id),
    INDEX idx_prescriptions_dea_schedule (dea_schedule)
);

COMMENT ON TABLE prescriptions IS 'Medication prescriptions from telemedicine consultations, with EPCS (Electronic Prescriptions for Controlled Substances) support.';
COMMENT ON COLUMN prescriptions.dea_schedule IS 'For controlled substances (II-V), requires EPCS transmission and DEA number on prescription.';
COMMENT ON COLUMN prescriptions.epcs_transmission_method IS 'Surescripts NCPDP standard for e-Rx, or fax fallback for non-participating pharmacies.';
COMMENT ON COLUMN prescriptions.status IS 'Prescription state machine: draft → signed → transmitted → dispensed. Voided status used for revocation.';
```

---

## 7. Lab Orders Table

```sql
CREATE TABLE lab_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Foreign key
    consultation_id UUID NOT NULL REFERENCES consultations(id) ON DELETE RESTRICT,
    
    -- Lab order details
    test_names TEXT[] DEFAULT ARRAY[]::TEXT[],
    loinc_codes TEXT[] DEFAULT ARRAY[]::TEXT[],  -- LOINC codes for lab tests
    
    -- Lab provider
    lab_provider VARCHAR(255),
    lab_provider_clia_number VARCHAR(50),
    lab_npi VARCHAR(10),
    
    -- Order metadata
    order_date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    specimen_collection_date TIMESTAMPTZ,
    results_available_at TIMESTAMPTZ,
    
    -- Status
    status VARCHAR(50) DEFAULT 'ordered',  -- 'ordered', 'collected', 'processing', 'results_available', 'cancelled'
    
    -- Results
    results_received_at TIMESTAMPTZ,
    results_delivered_to_patient_at TIMESTAMPTZ,
    
    -- Digital document
    results_document_s3_path VARCHAR(500),
    results_encrypted BOOLEAN DEFAULT true,
    
    -- HIPAA compliance
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_lab_orders_consultation_id (consultation_id),
    INDEX idx_lab_orders_status (status)
);

COMMENT ON TABLE lab_orders IS 'Lab test orders initiated during telemedicine consultation.';
COMMENT ON COLUMN lab_orders.loinc_codes IS 'LOINC (Logical Observation Identifiers Names and Codes) for standardized lab result reporting.';
```

---

## 8. Insurance Payers Table

```sql
CREATE TABLE insurance_payers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Payer information
    payer_name VARCHAR(255) NOT NULL UNIQUE,
    payer_id_national VARCHAR(50),  -- NCPDP Payer ID
    
    -- Contact for claims
    claims_email VARCHAR(255),
    claims_phone VARCHAR(20),
    clearinghouse_name VARCHAR(255),
    
    -- EDI connectivity
    edi_processor_id VARCHAR(50),
    edi_transmission_method VARCHAR(50),  -- 'sftp', 'api', 'hl7'
    
    -- Prior authorization
    prior_auth_required BOOLEAN DEFAULT false,
    prior_auth_contact_method VARCHAR(50),  -- 'phone', 'api', 'portal'
    prior_auth_url VARCHAR(500),
    
    -- Coverage determination
    requires_medical_necessity_review BOOLEAN DEFAULT false,
    telehealth_covered BOOLEAN DEFAULT true,
    
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_payers_name (payer_name)
);

COMMENT ON TABLE insurance_payers IS 'Insurance company/payer information for claims submission and eligibility verification.';
```

---

## 9. Insurance Claims Table

```sql
CREATE TABLE insurance_claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Foreign keys
    consultation_id UUID NOT NULL REFERENCES consultations(id) ON DELETE RESTRICT,
    payer_id UUID NOT NULL REFERENCES insurance_payers(id) ON DELETE RESTRICT,
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE RESTRICT,
    
    -- Claim identification
    claim_number VARCHAR(50),
    claim_reference_number VARCHAR(100),
    claim_submitter_id VARCHAR(50),  -- Tax ID or EIN of billing entity
    
    -- Claim details
    icd10_codes TEXT[] DEFAULT ARRAY[]::TEXT[],
    cpt_codes TEXT[] DEFAULT ARRAY[]::TEXT[],
    modifiers TEXT[] DEFAULT ARRAY[]::TEXT[],  -- e.g., '25' (significant, separately identifiable service)
    
    -- Billing amounts
    billed_amount NUMERIC(10, 2),
    allowed_amount NUMERIC(10, 2),
    deductible_applied NUMERIC(10, 2),
    coinsurance_patient_responsibility NUMERIC(10, 2),
    copay_applied NUMERIC(10, 2),
    paid_amount NUMERIC(10, 2),
    write_off_amount NUMERIC(10, 2),
    patient_balance NUMERIC(10, 2),
    
    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    -- statuses: draft, submitted, pending_review, approved, denied, paid, partially_paid, appealed, voided
    
    -- Submission and processing dates
    submitted_at TIMESTAMPTZ,
    edi_transmission_id VARCHAR(100),
    edi_837_file_path VARCHAR(500),
    
    -- Payer response
    eob_received_at TIMESTAMPTZ,
    eob_document_s3_path VARCHAR(500),
    
    -- Denial/approval
    approval_date TIMESTAMPTZ,
    denial_date TIMESTAMPTZ,
    denial_reason_code VARCHAR(50),
    denial_reason_text TEXT,
    medical_necessity_denial BOOLEAN DEFAULT false,
    
    -- Appeals
    appeal_submitted_at TIMESTAMPTZ,
    appeal_status VARCHAR(50),
    appeal_decision_date TIMESTAMPTZ,
    
    -- Payment
    payment_received_at TIMESTAMPTZ,
    remittance_advice_received_at TIMESTAMPTZ,
    remittance_advice_s3_path VARCHAR(500),
    
    -- HIPAA compliance
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_claims_consultation_id (consultation_id),
    INDEX idx_claims_payer_id (payer_id),
    INDEX idx_claims_patient_id (patient_id),
    INDEX idx_claims_status (status),
    INDEX idx_claims_submitted_at (submitted_at)
);

COMMENT ON TABLE insurance_claims IS 'Insurance claim submission and tracking per EDI 837/835 standards.';
COMMENT ON COLUMN insurance_claims.cpt_codes IS 'Current Procedural Terminology codes (e.g., 99213, 99214 for office visit complexity).';
COMMENT ON COLUMN insurance_claims.modifiers IS 'CPT modifiers indicating service context (25 = separate, identifiable service; 59 = distinct service).';
COMMENT ON COLUMN insurance_claims.edi_837_file_path IS 'Path to EDI 837 claim file submitted to clearinghouse or payer.';
COMMENT ON COLUMN insurance_claims.denial_reason_code IS 'NUBC claim adjustment group code and reason code (e.g., "4" = denial).';
```

---

## 10. Audit Logs Table

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Actor
    user_id UUID,
    user_email VARCHAR(255),
    user_role VARCHAR(50),  -- 'clinician', 'patient', 'admin', 'billing'
    
    -- Resource affected
    resource_type VARCHAR(100),  -- 'patient', 'appointment', 'consultation', 'prescription', 'claim'
    resource_id UUID,
    resource_patient_id UUID,
    
    -- Action
    action VARCHAR(100),  -- 'create', 'read', 'update', 'delete', 'sign', 'transmit'
    action_code VARCHAR(50),
    
    -- PHI access indicator
    phi_accessed BOOLEAN DEFAULT false,
    phi_field_accessed TEXT,  -- Specific PHI field (e.g., 'first_name', 'dob')
    phi_fields_accessed TEXT[] DEFAULT ARRAY[]::TEXT[],
    
    -- Network and location
    ip_address INET,
    user_agent VARCHAR(500),
    session_id VARCHAR(255),
    
    -- Details
    details JSONB,
    changes_before JSONB,
    changes_after JSONB,
    
    -- Compliance
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_audit_logs_user_id (user_id),
    INDEX idx_audit_logs_resource_type_id (resource_type, resource_id),
    INDEX idx_audit_logs_resource_patient_id (resource_patient_id),
    INDEX idx_audit_logs_phi_accessed (phi_accessed),
    INDEX idx_audit_logs_timestamp (timestamp),
    INDEX idx_audit_logs_action (action)
);

COMMENT ON TABLE audit_logs IS 'HIPAA-required access and modification logs for all PHI. Immutable append-only log. Retention: 6 years minimum per 45 CFR 164.530(j)(2).';
COMMENT ON COLUMN audit_logs.phi_accessed IS 'TRUE if this action accessed, modified, or deleted PHI. Used to identify access violations.';
COMMENT ON COLUMN audit_logs.resource_patient_id IS 'Patient ID whose data was accessed. Enables audit queries "who accessed patient X''s records?"';
COMMENT ON COLUMN audit_logs.details IS 'JSONB for detailed action context (e.g., search filters, export parameters).';
```

---

## 11. Encryption Keys Management

```sql
CREATE TABLE encryption_key_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Key metadata
    key_id VARCHAR(255) NOT NULL,
    key_name VARCHAR(255),
    key_rotation_date TIMESTAMPTZ,
    key_algorithm VARCHAR(50),  -- 'AES-256', 'RSA-4096'
    
    -- KMS information
    kms_key_arn VARCHAR(500),
    kms_provider VARCHAR(50),  -- 'aws', 'vault', 'azure'
    
    -- Access logs
    accessed_at TIMESTAMPTZ,
    accessed_by_service VARCHAR(100),  -- 'encryption_service', 'patient_api'
    
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_key_rotation (key_rotation_date)
);

COMMENT ON TABLE encryption_key_audit IS 'Track encryption key usage and rotations per HIPAA Security Rule § 164.312(e)(2)(ii).';
```

---

## 12. Entity Relationship Diagram (ERD)

```
patients (PK: id)
    ├─ insurance_id → insurance_payers (PK: id)
    ├─ appointments (FK: patient_id)
    │   ├─ doctor_id → doctors (PK: id)
    │   ├─ consultations (FK: appointment_id)
    │   │   ├─ signed_by → doctors (PK: id)
    │   │   ├─ prescriptions (FK: consultation_id)
    │   │   ├─ lab_orders (FK: consultation_id)
    │   │   └─ insurance_claims (FK: consultation_id)
    │   │       └─ payer_id → insurance_payers (PK: id)
    │   └─ vital_signs (FK: appointment_id)
    │       └─ consultation_id → consultations (FK: id)
    └─ audit_logs (FK: resource_patient_id)

doctors (PK: id)
    ├─ appointments (FK: doctor_id)
    ├─ consultations (FK: signed_by)
    └─ audit_logs (FK: user_id when clinician)

insurance_payers (PK: id)
    └─ insurance_claims (FK: payer_id)
    └─ patients (FK: insurance_id)
```

---

## 13. Indexing Strategy

All indexes are designed to support HIPAA audit queries and clinical workflows:

| Table | Index | Purpose |
|---|---|---|
| patients | idx_patients_mrn | Fast MRN lookup for chart access |
| patients | idx_patients_state | Filter patients by licensing state |
| appointments | idx_appointments_patient_id | Get patient's appointments |
| appointments | idx_appointments_doctor_id | Get doctor's schedule |
| appointments | idx_appointments_scheduled_at | Time-range queries |
| appointments | idx_appointments_status | Filter by status (no_show, completed) |
| consultations | idx_consultations_signed_at | Audit query: consultations signed by date |
| consultations | idx_consultations_icd10 | Epidemiologic queries (diagnoses) |
| prescriptions | idx_prescriptions_status | Track Rx transmission/dispensing |
| prescriptions | idx_prescriptions_dea_schedule | Controlled substance reporting |
| insurance_claims | idx_claims_status | AR aging reports |
| insurance_claims | idx_claims_submitted_at | Claims aging by submission date |
| audit_logs | idx_audit_logs_phi_accessed | HIPAA compliance: who accessed PHI? |
| audit_logs | idx_audit_logs_timestamp | Forensic analysis by date range |
| audit_logs | idx_audit_logs_action | Query by action type (delete, export) |

---

## 14. HIPAA Compliance Annotations

**Data Encryption**:
- All PHI columns (encrypted suffix) encrypted at rest with AES-256 via AWS KMS.
- Encryption keys rotated annually per § 164.312(e)(2)(ii).
- Decryption only allowed for authenticated clinicians with appropriate access privilege.

**Access Logging**:
- Every PHI access logged to audit_logs with user_id, timestamp, PHI field, action.
- Audit logs immutable and retained 6+ years per § 164.530(j)(2).

**Data Retention**:
- Patient records retained 6 years minimum per § 164.530(j) (most states require 7 years for minors).
- Video recordings auto-deleted after 7 years from consultation date.
- Audit logs archived to cold storage (S3 Glacier) after 2 years.

**Breach Notification**:
- Unauthorized access/modification of PHI triggers alert in audit logs.
- Breach response team notified within 1 hour via SNS.
- 60-day clock starts for breach notification per 45 CFR 164.404.

---

## 15. Foreign Key Constraints

All foreign keys use ON DELETE RESTRICT for PHI data (prevents accidental cascade deletions):

```sql
ALTER TABLE appointments ADD CONSTRAINT fk_appointments_patient 
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE RESTRICT;

ALTER TABLE consultations ADD CONSTRAINT fk_consultations_appointment 
    FOREIGN KEY (appointment_id) REFERENCES appointments(id) ON DELETE CASCADE;

ALTER TABLE prescriptions ADD CONSTRAINT fk_prescriptions_consultation 
    FOREIGN KEY (consultation_id) REFERENCES consultations(id) ON DELETE RESTRICT;

ALTER TABLE insurance_claims ADD CONSTRAINT fk_claims_consultation 
    FOREIGN KEY (consultation_id) REFERENCES consultations(id) ON DELETE RESTRICT;

ALTER TABLE audit_logs ADD CONSTRAINT fk_audit_resource 
    FOREIGN KEY (resource_patient_id) REFERENCES patients(id) ON DELETE CASCADE;
```

---

## 16. Partitioning Strategy (Optional, for large deployments)

For high-volume deployments, partition tables by date range:

```sql
-- Partition audit_logs by month for faster queries
CREATE TABLE audit_logs_2024_01 PARTITION OF audit_logs
    FOR VALUES FROM ('2024-01-01'::date) TO ('2024-02-01'::date);

-- Partition consultations by year
CREATE TABLE consultations_2024 PARTITION OF consultations
    FOR VALUES FROM ('2024-01-01'::timestamptz) TO ('2025-01-01'::timestamptz);
```

All partitions inherit indexes and constraints from parent table.
