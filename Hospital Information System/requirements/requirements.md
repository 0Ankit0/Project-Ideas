# Requirements

## Purpose
Define implementation-ready requirements for the **Hospital Information System** so product, engineering, integration, security, and operations teams can build a production-grade hospital platform from the documentation alone.

## Product Vision
The HIS is the operational and clinical system of record for inpatient and outpatient hospital workflows. It must support patient identity resolution, registration, admission-transfer-discharge, bed management, encounters, clinical orders, medication administration, results review, discharge, charge capture, insurance touchpoints, and external interoperability through HL7 v2 and FHIR.

## Scope and Release Boundary

| Domain | In Scope | Explicit Boundary |
|---|---|---|
| Patient Identity | EMPI, MRN issuance, duplicate detection, merge and unmerge, alias tracking, deceased handling, consent registry | National identity issuance outside hospital authority |
| Registration and ADT | Pre-registration, check-in, admission, transfer, discharge, bed board, census, boarding, waitlist | Long-term care bed optimization across external facilities |
| Clinical Documentation | Encounters, notes, diagnoses, allergies, problem list, care team, discharge summary | Specialty-specific documentation templates managed outside core release |
| Orders and Fulfillment | CPOE, lab, radiology, pharmacy, nursing tasks, result routing, order correction | Advanced closed-loop infusion pump device control |
| Medication Administration | MAR, barcode medication administration, hold and refusal, witness flows, controlled substance audit | Smart cabinet hardware firmware |
| Revenue Cycle | Eligibility check, pre-auth tracking, charge capture, coding handoff, claim submission trigger | Full general ledger accounting |
| Interoperability | HL7 ADT ORM ORU, FHIR R4 facade, payer APIs, PACS and LIS connectors | National HIE analytics beyond exchange and audit evidence |

## Primary Actors
- **Patient Access Clerk** creates or retrieves patient identity, registers visits, and initiates admissions.
- **Bed Manager** governs ward capacity, isolation placement, and transfer queues.
- **Physician** opens encounters, places orders, reviews results, and signs discharge.
- **Nurse** documents assessments, administers medication, acknowledges critical results, and completes transfers.
- **Pharmacist** verifies medication orders, dispenses drugs, and governs formulary or controlled substances.
- **Lab Technologist** collects specimens, posts results, and escalates critical values.
- **Radiology Technologist** manages modality workflow and result handoff.
- **Billing and Insurance Staff** validate coverage, reconcile charges, and manage claims or denials.
- **Compliance Auditor** reviews PHI access, break-glass events, and medico-legal evidence.

## Functional Requirements

### FR-1 Patient Identity and Registration
1. The system must support search-before-create using MRN, local patient ID, national identifier, phone, DOB, and phonetic name matching.
2. The EMPI must calculate duplicate candidate scores and hard-stop creation when score is above configurable review threshold.
3. The system must issue one active enterprise patient identifier and one or more facility-scoped MRNs with alias lineage.
4. Unidentified patients must receive temporary trauma identifiers that can later convert to canonical identity without breaking downstream references.
5. Merge must preserve source identifiers, chart lineage, audit history, and downstream reconciliation tasks for pharmacy, lab, radiology, billing, and external feeds.
6. Unmerge must be supported only for governed cases and must restore aliases, encounters, orders, and external identifiers from recorded lineage snapshots.
7. Registration must capture guarantor, emergency contact, preferred language, communication consent, privacy flags, and insurance coverage snapshot.

### FR-2 Admissions Transfer Discharge and Bed Management
1. Admission must validate patient identity, attending physician, level of care, infection isolation needs, code status, and financial class.
2. Bed assignment must enforce occupancy, room type, gender and age policies where applicable, isolation rules, service line restrictions, and bed cleaning status.
3. Transfer must create a new bed occupancy segment, retain previous location history, and notify nursing, pharmacy, lab, and transport consumers through events.
4. Discharge must verify discharge order, medication reconciliation status, summary sign-off, bed release workflow, and billing disposition.
5. ADT events must publish HL7 v2 ADT messages and internal Kafka events with idempotent replay support.
6. Boarding and overflow workflow must support queueing patients when no compliant bed exists, including manual override with dual approval.

