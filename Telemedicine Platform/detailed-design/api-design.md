# API Design — Telemedicine Platform

## Overview

All APIs follow REST conventions and are versioned under the `/v1/` path prefix. Future breaking changes will be introduced under `/v2/` with a minimum 12-month deprecation window for `/v1/` endpoints. Non-breaking additions (new optional fields, new endpoints) are deployed in-place without version bumps.

Every endpoint returns `application/json`. Timestamps use ISO 8601 with UTC offset (`2025-07-04T14:30:00Z`). UUIDs are v4 and represented as lowercase hyphenated strings. Pagination uses cursor-based navigation via `nextCursor` / `prevCursor` fields in list responses to handle concurrent data changes without skipping records.

The base URL for all endpoints is `https://api.telemedicine.example.com`.

---

## Authentication & Authorization

All endpoints require a Bearer JWT issued by Auth0. Tokens are short-lived (15-minute expiry) and must be refreshed via the Auth0 `/oauth/token` refresh grant before expiry. The API gateway validates the JWT signature and expiry before routing the request.

**Scopes required per actor:**

| Actor | Granted Scopes |
|-------|---------------|
| Patient | `patient:read`, `patient:write` |
| Doctor | `patient:read`, `doctor:write`, `prescription:write` |
| Billing Staff | `patient:read`, `billing:write` |
| Admin | `patient:read`, `patient:write`, `admin:read`, `admin:write` |

**Rate limits:**

| Actor | Requests / minute | Burst |
|-------|-------------------|-------|
| Patient | 100 | 150 |
| Provider | 500 | 750 |
| Admin | 1 000 | 1 500 |
| Lab System (service account) | 2 000 | 3 000 |

**HIPAA Audit Header — required on every request that touches PHI:**

```
X-Audit-Context: {"purpose": "TREATMENT", "actorRole": "DOCTOR", "note": "Reviewing prior Rx before prescribing"}
```

Valid `purpose` values: `TREATMENT`, `PAYMENT`, `HEALTHCARE_OPERATIONS`, `PATIENT_REQUEST`, `REQUIRED_BY_LAW`. Requests missing this header on PHI endpoints are rejected with `400 MISSING_AUDIT_CONTEXT`.

---

## Appointments API

### GET /v1/appointments

List appointments. Patients see only their own; doctors see their own schedule; admins see all. Results are paginated (default page size 20, max 100).

| Field | Value |
|-------|-------|
| Auth Scope | `patient:read` |
| Query Params | `status` (scheduled\|confirmed\|cancelled\|completed), `from` (ISO date), `to` (ISO date), `doctorId` (admin only), `patientId` (admin/doctor), `cursor`, `limit` |

**Response 200:**
```json
{
  "data": [
    {
      "appointmentId": "a1b2c3d4-...",
      "patientId": "p1...",
      "doctorId": "d1...",
      "scheduledAt": "2025-08-01T10:00:00Z",
      "durationMinutes": 30,
      "type": "VIDEO",
      "status": "CONFIRMED",
      "chiefComplaint": "Follow-up for hypertension"
    }
  ],
  "nextCursor": "eyJpZCI6Ii4uLiJ9",
  "total": 142
}
```

**HIPAA Note:** Doctor querying another doctor's schedule without explicit admin role returns `403`. Patient field `chiefComplaint` is PHI and is logged on every access.

---

### POST /v1/appointments

Create a new appointment. Triggers an insurance eligibility pre-check and schedules reminder notifications.

| Field | Value |
|-------|-------|
| Auth Scope | `patient:write` |

**Request Body:**
```json
{
  "patientId": "p1b2c3d4-...",
  "doctorId": "d1e2f3a4-...",
  "scheduledAt": "2025-08-01T10:00:00Z",
  "durationMinutes": 30,
  "type": "VIDEO",
  "chiefComplaint": "Chest tightness since yesterday",
  "insuranceId": "ins-9f8e7d6c-..."
}
```

**Response 201:**
```json
{
  "appointmentId": "a9b8c7d6-...",
  "status": "PENDING_CONFIRMATION",
  "eligibilityStatus": "ELIGIBLE",
  "estimatedCopay": 25.00,
  "videoJoinUrl": "https://telehealth.example.com/join/a9b8c7d6"
}
```

**Error Codes:** `400 VALIDATION_ERROR`, `409 SLOT_CONFLICT`, `422 PATIENT_NOT_ELIGIBLE`, `422 PROVIDER_NOT_ACCEPTING`

