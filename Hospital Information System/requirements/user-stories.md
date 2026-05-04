# User Stories

## Purpose
Provide delivery-ready user stories for the **Hospital Information System** with clear actor intent, acceptance criteria, operational constraints, and evidence expectations.

## Story Writing Standard
- Every story includes the persona, trigger, expected outcome, safety or compliance concern, and measurable completion criteria.
- Negative paths must be explicit when workflow failure can affect patient safety, PHI protection, or revenue integrity.
- Each story references the primary services and event contracts needed for implementation.

## Story Map by Journey

| Journey | Personas | Primary Services |
|---|---|---|
| Identity and registration | Patient Access Clerk, MPI Analyst | Patient Service, FHIR Adapter, Audit Service |
| Admission and bed placement | Admitting Nurse, Bed Manager, House Supervisor | ADT Service, Staff Service, Billing Service |
| Clinical ordering | Physician, Pharmacist, Lab Technologist, Radiology Technologist | Clinical Service, Pharmacy, Lab, Radiology |
| Medication administration | Nurse, Pharmacist | Pharmacy Service, Clinical Service, Billing Service |
| Consent and privacy | Registrar, Clinician, Compliance Auditor | Patient Service, Auth Service, Audit Service |
| Discharge and claims | Physician, Nurse, Case Manager, Billing Staff, Insurance Staff | Clinical Service, ADT Service, Billing Service, Insurance Service |

## Identity Registration and ADT Stories

### US-REG-01 Search before create
**As a** patient access clerk  
**I want** to search existing records before creating a patient  
**So that** duplicate MRNs are avoided and clinical history stays attached to the correct person.

**Acceptance Criteria**
- Search accepts enterprise ID, local MRN, national ID, phone, DOB, email, phonetic name, and mother maiden name when configured.
- When duplicate confidence score exceeds threshold, the UI blocks create and opens duplicate review candidates with score rationale.
- Clerk can mark the registration attempt as `possible_duplicate` and route it to the MPI queue.
- All search and duplicate review actions generate audit evidence with actor, workstation, and correlation ID.

**Implementation Notes**
- Services: Patient Service, Audit Service.
- API touchpoints: `GET /patients/search`, `POST /patients/duplicate-reviews`.
- Events: `his.patient.duplicate_flagged.v1`.

### US-REG-02 Temporary trauma identity
**As an** emergency registrar  
**I want** to create a temporary trauma identity within seconds  
**So that** care can start before the patient is formally identified.

**Acceptance Criteria**
- Temporary identity issues a trauma MRN and wristband in under 30 seconds.
- Clinical orders, medication administrations, and ADT events can reference the temporary identity.
- Identity resolution later converts the trauma identity without losing encounter, order, or result links.
- Merge or conversion requires documented resolver and timestamp.

### US-ADT-01 Admit to compliant bed
**As an** admitting nurse  
**I want** the system to assign a safe bed  
**So that** the patient is placed according to level of care, infection precautions, and bed availability.

**Acceptance Criteria**
- Admission fails when the selected bed is occupied, dirty, blocked, or incompatible with isolation or specialty needs.
- Soft occupancy warnings appear above 95 percent. Hard stop occurs at 100 percent unless a declared surge override exists.
- Successful admission publishes bed occupancy, ADT event, and billing class update atomically.
- Transfer queue is created when no compliant bed exists.

### US-ADT-02 Track transfer history
**As a** bed manager  
**I want** every transfer to retain location history  
**So that** census, billing, and care-team handoff remain accurate.

**Acceptance Criteria**
- Transfer creates start and end timestamps for both source and destination bed occupancy segments.
- Medication due tasks, specimen collection tasks, and transport tasks move to the destination unit.
- Transfer events are visible on the patient timeline and on the operational bed board.
- Failed downstream notifications do not roll back the transfer commit but do create retry work items.

## Clinical and Order Management Stories

### US-CLN-01 Place medication order with CDS
**As a** physician  
**I want** medication orders checked before activation  
**So that** allergy, dose, and formulary issues are caught before the drug reaches the patient.

**Acceptance Criteria**
- Required checks include allergy, cross-reactivity, duplicate therapy, drug interaction, renal adjustment, pregnancy flag, and formulary coverage when data is present.
- Hard-stop safety issues prevent signature. Override-capable issues require reason, supervisor role when configured, and audit evidence.
- Signed medication order publishes an event that pharmacy can verify or question.
- The order remains versioned. Corrections create a superseding order instead of overwriting the original.

### US-CLN-02 Collect specimen and post critical result
**As a** lab technologist  
**I want** specimen and result workflow tied to the order  
**So that** clinicians can trust provenance and urgent results are escalated.