### FR-3 Encounters Clinical Documentation and Orders
1. The HIS must maintain encounter records across ED, inpatient, surgery, outpatient, and teleconsult contexts with attending and care team history.
2. Signed notes are immutable. Amendments require addendum linkage, author, reason, and timestamp.
3. Orders must support lifecycle states `draft`, `pending_signature`, `active`, `in_progress`, `completed`, `discontinued`, `canceled`, `corrected`, and `entered_in_error`.
4. Medication orders must run allergy, interaction, formulary, duplicate therapy, dose-range, and renal or weight safety checks before activation.
5. Lab and radiology orders must create fulfillable tasks with specimen or modality workflow, status updates, and final result publishing.
6. Critical result workflow must notify ordering clinician first, escalate to covering provider and charge nurse if unacknowledged within policy SLA, and retain evidence.
7. Order correction must never mutate away the original signed order. The original remains visible with correction reason and superseding order linkage.

### FR-4 Medication Administration and Nursing Workflow
1. The system must support barcode scanning for patient wristband and medication package before documentation of administration.
2. Five-rights checks must validate patient, medication, dose, route, and time, with documented override path for downtime and emergency administration.
3. Holds, refusals, wastage, witness signatures, and controlled substance counts must be captured as discrete medication administration events.
4. MAR must reflect the current authoritative order set and distinguish active, held, corrected, canceled, and downtime-entered administrations.

### FR-5 Results, Imaging, and Clinical Communication
1. Lab results must support prelim, corrected, final, and canceled states with value-level normal, abnormal, and critical interpretation.
2. Radiology results must link order, accession, modality, report, and image references while allowing PACS outage queueing.
3. Result corrections must create an amended result version and re-trigger notification to prior viewers and active care team.
4. The clinical inbox must consolidate abnormal results, unread critical alerts, unsigned notes, and pending discharge actions.

### FR-6 Discharge, Billing, and Insurance Touchpoints
1. Discharge workflow must gather disposition, follow-up appointments, discharge medications, pending results, patient instructions, and responsible provider.
2. Charges must be generated from ADT segments, procedures, medication administrations, consumables, and diagnostics using service-specific charge rules.
3. Eligibility and pre-auth checks must be callable at registration, admission, and high-cost order entry.
4. Claim preparation must wait for discharge completion, coding readiness, and bill-hold exceptions before submission.
5. Claim correction and denial rework must preserve prior submission history, payer responses, and staff actions.

### FR-7 Interoperability and External Outages
1. FHIR adapter must expose patient, encounter, condition, allergy intolerance, medication request, medication administration, observation, diagnostic report, procedure, coverage, and consent resources.
2. HL7 integration must support inbound and outbound ACK handling, duplicate message detection, replay, and dead-letter review.
3. When LIS, PACS, payer, HIE, or identity provider is unavailable, the HIS must degrade safely, queue retriable work, and surface operator guidance.
4. External outage recovery must reconcile queued transactions back to the authoritative service using correlation IDs and message control IDs.

## Non-Functional Requirements

| ID | Requirement | Target |
|---|---|---|
| NFR-1 | Tier 1 clinical write APIs | 99.95% monthly availability |
| NFR-2 | Registration and patient search | P95 under 2 seconds at 2,000 concurrent users |
| NFR-3 | Bed assignment commit | P95 under 10 seconds including rules evaluation |
| NFR-4 | Medication verification | P95 under 1 second for CDS checks |
| NFR-5 | Critical result escalation | initial notification under 5 minutes from result finalization |
| NFR-6 | Audit evidence retrieval | exportable within 15 minutes for a requested incident window |
| NFR-7 | Disaster recovery | RTO 60 minutes, RPO 5 minutes for transactional stores |
| NFR-8 | Event delivery | at-least-once with consumer idempotency and replay from 7-year archive |
| NFR-9 | Security | TLS 1.3 in transit, encryption at rest, MFA for privileged and clinical roles |
| NFR-10 | Observability | structured logs, metrics, traces, domain audit events for every critical workflow |

