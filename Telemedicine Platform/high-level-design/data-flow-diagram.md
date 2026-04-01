# Data Flow Diagrams — Telemedicine Platform

## Overview

These data flow diagrams (DFDs) document how information — particularly Protected Health Information (PHI) — moves through the Telemedicine Platform. Understanding data flows is a prerequisite for HIPAA Security Rule compliance (§164.308(a)(1)), enabling accurate risk analysis, gap assessment, and the correct placement of security controls.

### DFD Notation Used

| Shape | Meaning |
|---|---|
| Rectangle | External entity (actor or third-party system) |
| Rounded box | Process or service |
| Cylinder | Data store |
| Arrow | Data flow (direction = data movement direction) |
| `[PHI]` tag | Flow or store contains Protected Health Information |
| `[ENC]` tag | Data is encrypted at this point |
| `[AUD]` tag | Access is audited and logged |

All PHI flows cross HIPAA-covered boundaries only over TLS 1.3 with certificate pinning where mobile clients are involved. PHI at rest uses AES-256 with AWS KMS-managed keys. Every PHI store has row-level access controls enforced at the database role layer.

---

## PHI Data Flow

This diagram traces the complete lifecycle of PHI from initial patient input through storage, processing, and transmission to external covered entities.

```mermaid
flowchart TB
    subgraph Patients["External — Patients"]
        PT[Patient Browser / Mobile App]
        PT_INPUT[Patient-entered PHI\nname · DOB · SSN · symptoms]
    end

    subgraph IdP["Identity Layer"]
        AUTH0[Auth0 Identity Provider\nMFA enforced\nNo PHI stored]
        JWT_ISSUED[JWT with sub claim\nNo PHI in token payload]
    end

    subgraph API_Boundary["API Boundary — Public Subnet"]
        APIGW[AWS API Gateway\nWAF · Rate Limiting\nJWT Validation]
        KONG[Kong Gateway\nRequest Transformation\nRoute to Service]
    end

    subgraph CoreServices["Core Services — Private Subnet"]
        REGSVC[Registration Service\nPersonalInfo · InsuranceInfo\nPHI stored → encrypted]
        SCHSVC[Scheduling Service\nAppointment data\nCoverage info]
        CONSVC[Consultation Service\nSOAP Notes · Vitals\nDiagnoses · CPT codes]
        RXSVC[Prescription Service\nDrug · Dosage · Prescriber\nDEA Schedule]
        LABSVC[Lab Service\nTest orders · Results\nCritical value flags]
        EHRSVC[EHR Integration Service\nFHIR R4 adapter\nRecord sync]
        BILLSVC[Billing Service\nClaims · Coverage\nPayment records]
        AUDITSVC[Audit Service\nAccess logs · Events\nWrite-once store]
    end

    subgraph DataLayer["Data Layer — Private Subnet — All Encrypted AES-256"]
        PG_MAIN[(PostgreSQL RDS Multi-AZ\nPrimary PHI Store\nENC · AUD)]
        PG_AUDIT[(PostgreSQL Audit DB\nWrite-once rows\nENC · AUD)]
        S3_PHI[(S3 Bucket — PHI\nConsultation summaries\nLab reports · Recordings\nKMS SSE-C · ENC)]
        BACKUP[(RDS Automated Backups\nEncrypted snapshots\n35-day retention\nENC)]
        REDIS[(ElastiCache Redis\nSession state only\nNo persistent PHI\nTLS in-transit)]
    end

    subgraph ExternalCovered["External Covered Entities — BAA Required — TLS 1.3"]
        EHR_SYS[Epic / Cerner EHR\nHL7 FHIR R4\nPHI sync]
        PHARMACY[Surescripts Pharmacy Network\nNCPDP SCRIPT 2017071\nRx transmission]
        LAB_SYS[Quest / LabCorp LIS\nHL7 v2.5.1 / FHIR R4\nOrder + result]
        INSURER[Payer / Clearinghouse\nEDI 270/271 · 837P/835\nCoverage + claims]
    end

    PT -->|HTTPS — enter PHI| PT_INPUT
    PT_INPUT -->|HTTPS POST — register / update| APIGW
    PT -->|HTTPS — authenticate| AUTH0
    AUTH0 -->|OAuth 2.0 OIDC callback| JWT_ISSUED
    JWT_ISSUED -->|Bearer token| PT

    APIGW -->|Validated request — no raw PHI in logs| KONG
    KONG -->|Route to service| REGSVC
    KONG -->|Route to service| SCHSVC
    KONG -->|Route to service| CONSVC
    KONG -->|Route to service| RXSVC
    KONG -->|Route to service| LABSVC
    KONG -->|Route to service| BILLSVC

    REGSVC -->|Write PHI — TLS — field-level encryption| PG_MAIN
    SCHSVC -->|Read/Write appointment + coverage| PG_MAIN
    CONSVC -->|Write SOAP notes, vitals, diagnoses| PG_MAIN
    CONSVC -->|Store consultation summary PDF| S3_PHI
    RXSVC -->|Write prescription records| PG_MAIN
    LABSVC -->|Write orders, store result files| PG_MAIN
    LABSVC -->|Store lab result PDFs| S3_PHI
    BILLSVC -->|Write claim records, EOBs| PG_MAIN

    PG_MAIN -->|Automated backup — encrypted| BACKUP
    PG_MAIN -->|All access events| AUDITSVC
    S3_PHI -->|All object access events| AUDITSVC
    AUDITSVC -->|Write immutable audit records| PG_AUDIT

    EHRSVC -->|HL7 FHIR R4 GET/POST — TLS 1.3 — PHI| EHR_SYS
    EHR_SYS -->|FHIR R4 PUT resources — PHI| EHRSVC
    EHRSVC -->|Persist synced FHIR resources| PG_MAIN

    RXSVC -->|NCPDP SCRIPT NewRx — TLS 1.3 — PHI| PHARMACY
    PHARMACY -->|RxFill acknowledgement| RXSVC

    LABSVC -->|HL7 ORM Order message — TLS 1.3 — PHI| LAB_SYS
    LAB_SYS -->|HL7 ORU Result message — PHI| LABSVC

    BILLSVC -->|EDI 270 eligibility request — TLS 1.3| INSURER
    INSURER -->|EDI 271 eligibility response| BILLSVC
    BILLSVC -->|EDI 837P claim — TLS 1.3 — PHI| INSURER
    INSURER -->|EDI 835 ERA remittance| BILLSVC
```