---

### GET /v1/appointments/{appointmentId}

Retrieve full details of a single appointment including SOAP notes summary if the consultation is completed.

| Field | Value |
|-------|-------|
| Auth Scope | `patient:read` |
| Path Param | `appointmentId` — UUID |

**Response 200:**
```json
{
  "appointmentId": "a9b8c7d6-...",
  "patient": { "id": "p1...", "name": "Jane Doe", "dob": "1985-03-12" },
  "doctor": { "id": "d1...", "name": "Dr. Smith", "npi": "1234567890" },
  "scheduledAt": "2025-08-01T10:00:00Z",
  "status": "COMPLETED",
  "consultationId": "c3d4e5f6-...",
  "eligibilityStatus": "ELIGIBLE"
}
```

**Error Codes:** `404 APPOINTMENT_NOT_FOUND`, `403 ACCESS_DENIED`

---

### PATCH /v1/appointments/{appointmentId}

Update appointment status (confirm, cancel, reschedule). Reschedule triggers a new conflict check.

| Field | Value |
|-------|-------|
| Auth Scope | `patient:write` (cancel own), `doctor:write` (confirm) |

**Request Body:**
```json
{
  "action": "RESCHEDULE",
  "newScheduledAt": "2025-08-03T14:00:00Z",
  "cancellationReason": null
}
```

**Error Codes:** `409 SLOT_CONFLICT`, `422 APPOINTMENT_NOT_MODIFIABLE`, `422 CANCELLATION_WINDOW_EXPIRED`

---

### DELETE /v1/appointments/{appointmentId}

Cancel an appointment. Soft-delete only; record retained for HIPAA 6-year minimum. Triggers cancellation notifications and waitlist promotion.

| Field | Value |
|-------|-------|
| Auth Scope | `patient:write` |

**Response:** `204 No Content`

**Error Codes:** `404 APPOINTMENT_NOT_FOUND`, `422 CANNOT_CANCEL_ACTIVE_CONSULTATION`

---

### GET /v1/appointments/{appointmentId}/eligibility

Refresh the insurance eligibility check for a specific appointment using the latest insurance data from the payer.

| Field | Value |
|-------|-------|
| Auth Scope | `patient:read` |

**Response 200:**
```json
{
  "appointmentId": "a9b8c7d6-...",
  "eligibilityStatus": "ELIGIBLE",
  "payerName": "Aetna",
  "memberId": "AET-123456",
  "copayAmount": 25.00,
  "deductibleRemaining": 500.00,
  "checkedAt": "2025-07-04T09:00:00Z"
}
```

---

## Consultations API

### POST /v1/consultations/{consultationId}/join

Join an active video consultation. Returns Amazon Chime SDK meeting and attendee credentials. Valid only within 5 minutes before scheduled start and during active consultation window.

| Field | Value |
|-------|-------|
| Auth Scope | `patient:read` or `doctor:write` |

**Response 200:**
```json
{
  "consultationId": "c3d4e5f6-...",
  "meetingId": "chime-mtg-abc123",
  "attendeeId": "chime-att-xyz789",
  "joinToken": "eyJhbGci...",
  "webSocketEndpoint": "wss://signal.chime.aws/...",
  "turnCredentials": { "username": "u", "password": "p", "ttlSeconds": 1800 }
}
```

**Error Codes:** `403 NOT_A_PARTICIPANT`, `422 CONSULTATION_NOT_ACTIVE`, `422 JOIN_WINDOW_EXPIRED`

**HIPAA Note:** Join event logged with actor, consultation ID, IP address, and user agent.

---

### POST /v1/consultations/{consultationId}/end

End the active consultation. Doctor or patient may end. Triggers billing event, SOAP note reminder, and summary generation.

| Field | Value |
|-------|-------|
| Auth Scope | `doctor:write` |

**Response 200:**
```json
{
  "consultationId": "c3d4e5f6-...",
  "endedAt": "2025-08-01T10:31:45Z",
  "durationSeconds": 1905,
  "recordingAvailable": true
}
```

---

### PUT /v1/consultations/{consultationId}/notes

Save or update SOAP notes for the consultation. Doctor only. Notes are PHI and immutable after 24 hours (amendment workflow required).

| Field | Value |
|-------|-------|
| Auth Scope | `doctor:write` |

