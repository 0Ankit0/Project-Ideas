# User Stories — Telemedicine Platform

## Patient Stories

---

**US-PT-001 — Book a Video Appointment**

> As a patient, I want to search for available doctors by specialty and book a video consultation, so that I can receive care without traveling to a clinic.

Acceptance Criteria:
- Patient can filter providers by specialty, gender preference, language spoken, and insurance accepted.
- Calendar shows real-time availability based on provider schedule gaps.
- System validates that the selected provider is licensed in the patient's state of residence before confirming the booking.
- Booking is rejected with an informative error if the appointment start time is less than 15 minutes from now.
- Patient receives an email and SMS confirmation within 60 seconds of booking.

---

**US-PT-002 — Complete Pre-Visit Intake Forms**

> As a patient, I want to complete digital intake forms before my appointment, so that the doctor has my medical history ready at the start of the consultation.

Acceptance Criteria:
- Patient receives a link to intake forms 24 hours before the appointment.
- Forms include: reason for visit, current medications, allergies, and review of systems relevant to the stated complaint.
- Partially completed forms auto-save every 30 seconds.
- Session timeout warning appears 2 minutes before the 30-minute inactivity limit, with option to extend.
- Completed intake data is visible to the clinician at consultation start.

---

**US-PT-003 — Join a Video Consultation**

> As a patient, I want to join my scheduled video consultation with one click, so that I can connect with my doctor without technical friction.

Acceptance Criteria:
- A "Join Now" button becomes active 5 minutes before the appointment.
- Clicking "Join Now" performs an automated pre-flight check: camera, microphone, browser compatibility, network bandwidth.
- If bandwidth is below 500 kbps, patient is warned that video quality may be degraded.
- Patient enters a virtual waiting room and is notified when the doctor has joined.
- Video call connects within 2 seconds of the doctor admitting the patient.

---

**US-PT-004 — View Consultation Summary and Notes**

> As a patient, I want to view a summary of my consultation after it ends, so that I have a record of the diagnosis, treatment plan, and any prescriptions issued.

Acceptance Criteria:
- Consultation summary appears in the patient portal within 1 hour of the visit ending.
- Summary includes: date, provider name, diagnosis (ICD-10 description), treatment plan, prescriptions issued, and follow-up instructions.
- Patient can download the summary as a PDF.
- If the clinician has not yet signed the note, the portal shows "Your visit summary is being finalized" rather than an unsigned note.

---

**US-PT-005 — View and Pay Bills**

> As a patient, I want to view my billing statements and pay my balance online, so that I can manage healthcare costs without paper bills.

Acceptance Criteria:
- Billing statements are available in the portal within 48 hours of claim processing.
- Statement shows: date of service, provider, procedure description, billed amount, insurance adjustment, patient responsibility.
- Patient can pay via credit card, debit card, or HSA/FSA card.
- Payment confirmation is emailed within 5 minutes of successful transaction.
- Patients can set up automatic payment plans for balances over $100.

---

**US-PT-006 — Request Medical Records Export**

> As a patient, I want to download a copy of my complete medical records, so that I can share them with another provider or keep them for my own reference.

Acceptance Criteria:
- Patient can submit a records export request from the portal with one click.
- System generates the export in PDF or FHIR R4 JSON format per patient preference.
- Export is available for download within 30 calendar days of the request.
- Patient receives an email notification when the export is ready.
- The export includes: demographics, medical history, consultations, prescriptions, lab results, and billing records.

---

**US-PT-007 — Receive Prescription Routing Confirmation**

> As a patient, I want to know when my prescription has been sent to my pharmacy, so that I can plan when to pick it up.

Acceptance Criteria:
- Patient receives an in-app notification and SMS within 5 minutes of the clinician transmitting the prescription.
- Notification includes: medication name, pharmacy name, estimated ready time if available from the pharmacy.
- Patient can view all active prescriptions and their status in the portal.

---

**US-PT-008 — Connect a Wearable Device**