**Acceptance Criteria**
- Result cannot be finalized without specimen collection timestamp, performer, analyzer or manual entry source, and reference range.
- When the value is critical, the system triggers notification and acknowledgement timers immediately.
- Corrected results remain linked to the prior version with correction reason.
- Chart viewers who already opened the prior result receive a corrected-result notification.

### US-CLN-03 Administer medication at bedside
**As a** nurse  
**I want** barcode checks at administration time  
**So that** wrong patient or wrong drug risk is reduced.

**Acceptance Criteria**
- Wristband and medication barcode scan are both required unless downtime or emergency override is documented.
- Five-rights validation runs at documentation time using current patient, order, and schedule context.
- Refusal, hold, wastage, partial dose, and witness data are captured as distinct administration outcomes.
- The completed administration produces a chargeable event when the medication is billable.

### US-CLN-04 Correct an erroneous order
**As a** physician  
**I want** to cancel, discontinue, or correct an order safely  
**So that** downstream departments do not perform the wrong action.

**Acceptance Criteria**
- Correction options depend on current state and fulfillment status.
- Wrong-patient or wrong-drug corrections notify all downstream consumers and active bedside users.
- Original order remains visible with `entered_in_error` or `corrected` status and linkage to replacement order.
- If fulfillment already happened, the system creates remediation tasks such as specimen disposal, medication return, or result amendment review.

## Consent and Privacy Stories

### US-CNS-01 Verify consent before sensitive care
**As a** clinician  
**I want** consent-sensitive content checked before display or action  
**So that** restricted diagnoses, research data, and sensitive services are only accessed lawfully.

**Acceptance Criteria**
- Sensitive compartments include behavioral health, sexual health, HIV-related information, reproductive services, and any locally configured privacy class.
- Authorization uses purpose-of-use, actor role, encounter relationship, location, and consent state.
- Denied access returns user-facing explanation without leaking hidden content.
- Break-glass creates time-bound elevated access with required reason and retrospective review task.

### US-CNS-02 Review break-glass usage
**As a** compliance auditor  
**I want** complete evidence of emergency access  
**So that** privacy exceptions can be justified or remediated.

**Acceptance Criteria**
- Review export includes who accessed what, why, from where, duration, records viewed, and whether follow-up attestation was completed.
- Repeated break-glass usage by same actor or unit is detectable by query and alert.
- Evidence is immutable and retained according to policy.

## Discharge and Revenue Cycle Stories

### US-DSC-01 Complete discharge packet
**As a** discharging physician  
**I want** one workflow for orders, summary, medications, and follow-up  
**So that** the patient leaves with a coherent care plan and the chart is ready for billing.

**Acceptance Criteria**
- Discharge workflow surfaces unresolved critical results, unsigned notes, pending consults, incomplete medication reconciliation, and missing follow-up tasks.
- Patient instructions include diagnosis summary, medications, precautions, appointments, and contact points.
- Discharge cannot complete until bed release disposition is chosen and summary is signed or delegated per policy.
- Completion triggers downstream coding and billing readiness events.

### US-RCM-01 Submit clean claim
**As a** billing specialist  
**I want** charge completeness and payer validation before claim submission  
**So that** avoidable denials are reduced.

**Acceptance Criteria**
- Claim builder validates coverage, authorization, diagnosis pointers, modifiers, discharge status, and required attachments.
- Missing data creates work queue items with clear owner and blocker reason.
- Claim submission outcome is captured with transmission ID, timestamp, payer acknowledgement, and retry state.
- Denials can be corrected and resubmitted without losing prior versions.

## Downtime and Operations Stories

### US-DTN-01 Continue care during outage
**As a** charge nurse  
**I want** a downtime workflow for admissions, orders, and medication administration  
**So that** patient care continues safely when core services are unavailable.

**Acceptance Criteria**
- The system or runbook identifies when downtime mode is active and prints or exposes downtime packets.
- Local downtime identifiers can be reconciled back to canonical patient and encounter records.
- Back-entry requires dual verification for medication administrations and critical orders.
- Reconciliation dashboard tracks entered, pending, rejected, and resolved downtime records.

### US-OPS-01 Replay failed interface transactions
**As an** integration engineer  
**I want** to replay failed HL7 or FHIR transactions safely  
**So that** external outages do not create silent data loss.

**Acceptance Criteria**
- Replay is idempotent and scoped by message type, correlation ID, patient, or outage window.
- Operators can see original payload, ACK or HTTP response, retry count, and current disposition.
- Replay actions are audited and require elevated privilege.
- Post-replay reconciliation shows counts expected, sent, accepted, rejected, and manually resolved.