**Request Body:**
```json
{
  "subjective": "Patient reports chest tightness since yesterday evening...",
  "objective": "HR 88, BP 142/90, SpO2 98%",
  "assessment": "Hypertensive urgency, rule out ACS",
  "plan": "Increase lisinopril to 20mg. Refer to cardiology. Return if worsening."
}
```

**Error Codes:** `403 NOT_PRESCRIBING_DOCTOR`, `422 NOTES_LOCKED_FOR_AMENDMENT`

---

### PUT /v1/consultations/{consultationId}/vitals

Record vitals observed or reported during the consultation.

| Field | Value |
|-------|-------|
| Auth Scope | `doctor:write` |

**Request Body:**
```json
{
  "heartRateBpm": 88,
  "bloodPressureSystolic": 142,
  "bloodPressureDiastolic": 90,
  "temperatureCelsius": 37.1,
  "oxygenSaturationPct": 98,
  "weightKg": 82.5,
  "recordedAt": "2025-08-01T10:05:00Z"
}
```

---

### POST /v1/consultations/{consultationId}/escalate

Trigger an emergency escalation. Notifies the on-call emergency coordinator and dispatches to 911 if `dispatchEmergencyServices` is true.

| Field | Value |
|-------|-------|
| Auth Scope | `doctor:write` |

**Request Body:**
```json
{
  "severity": "CRITICAL",
  "reason": "Patient reporting crushing chest pain with radiation to left arm",
  "patientLocation": { "address": "123 Main St", "city": "Boston", "state": "MA", "zip": "02101" },
  "dispatchEmergencyServices": true
}
```

**Response 200:**
```json
{ "escalationId": "esc-...", "dispatchConfirmed": true, "coordinatorNotified": true }
```

---

### GET /v1/consultations/{consultationId}/summary

Retrieve the post-consultation summary including SOAP notes, vitals, prescriptions issued, lab orders, and follow-up plan.

| Field | Value |
|-------|-------|
| Auth Scope | `patient:read` |

**Response 200:**
```json
{
  "consultationId": "c3d4e5f6-...",
  "doctor": { "id": "d1...", "name": "Dr. Smith" },
  "completedAt": "2025-08-01T10:31:45Z",
  "soapNotes": { "subjective": "...", "plan": "..." },
  "vitals": { "heartRateBpm": 88 },
  "prescriptionsIssued": ["rx-abc123"],
  "labOrdersPlaced": ["lo-def456"],
  "followUpRecommended": true,
  "followUpInDays": 14
}
```

---

## Prescriptions API

### POST /v1/prescriptions

Create a new prescription. Triggers drug-interaction check, formulary check, and PDMP lookup. Doctor only.

| Field | Value |
|-------|-------|
| Auth Scope | `prescription:write` |

**Request Body:**
```json
{
  "consultationId": "c3d4e5f6-...",
  "ndcCode": "00093-7233-56",
  "drugName": "Lisinopril 20mg",
  "dosageInstructions": "Take 1 tablet by mouth once daily",
  "quantity": 30,
  "daysSupply": 30,
  "refills": 2,
  "isControlled": false,
  "deaSchedule": null,
  "pharmacyId": "pharm-abc123"
}
```

**Response 201:**
```json
{
  "prescriptionId": "rx-abc123-...",
  "status": "DRAFT",
  "interactionAlerts": [],
  "formularyStatus": "PREFERRED",
  "estimatedPatientCost": 4.50
}
```

**Error Codes:** `422 DRUG_INTERACTION_CRITICAL`, `422 CONTROLLED_REQUIRES_DEA`, `422 PDMP_CHECK_BLOCKED`

---

### GET /v1/prescriptions/{prescriptionId}

Retrieve full prescription details including current status and transmission history.

| Field | Value |
|-------|-------|
| Auth Scope | `patient:read` |

**Error Codes:** `404 PRESCRIPTION_NOT_FOUND`, `403 ACCESS_DENIED`

---

### POST /v1/prescriptions/{prescriptionId}/sign

Cryptographically sign the prescription. For Schedule II-V controlled substances, triggers DEA two-factor authentication before signing.

| Field | Value |
|-------|-------|
| Auth Scope | `prescription:write` |

**Request Body:**
```json
{
  "doctorNpi": "1234567890",
  "deaNumber": "AS1234563",
  "twoFactorCode": "847291"
}
```

**Response 200:**
```json
{
  "prescriptionId": "rx-abc123-...",
  "status": "SIGNED",
  "signedAt": "2025-08-01T10:20:00Z",
  "signatureHash": "sha256:e3b0c44298fc1c149afbf4c8..."
}
```

