# System Sequence Diagrams — Telemedicine Platform

## Overview

These sequence diagrams capture the primary interaction flows across the Telemedicine Platform, illustrating how actors, services, and external systems collaborate to deliver HIPAA-compliant telehealth workflows. Each diagram traces the happy path alongside error and edge-case branches, making the temporal ordering of messages explicit for both design validation and developer implementation guidance.

The platform is built on an event-driven microservices architecture deployed on AWS. All inter-service communication over the public internet uses TLS 1.3. PHI is never logged in plaintext; every audit record references encrypted content stored in the audit database.

---

## Video Consultation Setup (WebRTC Signaling)

This sequence covers the full lifecycle of a real-time video consultation, from a patient entering the waiting room through WebRTC ICE negotiation to session teardown and HIPAA audit logging.

```mermaid
sequenceDiagram
    autonumber
    actor PB as Patient Browser
    participant APIGW as API Gateway
    participant VS as VideoService
    participant TURN as TURN/STUN Server
    actor DB as Doctor Browser
    participant NS as NotificationService
    participant AS as AuditService

    PB->>+APIGW: POST /consultations/{id}/join (JWT)
    APIGW->>APIGW: Validate JWT, check appointment status
    APIGW->>+VS: JoinConsultation(consultationId, patientId)
    VS->>VS: Create Amazon Chime SDK meeting session
    VS->>VS: Generate short-lived meeting token (patient)
    VS-->>-APIGW: { meetingId, patientToken, turnCredentials }
    APIGW-->>-PB: 200 OK { meetingId, token, iceServers }

    VS->>+NS: NotifyDoctorConsultationReady(doctorId, consultationId)
    NS->>DB: Push notification (FCM/APNs) — "Patient is waiting"
    NS-->>-VS: ACK

    DB->>+APIGW: POST /consultations/{id}/join (JWT)
    APIGW->>APIGW: Validate JWT, verify doctor owns appointment
    APIGW->>+VS: JoinConsultation(consultationId, doctorId)
    VS->>VS: Generate short-lived meeting token (doctor)
    VS-->>-APIGW: { meetingId, doctorToken, turnCredentials }
    APIGW-->>-DB: 200 OK { meetingId, token, iceServers }

    PB->>+TURN: ICE candidate gathering (STUN BINDING REQUEST)
    TURN-->>-PB: Reflexive address / relay candidate

    DB->>+TURN: ICE candidate gathering (STUN BINDING REQUEST)
    TURN-->>-DB: Reflexive address / relay candidate

    PB->>DB: ICE candidate exchange via signaling channel (WebSocket)
    DB->>PB: ICE candidate exchange via signaling channel (WebSocket)

    PB->>DB: DTLS ClientHello (fingerprint in SDP)
    DB->>PB: DTLS ServerHello + Certificate
    PB->>DB: DTLS Finished — handshake complete
    Note over PB,DB: SRTP keys derived from DTLS handshake (E2EE)

    PB->>DB: SRTP Audio/Video stream
    DB->>PB: SRTP Audio/Video stream
    Note over PB,DB: Media flows peer-to-peer or via TURN relay

    VS->>+AS: AuditEvent(type=SESSION_START, consultationId, patientId, doctorId, timestamp)
    AS->>AS: Encrypt PHI fields, write to audit DB (write-once)
    AS-->>-VS: ACK

    PB->>+APIGW: POST /consultations/{id}/end (JWT)
    APIGW->>+VS: EndConsultation(consultationId, patientId)
    VS-->>-APIGW: ACK
    APIGW-->>-PB: 200 OK

    DB->>+APIGW: POST /consultations/{id}/end (JWT)
    APIGW->>+VS: EndConsultation(consultationId, doctorId)
    VS->>VS: Record session end time, duration, quality metrics
    VS-->>-APIGW: ACK
    APIGW-->>-DB: 200 OK

    VS->>+AS: AuditEvent(type=SESSION_END, consultationId, duration, endedBy)
    AS->>AS: Encrypt and persist audit record
    AS-->>-VS: ACK
```

