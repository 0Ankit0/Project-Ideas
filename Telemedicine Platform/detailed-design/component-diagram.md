# Component Diagrams — Telemedicine Platform

## Overview

This document captures the internal component structure of the four core backend services in the Telemedicine Platform: **VideoService**, **SchedulingService**, **PrescriptionService**, and **BillingService**. Each diagram maps responsibilities, intra-service dependencies, and external integration points.

Component boundaries are designed around the principle of **minimum necessary access**: no component holds more data or capabilities than required for its single purpose. All PHI-touching components route access through an `AuditEventPublisher` before any data leaves the service. External system adapters encapsulate protocol and credential details, keeping core business logic clean and independently testable.

Arrows are labeled with the semantic purpose of the relationship, not the transport protocol, except where the protocol itself is a security constraint (TLS, mTLS, HTTPS).

---

## VideoService Component Diagram

The VideoService owns the lifecycle of a video consultation session. It uses Amazon Chime SDK for managed WebRTC infrastructure, Redis for ephemeral session state, PostgreSQL for durable session records, and SQS/SNS for audit and domain event publication. Recording is consent-gated — the `RecordingManager` checks the patient's explicit recording consent flag before initiating any capture.

```mermaid
flowchart TD
    subgraph VideoService["VideoService — Internal Components"]
        SC["SessionController\nHTTP endpoints: join, end, status"]
        WM["WebSocketManager\nReal-time signaling channel"]
        CA["ChimeSDKAdapter\nAWS Chime SDK wrapper"]
        ICE["ICECandidateManager\nTURN/STUN coordination"]
        RM["RecordingManager\nConsent-gated S3 recording"]
        SCache["SessionStateCache\nRedis ephemeral state"]
        SRepo["SessionRepository\nPostgreSQL persistence"]
        AEP["AuditEventPublisher\nSQS HIPAA audit events"]
        NP["NotificationPublisher\nSNS domain events"]
        MC["MetricsCollector\nCloudWatch call quality"]
    end

    SC -->|"create / end meeting"| CA
    SC -->|"upgrade to WebSocket for signaling"| WM
    SC -->|"read + write ephemeral state"| SCache
    SC -->|"persist session record"| SRepo
    SC -->|"log every PHI access"| AEP
    SC -->|"emit ConsultationStarted / Ended"| NP
    WM -->|"relay ICE candidates"| ICE
    ICE -->|"request TURN credentials"| CA
    CA -->|"emit call quality metrics"| MC
    RM -->|"verify consent flag"| SRepo
    RM -->|"stream recording"| S3Ext["S3 Recordings Bucket\nKMS-encrypted"]

    CA -->|"HTTPS — meeting management"| ChimeExt["Amazon Chime SDK\nAWS Managed"]
    ICE -->|"HTTPS — media placement"| ChimeExt
    SCache -->|"TLS"| RedisExt["Redis\nElastiCache"]
    SRepo -->|"TLS"| PGExt["PostgreSQL\nAWS RDS"]
    AEP -->|"HTTPS"| SQSExt["SQS Audit Queue"]
    NP -->|"HTTPS"| SNSExt["SNS Events Topic"]
    MC -->|"HTTPS"| CWExt["CloudWatch"]
```

---

## SchedulingService Component Diagram

The SchedulingService coordinates appointment booking across multiple dimensions: provider availability calculation, double-booking prevention, insurance eligibility pre-checks, external calendar synchronisation, and automated patient reminders. It delegates eligibility verification to the BillingService via a dedicated HTTP client rather than replicating insurance logic.