**Error Codes:** `422 DEA_VALIDATION_FAILED`, `422 PDMP_THRESHOLD_EXCEEDED`, `422 PRESCRIPTION_ALREADY_SIGNED`

---

### POST /v1/prescriptions/{prescriptionId}/transmit

Transmit the signed prescription to the designated pharmacy via Surescripts (NCPDP SCRIPT 2017071).

| Field | Value |
|-------|-------|
| Auth Scope | `prescription:write` |

**Response 200:**
```json
{
  "prescriptionId": "rx-abc123-...",
  "status": "TRANSMITTED",
  "transmittedAt": "2025-08-01T10:21:00Z",
  "pharmacyNcpdpId": "5831234",
  "surescriptsMessageId": "SS-MSG-789XYZ"
}
```

**Error Codes:** `422 PRESCRIPTION_NOT_SIGNED`, `503 SURESCRIPTS_UNAVAILABLE`

---

### POST /v1/prescriptions/{prescriptionId}/cancel

Cancel a prescription that has not yet been transmitted. Transmitted prescriptions require a separate cancellation request via Surescripts CancelRx.

| Field | Value |
|-------|-------|
| Auth Scope | `prescription:write` |

**Error Codes:** `422 CANNOT_CANCEL_TRANSMITTED_RX`

---

### GET /v1/patients/{patientId}/prescriptions

Retrieve paginated prescription history for a patient. Includes all statuses. Doctors see full history; patients see their own.

| Field | Value |
|-------|-------|
| Auth Scope | `patient:read` |
| Query Params | `status`, `isControlled`, `from`, `to`, `cursor`, `limit` |

---

## Lab Orders API

### POST /v1/lab-orders

Create a lab order for a patient. Doctor only. Order is routed to the designated lab system via HL7 ORM message.

| Field | Value |
|-------|-------|
| Auth Scope | `doctor:write` |

**Request Body:**
```json
{
  "consultationId": "c3d4e5f6-...",
  "loincCodes": ["2093-3", "2085-9"],
  "testNames": ["Total Cholesterol", "HDL Cholesterol"],
  "priority": "ROUTINE",
  "labId": "lab-quest-001",
  "specimenInstructions": "Fasting 12 hours required"
}
```

---

### GET /v1/lab-orders/{orderId}

Retrieve a lab order including results when available. Results include LOINC code, value, unit, reference range, and abnormal flag.

| Field | Value |
|-------|-------|
| Auth Scope | `patient:read` |

---

### GET /v1/patients/{patientId}/lab-orders

Retrieve paginated lab order history for a patient.

| Field | Value |
|-------|-------|
| Auth Scope | `patient:read` |
| Query Params | `status` (ordered\|resulted\|reviewed), `from`, `to`, `cursor`, `limit` |

---

### POST /v1/lab-orders/{orderId}/results

Receive lab results from a lab system callback. Service account only. Triggers notification to ordering physician.

| Field | Value |
|-------|-------|
| Auth Scope | `lab:write` (service account) |

**Request Body:**
```json
{
  "results": [
    {
      "loincCode": "2093-3",
      "value": "195",
      "unit": "mg/dL",
      "referenceRange": "< 200 mg/dL",
      "abnormalFlag": "N",
      "resultedAt": "2025-08-02T08:15:00Z"
    }
  ]
}
```

---

## Insurance Claims API

### POST /v1/insurance-claims

Submit a billing claim. Billing staff only. Assembles CPT and ICD-10 codes from the consultation, generates EDI 837, and submits to the payer via Availity.

| Field | Value |
|-------|-------|
| Auth Scope | `billing:write` |

**Request Body:**
```json
{
  "consultationId": "c3d4e5f6-...",
  "renderingProviderId": "d1...",
  "placeOfService": "02",
  "cptCodes": ["99214"],
  "icd10Codes": ["I10", "Z87.891"],
  "chargeAmount": 180.00
}
```

---

### GET /v1/insurance-claims/{claimId}

Get current claim status including payer adjudication decision and ERA details.

| Field | Value |
|-------|-------|
| Auth Scope | `billing:write` |

---

### POST /v1/insurance-claims/{claimId}/appeal

Submit a formal appeal for a denied claim with supporting documentation.

| Field | Value |
|-------|-------|
| Auth Scope | `billing:write` |

**Request Body:**
```json
{
  "appealReason": "MEDICAL_NECESSITY",
  "supportingDocuments": ["doc-uuid-1", "doc-uuid-2"],
  "notes": "Patient met criteria per CMS LCD L37166"
}
```