**Notes:**
- Amazon Chime SDK handles media server coordination; TURN relay is used only when peer-to-peer ICE fails.
- DTLS-SRTP ensures end-to-end encryption of all audio and video; the platform's media servers cannot decrypt streams.
- Meeting tokens expire after 30 minutes and are tied to the specific `consultationId`.
- AuditService writes are asynchronous but guaranteed via SQS dead-letter queue retry.

---

## E-Prescription Workflow

This sequence covers the full e-prescribing flow initiated during a consultation, including controlled substance checks, PDMP queries, formulary validation, and Surescripts transmission.

```mermaid
sequenceDiagram
    autonumber
    actor DUI as Doctor UI
    participant APIGW as API Gateway
    participant PS as PrescriptionService
    participant DIS as DrugInteractionService
    participant PDMP as PDMPService
    participant SG as SurescriptsGateway
    participant PH as PharmacySystem
    participant PNS as PatientNotificationService

    DUI->>+APIGW: POST /prescriptions (JWT, rxDetails, consultationId)
    APIGW->>APIGW: Validate JWT, verify active consultation ownership
    APIGW->>+PS: CreatePrescription(rxDetails, doctorId, patientId)

    PS->>+DIS: CheckInteractions(drug, patientMedications, allergies)
    DIS->>DIS: Query drug-drug and drug-allergy databases
    DIS-->>-PS: InteractionResult { interactions[], severity }

    alt Critical interaction detected
        PS-->>APIGW: 422 { code: CRITICAL_INTERACTION, details }
        APIGW-->>DUI: 422 — doctor must review and override with justification
        DUI->>APIGW: POST /prescriptions (override=true, justification)
        APIGW->>PS: CreatePrescription(..., overrideJustification)
    end

    alt Drug is a controlled substance (DEA Schedule II–V)
        PS->>+PDMP: QueryPatientHistory(patientId, state, dateRange)
        PDMP->>PDMP: Query state PDMP database via PMPInterConnect
        PDMP-->>-PS: PDMPReport { priorControlledRx[], morphineEquivalents }
        PS->>PS: Evaluate MME thresholds and concurrent opioid prescriptions
        PS->>PS: Validate doctor DEA registration for patient's state
        PS->>PS: Validate state e-prescribing controlled substance (EPCS) license
    end

    PS->>PS: Apply formulary check via patient's PBM/insurance
    PS->>PS: Identify preferred alternatives if off-formulary

    PS-->>-APIGW: PrescriptionDraft { formularyTier, interactions, pdmpFlags }
    APIGW-->>-DUI: 200 OK — draft with warnings for review

    DUI->>+APIGW: POST /prescriptions/{id}/sign (JWT, electronicSignature)
    APIGW->>+PS: SignPrescription(prescriptionId, signature)
    PS->>PS: Validate EPCS two-factor authentication token
    PS->>PS: Attach qualified electronic signature (21 CFR Part 11)
    PS->>PS: Set status = SIGNED

    PS->>+SG: TransmitPrescription(ncpdpScriptMessage, pharmacyNcpdpId)
    Note over SG: NCPDP SCRIPT 10.6 / 2017071 standard
    SG->>+PH: NewRx transaction (TLS 1.3, encrypted payload)
    PH->>PH: Validate, queue for pharmacist review
    PH-->>-SG: RxFill acknowledgement (status=Received)
    SG-->>-PS: TransmitAck { ncpdpAckCode, pharmacyName, transmitTime }

    PS->>PS: Update status = TRANSMITTED, record transmitTime
    PS-->>-APIGW: ACK
    APIGW-->>-DUI: 200 OK { prescriptionId, status: TRANSMITTED }

    PS->>+PNS: NotifyPatient(patientId, prescriptionId, pharmacyInfo)
    PNS->>PNS: Send SMS + email via AWS SNS / SES
    PNS-->>-PS: ACK
```

**Notes:**
- EPCS (Electronic Prescribing of Controlled Substances) requires two-factor authentication per DEA 21 CFR Part 1311.
- PDMP queries are mandatory for Schedule II drugs in all 50 states; Schedule III–V varies by state law.
- Surescripts connectivity uses HTTPS with mutual TLS; all PHI is encrypted in transit.
- Formulary data is sourced from the patient's PBM in real time via a separate formulary API.