---

## Video Stream Data Flow

Video consultation data flows through a separate path from PHI records. By design, no PHI is embedded in the media stream path; clinical notes and diagnoses remain in the core services layer.

```mermaid
flowchart TB
    subgraph PatientSide["Patient Side"]
        PT_DEVICE[Patient Device\nCamera · Microphone\nWebRTC Client]
        PT_ICE[ICE Agent — Patient\nGather host · srflx · relay\ncandidates]
    end

    subgraph DoctorSide["Doctor Side"]
        DR_DEVICE[Doctor Device\nCamera · Microphone\nWebRTC Client]
        DR_ICE[ICE Agent — Doctor\nGather host · srflx · relay\ncandidates]
    end

    subgraph SignalingPath["Signaling Channel — HTTPS / WSS"]
        WS_APIGW[API Gateway WebSocket\nRoute selection based on\nconsultationId]
        VS[Video Service\nChime SDK integration\nSession state management]
        SQS_VS[SQS — VideoService Queue\nAsync event delivery]
        REDIS_SIG[(Redis — Session State\nMeeting tokens\nICE state)]
    end

    subgraph STUNTURNServers["ICE Infrastructure"]
        STUN[STUN Server\nAWS hosted\nReflexive address discovery]
        TURN[TURN Server\nAWS hosted\nMedia relay — TLS]
    end

    subgraph MediaPath["Media Path — DTLS-SRTP End-to-End Encrypted"]
        DTLS_HANDSHAKE[DTLS 1.2 Handshake\nFingerprint verified via SDP\nSRTP keys derived]
        SRTP_STREAM[SRTP Audio/Video Streams\nE2E Encrypted\nNo platform decryption]
    end

    subgraph RecordingPath["Optional Recording — Consent Required"]
        CHIME_SDK[Amazon Chime SDK\nMedia Capture Pipeline\nActivated only on consent]
        S3_REC[(S3 — Encrypted Recordings\nKMS SSE-C per consultation\nDeleted after 90 days\nENC · AUD)]
        CONSENT_CHECK{Consent\nGranted?}
    end

    PT_DEVICE -->|SDP Offer via WebSocket| WS_APIGW
    WS_APIGW -->|Forward SDP| VS
    VS -->|Generate meeting token| REDIS_SIG
    VS -->|Return SDP Answer + ICE config| WS_APIGW
    WS_APIGW -->|SDP Answer| PT_DEVICE

    DR_DEVICE -->|SDP Offer via WebSocket| WS_APIGW
    WS_APIGW -->|Forward SDP| VS
    VS -->|Return SDP Answer + ICE config| WS_APIGW
    WS_APIGW -->|SDP Answer| DR_DEVICE

    PT_ICE -->|STUN BINDING REQUEST| STUN
    STUN -->|Reflexive address| PT_ICE
    DR_ICE -->|STUN BINDING REQUEST| STUN
    STUN -->|Reflexive address| DR_ICE

    PT_ICE -->|Candidate exchange via signaling| DR_ICE

    PT_ICE -->|If P2P fails — TURN ALLOCATE| TURN
    DR_ICE -->|If P2P fails — TURN ALLOCATE| TURN

    PT_DEVICE -->|DTLS ClientHello| DTLS_HANDSHAKE
    DR_DEVICE -->|DTLS ServerHello| DTLS_HANDSHAKE
    DTLS_HANDSHAKE -->|SRTP key material| SRTP_STREAM

    SRTP_STREAM -->|Encrypted audio/video — P2P or via TURN| PT_DEVICE
    SRTP_STREAM -->|Encrypted audio/video — P2P or via TURN| DR_DEVICE

    VS -->|ConsultationStarted event| SQS_VS

    VS -->|Check consent flag| CONSENT_CHECK
    CONSENT_CHECK -->|Yes — activate capture pipeline| CHIME_SDK
    CONSENT_CHECK -->|No — no recording| VS
    CHIME_SDK -->|Store encrypted recording| S3_REC
```