---

### POST /v1/insurance/eligibility

Real-time eligibility check against a payer. Can be called independently of an appointment.

| Field | Value |
|-------|-------|
| Auth Scope | `billing:write` |

**Request Body:**
```json
{
  "memberId": "AET-123456",
  "payerId": "60054",
  "serviceDate": "2025-08-01",
  "serviceTypeCode": "98"
}
```

---

## Medical Records API

### GET /v1/patients/{patientId}/records

List all medical record entries for a patient. Implements HIPAA right of access. Patients access own records; providers access records for active care relationships only.

| Field | Value |
|-------|-------|
| Auth Scope | `patient:read` |

---

### GET /v1/patients/{patientId}/records/{recordId}

Retrieve a specific medical record entry (consultation note, lab result, prescription, imaging report).

| Field | Value |
|-------|-------|
| Auth Scope | `patient:read` |

---

### POST /v1/patients/{patientId}/records/export

Request a FHIR R4 Bundle export of the patient's complete record. Asynchronous — returns a job ID; patient receives download link via email when ready (within 24 hours per HIPAA access request rules).

| Field | Value |
|-------|-------|
| Auth Scope | `patient:read` |

**Request Body:**
```json
{ "format": "FHIR_R4", "dateRange": { "from": "2020-01-01", "to": "2025-07-04" } }
```

**Response 202:**
```json
{ "exportJobId": "export-job-abc123", "estimatedReadyAt": "2025-07-04T22:00:00Z" }
```

---

### POST /v1/patients/{patientId}/records/share

Share a portion of the patient's record with an external provider. Requires a valid patient consent token. Generates a time-limited, scoped access URL.

| Field | Value |
|-------|-------|
| Auth Scope | `patient:write` |

**Request Body:**
```json
{
  "consentTokenId": "consent-xyz-...",
  "recipientNpi": "9876543210",
  "recordTypes": ["CONSULTATION_NOTES", "LAB_RESULTS"],
  "expiresInHours": 72
}
```

---

## Error Response Schema

All error responses use this envelope:

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Appointment a9b8c7d6 not found or access denied",
    "details": { "field": "appointmentId", "value": "a9b8c7d6-..." },
    "correlationId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "timestamp": "2025-07-04T14:30:00Z"
  }
}
```

| HTTP Status | Error Code | Meaning |
|-------------|-----------|---------|
| 400 | `VALIDATION_ERROR` | Request body or query param failed schema validation |
| 400 | `MISSING_AUDIT_CONTEXT` | `X-Audit-Context` header missing on PHI endpoint |
| 401 | `TOKEN_EXPIRED` | JWT has expired; client must refresh |
| 401 | `INVALID_TOKEN` | JWT signature invalid or malformed |
| 403 | `INSUFFICIENT_SCOPE` | JWT scope does not permit this operation |
| 403 | `ACCESS_DENIED` | Caller does not have a care relationship with this patient |
| 404 | `RESOURCE_NOT_FOUND` | Entity does not exist or is not visible to caller |
| 409 | `SLOT_CONFLICT` | Appointment slot is already taken |
| 422 | `BUSINESS_RULE_VIOLATION` | Request is valid but violates a domain rule (see `code` for specifics) |
| 429 | `RATE_LIMIT_EXCEEDED` | Too many requests; retry after `Retry-After` header value |
| 500 | `INTERNAL_ERROR` | Unexpected server error; include `correlationId` when reporting |
| 503 | `SERVICE_UNAVAILABLE` | Downstream dependency unavailable; retry with backoff |

---

## HIPAA Audit Logging Requirements

Every request that accesses, creates, modifies, or deletes PHI generates an immutable audit record written to the SQS audit queue and consumed by the centralised AuditService. The audit log is stored in a dedicated append-only S3 bucket with Object Lock enabled (WORM, 6-year retention) per HIPAA §164.312(b) and §164.316(b)(2).

**Minimum audit record fields (HIPAA §164.312(b)):**

| Field | Type | Description |
|-------|------|-------------|
| `eventId` | UUID v4 | Unique identifier for this audit record |
| `timestamp` | ISO 8601 UTC | Exact time of the access |
| `actorId` | string | Authenticated user ID (sub claim from JWT) |
| `actorRole` | string | `PATIENT`, `DOCTOR`, `BILLING_STAFF`, `ADMIN` |
| `action` | string | `READ`, `CREATE`, `UPDATE`, `DELETE`, `EXPORT`, `SHARE` |
| `resourceType` | string | `APPOINTMENT`, `CONSULTATION`, `PRESCRIPTION`, `LAB_ORDER`, `CLAIM`, `MEDICAL_RECORD` |
| `resourceId` | UUID | ID of the PHI record accessed |
| `patientId` | UUID | Patient whose PHI was accessed |
| `purpose` | string | From `X-Audit-Context` header |
| `sourceIp` | string | Client IP address |
| `userAgent` | string | HTTP `User-Agent` header value |
| `correlationId` | UUID | Matches `correlationId` in API response for traceability |
| `outcome` | string | `SUCCESS`, `DENIED`, `ERROR` |

---

## OpenAPI Schema Excerpt

### POST /v1/appointments

```yaml
openapi: "3.0.3"
info:
  title: Telemedicine Platform API
  version: "1.0.0"