```mermaid
flowchart TD
    subgraph SchedulingService["SchedulingService — Internal Components"]
        AC["AppointmentController\nHTTP endpoints"]
        AE["AvailabilityEngine\nSlot calculation logic"]
        CD["ConflictDetector\nOverlap and double-booking checks"]
        RS["ReminderScheduler\nAsync reminder job runner"]
        WL["WaitlistManager\nQueue and auto-promote logic"]
        AR["AppointmentRepository\nPostgreSQL persistence"]
        CSA["CalendarSyncAdapter\nGoogle / Apple Calendar"]
        IEC["InsuranceEligibilityClient\nHTTP → BillingService"]
        NP["NotificationPublisher\nSNS domain events"]
        AEP["AuditEventPublisher\nSQS HIPAA audit events"]
        TZ["TimezoneConverter\nIANA timezone database"]
    end

    AC -->|"compute available slots"| AE
    AC -->|"check for scheduling conflicts"| CD
    AC -->|"convert timestamps"| TZ
    AC -->|"pre-visit eligibility check"| IEC
    AC -->|"persist appointment record"| AR
    AC -->|"schedule reminder jobs"| RS
    AC -->|"add to waitlist if no slot"| WL
    AC -->|"sync to external calendar"| CSA
    AC -->|"emit AppointmentCreated / Cancelled"| NP
    AC -->|"log every PHI access"| AEP
    AE -->|"read provider schedule"| AR
    CD -->|"read existing appointments"| AR
    WL -->|"check availability before promote"| AE
    RS -->|"publish reminder notifications"| NP

    AR -->|"TLS"| PGExt["PostgreSQL\nAWS RDS"]
    IEC -->|"HTTPS / mTLS"| BillExt["BillingService API"]
    CSA -->|"OAuth2 / HTTPS"| GCalExt["Google Calendar API"]
    CSA -->|"OAuth2 / HTTPS"| ACalExt["Apple Calendar API"]
    NP -->|"HTTPS"| SNSExt["SNS Events Topic"]
    AEP -->|"HTTPS"| SQSExt["SQS Audit Queue"]
```

---

## PrescriptionService Component Diagram

The PrescriptionService manages the full e-prescription lifecycle: drug interaction screening, DEA schedule validation, state PDMP lookups for controlled substance history, insurance formulary checking, cryptographic signing of the prescription document, and transmission to pharmacies via the Surescripts network using the NCPDP SCRIPT standard.

```mermaid
flowchart TD
    subgraph PrescriptionService["PrescriptionService — Internal Components"]
        PCtrl["PrescriptionController\nHTTP endpoints"]
        DIC["DrugInteractionChecker\nNLM RxNorm API client"]
        PDMP["PDMPAdapter\nState PDMP gateway client"]
        DEA["DEAValidationService\nSchedule + DEA number logic"]
        FC["FormularyChecker\nPBM formulary API client"]
        SG["SurescriptsGateway\nNCPP SCRIPT transmitter"]
        CSM["ControlledSubstanceMonitor\nReporting rules engine"]
        PR["PrescriptionRepository\nPostgreSQL persistence"]
        SigSvc["SignatureService\nCryptographic signing + KMS"]
        AEP["AuditEventPublisher\nSQS HIPAA audit events"]
    end

    PCtrl -->|"drug-drug interaction check"| DIC
    PCtrl -->|"DEA number + schedule validation"| DEA
    PCtrl -->|"PDMP patient history lookup"| PDMP
    PCtrl -->|"formulary coverage check"| FC
    PCtrl -->|"cryptographic sign"| SigSvc
    PCtrl -->|"transmit to pharmacy"| SG
    PCtrl -->|"flag controlled substance rules"| CSM
    PCtrl -->|"persist prescription"| PR
    PCtrl -->|"log every access"| AEP
    DEA -->|"cross-reference PDMP history"| PDMP
    CSM -->|"read prescription history"| PR
    SigSvc -->|"store signed document"| PR

    DIC -->|"HTTPS"| NLMExt["NLM Drug Interaction API"]
    PDMP -->|"HTTPS / SFTP"| PDMPExt["State PDMP Systems"]
    SG -->|"HTTPS / EDI"| SuresExt["Surescripts Network"]
    FC -->|"HTTPS"| PBMExt["PBM Formulary API"]
    PR -->|"TLS"| PGExt["PostgreSQL\nAWS RDS"]
    AEP -->|"HTTPS"| SQSExt["SQS Audit Queue"]
```