---

## Billing Data Flow

The billing data flow covers the complete revenue cycle from consultation completion through claim adjudication and patient payment collection.

```mermaid
flowchart TB
    subgraph TriggerEvent["Trigger"]
        CONSULT_END[ConsultationEnded Event\npublished to SNS]
    end

    subgraph BillingCore["Billing Service — Private Subnet"]
        BS_RECEIVE[BillingService\nConsumes ConsultationEnded\nvia SQS subscription]
        CPT_ASSIGN[CPT Code Assignment\nMap consultation type + duration\nto CPT codes 99201–99215]
        ICD_MAP[ICD-10-CM Mapping\nDiagnoses from SOAP notes\nPrimary + secondary codes]
        CLAIM_BUILD[Claim Assembly\nProvider NPI · Patient demographics\nDates of service · Place of service: 02 Telehealth]
        CLAIM_SCRUB[Claim Scrubbing\nEdit check rules\nPayer-specific edits\nCCI edits]
    end

    subgraph EligibilityFlow["Eligibility Flow — Pre-service"]
        ELIG_CHECK[Eligibility Check\nASC X12 270 request]
        AVAILITY[Availity Clearinghouse\nRoute to correct payer]
        PAYER_ELIG[Payer Eligibility System\nMember lookup]
        ELIG_RESP[271 Response\nCoverage · Deductible · Copay]
    end

    subgraph ClaimSubmission["Claim Submission — Post-service"]
        EDI_837[EDI 837P Transaction\nASC X12 5010 standard\nTLS 1.3]
        CLEARINGHOUSE[Availity Clearinghouse\nFormat validation\nRoute to payer]
        PAYER_ADJ[Payer Adjudication\nApply benefits · Contractual adjustment]
        EDI_835[EDI 835 ERA\nRemittance advice\nPayment details]
    end

    subgraph PatientBilling["Patient Billing — Out-of-Pocket"]
        COPAY_DUE[Copay / Balance Calculation\nAdjudicated amount minus payments]
        STRIPE[Stripe Payment Processor\nPCI-DSS Level 1\nNo card data on platform]
        STRIPE_CONFIRM[Payment Confirmation\nCharge · Receipt · Token]
        PT_PORTAL[Patient Portal\nStatement · Balance\nPayment history]
    end

    subgraph ClaimDataStore["Billing Data Store — Encrypted"]
        PG_BILLING[(PostgreSQL Billing DB\nClaims · Remittance\nPatient balances\nENC · AUD)]
        S3_EDI[(S3 — EDI Archive\nRaw 837P · 835 files\n7-year retention\nENC)]
    end

    CONSULT_END -->|Event consumed| BS_RECEIVE
    BS_RECEIVE -->|Fetch consultation details| CPT_ASSIGN
    CPT_ASSIGN -->|Assign procedure codes| ICD_MAP
    ICD_MAP -->|Add diagnosis codes| CLAIM_BUILD
    CLAIM_BUILD -->|Assembled claim| CLAIM_SCRUB
    CLAIM_SCRUB -->|Scrubbed claim| PG_BILLING

    ELIG_CHECK -->|270 request| AVAILITY
    AVAILITY -->|Route| PAYER_ELIG
    PAYER_ELIG -->|271 response| ELIG_RESP
    ELIG_RESP -->|Store coverage record| PG_BILLING

    CLAIM_SCRUB -->|Submit EDI 837P| EDI_837
    EDI_837 -->|Archive raw file| S3_EDI
    EDI_837 -->|Send to clearinghouse| CLEARINGHOUSE
    CLEARINGHOUSE -->|Forward to payer| PAYER_ADJ
    PAYER_ADJ -->|835 ERA response| EDI_835
    EDI_835 -->|Archive raw file| S3_EDI
    EDI_835 -->|Post payment — update claim| PG_BILLING

    PG_BILLING -->|Compute patient balance| COPAY_DUE
    COPAY_DUE -->|Initiate payment intent| STRIPE
    STRIPE -->|Charge patient card| STRIPE_CONFIRM
    STRIPE_CONFIRM -->|Update payment record| PG_BILLING
    PG_BILLING -->|Refresh patient statement| PT_PORTAL
```