> As a patient, I want to connect my smartwatch or medical device to the platform, so that my doctor can review my biometric trends during consultations.

Acceptance Criteria:
- Patient can authorize Apple HealthKit or Google Fit data sharing from the portal settings page.
- After authorization, the system syncs the last 90 days of relevant biometric data (heart rate, blood pressure, SpO2, blood glucose if applicable).
- Patient can revoke wearable access at any time, which immediately stops data ingestion.
- Wearable data is shown to the clinician only during scheduled consultations; it is not shared beyond the care team without additional consent.

---

**US-PT-009 — Manage Emergency Contact**

> As a patient, I want to designate an emergency contact on my profile, so that the platform can notify them if a medical emergency occurs during a consultation.

Acceptance Criteria:
- Patient can add, edit, or remove an emergency contact from their profile.
- Emergency contact requires: full name, relationship, and verified mobile phone number.
- Verification SMS is sent to the emergency contact's number; contact is not active until the verification code is confirmed.
- Emergency contact is notified automatically if an emergency escalation is triggered during a consultation.

---

**US-PT-010 — Receive Lab Results**

> As a patient, I want to view my lab results in the patient portal after my doctor has reviewed them, so that I understand my health status.

Acceptance Criteria:
- Lab results are not visible to the patient until the ordering clinician has reviewed and released them.
- Once released, the patient receives an in-app and email notification.
- Results are displayed with reference ranges and a plain-language explanation of normal vs. abnormal values.
- Patient can message their care team directly from the lab results view with questions.

---

## Doctor Stories

---

**US-DR-001 — Manage My Availability Schedule**

> As a doctor, I want to set and update my availability schedule, so that patients can book appointments during times I am ready to see them.

Acceptance Criteria:
- Doctor can define recurring weekly availability windows in 30-minute increments.
- Doctor can block individual time slots for administrative tasks, continuing education, or personal time.
- Schedule changes apply to future bookings immediately; existing confirmed appointments are not affected.
- Doctor receives a daily schedule digest email at 07:00 showing the day's appointments.

---

**US-DR-002 — Review Patient Intake Before Consultation**

> As a doctor, I want to review a patient's intake form and medical history before the consultation starts, so that I can prepare relevant clinical questions.

Acceptance Criteria:
- The patient's intake form, prior visit notes, active medications, and allergy list are available in the consultation prep view.
- Prep view opens when the doctor clicks "Start Consultation" and stays accessible throughout the visit.
- If the patient did not complete the intake form, a prominent warning is shown.

---

**US-DR-003 — Conduct a Video Consultation**

> As a doctor, I want to see and hear my patient clearly during a video consultation, so that I can perform an effective remote clinical assessment.

Acceptance Criteria:
- Video stream is at minimum 720p at 30 fps when both parties have adequate bandwidth.
- Doctor's view shows the patient's name, DOB, and chief complaint as an overlay.
- Doctor can share their screen to display lab results or educational materials.
- Doctor can mute/unmute the patient if necessary (with patient notification).
- Consultation timer is visible to the doctor throughout the session.

---

**US-DR-004 — Write and Sign a SOAP Note**

> As a doctor, I want to document the consultation with a structured SOAP note and sign it digitally, so that the visit has a legally valid medical record.

Acceptance Criteria:
- SOAP note editor is embedded in the consultation interface.
- ICD-10-CM code lookup is available inline in the Assessment section.
- CPT code suggestions are auto-populated based on the visit type and documentation.
- Doctor can save a draft at any time.
- Signing the note applies the doctor's cryptographic signature and locks the record from editing.
- If not signed within 24 hours, escalating reminders are sent at 8, 16, and 23-hour marks.

---

**US-DR-005 — Issue an Electronic Prescription**

> As a doctor, I want to prescribe medications electronically and route them directly to the patient's pharmacy, so that the patient can receive treatment quickly.