---

## Insurance Eligibility Check

This sequence shows the automated 270/271 eligibility verification triggered by appointment booking, ensuring patients understand their coverage and cost obligations before consultation.

```mermaid
sequenceDiagram
    autonumber
    participant SS as SchedulingService
    participant BS as BillingService
    participant AV as Availity Clearinghouse
    participant PAY as Payer System
    participant PNS as PatientNotificationService

    SS->>SS: AppointmentBooked event published to SNS
    SS->>+BS: EligibilityCheckRequest(patientId, insuranceInfo, appointmentDate, serviceType)

    BS->>BS: Build ASC X12 270 eligibility inquiry transaction
    BS->>+AV: Send 270 (subscriber, provider NPI, date of service)
    AV->>AV: Route to correct payer by payer ID
    AV->>+PAY: Forward 270 inquiry
    PAY->>PAY: Query member enrollment database
    PAY->>PAY: Calculate deductible, OOP max, copay for telehealth

    PAY-->>-AV: 271 eligibility response (active/inactive, benefit details)
    AV-->>-BS: 271 response (parsed coverage segments)

    BS->>BS: Parse EB segments: coverage status, deductible met, copay amount
    BS->>BS: Store EligibilityRecord(patientId, appointmentId, coverage, copay, deductible)
    BS-->>-SS: EligibilityResult { eligible, copay, deductibleRemaining, priorAuthRequired }

    SS->>SS: Update appointment record with coverage info and cost estimate
    SS->>SS: Flag if prior authorization required

    alt Patient is ineligible or coverage inactive
        SS->>+PNS: NotifyPatient(patientId, type=INELIGIBLE, alternatives)
        PNS->>PNS: Send SMS/email: "Insurance inactive — self-pay options: $X"
        PNS-->>-SS: ACK
    else Prior authorization required
        SS->>+PNS: NotifyPatient(patientId, type=PRIOR_AUTH_REQUIRED)
        PNS->>PNS: Send SMS/email with prior auth instructions
        PNS-->>-SS: ACK
    else Patient is eligible
        SS->>+PNS: NotifyPatient(patientId, type=ELIGIBLE, copay, deductible)
        PNS->>PNS: Send appointment confirmation with cost estimate
        PNS-->>-SS: ACK
    end
```

**Notes:**
- Eligibility checks run automatically at booking and again 24 hours before the appointment.
- The 270/271 transaction set is the HIPAA-mandated standard for eligibility verification.
- Copay amounts displayed to patients are estimates; final amounts depend on provider claim adjudication.
- All EDI transactions are logged to the AuditService with the payer response archived for 7 years.

---

## Emergency Escalation Sequence

This sequence covers the detection and handling of a medical emergency identified during a video consultation, including 911 dispatch and family notification.