---

## Audit and Compliance Data Flow

Every PHI access generates an audit event. This diagram shows how audit data flows from access points to long-term compliance archives and anomaly detection.

```mermaid
flowchart TB
    subgraph PHIAccessPoints["PHI Access Points"]
        SVC_LAYER[All Core Services\nScheduling · Video · Rx\nLab · Billing · EHR]
        DB_ACCESS[Database Repositories\nRow-level audit on\nPHI table access]
        S3_ACCESS[S3 Object Access\nServer-access logs\nfor PHI buckets]
        API_ACCESS[API Gateway Access Logs\nRequest metadata only\nNo PHI in logs]
    end

    subgraph AuditInterceptor["Audit Interceptor Layer"]
        INTERCEPTOR[Audit Interceptor\nAOP-based — TypeScript\ndecorates all PHI read/write]
        AUDIT_EVENT[AuditEvent struct\nuserID · resourceType\nresourceID · action\ntimestamp · ipHash\njustification]
        KMS_ENCRYPT[KMS Encryption\nEncrypt PHI fields\nin audit payload]
    end

    subgraph AuditStorage["Audit Storage — HIPAA §164.312(b)"]
        AUDIT_QUEUE[SQS — Audit Queue\nGuaranteed delivery\nDLQ for retries]
        AUDITSVC[Audit Service\nConsumes from SQS\nAppends to audit DB]
        PG_AUDIT[(PostgreSQL Audit DB\nWrite-once rows\nRow deletion disabled\n7-year retention\nENC · AUD)]
        CLOUDTRAIL[AWS CloudTrail\nAWS API-level audit\nAll KMS · S3 · RDS events]
        S3_AUDIT_ARCHIVE[(S3 — Audit Archive\nCompressed · signed\nGlacier after 90 days\nENC)]
    end

    subgraph SIEMLayer["SIEM and Monitoring"]
        CW_LOGS[CloudWatch Logs\nService logs\nNo PHI in log lines]
        OPENSEARCH[Amazon OpenSearch\nLog aggregation\nAnomaly detection queries]
        SIEM[SIEM — Splunk Cloud\nCorrelation rules\nThreat detection]
        ALERT[Security Alert\nPagerDuty · SNS\nSecurity team notification]
    end

    subgraph ComplianceReporting["Compliance and Reporting"]
        COMPLIANCE_RPT[Compliance Reports\nHIPAA audit trails\nAccess reports per patient]
        BREACH_DETECT[Breach Detection\nUnusual bulk access\nAfter-hours access patterns]
        OCR_EXPORT[OCR Export\nBusiness Associate audit\nPatient right-of-access]
    end

    SVC_LAYER -->|PHI read/write triggers interceptor| INTERCEPTOR
    DB_ACCESS -->|Query-level audit hooks| INTERCEPTOR
    S3_ACCESS -->|S3 access log → EventBridge| AUDIT_QUEUE
    API_ACCESS -->|Request logs → CloudWatch| CW_LOGS

    INTERCEPTOR -->|Build audit payload| AUDIT_EVENT
    AUDIT_EVENT -->|Encrypt PHI fields| KMS_ENCRYPT
    KMS_ENCRYPT -->|Publish to SQS| AUDIT_QUEUE

    AUDIT_QUEUE -->|Consume events| AUDITSVC
    AUDITSVC -->|Append — no updates/deletes| PG_AUDIT
    PG_AUDIT -->|Nightly export compressed| S3_AUDIT_ARCHIVE

    CLOUDTRAIL -->|API events| CW_LOGS
    CW_LOGS -->|Log forwarding| OPENSEARCH
    OPENSEARCH -->|Index and query| SIEM
    SIEM -->|Trigger on rule match| ALERT
    ALERT -->|Notify security team| BREACH_DETECT

    PG_AUDIT -->|Query for reports| COMPLIANCE_RPT
    COMPLIANCE_RPT -->|Generate access report| OCR_EXPORT
    BREACH_DETECT -->|Documented incident record| PG_AUDIT
```