Acceptance Criteria:
- Prescription form pre-populates with the patient's known allergies and current medications.
- Drug-drug interaction check runs in real time as the doctor types the medication name.
- For Schedule II–V controlled substances, the system requires EPCS two-factor authentication before submission.
- For controlled substances, a PDMP query result is displayed before the doctor can submit the prescription.
- Prescription is transmitted to the patient's selected pharmacy via Surescripts within 30 seconds of submission.

---

**US-DR-006 — Order Laboratory Tests**

> As a doctor, I want to order lab tests electronically during a consultation, so that I can investigate clinical findings without a separate office visit for the patient.

Acceptance Criteria:
- Lab order form provides LOINC-coded test search with common-name aliases (e.g., "CBC" maps to LOINC 58410-2).
- Order is transmitted to the patient's selected lab partner (Quest or LabCorp) within 60 seconds.
- Doctor receives an in-app notification when results are received and available for review.
- Critical values trigger immediate alerts regardless of the doctor's current session state.

---

**US-DR-007 — Initiate Emergency Escalation**

> As a doctor, I want to escalate a patient to emergency services during a consultation, so that I can ensure they receive immediate in-person care when needed.

Acceptance Criteria:
- An "Emergency Escalation" button is permanently visible during any active consultation.
- Clicking the button opens a modal with the patient's last-known address pre-populated.
- Doctor confirms or corrects the address before dispatch is initiated.
- The system contacts local 911 dispatch with patient demographics and emergency description.
- The emergency escalation event is logged with a timestamp, the clinician identity, and all location data.

---

**US-DR-008 — View My Performance Dashboard**

> As a doctor, I want to view my consultation metrics and patient satisfaction scores, so that I can identify areas for improvement in my practice.

Acceptance Criteria:
- Dashboard shows: consultations completed (weekly/monthly), average consultation duration, prescription count, lab order count, and patient satisfaction score (derived from post-visit surveys).
- Data refreshes every 24 hours.
- Doctor can filter metrics by date range.

---

## Nurse / Medical Assistant Stories

---

**US-NR-001 — Perform Pre-Consultation Triage**

> As a nurse, I want to perform a digital triage intake with the patient before the doctor joins, so that the consultation is efficient and the doctor starts with structured information.

Acceptance Criteria:
- Nurse can join the waiting room and conduct an audio-video triage session with the patient before the doctor joins.
- Nurse can record chief complaint, current vital signs (manually entered or from integrated device), pain scale, and medication updates.
- Triage notes are automatically appended to the consultation record and visible to the joining doctor.

---

**US-NR-002 — Record Vital Signs from Connected Device**

> As a nurse, I want to capture vital signs from a Bluetooth-connected medical device, so that measurements are accurate and documented without manual transcription.

Acceptance Criteria:
- Platform supports Bluetooth pairing with approved pulse oximeter, blood pressure cuff, and thermometer models.
- Readings are captured directly into the vital signs section of the triage note.
- Out-of-range values are flagged with a visual indicator at the time of capture.

---

## Billing Administrator Stories

---

**US-BA-001 — Review and Submit Insurance Claims**

> As a billing administrator, I want to review generated CMS-1500 claims and submit them to payers, so that the practice receives reimbursement for services rendered.

Acceptance Criteria:
- Claims are automatically generated within 1 hour of a clinician signing the consultation note.
- Billing admin can review claim line items, edit diagnosis and procedure codes, and attach required documentation before submission.
- Batch submission sends all approved claims to the clearinghouse via X12 837P.
- Submission confirmation (X12 999 acknowledgment) is displayed and stored.

---

**US-BA-002 — Process Claim Denials**

> As a billing administrator, I want to work a denial queue with actionable reason codes, so that I can resubmit corrected claims efficiently.

Acceptance Criteria:
- Denied claims appear in the denial worklist within 24 hours of the ERA receipt.
- Each denial shows the payer's CARC/RARC codes translated to plain-language action items.
- Admin can correct the claim, attach supporting documentation, and resubmit without leaving the denial detail view.
- Resubmitted claims are tracked with the original claim number for audit purposes.