## Compliance and Safety Obligations
- Enforce minimum necessary PHI access with purpose-of-use and relationship-to-patient context.
- Record immutable audit events for PHI reads, state-changing writes, break-glass access, consent overrides, order corrections, and identity merges.
- Retain medico-legal records, audit logs, and clinical event history per jurisdiction and hospital retention schedule. Records under legal hold are never purged automatically.
- Support HIPAA, HITECH, local health record retention law, and hospital privacy board review workflows.
- Provide evidence for Joint Commission style critical result escalation, medication safety, and downtime drills.

## Acceptance Criteria by Critical Workflow

| Workflow | Minimum Acceptance Criteria |
|---|---|
| Search before create | Duplicate candidate list appears before new registration when threshold exceeded. Staff can route to MPI queue. No MRN is issued until adjudication resolves. |
| Admission with bed assignment | Admission cannot complete without compliant bed or documented override. ADT event and bed occupancy record commit atomically. |
| Medication order activation | Order remains pending until CDS checks, required signature, and formulary or override evidence complete. |
| Critical lab result | Result is visible in chart, alert reaches responsible clinician, escalation fires if no acknowledgement, and acknowledgement is audit logged. |
| Discharge | Summary is signed, pending critical tasks are surfaced, discharge medications are reconciled, and bed is marked dirty then available only after environmental services completion. |
| Claim submission | Claim cannot transmit when required diagnosis, coverage, or charge completeness checks fail. Denial or payer outage creates work queue item. |
| Break-glass access | Reason, duration, approving policy, viewed records, and retrospective review task are all captured. |

## Event and Integration Contracts

| Event or Interface | Producer | Required Consumers | Notes |
|---|---|---|---|
| `his.patient.duplicate_flagged.v1` | Patient Service | MPI work queue, registration UI, audit service | Raised before record creation hard stop |
| `his.adt.patient_admitted.v1` | ADT Service | Billing, bed board, FHIR adapter, integration engine | Maps to HL7 ADT A01 |
| `his.adt.patient_transferred.v1` | ADT Service | Pharmacy, lab, radiology, billing | Maps to HL7 ADT A02 |
| `his.clinical.order_placed.v1` | Clinical Service | Lab, radiology, pharmacy, billing | Includes encounter and priority context |
| `his.lab.critical_value_alerted.v1` | Lab Service | Clinical inbox, notification service, audit service | Retain acknowledgement SLA metadata |
| `his.pharmacy.medication_administered.v1` | Pharmacy Service | Clinical timeline, billing, analytics | Basis for charge capture and MAR history |
| FHIR R4 REST | FHIR Adapter | External EHR, HIE, patient app | Read and create only for approved resources |
| HL7 v2 MLLP | Integration Engine | LIS, PACS, payer clearinghouse | ACK and replay required |

## Out of Scope for Initial Delivery
- Full patient portal self-scheduling and self-service bill payment.
- AI-assisted diagnosis or autonomous coding.
- Device-native bedside charting outside supported barcode scanners and printing.
- Multi-hospital enterprise scheduling optimization across external health systems.

## Traceability Notes
- Functional requirements align to TM-001 through TM-008 in `traceability-matrix.md`.
- Business rule IDs in `analysis/business-rules.md` define hard-stop logic for identity uniqueness, bed allocation, consent verification, critical results, and PHI access.
- Implementation readiness gates are defined in `implementation/backend-status-matrix.md`.