---

## BillingService Component Diagram

The BillingService covers the full revenue cycle: real-time eligibility verification, CPT/ICD-10 coding, EDI 837 claim construction, clearinghouse submission via Availity, ERA (835) ingestion and payment posting, denial management with appeal workflows, and patient balance collection via Stripe.

```mermaid
flowchart TD
    subgraph BillingService["BillingService — Internal Components"]
        CCtrl["ClaimController\nHTTP endpoints"]
        EE["EligibilityEngine\nReal-time eligibility checks"]
        CPA["CPTCodeAssigner\nProcedure code mapping"]
        ICD["ICD10Mapper\nDiagnosis code lookup"]
        CB["ClaimBuilder\nEDI 837 generator"]
        AG["AvailityGateway\nClearinghouse HTTP client"]
        ERA["ERACleaner\n835 ERA processor"]
        DM["DenialManager\nDenial + appeal workflow"]
        PPS["PaymentPostingService\nEOB reconciliation"]
        SA["StripeAdapter\nPatient payment collection"]
        BR["BillingRepository\nPostgreSQL persistence"]
        AEP["AuditEventPublisher\nSQS HIPAA audit events"]
    end

    CCtrl -->|"real-time eligibility"| EE
    CCtrl -->|"assign CPT codes"| CPA
    CCtrl -->|"map ICD-10 codes"| ICD
    CPA -->|"build EDI 837 claim"| CB
    ICD -->|"build EDI 837 claim"| CB
    CB -->|"submit claim"| AG
    AG -->|"receive ERA 835"| ERA
    ERA -->|"route denial"| DM
    ERA -->|"post payment"| PPS
    DM -->|"resubmit corrected claim"| AG
    PPS -->|"collect patient balance"| SA
    CCtrl -->|"persist claim record"| BR
    ERA -->|"update claim status"| BR
    CCtrl -->|"log billing PHI access"| AEP

    AG -->|"HTTPS / X12 EDI"| AvailExt["Availity Clearinghouse"]
    EE -->|"HTTPS"| AvailExt
    SA -->|"HTTPS"| StripeExt["Stripe API"]
    BR -->|"TLS"| PGExt["PostgreSQL\nAWS RDS"]
    AEP -->|"HTTPS"| SQSExt["SQS Audit Queue"]
```

---

## Component Interaction Patterns

### Synchronous Calls

Components that require an immediate response before the request can continue use synchronous in-process calls or blocking HTTP with enforced timeouts and circuit breakers.

| Caller | Callee | Transport | Timeout | Circuit Breaker |
|--------|--------|-----------|---------|-----------------|
| AppointmentController | InsuranceEligibilityClient | HTTP / mTLS | 5 s | Half-open after 30 s |
| PrescriptionController | DrugInteractionChecker | HTTPS | 3 s | Half-open after 20 s |
| PrescriptionController | DEAValidationService | In-process | < 100 ms | N/A |
| PrescriptionController | FormularyChecker | HTTPS | 4 s | Half-open after 30 s |
| SessionController | ChimeSDKAdapter | In-process | 2 s | N/A |
| ClaimController | EligibilityEngine | In-process | 8 s | N/A |
| EligibilityEngine | AvailityGateway | HTTPS | 8 s | Half-open after 60 s |

### Asynchronous Events

Components that do not need to block the caller publish events to SNS/SQS. Consumers process events independently, allowing services to remain decoupled across failure boundaries.

| Publisher | Event Name | Primary Consumers |
|-----------|-----------|-------------------|
| AuditEventPublisher (all services) | `phi.accessed` | AuditService (SQS) |
| NotificationPublisher (Scheduling) | `appointment.created` | NotificationService |
| NotificationPublisher (Scheduling) | `appointment.cancelled` | NotificationService, VideoService |
| NotificationPublisher (Video) | `consultation.started` | BillingService |
| NotificationPublisher (Video) | `consultation.ended` | BillingService, MedicalRecordsService |
| ControlledSubstanceMonitor | `controlled.rx.issued` | ComplianceService |
| ERACleaner | `claim.paid` | AccountsReceivable ledger |
| ReminderScheduler | `appointment.reminder` | NotificationService |