```mermaid
sequenceDiagram
    autonumber
    actor DR as Doctor UI
    participant APIGW as API Gateway
    participant ES as EmergencyService
    participant GeoSvc as GeoLocationService
    participant Dispatch as 911 CAD System
    participant NS as NotificationService
    participant AS as AuditService
    actor PT as Patient

    DR->>+APIGW: POST /consultations/{id}/escalate (JWT, { reason, type: CARDIAC_EVENT })
    APIGW->>APIGW: Validate JWT, confirm active consultation
    APIGW->>+ES: InitiateEscalation(consultationId, doctorId, escalationType, reason)

    ES->>+GeoSvc: GetPatientLocation(patientId)
    GeoSvc->>GeoSvc: Retrieve last known address + GPS if mobile consent given
    GeoSvc-->>-ES: GeoLocation { address, coordinates, confidence }

    ES->>ES: Create EscalationRecord (status=DISPATCHING)
    ES->>+Dispatch: Dispatch911(location, patientInfo, chiefComplaint, consultingPhysician)
    Note over Dispatch: Integration via NG911 ESInet or CAD API
    Dispatch->>Dispatch: Create incident, assign nearest unit
    Dispatch-->>-ES: DispatchAck { incidentId, estimatedArrival, unitId }

    ES->>ES: Update EscalationRecord (status=DISPATCHED, incidentId, eta)

    ES->>+NS: NotifyEmergencyContacts(patientId, escalationId, location, hospital)
    NS->>NS: Send SMS to all emergency contacts on file
    NS-->>-ES: ACK

    ES->>+NS: NotifyDoctor(doctorId, escalationId, dispatchEta, instructions)
    NS->>NS: Send push + in-app alert to doctor
    NS-->>-ES: ACK

    ES->>+AS: AuditEvent(type=EMERGENCY_ESCALATION, consultationId, patientId, location, dispatched=true)
    AS->>AS: Write immutable audit record (encrypted PHI)
    AS-->>-ES: ACK

    ES-->>-APIGW: EscalationResponse { escalationId, status: DISPATCHED, eta }
    APIGW-->>-DR: 200 OK { escalationId, dispatchEta, incidentId }

    Note over DR,PT: Doctor maintains video connection until EMS arrives if patient is conscious

    Dispatch->>ES: StatusUpdate(incidentId, status=ON_SCENE)
    ES->>ES: Update EscalationRecord (status=EMS_ON_SCENE)
    ES->>+NS: NotifyDoctor(doctorId, type=EMS_ARRIVED)
    NS-->>-ES: ACK

    ES->>+AS: AuditEvent(type=EMS_ON_SCENE, escalationId, timestamp)
    AS-->>-ES: ACK
```

**Notes:**
- Emergency escalation is a fire-and-forget pattern with guaranteed delivery via SQS; it does not block the doctor's UI.
- Patient location is obtained from the registration address; GPS coordinates require explicit mobile consent.
- The care transition document (CCD/CDA) is automatically generated and sent to the receiving hospital's EHR.
- All escalation actions are HIPAA-audited and cannot be deleted or modified (write-once audit database).

---

## Sequence Diagram Conventions

### Actor and Participant Notation

| Symbol | Meaning |
|---|---|
| `actor` | Human user or external organization |
| `participant` | Software service or system component |
| `autonumber` | Sequential step numbers for traceability |
| `+` / `-` on arrow | Activation box — service is processing |
| `Note over` | Contextual annotation for a group of participants |
| `alt / else / end` | Conditional branching (if/else logic) |
| `loop` | Repeated interaction (polling, retries) |
| `par` | Parallel execution blocks |

### Timing Assumptions

| Flow | SLA | Timeout |
|---|---|---|
| JWT validation at API Gateway | < 5 ms | 500 ms |
| WebRTC ICE gathering | < 2 s | 10 s |
| DTLS handshake | < 500 ms | 5 s |
| Drug interaction check | < 200 ms | 3 s |
| PDMP query | < 3 s | 10 s |
| Surescripts transmission | < 5 s | 30 s |
| 270/271 eligibility round-trip | < 10 s | 30 s |
| 911 dispatch acknowledgement | < 5 s | 15 s |

### HIPAA Audit Requirements

Every sequence that touches PHI triggers an audit event to the AuditService. Audit records include:
- `userId` of the accessor (encrypted)
- `resourceType` and `resourceId`
- `action` (READ, WRITE, TRANSMIT, DELETE)
- `timestamp` (UTC, millisecond precision)
- `ipAddress` (hashed)
- `justification` (for break-glass access)

Audit records are written to a PostgreSQL table with row-level deletion disabled at the database role level, satisfying HIPAA §164.312(b) audit control requirements.

### Error Handling Convention

All sequence diagrams show the happy path. Error branches follow these patterns:
- **4xx client errors** — returned synchronously to the calling actor with a structured error body.
- **5xx service errors** — retried via SQS with exponential backoff (max 3 retries); unresolved failures go to the DLQ and trigger a PagerDuty alert.
- **Timeout errors** — the calling service applies circuit-breaker logic (Resilience4j); degraded-mode responses are returned where clinically safe (e.g., eligibility check failure falls back to self-pay flow, never blocks care).