paths:
  /v1/appointments:
    post:
      summary: Create appointment
      operationId: createAppointment
      security:
        - bearerAuth: [patient:write]
      parameters:
        - in: header
          name: X-Audit-Context
          required: true
          schema:
            type: string
          description: JSON with purpose and actorRole fields
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [patientId, doctorId, scheduledAt, type, chiefComplaint]
              properties:
                patientId:
                  type: string
                  format: uuid
                doctorId:
                  type: string
                  format: uuid
                scheduledAt:
                  type: string
                  format: date-time
                durationMinutes:
                  type: integer
                  minimum: 15
                  maximum: 120
                  default: 30
                type:
                  type: string
                  enum: [VIDEO, PHONE, IN_PERSON]
                chiefComplaint:
                  type: string
                  maxLength: 500
                insuranceId:
                  type: string
                  format: uuid
      responses:
        "201":
          description: Appointment created
          content:
            application/json:
              schema:
                type: object
                properties:
                  appointmentId:
                    type: string
                    format: uuid
                  status:
                    type: string
                    enum: [PENDING_CONFIRMATION, CONFIRMED]
                  eligibilityStatus:
                    type: string
                    enum: [ELIGIBLE, INELIGIBLE, PENDING, UNKNOWN]
                  estimatedCopay:
                    type: number
                    format: float
                  videoJoinUrl:
                    type: string
                    format: uri
        "400":
          $ref: "#/components/responses/ValidationError"
        "409":
          $ref: "#/components/responses/Conflict"
        "422":
          $ref: "#/components/responses/BusinessRuleViolation"
```

### POST /v1/prescriptions/{prescriptionId}/sign

```yaml
  /v1/prescriptions/{prescriptionId}/sign:
    post:
      summary: Sign a prescription
      operationId: signPrescription
      security:
        - bearerAuth: [prescription:write]
      parameters:
        - in: path
          name: prescriptionId
          required: true
          schema:
            type: string
            format: uuid
        - in: header
          name: X-Audit-Context
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [doctorNpi]
              properties:
                doctorNpi:
                  type: string
                  pattern: "^[0-9]{10}$"
                deaNumber:
                  type: string
                  pattern: "^[A-Z]{2}[0-9]{7}$"
                  description: Required for Schedule II-V controlled substances
                twoFactorCode:
                  type: string
                  pattern: "^[0-9]{6}$"
                  description: Required for controlled substances (DEA 2FA)
      responses:
        "200":
          description: Prescription signed successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  prescriptionId:
                    type: string
                    format: uuid
                  status:
                    type: string
                    enum: [SIGNED]
                  signedAt:
                    type: string
                    format: date-time
                  signatureHash:
                    type: string
                    description: SHA-256 hash of the signed prescription document
        "422":
          $ref: "#/components/responses/BusinessRuleViolation"
        "403":
          $ref: "#/components/responses/Forbidden"
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
  responses:
    ValidationError:
      description: Request validation failed
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/ErrorEnvelope"
    Conflict:
      description: Resource conflict
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/ErrorEnvelope"
    BusinessRuleViolation:
      description: Business rule violation
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/ErrorEnvelope"
    Forbidden:
      description: Insufficient permissions
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/ErrorEnvelope"
  schemas:
    ErrorEnvelope:
      type: object
      properties:
        error:
          type: object
          properties:
            code:
              type: string
            message:
              type: string
            details:
              type: object
            correlationId:
              type: string
              format: uuid
            timestamp:
              type: string
              format: date-time
```