---

## Component Failure Modes

| Component | Failure Mode | Service Impact | Recovery Strategy |
|-----------|-------------|----------------|-------------------|
| ChimeSDKAdapter | AWS Chime API timeout / 5xx | Video session cannot start | Circuit breaker opens; route to Twilio Video fallback via feature flag |
| SessionStateCache | Redis cluster unavailable | Higher latency; cache misses on every call | Degrade gracefully; fall back to SessionRepository reads; page on-call |
| AuditEventPublisher | SQS unavailable | PHI access cannot be recorded | **Fail-closed**: reject request with 503; write to local dead-letter file; trigger PagerDuty P1 |
| SessionRepository | PostgreSQL primary unavailable | Sessions cannot be persisted or retrieved | Return 503; retry with exponential backoff (3 attempts, jitter); fail open to read replica for reads |
| RecordingManager | S3 bucket unreachable | Recording cannot be stored | Allow call without recording; display in-session banner to both parties; log incident ticket |
| AvailityGateway | Clearinghouse down | Claims cannot be submitted | Queue claims in DenialManager retry queue; auto-retry at 1-hour intervals; alert billing team |
| SurescriptsGateway | Network failure | Prescription cannot be transmitted | Enqueue for manual fax fallback; alert prescribing physician via notification |
| DrugInteractionChecker | NLM API down | Interaction check unavailable | Fail-open with prominent prescriber warning banner; log unavailability in audit trail |
| PDMPAdapter | State system unreachable | PDMP history unavailable | Block controlled substance prescriptions (fail-closed); allow non-controlled; alert compliance officer |
| ConflictDetector | In-process exception | Risk of double-booking | Fail-closed: reject booking; log error; alert ops; do not degrade silently |
| InsuranceEligibilityClient | BillingService unreachable | Pre-visit eligibility unavailable | Allow booking with "eligibility pending" status; retry at appointment reminder time |
| FormularyChecker | PBM API timeout | Formulary coverage unknown | Warn prescriber; allow prescription with manual coverage note required |

---

## Testing Approach

### Unit Test Boundaries

Each component is tested in isolation with its direct collaborators mocked at the interface boundary.

| Component | Test Framework | Mocking Strategy |
|-----------|---------------|------------------|
| SessionController | Jest + Supertest | Mock ChimeSDKAdapter, SessionRepository, AuditEventPublisher |
| ChimeSDKAdapter | Jest | Mock `@aws-sdk/client-chime-sdk-meetings` with jest.mock |
| RecordingManager | Jest | Mock S3 client; mock SessionRepository consent flag |
| AuditEventPublisher | Jest | Mock SQS `SendMessageCommand`; assert message envelope schema |
| AvailabilityEngine | Jest | No mocks — pure function; use property-based tests with fast-check |
| DrugInteractionChecker | Jest + nock | Mock NLM HTTP response with fixture JSON |
| ClaimBuilder | Jest | Compare EDI 837 output against known-good fixture files |
| ICD10Mapper | Jest | Use embedded ICD-10 lookup table; no I/O |
| TimezoneConverter | Jest | DST edge cases with `@date-fns/tz`; no mocks needed |
| ConflictDetector | Jest | Pure function; exhaustive boundary test cases |
| SignatureService | Jest | Mock KMS `SignCommand`; verify signature format |

### Integration Test Boundaries

Integration tests use Docker Compose with real PostgreSQL and Redis, plus LocalStack for AWS services (SQS, SNS, S3, CloudWatch). External HTTP services (Surescripts, Availity, NLM, state PDMP systems) are stubbed with WireMock. All integration tests run in CI on every pull request to `main`.

Contract tests using Pact verify the HTTP interface between InsuranceEligibilityClient (SchedulingService) and the BillingService eligibility endpoint, ensuring schema compatibility is caught before integration deployment.
