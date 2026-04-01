# Use Case Descriptions — Hospital Information System

**Version:** 2.0  
**Status:** Approved  
**Date:** 2025-01-15  
**Author:** Systems Analysis Team  
**Last Reviewed:** 2025-01-15  

---

## Table of Contents

1. [UC-001: Patient Registration](#uc-001-patient-registration)
2. [UC-002: Appointment Scheduling](#uc-002-appointment-scheduling)
3. [UC-003: Patient Admission (Inpatient)](#uc-003-patient-admission-inpatient)
4. [UC-004: Clinical Note Entry (SOAP Note)](#uc-004-clinical-note-entry-soap-note)
5. [UC-005: Medication Ordering](#uc-005-medication-ordering)
6. [UC-006: Lab Order Processing](#uc-006-lab-order-processing)
7. [UC-007: Patient Discharge](#uc-007-patient-discharge)
8. [UC-008: Billing and Claim Submission](#uc-008-billing-and-claim-submission)
9. [UC-009: Emergency Patient Admission (Triage)](#uc-009-emergency-patient-admission-triage)
10. [UC-010: Operating Theatre Scheduling](#uc-010-operating-theatre-scheduling)

---

## UC-001: Patient Registration

**ID:** UC-001  
**Name:** Patient Registration  
**Module:** Patient Management  
**Primary Actor:** Patient Access Clerk  
**Secondary Actors:** IT Admin (EMPI System), HL7 FHIR Gateway, SMS/Email Gateway  
**Preconditions:**
- Clerk is authenticated and holds the `PATIENT_REGISTER` role permission.
- Patient presents at least one valid government-issued photo identification document (e.g., national ID, passport, driver's licence).
- A workstation with access to the HIS patient registration module is available.

**Main Flow:**
1. Clerk opens the "New Patient Registration" screen in the HIS.
2. Clerk scans or manually enters the patient's identity document number; the system queries the Enterprise Master Patient Index (EMPI) for an existing record.
3. EMPI returns no match; the system generates a new unique Medical Record Number (MRN) following the configured MRN algorithm (e.g., facility prefix + 8-digit sequential).
4. Clerk enters mandatory demographic data: legal full name, date of birth, biological sex, primary contact phone number, and residential address.
5. Clerk enters optional data: alternate contact, email address, preferred language, religion, ethnicity, and next-of-kin details.
6. Clerk selects primary insurance plan from the payer master list and enters the member ID, group number, and policy holder name; system triggers a real-time eligibility check (270 transaction) via the Insurance Network interface.
7. Insurance Network returns a 271 response; system displays coverage details including deductible, co-pay, and covered services. Clerk confirms and saves coverage.
8. Clerk captures or uploads patient photograph and consent form signature via digital pad or document scanner.
9. Clerk clicks **Save & Register**; system creates the patient record, assigns the MRN, stamps the registration timestamp, and records the clerk's user ID as the registering clinician.
10. System publishes a `PatientRegistered` event to the internal event bus; the HL7 FHIR Gateway syncs the new patient demographic to the National Health Registry.
11. System generates and prints a patient registration card with MRN barcode/QR code.
12. System sends a registration confirmation SMS/email to the patient's contact with the MRN and appointment instructions (if applicable).

**Alternative Flows:**
- **AF-1 — Duplicate Patient Detected:** At step 2, EMPI returns one or more potential duplicate records. System displays a side-by-side comparison screen. If the clerk confirms it is the same patient, the flow redirects to UC-002 (Search Patient) and opens the existing record. If uncertain, clerk escalates to the IT Administrator to run UC-004 (Merge Patient Records) post-registration.
- **AF-2 — Insurance Eligibility Failure:** At step 6, the Insurance Network returns an error or inactive coverage status. Clerk marks insurance as "Pending Verification", documents the issue, and proceeds with self-pay registration. An insurance coordinator follow-up task is auto-created.
- **AF-3 — Missing Mandatory Fields:** At step 9, if mandatory fields are empty, the system highlights the fields in red and prevents save. Clerk must complete all required fields before re-attempting.
- **AF-4 — Offline Mode:** If the EMPI or insurance eligibility endpoint is unreachable, the system records the patient locally in "Offline" status and queues synchronization for when connectivity is restored. A warning banner is displayed.

**Postconditions:**
- A unique patient record exists in the HIS with an assigned MRN and at least one active encounter type.
- `PatientRegistered` domain event has been published and consumed by the notification, audit, and FHIR sync services.
- Patient demographics are mirrored to the National Health Registry via the FHIR Gateway.
- An audit trail entry records the registering clerk, timestamp, workstation IP, and data fields entered.

**Business Rules:**
- BR-01: Each patient must have exactly one active MRN within the facility.
- BR-02: Date of birth must be a valid past date; future dates are rejected.
- BR-03: At least one phone number (mobile or landline) must be captured.
- BR-12: Duplicate MRNs are never reused; deactivated MRNs are archived with a cross-reference to the surviving record.

---

## UC-002: Appointment Scheduling

**ID:** UC-002  
**Name:** Appointment Scheduling  
**Module:** Appointment Scheduling  
**Primary Actor:** Receptionist / Patient (via Patient Portal)  
**Secondary Actors:** Doctor, SMS/Email Gateway  
**Preconditions:**
- Patient is registered in the system with a valid MRN.
- The receptionist holds the `APPOINTMENT_BOOK` permission, or the patient is authenticated in the patient portal.
- At least one active doctor profile with configured clinic slots exists in the system.

**Main Flow:**
1. Receptionist searches for the patient by MRN, phone number, or name; selects the correct record.
2. Receptionist selects "Book Appointment" and chooses the department/specialty (e.g., General Medicine, Cardiology, Orthopaedics).
3. System displays a calendar view of all doctors in the selected specialty with their available slot grids (next 30 days by default).
4. Receptionist selects a preferred doctor; system displays available time slots color-coded by availability (green = free, yellow = waitlisted, red = full).
5. Receptionist selects a slot; system checks for scheduling conflicts (double-booking, doctor leave, clinic closure) and confirms slot eligibility.
6. Receptionist enters the visit reason, appointment type (New/Follow-up/Urgent), and any patient notes.
7. Receptionist confirms the appointment; system locks the slot, creates the appointment record with a unique Appointment ID, and links it to the patient's MRN.
8. System determines the prior authorization requirement by cross-referencing the patient's insurance plan and the selected procedure/specialty.
9. If pre-authorization is required, the system auto-creates an insurance pre-auth task for the Insurance Coordinator.
10. System sends a booking confirmation with appointment date, time, doctor name, location, and preparation instructions via SMS and/or email.
11. System schedules an automated reminder 24 hours before the appointment (SMS/email) via the SMS/Email Gateway.

**Alternative Flows:**
- **AF-1 — No Available Slots:** System offers the next available slot across all doctors in the specialty or adds the patient to a waitlist. If a cancellation occurs, the top-of-waitlist patient is notified.
- **AF-2 — Patient Books via Portal:** Patient logs in, searches by specialty or doctor name, selects slot, completes booking — same logic applies but the actor is the patient, not the receptionist. Portal enforces the same slot locking rules.
- **AF-3 — Emergency / Walk-in Override:** For urgent cases, a supervisor with `APPOINTMENT_OVERRIDE` permission can book into a full slot, which generates a conflict notification to the doctor.

**Postconditions:**
- Appointment record exists in the system with status `Scheduled`.
- Appointment slot is blocked in the doctor's schedule.
- Confirmation message delivered to the patient.
- If pre-auth required, an Insurance Coordinator task is created with status `Pending`.

**Business Rules:**
- BR-10: A slot cannot be double-booked without supervisor override.
- BR-11: Appointments must be booked at least 15 minutes in advance (configurable per clinic).
- BR-15: Reminder SMS is suppressed if patient has opted out of notifications.

---

## UC-003: Patient Admission (Inpatient)

**ID:** UC-003  
**Name:** Patient Admission (Inpatient)  
**Module:** ADT Management  
**Primary Actor:** Admissions Officer  
**Secondary Actors:** Attending Physician, Ward Nurse, Insurance Coordinator, Billing Clerk  
**Preconditions:**
- Patient is registered with a valid MRN.
- A valid admission order has been written by an authorized physician (either electronically via CPOE or presented as a written order).
- At least one bed is available in the requested ward or the patient is placed on a bed-request queue.

**Main Flow:**
1. Admissions Officer searches for the patient record using MRN or name and opens the ADT (Admission-Discharge-Transfer) screen.
2. Officer selects "Initiate Admission" and enters the admission type: Elective, Emergency, or Maternity.
3. Officer records the admitting diagnosis (ICD-10 code or free text), admitting physician, admission date and time.
4. System triggers an insurance eligibility re-verification and displays current coverage details including inpatient benefit limits and required pre-authorization status.
5. Officer confirms the admitting ward and bed class (General, Semi-Private, Private, ICU) based on clinical need and patient preference.
6. System displays the real-time bed map; Officer selects an available bed. System marks the bed as "Occupied/Reserved".
7. Officer prints the admission wristband with MRN barcode, patient name, DOB, allergies, and blood type.
8. System creates an inpatient encounter record linked to the patient's MRN, assigns an Encounter ID, and sets encounter status to `Active`.
9. System notifies the assigned ward nurse via in-app notification that a new admission is arriving with bed number and estimated arrival time.
10. System notifies the Billing department to open a billing episode and verify any deposit/advance payment requirements per hospital policy.
11. Officer provides the patient with the admission welcome packet including ward rules, visiting hours, consent forms, and patient rights documentation.
12. Patient is escorted to the assigned ward; ward nurse confirms patient arrival and transitions admission status to `Admitted`.

**Alternative Flows:**
- **AF-1 — No Bed Available:** System places the patient in a "Bed Pending" queue. Officer notifies the patient of the wait. When a bed becomes available (post-discharge of another patient), the system auto-assigns and notifies the admissions officer.
- **AF-2 — Insurance Pre-auth Not Obtained:** System displays a warning. Admissions Officer may proceed after documenting a clinical justification or obtaining supervisor sign-off. An urgent pre-auth task is created for the Insurance Coordinator.
- **AF-3 — Emergency Admission:** For unplanned emergency admissions, the admission order may be entered retrospectively within a configured grace period (default: 24 hours). The system creates a provisional encounter immediately upon registration in the Emergency Department.

**Postconditions:**
- An active inpatient encounter record exists in the HIS linked to the patient's MRN.
- Bed is marked `Occupied` in the bed management module.
- Ward nurse has received an admission notification.
- Billing episode has been opened with the correct payer and encounter type.
- An audit log entry captures the admitting officer, timestamp, and bed assignment.

**Business Rules:**
- BR-20: Every inpatient admission requires a physician admission order within 24 hours.
- BR-21: ICU admissions require approval from the ICU Consultant.
- BR-22: Patients under 18 must have a legal guardian's consent recorded before admission.

---

## UC-004: Clinical Note Entry (SOAP Note)

**ID:** UC-004  
**Name:** Clinical Note Entry (SOAP Note)  
**Module:** Clinical Records  
**Primary Actor:** Doctor / Physician  
**Secondary Actors:** Nurse (for Nursing Notes), HL7 FHIR Gateway  
**Preconditions:**
- Doctor is authenticated and has an active patient encounter open (inpatient or outpatient).
- Doctor holds the `CLINICAL_NOTE_WRITE` permission for the patient's current encounter.
- Patient has a registered record with a valid MRN.

**Main Flow:**
1. Doctor opens the patient's active encounter from the clinical worklist and navigates to the "Clinical Notes" tab.
2. Doctor selects "New Note" and chooses the note type: Progress Note, Admission Note, Discharge Summary, Consultation Note, or Procedure Note.
3. **Subjective section:** Doctor enters the chief complaint, history of present illness (HPI), review of systems (ROS), and patient-reported symptoms using structured or free-text entry.
4. **Objective section:** System auto-populates the most recent vital signs from the nursing record. Doctor adds relevant physical examination findings (e.g., cardiovascular, respiratory, abdominal, neurological exam findings).
5. **Assessment section:** Doctor records the working or confirmed diagnosis using the ICD-10 code search typeahead (minimum 3 characters to trigger). Multiple diagnoses can be added with primary, secondary, and comorbidity flags.
6. **Plan section:** Doctor enters the management plan covering medications (links to prescription module), investigations (links to lab/radiology order modules), procedures, referrals, follow-up date, and patient education instructions.
7. Doctor uses smart text shortcuts and clinical templates for common conditions (e.g., typing `.DM2` auto-expands to the standard Type 2 Diabetes management template).
8. Doctor reviews the complete SOAP note and clicks **Sign & Finalize**; system records the doctor's digital signature (cryptographic hash of user ID + timestamp + note content), finalizes the note, and sets status to `Signed`.
9. Signed note is appended to the patient's permanent clinical record in a read-only format. Amendments require a new addendum entry — the original note cannot be edited.
10. System publishes a `ClinicalNoteCreated` event; the HL7 FHIR Gateway packages the note as a FHIR `DocumentReference` or `ClinicalImpression` resource and forwards it to subscribed external systems if configured.

**Alternative Flows:**
- **AF-1 — Auto-save Draft:** Every 30 seconds the system auto-saves the note as a draft. If the browser/session times out, the draft is recoverable for 24 hours.
- **AF-2 — Co-signature Required:** For trainee doctors (registrars/interns), the note is saved as `Pending Co-signature`. The supervising consultant receives a notification to review and co-sign. The note is not finalized until co-signed.
- **AF-3 — Addendum After Signing:** If a correction is needed post-signature, the doctor creates an addendum note linked to the original. The original remains unchanged. The addendum is time-stamped and signed separately.

**Postconditions:**
- A signed, immutable clinical note exists in the patient's clinical record.
- Diagnoses entered are reflected in the patient's active problem list.
- Orders linked from the plan section are active in the respective module (pharmacy, lab, radiology).
- The note is available for downstream consumers (billing for diagnosis coding, insurance for pre-auth).

**Business Rules:**
- BR-30: Clinical notes must be signed within 24 hours of encounter for inpatients, 48 hours for outpatients.
- BR-31: Signed notes cannot be deleted; only addenda are permitted.
- BR-32: ICD-10 codes must be at the highest level of specificity available (4th or 5th character required where applicable).

---

## UC-005: Medication Ordering

**ID:** UC-005  
**Name:** Medication Ordering (Prescription / CPOE)  
**Module:** Pharmacy  
**Primary Actor:** Doctor / Physician  
**Secondary Actors:** Pharmacist, Nurse, Drug Interaction Database  
**Preconditions:**
- Doctor is authenticated with `PRESCRIPTION_WRITE` permission.
- Patient has an active encounter (outpatient or inpatient).
- The hospital formulary has been loaded into the pharmacy module with current drug names, strengths, routes, and formulary status.
- Patient's allergy list is accessible (even if empty, confirmed as reviewed).

**Main Flow:**
1. Doctor opens the Medication Ordering (CPOE) module from the active encounter.
2. Doctor searches for the medication by generic name, brand name, or drug class. System displays formulary and non-formulary options; non-formulary items require justification.
3. Doctor selects the drug; system retrieves the drug profile: available strengths, formulations, recommended dose ranges, and contraindications.
4. Doctor selects dose, frequency, route of administration (e.g., PO, IV, IM, SC), start date, and duration or end date.
5. System immediately runs a Clinical Decision Support (CDS) check:
   - Allergy cross-check: drug vs. patient's recorded allergy list.
   - Drug-drug interaction check: new drug vs. all current active medications.
   - Dose range check: prescribed dose vs. weight-based and age-based limits.
   - Duplicate therapy check: flags if the same drug or therapeutic class is already ordered.
6. If CDS returns a HIGH severity alert (e.g., life-threatening interaction or known allergy), the system blocks ordering and requires the doctor to acknowledge the override with a mandatory clinical reason.
7. If CDS returns LOW/MEDIUM severity alerts, a non-blocking warning is shown. Doctor reviews and can proceed.
8. Doctor adds administration instructions (e.g., "Take with food", "Dilute in 100 mL NS over 30 min") and pharmacy notes.
9. Doctor signs and submits the prescription electronically; system creates the medication order with a unique Prescription ID, timestamps it, and routes it to the pharmacy work queue.
10. System sends an in-app notification to the assigned pharmacist that a new order awaits verification.
11. For inpatients, the medication is also added to the patient's Medication Administration Record (MAR) in a `Pending Pharmacist Verification` state.

**Alternative Flows:**
- **AF-1 — Non-formulary Drug:** Doctor selects a non-formulary drug; system requires the doctor to enter a clinical justification. A pharmacy approval workflow is initiated for formulary exception.
- **AF-2 — PRN (As Needed) Order:** Doctor marks the order as PRN and specifies the indication (e.g., "PRN chest pain"), minimum interval between doses, and maximum daily dose.
- **AF-3 — Verbal / Telephone Order:** In emergency scenarios, nurse enters the order on behalf of the doctor with an order type of "Verbal Order." The doctor must counter-sign within the configured grace period (default: 1 hour).

**Postconditions:**
- An active medication order exists in the pharmacy work queue with status `Pending Verification`.
- The medication appears on the patient's MAR (for inpatients).
- CDS check results are logged in the audit trail including any overrides with clinical justifications.
- Insurance pre-auth is triggered if the drug is in the high-cost or restricted formulary tier.

**Business Rules:**
- BR-40: HIGH-severity allergy overrides must be documented with a mandatory reason code and are escalated to the pharmacy supervisor.
- BR-41: Controlled substances (Schedule II-V) require a two-factor authentication confirmation before order submission.
- BR-42: Weight-based dosing calculations are mandatory for paediatric patients (age < 12 years).

---

## UC-006: Lab Order Processing

**ID:** UC-006  
**Name:** Lab Order Processing  
**Module:** Laboratory  
**Primary Actor:** Doctor (order creation), Lab Technician (processing)  
**Secondary Actors:** Nurse (specimen collection), External Lab System, SMS/Email Gateway  
**Preconditions:**
- Doctor is authenticated with `LAB_ORDER_WRITE` permission.
- Patient has an active encounter.
- The laboratory test catalogue has been configured with test codes, reference ranges, specimen types, and turnaround time targets.

**Main Flow:**
1. Doctor opens the Lab Orders module from the active encounter and selects "New Lab Order".
2. Doctor searches for the test by name or LOINC code (e.g., "CBC", "HbA1c", "Blood Culture") using the test catalogue search.
3. Doctor selects one or more tests; system displays required specimen type (e.g., 3 mL EDTA whole blood, mid-stream urine), collection instructions, and fasting requirements.
4. Doctor selects the urgency: Routine, Urgent, or STAT. STAT orders trigger immediate notification to the lab.
5. Doctor adds clinical indication (ICD-10 code) for insurance billing purposes and any special instructions.
6. Doctor signs and submits the order; system creates a Lab Order with a unique Lab Order ID and routes it to the laboratory work queue.
7. For outreach / reference lab tests, the HL7 FHIR Gateway transmits an OML^O21 HL7 order message to the External Lab System.
8. Nurse or phlebotomist receives the collection task on their worklist, goes to the patient's bedside, and scans the patient's wristband barcode to confirm patient identity (positive patient identification — PPID).
9. Nurse prints and applies specimen labels with patient name, MRN, DOB, order ID, collection date/time, and test name; collects the specimen according to protocol.
10. Specimen is delivered to the laboratory with a chain-of-custody transfer record.
11. Lab Technician accesses the specimen, logs it into the LIS (Laboratory Information System) by scanning the barcode, and places it on the appropriate analyzer or processes it manually.
12. Analyzer returns results; Lab Technician reviews each result value against the reference range and flags abnormal values.
13. For critical values (e.g., K+ > 6.5 mEq/L, platelet count < 20,000/µL), Lab Technician triggers the critical value alert workflow: calls the ordering physician and documents the call details (time, person notified, read-back confirmation) in the LIS.
14. Lab Technician authorizes and releases results; system updates the Lab Order status to `Results Available` and notifies the ordering physician.
15. Results are displayed in the patient's clinical record in a structured format with color-coded H (High) / L (Low) / C (Critical) flags and trend graphs for serial values.

**Alternative Flows:**
- **AF-1 — Specimen Rejected:** If specimen is haemolyzed, quantity insufficient, or improperly labelled, the Lab Technician marks it as `Rejected`, documents the rejection reason, and triggers a re-collection task.
- **AF-2 — Reference Lab:** For tests not performed in-house, the system routes the order to the External Lab System. The external lab's result arrives via HL7 ORU message or FHIR `DiagnosticReport` and is auto-filed to the patient record.

**Postconditions:**
- Lab results are attached to the patient's clinical record with LOINC-coded values and interpretation flags.
- Ordering physician has been notified (in-app + SMS for critical values).
- Lab Order status is `Completed` or `Partial` (if a panel is partially resulted).
- Billing charges for lab tests are automatically posted to the encounter.

**Business Rules:**
- BR-50: Critical value notification must be completed and documented within 30 minutes of result authorization.
- BR-51: STAT orders must have results available within the configured TAT target (default: 60 minutes for common tests).
- BR-52: Specimen labels must be printed at the point of collection, not in advance.

---

## UC-007: Patient Discharge

**ID:** UC-007  
**Name:** Patient Discharge  
**Module:** ADT Management  
**Primary Actor:** Attending Physician (discharge order), Discharge Nurse, Admissions Officer  
**Secondary Actors:** Pharmacist, Billing Clerk, Insurance Coordinator, Patient  
**Preconditions:**
- Patient has an active inpatient encounter with status `Admitted`.
- The attending physician has clinically cleared the patient for discharge.
- All outstanding lab and radiology results are acknowledged by the physician.

**Main Flow:**
1. Attending Physician opens the patient's inpatient encounter and selects "Initiate Discharge Order".
2. Physician documents the discharge condition (Improved, Unchanged, Died, Left Against Medical Advice), final diagnosis list (ICD-10), and discharge disposition (Home, Transfer to SNF, Transfer to Rehab, Home with Home Care).
3. Physician completes and signs the Discharge Summary document within the clinical notes module, including: hospital course narrative, procedures performed, significant investigation results, discharge medications, follow-up instructions, and patient education provided.
4. System triggers a medication reconciliation task: comparing medications on admission, medications added/changed during the stay, and discharge medications to identify discrepancies.
5. Pharmacist reviews the discharge medication list, verifies doses and formulations, and confirms no drug interactions exist in the discharge prescription.
6. Nurse performs patient and/or family education covering: discharge medications (name, dose, frequency, purpose, side effects), wound care, dietary restrictions, activity restrictions, and follow-up appointment details.
7. Nurse documents the patient education session in the nursing notes, including the patient's demonstrated understanding (teach-back method).
8. Admissions Officer receives the discharge notification, processes the checkout at the front desk, and verifies that all signed consent forms and administrative documents are on file.
9. System generates the final itemized bill for the encounter, consolidating all chargeable services (room charges, nursing care, procedures, medications, lab, radiology).
10. Billing Clerk reviews the itemized charges for completeness, applies insurance contractual adjustments, and confirms the patient's outstanding balance.
11. Patient settles the outstanding balance (cash, card, or online payment) or signs a payment arrangement form.
12. System updates the encounter status to `Discharged`, releases the bed, and triggers the bed cleaning/housekeeping notification.
13. Discharge summary is transmitted to the patient's primary care physician via the HL7 FHIR Gateway (FHIR `Composition` resource) and a copy is provided to the patient.

**Alternative Flows:**
- **AF-1 — Against Medical Advice (AMA):** Patient chooses to leave AMA. Physician documents the AMA conversation, risks explained, and patient's informed decision. AMA form is signed by patient. Discharge proceeds but is flagged as AMA.
- **AF-2 — Transfer Discharge:** For inter-facility transfers, the system generates a transfer summary and communicates with the receiving facility. The HL7 FHIR Gateway transmits the patient's clinical summary to the destination facility.

**Postconditions:**
- Inpatient encounter status is `Discharged`.
- Bed status is `Vacant/Pending Cleaning`.
- Final claim is generated and submitted to the insurance payer.
- Discharge summary is distributed to the patient and referring physician.
- A follow-up appointment is created if specified in the discharge plan.

**Business Rules:**
- BR-60: Discharge summary must be signed by the attending physician within 24 hours of discharge.
- BR-61: Medication reconciliation must be documented before discharge orders are marked complete.
- BR-62: For deaths, the Coroner's notification workflow is initiated and the encounter type is updated to `Expired`.

---

## UC-008: Billing and Claim Submission

**ID:** UC-008  
**Name:** Billing and Claim Submission  
**Module:** Billing & Revenue Cycle  
**Primary Actor:** Billing Clerk  
**Secondary Actors:** Insurance Network, Doctor (for coding review), Coding Specialist  
**Preconditions:**
- Patient encounter is in `Discharged` status (for inpatient) or `Completed` status (for outpatient).
- All clinical documentation (diagnosis codes, procedure codes) has been entered and signed.
- Patient insurance information is verified and active.

**Main Flow:**
1. Billing Clerk opens the billing work queue and selects the patient's encounter for billing.
2. System auto-populates the claim with: patient demographics, insurance payer details, encounter dates, admitting/attending physician NPI numbers, facility NPI, and place of service code.
3. Coding Specialist reviews the ICD-10 diagnosis codes and CPT/HCPCS procedure codes documented by the clinical team for accuracy, specificity, and compliance with payer-specific coding guidelines.
4. Billing Clerk enters charge master entries for all services rendered: room and board, nursing care, operating theatre time, anesthesia, pharmacy, laboratory, radiology, and medical supplies.
5. System runs the claim scrubber: validates codes against payer-specific edits, NCCI (National Correct Coding Initiative) edits, LCD/NCD coverage rules, and prior authorization requirements.
6. If the claim scrubber flags errors (e.g., invalid code combination, missing modifier, authorization number absent), the system presents a work queue of errors to the Billing Clerk for correction.
7. Billing Clerk resolves all claim errors and re-runs the scrubber until the claim is clean.
8. Billing Clerk submits the clean claim electronically to the Insurance Network via the clearinghouse as an ANSI X12 837P (professional) or 837I (institutional) transaction.
9. Clearinghouse returns a 277CA acknowledgement (claim acknowledgement) within 24-48 hours confirming receipt and forwarding to the payer.
10. System monitors the claim status; upon receiving the 835 ERA (Electronic Remittance Advice), system auto-posts the insurance payment, contractual adjustments, and patient responsibility amounts.
11. If the claim is fully adjudicated with zero patient balance, the encounter billing status is updated to `Closed`.
12. If a patient balance remains, the system generates a patient statement and sends it via mail/email.

**Alternative Flows:**
- **AF-1 — Claim Denial:** If the payer denies the claim (835 with denial code), the system routes it to the denials work queue. Billing Clerk reviews the denial reason code (CO-4, CO-50, PR-1, etc.) and decides to appeal, correct and resubmit, or write off.
- **AF-2 — Claim Appeal:** Billing Clerk prepares an appeal letter with supporting clinical documentation and resubmits via the payer's appeal portal or by paper. Appeal status is tracked in the HIS.

**Postconditions:**
- Claim has been submitted electronically to the payer with a unique claim reference number.
- Claim status is tracked in real time within the HIS billing module.
- Upon EOB receipt, payments are auto-posted and the patient ledger is updated.
- Revenue cycle metrics (Days in A/R, Clean Claim Rate, Denial Rate) are updated.

**Business Rules:**
- BR-70: Claims must be submitted within the payer's timely filing deadline (typically 90–365 days from date of service).
- BR-71: All claims require at minimum one principal ICD-10 diagnosis code and one CPT/HCPCS procedure code.
- BR-72: Claims for controlled substances must include the prescribing physician's DEA number.

---

## UC-009: Emergency Patient Admission (Triage)

**ID:** UC-009  
**Name:** Emergency Patient Admission (Triage)  
**Module:** Emergency Department / ADT Management  
**Primary Actor:** Triage Nurse  
**Secondary Actors:** Emergency Physician, Radiologist, Lab Technician, Admissions Officer, ICU Nurse  
**Preconditions:**
- The Emergency Department (ED) is operational with at least one triage nurse and one emergency physician on duty.
- The HIS Emergency Module is active with access to the patient registration and triage screens.

**Main Flow:**
1. Patient arrives at the Emergency Department reception; if ambulatory, patient proceeds to the triage window. If by ambulance (EMS), a pre-notification may have been received via the Ambulance/EMS integration.
2. Triage Nurse creates an emergency encounter: if the patient is a returning patient, retrieves existing record by MRN/phone. If new, creates an unregistered patient record with basic demographics (name, DOB, phone) — full registration completed later.
3. Triage Nurse records chief complaint (free text) and assigns an Emergency Severity Index (ESI) triage category:
   - ESI-1: Immediate (life-threatening, requires immediate physician attention)
   - ESI-2: Emergent (high risk, severe pain/distress)
   - ESI-3: Urgent (multiple resources expected, stable vitals)
   - ESI-4: Less Urgent (one resource expected)
   - ESI-5: Non-Urgent (no resources expected)
4. Triage Nurse records initial vital signs: BP, HR, RR, SpO2, temperature, pain score (0–10), GCS (if applicable), weight/height.
5. For ESI-1 or ESI-2 patients: system immediately alerts the Emergency Physician and bed coordinator; patient is taken directly to the Resuscitation Bay or high-acuity area. Standard triage queue rules are bypassed.
6. For ESI-3 to 5 patients: patient is placed in the ED waiting queue; system displays the estimated wait time based on current ED census.
7. Emergency Physician evaluates the patient, performs a history and physical examination, and documents findings in the ED encounter note.
8. Physician orders investigations (blood work, ECG, imaging) via CPOE; Lab and Radiology modules receive the orders with STAT priority.
9. Physician initiates treatment orders (IV access, fluid resuscitation, analgesia, antibiotic therapy) as clinically indicated.
10. Based on investigation results and clinical evaluation, Physician determines disposition:
    - **Admit:** Admission order is written; Admissions Officer initiates UC-003 (Patient Admission).
    - **Discharge:** Discharge instructions are generated; patient is discharged from the ED.
    - **Transfer:** Transfer to a higher-level care facility; transfer summary generated.
    - **Observation:** Patient is placed in ED observation status (distinct from inpatient admission).
11. All ED events (triage time, physician contact time, disposition time) are automatically timestamped for ED metrics reporting (LWBS rate, door-to-doctor time, length of stay).

**Alternative Flows:**
- **AF-1 — MCI (Mass Casualty Incident):** Hospital activates MCI protocol; system switches to disaster triage mode (START triage tags). Patient identifiers may be temporary. System notifies the Hospital Administrator and Command Center.
- **AF-2 — Unknown / Unconscious Patient:** System creates a John Doe / Jane Doe record with a temporary ID. Demographics are reconciled later using available identifiers or family contact.

**Postconditions:**
- Emergency encounter is created and linked to the patient's MRN.
- ESI triage score and triage time are documented in the ED record.
- All ED timestamps are recorded for regulatory and quality reporting.
- If admitted, an inpatient encounter is created and linked to the ED encounter.

**Business Rules:**
- BR-80: ESI-1 patients must have physician evaluation within 0 minutes (immediate). ESI-2 within 15 minutes. ESI-3 within 30 minutes. These are monitored by the dashboard.
- BR-81: Triage must be completed within 5 minutes of patient registration.
- BR-82: All ED encounters, even those that result in a walkout, must be documented in the system.

---

## UC-010: Operating Theatre Scheduling

**ID:** UC-010  
**Name:** Operating Theatre (OT) Scheduling  
**Module:** Staff Management / Surgical Services  
**Primary Actor:** OT Manager / Scheduling Coordinator  
**Secondary Actors:** Surgeon, Anaesthetist, Scrub Nurse, Pharmacy, Biomedical Engineering  
**Preconditions:**
- Patient has a valid surgical booking order signed by the operating surgeon.
- Pre-operative assessment has been completed and documented (anaesthetic pre-assessment, surgical consent).
- Operating theatre availability has been checked and a suitable OT slot exists.
- Required surgical instruments, implants, and equipment have been confirmed with the sterile services department.

**Main Flow:**
1. OT Manager opens the OT Scheduling module and selects the operating theatre, surgical date, and time slot.
2. Manager searches for the patient by MRN, confirms identity, and selects the surgical procedure (CPT code and procedure description).
3. System checks and displays: patient's pre-op assessment status, signed consent form, blood group and crossmatch status, active allergies, and current medications.
4. Manager assigns the primary surgeon, assistant surgeon(s), anaesthetist, scrub nurse, and circulating nurse to the case using the staff availability roster.
5. System validates no scheduling conflicts: surgeon availability, anaesthetist availability, OT suite availability, and equipment availability.
6. Manager enters the estimated procedure duration, special equipment requirements (e.g., C-arm fluoroscopy, intraoperative neuromonitoring, robotic surgical system), and implant requirements (prosthesis size, brand).
7. Manager confirms the case; system locks the OT slot and generates an OT booking confirmation with a unique OT Case Number.
8. System sends notifications to: the assigned surgeon, anaesthetist, scrub nurse team, pharmacy (for surgical medications and anaesthetic drugs), and central sterile supply department (CSSD) for instrument preparation.
9. Pharmacy receives the surgical medication list (antibiotics, anaesthetic drugs, blood products) and prepares the surgical drug tray.
10. CSSD processes the instrument request: checks sterility expiry, prepares surgical sets, and delivers to the OT suite.
11. On the day of surgery, the OT Manager confirms all team members are present, instruments and equipment are ready, and the WHO Surgical Safety Checklist is initiated.
12. OT suite is marked as `In Use` from the scheduled start time; system records actual start time for OT utilization reporting.
13. Upon case completion, scrub nurse documents actual instruments used, implants placed (with lot numbers for traceability), and specimens sent.
14. System records actual end time, calculates OT utilization vs. estimated time, and releases the suite for cleaning and next case preparation.

**Alternative Flows:**
- **AF-1 — Emergency Add-on Case:** An emergency surgery case is added to the schedule, bumping or delaying elective cases. System generates delay notifications to affected patients and surgical teams.
- **AF-2 — Case Cancellation:** Case is cancelled due to patient medical condition, equipment failure, or consent withdrawal. System cancels the booking, releases the OT slot, sends cancellation notifications, and creates a rebooking task.
- **AF-3 — Equipment Unavailable:** If a critical piece of equipment (e.g., the required implant size) is not available, the system flags the case as `Blocked - Equipment Pending` and notifies the biomedical team and OT Manager.

**Postconditions:**
- OT booking is confirmed with all assigned personnel and equipment.
- Pre-operative orders are active in the clinical module.
- On case completion, the surgical report is linked to the patient's encounter.
- Implant traceability records are created for regulatory compliance.
- OT utilization metrics are updated in real time.

**Business Rules:**
- BR-90: Elective surgeries cannot proceed without a signed informed consent form in the patient's digital record.
- BR-91: Blood group and crossmatch results must be available and acknowledged for any case anticipated to require blood transfusion.
- BR-92: Antibiotic prophylaxis must be documented as given within 60 minutes prior to incision (per surgical site infection prevention protocol).
- BR-93: WHO Surgical Safety Checklist (Sign-in, Time-out, Sign-out) must be completed and documented for every surgical case.