---

## Data Classification

| Data Type | Classification | Encryption at Rest | Encryption in Transit | Retention Period | Access Control |
|---|---|---|---|---|---|
| Patient demographics (name, DOB, address) | PHI — Restricted | AES-256, KMS | TLS 1.3 | Life of record + 7 years | RBAC + audit |
| Social Security Number | PHI — Highly Restricted | AES-256, field-level | TLS 1.3 | Life of record + 7 years | Need-to-know only |
| Clinical notes (SOAP) | PHI — Restricted | AES-256, KMS | TLS 1.3 | 7 years (10 years for minors) | Treating team only |
| Prescription records | PHI — Restricted | AES-256, KMS | TLS 1.3 | 7 years (controlled: 10 years) | Prescriber + pharmacist |
| Lab results | PHI — Restricted | AES-256, KMS | TLS 1.3 | 7 years | Ordering provider + patient |
| Insurance / billing | PHI — Restricted | AES-256, KMS | TLS 1.3 | 7 years | Billing staff + patient |
| Audit log records | Compliance — Restricted | AES-256, KMS | TLS 1.3 | 7 years (HIPAA minimum) | Compliance team only |
| Video recordings (consented) | PHI — Restricted | AES-256, SSE-C | TLS 1.3 | 90 days (configurable) | Patient + treating doctor |
| JWT access tokens | Security — Internal | N/A (short-lived) | TLS 1.3 | 15-minute TTL | Bearer only |
| De-identified analytics | Internal | AES-256 | TLS 1.3 | Indefinite | Analytics team |
| System logs (no PHI) | Internal | Standard | TLS 1.3 | 90 days | DevOps team |

---

## PHI Inventory

The following PHI fields are present in the platform. Each field is tagged with the services that process it and the stores where it persists.

| PHI Field | HIPAA Identifier | Services | Stores |
|---|---|---|---|
| Patient full name | Name | Registration, Billing, Rx | PostgreSQL (patients table) |
| Date of birth | DOB | Registration, Billing, Rx | PostgreSQL (patients table) |
| Address | Geographic | Registration, Billing, Emergency | PostgreSQL (patients table) |
| Phone number | Phone | Registration, Notification | PostgreSQL (patients table) |
| Email address | Email | Registration, Notification | PostgreSQL (patients table) |
| Social Security Number | SSN | Registration (optional), Billing | PostgreSQL (patients table) — field-encrypted |
| Medical Record Number | MRN | All clinical services | PostgreSQL (patients table) |
| Health plan beneficiary number | Health plan | Billing | PostgreSQL (billing_eligibility table) |
| ICD-10 diagnosis codes | Diagnosis | Consultation, Billing, EHR | PostgreSQL (consultations, claims tables) |
| CPT procedure codes | Treatment | Consultation, Billing | PostgreSQL (consultations, claims tables) |
| Prescription details (drug, dose) | Rx | PrescriptionService | PostgreSQL (prescriptions table) |
| Lab results | Lab | LabService | PostgreSQL + S3 |
| SOAP clinical notes | Notes | ConsultationService | PostgreSQL (consultations table) |
| Video recordings | Audio/Video | VideoService | S3 (encrypted, consent-gated) |
| GPS location (emergency) | Location | EmergencyService | PostgreSQL (escalations table) — ephemeral |
| Payment card tokens | Financial | BillingService | Stripe (never stored on platform) |

---

## Data Minimization Principles

HIPAA's Minimum Necessary Standard (§164.514(d)) is applied to each data flow:

- **API responses** return only the fields required for the requesting client's function. Patient list responses include name and appointment time; full demographics are only returned in the patient profile view.
- **Service-to-service calls** pass identifiers (UUIDs) rather than PHI; downstream services fetch PHI from their own data stores when needed.
- **Notification payloads** contain no PHI. SMS/email notifications say "Your appointment is confirmed" — not the doctor's diagnosis or prescription details.
- **Audit event payloads** encrypt PHI fields before persisting; the audit record schema uses a reference (resourceId + resourceType) rather than embedded PHI values.
- **External transmissions** (Surescripts, HL7, EDI) include only the minimum data elements required by the interoperability standard for that transaction.
- **Logging configuration** explicitly suppresses PHI fields at the logger middleware level; request/response bodies containing PHI are never written to CloudWatch Logs.
- **Analytics and reporting** use de-identified data (Safe Harbor de-identification per §164.514(b)) with all 18 HIPAA identifiers removed or generalized.