---

**US-BA-003 — Verify Patient Insurance Eligibility**

> As a billing administrator, I want to verify a patient's insurance eligibility before their appointment, so that the patient is informed of their coverage and copay before the visit.

Acceptance Criteria:
- Eligibility verification runs automatically 24 hours before each appointment via X12 270/271.
- Results show: plan name, effective dates, deductible balance, copay amounts, and out-of-pocket maximum.
- If eligibility verification fails, an alert is sent to the billing team and the patient is notified to update their insurance information.

---

**US-BA-004 — Generate Accounts Receivable Reports**

> As a billing administrator, I want to run aging accounts receivable reports, so that I can track outstanding balances and prioritize collections activity.

Acceptance Criteria:
- AR report can be filtered by payer, provider, date range, and aging bucket (0–30, 31–60, 61–90, 90+ days).
- Report is exportable as CSV for use in practice management software.
- Report shows both insurance AR and patient responsibility AR separately.

---

## Platform Administrator Stories

---

**US-AD-001 — Onboard a New Provider**

> As a platform administrator, I want to onboard a new provider with license verification, so that only credentialed clinicians can see patients on the platform.

Acceptance Criteria:
- Onboarding form collects: NPI number, DEA registration, state medical licenses, malpractice insurance certificate, and board certifications.
- System verifies the NPI via NPPES API and state licenses via the FSMB DataLink API.
- Provider account is held in "pending" status until all verifications pass and a compliance officer approves the profile.
- Provider is notified by email when their account is activated.

---

**US-AD-002 — Generate Compliance Reports**

> As a platform administrator, I want to generate HIPAA and SOC-2 compliance reports, so that I can demonstrate regulatory adherence to auditors and partners.

Acceptance Criteria:
- Compliance dashboard shows: PHI access audit trail, failed login attempts, MFA adoption rate, patch status of all services, and BAA coverage.
- Reports are exportable as PDF with digital signature for submission to auditors.
- Report data covers any custom date range up to the last 6 years.

---

**US-AD-003 — Manage Business Associate Agreements**

> As a platform administrator, I want to track BAA status with all third-party vendors that process PHI, so that the platform remains HIPAA-compliant.

Acceptance Criteria:
- BAA registry shows all vendors, BAA execution date, expiration date, and renewal status.
- Admins receive email reminders 90, 60, and 30 days before a BAA expires.
- Expired BAAs trigger an automatic vendor data-processing suspension alert.

---

**US-AD-004 — Configure State Telehealth Policy Rules**

> As a platform administrator, I want to configure state-specific telehealth rules, so that the platform enforces applicable regulations when patients and providers from different states interact.

Acceptance Criteria:
- Admin can enable or disable audio-only telehealth per state.
- Admin can configure state-specific informed consent language that is presented to patients at booking.
- Admin can configure prescribing restrictions per state (e.g., no Schedule II in initial telehealth visit).
- Changes to state rules take effect within 5 minutes without requiring a deployment.

---

**US-AD-005 — Monitor Platform Health**

> As a platform administrator, I want to see a real-time operational dashboard of platform health, so that I can detect and respond to service degradations quickly.

Acceptance Criteria:
- Dashboard shows real-time status for all microservices (video, scheduling, prescriptions, billing, EHR, notifications).
- Active video session count, error rate, and P95 latency are displayed and updated every 60 seconds.
- PagerDuty alerts fire automatically when error rate exceeds 1% for 3 consecutive minutes.

---

**US-AD-006 — Suspend or Terminate a Provider Account**

> As a platform administrator, I want to suspend or terminate a provider's account immediately, so that I can respond to licensure revocation or conduct concerns.

Acceptance Criteria:
- Suspension immediately prevents the provider from starting or joining any new consultations.
- Any in-progress consultations are flagged for immediate review by the clinical supervisor.
- Suspension reason is logged in the audit trail with the administrator's identity and timestamp.
- Provider is notified by email of the suspension and the appeals process.
